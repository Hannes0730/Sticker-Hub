from __future__ import annotations

import re
from urllib.parse import urlparse

from .provider_shared import build_preferred_variants, looks_like_image_url, normalize_url_for_dedupe


def can_handle(source_url: str) -> bool:
    parsed = urlparse(source_url)
    return "sigstick.com" in parsed.netloc.lower() and "/pack/" in parsed.path


def resolve(source_url: str, html: str, max_results: int = 40) -> list[str]:
    parsed = urlparse(source_url)
    pack_token = pack_token_from_path(parsed.path)
    if not pack_token:
        return []

    cdn_urls = re.findall(r"https?://cdn\d?\.cdnstep\.com/[^\s\"'<>]+", html)
    if not cdn_urls:
        return []

    filtered: list[str] = []
    seen: set[str] = set()
    token_marker = f"/{pack_token.lower()}/"
    for candidate in cdn_urls:
        if token_marker not in candidate.lower():
            continue
        for variant_url in build_preferred_variants(candidate):
            if not looks_like_image_url(variant_url):
                continue
            normalized_key = normalize_url_for_dedupe(variant_url)
            if normalized_key in seen:
                continue
            seen.add(normalized_key)
            filtered.append(variant_url)
            if len(filtered) >= max_results:
                return filtered

    return filtered


def pack_token_from_path(path: str) -> str:
    marker = "/pack/"
    if marker not in path:
        return ""

    slug = path.split(marker, 1)[1].strip("/")
    if not slug:
        return ""

    token = slug.split("-", 1)[0].strip()
    if not token:
        return ""

    if not re.fullmatch(r"[A-Za-z0-9]+", token):
        return ""
    return token
