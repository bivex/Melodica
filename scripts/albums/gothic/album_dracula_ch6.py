# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_dracula_ch6.py — ДРАКУЛА: Глава VI (Dracula: Chapter VI - The Looming Storm)

Musical adaptation of Chapter VI of Bram Stoker's gothic masterpiece "Dracula"
(Mina's diary in Whitby, the ruins of the Abbey, Mr. Swales' tales of empty graves,
Lucy's sleepwalking, and the mysterious Russian schooner approaching in the storm).

Tracks:
  I.   Руины Уитби (Whitby Abbey) — 85 BPM. D Dorian.
       Atmosphere: Majestic, slightly melancholic. Ancient ruins overlooking the sea.
  II.  Пустые могилы (The Empty Graves) — 110 BPM. G Harmonic Minor.
       Atmosphere: A dark sea-shanty waltz. Mr. Swales talking about dead sailors and the sea.
  III. Лунатик Люси (Lucy the Sleepwalker) — 70 BPM. F Hungarian Minor.
       Atmosphere: Tense, ethereal, creeping. Lucy trying to escape the locked room at night.
  IV.  Надвигающийся шторм (The Approaching Storm) — 60 to 105 BPM. C Phrygian.
       Atmosphere: The sky turns gray, smell of death in the wind, the erratic Russian schooner.
"""

import random
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.accent import RhythmicAccentGenerator
from melodica.composer.automation import AutomationCurve
from melodica.composer.album_pipeline import produce_track, Mood

# Scales
KEY_D_DORIAN = types.Scale(root=2, mode=types.Mode.DORIAN)
KEY_G_HARMONIC = types.Scale(root=7, mode=types.Mode.HARMONIC_MINOR)
KEY_F_HUNGARIAN = types.Scale(root=5, mode=types.Mode.HUNGARIAN_MINOR)
KEY_C_PHRYGIAN = types.Scale(root=0, mode=types.Mode.PHRYGIAN)

random.seed(1897)
OUT = Path("output/album_dracula_ch6")
OUT.mkdir(parents=True, exist_ok=True)


# =====================================================================
# I. Руины Уитби (Whitby Abbey) — 85 BPM
# =====================================================================
def produce_whitby_abbey():
    """
    Majestic and ancient, overlooking the sea.
    Showcases: Dorian mode, acoustic guitar, choir pad.
    """
    bpm, dur = 85, 64.0

    # Dorian signature progression with major IV
    prog_str = "i:4.0 - IV:4.0 - v:4.0 - i:4.0"
    chords = types.parse_progression(prog_str, KEY_D_DORIAN)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Flowing Acoustic Guitar (Acoustic Guitar (steel) - Program 25)
    guitar_gen = ArpeggiatorGenerator(
        GeneratorParams(
            density=0.75, velocity_range=(65, 85),
            key_range_low=48, key_range_high=76
        ),
        pattern="up_down"
    )
    guitar = guitar_gen.render(full_chords, KEY_D_DORIAN, dur)
    guitar_track = types.Track(name="guitar", notes=guitar)
    guitar_track.humanize(timing_std_beats=0.015, velocity_std=3.0)

    # Majestic Choir Pad (Choir Aahs - Program 52)
    choir = AmbientPadGenerator(
        GeneratorParams(
            density=0.3, velocity_range=(50, 70),
            key_range_low=60, key_range_high=84
        )
    ).render(full_chords, KEY_D_DORIAN, dur)

    # Melancholic Cello Solo (Cello - Program 42)
    cello_gen = MelodyGenerator(
        GeneratorParams(
            density=0.45, complexity=0.5,
            velocity_range=(75, 100),
            key_range_low=48, key_range_high=72
        ),
        phrase_length=8.0
    )
    cello = cello_gen.render(full_chords, KEY_D_DORIAN, dur)

    cc_events = {
        "choir": AutomationCurve.sine_lfo(11, 60, 100, 0.0, dur, period=8.0),
        "cello": AutomationCurve.sine_lfo(1, 10, 80, 0.0, dur, period=4.0)
    }

    produce_track(
        tracks={"guitar": guitar_track.notes, "choir": choir, "cello": cello},
        bpm=bpm,
        instruments={"guitar": 25, "choir": 52, "cello": 42},
        path=OUT / "01_Whitby_Abbey.mid",
        mood=Mood.CHAMBER, key=KEY_D_DORIAN,
        chords=full_chords, cc_events=cc_events
    )

# =====================================================================
# II. Пустые могилы (The Empty Graves) — 110 BPM
# =====================================================================
def produce_empty_graves():
    """
    Mr. Swales' tales of dead sailors. A dark sea-shanty waltz.
    Showcases: 3/4 waltz accent generator, Accordion, Pizzicato strings.
    """
    bpm, dur = 110, 48.0

    # Waltz feel (3 beats per chord)
    prog_str = "i:3.0 - V:3.0 - VI:3.0 - V:3.0"
    chords = types.parse_progression(prog_str, KEY_G_HARMONIC)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Sea-shanty Accordion (Accordion - Program 21)
    accordion_gen = MelodyGenerator(
        GeneratorParams(
            density=0.6, complexity=0.7,
            velocity_range=(80, 105),
            key_range_low=60, key_range_high=84
        ),
        phrase_length=6.0
    )
    accordion = accordion_gen.render(full_chords, KEY_G_HARMONIC, dur)

    # Waltz rhythm backing (Pizzicato Strings - Program 45)
    pizzicato = RhythmicAccentGenerator(
        preset="waltz", pitch=None, octave=5, velocity_humanize=10
    ).render(full_chords, KEY_G_HARMONIC, dur)

    # Walking acoustic bass (Acoustic Bass - Program 32)
    bass = BassGenerator(
        GeneratorParams(
            density=0.5, velocity_range=(65, 85),
            key_range_low=28, key_range_high=45
        )
    ).render(full_chords, KEY_G_HARMONIC, dur)

    cc_events = {
        "accordion": AutomationCurve.sine_lfo(11, 70, 110, 0.0, dur, period=6.0)
    }

    produce_track(
        tracks={"accordion": accordion, "pizzicato": pizzicato, "bass": bass},
        bpm=bpm,
        instruments={"accordion": 21, "pizzicato": 45, "bass": 32},
        path=OUT / "02_The_Empty_Graves.mid",
        mood=Mood.CHAMBER, key=KEY_G_HARMONIC,
        chords=full_chords, cc_events=cc_events
    )

# =====================================================================
# III. Лунатик Люси (Lucy the Sleepwalker) — 70 BPM
# =====================================================================
def produce_lucy_sleepwalker():
    """
    Tense, ethereal. Lucy wandering the locked room.
    Showcases: Music Box, Eerie Pad, Harp plucks.
    """
    bpm, dur = 70, 64.0

    prog_str = "i:4.0 - bII:4.0 - vii:4.0 - V:4.0"
    chords = types.parse_progression(prog_str, KEY_F_HUNGARIAN)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Creepy lullaby Music Box (Music Box - Program 10)
    musicbox_gen = ArpeggiatorGenerator(
        GeneratorParams(
            density=0.5, velocity_range=(50, 75),
            key_range_low=72, key_range_high=96
        ),
        pattern="random"
    )
    musicbox = musicbox_gen.render(full_chords, KEY_F_HUNGARIAN, dur)

    # Eerie Pad (Pad 4 Choir - Program 91)
    pad = AmbientPadGenerator(
        GeneratorParams(
            density=0.25, velocity_range=(40, 65),
            key_range_low=48, key_range_high=72
        )
    ).render(full_chords, KEY_F_HUNGARIAN, dur)

    # Plucked Orchestral Harp acting as nervous steps (Orchestral Harp - Program 46)
    harp = RhythmicAccentGenerator(
        preset="gallop", pitch=None, octave=4, velocity_humanize=15, accent_strength=1.2
    ).render(full_chords, KEY_F_HUNGARIAN, dur)

    # Fretless Bass slipping around (Fretless Bass - Program 35)
    bass = BassGenerator(
        GeneratorParams(
            density=0.3, velocity_range=(45, 65),
            key_range_low=24, key_range_high=40
        )
    ).render(full_chords, KEY_F_HUNGARIAN, dur)

    cc_events = {
        "pad": AutomationCurve.sine_lfo(74, 30, 85, 0.0, dur, period=12.0)
    }

    produce_track(
        tracks={"musicbox": musicbox, "pad": pad, "harp": harp, "bass": bass},
        bpm=bpm,
        instruments={"musicbox": 10, "pad": 91, "harp": 46, "bass": 35},
        path=OUT / "03_Lucy_the_Sleepwalker.mid",
        mood=Mood.CHAMBER, key=KEY_F_HUNGARIAN,
        chords=full_chords, cc_events=cc_events
    )

# =====================================================================
# IV. Надвигающийся шторм (The Approaching Storm) — 60 to 105 BPM
# =====================================================================
def produce_approaching_storm():
    """
    The sky turns gray, smell of death, erratic Russian schooner.
    Showcases: Phrygian dread, Timpani rolls, Strings swells, Accelerando.
    """
    bpm, dur = 60, 64.0

    # Ominous shifting chords
    prog_str = "i:4.0 - bII:4.0 - iv:4.0 - bII:4.0"
    chords = types.parse_progression(prog_str, KEY_C_PHRYGIAN)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Tremolo Strings simulating the howling wind (Tremolo Strings - Program 44)
    strings_gen = StringsEnsembleGenerator(
        GeneratorParams(
            density=0.8, velocity_range=(60, 95),
            key_range_low=48, key_range_high=72
        )
    )
    strings = strings_gen.render(full_chords, KEY_C_PHRYGIAN, dur)

    # French Horn playing a dark melody (French Horn - Program 60)
    horn_gen = MelodyGenerator(
        GeneratorParams(
            density=0.5, complexity=0.3,
            velocity_range=(80, 110),
            key_range_low=45, key_range_high=65
        ),
        phrase_length=4.0
    )
    horn = horn_gen.render(full_chords, KEY_C_PHRYGIAN, dur)

    # Heavy Timpani (Timpani - Program 47)
    timpani = RhythmicAccentGenerator(
        preset="march", pitch=36, velocity_humanize=10, accent_strength=1.4
    ).render(full_chords, KEY_C_PHRYGIAN, dur)

    # Deep Contrabass (Contrabass - Program 43)
    bass = BassGenerator(
        GeneratorParams(
            density=0.5, velocity_range=(70, 90),
            key_range_low=20, key_range_high=35
        )
    ).render(full_chords, KEY_C_PHRYGIAN, dur)

    # Dynamic accelerando as the storm approaches and the ship gets closer
    tempo_events = []
    for beat in range(0, int(dur), 4):
        interpolated_bpm = 60.0 + (105.0 - 60.0) * (beat / dur)
        tempo_events.append((float(beat), interpolated_bpm))

    cc_events = {
        "strings": AutomationCurve.exponential(11, 40, 110, 0.0, dur, exponent=1.5, steps=30),
        "horn": AutomationCurve.sine_lfo(1, 0, 80, 0.0, dur, period=4.0)
    }

    produce_track(
        tracks={"strings": strings, "horn": horn, "timpani": timpani, "bass": bass},
        bpm=bpm,
        instruments={"strings": 44, "horn": 60, "timpani": 47, "bass": 43},
        path=OUT / "04_The_Approaching_Storm.mid",
        mood=Mood.CINEMATIC, key=KEY_C_PHRYGIAN,
        chords=full_chords, cc_events=cc_events,
        tempo_events=tempo_events
    )

# =====================================================================
# Main execution
# =====================================================================
if __name__ == "__main__":
    print("================================================================================")
    print("   БРЭМ СТОКЕР — ДРАКУЛА: ГЛАВА VI (Gothic Album - The Looming Storm)")
    print("   Руины Уитби, легенды старого моряка, лунатизм Люси и таинственный корабль")
    print("================================================================================")
    
    print("\n-> Compiling Track 1: Руины Уитби (Whitby Abbey)...")
    produce_whitby_abbey()
    
    print("\n-> Compiling Track 2: Пустые могилы (The Empty Graves)...")
    produce_empty_graves()
    
    print("\n-> Compiling Track 3: Лунатик Люси (Lucy the Sleepwalker)...")
    produce_lucy_sleepwalker()
    
    print("\n-> Compiling Track 4: Надвигающийся шторм (The Approaching Storm)...")
    produce_approaching_storm()
    
    print("\n================================================================================")
    print("   CHAPTER VI GOTHIC ALBUM SUCCESSFULLY COMPILED!")
    print("   MIDI output saved in: " + str(OUT.resolve()))
    print("================================================================================")
