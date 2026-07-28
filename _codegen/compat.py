"""Auto-Shield Reborn cross-version "era brain" for Cog code generation.

Given an MC version string (mcver) and loader, returns the correct WHOLE-FILE source for each
drift point. Cog source files are thin: a single //[[[cog ... //]]] block that calls one of the
emit_* helpers here, so ONE set of cog_sources direct-compiles correctly for every MC version the
mod claims. Direct-compile (Cog) rather than reflection because pre-26 Fabric runs on the
intermediary runtime -- reflection-by-mojmap-name misses there; Cog emits the correct mojmap symbol
as real source, which loom then remaps at build time.

The 26 master is the reference: emit_* reproduce the shipped 26 code byte-for-byte (comment-agnostic)
for v >= 26. Verification is comment-agnostic, so javadoc here is uniform/clean and need not match the
per-era shipped javadocs (some of which had copy/paste errors).

ASCII-only. Plain Python stdlib. Whole-file emitters return the ENTIRE .java file starting at column 0.

Drift axes (docs/COG-SPEC.md):
  blocking hook : applyItemBlocking (component: v>=26 or v==1.21.11) | hurtServer (1.21.2..1.21.8) |
                  hurt (<=1.21.1, 1.20.x)
  bypass check  : bypassedBy().map(tag -> tag.contains(source.typeHolder())) (v>=26) vs .map(source::is) (1.21.11)
  durability    : Consumer/broadcastBreakEvent (1.20.1) | EquipmentSlot (1.20.6/1.21.1/1.21.5/1.21.8) |
                  InteractionHand (component)
  view vector   : manual yaw math (1.20.1, calculateViewVector protected) | calculateViewVector (else)
  arrow pkg     : projectile.arrow (v>=26 or v==1.21.11) | projectile (else)
  net register  : serverboundPlay/clientboundPlay (v>=26) | playC2S/playS2C (1.20.6..1.21.11) |
                  FriendlyByteBuf channel (1.20.1, no payload API)
  identifier    : Identifier.fromNamespaceAndPath (v>=26) | ResourceLocation.fromNamespaceAndPath
                  (1.21.x) | new ResourceLocation (1.20.6)
  permission    : permissions().hasPermission(COMMANDS_GAMEMASTER) (v>=26 or v==1.21.11) | hasPermissions(2) (else)
"""

import sys

MOD_ID = "autoshield_reborn"


# ---------------------------------------------------------------------------
# Version parsing + era predicates
# ---------------------------------------------------------------------------

def _parse(mcver):
    """Parse an MC version string into a comparable (major, minor, patch) tuple.
    Drops a trailing -snapshot/-pre/-rc qualifier; the numeric prefix decides the era."""
    core = str(mcver).strip()
    for sep in ("-", "+", " "):
        if sep in core:
            core = core.split(sep, 1)[0]
    parts = []
    for tok in core.split("."):
        num = ""
        for ch in tok:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_26(mcver):
    """True on the 26.x line (major >= 26): the master shape."""
    return _parse(mcver)[0] >= 26


def is_component(mcver):
    """Component-blocking era: v >= 26 OR v == 1.21.11 (ASR uses the 26.1-era component path at 1.21.11)."""
    v = _parse(mcver)
    return v[0] >= 26 or v == (1, 21, 11)


def uses_hurtserver(mcver):
    """Legacy hurtServer(ServerLevel,...) entry: 1.21.2 <= v < 1.21.9 (in ASR's matrix: 1.21.5, 1.21.8)."""
    v = _parse(mcver)
    return not is_component(mcver) and (1, 21, 2) <= v < (1, 21, 11)  # extended to 1.21.9/1.21.10: hurtServer(ServerLevel,DamageSource,float) is byte-identical through 1.21.10; component path is 1.21.11+. (Level.isClientSide went private at 1.21.9 but the hurtServer path never touches that field.)


def uses_hurt(mcver):
    """Legacy hurt(DamageSource,float) entry: <= 1.21.1 and the 1.20.x line (1.20.1, 1.20.6, 1.21.1)."""
    return not is_component(mcver) and not uses_hurtserver(mcver)


def manual_view(mcver):
    """Compute the horizontal view from yaw manually (identical to calculateViewVector(0,yaw)):
    on 1.20.1 calculateViewVector is protected; on 26.x it triggers an -Xlint [static] warning. Both
    use the manual form. 1.21.x keeps self.calculateViewVector (byte-transparent with the shipped jars)."""
    return (1, 20, 0) <= _parse(mcver) < (1, 20, 5) or is_26(mcver)


def durability_kind(mcver):
    """consumer (1.20.1) | hand (component) | slot (else)."""
    if (1, 20, 0) <= _parse(mcver) < (1, 20, 5):
        return "consumer"
    if is_component(mcver):
        return "hand"
    return "slot"


def arrow_package(mcver):
    """AbstractArrow package: projectile.arrow (component era) vs projectile (legacy)."""
    if is_component(mcver):
        return "net.minecraft.world.entity.projectile.arrow"
    return "net.minecraft.world.entity.projectile"


def has_payload_api(mcver):
    """The custom-payload API (records + PayloadTypeRegistry) exists from MC 1.20.5. 1.20.1 has none."""
    return _parse(mcver) >= (1, 20, 5)


def modern_permission(mcver):
    """permissions().hasPermission(COMMANDS_GAMEMASTER) from the component era; hasPermissions(2) below."""
    return is_component(mcver)


def identifier_expr(mcver, path):
    """Expression constructing the mod Identifier/ResourceLocation for a payload channel path."""
    if _parse(mcver) >= (1, 21, 11):
        return 'Identifier.fromNamespaceAndPath(AutoShieldReborn.MOD_ID, "%s")' % path
    if _parse(mcver) >= (1, 21, 0):
        return 'ResourceLocation.fromNamespaceAndPath(AutoShieldReborn.MOD_ID, "%s")' % path
    return 'new ResourceLocation(AutoShieldReborn.MOD_ID, "%s")' % path


def _identifier_import(mcver):
    if _parse(mcver) >= (1, 21, 11):
        return "import net.minecraft.resources.Identifier;"
    return "import net.minecraft.resources.ResourceLocation;"
# (fromNamespaceAndPath used from 1.20.5; new ResourceLocation only on 1.20.1)


def compat_level(mcver):
    """mixins.json compatibilityLevel / javac release: JAVA_17 (<1.20.5) / JAVA_21 (1.20.5..1.21.x) /
    JAVA_25 (>=26)."""
    v = _parse(mcver)
    if v < (1, 20, 5):
        return "JAVA_17"
    if v[0] >= 26:
        return "JAVA_25"
    return "JAVA_21"


def java_release(mcver):
    """javac --release for this cell: 17 / 21 / 25 (mirrors compat_level)."""
    return {"JAVA_17": "17", "JAVA_21": "21", "JAVA_25": "25"}[compat_level(mcver)]


def forge_needs_refmap(mcver):
    """Classic-SRG Forge (FG6) runs SRG-mapped at runtime up to 1.20.4 -> mixin refmap key MANDATORY;
    from 1.20.6 (official mappings) it must be ABSENT. Loader-specific (cog-gen only calls on -Loader Forge)."""
    v = _parse(mcver)
    return v[0] == 1 and v[1] == 20 and v[2] < 5


# ---------------------------------------------------------------------------
# Mixin -- the whole AutoShieldMixin.java (the heart of the mod)
# ---------------------------------------------------------------------------

def datapack_format(mcver):
    """pack.mcmeta pack_format for this MC version (Forge 56+/58 requires the mod to ship a
    pack.mcmeta or its datapack never finishes loading -> LootModifierManager world-tick crash,
    seen on Forge 1.21.8). Values are representative; the emitted mcmeta also carries a wide
    supported_formats range so the exact int is non-critical."""
    v = _parse(mcver)
    if v[0] >= 26:
        return 88
    if v < (1, 20, 5):
        return 15
    if v < (1, 21, 0):
        return 41
    if v < (1, 21, 2):
        return 48
    if v < (1, 21, 6):
        return 71
    return 81

