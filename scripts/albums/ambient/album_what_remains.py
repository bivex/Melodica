# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_what_remains.py — What Remains

8-track ambient album in Aeolian minor. Full arrangements with
interweaving voices, dynamic arcs, and evolving textures.
Register-separated to minimize masking and clashes.

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

# -- Register bands (separated to avoid masking) ---
# Sub-bass:   24-35  (bass drones only)
# Pad/strings: 36-47  (harmonic bed)
# Low voice:   48-59  (cello, guitar root)
# Mid voice:   60-71  (piano, harp arps)
# High voice:  72-84  (flute, vibes, melody)
# Sparkle:     84-96  (glock, bowl overtones)

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
        "pad": 0.4, "choir": 0.5, "drone": 0.35, "bowl": 0.55,
        "guitar": 0.65, "strings": 0.45, "arp": 0.5, "bass": 0.35,
        "vibes": 0.55, "motif": 0.6, "pad_space": 0.4,
        "glock": 0.4,
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
# E Aeolian, 48 BPM. Pad low, cello mid, piano high, harp sparkle.
def produce_01_afterimage():
    print("--- 01_Afterimage ---")
    bpm, dur = 48, 220.0
    key = Scale(4, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    # Pad: deep sub-bed, very low density
    pad = AmbientPadGenerator(GeneratorParams(density=0.04, key_range_low=28, key_range_high=44), overlap=1.0).render(chords, key, dur)

    # Drone: sub-bass anchor
    drone = DroneGenerator(GeneratorParams(density=0.01, key_range_low=24, key_range_high=28), velocity=38).render(chords, key, dur)

    # Cello: mid-low voice
    cello = MelodyGenerator(GeneratorParams(density=0.05, velocity_range=(42, 60)), phrase_length=16.0, note_range_low=48, note_range_high=57, register_smoothness=0.9).render(chords, key, dur - 40.0)
    cello = _off(cello, 24.0)

    # Piano: high register melody
    piano = MelodyGenerator(GeneratorParams(density=0.07, velocity_range=(44, 68)), phrase_length=10.0, note_range_low=72, note_range_high=84, register_smoothness=0.85, harmony_note_probability=0.4, steps_probability=0.82).render(chords, key, dur - 60.0)
    piano = _off(piano, 32.0)

    # Harp: sparkle arpeggios high up
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.08, key_range_low=72, key_range_high=88), pattern="up", note_duration=2.0).render(chords, key, dur - 80.0)
    harp = _off(harp, 60.0)

    # Bowl: isolated high strikes
    bowl = [NoteInfo(pitch=84, start=float(25 + i * 28), duration=8.0, velocity=42) for i in range(7)]

    motif = LM.render("grief_bowl", offset=170.0, transpose=4,
                       fragment_start=0.0, fragment_end=6.5, augment_factor=1.5)

    _export({"pad": pad, "drone": drone, "cello": cello, "piano": piano,
             "harp": harp, "bowl": bowl, "motif": motif},
            OUT / "01_Afterimage.mid", bpm, key,
            {"pad": PAD_SPACE, "drone": ACOUSTIC_BASS, "cello": CELLO,
             "piano": PIANO, "harp": HARP, "bowl": BOWL, "motif": BOWL})


# Track 2 — Hollow
# A Aeolian, 50 BPM. Guitar low arps, cello mid, choir high-back.
def produce_02_hollow():
    print("--- 02_Hollow ---")
    bpm, dur = 50, 200.0
    key = Scale(9, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    # Pad: low bed
    pad = AmbientPadGenerator(GeneratorParams(density=0.04, key_range_low=28, key_range_high=44), overlap=1.0).render(chords, key, dur)

    # Guitar: low arpeggios (roots + fifths)
    guitar = ArpeggiatorGenerator(GeneratorParams(density=0.1, key_range_low=48, key_range_high=59), pattern="down", note_duration=3.0).render(chords, key, dur)

    # Cello: lead voice, mid register
    cello = MelodyGenerator(GeneratorParams(density=0.06, velocity_range=(44, 65)), phrase_length=12.0, note_range_low=48, note_range_high=60, register_smoothness=0.88, harmony_note_probability=0.35, steps_probability=0.85).render(chords, key, dur - 30.0)
    cello = _off(cello, 16.0)

    # Choir: high backing vocals (separated from cello)
    choir = MelodyGenerator(GeneratorParams(density=0.04, velocity_range=(34, 50)), phrase_length=18.0, note_range_low=60, note_range_high=72, register_smoothness=0.93).render(chords, key, dur - 60.0)
    choir = _off(choir, 60.0)

    # Harp: high sparkle
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.06, key_range_low=72, key_range_high=88), pattern="up", note_duration=3.5).render(chords, key, dur - 60.0)
    harp = _off(harp, 40.0)

    motif = LM.render("grief_cello", offset=150.0, transpose=9, augment_factor=1.5)

    _export({"pad": pad, "guitar": guitar, "cello": cello, "choir": choir,
             "harp": harp, "motif": motif},
            OUT / "02_Hollow.mid", bpm, key,
            {"pad": PAD_WARM, "guitar": NYLON_GUITAR, "cello": CELLO,
             "choir": CHOIR, "harp": HARP, "motif": CELLO})


