# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_sunny_side.py — Sunny Side Up

8-track cheerful jazz album. Bebop, swing, blues, Latin, smooth.
MIDI output only. Uses FunctionalHMMHarmonizer for jazz harmony.
"""

import random
from pathlib import Path

from melodica import types
from melodica.types import Scale, Mode, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.sax_solo import SaxSoloGenerator
from melodica.generators.swing import SwingGenerator
from melodica.generators.stride_piano import StridePianoGenerator
from melodica.generators.montuno import MontunoGenerator
from melodica.generators.blues_lick import BluesLickGenerator
from melodica.generators.boogie_woogie import BoogieWoogieGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer

# GM Programs
PIANO = 0
EPIANO = 4
ORGAN = 16
JAZZ_GUITAR = 26
ACOUSTIC_BASS = 32
FRETLESS_BASS = 35
TRUMPET = 56
TROMBONE = 57
SOPRANO_SAX = 64
ALTO_SAX = 65
TENOR_SAX = 66
BARI_SAX = 67
CLARINET = 71
FLUTE = 73
VIBRAPHONE = 11
DRUMS = 0  # ch.10 handled by instruments map

random.seed(2028)
OUT = Path("output/sunny_side")
OUT.mkdir(parents=True, exist_ok=True)

_harmonizer = CoupledHMMHarmonizer(beam_width=14, chord_change="half")


def _off(notes, offset):
    return [NoteInfo(pitch=n.pitch, start=n.start + offset,
                     duration=n.duration, velocity=n.velocity)
            for n in notes]


def _get_chords(scale: Scale, dur: float):
    degs = scale.degrees()
    guide = [NoteInfo(pitch=60 + int(degs[0]), start=0.0, duration=dur)]
    return _harmonizer.harmonize(melody=guide, initial_scale=scale, duration_beats=dur)


def _master(raw: dict, bpm: float, lufs: float = -18.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.8, "comp": 0.65, "bass": 0.7, "sax": 0.75,
        "trumpet": 0.7, "drums": 0.6, "stride": 0.7, "boogie": 0.65,
        "guitar": 0.6, "montuno": 0.6, "blues": 0.7, "vibes": 0.55,
        "flute": 0.6, "clarinet": 0.6, "swing": 0.5, "organ": 0.55,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def _export(tracks: dict, path: Path, bpm: float, key: Scale, instruments: dict):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)


# =====================================================================
# Track 1 — Sunny Side Up
# F Major, 160 BPM. Stride piano + walking bass + alto sax. Bright opener.
def produce_01_sunny_side_up():
    print("--- 01_Sunny_Side_Up ---")
    bpm, dur = 160, 128.0
    key = Scale(5, Mode.IONIAN)
    chords = _get_chords(key, dur)

    stride = StridePianoGenerator(
        GeneratorParams(density=0.12, key_range_low=40, key_range_high=88),
        pattern="standard", chromatic_approach=True, ornaments=True
    ).render(chords, key, dur)

    bass = WalkingBassGenerator(
        GeneratorParams(density=0.08, key_range_low=24, key_range_high=38),
        approach_style="mixed", swing_eighth_ratio=0.67
    ).render(chords, key, dur)

    sax = SaxSoloGenerator(
        GeneratorParams(density=0.1, velocity_range=(50, 90), key_range_low=60, key_range_high=84),
        style="bebop", chromaticism=0.6, blues_notes=True
    ).render(chords, key, dur - 24.0)
    sax = _off(sax, 16.0)

    swing = SwingGenerator(
        GeneratorParams(density=0.06, key_range_low=72, key_range_high=88),
        swing_ratio=0.67, pitch_strategy="chord_tone", accent_pattern="backbeat"
    ).render(chords, key, dur - 48.0)
    swing = _off(swing, 32.0)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.08), style="jazz", groove_swing=0.67,
        fill_frequency=0.15, auto_fills=True
    ).render(chords, key, dur)

    _export({"stride": stride, "bass": bass, "sax": sax, "vibes": swing, "drums": drums},
            OUT / "01_Sunny_Side_Up.mid", bpm, key,
            {"stride": PIANO, "bass": ACOUSTIC_BASS, "sax": ALTO_SAX, "vibes": VIBRAPHONE, "drums": DRUMS})


# =====================================================================
# Track 2 — Café on the Corner
# Bb Major, 120 BPM. Piano comp + walking bass + flute. Smooth bossa feel.
def produce_02_cafe():
    print("--- 02_Cafe_on_the_Corner ---")
    bpm, dur = 120, 160.0
    key = Scale(10, Mode.IONIAN)
    chords = _get_chords(key, dur)

    comp = PianoCompGenerator(
        GeneratorParams(density=0.06, key_range_low=60, key_range_high=84),
        comp_style="bossa", voicing_type="rootless", accent_pattern="syncopated"
    ).render(chords, key, dur)

    bass = WalkingBassGenerator(
        GeneratorParams(density=0.06, key_range_low=28, key_range_high=44),
        approach_style="diatonic", swing_eighth_ratio=0.6
    ).render(chords, key, dur)

    flute = MelodyGenerator(
        GeneratorParams(density=0.06, velocity_range=(48, 72)),
        phrase_length=8.0, note_range_low=72, note_range_high=96,
        register_smoothness=0.85, harmony_note_probability=0.35,
        steps_probability=0.8
    ).render(chords, key, dur - 32.0)
    flute = _off(flute, 16.0)

    guitar = PianoCompGenerator(
        GeneratorParams(density=0.04, key_range_low=48, key_range_high=60),
        comp_style="bossa", voicing_type="shell"
    ).render(chords, key, dur - 40.0)
    guitar = _off(guitar, 24.0)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.04), style="jazz", groove_swing=0.55,
        fill_frequency=0.1, auto_fills=True
    ).render(chords, key, dur)

    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.03), pattern="jazz", target="snare",
        ghost_velocity=30, ghost_density=0.4
    ).render(chords, key, dur)

    _export({"comp": comp, "bass": bass, "flute": flute, "guitar": guitar, "drums": drums, "ghosts": ghosts},
            OUT / "02_Cafe_on_the_Corner.mid", bpm, key,
            {"comp": EPIANO, "bass": FRETLESS_BASS, "flute": FLUTE, "guitar": JAZZ_GUITAR, "drums": DRUMS, "ghosts": DRUMS})


# =====================================================================
# Track 3 — Blues for Breakfast
# Eb Blues, 140 BPM. Boogie woogie + blues licks + tenor sax. Shuffle.
def produce_03_blues_breakfast():
    print("--- 03_Blues_for_Breakfast ---")
    bpm, dur = 140, 144.0
    key = Scale(3, Mode.BLUES)
    chords = _get_chords(key, dur)

    boogie = BoogieWoogieGenerator(
        GeneratorParams(density=0.12, key_range_low=24, key_range_high=72),
        pattern="standard", swing=0.67, octave_bass=True
    ).render(chords, key, dur)

    blues = BluesLickGenerator(
        GeneratorParams(density=0.08, velocity_range=(50, 85), key_range_low=48, key_range_high=72),
        lick_style="standard", phrase_length=4, rest_probability=0.25,
        enclosure_probability=0.3, bend_probability=0.2
    ).render(chords, key, dur - 32.0)
    blues = _off(blues, 16.0)

    sax = SaxSoloGenerator(
        GeneratorParams(density=0.07, velocity_range=(48, 88), key_range_low=54, key_range_high=78),
        style="bebop", blues_notes=True, chromaticism=0.5
    ).render(chords, key, dur - 48.0)
    sax = _off(sax, 32.0)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.1), style="jazz", groove_swing=0.67,
        fill_frequency=0.2, auto_fills=True
    ).render(chords, key, dur)

    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.05), pattern="jazz", target="snare",
        ghost_velocity=35, ghost_density=0.5
    ).render(chords, key, dur)

    _export({"boogie": boogie, "blues": blues, "sax": sax, "drums": drums, "ghosts": ghosts},
            OUT / "03_Blues_for_Breakfast.mid", bpm, key,
            {"boogie": PIANO, "blues": TRUMPET, "sax": TENOR_SAX, "drums": DRUMS, "ghosts": DRUMS})


# =====================================================================
# Track 4 — Park Bench Swing
# G Dorian, 130 BPM. Piano comp + walking bass + vibes. Cool medium swing.
def produce_04_park_bench():
    print("--- 04_Park_Bench_Swing ---")
    bpm, dur = 130, 160.0
    key = Scale(7, Mode.DORIAN)
    chords = _get_chords(key, dur)

    comp = PianoCompGenerator(
        GeneratorParams(density=0.07, key_range_low=48, key_range_high=84),
        comp_style="jazz", voicing_type="shell", accent_pattern="charleston",
        chord_density=0.8
    ).render(chords, key, dur)

    bass = WalkingBassGenerator(
        GeneratorParams(density=0.07, key_range_low=28, key_range_high=44),
        approach_style="mixed", swing_eighth_ratio=0.67
    ).render(chords, key, dur)

    vibes = MelodyGenerator(
        GeneratorParams(density=0.06, velocity_range=(45, 70)),
        phrase_length=8.0, note_range_low=60, note_range_high=84,
        register_smoothness=0.85, harmony_note_probability=0.4,
        steps_probability=0.82
    ).render(chords, key, dur - 24.0)
    vibes = _off(vibes, 12.0)

    sax = SaxSoloGenerator(
        GeneratorParams(density=0.06, velocity_range=(46, 80), key_range_low=54, key_range_high=78),
        style="smooth", chromaticism=0.4
    ).render(chords, key, dur - 64.0)
    sax = _off(sax, 48.0)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.06), style="jazz", groove_swing=0.67,
        fill_frequency=0.12, auto_fills=True
    ).render(chords, key, dur)

    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.03), pattern="jazz", target="snare",
        ghost_velocity=28, ghost_density=0.35
    ).render(chords, key, dur)

    _export({"comp": comp, "bass": bass, "vibes": vibes, "sax": sax, "drums": drums, "ghosts": ghosts},
            OUT / "04_Park_Bench_Swing.mid", bpm, key,
            {"comp": EPIANO, "bass": ACOUSTIC_BASS, "vibes": VIBRAPHONE, "sax": TENOR_SAX, "drums": DRUMS, "ghosts": DRUMS})


# =====================================================================
# Track 5 — Latin Lunch
# A Minor, 150 BPM. Montuno + walking bass + trumpet. Latin jazz heat.
def produce_05_latin_lunch():
    print("--- 05_Latin_Lunch ---")
    bpm, dur = 150, 128.0
    key = Scale(9, Mode.DORIAN)
    chords = _get_chords(key, dur)

    montuno = MontunoGenerator(
        GeneratorParams(density=0.1, key_range_low=60, key_range_high=84),
        pattern="salsa", clave_type="son_23", octave_doubling=False
    ).render(chords, key, dur)

    bass = WalkingBassGenerator(
        GeneratorParams(density=0.07, key_range_low=28, key_range_high=44),
        approach_style="diatonic", swing_eighth_ratio=0.55
    ).render(chords, key, dur)

    trumpet = SaxSoloGenerator(
        GeneratorParams(density=0.08, velocity_range=(52, 92), key_range_low=58, key_range_high=82),
        style="fusion", chromaticism=0.5, blues_notes=True
    ).render(chords, key, dur - 24.0)
    trumpet = _off(trumpet, 16.0)

    comp = PianoCompGenerator(
        GeneratorParams(density=0.05, key_range_low=48, key_range_high=72),
        comp_style="jazz", voicing_type="shell"
    ).render(chords, key, dur - 40.0)
    comp = _off(comp, 24.0)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.08), style="jazz", groove_swing=0.55,
        fill_frequency=0.15, auto_fills=True
    ).render(chords, key, dur)

    _export({"montuno": montuno, "bass": bass, "trumpet": trumpet, "comp": comp, "drums": drums},
            OUT / "05_Latin_Lunch.mid", bpm, key,
            {"montuno": EPIANO, "bass": ACOUSTIC_BASS, "trumpet": TRUMPET, "comp": JAZZ_GUITAR, "drums": DRUMS})


# =====================================================================
# Track 6 — Sunday Stroll
# C Lydian, 110 BPM. Piano comp + fretless bass + soprano sax. Smooth.
def produce_06_sunday_stroll():
    print("--- 06_Sunday_Stroll ---")
    bpm, dur = 110, 176.0
    key = Scale(0, Mode.LYDIAN)
    chords = _get_chords(key, dur)

    comp = PianoCompGenerator(
        GeneratorParams(density=0.05, key_range_low=60, key_range_high=84),
        comp_style="pop", voicing_type="close", accent_pattern="syncopated"
    ).render(chords, key, dur)

    bass = WalkingBassGenerator(
        GeneratorParams(density=0.05, key_range_low=24, key_range_high=40),
        approach_style="chromatic", swing_eighth_ratio=0.55
    ).render(chords, key, dur)

    sax = SaxSoloGenerator(
        GeneratorParams(density=0.05, velocity_range=(44, 75), key_range_low=60, key_range_high=84),
        style="smooth", vibrato_depth=0.4, chromaticism=0.3
    ).render(chords, key, dur - 32.0)
    sax = _off(sax, 20.0)

    guitar = PianoCompGenerator(
        GeneratorParams(density=0.04, key_range_low=48, key_range_high=60),
        comp_style="bossa", voicing_type="rootless"
    ).render(chords, key, dur - 48.0)
    guitar = _off(guitar, 32.0)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.03), style="jazz", groove_swing=0.55,
        fill_frequency=0.08, auto_fills=True
    ).render(chords, key, dur)

    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.02), pattern="jazz", target="snare",
        ghost_velocity=25, ghost_density=0.3
    ).render(chords, key, dur)

    _export({"comp": comp, "bass": bass, "sax": sax, "guitar": guitar, "drums": drums, "ghosts": ghosts},
            OUT / "06_Sunday_Stroll.mid", bpm, key,
            {"comp": EPIANO, "bass": FRETLESS_BASS, "sax": SOPRANO_SAX, "guitar": JAZZ_GUITAR, "drums": DRUMS, "ghosts": DRUMS})


# =====================================================================
# Track 7 — Jumping Beans
# D Bebop Dominant, 180 BPM. Stride + walking bass + bari sax. Burner.
def produce_07_jumping_beans():
    print("--- 07_Jumping_Beans ---")
    bpm, dur = 180, 112.0
    key = Scale(2, Mode.BEBOP_DOMINANT)
    chords = _get_chords(key, dur)

    stride = StridePianoGenerator(
        GeneratorParams(density=0.14, key_range_low=40, key_range_high=88),
        pattern="tatum", chromatic_approach=True, ornaments=True
    ).render(chords, key, dur)

    bass = WalkingBassGenerator(
        GeneratorParams(density=0.1, key_range_low=24, key_range_high=38),
        approach_style="mixed", swing_eighth_ratio=0.67
    ).render(chords, key, dur)

    sax = SaxSoloGenerator(
        GeneratorParams(density=0.12, velocity_range=(55, 95), key_range_low=42, key_range_high=66),
        style="bebop", chromaticism=0.7, blues_notes=True
    ).render(chords, key, dur - 16.0)
    sax = _off(sax, 8.0)

    trumpet = SaxSoloGenerator(
        GeneratorParams(density=0.08, velocity_range=(50, 90), key_range_low=58, key_range_high=82),
        style="fusion", chromaticism=0.5
    ).render(chords, key, dur - 48.0)
    trumpet = _off(trumpet, 32.0)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.12), style="jazz", groove_swing=0.67,
        fill_frequency=0.2, auto_fills=True
    ).render(chords, key, dur)

    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.06), pattern="jazz", target="snare",
        ghost_velocity=35, ghost_density=0.55
    ).render(chords, key, dur)

    _export({"stride": stride, "bass": bass, "sax": sax, "trumpet": trumpet, "drums": drums, "ghosts": ghosts},
            OUT / "07_Jumping_Beans.mid", bpm, key,
            {"stride": PIANO, "bass": ACOUSTIC_BASS, "sax": BARI_SAX, "trumpet": TRUMPET, "drums": DRUMS, "ghosts": DRUMS})


# =====================================================================
# Track 8 — Last Call
# F Mixolydian, 155 BPM. Full band. Piano comp + walking bass + tenor sax
# + trumpet + vibes. Hard bop closer.
def produce_08_last_call():
    print("--- 08_Last_Call ---")
    bpm, dur = 155, 136.0
    key = Scale(5, Mode.MIXOLYDIAN)
    chords = _get_chords(key, dur)

    comp = PianoCompGenerator(
        GeneratorParams(density=0.08, key_range_low=48, key_range_high=84),
        comp_style="jazz", voicing_type="shell", accent_pattern="2_4",
        chord_density=0.85
    ).render(chords, key, dur)

    bass = WalkingBassGenerator(
        GeneratorParams(density=0.08, key_range_low=28, key_range_high=48),
        approach_style="mixed", swing_eighth_ratio=0.67
    ).render(chords, key, dur)

    sax = SaxSoloGenerator(
        GeneratorParams(density=0.09, velocity_range=(50, 88), key_range_low=54, key_range_high=78),
        style="bebop", chromaticism=0.6, blues_notes=True
    ).render(chords, key, dur - 20.0)
    sax = _off(sax, 12.0)

    trumpet = SaxSoloGenerator(
        GeneratorParams(density=0.06, velocity_range=(48, 85), key_range_low=58, key_range_high=82),
        style="fusion", chromaticism=0.4
    ).render(chords, key, dur - 56.0)
    trumpet = _off(trumpet, 40.0)

    vibes = SwingGenerator(
        GeneratorParams(density=0.05, key_range_low=60, key_range_high=84),
        swing_ratio=0.67, pitch_strategy="chord_tone", accent_pattern="backbeat"
    ).render(chords, key, dur - 48.0)
    vibes = _off(vibes, 32.0)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.1), style="jazz", groove_swing=0.67,
        fill_frequency=0.18, auto_fills=True
    ).render(chords, key, dur)

    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.04), pattern="jazz", target="snare",
        ghost_velocity=32, ghost_density=0.45
    ).render(chords, key, dur)

    _export({"comp": comp, "bass": bass, "sax": sax, "trumpet": trumpet, "vibes": vibes, "drums": drums, "ghosts": ghosts},
            OUT / "08_Last_Call.mid", bpm, key,
            {"comp": PIANO, "bass": ACOUSTIC_BASS, "sax": TENOR_SAX,
             "trumpet": TRUMPET, "vibes": VIBRAPHONE, "drums": DRUMS, "ghosts": DRUMS})


def main():
    produce_01_sunny_side_up()
    produce_02_cafe()
    produce_03_blues_breakfast()
    produce_04_park_bench()
    produce_05_latin_lunch()
    produce_06_sunday_stroll()
    produce_07_jumping_beans()
    produce_08_last_call()
    print(f"\nAlbum 'Sunny Side Up' complete. Files in {OUT}/")


if __name__ == "__main__":
    main()
