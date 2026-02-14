"""
Generate custom military-style SVG marker icons for Fallout 4 HUDMenu.swf
Each marker has two shapes: Discovered (detailed) and Undiscovered (simpler outline)
SVGs must match FFDec's expected format for importShapes
"""

import os
import math

OUTPUT_DIR = r"C:\Modlists\WastelandReborn\Tools\swf_analysis\custom_shapes"

def svg_wrap(path_d, width, height, cx=None, cy=None):
    """Wrap a path in FFDec-compatible SVG."""
    if cx is None:
        cx = width / 2
    if cy is None:
        cy = height / 2
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:ffdec="https://www.free-decompiler.com/flash" xmlns:xlink="http://www.w3.org/1999/xlink" ffdec:objectType="shape" height="{height}px" width="{width}px" xmlns="http://www.w3.org/2000/svg">
  <g transform="matrix(1.0, 0.0, 0.0, 1.0, {cx}, {cy})">
    {path_d}
  </g>
</svg>
'''

def write_svg(shape_id, content):
    path = os.path.join(OUTPUT_DIR, f"{shape_id}.svg")
    with open(path, 'w') as f:
        f.write(content)
    print(f"  Created shape {shape_id}.svg")


def path_tag(d, fill="#ffffff"):
    return f'<path d="{d}" fill="{fill}" fill-rule="evenodd" stroke="none"/>'


# ============================================================
# MARKER SHAPE DEFINITIONS
# Format: (sprite_id, name, discovered_shape_id, undiscovered_shape_id)
# ============================================================

# Helper: Generate star points
def star_points(cx, cy, outer_r, inner_r, points=5, rotation=-90):
    """Generate star polygon points."""
    coords = []
    for i in range(points * 2):
        angle = math.radians(rotation + i * 360 / (points * 2))
        r = outer_r if i % 2 == 0 else inner_r
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        coords.append((round(x, 2), round(y, 2)))
    return coords

def star_path(cx, cy, outer_r, inner_r, points=5):
    pts = star_points(cx, cy, outer_r, inner_r, points)
    d = f"M {pts[0][0]} {pts[0][1]} "
    for p in pts[1:]:
        d += f"L {p[0]} {p[1]} "
    d += f"L {pts[0][0]} {pts[0][1]}"
    return d

def circle_path(cx, cy, r, segments=16):
    """Approximate circle using line segments (Flash-friendly)."""
    pts = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        pts.append((round(x, 2), round(y, 2)))
    d = f"M {pts[0][0]} {pts[0][1]} "
    for p in pts[1:]:
        d += f"L {p[0]} {p[1]} "
    d += "Z"
    return d

def rect_path(x, y, w, h):
    """Rectangle path."""
    return f"M {x} {y} L {x+w} {y} L {x+w} {y+h} L {x} {y+h} Z"

def diamond_path(cx, cy, rx, ry):
    """Diamond/rhombus."""
    return f"M {cx} {cy-ry} L {cx+rx} {cy} L {cx} {cy+ry} L {cx-rx} {cy} Z"

def hexagon_path(cx, cy, r):
    """Regular hexagon."""
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 90)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        pts.append((round(x, 2), round(y, 2)))
    d = f"M {pts[0][0]} {pts[0][1]} "
    for p in pts[1:]:
        d += f"L {p[0]} {p[1]} "
    d += "Z"
    return d

def triangle_up(cx, cy, size):
    h = size * math.sqrt(3) / 2
    return f"M {cx} {cy - h*0.66} L {cx + size/2} {cy + h*0.34} L {cx - size/2} {cy + h*0.34} Z"

def triangle_down(cx, cy, size):
    h = size * math.sqrt(3) / 2
    return f"M {cx} {cy + h*0.66} L {cx + size/2} {cy - h*0.34} L {cx - size/2} {cy - h*0.34} Z"


# ============================================================
# CATEGORY: SETTLEMENTS (Green on map overlay) - House/flag icons
# ============================================================

def make_settlement_markers():
    """SettlementMarker (43): Discovered=41, Undiscovered=42
    Military flag on pole - settlement claimed/unclaimed"""
    # Discovered: flag with pole, fully rendered
    d = (
        # Flagpole
        "M -1 -9 L 1 -9 L 1 9 L -1 9 Z "
        # Flag (waving pennant shape)
        "M 1 -9 L 8 -7 L 7 -4 L 8 -1 L 1 -3 Z "
        # Base platform
        "M -5 7 L 5 7 L 5 9 L -5 9 Z"
    )
    write_svg(41, svg_wrap(path_tag(d), 18.0, 20.0, 9.0, 10.0))

    # Undiscovered: simple flag outline
    d = (
        "M -0.5 -9 L 0.5 -9 L 0.5 9 L -0.5 9 Z "
        "M 0.5 -9 L 7 -7 L 6 -4 L 7 -1 L 0.5 -3 Z "
        "M -4 7.5 L 4 7.5 L 4 9 L -4 9 Z"
    )
    write_svg(42, svg_wrap(path_tag(d), 18.0, 20.0, 9.0, 10.0))


def make_town_markers():
    """TownMarker (21): Discovered=19, Undiscovered=20
    Building cluster silhouette"""
    # Discovered: multi-building skyline
    d = (
        # Tall building left
        "M -8 -2 L -4 -2 L -4 8 L -8 8 Z "
        # Short building center
        "M -3 2 L 2 2 L 2 8 L -3 8 Z "
        # Tall building right
        "M 3 -5 L 7 -5 L 7 8 L 3 8 Z "
        # Antenna on right building
        "M 4.5 -8 L 5.5 -8 L 5.5 -5 L 4.5 -5 Z "
        # Window left building
        "M -7 -0.5 L -5.5 -0.5 L -5.5 1 L -7 1 Z "
        "M -7 2.5 L -5.5 2.5 L -5.5 4 L -7 4 Z "
        # Window right building
        "M 4 -3.5 L 6 -3.5 L 6 -2 L 4 -2 Z "
        "M 4 -0.5 L 6 -0.5 L 6 1 L 4 1 Z "
        # Ground line
        "M -9 8 L 8 8 L 8 9 L -9 9 Z"
    )
    write_svg(19, svg_wrap(path_tag(d), 19.0, 19.0, 9.5, 9.5))

    # Undiscovered: simpler silhouette
    d = (
        "M -7 0 L -3 0 L -3 8 L -7 8 Z "
        "M -2 3 L 2 3 L 2 8 L -2 8 Z "
        "M 3 -3 L 7 -3 L 7 8 L 3 8 Z "
        "M 4.5 -6 L 5.5 -6 L 5.5 -3 L 4.5 -3 Z "
        "M -8 8 L 8 8 L 8 9 L -8 9 Z"
    )
    write_svg(20, svg_wrap(path_tag(d), 18.0, 18.0, 9.0, 9.0))


def make_city_markers():
    """CityMarker (225): Discovered=223, Undiscovered=224
    Dense urban skyline - larger than town"""
    # Discovered: detailed cityscape
    d = (
        # Skyscraper left
        "M -8 -6 L -5 -6 L -5 8 L -8 8 Z "
        # Mid building
        "M -4 -2 L -1 -2 L -1 8 L -4 8 Z "
        # Tall center tower
        "M 0 -8 L 3 -8 L 3 8 L 0 8 Z "
        # Short right
        "M 4 0 L 8 0 L 8 8 L 4 8 Z "
        # Antenna
        "M 1 -9.5 L 2 -9.5 L 2 -8 L 1 -8 Z "
        # Windows on center tower
        "M 0.5 -6 L 2.5 -6 L 2.5 -5 L 0.5 -5 Z "
        "M 0.5 -3.5 L 2.5 -3.5 L 2.5 -2.5 L 0.5 -2.5 Z "
        "M 0.5 -1 L 2.5 -1 L 2.5 0 L 0.5 0 Z "
        # Ground
        "M -9 8 L 9 8 L 9 9.5 L -9 9.5 Z"
    )
    write_svg(223, svg_wrap(path_tag(d), 20.0, 21.0, 10.0, 10.5))

    # Undiscovered
    d = (
        "M -7 -4 L -4 -4 L -4 8 L -7 8 Z "
        "M -3 0 L 0 0 L 0 8 L -3 8 Z "
        "M 1 -7 L 4 -7 L 4 8 L 1 8 Z "
        "M 5 1 L 7 1 L 7 8 L 5 8 Z "
        "M 2 -8.5 L 3 -8.5 L 3 -7 L 2 -7 Z "
        "M -8 8 L 8 8 L 8 9 L -8 9 Z"
    )
    write_svg(224, svg_wrap(path_tag(d), 18.0, 20.0, 9.0, 10.0))


# ============================================================
# CATEGORY: MILITARY (Red on map overlay) - NATO-style tactical markers
# ============================================================

# VaultMarker (4, 5) and MilitaryBaseMarker (106, 107) already done in previous session


def make_airfield_markers():
    """AirfieldMarker (255): Discovered=253, Undiscovered=254
    Airplane/runway silhouette"""
    # Discovered: military aircraft silhouette (top-down)
    d = (
        # Fuselage
        "M 0 -9 L 1.5 -7 L 1.5 2 L 0.75 8 L -0.75 8 L -1.5 2 L -1.5 -7 Z "
        # Wings
        "M -8 -1 L -1.5 -3 L -1.5 1 L -8 2 Z "
        "M 8 -1 L 1.5 -3 L 1.5 1 L 8 2 Z "
        # Tail fins
        "M -3.5 6 L -1 5 L -0.75 7.5 L -3.5 8 Z "
        "M 3.5 6 L 1 5 L 0.75 7.5 L 3.5 8 Z"
    )
    write_svg(253, svg_wrap(path_tag(d), 18.0, 19.0, 9.0, 9.5))

    # Undiscovered
    d = (
        "M 0 -8 L 1 -6 L 1 2 L 0.5 7 L -0.5 7 L -1 2 L -1 -6 Z "
        "M -7 -0.5 L -1 -2.5 L -1 0.5 L -7 1.5 Z "
        "M 7 -0.5 L 1 -2.5 L 1 0.5 L 7 1.5 Z "
        "M -3 5.5 L -0.5 4.5 L -0.5 7 L -3 7 Z "
        "M 3 5.5 L 0.5 4.5 L 0.5 7 L 3 7 Z"
    )
    write_svg(254, svg_wrap(path_tag(d), 16.0, 17.0, 8.0, 8.5))


def make_sentinel_markers():
    """SentinelMarker (46): Discovered=44, Undiscovered=45
    Watchtower/guard post"""
    # Discovered: watchtower
    d = (
        # Tower body
        "M -3 -2 L 3 -2 L 2 8 L -2 8 Z "
        # Platform/lookout top
        "M -5 -4 L 5 -4 L 5 -2 L -5 -2 Z "
        # Roof
        "M -4 -4 L 0 -8 L 4 -4 Z "
        # Window
        "M -1.5 -3.5 L 1.5 -3.5 L 1.5 -2.5 L -1.5 -2.5 Z "
        # Base
        "M -4 7 L 4 7 L 4 9 L -4 9 Z"
    )
    write_svg(44, svg_wrap(path_tag(d), 12.0, 19.0, 6.0, 9.5))

    d = (
        "M -2.5 -1 L 2.5 -1 L 1.5 8 L -1.5 8 Z "
        "M -4 -3 L 4 -3 L 4 -1 L -4 -1 Z "
        "M -3 -3 L 0 -7 L 3 -3 Z "
        "M -3.5 7 L 3.5 7 L 3.5 8.5 L -3.5 8.5 Z"
    )
    write_svg(45, svg_wrap(path_tag(d), 10.0, 17.0, 5.0, 8.5))


def make_bunker_markers():
    """BunkerMarker (243): Discovered=241, Undiscovered=242
    Reinforced bunker/underground entrance"""
    # Discovered: bunker with blast door
    d = (
        # Dome/arch top
        "M -8 3 L -8 -1 L -6 -4 L -3 -6 L 0 -7 L 3 -6 L 6 -4 L 8 -1 L 8 3 Z "
        # Door frame
        "M -3 3 L -3 -2 L 3 -2 L 3 3 Z "
        # Door center line
        "M -0.5 3 L -0.5 -2 L 0.5 -2 L 0.5 3 Z "
        # Reinforcement lines
        "M -7 0 L 7 0 L 7 1 L -7 1 Z "
        # Ground
        "M -9 3 L 9 3 L 9 4 L -9 4 Z"
    )
    write_svg(241, svg_wrap(path_tag(d), 20.0, 13.0, 10.0, 8.0))

    d = (
        "M -7 3 L -7 0 L -5 -3 L -2.5 -5 L 0 -6 L 2.5 -5 L 5 -3 L 7 0 L 7 3 Z "
        "M -2.5 3 L -2.5 -1 L 2.5 -1 L 2.5 3 Z "
        "M -8 3 L 8 3 L 8 4 L -8 4 Z"
    )
    write_svg(242, svg_wrap(path_tag(d), 18.0, 12.0, 9.0, 7.0))


# ============================================================
# CATEGORY: METRO/UNDERGROUND (Cyan on map overlay) - "M" in circle
# ============================================================

def make_metro_markers():
    """MetroMarker (111): Discovered=109, Undiscovered=110
    Underground metro symbol - tunnel entrance"""
    # Discovered: tunnel/arch with rails
    d = (
        # Tunnel arch
        "M -8 5 L -8 -1 L -6 -4 L -3 -6.5 L 0 -7.5 L 3 -6.5 L 6 -4 L 8 -1 L 8 5 "
        "L 6 5 L 6 -0.5 L 4.5 -3 L 2.5 -5 L 0 -5.8 L -2.5 -5 L -4.5 -3 L -6 -0.5 L -6 5 Z "
        # Rails
        "M -5 3 L 5 3 L 5 4 L -5 4 Z "
        "M -5 5 L 5 5 L 5 6 L -5 6 Z "
        # Rail ties
        "M -3 3 L -2 3 L -2 6 L -3 6 Z "
        "M 0 3 L 1 3 L 1 6 L 0 6 Z "
        "M 3 3 L 4 3 L 4 6 L 3 6 Z "
        # Ground
        "M -9 6 L 9 6 L 9 7 L -9 7 Z"
    )
    write_svg(109, svg_wrap(path_tag(d), 20.0, 16.0, 10.0, 8.5))

    d = (
        "M -7 5 L -7 0 L -5 -3 L -2.5 -5.5 L 0 -6 L 2.5 -5.5 L 5 -3 L 7 0 L 7 5 "
        "L 5.5 5 L 5.5 0.5 L 4 -2 L 2 -4 L 0 -4.5 L -2 -4 L -4 -2 L -5.5 0.5 L -5.5 5 Z "
        "M -6 5 L 6 5 L 6 6 L -6 6 Z "
        "M -8 6.5 L 8 6.5 L 8 7.5 L -8 7.5 Z"
    )
    write_svg(110, svg_wrap(path_tag(d), 18.0, 16.0, 9.0, 8.0))


def make_sewer_markers():
    """SewerMarker (40): Discovered=38, Undiscovered=39
    Manhole cover / grate"""
    # Discovered: circular grate with cross pattern
    # Outer ring
    c1 = circle_path(0, 0, 8, 20)
    # Inner hole (cut out by evenodd)
    c2 = circle_path(0, 0, 5.5, 16)
    d = (
        c1 + " " + c2 + " "
        # Cross bars through center
        "M -8 -1 L 8 -1 L 8 1 L -8 1 Z "
        "M -1 -8 L 1 -8 L 1 8 L -1 8 Z"
    )
    write_svg(38, svg_wrap(path_tag(d), 18.0, 18.0, 9.0, 9.0))

    c1 = circle_path(0, 0, 7, 16)
    c2 = circle_path(0, 0, 5, 14)
    d = (
        c1 + " " + c2 + " "
        "M -7 -0.75 L 7 -0.75 L 7 0.75 L -7 0.75 Z "
        "M -0.75 -7 L 0.75 -7 L 0.75 7 L -0.75 7 Z"
    )
    write_svg(39, svg_wrap(path_tag(d), 16.0, 16.0, 8.0, 8.0))


# ============================================================
# CATEGORY: POLICE (Light Blue) - Shield/badge
# ============================================================

def make_police_markers():
    """PoliceStationMarker (90): Discovered=88, Undiscovered=89
    Police shield/badge"""
    # Discovered: shield with star
    # Star in center
    s1 = star_path(0, -0.5, 3.5, 1.4, 5)
    d = (
        # Shield outline
        "M 0 -8 L 7 -5 L 7 1 L 4 5 L 0 8 L -4 5 L -7 1 L -7 -5 Z "
        # Inner shield (evenodd cutout)
        "M 0 -6 L 5.5 -3.5 L 5.5 0.5 L 3 4 L 0 6.5 L -3 4 L -5.5 0.5 L -5.5 -3.5 Z "
        + s1
    )
    write_svg(88, svg_wrap(path_tag(d), 16.0, 18.0, 8.0, 9.0))

    s1 = star_path(0, -0.5, 3, 1.2, 5)
    d = (
        "M 0 -7 L 6 -4 L 6 1 L 3.5 4.5 L 0 7 L -3.5 4.5 L -6 1 L -6 -4 Z "
        "M 0 -5.5 L 4.5 -3 L 4.5 0.5 L 2.5 3.5 L 0 5.5 L -2.5 3.5 L -4.5 0.5 L -4.5 -3 Z "
        + s1
    )
    write_svg(89, svg_wrap(path_tag(d), 14.0, 16.0, 7.0, 8.0))


# ============================================================
# CATEGORY: RADIO TOWER - Antenna/broadcast
# ============================================================

def make_radio_tower_markers():
    """RadioTowerMarker (70): Discovered=68, Undiscovered=69
    Radio antenna with broadcast waves"""
    # Discovered: tower with signal waves
    d = (
        # Tower structure (lattice)
        "M -0.75 -9 L 0.75 -9 L 3 8 L 1 8 L 0.75 6 L -0.75 6 L -1 8 L -3 8 Z "
        # Cross braces
        "M -1.5 -3 L 1.5 -3 L 1.5 -2 L -1.5 -2 Z "
        "M -2 2 L 2 2 L 2 3 L -2 3 Z "
        # Signal waves left
        "M -4 -7 L -5 -8 L -6.5 -6 L -5 -4 L -4 -5 L -5 -6 Z "
        "M -6 -8.5 L -7 -9 L -9 -6 L -7 -3 L -6 -4 L -7.5 -6 Z "
        # Signal waves right
        "M 4 -7 L 5 -8 L 6.5 -6 L 5 -4 L 4 -5 L 5 -6 Z "
        "M 6 -8.5 L 7 -9 L 9 -6 L 7 -3 L 6 -4 L 7.5 -6 Z "
        # Base
        "M -4 7 L 4 7 L 4 9 L -4 9 Z"
    )
    write_svg(68, svg_wrap(path_tag(d), 20.0, 20.0, 10.0, 10.0))

    d = (
        "M -0.5 -8 L 0.5 -8 L 2.5 7 L 0.5 7 L 0.5 5 L -0.5 5 L -0.5 7 L -2.5 7 Z "
        "M -1 -2 L 1 -2 L 1 -1 L -1 -1 Z "
        "M -1.5 3 L 1.5 3 L 1.5 4 L -1.5 4 Z "
        "M -3.5 7.5 L 3.5 7.5 L 3.5 8.5 L -3.5 8.5 Z"
    )
    write_svg(69, svg_wrap(path_tag(d), 9.0, 18.0, 4.5, 9.0))


# ============================================================
# CATEGORY: WATER/MARINE (Cyan) - Anchor/wave symbols
# ============================================================

def make_pier_markers():
    """PierMarker (93): Discovered=91, Undiscovered=92
    Anchor symbol"""
    # Discovered: anchor
    # Ring at top
    c1 = circle_path(0, -6.5, 2.5, 12)
    c2 = circle_path(0, -6.5, 1.2, 10)
    d = (
        c1 + " " + c2 + " "
        # Vertical shaft
        "M -1 -4 L 1 -4 L 1 5 L -1 5 Z "
        # Cross bar
        "M -5 -2 L 5 -2 L 5 -0.5 L -5 -0.5 Z "
        # Curved flukes (simplified)
        "M -6 7 L -5 5 L -1 5 L -1 7 L -3 8 Z "
        "M 6 7 L 5 5 L 1 5 L 1 7 L 3 8 Z"
    )
    write_svg(91, svg_wrap(path_tag(d), 14.0, 19.0, 7.0, 9.5))

    c1 = circle_path(0, -6, 2, 10)
    c2 = circle_path(0, -6, 1, 8)
    d = (
        c1 + " " + c2 + " "
        "M -0.75 -4 L 0.75 -4 L 0.75 5 L -0.75 5 Z "
        "M -4 -2 L 4 -2 L 4 -0.75 L -4 -0.75 Z "
        "M -5 6 L -4 4.5 L -0.75 4.5 L -0.75 6 L -2.5 7 Z "
        "M 5 6 L 4 4.5 L 0.75 4.5 L 0.75 6 L 2.5 7 Z"
    )
    write_svg(92, svg_wrap(path_tag(d), 12.0, 17.0, 6.0, 8.5))


def make_submarine_markers():
    """SubmarineMarker (34): Discovered=32, Undiscovered=33"""
    # Submarine silhouette
    d = (
        # Hull
        "M -8 -1 L -6 -3 L 6 -3 L 8 -1 L 8 2 L 6 4 L -6 4 L -8 2 Z "
        # Conning tower
        "M -1 -6 L 2 -6 L 3 -3 L -2 -3 Z "
        # Periscope
        "M 0 -8 L 1 -8 L 1 -6 L 0 -6 Z "
        # Propeller
        "M 8 -2 L 9.5 -3 L 9.5 -1.5 Z "
        "M 8 3 L 9.5 4 L 9.5 2.5 Z"
    )
    write_svg(32, svg_wrap(path_tag(d), 21.0, 14.0, 10.5, 9.0))

    d = (
        "M -7 -0.5 L -5 -2.5 L 5 -2.5 L 7 -0.5 L 7 1.5 L 5 3.5 L -5 3.5 L -7 1.5 Z "
        "M -0.5 -5 L 1.5 -5 L 2 -2.5 L -1 -2.5 Z "
        "M 0 -6.5 L 0.75 -6.5 L 0.75 -5 L 0 -5 Z"
    )
    write_svg(33, svg_wrap(path_tag(d), 16.0, 12.0, 8.0, 7.5))


def make_shipwreck_markers():
    """ShipwreckMarker (37): Discovered=35, Undiscovered=36"""
    # Broken ship hull
    d = (
        # Hull bottom
        "M -8 2 L -6 5 L 6 5 L 8 2 Z "
        # Broken mast left
        "M -3 -7 L -2 -7 L -1 2 L -3 2 Z "
        # Broken mast right (tilted)
        "M 2 -4 L 3 -5 L 5 0 L 3 1 Z "
        # Wave lines
        "M -9 6 L -6 5 L -3 6.5 L 0 5.5 L 3 6.5 L 6 5 L 9 6 L 9 7 L -9 7 Z"
    )
    write_svg(35, svg_wrap(path_tag(d), 20.0, 16.0, 10.0, 8.0))

    d = (
        "M -7 2 L -5 4.5 L 5 4.5 L 7 2 Z "
        "M -2 -5 L -1 -5 L 0 2 L -2 2 Z "
        "M 2 -3 L 3 -4 L 4 0 L 2.5 0.5 Z "
        "M -8 5 L -5 4 L -2 5.5 L 1 4.5 L 4 5.5 L 7 4 L 8 5 L 8 6 L -8 6 Z"
    )
    write_svg(36, svg_wrap(path_tag(d), 18.0, 14.0, 9.0, 7.0))


# ============================================================
# CATEGORY: INDUSTRIAL (Purple) - Gear/factory
# ============================================================

def make_factory_markers():
    """FactoryMarker (197): Discovered=133, Undiscovered=134
    NOTE: Factory shares shapes 133/134 with IndustrialStacksMarker!
    Factory smokestacks"""
    # Discovered: factory with smokestacks
    d = (
        # Building base
        "M -8 0 L 8 0 L 8 8 L -8 8 Z "
        # Smokestack 1
        "M -7 -7 L -5 -7 L -5 0 L -7 0 Z "
        # Smokestack 2
        "M -2 -5 L 0 -5 L 0 0 L -2 0 Z "
        # Smoke puff 1
        "M -7.5 -8.5 L -4.5 -8.5 L -4.5 -7.5 L -7.5 -7.5 Z "
        # Saw-tooth roof right
        "M 2 -3 L 5 0 L 2 0 Z "
        "M 5 -3 L 8 0 L 5 0 Z "
        # Windows
        "M -6.5 2 L -3.5 2 L -3.5 4 L -6.5 4 Z "
        "M 3 2 L 7 2 L 7 4 L 3 4 Z "
        # Door
        "M -1.5 4 L 1.5 4 L 1.5 8 L -1.5 8 Z "
        # Ground
        "M -9 8 L 9 8 L 9 9 L -9 9 Z"
    )
    write_svg(133, svg_wrap(path_tag(d), 20.0, 20.0, 10.0, 10.0))

    d = (
        "M -7 1 L 7 1 L 7 7 L -7 7 Z "
        "M -6 -5 L -4 -5 L -4 1 L -6 1 Z "
        "M -1 -3 L 1 -3 L 1 1 L -1 1 Z "
        "M 3 -2 L 5 0 L 7 0 L 7 1 L 3 1 Z "
        "M -8 7 L 8 7 L 8 8 L -8 8 Z"
    )
    write_svg(134, svg_wrap(path_tag(d), 18.0, 15.0, 9.0, 8.5))


def make_industrial_dome_markers():
    """IndustrialDomeMarker (138): Discovered=136, Undiscovered=137"""
    # Dome with industrial features
    d = (
        # Dome shape
        "M -8 4 L -8 0 L -6 -3 L -3 -5.5 L 0 -6.5 L 3 -5.5 L 6 -3 L 8 0 L 8 4 Z "
        # Inner dome cutout (evenodd)
        "M -6 4 L -6 0.5 L -4.5 -2 L -2 -4 L 0 -4.8 L 2 -4 L 4.5 -2 L 6 0.5 L 6 4 Z "
        # Pipe on top
        "M -1 -8 L 1 -8 L 1 -6.5 L -1 -6.5 Z "
        # Ground
        "M -9 4 L 9 4 L 9 5 L -9 5 Z"
    )
    write_svg(136, svg_wrap(path_tag(d), 20.0, 15.0, 10.0, 9.0))

    d = (
        "M -7 4 L -7 0 L -5 -2.5 L -2.5 -4.5 L 0 -5.5 L 2.5 -4.5 L 5 -2.5 L 7 0 L 7 4 Z "
        "M -5.5 4 L -5.5 0.5 L -4 -1.5 L -2 -3 L 0 -3.8 L 2 -3 L 4 -1.5 L 5.5 0.5 L 5.5 4 Z "
        "M -8 4 L 8 4 L 8 5 L -8 5 Z"
    )
    write_svg(137, svg_wrap(path_tag(d), 18.0, 13.0, 9.0, 7.0))


# ============================================================
# CATEGORY: POWER ARMOR (Orange) - Power suit helmet
# ============================================================

def make_power_armor_markers():
    """PowerArmorLocMarker (81): LevelWithPlayer=80, BelowPlayer=24
    Power armor helmet shape"""
    # Shape 80: the main PA icon (level with player)
    d = (
        # Helmet outline
        "M -5 -7 L 5 -7 L 7 -4 L 7 2 L 5 5 L 3 5 L 2 3 L -2 3 L -3 5 L -5 5 L -7 2 L -7 -4 Z "
        # Visor slit
        "M -4 -3 L 4 -3 L 4 -1 L -4 -1 Z "
        # Breather vents
        "M -3 1 L -1 1 L -1 2.5 L -3 2.5 Z "
        "M 1 1 L 3 1 L 3 2.5 L 1 2.5 Z"
    )
    write_svg(80, svg_wrap(path_tag(d), 16.0, 14.0, 8.0, 8.0))
    # Note: shape 24 is shared "BelowPlayer" arrow, don't touch


# ============================================================
# CATEGORY: QUEST/SPECIAL markers
# ============================================================

def make_diamond_city_markers():
    """DiamondCityMarker (213): Discovered=211, Undiscovered=212
    Diamond shape"""
    # Discovered: diamond with inner detail
    d1 = diamond_path(0, 0, 8, 9)
    d2 = diamond_path(0, 0, 5.5, 6.5)
    d = (
        d1 + " " + d2 + " "
        # Inner cross
        "M -2 -0.5 L 2 -0.5 L 2 0.5 L -2 0.5 Z "
        "M -0.5 -2 L 0.5 -2 L 0.5 2 L -0.5 2 Z"
    )
    write_svg(211, svg_wrap(path_tag(d), 18.0, 20.0, 9.0, 10.0))

    d1 = diamond_path(0, 0, 7, 8)
    d2 = diamond_path(0, 0, 5, 6)
    d = d1 + " " + d2
    write_svg(212, svg_wrap(path_tag(d), 16.0, 18.0, 8.0, 9.0))


def make_goodneighbor_markers():
    """GoodneighborMarker (184): Discovered=182, Undiscovered=183
    Neon sign / star in circle"""
    c1 = circle_path(0, 0, 8.5, 20)
    c2 = circle_path(0, 0, 6.5, 16)
    s1 = star_path(0, 0, 5, 2, 5)
    d = c1 + " " + c2 + " " + s1
    write_svg(182, svg_wrap(path_tag(d), 19.0, 19.0, 9.5, 9.5))

    c1 = circle_path(0, 0, 7.5, 18)
    c2 = circle_path(0, 0, 5.5, 14)
    s1 = star_path(0, 0, 4, 1.6, 5)
    d = c1 + " " + c2 + " " + s1
    write_svg(183, svg_wrap(path_tag(d), 17.0, 17.0, 8.5, 8.5))


# ============================================================
# CATEGORY: CHURCH/SCHOOL/OFFICE/HOSPITAL (OrangeDark)
# ============================================================

def make_church_markers():
    """ChurchMarker (228): Discovered=226, Undiscovered=227
    Cross on building"""
    d = (
        # Building
        "M -6 -1 L 6 -1 L 6 8 L -6 8 Z "
        # Steeple
        "M -2 -1 L 0 -6 L 2 -1 Z "
        # Cross on top
        "M -0.75 -9 L 0.75 -9 L 0.75 -7 L 2 -7 L 2 -5.5 L 0.75 -5.5 L 0.75 -4 L -0.75 -4 L -0.75 -5.5 L -2 -5.5 L -2 -7 L -0.75 -7 Z "
        # Door
        "M -1.5 4 L 1.5 4 L 1.5 8 L -1.5 8 Z "
        # Windows
        "M -5 1 L -3 1 L -3 3.5 L -5 3.5 Z "
        "M 3 1 L 5 1 L 5 3.5 L 3 3.5 Z "
        # Ground
        "M -7 8 L 7 8 L 7 9 L -7 9 Z"
    )
    write_svg(226, svg_wrap(path_tag(d), 16.0, 20.0, 8.0, 10.0))

    d = (
        "M -5 0 L 5 0 L 5 7 L -5 7 Z "
        "M -1.5 0 L 0 -4 L 1.5 0 Z "
        "M -0.5 -7 L 0.5 -7 L 0.5 -5.5 L 1.5 -5.5 L 1.5 -4.5 L 0.5 -4.5 L 0.5 -3 L -0.5 -3 L -0.5 -4.5 L -1.5 -4.5 L -1.5 -5.5 L -0.5 -5.5 Z "
        "M -6 7 L 6 7 L 6 8 L -6 8 Z"
    )
    write_svg(227, svg_wrap(path_tag(d), 14.0, 18.0, 7.0, 9.0))


def make_hospital_markers():
    """HospitalMarker (178): Discovered=176, Undiscovered=177
    Medical cross"""
    d = (
        # Building
        "M -7 -2 L 7 -2 L 7 8 L -7 8 Z "
        # Medical cross
        "M -2 -8 L 2 -8 L 2 -2 L -2 -2 Z "
        "M -5 -6 L 5 -6 L 5 -4 L -5 -4 Z "
        # Door
        "M -1.5 4 L 1.5 4 L 1.5 8 L -1.5 8 Z "
        # Windows
        "M -6 0 L -3.5 0 L -3.5 2.5 L -6 2.5 Z "
        "M 3.5 0 L 6 0 L 6 2.5 L 3.5 2.5 Z "
        # Ground
        "M -8 8 L 8 8 L 8 9 L -8 9 Z"
    )
    write_svg(176, svg_wrap(path_tag(d), 18.0, 19.0, 9.0, 9.5))

    d = (
        "M -6 -1 L 6 -1 L 6 7 L -6 7 Z "
        "M -1.5 -6 L 1.5 -6 L 1.5 -1 L -1.5 -1 Z "
        "M -4 -4.5 L 4 -4.5 L 4 -2.5 L -4 -2.5 Z "
        "M -7 7 L 7 7 L 7 8 L -7 8 Z"
    )
    write_svg(177, svg_wrap(path_tag(d), 16.0, 16.0, 8.0, 8.0))


def make_school_markers():
    """SchoolMarker (49): Discovered=47, Undiscovered=48"""
    # Book/graduation cap
    d = (
        # Open book shape
        "M 0 -3 L 8 -6 L 8 4 L 0 7 Z "
        "M 0 -3 L -8 -6 L -8 4 L 0 7 Z "
        # Spine
        "M -0.75 -3 L 0.75 -3 L 0.75 7 L -0.75 7 Z "
        # Pencil on top
        "M -1 -8 L 1 -8 L 1 -3 L -1 -3 Z "
        "M -1.5 -8 L 1.5 -8 L 1.5 -7 L -1.5 -7 Z "
        "M 0 -9.5 L 0.75 -8 L -0.75 -8 Z"
    )
    write_svg(47, svg_wrap(path_tag(d), 18.0, 19.0, 9.0, 10.0))

    d = (
        "M 0 -2 L 7 -5 L 7 3.5 L 0 6 Z "
        "M 0 -2 L -7 -5 L -7 3.5 L 0 6 Z "
        "M -0.5 -2 L 0.5 -2 L 0.5 6 L -0.5 6 Z"
    )
    write_svg(48, svg_wrap(path_tag(d), 16.0, 13.0, 8.0, 6.5))


def make_office_markers():
    """OfficeMarker (96): Discovered=94, Undiscovered=95"""
    # Tall office building
    d = (
        "M -5 -8 L 5 -8 L 5 8 L -5 8 Z "
        # Windows grid
        "M -3.5 -6 L -1.5 -6 L -1.5 -4.5 L -3.5 -4.5 Z "
        "M 1.5 -6 L 3.5 -6 L 3.5 -4.5 L 1.5 -4.5 Z "
        "M -3.5 -3 L -1.5 -3 L -1.5 -1.5 L -3.5 -1.5 Z "
        "M 1.5 -3 L 3.5 -3 L 3.5 -1.5 L 1.5 -1.5 Z "
        "M -3.5 0 L -1.5 0 L -1.5 1.5 L -3.5 1.5 Z "
        "M 1.5 0 L 3.5 0 L 3.5 1.5 L 1.5 1.5 Z "
        "M -3.5 3 L -1.5 3 L -1.5 4.5 L -3.5 4.5 Z "
        "M 1.5 3 L 3.5 3 L 3.5 4.5 L 1.5 4.5 Z "
        # Door
        "M -1.5 5.5 L 1.5 5.5 L 1.5 8 L -1.5 8 Z "
        # Ground
        "M -6 8 L 6 8 L 6 9 L -6 9 Z"
    )
    write_svg(94, svg_wrap(path_tag(d), 14.0, 19.0, 7.0, 9.5))

    d = (
        "M -4 -7 L 4 -7 L 4 7 L -4 7 Z "
        "M -2.5 -5 L -1 -5 L -1 -3.5 L -2.5 -3.5 Z "
        "M 1 -5 L 2.5 -5 L 2.5 -3.5 L 1 -3.5 Z "
        "M -2.5 -2 L -1 -2 L -1 -0.5 L -2.5 -0.5 Z "
        "M 1 -2 L 2.5 -2 L 2.5 -0.5 L 1 -0.5 Z "
        "M -5 7 L 5 7 L 5 8 L -5 8 Z"
    )
    write_svg(95, svg_wrap(path_tag(d), 12.0, 17.0, 6.0, 8.5))


# ============================================================
# CATEGORY: OUTDOOR/WILDERNESS (Yellow)
# ============================================================

def make_cave_markers():
    """CaveMarker (231): Discovered=229, Undiscovered=230"""
    # Cave entrance
    d = (
        # Rocky arch
        "M -9 5 L -7 -1 L -5 -4 L -2 -6 L 0 -7 L 2 -6 L 5 -4 L 7 -1 L 9 5 "
        "L 6 5 L 5 1 L 3 -2 L 0 -3.5 L -3 -2 L -5 1 L -6 5 Z "
        # Stalactites
        "M -2 -3 L -1.5 -1 L -1 -3 Z "
        "M 1 -3 L 1.5 -0.5 L 2 -3 Z "
        # Ground
        "M -9 5 L 9 5 L 9 6 L -9 6 Z"
    )
    write_svg(229, svg_wrap(path_tag(d), 20.0, 15.0, 10.0, 8.0))

    d = (
        "M -8 5 L -6 0 L -4 -3 L -1.5 -5 L 0 -5.5 L 1.5 -5 L 4 -3 L 6 0 L 8 5 "
        "L 5 5 L 4 1 L 2.5 -1.5 L 0 -2.5 L -2.5 -1.5 L -4 1 L -5 5 Z "
        "M -8 5 L 8 5 L 8 6 L -8 6 Z"
    )
    write_svg(230, svg_wrap(path_tag(d), 18.0, 13.0, 9.0, 7.0))


def make_junkyard_markers():
    """JunkyardMarker (126): Discovered=124, Undiscovered=125"""
    # Pile of junk/wrench
    cog_outer = circle_path(-5, 4, 3, 8)
    cog_inner = circle_path(-5, 4, 1.5, 6)
    d = (
        "M -6 -7 L -3 -7 L -3 -4 L -1 -2 L 5 4 L 7 4 L 8 5 L 8 7 L 6 8 L 4 8 L 3 7 L 3 5 L -3 -1 L -6 -1 Z "
        "M -5 -6 L -4 -6 L -4 -2 L -5 -2 Z "
        + cog_outer + " " + cog_inner
    )
    write_svg(124, svg_wrap(path_tag(d), 18.0, 18.0, 9.0, 9.0))

    cog_outer2 = circle_path(-4.5, 3.5, 2.5, 8)
    cog_inner2 = circle_path(-4.5, 3.5, 1.2, 6)
    d = (
        "M -5 -6 L -2 -6 L -2 -3 L 0 -1 L 5 4 L 6 3.5 L 7 5 L 5 7 L 3 6 L 3.5 5 L -2 -0.5 L -5 -0.5 Z "
        + cog_outer2 + " " + cog_inner2
    )
    write_svg(125, svg_wrap(path_tag(d), 16.0, 16.0, 8.0, 8.0))


def make_graveyard_markers():
    """GraveyardMarker (181): Discovered=179, Undiscovered=180"""
    # Tombstone/cross
    d = (
        # Tombstone shape
        "M -4 -5 L -4 -7 L -2 -9 L 2 -9 L 4 -7 L 4 -5 L 4 7 L -4 7 Z "
        # Cross on tombstone
        "M -1.5 -7 L 1.5 -7 L 1.5 -4 L 3 -4 L 3 -2 L 1.5 -2 L 1.5 2 L -1.5 2 L -1.5 -2 L -3 -2 L -3 -4 L -1.5 -4 Z "
        # Ground mound
        "M -6 6 L -4 4 L 0 3 L 4 4 L 6 6 L 6 8 L -6 8 Z"
    )
    write_svg(179, svg_wrap(path_tag(d), 14.0, 19.0, 7.0, 10.0))

    d = (
        "M -3 -4 L -3 -6 L -1.5 -7.5 L 1.5 -7.5 L 3 -6 L 3 -4 L 3 6 L -3 6 Z "
        "M -1 -6 L 1 -6 L 1 -3 L 2 -3 L 2 -1.5 L 1 -1.5 L 1 1.5 L -1 1.5 L -1 -1.5 L -2 -1.5 L -2 -3 L -1 -3 Z "
        "M -5 5 L 5 5 L 5 7 L -5 7 Z"
    )
    write_svg(180, svg_wrap(path_tag(d), 12.0, 17.0, 6.0, 8.5))


# ============================================================
# CATEGORY: LANDMARKS/OTHER (Grey/Gold/etc)
# ============================================================

def make_landmark_markers():
    """LandmarkMarker (123): Discovered=121, Undiscovered=122
    Generic landmark - pyramid/obelisk"""
    d = (
        # Obelisk
        "M -3 -9 L 3 -9 L 4 8 L -4 8 Z "
        # Horizontal bands
        "M -3.3 -5 L 3.3 -5 L 3.3 -4 L -3.3 -4 Z "
        "M -3.6 -1 L 3.6 -1 L 3.6 0 L -3.6 0 Z "
        "M -3.8 3 L 3.8 3 L 3.8 4 L -3.8 4 Z "
        # Base
        "M -6 7 L 6 7 L 6 9 L -6 9 Z"
    )
    write_svg(121, svg_wrap(path_tag(d), 14.0, 20.0, 7.0, 10.0))

    d = (
        "M -2.5 -8 L 2.5 -8 L 3.5 7 L -3.5 7 Z "
        "M -5 7 L 5 7 L 5 8.5 L -5 8.5 Z"
    )
    write_svg(122, svg_wrap(path_tag(d), 12.0, 18.0, 6.0, 9.5))


def make_monument_markers():
    """MonumentMarker (102): Discovered=100, Undiscovered=101
    Column/pillar"""
    d = (
        # Column
        "M -3 -6 L 3 -6 L 3 6 L -3 6 Z "
        # Capital (top)
        "M -5 -7 L 5 -7 L 5 -6 L -5 -6 Z "
        "M -4 -8 L 4 -8 L 5 -7 L -5 -7 Z "
        # Base
        "M -5 6 L 5 6 L 5 7 L -5 7 Z "
        "M -6 7 L 6 7 L 6 8 L -6 8 Z "
        # Fluting lines
        "M -1 -6 L -0.5 -6 L -0.5 6 L -1 6 Z "
        "M 0.5 -6 L 1 -6 L 1 6 L 0.5 6 Z"
    )
    write_svg(100, svg_wrap(path_tag(d), 14.0, 18.0, 7.0, 9.0))

    d = (
        "M -2.5 -5 L 2.5 -5 L 2.5 5.5 L -2.5 5.5 Z "
        "M -4 -6 L 4 -6 L 4 -5 L -4 -5 Z "
        "M -4 5.5 L 4 5.5 L 4 6.5 L -4 6.5 Z "
        "M -5 6.5 L 5 6.5 L 5 7.5 L -5 7.5 Z"
    )
    write_svg(101, svg_wrap(path_tag(d), 12.0, 16.0, 6.0, 8.0))


def make_skyscraper_markers():
    """SkyscraperMarker (216): Discovered=214, Undiscovered=215"""
    d = (
        "M -4 -9 L 4 -9 L 4 8 L -4 8 Z "
        "M 0 -10 L 1 -10 L 1 -9 L 0 -9 Z "
        # Window grid
        "M -3 -7 L -1 -7 L -1 -5.5 L -3 -5.5 Z "
        "M 1 -7 L 3 -7 L 3 -5.5 L 1 -5.5 Z "
        "M -3 -4 L -1 -4 L -1 -2.5 L -3 -2.5 Z "
        "M 1 -4 L 3 -4 L 3 -2.5 L 1 -2.5 Z "
        "M -3 -1 L -1 -1 L -1 0.5 L -3 0.5 Z "
        "M 1 -1 L 3 -1 L 3 0.5 L 1 0.5 Z "
        "M -3 2 L -1 2 L -1 3.5 L -3 3.5 Z "
        "M 1 2 L 3 2 L 3 3.5 L 1 3.5 Z "
        "M -1 5 L 1 5 L 1 8 L -1 8 Z "
        "M -5 8 L 5 8 L 5 9.5 L -5 9.5 Z"
    )
    write_svg(214, svg_wrap(path_tag(d), 12.0, 21.0, 6.0, 10.5))

    d = (
        "M -3.5 -8 L 3.5 -8 L 3.5 7 L -3.5 7 Z "
        "M -0.5 -9 L 0.5 -9 L 0.5 -8 L -0.5 -8 Z "
        "M -4.5 7 L 4.5 7 L 4.5 8 L -4.5 8 Z"
    )
    write_svg(215, svg_wrap(path_tag(d), 11.0, 19.0, 5.5, 10.0))


# ============================================================
# CATEGORY: MISC MARKERS - all remaining types
# ============================================================

def make_farm_markers():
    """FarmMarker (193): Discovered=191, Undiscovered=192"""
    # Barn with silo
    d = (
        # Barn body
        "M -7 -1 L 3 -1 L 3 8 L -7 8 Z "
        # Barn roof
        "M -8 -1 L -2 -6 L 4 -1 Z "
        # Barn door
        "M -4 4 L -1 4 L -1 8 L -4 8 Z "
        # Silo
        "M 5 -5 L 8 -5 L 8 8 L 5 8 Z "
        # Silo dome
        "M 5 -5 L 6.5 -7 L 8 -5 Z "
        # Ground
        "M -8 8 L 9 8 L 9 9 L -8 9 Z"
    )
    write_svg(191, svg_wrap(path_tag(d), 19.0, 18.0, 9.5, 9.0))

    d = (
        "M -6 0 L 3 0 L 3 7 L -6 7 Z "
        "M -7 0 L -1.5 -4 L 4 0 Z "
        "M 5 -4 L 7 -4 L 7 7 L 5 7 Z "
        "M 5 -4 L 6 -5.5 L 7 -4 Z "
        "M -7 7 L 8 7 L 8 8 L -7 8 Z"
    )
    write_svg(192, svg_wrap(path_tag(d), 17.0, 15.0, 8.5, 7.5))


def make_filling_station_markers():
    """FillingStationMarker (190): Discovered=188, Undiscovered=189"""
    # Gas pump
    d = (
        # Pump body
        "M -4 -5 L 3 -5 L 3 7 L -4 7 Z "
        # Pump top
        "M -5 -6 L 4 -6 L 4 -5 L -5 -5 Z "
        # Display
        "M -3 -4 L 2 -4 L 2 -1 L -3 -1 Z "
        # Hose
        "M 3 -3 L 5 -3 L 7 -1 L 7 2 L 5 2 Z "
        # Nozzle
        "M 5 2 L 8 4 L 7 5 L 4 3 Z "
        # Base
        "M -5 7 L 4 7 L 4 8 L -5 8 Z"
    )
    write_svg(188, svg_wrap(path_tag(d), 15.0, 16.0, 6.0, 8.0))

    d = (
        "M -3 -4 L 2 -4 L 2 6 L -3 6 Z "
        "M -4 -5 L 3 -5 L 3 -4 L -4 -4 Z "
        "M 2 -2 L 4 -2 L 5 0 L 5 2 L 4 2 Z "
        "M -4 6 L 3 6 L 3 7 L -4 7 Z"
    )
    write_svg(189, svg_wrap(path_tag(d), 11.0, 14.0, 5.0, 7.0))


def make_drive_in_markers():
    """DriveInMarker (206): Discovered=204, Undiscovered=205"""
    # Movie screen
    d = (
        # Screen
        "M -7 -7 L 7 -7 L 7 3 L -7 3 Z "
        # Screen border
        "M -6 -6 L 6 -6 L 6 2 L -6 2 Z "
        # Support pole
        "M -1 3 L 1 3 L 1 7 L -1 7 Z "
        # Base
        "M -4 7 L 4 7 L 4 8 L -4 8 Z"
    )
    write_svg(204, svg_wrap(path_tag(d), 16.0, 17.0, 8.0, 8.5))

    d = (
        "M -6 -6 L 6 -6 L 6 2 L -6 2 Z "
        "M -5 -5 L 5 -5 L 5 1 L -5 1 Z "
        "M -0.75 2 L 0.75 2 L 0.75 6 L -0.75 6 Z "
        "M -3 6 L 3 6 L 3 7 L -3 7 Z"
    )
    write_svg(205, svg_wrap(path_tag(d), 14.0, 15.0, 7.0, 7.5))


def make_camp_markers():
    """CamperMarker (240): Discovered=238, Undiscovered=239"""
    # Tent
    d = (
        # Tent body
        "M 0 -7 L 8 6 L -8 6 Z "
        # Door flap
        "M -2 6 L 0 1 L 2 6 Z "
        # Ground
        "M -9 6 L 9 6 L 9 7 L -9 7 Z"
    )
    write_svg(238, svg_wrap(path_tag(d), 20.0, 16.0, 10.0, 8.0))

    d = (
        "M 0 -6 L 7 5 L -7 5 Z "
        "M -1.5 5 L 0 1.5 L 1.5 5 Z "
        "M -8 5 L 8 5 L 8 6 L -8 6 Z"
    )
    write_svg(239, svg_wrap(path_tag(d), 18.0, 14.0, 9.0, 7.0))


def make_car_markers():
    """CarMarker (237): Discovered=235, Undiscovered=236"""
    # Car silhouette
    # Wheels
    w1 = circle_path(-5, 4, 2, 8)
    w2 = circle_path(5, 4, 2, 8)
    d = (
        # Car body
        "M -8 0 L -5 0 L -4 -3 L 3 -3 L 5 0 L 8 0 L 8 3 L -8 3 Z "
        # Roof
        "M -3 -3 L -2 -6 L 3 -6 L 4 -3 Z "
        + w1 + " " + w2 + " "
        # Axle line
        "M -8 3 L 8 3 L 8 4 L -8 4 Z"
    )
    write_svg(235, svg_wrap(path_tag(d), 18.0, 14.0, 9.0, 7.0))

    w1 = circle_path(-4.5, 3.5, 1.5, 8)
    w2 = circle_path(4.5, 3.5, 1.5, 8)
    d = (
        "M -7 0 L -4 0 L -3 -2.5 L 3 -2.5 L 4 0 L 7 0 L 7 2.5 L -7 2.5 Z "
        "M -2.5 -2.5 L -1.5 -5 L 3 -5 L 3.5 -2.5 Z "
        + w1 + " " + w2
    )
    write_svg(236, svg_wrap(path_tag(d), 16.0, 12.0, 8.0, 6.0))


def make_radioactive_markers():
    """RadioactiveAreaMarker (73): Discovered=71, Undiscovered=72"""
    # Radiation trefoil
    # Center dot
    c_center = circle_path(0, 0, 2, 8)
    # Outer ring
    c_outer = circle_path(0, -1, 9, 20)
    c_inner = circle_path(0, -1, 7.5, 18)
    d = (
        c_center + " "
        # Three blades (simplified as triangular sectors)
        # Top blade
        "M -2 -3 L 0 -8.5 L 2 -3 Z "
        # Bottom-left blade
        "M -3 1.5 L -8 -1.5 L -4 -4 Z "
        # Bottom-right blade
        "M 3 1.5 L 8 -1.5 L 4 -4 Z "
        + c_outer + " " + c_inner
    )
    write_svg(71, svg_wrap(path_tag(d), 20.0, 20.0, 10.0, 10.0))

    c_center = circle_path(0, 0, 1.5, 8)
    c_outer = circle_path(0, -0.5, 8, 18)
    c_inner = circle_path(0, -0.5, 6.5, 16)
    d = (
        c_center + " "
        "M -1.5 -2.5 L 0 -7 L 1.5 -2.5 Z "
        "M -2.5 1 L -6.5 -1 L -3.5 -3 Z "
        "M 2.5 1 L 6.5 -1 L 3.5 -3 Z "
        + c_outer + " " + c_inner
    )
    write_svg(72, svg_wrap(path_tag(d), 18.0, 18.0, 9.0, 9.0))


def make_quarry_markers():
    """QuarryMarker (76): Discovered=74, Undiscovered=75"""
    # Pickaxe
    d = (
        # Handle
        "M -6 8 L -5 7 L 3 -1 L 2 -2 L -6 8 Z "
        # Pick head
        "M 1 -3 L 7 -8 L 8 -7 L 4 -2 Z "
        "M 1 -3 L -2 -8 L -1 -9 L 4 -2 Z "
        # Rocks
        "M -3 5 L -1 3 L 1 4 L 0 6 Z "
        "M 3 6 L 5 4 L 7 5.5 L 6 7 Z "
    )
    write_svg(74, svg_wrap(path_tag(d), 18.0, 19.0, 9.0, 10.0))

    d = (
        "M -5 7 L -4 6 L 3 -1 L 2 -2 L -5 7 Z "
        "M 1 -2.5 L 6 -7 L 7 -6 L 3.5 -1.5 Z "
        "M 1 -2.5 L -1.5 -7 L -0.5 -7.5 L 3.5 -1.5 Z"
    )
    write_svg(75, svg_wrap(path_tag(d), 16.0, 17.0, 8.0, 8.5))


def make_poi_markers():
    """POIMarker (150): Discovered=148, Undiscovered=149
    Generic point of interest - small dot/circle"""
    c1 = circle_path(0, 0, 5, 12)
    c2 = circle_path(0, 0, 3, 10)
    c3 = circle_path(0, 0, 1.5, 6)
    d = c1 + " " + c2 + " " + c3
    write_svg(148, svg_wrap(path_tag(d), 12.0, 12.0, 6.0, 6.0))

    c1 = circle_path(0, 0, 4, 10)
    c2 = circle_path(0, 0, 2.5, 8)
    c3 = circle_path(0, 0, 1, 6)
    d = c1 + " " + c2 + " " + c3
    write_svg(149, svg_wrap(path_tag(d), 10.0, 10.0, 5.0, 5.0))


def make_encampment_markers():
    """EncampmentMarker (200): Discovered=198, Undiscovered=199"""
    # Military tents/camp
    d = (
        # Tent 1
        "M -8 6 L -4 -1 L 0 6 Z "
        # Tent 2 (overlapping)
        "M -1 6 L 4 -2 L 9 6 Z "
        # Flag
        "M 4 -7 L 4 -2 L 3.5 -2 L 3.5 -7 Z "
        "M 4 -7 L 7 -5.5 L 4 -4 Z "
        # Ground
        "M -9 6 L 9 6 L 9 7 L -9 7 Z"
    )
    write_svg(198, svg_wrap(path_tag(d), 20.0, 16.0, 10.0, 8.0))

    d = (
        "M -7 5 L -3 0 L 1 5 Z "
        "M 0 5 L 4 -1 L 8 5 Z "
        "M -8 5 L 9 5 L 9 6 L -8 6 Z"
    )
    write_svg(199, svg_wrap(path_tag(d), 19.0, 13.0, 9.5, 7.0))


def make_satellite_markers():
    """SatelliteMarker (52): Discovered=50, Undiscovered=51"""
    # Satellite dish
    d = (
        # Dish
        "M -7 -2 L -5 -6 L 0 -8 L 5 -6 L 7 -2 L 5 0 L -5 0 Z "
        # Feed arm
        "M -1 0 L 0 -3 L 1 0 Z "
        # Stand
        "M -1 0 L 1 0 L 2 7 L -2 7 Z "
        # Base
        "M -4 7 L 4 7 L 4 8 L -4 8 Z"
    )
    write_svg(50, svg_wrap(path_tag(d), 16.0, 18.0, 8.0, 9.0))

    d = (
        "M -6 -1 L -4 -5 L 0 -7 L 4 -5 L 6 -1 L 4 0.5 L -4 0.5 Z "
        "M -0.5 0.5 L 0.5 0.5 L 1.5 6 L -1.5 6 Z "
        "M -3 6 L 3 6 L 3 7 L -3 7 Z"
    )
    write_svg(51, svg_wrap(path_tag(d), 14.0, 16.0, 7.0, 8.0))


def make_pond_lake_markers():
    """PondLakeMarker (87): Discovered=85, Undiscovered=86"""
    # Water waves
    d = (
        # Wave lines (3 rows)
        "M -8 -4 L -5 -6 L -2 -4 L 1 -6 L 4 -4 L 7 -6 L 8 -5 L 5 -3 L 2 -5 L -1 -3 L -4 -5 L -7 -3 Z "
        "M -8 1 L -5 -1 L -2 1 L 1 -1 L 4 1 L 7 -1 L 8 0 L 5 2 L 2 0 L -1 2 L -4 0 L -7 2 Z "
        "M -8 6 L -5 4 L -2 6 L 1 4 L 4 6 L 7 4 L 8 5 L 5 7 L 2 5 L -1 7 L -4 5 L -7 7 Z"
    )
    write_svg(85, svg_wrap(path_tag(d), 18.0, 16.0, 9.0, 8.0))

    d = (
        "M -7 -3 L -4 -5 L -1 -3 L 2 -5 L 5 -3 L 7 -5 L 7 -4 L 5 -2 L 2 -4 L -1 -2 L -4 -4 L -7 -2 Z "
        "M -7 2 L -4 0 L -1 2 L 2 0 L 5 2 L 7 0 L 7 1 L 5 3 L 2 1 L -1 3 L -4 1 L -7 3 Z"
    )
    write_svg(86, svg_wrap(path_tag(d), 16.0, 12.0, 8.0, 6.0))


def make_castle_markers():
    """CastleMarker (234): Discovered=232, Undiscovered=233"""
    # Castle with battlements
    d = (
        # Main wall
        "M -7 -1 L 7 -1 L 7 8 L -7 8 Z "
        # Battlements (crenellations)
        "M -7 -4 L -5 -4 L -5 -1 L -3 -1 L -3 -4 L -1 -4 L -1 -1 L 1 -1 L 1 -4 L 3 -4 L 3 -1 L 5 -1 L 5 -4 L 7 -4 L 7 -1 L -7 -1 Z "
        # Gate
        "M -2 3 L -2 0 L 2 0 L 2 3 L 2 8 L -2 8 Z "
        # Gate arch
        "M -2 0 L 0 -2 L 2 0 Z "
        # Ground
        "M -8 8 L 8 8 L 8 9 L -8 9 Z"
    )
    write_svg(232, svg_wrap(path_tag(d), 18.0, 15.0, 9.0, 7.0))

    d = (
        "M -6 0 L 6 0 L 6 7 L -6 7 Z "
        "M -6 -3 L -4 -3 L -4 0 L -2 0 L -2 -3 L 0 -3 L 0 0 L 2 0 L 2 -3 L 4 -3 L 4 0 L 6 0 L 6 -3 L 6 0 L -6 0 Z "
        "M -7 7 L 7 7 L 7 8 L -7 8 Z"
    )
    write_svg(233, svg_wrap(path_tag(d), 16.0, 13.0, 8.0, 6.0))


def make_brownstone_markers():
    """BrownstoneMarker (249): Discovered=247, Undiscovered=248"""
    # Row house
    d = (
        "M -7 -3 L 7 -3 L 7 8 L -7 8 Z "
        # Roof
        "M -8 -3 L 8 -3 L 8 -2 L -8 -2 Z "
        # Steps
        "M -2 6 L 2 6 L 2 8 L -2 8 Z "
        "M -3 7 L 3 7 L 3 8 L -3 8 Z "
        # Windows
        "M -5.5 -1 L -3.5 -1 L -3.5 1 L -5.5 1 Z "
        "M -1 -1 L 1 -1 L 1 1 L -1 1 Z "
        "M 3.5 -1 L 5.5 -1 L 5.5 1 L 3.5 1 Z "
        "M -5.5 3 L -3.5 3 L -3.5 5 L -5.5 5 Z "
        "M 3.5 3 L 5.5 3 L 5.5 5 L 3.5 5 Z "
        "M -8 8 L 8 8 L 8 9 L -8 9 Z"
    )
    write_svg(247, svg_wrap(path_tag(d), 18.0, 14.0, 9.0, 6.0))

    d = (
        "M -6 -2 L 6 -2 L 6 7 L -6 7 Z "
        "M -7 -2 L 7 -2 L 7 -1 L -7 -1 Z "
        "M -7 7 L 7 7 L 7 8 L -7 8 Z"
    )
    write_svg(248, svg_wrap(path_tag(d), 16.0, 12.0, 8.0, 5.0))


def make_sanc_hills_markers():
    """SancHillsMarker (55): Discovered=53, Undiscovered=54
    Home/starter settlement - house with flag"""
    d = (
        # House
        "M -6 0 L 6 0 L 6 8 L -6 8 Z "
        # Roof
        "M -7 0 L 0 -6 L 7 0 Z "
        # Door
        "M -1.5 4 L 1.5 4 L 1.5 8 L -1.5 8 Z "
        # Windows
        "M -5 2 L -3 2 L -3 4 L -5 4 Z "
        "M 3 2 L 5 2 L 5 4 L 3 4 Z "
        # Flag on roof
        "M -0.5 -8 L 0.5 -8 L 0.5 -4 L -0.5 -4 Z "
        "M 0.5 -8 L 3.5 -7 L 0.5 -6 Z "
        # Ground
        "M -7 8 L 7 8 L 7 9 L -7 9 Z"
    )
    write_svg(53, svg_wrap(path_tag(d), 16.0, 19.0, 8.0, 9.5))

    d = (
        "M -5 0 L 5 0 L 5 7 L -5 7 Z "
        "M -6 0 L 0 -5 L 6 0 Z "
        "M -0.5 -7 L 0.5 -7 L 0.5 -3 L -0.5 -3 Z "
        "M 0.5 -7 L 3 -6 L 0.5 -5 Z "
        "M -6 7 L 6 7 L 6 8 L -6 8 Z"
    )
    write_svg(54, svg_wrap(path_tag(d), 14.0, 17.0, 7.0, 8.5))


def make_low_rise_markers():
    """LowRiseMarker (117): Discovered=115, Undiscovered=116"""
    # Low-rise apartment building
    d = (
        "M -7 -2 L 7 -2 L 7 8 L -7 8 Z "
        "M -8 -3 L 8 -3 L 8 -2 L -8 -2 Z "
        # Windows row 1
        "M -5.5 0 L -3.5 0 L -3.5 2 L -5.5 2 Z "
        "M -1 0 L 1 0 L 1 2 L -1 2 Z "
        "M 3.5 0 L 5.5 0 L 5.5 2 L 3.5 2 Z "
        # Windows row 2
        "M -5.5 4 L -3.5 4 L -3.5 6 L -5.5 6 Z "
        "M 3.5 4 L 5.5 4 L 5.5 6 L 3.5 6 Z "
        # Door
        "M -1 4 L 1 4 L 1 8 L -1 8 Z "
        "M -8 8 L 8 8 L 8 9 L -8 9 Z"
    )
    write_svg(115, svg_wrap(path_tag(d), 18.0, 14.0, 9.0, 6.0))

    d = (
        "M -6 -1 L 6 -1 L 6 7 L -6 7 Z "
        "M -7 -2 L 7 -2 L 7 -1 L -7 -1 Z "
        "M -7 7 L 7 7 L 7 8 L -7 8 Z"
    )
    write_svg(116, svg_wrap(path_tag(d), 16.0, 12.0, 8.0, 5.0))


# ============================================================
# RUN ALL GENERATORS
# ============================================================

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=== Generating Military Map Marker SVGs ===")
    print()

    print("[SETTLEMENTS]")
    make_settlement_markers()    # 41, 42
    make_town_markers()          # 19, 20
    make_city_markers()          # 223, 224
    make_sanc_hills_markers()    # 53, 54
    make_low_rise_markers()      # 115, 116
    make_farm_markers()          # 191, 192
    make_filling_station_markers()  # 188, 189
    make_drive_in_markers()      # 204, 205
    make_castle_markers()        # 232, 233
    make_brownstone_markers()    # 247, 248
    make_camp_markers()          # 238, 239
    make_encampment_markers()    # 198, 199

    print("\n[MILITARY]")
    make_airfield_markers()      # 253, 254
    make_sentinel_markers()      # 44, 45
    make_bunker_markers()        # 241, 242

    print("\n[UNDERGROUND]")
    make_metro_markers()         # 109, 110
    make_sewer_markers()         # 38, 39
    make_cave_markers()          # 229, 230

    print("\n[POLICE]")
    make_police_markers()        # 88, 89

    print("\n[RADIO]")
    make_radio_tower_markers()   # 68, 69

    print("\n[MARINE]")
    make_pier_markers()          # 91, 92
    make_submarine_markers()     # 32, 33
    make_shipwreck_markers()     # 35, 36
    make_pond_lake_markers()     # 85, 86

    print("\n[INDUSTRIAL]")
    make_factory_markers()       # 133, 134
    make_industrial_dome_markers()  # 136, 137

    print("\n[POWER ARMOR]")
    make_power_armor_markers()   # 80

    print("\n[CITY SPECIALS]")
    make_diamond_city_markers()  # 211, 212
    make_goodneighbor_markers()  # 182, 183

    print("\n[SERVICES]")
    make_church_markers()        # 226, 227
    make_hospital_markers()      # 176, 177
    make_school_markers()        # 47, 48
    make_office_markers()        # 94, 95

    print("\n[WILDERNESS]")
    make_junkyard_markers()      # 124, 125
    make_graveyard_markers()     # 179, 180
    make_radioactive_markers()   # 71, 72
    make_quarry_markers()        # 74, 75
    make_car_markers()           # 235, 236

    print("\n[LANDMARKS]")
    make_landmark_markers()      # 121, 122
    make_monument_markers()      # 100, 101
    make_skyscraper_markers()    # 214, 215
    make_satellite_markers()     # 50, 51
    make_poi_markers()           # 148, 149

    # Count total shapes
    svgs = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.svg')]
    print(f"\n=== Total: {len(svgs)} custom SVG shapes generated ===")
    print("Ready for FFDec importShapes!")
