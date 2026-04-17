from __future__ import annotations

from importlib import metadata
from pathlib import Path
import sys
import tomllib


DISTRIBUTION_NAME = "sticker-hub"


def get_app_version() -> str:
    try:
        return metadata.version(DISTRIBUTION_NAME)
    except metadata.PackageNotFoundError:
        pass

    candidate_paths = [
        Path(__file__).resolve().parents[1] / "pyproject.toml",
        Path(__file__).resolve().parents[2] / "pyproject.toml",
    ]
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass:
        candidate_paths.insert(0, Path(meipass) / "pyproject.toml")

    for pyproject_path in candidate_paths:
        if not pyproject_path.exists():
            continue
        try:
            payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            project = payload.get("project", {})
            version = str(project.get("version", "")).strip()
            if version:
                return version
        except Exception:
            continue

    return "dev"

