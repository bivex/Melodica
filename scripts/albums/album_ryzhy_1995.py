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
from melodica.composer.scene_renderer import StitchResult, render_scene_graph
from melodica.composer.automation import AutomationCurve
from melodica.composer.album_pipeline import Mood
from melodica.midi import export_multitrack_midi
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.accent import RhythmicAccentGenerator
from melodica.generators.countermelody import CountermelodyGenerator

# ── Scales ──────────────────────────────────────────────────────────────
KEY_D_PHRYGIAN = types.Scale(root=2, mode=types.Mode.PHRYGIAN)
KEY_B_LOCRIAN = types.Scale(root=11, mode=types.Mode.LOCRIAN)
KEY_F_LYDIAN = types.Scale(root=5, mode=types.Mode.LYDIAN)
KEY_G_IONIAN = types.Scale(root=7, mode=types.Mode.IONIAN)
KEY_E_MINOR = types.Scale(root=4, mode=types.Mode.NATURAL_MINOR)
KEY_CS_MINOR = types.Scale(root=1, mode=types.Mode.HARMONIC_MINOR)

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
            result.append(
                types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration)
            )
            t += c.duration
    return result


# =====================================================================
# I. Заозерский прииск — 55 BPM, D Phrygian
# =====================================================================
# Gritty mining settlement. Rough, cynical, drunken.
# Acoustic Guitar, Honky-tonk, Fretless Bass.
def build_scene_01_zaozersky() -> types.Scene:
    bpm, dur = 55, 72.0
    prog = "i:4.0 - bII:4.0 - v:4.0 - iv:4.0"
    chords = _loop_chords(prog, KEY_D_PHRYGIAN, dur)

    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.6, velocity_range=(55, 80), key_range_low=40, key_range_high=60),
        pattern="up_down",
    ).render(chords, KEY_D_PHRYGIAN, dur)
    guitar = types.Track(name="guitar", notes=guitar).humanize(0.04, 6.0)

    honky = MelodyGenerator(
        GeneratorParams(
            density=0.35,
            complexity=0.5,
            velocity_range=(70, 95),
            key_range_low=55,
            key_range_high=79,
        ),
        phrase_length=8.0,
    ).render(chords, KEY_D_PHRYGIAN, dur)
    honky = types.Track(name="honky_tonk", notes=honky).humanize(0.05, 7.0)

    bass = BassGenerator(
        GeneratorParams(density=0.5, velocity_range=(65, 85), key_range_low=28, key_range_high=40)
    ).render(chords, KEY_D_PHRYGIAN, dur)

    cc_events = {
        "honky_tonk": AutomationCurve.sine_lfo(11, 55, 100, 0.0, dur, period=8.0),
    }

    return types.Scene(
        id="zaozersky",
        label="I. Заозерский прииск",
        key=KEY_D_PHRYGIAN,
        bpm=bpm,
        mood="intimate",
        duration_bars=int(dur / 4.0),
        section_type="intro",
        tags=["mine", "phrygian", "drunken"],
        tracks={"guitar": guitar.notes, "honky_tonk": honky.notes, "bass": bass},
        progression=chords,
    )


# =====================================================================
# II. Север — 50 BPM, B Locrian
# =====================================================================
# A corpse in the taiga. Cold, sparse, reverent dread.
# Music Box, Strings, Tuba Bass.
def build_scene_02_the_north() -> types.Scene:
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

    return types.Scene(
        id="north",
        label="II. Север",
        key=KEY_B_LOCRIAN,
        bpm=bpm,
        mood="ambient",
        duration_bars=int(dur / 4.0),
        section_type="verse",
        tags=["taiga", "locrian", "cold"],
        tracks={"music_box": music_box.notes, "strings": strings, "pad": pad, "bass": bass},
        progression=chords,
    )


