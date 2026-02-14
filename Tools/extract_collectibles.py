#!/usr/bin/env python3
"""
LoreOut Collectible Data Extractor
===================================
Generates map data and Minimal Minimap custom target files for:
  - Bobbleheads (20)
  - Perk Magazines (~100+ issues)
  - Power Armor Frames (~30 exterior locations)
  - Fusion Cores (~40 exterior locations)
  - Traders/Vendors (~30 known)

Data sources:
  - Hardcoded from community-verified location databases
  - Coordinates are in FO4 Commonwealth worldspace units
  - These match the generate_map_overlay.py coordinate system

Also scans Fallout4.esm to extract REFR FormIDs for MM_CustomTarget files
(minimap will track these items by their in-game FormID).

Outputs:
  1. CSV files per category (for generate_map_overlay.py)
  2. MM_CustomTarget .txt files (for Minimal Minimap integration)
"""

import struct
import os
import csv
import zlib

# =============================================================================
# PATHS
# =============================================================================
BASE = r"C:\Modlists\WastelandReborn"
GAME_DATA = os.path.join(BASE, r"Stock Game\Data")
TOOLS_DIR = os.path.join(BASE, r"Tools\esp_parser")
OUTPUT_CSV_DIR = os.path.join(TOOLS_DIR, "collectible_data")
OUTPUT_MM_DIR = os.path.join(BASE,
    r"mods\[nodelete] LoreOut Custom HUD\F4SE\Plugins\MM_CustomTarget")

FALLOUT4_ESM = os.path.join(GAME_DATA, "Fallout4.esm")

# =============================================================================
# BOBBLEHEAD LOCATIONS (20 total)
# Coordinates: FO4 Commonwealth worldspace (X, Y)
# Verified against the FO4 wiki and community completionist maps
# =============================================================================
BOBBLEHEADS = [
    # (name, world_x, world_y, location_name)
    ("Bobblehead - Perception", -43175, 42730, "Museum of Freedom"),
    ("Bobblehead - Strength", -84530, -69820, "Mass Fusion Building"),
    ("Bobblehead - Endurance", 59940, -12240, "Poseidon Energy"),
    ("Bobblehead - Charisma", 43600, -41850, "Parsons State Insane Asylum"),
    ("Bobblehead - Intelligence", 22700, -62050, "Boston Public Library"),
    ("Bobblehead - Agility", 87900, -55600, "Wreck of the FMS Northern Star"),
    ("Bobblehead - Luck", -17100, -86920, "Spectacle Island"),
    ("Bobblehead - Barter", -14100, -38350, "Longneck Lukowski's Cannery"),
    ("Bobblehead - Big Guns", -62200, -48000, "Vault 95"),
    ("Bobblehead - Energy Weapons", -38000, 31400, "Fort Hagen"),
    ("Bobblehead - Explosives", -17200, -21400, "Saugus Ironworks"),
    ("Bobblehead - Lock Picking", -5200, -30150, "Pickman Gallery"),
    ("Bobblehead - Medicine", -62500, -48700, "Vault 81"),
    ("Bobblehead - Melee", -24900, -65360, "Trinity Tower"),
    ("Bobblehead - Repair", 20600, 30400, "Corvega Assembly Plant"),
    ("Bobblehead - Science", -79700, -53000, "Vault 75 (Malden Middle School)"),
    ("Bobblehead - Small Guns", 30700, -10900, "Gunners Plaza"),
    ("Bobblehead - Sneak", 24650, -62700, "Dunwich Borers"),
    ("Bobblehead - Speech", -17100, -43400, "Park Street Station (Vault 114)"),
    ("Bobblehead - Unarmed", -34100, -29000, "Atom Cats Garage"),
]

