# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_dark_age.py — DARK AGE: ASHES OF THE FORGOTTEN

A 14-movement dark orchestral suite (~50 min) inspired by Dark Souls aesthetics:
desolation, hollow echoes, crumbling grandeur, doomed perseverance, and the
bittersweet linking of the flame.

Four phases:
    Phase I:  The Undead Asylum    (desolation, silence, distant memory)
    Phase II: The Fallen Kingdom   (ruins, hollows, fading glory)
    Phase III: The Abyss Beckons   (horror, corruption, despair)
    Phase IV: The First Flame      (sacrifice, resolve, bittersweet ending)

Modes emphasize darkness: PHRYGIAN, HARMONIC_MINOR, HUNGARIAN_MINOR,
AEOLIAN, LOCRIAN, DORIAN, PHRYGIAN_DOMINANT, MELODIC_MINOR,
DOUBLE_HARMONIC, ALTERED, BYZANTINE, PERSIAN, HORROR_CLUSTER.
"""

import math
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
from melodica.generators.drone import DroneGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.tension import TensionGenerator
from melodica.generators.chorale import ChoraleGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.canon import CanonGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator

from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# ---------------------------------------------------------------------------
# Scales — all dark, modal, unsettling
# ---------------------------------------------------------------------------

D_PHRYG     = Scale(root=2,  mode=Mode.PHRYGIAN)
E_PHRYG     = Scale(root=4,  mode=Mode.PHRYGIAN)
A_PHRYG     = Scale(root=9,  mode=Mode.PHRYGIAN)
B_PHRYG     = Scale(root=11, mode=Mode.PHRYGIAN)

E_HARM      = Scale(root=4,  mode=Mode.HARMONIC_MINOR)
A_HARM      = Scale(root=9,  mode=Mode.HARMONIC_MINOR)
B_HARM      = Scale(root=11, mode=Mode.HARMONIC_MINOR)
D_HARM      = Scale(root=2,  mode=Mode.HARMONIC_MINOR)
F_HARM      = Scale(root=5,  mode=Mode.HARMONIC_MINOR)
C_HARM      = Scale(root=0,  mode=Mode.HARMONIC_MINOR)
FS_HARM     = Scale(root=6,  mode=Mode.HARMONIC_MINOR)

E_HUNG      = Scale(root=4,  mode=Mode.HUNGARIAN_MINOR)
A_HUNG      = Scale(root=9,  mode=Mode.HUNGARIAN_MINOR)
B_HUNG      = Scale(root=11, mode=Mode.HUNGARIAN_MINOR)

D_AEOL      = Scale(root=2,  mode=Mode.AEOLIAN)
E_AEOL      = Scale(root=4,  mode=Mode.AEOLIAN)
A_AEOL      = Scale(root=9,  mode=Mode.AEOLIAN)
B_AEOL      = Scale(root=11, mode=Mode.AEOLIAN)
C_AEOL      = Scale(root=0,  mode=Mode.AEOLIAN)
F_AEOL      = Scale(root=5,  mode=Mode.AEOLIAN)
FS_AEOL     = Scale(root=6,  mode=Mode.AEOLIAN)
BB_AEOL     = Scale(root=10, mode=Mode.AEOLIAN)

E_LOC       = Scale(root=4,  mode=Mode.LOCRIAN)
B_LOC       = Scale(root=11, mode=Mode.LOCRIAN)

D_DOR       = Scale(root=2,  mode=Mode.DORIAN)
E_DOR       = Scale(root=4,  mode=Mode.DORIAN)
A_DOR       = Scale(root=9,  mode=Mode.DORIAN)

A_PHRYG_DOM = Scale(root=9,  mode=Mode.PHRYGIAN_DOMINANT)
E_PHRYG_DOM = Scale(root=4,  mode=Mode.PHRYGIAN_DOMINANT)
B_PHRYG_DOM = Scale(root=11, mode=Mode.PHRYGIAN_DOMINANT)

A_DBL_HARM  = Scale(root=9,  mode=Mode.DOUBLE_HARMONIC)
E_DBL_HARM  = Scale(root=4,  mode=Mode.DOUBLE_HARMONIC)

E_ALT       = Scale(root=4,  mode=Mode.ALTERED)

A_BYZ       = Scale(root=9,  mode=Mode.BYZANTINE)

E_PERS      = Scale(root=4,  mode=Mode.PERSIAN)

E_MELODIC   = Scale(root=4,  mode=Mode.MELODIC_MINOR)


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
        (round(note.start, 3), 40),
        (round(peak_t, 3), 100),
        (round(note.start + duration, 3), 30),
    ]


def apply_dark_age_mix(raw_tracks: dict, bpm: float, lufs: float = -16.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Violins": 0.75, "Viola": 0.73, "Cello": 0.78, "Bass": 0.85,
        "Brass": 0.72, "Horns": 0.74, "Trumpet": 0.68, "Trombone": 0.70,
        "Tuba": 0.82, "Woodwinds": 0.76, "Flute": 0.70, "Oboe": 0.72,
        "Clarinet": 0.74, "Bassoon": 0.78, "Choir": 0.80, "Organ": 0.68,
        "Harp": 0.82, "Timpani": 0.88, "Mallet": 0.74, "Bells": 0.78,
        "Snare": 0.60, "Tremolo": 0.74, "Pizzicato": 0.72, "Pedal": 0.82,
        "Drone": 0.78, "Ostinato": 0.76, "Tension": 0.70, "Chorale": 0.76,
        "Counterpoint": 0.74, "Canon": 0.74, "Hit": 0.82,
        "Strings": 0.78, "Fanfare": 0.74, "WoodwindsEns": 0.76,
    })
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan


# ===========================================================================
# PHASE I: THE UNDEAD ASYLUM — Desolation, Silence, Distant Memory
# ===========================================================================

def track_01_ashes():
    """I. Ashes Remain (E Phrygian, 38 BPM)
    A single cello over low drone. The world is dead and you wake."""
    print("  I. Ashes Remain")
    dur = 88.0
    chords = _build_chords("i bII i v i bVI bVII i v i bII bVI i", dur, E_PHRYG)

    cello_p = GeneratorParams(density=0.35, key_range_low=36, key_range_high=55)
    cello = CelloGenerator(cello_p, articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.2)
    cello_notes = _clamp(cello.render(chords, E_PHRYG, dur), 35, 75)
    for n in cello_notes:
        _expr_swell(n, min(n.duration, 6.0), peak_ratio=0.6)

    drone_p = GeneratorParams(density=0.02, key_range_low=20, key_range_high=32)
    drone = DroneGenerator(drone_p, velocity=45)
    drone_notes = _clamp(drone.render(chords, E_PHRYG, dur), 25, 50)

    bassoon_p = GeneratorParams(density=0.25, key_range_low=34, key_range_high=50)
    bassoon = BassoonGenerator(bassoon_p, articulation="sustained", vibrato=False, dynamic_curve="decrescendo", note_density=1.0)
    bassoon_notes = _clamp(bassoon.render(chords, E_PHRYG, dur), 30, 55)

    return {
        "Cello": cello_notes, "Drone": drone_notes, "Bassoon": bassoon_notes,
    }, 38.0


def track_02_hollow():
    """II. Hollow Steps (D Aeolian, 44 BPM)
    Pizzicato strings, distant timpani, shuffling through empty corridors."""
    print("  II. Hollow Steps")
    dur = 80.0
    chords = _build_chords("i iv i bVII i III iv v i bVII iv i v i", dur, D_AEOL)

    pizz_p = GeneratorParams(density=0.4, key_range_low=36, key_range_high=60)
    pizz = StringsPizzicatoGenerator(pizz_p, pattern="ostinato", staccato_length=0.08)
    pizz_notes = _clamp(pizz.render(chords, D_AEOL, dur), 30, 55)

    timp_p = GeneratorParams(density=0.2)
    timp = TimpaniGenerator(timp_p, stroke_pattern="roll", drum_count=4)
    timp_notes = _clamp(timp.render(chords, D_AEOL, dur), 35, 50)

    viola_p = GeneratorParams(density=0.3, key_range_low=48, key_range_high=65)
    viola = ViolaGenerator(viola_p, articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=1.0)
    viola_notes = _clamp(viola.render(chords, D_AEOL, dur), 30, 60)

    pedal_p = GeneratorParams(density=0.2, key_range_low=24, key_range_high=36)
    pedal = PedalBassGenerator(pedal_p, pedal_note="root", sustain=2.0, velocity_level=0.4)
    pedal_notes = _clamp(pedal.render(chords, D_AEOL, dur), 25, 45)

    return {
        "Pizzicato": pizz_notes, "Timpani": timp_notes, "Viola": viola_notes,
        "Pedal": pedal_notes,
    }, 44.0


def track_03_bonfire():
    """III. The Bonfire's Memory (A Dorian, 42 BPM)
    Gentle harp, oboe, and strings — a moment of warmth in the dark."""
    print("  III. The Bonfire's Memory")
    dur = 76.0
    chords = _build_chords("i IV i V i III VII iv i i IV VII i", dur, A_DOR)

    harp_p = GeneratorParams(density=0.45, key_range_low=40, key_range_high=80)
    harp = HarpGenerator(harp_p, pattern="arpeggio", direction="up", spread_speed=0.15)
    harp_notes = _clamp(harp.render(chords, A_DOR, dur), 30, 60)

    oboe_p = GeneratorParams(density=0.5, key_range_low=58, key_range_high=82)
    oboe = OboeGenerator(oboe_p, articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.5)
    oboe_notes = _clamp(oboe.render(chords, A_DOR, dur), 35, 75)
    for n in oboe_notes:
        _expr_swell(n, min(n.duration, 4.0))

    strings_p = GeneratorParams(density=0.4, key_range_low=44, key_range_high=72)
    strings = StringsLegatoGenerator(strings_p, ensemble_mode="section", dynamic_shape="crescendo")
    strings_notes = _clamp(strings.render(chords, A_DOR, dur), 25, 65)

    flute_p = GeneratorParams(density=0.35, key_range_low=60, key_range_high=90)
    flute = FluteGenerator(flute_p, articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=1.2)
    flute_notes = _clamp(flute.render(chords, A_DOR, dur), 30, 65)

    return {
        "Harp": harp_notes, "Oboe": oboe_notes, "Strings": strings_notes,
        "Flute": flute_notes,
    }, 42.0


# ===========================================================================
# PHASE II: THE FALLEN KINGDOM — Ruins, Hollows, Fading Glory
# ===========================================================================

def track_04_ruins():
    """IV. Anor Londo in Ruin (E Hungarian Minor, 48 BPM)
    Trombone chorale over ostinato, distant choir. The golden city crumbles."""
    print("  IV. Anor Londo in Ruin")
    dur = 84.0
    chords = _build_chords("i bII iv V i bVI iv bII i V bVI iv i", dur, E_HUNG)

    chorale_p = GeneratorParams(density=0.4, key_range_low=32, key_range_high=72)
    chorale = ChoraleGenerator(chorale_p, voice_spacing=12, soprano_motion="stepwise", rhythmic_unit=2.0)
    chorale_notes = _clamp(chorale.render(chords, E_HUNG, dur), 35, 70)

    ost_p = GeneratorParams(density=0.5, key_range_low=28, key_range_high=52)
    ostinato = OstinatoGenerator(ost_p, pattern="repeated_figure", repeat_notes=3, changed_notes_count=2)
    ost_notes = _clamp(ostinato.render(chords, E_HUNG, dur), 30, 55)

    choir_p = GeneratorParams(density=0.35, key_range_low=44, key_range_high=72)
    choir = ChoirAahsGenerator(choir_p, voice_count=4, dynamics="pp", syllable="aah", vibrato=0.2)
    choir_notes = _clamp(choir.render(chords, E_HUNG, dur), 25, 55)

    horn_p = GeneratorParams(density=0.35, key_range_low=36, key_range_high=60)
    horn = FrenchHornGenerator(horn_p, articulation="sustained", dynamic_curve="flat", note_density=1.5)
    horn_notes = _clamp(horn.render(chords, E_HUNG, dur), 30, 65)

    return {
        "Chorale": chorale_notes, "Ostinato": ost_notes, "Choir": choir_notes,
        "Horns": horn_notes,
    }, 48.0


def track_05_hollows_march():
    """V. March of the Hollows (B Phrygian, 52 BPM)
    Snare drum, low brass, grinding strings. Endless shambling."""
    print("  V. March of the Hollows")
    dur = 72.0
    chords = _build_chords("i bII i v bVII bVI bVII i v i bII v i", dur, B_PHRYG)

    snare_p = GeneratorParams(density=0.6)
    snare = SnareDrumGenerator(snare_p, pattern_type="march")
    snare_notes = _clamp(snare.render(chords, B_PHRYG, dur), 40, 70)

    trombone_p = GeneratorParams(density=0.45, key_range_low=28, key_range_high=48)
    trombone = TromboneGenerator(trombone_p, articulation="sustained", dynamic_curve="flat", note_density=2.0)
    trombone_notes = _clamp(trombone.render(chords, B_PHRYG, dur), 35, 70)

    trem_p = GeneratorParams(density=0.5, key_range_low=36, key_range_high=60)
    tremolo = TremoloStringsGenerator(trem_p, bow_speed=0.0625, dynamic_swell=False)
    trem_notes = _clamp(tremolo.render(chords, B_PHRYG, dur), 30, 60)

    tuba_p = GeneratorParams(density=0.35, key_range_low=24, key_range_high=40)
    tuba = TubaGenerator(tuba_p, articulation="sustained")
    tuba_notes = _clamp(tuba.render(chords, B_PHRYG, dur), 30, 60)

    timp_p = GeneratorParams(density=0.35)
    timp = TimpaniGenerator(timp_p, stroke_pattern="single", drum_count=5)
    timp_notes = _clamp(timp.render(chords, B_PHRYG, dur), 40, 65)

    return {
        "Snare": snare_notes, "Trombone": trombone_notes, "Tremolo": trem_notes,
        "Tuba": tuba_notes, "Timpani": timp_notes,
    }, 52.0


def track_06_fading_glory():
    """VI. Fading Glory (A Aeolian, 40 BPM)
    Solo violin lament, harp, pedal bass. Remembering what was lost."""
    print("  VI. Fading Glory")
    dur = 80.0
    chords = _build_chords("i iv i bVI bVII i III iv v i bVI iv i", dur, A_AEOL)

    violin_p = GeneratorParams(density=0.45, key_range_low=55, key_range_high=84)
    violin = ViolinGenerator(violin_p, articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.8)
    violin_notes = _clamp(violin.render(chords, A_AEOL, dur), 35, 80)
    for n in violin_notes:
        _expr_swell(n, min(n.duration, 5.0), peak_ratio=0.55)

    harp_p = GeneratorParams(density=0.35, key_range_low=36, key_range_high=76)
    harp = HarpGenerator(harp_p, pattern="arpeggio", direction="down", spread_speed=0.12)
    harp_notes = _clamp(harp.render(chords, A_AEOL, dur), 25, 55)

    pedal_p = GeneratorParams(density=0.25, key_range_low=24, key_range_high=36)
    pedal = PedalBassGenerator(pedal_p, pedal_note="root", sustain=2.0, velocity_level=0.4)
    pedal_notes = _clamp(pedal.render(chords, A_AEOL, dur), 25, 45)

    cello_p = GeneratorParams(density=0.3, key_range_low=36, key_range_high=56)
    cello = CelloGenerator(cello_p, articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=1.0)
    cello_notes = _clamp(cello.render(chords, A_AEOL, dur), 25, 55)

    return {
        "Violins": violin_notes, "Harp": harp_notes, "Pedal": pedal_notes,
        "Cello": cello_notes,
    }, 40.0


def track_07_knight():
    """VII. The Black Knight (E Phrygian Dominant, 58 BPM)
    Brass, timpani, snare, orchestral hits. A warrior's theme."""
    print("  VII. The Black Knight")
    dur = 64.0
    chords = _build_chords("i bII V i bVI iv bII V i iv bVI V i", dur, E_PHRYG_DOM)

    brass_p = GeneratorParams(density=0.55, key_range_low=36, key_range_high=72)
    brass = BrassSectionGenerator(brass_p, articulation="sustained", voicing="closed", divisi_count=4)
    brass_notes = _clamp(brass.render(chords, E_PHRYG_DOM, dur), 45, 90)

    timp_p = GeneratorParams(density=0.5)
    timp = TimpaniGenerator(timp_p, stroke_pattern="single", drum_count=5)
    timp_notes = _clamp(timp.render(chords, E_PHRYG_DOM, dur), 45, 80)

    snare_p = GeneratorParams(density=0.45)
    snare = SnareDrumGenerator(snare_p, pattern_type="march")
    snare_notes = _clamp(snare.render(chords, E_PHRYG_DOM, dur), 40, 75)

    hit_p = GeneratorParams(density=0.25, key_range_low=36, key_range_high=72)
    hit = OrchestralHitGenerator(hit_p, hit_type="staccato", voicing="chord")
    hit_notes = _clamp(hit.render(chords, E_PHRYG_DOM, dur), 50, 95)

    strings_p = GeneratorParams(density=0.45, key_range_low=40, key_range_high=72)
    strings = StringsLegatoGenerator(strings_p, ensemble_mode="section", dynamic_shape="flat")
    strings_notes = _clamp(strings.render(chords, E_PHRYG_DOM, dur), 35, 70)

    return {
        "Brass": brass_notes, "Timpani": timp_notes, "Snare": snare_notes,
        "Hit": hit_notes, "Strings": strings_notes,
    }, 58.0


