#!/usr/bin/env python3
"""
LoreOut Completionist Map Generator v5 -- Quality Overhaul
==============================================================
Professional completionist world map overlay for Fallout 4
with clean STALKER/military aesthetic.

All icons drawn programmatically -- no external assets needed.
4x supersampled for crisp anti-aliasing at any zoom level.

Changes from v4:
  - Larger icons (survive 16:1 downscale to Pip-Boy resolution)
  - Military fonts: Impact for major locations, Bahnschrift for regular
  - Larger font sizes (42pt major, 32pt regular, 40pt grid)
  - Subtle grey continuous grid lines (replaced gold dashed)
  - Tighter label placement with collision detection
  - Removed baked legend (FallUI Map color system handles this)
  - Reduced threat zone alpha for subtler color washes
  - Skip labels for generic POI/other to reduce clutter

Outputs:
  - 8K DXT1-compressed DDS for in-game Pip-Boy world map
  - 2K PNG preview
"""

import struct
import os
import math
import csv
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# =============================================================================
# PATHS
# =============================================================================
BASE = r"C:\Modlists\WastelandReborn"
SOURCE_DDS = os.path.join(BASE, r"mods\[nodelete] Alternative Satellite World Maps\textures\interface\pip-boy\worldmap_d.dds")
OUTPUT_DIR = os.path.join(BASE, r"mods\[nodelete] LoreOut Custom Map\textures\interface\pip-boy")
OUTPUT_DDS = os.path.join(OUTPUT_DIR, "worldmap_d.dds")
OUTPUT_PNG = os.path.join(BASE, r"Tools\esp_parser\worldmap_overlay_preview.png")

CARTOGRAPHERS_ESP = os.path.join(BASE, r"mods\[nodelete] Cartographers Map Markers (Fallout 4 Edition)\CartographersMapMarkers Commonwealth.esp")
MAP_MARKER_ESP = os.path.join(BASE, r"mods\Map Marker Overhaul - Unmarked Locations - Fast Travel - Exploration\MapMarkerREF_Q.esp")

CSV_DIR = os.path.join(BASE, r"Tools\esp_parser\collectible_data")

# =============================================================================
# MAP COORDINATE SYSTEM -- 62x62 cells (SQUARE)
# =============================================================================
IMG_SIZE = 8192
WORLD_X_MIN = -135168.0
WORLD_X_MAX = 118784.0
WORLD_Y_MIN = -147456.0
WORLD_Y_MAX = 106496.0
WORLD_X_RANGE = WORLD_X_MAX - WORLD_X_MIN   # 253952
WORLD_Y_RANGE = WORLD_Y_MAX - WORLD_Y_MIN   # 253952

def world_to_pixel(wx, wy):
    px = ((wx - WORLD_X_MIN) / WORLD_X_RANGE) * IMG_SIZE
    py = ((WORLD_Y_MAX - wy) / WORLD_Y_RANGE) * IMG_SIZE
    return int(px), int(py)

# =============================================================================
# COLORS -- Military / STALKER tactical palette
# =============================================================================
WHITE = (255, 255, 255, 255)
WHITE_DIM = (210, 210, 200, 230)
ICON_WHITE = (240, 240, 230, 245)       # Slightly warm white for military feel
SHADOW = (0, 0, 0, 170)
OUTLINE_DARK = (10, 10, 5, 200)

# v5: Subtle grey grid -- nearly invisible, doesn't compete with markers
GRID_COLOR = (160, 160, 160, 30)
GRID_LABEL_COLOR = (180, 175, 160, 120)

# Dashed border -- dark tactical
BORDER_COLOR = (50, 45, 30, 150)

# Category text colors -- STALKER-inspired (muted military tones)
LABEL_COLORS = {
    'settlement':   (90, 200, 90, 255),     # Friendly green
    'vault':        (70, 140, 230, 255),     # Intel blue
    'military':     (220, 60, 50, 255),      # Hostile/danger red
    'metro':        (60, 200, 200, 255),     # Infrastructure cyan
    'police':       (100, 155, 230, 255),    # Authority blue
    'city':         (230, 220, 180, 255),    # Warm white/parchment
    'other':        (170, 170, 160, 200),    # Neutral grey
    'poi':          (200, 180, 100, 200),    # Recon amber
}

# Collectible indicator colors (small tactical symbols)
COLLECT_COLORS = {
    'bobblehead':   (240, 220, 60, 255),    # High-value gold
    'magazine':     (200, 110, 200, 255),    # Intel purple
    'power_armor':  (240, 170, 50, 255),     # Equipment orange
    'fusion_core':  (80, 220, 240, 255),     # Energy cyan
    'trader':       (200, 175, 60, 255),     # Commerce gold
}

# v5: LARGER icon sizes -- must survive 16:1 downscale to Pip-Boy
# At 8192 displayed at ~512, each source pixel = 0.0625 display pixels
# Icons need to be 16-28px to appear as 1-2px visible markers
ICON_SIZES = {
    'city':       26,    # Major locations -- must be very visible
    'vault':      26,    # Key locations
    'military':   24,    # Key locations
    'settlement': 24,    # Key locations
    'metro':      20,    # Secondary
    'police':     20,    # Secondary
    'other':      14,    # Background markers (slightly larger than v4)
    'poi':        14,    # Recon targets
}