# =====================================================================
# III. Фонтанчик — 72 BPM, F Lydian
# =====================================================================
# Stone lions, autumn debris, quiet melancholy.
# Celesta, Oboe, Classical Guitar, Bass.
def build_scene_03_fountain() -> types.Scene:
    bpm, dur = 72, 56.0
    prog = "I:4.0 - II:4.0 - V:4.0 - I:4.0"
    chords = _loop_chords(prog, KEY_F_LYDIAN, dur)

    celesta = ArpeggiatorGenerator(
        GeneratorParams(density=0.5, velocity_range=(50, 75), key_range_low=72, key_range_high=96),
        pattern="up_down",
    ).render(chords, KEY_F_LYDIAN, dur)
    celesta = types.Track(name="celesta", notes=celesta).humanize(0.02, 3.0)

    oboe = MelodyGenerator(
        GeneratorParams(
            density=0.3,
            complexity=0.4,
            velocity_range=(65, 90),
            key_range_low=60,
            key_range_high=84,
        ),
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

    return types.Scene(
        id="fountain",
        label="III. Фонтанчик",
        key=KEY_F_LYDIAN,
        bpm=bpm,
        mood="chamber",
        duration_bars=int(dur / 4.0),
        section_type="verse",
        tags=["lydian", "autumn", "melancholy"],
        tracks={"celesta": celesta.notes, "oboe": oboe.notes, "guitar": guitar.notes, "bass": bass},
        progression=chords,
    )


# =====================================================================
# IV. Одним мурлыканьем — 80 BPM, G Ionian (Major)
# =====================================================================
# Gentle, bittersweet, purring tenderness.
# Warm Pad, Clarinet, Fingerpicked Guitar.
def build_scene_04_one_purr() -> types.Scene:
    bpm, dur = 80, 52.0
    prog = "I:3.0 - vi:3.0 - IV:3.0 - V:3.0"
    chords = _loop_chords(prog, KEY_G_IONIAN, dur)

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.2, velocity_range=(40, 60), key_range_low=48, key_range_high=72)
    ).render(chords, KEY_G_IONIAN, dur)

    clarinet = MelodyGenerator(
        GeneratorParams(
            density=0.4,
            complexity=0.35,
            velocity_range=(65, 90),
            key_range_low=55,
            key_range_high=79,
        ),
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
        GeneratorParams(
            density=0.25,
            complexity=0.3,
            velocity_range=(50, 70),
            key_range_low=67,
            key_range_high=84,
        )
    ).render(chords, KEY_G_IONIAN, dur)

    return types.Scene(
        id="one_purr",
        label="IV. Одним мурлыканьем",
        key=KEY_G_IONIAN,
        bpm=bpm,
        mood="intimate",
        duration_bars=int(dur / 4.0),
        section_type="chorus",
        tags=["major", "tenderness", "ionian"],
        tracks={
            "pad": pad,
            "clarinet": clarinet.notes,
            "guitar": guitar.notes,
            "bass": bass,
            "counter": counter,
        },
        progression=chords,
    )


# =====================================================================
# V. Летний сад: I–III — 60 BPM, E Natural Minor
# =====================================================================
# Swans, parting, angels weeping. Romantic tragedy.
# Piano, Violin, Cello, Bass.
def build_scene_05_summer_garden_1() -> types.Scene:
    bpm, dur = 60, 80.0
    prog = "i:4.0 - VI:4.0 - III:4.0 - V:4.0"
    chords = _loop_chords(prog, KEY_E_MINOR, dur)

    piano = ArpeggiatorGenerator(
        GeneratorParams(density=0.55, velocity_range=(50, 75), key_range_low=48, key_range_high=72),
        pattern="up_down",
    ).render(chords, KEY_E_MINOR, dur)
    piano = types.Track(name="piano", notes=piano).humanize(0.02, 3.0)

    violin = MelodyGenerator(
        GeneratorParams(
            density=0.4,
            complexity=0.45,
            velocity_range=(70, 95),
            key_range_low=64,
            key_range_high=88,
        ),
        phrase_length=8.0,
    ).render(chords, KEY_E_MINOR, dur)
    violin = types.Track(name="violin", notes=violin).humanize(0.03, 5.0)

    cello = CountermelodyGenerator(
        GeneratorParams(
            density=0.35,
            complexity=0.3,
            velocity_range=(55, 80),
            key_range_low=36,
            key_range_high=60,
        )
    ).render(chords, KEY_E_MINOR, dur)

    bass = BassGenerator(
        GeneratorParams(density=0.4, velocity_range=(55, 75), key_range_low=28, key_range_high=40)
    ).render(chords, KEY_E_MINOR, dur)

    return types.Scene(
        id="garden1",
        label="V. Летний сад: I–III",
        key=KEY_E_MINOR,
        bpm=bpm,
        mood="chamber",
        duration_bars=int(dur / 4.0),
        section_type="bridge",
        tags=["minor", "romantic", "tragedy"],
        tracks={"piano": piano.notes, "violin": violin.notes, "cello": cello, "bass": bass},
        progression=chords,
    )


