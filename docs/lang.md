# Lang: interface translations

Every visible text in the app goes through `L10n.t(key, fallback)` — language
is a matter of **keys**, not embedded strings. A language pack
(`type: "lang"`) carries **one `.bin` per language code**, named after the
code: `es.bin`, `en.bin`, …

## Folder layout

```
my-lang/
  manifest.json      {"type": "lang", "id": "my-lang", "languages": ["es"], ...}
  lang/es.json
  lang/en.json       one per declared code, no extras
  assets/            optional; icon.png is the manager row icon
```

```sh
python3 tools/necroext.py build my-lang -o dist/
```

Declared codes and files must match exactly: a declared code with no file
fails, and a file that is not declared fails too.

## Table format

Each `.bin` is a JSON (u32 length + compact JSON):

```json
{ "tab.home": "Inicio", "tabs.following": "SIGUIENDO", "...": "..." }
```

- Missing keys **break nothing**: the builtin text of that language answers
  (the fallback chain does). A pack may translate a subset.
- The app language and the active pack are chosen on the **You** screen; a
  pack may declare several languages (one entry per code).
- A provider receives the active code as `{{lang}}`, so a multilingual
  provider can pick its own language along with the interface.

## Getting the key list

`tools/sweep_l10n.py` walks the app's source and dumps the key inventory with
its builtin texts — the working base for a translation:

```sh
python3 tools/sweep_l10n.py
```

Translate the values you want and save the result as `<code>.json`; the
packer converts it.

## Golden rules

1. **Home headers are keys too**: `home.section.<id>` — the section text is
   painted by the language pack; the provider only sends the id. If your
   provider declares a section with no key, the reader shows the raw id
   (honest, debuggable).
2. Behavior variables never carry user-facing text.
3. Language packs and theme packs are separate extensions — a `bundle` can
   distribute them together.
