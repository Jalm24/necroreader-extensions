#!/usr/bin/env python3
"""One packer for the four extension types.

    tools/necroext.py build examples/provider-example
    tools/necroext.py build mytheme -o dist/
    tools/necroext.py inspect myprovider.necroext
    tools/necroext.py unpack myprovider.necroext myprovider/

The input is a FOLDER, not a pile of flags: the type lives in manifest.json
and the tool turns what is inside into the .necroext container
(manifest.bin + payload). The developer never writes bytes.

    my-ext/
      manifest.json       {"type","id","name","version","author","languages"}
      assets/             optional: icon.png and whatever the extension
                          needs; copied as-is, recursively
      behaviors.json      type "provider"
      theme.json          type "theme"   (+ icons/<sprite>.png)
      lang/<code>.json    type "lang"    (one per declared language)
      *.necroext          type "bundle"  (inner packs)

The tool re-reads the container with the installer's own parser and
applies its limits up front (1 MB per JSON payload, 4 MB per file,
8 MB per extension).
"""
import argparse
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extpack import (build_container, fail, manifest_bin, read_container,
                     sized_json, valid_id)

TYPES = ("provider", "theme", "lang", "bundle")
MAX_JSON = 1024 * 1024
MAX_ENTRY = 4 * 1024 * 1024
MAX_TOTAL = 8 * 1024 * 1024
MAX_MANIFEST = 64 * 1024


def warn(message):
    sys.stdout.flush()
    sys.stderr.write("WARN: %s\n" % message)


def load_json(path):
    try:
        with open(path, "rb") as raw:
            return json.loads(raw.read().decode("utf-8"))
    except (OSError, ValueError) as error:
        fail("%s is not valid JSON: %s" % (os.path.basename(path), error))


def compact(doc):
    return json.dumps(doc, separators=(",", ":"), ensure_ascii=False,
                      sort_keys=True)


def read_bytes(path):
    with open(path, "rb") as raw:
        return raw.read()


def infer_type(folder):
    """Only when manifest.json omits "type": the payload says what it is."""
    if os.path.isfile(os.path.join(folder, "behaviors.json")):
        return "provider"
    if os.path.isfile(os.path.join(folder, "theme.json")):
        return "theme"
    if os.path.isdir(os.path.join(folder, "lang")):
        return "lang"
    for name in os.listdir(folder):
        if name.endswith(".necroext"):
            return "bundle"
    fail("manifest.json has no type and the folder does not tell")


def read_manifest(folder):
    path = os.path.join(folder, "manifest.json")
    if not os.path.isfile(path):
        fail("manifest.json is missing in %s" % folder)
    doc = load_json(path)
    if not isinstance(doc, dict):
        fail("manifest.json must be an object")
    ext_id = doc.get("id")
    if not isinstance(ext_id, str) or not valid_id(ext_id):
        fail("invalid extension id: %r" % ext_id)
    ext_type = doc.get("type") or infer_type(folder)
    if ext_type not in TYPES:
        fail("invalid type: %r (valid: %s)" % (ext_type, ", ".join(TYPES)))
    languages = doc.get("languages") or []
    if not isinstance(languages, list) or not all(
            isinstance(code, str) and valid_id(code) for code in languages):
        fail("languages must be a list of codes")
    if ext_type == "lang" and not languages:
        fail("a language pack declares its languages in manifest.json")
    return {
        "type": ext_type,
        "id": ext_id,
        "name": str(doc.get("name") or ext_id),
        "version": str(doc.get("version") or "1.0.0"),
        "author": str(doc.get("author") or ""),
        "languages": languages,
    }


def strip_ui_text(node):
    """Drops the section text fields from the behaviors, keeps the data.
    ONLY the section specs carry them (a node with its own layout); the
    mappers legitimately use a "title" key that tells the app which field
    of the response holds the manga name."""
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


