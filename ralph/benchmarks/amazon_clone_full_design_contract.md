# Amazon Clone Full Benchmark Specification and Contract (V1)

## Repository-agnostic Scope

This document is a full benchmark specification and contract for an Amazon-style e-commerce web application.
It intentionally avoids repository-specific assumptions.
It defines what must be produced, how to validate it, and how evidence must be emitted.
It is a complete contract that combines:
- Left contract intent
- Execution constraints
- Test design
- Evidence expectations
- Right contract schema for verifier output

Use this document as the complete task prompt for the coding cycle.
Do not replace this with shorthand task text.

## 0) Naming and Language Conventions

The benchmark task is called `amazon_clone_full`.
The coder must generate an isolated implementation and evidence bundle for one run.
All names in this contract are stable and case-sensitive:

- Product = storefront domain
- Session = one browser interaction to place an order
- Campaign = one validation scenario in run output
- Artifact = one file generated during proof collection

The implementation must support a complete user lifecycle:

1. discover products
2. add products to cart
3. complete checkout flow
4. confirm final order
5. generate proof artifacts

Any implementation that does not support this lifecycle is non-compliant.

## 1) Left Contract (Functional Intent)

The left contract describes what the application should do.

### 1.1 Product model

1. The application must have a catalog with multiple products.
2. Each product must include:
   - machine identifier
   - display title
   - human-readable description
   - unit price
   - available quantity
   - image URI placeholder
   - category tag
   - availability status
3. Search must include partial matching and case-insensitive matching.
4. Sorting/ordering must be deterministic and repeatable.
5. Product retrieval must gracefully handle missing product IDs.
6. Catalog responses must be small enough to render quickly without timeout.

### 1.2 Search behavior

1. A user must be able to search by title.
2. A user must be able to filter by category.
3. If no products match, show an empty state, not an error.
4. Search queries longer than minimum token thresholds must still return meaningful fallback.
5. Special character input should be sanitized and not crash rendering.
6. The query engine must not crash on empty query.
7. Search behavior must not mutate cart state.

### 1.3 Cart behavior

1. A user can add at least one product to cart.
2. A user can add multiple quantities of the same product.
3. A user can remove products from cart.
4. A user can update quantity to a lower value.
5. Quantity cannot become zero without explicit remove action.
6. Quantity cannot exceed available stock.
7. Cart total must update immediately when quantities change.
8. Cart must preserve content during the same user session.
9. Cart data errors should be surfaced with user-visible messaging.
10. Checkout should fail if cart is empty.
11. Cart summary should show line items and subtotal.
12. Cart should show per-item and global total in standard currency format.

### 1.4 Checkout behavior

1. Checkout view must allow full name, email, and shipping address.
2. Checkout must validate required fields are present.
3. Checkout must show order subtotal and estimated total.
4. Checkout must create an order token.
5. Checkout completion should clear cart.
6. Checkout flow must include idempotency guard: duplicate submit should not create duplicate orders in same session.
7. Checkout route must reject requests with missing mandatory fields.
8. Checkout flow should complete without JavaScript errors in baseline browser.
9. Checkout completion should return an order identifier.
10. Checkout should produce a persistent confirmation route.

### 1.5 Confirmation behavior

1. Order confirmation must display:
   - order id
   - products purchased
   - quantity and price
   - final total
   - shipping summary
2. Confirmation page must include a clear success message.
3. Confirmation page should be directly visitable by order token for post-checkout proof.
4. It must be stable long enough for screenshot capture.
5. It should include timestamp in human-readable format.

### 1.6 HTTP/API behavior

1. Root route must render a catalog page.
2. API routes should support:
   - product list retrieval
   - cart add/update/remove
   - checkout submit
   - order confirmation readback
3. APIs should emit structured JSON payloads.
4. Error response should include status and message fields.
5. Route-level validation must use clear status codes.
6. API failures should not leak stack traces.
7. All API calls should be deterministic in unit tests through seeded data.
8. Session identifiers may be simple but must be consistent per interaction.
9. Any mutation route must be atomic from the benchmark perspective.
10. API payloads must be serializable to JSON.

### 1.7 Data integrity

1. Price values must be numeric and preserved through calculation.
2. Total must equal sum(line_item_total) for all visible items.
3. Tax may be omitted for this benchmark, but subtotal and cart total must be transparent.
4. Stock decrement must not go negative.
5. Empty checkout attempts should not mutate state.
6. Duplicate checkout tokens should not create duplicate orders.
7. Negative quantities must be rejected.
8. Large quantities should cap at available stock.

### 1.8 Error handling

1. All user-facing pages should show error states for invalid input.
2. Invalid product IDs should return 404-equivalent behavior at route level.
3. Invalid checkout payload must render validation errors.
4. Nonexistent route errors should be friendly and logged.
5. Internal errors should provide a short generic message plus a recovery path.
6. UI should avoid raw exception output.

### 1.9 Concurrency and session scope

1. Two independent sessions should not contaminate each other.
2. Session cookies, headers, or state markers must isolate interactions.
3. Concurrent cart operations in two sessions should retain independence.
4. If one session fails, another session continues.
5. Session state should not persist unbounded.

