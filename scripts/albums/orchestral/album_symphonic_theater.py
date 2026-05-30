# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_symphonic_theater.py — "ТЕАТР ТЕНЕЙ И СВЕТА" (Theater of Shadow & Light)

A 12-movement symphonic theater suite (~42 min) in four acts:
    Act I:  The Stage Awakens  (Prologue, entrance, opening scene)
    Act II: Passion & Conflict (Love duet, villain aria, confrontation)
    Act III: Darkness & Despair (Crisis, lament, storm)
    Act IV: Dawn & Redemption  (Resolution, reprise, grand finale)

Full orchestral instrumentation: strings (solo + section), brass (solo + section),
woodwinds (solo + ensemble), percussion (timpani, mallet, snare, bells),
plus choir, harp, organ, and specialty generators (chorale, canon, ostinato, etc.).

Modes: MAJOR, HARMONIC_MINOR, DORIAN, PHRYGIAN, LYDIAN, MIXOLYDIAN,
       PHRYGIAN_DOMINANT, HUNGARIAN_MINOR, AEOLIAN
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
from melodica.generators.victory_fanfare import VictoryFanfareGenerator
from melodica.generators.waltz import WaltzGenerator
from melodica.generators.chorale import ChoraleGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.canon import CanonGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator

from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# ---------------------------------------------------------------------------
# Scales
# ---------------------------------------------------------------------------

C_MAJOR      = Scale(root=0,  mode=Mode.IONIAN)
D_MAJOR      = Scale(root=2,  mode=Mode.IONIAN)
EB_MAJOR     = Scale(root=3,  mode=Mode.IONIAN)
G_MAJOR      = Scale(root=7,  mode=Mode.IONIAN)
B_MAJOR      = Scale(root=11, mode=Mode.IONIAN)

A_MINOR      = Scale(root=9,  mode=Mode.AEOLIAN)
B_MINOR      = Scale(root=11, mode=Mode.AEOLIAN)
C_MINOR      = Scale(root=0,  mode=Mode.AEOLIAN)
D_MINOR      = Scale(root=2,  mode=Mode.AEOLIAN)
E_MINOR      = Scale(root=4,  mode=Mode.AEOLIAN)
F_MINOR      = Scale(root=5,  mode=Mode.AEOLIAN)
FS_MINOR     = Scale(root=6,  mode=Mode.AEOLIAN)
CS_MINOR     = Scale(root=1,  mode=Mode.AEOLIAN)

A_HARM       = Scale(root=9,  mode=Mode.HARMONIC_MINOR)
D_HARM       = Scale(root=2,  mode=Mode.HARMONIC_MINOR)
E_HARM       = Scale(root=4,  mode=Mode.HARMONIC_MINOR)
G_HARM       = Scale(root=7,  mode=Mode.HARMONIC_MINOR)

D_DORIAN     = Scale(root=2,  mode=Mode.DORIAN)
E_PHRYGIAN   = Scale(root=4,  mode=Mode.PHRYGIAN)
F_LYDIAN     = Scale(root=5,  mode=Mode.LYDIAN)
G_MIXO       = Scale(root=7,  mode=Mode.MIXOLYDIAN)
A_PHRYG_DOM  = Scale(root=9,  mode=Mode.PHRYGIAN_DOMINANT)
E_HUNGARIAN  = Scale(root=4,  mode=Mode.HUNGARIAN_MINOR)


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


def apply_theater_mix(raw_tracks: dict, bpm: float, lufs: float = -14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Violins": 0.82, "Viola": 0.80, "Cello": 0.84, "Bass": 0.88,
        "Brass": 0.78, "Horns": 0.80, "Trumpet": 0.76, "Trombone": 0.78,
        "Tuba": 0.85, "Woodwinds": 0.82, "Flute": 0.80, "Oboe": 0.78,
        "Clarinet": 0.80, "Bassoon": 0.82, "Choir": 0.85, "Organ": 0.75,
        "Harp": 0.88, "Timpani": 0.90, "Mallet": 0.82, "Bells": 0.86,
        "Snare": 0.65, "Tremolo": 0.80, "Pizzicato": 0.78, "Pedal": 0.85,
        "Drone": 0.70, "Ostinato": 0.80, "Tension": 0.72, "Waltz": 0.82,
        "Chorale": 0.82, "Counterpoint": 0.80, "Canon": 0.80, "Hit": 0.85,
        "Fanfare": 0.82, "Strings": 0.84,
    })
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan


