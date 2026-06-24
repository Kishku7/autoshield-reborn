package com.kishku7.autoshieldreborn.net;

import com.kishku7.autoshieldreborn.AutoShieldReborn;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;

/**
 * Server -> client: the authoritative current durability cost. Sent on join and whenever the
 * value changes, so every client's config screen shows the truth.
 */
public record SyncDurabilityPayload(int cost) implements CustomPacketPayload {

    public static final Type<SyncDurabilityPayload> TYPE =
            new Type<>(Identifier.fromNamespaceAndPath(AutoShieldReborn.MOD_ID, "sync_durability"));

    public static final StreamCodec<RegistryFriendlyByteBuf, SyncDurabilityPayload> CODEC =
            StreamCodec.composite(ByteBufCodecs.VAR_INT, SyncDurabilityPayload::cost, SyncDurabilityPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