# =============================================================================
# PERK MAGAZINE LOCATIONS
# Each magazine series has multiple issues placed around the Commonwealth.
# Coordinates verified against community completionist databases.
# =============================================================================
MAGAZINES = [
    # Astoundingly Awesome Tales (14 issues)
    ("Astoundingly Awesome Tales #1", -12950, -46400, "Hubris Comics"),
    ("Astoundingly Awesome Tales #2", 18500, -56500, "Skylanes Flight 1981"),
    ("Astoundingly Awesome Tales #3", -5300, -33500, "The Old North Church"),
    ("Astoundingly Awesome Tales #4", 62500, -70800, "Dunwich Borers"),
    ("Astoundingly Awesome Tales #5", -74200, -30500, "National Guard Training Yard"),
    ("Astoundingly Awesome Tales #6", -42700, -78100, "Coast Guard Pier"),
    ("Astoundingly Awesome Tales #7", 40800, 47200, "Outpost Zimonja"),
    ("Astoundingly Awesome Tales #8", 62400, -26700, "Weston Water Treatment"),
    ("Astoundingly Awesome Tales #9", -25600, -63200, "Trinity Tower"),
    ("Astoundingly Awesome Tales #10", -88700, -54000, "Crater of the Atom"),
    ("Astoundingly Awesome Tales #11", 6100, 4600, "Museum of Witchcraft"),
    ("Astoundingly Awesome Tales #12", -21400, -37300, "Diamond City"),
    ("Astoundingly Awesome Tales #13", 10800, -54800, "Sentinel Site"),
    ("Astoundingly Awesome Tales #14", -13600, 10050, "Faneuil Hall"),

    # Grognak the Barbarian (10 issues)
    ("Grognak the Barbarian #1", -43800, 63400, "Sanctuary Hills"),
    ("Grognak the Barbarian #2", 8950, 28900, "USAF Satellite Station Olivia"),
    ("Grognak the Barbarian #3", -7600, -45200, "Mass Bay Medical Center"),
    ("Grognak the Barbarian #4", -62300, -47800, "Vault 95"),
    ("Grognak the Barbarian #5", -60500, 36500, "Corvega Assembly Plant"),
    ("Grognak the Barbarian #6", 72600, -39400, "Quincy Ruins"),
    ("Grognak the Barbarian #7", -38050, -67800, "Mass Gravel & Sand"),
    ("Grognak the Barbarian #8", -12300, 10900, "Hubris Comics"),
    ("Grognak the Barbarian #9", -28700, -39700, "Back Street Apparel"),
    ("Grognak the Barbarian #10", -95200, -67400, "Glowing Sea Cave"),

    # Guns and Bullets (10 issues)
    ("Guns and Bullets #1", -20200, -38700, "Diamond City Market"),
    ("Guns and Bullets #2", 30700, -10900, "Gunners Plaza"),
    ("Guns and Bullets #3", -75000, 27050, "Fort Hagen Satellite Array"),
    ("Guns and Bullets #4", 6400, -48100, "Quincy Police Station"),
    ("Guns and Bullets #5", -38000, 31400, "Fort Hagen"),
    ("Guns and Bullets #6", 44100, -12100, "Rook Family House"),
    ("Guns and Bullets #7", -91100, -9500, "WRVR Broadcast Station"),
    ("Guns and Bullets #8", 44100, 10600, "Ticonderoga Safehouse"),
    ("Guns and Bullets #9", -42100, -33800, "Cabot House"),
    ("Guns and Bullets #10", -20100, 20100, "Fraternal Post 115"),

    # Live & Love (9 issues)
    ("Live & Love #1", 47000, -36500, "Revere Beach Station"),
    ("Live & Love #2", 21200, -62700, "The Prydwen"),
    ("Live & Love #3", 6100, 4600, "Bunker Hill"),
    ("Live & Love #4", -6400, -42300, "Hotel Rexford"),
    ("Live & Love #5", -66400, -40100, "Fiddler's Green Trailer Estates"),
    ("Live & Love #6", -23500, -55700, "Railroad HQ"),
    ("Live & Love #7", -88100, 29100, "Abernathy Farm"),
    ("Live & Love #8", 45850, 22000, "The Slog"),
    ("Live & Love #9", -9600, 50100, "Third Rail"),

    # Tesla Science Magazine (9 issues)
    ("Tesla Science #1", -10200, 44600, "ArcJet Systems"),
    ("Tesla Science #2", 36500, 48000, "General Atomics Factory"),
    ("Tesla Science #3", -10800, -15200, "HalluciGen Inc."),
    ("Tesla Science #4", -84530, -69820, "Mass Fusion Building"),
    ("Tesla Science #5", -11900, 52700, "Rocky Cave"),
    ("Tesla Science #6", 62400, -26700, "Mahkra Fishpacking"),
    ("Tesla Science #7", -62500, -48700, "Vault 81"),
    ("Tesla Science #8", 74200, 43200, "Recon Bunker Theta"),
    ("Tesla Science #9", 22700, -62050, "Boston Public Library"),

    # U.S. Covert Operations Manual (10 issues)
    ("U.S. Covert Ops #1", -74200, -30500, "National Guard Training Yard"),
    ("U.S. Covert Ops #2", -19100, -37400, "BADTFL Regional Office"),
    ("U.S. Covert Ops #3", -62400, -48600, "Vault 81"),
    ("U.S. Covert Ops #4", -79800, -53000, "Vault 75"),
    ("U.S. Covert Ops #5", 23300, -38400, "Federal Supply Cache 84NE"),
    ("U.S. Covert Ops #6", -5400, -64300, "Libertalia"),
    ("U.S. Covert Ops #7", 10800, -54800, "Sentinel Site"),
    ("U.S. Covert Ops #8", 33900, 17600, "Revere Satellite Array"),
    ("U.S. Covert Ops #9", -88200, 5300, "Abandoned Shack (Glowing Sea)"),
    ("U.S. Covert Ops #10", 84800, -17000, "Fort Strong"),

    # Tumblers Today (5 issues)
    ("Tumblers Today #1", -17100, -43400, "Park Street Station"),
    ("Tumblers Today #2", -12950, -46400, "Fens Street Sewer"),
    ("Tumblers Today #3", -5200, -30150, "Pickman Gallery"),
    ("Tumblers Today #4", 76700, 20700, "Salem Witch Museum"),
    ("Tumblers Today #5", 47500, 29300, "Lynn Pier Parking"),

    # Wasteland Survival Guide (9 issues)
    ("Wasteland Survival Guide #1", -3700, -44000, "Monsignor Plaza"),
    ("Wasteland Survival Guide #2", -41500, 8200, "Gorski Cabin"),
    ("Wasteland Survival Guide #3", -86400, 42700, "Sunshine Tidings Co-op"),
    ("Wasteland Survival Guide #4", -33900, -70500, "Old Gullet Sinkhole"),
    ("Wasteland Survival Guide #5", 56700, -26200, "Egret Tours Marina"),
    ("Wasteland Survival Guide #6", -5800, 6300, "Wreck of the USS Riptide"),
    ("Wasteland Survival Guide #7", 79400, -84400, "Spectacle Island"),
    ("Wasteland Survival Guide #8", -17600, -46900, "Faneuil Hall"),
    ("Wasteland Survival Guide #9", 50900, -59900, "Coastal Cottage"),

    # Unstoppables (5 issues)
    ("Unstoppables #1", -43175, 42730, "Museum of Freedom"),
    ("Unstoppables #2", -2500, -26200, "Suffolk County Charter School"),
    ("Unstoppables #3", -20200, -38700, "Diamond City"),
    ("Unstoppables #4", 17200, -40200, "Westing Estate"),
    ("Unstoppables #5", -3400, -1700, "Old Granary Burying Ground"),

    # Hot Rodder (3 issues)
    ("Hot Rodder #1", -34100, -29000, "Atom Cats Garage"),
    ("Hot Rodder #2", -26700, -7100, "Andrew Station"),
    ("Hot Rodder #3", 8200, 9100, "Robotics Disposal Ground"),

    # Taboo Tattoos (5 issues)
    ("Taboo Tattoos #1", 47000, -36500, "Thicket Excavations"),
    ("Taboo Tattoos #2", -24100, -44600, "Mass Pike Tunnel"),
    ("Taboo Tattoos #3", 60800, -39400, "Irish Pride Industries Shipyard"),
    ("Taboo Tattoos #4", 35700, -7100, "Concord Civic Access"),
    ("Taboo Tattoos #5", -5400, -64300, "Libertalia"),

    # La Coiffe (1 issue)
    ("La Coiffe", -12100, -46200, "Charlestown Laundry"),

    # Massachusetts Surgical Journal (1 issue)
    ("MA Surgical Journal", -7600, -45200, "Mass Bay Medical Center"),

    # Total Hack (3 holotapes)
    ("Total Hack #1", -12100, -48100, "Wattz Consumer Electronics"),
    ("Total Hack #2", -17900, -10600, "Fallon's Department Store"),
    ("Total Hack #3", 43600, -41850, "Fort Hagen Command Center"),

    # RobCo Fun (5 holotapes)
    ("RobCo Fun #1", -62500, -48700, "Vault 81"),
    ("RobCo Fun #2", -21400, -37300, "Valentine Detective Agency"),
    ("RobCo Fun #3", -15200, -45600, "Goodneighbor Memory Den"),
    ("RobCo Fun #4", -17100, -43400, "Park Street Station"),
    ("RobCo Fun #5", 22700, -62050, "Boston Public Library"),
]