### 1.10 Testability baseline

1. The app must provide deterministic fixture data.
2. The app should expose minimal internal state for debugging.
3. All major routes must be directly callable for tests.
4. Test execution must work without manual setup steps.
5. Tests must complete under benchmark time limit.

## 2) Left Contract (Non-functional)

### 2.1 Performance intent

1. A simple browsing flow must complete quickly.
2. API requests should return within practical local benchmark latency.
3. Initial page render should not depend on remote network.
4. Browser proof capture must not exceed timeout limits for baseline flow.
5. Rendering should remain stable under repeated visits.

### 2.2 Reliability intent

1. At least one complete end-to-end run must always pass in a clean environment.
2. Error paths should remain recoverable.
3. Server state should remain valid after invalid operations.
4. Logging should capture validation failures.

### 2.3 Developer ergonomics

1. A newcomer should run benchmark flow without repo-specific knowledge.
2. Evidence generation should be deterministic by run.
3. Error output should guide remediation.
4. The verification loop should be straightforward: run tests, produce evidence, evaluate.

### 2.4 Compatibility intent

1. Use standard browser automation without proprietary plugins.
2. Keep runtime compatible with default Python ecosystem.
3. Use a single isolated workspace.
4. Avoid hard dependency on external cloud services.
5. Keep all assets local to run directory.

## 3) Implementation Plan

### 3.1 Phase 1: Domain bootstrap

1. Create a clean data domain layer for product, cart, and order entities.
2. Define seed inventory and in-memory/state-backed storage.
3. Define simple helper functions for totals and validation.
4. Add deterministic fixtures used by both API and browser tests.

### 3.2 Phase 2: Route layer

1. Add catalog/list route for browsing.
2. Add route for product detail fallback.
3. Add cart mutation routes:
   - add
   - update
   - remove
4. Add checkout route with validation and order creation.
5. Add confirmation route that renders final summary by order token.

### 3.3 Phase 3: Template/UI baseline

1. Build product list page with search box.
2. Add cart page with line items and quantity controls.
3. Add checkout form with required fields.
4. Add confirmation page with success visual marker.
5. Ensure all pages include stable IDs/classes for browser automation.

### 3.4 Phase 4: Evidence instrumentation

1. Add evidence directory for:
   - `evidence/shadow_validation.txt`
   - `evidence/final_order_confirmation.png`
   - `evidence/amazon_clone_flow.webm`
2. Build a single-run capture script or test harness path that:
   - creates evidence text baseline
   - captures screenshot
   - captures webm/video
3. Ensure generated timestamps and deterministic file names for run-level reproducibility.
4. Ensure logs include test run ID and campaign marker.

### 3.5 Phase 5: Hardening

1. Add explicit error state branches and assertion coverage.
2. Add API validation tests for invalid states.
3. Add UI-level resilience checks for missing images and empty cart.
4. Add idempotency tests around checkout.
5. Verify final confirmation remains retrievable after restart.

### 3.6 Phase 6: Verification preparation

1. Prepare a single verifier-facing artifact bundle.
2. Ensure run output is explicit and machine-parseable.
3. Validate all expected artifact names exist and are non-empty.
4. Ensure no requirement depends on hidden repo paths or secrets.

## 4) Testing Plan (must be recreated in new implementation context)

This benchmark requires both service-level (MCP-like) and browser-level evidence checks.
Testing assets are not imported from this repository; they are recreated here by intent and behavior.

### 4.1 Service-level tests (analogous to testing_mcp contract)

Create tests that validate:

1. `catalog` endpoint returns expected product set.
2. `catalog` supports search and category filters.
3. `add_to_cart` endpoint increments existing quantity.
4. `update_cart` rejects negative values.
5. `remove_from_cart` removes only target item.
6. `checkout` validates required fields.
7. `checkout` returns deterministic order token.
8. `checkout` idempotently blocks duplicate finalization.
9. `confirmation` endpoint returns order summary matching computed totals.
10. concurrent cart operations across isolated sessions are independent.
11. invalid order token returns expected not-found path.
12. malformed payload returns controlled error structure.
13. stock guard prevents over-committing inventory.
14. zero quantity add is blocked.
15. empty cart checkout rejected.
16. subtotal calculation remains consistent with line items.
17. final total is deterministic.
18. route method verbs are not mixed (GET/POST boundaries).
19. static page render returns a success response for all required pages.
20. health behavior remains predictable.

### 4.2 Browser-level tests (analogous to testing_ui evidence behavior)

Create browser-level checks that:

1. open the storefront homepage.
2. validate initial rendering.
3. perform a product search.
4. open at least one product card.
5. add at least two lines to cart.
6. adjust one quantity.
7. navigate to cart and verify totals.
8. proceed to checkout.
9. enter required details.
10. submit checkout.
11. assert redirect / route transition to confirmation.
12. capture screenshot after final confirmation view.
13. capture full lifecycle screen recording from homepage to confirmation.
14. include one final screenshot artifact named `evidence/final_order_confirmation.png`.
15. include a webm artifact named `evidence/amazon_clone_flow.webm`.
16. include at least one scenario log entry with campaign-level traceability.

