"""
Halcyon Expanse — Scene Manager
Build Step 5: Nine placeholder scenes named per star_systems.order,
tagged with biome_tags for material/lighting presets.
"""
import json


class Scene:
    def __init__(self, name, biome_tags, lighting_preset="default"):
        self.name = name
        self.biome_tags = biome_tags
        self.lighting_preset = lighting_preset
        self.loaded = False
        self.entities = []

    def get_lighting_profile(self):
        """Map biome tags to lighting preset names."""
        tag_map = {
            "low_light": "horror_dark",
            "horror": "horror_dark",
            "subterranean": "cave_dim",
            "zero_g": "space_ambient",
            "floating": "space_ambient",
            "volcanic": "lava_glow",
            "ashfall": "smoke_haze",
            "twilight": "dusk_blue",
            "fog": "volumetric_fog",
            "haunted": "ghostly_green",
            "industrial": "neon_orange",
            "forge": "forge_heat",
            "acoustic": "crystal_resonance",
            "crystalline": "crystal_resonance",
            "deep": "abyssal_black",
            "desert": "sun_bleached",
            "salt_flat": "white_blinding",
            "barren": "dead_grey",
            "temperate": "daylight_standard",
            "capital": "urban_neon",
            "urban": "urban_neon",
            "riverine": "water_blue",
            "wetlands": "swamp_murk",
            "trade": "market_gold",
            "wind": "wind_swept",
        }
        for tag in self.biome_tags:
            if tag in tag_map:
                return tag_map[tag]
        return "default"

    def to_dict(self):
        return {
            "name": self.name,
            "biome_tags": self.biome_tags,
            "lighting_preset": self.get_lighting_profile(),
            "loaded": self.loaded,
        }


class SceneManager:
    """Manages 9 placeholder scenes, one per star system."""

    SYSTEM_ORDER = ["VeyraPrime", "Ashduin", "TwoRivers", "HollowAnchor",
                    "GalesReach", "IronMeridian", "ChorusDeep", "SaltWastes", "HushMarches"]

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
        self.scenes = {}
        self._load_defaults()
        if config_path:
            self.load_from_config(config_path)

    def _load_defaults(self):
        for name in self.SYSTEM_ORDER:
            self.scenes[name] = Scene(
                name=f"scene_{name}",
                biome_tags=self.DEFAULT_BIOMES.get(name, [])
            )

    def load_from_config(self, path):
        with open(path) as f:
            data = json.load(f)
        cfg = data.get("star_systems", {})
        for name in cfg.get("order", []):
            if name in self.scenes:
                self.scenes[name].biome_tags = cfg.get("biome_tags", {}).get(name, [])

    def get_scene(self, system_name):
        return self.scenes.get(system_name)

    def load_scene(self, system_name):
        scene = self.scenes.get(system_name)
        if scene:
            scene.loaded = True
            return scene
        return None

    def unload_scene(self, system_name):
        scene = self.scenes.get(system_name)
        if scene:
            scene.loaded = False

    def to_dict(self):
        return {k: v.to_dict() for k, v in self.scenes.items()}
