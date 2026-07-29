"""
Halcyon Expanse — Lighting Engine
Dynamic lighting with torch flicker, bioluminescence, spell glow, ambient occlusion.
"""
import math
import random


class LightSource:
    """A point light source in the world."""
    def __init__(self, x, y, radius, color, intensity=1.0, flicker=False):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color  # (r, g, b)
        self.intensity = intensity
        self.flicker = flicker
        self.flicker_timer = 0.0
        self.base_intensity = intensity

    def update(self, dt):
        if self.flicker:
            self.flicker_timer += dt
            # Torch flicker: random intensity variation
            noise = math.sin(self.flicker_timer * 10) * 0.1 + random.uniform(-0.05, 0.05)
            self.intensity = max(0.3, min(1.5, self.base_intensity + noise))

    def get_intensity_at(self, tx, ty):
        """Get light intensity at a given tile position."""
        dist = math.sqrt((tx - self.x)**2 + (ty - self.y)**2)
        if dist > self.radius:
            return 0.0
        # Smooth falloff
        falloff = 1.0 - (dist / self.radius) ** 2
        return falloff * self.intensity


class LightingEngine:
    """Manages all lighting in the game world."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.lights = []
        self.ambient_light = 0.1  # Base ambient (0-1)
        self.light_map = [[self.ambient_light for _ in range(width)] for _ in range(height)]
        self.color_map = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]

    def add_light(self, x, y, radius, color, intensity=1.0, flicker=False):
        light = LightSource(x, y, radius, color, intensity, flicker)
        self.lights.append(light)
        return light

    def remove_light(self, light):
        if light in self.lights:
            self.lights.remove(light)

    def clear_lights(self):
        self.lights = []

    def set_ambient(self, level):
        """Set ambient light level (0-1)."""
        self.ambient_light = max(0, min(1, level))

    def update(self, dt, player_x, player_y):
        """Update light map based on all light sources."""
        # Update flickering lights
        for light in self.lights:
            light.update(dt)

        # Player always has a light
        player_light = None
        for light in self.lights:
            if abs(light.x - player_x) < 0.5 and abs(light.y - player_y) < 0.5:
                player_light = light
                break

        if not player_light:
            self.add_light(player_x, player_y, 8, (255, 240, 200), 1.0, True)
        else:
            player_light.x = player_x
            player_light.y = player_y

        # Recalculate light map
        for y in range(self.height):
            for x in range(self.width):
                total_intensity = self.ambient_light
                total_color = [0, 0, 0]

                for light in self.lights:
                    intensity = light.get_intensity_at(x, y)
                    if intensity > 0:
                        total_intensity += intensity
                        for i in range(3):
                            total_color[i] += light.color[i] * intensity

                total_intensity = min(1.0, total_intensity)
                self.light_map[y][x] = total_intensity

                # Normalize color
                if total_intensity > 0:
                    self.color_map[y][x] = tuple(
                        min(255, int(c / total_intensity)) for c in total_color
                    )
                else:
                    self.color_map[y][x] = (0, 0, 0)

    def get_light_level(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.light_map[y][x]
        return 0.0

    def get_light_color(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.color_map[y][x]
        return (0, 0, 0)

    def apply_to_tile(self, tile_color, x, y):
        """Apply lighting to a tile color."""
        light_level = self.get_light_level(x, y)
        light_color = self.get_light_color(x, y)

        if light_level <= 0:
            return (0, 0, 0)

        # Multiply tile color by light
        result = []
        for i in range(3):
            # Mix ambient white with colored light
            mixed_light = int(255 * light_level * 0.7 + light_color[i] * light_level * 0.3)
            result.append(min(255, int(tile_color[i] * light_level * (mixed_light / 255))))

        return tuple(result)
