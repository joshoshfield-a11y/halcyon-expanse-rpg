"""
Halcyon Expanse — Boss System
Multi-phase boss fights with unique mechanics, arena effects, and legendary loot.
"""
import math
import random
import time


class BossPhase:
    """A single phase of a boss fight."""
    def __init__(self, phase_name, hp_threshold, behavior_pattern, 
                 attack_cooldown, special_ability=None, arena_effect=None):
        self.phase_name = phase_name
        self.hp_threshold = hp_threshold  # HP % to trigger this phase
        self.behavior_pattern = behavior_pattern
        self.attack_cooldown = attack_cooldown
        self.special_ability = special_ability
        self.arena_effect = arena_effect  # "lc_drain", "damage_over_time", "spawn_adds"
        self.last_attack = 0
        self.ability_charges = 3

    def can_attack(self):
        return time.time() - self.last_attack >= self.attack_cooldown

    def on_attack(self):
        self.last_attack = time.time()


class Boss:
    """A boss enemy with multiple phases and unique mechanics."""

    def __init__(self, name, title, hp, phases, loot_table, 
                 arena_size=10, intro_text="", defeat_text=""):
        self.name = name
        self.title = title
        self.hp = hp
        self.max_hp = hp
        self.phases = sorted(phases, key=lambda p: p.hp_threshold, reverse=True)
        self.current_phase_idx = 0
        self.current_phase = self.phases[0] if self.phases else None
        self.loot_table = loot_table
        self.arena_size = arena_size
        self.intro_text = intro_text
        self.defeat_text = defeat_text

        self.x = 0
        self.y = 0
        self.kind = "boss"
        self.state = "idle"
        self.threat_tier = 6  # Boss tier

        self.enraged = False
        self.shield_active = False
        self.shield_hp = 0
        self.summons = []

        self.damage_taken_this_phase = 0
        self.phase_transition_timer = 0

    @property
    def hp_pct(self):
        return self.hp / self.max_hp if self.max_hp > 0 else 0

    def check_phase_transition(self):
        """Check if boss should transition to next phase."""
        if self.current_phase_idx >= len(self.phases) - 1:
            return False

        next_phase = self.phases[self.current_phase_idx + 1]
        if self.hp_pct <= next_phase.hp_threshold:
            self.current_phase_idx += 1
            self.current_phase = self.phases[self.current_phase_idx]
            self.phase_transition_timer = 2.0  # Transition immunity
            self.shield_active = False
            return True
        return False

    def update(self, dt, player, all_enemies):
        """Update boss AI."""
        if self.phase_transition_timer > 0:
            self.phase_transition_timer -= dt
            self.state = "transition"
            return

        # Check phase transition
        if self.check_phase_transition():
            self.state = f"phase_{self.current_phase_idx + 1}"
            return

        # Enrage at 10% HP
        if self.hp_pct <= 0.1 and not self.enraged:
            self.enraged = True
            self.state = "enraged"
            return

        dist = math.sqrt((self.x - player.x)**2 + (self.y - player.y)**2)

        # Arena effects
        if self.current_phase and self.current_phase.arena_effect:
            if self.current_phase.arena_effect == "lc_drain" and dist <= self.arena_size:
                if hasattr(player, 'lattice_charge'):
                    player.lattice_charge = max(0, player.lattice_charge - 8 * dt)
            elif self.current_phase.arena_effect == "damage_over_time" and dist <= self.arena_size:
                player.hp -= 2 * dt
            elif self.current_phase.arena_effect == "spawn_adds" and random.random() < 0.02:
                # Would spawn adds in real implementation
                pass

        # Movement
        if dist > 2 and dist < self.arena_size:
            dx = (player.x - self.x) / dist if dist > 0 else 0
            dy = (player.y - self.y) / dist if dist > 0 else 0
            self.x += dx * 1.0 * dt
            self.y += dy * 1.0 * dt

        # Attack
        if self.current_phase and self.current_phase.can_attack() and dist <= 3:
            self.current_phase.on_attack()
            self.state = "attack"

            # Special ability
            if self.current_phase.special_ability and self.current_phase.ability_charges > 0:
                if random.random() < 0.3:
                    self.current_phase.ability_charges -= 1
                    self.state = "special"
                    return self.current_phase.special_ability
        else:
            self.state = "idle"

        return None

    def take_damage(self, amount):
        """Take damage, accounting for shields."""
        if self.shield_active and self.shield_hp > 0:
            self.shield_hp -= amount
            if self.shield_hp <= 0:
                self.shield_active = False
                self.shield_hp = 0
            return False

        self.hp -= amount
        self.damage_taken_this_phase += amount
        return self.hp <= 0

    def activate_shield(self, hp):
        self.shield_active = True
        self.shield_hp = hp

    def get_loot(self):
        """Roll loot from boss table."""
        loot = []
        for item, chance in self.loot_table:
            if random.random() < chance:
                loot.append(item)
        return loot

    def to_dict(self):
        return {
            "name": self.name,
            "title": self.title,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "phase": self.current_phase_idx + 1 if self.current_phase else 0,
            "enraged": self.enraged,
            "shield": self.shield_active,
            "state": self.state,
        }


