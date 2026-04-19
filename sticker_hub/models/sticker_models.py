from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


DB_NAME = "stickers.db"
SCHEMA_VERSION = 1


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
    db_path = _db_path_for(path)
    _ensure_database(db_path)

    with _open_connection(db_path) as conn:
        if _is_database_empty(conn):
            _import_json_into_db(conn, path)
            conn.commit()

        stickers = _load_stickers_from_db(conn)

    _write_json_cache_from_db(path, stickers)
    return StickerCatalog(stickers)


def append_sticker_to_json(
    path: Path,
    category: str,
    image_url: str,
    name: str = "",
    pack_name: str = "",
    pack_url: str = "",
) -> bool:
    normalized_category = _to_title_case(category.strip()) or "Imported"
    normalized_url = image_url.strip()
    normalized_name = _to_title_case(name.strip())
    normalized_pack_name = _to_title_case(pack_name.strip())
    normalized_pack_url = pack_url.strip()

    if not normalized_url:
        raise ValueError("image_url cannot be empty")

    db_path = _db_path_for(path)
    _ensure_database(db_path)

    with _open_connection(db_path) as conn:
        pack_id = _upsert_pack(
            conn,
            parent_category=normalized_category,
            pack_name=normalized_pack_name,
            source_url=normalized_pack_url,
            raw_json="",
        )

        dedupe_hash = _compute_file_hash(normalized_url)
        if _sticker_hash_exists(conn, dedupe_hash):
            return False

        file_name = _derive_file_name(normalized_url, fallback_prefix="sticker")
        file_name = _unique_file_name_in_pack(conn, pack_id, file_name)
        _insert_sticker(
            conn,
            pack_id=pack_id,
            file_name=file_name,
            file_hash=dedupe_hash,
            image_url=normalized_url,
            display_name=normalized_name,
            user_emoji="",
        )
        conn.commit()

        stickers = _load_stickers_from_db(conn)

    _write_json_cache_from_db(path, stickers)
    return True


def delete_category_from_json(path: Path, category: str) -> bool:
    target = category.strip()
    if not target:
        return False

    db_path = _db_path_for(path)
    _ensure_database(db_path)

    with _open_connection(db_path) as conn:
        row = conn.execute("SELECT id FROM packs WHERE parent_category = ? LIMIT 1", (target,)).fetchone()
        if not row:
            return False

        conn.execute("DELETE FROM packs WHERE parent_category = ?", (target,))
        conn.commit()
        stickers = _load_stickers_from_db(conn)

    _write_json_cache_from_db(path, stickers)
    return True


def delete_pack_from_json(path: Path, category: str, pack_name: str) -> bool:
    target_category = category.strip()
    target_pack = pack_name.strip()
    if not target_category or not target_pack:
        return False

    db_path = _db_path_for(path)
    _ensure_database(db_path)

    with _open_connection(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM packs WHERE parent_category = ? AND name = ?",
            (target_category, target_pack),
        ).fetchone()
        if not row:
            return False

        conn.execute(
            "DELETE FROM packs WHERE parent_category = ? AND name = ?",
            (target_category, target_pack),
        )
        conn.commit()
        stickers = _load_stickers_from_db(conn)

    _write_json_cache_from_db(path, stickers)
    return True


def get_catalog_db_status(path: Path) -> dict[str, Any]:
    db_path = _db_path_for(path)
    exists = db_path.exists()
    if not exists:
        return {
            "db_path": str(db_path),
            "exists": False,
            "table_count": 0,
            "tables": [],
        }

    with _open_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()

    tables = [str(row["name"]) for row in rows]
    return {
        "db_path": str(db_path),
        "exists": True,
        "table_count": len(tables),
        "tables": tables,
    }


