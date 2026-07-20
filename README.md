# Auto-Shield Reborn

Hold a shield in **either hand** and you automatically block any hit a raised shield would normally
block - no need to raise it. All blocking is server-authoritative, so it works on dedicated servers
even for players who do not have the mod installed.

## Why Auto-Shield Reborn

- **Block without raising.** Melee, projectiles, and most direct damage from your front 180-degree arc
  (horizontal) are blocked automatically while a shield is in your main or off hand; hits from behind
  still land, and shield-bypassing damage (fire, fall, drowning, magic, starvation) passes through -
  exactly like a manually-raised shield.
- **Server-authoritative + fair.** The per-hit shield durability cost is server-configurable (0-10,
  default 1; 0 = the shield never wears). Operators set it; everyone else sees it read-only.
- **Lightweight.** Adds no blocks, items, or commands. Install it on a server for the behaviour;
  install it on clients too for the in-game config screen.

## Usage

Hold a shield. Each automatic block plays the shield sound, swings your arm, and chips the shield by
the configured cost. Open the config screen from **ModMenu** (Fabric) or the **Config** button on the
mod-list entry (Forge / NeoForge); operators edit the durability cost and the server clamps, persists,
and syncs it to everyone.

Ships as a **Fabric, Forge, and NeoForge** mod (client + server).

- Source code: https://github.com/Kishku7/autoshield-reborn/tree/minecraft-1.20-26.3
- Report issues / Support: https://github.com/Kishku7/mod_support/issues

By Kishku7. All Rights Reserved. A from-scratch rewrite of
[agorasim20/autoshield](https://github.com/agorasim20/autoshield) (CC0-1.0).
