"""Orchestral demos using MelodyGenerator for all voices."""

import os
from melodica import Scale, Mode
from melodica.types import parse_progression
from melodica.generators.melody import MelodyGenerator
from melodica.generators import GeneratorParams
from melodica.midi import export_multitrack_midi

KEY = Scale(root=0, mode=Mode.MAJOR)
BPM = 100
OUT = "output/melody_demos"
os.makedirs(OUT, exist_ok=True)

# GM instrument numbers
VIOLIN = 40
CELLO = 42
FLUTE = 73
OBOE = 68
FRENCH_HORN = 60
TRUMPET = 56
TIMPANI = 47
STRING_ENS = 48
CHOIR = 52
PIZZ_STR = 45


def _chords(prog: str, bars: int = 8):
    """Parse progression, return (chords, duration)."""
    return parse_progression(prog, KEY), bars * 4.0


# -----------------------------------------------------------------------
# 1. Epic Opener — full orchestra, heroic
# -----------------------------------------------------------------------
def demo_epic_opener():
    chords, dur = _chords("I V vi IV I iii IV V")
    params_bright = GeneratorParams(density=0.65, key_range_low=60, key_range_high=84)
    params_mid = GeneratorParams(density=0.55, key_range_low=48, key_range_high=72)
    params_low = GeneratorParams(density=0.45, key_range_low=36, key_range_high=60)
    params_pad = GeneratorParams(density=0.30, key_range_low=36, key_range_high=72)

    tracks = {}
    instruments = {}

    # Lead: violins, arch contour
    tracks["Violins Lead"] = MelodyGenerator(
        params_bright, phrase_contour="arch", motif_probability=0.55,
        syncopation=0.15, rhythm_variety=0.4, ornament_probability=0.10,
    ).render(chords, KEY, dur)
    instruments["Violins Lead"] = VIOLIN

    # Counter-melody: oboe, spiral rising
    tracks["Oboe"] = MelodyGenerator(
        params_bright, phrase_contour="spiral", direction_bias=0.15,
        motif_probability=0.45, syncopation=0.20, rhythm_variety=0.35,
        harmony_note_probability=0.55,
    ).render(chords, KEY, dur)
    instruments["Oboe"] = OBOE

    # Violas: mid-range, wave contour
    tracks["Violas"] = MelodyGenerator(
        params_mid, phrase_contour="wave", motif_probability=0.40,
        rhythm_variety=0.30, harmony_note_probability=0.70,
    ).render(chords, KEY, dur)
    instruments["Violas"] = STRING_ENS

    # Cellos: lower, stepwise
    tracks["Cellos"] = MelodyGenerator(
        params_low, phrase_contour="rise_fall", motif_probability=0.35,
        steps_probability=0.80, harmony_note_probability=0.75,
        rhythm_variety=0.25,
    ).render(chords, KEY, dur)
    instruments["Cellos"] = CELLO

    # Horns: sustained, low movement
    tracks["French Horns"] = MelodyGenerator(
        params_pad, phrase_contour="arch", random_movement=0.20,
        harmony_note_probability=0.85, note_repetition_probability=0.25,
        rhythm_variety=0.15,
    ).render(chords, KEY, dur)
    instruments["French Horns"] = FRENCH_HORN

    path = os.path.join(OUT, "orch_epic_opener.mid")
    export_multitrack_midi(tracks, path, bpm=BPM, instruments=instruments, key=KEY)
    print(f"  epic_opener: {len(tracks)} tracks -> {path}")


