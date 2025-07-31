#!/usr/bin/env python3
"""
Test Framework for Milestone 0.4: Structured Generation Testing
Tests three approaches to preventing narrative desynchronization
"""

import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

# Add project root to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, project_root)

from schemas.entities_simple import SceneManifest, create_from_game_state

from prototype.validators.narrative_sync_validator import NarrativeSyncValidator
from scripts.test_scenarios import get_scenario


class TestApproach(Enum):
    """Testing approach types"""

    VALIDATION_ONLY = "validation_only"
    PYDANTIC_ONLY = "pydantic_only"
    COMBINED = "combined"


@dataclass
class TestResult:
    """Result from a single test run"""

    approach: TestApproach
    campaign_id: str
    scenario_id: str
    session: int
    turn: int

    # Performance metrics
    generation_time_ms: float
    validation_time_ms: float
    total_time_ms: float
    estimated_tokens: int
    estimated_cost: float

    # Results
    entities_expected: list[str]
    entities_found: list[str]
    entities_missing: list[str]
    desync_detected: bool
    desync_pattern: str | None

    # Narrative quality
    narrative_length: int
    narrative_excerpt: str

    # Metadata
    timestamp: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    @property
    def success_rate(self) -> float:
        """Calculate entity mention success rate"""
        if not self.entities_expected:
            return 1.0
        # If both lists empty, validation passed perfectly
        if not self.entities_found and not self.entities_missing:
            return 1.0
        # Otherwise calculate based on what's missing
        found_count = len(self.entities_expected) - len(self.entities_missing)
        return found_count / len(self.entities_expected)


