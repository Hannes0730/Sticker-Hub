# Dedicated Stickerly provider (currently uses generic extraction path).
from __future__ import annotations

from urllib.parse import urlparse

from .provider_shared import extract_generic_urls


def can_handle(source_url: str) -> bool:
    parsed = urlparse(source_url)
    host = parsed.netloc.lower()
    return "sticker.ly" in host or "stickerly" in host


def resolve(source_url: str, html: str, max_results: int = 40) -> list[str]:
    return extract_generic_urls(source_url, html, max_results=max_results)

