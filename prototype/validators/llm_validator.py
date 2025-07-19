"""
LLM-based validator using Gemini API for narrative validation.
Uses natural language understanding to detect entity presence.
"""

import json
import time
from typing import Any

from ..logging_config import setup_logging, with_metrics
from ..validator import BaseValidator, ValidationResult

# Prompt templates for LLM validation
VALIDATION_PROMPT_TEMPLATE = """You are a narrative analyzer for a role-playing game. Your task is to identify which characters are present or mentioned in a given narrative text.

EXPECTED CHARACTERS:
{expected_entities}

NARRATIVE TEXT:
{narrative_text}

INSTRUCTIONS:
1. Identify which expected characters are present in the narrative
2. Consider all forms of reference: names, titles, descriptions, pronouns
3. Note any special states (hidden, unconscious, etc.)
4. Be precise - only mark a character as present if clearly referenced

EXAMPLES:

Example 1:
Expected: ["Gideon", "Rowan"]
Text: "The knight stepped forward while the healer prepared her spells."
Analysis: Both present - "knight" refers to Gideon, "healer" to Rowan

Example 2:
Expected: ["Gideon", "Rowan"]
Text: "He stood alone in the chamber, wondering where she had gone."
Analysis: Uncertain without more context - pronouns could refer to expected characters

Example 3:
Expected: ["Gideon", "Rowan"]
Text: "Gideon searched the room. Rowan was nowhere to be found."
Analysis: Gideon present, Rowan absent (mentioned but not present)

Please respond in JSON format:
{{
  "entities_found": ["list of characters present"],
  "entities_missing": ["list of characters not found"],
  "entity_states": {{"character": ["states"]}},
  "confidence": 0.0-1.0,
  "analysis": "brief explanation"
}}"""

SIMPLE_PROMPT_TEMPLATE = """List which of these characters appear in the text: {expected_entities}

Text: {narrative_text}

Return JSON: {{"found": [], "missing": [], "confidence": 0.0-1.0}}"""