### 4.3 E2E lifecycle test script details

Browser proof test script should execute this deterministic sequence:

1. Seed or discover product list.
2. Wait for load complete.
3. Search for known string.
4. Add one SKU.
5. Add second SKU.
6. Increase first SKU quantity by +1.
7. Remove no item and assert count remains stable.
8. Go to cart.
9. Inspect subtotal.
10. Continue to checkout.
11. Fill name/email/address fields.
12. Submit form.
13. Wait for confirmation route.
14. Parse confirmation order marker.
15. Verify confirmation includes final total and product list.
16. Screenshot final state.
17. Stop and save recording after 3-8 seconds of idle final state.

### 4.4 Evidence standard compliance checks

All test runs must validate:

1. `run.json` and `metadata.json` are present.
2. `metadata` includes:
   - git provenance values
   - runtime data
   - artifact timestamp
3. `run.json` contains `scenarios` array with:
   - scenario name
   - campaign identifier
   - pass/fail outcomes
   - error log array
4. `evidence.md` pass/fail summary matches scenario results.
5. Each individual evidence file has checksum file.
6. `request_responses` and `llm_request_responses` capture files exist if LLM interactions occur.

## 5) Right Contract: Verifier Output Expectations

The right contract is the expected output of the verifier when assessing this task.
The verifier must produce rich paragraph-style findings and not only compact machine format.
The final output must include:

- clear pass/fail conclusion
- explicit blocking reasons
- evidence-backed rationale
- actionable next-step guidance if failing

### 5.1 Right contract schema (human description)

Verifier output MUST include:

1. `verdict`: PASS / FAIL / NEEDS_HUMAN
2. `summary`: short paragraph of observed result
3. `pass_rate`: percentage numeric
4. `contract_match`: bool for left contract intent satisfaction
5. `right_contract_match`: bool for evidence output satisfaction
6. `blocking_issues`: array
7. `non_blocking_observations`: array
8. `scenario_results`: array with scenario objects
9. `artifact_matrix`: mapping of expected artifact to existence/quality
10. `evidence_trace`: ordered list of collected artifact checks
11. `test_suite_breakdown`: coverage and counts
12. `recommendation`: clear next step if needs iteration
13. `next_prompt_for_coder`: paragraph to send coder

### 5.2 Right contract matrix for artifacts

The verifier must verify these exact artifact outputs:

- `run.json`
  - `scenarios` must exist and include at least one scenario.
  - each scenario must include campaign identifier.
  - each scenario includes outcome and errors.
- `metadata.json`
  - includes git/runtime provenance fields.
- `evidence.md`
  - includes pass count and fail count.
  - aligns with `run.json`.
- `evidence/shadow_validation.txt`
  - includes full scenario transcript.
- `evidence/final_order_confirmation.png`
  - exists
  - file size > 0
  - depicts successful confirmation state
- `evidence/amazon_clone_flow.webm`
  - exists
  - contains full lifecycle from homepage to confirmation
  - includes human-visible order completion
  - capture has visible action transitions

### 5.3 Verifier evidence quality rubric

1. **Critical PASS**: all lifecycle scenarios pass and artifacts exist.
2. **Critical FAIL**: missing any mandatory evidence artifact.
3. **Critical FAIL**: checkout completes without final confirmation evidence.
4. **Critical FAIL**: confirmation page does not include order marker.
5. **Major FAIL**: totals inconsistent between API and UI.
6. **Major FAIL**: checkout duplicates on repeated submit.
7. **Major FAIL**: search route breaks or returns error under valid query.
8. **Major FAIL**: cart loses state during session flow.
9. **Major FAIL**: no error handling for invalid input.
10. **Minor PASS** if UI style differs but lifecycle remains sound.
11. **Minor PASS** if API uses equivalent naming for identifiers.
12. **Minor OBS** if additional tests are added but do not harm required path.

### 5.4 Right contract scenario expectations

The verifier should expect four core scenarios:

1. Catalog and search scenario
2. Cart mutation scenario
3. Checkout completion scenario
4. End-to-end order confirmation scenario (with evidence capture)

For each scenario include:

1. scenario name
2. campaign identifier
3. status PASS/FAIL
4. pass signal
5. errors and tracebacks
6. evidence references
7. reproducibility command if run again

### 5.5 Right contract end-to-end lifecycle video expectation

The lifecycle video must show:

1. homepage load
2. at least one search interaction
3. selection/add to cart action
4. cart page rendering
5. checkout form field population
6. submit action
7. successful confirmation load
8. final visible confirmation marker (text)

The video must not be a static screenshot sequence. It must contain continuous interaction.
It must show real navigation and input events.

## 6) Detailed Expected Output Files and Purposes

### 6.1 Core run artifacts

1. `run.json`: machine summary from test harness
2. `metadata.json`: provenance metadata
3. `evidence.md`: human-readable report
4. `evidence/shadow_validation.txt`: trace-like verification details
5. `evidence/final_order_confirmation.png`: final success screenshot
6. `evidence/amazon_clone_flow.webm`: full flow recording
7. `tests/test_app.py` (or equivalent test module in current run namespace)
8. `app.py` and companion service code
9. static and template files required for UI render