# Track 3 — Dusk
# D Aeolian, 52 BPM. Guitar mid, strings low, flute high, vibes high.
def produce_03_dusk():
    print("--- 03_Dusk ---")
    bpm, dur = 52, 190.0
    key = Scale(2, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    # Strings: low harmonic bed (not competing with guitar)
    strings = StringsEnsembleGenerator(GeneratorParams(density=0.04, key_range_low=36, key_range_high=48)).render(chords, key, dur)

    # Guitar: mid-register arpeggios
    guitar = ArpeggiatorGenerator(GeneratorParams(density=0.1, key_range_low=55, key_range_high=67), pattern="up_down", note_duration=2.0).render(chords, key, dur)

    # Flute: high melody
    flute = MelodyGenerator(GeneratorParams(density=0.07, velocity_range=(42, 62)), phrase_length=10.0, note_range_low=72, note_range_high=84, register_smoothness=0.85, harmony_note_probability=0.4, steps_probability=0.82).render(chords, key, dur - 40.0)
    flute = _off(flute, 24.0)

    # Vibes: high countermelody
    vibes = MelodyGenerator(GeneratorParams(density=0.05, velocity_range=(36, 52)), phrase_length=12.0, note_range_low=72, note_range_high=84, register_smoothness=0.85).render(chords, key, dur - 70.0)
    vibes = _off(vibes, 50.0)

    motif = LM.render("grief_flute", offset=130.0, transpose=2, invert=True)

    _export({"strings": strings, "guitar": guitar, "flute": flute,
             "vibes": vibes, "motif": motif},
            OUT / "03_Dusk.mid", bpm, key,
            {"strings": 49, "guitar": NYLON_GUITAR,
             "flute": FLUTE, "vibes": VIBRAPHONE, "motif": FLUTE})


# Track 4 — Between
# B Aeolian, 46 BPM. Cello low, piano mid, harp high. Filled ending.
def produce_04_between():
    print("--- 04_Between ---")
    bpm, dur = 46, 200.0
    key = Scale(11, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    # Pad: low
    pad = AmbientPadGenerator(GeneratorParams(density=0.04, key_range_low=28, key_range_high=44), overlap=1.0).render(chords, key, dur)

    # Cello: sustained low voice
    cello = DroneGenerator(GeneratorParams(density=0.01, key_range_low=36, key_range_high=40), velocity=48).render(chords, key, dur)

    # Piano: mid-high lyric voice — extend deeper into Q4
    piano = MelodyGenerator(GeneratorParams(density=0.06, velocity_range=(42, 62)), phrase_length=14.0, note_range_low=60, note_range_high=84, register_smoothness=0.88, harmony_note_probability=0.4, steps_probability=0.82).render(chords, key, dur - 10.0)
    piano = _off(piano, 8.0)

    # Harp: high arpeggios — run to very end
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.07, key_range_low=72, key_range_high=88), pattern="up", note_duration=3.0).render(chords, key, dur - 5.0)

    # Choir: high ethereal backing — extend into Q4
    choir = MelodyGenerator(GeneratorParams(density=0.03, velocity_range=(32, 48)), phrase_length=20.0, note_range_low=60, note_range_high=72, register_smoothness=0.93).render(chords, key, dur - 20.0)
    choir = _off(choir, 16.0)

    # Bowl: high sparkle accents — extend into Q4
    bowl = [NoteInfo(pitch=84, start=float(30 + i * 28), duration=10.0, velocity=38) for i in range(7)]

    # Coda: explicit notes in last 30 beats to fill Q4
    coda_piano = [NoteInfo(pitch=76 + i * 2, start=170.0 + i * 4, duration=4.0, velocity=45) for i in range(8)]
    coda_harp = [NoteInfo(pitch=84, start=170.0 + i * 5, duration=3.0, velocity=38) for i in range(6)]
    coda_choir = [NoteInfo(pitch=67, start=175.0, duration=25.0, velocity=35),
                  NoteInfo(pitch=64, start=180.0, duration=20.0, velocity=30)]

    motif = LM.render("grief_harp", offset=150.0, transpose=11, augment_factor=1.5)
    motif2 = LM.render("grief", offset=180.0, transpose=11, fragment_start=6.5, fragment_end=13.0, diminish_factor=1.5)
    motif3 = LM.render("grief_bowl", offset=190.0, transpose=11, fragment_start=0.0, fragment_end=3.5, augment_factor=2.0)

    _export({"pad": pad, "cello": cello, "piano": piano + coda_piano, "harp": harp + coda_harp,
             "choir": choir + coda_choir, "bowl": bowl, "motif": motif + motif2 + motif3},
            OUT / "04_Between.mid", bpm, key,
            {"pad": PAD_SPACE, "cello": CELLO, "piano": PIANO,
             "harp": HARP, "choir": CHOIR, "bowl": BOWL, "motif": PIANO})