# v5: Larger collectible icons
COLLECT_ICON_SIZES = {
    'bobblehead':   16,  # High-value, must be visible
    'magazine':     14,  # Important
    'power_armor':  16,  # Important
    'fusion_core':  10,  # Less important but still visible
    'trader':       14,  # Important for gameplay
}
COLLECT_ICON_DEFAULT = 10

# =============================================================================
# THREAT ZONES -- v5: reduced alpha for subtler color washes
# =============================================================================
THREAT_ZONES = [
    {'name': 'Safe Zone (1-10)', 'color': (0, 180, 0, 8),
     'polygon': [(-135168, 114688), (-135168, 20000), (-60000, 20000),
                 (-60000, 60000), (-20000, 60000), (-20000, 114688)]},
    {'name': 'Low Risk (5-15)', 'color': (120, 200, 0, 8),
     'polygon': [(-20000, 114688), (-20000, 60000), (40000, 60000),
                 (102400, 60000), (102400, 114688)]},
    {'name': 'Moderate (10-25)', 'color': (200, 200, 0, 7),
     'polygon': [(-60000, 20000), (-60000, -20000), (-20000, -20000),
                 (-20000, 20000), (40000, 60000), (-20000, 60000),
                 (-60000, 60000), (-60000, 20000)]},
    {'name': 'Dangerous (20-35)', 'color': (220, 140, 0, 7),
     'polygon': [(-20000, 20000), (-20000, -20000), (40000, -20000),
                 (40000, 20000), (102400, 20000), (102400, 60000),
                 (40000, 60000)]},
    {'name': 'High Risk (25-40)', 'color': (220, 60, 0, 9),
     'polygon': [(-60000, -20000), (-60000, -60000), (0, -60000),
                 (40000, -60000), (40000, -20000), (-20000, -20000)]},
    {'name': 'Very Dangerous (30-50+)', 'color': (180, 0, 0, 9),
     'polygon': [(40000, -20000), (40000, -60000), (102400, -60000),
                 (102400, -20000)]},
    {'name': 'Extreme (35-50+)', 'color': (150, 0, 0, 11),
     'polygon': [(-60000, -60000), (-60000, -100000), (102400, -100000),
                 (102400, -60000), (40000, -60000), (0, -60000)]},
    {'name': 'Glowing Sea (40+)', 'color': (140, 0, 40, 14),
     'polygon': [(-135168, -60000), (-135168, -147456), (-60000, -147456),
                 (-60000, -100000), (-60000, -60000)]},
]

# =============================================================================
# LOCATION CLASSIFICATION
# =============================================================================
SETTLEMENT_KEYWORDS = [
    'sanctuary', 'red rocket truck stop', 'starlight drive', 'tenpines',
    'abernathy', 'sunshine tidings', 'oberland', 'graygarden', 'gray garden',
    "hangman's alley", 'jamaica plain', 'the castle', 'spectacle island',
    'warwick homestead', 'somerville place', 'murkwater', 'nordhagen',
    'bunker hill', 'covenant', 'county crossing', 'finch farm', 'the slog',
    'croup manor', 'kingsport lighthouse', 'egret tours', 'boston airport',
    'outpost zimonja', 'taffington boathouse', 'coastal cottage',
    'homeplate', 'home plate',
]
VAULT_KEYWORDS = ['vault 111', 'vault 81', 'vault 114', 'vault 75', 'vault 95', 'vault 88', 'vault overlook']
MILITARY_KEYWORDS = [
    'fort hagen', 'fort strong', 'national guard', 'military',
    'gunners plaza', 'south boston checkpoint', 'castle',
    'u.s.s.', 'uss ', 'army', 'sentinel site',
]
METRO_KEYWORDS = ['station', 'metro', 'subway', 'tunnel']
POLICE_KEYWORDS = ['police', 'cambridge police']
CITY_KEYWORDS = ['diamond city', 'goodneighbor', 'the institute', 'faneuil hall', 'prydwen']

def classify_location(name):
    nl = name.lower()
    for kw in VAULT_KEYWORDS:
        if kw in nl: return 'vault'
    for kw in MILITARY_KEYWORDS:
        if kw in nl: return 'military'
    for kw in POLICE_KEYWORDS:
        if kw in nl: return 'police'
    for kw in CITY_KEYWORDS:
        if kw in nl: return 'city'
    for kw in SETTLEMENT_KEYWORDS:
        if kw in nl: return 'settlement'
    for kw in METRO_KEYWORDS:
        if kw in nl: return 'metro'
    return 'other'

