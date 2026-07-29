"""
Halcyon Expanse — 2D Top-Down Game Loop
Real-time game loop with input handling, physics, combat, and rendering.
"""
import time
import sys
import os
import math

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import Engine, Subsystem
from core.state import GameState
from generation.procgen import WorldGenerator
from simulation.simcore import Entity, PhysicsSim
from rendering.renderer import ASCIIRenderer

from halcyon.actor import Actor, RESONANCE_TYPES
from halcyon.ability_system import AbilitySystem, Ability
from halcyon.star_system_manager import StarSystemManager
from halcyon.scene_manager import SceneManager
from halcyon.hollowed_zone import HollowedZoneManager
from halcyon.faction import FactionManager
from halcyon.economy import Economy
from halcyon.inventory import Inventory, Item
from halcyon.bestiary import Bestiary
from halcyon.codex import Codex

from engine2d.tilemap import TileMap, BIOME_TILESETS
from engine2d.renderer2d import Renderer2D
from engine2d.combat import CombatSystem

CURRENT_YEAR = 706


class Game2D:
    """Main 2D top-down RPG game class."""

    def __init__(self, seed=None, player_resonance="Ember", use_visual=True):
        self.seed = seed or 78
        self.player_resonance = player_resonance
        self.use_visual = use_visual

        # Systems
        self.ability_system = AbilitySystem()
        self.star_systems = StarSystemManager()
        self.scenes = SceneManager()
        self.hollowed_zones = HollowedZoneManager()
        self.factions = FactionManager()
        self.economy = Economy()
        self.inventory = Inventory(capacity=30)
        self.bestiary = Bestiary()
        self.codex = Codex()
        self.combat = None

        # World
        self.tilemap = None
        self.renderer = Renderer2D()
        self.use_visual = use_visual
        self.ascii_renderer = ASCIIRenderer()

        # Player
        self.player = None

        # Game state
        self.running = False
        self.frame_count = 0
        self.last_frame_time = time.time()
        self.dt = 0.016  # ~60 FPS target

        # Camera
        self.camera_x = 0
        self.camera_y = 0

        self._init_game()

    def _init_game(self):
        """Initialize all game systems."""
        # Register abilities
        abilities = [
            Ability("ember_strike", "Ember Strike", 50, "Ember", 1, "Fire melee attack"),
            Ability("gale_dash", "Gale Dash", 40, "Gale", 1, "Wind dash forward"),
            Ability("tide_heal", "Tide Heal", 60, "Tide", 1, "Restore HP"),
            Ability("hollow_drain", "Hollow Drain", 70, "Hollow", 2, "Drain enemy LC"),
            Ability("iron_shield", "Iron Shield", 45, "Iron", 1, "Block next attack"),
            Ability("root_bind", "Root Bind", 55, "Root", 1, "Immobilize target"),
            Ability("chorus_blast", "Chorus Blast", 80, "Chorus", 2, "Sonic area damage"),
        ]
        for ab in abilities:
            self.ability_system.register_ability(ab)

        # Create player
        self.player = Actor(
            kind="player",
            x=5, y=5, hp=100,
            resonance_type=self.player_resonance,
            attunement_level=1,
            lattice_charge=500.0,
            lattice_debt=0.0
        )
        self.player.data["shield_active"] = False
        self.player.data["shield_duration"] = 0.0

        # Starting items
        self.inventory.add_item(Item("starter_sword", "Rusty Blade", "Common", "weapon"))
        self.inventory.add_item(Item("healing_potion", "Glowroot Tincture", "Uncommon", "consumable"))
        self.inventory.add_item(Item("ember_shard", "Ember Shard", "Rare", "material"))

        # Load initial scene
        self._load_system("VeyraPrime")

        # Check codex
        self.codex.check_triggers(location="VeyraPrime")

    def _load_system(self, system_name):
        """Load a star system as a tilemap."""
        scene = self.scenes.get_scene(system_name)
        biome = scene.biome_tags[0] if scene.biome_tags else "temperate"

        self.tilemap = TileMap(width=64, height=64, biome=biome, seed=self.seed + hash(system_name) % 10000)
        self.tilemap.add_entity(self.player, self.player.x, self.player.y)

        # Spawn some enemies based on system
        enemy_count = {"VeyraPrime": 1, "Ashduin": 3, "HollowAnchor": 4, "GalesReach": 2,
                       "IronMeridian": 3, "ChorusDeep": 2, "SaltWastes": 2, "HushMarches": 3,
                       "TwoRivers": 1}.get(system_name, 2)

        enemy_types = ["Ash Wraith", "Ferro Drone", "Hollow Stalker", "Tide Leviathan", "Chorus Hymnal", "Salt Scarab"]
        for _ in range(enemy_count):
            etype = self.tilemap.rng.choice(enemy_types)
            ex = self.tilemap.rng.randint(10, 55)
            ey = self.tilemap.rng.randint(10, 55)
            if self.tilemap.is_walkable(ex, ey):
                enemy = self.bestiary.spawn(etype, x=ex, y=ey)

        self.combat = CombatSystem(self.ability_system, self.bestiary, self.tilemap)
        self.star_systems.current_system = system_name
        self.scenes.load_scene(system_name)

        # Check hollowed zones
        zones = self.hollowed_zones.get_zones_in_system(system_name)
        for zone in zones:
            zone.on_enter(self.player)

    def move_player(self, dx, dy):
        """Move player with collision."""
        if self.tilemap.move_entity(self.player, dx, dy):
            self.player.update_debt()
            self.player.regenerate_lc(self.dt)

            # Check for seam gate interaction
            tile = self.tilemap.get_tile(int(self.player.x), int(self.player.y))
            if tile == "seam_gate":
                return "seam_gate"
        return None

    def interact(self):
        """Interact with current tile."""
        tile = self.tilemap.get_tile(int(self.player.x), int(self.player.y))
        if tile == "seam_gate":
            return self._show_warp_menu()
        return "Nothing to interact with"

    def _show_warp_menu(self):
        """Show available warp targets."""
        targets = self.star_systems.get_available_warp_targets()
        names = [t.name for t in targets]
        return f"SEAM GATE — Available destinations: {', '.join(names)}"

    def warp(self, target_name):
        """Warp to another system."""
        success, msg = self.star_systems.warp(target_name)
        if success:
            # Exit current hollowed zones
            zones = self.hollowed_zones.get_zones_in_system(self.star_systems.current_system)
            for zone in zones:
                zone.on_exit(self.player)

            self._load_system(target_name)
            self.codex.check_triggers(location=target_name)
            return f"WARPED to {target_name}"
        return msg

    def cast_ability(self, ability_id):
        """Cast an ability."""
        if self.combat:
            return self.combat.player_cast(self.player, ability_id)
        return self.ability_system.cast(ability_id, self.player)

    def attack(self, direction):
        """Melee attack."""
        if self.combat:
            return self.combat.player_attack(self.player, direction)
        return False, "Combat system not initialized"

    def update(self):
        """Single frame update."""
        now = time.time()
        self.dt = min(now - self.last_frame_time, 0.1)  # Cap dt
        self.last_frame_time = now

        # Update player
        self.player.update_debt()
        self.player.regenerate_lc(self.dt)

        # Update camera
        self.camera_x = int(self.player.x)
        self.camera_y = int(self.player.y)

        # Update enemies
        if self.combat:
            self.combat.update_enemies(self.dt, self.player)

        # Update economy
        self.economy.update_rates()

        # Check codex
        self.codex.check_triggers(location=self.star_systems.current_system)

        self.frame_count += 1

        # Check player death
        if self.player.hp <= 0:
            return "DEAD"

        return "OK"

    def render(self, output_path=None):
        """Render current frame."""
        if self.use_visual and self.renderer and self.tilemap:
            entities = [self.player] + self.bestiary.enemies
            return self.renderer.render_frame(
                self.tilemap, entities,
                viewport_width=25, viewport_height=19,
                camera_x=self.camera_x, camera_y=self.camera_y,
                output_path=output_path
            )
        elif self.tilemap:
            entities = [self.player] + self.bestiary.enemies
            return self.renderer.render_ascii(
                self.tilemap, entities,
                viewport_width=40, viewport_height=20,
                camera_x=self.camera_x, camera_y=self.camera_y
            )
        return None

    def get_status(self):
        """Get full player status."""
        return {
            "resonance": self.player.resonance_type,
            "attunement": self.player.attunement_level,
            "hp": self.player.hp,
            "lc": self.player.lattice_charge,
            "lc_max": self.player.lattice_charge_max,
            "debt": self.player.lattice_debt,
            "system": self.star_systems.current_system,
            "biome": self.scenes.get_scene(self.star_systems.current_system).biome_tags[0] if self.scenes.get_scene(self.star_systems.current_system) else "unknown",
            "year": CURRENT_YEAR,
            "position": (self.player.x, self.player.y),
            "enemies_nearby": len([e for e in self.bestiary.enemies 
                                   if math.sqrt((e.x-self.player.x)**2 + (e.y-self.player.y)**2) < 10]),
            "inventory_count": len(self.inventory.items),
            "cs": self.economy.get_balance("CS"),
            "lm": self.economy.get_balance("LM"),
        }

    def get_combat_log(self):
        if self.combat:
            return self.combat.get_combat_log()
        return []
