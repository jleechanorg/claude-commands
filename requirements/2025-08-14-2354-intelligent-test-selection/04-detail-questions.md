# Expert Detail Questions

**Phase 4: Senior Developer Detail Questions**
**Date**: 2025-08-15 00:00

Based on deep codebase analysis, these are the most pressing technical questions for system behavior:

## Q1: Should the intelligent selection preserve the existing memory monitoring limits (5GB local, 10GB CI replica)?
**Default if unknown:** Yes (maintains existing safety infrastructure)

The current `run_tests.sh` has sophisticated memory monitoring with environment-specific limits. The intelligent system should integrate with rather than replace this proven safety mechanism.

## Q2: Should the dependency mapping include frontend-to-backend API test relationships (e.g., frontend_v2 changes → API test execution)?
**Default if unknown:** Yes (ensures full-stack test coverage)

Changes to `frontend_v2/src/services/api.service.ts` could affect API contracts that need validation through backend API tests, requiring cross-layer dependency mapping.

## Q3: Should the system create a new `--intelligent` flag or enhance existing flags with intelligent behavior?
**Default if unknown:** New `--intelligent` flag (preserves backward compatibility)

Following existing CLI patterns (`--coverage`, `--integration`), a dedicated flag provides clear opt-in behavior while maintaining full backward compatibility.

## Q4: Should the dependency configuration support glob patterns for scalable file matching (e.g., `frontend_v2/**/*.tsx` → specific test patterns)?
**Default if unknown:** Yes (provides flexible scalable configuration)

With 40+ directories and hundreds of test files, glob patterns enable maintainable configuration that scales with codebase growth without manual mapping updates.

## Q5: Should the system include a dry-run mode that shows which tests would be selected without executing them?
**Default if unknown:** Yes (enables validation and debugging)

A `--dry-run` or `--show-selection` mode would allow developers to validate test selection logic and debug dependency mappings before execution.