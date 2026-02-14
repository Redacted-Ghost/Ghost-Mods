# Ghost-Mods Handoff Document for Codex / ChatGPT

## Project Overview

**Repo:** `https://github.com/Redacted-Ghost/Ghost-Mods.git` (branch: `master`)
**Owner:** Redacted-Ghost
**Purpose:** Custom Fallout 4 HUD + World Map mod suite for the "Wasteland Reborn" Wabbajack modlist, LoreOut profile. Military/STALKER tactical aesthetic throughout.

The project has two main components:
- **Ghost HUD** — A compact FallUI HUD preset with military styling, bundled SWFs from multiple mods, custom minimap, and condition display
- **Ghost Map** — An 8K satellite world map overlay with 818 tactical markers, collectible indicators, threat zones, and a subtle grid

---

## Repo Structure

```
Ghost-Mods/
  .gitignore              # Excludes *.dds, *.ba2 (large binaries)
  README.md               # Public-facing readme
  HANDOFF.md              # THIS FILE

  Ghost-HUD/
    F4SE/Plugins/
      MM_HideUI.txt                    # Menus that hide minimap
      MM_CustomTarget/                 # Minimap custom marker files
        loreout_bobbleheads.txt
        loreout_fusion_cores.txt
        loreout_magazines.txt
        loreout_power_armor.txt
      MM_ShapeData/                    # Minimap icon shape definitions
        0.txt through 100.txt (15 files)
    Interface/
      HUDMenu.swf          (4.5MB)    # Main HUD - from S.T.A.L.K.E.R. HUD Remastered (modified FallUI)
      BodypartsUI.swf       (1.1MB)    # Body condition display - from Condition Boy
      MiniMap.swf           (5KB)      # Minimap core - from Minimal Minimap
      MiniMap_HUD.swf       (128KB)    # Minimap HUD overlay - from Additional Interfaces (square)
      MiniMap_PNG.swf       (1.5MB)    # Minimap PNG renderer - from Additional Interfaces
      Pipboy_MapPage.swf    (165KB)    # Pip-Boy map - from FallUI Map
      PromptMenu.swf        (64KB)     # Prompt UI - from FallUI HUD
      Workshop.swf          (118KB)    # Workshop UI - from FallUI HUD
      FallUI HUD/
        Importable HUD Layouts/
          Ghost HUD.ini                # Importable layout preset (FallUI format)
        Translation/
          Translate_en.txt             # English HUD translations
      FallUI Map/
        Marker Color Sets/
          Ghost.ini                    # Custom marker color set (14 colors)
    MCM/
      Config/
        ConditionBoy/    config.json, lib.swf, settings.ini
        FallUIHUD/       config.json, lib.swf, settings.ini
        FallUIMap/       config.json, lib.swf, settings.ini
      Settings/
        FallUI.ini                     # FallUI base settings
        FallUIHUD.ini                  # Main HUD MCM settings + widget layout
        SSW.ini                        # SSW widget settings
        Presets/
          Ghost Unified HUD.ini        # One-click MCM preset for all HUD mods

  Ghost-Map/
    preview.png            (8.8MB)     # 2K preview of the generated map
    textures/interface/pip-boy/        # Empty - DDS is gitignored, regenerate with tools

  Tools/
    generate_ghost_map.py              # 8K map overlay generator (Python + Pillow)
    fo4_esp_parser.py                  # Fallout 4 ESP/ESM binary parser library
    extract_collectibles.py            # Collectible location extractor
```

---

## Live Mod Location (on user's machine)

The actual installed mod is at:
```
C:\Modlists\WastelandReborn\mods\[nodelete] LoreOut Custom HUD\
```

This is a MO2 (Mod Organizer 2) virtual filesystem mod. The repo's `Ghost-HUD/` folder maps to this location but with "LoreOut" branding instead of "Ghost" in filenames:
- `Ghost HUD.ini` (repo) = `LoreOut HUD.ini` (live)
- `Ghost.ini` color set (repo) = `LoreOut.ini` (live)
- `Ghost Unified HUD.ini` (repo) = `LoreOut Unified HUD.ini` (live)

The map generator lives at:
```
C:\Modlists\WastelandReborn\Tools\esp_parser\generate_map_overlay.py
```
(This is the same script as `Tools/generate_ghost_map.py` in the repo, with hardcoded paths pointing to the local modlist.)

---

## Technical Architecture

### HUD System (FallUI-based)

The HUD uses **FallUI HUD**'s widget positioning system. Every HUD element is controlled via INI keys in this format:

```
s<GroupName>__<WidgetName>=on:<X>x<Y>*<scaleX>*<scaleY>r<rotation>:<properties>
```

