# Python Modules: analysis

> Auto-generated overview of module docstrings and public APIs. Enhance descriptions as needed.
> Last updated: 2025-10-08

## `analysis/capture_actual_llm_responses.py`

**Role:** Capture actual LLM responses from Sariel campaign using the working integration test pattern. Based on mvp_site/tests/test_integration.py approach.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `capture_sariel_llm_responses` – Capture actual LLM responses using the working integration pattern (Status: Keep).

---

## `analysis/capture_llm_responses.py`

**Role:** Capture actual LLM responses from Sariel campaign replay for documentation. This runs a single test and saves the complete narrative responses.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `capture_sariel_responses` – Run Sariel campaign and capture actual LLM responses (Status: Keep).

---

## `analysis/run_real_sariel_capture.py`

**Role:** Capture actual LLM responses by calling the main project environment. Uses subprocess to run tests in the proper environment where Flask is available.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `run_sariel_capture_in_main_project` – Run the Sariel capture in the main project where dependencies exist (Status: Keep).

---

## `analysis/run_sariel_replays.py`

**Role:** Run 10 Sariel campaign replays to measure entity tracking desync rates. This provides statistical significance for the architectural decision validation.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `run_single_sariel_test` – Run a single Sariel campaign integration test and return results (Status: Keep).
- `analyze_replay_results` – Analyze results from multiple replays (Status: Keep).
- `main` – Run 10 Sariel campaign replays and analyze results (Status: Keep).

---

