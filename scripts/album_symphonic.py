# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_symphonic.py — "SYMPHONIA OBSCURA"
A 14-movement symphonic album in four parts:
    I.   Overture & Awakening     (Dawn of the orchestra)
    II.  Scherzo & Dance          (Rhythmic vitality)
    III. Adagio & Lament          (Emotional depth)
    IV.  Finale & Resolution      (Triumph and transcendence)

Uses all improved generators: individual orchestral instruments
(Violin, Viola, Cello, Contrabass, Trumpet, Trombone, FrenchHorn,
Flute, Oboe, Clarinet, Bassoon, Timpani, Mallet), plus section
generators, choir, harp, organ, tubular bells, snare, tuba, and
composition generators (chorale, counterpoint, canon).
"""

import math
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams

# Individual orchestral instruments
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

# Speciality generators
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

C_MINOR     = Scale(root=0,  mode=Mode.AEOLIAN)
D_MINOR     = Scale(root=2,  mode=Mode.AEOLIAN)
E_MINOR     = Scale(root=4,  mode=Mode.AEOLIAN)
F_MINOR     = Scale(root=5,  mode=Mode.AEOLIAN)
G_MINOR     = Scale(root=7,  mode=Mode.AEOLIAN)
A_MINOR     = Scale(root=9,  mode=Mode.AEOLIAN)
B_MINOR     = Scale(root=11, mode=Mode.AEOLIAN)
EB_MINOR    = Scale(root=3,  mode=Mode.AEOLIAN)
BB_MINOR    = Scale(root=10, mode=Mode.AEOLIAN)
FS_MINOR    = Scale(root=6,  mode=Mode.AEOLIAN)
CS_MINOR    = Scale(root=1,  mode=Mode.AEOLIAN)

C_MAJOR     = Scale(root=0,  mode=Mode.IONIAN)
D_MAJOR     = Scale(root=2,  mode=Mode.IONIAN)
EB_MAJOR    = Scale(root=3,  mode=Mode.IONIAN)
G_MAJOR     = Scale(root=7,  mode=Mode.IONIAN)
A_MAJOR     = Scale(root=9,  mode=Mode.IONIAN)
B_MAJOR     = Scale(root=11, mode=Mode.IONIAN)

# Exotic / modal
D_DORIAN     = Scale(root=2,  mode=Mode.DORIAN)
E_PHRYGIAN   = Scale(root=4,  mode=Mode.PHRYGIAN)
F_LYDIAN     = Scale(root=5,  mode=Mode.LYDIAN)
A_HARM_MINOR = Scale(root=9,  mode=Mode.HARMONIC_MINOR)
D_HARM_MINOR = Scale(root=2,  mode=Mode.HARMONIC_MINOR)
G_HARM_MINOR = Scale(root=7,  mode=Mode.HARMONIC_MINOR)
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
    """Attach CC11 expression swell (pp->f->pp) to a note."""
    peak_t = note.start + duration * peak_ratio
    note.expression[11] = [
        (round(note.start, 3), 40),
        (round(peak_t, 3), 100),
        (round(note.start + duration, 3), 30),
    ]


def apply_symphonic_mix(raw_tracks: dict, bpm: float, lufs: float = -14.0):
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
    })
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan


# ===========================================================================
# PART I: OVERTURE & AWAKENING
# ===========================================================================

def track_01_overture():
    """I. Overture — Dawn of the Orchestra (D Major, 56 BPM)"""
    print("  I. Overture — Dawn of the Orchestra")
    dur = 64.0
    chords = _build_chords("I IV V I vi ii V I I IV V I", dur, D_MAJOR)

    # Solo oboe melody — the first voice to awaken
    oboe_p = GeneratorParams(density=0.6, key_range_low=58, key_range_high=84)
    oboe = OboeGenerator(oboe_p, articulation="sustained", vibrato=True, dynamic_curve="crescendo")
    oboe_notes = _clamp(oboe.render(chords, D_MAJOR, dur), 40, 90)

    # Harp arpeggios — shimmering morning light
    harp_p = GeneratorParams(density=0.5, key_range_low=40, key_range_high=84)
    harp = HarpGenerator(harp_p, pattern="arpeggio", direction="up", spread_speed=0.1)
    harp_notes = _clamp(harp.render(chords, D_MAJOR, dur), 35, 70)

    # Strings emerge softly
    strings_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=76)
    strings = StringsLegatoGenerator(strings_p, section_size="ensemble", dynamic_shape="crescendo")
    strings_notes = _clamp(strings.render(chords, D_MAJOR, dur), 30, 80)

    # French horns — noble fanfare undertone
    horn_p = GeneratorParams(density=0.4, key_range_low=40, key_range_high=65)
    horn = FrenchHornGenerator(horn_p, articulation="sustained", dynamic_curve="crescendo")
    horn_notes = _clamp(horn.render(chords, D_MAJOR, dur), 35, 75)

    # Timpani — soft rhythmic foundation
    timp_p = GeneratorParams(density=0.3)
    timp = TimpaniGenerator(timp_p, stroke_pattern="single", drum_count=4)
    timp_notes = _clamp(timp.render(chords, D_MAJOR, dur), 40, 65)

    return {
        "Oboe": oboe_notes,
        "Harp": harp_notes,
        "Strings": strings_notes,
        "Horns": horn_notes,
        "Timpani": timp_notes,
    }, 56.0


def track_02_awakening():
    """II. Awakening — Strings Unbound (G Major, 60 BPM)"""
    print("  II. Awakening — Strings Unbound")
    dur = 56.0
    chords = _build_chords("I V vi IV I V IV I", dur, G_MAJOR)

    # Solo violin cadenza
    violin_p = GeneratorParams(density=0.7, key_range_low=55, key_range_high=96)
    violin = ViolinGenerator(violin_p, articulation="sustained", vibrato=True, dynamic_curve="crescendo")
    violin_notes = _clamp(violin.render(chords, G_MAJOR, dur), 40, 95)

    # Cello counter-melody
    cello_p = GeneratorParams(density=0.55, key_range_low=36, key_range_high=60)
    cello = CelloGenerator(cello_p, articulation="sustained", vibrato=True, dynamic_curve="crescendo")
    cello_notes = _clamp(cello.render(chords, G_MAJOR, dur), 35, 80)

    # Viola harmony
    viola_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    viola = ViolaGenerator(viola_p, articulation="sustained", vibrato=True)
    viola_notes = _clamp(viola.render(chords, G_MAJOR, dur), 35, 75)

    # Contrabass pedal
    bass_p = GeneratorParams(density=0.35, key_range_low=28, key_range_high=43)
    bass = ContrabassGenerator(bass_p, articulation="sustained", dynamic_curve="flat")
    bass_notes = _clamp(bass.render(chords, G_MAJOR, dur), 30, 60)

    return {
        "Violins": violin_notes,
        "Cello": cello_notes,
        "Viola": viola_notes,
        "Bass": bass_notes,
    }, 60.0


def track_03_procession():
    """III. Procession — Solemn March (D Dorian, 52 BPM)"""
    print("  III. Procession — Solemn March")
    dur = 60.0
    chords = _build_chords("i IV i V i IV V i", dur, D_DORIAN)

    # Chorale — four-part SATB harmony
    chorale_p = GeneratorParams(density=0.5, key_range_low=36, key_range_high=84)
    chorale = ChoraleGenerator(chorale_p, voice_spacing=12, soprano_motion="stepwise", rhythmic_unit=2.0)
    chorale_notes = _clamp(chorale.render(chords, D_DORIAN, dur), 40, 80)

    # Snare drum — muted march
    snare_p = GeneratorParams(density=0.35)
    snare = SnareDrumGenerator(snare_p, pattern_type="march")
    snare_notes = _clamp(snare.render(chords, D_DORIAN, dur), 30, 55)

    # Tuba — low brass foundation
    tuba_p = GeneratorParams(density=0.4, key_range_low=29, key_range_high=45)
    tuba = TubaGenerator(tuba_p, articulation="walking")
    tuba_notes = _clamp(tuba.render(chords, D_DORIAN, dur), 40, 70)

    # Organ — chapel resonance
    organ_p = GeneratorParams(density=0.45, key_range_low=36, key_range_high=60)
    organ = OrganDrawbarsGenerator(organ_p, registration="gospel", leslie_speed="slow", percussion=False)
    organ_notes = _clamp(organ.render(chords, D_DORIAN, dur), 30, 60)

    return {
        "Chorale": chorale_notes,
        "Snare": snare_notes,
        "Tuba": tuba_notes,
        "Organ": organ_notes,
    }, 52.0


# ===========================================================================
# PART II: SCHERZO & DANCE
# ===========================================================================

def track_04_scherzo():
    """IV. Scherzo — Woodwind Games (G Major waltz, 72 BPM)"""
    print("  IV. Scherzo — Woodwind Games")
    dur = 52.0
    chords = _build_chords("I IV V I vi ii V I", dur, G_MAJOR)

    # Waltz accompaniment
    waltz_p = GeneratorParams(density=0.5, key_range_low=36, key_range_high=72)
    waltz = WaltzGenerator(waltz_p, variant="viennese")
    waltz_notes = _clamp(waltz.render(chords, G_MAJOR, dur), 35, 75)

    # Flute — bright, dancing melody
    flute_p = GeneratorParams(density=0.65, key_range_low=60, key_range_high=96)
    flute = FluteGenerator(flute_p, articulation="staccato", vibrato=True, dynamic_curve="flat")
    flute_notes = _clamp(flute.render(chords, G_MAJOR, dur), 45, 85)

    # Clarinet — playful counter
    clar_p = GeneratorParams(density=0.55, key_range_low=50, key_range_high=79)
    clar = ClarinetGenerator(clar_p, articulation="staccato", dynamic_curve="flat")
    clar_notes = _clamp(clar.render(chords, G_MAJOR, dur), 40, 80)

    # Pizzicato strings — rhythmic bounce
    pizz_p = GeneratorParams(density=0.5, key_range_low=36, key_range_high=60)
    pizz = StringsPizzicatoGenerator(pizz_p, pattern="ostinato", staccato_length=0.12)
    pizz_notes = _clamp(pizz.render(chords, G_MAJOR, dur), 40, 70)

    return {
        "Waltz": waltz_notes,
        "Flute": flute_notes,
        "Clarinet": clar_notes,
        "Pizzicato": pizz_notes,
    }, 72.0


def track_05_dance():
    """V. Dance of Shadows — Hungarian Minor (E Hungarian, 66 BPM)"""
    print("  V. Dance of Shadows")
    dur = 56.0
    chords = _build_chords("i IV V i i IV V i", dur, E_HUNGARIAN)

    # Canon — two chasing voices
    canon_p = GeneratorParams(density=0.6, key_range_low=48, key_range_high=84)
    canon = CanonGenerator(canon_p, canon_type="tonal", delay_beats=2.0, interval=7, num_followers=2)
    canon_notes = _clamp(canon.render(chords, E_HUNGARIAN, dur), 40, 85)

    # Mallet percussion — marimba ostinato
    mallet_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    mallet = MalletPercussionGenerator(mallet_p, instrument="marimba", pattern="arpeggio", mallet_count=4)
    mallet_notes = _clamp(mallet.render(chords, E_HUNGARIAN, dur), 40, 75)

    # Contrabass — driving bass
    bass_p = GeneratorParams(density=0.45, key_range_low=28, key_range_high=45)
    bass = ContrabassGenerator(bass_p, articulation="pizzicato", dynamic_curve="flat")
    bass_notes = _clamp(bass.render(chords, E_HUNGARIAN, dur), 40, 70)

    # Timpani rolls — dramatic accents
    timp_p = GeneratorParams(density=0.35)
    timp = TimpaniGenerator(timp_p, stroke_pattern="roll", drum_count=4)
    timp_notes = _clamp(timp.render(chords, E_HUNGARIAN, dur), 45, 80)

    return {
        "Canon": canon_notes,
        "Mallet": mallet_notes,
        "Bass": bass_notes,
        "Timpani": timp_notes,
    }, 66.0


def track_06_fugue():
    """VI. Fugato — Three-Part Invention (A Minor, 63 BPM)"""
    print("  VI. Fugato — Three-Part Invention")
    dur = 64.0
    chords = _build_chords("i iv v i VI iv V i", dur, A_MINOR)

    # Fugue via CanonGenerator
    fugue_p = GeneratorParams(density=0.6, key_range_low=40, key_range_high=84)
    fugue = CanonGenerator(fugue_p, canon_type="fugue", delay_beats=3.0, interval=7,
                           num_followers=2, subject_length=4.0, augmentation=2.0)
    fugue_notes = _clamp(fugue.render(chords, A_MINOR, dur), 40, 85)

    # Pedal bass — organ point
    pedal_p = GeneratorParams(density=0.3, key_range_low=28, key_range_high=40)
    pedal = PedalBassGenerator(pedal_p, pedal_note="root", sustain=2.0, velocity_level=0.5)
    pedal_notes = _clamp(pedal.render(chords, A_MINOR, dur), 30, 55)

    return {
        "Canon": fugue_notes,
        "Pedal": pedal_notes,
    }, 63.0


def track_07_carnival():
    """VII. Carnival of Masks — Bright Phrygian (E Phrygian, 70 BPM)"""
    print("  VII. Carnival of Masks")
    dur = 52.0
    chords = _build_chords("i bII v i bII VII i v i", dur, E_PHRYGIAN)

    # Trumpet — bright fanfare calls
    trp_p = GeneratorParams(density=0.55, key_range_low=55, key_range_high=82)
    trumpet = TrumpetGenerator(trp_p, articulation="sustained", fanfare_mode=True, dynamic_curve="flat")
    trumpet_notes = _clamp(trumpet.render(chords, E_PHRYGIAN, dur), 45, 90)

    # Trombone — brassy response
    trb_p = GeneratorParams(density=0.45, key_range_low=40, key_range_high=65)
    trombone = TromboneGenerator(trb_p, articulation="sustained", dynamic_curve="flat")
    trombone_notes = _clamp(trombone.render(chords, E_PHRYGIAN, dur), 40, 80)

    # Ostinato strings
    ost_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=72)
    ost = OstinatoGenerator(ost_p, repeat_notes=2, insert_root_every=2)
    ost_notes = _clamp(ost.render(chords, E_PHRYGIAN, dur), 40, 75)

    # Snare — crisp military rolls
    snare_p = GeneratorParams(density=0.4)
    snare = SnareDrumGenerator(snare_p, pattern_type="roll")
    snare_notes = _clamp(snare.render(chords, E_PHRYGIAN, dur), 35, 65)

    # Glockenspiel — sparkling highlights
    gl_p = GeneratorParams(density=0.35, key_range_low=72, key_range_high=96)
    glock = MalletPercussionGenerator(gl_p, instrument="glockenspiel", pattern="arpeggio")
    glock_notes = _clamp(glock.render(chords, E_PHRYGIAN, dur), 40, 65)

    return {
        "Trumpet": trumpet_notes,
        "Trombone": trombone_notes,
        "Ostinato": ost_notes,
        "Snare": snare_notes,
        "Mallet": glock_notes,
    }, 70.0


# ===========================================================================
# PART III: ADAGIO & LAMENT
# ===========================================================================

def track_08_adagio():
    """VIII. Adagio — Night Over the Cathedral (F Minor, 38 BPM)"""
    print("  VIII. Adagio — Night Over the Cathedral")
    dur = 72.0
    chords = _build_chords("i iv v i VI iv V i", dur, F_MINOR)

    # Cello — singing lament
    cello_p = GeneratorParams(density=0.55, key_range_low=36, key_range_high=60)
    cello = CelloGenerator(cello_p, articulation="sustained", vibrato=True, dynamic_curve="crescendo")
    cello_notes = _clamp(cello.render(chords, F_MINOR, dur), 30, 80)
    for n in cello_notes:
        _expr_swell(n, min(n.duration, 4.0))

    # Bassoon — dark woodwind commentary
    bsn_p = GeneratorParams(density=0.45, key_range_low=34, key_range_high=58)
    bassoon = BassoonGenerator(bsn_p, articulation="legato", dynamic_curve="flat", breath_phrase=True)
    bsn_notes = _clamp(bassoon.render(chords, F_MINOR, dur), 30, 65)

    # Drone — atmospheric pedal
    drone_p = GeneratorParams(density=0.3, key_range_low=24, key_range_high=36)
    drone = DroneGenerator(drone_p, variant="tonic", fade_in=4.0, fade_out=4.0)
    drone_notes = _clamp(drone.render(chords, F_MINOR, dur), 25, 45)

    # Organ — distant chapel
    organ_p = GeneratorParams(density=0.4, key_range_low=24, key_range_high=48)
    organ = OrganDrawbarsGenerator(organ_p, registration="gospel", leslie_speed="slow", percussion=False)
    organ_notes = _clamp(organ.render(chords, F_MINOR, dur), 25, 50)

    # Bells — midnight chime
    bells_p = GeneratorParams(density=0.15, key_range_low=60, key_range_high=79)
    bells = TubularBellsGenerator(bells_p, stroke_pattern="chime", dampen=True)
    bells_notes = _clamp(bells.render(chords, F_MINOR, dur), 35, 55)

    return {
        "Cello": cello_notes,
        "Bassoon": bsn_notes,
        "Drone": drone_notes,
        "Organ": organ_notes,
        "Bells": bells_notes,
    }, 38.0


def track_09_counterpoint():
    """IX. Dialogue — Flute & Oboe Counterpoint (Bb Minor, 44 BPM)"""
    print("  IX. Dialogue — Flute & Oboe Counterpoint")
    dur = 56.0
    chords = _build_chords("i iv v i VI iv V i", dur, BB_MINOR)

    # Two-voice counterpoint: flute as cantus firmus, oboe as counterpoint
    cp_p = GeneratorParams(density=0.55, key_range_low=58, key_range_high=91)
    counterpoint = CounterpointGenerator(cp_p, species=2, voices=2, cantus_position="above")
    cp_notes = _clamp(counterpoint.render(chords, BB_MINOR, dur), 35, 75)

    # Viola — gentle harmonic support
    viola_p = GeneratorParams(density=0.4, key_range_low=48, key_range_high=68)
    viola = ViolaGenerator(viola_p, articulation="sustained", vibrato=True, con_sordino=True)
    viola_notes = _clamp(viola.render(chords, BB_MINOR, dur), 30, 55)

    return {
        "Woodwinds": cp_notes,
        "Viola": viola_notes,
    }, 44.0


def track_10_lament():
    """X. Lament — Choir of the Fallen (C# Minor, 36 BPM)"""
    print("  X. Lament — Choir of the Fallen")
    dur = 64.0
    chords = _build_chords("i iv v i VI iv V i", dur, CS_MINOR)

    # Choir — full SATB lament
    choir_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=76)
    choir = ChoirAahsGenerator(choir_p, voice_count=4, dynamics="pp", syllable="aah", vibrato=0.4)
    choir_notes = _clamp(choir.render(chords, CS_MINOR, dur), 30, 60)
    for n in choir_notes:
        n.expression[11] = int(40 + 20 * math.sin(n.start / dur * math.pi))

    # Tremolo strings — sustained tension
    trem_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    trem = TremoloStringsGenerator(trem_p, bow_speed=0.04, dynamic_swell=True, attack_time=2.0, decay_time=2.0)
    trem_notes = _clamp(trem.render(chords, CS_MINOR, dur), 25, 55)

    # French horn — mournful solo
    horn_p = GeneratorParams(density=0.4, key_range_low=34, key_range_high=60)
    horn = FrenchHornGenerator(horn_p, articulation="sustained", dynamic_curve="decrescendo", con_sordino=True)
    horn_notes = _clamp(horn.render(chords, CS_MINOR, dur), 30, 60)

    return {
        "Choir": choir_notes,
        "Tremolo": trem_notes,
        "Horns": horn_notes,
    }, 36.0


