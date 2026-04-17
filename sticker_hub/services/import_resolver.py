from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests

_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")


class _ImageExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.candidates: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_dict = dict(attrs)

        if tag == "meta":
            prop = attrs_dict.get("property", "")
            name = attrs_dict.get("name", "")
            if prop in {"og:image", "og:image:url"} or name in {"twitter:image", "twitter:image:src"}:
                content = attrs_dict.get("content", "").strip()
                if content:
                    self.candidates.append(content)
            return

        if tag != "img":
            return

        for key in ("src", "data-src", "data-original"):
            value = attrs_dict.get(key, "").strip()
            if value:
                self.candidates.append(value)


def resolve_sticker_urls(source_url: str, timeout_seconds: int = 20, max_results: int = 40) -> list[str]:
    source_url = source_url.strip()
    if not source_url:
        return []

    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"}:
        return []

    if _looks_like_image_url(source_url):
        return [source_url]

    response = requests.get(source_url, timeout=timeout_seconds)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    if content_type.startswith("image/"):
        return [source_url]

    html = response.text

    parser = _ImageExtractor()
    parser.feed(html)

    regex_urls = re.findall(r"https?://[^\s\"'<>]+", html)
    parser.candidates.extend(regex_urls)

    normalized: list[str] = []
    seen: set[str] = set()
    ranked_candidates = sorted(parser.candidates, key=_candidate_rank)
    for candidate in ranked_candidates:
        absolute_url = urljoin(source_url, candidate)
        for variant_url in _build_preferred_variants(absolute_url):
            normalized_key = _normalize_url_for_dedupe(variant_url)
            if normalized_key in seen:
                continue
            if not _looks_like_image_url(variant_url):
                continue

            seen.add(normalized_key)
            normalized.append(variant_url)
            if len(normalized) >= max_results:
                return normalized

    return normalized


def preferred_image_url(url: str) -> str:
    value = url.strip()
    if not value:
        return ""

    for variant in _build_preferred_variants(value):
        if _looks_like_image_url(variant):
            return variant
    return value


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
        if not isinstance(items, list):
            rewritten[category] = items
            continue

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
            normalized_key = _normalize_url_for_dedupe(upgraded_url)
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

        rewritten[category] = new_items

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


def _looks_like_image_url(value: str) -> bool:
    path = urlparse(value).path.lower()
    return path.endswith(_IMAGE_EXTENSIONS)


def _candidate_rank(candidate: str) -> tuple[int, int]:
    parsed = urlparse(candidate)
    path = parsed.path.lower()
    # Prefer likely animated and non-thumbnail URLs first.
    animated_score = 0 if path.endswith((".gif", ".webp")) else 1
    thumb_score = 1 if ".thumb" in path else 0
    return (thumb_score, animated_score)


def _build_preferred_variants(url: str) -> list[str]:
    """Return full-size variants first, then original URL as fallback."""
    parsed = urlparse(url)
    path_without_thumb = re.sub(r"\.thumb\d+", "", parsed.path, flags=re.IGNORECASE)

    query_items = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered in {
            "w",
            "h",
            "width",
            "height",
            "size",
            "s",
            "thumbnail",
            "thumb",
            "quality",
            "q",
            "fit",
            "crop",
            "format",
            "fm",
        }:
            continue
        query_items.append((key, value))

    preferred = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            path_without_thumb,
            parsed.params,
            urlencode(query_items, doseq=True),
            parsed.fragment,
        )
    )

    if preferred == url:
        return [url]
    return [preferred, url]


def _normalize_url_for_dedupe(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return url.strip()

    filtered_query = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in {"fbclid", "gclid", "igshid", "ref", "source"}:
            continue
        filtered_query.append((key, value))

    normalized_path = re.sub(r"\.thumb\d+", "", parsed.path, flags=re.IGNORECASE)
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            normalized_path,
            parsed.params,
            urlencode(filtered_query, doseq=True),
            "",
        )
    )


