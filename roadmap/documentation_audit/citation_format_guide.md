# Documentation Citation Format Guide

## Overview
This guide establishes a standardized citation format for the WorldArchitect.AI documentation audit. The format uses inline references `[ref#N]` with detailed reference sections at the bottom of each document.

## Citation Format

### Inline Citation
Use `[ref#N]` format where N is a sequential number:
- Example: "The Gemini API supports structured outputs [ref#1]"
- Example: "Configure Firebase authentication as described [ref#2]"

### Reference Section Format
Place at the bottom of each document:

```markdown
## References

[ref#1] Technical Documentation - API/Framework Name
URL: https://example.com/docs
Accessed: YYYY-MM-DD
Section: Specific section if applicable

[ref#2] Code File - path/to/file.py
Lines: 45-67 (if specific lines are referenced)
Function/Class: SpecificFunction (if applicable)
```

## Reference Categories

### 1. Technical Documentation (APIs, Frameworks)
For external technical documentation:

```markdown
[ref#1] Gemini API Documentation - Content Generation
URL: https://ai.google.dev/gemini-api/docs/content-generation
Accessed: 2025-01-12
Section: Structured Output Generation

[ref#2] Flask Documentation - Application Setup
URL: https://flask.palletsprojects.com/en/3.0.x/tutorial/factory/
Accessed: 2025-01-12
Section: Application Factory Pattern
```

### 2. Code File References
For project code files:

```markdown
[ref#3] Code File - mvp_site/gemini_service.py
Lines: 234-256
Function: generate_scene()
Purpose: Scene generation implementation

[ref#4] Code File - mvp_site/main.py
Lines: 45-89
Class: WorldArchitectApp
Purpose: Main application configuration
```

### 3. Configuration/Setup Guides
For configuration and setup documentation:

```markdown
[ref#5] Configuration Guide - Firebase Setup
File: mvp_site/firebase_setup.md
Section: Authentication Configuration
Key Points: Service account setup, environment variables

[ref#6] Setup Guide - Local Development
File: VENV_SETUP.md
Section: Virtual Environment Creation
Command: python3 -m venv venv
```

### 4. External Resources
For third-party resources and tools:

```markdown
[ref#7] External Resource - Google Cloud Run Documentation
URL: https://cloud.google.com/run/docs/deploying
Accessed: 2025-01-12
Section: Deploying from Source Code

[ref#8] External Tool - Playwright Testing Framework
URL: https://playwright.dev/python/docs/intro
Accessed: 2025-01-12
Version: 1.40.0
```

### 5. Internal Project Files
For internal documentation and configuration:

```markdown
[ref#9] Project Documentation - Architecture Overview
File: mvp_site/README.md
Section: System Architecture
Diagram: Figure 2 - Component Interaction

[ref#10] Project Configuration - Testing Setup
File: mvp_site/testing_ui/README_TEST_MODE.md
Section: Browser Test Authentication Bypass
Parameters: test_mode=true, test_user_id=test-user-123
```

## When to Cite

### Citations Required
- **Technical Claims**: Any specific technical capability or limitation
- **Implementation Details**: How something is implemented in code
- **Configuration Steps**: Specific setup or configuration instructions
- **API/Framework Features**: Specific features or methods from external tools
- **Performance Metrics**: Specific numbers or benchmarks
- **Security Requirements**: Authentication, authorization, or security practices
- **Version-Specific Information**: Features tied to specific versions

### Citations Not Required
- **General Programming Concepts**: Common patterns like MVC, REST
- **Standard Practices**: Industry-standard approaches
- **Project Goals**: High-level objectives and vision
- **User Stories**: Feature descriptions from user perspective
- **Basic Definitions**: Common terms that don't require verification

## Template Reference Section

```markdown
## References

[ref#1] Category - Title/Name
URL: (if applicable)
File: (if internal)
Accessed: YYYY-MM-DD
Section/Lines: Specific location
Notes: Additional context if needed

[ref#2] Category - Title/Name
URL: (if applicable)
File: (if internal)
Accessed: YYYY-MM-DD
Section/Lines: Specific location
Notes: Additional context if needed
```

## Best Practices

### 1. Reference Numbering
- Number sequentially within each document
- Start from [ref#1] in each new document
- Don't reuse numbers if references are removed

### 2. Reference Grouping
- Group similar references together in the reference section
- Order by first appearance in document
- Consider sub-grouping by category for documents with many references

### 3. URL Management
- Always include access date for external URLs
- Use permanent links when available (avoid temporary or session-based URLs)
- For versioned documentation, include version number

### 4. Code References
- Include file path relative to project root
- Specify line numbers for specific implementations
- Reference function/class names for context
- Update line numbers if code changes significantly

### 5. Verification
- Verify all URLs are accessible before finalizing
- Ensure code references point to correct lines
- Check that internal file paths are accurate
- Update access dates if re-verifying sources

## Example Document with Citations

```markdown
# Gemini Service Implementation

## Overview
The Gemini service handles all AI content generation for WorldArchitect.AI using Google's Gemini API [ref#1].

## Configuration
The service requires a valid API key configured in environment variables [ref#2]:

```python
api_key = os.getenv('GEMINI_API_KEY')
```

## Scene Generation
Scene generation uses the structured output feature [ref#3] implemented in the `generate_scene()` function [ref#4].

## Error Handling
The service implements exponential backoff for rate limiting [ref#5] with a maximum of 3 retries.

## References

[ref#1] Gemini API Documentation - Overview
URL: https://ai.google.dev/gemini-api/docs
Accessed: 2025-01-12
Section: Getting Started

[ref#2] Code File - mvp_site/gemini_service.py
Lines: 45-47
Function: __init__()
Purpose: API key configuration

[ref#3] Gemini API Documentation - Structured Output
URL: https://ai.google.dev/gemini-api/docs/structured-output
Accessed: 2025-01-12
Section: JSON Schema Support

[ref#4] Code File - mvp_site/gemini_service.py
Lines: 234-289
Function: generate_scene()
Purpose: Main scene generation logic

[ref#5] Code File - mvp_site/gemini_service.py
Lines: 156-178
Function: _handle_rate_limit()
Purpose: Rate limit retry logic
```

## Citation Validation Checklist

Before finalizing any document:
- [ ] All technical claims have citations
- [ ] All code references include file paths and line numbers
- [ ] All external URLs include access dates
- [ ] Reference numbers are sequential
- [ ] No broken or inaccessible links
- [ ] Internal file paths are correct
- [ ] Version-specific information is clearly marked
- [ ] Citation numbers match between inline and reference section