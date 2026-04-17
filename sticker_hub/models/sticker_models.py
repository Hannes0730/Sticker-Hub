from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


@dataclass(frozen=True)
class Sticker:
    sticker_id: str
    category: str
    image_url: str
    name: str = ""

    @property
    def label(self) -> str:
        return self.name.strip()


class StickerCatalog:
    def __init__(self, stickers: list[Sticker]):
        self.stickers = stickers
        self._by_id = {sticker.sticker_id: sticker for sticker in stickers}
        self.categories = sorted({sticker.category for sticker in stickers})

    def by_id(self, sticker_id: str) -> Sticker | None:
        return self._by_id.get(sticker_id)

    def filtered(self, category: str | None, query: str) -> list[Sticker]:
        normalized_query = query.strip().lower()

        results: list[Sticker] = []
        for sticker in self.stickers:
            if category and category not in {"All", sticker.category}:
                continue

            if normalized_query:
                haystack = f"{sticker.label} {sticker.category}".lower()
                if normalized_query not in haystack:
                    continue

            results.append(sticker)

        return results


def load_catalog_from_json(path: Path) -> StickerCatalog:
    if not path.exists():
        return StickerCatalog([])

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("stickers.json must be an object of category arrays")

    stickers: list[Sticker] = []
    for category, items in raw.items():
        if not isinstance(items, list):
            continue

        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue

            sticker = _parse_sticker(category, item, idx)
            if sticker:
                stickers.append(sticker)

    return StickerCatalog(stickers)


def append_sticker_to_json(path: Path, category: str, image_url: str, name: str = "") -> bool:
    normalized_category = category.strip() or "Imported"
    normalized_url = image_url.strip()
    normalized_name = name.strip()

    if not normalized_url:
        raise ValueError("image_url cannot be empty")

    data = _load_json_object(path)
    if _url_exists(data, normalized_url):
        return False

    entries = data.setdefault(normalized_category, [])
    if not isinstance(entries, list):
        entries = []
        data[normalized_category] = entries

    entries.append({"name": normalized_name, "image_url": normalized_url})
    _atomic_write_json(path, data)
    return True


def _parse_sticker(category: str, item: dict[str, Any], idx: int) -> Sticker | None:
    image_url = str(item.get("image_url", "")).strip()
    if not image_url:
        return None

    raw_name = ""
    safe_name = f"{category}-{idx + 1}"
    sticker_id = f"{category}:{safe_name}:{idx}"

    return Sticker(
        sticker_id=sticker_id,
        category=category,
        image_url=image_url,
        name=raw_name,
    )


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("stickers.json must be an object of category arrays")
    return loaded


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


def _url_exists(payload: dict[str, Any], url: str) -> bool:
    normalized_target = _normalize_url_for_dedupe(url)
    for items in payload.values():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            existing_url = str(item.get("image_url", "")).strip()
            if _normalize_url_for_dedupe(existing_url) == normalized_target:
                return True
    return False


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


