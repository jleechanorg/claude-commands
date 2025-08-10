### Product Specification (Spec) for Integrated Fake Code Detection System

#### 1. Overview
- **Project Name**: Claude Fake Code Guard (CFCG)
- **Purpose**: Enhance the existing /fake command and detection hook in the Claude Code CLI workflow by integrating DeepEval and Guardrails AI. This creates a layered, automated system for detecting and preventing "fake" code (e.g., placeholders, speculations, hallucinations) in AI-generated outputs. The system runs non-manually on post-commit and PR push events, providing proactive prevention (during generation), post-evaluation (on saved code), and actionable alerts. It maintains the advisory nature (non-blocking) while improving detection accuracy to 90%+ for obvious fakes, reducing manual intervention needs.
- **Scope**: 
  - Integrate DeepEval and Guardrails AI without modifying their cores.
  - Support Claude Code CLI's hook system (e.g., detect_speculation_and_fake_code.sh).
  - Focus on local machine execution for a solo developer; no cloud dependencies beyond optional LLM APIs.
  - Out of scope: Full autonomy for large features (human review still possible); ML training; UI beyond terminal alerts.
- **Target Users**: Solo developers using Claude Code CLI for AI-assisted coding, seeking automated quality assurance.
- **Business Value**: Reduces debugging time by 30-50% (based on 2025 OSS benchmarks), prevents bad merges, and scales your flywheel of boundary testing/improvements. Potential for open-sourcing as a Claude extension.

#### 2. Requirements
- **Functional Requirements**:
  - **Detection Layers**:
    - Guardrails AI: Runtime prevention—validate code during generation/saving to block or flag fakes (e.g., regex for "TODO", LLM-validator for non-functional logic).
    - DeepEval: Post-generation evaluation—score saved code/PRs for hallucinations/speculation (e.g., G-Eval for correctness, threshold-based alerts).
    - Native Hook: Retain your 21 patterns for speculation/fake code, running first for lightweight checks.
  - **Triggers**: Auto-run on:
    - File saves from Claude (via watcher).
    - Git commits/PR pushes (via pre-commit hooks).
  - **Alerts**: Terminal/console notifications for detections (e.g., "🚨 Fake Code Alert: Placeholder found - Score: 0.4"). Optional: Desktop popups, Slack/email.
  - **Reporting**: Combined summary (e.g., "Guardrails: Passed prevention; DeepEval: Failed evaluation - Details: ...").
  - **Customization**: Easy addition of patterns/metrics (e.g., YAML config for your 21 patterns).
  - **Performance**: <5s per run for small files; non-blocking (advisory exit 0).
- **Non-Functional Requirements**:
  - **Usability**: Seamless with existing /fake (e.g., wrapper script calls both tools).
  - **Compatibility**: Works on Linux/Mac/Windows; Python 3.9+; integrates with gh CLI/git.
  - **Security**: No external data sharing; local execution.
  - **Reliability**: 90%+ detection for common fakes (benchmarked against your manual tests).
  - **Scalability**: Handles 100s of PRs/month; low resource use (no heavy ML).
- **User Stories**:
  - As a dev, I want automatic checks on Claude saves, so fakes are flagged before commit.
  - As a dev, I want layered detection (prevention + evaluation), so accuracy improves without manual effort.
  - As a dev, I want customizable alerts, so I get notified only on critical issues.

#### 3. Assumptions and Constraints
- **Assumptions**: Claude Code CLI supports hooks; you have API keys for LLMs (e.g., Anthropic/OpenAI for judging).
- **Constraints**: No full code autonomy (human review for large features); bash/Python hybrid; local-only (no cloud).

#### 4. Installation Instructions for DeepEval
- **Prerequisites**: Python 3.9+ (check: `python --version`), pip. Internet needed for initial install; runs locally after.
- **Steps**:
  1. Create a virtual environment (recommended): `python -m venv deepeval_env`
     - Activate: Linux/Mac: `source deepeval_env/bin/activate`; Windows: `deepeval_env\Scripts\activate`.
  2. Install DeepEval: `pip install deepeval`
     - Installs core library (~100 MB, ~1-2 min on standard machines).
  3. Optional for Claude integration: Install Anthropic SDK: `pip install anthropic`.
  4. Set API key: Create `.env` in project root:
     ```
     ANTHROPIC_API_KEY=your_claude_api_key_here
     ```
     - Load in scripts: `from dotenv import load_dotenv; load_dotenv()`.