# ===========================================================================
# ACT I: THE STAGE AWAKENS
# ===========================================================================

def track_01_prologue():
    """I. Prologue — Curtain Rises (D Major, 52 BPM)
    Solo oboe over harp arpeggios and soft strings. The theater awakens."""
    print("  I. Prologue — Curtain Rises")
    dur = 72.0
    chords = _build_chords("I IV vi V I iii IV V I vi ii V I", dur, D_MAJOR)

    oboe_p = GeneratorParams(density=0.6, key_range_low=58, key_range_high=84)
    oboe = OboeGenerator(oboe_p, articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=2.0)
    oboe_notes = _clamp(oboe.render(chords, D_MAJOR, dur), 40, 90)

    harp_p = GeneratorParams(density=0.5, key_range_low=40, key_range_high=84)
    harp = HarpGenerator(harp_p, pattern="arpeggio", direction="up", spread_speed=0.1)
    harp_notes = _clamp(harp.render(chords, D_MAJOR, dur), 35, 70)

    strings_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=76)
    strings = StringsLegatoGenerator(strings_p, ensemble_mode="section", dynamic_shape="crescendo")
    strings_notes = _clamp(strings.render(chords, D_MAJOR, dur), 30, 80)

    horn_p = GeneratorParams(density=0.4, key_range_low=40, key_range_high=65)
    horn = FrenchHornGenerator(horn_p, articulation="sustained", dynamic_curve="crescendo", note_density=2.0)
    horn_notes = _clamp(horn.render(chords, D_MAJOR, dur), 35, 75)

    timp_p = GeneratorParams(density=0.3)
    timp = TimpaniGenerator(timp_p, stroke_pattern="single", drum_count=4)
    timp_notes = _clamp(timp.render(chords, D_MAJOR, dur), 40, 65)

    return {
        "Oboe": oboe_notes, "Harp": harp_notes, "Strings": strings_notes,
        "Horns": horn_notes, "Timpani": timp_notes,
    }, 52.0


def track_02_entrance():
    """II. Entrance March — The Cast Arrives (G Mixolydian, 66 BPM)
    Waltz rhythm with woodwinds, trumpet calls, and pizzicato strings."""
    print("  II. Entrance March — The Cast Arrives")
    dur = 60.0
    chords = _build_chords("I IV vii iii IV I V IV I", dur, G_MIXO)

    waltz_p = GeneratorParams(density=0.5, key_range_low=36, key_range_high=72)
    waltz = WaltzGenerator(waltz_p, variant="viennese")
    waltz_notes = _clamp(waltz.render(chords, G_MIXO, dur), 35, 75)

    flute_p = GeneratorParams(density=0.65, key_range_low=60, key_range_high=96)
    flute = FluteGenerator(flute_p, articulation="staccato", vibrato=True, dynamic_curve="flat", note_density=3.0)
    flute_notes = _clamp(flute.render(chords, G_MIXO, dur), 45, 85)

    trp_p = GeneratorParams(density=0.5, key_range_low=55, key_range_high=82)
    trumpet = TrumpetGenerator(trp_p, articulation="sustained", fanfare_mode=True, dynamic_curve="flat", note_density=2.5)
    trumpet_notes = _clamp(trumpet.render(chords, G_MIXO, dur), 45, 90)

    pizz_p = GeneratorParams(density=0.5, key_range_low=36, key_range_high=60)
    pizz = StringsPizzicatoGenerator(pizz_p, pattern="ostinato", staccato_length=0.12)
    pizz_notes = _clamp(pizz.render(chords, G_MIXO, dur), 40, 70)

    mallet_p = GeneratorParams(density=0.35, key_range_low=72, key_range_high=96)
    mallet = MalletPercussionGenerator(mallet_p, instrument="glockenspiel", pattern="arpeggio")
    mallet_notes = _clamp(mallet.render(chords, G_MIXO, dur), 40, 65)

    return {
        "Waltz": waltz_notes, "Flute": flute_notes, "Trumpet": trumpet_notes,
        "Pizzicato": pizz_notes, "Mallet": mallet_notes,
    }, 66.0


