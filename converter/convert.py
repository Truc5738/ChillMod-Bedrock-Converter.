#!/usr/bin/env python3
"""Port mapped Java PNG textures to Bedrock vanilla texture paths."""
from pathlib import Path
from collections import Counter
import json, shutil, zipfile, uuid, sys, struct, re

ROOT = Path.cwd()
INPUT = ROOT / "input" / "chillmod.zip"
TERRAIN_ATLAS = ROOT / "input" / "terrain_texture.json"
ITEM_ATLAS = ROOT / "input" / "item_texture.json"
WORK, DIST, PACK = ROOT / "work", ROOT / "dist", ROOT / "bedrock_pack"

def fail(message):
    print("ERROR:", message)
    sys.exit(1)

def load_json(path):
    if not path.is_file():
        fail(f"Missing required Bedrock vanilla atlas: {path}")
    raw = re.sub(r"^\s*//[^\n]*\n", "", path.read_text(encoding="utf-8"))
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"Invalid atlas JSON {path}: {exc}")

def collect_paths(value):
    found = []
    if isinstance(value, str):
        if value.startswith("textures/"):
            found.append(value.removesuffix(".png"))
    elif isinstance(value, list):
        for item in value:
            found.extend(collect_paths(item))
    elif isinstance(value, dict):
        if isinstance(value.get("path"), str):
            found.extend(collect_paths(value["path"]))
        elif "textures" in value:
            found.extend(collect_paths(value["textures"]))
    return found

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
    fail("Could not find assets/minecraft. Source is not a Java resource pack.")
source = max(roots, key=lambda p: len(p.parts))
textures = source / "assets" / "minecraft" / "textures"
if not textures.is_dir():
    fail("Java resource pack has no assets/minecraft/textures directory.")

terrain = load_json(TERRAIN_ATLAS).get("texture_data", {})
items = load_json(ITEM_ATLAS).get("texture_data", {})

def build_index(atlas):
    by_key, by_base = {}, {}
    for key, entry in atlas.items():
        paths = list(dict.fromkeys(collect_paths(entry.get("textures"))))
        if paths:
            by_key[key] = paths
            for path in paths:
                by_base.setdefault(Path(path).name, []).append(path)
    return by_key, {k: list(dict.fromkeys(v)) for k, v in by_base.items()}

terrain_key, terrain_base = build_index(terrain)
item_key, item_base = build_index(items)

ALIASES = {
    "grass_block_top":"textures/blocks/grass_top",
    "grass_block_side":"textures/blocks/grass_side",
    "short_grass":"textures/blocks/tallgrass",
    "dead_bush":"textures/blocks/deadbush",
    "lily_pad":"textures/blocks/waterlily",
    "dandelion":"textures/blocks/flower_dandelion",
    "poppy":"textures/blocks/flower_rose",
    "blue_orchid":"textures/blocks/flower_blue_orchid",
    "allium":"textures/blocks/flower_allium",
    "azure_bluet":"textures/blocks/flower_houstonia",
    "red_tulip":"textures/blocks/flower_tulip_red",
    "orange_tulip":"textures/blocks/flower_tulip_orange",
    "white_tulip":"textures/blocks/flower_tulip_white",
    "pink_tulip":"textures/blocks/flower_tulip_pink",
    "oxeye_daisy":"textures/blocks/flower_oxeye_daisy",
    "cornflower":"textures/blocks/flower_cornflower",
    "lily_of_the_valley":"textures/blocks/flower_lily_of_the_valley",
    "sunflower_bottom":"textures/blocks/double_plant_sunflower_bottom",
    "sunflower_top":"textures/blocks/double_plant_sunflower_top",
    "lilac_bottom":"textures/blocks/double_plant_syringa_bottom",
    "lilac_top":"textures/blocks/double_plant_syringa_top",
    "tall_grass_bottom":"textures/blocks/double_plant_grass_bottom",
    "tall_grass_top":"textures/blocks/double_plant_grass_top",
    "large_fern_bottom":"textures/blocks/double_plant_fern_bottom",
    "large_fern_top":"textures/blocks/double_plant_fern_top",
    "rose_bush_bottom":"textures/blocks/double_plant_rose_bottom",
    "rose_bush_top":"textures/blocks/double_plant_rose_top",
    "peony_bottom":"textures/blocks/double_plant_paeonia_bottom",
    "peony_top":"textures/blocks/double_plant_paeonia_top",
    "oak_leaves":"textures/blocks/leaves_oak",
    "spruce_leaves":"textures/blocks/leaves_spruce",
    "birch_leaves":"textures/blocks/leaves_birch",
    "jungle_leaves":"textures/blocks/leaves_jungle",
    "acacia_leaves":"textures/blocks/leaves_acacia",
    "dark_oak_leaves":"textures/blocks/leaves_big_oak",
    "oak_sapling":"textures/blocks/sapling_oak",
    "spruce_sapling":"textures/blocks/sapling_spruce",
    "birch_sapling":"textures/blocks/sapling_birch",
    "jungle_sapling":"textures/blocks/sapling_jungle",
    "acacia_sapling":"textures/blocks/sapling_acacia",
    "dark_oak_sapling":"textures/blocks/sapling_roofed_oak",
    "oak_log":"textures/blocks/log_oak",
    "oak_log_top":"textures/blocks/log_oak_top",
    "spruce_log":"textures/blocks/log_spruce",
    "spruce_log_top":"textures/blocks/log_spruce_top",
    "birch_log":"textures/blocks/log_birch",
    "birch_log_top":"textures/blocks/log_birch_top",
    "jungle_log":"textures/blocks/log_jungle",
    "jungle_log_top":"textures/blocks/log_jungle_top",
    "acacia_log":"textures/blocks/log_acacia",
    "acacia_log_top":"textures/blocks/log_acacia_top",
    "dark_oak_log":"textures/blocks/log_big_oak",
    "dark_oak_log_top":"textures/blocks/log_big_oak_top"
}

