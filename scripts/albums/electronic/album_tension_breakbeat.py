# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_tension_breakbeat.py — "Tension & Breaks" Breakbeat Album.

An album showcasing the synergy of the BreakbeatGenerator and the TensionGenerator 
in minor keys and film tension scales.

Tracks:
  1. Subterranean Echoes — Atmospheric breakbeat with high-register major 7th tension.
                          Key: A Minor (Aeolian) | 160 BPM
  2. Suspended Gravity   — Heavy industrial breakbeat with mid-register semitone clusters.
                          Key: D Suspense (Tension scale) | 140 BPM
  3. Neural Collapse     — Glitchy/IDM breakbeat with rapid atonal scatter dissonance.
                          Key: G Harmonic Minor | 170 BPM
"""

import random
from pathlib import Path

from melodica.types import Scale, Mode, ChordLabel, NoteInfo, parse_progression
from melodica.generators import GeneratorParams
from melodica.generators.breakbeat import BreakbeatGenerator
from melodica.generators.tension import TensionGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.composer.album_pipeline import produce_track, Mood

# GM Programs mapping
SYNTH_BASS = 38
DARK_PAD = 88
SYNTH_LEAD = 80
CLEAN_GUITAR = 27
DRUMS = 0

random.seed(2026)
OUT = Path("output/album_tension_breakbeat")
OUT.mkdir(parents=True, exist_ok=True)


# =====================================================================
# Track 1: Subterranean Echoes — 160 BPM — A Aeolian
# =====================================================================
def produce_subterranean_echoes():
    print("  1. Subterranean Echoes [A Minor — 160 BPM]")
    key = Scale(root=9, mode=Mode.AEOLIAN)
    dur = 96.0  # 24 bars
    chords = parse_progression("i:4 iadd9:4 iv7:4 iadd9:4 v7:4 iv7:4 iadd9:8 " * 3, key)

    # Classic Amen breakbeat with medium chop probability
    drums = BreakbeatGenerator(
        variant="amen", chop_probability=0.25, ghost_notes=True
    ).render(chords, key, dur)

    # Low, warm sub synth bass
    bass = SynthBassGenerator(
        waveform="sine", pattern="sub_kick"
    ).render(chords, key, dur)

    # Soft ambient background pads
    pad = DarkPadGenerator(
        mode="minor_pad", register="low", velocity_level=0.35, chord_dur=8.0
    ).render(chords, key, dur)

    # Beautiful floaty high-register major 7th tension layer (eerie beauty)
    tension = TensionGenerator(
        mode="major7_tension", note_duration=4.0, velocity_level=0.30, register="high", density=0.5
    ).render(chords, key, dur)

    # Soft, searching solo synth lead melody
    lead = SoloMelodyGenerator(
        params=GeneratorParams(key_range_low=60, key_range_high=84),
        style="modal_ambient",
        vibrato_depth=0.5,
    ).render(chords, key, dur)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "dark_pad": pad,
        "tension_fx": tension,
        "lead_synth": lead,
    }

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "tension_fx": SYNTH_LEAD,
        "lead_synth": SYNTH_LEAD,
    }

    produce_track(
        tracks=tracks,
        bpm=160.0,
        instruments=inst,
        path=OUT / "01_Subterranean_Echoes.mid",
        mood=Mood.AMBIENT,
        key=key,
        verbose=False,
    )


# =====================================================================
# Track 2: Suspended Gravity — 140 BPM — D Suspense
# =====================================================================
def produce_suspended_gravity():
    print("  2. Suspended Gravity [D Suspense — 140 BPM]")
    key = Scale(root=2, mode=Mode.SUSPENSE)
    dur = 96.0  # 24 bars
    # i, bII, i, v progressions parsed from D Suspense scale (root D, b2 Eb)
    chords = parse_progression("i:4 bII:4 i:4 v:4 " * 6, key)

    # Heavy, syncopated funky breakbeat
    drums = BreakbeatGenerator(
        variant="funky", chop_probability=0.35, ghost_notes=True
    ).render(chords, key, dur)

    # Aggressive reese synth bass sliding in Phrygian/Suspense steps
    bass = SynthBassGenerator(
        waveform="acid", pattern="reese", slide_probability=0.45, octave_variation=0.2
    ).render(chords, key, dur)

    # Dark tritone drone pads in the low register
    pad = DarkPadGenerator(
        mode="tritone_drone", register="low", velocity_level=0.40, chord_dur=4.0
    ).render(chords, key, dur)

    # Mid-register semitone clusters creating massive harmonic rubbing/tension
    tension = TensionGenerator(
        mode="semitone_cluster", note_duration=2.0, velocity_level=0.40, register="mid", density=0.7
    ).render(chords, key, dur)

    # Occult, expressive guitar lead notes
    lead = SoloMelodyGenerator(
        params=GeneratorParams(key_range_low=50, key_range_high=74),
        style="cinematic_strings",
        vibrato_depth=0.7,
    ).render(chords, key, dur)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "dark_pad": pad,
        "tension_fx": tension,
        "lead_guitar": lead,
    }

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "tension_fx": SYNTH_LEAD,
        "lead_guitar": CLEAN_GUITAR,
    }

    produce_track(
        tracks=tracks,
        bpm=140.0,
        instruments=inst,
        path=OUT / "02_Suspended_Gravity.mid",
        mood=Mood.EXPERIMENTAL,
        key=key,
        verbose=False,
    )


# =====================================================================
# Track 3: Neural Collapse — 170 BPM — G Harmonic Minor
# =====================================================================
def produce_neural_collapse():
    print("  3. Neural Collapse [G Harmonic Minor — 170 BPM]")
    key = Scale(root=7, mode=Mode.HARMONIC_MINOR)
    dur = 96.0  # 24 bars
    chords = parse_progression("i:4 VI:4 iv7:4 V7:4 " * 6, key)

    # Complex, glitchy IDM breakbeat played at double time speed
    drums = BreakbeatGenerator(
        variant="idm", chop_probability=0.6, ghost_notes=True, double_time=True
    ).render(chords, key, dur)

    # Sawtooth wobble bass
    bass = SynthBassGenerator(
        waveform="saw", pattern="wobble", octave_variation=0.3
    ).render(chords, key, dur)

    # Shimmering diminished cluster pads
    pad = DarkPadGenerator(
        mode="dim_cluster", register="mid", velocity_level=0.35, chord_dur=4.0
    ).render(chords, key, dur)

    # Rapid high-register atonal scatter (unresolved glitched notes)
    tension = TensionGenerator(
        mode="atonal_scatter", note_duration=1.0, velocity_level=0.45, register="high", density=0.8
    ).render(chords, key, dur)

    # Fast vocal-mimicking synth lead melody
    lead = SoloMelodyGenerator(
        params=GeneratorParams(key_range_low=64, key_range_high=88),
        style="vocal_mimic",
        vibrato_depth=0.6,
    ).render(chords, key, dur)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "dark_pad": pad,
        "tension_fx": tension,
        "lead_synth": lead,
    }

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "tension_fx": SYNTH_LEAD,
        "lead_synth": SYNTH_LEAD,
    }

    produce_track(
        tracks=tracks,
        bpm=170.0,
        instruments=inst,
        path=OUT / "03_Neural_Collapse.mid",
        mood=Mood.AGGRESSIVE,
        key=key,
        verbose=False,
    )


def main():
    print("\n" + "=" * 60)
    print("   TENSION & BREAKS — Breakbeat Album Suite")
    print("   Evocative Rhythms & Creepy Dissonances")
    print("=" * 60 + "\n")

    produce_subterranean_echoes()
    produce_suspended_gravity()
    produce_neural_collapse()

    print("\n" + "=" * 60)
    print("   PRODUCTION COMPLETE: TENSION & BREAKS")
    print(f"   MIDI output saved to: {OUT.absolute()}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
