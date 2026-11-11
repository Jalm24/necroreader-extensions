#!/usr/bin/env python3
"""Packs a language extension (.necroext, type "lang").

    tools/build_langpack.py --name TuPackLang --author X \
        es:es.json en:en.json -o tupacklang.necroext

Every argument CODE:FILE carries the translation table of that code
(plain JSON "key": "text"); the manifest does not need manual edition. The
tables ride sized like behaviors.bin (u32 size + JSON), so the reader's
loader opens them as-is. The output is re-opened and re-validated here
before the exit, so what lands on the device is what the installer takes.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extpack import (build_container, build_entries, common_args, fail,
                     parse_manifest, read_container, sized_json)


def load_table(label, path):
    try:
        with open(path, "rb") as table:
            raw = table.read()
    except OSError as error:
        fail("no se pudo leer %s: %s" % (path, error))
    try:
        data = json.loads(raw.decode("utf-8"))
    except ValueError as error:
        fail("%s no es JSON valido: %s" % (path, error))
    if not isinstance(data, dict):
        fail("%s debe ser un objeto clave : texto" % label)
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, str):
            fail("%s: las claves y los textos deben ser strings" % label)
    return raw


def main():
    parser = common_args()
    parser.add_argument("tables", nargs="+", metavar="CODE:FILE")
    parser.add_argument("-o", "--output", required=True)
    parsed = parser.parse_args()

    pairs = []
    for spec in parsed.tables:
        code, sep, table = spec.partition(":")
        if not sep or not table:
            fail("falta CODE:FILE: %r" % spec)
        pairs.append((code, load_table(code, table)))
    if not pairs:
        fail("al menos un idioma")

    codes = [code for code, _ in pairs]
    ext_id = parsed.id or (parsed.name.lower().strip()
                           .replace(" ", "_"))
    entries = build_entries(
        "lang", ext_id, parsed.name, parsed.version, parsed.author,
        codes, [(code + ".bin", sized_json(raw.decode("utf-8")))
                for code, raw in pairs],
        parsed.icon)
    if not parsed.output.endswith(".necroext"):
        fail("la salida debe terminar en .necroext")
    build_container(parsed.output, entries)

    manifest, names = read_container(parsed.output)
    print("pack: %s (%s) idiomas: %s entradas: %d ok" %
          (manifest["name"], manifest["id"],
           ",".join(manifest["languages"]), len(names)))


if __name__ == "__main__":
    main()