# ===========================================================================
# PHASE III: THE ABYSS BECKONS — Horror, Corruption, Despair
# ===========================================================================

def track_08_abyss():
    """VIII. The Abyss Gazes Back (E Locrian, 36 BPM)
    Tension clusters, bassoon, drone. Something watches from below."""
    print("  VIII. The Abyss Gazes Back")
    dur = 92.0
    chords = _build_chords("i bII iv bvii i bv bVI bvii i bII bv i bVI bvii i", dur, E_LOC)

    tension_p = GeneratorParams(density=0.4, key_range_low=28, key_range_high=72)
    tension = TensionGenerator(tension_p, mode="semitone_cluster", note_duration=3.0, velocity_level=0.35, register="low")
    tension_notes = _clamp(tension.render(chords, E_LOC, dur), 25, 55)

    drone_p = GeneratorParams(density=0.02, key_range_low=16, key_range_high=28)
    drone = DroneGenerator(drone_p, velocity=40)
    drone_notes = _clamp(drone.render(chords, E_LOC, dur), 20, 45)

    bassoon_p = GeneratorParams(density=0.3, key_range_low=34, key_range_high=52)
    bassoon = BassoonGenerator(bassoon_p, articulation="staccato", vibrato=False, dynamic_curve="flat", note_density=1.2)
    bassoon_notes = _clamp(bassoon.render(chords, E_LOC, dur), 25, 50)

    trem_p = GeneratorParams(density=0.4, key_range_low=32, key_range_high=56)
    tremolo = TremoloStringsGenerator(trem_p, bow_speed=0.04, dynamic_swell=True)
    trem_notes = _clamp(tremolo.render(chords, E_LOC, dur), 20, 50)

    return {
        "Tension": tension_notes, "Drone": drone_notes, "Bassoon": bassoon_notes,
        "Tremolo": trem_notes,
    }, 36.0


