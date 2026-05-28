# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_apocalyptus.py — АПОКАЛИПСИС (APOCALYPTUS)
Смешение: оркестр + хор + электроника + металл + эмбиент.
Каждый трек — сцена из фильма о конце света.

  1. Сигнал         — Эмбиент/оркестр. Первые знамения. 60 BPM.
  2. Пробуждение    — Оркестр + хор. Древнее зло просыпается. 72 BPM.
  3. Погоня         — Металл + электроника. Сквозь руины. 140 BPM.
  4. Осада          — Всё сразу. Максимальная война. 150 BPM.
  5. Потеря         — Голос + струнные + пианино. После битвы. 52 BPM.
  6. Вознесение     — Эмбиент → электроника → оркестр → хор. 80→120 BPM.

Масштаб проверяется не громкостью, а контрастом тишины и крика.
"""

from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.supersaw_pad import SupersawPadGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.power_chord import PowerChordGenerator
from melodica.generators.riff import RiffGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.vocal_oohs import VocalOohsGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# === SCALES ===
D_PHRYGIAN_DOM = types.Scale(root=2, mode=types.Mode.PHRYGIAN_DOMINANT)
D_LYDIAN_MINOR = types.Scale(root=2, mode=types.Mode.LYDIAN_MINOR)
D_HARM_MINOR   = types.Scale(root=2, mode=types.Mode.HARMONIC_MINOR)
D_DOUBLE_HARM  = types.Scale(root=2, mode=types.Mode.DOUBLE_HARM_MAJOR)


def _section(chords, start, end=None):
    """Return chords in [start, end) with start times shifted to be relative."""
    if end is None:
        end = max(c.start + c.duration for c in chords)
    out = []
    for c in chords:
        if c.start >= start and c.start < end:
            nc = type(c).__new__(type(c))
            nc.__dict__.update(c.__dict__)
            nc.start = c.start - start
            out.append(nc)
    return out


def _chords(key, progression: str, duration: float, beats_per_chord: float | None = None):
    parts = progression.split()
    bpc = beats_per_chord if beats_per_chord else duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        c = key.parse_roman(p)
        c.start = i * bpc
        c.duration = bpc
        chords.append(c)
    return chords


def _master(raw: dict, bpm: float, lufs: float = -12.0, gains: dict | None = None):
    desk = MixingDesk(niche_cfg={})
    default_gains = {
        "strings": 0.6, "strings_hi": 0.5, "tremolo": 0.55,
        "choir": 0.7, "choir_lo": 0.65,
        "brass": 0.65, "horns": 0.6,
        "drums": 0.8, "drums_metal": 0.85, "timpani": 0.7,
        "bass": 0.7, "dark_bass": 0.6,
        "guitar": 0.75, "riff": 0.8,
        "pad": 0.4, "supersaw": 0.5, "dark_pad": 0.35, "nebula": 0.3,
        "drone": 0.25, "ambient": 0.3,
        "piano": 0.6, "voice": 0.7, "harp": 0.5,
        "riser": 0.6, "impact": 0.8, "fx": 0.5,
    }
    if gains:
        default_gains.update(gains)
    desk.track_gains.update(default_gains)
    mixed = desk.apply_mixing(raw, [("Dynamics", 400, [])], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# =====================================================================
# Track 1 — СИГНАЛ (The Signal)
# 60 BPM, 4/4, D Phrygian Dominant
# Пустота. Далёкий гул. Небо темнеет. Первые знамения.
# =====================================================================
def produce_signal():
    """Ambient void → distant strings → single timpani → dread pad rises."""
    print("  I. СИГНАЛ [Phrygian Dominant — 60 BPM — D]")

    dur = 240.0  # 6:40 — patience is the weapon
    key = D_PHRYGIAN_DOM
    chords = _chords(key, "i bII bVII i " * 6, dur)

    s1, s2, s3, s4 = 60.0, 120.0, 180.0, 210.0

    # 1. Drone — the hum of something wrong
    drone = DroneGenerator(
        GeneratorParams(density=0.03), variant="tonic",
        fade_in=40.0, fade_out=0, velocity=50,
    ).render(chords, key, dur)

    # 2. Nebula — cosmic dust, barely there
    nebula = NebulaGenerator(
        GeneratorParams(density=0.06), variant="stasis",
        density_notes=2, pitch_spread=3, note_duration=8.0,
        overlap=0.7, use_scale_tones=True,
    ).render(chords, key, dur)

    # 3. Strings — distant, pp, entering at s1
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.08, key_range_low=42, key_range_high=60),
        articulation="sustained", divisi=1, dynamic_curve="crescendo",
    ).render(_section(chords, s1, s3), key, s3 - s1)
    for n in strings:
        n.start += s1

    # 4. Timpani — ONE roll at s2, the first warning
    timpani = [types.NoteInfo(pitch=38, start=s2, duration=8.0, velocity=90)]
    timpani_roll = TimpaniGenerator(
        GeneratorParams(density=0.15), stroke_pattern="roll",
        drum_count=2, roll_speed=0.0625,
    ).render(_section(chords, s2, s2 + 16), key, 16.0)
    for n in timpani_roll:
        n.start += s2

    # 5. Dark pad — rises from s3, dread
    dark_pad = DarkPadGenerator(
        GeneratorParams(density=0.12), mode="phrygian_pad",
        chord_dur=4.0, velocity_level=0.6, register="low", overlap=0.5,
    ).render(_section(chords, s3), key, dur - s3)
    for n in dark_pad:
        n.start += s3

    # 6. Riser — final 30 seconds, tension to nowhere (cliffhanger)
    riser = FXRiserGenerator(
        GeneratorParams(density=0.2), riser_type="noise",
        length_beats=16.0, pitch_curve="exponential", peak_velocity=100,
    ).render(_section(chords, dur - 30), key, 30.0)
    for n in riser:
        n.start += dur - 30

    raw = {"drone": drone, "nebula": nebula, "strings": strings,
           "timpani": timpani + timpani_roll, "dark_pad": dark_pad, "riser": riser}
    mastered, pan = _master(raw, 60.0, lufs=-24.0, gains={"timpani": 0.8})
    return mastered, pan, 60.0, key, {
        "drone": 91,       # New Age Pad
        "nebula": 95,      # Pad (halo)
        "strings": 49,     # String Ensemble 1
        "timpani": 47,     # Timpani
        "dark_pad": 92,    # Pad (bowed)
        "riser": 125,      # FX (rain) — placeholder for riser
    }


# =====================================================================
# Track 2 — ПРОБУЖДЕНИЕ (Awakening)
# 72 BPM, 4/4, D Double Harmonic → D Phrygian Dominant
# Древнее зло открывает глаза. Хор возвещает. Рога трубят.
# =====================================================================
def produce_awakening():
    """Choir + full orchestra + harp glissandi. The seal breaks."""
    print("  II. ПРОБУЖДЕНИЕ [Double Harmonic → Phrygian Dom — 72 BPM — D]")

    dur = 256.0  # ~7:00
    key = D_DOUBLE_HARM
    chords = _chords(key, "i bII bVII i bVI bVII i i " * 4, dur)

    s1, s2, s3 = 64.0, 128.0, 192.0

    # 1. Choir — enters immediately. Latin syllables, ominous.
    choir_a = ChoirAahsGenerator(
        GeneratorParams(density=0.15), voice_count=4,
        dynamics="pp", vibrato=0.2, syllable="aah",
    ).render(_section(chords, 0, s1), key, s1)

    choir_b = ChoirAahsGenerator(
        GeneratorParams(density=0.35), voice_count=4,
        dynamics="mf", vibrato=0.3, syllable="oh",
    ).render(_section(chords, s1, s2), key, s2 - s1)
    for n in choir_b:
        n.start += s1

    choir_d = ChoirAahsGenerator(
        GeneratorParams(density=0.5), voice_count=4,
        dynamics="ff", vibrato=0.4, syllable="aah",
    ).render(_section(chords, s3), key, dur - s3)
    for n in choir_d:
        n.start += s3
    choir = choir_a + choir_b + choir_d

    # 2. Strings — sustained, dark, building
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.2, key_range_low=36, key_range_high=72),
        articulation="sustained", divisi=2, dynamic_curve="crescendo",
    ).render(chords, key, dur)

    # 3. Brass — fanfare stabs at section boundaries
    brass = BrassSectionGenerator(
        GeneratorParams(density=0.18), articulation="hit",
        voicing="close", intensity=0.7, divisi_count=3,
        ensemble_mode="section", breath_gap=0.3,
    ).render(_section(chords, s1, s3), key, s3 - s1)
    for n in brass:
        n.start += s1

    # 4. Harp — glissandi, like cracking stone
    harp = HarpGenerator(
        GeneratorParams(density=0.1), pattern="glissando",
        direction="up", spread_speed=0.3, octave_span=2,
    ).render(_section(chords, 0, s2), key, s2)

    # 5. Timpani — heartbeat pulse
    timpani = TimpaniGenerator(
        GeneratorParams(density=0.2), stroke_pattern="accented",
        drum_count=4, roll_speed=0.125,
    ).render(_section(chords, s1), key, dur - s1)
    for n in timpani:
        n.start += s1

    # 6. Dark bass — sub-rumble
    dark_bass = DarkBassGenerator(
        GeneratorParams(density=0.08), mode="doom",
        octave=2, note_duration=4.0, velocity_level=0.7, movement="slow",
    ).render(_section(chords, s1), key, dur - s1)
    for n in dark_bass:
        n.start += s1

    # 7. Impact at climax (s3)
    impact = FXImpactGenerator(
        GeneratorParams(density=0.3), impact_type="boom",
        tail_length=8.0, pitch_drop=6,
    ).render(_section(chords, s3, s3 + 4), key, 4.0)
    for n in impact:
        n.start += s3

    raw = {"choir": choir, "strings": strings, "brass": brass,
           "harp": harp, "timpani": timpani, "dark_bass": dark_bass, "impact": impact}
    mastered, pan = _master(raw, 72.0, lufs=-14.0, gains={"impact": 0.9})
    return mastered, pan, 72.0, key, {
        "choir": 52,       # Choir Aahs
        "strings": 49,     # String Ensemble 1
        "brass": 61,       # Brass Section
        "harp": 46,        # Orchestral Harp
        "timpani": 47,     # Timpani
        "dark_bass": 48,   # Synth Strings 1 (dark sub)
        "impact": 127,     # FX (crash) — impact hit
    }


# =====================================================================
# Track 3 — ПОГОНЯ (The Chase)
# 140 BPM, 4/4, D Phrygian Dominant
# Сквозь горящий город. Металлические риффы + электронные удары.
# Оркестр не отстаёт.
# =====================================================================
def produce_chase():
    """Power chords + electronic drums + orchestral strings at full sprint."""
    print("  III. ПОГОНЯ [Phrygian Dominant — 140 BPM — D]")

    dur = 192.0  # ~3:30 at 140 — short, violent, relentless
    key = D_PHRYGIAN_DOM
    chords = _chords(key, "i bVII bVI V i bVII bVI V " * 3, dur)

    s1, s2, s3 = 48.0, 96.0, 144.0

    # 1. Power chords — palm-muted gallop, the engine
    guitar_a = PowerChordGenerator(
        GeneratorParams(density=0.4), pattern="gallop",
        include_octave=True, palm_mute_ratio=0.7, gallop_speed=0.1,
    ).render(_section(chords, 0, s1), key, s1)

    guitar_b = PowerChordGenerator(
        GeneratorParams(density=0.55), pattern="gallop",
        include_octave=True, palm_mute_ratio=0.5, gallop_speed=0.1,
        dead_notes=True,
    ).render(_section(chords, s1, s2), key, s2 - s1)
    for n in guitar_b:
        n.start += s1

    guitar_d = PowerChordGenerator(
        GeneratorParams(density=0.65), pattern="chug",
        include_octave=True, palm_mute_ratio=0.3, gallop_speed=0.1,
    ).render(_section(chords, s3), key, dur - s3)
    for n in guitar_d:
        n.start += s3
    guitar = guitar_a + guitar_b + guitar_d

    # 2. Riff — melodic metal lead on top
    riff = RiffGenerator(
        GeneratorParams(density=0.3), scale_type="minor_pent",
        riff_pattern="gallop", palm_mute_prob=0.2, power_chord=False,
    ).render(_section(chords, s1, s3), key, s3 - s1)
    for n in riff:
        n.start += s1

    # 3. Electronic drums — 808 with sidechain pump
    drums_a = ElectronicDrumsGenerator(
        GeneratorParams(density=0.5), kit="808", pattern="breakbeat",
        sidechain=True, sidechain_depth=0.6,
    ).render(_section(chords, 0, s1), key, s1)

    drums_b = ElectronicDrumsGenerator(
        GeneratorParams(density=0.65), kit="808", pattern="breakbeat",
        sidechain=True, sidechain_depth=0.8,
    ).render(_section(chords, s1, s3), key, s3 - s1)
    for n in drums_b:
        n.start += s1

    drums_d = ElectronicDrumsGenerator(
        GeneratorParams(density=0.75), kit="808", pattern="breakbeat",
        sidechain=True, sidechain_depth=1.0,
    ).render(_section(chords, s3), key, dur - s3)
    for n in drums_d:
        n.start += s3
    drums = drums_a + drums_b + drums_d

    # 4. Acoustic drums — double-kick underneath (rock kit)
    rock_drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.55), style="rock",
        hihat_pattern="sixteenth", fill_frequency=0.15,
        sidechain_depth=0.0, groove_swing=0.0,
    ).render(_section(chords, s1), key, dur - s1)
    for n in rock_drums:
        n.start += s1

    # 5. Strings — tremolo, frantic, high register
    strings = TremoloStringsGenerator(
        GeneratorParams(density=0.35, key_range_low=60, key_range_high=84),
        variant="measured", bow_speed=0.25, dynamic_swell=True,
    ).render(_section(chords, s1, s3), key, s3 - s1)
    for n in strings:
        n.start += s1

    # 6. Bass — dark, driving eighth notes
    bass = DarkBassGenerator(
        GeneratorParams(density=0.4), mode="doom",
        octave=2, note_duration=0.5, velocity_level=0.9, movement="driving",
    ).render(chords, key, dur)

    # 7. Supersaw — electronic wall of sound
    supersaw = SupersawPadGenerator(
        GeneratorParams(density=0.2), variant="trance",
        voice_count=7, detune_amount=0.6, release_time=2.0, sidechain_feel=True,
    ).render(_section(chords, s2), key, dur - s2)
    for n in supersaw:
        n.start += s2

    raw = {"guitar": guitar, "riff": riff, "drums": drums,
           "rock_drums": rock_drums, "strings": strings,
           "bass": bass, "supersaw": supersaw}
    mastered, pan = _master(raw, 140.0, lufs=-8.0)
    return mastered, pan, 140.0, key, {
        "guitar": 30,      # Overdriven Guitar
        "riff": 30,        # Overdriven Guitar
        "drums": 0,        # 808 kit (channel 10)
        "rock_drums": 0,   # Rock kit (channel 10)
        "strings": 44,     # Tremolo Strings
        "bass": 38,        # Synth Bass 1
        "supersaw": 81,    # Lead 2 (sawtooth)
    }


# =====================================================================
# Track 4 — ОСАДА (The Siege)
# 150 BPM, 4/4, D Double Harmonic Major
# Всё сразу. Хор кричит. Медные трубы. Метал-риффы. Басы.
# Максимальная плотность. Тест на удержание внимания.
# =====================================================================
def produce_siege():
    """Every layer at maximum. Choir + brass + metal + electronic + orchestra."""
    print("  IV. ОСАДА [Double Harmonic — 150 BPM — D]")

    dur = 224.0  # ~3:45
    key = D_DOUBLE_HARM
    chords = _chords(key, "i bII V i bVI bVII i V " * 4, dur)

    s1, s2, s3 = 56.0, 112.0, 168.0

    # 1. Choir — 12 voices, fortissimo, chanting
    choir = ChoirAahsGenerator(
        GeneratorParams(density=0.45), voice_count=12,
        dynamics="ff", vibrato=0.35, syllable="aah",
    ).render(chords, key, dur)

    # 2. Brass — fanfare, marcato, full section
    brass = BrassSectionGenerator(
        GeneratorParams(density=0.35), articulation="hit",
        voicing="open", intensity=0.9, divisi_count=4,
        ensemble_mode="section", breath_gap=0.2,
    ).render(_section(chords, s1, s3), key, s3 - s1)

    brass_d = BrassSectionGenerator(
        GeneratorParams(density=0.5), articulation="hit",
        voicing="close", intensity=1.0, divisi_count=4,
        ensemble_mode="section", breath_gap=0.1,
    ).render(_section(chords, s3), key, dur - s3)
    for n in brass_d:
        n.start += s3
    brass = brass + brass_d

    # 3. Strings — full section, tremolo + sustained layers
    strings_sus = StringsEnsembleGenerator(
        GeneratorParams(density=0.3, key_range_low=36, key_range_high=72),
        articulation="sustained", divisi=2, dynamic_curve="flat",
    ).render(chords, key, dur)

    strings_trem = TremoloStringsGenerator(
        GeneratorParams(density=0.4, key_range_low=55, key_range_high=79),
        variant="measured", bow_speed=0.25, dynamic_swell=True,
    ).render(_section(chords, s1), key, dur - s1)

    # 4. Metal guitar — chug pattern, aggressive
    guitar = PowerChordGenerator(
        GeneratorParams(density=0.5), pattern="chug",
        include_octave=True, palm_mute_ratio=0.4,
    ).render(_section(chords, s1), key, dur - s1)

    # 5. Riff — melodic lead over the chaos
    riff = RiffGenerator(
        GeneratorParams(density=0.35), scale_type="minor_pent",
        riff_pattern="syncopated", palm_mute_prob=0.1, power_chord=False,
    ).render(_section(chords, s2), key, dur - s2)

    # 6. Electronic drums + acoustic drums — both at once
    e_drums = ElectronicDrumsGenerator(
        GeneratorParams(density=0.6), kit="909", pattern="breakbeat",
        sidechain=True, sidechain_depth=0.5,
    ).render(chords, key, dur)

    rock_drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.65), style="rock",
        hihat_pattern="sixteenth", fill_frequency=0.2,
        sidechain_depth=0.0, groove_swing=0.0,
    ).render(chords, key, dur)

    # 7. Timpani — constant thunder
    timpani = TimpaniGenerator(
        GeneratorParams(density=0.3), stroke_pattern="accented",
        drum_count=4, roll_speed=0.25,
    ).render(chords, key, dur)

    # 8. Bass — aggressive, low
    bass = DarkBassGenerator(
        GeneratorParams(density=0.45), mode="doom",
        octave=1, note_duration=0.5, velocity_level=1.0, movement="driving",
    ).render(chords, key, dur)

    # 9. Supersaw — electronic wall
    supersaw = SupersawPadGenerator(
        GeneratorParams(density=0.25), variant="trance",
        voice_count=7, detune_amount=0.7, release_time=1.5, sidechain_feel=True,
    ).render(_section(chords, s2), key, dur - s2)

    # 10. Impact hits at section boundaries
    impact_hits = []
    for t in [0, s1, s2, s3]:
        impact_hits.extend([
            types.NoteInfo(pitch=36, start=t, duration=2.0, velocity=127),
            types.NoteInfo(pitch=38, start=t, duration=2.0, velocity=120),
        ])

    raw = {"choir": choir, "brass": brass, "strings": strings_sus,
           "tremolo": strings_trem, "guitar": guitar, "riff": riff,
           "drums": e_drums, "rock_drums": rock_drums,
           "timpani": timpani, "bass": bass, "supersaw": supersaw,
           "impact": impact_hits}
    mastered, pan = _master(raw, 150.0, lufs=-6.0)
    return mastered, pan, 150.0, key, {
        "choir": 52,       # Choir Aahs
        "brass": 61,       # Brass Section
        "strings": 49,     # String Ensemble 1
        "tremolo": 44,     # Tremolo Strings
        "guitar": 30,      # Overdriven Guitar
        "riff": 30,        # Overdriven Guitar
        "drums": 0,        # 909 kit (channel 10)
        "rock_drums": 0,   # Rock kit (channel 10)
        "timpani": 47,     # Timpani
        "bass": 38,        # Synth Bass 1
        "supersaw": 81,    # Lead 2 (sawtooth)
        "impact": 0,       # Impact (channel 10)
    }


# =====================================================================
# Track 5 — ПОТЕРЯ (Loss)
# 52 BPM, 3/4, D Harmonic Minor
# После битвы. Пепел. Одиночество. Красота в разрушении.
# =====================================================================
def produce_loss():
    """Solo voice → piano → strings join. Grief without words."""
    print("  V. ПОТЕРЯ [Harmonic Minor — 52 BPM — D]")

    dur = 240.0  # 7:30 — let it breathe
    key = D_HARM_MINOR
    bpc = 3.0  # 3/4 waltz of grief
    chords = _chords(key, "i V i iv V i iv V " * 8, dur, beats_per_chord=bpc)

    s1, s2, s3 = 60.0, 120.0, 192.0

    # 1. Voice — solo, wordless, enters alone
    voice_a = VocalOohsGenerator(
        GeneratorParams(density=0.12), syllable="ooh",
        harmony_count=2, vibrato=0.4, breath_phasing=True,
    ).render(_section(chords, 0, s1), key, s1)

    voice_b = VocalOohsGenerator(
        GeneratorParams(density=0.22), syllable="ooh",
        harmony_count=2, vibrato=0.5, breath_phasing=True,
    ).render(_section(chords, s1, s2), key, s2 - s1)
    for n in voice_b:
        n.start += s1

    voice_c = VocalOohsGenerator(
        GeneratorParams(density=0.18), syllable="ooh",
        harmony_count=2, vibrato=0.3, breath_phasing=True,
    ).render(_section(chords, s2, s3), key, s3 - s2)
    for n in voice_c:
        n.start += s2
    voice = voice_a + voice_b + voice_c

    # 2. Piano — sparse, intimate, enters at s1
    piano = PianoCompGenerator(
        GeneratorParams(density=0.15), comp_style="waltz",
        voicing_type="shell", chord_density=0.3,
    ).render(_section(chords, s1, s3), key, s3 - s1)

    # 3. Strings — enter at s2, pp, sustained, like cold wind
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.1, key_range_low=42, key_range_high=65),
        articulation="sustained", divisi=1, dynamic_curve="flat",
    ).render(_section(chords, s2), key, dur - s2)

    # 4. Harp — single notes, like tears falling
    harp = HarpGenerator(
        GeneratorParams(density=0.06), pattern="arpeggio",
        direction="up", spread_speed=0.5, octave_span=1,
    ).render(_section(chords, s1, s2), key, s2 - s1)

    # 5. Drone — barely audible sub-bass
    drone = DroneGenerator(
        GeneratorParams(density=0.02), variant="tonic",
        fade_in=20.0, fade_out=0, velocity=35,
    ).render(chords, key, dur)

    # 6. Single impact at s3 — the moment of acceptance
    final_hit = [types.NoteInfo(pitch=48, start=s3, duration=6.0, velocity=80)]

    raw = {"voice": voice, "piano": piano, "strings": strings,
           "harp": harp, "drone": drone, "impact": final_hit}
    mastered, pan = _master(raw, 52.0, lufs=-20.0, gains={"impact": 0.7})
    return mastered, pan, 52.0, key, {
        "voice": 53,       # Voice Oohs
        "piano": 0,        # Acoustic Grand Piano
        "strings": 49,     # String Ensemble 1
        "harp": 46,        # Orchestral Harp
        "drone": 91,       # New Age Pad
        "impact": 47,      # Timpani (soft hit)
    }


# =====================================================================
# Track 6 — ВОЗНЕСЕНИЕ (Ascension)
# 80→120 BPM, 4/4, D Lydian Minor → D Double Harmonic
# Эмбиент → электроника → оркестр → хор. Трансцендентность.
# =====================================================================
def produce_ascension():
    """From silence to everything. The final scene. Light through cracks."""
    print("  VI. ВОЗНЕСЕНИЕ [Lydian Minor → Double Harmonic — 80→120 BPM — D]")

    dur = 320.0  # 8:00 — the longest, the most patient
    key_slow = D_LYDIAN_MINOR
    key_fast = D_DOUBLE_HARM

    # Phase 1: ambient (80 BPM, Lydian Minor) — 0-120s
    # Phase 2: electronic (100 BPM feel) — 120-200s
    # Phase 3: orchestral (120 BPM) — 200-280s
    # Phase 4: choir climax (120 BPM, Double Harmonic) — 280-320s
    s1, s2, s3 = 120.0, 200.0, 280.0

    chords_slow = _chords(key_slow, "i IV vi bVII " * 8, s2)
    chords_fast = _chords(key_fast, "i bII V i bVI bVII i V " * 4, dur - s2)
    for c in chords_fast:
        c.start += s2

    # Phase 1: AMBIENT — nebula + drone + harp
    nebula = NebulaGenerator(
        GeneratorParams(density=0.08), variant="cascade",
        density_notes=3, pitch_spread=4, note_duration=6.0,
        overlap=0.8, use_scale_tones=True,
    ).render(_section(chords_slow, 0, s1), key_slow, s1)

    drone = DroneGenerator(
        GeneratorParams(density=0.03), variant="tonic",
        fade_in=10.0, fade_out=0, velocity=45,
    ).render(_section(chords_slow, 0, s1), key_slow, s1)

    harp_amb = HarpGenerator(
        GeneratorParams(density=0.06), pattern="arpeggio",
        direction="up", spread_speed=0.8, octave_span=2,
    ).render(_section(chords_slow, 0, s1), key_slow, s1)

    # Phase 2: ELECTRONIC — supersaw + electronic drums + synth bass
    supersaw = SupersawPadGenerator(
        GeneratorParams(density=0.2), variant="trance",
        voice_count=7, detune_amount=0.5, release_time=3.0, sidechain_feel=True,
    ).render(_section(chords_slow, s1, s2), key_slow, s2 - s1)
    for n in supersaw:
        n.start += s1

    e_drums = ElectronicDrumsGenerator(
        GeneratorParams(density=0.35), kit="909", pattern="four_on_floor",
        sidechain=True, sidechain_depth=0.4,
    ).render(_section(chords_slow, s1, s2), key_slow, s2 - s1)
    for n in e_drums:
        n.start += s1

    synth_bass_mel = MelodyGenerator(
        GeneratorParams(density=0.2, key_range_low=36, key_range_high=48),
        drama_shape="crescendo", drama_peak=0.5,
        harmony_note_probability=0.9, note_range_low=36, note_range_high=48,
        phrase_length=8.0, register_smoothness=0.95,
        steps_probability=0.9, first_note="tonic",
    ).render(_section(chords_slow, s1, s2), key_slow, s2 - s1)
    for n in synth_bass_mel:
        n.start += s1

    # Riser at transition s1→s2
    riser = FXRiserGenerator(
        GeneratorParams(density=0.15), riser_type="noise",
        length_beats=16.0, pitch_curve="linear", peak_velocity=90,
    ).render(_section(chords_slow, s2 - 16, s2), key_slow, 16.0)
    for n in riser:
        n.start += s2 - 16

    # Phase 3: ORCHESTRAL — full strings + brass + timpani
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.3, key_range_low=36, key_range_high=76),
        articulation="sustained", divisi=2, dynamic_curve="crescendo",
    ).render(_section(chords_fast, s2), key_fast, dur - s2)

    brass = BrassSectionGenerator(
        GeneratorParams(density=0.3), articulation="sustained",
        voicing="open", intensity=0.7, divisi_count=3,
        ensemble_mode="section", breath_gap=0.3,
    ).render(_section(chords_fast, s2, s3), key_fast, s3 - s2)

    timpani = TimpaniGenerator(
        GeneratorParams(density=0.25), stroke_pattern="accented",
        drum_count=4, roll_speed=0.125,
    ).render(_section(chords_fast, s2), key_fast, dur - s2)

    # Phase 4: CHOIR CLIMAX
    choir = ChoirAahsGenerator(
        GeneratorParams(density=0.5), voice_count=4,
        dynamics="ff", vibrato=0.4, syllable="aah",
    ).render(_section(chords_fast, s3), key_fast, dur - s3)
    for n in choir:
        n.start += s3

    # Sustained through phase 3-4
    rock_drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.4), style="rock",
        hihat_pattern="eighth", fill_frequency=0.1,
        sidechain_depth=0.0, groove_swing=0.05,
    ).render(_section(chords_fast, s2), key_fast, dur - s2)

    # Final impact
    final_impact = []
    for t in [s3, s3 + 16, s3 + 32]:
        final_impact.extend([
            types.NoteInfo(pitch=36, start=t, duration=4.0, velocity=127),
            types.NoteInfo(pitch=38, start=t + 0.1, duration=4.0, velocity=120),
            types.NoteInfo(pitch=43, start=t + 0.2, duration=4.0, velocity=110),
        ])

    raw = {"nebula": nebula, "drone": drone, "harp": harp_amb,
           "supersaw": supersaw, "drums": e_drums, "bass": synth_bass_mel,
           "riser": riser, "strings": strings, "brass": brass,
           "timpani": timpani, "choir": choir, "rock_drums": rock_drums,
           "impact": final_impact}
    mastered, pan = _master(raw, 120.0, lufs=-10.0, gains={"impact": 0.9})
    return mastered, pan, 120.0, key_fast, {
        "nebula": 95,      # Pad (halo)
        "drone": 91,       # New Age Pad
        "harp": 46,        # Orchestral Harp
        "supersaw": 81,    # Lead 2 (sawtooth)
        "drums": 0,        # 909 kit (channel 10)
        "bass": 38,        # Synth Bass 1
        "riser": 125,      # FX (rain) — placeholder
        "strings": 49,     # String Ensemble 1
        "brass": 61,       # Brass Section
        "timpani": 47,     # Timpani
        "choir": 52,       # Choir Aahs
        "rock_drums": 0,   # Rock kit (channel 10)
        "impact": 0,       # Impact (channel 10)
    }


# =====================================================================
# Main
# =====================================================================
def main():
    album_dir = Path("output/album_apocalyptus")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 70)
    print("   А П О К А Л И П С И С")
    print("   APOCALYPTUS — 6 Scenes from the End of the World")
    print("   Orchestra + Choir + Electronics + Metal + Ambient")
    print("=" * 70 + "\n")

    tracks = [
        ("01_Signal_Сигнал",             produce_signal),
        ("02_Awakening_Пробуждение",     produce_awakening),
        ("03_Chase_Погоня",              produce_chase),
        ("04_Siege_Осада",               produce_siege),
        ("05_Loss_Потеря",               produce_loss),
        ("06_Ascension_Вознесение",      produce_ascension),
    ]

    for name, producer in tracks:
        print(f"\n--- {name} ---")
        mastered, pan, bpm, key, instr = producer()
        export_multitrack_midi(
            mastered,
            str(album_dir / f"{name}.mid"),
            bpm=bpm, key=key, cc_events=pan, instruments=instr,
        )
        inst_names = {
            0: "Drums", 30: "Overdriven Guitar", 38: "Synth Bass 1",
            44: "Tremolo Strings", 46: "Orchestral Harp", 47: "Timpani",
            48: "Synth Strings 1", 49: "String Ensemble 1",
            52: "Choir Aahs", 53: "Voice Oohs", 61: "Brass Section",
            81: "Lead 2 (saw)", 89: "New Age Pad", 91: "New Age Pad",
            92: "Pad (bowed)", 95: "Pad (halo)", 125: "FX (rain)",
            127: "FX (crash)",
        }
        print(f"    -> {name}.mid  ({bpm} BPM, {len(mastered)} tracks)")
        for track_name, program in instr.items():
            gm_name = inst_names.get(program, f"GM#{program}")
            note_count = sum(len(v) for k, v in mastered.items() if k == track_name)
            print(f"       {track_name:16s}  {gm_name:20s}  {note_count:>4d} notes")

    print("\n" + "=" * 70)
    print(f"   АПОКАЛИПСИС — COMPLETE.")
    print(f"   Files in: {album_dir}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
