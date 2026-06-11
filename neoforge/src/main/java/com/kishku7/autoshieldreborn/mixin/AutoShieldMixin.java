package com.kishku7.autoshieldreborn.mixin;

import com.kishku7.autoshieldreborn.ASRConfig;

import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.BlocksAttacks;
import net.minecraft.world.phys.Vec3;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * The whole mod. Injects the server-side blocking path so a player auto-blocks whenever they
 * hold a shield - no need to raise it.
 *
 * Hooks {@code LivingEntity.applyItemBlocking} (the method vanilla uses to subtract shield-blocked
 * damage). When the player is NOT already actively raising a shield, we look for a shield in either
 * hand and, mirroring vanilla's own blocking rules, decide whether this damage can be blocked:
 *   - the item carries the {@code blocks_attacks} component and the damage type is not in its
 *     {@code bypassedBy} set (so fire / drowning / fall / magic / starvation pass straight through,
 *     exactly like a manually-raised shield);
 *   - piercing arrows ignore shields;
 *   - the damage has a source position and that position lies within a 180-degree frontal arc
 *     (head-yaw, horizontal plane) - damage from behind is NOT blocked.
 *
 * On a successful block we fully negate the damage, play the shield-block sound, swing the blocking
 * hand, and chip the shield by the server-configured durability cost (0-10). All server-authoritative.
 */
@Mixin(LivingEntity.class)
public abstract class AutoShieldMixin {

    @Inject(method = "applyItemBlocking", at = @At("HEAD"), cancellable = true)
    private void asr$autoBlock(ServerLevel level, DamageSource source, float damage, CallbackInfoReturnable<Float> cir) {
        LivingEntity self = (LivingEntity) (Object) this;
        if (damage <= 0.0F || !(self instanceof Player player)) {
            return;
        }
        // If the player is genuinely raising a shield, let vanilla handle it normally.
        if (self.getItemBlockingWith() != null) {
            return;
        }

        // Find a shield (any item with the blocks_attacks component) in either hand; prefer the offhand.
        InteractionHand hand;
        BlocksAttacks blocksAttacks;
        ItemStack offHand = player.getOffhandItem();
        ItemStack mainHand = player.getMainHandItem();
        BlocksAttacks offBlocks = offHand.get(DataComponents.BLOCKS_ATTACKS);
        BlocksAttacks mainBlocks = mainHand.get(DataComponents.BLOCKS_ATTACKS);
        if (offBlocks != null) {
            hand = InteractionHand.OFF_HAND;
            blocksAttacks = offBlocks;
        } else if (mainBlocks != null) {
            hand = InteractionHand.MAIN_HAND;
            blocksAttacks = mainBlocks;
        } else {
            return;
        }

        // This damage type bypasses the shield (mirror vanilla's per-item bypassedBy set).
        if (blocksAttacks.bypassedBy().map(tag -> tag.contains(source.typeHolder())).orElse(false)) {
            return;
        }
        // Piercing arrows go through shields.
        if (source.getDirectEntity() instanceof AbstractArrow arrow && arrow.getPierceLevel() > 0) {
            return;
        }

        // Directional gate: must have a source position, and it must be within the forward 180 degrees.
        Vec3 sourcePos = source.getSourcePosition();
        if (sourcePos == null) {
            return;
        }
        Vec3 view = self.calculateViewVector(0.0F, self.getYHeadRot());
        Vec3 toSource = sourcePos.subtract(self.position());
        toSource = new Vec3(toSource.x, 0.0, toSource.z).normalize();
        if (toSource.dot(view) < 0.0) {
            return; // source is behind the player -> not blocked
        }

        // Auto-block: fully negate the damage with feedback and the configured durability cost.
        ItemStack shield = player.getItemInHand(hand);
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.SHIELD_BLOCK, SoundSource.PLAYERS, 1.0F,
                0.8F + level.getRandom().nextFloat() * 0.4F);
        player.swing(hand, true);
        int cost = ASRConfig.durabilityCost();
        if (cost > 0) {
            shield.hurtAndBreak(cost, self, hand);
        }
        cir.setReturnValue(damage);
    }
}