def resource_format(mcver):
    """RESOURCE pack_format for a 26.x version, or None below 26.

    26.x is a different regime from datapack_format() above: a 26.x jar must ship the
    EXACT-SINGLE RANGE form (pack_format = min_format = max_format = <resource major>).
    A plain int > 81 FATALs the NeoForge dedicated-server datapack load, and the pre-26
    "supported_formats" shape is rejected outright. Values are the resource major read out
    of each line's SharedConstants (authority: Memory/knowledge/pack-formats.md):
    26.1 -> 84, 26.2 -> 88, 26.3 -> 94 (snapshot-6; earlier 26.3 snapshots were 89-93).
    """
    v = _parse(mcver)
    if v[0] < 26:
        return None
    line = v[1] if len(v) > 1 else 0
    return {1: 84, 2: 88, 3: 94}.get(line, 94)


_MIXIN_HEAD = "package com.kishku7.autoshieldreborn.mixin;\n\nimport com.kishku7.autoshieldreborn.ASRConfig;\n\n"


def _mixin_imports(mcver):
    v = _parse(mcver)
    lines = []
    if is_component(mcver):
        lines.append("import net.minecraft.core.component.DataComponents;")
        lines.append("import net.minecraft.server.level.ServerLevel;")
    elif uses_hurtserver(mcver):
        lines.append("import net.minecraft.server.level.ServerLevel;")
    lines.append("import net.minecraft.sounds.SoundEvents;")
    lines.append("import net.minecraft.sounds.SoundSource;")
    lines.append("import net.minecraft.world.InteractionHand;")
    if durability_kind(mcver) == "slot":
        lines.append("import net.minecraft.world.entity.EquipmentSlot;")
    lines.append("import net.minecraft.world.damagesource.DamageSource;")
    lines.append("import net.minecraft.world.entity.LivingEntity;")
    lines.append("import net.minecraft.world.entity.player.Player;")
    lines.append("import %s.AbstractArrow;" % arrow_package(mcver))
    lines.append("import net.minecraft.world.item.ItemStack;")
    if is_component(mcver):
        lines.append("import net.minecraft.world.item.component.BlocksAttacks;")
    else:
        lines.append("import net.minecraft.world.item.ShieldItem;")
    lines.append("import net.minecraft.world.phys.Vec3;")
    lines.append("")
    lines.append("import org.spongepowered.asm.mixin.Mixin;")
    lines.append("import org.spongepowered.asm.mixin.injection.At;")
    lines.append("import org.spongepowered.asm.mixin.injection.Inject;")
    lines.append("import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;")
    return "\n".join(lines)


def _mixin_view_block(mcver):
    if manual_view(mcver):
        return ("        double yawRad = Math.toRadians(self.getYHeadRot());\n"
                "        Vec3 view = new Vec3(-Math.sin(yawRad), 0.0, Math.cos(yawRad));")
    return "        Vec3 view = self.calculateViewVector(0.0F, self.getYHeadRot());"


def _mixin_level_ref(mcver):
    # component + hurtServer expose the ServerLevel param `level`; hurt uses self.level().
    return "level" if (is_component(mcver) or uses_hurtserver(mcver)) else "self.level()"


def _mixin_durability_block(mcver):
    k = durability_kind(mcver)
    if k == "hand":
        return "            shield.hurtAndBreak(cost, self, hand);"
    if k == "consumer":
        return "            shield.hurtAndBreak(cost, self, e -> e.broadcastBreakEvent(hand));"
    return ("            EquipmentSlot slot = (hand == InteractionHand.OFF_HAND) ? EquipmentSlot.OFFHAND : EquipmentSlot.MAINHAND;\n"
            "            shield.hurtAndBreak(cost, self, slot);")


def _mixin_feedback_and_end(mcver):
    lvl = _mixin_level_ref(mcver)
    ret = "cir.setReturnValue(damage);" if is_component(mcver) else "cir.setReturnValue(false);"
    return (
        "        // Auto-block: fully negate the damage with feedback and the configured durability cost.\n"
        "        ItemStack shield = player.getItemInHand(hand);\n"
        "        %s.playSound(null, player.getX(), player.getY(), player.getZ(),\n"
        "                SoundEvents.SHIELD_BLOCK, SoundSource.PLAYERS, 1.0F,\n"
        "                0.8F + %s.getRandom().nextFloat() * 0.4F);\n"
        "        player.swing(hand, true);\n"
        "        int cost = ASRConfig.durabilityCost();\n"
        "        if (cost > 0) {\n"
        "%s\n"
        "        }\n"
        "        %s\n"
        "    }\n"
        "}\n" % (lvl, lvl, _mixin_durability_block(mcver), ret)
    )


def _mixin_arc_block(mcver):
    return (
        "        // Directional gate: must have a source position, and it must be within the forward 180 degrees.\n"
        "        Vec3 sourcePos = source.getSourcePosition();\n"
        "        if (sourcePos == null) {\n"
        "            return;\n"
        "        }\n"
        "%s\n"
        "        Vec3 toSource = sourcePos.subtract(self.position());\n"
        "        toSource = new Vec3(toSource.x, 0.0, toSource.z).normalize();\n"
        "        if (toSource.dot(view) < 0.0) {\n"
        "            return; // source is behind the player -> not blocked\n"
        "        }\n\n" % _mixin_view_block(mcver)
    )


def _mixin_piercing_block():
    return (
        "        // Piercing arrows go through shields.\n"
        "        if (source.getDirectEntity() instanceof AbstractArrow arrow && arrow.getPierceLevel() > 0) {\n"
        "            return;\n"
        "        }\n\n"
    )


