"""Tests for browserclaw.cookies — Chrome cookie decryption on macOS.

These tests build a tiny Chromium-format Cookies SQLite DB in a tmpdir,
encrypt a known cookie with the real Chromium key derivation (PBKDF2-HMAC-SHA1
+ AES-128-CBC + v10 prefix + DB v24 SHA256(domain) prefix), then decrypt
with `decrypt_chrome_cookies` and assert roundtrip equality.

Tests run on macOS only (uses Keychain) but skip cleanly on other platforms.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sqlite3
import tempfile
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from browserclaw.cookies import (
    Cookie,
    _chrome_expires_to_unix,
    decrypt_chrome_cookies,
    derive_aes_key,
    keychain_password,
    read_cookies_json,
    write_cookies_json,
)

PBKDF2_SALT = b"saltysalt"
PBKDF2_ITERATIONS = 1003
CBC_IV = b" " * 16
PASSWORD = b"GN6oxTvweY8PJsg6ER8KRA=="
HOST = ".slack.com"
NAME = "d"
VALUE = "xoxd-iY2SQ6X3yzw48c+abh+DUuSolHzhiAoVTIJTlf4SyDzpFL"


def _encrypt_chrome_value(plaintext: bytes, aes_key: bytes, host: str, db_version: int) -> bytes:
    """Reproduce Chromium's OSCrypt encrypt-with-host-tagging for DB v24+.

    For DB v24+, the SHA256(host) prefix lives INSIDE the encrypted plaintext,
    BEFORE the actual cookie value. Layout:

        v10 || AES-CBC( SHA256(host) || PKCS7-pad(plaintext) )

    This matches what real Chrome emits on disk for v24+ cookies — verified
    against the live `~/Library/Application Support/Google/Chrome/Default/Cookies`
    on macOS.
    """
    import hashlib

    body = plaintext
    if db_version >= 24:
        body = hashlib.sha256(host.encode("utf-8")).digest() + body
    pad_len = 16 - (len(body) % 16)
    padded = body + bytes([pad_len]) * pad_len
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(CBC_IV))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return b"v10" + ciphertext


def _build_cookie_db(db_path: Path, plaintext: bytes, host: str, name: str, db_version: int = 24) -> bytes:
    """Write a minimal Chromium Cookies SQLite DB with one encrypted cookie."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "create table meta (key text primary key, value text)"
        )
        conn.execute("insert into meta (key, value) values ('version', ?)", (str(db_version),))
        conn.execute(
            "create table cookies ("
            "  host_key text, name text, path text, expires_utc integer,"
            "  is_secure integer, is_httponly integer, samesite integer,"
            "  encrypted_value blob"
            ")"
        )
        aes_key = derive_aes_key(PASSWORD)
        encrypted = _encrypt_chrome_value(plaintext, aes_key, host, db_version)
        # Chromium expires_utc: pick something 30 days out in Windows file time.
        import time
        unix_future = int(time.time()) + 30 * 86400
        win_ft = int((unix_future + 11644473600) * 1_000_000)
        conn.execute(
            "insert into cookies values (?, ?, ?, ?, ?, ?, ?, ?)",
            (host, name, "/", win_ft, 1, 1, 1, encrypted),
        )
        conn.commit()
    finally:
        conn.close()
    return encrypted


@pytest.fixture
def fake_cookie_db(tmp_path: Path) -> Path:
    db = tmp_path / "Cookies"
    _build_cookie_db(db, VALUE.encode("utf-8"), HOST, NAME)
    return db


def test_derive_aes_key_matches_chromium():
    """PBKDF2-HMAC-SHA1(saltysalt, 1003) → 16-byte AES key, deterministic."""
    k1 = derive_aes_key(PASSWORD)
    k2 = derive_aes_key(PASSWORD)
    assert k1 == k2
    assert len(k1) == 16


def test_keychain_password_uses_security_cli(monkeypatch):
    """keychain_password should invoke `security find-generic-password`."""
    if platform.system() != "Darwin":
        pytest.skip("Keychain is macOS-only")

    calls: list[list[str]] = []

    import subprocess
    import browserclaw.cookies as cookies_mod

    def fake_check_output(cmd, stderr=None):
        calls.append(cmd)
        return b"GN6oxTvweY8PJsg6ER8KRA=="

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    pw = keychain_password()
    assert pw == b"GN6oxTvweY8PJsg6ER8KRA=="
    assert calls and calls[0][:4] == ["security", "find-generic-password", "-s", "Chrome Safe Storage"]
    assert "-a" in calls[0]
    assert "Chrome" in calls[0]