def validate_sections(behaviors):
    if not isinstance(behaviors, dict):
        fail("behaviors must be an object")
    home = behaviors.get("get_home") or behaviors.get("sections")
    actions = behaviors.get("actions")
    if not home and isinstance(actions, dict):
        home = actions.get("get_home")
    if not home:
        return

    def walk(node):
        if isinstance(node, dict):
            if "layout" in node and "id" in node and not valid_id(str(node["id"])):
                fail("invalid section id: %r" % node["id"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(home)


def provider_payload(folder):
    path = os.path.join(folder, "behaviors.json")
    if not os.path.isfile(path):
        fail("a provider needs behaviors.json")
    behaviors = load_json(path)
    validate_sections(behaviors)
    strip_ui_text(behaviors)
    return [("behaviors.bin", sized_json(compact(behaviors)))]


def theme_payload(folder):
    path = os.path.join(folder, "theme.json")
    if not os.path.isfile(path):
        fail("a theme needs theme.json")
    theme = load_json(path)
    if not isinstance(theme, dict) or not theme:
        fail("theme.json must be an object with at least one token")
    entries = [("theme.bin", sized_json(compact(theme)))]
    icons = os.path.join(folder, "icons")
    if os.path.isdir(icons):
        for name in sorted(os.listdir(icons)):
            if not name.endswith(".png"):
                warn("icons/%s skipped: only .png is packed" % name)
                continue
            entries.append(("icons/" + name, read_bytes(os.path.join(icons, name))))
    return entries


def lang_payload(folder, languages):
    entries = []
    for code in languages:
        path = os.path.join(folder, "lang", code + ".json")
        if not os.path.isfile(path):
            fail("lang/%s.json is missing (declared in languages)" % code)
        table = load_json(path)
        if not isinstance(table, dict):
            fail("lang/%s.json must be a table of key -> text" % code)
        entries.append((code + ".bin", sized_json(compact(table))))
    declared = set(code + ".json" for code in languages)
    lang_dir = os.path.join(folder, "lang")
    if os.path.isdir(lang_dir):
        for name in sorted(os.listdir(lang_dir)):
            if name.endswith(".json") and name not in declared:
                fail("lang/%s is not declared in languages" % name)
    return entries


def bundle_payload(folder):
    entries = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".necroext"):
            continue
        inner, _ = read_container(os.path.join(folder, name))
        if inner["type"] == "bundle":
            fail("%s: a bundle cannot carry bundles" % name)
        entries.append((name, read_bytes(os.path.join(folder, name))))
    if not entries:
        fail("a bundle needs at least one inner .necroext")
    return entries


def asset_entries(folder, entries):
    root = os.path.join(folder, "assets")
    if not os.path.isdir(root):
        warn("no assets/ folder: the manager row will use the builtin icon")
        return
    for base, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(base, name)
            entries.append((os.path.relpath(full, folder).replace(os.sep, "/"),
                            read_bytes(full)))
    if not any(name == "assets/icon.png" for name, _ in entries):
        warn("assets/icon.png is missing: the manager row will use the builtin icon")


def check_limits(entries):
    total = 0
    for name, data in entries:
        if len(data) > MAX_ENTRY:
            fail("%s exceeds 4 MB" % name)
        if name.endswith(".bin") and name != "manifest.bin" and len(data) > MAX_JSON:
            fail("%s exceeds 1 MB" % name)
        if name == "manifest.bin" and len(data) > MAX_MANIFEST:
            fail("manifest.bin exceeds 64 KB")
        total += len(data)
    if total > MAX_TOTAL:
        fail("the extension exceeds 8 MB in total")


def output_path(given, ext_id):
    if not given:
        return ext_id + ".necroext"
    if os.path.isdir(given) or given.endswith(os.sep):
        return os.path.join(given, ext_id + ".necroext")
    if not given.endswith(".necroext"):
        fail("the output must end in .necroext")
    return given


def build(folder, info, out_path):
    if not os.path.isdir(folder):
        fail("no such folder: %r" % folder)
    if info["type"] == "provider":
        payload = provider_payload(folder)
    elif info["type"] == "theme":
        payload = theme_payload(folder)
    elif info["type"] == "lang":
        payload = lang_payload(folder, info["languages"])
    else:
        payload = bundle_payload(folder)
    if info["type"] != "bundle":
        # A bundle is distribution only: it never installs, so the
        # manager-row icon and its warnings do not apply.
        asset_entries(folder, payload)
    entries = [("manifest.bin",
                manifest_bin(info["type"], info["id"], info["name"],
                             info["version"], info["author"],
                             info["languages"]))] + payload
    check_limits(entries)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    try:
        build_container(out_path, entries)
    except OSError as error:
        fail("could not write %s: %s" % (out_path, error))

    manifest, names = read_container(out_path)
    print("%s: %s (%s) v%s" % (manifest["type"], manifest["name"],
                               manifest["id"], manifest["version"]))
    for name, data in sorted(entries):
        print("  %-32s %7.1f KB" % (name, len(data) / 1024.0))
    print("-> %s (%.1f KB, %d entries)" %
          (out_path, os.path.getsize(out_path) / 1024.0, len(names)))


def inspect(pack):
    manifest, names = read_container(pack)
    print("type:      %s" % manifest["type"])
    print("id:        %s" % manifest["id"])
    print("name:      %s" % manifest["name"])
    print("version:   %s" % manifest["version"])
    print("author:    %s" % (manifest["author"] or "(empty)"))
    if manifest["languages"]:
        print("languages: %s" % ", ".join(manifest["languages"]))
    with zipfile.ZipFile(pack) as zf:
        for name in sorted(names):
            print("  %-32s %7.1f KB" % (name, zf.getinfo(name).file_size / 1024.0))


def json_pretty(sized):
    doc = json.loads(sized[4:].decode("utf-8"))
    return (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def unpack(pack, folder):
    manifest, names = read_container(pack)
    os.makedirs(folder, exist_ok=True)
    doc = {
        "type": manifest["type"],
        "id": manifest["id"],
        "name": manifest["name"],
        "version": manifest["version"],
        "author": manifest["author"],
    }
    if manifest["languages"]:
        doc["languages"] = manifest["languages"]
    with open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8") as out:
        out.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")

    with zipfile.ZipFile(pack) as zf:
        for name in names:
            if name == "manifest.bin":
                continue
            data = zf.read(name)
            target = name
            if name in ("behaviors.bin", "theme.bin"):
                target = name[:-4] + ".json"
                data = json_pretty(data)
            elif name.endswith(".bin") and name[:-4] in manifest["languages"]:
                target = "lang/" + name[:-4] + ".json"
                data = json_pretty(data)
            full = os.path.join(folder, target)
            os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
            with open(full, "wb") as out:
                out.write(data)
    print("unpacked: %s -> %s (%d files)" % (pack, folder, len(names) - 1))


def main():
    parser = argparse.ArgumentParser(
        description="Pack, inspect and unpack NecroReader extensions.")
    sub = parser.add_subparsers(dest="command", required=True)

    build_parser = sub.add_parser("build", help="folder -> .necroext")
    build_parser.add_argument("folder", help="folder with manifest.json")
    build_parser.add_argument("-o", "--output", default=None,
                              help="output .necroext file or folder")

    inspect_parser = sub.add_parser("inspect", help="show manifest and members")
    inspect_parser.add_argument("pack")

    unpack_parser = sub.add_parser("unpack", help=".necroext -> editable folder")
    unpack_parser.add_argument("pack")
    unpack_parser.add_argument("folder")

    args = parser.parse_args()
    if args.command == "build":
        info = read_manifest(args.folder)
        build(args.folder, info, output_path(args.output, info["id"]))
    elif args.command == "inspect":
        inspect(args.pack)
    else:
        unpack(args.pack, args.folder)


if __name__ == "__main__":
    main()
