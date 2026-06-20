# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_six_worlds.py — SIX WORLDS, SIX MODES

A 6-movement world-music suite designed as a live regression test for the
CoupledHMM engine. Each movement lives in a different tradition and a
different mode that PREVIOUSLY broke the harmonizer, so a single listen (or
a single --verify run) confirms the fixes hold together musically.

    I.   Hagia Sophia at Dawn       (D Byzantine,           66 BPM)  — fix #1: enum exotic, was 0%
    II.  Gardens of Isfahan         (C Persian,             72 BPM)  — fix #1: enum exotic, was 0%
    III. Raga Yaman at Sunset       (C Yaman,               76 BPM)  — fix #5: alias of Lydian, was 0%
    IV.  Flamenco de la Luna        (E Flamenco [string],   92 BPM)  — fix #6: string-mode, was silent
    V.   Makam Hicaz Gözyaşları     (A Hicaz [string µtonal], 80 BPM) — fix #7: microtonal string, was silent
    VI.  Éclats sur le Ciel         (C Messiaen-3,          60 BPM)  — fix #1+#5: modernist enum + alias

Before the fixes these modes were either collapsed to major/minor (I, II, III,
VI), silently mapped to a nearest enum (IV), or silently snapped to 12-TET (V).
The string-mode movements (IV, V) will emit a UserWarning on load — that is
the intended behaviour of fix #6/#7 surfacing the limitation.
"""

import random
import warnings
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.orchestral_strings import (
    ViolinGenerator, ViolaGenerator, CelloGenerator, ContrabassGenerator,
)
from melodica.generators.orchestral_woodwinds import (
    FluteGenerator, OboeGenerator, ClarinetGenerator, BassoonGenerator,
)
from melodica.generators.orchestral_brass import FrenchHornGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator

# World-music ensembles — these are what make the album interesting.
from melodica.generators.arabic_ensemble import OudGenerator, NeyGenerator, DarbukaGenerator
from melodica.generators.indian_ensemble import SitarGenerator, TablaGenerator, TanpuraGenerator
from melodica.generators.east_asian_ensemble import KotoGenerator, ErhuGenerator

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer, HMMConfig
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

random.seed(626)  # aria da capo

# ---------------------------------------------------------------------------
# Scales — six modes, each a different regression case
# ---------------------------------------------------------------------------
D_BYZANTINE    = Scale(root=2, mode=Mode.BYZANTINE)          # D Eb F# G A Bb C# — fix #1
C_PERSIAN      = Scale(root=0, mode=Mode.PERSIAN)            # C Db E F F# Ab B   — fix #1
C_YAMAN        = Scale(root=0, mode=Mode.YAMAN)              # C D E F# G A B     — fix #5 (alias of Lydian)
E_FLAMENCO     = Scale(root=4, mode="flamenco")              # string mode        — fix #6
A_HICAZ        = Scale(root=9, mode="makam_hicaz")           # µtonal string mode — fix #7
C_MESSIAEN_3   = Scale(root=0, mode=Mode.MESSIAEN_3)         # C Db E F F# Ab Bb  — fix #1+#5 (alias of Aug Mode 2)

_HARM = CoupledHMMHarmonizer(beam_width=14, chord_change="bars")


# ---------------------------------------------------------------------------
# Utilities (shared with album_phrygia — proven shape)
# ---------------------------------------------------------------------------

# Diatonic chord quality per (mode, degree). Built by hand from each mode's
# interval structure so the cadence phrases below use idiomatic qualities.
# Degrees: 0=I, 1=bII/II, 2=bIII/III, 3=iv/IV, 4=V/v, 5=VI, 6=vii/bVII.
_DIATONIC_QUALITY: dict[str, list[Quality]] = {
    # Byzantine / Double-harmonic major: I bII III iv V VI vii°
    "byzantine":      [Quality.MAJOR, Quality.MAJOR, Quality.MINOR, Quality.MINOR,
                        Quality.MAJOR, Quality.MAJOR, Quality.DIMINISHED],
    # Persian (intervals [0,1,4,5,6,8,11]): I bII III iv v° VI vii°
    "persian":        [Quality.MAJOR, Quality.MAJOR, Quality.MINOR, Quality.MINOR,
                        Quality.DIMINISHED, Quality.MAJOR, Quality.DIMINISHED],
    # Yaman (= Lydian [0,2,4,6,7,9,11]): I II iii iv° V vi vii°
    "yaman":          [Quality.MAJOR, Quality.MAJOR, Quality.MINOR, Quality.DIMINISHED,
                        Quality.MAJOR, Quality.MINOR, Quality.DIMINISHED],
    # Flamenco (= double-harmonic major intervals [0,1,4,5,7,8,11])
    "flamenco":       [Quality.MAJOR, Quality.MAJOR, Quality.MINOR, Quality.MINOR,
                        Quality.MAJOR, Quality.MAJOR, Quality.DIMINISHED],
    # Makam Hicaz (snapped PCs {0,1,4,5,7,8,10} after µtonal round)
    "makam_hicaz":    [Quality.MAJOR, Quality.MAJOR, Quality.MINOR, Quality.MINOR,
                        Quality.MAJOR, Quality.MAJOR, Quality.DIMINISHED],
    # Messiaen-3 (= augmented mode 2, [0,1,4,5,8,9]) — only 6 degrees
    "messiaen_3":     [Quality.MAJOR, Quality.MAJOR, Quality.AUGMENTED, Quality.AUGMENTED,
                        Quality.MAJOR, Quality.MAJOR, Quality.MAJOR],
}


def _qualities_for(scale: Scale) -> list[Quality]:
    """Look up the diatonic-quality table by mode name (handles string modes)."""
    mode_name = scale.mode.value if hasattr(scale.mode, "value") else str(scale.mode)
    return _DIATONIC_QUALITY.get(mode_name, [Quality.MAJOR] * 7)


def _phrase_chords(scale: Scale, phrase: list[tuple[int, int]]) -> list[ChordLabel]:
    """Build a phrase of ChordLabels from (degree_index, bars) specs."""
    deg = [d % 12 for d in scale.degrees()]
    qualities = _qualities_for(scale)
    out = []
    t = 0.0
    for deg_idx, bars in phrase:
        q = qualities[deg_idx] if deg_idx < len(qualities) else Quality.MAJOR
        out.append(ChordLabel(
            root=deg[deg_idx % len(deg)], quality=q,
            start=t, duration=bars * 4.0,
        ))
        t += bars * 4.0
    return out


def _phrase_constraints(scale: Scale, phrases: list[list[tuple[int, int]]],
                        form: str, dur: float) -> list[ChordLabel]:
    """Tile phrases across `dur` beats following a form (e.g. 'AAB')."""
    letter_to_idx = {c: i for i, c in enumerate("ABCDEFGHIJ")}
    cycle = [phrases[letter_to_idx[c]] for c in form]
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
                qualities = _qualities_for(scale)
                q = qualities[deg_idx % len(qualities)] if deg_idx < len(qualities) else Quality.MAJOR
                constraints.append(ChordLabel(
                    root=deg[deg_idx % len(deg)], quality=q,
                    start=t, duration=chord_beats,
                ))
                t += bars * 4.0
    return constraints


def _harmonize(melody: list[NoteInfo], scale: Scale, dur: float,
               constraints: list[ChordLabel] | None = None) -> list[ChordLabel]:
    return _HARM.harmonize(melody, scale, duration_beats=dur, constraints=constraints)


def _lead_melody(scale: Scale, dur: float, *, lo: int, hi: int,
                 density: float, seed_off: int = 0) -> list[NoteInfo]:
    p = GeneratorParams(density=density, velocity_range=(55, 95),
                        key_range_low=lo, key_range_high=hi)
    gen = MelodyGenerator(p, phrase_length=8.0,
                          note_range_low=lo, note_range_high=hi,
                          register_smoothness=0.7, steps_probability=0.6,
                          motif_probability=0.55, phrase_contour="arch")
    guide_chords = [ChordLabel(root=scale.root, quality=Quality.MAJOR,
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


def _drone(lo_pitch: int, hi_pitch: int, dur: float, *,
           note_dur: float = 8.0, velocity: int = 46) -> list[NoteInfo]:
    """Sustained two-note drone — modal bedrock for non-diatonic modes."""
    notes = []
    t = 0.0
    while t < dur:
        actual = min(note_dur, dur - t)
        notes.append(NoteInfo(pitch=lo_pitch, start=t, duration=actual, velocity=velocity))
        notes.append(NoteInfo(pitch=hi_pitch, start=t, duration=actual, velocity=velocity))
        t += note_dur
    return notes


def _pedal(pitch: int, dur: float, *, note_dur: float = 4.0,
           velocity: int = 50) -> list[NoteInfo]:
    notes = []
    t = 0.0
    while t < dur:
        actual = min(note_dur, dur - t)
        notes.append(NoteInfo(pitch=pitch, start=t, duration=actual, velocity=velocity))
        t += note_dur
    return notes


def _thin(notes: list[NoteInfo], dur: float, *,
          intro_end: float | None = None,
          outro_start: float | None = None,
          keep: float = 0.25) -> list[NoteInfo]:
    """Drop a fraction of notes in intro/outro to shape the energy curve."""
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
        "Lead": 0.84, "Choir": 0.80, "Strings": 0.80, "Cello": 0.78,
        "Bass": 0.84, "Drone": 0.82, "Pedal": 0.80, "Timpani": 0.84,
        "Harp": 0.82, "Oud": 0.82, "Ney": 0.80, "Darbuka": 0.80,
        "Sitar": 0.84, "Tabla": 0.80, "Tanpura": 0.78, "Koto": 0.82,
        "Erhu": 0.80, "Oboe": 0.78, "Clarinet": 0.78, "Bassoon": 0.78,
        "Horns": 0.78, "Flute": 0.78, "Glock": 0.74, "Ostinato": 0.76,
        "Counter": 0.74, "Mallet": 0.74, "Tremolo": 0.76,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# ===========================================================================
# I. Hagia Sophia at Dawn — D Byzantine (fix #1)
#    Slow Orthodox chant. Low choir drone, distant ney, sustained low strings.
#    The Byzantine double-harmonic augmented seconds (D-Eb, A-Bb) color the dawn.
#    Before fix #1 this collapsed to D harmonic_minor throughout.
# ===========================================================================

def track_01_hagia_sophia():
    print("  I. Hagia Sophia at Dawn")
    bpm, dur = 66.0, 100.0
    key = D_BYZANTINE

    # Byzantine cadential phrases. The tonic is major (D), bII (Eb) gives the
    # characteristic eastern pull. A = I-bII-I-III (D-Eb-D-F#), the archetypal
    # double-harmonic statement; B = I-iv-bII-I (D-G-Eb-D). Form AAB.
    phrases = [
        [(0, 1), (1, 1), (0, 1), (2, 1)],   # A: I - bII - I - III
        [(0, 1), (3, 1), (1, 1), (0, 1)],   # B: I - iv - bII - I
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=62, hi=86, density=0.35)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=68),
        voice_count=6, dynamics="p", syllable="aah").render(chords, key, dur), 40, 72), dur)

    ney = _thin(_clamp(NeyGenerator(
        GeneratorParams(density=0.4, key_range_low=67, key_range_high=88),
        breath_noise=0.45, vibrato_depth=0.3, legato_glide=0.3).render(chords, key, dur), 45, 78), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.3, key_range_low=43, key_range_high=62),
        section_size="full", dynamic_shape="cresc_dim").render(chords, key, dur), 38, 70), dur)

    cello = _thin(_clamp(CelloGenerator(
        GeneratorParams(density=0.4, key_range_low=36, key_range_high=52),
        articulation="legato").render(chords, key, dur), 42, 72), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.6, key_range_low=24, key_range_high=36),
        articulation="legato").render(chords, key, dur), 45, 75)

    # Drone on D (26) + A (33) — the modal center that anchors the augmented seconds
    drone = _drone(26, 33, dur, note_dur=8.0, velocity=46)

    return {
        "Lead": _clamp(lead, 50, 85), "Choir": choir, "Ney": ney,
        "Strings": strings, "Cello": cello, "Bass": bass, "Drone": drone,
    }, bpm


# ===========================================================================
# II. Gardens of Isfahan — C Persian (fix #1)
#     Garden at golden hour. Harp arpeggios, ney melody, oud counterline.
#     Persian mode [0,1,4,5,6,8,11] — two augmented seconds (C-Db, F-F#).
#     Before fix #1 this collapsed to C melodic_minor.
# ===========================================================================

def track_02_isfahan():
    print("  II. Gardens of Isfahan")
    bpm, dur = 72.0, 96.0
    key = C_PERSIAN

    # Persian phrases. A = I-bII-III-iv (C-Db-E-Fm), reaching the major III
    # for color; B = I-iv-V-I (C-Fm-G-C) with the Persian major V (G, despite
    # the augmented-second surroundings). Form AAB.
    phrases = [
        [(0, 1), (1, 1), (2, 1), (3, 1)],   # A: I - bII - III - iv
        [(0, 1), (3, 1), (4, 1), (0, 1)],   # B: I - iv - V - I
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=88, density=0.45)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.35, key_range_low=50, key_range_high=86),
        pattern="arpeggio", direction="up_down", octave_span=4).render(chords, key, dur), 40, 76), dur)

    ney = _thin(_clamp(NeyGenerator(
        GeneratorParams(density=0.5, key_range_low=67, key_range_high=91),
        breath_noise=0.4, vibrato_depth=0.35, legato_glide=0.4).render(chords, key, dur), 48, 82), dur)

    oud = _thin(_clamp(OudGenerator(
        GeneratorParams(density=0.4, key_range_low=48, key_range_high=67),
        tremolo_density=0.35, risha_style="standard").render(chords, key, dur), 45, 78), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=67),
        section_size="chamber", dynamic_shape="cresc_dim").render(chords, key, dur), 38, 72), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.65, key_range_low=24, key_range_high=38),
        articulation="legato").render(chords, key, dur), 46, 78)

    drone = _drone(24, 31, dur, note_dur=8.0, velocity=44)  # C + G

    return {
        "Lead": _clamp(lead, 52, 88), "Harp": harp, "Ney": ney,
        "Oud": oud, "Strings": strings, "Bass": bass, "Drone": drone,
    }, bpm


# ===========================================================================
# III. Raga Yaman at Sunset — C Yaman (fix #5: alias of Lydian)
#      Hindustani evening raga. Sitar alapi + tabla + tanpura drone.
#      Yaman is the same scale as Lydian (raised 4th, F#-on-C); before fix #5
#      Yaman was penalised at prior -10 and never detected as itself.
# ===========================================================================

def track_03_yaman():
    print("  III. Raga Yaman at Sunset")
    bpm, dur = 76.0, 104.0
    key = C_YAMAN

    # Yaman (= Lydian) phrases. The raised 4th (F#) is the raga's color tone.
    # A = I-II-IV-V (C-D-F#-G), the Lydian ascent; B = I-vi-IV-I (C-Am-F#-C),
    # a plagal-ish cadence that lands the raised 4th before tonic.
    phrases = [
        [(0, 1), (1, 1), (3, 1), (4, 1)],   # A: I - II - IV - V
        [(0, 1), (5, 1), (3, 1), (0, 1)],   # B: I - vi - IV - I
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=89, density=0.45)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    sitar = _thin(_clamp(SitarGenerator(
        GeneratorParams(density=0.5, key_range_low=55, key_range_high=84),
        sympathetic_resonance=0.45, meend_probability=0.4,
        krintan_probability=0.3).render(chords, key, dur), 50, 84), dur)

    tabla = _thin(_clamp(TablaGenerator(
        GeneratorParams(density=0.6, key_range_low=40, key_range_high=55),
        tala="teental", bayan_modulation=0.55, humanize_swing=0.08).render(chords, key, dur),
        50, 88), dur, intro_end=dur*0.25, keep=0.1)

    tanpura = _clamp(TanpuraGenerator(
        GeneratorParams(density=0.4, key_range_low=40, key_range_high=55),
        tuning="Sa-Pa", jivari=0.55, pluck_pattern="standard").render(chords, key, dur), 45, 72)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.25, key_range_low=50, key_range_high=70),
        section_size="chamber", dynamic_shape="cresc_dim").render(chords, key, dur), 38, 72), dur)

    # Tanpura + low drone double the Sa-Pa (C-G) foundation.
    drone = _drone(36, 43, dur, note_dur=8.0, velocity=42)

    return {
        "Lead": _clamp(lead, 55, 88), "Sitar": sitar, "Tabla": tabla,
        "Tanpura": tanpura, "Strings": strings, "Drone": drone,
    }, bpm


# ===========================================================================
# IV. Flamenco de la Luna — E Flamenco (string mode, fix #6)
#     Spanish guitar + cajon + palmas. Flamenco = double-harmonic-major
#     intervals [0,1,4,5,7,8,11]. This is a STRING mode (not in MODES_LIST),
#     so before fix #6 it was silently mapped to a nearest enum (harmonic_minor)
#     with no warning. Now it emits a UserWarning at load — that is correct.
# ===========================================================================

def track_04_flamenco():
    print("  IV. Flamenco de la Luna")
    bpm, dur = 92.0, 88.0
    key = E_FLAMENCO

    # Flamenco phrases. Tonic E major, bII (F) gives the Andalusian cadence.
    # A = I-bII-I-iv (E-F-E-Am), the soleá; B = I-iv-bII-I (E-Am-F-E),
    # the descending Andalusian cadence Am-G-F-E shifted to E-F. Form AAB.
    phrases = [
        [(0, 1), (1, 1), (0, 1), (3, 1)],   # A: I - bII - I - iv
        [(0, 1), (3, 1), (1, 1), (0, 1)],   # B: I - iv - bII - I
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=88, density=0.6)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    # Oud stands in for flamenco guitar (no dedicated guitar generator): risha
    # flatpick + chorus gives a percussive, metallic tone close to a golpe.
    guitar = _thin(_clamp(OudGenerator(
        GeneratorParams(density=0.7, key_range_low=52, key_range_high=79),
        tremolo_density=0.45, risha_style="rasgueado",
        chorus_detune=0.18).render(chords, key, dur), 55, 88), dur)

    # Darbuka stands in for cajon: dry, mid percussion for the compás.
    cajon = _thin(_clamp(DarbukaGenerator(
        GeneratorParams(density=0.7, key_range_low=38, key_range_high=50),
        rhythm_pattern="buleria", rolls_probability=0.25).render(chords, key, dur),
        55, 90), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.3, key_range_low=50, key_range_high=70),
        section_size="chamber", dynamic_shape="cresc_dim").render(chords, key, dur), 40, 76), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.7, key_range_low=28, key_range_high=40),
        articulation="pizzicato").render(chords, key, dur), 50, 85)

    pedal = _pedal(40, dur, note_dur=2.0, velocity=48)  # E pedal

    return {
        "Lead": _clamp(lead, 58, 92), "Guitar": guitar, "Cajon": cajon,
        "Strings": strings, "Bass": bass, "Pedal": pedal,
    }, bpm


# ===========================================================================
# V. Makam Hicaz Gözyaşları — A Hicaz (string mode, microtonal, fix #7)
#    Turkish lament. Oud + ney + darbuka. Makam Hicaz intervals
#    [0,1,4,5,7,8,10] with the augmented second Db-E (1.5→2 snap warning).
#    This is BOTH a string mode AND microtonal — fix #7 emits the combined
#    warning. The HMM snaps the 1.5-semitone steps to 12-TET, so the actual
#    harmony uses the snapped PCs {0,1,4,5,7,8,10}. Listenable, but the
#    quarter-tone color is lost — that is the documented limitation.
# ===========================================================================

def track_05_hicaz():
    print("  V. Makam Hicaz Gözyaşları")
    bpm, dur = 80.0, 92.0
    key = A_HICAZ

    # Hicaz phrases (using snapped PCs). A = I-bII-III-iv (A-Bb-C#-Dm), the
    # ascending Hicaz tetrachord; B = I-iv-bII-I (A-Dm-Bb-A), the descending
    # cadence. Form AAB.
    phrases = [
        [(0, 1), (1, 1), (2, 1), (3, 1)],   # A: I - bII - III - iv
        [(0, 1), (3, 1), (1, 1), (0, 1)],   # B: I - iv - bII - I
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=89, density=0.45)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    oud = _thin(_clamp(OudGenerator(
        GeneratorParams(density=0.5, key_range_low=50, key_range_high=72),
        tremolo_density=0.4, risha_style="standard").render(chords, key, dur), 48, 82), dur)

    ney = _thin(_clamp(NeyGenerator(
        GeneratorParams(density=0.55, key_range_low=67, key_range_high=91),
        breath_noise=0.5, vibrato_depth=0.4, legato_glide=0.45).render(chords, key, dur), 48, 84), dur)

    darbuka = _thin(_clamp(DarbukaGenerator(
        GeneratorParams(density=0.6, key_range_low=38, key_range_high=50),
        rhythm_pattern="maqsoum", rolls_probability=0.2).render(chords, key, dur),
        50, 88), dur, intro_end=dur*0.20, keep=0.15)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.25, key_range_low=45, key_range_high=64),
        section_size="chamber", dynamic_shape="cresc_dim").render(chords, key, dur), 38, 72), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.65, key_range_low=24, key_range_high=38),
        articulation="legato").render(chords, key, dur), 46, 80)

    drone = _drone(33, 40, dur, note_dur=8.0, velocity=44)  # A + E

    return {
        "Lead": _clamp(lead, 50, 88), "Oud": oud, "Ney": ney,
        "Darbuka": darbuka, "Strings": strings, "Bass": bass, "Drone": drone,
    }, bpm


# ===========================================================================
# VI. Éclats sur le Ciel — C Messiaen-3 (fix #1 + fix #5 alias)
#     Modern / impressionistic. Glockenspiel shards, harp, choir, low brass.
#     Messiaen mode 3 [0,1,4,5,8,9] is a 6-note symmetric mode (same PCs as
#     AUGMENTED_MODE_2, an alias group). Before fix #1 it was 0%-detected;
#     fix #5 lifts it to its alias peer's prior. Floating, non-tonal color.
# ===========================================================================

def track_06_eclats():
    print("  VI. Éclats sur le Ciel")
    bpm, dur = 60.0, 96.0
    key = C_MESSIAEN_3

    # Messiaen-3 has only 6 degrees (0,1,4,5,8,9). Phrases walk the mode's
    # own pitches; cadence is intentionally ambiguous (the mode is non-tonal).
    # A = I-bII-IV-#V (C-Db-F-F#), A walks two tritone-related triads;
    # B = I-IV-I-bII (C-F-C-Db), a colour oscillation. Form AAB.
    phrases = [
        [(0, 1), (1, 1), (3, 1), (4, 1)],   # A: I - bII - IV - #V
        [(0, 1), (3, 1), (0, 1), (1, 1)],   # B: I - IV - I - bII
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=66, hi=92, density=0.35)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    glock = _thin(_clamp(GlockenspielGenerator(
        GeneratorParams(density=0.5, key_range_low=84, key_range_high=108),
        pattern="sparkling_run", note_density=1.0).render(chords, key, dur), 40, 78), dur,
        intro_end=dur*0.30, keep=0.20)

    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.4, key_range_low=50, key_range_high=86),
        pattern="arpeggio", direction="up", octave_span=4).render(chords, key, dur), 38, 74), dur)

    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.3, key_range_low=50, key_range_high=72),
        voice_count=6, dynamics="p", syllable="ooh").render(chords, key, dur), 38, 70), dur)

    horns = _thin(_clamp(FrenchHornGenerator(
        GeneratorParams(density=0.3, key_range_low=43, key_range_high=60),
        articulation="legato").render(chords, key, dur), 42, 78), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.3, key_range_low=43, key_range_high=67),
        section_size="full", dynamic_shape="cresc_dim").render(chords, key, dur), 38, 74), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.55, key_range_low=24, key_range_high=36),
        articulation="legato").render(chords, key, dur), 45, 75)

    return {
        "Lead": _clamp(lead, 50, 85), "Glock": glock, "Harp": harp,
        "Choir": choir, "Horns": horns, "Strings": strings, "Bass": bass,
    }, bpm


# ---------------------------------------------------------------------------
# Instrument GM program maps per track
# ---------------------------------------------------------------------------

TRACKS = [
    (track_01_hagia_sophia, "01_Hagia_Sophia_at_Dawn.mid", {
        "Lead": 71, "Choir": 52, "Ney": 77, "Strings": 48,
        "Cello": 42, "Bass": 43, "Drone": 43,
    }),
    (track_02_isfahan, "02_Gardens_of_Isfahan.mid", {
        "Lead": 71, "Harp": 46, "Ney": 77, "Oud": 105,
        "Strings": 48, "Bass": 43, "Drone": 43,
    }),
    (track_03_yaman, "03_Raga_Yaman_at_Sunset.mid", {
        "Lead": 71, "Sitar": 104, "Tabla": 115, "Tanpura": 105,
        "Strings": 48, "Drone": 43,
    }),
    (track_04_flamenco, "04_Flamenco_de_la_Luna.mid", {
        "Lead": 71, "Guitar": 24, "Cajon": 115, "Strings": 48,
        "Bass": 33, "Pedal": 43,
    }),
    (track_05_hicaz, "05_Makam_Hicaz_Gözyaşları.mid", {
        "Lead": 71, "Oud": 105, "Ney": 77, "Darbuka": 115,
        "Strings": 48, "Bass": 43, "Drone": 43,
    }),
    (track_06_eclats, "06_Éclats_sur_le_Ciel.mid", {
        "Lead": 71, "Glock": 9, "Harp": 46, "Choir": 52,
        "Horns": 60, "Strings": 48, "Bass": 43,
    }),
]


def main():
    album_dir = Path("output/album_six_worlds")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 78)
    print("      S I X   W O R L D S,   S I X   M O D E S")
    print("      A live regression suite for the CoupledHMM engine")
    print("=" * 78)
    print("  I.   Hagia Sophia at Dawn   D Byzantine       (fix #1)")
    print("  II.  Gardens of Isfahan     C Persian         (fix #1)")
    print("  III. Raga Yaman at Sunset   C Yaman           (fix #5 alias)")
    print("  IV.  Flamenco de la Luna    E Flamenco [str]  (fix #6)")
    print("  V.   Makam Hicaz            A Hicaz [µtonal]  (fix #7)")
    print("  VI.  Éclats sur le Ciel     C Messiaen-3      (fix #1+#5)")
    print("=" * 78)
    print("  NOTE: tracks IV and V emit UserWarnings — that is the intended")
    print("  behaviour of fix #6/#7 surfacing the string-mode limitation.")
    print("=" * 78)

    total_notes = 0
    for producer, filename, instruments in TRACKS:
        print("-" * 78)
        # Let the string-mode warnings surface on stderr (don't suppress).
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
    print(f"  COMPLETE: SIX WORLDS — {total_notes} notes across 6 movements")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