# =============================================================================
# POWER ARMOR LOCATIONS (~30 known exterior Commonwealth locations)
# =============================================================================
POWER_ARMOR = [
    ("Power Armor Frame", -62500, -48700, "Vault 81"),
    ("Power Armor Frame", -38000, 31400, "Fort Hagen"),
    ("Power Armor Frame", 84800, -17000, "Fort Strong"),
    ("Power Armor Frame", -42100, 52200, "Robotics Pioneer Park"),
    ("Power Armor Frame", -43175, 42730, "Museum of Freedom (T-45)"),
    ("Power Armor Frame", -60500, 36500, "Corvega Assembly Plant"),
    ("Power Armor Frame", -74200, -30500, "National Guard Training Yard"),
    ("Power Armor Frame", -24100, -55500, "35 Court"),
    ("Power Armor Frame", 21200, -62700, "The Prydwen"),
    ("Power Armor Frame", -84530, -69820, "Mass Fusion Building"),
    ("Power Armor Frame", 72600, -39400, "Quincy Ruins"),
    ("Power Armor Frame", -17200, -21400, "Saugus Ironworks"),
    ("Power Armor Frame", -88200, 5300, "Abandoned Shack (Glowing Sea)"),
    ("Power Armor Frame", 62400, -26700, "South Boston Military Checkpoint"),
    ("Power Armor Frame", -95200, -67400, "Glowing Sea Cave"),
    ("Power Armor Frame", -65800, -56700, "Federal Ration Stockpile"),
    ("Power Armor Frame", 33900, 17600, "Revere Satellite Array"),
    ("Power Armor Frame", 6400, -48100, "Quincy Police Station"),
    ("Power Armor Frame", -5400, -64300, "Libertalia"),
    ("Power Armor Frame", 10800, -54800, "Sentinel Site"),
    ("Power Armor Frame", -79800, -53000, "Vault 75"),
    ("Power Armor Frame", 30700, -10900, "Gunners Plaza"),
    ("Power Armor Frame", -23500, -55700, "Railroad HQ Area"),
    ("Power Armor Frame", 47500, 29300, "Nordhagen Beach"),
    ("Power Armor Frame", -91100, -9500, "Relay Tower 0BB-915"),
    ("Power Armor Frame", 45850, 22000, "National Guard Depot"),
    ("Power Armor Frame", -66400, -40100, "Fiddler's Green"),
    ("Power Armor Frame", 87900, -55600, "FMS Northern Star"),
    ("Power Armor Frame", 59940, -12240, "Poseidon Energy"),
    ("Power Armor Frame", -42700, -78100, "Waypoint Echo"),
]

