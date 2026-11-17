#!/usr/bin/env python3
"""Shared base of necroext.py: manifest.bin writer, container builder and
container validator. One CLI (necroext.py) drives every extension type.

The manifest layout is the one NecroReader's installer reads today:
    "NECR" | u32 version (1,0,0) | u32 payloadSize | u32 crc32(payload)
    payload: u8len type | u8len id | u16len name | u16len version |
             u16len author | u8 langCount | (u8len code)*
"""
import re
import struct
import sys
import zipfile
import zlib

MAGIC = b"NECR"
VALID_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def valid_id(value):
    return bool(VALID_ID.match(value)) and not value.startswith(".")


def manifest_bin(ext_type, ext_id, name, version, author, languages):
    """One manifest.bin, byte-exact with the installer's parser."""
    def u8(value):
        return bytes([len(value)]) + value.encode("utf-8")

    def u16(value):
        raw = value.encode("utf-8")
        return struct.pack("<H", len(raw)) + raw

    payload = (u8(ext_type) + u8(ext_id) + u16(name) + u16(version)
               + u16(author) + bytes([len(languages)]))
    for code in languages:
        payload += u8(code)
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    return MAGIC + bytes([1, 0, 0, 0]) + struct.pack("<I", len(payload)) + \
        struct.pack("<I", crc) + payload


def sized_json(table_json):
    """The u32 + JSON shape behaviors.bin and the language tables share."""
    raw = table_json.encode("utf-8")
    return struct.pack("<I", len(raw)) + raw


def fail(message):
    print("FAIL: %s" % message)
    sys.exit(1)


def build_container(out_path, entries):
    """Writes the .necroext (a plain zip; miniz opens it as-is)."""
    # Sorted names and a fixed timestamp make the bytes reproducible:
    # unpack -> build gives the same file back.
    entries = sorted(entries, key=lambda entry: entry[0])
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries:
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            zf.writestr(info, data)


def parse_manifest(manifest_bytes):
    """Reads a manifest.bin the same way as the C++ parser; raises on any
    shortcut the installer would refuse."""
    if manifest_bytes[:4] != MAGIC:
        fail("manifest.bin: bad magic")
    version = manifest_bytes[4:8]
    if version != bytes([1, 0, 0, 0]):
        fail("manifest.bin: unsupported version")
    size = struct.unpack("<I", manifest_bytes[8:12])[0]
    crc = struct.unpack("<I", manifest_bytes[12:16])[0]
    payload = manifest_bytes[16:]
    if len(payload) != size or zlib.crc32(payload) & 0xFFFFFFFF != crc:
        fail("manifest.bin: size or CRC mismatch")

    def read8(index):
        if index + 1 > len(payload):
            fail("manifest.bin: truncated")
        length = payload[index]
        end = index + 1 + length
        text = payload[index + 1:end].decode("utf-8")
        return text, end

    def read16(index):
        if index + 2 > len(payload):
            fail("manifest.bin: truncated")
        length = struct.unpack("<H", payload[index:index + 2])[0]
        end = index + 2 + length
        text = payload[index + 2:end].decode("utf-8")
        return text, end

    ext_type, index = read8(0)
    ext_id, index = read8(index)
    name, index = read16(index)
    version, index = read16(index)
    author, index = read16(index)
    if not valid_id(ext_id):
        fail("invalid extension id: %r" % ext_id)
    if index >= len(payload):
        fail("manifest.bin: truncated at the languages")
    count = payload[index]
    index += 1
    codes = []
    for _ in range(count):
        code, index = read8(index)
        if index > len(payload):
            fail("manifest.bin: truncated inside a code")
        if not valid_id(code):
            fail("invalid language code: %r" % code)
        codes.append(code)
    return {
        "type": ext_type,
        "id": ext_id,
        "name": name,
        "version": version,
        "author": author,
        "languages": codes,
    }


def read_container(out_path):
    """Opens a built container and returns its manifest + member names."""
    try:
        with zipfile.ZipFile(out_path) as zf:
            names = zf.namelist()
            raw = zf.read("manifest.bin")
    except (OSError, KeyError) as error:
        fail("could not re-read the container: %s" % error)
    return parse_manifest(raw), names
