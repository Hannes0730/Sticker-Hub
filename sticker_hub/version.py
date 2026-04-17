from __future__ import annotations

from importlib import metadata
from pathlib import Path
import tomllib


DISTRIBUTION_NAME = "sticker-hub"


def get_app_version() -> str:
    try:
        return metadata.version(DISTRIBUTION_NAME)
    except metadata.PackageNotFoundError:
        pass

    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if pyproject_path.exists():
        try:
            payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            project = payload.get("project", {})
            version = str(project.get("version", "")).strip()
            if version:
                return version
        except Exception:
            pass

    return "dev"

