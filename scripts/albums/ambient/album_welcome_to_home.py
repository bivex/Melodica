# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_welcome_to_home.py — Welcome to Home

Warm, cheerful 9-track ambient album for the Roblox game "Welcome to Home".
Every track feels like coming home — sunlight through windows, cozy rooms,
a garden in bloom, a fireplace crackling, a cup of tea on the table.

  I.   Morning Light         — C Major. Sunbeam through curtains. 56 BPM.
  II.  Open Door              — G Lydian. Stepping inside. 52 BPM.
  III. Kitchen Warmth         — F Lydian. Tea kettle, toast, laughter. 60 BPM.
  IV.  Garden Outside         — D Major. Flowers, breeze, birds. 64 BPM.
  V.   Living Room            — A Dorian. Comfy couch, soft blankets. 54 BPM.
  VI.  Rainy Window           — E Minor. Gentle rain, cozy inside. 50 BPM.
  VII. Sunroom                — G Major. Golden afternoon light. 58 BPM.
  VIII.Fireplace              — C Lydian. Crackling warmth, stories. 48 BPM.
  IX.  Goodnight              — F Major. Stars outside, safe and sound. 44 BPM.
"""

import random
from pathlib import Path

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
XYLOPHONE = 13
VIBRAPHONE = 11
GLOCKENSPIEL = 9
ACOUSTIC_BASS = 32

random.seed(2026)
OUT = Path("output/welcome_to_home")
OUT.mkdir(parents=True, exist_ok=True)


def _off(notes, offset):
    return [
        NoteInfo(pitch=n.pitch, start=n.start + offset,
                 duration=n.duration, velocity=n.velocity)
        for n in notes
    ]


def _master(raw: dict, bpm: float, lufs: float = -18.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.8, "harp": 0.7, "flute": 0.75, "cello": 0.55,
        "pad": 0.45, "choir": 0.5, "drone": 0.4, "bowl": 0.55,
        "guitar": 0.65, "strings": 0.55, "arp": 0.5, "bass": 0.4,
        "bells": 0.45, "vibes": 0.5, "glock": 0.4,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def _export(tracks: dict, path: Path, bpm: float, key: Scale, instruments: dict):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)


# =====================================================================
# I. Morning Light — C Major, 56 BPM
# =====================================================================
def produce_01_morning_light():
    print("--- 01_Morning_Light ---")
    bpm = 56
    dur = 200.0
    key = Scale(0, Mode.MAJOR)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=dur)]

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.08, key_range_low=48, key_range_high=72),
        overlap=1.0
    ).render(chords, key, dur)

    piano = MelodyGenerator(
        GeneratorParams(density=0.06, velocity_range=(45, 65)),
        phrase_length=12.0,
        note_range_low=60, note_range_high=84,
        register_smoothness=0.9
    ).render(chords, key, dur - 48.0)
    piano = _off(piano, 24.0)

    bells = [NoteInfo(pitch=84, start=float(i * 25), duration=6.0, velocity=50)
             for i in range(8)]

    _export(
        {"pad": pad, "piano": piano, "bells": bells},
        OUT / "01_Morning_Light.mid", bpm, key,
        {"pad": PAD_WARM, "piano": PIANO, "bells": BOWL},
    )


# =====================================================================
# II. Open Door — G Lydian, 52 BPM
# =====================================================================
def produce_02_open_door():
    print("--- 02_Open_Door ---")
    bpm = 52
    dur = 180.0
    key = Scale(7, Mode.LYDIAN)
    chords = [ChordLabel(root=7, quality=Quality.MAJOR, start=0, duration=dur)]

    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.12, key_range_low=60, key_range_high=84),
        pattern="up", note_duration=3.0
    ).render(chords, key, dur)

    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.04, key_range_low=36, key_range_high=60),
    ).render(chords, key, dur)

    flute = MelodyGenerator(
        GeneratorParams(density=0.05, velocity_range=(40, 58)),
        phrase_length=16.0,
        note_range_low=72, note_range_high=84,
        register_smoothness=0.85
    ).render(chords, key, dur - 60.0)
    flute = _off(flute, 40.0)

    _export(
        {"harp": harp, "strings": strings, "flute": flute},
        OUT / "02_Open_Door.mid", bpm, key,
        {"harp": HARP, "strings": 49, "flute": FLUTE},
    )


# =====================================================================
# III. Kitchen Warmth — F Lydian, 60 BPM
# =====================================================================
def produce_03_kitchen_warmth():
    print("--- 03_Kitchen_Warmth ---")
    bpm = 60
    dur = 160.0
    key = Scale(5, Mode.LYDIAN)
    chords = [
        ChordLabel(root=5, quality=Quality.MAJOR, start=0, duration=80),
        ChordLabel(root=0, quality=Quality.MAJOR, start=80, duration=80),
    ]

    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.15, key_range_low=48, key_range_high=72),
        pattern="up_down", note_duration=2.5
    ).render(chords, key, dur)

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.06, key_range_low=36, key_range_high=60),
        overlap=1.0
    ).render(chords, key, dur)

    glock = MelodyGenerator(
        GeneratorParams(density=0.07, velocity_range=(35, 55)),
        phrase_length=8.0,
        note_range_low=72, note_range_high=96,
        register_smoothness=0.8
    ).render(chords, key, dur - 40.0)
    glock = _off(glock, 24.0)

    _export(
        {"guitar": guitar, "pad": pad, "glock": glock},
        OUT / "03_Kitchen_Warmth.mid", bpm, key,
        {"guitar": NYLON_GUITAR, "pad": PAD_WARM, "glock": GLOCKENSPIEL},
    )


# =====================================================================
# IV. Garden Outside — D Major, 64 BPM
# =====================================================================
def produce_04_garden_outside():
    print("--- 04_Garden_Outside ---")
    bpm = 64
    dur = 180.0
    key = Scale(2, Mode.MAJOR)
    chords = [
        ChordLabel(root=2, quality=Quality.MAJOR, start=0, duration=60),
        ChordLabel(root=7, quality=Quality.MAJOR, start=60, duration=60),
        ChordLabel(root=9, quality=Quality.MINOR, start=120, duration=60),
    ]

    flute = MelodyGenerator(
        GeneratorParams(density=0.08, velocity_range=(45, 65)),
        phrase_length=12.0,
        note_range_low=72, note_range_high=84,
        register_smoothness=0.85,
        harmony_note_probability=0.7,
        steps_probability=0.85
    ).render(chords, key, dur - 32.0)
    flute = _off(flute, 16.0)

    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.12, key_range_low=60, key_range_high=84),
        pattern="up", note_duration=2.0
    ).render(chords, key, dur)

    bass = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=36, key_range_high=38),
        velocity=40
    ).render(chords, key, dur)

    _export(
        {"flute": flute, "harp": harp, "bass": bass},
        OUT / "04_Garden_Outside.mid", bpm, key,
        {"flute": FLUTE, "harp": HARP, "bass": ACOUSTIC_BASS},
    )


# =====================================================================
# V. Living Room — A Dorian, 54 BPM
# =====================================================================
def produce_05_living_room():
    print("--- 05_Living_Room ---")
    bpm = 54
    dur = 200.0
    key = Scale(9, Mode.DORIAN)
    chords = [ChordLabel(root=9, quality=Quality.MINOR, start=0, duration=dur)]

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.07, key_range_low=36, key_range_high=60),
        overlap=1.0
    ).render(chords, key, dur)

    piano = MelodyGenerator(
        GeneratorParams(density=0.05, velocity_range=(40, 60)),
        phrase_length=16.0,
        note_range_low=60, note_range_high=84,
        register_smoothness=0.9
    ).render(chords, key, dur - 60.0)
    piano = _off(piano, 32.0)

    cello = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=36, key_range_high=40),
        velocity=38
    ).render(chords, key, dur)

    choir = MelodyGenerator(
        GeneratorParams(density=0.03, velocity_range=(30, 48)),
        phrase_length=20.0,
        note_range_low=48, note_range_high=60,
        register_smoothness=0.95
    ).render(chords, key, dur - 40.0)
    choir = _off(choir, 24.0)

    _export(
        {"pad": pad, "piano": piano, "cello": cello, "choir": choir},
        OUT / "05_Living_Room.mid", bpm, key,
        {"pad": PAD_WARM, "piano": PIANO, "cello": CELLO, "choir": CHOIR},
    )


# =====================================================================
# VI. Rainy Window — E Minor, 50 BPM
# =====================================================================
def produce_06_rainy_window():
    print("--- 06_Rainy_Window ---")
    bpm = 50
    dur = 220.0
    key = Scale(4, Mode.AEOLIAN)
    chords = [
        ChordLabel(root=4, quality=Quality.MINOR, start=0, duration=110),
        ChordLabel(root=0, quality=Quality.MAJOR, start=110, duration=110),
    ]

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.06, key_range_low=36, key_range_high=60),
        overlap=1.0
    ).render(chords, key, dur)

    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.08, key_range_low=60, key_range_high=84),
        pattern="down", note_duration=3.0
    ).render(chords, key, dur)

    flute = MelodyGenerator(
        GeneratorParams(density=0.04, velocity_range=(35, 52)),
        phrase_length=20.0,
        note_range_low=72, note_range_high=84,
        register_smoothness=0.9
    ).render(chords, key, dur - 64.0)
    flute = _off(flute, 48.0)

    _export(
        {"pad": pad, "harp": harp, "flute": flute},
        OUT / "06_Rainy_Window.mid", bpm, key,
        {"pad": PAD_SPACE, "harp": HARP, "flute": FLUTE},
    )


# =====================================================================
# VII. Sunroom — G Major, 58 BPM
# =====================================================================
def produce_07_sunroom():
    print("--- 07_Sunroom ---")
    bpm = 58
    dur = 180.0
    key = Scale(7, Mode.MAJOR)
    chords = [
        ChordLabel(root=7, quality=Quality.MAJOR, start=0, duration=60),
        ChordLabel(root=2, quality=Quality.MAJOR, start=60, duration=60),
        ChordLabel(root=5, quality=Quality.MAJOR, start=120, duration=60),
    ]

    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.12, key_range_low=48, key_range_high=72),
        pattern="up", note_duration=2.0
    ).render(chords, key, dur)

    vibes = MelodyGenerator(
        GeneratorParams(density=0.06, velocity_range=(40, 58)),
        phrase_length=12.0,
        note_range_low=60, note_range_high=84,
        register_smoothness=0.85
    ).render(chords, key, dur - 36.0)
    vibes = _off(vibes, 20.0)

    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.04, key_range_low=36, key_range_high=60),
    ).render(chords, key, dur)

    bass = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=36, key_range_high=38),
        velocity=35
    ).render(chords, key, dur)

    _export(
        {"guitar": guitar, "vibes": vibes, "strings": strings, "bass": bass},
        OUT / "07_Sunroom.mid", bpm, key,
        {"guitar": NYLON_GUITAR, "vibes": VIBRAPHONE, "strings": 49, "bass": ACOUSTIC_BASS},
    )


# =====================================================================
# VIII. Fireplace — C Lydian, 48 BPM
# =====================================================================
def produce_08_fireplace():
    print("--- 08_Fireplace ---")
    bpm = 48
    dur = 240.0
    key = Scale(0, Mode.LYDIAN)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=dur)]

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.05, key_range_low=36, key_range_high=60),
        overlap=1.0
    ).render(chords, key, dur)

    piano = MelodyGenerator(
        GeneratorParams(density=0.04, velocity_range=(35, 55)),
        phrase_length=20.0,
        note_range_low=60, note_range_high=84,
        register_smoothness=0.9
    ).render(chords, key, dur - 80.0)
    piano = _off(piano, 40.0)

    cello = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=36, key_range_high=40),
        velocity=35
    ).render(chords, key, dur)

    choir = MelodyGenerator(
        GeneratorParams(density=0.03, velocity_range=(28, 45)),
        phrase_length=24.0,
        note_range_low=48, note_range_high=60,
        register_smoothness=0.95
    ).render(chords, key, dur - 60.0)
    choir = _off(choir, 36.0)

    _export(
        {"pad": pad, "piano": piano, "cello": cello, "choir": choir},
        OUT / "08_Fireplace.mid", bpm, key,
        {"pad": PAD_WARM, "piano": PIANO, "cello": CELLO, "choir": CHOIR},
    )


# =====================================================================
# IX. Goodnight — F Major, 44 BPM
# =====================================================================
def produce_09_goodnight():
    print("--- 09_Goodnight ---")
    bpm = 44
    dur = 260.0
    key = Scale(5, Mode.MAJOR)
    chords = [
        ChordLabel(root=5, quality=Quality.MAJOR, start=0, duration=87),
        ChordLabel(root=0, quality=Quality.MAJOR, start=87, duration=86),
        ChordLabel(root=5, quality=Quality.MAJOR, start=173, duration=87),
    ]

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.04, key_range_low=36, key_range_high=60),
        overlap=1.0
    ).render(chords, key, dur)

    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.06, key_range_low=60, key_range_high=84),
        pattern="up", note_duration=4.0
    ).render(chords, key, dur - 80.0)

    choir = MelodyGenerator(
        GeneratorParams(density=0.03, velocity_range=(25, 42)),
        phrase_length=24.0,
        note_range_low=48, note_range_high=60,
        register_smoothness=0.95
    ).render(chords, key, dur - 100.0)
    choir = _off(choir, 60.0)

    bowl = [NoteInfo(pitch=72, start=float(i * 40), duration=12.0, velocity=45)
            for i in range(7)]

    _export(
        {"pad": pad, "harp": harp, "choir": choir, "bowl": bowl},
        OUT / "09_Goodnight.mid", bpm, key,
        {"pad": PAD_SPACE, "harp": HARP, "choir": CHOIR, "bowl": BOWL},
    )


def main():
    produce_01_morning_light()
    produce_02_open_door()
    produce_03_kitchen_warmth()
    produce_04_garden_outside()
    produce_05_living_room()
    produce_06_rainy_window()
    produce_07_sunroom()
    produce_08_fireplace()
    produce_09_goodnight()
    print(f"\nAlbum 'Welcome to Home' complete. Files in {OUT}/")


if __name__ == "__main__":
    main()
