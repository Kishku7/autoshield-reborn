package com.kishku7.autoshieldreborn.net;

import com.kishku7.autoshieldreborn.AutoShieldReborn;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;

/**
 * Client -> server: an operator (or single-player host) requests a new shield durability cost.
 * The server clamps it, applies it, persists it, and broadcasts the result back to everyone.
 * Requests from non-operators are dropped server-side.
 */
public record SetDurabilityPayload(int cost) implements CustomPacketPayload {

    public static final Type<SetDurabilityPayload> TYPE =
            new Type<>(Identifier.fromNamespaceAndPath(AutoShieldReborn.MOD_ID, "set_durability"));

    public static final StreamCodec<RegistryFriendlyByteBuf, SetDurabilityPayload> CODEC =
            StreamCodec.composite(ByteBufCodecs.VAR_INT, SetDurabilityPayload::cost, SetDurabilityPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