# -----------------------------------------------------------------------
# 2. Dark Forest — minor key, mysterious
# -----------------------------------------------------------------------
def demo_dark_forest():
    key = Scale(root=9, mode=Mode.NATURAL_MINOR)  # A minor
    chords = parse_progression("i VI III VII i iv VI VII", key)
    dur = 32.0

    params_high = GeneratorParams(density=0.55, key_range_low=67, key_range_high=88)
    params_mid = GeneratorParams(density=0.50, key_range_low=48, key_range_high=72)
    params_low = GeneratorParams(density=0.40, key_range_low=36, key_range_high=60)
    params_drone = GeneratorParams(density=0.20, key_range_low=36, key_range_high=55)

    tracks = {}
    instruments = {}

    # Flute: ethereal melody
    tracks["Flute"] = MelodyGenerator(
        params_high, phrase_contour="wave", motif_probability=0.50,
        syncopation=0.25, rhythm_variety=0.45, ornament_probability=0.12,
        direction_bias=-0.15,  # slightly descending
    ).render(chords, key, dur)
    instruments["Flute"] = FLUTE

    # Strings: counter-melody
    tracks["Strings"] = MelodyGenerator(
        params_mid, phrase_contour="spiral", motif_probability=0.40,
        syncopation=0.15, rhythm_variety=0.30, harmony_note_probability=0.60,
    ).render(chords, key, dur)
    instruments["Strings"] = STRING_ENS

    # Cello: bass line
    tracks["Cello"] = MelodyGenerator(
        params_low, phrase_contour="rise_fall", steps_probability=0.85,
        harmony_note_probability=0.80, motif_probability=0.30,
        rhythm_variety=0.20, note_repetition_probability=0.20,
    ).render(chords, key, dur)
    instruments["Cello"] = CELLO

    # Horn: sustained pads
    tracks["Horn"] = MelodyGenerator(
        params_drone, random_movement=0.15, harmony_note_probability=0.90,
        note_repetition_probability=0.30, rhythm_variety=0.10,
    ).render(chords, key, dur)
    instruments["Horn"] = FRENCH_HORN

    path = os.path.join(OUT, "orch_dark_forest.mid")
    export_multitrack_midi(tracks, path, bpm=85, instruments=instruments, key=key)
    print(f"  dark_forest: {len(tracks)} tracks -> {path}")


# -----------------------------------------------------------------------
# 3. Waltz — 3/4 feel, light & elegant
# -----------------------------------------------------------------------
def demo_waltz():
    chords = parse_progression("I IV V I vi ii V I", KEY)
    dur = 32.0

    params_mel = GeneratorParams(density=0.60, key_range_low=62, key_range_high=86)
    params_acc = GeneratorParams(density=0.55, key_range_low=55, key_range_high=76)
    params_bass = GeneratorParams(density=0.45, key_range_low=36, key_range_high=55)
    params_pad = GeneratorParams(density=0.25, key_range_low=48, key_range_high=72)

    tracks = {}
    instruments = {}

    # Solo violin: ornamental melody
    tracks["Solo Violin"] = MelodyGenerator(
        params_mel, phrase_contour="arch", motif_probability=0.55,
        syncopation=0.10, rhythm_variety=0.50, ornament_probability=0.20,
    ).render(chords, KEY, dur)
    instruments["Solo Violin"] = VIOLIN

    # Flute: light counter
    tracks["Flute"] = MelodyGenerator(
        params_acc, phrase_contour="wave", motif_probability=0.40,
        syncopation=0.15, rhythm_variety=0.35, harmony_note_probability=0.55,
    ).render(chords, KEY, dur)
    instruments["Flute"] = FLUTE

    # Pizzicato strings: rhythmic bass
    tracks["Pizz Bass"] = MelodyGenerator(
        params_bass, harmony_note_probability=0.85,
        note_repetition_probability=0.25, rhythm_variety=0.30,
        motif_probability=0.35,
    ).render(chords, KEY, dur)
    instruments["Pizz Bass"] = PIZZ_STR

    # String ensemble: sustained harmony
    tracks["Strings Pad"] = MelodyGenerator(
        params_pad, harmony_note_probability=0.90, random_movement=0.15,
        note_repetition_probability=0.30, rhythm_variety=0.10,
    ).render(chords, KEY, dur)
    instruments["Strings Pad"] = STRING_ENS

    path = os.path.join(OUT, "orch_waltz.mid")
    export_multitrack_midi(tracks, path, bpm=130, instruments=instruments, key=KEY)
    print(f"  waltz:       {len(tracks)} tracks -> {path}")


