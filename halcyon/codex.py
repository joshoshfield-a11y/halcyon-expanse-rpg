"""
Halcyon Expanse — Codex / Lore System
Build Step 11: Eras timeline as unlockable entries, triggered by location/quest flags.
Not playable content — pure lore unlocks.
"""


class CodexEntry:
    def __init__(self, year, name, description, unlock_trigger=None):
        self.year = year
        self.name = name
        self.description = description
        self.unlocked = False
        self.unlock_trigger = unlock_trigger or {}

    def unlock(self):
        self.unlocked = True
        return f"Codex unlocked: Year {self.year} — {self.name}"

    def check_trigger(self, location=None, quest_flags=None):
        """Check if unlock conditions are met."""
        if self.unlocked:
            return False
        trigger = self.unlock_trigger
        if trigger.get("location") and location == trigger["location"]:
            return True
        if trigger.get("quest_flag") and quest_flags and trigger["quest_flag"] in quest_flags:
            return True
        return False

    def to_dict(self):
        return {
            "year": self.year,
            "name": self.name,
            "description": self.description,
            "unlocked": self.unlocked,
        }


class Codex:
    """Unlockable lore codex."""

    DEFAULT_ENTRIES = [
        {"year": 0, "name": "The Shattering", "description": "Lattice first discovered.",
         "unlock_trigger": {"location": "VeyraPrime"}},
        {"year": 187, "name": "First Concord", "description": "Factions form.",
         "unlock_trigger": {"quest_flag": "first_concord"}},
        {"year": 412, "name": "The Hollowing", "description": "HollowAnchor founded.",
         "unlock_trigger": {"location": "HollowAnchor"}},
        {"year": 518, "name": "Vashti Scar Sealed", "description": "Concord Wall built.",
         "unlock_trigger": {"location": "Vashti Scar"}},
        {"year": 688, "name": "Hollow Choir Withdrawal", "description": "Choir withdraws from public.",
         "unlock_trigger": {"quest_flag": "choir_withdrawal"}},
        {"year": 706, "name": "Current Era", "description": "Present day.",
         "unlock_trigger": {}},  # Always unlocked
    ]

    def __init__(self):
        self.entries = {}
        self._load_defaults()

    def _load_defaults(self):
        for e in self.DEFAULT_ENTRIES:
            entry = CodexEntry(**e)
            self.entries[entry.year] = entry
        # Unlock current era by default
        self.entries[706].unlock()

    def check_triggers(self, location=None, quest_flags=None):
        """Check all entries for unlock conditions. Returns list of newly unlocked."""
        newly_unlocked = []
        for entry in self.entries.values():
            if entry.check_trigger(location, quest_flags):
                entry.unlock()
                newly_unlocked.append(entry)
        return newly_unlocked

    def get_unlocked(self):
        return [e for e in self.entries.values() if e.unlocked]

    def to_dict(self):
        return {"entries": [e.to_dict() for e in self.entries.values()]}
