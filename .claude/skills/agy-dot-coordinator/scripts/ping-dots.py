#!/usr/bin/env python3
"""One scheduled model-written ping through the existing Dot tool; no retry loop."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request

REMINDER_OPENING = 'Inventory the work I asked for in the last 24 hours and verify what’s done versus not done.'

# Harness fix 2026-10-11 (revised): the reminder was one unstructured policy blob
# with no reply contract, so receiving Dots satisfied it with a reaction. It now carries
# labelled sections, an explicit standing-authority line, and a mandated reply format,
# while honouring the delivery contract: every original imperative phrase is preserved
# and the delivered message (body + attribution) stays within 1,200 bytes.
REMINDER_BODY = (
    'Inventory the work I asked for in the last 24 hours and verify what’s done versus not done.' + '\n\n'
    'AUTHORITY: standing owner-authorized scope; resume feasible work now; merge, destructive, credential actions need the owner.' + '\n\n'
    "NOW: resume authorized requests; recover outcome, durable checkpoint, acceptance gap; give owners safe next actions; avoid duplicate writers; check EACH last-24h request and older commitment for feasible alternate execution, validation or design work; do it. A publication hold needn't block safe testing/design. Local substeps and blocked work aren't completed user outcomes; honor explicit environments. Six useful tasks is a target, not permission; Owner-approved scope needs no re-approval." + '\n\n'
    'REPLY IN TEXT: STATUS: done/not-done. ACTIONS + PROOF: what you executed. Report commit URLs, PR URLs or artifacts as proof. BLOCKERS: action|cause|missing capability/approval|concrete unblock; if unchanged reply "Blockers unchanged from <dated receipt>". NEXT: your next executable step.' + '\n\n'
    'Never reply with only a reaction. Recheck on new evidence. Wait quietly only when all work is blocked, with exact blockers'
)
MAX_RESPONSE_CHARS = 2600  # the restructured body is ~1,900 chars; writers echo it back
PROMPT = (
    'Writer: return the recipient instructions below unchanged, at most {limit:,} characters. '
    'The recipient executes these instructions; you only relay the reminder. '
    'Return only those instructions, without a heading, attribution, or claims of progress.\n\n'
).format(limit=MAX_RESPONSE_CHARS) + REMINDER_BODY
HAIKU_MODEL = 'claude-haiku-5-5'
LUNA_MODEL = os.environ.get('LUNAROUTE_MODEL') or 'deepseek-4.1-flash'
MINIMAX_MODEL = 'MiniMax-M3.1-Flash-Preview'
MINIMAX_BASE_URL = 'https://api.minimax.io/anthropic'
# agy moved to last resort while quota-walled (owner directive 2026-10-11: use pi/lunaroute);
# it stays available so a recovered quota re-enables it without a code change.
PROVIDERS = ('luna', 'minimax', 'codex', 'gemini')
IDENTITIES = {'agy': 'AGY', 'luna': 'LunaRoute', 'minimax': 'MiniMax Claude',
              'gemini': 'Gemini direct',
              'codex': 'Codex', 'haiku': 'Claude Haiku'}


def bounded_run(command, stdin_text=None, timeout=180, cwd=None, env=None, check=True):
    """Run one command under a hard wall-clock bound covering the whole process tree.

    File-backed stdin: a child that never reads stdin cannot block the parent.
    On timeout the child's process group is killed: a surviving grandchild keeps
    the output pipe open and would otherwise block communicate() indefinitely,
    wedging every later provider fallback behind one hung call.
    """
    stdin_file = tempfile.TemporaryFile(mode='w+') if stdin_text is not None else None
    try:
        if stdin_file is not None:
            stdin_file.write(stdin_text)
            stdin_file.seek(0)
            stdin_arg = stdin_file
        else:
            stdin_arg = subprocess.DEVNULL
        process = subprocess.Popen(command, stdin=stdin_arg, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, cwd=cwd, env=env,
                                   start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                process.kill()
            process.communicate()
            raise
    finally:
        if stdin_file is not None:
            stdin_file.close()
    if check and process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command, stderr=stderr)
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def run_with_stdin(command, stdin_text, timeout=180, **kwargs):
    return bounded_run(command, stdin_text=stdin_text, timeout=timeout, **kwargs)


def claude_json(model, env=None):
    command = [shutil.which('claude') or 'claude', '--dangerously-skip-permissions',
               '--print', '--model', model, '--output-format', 'json',
               '--no-session-persistence', '--tools', '', '--disable-slash-commands', PROMPT]
    result = bounded_run(command, timeout=180, cwd='/tmp', env=env)
    response = json.loads(result.stdout)
    if (not isinstance(response, dict) or response.get('is_error') is not False
            or not isinstance(response.get('result'), str)):
        raise ValueError('Claude returned no successful result')
    return response['result']


# Dedicated env name: ~/.bashrc exports GEMINI_MODEL for the agy CLI, whose
# model aliases (e.g. gemini-3.6-flash-high) are not valid direct-API names.
GEMINI_MODEL = os.environ.get('COORDINATOR_GEMINI_MODEL') or 'gemini-3.8-flash'


def gemini_payload(prompt):
    return {'contents': [{'parts': [{'text': prompt}]}]}


def gemini_extract(body):
    try:
        text = body['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError, TypeError):
        raise ValueError('Gemini returned no text candidate')
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Gemini returned empty text')
    return text


def generate_gemini():
    """Direct Gemini API call (agy is quota-quarantined; owner directive 2026-10-12).

    Reads GEMINI_API_KEY (falling back to WORLDAI_DEV_GEMINI_API_KEY); the
    launchd/systemd wrapper sources ~/.bashrc so scheduled runs see the same key.
    """
    key = os.environ.get('GEMINI_API_KEY') or os.environ.get('WORLDAI_DEV_GEMINI_API_KEY')
    if not key:
        raise ValueError('GEMINI_API_KEY unavailable')
    request = urllib.request.Request(
        'https://generativelanguage.googleapis.com/v1beta/models/'
        + GEMINI_MODEL + ':generateContent',
        data=json.dumps(gemini_payload(PROMPT)).encode(),
        headers={'Content-Type': 'application/json', 'x-goog-api-key': key})
    with urllib.request.urlopen(request, timeout=180) as response:
        return gemini_extract(json.loads(response.read().decode()))


def generate(provider):
    if provider == 'gemini':
        return generate_gemini()

    if provider == 'agy':
        # Quota-quarantined per the owner directive 2026-10-12: never selected by
        # the automatic ladder; available only via --generator agy.
        command = [os.environ.get('COORDINATOR_AGY') or shutil.which('agy') or 'agy',
                   '--dangerously-skip-permissions', '--new-project', '--print-timeout', '180s',
                   '--input-format', 'stream-json', '--output-format', 'stream-json']
        request = json.dumps({'event': 'user', 'message': {'content': PROMPT}})+'\n'
        with tempfile.TemporaryDirectory(prefix='dot-ping-agy-', dir='/tmp') as workdir:
            result = run_with_stdin(command, request, cwd=workdir)
        events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        if any(not isinstance(event, dict) for event in events):
            raise ValueError('AGY returned malformed event data')
        results = [event.get('result') for event in events if event.get('event') == 'result']
        if (len(results) != 1 or not isinstance(results[0], dict)
                or results[0].get('status') != 'SUCCESS'):
            raise ValueError('AGY returned no single successful result')
        response = results[0].get('response')
        if not isinstance(response, str):
            raise ValueError('AGY returned no text response')
        return response

    if provider == 'luna':
        key = os.environ.get('LUNAROUTE_API_KEY') or bounded_run(
            [shutil.which('lunaroute') or 'lunaroute', 'key'], timeout=30).stdout.strip()
        if not key:
            raise ValueError('LunaRoute key unavailable')
        command = [shutil.which('pi') or 'pi', '--provider', 'lunaroute', '--model', LUNA_MODEL,
                   '--print', '--mode', 'text', '--no-session', '--no-tools', '--no-extensions',
                   '--no-skills', '--no-mcp', '--no-prompt-templates', PROMPT]
        result = bounded_run(command, timeout=180, cwd='/tmp',
                             env=dict(os.environ, LUNAROUTE_API_KEY=key))
        return result.stdout

    if provider == 'minimax':
        key = os.environ.get('MINIMAX_API_KEY')
        if not key:
            raise ValueError('MINIMAX_API_KEY unavailable')
        env = dict(os.environ, ANTHROPIC_BASE_URL=MINIMAX_BASE_URL, ANTHROPIC_AUTH_TOKEN=key,
                   ANTHROPIC_MODEL=MINIMAX_MODEL)
        env.pop('ANTHROPIC_API_KEY', None)
        return claude_json(MINIMAX_MODEL, env)

    if provider == 'codex':
        generator = os.environ.get('COORDINATOR_GENERATOR') or shutil.which('codex-luna') or shutil.which('codex') or 'codex'
        command = [generator]
        if Path(generator).name != 'codex-luna':
            command += ['exec', '--yolo', '-m', 'gpt-6-luna']
        with tempfile.TemporaryDirectory(prefix='dot-ping-codex-', dir='/tmp') as workdir:
            with tempfile.NamedTemporaryFile(mode='r+', dir=workdir, prefix='message-') as output:
                run_with_stdin(command + ['--ephemeral', '--skip-git-repo-check',
                                          '--config', 'project_doc_max_bytes=0',
                                          '--output-last-message', output.name], PROMPT,
                               cwd=workdir)
                output.seek(0)
                return output.read()

    if provider == 'haiku':
        return claude_json(HAIKU_MODEL)

    raise ValueError('Unknown generator: '+provider)


def generate_message(providers):
    for provider in providers:
        try:
            message = generate(provider)
            if not isinstance(message, str):
                raise ValueError('response is not text')
            stripped = message.strip()
            if not stripped:
                raise ValueError(
                    f'response empty after trimming ({len(message):,} raw characters)'
                )
            if len(stripped) > MAX_RESPONSE_CHARS:
                raise ValueError(
                    f'response exceeds {MAX_RESPONSE_CHARS:,} characters '
                    f'({len(stripped):,} stripped; {len(message):,} raw)'
                )
            collapse = lambda text: ' '.join(text.replace('’', "'").split())
            if not stripped.startswith(REMINDER_OPENING):
                raise ValueError('response does not begin with the required inventory sentence')
            if collapse(stripped) != collapse(REMINDER_BODY):
                raise ValueError('response changed the required recovery instructions')
            # Content-exact but layout-tolerant; deliver the canonical body so
            # wording (not writer formatting) is byte-stable.
            stripped = REMINDER_BODY
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            print(provider+' generation failed: '+str(error), file=sys.stderr)
            if isinstance(error, subprocess.CalledProcessError) and error.stderr:
                print(error.stderr[:4000], file=sys.stderr)
            continue
        print('Generation succeeded with '+provider)
        return provider, stripped
    raise ValueError('All generation providers failed; no Dot send')


# Colon-formed labels only: bare words caused false-positive 'compliance'.
STATUS_MARKERS = ('STATUS:', 'ACTIONS + PROOF:', 'BLOCKERS:', 'NEXT:')

# Harness fix 2026-10-11: one explicit text-demanding escalation is already
# empirically proven to convert an emoji-only Dot into substantive work.
ESCALATION_BODY = (
    'Your last coordinator reminder received no text reply, and a reaction is not a receipt. '
    'Reply in text now in exactly this format: STATUS: inventory of done versus not done. '
    'ACTIONS + PROOF: what you executed, with commit URLs, PR URLs or artifact names. '
    'BLOCKERS: blocked action | cause | missing capability or approval | concrete unblock; if unchanged reply "Blockers unchanged from <dated receipt>" and name the affected tasks. '
    'NEXT: your next executable step. This is standing owner-authorized scope: resume feasible work now instead of waiting; merge, destructive and credential gates still need the owner. '
    'Do not reply with an emoji or a reaction.'
)


def classify_response(page_text):
    """Classify the Dot reply to the most recent reminder from the page tail.

    Returns compliant, reaction_only, unstructured_text or no_response.
    A compliant reply carries at least two required reply labels (or the
    unchanged-blockers line); a short body after the reminder is a reaction.
    """
    if not isinstance(page_text, str) or not page_text.strip():
        return 'no_response'
    idx = page_text.rfind(REMINDER_OPENING)
    if idx == -1:
        return 'no_response'
    after = page_text[idx + len(REMINDER_OPENING):]
    cut = after.find('coordinator: automated reminder; no new authority.')
    if cut != -1:
        after = after[cut + len('coordinator: automated reminder; no new authority.'):]
    body = ' '.join(after.split())
    if not body:
        return 'no_response'
    hits = sum(1 for marker in STATUS_MARKERS if marker in body)
    if 'Blockers unchanged' in body or hits >= 2:
        return 'compliant'
    if len(body) < 300:
        return 'reaction_only'
    return 'unstructured_text'


def read_tail(dot, account, env, chars=12000, timeout=180):
    result = bounded_run([dot, '--account', account, 'read', str(chars)],
                         timeout=timeout, env=env, check=False)
    return result.stdout


def read_and_classify(dot, account, env, windows=None):
    """Classify the reply, widening the read window before concluding no_response.

    A busy Dot can push the reminder beyond a small page tail (observed: 10,040
    characters on worldarchitect, producing false no_response verdicts and
    spurious escalations). Only the largest window may return no_response.
    """
    if windows is None:
        windows = tuple(int(n) for n in
                        os.environ.get('COORDINATOR_READ_WINDOWS', '12000,40000').split(','))
    verdict = 'no_response'
    for chars in windows:
        verdict = classify_response(read_tail(dot, account, env, chars=chars))
        if verdict != 'no_response':
            return verdict
    return verdict


def verify_and_escalate(dot, account, env, provider, state_file, wait_secs=180, recheck_secs=120):
    """Check the reply after a verified send and escalate once when it is not compliant.

    A Dot still reasoning is common (3-6 minutes), so a first-check
    no_response/reaction_only is re-checked after recheck_secs before any
    escalation; only a persistently non-compliant reply escalates.
    """
    time.sleep(min(max(wait_secs, 0), 900))
    verdict = read_and_classify(dot, account, env)
    if verdict != 'compliant' and recheck_secs > 0:
        time.sleep(min(max(recheck_secs, 0), 600))
        verdict = read_and_classify(dot, account, env)
    record = {}
    if state_file.exists():
        try:
            record = json.loads(state_file.read_text())
        except (OSError, ValueError):
            record = {}
    record['last_response_status'] = verdict
    record['last_response_checked_epoch'] = int(time.time())
    if verdict == 'compliant':
        record['consecutive_noncompliance'] = 0
        print(account + ': response compliant')
    else:
        identity = IDENTITIES.get(provider, 'Coordinator')
        with tempfile.NamedTemporaryFile(mode='w+', prefix='dot-escalation-', dir='/tmp') as file:
            file.write(ESCALATION_BODY + '\nFrom ' + identity +
                       ' coordinator: automated escalation; no new authority.')
            file.flush()
            sent = bounded_run([dot, '--account', account, 'send-once', file.name],
                               timeout=180, env=env, check=False)
        escalated = sent.returncode == 0 and 'DOT_SENT_VERIFIED' in sent.stdout.splitlines()
        record['escalation_sent_epoch'] = int(time.time())
        record['escalation_verified'] = escalated
        record['consecutive_noncompliance'] = int(record.get('consecutive_noncompliance', 0)) + 1
        print(account + ': response ' + verdict + '; escalation ' +
              ('sent' if escalated else 'not verified'))
    state_file.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
    return verdict


def delivery_message(provider, message):
    if message != REMINDER_BODY:
        raise ValueError('The complete required recovery instructions must be delivered')
    identity = IDENTITIES[provider]
    return message + '\nFrom ' + identity + ' coordinator: automated reminder; no new authority.'


def due_account(accounts, role, now):
    offsets = (0, 20, 40) if role == 'mac' else (30, 50, 10)
    local = time.localtime(now)
    now = local.tm_min*60 + local.tm_sec
    return next((account for account, minute in zip(accounts, offsets)
                 if 0 <= (now-minute*60) % 3600 <= 120), None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--account', help='One configured account; otherwise use this host’s due slot')
    parser.add_argument('--generator', choices=('auto',)+tuple(IDENTITIES), default='auto')
    parser.add_argument('--generate-only', action='store_true', help='Generate and print one message without sending')
    args = parser.parse_args()
    config = json.loads(Path(os.environ.get('DOT_CONFIG_FILE', '~/.config/dot/config.json')).expanduser().read_text())
    accounts = config.get('rotation') or list(config.get('accounts', {}))
    if not isinstance(accounts, list) or len(accounts) != 3 or len(set(accounts)) != 3:
        raise ValueError('Configure exactly three distinct Dot account keys')
    role = 'mac' if platform.system() == 'Darwin' else 'linux'
    account = args.account or due_account(accounts, role, time.time())
    if account is None:
        print('No account due; no send')
        return 0
    if account not in accounts:
        raise ValueError('Unknown configured account')
    state = Path(os.environ.get('COORDINATOR_STATE_DIR', '~/.local/state/ai.gemini.agy-dot-coordinator')).expanduser()
    state.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = Path(os.environ.get('COORDINATOR_LOCK_FILE', '/tmp/ai.gemini.agy-dot-coordinator.lock'))
    with lock_path.open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Another ping is running; no send')
            return 0
        if (state/'STOP').exists():
            print('STOP is present; no send')
            return 0
        for path in (state/'state.json', state/('state_'+account+'.json')):
            if path.exists():
                record = json.loads(path.read_text())
                record = record.get('accounts', {}).get(account, record)
                if record.get('delivery_unverified') or str(record.get('last_status', '')).startswith('UNVERIFIED_SEND'):
                    print(account+': existing delivery hold; no send')
                    return 0
        providers = PROVIDERS if args.generator == 'auto' else (args.generator,)
        provider, message = generate_message(providers)
        if args.generate_only:
            print(message)
            return 0
        if (state/'STOP').exists():
            print('STOP is present; no send')
            return 0
        env = dict(os.environ, DOT_ROTATE_ON_LIMIT='0')
        for key in ('DOT_REMOTE_HOST', 'DOT_CHROME_USER_DATA', 'DOT_URL', 'DOT_CLEAR_DRAFT'):
            env.pop(key, None)
        dot = os.environ.get('COORDINATOR_DOT_SCRIPT', str(Path(__file__).resolve().parents[2]/'dot/scripts/dot.sh'))
        with tempfile.NamedTemporaryFile(mode='w+', prefix='dot-ping-', dir='/tmp') as file:
            file.write(delivery_message(provider, message))
            file.flush()
            sent = bounded_run([dot, '--account', account, 'send-once', file.name],
                               timeout=180, env=env, check=False)
        sys.stdout.write(sent.stdout)
        sys.stderr.write(sent.stderr)
        verified = sent.returncode == 0 and 'DOT_SENT_VERIFIED' in sent.stdout.splitlines()
        if not verified:
            print(account+': send not verified; inspect the existing Dot tool before retrying')
            return 1
        print(account+': sent')
        if os.environ.get('COORDINATOR_VERIFY_RESPONSE', '1') == '1':
            verify_and_escalate(dot, account, env, provider,
                                state/('state_'+account+'.json'),
                                wait_secs=int(os.environ.get('COORDINATOR_RESPONSE_WAIT_SECS', '180')),
                                recheck_secs=int(os.environ.get('COORDINATOR_RESPONSE_RECHECK_SECS', '120')))
        return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print('Dot ping failed: '+str(error), file=sys.stderr)
        raise SystemExit(1)