**Groups and their screen anchors:**
- `sCenterGroup_mc` — Screen center (crosshair, quickloot, rollover)
- `sLeftMeters_mc` — Bottom-left (HP, AP, rads, location text)
- `sRightMeters_mc` — Bottom-right (ammo, flashlight, active effects, fatigue)
- `sTopCenterGroup_mc` — Top-center (enemy health, stealth meter)
- `sBottomCenterGroup_mc` — Bottom-center (compass, crit meter, subtitles)
- `sHUDNotificationsGroup_mc` — Left side (quest updates, messages, XP, tutorials)

**Coordinates are RELATIVE to the group anchor**, not absolute screen positions. Negative X moves left, negative Y moves up from the anchor point.

**Key properties in widget strings:**
- `Cl=<int>` — Color as decimal integer (e.g., `11867648` = `0xB54200` burnt orange)
- `hideBracket=true` — Hides FallUI's bracket decorations
- `textFontType=0` — Font index (0=default, 1=bold, 16=special)
- `*barSlices=N` — Number of segments in bar meters
- `*barGrV=true` — Gradient on bar
- `_fuiPerVis=true` — FallUI persistent visibility
- `SV=false` — Shadow visible
- `GrV=true` — Gradient visible

### Color Palette (current)
```
ColorSlot1 = 0x8CABE1  (muted blue-grey)
ColorSlot2 = 0x53E13A  (green — HP/AP bars)
ColorSlot3 = 0xFFFFFF  (white — text)
ColorSlot4 = 0xB54200  (burnt orange — hit indicators)
```

### Map System

The map overlay is generated by `generate_ghost_map.py` (Python 3 + Pillow). It:

1. Reads a base satellite DDS texture
2. Parses two ESP files for map marker locations (Cartographers + Map Marker Overhaul)
3. Loads collectible CSVs (bobbleheads, magazines, power armor, fusion cores, traders)
4. Draws programmatic icons at each location (no external image assets)
5. Adds text labels, grid, threat zones, collectible indicators
6. Outputs 8K DXT1-compressed DDS with 12 mipmap levels

**Coordinate system:** 62x62 cell grid mapping world coordinates to 8192x8192 pixels:
```python
WORLD_X_MIN = -135168.0, WORLD_X_MAX = 118784.0
WORLD_Y_MIN = -147456.0, WORLD_Y_MAX = 106496.0
```

**Icon rendering:** All icons are drawn programmatically using PIL, rendered at 4x resolution then downscaled with LANCZOS for anti-aliasing.

### FallUI Map Color Set

The `LoreOut.ini` / `Ghost.ini` color set maps Fallout 4's native marker types to STALKER-themed colors. FallUI Map reads this and colorizes the game's interactive markers accordingly. This works alongside the static map overlay — the overlay shows the satellite texture with baked icons/labels, while FallUI Map provides clickable/searchable colored markers on top.

---

## External Dependencies (Cannot Be Bundled)

These mods must remain installed — we only need their DLLs/ESPs, not their SWF/INI files (ours override those):

| Mod | What We Need | Why |
|-----|-------------|-----|
| **F4SE** | Script extender runtime | All F4SE plugins depend on it |
| **MCM** (Mod Configuration Menu) | MCM framework | All MCM config trees need it |
| **Minimal Minimap** | `MinimalMinimap.dll` | F4SE plugin that feeds real-time data to minimap SWFs |
| **Condition Boy** | `BodyPartsUI.dll` + `ConditionBoy.esp` | F4SE plugin for body condition display |
| **FallUI - HUD** | Nothing (we bundle everything) | But it's the framework our SWFs are built on |
| **FallUI - Map** | Nothing (we bundle everything) | But `Pipboy_MapPage.swf` is theirs |

---

## What's Been Completed

1. **Ghost HUD v3** — Compact military layout with S.T.A.L.K.E.R. coordinate system, reduced scales
2. **Ghost Map v5** — Quality overhaul with larger icons (14-26px), Impact/Bahnschrift fonts, subtle grey grid, no baked legend, reduced threat zone alpha
3. **FallUI Map Color Set** — 14-color STALKER palette mapping all marker types
4. **MCM Unified Preset** — One-click apply for FallUIHUD + ConditionBoy + MinimalMinimap + WmkActiveEffects + FallUIMap
5. **SWF Bundling** — All 8 SWFs from 6 different mods bundled into one standalone mod
6. **DDS Mipmap Fix** — Proper 12-level mipmap chain in DXT1 compression (fixed CreateTexture2D crash)
7. **GitHub Repo** — Everything pushed to `Redacted-Ghost/Ghost-Mods`

---

## What's Left To Do (Next Steps)

### Priority 1: SWF Customization (Deep Custom Visuals)

