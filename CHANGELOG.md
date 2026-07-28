# Changelog

All notable changes to Auto-Shield Reborn are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Jars are suffixed with the Minecraft version.
Versioning policy is universal across all mods and is NOT restated here -- see Memory/minecraft/mod-rules.md.

## [1.1.1] - 2026-07-27

### Added
- scripts/build-neoforge.ps1 - Auto-Shield Reborn previously had no canonical NeoForge build script, so its NeoForge/26 cell had no reproducible build path and a bare gradlew build silently compiled a stale gitignored gen/ tree. The new script drives cog-gen then Gradle with per-26.X -P overrides and copies to dist/, matching the other mods.

### Changed
- NeoForge 26 cells rebuilt against the now-PUBLISHED NeoForge builds: 26.1 -> 26.1.2.87, 26.2 -> 26.2.0.35-beta (previously 26.2.0.25-beta, and the 26.1 NeoForge jar had no reproducible build at all). mavenLocal() removed from the cell.
- No source or behaviour change. Server-boot smoketested on NeoForge 26.1.2 and 26.2.

## [1.1.0] - 2026-07-19

### Added
- **Forge (FG6) support**: 1.20.1, 1.20.6, 1.21.1, 1.21.5, 1.21.8.
- **NeoForge below 26**: 1.20.6, 1.21.1, 1.21.5, 1.21.8, 1.21.11.
- **Fabric 26.3-snapshot-5** cell (fabric-api 0.155.3+26.3, dep `26.3-alpha.5`). Loads + renders
  in-world on the snapshot (headless client-harness eyeballed).

### Changed
- The 26.x config-screen entrypoint now sources **ModMenu from Modrinth's maven**
  (`maven.modrinth:modmenu`) instead of `maven.terraformersmc.com`, which stopped serving the
  18.x ModMenu artifacts. Also fixed a `-M26` build-script arg bug (a `$M26`/`$m26` PowerShell
  case-insensitive name collision that clobbered the target parameter).

### Changed
- Unified every loader and Minecraft version onto a single Cog source of truth (`_codegen`), matching
  the shared mod standard; eliminated the `shared_minecraft` tree.
- `-Xlint:all` is now wired on every cell and the whole 21-cell matrix compiles with zero warnings.
- Config screen unified on the loader-neutral `ClientNet` sender across all payload-era cells.

### Fixed
- Correct per-version drift now proven by build across the full matrix: the `Identifier` rename
  (1.21.11), `ResourceLocation.fromNamespaceAndPath` vs `new ResourceLocation` boundary, NeoForge
  `ClientPacketDistributor` split (1.21.6), and the static `calculateViewVector` lint on 26.x.

## [1.0.2] - 2026-06-17
- 26.2 stable (Fabric + NeoForge); Fabric backports to the 1.20.x and 1.21.x lines (source).

## [1.0.0] - 2026-06-11
- Initial release: Fabric + NeoForge on the 26.x line.