def track_11_tension():
    """XI. Gathering Storm — Tension Build (F# Minor, 48 BPM accelerating to 64)"""
    print("  XI. Gathering Storm")
    dur = 60.0
    chords = _build_chords("i iv v i bII VII v i", dur, FS_MINOR)

    # Tension cluster — ominous rising
    tens_p = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    tension = TensionGenerator(tens_p, mode="chromatic_rise", note_duration=2.0, velocity_level=0.5)
    tens_notes = _clamp(tension.render(chords, FS_MINOR, dur), 30, 75)

    # Brass section — building intensity
    brass_p = GeneratorParams(density=0.5, key_range_low=40, key_range_high=70)
    brass = BrassSectionGenerator(brass_p, articulation="swell", intensity=0.6, divisi_count=4)
    brass_notes = _clamp(brass.render(chords, FS_MINOR, dur), 35, 80)

    # Timpani — accelerating rolls
    timp_p = GeneratorParams(density=0.4)
    timp = TimpaniGenerator(timp_p, stroke_pattern="roll", drum_count=5)
    timp_notes = _clamp(timp.render(chords, FS_MINOR, dur), 40, 75)

    # Bass drum — low impacts
    tuba_p = GeneratorParams(density=0.35, key_range_low=24, key_range_high=40)
    tuba = TubaGenerator(tuba_p, articulation="staccato", growl=True)
    tuba_notes = _clamp(tuba.render(chords, FS_MINOR, dur), 40, 70)

    return {
        "Tension": tens_notes,
        "Brass": brass_notes,
        "Timpani": timp_notes,
        "Tuba": tuba_notes,
    }, 48.0