def track_09_corruption():
    """IX. The Deep (A Double Harmonic, 48 BPM)
    Persian-scale woodwinds, choir, ostinato. Corruption seeps upward."""
    print("  IX. The Deep")
    dur = 76.0
    chords = _build_chords("i bII V i iv bVI bII V i bVI iv i V", dur, A_DBL_HARM)

    woodwinds_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=84)
    woodwinds = WoodwindsEnsembleGenerator(woodwinds_p, articulation="legato")
    woodwinds_notes = _clamp(woodwinds.render(chords, A_DBL_HARM, dur), 30, 70)

    choir_p = GeneratorParams(density=0.4, key_range_low=40, key_range_high=68)
    choir = ChoirAahsGenerator(choir_p, voice_count=6, dynamics="mp", syllable="ooh", vibrato=0.3)
    choir_notes = _clamp(choir.render(chords, A_DBL_HARM, dur), 25, 60)

    ost_p = GeneratorParams(density=0.5, key_range_low=24, key_range_high=48)
    ostinato = OstinatoGenerator(ost_p, pattern="repeated_figure", repeat_notes=3, changed_notes_count=2)
    ost_notes = _clamp(ostinato.render(chords, A_DBL_HARM, dur), 30, 55)

    pedal_p = GeneratorParams(density=0.25, key_range_low=20, key_range_high=32)
    pedal = PedalBassGenerator(pedal_p, pedal_note="root", sustain=2.0, velocity_level=0.5)
    pedal_notes = _clamp(pedal.render(chords, A_DBL_HARM, dur), 25, 45)

    return {
        "WoodwindsEns": woodwinds_notes, "Choir": choir_notes, "Ostinato": ost_notes,
        "Pedal": pedal_notes,
    }, 48.0


