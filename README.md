# Auto-Shield Reborn (ASR)

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?logo=discord&logoColor=white)](https://discord.gg/NVcgJJRsx)


Automatic shield blocking for Minecraft. Hold a shield in **either hand** and you will automatically
block any attack a shield can normally block — melee, projectiles, and more — with no need to raise
it. Blocking only applies to threats from within a **180° frontal arc**: damage from behind still
lands. The durability your shield loses per blocked hit is **server-configurable (0–10, default 1)**.

Auto-Shield Reborn is a from-scratch rewrite and major expansion of
[agorasim20/autoshield](https://github.com/agorasim20/autoshield) (CC0-1.0). The original auto-blocked
**arrows only**; ASR blocks the full set of shield-blockable damage, adds the directional gate, the
configurable durability cost, an in-game config screen, and server-authoritative operator sync —
across Fabric and NeoForge on Minecraft 26.x. Credit and thanks to agorasim20 for the original idea.

## Features

- **Auto-block while holding a shield** in the main or off hand — no right-click needed.
- **Blocks everything a raised shield would** (mirrors vanilla's own blockable rule): melee, arrows,
  tridents, and other directional attacks. Fire, drowning, fall, magic, and starvation pass through,
  exactly as if you had manually raised the shield. Piercing arrows still bypass shields.
- **180° facing gate** — only blocks attacks from your forward hemisphere (horizontal head facing).
- **Server-set durability cost (0–10, default 1).** 0 means the shield never wears from auto-blocks.
- **In-game config screen** via ModMenu (Fabric) or the NeoForge mods-list "Config" button. Operators
  (and single-player hosts) change the value and it syncs to the server live and persists; everyone
  else sees it read-only.
- **Dedicated-server safe.** All blocking logic is server-authoritative — fully functional with no
  client installed (clients only add the config screen).

## Downloads

| Minecraft | File | Loaders |
|-----------|------|---------|
| 26.1.2 (Fabric also 26.1 / 26.1.1) | `autoshield-reborn-1.0.0+26.1.2.jar` — **one universal jar** | Fabric **and** NeoForge |
| 26.2 (incl. 26.2-rc-1) | `autoshield-reborn-1.0.0+26.2.jar` | Fabric |

The 26.1.2 download is a single merged jar that runs on **both** Fabric and NeoForge — just drop it in
`mods/`. NeoForge for 26.2 will be added once NeoForge ships a 26.2 build. On Fabric 26.2, ModMenu had
not yet published a 26.2-compatible release at time of writing — the JSON config and all blocking still
work without it.

Fabric builds need [Fabric API](https://modrinth.com/mod/fabric-api). ModMenu is optional (only for the
config screen).

## Configuration

The setting lives in `config/autoshield-reborn.json` on the server (or in single-player):

```json
{
  "durabilityCost": 1
}
```

`durabilityCost` is clamped to 0–10 — the durability a shield loses each time it auto-blocks a hit.
Change it in-game from the config screen (operators only on a server) or by editing this file.

## Source layout (branches)

- `main` — this landing page.
- `26.1.2` — source for the 26.1.2 universal release: `fabric/` (fabric-loom) and `neoforge/`
  (ModDevGradle), both JDK 25, mojmap-native (no Architectury). The release jar is the two built per
  the build step below and merged with [Forgix](https://github.com/PacifistMC/Forgix).
- `26.2` — `fabric/` source targeting 26.2-rc-1 (JDK 25, fabric-loom).

Each subproject builds with `./gradlew build`; jars land in `build/libs/`.

## License

All Rights Reserved. See `LICENSE`. (The CC0 origin permits relicensing derivatives; the original
agorasim20/autoshield remains available under CC0-1.0.)