# =====================================================================
# VI. Летний сад: IV–V — 65 BPM, C# Harmonic Minor
# =====================================================================
# The artist-violinist, September crown of leaves, mortality.
# Harpsichord, Viola, Oboe, Timpani, Bass.
def build_scene_06_summer_garden_2() -> types.Scene:
    bpm, dur = 65, 72.0
    prog = "i:4.0 - bII:4.0 - iv:4.0 - V:4.0"
    chords = _loop_chords(prog, KEY_CS_MINOR, dur)

    harpsichord = ArpeggiatorGenerator(
        GeneratorParams(density=0.5, velocity_range=(55, 80), key_range_low=48, key_range_high=72),
        pattern="up",
    ).render(chords, KEY_CS_MINOR, dur)
    harpsichord = types.Track(name="harpsichord", notes=harpsichord).humanize(0.02, 3.0)

    viola = MelodyGenerator(
        GeneratorParams(
            density=0.35,
            complexity=0.4,
            velocity_range=(65, 90),
            key_range_low=48,
            key_range_high=72,
        ),
        phrase_length=8.0,
    ).render(chords, KEY_CS_MINOR, dur)
    viola = types.Track(name="viola", notes=viola).humanize(0.03, 4.0)

    oboe = CountermelodyGenerator(
        GeneratorParams(
            density=0.3,
            complexity=0.35,
            velocity_range=(55, 80),
            key_range_low=60,
            key_range_high=84,
        )
    ).render(chords, KEY_CS_MINOR, dur)

    timpani = RhythmicAccentGenerator(
        preset="march", pitch=36, velocity_humanize=10, accent_strength=0.8
    ).render(chords, KEY_CS_MINOR, dur)

    bass = BassGenerator(
        GeneratorParams(density=0.45, velocity_range=(60, 80), key_range_low=24, key_range_high=36)
    ).render(chords, KEY_CS_MINOR, dur)

    # Melody-track CC events (stored for use after rendering)
    cc_events = {
        "viola": AutomationCurve.sine_lfo(11, 50, 100, 0.0, dur, period=8.0),
        "oboe": AutomationCurve.sine_lfo(74, 40, 80, 0.0, dur, period=10.0),
    }

    return types.Scene(
        id="garden2",
        label="VI. Летний сад: IV–V",
        key=KEY_CS_MINOR,
        bpm=bpm,
        mood="cinematic",
        duration_bars=int(dur / 4.0),
        section_type="outro",
        tags=["harmonic_minor", "mortality", "sepulchral"],
        tracks={
            "harpsichord": harpsichord.notes,
            "viola": viola.notes,
            "oboe": oboe,
            "timpani": timpani,
            "bass": bass,
        },
        progression=chords,
    )


