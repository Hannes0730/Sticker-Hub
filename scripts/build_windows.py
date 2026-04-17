from __future__ import annotations

import argparse
import ctypes
import subprocess
import sys
from pathlib import Path

from PIL import Image


def _is_access_denied(output: str) -> bool:
    lowered = output.lower()
    return "winerror 5" in lowered or "access is denied" in lowered


def _is_admin() -> bool:
    if sys.platform != "win32":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _run_pyinstaller(spec: Path, distpath: Path, workpath: Path, clean: bool) -> tuple[int, str]:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--distpath",
        str(distpath),
        "--workpath",
        str(workpath),
    ]
    if clean:
        command.append("--clean")
    command.append(str(spec))

    print(f"\nBuilding with dist={distpath} work={workpath}")
    result = subprocess.run(command, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode == 0:
        print("Build succeeded.")
    return result.returncode, f"{result.stdout}\n{result.stderr}"


def _print_elevation_hint(script_path: Path, spec: Path, clean: bool) -> None:
    clean_flag = " --clean" if clean else ""
    command = (
        "Start-Process -Verb RunAs -FilePath \""
        + sys.executable
        + "\" -ArgumentList \""
        + str(script_path)
        + " --spec "
        + str(spec)
        + clean_flag
        + "\""
    )
    print("\nOption 1 (Run as Administrator):")
    print("Run this in PowerShell:")
    print(command)


def _prepare_windows_icon(project_root: Path) -> None:
    png_icon = project_root / "assets" / "icon.png"
    ico_icon = project_root / "assets" / "icon.ico"

    if not png_icon.exists():
        print(f"Icon source not found, skipping icon conversion: {png_icon}")
        return

    try:
        with Image.open(png_icon) as image:
            rgba = image.convert("RGBA")

            width, height = rgba.size
            if width != height:
                side = min(width, height)
                left = (width - side) // 2
                top = (height - side) // 2
                rgba = rgba.crop((left, top, left + side, top + side))

            rgba.save(
                ico_icon,
                format="ICO",
                sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
            )
        print(f"Prepared Windows icon: {ico_icon}")
    except Exception as exc:
        print(f"Failed to prepare Windows icon from {png_icon}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build StickerHub in project-local dist/build with WinError 5 guidance."
    )
    parser.add_argument("--spec", default="StickerHub.spec")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    spec = (project_root / args.spec).resolve() if not Path(args.spec).is_absolute() else Path(args.spec)

    if not spec.exists():
        print(f"Spec file not found: {spec}")
        return 2

    _prepare_windows_icon(project_root)

    primary_dist = project_root / "dist"
    primary_work = project_root / "build"

    code, output = _run_pyinstaller(spec, primary_dist, primary_work, args.clean)
    if code == 0:
        return 0

    if not _is_access_denied(output):
        print("Build failed for a reason other than access denied. See output above.")
        return code

    print("\nDetected Windows access denied (WinError 5).")
    print("This usually means a file is locked (for example, app running from dist) or permission is restricted.")
    if _is_admin():
        print("You are already running elevated, so this is likely a lock from a running process or antivirus scan.")
    else:
        print("Try rerunning as Administrator.")

    print("\nAdditional checks:")
    print("  - Close any running app started from dist\\StickerHub")
    print("  - Exclude project dist/build from antivirus real-time scanning if needed")

    _print_elevation_hint(Path(__file__).resolve(), spec, args.clean)
    return 1



if __name__ == "__main__":
    raise SystemExit(main())
