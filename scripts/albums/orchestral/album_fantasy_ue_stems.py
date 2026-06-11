# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_fantasy_ue_stems.py — ECHOES OF THE FORGOTTEN REALM
A fantasy RPG orchestral album designed for Unreal Engine stem-based
adaptive audio.

Structure:
    Act I   – The Village at Peace    (exploration, serene, hopeful)
    Act II  – Into the Wild           (adventure, forward momentum)
    Act III – The Ancient Dungeon     (tension, dread, mystery)
    Act IV  – The Boss Confrontation  (epic battle, fury)
    Act V   – The Hero's Return       (triumph, bittersweet, epilogue)

Stem export layout (per cue):
    <cue>/
        <cue>_stems/
            stem_<layer>.mid   ← one file per instrument stem
        <cue>_mix.mid          ← optional full-mix reference

Each stem file contains exactly one MIDI track.
This layout maps directly to Unreal Engine's MetaSound / WWise
multi-layer audio system, where each stem can be loaded independently
and blended at runtime.
"""

from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams

# Orchestral solo instruments
from melodica.generators.orchestral_strings import (
    ViolinGenerator,
    ViolaGenerator,
    CelloGenerator,
    ContrabassGenerator,
)
from melodica.generators.orchestral_brass import (
    TrumpetGenerator,
    TromboneGenerator,
    FrenchHornGenerator,
)
from melodica.generators.orchestral_woodwinds import (
    FluteGenerator,
    OboeGenerator,
    ClarinetGenerator,
    BassoonGenerator,
)
from melodica.generators.orchestral_percussion import (
    TimpaniGenerator,
    MalletPercussionGenerator,
)

# Section / ensemble generators
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.tuba import TubaGenerator
from melodica.generators.snare_drum import SnareDrumGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator

# Specialty generators
from melodica.generators.harp import HarpGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.tension import TensionGenerator
from melodica.generators.chorale import ChoraleGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.boss_battle import BossBattleGenerator

from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# ---------------------------------------------------------------------------
# Scales
# ---------------------------------------------------------------------------

C_IONIAN    = Scale(root=0,  mode=Mode.IONIAN)         # C major — village peace
G_MIXOLYD   = Scale(root=7,  mode=Mode.MIXOLYDIAN)     # G Mixolydian — adventure road
A_AEOLIAN   = Scale(root=9,  mode=Mode.AEOLIAN)        # A natural minor — dungeon
D_PHRYG     = Scale(root=2,  mode=Mode.PHRYGIAN)       # D Phrygian — boss / dread
E_HARM      = Scale(root=4,  mode=Mode.HARMONIC_MINOR) # E harmonic minor — final battle
A_DOR       = Scale(root=9,  mode=Mode.DORIAN)         # A Dorian — hero's return


# ---------------------------------------------------------------------------
# GM programs
# ---------------------------------------------------------------------------

GM_VIOLIN          = 40
GM_VIOLA           = 41
GM_CELLO           = 42
GM_CONTRABASS      = 43
GM_STRINGS_ENS     = 48
GM_PIZZICATO       = 45
GM_TREMOLO         = 44
GM_HARP            = 46
GM_FLUTE           = 73
GM_OBOE            = 68
GM_CLARINET        = 71
GM_BASSOON         = 70
GM_FRENCH_HORN     = 60
GM_TRUMPET         = 56
GM_TROMBONE        = 57
GM_TUBA            = 58
GM_BRASS_SECTION   = 61
GM_CHOIR           = 52
GM_CHOIR_OOH       = 53
GM_TUBULAR_BELLS   = 14
GM_TIMPANI         = 47
GM_MALLET          = 11
GM_SNARE           = 115
GM_ORCH_HIT        = 55
GM_DRONE_PAD       = 89
GM_TENSION         = 99


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chords(progression: str, duration: float, key: Scale) -> list[ChordLabel]:
    """Build a simple uniform chord progression."""
    parts = progression.split()
    beats = duration / len(parts)
    result = []
    for i, p in enumerate(parts):
        c = key.parse_roman(p)
        c.start = i * beats
        c.duration = beats
        result.append(c)
    return result


def _vel(notes: list[NoteInfo], lo: int = 1, hi: int = 127) -> list[NoteInfo]:
    for n in notes:
        n.velocity = max(lo, min(hi, n.velocity))
    return notes


def _off(notes: list[NoteInfo], offset: float) -> list[NoteInfo]:
    return [NoteInfo(pitch=n.pitch, start=n.start + offset,
                     duration=n.duration, velocity=n.velocity)
            for n in notes]


def _mix_and_master(raw: dict, bpm: float, lufs: float = -16.0):
    """Apply mixing gains then mastering."""
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        # Strings
        "Strings":     0.78, "Violins":  0.76, "Viola":    0.74,
        "Cello":       0.78, "Bass":     0.82, "Pizzicato": 0.70,
        "Tremolo":     0.72, "Melody":   0.80,
        # Brass
        "Brass":       0.74, "Horns":    0.76, "Trumpet":  0.70,
        "Trombone":    0.72, "Tuba":     0.80,
        # Woodwinds
        "Flute":       0.72, "Oboe":     0.74, "Clarinet": 0.72, "Bassoon": 0.76,
        # Choir / vocal
        "Choir":       0.80,
        # Harp / bells
        "Harp":        0.82, "Bells":    0.75,
        # Percussion
        "Timpani":     0.85, "Snare":    0.65, "Hit":      0.80,
        # Pads / FX
        "Drone":       0.70, "Tension":  0.68, "Pedal":    0.80,
        "Ostinato":    0.74, "Chorale":  0.76,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def _export_stems(
    raw_stems: dict[str, list[NoteInfo]],
    instruments: dict[str, int],
    cue_dir: Path,
    cue_name: str,
    bpm: float,
    key: Scale,
):
    """
    Export each stem as its own single-track MIDI file, then write a
    full-mix reference MIDI with all stems on separate tracks.

    Output layout:
        <cue_dir>/
            <cue_name>_stems/
                stem_<layer>.mid
            <cue_name>_mix.mid
    """
    stem_dir = cue_dir / f"{cue_name}_stems"
    stem_dir.mkdir(parents=True, exist_ok=True)

    mastered, cc_events = _mix_and_master(raw_stems, bpm)

    # 1. Individual stem files (one MIDI track per file)
    for stem_name, notes in mastered.items():
        stem_path = stem_dir / f"stem_{stem_name}.mid"
        instr = {stem_name: instruments.get(stem_name, 0)}
        stem_cc = {stem_name: cc_events.get(stem_name, [])} if cc_events else None
        export_multitrack_midi(
            {stem_name: notes},
            str(stem_path),
            bpm=bpm,
            key=key,
            instruments=instr,
            cc_events=stem_cc,
        )

    # 2. Full-mix reference (all stems in one Type-1 MIDI)
    mix_path = cue_dir / f"{cue_name}_mix.mid"
    export_multitrack_midi(
        mastered,
        str(mix_path),
        bpm=bpm,
        key=key,
        instruments=instruments,
        cc_events=cc_events,
    )

    total = sum(len(n) for n in raw_stems.values())
    stem_count = len(mastered)
    print(f"    -> {cue_name}: {stem_count} stems, {total} notes, {bpm} BPM")


# ===========================================================================
# ACT I — The Village at Peace  (C Ionian, 72 BPM)
# Warm, pastoral. Used in open-world exploration / safe zones.
# Stems: Melody, Flute, Harp, Strings, Choir, Pizzicato, Oboe
# ===========================================================================

def cue_01_village():
    print("  01 — The Village at Peace")
    bpm, dur = 72, 128.0
    key = C_IONIAN
    prog = _chords("Imaj7 IVmaj7 Imaj7 V7 Imaj9 vim7 IVmaj7 V7 Imaj7 IVadd9 vim7 V7 Imaj9", dur, key)

    melody = MelodyGenerator(
        GeneratorParams(density=0.30, key_range_low=60, key_range_high=84),
        phrase_length=8.0, phrase_rest_probability=0.20,
        phrase_contour="arch", syncopation=0.05
    ).render(prog, key, dur)

    flute = FluteGenerator(
        GeneratorParams(density=0.40, key_range_low=64, key_range_high=90),
        articulation="sustained", vibrato=True, dynamic_curve="arch", note_density=1.2
    ).render(prog, key, dur - 16.0)
    flute = _off(flute, 16.0)

    oboe = OboeGenerator(
        GeneratorParams(density=0.30, key_range_low=58, key_range_high=78),
        articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=1.0
    ).render(prog, key, dur - 32.0)
    oboe = _off(oboe, 32.0)

    harp = HarpGenerator(
        GeneratorParams(density=0.40, key_range_low=40, key_range_high=76),
        pattern="arpeggio", direction="up", spread_speed=0.15
    ).render(prog, key, dur)

    strings = StringsLegatoGenerator(
        GeneratorParams(density=0.35, key_range_low=44, key_range_high=72),
        ensemble_mode="section", dynamic_shape="crescendo"
    ).render(prog, key, dur)

    pizz = StringsPizzicatoGenerator(
        GeneratorParams(density=0.35, key_range_low=36, key_range_high=60),
        pattern="ostinato", staccato_length=0.08
    ).render(prog, key, dur)

    choir = ChoirAahsGenerator(
        GeneratorParams(density=0.25, key_range_low=44, key_range_high=68),
        voice_count=4, dynamics="pp", syllable="aah", vibrato=0.2
    ).render(prog, key, dur - 32.0)
    choir = _off(choir, 32.0)

    pedal = PedalBassGenerator(
        GeneratorParams(density=0.20, key_range_low=24, key_range_high=36),
        pedal_note="root", sustain=2.0, velocity_level=0.35
    ).render(prog, key, dur)

    raw = {
        "Melody":    _vel(melody,  35, 78),
        "Flute":     _vel(flute,   30, 72),
        "Oboe":      _vel(oboe,    30, 70),
        "Harp":      _vel(harp,    28, 62),
        "Strings":   _vel(strings, 25, 70),
        "Pizzicato": _vel(pizz,    28, 60),
        "Choir":     _vel(choir,   20, 55),
        "Pedal":     _vel(pedal,   25, 50),
    }
    instruments = {
        "Melody":    GM_VIOLIN, "Flute": GM_FLUTE, "Oboe": GM_OBOE,
        "Harp":      GM_HARP,   "Strings": GM_STRINGS_ENS,
        "Pizzicato": GM_PIZZICATO, "Choir": GM_CHOIR, "Pedal": GM_CONTRABASS,
    }
    return raw, instruments, bpm, key


# ===========================================================================
# ACT II — Into the Wild  (G Mixolydian, 96 BPM)
# Forward-moving adventure theme. Used during world travel / overworld map.
# Stems: Melody, Horns, Strings, Trumpet, Pizzicato, Harp, Timpani
# ===========================================================================

def cue_02_into_the_wild():
    print("  02 — Into the Wild")
    bpm, dur = 96, 128.0
    key = G_MIXOLYD
    prog = _chords("Imaj7 V7 IVmaj7 I7 bVII7 IVadd9 Vsus4 V7 IVmaj9 bVII7 Imaj7 V7 IVmaj7 Iadd9", dur, key)

    melody = MelodyGenerator(
        GeneratorParams(density=0.35, key_range_low=60, key_range_high=88),
        phrase_length=8.0, phrase_rest_probability=0.15,
        phrase_contour="rise_fall", syncopation=0.20
    ).render(prog, key, dur)

    horns = FrenchHornGenerator(
        GeneratorParams(density=0.40, key_range_low=40, key_range_high=65),
        articulation="sustained", dynamic_curve="crescendo", note_density=1.5
    ).render(prog, key, dur)

    trumpet = TrumpetGenerator(
        GeneratorParams(density=0.30, key_range_low=55, key_range_high=80),
        articulation="staccato", dynamic_curve="flat", note_density=1.2
    ).render(prog, key, dur - 16.0)
    trumpet = _off(trumpet, 16.0)

    strings = StringsLegatoGenerator(
        GeneratorParams(density=0.45, key_range_low=40, key_range_high=72),
        ensemble_mode="section", dynamic_shape="flat"
    ).render(prog, key, dur)

    pizz = StringsPizzicatoGenerator(
        GeneratorParams(density=0.45, key_range_low=36, key_range_high=60),
        pattern="ostinato", staccato_length=0.07
    ).render(prog, key, dur)

    harp = HarpGenerator(
        GeneratorParams(density=0.30, key_range_low=44, key_range_high=76),
        pattern="arpeggio", direction="up", spread_speed=0.12
    ).render(prog, key, dur)

    timp = TimpaniGenerator(
        GeneratorParams(density=0.30),
        stroke_pattern="single", drum_count=4
    ).render(prog, key, dur)

    ostinato = OstinatoGenerator(
        GeneratorParams(density=0.05, key_range_low=36, key_range_high=52),
        pattern="1-5-1-5", repeat_notes=2,
        phrase_length=8.0, phrase_ending="hold",
        seed=77
    ).render(prog, key, dur)

    raw = {
        "Melody":   _vel(melody,   40, 85),
        "Horns":    _vel(horns,    35, 80),
        "Trumpet":  _vel(trumpet,  35, 78),
        "Strings":  _vel(strings,  30, 80),
        "Pizzicato":_vel(pizz,     30, 65),
        "Harp":     _vel(harp,     28, 58),
        "Timpani":  _vel(timp,     40, 80),
        "Ostinato": _vel(ostinato, 30, 60),
    }
    instruments = {
        "Melody":   GM_VIOLIN, "Horns": GM_FRENCH_HORN, "Trumpet": GM_TRUMPET,
        "Strings":  GM_STRINGS_ENS, "Pizzicato": GM_PIZZICATO,
        "Harp":     GM_HARP, "Timpani": GM_TIMPANI, "Ostinato": GM_CELLO,
    }
    return raw, instruments, bpm, key


# ===========================================================================
# ACT III — The Ancient Dungeon  (A Aeolian, 54 BPM)
# Dark, suspenseful. Tension layer can be dynamically mixed in/out in UE.
# Stems: Tension, Drone, Tremolo, Ostinato, Bassoon, Choir, Pedal, Harp
# ===========================================================================

def cue_03_dungeon():
    print("  03 — The Ancient Dungeon")
    bpm, dur = 54, 160.0
    key = A_AEOLIAN
    prog = _chords("im7 ivm7 im7 bVImaj7 bVII7 im7 IIIdim7 ivm7 vm7b5 im7 bVImaj7 ivm7 bVII7 im9", dur, key)

    drone = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=20, key_range_high=33),
        velocity=42
    ).render(prog, key, dur)

    tremolo = TremoloStringsGenerator(
        GeneratorParams(density=0.45, key_range_low=36, key_range_high=60),
        bow_speed=0.05, dynamic_swell=True
    ).render(prog, key, dur)

    tension = TensionGenerator(
        GeneratorParams(density=0.38, key_range_low=28, key_range_high=68),
        mode="semitone_cluster", note_duration=3.0, velocity_level=0.32, register="low"
    ).render(prog, key, dur)

    ostinato = OstinatoGenerator(
        GeneratorParams(density=0.06, key_range_low=28, key_range_high=48),
        pattern="1-3-1-5", repeat_notes=2,
        phrase_length=12.0, phrase_ending="silence",
        variation_probability=0.12,
        timing_jitter=0.015, velocity_jitter=10,
        seed=404
    ).render(prog, key, dur - 24.0)
    ostinato = _off(ostinato, 24.0)

    bassoon = BassoonGenerator(
        GeneratorParams(density=0.30, key_range_low=34, key_range_high=52),
        articulation="sustained", vibrato=False, dynamic_curve="flat", note_density=1.1
    ).render(prog, key, dur)

    choir = ChoirAahsGenerator(
        GeneratorParams(density=0.30, key_range_low=40, key_range_high=66),
        voice_count=5, dynamics="pp", syllable="ooh", vibrato=0.25
    ).render(prog, key, dur - 32.0)
    choir = _off(choir, 32.0)

    harp = HarpGenerator(
        GeneratorParams(density=0.20, key_range_low=36, key_range_high=72),
        pattern="arpeggio", direction="down", spread_speed=0.20
    ).render(prog, key, dur)

    pedal = PedalBassGenerator(
        GeneratorParams(density=0.22, key_range_low=20, key_range_high=33),
        pedal_note="root", sustain=4.0, velocity_level=0.42
    ).render(prog, key, dur)

    raw = {
        "Drone":    _vel(drone,    20, 48),
        "Tremolo":  _vel(tremolo,  22, 58),
        "Tension":  _vel(tension,  22, 55),
        "Ostinato": _vel(ostinato, 28, 55),
        "Bassoon":  _vel(bassoon,  28, 58),
        "Choir":    _vel(choir,    18, 52),
        "Harp":     _vel(harp,     22, 52),
        "Pedal":    _vel(pedal,    25, 50),
    }
    instruments = {
        "Drone":    GM_DRONE_PAD, "Tremolo": GM_TREMOLO,
        "Tension":  GM_TENSION,   "Ostinato": GM_CELLO,
        "Bassoon":  GM_BASSOON,   "Choir": GM_CHOIR_OOH,
        "Harp":     GM_HARP,      "Pedal": GM_CONTRABASS,
    }
    return raw, instruments, bpm, key


# ===========================================================================
# ACT IV — The Boss Confrontation  (D Phrygian → E Harmonic Minor, 138 BPM)
# Epic battle. Each stem is a distinct intensity layer for UE combat states.
# Stems: Brass, Strings, Choir, Timpani, Snare, Hit, Horns, Tuba, Ostinato
# ===========================================================================

def cue_04_boss():
    print("  04 — The Boss Confrontation")
    bpm, dur = 138, 96.0
    key = D_PHRYG
    prog = _chords("im7 bIIdim7 V7 im7 bVImaj7 ivm7 bIIdim7 V7 im9 ivm7 bVImaj7 Vdim7 im7 bII7 im7", dur, key)

    brass = BrassSectionGenerator(
        GeneratorParams(density=0.60, key_range_low=36, key_range_high=76),
        articulation="sustained", voicing="open", divisi_count=5
    ).render(prog, key, dur)

    strings = StringsLegatoGenerator(
        GeneratorParams(density=0.60, key_range_low=36, key_range_high=80),
        ensemble_mode="section", dynamic_shape="flat"
    ).render(prog, key, dur)

    choir = ChoirAahsGenerator(
        GeneratorParams(density=0.50, key_range_low=40, key_range_high=72),
        voice_count=6, dynamics="ff", syllable="aah", vibrato=0.40
    ).render(prog, key, dur)

    timp = TimpaniGenerator(
        GeneratorParams(density=0.50),
        stroke_pattern="single", drum_count=5
    ).render(prog, key, dur)

    snare = SnareDrumGenerator(
        GeneratorParams(density=0.45),
        pattern_type="march"
    ).render(prog, key, dur)

    hit = OrchestralHitGenerator(
        GeneratorParams(density=0.30, key_range_low=36, key_range_high=76),
        hit_type="staccato", voicing="chord"
    ).render(prog, key, dur)

    horns = FrenchHornGenerator(
        GeneratorParams(density=0.45, key_range_low=36, key_range_high=65),
        articulation="sustained", dynamic_curve="flat", note_density=2.0
    ).render(prog, key, dur)

    tuba = TubaGenerator(
        GeneratorParams(density=0.35, key_range_low=24, key_range_high=40),
        articulation="sustained"
    ).render(prog, key, dur)

    ostinato = OstinatoGenerator(
        GeneratorParams(density=0.08, key_range_low=36, key_range_high=60),
        pattern="1-3-5-3", repeat_notes=1,
        patterns=["1-3-5-3", "1-3-4-5-4-3"], change_pattern_every=8.0,
        phrase_length=8.0, phrase_ending="root",
        variation_probability=0.10,
        seed=911
    ).render(prog, key, dur)

    tremolo = TremoloStringsGenerator(
        GeneratorParams(density=0.50, key_range_low=32, key_range_high=60),
        bow_speed=0.04, dynamic_swell=False
    ).render(prog, key, dur)

    raw = {
        "Brass":    _vel(brass,    50, 100),
        "Strings":  _vel(strings,  45, 95),
        "Choir":    _vel(choir,    45, 95),
        "Timpani":  _vel(timp,     55, 100),
        "Snare":    _vel(snare,    45, 85),
        "Hit":      _vel(hit,      60, 105),
        "Horns":    _vel(horns,    40, 90),
        "Tuba":     _vel(tuba,     35, 75),
        "Ostinato": _vel(ostinato, 40, 80),
        "Tremolo":  _vel(tremolo,  35, 80),
    }
    instruments = {
        "Brass":    GM_BRASS_SECTION, "Strings": GM_STRINGS_ENS,
        "Choir":    GM_CHOIR,         "Timpani": GM_TIMPANI,
        "Snare":    GM_SNARE,         "Hit":     GM_ORCH_HIT,
        "Horns":    GM_FRENCH_HORN,   "Tuba":    GM_TUBA,
        "Ostinato": GM_TREMOLO,       "Tremolo": GM_TREMOLO,
    }
    return raw, instruments, bpm, key


# ===========================================================================
# ACT V — The Hero's Return  (A Dorian, 80 BPM)
# Bittersweet triumph. Stems for cinematic cutscene / credits.
# Melody solo fades up from silence; choir swells last.
# Stems: Melody, Violin, Cello, Harp, Strings, Horns, Choir, Bells, Pedal
# ===========================================================================

def cue_05_heroes_return():
    print("  05 — The Hero's Return")
    bpm, dur = 80, 144.0
    key = A_DOR
    prog = _chords("im9 IVmaj9 im7 V7 im7 IIImaj7 bVII7 ivm7 im9 IVmaj7 Vsus4 V7 Imaj9 bVII7 Imaj9", dur, key)

    melody = MelodyGenerator(
        GeneratorParams(density=0.28, key_range_low=60, key_range_high=84),
        phrase_length=8.0, phrase_rest_probability=0.25,
        phrase_contour="arch", syncopation=0.08
    ).render(prog, key, dur)

    violin = ViolinGenerator(
        GeneratorParams(density=0.40, key_range_low=55, key_range_high=84),
        articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.6
    ).render(prog, key, dur - 24.0)
    violin = _off(violin, 24.0)

    cello = CelloGenerator(
        GeneratorParams(density=0.35, key_range_low=36, key_range_high=56),
        articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=1.2
    ).render(prog, key, dur)

    harp = HarpGenerator(
        GeneratorParams(density=0.35, key_range_low=36, key_range_high=80),
        pattern="arpeggio", direction="up", spread_speed=0.12
    ).render(prog, key, dur)

    strings = StringsLegatoGenerator(
        GeneratorParams(density=0.45, key_range_low=40, key_range_high=72),
        ensemble_mode="section", dynamic_shape="crescendo"
    ).render(prog, key, dur - 16.0)
    strings = _off(strings, 16.0)

    horns = FrenchHornGenerator(
        GeneratorParams(density=0.35, key_range_low=36, key_range_high=62),
        articulation="sustained", dynamic_curve="crescendo", note_density=1.8
    ).render(prog, key, dur - 32.0)
    horns = _off(horns, 32.0)

    choir = ChoirAahsGenerator(
        GeneratorParams(density=0.35, key_range_low=44, key_range_high=70),
        voice_count=5, dynamics="mp", syllable="aah", vibrato=0.30
    ).render(prog, key, dur - 48.0)
    choir = _off(choir, 48.0)

    bells = TubularBellsGenerator(
        GeneratorParams(density=0.20, key_range_low=60, key_range_high=84),
        stroke_pattern="chime"
    ).render(prog, key, dur)

    pedal = PedalBassGenerator(
        GeneratorParams(density=0.25, key_range_low=24, key_range_high=36),
        pedal_note="root", sustain=3.0, velocity_level=0.40
    ).render(prog, key, dur)

    raw = {
        "Melody":  _vel(melody,  35, 80),
        "Violin":  _vel(violin,  30, 78),
        "Cello":   _vel(cello,   30, 72),
        "Harp":    _vel(harp,    25, 60),
        "Strings": _vel(strings, 28, 78),
        "Horns":   _vel(horns,   30, 78),
        "Choir":   _vel(choir,   22, 68),
        "Bells":   _vel(bells,   30, 68),
        "Pedal":   _vel(pedal,   25, 55),
    }
    instruments = {
        "Melody":  GM_VIOLIN,   "Violin": GM_VIOLIN,    "Cello":   GM_CELLO,
        "Harp":    GM_HARP,     "Strings": GM_STRINGS_ENS,
        "Horns":   GM_FRENCH_HORN, "Choir": GM_CHOIR,
        "Bells":   GM_TUBULAR_BELLS, "Pedal": GM_CONTRABASS,
    }
    return raw, instruments, bpm, key


# ===========================================================================
# Cue registry
# ===========================================================================

CUES = [
    ("01_Village_at_Peace",       cue_01_village),
    ("02_Into_the_Wild",          cue_02_into_the_wild),
    ("03_Ancient_Dungeon",        cue_03_dungeon),
    ("04_Boss_Confrontation",     cue_04_boss),
    ("05_Heroes_Return",          cue_05_heroes_return),
]


def main():
    out_root = Path("output/fantasy_ue_stems")
    out_root.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 70)
    print("   ECHOES OF THE FORGOTTEN REALM — UE Stem Export")
    print("   Fantasy RPG Orchestral Score — 5 adaptive cues")
    print("=" * 70)
    print()
    print("  Stem layout per cue:")
    print("    <cue>/<cue>_stems/stem_<layer>.mid  — individual stems for UE")
    print("    <cue>/<cue>_mix.mid                 — full-mix reference MIDI")
    print()

    for cue_name, producer in CUES:
        print(f"  Cue: {cue_name}")
        raw, instruments, bpm, key = producer()
        cue_dir = out_root / cue_name
        cue_dir.mkdir(parents=True, exist_ok=True)
        _export_stems(raw, instruments, cue_dir, cue_name, bpm, key)

    print()
    print("=" * 70)
    print(f"  ✓ All stems exported to: {out_root.resolve()}/")
    print()
    print("  Unreal Engine integration:")
    print("    1. Import each stem_*.mid into your UE project as audio assets.")
    print("    2. Create a MetaSound / Sound Cue per cue folder.")
    print("    3. Drive stem volumes via Blueprint / WWise RTPCs:")
    print("       - Combat intensity  → Brass, Choir, Timpani, Snare, Hit")
    print("       - Exploration mode  → Melody, Flute, Harp, Pizzicato")
    print("       - Dungeon depth     → Tension, Drone, Tremolo (fade-in)")
    print("       - Narrative moment  → Strings, Horns, Choir (fade-in)")
    print("=" * 70)


if __name__ == "__main__":
    main()