def track_10_descent():
    """X. Descent into Madness (E Altered, 44 BPM)
    Tension, organ, chromatic counterpoint. Losing your mind."""
    print("  X. Descent into Madness")
    dur = 72.0
    chords = _build_chords("i bII biii iv bv bvi bvii i bII bv i bvi bvii i", dur, E_ALT)

    tension_p = GeneratorParams(density=0.45, key_range_low=32, key_range_high=76)
    tension = TensionGenerator(tension_p, mode="tritone_pulse", note_duration=2.0, velocity_level=0.4, register="mid")
    tension_notes = _clamp(tension.render(chords, E_ALT, dur), 25, 55)

    organ_p = GeneratorParams(density=0.4, key_range_low=28, key_range_high=60)
    organ = OrganDrawbarsGenerator(organ_p, registration="jazz", leslie_speed="slow", percussion=True)
    organ_notes = _clamp(organ.render(chords, E_ALT, dur), 25, 55)

    cp_p = GeneratorParams(density=0.45, key_range_low=36, key_range_high=72)
    cp = CounterpointGenerator(cp_p, species=3, voices=2)
    cp_notes = _clamp(cp.render(chords, E_ALT, dur), 25, 60)

    timpani_p = GeneratorParams(density=0.25)
    timp = TimpaniGenerator(timpani_p, stroke_pattern="roll", drum_count=4)
    timp_notes = _clamp(timp.render(chords, E_ALT, dur), 30, 50)

    return {
        "Tension": tension_notes, "Organ": organ_notes, "Counterpoint": cp_notes,
        "Timpani": timp_notes,
    }, 44.0


