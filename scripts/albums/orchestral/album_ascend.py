# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_ascend.py — ASCEND: SYMPHONY OF RISING LIGHT

A 20-movement uplifting symphonic suite (~70 min) designed to elevate mood,
ignite motivation, and inspire perseverance. From dawn stillness to triumphant
fanfares, every track builds energy and resolve.

Five phases:
    Phase I:   Dawn Awakening     (stillness, first light, gentle hope)
    Phase II:  Gathering Storm    (building energy, determination, resolve)
    Phase III: The Climb          (struggle, perseverance, overcoming)
    Phase IV:  Summit Glory       (triumph, euphoria, celebration)
    Phase V:   Eternal Flame      (reflection, gratitude, lasting power)

Bright modes: IONIAN, LYDIAN, MIXOLYDIAN, MAJOR, DORIAN, PENTATONIC,
MELODIC_MINOR_ASC, HARMONIC_MAJOR, LYDIAN_AUGMENTED.
"""

from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams

# Solo orchestral instruments
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
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.tuba import TubaGenerator
from melodica.generators.snare_drum import SnareDrumGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator
from melodica.generators.organ_drawbars import OrganDrawbarsGenerator

# Specialty generators
from melodica.generators.harp import HarpGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.chorale import ChoraleGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.canon import CanonGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator

from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# ---------------------------------------------------------------------------
# Scales — bright, open, soaring
# ---------------------------------------------------------------------------

C_MAJOR  = Scale(root=0,  mode=Mode.MAJOR)
D_MAJOR  = Scale(root=2,  mode=Mode.MAJOR)
E_MAJOR  = Scale(root=4,  mode=Mode.MAJOR)
F_MAJOR  = Scale(root=5,  mode=Mode.MAJOR)
G_MAJOR  = Scale(root=7,  mode=Mode.MAJOR)
A_MAJOR  = Scale(root=9,  mode=Mode.MAJOR)
B_MAJOR  = Scale(root=11, mode=Mode.MAJOR)
BB_MAJOR = Scale(root=10, mode=Mode.MAJOR)
EB_MAJOR = Scale(root=3,  mode=Mode.MAJOR)

C_LYDIAN  = Scale(root=0,  mode=Mode.LYDIAN)
D_LYDIAN  = Scale(root=2,  mode=Mode.LYDIAN)
F_LYDIAN  = Scale(root=5,  mode=Mode.LYDIAN)
G_LYDIAN  = Scale(root=7,  mode=Mode.LYDIAN)
A_LYDIAN  = Scale(root=9,  mode=Mode.LYDIAN)

D_MIXO = Scale(root=2,  mode=Mode.MIXOLYDIAN)
G_MIXO = Scale(root=7,  mode=Mode.MIXOLYDIAN)
A_MIXO = Scale(root=9,  mode=Mode.MIXOLYDIAN)

D_DOR   = Scale(root=2,  mode=Mode.DORIAN)
E_DOR   = Scale(root=4,  mode=Mode.DORIAN)
A_DOR   = Scale(root=9,  mode=Mode.DORIAN)
B_DOR   = Scale(root=11, mode=Mode.DORIAN)

E_DBL_HM = Scale(root=4, mode=Mode.DOUBLE_HARM_MAJOR)
A_LYD_AUG = Scale(root=9, mode=Mode.LYDIAN_AUG_MODE)

E_MELODIC = Scale(root=4,  mode=Mode.MELODIC_MINOR)
A_MELODIC = Scale(root=9,  mode=Mode.MELODIC_MINOR)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _build_chords(progression: str, duration: float, key: Scale) -> list[ChordLabel]:
    parts = progression.split()
    beats_per = duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        chord = key.parse_roman(p)
        chord.start = i * beats_per
        chord.duration = beats_per
        chords.append(chord)
    return chords


def _clamp(notes: list[NoteInfo], lo: int = 1, hi: int = 127) -> list[NoteInfo]:
    for n in notes:
        n.velocity = max(lo, min(hi, n.velocity))
    return notes


def _expr_swell(note: NoteInfo, duration: float, peak_ratio: float = 0.5):
    peak_t = note.start + duration * peak_ratio
    note.expression[11] = [
        (round(note.start, 3), 50),
        (round(peak_t, 3), 110),
        (round(note.start + duration, 3), 40),
    ]


def apply_ascend_mix(raw_tracks: dict, bpm: float, lufs: float = -14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Violin": 0.80, "Viola": 0.78, "Cello": 0.82, "Bass": 0.85,
        "Brass": 0.78, "Horns": 0.80, "Trumpet": 0.76, "Trombone": 0.74,
        "Tuba": 0.84, "Woodwinds": 0.78, "Flute": 0.74, "Oboe": 0.76,
        "Clarinet": 0.78, "Bassoon": 0.80, "Choir": 0.82, "Organ": 0.72,
        "Harp": 0.84, "Timpani": 0.86, "Mallet": 0.78, "Bells": 0.82,
        "Snare": 0.68, "Tremolo": 0.78, "Pizzicato": 0.76, "Pedal": 0.82,
        "Ostinato": 0.78, "Chorale": 0.80, "Counterpoint": 0.78,
        "Canon": 0.78, "Hit": 0.84, "Strings": 0.82, "Fanfare": 0.80,
        "WoodwindsEns": 0.78, "Glock": 0.76,
    })
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan


# ===========================================================================
# PHASE I: DAWN AWAKENING — Stillness, First Light, Gentle Hope
# ===========================================================================

def track_01_dawn():
    """1. First Light (C Lydian, 56 BPM)
    Solo harp + muted strings. The world stirs."""
    print("  1. First Light")
    dur = 72.0
    chords = _build_chords("I II I V I IV V I IV I II V I", dur, C_LYDIAN)

    harp_p = GeneratorParams(density=0.5, key_range_low=60, key_range_high=84)
    harp = HarpGenerator(harp_p, pattern="arpeggio", direction="up", octave_span=3)
    harp_notes = _clamp(harp.render(chords, C_LYDIAN, dur), 45, 80)

    str_p = GeneratorParams(density=0.3, key_range_low=48, key_range_high=72)
    strings = StringsLegatoGenerator(str_p, section_size="chamber", dynamic_shape="cresc_dim")
    str_notes = _clamp(strings.render(chords, C_LYDIAN, dur), 30, 60)

    fl_p = GeneratorParams(density=0.25, key_range_low=72, key_range_high=96)
    flute = FluteGenerator(fl_p, articulation="legato", register=3)
    fl_notes = _clamp(flute.render(chords, C_LYDIAN, dur), 35, 65)

    return {
        "Harp": harp_notes, "Strings": str_notes, "Flute": fl_notes,
    }, 56.0


def track_02_breathe():
    """2. Breathe (F Major, 60 BPM)
    Gentle oboe melody over sustained choir. Breathe in hope."""
    print("  2. Breathe")
    dur = 64.0
    chords = _build_chords("I vi IV V I iii vi V I IV I V I", dur, F_MAJOR)

    ob_p = GeneratorParams(density=0.4, key_range_low=70, key_range_high=91)
    oboe = OboeGenerator(ob_p, articulation="legato", vibrato=True, register=2)
    ob_notes = _clamp(oboe.render(chords, F_MAJOR, dur), 40, 75)

    choir_p = GeneratorParams(density=0.3, key_range_low=48, key_range_high=72)
    choir = ChoirAahsGenerator(choir_p, voice_count=4, dynamics="mp", syllable="aah")
    ch_notes = _clamp(choir.render(chords, F_MAJOR, dur), 30, 55)

    hp_p = GeneratorParams(density=0.4, key_range_low=60, key_range_high=84)
    harp = HarpGenerator(hp_p, pattern="arpeggio", direction="up")
    hp_notes = _clamp(harp.render(chords, F_MAJOR, dur), 35, 65)

    return {
        "Oboe": ob_notes, "Choir": ch_notes, "Harp": hp_notes,
    }, 60.0


def track_03_morning():
    """3. Morning Dew (G Lydian, 64 BPM)
    Glockenspiel sparkle + pizzicato strings. Freshness."""
    print("  3. Morning Dew")
    dur = 56.0
    chords = _build_chords("I II V I IV V I II IV I V I", dur, G_LYDIAN)

    gl_p = GeneratorParams(density=0.45, key_range_low=84, key_range_high=108)
    glock = GlockenspielGenerator(gl_p, pattern="sparkling_run", note_density=1.2)
    gl_notes = _clamp(glock.render(chords, G_LYDIAN, dur), 40, 70)

    piz_p = GeneratorParams(density=0.4, key_range_low=48, key_range_high=72)
    pizz = StringsPizzicatoGenerator(piz_p)
    piz_notes = _clamp(pizz.render(chords, G_LYDIAN, dur), 35, 65)

    cl_p = GeneratorParams(density=0.3, key_range_low=60, key_range_high=84)
    clar = ClarinetGenerator(cl_p, articulation="legato")
    cl_notes = _clamp(clar.render(chords, G_LYDIAN, dur), 35, 65)

    return {
        "Glock": gl_notes, "Pizzicato": piz_notes, "Clarinet": cl_notes,
    }, 64.0


def track_04_awaken():
    """4. The World Awakens (D Major, 68 BPM)
    Full strings + horns. Energy begins to build."""
    print("  4. The World Awakens")
    dur = 68.0
    chords = _build_chords("I IV V I vi iii IV V I I IV V I", dur, D_MAJOR)

    str_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=79)
    strings = StringsLegatoGenerator(str_p, section_size="full", dynamic_shape="cresc_dim")
    str_notes = _clamp(strings.render(chords, D_MAJOR, dur), 40, 80)

    hn_p = GeneratorParams(density=0.35, key_range_low=48, key_range_high=67)
    horns = FrenchHornGenerator(hn_p, articulation="sustained", fanfare_mode=True, note_density=0.8)
    hn_notes = _clamp(horns.render(chords, D_MAJOR, dur), 40, 75)

    hp_p = GeneratorParams(density=0.4, key_range_low=60, key_range_high=84)
    harp = HarpGenerator(hp_p, pattern="arpeggio", direction="up", octave_span=3)
    hp_notes = _clamp(harp.render(chords, D_MAJOR, dur), 35, 70)

    fl_p = GeneratorParams(density=0.3, key_range_low=72, key_range_high=96)
    flute = FluteGenerator(fl_p, articulation="legato", register=3)
    fl_notes = _clamp(flute.render(chords, D_MAJOR, dur), 40, 70)

    return {
        "Strings": str_notes, "Horns": hn_notes, "Harp": hp_notes, "Flute": fl_notes,
    }, 68.0


# ===========================================================================
# PHASE II: GATHERING STORM — Building Energy, Determination, Resolve
# ===========================================================================

def track_05_resolve():
    """5. Inner Resolve (A Lydian, 72 BPM)
    Ostinato strings + woodwinds. Determination takes hold."""
    print("  5. Inner Resolve")
    dur = 64.0
    chords = _build_chords("I V vi IV I V IV V I vi I V I", dur, A_LYDIAN)

    ost_p = GeneratorParams(density=0.6, key_range_low=48, key_range_high=72)
    ost = OstinatoGenerator(ost_p, pattern="alternating", repeat_notes=2, changed_notes_count=1)
    ost_notes = _clamp(ost.render(chords, A_LYDIAN, dur), 45, 75)

    ww_p = GeneratorParams(density=0.4, key_range_low=60, key_range_high=84)
    ww = WoodwindsEnsembleGenerator(ww_p, section="quartet", articulation="legato")
    ww_notes = _clamp(ww.render(chords, A_LYDIAN, dur), 40, 70)

    tr_p = GeneratorParams(density=0.35, key_range_low=48, key_range_high=67)
    trump = TrumpetGenerator(tr_p, articulation="sustained", fanfare_mode=True, note_density=0.7)
    tr_notes = _clamp(trump.render(chords, A_LYDIAN, dur), 40, 70)

    return {
        "Ostinato": ost_notes, "WoodwindsEns": ww_notes, "Trumpet": tr_notes,
    }, 72.0


def track_06_gathering():
    """6. Gathering Clouds (E Melodic Minor, 76 BPM)
    Tremolo strings + timpani rolls. Storm of purpose."""
    print("  6. Gathering Clouds")
    dur = 60.0
    chords = _build_chords("i IV V i VI VII i iv V i VI i V i", dur, E_MELODIC)

    trem_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=72)
    trem = TremoloStringsGenerator(trem_p, bow_speed=0.0625, dynamic_swell=True)
    trem_notes = _clamp(trem.render(chords, E_MELODIC, dur), 40, 80)

    timp_p = GeneratorParams(density=0.4, key_range_low=36, key_range_high=55)
    timp = TimpaniGenerator(timp_p, stroke_pattern="roll", drum_count=4, tuning_follows=True)
    timp_notes = _clamp(timp.render(chords, E_MELODIC, dur), 50, 90)

    hn_p = GeneratorParams(density=0.35, key_range_low=48, key_range_high=67)
    horns = FrenchHornGenerator(hn_p, articulation="sustained", dynamic_curve="crescendo")
    hn_notes = _clamp(horns.render(chords, E_MELODIC, dur), 40, 75)

    return {
        "Tremolo": trem_notes, "Timpani": timp_notes, "Horns": hn_notes,
    }, 76.0


def track_07_fire():
    """7. Spark of Fire (D Mixolydian, 80 BPM)
    Brass fanfare + snare. Energy ignites."""
    print("  7. Spark of Fire")
    dur = 56.0
    chords = _build_chords("I IV I V IV I V IV I bVII IV I V I", dur, D_MIXO)

    brass_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=72)
    brass = BrassSectionGenerator(brass_p, articulation="hit", voicing="closed",
                                   divisi_count=3, ensemble_mode="full")
    br_notes = _clamp(brass.render(chords, D_MIXO, dur), 50, 90)

    sn_p = GeneratorParams(density=0.5, key_range_low=38, key_range_high=40)
    snare = SnareDrumGenerator(sn_p, pattern_type="march")
    sn_notes = _clamp(snare.render(chords, D_MIXO, dur), 45, 85)

    timp_p = GeneratorParams(density=0.4, key_range_low=36, key_range_high=55)
    timp = TimpaniGenerator(timp_p, stroke_pattern="single", drum_count=4)
    timp_notes = _clamp(timp.render(chords, D_MIXO, dur), 50, 85)

    return {
        "Brass": br_notes, "Snare": sn_notes, "Timpani": timp_notes,
    }, 80.0


def track_08_rise():
    """8. Rise Up (G Major, 84 BPM)
    Full strings + choir. Rising together."""
    print("  8. Rise Up")
    dur = 60.0
    chords = _build_chords("I V vi IV I V IV V I iii vi IV V I", dur, G_MAJOR)

    str_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=79)
    strings = StringsLegatoGenerator(str_p, section_size="full", dynamic_shape="cresc_dim")
    str_notes = _clamp(strings.render(chords, G_MAJOR, dur), 45, 85)

    choir_p = GeneratorParams(density=0.4, key_range_low=48, key_range_high=72)
    choir = ChoirAahsGenerator(choir_p, voice_count=4, dynamics="f", syllable="aah")
    ch_notes = _clamp(choir.render(chords, G_MAJOR, dur), 40, 80)

    hn_p = GeneratorParams(density=0.4, key_range_low=48, key_range_high=67)
    horns = FrenchHornGenerator(hn_p, articulation="sustained", fanfare_mode=True, note_density=0.9)
    hn_notes = _clamp(horns.render(chords, G_MAJOR, dur), 45, 80)

    bell_p = GeneratorParams(density=0.3, key_range_low=72, key_range_high=96)
    bells = TubularBellsGenerator(bell_p, stroke_pattern="single")
    bell_notes = _clamp(bells.render(chords, G_MAJOR, dur), 50, 80)

    return {
        "Strings": str_notes, "Choir": ch_notes, "Horns": hn_notes, "Bells": bell_notes,
    }, 84.0


# ===========================================================================
# PHASE III: THE CLIMB — Struggle, Perseverance, Overcoming
# ===========================================================================

def track_09_mountain():
    """9. The Mountain Before You (B Dorian, 78 BPM)
    Pedal bass + counterpoint. The challenge is real."""
    print("  9. The Mountain Before You")
    dur = 64.0
    chords = _build_chords("i IV v i VII IV i v VII i IV VII v i", dur, B_DOR)

    ped_p = GeneratorParams(density=0.4, key_range_low=24, key_range_high=43)
    pedal = PedalBassGenerator(ped_p)
    ped_notes = _clamp(pedal.render(chords, B_DOR, dur), 40, 75)

    cp_p = GeneratorParams(density=0.5, key_range_low=55, key_range_high=79)
    cp = CounterpointGenerator(cp_p, species=1, voices=2)
    cp_notes = _clamp(cp.render(chords, B_DOR, dur), 45, 75)

    str_p = GeneratorParams(density=0.45, key_range_low=48, key_range_high=72)
    strings = StringsLegatoGenerator(str_p, section_size="full", dynamic_shape="cresc_dim")
    str_notes = _clamp(strings.render(chords, B_DOR, dur), 40, 75)

    return {
        "Pedal": ped_notes, "Counterpoint": cp_notes, "Strings": str_notes,
    }, 78.0


def track_10_steps():
    """10. Every Step Counts (A Melodic Minor, 82 BPM)
    Ostinato + woodwinds. Steady progress upward."""
    print("  10. Every Step Counts")
    dur = 56.0
    chords = _build_chords("i IV V i VI VII i iv V i VII V i IV i", dur, A_MELODIC)

    ost_p = GeneratorParams(density=0.6, key_range_low=48, key_range_high=72)
    ost = OstinatoGenerator(ost_p, pattern="ascending", repeat_notes=1, changed_notes_count=2)
    ost_notes = _clamp(ost.render(chords, A_MELODIC, dur), 50, 80)

    ww_p = GeneratorParams(density=0.4, key_range_low=60, key_range_high=84)
    ww = WoodwindsEnsembleGenerator(ww_p, articulation="legato", breath_interval=5.0)
    ww_notes = _clamp(ww.render(chords, A_MELODIC, dur), 45, 75)

    timp_p = GeneratorParams(density=0.4, key_range_low=36, key_range_high=55)
    timp = TimpaniGenerator(timp_p, stroke_pattern="single", drum_count=4, tuning_follows=True)
    timp_notes = _clamp(timp.render(chords, A_MELODIC, dur), 50, 80)

    return {
        "Ostinato": ost_notes, "WoodwindsEns": ww_notes, "Timpani": timp_notes,
    }, 82.0


def track_11_storm():
    """11. Through the Storm (D Dorian, 88 BPM)
    Brass + snare + tremolo. Pushing through adversity."""
    print("  11. Through the Storm")
    dur = 52.0
    chords = _build_chords("i IV v i VII IV i v VII i IV v i VII i", dur, D_DOR)

    brass_p = GeneratorParams(density=0.6, key_range_low=48, key_range_high=72)
    brass = BrassSectionGenerator(brass_p, articulation="sustained", voicing="open",
                                   divisi_count=3, ensemble_mode="full")
    br_notes = _clamp(brass.render(chords, D_DOR, dur), 50, 90)

    sn_p = GeneratorParams(density=0.5, key_range_low=38, key_range_high=40)
    snare = SnareDrumGenerator(sn_p, pattern_type="march")
    sn_notes = _clamp(snare.render(chords, D_DOR, dur), 50, 90)

    trem_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    trem = TremoloStringsGenerator(trem_p, bow_speed=0.0625, dynamic_swell=True)
    trem_notes = _clamp(trem.render(chords, D_DOR, dur), 45, 85)

    return {
        "Brass": br_notes, "Snare": sn_notes, "Tremolo": trem_notes,
    }, 88.0


def track_12_unbreak():
    """12. Unbreakable (E Dorian, 84 BPM)
    Canon + full strings + choir. Spirit that cannot be broken."""
    print("  12. Unbreakable")
    dur = 60.0
    chords = _build_chords("i IV v i VII IV i v VII i IV v i VII i", dur, E_DOR)

    canon_p = GeneratorParams(density=0.5, key_range_low=55, key_range_high=79)
    canon = CanonGenerator(canon_p)
    ca_notes = _clamp(canon.render(chords, E_DOR, dur), 45, 80)

    str_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=79)
    strings = StringsLegatoGenerator(str_p, section_size="full", dynamic_shape="cresc_dim")
    str_notes = _clamp(strings.render(chords, E_DOR, dur), 45, 85)

    choir_p = GeneratorParams(density=0.4, key_range_low=48, key_range_high=72)
    choir = ChoirAahsGenerator(choir_p, voice_count=4, dynamics="f", syllable="aah")
    ch_notes = _clamp(choir.render(chords, E_DOR, dur), 40, 80)

    return {
        "Canon": ca_notes, "Strings": str_notes, "Choir": ch_notes,
    }, 84.0


# ===========================================================================
# PHASE IV: SUMMIT GLORY — Triumph, Euphoria, Celebration
# ===========================================================================

def track_13_summit():
    """13. The Summit (C Major, 90 BPM)
    Full orchestra fanfare. You made it to the top."""
    print("  13. The Summit")
    dur = 52.0
    chords = _build_chords("I IV V I vi IV V I I IV V I V I", dur, C_MAJOR)

    brass_p = GeneratorParams(density=0.65, key_range_low=48, key_range_high=72)
    brass = BrassSectionGenerator(brass_p, articulation="sustained", voicing="open",
                                   divisi_count=4, ensemble_mode="full", intensity=1.0)
    br_notes = _clamp(brass.render(chords, C_MAJOR, dur), 55, 100)

    str_p = GeneratorParams(density=0.6, key_range_low=48, key_range_high=84)
    strings = StringsLegatoGenerator(str_p, section_size="full", dynamic_shape="cresc_dim")
    str_notes = _clamp(strings.render(chords, C_MAJOR, dur), 50, 95)

    timp_p = GeneratorParams(density=0.5, key_range_low=36, key_range_high=55)
    timp = TimpaniGenerator(timp_p, stroke_pattern="roll", drum_count=4, roll_speed=0.0625)
    timp_notes = _clamp(timp.render(chords, C_MAJOR, dur), 55, 95)

    bell_p = GeneratorParams(density=0.4, key_range_low=72, key_range_high=96)
    bells = TubularBellsGenerator(bell_p, stroke_pattern="single")
    bell_notes = _clamp(bells.render(chords, C_MAJOR, dur), 55, 90)

    return {
        "Brass": br_notes, "Strings": str_notes, "Timpani": timp_notes, "Bells": bell_notes,
    }, 90.0


def track_14_glory():
    """14. Glory and Light (D Major, 92 BPM)
    Trumpet fanfare + glockenspiel + full choir."""
    print("  14. Glory and Light")
    dur = 48.0
    chords = _build_chords("I V vi IV I V IV V I iii vi IV V I", dur, D_MAJOR)

    tr_p = GeneratorParams(density=0.55, key_range_low=58, key_range_high=79)
    trump = TrumpetGenerator(tr_p, articulation="sustained", fanfare_mode=True, note_density=1.0)
    tr_notes = _clamp(trump.render(chords, D_MAJOR, dur), 55, 95)

    gl_p = GeneratorParams(density=0.5, key_range_low=84, key_range_high=108)
    glock = GlockenspielGenerator(gl_p, pattern="sparkling_run", note_density=1.3)
    gl_notes = _clamp(glock.render(chords, D_MAJOR, dur), 50, 85)

    choir_p = GeneratorParams(density=0.45, key_range_low=48, key_range_high=72)
    choir = ChoirAahsGenerator(choir_p, voice_count=4, dynamics="ff", syllable="aah")
    ch_notes = _clamp(choir.render(chords, D_MAJOR, dur), 45, 90)

    str_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=79)
    strings = StringsLegatoGenerator(str_p, section_size="full", dynamic_shape="cresc_dim")
    str_notes = _clamp(strings.render(chords, D_MAJOR, dur), 50, 90)

    return {
        "Trumpet": tr_notes, "Glock": gl_notes, "Choir": ch_notes, "Strings": str_notes,
    }, 92.0


def track_15_champions():
    """15. Champions Rise (Eb Major, 96 BPM)
    Full orchestral hit + snare + brass. Epic celebration."""
    print("  15. Champions Rise")
    dur = 44.0
    chords = _build_chords("I IV V I vi IV I V I bVII IV I V I", dur, EB_MAJOR)

    hit_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    hit = OrchestralHitGenerator(hit_p, hit_type="staccato", voicing="chord")
    hit_notes = _clamp(hit.render(chords, EB_MAJOR, dur), 55, 100)

    brass_p = GeneratorParams(density=0.6, key_range_low=48, key_range_high=72)
    brass = BrassSectionGenerator(brass_p, articulation="hit", voicing="open",
                                   divisi_count=4, ensemble_mode="full", intensity=1.0)
    br_notes = _clamp(brass.render(chords, EB_MAJOR, dur), 55, 100)

    sn_p = GeneratorParams(density=0.5, key_range_low=38, key_range_high=40)
    snare = SnareDrumGenerator(sn_p, pattern_type="march")
    sn_notes = _clamp(snare.render(chords, EB_MAJOR, dur), 50, 95)

    choir_p = GeneratorParams(density=0.4, key_range_low=48, key_range_high=72)
    choir = ChoirAahsGenerator(choir_p, voice_count=4, dynamics="ff", syllable="aah")
    ch_notes = _clamp(choir.render(chords, EB_MAJOR, dur), 45, 90)

    return {
        "Hit": hit_notes, "Brass": br_notes, "Snare": sn_notes, "Choir": ch_notes,
    }, 96.0


def track_16_euphoria():
    """16. Euphoria (A Major, 100 BPM)
    Fast strings + woodwinds + bells. Pure joy."""
    print("  16. Euphoria")
    dur = 40.0
    chords = _build_chords("I V vi IV I IV V I I vi IV V I", dur, A_MAJOR)

    str_p = GeneratorParams(density=0.65, key_range_low=48, key_range_high=84)
    strings = StringsLegatoGenerator(str_p, section_size="full", dynamic_shape="cresc_dim")
    str_notes = _clamp(strings.render(chords, A_MAJOR, dur), 50, 95)

    ww_p = GeneratorParams(density=0.5, key_range_low=60, key_range_high=84)
    ww = WoodwindsEnsembleGenerator(ww_p, articulation="legato", breath_interval=4.0)
    ww_notes = _clamp(ww.render(chords, A_MAJOR, dur), 45, 85)

    bell_p = GeneratorParams(density=0.4, key_range_low=72, key_range_high=96)
    bells = TubularBellsGenerator(bell_p, stroke_pattern="single")
    bell_notes = _clamp(bells.render(chords, A_MAJOR, dur), 55, 90)

    gl_p = GeneratorParams(density=0.45, key_range_low=84, key_range_high=108)
    glock = GlockenspielGenerator(gl_p, pattern="sparkling_run", note_density=1.4)
    gl_notes = _clamp(glock.render(chords, A_MAJOR, dur), 50, 85)

    return {
        "Strings": str_notes, "WoodwindsEns": ww_notes,
        "Bells": bell_notes, "Glock": gl_notes,
    }, 100.0


# ===========================================================================
# PHASE V: ETERNAL FLAME — Reflection, Gratitude, Lasting Power
# ===========================================================================

def track_17_look_back():
    """17. Look How Far (F Lydian, 72 BPM)
    Gentle reflection. Solo violin + choir + harp."""
    print("  17. Look How Far")
    dur = 64.0
    chords = _build_chords("I II V I IV V I II IV I V I I IV V I", dur, F_LYDIAN)

    vn_p = GeneratorParams(density=0.5, key_range_low=67, key_range_high=91)
    violin = ViolinGenerator(vn_p, articulation="legato", vibrato=True, dynamic_curve="swell")
    vn_notes = _clamp(violin.render(chords, F_LYDIAN, dur), 45, 80)

    choir_p = GeneratorParams(density=0.35, key_range_low=48, key_range_high=72)
    choir = ChoirAahsGenerator(choir_p, voice_count=4, dynamics="mf", syllable="aah")
    ch_notes = _clamp(choir.render(chords, F_LYDIAN, dur), 35, 65)

    hp_p = GeneratorParams(density=0.4, key_range_low=60, key_range_high=84)
    harp = HarpGenerator(hp_p, pattern="arpeggio", direction="up", octave_span=3)
    hp_notes = _clamp(harp.render(chords, F_LYDIAN, dur), 40, 70)

    return {
        "Violin": vn_notes, "Choir": ch_notes, "Harp": hp_notes,
    }, 72.0


def track_18_gratitude():
    """18. Gratitude (Bb Major, 68 BPM)
    Chorale + bells + cello. Thankful stillness."""
    print("  18. Gratitude")
    dur = 60.0
    chords = _build_chords("I IV V I vi iii IV V I I vi IV V I", dur, BB_MAJOR)

    chor_p = GeneratorParams(density=0.4, key_range_low=48, key_range_high=72)
    chorale = ChoraleGenerator(chor_p)
    ch_notes = _clamp(chorale.render(chords, BB_MAJOR, dur), 40, 75)

    bell_p = GeneratorParams(density=0.3, key_range_low=72, key_range_high=96)
    bells = TubularBellsGenerator(bell_p, stroke_pattern="single")
    bell_notes = _clamp(bells.render(chords, BB_MAJOR, dur), 45, 75)

    cel_p = GeneratorParams(density=0.4, key_range_low=36, key_range_high=60)
    cello = CelloGenerator(cel_p, articulation="sustained", vibrato=True, dynamic_curve="swell")
    cel_notes = _clamp(cello.render(chords, BB_MAJOR, dur), 40, 70)

    return {
        "Chorale": ch_notes, "Bells": bell_notes, "Cello": cel_notes,
    }, 68.0


def track_19_carry():
    """19. Carry the Flame (E Harmonic Major, 80 BPM)
    Organ + full orchestra. The light endures."""
    print("  19. Carry the Flame")
    dur = 52.0
    chords = _build_chords("I IV V I vi III IV V I I vi IV V I", dur, E_DBL_HM)

    org_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    organ = OrganDrawbarsGenerator(org_p, registration="gospel", leslie_speed="slow", percussion=True)
    org_notes = _clamp(organ.render(chords, E_DBL_HM, dur), 45, 80)

    str_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=79)
    strings = StringsLegatoGenerator(str_p, section_size="full", dynamic_shape="cresc_dim")
    str_notes = _clamp(strings.render(chords, E_DBL_HM, dur), 45, 85)

    brass_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    brass = BrassSectionGenerator(brass_p, articulation="sustained", voicing="open",
                                   divisi_count=3, ensemble_mode="full")
    br_notes = _clamp(brass.render(chords, E_DBL_HM, dur), 50, 85)

    choir_p = GeneratorParams(density=0.4, key_range_low=48, key_range_high=72)
    choir = ChoirAahsGenerator(choir_p, voice_count=4, dynamics="f", syllable="aah")
    ch_notes = _clamp(choir.render(chords, E_DBL_HM, dur), 45, 80)

    return {
        "Organ": org_notes, "Strings": str_notes,
        "Brass": br_notes, "Choir": ch_notes,
    }, 80.0


def track_20_eternal():
    """20. Eternal Ascend (C Major, 88 BPM)
    Full orchestra tutti + choir + bells. Grand finale."""
    print("  20. Eternal Ascend")
    dur = 56.0
    chords = _build_chords("I IV V I vi IV V I I IV V I V I IV V I", dur, C_MAJOR)

    str_p = GeneratorParams(density=0.65, key_range_low=48, key_range_high=84)
    strings = StringsLegatoGenerator(str_p, section_size="full", dynamic_shape="cresc_dim")
    str_notes = _clamp(strings.render(chords, C_MAJOR, dur), 50, 100)

    brass_p = GeneratorParams(density=0.6, key_range_low=48, key_range_high=72)
    brass = BrassSectionGenerator(brass_p, articulation="sustained", voicing="open",
                                   divisi_count=4, ensemble_mode="full", intensity=1.0)
    br_notes = _clamp(brass.render(chords, C_MAJOR, dur), 55, 100)

    choir_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    choir = ChoirAahsGenerator(choir_p, voice_count=4, dynamics="ff", syllable="aah")
    ch_notes = _clamp(choir.render(chords, C_MAJOR, dur), 50, 95)

    timp_p = GeneratorParams(density=0.5, key_range_low=36, key_range_high=55)
    timp = TimpaniGenerator(timp_p, stroke_pattern="roll", drum_count=4, roll_speed=0.0625)
    timp_notes = _clamp(timp.render(chords, C_MAJOR, dur), 55, 100)

    bell_p = GeneratorParams(density=0.4, key_range_low=72, key_range_high=96)
    bells = TubularBellsGenerator(bell_p, stroke_pattern="single")
    bell_notes = _clamp(bells.render(chords, C_MAJOR, dur), 55, 95)

    gl_p = GeneratorParams(density=0.45, key_range_low=84, key_range_high=108)
    glock = GlockenspielGenerator(gl_p, pattern="sparkling_run", note_density=1.3)
    gl_notes = _clamp(glock.render(chords, C_MAJOR, dur), 50, 90)

    return {
        "Strings": str_notes, "Brass": br_notes, "Choir": ch_notes,
        "Timpani": timp_notes, "Bells": bell_notes, "Glock": gl_notes,
    }, 88.0


# ===========================================================================
# Track registry
# ===========================================================================

TRACKS = [
    # Phase I: Dawn Awakening
    (track_01_dawn,     "01_First_Light.mid", {
        "Harp": 46, "Strings": 48, "Flute": 73,
    }),
    (track_02_breathe,  "02_Breathe.mid", {
        "Oboe": 68, "Choir": 52, "Harp": 46,
    }),
    (track_03_morning,  "03_Morning_Dew.mid", {
        "Glock": 9, "Pizzicato": 45, "Clarinet": 71,
    }),
    (track_04_awaken,   "04_The_World_Awakens.mid", {
        "Strings": 48, "Horns": 60, "Harp": 46, "Flute": 73,
    }),
    # Phase II: Gathering Storm
    (track_05_resolve,  "05_Inner_Resolve.mid", {
        "Ostinato": 43, "WoodwindsEns": 68, "Trumpet": 56,
    }),
    (track_06_gathering,"06_Gathering_Clouds.mid", {
        "Tremolo": 44, "Timpani": 47, "Horns": 60,
    }),
    (track_07_fire,     "07_Spark_of_Fire.mid", {
        "Brass": 61, "Snare": 115, "Timpani": 47,
    }),
    (track_08_rise,     "08_Rise_Up.mid", {
        "Strings": 48, "Choir": 52, "Horns": 60, "Bells": 14,
    }),
    # Phase III: The Climb
    (track_09_mountain, "09_The_Mountain_Before_You.mid", {
        "Pedal": 43, "Counterpoint": 40, "Strings": 48,
    }),
    (track_10_steps,    "10_Every_Step_Counts.mid", {
        "Ostinato": 43, "WoodwindsEns": 68, "Timpani": 47,
    }),
    (track_11_storm,    "11_Through_the_Storm.mid", {
        "Brass": 61, "Snare": 115, "Tremolo": 44,
    }),
    (track_12_unbreak,  "12_Unbreakable.mid", {
        "Canon": 40, "Strings": 48, "Choir": 52,
    }),
    # Phase IV: Summit Glory
    (track_13_summit,   "13_The_Summit.mid", {
        "Brass": 61, "Strings": 48, "Timpani": 47, "Bells": 14,
    }),
    (track_14_glory,    "14_Glory_and_Light.mid", {
        "Trumpet": 56, "Glock": 9, "Choir": 52, "Strings": 48,
    }),
    (track_15_champions,"15_Champions_Rise.mid", {
        "Hit": 55, "Brass": 61, "Snare": 115, "Choir": 52,
    }),
    (track_16_euphoria, "16_Euphoria.mid", {
        "Strings": 48, "WoodwindsEns": 68, "Bells": 14, "Glock": 9,
    }),
    # Phase V: Eternal Flame
    (track_17_look_back,"17_Look_How_Far.mid", {
        "Violin": 40, "Choir": 52, "Harp": 46,
    }),
    (track_18_gratitude,"18_Gratitude.mid", {
        "Chorale": 48, "Bells": 14, "Cello": 42,
    }),
    (track_19_carry,    "19_Carry_the_Flame.mid", {
        "Organ": 19, "Strings": 48, "Brass": 61, "Choir": 52,
    }),
    (track_20_eternal,  "20_Eternal_Ascend.mid", {
        "Strings": 48, "Brass": 61, "Choir": 52,
        "Timpani": 47, "Bells": 14, "Glock": 9,
    }),
]


def main():
    album_dir = Path("output/album_ascend")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("      A S C E N D :   S Y M P H O N Y   O F   R I S I N G   L I G H T")
    print("      20 Movements for Motivation and Elevation (~70 min)")
    print("      Phase I: Dawn Awakening | Phase II: Gathering Storm")
    print("      Phase III: The Climb | Phase IV: Summit Glory")
    print("      Phase V: Eternal Flame")
    print("=" * 80)

    total_notes = 0
    for i, (producer, filename, instruments) in enumerate(TRACKS):
        print("-" * 80)
        raw, bpm = producer()
        mastered, pan = apply_ascend_mix(raw, bpm)
        export_multitrack_midi(
            mastered,
            str(album_dir / filename),
            bpm=bpm,
            cc_events=pan,
            instruments=instruments,
        )
        note_count = sum(len(n) for n in raw.values())
        total_notes += note_count
        print(f"    -> {filename}  ({note_count} notes, {bpm} BPM)")

    print()
    print("=" * 80)
    print(f"  COMPLETE: ASCEND — Symphony of Rising Light")
    print(f"  {total_notes} total notes across 20 movements")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
