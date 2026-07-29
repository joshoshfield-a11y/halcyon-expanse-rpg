"""
Halcyon Expanse — Save/Load System
JSON-based persistence with compression. Multiple save slots.
"""
import json
import os
import gzip
import time


class SaveManager:
    """Manages game saves with multiple slots."""

    SAVE_DIR = "saves"
    MAX_SLOTS = 5

    def __init__(self):
        os.makedirs(self.SAVE_DIR, exist_ok=True)
        self.current_slot = 1

    def _get_path(self, slot):
        return os.path.join(self.SAVE_DIR, f"save_{slot}.json.gz")

    def save_exists(self, slot):
        return os.path.exists(self._get_path(slot))

    def get_save_info(self, slot):
        """Get metadata about a save without loading full data."""
        path = self._get_path(slot)
        if not os.path.exists(path):
            return None
        try:
            with gzip.open(path, 'rt') as f:
                data = json.load(f)
            return {
                "slot": slot,
                "system": data.get("system", "Unknown"),
                "resonance": data.get("resonance", "Unknown"),
                "level": data.get("attunement_level", 1),
                "hp": data.get("hp", 0),
                "play_time": data.get("play_time", 0),
                "timestamp": data.get("timestamp", 0),
                "date": time.strftime("%Y-%m-%d %H:%M", time.localtime(data.get("timestamp", 0))),
            }
        except:
            return None

    def list_saves(self):
        """List all save slots with info."""
        saves = []
        for slot in range(1, self.MAX_SLOTS + 1):
            info = self.get_save_info(slot)
            if info:
                saves.append(info)
        return saves

    def save_game(self, game_state_dict, slot=None):
        """Save game state to a slot."""
        slot = slot or self.current_slot
        path = self._get_path(slot)

        # Add metadata
        save_data = dict(game_state_dict)
        save_data["timestamp"] = time.time()
        save_data["save_version"] = "0.3.0"

        # Compress and save
        with gzip.open(path, 'wt') as f:
            json.dump(save_data, f, indent=2)

        return f"Game saved to slot {slot}"

    def load_game(self, slot=None):
        """Load game state from a slot."""
        slot = slot or self.current_slot
        path = self._get_path(slot)

        if not os.path.exists(path):
            return None, f"No save found in slot {slot}"

        try:
            with gzip.open(path, 'rt') as f:
                data = json.load(f)
            return data, f"Game loaded from slot {slot}"
        except Exception as e:
            return None, f"Failed to load slot {slot}: {e}"

    def delete_save(self, slot):
        """Delete a save slot."""
        path = self._get_path(slot)
        if os.path.exists(path):
            os.remove(path)
            return f"Save slot {slot} deleted"
        return f"No save in slot {slot}"

    def auto_save(self, game_state_dict):
        """Quick auto-save to slot 0 (overwritten each time)."""
        path = os.path.join(self.SAVE_DIR, "autosave.json.gz")
        save_data = dict(game_state_dict)
        save_data["timestamp"] = time.time()
        save_data["save_version"] = "0.3.0"
        with gzip.open(path, 'wt') as f:
            json.dump(save_data, f, indent=2)
        return "Auto-saved"
