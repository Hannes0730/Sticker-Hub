from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import requests

ProgressCallback = Callable[[int, int | None], None]


@dataclass(frozen=True)
class UpdateInstallResult:
    started: bool
    message: str


def start_in_app_update(
    download_url: str,
    asset_name: str,
    latest_version: str,
    progress_callback: ProgressCallback | None = None,
) -> UpdateInstallResult:
    if sys.platform != "win32":
        return UpdateInstallResult(False, "In-app updates are currently supported on Windows only.")

    if not getattr(sys, "frozen", False):
        return UpdateInstallResult(
            False,
            "In-app replace is available only in packaged builds. Use GitHub release download in dev mode.",
        )

    cleaned_url = str(download_url or "").strip()
    cleaned_name = str(asset_name or "").strip()
    if not cleaned_url:
        return UpdateInstallResult(False, "No update download URL found.")

    if not cleaned_name:
        cleaned_name = f"StickerHub-{latest_version}.zip"

    staging_dir = Path(tempfile.gettempdir()) / "StickerHub" / "updates"
    staging_dir.mkdir(parents=True, exist_ok=True)
    staged_asset = staging_dir / cleaned_name

    try:
        _download_file(cleaned_url, staged_asset, progress_callback=progress_callback)
    except Exception as exc:
        return UpdateInstallResult(False, f"Failed to download update: {exc}")

    suffix = staged_asset.suffix.lower()
    if suffix == ".zip":
        try:
            _launch_zip_updater(staged_asset)
        except Exception as exc:
            return UpdateInstallResult(False, f"Failed to start updater: {exc}")
        return UpdateInstallResult(True, f"Updating to v{latest_version}...")

    if suffix in {".exe", ".msi"}:
        try:
            _launch_installer(staged_asset)
        except Exception as exc:
            return UpdateInstallResult(False, f"Failed to launch installer: {exc}")
        return UpdateInstallResult(True, f"Launching installer for v{latest_version}...")

    return UpdateInstallResult(False, f"Unsupported update asset type: {staged_asset.suffix}")


def _download_file(url: str, target_path: Path, progress_callback: ProgressCallback | None = None) -> None:
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    total: int | None = None
    content_length = response.headers.get("Content-Length", "").strip()
    if content_length.isdigit():
        total = int(content_length)

    downloaded = 0
    temp_path = target_path.with_suffix(target_path.suffix + ".part")
    with temp_path.open("wb") as stream:
        for chunk in response.iter_content(chunk_size=1024 * 64):
            if not chunk:
                continue
            stream.write(chunk)
            downloaded += len(chunk)
            if progress_callback:
                progress_callback(downloaded, total)

    temp_path.replace(target_path)


def _launch_installer(installer_path: Path) -> None:
    flags = 0
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        flags |= subprocess.CREATE_NO_WINDOW
    if hasattr(subprocess, "DETACHED_PROCESS"):
        flags |= subprocess.DETACHED_PROCESS
    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        flags |= subprocess.CREATE_NEW_PROCESS_GROUP

    subprocess.Popen([str(installer_path)], creationflags=flags, close_fds=True)


def _launch_zip_updater(zip_path: Path) -> None:
    current_exe = Path(sys.executable).resolve()
    app_dir = current_exe.parent
    pid = os.getpid()

    script_dir = Path(tempfile.gettempdir()) / "StickerHub" / "updates"
    script_dir.mkdir(parents=True, exist_ok=True)
    script_path = script_dir / f"apply_update_{pid}.cmd"

    script_content = _render_zip_updater_script(
        zip_path=str(zip_path),
        app_dir=str(app_dir),
        exe_path=str(current_exe),
        pid=pid,
    )
    script_path.write_text(script_content, encoding="utf-8")

    flags = 0
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        flags |= subprocess.CREATE_NO_WINDOW
    if hasattr(subprocess, "DETACHED_PROCESS"):
        flags |= subprocess.DETACHED_PROCESS
    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        flags |= subprocess.CREATE_NEW_PROCESS_GROUP

    subprocess.Popen(["cmd", "/c", str(script_path)], creationflags=flags, close_fds=True)


def _render_zip_updater_script(zip_path: str, app_dir: str, exe_path: str, pid: int) -> str:
    escaped_zip = zip_path.replace("'", "''")
    lines = [
        "@echo off",
        "setlocal",
        f'set "TARGET_PID={pid}"',
        f'set "ZIP_PATH={zip_path}"',
        f'set "APP_DIR={app_dir}"',
        f'set "EXE_PATH={exe_path}"',
        "set \"WORK_DIR=%TEMP%\\StickerHub\\update_work_%RANDOM%%RANDOM%\"",
        "set \"EXTRACT_DIR=%WORK_DIR%\\extract\"",
        "set \"RETRY_COUNT=0\"",
        "set \"MAX_RETRIES=45\"",
        "mkdir \"%EXTRACT_DIR%\" >nul 2>nul",
        "timeout /t 1 /nobreak >nul",
        f"powershell -NoProfile -ExecutionPolicy Bypass -Command \"Expand-Archive -LiteralPath '{escaped_zip}' -DestinationPath '%EXTRACT_DIR%' -Force\"",
        "if errorlevel 1 goto fail",
        "if exist \"%EXTRACT_DIR%\\StickerHub\\StickerHub.exe\" (",
        "  set \"SOURCE_DIR=%EXTRACT_DIR%\\StickerHub\"",
        ") else (",
        "  set \"SOURCE_DIR=%EXTRACT_DIR%\"",
        ")",
        ":copy_retry",
        "robocopy \"%SOURCE_DIR%\" \"%APP_DIR%\" /E /R:2 /W:1 >nul",
        "if errorlevel 8 (",
        "  set /a RETRY_COUNT+=1",
        "  if %RETRY_COUNT% GEQ %MAX_RETRIES% goto fail",
        "  timeout /t 1 /nobreak >nul",
        "  goto copy_retry",
        ")",
        "if not exist \"%EXE_PATH%\" goto fail",
        "start \"\" \"%EXE_PATH%\"",
        "rmdir /s /q \"%WORK_DIR%\" >nul 2>nul",
        "del \"%ZIP_PATH%\" >nul 2>nul",
        "del \"%~f0\" >nul 2>nul",
        "goto end",
        ":fail",
        "echo Sticker Hub update failed at %DATE% %TIME% > \"%TEMP%\\StickerHub\\update_error.log\"",
        "echo zip=%ZIP_PATH% >> \"%TEMP%\\StickerHub\\update_error.log\"",
        "echo app=%APP_DIR% >> \"%TEMP%\\StickerHub\\update_error.log\"",
        "if exist \"%EXE_PATH%\" start \"\" \"%EXE_PATH%\"",
        ":end",
        "endlocal",
    ]
    return "\r\n".join(lines) + "\r\n"




