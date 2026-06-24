package com.kishku7.autoshieldreborn.client;

import com.kishku7.autoshieldreborn.ASRConfig;
import com.kishku7.autoshieldreborn.net.SyncDurabilityPayload;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

/**
 * Client entrypoint. Keeps the local copy of the durability value in sync with the server so the
 * config screen always shows the authoritative number. The screen itself is opened from ModMenu
 * (see {@link ASRModMenu}).
 */
public class AutoShieldRebornClient implements ClientModInitializer {

    @Override
    public void onInitializeClient() {
        ClientPlayNetworking.registerGlobalReceiver(SyncDurabilityPayload.TYPE, (payload, context) ->
                ASRConfig.setDurabilityCostNoSave(payload.cost()));
    }
}
