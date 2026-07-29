

"""
Game state container with JSON save/load. Holds entities, world grid,
player prompt history, and RNG seed for deterministic replay.
"""
import json, random

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

    def remove_entity(self, eid):
        self.entities.pop(eid, None)

    def log_prompt(self, text, parsed_command):
        self.prompt_log.append({"text": text, "command": parsed_command})

    def to_dict(self):
        return {
            "seed": self.seed,
            "world": self.world,
            "entities": {eid: e.to_dict() for eid, e in self.entities.items()},
            "prompt_log": self.prompt_log,
            "next_entity_id": self.next_entity_id,
        }

    def save(self, path):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path, entity_factory):
        with open(path) as f:
            data = json.load(f)
        gs = cls(seed=data["seed"])
        gs.world = data["world"]
        gs.prompt_log = data["prompt_log"]
        gs.next_entity_id = data["next_entity_id"]
        for eid, edata in data["entities"].items():
            gs.entities[int(eid)] = entity_factory.from_dict(edata)
        return gs
