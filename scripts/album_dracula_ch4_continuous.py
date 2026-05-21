# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_dracula_ch4_continuous.py — ДРАКУЛА: Глава IV (Continuous Gothic Masterpiece)

Compiles all five movements of Chapter IV into a single seamless continuous MIDI
using compile_continuous_album with diatonic modulation bridges at key transitions.

Continuous structure (total ≈ 20 min at original BPMs):
  I.   Тайные письма           — 72  BPM | B Hungarian Minor
  II.  Зверство у ворот        — 95  BPM | B Hungarian Minor  (same key, no bridge)
  III. В склепе Дракулы        — 50  BPM | B Phrygian         ← pivot bridge
  IV.  Удар лопаты             — 80  BPM | B Hungarian Minor  ← dominant bridge
  V.   Прыжок в бездну         — 64  BPM | B Phrygian → B Major ← chromatic bridge

Each movement is built by a modular function returning a metadata dict
compatible with compile_continuous_album.
"""

import random
from pathlib import Path

from melodica import types
from melodica.theory import Quality
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.accent import RhythmicAccentGenerator
from melodica.composer.automation import AutomationCurve
from melodica.composer.album_pipeline import compile_continuous_album, Mood
from melodica.composer.transition_coordinator import TransitionCoordinator

# Scales
KEY_MINOR    = types.Scale(root=11, mode=types.Mode.HUNGARIAN_MINOR)
KEY_PHRYGIAN = types.Scale(root=11, mode=types.Mode.PHRYGIAN)
KEY_MAJOR    = types.Scale(root=11, mode=types.Mode.MAJOR)

random.seed(1897)
OUT = Path("output/album_dracula_ch4")
OUT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _loop_chords(base_chords, dur: float) -> list:
    """Repeat a chord list until it fills `dur` beats."""
    full = []
    t = 0.0
    while t < dur:
        for c in base_chords:
            if t >= dur:
                break
            full.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration
    return full


# ---------------------------------------------------------------------------
# I. Тайные письма (Secret Correspondence) — 72 BPM | B Hungarian Minor
# ---------------------------------------------------------------------------

def build_secret_correspondence() -> dict:
    """Harker bribes the gypsies. Gypsy guitar + melancholic violin + cold pad.
    REFACTORED: Better spacing, rhythmic pulses, and dynamic entry."""
    bpm, dur = 72, 96.0
    chords = _loop_chords(types.parse_progression("i:4.0 - iv:4.0 - V:4.0 - i:4.0", KEY_MINOR), dur)

    # 1. BASS - Foundation only
    bass = BassGenerator(
        GeneratorParams(density=0.35, velocity_range=(50, 70), key_range_low=23, key_range_high=35),
        style="walking" # Add subtle motion instead of hold
    ).render(chords, KEY_MINOR, dur)

    # 2. GUITAR - Harmonic Body (shifted UP for separation)
    guitar_notes = ArpeggiatorGenerator(
        GeneratorParams(density=0.55, velocity_range=(55, 75), key_range_low=55, key_range_high=79),
        pattern="up_down"
    ).render(chords, KEY_MINOR, dur)
    guitar_track = types.Track(name="guitar", notes=guitar_notes)
    guitar_track.humanize(timing_std_beats=0.015, velocity_std=4.0)

    # 3. PAD - Airy layer (Filtered and sparse)
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.12, velocity_range=(40, 55), key_range_low=67, key_range_high=91),
        voicing="spread"
    ).render(chords, KEY_MINOR, dur)
    # Staggered entrance for pad: starts after 16 beats
    pad = [n for n in pad if n.start >= 16.0]

    # 4. VIOLIN - Emotional Lead (Anxiety/Tension)
    violin_notes = MelodyGenerator(
        GeneratorParams(density=0.48, complexity=0.70, velocity_range=(75, 105),
                        key_range_low=67, key_range_high=93),
        phrase_length=6.0, motif_probability=0.85
    ).render(chords, KEY_MINOR, dur)
    violin_track = types.Track(name="violin", notes=violin_notes)
    # Give it 'breath': silence at specific intervals
    violin_track.notes = [n for n in violin_track.notes if not (32.0 <= n.start <= 40.0)]

    cc_events = {
        "violin": AutomationCurve.exponential(11, 60, 110, 0.0, dur, exponent=1.1, steps=40),
        "pad":    AutomationCurve.sine_lfo(74, 40, 110, 16.0, dur, period=16.0),
    }

    return {
        "tracks":      {"guitar": guitar_track.notes, "violin": violin_track.notes, "pad": pad, "bass": bass},
        "bpm":         bpm,
        "instruments": {"guitar": 24, "violin": 40, "pad": 89, "bass": 32},
        "cc_events":   cc_events,
        "key":         KEY_MINOR,
    }


# ---------------------------------------------------------------------------
# II. Зверство у ворот (Atrocity at the Gates) — 95 BPM | B Hungarian Minor
# ---------------------------------------------------------------------------

def build_atrocity_at_gates() -> dict:
    """Frantic mother screaming, wolf pack descending. Dynamic accelerando."""
    bpm, dur = 95, 64.0
    chords = _loop_chords(types.parse_progression("i:4.0 - bII:4.0 - iidim:4.0 - V:4.0", KEY_MINOR), dur)

    screaming = MelodyGenerator(
        GeneratorParams(density=0.75, complexity=0.85, velocity_range=(90, 115),
                        key_range_low=64, key_range_high=93),
        phrase_length=4.0
    ).render(chords, KEY_MINOR, dur)
    screaming_track = types.Track(name="screaming_violin", notes=screaming)
    screaming_track.scale_velocity(1.30).transpose(1)

    timpani = RhythmicAccentGenerator(
        preset="gallop", pitch=35, velocity_humanize=10, accent_strength=1.2
    ).render(chords, KEY_MINOR, dur)

    horns = StringsEnsembleGenerator(
        GeneratorParams(density=0.40, velocity_range=(75, 100), key_range_low=47, key_range_high=71)
    ).render(chords, KEY_MINOR, dur)

    tempo_events = [(float(b), 95.0 + (132.0 - 95.0) * (b / dur)) for b in range(0, int(dur), 4)]

    cc_events = {
        "screaming_violin": AutomationCurve.sine_lfo(1, 0, 120, 0.0, dur, period=4.0),
        "horns":            AutomationCurve.exponential(11, 60, 115, 0.0, dur, exponent=2.0, steps=20),
    }

    # --- TransitionCoordinator: orchestrate the pre-transition sweep & fill ---
    # (We won't know the next boundary until compile time, so we annotate the
    #  tail section here: in the last 4 bars the horns filter will close.)
    tracks_dict = {
        "screaming_violin": screaming_track,
        "timpani": types.Track(name="timpani", notes=timpani),
        "horns": types.Track(name="horns", notes=horns),
    }
    TransitionCoordinator.apply_sweeps(
        tracks_dict, cc_events, ["horns"],
        cc_num=74, start_val=95, end_val=20,
        start_beat=dur - 8.0, end_beat=dur,
        curve_type="linear", steps=8
    )

    return {
        "tracks":        {k: v.notes if isinstance(v, types.Track) else v for k, v in tracks_dict.items()},
        "bpm":           bpm,
        "instruments":   {"screaming_violin": 40, "timpani": 47, "horns": 60},
        "cc_events":     cc_events,
        "tempo_events":  tempo_events,
        "key":           KEY_MINOR,
    }


# ---------------------------------------------------------------------------
# III. В склепе Дракулы (Dracula's Vault) — 50 BPM | B Phrygian
# ---------------------------------------------------------------------------

def build_draculas_vault() -> dict:
    """Cold crypt, Count lying bloated. Scale morph from Hungarian Minor → Phrygian."""
    bpm, dur = 50, 80.0
    chords = _loop_chords(types.parse_progression("i:4.0 - bII:4.0 - vii:4.0 - iv:4.0", KEY_PHRYGIAN), dur)

    cello_notes = MelodyGenerator(
        GeneratorParams(density=0.48, complexity=0.60, velocity_range=(65, 90),
                        key_range_low=48, key_range_high=72),
        phrase_length=8.0
    ).render(chords, KEY_MINOR, dur)
    cello_track = types.Track(name="cello", notes=cello_notes)
    cello_track.morph_scale(from_scale=KEY_MINOR, to_scale=KEY_PHRYGIAN, strategy="degree")
    cello_track.scale_velocity(0.85)

    organ = AmbientPadGenerator(
        GeneratorParams(density=0.18, velocity_range=(45, 65), key_range_low=47, key_range_high=76)
    ).render(chords, KEY_PHRYGIAN, dur)

    contrabass_notes = BassGenerator(
        GeneratorParams(density=0.30, velocity_range=(50, 70), key_range_low=23, key_range_high=38)
    ).render(chords, KEY_PHRYGIAN, dur)
    contrabass_track = types.Track(name="contrabass", notes=contrabass_notes)
    contrabass_track.transpose(-12).scale_velocity(0.90)

    cc_events = {
        "cello":      AutomationCurve.sine_lfo(11, 45, 105, 0.0, dur, period=10.0),
        "organ":      AutomationCurve.exponential(74, 30, 85, 0.0, dur, exponent=1.5, steps=30),
        "contrabass": AutomationCurve.linear(7, 80, 50, 0.0, dur, steps=20),
    }

    return {
        "tracks":      {"cello": cello_track.notes, "organ": organ, "contrabass": contrabass_track.notes},
        "bpm":         bpm,
        "instruments": {"cello": 42, "organ": 19, "contrabass": 43},
        "cc_events":   cc_events,
        "key":         KEY_PHRYGIAN,
    }


# ---------------------------------------------------------------------------
# IV. Удар лопаты (The Shovel's Strike) — 80 BPM | B Hungarian Minor
# ---------------------------------------------------------------------------

def build_shovels_strike() -> dict:
    """Jonathan strikes Dracula. Martial percussion, accelerando, Dracula's glare.
    REFACTORED: High-register 'air', clearer bass, and dramatic expansion."""
    bpm, dur = 80, 48.0
    chords = _loop_chords(types.parse_progression("i:2.0 - V:2.0 - VI:2.0 - iv:2.0", KEY_MINOR), dur)

    # 1. BASS - Clear sub foundation
    timpani = RhythmicAccentGenerator(
        preset="march", pitch=36, velocity_humanize=8, accent_strength=1.3
    ).render(chords, KEY_MINOR, dur)

    # 2. CELLO - Mid-low drive (restricted to C2-C3 for separation)
    cello = StringsEnsembleGenerator(
        GeneratorParams(density=0.45, velocity_range=(75, 95), key_range_low=36, key_range_high=48)
    ).render(chords, KEY_MINOR, dur)

    # 3. VIOLIN - High Lead (Screaming/Anxiety)
    violin_notes = MelodyGenerator(
        GeneratorParams(density=0.65, complexity=0.85, velocity_range=(90, 115),
                        key_range_low=72, key_range_high=96),
        phrase_length=4.0
    ).render(chords, KEY_MINOR, dur)
    violin_track = types.Track(name="violin", notes=violin_notes)

    # 4. AIR LAYER - Glass/Metallic textures (High register > 6kHz equivalent)
    # Using Arp with very high register and sparse density
    sparkle = ArpeggiatorGenerator(
        GeneratorParams(density=0.15, velocity_range=(40, 65), key_range_low=96, key_range_high=108),
        pattern="random", note_duration=0.125
    ).render(chords, KEY_MINOR, dur)

    tempo_events = [(float(b), 80.0 + (135.0 - 80.0) * (b / dur)) for b in range(0, int(dur), 2)]

    cc_events = {
        "violin":  AutomationCurve.exponential(1, 40, 120, 0.0, dur, exponent=1.5, steps=30),
        "cello":   AutomationCurve.exponential(74, 30, 95, 0.0, dur, exponent=2.0, steps=20),
        "sparkle": AutomationCurve.sine_lfo(74, 20, 90, 0.0, dur, period=8.0),
    }

    return {
        "tracks":       {"violin": violin_track.notes, "timpani": timpani, "cello": cello, "sparkle": sparkle},
        "bpm":          bpm,
        "instruments":  {"violin": 40, "timpani": 47, "cello": 42, "sparkle": 98}, # 98: Crystal/FX
        "cc_events":    cc_events,
        "tempo_events": tempo_events,
        "key":          KEY_MINOR,
    }


# ---------------------------------------------------------------------------
# V. Прыжок в бездну (Leap into the Abyss) — 64 BPM | B Phrygian → B Major
# ---------------------------------------------------------------------------

def build_leap_into_abyss() -> dict:
    """Jonathan's final diary entry and his desperate leap into eternity."""
    bpm, dur = 64, 80.0
    chords = _loop_chords(types.parse_progression("i:6.0 - VI:6.0 - bII:6.0 - V:6.0", KEY_PHRYGIAN), dur)

    flute_notes = MelodyGenerator(
        GeneratorParams(density=0.45, complexity=0.65, velocity_range=(70, 95),
                        key_range_low=67, key_range_high=91),
        phrase_length=6.0
    ).render(chords, KEY_PHRYGIAN, dur)
    flute_track = types.Track(name="flute", notes=flute_notes)
    flute_track.humanize(timing_std_beats=0.012, velocity_std=3.0)

    cello_waltz = RhythmicAccentGenerator(
        preset="waltz", pitch=None, octave=4, velocity_humanize=8
    ).render(chords, KEY_PHRYGIAN, dur)

    pad_notes = AmbientPadGenerator(
        GeneratorParams(density=0.25, velocity_range=(45, 65), key_range_low=60, key_range_high=84)
    ).render(chords, KEY_PHRYGIAN, dur)
    for note in pad_notes:
        if note.start >= 70.0:
            note.morph_scale(from_scale=KEY_PHRYGIAN, to_scale=KEY_MAJOR, strategy="degree")
            note.velocity = 95

    contrabass = BassGenerator(
        GeneratorParams(density=0.35, velocity_range=(55, 75), key_range_low=23, key_range_high=40)
    ).render(chords, KEY_PHRYGIAN, dur)

    cc_events = {
        "flute": AutomationCurve.exponential(7, 95, 0, 70.0, 80.0, exponent=1.8, steps=15),
        "pad":   AutomationCurve.linear(74, 50, 95, 60.0, 78.0, steps=10),
    }

    return {
        "tracks":      {"flute": flute_track.notes, "cello_waltz": cello_waltz,
                        "pad": pad_notes, "contrabass": contrabass},
        "bpm":         bpm,
        "instruments": {"flute": 73, "cello_waltz": 42, "pad": 92, "contrabass": 43},
        "cc_events":   cc_events,
        "key":         KEY_PHRYGIAN,
    }