# =============================================================================
# ESP PARSER
# =============================================================================
def extract_markers_from_esp(path):
    markers = []
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found")
        return markers
    with open(path, 'rb') as f:
        data = f.read()
    pos = 0
    while pos < len(data):
        if pos + 24 > len(data): break
        rec_type = data[pos:pos+4].decode('ascii', errors='replace')
        data_size = struct.unpack_from('<I', data, pos+4)[0]
        if rec_type == 'GRUP':
            pos += 24; continue
        if rec_type == 'REFR':
            rec_data = data[pos+24:pos+24+data_size]
            sub_pos = 0; x = y = z = None; name = None
            while sub_pos < len(rec_data) - 6:
                st = rec_data[sub_pos:sub_pos+4].decode('ascii', errors='replace')
                ss = struct.unpack_from('<H', rec_data, sub_pos+4)[0]
                sd = rec_data[sub_pos+6:sub_pos+6+ss]
                if st == 'DATA' and ss >= 12:
                    x, y, z = struct.unpack_from('<fff', sd, 0)
                if st == 'FULL' and ss > 0:
                    try: name = sd.decode('utf-8').rstrip('\x00')
                    except: pass
                sub_pos += 6 + ss
            if name and x is not None:
                px, py = world_to_pixel(x, y)
                if 0 <= px < IMG_SIZE and 0 <= py < IMG_SIZE:
                    markers.append({'name': name, 'world_x': x, 'world_y': y,
                                    'px': px, 'py': py, 'category': classify_location(name)})
        pos += 24 + data_size
    return markers

