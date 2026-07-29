"""
Halcyon Expanse — Ability System
Build Step 3: Reads ability rows, resolves cost via resonance_adjacency_rule.
7-node resonance wheel: Ember-Gale-Hollow-Tide-Root-Iron-Chorus
Ring distance: min(|a-b|, 7-|a-b|)
Cost multipliers: 0=native 1.4x, 1=adjacent 1.0x, 2=neutral 0.8x, 3=opposed 0.6x
"""
import json
import os

RESONANCE_ORDER = ["Ember", "Gale", "Hollow", "Tide", "Root", "Iron", "Chorus"]
COST_MULTIPLIERS = {0: 1.4, 1: 1.0, 2: 0.8, 3: 0.6}


class Ability:
    """Single ability instance from ability_row_schema."""
    def __init__(self, ability_id, name, base_lc_cost, resonance_type, tier, description=""):
        self.ability_id = ability_id
        self.name = name
        self.base_lc_cost = float(base_lc_cost)
        self.resonance_type = resonance_type
        self.tier = int(tier)
        self.description = description

    def to_dict(self):
        return {
            "ability_id": self.ability_id,
            "name": self.name,
            "base_lc_cost": self.base_lc_cost,
            "resonance_type": self.resonance_type,
            "tier": self.tier,
            "description": self.description,
        }


class AbilitySystem:
    """Manages ability database and cost resolution."""
    def __init__(self, config_path=None):
        self.abilities = {}  # ability_id -> Ability
        self._config_path = config_path
        if config_path and os.path.exists(config_path):
            self.load_from_json(config_path)

    def load_from_json(self, path):
        with open(path) as f:
            data = json.load(f)
        for row in data.get("abilities", []):
            self.register_ability(Ability(**row))

    def register_ability(self, ability):
        self.abilities[ability.ability_id] = ability

    @staticmethod
    def resonance_distance(type_a, type_b):
        """Compute ring distance on 7-node resonance wheel."""
        if type_a not in RESONANCE_ORDER or type_b not in RESONANCE_ORDER:
            return 3  # default to opposed for unknown types
        idx_a = RESONANCE_ORDER.index(type_a)
        idx_b = RESONANCE_ORDER.index(type_b)
        dist = abs(idx_a - idx_b)
        return min(dist, 7 - dist)

    def resolve_cost(self, ability_id, actor_resonance):
        """Resolve LC cost for an ability based on actor resonance adjacency."""
        ability = self.abilities.get(ability_id)
        if not ability:
            return None
        dist = self.resonance_distance(ability.resonance_type, actor_resonance)
        multiplier = COST_MULTIPLIERS.get(dist, 0.6)
        return ability.base_lc_cost * multiplier

    def can_cast(self, ability_id, actor):
        """Check if actor can afford the resolved cost."""
        cost = self.resolve_cost(ability_id, actor.resonance_type)
        if cost is None:
            return False
        return actor.lattice_charge >= cost and not actor._hollowed_zone_active

    def cast(self, ability_id, actor):
        """Attempt to cast an ability. Returns (success, message)."""
        cost = self.resolve_cost(ability_id, actor.resonance_type)
        if cost is None:
            return False, f"Ability {ability_id} not found"
        if actor._hollowed_zone_active:
            return False, "Lattice Actions blocked in Hollowed Zone"
        if actor.consume_lc(cost):
            ability = self.abilities[ability_id]
            return True, f"Cast {ability.name} for {cost:.1f} LC"
        return False, f"Insufficient LC (need {cost:.1f}, have {actor.lattice_charge:.1f})"

    def list_abilities(self):
        return list(self.abilities.values())
