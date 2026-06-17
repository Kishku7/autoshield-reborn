# Auto-Shield Reborn

**Auto-Shield Reborn** is a client + server mod that automatically blocks any shield-blockable hit coming from your frontal 180-degree arc whenever you hold a shield in **either hand** - no need to raise it. All blocking logic is server-authoritative, so it works on dedicated servers even with no client installed (the client only adds an in-game config screen). The per-hit shield durability cost is server-configurable (0-10, default 1).

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?logo=discord&logoColor=white)](https://discord.gg/2ZxzbCzAHe)

## Branches

Source is organized by Minecraft line. Each MC-line branch carries standalone `Fabric/<version>` and
`NeoForge/<version>` build trees - **no Architectury, no `common/` subproject** (MC 26.x is mojmap-native).
`main` (this branch) is the overview.

- [26.1](https://github.com/Kishku7/autoshield-reborn/tree/26.1) - Minecraft 26.1 - 26.1.2
- [26.2](https://github.com/Kishku7/autoshield-reborn/tree/26.2) - Minecraft 26.2 (pre-release)
- [1.20.x](https://github.com/Kishku7/autoshield-reborn/tree/1.20.x) - Minecraft 1.20 line (builds pending - scaffold)
- [1.21.x](https://github.com/Kishku7/autoshield-reborn/tree/1.21.x) - Minecraft 1.21 line (builds pending - scaffold)

## Supported platforms

- **Fabric** and **NeoForge** (client + server). Built for the **26.x line** today: Fabric covers
  26.1 - 26.1.2 and the 26.2 pre-release line; NeoForge covers 26.1.2 and 26.2.
- **No Forge** on 26.x (no Forge toolchain for unobfuscated Minecraft).
- **No Quilt:** ASR requires Fabric API, and Quilt retired Quilted Fabric API at 26.1, so the Fabric jar
  will not load on Quilt for the 26.x line (the only line ASR currently ships).
- The `1.20.x` / `1.21.x` branches are scaffolds (structure only, builds pending).
- Fabric builds require **Fabric API**; ModMenu is optional (config screen).

## Using it

Hold a shield in your main or off hand. Any hit that a manually-raised shield would block (melee, ranged, and most direct sources - not fire/fall/drowning/magic) is blocked automatically if it comes from your front 180-degree arc (horizontal); hits from behind still land. Each block plays the shield sound, swings the arm, and costs shield durability.

- **Durability cost** is server-controlled: an integer 0-10 (default 1; 0 = the shield never wears).
- **Config screen:** open it via **ModMenu** on Fabric or NeoForge's built-in mod **Config** button. The value is operator-only (permission level 2) - non-ops see it read-only; ops edit it and the server applies, clamps, persists (to `config/autoshield-reborn.json`), and syncs it to everyone.
- Adds **no blocks, items, or commands**.

## Downloads

- Releases: https://github.com/Kishku7/autoshield-reborn/releases
- Modrinth: https://modrinth.com/mod/autoshield-reborn
- Discord: https://discord.gg/2ZxzbCzAHe

By Kishku7. All Rights Reserved. A from-scratch rewrite of [agorasim20/autoshield](https://github.com/agorasim20/autoshield) (CC0-1.0).
