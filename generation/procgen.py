

"""
Procedural Generation Subsystem
--------------------------------
Prompt-driven world/asset generation. Accepts natural language prompts
(parsed by interface.prompt_parser) and produces terrain, dungeons,
NPCs, items, and quest structures using seeded deterministic algorithms.
"""
import random

class WorldGenerator:
    BIOMES = ["forest", "desert", "tundra", "swamp", "volcanic", "ocean", "grassland", "cave"]

    def __init__(self, rng: random.Random):
        self.rng = rng

    def generate_chunk(self, width=32, height=32, biome=None):
        biome = biome or self.rng.choice(self.BIOMES)
        grid = [[self._tile(biome) for _ in range(width)] for _ in range(height)]
        return {"biome": biome, "width": width, "height": height, "grid": grid}

    def _tile(self, biome):
        density = self.rng.random()
        if density > 0.85:
            return "obstacle"
        if density > 0.6:
            return "resource"
        return "floor"

    def generate_dungeon(self, depth=1, rooms=None):
        rooms = rooms or (5 + depth * 2)
        layout = []
        for i in range(rooms):
            layout.append({
                "room_id": i,
                "size": (self.rng.randint(4, 12), self.rng.randint(4, 12)),
                "connections": [j for j in range(rooms) if j != i and self.rng.random() < 0.2],
                "encounter": self._roll_encounter(depth),
            })
        return {"depth": depth, "rooms": layout}

    def _roll_encounter(self, depth):
        table = ["empty", "trap", "treasure", "monster", "puzzle", "shrine"]
        weights = [30, 15, 15, 25, 10, 5]
        return self.rng.choices(table, weights=weights, k=1)[0]


class NPCGenerator:
    ARCHETYPES = ["merchant", "guard", "sage", "outlaw", "wanderer", "artisan", "noble", "hermit"]
    TRAITS = ["cautious", "greedy", "loyal", "cunning", "honorable", "erratic", "stoic", "curious"]

    def __init__(self, rng: random.Random):
        self.rng = rng

    def generate(self, name_seed=None):
        return {
            "archetype": self.rng.choice(self.ARCHETYPES),
            "traits": self.rng.sample(self.TRAITS, k=2),
            "disposition": self.rng.randint(-100, 100),
            "inventory_seed": self.rng.randint(0, 99999),
        }


class QuestGenerator:
    TEMPLATES = [
        "retrieve the {item} from the {location}",
        "defeat the {enemy} threatening {location}",
        "deliver a message to the {npc_role} in {location}",
        "escort the {npc_role} safely to {location}",
        "uncover the secret of the {item}",
    ]

    def __init__(self, rng: random.Random):
        self.rng = rng

    def generate(self, item="artifact", location="ruins", enemy="warlord", npc_role="elder"):
        template = self.rng.choice(self.TEMPLATES)
        text = template.format(item=item, location=location, enemy=enemy, npc_role=npc_role)
        return {"description": text, "difficulty": self.rng.randint(1, 10)}
