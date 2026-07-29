"""
Halcyon Expanse — World Events System
Random encounters, weather, day/night cycle, faction events.
"""
import random
import math
import time


class WorldEvent:
    """A dynamic world event."""
    def __init__(self, event_id, name, description, duration, 
                 effects=None, condition=None, on_trigger=None):
        self.event_id = event_id
        self.name = name
        self.description = description
        self.duration = duration
        self.remaining = duration
        self.effects = effects or {}
        self.condition = condition
        self.on_trigger = on_trigger
        self.active = False

    def update(self, dt):
        if self.active:
            self.remaining -= dt
            if self.remaining <= 0:
                self.active = False
                return "ended"
        return "active" if self.active else "inactive"

    def trigger(self, game_state):
        if self.condition and not self.condition(game_state):
            return False
        self.active = True
        self.remaining = self.duration
        if self.on_trigger:
            self.on_trigger(game_state)
        return True


class WorldEventManager:
    """Manages all world events and random encounters."""

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.events = []
        self.active_events = []
        self.event_history = []
        self.time_of_day = 12.0  # 0-24 hour cycle
        self.day_length = 300.0  # 5 minutes = 24 hours
        self.weather = "clear"
        self.weather_timer = 0.0
        self.encounter_cooldown = 0.0
        self._init_events()

    def _init_events(self):
        """Initialize possible world events."""
        self.events = [
            WorldEvent("lattice_storm", "Lattice Storm", 
                      "The Lattice surges unpredictably. All abilities cost 50% more.",
                      60.0,
                      effects={"lc_cost_mult": 1.5}),
            WorldEvent("ashfall_surge", "Ashfall Surge",
                      "Ashduin's volcanoes erupt. Visibility reduced, fire damage increased.",
                      90.0,
                      effects={"visibility": 0.5, "fire_damage": 2.0}),
            WorldEvent("choir_whispers", "Choir Whispers",
                      "The Hollow Choir speaks. Hollow resonance abilities are empowered.",
                      45.0,
                      effects={"hollow_power": 1.5}),
            WorldEvent("ferro_embargo", "Ferro Embargo",
                      "The Ferro Compact halts trade. CS value drops 30%.",
                      120.0,
                      effects={"cs_value": 0.7}),
            WorldEvent("seam_flux", "Seam Flux",
                      "The Seams are unstable. Warp costs double LC.",
                      60.0,
                      effects={"warp_cost": 2.0}),
            WorldEvent("starfall", "Starfall",
                      "Meteorites rain from above. Rare materials can be found.",
                      30.0,
                      effects={"loot_quality": 2.0}),
        ]

    def update(self, dt, game_state):
        """Update time, weather, and events."""
        # Time of day
        self.time_of_day = (self.time_of_day + (dt / self.day_length) * 24) % 24

        # Weather changes
        self.weather_timer -= dt
        if self.weather_timer <= 0:
            self.weather_timer = self.rng.uniform(60, 180)
            weather_options = ["clear", "cloudy", "rain", "fog", "storm"]
            weights = [0.4, 0.25, 0.15, 0.12, 0.08]
            self.weather = self.rng.choices(weather_options, weights=weights)[0]

        # Random event trigger
        if self.rng.random() < 0.001 and len(self.active_events) < 2:
            available = [e for e in self.events if not e.active]
            if available:
                event = self.rng.choice(available)
                if event.trigger(game_state):
                    self.active_events.append(event)
                    self.event_history.append(f"{event.name} started")

        # Update active events
        for event in self.active_events[:]:
            status = event.update(dt)
            if status == "ended":
                self.active_events.remove(event)
                self.event_history.append(f"{event.name} ended")

        # Encounter cooldown
        if self.encounter_cooldown > 0:
            self.encounter_cooldown -= dt

    def get_time_string(self):
        """Get formatted time of day."""
        hour = int(self.time_of_day)
        minute = int((self.time_of_day - hour) * 60)
        period = "AM" if hour < 12 else "PM"
        display_hour = hour if hour <= 12 else hour - 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour}:{minute:02d} {period}"

    def get_lighting_modifier(self):
        """Get lighting modifier based on time of day."""
        if 6 <= self.time_of_day < 18:
            return 1.0  # Day
        elif 5 <= self.time_of_day < 7 or 17 <= self.time_of_day < 19:
            return 0.6  # Dawn/Dusk
        else:
            return 0.25  # Night

    def check_random_encounter(self, game_state):
        """Check for random encounter."""
        if self.encounter_cooldown > 0:
            return None

        if self.rng.random() < 0.02:  # 2% per check
            self.encounter_cooldown = 30.0

            encounter_types = [
                ("wandering_merchant", 0.15),
                ("ambush", 0.35),
                ("distress_signal", 0.20),
                ("resource_cache", 0.20),
                ("faction_patrol", 0.10),
            ]
            types, weights = zip(*encounter_types)
            encounter = self.rng.choices(types, weights=weights)[0]
            return encounter
        return None

    def to_dict(self):
        return {
            "time": self.get_time_string(),
            "weather": self.weather,
            "active_events": [e.name for e in self.active_events],
            "history": self.event_history[-10:],
        }
