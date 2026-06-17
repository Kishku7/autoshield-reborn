# Auto-Shield Reborn - Fabric (Minecraft 26.1 - 26.1.2)

**Fabric** builds of Auto-Shield Reborn for the Minecraft 26.1 - 26.1.2 line. Client + server mod (server-authoritative). Fabric only - not built for Quilt (see below).
Standalone - no Architectury, no `common/` subproject.

## Builds

| Version | Minecraft | Java | Toolchain |
| --- | --- | --- | --- |
| [`26.1.2/`](26.1.2) | 26.1 - 26.1.2 | 25 | fabric-loom |

## Excluded / not built

- **Forge** is not built for the 26.x line - there is no Forge toolchain for unobfuscated Minecraft 26.x.
- **Quilt** is not offered - Auto-Shield Reborn currently ships only for the 26.x line, where Quilt is not viable: Quilt retired Quilted Fabric API at 26.1 and ASR requires Fabric API, so the Fabric jar will not load on Quilt for 26.x.

## Build

```
cd <version>
./gradlew build      # Windows: .\gradlew.bat build
```

Output: `build/libs/autoshield-reborn-*.jar`. Part of the [`26.1` branch](https://github.com/Kishku7/autoshield-reborn/tree/26.1).
