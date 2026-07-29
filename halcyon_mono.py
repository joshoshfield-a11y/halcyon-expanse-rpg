"""
HALCYON EXPANSE 2D RPG — MONOLITHIC VERSION
Single file. Run: python halcyon_mono.py
Contains: Xandria engine core + Halcyon spec + 2D engine + main loop
"""
import sys, os, time, math, random, json

# =============================================================================
# CORE ENGINE
# =============================================================================
class EventBus:
    def __init__(self):
        from collections import defaultdict, deque
        self._subs = defaultdict(list)
        self._queue = deque()
    def subscribe(self, event_type, callback):
        self._subs[event_type].append(callback)
    def emit(self, event_type, payload=None):
        self._queue.append((event_type, payload))
    def flush(self):
        while self._queue:
            event_type, payload = self._queue.popleft()
            for cb in self._subs.get(event_type, []):
                cb(payload)

class Subsystem:
    name = "base"
    def on_attach(self, engine): self.engine = engine
    def update(self, dt): pass
    def shutdown(self): pass

class Engine:
    def __init__(self, tick_rate=30):
        self.tick_rate = tick_rate
        self.dt = 1.0 / tick_rate
        self.subsystems = {}
        self.bus = EventBus()
        self.running = False
        self.frame = 0
    def register(self, subsystem):
        subsystem.on_attach(self)
        self.subsystems[subsystem.name] = subsystem
        return subsystem
    def step(self):
        self.frame += 1
        for sub in self.subsystems.values():
            sub.update(self.dt)
        self.bus.flush()
    def run(self, max_frames=None, realtime=False):
        self.running = True
        while self.running:
            self.step()
            if realtime:
                time.sleep(self.dt)
            if max_frames and self.frame >= max_frames:
                self.running = False
    def stop(self):
        self.running = False

class GameState:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 2**31)
        self.rng = random.Random(self.seed)
        self.entities = {}
        self.world = {}
        self.prompt_log = []
        self.next_entity_id = 1
    def add_entity(self, entity):
        eid = self.next_entity_id
        entity.id = eid
        self.entities[eid] = entity
        self.next_entity_id += 1
        return eid

class Entity:
    def __init__(self, kind="generic", x=0, y=0, hp=100, data=None):
        self.id = None
        self.kind = kind
        self.x, self.y = x, y
        self.hp = hp
        self.data = data or {}
    def to_dict(self):
        return {"kind": self.kind, "x": self.x, "y": self.y, "hp": self.hp, "data": self.data}

# =============================================================================
# HALCYON SYSTEMS
# =============================================================================
RESONANCE_TYPES = ["Ember", "Gale", "Hollow", "Tide", "Root", "Iron", "Chorus"]
COST_MULTIPLIERS = {0: 1.4, 1: 1.0, 2: 0.8, 3: 0.6}
CURRENT_YEAR = 706

class Actor(Entity):
    def __init__(self, kind="actor", x=0, y=0, hp=100, resonance_type="Ember", attunement_level=1,
                 lattice_charge=500.0, lattice_debt=0.0, data=None):
        super().__init__(kind=kind, x=x, y=y, hp=hp, data=data)
        self.resonance_type = resonance_type
        self.attunement_level = max(1, min(10, int(attunement_level)))
        self.lattice_charge = max(0.0, min(1000.0, float(lattice_charge)))
        self.lattice_debt = max(0.0, float(lattice_debt))
        self._hollowed_zone_active = False
        self._base_max_lc = 1000.0
    @property
    def lattice_charge_max(self):
        return 0.0 if self._hollowed_zone_active else self._base_max_lc
    def consume_lc(self, amount):
        if self._hollowed_zone_active:
            return False
        if self.lattice_charge >= amount:
            self.lattice_charge -= amount
            return True
        return False
    def regenerate_lc(self, dt):
        if self._hollowed_zone_active:
            return
        regen = 10.0 * dt
        self.lattice_charge = min(self.lattice_charge_max, self.lattice_charge + regen)
    def enter_hollowed_zone(self):
        self._hollowed_zone_active = True
        self.lattice_charge = 0.0
    def exit_hollowed_zone(self):
        self._hollowed_zone_active = False

class Ability:
    def __init__(self, ability_id, name, base_lc_cost, resonance_type, tier, description=""):
        self.ability_id = ability_id
        self.name = name
        self.base_lc_cost = float(base_lc_cost)
        self.resonance_type = resonance_type
        self.tier = int(tier)
        self.description = description