# ===========================================================================
# PART IV: FINALE & RESOLUTION
# ===========================================================================

def track_12_fanfare():
    """XII. Triumph — Brass Fanfare (Eb Major, 80 BPM)"""
    print("  XII. Triumph — Brass Fanfare")
    dur = 56.0
    chords = _build_chords("I IV V I vi ii V I", dur, EB_MAJOR)

    # Victory fanfare
    fanf_p = GeneratorParams(density=0.6, key_range_low=36, key_range_high=84)
    fanfare = VictoryFanfareGenerator(fanf_p, variant="victory", register=4, dynamics="forte")
    fanf_notes = _clamp(fanfare.render(chords, EB_MAJOR, dur), 55, 110)

    # Full brass section
    brass_p = GeneratorParams(density=0.55, key_range_low=40, key_range_high=72)
    brass = BrassSectionGenerator(brass_p, articulation="fanfare", intensity=0.9, divisi_count=5)
    brass_notes = _clamp(brass.render(chords, EB_MAJOR, dur), 55, 105)

    # Orchestral hit — power impacts
    hit_p = GeneratorParams(density=0.4, key_range_low=36, key_range_high=72)
    hit = OrchestralHitGenerator(hit_p, hit_type="braam", voicing="chord", duration=0.8)
    hit_notes = _clamp(hit.render(chords, EB_MAJOR, dur), 60, 115)

    # Timpani — thunderous
    timp_p = GeneratorParams(density=0.45)
    timp = TimpaniGenerator(timp_p, stroke_pattern="roll", drum_count=5, roll_speed=0.0625)
    timp_notes = _clamp(timp.render(chords, EB_MAJOR, dur), 55, 95)

    # Snare — military
    snare_p = GeneratorParams(density=0.4)
    snare = SnareDrumGenerator(snare_p, pattern_type="march")
    snare_notes = _clamp(snare.render(chords, EB_MAJOR, dur), 40, 75)

    return {
        "Brass": brass_notes,
        "Horns": fanf_notes,
        "Hit": hit_notes,
        "Timpani": timp_notes,
        "Snare": snare_notes,
    }, 80.0


