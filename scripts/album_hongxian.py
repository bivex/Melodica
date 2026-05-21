# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_hongxian.py — 红线成灰 (Red Thread to Ashes)

Five songs inspired by classical Chinese poetry motifs:
moonlit bridges, falling petals, diverging roads, silent snow, and sea winds.

Tracks:
  I.   月光旧桥 (Moonlight at the Old Bridge)     — 48 BPM. E Kumoi.
  II.  花落青苔 (Petals on the Moss)              — 60 BPM. D Hirojoshi.
  III. 长街孤城 (Lonely City of Long Streets)     — 72 BPM. B Byzantine.
  IV.  雪落无声 (Silent Snow)                      — 42 BPM. C# Pelog Approx.
  V.   海风旧誓 (Sea Wind, Old Vows)              — 88 BPM. A Minor Pentatonic.
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
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.composer.automation import AutomationCurve
from melodica.composer.album_pipeline import produce_track, Mood

# ── Scales ──────────────────────────────────────────────────────────────
KEY_E_KUMOI     = types.Scale(root=4,  mode=types.Mode.KUMOI)
KEY_D_HIROJOSHI = types.Scale(root=2,  mode=types.Mode.HIROJOSHI)
KEY_B_BYZANTINE = types.Scale(root=11, mode=types.Mode.BYZANTINE)
KEY_CS_PELOG    = types.Scale(root=1,  mode=types.Mode.PELOG_APPROX)
KEY_A_MINPENT   = types.Scale(root=9,  mode=types.Mode.MINOR_PENTATONIC)

random.seed(618)  # Tang dynasty year 618
OUT = Path("output/album_hongxian")
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
# I. 月光旧桥 — 48 BPM, E Kumoi
# =====================================================================
# Moonlight, old bridge, red thread turned to ash, waiting a thousand years.
# Koto (drawn from harmonics), Shakuhachi (melody), Guzheng pad, Bass.
def track_01_moonlight_bridge():
    bpm, dur = 48, 76.0
    prog = "i:4.0 - v:4.0 - bIII:4.0 - iv:4.0"
    chords = _loop_chords(prog, KEY_E_KUMOI, dur)

    koto = ArpeggiatorGenerator(
        GeneratorParams(density=0.4, velocity_range=(45, 70), key_range_low=64, key_range_high=88),
        pattern="up",
    ).render(chords, KEY_E_KUMOI, dur)
    koto = types.Track(name="koto", notes=koto).humanize(0.03, 5.0)

    shakuhachi = MelodyGenerator(
        GeneratorParams(density=0.25, complexity=0.35, velocity_range=(55, 85), key_range_low=60, key_range_high=84),
        phrase_length=12.0,
    ).render(chords, KEY_E_KUMOI, dur)
    shakuhachi = types.Track(name="shakuhachi", notes=shakuhachi).humanize(0.04, 8.0)

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.15, velocity_range=(30, 50), key_range_low=36, key_range_high=60)
    ).render(chords, KEY_E_KUMOI, dur)

    bass = BassGenerator(
        GeneratorParams(density=0.3, velocity_range=(45, 65), key_range_low=28, key_range_high=40)
    ).render(chords, KEY_E_KUMOI, dur)

    cc_events = {
        "shakuhachi": AutomationCurve.sine_lfo(11, 40, 90, 0.0, dur, period=12.0),
        "koto": AutomationCurve.sine_lfo(74, 25, 65, 0.0, dur, period=16.0),
    }

    produce_track(
        tracks={"koto": koto.notes, "shakuhachi": shakuhachi.notes, "pad": pad, "bass": bass},
        bpm=bpm,
        instruments={"koto": 15, "shakuhachi": 75, "pad": 98, "bass": 34},
        path=OUT / "01_Moonlight_Old_Bridge.mid",
        mood=Mood.AMBIENT, key=KEY_E_KUMOI, chords=chords, cc_events=cc_events,
    )