def track_03_opening_scene():
    """III. Opening Scene — The Story Begins (D Dorian, 58 BPM)
    Chorale with organ, cello solo, and pedal bass."""
    print("  III. Opening Scene — The Story Begins")
    dur = 68.0
    chords = _build_chords("i IV i V i III VII iv i", dur, D_DORIAN)

    chorale_p = GeneratorParams(density=0.5, key_range_low=36, key_range_high=84)
    chorale = ChoraleGenerator(chorale_p, voice_spacing=12, soprano_motion="stepwise", rhythmic_unit=2.0)
    chorale_notes = _clamp(chorale.render(chords, D_DORIAN, dur), 40, 80)

    cello_p = GeneratorParams(density=0.55, key_range_low=36, key_range_high=60)
    cello = CelloGenerator(cello_p, articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=2.2)
    cello_notes = _clamp(cello.render(chords, D_DORIAN, dur), 35, 80)
    for n in cello_notes:
        _expr_swell(n, min(n.duration, 4.0))

    pedal_p = GeneratorParams(density=0.3, key_range_low=28, key_range_high=40)
    pedal = PedalBassGenerator(pedal_p, pedal_note="root", sustain=2.0, velocity_level=0.5)
    pedal_notes = _clamp(pedal.render(chords, D_DORIAN, dur), 30, 55)

    organ_p = GeneratorParams(density=0.4, key_range_low=36, key_range_high=60)
    organ = OrganDrawbarsGenerator(organ_p, registration="gospel", leslie_speed="slow", percussion=False)
    organ_notes = _clamp(organ.render(chords, D_DORIAN, dur), 30, 60)

    return {
        "Chorale": chorale_notes, "Cello": cello_notes, "Pedal": pedal_notes,
        "Organ": organ_notes,
    }, 58.0


# ===========================================================================
# ACT II: PASSION & CONFLICT
# ===========================================================================

def track_04_love_duet():
    """IV. Love Duet — Two Hearts (F Lydian, 48 BPM)
    Violin and flute in canon, harp glissandi, gentle strings."""
    print("  IV. Love Duet — Two Hearts")
    dur = 72.0
    chords = _build_chords("I II IV V I vi II V I IV V I", dur, F_LYDIAN)

    canon_p = GeneratorParams(density=0.6, key_range_low=55, key_range_high=96)
    canon = CanonGenerator(canon_p, canon_type="tonal", delay_beats=4.0, interval=4, num_followers=2)
    canon_notes = _clamp(canon.render(chords, F_LYDIAN, dur), 40, 85)

    harp_p = GeneratorParams(density=0.45, key_range_low=36, key_range_high=84)
    harp = HarpGenerator(harp_p, pattern="glissando", direction="up", spread_speed=0.08)
    harp_notes = _clamp(harp.render(chords, F_LYDIAN, dur), 30, 65)

    strings_p = GeneratorParams(density=0.5, key_range_low=44, key_range_high=68)
    strings = StringsLegatoGenerator(strings_p, ensemble_mode="section", dynamic_shape="crescendo")
    strings_notes = _clamp(strings.render(chords, F_LYDIAN, dur), 30, 70)

    clar_p = GeneratorParams(density=0.4, key_range_low=50, key_range_high=79)
    clarinet = ClarinetGenerator(clar_p, articulation="legato", vibrato=True, dynamic_curve="crescendo", note_density=2.0)
    clar_notes = _clamp(clarinet.render(chords, F_LYDIAN, dur), 35, 75)

    return {
        "Canon": canon_notes, "Harp": harp_notes, "Strings": strings_notes,
        "Clarinet": clar_notes,
    }, 48.0


