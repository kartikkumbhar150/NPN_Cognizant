"""Deterministic text and URL normalization for knowledge ingestion.

Normalization is a pure function of the input: no locale, no clock, no
network, no LLM.  It removes presentation noise (carriage returns, tab
indentation, collapsed whitespace, repeated blank lines) without ever
changing factual meaning — words, numbers, and punctuation that carry
banking facts pass through untouched.

Fetched web content is DATA, never agent instructions: nothing in this
module interprets content, and no transformation here can turn text into
executable behaviour.
"""

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Runs of spaces/tabs (incl. non-breaking and thin spaces) inside a line.
_WHITESPACE_RUN = re.compile(r"[ \t\u00a0\u2009\u202f]+")
# Three or more consecutive newlines → exactly one blank line.
_EXCESS_NEWLINES = re.compile(r"\n{3,}")
# Tracking parameters safe to drop for canonical-URL duplicate detection.
_TRACKING_PARAMS = frozenset(
    {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid", "msclkid"}
)


def normalize_text(text: str) -> str:
    """Return the deterministic normalized form of ``text``.

    CRLF/CR to LF → strip trailing per-line whitespace → collapse
    intra-line whitespace runs to one space → collapse 3+ newlines to one
    blank line → strip the whole document.  Empty or whitespace-only
    input returns ``""``.
    """
    if not isinstance(text, str):
        raise TypeError(f"normalize_text expects str, got {type(text).__name__}")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_WHITESPACE_RUN.sub(" ", line).strip() for line in normalized.split("\n")]
    collapsed = _EXCESS_NEWLINES.sub("\n\n", "\n".join(lines))
    return collapsed.strip()


def canonical_url(url: str) -> str:
    """Return the canonical form of ``url`` for duplicate detection.

    Lowercases scheme and host, drops the fragment and trailing slash,
    and removes known tracking query parameters.  Meaningful query
    parameters are preserved and their original order kept.  The
    original URL (for provenance) is always the caller's responsibility —
    this form is only for comparing two sources.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("canonical_url expects a non-empty string")
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError(f"not an http(s) URL: {url!r}")
    host = parts.hostname.lower()
    port = parts.port
    if port is not None and not _is_default_port(parts.scheme, port):
        host = f"{host}:{port}"
    kept = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in _TRACKING_PARAMS
    ]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), host, path, urlencode(kept), ""))


def _is_default_port(scheme: str, port: int) -> bool:
    return (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
