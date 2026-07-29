

"""
Xandria Engine Suite — Main Entry Point
------------------------------------------
Runnable, prompt-driven game loop. Launch with: python main.py
Type natural-language commands at the prompt (e.g. "go north",
"generate a dungeon", "attack the guard", "save", "quit").
"""
import sys
from core.engine import Engine, Subsystem
from core.state import GameState
from generation.procgen import WorldGenerator, NPCGenerator, QuestGenerator
from simulation.simcore import Entity, EntityFactory, PhysicsSim, EconomySim, FactionSim
from rendering.renderer import ASCIIRenderer, VisualRenderer
from interface.prompt_parser import PromptParser, CommandRouter


class GenerationSubsystem(Subsystem):
    name = "generation"
    def __init__(self, state):
        self.state = state
        self.world_gen = WorldGenerator(state.rng)
        self.npc_gen = NPCGenerator(state.rng)
        self.quest_gen = QuestGenerator(state.rng)

    def update(self, dt):
        pass


class RenderSubsystem(Subsystem):
    name = "render"
    def __init__(self, state):
        self.state = state
        self.ascii_renderer = ASCIIRenderer()
        self.visual_renderer = VisualRenderer()

    def update(self, dt):
        pass


def bootstrap():
    state = GameState()
    engine = Engine(tick_rate=10)

    gen_sub = engine.register(GenerationSubsystem(state))
    render_sub = engine.register(RenderSubsystem(state))
    physics_sub = engine.register(PhysicsSim(state))

    chunk = gen_sub.world_gen.generate_chunk(width=20, height=12)
    state.world["current_chunk"] = chunk

    player = Entity(kind="player", x=2, y=2, hp=100)
    state.add_entity(player)

    parser = PromptParser()
    router = CommandRouter(engine, state)

    print("=== Xandria Engine Suite ===")
    print(render_sub.ascii_renderer.render_entities(chunk, list(state.entities.values())))
    print("Type commands (go north, generate dungeon, attack guard, save, quit)")

    return state, engine, gen_sub, render_sub, parser, router


def repl():
    state, engine, gen_sub, render_sub, parser, router = bootstrap()
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
    repl()
