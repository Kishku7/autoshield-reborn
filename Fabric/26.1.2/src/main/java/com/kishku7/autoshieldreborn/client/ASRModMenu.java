package com.kishku7.autoshieldreborn.client;

import com.terraformersmc.modmenu.api.ConfigScreenFactory;
import com.terraformersmc.modmenu.api.ModMenuApi;

/**
 * ModMenu integration: puts the "Config" button on the Auto-Shield Reborn entry in ModMenu's mod
 * list, opening {@link ASRConfigScreen}. ModMenu is a suggested (soft) dependency - if it is not
 * installed, this entrypoint is simply never invoked and the mod still works (the JSON config and
 * server-side blocking are unaffected).
 */
public class ASRModMenu implements ModMenuApi {

    @Override
    public ConfigScreenFactory<?> getModConfigScreenFactory() {
        return ASRConfigScreen::new;
    }
}
