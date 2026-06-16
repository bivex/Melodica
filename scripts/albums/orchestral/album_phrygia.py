# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_phrygia.py — PHRYGIA: FIVE TABLEAUX IN SHADOW

A 5-movement orchestral suite built entirely on the Phrygian family of modes,
designed to showcase the Layer-2 requested-key fix in the CoupledHMM engine.

Before the fix, every modal piece below would have been silently rewritten to
major by Layer 2 (key detection collapsed Phrygian/Dorian/Mixolydian to major
~100% of the time), losing the characteristic bII->i cadence and dark color.
Now each movement holds its mode: the characteristic Phrygian flat-second
(E->F->E), the gypsy augmented-second tension, the Byzantine double-harmonic
cadence all come through.

    I.   Descensus            (E Phrygian,          72 BPM)  — slow descent, low strings, choir drone
    II.  The Citadel at Dusk  (A Phrygian Dominant, 92 BPM)  —Processional, brass + frame-drum, Spanish/eastern color
    III. Cavern Rites         (D Double Harmonic,   84 BPM)  — ritualistic, ostinato + reed interplay
    IV.  Horsemen of the Steppe (B Hungarian Minor, 120 BPM) — fiery, driving, pizzicato + mallets
    V.   Apokalypsis          (C Phrygian,          96 BPM)  — grand finale, full tutti, timpani rolls
