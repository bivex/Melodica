# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_ryzhy_1995.py — БОРИС РЫЖИЙ: ОТ САМОГО СЕРДЦА (1995)

Musical adaptation of six poems written by Boris Ryzhy in August–December 1995,
during his time at the Zaozersky mine and Kytlym settlement in the Urals.

Tracks:
  I.   Заозерский прииск (Zaozersky Mine)      — 55 BPM. D Phrygian.
  II.  Север (The North)                        — 50 BPM. B Locrian.
  III. Фонтанчик (The Fountain)                 — 72 BPM. F Lydian.
  IV.  Одним мурлыканьем (With One Purr)        — 80 BPM. G Ionian.
  V.   Летний сад: I–III (Summer Garden Pt.1)   — 60 BPM. E Minor.
  VI.  Летний сад: IV–V (Summer Garden Pt.2)    — 65 BPM. C# Minor.
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
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.composer.automation import AutomationCurve
from melodica.composer.album_pipeline import produce_track, Mood

# ── Scales ──────────────────────────────────────────────────────────────
KEY_D_PHRYGIAN   = types.Scale(root=2,  mode=types.Mode.PHRYGIAN)
KEY_B_LOCRIAN    = types.Scale(root=11, mode=types.Mode.LOCRIAN)
KEY_F_LYDIAN     = types.Scale(root=5,  mode=types.Mode.LYDIAN)
KEY_G_IONIAN     = types.Scale(root=7,  mode=types.Mode.IONIAN)
KEY_E_MINOR      = types.Scale(root=4,  mode=types.Mode.NATURAL_MINOR)
KEY_CS_MINOR     = types.Scale(root=1,  mode=types.Mode.HARMONIC_MINOR)

random.seed(1995)
OUT = Path("output/album_ryzhy_1995")
OUT.mkdir(parents=True, exist_ok=True)


def _loop_chords(prog_str: str, key: types.Scale, dur: float) -> list[types.ChordLabel]:
    chords = types.parse_progression(prog_str, key)
    result: list[types.ChordLabel] = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            result.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration
    return result


# =====================================================================
# I. Заозерский прииск — 55 BPM, D Phrygian
# =====================================================================
# Gritty mining settlement. Rough, cynical, drunken.
# Acoustic Guitar, Honky-tonk, Fretless Bass.
def track_01_zaozersky():
    bpm, dur = 55, 72.0
    prog = "i:4.0 - bII:4.0 - v:4.0 - iv:4.0"
    chords = _loop_chords(prog, KEY_D_PHRYGIAN, dur)

    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.6, velocity_range=(55, 80), key_range_low=40, key_range_high=60),
        pattern="up_down",
    ).render(chords, KEY_D_PHRYGIAN, dur)
    guitar = types.Track(name="guitar", notes=guitar).humanize(0.04, 6.0)

    honky = MelodyGenerator(
        GeneratorParams(density=0.35, complexity=0.5, velocity_range=(70, 95), key_range_low=55, key_range_high=79),
        phrase_length=8.0,
    ).render(chords, KEY_D_PHRYGIAN, dur)
    honky = types.Track(name="honky_tonk", notes=honky).humanize(0.05, 7.0)

    bass = BassGenerator(
        GeneratorParams(density=0.5, velocity_range=(65, 85), key_range_low=28, key_range_high=40)
    ).render(chords, KEY_D_PHRYGIAN, dur)

    cc_events = {
        "honky_tonk": AutomationCurve.sine_lfo(11, 55, 100, 0.0, dur, period=8.0),
    }

    produce_track(
        tracks={"guitar": guitar.notes, "honky_tonk": honky.notes, "bass": bass},
        bpm=bpm,
        instruments={"guitar": 24, "honky_tonk": 3, "bass": 35},
        path=OUT / "01_Zaozersky_Mine.mid",
        mood=Mood.INTIMATE, key=KEY_D_PHRYGIAN, chords=chords, cc_events=cc_events,
    )


