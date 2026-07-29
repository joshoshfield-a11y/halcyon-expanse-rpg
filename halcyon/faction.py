"""
Halcyon Expanse — Faction System
Build Step 7: Faction reputation with archetype-based quest-giver behavior.
5 major factions + Ashborn hostile wilderness.
"""
import random


class Faction:
    """Single faction with reputation, home regions, and archetype."""
    def __init__(self, name, home_regions, archetype, reputation=0):
        self.name = name
        self.home_regions = home_regions if isinstance(home_regions, list) else [home_regions]
        self.archetype = archetype
        self.reputation = max(-100, min(100, reputation))
        self.quest_giver_preset = self._derive_quest_preset()

    def _derive_quest_preset(self):
        """Map archetype to quest-giver behavior preset."""
        presets = {
            "bureaucratic_democracy": "formal_procedure",
            "industrial_oligarchy": "resource_demand",
            "mystic_theocracy": "ritual_requirement",
            "mercantile_guild": "trade_offer",
            "hostile_wilderness": "aggressive_threat",
        }
        return presets.get(self.archetype, "generic")

    def modify_reputation(self, delta):
        self.reputation = max(-100, min(100, self.reputation + delta))
        return self.reputation

    def get_standing(self):
        if self.reputation >= 80:
            return "Ally"
        elif self.reputation >= 40:
            return "Friendly"
        elif self.reputation >= 10:
            return "Cordial"
        elif self.reputation > -10:
            return "Neutral"
        elif self.reputation > -40:
            return "Unfriendly"
        elif self.reputation > -80:
            return "Hostile"
        return "Enemy"

    def to_dict(self):
        return {
            "name": self.name,
            "home_regions": self.home_regions,
            "archetype": self.archetype,
            "reputation": self.reputation,
            "standing": self.get_standing(),
            "quest_preset": self.quest_giver_preset,
        }


class FactionManager:
    """Manages all factions and pairwise relations."""

    DEFAULT_FACTIONS = {
        "Concord Table": {"home": ["VeyraPrime"], "archetype": "bureaucratic_democracy"},
        "Ferro Compact": {"home": ["IronMeridian", "SaltWastes"], "archetype": "industrial_oligarchy"},
        "Hollow Choir": {"home": ["HollowAnchor"], "archetype": "mystic_theocracy"},
        "Gale Syndicate": {"home": ["GalesReach"], "archetype": "mercantile_guild"},
        "Ashborn": {"home": ["Ashduin"], "archetype": "hostile_wilderness"},
    }

    def __init__(self, config_path=None, rng=None):
        self.factions = {}
        self.rng = rng or random.Random()
        self._load_defaults()

    def _load_defaults(self):
        for name, data in self.DEFAULT_FACTIONS.items():
            self.factions[name] = Faction(
                name=name,
                home_regions=data["home"],
                archetype=data["archetype"]
            )

    def get_faction(self, name):
        return self.factions.get(name)

    def modify_reputation(self, faction_name, delta):
        faction = self.factions.get(faction_name)
        if faction:
            return faction.modify_reputation(delta)
        return None

    def get_factions_in_region(self, region):
        return [f for f in self.factions.values() if region in f.home_regions]

    def to_dict(self):
        return {k: v.to_dict() for k, v in self.factions.items()}
