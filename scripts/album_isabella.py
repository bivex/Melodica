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
album_isabella.py — "Изабелла" (Isabella).

A three-movement album in Лирический мажор (Lyrical Major / Harmonic Major).
Scale: [0, 2, 4, 5, 7, 8, 11] — major with lowered 6th degree.
Root: D (2) — warm, cello-rich register.

Movements:
  I.  Утренний свет (Morning Light)       — gentle, ascending, hopeful
  II. Танец теней (Dance of Shadows)       — restless, syncopated, passionate
  III. Возвращение (Return)                 — resolution, warmth, canon closure

Uses newly ported features:
  - spiceup() for melodic ornamentation
  - PredictiveHarmonizer for chord refinement
  - serialize_canon() for the finale
"""

import random
from pathlib import Path

from melodica import types
from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.composer.transformers import spiceup, serialize_canon, Identity, OneToThree
from melodica.harmonize.predictive import PredictiveHarmonizer

# Key: D Lyrical Major (D, E, F#, G, A, Bb, C#)
KEY = Scale(root=2, mode=Mode.LYRICAL_MAJOR)


def _build_chords(progression: str, duration: float) -> list[ChordLabel]:
    """Parse a space-separated Roman numeral progression into ChordLabels."""
    parts = progression.split()
    beats_per = duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        chord = KEY.parse_roman(p)
        chord.start = i * beats_per
        chord.duration = beats_per
        chords.append(chord)
    return chords


# ---------------------------------------------------------------------------
# I. Утренний свет (Morning Light)
# ---------------------------------------------------------------------------

def produce_track_1():
    """Gentle awakening. Stepwise melodies, low density, warm pad."""
    print("Producing I. Утренний свет...")

    params = GeneratorParams(density=0.22, leap_probability=0.12)
    gen = MelodyGenerator(
        params,
        drama_shape="crescendo",
        drama_peak=0.55,
        motif_probability=0.7,
        harmony_note_probability=0.85,
        note_range_low=50,
        note_range_high=74,
        phrase_length=10.0,
        register_smoothness=0.95,
        steps_probability=0.88,
        first_note="tonic",
        last_note="scale",
    )

    duration = 96.0
    # I - IV - bvI - V in D lyrical major
    progression = "I IV bvI V" * 6
    chords = _build_chords(progression, duration)

    # Predictive harmonizer refines weak spots
    raw_melody = gen.render(chords, KEY, duration)
    harmonizer = PredictiveHarmonizer(certainty_threshold=2.0)
    chords = harmonizer.refine(chords, raw_melody, KEY, duration)

    # Spice up lightly (depth=1, mostly identity)
    melody = spiceup(raw_melody, KEY, depth=1,
                     single_pool=[Identity, Identity, Identity, OneToThree])

    # Pad: sustained chord tones one octave lower
    pad = [
        NoteInfo(
            pitch=c.root + 36,
            start=c.start,
            duration=c.duration,
            velocity=55,
        )
        for c in chords
    ]

    # Ethereal high harmonics — sparse, octave above melody peaks
    harmonics = [
        NoteInfo(pitch=n.pitch + 12, start=n.start, duration=n.duration * 1.5, velocity=35)
        for n in melody
        if n.velocity > 70 and n.pitch < 70
    ]

    return {"piano": melody, "pad": pad, "harmonics": harmonics}, melody, 72.0


# ---------------------------------------------------------------------------
# II. Танец теней (Dance of Shadows)
# ---------------------------------------------------------------------------

def produce_track_2():
    """Restless dance. Higher density, syncopation, dramatic leaps."""
    print("Producing II. Танец теней...")

    params = GeneratorParams(density=0.65, leap_probability=0.5)
    gen = MelodyGenerator(
        params,
        drama_shape="dramatic",
        drama_peak=0.8,
        motif_probability=0.45,
        ornament_probability=0.5,
        harmony_note_probability=0.5,
        note_range_low=42,
        note_range_high=86,
        syncopation=0.6,
        rhythm_variety=0.8,
        after_leap="step_any",
        direction_bias=0.4,
        allow_7th=True,
    )

    duration = 120.0
    # More turbulent progression: bvI - V - bvII - I, mixed with ii - bvI
    progression = "i bvI V i bvII i V bvI V" * 4 + "I bvVI V I bvVI bvII V I" * 2
    chords = _build_chords(progression, duration)

    notes = gen.render(chords, KEY, duration)

    # Refine harmonization
    harmonizer = PredictiveHarmonizer(certainty_threshold=3.0, re_evaluation_bonus=2.0)
    chords = harmonizer.refine(chords, notes, KEY, duration)

    # Moderate spice
    melody = spiceup(notes, KEY, depth=1)

    # Bass ostinato: root notes of each chord, doubled
    bass = [
        NoteInfo(
            pitch=max(24, c.root + 24),
            start=c.start,
            duration=c.duration * 0.85,
            velocity=80,
        )
        for c in chords
    ]

    # Percussive accents on strong beats
    accents = [
        NoteInfo(pitch=n.pitch, start=n.start, duration=0.15, velocity=120)
        for n in melody
        if n.velocity > 100
    ]

    return {"lead": melody, "bass": bass, "accents": accents}, 108.0


# ---------------------------------------------------------------------------
# III. Возвращение (Return)
# ---------------------------------------------------------------------------

def produce_track_3(theme_notes):
    """Resolution. Canon between two voices, warmth, thematic return."""
    print("Producing III. Возвращение...")

    params = GeneratorParams(density=0.4, leap_probability=0.25)
    gen = MelodyGenerator(
        params,
        drama_shape="epic",
        drama_peak=0.6,
        motif_probability=0.85,
        harmony_note_probability=0.8,
        note_range_low=50,
        note_range_high=79,
        phrase_length=8.0,
        register_smoothness=0.92,
        penultimate_step_above=True,
        first_note="tonic",
        last_note="scale",
    )

    duration = 112.0
    progression = "I IV V bvI I ii V I" * 4
    chords = _build_chords(progression, duration)

    notes = gen.render(chords, KEY, duration)

    # Light ornamentation
    melody = spiceup(notes, KEY, depth=1,
                     single_pool=[Identity, Identity, OneToThree])

    # Canon: lead voice + delayed voice a 5th below
    canon = serialize_canon(
        voices=[melody, melody],
        delay_beats=4.0,
        transpositions=[0, -7],
        duration_beats=duration,
    )

    # Warm pad from chord roots
    pad = [
        NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration * 1.2, velocity=50)
        for c in chords
    ]

    return {"canon": canon, "pad": pad}, 80.0


# ---------------------------------------------------------------------------
# Post-production
# ---------------------------------------------------------------------------

def apply_post_production(raw_tracks, bpm, lufs=-14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.95,
        "pad": 0.40,
        "harmonics": 0.30,
        "lead": 0.90,
        "bass": 0.55,
        "accents": 1.05,
        "canon": 0.90,
    })

    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan_events = master.apply_mastering(mixed)
    return mastered, pan_events


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    album_dir = Path("output/album_isabella")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 50)
    print("   ИЗАБЕЛЛА — Album in D Lyrical Major")
    print("   Scale: D E F# G A Bb C#")
    print("=" * 50 + "\n")

    # I. Утренний свет
    t1_raw, t1_melody, t1_bpm = produce_track_1()
    t1_m, t1_pan = apply_post_production(t1_raw, t1_bpm, lufs=-18.0)
    export_multitrack_midi(
        t1_m, str(album_dir / "01_Utrenniy_Svet.mid"),
        bpm=t1_bpm, cc_events=t1_pan,
        instruments={"piano": 1, "pad": 89, "harmonics": 46},
    )

    # II. Танец теней
    t2_raw, t2_bpm = produce_track_2()
    t2_m, t2_pan = apply_post_production(t2_raw, t2_bpm, lufs=-11.0)
    export_multitrack_midi(
        t2_m, str(album_dir / "02_Tanets_Teney.mid"),
        bpm=t2_bpm, cc_events=t2_pan,
        instruments={"lead": 42, "bass": 35, "accents": 14},
    )

    # III. Возвращение
    t3_raw, t3_bpm = produce_track_3(t1_melody)
    t3_m, t3_pan = apply_post_production(t3_raw, t3_bpm, lufs=-14.0)
    export_multitrack_midi(
        t3_m, str(album_dir / "03_Vozvrashenie.mid"),
        bpm=t3_bpm, cc_events=t3_pan,
        instruments={"canon": 42, "pad": 52},
    )

    print("\n" + "=" * 50)
    print("   PRODUCTION COMPLETE: ИЗАБЕЛЛА")
    print(f"   Location: {album_dir}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
