# ChillMod Bedrock Converter

A texture-only Java resource-pack port for Minecraft Bedrock / PE 1.26.52.

## Run on GitHub (phone-friendly)

1. Open Actions.
2. Select Download and convert ChillMod to Bedrock.
3. Tap Run workflow.
4. When complete, download the artifact ChillMod-Plant-Bedrock-1.26.52.
5. Import the .mcpack into Minecraft and enable it in world/resource-pack settings.

No PC, Termux, or manual ZIP upload is required.

## What it does

- Downloads the ChillMod 1.3 Plant Package from CurseForge.
- Downloads official Mojang Bedrock vanilla texture atlases.
- Maps known Java plant/foliage PNG names to Bedrock vanilla texture paths.
- Places PNGs at the Bedrock paths used by vanilla, overriding those textures.
- Produces a report listing every mapped and unmapped file.

## Limitations

This is not a complete Java-to-Bedrock resource-pack converter. It only applies PNGs with a known Bedrock vanilla mapping. Java block models, blockstates, random texture variants, connected textures, OptiFine/CIT, shaders, and Java-specific animation/rendering are not translated. Review conversion-report.txt to see exactly what was mapped.

The workflow uses Mojang's public bedrock-samples repository as the reference for Bedrock texture paths.
