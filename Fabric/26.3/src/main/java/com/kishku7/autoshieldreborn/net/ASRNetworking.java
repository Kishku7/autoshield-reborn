package com.kishku7.autoshieldreborn.net;

import com.kishku7.autoshieldreborn.ASRConfig;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.permissions.Permissions;

/**
 * Common (server-side) networking for Auto-Shield Reborn.
 *
 * Registers both payload types and the server-side handlers. The durability value is
 * server-authoritative: only operators (gamemaster permission / op level 2 and above) may change
 * it, and any change is persisted and re-broadcast to every connected player. New joiners are sent
 * the current value so their config screen is accurate.
 */
public final class ASRNetworking {

    private ASRNetworking() {
    }

    public static void register() {
        PayloadTypeRegistry.serverboundPlay().register(SetDurabilityPayload.TYPE, SetDurabilityPayload.CODEC);
        PayloadTypeRegistry.clientboundPlay().register(SyncDurabilityPayload.TYPE, SyncDurabilityPayload.CODEC);

        ServerPlayNetworking.registerGlobalReceiver(SetDurabilityPayload.TYPE, (payload, context) -> {
            ServerPlayer player = context.player();
            // Operators only. The single-player host is an operator (level 4), so this passes there too.
            if (!player.permissions().hasPermission(Permissions.COMMANDS_GAMEMASTER)) {
                return;
            }
            int applied = ASRConfig.setDurabilityCost(payload.cost());
            MinecraftServer server = player.level().getServer();
            if (server != null) {
                for (ServerPlayer online : server.getPlayerList().getPlayers()) {
                    ServerPlayNetworking.send(online, new SyncDurabilityPayload(applied));
                }
            } else {
                ServerPlayNetworking.send(player, new SyncDurabilityPayload(applied));
            }
        });

        // Tell each joining player the authoritative current value.
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) ->
                ServerPlayNetworking.send(handler.player, new SyncDurabilityPayload(ASRConfig.durabilityCost())));
    }
}