def track_05_villain_aria():
    """V. Villain Aria — The Shadow Speaks (A Phrygian Dominant, 54 BPM)
    Hungarian mode darkness: organ drone, trombone, snare march, choir."""
    print("  V. Villain Aria — The Shadow Speaks")
    dur = 64.0
    chords = _build_chords("i bII v i bII VII i v i", dur, A_PHRYG_DOM)

    trombone_p = GeneratorParams(density=0.5, key_range_low=40, key_range_high=65)
    trombone = TromboneGenerator(trombone_p, articulation="sustained", dynamic_curve="flat", note_density=2.0)
    trombone_notes = _clamp(trombone.render(chords, A_PHRYG_DOM, dur), 45, 90)

    organ_p = GeneratorParams(density=0.45, key_range_low=24, key_range_high=48)
    organ = OrganDrawbarsGenerator(organ_p, registration="rock", leslie_speed="slow", percussion=True)
    organ_notes = _clamp(organ.render(chords, A_PHRYG_DOM, dur), 35, 65)

    choir_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=76)
    choir = ChoirAahsGenerator(choir_p, voice_count=4, dynamics="mf", syllable="aah", vibrato=0.3)
    choir_notes = _clamp(choir.render(chords, A_PHRYG_DOM, dur), 35, 75)

    snare_p = GeneratorParams(density=0.35)
    snare = SnareDrumGenerator(snare_p, pattern_type="march")
    snare_notes = _clamp(snare.render(chords, A_PHRYG_DOM, dur), 30, 55)

    tuba_p = GeneratorParams(density=0.4, key_range_low=29, key_range_high=45)
    tuba = TubaGenerator(tuba_p, articulation="walking")
    tuba_notes = _clamp(tuba.render(chords, A_PHRYG_DOM, dur), 40, 70)

    return {
        "Trombone": trombone_notes, "Organ": organ_notes, "Choir": choir_notes,
        "Snare": snare_notes, "Tuba": tuba_notes,
    }, 54.0


def track_06_confrontation():
    """VI. Confrontation — Swords Cross (E Hungarian Minor, 78 BPM)
    Canon fugue with brass section, timpani rolls, ostinato strings."""
    print("  VI. Confrontation — Swords Cross")
    dur = 56.0
    chords = _build_chords("i IV V i i IV V i", dur, E_HUNGARIAN)

    fugue_p = GeneratorParams(density=0.6, key_range_low=40, key_range_high=84)
    fugue = CanonGenerator(fugue_p, canon_type="fugue", delay_beats=3.0, interval=7,
                           num_followers=2, subject_length=4.0, augmentation=2.0)
    fugue_notes = _clamp(fugue.render(chords, E_HUNGARIAN, dur), 40, 85)

    brass_p = GeneratorParams(density=0.55, key_range_low=40, key_range_high=72)
    brass = BrassSectionGenerator(brass_p, articulation="fanfare", intensity=0.8, divisi_count=4)
    brass_notes = _clamp(brass.render(chords, E_HUNGARIAN, dur), 45, 95)

    ost_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=72)
    ost = OstinatoGenerator(ost_p, repeat_notes=2, insert_root_every=2)
    ost_notes = _clamp(ost.render(chords, E_HUNGARIAN, dur), 40, 75)

    timp_p = GeneratorParams(density=0.4)
    timp = TimpaniGenerator(timp_p, stroke_pattern="roll", drum_count=5)
    timp_notes = _clamp(timp.render(chords, E_HUNGARIAN, dur), 50, 85)

    hit_p = GeneratorParams(density=0.35, key_range_low=36, key_range_high=72)
    hit = OrchestralHitGenerator(hit_p, hit_type="braam", voicing="chord", duration=0.6)
    hit_notes = _clamp(hit.render(chords, E_HUNGARIAN, dur), 60, 115)

    return {
        "Canon": fugue_notes, "Brass": brass_notes, "Ostinato": ost_notes,
        "Timpani": timp_notes, "Hit": hit_notes,
    }, 78.0