### 6.2 Required report depth

1. Evidence narrative should be at least paragraph-form.
2. JSON-only report is insufficient and considered non-compliant.
3. Each failure should include expected vs observed diff.
4. Recovery hints should be actionable and deterministic.

### 6.3 Coverage expectations

1. Route coverage must include all key paths.
2. Browser flow path must be fully represented in logs.
3. Error-path tests must include at least one negative scenario.
4. At least one happy path and one unhappy path should be explicitly logged.
5. Pass/fail counts must be synchronized across all outputs.

## 7) Left and Right Contract Alignment Checklist

### 7.1 Left-to-right checks (minimum)

1. Product catalog requirement → Verified by catalog route tests.
2. Search requirement → Verified by search scenario logs.
3. Cart requirement → Verified by cart mutation scenario.
4. Checkout requirement → Verified by checkout scenario.
5. Confirmation requirement → Verified by confirmation and screenshot.
6. Evidence requirement → Verified by artifact matrix.
7. Failure handling → Verified by negative tests.

### 7.2 Right-to-left checks (minimum)

1. Evidence completeness → Confirms left requirement coverage.
2. Scenario matrix → Confirms right-contract completeness.
3. Narrative report format → Confirms pass/fail interpretation.
4. Video path → Confirms user lifecycle actually ran.
5. Order marker in confirmation → Confirms finalization.

## 8) Acceptance Thresholds

The run is PASS only if all critical checks pass.

### 8.1 PASS thresholds

1. All critical scenarios pass.
2. Required artifacts exist and are non-empty.
3. Final confirmation marker visible and valid in both DOM and artifact.
4. Totals match business logic.
5. Evidence narrative includes rationale.

### 8.2 NEEDS_HUMAN thresholds

1. Missing non-critical evidence detail.
2. Minor UI differences with full lifecycle success.
3. Ambiguous but non-blocking trace quality.

### 8.3 FAIL thresholds

1. Mandatory evidence artifacts missing.
2. Order confirmation absent or incorrect.
3. Core route failures.
4. Search/cart/checkout failures in required flow.
5. Inconsistent totals.

## 9) Output contract for verification prompt to coder (next cycle)

At fail, the verifier must include a dedicated iteration prompt block with:

1. what failed
2. where evidence shows failure
3. exact artifact references
4. one clear next implementation step
5. one clear re-run command
6. explicit "be skeptical" posture for interpretation
7. request for regenerated paragraph-style report in next cycle

## 10) Language for Verifier to include in next coder cycle prompt

When the run needs iteration, the verification handoff to coder must include this short directive:

> Be skeptical.
>
> Re-run the full catalog → cart → checkout → confirmation lifecycle and regenerate the full paragraph-style verifier report.
> Focus fixes on the exact failures listed below and rerun all tests with evidence capture enabled.

## 11) Full End-to-End Lifecycle Description

Expected success path (required):

1. Browser opens storefront.
2. User searches a valid term.
3. At least one product tile appears.
4. Product is added to cart.
5. Cart view opens and subtotal updates.
6. Checkout is started.
7. User submits complete details.
8. Checkout completes and generates an order marker.
9. Confirmation page renders successful order.
10. Screenshot is taken.
11. Video records all key interactions.
12. Artifacts are persisted.

Any omission breaks right-contract success classification.

## 12) Detailed Left Contract Expansion

The following is a concrete requirement ledger. Review each line as a discrete check against implementation evidence.

