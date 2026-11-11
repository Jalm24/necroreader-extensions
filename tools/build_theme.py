#!/usr/bin/env python3
"""Packs a theme extension (.necroext, theme.bin + optional icons/).

    tools/build_theme.py --name "My Theme" theme.json \
        [--icons ./icons] -o mytheme.necroext

theme.json is the theme document: palette tokens at the top level
("#RRGGBB" or "#AARRGGBB"), the optional "spacing" object (dp values)
and the optional "layout" object (startup, tab board, home slots, list
stacks, details flow). Anything the document omits rides the builtin
look — a palette-only theme is a valid theme.

The icons folder carries one PNG per icon override, named after the
icon (e.g. ic_search.png, rating_bright.png). Any size works: the app
scales; the tint rule recolours unless the art asks otherwise.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extpack import (build_container, build_entries, common_args, fail,
                     read_container, sized_json)


def main():
    parser = common_args()
    parser.add_argument("theme", help="theme.json (paleta + spacing + layout)")
    parser.add_argument("--icons", default=None,
                        help="folder of PNG overrides (icons/<name>.png)")
    parser.add_argument("-o", "--output", required=True)
    parsed = parser.parse_args()

    try:
        with open(parsed.theme, "rb") as raw:
            doc = json.loads(raw.read().decode("utf-8"))
    except (OSError, ValueError) as error:
        fail("theme.json invalido: %s" % error)
    if not isinstance(doc, dict) or not doc:
        fail("theme.json debe ser un objeto con al menos un token")
    body = json.dumps(doc, separators=(",", ":"),
                      ensure_ascii=False, sort_keys=True)

    ext_id = parsed.id or (parsed.name.lower().strip().replace(" ", "_"))
    payload = [("theme.bin", sized_json(body))]
    if parsed.icons:
        if not os.path.isdir(parsed.icons):
            fail("carpeta de iconos inexistente: %r" % parsed.icons)
        for name in sorted(os.listdir(parsed.icons)):
            if not name.endswith(".png"):
                continue
            with open(os.path.join(parsed.icons, name), "rb") as png:
                payload.append(("icons/" + name, png.read()))
    entries = build_entries("theme", ext_id, parsed.name, parsed.version,
                            parsed.author, [], payload, parsed.icon)
    if not parsed.output.endswith(".necroext"):
        fail("la salida debe terminar en .necroext")
    build_container(parsed.output, entries)
    manifest, names = read_container(parsed.output)
    icons = len([n for n in names if n.startswith("icons/")])
    print("theme: %s (%s) tokens: %.1fKB iconos: %d ok" %
          (manifest["name"], manifest["id"], len(body) / 1024.0, icons))


if __name__ == "__main__":
    main()
