<h1 align="center">Stickers Hub</h1>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white" />
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white" />
  <img alt="License" src="https://img.shields.io/github/license/Hannes0730/Sticker-Hub" />
  <img alt="Latest Release" src="https://img.shields.io/github/v/release/Hannes0730/Sticker-Hub?display_name=tag" />
  <img alt="Open Issues" src="https://img.shields.io/github/issues/Hannes0730/Sticker-Hub" />
</p>

<img src="assets/icon.png" alt="Stickers Hub Icon" width="360" />

Stickers Hub is a desktop app that collects stickers from sources like SigStick, Sticker.ly, and more. Pick a sticker, click once, and it is copied so you can paste it directly into Messenger, Instagram, Facebook, Telegram, and similar platforms.

If an animated sticker is sent as a static image on a platform, switch copy mode to GIF for better animation compatibility.

## What You Can Do

- Import sticker packs from URLs
- Organize stickers into categories
- Click a sticker to copy it instantly
- Drag stickers into supported apps
- Convert copy output to `Original`, `GIF`, or `WebP`
- Keep imports persistent even if `%TEMP%` is cleared

## Quick Start (For Users)

1. Open Stickers Hub.
2. Click `Import URL`.
3. Paste a sticker pack link.
4. Open a category and click a sticker to copy.
5. Paste into your chat app.

## If Animated Stickers Become Static

Some platforms do not play all animated formats consistently.

- Set copy mode to `GIF` for better compatibility.
- If quality is more important and the platform supports it, try `Original` or `WebP`.

## Supported Formats

- PNG
- JPG/JPEG
- GIF
- WebP

## Data Locations

- Persistent sticker catalog:
  - `C:\Users\<you>\Documents\StickerHub\stickers.json`
- Download/cache files (safe to clear):
  - `%TEMP%\StickerHub`

You can clear `%TEMP%` anytime; Stickers Hub will re-download cached files as needed while keeping imported URLs in `Documents`.

## Install and Run From Source

```powershell
python -m pip install -e .
python .\main.py
```

## Build Windows EXE

```powershell
python .\scripts\build_windows.py --clean
```

Build output:

- `dist\StickerHub`
- Release artifact: `StickerHub-win64.zip` (recommended for users)

If you see `WinError 5` during build, close running app instances from `dist\StickerHub` and retry.

## Import Notes

- Duplicate URLs are skipped automatically.
- `Upgrade URLs` can improve existing entries to preferred full-size links.
- Imported stickers are saved without forced display names.

## Smoke Test

```powershell
python .\tests\smoke_test.py
```