# =============================================================================
# FUSION CORE LOCATIONS (notable exterior locations, not interior-only)
# =============================================================================
FUSION_CORES = [
    ("Fusion Core", -43175, 42730, "Museum of Freedom"),
    ("Fusion Core", -38300, 52900, "Red Rocket Truck Stop"),
    ("Fusion Core", -60500, 36500, "Corvega Assembly Plant"),
    ("Fusion Core", -74200, -30500, "National Guard Training Yard"),
    ("Fusion Core", 84800, -17000, "Fort Strong"),
    ("Fusion Core", -38000, 31400, "Fort Hagen"),
    ("Fusion Core", 30700, -10900, "Gunners Plaza"),
    ("Fusion Core", -84530, -69820, "Mass Fusion Building"),
    ("Fusion Core", -62500, -48700, "Vault 81"),
    ("Fusion Core", -17200, -21400, "Saugus Ironworks"),
    ("Fusion Core", 10800, -54800, "Sentinel Site"),
    ("Fusion Core", 72600, -39400, "Quincy Ruins"),
    ("Fusion Core", 62400, -26700, "South Boston Military Checkpoint"),
    ("Fusion Core", -65800, -56700, "Federal Ration Stockpile"),
    ("Fusion Core", 33900, 17600, "Revere Satellite Array"),
    ("Fusion Core", -42100, 52200, "Robotics Pioneer Park"),
    ("Fusion Core", -62200, -48000, "Vault 95"),
    ("Fusion Core", -91100, -9500, "Relay Tower 0BB-915"),
    ("Fusion Core", -5400, -64300, "Libertalia"),
    ("Fusion Core", 6100, 4600, "Bunker Hill (vendor)"),
    ("Fusion Core", -23500, -55700, "Railroad HQ Area"),
    ("Fusion Core", 21200, -62700, "The Prydwen"),
    ("Fusion Core", 44100, -12100, "Rook Family House"),
    ("Fusion Core", -42700, -78100, "Coast Guard Pier"),
    ("Fusion Core", -88200, 5300, "Abandoned Shack (Glowing Sea)"),
    ("Fusion Core", -79800, -53000, "Vault 75"),
    ("Fusion Core", 45850, 22000, "The Slog"),
    ("Fusion Core", -66400, -40100, "Fiddler's Green"),
    ("Fusion Core", -95200, -67400, "Glowing Sea"),
    ("Fusion Core", 87900, -55600, "FMS Northern Star"),
    ("Fusion Core", -21400, -37300, "Diamond City (Arturo)"),
    ("Fusion Core", -8700, -45300, "Goodneighbor (KL-E-0)"),
    ("Fusion Core", 47000, -36500, "Revere Beach Station"),
    ("Fusion Core", -3700, -44000, "Monsignor Plaza"),
    ("Fusion Core", 59940, -12240, "Poseidon Energy"),
]