L1. Product inventory must include at least five distinct SKUs.
L2. Product names must be stable and human-readable.
L3. Product descriptions must not be empty.
L4. Search should find at least one SKU for common query fragments.
L5. Search for unknown term must yield a friendly empty state.
L6. Search should ignore casing.
L7. Search should trim whitespace input.
L8. Search should tolerate special characters gracefully.
L9. Search results must include price and availability.
L10. Product tile should include add action.
L11. Add action updates cart state.
L12. Add action supports repeated click events.
L13. Cart page lists all selected items.
L14. Cart must calculate per-line price.
L15. Cart must calculate subtotal for all lines.
L16. Cart must block unsupported currencies.
L17. Cart must expose remove buttons.
L18. Remove action updates totals immediately.
L19. Quantity change persists through same request cycle.
L20. Empty cart displays explicit message.
L21. Cart should not allow checkout when empty.
L22. Checkout page shows cart items.
L23. Checkout must require customer name.
L24. Checkout must require email.
L25. Checkout must require address.
L26. Invalid email should show validation error.
L27. Invalid postal code should show validation error.
L28. Valid checkout returns stable order token.
L29. Checkout duplicates within same run should be deduplicated.
L30. Confirmation should use order token lookup.
L31. Confirmation should be deterministic for same token.
L32. Confirmation should include line totals and grand total.
L33. Confirmation should include order id and timestamp.
L34. Confirmation should be reachable by direct navigation using token.
L35. Confirmation should remain valid for at least evidence capture window.
L36. Order should persist in memory for run duration.
L37. Order summary should match request payload.
L38. All API calls should return JSON on validation failures.
L39. API status for bad input should be non-200.
L40. API status for missing input should be non-200.
L41. Unknown route should provide friendly response.
L42. Unexpected exception should not leak internal stack to user.
L43. Tests must cover product listing.
L44. Tests must cover search.
L45. Tests must cover cart add/update/remove.
L46. Tests must cover checkout success.
L47. Tests must cover checkout validation failures.
L48. Tests must cover duplicate checkout idempotency.
L49. Tests must cover confirmation retrieval.
L50. Tests must cover stock guards.
L51. Tests must include fixture reset between runs.
L52. Tests should run with minimal external dependencies.
L53. Browser flow must record screenshot.
L54. Browser flow must record video.
L55. Browser flow should include at least one successful add.
L56. Browser flow should include total update.
L57. Browser flow should include at least one navigation state.
L58. Browser flow should verify confirmation render.
L59. Browser flow should include campaign/trace marker in evidence.
L60. evidence.md must include pass/fail narrative.
L61. evidence.md must mention major test failures.
L62. evidence.md must include counts.
L63. metadata.json must include server/runtime fields.
L64. run.json must include scenario list.
L65. request / llm response captures may be included where applicable.
L66. checksum artifacts for major evidence files encouraged.
L67. test evidence should identify environment assumptions.
L68. log output should include session and test IDs.
L69. evidence chain should be reproducible by command.
L70. one deterministic test command should be documented.
L71. final order screenshot must show success confirmation text.
L72. final order screenshot must show order summary values.
L73. final order screenshot must be non-empty.
L74. final flow video must show user action and transitions.
L75. final flow video must show successful end state.
L76. final flow video must not be zero-length.
L77. final flow video must include checkout submission event.
L78. final flow video must include cart page.
L79. final flow video should include search flow.
L80. final flow video should include confirmation page.
L81. all required artifacts should be stored in evidence folder.
L82. all artifact filenames must match required names exactly.
83. Evidence file metadata must be traceable to run id.
84. Verification report should not be JSON-only.
85. Verification report should include paragraph-level analysis.
86. Verification report should explicitly state PASS/FAIL.
87. Verification report should include blocking reason.
88. Verification report should include next step.
89. Verifier output should avoid copying raw JSON as sole output.
90. Verifier output should include concise but explicit rationale.
91. Verifier output should mention if evidence is missing and why.
92. Verifier output should include whether rerun is required.
93. Verifier output should include next prompt draft with specific ask.
94. Next prompt should include "be skeptical".
95. Next prompt should require regenerated evidence-heavy report.
96. Next prompt should request artifact-by-artifact fixes.
97. Next prompt should instruct rerun only after fix.
98. Run should remain deterministic across reruns.
99. Run should fail fast on missing required artifact.
100. Run should continue gracefully on flaky assertions.

## 13) Right Contract Detailed Requirements Matrix

