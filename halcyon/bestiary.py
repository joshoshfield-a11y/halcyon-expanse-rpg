"""
Halcyon Expanse — Bestiary System
Build Step 10: Six enemy types as AI agents with behavior_pattern state machines.
Behavior patterns used as literal state-machine state names.
"""
import time


class Enemy:
    """Single enemy agent with behavior state machine."""
    def __init__(self, name, behavior_pattern, threat_tier, hp=100, x=0, y=0):
        self.name = name
        self.behavior_pattern = behavior_pattern
        self.threat_tier = threat_tier
        self.hp = hp
        self.max_hp = hp
        self.x = x
        self.y = y
        self.state = "idle"
        self.state_timer = 0.0
        self.target = None
        self.lc_drain_per_tick = 5.0  # For LC drain behaviors

    def update(self, dt, player, all_enemies):
        """State machine update based on behavior_pattern."""
        self.state_timer += dt

        if self.behavior_pattern == "phase_cycle_4s_LC_drain":
            # Ash Wraith: 4-second visibility toggle, drains LC
            cycle = self.state_timer % 4.0
            if cycle < 2.0:
                self.state = "visible"
                if player and hasattr(player, 'lattice_charge'):
                    player.lattice_charge = max(0, player.lattice_charge - self.lc_drain_per_tick * dt)
            else:
                self.state = "phased"

        elif self.behavior_pattern == "patrol_loop_shield_burst":
            # Ferro Drone: patrols in loop, shield burst every 5s
            if self.state_timer % 5.0 < 1.0:
                self.state = "shield_burst"
            else:
                self.state = "patrol"
                # Simple patrol: move in square
                self.x = (self.x + 1) % 20

        elif self.behavior_pattern == "stealth_ambush_LC_leech":
            # Hollow Stalker: stealth until close, then ambush and leech LC
            if player:
                dist = abs(self.x - player.x) + abs(self.y - player.y)
                if dist <= 2 and self.state == "stealth":
                    self.state = "ambush"
                    self.state_timer = 0
                elif self.state == "ambush" and self.state_timer > 2.0:
                    self.state = "leech"
                    if hasattr(player, 'lattice_charge'):
                        player.lattice_charge = max(0, player.lattice_charge - 10 * dt)
                elif dist > 5:
                    self.state = "stealth"

        elif self.behavior_pattern == "area_pulse_knockback":
            # Tide Leviathan: periodic area pulse
            if self.state_timer % 6.0 < 1.5:
                self.state = "pulse"
                # Knockback effect would push player away
            else:
                self.state = "charge"

        elif self.behavior_pattern == "buff_ally_resonance_amplify":
            # Chorus Hymnal: buffs nearby allies
            self.state = "buffing"
            for ally in all_enemies:
                if ally != self and abs(ally.x - self.x) + abs(ally.y - self.y) <= 3:
                    ally.hp = min(ally.max_hp, ally.hp + 2 * dt)

        elif self.behavior_pattern == "swarm_split_on_damage":
            # Salt Scarab: splits when damaged
            if self.hp < self.max_hp * 0.5 and self.state != "splitting":
                self.state = "splitting"
                # Would spawn clone in real implementation
            else:
                self.state = "swarm"

        else:
            self.state = "idle"

    def take_damage(self, amount):
        self.hp -= amount
        return self.hp <= 0

    def to_dict(self):
        return {
            "name": self.name,
            "behavior_pattern": self.behavior_pattern,
            "threat_tier": self.threat_tier,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "x": self.x,
            "y": self.y,
            "state": self.state,
        }


class Bestiary:
    """Manages all enemy types and spawns."""

    ENEMY_TEMPLATES = [
        {"name": "Ash Wraith", "behavior_pattern": "phase_cycle_4s_LC_drain", "threat_tier": 3, "hp": 80},
        {"name": "Ferro Drone", "behavior_pattern": "patrol_loop_shield_burst", "threat_tier": 2, "hp": 60},
        {"name": "Hollow Stalker", "behavior_pattern": "stealth_ambush_LC_leech", "threat_tier": 4, "hp": 120},
        {"name": "Tide Leviathan", "behavior_pattern": "area_pulse_knockback", "threat_tier": 5, "hp": 200},
        {"name": "Chorus Hymnal", "behavior_pattern": "buff_ally_resonance_amplify", "threat_tier": 3, "hp": 90},
        {"name": "Salt Scarab", "behavior_pattern": "swarm_split_on_damage", "threat_tier": 2, "hp": 40},
    ]

    def __init__(self):
        self.enemies = []
        self.templates = {t["name"]: t for t in self.ENEMY_TEMPLATES}

    def spawn(self, name, x=0, y=0):
        template = self.templates.get(name)
        if not template:
            return None
        enemy = Enemy(
            name=template["name"],
            behavior_pattern=template["behavior_pattern"],
            threat_tier=template["threat_tier"],
            hp=template["hp"],
            x=x, y=y
        )
        self.enemies.append(enemy)
        return enemy

    def update_all(self, dt, player):
        for enemy in self.enemies:
            enemy.update(dt, player, self.enemies)

    def remove_dead(self):
        self.enemies = [e for e in self.enemies if e.hp > 0]

    def to_dict(self):
        return {"enemies": [e.to_dict() for e in self.enemies]}
