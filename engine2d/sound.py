"""
Halcyon Expanse — Sound System
Procedural WAV generation for combat, spells, ambience. Pure Python, no deps.
"""
import struct
import math
import random
import wave
import io


class SoundGenerator:
    """Generates procedural sound effects as WAV data."""

    SAMPLE_RATE = 22050

    @staticmethod
    def generate_tone(frequency, duration, amplitude=0.5, fade=True):
        """Generate a pure tone."""
        samples = int(SoundGenerator.SAMPLE_RATE * duration)
        data = []
        for i in range(samples):
            t = i / SoundGenerator.SAMPLE_RATE
            val = math.sin(2 * math.pi * frequency * t) * amplitude
            if fade:
                val *= (1 - t / duration)  # Linear fade out
            data.append(int(val * 32767))
        return data

    @staticmethod
    def generate_noise(duration, amplitude=0.3):
        """Generate white noise."""
        samples = int(SoundGenerator.SAMPLE_RATE * duration)
        return [int((random.random() * 2 - 1) * amplitude * 32767) for _ in range(samples)]

    @staticmethod
    def generate_sweep(start_freq, end_freq, duration, amplitude=0.5):
        """Frequency sweep (useful for whoosh/slide effects)."""
        samples = int(SoundGenerator.SAMPLE_RATE * duration)
        data = []
        for i in range(samples):
            t = i / SoundGenerator.SAMPLE_RATE
            progress = t / duration
            freq = start_freq + (end_freq - start_freq) * progress
            val = math.sin(2 * math.pi * freq * t) * amplitude * (1 - progress)
            data.append(int(val * 32767))
        return data

    @staticmethod
    def generate_explosion():
        """Explosion sound: noise burst + low frequency decay."""
        noise = SoundGenerator.generate_noise(0.3, 0.8)
        rumble = SoundGenerator.generate_tone(80, 0.5, 0.6)
        # Mix
        mixed = []
        for i in range(max(len(noise), len(rumble))):
            n = noise[i] if i < len(noise) else 0
            r = rumble[i] if i < len(rumble) else 0
            mixed.append(min(32767, max(-32768, int(n * 0.7 + r * 0.3))))
        return mixed

    @staticmethod
    def generate_sword_hit():
        """Sword hit: high frequency noise burst."""
        return SoundGenerator.generate_noise(0.1, 0.4)

    @staticmethod
    def generate_spell_cast(resonance="Ember"):
        """Spell cast sound based on resonance."""
        frequencies = {
            "Ember": (400, 800),
            "Gale": (600, 1200),
            "Hollow": (150, 400),
            "Tide": (300, 600),
            "Root": (200, 500),
            "Iron": (100, 300),
            "Chorus": (500, 1000),
        }
        start, end = frequencies.get(resonance, (300, 600))
        return SoundGenerator.generate_sweep(start, end, 0.4, 0.4)

    @staticmethod
    def generate_heal():
        """Healing sound: ascending chime."""
        data = []
        for freq in [400, 500, 600, 800]:
            data.extend(SoundGenerator.generate_tone(freq, 0.15, 0.3))
        return data

    @staticmethod
    def generate_footstep():
        """Footstep: short low thud."""
        return SoundGenerator.generate_tone(150, 0.08, 0.2)

    @staticmethod
    def generate_boss_roar():
        """Boss roar: low frequency sweep + distortion."""
        sweep = SoundGenerator.generate_sweep(80, 40, 1.0, 0.7)
        noise = SoundGenerator.generate_noise(0.5, 0.2)
        mixed = []
        for i in range(max(len(sweep), len(noise))):
            s = sweep[i] if i < len(sweep) else 0
            n = noise[i] if i < len(noise) else 0
            mixed.append(min(32767, max(-32768, int(s * 0.8 + n * 0.2))))
        return mixed

    @staticmethod
    def generate_ambient(biome="temperate"):
        """Ambient background sound."""
        if biome in ["volcanic", "forge", "ashfall"]:
            return SoundGenerator.generate_noise(2.0, 0.1)  # Low rumble
        elif biome in ["riverine", "wetlands"]:
            return SoundGenerator.generate_noise(2.0, 0.05)  # Water flow
        elif biome in ["zero_g", "floating"]:
            return SoundGenerator.generate_tone(200, 2.0, 0.05)  # Deep drone
        else:
            return SoundGenerator.generate_noise(2.0, 0.03)  # Wind

    @staticmethod
    def to_wav_bytes(samples):
        """Convert samples to WAV bytes."""
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SoundGenerator.SAMPLE_RATE)
            for s in samples:
                wf.writeframes(struct.pack('<h', max(-32768, min(32767, s))))
        return buf.getvalue()

    @staticmethod
    def save_wav(samples, filepath):
        """Save samples to WAV file."""
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SoundGenerator.SAMPLE_RATE)
            for s in samples:
                wf.writeframes(struct.pack('<h', max(-32768, min(32767, s))))
        return filepath


class SoundManager:
    """Manages all game sounds."""

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.sounds = {}
        self._generate_all_sounds()

    def _generate_all_sounds(self):
        """Pre-generate all sound effects."""
        gen = SoundGenerator
        self.sounds = {
            "attack": gen.generate_sword_hit(),
            "hit": gen.generate_explosion(),
            "spell_ember": gen.generate_spell_cast("Ember"),
            "spell_gale": gen.generate_spell_cast("Gale"),
            "spell_hollow": gen.generate_spell_cast("Hollow"),
            "spell_tide": gen.generate_spell_cast("Tide"),
            "spell_root": gen.generate_spell_cast("Root"),
            "spell_iron": gen.generate_spell_cast("Iron"),
            "spell_chorus": gen.generate_spell_cast("Chorus"),
            "heal": gen.generate_heal(),
            "footstep": gen.generate_footstep(),
            "boss_roar": gen.generate_boss_roar(),
            "warp": gen.generate_sweep(200, 800, 0.5, 0.4),
            "level_up": gen.generate_sweep(400, 1200, 0.8, 0.5),
        }

    def play(self, sound_name):
        """Play a sound (returns WAV bytes for external playback)."""
        if not self.enabled:
            return None
        samples = self.sounds.get(sound_name)
        if samples:
            return SoundGenerator.to_wav_bytes(samples)
        return None

    def save_all(self, output_dir="sounds"):
        """Save all sounds to WAV files."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        for name, samples in self.sounds.items():
            path = os.path.join(output_dir, f"{name}.wav")
            SoundGenerator.save_wav(samples, path)
        return output_dir