# =============================================================================
# CSV LOADER
# =============================================================================
def load_collectibles_csv(csv_path, category):
    items = []
    if not os.path.exists(csv_path):
        print(f"    WARNING: {csv_path} not found")
        return items
    with open(csv_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            wx, wy = float(row['world_x']), float(row['world_y'])
            px, py = world_to_pixel(wx, wy)
            if 0 <= px < IMG_SIZE and 0 <= py < IMG_SIZE:
                items.append({'name': row['name'], 'location': row.get('location', ''),
                              'world_x': wx, 'world_y': wy, 'px': px, 'py': py,
                              'category': category})
    return items

# =============================================================================
# CUSTOM ICON DRAWING -- All icons drawn at 4x then downscaled for AA
# =============================================================================
_icon_cache = {}

def _make_icon(draw_func, size, color=ICON_WHITE, outline=OUTLINE_DARK):
    """Render an icon at 4x resolution and downscale for AA."""
    S = 4  # supersample factor
    big = size * S
    pad = 4 * S  # padding for outline
    buf = Image.new('RGBA', (big + pad*2, big + pad*2), (0, 0, 0, 0))
    d = ImageDraw.Draw(buf)
    cx, cy = buf.size[0] // 2, buf.size[1] // 2
    # Draw outline (slightly larger, dark)
    draw_func(d, cx, cy, big, outline, offset=2*S)
    # Draw main icon
    draw_func(d, cx, cy, big, color, offset=0)
    # Downscale with LANCZOS
    final = size + 8  # with some padding
    result = buf.resize((final, final), Image.LANCZOS)
    return result

def _draw_settlement(d, cx, cy, s, color, offset=0):
    """Settlement -- NATO-style friendly base: flag/pennant on post."""
    o = offset
    hs = s // 2
    lw = max(2, s // 10)
    # Vertical post
    d.rectangle([cx - lw//2 - o, cy - hs - o, cx + lw//2 + o, cy + hs + o], fill=color)
    # Flag/pennant (triangle pointing right from top of post)
    flag_h = int(hs * 0.7)
    flag_w = int(hs * 0.9)
    flag_pts = [(cx + lw//2 + o, cy - hs - o),
                (cx + lw//2 + flag_w + o, cy - hs + flag_h//2),
                (cx + lw//2 + o, cy - hs + flag_h + o)]
    d.polygon(flag_pts, fill=color)
    # Small base line
    base_w = int(hs * 0.6)
    d.rectangle([cx - base_w - o, cy + hs - lw - o, cx + base_w + o, cy + hs + o], fill=color)

def _draw_vault(d, cx, cy, s, color, offset=0):
    """Vault -- Hardened bunker: circle with crosshairs."""
    o = offset
    r = s // 2 + o
    lw = max(2, s // 10)
    # Outer circle (ring)
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color)
    # Inner cutout
    ri = int(r * 0.6)
    d.ellipse([cx-ri, cy-ri, cx+ri, cy+ri], fill=(0, 0, 0, 0))
    # Crosshair lines
    d.rectangle([cx - lw//2, cy - r, cx + lw//2, cy + r], fill=color)
    d.rectangle([cx - r, cy - lw//2, cx + r, cy + lw//2], fill=color)
    # Center dot
    cd = max(2, r // 4)
    d.ellipse([cx-cd, cy-cd, cx+cd, cy+cd], fill=color)

def _draw_military(d, cx, cy, s, color, offset=0):
    """Military -- NATO unit marker: rectangle with X (combat unit)."""
    o = offset
    hs = s // 2 + o
    hw = int(hs * 0.9)
    lw = max(2, s // 10)
    # Rectangle frame
    d.rectangle([cx-hw, cy-hs, cx+hw, cy+hs], outline=color, width=lw)
    # X inside (crossed swords / combat designation)
    d.line([(cx-hw+lw, cy-hs+lw), (cx+hw-lw, cy+hs-lw)], fill=color, width=lw)
    d.line([(cx+hw-lw, cy-hs+lw), (cx-hw+lw, cy+hs-lw)], fill=color, width=lw)

def _draw_poi(d, cx, cy, s, color, offset=0):
    """POI/Undiscovered -- Recon target: crosshair circle."""
    o = offset
    r = s // 2 + o
    lw = max(1, s // 12)
    # Outer circle (thin)
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=color, width=lw)
    # Short crosshair ticks
    tick = int(r * 0.4)
    d.line([(cx, cy - r - 1), (cx, cy - r + tick)], fill=color, width=lw)
    d.line([(cx, cy + r + 1), (cx, cy + r - tick)], fill=color, width=lw)
    d.line([(cx - r - 1, cy), (cx - r + tick, cy)], fill=color, width=lw)
    d.line([(cx + r + 1, cy), (cx + r - tick, cy)], fill=color, width=lw)

def _draw_metro(d, cx, cy, s, color, offset=0):
    """Metro -- Underground tunnel: circle with horizontal bar."""
    o = offset
    r = s // 2 + o
    lw = max(2, s // 8)
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=color, width=lw)
    bar_h = max(2, lw)
    d.rectangle([cx - r + lw, cy - bar_h, cx + r - lw, cy + bar_h], fill=color)

def _draw_city(d, cx, cy, s, color, offset=0):
    """City -- Urban area: angular skyline silhouette."""
    o = offset
    hs = s // 2 + o
    bw = max(2, s // 5)
    gap = max(1, s // 16)
    # Tall center tower
    d.rectangle([cx - bw//2, cy - hs, cx + bw//2, cy + hs//2], fill=color)
    # Left block (shorter)
    d.rectangle([cx - bw - gap - bw//2, cy - int(hs*0.5), cx - gap - bw//2, cy + hs//2], fill=color)
    # Right block (medium)
    d.rectangle([cx + gap + bw//2, cy - int(hs*0.7), cx + bw + gap + bw//2, cy + hs//2], fill=color)
    # Base line
    d.rectangle([cx - bw - gap - bw//2 - o, cy + hs//2, cx + bw + gap + bw//2 + o, cy + hs//2 + max(1, s//14)], fill=color)

def _draw_police(d, cx, cy, s, color, offset=0):
    """Police -- 6-pointed star badge."""
    o = offset
    r = s // 2 + o
    ri = int(r * 0.5)
    pts = []
    for i in range(12):
        angle = math.pi / 2 + (math.pi * i / 6)
        radius = r if i % 2 == 0 else ri
        pts.append((cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
    d.polygon(pts, fill=color)

def _draw_waypoint(d, cx, cy, s, color, offset=0):
    """Generic waypoint -- small chevron/arrow pointing down."""
    o = offset
    hs = s // 2 + o
    hw = int(hs * 0.7)
    pts = [(cx - hw, cy - hs//2), (cx, cy + hs//2), (cx + hw, cy - hs//2),
           (cx + hw//2, cy - hs//2), (cx, cy), (cx - hw//2, cy - hs//2)]
    d.polygon(pts, fill=color)

# --- Collectible mini-icons ---
def _draw_mini_star(d, cx, cy, s, color, offset=0):
    """High-value target: 4-pointed star."""
    o = offset
    r = s // 2 + o
    ri = int(r * 0.3)
    pts = []
    for i in range(8):
        angle = math.pi / 4 + (math.pi * i / 4)
        radius = r if i % 2 == 0 else ri
        pts.append((cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
    d.polygon(pts, fill=color)

def _draw_mini_intel(d, cx, cy, s, color, offset=0):
    """Intel document: small rectangle with corner fold."""
    o = offset
    hs = s // 2 + o
    bw = max(1, int(hs * 0.8))
    d.rectangle([cx - bw, cy - hs, cx + bw, cy + hs], fill=color)
    fold = max(1, hs // 2)
    tri = [(cx + bw - fold, cy - hs), (cx + bw, cy - hs), (cx + bw, cy - hs + fold)]
    d.polygon(tri, fill=(0, 0, 0, 100))

def _draw_mini_dot(d, cx, cy, s, color, offset=0):
    """Energy/resource: filled dot."""
    o = offset
    r = s // 2 + o
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color)

def _draw_mini_shield(d, cx, cy, s, color, offset=0):
    """Equipment cache: small angular shield."""
    o = offset
    hs = s // 2 + o
    hw = int(hs * 0.7)
    pts = [(cx, cy + hs), (cx - hw, cy - hs//3), (cx - hw, cy - hs),
           (cx + hw, cy - hs), (cx + hw, cy - hs//3)]
    d.polygon(pts, fill=color)

def _draw_mini_diamond(d, cx, cy, s, color, offset=0):
    """Trade/commerce: small diamond."""
    o = offset
    r = s // 2 + o
    pts = [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)]
    d.polygon(pts, fill=color)


# Build icon generators lookup
ICON_GENERATORS = {
    'settlement': _draw_settlement,
    'vault':      _draw_vault,
    'military':   _draw_military,
    'metro':      _draw_metro,
    'city':       _draw_city,
    'police':     _draw_police,
    'other':      _draw_waypoint,
    'poi':        _draw_poi,
}

COLLECT_GENERATORS = {
    'bobblehead':   _draw_mini_star,
    'magazine':     _draw_mini_intel,
    'power_armor':  _draw_mini_shield,
    'fusion_core':  _draw_mini_dot,
    'trader':       _draw_mini_diamond,
}

def get_icon(category, size=None):
    """Get a cached pre-rendered icon image."""
    if size is None:
        size = ICON_SIZES.get(category, 14)
    key = (category, size)
    if key not in _icon_cache:
        gen = ICON_GENERATORS.get(category, _draw_waypoint)
        _icon_cache[key] = _make_icon(gen, size)
    return _icon_cache[key]

def get_collect_icon(category, size=None):
    """Get a cached pre-rendered collectible indicator icon."""
    if size is None:
        size = COLLECT_ICON_SIZES.get(category, COLLECT_ICON_DEFAULT)
    key = ('collect_' + category, size)
    if key not in _icon_cache:
        gen = COLLECT_GENERATORS.get(category, _draw_mini_dot)
        color = COLLECT_COLORS.get(category, (200, 200, 200, 255))
        _icon_cache[key] = _make_icon(gen, size, color=color)
    return _icon_cache[key]

def paste_icon(overlay, icon, cx, cy):
    """Paste a pre-rendered icon centered at (cx, cy)."""
    iw, ih = icon.size
    px = cx - iw // 2
    py = cy - ih // 2
    if px < 0: px = 0
    if py < 0: py = 0
    if px + iw > overlay.size[0]: px = overlay.size[0] - iw
    if py + ih > overlay.size[1]: py = overlay.size[1] - ih
    try:
        overlay.alpha_composite(icon, (px, py))
    except ValueError:
        pass

# =============================================================================
# THREAT ZONE RENDERING
# =============================================================================
def draw_threat_zones(overlay):
    for zone in THREAT_ZONES:
        pixel_poly = [world_to_pixel(wx, wy) for wx, wy in zone['polygon']]
        if len(pixel_poly) >= 3:
            layer = Image.new('RGBA', overlay.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).polygon(pixel_poly, fill=zone['color'])
            overlay.alpha_composite(layer)

# =============================================================================
# v5: SUBTLE CONTINUOUS GRID (replaced gold dashed)
# =============================================================================
GRID_SPACING = 8192.0

def draw_grid(draw, font_grid):
    """Draw subtle continuous grey grid lines with edge labels."""
    start_x = math.ceil(WORLD_X_MIN / GRID_SPACING) * GRID_SPACING
    end_x = math.floor(WORLD_X_MAX / GRID_SPACING) * GRID_SPACING
    start_y = math.ceil(WORLD_Y_MIN / GRID_SPACING) * GRID_SPACING
    end_y = math.floor(WORLD_Y_MAX / GRID_SPACING) * GRID_SPACING

    col_labels = []
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        col_labels.append(f"1{c}")
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        col_labels.append(f"2{c}")

    # v5: Simple continuous lines, width=1, very subtle
    col_idx = 0
    wx = start_x
    while wx <= end_x:
        px, _ = world_to_pixel(wx, 0)
        if 60 < px < IMG_SIZE - 60:
            draw.line([(px, 0), (px, IMG_SIZE)], fill=GRID_COLOR, width=1)
            if col_idx < len(col_labels):
                draw.text((px - 12, 16), col_labels[col_idx],
                          font=font_grid, fill=GRID_LABEL_COLOR)
        col_idx += 1
        wx += GRID_SPACING

    row_idx = 1
    wy = end_y
    while wy >= start_y:
        _, py = world_to_pixel(0, wy)
        if 60 < py < IMG_SIZE - 60:
            draw.line([(0, py), (IMG_SIZE, py)], fill=GRID_COLOR, width=1)
            draw.text((16, py - 12), f"{row_idx:02d}",
                      font=font_grid, fill=GRID_LABEL_COLOR)
        row_idx += 1
        wy -= GRID_SPACING

# =============================================================================
# LABEL PLACER -- v5: collision detection for clean label placement
# =============================================================================
class LabelPlacer:
    def __init__(self):
        self.placed = []

    def try_place(self, x, y, w, h, max_attempts=8):
        """Try to place a label, shifting if it collides with existing ones."""
        offsets = [
            (0, 0),           # right of icon (default)
            (0, h + 4),       # below
            (0, -(h + 4)),    # above
            (w + 8, 0),       # further right
            (-(w + 8), 0),    # left of icon
            (0, h * 2 + 8),   # well below
            (w + 4, h + 4),   # diagonal down-right
            (-(w + 4), -(h + 4)),  # diagonal up-left
        ]
        for dx, dy in offsets[:max_attempts]:
            nx, ny = x + dx, y + dy
            # Keep within map bounds
            nx = max(4, min(nx, IMG_SIZE - w - 4))
            ny = max(4, min(ny, IMG_SIZE - h - 4))
            box = (nx, ny, nx + w, ny + h)
            if not self._overlaps(box):
                self.placed.append(box)
                return (nx, ny)
        # Fallback: place anyway
        self.placed.append((x, y, x + w, y + h))
        return (x, y)

    def _overlaps(self, box):
        x1, y1, x2, y2 = box
        for ox1, oy1, ox2, oy2 in self.placed:
            if x1 < ox2 and x2 > ox1 and y1 < oy2 and y2 > oy1:
                return True
        return False

# =============================================================================
# TEXT HELPERS -- v5: clean 2-pass shadow
# =============================================================================
def draw_text_shadow(draw, pos, text, font, fill=WHITE, shadow=(0, 0, 0, 160)):
    """Draw text with a single offset shadow for clean readability."""
    x, y = pos
    # Single offset shadow (cleaner than multi-direction blur)
    draw.text((x + 3, y + 3), text, font=font, fill=shadow)
    # Main text
    draw.text((x, y), text, font=font, fill=fill)

# =============================================================================
# COLLECTIBLE GROUPING
# =============================================================================
def group_collectibles_to_locations(collectibles, locations, max_dist=300):
    """Group collectible items to their nearest location marker."""
    groups = {}
    for item in collectibles:
        best_idx = None
        best_dist = max_dist
        for i, loc in enumerate(locations):
            dist = math.sqrt((item['px'] - loc['px'])**2 + (item['py'] - loc['py'])**2)
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        if best_idx is not None:
            if best_idx not in groups:
                groups[best_idx] = []
            groups[best_idx].append(item['category'])
    return groups

# =============================================================================
# DXT1 COMPRESSION (with mipmaps)
# =============================================================================
def _rgb565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

def _unpack565(c):
    return (((c >> 11) & 0x1F) << 3, ((c >> 5) & 0x3F) << 2, (c & 0x1F) << 3)

def _compress_block(pixels):
    rmin = gmin = bmin = 255
    rmax = gmax = bmax = 0
    for r, g, b in pixels:
        rmin, gmin, bmin = min(rmin,r), min(gmin,g), min(bmin,b)
        rmax, gmax, bmax = max(rmax,r), max(gmax,g), max(bmax,b)
    c0 = _rgb565(rmax, gmax, bmax)
    c1 = _rgb565(rmin, gmin, bmin)
    if c0 < c1: c0, c1 = c1, c0
    if c0 == c1: return struct.pack('<HHI', c0, c1, 0)
    r0,g0,b0 = _unpack565(c0)
    r1,g1,b1 = _unpack565(c1)
    pal = [(r0,g0,b0),(r1,g1,b1),
           ((2*r0+r1+1)//3,(2*g0+g1+1)//3,(2*b0+b1+1)//3),
           ((r0+2*r1+1)//3,(g0+2*g1+1)//3,(b0+2*b1+1)//3)]
    idx = 0
    for i,(r,g,b) in enumerate(pixels):
        best = 0; bd = 999999
        for j,(pr,pg,pb) in enumerate(pal):
            d = (r-pr)**2+(g-pg)**2+(b-pb)**2
            if d < bd: bd = d; best = j
        idx |= best << (i*2)
    return struct.pack('<HHI', c0, c1, idx)

def _compress_mip_level(img):
    """Compress a single mip level to DXT1 blocks."""
    w, h = img.size
    px = img.load()
    blocks = bytearray()
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            blk = []
            for py in range(4):
                for ppx in range(4):
                    sx = min(bx + ppx, w - 1)
                    sy = min(by + py, h - 1)
                    p = px[sx, sy]
                    blk.append((p[0], p[1], p[2]))
            blocks.extend(_compress_block(blk))
    return bytes(blocks)

def save_dxt1_dds(path, img):
    w, h = img.size
    mip_count = 1
    mw, mh = w, h
    while mw > 4 and mh > 4:
        mw //= 2; mh //= 2
        mip_count += 1
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x20000 | 0x80000
    hdr = bytearray(128)
    hdr[0:4] = b'DDS '
    struct.pack_into('<I', hdr, 4, 124)
    struct.pack_into('<I', hdr, 8, flags)
    struct.pack_into('<I', hdr, 12, h)
    struct.pack_into('<I', hdr, 16, w)
    struct.pack_into('<I', hdr, 20, max(1,(w+3)//4)*max(1,(h+3)//4)*8)
    struct.pack_into('<I', hdr, 28, mip_count)
    struct.pack_into('<I', hdr, 76, 32)
    struct.pack_into('<I', hdr, 80, 0x4)
    hdr[84:88] = b'DXT1'
    struct.pack_into('<I', hdr, 108, 0x1000 | 0x8 | 0x400000)
    all_data = bytearray()
    current = img.convert('RGB')
    for mip in range(mip_count):
        mw, mh = current.size
        print(f"    DXT1 mip {mip}: {mw}x{mh}", flush=True)
        all_data.extend(_compress_mip_level(current))
        if mip < mip_count - 1:
            nw = max(4, mw // 2)
            nh = max(4, mh // 2)
            current = current.resize((nw, nh), Image.LANCZOS)
    with open(path, 'wb') as f:
        f.write(hdr)
        f.write(all_data)
    print(f"    Saved DXT1 DDS ({mip_count} mipmaps): {os.path.getsize(path)/1024/1024:.1f} MB")

# =============================================================================
# MAIN
# =============================================================================
def main():
    print("=" * 60)
    print("  LoreOut Completionist Map Generator v5")
    print("  Quality Overhaul Edition")
    print("=" * 60)

    # v5: Military-aesthetic fonts at larger sizes
    try:
        # Impact for major locations -- bold, condensed, high-contrast (STALKER feel)
        font_major = ImageFont.truetype(r"C:\Windows\Fonts\impact.ttf", 42)
        # Bahnschrift for regular locations -- clean geometric sans-serif
        font_regular = ImageFont.truetype(r"C:\Windows\Fonts\bahnschrift.ttf", 32)
        # Consolas for grid labels -- monospace technical aesthetic
        font_grid = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 40)
        # Watermark
        font_watermark = ImageFont.truetype(r"C:\Windows\Fonts\bahnschrift.ttf", 18)
    except Exception as e:
        print(f"  Font warning: {e}")
        font_major = ImageFont.load_default()
        font_regular = font_major
        font_grid = font_major
        font_watermark = font_major

    # Pre-render all icon types
    print("\n  Pre-rendering custom icons (v5 larger sizes)...")
    for cat in ICON_GENERATORS:
        sz = ICON_SIZES.get(cat, 14)
        icon = get_icon(cat, sz)
        print(f"    {cat}: {sz}px -> rendered {icon.size[0]}x{icon.size[1]}px")
    for cat in COLLECT_GENERATORS:
        sz = COLLECT_ICON_SIZES.get(cat, COLLECT_ICON_DEFAULT)
        icon = get_collect_icon(cat, sz)
        print(f"    {cat} (collect): {sz}px -> rendered {icon.size[0]}x{icon.size[1]}px")

    # Load base map
    print(f"\n  Loading satellite map...")
    base_img = Image.open(SOURCE_DDS).convert('RGBA')
    print(f"  Size: {base_img.size}")

    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # STEP 1: Threat zones (subtler alpha in v5)
    print("\n  Drawing threat zones (reduced alpha)...")
    draw_threat_zones(overlay)
    draw = ImageDraw.Draw(overlay)

    # STEP 2: Extract markers
    print(f"\n  Parsing ESPs...")
    markers_cart = extract_markers_from_esp(CARTOGRAPHERS_ESP)
    print(f"    Cartographers: {len(markers_cart)}")
    markers_mmo = extract_markers_from_esp(MAP_MARKER_ESP)
    print(f"    Map Marker Overhaul: {len(markers_mmo)}")

    # Merge and deduplicate
    all_markers = markers_mmo.copy()
    for m in markers_cart:
        if not any(math.sqrt((m['px']-e['px'])**2 + (m['py']-e['py'])**2) < 120 for e in all_markers):
            all_markers.append(m)
    print(f"  Total unique: {len(all_markers)}")

    # STEP 3: Load collectibles
    print(f"\n  Loading collectibles...")
    bobbleheads = load_collectibles_csv(os.path.join(CSV_DIR, "bobbleheads.csv"), "bobblehead")
    magazines = load_collectibles_csv(os.path.join(CSV_DIR, "magazines.csv"), "magazine")
    power_armor = load_collectibles_csv(os.path.join(CSV_DIR, "power_armor.csv"), "power_armor")
    fusion_cores = load_collectibles_csv(os.path.join(CSV_DIR, "fusion_cores.csv"), "fusion_core")
    traders = load_collectibles_csv(os.path.join(CSV_DIR, "traders.csv"), "trader")
    all_collectibles = bobbleheads + magazines + power_armor + fusion_cores + traders
    print(f"    Total: {len(all_collectibles)}")

    # Category counts
    cat_counts = {}
    for m in all_markers:
        cat_counts[m['category']] = cat_counts.get(m['category'], 0) + 1
    for cat, count in sorted(cat_counts.items()):
        print(f"    {cat}: {count}")

    # STEP 4: Subtle continuous grid (v5: grey, thin, non-distracting)
    print("\n  Drawing subtle grid...")
    draw_grid(draw, font_grid)

    # Dashed playable area border
    print("  Drawing dashed border...")
    border_inset = 8192.0
    bx1, by1 = world_to_pixel(WORLD_X_MIN + border_inset, WORLD_Y_MAX - border_inset)
    bx2, by2 = world_to_pixel(WORLD_X_MAX - border_inset, WORLD_Y_MIN + border_inset)
    # Keep border dashed (it's useful as a boundary indicator)
    for edge in [((bx1, by1), (bx2, by1)), ((bx2, by1), (bx2, by2)),
                 ((bx2, by2), (bx1, by2)), ((bx1, by2), (bx1, by1))]:
        _draw_dashed_line(draw, edge[0], edge[1], BORDER_COLOR, width=2, dash_len=30, gap_len=15)

    # STEP 5: Group collectibles near locations
    print("  Grouping collectibles to nearest locations...")
    collect_groups = group_collectibles_to_locations(all_collectibles, all_markers)
    print(f"    {len(collect_groups)} locations have nearby collectibles")

    # STEP 6: Draw location icons (v5: larger)
    print("  Drawing location icons (larger v5 sizes)...")
    for m in all_markers:
        cat = m['category']
        icon = get_icon(cat)
        paste_icon(overlay, icon, m['px'], m['py'])
    draw = ImageDraw.Draw(overlay)

    # STEP 7: Draw collectible indicators near locations (v5: larger)
    print("  Drawing collectible indicators...")
    for loc_idx, categories in collect_groups.items():
        loc = all_markers[loc_idx]
        unique_cats = list(set(categories))
        loc_icon_sz = ICON_SIZES.get(loc['category'], 14)
        # Position below the main icon
        start_x = loc['px'] - (len(unique_cats) * 10) // 2
        iy = loc['py'] + loc_icon_sz // 2 + 10  # below the icon
        for ci, cat in enumerate(sorted(unique_cats)):
            cicon = get_collect_icon(cat)
            paste_icon(overlay, cicon, start_x + ci * 20, iy)
    draw = ImageDraw.Draw(overlay)

    # STEP 8: Draw location labels (v5: tighter placement, skip POI/other, bigger fonts)
    print("  Drawing location labels...")
    placer = LabelPlacer()
    priority = {'city': 0, 'vault': 1, 'military': 2, 'settlement': 3,
                'metro': 4, 'police': 5, 'other': 99, 'poi': 99}
    # v5: Skip 'other' and 'poi' labels to reduce clutter
    labeled = [m for m in all_markers if m['category'] not in ('poi', 'other')]
    labeled.sort(key=lambda m: priority.get(m['category'], 50))

    for m in labeled:
        cat = m['category']
        icon_sz = ICON_SIZES.get(cat, 14)

        # v5: Impact for major, Bahnschrift for regular
        font = font_major if cat in ('city', 'vault', 'military') else font_regular
        color = LABEL_COLORS.get(cat, WHITE_DIM)

        text = m['name']
        try:
            bbox = font.getbbox(text)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except:
            tw, th = len(text) * 12, 20

        # v5: Tighter placement -- directly adjacent to icon edge
        label_x = m['px'] + icon_sz // 2 + 4
        label_y = m['py'] - th // 2

        pos = placer.try_place(label_x, label_y, tw + 6, th + 4)
        if pos:
            draw_text_shadow(draw, pos, text, font, fill=color)

    # v5: NO LEGEND (removed -- FallUI Map color system handles marker identification)

    # STEP 9: Subtle watermark
    draw_text_shadow(draw, (IMG_SIZE - 250, IMG_SIZE - 45), "LOREOUT",
                     font_watermark, fill=(160, 160, 160, 50), shadow=(0, 0, 0, 30))

    # STEP 10: Very subtle AA post-process
    print("  Post-processing (subtle blur)...")
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.5))

    # STEP 11: Composite and save
    print("\n  Compositing...")
    result = Image.alpha_composite(base_img, overlay)

    full_png = OUTPUT_DDS.replace('.dds', '.png')
    print(f"  Saving 8K PNG...")
    result.save(full_png, 'PNG')

    print(f"  Saving 2K preview...")
    preview = result.resize((2048, 2048), Image.LANCZOS)
    preview.save(OUTPUT_PNG, 'PNG')

    print(f"  Compressing to DXT1...")
    save_dxt1_dds(OUTPUT_DDS, result.convert('RGB'))

    total = len(all_markers) + len(all_collectibles)
    print("\n" + "=" * 60)
    print("  MAP v5 GENERATED (Quality Overhaul)!")
    print(f"  Total markers: {total}")
    print(f"    Locations:     {len(all_markers)}")
    print(f"    Bobbleheads:   {len(bobbleheads)}")
    print(f"    Magazines:     {len(magazines)}")
    print(f"    Power Armor:   {len(power_armor)}")
    print(f"    Fusion Cores:  {len(fusion_cores)}")
    print(f"    Traders:       {len(traders)}")
    print(f"    Loc w/ items:  {len(collect_groups)}")
    print(f"  Preview: {OUTPUT_PNG}")
    print(f"  DDS: {OUTPUT_DDS}")
    print("=" * 60)


def _draw_dashed_line(draw, start, end, color, width=1, dash_len=20, gap_len=15):
    """Draw a dashed line from start to end."""
    x0, y0 = start
    x1, y1 = end
    dx = x1 - x0
    dy = y1 - y0
    length = math.sqrt(dx*dx + dy*dy)
    if length < 1: return
    ux, uy = dx / length, dy / length
    pos = 0.0
    while pos < length:
        seg_end = min(pos + dash_len, length)
        sx = x0 + ux * pos
        sy = y0 + uy * pos
        ex = x0 + ux * seg_end
        ey = y0 + uy * seg_end
        draw.line([(int(sx), int(sy)), (int(ex), int(ey))], fill=color, width=width)
        pos += dash_len + gap_len


if __name__ == '__main__':
    main()