The current SWFs are copies from other mod authors. To make truly custom visuals, they need to be decompiled and modified using **JPEXS Free Flash Decompiler (FFDec)**:
- Download: https://github.com/nickshanks/jpexs-decompiler/releases
- The main target is `HUDMenu.swf` (4.5MB) — this contains all the bar shapes, frame graphics, icons, and layout logic
- Decompiled ActionScript from the FallUI Map SWF already exists at `C:\Modlists\WastelandReborn\Tools\swf_analysis\`

**What can be changed in SWFs:**
- Bar shapes (HP/AP/XP meters — currently using S.T.A.L.K.E.R.'s sliced bar style)
- Frame/border graphics around UI elements
- Icon assets (compass markers, weapon type icons)
- Animation timelines (fade effects, transitions)
- Color constants hardcoded in ActionScript

**Approach:**
1. Open SWF in JPEXS
2. Navigate to shapes/sprites for the element you want to change
3. Edit the vector graphics or replace with custom shapes
4. Export modified SWF
5. Test in-game via MO2

### Priority 2: MO2 Load Order Verification

Ensure the `[nodelete] LoreOut Custom HUD` mod wins all file conflicts in MO2's left pane (should be loaded after all the source mods it overrides):
- After S.T.A.L.K.E.R. HUD Remastered
- After FallUI - HUD
- After FallUI - Map
- After Minimal Minimap
- After Condition Boy
- After Additional Interfaces

### Priority 3: In-Game Testing

The v5 map and v3 HUD layout haven't been verified in-game together yet. Need to:
1. Launch FO4 via MO2 with LoreOut profile
2. Check Pip-Boy map — verify satellite overlay with larger icons is visible and readable
3. Check HUD layout — verify all elements positioned correctly (HP/AP bottom-left, ammo bottom-right, compass bottom-center)
4. Check MCM → FallUI Map → verify "LoreOut" color set is active
5. Check MCM → MCM Settings Manager → apply "LoreOut Unified HUD" preset → verify all settings apply

### Priority 4: Custom HUD Full Rebuild

The user wants to eventually build a completely new HUD from scratch — not just repositioned vanilla/STALKER elements, but truly custom bar shapes, icons, and layout. This requires:
1. Learning the FallUI HUD SWF structure (how widgets are defined in Flash)
2. Designing new bar shapes (angular/military style)
3. Designing new frame graphics
4. Implementing in JPEXS or Adobe Animate
5. Testing each modified SWF individually

---

## Key File Formats

### FallUI HUD Layout INI
```ini
[ExportInfo]
sExportTime=2026-02-14 18:00

[HUDConfig]
sLayoutGlobalSettings=ColorSlot4;i;11867648;...
sCenterGroup_mc__HUDCrosshair_mc=on:0x0*0.55*0.55r0:Cl=16777215,...
sLeftMeters_mc__HPMeter_mc=on:-14x-100*0.5*0.5r0:hpbarSV=true,...
```

### FallUI Map Color Set INI
```ini
[Colors]
sColor:Green = 80,220,80
sColor:Red = 220,50,50

[WorldMapHolder]
sMarkerColor:CityMarker,SettlementMarker = Green
sMarkerColor:MilitaryBaseMarker = Red
```

### MCM Unified Preset INI
```ini
[MCMSettings]
sSettings={ModName:{ini:{Section:{key:value,...}}},AnotherMod:{...}}
```
This is a single-line JSON blob inside an INI file. Each mod has its own nested object with sections and key-value pairs.

### DDS with Mipmaps (DXT1)
The map generator outputs proper DXT1-compressed DDS with:
- 128-byte header with flags: CAPS|HEIGHT|WIDTH|PIXELFORMAT|MIPMAPCOUNT|LINEARSIZE
- Caps: TEXTURE|COMPLEX|MIPMAP
- 12 mip levels (8192 down to 4x4)
- Each mip compressed to DXT1 4x4 blocks (8 bytes per block)

---

## Coding Conventions

- Python scripts use `snake_case` for functions and variables
- INI keys use FallUI's format: `bBoolSetting`, `iIntSetting`, `fFloatSetting`, `sSetting`
- Colors in INI are decimal integers (use `hex()` to convert: `11867648` = `0xB54200`)
- Colors in color sets are `R,G,B` tuples (0-255)
- Coordinates in widget strings are `XxY` format (e.g., `-14x-100`)
- Scale in widget strings is `*scaleX*scaleY` (e.g., `*0.5*0.5`)
- Rotation in widget strings is `r<degrees>` (e.g., `r0`, `r-90`)

---

## Git Workflow

- Default branch: `master`
- Binary assets (`.dds`, `.ba2`) are gitignored — regenerate via Python tools
- SWF files ARE committed (they're the core mod assets)
- Commit messages should describe what changed and why
- Always include `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>` or the appropriate AI credit

---

## User Preferences

- Military/STALKER aesthetic throughout
- Small, non-intrusive UI elements
- Clean and modern looking while maintaining old-school Fallout vibes
- No unnecessary clutter (hidden brackets, vault boy disabled, etc.)
- GitHub username: `Redacted-Ghost`
- Modlist: Wasteland Reborn (Wabbajack), profile: LoreOut
- Using MO2 (Mod Organizer 2) on Windows