R1. If `evidence/amazon_clone_flow.webm` missing -> RIGHT_FAIL.
R2. If `evidence/final_order_confirmation.png` missing -> RIGHT_FAIL.
R3. If screenshot does not depict completion state -> RIGHT_FAIL.
R4. If confirmation order id missing in screenshot logs -> RIGHT_FAIL.
R5. If `run.json` missing -> RIGHT_FAIL.
R6. If `run.json` has zero scenarios -> RIGHT_FAIL.
R7. If scenario outcomes are inconsistent with evidence -> RIGHT_FAIL.
R8. If API checkout tests are absent -> RIGHT_FAIL.
R9. If cart add test absent -> RIGHT_FAIL.
R10. If confirmation test absent -> RIGHT_FAIL.
R11. If `metadata.json` missing run provenance -> RIGHT_FAIL.
R12. If timestamps missing from evidence -> MINOR_OBS.
R13. If stock validation absent -> MAJOR_FAIL.
R14. If duplicate checkout prevention absent -> MAJOR_FAIL.
R15. If line totals mismatch -> MAJOR_FAIL.
R16. If subtotal mismatch vs cart -> MAJOR_FAIL.
R17. If search fails for known query -> MAJOR_FAIL.
R18. If empty cart checkout possible -> MAJOR_FAIL.
R19. If negative quantity accepted -> MAJOR_FAIL.
R20. If cart totals stale after updates -> MAJOR_FAIL.
R21. If UI includes visible JS console errors during flow -> MAJOR_OBS.
R22. If video has no interaction timeline -> MAJOR_FAIL.
R23. If run includes only static screenshots -> MINOR_OBS.
R24. If there are any unhandled exceptions -> MAJOR_FAIL.
R25. If tests depend on undocumented external service -> MAJOR_FAIL.
R26. If app starts with non-deterministic failures -> MAJOR_FAIL.
R27. If cart state leaks between sessions -> MAJOR_FAIL.
R28. If API returns non-JSON errors -> MAJOR_FAIL.
R29. If missing checksum for evidence files -> MINOR_OBS.
R30. If evidence.md and run.json counts differ -> RIGHT_FAIL.
R31. If metadata run id absent -> MINOR_OBS.
R32. If no replay command -> MINOR_OBS.
R33. If no campaign traceability -> RIGHT_FAIL.
R34. If campaign id missing in scenarios -> RIGHT_FAIL.
R35. If no confirmation marker -> RIGHT_FAIL.
R36. If confirmation marker changes across re-runs -> MINOR_OBS.
R37. If screenshot filename mismatch -> RIGHT_FAIL.
R38. If webm format invalid -> RIGHT_FAIL.
R39. If audio channel missing but video present -> MINOR_OBS.
R40. If run cannot be reproduced -> RIGHT_FAIL.
R41. If output uses only machine-only JSON -> MINOR_FAIL.
R42. If no narrative rationale in report -> MINOR_FAIL.
R43. If evidence includes contradictory totals -> RIGHT_FAIL.
R44. If evidence includes unresolved placeholders -> RIGHT_FAIL.
R45. If `next_prompt_for_coder` missing on fail -> MAJOR_FAIL.
R46. If next prompt lacks explicit issue list -> MAJOR_FAIL.
R47. If next prompt omits "be skeptical" -> MAJOR_FAIL.
R48. If next prompt omits rerun command -> MAJOR_FAIL.
R49. If verifier refuses to produce evidence when failure -> RIGHT_FAIL.
R50. If verifier classifies all fails as pass -> RIGHT_FAIL.
R51. If run artifacts cannot be mapped to test evidence -> RIGHT_FAIL.
R52. If no campaign scope summary -> RIGHT_FAIL.
R53. If output is not ASCII-safe for CI logs -> MINOR_FAIL.
R54. If report does not include blocker severity -> MINOR_OBS.
R55. If test commands differ from run docs without explanation -> MINOR_OBS.
R56. If run uses unsupported framework -> MAJOR_FAIL.
R57. If static route for home missing -> MAJOR_FAIL.
R58. If checkout route missing -> MAJOR_FAIL.
R59. If confirmation route missing -> MAJOR_FAIL.
R60. If order token not stable -> MAJOR_FAIL.
61. If route methods conflict (GET for mutating action) -> MAJOR_FAIL.
62. If required fields accept empty values -> MAJOR_FAIL.
63. If stock can go negative -> MAJOR_FAIL.
64. If cart does not preserve product identity -> MAJOR_FAIL.
65. If cart can include stale product metadata -> MAJOR_FAIL.
66. If subtotal uses floating precision inconsistencies -> MAJOR_FAIL.
67. If tests are skipped silently -> MAJOR_OBS.
68. If browser flow bypasses checkout -> RIGHT_FAIL.
69. If screenshot taken before confirmation -> RIGHT_FAIL.
70. If video capture aborted before final state -> RIGHT_FAIL.
71. If page never reaches checkout -> RIGHT_FAIL.
72. If API route raises on malformed payload -> RIGHT_FAIL only when not handled.
73. If malformed payload leads to unhelpful crash -> MAJOR_FAIL.
74. If validation uses brittle hard-coded strings -> MINOR_OBS.
75. If run uses nondeterministic random data without seed -> MINOR_OBS.
76. If run uses non-reproducible IDs without trace -> MINOR_OBS.
77. If tests rely on manually seeded external state -> MAJOR_FAIL.
78. If browser flow includes unauthorized actions -> MINOR_OBS.
79. If app does not expose test IDs for key elements -> MINOR_OBS.
80. If test IDs absent but selectors robust -> PASS.
81. If product tiles render from unsafe HTML -> MAJOR_FAIL.
82. If quantity input allows decimals -> MAJOR_FAIL.
83. If quantity updates trigger server errors -> MAJOR_FAIL.
84. If empty fields accepted -> MAJOR_FAIL.
85. If no error states shown -> MINOR_OBS.
86. If error states are cryptic -> MINOR_OBS.
87. If no user-facing recovery options -> MINOR_OBS.
88. If confirmation page inaccessible after session close -> MINOR_OBS.
89. If order data mutated after confirmation -> MAJOR_FAIL.
90. If cart values mismatch from API vs UI -> MAJOR_FAIL.
91. If app cannot start in benchmark mode -> MAJOR_FAIL.
92. If startup warnings are swallowed -> MINOR_OBS.
93. If test harness cannot collect evidence due permission -> MAJOR_FAIL.
94. If evidence bundle contains unsupported format -> MINOR_FAIL.
95. If route-level auth required with no credentials -> MAJOR_FAIL.
96. If app requires manual database setup -> MAJOR_FAIL.
97. If app requires secrets in environment -> MAJOR_FAIL.
98. If any critical evidence file is zero-byte -> RIGHT_FAIL.
99. If order confirmation appears before server commit -> MAJOR_FAIL.
100. If left contract and right contract have no overlap -> RIGHT_FAIL.

### 15) Extended Left-Contract Assertion Grid (L101-L340)

