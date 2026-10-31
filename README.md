# ChillMod Bedrock Converter

GitHub Actions downloads the ChillMod 1.3 128x **Plant Package** from its CurseForge file page and attempts a best-effort conversion to a Bedrock resource pack.

## Target
- Minecraft Bedrock / PE: **1.26.52**
- Output: `.mcpack`
- Preserve source PNG dimensions (including 128x)

## Run
1. Open the **Actions** tab.
2. Select **Download and convert ChillMod to Bedrock**.
3. Tap **Run workflow**.
4. When complete, download the artifact named `ChillMod-Plant-Bedrock-1.26.52`.

No ZIP upload is needed. The workflow downloads the source archive directly from CurseForge.

## Scope and limitations
This workflow currently downloads only the Plant Package (CurseForge file ID 9021741, 38.9 MB). ChillMod's CurseForge page lists three other separate packages; they are not included in this first automated workflow yet.

The converter is experimental. It packages compatible PNG assets and generates a Bedrock manifest/atlases, but Java texture names and Bedrock vanilla identifiers differ. A generated `.mcpack` may import without reproducing all Java visuals. Java CIT, OptiFine, shaders, custom models, connected textures and Java-specific rendering features are not automatically translated.