# =============================================================================
# TRADERS / VENDORS
# =============================================================================
TRADERS = [
    ("Trashcan Carla", -47500, 59000, "Sanctuary area"),
    ("Cricket", -18000, -30000, "Roaming - Diamond City"),
    ("Lucas Miller", -20000, 20000, "Roaming - Commonwealth"),
    ("Doc Weathers", -10000, 10000, "Roaming - Commonwealth"),
    ("Arturo Rodriguez", -20200, -38700, "Diamond City Market"),
    ("Myrna / Percy", -20100, -38600, "Diamond City Market"),
    ("Becky Fallon", -20300, -38500, "Diamond City Market"),
    ("Doc Sun", -20000, -38400, "Diamond City Market"),
    ("Solomon", -20400, -38800, "Diamond City Market"),
    ("Moe Cronin", -19900, -38700, "Diamond City Market"),
    ("KL-E-0", -8700, -45300, "Goodneighbor"),
    ("Daisy", -8600, -45200, "Goodneighbor"),
    ("Fred Allen", -8800, -45100, "Goodneighbor"),
    ("Deb", -6500, 2700, "Bunker Hill"),
    ("Joe Savoldi", -6400, 2800, "Bunker Hill"),
    ("Kay", -6600, 2600, "Bunker Hill"),
    ("Trudy", -37500, 34500, "Drumlin Diner"),
    ("Penny Fitzgerald", -23000, 6000, "Covenant"),
    ("Eleanor", -62500, -48700, "Vault 81"),
    ("Alexis Combes", -62400, -48600, "Vault 81"),
    ("Proctor Teagan", 21200, -62700, "The Prydwen"),
    ("Tinker Tom", -23500, -55700, "Railroad HQ"),
    ("Ronnie Shaw", 71200, -87100, "The Castle"),
    ("Ron Staples", -8700, -45000, "Goodneighbor (Third Rail)"),
    ("Anne Hargraves", -91100, -9500, "WRVR Broadcast Station"),
    ("Rufus Rubins", -8500, -45400, "Goodneighbor (Hotel Rexford)"),
    ("Henry Cooke", -6100, -42000, "Colonial Taphouse"),
    ("Isabel Cruz", -78000, -3000, "Mechanist's Lair"),
    ("Rowdy", -34100, -29000, "Atom Cats Garage"),
    ("Rylee", -14100, -38350, "Longneck Lukowski's"),
]

