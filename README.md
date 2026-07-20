# Auto-Shield Reborn - Build Guide (`minecraft-1.20-26.3` branch)

The single cross-version source for **Auto-Shield Reborn** on Fabric, Forge, and NeoForge, MC
**1.20.1 -> 26.3-snapshot-4**. Landing page / what-it-is: the [`main` branch](https://github.com/Kishku7/autoshield-reborn/tree/main).
Report issues: [mod_support](https://github.com/Kishku7/mod_support/issues).

One Cog source of truth (`_codegen/cog_sources`) generates every `(loader, MC-version)` cell's
`gen/` tree; each cell's `build.gradle` compiles `gen/`, never the sources directly. All version and
loader drift is resolved by `_codegen/compat.py`.

## What you need installed

- **JDKs** (Eclipse Adoptium): **17** (Forge 1.20.1), **21** (1.20.6 - 1.21.x cells), **25** (26.x cells).
- **Python 3** + **Cog**: `pip install cogapp`.
- **PowerShell 7** (`pwsh`) to run the generator + build scripts.
- Gradle is provided per cell by its wrapper (Fabric/NeoForge use Gradle 9.x; Forge FG6 uses 8.8).

## How to build

```
pwsh scripts/build-fabric.ps1            # all pre-26 Fabric cells
pwsh scripts/build-fabric.ps1 -M26 @('26.1','26.2','26.3')
```
NeoForge + Forge cells build from their `<Loader>/<ver>` dir: `scripts/cog-gen.ps1 -Cell <Loader>/<ver>
-McVer <v> -Loader <Loader>` then that cell's `gradlew clean build`. Built jars are copied to `dist/`.

## Coverage

| Loader | Versions |
|--------|----------|
| Fabric | 1.20.1, 1.20.6, 1.21.1, 1.21.5, 1.21.8, 1.21.11, 26.1, 26.2, 26.3-snapshot-4 |
| NeoForge | 1.20.6, 1.21.1, 1.21.5, 1.21.8, 1.21.11, 26.1.2, 26.2 |
| Forge (FG6) | 1.20.1, 1.20.6, 1.21.1, 1.21.5, 1.21.8 |

Forge ceiling is 1.21.8 (FG6; 1.21.9-1.21.11 are Fabric + NeoForge only). All cells compile
`-Xlint:all` with zero warnings.

## Repository layout

- `_codegen/compat.py` - the cross-version/loader "era brain": whole-file emitters (mixin, networking,
  payloads, entrypoints, config screen) selected per MC version + loader.
- `_codegen/cog_sources/` - thin Cog wrappers + invariant shared files (ASRConfig, icon) + per-loader
  entrypoint/client/manifest sources.
- `scripts/cog-gen.ps1` - materialises a cell's `gen/` tree (loader-aware placement, presence-gates the
  payload API + ClientNet out of 1.20.1, regenerates the mixin config's compatibilityLevel + Forge refmap).
- `scripts/build-fabric.ps1` - Fabric build driver.
- `<Loader>/<ver>/` - per-cell Gradle project (build.gradle + gradle.properties + wrapper); `gen/` is generated.

## How the code generation works

`compat.py` parses the MC version into an era and returns the correct WHOLE-FILE source for each drift
point: the blocking mixin hook (component `applyItemBlocking` on 26.x + 1.21.11; legacy `hurtServer`
1.21.2-1.21.8 / `hurt` <=1.21.1), the identifier form (`Identifier` >=1.21.11, `ResourceLocation.
fromNamespaceAndPath` 1.21.x, `new ResourceLocation` below), networking (Fabric payload registry vs
1.20.1 channel; NeoForge PayloadRegistrar; Forge PayloadChannel vs 1.20.1 SimpleChannel), permissions,
screen-open, durability signature, and the AbstractArrow package. Direct-compile (Cog) rather than
reflection because pre-26 Fabric runs on the intermediary runtime.

By Kishku7. All Rights Reserved. A from-scratch rewrite of
[agorasim20/autoshield](https://github.com/agorasim20/autoshield) (CC0-1.0).