def track_13_resolution():
    """XIII. Resolution — Strings Reunite (D Harmonic Minor -> D Major, 50 BPM)"""
    print("  XIII. Resolution — Strings Reunite")
    dur = 68.0

    # First half: D harmonic minor, second half: D major (mode shift = hope)
    minor_dur = dur / 2
    major_dur = dur / 2
    minor_chords = _build_chords("i iv V i", minor_dur, D_HARM_MINOR)
    major_chords = _build_chords("I IV V I", major_dur, D_MAJOR)

    # Violin — lyrical solo transforming from minor to major
    v_p = GeneratorParams(density=0.6, key_range_low=55, key_range_high=96)
    violin = ViolinGenerator(v_p, articulation="sustained", vibrato=True, dynamic_curve="crescendo")
    v_minor = _clamp(violin.render(minor_chords, D_HARM_MINOR, minor_dur), 35, 80)
    v_major = _clamp(violin.render(major_chords, D_MAJOR, major_dur), 50, 95)
    for n in v_major:
        n.start += minor_dur

    # Cello — warm support
    c_p = GeneratorParams(density=0.5, key_range_low=36, key_range_high=60)
    cello = CelloGenerator(c_p, articulation="sustained", vibrato=True, dynamic_curve="crescendo")
    c_minor = _clamp(cello.render(minor_chords, D_HARM_MINOR, minor_dur), 30, 70)
    c_major = _clamp(cello.render(major_chords, D_MAJOR, major_dur), 40, 80)
    for n in c_major:
        n.start += minor_dur

    # Harp — celestial glissando in major section
    h_p = GeneratorParams(density=0.45, key_range_low=36, key_range_high=84)
    harp = HarpGenerator(h_p, pattern="glissando", direction="up", spread_speed=0.08)
    harp_notes = _clamp(harp.render(major_chords, D_MAJOR, major_dur), 30, 65)
    for n in harp_notes:
        n.start += minor_dur

    # Tremolo strings — emotional swell in minor
    t_p = GeneratorParams(density=0.5, key_range_low=44, key_range_high=68)
    trem = TremoloStringsGenerator(t_p, bow_speed=0.05, dynamic_swell=True)
    trem_notes = _clamp(trem.render(minor_chords, D_HARM_MINOR, minor_dur), 25, 65)

    return {
        "Violins": v_minor + v_major,
        "Cello": c_minor + c_major,
        "Harp": harp_notes,
        "Tremolo": trem_notes,
    }, 50.0


