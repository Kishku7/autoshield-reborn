package com.kishku7.autoshieldreborn;

import com.kishku7.autoshieldreborn.client.AutoShieldRebornNeoForgeClient;
import com.kishku7.autoshieldreborn.net.SetDurabilityPayload;
import com.kishku7.autoshieldreborn.net.SyncDurabilityPayload;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.permissions.Permissions;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.registration.PayloadRegistrar;

/**
 * Auto-Shield Reborn - NeoForge entrypoint.
 *
 * Loads the server-authoritative durability config, registers the two payloads, and wires the
 * server-side handlers. The blocking behaviour itself is the shared {@code mixin.AutoShieldMixin}.
 * The durability value is server-authoritative: only operators may change it (and the change is
 * persisted and broadcast). Joining players are sent the current value. Nothing on the server side
 * is client-only, so the mod is fully functional on dedicated servers; the client config screen is
 * registered separately in {@link AutoShieldRebornNeoForgeClient}.
 */
@Mod(AutoShieldReborn.MOD_ID)
public class AutoShieldRebornNeoForge {

    public AutoShieldRebornNeoForge(ModContainer mod, IEventBus bus, Dist dist) {
        ASRConfig.init(FMLPaths.CONFIGDIR.get());
        bus.addListener(this::registerPayloads);
        NeoForge.EVENT_BUS.addListener(this::onPlayerJoin);
        if (dist.isClient()) {
            AutoShieldRebornNeoForgeClient.init(mod);
        }
        AutoShieldReborn.LOGGER.info("[ASR] ready - durability cost per blocked hit: {}", ASRConfig.durabilityCost());
    }

    private void registerPayloads(RegisterPayloadHandlersEvent event) {
        PayloadRegistrar registrar = event.registrar(AutoShieldReborn.MOD_ID).versioned("1.0.0");

        registrar.playToClient(SyncDurabilityPayload.TYPE, SyncDurabilityPayload.CODEC,
                (payload, context) -> ASRConfig.setDurabilityCostNoSave(payload.cost()));

        registrar.playToServer(SetDurabilityPayload.TYPE, SetDurabilityPayload.CODEC, (payload, context) -> {
            if (context.player() instanceof ServerPlayer player
                    && player.permissions().hasPermission(Permissions.COMMANDS_GAMEMASTER)) {
                int applied = ASRConfig.setDurabilityCost(payload.cost());
                PacketDistributor.sendToAllPlayers(new SyncDurabilityPayload(applied));
            }
        });
    }

    private void onPlayerJoin(PlayerEvent.PlayerLoggedInEvent event) {
        if (event.getEntity() instanceof ServerPlayer player) {
            PacketDistributor.sendToPlayer(player, new SyncDurabilityPayload(ASRConfig.durabilityCost()));
        }
    }
}
