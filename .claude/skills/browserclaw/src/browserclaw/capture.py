from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Iterable

from playwright.async_api import BrowserContext, Page, async_playwright

from .models import (
    WebSocketCaptureResult,
    WebSocketConnection,
    WebSocketFrame,
    parse_firestore_message,
)


async def _run_step(page: Page, step) -> None:
    from .models import BrowserStep
    step = BrowserStep(**step) if isinstance(step, dict) else step
    if step.action == "goto":
        await page.goto(step.url or "", wait_until="networkidle")
    elif step.action == "click":
        await page.click(step.selector or "")
    elif step.action == "fill":
        await page.fill(step.selector or "", step.value or "")
    elif step.action == "press":
        await page.press(step.selector or "", step.value or "")
    elif step.action == "wait_for_timeout":
        await page.wait_for_timeout(float(step.milliseconds or 1000))
    elif step.action == "wait_for_url":
        await page.wait_for_url(step.value or "")
    elif step.action == "eval":
        await page.evaluate(step.value or "")
    else:
        raise ValueError(f"Unsupported browser step: {step.action}")


def load_steps(path: str | Path) -> list:
    payload = json.loads(Path(path).read_text())
    return payload


async def _connect_superpower_chrome(playwright):
    """Try to connect to superpower chrome at localhost:9222. Returns (browser, context, page) or None."""
    try:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[-1]
        # Verify it's alive with a quick eval
        await page.evaluate("1 + 1")
        return browser, context, page
    except Exception:
        return None


async def _capture(
    url: str,
    output: Path,
    *,
    browser_channel: str,
    headless: bool,
    storage_state: str | None,
    manual: bool,
    wait_after_load: float,
    steps: Iterable | None,
    extra_headers: dict[str, str] | None = None,
) -> Path:
    async with async_playwright() as playwright:
        # Try superpower chrome first (has auth already attached)
        sc = await _connect_superpower_chrome(playwright)
        if sc:
            browser, context, page = sc
            _use_superpower = True
        else:
            browser = await playwright.chromium.launch(
                channel=browser_channel,
                headless=headless,
                args=["--disable-font-subpixel-positioning", "--disable-gpu"],
            )
            context_options: dict = {
                "record_har_path": str(output),
                "record_har_mode": "full",
                "record_har_content": "embed",
            }
            if storage_state:
                context_options["storage_state"] = storage_state
            if extra_headers:
                context_options["extra_http_headers"] = extra_headers
            context = await browser.new_context(**context_options)
            page = await context.new_page()
            _use_superpower = False

        # Only enable HAR recording when NOT using superpower chrome
        # (superpower chrome's CDP already captures network via its own proxy)
        if not _use_superpower:
            cdp = await context.new_cdp_session(page)
            await cdp.send("Network.enable")

        await page.goto(url, wait_until="domcontentloaded")

        if steps:
            for step in steps:
                await _run_step(page, step)

        if manual:
            await asyncio.to_thread(
                input,
                "Interact with the page, then press Enter here to finish HAR capture: ",
            )
        else:
            await page.wait_for_timeout(wait_after_load * 1000)

        if not _use_superpower:
            await context.close()
        await browser.close()
    return output


def capture_har(
    url: str,
    output: str | Path,
    *,
    browser_channel: str = "chromium",
    headless: bool = False,
    storage_state: str | None = None,
    manual: bool = True,
    wait_after_load: float = 15.0,
    steps: Iterable | None = None,
    extra_headers: dict[str, str] | None = None,
) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return asyncio.run(
        _capture(
            url,
            output_path,
            browser_channel=browser_channel,
            headless=headless,
            storage_state=storage_state,
            manual=manual,
            wait_after_load=wait_after_load,
            steps=steps,
            extra_headers=extra_headers,
        )
    )


# ─── Superpower Chrome: response capture ───────────────────────────────────────


async def _capture_responses_superpower(url: str) -> dict[str, dict]:
    """Use superpower chrome's fetchApi to capture authenticated response bodies.

    Returns a dict mapping endpoint path -> {status, data, headers}.
    Empty dict if superpower chrome is not available.
    """
    result: dict[str, dict] = {}
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception:
            return result

        try:
            context = browser.contexts[0]
            page = context.pages[-1]

            # Verify fetchApi is available
            is_fn = await page.evaluate("typeof window.fetchApi === 'function'")
            if not is_fn:
                return result

            base = url.rstrip("/")
            endpoints = [
                ("/api/campaigns", "GET", None),
                ("/api/settings", "GET", None),
                ("/api/time", "GET", None),
            ]

            for path, method, body in endpoints:
                try:
                    js = f"""async () => {{
                        const r = await window.fetchApi('{path}');
                        return {{ status: r.status, data: r.data, headers: {{}} }};
                    }}"""
                    resp = await page.evaluate(js)
                    result[path] = resp
                except Exception:
                    pass

            # Try first campaign's story + details if campaigns are accessible
            try:
                campaigns_resp = result.get("/api/campaigns")
                if campaigns_resp and campaigns_resp.get("data", {}).get("campaigns"):
                    first = campaigns_resp["data"]["campaigns"][0]
                    cid = first.get("id", "")
                    if cid:
                        story_resp = await page.evaluate(
                            f"""async () => {{
                                const r = await window.fetchApi('/api/campaigns/{cid}/story');
                                return {{ status: r.status, data: r.data }};
                            }}"""
                        )
                        result[f"/api/campaigns/{cid}/story"] = story_resp

                        # Try export endpoint (may return non-JSON — use native fetch)
                        try:
                            export_resp = await page.evaluate(
                                f"""async () => {{
                                    const r = await fetch('/api/campaigns/{cid}/export', {{
                                        method: 'GET',
                                        credentials: 'include'
                                    }});
                                    const text = await r.text();
                                    return {{
                                        status: r.status,
                                        contentType: r.headers.get('content-type'),
                                        body: text.slice(0, 500),
                                        isRateLimited: r.status === 429
                                    }};
                                }}"""
                            )
                            result[f"/api/campaigns/{cid}/export"] = export_resp
                        except Exception:
                            pass
            except Exception:
                pass

        finally:
            await browser.close()

    return result


