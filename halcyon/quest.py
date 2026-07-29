"""
Halcyon Expanse — Quest System
Objectives, rewards, tracking, quest log with faction reputation effects.
"""
import time


class QuestObjective:
    """Single quest objective."""
    def __init__(self, description, objective_type, target, required=1, current=0):
        self.description = description
        self.objective_type = objective_type  # "kill", "collect", "reach", "talk", "escort"
        self.target = target
        self.required = required
        self.current = current
        self.completed = False

    def progress(self, amount=1):
        if not self.completed:
            self.current += amount
            if self.current >= self.required:
                self.current = self.required
                self.completed = True
                return True
        return False

    def to_dict(self):
        return {
            "description": self.description,
            "type": self.objective_type,
            "target": self.target,
            "required": self.required,
            "current": self.current,
            "completed": self.completed,
        }


class Quest:
    """A complete quest with multiple objectives."""

    DIFFICULTY_REWARDS = {
        1: {"xp": 50, "cs": 10, "lm": 5},
        2: {"xp": 100, "cs": 25, "lm": 10},
        3: {"xp": 200, "cs": 50, "lm": 20},
        4: {"xp": 400, "cs": 100, "lm": 40},
        5: {"xp": 800, "cs": 200, "lm": 80},
    }

    def __init__(self, quest_id, name, description, giver, faction, difficulty=1, objectives=None):
        self.quest_id = quest_id
        self.name = name
        self.description = description
        self.giver = giver
        self.faction = faction
        self.difficulty = difficulty
        self.objectives = objectives or []
        self.active = False
        self.completed = False
        self.turned_in = False
        self.time_started = 0
        self.time_completed = 0

    def start(self):
        self.active = True
        self.time_started = time.time()

    def check_completion(self):
        if all(obj.completed for obj in self.objectives):
            self.completed = True
            self.time_completed = time.time()
            return True
        return False

    def get_rewards(self):
        return self.DIFFICULTY_REWARDS.get(self.difficulty, {"xp": 50, "cs": 10, "lm": 5})

    def get_progress_text(self):
        lines = [f"{self.name} (Difficulty: {self.difficulty})"]
        lines.append(f"  {self.description}")
        lines.append(f"  Given by: {self.giver} ({self.faction})")
        for i, obj in enumerate(self.objectives, 1):
            status = "✓" if obj.completed else "○"
            lines.append(f"  {status} {i}. {obj.description} ({obj.current}/{obj.required})")
        return "\n".join(lines)

    def to_dict(self):
        return {
            "quest_id": self.quest_id,
            "name": self.name,
            "description": self.description,
            "giver": self.giver,
            "faction": self.faction,
            "difficulty": self.difficulty,
            "objectives": [obj.to_dict() for obj in self.objectives],
            "active": self.active,
            "completed": self.completed,
            "turned_in": self.turned_in,
        }


class QuestManager:
    """Manages all quests in the game."""

    def __init__(self):
        self.quests = {}
        self.active_quests = []
        self.completed_quests = []
        self.quest_log = []

    def add_quest(self, quest):
        self.quests[quest.quest_id] = quest

    def start_quest(self, quest_id):
        quest = self.quests.get(quest_id)
        if quest and not quest.active and not quest.completed:
            quest.start()
            self.active_quests.append(quest)
            self.quest_log.append(f"Started: {quest.name}")
            return True, f"Quest started: {quest.name}"
        return False, "Quest not available"

    def update_objective(self, objective_type, target, amount=1):
        """Update objectives across all active quests."""
        updated = []
        for quest in self.active_quests:
            for obj in quest.objectives:
                if obj.objective_type == objective_type and obj.target == target and not obj.completed:
                    if obj.progress(amount):
                        updated.append((quest, obj))
                        self.quest_log.append(f"Objective complete: {obj.description}")
            if quest.check_completion():
                self.active_quests.remove(quest)
                self.completed_quests.append(quest)
                self.quest_log.append(f"Quest complete: {quest.name}")
        return updated

    def turn_in_quest(self, quest_id):
        """Turn in a completed quest for rewards."""
        quest = self.quests.get(quest_id)
        if quest and quest.completed and not quest.turned_in:
            quest.turned_in = True
            rewards = quest.get_rewards()
            self.quest_log.append(f"Turned in: {quest.name}")
            return True, rewards
        return False, None

    def get_active_quests(self):
        return self.active_quests

    def get_available_quests(self):
        return [q for q in self.quests.values() if not q.active and not q.completed]

    def get_quest_log(self, max_entries=10):
        return self.quest_log[-max_entries:]

    def to_dict(self):
        return {
            "quests": {k: v.to_dict() for k, v in self.quests.items()},
            "active": [q.quest_id for q in self.active_quests],
            "completed": [q.quest_id for q in self.completed_quests],
            "log": self.quest_log,
        }