def mixin_source(mcver, loader=None):
    """The whole AutoShieldMixin.java for this MC version."""
    out = [_MIXIN_HEAD + _mixin_imports(mcver) + "\n\n"]
    out.append("/**\n"
               " * Auto-Shield Reborn - server-side auto-block. Hold a shield in either hand and any\n"
               " * shield-blockable hit from a 180-degree frontal arc is negated (durability cost applied).\n"
               " * Cog-generated per MC version from _codegen/compat.py.\n"
               " */\n")
    out.append("@Mixin(LivingEntity.class)\n")
    out.append("public abstract class AutoShieldMixin {\n\n")

    if is_component(mcver):
        out.append('    @Inject(method = "applyItemBlocking", at = @At("HEAD"), cancellable = true)\n')
        out.append("    private void asr$autoBlock(ServerLevel level, DamageSource source, float damage, CallbackInfoReturnable<Float> cir) {\n")
        out.append("        LivingEntity self = (LivingEntity) (Object) this;\n")
        out.append("        if (damage <= 0.0F || !(self instanceof Player player)) {\n            return;\n        }\n")
        out.append("        // If the player is genuinely raising a shield, let vanilla handle it normally.\n")
        out.append("        if (self.getItemBlockingWith() != null) {\n            return;\n        }\n\n")
        out.append("        // Find a shield (any item with the blocks_attacks component) in either hand; prefer the offhand.\n")
        out.append("        InteractionHand hand;\n        BlocksAttacks blocksAttacks;\n")
        out.append("        ItemStack offHand = player.getOffhandItem();\n        ItemStack mainHand = player.getMainHandItem();\n")
        out.append("        BlocksAttacks offBlocks = offHand.get(DataComponents.BLOCKS_ATTACKS);\n")
        out.append("        BlocksAttacks mainBlocks = mainHand.get(DataComponents.BLOCKS_ATTACKS);\n")
        out.append("        if (offBlocks != null) {\n            hand = InteractionHand.OFF_HAND;\n            blocksAttacks = offBlocks;\n")
        out.append("        } else if (mainBlocks != null) {\n            hand = InteractionHand.MAIN_HAND;\n            blocksAttacks = mainBlocks;\n")
        out.append("        } else {\n            return;\n        }\n\n")
        out.append("        // This damage type bypasses the shield (mirror vanilla's per-item bypassedBy set).\n")
        if is_26(mcver):
            out.append("        if (blocksAttacks.bypassedBy().map(tag -> tag.contains(source.typeHolder())).orElse(false)) {\n            return;\n        }\n")
        else:
            out.append("        if (blocksAttacks.bypassedBy().map(source::is).orElse(false)) {\n            return;\n        }\n")
        out.append(_mixin_piercing_block())
        out.append(_mixin_arc_block(mcver))
        out.append(_mixin_feedback_and_end(mcver))
        return "".join(out)

    # legacy (hurt / hurtServer)
    if uses_hurtserver(mcver):
        out.append('    @Inject(method = "hurtServer", at = @At("HEAD"), cancellable = true)\n')
        out.append("    private void asr$autoBlock(ServerLevel level, DamageSource source, float damage, CallbackInfoReturnable<Boolean> cir) {\n")
        out.append("        LivingEntity self = (LivingEntity) (Object) this;\n")
    else:
        out.append('    @Inject(method = "hurt", at = @At("HEAD"), cancellable = true)\n')
        out.append("    private void asr$autoBlock(DamageSource source, float damage, CallbackInfoReturnable<Boolean> cir) {\n")
        out.append("        LivingEntity self = (LivingEntity) (Object) this;\n")
        out.append("        if (self.level().isClientSide) {\n            return;\n        }\n")
    out.append("        if (damage <= 0.0F || !(self instanceof Player player) || !player.isAlive()) {\n            return;\n        }\n")
    out.append("        // If the player is genuinely raising a shield, let vanilla handle it normally.\n")
    out.append("        if (self.isBlocking()) {\n            return;\n        }\n\n")
    out.append("        // Find a shield in either hand; prefer the offhand.\n")
    # 1.20.1's durability Consumer lambda captures `hand`, so it must be (effectively) final there.
    out.append("        final InteractionHand hand;\n" if durability_kind(mcver) == "consumer" else "        InteractionHand hand;\n")
    out.append("        ItemStack offHand = player.getOffhandItem();\n        ItemStack mainHand = player.getMainHandItem();\n")
    out.append("        if (offHand.getItem() instanceof ShieldItem) {\n            hand = InteractionHand.OFF_HAND;\n")
    out.append("        } else if (mainHand.getItem() instanceof ShieldItem) {\n            hand = InteractionHand.MAIN_HAND;\n")
    out.append("        } else {\n            return;\n        }\n\n")
    out.append(_mixin_piercing_block())
    out.append(_mixin_arc_block(mcver))
    out.append(_mixin_feedback_and_end(mcver))
    return "".join(out)


# ---------------------------------------------------------------------------
# Payloads -- SetDurabilityPayload / SyncDurabilityPayload (present only where has_payload_api)
# ---------------------------------------------------------------------------

def payload_source(kind, mcver):
    """kind = 'set' | 'sync'. Whole record file. Only emitted where has_payload_api (>=1.20.5)."""
    if kind == "set":
        cls, path = "SetDurabilityPayload", "set_durability"
        doc = ("Client -> server: an operator (or single-player host) requests a new shield durability cost.\n"
               " * The server clamps it, applies it, persists it, and broadcasts the result back to everyone.")
    else:
        cls, path = "SyncDurabilityPayload", "sync_durability"
        doc = ("Server -> client: the authoritative current durability cost. Sent on join and whenever the\n"
               " * value changes, so every client's config screen shows the truth.")
    # `new ResourceLocation(ns,path)` is deprecated-for-removal on Forge's official mappings (<1.21);
    # it is the only cross-loader form there (Fabric/NeoForge 1.20.6 lack fromNamespaceAndPath).
    suppress = '@SuppressWarnings("removal")\n' if _parse(mcver) < (1, 21, 0) else ""
    return (
        "package com.kishku7.autoshieldreborn.net;\n\n"
        "import com.kishku7.autoshieldreborn.AutoShieldReborn;\n\n"
        "import net.minecraft.network.RegistryFriendlyByteBuf;\n"
        "import net.minecraft.network.codec.ByteBufCodecs;\n"
        "import net.minecraft.network.codec.StreamCodec;\n"
        "import net.minecraft.network.protocol.common.custom.CustomPacketPayload;\n"
        "%s\n\n"
        "/** %s */\n"
        "%spublic record %s(int cost) implements CustomPacketPayload {\n\n"
        "    public static final Type<%s> TYPE =\n"
        "            new Type<>(%s);\n\n"
        "    public static final StreamCodec<RegistryFriendlyByteBuf, %s> CODEC =\n"
        "            StreamCodec.composite(ByteBufCodecs.VAR_INT, %s::cost, %s::new);\n\n"
        "    @Override\n"
        "    public Type<? extends CustomPacketPayload> type() {\n"
        "        return TYPE;\n"
        "    }\n"
        "}\n" % (_identifier_import(mcver), doc, suppress, cls, cls, identifier_expr(mcver, path), cls, cls, cls)
    )


# ---------------------------------------------------------------------------
# Networking -- the whole ASRNetworking.java (server-side register)
# ---------------------------------------------------------------------------

def _net_channel_source(mcver):
    """1.20.1 only: no custom-payload API -> classic ResourceLocation channel + FriendlyByteBuf."""
    return (
        "package com.kishku7.autoshieldreborn.net;\n\n"
        "import com.kishku7.autoshieldreborn.ASRConfig;\n"
        "import com.kishku7.autoshieldreborn.AutoShieldReborn;\n\n"
        "import net.fabricmc.fabric.api.networking.v1.PacketByteBufs;\n"
        "import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;\n"
        "import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;\n"
        "import net.minecraft.network.FriendlyByteBuf;\n"
        "import net.minecraft.resources.ResourceLocation;\n"
        "import net.minecraft.server.level.ServerPlayer;\n\n"
        "/** Server-side networking (1.20.1 classic channel): op-gated set + broadcast + join-sync. */\n"
        "public final class ASRNetworking {\n\n"
        "    public static final ResourceLocation SET_DURABILITY = new ResourceLocation(AutoShieldReborn.MOD_ID, \"set_durability\");\n"
        "    public static final ResourceLocation SYNC_DURABILITY = new ResourceLocation(AutoShieldReborn.MOD_ID, \"sync_durability\");\n\n"
        "    private ASRNetworking() {\n    }\n\n"
        "    public static void register() {\n"
        "        ServerPlayNetworking.registerGlobalReceiver(SET_DURABILITY, (server, player, handler, buf, responseSender) -> {\n"
        "            int requested = buf.readVarInt();\n"
        "            server.execute(() -> {\n"
        "                if (!player.hasPermissions(2)) {\n                    return;\n                }\n"
        "                int applied = ASRConfig.setDurabilityCost(requested);\n"
        "                for (ServerPlayer online : server.getPlayerList().getPlayers()) {\n"
        "                    FriendlyByteBuf out = PacketByteBufs.create();\n"
        "                    out.writeVarInt(applied);\n"
        "                    ServerPlayNetworking.send(online, SYNC_DURABILITY, out);\n"
        "                }\n"
        "            });\n"
        "        });\n\n"
        "        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {\n"
        "            FriendlyByteBuf buf = PacketByteBufs.create();\n"
        "            buf.writeVarInt(ASRConfig.durabilityCost());\n"
        "            sender.sendPacket(SYNC_DURABILITY, buf);\n"
        "        });\n"
        "    }\n}\n"
    )


