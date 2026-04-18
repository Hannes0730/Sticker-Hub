from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests
from packaging.version import InvalidVersion, Version

DEFAULT_RELEASE_REPO = "Hannes0730/Sticker-Hub"
GITHUB_RELEASE_API = "https://api.github.com/repos/{repo}/releases/latest"


@dataclass(frozen=True)
class UpdateCheckResult:
    update_available: bool
    latest_version: str = ""
    download_url: str = ""
    asset_name: str = ""
    error: str = ""


def check_for_update(current_version: str, timeout_seconds: int = 8) -> UpdateCheckResult:
    repo = os.getenv("STICKER_HUB_RELEASE_REPO", "").strip() or DEFAULT_RELEASE_REPO
    api_url = GITHUB_RELEASE_API.format(repo=repo)

    try:
        response = requests.get(api_url, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        return UpdateCheckResult(update_available=False, error=f"Unable to check updates: {exc}")

    latest_tag = str(payload.get("tag_name", "")).strip()
    latest_version = _normalize_tag_version(latest_tag)
    if not latest_version:
        return UpdateCheckResult(update_available=False, error="No valid release version found.")

    try:
        latest = Version(latest_version)
        current = Version(_normalize_tag_version(current_version) or current_version)
    except InvalidVersion:
        return UpdateCheckResult(update_available=False, error="Current version format is invalid.")

    if latest <= current:
        return UpdateCheckResult(update_available=False, latest_version=latest_version)

    asset_name, download_url = _select_windows_asset(payload.get("assets", []))
    return UpdateCheckResult(
        update_available=True,
        latest_version=latest_version,
        download_url=download_url,
        asset_name=asset_name,
    )


def _normalize_tag_version(tag_or_version: str) -> str:
    value = str(tag_or_version or "").strip()
    if value.lower().startswith("v"):
        value = value[1:]
    return value


def _select_windows_asset(assets: object) -> tuple[str, str]:
    if not isinstance(assets, list):
        return "", ""

    # Prefer ZIP for in-place replacement updates, then installer fallbacks.
    ranked: list[tuple[int, str, str]] = []
    for item in assets:
        if not isinstance(item, dict):
            continue

        name = str(item.get("name", "")).strip()
        url = str(item.get("browser_download_url", "")).strip()
        if not name or not url:
            continue

        lowered = name.lower()
        if "source code" in lowered:
            continue
        score = 99
        if lowered.endswith(".zip"):
            score = 0
        elif lowered.endswith(".exe"):
            score = 1
        elif lowered.endswith(".msi"):
            score = 2

        if "windows" in lowered or "win" in lowered or lowered.endswith((".exe", ".zip", ".msi")):
            ranked.append((score, name, url))

    if not ranked:
        return "", ""

    ranked.sort(key=lambda item: (item[0], item[1].lower()))
    _, name, url = ranked[0]
    return name, url