if __name__ == "__main__":
    from melodica.composer.scene_renderer import StitchResult, render_scene_graph
    from melodica.midi import export_multitrack_midi
    from melodica.types import SceneTransition, TransitionType

    # ── Build all six scenes ─────────────────────────────────────────
    s1 = build_scene_01_zaozersky()
    s2 = build_scene_02_the_north()
    s3 = build_scene_03_fountain()
    s4 = build_scene_04_one_purr()
    s5 = build_scene_05_summer_garden_1()
    s6 = build_scene_06_summer_garden_2()

    # ── Transition plan ─────────────────────────────────────────────
    # I→II  FADE  (phrygian starkness → locrian cold, BPM 55→50)
    # II→III CUT   (taiga → spring rebirth, BPM 50→72)
    # III→IV CUT   (Lydian → Ionian opening-up)
    # IV→V  FADE  (major tenderness → minor tragedy, BPM 80→60)
    # V→VI  CROSSFADE (minor → harmonic minor, darkening)
    transitions = [
        SceneTransition("zaozersky", "north", TransitionType.FADE, duration_bars=2),
        SceneTransition("north", "fountain", TransitionType.CUT, duration_bars=0),
        SceneTransition("fountain", "one_purr", TransitionType.CUT, duration_bars=0),
        SceneTransition("one_purr", "garden1", TransitionType.FADE, duration_bars=2),
        SceneTransition("garden1", "garden2", TransitionType.CROSSFADE, duration_bars=1),
    ]

    graph = types.SceneGraph(
        scenes={s.id: s for s in (s1, s2, s3, s4, s5, s6)},
        default_order=[s.id for s in (s1, s2, s3, s4, s5, s6)],
        transitions=transitions,
    )

    # ── Instruments mapping (auto-assigned per track) ───────────────
    instrument_map = {
        "guitar": 24,  # Acoustic Guitar
        "honky_tonk": 3,  # Honky-tonk Piano
        "bass": 35,  # Fretless Bass
        "music_box": 10,  # Music Box
        "strings": 44,  # Tremolo Strings
        "pad": 89,  # Pad 2 Warm
        "celesta": 8,  # Celesta
        "oboe": 68,  # Oboe
        "clarinet": 71,  # Clarinet
        "counter": 73,  # Flute (countermelody)
        "piano": 0,  # Acoustic Grand Piano
        "violin": 40,  # Violin
        "cello": 42,  # Cello
        "harpsichord": 6,  # Harpsichord
        "viola": 41,  # Viola
        "timpani": 47,  # Timpani
    }

    print("=" * 80)
    print("   БОРИС РЫЖИЙ — ОТ САМОГО СЕРДЦА (1995)")
    print("=" * 80)

    print("\n-> SceneGraph: zaozersky → north → fountain → one_purr → garden1 → garden2")
    print("   Transitions: FADE → CUT → CUT → FADE → CROSSFADE")

    print("\n-> Rendering scene graph (in-memory, no individual MIDI files)...")
    stitch: StitchResult = render_scene_graph(
        graph,
        instruments=instrument_map,
        output_path="/dev/null",  # not used; scene data is in StitchResult
        psycho_verify_enabled=True,
    )

    print(f"   Total duration: {stitch.duration:.1f} beats")
    print(f"   Tracks: {len(stitch.tracks)}")
    if stitch.cc_events:
        print(f"   CC events: {sum(len(v) for v in stitch.cc_events.values())} total")

    combined_mid = OUT / "Ryzhy_1995_Album.mid"
    print(f"\n-> Exporting unified album MIDI → {combined_mid}")
    export_multitrack_midi(
        stitch.tracks,
        combined_mid,
        bpm=120,  # initial BPM (tempo events override per-scene BPMs)
        instruments=stitch.instruments,
        cc_events=stitch.cc_events,
        tempo_events=stitch.tempo_events,
    )

    print("\n" + "=" * 80)
    print("   АЛЬБОМ «ОТ САМОГО СЕРДЦА» СГЕНЕРИРОВАН!")
    print(f"   MIDI: {OUT.resolve()}")
    print("=" * 80)
    print("   БОРИС РЫЖИЙ — ОТ САМОГО СЕРДЦА (1995)")
    print("=" * 80)

    print("\n-> SceneGraph: zaozersky → north → fountain → one_purr → garden1 → garden2")
    print("   Transitions: FADE → CUT → CUT → FADE → CROSSFADE")

    print("\n-> Rendering scene graph (in-memory, no individual MIDI files)...")
    stitch: StitchResult = render_scene_graph(
        graph,
        instruments=instrument_map,
        output_path="/dev/null",  # not used; scene data is in StitchResult
        psycho_verify_enabled=True,
    )

    print(f"   Total duration: {stitch.duration:.1f} beats")
    print(f"   Tracks: {len(stitch.tracks)}")
    if stitch.cc_events:
        print(f"   CC events: {sum(len(v) for v in stitch.cc_events.values())} total")

    combined_mid = OUT / "Ryzhy_1995_Album.mid"
    print(f"\n-> Exporting unified album MIDI → {combined_mid}")
    export_multitrack_midi(
        stitch.tracks,
        combined_mid,
        bpm=120,  # initial BPM (tempo events override per-scene BPMs)
        instruments=stitch.instruments,
        cc_events=stitch.cc_events,
        tempo_events=stitch.tempo_events,
    )

    print("\n" + "=" * 80)
    print("   АЛЬБОМ «ОТ САМОГО СЕРДЦА» СГЕНЕРИРОВАН!")
    print(f"   MIDI: {OUT.resolve()}")
    print("=" * 80)