def net_source(mcver, loader=None):
    """The whole ASRNetworking.java for this MC version (Fabric server-side)."""
    if not has_payload_api(mcver):
        return _net_channel_source(mcver)
    c2s, s2c = ("serverboundPlay", "clientboundPlay") if is_26(mcver) else ("playC2S", "playS2C")
    perm = ("player.permissions().hasPermission(Permissions.COMMANDS_GAMEMASTER)"
            if modern_permission(mcver) else "player.hasPermissions(2)")
    imports = [
        "import com.kishku7.autoshieldreborn.ASRConfig;",
        "",
        "import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;",
        "import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;",
        "import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;",
        "import net.minecraft.server.MinecraftServer;",
        "import net.minecraft.server.level.ServerPlayer;",
    ]
    if modern_permission(mcver):
        imports.append("import net.minecraft.server.permissions.Permissions;")
    return (
        "package com.kishku7.autoshieldreborn.net;\n\n"
        + "\n".join(imports) + "\n\n"
        "/** Server-side networking: op-gated set + broadcast + join-sync of the durability cost. */\n"
        "public final class ASRNetworking {\n\n"
        "    private ASRNetworking() {\n    }\n\n"
        "    public static void register() {\n"
        "        PayloadTypeRegistry." + c2s + "().register(SetDurabilityPayload.TYPE, SetDurabilityPayload.CODEC);\n"
        "        PayloadTypeRegistry." + s2c + "().register(SyncDurabilityPayload.TYPE, SyncDurabilityPayload.CODEC);\n\n"
        "        ServerPlayNetworking.registerGlobalReceiver(SetDurabilityPayload.TYPE, (payload, context) -> {\n"
        "            ServerPlayer player = context.player();\n"
        "            if (!" + perm + ") {\n                return;\n            }\n"
        "            int applied = ASRConfig.setDurabilityCost(payload.cost());\n"
        "            MinecraftServer server = player.level().getServer();\n"
        "            if (server != null) {\n"
        "                for (ServerPlayer online : server.getPlayerList().getPlayers()) {\n"
        "                    ServerPlayNetworking.send(online, new SyncDurabilityPayload(applied));\n"
        "                }\n"
        "            } else {\n"
        "                ServerPlayNetworking.send(player, new SyncDurabilityPayload(applied));\n"
        "            }\n"
        "        });\n\n"
        "        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) ->\n"
        "                ServerPlayNetworking.send(handler.player, new SyncDurabilityPayload(ASRConfig.durabilityCost())));\n"
        "    }\n}\n"
    )


# ---------------------------------------------------------------------------
# Entrypoints (per loader, D15) + client
# ---------------------------------------------------------------------------

def fabric_entrypoint(mcver=None):
    """Fabric main entrypoint AutoShieldReborn.java (ModInitializer + MOD_ID + LOGGER). Invariant."""
    return (
        "package com.kishku7.autoshieldreborn;\n\n"
        "import com.kishku7.autoshieldreborn.net.ASRNetworking;\n\n"
        "import net.fabricmc.api.ModInitializer;\n"
        "import net.fabricmc.loader.api.FabricLoader;\n\n"
        "import org.slf4j.Logger;\n"
        "import org.slf4j.LoggerFactory;\n\n"
        "/** Auto-Shield Reborn - Fabric entrypoint. Loads config + registers server-side networking. */\n"
        "public class AutoShieldReborn implements ModInitializer {\n"
        "    public static final String MOD_ID = \"autoshield_reborn\";\n"
        "    public static final Logger LOGGER = LoggerFactory.getLogger(\"Auto-Shield Reborn\");\n\n"
        "    @Override\n"
        "    public void onInitialize() {\n"
        "        ASRConfig.init(FabricLoader.getInstance().getConfigDir());\n"
        "        ASRNetworking.register();\n"
        "        LOGGER.info(\"[ASR] ready - durability cost per blocked hit: {}\", ASRConfig.durabilityCost());\n"
        "    }\n}\n"
    )


def neoforge_constants(mcver=None):
    """NeoForge constants holder AutoShieldReborn.java (the @Mod class is AutoShieldRebornNeoForge)."""
    return (
        "package com.kishku7.autoshieldreborn;\n\n"
        "import org.slf4j.Logger;\n"
        "import org.slf4j.LoggerFactory;\n\n"
        "/** Shared constants for the NeoForge build (mod id + logger). Entrypoint = AutoShieldRebornNeoForge. */\n"
        "public final class AutoShieldReborn {\n"
        "    public static final String MOD_ID = \"autoshield_reborn\";\n"
        "    public static final Logger LOGGER = LoggerFactory.getLogger(\"Auto-Shield Reborn\");\n\n"
        "    private AutoShieldReborn() {\n    }\n}\n"
    )


# --- client: screen close + permission drift ---

def _perm_editable(mcver):
    if modern_permission(mcver):
        return "mc.player != null\n                && mc.player.permissions().hasPermission(Permissions.COMMANDS_GAMEMASTER)"
    return "mc.player != null && mc.player.hasPermissions(2)"


def _screen_close_call(mcver):
    v = _parse(mcver)
    if v[0] >= 26 and v >= (26, 2):
        return "Minecraft.getInstance().gui.setScreen(this.parent);"
    return "Minecraft.getInstance().setScreen(this.parent);"


_SLIDER_INNER = (
    "    /** A 0..MAX_COST integer slider. */\n"
    "    private static final class DurabilitySlider extends AbstractSliderButton {\n\n"
    "        DurabilitySlider(int x, int y, int width, int height, int initial) {\n"
    "            super(x, y, width, height, Component.empty(),\n"
    "                    ASRConfig.clamp(initial) / (double) ASRConfig.MAX_COST);\n"
    "            this.updateMessage();\n"
    "        }\n\n"
    "        int getValue() {\n"
    "            return (int) Math.round(this.value * ASRConfig.MAX_COST);\n"
    "        }\n\n"
    "        @Override\n"
    "        protected void updateMessage() {\n"
    "            setMessage(Component.literal(\"Shield durability cost per block: \" + getValue()));\n"
    "        }\n\n"
    "        @Override\n"
    "        protected void applyValue() {\n"
    "            updateMessage();\n"
    "        }\n"
    "    }\n"
)


