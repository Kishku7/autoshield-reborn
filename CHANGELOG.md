# Changelog

All notable changes to Auto-Shield Reborn are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Jars are suffixed with the Minecraft version.
Versioning policy is universal across all mods and is NOT restated here -- see Memory/minecraft/mod-rules.md.

## [1.2.1] - 2026-08-05

### Fixed
- **`LivingEntity.swing(InteractionHand, boolean)` is GONE at 26.3-snapshot-7** -- a hard compile
  break in the auto-block mixin, which swings the shield hand as block feedback. Both the 1-arg and
  2-arg overloads were removed; the only remaining form is
  `swing(hand, SwingAnimation, sendToSwingingEntity)`. Now emitted per version by the codegen
  (`compat.swing_anim`, `>= 26.3`): 26.3+ passes the shield's own
  `getInteractAnimation()` -- a block is a use-path action, which is the animation vanilla threads
  through its own interact sites -- and every earlier cell keeps the plain 2-arg call. The
  `sendToSwingingEntity` flag stays `true` either way: this mixin runs server-side and the blocking
  player should see their own swing.

### Changed
- **Fabric 26.3 cell moved to MC 26.3-snapshot-7** (from snapshot-6): fabric-api
  `0.156.1+26.3` -> `0.156.2+26.3`, resource `pack_format` `94` -> `95` (bumped in
  `_codegen/compat.py` `resource_format`, the mod's single source for that value), exclusive window
  `[26.3-alpha.6, 26.3-alpha.7)` -> `[26.3-alpha.7, 26.3-alpha.8)`. Every 26.3 snapshot bumps
  pack_format by one, so each jar stays snapshot-exclusive. ModMenu stays on `21.0.0-alpha.1`
  (still the 26.3-line major). No other cell changed.

### Notes
- The other snapshot-7 breaking surfaces do not touch ASR: the trailing `Prediction` argument on
  `LivingEntity.drop(ItemStack, boolean)` / `Inventory.placeItemBackInInventory` (ASR neither drops
  nor returns items), the client-side `LocalPlayer.drop(boolean)` return-type change, the
  `InteractionResult.SwingSource` `CLIENT`/`SERVER` -> `PREDICTED`/`SERVER_ONLY` rename (ASR uses
  only the plain `InteractionResult` constants), and the 32 new concrete slab/stair blocks plus the
  filled-map colour component removals.
## [1.2.0] - 2026-07-28

### Added
- **`/asr` commands -- ModMenu is now genuinely optional.** Every setting the ModMenu config
  screen can reach is now reachable from a command, so ModMenu can be dropped at any time
  (and a vanilla client or the server console can drive it):
  - `/asr` or `/asr durability` -- show the current durability cost (anyone).
  - `/asr durability <0-10>` -- set it (op only). Persists to the config file and broadcasts
    the new value to every connected client, exactly like the screen did.
  - `/asr reload` -- re-read the config file from disk and re-sync (op only), so a hand-edited
    JSON can be applied without a restart.
  The tree lives in ONE loader-neutral class (`command/ASRCommands.java`, cog-emitted); each
  loader supplies only its `CommandDispatcher` and an S2C broadcast callback, since that part
  is genuinely loader-specific. Registered on Fabric via `CommandRegistrationCallback`, and on
  NeoForge/Forge via `RegisterCommandsEvent` (both the EB6 and EB7 wiring).
- `ASRConfig.reload()` backing `/asr reload`.

### Fixed
- **All three 26.x ModMenu pins were pointing at the wrong MC line.** ModMenu ships a separate
  major per MC line, and an older major is INTERMEDIARY-named, so it cannot compile against a
  newer mojmap MC. The 26.1 row pinned `17.0.0-beta.1` -- which is the **1.21.11** line -- and
  that is what broke the 26.1 cell (`cannot access class_437`). 26.2 and 26.3 were both pinned
  to 26.1-era ModMenu and only compiled by luck, since ASR touches just the `ModMenuApi` /
  `ConfigScreenFactory` surface. Corrected to the real per-line versions:
  **26.1 -> 18.0.0, 26.2 -> 20.0.1, 26.3 -> 21.0.0-alpha.1**. The Fabric 26.1 cell builds again.

### Changed
- Version 1.1.3 -> **1.2.0** (minor: new user-facing feature).

### Verified
- Fabric 26.1 / 26.2 / 26.3 and NeoForge 26.1 / 26.2 all build clean (0 javac warnings).
- Forge validated on BOTH event-bus eras: 1.20.1 (EB6 + SimpleChannel) and 1.21.8 (EB7).
- **Behavioural**, on the Raider 26.3-snapshot-6 dedicated server: `/asr` reported cost 1,
  `/asr durability 4` applied and echoed, `/asr` read back 4, `/asr reload` re-read 4, and the
  value was confirmed written to `config/autoshield-reborn.json`.

### Known gap (unchanged from 1.1.3)
- ASR still has **no `scripts/build-forge.ps1`**; the Forge cells have to be driven cell-by-cell
  through their own `gradlew`. Every other loader has a canonical build script.

## [1.1.3] - 2026-07-28

### Fixed
- **26.x jars now ship a `pack.mcmeta`.** No ASR 26.x jar carried one -- not Fabric
  26.1/26.2/26.3, not the NeoForge 26 jars. `cog-gen.ps1` only emitted the file for Forge
  cells, and `compat.datapack_format()` returned a flat 88 for all of 26.x, which is not the
  26 shape anyway. Now every 26.x cell, on every loader, emits the exact-single RANGE form
  (`pack_format = min_format = max_format`) required by the 26 codec -- a plain int > 81 FATALs
  the NeoForge dedicated-server datapack load, and the pre-26 `supported_formats` shape is
  rejected outright.
- New `compat.resource_format(mcver)` supplies the RESOURCE major per 26.X line
  (26.1 -> 84, 26.2 -> 88, 26.3 -> 94, read from each line's `SharedConstants`); it returns
  `None` below 26 so the pre-26 Forge-only `datapack_format` path is untouched.
- Rebuilt and verified in the jars: Fabric 26.2 -> 88, Fabric 26.3 -> 94,
  NeoForge 26.1.2 -> 84, NeoForge 26.2 -> 88, all in range form.

### Changed
- Mod-wide version 1.1.2 -> **1.1.3** (every rebuilt-and-shipped binary gets a bump).

### Known issue (PRE-EXISTING, surfaced by this rebuild -- NOT caused by it)
- **The Fabric 26.1 cell does not compile.** It fails in `ASRModMenu.java` with
  `cannot access class_437` / `invalid constructor reference` -- the ModMenu artifact pinned for
  the 26.1 row (`17.0.0-beta.1`) resolves to an intermediary-named build that will not compile
  against the mojmap 26.x cell. Unrelated to pack.mcmeta (26.2 and 26.3 build clean with the
  identical change). The 26.1 Fabric jar therefore still ships WITHOUT pack.mcmeta until the
  ModMenu pin is sorted; 26.2, 26.3 and both NeoForge cells are fixed.

## [1.1.2] - 2026-07-28

### Changed
- **Fabric 26.3 cell moved to MC 26.3-snapshot-6** (from snapshot-5): fabric-api
  `0.155.3+26.3` -> `0.156.1+26.3`, exclusive window `[26.3-alpha.5, 26.3-alpha.6)` ->
  `[26.3-alpha.6, 26.3-alpha.7)`.
- `scripts/build-fabric.ps1` no longer hard-codes `-Pmod_version=1.1.0` -- it was pinned to a
  released number, so every rebuild re-used it. Now 1.1.2, computed from CHANGELOG per the
  global versioning rule.

### Fixed
- **The Fabric 26 line could not build at all from `build-fabric.ps1`.** The script sets
  `JAVA_HOME` to JDK 21 at the top for the pre-26 cells and never changed it for the 26 line,
  which compiles at release 25 -- so `-M26 26.x` died with `error: release version 25 not
  supported`. `Build-26` now swaps `JAVA_HOME` to JDK 25 for the 26 cells and restores the
  previous value afterwards, so a mixed pre-26 + 26 run still works.

### Notes
- **No source change required.** The whole tree was scanned against every snapshot-6 breaking
  surface (worldgen noise overhaul, Entity invulnerability split, `startSleeping` void ->
  boolean, `SharedSuggestionProvider` filter parameter, `InputWithModifiers.getDigit()`
  removal, options-screen reshuffle, terrain multidraw path, block-entity loot helpers) with
  zero hits.

### Known gap (pre-existing, NOT introduced here)
- **No ASR 26.x jar ships a `pack.mcmeta`** -- not Fabric 26.1/26.2/26.3, not the NeoForge 26
  jars. The 26.x rule wants the exact-single range form (`pack_format = min_format =
  max_format`). Fabric and NeoForge both synthesise usable defaults when the file is absent, so
  nothing is broken today, but this is a real deviation and fixing it needs build wiring (a
  per-row `pf` value + a `${packFormat}` placeholder), not a one-line edit. Left for a
  deliberate pass rather than changed mid-snapshot-bump.

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