# ===========================================================================
# ACT III: DARKNESS & DESPAIR
# ===========================================================================

def track_07_crisis():
    """VII. Crisis — Everything Collapses (G Harmonic Minor, 42 BPM)
    Tension clusters, tremolo strings, ominous bassoon, distant bells."""
    print("  VII. Crisis — Everything Collapses")
    dur = 64.0
    chords = _build_chords("i iv V i bII VII v i", dur, G_HARM)

    tens_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    tension = TensionGenerator(tens_p, mode="chromatic_rise", note_duration=2.0, velocity_level=0.5)
    tens_notes = _clamp(tension.render(chords, G_HARM, dur), 30, 75)

    trem_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    trem = TremoloStringsGenerator(trem_p, bow_speed=0.04, dynamic_swell=True, attack_time=2.0, decay_time=2.0)
    trem_notes = _clamp(trem.render(chords, G_HARM, dur), 25, 65)

    bsn_p = GeneratorParams(density=0.45, key_range_low=34, key_range_high=58)
    bassoon = BassoonGenerator(bsn_p, articulation="legato", dynamic_curve="flat", breath_phrase=True, note_density=2.2)
    bsn_notes = _clamp(bassoon.render(chords, G_HARM, dur), 30, 65)

    drone_p = GeneratorParams(density=0.3, key_range_low=24, key_range_high=36)
    drone = DroneGenerator(drone_p, variant="tonic", fade_in=4.0, fade_out=4.0)
    drone_notes = _clamp(drone.render(chords, G_HARM, dur), 25, 45)

    bells_p = GeneratorParams(density=0.12, key_range_low=60, key_range_high=79)
    bells = TubularBellsGenerator(bells_p, stroke_pattern="chime", dampen=True)
    bells_notes = _clamp(bells.render(chords, G_HARM, dur), 35, 55)

    return {
        "Tension": tens_notes, "Tremolo": trem_notes, "Bassoon": bsn_notes,
        "Drone": drone_notes, "Bells": bells_notes,
    }, 42.0


def track_08_lament():
    """VIII. Lament — The Fallen (C# Minor, 36 BPM)
    Choir of the fallen over tremolo, solo viola, organ."""
    print("  VIII. Lament — The Fallen")
    dur = 72.0
    chords = _build_chords("i iv v i VI iv V i", dur, CS_MINOR)

    choir_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=76)
    choir = ChoirAahsGenerator(choir_p, voice_count=4, dynamics="pp", syllable="aah", vibrato=0.4)
    choir_notes = _clamp(choir.render(chords, CS_MINOR, dur), 30, 60)
    for n in choir_notes:
        n.expression[11] = int(40 + 20 * math.sin(n.start / dur * math.pi))

    viola_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    viola = ViolaGenerator(viola_p, articulation="sustained", vibrato=True, con_sordino=True, note_density=2.0)
    viola_notes = _clamp(viola.render(chords, CS_MINOR, dur), 30, 65)
    for n in viola_notes:
        _expr_swell(n, min(n.duration, 4.0))

    trem_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    trem = TremoloStringsGenerator(trem_p, bow_speed=0.05, dynamic_swell=True)
    trem_notes = _clamp(trem.render(chords, CS_MINOR, dur), 25, 55)

    organ_p = GeneratorParams(density=0.35, key_range_low=24, key_range_high=48)
    organ = OrganDrawbarsGenerator(organ_p, registration="gospel", leslie_speed="slow", percussion=False)
    organ_notes = _clamp(organ.render(chords, CS_MINOR, dur), 25, 50)

    return {
        "Choir": choir_notes, "Viola": viola_notes, "Tremolo": trem_notes,
        "Organ": organ_notes,
    }, 36.0


