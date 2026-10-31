# ChillMod Bedrock Converter

GitHub Actions workflow for converting a Java resource-pack ZIP into a Bedrock `.mcpack`.

## Target
- Minecraft Bedrock / PE: **1.26.52**
- Output: Resource Pack (`.mcpack`)
- Preserve original image resolution (including 128x)

## Use
1. Upload the original ChillMod ZIP from CurseForge to `input/chillmod.zip`.
2. Open **Actions → Convert ChillMod to Bedrock**.
3. Select **Run workflow**.
4. Download the generated pack and conversion report from the workflow Artifacts.

## Important
This is a best-effort converter, not a perfect Java-to-Bedrock translator. It reorganizes compatible image assets, creates a Bedrock manifest and texture atlases, and reports Java-only features that need manual work. Java CIT, OptiFine, shaders, custom models, predicates, and pack-specific rendering features cannot be translated automatically.

The repository does not include ChillMod itself. Upload a copy you are permitted to use.