def track_14_finale():
    """XIV. Finale — All Voices United (C Major, 54 BPM)"""
    print("  XIV. Finale — All Voices United")
    dur = 80.0
    chords = _build_chords("I IV V I vi ii V I I IV V I", dur, C_MAJOR)

    # Chorale — full SATB
    chorale_p = GeneratorParams(density=0.5, key_range_low=36, key_range_high=84)
    chorale = ChoraleGenerator(chorale_p, voice_spacing=12, soprano_motion="stepwise", rhythmic_unit=2.0)
    chorale_notes = _clamp(chorale.render(chords, C_MAJOR, dur), 40, 90)

    # Full string ensemble
    str_p = GeneratorParams(density=0.55, key_range_low=36, key_range_high=84)
    strings = StringsLegatoGenerator(str_p, section_size="ensemble", dynamic_shape="crescendo")
    strings_notes = _clamp(strings.render(chords, C_MAJOR, dur), 35, 90)

    # Woodwind quartet
    ww_p = GeneratorParams(density=0.5, key_range_low=50, key_range_high=84)
    ww = WoodwindsEnsembleGenerator(ww_p, section="quartet", articulation="legato")
    ww_notes = _clamp(ww.render(chords, C_MAJOR, dur), 35, 80)

    # Choir — triumphant
    ch_p = GeneratorParams(density=0.55, key_range_low=48, key_range_high=76)
    choir = ChoirAahsGenerator(ch_p, voice_count=4, dynamics="ff", syllable="aah", vibrato=0.3)
    choir_notes = _clamp(choir.render(chords, C_MAJOR, dur), 45, 100)

    # Organ — cathedral resonance
    org_p = GeneratorParams(density=0.45, key_range_low=24, key_range_high=60)
    organ = OrganDrawbarsGenerator(org_p, registration="gospel", leslie_speed="slow")
    organ_notes = _clamp(organ.render(chords, C_MAJOR, dur), 30, 70)

    # Timpani — final rolls
    timp_p = GeneratorParams(density=0.35)
    timp = TimpaniGenerator(timp_p, stroke_pattern="roll", drum_count=5)
    timp_notes = _clamp(timp.render(chords, C_MAJOR, dur), 45, 85)

    # Bells — triumphant chimes
    bell_p = GeneratorParams(density=0.2, key_range_low=60, key_range_high=79)
    bells = TubularBellsGenerator(bell_p, stroke_pattern="chime")
    bell_notes = _clamp(bells.render(chords, C_MAJOR, dur), 45, 75)

    return {
        "Chorale": chorale_notes,
        "Strings": strings_notes,
        "Woodwinds": ww_notes,
        "Choir": choir_notes,
        "Organ": organ_notes,
        "Timpani": timp_notes,
        "Bells": bell_notes,
    }, 54.0