# =====================================================================
# II. Север — 50 BPM, B Locrian
# =====================================================================
# A corpse in the taiga. Cold, sparse, reverent dread.
# Music Box, Strings, Tuba Bass.
def track_02_the_north():
    bpm, dur = 50, 80.0
    prog = "i:4.0 - bII:2.0 - iv:2.0 - bVII:4.0 - i:4.0"
    chords = _loop_chords(prog, KEY_B_LOCRIAN, dur)

    music_box = ArpeggiatorGenerator(
        GeneratorParams(density=0.35, velocity_range=(40, 65), key_range_low=72, key_range_high=96),
        pattern="up",
    ).render(chords, KEY_B_LOCRIAN, dur)
    music_box = types.Track(name="music_box", notes=music_box).humanize(0.02, 3.0)

    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.5, velocity_range=(45, 70), key_range_low=48, key_range_high=72)
    ).render(chords, KEY_B_LOCRIAN, dur)

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.15, velocity_range=(30, 50), key_range_low=36, key_range_high=60)
    ).render(chords, KEY_B_LOCRIAN, dur)

    bass = BassGenerator(
        GeneratorParams(density=0.3, velocity_range=(55, 75), key_range_low=24, key_range_high=36)
    ).render(chords, KEY_B_LOCRIAN, dur)

    cc_events = {
        "music_box": AutomationCurve.sine_lfo(74, 30, 80, 0.0, dur, period=16.0),
        "strings": AutomationCurve.exponential(11, 30, 90, 0.0, dur, exponent=1.3, steps=25),
    }

    produce_track(
        tracks={"music_box": music_box.notes, "strings": strings, "pad": pad, "bass": bass},
        bpm=bpm,
        instruments={"music_box": 10, "strings": 44, "pad": 89, "bass": 58},
        path=OUT / "02_The_North.mid",
        mood=Mood.AMBIENT, key=KEY_B_LOCRIAN, chords=chords, cc_events=cc_events,
    )


# =====================================================================
# III. Фонтанчик — 72 BPM, F Lydian
# =====================================================================
# Stone lions, autumn debris, quiet melancholy.
# Celesta, Oboe, Classical Guitar, Bass.
def track_03_fountain():
    bpm, dur = 72, 56.0
    prog = "I:4.0 - II:4.0 - V:4.0 - I:4.0"
    chords = _loop_chords(prog, KEY_F_LYDIAN, dur)

    celesta = ArpeggiatorGenerator(
        GeneratorParams(density=0.5, velocity_range=(50, 75), key_range_low=72, key_range_high=96),
        pattern="up_down",
    ).render(chords, KEY_F_LYDIAN, dur)
    celesta = types.Track(name="celesta", notes=celesta).humanize(0.02, 3.0)

    oboe = MelodyGenerator(
        GeneratorParams(density=0.3, complexity=0.4, velocity_range=(65, 90), key_range_low=60, key_range_high=84),
        phrase_length=8.0,
    ).render(chords, KEY_F_LYDIAN, dur)
    oboe = types.Track(name="oboe", notes=oboe).humanize(0.02, 4.0)

    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.4, velocity_range=(50, 70), key_range_low=40, key_range_high=60),
        pattern="random",
    ).render(chords, KEY_F_LYDIAN, dur)
    guitar = types.Track(name="guitar", notes=guitar).humanize(0.03, 4.0)

    bass = BassGenerator(
        GeneratorParams(density=0.45, velocity_range=(55, 75), key_range_low=28, key_range_high=40)
    ).render(chords, KEY_F_LYDIAN, dur)

    cc_events = {
        "oboe": AutomationCurve.sine_lfo(11, 50, 95, 0.0, dur, period=6.0),
        "celesta": AutomationCurve.sine_lfo(74, 30, 70, 0.0, dur, period=12.0),
    }

    produce_track(
        tracks={"celesta": celesta.notes, "oboe": oboe.notes, "guitar": guitar.notes, "bass": bass},
        bpm=bpm,
        instruments={"celesta": 8, "oboe": 68, "guitar": 24, "bass": 32},
        path=OUT / "03_The_Fountain.mid",
        mood=Mood.CHAMBER, key=KEY_F_LYDIAN, chords=chords, cc_events=cc_events,
    )


