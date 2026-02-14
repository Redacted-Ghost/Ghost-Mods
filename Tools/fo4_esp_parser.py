"""
Fallout 4 ESP/ESM/ESL Binary Parser
====================================
Reads plugin files WITHOUT needing master files loaded.
Extracts all records, subrecords, FormIDs, keywords, and values.

Usage:
    python fo4_esp_parser.py <path_to_esp> [--type WEAP] [--csv output.csv] [--verbose]

Examples:
    python fo4_esp_parser.py "MAIM.esp" --type WEAP --csv maim_weapons.csv
    python fo4_esp_parser.py "AnomalyPatching.esp" --csv anomaly_dump.csv
    python fo4_esp_parser.py "MAIM.esp" --type KYWD --csv maim_keywords.csv
    python fo4_esp_parser.py "MAIM.esp" --summary
"""

import struct
import zlib
import os
import sys
import csv
import argparse
import json
from collections import defaultdict, OrderedDict


# ============================================================================
# CONSTANTS
# ============================================================================

# Record flags
FLAG_ESM         = 0x00000001
FLAG_LOCALIZED   = 0x00000040
FLAG_ESL         = 0x00000200
FLAG_COMPRESSED  = 0x00040000

# Record types we care about most for modding
INTERESTING_TYPES = {
    'KYWD', 'WEAP', 'AMMO', 'ARMO', 'NPC_', 'PERK', 'SPEL', 'ENCH',
    'ALCH', 'COBJ', 'LVLI', 'LVLN', 'FLST', 'GLOB', 'GMST', 'RACE',
    'MISC', 'OMOD', 'INNR', 'FACT'
}

# Subrecords that contain human-readable strings (when not localized)
STRING_SUBRECORDS = {'EDID', 'FULL', 'DESC', 'MODL', 'ICON', 'MAST', 'CNAM',
                     'SNAM', 'DNAM', 'NNAM', 'ANAM', 'BNAM'}

# Known vanilla Fallout 4 weapon keywords (FormIDs from Fallout4.esm)
# These are the ones MAIM Redux uses for penetration classification
VANILLA_WEAPON_KEYWORDS = {
    0x0004A0A2: 'WeaponTypeRifle',
    0x0004A0A1: 'WeaponTypePistol',
    0x00054C45: 'WeaponTypeShotgun',
    0x000A36BE: 'WeaponTypeSniper',
    0x000A36D6: 'WeaponTypeGatling',
    0x00054C46: 'WeaponTypeLaser',
    0x000A36D4: 'WeaponTypePlasma',
    0x000A36D5: 'WeaponTypeHeavyGun',
    0x0004A0A4: 'WeaponTypeMelee1H',
    0x0004A0A5: 'WeaponTypeMelee2H',
    0x0004A0A6: 'WeaponTypeUnarmed',
    0x0004A0A3: 'WeaponTypeAutomatic',
    0x000A36D7: 'WeaponTypeGrenade',
    0x000A36D8: 'WeaponTypeMine',
    0x000424EF: 'ObjectTypeWeapon',
    0x000424EE: 'ObjectTypeArmor',
    0x000424F0: 'ObjectTypeDrink',
    0x000424F1: 'ObjectTypeFood',
}


# ============================================================================
# BINARY READING HELPERS
# ============================================================================

class BinaryReader:
    """Wraps a bytes object for sequential reading with position tracking."""

    def __init__(self, data, offset=0):
        self.data = data
        self.pos = offset

    def read(self, n):
        result = self.data[self.pos:self.pos + n]
        self.pos += n
        return result

    def read_uint8(self):
        val = struct.unpack_from('<B', self.data, self.pos)[0]
        self.pos += 1
        return val

    def read_uint16(self):
        val = struct.unpack_from('<H', self.data, self.pos)[0]
        self.pos += 2
        return val

    def read_uint32(self):
        val = struct.unpack_from('<I', self.data, self.pos)[0]
        self.pos += 4
        return val

    def read_int32(self):
        val = struct.unpack_from('<i', self.data, self.pos)[0]
        self.pos += 4
        return val

    def read_float(self):
        val = struct.unpack_from('<f', self.data, self.pos)[0]
        self.pos += 4
        return val

    def read_string(self, n):
        raw = self.data[self.pos:self.pos + n]
        self.pos += n
        # Strip null terminator
        if b'\x00' in raw:
            raw = raw[:raw.index(b'\x00')]
        try:
            return raw.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return raw.decode('cp1252')
            except:
                return raw.hex()

    def read_sig(self):
        """Read a 4-byte record/subrecord signature."""
        raw = self.data[self.pos:self.pos + 4]
        self.pos += 4
        try:
            return raw.decode('ascii')
        except:
            return raw.hex()

    def remaining(self):
        return len(self.data) - self.pos

    def has_data(self):
        return self.pos < len(self.data)

    def peek_sig(self):
        if self.pos + 4 > len(self.data):
            return None
        try:
            return self.data[self.pos:self.pos + 4].decode('ascii')
        except:
            return None

    def skip(self, n):
        self.pos += n