# ===========================================================================
# Main
# ===========================================================================

TRACKS = [
    # (producer, filename, GM instruments)
    (track_01_overture,    "01_Overture_Dawn_of_the_Orchestra.mid", {
        "Oboe": 68, "Harp": 46, "Strings": 48, "Horns": 60, "Timpani": 47,
    }),
    (track_02_awakening,   "02_Awakening_Strings_Unbound.mid", {
        "Violins": 40, "Cello": 42, "Viola": 41, "Bass": 43,
    }),
    (track_03_procession,  "03_Procession_Solemn_March.mid", {
        "Chorale": 48, "Snare": 115, "Tuba": 58, "Organ": 19,
    }),
    (track_04_scherzo,     "04_Scherzo_Woodwind_Games.mid", {
        "Waltz": 48, "Flute": 73, "Clarinet": 71, "Pizzicato": 45,
    }),
    (track_05_dance,       "05_Dance_of_Shadows.mid", {
        "Canon": 40, "Mallet": 12, "Bass": 43, "Timpani": 47,
    }),
    (track_06_fugue,       "06_Fugato_Three_Part_Invention.mid", {
        "Canon": 41, "Pedal": 38,
    }),
    (track_07_carnival,    "07_Carnival_of_Masks.mid", {
        "Trumpet": 56, "Trombone": 57, "Ostinato": 48, "Snare": 115, "Mallet": 9,
    }),
    (track_08_adagio,      "08_Adagio_Night_Over_the_Cathedral.mid", {
        "Cello": 42, "Bassoon": 70, "Drone": 38, "Organ": 19, "Bells": 14,
    }),
    (track_09_counterpoint,"09_Dialogue_Flute_Oboe_Counterpoint.mid", {
        "Woodwinds": 68, "Viola": 41,
    }),
    (track_10_lament,      "10_Lament_Choir_of_the_Fallen.mid", {
        "Choir": 52, "Tremolo": 44, "Horns": 60,
    }),
    (track_11_tension,     "11_Gathering_Storm.mid", {
        "Tension": 48, "Brass": 61, "Timpani": 47, "Tuba": 58,
    }),
    (track_12_fanfare,     "12_Triumph_Brass_Fanfare.mid", {
        "Brass": 61, "Horns": 60, "Hit": 55, "Timpani": 47, "Snare": 115,
    }),
    (track_13_resolution,  "13_Resolution_Strings_Reunite.mid", {
        "Violins": 40, "Cello": 42, "Harp": 46, "Tremolo": 44,
    }),
    (track_14_finale,      "14_Finale_All_Voices_United.mid", {
        "Chorale": 48, "Strings": 48, "Woodwinds": 68, "Choir": 52,
        "Organ": 19, "Timpani": 47, "Bells": 14,
    }),
]


def main():
    album_dir = Path("output/album_symphonia")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        S Y M P H O N I A   O B S C U R A")
    print("        A 14-Movement Symphonic Suite in Four Parts")
    print("        I. Overture & Awakening | II. Scherzo & Dance")
    print("        III. Adagio & Lament | IV. Finale & Resolution")
    print("=" * 80)

    total_notes = 0
    for i, (producer, filename, instruments) in enumerate(TRACKS):
        print("-" * 80)
        raw, bpm = producer()
        mastered, pan = apply_symphonic_mix(raw, bpm)
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
    print(f"  COMPLETE: SYMPHONIA OBSCURA — {total_notes} total notes across 14 movements")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
