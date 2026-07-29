

"""
Simulation Subsystem
---------------------
Handles physics-lite movement, entity AI ticking, economy simulation,
and faction relationship dynamics. Runs deterministically off GameState.rng.
"""

class Entity:
    def __init__(self, kind="generic", x=0, y=0, hp=100, data=None):
        self.id = None
        self.kind = kind
        self.x, self.y = x, y
        self.hp = hp
        self.data = data or {}

    def to_dict(self):
        return {"kind": self.kind, "x": self.x, "y": self.y, "hp": self.hp, "data": self.data}


class EntityFactory:
    @staticmethod
    def from_dict(d):
        e = Entity(kind=d["kind"], x=d["x"], y=d["y"], hp=d["hp"], data=d.get("data", {}))
        return e


class PhysicsSim:
    name = "physics"
    def __init__(self, state):
        self.state = state

    def update(self, dt):
        for e in self.state.entities.values():
            vx, vy = e.data.get("vx", 0), e.data.get("vy", 0)
            e.x += vx * dt
            e.y += vy * dt


class EconomySim:
    name = "economy"
    def __init__(self, state, rng):
        self.state = state
        self.rng = rng
        self.markets = {}

    def register_market(self, region, base_prices):
        self.markets[region] = dict(base_prices)

    def update(self, dt):
        for region, prices in self.markets.items():
            for good in prices:
                drift = self.rng.uniform(-0.02, 0.02)
                prices[good] = max(1, round(prices[good] * (1 + drift), 2))


class FactionSim:
    name = "factions"
    def __init__(self, rng):
        self.rng = rng
        self.relations = {}

    def set_relation(self, a, b, value):
        self.relations[frozenset((a, b))] = value

    def update(self, dt):
        for key in list(self.relations.keys()):
            drift = self.rng.uniform(-0.5, 0.5)
            self.relations[key] = max(-100, min(100, self.relations[key] + drift))