if PACK.exists():
    shutil.rmtree(PACK)
(PACK / "textures").mkdir(parents=True)
copied, skipped, dimensions = [], [], Counter()
png_count = 0

for file in sorted(textures.rglob("*.png")):
    if not file.is_file():
        continue
    png_count += 1
    relative = file.relative_to(textures)
    category = relative.parts[0] if relative.parts else ""
    stem = file.stem.lower()
    if category in ("block", "blocks"):
        key_index, base_index = terrain_key, terrain_base
    elif category in ("item", "items"):
        key_index, base_index = item_key, item_base
    else:
        skipped.append(f"{relative.as_posix()}: unsupported Java category")
        continue

    alias = ALIASES.get(stem)
    if alias:
        target_paths = [alias] if Path(alias).name in base_index else []
    elif stem in key_index and len(key_index[stem]) == 1:
        target_paths = key_index[stem]
    else:
        target_paths = base_index.get(stem, [])
    target_paths = list(dict.fromkeys(target_paths))
    if not target_paths:
        skipped.append(f"{relative.as_posix()}: no safe Bedrock vanilla mapping")
        continue

    data = file.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        skipped.append(f"{relative.as_posix()}: invalid PNG")
        continue
    width, height = struct.unpack(">II", data[16:24])
    dimensions[f"{width}x{height}"] += 1
    for target in target_paths:
        destination = PACK / (target + ".png")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, destination)
        copied.append((relative.as_posix(), destination.relative_to(PACK).as_posix(), width, height))

if not copied:
    fail("No source PNG could be safely mapped to a Bedrock vanilla texture.")

manifest = {
    "format_version": 2,
    "header": {
        "name": "ChillMod 1.3 Plant Pack (Bedrock texture port)",
        "description": "Mapped Java plant textures for Minecraft Bedrock. Unmapped Java features are not included.",
        "uuid": str(uuid.uuid4()),
        "version": [1, 0, 2],
        "min_engine_version": [1, 26, 0]
    },
    "modules": [{"type": "resources", "uuid": str(uuid.uuid4()), "version": [1, 0, 2]}]
}
(PACK / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
DIST.mkdir(exist_ok=True)
output = DIST / "ChillMod-Plant-Bedrock-1.26.52.mcpack"
if output.exists():
    output.unlink()
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(PACK.rglob("*")):
        if file.is_file():
            archive.write(file, file.relative_to(PACK).as_posix())

with zipfile.ZipFile(output) as archive:
    bad = archive.testzip()
    if bad:
        fail(f"Output package ZIP error: {bad}")
    names = set(archive.namelist())
    if "manifest.json" not in names:
        fail("manifest.json must be at package root.")
    if not any(n.startswith("textures/") and n.endswith(".png") for n in names):
        fail("Package contains no Bedrock texture overrides.")
    for _, dest, _, _ in copied:
        if dest not in names:
            fail(f"Missing packaged texture: {dest}")

report = [
    "ChillMod Java -> Bedrock texture port report",
    "Target: Minecraft Bedrock / PE 1.26.52",
    f"Source PNG files found: {png_count}",
    f"PNG overrides mapped: {len(copied)}",
    f"Unique Bedrock texture files: {len(set(x[1] for x in copied))}",
    f"Unmapped/unsupported files: {len(skipped)}",
    "Package ZIP integrity: PASS",
    "Root manifest: PASS",
    "Texture files: PASS",
    "",
    "TEXTURE DIMENSIONS:",
    *[f"{size}: {count}" for size, count in sorted(dimensions.items())],
    "",
    "MAPPED OVERRIDES:",
    *[f"{src} -> {dst} ({w}x{h})" for src, dst, w, h in copied],
    "",
    "NOT MAPPED:",
    *skipped,
    "",
    "LIMITATIONS:",
    "Only PNGs with a known Bedrock vanilla mapping are applied.",
    "Java models, blockstates, random variants, connected textures, OptiFine/CIT, shaders and animations are not converted.",
    "Import and visually test in Minecraft Bedrock 1.26.52."
]
(DIST / "conversion-report.txt").write_text("\n".join(report), encoding="utf-8")
print(f"Created {output}: {len(copied)} mapped overrides from {png_count} Java PNGs; {len(skipped)} not mapped.")