def track_11_boss():
    """XI. The Lord of Cinder (E Harmonic Minor, 72 BPM)
    Full orchestra battle theme. Brass fanfares, choir, percussion fury."""
    print("  XI. The Lord of Cinder")
    dur = 68.0
    chords = _build_chords("i iv V i bVI bVII V i iv bVI V i bVII V i", dur, E_HARM)

    brass_p = GeneratorParams(density=0.6, key_range_low=36, key_range_high=76)
    brass = BrassSectionGenerator(brass_p, articulation="sustained", voicing="open", divisi_count=5)
    brass_notes = _clamp(brass.render(chords, E_HARM, dur), 50, 95)

    strings_p = GeneratorParams(density=0.6, key_range_low=36, key_range_high=80)
    strings = StringsLegatoGenerator(strings_p, ensemble_mode="section", dynamic_shape="flat")
    strings_notes = _clamp(strings.render(chords, E_HARM, dur), 40, 85)

    choir_p = GeneratorParams(density=0.5, key_range_low=40, key_range_high=72)
    choir = ChoirAahsGenerator(choir_p, voice_count=6, dynamics="ff", syllable="aah", vibrato=0.4)
    choir_notes = _clamp(choir.render(chords, E_HARM, dur), 40, 85)

    timp_p = GeneratorParams(density=0.5)
    timp = TimpaniGenerator(timp_p, stroke_pattern="single", drum_count=5)
    timp_notes = _clamp(timp.render(chords, E_HARM, dur), 50, 90)

    snare_p = GeneratorParams(density=0.4)
    snare = SnareDrumGenerator(snare_p, pattern_type="march")
    snare_notes = _clamp(snare.render(chords, E_HARM, dur), 45, 80)

    hit_p = GeneratorParams(density=0.3, key_range_low=36, key_range_high=76)
    hit = OrchestralHitGenerator(hit_p, hit_type="staccato", voicing="chord")
    hit_notes = _clamp(hit.render(chords, E_HARM, dur), 55, 100)

    return {
        "Brass": brass_notes, "Strings": strings_notes, "Choir": choir_notes,
        "Timpani": timp_notes, "Snare": snare_notes, "Hit": hit_notes,
    }, 72.0


