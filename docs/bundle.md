# Bundle: several packs in one file

A `bundle` (`type: "bundle"`) is a **distribution** envelope: a zip
(`.necroext`) carrying other `.necroext` files. The installer opens the
envelope and installs each inner pack as an **independent extension** (with
its own manifest, id and type); the bundle itself is never stored.

## Folder layout

```
my-bundle/
  manifest.json      {"type": "bundle", "id": "my-bundle", ...}
  theme.necroext
  lang.necroext
```

```sh
python3 tools/necroext.py build my-bundle -o dist/
```

Every `*.necroext` in the folder is embedded. A bundle never carries
`assets/` (it never installs, so there is no manager row to give an icon)
and it is not checked for one.

Typical uses:

- Shipping **theme + language** together (they go hand in hand: the looks and
  the words).
- Handing out a family of themes.

Rules:

- Inner packs keep their manifest: each installs and updates by its own id.
- The bundle has its own `manifest.bin` (type `bundle`), but the installer
  only uses it to show the envelope; staging is the inner packs' business.
- Nested bundles are refused. If one inner pack fails validation, the rest
  are installed and the error names the failing one.