class AbilitySystem:
    def __init__(self):
        self.abilities = {}
    def register_ability(self, ability):
        self.abilities[ability.ability_id] = ability
    @staticmethod
    def resonance_distance(type_a, type_b):
        if type_a not in RESONANCE_TYPES or type_b not in RESONANCE_TYPES:
            return 3
        idx_a = RESONANCE_TYPES.index(type_a)
        idx_b = RESONANCE_TYPES.index(type_b)
        dist = abs(idx_a - idx_b)
        return min(dist, 7 - dist)
    def resolve_cost(self, ability_id, actor_resonance):
        ability = self.abilities.get(ability_id)
        if not ability:
            return None
        dist = self.resonance_distance(ability.resonance_type, actor_resonance)
        multiplier = COST_MULTIPLIERS.get(dist, 0.6)
        return ability.base_lc_cost * multiplier
    def cast(self, ability_id, actor):
        cost = self.resolve_cost(ability_id, actor.resonance_type)
        if cost is None:
            return False, f"Ability {ability_id} not found"
        if actor._hollowed_zone_active:
            return False, "Lattice Actions blocked in Hollowed Zone"
        if actor.consume_lc(cost):
            ability = self.abilities[ability_id]
            return True, f"Cast {ability.name} for {cost:.1f} LC"
        return False, f"Insufficient LC (need {cost:.1f}, have {actor.lattice_charge:.1f})"

