package com.kishku7.autoshieldreborn;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Loader-agnostic configuration holder for Auto-Shield Reborn.
 *
 * Holds the single server-authoritative setting: {@code durabilityCost}, the amount of
 * durability a shield loses per blocked hit (0-10, default 1; 0 = the shield never wears).
 * Persisted as a small JSON file ({@code config/autoshield-reborn.json}) so the value
 * survives restarts. The per-loader entrypoint supplies the config directory via
 * {@link #init(Path)} - nothing here is tied to Fabric or NeoForge.
 */
public final class ASRConfig {
    public static final int MIN_COST = 0;
    public static final int MAX_COST = 10;
    public static final int DEFAULT_COST = 1;

    private static final String FILE_NAME = "autoshield-reborn.json";
    private static final String KEY_DURABILITY = "durabilityCost";
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    private static volatile int durabilityCost = DEFAULT_COST;
    private static Path file;

    private ASRConfig() {
    }

    /** Durability lost per blocked hit, clamped to [0, 10]. */
    public static int durabilityCost() {
        return durabilityCost;
    }

    public static int clamp(int value) {
        return Math.max(MIN_COST, Math.min(MAX_COST, value));
    }

    /**
     * Sets the value in memory (clamped) and persists it. Returns the value actually applied.
     * Server-authoritative callers (config screen via op, or single-player) use this.
     */
    public static int setDurabilityCost(int value) {
        durabilityCost = clamp(value);
        save();
        return durabilityCost;
    }

    /** Sets the in-memory value only (clamped), without writing to disk. Used for S2C sync on clients. */
    public static void setDurabilityCostNoSave(int value) {
        durabilityCost = clamp(value);
    }

    /** Resolve the config file under the given directory and load it (creating defaults if absent). */
    public static void init(Path configDir) {
        file = configDir.resolve(FILE_NAME);
        load();
    }

    private static void load() {
        if (file == null) {
            return;
        }
        try {
            if (Files.exists(file)) {
                JsonObject obj = GSON.fromJson(Files.readString(file), JsonObject.class);
                if (obj != null && obj.has(KEY_DURABILITY)) {
                    durabilityCost = clamp(obj.get(KEY_DURABILITY).getAsInt());
                }
            }
            save();
        } catch (Exception e) {
            AutoShieldReborn.LOGGER.warn("[ASR] could not read config, using default ({}): {}", DEFAULT_COST, e.toString());
            durabilityCost = DEFAULT_COST;
        }
    }

    private static void save() {
        if (file == null) {
            return;
        }
        try {
            JsonObject obj = new JsonObject();
            obj.addProperty(KEY_DURABILITY, durabilityCost);
            if (file.getParent() != null) {
                Files.createDirectories(file.getParent());
            }
            Files.writeString(file, GSON.toJson(obj));
        } catch (IOException e) {
            AutoShieldReborn.LOGGER.warn("[ASR] could not write config: {}", e.toString());
        }
    }
}