class TestHarness:
    """Main test harness for structured generation testing"""

    def __init__(self, config_path: str | None = None):
        """Initialize test harness with configuration"""
        self.config = self._load_config(config_path)
        self.validator = NarrativeSyncValidator()
        self.results: list[TestResult] = []
        self.logger = self._setup_logging()

        # Metrics tracking
        self.metrics = {
            "total_tests": 0,
            "tests_by_approach": {approach.value: 0 for approach in TestApproach},
            "total_time_ms": 0,
            "total_tokens": 0,
            "total_cost": 0,
        }

    def _load_config(self, config_path: str | None) -> dict[str, Any]:
        """Load test configuration"""
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                return json.load(f)

        # Default configuration
        return {
            "campaigns": [
                "sariel_v2_001",
                "thornwood_001",
                "darkmoor_001",
                "brass_compass_001",
                "frostholm_001",
            ],
            "scenarios": [
                "multi_character",
                "split_party",
                "combat_injured",
                "hidden_characters",
                "npc_heavy",
            ],
            "approaches": [a.value for a in TestApproach],
            "api_config": {
                "model": "gemini-1.5-flash",
                "temperature": 0.7,
                "max_tokens": 500,
                "timeout_seconds": 30,
            },
            "output_dir": "analysis/test_results",
            "save_narratives": True,
        }

    def _setup_logging(self) -> logging.Logger:
        """Configure logging"""
        logger = logging.getLogger("TestHarness")
        logger.setLevel(logging.INFO)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler
        os.makedirs("logs", exist_ok=True)
        fh = logging.FileHandler(
            f"logs/test_harness_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        return logger

    def run_all_tests(self):
        """Run all configured tests"""
        self.logger.info(
            f"Starting test harness with {len(self.config['campaigns'])} campaigns"
        )

        for campaign_id in self.config["campaigns"]:
            for scenario_id in self.config["scenarios"]:
                for approach in self.config["approaches"]:
                    self._run_single_test(
                        campaign_id, scenario_id, TestApproach(approach)
                    )

        self._save_results()
        self._generate_summary()

    def _run_single_test(
        self, campaign_id: str, scenario_id: str, approach: TestApproach
    ):
        """Run a single test"""
        self.logger.info(f"Running test: {campaign_id}/{scenario_id}/{approach.value}")

        # Get test scenario
        scenario = get_scenario(scenario_id, campaign_id)

        # Run appropriate approach
        if approach == TestApproach.VALIDATION_ONLY:
            result = self._run_validation_only(campaign_id, scenario)
        elif approach == TestApproach.PYDANTIC_ONLY:
            result = self._run_pydantic_only(campaign_id, scenario)
        elif approach == TestApproach.COMBINED:
            result = self._run_combined(campaign_id, scenario)
        else:
            raise ValueError(f"Unknown approach: {approach}")

        # Store result
        self.results.append(result)

        # Update metrics
        self.metrics["total_tests"] += 1
        self.metrics["tests_by_approach"][approach.value] += 1
        self.metrics["total_time_ms"] += result.total_time_ms
        self.metrics["total_tokens"] += result.estimated_tokens
        self.metrics["total_cost"] += result.estimated_cost

        return result

    def _run_validation_only(
        self, campaign_id: str, scenario: dict[str, Any]
    ) -> TestResult:
        """Approach 1: Validation-only testing"""
        start_time = time.time()

        # Extract scenario data
        game_state = scenario["game_state"]
        expected_entities = scenario["expected_entities"]

        # Generate narrative (mock for now - will integrate with Gemini later)
        generation_start = time.time()
        narrative = self._generate_mock_narrative(
            game_state, approach=TestApproach.VALIDATION_ONLY
        )
        generation_time = (time.time() - generation_start) * 1000

        # Validate narrative
        validation_start = time.time()
        validation_result = self.validator.validate(
            narrative_text=narrative,
            expected_entities=expected_entities,
            location=game_state.get("location"),
        )
        validation_time = (time.time() - validation_start) * 1000

        # Determine desync pattern
        desync_pattern = None
        if validation_result.entities_missing:
            if game_state.get("combat_state", {}).get("in_combat"):
                desync_pattern = "combat_entity_missing"
            elif "split" in scenario["scenario_id"]:
                desync_pattern = "split_party_confusion"
            else:
                desync_pattern = "general_omission"

        # Create result
        return TestResult(
            approach=TestApproach.VALIDATION_ONLY,
            campaign_id=campaign_id,
            scenario_id=scenario["scenario_id"],
            session=scenario.get("session", 1),
            turn=scenario.get("turn", 1),
            generation_time_ms=generation_time,
            validation_time_ms=validation_time,
            total_time_ms=(time.time() - start_time) * 1000,
            estimated_tokens=len(narrative.split()) * 1.3,  # Rough estimate
            estimated_cost=0.001,  # Placeholder
            entities_expected=expected_entities,
            entities_found=validation_result.entities_found,
            entities_missing=validation_result.entities_missing,
            desync_detected=len(validation_result.entities_missing) > 0,
            desync_pattern=desync_pattern,
            narrative_length=len(narrative),
            narrative_excerpt=narrative[:200] + "..."
            if len(narrative) > 200
            else narrative,
        )


    def _run_pydantic_only(
        self, campaign_id: str, scenario: dict[str, Any]
    ) -> TestResult:
        """Approach 2: Pydantic-only testing"""
        start_time = time.time()

        # Extract scenario data
        game_state = scenario["game_state"]
        expected_entities = scenario["expected_entities"]
        session = scenario.get("session", 1)
        turn = scenario.get("turn", 1)

        # Convert to SceneManifest
        manifest = create_from_game_state(game_state, session, turn)

        # Generate structured prompt
        structured_prompt = manifest.to_prompt_format()

        # Generate narrative with structure (mock for now)
        generation_start = time.time()
        narrative = self._generate_structured_narrative(manifest, structured_prompt)
        generation_time = (time.time() - generation_start) * 1000

        # Simple string matching (no validator)
        validation_start = time.time()
        found_entities = []
        missing_entities = []

        narrative_lower = narrative.lower()
        for entity in expected_entities:
            if entity.lower() in narrative_lower:
                found_entities.append(entity)
            else:
                missing_entities.append(entity)

        validation_time = (time.time() - validation_start) * 1000

        # Create result
        return TestResult(
            approach=TestApproach.PYDANTIC_ONLY,
            campaign_id=campaign_id,
            scenario_id=scenario["scenario_id"],
            session=session,
            turn=turn,
            generation_time_ms=generation_time,
            validation_time_ms=validation_time,
            total_time_ms=(time.time() - start_time) * 1000,
            estimated_tokens=len(narrative.split()) * 1.3
            + len(structured_prompt.split()) * 1.3,
            estimated_cost=0.002,  # Higher due to structured prompt
            entities_expected=expected_entities,
            entities_found=found_entities,
            entities_missing=missing_entities,
            desync_detected=len(missing_entities) > 0,
            desync_pattern="structured_miss" if missing_entities else None,
            narrative_length=len(narrative),
            narrative_excerpt=narrative[:200] + "..."
            if len(narrative) > 200
            else narrative,
        )


    def _generate_structured_narrative(
        self, manifest: SceneManifest, prompt: str
    ) -> str:
        """Generate narrative with Pydantic structure (mock)"""
        # Simulate better performance with structure
        entities = manifest.get_expected_entities()

        if len(entities) > 3:
            # Still miss some in complex scenes
            included = entities[:3]
            narrative = f"In {manifest.current_location.display_name}, "
            narrative += f"{included[0]} stood with {included[1]} and {included[2]}. "
            narrative += "They discussed their plans carefully."
        else:
            # Include all for simple scenes
            narrative = f"In {manifest.current_location.display_name}, "
            if len(entities) == 1:
                narrative += f"{entities[0]} considered the situation."
            else:
                narrative += f"{' and '.join(entities)} were present."

        return narrative

    def _run_combined(self, campaign_id: str, scenario: dict[str, Any]) -> TestResult:
        """Approach 3: Combined approach - Structure + Validation"""
        start_time = time.time()

        # Extract scenario data
        game_state = scenario["game_state"]
        expected_entities = scenario["expected_entities"]
        session = scenario.get("session", 1)
        turn = scenario.get("turn", 1)

        # Convert to SceneManifest for structure
        manifest = create_from_game_state(game_state, session, turn)
        structured_prompt = manifest.to_prompt_format()

        # Generate narrative with structure
        generation_start = time.time()
        narrative = self._generate_combined_narrative(manifest, structured_prompt)
        generation_time = (time.time() - generation_start) * 1000

        # Validate with advanced validator
        validation_start = time.time()
        validation_result = self.validator.validate(
            narrative_text=narrative,
            expected_entities=expected_entities,
            location=game_state.get("location"),
        )
        validation_time = (time.time() - validation_start) * 1000

        # Create result
        return TestResult(
            approach=TestApproach.COMBINED,
            campaign_id=campaign_id,
            scenario_id=scenario["scenario_id"],
            session=session,
            turn=turn,
            generation_time_ms=generation_time,
            validation_time_ms=validation_time,
            total_time_ms=(time.time() - start_time) * 1000,
            estimated_tokens=len(narrative.split()) * 1.3
            + len(structured_prompt.split()) * 1.3,
            estimated_cost=0.0025,  # Highest due to structure + validation
            entities_expected=expected_entities,
            entities_found=validation_result.entities_found,
            entities_missing=validation_result.entities_missing,
            desync_detected=len(validation_result.entities_missing) > 0,
            desync_pattern="combined_miss"
            if validation_result.entities_missing
            else None,
            narrative_length=len(narrative),
            narrative_excerpt=narrative[:200] + "..."
            if len(narrative) > 200
            else narrative,
        )


    def _generate_combined_narrative(self, manifest: SceneManifest, prompt: str) -> str:
        """Generate narrative with both structure and validation awareness (mock)"""
        # Simulate best performance - structure + validation hints
        entities = manifest.get_expected_entities()
        location = manifest.current_location.display_name

        # Include all entities with explicit mentions
        narrative_parts = [f"In {location}"]

        if len(entities) == 1:
            narrative_parts.append(f"{entities[0]} surveyed the area carefully.")
        elif len(entities) == 2:
            narrative_parts.append(f"{entities[0]} and {entities[1]} stood together.")
        else:
            # Explicitly mention each entity
            narrative_parts.append("the group had assembled:")
            for entity in entities:
                narrative_parts.append(f"{entity} was present,")
            narrative_parts[-1] = narrative_parts[-1].rstrip(",") + "."

        # Add context based on scenario
        if any(
            pc.health.hp < pc.health.hp_max * 0.5 for pc in manifest.player_characters
        ):
            narrative_parts.append("Some bore wounds from recent battles.")

        return " ".join(narrative_parts)

    def _generate_mock_narrative(
        self, game_state: dict[str, Any], approach: TestApproach
    ) -> str:
        """Generate mock narrative for testing"""
        # Mock narratives with typical desync patterns
        location = game_state.get("location", "the area")
        pc_name = game_state.get("player_character_data", {}).get(
            "name", "the adventurer"
        )

        if approach == TestApproach.VALIDATION_ONLY:
            # Simulate typical desyncs
            if game_state.get("combat_state", {}).get("in_combat"):
                return f"The battle raged on in {location}. {pc_name} swung their weapon at the enemies."
            return f"{pc_name} looked around {location}, considering the next move."

        # Will add more sophisticated mocks for other approaches
        return f"In {location}, {pc_name} stood ready."

    def _save_results(self):
        """Save all test results"""
        output_dir = self.config["output_dir"]
        os.makedirs(output_dir, exist_ok=True)

        # Save raw results
        results_file = os.path.join(
            output_dir, f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        # Convert config to be JSON serializable
        config_serializable = {
            k: v.value if isinstance(v, TestApproach) else v
            for k, v in self.config.items()
        }
        if "approaches" in config_serializable:
            config_serializable["approaches"] = [
                a.value if isinstance(a, TestApproach) else a
                for a in config_serializable["approaches"]
            ]

        # Convert results to be JSON serializable
        results_serializable = []
        for r in self.results:
            result_dict = asdict(r)
            # asdict preserves enums, so we need to convert them
            if "approach" in result_dict:
                result_dict["approach"] = result_dict["approach"].value
            results_serializable.append(result_dict)

        with open(results_file, "w") as f:
            json.dump(
                {
                    "config": config_serializable,
                    "metrics": self.metrics,
                    "results": results_serializable,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        self.logger.info(f"Saved {len(self.results)} results to {results_file}")

    def _generate_summary(self):
        """Generate summary statistics"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("TEST SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total tests run: {self.metrics['total_tests']}")

        for approach, count in self.metrics["tests_by_approach"].items():
            self.logger.info(f"  {approach}: {count} tests")

        if self.results:
            # Calculate success rates by approach
            approach_stats = {}
            for approach in TestApproach:
                approach_results = [r for r in self.results if r.approach == approach]
                if approach_results:
                    avg_success = sum(r.success_rate for r in approach_results) / len(
                        approach_results
                    )
                    approach_stats[approach.value] = avg_success

            self.logger.info("\nSuccess rates by approach:")
            for approach, rate in approach_stats.items():
                self.logger.info(f"  {approach}: {rate:.2%}")


def main():
    """Main execution"""
    print("Milestone 0.4: Test Structured Generation")
    print("=" * 60)

    # Create test harness
    harness = TestHarness()

    # Show configuration
    print("\nConfiguration:")
    print(f"  Campaigns: {len(harness.config['campaigns'])}")
    print(f"  Scenarios: {len(harness.config['scenarios'])}")
    print(f"  Approaches: {len(harness.config['approaches'])}")
    print(
        f"  Total tests: {len(harness.config['campaigns']) * len(harness.config['scenarios']) * len(harness.config['approaches'])}"
    )

    print("\nTest harness initialized successfully!")
    print("Next step: Implement individual test approaches")


if __name__ == "__main__":
    main()