class BossManager:
    """Manages all boss encounters."""

    BOSSES = {
        "ash_titan": {
            "name": "Ash Titan",
            "title": "The Scorched Colossus",
            "hp": 500,
            "phases": [
                BossPhase("Phase 1: Ember Wake", 1.0, "melee_rush", 2.0, 
                         special_ability="ember_slam", arena_effect=None),
                BossPhase("Phase 2: Ash Storm", 0.6, "ranged_bombard", 1.5,
                         special_ability="ash_nova", arena_effect="damage_over_time"),
                BossPhase("Phase 3: Core Exposure", 0.25, "desperate_charge", 1.0,
                         special_ability="core_detonate", arena_effect="lc_drain"),
            ],
            "loot": [
                ("titan_heart", 1.0),
                ("ashborn_plate", 0.5),
                ("ember_core", 0.3),
            ],
            "intro": "The ground splits. Molten ash rises. The Titan awakens.",
            "defeat": "The Titan crumbles. Its core dims. The ash settles.",
        },
        "hollow_queen": {
            "name": "Hollow Queen",
            "title": "She Who Devours Light",
            "hp": 400,
            "phases": [
                BossPhase("Phase 1: Shadow Weaver", 1.0, "stealth_strike", 2.5,
                         special_ability="shadow_web", arena_effect=None),
                BossPhase("Phase 2: Brood Mother", 0.5, "summon_swarm", 3.0,
                         special_ability="brood_call", arena_effect="spawn_adds"),
                BossPhase("Phase 3: Void Heart", 0.2, "desperate_drain", 1.5,
                         special_ability="void_vortex", arena_effect="lc_drain"),
            ],
            "loot": [
                ("queens_crown", 1.0),
                ("void_shard", 0.5),
                ("hollow_essence", 0.3),
            ],
            "intro": "The darkness breathes. Eight eyes open. The Queen descends.",
            "defeat": "The Queen screams silently. Her brood scatters. Light returns.",
        },
        "iron_overseer": {
            "name": "Iron Overseer",
            "title": "Fist of the Ferro Compact",
            "hp": 600,
            "phases": [
                BossPhase("Phase 1: Forge Guard", 1.0, "shield_bash", 2.0,
                         special_ability="forge_hammer", arena_effect=None),
                BossPhase("Phase 2: Assembly Line", 0.55, "drone_swarm", 2.5,
                         special_ability="drone_bombardment", arena_effect="spawn_adds"),
                BossPhase("Phase 3: Meltdown", 0.2, "suicide_charge", 1.0,
                         special_ability="core_meltdown", arena_effect="damage_over_time"),
            ],
            "loot": [
                ("overseer_cog", 1.0),
                ("ferro_plating", 0.5),
                ("melted_core", 0.3),
            ],
            "intro": "Gears scream. Furnaces roar. The Overseer marches.",
            "defeat": "The Overseer falls. Its gears grind to silence. The forge cools.",
        },
        "chorus_prime": {
            "name": "Chorus Prime",
            "title": "The Resonant One",
            "hp": 450,
            "phases": [
                BossPhase("Phase 1: Harmonic Shield", 1.0, "buff_and_strike", 2.5,
                         special_ability="sonic_barrier", arena_effect=None),
                BossPhase("Phase 2: Dissonance", 0.5, "debuff_spam", 2.0,
                         special_ability="dissonant_wave", arena_effect="lc_drain"),
                BossPhase("Phase 3: Crescendo", 0.15, "all_out_assault", 0.8,
                         special_ability="final_crescendo", arena_effect="damage_over_time"),
            ],
            "loot": [
                ("prime_resonator", 1.0),
                ("harmonic_crystal", 0.5),
                ("dissonant_echo", 0.3),
            ],
            "intro": "The air vibrates. A single note becomes a symphony of war.",
            "defeat": "The Prime shatters. Its resonance fades. Silence falls.",
        },
    }

    def __init__(self):
        self.active_boss = None
        self.defeated_bosses = []

    def spawn_boss(self, boss_id, x=32, y=32):
        """Spawn a boss by ID."""
        template = self.BOSSES.get(boss_id)
        if not template:
            return None

        boss = Boss(
            name=template["name"],
            title=template["title"],
            hp=template["hp"],
            phases=template["phases"],
            loot_table=template["loot"],
            intro_text=template["intro"],
            defeat_text=template["defeat"],
        )
        boss.x = x
        boss.y = y
        self.active_boss = boss
        return boss

    def get_available_bosses(self):
        """Get list of undefeated bosses."""
        return [bid for bid in self.BOSSES.keys() if bid not in self.defeated_bosses]

    def on_boss_defeated(self, boss):
        """Handle boss defeat."""
        self.defeated_bosses.append(boss.name.lower().replace(" ", "_"))
        self.active_boss = None
        return boss.get_loot()
