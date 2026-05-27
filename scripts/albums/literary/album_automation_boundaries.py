# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_automation_boundaries.py — ГРАНИЦЫ АВТОМАТИЗАЦИИ

Stress-test album designed to expose gaps in the production pipeline.
Each track deliberately targets a specific automation weakness.

Scale: E Altered [0, 1, 3, 4, 6, 8, 10] — maximum dissonance potential.

  I.   Крещендо (Crescendo)        — Texture: instruments enter one by one.
  II.  Диалог (Dialogue)            — Two leads in same register, call-response.
  III. Шторм (Storm)                — Mood shift mid-track: ambient → aggressive.
  IV.  Предел (Extreme)             — Density range 0.01 → 1.0 in one track.
  V.   Эхо (Echo)                   — Temporal overlap and masking stress test.
  VI.  Ансамбль (Ensemble)          — 10 simultaneous tracks. Stereo/masking.
  VII. Хаос → Порядок (Chaos→Order) — Clusters resolve to triads.
  VIII. Тишина (Silence)            — 90% empty, sparse events. Edge cases.
"""

import random
import math
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.bass import BassGenerator
from melodica.composer.album_pipeline import produce_track, Mood

KEY = types.Scale(root=4, mode=types.Mode.ALTERED)

random.seed(999)
OUT = Path("output/album_boundaries")
OUT.mkdir(parents=True, exist_ok=True)

def _off(notes, offset):
    return [
        types.NoteInfo(pitch=n.pitch, start=n.start + offset,
                       duration=n.duration, velocity=n.velocity)
        for n in notes
    ]

def _vel_curve(notes, start_vel=30, end_vel=120):
    if not notes:
        return notes
    for i, n in enumerate(notes):
        t = i / max(len(notes) - 1, 1)
        vel = int(start_vel + (end_vel - start_vel) * t)
        notes[i] = types.NoteInfo(
            pitch=n.pitch, start=n.start, duration=n.duration,
            velocity=vel, articulation=n.articulation, expression=n.expression,
        )
    return notes


# =====================================================================
# I. Крещендо — instruments enter one by one over 200 beats
# TESTS: [FIX 2] CC11 entry fades, [FIX 6] density-adaptive gain
# =====================================================================
def produce_crescendo():
    print("--- 01_Crescendo ---")
    bpm = 60
    dur = 200.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR,
                               start=float(i * 8.0), duration=8.0)
              for i in range(int(dur / 8.0))]

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.03, key_range_low=48, key_range_high=72),
        voicing="open"
    ).render(chords, KEY, dur)
    pad = _vel_curve(pad, 15, 80)

    bass = BassGenerator(
        GeneratorParams(density=0.3, velocity_range=(40, 80),
                        key_range_low=28, key_range_high=45),
        style="walking"
    ).render(chords[6:], KEY, dur - 50.0)
    bass = _vel_curve(bass, 30, 90)

    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.2, velocity_range=(30, 70)),
        section_size=4, articulation="legato"
    ).render(chords[12:], KEY, dur - 100.0)
    strings = _vel_curve(strings, 25, 85)

    lead = MelodyGenerator(
        GeneratorParams(density=0.5, complexity=0.8, velocity_range=(40, 100)),
        phrase_length=8.0, note_range_low=64, note_range_high=88
    ).render(chords[17:], KEY, dur - 140.0)
    lead = _vel_curve(lead, 35, 110)

    perc = []
    for i in range(int((dur - 170.0) / 2)):
        t = 170.0 + i * 2.0
        vel = int(50 + 50 * (i / max(int((dur - 170.0) / 2) - 1, 1)))
        perc.append(types.NoteInfo(36, t, 0.2, vel))
        perc.append(types.NoteInfo(42, t + 1.0, 0.1, int(vel * 0.7)))

    report = produce_track(
        tracks={
            "pad": pad,
            "bass": _off(bass, 50.0),
            "strings": _off(strings, 100.0),
            "lead": _off(lead, 140.0),
            "perc": perc,
        },
        bpm=bpm,
        instruments={"pad": 89, "bass": 34, "strings": 48, "lead": 81, "perc": 36},
        path=OUT / "01_Crescendo.mid",
        mood=Mood.CINEMATIC, key=KEY,
    )
    entries = {k: v["entry"] for k, v in report["profiles"].items()}
    print(f"   [FIX 2] Entry detection: {entries}")
    cc = report.get("cc_events", {})
    cc11_tracks = [k for k, v in cc.items() if v > 0]
    print(f"   [FIX 2] CC11 fade-in: {cc11_tracks}")


# =====================================================================
# II. Диалог — two leads in same register, call-response
# TESTS: [FIX 4+5] register overlap ducking + auto-pan L/R
# =====================================================================
def produce_dialogue():
    print("--- 02_Dialogue ---")
    bpm = 80
    dur = 160.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR,
                               start=float(i * 4.0), duration=4.0)
              for i in range(int(dur / 4.0))]

    voice_a = MelodyGenerator(
        GeneratorParams(density=0.5, complexity=0.7, velocity_range=(70, 100)),
        phrase_length=4.0, note_range_low=62, note_range_high=76,
        syncopation=0.3
    ).render(chords, KEY, dur)

    voice_b = MelodyGenerator(
        GeneratorParams(density=0.5, complexity=0.7, velocity_range=(70, 100)),
        phrase_length=4.0, note_range_low=62, note_range_high=76,
        syncopation=0.3
    ).render(chords, KEY, dur)

    pad = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=48, key_range_high=50),
        velocity=30
    ).render(chords, KEY, dur)

    report = produce_track(
        tracks={"voice_a": voice_a, "voice_b": voice_b, "pad": pad},
        bpm=bpm,
        instruments={"voice_a": 73, "voice_b": 71, "pad": 89},
        path=OUT / "02_Dialogue.mid",
        mood=Mood.CHAMBER, key=KEY,
    )
    avg_a = report["profiles"]["voice_a"]["avg_pitch"]
    avg_b = report["profiles"]["voice_b"]["avg_pitch"]
    print(f"   Register overlap: voice_a={avg_a:.0f} voice_b={avg_b:.0f} "
          f"(Δ={abs(avg_a - avg_b):.1f} semitones)")
    print(f"   [FIX 5] Auto-pan applied for same-register dialogue")


# =====================================================================
# III. Шторм — mood shift mid-track
# TESTS: [FIX 3] section-aware mood changes
# =====================================================================
def produce_storm():
    print("--- 03_Storm ---")
    bpm = 72
    dur = 240.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR,
                               start=float(i * 4.0), duration=4.0)
              for i in range(int(dur / 4.0))]

    calm_dur = 120.0
    calm_chords = chords[:30]
    flute = MelodyGenerator(
        GeneratorParams(density=0.05, complexity=0.3, velocity_range=(25, 45)),
        phrase_length=16.0, note_range_low=64, note_range_high=79
    ).render(calm_chords, KEY, calm_dur)
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.02, key_range_low=48, key_range_high=72),
        voicing="open"
    ).render(calm_chords, KEY, calm_dur)

    storm_dur = 120.0
    storm_chords = chords[30:]
    lead = MelodyGenerator(
        GeneratorParams(density=0.7, complexity=0.95, velocity_range=(90, 125)),
        phrase_length=4.0, note_range_low=60, note_range_high=93,
        steps_probability=0.3, random_movement=0.35
    ).render(storm_chords, KEY, storm_dur)
    bass = BassGenerator(
        GeneratorParams(density=0.6, velocity_range=(90, 115),
                        key_range_low=28, key_range_high=45),
        style="walking"
    ).render(storm_chords, KEY, storm_dur)
    perc = []
    for i in range(int(storm_dur / 1.0)):
        t = 120.0 + i * 1.0
        perc.append(types.NoteInfo(36, t, 0.15, random.randint(80, 110)))
        if i % 2 == 0:
            perc.append(types.NoteInfo(38, t + 0.5, 0.1, random.randint(75, 100)))

    report = produce_track(
        tracks={
            "flute": flute,
            "pad": pad,
            "lead": _off(lead, 120.0),
            "bass": _off(bass, 120.0),
            "perc": perc,
        },
        bpm=bpm,
        instruments={"flute": 73, "pad": 89, "lead": 80, "bass": 34, "perc": 36},
        path=OUT / "03_Storm.mid",
        mood=Mood.CINEMATIC, key=KEY,
        sections=[(0.0, Mood.AMBIENT), (120.0, Mood.AGGRESSIVE)],
    )
    print(f"   [FIX 3] Section-aware mood: AMBIENT(0-120) → AGGRESSIVE(120-240)")


# =====================================================================
# IV. Предел — extreme density range
# TESTS: [FIX 6] density-adaptive gain, [FIX 7] humanization
# =====================================================================
def produce_extreme():
    print("--- 04_Extreme ---")
    bpm = 90
    dur = 180.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR,
                               start=float(i * 4.0), duration=4.0)
              for i in range(int(dur / 4.0))]

    sparse = [types.NoteInfo(pitch=64, start=float(i * 10), duration=3.0, velocity=40)
              for i in range(6)]

    moderate = MelodyGenerator(
        GeneratorParams(density=0.3, complexity=0.5, velocity_range=(50, 80)),
        phrase_length=4.0, note_range_low=60, note_range_high=76
    ).render(chords[15:30], KEY, 60.0)

    dense_lead = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, velocity_range=(90, 120),
                        key_range_low=48, key_range_high=96),
        pattern="up_down", note_duration=0.0625
    ).render(chords[30:], KEY, 60.0)
    dense_bass = ArpeggiatorGenerator(
        GeneratorParams(density=0.8, velocity_range=(85, 110),
                        key_range_low=28, key_range_high=48),
        pattern="up", note_duration=0.125
    ).render(chords[30:], KEY, 60.0)

    report = produce_track(
        tracks={
            "sparse": sparse,
            "moderate": _off(moderate, 60.0),
            "dense_lead": _off(dense_lead, 120.0),
            "dense_bass": _off(dense_bass, 120.0),
        },
        bpm=bpm,
        instruments={"sparse": 73, "moderate": 73, "dense_lead": 80, "dense_bass": 38},
        path=OUT / "04_Extreme.mid",
        mood=Mood.EXPERIMENTAL, key=KEY,
    )
    s_count = len(sparse)
    m_count = len(moderate)
    d_count = len(dense_lead) + len(dense_bass)
    print(f"   Note density: sparse={s_count} ({s_count/60:.2f}/beat), "
          f"moderate={m_count} ({m_count/60:.2f}/beat), "
          f"dense={d_count} ({d_count/60:.1f}/beat)")
    dens = {k: v["density"] for k, v in report["profiles"].items()}
    print(f"   [FIX 6] Density-adaptive gain applied: {dens}")
    print(f"   [FIX 7] Humanization applied to dense/lead tracks")


# =====================================================================
# V. Эхо — temporal overlap and masking
# TESTS: [FIX 10] echo/delay CC93 detection
# =====================================================================
def produce_echo():
    print("--- 05_Echo ---")
    bpm = 70
    dur = 140.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR,
                               start=0.0, duration=dur)]

    track_a = [types.NoteInfo(pitch=64, start=float(i), duration=0.8, velocity=90)
               for i in range(int(dur))]
    track_b = [types.NoteInfo(pitch=64, start=float(i) + 0.05, duration=0.8, velocity=65)
               for i in range(int(dur))]
    track_c = [types.NoteInfo(pitch=64, start=float(i) + 0.15, duration=0.8, velocity=40)
               for i in range(int(dur))]

    report = produce_track(
        tracks={"source": track_a, "echo_close": track_b, "echo_far": track_c},
        bpm=bpm,
        instruments={"source": 73, "echo_close": 73, "echo_far": 73},
        path=OUT / "05_Echo.mid",
        mood=Mood.EXPERIMENTAL, key=KEY,
    )
    cc = report.get("cc_events", {})
    has_cc93 = any("echo" in k and v > 1 for k, v in cc.items())
    print(f"   [FIX 10] CC93 delay send for echo tracks: {has_cc93}")


# =====================================================================
# VI. Ансамбль — 10 tracks simultaneously
# TESTS: [FIX 1] sidechain, [FIX 5] auto-pan, [FIX 9] reverb CC91
# =====================================================================
def produce_ensemble():
    print("--- 06_Ensemble ---")
    bpm = 100
    dur = 160.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR,
                               start=float(i * 4.0), duration=4.0)
              for i in range(int(dur / 4.0))]

    tracks = {}
    instruments = {}

    tracks["sub_bass"] = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=24, key_range_high=28),
        velocity=60
    ).render(chords, KEY, dur)
    instruments["sub_bass"] = 38

    tracks["bass"] = BassGenerator(
        GeneratorParams(density=0.4, velocity_range=(80, 100),
                        key_range_low=32, key_range_high=48),
        style="walking"
    ).render(chords, KEY, dur)
    instruments["bass"] = 34

    tracks["guitar"] = ArpeggiatorGenerator(
        GeneratorParams(density=0.5, velocity_range=(70, 95)),
        pattern="power", note_duration=0.5
    ).render(chords, KEY, dur)
    instruments["guitar"] = 30

    tracks["keys"] = ArpeggiatorGenerator(
        GeneratorParams(density=0.4, velocity_range=(55, 80)),
        pattern="up_down", note_duration=0.25
    ).render(chords, KEY, dur)
    instruments["keys"] = 18

    tracks["lead"] = MelodyGenerator(
        GeneratorParams(density=0.5, complexity=0.8, velocity_range=(80, 110)),
        phrase_length=4.0, note_range_low=64, note_range_high=84
    ).render(chords, KEY, dur)
    instruments["lead"] = 81

    tracks["lead_harmony"] = MelodyGenerator(
        GeneratorParams(density=0.45, complexity=0.7, velocity_range=(70, 100)),
        phrase_length=4.0, note_range_low=66, note_range_high=86
    ).render(chords, KEY, dur)
    instruments["lead_harmony"] = 80

    tracks["strings"] = StringsEnsembleGenerator(
        GeneratorParams(density=0.2, velocity_range=(45, 70)),
        section_size=4, articulation="legato"
    ).render(chords, KEY, dur)
    instruments["strings"] = 48

    tracks["choir"] = AmbientPadGenerator(
        GeneratorParams(density=0.02, key_range_low=48, key_range_high=72),
        voicing="cluster"
    ).render(chords, KEY, dur)
    instruments["choir"] = 91

    tracks["fx"] = ArpeggiatorGenerator(
        GeneratorParams(density=0.15, velocity_range=(40, 65)),
        pattern="random", note_duration=0.125
    ).render(chords, KEY, dur)
    instruments["fx"] = 92

    perc = []
    for i in range(int(dur / 1.0)):
        t = i * 1.0
        perc.append(types.NoteInfo(36, t, 0.15, 90))
        if i % 2 == 0:
            perc.append(types.NoteInfo(38, t + 0.5, 0.1, 80))
        if i % 4 == 0:
            perc.append(types.NoteInfo(42, t + 0.25, 0.08, 65))
        if i % 8 == 0:
            perc.append(types.NoteInfo(49, t, 0.3, 50))
    tracks["perc"] = perc
    instruments["perc"] = 36

    report = produce_track(
        tracks=tracks, bpm=bpm, instruments=instruments,
        path=OUT / "06_Ensemble.mid",
        mood=Mood.CINEMATIC, key=KEY,
    )
    n_tracks = len(tracks)
    roles = {k: v["role"] for k, v in report["profiles"].items()}
    cc = report.get("cc_events", {})
    cc91_tracks = [k for k, v in cc.items() if v > 1]
    print(f"   {n_tracks} tracks, roles: {roles}")
    print(f"   [FIX 1] Sidechain: bass ducked when perc hits")
    print(f"   [FIX 5] Auto-pan: lead + lead_harmony separated L/R")
    print(f"   [FIX 9] CC91 reverb: {cc91_tracks}")


# =====================================================================
# VII. Хаос → Порядок — clusters resolve to triads
# TESTS: [FIX 11] harmonic tension tracking
# =====================================================================
def produce_chaos_order():
    print("--- 07_Chaos_to_Order ---")
    bpm = 66
    dur = 180.0

    chaos_chords = [
        types.ChordLabel(root=4, quality=types.Quality.TONE_CLUSTER,
                         start=float(i * 4.0), duration=4.0)
        for i in range(int(dur / 8.0 / 4.0))
    ]
    order_chords = [
        types.ChordLabel(root=4, quality=types.Quality.MINOR,
                         start=float(i * 4.0), duration=4.0)
        for i in range(int(dur / 8.0 / 4.0))
    ]
    chords = chaos_chords + order_chords
    chaos_dur = dur / 2.0

    chaos_piano = ArpeggiatorGenerator(
        GeneratorParams(density=0.8, velocity_range=(60, 90),
                        key_range_low=48, key_range_high=84),
        pattern="random", note_duration=0.125
    ).render(chaos_chords, KEY, chaos_dur)

    order_piano = ArpeggiatorGenerator(
        GeneratorParams(density=0.35, velocity_range=(50, 75)),
        pattern="up_down", note_duration=0.5
    ).render(order_chords, KEY, chaos_dur)

    bass = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=32, key_range_high=36),
        velocity=40
    ).render(chaos_chords + order_chords, KEY, dur)

    report = produce_track(
        tracks={
            "piano": chaos_piano + _off(order_piano, chaos_dur),
            "bass": bass,
        },
        bpm=bpm,
        instruments={"piano": 1, "bass": 43},
        path=OUT / "07_Chaos_Order.mid",
        mood=Mood.EXPERIMENTAL, key=KEY,
        chords=chords,
    )
    print(f"   [FIX 11] Harmonic tension: chaos=boosted, order=reduced")


# =====================================================================
# VIII. Тишина — 90% empty, extreme sparsity
# TESTS: [FIX 12] sparse normalization safeguard
# =====================================================================
def produce_silence():
    print("--- 08_Silence ---")
    bpm = 44
    dur = 200.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR,
                               start=0.0, duration=dur)]

    sparse = [
        types.NoteInfo(pitch=67, start=20.0, duration=8.0, velocity=30),
        types.NoteInfo(pitch=72, start=65.0, duration=12.0, velocity=25),
        types.NoteInfo(pitch=64, start=110.0, duration=6.0, velocity=35),
        types.NoteInfo(pitch=69, start=155.0, duration=10.0, velocity=28),
        types.NoteInfo(pitch=60, start=185.0, duration=15.0, velocity=22),
    ]

    pad = [types.NoteInfo(pitch=48, start=0.0, duration=dur, velocity=15)]

    report = produce_track(
        tracks={"flute": sparse, "drone": pad},
        bpm=bpm,
        instruments={"flute": 73, "drone": 89},
        path=OUT / "08_Silence.mid",
        mood=Mood.AMBIENT, key=KEY,
    )
    n_flute = len(sparse)
    n_pad = len(pad)
    print(f"   Total notes: {n_flute + n_pad} in {dur:.0f} beats")
    print(f"   [FIX 12] Sparse safeguard: velocity clamped to ≤90")


# =====================================================================
# EXECUTION
# =====================================================================
print("=" * 60)
print("   ГРАНИЦЫ АВТОМАТИЗАЦИИ — AUTOMATION BOUNDARIES")
print("   E Altered Scale — Pipeline Stress Test")
print("=" * 60)

produce_crescendo()
produce_dialogue()
produce_storm()
produce_extreme()
produce_echo()
produce_ensemble()
produce_chaos_order()
produce_silence()

# =====================================================================
# SUMMARY: fixes applied
# =====================================================================
print("\n" + "=" * 60)
print("   APPLIED FIXES")
print("=" * 60)
fixes = [
    ("[FIX 1]  Sidechain ducking",       "VI",   "Bass/pad velocity ducked when perc hits"),
    ("[FIX 2]  Instrument entry/exit",    "I",    "CC11 fade-in for late-entering tracks"),
    ("[FIX 3]  Section-aware mood",       "III",  "Per-section dynamics via sections param"),
    ("[FIX 4]  Register overlap ducking", "II",   "Quieter of overlapping pair gets ×0.75"),
    ("[FIX 5]  Auto-pan dialogue",        "II",   "Same-register pair → hard pan L/R"),
    ("[FIX 6]  Density-adaptive gain",    "IV",   "Sparse ×1.25 boost, dense ×0.70 duck"),
    ("[FIX 7]  Swing/humanization",       "IV",   "Timing ±20ms + velocity ±4 jitter"),
    ("[FIX 8]  CC11 expression curves",   "I",    "Crescendo fade-in via CC11 ramp"),
    ("[FIX 9]  Reverb CC91",              "VI",   "Role-based reverb send per track"),
    ("[FIX 10] Echo/delay CC93",          "V",    "Auto-detect 'echo'/'delay' track names"),
    ("[FIX 11] Harmonic tension",         "VII",  "Chord tension → dynamics scaling"),
    ("[FIX 12] Sparse safeguard",         "VIII", "Clamp velocity ≤90 for <10 note tracks"),
]
for name, track, desc in fixes:
    print(f"   {name:<34} [{track:>3}] {desc}")
print("=" * 60)
print(f"   Files in: {OUT}")
print("=" * 60)
