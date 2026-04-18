<h1 align="center">Stickers Hub</h1>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white" />
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white" />
  <img alt="License" src="https://img.shields.io/github/license/Hannes0730/Sticker-Hub?color=green" />
  <img alt="Latest Release" src="https://img.shields.io/github/v/release/Hannes0730/Sticker-Hub?display_name=tag" />
  <img alt="Open Issues" src="https://img.shields.io/github/issues/Hannes0730/Sticker-Hub" />
  <img alt="Total Downloads" src="https://img.shields.io/github/downloads/Hannes0730/Sticker-Hub/total" />
</p>

<p align="center">
  <img src="assets/icon.png" alt="Stickers Hub Icon" width="120" />
</p>

Stickers Hub is a Windows desktop app that imports sticker packs (SigStick, Sticker.ly, and more), organizes them, and lets you copy/send stickers fast.

Click a sticker once to copy it, then paste in Messenger, Instagram, Facebook, Telegram, or other supported chat platforms.

## Summary

- Import from pack URLs and direct image URLs
- Browse by **Category** in the left sidebar
- Filter by **Pack** with the top pack dropdown
- Click to copy, drag-and-drop to apps, or save locally
- If animation is lost on send, switch copy mode to `GIF`

## How To Use

1. Open Stickers Hub.
2. Click `Import URL`.
3. Enter:
   - `Category` (parent group, for example `Cats`)
   - `Pack Name` (for example `Nailong Pack`)
4. Pick the category in the sidebar.
5. (Optional) Pick a pack from the pack dropdown.
6. Click a sticker to copy, then paste in your chat app.

## Delete Actions

- **Delete whole category:** right-click a custom category in the sidebar, then choose delete.
- **Delete selected pack:** choose a pack in the pack dropdown, then click `Delete Pack`.

Both actions ask for confirmation before removing data.

## Animation Notes

- Animated stickers play while the app window is active.
- Animations pause when the app is inactive or minimized.
- Some platforms send animated files as static; use `Copy: GIF` for better compatibility.

## Platform Compatibility Guide

Different chat platforms handle pasted sticker files differently. Use this as a quick reference for the best copy mode per app.

| Platform | Original | GIF | WebP |
| :-- | :--: | :--: | :--: |
| **Facebook Messenger** | ❌ No | ✅ Yes | ❌ No |
| **Instagram** | ⚠️ Yes (BG) | ⚠️ Yes (BG) | ⚠️ Yes (BG) |
| **Telegram** | ❌ No | ⚠️ Yes (BG) | ❌ No |
| **Discord** | ❌ No | ✅ Yes | ✅ Yes |

**Legend**
- `✅ Yes`: Sticker is sent as animated on that platform.
- `⚠️ Yes (BG)`: Sticker is sent as animated, but platform may force a solid background.
- `❌ No`: Format is not reliably supported for direct paste/send and only resulted to a static image.

> **Note:** `(BG)` means the platform adds a solid background color when pasted, so transparent edges may not be preserved.

## Sticker JSON Structure

Stickers Hub supports both legacy flat format and nested pack format.

### Nested format (recommended)

```json
{
  "Cats": {
    "Nailong Pack": {
      "sticker_pack_url": "https://example.com/pack",
      "stickers": [
        { "name": "", "image_url": "https://..." }
      ]
    }
  }
}
```

### Legacy flat format (still supported)

```json
{
  "Imported": [
    { "name": "", "image_url": "https://..." }
  ]
}
```

## Supported Formats

- PNG
- JPG/JPEG
- GIF
- WebP

## Data Locations

- Persistent catalog:
  - `C:\Users\<you>\Documents\StickerHub\stickers.json`
- Download/cache files (safe to clear):
  - `%TEMP%\StickerHub`

Clearing `%TEMP%` removes cached files only. Imported sticker URLs remain in `Documents`.

## Run From Source

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
- Release asset: `StickerHub-win64.zip` (recommended)

If you hit `WinError 5`, close running app instances from `dist\StickerHub` and retry.

## Maintenance

- `Upgrade URLs` can rewrite entries to preferred full-size links and clean duplicates.
- Duplicate imports are skipped automatically.

## Smoke Test

```powershell
python .\tests\smoke_test.py
```
