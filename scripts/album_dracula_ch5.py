# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_dracula_ch5.py — ДРАКУЛА: Глава V (Dracula: Chapter V - Love and Madness)

Musical adaptation of Chapter V of Bram Stoker's gothic masterpiece "Dracula"
(Mina's shorthand letters, Lucy's three proposals in one day, Dr. Seward's heartbreak,
the introduction of the lunatic Renfield, and Quincey's campfire toast).

Scale: Contrasting scales representing the light of London/Whitby vs the looming madness.

Tracks:
  I.   Стенография Мины (Mina's Shorthand) — 110 BPM. C Major.
       Atmosphere: Light, rhythmic, structured. Mina typing and practicing shorthand.
  II.  Три предложения (Three Proposals) — 90 BPM. F Major.
       Atmosphere: Romantic, sweeping strings and harp. Lucy's overwhelming joy and gentle rejection of the two.
  III. Пациент Ренфилд (Patient Renfield) — 60 BPM. D Minor.
       Atmosphere: Dr. Seward's broken heart turning into a clinical obsession with a zoophagous maniac. Dark, erratic, moody.
  IV.  Тост у костра (The Campfire Toast) — 75 BPM. G Major.
       Atmosphere: Quincey Morris invites Seward and Arthur to drink to the winner. Acoustic, comradely, slightly melancholic.
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
KEY_C_MAJOR = types.Scale(root=0, mode=types.Mode.MAJOR)
KEY_F_MAJOR = types.Scale(root=5, mode=types.Mode.MAJOR)
KEY_D_MINOR = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)
KEY_G_MAJOR = types.Scale(root=7, mode=types.Mode.MAJOR)

random.seed(1897)  # Year of Dracula's first publication
OUT = Path("output/album_dracula_ch5")
OUT.mkdir(parents=True, exist_ok=True)


# =====================================================================
# I. Стенография Мины (Mina's Shorthand) — 110 BPM
# =====================================================================
def produce_minas_shorthand():
    """
    Light, staccato, typewriter-like feel for Mina practicing her shorthand
    and writing to Lucy.
    """
    bpm, dur = 110, 64.0

    prog_str = "I:4.0 - IV:4.0 - V:4.0 - I:4.0"
    chords = types.parse_progression(prog_str, KEY_C_MAJOR)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Staccato Piano acting as a typewriter (Acoustic Grand Piano - Program 0)
    piano_gen = ArpeggiatorGenerator(
        GeneratorParams(
            density=0.8, velocity_range=(70, 90),
            key_range_low=60, key_range_high=84
        ),
        pattern="random"
    )
    piano_notes = piano_gen.render(full_chords, KEY_C_MAJOR, dur)
    piano_track = types.Track(name="piano", notes=piano_notes)
    piano_track.humanize(timing_std_beats=0.01, velocity_std=2.0) # Very precise, like a machine

    # Gentle Flute melody for Mina's daydreaming about Jonathan (Flute - Program 73)
    flute_gen = MelodyGenerator(
        GeneratorParams(
            density=0.4, complexity=0.4,
            velocity_range=(65, 80),
            key_range_low=72, key_range_high=96
        ),
        phrase_length=8.0
    )
    flute_notes = flute_gen.render(full_chords, KEY_C_MAJOR, dur)
    
    # Light Bass (Acoustic Bass - Program 32)
    bass = BassGenerator(
        GeneratorParams(
            density=0.5, velocity_range=(60, 75),
            key_range_low=24, key_range_high=48
        )
    ).render(full_chords, KEY_C_MAJOR, dur)

    cc_events = {
        "flute": AutomationCurve.sine_lfo(11, 50, 100, 0.0, dur, period=8.0)
    }

    produce_track(
        tracks={"piano": piano_track.notes, "flute": flute_notes, "bass": bass},
        bpm=bpm,
        instruments={"piano": 0, "flute": 73, "bass": 32},
        path=OUT / "01_Minas_Shorthand.mid",
        mood=Mood.CHAMBER, key=KEY_C_MAJOR,
        chords=full_chords, cc_events=cc_events
    )

# =====================================================================
# II. Три предложения (Three Proposals) — 90 BPM
# =====================================================================
def produce_three_proposals():
    """
    Lucy's overwhelming joy and romantic flutter as she receives
    three proposals in one day. Lush strings and harp.
    """
    bpm, dur = 90, 80.0

    # Romantic and sweeping: I -> vi -> ii -> V
    prog_str = "I:4.0 - vi:4.0 - ii:4.0 - V:4.0"
    chords = types.parse_progression(prog_str, KEY_F_MAJOR)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Harp arpeggios (Orchestral Harp - Program 46)
    harp_gen = ArpeggiatorGenerator(
        GeneratorParams(
            density=0.75, velocity_range=(60, 85),
            key_range_low=48, key_range_high=84
        ),
        pattern="up"
    )
    harp = harp_gen.render(full_chords, KEY_F_MAJOR, dur)

    # Lush Strings Ensemble (String Ensemble 1 - Program 48)
    strings = StringsEnsembleGenerator(
        GeneratorParams(
            density=0.6, velocity_range=(70, 95),
            key_range_low=48, key_range_high=72
        )
    ).render(full_chords, KEY_F_MAJOR, dur)

    # A beautiful Violin solo representing Lucy's ultimate choice, Arthur (Violin - Program 40)
    violin_gen = MelodyGenerator(
        GeneratorParams(
            density=0.5, complexity=0.6,
            velocity_range=(80, 105),
            key_range_low=65, key_range_high=89
        ),
        phrase_length=8.0
    )
    violin = violin_gen.render(full_chords, KEY_F_MAJOR, dur)
    
    cc_events = {
        "strings": AutomationCurve.sine_lfo(11, 60, 110, 0.0, dur, period=8.0),
        "violin": AutomationCurve.sine_lfo(1, 20, 90, 0.0, dur, period=4.0)
    }

    produce_track(
        tracks={"harp": harp, "strings": strings, "violin": violin},
        bpm=bpm,
        instruments={"harp": 46, "strings": 48, "violin": 40},
        path=OUT / "02_Three_Proposals.mid",
        mood=Mood.CINEMATIC, key=KEY_F_MAJOR,
        chords=full_chords, cc_events=cc_events
    )

# =====================================================================
# III. Пациент Ренфилд (Patient Renfield) — 60 BPM
# =====================================================================
def produce_patient_renfield():
    """
    Dr. Seward's diary. Heartbroken, he throws himself into work
    and introduces the zoophagous maniac R.M. Renfield. Dark, moody, clinical.
    """
    bpm, dur = 60, 64.0

    # Clinical, slightly dissonant minor: i -> iv -> viidim -> III
    prog_str = "i:4.0 - iv:4.0 - viidim:4.0 - III:4.0"
    chords = types.parse_progression(prog_str, KEY_D_MINOR)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Melancholic Cello for Dr. Seward's broken heart (Cello - Program 42)
    cello_gen = MelodyGenerator(
        GeneratorParams(
            density=0.35, complexity=0.7,
            velocity_range=(50, 75),
            key_range_low=36, key_range_high=60
        ),
        phrase_length=4.0
    )
    cello = cello_gen.render(full_chords, KEY_D_MINOR, dur)

    # Eerie Pad for the asylum atmosphere (Pad 1 / New age - Program 88)
    pad = AmbientPadGenerator(
        GeneratorParams(
            density=0.2, velocity_range=(40, 60),
            key_range_low=48, key_range_high=72
        )
    ).render(full_chords, KEY_D_MINOR, dur)
    
    # Erratic ticking/accent representing Renfield catching flies/spiders (Woodblock / Percussion)
    # Using Timpani slot but pitched high
    ticks = RhythmicAccentGenerator(
        preset="gallop", pitch=76, velocity_humanize=15, accent_strength=1.5
    ).render(full_chords, KEY_D_MINOR, dur)

    # Low creeping bass (Contrabass - Program 43)
    bass = BassGenerator(
        GeneratorParams(
            density=0.4, velocity_range=(45, 65),
            key_range_low=24, key_range_high=36
        )
    ).render(full_chords, KEY_D_MINOR, dur)

    cc_events = {
        "pad": AutomationCurve.sine_lfo(74, 30, 80, 0.0, dur, period=12.0)
    }

    produce_track(
        tracks={"cello": cello, "pad": pad, "ticks": ticks, "bass": bass},
        bpm=bpm,
        instruments={"cello": 42, "pad": 88, "ticks": 115, "bass": 43}, # 115 is Woodblock
        path=OUT / "03_Patient_Renfield.mid",
        mood=Mood.CHAMBER, key=KEY_D_MINOR,
        chords=full_chords, cc_events=cc_events
    )

# =====================================================================
# IV. Тост у костра (The Campfire Toast) — 75 BPM
# =====================================================================
def produce_campfire_toast():
    """
    Quincey Morris invites Arthur and Seward to drink.
    Acoustic Texan warmth, comradely but hiding heartbreak.
    """
    bpm, dur = 75, 64.0

    prog_str = "I:4.0 - IV:4.0 - V:4.0 - I:4.0"
    chords = types.parse_progression(prog_str, KEY_G_MAJOR)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Acoustic Steel Guitar (Acoustic Guitar (steel) - Program 25)
    guitar_gen = ArpeggiatorGenerator(
        GeneratorParams(
            density=0.6, velocity_range=(65, 85),
            key_range_low=40, key_range_high=72
        ),
        pattern="up_down"
    )
    guitar = guitar_gen.render(full_chords, KEY_G_MAJOR, dur)
    guitar_track = types.Track(name="guitar", notes=guitar)
    guitar_track.humanize(timing_std_beats=0.02, velocity_std=4.0).swing(factor=0.1)

    # Fretless Bass (Fretless Bass - Program 35)
    bass = BassGenerator(
        GeneratorParams(
            density=0.45, velocity_range=(60, 80),
            key_range_low=28, key_range_high=40
        )
    ).render(full_chords, KEY_G_MAJOR, dur)

    # Harmonicas or a whistling lead (Ocarina - Program 79 or Whistle - Program 78)
    whistle_gen = MelodyGenerator(
        GeneratorParams(
            density=0.35, complexity=0.4,
            velocity_range=(70, 90),
            key_range_low=72, key_range_high=84
        ),
        phrase_length=8.0
    )
    whistle = whistle_gen.render(full_chords, KEY_G_MAJOR, dur)

    cc_events = {
        "whistle": AutomationCurve.sine_lfo(11, 70, 110, 0.0, dur, period=4.0)
    }

    produce_track(
        tracks={"guitar": guitar_track.notes, "bass": bass, "whistle": whistle},
        bpm=bpm,
        instruments={"guitar": 25, "bass": 35, "whistle": 78},
        path=OUT / "04_The_Campfire_Toast.mid",
        mood=Mood.CHAMBER, key=KEY_G_MAJOR,
        chords=full_chords, cc_events=cc_events
    )

# =====================================================================
# Main execution
# =====================================================================
if __name__ == "__main__":
    print("================================================================================")
    print("   БРЭМ СТОКЕР — ДРАКУЛА: ГЛАВА V (Gothic Album - Love and Madness)")
    print("   Письма Мины и Люси, дневник Сьюворда (Ренфилд) и телеграмма Артура")
    print("================================================================================")
    
    print("\n-> Compiling Track 1: Стенография Мины (Mina's Shorthand)...")
    produce_minas_shorthand()
    
    print("\n-> Compiling Track 2: Три предложения (Three Proposals)...")
    produce_three_proposals()
    
    print("\n-> Compiling Track 3: Пациент Ренфилд (Patient Renfield)...")
    produce_patient_renfield()
    
    print("\n-> Compiling Track 4: Тост у костра (The Campfire Toast)...")
    produce_campfire_toast()
    
    print("\n================================================================================")
    print("   CHAPTER V GOTHIC ALBUM SUCCESSFULLY COMPILED!")
    print("   MIDI output saved in: " + str(OUT.resolve()))
    print("================================================================================")
