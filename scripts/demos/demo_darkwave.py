"""Dark wave / Phrygian witch house demo."""

import os
from melodica import Scale, Mode
from melodica.types import parse_progression
from melodica.generators.melody import MelodyGenerator
from melodica.generators import GeneratorParams
from melodica.midi import export_multitrack_midi

OUT = "output/melody_demos"
os.makedirs(OUT, exist_ok=True)

# E Phrygian — dark, eerie
KEY = Scale(root=4, mode=Mode.PHRYGIAN)
BPM = 68

# GM instruments
PAD_SYNTH = 89   # Pad 1 (new age)
BASS_SYNTH = 38  # Synth Bass 1
LEAD_SYNTH = 81  # Lead 1 (square)
CHOIR = 52
STRING_ENS = 48
ATMOSPHERE = 99  # Atmosphere
HI_SYNTH = 88    # Pad 4 (choir)

# ---- Progressions ----
# Main: i - bvII - bIII - iv  (classic Phrygian dark)
prog_main = parse_progression("i bII bIII iv", KEY)
# Bridge: v - bvII - i - bvII
prog_bridge = parse_progression("v bII i bII", KEY)
# Interlude: bvII - bIII - iv - v
prog_inter = parse_progression("bII bIII iv v", KEY)
# Full cycle
prog_full = parse_progression("i bII bIII iv v bVI bvII i", KEY)

chords_main = prog_main * 2
chords_bridge = prog_bridge * 2
chords_full = prog_full * 2

dur_main = 32.0   # 8 bars
dur_bridge = 32.0
dur_full = 64.0


def _key():
    return KEY.get_key_at(0) if hasattr(KEY, 'get_key_at') else KEY


def demo_darkwave():
    key = _key()
    chords = chords_full
    dur = dur_full

    params_lead = GeneratorParams(density=0.45, key_range_low=64, key_range_high=84)
    params_counter = GeneratorParams(density=0.40, key_range_low=58, key_range_high=76)
    params_bass = GeneratorParams(density=0.35, key_range_low=28, key_range_high=48)
    params_pad = GeneratorParams(density=0.18, key_range_low=36, key_range_high=60)
    params_atmo = GeneratorParams(density=0.12, key_range_low=48, key_range_high=72)
    params_hi = GeneratorParams(density=0.25, key_range_low=72, key_range_high=96)

    tracks = {}
    instruments = {}

    # Lead: slow, spiraling melody — eerie Phrygian flavor
    tracks["Lead"] = MelodyGenerator(
        params_lead,
        phrase_contour="spiral", direction_bias=0.05,
        motif_probability=0.55, motif_variation="any",
        syncopation=0.25, rhythm_variety=0.45,
        ornament_probability=0.08,
        harmony_note_probability=0.50,
    ).render(chords, key, dur)
    instruments["Lead"] = LEAD_SYNTH

    # Counter-melody: haunting, descending bias
    tracks["Counter"] = MelodyGenerator(
        params_counter,
        phrase_contour="wave", direction_bias=-0.2,
        motif_probability=0.45, syncopation=0.30,
        rhythm_variety=0.35, harmony_note_probability=0.60,
    ).render(chords, key, dur)
    instruments["Counter"] = CHOIR

    # Sub bass: deep, minimal movement
    tracks["Bass"] = MelodyGenerator(
        params_bass,
        phrase_contour="flat",
        harmony_note_probability=0.92, steps_probability=0.90,
        note_repetition_probability=0.30, rhythm_variety=0.20,
        motif_probability=0.20, syncopation=0.10,
    ).render(chords, key, dur)
    instruments["Bass"] = BASS_SYNTH

    # Dark pad: sustained, barely moving
    tracks["Pad"] = MelodyGenerator(
        params_pad,
        harmony_note_probability=0.95, random_movement=0.10,
        note_repetition_probability=0.40, rhythm_variety=0.05,
    ).render(chords, key, dur)
    instruments["Pad"] = PAD_SYNTH

    # Atmosphere: sparse, high ethereal layer
    tracks["Atmo"] = MelodyGenerator(
        params_atmo,
        phrase_contour="arch", harmony_note_probability=0.88,
        random_movement=0.12, note_repetition_probability=0.35,
        rhythm_variety=0.08,
    ).render(chords, key, dur)
    instruments["Atmo"] = ATMOSPHERE

    # High shimmer: very sparse, upper register
    tracks["Shimmer"] = MelodyGenerator(
        params_hi,
        phrase_contour="spiral", direction_bias=-0.1,
        motif_probability=0.35, syncopation=0.35,
        rhythm_variety=0.50, harmony_note_probability=0.45,
        ornament_probability=0.06,
    ).render(chords, key, dur)
    instruments["Shimmer"] = HI_SYNTH

    path = os.path.join(OUT, "darkwave_phrygian.mid")
    export_multitrack_midi(tracks, path, bpm=BPM, instruments=instruments, key=KEY)
    print(f"  darkwave: {len(tracks)} tracks -> {path}")


def demo_witch_short():
    """Shorter, denser version — 4 bars, different progression."""
    key = _key()
    chords = chords_main
    dur = dur_main

    params_lead = GeneratorParams(density=0.55, key_range_low=60, key_range_high=80)
    params_bass = GeneratorParams(density=0.40, key_range_low=32, key_range_high=48)
    params_pad = GeneratorParams(density=0.22, key_range_low=40, key_range_high=64)

    tracks = {}
    instruments = {}

    tracks["Lead"] = MelodyGenerator(
        params_lead,
        phrase_contour="wave", motif_probability=0.50,
        syncopation=0.30, rhythm_variety=0.50,
        harmony_note_probability=0.55, direction_bias=-0.1,
    ).render(chords, key, dur)
    instruments["Lead"] = 82  # Lead 2 (sawtooth)

    tracks["Bass"] = MelodyGenerator(
        params_bass,
        harmony_note_probability=0.90, steps_probability=0.88,
        note_repetition_probability=0.25, rhythm_variety=0.25,
        syncopation=0.15,
    ).render(chords, key, dur)
    instruments["Bass"] = BASS_SYNTH

    tracks["Pad"] = MelodyGenerator(
        params_pad,
        harmony_note_probability=0.92, random_movement=0.10,
        note_repetition_probability=0.35, rhythm_variety=0.08,
    ).render(chords, key, dur)
    instruments["Pad"] = 90  # Pad 2 (warm)

    path = os.path.join(OUT, "witch_phrygian.mid")
    export_multitrack_midi(tracks, path, bpm=BPM + 4, instruments=instruments, key=KEY)
    print(f"  witch:    {len(tracks)} tracks -> {path}")


if __name__ == "__main__":
    print("Dark wave / Phrygian / Witch house demos...")
    demo_darkwave()
    demo_witch_short()
    print("Done.")
