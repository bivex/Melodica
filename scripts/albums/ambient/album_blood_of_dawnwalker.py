# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_blood_of_dawnwalker.py — THE BLOOD OF DAWNWALKER

A dark ambient / atmospheric album (7 movements, ~45 min) for the world of
Dawnwalker — a young man cursed to walk between day and night, torn between
humanity and the vampiric power he needs to save his family.

Movements:
    I.   The Last Sunrise        (the morning before the bite)
    II.  Turning                 (fever, transformation, first thirst)
    III. Between Worlds          (the Dawnwalker's liminal existence)
    IV.  The Family Name         (love remembered, the reason to fight)
    V.   Night's Dominion        (the curse's seduction, power's pull)
    VI.  Blood Price             (what must be sacrificed)
    VII. Dawn or Dust            (the final choice — soul or family)

Scales: AEOLIAN, PHRYGIAN, HARM_MINOR, LOCRIAN, DORIAN, LYDIAN, AEOLIC.
        Predominantly dark with fleeting moments of warmth.
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
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# ---------------------------------------------------------------------------
# Scales
# ---------------------------------------------------------------------------
A_AE   = Scale(root=9,  mode=Mode.AEOLIAN)
E_AE   = Scale(root=4,  mode=Mode.AEOLIAN)
D_AE   = Scale(root=2,  mode=Mode.AEOLIAN)
B_AE   = Scale(root=11, mode=Mode.AEOLIAN)
F_AE   = Scale(root=5,  mode=Mode.AEOLIAN)
FS_AE  = Scale(root=6,  mode=Mode.AEOLIAN)
G_AE   = Scale(root=7,  mode=Mode.AEOLIAN)
C_AE   = Scale(root=0,  mode=Mode.AEOLIAN)
BB_AE  = Scale(root=10, mode=Mode.AEOLIAN)
EF_AE  = Scale(root=3,  mode=Mode.AEOLIAN)

E_PH   = Scale(root=4,  mode=Mode.PHRYGIAN)
A_PH   = Scale(root=9,  mode=Mode.PHRYGIAN)
B_PH   = Scale(root=11, mode=Mode.PHRYGIAN)
D_PH   = Scale(root=2,  mode=Mode.PHRYGIAN)
FS_PH  = Scale(root=6,  mode=Mode.PHRYGIAN)

A_HM   = Scale(root=9,  mode=Mode.HARMONIC_MINOR)
E_HM   = Scale(root=4,  mode=Mode.HARMONIC_MINOR)
B_HM   = Scale(root=11, mode=Mode.HARMONIC_MINOR)
D_HM   = Scale(root=2,  mode=Mode.HARMONIC_MINOR)
F_HM   = Scale(root=5,  mode=Mode.HARMONIC_MINOR)
CS_HM  = Scale(root=1,  mode=Mode.HARMONIC_MINOR)

B_LOC  = Scale(root=11, mode=Mode.LOCRIAN)
E_LOC  = Scale(root=4,  mode=Mode.LOCRIAN)

A_DOR  = Scale(root=9,  mode=Mode.DORIAN)
D_DOR  = Scale(root=2,  mode=Mode.DORIAN)

F_LYD  = Scale(root=5,  mode=Mode.LYDIAN)
C_LYD  = Scale(root=0,  mode=Mode.LYDIAN)


# ---------------------------------------------------------------------------
# GM Programs
# ---------------------------------------------------------------------------
TIBETAN_BOWL = 14
CELLO        = 42
CONTRABASS   = 43
HARP         = 46
FLUTE        = 73
OBOE         = 68
CHOIR_AAH    = 52
VOICE_OOH    = 53
PAD_WARM     = 89
PAD_SPACE    = 91
PAD_CHOIR    = 88
PIANO        = 0
ORGAN        = 19
STRINGS_ENS  = 48
TREM_STR     = 44


random.seed(666)
OUT = Path("output/album_blood_of_dawnwalker")
OUT.mkdir(parents=True, exist_ok=True)


def _off(notes, offset):
    return [
        NoteInfo(pitch=n.pitch, start=n.start + offset,
                 duration=n.duration, velocity=n.velocity)
        for n in notes
    ]


def _master(raw: dict, bpm: float, lufs: float = -16.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "bowl": 0.75, "pad": 0.4, "flute": 0.65, "cello": 0.5,
        "drone": 0.35, "harp": 0.6, "bass": 0.4, "piano": 0.65,
        "voice": 0.55, "choir": 0.5, "strings": 0.5, "arp": 0.45,
        "organ": 0.4, "trem": 0.45, "oboe": 0.6,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def _export(tracks: dict, path: Path, bpm: float, key: Scale,
            instruments: dict, lufs: float = -16.0):
    final_notes, cc_events = _master(tracks, bpm, lufs)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)


# ===========================================================================
# I. THE LAST SUNRISE — The morning before the bite
# ===========================================================================
def track_01():
    """The last morning he felt the sun on his skin. Warm. Human. Final."""
    print("--- 01_The_Last_Sunrise ---")
    bpm = 48
    dur = 240.0
    key = C_LYD

    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0,    duration=80),
        ChordLabel(root=7, quality=Quality.MAJOR, start=80,   duration=80),
        ChordLabel(root=5, quality=Quality.MAJOR, start=160,  duration=40),
        ChordLabel(root=0, quality=Quality.MAJOR, start=200,  duration=40),
    ]

    # Warm pad — the last warmth of daylight
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.06, velocity_range=(30, 50))
    ).render(chords, key, dur)

    # Solo cello — a human voice, unadorned
    cello = MelodyGenerator(
        GeneratorParams(density=0.06, velocity_range=(40, 60)),
        phrase_length=20.0, harmony_note_probability=0.7,
        steps_probability=0.85, note_range_low=36, note_range_high=55,
        register_smoothness=0.9
    ).render(chords, key, dur - 60.0)
    cello = _off(cello, 40.0)

    # Harp — light through window, dust motes
    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.12, velocity_range=(25, 45)),
        pattern="up", note_duration=2.0
    ).render(chords, key, dur)

    # Bowl — the sun rises
    bowls = [
        NoteInfo(pitch=72, start=4.0,  duration=20.0, velocity=65),
        NoteInfo(pitch=60, start=80.0,  duration=18.0, velocity=55),
        NoteInfo(pitch=67, start=160.0, duration=16.0, velocity=50),
        NoteInfo(pitch=72, start=220.0, duration=18.0, velocity=45),
    ]

    _export(
        {"pad": pad, "cello": cello, "harp": harp, "bowl": bowls},
        OUT / "01_The_Last_Sunrise.mid", bpm, key,
        {"pad": PAD_WARM, "cello": CELLO, "harp": HARP, "bowl": TIBETAN_BOWL},
    )


