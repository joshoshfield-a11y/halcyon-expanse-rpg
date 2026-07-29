

"""
Prompt Parser / Command Interface
-----------------------------------
Converts free-text player input into structured engine commands, in-game.
This is the layer that makes the whole suite prompt-driven: a live player
types natural language, and this module maps intent -> engine call, using
lightweight keyword/pattern matching (no external LLM dependency required,
though a hook is provided to route through one if available).
"""
import re

MOVE_WORDS = {
    "north": (0, -1), "n": (0, -1),
    "south": (0, 1), "s": (0, 1),
    "east": (1, 0), "e": (1, 0),
    "west": (-1, 0), "w": (-1, 0),
}

INTENT_PATTERNS = [
    (re.compile(r"^(go|move|walk|head)\s+(?P<dir>\w+)", re.I), "move"),
    (re.compile(r"^(attack|fight|strike)\s+(?P<target>.+)", re.I), "attack"),
    (re.compile(r"^(talk to|speak to|greet)\s+(?P<target>.+)", re.I), "talk"),
    (re.compile(r"^(generate|create|build)\s+(a\s+)?(?P<what>dungeon|npc|quest|world|chunk)", re.I), "generate"),
    (re.compile(r"^(inspect|look at|examine)\s+(?P<target>.+)", re.I), "inspect"),
    (re.compile(r"^(save)\b", re.I), "save"),
    (re.compile(r"^(load)\b", re.I), "load"),
    (re.compile(r"^(quit|exit)\b", re.I), "quit"),
]


class ParsedCommand:
    def __init__(self, intent, args):
        self.intent = intent
        self.args = args

    def __repr__(self):
        return f"ParsedCommand(intent={self.intent!r}, args={self.args!r})"


class PromptParser:
    def __init__(self, llm_hook=None):
        self.llm_hook = llm_hook

    def parse(self, text):
        text = text.strip()
        for pattern, intent in INTENT_PATTERNS:
            m = pattern.match(text)
            if m:
                return ParsedCommand(intent, m.groupdict())
        if self.llm_hook:
            return self.llm_hook(text)
        return ParsedCommand("unknown", {"raw": text})


class CommandRouter:
    """Dispatches ParsedCommand objects to engine/subsystem actions."""
    def __init__(self, engine, state):
        self.engine = engine
        self.state = state
        self.handlers = {
            "move": self._move,
            "attack": self._attack,
            "talk": self._talk,
            "generate": self._generate,
            "inspect": self._inspect,
            "save": self._save,
            "load": self._load,
            "quit": self._quit,
            "unknown": self._unknown,
        }

    def dispatch(self, cmd: ParsedCommand):
        handler = self.handlers.get(cmd.intent, self._unknown)
        result = handler(cmd.args)
        self.state.log_prompt(str(cmd.args), cmd.intent)
        return result

    def _move(self, args):
        d = args.get("dir", "").lower()
        dx, dy = MOVE_WORDS.get(d, (0, 0))
        player = self.state.entities.get(1)
        if player:
            player.x += dx
            player.y += dy
        return f"moved {d} ({dx},{dy})"

    def _attack(self, args):
        return f"attacking {args.get('target')}"

    def _talk(self, args):
        return f"talking to {args.get('target')}"

    def _generate(self, args):
        return f"generating {args.get('what')}"

    def _inspect(self, args):
        return f"inspecting {args.get('target')}"

    def _save(self, args):
        self.state.save("autosave.json")
        return "state saved"

    def _load(self, args):
        return "load requested"

    def _quit(self, args):
        self.engine.stop()
        return "engine stopped"

    def _unknown(self, args):
        return f"unrecognized command: {args.get('raw')}"
