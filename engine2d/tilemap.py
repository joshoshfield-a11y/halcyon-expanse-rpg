"""
Halcyon Expanse — 2D Top-Down Tilemap Engine
Tile-based world with biomes, entities, collision, and lighting.
"""
import random
import numpy as np

TILE_SIZE = 32  # pixels per tile

TILE_TYPES = {
    "floor": {"char": ".", "color": (40, 40, 40), "walkable": True},
    "wall": {"char": "#", "color": (80, 80, 80), "walkable": False},
    "water": {"char": "~", "color": (30, 60, 90), "walkable": False},
    "lava": {"char": "^", "color": (180, 60, 20), "walkable": False, "damage": 5},
    "grass": {"char": ",", "color": (34, 85, 51), "walkable": True},
    "sand": {"char": ":", "color": (194, 178, 128), "walkable": True},
    "snow": {"char": "*", "color": (220, 220, 230), "walkable": True},
    "swamp": {"char": ";", "color": (45, 65, 35), "walkable": True, "slow": 0.5},
    "crystal": {"char": "+", "color": (120, 80, 160), "walkable": True, "glow": True},
    "ash": {"char": "`", "color": (60, 55, 50), "walkable": True},
    "iron_floor": {"char": "=", "color": (70, 75, 80), "walkable": True},
    "void": {"char": " ", "color": (10, 10, 15), "walkable": False},
    "seam_gate": {"char": "O", "color": (200, 180, 100), "walkable": True, "interactive": True},
}

BIOME_TILESETS = {
    "temperate": {"floor": "grass", "wall": "wall", "water": "water", "special": "crystal"},
    "capital": {"floor": "iron_floor", "wall": "wall", "water": "water", "special": "seam_gate"},
    "urban": {"floor": "iron_floor", "wall": "wall", "water": "water", "special": "seam_gate"},
    "ashfall": {"floor": "ash", "wall": "wall", "water": "lava", "special": "crystal"},
    "volcanic": {"floor": "ash", "wall": "wall", "water": "lava", "special": "lava"},
    "ruins": {"floor": "ash", "wall": "wall", "water": "water", "special": "crystal"},
    "riverine": {"floor": "grass", "wall": "wall", "water": "water", "special": "crystal"},
    "wetlands": {"floor": "swamp", "wall": "wall", "water": "water", "special": "crystal"},
    "trade": {"floor": "iron_floor", "wall": "wall", "water": "water", "special": "seam_gate"},
    "low_light": {"floor": "floor", "wall": "wall", "water": "water", "special": "crystal"},
    "horror": {"floor": "floor", "wall": "wall", "water": "water", "special": "void"},
    "subterranean": {"floor": "floor", "wall": "wall", "water": "water", "special": "crystal"},
    "zero_g": {"floor": "void", "wall": "void", "water": "void", "special": "crystal"},
    "floating": {"floor": "void", "wall": "void", "water": "void", "special": "crystal"},
    "wind": {"floor": "ash", "wall": "wall", "water": "water", "special": "crystal"},
    "industrial": {"floor": "iron_floor", "wall": "wall", "water": "water", "special": "seam_gate"},
    "forge": {"floor": "iron_floor", "wall": "wall", "water": "lava", "special": "lava"},
    "acoustic": {"floor": "crystal", "wall": "wall", "water": "water", "special": "crystal"},
    "crystalline": {"floor": "crystal", "wall": "crystal", "water": "crystal", "special": "crystal"},
    "deep": {"floor": "floor", "wall": "wall", "water": "water", "special": "void"},
    "desert": {"floor": "sand", "wall": "wall", "water": "water", "special": "crystal"},
    "salt_flat": {"floor": "sand", "wall": "wall", "water": "water", "special": "crystal"},
    "barren": {"floor": "ash", "wall": "wall", "water": "water", "special": "ash"},
    "twilight": {"floor": "floor", "wall": "wall", "water": "water", "special": "crystal"},
    "fog": {"floor": "swamp", "wall": "wall", "water": "water", "special": "void"},
    "haunted": {"floor": "floor", "wall": "wall", "water": "water", "special": "void"},
}


class TileMap:
    """2D tile-based world map."""
    def __init__(self, width=64, height=64, biome="temperate", seed=None):
        self.width = width
        self.height = height
        self.biome = biome
        self.seed = seed or random.randint(0, 2**31)
        self.rng = random.Random(self.seed)
        self.tiles = [["floor" for _ in range(width)] for _ in range(height)]
        self.entities = []  # (x, y, entity_ref)
        self.lighting = [[1.0 for _ in range(width)] for _ in range(height)]
        self._generate()

    def _generate(self):
        tileset = BIOME_TILESETS.get(self.biome, BIOME_TILESETS["temperate"])

        for y in range(self.height):
            for x in range(self.width):
                noise = self.rng.random()
                if noise > 0.92:
                    self.tiles[y][x] = tileset["wall"]
                elif noise > 0.85:
                    self.tiles[y][x] = tileset["water"]
                elif noise > 0.80:
                    self.tiles[y][x] = tileset["special"]
                elif noise > 0.75:
                    self.tiles[y][x] = tileset.get("floor", "floor")
                else:
                    self.tiles[y][x] = tileset.get("floor", "floor")

        # Ensure spawn area is clear
        for y in range(2, 8):
            for x in range(2, 8):
                self.tiles[y][x] = tileset.get("floor", "floor")

        # Add seam gate at edge
        edge_x = self.width - 3
        edge_y = self.height // 2
        self.tiles[edge_y][edge_x] = "seam_gate"
        self.tiles[edge_y+1][edge_x] = "seam_gate"
        self.tiles[edge_y-1][edge_x] = "seam_gate"

    def is_walkable(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return TILE_TYPES.get(self.tiles[y][x], {}).get("walkable", True)
        return False

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return "void"

    def add_entity(self, entity, x, y):
        self.entities.append((x, y, entity))
        entity.x = x
        entity.y = y

    def move_entity(self, entity, dx, dy):
        new_x = entity.x + dx
        new_y = entity.y + dy
        if self.is_walkable(new_x, new_y):
            entity.x = new_x
            entity.y = new_y
            return True
        return False

    def update_lighting(self, player_x, player_y, radius=8):
        """Simple radial lighting with biome modifiers."""
        for y in range(self.height):
            for x in range(self.width):
                dist = ((x - player_x)**2 + (y - player_y)**2) ** 0.5
                if dist < radius:
                    self.lighting[y][x] = max(0.1, 1.0 - (dist / radius) * 0.8)
                else:
                    self.lighting[y][x] = 0.05

        # Biome lighting modifiers
        if self.biome in ["horror", "subterranean", "deep", "haunted"]:
            for y in range(self.height):
                for x in range(self.width):
                    self.lighting[y][x] *= 0.4
        elif self.biome in ["twilight", "fog"]:
            for y in range(self.height):
                for x in range(self.width):
                    self.lighting[y][x] *= 0.6
        elif self.biome in ["volcanic", "forge", "ashfall"]:
            for y in range(self.height):
                for x in range(self.width):
                    tile = self.tiles[y][x]
                    if tile in ["lava", "ash"]:
                        self.lighting[y][x] = min(1.0, self.lighting[y][x] + 0.3)

    def to_dict(self):
        return {
            "width": self.width, "height": self.height,
            "biome": self.biome, "seed": self.seed,
            "tiles": self.tiles,
        }
