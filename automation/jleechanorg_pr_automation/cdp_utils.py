"""Shared Chrome CDP utilities."""


def format_cdp_host_for_url(host: str) -> str:
    """Format CDP host for URL, wrapping IPv6 addresses in brackets."""
    if ":" in host and not (host.startswith("[") and host.endswith("]")):
        return f"[{host}]"
    return host