"""

import random
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.orchestral_strings import (
    ViolinGenerator, ViolaGenerator, CelloGenerator, ContrabassGenerator,
)
from melodica.generators.orchestral_brass import (
    TrumpetGenerator, TromboneGenerator, FrenchHornGenerator,
)
from melodica.generators.orchestral_woodwinds import (
    FluteGenerator, OboeGenerator, ClarinetGenerator, BassoonGenerator,
)
from melodica.generators.orchestral_percussion import (
    TimpaniGenerator, MalletPercussionGenerator,
)
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.tuba import TubaGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer, HMMConfig
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

random.seed(1729)

# ---------------------------------------------------------------------------
# Scales — all Phrygian family
# ---------------------------------------------------------------------------
E_PHRYGIAN          = Scale(root=4,  mode=Mode.PHRYGIAN)            # E F G A B C D
A_PHRYGIAN_DOMINANT = Scale(root=9,  mode=Mode.PHRYGIAN_DOMINANT)   # A Bb C# D E F G
D_DOUBLE_HARMONIC   = Scale(root=2,  mode=Mode.DOUBLE_HARMONIC)     # D Eb F# G A Bb C#
B_HUNGARIAN_MINOR   = Scale(root=11, mode=Mode.HUNGARIAN_MINOR)     # B C# D E# F# G# A#
C_PHRYGIAN          = Scale(root=0,  mode=Mode.PHRYGIAN)            # C Db Eb F G Ab Bb

# Shared harmonizer — uses the corrected emission_weight=20 default.
# chord_change="bars": one chord per bar (not every 2 beats) so progressions
# phrase meaningfully instead of a stream of disconnected half-bar changes.
# beam_width is accepted for API compatibility but CoupledHMM runs exact Viterbi.
_HARM = CoupledHMMHarmonizer(beam_width=14, chord_change="bars")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

# Diatonic chord-quality table per (mode, degree index) — built from the
# interval structure of each mode so the cadence phrases below use the
# correct chord quality (e.g. Phrygian i is minor, bII is major, V is dim).
# Degrees: 0=i, 1=bII, 2=III, 3=iv, 4=V, 5=VI, 6=vii.
_DIATONIC_QUALITY: dict[Mode, list[Quality]] = {
    Mode.PHRYGIAN:           [Quality.MINOR, Quality.MAJOR, Quality.MAJOR, Quality.MINOR, Quality.DIMINISHED, Quality.MAJOR, Quality.MINOR],
    Mode.PHRYGIAN_DOMINANT:  [Quality.MAJOR, Quality.MAJOR, Quality.DIMINISHED, Quality.MINOR, Quality.DIMINISHED, Quality.MAJOR, Quality.MINOR],
    Mode.DOUBLE_HARMONIC:    [Quality.MAJOR, Quality.MAJOR, Quality.MINOR, Quality.MINOR, Quality.MAJOR, Quality.MAJOR, Quality.DIMINISHED],
    Mode.HUNGARIAN_MINOR:    [Quality.MINOR, Quality.MAJOR, Quality.AUGMENTED, Quality.MAJOR, Quality.MAJOR, Quality.MAJOR, Quality.DIMINISHED],
}


def _phrase_chords(scale: Scale, phrase: list[tuple[int, int]]) -> list[ChordLabel]:
    """Build a phrase of ChordLabels from (degree_index, bars) specs.

    degree_index indexes the mode's scale degrees (0=tonic, 1=bII, ...).
    Chord quality is looked up from the diatonic table for the mode.
    """
    deg = [d % 12 for d in scale.degrees()]
    qualities = _DIATONIC_QUALITY[scale.mode]
    out = []
    t = 0.0
    for deg_idx, bars in phrase:
        out.append(ChordLabel(
            root=deg[deg_idx], quality=qualities[deg_idx],
            start=t, duration=bars * 4.0,
        ))
        t += bars * 4.0
    return out


def _phrase_constraints(scale: Scale, phrases: list[list[tuple[int, int]]],
                        form: str, dur: float) -> list[ChordLabel]:
    """Tile phrases across `dur` beats following a form (e.g. 'AAB').

    phrases: list of phrase specs, indexed by A/B/C in `form`.
    form: sequence of letters mapping to phrase indices (A=0, B=1, C=2).
    The form is repeated to fill `dur`. The final chord of the last repetition
    is lengthened to land on the tonic, giving a closing cadence.
    """
    letter_to_idx = {c: i for i, c in enumerate("ABCDEFGHIJ")}
    cycle = [phrases[letter_to_idx[c]] for c in form]
    cycle_beats = sum(bars * 4.0 for ph in cycle for _, bars in ph)
    constraints = []
    t = 0.0
    while t < dur - 0.01:
        for ph in cycle:
            if t >= dur - 0.01:
                break
            for deg_idx, bars in ph:
                if t >= dur - 0.01:
                    break
                chord_beats = min(bars * 4.0, dur - t)
                deg = [d % 12 for d in scale.degrees()]
                qualities = _DIATONIC_QUALITY[scale.mode]
                constraints.append(ChordLabel(
                    root=deg[deg_idx], quality=qualities[deg_idx],
                    start=t, duration=chord_beats,
                ))
                t += bars * 4.0
    return constraints


def _harmonize(melody: list[NoteInfo], scale: Scale, dur: float,
               constraints: list[ChordLabel] | None = None) -> list[ChordLabel]:
    """Harmonize a real melody line with the CoupledHMM engine.

    When constraints are supplied they lock the cadential phrase structure
    (built by _phrase_constraints), giving meaningful modal progressions
    instead of free chromatic wandering.
    """
    return _HARM.harmonize(melody, scale, duration_beats=dur, constraints=constraints)


def _lead_melody(scale: Scale, dur: float, *, lo: int, hi: int,
                 density: float, seed_off: int = 0) -> list[NoteInfo]:
    """Generate a lead melody line to harmonize against."""
    p = GeneratorParams(density=density, velocity_range=(60, 100),
                        key_range_low=lo, key_range_high=hi)
    gen = MelodyGenerator(p, phrase_length=8.0,
                          note_range_low=lo, note_range_high=hi,
                          register_smoothness=0.7, steps_probability=0.65,
                          motif_probability=0.6, phrase_contour="arch")
    guide_chords = [ChordLabel(root=scale.root, quality=scale.parse_roman("I").quality,
                               start=0.0, duration=dur)]
    return gen.render(guide_chords, scale, dur)


def _clamp(notes: list[NoteInfo], lo: int = 1, hi: int = 127) -> list[NoteInfo]:
    for n in notes:
        n.velocity = max(lo, min(hi, n.velocity))
    return notes


def _off(notes, offset):
    return [NoteInfo(pitch=n.pitch, start=n.start + offset,
                     duration=n.duration, velocity=n.velocity)
            for n in notes]


def _pedal_tone(chords: list[ChordLabel], scale: Scale, dur: float, *,
                pitch: int, note_dur: float = 4.0, velocity: int = 55) -> list[NoteInfo]:
    """Static pedal point — holds tonic/dominant pitch in long notes.

    Creates oblique motion against the moving bass, eliminating parallel
    fifths/octaves while reinforcing the modal tonic.
    """
    notes = []
    t = 0.0
    while t < dur:
        actual_dur = min(note_dur, dur - t)
        notes.append(NoteInfo(pitch=pitch, start=t, duration=actual_dur, velocity=velocity))
        t += note_dur
    return notes


def _drone(scale: Scale, dur: float, *, lo_pitch: int, hi_pitch: int,
           note_dur: float = 8.0, velocity: int = 48) -> list[NoteInfo]:
    """Sustained two-note drone (tonic + fifth/octave) — the bedrock of modal
    pieces. Long sustained tones, unlike ContrabassGenerator which follows
    chord roots."""
    notes = []
    t = 0.0
    while t < dur:
        actual_dur = min(note_dur, dur - t)
        notes.append(NoteInfo(pitch=lo_pitch, start=t, duration=actual_dur, velocity=velocity))
        notes.append(NoteInfo(pitch=hi_pitch, start=t, duration=actual_dur, velocity=velocity))
        t += note_dur
    return notes


def _thin(notes: list[NoteInfo], dur: float, *,
          intro_end: float | None = None,
          outro_start: float | None = None,
          keep: float = 0.25) -> list[NoteInfo]:
    """Drop a fraction of notes in intro/outro windows to create an energy curve."""
    rng = random.Random(42)
    intro_end = intro_end if intro_end is not None else dur * 0.20
    outro_start = outro_start if outro_start is not None else dur * 0.80
    result = []
    for n in notes:
        if n.start < intro_end or n.start >= outro_start:
            if rng.random() < keep:
                result.append(n)
        else:
            result.append(n)
    return result


def _mix(raw: dict, bpm: float, lufs: float = -14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Violin1": 0.80, "Viola": 0.76, "Cello": 0.80, "Bass": 0.84,
        "Brass": 0.78, "Horns": 0.80, "Trumpet": 0.76, "Trombone": 0.74,
        "Tuba": 0.84, "Woodwinds": 0.76, "Flute": 0.74, "Oboe": 0.74,
        "Clarinet": 0.76, "Bassoon": 0.78, "Choir": 0.80, "Harp": 0.82,
        "Timpani": 0.84, "Glock": 0.74, "Bells": 0.80, "Tremolo": 0.76,
        "Ostinato": 0.76, "Lead": 0.84, "Counter": 0.74, "Mallet": 0.74,
        "Pedal": 0.80, "Drone": 0.82,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# ===========================================================================
# I. Descensus — E Phrygian, 72 BPM
#    Slow, dark descent. Low strings, choir drone, distant timpani.
#    The signature E-F-E Phrygian flat-second colors the opening.
# ===========================================================================

def track_01_descensus():
    print("  I. Descensus")
    bpm, dur = 72.0, 104.0
    key = E_PHRYGIAN

    # Phrygian cadential phrases. A = i-VI-bII-i (Em-C-F-Em), the archetypal
    # Phrygian descent; B = i-iv-bII-i (Em-Am-F-Em) broadens to iv before the
    # characteristic bII->i cadence. Form AAB lands both statements then the
    # resolution, so the dark F->E flat-second colors every phrase end.
    phrases = [
        [(0, 1), (5, 1), (1, 1), (0, 1)],   # A: i - VI - bII - i
        [(0, 1), (3, 1), (1, 1), (0, 1)],   # B: i - iv - bII - i
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=84, density=0.4)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    cello = _thin(_clamp(CelloGenerator(
        GeneratorParams(density=0.4, key_range_low=36, key_range_high=52),
        articulation="legato").render(chords, key, dur), 40, 72), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=67),
        section_size="full", dynamic_shape="cresc_dim").render(chords, key, dur), 35, 68), dur)

    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.3, key_range_low=50, key_range_high=70),
        voice_count=6, dynamics="p", syllable="aah").render(chords, key, dur), 40, 72), dur)

    oboe = _clamp(OboeGenerator(
        GeneratorParams(density=0.4, key_range_low=67, key_range_high=88),
        articulation="legato", register=2).render(chords, key, dur - 8.0), 45, 80)
    oboe = _thin(_off(oboe, 8.0), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.6, key_range_low=24, key_range_high=36),
        articulation="legato").render(chords, key, dur), 45, 78)

    # Drone on tonic E (MIDI 28) + fifth B (MIDI 35) — modal bedrock
    drone = _drone(key, dur, lo_pitch=28, hi_pitch=35, note_dur=8.0, velocity=46)

    timp = _thin(_clamp(TimpaniGenerator(
        GeneratorParams(density=0.2, key_range_low=36, key_range_high=45),
        stroke_pattern="single").render(chords, key, dur), 55, 88), dur)

    return {
        "Lead": _clamp(lead, 50, 88), "Cello": cello, "Strings": strings,
        "Choir": choir, "Oboe": oboe, "Bass": bass, "Drone": drone, "Timpani": timp,
    }, bpm


# ===========================================================================
# II. The Citadel at Dusk — A Phrygian Dominant, 92 BPM
#     Processional. Brass chorale + harp arpeggios + frame-drum ostinato.
#     The Phrygian-dominant (Spanish/Arabic) color with raised third.
# ===========================================================================

def track_02_citadel():
    print("  II. The Citadel at Dusk")
    bpm, dur = 92.0, 96.0
    key = A_PHRYGIAN_DOMINANT

    # Phrygian-dominant phrases. The tonic is major here (A major), so I-bII
    # gives the Spanish/Arabic A->Bb pull. A = I-bII-I-iv (A-Bb-A-D),
    # B = I-vii-bII-I (A-G-Bb-A) walks down through the flat-seventh to the
    # cadence. Form AAB.
    phrases = [
        [(0, 1), (1, 1), (0, 1), (3, 1)],   # A: I - bII - I - iv
        [(0, 1), (6, 1), (1, 1), (0, 1)],   # B: I - vii - bII - I
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=65, hi=88, density=0.5)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    trumpet = _thin(_clamp(TrumpetGenerator(
        GeneratorParams(density=0.4, key_range_low=57, key_range_high=81),
        register=2, fanfare_mode=True).render(chords, key, dur), 50, 92), dur)

    brass_raw = _clamp(BrassSectionGenerator(
        GeneratorParams(density=0.35, key_range_low=48, key_range_high=72),
        ensemble_mode="full", intensity=0.85).render(chords, key, dur - 8.0), 48, 90)
    brass = _thin(_off(brass_raw, 8.0), dur)

    horns = _thin(_clamp(FrenchHornGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=67),
        articulation="legato").render(chords, key, dur), 42, 82), dur)

    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=84),
        pattern="arpeggio", direction="up_down", octave_span=4).render(chords, key, dur), 38, 78), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.35, key_range_low=50, key_range_high=74),
        section_size="full", dynamic_shape="crescendo").render(chords, key, dur), 40, 80), dur)

    viola = _thin(_clamp(ViolaGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=65),
        articulation="legato").render(chords, key, dur), 40, 75), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.75, key_range_low=24, key_range_high=36),
        articulation="legato").render(chords, key, dur), 48, 82)

    # Pedal on tonic A (MIDI 33)
    pedal = _pedal_tone(chords, key, dur, pitch=33, note_dur=4.0, velocity=50)

    timp = _thin(_clamp(TimpaniGenerator(
        GeneratorParams(density=0.3, key_range_low=36, key_range_high=48),
        stroke_pattern="single").render(chords, key, dur), 55, 92), dur)

    return {
        "Lead": _clamp(lead, 55, 92), "Trumpet": trumpet, "Brass": brass,
        "Horns": horns, "Harp": harp, "Strings": strings, "Viola": viola,
        "Bass": bass, "Pedal": pedal, "Timpani": timp,
    }, bpm


# ===========================================================================
# III. Cavern Rites — D Double Harmonic, 84 BPM
#      Ritualistic, mysterious. Ostinato + reed interplay + low choir.
#      The double-harmonic (gypsy major) augmented seconds throughout.
# ===========================================================================

def track_03_cavern():
    print("  III. Cavern Rites")
    bpm, dur = 84.0, 100.0
    key = D_DOUBLE_HARMONIC

    # Double-harmonic phrases. Both augmented seconds (D->Eb, A->Bb) sing in
    # I-bII. A = I-bII-I-III (D-Eb-D-F#), B = I-iv-bII-I (D-G-Eb-D) reaches
    # to iv before the cadence. Form AAB.
    phrases = [
        [(0, 1), (1, 1), (0, 1), (2, 1)],   # A: I - bII - I - III
        [(0, 1), (3, 1), (1, 1), (0, 1)],   # B: I - iv - bII - I
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=62, hi=86, density=0.5)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    ostinato = _thin(_clamp(OstinatoGenerator(
        GeneratorParams(density=0.7, key_range_low=50, key_range_high=67),
        pattern_length=4).render(chords, key, dur), 45, 78), dur)

    counter = _thin(_clamp(CounterpointGenerator(
        GeneratorParams(density=0.25, key_range_low=55, key_range_high=79)
    ).render(chords, key, dur), 42, 80), dur)

    clarinet = _thin(_clamp(ClarinetGenerator(
        GeneratorParams(density=0.45, key_range_low=55, key_range_high=79),
        articulation="legato").render(chords, key, dur), 42, 80), dur)

    bassoon = _thin(_clamp(BassoonGenerator(
        GeneratorParams(density=0.4, key_range_low=36, key_range_high=55),
        articulation="legato").render(chords, key, dur), 42, 78), dur)

    tremolo = _thin(_clamp(TremoloStringsGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=62),
        variant="single", bow_speed=0.20).render(chords, key, dur), 35, 66), dur)

    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=68),
        voice_count=6, dynamics="p", syllable="aah").render(chords, key, dur), 40, 72), dur)

    mallet = _thin(_clamp(MalletPercussionGenerator(
        GeneratorParams(density=0.5, key_range_low=72, key_range_high=96),
        instrument="marimba", pattern="run").render(chords, key, dur), 42, 80), dur,
        intro_end=dur*0.30, outro_start=dur*0.75, keep=0.15)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.7, key_range_low=24, key_range_high=38),
        articulation="pizzicato").render(chords, key, dur), 48, 82)

    # Drone on tonic D (MIDI 26) + fifth A (MIDI 33)
    drone = _drone(key, dur, lo_pitch=26, hi_pitch=33, note_dur=8.0, velocity=46)

    return {
        "Lead": _clamp(lead, 52, 88), "Ostinato": ostinato, "Counter": counter,
        "Clarinet": clarinet, "Bassoon": bassoon, "Tremolo": tremolo,
        "Choir": choir, "Mallet": mallet, "Bass": bass, "Drone": drone,
    }, bpm


# ===========================================================================
# IV. Horsemen of the Steppe — B Hungarian Minor, 120 BPM
#     Fiery, driving. Pizzicato gallop + mallets + violin flourishes.
#     Hungarian minor augmented-second for an eastern-European edge.
# ===========================================================================

def track_04_horsemen():
    print("  IV. Horsemen of the Steppe")
    bpm, dur = 120.0, 88.0
    key = B_HUNGARIAN_MINOR

    # Hungarian-minor phrases. The augmented second B->C# colors bII.
    # A = i-VI-bII-i (Bm-G-C#-Bm), B = i-V-bII-i (Bm-F#-C#-Bm) uses the
    # major V (F#) for a stronger pull before the Phrygian cadence. Form AAB.
    phrases = [
        [(0, 1), (5, 1), (1, 1), (0, 1)],   # A: i - VI - bII - i
        [(0, 1), (4, 1), (1, 1), (0, 1)],   # B: i - V - bII - i
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=66, hi=89, density=0.65)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.65, key_range_low=66, key_range_high=90),
        articulation="spiccato").render(chords, key, dur), 50, 92), dur)

    pizz = _thin(_clamp(CelloGenerator(
        GeneratorParams(density=0.55, key_range_low=40, key_range_high=55),
        articulation="pizzicato").render(chords, key, dur), 48, 85), dur,
        intro_end=dur*0.25, outro_start=dur*0.78, keep=0.15)

    flute = _clamp(FluteGenerator(
        GeneratorParams(density=0.55, key_range_low=72, key_range_high=96),
        articulation="staccato", register=3).render(chords, key, dur - 12.0), 45, 84)
    flute = _thin(_off(flute, 6.0), dur)

    mallet = _thin(_clamp(MalletPercussionGenerator(
        GeneratorParams(density=0.6, key_range_low=72, key_range_high=96),
        instrument="marimba", pattern="run").render(chords, key, dur), 45, 82), dur)

    glock_raw = _clamp(GlockenspielGenerator(
        GeneratorParams(density=0.4, key_range_low=84, key_range_high=104),
        pattern="sparkling_run", note_density=1.0).render(chords, key, dur - 8.0), 38, 72)
    glock = _thin(_off(glock_raw, 8.0), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.3, key_range_low=50, key_range_high=67),
        section_size="full", dynamic_shape="crescendo").render(chords, key, dur), 38, 76), dur,
        intro_end=dur*0.25, outro_start=dur*0.78, keep=0.15)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.8, key_range_low=24, key_range_high=38),
        articulation="pizzicato").render(chords, key, dur), 50, 88)

    # Pedal on tonic B (MIDI 35)
    pedal = _pedal_tone(chords, key, dur, pitch=35, note_dur=2.0, velocity=50)

    timp = _thin(_clamp(TimpaniGenerator(
        GeneratorParams(density=0.4, key_range_low=36, key_range_high=48),
        stroke_pattern="single").render(chords, key, dur), 55, 95), dur)

    return {
        "Lead": _clamp(lead, 58, 96), "Violin1": violin, "Pizzicato": pizz,
        "Flute": flute, "Mallet": mallet, "Glock": glock, "Strings": strings,
        "Bass": bass, "Pedal": pedal, "Timpani": timp,
    }, bpm


# ===========================================================================
# V. Apokalypsis — C Phrygian, 96 BPM
#    Grand finale. Full tutti, timpani rolls, brass fanfares, choir.
#    Returns to pure Phrygian to close the arc.
# ===========================================================================

def track_05_apokalypsis():
    print("  V. Apokalypsis")
    bpm, dur = 96.0, 112.0
    key = C_PHRYGIAN

    # C Phrygian cadential phrases — and the constraints anchor the tonic on
    # C (no drift to C#), fixing the earlier Layer-2 slip.
    # A = i-bII-i-VI (Cm-Db-Cm-Ab), B = i-iv-bII-i (Cm-F-Db-Cm).
    # Form AAB for the grand-finale arc.
    phrases = [
        [(0, 1), (1, 1), (0, 1), (5, 1)],   # A: i - bII - i - VI
        [(0, 1), (3, 1), (1, 1), (0, 1)],   # B: i - iv - bII - i
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=88, density=0.5)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    trumpet = _thin(_clamp(TrumpetGenerator(
        GeneratorParams(density=0.45, key_range_low=60, key_range_high=84),
        register=2, fanfare_mode=True).render(chords, key, dur), 55, 100), dur)

    brass_raw = _clamp(BrassSectionGenerator(
        GeneratorParams(density=0.4, key_range_low=48, key_range_high=72),
        ensemble_mode="full", intensity=0.9).render(chords, key, dur - 4.0), 50, 98)
    brass = _thin(_off(brass_raw, 4.0), dur)

    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.6, key_range_low=67, key_range_high=91),
        articulation="legato").render(chords, key, dur), 50, 95), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.4, key_range_low=48, key_range_high=72),
        section_size="full", dynamic_shape="crescendo").render(chords, key, dur), 45, 85), dur)

    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.35, key_range_low=50, key_range_high=74),
        voice_count=6, dynamics="ff", syllable="aah").render(chords, key, dur), 45, 90), dur)

    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.6, key_range_low=48, key_range_high=84),
        pattern="arpeggio", direction="up_down").render(chords, key, dur), 40, 82), dur)

    glock = _thin(_clamp(GlockenspielGenerator(
        GeneratorParams(density=0.5, key_range_low=88, key_range_high=104),
        pattern="sparkling_run", note_density=1.2).render(chords, key, dur), 45, 82), dur)

    tuba = _thin(_clamp(TubaGenerator(
        GeneratorParams(density=0.4, key_range_low=28, key_range_high=46)
    ).render(chords, key, dur), 50, 92), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.8, key_range_low=24, key_range_high=40),
        articulation="legato").render(chords, key, dur), 48, 88)

    # Pedal on tonic C (MIDI 24)
    pedal = _pedal_tone(chords, key, dur, pitch=24, note_dur=4.0, velocity=52)

    timp = _thin(_clamp(TimpaniGenerator(
        GeneratorParams(density=0.45, key_range_low=36, key_range_high=48),
        stroke_pattern="roll").render(chords, key, dur), 55, 100), dur)

    return {
        "Lead": _clamp(lead, 60, 100), "Trumpet": trumpet, "Brass": brass,
        "Violin1": violin, "Strings": strings, "Choir": choir,
        "Harp": harp, "Glock": glock, "Tuba": tuba, "Bass": bass,
        "Pedal": pedal, "Timpani": timp,
    }, bpm


# ---------------------------------------------------------------------------
# Instrument GM program maps per track
# ---------------------------------------------------------------------------

TRACKS = [
    (track_01_descensus, "01_Descensus.mid", {
        "Lead": 71, "Cello": 42, "Strings": 48, "Choir": 52,
        "Oboe": 68, "Bass": 43, "Drone": 43, "Timpani": 47,
    }),
    (track_02_citadel, "02_The_Citadel_at_Dusk.mid", {
        "Lead": 40, "Trumpet": 56, "Brass": 61, "Horns": 60,
        "Harp": 46, "Strings": 48, "Viola": 41, "Bass": 43,
        "Pedal": 43, "Timpani": 47,
    }),
    (track_03_cavern, "03_Cavern_Rites.mid", {
        "Lead": 71, "Ostinato": 45, "Counter": 71, "Clarinet": 71,
        "Bassoon": 70, "Tremolo": 44, "Choir": 52, "Mallet": 13,
        "Bass": 43, "Drone": 43,
    }),
    (track_04_horsemen, "04_Horsemen_of_the_Steppe.mid", {
        "Lead": 40, "Violin1": 40, "Pizzicato": 42, "Flute": 73,
        "Mallet": 13, "Glock": 9, "Strings": 48, "Bass": 43,
        "Pedal": 43, "Timpani": 47,
    }),
    (track_05_apokalypsis, "05_Apokalypsis.mid", {
        "Lead": 40, "Trumpet": 56, "Brass": 61, "Violin1": 40,
        "Strings": 48, "Choir": 52, "Harp": 46, "Glock": 9,
        "Tuba": 58, "Bass": 43, "Pedal": 43, "Timpani": 47,
    }),
]


def main():
    album_dir = Path("output/album_phrygia")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 78)
    print("      P H R Y G I A :   F I V E   T A B L E A U X   I N   S H A D O W")
    print("      All Phrygian-family modes — held by the Layer-2 requested-key fix")
    print("=" * 78)

    total_notes = 0
    for producer, filename, instruments in TRACKS:
        print("-" * 78)
        raw, bpm = producer()
        mastered, pan = _mix(raw, bpm)
        export_multitrack_midi(
            mastered,
            str(album_dir / filename),
            bpm=bpm,
            cc_events=pan,
            instruments=instruments,
            reaper_project=True,
        )
        nc = sum(len(n) for n in raw.values())
        total_notes += nc
        print(f"    -> {filename}  ({nc} notes, {bpm:.0f} BPM)")

    print()
    print("=" * 78)
    print(f"  COMPLETE: PHRYGIA — {total_notes} notes across 5 movements")
    print(f"  Modes: E Phrygian | A Phrygian Dominant | D Double Harmonic |")
    print(f"         B Hungarian Minor | C Phrygian")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
