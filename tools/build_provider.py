#!/usr/bin/env python3
"""Packs a provider extension (.necroext, behaviors.bin, type "provider").

    tools/build_provider.py --name X --bases https://api.example.com/ \
        behaviors_v2.json -o x.necroext

The behaviors make the contract the interface respects: the provider sends
 VARIABLES, never UI text. A section declares id/layout/loop and the actual
data flow (source/steps/mappers) of each request. The section header and
 its action button are painted by the app: L10n.t("home.section." + id)
 and L10n.t("home.action." + actionId), falling back to the raw id.

Members of the JSON that would carry UI text ("title" in the sections or
 "action" with a sentence) are dropped. `manga.title`, `manga.author` and
 such stay data: those are the content the app shows verbatim.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extpack import (build_container, build_entries, common_args, fail,
                     parse_manifest, read_container, sized_json)


def strip_ui_text(node):
    """Walks the behaviors: drops the section text fields, keeps data.
    ONLY the section specs carry them (a node with its own layout); the
    mappers legitimately use a "title" key that tells the app the field
    of the response the manga name comes from."""
    if isinstance(node, list):
        for item in node:
            strip_ui_text(item)
    elif isinstance(node, dict):
        if "layout" in node:
            node.pop("title", None)
            if node.get("action") and not str(node.get("action")).isalnum():
                node.pop("action", None)
        for value in node.values():
            strip_ui_text(value)


def validate(behaviors):
    if not isinstance(behaviors, dict):
        fail("behaviors debe ser un objeto")
    home = behaviors.get("get_home") or behaviors.get("sections")
    if home:
        def walk(node):
            if isinstance(node, dict):
                if "layout" in node and "id" in node:
                    ident = node.get("id")
                    from extpack import valid_id
                    if not valid_id(str(ident)):
                        fail("id de seccion invalido: %r" % ident)
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
        walk(home)


def main():
    parser = common_args()
    parser.add_argument("behaviors", help="behaviors JSON (v2: sin title/action)")
    parser.add_argument("-o", "--output", required=True)
    parsed = parser.parse_args()

    try:
        with open(parsed.behaviors, "rb") as raw:
            behaviors = json.loads(raw.read().decode("utf-8"))
    except (OSError, ValueError) as error:
        fail("behaviors invalido: %s" % error)
    validate(behaviors)
    strip_ui_text(behaviors)
    body = json.dumps(behaviors, separators=(",", ":"),
                      ensure_ascii=False, sort_keys=True)

    from extpack import valid_id
    ext_id = parsed.id or (parsed.name.lower().strip().replace(" ", "_"))
    if not valid_id(ext_id):
        fail("id de extension invalido: %r" % ext_id)
    entries = build_entries("provider", ext_id, parsed.name, parsed.version,
                            parsed.author, [], [
                                ("behaviors.bin", sized_json(body))],
                            parsed.icon)
    if not parsed.output.endswith(".necroext"):
        fail("la salida debe terminar en .necroext")
    build_container(parsed.output, entries)
    manifest, names = read_container(parsed.output)
    print("provider: %s (%s) behaviours: %.1fKB entradas: %d ok" %
          (manifest["name"], manifest["id"], len(body) / 1024.0, len(names)))


if __name__ == "__main__":
    main()
