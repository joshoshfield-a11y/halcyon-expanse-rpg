"""
Halcyon Expanse — Equipment System
Weapons, armor, accessories with stat bonuses and resonance requirements.
"""


class Equipment:
    """Base equipment item with stats."""

    SLOT_NAMES = ["weapon", "armor", "helmet", "accessory", "relic"]

    def __init__(self, item_id, name, slot, rarity="Common", 
                 resonance_req=None, attunement_req=1,
                 hp_bonus=0, lc_bonus=0, damage_bonus=0, defense_bonus=0,
                 lc_regen_bonus=0, debt_reduction=0, description=""):
        self.item_id = item_id
        self.name = name
        self.slot = slot
        self.rarity = rarity
        self.resonance_req = resonance_req
        self.attunement_req = attunement_req
        self.hp_bonus = hp_bonus
        self.lc_bonus = lc_bonus
        self.damage_bonus = damage_bonus
        self.defense_bonus = defense_bonus
        self.lc_regen_bonus = lc_regen_bonus
        self.debt_reduction = debt_reduction
        self.description = description
        self.equipped = False

    def can_equip(self, actor):
        """Check if actor can equip this item."""
        if self.resonance_req and actor.resonance_type != self.resonance_req:
            return False, f"Requires {self.resonance_req} resonance"
        if actor.attunement_level < self.attunement_req:
            return False, f"Requires attunement {self.attunement_req}"
        return True, "Can equip"

    def get_stat_text(self):
        stats = []
        if self.hp_bonus:
            stats.append(f"+{self.hp_bonus} HP")
        if self.lc_bonus:
            stats.append(f"+{self.lc_bonus} LC")
        if self.damage_bonus:
            stats.append(f"+{self.damage_bonus} DMG")
        if self.defense_bonus:
            stats.append(f"+{self.defense_bonus} DEF")
        if self.lc_regen_bonus:
            stats.append(f"+{self.lc_regen_bonus} LC/s")
        if self.debt_reduction:
            stats.append(f"-{self.debt_reduction}% Debt")
        return ", ".join(stats) if stats else "No bonuses"

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "name": self.name,
            "slot": self.slot,
            "rarity": self.rarity,
            "resonance_req": self.resonance_req,
            "attunement_req": self.attunement_req,
            "hp_bonus": self.hp_bonus,
            "lc_bonus": self.lc_bonus,
            "damage_bonus": self.damage_bonus,
            "defense_bonus": self.defense_bonus,
            "lc_regen_bonus": self.lc_regen_bonus,
            "debt_reduction": self.debt_reduction,
            "description": self.description,
        }


class EquipmentManager:
    """Manages equipped items and their effects."""

    def __init__(self):
        self.equipped = {}  # slot -> Equipment
        self.total_stats = {
            "hp_bonus": 0,
            "lc_bonus": 0,
            "damage_bonus": 0,
            "defense_bonus": 0,
            "lc_regen_bonus": 0,
            "debt_reduction": 0,
        }

    def equip(self, equipment, actor):
        """Equip an item, returning the previously equipped item if any."""
        can_equip, msg = equipment.can_equip(actor)
        if not can_equip:
            return False, msg, None

        old_item = self.equipped.get(equipment.slot)
        self.equipped[equipment.slot] = equipment
        equipment.equipped = True
        if old_item:
            old_item.equipped = False

        self._recalculate_stats()
        return True, f"Equipped {equipment.name}", old_item

    def unequip(self, slot):
        """Unequip an item from a slot."""
        item = self.equipped.pop(slot, None)
        if item:
            item.equipped = False
            self._recalculate_stats()
            return item
        return None

    def _recalculate_stats(self):
        """Recalculate total stat bonuses from all equipped items."""
        self.total_stats = {
            "hp_bonus": 0,
            "lc_bonus": 0,
            "damage_bonus": 0,
            "defense_bonus": 0,
            "lc_regen_bonus": 0,
            "debt_reduction": 0,
        }
        for item in self.equipped.values():
            self.total_stats["hp_bonus"] += item.hp_bonus
            self.total_stats["lc_bonus"] += item.lc_bonus
            self.total_stats["damage_bonus"] += item.damage_bonus
            self.total_stats["defense_bonus"] += item.defense_bonus
            self.total_stats["lc_regen_bonus"] += item.lc_regen_bonus
            self.total_stats["debt_reduction"] += item.debt_reduction

    def get_equipped_in_slot(self, slot):
        return self.equipped.get(slot)

    def get_all_equipped(self):
        return list(self.equipped.values())

    def to_dict(self):
        return {
            "equipped": {slot: item.to_dict() for slot, item in self.equipped.items()},
            "total_stats": self.total_stats,
        }
