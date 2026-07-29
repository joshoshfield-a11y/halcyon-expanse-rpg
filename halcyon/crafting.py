"""
Halcyon Expanse — Crafting System
Recipes, material requirements, forging, enchanting.
"""
import random


class Recipe:
    """A crafting recipe."""
    def __init__(self, recipe_id, name, result_item, materials, 
                 resonance_req=None, attunement_req=1, crafting_time=1.0,
                 description=""):
        self.recipe_id = recipe_id
        self.name = name
        self.result_item = result_item
        self.materials = materials  # {item_id: count}
        self.resonance_req = resonance_req
        self.attunement_req = attunement_req
        self.crafting_time = crafting_time
        self.description = description

    def can_craft(self, inventory, actor):
        """Check if player can craft this recipe."""
        if self.resonance_req and actor.resonance_type != self.resonance_req:
            return False, f"Requires {self.resonance_req} resonance"
        if actor.attunement_level < self.attunement_req:
            return False, f"Requires attunement {self.attunement_req}"

        for item_id, needed in self.materials.items():
            have = sum(1 for item in inventory.items if item.item_id == item_id)
            if have < needed:
                return False, f"Need {needed}x {item_id}, have {have}"

        return True, "Can craft"

    def get_materials_text(self):
        return ", ".join(f"{count}x {item_id}" for item_id, count in self.materials.items())


class CraftingSystem:
    """Manages all crafting recipes and operations."""

    def __init__(self):
        self.recipes = {}
        self._init_default_recipes()

    def _init_default_recipes(self):
        """Initialize default crafting recipes."""
        default_recipes = [
            Recipe("healing_potion", "Glowroot Tincture", "healing_potion",
                  {"glowroot": 2, "water": 1},
                  description="Restores 30 HP"),
            Recipe("lc_potion", "Lattice Elixir", "lc_potion",
                  {"crystal_shard": 2, "ember_dust": 1},
                  description="Restores 100 LC"),
            Recipe("iron_blade", "Iron Blade", "iron_blade",
                  {"iron_ore": 3, "coal": 2},
                  attunement_req=2,
                  description="Weapon: +8 DMG"),
            Recipe("ashborn_plate", "Ashborn Plate", "ashborn_plate",
                  {"ash_essence": 3, "iron_ore": 2, "titan_heart": 1},
                  resonance_req="Ember", attunement_req=3,
                  description="Armor: +15 DEF, +20 HP"),
            Recipe("void_cloak", "Void Cloak", "void_cloak",
                  {"void_shard": 2, "shadow_silk": 3},
                  resonance_req="Hollow", attunement_req=4,
                  description="Armor: +10 DEF, stealth bonus"),
            Recipe("harmonic_amplifier", "Harmonic Amplifier", "harmonic_amplifier",
                  {"harmonic_crystal": 2, "prime_resonator": 1, "gold_wire": 2},
                  resonance_req="Chorus", attunement_req=5,
                  description="Accessory: +30 LC, +5 LC/s, ability damage +20%"),
            Recipe("concord_badge", "Concord Badge", "concord_badge",
                  {"gold_bar": 1, "concord_seal": 1},
                  attunement_req=2,
                  description="Relic: +20 HP, -5% debt"),
            Recipe("ember_core", "Ember Core", "ember_core",
                  {"ember_shard": 5, "magma_stone": 2, "titan_heart": 1},
                  resonance_req="Ember", attunement_req=5,
                  description="Relic: +50 LC, +5 DMG, ember abilities cost -20%"),
        ]
        for recipe in default_recipes:
            self.recipes[recipe.recipe_id] = recipe

    def get_available_recipes(self, inventory, actor):
        """Get recipes the player can currently craft."""
        available = []
        for recipe in self.recipes.values():
            can_craft, _ = recipe.can_craft(inventory, actor)
            if can_craft:
                available.append(recipe)
        return available

    def get_all_recipes(self):
        return list(self.recipes.values())

    def craft(self, recipe_id, inventory, actor):
        """Attempt to craft a recipe."""
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            return False, "Recipe not found"

        can_craft, msg = recipe.can_craft(inventory, actor)
        if not can_craft:
            return False, msg

        # Consume materials
        for item_id, needed in recipe.materials.items():
            removed = 0
            for item in inventory.items[:]:
                if item.item_id == item_id and removed < needed:
                    inventory.items.remove(item)
                    removed += 1

        return True, f"Crafted {recipe.name}"

    def to_dict(self):
        return {"recipes": [r.recipe_id for r in self.recipes.values()]}