def capture_responses_superpower(url: str) -> dict[str, dict]:
    """Synchronous wrapper for _capture_responses_superpower."""
    return asyncio.run(_capture_responses_superpower(url))


# ─── Evidence capture (screenshots + console) ─────────────────────────────────


async def _capture_evidence(
    url: str,
    output_dir: Path,
    *,
    browser_channel: str,
    headless: bool,
) -> Path:
    """Take a screenshot and capture console messages using Playwright.

    Saves evidence/ subdirectory under output_dir with screenshot and console log.
    Returns Path to the evidence directory.
    """
    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        sc = await _connect_superpower_chrome(p)
        if sc:
            browser, context, page = sc
            source = "superpower_chrome"
            _use_superpower = True
        else:
            browser = await p.chromium.launch(channel=browser_channel, headless=headless)
            context = await browser.new_context()
            page = await context.new_page()
            source = "playwright"
            _use_superpower = False

        try:
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            # Screenshot (non-fatal — fonts may hang in headless)
            try:
                screenshot_path = evidence_dir / "screenshot.png"
                await page.screenshot(path=str(screenshot_path), timeout=5000)
            except Exception:
                pass  # fonts/loading issues in headless — skip screenshot

            # Console messages
            console_entries: list[str] = []

            def on_console(msg):
                console_entries.append(f"[{msg.type}] {msg.text}")

            page.on("console", on_console)
            await page.wait_for_timeout(500)
            page.remove_listener("console", on_console)

            console_path = evidence_dir / "console.txt"
            console_path.write_text(
                f"# Browser console log (source: {source})\n"
                f"# URL: {url}\n"
                + "\n".join(console_entries)
            )

            # Also save page title + URL metadata
            meta_path = evidence_dir / "meta.txt"
            title = await page.title()
            meta_path.write_text(f"url: {url}\ntitle: {title}\nsource: {source}\n")

        finally:
            if not _use_superpower:
                await context.close()
            await browser.close()

    return evidence_dir


def capture_evidence(
    url: str,
    output_dir: str | Path,
    *,
    browser_channel: str = "chromium",
    headless: bool = True,
) -> Path:
    """Synchronous wrapper for _capture_evidence."""
    return asyncio.run(_capture_evidence(url, Path(output_dir), browser_channel=browser_channel, headless=headless))


# ─── WebSocket Capture ─────────────────────────────────────────────────────────


