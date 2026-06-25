# Auto-Shield Reborn -- MC 26.x (unified line)

Auto-blocks shield-blockable damage while holding a shield (either hand), with a facing gate and
server-configurable durability cost. Client+server; one source tree builds every 26.x version on both loaders.

Layout (shared standard):
- shared_minecraft/ -- MC-coupled core + mixin + payloads + the shared config screen
  (ASRConfig, AutoShieldMixin, Set/SyncDurabilityPayload, ASRConfigScreen, plus a ClientNet sender
  facade and a reflective ScreenCompat setScreen bridge so one screen serves 26.1->26.3). srcDir'd per loader.
- Fabric/ -- entrypoint + ModMenu hook + payload registration (ASRNetworking) + client init + fabric.mod.json.
- NeoForge/ -- entrypoint + @Mod wiring + config-screen factory + client init + neoforge.mods.toml.

Build: `pwsh build-all-fabric.ps1` (26.1.2/26.2/26.3-snapshot-1) / `pwsh build-all-neoforge.ps1` (26.1.2/26.2).
