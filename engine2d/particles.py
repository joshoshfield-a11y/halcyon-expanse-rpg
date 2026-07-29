"""
Halcyon Expanse — Particle System
Visual effects: explosions, spell casts, environmental effects, damage numbers.
"""
import random
import math


class Particle:
    """Single particle with physics."""
    def __init__(self, x, y, vx, vy, color, lifetime, size=2, gravity=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color  # (r, g, b)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.gravity = gravity
        self.alive = True

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def get_alpha(self):
        """Fade out over lifetime."""
        return max(0, self.lifetime / self.max_lifetime)

    def get_size(self):
        """Shrink over lifetime."""
        return max(1, self.size * (self.lifetime / self.max_lifetime))


class ParticleSystem:
    """Manages all particles in the game."""

    def __init__(self):
        self.particles = []
        self.emitters = []

    def emit(self, x, y, count=10, color=(255, 255, 255), speed=50, 
             lifetime=1.0, size=2, gravity=0, spread=6.28):
        """Emit a burst of particles."""
        for _ in range(count):
            angle = random.uniform(0, spread)
            spd = random.uniform(0.3, 1.0) * speed
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            p = Particle(x, y, vx, vy, color, random.uniform(lifetime * 0.5, lifetime), size, gravity)
            self.particles.append(p)

    def emit_explosion(self, x, y, color=(255, 100, 50), intensity=1.0):
        """Explosion effect."""
        count = int(20 * intensity)
        self.emit(x, y, count=count, color=color, speed=80, lifetime=0.8, 
                  size=3, gravity=20, spread=6.28)
        # Core flash
        self.emit(x, y, count=5, color=(255, 255, 200), speed=30, 
                  lifetime=0.3, size=4, gravity=0)

    def emit_spell_cast(self, x, y, resonance_type="Ember"):
        """Spell casting effect based on resonance."""
        colors = {
            "Ember": (255, 100, 50),
            "Gale": (150, 220, 255),
            "Hollow": (80, 40, 100),
            "Tide": (50, 150, 255),
            "Root": (50, 200, 80),
            "Iron": (180, 180, 200),
            "Chorus": (200, 100, 255),
        }
        color = colors.get(resonance_type, (255, 255, 255))
        self.emit(x, y, count=15, color=color, speed=60, lifetime=0.6, 
                  size=2, gravity=-10, spread=3.14)

    def emit_damage_number(self, x, y, amount, is_critical=False):
        """Floating damage number (rendered as text, not particle)."""
        color = (255, 50, 50) if not is_critical else (255, 200, 50)
        self.emit(x, y, count=1, color=color, speed=20, lifetime=1.0, 
                  size=0, gravity=-30)  # size=0 means text particle

    def emit_heal(self, x, y):
        """Healing effect."""
        self.emit(x, y, count=12, color=(100, 255, 150), speed=40, 
                  lifetime=0.8, size=2, gravity=-15, spread=3.14)

    def emit_environmental(self, x, y, biome="temperate"):
        """Ambient environmental particles."""
        effects = {
            "temperate": ((100, 255, 100), 2, 0.05),
            "volcanic": ((255, 80, 30), 3, 0.1),
            "ashfall": ((150, 140, 130), 2, 0.08),
            "low_light": ((80, 60, 100), 1, 0.03),
            "zero_g": ((200, 200, 255), 2, 0.0),
            "industrial": ((255, 150, 50), 2, 0.06),
            "acoustic": ((180, 100, 255), 2, 0.04),
            "desert": ((200, 180, 140), 2, 0.05),
            "twilight": ((150, 100, 200), 1, 0.03),
        }
        color, size, gravity = effects.get(biome, ((200, 200, 200), 2, 0.05))
        self.emit(x, y, count=3, color=color, speed=15, lifetime=2.0, 
                  size=size, gravity=gravity, spread=1.0)

    def emit_trail(self, x, y, color=(255, 255, 255), width=1):
        """Movement trail."""
        self.emit(x, y, count=2, color=color, speed=5, lifetime=0.3, 
                  size=width, gravity=0, spread=0.5)

    def update(self, dt):
        """Update all particles."""
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def clear(self):
        self.particles = []

    def get_active_count(self):
        return len(self.particles)