# ============================================================================
# ESP FILE PARSER
# ============================================================================

class ESPRecord:
    """Represents a single record from an ESP file."""

    def __init__(self):
        self.type = ''
        self.data_size = 0
        self.flags = 0
        self.form_id = 0
        self.timestamp = 0
        self.version_info = 0
        self.subrecords = []  # List of (type, data) tuples
        self.is_compressed = False

        # Parsed fields (populated by parse_subrecords)
        self.editor_id = ''
        self.full_name = ''
        self.keywords = []  # List of FormIDs
        self.raw_data = {}  # Subrecord type -> raw bytes for further parsing

    @property
    def form_id_hex(self):
        return f'{self.form_id:08X}'

    @property
    def master_index(self):
        return (self.form_id >> 24) & 0xFF

    @property
    def local_id(self):
        return self.form_id & 0x00FFFFFF

    def parse_subrecords(self):
        """Parse common subrecords into named fields."""
        keyword_count = 0

        for sub_type, sub_data in self.subrecords:
            if sub_type == 'EDID':
                try:
                    self.editor_id = sub_data.rstrip(b'\x00').decode('utf-8')
                except:
                    try:
                        self.editor_id = sub_data.rstrip(b'\x00').decode('cp1252')
                    except:
                        self.editor_id = sub_data.hex()

            elif sub_type == 'FULL':
                if len(sub_data) == 4:
                    # Localized string ID
                    string_id = struct.unpack('<I', sub_data)[0]
                    self.full_name = f'[LSTRING:{string_id:08X}]'
                else:
                    try:
                        self.full_name = sub_data.rstrip(b'\x00').decode('utf-8')
                    except:
                        try:
                            self.full_name = sub_data.rstrip(b'\x00').decode('cp1252')
                        except:
                            self.full_name = sub_data.hex()

            elif sub_type == 'KSIZ':
                if len(sub_data) >= 4:
                    keyword_count = struct.unpack('<I', sub_data)[0]

            elif sub_type == 'KWDA':
                self.keywords = []
                for i in range(0, len(sub_data), 4):
                    if i + 4 <= len(sub_data):
                        kw_fid = struct.unpack('<I', sub_data[i:i+4])[0]
                        self.keywords.append(kw_fid)

            # Store raw data for type-specific parsing
            if sub_type not in self.raw_data:
                self.raw_data[sub_type] = sub_data
            else:
                # Some subrecords appear multiple times (e.g., MAST)
                if isinstance(self.raw_data[sub_type], list):
                    self.raw_data[sub_type].append(sub_data)
                else:
                    self.raw_data[sub_type] = [self.raw_data[sub_type], sub_data]


