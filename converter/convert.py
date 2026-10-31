#!/usr/bin/env python3
"""Best-effort Java resource pack to Bedrock resource pack converter."""
from pathlib import Path
import json, shutil, zipfile, uuid, re, sys

ROOT = Path.cwd()
INPUT = ROOT / "input" / "chillmod.zip"
WORK = ROOT / "work"
DIST = ROOT / "dist"
PACK = ROOT / "bedrock_pack"

def fail(message):
    print("ERROR:", message)
    sys.exit(1)

if not INPUT.exists():
    fail("Missing input/chillmod.zip. Upload the ChillMod ZIP to that exact path.")

if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)
try:
    with zipfile.ZipFile(INPUT) as archive:
        bad = archive.testzip()
        if bad:
            fail(f"ZIP integrity error: {bad}")
        archive.extractall(WORK)
except zipfile.BadZipFile:
    fail("input/chillmod.zip is not a valid ZIP archive.")

roots = [p for p in [WORK, *WORK.rglob("*")] if p.is_dir() and (p / "assets" / "minecraft").is_dir()]
if not roots:
    fail("Could not find assets/minecraft. Upload the actual Java resource-pack ZIP.")
source = max(roots, key=lambda p: len(p.parts))
textures = source / "assets" / "minecraft" / "textures"

if PACK.exists():
    shutil.rmtree(PACK)
(PACK / "textures").mkdir(parents=True)

category_map = {
    "block": "blocks", "blocks": "blocks",
    "item": "items", "items": "items",
    "entity": "entity", "gui": "ui",
    "environment": "environment", "particle": "particle",
    "map": "map", "painting": "painting",
    "mob_effect": "ui"
}
copied = []
warnings = []

if textures.exists():
    for file in textures.rglob("*"):
        if not file.is_file() or file.suffix.lower() != ".png":
            continue
        relative = file.relative_to(textures)
        category = relative.parts[0] if relative.parts else ""
        if category not in category_map:
            warnings.append(f"Unmapped texture category: {relative.as_posix()}")
            continue
        folder = PACK / "textures" / category_map[category]
        folder.mkdir(parents=True, exist_ok=True)
        destination = folder / file.name
        if destination.exists():
            destination = folder / ("_".join(relative.parts))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, destination)
        copied.append((relative.as_posix(), destination.relative_to(PACK).as_posix()))
else:
    warnings.append("No assets/minecraft/textures folder found.")

# Bedrock atlas references. These make assets addressable, but do not guarantee
# that Java texture names match Bedrock's built-in texture identifiers.
def make_atlas(folder_name):
    data = {"resource_pack_name": "chillmod_bedrock", "texture_name": "atlas." + folder_name, "texture_data": {}}
    prefix = "textures/" + folder_name + "/"
    for _, destination in copied:
        if not destination.startswith(prefix):
            continue
        rel = Path(destination).relative_to(prefix).with_suffix("")
        key = re.sub(r"[^a-zA-Z0-9_]", "_", rel.as_posix())
        data["texture_data"][key] = {"textures": destination[:-4]}
    return data

(PACK / "terrain_texture.json").write_text(json.dumps(make_atlas("blocks"), indent=2), encoding="utf-8")
(PACK / "item_texture.json").write_text(json.dumps(make_atlas("items"), indent=2), encoding="utf-8")

manifest = {
    "format_version": 2,
    "header": {
        "name": "ChillMod 1.3 128x (Bedrock conversion)",
        "description": "Best-effort conversion for Minecraft Bedrock 1.26.52.",
        "uuid": str(uuid.uuid4()),
        "version": [1, 0, 0],
        "min_engine_version": [1, 26, 0]
    },
    "modules": [{
        "type": "resources",
        "uuid": str(uuid.uuid4()),
        "version": [1, 0, 0]
    }]
}
(PACK / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

DIST.mkdir(exist_ok=True)
output = DIST / "ChillMod-1.3-Bedrock-1.26.52.mcpack"
if output.exists():
    output.unlink()
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
    for file in PACK.rglob("*"):
        if file.is_file():
            archive.write(file, file.relative_to(PACK).as_posix())

report = [
    "ChillMod Java -> Bedrock conversion report",
    "Target: Minecraft Bedrock / PE 1.26.52",
    f"PNG textures copied: {len(copied)}",
    "",
    "COPIED FILES:",
    *[f"{src} -> {dst}" for src, dst in copied],
    "",
    "WARNINGS / MANUAL REVIEW:",
    *warnings,
    "",
    "IMPORTANT: .mcpack packaging success does not prove visual parity. Bedrock uses different texture identifiers and rendering features."
]
(DIST / "conversion-report.txt").write_text("\n".join(report), encoding="utf-8")
print(f"Created {output} with {len(copied)} PNG textures.")
