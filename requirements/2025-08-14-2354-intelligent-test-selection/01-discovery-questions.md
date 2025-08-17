# Discovery Questions

**Phase 2: Context Discovery Questions**

Based on the codebase analysis, here are the five most important yes/no questions to understand the intelligent test selection requirements:

## Q1: Should the intelligent test selection system integrate with CI/CD pipelines (GitHub Actions)?
**Default if unknown:** Yes (CI optimization is a primary benefit)

The codebase has `.github/workflows/` files and GitHub Actions setup. Intelligent test selection would provide maximum value when integrated with automated CI runs to reduce build times and costs.

## Q2: Should the system maintain compatibility with existing test execution modes (--coverage, --integration)?
**Default if unknown:** Yes (backward compatibility is essential)

The current `run_tests.sh` supports `--coverage` and `--integration` flags. The intelligent system should preserve these capabilities while adding smart selection.

## Q3: Should the test selection include safety nets that always run critical integration tests?
**Default if unknown:** Yes (safety is paramount for test reliability)

Critical tests like `test_integration_mock.py` and hook tests should always run regardless of changes to prevent false negatives and maintain system integrity.

## Q4: Should the dependency mapping system be configurable/extensible for future codebase changes?
**Default if unknown:** Yes (maintainability for evolving codebase)

The codebase is actively developed with multiple directories (mvp_site/, tests/, .claude/, orchestration/). A configurable mapping system would allow easy updates as the codebase evolves.

## Q5: Should the system provide detailed reporting of which tests were selected and why?
**Default if unknown:** Yes (transparency for debugging and verification)

Developers need to understand why certain tests were included/excluded to trust the system and debug issues when tests are missed or unnecessarily included.