# ===========================================================================
# II. TURNING — Fever, transformation, first thirst
# ===========================================================================
def track_02():
    """The blood takes hold. Skin burns. Teeth sharpen. Hunger awakens."""
    print("--- 02_Turning ---")
    bpm = 52
    dur = 200.0
    key = E_PH

    chords = [
        ChordLabel(root=4, quality=Quality.MINOR, start=0,   duration=50),
        ChordLabel(root=5, quality=Quality.MINOR, start=50,  duration=50),
        ChordLabel(root=9, quality=Quality.MINOR, start=100, duration=50),
        ChordLabel(root=4, quality=Quality.MINOR, start=150, duration=50),
    ]

    # Low drone — the curse taking root
    drone = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=28, key_range_high=32),
        velocity=40
    ).render(chords, key, dur)

    # Tremolo strings — the fever, the shaking
    trem = AmbientPadGenerator(
        GeneratorParams(density=0.08, velocity_range=(25, 50),
                        key_range_low=40, key_range_high=60)
    ).render(chords, key, dur)

    # Oboe — pain given voice
    oboe = MelodyGenerator(
        GeneratorParams(density=0.08, velocity_range=(35, 60)),
        phrase_length=12.0, harmony_note_probability=0.6,
        note_range_low=58, note_range_high=74,
        register_smoothness=0.8
    ).render(chords, key, dur - 50.0)
    oboe = _off(oboe, 30.0)

    # Choir — something inhuman stirring
    choir = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=48, key_range_high=60),
        velocity=30
    ).render(chords, key, dur)

    _export(
        {"drone": drone, "trem": trem, "oboe": oboe, "choir": choir},
        OUT / "02_Turning.mid", bpm, key,
        {"drone": CONTRABASS, "trem": TREM_STR, "oboe": OBOE, "choir": CHOIR_AAH},
    )