# ---------------------------------------------------------------------------
# Main — compile all five movements into one continuous masterpiece
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 80)
    print("   БРЭМ СТОКЕР — ДРАКУЛА: ГЛАВА IV (Continuous Gothic Masterpiece)")
    print("   Собираем пять частей в единое непрерывное готическое путешествие...")
    print("=" * 80)

    print("\n-> Building movement I:   Тайные письма (Secret Correspondence)...")
    meta_i   = build_secret_correspondence()

    print("-> Building movement II:  Зверство у ворот (Atrocity at the Gates)...")
    meta_ii  = build_atrocity_at_gates()

    print("-> Building movement III: В склепе Дракулы (Dracula's Vault)...")
    meta_iii = build_draculas_vault()

    print("-> Building movement IV:  Удар лопаты (The Shovel's Strike)...")
    meta_iv  = build_shovels_strike()

    print("-> Building movement V:   Прыжок в бездну (Leap into the Abyss)...")
    meta_v   = build_leap_into_abyss()

    output_path = OUT / "Dracula_Chapter_IV_Continuous.mid"

    print("\n-> Compiling continuous album with diatonic modulation bridges...")
    print("   Overlap: 8 beats  |  Strategy: dominant  |  Bridge pad: GM 89 (Warm Pad)")
    print("   Key transitions:")
    print("     I → II  : B Hungarian Minor → B Hungarian Minor  (no bridge)")
    print("     II → III: B Hungarian Minor → B Phrygian         (pivot bridge)")
    print("     III → IV: B Phrygian → B Hungarian Minor         (dominant bridge)")
    print("     IV → V  : B Hungarian Minor → B Phrygian         (chromatic bridge)")

    report = compile_continuous_album(
        tracks_metadata=[meta_i, meta_ii, meta_iii, meta_iv, meta_v],
        output_path=output_path,
        overlap_beats=8.0,
        mood=Mood.CHAMBER,
        modulation_strategy="dominant",
        transition_instrument=89,      # Pad 2 Warm — eerie gothic transition pads
    )

    print("\n" + "=" * 80)
    print("   ✓ CONTINUOUS ALBUM COMPILED SUCCESSFULLY")
    print(f"   Output: {output_path.resolve()}")
    print("=" * 80)

    print("\nTrack profiles in continuous mix:")
    for name, prof in report.get("profiles", {}).items():
        print(f"   {name:22s} | role={prof['role']:8s} | avg_pitch={prof['avg_pitch']:5.1f}"
              f" | density={prof['density']:.3f}")

    transition_pads = [k for k in report.get("profiles", {}) if "transition" in k]
    if transition_pads:
        n_bridges = len(transition_pads)
        print(f"\n   ✓ Diatonic modulation bridges inserted ({n_bridges} pad track(s)): {transition_pads}")
    else:
        print("\n   Note: all tracks shared the same key — no modulation bridges needed.")

