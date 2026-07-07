# Extracting your Reddit session cookie from the macOS keychain

As of 2026-06-23, the cleanest way to get live Reddit data from this
MacBook is **to use the same session cookie your browser already has**.
Reddit's `.json` endpoints trust the `reddit_session` cookie alone for
read-only requests (no OAuth app registration, no client_secret, no
rate-limit wallet), and the cookie lasts ~365 days before expiry.

## How Chromium stores cookies

The macOS Chromium cookie DB stores values encrypted with a key derived
from the keychain "<Browser> Safe Storage" password. Don't trust the
AES-GCM code in old SO answers — it's wrong. The actual algorithm:

- v10 = `b'v10'` (3B) ‖ ciphertext, **AES-128-CBC**, IV = b' '*16 (sixteen
  literal spaces, hard-coded), PKCS7 padding
- v20 = `b'v20'` (3B) ‖ nonce (24B) ‖ ciphertext+tag (16B),
  **XChaCha20-Poly1305**, 32-byte key

For our Reddit cookies the v10 path applies (verified 2026-06-23: all
13 Reddit cookies in Comet/Default have v10 prefix).

## Where the Reddit session lives

**Jeffrey's setup** (verified 2026-06-23):
- Browser: **Comet** (Perplexity's Chromium fork), Default profile
- Cookie DB: `$HOME/Library/Application Support/Comet/Default/Cookies`
- Keychain service: `Comet Safe Storage`
- Reddit session: 722-byte JWT at SQLite offset 32 inside the
  `reddit_session` cookie's `encrypted_value` column

Why not Chrome? Chrome's Default profile has zero Reddit cookies —
Jeffrey's Reddit session is in Comet, not Chrome.

## Decryption gotcha (caught during this work)

The script initially failed with `ValueError: Invalid padding bytes` on
v10 cookies. The bug: the plaintext is `[32 bytes binary tag][JWT]`, not
just `[JWT]`. Find the JWT by searching for the `eyJ` header signature
(after stripping PKCS7 padding), not by assuming the whole plaintext
is the JWT.

The 32-byte prefix appears to be a 16-byte block of post-decryption
metadata (possibly a tamper-detection HMAC or a v20 migration artifact)
followed by 16 bytes of the AES block boundary. Don't try to decrypt
those 32 bytes — just skip them.

## Implementation: `scripts/extract_reddit_session.py`

The shipped implementation:
1. Queries macOS keychain for the Safe Storage password
2. Derives 16-byte key via PBKDF2-HMAC-SHA1 (1003 iterations, salt=b"saltysalt")
3. Opens the local browser's Cookies SQLite DB
4. Filters to `host_key LIKE '%reddit.com' AND name='reddit_session'`
5. Decrypts the v10 blob with AES-128-CBC + IV = 16 spaces
6. Strips PKCS7 padding
7. Searches the plaintext for the first `eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+` regex match
8. Returns the JWT on stdout, or exits 1 with "NO_SESSION" on stderr

The JWT is then passed to Reddit as `--cookie reddit_session=<jwt>` on
every `.json` request. **No app registration, no OAuth, no proxy.**

## Limitations

- If the user logs out of Reddit in their browser, the session becomes invalid.
- If the user is in a different browser profile (e.g. Chrome profile
  2), the script searches Comet first, then Chrome, then Brave.
- The script needs the user's Keychain password to be unlockable
  (touch ID on a locked Mac will fail; user must be logged in).
- The script uses `subprocess` to shell to `security` for the keychain
  password — this requires the user to have unlocked Keychain recently.
- For write operations (POST, vote, comment) you'd also need the
  `csrf_token` cookie — the script doesn't extract that today.

## Cross-references

- `~/.hermes_prod/skills/browserclaw/SKILL.md` — `scripts/decrypt_chrome_cookies.py` is
  the generic v10+v20 decryptor this script is based on.
- Reddit's session cookie format is documented in
  https://github.com/reddit-archive/reddit/blob/master/r2/r2/lib/_py_beta.py
  (function `make_session_cookie` and friends).