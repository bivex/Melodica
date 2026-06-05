# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_what_remains.py — What Remains

8-track ambient album in Aeolian minor. Pulls at something deep —
loss, memory, the ache of empty rooms. Full arrangements with
interweaving voices, dynamic arcs, and evolving textures.

Uses the Coupled HMM Harmonizer (Engine 4).
"""

import random
from pathlib import Path

import numpy as np

from melodica import types
from melodica.types import Scale, Mode, Quality, ChordLabel, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.rest import RestGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.composer import Motif, LeitmotifRegistry
from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer

# GM Programs
PIANO = 0
HARP = 46
CELLO = 42
FLUTE = 73
PAD_WARM = 89
PAD_SPACE = 91
CHOIR = 52
BOWL = 14
NYLON_GUITAR = 24
VIBRAPHONE = 11
ACOUSTIC_BASS = 32
GLOCKENSPIEL = 9

random.seed(2027)
OUT = Path("output/what_remains")
OUT.mkdir(parents=True, exist_ok=True)

_harmonizer = CoupledHMMHarmonizer(beam_width=14, chord_change="half")

# -- Leitmotif: descending "grief" theme --
# E5 -> D5 -> C5 -> B4 -> G4
_grief_motif = Motif.from_notes([
    NoteInfo(pitch=76, start=0.0, duration=3.5, velocity=55),
    NoteInfo(pitch=74, start=3.5, duration=3.0, velocity=50),
    NoteInfo(pitch=72, start=6.5, duration=2.5, velocity=48),
    NoteInfo(pitch=71, start=9.0, duration=4.0, velocity=55),
    NoteInfo(pitch=67, start=13.0, duration=6.0, velocity=50),
])

LM = LeitmotifRegistry()
LM.register("grief", _grief_motif,
            tags=["loss", "longing"], instrument=PIANO, velocity=50)
LM.register("grief_cello", _grief_motif,
            tags=["loss", "depth"], instrument=CELLO, velocity=48)
LM.register("grief_choir", _grief_motif,
            tags=["loss", "memory"], instrument=CHOIR, velocity=40)
LM.register("grief_flute", _grief_motif,
            tags=["loss", "distance"], instrument=FLUTE, velocity=48)
LM.register("grief_harp", _grief_motif,
            tags=["loss", "fragile"], instrument=HARP, velocity=45)
LM.register("grief_bowl", _grief_motif,
            tags=["loss", "eternal"], instrument=BOWL, velocity=45)


def _off(notes, offset):
    return [
        NoteInfo(pitch=n.pitch, start=n.start + offset,
                 duration=n.duration, velocity=n.velocity)
        for n in notes
    ]


def _master(raw: dict, bpm: float, lufs: float = -20.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.8, "harp": 0.7, "flute": 0.75, "cello": 0.6,
        "pad": 0.45, "choir": 0.5, "drone": 0.4, "bowl": 0.55,
        "guitar": 0.65, "strings": 0.55, "arp": 0.5, "bass": 0.4,
        "vibes": 0.55, "motif": 0.6, "pad_space": 0.45,
        "glock": 0.45, "arp2": 0.45,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def _export(tracks: dict, path: Path, bpm: float, key: Scale, instruments: dict):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)


def _get_chords(scale: Scale, dur: float):
    degs = scale.degrees()
    guide = [NoteInfo(pitch=60 + int(degs[0]), start=0.0, duration=dur)]
    return _harmonizer.harmonize(melody=guide, initial_scale=scale, duration_beats=dur)


# =====================================================================
# Track 1 — Afterimage
# E Aeolian, 48 BPM. Cold open building to piano cry.
# Pad + cello drone underpin a sparse piano that gradually
# fills with arpeggiated harp and the motif fragment.
def produce_01_afterimage():
    print("--- 01_Afterimage ---")
    bpm, dur = 48, 220.0
    key = Scale(4, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    # Bed: two pad layers for depth
    pad = AmbientPadGenerator(GeneratorParams(density=0.07, key_range_low=36, key_range_high=60), overlap=1.0).render(chords, key, dur)
    drone = DroneGenerator(GeneratorParams(density=0.01, key_range_low=28, key_range_high=32), velocity=40).render(chords, key, dur)

    # Cello: long sustained line entering mid-first section
    cello = MelodyGenerator(GeneratorParams(density=0.04, velocity_range=(40, 58)), phrase_length=18.0, note_range_low=36, note_range_high=55, register_smoothness=0.92).render(chords, key, dur - 60.0)
    cello = _off(cello, 32.0)

    # Piano: sparse at first, then fills
    piano = MelodyGenerator(GeneratorParams(density=0.08, velocity_range=(42, 68)), phrase_length=10.0, note_range_low=60, note_range_high=84, register_smoothness=0.85, harmony_note_probability=0.5, steps_probability=0.8).render(chords, key, dur - 80.0)
    piano = _off(piano, 48.0)

    # Harp arpeggios enter later, adding movement
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.1, key_range_low=60, key_range_high=84), pattern="up", note_duration=2.5).render(chords, key, dur - 100.0)

    # Bowl: isolated strikes for color
    bowl = [NoteInfo(pitch=72, start=float(20 + i * 30), duration=8.0, velocity=45) for i in range(7)]

    # Motif: first fragment appears deep in the track
    motif = LM.render("grief_bowl", offset=170.0, transpose=4,
                       fragment_start=0.0, fragment_end=6.5, augment_factor=1.5)

    _export({"pad": pad, "drone": drone, "cello": cello, "piano": piano,
             "harp": harp, "bowl": bowl, "motif": motif},
            OUT / "01_Afterimage.mid", bpm, key,
            {"pad": PAD_SPACE, "drone": ACOUSTIC_BASS, "cello": CELLO,
             "piano": PIANO, "harp": HARP, "bowl": BOWL, "motif": BOWL})


# Track 2 — Hollow
# A Aeolian, 50 BPM. Cello-led with guitar arpeggios underneath.
# Choir swells in the second half. Motif on cello.
def produce_02_hollow():
    print("--- 02_Hollow ---")
    bpm, dur = 50, 200.0
    key = Scale(9, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    pad = AmbientPadGenerator(GeneratorParams(density=0.08, key_range_low=36, key_range_high=60), overlap=1.0).render(chords, key, dur)

    # Guitar arpeggios: slow, steady heartbeat
    guitar = ArpeggiatorGenerator(GeneratorParams(density=0.1, key_range_low=48, key_range_high=67), pattern="down", note_duration=3.0).render(chords, key, dur)

    # Cello: the lead voice, wide-ranging melody
    cello = MelodyGenerator(GeneratorParams(density=0.07, velocity_range=(42, 65)), phrase_length=12.0, note_range_low=36, note_range_high=60, register_smoothness=0.88, harmony_note_probability=0.4, steps_probability=0.85).render(chords, key, dur - 40.0)
    cello = _off(cello, 20.0)

    # Choir: enters late, wordless backing
    choir = MelodyGenerator(GeneratorParams(density=0.04, velocity_range=(32, 50)), phrase_length=18.0, note_range_low=48, note_range_high=60, register_smoothness=0.93).render(chords, key, dur - 80.0)
    choir = _off(choir, 80.0)

    # Harp: gentle fills between cello phrases
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.06, key_range_low=60, key_range_high=79), pattern="up", note_duration=4.0).render(chords, key, dur - 60.0)
    harp = _off(harp, 50.0)

    motif = LM.render("grief_cello", offset=150.0, transpose=9, augment_factor=1.5)

    _export({"pad": pad, "guitar": guitar, "cello": cello, "choir": choir,
             "harp": harp, "motif": motif},
            OUT / "02_Hollow.mid", bpm, key,
            {"pad": PAD_WARM, "guitar": NYLON_GUITAR, "cello": CELLO,
             "choir": CHOIR, "harp": HARP, "motif": CELLO})


# Track 3 — Dusk
# D Aeolian, 52 BPM. Flute and guitar in dialogue.
# Strings swell. Vibraphone countermelody.
def produce_03_dusk():
    print("--- 03_Dusk ---")
    bpm, dur = 52, 190.0
    key = Scale(2, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    pad = AmbientPadGenerator(GeneratorParams(density=0.06, key_range_low=36, key_range_high=60), overlap=1.0).render(chords, key, dur)

    # Guitar: fingerpicked arpeggios, main harmonic driver
    guitar = ArpeggiatorGenerator(GeneratorParams(density=0.12, key_range_low=48, key_range_high=72), pattern="up_down", note_duration=2.0).render(chords, key, dur)

    # Strings: sustained beds underneath
    strings = StringsEnsembleGenerator(GeneratorParams(density=0.05, key_range_low=36, key_range_high=55)).render(chords, key, dur)

    # Flute: main melody, enters after intro
    flute = MelodyGenerator(GeneratorParams(density=0.08, velocity_range=(40, 62)), phrase_length=10.0, note_range_low=72, note_range_high=84, register_smoothness=0.85, harmony_note_probability=0.5, steps_probability=0.8).render(chords, key, dur - 50.0)
    flute = _off(flute, 30.0)

    # Vibraphone: countermelody weaving through flute rests
    vibes = MelodyGenerator(GeneratorParams(density=0.06, velocity_range=(35, 52)), phrase_length=8.0, note_range_low=60, note_range_high=79, register_smoothness=0.85).render(chords, key, dur - 80.0)
    vibes = _off(vibes, 60.0)

    motif = LM.render("grief_flute", offset=130.0, transpose=2, invert=True)

    _export({"pad": pad, "guitar": guitar, "strings": strings, "flute": flute,
             "vibes": vibes, "motif": motif},
            OUT / "03_Dusk.mid", bpm, key,
            {"pad": PAD_WARM, "guitar": NYLON_GUITAR, "strings": 49,
             "flute": FLUTE, "vibes": VIBRAPHONE, "motif": FLUTE})


# Track 4 — Between
# B Aeolian, 46 BPM. More than silence — harp and piano
# in call-response. Cello drone. Bowl accents.
def produce_04_between():
    print("--- 04_Between ---")
    bpm, dur = 46, 210.0
    key = Scale(11, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    pad = AmbientPadGenerator(GeneratorParams(density=0.05, key_range_low=36, key_range_high=60), overlap=1.0).render(chords, key, dur)

    # Cello drone: foundation
    cello = DroneGenerator(GeneratorParams(density=0.01, key_range_low=36, key_range_high=40), velocity=45).render(chords, key, dur)

    # Harp arpeggios: gentle, spacious
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.08, key_range_low=60, key_range_high=84), pattern="up", note_duration=3.5).render(chords, key, dur)

    # Piano: responds to harp, more lyrical
    piano = MelodyGenerator(GeneratorParams(density=0.06, velocity_range=(40, 60)), phrase_length=14.0, note_range_low=60, note_range_high=84, register_smoothness=0.88, harmony_note_probability=0.45, steps_probability=0.82).render(chords, key, dur - 50.0)
    piano = _off(piano, 28.0)

    # Choir: breathes in the middle
    choir = MelodyGenerator(GeneratorParams(density=0.03, velocity_range=(30, 46)), phrase_length=20.0, note_range_low=48, note_range_high=60, register_smoothness=0.93).render(chords, key, dur - 80.0)
    choir = _off(choir, 56.0)

    # Bowl: punctuating moments
    bowl = [NoteInfo(pitch=67, start=float(35 + i * 38), duration=10.0, velocity=40) for i in range(5)]

    motif = LM.render("grief_harp", offset=160.0, transpose=11, augment_factor=1.5)
    motif2 = LM.render("grief", offset=180.0, transpose=11, fragment_start=6.5, fragment_end=13.0, diminish_factor=1.5)

    _export({"pad": pad, "cello": cello, "harp": harp, "piano": piano,
             "choir": choir, "bowl": bowl, "motif": motif + motif2},
            OUT / "04_Between.mid", bpm, key,
            {"pad": PAD_SPACE, "cello": CELLO, "harp": HARP,
             "piano": PIANO, "choir": CHOIR, "bowl": BOWL, "motif": PIANO})


# Track 5 — Return
# F# Aeolian, 54 BPM. Most rhythmic track — guitar ostinato,
# piano and flute layered, building intensity.
def produce_05_return():
    print("--- 05_Return ---")
    bpm, dur = 54, 190.0
    key = Scale(6, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    pad = AmbientPadGenerator(GeneratorParams(density=0.06, key_range_low=36, key_range_high=60), overlap=1.0).render(chords, key, dur)

    # Guitar: rhythmic ostinato pattern
    guitar = ArpeggiatorGenerator(GeneratorParams(density=0.14, key_range_low=48, key_range_high=72), pattern="up_down", note_duration=1.5).render(chords, key, dur)

    # Strings: building underneath
    strings = StringsEnsembleGenerator(GeneratorParams(density=0.06, key_range_low=36, key_range_high=60)).render(chords, key, dur)

    # Bass: grounding pulse
    bass = DroneGenerator(GeneratorParams(density=0.01, key_range_low=30, key_range_high=34), velocity=45).render(chords, key, dur)

    # Piano: enters after intro, more active melody
    piano = MelodyGenerator(GeneratorParams(density=0.1, velocity_range=(42, 65)), phrase_length=8.0, note_range_low=60, note_range_high=84, register_smoothness=0.82, harmony_note_probability=0.55, steps_probability=0.8).render(chords, key, dur - 60.0)
    piano = _off(piano, 32.0)

    # Flute: higher register echo of piano
    flute = MelodyGenerator(GeneratorParams(density=0.06, velocity_range=(38, 58)), phrase_length=12.0, note_range_low=72, note_range_high=84, register_smoothness=0.85).render(chords, key, dur - 80.0)
    flute = _off(flute, 70.0)

    motif = LM.render("grief", offset=130.0, transpose=6,
                       sequence_intervals=[0, -2, -5], sequence_spacing=12.0)

    _export({"pad": pad, "guitar": guitar, "strings": strings, "bass": bass,
             "piano": piano, "flute": flute, "motif": motif},
            OUT / "05_Return.mid", bpm, key,
            {"pad": PAD_WARM, "guitar": NYLON_GUITAR, "strings": 49,
             "bass": ACOUSTIC_BASS, "piano": PIANO, "flute": FLUTE, "motif": PIANO})


# Track 6 — White Fog
# C Aeolian, 48 BPM. Atmospheric with vibraphone lead.
# Harp arpeggios through fog, choir like distant voices.
def produce_06_white_fog():
    print("--- 06_White_Fog ---")
    bpm, dur = 48, 220.0
    key = Scale(0, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    # Two pad layers: warm + space for thickness
    pad_warm = AmbientPadGenerator(GeneratorParams(density=0.06, key_range_low=36, key_range_high=55), overlap=1.0).render(chords, key, dur)

    # Harp: slow arpeggios creating mist movement
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.08, key_range_low=60, key_range_high=84), pattern="down", note_duration=3.0).render(chords, key, dur)

    # Vibraphone: the voice in the fog
    vibes = MelodyGenerator(GeneratorParams(density=0.08, velocity_range=(38, 58)), phrase_length=12.0, note_range_low=60, note_range_high=79, register_smoothness=0.88, harmony_note_probability=0.4, steps_probability=0.82).render(chords, key, dur - 50.0)
    vibes = _off(vibes, 28.0)

    # Choir: distant wordless chorus
    choir = MelodyGenerator(GeneratorParams(density=0.04, velocity_range=(30, 48)), phrase_length=18.0, note_range_low=48, note_range_high=60, register_smoothness=0.93).render(chords, key, dur - 80.0)
    choir = _off(choir, 60.0)

    # Cello: low counterline
    cello = MelodyGenerator(GeneratorParams(density=0.04, velocity_range=(36, 52)), phrase_length=16.0, note_range_low=36, note_range_high=52, register_smoothness=0.9).render(chords, key, dur - 60.0)
    cello = _off(cello, 40.0)

    motif = LM.render("grief_choir", offset=160.0, transpose=0, retrograde=True, augment_factor=1.5)

    _export({"pad": pad_warm, "harp": harp, "vibes": vibes, "choir": choir,
             "cello": cello, "motif": motif},
            OUT / "06_White_Fog.mid", bpm, key,
            {"pad": PAD_SPACE, "harp": HARP, "vibes": VIBRAPHONE,
             "choir": CHOIR, "cello": CELLO, "motif": CHOIR})


# Track 7 — Embers
# G Aeolian, 50 BPM. Intimate — guitar + piano + vibes.
# Multiple motif fragments scattered like dying sparks.
def produce_07_embers():
    print("--- 07_Embers ---")
    bpm, dur = 50, 200.0
    key = Scale(7, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    pad = AmbientPadGenerator(GeneratorParams(density=0.06, key_range_low=36, key_range_high=60), overlap=1.0).render(chords, key, dur)

    # Guitar: fingerpicked, warm
    guitar = ArpeggiatorGenerator(GeneratorParams(density=0.1, key_range_low=48, key_range_high=72), pattern="up_down", note_duration=2.5).render(chords, key, dur)

    # Piano: lyric melody
    piano = MelodyGenerator(GeneratorParams(density=0.08, velocity_range=(42, 62)), phrase_length=10.0, note_range_low=60, note_range_high=84, register_smoothness=0.85, harmony_note_probability=0.5, steps_probability=0.82).render(chords, key, dur - 50.0)
    piano = _off(piano, 26.0)

    # Vibraphone: gentle countermelody
    vibes = MelodyGenerator(GeneratorParams(density=0.06, velocity_range=(35, 52)), phrase_length=10.0, note_range_low=60, note_range_high=79, register_smoothness=0.85).render(chords, key, dur - 70.0)
    vibes = _off(vibes, 48.0)

    # Strings: subtle bed
    strings = StringsEnsembleGenerator(GeneratorParams(density=0.04, key_range_low=36, key_range_high=55)).render(chords, key, dur)

    # Glockenspiel: tiny sparkles
    glock = MelodyGenerator(GeneratorParams(density=0.04, velocity_range=(32, 48)), phrase_length=14.0, note_range_low=72, note_range_high=96, register_smoothness=0.9).render(chords, key, dur - 100.0)
    glock = _off(glock, 70.0)

    motif = LM.render("grief_bowl", offset=130.0, transpose=7,
                       fragment_start=6.5, fragment_end=13.0,
                       sequence_intervals=[0, 3, -1, 4], sequence_spacing=14.0)
    motif2 = LM.render("grief_flute", offset=160.0, transpose=7,
                        fragment_start=0.0, fragment_end=3.5, augment_factor=2.0)

    _export({"pad": pad, "guitar": guitar, "piano": piano, "vibes": vibes,
             "strings": strings, "glock": glock, "motif": motif + motif2},
            OUT / "07_Embers.mid", bpm, key,
            {"pad": PAD_WARM, "guitar": NYLON_GUITAR, "piano": PIANO,
             "vibes": VIBRAPHONE, "strings": 49, "glock": GLOCKENSPIEL, "motif": BOWL})


# Track 8 — Let Go
# E Aeolian, 44 BPM. Full ensemble. The motif appears
# in original form then triple-augmented, dissolving.
def produce_08_let_go():
    print("--- 08_Let_Go ---")
    bpm, dur = 44, 260.0
    key = Scale(4, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    pad = AmbientPadGenerator(GeneratorParams(density=0.06, key_range_low=36, key_range_high=60), overlap=1.0).render(chords, key, dur)

    # Cello: long breathing line
    cello = MelodyGenerator(GeneratorParams(density=0.05, velocity_range=(38, 55)), phrase_length=16.0, note_range_low=36, note_range_high=55, register_smoothness=0.9, harmony_note_probability=0.3, steps_probability=0.88).render(chords, key, dur - 60.0)
    cello = _off(cello, 32.0)

    # Piano: main melody voice
    piano = MelodyGenerator(GeneratorParams(density=0.07, velocity_range=(40, 60)), phrase_length=12.0, note_range_low=60, note_range_high=84, register_smoothness=0.88, harmony_note_probability=0.45, steps_probability=0.82).render(chords, key, dur - 80.0)
    piano = _off(piano, 48.0)

    # Harp: arpeggiated texture
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.07, key_range_low=60, key_range_high=84), pattern="up", note_duration=3.5).render(chords, key, dur - 80.0)
    harp = _off(harp, 50.0)

    # Choir: enters in second half, building to finale
    choir = MelodyGenerator(GeneratorParams(density=0.04, velocity_range=(30, 48)), phrase_length=20.0, note_range_low=48, note_range_high=60, register_smoothness=0.93).render(chords, key, dur - 100.0)
    choir = _off(choir, 80.0)

    # Strings: full bed
    strings = StringsEnsembleGenerator(GeneratorParams(density=0.05, key_range_low=36, key_range_high=60)).render(chords, key, dur)

    # Flute: final whispered melody
    flute = MelodyGenerator(GeneratorParams(density=0.04, velocity_range=(35, 52)), phrase_length=16.0, note_range_low=72, note_range_high=84, register_smoothness=0.9).render(chords, key, dur - 120.0)
    flute = _off(flute, 100.0)

    # Motif: original form, then dissolving
    motif_a = LM.render("grief", offset=180.0, transpose=4)
    motif_b = LM.render("grief_choir", offset=210.0, transpose=4, augment_factor=3.0)
    motif_c = LM.render("grief_harp", offset=240.0, transpose=4,
                         fragment_start=0.0, fragment_end=3.5, augment_factor=2.0)

    _export({"pad": pad, "cello": cello, "piano": piano, "harp": harp,
             "choir": choir, "strings": strings, "flute": flute,
             "motif": motif_a + motif_b + motif_c},
            OUT / "08_Let_Go.mid", bpm, key,
            {"pad": PAD_SPACE, "cello": CELLO, "piano": PIANO,
             "harp": HARP, "choir": CHOIR, "strings": 49,
             "flute": FLUTE, "motif": CHOIR})


def main():
    produce_01_afterimage()
    produce_02_hollow()
    produce_03_dusk()
    produce_04_between()
    produce_05_return()
    produce_06_white_fog()
    produce_07_embers()
    produce_08_let_go()
    print(f"\nAlbum 'What Remains' complete. Files in {OUT}/")


if __name__ == "__main__":
    main()