class StarSystemManager:
    SYSTEM_ORDER = ["VeyraPrime", "Ashduin", "TwoRivers", "HollowAnchor", "GalesReach", "IronMeridian", "ChorusDeep", "SaltWastes", "HushMarches"]
    ADJACENCY = {
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
    def __init__(self):
        self.current_system = "VeyraPrime"
    def get_available_warp_targets(self, system_name=None):
        name = system_name or self.current_system
        return self.ADJACENCY.get(name, [])
    def warp(self, target_name):
        if target_name not in self.SYSTEM_ORDER:
            return False, f"System {target_name} does not exist"
        if target_name not in self.ADJACENCY.get(self.current_system, []):
            return False, f"No Seam connection from {self.current_system} to {target_name}"
        self.current_system = target_name
        return True, f"Warped to {target_name}"

class SceneManager:
    BIOMES = {
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
    def get_scene(self, system_name):
        return type("Scene", (), {"biome_tags": self.BIOMES.get(system_name, ["temperate"])})()

class HollowedZone:
    def __init__(self, name, system):
        self.name = name
        self.system = system
    def on_enter(self, actor):
        actor.enter_hollowed_zone()
    def on_exit(self, actor):
        actor.exit_hollowed_zone()

class HollowedZoneManager:
    ZONES = [
        {"name": "Vashti Scar", "system": "VeyraPrime"},
        {"name": "Grey Reef", "system": "ChorusDeep"},
        {"name": "Bare Meridian", "system": "IronMeridian"},
    ]
    def __init__(self):
        self.zones = {z["name"]: HollowedZone(**z) for z in self.ZONES}
    def get_zones_in_system(self, system_name):
        return [z for z in self.zones.values() if z.system == system_name]

class FactionManager:
    def __init__(self):
        pass

class Economy:
    def __init__(self):
        self.wallets = {"CS": 100.0, "LM": 50.0}
        self.rate_CS_to_LM = 0.85
    def get_balance(self, currency):
        return self.wallets.get(currency, 0.0)
    def exchange(self, from_c, to_c, amount):
        if self.wallets.get(from_c, 0) < amount:
            return None
        if from_c == "CS" and to_c == "LM":
            received = amount * self.rate_CS_to_LM
        elif from_c == "LM" and to_c == "CS":
            received = amount / self.rate_CS_to_LM
        else:
            return None
        self.wallets[from_c] -= amount
        self.wallets[to_c] = self.wallets.get(to_c, 0) + received
        return received

class Item:
    RARITY_COLORS = {"Common": "#FFFFFF", "Uncommon": "#00FF00", "Rare": "#0000FF", "Legendary": "#FFD700"}
    def __init__(self, item_id, name, rarity="Common", item_type="misc"):
        self.item_id = item_id
        self.name = name
        self.rarity = rarity
        self.item_type = item_type
    def get_border_color(self):
        return self.RARITY_COLORS.get(self.rarity, "#FFFFFF")

class Inventory:
    def __init__(self, capacity=50):
        self.items = []
        self.capacity = capacity
    def add_item(self, item):
        if len(self.items) < self.capacity:
            self.items.append(item)
            return True
        return False

class Enemy:
    def __init__(self, name, behavior_pattern, threat_tier, hp=100, x=0, y=0):
        self.kind = "enemy"
        self.name = name
        self.behavior_pattern = behavior_pattern
        self.threat_tier = threat_tier
        self.hp = hp
        self.max_hp = hp
        self.x = x
        self.y = y
        self.state = "idle"
    def take_damage(self, amount):
        self.hp -= amount
        return self.hp <= 0
    def update(self, dt, player, all_enemies):
        self.state_timer = getattr(self, 'state_timer', 0) + dt
        if self.behavior_pattern == "phase_cycle_4s_LC_drain":
            cycle = self.state_timer % 4.0
            self.state = "visible" if cycle < 2.0 else "phased"
            if self.state == "visible" and hasattr(player, 'lattice_charge'):
                player.lattice_charge = max(0, player.lattice_charge - 5 * dt)
        elif self.behavior_pattern == "patrol_loop_shield_burst":
            self.state = "shield_burst" if self.state_timer % 5.0 < 1.0 else "patrol"
        elif self.behavior_pattern == "stealth_ambush_LC_leech":
            dist = abs(self.x - player.x) + abs(self.y - player.y)
            if dist <= 2 and self.state == "idle":
                self.state = "ambush"
            elif self.state == "ambush":
                self.state = "leech"
        elif self.behavior_pattern == "area_pulse_knockback":
            self.state = "pulse" if self.state_timer % 6.0 < 1.5 else "charge"
        elif self.behavior_pattern == "buff_ally_resonance_amplify":
            self.state = "buffing"
        elif self.behavior_pattern == "swarm_split_on_damage":
            self.state = "swarm"

class Bestiary:
    TEMPLATES = [
        {"name": "Ash Wraith", "behavior_pattern": "phase_cycle_4s_LC_drain", "threat_tier": 3, "hp": 80},
        {"name": "Ferro Drone", "behavior_pattern": "patrol_loop_shield_burst", "threat_tier": 2, "hp": 60},
        {"name": "Hollow Stalker", "behavior_pattern": "stealth_ambush_LC_leech", "threat_tier": 4, "hp": 120},
        {"name": "Tide Leviathan", "behavior_pattern": "area_pulse_knockback", "threat_tier": 5, "hp": 200},
        {"name": "Chorus Hymnal", "behavior_pattern": "buff_ally_resonance_amplify", "threat_tier": 3, "hp": 90},
        {"name": "Salt Scarab", "behavior_pattern": "swarm_split_on_damage", "threat_tier": 2, "hp": 40},
    ]
    def __init__(self):
        self.enemies = []
    def spawn(self, name, x=0, y=0):
        template = next((t for t in self.TEMPLATES if t["name"] == name), None)
        if not template:
            return None
        enemy = Enemy(**template, x=x, y=y)
        self.enemies.append(enemy)
        return enemy
    def update_all(self, dt, player):
        for enemy in self.enemies:
            enemy.update(dt, player, self.enemies)
    def remove_dead(self):
        self.enemies = [e for e in self.enemies if e.hp > 0]

class CodexEntry:
    def __init__(self, year, name, description, unlock_trigger=None):
        self.year = year
        self.name = name
        self.description = description
        self.unlocked = False
        self.unlock_trigger = unlock_trigger or {}
    def unlock(self):
        self.unlocked = True
        return f"Codex unlocked: Year {self.year} - {self.name}"
    def check_trigger(self, location=None):
        if self.unlocked:
            return False
        if self.unlock_trigger.get("location") == location:
            return True
        return not self.unlock_trigger

class Codex:
    ENTRIES = [
        {"year": 0, "name": "The Shattering", "description": "Lattice first discovered.", "unlock_trigger": {"location": "VeyraPrime"}},
        {"year": 187, "name": "First Concord", "description": "Factions form.", "unlock_trigger": {}},
        {"year": 412, "name": "The Hollowing", "description": "HollowAnchor founded.", "unlock_trigger": {"location": "HollowAnchor"}},
        {"year": 518, "name": "Vashti Scar Sealed", "description": "Concord Wall built.", "unlock_trigger": {"location": "VeyraPrime"}},
        {"year": 688, "name": "Hollow Choir Withdrawal", "description": "Choir withdraws from public.", "unlock_trigger": {}},
        {"year": 706, "name": "Current Era", "description": "Present day.", "unlock_trigger": {}},
    ]
    def __init__(self):
        self.entries = {e["year"]: CodexEntry(**e) for e in self.ENTRIES}
        self.entries[706].unlock()
    def check_triggers(self, location=None):
        newly = []
        for entry in self.entries.values():
            if entry.check_trigger(location):
                entry.unlock()
                newly.append(entry)
        return newly
    def get_unlocked(self):
        return [e for e in self.entries.values() if e.unlocked]

# =============================================================================
# 2D TILEMAP ENGINE
# =============================================================================
TILE_TYPES = {
    "floor": {"char": ".", "color": (40, 40, 40), "walkable": True},
    "wall": {"char": "#", "color": (80, 80, 80), "walkable": False},
    "water": {"char": "~", "color": (30, 60, 90), "walkable": False},
    "lava": {"char": "^", "color": (180, 60, 20), "walkable": False},
    "grass": {"char": ",", "color": (34, 85, 51), "walkable": True},
    "sand": {"char": ":", "color": (194, 178, 128), "walkable": True},
    "ash": {"char": "`", "color": (60, 55, 50), "walkable": True},
    "iron_floor": {"char": "=", "color": (70, 75, 80), "walkable": True},
    "crystal": {"char": "+", "color": (120, 80, 160), "walkable": True},
    "seam_gate": {"char": "O", "color": (200, 180, 100), "walkable": True},
}

BIOME_TILESETS = {
    "temperate": {"floor": "grass", "wall": "wall", "water": "water", "special": "crystal"},
    "capital": {"floor": "iron_floor", "wall": "wall", "water": "water", "special": "seam_gate"},
    "ashfall": {"floor": "ash", "wall": "wall", "water": "lava", "special": "crystal"},
    "volcanic": {"floor": "ash", "wall": "wall", "water": "lava", "special": "lava"},
    "low_light": {"floor": "floor", "wall": "wall", "water": "water", "special": "crystal"},
    "horror": {"floor": "floor", "wall": "wall", "water": "water", "special": "crystal"},
    "subterranean": {"floor": "floor", "wall": "wall", "water": "water", "special": "crystal"},
    "zero_g": {"floor": "void", "wall": "void", "water": "void", "special": "crystal"},
    "industrial": {"floor": "iron_floor", "wall": "wall", "water": "water", "special": "seam_gate"},
    "forge": {"floor": "iron_floor", "wall": "wall", "water": "lava", "special": "lava"},
    "acoustic": {"floor": "crystal", "wall": "wall", "water": "water", "special": "crystal"},
    "crystalline": {"floor": "crystal", "wall": "crystal", "water": "crystal", "special": "crystal"},
    "deep": {"floor": "floor", "wall": "wall", "water": "water", "special": "crystal"},
    "desert": {"floor": "sand", "wall": "wall", "water": "water", "special": "crystal"},
    "twilight": {"floor": "floor", "wall": "wall", "water": "water", "special": "crystal"},
    "fog": {"floor": "ash", "wall": "wall", "water": "water", "special": "crystal"},
    "haunted": {"floor": "floor", "wall": "wall", "water": "water", "special": "crystal"},
}

class TileMap:
    def __init__(self, width=64, height=64, biome="temperate", seed=None):
        self.width = width
        self.height = height
        self.biome = biome
        self.rng = random.Random(seed or 78)
        self.tiles = [["floor" for _ in range(width)] for _ in range(height)]
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
                else:
                    self.tiles[y][x] = tileset.get("floor", "floor")
        for y in range(2, 8):
            for x in range(2, 8):
                self.tiles[y][x] = tileset.get("floor", "floor")
        edge_x = self.width - 3
        edge_y = self.height // 2
        for dy in [-1, 0, 1]:
            self.tiles[edge_y+dy][edge_x] = "seam_gate"
    def is_walkable(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return TILE_TYPES.get(self.tiles[y][x], {}).get("walkable", True)
        return False
    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return "void"
    def move_entity(self, entity, dx, dy):
        new_x = int(entity.x + dx)
        new_y = int(entity.y + dy)
        if self.is_walkable(new_x, new_y):
            entity.x = new_x
            entity.y = new_y
            return True
        return False

class CombatSystem:
    def __init__(self, ability_system, bestiary, tilemap):
        self.ability_system = ability_system
        self.bestiary = bestiary
        self.tilemap = tilemap
        self.combat_log = []
        self.last_attack_time = 0
    def player_attack(self, player, direction):
        now = time.time()
        if now - self.last_attack_time < 0.5:
            return False, "Attack on cooldown"
        self.last_attack_time = now
        dx, dy = direction
        target_x = int(player.x + dx)
        target_y = int(player.y + dy)
        for enemy in self.bestiary.enemies:
            if int(enemy.x) == target_x and int(enemy.y) == target_y:
                damage = 15 + player.attunement_level * 3
                dead = enemy.take_damage(damage)
                msg = f"Hit {enemy.name} for {damage} damage! ({enemy.hp}/{enemy.max_hp} HP)"
                self.combat_log.append(msg)
                if dead:
                    self.combat_log.append(f"{enemy.name} destroyed!")
                    self.bestiary.remove_dead()
                return True, msg
        return False, "No target in range"
    def player_cast(self, player, ability_id):
        success, msg = self.ability_system.cast(ability_id, player)
        self.combat_log.append(msg)
        if success:
            ability = self.ability_system.abilities.get(ability_id)
            if ability and "heal" in ability.name.lower():
                player.hp = min(100, player.hp + 20 + player.attunement_level * 5)
                self.combat_log.append(f"Healed for {20 + player.attunement_level * 5} HP")
            elif ability and "shield" in ability.name.lower():
                player.data["shield_active"] = True
                player.data["shield_duration"] = 3.0
                self.combat_log.append("Shield activated!")
        return success, msg
    def update_enemies(self, dt, player):
        self.bestiary.update_all(dt, player)
        for enemy in self.bestiary.enemies:
            dist = math.sqrt((enemy.x - player.x)**2 + (enemy.y - player.y)**2)
            if dist < 8 and dist > 1.5:
                dx = (player.x - enemy.x) / dist if dist > 0 else 0
                dy = (player.y - enemy.y) / dist if dist > 0 else 0
                new_x = enemy.x + dx * 1.5 * dt
                new_y = enemy.y + dy * 1.5 * dt
                if self.tilemap.is_walkable(int(new_x), int(new_y)):
                    enemy.x = new_x
                    enemy.y = new_y
            if dist <= 1.5:
                damage = enemy.threat_tier * 3
                if player.data.get("shield_active"):
                    damage = max(0, damage - 10)
                    self.combat_log.append(f"Shield blocked {enemy.name} attack!")
                player.hp -= damage
                self.combat_log.append(f"{enemy.name} hit you for {damage} damage!")
            if player.data.get("shield_active"):
                player.data["shield_duration"] -= dt
                if player.data["shield_duration"] <= 0:
                    player.data["shield_active"] = False
                    self.combat_log.append("Shield expired")
    def get_combat_log(self, max_lines=5):
        return self.combat_log[-max_lines:]

# =============================================================================
# MAIN GAME CLASS
# =============================================================================
class Game2D:
    def __init__(self, seed=None, player_resonance="Ember", use_visual=True):
        self.seed = seed or 78
        self.player_resonance = player_resonance
        self.use_visual = use_visual
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
        self.tilemap = None
        self.player = None
        self.frame_count = 0
        self.last_frame_time = time.time()
        self.dt = 0.016
        self.camera_x = 0
        self.camera_y = 0
        self._init_game()

    def _init_game(self):
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
        self.player = Actor(
            kind="player", x=5, y=5, hp=100,
            resonance_type=self.player_resonance,
            attunement_level=1, lattice_charge=500.0, lattice_debt=0.0
        )
        self.player.data["shield_active"] = False
        self.player.data["shield_duration"] = 0.0
        self.inventory.add_item(Item("starter_sword", "Rusty Blade", "Common", "weapon"))
        self.inventory.add_item(Item("healing_potion", "Glowroot Tincture", "Uncommon", "consumable"))
        self.inventory.add_item(Item("ember_shard", "Ember Shard", "Rare", "material"))
        self._load_system("VeyraPrime")
        self.codex.check_triggers(location="VeyraPrime")

    def _load_system(self, system_name):
        scene = self.scenes.get_scene(system_name)
        biome = scene.biome_tags[0] if scene.biome_tags else "temperate"
        self.tilemap = TileMap(width=64, height=64, biome=biome, seed=self.seed + hash(system_name) % 10000)
        self.player.x = 5
        self.player.y = 5
        enemy_count = {"VeyraPrime": 1, "Ashduin": 3, "HollowAnchor": 4, "GalesReach": 2,
                       "IronMeridian": 3, "ChorusDeep": 2, "SaltWastes": 2, "HushMarches": 3,
                       "TwoRivers": 1}.get(system_name, 2)
        enemy_types = ["Ash Wraith", "Ferro Drone", "Hollow Stalker", "Tide Leviathan", "Chorus Hymnal", "Salt Scarab"]
        for _ in range(enemy_count):
            etype = self.tilemap.rng.choice(enemy_types)
            ex = self.tilemap.rng.randint(10, 55)
            ey = self.tilemap.rng.randint(10, 55)
            if self.tilemap.is_walkable(ex, ey):
                self.bestiary.spawn(etype, x=ex, y=ey)
        self.combat = CombatSystem(self.ability_system, self.bestiary, self.tilemap)
        self.star_systems.current_system = system_name
        zones = self.hollowed_zones.get_zones_in_system(system_name)
        for zone in zones:
            zone.on_enter(self.player)

    def move_player(self, dx, dy):
        if self.tilemap.move_entity(self.player, dx, dy):
            self.player.regenerate_lc(self.dt)
            tile = self.tilemap.get_tile(int(self.player.x), int(self.player.y))
            if tile == "seam_gate":
                return "seam_gate"
        return None

    def interact(self):
        tile = self.tilemap.get_tile(int(self.player.x), int(self.player.y))
        if tile == "seam_gate":
            targets = self.star_systems.get_available_warp_targets()
            return f"SEAM GATE - Available: {', '.join(targets)}"
        return "Nothing to interact with"

    def warp(self, target_name):
        success, msg = self.star_systems.warp(target_name)
        if success:
            zones = self.hollowed_zones.get_zones_in_system(self.star_systems.current_system)
            for zone in zones:
                zone.on_exit(self.player)
            self._load_system(target_name)
            self.codex.check_triggers(location=target_name)
            return f"WARPED to {target_name}"
        return msg

    def cast_ability(self, ability_id):
        if self.combat:
            return self.combat.player_cast(self.player, ability_id)
        return self.ability_system.cast(ability_id, self.player)

    def attack(self, direction):
        if self.combat:
            return self.combat.player_attack(self.player, direction)
        return False, "Combat not initialized"

    def update(self):
        now = time.time()
        self.dt = min(now - self.last_frame_time, 0.1)
        self.last_frame_time = now
        self.player.regenerate_lc(self.dt)
        self.camera_x = int(self.player.x)
        self.camera_y = int(self.player.y)
        if self.combat:
            self.combat.update_enemies(self.dt, self.player)
        self.codex.check_triggers(location=self.star_systems.current_system)
        self.frame_count += 1
        if self.player.hp <= 0:
            return "DEAD"
        return "OK"

    def render(self, output_path=None):
        start_x = max(0, self.camera_x - 20)
        start_y = max(0, self.camera_y - 10)
        end_x = min(self.tilemap.width, start_x + 40)
        end_y = min(self.tilemap.height, start_y + 20)
        lines = []
        for ty in range(start_y, end_y):
            row = []
            for tx in range(start_x, end_x):
                entity_here = None
                for e in [self.player] + self.bestiary.enemies:
                    if int(e.x) == tx and int(e.y) == ty:
                        entity_here = e
                        break
                if entity_here:
                    if entity_here.kind == 'player':
                        row.append('@')
                    else:
                        row.append('E')
                else:
                    tile_name = self.tilemap.tiles[ty][tx]
                    tile_info = TILE_TYPES.get(tile_name, TILE_TYPES["floor"])
                    row.append(tile_info["char"])
            lines.append(''.join(row))
        return '\n'.join(lines)

    def get_status(self):
        return {
            "resonance": self.player.resonance_type,
            "attunement": self.player.attunement_level,
            "hp": self.player.hp,
            "lc": self.player.lattice_charge,
            "lc_max": self.player.lattice_charge_max,
            "debt": self.player.lattice_debt,
            "system": self.star_systems.current_system,
            "biome": self.scenes.get_scene(self.star_systems.current_system).biome_tags[0],
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

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def print_banner():
    print("+" + "="*62 + "+")
    print("|" + " "*62 + "|")
    print("|" + "           H A L C Y O N   E X P A N S E".center(62) + "|")
    print("|" + "              2D Top-Down RPG v0.2.0".center(62) + "|")
    print("|" + " "*62 + "|")
    print("|" + "  Year 706 | 9 Star Systems | 7 Resonances | 6 Enemy Types".center(62) + "|")
    print("|" + " "*62 + "|")
    print("+" + "="*62 + "+")

def print_help():
    print("""
CONTROLS:
  w/a/s/d or arrows - Move
  space             - Attack (direction of last move)
  e                 - Interact (seam gates, items, NPCs)
  1-7               - Cast Lattice Ability
  i                 - Inventory
  c                 - Codex (lore entries)
  t                 - Status / Stats
  warp <system>     - Warp via Seam (when at gate)
  spawn <enemy>     - Spawn enemy (debug)
  exchange <amt> <from> <to> - Currency exchange
  q                 - Quit

ABILITIES:
  1: ember_strike  | 2: gale_dash  | 3: tide_heal
  4: hollow_drain  | 5: iron_shield | 6: root_bind
  7: chorus_blast
""")

def main():
    print_banner()
    print("Choose your Resonance:")
    resonances = ["Ember", "Gale", "Hollow", "Tide", "Root", "Iron", "Chorus"]
    for i, r in enumerate(resonances, 1):
        print(f"  {i}. {r}")
    choice = input("\nEnter number (1-7) or name: ").strip()
    try:
        idx = int(choice) - 1
        player_res = resonances[idx] if 0 <= idx < 7 else "Ember"
    except:
        player_res = choice if choice in resonances else "Ember"
    print(f"\nResonance: {player_res}")
    print("Initializing world...")
    game = Game2D(seed=78, player_resonance=player_res, use_visual=False)
    print("\n" + "="*60)
    print("WORLD LOADED")
    print("="*60)
    status = game.get_status()
    print(f"System: {status['system']} | Biome: {status['biome']}")
    print(f"Position: {status['position']}")
    print(f"HP: {status['hp']} | LC: {status['lc']:.0f}/{status['lc_max']:.0f}")
    print(f"Debt: {status['debt']:.2f} | Attunement: {status['attunement']}")
    print(f"Inventory: {status['inventory_count']} items")
    print(f"CS: {status['cs']:.2f} | LM: {status['lm']:.2f}")
    print(f"Enemies nearby: {status['enemies_nearby']}")
    print("="*60)
    print_help()
    last_dir = (0, -1)
    while True:
        try:
            cmd = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if not cmd:
            continue
        parts = cmd.split()
        action = parts[0]
        if action in ['w', 'up', 'north']:
            last_dir = (0, -1)
            result = game.move_player(0, -1)
            if result == "seam_gate":
                print("You stand before a SEAM GATE. Press E to interact.")
        elif action in ['s', 'down', 'south']:
            last_dir = (0, 1)
            result = game.move_player(0, 1)
            if result == "seam_gate":
                print("You stand before a SEAM GATE. Press E to interact.")
        elif action in ['a', 'left', 'west']:
            last_dir = (-1, 0)
            result = game.move_player(-1, 0)
            if result == "seam_gate":
                print("You stand before a SEAM GATE. Press E to interact.")
        elif action in ['d', 'right', 'east']:
            last_dir = (1, 0)
            result = game.move_player(1, 0)
            if result == "seam_gate":
                print("You stand before a SEAM GATE. Press E to interact.")
        elif action in ['space', 'attack', 'atk']:
            success, msg = game.attack(last_dir)
            print(msg)
        elif action in ['1', '2', '3', '4', '5', '6', '7']:
            abilities = ['ember_strike', 'gale_dash', 'tide_heal', 'hollow_drain', 
                        'iron_shield', 'root_bind', 'chorus_blast']
            ability_id = abilities[int(action) - 1]
            success, msg = game.cast_ability(ability_id)
            print(msg)
        elif action in ['e', 'interact']:
            result = game.interact()
            print(result)
        elif action == 'warp' and len(parts) > 1:
            target = parts[1].capitalize()
            target_map = {
                'Veyraprime': 'VeyraPrime', 'Ashduin': 'Ashduin', 'Tworivers': 'TwoRivers',
                'Hollowanchor': 'HollowAnchor', 'Galesreach': 'GalesReach',
                'Ironmeridian': 'IronMeridian', 'Chorusdeep': 'ChorusDeep',
                'Saltwastes': 'SaltWastes', 'Hushmarches': 'HushMarches'
            }
            target = target_map.get(target, target)
            msg = game.warp(target)
            print(msg)
        elif action in ['i', 'inventory', 'inv']:
            print(f"\nINVENTORY ({len(game.inventory.items)}/{game.inventory.capacity}):")
            for item in game.inventory.items:
                print(f"  [{item.rarity}] {item.name} ({item.item_type}) - {item.get_border_color()}")
            print(f"\nCS: {game.economy.get_balance('CS'):.2f} | LM: {game.economy.get_balance('LM'):.2f}")
        elif action in ['c', 'codex', 'lore']:
            unlocked = game.codex.get_unlocked()
            print(f"\nCODEX ({len(unlocked)}/{len(game.codex.entries)} entries unlocked):")
            for entry in unlocked:
                print(f"  Year {entry.year}: {entry.name}")
                print(f"    {entry.description}")
        elif action in ['t', 'status', 'stats']:
            s = game.get_status()
            print(f"\n{'='*50}")
            print(f"  RESONANCE: {s['resonance']} | ATTUNEMENT: {s['attunement']}/10")
            print(f"  HP: {s['hp']} | LC: {s['lc']:.0f}/{s['lc_max']:.0f}")
            print(f"  DEBT: {s['debt']:.2f} (3%/hr)")
            print(f"  SYSTEM: {s['system']} | BIOME: {s['biome']}")
            print(f"  POSITION: ({s['position'][0]:.1f}, {s['position'][1]:.1f})")
            print(f"  YEAR: {s['year']}")
            print(f"  ENEMIES NEARBY: {s['enemies_nearby']}")
            print(f"  INVENTORY: {s['inventory_count']} items")
            print(f"  CS: {s['cs']:.2f} | LM: {s['lm']:.2f}")
            print(f"{'='*50}")
        elif action == 'exchange' and len(parts) >= 4:
            try:
                amt = float(parts[1])
                from_c = parts[2].upper()
                to_c = parts[3].upper()
                result = game.economy.exchange(from_c, to_c, amt)
                if result:
                    print(f"Exchanged {amt} {from_c} -> {result:.2f} {to_c}")
                else:
                    print("Exchange failed")
            except:
                print("Usage: exchange <amount> <from> <to>")
        elif action == 'spawn' and len(parts) > 1:
            enemy_name = ' '.join(parts[1:]).title()
            enemy = game.bestiary.spawn(enemy_name)
            if enemy:
                enemy.x = game.player.x + 2
                enemy.y = game.player.y + 2
                print(f"Spawned {enemy.name} at ({enemy.x:.0f}, {enemy.y:.0f})")
            else:
                print(f"Unknown enemy: {enemy_name}")
        elif action in ['r', 'render', 'frame']:
            print(game.render())
        elif action in ['log', 'combat']:
            log = game.get_combat_log()
            if log:
                print("\nCOMBAT LOG:")
                for line in log:
                    print(f"  {line}")
            else:
                print("No combat log entries")
        elif action in ['h', 'help', '?']:
            print_help()
        elif action in ['q', 'quit', 'exit']:
            print("\nSaving state...")
            print("Goodbye, traveler.")
            break
        game.update()
        if game.player.hp <= 0:
            print("\n" + "="*60)
            print("  YOU HAVE DIED")
            print("  Your lattice fades into the void...")
            print("="*60)
            break
        nearby = [e for e in game.bestiary.enemies 
                  if math.sqrt((e.x-game.player.x)**2 + (e.y-game.player.y)**2) < 5]
        if nearby:
            print(f"\nWARNING: {len(nearby)} ENEMIES NEARBY")
            for e in nearby:
                dist = math.sqrt((e.x-game.player.x)**2 + (e.y-game.player.y)**2)
                print(f"  {e.name} (T{e.threat_tier}) [{e.hp}/{e.max_hp} HP] - {dist:.1f}m away, state: {e.state}")

if __name__ == "__main__":
    main()