# ===========================================================================
# III. BETWEEN WORLDS — The Dawnwalker's liminal existence
# ===========================================================================
def track_03():
    """Neither alive nor dead. Day burns. Night calls. He walks the edge."""
    print("--- 03_Between_Worlds ---")
    bpm = 44
    dur = 300.0
    key = B_LOC

    chords = [
        ChordLabel(root=11, quality=Quality.MINOR, start=0,   duration=75),
        ChordLabel(root=4,  quality=Quality.MINOR, start=75,  duration=75),
        ChordLabel(root=9,  quality=Quality.MINOR, start=150, duration=75),
        ChordLabel(root=2,  quality=Quality.MINOR, start=225, duration=75),
    ]

    # Space pad — the void between day and night
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.05, velocity_range=(25, 45))
    ).render(chords, key, dur)

    # Sparse piano — footsteps on the threshold
    piano = MelodyGenerator(
        GeneratorParams(density=0.04, velocity_range=(35, 55)),
        phrase_length=24.0, harmony_note_probability=0.7,
        steps_probability=0.9, note_range_low=60, note_range_high=79,
        register_smoothness=0.95
    ).render(chords, key, dur - 80.0)
    piano = _off(piano, 60.0)

    # Drone — the constant pull of two worlds
    drone = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=36, key_range_high=40),
        velocity=30
    ).render(chords, key, dur)

    # Bowl hits — moments of clarity in the fog
    bowls = [
        NoteInfo(pitch=60, start=20.0,  duration=25.0, velocity=55),
        NoteInfo(pitch=55, start=95.0,  duration=20.0, velocity=50),
        NoteInfo(pitch=67, start=170.0, duration=22.0, velocity=48),
        NoteInfo(pitch=60, start=250.0, duration=25.0, velocity=45),
    ]

    _export(
        {"pad": pad, "piano": piano, "drone": drone, "bowl": bowls},
        OUT / "03_Between_Worlds.mid", bpm, key,
        {"pad": PAD_SPACE, "piano": PIANO, "drone": PAD_WARM, "bowl": TIBETAN_BOWL},
    )


# ===========================================================================
# IV. THE FAMILY NAME — Love remembered, the reason to fight
# ===========================================================================
def track_04():
    """Faces in memory. A mother's voice. A brother's laugh. Why he endures."""
    print("--- 04_The_Family_Name ---")
    bpm = 50
    dur = 220.0
    key = D_DOR

    chords = [
        ChordLabel(root=2, quality=Quality.MINOR, start=0,   duration=55),
        ChordLabel(root=7, quality=Quality.MAJOR, start=55,  duration=55),
        ChordLabel(root=9, quality=Quality.MINOR, start=110, duration=55),
        ChordLabel(root=5, quality=Quality.MAJOR, start=165, duration=55),
    ]

    # Warm pad — memory, tenderness
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.07, velocity_range=(30, 50))
    ).render(chords, key, dur)

    # Cello — the human heart still beating
    cello = MelodyGenerator(
        GeneratorParams(density=0.07, velocity_range=(40, 65)),
        phrase_length=16.0, harmony_note_probability=0.8,
        steps_probability=0.9, note_range_low=36, note_range_high=55,
        register_smoothness=0.9
    ).render(chords, key, dur - 40.0)
    cello = _off(cello, 24.0)

    # Harp — children's laughter, once
    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.1, velocity_range=(25, 45)),
        pattern="up", note_duration=1.5
    ).render(chords, key, dur)

    # Voice — a mother's song, half-remembered
    voice = MelodyGenerator(
        GeneratorParams(density=0.05, velocity_range=(35, 50)),
        phrase_length=20.0, note_range_low=60, note_range_high=72,
        register_smoothness=0.95
    ).render(chords, key, dur - 60.0)
    voice = _off(voice, 50.0)

    _export(
        {"pad": pad, "cello": cello, "harp": harp, "voice": voice},
        OUT / "04_The_Family_Name.mid", bpm, key,
        {"pad": PAD_WARM, "cello": CELLO, "harp": HARP, "voice": VOICE_OOH},
    )


