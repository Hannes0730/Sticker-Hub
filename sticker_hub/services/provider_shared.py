from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")
_ANIMATED_FORMAT_HINTS = {"gif", "webp"}
_STATIC_FORMAT_HINTS = {"png", "jpg", "jpeg"}


class ImageExtractor(HTMLParser):
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


def query_format_hint(url_or_parsed) -> str:
    parsed = url_or_parsed if hasattr(url_or_parsed, "query") else urlparse(str(url_or_parsed))
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered_key = key.lower()
        if lowered_key not in {"format", "fm", "ext", "type", "mime"}:
            continue

        lowered_value = value.strip().lower()
        if not lowered_value:
            continue

        if "gif" in lowered_value:
            return "gif"
        if "webp" in lowered_value:
            return "webp"
        if "png" in lowered_value:
            return "png"
        if "jpeg" in lowered_value or "jpg" in lowered_value:
            return "jpg"

    return ""


def looks_like_image_url(value: str) -> bool:
    parsed = urlparse(value)
    path = parsed.path.lower()
    if path.endswith(_IMAGE_EXTENSIONS):
        return True

    hinted_format = query_format_hint(parsed)
    if hinted_format in _ANIMATED_FORMAT_HINTS.union(_STATIC_FORMAT_HINTS):
        return True

    return False


def candidate_rank(candidate: str) -> tuple[int, int, int]:
    parsed = urlparse(candidate)
    path = parsed.path.lower()

    hinted_format = query_format_hint(parsed)
    animated_score = 0 if path.endswith((".gif", ".webp")) or hinted_format in _ANIMATED_FORMAT_HINTS else 1
    static_score = 1 if path.endswith((".png", ".jpg", ".jpeg")) or hinted_format in _STATIC_FORMAT_HINTS else 0
    thumb_score = 1 if ".thumb" in path else 0
    return (thumb_score, animated_score, static_score)


def build_preferred_variants(url: str) -> list[str]:
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


def normalize_url_for_dedupe(url: str) -> str:
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


def preferred_image_url(url: str) -> str:
    value = url.strip()
    if not value:
        return ""

    for variant in build_preferred_variants(value):
        if looks_like_image_url(variant):
            return variant
    return value


def extract_generic_urls(source_url: str, html: str, max_results: int = 40) -> list[str]:
    parser = ImageExtractor()
    parser.feed(html)

    regex_urls = re.findall(r"https?://[^\s\"'<>]+", html)
    parser.candidates.extend(regex_urls)

    normalized: list[str] = []
    seen: set[str] = set()
    ranked_candidates = sorted(parser.candidates, key=candidate_rank)
    for candidate in ranked_candidates:
        absolute_url = urljoin(source_url, candidate)
        for variant_url in build_preferred_variants(absolute_url):
            normalized_key = normalize_url_for_dedupe(variant_url)
            if normalized_key in seen:
                continue
            if not looks_like_image_url(variant_url):
                continue

            seen.add(normalized_key)
            normalized.append(variant_url)
            if len(normalized) >= max_results:
                return normalized

    return normalized

