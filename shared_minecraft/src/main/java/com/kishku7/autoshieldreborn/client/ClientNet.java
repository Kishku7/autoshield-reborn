package com.kishku7.autoshieldreborn.client;

import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import java.util.function.Consumer;

/**
 * Loader-neutral C2S sender facade. Each loader's client init sets SENDER (Fabric
 * ClientPlayNetworking::send / NeoForge ClientPacketDistributor::sendToServer); shared client code
 * calls sendToServer(...) and stays loader-agnostic.
 */
public final class ClientNet {
    private ClientNet() {}

    public static volatile Consumer<CustomPacketPayload> SENDER = payload -> {};

    public static void sendToServer(CustomPacketPayload payload) {
        SENDER.accept(payload);
    }
}