# ===========================================================================
# V. NIGHT'S DOMINION — The curse's seduction, power's pull
# ===========================================================================
def track_05():
    """The darkness whispers: why fight it? The power is yours. Take it."""
    print("--- 05_Nights_Dominion ---")
    bpm = 56
    dur = 200.0
    key = A_HM

    chords = [
        ChordLabel(root=9,  quality=Quality.MINOR, start=0,   duration=50),
        ChordLabel(root=4,  quality=Quality.MINOR, start=50,  duration=50),
        ChordLabel(root=0,  quality=Quality.MINOR, start=100, duration=50),
        ChordLabel(root=9,  quality=Quality.MINOR, start=150, duration=50),
    ]

    # Organ — the ancient power, cathedral dark
    organ = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=36, key_range_high=48),
        velocity=35
    ).render(chords, key, dur)

    # Pad — seductive, rich, dark
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.08, velocity_range=(30, 55),
                        key_range_low=40, key_range_high=64)
    ).render(chords, key, dur)

    # Bass drone — the pull of the abyss
    bass = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=24, key_range_high=28),
        velocity=38
    ).render(chords, key, dur)

    # Choir — voices of the turned, the lost
    choir = MelodyGenerator(
        GeneratorParams(density=0.06, velocity_range=(35, 55)),
        phrase_length=16.0, note_range_low=48, note_range_high=64,
        register_smoothness=0.9
    ).render(chords, key, dur - 40.0)
    choir = _off(choir, 24.0)

    # Sparse arpeggio — temptation's glitter
    arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.1, velocity_range=(25, 45)),
        pattern="random", note_duration=1.0
    ).render(chords, key, dur)

    _export(
        {"organ": organ, "pad": pad, "bass": bass, "choir": choir, "arp": arp},
        OUT / "05_Nights_Dominion.mid", bpm, key,
        {"organ": ORGAN, "pad": PAD_SPACE, "bass": CONTRABASS,
         "choir": CHOIR_AAH, "arp": HARP},
    )


# ===========================================================================
# VI. BLOOD PRICE — What must be sacrificed
# ===========================================================================
def track_06():
    """Every cure has a cost. Every victory demands a wound."""
    print("--- 06_Blood_Price ---")
    bpm = 46
    dur = 260.0
    key = F_HM

    chords = [
        ChordLabel(root=5,  quality=Quality.MINOR, start=0,   duration=65),
        ChordLabel(root=0,  quality=Quality.MINOR, start=65,  duration=65),
        ChordLabel(root=7,  quality=Quality.MINOR, start=130, duration=65),
        ChordLabel(root=5,  quality=Quality.MINOR, start=195, duration=65),
    ]

    # Cello — the weight of decision
    cello = MelodyGenerator(
        GeneratorParams(density=0.06, velocity_range=(35, 55)),
        phrase_length=18.0, harmony_note_probability=0.7,
        note_range_low=36, note_range_high=52,
        register_smoothness=0.9
    ).render(chords, key, dur - 60.0)
    cello = _off(cello, 40.0)

    # Drone — the ticking clock, the draining hourglass
    drone = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=36, key_range_high=40),
        velocity=32
    ).render(chords, key, dur)

    # Tremolo strings — tension, the price being weighed
    trem = AmbientPadGenerator(
        GeneratorParams(density=0.06, velocity_range=(25, 45),
                        key_range_low=44, key_range_high=60)
    ).render(chords, key, dur)

    # Flute — the soul's fragile voice
    flute = MelodyGenerator(
        GeneratorParams(density=0.05, velocity_range=(30, 50)),
        phrase_length=20.0, note_range_low=67, note_range_high=84,
        register_smoothness=0.95
    ).render(chords, key, dur - 80.0)
    flute = _off(flute, 60.0)

    # Bowl — the moment of choice approaches
    bowls = [
        NoteInfo(pitch=60, start=30.0,  duration=20.0, velocity=50),
        NoteInfo(pitch=55, start=100.0, duration=18.0, velocity=45),
        NoteInfo(pitch=67, start=165.0, duration=20.0, velocity=48),
        NoteInfo(pitch=60, start=230.0, duration=22.0, velocity=55),
    ]

    _export(
        {"cello": cello, "drone": drone, "trem": trem, "flute": flute, "bowl": bowls},
        OUT / "06_Blood_Price.mid", bpm, key,
        {"cello": CELLO, "drone": PAD_WARM, "trem": TREM_STR,
         "flute": FLUTE, "bowl": TIBETAN_BOWL},
    )