def config_screen(mcver, loader=None):
    """ASRConfigScreen.java. Widgets-only shape (>=1.20.2); the 1.20.1 render-override shape is a special.
    Send goes through the ClientNet facade (payload era); 1.20.1 uses the classic channel directly."""
    if (1, 20, 0) <= _parse(mcver) < (1, 20, 5):
        return _config_screen_1201_forge() if loader == "Forge" else _config_screen_1201()
    imports = [
        "import com.kishku7.autoshieldreborn.ASRConfig;",
        "import com.kishku7.autoshieldreborn.net.SetDurabilityPayload;",
        "",
        "import net.minecraft.client.Minecraft;",
        "import net.minecraft.client.gui.components.AbstractSliderButton;",
        "import net.minecraft.client.gui.components.Button;",
        "import net.minecraft.client.gui.components.StringWidget;",
        "import net.minecraft.client.gui.screens.Screen;",
        "import net.minecraft.network.chat.Component;",
    ]
    if modern_permission(mcver):
        imports.append("import net.minecraft.server.permissions.Permissions;")
    return (
        "package com.kishku7.autoshieldreborn.client;\n\n"
        + "\n".join(imports) + "\n\n"
        "/** Auto-Shield Reborn config screen (widgets-only). Op-editable durability slider; syncs via ClientNet. */\n"
        "public class ASRConfigScreen extends Screen {\n\n"
        "    private final Screen parent;\n"
        "    private boolean editable;\n"
        "    private DurabilitySlider slider;\n\n"
        "    public ASRConfigScreen(Screen parent) {\n"
        "        super(Component.literal(\"Auto-Shield Reborn\"));\n"
        "        this.parent = parent;\n"
        "    }\n\n"
        "    @Override\n"
        "    protected void init() {\n"
        "        Minecraft mc = Minecraft.getInstance();\n"
        "        this.editable = " + _perm_editable(mcver) + ";\n\n"
        "        int cx = this.width / 2;\n"
        "        int y = this.height / 2 - 20;\n\n"
        "        this.addRenderableWidget(new StringWidget(cx - 150, y - 52, 300, 12, this.title, this.font));\n"
        "        if (!this.editable) {\n"
        "            this.addRenderableWidget(new StringWidget(cx - 150, y - 36, 300, 12,\n"
        "                    Component.literal(\"Server-controlled - operators only\"), this.font));\n"
        "        }\n\n"
        "        this.slider = new DurabilitySlider(cx - 110, y, 220, 20, ASRConfig.durabilityCost());\n"
        "        this.slider.active = this.editable;\n"
        "        this.addRenderableWidget(this.slider);\n\n"
        "        this.addRenderableWidget(Button.builder(Component.literal(\"Done\"), b -> {\n"
        "            if (this.editable && this.slider.getValue() != ASRConfig.durabilityCost()) {\n"
        "                ClientNet.sendToServer(new SetDurabilityPayload(this.slider.getValue()));\n"
        "            }\n"
        "            this.onClose();\n"
        "        }).bounds(cx - 110, y + 44, 220, 20).build());\n"
        "    }\n\n"
        "    @Override\n"
        "    public void onClose() {\n"
        "        " + _screen_close_call(mcver) + "\n"
        "    }\n\n"
        + _SLIDER_INNER +
        "}\n"
    )


def _config_screen_1201():
    """The 1.20.1 render-override screen (verbatim shipped: GuiGraphics labels + classic channel send)."""
    return (
        "package com.kishku7.autoshieldreborn.client;\n\n"
        "import com.kishku7.autoshieldreborn.ASRConfig;\n"
        "import com.kishku7.autoshieldreborn.net.ASRNetworking;\n\n"
        "import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;\n"
        "import net.fabricmc.fabric.api.networking.v1.PacketByteBufs;\n"
        "import net.minecraft.client.Minecraft;\n"
        "import net.minecraft.client.gui.GuiGraphics;\n"
        "import net.minecraft.client.gui.components.AbstractSliderButton;\n"
        "import net.minecraft.client.gui.components.Button;\n"
        "import net.minecraft.client.gui.screens.Screen;\n"
        "import net.minecraft.network.FriendlyByteBuf;\n"
        "import net.minecraft.network.chat.Component;\n\n"
        "/** Auto-Shield Reborn config screen (1.20.1: render-override labels, classic channel send). */\n"
        "public class ASRConfigScreen extends Screen {\n\n"
        "    private final Screen parent;\n"
        "    private boolean editable;\n"
        "    private DurabilitySlider slider;\n\n"
        "    public ASRConfigScreen(Screen parent) {\n"
        "        super(Component.literal(\"Auto-Shield Reborn\"));\n"
        "        this.parent = parent;\n"
        "    }\n\n"
        "    @Override\n"
        "    protected void init() {\n"
        "        Minecraft mc = Minecraft.getInstance();\n"
        "        this.editable = mc.player != null && mc.player.hasPermissions(2);\n\n"
        "        int cx = this.width / 2;\n"
        "        int y = this.height / 2 - 20;\n\n"
        "        this.slider = new DurabilitySlider(cx - 110, y, 220, 20, ASRConfig.durabilityCost());\n"
        "        this.slider.active = this.editable;\n"
        "        this.addRenderableWidget(this.slider);\n\n"
        "        this.addRenderableWidget(Button.builder(Component.literal(\"Done\"), b -> {\n"
        "            if (this.editable && this.slider.getValue() != ASRConfig.durabilityCost()) {\n"
        "                FriendlyByteBuf buf = PacketByteBufs.create();\n"
        "                buf.writeVarInt(this.slider.getValue());\n"
        "                ClientPlayNetworking.send(ASRNetworking.SET_DURABILITY, buf);\n"
        "            }\n"
        "            this.onClose();\n"
        "        }).bounds(cx - 110, y + 44, 220, 20).build());\n"
        "    }\n\n"
        "    @Override\n"
        "    public void render(GuiGraphics guiGraphics, int mouseX, int mouseY, float partialTick) {\n"
        "        this.renderBackground(guiGraphics);\n"
        "        int cx = this.width / 2;\n"
        "        int y = this.height / 2 - 20;\n"
        "        guiGraphics.drawCenteredString(this.font, this.title, cx, y - 52, 0xFFFFFF);\n"
        "        if (!this.editable) {\n"
        "            guiGraphics.drawCenteredString(this.font, Component.literal(\"Server-controlled - operators only\"),\n"
        "                    cx, y - 36, 0xA0A0A0);\n"
        "        }\n"
        "        super.render(guiGraphics, mouseX, mouseY, partialTick);\n"
        "    }\n\n"
        "    @Override\n"
        "    public void onClose() {\n"
        "        Minecraft.getInstance().setScreen(this.parent);\n"
        "    }\n\n"
        + _SLIDER_INNER +
        "}\n"
    )


def _config_screen_1201_forge():
    """1.20.1 Forge screen: render-override labels, sends the durability via the SimpleChannel seam."""
    return (
        "package com.kishku7.autoshieldreborn.client;\n\n"
        "import com.kishku7.autoshieldreborn.ASRConfig;\n"
        "import com.kishku7.autoshieldreborn.net.ASRForgeNetworking;\n\n"
        "import net.minecraft.client.Minecraft;\n"
        "import net.minecraft.client.gui.GuiGraphics;\n"
        "import net.minecraft.client.gui.components.AbstractSliderButton;\n"
        "import net.minecraft.client.gui.components.Button;\n"
        "import net.minecraft.client.gui.screens.Screen;\n"
        "import net.minecraft.network.chat.Component;\n\n"
        "/** Auto-Shield Reborn config screen (1.20.1 Forge: render-override labels, SimpleChannel send). */\n"
        "public class ASRConfigScreen extends Screen {\n\n"
        "    private final Screen parent;\n"
        "    private boolean editable;\n"
        "    private DurabilitySlider slider;\n\n"
        "    public ASRConfigScreen(Screen parent) {\n"
        "        super(Component.literal(\"Auto-Shield Reborn\"));\n"
        "        this.parent = parent;\n"
        "    }\n\n"
        "    @Override\n"
        "    protected void init() {\n"
        "        Minecraft mc = Minecraft.getInstance();\n"
        "        this.editable = mc.player != null && mc.player.hasPermissions(2);\n\n"
        "        int cx = this.width / 2;\n"
        "        int y = this.height / 2 - 20;\n\n"
        "        this.slider = new DurabilitySlider(cx - 110, y, 220, 20, ASRConfig.durabilityCost());\n"
        "        this.slider.active = this.editable;\n"
        "        this.addRenderableWidget(this.slider);\n\n"
        "        this.addRenderableWidget(Button.builder(Component.literal(\"Done\"), b -> {\n"
        "            if (this.editable && this.slider.getValue() != ASRConfig.durabilityCost()) {\n"
        "                ASRForgeNetworking.sendToServer(this.slider.getValue());\n"
        "            }\n"
        "            this.onClose();\n"
        "        }).bounds(cx - 110, y + 44, 220, 20).build());\n"
        "    }\n\n"
        "    @Override\n"
        "    public void render(GuiGraphics guiGraphics, int mouseX, int mouseY, float partialTick) {\n"
        "        this.renderBackground(guiGraphics);\n"
        "        int cx = this.width / 2;\n"
        "        int y = this.height / 2 - 20;\n"
        "        guiGraphics.drawCenteredString(this.font, this.title, cx, y - 52, 0xFFFFFF);\n"
        "        if (!this.editable) {\n"
        "            guiGraphics.drawCenteredString(this.font, Component.literal(\"Server-controlled - operators only\"),\n"
        "                    cx, y - 36, 0xA0A0A0);\n"
        "        }\n"
        "        super.render(guiGraphics, mouseX, mouseY, partialTick);\n"
        "    }\n\n"
        "    @Override\n"
        "    public void onClose() {\n"
        "        Minecraft.getInstance().setScreen(this.parent);\n"
        "    }\n\n"
        + _SLIDER_INNER +
        "}\n"
    )


