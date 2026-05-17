"""Test melody rework — generates comparison MIDIs (old defaults vs new)."""

from melodica import harmonize, Note, Scale, Mode, notes_to_midi, ChordLabel, Quality
from melodica.types import parse_progression
from melodica.generators.melody import MelodyGenerator
from melodica.generators import GeneratorParams

KEY = Scale(root=0, mode=Mode.MAJOR)
BPM = 110
DURATION = 16.0  # 4 bars

# C major diatonic progression: I - vi - IV - V
CHORDS = parse_progression("I vi IV V", KEY)


def generate_new_default():
    """MelodyGenerator with new defaults — no manual tuning."""
    gen = MelodyGenerator(GeneratorParams(density=0.6))
    notes = gen.render(CHORDS, KEY, DURATION)
    path = "output/melody_demos/rework_new_default.mid"
    notes_to_midi(notes, path, bpm=BPM)
    print(f"  new_default: {len(notes)} notes -> {path}")


def generate_old_default():
    """MelodyGenerator with old defaults (before rework)."""
    gen = MelodyGenerator(
        GeneratorParams(density=0.6),
        random_movement=0.80,
        after_leap="any",
        rhythm_variety=0.0,
        syncopation=0.0,
        phrase_length=0.0,
        motif_probability=0.0,
        motif_variation="transpose",
        climax="first_plus_maj3",
    )
    notes = gen.render(CHORDS, KEY, DURATION)
    path = "output/melody_demos/rework_old_default.mid"
    notes_to_midi(notes, path, bpm=BPM)
    print(f"  old_default: {len(notes)} notes -> {path}")


def generate_wave_contour():
    """Wave contour — double arch."""
    gen = MelodyGenerator(
        GeneratorParams(density=0.65),
        phrase_contour="wave",
    )
    notes = gen.render(CHORDS, KEY, DURATION)
    path = "output/melody_demos/rework_wave.mid"
    notes_to_midi(notes, path, bpm=BPM)
    print(f"  wave:        {len(notes)} notes -> {path}")


def generate_spiral_contour():
    """Spiral contour — ascending with dips."""
    gen = MelodyGenerator(
        GeneratorParams(density=0.65),
        phrase_contour="spiral",
        direction_bias=0.2,
    )
    notes = gen.render(CHORDS, KEY, DURATION)
    path = "output/melody_demos/rework_spiral.mid"
    notes_to_midi(notes, path, bpm=BPM)
    print(f"  spiral:      {len(notes)} notes -> {path}")


def generate_syncopated():
    """High syncopation + motif."""
    gen = MelodyGenerator(
        GeneratorParams(density=0.75),
        syncopation=0.35,
        rhythm_variety=0.5,
        motif_probability=0.60,
        ornament_probability=0.15,
    )
    notes = gen.render(CHORDS, KEY, DURATION)
    path = "output/melody_demos/rework_syncopated.mid"
    notes_to_midi(notes, path, bpm=BPM)
    print(f"  syncopated:  {len(notes)} notes -> {path}")


def generate_32bars():
    """Longer phrase — 32 beats (8 bars) to test motif carryover."""
    long_chords = parse_progression("I vi IV V I V vi IV", KEY)
    gen = MelodyGenerator(
        GeneratorParams(density=0.65),
        motif_probability=0.50,
        syncopation=0.20,
        rhythm_variety=0.4,
    )
    notes = gen.render(long_chords, KEY, 32.0)
    path = "output/melody_demos/rework_32bars.mid"
    notes_to_midi(notes, path, bpm=BPM)
    print(f"  32bars:      {len(notes)} notes -> {path}")


if __name__ == "__main__":
    import os
    os.makedirs("output/melody_demos", exist_ok=True)

    print("Generating test melodies...")
    generate_old_default()
    generate_new_default()
    generate_wave_contour()
    generate_spiral_contour()
    generate_syncopated()
    generate_32bars()
    print("Done. Files in output/melody_demos/")
