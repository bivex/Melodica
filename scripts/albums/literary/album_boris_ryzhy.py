# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_boris_ryzhy.py — БОРИС РЫЖИЙ (В РОССИИ РАССТАЮТСЯ НАВСЕГДА...)

Musical adaptation of the tragic, nostalgic, and existential poetry of Boris Ryzhy.
The orchestration is kept "clean" to avoid mid-range clutter and low-end clashes,
providing a professional, wide, and deep mix.

Tracks:
  I.   В России расстаются навсегда (In Russia, partings are forever) — 60 BPM. C Minor.
  II.  Заезженная пластинка (The Worn-out Record) — 85 BPM. A Dorian.
  III. Сны об отце (Dreams of Father) — 65 BPM. E Minor.
  IV.  Подвальчик (The Basement Bar) — 75 BPM. D Dorian.
  V.   Бледный всадник (The Pale Rider) — 120 BPM. G Phrygian.
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
from melodica.generators.orchestral_strings import ViolinGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.composer.automation import AutomationCurve
from melodica.composer.album_pipeline import produce_track, Mood

# Scales
KEY_C_MINOR = types.Scale(root=0, mode=types.Mode.NATURAL_MINOR)
KEY_A_DORIAN = types.Scale(root=9, mode=types.Mode.DORIAN)
KEY_E_MINOR = types.Scale(root=4, mode=types.Mode.NATURAL_MINOR)
KEY_D_DORIAN = types.Scale(root=2, mode=types.Mode.DORIAN)
KEY_G_PHRYGIAN = types.Scale(root=7, mode=types.Mode.PHRYGIAN)

random.seed(1974)  # Birth year of Boris Ryzhy
OUT = Path("output/album_boris_ryzhy")
OUT.mkdir(parents=True, exist_ok=True)


# =====================================================================
# I. В России расстаются навсегда — 60 BPM
# =====================================================================
def produce_partings_forever():
    """
    Cold, fatalistic, sparse. 
    Acoustic Grand Piano, Violin solo, Acoustic Bass.
    """
    bpm, dur = 60, 64.0
    prog_str = "i:4.0 - v:4.0 - VI:4.0 - iv:4.0"
    chords = types.parse_progression(prog_str, KEY_C_MINOR)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    piano_gen = ArpeggiatorGenerator(GeneratorParams(density=0.5, velocity_range=(50, 75), key_range_low=48, key_range_high=72), pattern="up_down")
    piano = types.Track(name="piano", notes=piano_gen.render(full_chords, KEY_C_MINOR, dur)).humanize(0.02, 3.0)

    violin_gen = MelodyGenerator(GeneratorParams(density=0.3, complexity=0.4, velocity_range=(70, 95), key_range_low=60, key_range_high=84), phrase_length=8.0)
    violin = types.Track(name="violin", notes=violin_gen.render(full_chords, KEY_C_MINOR, dur)).humanize(0.03, 4.0)

    bass = BassGenerator(GeneratorParams(density=0.4, velocity_range=(60, 80), key_range_low=24, key_range_high=36)).render(full_chords, KEY_C_MINOR, dur)

    # Plaintive solo violin — the farewell at the station, bowing into the cold
    solo_violin = ViolinGenerator(
        GeneratorParams(density=0.25, velocity_range=(55, 85), key_range_low=60, key_range_high=84),
        articulation="legato", vibrato=True, con_sordino=True
    ).render(full_chords, KEY_C_MINOR, dur)

    # Distant choir — the crowd on the platform, wordless
    choir = ChoirAahsGenerator(
        GeneratorParams(density=0.03, velocity_range=(25, 45), key_range_low=48, key_range_high=64)
    ).render(full_chords, KEY_C_MINOR, dur)

    cc_events = {
        "violin": AutomationCurve.sine_lfo(11, 40, 100, 0.0, dur, period=8.0)
    }

    produce_track(
        tracks={"piano": piano.notes, "violin": violin.notes, "bass": bass,
                "solo_violin": solo_violin, "choir": choir},
        bpm=bpm,
        instruments={"piano": 0, "violin": 40, "bass": 32,
                     "solo_violin": 40, "choir": 52},
        path=OUT / "01_Partings_Forever.mid",
        mood=Mood.CHAMBER, key=KEY_C_MINOR, chords=full_chords, cc_events=cc_events
    )


