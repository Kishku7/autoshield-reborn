# Auto-Shield Reborn - Minecraft 26.2 (source branch)

Automatically blocks shield-blockable hits from your frontal arc while you hold a shield in either hand.

This branch holds the **Minecraft 26.2** source. For the current stable release, see the
[26.1.2 branch](https://github.com/Kishku7/autoshield-reborn/tree/26.1.2).

MC 26.x is unobfuscated (mojmap-native), so there is no Architectury - two independent per-loader trees:

- `fabric/`   - fabric-loom.    Build: `cd fabric && ./gradlew build`
- `neoforge/` - ModDevGradle.   Build: `cd neoforge && ./gradlew build` (see the NeoForge note below)

## Fabric
Targets the MC 26.2 pre/rc line with Fabric API. Builds with the published Fabric 26.2 toolchain - no extra setup.

## NeoForge - requires a locally built NeoForge 26.2 (alpha)
NeoForge has not published a 26.2 build, so `neoforge/` depends on a NeoForge 26.2 that you build yourself
and publish to your local Maven. One time:

1. `git clone --branch port/26.2 https://github.com/neoforged/NeoForge`
2. Install **JDK 25** (the JDK the `port/26.2` branch requires).
3. Build it and publish to your local Maven:

       ./gradlew setup
       ./gradlew :neoforge:publishToMavenLocal --no-configuration-cache

   This publishes `net.neoforged:neoforge:26.2.0-alpha.0+<suffix>` into `~/.m2` (the suffix is timestamped).
4. Set that exact version in `neoforge/gradle.properties` (`neo_version`), then `cd neoforge && ./gradlew build`.
   (`neoforge/build.gradle` already includes `mavenLocal()`.)

To **run** the NeoForge build, install that same locally built NeoForge (its `*-installer.jar`) into your
launcher - there is no public NeoForge 26.2 to install yet.

## Downloads (Modrinth, beta)
https://modrinth.com/mod/autoshield-reborn