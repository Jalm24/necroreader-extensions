# NecroReader — extension API and tools (made with ai)

Documentation and tooling for building [NecroReader](https://jalm24.itch.io/necro-reader)
extensions: the native (C++/Android) manga reader where **content and looks
live in extensions**, not in the app.

The base app ships no third-party providers or themes: it is a shell with a
ghost provider (a Home of placeholders, no network). Everything else arrives
as a `.necroext`.

## The four extension types

| Type | What it is for | Document |
|------|----------------|----------|
| **provider** | a content source (API, declarative scraper) | [`docs/provider.md`](docs/provider.md) |
| **theme** | palette, spacing, composition, icons | [`docs/theme.md`](docs/theme.md) |
| **lang** | interface translations, and the language a multilingual provider uses | [`docs/lang.md`](docs/lang.md) |
| **bundle** | several extensions in one file | [`docs/bundle.md`](docs/bundle.md) |

The container format (`.necroext` = zip + `manifest.bin`) is described in
[`docs/container-format.md`](docs/container-format.md).

## Quick start

One tool, one input: a **folder** with a `manifest.json`. The type lives in
the manifest, so there is nothing to remember per type.

```sh
# build any of the examples (each is a folder)
python3 tools/necroext.py build examples/provider-example -o dist/
python3 tools/necroext.py build examples/theme-example    -o dist/
python3 tools/necroext.py build examples/lang-example     -o dist/

# look inside a pack, or turn one back into an editable folder
python3 tools/necroext.py inspect dist/example-provider.necroext
python3 tools/necroext.py unpack dist/example-provider.necroext /tmp/my-provider
```

A minimal extension folder:

```
my-ext/
  manifest.json          identity: type, id, name, version, author
  assets/                optional; icon.png and anything the extension needs
  behaviors.json         type "provider"
  theme.json             type "theme"       (+ icons/<sprite>.png)
  lang/<code>.json       type "lang"        (one per declared language)
  *.necroext             type "bundle"      (inner packs)
```

`assets/` is optional but always checked: if it — or `assets/icon.png` — is
missing, the build still succeeds and prints a warning, because the extension
manager row falls back to the builtin icon. Everything inside `assets/` is
copied into the pack verbatim, recursively; only `icon.png` has a meaning to
the app today.

Every tool and every message in this repo is in English. Details:
[`docs/tools.md`](docs/tools.md).

## Important information

1. **Providers send variables, never interface text.** Home headers and
   action buttons are painted by the app with the active language pack; the
   packer strips whatever UI text it receives.
2. **Themes own the look**: palette, spacing, per-screen composition and
   icons. Whatever a theme does not specify falls back to the default
   theme.
3. **Nothing breaks by omission**: everything a pack does not declare falls
   back to the builtin look. A palette-only theme is valid; so is a provider
   without a shelf.
4. **The base app knows no APIs**: the builtin provider answers everything
   with empty data (the placeholder Home). Installing a real provider
   replaces that void once it is activated.

## License

MIT — see [`LICENSE`](LICENSE).