# ===========================================================================
# PHASE IV: THE FIRST FLAME — Sacrifice, Resolve, Bittersweet Ending
# ===========================================================================

def track_12_silence():
    """XII. After the Battle (F Aeolian, 34 BPM)
    Solo clarinet, cello, and harp. Silence after the storm."""
    print("  XII. After the Battle")
    dur = 80.0
    chords = _build_chords("i iv i bVI bVII i iv v i bVI iv i", dur, F_AEOL)

    clarinet_p = GeneratorParams(density=0.4, key_range_low=50, key_range_high=74)
    clarinet = ClarinetGenerator(clarinet_p, articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.3)
    clarinet_notes = _clamp(clarinet.render(chords, F_AEOL, dur), 30, 70)
    for n in clarinet_notes:
        _expr_swell(n, min(n.duration, 5.0), peak_ratio=0.55)

    cello_p = GeneratorParams(density=0.35, key_range_low=36, key_range_high=56)
    cello = CelloGenerator(cello_p, articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=1.2)
    cello_notes = _clamp(cello.render(chords, F_AEOL, dur), 30, 65)

    harp_p = GeneratorParams(density=0.3, key_range_low=36, key_range_high=76)
    harp = HarpGenerator(harp_p, pattern="arpeggio", direction="up", spread_speed=0.18)
    harp_notes = _clamp(harp.render(chords, F_AEOL, dur), 25, 50)

    return {
        "Clarinet": clarinet_notes, "Cello": cello_notes, "Harp": harp_notes,
    }, 34.0


