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
album_violetta.py — "Violetta EP".

A beautiful, high-fidelity four-movement modern electronic and acoustic EP
utilizing our advanced 2025 modern bass generator styles.
Scale: C Aeolian (C=0, D=2, Eb=3, F=5, G=7, Ab=8, Bb=10) & C Dorian (C=0, D=2, Eb=3, F=5, G=7, A=9, Bb=10).
Root: C (0) — warm, extremely rich register for modern basses.

Movements:
  I.   Violet Twilight (Фиолетовые сумерки)  — Neo Soul / Alt-R&B in C Aeolian (fingerstyle bass)
  II.  Ultraviolet (Ультрафиолет)            — Syncopated Future Funk in C Dorian (slap bass)
  III. Purple Horizon (Пурпурный горизонт)   — Cosmic Synthwave in C Aeolian (sidechain_reactive bass)
  IV.  Amethyst Dream (Аметистовый сон)      — Evolving Cinematic Ambient in C Dorian (self_modifying bass)
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

# C Aeolian (C, D, Eb, F, G, Ab, Bb)
KEY_AEOLIAN = Scale(root=0, mode=Mode.AEOLIAN)
# C Dorian (C, D, Eb, F, G, A, Bb)
KEY_DORIAN = Scale(root=0, mode=Mode.DORIAN)


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
# I. Violet Twilight (Фиолетовые сумерки)
# ---------------------------------------------------------------------------

def produce_track_1():
    """Warm Neo-Soul / Alt-R&B in C Aeolian. Laid-back groove and fingerstyle bass."""
    print("Producing I. Violet Twilight (Neo-Soul / Fingerstyle Bass)...")

    duration = 96.0
    # i - iv - VII - v in C Aeolian
    progression = "i iv VII v" * 6
    chords = _build_chords(progression, duration, KEY_AEOLIAN)

    # Melody: Smooth stepwise Rhodes piano lines
    params = GeneratorParams(density=0.38, key_range_low=52, key_range_high=76)
    melody_gen = MelodyGenerator(
        params,
        drama_shape="crescendo",
        drama_peak=0.6,
        motif_probability=0.75,
        phrase_length=8.0,
        groove_template=LAID_BACK,
        beats_per_bar=4,
    )
    raw_melody = melody_gen.render(chords, KEY_AEOLIAN, duration)

    # Refine chords with predictive harmonizer and add light spice
    harmonizer = PredictiveHarmonizer(certainty_threshold=2.0)
    chords = harmonizer.refine(chords, raw_melody, KEY_AEOLIAN, duration)
    melody = spiceup(raw_melody, KEY_AEOLIAN, depth=1)

    # Modern 2025 Legato Fingerstyle Bass (pocket lock: Avg 63, Max 84)
    bass_params = GeneratorParams(density=0.55, key_range_low=28, key_range_high=48)
    bass_gen = ModernBass2025Generator(bass_params, style="fingerstyle")
    bass = bass_gen.render(chords, KEY_AEOLIAN, duration)

    # Warm sustained pad
    pad = [
        NoteInfo(pitch=c.root + 36, start=c.start, duration=c.duration * 1.05, velocity=48)
        for c in chords
    ]

    return {"piano": melody, "bass": bass, "pad": pad}, 78.0


# ---------------------------------------------------------------------------
# II. Ultraviolet (Ультрафиолет)
# ---------------------------------------------------------------------------

def produce_track_2():
    """Future Funk / Alt-Pop. Dynamic, highly syncopated slap/pop bass in C Dorian."""
    print("Producing II. Ultraviolet (Syncopated Future Funk / Slap Bass)...")

    duration = 120.0
    # i - iv - bVI - V progression (bright natural 6th from Dorian makes bVI major and iv minor sound amazing)
    progression = "i iv bVI V" * 8
    chords = _build_chords(progression, duration, KEY_DORIAN)

    # Bright syncopated lead chords
    params = GeneratorParams(density=0.65, key_range_low=55, key_range_high=80)
    melody_gen = MelodyGenerator(
        params,
        drama_shape="dramatic",
        drama_peak=0.8,
        syncopation=0.75,
        groove_template=SWING_60,
        beats_per_bar=4,
    )
    raw_melody = melody_gen.render(chords, KEY_DORIAN, duration)
    melody = spiceup(raw_melody, KEY_DORIAN, depth=1)

    # Modern 2025 Slap Bass (peaks at 95, classic funk, avg 64)
    bass_params = GeneratorParams(density=0.75, key_range_low=32, key_range_high=58)
    bass_gen = ModernBass2025Generator(bass_params, style="slap")
    bass = bass_gen.render(chords, KEY_DORIAN, duration)

    # High perk synth accents on strong note peaks
    accents = [
        NoteInfo(pitch=n.pitch + 12, start=n.start, duration=0.15, velocity=110)
        for n in melody
        if n.velocity > 85
    ]

    return {"lead": melody, "bass": bass, "accents": accents}, 115.0


# ---------------------------------------------------------------------------
# III. Purple Horizon (Пурпурный горизонт)
# ---------------------------------------------------------------------------

