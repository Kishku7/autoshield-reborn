package com.kishku7.autoshieldreborn.client;

import net.neoforged.fml.ModContainer;
import net.neoforged.neoforge.client.gui.IConfigScreenFactory;

/**
 * Client-only NeoForge wiring: registers the "Config" button shown on the Auto-Shield Reborn entry
 * in the mods list, opening {@link ASRConfigScreen}. Kept in a separate client class so the
 * {@code IConfigScreenFactory} reference is never loaded on a dedicated server.
 */
public final class AutoShieldRebornNeoForgeClient {

    private AutoShieldRebornNeoForgeClient() {
    }

    public static void init(ModContainer mod) {
        // Concretely-typed instance disambiguates registerExtensionPoint(Class, T) from the
        // (Class, Supplier) overload.
        IConfigScreenFactory factory = (container, modListScreen) -> new ASRConfigScreen(modListScreen);
        mod.registerExtensionPoint(IConfigScreenFactory.class, factory);
    }
}