def track_09_storm():
    """IX. The Storm — Nature Unleashed (E Phrygian, 88 BPM)
    Full orchestra: brass fanfare, timpani thunder, woodwind fury, orchestral hits."""
    print("  IX. The Storm — Nature Unleashed")
    dur = 52.0
    chords = _build_chords("i bII v i bII VII v i bII v i", dur, E_PHRYGIAN)

    brass_p = GeneratorParams(density=0.6, key_range_low=40, key_range_high=72)
    brass = BrassSectionGenerator(brass_p, articulation="fanfare", intensity=0.9, divisi_count=5)
    brass_notes = _clamp(brass.render(chords, E_PHRYGIAN, dur), 55, 110)

    ww_p = GeneratorParams(density=0.55, key_range_low=50, key_range_high=84)
    ww = WoodwindsEnsembleGenerator(ww_p, section="quartet", articulation="staccato")
    ww_notes = _clamp(ww.render(chords, E_PHRYGIAN, dur), 45, 95)

    timp_p = GeneratorParams(density=0.5)
    timp = TimpaniGenerator(timp_p, stroke_pattern="roll", drum_count=5, roll_speed=0.0625)
    timp_notes = _clamp(timp.render(chords, E_PHRYGIAN, dur), 55, 100)

    snare_p = GeneratorParams(density=0.45)
    snare = SnareDrumGenerator(snare_p, pattern_type="roll")
    snare_notes = _clamp(snare.render(chords, E_PHRYGIAN, dur), 40, 80)

    hit_p = GeneratorParams(density=0.4, key_range_low=36, key_range_high=72)
    hit = OrchestralHitGenerator(hit_p, hit_type="braam", voicing="chord", duration=0.8)
    hit_notes = _clamp(hit.render(chords, E_PHRYGIAN, dur), 60, 120)

    bass_p = GeneratorParams(density=0.4, key_range_low=28, key_range_high=43)
    bass = ContrabassGenerator(bass_p, articulation="pizzicato", dynamic_curve="flat", note_density=2.0)
    bass_notes = _clamp(bass.render(chords, E_PHRYGIAN, dur), 50, 85)

    return {
        "Brass": brass_notes, "Woodwinds": ww_notes, "Timpani": timp_notes,
        "Snare": snare_notes, "Hit": hit_notes, "Bass": bass_notes,
    }, 88.0


# ===========================================================================
# ACT IV: DAWN & REDEMPTION
# ===========================================================================

def track_10_dawn():
    """X. Dawn — Light Returns (C Major, 46 BPM)
    Violin solo over harp, soft strings emerge from silence."""
    print("  X. Dawn — Light Returns")
    dur = 68.0

    # Mode shift: first half C minor (darkness), second half C major (light)
    minor_dur = dur / 2
    major_dur = dur / 2
    minor_chords = _build_chords("i iv V i", minor_dur, C_MINOR)
    major_chords = _build_chords("I IV V I", major_dur, C_MAJOR)

    v_p = GeneratorParams(density=0.6, key_range_low=55, key_range_high=96)
    violin = ViolinGenerator(v_p, articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=2.5)
    v_minor = _clamp(violin.render(minor_chords, C_MINOR, minor_dur), 30, 75)
    v_major = _clamp(violin.render(major_chords, C_MAJOR, major_dur), 50, 95)
    for n in v_major:
        n.start += minor_dur

    harp_p = GeneratorParams(density=0.45, key_range_low=36, key_range_high=84)
    harp = HarpGenerator(harp_p, pattern="glissando", direction="up", spread_speed=0.08)
    harp_notes = _clamp(harp.render(major_chords, C_MAJOR, major_dur), 30, 65)
    for n in harp_notes:
        n.start += minor_dur

    str_p = GeneratorParams(density=0.5, key_range_low=36, key_range_high=84)
    strings = StringsLegatoGenerator(str_p, ensemble_mode="section", dynamic_shape="crescendo")
    s_minor = _clamp(strings.render(minor_chords, C_MINOR, minor_dur), 25, 60)
    s_major = _clamp(strings.render(major_chords, C_MAJOR, major_dur), 40, 80)
    for n in s_major:
        n.start += minor_dur

    horn_p = GeneratorParams(density=0.35, key_range_low=34, key_range_high=60)
    horn = FrenchHornGenerator(horn_p, articulation="sustained", dynamic_curve="crescendo", con_sordino=True, note_density=2.0)
    horn_notes = _clamp(horn.render(major_chords, C_MAJOR, major_dur), 35, 70)
    for n in horn_notes:
        n.start += minor_dur

    return {
        "Violins": v_minor + v_major, "Harp": harp_notes,
        "Strings": s_minor + s_major, "Horns": horn_notes,
    }, 46.0