def _db_path_for(catalog_path: Path) -> Path:
    if catalog_path.suffix.lower() == ".db":
        return catalog_path
    return catalog_path.with_name(DB_NAME)


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_database(db_path: Path) -> None:
    with _open_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS packs (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                parent_category TEXT NOT NULL,
                folder_name TEXT NOT NULL UNIQUE,
                source_url TEXT NOT NULL DEFAULT '',
                raw_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(parent_category, name)
            );

            CREATE TABLE IF NOT EXISTS stickers (
                id INTEGER PRIMARY KEY,
                pack_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_hash TEXT NOT NULL UNIQUE,
                image_url TEXT NOT NULL,
                display_name TEXT NOT NULL DEFAULT '',
                user_emoji TEXT NOT NULL DEFAULT '',
                is_favorite INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(pack_id, file_name),
                FOREIGN KEY(pack_id) REFERENCES packs(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL DEFAULT 'ai',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sticker_tags (
                sticker_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                source TEXT NOT NULL DEFAULT 'ai',
                confidence REAL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(sticker_id, tag_id, source),
                FOREIGN KEY(sticker_id) REFERENCES stickers(id) ON DELETE CASCADE,
                FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_packs_parent ON packs(parent_category);
            CREATE INDEX IF NOT EXISTS idx_stickers_pack ON stickers(pack_id);
            CREATE INDEX IF NOT EXISTS idx_stickers_hash ON stickers(file_hash);
            CREATE INDEX IF NOT EXISTS idx_sticker_tags_sticker ON sticker_tags(sticker_id);
            """
        )
        conn.execute(
            "INSERT OR REPLACE INTO metadata(key, value) VALUES('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        conn.commit()


@contextmanager
def _open_connection(db_path: Path):
    conn = _connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


def _is_database_empty(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT COUNT(*) AS count FROM stickers").fetchone()
    return int(row["count"] if row else 0) == 0


def _import_json_into_db(conn: sqlite3.Connection, json_path: Path) -> None:
    if not json_path.exists():
        return

    raw = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("stickers.json must be an object of category arrays")

    for parent_category, items in raw.items():
        if isinstance(items, list):
            pack_id = _upsert_pack(
                conn,
                parent_category=_to_title_case(parent_category.strip()) or "Imported",
                pack_name="",
                source_url="",
                raw_json=json.dumps(items, ensure_ascii=True),
            )
            _insert_items_into_pack(conn, pack_id, items)
            continue

        if not isinstance(items, dict):
            continue

        normalized_parent = _to_title_case(parent_category.strip()) or "Imported"
        for pack_name, pack_payload in items.items():
            if not isinstance(pack_payload, dict):
                continue

            source_url = str(pack_payload.get("sticker_pack_url", "")).strip()
            stickers = pack_payload.get("stickers", [])
            if not isinstance(stickers, list):
                continue

            pack_id = _upsert_pack(
                conn,
                parent_category=normalized_parent,
                pack_name=_to_title_case(str(pack_name).strip()),
                source_url=source_url,
                raw_json=json.dumps(pack_payload, ensure_ascii=True),
            )
            _insert_items_into_pack(conn, pack_id, stickers)


def _insert_items_into_pack(conn: sqlite3.Connection, pack_id: int, items: list[Any]) -> None:
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue

        image_url = str(item.get("image_url", "")).strip()
        if not image_url:
            continue

        file_hash = str(item.get("file_hash", "")).strip() or _compute_file_hash(image_url)
        if _sticker_hash_exists(conn, file_hash):
            continue

        file_name = _derive_file_name(image_url, fallback_prefix=f"sticker-{idx + 1}")
        file_name = _unique_file_name_in_pack(conn, pack_id, file_name)
        display_name = _to_title_case(str(item.get("name", "")).strip())
        user_emoji = str(item.get("emoji", "")).strip()

        sticker_id = _insert_sticker(
            conn,
            pack_id=pack_id,
            file_name=file_name,
            file_hash=file_hash,
            image_url=image_url,
            display_name=display_name,
            user_emoji=user_emoji,
        )

        _insert_tags_for_sticker(conn, sticker_id, item.get("tags"))


def _upsert_pack(
    conn: sqlite3.Connection,
    parent_category: str,
    pack_name: str,
    source_url: str,
    raw_json: str,
) -> int:
    normalized_parent = parent_category.strip() or "Imported"
    normalized_pack = pack_name.strip()
    folder_seed = f"{normalized_parent}-{normalized_pack}" if normalized_pack else normalized_parent
    folder_name = _to_folder_name(folder_seed)
    now = _now_iso()

    existing = conn.execute(
        "SELECT id FROM packs WHERE parent_category = ? AND name = ?",
        (normalized_parent, normalized_pack),
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE packs
            SET source_url = COALESCE(NULLIF(?, ''), source_url),
                raw_json = CASE WHEN ? <> '' THEN ? ELSE raw_json END,
                updated_at = ?
            WHERE id = ?
            """,
            (source_url, raw_json, raw_json, now, int(existing["id"])),
        )
        return int(existing["id"])

    collision = 1
    candidate_folder = folder_name
    while conn.execute("SELECT 1 FROM packs WHERE folder_name = ?", (candidate_folder,)).fetchone():
        collision += 1
        candidate_folder = f"{folder_name}-{collision}"

    cursor = conn.execute(
        """
        INSERT INTO packs(name, parent_category, folder_name, source_url, raw_json, created_at, updated_at)
        VALUES(?, ?, ?, ?, ?, ?, ?)
        """,
        (normalized_pack, normalized_parent, candidate_folder, source_url, raw_json or "{}", now, now),
    )
    return int(cursor.lastrowid)


def _insert_sticker(
    conn: sqlite3.Connection,
    pack_id: int,
    file_name: str,
    file_hash: str,
    image_url: str,
    display_name: str,
    user_emoji: str,
) -> int:
    now = _now_iso()
    cursor = conn.execute(
        """
        INSERT INTO stickers(pack_id, file_name, file_hash, image_url, display_name, user_emoji, is_favorite, created_at, updated_at)
        VALUES(?, ?, ?, ?, ?, ?, 0, ?, ?)
        """,
        (pack_id, file_name, file_hash, image_url, display_name, user_emoji, now, now),
    )
    return int(cursor.lastrowid)


def _unique_file_name_in_pack(conn: sqlite3.Connection, pack_id: int, file_name: str) -> str:
    candidate = file_name.strip() or "sticker.webp"
    stem = Path(candidate).stem or "sticker"
    suffix = Path(candidate).suffix or ".webp"

    counter = 1
    while conn.execute(
        "SELECT 1 FROM stickers WHERE pack_id = ? AND file_name = ? LIMIT 1",
        (pack_id, candidate),
    ).fetchone():
        counter += 1
        candidate = f"{stem}-{counter}{suffix}"
    return candidate


def _insert_tags_for_sticker(conn: sqlite3.Connection, sticker_id: int, raw_tags: Any) -> None:
    tags = _parse_tags(raw_tags)
    if not tags:
        return

    for tag in tags:
        normalized = tag.casefold().strip()
        if not normalized:
            continue

        row = conn.execute("SELECT id FROM tags WHERE normalized_name = ?", (normalized,)).fetchone()
        if row:
            tag_id = int(row["id"])
        else:
            now = _now_iso()
            cursor = conn.execute(
                "INSERT INTO tags(name, normalized_name, kind, created_at) VALUES(?, ?, 'ai', ?)",
                (tag, normalized, now),
            )
            tag_id = int(cursor.lastrowid)

        conn.execute(
            "INSERT OR IGNORE INTO sticker_tags(sticker_id, tag_id, source, confidence, created_at) VALUES(?, ?, 'ai', NULL, ?)",
            (sticker_id, tag_id, _now_iso()),
        )


def _sticker_hash_exists(conn: sqlite3.Connection, file_hash: str) -> bool:
    row = conn.execute("SELECT 1 FROM stickers WHERE file_hash = ? LIMIT 1", (file_hash,)).fetchone()
    return bool(row)


def _load_stickers_from_db(conn: sqlite3.Connection) -> list[Sticker]:
    rows = conn.execute(
        """
        SELECT
            s.id AS sticker_id,
            s.image_url,
            s.display_name,
            p.parent_category,
            p.name AS pack_name,
            p.source_url
        FROM stickers s
        JOIN packs p ON p.id = s.pack_id
        ORDER BY p.parent_category COLLATE NOCASE, p.name COLLATE NOCASE, s.id
        """
    ).fetchall()

    stickers: list[Sticker] = []
    for row in rows:
        parent_category = str(row["parent_category"] or "").strip()
        pack_name = str(row["pack_name"] or "").strip()
        display_category = f"{parent_category} / {pack_name}" if pack_name else parent_category

        stickers.append(
            Sticker(
                sticker_id=str(row["sticker_id"]),
                category=display_category,
                image_url=str(row["image_url"] or "").strip(),
                name=str(row["display_name"] or "").strip(),
                parent_category=parent_category,
                pack_name=pack_name,
                pack_url=str(row["source_url"] or "").strip(),
            )
        )

    return stickers


def _write_json_cache_from_db(cache_path: Path, stickers: list[Sticker]) -> None:
    payload: dict[str, Any] = {}

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for sticker in stickers:
        key = (sticker.parent_category, sticker.pack_name)
        bucket = grouped.setdefault(
            key,
            {
                "source_url": sticker.pack_url,
                "stickers": [],
            },
        )
        if sticker.pack_url and not bucket["source_url"]:
            bucket["source_url"] = sticker.pack_url

        bucket["stickers"].append(
            {
                "name": sticker.name,
                "image_url": sticker.image_url,
            }
        )

    for (parent_category, pack_name), entry in grouped.items():
        if pack_name:
            node = payload.setdefault(parent_category, {})
            if not isinstance(node, dict):
                node = {}
                payload[parent_category] = node
            node[pack_name] = {
                "sticker_pack_url": entry["source_url"],
                "stickers": entry["stickers"],
            }
        else:
            node = payload.setdefault(parent_category, [])
            if not isinstance(node, list):
                node = []
                payload[parent_category] = node
            node.extend(entry["stickers"])

    _atomic_write_json(cache_path, payload)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


def _parse_tags(raw_tags: Any) -> list[str]:
    if isinstance(raw_tags, list):
        values = [str(tag).strip() for tag in raw_tags]
    elif isinstance(raw_tags, str):
        values = [part.strip() for part in re.split(r"[,;|]", raw_tags)]
    else:
        return []

    seen: set[str] = set()
    tags: list[str] = []
    for value in values:
        if not value:
            continue
        lowered = value.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        tags.append(value)
    return tags


def _derive_file_name(image_url: str, fallback_prefix: str) -> str:
    parsed = urlparse(image_url)
    candidate = Path(parsed.path).name.strip()
    if candidate:
        return candidate

    digest = hashlib.sha1(image_url.encode("utf-8")).hexdigest()[:12]
    return f"{fallback_prefix}-{digest}.webp"


def _compute_file_hash(image_url: str) -> str:
    normalized = _normalize_url_for_dedupe(image_url)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _normalize_url_for_dedupe(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return url.strip()

    filtered_query = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in {
            "fbclid",
            "gclid",
            "igshid",
            "ref",
            "source",
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
        }:
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


def _to_title_case(value: str) -> str:
    if not value:
        return ""
    return " ".join(part.capitalize() for part in value.split())


def _to_folder_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-")
    return cleaned.casefold() or "pack"


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