class ESPParser:
    """Parses a Fallout 4 ESP/ESM/ESL file."""

    def __init__(self, filepath, verbose=False):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.verbose = verbose

        # TES4 header info
        self.version = 0.0
        self.num_records = 0
        self.next_object_id = 0
        self.author = ''
        self.description = ''
        self.masters = []  # Ordered list of master filenames
        self.is_esm = False
        self.is_esl = False
        self.is_localized = False

        # All parsed records indexed by type
        self.records = defaultdict(list)
        self.records_by_formid = {}

        # Statistics
        self.group_count = 0
        self.record_count = 0
        self.compressed_count = 0
        self.type_counts = defaultdict(int)

    def parse(self, filter_types=None):
        """
        Parse the entire ESP file.
        filter_types: optional set of record types to parse (e.g., {'WEAP', 'KYWD'})
                      Pass None to parse everything.
        """
        with open(self.filepath, 'rb') as f:
            data = f.read()

        reader = BinaryReader(data)

        # First record must be TES4
        self._parse_tes4(reader)

        # Parse remaining groups
        while reader.has_data() and reader.remaining() >= 4:
            sig = reader.peek_sig()
            if sig == 'GRUP':
                self._parse_group(reader, filter_types)
            else:
                # Shouldn't happen at top level, but handle gracefully
                self._parse_record(reader, filter_types)

        if self.verbose:
            print(f'\nParsing complete:')
            print(f'  File: {self.filename}')
            print(f'  Masters: {self.masters}')
            print(f'  Groups: {self.group_count}')
            print(f'  Records: {self.record_count}')
            print(f'  Compressed: {self.compressed_count}')
            print(f'  Record types found:')
            for rtype, count in sorted(self.type_counts.items()):
                print(f'    {rtype}: {count}')

    def _parse_tes4(self, reader):
        """Parse the TES4 file header record."""
        sig = reader.read_sig()
        assert sig == 'TES4', f'Expected TES4 header, got {sig}'

        data_size = reader.read_uint32()
        flags = reader.read_uint32()
        form_id = reader.read_uint32()
        timestamp = reader.read_uint32()
        version_info = reader.read_uint32()  # 2x uint16

        self.is_esm = bool(flags & FLAG_ESM)
        self.is_esl = bool(flags & FLAG_ESL)
        self.is_localized = bool(flags & FLAG_LOCALIZED)

        # Parse TES4 subrecords
        end_pos = reader.pos + data_size
        current_master = None

        while reader.pos < end_pos:
            sub_type = reader.read_sig()
            sub_size = reader.read_uint16()
            sub_data = reader.read(sub_size)

            if sub_type == 'HEDR':
                self.version = struct.unpack('<f', sub_data[0:4])[0]
                self.num_records = struct.unpack('<i', sub_data[4:8])[0]
                self.next_object_id = struct.unpack('<I', sub_data[8:12])[0]

            elif sub_type == 'CNAM':
                try:
                    self.author = sub_data.rstrip(b'\x00').decode('utf-8')
                except:
                    self.author = sub_data.rstrip(b'\x00').decode('cp1252', errors='replace')

            elif sub_type == 'SNAM':
                try:
                    self.description = sub_data.rstrip(b'\x00').decode('utf-8')
                except:
                    self.description = sub_data.rstrip(b'\x00').decode('cp1252', errors='replace')

            elif sub_type == 'MAST':
                master_name = sub_data.rstrip(b'\x00').decode('utf-8', errors='replace')
                self.masters.append(master_name)

            elif sub_type == 'DATA':
                pass  # Master file size data, we don't need it

        if self.verbose:
            flag_str = []
            if self.is_esm: flag_str.append('ESM')
            if self.is_esl: flag_str.append('ESL')
            if self.is_localized: flag_str.append('LOCALIZED')
            print(f'TES4 Header:')
            print(f'  Version: {self.version}')
            print(f'  Flags: {" | ".join(flag_str) if flag_str else "ESP"}')
            print(f'  Masters ({len(self.masters)}):')
            for i, m in enumerate(self.masters):
                print(f'    [{i:02X}] {m}')
            print(f'  This plugin index: [{len(self.masters):02X}]')

    def _parse_group(self, reader, filter_types=None):
        """Parse a GRUP record."""
        sig = reader.read_sig()
        assert sig == 'GRUP', f'Expected GRUP, got {sig}'

        group_size = reader.read_uint32()  # Includes 24-byte header
        label_raw = reader.read(4)
        group_type = reader.read_int32()
        timestamp = reader.read_uint32()
        version_info = reader.read_uint32()

        self.group_count += 1

        # Content size = group_size minus the 24-byte header we just read
        content_size = group_size - 24
        end_pos = reader.pos + content_size

        # For top-level groups (type 0), label is the record type
        if group_type == 0:
            try:
                group_label = label_raw.decode('ascii')
            except:
                group_label = label_raw.hex()

            if self.verbose:
                print(f'  Group: {group_label} (size: {content_size} bytes)')

            # Skip groups we don't care about if filtering
            if filter_types and group_label not in filter_types:
                reader.skip(content_size)
                return

        # Parse contents
        while reader.pos < end_pos:
            if reader.remaining() < 4:
                break

            next_sig = reader.peek_sig()
            if next_sig == 'GRUP':
                self._parse_group(reader, filter_types)
            else:
                self._parse_record(reader, filter_types)

    def _parse_record(self, reader, filter_types=None):
        """Parse a single record."""
        if reader.remaining() < 24:
            reader.skip(reader.remaining())
            return None

        sig = reader.read_sig()
        data_size = reader.read_uint32()
        flags = reader.read_uint32()
        form_id = reader.read_uint32()
        timestamp = reader.read_uint32()
        version_info = reader.read_uint32()

        self.record_count += 1
        self.type_counts[sig] += 1

        # Read the record data
        if data_size > reader.remaining():
            reader.skip(reader.remaining())
            return None

        record_data = reader.read(data_size)

        # Create record object
        rec = ESPRecord()
        rec.type = sig
        rec.data_size = data_size
        rec.flags = flags
        rec.form_id = form_id
        rec.timestamp = timestamp
        rec.version_info = version_info
        rec.is_compressed = bool(flags & FLAG_COMPRESSED)

        # Decompress if needed
        if rec.is_compressed and len(record_data) >= 4:
            self.compressed_count += 1
            decompressed_size = struct.unpack('<I', record_data[0:4])[0]
            try:
                record_data = zlib.decompress(record_data[4:], bufsize=decompressed_size)
            except zlib.error as e:
                if self.verbose:
                    print(f'    WARNING: Failed to decompress {sig} {form_id:08X}: {e}')
                return rec

        # Parse subrecords
        sub_reader = BinaryReader(record_data)
        xxxx_size = None

        while sub_reader.has_data() and sub_reader.remaining() >= 6:
            sub_type = sub_reader.read_sig()
            sub_size = sub_reader.read_uint16()

            # Handle XXXX oversized subrecord
            if sub_type == 'XXXX':
                xxxx_size = struct.unpack('<I', sub_reader.read(4))[0]
                continue

            if xxxx_size is not None:
                sub_size = xxxx_size
                xxxx_size = None

            if sub_size > sub_reader.remaining():
                break

            sub_data = sub_reader.read(sub_size)
            rec.subrecords.append((sub_type, sub_data))

        # Parse common subrecord fields
        rec.parse_subrecords()

        # Store the record
        self.records[sig].append(rec)
        self.records_by_formid[form_id] = rec

        return rec

    def resolve_formid(self, form_id):
        """
        Resolve a FormID to (master_filename, local_id).
        Returns (filename, local_id_hex) tuple.
        """
        master_idx = (form_id >> 24) & 0xFF
        local_id = form_id & 0x00FFFFFF

        if master_idx < len(self.masters):
            return (self.masters[master_idx], f'{local_id:06X}')
        elif master_idx == len(self.masters):
            return (self.filename, f'{local_id:06X}')
        else:
            return (f'UNKNOWN_MASTER_{master_idx:02X}', f'{local_id:06X}')

    def resolve_formid_str(self, form_id):
        """Human-readable FormID resolution."""
        master, local = self.resolve_formid(form_id)
        return f'{master}|{local}'

    def get_keyword_name(self, form_id):
        """Try to resolve a keyword FormID to a name."""
        # Check if it's in our parsed records
        if form_id in self.records_by_formid:
            rec = self.records_by_formid[form_id]
            if rec.editor_id:
                return rec.editor_id

        # Check vanilla keyword lookup
        if form_id in VANILLA_WEAPON_KEYWORDS:
            return VANILLA_WEAPON_KEYWORDS[form_id]

        # Return the resolved FormID string
        return self.resolve_formid_str(form_id)

    def get_summary(self):
        """Return a summary of the parsed file."""
        lines = []
        lines.append(f'{"="*60}')
        lines.append(f'ESP Parser Summary: {self.filename}')
        lines.append(f'{"="*60}')
        lines.append(f'File type: {"ESM" if self.is_esm else "ESL" if self.is_esl else "ESP"}')
        lines.append(f'Version: {self.version}')
        lines.append(f'Localized: {self.is_localized}')
        lines.append(f'Author: {self.author}')
        lines.append(f'Description: {self.description[:100]}...' if len(self.description) > 100 else f'Description: {self.description}')
        lines.append(f'')
        lines.append(f'Masters ({len(self.masters)}):')
        for i, m in enumerate(self.masters):
            lines.append(f'  [{i:02X}] {m}')
        lines.append(f'  [{len(self.masters):02X}] {self.filename} (this file)')
        lines.append(f'')
        lines.append(f'Record Statistics:')
        lines.append(f'  Total groups: {self.group_count}')
        lines.append(f'  Total records: {self.record_count}')
        lines.append(f'  Compressed records: {self.compressed_count}')
        lines.append(f'')
        lines.append(f'Records by type:')
        for rtype, count in sorted(self.type_counts.items(), key=lambda x: -x[1]):
            lines.append(f'  {rtype}: {count}')

        return '\n'.join(lines)


