package com.kishku7.autoshieldreborn.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.Screen;

import java.lang.reflect.Field;
import java.lang.reflect.Method;

/**
 * Bridges the 26.1 -> 26.2 screen-open change so one ASRConfigScreen serves the whole 26.x line.
 * 26.1: Minecraft.setScreen(Screen). 26.2+: Minecraft.setScreen removed -> Minecraft.gui.setScreen(Screen).
 */
public final class ScreenCompat {
    private ScreenCompat() {}

    public static void setScreen(Screen screen) {
        Minecraft mc = Minecraft.getInstance();
        // 26.2+ path: gui.setScreen
        try {
            Field guiField = Minecraft.class.getField("gui");
            Object gui = guiField.get(mc);
            for (Method m : gui.getClass().getMethods()) {
                if (m.getName().equals("setScreen") && m.getParameterCount() == 1
                        && m.getParameterTypes()[0].isAssignableFrom(Screen.class)) {
                    m.invoke(gui, screen);
                    return;
                }
            }
        } catch (NoSuchFieldException ignored) {
            // 26.1 has no usable gui.setScreen route; fall through to Minecraft.setScreen.
        } catch (Exception e) {
            throw new RuntimeException("ASR setScreen via gui failed", e);
        }
        // 26.1 path: Minecraft.setScreen(Screen)
        try {
            Method m = Minecraft.class.getMethod("setScreen", Screen.class);
            m.invoke(mc, screen);
        } catch (Exception e) {
            throw new RuntimeException("ASR setScreen failed", e);
        }
    }
}
