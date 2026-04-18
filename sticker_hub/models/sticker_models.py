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
    parent_category: str = ""
    pack_name: str = ""
    pack_url: str = ""

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
    for parent_category, items in raw.items():
        if isinstance(items, list):
            for idx, item in enumerate(items):
                if not isinstance(item, dict):
                    continue

                sticker = _parse_sticker(parent_category, item, idx)
                if sticker:
                    stickers.append(sticker)
            continue

        if not isinstance(items, dict):
            continue

        for pack_name, pack_payload in items.items():
            if not isinstance(pack_payload, dict):
                continue

            pack_url = str(pack_payload.get("sticker_pack_url", "")).strip()
            pack_stickers = pack_payload.get("stickers", [])
            if not isinstance(pack_stickers, list):
                continue

            for idx, item in enumerate(pack_stickers):
                if not isinstance(item, dict):
                    continue

                sticker = _parse_sticker(parent_category, item, idx, pack_name=pack_name, pack_url=pack_url)
                if sticker:
                    stickers.append(sticker)

    return StickerCatalog(stickers)


def append_sticker_to_json(
    path: Path,
    category: str,
    image_url: str,
    name: str = "",
    pack_name: str = "",
    pack_url: str = "",
) -> bool:
    normalized_category = category.strip() or "Imported"
    normalized_url = image_url.strip()
    normalized_name = name.strip()
    normalized_pack_name = pack_name.strip()
    normalized_pack_url = pack_url.strip()

    if not normalized_url:
        raise ValueError("image_url cannot be empty")

    data = _load_json_object(path)
    if _url_exists(data, normalized_url):
        return False

    if normalized_pack_name:
        category_node = data.setdefault(normalized_category, {})
        if not isinstance(category_node, dict):
            category_node = {}
            data[normalized_category] = category_node

        pack_node = category_node.setdefault(normalized_pack_name, {})
        if not isinstance(pack_node, dict):
            pack_node = {}
            category_node[normalized_pack_name] = pack_node

        if normalized_pack_url:
            pack_node["sticker_pack_url"] = normalized_pack_url

        stickers_list = pack_node.setdefault("stickers", [])
        if not isinstance(stickers_list, list):
            stickers_list = []
            pack_node["stickers"] = stickers_list

        stickers_list.append({"name": normalized_name, "image_url": normalized_url})
    else:
        entries = data.setdefault(normalized_category, [])
        if not isinstance(entries, list):
            entries = []
            data[normalized_category] = entries

        entries.append({"name": normalized_name, "image_url": normalized_url})

    _atomic_write_json(path, data)
    return True


def _parse_sticker(
    parent_category: str,
    item: dict[str, Any],
    idx: int,
    pack_name: str = "",
    pack_url: str = "",
) -> Sticker | None:
    image_url = str(item.get("image_url", "")).strip()
    if not image_url:
        return None

    raw_name = ""
    display_category = f"{parent_category} / {pack_name}" if pack_name else parent_category
    safe_name = f"{display_category}-{idx + 1}"
    sticker_id = f"{parent_category}:{pack_name}:{safe_name}:{idx}"

    return Sticker(
        sticker_id=sticker_id,
        category=display_category,
        image_url=image_url,
        name=raw_name,
        parent_category=parent_category,
        pack_name=pack_name,
        pack_url=pack_url,
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
    for existing_url in _iter_all_image_urls(payload):
        if _normalize_url_for_dedupe(existing_url) == normalized_target:
            return True
    return False


def _iter_all_image_urls(payload: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for category_value in payload.values():
        if isinstance(category_value, list):
            urls.extend(_extract_urls_from_entries(category_value))
            continue

        if not isinstance(category_value, dict):
            continue

        for pack_payload in category_value.values():
            if not isinstance(pack_payload, dict):
                continue
            stickers = pack_payload.get("stickers", [])
            if isinstance(stickers, list):
                urls.extend(_extract_urls_from_entries(stickers))

    return urls


def _extract_urls_from_entries(entries: list[Any]) -> list[str]:
    urls: list[str] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        existing_url = str(item.get("image_url", "")).strip()
        if existing_url:
            urls.append(existing_url)
    return urls


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


