#!/usr/bin/env python3
"""Regression tests for the reminder reply contract and compliance loop.

Incident (2026-10-11): the coordinator sent a ~1,100-character unstructured
policy blob with no reply contract and no response verification. Receiving Dots
satisfied it with an emoji reaction for three consecutive cycles; one explicit
text-demanding message produced substantive work immediately. These tests pin the
harness fix: labelled reminder sections with a mandated reply format, a
layout-tolerant content-exact generation contract, and reply classification.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'ping-dots.py'


def load_module():
    spec = importlib.util.spec_from_file_location('ping_dots', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = load_module()
FAILURES = []


def check(name, condition):
    if condition:
        print(f"  ok - {name}")
    else:
        print(f"  FAIL - {name}")
        FAILURES.append(name)


# --- reminder contract ---
check("body fits the generation cap", len(m.REMINDER_BODY) <= m.MAX_RESPONSE_CHARS)
check("body starts with the mandated inventory sentence",
      m.REMINDER_BODY.startswith(m.REMINDER_OPENING))
check("body mandates the reply labels",
      all(label in m.REMINDER_BODY for label in ('STATUS:', 'ACTIONS + PROOF:', 'BLOCKERS:', 'NEXT:')))
check("body states standing authorization",
      'standing owner-authorized scope' in m.REMINDER_BODY)
check("body preserves every original imperative",
      all(text in m.REMINDER_BODY for text in (
          'Resume unfinished authorized requests', 'avoid duplicate writers',
          'Use cloud coders', 'Six useful tasks is a target',
          'preserve cancellations', 'wait quietly only when all such work is blocked')))
check("delivery appends the no-new-authority attribution",
      m.delivery_message('luna', m.REMINDER_BODY).endswith(
          'From LunaRoute coordinator: automated reminder; no new authority.'))
check("luna is primary, direct Gemini replaces agy, and agy is quarantined from the ladder",
      m.PROVIDERS[0] == 'luna' and 'gemini' in m.PROVIDERS and 'agy' not in m.PROVIDERS)

# --- direct Gemini provider (agy quota quarantine, owner directive 2026-10-12) ---
check("gemini model ignores the agy-CLI GEMINI_MODEL alias",
      m.GEMINI_MODEL == os.environ.get("COORDINATOR_GEMINI_MODEL", "gemini-3.8-flash"))

check("gemini payload shape", m.gemini_payload('hi') == {'contents': [{'parts': [{'text': 'hi'}]}]})
check("gemini extract happy path",
      m.gemini_extract({'candidates': [{'content': {'parts': [{'text': 'hello'}]}}]}) == 'hello')
for bad in ({}, {'candidates': []}, {'candidates': [{}]},
            {'candidates': [{'content': {'parts': [{'text': '  '}]}}]}):
    try:
        m.gemini_extract(bad)
        check(f"gemini extract rejects {str(bad)[:20]}", False)
    except ValueError:
        check(f"gemini extract rejects {str(bad)[:20]}", True)
saved = dict(os.environ)
os.environ.pop('GEMINI_API_KEY', None)
os.environ.pop('WORLDAI_DEV_GEMINI_API_KEY', None)
try:
    m.generate_gemini()
    check("gemini provider fails cleanly without a key", False)
except ValueError as error:
    check("gemini provider fails cleanly without a key", 'GEMINI_API_KEY unavailable' in str(error))
os.environ.clear(); os.environ.update(saved)

# --- layout-tolerant generation contract ---
collapse = lambda t: ' '.join(t.replace('\u2019', "'").split())
reformatted = m.REMINDER_BODY.replace('\n\n', '\n').replace('  ', ' ')
check("reformatted echo passes the content-exact contract", collapse(reformatted) == collapse(m.REMINDER_BODY))
check("altered text fails the content-exact contract",
      collapse(m.REMINDER_BODY.replace('wait quietly only when', 'whenever you feel like it,')) != collapse(m.REMINDER_BODY))

# --- reply classification (the historical failure) ---
reminder = m.REMINDER_BODY + '\nFrom LunaRoute coordinator: automated reminder; no new authority.'
check("reaction-only reply is non-compliant",
      m.classify_response(reminder + '\n\U0001f440') == 'reaction_only')
check("empty tail is no_response", m.classify_response('') == 'no_response')
check("unrelated text is no_response",
      m.classify_response('no reminder present in this tail') == 'no_response')
check("full contract reply is compliant",
      m.classify_response(reminder + '\nSTATUS: x\nACTIONS + PROOF: y\nBLOCKERS: none\nNEXT: z') == 'compliant')
check("unchanged-blockers line is compliant",
      m.classify_response(reminder + '\nBlockers unchanged from 3:39 PM receipt') == 'compliant')
check("long unlabelled text is unstructured_text",
      m.classify_response(reminder + '\n' + 'word ' * 120) == 'unstructured_text')
check("escalation body forbids reactions and demands the contract",
      'Do not reply with an emoji' in m.ESCALATION_BODY
      and all(label in m.ESCALATION_BODY for label in ('STATUS:', 'ACTIONS + PROOF:', 'BLOCKERS:', 'NEXT:')))

print()
print(f"fail={len(FAILURES)}")
if FAILURES:
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("all reminder-compliance checks passed")

# --- escalation path (deterministic, fake dot transport) ---
import os
import stat
import tempfile

def make_fake_dot(workdir, tail_text):
    path = Path(workdir) / 'fake-dot.sh'
    path.write_text(
        '#!/usr/bin/env bash\n'
        'if [[ "$1" == "--account" ]]; then shift 2; fi\n'
        'case "$1" in\n'
        '  read) printf "%s" "$FAKE_TAIL" ;;\n'
        '  send-once) cp "$2" "$FAKE_ESCALATION_CAPTURE"; echo DOT_SENT_VERIFIED ;;\n'
        'esac\n'
        'exit 0\n'
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path

with tempfile.TemporaryDirectory() as workdir:
    state_file = Path(workdir) / 'state_test.json'
    capture = Path(workdir) / 'escalation.txt'
    env = dict(os.environ, FAKE_TAIL=reminder + '\n\U0001f440',
               FAKE_ESCALATION_CAPTURE=str(capture))
    verdict = m.verify_and_escalate(make_fake_dot(workdir, ''), 'test', env, 'luna',
                                   state_file, wait_secs=0)
    recorded = json.loads(state_file.read_text())
    check("reaction-only reply escalates", verdict == 'reaction_only')
    check("escalation was actually sent", capture.exists() and 'DOT' in capture.read_text() or capture.exists())
    check("escalation demands the contract in text",
          capture.exists() and 'Do not reply with an emoji' in capture.read_text())
    check("state records the non-compliance and escalation",
          recorded.get('last_response_status') == 'reaction_only'
          and recorded.get('escalation_verified') is True
          and recorded.get('consecutive_noncompliance') == 1)
    # slow-but-compliant reply: first read reacts, re-check returns the contract -> no escalation
    state_file3 = Path(workdir) / 'state_test3.json'
    capture3 = Path(workdir) / 'escalation3.txt'
    slow_dot = Path(workdir) / 'slow-dot.sh'
    slow_dot.write_text(
        '#!/usr/bin/env bash\n'
        'if [[ "$1" == "--account" ]]; then shift 2; fi\n'
        'if [[ "$1" == "read" ]]; then\n'
        '  n=$(cat "$FAKE_COUNTER" 2>/dev/null || echo 0)\n'
        '  n=$((n+1)); echo $n > "$FAKE_COUNTER"\n'
        '  if [[ $n -eq 1 ]]; then printf "%s" "$FAKE_TAIL_FIRST"; else printf "%s" "$FAKE_TAIL_SECOND"; fi\n'
        'elif [[ "$1" == "send-once" ]]; then cp "$2" "$FAKE_ESCALATION_CAPTURE"; echo DOT_SENT_VERIFIED\n'
        'fi\nexit 0\n')
    slow_dot.chmod(slow_dot.stat().st_mode | stat.S_IEXEC)
    env3 = dict(os.environ, FAKE_COUNTER=str(Path(workdir) / 'counter'),
                FAKE_TAIL_FIRST=reminder + '\n\U0001f440',
                FAKE_TAIL_SECOND=reminder + '\nSTATUS: x\nACTIONS + PROOF: y\nBLOCKERS: none\nNEXT: z',
                FAKE_ESCALATION_CAPTURE=str(capture3))
    verdict3 = m.verify_and_escalate(slow_dot, 'test', env3, 'luna', state_file3,
                                     wait_secs=0, recheck_secs=1)
    check("slow-but-compliant reply (re-check path) does not escalate",
          verdict3 == 'compliant' and not capture3.exists())

    # busy-account false negative: reminder beyond the small window is found at the wide one
    state_file4 = Path(workdir) / 'state_test4.json'
    capture4 = Path(workdir) / 'escalation4.txt'
    busy_dot = Path(workdir) / 'busy-dot.sh'
    busy_dot.write_text(
        '#!/usr/bin/env bash\n'
        'if [[ "$1" == "--account" ]]; then shift 2; fi\n'
        'if [[ "$1" == "read" ]]; then\n'
        '  if [[ "${2:-0}" -ge 30000 ]]; then printf "%s" "$FAKE_TAIL_WIDE"; else printf "%s" "$FAKE_TAIL_NARROW"; fi\n'
        'elif [[ "$1" == "send-once" ]]; then cp "$2" "$FAKE_ESCALATION_CAPTURE"; echo DOT_SENT_VERIFIED\n'
        'fi\nexit 0\n')
    busy_dot.chmod(busy_dot.stat().st_mode | stat.S_IEXEC)
    env4 = dict(os.environ, FAKE_TRAFFIC='x '*3000,
                FAKE_TAIL_NARROW='busy traffic only, reminder scrolled out',
                FAKE_TAIL_WIDE=reminder + '\nSTATUS: x\nACTIONS + PROOF: y\nBLOCKERS: none\nNEXT: z',
                FAKE_ESCALATION_CAPTURE=str(capture4))
    verdict4 = m.verify_and_escalate(busy_dot, 'test', env4, 'luna', state_file4,
                                     wait_secs=0, recheck_secs=0)
    check("busy account: wide-window read finds the compliant reply without escalating",
          verdict4 == 'compliant' and not capture4.exists()
          and json.loads(state_file4.read_text()).get('last_response_status') == 'compliant')

    # compliant reply must NOT escalate
    state_file2 = Path(workdir) / 'state_test2.json'
    capture2 = Path(workdir) / 'escalation2.txt'
    compliant_tail = (reminder + '\nSTATUS: x\nACTIONS + PROOF: y\nBLOCKERS: none\nNEXT: z')
    env2 = dict(os.environ, FAKE_TAIL=compliant_tail, FAKE_ESCALATION_CAPTURE=str(capture2))
    verdict2 = m.verify_and_escalate(make_fake_dot(workdir, ''), 'test', env2, 'luna',
                                     state_file2, wait_secs=0)
    recorded2 = json.loads(state_file2.read_text())
    check("compliant reply does not escalate",
          verdict2 == 'compliant' and not capture2.exists()
          and recorded2.get('consecutive_noncompliance') == 0)
