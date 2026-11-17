# Theme: palette, spacing, composition and icons

`theme.bin` is a JSON (u32 length + compact JSON) with three parts, all
optional except for some palette:

```json
{
  "accent": "#008000", "...18 tokens...": "...",
  "spacing": { "details.block_gap": 16 },
  "layout":  { "startup": "home", "tabs": ["..."], "home": { "..." : "..." },
               "library": { "..." : "..." }, "discover": { "..." : "..." },
               "details": { "..." : "..." } }
}
```

Anything the document omits **falls back to the builtin look**: a theme can
be palette only. The builtin light theme is "Default"; the dark one is
**Default-Dark**; both ship with the app.

## Folder layout

```
my-theme/
  manifest.json      {"type": "theme", "id": "my-theme", ...}
  theme.json
  icons/<sprite>.png optional overrides (names in tools.md)
  assets/            optional; icon.png is the manager row icon
```

```sh
python3 tools/necroext.py build my-theme -o dist/
```

`icons/` and `assets/` are different contracts: `icons/<sprite>.png` is read
by the app for its icon set and the file name **is** the interface;
`assets/**` is copied verbatim for the extension itself (only `icon.png`
means anything to the app).

## Palette (the 18 tokens)

| token | use |
|-------|-----|
| `accent` | primary buttons, section titles, filled stars |
| `title` | main text |
| `content` | secondary text |
| `read` | rows already read |
| `white` | **the app background** |
| `black` | pure black |
| `soft` | text over the accent / switches |
| `bar_bg` | bottom tab bar |
| `tabs_bg` | the tab strip background |
| `top_bar` | reader and details bars |
| `card` | search box, follow button |
| `filled` | solid secondary buttons |
| `border` | button borders and outlines |
| `hairline` | thin separator lines |
| `divider` | separators |
| `placeholder` | ghost cover before loading |
| `link` | links inside comments |
| `dim` | switches off |

Format `#RRGGBB` or `#AARRGGBB`. In a dark theme, `white` **is the
background** (black) — the neutral light on top lives in `soft`.

## `spacing` (integer dp)

`details.block_gap`, `details.button_gap`, `details.desc_gap`,
`details.rec_gap`, `search.button_gap`. Crazy or unknown values fall back to
the builtin ones; the measurements of the pieces are **not** the theme's,
only the gaps between them are.

## `layout`

### The tab board (2–5 slots)

```json
"startup": "home",
"tabs": [ {"panel": "library"}, {"panel": "home"},
          {"panel": "discover"}, {"panel": "yo"} ]
```

- `panel`: `home` | `library` | `discover` | `yo` | `extensions`. Duplicates
  are dropped. **None is required** (build any board you want); if the theme
  forgets `yo`, it rides along at the end, because the extensions manager
  must stay reachable.
- `label`: optional L10n key for the text (without it, the panel's own key
  is used).
- `startup`: the opening panel; without it the **first slot** opens.

The `yo` panel is the **You** tab (`tab.settings` in the language pack); the
extensions manager is reached from there.

### The Home by slots

```json
"home": { "order": [
    {"id": "home.latest",  "layout": "grid_3"},
    {"id": "home.original", "layout": "carousel_big", "loop": true}
] }
```

- Each entry = **content + its own carousel**; repeats are valid (the same
  section twice, in different shapes).
- `id`: the provider section variable (`home.<id>`). Unknown id: that entry
  drops, the rest live.
- `layout`: `carousel_big` | `featured` | `grid_3` | `grid_2` (shortcuts:
  `carousel`, `grid`, `grid2`, `grid3`). Without `layout`, the provider's
  declared one wins. **`featured` loops by default**; only an explicit
  `"loop": false` turns it off. Loop is the theme's word: the provider never
  decides it.

### The list screens

```json
"library":  { "order": ["search", "tabs", "list"], "list": "list" },
"discover": { "order": ["search", "tabs", "list"] }
```

- `order`: the component stack, in any order (`search`, `tabs`, `list` —
  the content list is always last). The builtin "My manga" screen is
  `["tabs", "list", "search"]` (search at the bottom).
- `list` (library only): `"list"` (its own design) or `"catalog"` (reuses
  the Discover row).

### Details

```json
"details": {
  "flow": ["buttons", "tabs"],
  "tabs": { "detail": ["header", "description", "recs"],
            "chapter": [], "comment": [] }
}
```

- `flow`: the fixed blocks, in order. Tokens: `header`, `buttons`, `tabs`
  (the strip; one only).
- `tabs.<page>`: the free blocks of each tab, in order. Tokens: `header`,
  `buttons`, `description`, `recs`. Each free block sits **exactly once**
  across the flow and the tabs; any invalid scheme drops the whole theme to
  the builtin look.

## Icons (`icons/<name>.png`)

One PNG per icon, named as the sprite (full table in
[`tools.md`](tools.md)). Any size works: the app scales to each site's
request. **Tint** is applied just like to the builtin art:

- tint ≠ 0: replaces the colors and keeps the shape's **alpha**. If the PNG
  is a white disc with a glyph, the white is dropped first (the "disc" rule)
  so the tint looks native; a bare glyph takes the tint whole.
- tint = 0: the PNG paints its own colors.

That gives two styles: **art that inherits the theme color** (grey/alpha
silhouette, tinted with the accent) or **fixed-color art** (the PNG brings
its palette; tinting sites receive tint 0 so the art owns its colors — e.g.
the stars).