def test_decrypt_chrome_cookies_roundtrip(fake_cookie_db: Path, monkeypatch):
    """Decrypt a cookie we just encrypted with the same key derivation."""
    if platform.system() != "Darwin":
        pytest.skip("macOS only (uses Keychain lookup)")

    # Stub out keychain_password so we don't actually hit Keychain.
    import browserclaw.cookies as cookies_mod
    monkeypatch.setattr(cookies_mod, "keychain_password", lambda *a, **k: PASSWORD)

    cookies = decrypt_chrome_cookies(fake_cookie_db, domain_filter="%slack.com%")
    assert len(cookies) == 1
    c = cookies[0]
    assert c.name == NAME
    assert c.value == VALUE
    assert c.domain == HOST
    assert c.path == "/"
    assert c.secure is True
    assert c.httpOnly is True
    assert c.sameSite == "Lax"
    assert c.expires > 0


def test_decrypt_chrome_cookies_missing_db(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "browserclaw.cookies.keychain_password", lambda *a, **k: PASSWORD
    )
    with pytest.raises(Exception) as excinfo:
        decrypt_chrome_cookies(tmp_path / "does-not-exist")
    assert "Cookie DB not found" in str(excinfo.value)


def test_decrypt_chrome_cookies_empty_db(tmp_path: Path, monkeypatch):
    """Empty file is Chrome holding the exclusive lock — not an error to copy, but unreadable."""
    empty = tmp_path / "empty.sqlite"
    empty.write_bytes(b"")
    monkeypatch.setattr(
        "browserclaw.cookies.keychain_password", lambda *a, **k: PASSWORD
    )
    with pytest.raises(Exception) as excinfo:
        decrypt_chrome_cookies(empty)
    msg = str(excinfo.value)
    assert "empty" in msg.lower() or "not a database" in msg.lower()


def test_decrypt_chrome_cookies_non_chromium_db(tmp_path: Path, monkeypatch):
    """A SQLite file that isn't a Chromium Cookies DB should raise a clear error."""
    db = tmp_path / "fake.sqlite"
    conn = sqlite3.connect(db)
    conn.execute("create table other (x integer)")
    conn.execute("insert into other values (1)")
    conn.commit()
    conn.close()
    monkeypatch.setattr(
        "browserclaw.cookies.keychain_password", lambda *a, **k: PASSWORD
    )
    from browserclaw.cookies import CookieDecryptError
    with pytest.raises(CookieDecryptError) as excinfo:
        decrypt_chrome_cookies(db)
    assert "not a Chromium Cookies DB" in str(excinfo.value)


def test_decrypt_chrome_cookies_skips_bad_row(tmp_path: Path, monkeypatch):
    """A single malformed ciphertext must NOT abort the whole decrypt pass."""
    db = tmp_path / "Cookies"
    import time

    import browserclaw.cookies as cookies_mod

    # One good cookie, then one with a truncated (non-block-aligned) ciphertext.
    _build_cookie_db(db, VALUE.encode("utf-8"), HOST, NAME)
    conn = sqlite3.connect(db)
    conn.execute(
        "insert into cookies values (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            HOST,
            "broken",
            "/",
            int((time.time() + 30 * 86400 + 11644473600) * 1_000_000),
            1,
            1,
            1,
            b"v10" + b"\x00" * 5,  # 5-byte ciphertext — too short for AES
        ),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(cookies_mod, "keychain_password", lambda *a, **k: PASSWORD)
    cookies = decrypt_chrome_cookies(db, domain_filter="%slack.com%")
    # We get the good cookie; the bad row was skipped, not raised.
    assert len(cookies) == 1
    assert cookies[0].name == NAME


def test_decrypt_value_v20_chacha20_poly1305_roundtrip():
    """v20 prefix dispatches to ChaCha20-Poly1305 with the matching 32-byte key.

    Builds a v20 encrypted_value blob using the cryptography library and
    confirms ``_decrypt_value`` recovers the original plaintext (with DB v24
    SHA256(host) prefix handling). This guards against the v20 → AES
    regression where v20 cookies would decrypt to garbage.
    """
    import hashlib

    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

    from browserclaw.cookies import _decrypt_value

    # 32-byte ChaCha20 key — Chromium derives with PBKDF2 dkLen=32 for this path.
    chacha_key = b"\x11" * 32
    plaintext = b"xoxd-chacha20-payload"
    host = "slack.com"

    # Chromium v24 layout: SHA256(host) || plaintext, no PKCS#7 padding
    # (AEAD ciphers don't pad). ChaCha20-Poly1305: nonce(12) || ct || tag(16).
    inner = hashlib.sha256(host.encode("utf-8")).digest() + plaintext
    nonce = b"\x22" * 12
    aead = ChaCha20Poly1305(chacha_key)
    ct_with_tag = aead.encrypt(nonce, inner, associated_data=None)
    body = nonce + ct_with_tag  # 12-byte nonce || ciphertext || 16-byte tag
    encrypted = b"v20" + body

    out = _decrypt_value(encrypted, chacha_key, db_version=24)
    assert out == plaintext.decode("utf-8")