# ===========================================================================
# VII. DAWN OR DUST — The final choice — soul or family
# ===========================================================================
def track_07():
    """The horizon breaks. He chooses. Whatever comes after, he is no longer
    what he was. The sun rises — or it doesn't."""
    print("--- 07_Dawn_or_Dust ---")
    bpm = 42
    dur = 320.0
    key = A_DOR

    chords = [
        ChordLabel(root=9, quality=Quality.MINOR, start=0,   duration=80),
        ChordLabel(root=2, quality=Quality.MAJOR, start=80,  duration=80),
        ChordLabel(root=7, quality=Quality.MAJOR, start=160, duration=80),
        ChordLabel(root=9, quality=Quality.MINOR, start=240, duration=80),
    ]

    # Piano — the decision, note by note
    piano = MelodyGenerator(
        GeneratorParams(density=0.05, velocity_range=(35, 60)),
        phrase_length=24.0, harmony_note_probability=0.7,
        steps_probability=0.9, note_range_low=60, note_range_high=79,
        register_smoothness=0.9
    ).render(chords, key, dur - 80.0)
    piano = _off(piano, 50.0)

    # Warm pad — dawn breaking (or not)
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.06, velocity_range=(25, 50))
    ).render(chords, key, dur)

    # Strings ensemble — the world holding its breath
    strings = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=48, key_range_high=60),
        velocity=30
    ).render(chords, key, dur)

    # Harp — the first light (or the final dark)
    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.08, velocity_range=(20, 40)),
        pattern="up", note_duration=2.0
    ).render(chords, key, dur - 40.0)
    harp = _off(harp, 30.0)

    # Choir — the world's verdict
    choir = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=48, key_range_high=60),
        velocity=28
    ).render(chords, key, dur)

    # Final bowl — the last sound
    final_bowls = [
        NoteInfo(pitch=72, start=8.0,   duration=24.0, velocity=55),
        NoteInfo(pitch=67, start=100.0, duration=20.0, velocity=45),
        NoteInfo(pitch=60, start=200.0, duration=22.0, velocity=40),
        NoteInfo(pitch=55, start=280.0, duration=30.0, velocity=50),
        NoteInfo(pitch=48, start=310.0, duration=10.0, velocity=35),
    ]

    _export(
        {"piano": piano, "pad": pad, "strings": strings,
         "harp": harp, "choir": choir, "bowl": final_bowls},
        OUT / "07_Dawn_or_Dust.mid", bpm, key,
        {"piano": PIANO, "pad": PAD_WARM, "strings": STRINGS_ENS,
         "harp": HARP, "choir": CHOIR_AAH, "bowl": TIBETAN_BOWL},
    )


# ===========================================================================
# Main
# ===========================================================================
def main():
    print()
    print("=" * 72)
    print("   T H E   B L O O D   O F   D A W N W A L K E R")
    print("   A Dark Ambient Album in Seven Movements (~45 min)")
    print()
    print("   I.   The Last Sunrise     — the morning before the bite")
    print("   II.  Turning              — fever, transformation, first thirst")
    print("   III. Between Worlds       — the Dawnwalker's liminal existence")
    print("   IV.  The Family Name      — love remembered, the reason to fight")
    print("   V.   Night's Dominion     — the curse's seduction, power's pull")
    print("   VI.  Blood Price          — what must be sacrificed")
    print("   VII. Dawn or Dust         — the final choice: soul or family")
    print("=" * 72)

    track_01()
    track_02()
    track_03()
    track_04()
    track_05()
    track_06()
    track_07()

    total = sum(1 for f in OUT.glob("*.mid"))
    print()
    print("=" * 72)
    print(f"   THE BLOOD OF DAWNWALKER — COMPLETE.")
    print(f"   {total} movements generated in: {OUT.resolve()}")
    print("=" * 72)


if __name__ == "__main__":
    main()
