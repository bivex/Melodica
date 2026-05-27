"""Dramatic arc demo — same melody with and without drama_shape."""

import os
from melodica import Scale, Mode
from melodica.types import parse_progression
from melodica.generators.melody import MelodyGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators import GeneratorParams
from melodica.midi import export_multitrack_midi

OUT = "output/melody_demos"
os.makedirs(OUT, exist_ok=True)

KEY = Scale(root=0, mode=Mode.NATURAL_MINOR)  # A minor
BPM = 90
DUR = 48.0  # 12 bars

chords = parse_progression("i VI III VII i iv VI VII i VI iv V i iv VII i V", KEY)

# GM instruments
VIOLIN = 40; CELLO = 42; CHOIR = 52; STRING_ENS = 48
SYNTH_BASS = 38; PAD = 89; ATMOS = 99

SHAPES = ["none", "dramatic", "tension_release", "epic"]


def make_demo(shape, label):
    tracks = {}
    instruments = {}

    params_lead = GeneratorParams(density=0.50, key_range_low=62, key_range_high=84)
    params_counter = GeneratorParams(density=0.45, key_range_low=55, key_range_high=76)
    params_bass = GeneratorParams(density=0.35, key_range_low=36, key_range_high=55)

    # Lead: dramatic arc enabled
    tracks["Lead"] = MelodyGenerator(
        params_lead,
        drama_shape=shape, drama_peak=0.72,
        phrase_contour="arch", motif_probability=0.55,
        syncopation=0.20, rhythm_variety=0.45,
        harmony_note_probability=0.50,
        ornament_probability=0.06,
    ).render(chords, KEY, DUR)
    instruments["Lead"] = VIOLIN

    # Counter: also dramatic
    tracks["Counter"] = MelodyGenerator(
        params_counter,
        drama_shape=shape, drama_peak=0.70,
        phrase_contour="wave", motif_probability=0.45,
        syncopation=0.25, rhythm_variety=0.35,
        harmony_note_probability=0.60,
    ).render(chords, KEY, DUR)
    instruments["Counter"] = CHOIR

    # Bass: minimal drama
    tracks["Bass"] = DarkBassGenerator(
        params_bass, mode="trip_hop", octave=2,
        note_duration=2.0, velocity_level=0.65,
        movement="root_fifth",
    ).render(chords, KEY, DUR)
    instruments["Bass"] = CELLO

    # Pad
    tracks["Pad"] = DarkPadGenerator(
        GeneratorParams(density=0.20, key_range_low=36, key_range_high=60),
        mode="minor_pad", chord_dur=4.0, velocity_level=0.30,
        register="low", overlap=0.4,
    ).render(chords, KEY, DUR)
    instruments["Pad"] = PAD

    path = os.path.join(OUT, f"drama_{label}.mid")
    export_multitrack_midi(tracks, path, bpm=BPM, instruments=instruments, key=KEY)

    lead_notes = len(tracks["Lead"])
    lead_range = f"{min(n.pitch for n in tracks['Lead'])}-{max(n.pitch for n in tracks['Lead'])}"
    lead_vel = f"{min(n.velocity for n in tracks['Lead'])}-{max(n.velocity for n in tracks['Lead'])}"
    print(f"  {label:18s}: lead={lead_notes} notes range={lead_range} vel={lead_vel}")


if __name__ == "__main__":
    print("Dramatic arc comparison — same melody, different shapes")
    print(f"  Key: A minor, BPM: {BPM}, Duration: {DUR} beats")
    print()
    for shape in SHAPES:
        make_demo(shape, shape)
    print("\nDone. Compare the 4 files to hear the difference.")
