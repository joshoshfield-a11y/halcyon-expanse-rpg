"""
Halcyon Expanse — 2D Combat System
Real-time combat with Lattice Actions, melee, and enemy AI.
"""
import math
import time


class CombatSystem:
    """Handles all combat interactions between player and enemies."""

    def __init__(self, ability_system, bestiary, tilemap):
        self.ability_system = ability_system
        self.bestiary = bestiary
        self.tilemap = tilemap
        self.combat_log = []
        self.last_attack_time = 0
        self.attack_cooldown = 0.5  # seconds between attacks

    def player_attack(self, player, direction):
        """Player melee attack in a direction."""
        now = time.time()
        if now - self.last_attack_time < self.attack_cooldown:
            return False, "Attack on cooldown"
        self.last_attack_time = now

        dx, dy = direction
        target_x = int(player.x + dx)
        target_y = int(player.y + dy)

        # Find enemy at target position
        for enemy in self.bestiary.enemies:
            if int(enemy.x) == target_x and int(enemy.y) == target_y:
                damage = 15 + player.attunement_level * 3
                dead = enemy.take_damage(damage)
                msg = f"Hit {enemy.name} for {damage} damage! ({enemy.hp}/{enemy.max_hp} HP)"
                self.combat_log.append(msg)
                if dead:
                    self.combat_log.append(f"{enemy.name} destroyed!")
                    self.bestiary.remove_dead()
                return True, msg

        return False, "No target in range"

    def player_cast(self, player, ability_id):
        """Player casts a Lattice Action."""
        success, msg = self.ability_system.cast(ability_id, player)
        self.combat_log.append(msg)

        if success:
            # Apply effect based on ability
            ability = self.ability_system.abilities.get(ability_id)
            if ability:
                if "drain" in ability.name.lower() or "drain" in ability.description.lower():
                    # Drain nearby enemies
                    for enemy in self.bestiary.enemies:
                        dist = math.sqrt((enemy.x - player.x)**2 + (enemy.y - player.y)**2)
                        if dist <= 3:
                            drain = 10 + player.attunement_level * 2
                            enemy.take_damage(drain)
                            self.combat_log.append(f"Drained {enemy.name} for {drain} LC")
                elif "heal" in ability.name.lower():
                    player.hp = min(100, player.hp + 20 + player.attunement_level * 5)
                    self.combat_log.append(f"Healed for {20 + player.attunement_level * 5} HP")
                elif "shield" in ability.name.lower():
                    player.data["shield_active"] = True
                    player.data["shield_duration"] = 3.0
                    self.combat_log.append("Shield activated!")
                elif "blast" in ability.name.lower():
                    # Area damage
                    for enemy in self.bestiary.enemies:
                        dist = math.sqrt((enemy.x - player.x)**2 + (enemy.y - player.y)**2)
                        if dist <= 4:
                            dmg = 25 + player.attunement_level * 5
                            enemy.take_damage(dmg)
                            self.combat_log.append(f"Blast hit {enemy.name} for {dmg}")

        return success, msg

    def update_enemies(self, dt, player):
        """Update all enemy AI and attacks."""
        self.bestiary.update_all(dt, player)

        for enemy in self.bestiary.enemies:
            # Basic movement toward player if in range
            dist = math.sqrt((enemy.x - player.x)**2 + (enemy.y - player.y)**2)

            if dist < 8 and dist > 1.5:
                # Move toward player
                dx = (player.x - enemy.x) / dist if dist > 0 else 0
                dy = (player.y - enemy.y) / dist if dist > 0 else 0
                new_x = enemy.x + dx * 1.5 * dt
                new_y = enemy.y + dy * 1.5 * dt

                if self.tilemap.is_walkable(int(new_x), int(new_y)):
                    enemy.x = new_x
                    enemy.y = new_y

            # Attack player if adjacent
            if dist <= 1.5:
                damage = enemy.threat_tier * 3
                if player.data.get("shield_active"):
                    damage = max(0, damage - 10)
                    self.combat_log.append(f"Shield blocked {enemy.name} attack!")
                player.hp -= damage
                self.combat_log.append(f"{enemy.name} hit you for {damage} damage!")

            # LC drain behaviors
            if enemy.behavior_pattern == "phase_cycle_4s_LC_drain" and dist <= 3:
                if hasattr(player, 'lattice_charge'):
                    drain = 5 * dt
                    player.lattice_charge = max(0, player.lattice_charge - drain)

            # Update shield duration
            if player.data.get("shield_active"):
                player.data["shield_duration"] -= dt
                if player.data["shield_duration"] <= 0:
                    player.data["shield_active"] = False
                    self.combat_log.append("Shield expired")

    def get_combat_log(self, max_lines=5):
        return self.combat_log[-max_lines:]

    def clear_log(self):
        self.combat_log = []