class _WsCaptureSession:
    """CDP WebSocket event collector for Playwright 1.x.

    Playwright 1.x uses requestId (not connectionId) as the WS event key.
    Event shapes differ from CDP spec:
      - webSocketCreated: {requestId, url, initiator}
      - webSocketFrameSent/Received: {requestId, timestamp, response: {opcode, payloadData, payloadLength}}
      - webSocketHandshakeResponseReceived: {requestId, timestamp, response: {headers, status}}
      - webSocketDestroyed: {requestId, timestamp, reason}
    """

    def __init__(self, cdp):
        self.cdp = cdp
        self.connections: dict[str, WebSocketConnection] = {}
        self._call_count = 0
        self._firestore_calls: list = []

    async def enable(self):
        await self.cdp.send("Network.enable")
        self.cdp.on("Network.webSocketCreated", self._on_created)
        self.cdp.on("Network.webSocketFrameSent", self._on_frame_sent)
        self.cdp.on("Network.webSocketFrameReceived", self._on_frame_received)
        self.cdp.on("Network.webSocketHandshakeResponseReceived", self._on_handshake)
        self.cdp.on("Network.webSocketDestroyed", self._on_destroyed)

    def _on_created(self, event):
        # Playwright 1.x: requestId + url (no nested request.url)
        rid = event["requestId"]
        ws_url = event.get("url", "")
        initiator = event.get("initiator", {})
        req_headers = {}
        if isinstance(initiator, dict):
            pass
        self.connections[rid] = WebSocketConnection(
            connection_id=rid,
            url=ws_url,
            created_at=time.time(),
            request_headers=req_headers,
        )

    def _on_frame_sent(self, event):
        rid = event["requestId"]
        conn = self.connections.get(rid)
        if not conn:
            return
        response = event.get("response", {})
        payload_data = response.get("payloadData", "")
        opcode = response.get("opcode", 0)
        payload, is_bin = _decode_ws_payload(payload_data)
        frame = WebSocketFrame(
            timestamp=time.time(),
            connection_id=rid,
            direction="sent",
            opcode=opcode,
            payload=payload,
            size=response.get("payloadLength", len(payload_data) if payload_data else 0),
            is_binary=is_bin,
        )
        conn.frames.append(frame)
        self._maybe_parse_firestore(conn, frame)

    def _on_frame_received(self, event):
        rid = event["requestId"]
        conn = self.connections.get(rid)
        if not conn:
            return
        response = event.get("response", {})
        payload_data = response.get("payloadData", "")
        opcode = response.get("opcode", 0)
        payload, is_bin = _decode_ws_payload(payload_data)
        frame = WebSocketFrame(
            timestamp=time.time(),
            connection_id=rid,
            direction="received",
            opcode=opcode,
            payload=payload,
            size=response.get("payloadLength", len(payload_data) if payload_data else 0),
            is_binary=is_bin,
        )
        conn.frames.append(frame)
        self._maybe_parse_firestore(conn, frame)

    def _on_handshake(self, event):
        rid = event["requestId"]
        conn = self.connections.get(rid)
        if conn:
            response = event.get("response", {})
            headers = response.get("headers", {})
            conn.response_headers = dict(headers)

    def _on_destroyed(self, event):
        rid = event["requestId"]
        conn = self.connections.get(rid)
        if conn:
            conn.closed_at = time.time()

    def _maybe_parse_firestore(self, conn: WebSocketConnection, frame: WebSocketFrame):
        """If this is a Firestore connection, parse the frame for RPC calls."""
        if not conn.is_firestore:
            return
        if frame.is_binary or not frame.payload.strip():
            return
        calls = parse_firestore_message(frame.payload)
        for call in calls:
            call.call_id = self._call_count
            self._call_count += 1
            self._firestore_calls.append(call)

    def result(self) -> WebSocketCaptureResult:
        from .models import WebSocketCaptureResult as R
        return R(
            connections=list(self.connections.values()),
            firestore_calls=self._firestore_calls,
            notes=[
                f"Captured {len(self.connections)} WebSocket connections",
                f"Total frames: {sum(len(c.frames) for c in self.connections.values())}",
                f"Firestore RPC calls parsed: {len(self._firestore_calls)}",
            ],
        )


def _decode_ws_payload(data: str) -> tuple[str, bool]:
    """Decode WebSocket payload data. Returns (text, is_binary)."""
    if not data:
        return "", False
    try:
        return data, False
    except Exception:
        return "", True


async def _capture_ws(
    url: str,
    output: Path,
    *,
    browser_channel: str,
    headless: bool,
    storage_state: str | None,
    manual: bool,
    wait_after_load: float,
    steps: Iterable | None,
    extra_headers: dict[str, str] | None = None,
) -> Path:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(channel=browser_channel, headless=headless)
        context_options: dict = {}
        if storage_state:
            context_options["storage_state"] = storage_state
        if extra_headers:
            context_options["extra_http_headers"] = extra_headers
        context: BrowserContext = await browser.new_context(**context_options)
        page = await context.new_page()
        cdp = await context.new_cdp_session(page)

        session = _WsCaptureSession(cdp)
        await session.enable()

        await page.goto(url, wait_until="domcontentloaded")

        if steps:
            for step in steps:
                await _run_step(page, step)

        if manual:
            await asyncio.to_thread(
                input,
                "Interact with the page, then press Enter here to finish WebSocket capture: ",
            )
        else:
            await page.wait_for_timeout(wait_after_load * 1000)

        await context.close()
        await browser.close()

        result = session.result()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({
            "connections": [c.to_dict() for c in result.connections],
            "firestore_calls": [c.to_dict() for c in result.firestore_calls],
            "notes": result.notes,
        }, indent=2))
        return output


def capture_ws(
    url: str,
    output: str | Path,
    *,
    browser_channel: str = "chromium",
    headless: bool = False,
    storage_state: str | None = None,
    manual: bool = True,
    wait_after_load: float = 15.0,
    steps: Iterable | None = None,
    extra_headers: dict[str, str] | None = None,
) -> Path:
    """Capture WebSocket frames via CDP and save as JSON.

    Returns Path to the JSON output file containing:
    - connections: list of WebSocketConnection summaries
    - firestore_calls: parsed Firestore RPC calls (if Firestore WS detected)
    - notes: capture session summary
    """
    output_path = Path(output)
    return asyncio.run(
        _capture_ws(
            url,
            output_path,
            browser_channel=browser_channel,
            headless=headless,
            storage_state=storage_state,
            manual=manual,
            wait_after_load=wait_after_load,
            steps=steps,
            extra_headers=extra_headers,
        )
    )
