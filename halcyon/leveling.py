"""
Halcyon Expanse — Leveling & Experience System
XP gain, level-ups, attunement progression, skill points.
"""
import math


class LevelingSystem:
    """Manages player experience and level progression."""

    # XP required for each attunement level
    XP_TABLE = {
        1: 0,
        2: 100,
        3: 250,
        4: 500,
        5: 1000,
        6: 2000,
        7: 4000,
        8: 8000,
        9: 16000,
        10: 32000,
    }

    # XP rewards
    XP_REWARDS = {
        "kill_tier_1": 25,
        "kill_tier_2": 50,
        "kill_tier_3": 100,
        "kill_tier_4": 200,
        "kill_tier_5": 500,
        "quest_diff_1": 50,
        "quest_diff_2": 100,
        "quest_diff_3": 200,
        "quest_diff_4": 400,
        "quest_diff_5": 800,
        "discovery": 10,
        "codex_unlock": 25,
        "warp_new_system": 50,
    }

    def __init__(self):
        self.xp = 0
        self.total_xp = 0
        self.level = 1
        self.skill_points = 0
        self.xp_to_next = self.XP_TABLE[2]

    def add_xp(self, amount, source=""):
        """Add XP and check for level-ups."""
        self.xp += amount
        self.total_xp += amount
        leveled_up = False

        while self.level < 10 and self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.skill_points += 1
            leveled_up = True
            if self.level < 10:
                self.xp_to_next = self.XP_TABLE[self.level + 1] - self.XP_TABLE[self.level]
            else:
                self.xp_to_next = 999999

        return leveled_up, amount

    def get_xp_for_kill(self, enemy_threat_tier):
        return self.XP_REWARDS.get(f"kill_tier_{enemy_threat_tier}", 25)

    def get_xp_for_quest(self, difficulty):
        return self.XP_REWARDS.get(f"quest_diff_{difficulty}", 50)

    def get_progress_pct(self):
        if self.level >= 10:
            return 100.0
        return (self.xp / self.xp_to_next) * 100

    def get_level_bonuses(self):
        """Get stat bonuses for current level."""
        return {
            "hp_bonus": (self.level - 1) * 10,
            "lc_bonus": (self.level - 1) * 50,
            "damage_bonus": (self.level - 1) * 2,
            "lc_regen_bonus": (self.level - 1) * 1,
        }

    def to_dict(self):
        return {
            "xp": self.xp,
            "total_xp": self.total_xp,
            "level": self.level,
            "skill_points": self.skill_points,
            "xp_to_next": self.xp_to_next,
            "progress_pct": self.get_progress_pct(),
        }
