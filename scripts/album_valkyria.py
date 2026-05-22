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
album_valkyria.py — "Valkyria LP".

A monumental, high-fidelity 6-song epic electronic, orchestral, and acoustic album
showcasing the absolute limits of our Modern Bass and Expressive Solo Melody generators.

Scale & Key Settings:
  I.   Shield of Odin (Щит Одина)             — D Phrygian (saw bass + shred_guitar solo)
  II.  Ride of the Valkyries (Полет Валькирий)— E Aeolian (euclidean bass + cinematic_strings solo canon)
  III. Northern Lights (Северное сияние)      — G Lydian (sidechain bass + space_synth solo + arps)
  IV.  Runes of Wisdom (Руны мудрости)       — A Dorian (fingerstyle bass + neo_soul_keys Rhodes solo)
  V.   Whispering Winds (Шепот ветров)       — B Aeolian (spectral bass + modal_ambient detuned solo)
  VI.  Valhalla Gates (Врата Валгаллы)        — E Dorian (self_modifying bass + bebop_horn solo canon)
"""

import random
from pathlib import Path

from melodica import types
from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.modern_bass_2025 import ModernBass2025Generator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.composer.transformers import spiceup, serialize_canon, OneToThree
from melodica.harmonize.predictive import PredictiveHarmonizer
from melodica.rhythm.groove_template import SWING_60, LAID_BACK

# Keys Setup
KEY_D_PHRYGIAN = Scale(root=2, mode=Mode.PHRYGIAN)   # D Phrygian
KEY_E_AEOLIAN = Scale(root=4, mode=Mode.AEOLIAN)     # E Aeolian
KEY_G_LYDIAN = Scale(root=7, mode=Mode.LYDIAN)       # G Lydian
KEY_A_DORIAN = Scale(root=9, mode=Mode.DORIAN)       # A Dorian
KEY_B_AEOLIAN = Scale(root=11, mode=Mode.AEOLIAN)    # B Aeolian
KEY_E_DORIAN = Scale(root=4, mode=Mode.DORIAN)       # E Dorian


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
# I. Shield of Odin (Щит Одина)
# ---------------------------------------------------------------------------

def produce_track_1():
    """Dark Phrygian Metal / Industrial Rock in D Phrygian. Saw bass + Shred Solo."""
    print("Producing I. Shield of Odin (Dark Phrygian Metal / Saw Bass + Shred Solo)...")

    duration = 96.0
    # i - bII - VII - i in D Phrygian (dark heavy Phrygian bII step)
    progression = "i bII VII i" * 6
    chords = _build_chords(progression, duration, KEY_D_PHRYGIAN)

    # Solo: Shred guitar lines with pitch bends and rapid runs
    solo_params = GeneratorParams(density=0.65, key_range_low=50, key_range_high=80)
    solo_gen = SoloMelodyGenerator(solo_params, style="shred_guitar", vibrato_depth=0.8)
    raw_solo = solo_gen.render(chords, KEY_D_PHRYGIAN, duration)

    # Refine and spice
    harmonizer = PredictiveHarmonizer(certainty_threshold=1.5)
    chords = harmonizer.refine(chords, raw_solo, KEY_D_PHRYGIAN, duration)
    solo = spiceup(raw_solo, KEY_D_PHRYGIAN, depth=1)

    # Modern 2025 Saw Bass (peaks at 98, open aggressive sawtooth)
    bass_params = GeneratorParams(density=0.7, key_range_low=26, key_range_high=46)
    bass_gen = ModernBass2025Generator(bass_params, style="saw")
    bass = bass_gen.render(chords, KEY_D_PHRYGIAN, duration)

    # Heavy orchestral brass backing swells
    brass = [
        NoteInfo(pitch=c.root + 36, start=c.start, duration=c.duration * 0.9, velocity=88)
        for c in chords
    ]

    return {"guitar": solo, "bass": bass, "brass": brass}, 95.0


# ---------------------------------------------------------------------------
# II. Ride of the Valkyries (Полет Валькирий)
# ---------------------------------------------------------------------------

def produce_track_2():
    """Neo-classical Orchestral Rise in E Aeolian. Euclidean bass + String Solo."""
    print("Producing II. Ride of the Valkyries (Orchestral / Euclidean Bass + String Solo)...")

    duration = 128.0
    # i - VI - VII - i progression
    progression = "i VI VII i" * 8
    chords = _build_chords(progression, duration, KEY_E_AEOLIAN)

    # Solo: Cinematic string sweeps resolving tension stepwise
    solo_params = GeneratorParams(density=0.38, key_range_low=52, key_range_high=80)
    solo_gen = SoloMelodyGenerator(solo_params, style="cinematic_strings", vibrato_depth=0.95)
    raw_solo = solo_gen.render(chords, KEY_E_AEOLIAN, duration)
    solo = spiceup(raw_solo, KEY_E_AEOLIAN, depth=1)

    # Dual-voice delayed canon for massive symphonic space
    canon = serialize_canon(
        voices=[solo, solo],
        delay_beats=6.0,
        transpositions=[0, -12],
        duration_beats=duration,
    )

    # Modern 2025 Euclidean Bass (Bjorklund dynamic distribution)
    bass_params = GeneratorParams(density=0.6, key_range_low=28, key_range_high=48)
    bass_gen = ModernBass2025Generator(bass_params, style="euclidean")
    bass = bass_gen.render(chords, KEY_E_AEOLIAN, duration)

    # Thick string pad backing
    pad = [
        NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration * 1.05, velocity=42)
        for c in chords
    ]

    return {"canon_lead": canon, "bass": bass, "pad": pad}, 120.0


# ---------------------------------------------------------------------------
# III. Northern Lights (Северное сияние)
# ---------------------------------------------------------------------------

def produce_track_3():
    """Cosmic Synthwave / Progressive House in G Lydian. Sidechain bass + Space Synth."""
    print("Producing III. Northern Lights (Space House / Sidechain Bass + Space Solo)...")

    duration = 120.0
    # I - II - vii - I progression in G Lydian (majestic Lydian major II)
    progression = "I II vii I" * 7
    chords = _build_chords(progression, duration, KEY_G_LYDIAN)

    # Solo: Space synth lead with CC 74 cutoff sweep
    solo_params = GeneratorParams(density=0.45, key_range_low=58, key_range_high=86)
    solo_gen = SoloMelodyGenerator(solo_params, style="space_synth", vibrato_depth=0.7)
    raw_solo = solo_gen.render(chords, KEY_G_LYDIAN, duration)
    solo = spiceup(raw_solo, KEY_G_LYDIAN, depth=1)

    # Sparkling 16th-note arpeggiator chords
    arp_params = GeneratorParams(density=0.85, key_range_low=52, key_range_high=74)
    arp_gen = MelodyGenerator(arp_params, drama_shape="epic", phrase_length=4.0, beats_per_bar=4)
    arp_raw = arp_gen.render(chords, KEY_G_LYDIAN, duration)
    arp = spiceup(arp_raw, KEY_G_LYDIAN, depth=1, single_pool=[OneToThree])

    # Modern 2025 Sidechain-Reactive Synth Bass (pumping volume CC 7)
    bass_params = GeneratorParams(density=0.75, key_range_low=32, key_range_high=48)
    bass_gen = ModernBass2025Generator(bass_params, style="sidechain_reactive")
    bass = bass_gen.render(chords, KEY_G_LYDIAN, duration)

    # Shimmering space pad
    pad = [
        NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration * 1.1, velocity=45)
        for c in chords
    ]

    # Bell accents
    accents = [
        NoteInfo(pitch=n.pitch + 12, start=n.start, duration=0.18, velocity=105)
        for n in solo
        if n.velocity > 85
    ]

    return {"lead": solo, "arp": arp, "bass": bass, "pad": pad, "accents": accents}, 126.0


# ---------------------------------------------------------------------------
# IV. Runes of Wisdom (Руны мудрости)
# ---------------------------------------------------------------------------

def produce_track_4():
    """Velvet Neo-Soul / Alt-R&B in A Dorian. Fingerstyle bass + Rhodes Solo."""
    print("Producing IV. Runes of Wisdom (Neo-Soul / Fingerstyle Bass + Rhodes Solo)...")

    duration = 96.0
    # i - IV - VII - i in A Dorian (smooth natural major 6th Dorian IV step)
    progression = "i IV VII i" * 6
    chords = _build_chords(progression, duration, KEY_A_DORIAN)

    # Solo: Rhodes keys with syncopated chord stabs
    solo_params = GeneratorParams(density=0.4, key_range_low=52, key_range_high=74)
    solo_gen = SoloMelodyGenerator(solo_params, style="neo_soul_keys", vibrato_depth=0.7)
    raw_solo = solo_gen.render(chords, KEY_A_DORIAN, duration)

    # Harmonic refinement and warm spacing
    harmonizer = PredictiveHarmonizer(certainty_threshold=2.0)
    chords = harmonizer.refine(chords, raw_solo, KEY_A_DORIAN, duration)
    solo = spiceup(raw_solo, KEY_A_DORIAN, depth=1)

    # Modern 2025 Legato Fingerstyle Bass (pocket lock: Avg 63, Max 84)
    bass_params = GeneratorParams(density=0.52, key_range_low=28, key_range_high=48)
    bass_gen = ModernBass2025Generator(bass_params, style="fingerstyle")
    bass = bass_gen.render(chords, KEY_A_DORIAN, duration)

    # Warm sustained backing pad
    pad = [
        NoteInfo(pitch=c.root + 36, start=c.start, duration=c.duration * 1.05, velocity=48)
        for c in chords
    ]

    return {"piano": solo, "bass": bass, "pad": pad}, 82.0


# ---------------------------------------------------------------------------
# V. Whispering Winds (Шепот ветров)
# ---------------------------------------------------------------------------

def produce_track_5():
    """ Nordic Ambient Cinematic Drones in B Aeolian. Spectral bass + Detuned Solo."""
    print("Producing V. Whispering Winds (Ambient / Spectral Bass + Detuned Drone Solo)...")

    duration = 112.0
    # i - v - iv - i progression (long 4-bar drones)
    progression = "i i v v iv iv i i" * 2
    chords = _build_chords(progression, duration, KEY_B_AEOLIAN)

    # Solo: Modal ambient drone sweep with CC 98 VCO detune drift
    solo_params = GeneratorParams(density=0.32, key_range_low=55, key_range_high=82)
    solo_gen = SoloMelodyGenerator(solo_params, style="modal_ambient", vibrato_depth=0.65)
    raw_solo = solo_gen.render(chords, KEY_B_AEOLIAN, duration)
    solo = spiceup(raw_solo, KEY_B_AEOLIAN, depth=1)

    # Modern 2025 Spectral Morphing Bass (dynamic filter sweeps, pocket-locked)
    bass_params = GeneratorParams(density=0.45, key_range_low=26, key_range_high=46)
    bass_gen = ModernBass2025Generator(bass_params, style="spectral_morphing")
    bass = bass_gen.render(chords, KEY_B_AEOLIAN, duration)

    # Shimmering deep background space pads
    pad = [
        NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration * 1.1, velocity=38)
        for c in chords
    ]

    return {"lead": solo, "bass": bass, "pad": pad}, 72.0


# ---------------------------------------------------------------------------
# VI. Valhalla Gates (Врата Валгаллы)
# ---------------------------------------------------------------------------

def produce_track_6():
    """Monumental Brass & Jazz Fusion Finale in E Dorian. Self-modifying bass + Horn Solo."""
    print("Producing VI. Valhalla Gates (Fusion / Evolving Bass + Bebop Horn Solo)...")

    duration = 144.0
    # i - iv - v - i progression
    progression = "i iv v i" * 9
    chords = _build_chords(progression, duration, KEY_E_DORIAN)

    # Solo: Bebop Horn swing runs with displaced triplet timing
    solo_params = GeneratorParams(density=0.55, key_range_low=55, key_range_high=84)
    solo_gen = SoloMelodyGenerator(solo_params, style="bebop_horn", vibrato_depth=0.85)
    raw_solo = solo_gen.render(chords, KEY_E_DORIAN, duration)
    solo = spiceup(raw_solo, KEY_E_DORIAN, depth=1)

    # Dual horn canon for dynamic climax
    canon = serialize_canon(
        voices=[solo, solo],
        delay_beats=8.0,
        transpositions=[0, -12],
        duration_beats=duration,
    )

    # Modern 2025 Self-Modifying Bass (widens range and syncopation over duration)
    bass_params = GeneratorParams(density=0.65, key_range_low=24, key_range_high=48)
    bass_gen = ModernBass2025Generator(bass_params, style="self_modifying")
    bass = bass_gen.render(chords, KEY_E_DORIAN, duration)

    # Full epic brass chord backing
    brass = [
        NoteInfo(pitch=c.root + 36, start=c.start, duration=c.duration * 0.95, velocity=84)
        for c in chords
    ]

    return {"canon_lead": canon, "bass": bass, "brass": brass}, 104.0


# ---------------------------------------------------------------------------
# Post-production
# ---------------------------------------------------------------------------

def apply_post_production(raw_tracks, bpm, lufs=-14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.92,
        "guitar": 0.90,
        "lead": 0.88,
        "arp": 0.82,
        "canon_lead": 0.86,
        "bass": 1.18,  # Bold low-end for epic modern impact
        "pad": 0.46,
        "accents": 0.92,
        "brass": 0.85,
    })

    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan_events = master.apply_mastering(mixed)
    return mastered, pan_events


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

def main():
    album_dir = Path("output/album_valkyria")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   VALKYRIA LP — 6-Song Epic Masterpiece Album")
    print("   Featuring Advanced 2025 Basses & Expressive Solos")
    print("=" * 60 + "\n")

    # I. Shield of Odin
    t1_raw, t1_bpm = produce_track_1()
    t1_m, t1_pan = apply_post_production(t1_raw, t1_bpm, lufs=-12.0) # Hotter master for metal rock
    export_multitrack_midi(
        t1_m, str(album_dir / "01_Shield_of_Odin.mid"),
        bpm=t1_bpm, cc_events=t1_pan,
        instruments={"guitar": 30, "bass": 39, "brass": 61},
    )

    # II. Ride of the Valkyries
    t2_raw, t2_bpm = produce_track_2()
    t2_m, t2_pan = apply_post_production(t2_raw, t2_bpm, lufs=-14.0)
    export_multitrack_midi(
        t2_m, str(album_dir / "02_Ride_of_the_Valkyries.mid"),
        bpm=t2_bpm, cc_events=t2_pan,
        instruments={"canon_lead": 41, "bass": 39, "pad": 89},
    )

    # III. Northern Lights
    t3_raw, t3_bpm = produce_track_3()
    t3_m, t3_pan = apply_post_production(t3_raw, t3_bpm, lufs=-11.0) # Progressive house master
    export_multitrack_midi(
        t3_m, str(album_dir / "03_Northern_Lights.mid"),
        bpm=t3_bpm, cc_events=t3_pan,
        instruments={"lead": 82, "arp": 81, "bass": 39, "pad": 89, "accents": 14},
    )

    # IV. Runes of Wisdom
    t4_raw, t4_bpm = produce_track_4()
    t4_m, t4_pan = apply_post_production(t4_raw, t4_bpm, lufs=-15.0) # Laid-back velvet master
    export_multitrack_midi(
        t4_m, str(album_dir / "04_Runes_of_Wisdom.mid"),
        bpm=t4_bpm, cc_events=t4_pan,
        instruments={"piano": 5, "bass": 34, "pad": 89},
    )

    # V. Whispering Winds
    t5_raw, t5_bpm = produce_track_5()
    t5_m, t5_pan = apply_post_production(t5_raw, t5_bpm, lufs=-16.0) # Ethereal dynamic master
    export_multitrack_midi(
        t5_m, str(album_dir / "05_Whispering_Winds.mid"),
        bpm=t5_bpm, cc_events=t5_pan,
        instruments={"lead": 82, "bass": 39, "pad": 89},
    )

    # VI. Valhalla Gates
    t6_raw, t6_bpm = produce_track_6()
    t6_m, t6_pan = apply_post_production(t6_raw, t6_bpm, lufs=-13.0)
    export_multitrack_midi(
        t6_m, str(album_dir / "06_Valhalla_Gates.mid"),
        bpm=t6_bpm, cc_events=t6_pan,
        instruments={"canon_lead": 57, "bass": 39, "brass": 61},
    )

    print("\n" + "=" * 60)
    print("   PRODUCTION COMPLETE: VALKYRIA LP")
    print(f"   MIDI output saved under: {album_dir.resolve()}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
