"""
Halcyon Expanse — Sprite Atlas & Animation System
Sprite sheets, frame-based animations, directional sprites for player/enemies.
"""
import os
import json


class SpriteFrame:
    """Single animation frame with timing."""
    def __init__(self, char_glyph, fg_color, bg_color=None, duration=0.1):
        self.char_glyph = char_glyph  # ASCII fallback
        self.fg_color = fg_color      # (r,g,b) foreground
        self.bg_color = bg_color or (0, 0, 0)  # (r,g,b) background
        self.duration = duration      # seconds this frame displays


class AnimatedSprite:
    """Multi-frame animated sprite with state machine."""
    def __init__(self, name, frames=None, default_state="idle"):
        self.name = name
        self.frames = frames or {}  # state -> [SpriteFrame]
        self.current_state = default_state
        self.frame_index = 0
        self.state_timer = 0.0
        self.direction = "down"  # up/down/left/right

    def add_state(self, state_name, frame_list):
        self.frames[state_name] = frame_list

    def set_state(self, state):
        if state != self.current_state and state in self.frames:
            self.current_state = state
            self.frame_index = 0
            self.state_timer = 0.0

    def update(self, dt):
        self.state_timer += dt
        current_frames = self.frames.get(self.current_state, [])
        if not current_frames:
            return

        current_frame = current_frames[self.frame_index]
        if self.state_timer >= current_frame.duration:
            self.state_timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(current_frames)

    def get_current_frame(self):
        frames = self.frames.get(self.current_state, [])
        if frames:
            return frames[self.frame_index % len(frames)]
        return SpriteFrame("?", (255, 255, 255))