# =====================================================================
# II. Заезженная пластинка (А грустно было и уныло...) — 85 BPM
# =====================================================================
def produce_worn_out_record():
    """
    Nostalgic waltz. Dorian mode.
    Honky-tonk Piano, Acoustic Guitar, Fretless Bass.
    """
    bpm, dur = 85, 48.0
    # Dorian progression
    prog_str = "i:3.0 - IV:3.0 - VII:3.0 - i:3.0"
    chords = types.parse_progression(prog_str, KEY_A_DORIAN)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Honky-tonk for the vintage record feel
    honky_gen = ArpeggiatorGenerator(GeneratorParams(density=0.6, velocity_range=(65, 85), key_range_low=60, key_range_high=84), pattern="random")
    honky = types.Track(name="honky_tonk", notes=honky_gen.render(full_chords, KEY_A_DORIAN, dur)).humanize(0.04, 5.0).swing(0.1)

    guitar_gen = MelodyGenerator(GeneratorParams(density=0.5, complexity=0.6, velocity_range=(75, 95), key_range_low=48, key_range_high=72), phrase_length=6.0)
    guitar = types.Track(name="guitar", notes=guitar_gen.render(full_chords, KEY_A_DORIAN, dur)).humanize(0.02, 4.0).swing(0.1)

    bass = BassGenerator(GeneratorParams(density=0.5, velocity_range=(60, 80), key_range_low=28, key_range_high=40)).render(full_chords, KEY_A_DORIAN, dur)

    produce_track(
        tracks={"honky_tonk": honky.notes, "guitar": guitar.notes, "bass": bass},
        bpm=bpm,
        instruments={"honky_tonk": 3, "guitar": 24, "bass": 35},
        path=OUT / "02_Worn_Out_Record.mid",
        mood=Mood.CHAMBER, key=KEY_A_DORIAN, chords=full_chords
    )


# =====================================================================
# III. Сны об отце (А иногда отец мне говорил...) — 65 BPM
# =====================================================================
def produce_dreams_of_father():
    """
    Pensive, dreamy, regretful. E Natural Minor.
    Steel Acoustic Guitar, Flute, Warm Pad, Acoustic Bass.
    """
    bpm, dur = 65, 64.0
    prog_str = "i:4.0 - VI:4.0 - III:4.0 - V:4.0"
    chords = types.parse_progression(prog_str, KEY_E_MINOR)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    guitar_gen = ArpeggiatorGenerator(GeneratorParams(density=0.7, velocity_range=(60, 80), key_range_low=40, key_range_high=64), pattern="up_down")
    guitar = types.Track(name="guitar", notes=guitar_gen.render(full_chords, KEY_E_MINOR, dur)).humanize(0.02, 3.0)

    flute_gen = MelodyGenerator(GeneratorParams(density=0.3, complexity=0.3, velocity_range=(65, 85), key_range_low=72, key_range_high=96), phrase_length=8.0)
    flute = types.Track(name="flute", notes=flute_gen.render(full_chords, KEY_E_MINOR, dur)).humanize(0.02, 4.0)

    pad = AmbientPadGenerator(GeneratorParams(density=0.2, velocity_range=(45, 60), key_range_low=48, key_range_high=72)).render(full_chords, KEY_E_MINOR, dur)
    bass = BassGenerator(GeneratorParams(density=0.4, velocity_range=(55, 75), key_range_low=28, key_range_high=40)).render(full_chords, KEY_E_MINOR, dur)

    # Plaintive solo violin — the father's voice, remembered in dreams
    solo_violin = ViolinGenerator(
        GeneratorParams(density=0.2, velocity_range=(50, 75), key_range_low=60, key_range_high=84),
        articulation="legato", vibrato=True, con_sordino=True
    ).render(full_chords, KEY_E_MINOR, dur)

    # Distant choir — memory dissolving into warmth
    choir = ChoirAahsGenerator(
        GeneratorParams(density=0.025, velocity_range=(22, 40), key_range_low=48, key_range_high=64)
    ).render(full_chords, KEY_E_MINOR, dur)

    cc_events = {
        "flute": AutomationCurve.sine_lfo(11, 50, 100, 0.0, dur, period=8.0),
        "pad": AutomationCurve.sine_lfo(74, 40, 85, 0.0, dur, period=16.0)
    }

    produce_track(
        tracks={"guitar": guitar.notes, "flute": flute.notes, "pad": pad, "bass": bass,
                "solo_violin": solo_violin, "choir": choir},
        bpm=bpm,
        instruments={"guitar": 25, "flute": 73, "pad": 89, "bass": 32,
                     "solo_violin": 40, "choir": 52},
        path=OUT / "03_Dreams_Of_Father.mid",
        mood=Mood.CHAMBER, key=KEY_E_MINOR, chords=full_chords, cc_events=cc_events
    )


