package com.kishku7.autoshieldreborn;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Shared constants for Auto-Shield Reborn (NeoForge build). The NeoForge entrypoint is
 * {@link AutoShieldRebornNeoForge}; this class only holds the mod id and logger that the
 * loader-neutral classes (config, payloads, mixin) reference.
 */
public final class AutoShieldReborn {
    public static final String MOD_ID = "autoshield_reborn";
    public static final Logger LOGGER = LoggerFactory.getLogger("Auto-Shield Reborn");

    private AutoShieldReborn() {
    }
}
