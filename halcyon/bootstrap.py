"""
Halcyon Expanse — Bootstrap & Main Game Loop
Build Step 12: Current year = 706 (static constant).
Integrates all subsystems into the Xandria Engine.
"""
import sys
import os
import time
import json

# Add parent to path for Xandria imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import Engine, Subsystem
from core.state import GameState
from generation.procgen import WorldGenerator, NPCGenerator, QuestGenerator
from simulation.simcore import PhysicsSim, EconomySim, FactionSim
from rendering.renderer import ASCIIRenderer, VisualRenderer
from interface.prompt_parser import PromptParser, CommandRouter, ParsedCommand

from halcyon.actor import Actor, RESONANCE_TYPES
from halcyon.ability_system import AbilitySystem, Ability
from halcyon.star_system_manager import StarSystemManager
from halcyon.scene_manager import SceneManager
from halcyon.hollowed_zone import HollowedZoneManager
from halcyon.faction import FactionManager
from halcyon.economy import Economy
from halcyon.inventory import Inventory, Item, RARITY_TIERS
from halcyon.bestiary import Bestiary
from halcyon.codex import Codex

# Static world constant
CURRENT_YEAR = 706


class HalcyonGameState(GameState):
    """Extended GameState with Halcyon-specific data."""
    def __init__(self, seed=None):
        super().__init__(seed=seed)
        self.current_year = CURRENT_YEAR
        self.player_resonance = None
        self.player_attunement = 1
        self.codex = Codex()
        self.inventory = Inventory()
        self.economy = Economy(rng=self.rng)
        self.factions = FactionManager(rng=self.rng)
        self.bestiary = Bestiary()
        self.ability_system = AbilitySystem()
        self.star_systems = StarSystemManager()
        self.scenes = SceneManager()
        self.hollowed_zones = HollowedZoneManager()
        self.quest_flags = set()

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "current_year": self.current_year,
            "player_resonance": self.player_resonance,
            "player_attunement": self.player_attunement,
            "codex": self.codex.to_dict(),
            "inventory": self.inventory.to_dict(),
            "economy": self.economy.to_dict(),
            "factions": self.factions.to_dict(),
            "bestiary": self.bestiary.to_dict(),
            "star_systems": self.star_systems.to_dict(),
            "scenes": self.scenes.to_dict(),
            "hollowed_zones": self.hollowed_zones.to_dict(),
            "quest_flags": list(self.quest_flags),
        })
        return d


class HalcyonSubsystem(Subsystem):
    """Master subsystem coordinating all Halcyon systems per tick."""
    name = "halcyon_master"

    def __init__(self, state: HalcyonGameState):
        self.state = state
        self.last_economy_update = time.time()

    def update(self, dt):
        # Update all actors (debt accrual, LC regen)
        for entity in self.state.entities.values():
            if isinstance(entity, Actor):
                entity.update_debt()
                entity.regenerate_lc(dt)

        # Update economy rates
        self.state.economy.update_rates()

        # Update bestiary AI
        player = self.state.entities.get(1)
        self.state.bestiary.update_all(dt, player)
        self.state.bestiary.remove_dead()

        # Check codex unlocks
        current_scene = self.state.star_systems.current_system
        newly_unlocked = self.state.codex.check_triggers(
            location=current_scene,
            quest_flags=self.state.quest_flags
        )
        for entry in newly_unlocked:
            print(f"[CODEX] {entry.unlock()}")

        # Check hollowed zones
        if player and isinstance(player, Actor):
            zones = self.state.hollowed_zones.get_zones_in_system(current_scene)
            for zone in zones:
                # In real engine, check spatial overlap; here we check if "in zone"
                pass