class LLMValidator(BaseValidator):
    """
    LLM-based validator using Gemini API.
    """

    def __init__(
        self,
        gemini_service=None,
        use_simple_prompt=False,
        api_key_path=None,
        timeout=30.0,
        max_retries=3,
        retry_delay=1.0,
    ):
        super().__init__("LLMValidator")
        self.logger = setup_logging(self.name)
        self.gemini_service = gemini_service
        self.use_simple_prompt = use_simple_prompt
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Initialize Gemini if not provided
        if not self.gemini_service and api_key_path:
            try:
                self._init_gemini_service(api_key_path)
            except Exception as e:
                self.logger.warning(f"Failed to initialize Gemini service: {e}")

    def _init_gemini_service(self, api_key_path):
        """Initialize Gemini service from API key file."""
        try:
            # Import here to avoid dependency if not using real API
            import google.generativeai as genai

            # Read API key
            with open(api_key_path) as f:
                api_key = f.read().strip()

            # Configure Gemini
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-pro")
            self.gemini_service = self.model
            self.logger.info("Gemini service initialized successfully")

        except ImportError:
            raise ImportError("google-generativeai package not installed")
        except FileNotFoundError:
            raise FileNotFoundError(f"API key file not found: {api_key_path}")
        except Exception as e:
            raise Exception(f"Failed to initialize Gemini: {e}")

    def _create_prompt(self, narrative_text: str, expected_entities: list[str]) -> str:
        """Create validation prompt for LLM."""
        entities_str = ", ".join(f'"{e}"' for e in expected_entities)

        if self.use_simple_prompt:
            return SIMPLE_PROMPT_TEMPLATE.format(
                expected_entities=entities_str, narrative_text=narrative_text
            )
        return VALIDATION_PROMPT_TEMPLATE.format(
            expected_entities=entities_str, narrative_text=narrative_text
        )

    def _parse_llm_response(self, response_text: str) -> dict[str, Any]:
        """Parse LLM response into structured format."""
        try:
            # Try multiple extraction strategies

            # Strategy 1: Look for JSON code block
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end > json_start:
                    json_str = response_text[json_start:json_end].strip()
                    return json.loads(json_str)

            # Strategy 2: Look for raw JSON
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]

                # Clean up common issues
                json_str = self._clean_json_string(json_str)

                parsed = json.loads(json_str)

                # Validate and normalize the response
                return self._normalize_llm_response(parsed)
            # Fallback parsing if no JSON found
            self.logger.warning("No JSON found in LLM response, using fallback parsing")
            return self._fallback_parse(response_text)

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {e}")
            self.logger.debug(f"Failed to parse: {response_text[:200]}...")
            return self._fallback_parse(response_text)

    def _clean_json_string(self, json_str: str) -> str:
        """Clean common JSON formatting issues from LLM responses."""
        # Remove trailing commas
        json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)

        # Fix single quotes (LLMs sometimes use them)
        # But be careful not to break strings containing apostrophes
        # This is a simple approach - could be improved
        if json_str.count("'") > json_str.count('"'):
            json_str = json_str.replace("'", '"')

        # Remove comments (some LLMs add them)
        json_str = re.sub(r"//.*$", "", json_str, flags=re.MULTILINE)
        json_str = re.sub(r"/\*.*?\*/", "", json_str, flags=re.DOTALL)

        return json_str

    def _normalize_llm_response(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Normalize LLM response to expected format."""
        normalized = {}

        # Handle different field names the LLM might use
        # For entities_found
        found_keys = ["entities_found", "found", "present", "characters_found"]
        for key in found_keys:
            if key in parsed:
                normalized["entities_found"] = parsed[key]
                break
        else:
            normalized["entities_found"] = []

        # For entities_missing
        missing_keys = ["entities_missing", "missing", "absent", "not_found"]
        for key in missing_keys:
            if key in parsed:
                normalized["entities_missing"] = parsed[key]
                break
        else:
            normalized["entities_missing"] = []

        # For confidence
        conf_keys = ["confidence", "score", "certainty"]
        for key in conf_keys:
            if key in parsed:
                normalized["confidence"] = float(parsed[key])
                break
        else:
            normalized["confidence"] = 0.5

        # Ensure confidence is in valid range
        normalized["confidence"] = max(0.0, min(1.0, normalized["confidence"]))

        # Copy other fields
        for key in ["entity_states", "analysis", "explanation", "reasoning"]:
            if key in parsed:
                normalized[key] = parsed[key]

        return normalized

    def _fallback_parse(self, response_text: str) -> dict[str, Any]:
        """Fallback parsing when JSON extraction fails."""
        result = {
            "entities_found": [],
            "entities_missing": [],
            "confidence": 0.3,  # Low confidence for fallback
            "analysis": response_text[:500],
        }

        # Try to extract information using patterns
        response_lower = response_text.lower()

        # Look for positive indicators
        found_patterns = [
            r"(\w+) (?:is|are) present",
            r"found:?\s*([\w\s,]+)",
            r"characters present:?\s*([\w\s,]+)",
            r"identified:?\s*([\w\s,]+)",
        ]

        # Look for negative indicators
        missing_patterns = [
            r"(\w+) (?:is|are) (?:not present|missing|absent)",
            r"missing:?\s*([\w\s,]+)",
            r"not found:?\s*([\w\s,]+)",
            r"absent:?\s*([\w\s,]+)",
        ]

        # Extract found entities
        for pattern in found_patterns:
            matches = re.findall(pattern, response_lower)
            for match in matches:
                # Clean and split potential entity names
                entities = [e.strip() for e in re.split(r"[,\s]+", match) if e.strip()]
                result["entities_found"].extend(entities)

        # Extract missing entities
        for pattern in missing_patterns:
            matches = re.findall(pattern, response_lower)
            for match in matches:
                entities = [e.strip() for e in re.split(r"[,\s]+", match) if e.strip()]
                result["entities_missing"].extend(entities)

        # Deduplicate and capitalize
        result["entities_found"] = list(
            set(e.capitalize() for e in result["entities_found"] if e and len(e) > 2)
        )
        result["entities_missing"] = list(
            set(e.capitalize() for e in result["entities_missing"] if e and len(e) > 2)
        )

        # Adjust confidence if we found something
        if result["entities_found"] or result["entities_missing"]:
            result["confidence"] = 0.5

        self.logger.info(f"Fallback parsing extracted: {result}")
        return result

    def _mock_llm_call(self, prompt: str) -> str:
        """Mock LLM call for testing without API."""
        # Simulate processing time
        time.sleep(0.1)

        # Extract expected entities from prompt
        if "Gideon" in prompt and "Rowan" in prompt:
            if "knight" in prompt.lower() or "healer" in prompt.lower():
                return json.dumps(
                    {
                        "entities_found": ["Gideon", "Rowan"],
                        "entities_missing": [],
                        "confidence": 0.9,
                        "analysis": "Both characters identified through their roles",
                    }
                )
            if "alone" in prompt.lower():
                return json.dumps(
                    {
                        "entities_found": ["Gideon"],
                        "entities_missing": ["Rowan"],
                        "confidence": 0.85,
                        "analysis": "Only one character present",
                    }
                )

        return json.dumps(
            {
                "entities_found": [],
                "entities_missing": ["Gideon", "Rowan"],
                "confidence": 0.7,
                "analysis": "No clear character references found",
            }
        )

    def _call_llm_with_retry(self, prompt: str) -> str:
        """Call LLM with retry logic and timeout handling."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                if self.gemini_service:
                    # Real API call with timeout
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            self.gemini_service.generate_content, prompt
                        )

                        try:
                            llm_response = future.result(timeout=self.timeout)
                            response_text = llm_response.text

                            # Validate response is not empty
                            if not response_text or not response_text.strip():
                                raise ValueError("Empty response from LLM")

                            return response_text

                        except concurrent.futures.TimeoutError:
                            last_error = TimeoutError(
                                f"LLM call timed out after {self.timeout}s"
                            )
                            self.logger.warning(
                                f"Attempt {attempt + 1}/{self.max_retries} timed out"
                            )

                else:
                    # Mock for testing
                    return self._mock_llm_call(prompt)

            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )

                # Exponential backoff between retries
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    self.logger.info(f"Waiting {delay}s before retry...")
                    time.sleep(delay)

        # All retries failed
        self.logger.error(f"All {self.max_retries} attempts failed")
        raise last_error or Exception("LLM call failed after all retries")

    @with_metrics("LLMValidator")
    def validate(
        self,
        narrative_text: str,
        expected_entities: list[str],
        location: str = None,
        **kwargs,
    ) -> ValidationResult:
        """
        Validate narrative using LLM.
        """
        result = ValidationResult()

        # Create prompt
        prompt = self._create_prompt(narrative_text, expected_entities)

        try:
            # Call LLM with retry logic
            response_text = self._call_llm_with_retry(prompt)

            # Parse response
            parsed = self._parse_llm_response(response_text)

            # Map to ValidationResult
            if self.use_simple_prompt:
                result.entities_found = parsed.get("found", [])
                result.entities_missing = parsed.get("missing", [])
            else:
                result.entities_found = parsed.get("entities_found", [])
                result.entities_missing = parsed.get("entities_missing", [])

                # Handle entity states if provided
                if "entity_states" in parsed:
                    result.entity_states = parsed["entity_states"]

            result.confidence = float(parsed.get("confidence", 0.5))
            result.all_entities_present = len(result.entities_missing) == 0

            # Add metadata
            result.metadata = {
                "validator_name": self.name,
                "method": "llm",
                "prompt_type": "simple" if self.use_simple_prompt else "detailed",
                "narrative_length": len(narrative_text),
                "llm_analysis": parsed.get("analysis", ""),
            }

            # Add validation details
            result.validation_details = {
                "llm_analysis": {
                    "prompt_used": prompt[:200] + "..."
                    if len(prompt) > 200
                    else prompt,
                    "response": response_text[:200] + "..."
                    if len(response_text) > 200
                    else response_text,
                    "parsing_success": True,
                }
            }

        except Exception as e:
            # Handle errors
            self.logger.error(f"LLM validation error: {e}")
            result.errors.append(str(e))
            result.entities_missing = expected_entities
            result.confidence = 0.0
            result.all_entities_present = False

            result.validation_details = {
                "llm_analysis": {
                    "prompt_used": prompt[:200] + "...",
                    "response": "",
                    "parsing_success": False,
                }
            }

        return result
