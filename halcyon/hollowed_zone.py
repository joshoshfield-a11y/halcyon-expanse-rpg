"""
Halcyon Expanse — Hollowed Zones
Build Step 6: Three trigger volumes that force lattice_charge_max = 0.
Vashti Scar (VeyraPrime), Grey Reef (ChorusDeep), Bare Meridian (IronMeridian)
"""


class HollowedZone:
    """Anti-magic trigger volume. Nulls all LC while inside."""
    def __init__(self, name, system, world=None, description=""):
        self.name = name
        self.system = system
        self.world = world
        self.description = description
        self.active = False

    def on_enter(self, actor):
        """Called when actor enters the zone."""
        actor.enter_hollowed_zone()
        self.active = True
        return f"Entered {self.name}: Lattice Actions nullified"

    def on_exit(self, actor):
        """Called when actor exits the zone."""
        actor.exit_hollowed_zone()
        self.active = False
        return f"Exited {self.name}: Lattice Actions restored"

    def to_dict(self):
        return {
            "name": self.name,
            "system": self.system,
            "world": self.world,
            "description": self.description,
        }


class HollowedZoneManager:
    """Manages all three Hollowed Zones."""

    DEFAULT_ZONES = [
        {"name": "Vashti Scar", "system": "VeyraPrime", "world": "Kethara-Home",
         "description": "Walled containment, 40km circumference. LC permanently null."},
        {"name": "Grey Reef", "system": "ChorusDeep", "world": None,
         "description": "Anti-magic zone."},
        {"name": "Bare Meridian", "system": "IronMeridian", "world": None,
         "description": "Anti-magic zone."},
    ]

    def __init__(self, config_path=None):
        self.zones = {}
        self._load_defaults()

    def _load_defaults(self):
        for z in self.DEFAULT_ZONES:
            self.zones[z["name"]] = HollowedZone(**z)

    def get_zone(self, name):
        return self.zones.get(name)

    def get_zones_in_system(self, system_name):
        return [z for z in self.zones.values() if z.system == system_name]

    def check_actor_position(self, actor, system_name, zone_name=None):
        """Check if actor is in a hollowed zone. Returns zone or None."""
        zones = self.get_zones_in_system(system_name)
        if zone_name:
            zones = [z for z in zones if z.name == zone_name]
        # In a real engine, this would check spatial overlap
        # For now, return first matching zone
        return zones[0] if zones else None

    def to_dict(self):
        return {k: v.to_dict() for k, v in self.zones.items()}