# ============================================================================
# WEAPON ANALYSIS
# ============================================================================

def parse_weap_dnam(data):
    """Parse WEAP DNAM subrecord for weapon stats."""
    result = {}
    if len(data) >= 4:
        result['animation_type'] = struct.unpack('<I', data[0:4])[0]
    if len(data) >= 8:
        result['speed'] = struct.unpack('<f', data[4:8])[0]
    if len(data) >= 12:
        result['reach'] = struct.unpack('<f', data[8:12])[0]
    if len(data) >= 16:
        result['flags'] = struct.unpack('<H', data[12:14])[0]
    if len(data) >= 28:
        result['sight_fov'] = struct.unpack('<f', data[16:20])[0]
    if len(data) >= 36:
        result['vats_hit_chance'] = struct.unpack('<f', data[24:28])[0]
    if len(data) >= 48:
        result['min_range'] = struct.unpack('<f', data[36:40])[0]
    if len(data) >= 52:
        result['max_range'] = struct.unpack('<f', data[40:44])[0]
    if len(data) >= 60:
        result['stagger'] = struct.unpack('<f', data[56:60])[0]
    return result


def parse_weap_data(data):
    """Parse WEAP DATA subrecord for value/weight."""
    result = {}
    if len(data) >= 4:
        result['value'] = struct.unpack('<i', data[0:4])[0]
    if len(data) >= 8:
        result['weight'] = struct.unpack('<f', data[4:8])[0]
    return result