def track_13_flame():
    """XIII. The First Flame (D Harmonic Minor → D Dorian, 46 BPM)
    Canon builds from solo violin to full orchestra. The flame is linked."""
    print("  XIII. The First Flame")
    dur = 88.0
    # First half: dark, second half: hopeful mode shift
    half = dur / 2.0
    dark_chords = _build_chords("i iv V i bVI bVII i iv V", half, D_HARM)
    light_chords = _build_chords("i IV V I ii IV V I", half, D_DOR)
    chords = dark_chords + light_chords

    canon_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=84)
    canon = CanonGenerator(canon_p, canon_type="tonal", delay_beats=4.0, interval=4, num_followers=3)
    canon_notes = _clamp(canon.render(chords, D_HARM, dur), 35, 80)

    strings_p = GeneratorParams(density=0.5, key_range_low=40, key_range_high=76)
    strings = StringsLegatoGenerator(strings_p, ensemble_mode="section", dynamic_shape="crescendo")
    strings_notes = _clamp(strings.render(chords, D_HARM, dur), 25, 75)

    horn_p = GeneratorParams(density=0.4, key_range_low=36, key_range_high=65)
    horn = FrenchHornGenerator(horn_p, articulation="sustained", dynamic_curve="crescendo", note_density=1.8)
    horn_notes = _clamp(horn.render(chords, D_HARM, dur), 30, 75)

    harp_p = GeneratorParams(density=0.4, key_range_low=36, key_range_high=80)
    harp = HarpGenerator(harp_p, pattern="arpeggio", direction="up", spread_speed=0.1)
    harp_notes = _clamp(harp.render(chords, D_HARM, dur), 25, 60)

    tuba_p = GeneratorParams(density=0.3, key_range_low=24, key_range_high=40)
    tuba = TubaGenerator(tuba_p, articulation="sustained")
    tuba_notes = _clamp(tuba.render(chords, D_HARM, dur), 25, 55)

    return {
        "Canon": canon_notes, "Strings": strings_notes, "Horns": horn_notes,
        "Harp": harp_notes, "Tuba": tuba_notes,
    }, 46.0


def track_14_epilogue():
    """XIV. Nameless Song (Bb Aeolian, 36 BPM)
    Chorale, tubular bells, fading choir. The world goes dark.
    Named after the iconic Dark Souls track."""
    print("  XIV. Nameless Song")
    dur = 96.0
    chords = _build_chords("i iv i bVI bVII i III iv v i bVI iv i bVII i", dur, BB_AEOL)

    chorale_p = GeneratorParams(density=0.45, key_range_low=36, key_range_high=76)
    chorale = ChoraleGenerator(chorale_p, voice_spacing=14, soprano_motion="stepwise", rhythmic_unit=2.5)
    chorale_notes = _clamp(chorale.render(chords, BB_AEOL, dur), 30, 65)

    bell_p = GeneratorParams(density=0.2, key_range_low=60, key_range_high=84)
    bells = TubularBellsGenerator(bell_p, stroke_pattern="chime")
    bell_notes = _clamp(bells.render(chords, BB_AEOL, dur), 35, 65)

    choir_p = GeneratorParams(density=0.35, key_range_low=40, key_range_high=68)
    choir = ChoirAahsGenerator(choir_p, voice_count=4, dynamics="pp", syllable="aah", vibrato=0.15)
    choir_notes = _clamp(choir.render(chords, BB_AEOL, dur), 20, 50)

    violin_p = GeneratorParams(density=0.3, key_range_low=55, key_range_high=84)
    violin = ViolinGenerator(violin_p, articulation="sustained", vibrato=True, dynamic_curve="decrescendo", note_density=1.0)
    violin_notes = _clamp(violin.render(chords, BB_AEOL, dur), 25, 60)
    for n in violin_notes:
        _expr_swell(n, min(n.duration, 6.0), peak_ratio=0.4)

    drone_p = GeneratorParams(density=0.02, key_range_low=22, key_range_high=34)
    drone = DroneGenerator(drone_p, velocity=35)
    drone_notes = _clamp(drone.render(chords, BB_AEOL, dur), 20, 40)

    return {
        "Chorale": chorale_notes, "Bells": bell_notes, "Choir": choir_notes,
        "Violins": violin_notes, "Drone": drone_notes,
    }, 36.0