# -----------------------------------------------------------------------
# 4. Fanfare — brass, powerful
# -----------------------------------------------------------------------
def demo_fanfare():
    chords = parse_progression("I IV I V I IV ii V", KEY)
    dur = 32.0

    params_lead = GeneratorParams(density=0.70, key_range_low=58, key_range_high=82)
    params_brass = GeneratorParams(density=0.55, key_range_low=46, key_range_high=70)
    params_low = GeneratorParams(density=0.45, key_range_low=34, key_range_high=58)
    params_timp = GeneratorParams(density=0.35, key_range_low=36, key_range_high=48)

    tracks = {}
    instruments = {}

    # Trumpet: heroic lead
    tracks["Trumpet"] = MelodyGenerator(
        params_lead, phrase_contour="arch", motif_probability=0.60,
        direction_bias=0.15, rhythm_variety=0.40, syncopation=0.10,
    ).render(chords, KEY, dur)
    instruments["Trumpet"] = TRUMPET

    # French horns: mid brass
    tracks["Horns"] = MelodyGenerator(
        params_brass, phrase_contour="rise", motif_probability=0.45,
        harmony_note_probability=0.70, rhythm_variety=0.30,
    ).render(chords, KEY, dur)
    instruments["Horns"] = FRENCH_HORN

    # Low brass
    tracks["Low Brass"] = MelodyGenerator(
        params_low, harmony_note_probability=0.85, steps_probability=0.80,
        motif_probability=0.30, rhythm_variety=0.20,
        note_repetition_probability=0.22,
    ).render(chords, KEY, dur)
    instruments["Low Brass"] = 57  # Trombone

    # Timpani: rhythmic hits
    tracks["Timpani"] = MelodyGenerator(
        params_timp, harmony_note_probability=0.90,
        note_repetition_probability=0.35, rhythm_variety=0.35,
        random_movement=0.15,
    ).render(chords, KEY, dur)
    instruments["Timpani"] = TIMPANI

    path = os.path.join(OUT, "orch_fanfare.mid")
    export_multitrack_midi(tracks, path, bpm=110, instruments=instruments, key=KEY)
    print(f"  fanfare:     {len(tracks)} tracks -> {path}")


# -----------------------------------------------------------------------
# 5. Cinematic Tension — slow, building
# -----------------------------------------------------------------------
def demo_tension():
    key = Scale(root=0, mode=Mode.DORIAN)
    chords = parse_progression("i IV i VII IV i VII i", key)
    dur = 32.0

    params_high = GeneratorParams(density=0.40, key_range_low=65, key_range_high=86)
    params_mid = GeneratorParams(density=0.45, key_range_low=48, key_range_high=72)
    params_low = GeneratorParams(density=0.35, key_range_low=36, key_range_high=55)
    params_drone = GeneratorParams(density=0.15, key_range_low=36, key_range_high=52)

    tracks = {}
    instruments = {}

    # Violin: slow rising melody
    tracks["Violin"] = MelodyGenerator(
        params_high, phrase_contour="spiral", direction_bias=0.2,
        motif_probability=0.50, syncopation=0.20, rhythm_variety=0.45,
        ornament_probability=0.08,
    ).render(chords, key, dur)
    instruments["Violin"] = VIOLIN

    # Choir: sustained pads
    tracks["Choir"] = MelodyGenerator(
        params_drone, harmony_note_probability=0.92, random_movement=0.10,
        note_repetition_probability=0.35, rhythm_variety=0.05,
    ).render(chords, key, dur)
    instruments["Choir"] = CHOIR

    # Cellos: mid voice
    tracks["Cellos"] = MelodyGenerator(
        params_mid, phrase_contour="wave", motif_probability=0.35,
        harmony_note_probability=0.65, rhythm_variety=0.25,
    ).render(chords, key, dur)
    instruments["Cellos"] = CELLO

    # Bass strings
    tracks["Bass"] = MelodyGenerator(
        params_low, harmony_note_probability=0.85, steps_probability=0.85,
        motif_probability=0.25, rhythm_variety=0.15,
        note_repetition_probability=0.25,
    ).render(chords, key, dur)
    instruments["Bass"] = STRING_ENS

    path = os.path.join(OUT, "orch_tension.mid")
    export_multitrack_midi(tracks, path, bpm=72, instruments=instruments, key=key)
    print(f"  tension:     {len(tracks)} tracks -> {path}")


if __name__ == "__main__":
    print("Generating orchestral demos...")
    demo_epic_opener()
    demo_dark_forest()
    demo_waltz()
    demo_fanfare()
    demo_tension()
    print("Done.")