class HalcyonCommandRouter(CommandRouter):
    """Extended command router with Halcyon-specific commands."""

    def __init__(self, engine, state: HalcyonGameState):
        super().__init__(engine, state)
        self.handlers.update({
            "warp": self._warp,
            "cast": self._cast,
            "inventory": self._inventory,
            "codex": self._codex,
            "status": self._status,
            "exchange": self._exchange,
            "spawn": self._spawn_enemy,
            "year": self._year,
        })

        # Add patterns to parser
        from interface.prompt_parser import INTENT_PATTERNS
        INTENT_PATTERNS.extend([
            (r"^(warp|jump|travel)\s+to\s+(?P<target>\w+)", "warp"),
            (r"^(cast|use)\s+(?P<ability>\w+)", "cast"),
            (r"^(inventory|inv|items|bag)", "inventory"),
            (r"^(codex|lore|history)", "codex"),
            (r"^(status|stats|self)", "status"),
            (r"^(exchange|trade)\s+(?P<amount>\d+)\s+(?P<from>\w+)\s+to\s+(?P<to>\w+)", "exchange"),
            (r"^(spawn|summon)\s+(?P<enemy>\w+)", "spawn"),
            (r"^(year|date|time)", "year"),
        ])

    def _warp(self, args):
        target = args.get("target", "")
        success, msg = self.state.star_systems.warp(target)
        if success:
            self.state.scenes.load_scene(target)
        return msg

    def _cast(self, args):
        ability_id = args.get("ability", "")
        player = self.state.entities.get(1)
        if not player or not isinstance(player, Actor):
            return "No player actor found"
        success, msg = self.state.ability_system.cast(ability_id, player)
        return msg

    def _inventory(self, args):
        inv = self.state.inventory.to_dict()
        lines = [f"Inventory ({inv['count']}/{inv['capacity']}):"]
        for item in inv["items"]:
            lines.append(f"  [{item['rarity']}] {item['name']} ({item['border_color']})")
        return "\n".join(lines)

    def _codex(self, args):
        unlocked = self.state.codex.get_unlocked()
        lines = [f"Codex Entries ({len(unlocked)} unlocked):"]
        for entry in unlocked:
            lines.append(f"  Year {entry.year}: {entry.name}")
        return "\n".join(lines)

    def _status(self, args):
        player = self.state.entities.get(1)
        if not player or not isinstance(player, Actor):
            return "No player found"
        return (f"Resonance: {player.resonance_type} | "
                f"Attunement: {player.attunement_level} | "
                f"LC: {player.lattice_charge:.1f}/{player.lattice_charge_max:.1f} | "
                f"Debt: {player.lattice_debt:.2f} | "
                f"System: {self.state.star_systems.current_system} | "
                f"Year: {self.state.current_year}")

    def _exchange(self, args):
        amount = float(args.get("amount", 0))
        from_curr = args.get("from", "").upper()
        to_curr = args.get("to", "").upper()
        received = self.state.economy.exchange(from_curr, to_curr, amount)
        if received is None:
            return "Exchange failed (insufficient funds or invalid currency)"
        return f"Exchanged {amount} {from_curr} -> {received:.2f} {to_curr}"

    def _spawn_enemy(self, args):
        enemy_name = args.get("enemy", "")
        enemy = self.state.bestiary.spawn(enemy_name)
        if enemy:
            return f"Spawned {enemy.name} (Tier {enemy.threat_tier}) at ({enemy.x},{enemy.y})"
        return f"Unknown enemy type: {enemy_name}"

    def _year(self, args):
        return f"Current Year: {self.state.current_year} (locked)"


def bootstrap_halcyon(seed=None, player_resonance="Ember"):
    """Bootstrap the full Halcyon Expanse game."""
    state = HalcyonGameState(seed=seed)
    engine = Engine(tick_rate=10)

    # Register Xandria subsystems
    from main import GenerationSubsystem, RenderSubsystem
    gen_sub = engine.register(GenerationSubsystem(state))
    render_sub = engine.register(RenderSubsystem(state))
    physics_sub = engine.register(PhysicsSim(state))

    # Register Halcyon master subsystem
    halcyon_sub = engine.register(HalcyonSubsystem(state))

    # Create player as Actor
    player = Actor(
        kind="player",
        x=5, y=5, hp=100,
        resonance_type=player_resonance,
        attunement_level=1,
        lattice_charge=500.0,
        lattice_debt=0.0
    )
    state.add_entity(player)
    state.player_resonance = player_resonance

    # Register default abilities
    default_abilities = [
        Ability("ember_strike", "Ember Strike", 50, "Ember", 1, "Basic fire attack"),
        Ability("gale_dash", "Gale Dash", 40, "Gale", 1, "Wind dash forward"),
        Ability("tide_heal", "Tide Heal", 60, "Tide", 1, "Restore HP with water"),
        Ability("hollow_drain", "Hollow Drain", 70, "Hollow", 2, "Drain enemy LC"),
        Ability("iron_shield", "Iron Shield", 45, "Iron", 1, "Block next attack"),
        Ability("root_bind", "Root Bind", 55, "Root", 1, "Immobilize target"),
        Ability("chorus_blast", "Chorus Blast", 80, "Chorus", 2, "Sonic damage wave"),
    ]
    for ability in default_abilities:
        state.ability_system.register_ability(ability)

    # Add starting items
    state.inventory.add_item(Item("starter_sword", "Rusty Blade", "Common", "weapon"))
    state.inventory.add_item(Item("healing_potion", "Glowroot Tincture", "Uncommon", "consumable"))

    # Load initial scene
    state.scenes.load_scene("VeyraPrime")

    print("=== HALCYON EXPANSE ===")
    print(f"Year: {CURRENT_YEAR} | Seed: {state.seed}")
    print(f"Resonance: {player_resonance}")
    print(f"System: {state.star_systems.current_system}")
    print(f"Scene: {state.scenes.get_scene('VeyraPrime').get_lighting_profile()}")
    print(f"Abilities: {len(state.ability_system.abilities)}")
    print(f"Enemies: {len(state.bestiary.templates)}")
    print(f"Factions: {len(state.factions.factions)}")
    print(f"Codex: {len(state.codex.entries)} entries")
    print(f"Inventory: {len(state.inventory.items)} items")
    print(f"Economy: CS {state.economy.get_balance('CS'):.2f} | LM {state.economy.get_balance('LM'):.2f}")
    print("\nType commands: go north, warp Ashduin, cast ember_strike, status, inventory, codex, year")
    print("               spawn Ash Wraith, exchange 10 CS to LM, quit")

    return state, engine, gen_sub, render_sub, halcyon_sub


def halcyon_repl():
    state, engine, gen_sub, render_sub, halcyon_sub = bootstrap_halcyon(seed=78, player_resonance="Ember")

    parser = PromptParser()
    router = HalcyonCommandRouter(engine, state)

    while True:
        try:
            text = input("> ").strip()
        except EOFError:
            break
        if not text:
            continue
        cmd = parser.parse(text)
        result = router.dispatch(cmd)
        print(result)
        engine.step()
        if not engine.running:
            break


if __name__ == "__main__":
    halcyon_repl()
