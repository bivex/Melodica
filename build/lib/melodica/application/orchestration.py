from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict

from melodica.types import Track, NoteInfo

@dataclass
class InstrumentProfile:
    name: str
    min_pitch: int
    max_pitch: int
    default_pan: int           # CC 10: 0=L, 64=C, 127=R
    default_volume: int        # CC 7:  0-127
    spectral_priority: int     # 0-100 (velocity scaling weight)
    default_reverb: int = 40   # CC 91: hall reverb send
    default_chorus: int = 0    # CC 93: chorus send
    default_attack: int = 64   # CC 73: envelope attack (64=neutral; lower=faster)
    default_release: int = 64  # CC 72: envelope release (64=neutral; higher=longer)
    default_brightness: int = 64  # CC 74: filter brightness (64=neutral; higher=brighter)
    default_cc1: int = 64         # CC 1:  initial dynamic layer (sample library layer select)
    sweet_spot: tuple[int, int] = (0, 127)  # optimal MIDI range — tonal "comfort zone"
    spectral_centroid: float = 1000.0       # approximate tonal centre in Hz (used for zone analysis)


# Standard Orchestral Placement — concert hall seating + envelope characteristics
#
# Pan layout (front view of orchestra):
#   Violins I: far left (20), Violins II: center-left (40)
#   Viola: center-right (88), Cello: right of center (80), CB: center (58)
#   Woodwinds: center cluster, Brass: right side
#   Harp: far left (30), Timpani: center back (64)
#
# Attack/Release encode the instrument's natural envelope:
#   Fast attack = plucked/struck (harp=35, timpani=40)
#   Slow attack = bowed/blown sustained (strings=64, brass=68-70)
#   Long release = resonating body (harp=90, cello=74)
#   Short release = damped/clipped (trumpet=55, flute=60)
#
# Brightness encodes natural spectral character:
#   Bright (high CC74): Flute(80), Trumpet(90), Oboe(75)
#   Dark  (low  CC74):  Contrabass(50), Cello(55), Horn(58)

ORCHESTRAL_PROFILES = {
    # key             display name    lo  hi   pan  vol  pri  rev  cho  atk  rel  bri  cc1
    "Violins_I":  InstrumentProfile("Violins I",   64, 100, 20, 100, 90,  72,  0,  64, 68, 68, 75,
                                    sweet_spot=(64, 96),  spectral_centroid=2000.0),
    "Violins_II": InstrumentProfile("Violins II",  55,  90, 40,  85, 80,  68,  0,  64, 68, 65, 65,
                                    sweet_spot=(62, 91),  spectral_centroid=1800.0),
    "Viola":      InstrumentProfile("Viola",       48,  80, 88,  85, 75,  65,  0,  66, 70, 58, 65,
                                    sweet_spot=(55, 80),  spectral_centroid=900.0),
    "Cello":      InstrumentProfile("Cello",       36,  64, 80,  95, 85,  70,  0,  66, 74, 55, 70,
                                    sweet_spot=(40, 67),  spectral_centroid=400.0),
    "Contrabass": InstrumentProfile("Contrabass",  24,  48, 58, 110, 90,  60,  0,  68, 76, 50, 60,
                                    sweet_spot=(28, 52),  spectral_centroid=160.0),
    "Flute":      InstrumentProfile("Flute",       60,  96, 54,  95, 85,  55,  0,  58, 60, 80, 70,
                                    sweet_spot=(65, 96),  spectral_centroid=2200.0),
    "Oboe":       InstrumentProfile("Oboe",        58,  91, 74,  95, 85,  50,  0,  60, 62, 75, 72,
                                    sweet_spot=(60, 88),  spectral_centroid=1400.0),
    "Horn":       InstrumentProfile("Horn",        36,  72, 45, 100, 80,  48,  0,  70, 65, 58, 65,
                                    sweet_spot=(40, 70),  spectral_centroid=600.0),
    "Trumpet":    InstrumentProfile("Trumpet",     55,  82, 82, 105, 90,  40,  0,  65, 55, 90, 80,
                                    sweet_spot=(55, 80),  spectral_centroid=1800.0),
    "Trombone":   InstrumentProfile("Trombone",    40,  72, 68, 100, 85,  45,  0,  68, 62, 70, 68,
                                    sweet_spot=(40, 69),  spectral_centroid=500.0),
    "Timpani":    InstrumentProfile("Timpani",     36,  48, 64, 120, 100, 75,  0,  40, 82, 64, 85,
                                    sweet_spot=(41, 48),  spectral_centroid=150.0),
    "Harp":       InstrumentProfile("Harp",        40,  96, 30,  80, 70,  52,  8,  35, 90, 74, 55,
                                    sweet_spot=(43, 95),  spectral_centroid=700.0),
}

class OrchestralBalancer:
    """
    Applies mix settings from ORCHESTRAL_PROFILES: pan, volume, reverb, envelope.

    Each setting maps 1:1 to a Track field — no hidden math.
    Octave shifting and velocity scaling are available as separate explicit methods.
    """

    @staticmethod
    def apply_balancing(tracks: List[Track]) -> List[Track]:
        """Apply spatial, volume, reverb, envelope, and CC1 settings."""
        for track in tracks:
            profile = ORCHESTRAL_PROFILES.get(track.name)
            if not profile:
                continue

            track.pan = profile.default_pan
            track.volume = profile.default_volume
            track.expression = 127   # full headroom for CC11 automation
            track.attack = profile.default_attack
            track.release = profile.default_release
            track.brightness = profile.default_brightness
            track.reverb = profile.default_reverb
            track.chorus = profile.default_chorus
            track.modulation = profile.default_cc1
            track.instrument_name = profile.name

        return tracks

    @staticmethod
    def shift_octaves_into_range(tracks: List[Track]) -> List[Track]:
        """
        Shift notes by octaves so the average pitch fits the instrument's range.
        Only call this if you actually want octave correction.
        Returns the modified tracks.
        """
        for track in tracks:
            profile = ORCHESTRAL_PROFILES.get(track.name)
            if not profile or not track.notes:
                continue

            avg_pitch = sum(n.pitch for n in track.notes) / len(track.notes)

            shift = 0
            if avg_pitch < profile.min_pitch:
                shift = 12 * ((profile.min_pitch - int(avg_pitch)) // 12 + 1)
            elif avg_pitch > profile.max_pitch:
                shift = -12 * ((int(avg_pitch) - profile.max_pitch) // 12 + 1)

            if shift != 0:
                for n in track.notes:
                    n.pitch += shift

        return tracks

    @staticmethod
    def scale_velocities(tracks: List[Track], boost: float = 1.0) -> List[Track]:
        """
        Scale velocities by spectral_priority × boost.
        boost=1.0 means no extra boost; 1.2 = +20% on top of priority scaling.
        Only call this if you want velocity normalization.
        """
        for track in tracks:
            profile = ORCHESTRAL_PROFILES.get(track.name)
            if not profile or not track.notes:
                continue

            factor = (profile.spectral_priority / 100.0) * boost
            for n in track.notes:
                n.velocity = min(127, int(n.velocity * factor))

        return tracks
