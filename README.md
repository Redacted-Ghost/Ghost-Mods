# Ghost Mods - Fallout 4

Custom HUD and World Map mods for Fallout 4, designed for the Wasteland Reborn modlist. Military/STALKER-inspired tactical aesthetic.

## Ghost HUD

A compact, minimal FallUI HUD preset with a military-tactical look.

**Features:**
- Scaled-down UI elements (30-50% smaller than default STALKER HUD)
- Thin HP/AP/Rads bars (12px height, 180px width)
- Compact ammo counter with no background clutter
- Smaller compass widget (0.35 scale)
- Hidden brackets, vault boy, and unnecessary vanilla elements
- Military color palette (olive teal, amber warnings, soft white text)
- Clean dot crosshair at 55% scale
- Smaller active effects, notifications, and messages

**Requires:**
- [FallUI - HUD](https://www.nexusmods.com/fallout4/mods/51813)
- [Minimal Minimap](https://www.nexusmods.com/fallout4/mods/64937)
- [ConditionBoy - FO4 HUD](https://www.nexusmods.com/fallout4/mods/35813)
- [Active Effects on HUD](https://www.nexusmods.com/fallout4/mods/32735)

**Install:** Copy the `Ghost-HUD` folder contents into your Fallout 4 Data directory or create a mod in MO2/Vortex.

## Ghost Map

An 8K tactical satellite world map overlay with 818 custom markers for every discoverable location and collectible.

**Features:**
- 8192x8192 DXT1-compressed DDS with full 12-level mipmap chain
- 604 location markers with 8 tactical icon types (settlement, vault, military, metro, city, police, POI, other)
- 214 collectible indicators (bobbleheads, magazines, power armor, fusion cores, traders)
- Gold dashed grid overlay, military-style legend
- Collectibles grouped to nearest locations for clean display

**Requires:**
- [FallUI - Map](https://www.nexusmods.com/fallout4/mods/49920)
- Python 3.8+ with Pillow (for regenerating the map)

**Regenerate the map DDS:**
```bash
cd Tools
python generate_ghost_map.py
```
Note: You'll need the source satellite map DDS and ESP files from your modlist. Edit paths at the top of the script.

## Tools

- `generate_ghost_map.py` - Generates the 8K world map overlay from ESP data
- `fo4_esp_parser.py` - Parses Fallout 4 ESP/ESM files for map marker data
- `extract_collectibles.py` - Extracts bobblehead, magazine, and collectible locations

## License

Free to use and modify. Credit appreciated.
