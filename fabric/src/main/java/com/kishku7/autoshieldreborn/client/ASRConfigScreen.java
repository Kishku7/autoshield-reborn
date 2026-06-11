package com.kishku7.autoshieldreborn.client;

import com.kishku7.autoshieldreborn.ASRConfig;
import com.kishku7.autoshieldreborn.net.SetDurabilityPayload;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.components.AbstractSliderButton;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.StringWidget;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.server.permissions.Permissions;

/**
 * Auto-Shield Reborn config screen, opened from ModMenu (Fabric) or the NeoForge mods "Config"
 * button. Shows the server's durability cost (0-10). Operators (and the single-player host) get an
 * editable slider whose value is sent to the server on Done; everyone else sees it read-only with a
 * "server-controlled" note. The value shown is whatever the server last synced to this client.
 *
 * Built entirely from widgets (no custom render override) so it is unaffected by the 26.x GUI
 * render-state pipeline change.
 */
public class ASRConfigScreen extends Screen {

    private final Screen parent;
    private boolean editable;
    private DurabilitySlider slider;

    public ASRConfigScreen(Screen parent) {
        super(Component.literal("Auto-Shield Reborn"));
        this.parent = parent;
    }

    @Override
    protected void init() {
        Minecraft mc = Minecraft.getInstance();
        this.editable = mc.player != null
                && mc.player.permissions().hasPermission(Permissions.COMMANDS_GAMEMASTER);

        int cx = this.width / 2;
        int y = this.height / 2 - 20;

        this.addRenderableWidget(new StringWidget(cx - 150, y - 52, 300, 12, this.title, this.font));
        if (!this.editable) {
            this.addRenderableWidget(new StringWidget(cx - 150, y - 36, 300, 12,
                    Component.literal("Server-controlled - operators only"), this.font));
        }

        this.slider = new DurabilitySlider(cx - 110, y, 220, 20, ASRConfig.durabilityCost());
        this.slider.active = this.editable;
        this.addRenderableWidget(this.slider);

        this.addRenderableWidget(Button.builder(Component.literal("Done"), b -> {
            if (this.editable && this.slider.getValue() != ASRConfig.durabilityCost()) {
                ClientPlayNetworking.send(new SetDurabilityPayload(this.slider.getValue()));
            }
            this.onClose();
        }).bounds(cx - 110, y + 44, 220, 20).build());
    }

    @Override
    public void onClose() {
        Minecraft.getInstance().gui.setScreen(this.parent);
    }

    /** A 0..MAX_COST integer slider. */
    private static final class DurabilitySlider extends AbstractSliderButton {

        DurabilitySlider(int x, int y, int width, int height, int initial) {
            super(x, y, width, height, Component.empty(),
                    ASRConfig.clamp(initial) / (double) ASRConfig.MAX_COST);
            this.updateMessage();
        }

        int getValue() {
            return (int) Math.round(this.value * ASRConfig.MAX_COST);
        }

        @Override
        protected void updateMessage() {
            setMessage(Component.literal("Shield durability cost per block: " + getValue()));
        }

        @Override
        protected void applyValue() {
            updateMessage();
        }
    }
}