# Track 5 — Return
# F# Aeolian, 54 BPM. Most rhythmic. Guitar mid, strings low, piano+flute high.
def produce_05_return():
    print("--- 05_Return ---")
    bpm, dur = 54, 180.0
    key = Scale(6, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    # Strings: low bed only
    strings = StringsEnsembleGenerator(GeneratorParams(density=0.04, key_range_low=36, key_range_high=48)).render(chords, key, dur)

    # Guitar: rhythmic mid arps
    guitar = ArpeggiatorGenerator(GeneratorParams(density=0.12, key_range_low=55, key_range_high=67), pattern="up_down", note_duration=1.5).render(chords, key, dur)

    # Bass: sub anchor
    bass = DroneGenerator(GeneratorParams(density=0.01, key_range_low=24, key_range_high=28), velocity=42).render(chords, key, dur)

    # Piano: high melody
    piano = MelodyGenerator(GeneratorParams(density=0.08, velocity_range=(44, 65)), phrase_length=8.0, note_range_low=72, note_range_high=84, register_smoothness=0.82, harmony_note_probability=0.45, steps_probability=0.8).render(chords, key, dur - 50.0)
    piano = _off(piano, 28.0)

    # Flute: highest voice
    flute = MelodyGenerator(GeneratorParams(density=0.05, velocity_range=(40, 58)), phrase_length=12.0, note_range_low=77, note_range_high=88, register_smoothness=0.85).render(chords, key, dur - 70.0)
    flute = _off(flute, 55.0)

    motif = LM.render("grief", offset=120.0, transpose=6,
                       sequence_intervals=[0, -2, -5], sequence_spacing=12.0)

    _export({"strings": strings, "guitar": guitar, "bass": bass,
             "piano": piano, "flute": flute, "motif": motif},
            OUT / "05_Return.mid", bpm, key,
            {"strings": 49, "guitar": NYLON_GUITAR, "bass": ACOUSTIC_BASS,
             "piano": PIANO, "flute": FLUTE, "motif": PIANO})


# Track 6 — White Fog
# C Aeolian, 48 BPM. Harp high arps, vibes high lead, cello mid, choir high.
def produce_06_white_fog():
    print("--- 06_White_Fog ---")
    bpm, dur = 48, 210.0
    key = Scale(0, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    # Pad: low atmospheric bed
    pad = AmbientPadGenerator(GeneratorParams(density=0.04, key_range_low=28, key_range_high=44), overlap=1.0).render(chords, key, dur)

    # Cello: mid-low counterline
    cello = MelodyGenerator(GeneratorParams(density=0.04, velocity_range=(38, 55)), phrase_length=16.0, note_range_low=48, note_range_high=57, register_smoothness=0.9).render(chords, key, dur - 40.0)
    cello = _off(cello, 24.0)

    # Harp: high arpeggios
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.07, key_range_low=72, key_range_high=88), pattern="down", note_duration=2.5).render(chords, key, dur)

    # Vibes: high lead melody
    vibes = MelodyGenerator(GeneratorParams(density=0.06, velocity_range=(40, 58)), phrase_length=12.0, note_range_low=72, note_range_high=84, register_smoothness=0.88, harmony_note_probability=0.35, steps_probability=0.82).render(chords, key, dur - 40.0)
    vibes = _off(vibes, 24.0)

    # Choir: high backing
    choir = MelodyGenerator(GeneratorParams(density=0.03, velocity_range=(32, 48)), phrase_length=18.0, note_range_low=60, note_range_high=72, register_smoothness=0.93).render(chords, key, dur - 60.0)
    choir = _off(choir, 50.0)

    motif = LM.render("grief_choir", offset=155.0, transpose=0, retrograde=True, augment_factor=1.5)

    _export({"pad": pad, "cello": cello, "harp": harp, "vibes": vibes,
             "choir": choir, "motif": motif},
            OUT / "06_White_Fog.mid", bpm, key,
            {"pad": PAD_SPACE, "cello": CELLO, "harp": HARP,
             "vibes": VIBRAPHONE, "choir": CHOIR, "motif": CHOIR})