# =====================================================================
# II. 花落青苔 — 60 BPM, D Hirojoshi
# =====================================================================
# Flowers bloomed and fell, tears on moss, unread letter, cold rain.
# Piano, Erhu (violin), Cello counter, Bass.
def track_02_petals_moss():
    bpm, dur = 60, 64.0
    prog = "i:4.0 - bIII:4.0 - v:4.0 - iv:4.0"
    chords = _loop_chords(prog, KEY_D_HIROJOSHI, dur)

    piano = ArpeggiatorGenerator(
        GeneratorParams(density=0.5, velocity_range=(45, 70), key_range_low=48, key_range_high=72),
        pattern="up_down",
    ).render(chords, KEY_D_HIROJOSHI, dur)
    piano = types.Track(name="piano", notes=piano).humanize(0.02, 3.0)

    erhu = MelodyGenerator(
        GeneratorParams(density=0.35, complexity=0.4, velocity_range=(60, 90), key_range_low=62, key_range_high=86),
        phrase_length=8.0,
    ).render(chords, KEY_D_HIROJOSHI, dur)
    erhu = types.Track(name="erhu", notes=erhu).humanize(0.03, 6.0)

    cello = CountermelodyGenerator(
        GeneratorParams(density=0.3, complexity=0.25, velocity_range=(50, 70), key_range_low=36, key_range_high=60)
    ).render(chords, KEY_D_HIROJOSHI, dur)

    bass = BassGenerator(
        GeneratorParams(density=0.35, velocity_range=(50, 70), key_range_low=28, key_range_high=40)
    ).render(chords, KEY_D_HIROJOSHI, dur)

    cc_events = {
        "erhu": AutomationCurve.sine_lfo(11, 45, 100, 0.0, dur, period=8.0),
    }

    produce_track(
        tracks={"piano": piano.notes, "erhu": erhu.notes, "cello": cello, "bass": bass},
        bpm=bpm,
        instruments={"piano": 0, "erhu": 110, "cello": 42, "bass": 32},
        path=OUT / "02_Petals_on_the_Moss.mid",
        mood=Mood.INTIMATE, key=KEY_D_HIROJOSHI, chords=chords, cc_events=cc_events,
    )

def main():
    print("Generating HONGXIAN album...")
    track_01_moonlight_bridge()
    track_02_petals_moss()
    # Add other tracks as they are implemented or needed
    print("HONGXIAN generation complete.")

if __name__ == "__main__":
    main()


# =====================================================================
# III. 长街孤城 — 72 BPM, B Byzantine
# =====================================================================
# Long streets, diverging paths, hope for next life.
# Electric Piano, Trumpet, Strings, Bass.
def track_03_lonely_city():
    bpm, dur = 72, 56.0
    prog = "i:4.0 - bII:4.0 - bVI:4.0 - V:4.0"
    chords = _loop_chords(prog, KEY_B_BYZANTINE, dur)

    epiano = ArpeggiatorGenerator(
        GeneratorParams(density=0.55, velocity_range=(55, 80), key_range_low=48, key_range_high=72),
        pattern="random",
    ).render(chords, KEY_B_BYZANTINE, dur)
    epiano = types.Track(name="epiano", notes=epiano).humanize(0.02, 4.0)

    trumpet = MelodyGenerator(
        GeneratorParams(density=0.4, complexity=0.45, velocity_range=(70, 100), key_range_low=58, key_range_high=82),
        phrase_length=6.0,
    ).render(chords, KEY_B_BYZANTINE, dur)
    trumpet = types.Track(name="trumpet", notes=trumpet).humanize(0.03, 5.0)

    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.4, velocity_range=(45, 65), key_range_low=48, key_range_high=72)
    ).render(chords, KEY_B_BYZANTINE, dur)

    bass = BassGenerator(
        GeneratorParams(density=0.45, velocity_range=(60, 80), key_range_low=28, key_range_high=40)
    ).render(chords, KEY_B_BYZANTINE, dur)

    cc_events = {
        "trumpet": AutomationCurve.sine_lfo(11, 55, 105, 0.0, dur, period=6.0),
        "strings": AutomationCurve.exponential(11, 30, 80, 0.0, dur, exponent=1.2, steps=20),
    }

    produce_track(
        tracks={"epiano": epiano.notes, "trumpet": trumpet.notes, "strings": strings, "bass": bass},
        bpm=bpm,
        instruments={"epiano": 4, "trumpet": 56, "strings": 44, "bass": 32},
        path=OUT / "03_Lonely_City.mid",
        mood=Mood.CINEMATIC, key=KEY_B_BYZANTINE, chords=chords, cc_events=cc_events,
    )


