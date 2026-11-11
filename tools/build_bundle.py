#!/usr/bin/env python3
"""Packs a bundle (.necroext, type "bundle"): several extension packs in
one container for distribution only. Installing unpacks every inner
.necroext as its own extension — the bundle itself is never kept.

    tools/build_bundle.py --name "MD Look" --id mdlook pack1.necroext ...

Inner packs keep their own manifest/type/id: bundle = zip of packs.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extpack import (build_container, common_args, fail, manifest_bin,
                     valid_id)


def main():
    parser = common_args()
    parser.add_argument("packs", nargs="+",
                        help="los .necroext que el bundle lleva")
    parser.add_argument("-o", "--output", required=True)
    parsed = parser.parse_args()

    ext_id = parsed.id or (parsed.name.lower().strip().replace(" ", "_"))
    if not valid_id(ext_id):
        fail("id de bundle invalido: %r" % ext_id)
    if not parsed.output.endswith(".necroext"):
        fail("la salida debe terminar en .necroext")

    payload = []
    for path in parsed.packs:
        if not os.path.isfile(path):
            fail("no existe: %s" % path)
        name = os.path.basename(path)
        if not name.endswith(".necroext"):
            name += ".necroext"
        with open(path, "rb") as fh:
            payload.append((name, fh.read()))
        print("  + %s" % name)

    manifest = manifest_bin("bundle", ext_id, parsed.name, parsed.version,
                            parsed.author, [])
    body = [("manifest.bin", manifest)] + payload
    build_container(parsed.output, body)
    print("bundle: %s (%s) packs: %d ok" %
          (parsed.name, ext_id, len(payload)))


if __name__ == "__main__":
    main()