# =====================================================================
# IV. Одним мурлыканьем — 80 BPM, G Ionian (Major)
# =====================================================================
# Gentle, bittersweet, purring tenderness.
# Warm Pad, Clarinet, Fingerpicked Guitar.
def track_04_one_purr():
    bpm, dur = 80, 52.0
    prog = "I:3.0 - vi:3.0 - IV:3.0 - V:3.0"
    chords = _loop_chords(prog, KEY_G_IONIAN, dur)

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.2, velocity_range=(40, 60), key_range_low=48, key_range_high=72)
    ).render(chords, KEY_G_IONIAN, dur)

    clarinet = MelodyGenerator(
        GeneratorParams(density=0.4, complexity=0.35, velocity_range=(65, 90), key_range_low=55, key_range_high=79),
        phrase_length=6.0,
    ).render(chords, KEY_G_IONIAN, dur)
    clarinet = types.Track(name="clarinet", notes=clarinet).humanize(0.02, 3.0)

    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.65, velocity_range=(55, 75), key_range_low=43, key_range_high=67),
        pattern="up_down",
    ).render(chords, KEY_G_IONIAN, dur)
    guitar = types.Track(name="guitar", notes=guitar).humanize(0.02, 3.0)

    bass = BassGenerator(
        GeneratorParams(density=0.4, velocity_range=(55, 75), key_range_low=28, key_range_high=40)
    ).render(chords, KEY_G_IONIAN, dur)

    counter = CountermelodyGenerator(
        GeneratorParams(density=0.25, complexity=0.3, velocity_range=(50, 70), key_range_low=67, key_range_high=84)
    ).render(chords, KEY_G_IONIAN, dur)

    cc_events = {
        "clarinet": AutomationCurve.sine_lfo(11, 55, 100, 0.0, dur, period=6.0),
        "pad": AutomationCurve.sine_lfo(74, 35, 75, 0.0, dur, period=16.0),
    }

    produce_track(
        tracks={"pad": pad, "clarinet": clarinet.notes, "guitar": guitar.notes, "bass": bass, "counter": counter},
        bpm=bpm,
        instruments={"pad": 89, "clarinet": 71, "guitar": 25, "bass": 32, "counter": 73},
        path=OUT / "04_With_One_Purr.mid",
        mood=Mood.INTIMATE, key=KEY_G_IONIAN, chords=chords, cc_events=cc_events,
    )


# =====================================================================
# V. Летний сад: I–III — 60 BPM, E Natural Minor
# =====================================================================
# Swans, parting, angels weeping. Romantic tragedy.
# Piano, Violin, Cello, Bass.
def track_05_summer_garden_1():
    bpm, dur = 60, 80.0
    prog = "i:4.0 - VI:4.0 - III:4.0 - V:4.0"
    chords = _loop_chords(prog, KEY_E_MINOR, dur)

    piano = ArpeggiatorGenerator(
        GeneratorParams(density=0.55, velocity_range=(50, 75), key_range_low=48, key_range_high=72),
        pattern="up_down",
    ).render(chords, KEY_E_MINOR, dur)
    piano = types.Track(name="piano", notes=piano).humanize(0.02, 3.0)

    violin = MelodyGenerator(
        GeneratorParams(density=0.4, complexity=0.45, velocity_range=(70, 95), key_range_low=64, key_range_high=88),
        phrase_length=8.0,
    ).render(chords, KEY_E_MINOR, dur)
    violin = types.Track(name="violin", notes=violin).humanize(0.03, 5.0)

    cello = CountermelodyGenerator(
        GeneratorParams(density=0.35, complexity=0.3, velocity_range=(55, 80), key_range_low=36, key_range_high=60)
    ).render(chords, KEY_E_MINOR, dur)

    bass = BassGenerator(
        GeneratorParams(density=0.4, velocity_range=(55, 75), key_range_low=28, key_range_high=40)
    ).render(chords, KEY_E_MINOR, dur)

    cc_events = {
        "violin": AutomationCurve.sine_lfo(11, 50, 105, 0.0, dur, period=8.0),
        "cello": AutomationCurve.sine_lfo(74, 35, 75, 0.0, dur, period=12.0),
    }

    produce_track(
        tracks={"piano": piano.notes, "violin": violin.notes, "cello": cello, "bass": bass},
        bpm=bpm,
        instruments={"piano": 0, "violin": 40, "cello": 42, "bass": 32},
        path=OUT / "05_Summer_Garden_Pt1.mid",
        mood=Mood.CHAMBER, key=KEY_E_MINOR, chords=chords, cc_events=cc_events,
    )