#### 5. Installation Instructions for Guardrails AI
- **Prerequisites**: Python 3.9+, pip. Internet for install; local execution after.
- **Steps**:
  1. Use same virtual env or create new: `python -m venv guardrails_env`.
     - Activate as above.
  2. Install Guardrails AI: `pip install guardrails-ai`
     - Installs library (~50 MB, ~1 min).
  3. Optional for Claude: Install Anthropic SDK: `pip install anthropic`. For LangChain chaining: `pip install langchain`.
  4. Set API key (same `.env` as above for Claude).

### Engineering Design

#### 1. High-Level Architecture
- **Components**:
  - **Native Hook (Bash)**: Your detect_speculation_and_fake_code.sh—first line with 21 patterns for lightweight checks.
  - **Wrapper Script (Python)**: Calls Guardrails AI (prevention), DeepEval (evaluation), and combines results. Inputs: Response text or file from Claude saves/commits.
  - **Tools**:
    - Guardrails AI: Runtime validator with RAIL spec (XML for regex/LLM checks).
    - DeepEval: Post-evaluation with G-Eval/HallucinationMetric for scores.
  - **Triggers**: Git pre-commit hook (commits/PRs); file watcher (saves).
  - **Alerts Module**: Python for console, desktop (notifypy), or optional Slack/email.
  - **Config**: YAML for patterns/thresholds (extend your 21 patterns).
- **Data Flow**:
  1. Trigger (save/commit/PR) → Native bash hook scans.
  2. Wrapper called: Guardrails validates (blocks fakes if critical).
  3. DeepEval evaluates (scores output).
  4. Combine results → Alerts/logs.
  5. Exit 0 (advisory) or block if configured.
- **Diagram (Text-Based)**:
  ```
  Trigger (Save/Commit/PR) --> Native Bash Hook (21 Patterns)
                                |
                                v
  Wrapper (Python) --> Guardrails (Prevention/Validation) --> DeepEval (Evaluation/Scoring)
                                |
                                v
  Results Combiner --> Alerts (Console/Desktop/Slack) --> Log File
  ```

#### 2. Detailed Design
- **Integration Points**:
  - **Claude Saves**: Use inotifywait (Linux: `apt install inotify-tools`) or watchdog (Windows: `pip install watchdog`) to monitor Claude output dir. On file change, pipe content to bash hook, which calls wrapper.
  - **Git Commits/PRs**: Pre-commit hook (.pre-commit-config.yaml) runs bash hook on staged files, invoking wrapper for DeepEval/Guardrails.
  - **Wrapper Logic**:
    - Bash hook runs first (lightweight regex for 21 patterns).
    - If no fakes, wrapper calls Guardrails (RAIL spec checks for placeholders/speculation).
    - DeepEval runs (G-Eval scores, e.g., threshold <0.5 = alert).
    - Combine outputs: If Guardrails throws exception or DeepEval scores low, alert with details (e.g., "Fake code: TODO found, Score: 0.3").
  - **Alerts**: Console default (e.g., "🚨 Fake Code Alert"). Add notifypy for desktop popups (`pip install notifypy`). Optional: Slack via slack-sdk or email via smtplib.
- **Error Handling**: Catch API failures (e.g., Claude key issues) with fallback to bash patterns. Log errors to /tmp/claude_detection_log.txt.
- **Performance Optimization**: Batch small files (<10 MB); parallel processing for multi-core (Python multiprocessing). Target <5s for small files.
- **Testing**: Red/green tests for patterns (extend your 900% improvement benchmark). Validate combined detection (aim 90%+ for obvious fakes).
- **Maintenance**: Modular—update DeepEval/Guardrails via pip; YAML for new patterns. Version control in Claude .claude/hooks/.

#### 3. Implementation Notes
- **Setup Time**: 15-30 min (installs: 5-10 min; config/scripts: 10-20 min).
- **Dependencies**: Python 3.9+, bash, git, gh CLI, jq (for existing hook), inotify-tools/watchdog for saves.
- **Scalability**: Handles 100s of PRs/month (your ~900 PRs benchmark). Low memory (~100 MB for tools).
- **Security**: Local execution; no data sharing. Sanitize inputs to avoid injection.
- **Customization**: YAML config to add your 21 patterns to RAIL/G-Eval. Adjust thresholds for sensitivity.

This design leverages your hook's strengths (lightweight, advisory) while adding OSS robustness, ensuring seamless Claude integration and high detection accuracy. If you need tweaks (e.g., specific alert formats), let me know!