def analyze_weapons(parser):
    """Analyze all weapon records and return structured data."""
    weapons = []

    for rec in parser.records.get('WEAP', []):
        weapon = {
            'form_id': rec.form_id_hex,
            'form_id_resolved': parser.resolve_formid_str(rec.form_id),
            'editor_id': rec.editor_id,
            'full_name': rec.full_name,
            'master_index': rec.master_index,
            'is_override': rec.master_index < len(parser.masters),
            'overrides_master': parser.masters[rec.master_index] if rec.master_index < len(parser.masters) else parser.filename,
            'keywords': [parser.get_keyword_name(kw) for kw in rec.keywords],
            'keyword_formids': [f'{kw:08X}' for kw in rec.keywords],
            'flags': f'{rec.flags:08X}',
        }

        # Parse DNAM if present
        if 'DNAM' in rec.raw_data:
            dnam = rec.raw_data['DNAM']
            if isinstance(dnam, list):
                dnam = dnam[0]
            weapon['dnam'] = parse_weap_dnam(dnam)

        # Parse DATA if present
        if 'DATA' in rec.raw_data:
            data_sub = rec.raw_data['DATA']
            if isinstance(data_sub, list):
                data_sub = data_sub[0]
            weapon['data'] = parse_weap_data(data_sub)

        # Check for instance naming (INRD)
        if 'INRD' in rec.raw_data:
            inrd = rec.raw_data['INRD']
            if isinstance(inrd, list):
                inrd = inrd[0]
            if len(inrd) >= 4:
                weapon['instance_naming'] = parser.resolve_formid_str(
                    struct.unpack('<I', inrd[0:4])[0]
                )

        # Check for template (CNAM on WEAP = template weapon)
        if 'CNAM' in rec.raw_data:
            cnam = rec.raw_data['CNAM']
            if isinstance(cnam, list):
                cnam = cnam[0]
            if len(cnam) >= 4:
                weapon['template'] = parser.resolve_formid_str(
                    struct.unpack('<I', cnam[0:4])[0]
                )

        weapons.append(weapon)

    return weapons


# ============================================================================
# AMMO ANALYSIS
# ============================================================================

def parse_ammo_data(data):
    """Parse AMMO DATA subrecord."""
    result = {}
    if len(data) >= 4:
        result['projectile'] = f'{struct.unpack("<I", data[0:4])[0]:08X}'
    if len(data) >= 8:
        result['flags'] = struct.unpack('<I', data[4:8])[0]
    if len(data) >= 12:
        result['damage'] = struct.unpack('<f', data[8:12])[0]
    if len(data) >= 16:
        result['value'] = struct.unpack('<i', data[12:16])[0]
    if len(data) >= 20:
        result['weight'] = struct.unpack('<f', data[16:20])[0]
    return result


def analyze_ammo(parser):
    """Analyze all ammo records."""
    ammo_list = []

    for rec in parser.records.get('AMMO', []):
        ammo = {
            'form_id': rec.form_id_hex,
            'form_id_resolved': parser.resolve_formid_str(rec.form_id),
            'editor_id': rec.editor_id,
            'full_name': rec.full_name,
            'master_index': rec.master_index,
            'is_override': rec.master_index < len(parser.masters),
            'overrides_master': parser.masters[rec.master_index] if rec.master_index < len(parser.masters) else parser.filename,
            'keywords': [parser.get_keyword_name(kw) for kw in rec.keywords],
            'keyword_formids': [f'{kw:08X}' for kw in rec.keywords],
        }

        if 'DATA' in rec.raw_data:
            data_sub = rec.raw_data['DATA']
            if isinstance(data_sub, list):
                data_sub = data_sub[0]
            ammo['data'] = parse_ammo_data(data_sub)

        ammo_list.append(ammo)

    return ammo_list


# ============================================================================
# ARMOR ANALYSIS
# ============================================================================

