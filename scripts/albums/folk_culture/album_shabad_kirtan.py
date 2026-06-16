# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_shabad_kirtan.py — SHABAD KIRTAN: FIVE RAGAS

A 5-movement suite in the canonical Sikh devotional ragas used for Gurbani
Kirtan, built on a sustained tanpura drone (Sa-Pa) with raga-based melodies
harmonized by the CoupledHMM engine and anchored by raga-cadential phrases.

Each movement is set in a raga prescribed for a time of day in the Sikh
raga-mala tradition. The cadential progressions resolve toward Sa (the
tonic) at each phrase end, the way a shabad returns to its tonal center.

    I.   Raga Bhairav   (A Bhairav thaat)    — predawn, serene, austere
    II.  Raga Yaman     (C Kalyan thaat)     — evening, romantic, raised 4th
    III. Raga Bhupali   (D Kalyan pentatonic)— night, pentatonic, peaceful
    IV.  Raga Bhairavi  (D Bhairavi thaat)   — morning, all-flat, devotional
    V.   Raga Marwa     (C Marwa thaat)      — dusk, restless, no Pa

Tuning reference: Sa = root of each raga. Drone = Sa + Pa (perfect fifth),
except Raga Marwa which traditionally omits Pa (drone = Sa + Sa' octave).
"""

import random
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
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer, HMMConfig
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

random.seed(143)  # Nanakshahi-flavoured seed

# ---------------------------------------------------------------------------
# Ragas (root = Sa, as pitch class)
# ---------------------------------------------------------------------------
BHAIRAV   = Scale(root=9,  mode=Mode.DOUBLE_HARMONIC)   # A Sa: A Bb C# D E F G#
YAMAN     = Scale(root=0,  mode=Mode.LYDIAN)            # C Sa: C D E F# G A B
BHUPALI   = Scale(root=2,  mode=Mode.BHUPALI)           # D Sa: D E F# A B (pentatonic)
BHAIRAVI  = Scale(root=2,  mode=Mode.HARMONIC_MINOR)    # D Sa: D E F G A Bb C#
MARWA     = Scale(root=0,  mode=Mode.HUNGARIAN_MINOR)   # C Sa: C D Eb F# G Ab B

# CoupledHMM harmonizer. chord_change="bars" for long, breathing phrases
# suited to kirtan; the cadential constraints resolve toward Sa each phrase.
_HARM = CoupledHMMHarmonizer(beam_width=14, chord_change="bars")


# ---------------------------------------------------------------------------
# Diatonic chord-quality table per (mode, degree index)
# Degrees: 0=Sa, 1=re, 2=Ga, 3=ma, 4=Pa, 5=dha, 6=Ni.
# Built from each raga's interval structure so cadential phrases use the
# correct chord quality (e.g. Bhairav Sa is major, re is major).
# ---------------------------------------------------------------------------
_DIATONIC_QUALITY: dict[Mode, list[Quality]] = {
    # Double Harmonic (Bhairav): Sa Maj, re Maj, Ga min, ma min, Pa Maj, dha Maj, Ni dim
    Mode.DOUBLE_HARMONIC: [Quality.MAJOR, Quality.MAJOR, Quality.MINOR, Quality.MINOR, Quality.MAJOR, Quality.MAJOR, Quality.DIMINISHED],
    # Lydian (Yaman): all major/minor per the raised-4th scale
    Mode.LYDIAN:          [Quality.MAJOR, Quality.MAJOR, Quality.MINOR, Quality.DIMINISHED, Quality.MAJOR, Quality.MAJOR, Quality.MINOR],
    # Bhupali (pentatonic): 5 degrees — Sa Maj, re Maj, Ga Maj(unused), ma Maj, Pa Maj
    Mode.BHUPALI:         [Quality.MAJOR, Quality.MAJOR, Quality.MINOR, Quality.MAJOR, Quality.MAJOR],
    # Harmonic minor (Bhairavi)
    Mode.HARMONIC_MINOR:  [Quality.MINOR, Quality.DIMINISHED, Quality.AUGMENTED, Quality.MINOR, Quality.MINOR, Quality.MAJOR, Quality.DIMINISHED],
    # Hungarian minor (Marwa)
    Mode.HUNGARIAN_MINOR: [Quality.MINOR, Quality.MAJOR, Quality.AUGMENTED, Quality.MAJOR, Quality.MAJOR, Quality.MAJOR, Quality.DIMINISHED],
}


def _phrase_constraints(scale: Scale, phrases: list[list[tuple[int, int]]],
                        form: str, dur: float) -> list[ChordLabel]:
    """Tile phrases across `dur` beats following a form (e.g. 'AAB').

    phrases: list of phrase specs; each spec is [(degree_index, bars), ...].
    form: letters (A=0, B=1, ...) selecting phrases, repeated to fill `dur`.
    Each phrase resolves on Sa (degree 0) so the raga returns to its tonic.
    """
    letter_to_idx = {c: i for i, c in enumerate("ABCDEFGHIJ")}
    cycle = [phrases[letter_to_idx[c]] for c in form]
    deg = [d % 12 for d in scale.degrees()]
    qualities = _DIATONIC_QUALITY[scale.mode]
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
                constraints.append(ChordLabel(
                    root=deg[deg_idx % len(deg)],
                    quality=qualities[deg_idx % len(qualities)],
                    start=t, duration=chord_beats,
                ))
                t += bars * 4.0
    return constraints


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _harmonize(melody: list[NoteInfo], scale: Scale, dur: float,
               constraints: list[ChordLabel] | None = None) -> list[ChordLabel]:
    """Harmonize a melody with the CoupledHMM engine, cadential-phrase locked."""
    return _HARM.harmonize(melody, scale, duration_beats=dur, constraints=constraints)


def _lead_melody(scale: Scale, dur: float, *, lo: int, hi: int,
                 density: float) -> list[NoteInfo]:
    """Generate a raga-flavoured lead melody line to harmonize against.

    Steps-heavy (steps_probability high) for the smooth, meandering motion
    characteristic of alap/gat; arch contour for the rise-and-return of a shabad.
    """
    p = GeneratorParams(density=density, velocity_range=(60, 100),
                        key_range_low=lo, key_range_high=hi)
    gen = MelodyGenerator(p, phrase_length=8.0,
                          note_range_low=lo, note_range_high=hi,
                          register_smoothness=0.8, steps_probability=0.8,
                          motif_probability=0.55, phrase_contour="arch")
    ql = scale.parse_roman("I").quality
    guide = [ChordLabel(root=scale.root, quality=ql, start=0.0, duration=dur)]
    return gen.render(guide, scale, dur)


def _clamp(notes: list[NoteInfo], lo: int = 1, hi: int = 127) -> list[NoteInfo]:
    for n in notes:
        n.velocity = max(lo, min(hi, n.velocity))
    return notes


def _thin(notes: list[NoteInfo], dur: float, *,
          intro_end: float | None = None,
          outro_start: float | None = None,
          keep: float = 0.25) -> list[NoteInfo]:
    """Drop a fraction of notes in intro/outro windows for an energy curve."""
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
        "Lead": 0.84, "Tanpura": 0.82, "Tanpura2": 0.80, "Violin1": 0.78,
        "Viola": 0.74, "Cello": 0.80, "Bass": 0.84, "Strings": 0.76,
        "Tremolo": 0.74, "Choir": 0.80, "Harp": 0.78, "Flute": 0.74,
        "Oboe": 0.74, "Clarinet": 0.74, "Bassoon": 0.76, "Counter": 0.72,
        "Glock": 0.70, "Bells": 0.76, "Timpani": 0.80, "Ostinato": 0.74,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# ===========================================================================
# I. Raga Bhairav — predawn, serene, austere.
#    The double-harmonic augmented seconds (Sa-re, Pa-dha) give the
#    characteristic reverent, solemn color of early-morning kirtan.
#    Cadence: Sa - dha(Ni) - re - Sa  (the re->Sa flat-second resolves home).
# ===========================================================================

def track_01_bhairav():
    print("  I. Raga Bhairav (A Bhairav)")
    bpm, dur = 66.0, 108.0
    key = BHAIRAV

    # Sa-re-ma-Sa cadential phrases. A: Sa-dha-re-Sa; B: Sa-ma-re-Sa.
    # Both resolve via re (Bb) -> Sa (A), the Bhairav signature.
    phrases = [
        [(0, 1), (5, 1), (1, 1), (0, 1)],   # A: Sa - dha - re - Sa
        [(0, 1), (3, 1), (1, 1), (0, 1)],   # B: Sa - ma - re - Sa
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=84, density=0.38)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    # Tanpura drone: Sa (A2=45) + Pa (E3=52), sustained throughout
    tanpura = DroneGenerator(GeneratorParams(density=0.1, velocity_range=(55, 70)),
                             variant="power", fade_in=4.0).render(chords, key, dur)
    # A second, softer drone an octave up for shimmer
    tanpura_hi = _clamp(DroneGenerator(
        GeneratorParams(density=0.1, velocity_range=(45, 60)),
        variant="octave", fade_in=6.0).render(chords, key, dur), 40, 62)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.28, key_range_low=50, key_range_high=70),
        section_size="full", dynamic_shape="cresc_dim").render(chords, key, dur), 35, 68), dur)

    cello = _thin(_clamp(CelloGenerator(
        GeneratorParams(density=0.35, key_range_low=38, key_range_high=52),
        articulation="legato").render(chords, key, dur), 38, 70), dur)

    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.3, key_range_low=50, key_range_high=70),
        voice_count=6, dynamics="p", syllable="aah").render(chords, key, dur), 38, 70), dur)

    oboe = _clamp(OboeGenerator(
        GeneratorParams(density=0.35, key_range_low=67, key_range_high=88),
        articulation="legato", register=2).render(chords, key, dur - 8.0), 42, 78)
    oboe = _thin(_off(oboe, 8.0), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.5, key_range_low=26, key_range_high=38),
        articulation="legato").render(chords, key, dur), 44, 76)

    return {
        "Lead": _clamp(lead, 50, 88), "Tanpura": tanpura, "Tanpura2": tanpura_hi,
        "Strings": strings, "Cello": cello, "Choir": choir, "Oboe": oboe, "Bass": bass,
    }, bpm


def _off(notes, offset):
    return [NoteInfo(pitch=n.pitch, start=n.start + offset,
                     duration=n.duration, velocity=n.velocity) for n in notes]


# ===========================================================================
# II. Raga Yaman — evening, romantic, the raised 4th (ma = F#) is the vadi.
#    All shuddha (natural) except tivra ma. Lyrical, ascending.
#    Cadence: Sa - Ni(upper) - re - Sa, and Sa - Ga - re - Sa.
# ===========================================================================

def track_02_yaman():
    print("  II. Raga Yaman (C Kalyan)")
    bpm, dur = 80.0, 100.0
    key = YAMAN

    phrases = [
        [(0, 1), (6, 1), (1, 1), (0, 1)],   # A: Sa - Ni - re - Sa
        [(0, 1), (2, 1), (1, 1), (0, 1)],   # B: Sa - Ga - re - Sa
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=65, hi=88, density=0.45)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    tanpura = DroneGenerator(GeneratorParams(density=0.1, velocity_range=(55, 70)),
                             variant="power", fade_in=4.0).render(chords, key, dur)

    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.45, key_range_low=67, key_range_high=91),
        articulation="legato").render(chords, key, dur), 45, 86), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.3, key_range_low=52, key_range_high=72),
        section_size="full", dynamic_shape="crescendo").render(chords, key, dur), 38, 76), dur)

    flute = _clamp(FluteGenerator(
        GeneratorParams(density=0.4, key_range_low=72, key_range_high=96),
        articulation="legato", register=2).render(chords, key, dur - 8.0), 42, 80)
    flute = _thin(_off(flute, 8.0), dur)

    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.25, key_range_low=50, key_range_high=84),
        pattern="arpeggio", direction="up_down", octave_span=3).render(chords, key, dur), 38, 74), dur)

    cello = _thin(_clamp(CelloGenerator(
        GeneratorParams(density=0.3, key_range_low=40, key_range_high=55),
        articulation="legato").render(chords, key, dur), 40, 72), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.55, key_range_low=26, key_range_high=38),
        articulation="legato").render(chords, key, dur), 46, 78)

    return {
        "Lead": _clamp(lead, 52, 90), "Tanpura": tanpura, "Violin1": violin,
        "Strings": strings, "Flute": flute, "Harp": harp, "Cello": cello, "Bass": bass,
    }, bpm


# ===========================================================================
# III. Raga Bhupali — night, pentatonic (Sa re Ga Pa Dha), peaceful.
#    Auduva-sampurna (5-note ascent, 6-note descent). No ma, no Ni-flat.
#    Pentatonic means no half-steps; cadences resolve gently via Dha->Sa.
# ===========================================================================

def track_03_bhupali():
    print("  III. Raga Bhupali (D Kalyan pentatonic)")
    bpm, dur = 76.0, 96.0
    key = BHUPALI

    # Pentatonic degrees: 0=Sa(D), 1=re(E), 2=Ga(F#), 3=Pa(A), 4=Dha(B)
    phrases = [
        [(0, 1), (3, 1), (4, 1), (0, 1)],   # A: Sa - Pa - Dha - Sa
        [(0, 1), (2, 1), (4, 1), (0, 1)],   # B: Sa - Ga - Dha - Sa
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=66, hi=89, density=0.42)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    tanpura = DroneGenerator(GeneratorParams(density=0.1, velocity_range=(55, 70)),
                             variant="power", fade_in=4.0).render(chords, key, dur)

    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.4, key_range_low=68, key_range_high=90),
        articulation="legato").render(chords, key, dur), 44, 84), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.28, key_range_low=50, key_range_high=70),
        section_size="full", dynamic_shape="cresc_dim").render(chords, key, dur), 36, 70), dur)

    clarinet = _thin(_clamp(ClarinetGenerator(
        GeneratorParams(density=0.4, key_range_low=55, key_range_high=79),
        articulation="legato").render(chords, key, dur), 42, 78), dur)

    counter = _thin(_clamp(CounterpointGenerator(
        GeneratorParams(density=0.22, key_range_low=60, key_range_high=84)
    ).render(chords, key, dur), 40, 78), dur, intro_end=dur*0.30, outro_start=dur*0.75, keep=0.15)

    glock_raw = _clamp(GlockenspielGenerator(
        GeneratorParams(density=0.25, key_range_low=84, key_range_high=104),
        pattern="sparkling_run", note_density=0.7).render(chords, key, dur - 12.0), 36, 66)
    glock = _thin(_off(glock_raw, 12.0), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.5, key_range_low=26, key_range_high=40),
        articulation="legato").render(chords, key, dur), 44, 76)

    return {
        "Lead": _clamp(lead, 50, 88), "Tanpura": tanpura, "Violin1": violin,
        "Strings": strings, "Clarinet": clarinet, "Counter": counter,
        "Glock": glock, "Bass": bass,
    }, bpm


# ===========================================================================
# IV. Raga Bhairavi — morning, devotional, all svaras komal (flat) except Sa-Pa.
#    The most beloved raga for Sikh kirtan; can be sung any time but prescribed
#    for morning. Cadence: Sa - dha - re(komal) - Sa.
# ===========================================================================

def track_04_bhairavi():
    print("  IV. Raga Bhairavi (D Bhairavi)")
    bpm, dur = 72.0, 104.0
    key = BHAIRAVI

    phrases = [
        [(0, 1), (5, 1), (1, 1), (0, 1)],   # A: Sa - dha - re - Sa
        [(0, 1), (4, 1), (5, 1), (0, 1)],   # B: Sa - Pa - dha - Sa
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=86, density=0.42)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    tanpura = DroneGenerator(GeneratorParams(density=0.1, velocity_range=(55, 70)),
                             variant="power", fade_in=4.0).render(chords, key, dur)
    tanpura_hi = _clamp(DroneGenerator(
        GeneratorParams(density=0.1, velocity_range=(45, 58)),
        variant="octave", fade_in=6.0).render(chords, key, dur), 40, 60)

    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.32, key_range_low=50, key_range_high=72),
        voice_count=6, dynamics="p", syllable="aah").render(chords, key, dur), 38, 72), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.28, key_range_low=50, key_range_high=70),
        section_size="full", dynamic_shape="cresc_dim").render(chords, key, dur), 35, 68), dur)

    cello = _thin(_clamp(CelloGenerator(
        GeneratorParams(density=0.35, key_range_low=38, key_range_high=52),
        articulation="legato").render(chords, key, dur), 38, 70), dur)

    bassoon = _thin(_clamp(BassoonGenerator(
        GeneratorParams(density=0.35, key_range_low=36, key_range_high=55),
        articulation="legato").render(chords, key, dur), 40, 74), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.5, key_range_low=26, key_range_high=38),
        articulation="legato").render(chords, key, dur), 44, 76)

    return {
        "Lead": _clamp(lead, 50, 88), "Tanpura": tanpura, "Tanpura2": tanpura_hi,
        "Choir": choir, "Strings": strings, "Cello": cello, "Bassoon": bassoon, "Bass": bass,
    }, bpm


# ===========================================================================
# V. Raga Marwa — dusk, restless, poignant. Omits Pa (no perfect fifth degree),
#    creating a suspended, yearning character. Drone = Sa + Sa' (octave, no Pa).
#    Cadence: Sa - Ga - re - Sa, and Sa - Ni - re - Sa.
# ===========================================================================

def track_05_marwa():
    print("  V. Raga Marwa (C Marwa)")
    bpm, dur = 70.0, 108.0
    key = MARWA

    phrases = [
        [(0, 1), (2, 1), (1, 1), (0, 1)],   # A: Sa - Ga - re - Sa
        [(0, 1), (6, 1), (1, 1), (0, 1)],   # B: Sa - Ni - re - Sa
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=86, density=0.4)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    # Marwa omits Pa: drone = Sa + octave (not the usual Sa-Pa power drone)
    tanpura = DroneGenerator(GeneratorParams(density=0.1, velocity_range=(55, 70)),
                             variant="octave", fade_in=5.0).render(chords, key, dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.3, key_range_low=50, key_range_high=72),
        section_size="full", dynamic_shape="cresc_dim").render(chords, key, dur), 36, 70), dur)

    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.4, key_range_low=67, key_range_high=90),
        articulation="legato").render(chords, key, dur), 44, 84), dur)

    tremolo = _thin(_clamp(TremoloStringsGenerator(
        GeneratorParams(density=0.28, key_range_low=48, key_range_high=65),
        variant="single", bow_speed=0.22).render(chords, key, dur), 34, 64), dur)

    oboe = _clamp(OboeGenerator(
        GeneratorParams(density=0.35, key_range_low=67, key_range_high=88),
        articulation="legato", register=2).render(chords, key, dur - 8.0), 42, 78)
    oboe = _thin(_off(oboe, 8.0), dur)

    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.28, key_range_low=50, key_range_high=70),
        voice_count=6, dynamics="p", syllable="aah").render(chords, key, dur), 38, 68), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.5, key_range_low=26, key_range_high=38),
        articulation="legato").render(chords, key, dur), 44, 76)

    return {
        "Lead": _clamp(lead, 50, 88), "Tanpura": tanpura, "Strings": strings,
        "Violin1": violin, "Tremolo": tremolo, "Oboe": oboe, "Choir": choir, "Bass": bass,
    }, bpm


# ---------------------------------------------------------------------------
# Instrument GM program maps per track.
# Drone/Tanpura: use a sustained reed (72 = oboe-like) or string ensemble (48)
# to approximate the buzzy tanpura timbre. Lead = sitar-ish banjo (105) for I/IV,
# flute/strings elsewhere where a bowed-reed tone fits the raga better.
# ---------------------------------------------------------------------------

TRACKS = [
    (track_01_bhairav, "01_Raga_Bhairav.mid", {
        "Lead": 105, "Tanpura": 48, "Tanpura2": 48, "Strings": 48,
        "Cello": 42, "Choir": 52, "Oboe": 68, "Bass": 43,
    }),
    (track_02_yaman, "02_Raga_Yaman.mid", {
        "Lead": 73, "Tanpura": 48, "Violin1": 40, "Strings": 48,
        "Flute": 73, "Harp": 46, "Cello": 42, "Bass": 43,
    }),
    (track_03_bhupali, "03_Raga_Bhupali.mid", {
        "Lead": 105, "Tanpura": 48, "Violin1": 40, "Strings": 48,
        "Clarinet": 71, "Counter": 40, "Glock": 9, "Bass": 43,
    }),
    (track_04_bhairavi, "04_Raga_Bhairavi.mid", {
        "Lead": 105, "Tanpura": 48, "Tanpura2": 48, "Choir": 52,
        "Strings": 48, "Cello": 42, "Bassoon": 70, "Bass": 43,
    }),
    (track_05_marwa, "05_Raga_Marwa.mid", {
        "Lead": 73, "Tanpura": 48, "Strings": 48, "Violin1": 40,
        "Tremolo": 44, "Oboe": 68, "Choir": 52, "Bass": 43,
    }),
]


def main():
    album_dir = Path("output/album_shabad_kirtan")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 78)
    print("      S H A B A D   K I T A N :   F I V E   R A G A S")
    print("      Gurbani-kirtan ragas on a tanpura drone")
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
    print(f"  COMPLETE: SHABAD KIRTAN — {total_notes} notes across 5 ragas")
    print(f"  Ragas: Bhairav | Yaman | Bhupali | Bhairavi | Marwa")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