# =====================================================================
# IV. 雪落无声 — 42 BPM, C# Pelog Approx
# =====================================================================
# Silent snow, empty courtyard, old sorrow under the moon.
# Music Box, Choir Pad, Guzheng (harp), Bass.
def track_04_silent_snow():
    bpm, dur = 42, 84.0
    prog = "i:4.0 - bII:4.0 - v:4.0 - iv:4.0"
    chords = _loop_chords(prog, KEY_CS_PELOG, dur)

    music_box = ArpeggiatorGenerator(
        GeneratorParams(density=0.3, velocity_range=(35, 60), key_range_low=72, key_range_high=96),
        pattern="up",
    ).render(chords, KEY_CS_PELOG, dur)
    music_box = types.Track(name="music_box", notes=music_box).humanize(0.02, 3.0)

    choir = AmbientPadGenerator(
        GeneratorParams(density=0.12, velocity_range=(30, 45), key_range_low=36, key_range_high=60)
    ).render(chords, KEY_CS_PELOG, dur)

    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.4, velocity_range=(40, 65), key_range_low=48, key_range_high=72),
        pattern="up_down",
    ).render(chords, KEY_CS_PELOG, dur)
    harp = types.Track(name="harp", notes=harp).humanize(0.02, 4.0)

    bass = BassGenerator(
        GeneratorParams(density=0.25, velocity_range=(40, 60), key_range_low=24, key_range_high=36)
    ).render(chords, KEY_CS_PELOG, dur)

    cc_events = {
        "music_box": AutomationCurve.sine_lfo(74, 20, 60, 0.0, dur, period=20.0),
        "choir": AutomationCurve.sine_lfo(11, 25, 55, 0.0, dur, period=24.0),
    }

    produce_track(
        tracks={"music_box": music_box.notes, "choir": choir, "harp": harp.notes, "bass": bass},
        bpm=bpm,
        instruments={"music_box": 10, "choir": 52, "harp": 46, "bass": 34},
        path=OUT / "04_Silent_Snow.mid",
        mood=Mood.AMBIENT, key=KEY_CS_PELOG, chords=chords, cc_events=cc_events,
    )


# =====================================================================
# V. 海风旧誓 — 88 BPM, A Minor Pentatonic
# =====================================================================
# Sea wind, drifting boat, love buried in wine, sleep until next life.
# Steel Drum (resonant), Flute, Acoustic Guitar, Finger Bass.
def track_05_sea_wind():
    bpm, dur = 88, 60.0
    prog = "i:4.0 - bIII:4.0 - iv:4.0 - v:4.0"
    chords = _loop_chords(prog, KEY_A_MINPENT, dur)

    flute = MelodyGenerator(
        GeneratorParams(density=0.35, complexity=0.4, velocity_range=(60, 90), key_range_low=72, key_range_high=96),
        phrase_length=8.0,
    ).render(chords, KEY_A_MINPENT, dur)
    flute = types.Track(name="flute", notes=flute).humanize(0.02, 4.0)

    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.6, velocity_range=(55, 75), key_range_low=40, key_range_high=64),
        pattern="up_down",
    ).render(chords, KEY_A_MINPENT, dur)
    guitar = types.Track(name="guitar", notes=guitar).humanize(0.03, 4.0)

    counter = CountermelodyGenerator(
        GeneratorParams(density=0.25, complexity=0.3, velocity_range=(45, 65), key_range_low=60, key_range_high=84)
    ).render(chords, KEY_A_MINPENT, dur)

    bass = BassGenerator(
        GeneratorParams(density=0.5, velocity_range=(60, 85), key_range_low=28, key_range_high=40)
    ).render(chords, KEY_A_MINPENT, dur)

    cc_events = {
        "flute": AutomationCurve.sine_lfo(11, 50, 95, 0.0, dur, period=8.0),
        "guitar": AutomationCurve.sine_lfo(74, 30, 70, 0.0, dur, period=12.0),
    }

    produce_track(
        tracks={"flute": flute.notes, "guitar": guitar.notes, "counter": counter, "bass": bass},
        bpm=bpm,
        instruments={"flute": 73, "guitar": 25, "counter": 75, "bass": 35},
        path=OUT / "05_Sea_Wind_Old_Vows.mid",
        mood=Mood.CHAMBER, key=KEY_A_MINPENT, chords=chords, cc_events=cc_events,
    )


if __name__ == "__main__":
    print("=" * 80)
    print("   红线成灰 — RED THREAD TO ASHES")
    print("=" * 80)

    print("\n-> Compiling Track 1: 月光旧桥 (Moonlight at the Old Bridge)...")
    track_01_moonlight_bridge()

    print("\n-> Compiling Track 2: 花落青苔 (Petals on the Moss)...")
    track_02_petals_moss()

    print("\n-> Compiling Track 3: 长街孤城 (Lonely City of Long Streets)...")
    track_03_lonely_city()

    print("\n-> Compiling Track 4: 雪落无声 (Silent Snow)...")
    track_04_silent_snow()

    print("\n-> Compiling Track 5: 海风旧誓 (Sea Wind, Old Vows)...")
    track_05_sea_wind()

    print("\n" + "=" * 80)
    print("   红线成灰 — АЛЬБОМ СГЕНЕРИРОВАН!")
    print("   MIDI: " + str(OUT.resolve()))
    print("=" * 80)
