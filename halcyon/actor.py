"""
Halcyon Expanse — Actor System
Build Step 2: Actor base class with lattice_charge, resonance_type, attunement_level, lattice_debt
"""
import time
from simulation.simcore import Entity

RESONANCE_TYPES = ["Ember", "Gale", "Hollow", "Tide", "Root", "Iron", "Chorus"]


class Actor(Entity):
    """
    Actor base class matching actor_stats_schema exactly.
    Extends base Entity with Halcyon-specific stats.
    """
    def __init__(self, kind="actor", x=0, y=0, hp=100,
                 resonance_type="Ember", attunement_level=1,
                 lattice_charge=500.0, lattice_debt=0.0, data=None):
        super().__init__(kind=kind, x=x, y=y, hp=hp, data=data)

        # Immutable post-spawn
        if resonance_type not in RESONANCE_TYPES:
            raise ValueError(f"Invalid resonance_type: {resonance_type}. Must be one of {RESONANCE_TYPES}")
        self.resonance_type = resonance_type

        self.attunement_level = max(1, min(10, int(attunement_level)))
        self.lattice_charge = max(0.0, min(1000.0, float(lattice_charge)))
        self.lattice_debt = max(0.0, float(lattice_debt))

        # Debt tracking
        self._last_debt_update = time.time()
        self._debt_accrual_rate = 0.03  # 3% per hour
        self._debt_accrual_interval = 3600.0  # seconds

        # Hollowed zone suppression
        self._hollowed_zone_active = False
        self._base_max_lc = 1000.0

    @property
    def lattice_charge_max(self):
        if self._hollowed_zone_active:
            return 0.0
        return self._base_max_lc

    @property
    def effective_lc_regen(self):
        """LC regeneration rate, reduced by lattice debt."""
        debt_penalty = min(1.0, self.lattice_debt / 1000.0)
        return max(0.0, 1.0 - debt_penalty) * 10.0  # 10 LC/sec base regen

    def update_debt(self):
        """Accrue lattice debt based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_debt_update
        intervals = elapsed / self._debt_accrual_interval
        if intervals > 0:
            self.lattice_debt += self.lattice_debt * self._debt_accrual_rate * intervals
            self._last_debt_update = now

    def enter_hollowed_zone(self):
        self._hollowed_zone_active = True
        self.lattice_charge = 0.0

    def exit_hollowed_zone(self):
        self._hollowed_zone_active = False

    def consume_lc(self, amount):
        """Attempt to consume LC. Returns True if successful."""
        if self._hollowed_zone_active:
            return False
        if self.lattice_charge >= amount:
            self.lattice_charge -= amount
            return True
        return False

    def regenerate_lc(self, dt):
        """Regenerate LC over time, accounting for debt."""
        if self._hollowed_zone_active:
            return
        regen = self.effective_lc_regen * dt
        self.lattice_charge = min(self.lattice_charge_max, self.lattice_charge + regen)

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "resonance_type": self.resonance_type,
            "attunement_level": self.attunement_level,
            "lattice_charge": self.lattice_charge,
            "lattice_debt": self.lattice_debt,
            "hollowed_zone_active": self._hollowed_zone_active,
        })
        return d

    @classmethod
    def from_dict(cls, d):
        return cls(
            kind=d.get("kind", "actor"),
            x=d.get("x", 0), y=d.get("y", 0), hp=d.get("hp", 100),
            resonance_type=d.get("resonance_type", "Ember"),
            attunement_level=d.get("attunement_level", 1),
            lattice_charge=d.get("lattice_charge", 500.0),
            lattice_debt=d.get("lattice_debt", 0.0),
            data=d.get("data", {})
        )