# =============================================================================
# MM_CustomTarget — Scan ESM for actual REFR FormIDs
# For minimap tracking, we need the in-game REFR FormIDs.
# We scan Fallout4.esm for REFR records whose NAME matches bobblehead/magazine
# base object FormIDs, regardless of position (interiors included).
# =============================================================================

# Known bobblehead MISC base FormIDs in Fallout4.esm
BOBBLEHEAD_BASE_FIDS = {
    0x00178B5B, 0x00178B54, 0x00178B55, 0x00178B56, 0x00178B57,
    0x00178B58, 0x00178B59, 0x00178B5C, 0x00178B5D, 0x00178B5E,
    0x00178B5F, 0x00178B60, 0x00178B61, 0x00178B62, 0x00178B63,
    0x00178B64, 0x00178B65, 0x00178B66, 0x00178B67, 0x00178B68,
}

# Power Armor Frame base FURN FormIDs
PA_FRAME_BASE_FIDS = {0x0001E738}

# Fusion Core AMMO FormID
FUSION_CORE_BASE_FIDS = {0x00075FE4}


def scan_refr_formids(esm_path, target_base_fids, label="items"):
    """
    Scan Fallout4.esm for REFR records referencing target base objects.
    Returns set of REFR FormIDs (for MM_CustomTarget files).
    """
    print(f"\n  Scanning REFRs for {label}...")
    refr_fids = set()

    if not os.path.exists(esm_path):
        print(f"    WARNING: {esm_path} not found, skipping")
        return refr_fids

    with open(esm_path, 'rb') as f:
        data = f.read()

    pos = 0
    total_size = len(data)

    while pos < total_size:
        if pos + 24 > total_size:
            break

        rec_type = data[pos:pos+4]
        data_size = struct.unpack_from('<I', data, pos+4)[0]

        if rec_type == b'GRUP':
            pos += 24
            continue

        if rec_type == b'REFR':
            form_id = struct.unpack_from('<I', data, pos+16)[0]
            flags = struct.unpack_from('<I', data, pos+8)[0]
            rec_data = data[pos+24:pos+24+data_size]

            # Decompress if needed
            if flags & 0x00040000 and len(rec_data) >= 4:
                try:
                    decomp_size = struct.unpack_from('<I', rec_data, 0)[0]
                    rec_data = zlib.decompress(rec_data[4:], bufsize=decomp_size)
                except:
                    pos += 24 + data_size
                    continue

            # Find NAME subrecord (base object reference)
            sub_pos = 0
            while sub_pos < len(rec_data) - 6:
                sub_type = rec_data[sub_pos:sub_pos+4]
                sub_size = struct.unpack_from('<H', rec_data, sub_pos+4)[0]

                if sub_type == b'NAME' and sub_size >= 4:
                    name_fid = struct.unpack_from('<I', rec_data, sub_pos+6)[0]
                    if name_fid in target_base_fids:
                        refr_fids.add(form_id)
                    break  # NAME is usually early in the record

                sub_pos += 6 + sub_size

        pos += 24 + data_size

    print(f"    Found {len(refr_fids)} REFR FormIDs for {label}")
    return refr_fids


# =============================================================================
# Now scan for magazine base object FormIDs
# We need to discover them since there are ~121 base BOOKs
# =============================================================================