# ===========================================================================
# Track registry
# ===========================================================================

TRACKS = [
    # Phase I: The Undead Asylum
    (track_01_ashes,       "01_Ashes_Remain.mid", {
        "Cello": 42, "Drone": 43, "Bassoon": 70,
    }),
    (track_02_hollow,      "02_Hollow_Steps.mid", {
        "Pizzicato": 45, "Timpani": 47, "Viola": 41, "Pedal": 43,
    }),
    (track_03_bonfire,     "03_Bonfires_Memory.mid", {
        "Harp": 46, "Oboe": 68, "Strings": 48, "Flute": 73,
    }),
    # Phase II: The Fallen Kingdom
    (track_04_ruins,       "04_Anor_Londo_in_Ruin.mid", {
        "Chorale": 48, "Ostinato": 43, "Choir": 52, "Horns": 60,
    }),
    (track_05_hollows_march, "05_March_of_the_Hollows.mid", {
        "Snare": 115, "Trombone": 57, "Tremolo": 44, "Tuba": 58, "Timpani": 47,
    }),
    (track_06_fading_glory, "06_Fading_Glory.mid", {
        "Violins": 40, "Harp": 46, "Pedal": 43, "Cello": 42,
    }),
    (track_07_knight,      "07_The_Black_Knight.mid", {
        "Brass": 61, "Timpani": 47, "Snare": 115, "Hit": 55, "Strings": 48,
    }),
    # Phase III: The Abyss Beckons
    (track_08_abyss,       "08_The_Abyss_Gazes_Back.mid", {
        "Tension": 99, "Drone": 43, "Bassoon": 70, "Tremolo": 44,
    }),
    (track_09_corruption,  "09_The_Deep.mid", {
        "WoodwindsEns": 68, "Choir": 52, "Ostinato": 43, "Pedal": 43,
    }),
    (track_10_descent,     "10_Descent_into_Madness.mid", {
        "Tension": 99, "Organ": 19, "Counterpoint": 40, "Timpani": 47,
    }),
    (track_11_boss,        "11_The_Lord_of_Cinder.mid", {
        "Brass": 61, "Strings": 48, "Choir": 52, "Timpani": 47,
        "Snare": 115, "Hit": 55,
    }),
    # Phase IV: The First Flame
    (track_12_silence,     "12_After_the_Battle.mid", {
        "Clarinet": 71, "Cello": 42, "Harp": 46,
    }),
    (track_13_flame,       "13_The_First_Flame.mid", {
        "Canon": 40, "Strings": 48, "Horns": 60, "Harp": 46, "Tuba": 58,
    }),
    (track_14_epilogue,    "14_Nameless_Song.mid", {
        "Chorale": 48, "Bells": 14, "Choir": 52, "Violins": 40, "Drone": 43,
    }),
]


def main():
    album_dir = Path("output/album_dark_age")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("      D A R K   A G E :   A S H E S   O F   T H E   F O R G O T T E N")
    print("      A Dark Orchestral Suite in 14 Movements (~50 min)")
    print("      Phase I: The Undead Asylum | Phase II: The Fallen Kingdom")
    print("      Phase III: The Abyss Beckons | Phase IV: The First Flame")
    print("=" * 80)

    total_notes = 0
    for i, (producer, filename, instruments) in enumerate(TRACKS):
        print("-" * 80)
        raw, bpm = producer()
        mastered, pan = apply_dark_age_mix(raw, bpm)
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
    print(f"  COMPLETE: Dark Age — Ashes of the Forgotten")
    print(f"  {total_notes} total notes across 14 movements")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
