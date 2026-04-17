# Sticker Board (PySide6)

Modern desktop sticker manager inspired by Discord's sticker picker.

## Features

- Dark modern UI with sidebar categories, search, and responsive sticker grid
- Rounded sticker cards with hover/selection visuals
- Async downloads (`QThreadPool`) so the UI stays responsive
- Local cache with duplicate URL prevention on import
- PNG/JPG/GIF/WebP support with animated preview for GIF/WebP (`QMovie`)
- Drag-and-drop as local file URL (file path), compatible with apps like Discord
- Left click copies a send-ready file URL; right click shows Copy/Save As/Open Folder
- Copy format selector (`Original`, `GIF`, `WebP`) with fallback to original if conversion fails
- Optional Favorites and Recent categories

## Sticker Data Format

`stickers.json`

```json
{
  "CategoryName": [
    {
      "name": "optional",
      "image_url": "https://..."
    }
  ]
}
```

## Runtime Data Location

- Runtime catalog is auto-created at `~/Documents/StickerHub/stickers.json`.
- Windows example: `C:\Users\<you>\Documents\StickerHub\stickers.json`.
- On first run, this file is seeded from bundled/project `stickers.json` (if available).
- Optional override for advanced users: set `STICKER_HUB_DATA_DIR`.

## Run From Source

```powershell
python -m pip install -e .
python .\main.py
```

## Build EXE (Windows)

Build always targets project-local `dist` and `build`.

```powershell
python .\scripts\build_windows.py --clean
```

Build output:
- `./dist/StickerHub`

If you hit `WinError 5` (`Access is denied`):
- close any running app from `dist\StickerHub`
- rerun as Administrator
- check antivirus locks on `dist` / `build`

Admin rerun example:

```powershell
Start-Process -Verb RunAs -FilePath python -ArgumentList ".\scripts\build_windows.py --clean"
```

## Import From UI

1. Click `Import URL`.
2. Paste a direct image URL or a sticker pack/page URL.
3. Choose category (default `Imported`).
4. Confirm import; grid refreshes immediately.

Notes:
- Direct media URLs (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`) give best results.
- Page URLs are parsed for candidate image links.
- Duplicate URLs are skipped automatically.
- Imported stickers are stored without display names.

## Copy Behavior

- `Original`: keeps downloaded format.
- `GIF` / `WebP`: attempts conversion before copy.
- If conversion fails, app falls back to original format automatically.

## Project Structure

- `main.py` - entry point
- `scripts/build_windows.py` - Windows build helper
- `sticker_hub/app.py` - app bootstrap
- `sticker_hub/paths.py` - runtime data path helpers
- `sticker_hub/theme.py` - dark theme stylesheet
- `sticker_hub/models/sticker_models.py` - models + JSON load/write + dedupe
- `sticker_hub/services/cache_service.py` - cache + send-copy handling
- `sticker_hub/services/downloader.py` - threaded download orchestration
- `sticker_hub/workers/download_worker.py` - worker job for fetch/thumbnail
- `sticker_hub/ui/main_window.py` - main UI shell
- `sticker_hub/ui/sticker_grid.py` - responsive grid widget
- `sticker_hub/ui/sticker_card.py` - interactive sticker card
- `sticker_hub/utils/image_utils.py` - image format/animation helpers
- `tests/smoke_test.py` - non-GUI smoke test

## Smoke Test

```powershell
python .\tests\smoke_test.py
```
