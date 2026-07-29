"""
Halcyon Expanse — 2D Top-Down Renderer
Pygame-like rendering using matplotlib for frame export, with real ASCII fallback.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

TILE_SIZE = 32

# Color palette for entities
ENTITY_COLORS = {
    "player": (0, 200, 255),
    "enemy": (255, 60, 60),
    "npc": (200, 200, 100),
    "item": (255, 215, 0),
    "seam_gate": (200, 180, 100),
}

# Entity sprites (simple shapes drawn with PIL)
ENTITY_SPRITES = {
    "player": "circle",
    "enemy": "diamond",
    "npc": "square",
    "item": "star",
    "seam_gate": "hexagon",
}


class Renderer2D:
    """2D top-down tile renderer with PIL."""
    def __init__(self, tile_size=TILE_SIZE):
        self.tile_size = tile_size
        self.font = None
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
        except:
            self.font = ImageFont.load_default()

    def render_frame(self, tilemap, entities, viewport_width=20, viewport_height=15,
                     camera_x=0, camera_y=0, output_path=None):
        """Render a single frame as PNG."""
        w = viewport_width * self.tile_size
        h = viewport_height * self.tile_size
        img = Image.new("RGB", (w, h), (10, 10, 15))
        draw = ImageDraw.Draw(img)

        # Calculate viewport bounds
        start_x = max(0, camera_x - viewport_width // 2)
        start_y = max(0, camera_y - viewport_height // 2)
        end_x = min(tilemap.width, start_x + viewport_width)
        end_y = min(tilemap.height, start_y + viewport_height)

        # Update lighting
        player = next((e for e in entities if getattr(e, 'kind', '') == 'player'), None)
        if player:
            tilemap.update_lighting(int(player.x), int(player.y))

        # Render tiles
        from engine2d.tilemap import TILE_TYPES
        for ty in range(start_y, end_y):
            for tx in range(start_x, end_x):
                tile_name = tilemap.tiles[ty][tx]
                tile_info = TILE_TYPES.get(tile_name, TILE_TYPES["floor"])

                # Apply lighting
                light = tilemap.lighting[ty][tx]
                color = tuple(int(c * light) for c in tile_info["color"])

                px = (tx - start_x) * self.tile_size
                py = (ty - start_y) * self.tile_size

                draw.rectangle([px, py, px + self.tile_size - 1, py + self.tile_size - 1], fill=color)

                # Draw tile char
                char = tile_info["char"]
                if light > 0.2:
                    text_color = (255, 255, 255) if light > 0.5 else (150, 150, 150)
                    draw.text((px + 10, py + 8), char, fill=text_color, font=self.font)

                # Glow effect for special tiles
                if tile_info.get("glow") and light > 0.3:
                    glow = (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40))
                    draw.rectangle([px, py, px + 2, py + 2], fill=glow)

        # Render entities
        for entity in entities:
            ex, ey = int(entity.x), int(entity.y)
            if start_x <= ex < end_x and start_y <= ey < end_y:
                px = (ex - start_x) * self.tile_size + self.tile_size // 2
                py = (ey - start_y) * self.tile_size + self.tile_size // 2

                kind = getattr(entity, 'kind', 'generic')
                color = ENTITY_COLORS.get(kind, (200, 200, 200))
                light = tilemap.lighting[ey][ex] if ey < tilemap.height and ex < tilemap.width else 1.0
                color = tuple(int(c * light) for c in color)

                sprite = ENTITY_SPRITES.get(kind, "circle")
                r = self.tile_size // 3

                if sprite == "circle":
                    draw.ellipse([px-r, py-r, px+r, py+r], fill=color, outline=(255,255,255))
                elif sprite == "diamond":
                    draw.polygon([(px, py-r), (px+r, py), (px, py+r), (px-r, py)], fill=color, outline=(255,255,255))
                elif sprite == "square":
                    draw.rectangle([px-r, py-r, px+r, py+r], fill=color, outline=(255,255,255))
                elif sprite == "star":
                    draw.polygon([(px, py-r), (px+r//2, py-r//3), (px+r, py), (px+r//2, py+r//3), (px, py+r), (px-r//2, py+r//3), (px-r, py), (px-r//2, py-r//3)], fill=color)
                elif sprite == "hexagon":
                    draw.polygon([(px, py-r), (px+r*0.87, py-r*0.5), (px+r*0.87, py+r*0.5), (px, py+r), (px-r*0.87, py+r*0.5), (px-r*0.87, py-r*0.5)], fill=color, outline=(255,255,255))

                # HP bar for enemies
                if kind == "enemy" and hasattr(entity, 'hp') and hasattr(entity, 'max_hp'):
                    hp_pct = entity.hp / entity.max_hp
                    bar_w = self.tile_size - 4
                    bar_h = 3
                    bar_x = px - bar_w // 2
                    bar_y = py - r - 6
                    draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(60, 60, 60))
                    draw.rectangle([bar_x, bar_y, bar_x + int(bar_w * hp_pct), bar_y + bar_h], fill=(255, 60, 60))

        # UI overlay
        self._draw_ui(draw, img.width, img.height, entities, tilemap)

        if output_path:
            img.save(output_path)
        return img

    def _draw_ui(self, draw, w, h, entities, tilemap):
        """Draw HUD overlay."""
        player = next((e for e in entities if getattr(e, 'kind', '') == 'player'), None)
        if not player:
            return

        # Top bar - system info
        from halcyon.actor import Actor
        if isinstance(player, Actor):
            info = f"{player.resonance_type} | Attunement {player.attunement_level} | Year 706"
            draw.rectangle([0, 0, w, 28], fill=(20, 20, 30, 180))
            draw.text((10, 5), info, fill=(200, 200, 200))

            # LC bar
            lc_pct = player.lattice_charge / player.lattice_charge_max if player.lattice_charge_max > 0 else 0
            bar_w = 200
            bar_h = 12
            bar_x = w - bar_w - 10
            bar_y = 8
            draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(40, 40, 60))
            lc_color = (0, 200, 255) if lc_pct > 0.3 else (255, 100, 0)
            draw.rectangle([bar_x, bar_y, bar_x + int(bar_w * lc_pct), bar_y + bar_h], fill=lc_color)
            draw.text((bar_x, bar_y - 14), f"LC: {player.lattice_charge:.0f}/{player.lattice_charge_max:.0f}", fill=(200, 200, 200))

            # Debt indicator
            if player.lattice_debt > 0:
                draw.text((bar_x, bar_y + 16), f"Debt: {player.lattice_debt:.2f}", fill=(255, 100, 100))

        # Bottom bar - controls
        controls = "WASD/Arrows: Move | SPACE: Attack | E: Interact | Q: Quit"
        draw.rectangle([0, h - 24, w, h], fill=(20, 20, 30, 180))
        draw.text((10, h - 20), controls, fill=(150, 150, 150))

    def render_ascii(self, tilemap, entities, viewport_width=40, viewport_height=20,
                     camera_x=0, camera_y=0):
        """ASCII fallback renderer."""
        from engine2d.tilemap import TILE_TYPES

        start_x = max(0, camera_x - viewport_width // 2)
        start_y = max(0, camera_y - viewport_height // 2)
        end_x = min(tilemap.width, start_x + viewport_width)
        end_y = min(tilemap.height, start_y + viewport_height)

        lines = []
        for ty in range(start_y, end_y):
            row = []
            for tx in range(start_x, end_x):
                # Check for entity
                entity_here = None
                for e in entities:
                    if int(e.x) == tx and int(e.y) == ty:
                        entity_here = e
                        break

                if entity_here:
                    kind = getattr(entity_here, 'kind', '?')
                    if kind == 'player':
                        row.append('@')
                    elif kind == 'enemy':
                        row.append('E')
                    elif kind == 'npc':
                        row.append('N')
                    else:
                        row.append('?')
                else:
                    tile_name = tilemap.tiles[ty][tx]
                    tile_info = TILE_TYPES.get(tile_name, TILE_TYPES["floor"])
                    row.append(tile_info["char"])
            lines.append(''.join(row))
        return '\n'.join(lines)
