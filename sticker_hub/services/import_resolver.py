from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from . import provider_generic, provider_sigstick, provider_stickerly
from .provider_shared import looks_like_image_url, normalize_url_for_dedupe, preferred_image_url

# Provider priority matters: most specific first, generic fallback last.
_PROVIDERS = [
    provider_sigstick,
    provider_stickerly,
    provider_generic,
]


def resolve_sticker_urls(source_url: str, timeout_seconds: int = 20, max_results: int = 40) -> list[str]:
    source_url = source_url.strip()
    if not source_url:
        return []

    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"}:
        return []

    if looks_like_image_url(source_url):
        return [preferred_image_url(source_url)]

    response = requests.get(source_url, timeout=timeout_seconds)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    if content_type.startswith("image/"):
        return [preferred_image_url(response.url or source_url)]

    html = response.text
    resolved = _resolve_via_providers(source_url, html, max_results=max_results)
    return _dedupe_urls(resolved, max_results=max_results)


def _resolve_via_providers(source_url: str, html: str, max_results: int) -> list[str]:
    for provider in _PROVIDERS:
        if not provider.can_handle(source_url):
            continue

        resolved = provider.resolve(source_url, html, max_results=max_results)
        if resolved:
            return resolved

    return []


def _dedupe_urls(urls: list[str], max_results: int) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        preferred = preferred_image_url(url)
        normalized = normalize_url_for_dedupe(preferred)
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(preferred)
        if len(deduped) >= max_results:
            break
    return deduped


def upgrade_sticker_urls_file(path: Path) -> dict[str, int]:
    """Upgrade existing sticker URLs in-place and remove resulting duplicates."""
    if not path.exists():
        return {"updated": 0, "duplicates_removed": 0, "invalid_skipped": 0, "unchanged": 0}

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("stickers.json must be an object of category arrays")

    seen: set[str] = set()
    updated = 0
    duplicates_removed = 0
    invalid_skipped = 0
    unchanged = 0

    rewritten: dict[str, Any] = {}
    for category, items in payload.items():
        if isinstance(items, list):
            new_items, stats = _rewrite_sticker_entries(items, seen)
            updated += stats["updated"]
            duplicates_removed += stats["duplicates_removed"]
            invalid_skipped += stats["invalid_skipped"]
            unchanged += stats["unchanged"]
            rewritten[category] = new_items
            continue

        if not isinstance(items, dict):
            rewritten[category] = items
            continue

        rewritten_packs: dict[str, Any] = {}
        for pack_name, pack_payload in items.items():
            if not isinstance(pack_payload, dict):
                invalid_skipped += 1
                continue

            stickers = pack_payload.get("stickers", [])
            if not isinstance(stickers, list):
                invalid_skipped += 1
                continue

            rewritten_stickers, stats = _rewrite_sticker_entries(stickers, seen)
            updated += stats["updated"]
            duplicates_removed += stats["duplicates_removed"]
            invalid_skipped += stats["invalid_skipped"]
            unchanged += stats["unchanged"]

            pack_rewritten = dict(pack_payload)
            pack_rewritten["stickers"] = rewritten_stickers
            rewritten_packs[pack_name] = pack_rewritten

        rewritten[category] = rewritten_packs

    if updated or duplicates_removed or invalid_skipped:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(json.dumps(rewritten, indent=2), encoding="utf-8")
        temp_path.replace(path)

    return {
        "updated": updated,
        "duplicates_removed": duplicates_removed,
        "invalid_skipped": invalid_skipped,
        "unchanged": unchanged,
    }


def _rewrite_sticker_entries(items: list[Any], seen: set[str]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    updated = 0
    duplicates_removed = 0
    invalid_skipped = 0
    unchanged = 0

    new_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            invalid_skipped += 1
            continue

        original_url = str(item.get("image_url", "")).strip()
        if not original_url:
            invalid_skipped += 1
            continue

        upgraded_url = preferred_image_url(original_url)
        normalized_key = normalize_url_for_dedupe(upgraded_url)
        if normalized_key in seen:
            duplicates_removed += 1
            continue

        seen.add(normalized_key)
        updated_item = dict(item)
        updated_item["image_url"] = upgraded_url
        new_items.append(updated_item)

        if upgraded_url != original_url:
            updated += 1
        else:
            unchanged += 1

    return new_items, {
        "updated": updated,
        "duplicates_removed": duplicates_removed,
        "invalid_skipped": invalid_skipped,
        "unchanged": unchanged,
    }