def fabric_client(mcver, loader=None):
    """Fabric client entrypoint AutoShieldRebornClient.java (ClientModInitializer)."""
    if not has_payload_api(mcver):
        # 1.20.1: classic channel receiver, no ClientNet facade.
        return (
            "package com.kishku7.autoshieldreborn.client;\n\n"
            "import com.kishku7.autoshieldreborn.ASRConfig;\n"
            "import com.kishku7.autoshieldreborn.net.ASRNetworking;\n\n"
            "import net.fabricmc.api.ClientModInitializer;\n"
            "import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;\n\n"
            "/** Client entrypoint (1.20.1): classic-channel sync receiver. */\n"
            "public class AutoShieldRebornClient implements ClientModInitializer {\n\n"
            "    @Override\n"
            "    public void onInitializeClient() {\n"
            "        ClientPlayNetworking.registerGlobalReceiver(ASRNetworking.SYNC_DURABILITY,\n"
            "                (client, handler, buf, responseSender) -> {\n"
            "                    int value = buf.readVarInt();\n"
            "                    client.execute(() -> ASRConfig.setDurabilityCostNoSave(value));\n"
            "                });\n"
            "    }\n}\n"
        )
    return (
        "package com.kishku7.autoshieldreborn.client;\n\n"
        "import com.kishku7.autoshieldreborn.ASRConfig;\n"
        "import com.kishku7.autoshieldreborn.net.SyncDurabilityPayload;\n\n"
        "import net.fabricmc.api.ClientModInitializer;\n"
        "import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;\n\n"
        "/** Client entrypoint: keeps the local durability value synced; wires the ClientNet C2S sender. */\n"
        "public class AutoShieldRebornClient implements ClientModInitializer {\n\n"
        "    @Override\n"
        "    public void onInitializeClient() {\n"
        "        ClientPlayNetworking.registerGlobalReceiver(SyncDurabilityPayload.TYPE, (payload, context) ->\n"
        "                ASRConfig.setDurabilityCostNoSave(payload.cost()));\n"
        "        ClientNet.SENDER = ClientPlayNetworking::send;\n"
        "    }\n}\n"
    )

# ---------------------------------------------------------------------------
# NeoForge @Mod entrypoint (26 + sub-26 backfill) -- only the permission form drifts.
# ---------------------------------------------------------------------------

def neoforge_entrypoint(mcver, loader=None):
    """AutoShieldRebornNeoForge.java (@Mod). Permission: permissions().hasPermission (26/1.21.11)
    vs hasPermissions(2) (1.20.6..1.21.10). Payload registrar + PacketDistributor assumed stable
    NeoForge 1.20.6+ (build validates the backfill cells)."""
    modern = modern_permission(mcver)
    perm = ("player.permissions().hasPermission(Permissions.COMMANDS_GAMEMASTER)"
            if modern else "player.hasPermissions(2)")
    perm_import = "import net.minecraft.server.permissions.Permissions;\n" if modern else ""
    return (
        "package com.kishku7.autoshieldreborn;\n\n"
        "import com.kishku7.autoshieldreborn.client.AutoShieldRebornNeoForgeClient;\n"
        "import com.kishku7.autoshieldreborn.net.SetDurabilityPayload;\n"
        "import com.kishku7.autoshieldreborn.net.SyncDurabilityPayload;\n\n"
        "import net.minecraft.server.level.ServerPlayer;\n"
        + perm_import +
        "import net.neoforged.api.distmarker.Dist;\n"
        "import net.neoforged.bus.api.IEventBus;\n"
        "import net.neoforged.fml.ModContainer;\n"
        "import net.neoforged.fml.common.Mod;\n"
        "import net.neoforged.fml.loading.FMLPaths;\n"
        "import net.neoforged.neoforge.common.NeoForge;\n"
        "import net.neoforged.neoforge.event.entity.player.PlayerEvent;\n"
        "import net.neoforged.neoforge.network.PacketDistributor;\n"
        "import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;\n"
        "import net.neoforged.neoforge.network.registration.PayloadRegistrar;\n\n"
        "/** Auto-Shield Reborn - NeoForge entrypoint: config + payload registration + op-gated set/join-sync. */\n"
        "@Mod(AutoShieldReborn.MOD_ID)\n"
        "public class AutoShieldRebornNeoForge {\n\n"
        "    public AutoShieldRebornNeoForge(ModContainer mod, IEventBus bus, Dist dist) {\n"
        "        ASRConfig.init(FMLPaths.CONFIGDIR.get());\n"
        "        bus.addListener(this::registerPayloads);\n"
        "        NeoForge.EVENT_BUS.addListener(this::onPlayerJoin);\n"
        "        if (dist.isClient()) {\n"
        "            AutoShieldRebornNeoForgeClient.init(mod);\n"
        "        }\n"
        "        AutoShieldReborn.LOGGER.info(\"[ASR] ready - durability cost per blocked hit: {}\", ASRConfig.durabilityCost());\n"
        "    }\n\n"
        "    private void registerPayloads(RegisterPayloadHandlersEvent event) {\n"
        "        PayloadRegistrar registrar = event.registrar(AutoShieldReborn.MOD_ID).versioned(\"1.0.0\");\n\n"
        "        registrar.playToClient(SyncDurabilityPayload.TYPE, SyncDurabilityPayload.CODEC,\n"
        "                (payload, context) -> ASRConfig.setDurabilityCostNoSave(payload.cost()));\n\n"
        "        registrar.playToServer(SetDurabilityPayload.TYPE, SetDurabilityPayload.CODEC, (payload, context) -> {\n"
        "            if (context.player() instanceof ServerPlayer player\n"
        "                    && " + perm + ") {\n"
        "                int applied = ASRConfig.setDurabilityCost(payload.cost());\n"
        "                PacketDistributor.sendToAllPlayers(new SyncDurabilityPayload(applied));\n"
        "            }\n"
        "        });\n"
        "    }\n\n"
        "    private void onPlayerJoin(PlayerEvent.PlayerLoggedInEvent event) {\n"
        "        if (event.getEntity() instanceof ServerPlayer player) {\n"
        "            PacketDistributor.sendToPlayer(player, new SyncDurabilityPayload(ASRConfig.durabilityCost()));\n"
        "        }\n"
        "    }\n"
        "}\n"
    )