def track_11_reprise():
    """XI. Reprise — Love Returns (D Major, 56 BPM)
    Counterpoint of oboe and flute, warm strings, woodwinds ensemble."""
    print("  XI. Reprise — Love Returns")
    dur = 64.0
    chords = _build_chords("I IV V I vi ii V I I IV V I", dur, D_MAJOR)

    cp_p = GeneratorParams(density=0.55, key_range_low=58, key_range_high=91)
    counterpoint = CounterpointGenerator(cp_p, species=2, voices=2, cantus_position="above")
    cp_notes = _clamp(counterpoint.render(chords, D_MAJOR, dur), 35, 80)

    str_p = GeneratorParams(density=0.55, key_range_low=36, key_range_high=84)
    strings = StringsLegatoGenerator(str_p, ensemble_mode="section", dynamic_shape="crescendo")
    strings_notes = _clamp(strings.render(chords, D_MAJOR, dur), 35, 85)

    ww_p = GeneratorParams(density=0.5, key_range_low=50, key_range_high=84)
    ww = WoodwindsEnsembleGenerator(ww_p, section="quartet", articulation="legato")
    ww_notes = _clamp(ww.render(chords, D_MAJOR, dur), 35, 80)

    harp_p = GeneratorParams(density=0.4, key_range_low=36, key_range_high=84)
    harp = HarpGenerator(harp_p, pattern="arpeggio", direction="up_down", spread_speed=0.1)
    harp_notes = _clamp(harp.render(chords, D_MAJOR, dur), 30, 60)

    return {
        "Woodwinds": cp_notes, "Strings": strings_notes,
        "WoodwindsEns": ww_notes, "Harp": harp_notes,
    }, 56.0


def track_12_finale():
    """XII. Grand Finale — All Voices United (Eb Major, 60 BPM)
    Full orchestra + choir + bells. The theater celebrates."""
    print("  XII. Grand Finale — All Voices United")
    dur = 84.0
    chords = _build_chords("I IV V I vi ii V I I IV V I I IV V I", dur, EB_MAJOR)

    fanf_p = GeneratorParams(density=0.6, key_range_low=36, key_range_high=84)
    fanfare = VictoryFanfareGenerator(fanf_p, variant="victory", register=4, dynamics="forte")
    fanf_notes = _clamp(fanfare.render(chords, EB_MAJOR, dur), 55, 110)

    chorale_p = GeneratorParams(density=0.5, key_range_low=36, key_range_high=84)
    chorale = ChoraleGenerator(chorale_p, voice_spacing=12, soprano_motion="stepwise", rhythmic_unit=2.0)
    chorale_notes = _clamp(chorale.render(chords, EB_MAJOR, dur), 40, 90)

    str_p = GeneratorParams(density=0.55, key_range_low=36, key_range_high=84)
    strings = StringsLegatoGenerator(str_p, section_size="ensemble", dynamic_shape="crescendo")
    strings_notes = _clamp(strings.render(chords, EB_MAJOR, dur), 35, 90)

    brass_p = GeneratorParams(density=0.55, key_range_low=40, key_range_high=72)
    brass = BrassSectionGenerator(brass_p, articulation="fanfare", intensity=0.9, divisi_count=5)
    brass_notes = _clamp(brass.render(chords, EB_MAJOR, dur), 55, 105)

    ch_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=76)
    choir = ChoirAahsGenerator(ch_p, voice_count=4, dynamics="ff", syllable="aah", vibrato=0.3)
    choir_notes = _clamp(choir.render(chords, EB_MAJOR, dur), 45, 100)

    timp_p = GeneratorParams(density=0.4)
    timp = TimpaniGenerator(timp_p, stroke_pattern="roll", drum_count=5)
    timp_notes = _clamp(timp.render(chords, EB_MAJOR, dur), 50, 90)

    bell_p = GeneratorParams(density=0.15, key_range_low=60, key_range_high=79)
    bells = TubularBellsGenerator(bell_p, stroke_pattern="chime")
    bell_notes = _clamp(bells.render(chords, EB_MAJOR, dur), 45, 75)

    organ_p = GeneratorParams(density=0.4, key_range_low=24, key_range_high=60)
    organ = OrganDrawbarsGenerator(organ_p, registration="jazz", leslie_speed="fast")
    organ_notes = _clamp(organ.render(chords, EB_MAJOR, dur), 35, 70)

    return {
        "Fanfare": fanf_notes, "Chorale": chorale_notes, "Strings": strings_notes,
        "Brass": brass_notes, "Choir": choir_notes, "Timpani": timp_notes,
        "Bells": bell_notes, "Organ": organ_notes,
    }, 60.0


