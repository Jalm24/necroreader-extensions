# Tools

Everything lives in `tools/` (Python 3, standard library only). There is
**one** packer, `necroext.py`; `extpack.py` is its library and `sweep_l10n.py`
only inspects the app.

## `necroext.py` — the packer

```sh
python3 tools/necroext.py build <folder> [-o <file-or-dir>]
python3 tools/necroext.py inspect <pack>
python3 tools/necroext.py unpack <pack> <folder>
```

| Command | Does |
|---------|------|
| `build` | folder → `<id>.necroext` (in `-o` when given, else the cwd) |
| `inspect` | prints the manifest and every member with its size |
| `unpack` | `.necroext` → editable folder (`manifest.json` + payload files) |

The input is a **folder**, not a pile of flags. The type is read from
`manifest.json`; if `type` is omitted, the contents decide (a
`behaviors.json` means provider, a `theme.json` theme, a `lang/` folder lang,
an inner `.necroext` bundle).

What `build` does, in order:

1. Validates the manifest: `id`, `type`, `languages`.
2. Converts the payload of that type and validates it (see below).
3. Copies `assets/**` verbatim, recursively.
4. Checks the installer's limits: 1 MB per JSON payload, 4 MB per file,
   8 MB total.
5. Writes the container, then **re-reads it** with the installer's parser
   and prints the members it found.

Per type:

- **provider** — `behaviors.json` is required. Section ids are validated and
  interface text is stripped (`title` from section specs, non-token
  `action`), because the app paints those from the language pack. Mapper
  keys named `title` are data and stay.
- **theme** — `theme.json` is required and must be a non-empty object. Every
  `icons/*.png` is added as `icons/<name>.png`; other files there are
  skipped with a warning.
- **lang** — one `lang/<code>.json` per code declared in `languages`; a
  file not declared, or a declared code with no file, fails the build.
- **bundle** — every `*.necroext` in the folder is embedded. Nested bundles
  are refused, and a bundle never carries `assets/` (it never installs).

### `assets/` and its warning

`assets/` is optional, but the packer always looks at it:

- no `assets/` folder →
  `WARN: no assets/ folder: the manager row will use the builtin icon`
- `assets/` without `icon.png` →
  `WARN: assets/icon.png is missing: the manager row will use the builtin icon`
- either way the build **succeeds**; warnings go to stderr, the summary to
  stdout.

Bundles are exempt: they are distribution only, so no icon and no warning.

### Exit status

`0` on success (warnings included), `1` with a `FAIL: <reason>` line on any
rejection.

## `extpack.py` — the library (no CLI)

- `manifest_bin(type, id, name, version, author, languages)`: a
  `manifest.bin` byte-exact with the installer's parser.
- `parse_manifest(bytes)`: reads it the way the C++ does and rejects any
  shortcut the installer would reject.
- `sized_json(text)`: the u32 + JSON envelope used by `behaviors.bin`,
  `theme.bin` and language tables.
- `build_container(path, entries)`: writes the reproducible zip (sorted
  members, fixed timestamp).
- `read_container(path)`: manifest + member names, used to verify a build.

## `sweep_l10n.py` — key inventory

```sh
python3 tools/sweep_l10n.py
```

Walks the reader's source tree and dumps every `L10n` key with its builtin
text: the starting point of any translation. It packs nothing, so it matches
neither `build_*.py` nor the packer's contract. It expects to be run inside
the NecroReader source tree (the app repo, next to this one).

## Installing and testing on a device

1. Copy the `.necroext` to the SD card (e.g. `/sdcard/Download/`).
2. In the app: **You → Manage extensions → [+]** and pick the file.
3. Themes are activated under **Themes** (radio; applied on restart),
   providers under **Providers**, languages on the **You** screen.

## Icon names (theme overrides)

These are the builtin sprites, by PNG file name. `rating_*` are 24 px at
origin, the rest 32 px; any PNG size works, the app scales. Drop the ones you
want to override into `icons/` of a theme, named exactly as below:

| | | | |
|---|---|---|---|
| `ic_add_light` | `ic_add_speed` | `ic_arrow_back_light` | `ic_auto_scroll` |
| `ic_auto_scroll_checked` | `ic_chapter_to_end` | `ic_chapter_to_reading` | `ic_chapter_to_top` |
| `ic_comment_white` | `ic_menu_download_white` | `ic_menu_more` | `ic_menu_sort_asc` |
| `ic_menu_sort_desc` | `ic_picture` | `ic_read_detail` | `ic_read_feedback` |
| `ic_read_ltor` | `ic_read_ltor_light` | `ic_read_next` | `ic_read_previous` |
| `ic_read_rtol` | `ic_read_rtol_light` | `ic_read_share` | `ic_read_tab_brightness` |
| `ic_read_tab_chapter` | `ic_read_tab_rotate` | `ic_read_tab_setting` | `ic_read_ttob` |
| `ic_read_ttob_light` | `ic_search` | `ic_sent` | `ic_sub_light` |
| `ic_sub_speed` | `ic_tab_bookshelf` | `ic_tab_discover` | `ic_tab_home` |
| `ic_tab_me` | `ic_web` | `rating_bright` | `rating_dark` |

Where they are used: `ic_read_*` and `ic_auto_scroll*` in the reader bars;
`ic_chapter_to_*` and `ic_menu_sort_*` in the chapter list; `rating_*` are the
rating stars (a theme with its own star art receives tint 0, so its colors
win).