def analyze_armor(parser):
    """Analyze all armor records."""
    armor_list = []

    for rec in parser.records.get('ARMO', []):
        armor = {
            'form_id': rec.form_id_hex,
            'form_id_resolved': parser.resolve_formid_str(rec.form_id),
            'editor_id': rec.editor_id,
            'full_name': rec.full_name,
            'master_index': rec.master_index,
            'is_override': rec.master_index < len(parser.masters),
            'overrides_master': parser.masters[rec.master_index] if rec.master_index < len(parser.masters) else parser.filename,
            'keywords': [parser.get_keyword_name(kw) for kw in rec.keywords],
            'keyword_formids': [f'{kw:08X}' for kw in rec.keywords],
        }

        # Parse DNAM for armor rating
        if 'DNAM' in rec.raw_data:
            dnam = rec.raw_data['DNAM']
            if isinstance(dnam, list):
                dnam = dnam[0]
            if len(dnam) >= 4:
                armor['armor_rating'] = struct.unpack('<f', dnam[0:4])[0]

        # Parse DATA for value/weight
        if 'DATA' in rec.raw_data:
            data_sub = rec.raw_data['DATA']
            if isinstance(data_sub, list):
                data_sub = data_sub[0]
            if len(data_sub) >= 4:
                armor['value'] = struct.unpack('<i', data_sub[0:4])[0]
            if len(data_sub) >= 8:
                armor['weight'] = struct.unpack('<f', data_sub[4:8])[0]

        armor_list.append(armor)

    return armor_list


# ============================================================================
# KEYWORD ANALYSIS
# ============================================================================

def analyze_keywords(parser):
    """Analyze all keyword records."""
    keywords = []

    for rec in parser.records.get('KYWD', []):
        kw = {
            'form_id': rec.form_id_hex,
            'form_id_resolved': parser.resolve_formid_str(rec.form_id),
            'editor_id': rec.editor_id,
            'master_index': rec.master_index,
            'is_new': rec.master_index == len(parser.masters),
            'source': parser.masters[rec.master_index] if rec.master_index < len(parser.masters) else parser.filename,
        }
        keywords.append(kw)

    return keywords


# ============================================================================
# PERK ANALYSIS
# ============================================================================

def analyze_perks(parser):
    """Analyze all perk records."""
    perks = []

    for rec in parser.records.get('PERK', []):
        perk = {
            'form_id': rec.form_id_hex,
            'form_id_resolved': parser.resolve_formid_str(rec.form_id),
            'editor_id': rec.editor_id,
            'full_name': rec.full_name,
            'master_index': rec.master_index,
            'is_override': rec.master_index < len(parser.masters),
            'overrides_master': parser.masters[rec.master_index] if rec.master_index < len(parser.masters) else parser.filename,
        }

        # Parse DATA for perk info
        if 'DATA' in rec.raw_data:
            data_sub = rec.raw_data['DATA']
            if isinstance(data_sub, list):
                data_sub = data_sub[0]
            if len(data_sub) >= 5:
                perk['is_trait'] = data_sub[0]
                perk['level'] = data_sub[1]
                perk['num_ranks'] = data_sub[2]
                perk['playable'] = data_sub[3]
                perk['hidden'] = data_sub[4]

        perks.append(perk)

    return perks


# ============================================================================
# OVERRIDE / PATCH ANALYSIS
# ============================================================================

def analyze_overrides(parser):
    """
    Analyze which records in this plugin are overrides of other masters.
    This is KEY for understanding what a patch ESP is doing.
    """
    overrides = defaultdict(list)
    new_records = defaultdict(list)

    for rec_type, records in parser.records.items():
        for rec in records:
            if rec.master_index < len(parser.masters):
                # This is an override - the record originates from a master
                master = parser.masters[rec.master_index]
                overrides[master].append({
                    'type': rec.type,
                    'form_id': rec.form_id_hex,
                    'editor_id': rec.editor_id,
                    'full_name': rec.full_name,
                    'keywords': [parser.get_keyword_name(kw) for kw in rec.keywords],
                })
            else:
                # This is a new record defined in this plugin
                new_records[rec.type].append({
                    'form_id': rec.form_id_hex,
                    'editor_id': rec.editor_id,
                    'full_name': rec.full_name,
                    'keywords': [parser.get_keyword_name(kw) for kw in rec.keywords],
                })

    return overrides, new_records


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_to_csv(data, filepath, fieldnames=None):
    """Export a list of dicts to CSV."""
    if not data:
        print(f'No data to export to {filepath}')
        return

    if fieldnames is None:
        # Collect all keys from all records
        all_keys = OrderedDict()
        for item in data:
            for key in item.keys():
                all_keys[key] = True
        fieldnames = list(all_keys.keys())

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for item in data:
            # Flatten complex fields
            flat = {}
            for k, v in item.items():
                if isinstance(v, list):
                    flat[k] = ' | '.join(str(x) for x in v)
                elif isinstance(v, dict):
                    flat[k] = json.dumps(v)
                else:
                    flat[k] = v
            writer.writerow(flat)

    print(f'Exported {len(data)} records to {filepath}')


