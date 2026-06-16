# Auto-Shield Reborn (ASR)

An **auto-shield** mod for Minecraft - a **client + server** mod that automatically
blocks any shield-blockable hit coming from your frontal 180-degree arc while you hold a
shield in **either hand**, with no need to raise it. All blocking logic is
server-authoritative, so it works on dedicated servers even with no client installed
(the client only adds an in-game config screen). The per-hit durability cost is
server-configurable (0-10, default 1).

A from-scratch rewrite and major expansion of
[agorasim20/autoshield](https://github.com/agorasim20/autoshield) (CC0-1.0).

## Branches

| Branch    | Minecraft            | Status                |
|-----------|----------------------|-----------------------|
| `1.20.x`  | 1.20 line            | planned               |
| `1.21.x`  | 1.21 line            | planned               |
| `26.1`    | 26.1 - 26.1.2        | stable                |
| `26.2`    | 26.2                 | pre-release           |

Each MC-line branch carries standalone `Fabric/<version>` and `NeoForge/<version>` build
trees - **no Architectury, no common/ subproject** (MC 26.x is mojmap-native).

## Support

Fabric (and Quilt-compatible) plus NeoForge.

## Links

- Discord: https://discord.gg/2ZxzbCzAHe
- Modrinth: https://modrinth.com/mod/autoshield-reborn
- Releases: https://github.com/Kishku7/autoshield-reborn/releases

## License

See `LICENSE`.