# ===========================================================================
# Main
# ===========================================================================

TRACKS = [
    (track_01_prologue,      "01_Prologue_Curtain_Rises.mid", {
        "Oboe": 68, "Harp": 46, "Strings": 48, "Horns": 60, "Timpani": 47,
    }),
    (track_02_entrance,      "02_Entrance_March.mid", {
        "Waltz": 48, "Flute": 73, "Trumpet": 56, "Pizzicato": 45, "Mallet": 9,
    }),
    (track_03_opening_scene, "03_Opening_Scene.mid", {
        "Chorale": 48, "Cello": 42, "Pedal": 38, "Organ": 19,
    }),
    (track_04_love_duet,     "04_Love_Duet.mid", {
        "Canon": 40, "Harp": 46, "Strings": 48, "Clarinet": 71,
    }),
    (track_05_villain_aria,  "05_Villain_Aria.mid", {
        "Trombone": 57, "Organ": 19, "Choir": 52, "Snare": 115, "Tuba": 58,
    }),
    (track_06_confrontation, "06_Confrontation.mid", {
        "Canon": 41, "Brass": 61, "Ostinato": 48, "Timpani": 47, "Hit": 55,
    }),
    (track_07_crisis,        "07_Crisis.mid", {
        "Tension": 48, "Tremolo": 44, "Bassoon": 70, "Drone": 38, "Bells": 14,
    }),
    (track_08_lament,        "08_Lament.mid", {
        "Choir": 52, "Viola": 41, "Tremolo": 44, "Organ": 19,
    }),
    (track_09_storm,         "09_The_Storm.mid", {
        "Brass": 61, "Woodwinds": 68, "Timpani": 47, "Snare": 115, "Hit": 55, "Bass": 43,
    }),
    (track_10_dawn,          "10_Dawn.mid", {
        "Violins": 40, "Harp": 46, "Strings": 48, "Horns": 60,
    }),
    (track_11_reprise,       "11_Reprise.mid", {
        "Woodwinds": 68, "Strings": 48, "WoodwindsEns": 68, "Harp": 46,
    }),
    (track_12_finale,        "12_Grand_Finale.mid", {
        "Fanfare": 60, "Chorale": 48, "Strings": 48, "Brass": 61,
        "Choir": 52, "Timpani": 47, "Bells": 14, "Organ": 19,
    }),
]


def main():
    album_dir = Path("output/album_symphonic_theater")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("      Т Е А Т Р   Т Е Н Е Й   И   С В Е Т А")
    print("      Theater of Shadow & Light — A Symphonic Theater Suite")
    print("      Act I: The Stage Awakens | Act II: Passion & Conflict")
    print("      Act III: Darkness & Despair | Act IV: Dawn & Redemption")
    print("=" * 80)

    total_notes = 0
    for i, (producer, filename, instruments) in enumerate(TRACKS):
        print("-" * 80)
        raw, bpm = producer()
        mastered, pan = apply_theater_mix(raw, bpm)
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
    print(f"  COMPLETE: Theater of Shadow & Light")
    print(f"  {total_notes} total notes across 12 movements")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