def test_decrypt_value_v10_still_aes_after_v20_path_added():
    """v10 prefix must STILL route to AES-128-CBC, not be hijacked by v20 logic."""
    from browserclaw.cookies import _decrypt_value

    aes_key = derive_aes_key(PASSWORD)
    host = ".slack.com"
    plaintext = b"xoxd-aes-v10-payload"

    # Build v10 layout: AES-CBC( PKCS7-pad( SHA256(host) || plaintext ) ) + "v10"
    body = hashlib.sha256(host.encode("utf-8")).digest() + plaintext
    pad_len = 16 - (len(body) % 16)
    padded = body + bytes([pad_len]) * pad_len
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(CBC_IV))
    enc = cipher.encryptor()
    ciphertext = enc.update(padded) + enc.finalize()
    encrypted = b"v10" + ciphertext

    out = _decrypt_value(encrypted, aes_key, db_version=24)
    assert out == plaintext.decode("utf-8")


def test_decrypt_value_unrecognized_prefix_returns_empty():
    """A blob with neither v10/v11/v20 prefix returns '' instead of crashing."""
    from browserclaw.cookies import _decrypt_value

    out = _decrypt_value(b"v99" + b"\x00" * 16, b"\x00" * 16, db_version=24)
    assert out == ""


def test_to_playwright_session_cookie_preserves_domain_form():
    """Domain cookie (leading dot) — pass through verbatim, no widening."""
    c = Cookie(
        name="d", value="x", domain=".slack.com", path="/",
        expires=-1, secure=True, httpOnly=True, sameSite="Lax",
    )
    pw = c.to_playwright()
    assert pw["domain"] == ".slack.com"
    assert pw["expires"] == -1
    assert pw["sameSite"] == "Lax"


def test_to_playwright_host_only_cookie_not_widened():
    """Host-only cookie (no leading dot) — preserve verbatim, do NOT widen."""
    c = Cookie(
        name="d", value="x", domain="slack.com", path="/",
        expires=-1, secure=True, httpOnly=True, sameSite="Lax",
        host_only=True,
    )
    pw = c.to_playwright()
    # Playwright wants `url` not `domain` for host-only cookies; the host
    # itself must NOT get a leading dot (would widen scope to all subdomains).
    assert "domain" not in pw
    assert pw["url"] == "https://slack.com/"
    assert pw["expires"] == -1
    assert pw["sameSite"] == "Lax"


def test_to_playwright_rejects_invalid_samesite():
    c = Cookie(
        name="x", value="y", domain="x.com", path="/",
        expires=12345, secure=False, httpOnly=False, sameSite="bogus",
    )
    pw = c.to_playwright()
    assert pw["sameSite"] == "Lax"


def test_chrome_expires_to_unix_handles_zero_and_negative():
    assert _chrome_expires_to_unix(0) == -1
    assert _chrome_expires_to_unix(-1) == -1
    assert _chrome_expires_to_unix(None) == -1
    assert _chrome_expires_to_unix("not-a-number") == -1
    # 30 days out in Windows file time
    win_ft = int((1_700_000_000 + 30 * 86400 + 11644473600) * 1_000_000)
    out = _chrome_expires_to_unix(win_ft)
    assert out > 1_700_000_000


def test_write_read_cookies_json_roundtrip(tmp_path: Path):
    out = tmp_path / "cookies.json"
    cookies = [
        Cookie(
            name="d", value="xoxd-abc", domain=".slack.com", path="/",
            expires=1816379970, secure=True, httpOnly=True, sameSite="Lax",
        ),
        Cookie(
            name="b", value="xoxb-xyz", domain=".slack.com", path="/",
            expires=-1, secure=True, httpOnly=False, sameSite="None",
        ),
    ]
    write_cookies_json(cookies, out)
    data = json.loads(out.read_text())
    assert "cookies" in data
    assert "origins" in data
    assert len(data["cookies"]) == 2
    read_back = read_cookies_json(out)
    assert len(read_back) == 2
    assert read_back[0].name == "d"
    assert read_back[0].value == "xoxd-abc"
    assert read_back[1].expires == -1


def test_write_read_cookies_json_preserves_host_only(tmp_path: Path):
    """Round-trip must keep host_only flag — used by to_playwright() to pick
    between `domain` and `url` form. Without this, host-only cookies would be
    re-emitted as domain cookies on the next inject."""
    out = tmp_path / "cookies.json"
    cookies = [
        Cookie(
            name="d", value="xoxd-abc", domain="slack.com", path="/",
            expires=1816379970, secure=True, httpOnly=True, sameSite="Lax",
            host_only=True,
        ),
        Cookie(
            name="b", value="xoxb-xyz", domain=".slack.com", path="/",
            expires=-1, secure=True, httpOnly=False, sameSite="None",
            host_only=False,
        ),
    ]
    write_cookies_json(cookies, out)
    read_back = read_cookies_json(out)
    assert len(read_back) == 2
    assert read_back[0].host_only is True
    assert read_back[0].domain == "slack.com"
    assert read_back[1].host_only is False
    assert read_back[1].domain == ".slack.com"
