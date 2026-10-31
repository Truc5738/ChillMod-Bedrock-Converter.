#!/usr/bin/env python3
"""Package Java resource-pack PNG assets into a best-effort Bedrock resource pack.

This does not translate Java models, block states, CIT/OptiFine, shaders, or
map arbitrary Java texture names onto Bedrock's vanilla identifiers.
"""
from pathlib import Path
from collections import Counter
import json, shutil, zipfile, uuid, re, sys, struct

ROOT = Path.cwd()
INPUT = ROOT / "input" / "chillmod.zip"
WORK = ROOT / "work"
DIST = ROOT / "dist"
PACK = ROOT / "bedrock_pack"

def fail(message):
    print("ERROR:", message)
    sys.exit(1)

if not INPUT.is_file():
    fail("Missing input/chillmod.zip.")

if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)

try:
    with zipfile.ZipFile(INPUT) as archive:
        bad = archive.testzip()
        if bad:
            fail(f"Source ZIP integrity error: {bad}")
        archive.extractall(WORK)
except zipfile.BadZipFile:
    fail("input/chillmod.zip is not a valid ZIP archive.")

roots = [p for p in [WORK, *WORK.rglob("*")] if p.is_dir() and (p / "assets" / "minecraft").is_dir()]
if not roots:
    fail("Could not find assets/minecraft. This is not a Java resource-pack archive.")
source = max(roots, key=lambda p: len(p.parts))
textures = source / "assets" / "minecraft" / "textures"
if not textures.is_dir():
    fail("The Java pack has no assets/minecraft/textures directory.")

if PACK.exists():
    shutil.rmtree(PACK)
(PACK / "textures").mkdir(parents=True)

category_map = {
    "block": "blocks",
    "blocks": "blocks",
    "item": "items",
    "items": "items",
    "entity": "entity",
    "gui": "ui",
    "environment": "environment",
    "particle": "particle",
    "map": "map",
    "painting": "painting",
    "mob_effect": "ui/mob_effects",
}
copied = []
warnings = []
dimensions = Counter()
png_count = 0

for file in sorted(textures.rglob("*")):
    if not file.is_file() or file.suffix.lower() != ".png":
        continue
    png_count += 1
    relative = file.relative_to(textures)
    category = relative.parts[0] if relative.parts else ""
    target_category = category_map.get(category)
    if not target_category:
        warnings.append(f"Skipped unsupported texture category: {relative.as_posix()}")
        continue

    data = file.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        warnings.append(f"Skipped invalid PNG: {relative.as_posix()}")
        continue
    width, height = struct.unpack(">II", data[16:24])
    dimensions[f"{width}x{height}"] += 1

    subpath = Path(*relative.parts[1:])
    destination = PACK / "textures" / target_category / subpath
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file, destination)
    copied.append((relative.as_posix(), destination.relative_to(PACK).as_posix()))

if not copied:
    fail("No supported PNG textures were found.")

def make_atlas(folder_name):
    data = {
        "resource_pack_name": "chillmod_bedrock",
        "texture_name": "atlas." + folder_name,
        "texture_data": {}
    }
    prefix = "textures/" + folder_name + "/"
    for _, destination in copied:
        if not destination.startswith(prefix):
            continue
        rel = Path(destination).relative_to(prefix).with_suffix("")
        key = re.sub(r"[^a-zA-Z0-9_./-]", "_", rel.as_posix())
        data["texture_data"][key] = {"textures": destination[:-4]}
    return data

terrain = make_atlas("blocks")
items = make_atlas("items")
(PACK / "terrain_texture.json").write_text(json.dumps(terrain, indent=2), encoding="utf-8")
(PACK / "item_texture.json").write_text(json.dumps(items, indent=2), encoding="utf-8")

manifest = {
    "format_version": 2,
    "header": {
        "name": "ChillMod 1.3 128x (Bedrock best-effort)",
        "description": "PNG asset package. Java-specific features are not converted.",
        "uuid": str(uuid.uuid4()),
        "version": [1, 0, 1],
        "min_engine_version": [1, 26, 0]
    },
    "modules": [{
        "type": "resources",
        "uuid": str(uuid.uuid4()),
        "version": [1, 0, 1]
    }]
}
(PACK / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

DIST.mkdir(exist_ok=True)
output = DIST / "ChillMod-1.3-Bedrock-1.26.52.mcpack"
if output.exists():
    output.unlink()
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(PACK.rglob("*")):
        if file.is_file():
            archive.write(file, file.relative_to(PACK).as_posix())

# Validate the actual deliverable, not just the source files.
with zipfile.ZipFile(output) as archive:
    bad = archive.testzip()
    if bad:
        fail(f"Output MCpack ZIP integrity error: {bad}")
    names = set(archive.namelist())
    if "manifest.json" not in names:
        fail("Output is missing root-level manifest.json.")
    out_manifest = json.loads(archive.read("manifest.json"))
    if out_manifest.get("format_version") != 2:
        fail("Unsupported manifest format.")
    for atlas_name in ("terrain_texture.json", "item_texture.json"):
        atlas = json.loads(archive.read(atlas_name))
        for key, entry in atlas.get("texture_data", {}).items():
            texture_path = entry.get("textures", "") + ".png"
            if texture_path not in names:
                fail(f"Atlas entry {key} points to missing file {texture_path}.")

report = [
    "ChillMod Java -> Bedrock best-effort packaging report",
    "Target: Minecraft Bedrock / PE 1.26.52",
    f"PNG files found: {png_count}",
    f"PNG files copied: {len(copied)}",
    f"Block atlas entries: {len(terrain['texture_data'])}",
    f"Item atlas entries: {len(items['texture_data'])}",
    "Output ZIP integrity: PASS",
    "Manifest: PASS",
    "Atlas references: PASS",
    "",
    "PNG DIMENSIONS:",
    *[f"{size}: {count}" for size, count in sorted(dimensions.items())],
    "",
    "COPIED FILES:",
    *[f"{src} -> {dst}" for src, dst in copied],
    "",
    "WARNINGS / LIMITATIONS:",
    *warnings,
    "Bedrock atlas entries make copied assets addressable but do not automatically replace vanilla blocks/items.",
    "Java blockstate/model JSON, CTM, CIT, OptiFine, shaders, animations, and custom rendering are not translated.",
    "Visual compatibility must still be tested in Minecraft Bedrock 1.26.52."
]
(DIST / "conversion-report.txt").write_text("\n".join(report), encoding="utf-8")
print(f"Created and validated {output}: {len(copied)} PNG files, {len(terrain['texture_data'])} block atlas entries.")