class SpriteAtlas:
    """Central registry for all game sprites."""

    def __init__(self):
        self.sprites = {}
        self._build_default_sprites()

    def _build_default_sprites(self):
        # Player sprite — 4 directions, idle + walk + attack + cast
        player = AnimatedSprite("player")

        # Idle frames (breathing animation)
        player.add_state("idle_down", [
            SpriteFrame("@", (0, 200, 255), (20, 30, 40), 0.4),
            SpriteFrame("@", (0, 180, 230), (20, 30, 40), 0.4),
        ])
        player.add_state("idle_up", [
            SpriteFrame("^", (0, 200, 255), (20, 30, 40), 0.4),
            SpriteFrame("^", (0, 180, 230), (20, 30, 40), 0.4),
        ])
        player.add_state("idle_left", [
            SpriteFrame("<", (0, 200, 255), (20, 30, 40), 0.4),
            SpriteFrame("<", (0, 180, 230), (20, 30, 40), 0.4),
        ])
        player.add_state("idle_right", [
            SpriteFrame(">", (0, 200, 255), (20, 30, 40), 0.4),
            SpriteFrame(">", (0, 180, 230), (20, 30, 40), 0.4),
        ])

        # Walk frames
        player.add_state("walk_down", [
            SpriteFrame("@", (0, 220, 255), (20, 30, 40), 0.15),
            SpriteFrame("O", (0, 220, 255), (20, 30, 40), 0.15),
        ])
        player.add_state("walk_up", [
            SpriteFrame("^", (0, 220, 255), (20, 30, 40), 0.15),
            SpriteFrame("|", (0, 220, 255), (20, 30, 40), 0.15),
        ])

        # Attack frames
        player.add_state("attack", [
            SpriteFrame("X", (255, 100, 50), (40, 20, 20), 0.1),
            SpriteFrame("*", (255, 150, 80), (40, 20, 20), 0.1),
            SpriteFrame("@", (0, 200, 255), (20, 30, 40), 0.2),
        ])

        # Cast frames (Lattice Action)
        player.add_state("cast", [
            SpriteFrame("+", (200, 100, 255), (30, 20, 40), 0.15),
            SpriteFrame("*", (255, 150, 255), (40, 20, 50), 0.15),
            SpriteFrame("+", (200, 100, 255), (30, 20, 40), 0.15),
        ])

        self.sprites["player"] = player

        # Enemy sprites
        enemies = {
            "Ash Wraith": [
                ("idle", [("W", (180, 60, 20), (30, 10, 5), 0.3), ("w", (140, 50, 15), (25, 8, 4), 0.3)]),
                ("phased", [(".", (60, 60, 60), (10, 10, 10), 0.5)]),
                ("attack", [("W", (255, 80, 30), (40, 15, 10), 0.1), ("*", (255, 120, 50), (50, 20, 15), 0.1)]),
            ],
            "Ferro Drone": [
                ("idle", [("D", (150, 150, 160), (40, 40, 45), 0.3), ("d", (130, 130, 140), (35, 35, 40), 0.3)]),
                ("patrol", [(">", (150, 150, 160), (40, 40, 45), 0.2), ("-", (130, 130, 140), (35, 35, 40), 0.2)]),
                ("shield_burst", [("O", (200, 200, 255), (50, 50, 80), 0.1), ("0", (180, 180, 220), (45, 45, 70), 0.1)]),
            ],
            "Hollow Stalker": [
                ("idle", [("S", (80, 40, 100), (20, 10, 30), 0.4), ("s", (60, 30, 80), (15, 8, 25), 0.4)]),
                ("stealth", [(" ", (0, 0, 0), (0, 0, 0), 0.5)]),
                ("ambush", [("S", (255, 50, 50), (50, 10, 20), 0.1), ("!", (255, 100, 100), (60, 20, 30), 0.1)]),
            ],
            "Tide Leviathan": [
                ("idle", [("L", (50, 100, 200), (10, 20, 40), 0.3), ("l", (40, 80, 180), (8, 16, 35), 0.3)]),
                ("pulse", [("O", (100, 150, 255), (30, 40, 80), 0.1), ("0", (80, 120, 220), (25, 35, 70), 0.1)]),
            ],
            "Chorus Hymnal": [
                ("idle", [("H", (180, 100, 200), (40, 20, 50), 0.3), ("h", (160, 80, 180), (35, 18, 45), 0.3)]),
                ("buffing", [("+", (200, 150, 255), (50, 30, 70), 0.15), ("*", (220, 180, 255), (60, 40, 80), 0.15)]),
            ],
            "Salt Scarab": [
                ("idle", [("B", (200, 180, 140), (50, 40, 30), 0.2), ("b", (180, 160, 120), (45, 35, 25), 0.2)]),
                ("swarm", [("B", (220, 200, 160), (60, 50, 40), 0.1), ("*", (240, 220, 180), (70, 60, 50), 0.1)]),
            ],
        }

        for name, states in enemies.items():
            sprite = AnimatedSprite(name)
            for state_name, frame_data in states:
                frames = [SpriteFrame(c, fg, bg, d) for c, fg, bg, d in frame_data]
                sprite.add_state(state_name, frames)
            self.sprites[name] = sprite

        # NPC sprites
        npc_types = {
            "merchant": [("$", (255, 215, 0), (40, 35, 20), 0.4), ("$", (230, 195, 0), (35, 30, 18), 0.4)],
            "guard": [("G", (150, 150, 160), (30, 30, 35), 0.4), ("G", (130, 130, 140), (25, 25, 30), 0.4)],
            "sage": [("?", (200, 150, 255), (40, 30, 50), 0.5), ("?", (180, 130, 230), (35, 25, 45), 0.5)],
            "companion": [("C", (100, 255, 100), (20, 40, 20), 0.3), ("C", (80, 230, 80), (18, 35, 18), 0.3)],
        }

        for name, frames_data in npc_types.items():
            sprite = AnimatedSprite(name)
            frames = [SpriteFrame(c, fg, bg, d) for c, fg, bg, d in frames_data]
            sprite.add_state("idle", frames)
            sprite.add_state("talk", [
                SpriteFrame("!", (255, 255, 100), (40, 40, 20), 0.2),
                SpriteFrame("?", (255, 255, 150), (40, 40, 25), 0.2),
            ] + frames)
            self.sprites[name] = sprite

    def get_sprite(self, name):
        return self.sprites.get(name)

    def update_all(self, dt):
        for sprite in self.sprites.values():
            sprite.update(dt)


# Pre-built atlas instance
ATLAS = SpriteAtlas()