def export_full_dump(parser, output_dir):
    """Export everything to a set of CSV files in a directory."""
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(parser.filename)[0]

    # Summary
    summary_path = os.path.join(output_dir, f'{base}_summary.txt')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(parser.get_summary())
    print(f'Summary written to {summary_path}')

    # Keywords
    if parser.records.get('KYWD'):
        kw_data = analyze_keywords(parser)
        export_to_csv(kw_data, os.path.join(output_dir, f'{base}_keywords.csv'))

    # Weapons
    if parser.records.get('WEAP'):
        weap_data = analyze_weapons(parser)
        export_to_csv(weap_data, os.path.join(output_dir, f'{base}_weapons.csv'))

    # Ammo
    if parser.records.get('AMMO'):
        ammo_data = analyze_ammo(parser)
        export_to_csv(ammo_data, os.path.join(output_dir, f'{base}_ammo.csv'))

    # Armor
    if parser.records.get('ARMO'):
        armor_data = analyze_armor(parser)
        export_to_csv(armor_data, os.path.join(output_dir, f'{base}_armor.csv'))

    # Perks
    if parser.records.get('PERK'):
        perk_data = analyze_perks(parser)
        export_to_csv(perk_data, os.path.join(output_dir, f'{base}_perks.csv'))

    # Override analysis
    overrides, new_records = analyze_overrides(parser)

    override_path = os.path.join(output_dir, f'{base}_overrides.txt')
    with open(override_path, 'w', encoding='utf-8') as f:
        f.write(f'Override Analysis: {parser.filename}\n')
        f.write(f'{"="*60}\n\n')

        for master, records in sorted(overrides.items()):
            f.write(f'\nOverrides from {master} ({len(records)} records):\n')
            f.write(f'{"-"*50}\n')
            for rec in records:
                f.write(f'  [{rec["type"]}] {rec["form_id"]} | {rec["editor_id"]}\n')
                if rec['full_name']:
                    f.write(f'    Name: {rec["full_name"]}\n')
                if rec['keywords']:
                    f.write(f'    Keywords: {", ".join(rec["keywords"])}\n')

        f.write(f'\n\nNew Records in {parser.filename}:\n')
        f.write(f'{"="*60}\n')
        for rec_type, records in sorted(new_records.items()):
            f.write(f'\n  {rec_type} ({len(records)} new records):\n')
            for rec in records:
                f.write(f'    {rec["form_id"]} | {rec["editor_id"]}\n')
                if rec['full_name']:
                    f.write(f'      Name: {rec["full_name"]}\n')
                if rec['keywords']:
                    f.write(f'      Keywords: {", ".join(rec["keywords"])}\n')

    print(f'Override analysis written to {override_path}')

    # All records flat dump
    all_records = []
    for rec_type, records in parser.records.items():
        for rec in records:
            all_records.append({
                'type': rec.type,
                'form_id': rec.form_id_hex,
                'form_id_resolved': parser.resolve_formid_str(rec.form_id),
                'editor_id': rec.editor_id,
                'full_name': rec.full_name,
                'is_override': rec.master_index < len(parser.masters),
                'source_master': parser.masters[rec.master_index] if rec.master_index < len(parser.masters) else parser.filename,
                'keywords': ' | '.join(parser.get_keyword_name(kw) for kw in rec.keywords),
                'flags': f'{rec.flags:08X}',
                'compressed': rec.is_compressed,
                'subrecord_count': len(rec.subrecords),
            })

    export_to_csv(all_records, os.path.join(output_dir, f'{base}_all_records.csv'))


# ============================================================================
# BATCH PROCESSING - Scan multiple ESPs
# ============================================================================

def batch_scan_directory(directory, output_dir, filter_types=None):
    """Scan all ESP/ESM/ESL files in a directory tree."""
    os.makedirs(output_dir, exist_ok=True)

    results = []
    for root, dirs, files in os.walk(directory):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in ('.esp', '.esm', '.esl'):
                filepath = os.path.join(root, fname)
                try:
                    parser = ESPParser(filepath)
                    parser.parse(filter_types=filter_types)
                    results.append({
                        'file': fname,
                        'path': filepath,
                        'masters': ', '.join(parser.masters),
                        'master_count': len(parser.masters),
                        'record_count': parser.record_count,
                        'types': ', '.join(f'{k}:{v}' for k, v in sorted(parser.type_counts.items())),
                        'is_esm': parser.is_esm,
                        'is_esl': parser.is_esl,
                    })
                    print(f'  Scanned: {fname} ({parser.record_count} records)')
                except Exception as e:
                    print(f'  ERROR scanning {fname}: {e}')
                    results.append({
                        'file': fname,
                        'path': filepath,
                        'error': str(e),
                    })

    export_to_csv(results, os.path.join(output_dir, 'batch_scan_results.csv'))
    return results


# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    argparser = argparse.ArgumentParser(
        description='Fallout 4 ESP/ESM/ESL Binary Parser - No masters required!',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Parse a single ESP and dump everything:
    python fo4_esp_parser.py "MAIM.esp" --dump output_folder

  Extract just weapons to CSV:
    python fo4_esp_parser.py "MAIM.esp" --type WEAP --csv weapons.csv

  Extract keywords:
    python fo4_esp_parser.py "AnomalyPatching.esp" --type KYWD --csv keywords.csv

  Show file summary only:
    python fo4_esp_parser.py "Fallout Anomaly Overwrites.esp" --summary

  Batch scan a directory:
    python fo4_esp_parser.py --batch "C:\\Modlists\\mods" --dump output_folder

  Parse specific types:
    python fo4_esp_parser.py "MAIM.esp" --type WEAP AMMO KYWD ARMO --dump output
        """
    )

    argparser.add_argument('file', nargs='?', help='Path to ESP/ESM/ESL file')
    argparser.add_argument('--type', nargs='+', help='Record types to parse (e.g., WEAP AMMO KYWD)')
    argparser.add_argument('--csv', help='Export to CSV file')
    argparser.add_argument('--dump', help='Full dump to output directory')
    argparser.add_argument('--summary', action='store_true', help='Show file summary only')
    argparser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    argparser.add_argument('--batch', help='Batch scan directory for all ESPs')
    argparser.add_argument('--json', help='Export to JSON file')

    args = argparser.parse_args()

    if args.batch:
        filter_types = set(args.type) if args.type else None
        output_dir = args.dump or 'batch_output'
        batch_scan_directory(args.batch, output_dir, filter_types)
        return

    if not args.file:
        argparser.print_help()
        return

    if not os.path.exists(args.file):
        print(f'Error: File not found: {args.file}')
        sys.exit(1)

    # Parse the file
    filter_types = set(args.type) if args.type else None

    # Always include KYWD if we're parsing weapons/ammo/armor (for keyword resolution)
    if filter_types and filter_types & {'WEAP', 'AMMO', 'ARMO', 'NPC_', 'PERK'}:
        filter_types.add('KYWD')

    parser = ESPParser(args.file, verbose=args.verbose)
    parser.parse(filter_types=filter_types)

    # Summary mode
    if args.summary:
        print(parser.get_summary())
        return

    # Full dump mode
    if args.dump:
        export_full_dump(parser, args.dump)
        return

    # CSV export for specific type
    if args.csv and args.type:
        all_data = []
        for rtype in args.type:
            if rtype == 'WEAP':
                all_data.extend(analyze_weapons(parser))
            elif rtype == 'AMMO':
                all_data.extend(analyze_ammo(parser))
            elif rtype == 'ARMO':
                all_data.extend(analyze_armor(parser))
            elif rtype == 'KYWD':
                all_data.extend(analyze_keywords(parser))
            elif rtype == 'PERK':
                all_data.extend(analyze_perks(parser))
            else:
                # Generic dump for other types
                for rec in parser.records.get(rtype, []):
                    all_data.append({
                        'type': rec.type,
                        'form_id': rec.form_id_hex,
                        'form_id_resolved': parser.resolve_formid_str(rec.form_id),
                        'editor_id': rec.editor_id,
                        'full_name': rec.full_name,
                        'keywords': ' | '.join(parser.get_keyword_name(kw) for kw in rec.keywords),
                    })

        export_to_csv(all_data, args.csv)
        return

    # JSON export
    if args.json:
        output = {
            'file': parser.filename,
            'masters': parser.masters,
            'is_esm': parser.is_esm,
            'is_esl': parser.is_esl,
            'records': {}
        }

        for rtype in (args.type or parser.records.keys()):
            if rtype == 'WEAP':
                output['records']['WEAP'] = analyze_weapons(parser)
            elif rtype == 'AMMO':
                output['records']['AMMO'] = analyze_ammo(parser)
            elif rtype == 'ARMO':
                output['records']['ARMO'] = analyze_armor(parser)
            elif rtype == 'KYWD':
                output['records']['KYWD'] = analyze_keywords(parser)
            elif rtype == 'PERK':
                output['records']['PERK'] = analyze_perks(parser)

        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, default=str)
        print(f'Exported to {args.json}')
        return

    # Default: print summary
    print(parser.get_summary())


if __name__ == '__main__':
    main()