def produce_track_3():
    """Atmospheric Synthwave / Dark Disco in C Aeolian. Volume-ducking sidechain bass."""
    print("Producing III. Purple Horizon (Pumping Synthwave / Sidechain Bass)...")

    duration = 112.0
    # i - bVII - iv - i in C Aeolian
    progression = "i bVII iv i" * 7
    chords = _build_chords(progression, duration, KEY_AEOLIAN)

    # Rapid 16th-note sparkling arpeggiator
    params = GeneratorParams(density=0.8, key_range_low=58, key_range_high=86)
    melody_gen = MelodyGenerator(
        params,
        drama_shape="epic",
        phrase_length=4.0,
        beats_per_bar=4,
    )
    raw_melody = melody_gen.render(chords, KEY_AEOLIAN, duration)
    melody = spiceup(raw_melody, KEY_AEOLIAN, depth=1, single_pool=[OneToThree])

    # Modern 2025 Sidechain-Reactive Synth Bass (pumping volume CC 7, Avg 60, Max 84)
    bass_params = GeneratorParams(density=0.7, key_range_low=36, key_range_high=48)
    bass_gen = ModernBass2025Generator(bass_params, style="sidechain_reactive")
    bass = bass_gen.render(chords, KEY_AEOLIAN, duration)

    # Ethereal sweeping pad strings
    pad = [
        NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration * 1.1, velocity=40)
        for c in chords
    ]

    return {"arp": melody, "bass": bass, "pad": pad}, 122.0


# ---------------------------------------------------------------------------
# IV. Amethyst Dream (Аметистовый сон)
# ---------------------------------------------------------------------------

def produce_track_4():
    """Orchestral Ambient Rise & Release in C Dorian. Evolving self-modifying bass."""
    print("Producing IV. Amethyst Dream (Cinematic Ambient / Self-Modifying Bass)...")

    duration = 128.0
    # Long drone progression: i - v - iv - i (4 bars per chord = 16 beats)
    progression = "i i v v iv iv i i" * 2
    chords = _build_chords(progression, duration, KEY_DORIAN)

    # Expressive high lead melody theme
    params = GeneratorParams(density=0.32, key_range_low=52, key_range_high=76)
    melody_gen = MelodyGenerator(
        params,
        drama_shape="epic",
        drama_peak=0.9,
        phrase_length=16.0,
        beats_per_bar=4,
    )
    raw_melody = melody_gen.render(chords, KEY_DORIAN, duration)
    melody = spiceup(raw_melody, KEY_DORIAN, depth=1)

    # Canon for massive orchestration depth
    canon = serialize_canon(
        voices=[melody, melody],
        delay_beats=8.0,
        transpositions=[0, -12],
        duration_beats=duration,
    )

    # Modern 2025 Self-Modifying Bass (widens ranges/syncopation dynamically, Avg 66, Max 90)
    bass_params = GeneratorParams(density=0.6, key_range_low=24, key_range_high=48)
    bass_gen = ModernBass2025Generator(bass_params, style="self_modifying")
    bass = bass_gen.render(chords, KEY_DORIAN, duration)

    # Deep brass swells on transitions
    brass = [
        NoteInfo(pitch=c.root + 36, start=c.start, duration=2.5, velocity=90)
        for c in chords
    ]

    return {"canon_lead": canon, "bass": bass, "brass": brass}, 85.0


# ---------------------------------------------------------------------------
# Post-production
# ---------------------------------------------------------------------------

def apply_post_production(raw_tracks, bpm, lufs=-14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.92,
        "lead": 0.88,
        "arp": 0.82,
        "canon_lead": 0.85,
        "bass": 1.15,  # Push modern 2025 bass forward in the mix
        "pad": 0.48,
        "accents": 0.90,
        "brass": 0.85,
    })

    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan_events = master.apply_mastering(mixed)
    return mastered, pan_events


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    album_dir = Path("output/album_violetta")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   VIOLETTA EP — Album in C Aeolian & C Dorian")
    print("   Scale: C D Eb F G Ab Bb / C D Eb F G A Bb")
    print("   Featuring Modern 2025 Bass Generators")
    print("=" * 60 + "\n")

    # I. Violet Twilight
    t1_raw, t1_bpm = produce_track_1()
    t1_m, t1_pan = apply_post_production(t1_raw, t1_bpm, lufs=-16.0)
    export_multitrack_midi(
        t1_m, str(album_dir / "01_Violet_Twilight.mid"),
        bpm=t1_bpm, cc_events=t1_pan,
        instruments={"piano": 5, "bass": 34, "pad": 89},
    )

    # II. Ultraviolet
    t2_raw, t2_bpm = produce_track_2()
    t2_m, t2_pan = apply_post_production(t2_raw, t2_bpm, lufs=-12.0)
    export_multitrack_midi(
        t2_m, str(album_dir / "02_Ultraviolet.mid"),
        bpm=t2_bpm, cc_events=t2_pan,
        instruments={"lead": 81, "bass": 37, "accents": 14},
    )

    # III. Purple Horizon
    t3_raw, t3_bpm = produce_track_3()
    t3_m, t3_pan = apply_post_production(t3_raw, t3_bpm, lufs=-13.0)
    export_multitrack_midi(
        t3_m, str(album_dir / "03_Purple_Horizon.mid"),
        bpm=t3_bpm, cc_events=t3_pan,
        instruments={"arp": 81, "bass": 39, "pad": 89},
    )

    # IV. Amethyst Dream
    t4_raw, t4_bpm = produce_track_4()
    t4_m, t4_pan = apply_post_production(t4_raw, t4_bpm, lufs=-14.0)
    export_multitrack_midi(
        t4_m, str(album_dir / "04_Amethyst_Dream.mid"),
        bpm=t4_bpm, cc_events=t4_pan,
        instruments={"canon_lead": 82, "bass": 39, "brass": 61},
    )

    print("\n" + "=" * 60)
    print("   PRODUCTION COMPLETE: VIOLETTA EP")
    print(f"   MIDI output saved under: {album_dir.resolve()}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
