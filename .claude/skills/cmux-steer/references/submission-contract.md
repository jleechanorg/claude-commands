# Targeted submission and evidence

Use after resolving an authorized target with the cmux-steer workflow. The
contract applies to cmux-goal's composer fallback as well. Validate these
commands against the installed CLI; these are retained source contracts, not
an assertion that every version implements them.

## Type and submit in one call

Headless only (see `../SKILL.md` § "Headless only"; measured in `/tmp/spicy-search/cmux/focus-test.md`): send the text with its trailing `\n` (Enter) — via the socket `surface.send_text` below, or `cmux send` + `cmux send-key enter`. Both were measured NOT to change the operator's selected workspace. Build the JSON with a supported process-argument API or safely quoted shell variable. Never interpolate an untrusted title, path, or prompt into shell source or hand-built JSON.

```bash
# SURFACE_UUID is freshly resolved; TEXT is the approved payload (without the trailing newline).
printf '{"method":"surface.send_text","params":{"surface_id":"%s","text":"%s\\n"}}\n' "$SURFACE_UUID" "$TEXT" \
  | nc -U -w 3 "${CMUX_SOCKET_PATH:-/Users/jleechan/.local/state/cmux/cmux.sock}"
```

Inspect the response (`ok`, `queued`) before continuing. If it clearly failed,
diagnose the failure. If its result is uncertain, inspect the target before
repeating text. A successful response proves only socket acceptance, not that
the intended program consumed the input.

After the send, allow the target a brief opportunity to respond (the source
workflow used roughly 5-15 seconds), then read the same target headlessly:

```bash
cmux capture-pane --workspace "$WS_REF" --surface "$SURFACE_UUID" --lines 25
```

## What counts as evidence

- **Submitted:** a response tied to the new payload, an unambiguous new turn,
  or direct persisted state showing the requested builtin took effect.
- **Working:** a new processing indicator can corroborate consumption when
  it began after this submission and is attributable to this payload. An old
  or unrelated spinner is not proof, and no spinner alone proves completion.
- **Not submitted:** the complete intended text is visibly still in the
  untouched composer and has not been consumed.
- **Unverified/blocked:** target identity, input state, or post-send routing is
  uncertain. Report that uncertainty rather than retyping the payload.

## Bounded recovery

If the text is demonstrably still in the intended input, there is no new
response, and no intervening draft appeared, one additional targeted Enter
is allowed within the existing send authorization. Re-read afterward.
Do not re-send the text when consumption is ambiguous. If a retry is still
unconfirmed, stop sending and report the exact observed blocker.

Never blindly press Enter on a shell prompt or approval dialog. Never replay
a command that could duplicate a transaction, publication, commit, process
launch, or external message. Re-entering any payload requires evidence the
first typing did not land and that the same action remains authorized.

## Privacy-preserving receipt

Keep the receipt small and sufficient to distinguish typed from submitted:
target window/workspace/surface, payload purpose or non-sensitive excerpt,
Enter sent or not, observed matching response, and verification status.
Retain an exact payload in private task-local evidence only when needed and
permitted. There is no blanket obligation to copy the full terminal or other
agent's conversation to a user-visible message or outside service.
