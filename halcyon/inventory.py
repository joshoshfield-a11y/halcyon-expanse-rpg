"""
Halcyon Expanse — Inventory System
Build Step 9: Rarity tiers with color-coded UI borders.
Common(white), Uncommon(green), Rare(blue), Legendary(gold)
"""


RARITY_TIERS = {
    "Common": {"color": "white", "border_hex": "#FFFFFF", "drop_weight": 60},
    "Uncommon": {"color": "green", "border_hex": "#00FF00", "drop_weight": 25},
    "Rare": {"color": "blue", "border_hex": "#0000FF", "drop_weight": 12},
    "Legendary": {"color": "gold", "border_hex": "#FFD700", "drop_weight": 3},
}


class Item:
    """Single inventory item with rarity."""
    def __init__(self, item_id, name, rarity="Common", item_type="misc", data=None):
        if rarity not in RARITY_TIERS:
            raise ValueError(f"Invalid rarity: {rarity}")
        self.item_id = item_id
        self.name = name
        self.rarity = rarity
        self.item_type = item_type
        self.data = data or {}
        self.rarity_info = RARITY_TIERS[rarity]

    def get_border_color(self):
        return self.rarity_info["border_hex"]

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "name": self.name,
            "rarity": self.rarity,
            "item_type": self.item_type,
            "border_color": self.get_border_color(),
            "data": self.data,
        }


class Inventory:
    """Player inventory with rarity-weighted drops."""
    def __init__(self, capacity=50):
        self.items = []
        self.capacity = capacity

    def add_item(self, item):
        if len(self.items) >= self.capacity:
            return False, "Inventory full"
        self.items.append(item)
        return True, f"Added {item.name} ({item.rarity})"

    def remove_item(self, item_id):
        for i, item in enumerate(self.items):
            if item.item_id == item_id:
                return self.items.pop(i)
        return None

    def get_by_rarity(self, rarity):
        return [item for item in self.items if item.rarity == rarity]

    def to_dict(self):
        return {
            "capacity": self.capacity,
            "items": [item.to_dict() for item in self.items],
            "count": len(self.items),
        }