# =====================================================================
# VI. Летний сад: IV–V — 65 BPM, C# Harmonic Minor
# =====================================================================
# The artist-violinist, September crown of leaves, mortality.
# Harpsichord, Viola, Oboe, Timpani, Bass.
def track_06_summer_garden_2():
    bpm, dur = 65, 72.0
    prog = "i:4.0 - bII:4.0 - iv:4.0 - V:4.0"
    chords = _loop_chords(prog, KEY_CS_MINOR, dur)

    harpsichord = ArpeggiatorGenerator(
        GeneratorParams(density=0.5, velocity_range=(55, 80), key_range_low=48, key_range_high=72),
        pattern="up",
    ).render(chords, KEY_CS_MINOR, dur)
    harpsichord = types.Track(name="harpsichord", notes=harpsichord).humanize(0.02, 3.0)

    viola = MelodyGenerator(
        GeneratorParams(density=0.35, complexity=0.4, velocity_range=(65, 90), key_range_low=48, key_range_high=72),
        phrase_length=8.0,
    ).render(chords, KEY_CS_MINOR, dur)
    viola = types.Track(name="viola", notes=viola).humanize(0.03, 4.0)

    oboe = CountermelodyGenerator(
        GeneratorParams(density=0.3, complexity=0.35, velocity_range=(55, 80), key_range_low=60, key_range_high=84)
    ).render(chords, KEY_CS_MINOR, dur)

    timpani = RhythmicAccentGenerator(
        preset="march", pitch=36, velocity_humanize=10, accent_strength=0.8
    ).render(chords, KEY_CS_MINOR, dur)

    bass = BassGenerator(
        GeneratorParams(density=0.45, velocity_range=(60, 80), key_range_low=24, key_range_high=36)
    ).render(chords, KEY_CS_MINOR, dur)

    # Decelerando: 65 → 55 BPM
    tempo_events = [(float(b), 65.0 - 10.0 * (b / dur)) for b in range(0, int(dur), 4)]

    cc_events = {
        "viola": AutomationCurve.sine_lfo(11, 50, 100, 0.0, dur, period=8.0),
        "oboe": AutomationCurve.sine_lfo(74, 40, 80, 0.0, dur, period=10.0),
    }

    produce_track(
        tracks={"harpsichord": harpsichord.notes, "viola": viola.notes, "oboe": oboe, "timpani": timpani, "bass": bass},
        bpm=bpm,
        instruments={"harpsichord": 6, "viola": 41, "oboe": 68, "timpani": 47, "bass": 32},
        path=OUT / "06_Summer_Garden_Pt2.mid",
        mood=Mood.CINEMATIC, key=KEY_CS_MINOR, chords=chords, cc_events=cc_events, tempo_events=tempo_events,
    )


if __name__ == "__main__":
    print("=" * 80)
    print("   БОРИС РЫЖИЙ — ОТ САМОГО СЕРДЦА (1995)")
    print("=" * 80)

    print("\n-> Compiling Track 1: Заозерский прииск...")
    track_01_zaozersky()

    print("\n-> Compiling Track 2: Север...")
    track_02_the_north()

    print("\n-> Compiling Track 3: Фонтанчик...")
    track_03_fountain()

    print("\n-> Compiling Track 4: Одним мурлыканьем...")
    track_04_one_purr()

    print("\n-> Compiling Track 5: Летний сад (I–III)...")
    track_05_summer_garden_1()

    print("\n-> Compiling Track 6: Летний сад (IV–V)...")
    track_06_summer_garden_2()

    print("\n" + "=" * 80)
    print("   АЛЬБОМ «ОТ САМОГО СЕРДЦА» СГЕНЕРИРОВАН!")
    print("   MIDI: " + str(OUT.resolve()))
    print("=" * 80)