def neoforge_client(mcver, loader=None):
    """NeoForge client init: Config button (IConfigScreenFactory) + C2S sender. ClientPacketDistributor
    split out of PacketDistributor at ~1.21.6; before that the client send is PacketDistributor::sendToServer."""
    modern_send = _parse(mcver) >= (1, 21, 6)
    if modern_send:
        send_import = "import net.neoforged.neoforge.client.network.ClientPacketDistributor;"
        sender = "ClientPacketDistributor::sendToServer"
    else:
        send_import = "import net.neoforged.neoforge.network.PacketDistributor;"
        sender = "PacketDistributor::sendToServer"
    return (
        "package com.kishku7.autoshieldreborn.client;\n\n"
        "import net.neoforged.fml.ModContainer;\n"
        "import net.neoforged.neoforge.client.gui.IConfigScreenFactory;\n"
        + send_import + "\n\n"
        "/** NeoForge client: mods-list Config button (opens ASRConfigScreen) + the C2S sender. */\n"
        "public final class AutoShieldRebornNeoForgeClient {\n\n"
        "    private AutoShieldRebornNeoForgeClient() {\n    }\n\n"
        "    public static void init(ModContainer mod) {\n"
        "        ClientNet.SENDER = " + sender + ";\n"
        "        IConfigScreenFactory factory = (container, modListScreen) -> new ASRConfigScreen(modListScreen);\n"
        "        mod.registerExtensionPoint(IConfigScreenFactory.class, factory);\n"
        "    }\n"
        "}\n"
    )


# ---------------------------------------------------------------------------
# Forge FG6 backfill: entrypoint (EB6/EB7) + networking (PayloadChannel / SimpleChannel) + client.
# ASR Forge ceiling = 1.21.8; all cells are LEGACY-era (hasPermissions(2), ResourceLocation).
# ---------------------------------------------------------------------------

def forge_eb7(mcver):
    """Forge EventBus 7 landed with Forge 56 (MC 1.21.6). ASR: 1.21.8 = EB7; 1.20.1..1.21.5 = EB6."""
    return _parse(mcver) >= (1, 21, 6)


def forge_entrypoint(mcver, loader=None):
    """AutoShieldRebornForge.java (@Mod). EB6 (<1.21.6) vs EB7 (>=1.21.6) event-bus wiring."""
    eb7 = forge_eb7(mcver)
    common_imports = (
        "import com.kishku7.autoshieldreborn.client.AutoShieldRebornForgeClient;\n"
        "import com.kishku7.autoshieldreborn.net.ASRForgeNetworking;\n"
        "import net.minecraft.server.level.ServerPlayer;\n"
        "import net.minecraftforge.event.entity.player.PlayerEvent;\n"
        "import net.minecraftforge.fml.common.Mod;\n"
        "import net.minecraftforge.fml.loading.FMLEnvironment;\n"
        "import net.minecraftforge.fml.loading.FMLPaths;\n"
    )
    head = "package com.kishku7.autoshieldreborn;\n\n" + common_imports
    if eb7:
        head += (
            "import net.minecraftforge.eventbus.api.bus.BusGroup;\n"
            "import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;\n\n"
        )
        ctor = (
            "    public AutoShieldRebornForge(FMLJavaModLoadingContext context) {\n"
            "        ASRConfig.init(FMLPaths.CONFIGDIR.get());\n"
            "        BusGroup modBus = context.getModBusGroup();\n"
            "        ASRForgeNetworking.init();\n"
            "        PlayerEvent.PlayerLoggedInEvent.BUS.addListener(AutoShieldRebornForge::onJoin);\n"
            "        if (FMLEnvironment.dist.isClient()) {\n"
            "            AutoShieldRebornForgeClient.init(modBus);\n"
            "        }\n"
            "        AutoShieldReborn.LOGGER.info(\"[ASR] ready - durability cost per blocked hit: {}\", ASRConfig.durabilityCost());\n"
            "    }\n"
        )
        client_param = "BusGroup"
    else:
        head += (
            "import net.minecraftforge.common.MinecraftForge;\n"
            "import net.minecraftforge.eventbus.api.IEventBus;\n"
            "import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;\n\n"
        )
        ctor = (
            "    @SuppressWarnings(\"removal\")   // FMLJavaModLoadingContext.get() is the EB6-era accessor\n"
            "    public AutoShieldRebornForge() {\n"
            "        ASRConfig.init(FMLPaths.CONFIGDIR.get());\n"
            "        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();\n"
            "        ASRForgeNetworking.init();\n"
            "        MinecraftForge.EVENT_BUS.addListener((PlayerEvent.PlayerLoggedInEvent e) -> onJoin(e));\n"
            "        if (FMLEnvironment.dist.isClient()) {\n"
            "            AutoShieldRebornForgeClient.init(modBus);\n"
            "        }\n"
            "        AutoShieldReborn.LOGGER.info(\"[ASR] ready - durability cost per blocked hit: {}\", ASRConfig.durabilityCost());\n"
            "    }\n"
        )
        client_param = "IEventBus"
    return (
        head +
        "/** Auto-Shield Reborn - Forge entrypoint. Config + payload channel + op-gated set/join-sync. */\n"
        "@Mod(AutoShieldReborn.MOD_ID)\n"
        "public final class AutoShieldRebornForge {\n\n"
        + ctor + "\n"
        "    private static void onJoin(PlayerEvent.PlayerLoggedInEvent event) {\n"
        "        if (event.getEntity() instanceof ServerPlayer player) {\n"
        "            ASRForgeNetworking.sendSync(player, ASRConfig.durabilityCost());\n"
        "        }\n"
        "    }\n"
        "}\n"
    )