# Track 7 — Embers
# G Aeolian, 50 BPM. Thinned: guitar mid, piano high, vibes high.
# No strings to avoid overload. Glock sparkle.
def produce_07_embers():
    print("--- 07_Embers ---")
    bpm, dur = 50, 180.0
    key = Scale(7, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    # Pad: low bed (thinned, no separate strings layer)
    pad = AmbientPadGenerator(GeneratorParams(density=0.04, key_range_low=28, key_range_high=44), overlap=1.0).render(chords, key, dur)

    # Guitar: mid arpeggios
    guitar = ArpeggiatorGenerator(GeneratorParams(density=0.1, key_range_low=55, key_range_high=67), pattern="up_down", note_duration=2.5).render(chords, key, dur)

    # Piano: high melody — extend into Q4
    piano = MelodyGenerator(GeneratorParams(density=0.07, velocity_range=(44, 62)), phrase_length=10.0, note_range_low=72, note_range_high=84, register_smoothness=0.85, harmony_note_probability=0.4, steps_probability=0.82).render(chords, key, dur - 15.0)
    piano = _off(piano, 10.0)

    # Vibes: high countermelody — extend into Q4
    vibes = MelodyGenerator(GeneratorParams(density=0.05, velocity_range=(38, 52)), phrase_length=12.0, note_range_low=72, note_range_high=84, register_smoothness=0.85).render(chords, key, dur - 25.0)
    vibes = _off(vibes, 20.0)

    # Glock: sparkle — extend into Q4
    glock = MelodyGenerator(GeneratorParams(density=0.03, velocity_range=(32, 46)), phrase_length=16.0, note_range_low=84, note_range_high=96, register_smoothness=0.9).render(chords, key, dur - 40.0)
    glock = _off(glock, 30.0)

    # Coda: explicit notes in last 30 beats to fill Q4
    coda_piano = [NoteInfo(pitch=79 - i, start=150.0 + i * 3.5, duration=3.5, velocity=42) for i in range(9)]
    coda_vibes = [NoteInfo(pitch=84, start=155.0 + i * 5, duration=4.0, velocity=36) for i in range(5)]
    coda_glock = [NoteInfo(pitch=88, start=160.0, duration=6.0, velocity=30),
                  NoteInfo(pitch=91, start=168.0, duration=5.0, velocity=28)]
    coda_guitar = [NoteInfo(pitch=60, start=155.0, duration=25.0, velocity=40),
                   NoteInfo(pitch=64, start=160.0, duration=20.0, velocity=36)]

    motif = LM.render("grief_bowl", offset=130.0, transpose=7,
                       fragment_start=6.5, fragment_end=13.0,
                       sequence_intervals=[0, 3, -1], sequence_spacing=14.0)
    motif2 = LM.render("grief_flute", offset=155.0, transpose=7,
                        fragment_start=0.0, fragment_end=3.5, augment_factor=2.0)
    motif3 = LM.render("grief_harp", offset=168.0, transpose=7,
                        fragment_start=0.0, fragment_end=6.5, augment_factor=2.0)

    _export({"pad": pad, "guitar": guitar + coda_guitar, "piano": piano + coda_piano, "vibes": vibes + coda_vibes,
             "glock": glock + coda_glock, "motif": motif + motif2 + motif3},
            OUT / "07_Embers.mid", bpm, key,
            {"pad": PAD_WARM, "guitar": NYLON_GUITAR, "piano": PIANO,
             "vibes": VIBRAPHONE, "glock": GLOCKENSPIEL, "motif": BOWL})


# Track 8 — Let Go
# E Aeolian, 44 BPM. Full ensemble, register-separated.
# Cello mid-low, piano+flute high, harp sparkle, choir high-back.
# Filled to the end.
def produce_08_let_go():
    print("--- 08_Let_Go ---")
    bpm, dur = 44, 240.0
    key = Scale(4, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    # Pad: deep low bed
    pad = AmbientPadGenerator(GeneratorParams(density=0.04, key_range_low=28, key_range_high=44), overlap=1.0).render(chords, key, dur)

    # Cello: mid-low voice — extend to near end
    cello = MelodyGenerator(GeneratorParams(density=0.04, velocity_range=(40, 55)), phrase_length=16.0, note_range_low=48, note_range_high=57, register_smoothness=0.9, harmony_note_probability=0.25, steps_probability=0.88).render(chords, key, dur - 15.0)
    cello = _off(cello, 8.0)

    # Piano: high melody — extend deeper
    piano = MelodyGenerator(GeneratorParams(density=0.06, velocity_range=(42, 60)), phrase_length=12.0, note_range_low=72, note_range_high=84, register_smoothness=0.88, harmony_note_probability=0.4, steps_probability=0.82).render(chords, key, dur - 20.0)
    piano = _off(piano, 12.0)

    # Harp: high arpeggiated texture — run to end
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.06, key_range_low=72, key_range_high=88), pattern="up", note_duration=3.0).render(chords, key, dur - 8.0)
    harp = _off(harp, 6.0)

    # Choir: high backing — extend to near end
    choir = MelodyGenerator(GeneratorParams(density=0.03, velocity_range=(32, 48)), phrase_length=20.0, note_range_low=60, note_range_high=72, register_smoothness=0.93).render(chords, key, dur - 25.0)
    choir = _off(choir, 20.0)

    # Flute: highest voice — extend into Q4
    flute = MelodyGenerator(GeneratorParams(density=0.04, velocity_range=(38, 55)), phrase_length=16.0, note_range_low=77, note_range_high=88, register_smoothness=0.9).render(chords, key, dur - 40.0)
    flute = _off(flute, 40.0)

    # Coda: explicit notes in last 40 beats to fill Q4
    coda_cello = [NoteInfo(pitch=52, start=205.0, duration=35.0, velocity=40),
                  NoteInfo(pitch=55, start=215.0, duration=25.0, velocity=36)]
    coda_piano = [NoteInfo(pitch=76 + i, start=200.0 + i * 4, duration=4.0, velocity=40) for i in range(10)]
    coda_harp = [NoteInfo(pitch=84, start=205.0 + i * 4, duration=3.0, velocity=34) for i in range(9)]
    coda_choir = [NoteInfo(pitch=64, start=210.0, duration=30.0, velocity=30),
                  NoteInfo(pitch=67, start=220.0, duration=20.0, velocity=28)]
    coda_flute = [NoteInfo(pitch=79, start=210.0, duration=12.0, velocity=35),
                  NoteInfo(pitch=81, start=225.0, duration=8.0, velocity=30)]

    # Motif: original → augmented → dissolving fragment → final echo
    motif_a = LM.render("grief", offset=170.0, transpose=4)
    motif_b = LM.render("grief_choir", offset=195.0, transpose=4, augment_factor=2.5)
    motif_c = LM.render("grief_harp", offset=220.0, transpose=4,
                         fragment_start=0.0, fragment_end=3.5, augment_factor=2.0)
    motif_d = LM.render("grief_bowl", offset=232.0, transpose=4,
                         fragment_start=0.0, fragment_end=3.5, augment_factor=3.0)

    _export({"pad": pad, "cello": cello + coda_cello, "piano": piano + coda_piano, "harp": harp + coda_harp,
             "choir": choir + coda_choir, "flute": flute + coda_flute,
             "motif": motif_a + motif_b + motif_c + motif_d},
            OUT / "08_Let_Go.mid", bpm, key,
            {"pad": PAD_SPACE, "cello": CELLO, "piano": PIANO,
             "harp": HARP, "choir": CHOIR, "flute": FLUTE, "motif": CHOIR})


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
