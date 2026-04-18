from __future__ import annotations

import re
from pathlib import PurePosixPath
from urllib.parse import urlparse

import requests

from .provider_shared import build_preferred_variants, looks_like_image_url, normalize_url_for_dedupe


def can_handle(source_url: str) -> bool:
    parsed = urlparse(source_url)
    return "sigstick.com" in parsed.netloc.lower() and "/pack/" in parsed.path


def resolve(source_url: str, html: str, max_results: int = 40) -> list[str]:
    parsed = urlparse(source_url)
    pack_token = pack_token_from_path(parsed.path)
    if not pack_token:
        return []

    # Prefer SigStick's official API because it is more stable than scraping page HTML.
    resolved_from_api = _resolve_from_api(pack_token, max_results=max_results)
    if resolved_from_api:
        return resolved_from_api

    return _resolve_from_html(pack_token, html, max_results=max_results)


def _resolve_from_api(pack_id: str, max_results: int = 40) -> list[str]:
    api_url = f"https://api.sigstick.com/v1/stickerPack/{pack_id}"
    try:
        response = requests.get(api_url, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []

    return _extract_urls_from_api_payload(payload, max_results=max_results)


def _extract_urls_from_api_payload(payload: object, max_results: int = 40) -> list[str]:
    candidates: list[str] = []

    def walk(node: object) -> None:
        if len(candidates) >= max_results:
            return

        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, str):
                    lowered_key = str(key).lower()
                    if lowered_key in {
                        "url",
                        "image",
                        "imageurl",
                        "image_url",
                        "src",
                        "stickerurl",
                        "sticker_url",
                        "webp",
                        "gif",
                    } or looks_like_image_url(value):
                        candidates.append(value)
                        if len(candidates) >= max_results:
                            return
                else:
                    walk(value)
            return

        if isinstance(node, list):
            for item in node:
                walk(item)
                if len(candidates) >= max_results:
                    return
            return

        if isinstance(node, str) and looks_like_image_url(node):
            candidates.append(node)

    walk(payload)

    filtered: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        for variant_url in build_preferred_variants(candidate):
            if not looks_like_image_url(variant_url):
                continue
            if _is_pack_cover_url(variant_url):
                continue
            normalized_key = normalize_url_for_dedupe(variant_url)
            if normalized_key in seen:
                continue
            seen.add(normalized_key)
            filtered.append(variant_url)
            if len(filtered) >= max_results:
                return filtered

    return filtered


def _resolve_from_html(pack_token: str, html: str, max_results: int = 40) -> list[str]:

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
            if _is_pack_cover_url(variant_url):
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


def _is_pack_cover_url(url: str) -> bool:
    path = urlparse(url).path
    filename = PurePosixPath(path).name.lower()
    # SigStick cover assets are usually cover-<n>.<ext>; exclude them from imports.
    return bool(re.fullmatch(r"cover(?:-\d+)?\.(?:png|jpe?g|gif|webp)", filename))

