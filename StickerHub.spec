# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_root = Path(globals().get("SPECPATH", Path.cwd())).resolve()
icon_file = project_root / "assets" / "icon.ico"
png_icon_file = project_root / "assets" / "icon.png"
pyproject_file = project_root / "pyproject.toml"
datas = []
if png_icon_file.exists():
    datas.append((str(png_icon_file), "assets"))
if pyproject_file.exists():
    datas.append((str(pyproject_file), "."))


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StickerHub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    icon=str(icon_file) if icon_file.exists() else None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StickerHub',
)