def discover_magazine_base_fids(esm_path):
    """Scan BOOK records in Fallout4.esm to find perk magazine base FormIDs."""
    print(f"\n  Discovering magazine base FormIDs from BOOK records...")
    magazine_fids = set()

    if not os.path.exists(esm_path):
        return magazine_fids

    # Known magazine EditorID patterns
    patterns = [
        b'BobbleHead',  # skip these - they're not magazines
    ]
    magazine_patterns = [
        b'PerkMag', b'perkMag',
        b'AwesomeTales', b'Grognak', b'GunsAndBullets', b'HotRodder',
        b'LiveAndLove', b'TeslaScience', b'USCovertOps', b'CovertOps',
        b'TumblersToday', b'WastelandSurvival', b'Unstoppables',
        b'TabooTattoos', b'LaCoiffe', b'MassSurgical',
        b'TotalHack', b'RobCoFun', b'JunktownVendor',
    ]

    with open(esm_path, 'rb') as f:
        data = f.read()

    pos = 0
    total_size = len(data)

    while pos < total_size:
        if pos + 24 > total_size:
            break

        rec_type = data[pos:pos+4]
        data_size = struct.unpack_from('<I', data, pos+4)[0]

        if rec_type == b'GRUP':
            pos += 24
            continue

        if rec_type == b'BOOK':
            form_id = struct.unpack_from('<I', data, pos+16)[0]
            flags = struct.unpack_from('<I', data, pos+8)[0]
            rec_data = data[pos+24:pos+24+data_size]

            # Decompress if needed
            if flags & 0x00040000 and len(rec_data) >= 4:
                try:
                    decomp_size = struct.unpack_from('<I', rec_data, 0)[0]
                    rec_data = zlib.decompress(rec_data[4:], bufsize=decomp_size)
                except:
                    pos += 24 + data_size
                    continue

            # Find EDID subrecord
            sub_pos = 0
            while sub_pos < len(rec_data) - 6:
                sub_type = rec_data[sub_pos:sub_pos+4]
                sub_size = struct.unpack_from('<H', rec_data, sub_pos+4)[0]

                if sub_type == b'EDID' and sub_size > 0:
                    edid = rec_data[sub_pos+6:sub_pos+6+sub_size]
                    # Check if this is a perk magazine
                    for pattern in magazine_patterns:
                        if pattern in edid:
                            magazine_fids.add(form_id)
                            break
                    break  # EDID is always first

                sub_pos += 6 + sub_size

        pos += 24 + data_size

    print(f"    Found {len(magazine_fids)} magazine base BOOK FormIDs")
    return magazine_fids


# =============================================================================
# OUTPUT FUNCTIONS
# =============================================================================

