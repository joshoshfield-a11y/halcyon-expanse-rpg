

"""
Xandria Engine Core
--------------------
Central tick-based game loop with an event bus, subsystem registry,
and deterministic frame stepping. Every subsystem (renderer, physics,
AI, procgen) registers as a plugin and receives update(dt) calls.
"""
import time
from collections import defaultdict, deque

class EventBus:
    def __init__(self):
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
        self.state = None
        self.running = False
        self.frame = 0

    def register(self, subsystem: Subsystem):
        subsystem.on_attach(self)
        self.subsystems[subsystem.name] = subsystem
        return subsystem

    def get(self, name):
        return self.subsystems.get(name)

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
        for sub in self.subsystems.values():
            sub.shutdown()