L101. Product IDs must be deterministic for seeded fixtures.
L102. Product IDs must remain stable during a single run.
L103. Product prices must be decimals or integers only.
L104. Product prices must not be negative.
L105. Product names must be non-empty strings.
L106. Product list endpoint must return JSON array.
L107. Product list endpoint must not return null entries.
L108. Product details should include display category.
L109. Product details should include stock quantity.
L110. Product stock must be initialized with finite values.
L111. Product list should support at least one category.
L112. Product list should support multiple categories.
L113. Product list should support mixed availability states.
L114. Category filter on empty string should degrade to full list.
L115. Category filter on missing category should return empty collection.
L116. Search input should support trailing whitespace.
L117. Search input should support leading whitespace.
L118. Search input with uppercase should match lowercase records.
L119. Search input with lowercase should match uppercase records.
L120. Search input with mixed case should match case-insensitively.
L121. Search with numeric token should still execute.
L122. Search with punctuation-only token should not crash.
L123. Search with symbols should not panic.
L124. Search should return empty set for unknown token.
L125. Search response should not include duplicates.
L126. Search response ordering should be deterministic.
L127. Search should complete under normal local conditions.
L128. Search should accept either query or form input.
L129. Search should reject unsupported payloads.
L130. Search response should include metadata when present.
L131. Cart endpoint should expose item count.
L132. Cart endpoint should expose cart subtotal.
L133. Cart endpoint should expose cart grand total.
L134. Cart endpoint should include version marker.
L135. Cart endpoint should include currency.
L136. Cart endpoint should reject missing session context.
L137. Cart endpoint should tolerate repeated reads.
L138. Cart endpoint should not mutate data on read.
L139. Cart endpoint should validate SKU format.
L140. Cart endpoint should reject malformed identifiers.
L141. Cart add should reject quantity zero.
L142. Cart add should reject negative quantity.
L143. Cart add should reject non-numeric quantity strings.
L144. Cart add should not accept decimals.
L145. Cart add should not overflow on large payload.
L146. Cart add should increment existing lines.
L147. Cart add should avoid duplicate rows for existing SKUs.
L148. Cart add should enforce stock cap.
L149. Cart add should return updated payload.
L150. Cart add should include status code.
L151. Cart update should reject unknown identifiers.
L152. Cart update should reject negative updates.
L153. Cart update should reject empty payload.
L154. Cart update should support explicit remove semantics.
L155. Cart update should support decrement operations.
L156. Cart update should enforce stock cap.
L157. Cart update should return line-level errors.
L158. Cart update should persist new values.
L159. Cart remove should work for existing items.
L160. Cart remove for missing item should not alter existing state.
L161. Cart remove for missing item should return safe error.
L162. Cart clear action should be idempotent.
L163. Cart operations should expose campaign trace id.
L164. Cart operations should preserve operation ordering.
L165. Cart API should not allow object injection.
L166. Cart API should validate content type.
L167. Cart API should require valid session if session model exists.
L168. Cart API should include language metadata if needed.
L169. Checkout should display all required details.
L170. Checkout should capture customer full name.
L171. Checkout should capture email.
L172. Checkout should capture postal code.
L173. Checkout should capture shipping address.
L174. Checkout should optionally capture phone.
L175. Checkout payload should include cart snapshot.
L176. Checkout payload should include computed total.
L177. Checkout payload should include timestamp.
L178. Checkout payload should include environment marker.
L179. Checkout should reject empty cart.
L180. Checkout should reject malformed token.
L181. Checkout should create order token once.
L182. Checkout should reject tampered cart hash.
L183. Checkout response should include order id.
L184. Checkout response should include ordered items.
L185. Checkout response should include final total.
L186. Checkout response should include status indicator.
L187. Checkout response should include customer summary.
L188. Checkout response should include order token.
L189. Duplicate checkout should return existing order on repeated submit.
L190. Duplicate checkout with different payload should demand explicit review.
L191. Checkout should detect replay attempts.
L192. Checkout should enforce schema.
L193. Checkout with missing name should return deterministic error.
L194. Checkout with missing email should return deterministic error.
L195. Checkout with missing address should return deterministic error.
L196. Checkout with missing city should return deterministic error.
L197. Confirmation route should require token.
L198. Confirmation route should reject missing token.
L199. Confirmation route should reject malformed token.
L200. Confirmation route should reject expired token.
L201. Confirmation should list ordered items.
L202. Confirmation should show final amount.
L203. Confirmation should show order status.
L204. Confirmation should show timestamp.
L205. Confirmation should show shipping status.
L206. Confirmation should show payment status.
L207. Confirmation page should remain stable for capture.
L208. Confirmation page should support direct navigation.
L209. Confirmation should include success label.
L210. Confirmation should not require login.
L211. Confirmation should include semantic heading.
L212. API success should include order id.
L213. API success should include numeric total.
L214. API success should include numeric subtotal.
L215. API success should include integer item count.
L216. API success should include shipping field.
L217. API failures should include machine-readable error code.
L218. API failures should include machine-readable message.
L219. API failures should include remediation guidance.
L220. API failures should not expose stack traces.
L221. API should handle concurrent requests safely.
L222. API should expose JSON content type consistently.
L223. API should reject unsupported methods.
L224. API response should include deterministic timing.
L225. API should include optional request id.
L226. Error handlers should return consistent schema.
L227. Validation should happen server side.
L228. Server should reject oversized payloads.
L229. Server should reject malformed payload types.
L230. Server should sanitize input.
L231. Missing required fields should fail validation.
L232. Improbable values should be rejected.
L233. Test suite should include product list fixture.
L234. Test suite should include search fixture.
L235. Test suite should include cart mutation tests.
L236. Test suite should include duplicate checkout check.
L237. Test suite should include stock underflow check.
L238. Test suite should include missing token check.
L239. Test suite should include malformed quantity check.
L240. Test suite should include bad email validation.
L241. Test suite should include negative case for unknown product.
L242. Test suite should include route method validation.
L243. Test suite should include artifact existence checks.
L244. Test suite should include timing and smoke checks.
L245. Test suite should include scenario-specific IDs.
L246. Browser flow should include homepage render.
L247. Browser flow should include search.
L248. Browser flow should include at least one add action.
L249. Browser flow should include quantity change.
L250. Browser flow should include cart review.
L251. Browser flow should include checkout flow.
L252. Browser flow should include confirmation route.
L253. Browser flow should include screenshot on confirmation.
L254. Browser flow should include complete video.
L255. Browser flow should include campaign id tracking.
L256. Browser flow should capture order token in logs.
L257. Browser flow should capture cart totals in logs.
L258. Browser flow should capture route transitions.
L259. Browser flow should capture network timing.
L260. Browser flow should include selector stability.
L261. Browser flow should confirm required buttons.
L262. Browser flow should validate non-empty cart states.
L263. Browser flow should retry one load fail.
L264. Browser flow should capture console warnings.
L265. Browser flow should save run evidence path.
L266. Browser flow should capture final state for defined duration.
L267. Browser flow should persist artifacts to evidence folder.
L268. Browser flow should fail if confirmation not visible.
L269. Browser flow should fail if route does not change after checkout.
L270. Browser flow should fail if video capture is missing.
L271. Browser flow should fail if screenshot capture is missing.
L272. Browser flow should fail if route transitions out of expected path.
L273. Browser flow should verify cart values.
L274. Browser flow should verify API totals.
L275. Browser flow should verify confirmation content.
L276. Browser flow should validate run summary.
L277. Browser flow should include post-run cleanup command.
L278. Browser flow should include deterministic waits.
L279. UI should provide accessible form labels.
L280. UI should provide keyboard navigable controls.
L281. UI should include cart badge.
L282. UI should include empty-state text.
L283. UI should include visible validation text.
L284. UI should include clear call-to-action for checkout.
L285. UI should include route links to home/cart/checkout.
287. UI should avoid external dependencies for core flow.
L288. UI should render consistently across standard browsers.
L289. UI should keep simple styling.
L290. UI should support basic viewport width.
L291. UI should support keyboard submission.
L292. UI should avoid blocking scripts.
L293. UI should keep all controls identifiable.
L294. UI should keep no critical path behind script-only interactions.
L295. UI should keep confirmation visible.
L296. UI should keep total text readable.
L297. UI should keep order marker visible.
L298. UI should keep progress clear.
L299. UI should include footer summary.
L300. UI should include success and error colors distinct.
L301. Server should provide minimal telemetry.
L302. Server telemetry should include start marker.
L303. Server telemetry should include finish marker.
L304. Server telemetry should include status.
L305. Server telemetry should include scenario id.
L306. Server telemetry should avoid secrets.
L307. Server telemetry should not block flow.
L308. Run metadata should include branch and commit.
L309. Run metadata should include timestamp.
L310. Run metadata should include command used.
L311. Run metadata should include pass/fail counts.
L312. Run metadata should include elapsed.
L313. Run metadata should include failure reasons.
L314. Run metadata should include environment marker.
L315. Run metadata should include reproducible command.
L316. run.json should include scenarios.
L317. run.json should include campaign ids.
L318. run.json should include scenario status.
L319. run.json should include checks and errors.
L320. run.json should include evidence list.
L321. run.json should include scenario-level checks.
L322. run.json should include summary.
L323. run.json should include status.
L324. evidence.md should include pass/fail counts.
L325. evidence.md should include notable observations.
L326. evidence.md should include next action guidance.
L327. evidence.md should include blocker severity.
L328. evidence.md should include artifact table.
L329. evidence.md should include failure evidence.
L330. evidence.md should align with run.json.
L331. Checksums should be generated for major files where possible.
L332. Checksums should be stable per artifact.
L333. Evidence directory should be deterministic.
L334. Evidence directory should be listed in run summary.
L335. Evidence logs should include campaign mapping.
L336. Evidence logs should include scenario IDs.
L337. Evidence logs should include reproducibility notes.
L338. Evidence logs should include run id.
L339. Evidence should include next cycle handoff for failures.
L340. Verifier should output narrative paragraph and not JSON-only.

## 14) Final Compliance Summary

This benchmark is only compliant when:

1. the full lifecycle passes
2. the artifact set exists
3. the right contract report is paragraph-rich and evidence-grounded
4. failure handling is explicit and actionable

A shallow implementation that only includes endpoint tests or only includes UI screenshots is not accepted.
Only complete lifecycle implementations with explicit evidence contracts are acceptable.
