# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-22
# Last Updated: 2026-05-22
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
album_carina.py — "Carina EP".

A four-movement modern EP utilizing the new 2025 modern bass generator styles.
Scale: G Dorian (G=0, A=2, Bb=3, C=5, D=7, E=9, F=10) & G Mixolydian.
Root: G (7) — solid, rich bass foundation.

Movements:
  I.   Velvet Stars (Бархатные звезды)      — Neo Soul / Alt-R&B in G Dorian (velvet_soul bass)
  II.  Pulsar Dance (Пульсар)                — Syncopated Alt-Pop in G Dorian (hybrid_slap bass)
  III. Plucked Nebula (Туманность)           — Dark Disco / Atmospheric House in G Mixolydian (analog_pluck bass)
  IV.  Gravity Return (Притяжение)           — Cinematic Electronica in G Dorian (crescendo_return bass)
"""

import random
from pathlib import Path

from melodica import types
from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.modern_bass_2025 import ModernBass2025Generator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.composer.transformers import spiceup, serialize_canon, Identity, OneToThree
from melodica.harmonize.predictive import PredictiveHarmonizer
from melodica.rhythm.groove_template import SWING_60, LAID_BACK

# G Dorian (G, A, Bb, C, D, E, F)
KEY_DORIAN = Scale(root=7, mode=Mode.DORIAN)
# G Mixolydian (G, A, B, C, D, E, F)
KEY_MIXOLYDIAN = Scale(root=7, mode=Mode.MIXOLYDIAN)


def _build_chords(progression: str, duration: float, key: Scale) -> list[ChordLabel]:
    """Parse a space-separated Roman numeral progression into ChordLabels."""
    parts = progression.split()
    beats_per = duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        chord = key.parse_roman(p)
        chord.start = i * beats_per
        chord.duration = beats_per
        chords.append(chord)
    return chords


# ---------------------------------------------------------------------------
# I. Velvet Stars (Бархатные звезды)
# ---------------------------------------------------------------------------

def produce_track_1():
    """Jazzy Neo-Soul / Alt-R&B in G Dorian. Laid-back groove and velvet_soul bass."""
    print("Producing I. Velvet Stars (Neo-Soul / Velvet Bass)...")

    duration = 96.0
    # i - iv - VII - v in G Dorian
    progression = "i iv VII v" * 6
    chords = _build_chords(progression, duration, KEY_DORIAN)

    # Melody: Stepwise piano lines
    params = GeneratorParams(density=0.35, key_range_low=55, key_range_high=79)
    melody_gen = MelodyGenerator(
        params,
        drama_shape="crescendo",
        drama_peak=0.6,
        motif_probability=0.75,
        phrase_length=8.0,
        groove_template=LAID_BACK,
        beats_per_bar=4,
    )
    raw_melody = melody_gen.render(chords, KEY_DORIAN, duration)

    # Harmonize and spice
    harmonizer = PredictiveHarmonizer(certainty_threshold=2.0)
    chords = harmonizer.refine(chords, raw_melody, KEY_DORIAN, duration)
    melody = spiceup(raw_melody, KEY_DORIAN, depth=1)

    # Modern 2025 Velvet Bass
    bass_params = GeneratorParams(density=0.5, key_range_low=36, key_range_high=55)
    bass_gen = ModernBass2025Generator(bass_params, style="velvet_soul")
    bass = bass_gen.render(chords, KEY_DORIAN, duration)

    # Warm Rhodes pad
    pad = [
        NoteInfo(pitch=c.root + 36, start=c.start, duration=c.duration * 1.05, velocity=50)
        for c in chords
    ]

    return {"piano": melody, "bass": bass, "pad": pad}, 76.0


# ---------------------------------------------------------------------------
# II. Pulsar Dance (Пульсар)
# ---------------------------------------------------------------------------

def produce_track_2():
    """Future Funk / Alt-Pop. Heavy syncopated hybrid_slap bass in G Dorian."""
    print("Producing II. Pulsar Dance (Syncopated Alt-Pop / Hybrid Slap)...")

    duration = 120.0
    # i - iv - bVI - V progression
    progression = "i iv bVI V" * 8
    chords = _build_chords(progression, duration, KEY_DORIAN)

    # Bright syncopated lead synth chords
    params = GeneratorParams(density=0.6, key_range_low=58, key_range_high=82)
    melody_gen = MelodyGenerator(
        params,
        drama_shape="dramatic",
        drama_peak=0.75,
        syncopation=0.7,
        groove_template=SWING_60,
        beats_per_bar=4,
    )
    raw_melody = melody_gen.render(chords, KEY_DORIAN, duration)
    melody = spiceup(raw_melody, KEY_DORIAN, depth=1)

    # Modern 2025 Hybrid Slap bass (peaks at 92, ghost syncopation, avg 59)
    bass_params = GeneratorParams(density=0.8, key_range_low=36, key_range_high=62)
    bass_gen = ModernBass2025Generator(bass_params, style="hybrid_slap")
    bass = bass_gen.render(chords, KEY_DORIAN, duration)

    # High perk synth accents on strong note peaks
    accents = [
        NoteInfo(pitch=n.pitch + 12, start=n.start, duration=0.15, velocity=105)
        for n in melody
        if n.velocity > 85
    ]

    return {"lead": melody, "bass": bass, "accents": accents}, 112.0


# ---------------------------------------------------------------------------
# III. Plucked Nebula (Туманность)
# ---------------------------------------------------------------------------

def produce_track_3():
    """Dark Disco / Cosmic House in G Mixolydian. Tight analog_pluck bass."""
    print("Producing III. Plucked Nebula (Dark Disco / Analog Pluck)...")

    duration = 112.0
    # I - bVII - IV - I in G Mixolydian
    progression = "I bVII IV I" * 7
    chords = _build_chords(progression, duration, KEY_MIXOLYDIAN)

    # Sparkling high arpeggiator melody
    params = GeneratorParams(density=0.75, key_range_low=60, key_range_high=88)
    melody_gen = MelodyGenerator(
        params,
        drama_shape="epic",
        phrase_length=4.0,
        beats_per_bar=4,
    )
    raw_melody = melody_gen.render(chords, KEY_MIXOLYDIAN, duration)
    melody = spiceup(raw_melody, KEY_MIXOLYDIAN, depth=1, single_pool=[OneToThree])

    # Modern 2025 Analog Pluck synth bass
    bass_params = GeneratorParams(density=0.7, key_range_low=36, key_range_high=48)
    bass_gen = ModernBass2025Generator(bass_params, style="analog_pluck")
    bass = bass_gen.render(chords, KEY_MIXOLYDIAN, duration)

    # Ethereal sweeping string pad
    pad = [
        NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration * 1.1, velocity=45)
        for c in chords
    ]

    return {"arp": melody, "bass": bass, "pad": pad}, 120.0


# ---------------------------------------------------------------------------
# IV. Gravity Return (Притяжение)
# ---------------------------------------------------------------------------

def produce_track_4():
    """Cinematic Electronica in G Dorian. Deep crescendo_return bass rises."""
    print("Producing IV. Gravity Return (Cinematic / Crescendo Sweep)...")

    duration = 128.0
    # Long drone progression: i - v - iv - i (4 bars per chord)
    progression = "i i v v iv iv i i" * 2
    chords = _build_chords(progression, duration, KEY_DORIAN)

    # Expressive high lead theme
    params = GeneratorParams(density=0.3, key_range_low=55, key_range_high=79)
    melody_gen = MelodyGenerator(
        params,
        drama_shape="epic",
        drama_peak=0.9,
        phrase_length=16.0,
        beats_per_bar=4,
    )
    raw_melody = melody_gen.render(chords, KEY_DORIAN, duration)
    melody = spiceup(raw_melody, KEY_DORIAN, depth=1)

    # Canon for cinematic voice layering
    canon = serialize_canon(
        voices=[melody, melody],
        delay_beats=8.0,
        transpositions=[0, -12],
        duration_beats=duration,
    )

    # Modern 2025 Crescendo Sweep bass (starts at 31, rises to 68, open LPF CC 74)
    bass_params = GeneratorParams(density=0.6, key_range_low=24, key_range_high=48)
    bass_gen = ModernBass2025Generator(bass_params, style="crescendo_return")
    bass = bass_gen.render(chords, KEY_DORIAN, duration)

    # Deep brass hits on chord transitions
    brass = [
        NoteInfo(pitch=c.root + 36, start=c.start, duration=2.0, velocity=95)
        for c in chords
    ]

    return {"canon_lead": canon, "bass": bass, "brass": brass}, 88.0


# ---------------------------------------------------------------------------
# Post-production
# ---------------------------------------------------------------------------

def apply_post_production(raw_tracks, bpm, lufs=-14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.90,
        "lead": 0.85,
        "arp": 0.80,
        "canon_lead": 0.85,
        "bass": 1.10,  # Emphasize modern bass levels
        "pad": 0.45,
        "accents": 0.95,
        "brass": 0.80,
    })

    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan_events = master.apply_mastering(mixed)
    return mastered, pan_events


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    album_dir = Path("output/album_carina")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   CARINA EP — Album in G Dorian & Mixolydian")
    print("   Scale: G A Bb C D E F  / G A B C D E F")
    print("   Featuring Modern 2025 Bass Generators")
    print("=" * 60 + "\n")

    # I. Velvet Stars
    t1_raw, t1_bpm = produce_track_1()
    t1_m, t1_pan = apply_post_production(t1_raw, t1_bpm, lufs=-16.0)
    export_multitrack_midi(
        t1_m, str(album_dir / "01_Velvet_Stars.mid"),
        bpm=t1_bpm, cc_events=t1_pan,
        instruments={"piano": 1, "bass": 33, "pad": 89},
    )

    # II. Pulsar Dance
    t2_raw, t2_bpm = produce_track_2()
    t2_m, t2_pan = apply_post_production(t2_raw, t2_bpm, lufs=-12.0)
    export_multitrack_midi(
        t2_m, str(album_dir / "02_Pulsar_Dance.mid"),
        bpm=t2_bpm, cc_events=t2_pan,
        instruments={"lead": 81, "bass": 36, "accents": 46},
    )

    # III. Plucked Nebula
    t3_raw, t3_bpm = produce_track_3()
    t3_m, t3_pan = apply_post_production(t3_raw, t3_bpm, lufs=-13.0)
    export_multitrack_midi(
        t3_m, str(album_dir / "03_Plucked_Nebula.mid"),
        bpm=t3_bpm, cc_events=t3_pan,
        instruments={"arp": 39, "bass": 39, "pad": 52},
    )

    # IV. Gravity Return
    t4_raw, t4_bpm = produce_track_4()
    t4_m, t4_pan = apply_post_production(t4_raw, t4_bpm, lufs=-14.0)
    export_multitrack_midi(
        t4_m, str(album_dir / "04_Gravity_Return.mid"),
        bpm=t4_bpm, cc_events=t4_pan,
        instruments={"canon_lead": 81, "bass": 39, "brass": 61},
    )

    print("\n" + "=" * 60)
    print("   PRODUCTION COMPLETE: CARINA EP")
    print(f"   MIDI output saved under: {album_dir.resolve()}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
