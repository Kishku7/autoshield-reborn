package com.kishku7.autoshieldreborn;

import com.kishku7.autoshieldreborn.net.ASRNetworking;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.loader.api.FabricLoader;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Auto-Shield Reborn - common entrypoint (Fabric).
 *
 * Loads the server-authoritative durability config and registers networking. The blocking behavior
 * itself is driven by {@code mixin.AutoShieldMixin}, which runs inside the server-side damage path
 * ({@code LivingEntity.applyItemBlocking}). Nothing here is client-only, so the mod is fully
 * functional on dedicated servers.
 */
public class AutoShieldReborn implements ModInitializer {
    public static final String MOD_ID = "autoshield_reborn";
    public static final Logger LOGGER = LoggerFactory.getLogger("Auto-Shield Reborn");

    @Override
    public void onInitialize() {
        ASRConfig.init(FabricLoader.getInstance().getConfigDir());
        ASRNetworking.register();
        LOGGER.info("[ASR] ready - durability cost per blocked hit: {}", ASRConfig.durabilityCost());
    }
}
