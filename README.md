# Auto-Shield Reborn - branch `26.1`

Source for the Minecraft **26.1 - 26.1.2** line. Standalone `Fabric/` and `NeoForge/` build trees (one
subfolder per Minecraft version) - no Architectury, no `common/` subproject (MC 26.x is mojmap-native).
Client + server mod (server-authoritative; dedicated-server safe).

## Platforms

- [`Fabric/`](Fabric) - 1 build(s); see its README.
- [`NeoForge/`](NeoForge) - 1 build(s); see its README.

## Not supported on this line

- **Forge** is not built for the 26.x line - there is no Forge toolchain for unobfuscated Minecraft 26.x.
- **Quilt** is not offered - Auto-Shield Reborn currently ships only for the 26.x line, where Quilt is not viable: Quilt retired Quilted Fabric API at 26.1 and ASR requires Fabric API, so the Fabric jar will not load on Quilt for 26.x.

## Build

```
cd <Loader>/<version>
./gradlew build      # Windows: .\gradlew.bat build
```

Output: `build/libs/autoshield-reborn-*.jar`. Requires JDK 25 (Minecraft 26.x toolchain).

## Links

- Other branches: [`1.20.x`](https://github.com/Kishku7/autoshield-reborn/tree/1.20.x), [`1.21.x`](https://github.com/Kishku7/autoshield-reborn/tree/1.21.x), [`26.2`](https://github.com/Kishku7/autoshield-reborn/tree/26.2)
- Overview: [`main`](https://github.com/Kishku7/autoshield-reborn/tree/main)
- Modrinth: https://modrinth.com/mod/autoshield-reborn
- Releases: https://github.com/Kishku7/autoshield-reborn/releases

By Kishku7. All Rights Reserved. A from-scratch rewrite of [agorasim20/autoshield](https://github.com/agorasim20/autoshield) (CC0-1.0).
