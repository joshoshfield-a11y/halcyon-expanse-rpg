"""
Halcyon Expanse — 2D Top-Down Game Loop v2
Integrated with sprite atlas, particle system, lighting engine, visual renderer.
"""
import time
import sys
import os
import math
import random

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
from halcyon.save_load import SaveManager
from halcyon.quest import QuestManager, Quest, QuestObjective
from halcyon.equipment import EquipmentManager, Equipment
from halcyon.leveling import LevelingSystem
from halcyon.boss import BossManager
from halcyon.crafting import CraftingSystem
from halcyon.world_events import WorldEventManager
from halcyon.dialogue import DialogueManager
from engine2d.sound import SoundManager



from engine2d.tilemap import TileMap, BIOME_TILESETS
from engine2d.sprite_atlas import ATLAS, AnimatedSprite
from engine2d.particles import ParticleSystem
from engine2d.lighting_engine import LightingEngine
from engine2d.visual_renderer import VisualRenderer
from engine2d.combat import CombatSystem

CURRENT_YEAR = 706


class Game2D:
    """Main 2D top-down RPG game class with full graphics."""

    def __init__(self, seed=None, player_resonance="Ember", use_visual=True, render_every_frame=False):
        self.seed = seed or 78
        self.player_resonance = player_resonance
        self.use_visual = use_visual
        self.render_every_frame = render_every_frame

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
        self.save_manager = SaveManager()
        self.quest_manager = QuestManager()
        self.equipment_manager = EquipmentManager()
        self.leveling = LevelingSystem()
        self.boss_manager = BossManager()
        self.crafting = CraftingSystem()
        self.world_events = WorldEventManager(self.tilemap.rng if self.tilemap else None)
        self.dialogue_manager = DialogueManager()
        self.sound_manager = SoundManager(enabled=False)  # Disabled by default, enable if pygame available

        self.play_time = 0.0
        self.last_save_time = time.time()


        # Graphics
        self.tilemap = None
        self.visual_renderer = VisualRenderer() if use_visual else None
        self.ascii_renderer = ASCIIRenderer()
        self.particles = ParticleSystem() if use_visual else None
        self.lighting = None

        # Player
        self.player = None
        self.player_sprite = None

        # Game state
        self.running = False
        self.frame_count = 0
        self.last_frame_time = time.time()
        self.dt = 0.016

        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.camera_target_x = 0
        self.camera_target_y = 0

        # Animation state
        self.player_action_state = "idle"
        self.player_action_timer = 0.0

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

        # Get player sprite
        self.player_sprite = ATLAS.get_sprite("player")

        # Starting items
        self.inventory.add_item(Item("starter_sword", "Rusty Blade", "Common", "weapon"))
        self.inventory.add_item(Item("healing_potion", "Glowroot Tincture", "Uncommon", "consumable"))
        self.inventory.add_item(Item("ember_shard", "Ember Shard", "Rare", "material"))

        # Load initial scene
        self._load_system("VeyraPrime")

        # Check codex
        self.codex.check_triggers(location="VeyraPrime")
        # Initialize default quests
        self._init_default_quests()

        # Initialize default equipment
        self._init_default_equipment()

    def _init_default_quests(self):
        """Set up starting quests."""
        tutorial_quest = Quest(
            quest_id="tutorial_first_steps",
            name="First Steps",
            description="Explore the starting area and defeat your first enemy.",
            giver="Chancellor Isbeth Rowe",
            faction="Concord Table",
            difficulty=1,
            objectives=[
                QuestObjective("Move 10 steps", "reach", "move", required=10),
                QuestObjective("Defeat an Ash Wraith", "kill", "Ash Wraith", required=1),
            ]
        )
        self.quest_manager.add_quest(tutorial_quest)

        exploration_quest = Quest(
            quest_id="explore_ashduin",
            name="Into the Ash",
            description="Travel to Ashduin and survive the ashfall.",
            giver="Warden Nell Achera",
            faction="Concord Table",
            difficulty=2,
            objectives=[
                QuestObjective("Warp to Ashduin", "reach", "Ashduin", required=1),
                QuestObjective("Defeat 3 enemies in Ashduin", "kill", "any", required=3),
            ]
        )
        self.quest_manager.add_quest(exploration_quest)

        hollow_quest = Quest(
            quest_id="enter_vashti_scar",
            name="The Scar",
            description="Enter the Vashti Scar and survive without Lattice.",
            giver="Foreman Dask Ilyrian",
            faction="Ferro Compact",
            difficulty=3,
            objectives=[
                QuestObjective("Enter Vashti Scar", "reach", "Vashti Scar", required=1),
                QuestObjective("Survive 30 seconds in the Scar", "reach", "survive_scar", required=30),
            ]
        )
        self.quest_manager.add_quest(hollow_quest)

    def _init_default_equipment(self):
        """Set up starting equipment templates."""
        starter_items = [
            Equipment("rusty_blade", "Rusty Blade", "weapon", "Common",
                     damage_bonus=5, description="A worn iron blade."),
            Equipment("tattered_cloak", "Tattered Cloak", "armor", "Common",
                     defense_bonus=3, description="Offers minimal protection."),
            Equipment("ember_amulet", "Ember Amulet", "accessory", "Uncommon",
                     resonance_req="Ember", lc_bonus=50, lc_regen_bonus=2,
                     description="Warm to the touch."),
            Equipment("concord_badge", "Concord Badge", "relic", "Rare",
                     hp_bonus=20, debt_reduction=5,
                     description="Marks you as a Concord agent."),
        ]
        for item in starter_items:
            # Add to inventory
            from halcyon.inventory import Item
            inv_item = Item(item.item_id, item.name, item.rarity, item.slot)
            self.inventory.add_item(inv_item)


    def _load_system(self, system_name):
        """Load a star system as a tilemap."""
        scene = self.scenes.get_scene(system_name)
        biome = scene.biome_tags[0] if scene.biome_tags else "temperate"

        self.tilemap = TileMap(width=64, height=64, biome=biome, 
                               seed=self.seed + hash(system_name) % 10000)
        self.tilemap.add_entity(self.player, self.player.x, self.player.y)

        # Spawn enemies
        enemy_count = {"VeyraPrime": 1, "Ashduin": 3, "HollowAnchor": 4, "GalesReach": 2,
                       "IronMeridian": 3, "ChorusDeep": 2, "SaltWastes": 2, "HushMarches": 3,
                       "TwoRivers": 1}.get(system_name, 2)

        enemy_types = ["Ash Wraith", "Ferro Drone", "Hollow Stalker", 
                      "Tide Leviathan", "Chorus Hymnal", "Salt Scarab"]
        for _ in range(enemy_count):
            etype = self.tilemap.rng.choice(enemy_types)
            ex = self.tilemap.rng.randint(10, 55)
            ey = self.tilemap.rng.randint(10, 55)
            if self.tilemap.is_walkable(ex, ey):
                self.bestiary.spawn(etype, x=ex, y=ey)

        # Chance to spawn boss in certain systems
        boss_chance = {"Ashduin": 0.3, "HollowAnchor": 0.4, "IronMeridian": 0.3, 
                       "ChorusDeep": 0.25, "HushMarches": 0.35}
        if system_name in boss_chance and self.tilemap.rng.random() < boss_chance[system_name]:
            available = self.boss_manager.get_available_bosses()
            if available:
                boss_id = self.tilemap.rng.choice(available)
                boss = self.boss_manager.spawn_boss(boss_id, x=32, y=32)
                if boss:
                    print(f"\n!!! BOSS ENCOUNTER: {boss.name} - {boss.title} !!!")
                    print(f"    {boss.intro_text}")

        self.combat = CombatSystem(self.ability_system, self.bestiary, self.tilemap)
        self.star_systems.current_system = system_name
        self.scenes.load_scene(system_name)

        # Initialize lighting
        if self.use_visual and self.visual_renderer:
            self.lighting = LightingEngine(self.tilemap.width, self.tilemap.height)
            self.lighting.set_ambient(0.15)
            # Biome-specific ambient
            if biome in ["horror", "subterranean", "deep", "haunted"]:
                self.lighting.set_ambient(0.05)
            elif biome in ["twilight", "fog"]:
                self.lighting.set_ambient(0.08)
            elif biome in ["volcanic", "forge", "ashfall"]:
                self.lighting.set_ambient(0.2)
            self.visual_renderer.lighting = self.lighting

        # Check hollowed zones
        zones = self.hollowed_zones.get_zones_in_system(system_name)
        for zone in zones:
            zone.on_enter(self.player)

    def move_player(self, dx, dy):
        """Move player with collision and effects."""
        if self.player_action_timer > 0:
            return None  # Can't move during action

        if self.tilemap.move_entity(self.player, dx, dy):
            self.player.update_debt()
            self.player.regenerate_lc(self.dt)

            # Update player sprite state
            if self.player_sprite:
                if dy < 0:
                    self.player_sprite.set_state("walk_up")
                    self.player_sprite.direction = "up"
                elif dy > 0:
                    self.player_sprite.set_state("walk_down")
                    self.player_sprite.direction = "down"
                elif dx < 0:
                    self.player_sprite.set_state("idle_left")
                    self.player_sprite.direction = "left"
                elif dx > 0:
                    self.player_sprite.set_state("idle_right")
                    self.player_sprite.direction = "right"

            # Trail particles
            if self.particles:
                self.particles.emit_trail(self.player.x, self.player.y, 
                                         color=(200, 200, 255), width=1)

            # Check for seam gate interaction
            tile = self.tilemap.get_tile(int(self.player.x), int(self.player.y))
            if tile == "seam_gate":
                # Gate glow effect
                if self.particles:
                    self.particles.emit(self.player.x, self.player.y, count=5,
                                       color=(200, 180, 100), speed=20, lifetime=0.5,
                                       size=2, gravity=-5)
                return "seam_gate"
        return None

    def interact(self):
        """Interact with current tile."""
        tile = self.tilemap.get_tile(int(self.player.x), int(self.player.y))
        if tile == "seam_gate":
            # Gate activation effect
            if self.particles:
                self.particles.emit(self.player.x, self.player.y, count=20,
                                   color=(255, 220, 100), speed=40, lifetime=1.0,
                                   size=3, gravity=-10)
            return self._show_warp_menu()
        return "Nothing to interact with"

    def _show_warp_menu(self):
        """Show available warp targets."""
        targets = self.star_systems.get_available_warp_targets()
        names = [t for t in targets]
        return f"SEAM GATE - Available destinations: {', '.join(names)}"

    def warp(self, target_name):
        """Warp to another system with visual effects."""
        success, msg = self.star_systems.warp(target_name)
        if success:
            # Warp effect
            if self.particles:
                self.particles.emit_explosion(self.player.x, self.player.y, 
                                             color=(200, 200, 255), intensity=2.0)

            # Exit current hollowed zones
            zones = self.hollowed_zones.get_zones_in_system(self.star_systems.current_system)
            for zone in zones:
                zone.on_exit(self.player)

            self._load_system(target_name)
            self.codex.check_triggers(location=target_name)

            # Arrival effect
            if self.particles:
                self.particles.emit(self.player.x, self.player.y, count=15,
                                   color=(255, 255, 200), speed=30, lifetime=0.8,
                                   size=2, gravity=-8)

            return f"WARPED to {target_name}"
        return msg

    def cast_ability(self, ability_id):
        """Cast an ability with visual effects."""
        if self.combat:
            success, msg = self.combat.player_cast(self.player, ability_id)
        else:
            success, msg = self.ability_system.cast(ability_id, self.player)

        if success and self.particles:
            ability = self.ability_system.abilities.get(ability_id)
            if ability:
                self.particles.emit_spell_cast(self.player.x, self.player.y, 
                                              ability.resonance_type)

                # Screen shake for powerful spells
                if ability.tier >= 2:
                    if self.visual_renderer:
                        self.visual_renderer.add_screen_shake(3.0)

        return success, msg

    def attack(self, direction):
        """Melee attack with visual effects."""
        if self.combat:
            success, msg = self.combat.player_attack(self.player, direction)

            if success and self.particles:
                dx, dy = direction
                target_x = self.player.x + dx
                target_y = self.player.y + dy
                self.particles.emit_explosion(target_x, target_y, 
                                              color=(255, 100, 50), intensity=0.5)

                # Damage number
                if self.visual_renderer:
                    self.visual_renderer.add_damage_number(target_x, target_y, "18", 
                                                          color=(255, 200, 50))

            # Player attack animation
            if self.player_sprite:
                self.player_sprite.set_state("attack")
                self.player_action_state = "attack"
                self.player_action_timer = 0.3

            return success, msg
        return False, "Combat system not initialized"

    def update(self):
        """Single frame update with full graphics."""
        now = time.time()
        self.dt = min(now - self.last_frame_time, 0.1)
        self.last_frame_time = now

        # Update player action timer
        if self.player_action_timer > 0:
            self.player_action_timer -= self.dt
            if self.player_action_timer <= 0:
                self.player_action_timer = 0
                if self.player_sprite:
                    self.player_sprite.set_state("idle_down")

        # Update player sprite
        if self.player_sprite:
            self.player_sprite.update(self.dt)

        # Update enemy sprites
        for enemy in self.bestiary.enemies:
            sprite = ATLAS.get_sprite(enemy.name)
            if sprite:
                sprite.set_state(enemy.state)
                sprite.update(self.dt)

        # Update player
        self.player.update_debt()
        self.player.regenerate_lc(self.dt)

        # Smooth camera
        target_x = self.player.x
        target_y = self.player.y
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1

        # Update enemies
        if self.combat:
            self.combat.update_enemies(self.dt, self.player)

        # Update particles
        if self.particles:
            self.particles.update(self.dt)

        # Update lighting
        if self.lighting:
            self.lighting.update(self.dt, self.player.x, self.player.y)

        # Update world events
        self.world_events.update(self.dt, self)
        
        # Check random encounters
        encounter = self.world_events.check_random_encounter(self)
        if encounter:
            self.combat_log.append(f"Random encounter: {encounter}")
        
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
        """Render current frame with full graphics."""
        if self.use_visual and self.visual_renderer and self.tilemap:
            entities = [self.player] + self.bestiary.enemies

            # Update renderer's particle system
            self.visual_renderer.particles = self.particles

            return self.visual_renderer.render_frame(
                self.tilemap, entities, self.player,
                camera_x=int(self.camera_x), camera_y=int(self.camera_y),
                viewport_width=30, viewport_height=22,
                output_path=output_path,
                show_ui=True, show_minimap=True
            )
        elif self.tilemap:
            entities = [self.player] + self.bestiary.enemies
            return self.ascii_renderer.render_entities(
                self.tilemap.to_dict(), entities
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
            "particles": self.particles.get_active_count() if self.particles else 0,
            "frame": self.frame_count,
        }

    def get_combat_log(self):
        if self.combat:
            return self.combat.get_combat_log()
        return []
