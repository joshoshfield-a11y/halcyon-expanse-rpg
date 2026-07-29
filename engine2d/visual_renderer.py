"""
Halcyon Expanse — Visual Renderer v2
Sprite-based rendering with animations, particles, dynamic lighting, and UI.
Uses matplotlib for frame output (no pygame dependency).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import math
import random

from engine2d.sprite_atlas import ATLAS, SpriteFrame
from engine2d.particles import ParticleSystem
from engine2d.lighting_engine import LightingEngine


class VisualRenderer:
    """Advanced 2D renderer with sprites, particles, lighting, and UI."""

    TILE_SIZE = 24  # pixels per tile

    # Enhanced tile colors
    TILE_COLORS = {
        "floor": (40, 40, 40),
        "wall": (80, 80, 80),
        "water": (30, 60, 90),
        "lava": (180, 60, 20),
        "grass": (34, 85, 51),
        "sand": (194, 178, 128),
        "snow": (220, 220, 230),
        "swamp": (45, 65, 35),
        "crystal": (120, 80, 160),
        "ash": (60, 55, 50),
        "iron_floor": (70, 75, 80),
        "void": (10, 10, 15),
        "seam_gate": (200, 180, 100),
    }

    # Tile height variations for pseudo-3D
    TILE_HEIGHT = {
        "wall": 0.3,
        "water": -0.1,
        "lava": -0.05,
        "crystal": 0.1,
        "seam_gate": 0.2,
    }

    def __init__(self, tile_size=TILE_SIZE):
        self.tile_size = tile_size
        self.particles = ParticleSystem()
        self.lighting = None
        self.frame_count = 0
        self.damage_numbers = []  # [(x, y, text, color, timer)]
        self.screen_shake = 0.0
        self.shake_intensity = 0.0

    def render_frame(self, tilemap, entities, player, camera_x, camera_y,
                     viewport_width=30, viewport_height=22, output_path=None,
                     show_ui=True, show_minimap=True):
        """Render a complete game frame with all effects."""

        w = viewport_width * self.tile_size
        h = viewport_height * self.tile_size

        # Screen shake
        shake_x = random.uniform(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        shake_y = random.uniform(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        self.screen_shake = max(0, self.screen_shake - 0.5)

        fig, ax = plt.subplots(figsize=(w/72, h/72), dpi=72)
        fig.patch.set_facecolor((0.02, 0.02, 0.03))
        ax.set_facecolor((0.02, 0.02, 0.03))

        # Calculate viewport
        start_x = max(0, int(camera_x - viewport_width // 2))
        start_y = max(0, int(camera_y - viewport_height // 2))
        end_x = min(tilemap.width, start_x + viewport_width)
        end_y = min(tilemap.height, start_y + viewport_height)

        # Initialize lighting if needed
        if self.lighting is None or self.lighting.width != tilemap.width:
            self.lighting = LightingEngine(tilemap.width, tilemap.height)

        # Update lighting
        self.lighting.update(0.016, player.x, player.y)

        # Add environmental lights
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile_name = tilemap.tiles[y][x]
                if tile_name == "lava":
                    self.lighting.add_light(x + 0.5, y + 0.5, 3, (255, 80, 20), 0.6, True)
                elif tile_name == "crystal":
                    self.lighting.add_light(x + 0.5, y + 0.5, 2, (180, 100, 255), 0.4, True)
                elif tile_name == "seam_gate":
                    self.lighting.add_light(x + 0.5, y + 0.5, 4, (200, 180, 100), 0.8, True)

        # Render tiles (bottom to top for pseudo-3D)
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile_name = tilemap.tiles[y][x]
                base_color = self.TILE_COLORS.get(tile_name, (40, 40, 40))

                # Apply lighting
                lit_color = self.lighting.apply_to_tile(base_color, x, y)

                # Convert to 0-1 range for matplotlib
                color_norm = tuple(c / 255.0 for c in lit_color)

                px = (x - start_x) * self.tile_size + shake_x
                py = (viewport_height - (y - start_y) - 1) * self.tile_size + shake_y

                # Height offset for pseudo-3D
                height_offset = self.TILE_HEIGHT.get(tile_name, 0) * self.tile_size * 0.5

                # Draw tile
                rect = patches.Rectangle(
                    (px, py + height_offset), 
                    self.tile_size - 1, self.tile_size - 1,
                    facecolor=color_norm,
                    edgecolor=(0, 0, 0, 0.3),
                    linewidth=0.5
                )
                ax.add_patch(rect)

                # Draw height side for walls (pseudo-3D)
                if tile_name == "wall":
                    side_color = tuple(max(0, c - 0.15) for c in color_norm)
                    side_rect = patches.Rectangle(
                        (px, py), self.tile_size - 1, height_offset * 2,
                        facecolor=side_color,
                        edgecolor='none'
                    )
                    ax.add_patch(side_rect)

                # Water shimmer effect
                if tile_name == "water":
                    shimmer = random.random() * 0.1
                    shimmer_rect = patches.Rectangle(
                        (px + 2, py + 2), self.tile_size - 5, self.tile_size - 5,
                        facecolor=(0.2 + shimmer, 0.4 + shimmer, 0.6 + shimmer, 0.3),
                        edgecolor='none'
                    )
                    ax.add_patch(shimmer_rect)

                # Lava glow
                if tile_name == "lava":
                    glow = random.random() * 0.2
                    glow_rect = patches.Rectangle(
                        (px + 3, py + 3), self.tile_size - 7, self.tile_size - 7,
                        facecolor=(0.8 + glow, 0.3 + glow, 0.1, 0.4),
                        edgecolor='none'
                    )
                    ax.add_patch(glow_rect)

        # Update and render particles
        self.particles.update(0.016)
        for p in self.particles.particles:
            if p.alive:
                px = (p.x - start_x) * self.tile_size + shake_x
                py = (viewport_height - (p.y - start_y) - 1) * self.tile_size + shake_y
                alpha = p.get_alpha()
                size = p.get_size()
                color_norm = tuple(c / 255.0 for c in p.color) + (alpha,)

                if size > 0:
                    circle = patches.Circle(
                        (px + self.tile_size/2, py + self.tile_size/2),
                        size,
                        facecolor=color_norm,
                        edgecolor='none'
                    )
                    ax.add_patch(circle)

        # Render entities with sprites
        for entity in entities:
            ex = entity.x
            ey = entity.y
            if start_x <= ex < end_x and start_y <= ey < end_y:
                px = (ex - start_x) * self.tile_size + self.tile_size/2 + shake_x
                py = (viewport_height - (ey - start_y) - 1) * self.tile_size + self.tile_size/2 + shake_y

                # Get sprite
                sprite_name = getattr(entity, 'kind', 'generic')
                if sprite_name == 'player':
                    sprite_name = 'player'
                elif hasattr(entity, 'name'):
                    sprite_name = entity.name

                sprite = ATLAS.get_sprite(sprite_name)
                if sprite:
                    # Determine state
                    if hasattr(entity, 'behavior_pattern'):
                        sprite.set_state(entity.state)
                    elif sprite_name == 'player':
                        # Set based on player action
                        pass

                    frame = sprite.get_current_frame()
                    fg = tuple(c / 255.0 for c in frame.fg_color)
                    bg = tuple(c / 255.0 for c in frame.bg_color)

                    # Draw sprite background
                    bg_rect = patches.Rectangle(
                        (px - 8, py - 8), 16, 16,
                        facecolor=bg,
                        edgecolor='none'
                    )
                    ax.add_patch(bg_rect)

                    # Draw sprite character
                    ax.text(px, py, frame.char_glyph, 
                           fontsize=14, color=fg, ha='center', va='center',
                           fontweight='bold')
                else:
                    # Fallback
                    color = (0, 0.8, 1) if sprite_name == 'player' else (1, 0.2, 0.2)
                    circle = patches.Circle((px, py), 6, facecolor=color, edgecolor='white', linewidth=1)
                    ax.add_patch(circle)

                # HP bar for enemies
                if hasattr(entity, 'hp') and hasattr(entity, 'max_hp') and sprite_name != 'player':
                    hp_pct = entity.hp / entity.max_hp
                    bar_w = 20
                    bar_h = 3
                    bar_x = px - bar_w/2
                    bar_y = py - 12

                    ax.add_patch(patches.Rectangle((bar_x, bar_y), bar_w, bar_h, 
                                  facecolor=(0.2, 0.2, 0.2), edgecolor='none'))
                    ax.add_patch(patches.Rectangle((bar_x, bar_y), bar_w * hp_pct, bar_h,
                                  facecolor=(0.8, 0.2, 0.2), edgecolor='none'))

                # LC bar for player
                if sprite_name == 'player' and hasattr(entity, 'lattice_charge'):
                    lc_pct = entity.lattice_charge / entity.lattice_charge_max if entity.lattice_charge_max > 0 else 0
                    bar_w = 24
                    bar_h = 3
                    bar_x = px - bar_w/2
                    bar_y = py + 10

                    ax.add_patch(patches.Rectangle((bar_x, bar_y), bar_w, bar_h,
                                  facecolor=(0.1, 0.1, 0.2), edgecolor='none'))
                    lc_color = (0, 0.8, 1) if lc_pct > 0.3 else (1, 0.4, 0)
                    ax.add_patch(patches.Rectangle((bar_x, bar_y), bar_w * lc_pct, bar_h,
                                  facecolor=lc_color, edgecolor='none'))

        # Render damage numbers
        new_damage_numbers = []
        for dx, dy, text, color, timer in self.damage_numbers:
            if timer > 0:
                px = (dx - start_x) * self.tile_size + self.tile_size/2 + shake_x
                py = (viewport_height - (dy - start_y) - 1) * self.tile_size + shake_y - (1.0 - timer) * 20
                alpha = min(1, timer)
                color_norm = tuple(c / 255.0 for c in color) + (alpha,)
                ax.text(px, py, text, fontsize=10, color=color_norm, 
                       ha='center', va='center', fontweight='bold')
                new_damage_numbers.append((dx, dy, text, color, timer - 0.016))
        self.damage_numbers = new_damage_numbers

        # UI Overlay
        if show_ui:
            self._draw_ui(ax, w, h, player, entities, tilemap)

        # Minimap
        if show_minimap:
            self._draw_minimap(ax, tilemap, player, entities, w, h)

        ax.set_xlim(0, w)
        ax.set_ylim(0, h)
        ax.set_aspect('equal')
        ax.axis('off')

        plt.tight_layout(pad=0)

        if output_path:
            fig.savefig(output_path, facecolor=(0.02, 0.02, 0.03), 
                       dpi=72, bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            return output_path

        plt.close(fig)
        return None

    def _draw_ui(self, ax, w, h, player, entities, tilemap):
        """Draw UI overlay."""
        # Top bar background
        ui_bg = patches.Rectangle((0, h-35), w, 35, 
                                 facecolor=(0.05, 0.05, 0.08, 0.9),
                                 edgecolor='none')
        ax.add_patch(ui_bg)

        # Resonance and attunement
        if hasattr(player, 'resonance_type'):
            ax.text(10, h-18, f"{player.resonance_type} | Attunement {player.attunement_level}",
                   fontsize=9, color=(0.8, 0.8, 0.8), ha='left', va='center')

        # HP bar
        if hasattr(player, 'hp'):
            hp_pct = player.hp / 100.0
            ax.add_patch(patches.Rectangle((w-210, h-28), 200, 14,
                          facecolor=(0.2, 0.1, 0.1), edgecolor=(0.5, 0.5, 0.5), linewidth=1))
            ax.add_patch(patches.Rectangle((w-210, h-28), 200 * hp_pct, 14,
                          facecolor=(0.8, 0.2, 0.2), edgecolor='none'))
            ax.text(w-110, h-21, f"HP {player.hp}/100", fontsize=8, 
                   color=(1, 1, 1), ha='center', va='center', fontweight='bold')

        # LC bar
        if hasattr(player, 'lattice_charge'):
            lc_pct = player.lattice_charge / player.lattice_charge_max if player.lattice_charge_max > 0 else 0
            ax.add_patch(patches.Rectangle((w-210, h-45), 200, 10,
                          facecolor=(0.1, 0.1, 0.2), edgecolor=(0.3, 0.3, 0.5), linewidth=1))
            lc_color = (0, 0.7, 1) if lc_pct > 0.3 else (1, 0.5, 0)
            ax.add_patch(patches.Rectangle((w-210, h-45), 200 * lc_pct, 10,
                          facecolor=lc_color, edgecolor='none'))
            ax.text(w-110, h-40, f"LC {player.lattice_charge:.0f}/{player.lattice_charge_max:.0f}",
                   fontsize=7, color=(1, 1, 1), ha='center', va='center')

        # Bottom bar
        ui_bg_bottom = patches.Rectangle((0, 0), w, 25,
                                        facecolor=(0.05, 0.05, 0.08, 0.9),
                                        edgecolor='none')
        ax.add_patch(ui_bg_bottom)

        # Controls hint
        ax.text(w/2, 12, "WASD: Move | SPACE: Attack | 1-7: Abilities | E: Interact | I: Inv | C: Codex | Q: Quit",
               fontsize=7, color=(0.6, 0.6, 0.6), ha='center', va='center')

        # System info
        system_text = f"System: {tilemap.biome} | Year: 706 | Enemies: {len([e for e in entities if getattr(e, 'kind', '') == 'enemy'])}"
        ax.text(10, 12, system_text, fontsize=7, color=(0.6, 0.6, 0.6), ha='left', va='center')

    def _draw_minimap(self, ax, tilemap, player, entities, w, h):
        """Draw minimap in corner."""
        mm_size = 80
        mm_x = w - mm_size - 10
        mm_y = h - mm_size - 50

        # Minimap background
        ax.add_patch(patches.Rectangle((mm_x, mm_y), mm_size, mm_size,
                      facecolor=(0.05, 0.05, 0.08, 0.8),
                      edgecolor=(0.3, 0.3, 0.3), linewidth=1))

        # Scale
        scale_x = mm_size / tilemap.width
        scale_y = mm_size / tilemap.height

        # Draw explored tiles (simplified)
        for y in range(0, tilemap.height, 4):
            for x in range(0, tilemap.width, 4):
                tile = tilemap.tiles[y][x]
                if tile != "wall":
                    color = self.TILE_COLORS.get(tile, (40, 40, 40))
                    color_norm = tuple(c / 255.0 for c in color)
                    px = mm_x + x * scale_x
                    py = mm_y + y * scale_y
                    ax.add_patch(patches.Rectangle((px, py), scale_x * 4, scale_y * 4,
                                  facecolor=color_norm + (0.3,), edgecolor='none'))

        # Player dot
        px = mm_x + player.x * scale_x
        py = mm_y + player.y * scale_y
        ax.add_patch(patches.Circle((px, py), 3, facecolor=(0, 1, 1), edgecolor='white', linewidth=1))

        # Enemy dots
        for entity in entities:
            if getattr(entity, 'kind', '') == 'enemy':
                ex = mm_x + entity.x * scale_x
                ey = mm_y + entity.y * scale_y
                ax.add_patch(patches.Circle((ex, ey), 2, facecolor=(1, 0, 0), edgecolor='none'))

    def add_damage_number(self, x, y, text, color=(255, 50, 50)):
        """Add a floating damage number."""
        self.damage_numbers.append((x, y, text, color, 1.0))
        self.screen_shake = 3.0

    def add_screen_shake(self, intensity=5.0):
        """Trigger screen shake."""
        self.screen_shake = intensity