# =====================================================================
# IV. Подвальчик (Ах, какие звёзды...) — 75 BPM
# =====================================================================
def produce_basement_bar():
    """
    Gritty, intimate jazz bar feel. D Dorian.
    Electric Piano 1, Alto Sax, Double Bass.
    """
    bpm, dur = 75, 64.0
    prog_str = "i:4.0 - IV:4.0 - ii:4.0 - v:4.0"
    chords = types.parse_progression(prog_str, KEY_D_DORIAN)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    epiano_gen = ArpeggiatorGenerator(GeneratorParams(density=0.6, velocity_range=(65, 85), key_range_low=48, key_range_high=72), pattern="random")
    epiano = types.Track(name="epiano", notes=epiano_gen.render(full_chords, KEY_D_DORIAN, dur)).humanize(0.03, 4.0).swing(0.15)

    sax_gen = MelodyGenerator(GeneratorParams(density=0.4, complexity=0.5, velocity_range=(75, 100), key_range_low=60, key_range_high=80), phrase_length=4.0)
    sax = types.Track(name="sax", notes=sax_gen.render(full_chords, KEY_D_DORIAN, dur)).humanize(0.03, 5.0).swing(0.15)

    bass = BassGenerator(GeneratorParams(density=0.5, velocity_range=(70, 90), key_range_low=24, key_range_high=36)).render(full_chords, KEY_D_DORIAN, dur)
    
    # Slight expression swells on sax
    cc_events = {
        "sax": AutomationCurve.sine_lfo(11, 70, 110, 0.0, dur, period=4.0)
    }

    produce_track(
        tracks={"epiano": epiano.notes, "sax": sax.notes, "bass": bass},
        bpm=bpm,
        instruments={"epiano": 4, "sax": 65, "bass": 32},
        path=OUT / "04_Basement_Bar.mid",
        mood=Mood.CHAMBER, key=KEY_D_DORIAN, chords=full_chords, cc_events=cc_events
    )


# =====================================================================
# V. Бледный всадник — 120 BPM
# =====================================================================
def produce_pale_rider():
    """
    Apocalyptic, galloping Phrygian dread.
    Timpani, Tremolo Strings, French Horn, Contrabass.
    Accelerates towards the end.
    """
    bpm, dur = 120, 64.0
    prog_str = "i:4.0 - bII:4.0 - iv:4.0 - bII:4.0"
    chords = types.parse_progression(prog_str, KEY_G_PHRYGIAN)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    strings = StringsEnsembleGenerator(GeneratorParams(density=0.8, velocity_range=(70, 100), key_range_low=48, key_range_high=72)).render(full_chords, KEY_G_PHRYGIAN, dur)
    horn = MelodyGenerator(GeneratorParams(density=0.5, complexity=0.4, velocity_range=(85, 115), key_range_low=45, key_range_high=65), phrase_length=4.0).render(full_chords, KEY_G_PHRYGIAN, dur)
    
    # Galloping Timpani
    timpani = RhythmicAccentGenerator(preset="gallop", pitch=35, velocity_humanize=12, accent_strength=1.5).render(full_chords, KEY_G_PHRYGIAN, dur)
    bass = BassGenerator(GeneratorParams(density=0.6, velocity_range=(80, 105), key_range_low=24, key_range_high=36)).render(full_chords, KEY_G_PHRYGIAN, dur)

    # Plaintive solo violin — the rider's lament, cutting through the gallop
    solo_violin = ViolinGenerator(
        GeneratorParams(density=0.35, velocity_range=(75, 105), key_range_low=60, key_range_high=84),
        articulation="legato", vibrato=True, con_sordino=False
    ).render(full_chords, KEY_G_PHRYGIAN, dur)

    # Choir aahs — the apocalyptic chorus, voices of the dead
    choir = ChoirAahsGenerator(
        GeneratorParams(density=0.04, velocity_range=(45, 70), key_range_low=48, key_range_high=68)
    ).render(full_chords, KEY_G_PHRYGIAN, dur)

    # Accelerando from 120 to 145
    tempo_events = [(float(b), 120.0 + (145.0 - 120.0) * (b / dur)) for b in range(0, int(dur), 4)]

    cc_events = {
        "strings": AutomationCurve.exponential(11, 40, 110, 0.0, dur, exponent=1.5, steps=30),
        "horn": AutomationCurve.sine_lfo(11, 60, 127, 0.0, dur, period=4.0)
    }

    produce_track(
        tracks={"strings": strings, "horn": horn, "timpani": timpani, "bass": bass,
                "solo_violin": solo_violin, "choir": choir},
        bpm=bpm,
        instruments={"strings": 44, "horn": 60, "timpani": 47, "bass": 43,
                     "solo_violin": 40, "choir": 52},
        path=OUT / "05_Pale_Rider.mid",
        mood=Mood.CINEMATIC, key=KEY_G_PHRYGIAN, chords=full_chords, cc_events=cc_events, tempo_events=tempo_events
    )

if __name__ == "__main__":
    print("================================================================================")
    print("   БОРИС РЫЖИЙ — В РОССИИ РАССТАЮТСЯ НАВСЕГДА...")
    print("================================================================================")
    
    print("\n-> Compiling Track 1: В России расстаются навсегда...")
    produce_partings_forever()
    
    print("\n-> Compiling Track 2: Заезженная пластинка (А грустно было и уныло)...")
    produce_worn_out_record()
    
    print("\n-> Compiling Track 3: Сны об отце...")
    produce_dreams_of_father()
    
    print("\n-> Compiling Track 4: Подвальчик (Ах, какие звёзды)...")
    produce_basement_bar()

    print("\n-> Compiling Track 5: Бледный всадник...")
    produce_pale_rider()
    
    print("\n================================================================================")
    print("   POETRY ALBUM SUCCESSFULLY COMPILED!")
    print("   MIDI output saved in: " + str(OUT.resolve()))
    print("================================================================================")