def forge_net(mcver, loader=None):
    """ASRForgeNetworking.java. PayloadChannel (1.20.5+; ASR 1.20.6..1.21.8) vs classic SimpleChannel (1.20.1)."""
    if has_payload_api(mcver):
        return (
            "package com.kishku7.autoshieldreborn.net;\n\n"
            "import com.kishku7.autoshieldreborn.ASRConfig;\n"
            "import com.kishku7.autoshieldreborn.AutoShieldReborn;\n\n"
            "import net.minecraft.network.RegistryFriendlyByteBuf;\n"
            "import net.minecraft.network.codec.StreamCodec;\n"
            "import net.minecraft.network.protocol.common.custom.CustomPacketPayload;\n"
            + _identifier_import(mcver) + "\n"
            "import net.minecraft.server.level.ServerPlayer;\n"
            + ("import net.minecraft.server.permissions.Permissions;\n" if modern_permission(mcver) else "")
            + "import net.minecraftforge.network.Channel;\n"
            "import net.minecraftforge.network.ChannelBuilder;\n"
            "import net.minecraftforge.network.PacketDistributor;\n"
            "import net.minecraftforge.network.payload.PayloadProtocol;\n\n"
            "/** Forge payload-channel networking: op-gated durability set + broadcast + join-sync. */\n"
            "public final class ASRForgeNetworking {\n\n"
            "    private ASRForgeNetworking() {\n    }\n\n"
            "    private static Channel<CustomPacketPayload> CHANNEL;\n\n"
            "    /** Client -> server seam (ClientNet delegates here). */\n"
            "    public static void sendToServer(CustomPacketPayload p) {\n"
            "        CHANNEL.send(p, PacketDistributor.SERVER.noArg());\n"
            "    }\n\n"
            "    public static void sendSync(ServerPlayer player, int cost) {\n"
            "        CHANNEL.send(new SyncDurabilityPayload(cost), PacketDistributor.PLAYER.with(player));\n"
            "    }\n\n"
            "    /** Rewind a single-player double-decoded buffer (Forge PayloadChannel quirk). */\n"
            "    private static <T extends CustomPacketPayload> StreamCodec<RegistryFriendlyByteBuf, T> sp(\n"
            "            StreamCodec<RegistryFriendlyByteBuf, T> inner) {\n"
            "        return new StreamCodec<RegistryFriendlyByteBuf, T>() {\n"
            "            @Override\n"
            "            public T decode(RegistryFriendlyByteBuf buf) {\n"
            "                if (buf.readableBytes() == 0 && buf.writerIndex() > 0) buf.readerIndex(0);\n"
            "                return inner.decode(buf);\n"
            "            }\n"
            "            @Override\n"
            "            public void encode(RegistryFriendlyByteBuf buf, T val) {\n"
            "                inner.encode(buf, val);\n"
            "            }\n"
            "        };\n"
            "    }\n\n"
            "    public static void init() {\n"
            "        PayloadProtocol<RegistryFriendlyByteBuf, CustomPacketPayload> proto =\n"
            "                ChannelBuilder.named(" + identifier_expr(mcver, "main") + ")\n"
            "                        .networkProtocolVersion(1).optional().payloadChannel().play();\n"
            "        proto.serverbound().add(SetDurabilityPayload.TYPE, sp(SetDurabilityPayload.CODEC),\n"
            "                (m, c) -> c.enqueueWork(() -> onSet(m, c.getSender())));\n"
            "        CHANNEL = proto.clientbound().add(SyncDurabilityPayload.TYPE, sp(SyncDurabilityPayload.CODEC),\n"
            "                (m, c) -> c.enqueueWork(() -> ASRConfig.setDurabilityCostNoSave(m.cost()))).build();\n"
            "    }\n\n"
            "    private static void onSet(SetDurabilityPayload m, ServerPlayer player) {\n"
            "        if (player == null || !" + ("player.permissions().hasPermission(Permissions.COMMANDS_GAMEMASTER)" if modern_permission(mcver) else "player.hasPermissions(2)") + ") {\n            return;\n        }\n"
            "        int applied = ASRConfig.setDurabilityCost(m.cost());\n"
            "        for (ServerPlayer online : player.level().getServer().getPlayerList().getPlayers()) {\n"
            "            sendSync(online, applied);\n"
            "        }\n"
            "    }\n"
            "}\n"
        )
    # 1.20.1 SimpleChannel (classic; int payload serialized via VarInt directly)
    return (
        "package com.kishku7.autoshieldreborn.net;\n\n"
        "import com.kishku7.autoshieldreborn.ASRConfig;\n"
        "import com.kishku7.autoshieldreborn.AutoShieldReborn;\n\n"
        "import net.minecraft.network.FriendlyByteBuf;\n"
        "import net.minecraft.resources.ResourceLocation;\n"
        "import net.minecraft.server.level.ServerPlayer;\n"
        "import net.minecraftforge.network.NetworkRegistry;\n"
        "import net.minecraftforge.network.PacketDistributor;\n"
        "import net.minecraftforge.network.simple.SimpleChannel;\n\n"
        "/** Forge 1.20.1 classic SimpleChannel networking (no payload API): op-gated set + broadcast + join-sync. */\n"
        "public final class ASRForgeNetworking {\n\n"
        "    private ASRForgeNetworking() {\n    }\n\n"
        "    @SuppressWarnings(\"removal\")   // NetworkRegistry/SimpleChannel is the 1.20.1 (forge 47) networking API\n"
        "    private static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(\n"
        "            new ResourceLocation(AutoShieldReborn.MOD_ID, \"main\"), () -> \"1\", v -> true, v -> true);\n\n"
        "    public static void sendToServer(int cost) {\n"
        "        CHANNEL.sendToServer(cost);\n"
        "    }\n\n"
        "    public static void sendSync(ServerPlayer player, int cost) {\n"
        "        CHANNEL.send(PacketDistributor.PLAYER.with(() -> player), new SyncMsg(cost));\n"
        "    }\n\n"
        "    /** Message holders with explicit write/decode (SimpleChannel has no StreamCodec). */\n"
        "    public record SetMsg(int cost) {\n"
        "        public void write(FriendlyByteBuf b) { b.writeVarInt(cost); }\n"
        "        public static SetMsg decode(FriendlyByteBuf b) { return new SetMsg(b.readVarInt()); }\n"
        "    }\n\n"
        "    public record SyncMsg(int cost) {\n"
        "        public void write(FriendlyByteBuf b) { b.writeVarInt(cost); }\n"
        "        public static SyncMsg decode(FriendlyByteBuf b) { return new SyncMsg(b.readVarInt()); }\n"
        "    }\n\n"
        "    public static void init() {\n"
        "        int i = 0;\n"
        "        CHANNEL.registerMessage(i++, SetMsg.class, SetMsg::write, SetMsg::decode,\n"
        "                (m, ctx) -> { ctx.get().enqueueWork(() -> onSet(m, ctx.get().getSender())); ctx.get().setPacketHandled(true); });\n"
        "        CHANNEL.registerMessage(i++, SyncMsg.class, SyncMsg::write, SyncMsg::decode,\n"
        "                (m, ctx) -> { ctx.get().enqueueWork(() -> ASRConfig.setDurabilityCostNoSave(m.cost())); ctx.get().setPacketHandled(true); });\n"
        "    }\n\n"
        "    private static void onSet(SetMsg m, ServerPlayer player) {\n"
        "        if (player == null || !player.hasPermissions(2)) {\n            return;\n        }\n"
        "        int applied = ASRConfig.setDurabilityCost(m.cost());\n"
        "        for (ServerPlayer online : player.getServer().getPlayerList().getPlayers()) {\n"
        "            sendSync(online, applied);\n"
        "        }\n"
        "    }\n"
        "}\n"
    )


def forge_client(mcver, loader=None):
    """AutoShieldRebornForgeClient.java: mods-list Config button (ConfigScreenHandler). Payload cells
    also wire the ClientNet C2S sender; 1.20.1 (SimpleChannel) has no ClientNet -- the screen sends direct."""
    eb7 = forge_eb7(mcver)
    busimp = "import net.minecraftforge.eventbus.api.bus.BusGroup;" if eb7 else "import net.minecraftforge.eventbus.api.IEventBus;"
    bustype = "BusGroup" if eb7 else "IEventBus"
    payload = has_payload_api(mcver)
    net_import = "import com.kishku7.autoshieldreborn.net.ASRForgeNetworking;\n" if payload else ""
    sender_line = "        ClientNet.SENDER = ASRForgeNetworking::sendToServer;\n" if payload else ""
    return (
        "package com.kishku7.autoshieldreborn.client;\n\n"
        + net_import +
        "import net.minecraftforge.client.ConfigScreenHandler;\n"
        + busimp + "\n"
        "import net.minecraftforge.fml.ModLoadingContext;\n\n"
        "/** Forge client: registers the mods-list Config button (opens ASRConfigScreen). */\n"
        "public final class AutoShieldRebornForgeClient {\n\n"
        "    private AutoShieldRebornForgeClient() {\n    }\n\n"
        "    @SuppressWarnings(\"removal\")   // ModLoadingContext.get() is the EB6-era config-screen accessor\n"
        "    public static void init(" + bustype + " modBus) {\n"
        + sender_line +
        "        ModLoadingContext.get().registerExtensionPoint(ConfigScreenHandler.ConfigScreenFactory.class,\n"
        "                () -> new ConfigScreenHandler.ConfigScreenFactory((mc, parent) -> new ASRConfigScreen(parent)));\n"
        "    }\n"
        "}\n"
    )

def main():
    print("ASR compat.py era matrix")
    print("=" * 100)
    hdr = ("mcver", "26?", "comp?", "hook", "durab", "view", "arrowpkg", "net", "perm", "compat")
    print("%-16s %-4s %-6s %-11s %-9s %-7s %-9s %-11s %-8s %-7s" % hdr)
    for v in _TEST_VERSIONS:
        hook = "applyBlock" if is_component(v) else ("hurtServer" if uses_hurtserver(v) else "hurt")
        net = "serverbound" if is_26(v) else ("playC2S" if has_payload_api(v) else "channel")
        row = (v, str(is_26(v)), str(is_component(v)), hook, durability_kind(v),
               "manual" if manual_view(v) else "calc",
               arrow_package(v).split(".")[-1], net,
               "gamemaster" if modern_permission(v) else "lvl2", compat_level(v))
        print("%-16s %-4s %-6s %-11s %-9s %-7s %-9s %-11s %-8s %-7s" % row)
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
