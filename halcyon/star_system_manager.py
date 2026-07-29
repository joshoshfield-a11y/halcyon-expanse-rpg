"""
Halcyon Expanse — Star System Manager
Build Step 4: Seam graph adjacency for fast-travel/warp and level-streaming.
Fixed non-fully-connected graph. One scene per system.
"""
import json


class StarSystem:
    def __init__(self, name, biome_tags, connected_systems):
        self.name = name
        self.biome_tags = biome_tags
        self.connected_systems = connected_systems
        self.visited = False
        self.discovered = False

    def to_dict(self):
        return {
            "name": self.name,
            "biome_tags": self.biome_tags,
            "connected_systems": self.connected_systems,
            "visited": self.visited,
            "discovered": self.discovered,
        }


class StarSystemManager:
    """Manages the 9 fixed star systems and seam graph travel."""

    SYSTEM_ORDER = ["VeyraPrime", "Ashduin", "TwoRivers", "HollowAnchor",
                    "GalesReach", "IronMeridian", "ChorusDeep", "SaltWastes", "HushMarches"]

    DEFAULT_ADJACENCY = {
        "VeyraPrime": ["Ashduin", "TwoRivers"],
        "Ashduin": ["VeyraPrime", "TwoRivers", "HollowAnchor"],
        "TwoRivers": ["VeyraPrime", "Ashduin", "GalesReach"],
        "HollowAnchor": ["Ashduin", "GalesReach", "IronMeridian"],
        "GalesReach": ["TwoRivers", "HollowAnchor", "IronMeridian", "ChorusDeep"],
        "IronMeridian": ["HollowAnchor", "GalesReach", "ChorusDeep", "SaltWastes"],
        "ChorusDeep": ["GalesReach", "IronMeridian", "SaltWastes", "HushMarches"],
        "SaltWastes": ["IronMeridian", "ChorusDeep", "HushMarches"],
        "HushMarches": ["ChorusDeep", "SaltWastes"],
    }

    DEFAULT_BIOMES = {
        "VeyraPrime": ["temperate", "capital", "urban"],
        "Ashduin": ["ashfall", "volcanic", "ruins"],
        "TwoRivers": ["riverine", "wetlands", "trade"],
        "HollowAnchor": ["low_light", "horror", "subterranean"],
        "GalesReach": ["zero_g", "floating", "wind"],
        "IronMeridian": ["industrial", "zero_g", "forge"],
        "ChorusDeep": ["acoustic", "crystalline", "deep"],
        "SaltWastes": ["desert", "salt_flat", "barren"],
        "HushMarches": ["twilight", "fog", "haunted"],
    }

    def __init__(self, config_path=None):
        self.systems = {}
        self.current_system = "VeyraPrime"
        self._load_defaults()
        if config_path:
            self.load_from_config(config_path)

    def _load_defaults(self):
        for name in self.SYSTEM_ORDER:
            self.systems[name] = StarSystem(
                name=name,
                biome_tags=self.DEFAULT_BIOMES.get(name, []),
                connected_systems=self.DEFAULT_ADJACENCY.get(name, [])
            )
        self.systems["VeyraPrime"].discovered = True
        self.systems["VeyraPrime"].visited = True

    def load_from_config(self, path):
        with open(path) as f:
            data = json.load(f)
        cfg = data.get("star_systems", {})
        for name in cfg.get("order", []):
            if name in self.systems:
                self.systems[name].biome_tags = cfg.get("biome_tags", {}).get(name, [])
                self.systems[name].connected_systems = cfg.get("seam_graph_adjacency", {}).get(name, [])

    def get_available_warp_targets(self, system_name=None):
        """Return list of systems reachable via Seam from current or specified system."""
        name = system_name or self.current_system
        sys_obj = self.systems.get(name)
        if not sys_obj:
            return []
        return [self.systems[s] for s in sys_obj.connected_systems if s in self.systems]

    def warp(self, target_name):
        """Attempt to warp to target system. Returns (success, message)."""
        if target_name not in self.systems:
            return False, f"System {target_name} does not exist"
        if target_name not in self.systems[self.current_system].connected_systems:
            return False, f"No Seam connection from {self.current_system} to {target_name}"
        self.current_system = target_name
        self.systems[target_name].discovered = True
        self.systems[target_name].visited = True
        return True, f"Warped to {target_name}"

    def get_current_scene_name(self):
        """Return scene name for level streaming."""
        return f"scene_{self.current_system}"

    def get_current_biome_tags(self):
        return self.systems.get(self.current_system, StarSystem("", [], [])).biome_tags

    def to_dict(self):
        return {
            "current_system": self.current_system,
            "systems": {k: v.to_dict() for k, v in self.systems.items()},
        }
