# The `.necroext` container

A `.necroext` is a **plain zip** (the installer opens it as-is) with two
kinds of members:

1. `manifest.bin` — required; identifies the extension.
2. The payload of its type: whatever that type needs (see each type page).

## `manifest.bin`

Small binary, byte-exact with the installer's parser:

```
"NECR"                              magic (4 bytes)
u32 version (1,0,0)                 4 bytes: 01 00 00 00
u32 payloadSize                     little-endian
u32 crc32(payload)
payload:
    u8len  type                     "provider" | "theme" | "lang" | "bundle"
    u8len  id                       [A-Za-z0-9._-]{1,64}, no leading dot
    u16len name                     visible name
    u16len version                  free text ("1.0.0")
    u16len author
    u8     langCount
    (u8len code)*                   language codes (type "lang" only)
```

Strings are UTF-8; `u8len` is 1 length byte + bytes; `u16len` is a 2-byte
little-endian length + bytes.

Do not write a manifest by hand: **`tools/extpack.py` generates and validates
it** (`manifest_bin()`, `parse_manifest()`), and `tools/necroext.py` drives
it.

## Installer rules (what gets rejected)

- `manifest.bin` missing, or bad magic/version/CRC → rejected.
- Invalid `id` (empty, >64, characters outside the set) → rejected.
- **Size limits**: 1 MB per JSON payload (`behaviors.bin`, `theme.bin`,
  language `.bin`), 4 MB per file, 8 MB per extension. The packer checks all
  three before writing, so a pack the phone would refuse fails on your
  machine instead.
- No symlinks and no unsafe member names (`../`, absolute paths).
- Type `lang`: every language declared in the manifest **must** have its
  `<code>.bin` in the container, and no extra `.bin`.
- Type `theme`: requires `theme.bin`; optional PNGs live in `icons/`.
- Type `provider`: requires `behaviors.bin`.
- Type `bundle`: not installed as such — the installer opens the zip and
  installs each inner `.necroext` as an independent extension.

## Members the packer adds for you

- `assets/**` — copied verbatim from the folder, recursively. The app only
  reads `assets/icon.png` (the extension manager row); anything else is for
  the extension itself.
- `icons/<sprite>.png` — theme icon overrides; the file name **is** the
  interface (see [`theme.md`](theme.md)).

## What each type is

| Type | What it is for | Payload |
|------|----------------|---------|
| `provider` | a content source (API/scraper) | `behaviors.bin` |
| `theme` | palette, spacing, composition, icons | `theme.bin` + `icons/` |
| `lang` | interface translations | `<code>.bin` per language |
| `bundle` | distributing several packs in one file | other `.necroext` |

The first three install as independent extensions; a bundle is only a
distribution envelope.

## Reproducible output

The packer writes members in sorted order with a fixed timestamp
(`1980-01-01`). `unpack` followed by `build` gives back **identical bytes**,
so packs can be diffed and cached by hash.