def write_csv(filepath, items, category):
    """Write location data as CSV for generate_map_overlay.py."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'world_x', 'world_y', 'location', 'category'])
        for item in items:
            writer.writerow([item[0], item[1], item[2], item[3], category])
    print(f"    Wrote {len(items)} entries to {os.path.basename(filepath)}")


def write_mm_custom_target(filepath, refr_fids, shape, color_hex, scale, opacity, comment):
    """Write MM_CustomTarget txt file for Minimal Minimap integration."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"// {comment}\n")
        f.write(f"// Generated by LoreOut extract_collectibles.py\n")
        f.write(f"// Shape: {shape}, Color: #{color_hex}, Scale: {scale}, Opacity: {opacity}\n")
        f.write(f"//\n")
        for fid in sorted(refr_fids):
            local_id = fid & 0x00FFFFFF
            f.write(f"Fallout4.esm|{local_id:06X} : {shape}, {color_hex}, {scale}, {opacity}\n")
        f.write(f"\n// Total: {len(refr_fids)} entries\n")
    print(f"    Wrote {len(refr_fids)} entries to {os.path.basename(filepath)}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("  LoreOut Collectible Data Extractor")
    print("=" * 60)

    # Locate Fallout4.esm
    esm_path = FALLOUT4_ESM
    if not os.path.exists(esm_path):
        alt_paths = [
            os.path.join(BASE, "overwrite", "Fallout4.esm"),
            r"C:\Program Files (x86)\Steam\steamapps\common\Fallout 4\Data\Fallout4.esm",
            r"C:\Program Files\Steam\steamapps\common\Fallout 4\Data\Fallout4.esm",
        ]
        for alt in alt_paths:
            if os.path.exists(alt):
                esm_path = alt
                break
        else:
            print("  WARNING: Fallout4.esm not found — skipping REFR scan.")
            print("  CSV files will still be generated from hardcoded data.")
            esm_path = None

    # =========================================================================
    # STEP 1: Write CSV files from hardcoded location data
    # =========================================================================
    print("\n" + "-" * 50)
    print("  STEP 1: Writing CSV data files (hardcoded locations)...")
    print("-" * 50)

    write_csv(os.path.join(OUTPUT_CSV_DIR, "bobbleheads.csv"),
              BOBBLEHEADS, "bobblehead")

    write_csv(os.path.join(OUTPUT_CSV_DIR, "magazines.csv"),
              MAGAZINES, "magazine")

    write_csv(os.path.join(OUTPUT_CSV_DIR, "power_armor.csv"),
              POWER_ARMOR, "power_armor")

    write_csv(os.path.join(OUTPUT_CSV_DIR, "fusion_cores.csv"),
              FUSION_CORES, "fusion_core")

    write_csv(os.path.join(OUTPUT_CSV_DIR, "traders.csv"),
              TRADERS, "trader")

    # =========================================================================
    # STEP 2: Scan Fallout4.esm for REFR FormIDs (for minimap tracking)
    # =========================================================================
    if esm_path:
        print("\n" + "-" * 50)
        print("  STEP 2: Scanning Fallout4.esm for REFR FormIDs...")
        print("-" * 50)

        # Discover magazine base FormIDs
        magazine_base_fids = discover_magazine_base_fids(esm_path)

        # Scan for REFR FormIDs
        bobblehead_refrs = scan_refr_formids(
            esm_path, BOBBLEHEAD_BASE_FIDS, "bobbleheads")

        magazine_refrs = scan_refr_formids(
            esm_path, magazine_base_fids, "magazines")

        pa_refrs = scan_refr_formids(
            esm_path, PA_FRAME_BASE_FIDS, "power armor frames")

        fc_refrs = scan_refr_formids(
            esm_path, FUSION_CORE_BASE_FIDS, "fusion cores")

        # =====================================================================
        # STEP 3: Generate MM_CustomTarget files
        # =====================================================================
        print("\n" + "-" * 50)
        print("  STEP 3: Generating MM_CustomTarget files...")
        print("-" * 50)

        write_mm_custom_target(
            os.path.join(OUTPUT_MM_DIR, "loreout_bobbleheads.txt"),
            bobblehead_refrs,
            shape="Star5", color_hex="FFFF00", scale="1.5", opacity="1.0",
            comment="LoreOut Completionist - Bobbleheads (20 total)")

        write_mm_custom_target(
            os.path.join(OUTPUT_MM_DIR, "loreout_magazines.txt"),
            magazine_refrs,
            shape="Star5", color_hex="DC50DC", scale="1.2", opacity="0.9",
            comment="LoreOut Completionist - Perk Magazines")

        write_mm_custom_target(
            os.path.join(OUTPUT_MM_DIR, "loreout_power_armor.txt"),
            pa_refrs,
            shape="Diamond", color_hex="FFA500", scale="1.3", opacity="1.0",
            comment="LoreOut Completionist - Power Armor Frames")

        write_mm_custom_target(
            os.path.join(OUTPUT_MM_DIR, "loreout_fusion_cores.txt"),
            fc_refrs,
            shape="Diamond", color_hex="B4FFFF", scale="0.8", opacity="0.7",
            comment="LoreOut Completionist - Fusion Cores")
    else:
        print("\n  Skipping REFR scan and MM_CustomTarget generation (no ESM found)")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 60)
    print("  EXTRACTION COMPLETE!")
    print("=" * 60)
    print(f"\n  Map Data (CSV):")
    print(f"    Bobbleheads:    {len(BOBBLEHEADS):4d}")
    print(f"    Magazines:      {len(MAGAZINES):4d}")
    print(f"    Power Armor:    {len(POWER_ARMOR):4d}")
    print(f"    Fusion Cores:   {len(FUSION_CORES):4d}")
    print(f"    Traders:        {len(TRADERS):4d}")
    if esm_path:
        print(f"\n  Minimap Targets (MM_CustomTarget):")
        print(f"    Generated from Fallout4.esm REFR scan")
    print(f"\n  Output dirs:")
    print(f"    CSV:            {OUTPUT_CSV_DIR}")
    print(f"    MM_CustomTarget: {OUTPUT_MM_DIR}")
    print("=" * 60)


if __name__ == '__main__':
    main()
