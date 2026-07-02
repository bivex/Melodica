# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_sikah_rhapsody.py — SIKAH RHAPSODY: FIVE MOVEMENTS ON MAQAM SIKAH

A 5-movement suite built on Maqam Sikah and its principal branches (Sikah,
Huzam, Iraq), the characteristic Arabic maqamat whose tonic sits on a
half-flat degree in authentic practice. Here the melodic interval set is
realized on the 12-tone grid as the Sikah pitch-class collection.

Maqam Sikah's sayr (melodic path): the tonic is emphasized, the melody rises
through the jins (E-F half-step, F-G), dwells on the ghammaz (B / 5th), and
descends back. The cadential phrases resolve via the characteristic Arabic
cadences — the salām (return to tonic) and the rakbahan descents.

Each movement transposes Sikah and modulates among its branches for variety:

    I.   Sikah        (E, the canonical maqam) — rhapsodic, contemplative
    II.  Huzam        (A, lower jins shift)   — lamenting, plaintive
    III. Sikah Baladi (D, folk colour)        — energetic, dance-like
    IV.  Iraq         (B, modal shift)        — mysterious, distant
    V.   Sikah return (E, grand)              — climactic return home

Drone: the Arabic īqāʿ is underpinned by a sustained tonic + 4th/5th drone
(jins foundation), played by DroneGenerator.
"""

import random
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.orchestral_strings import (
    ViolinGenerator,
    ViolaGenerator,
    CelloGenerator,
    ContrabassGenerator,
)
from melodica.generators.orchestral_woodwinds import (
    FluteGenerator,
    OboeGenerator,
    ClarinetGenerator,
    BassoonGenerator,
)
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator
from melodica.generators.orchestral_percussion import (
    TimpaniGenerator,
    MalletPercussionGenerator,
)

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer, HMMConfig
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

random.seed(313)  # Sikah-flavoured seed

# ---------------------------------------------------------------------------
# Maqam scales (root = tonic pitch class). All drawn from the Sikah family.
# ---------------------------------------------------------------------------
SIKAH_E = Scale(root=4, mode=Mode.ARABIC_SIKAH)  # E Sikah (canonical)
SIKAH_A = Scale(root=9, mode=Mode.ARABIC_SIKAH)  # A Sikah -> Huzam colour
SIKAH_D = Scale(root=2, mode=Mode.ARABIC_SIKAH)  # D Sikah -> Baladi colour
SIKAH_B = Scale(root=11, mode=Mode.ARABIC_SIKAH)  # B Sikah -> Iraq colour

# chord_change="bars" for the long-breathed Arabic phrasing; cadential
# constraints resolve each phrase on the tonic (salām).
_HARM = CoupledHMMHarmonizer(beam_width=14, chord_change="bars")


# ---------------------------------------------------------------------------
# Diatonic triad qualities for Sikah (interval set [0,1,3,5,7,8,10]).
# Degrees: 0=tonic(min), 1=2nd(Maj), 2=3rd(Maj), 3=4th(min), 4=5th(dim),
#          5=6th(Maj), 6=7th(min). Identical pitch-class structure to the
#          Phrygian set, so the qualities are the same.
# ---------------------------------------------------------------------------
_DIATONIC_QUALITY = [
    Quality.MINOR,  # 0: tonic
    Quality.MAJOR,  # 1: 2nd (the Phrygian/Sikah bII colour)
    Quality.MAJOR,  # 2: 3rd
    Quality.MINOR,  # 3: 4th
    Quality.DIMINISHED,  # 4: 5th
    Quality.MAJOR,  # 5: 6th
    Quality.MINOR,  # 6: 7th
]


def _phrase_constraints(
    scale: Scale, phrases: list[list[tuple[int, int]]], form: str, dur: float
) -> list[ChordLabel]:
    """Tile cadential phrases across `dur`. Each phrase resolves on the tonic
    (the Arabic salām) so the maqam returns home at every phrase end."""
    letter_to_idx = {c: i for i, c in enumerate("ABCDEFGHIJ")}
    cycle = [phrases[letter_to_idx[c]] for c in form]
    deg = [int(d) % 12 for d in scale.degrees()]
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
                constraints.append(
                    ChordLabel(
                        root=deg[deg_idx % len(deg)],
                        quality=_DIATONIC_QUALITY[deg_idx % 7],
                        start=t,
                        duration=chord_beats,
                    )
                )
                t += bars * 4.0
    return constraints


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _harmonize(melody, scale, dur, constraints=None):
    return _HARM.harmonize(melody, scale, duration_beats=dur, constraints=constraints)


def _lead_melody(scale, dur, *, lo, hi, density):
    """Raga/maqam-flavoured lead: high steps_probability for the smooth
    sayr (melodic path) characteristic of Arabic maqam performance."""
    p = GeneratorParams(
        density=density, velocity_range=(60, 100), key_range_low=lo, key_range_high=hi
    )
    gen = MelodyGenerator(
        p,
        phrase_length=8.0,
        note_range_low=lo,
        note_range_high=hi,
        register_smoothness=0.82,
        steps_probability=0.78,
        motif_probability=0.55,
        phrase_contour="arch",
    )
    ql = scale.parse_roman("I").quality
    guide = [ChordLabel(root=scale.root, quality=ql, start=0.0, duration=dur)]
    return gen.render(guide, scale, dur)


def _clamp(notes, lo=1, hi=127):
    for n in notes:
        n.velocity = max(lo, min(hi, n.velocity))
    return notes


def _filter_range(notes, lo=1, hi=127):
    return [n for n in notes if lo <= n.pitch <= hi]


def _off(notes, offset):
    return [
        NoteInfo(pitch=n.pitch, start=n.start + offset, duration=n.duration, velocity=n.velocity)
        for n in notes
    ]


def _thin(notes, dur, *, intro_end=None, outro_start=None, keep=0.25):
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


def _mix(raw, bpm, lufs=-14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update(
        {
            "Lead": 0.84,
            "Drone": 0.82,
            "Drone2": 0.78,
            "Violin1": 0.78,
            "Viola": 0.74,
            "Cello": 0.80,
            "Bass": 0.84,
            "Strings": 0.76,
            "Tremolo": 0.74,
            "Brass": 0.78,
            "Choir": 0.80,
            "Harp": 0.78,
            "Oboe": 0.74,
            "Flute": 0.74,
            "Clarinet": 0.74,
            "Bassoon": 0.76,
            "Counter": 0.72,
            "Ostinato": 0.74,
            "Glock": 0.70,
            "Mallet": 0.72,
            "Timpani": 0.80,
            "Bells": 0.76,
        }
    )
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# ===========================================================================
# I. Sikah (canonical, E) — rhapsodic, contemplative.
#    Sayr: dwell on tonic, rise to ghammaz (5th), descend. Cadence resolves
#    via the 2nd (bII colour) -> tonic, the Sikah salām.
# ===========================================================================


def track_01_sikah():
    print("  I. Sikah (E)")
    bpm, dur = 78.0, 104.0
    key = SIKAH_E

    phrases = [
        [(0, 1), (5, 1), (1, 1), (0, 1)],
        [(0, 1), (2, 1), (1, 1), (0, 1)],
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=86, density=0.42)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    drone = _clamp(
        DroneGenerator(
            GeneratorParams(density=0.06, velocity_range=(48, 60)), variant="power", fade_in=4.0
        ).render(chords, key, dur),
        52,
        65,
    )
    drone_hi = _clamp(
        DroneGenerator(
            GeneratorParams(density=0.06, velocity_range=(40, 52)), variant="octave", fade_in=6.0
        ).render(chords, key, dur),
        40,
        52,
    )

    strings = _thin(
        _clamp(
            StringsLegatoGenerator(
                GeneratorParams(density=0.18, key_range_low=52, key_range_high=70),
                section_size="full",
                dynamic_shape="cresc_dim",
            ).render(chords, key, dur),
            35,
            66,
        ),
        dur,
    )

    oboe = _clamp(
        OboeGenerator(
            GeneratorParams(density=0.4, key_range_low=67, key_range_high=88),
            articulation="legato",
            register=2,
        ).render(chords, key, dur - 8.0),
        42,
        80,
    )
    oboe = _thin(_off(oboe, 8.0), dur)

    cello = _thin(
        _clamp(
            CelloGenerator(
                GeneratorParams(density=0.30, key_range_low=36, key_range_high=50),
                articulation="legato",
            ).render(chords, key, dur),
            38,
            66,
        ),
        dur,
    )

    counter = _thin(
        _clamp(
            CounterpointGenerator(
                GeneratorParams(density=0.18, key_range_low=62, key_range_high=80)
            ).render(chords, key, dur),
            40,
            72,
        ),
        dur,
        intro_end=dur * 0.30,
        outro_start=dur * 0.75,
        keep=0.12,
    )

    bass = _clamp(
        ContrabassGenerator(
            GeneratorParams(density=0.45, key_range_low=26, key_range_high=38),
            articulation="legato",
        ).render(chords, key, dur),
        44,
        72,
    )

    return {
        "Lead": _clamp(lead, 50, 88),
        "Drone": drone,
        "Drone2": drone_hi,
        "Strings": strings,
        "Oboe": oboe,
        "Cello": cello,
        "Counter": counter,
        "Bass": bass,
    }, bpm


# ===========================================================================
# II. Huzam (A, lower-jins shift) — lamenting, plaintive.
#    A related maqam; the cadential colour shifts. Uses the 6th and 3rd
#    as melodic centres before the salām.
# ===========================================================================


def track_02_huzam():
    print("  II. Huzam (A)")
    bpm, dur = 72.0, 100.0
    key = SIKAH_A

    phrases = [
        [(0, 1), (3, 1), (5, 1), (0, 1)],  # A: tonic - 4th - 6th - tonic
        [(0, 1), (2, 1), (3, 1), (0, 1)],  # B: tonic - 3rd - 4th - tonic
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=85, density=0.40)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    drone = _clamp(
        DroneGenerator(
            GeneratorParams(density=0.06, velocity_range=(48, 60)), variant="power", fade_in=4.0
        ).render(chords, key, dur),
        52,
        65,
    )

    violin = _thin(
        _clamp(
            ViolinGenerator(
                GeneratorParams(density=0.30, key_range_low=67, key_range_high=90),
                articulation="legato",
            ).render(chords, key, dur),
            42,
            82,
        ),
        dur,
    )

    strings = _thin(
        _clamp(
            StringsLegatoGenerator(
                GeneratorParams(density=0.16, key_range_low=54, key_range_high=70),
                section_size="full",
                dynamic_shape="cresc_dim",
            ).render(chords, key, dur),
            35,
            66,
        ),
        dur,
    )

    choir = _thin(
        _clamp(
            ChoirAahsGenerator(
                GeneratorParams(density=0.16, key_range_low=54, key_range_high=68),
                voice_count=6,
                dynamics="p",
                syllable="aah",
            ).render(chords, key, dur),
            38,
            66,
        ),
        dur,
    )

    clarinet = _thin(
        _clamp(
            ClarinetGenerator(
                GeneratorParams(density=0.22, key_range_low=60, key_range_high=78),
                articulation="legato",
            ).render(chords, key, dur),
            40,
            72,
        ),
        dur,
    )

    bass = _clamp(
        ContrabassGenerator(
            GeneratorParams(density=0.45, key_range_low=26, key_range_high=38),
            articulation="legato",
        ).render(chords, key, dur),
        44,
        72,
    )

    return {
        "Lead": _clamp(lead, 50, 86),
        "Drone": drone,
        "Violin1": violin,
        "Strings": strings,
        "Choir": choir,
        "Clarinet": clarinet,
        "Bass": bass,
    }, bpm


# ===========================================================================
# III. Sikah Baladi (D, folk colour) — energetic, dance-like.
#    Faster, rhythmic; ostinato and mallets drive a folk-ish pulse.
# ===========================================================================


def track_03_baladi():
    print("  III. Sikah Baladi (D)")
    bpm, dur = 108.0, 88.0
    key = SIKAH_D

    phrases = [
        [(0, 1), (2, 1), (5, 1), (0, 1)],  # A: tonic - 3rd - 6th - tonic
        [(0, 1), (1, 1), (2, 1), (0, 1)],  # B: tonic - 2nd - 3rd - tonic
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=66, hi=89, density=0.55)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    drone = _clamp(
        DroneGenerator(
            GeneratorParams(density=0.08, velocity_range=(50, 62)), variant="power", fade_in=3.0
        ).render(chords, key, dur),
        45,
        62,
    )

    ostinato = _thin(
        _clamp(
            OstinatoGenerator(
                GeneratorParams(density=0.55, key_range_low=52, key_range_high=66), pattern_length=4
            ).render(chords, key, dur),
            45,
            78,
        ),
        dur,
    )

    violin = _thin(
        _clamp(
            ViolinGenerator(
                GeneratorParams(density=0.45, key_range_low=67, key_range_high=91),
                articulation="spiccato",
            ).render(chords, key, dur),
            48,
            88,
        ),
        dur,
    )

    flute = _clamp(
        FluteGenerator(
            GeneratorParams(density=0.45, key_range_low=72, key_range_high=96),
            articulation="staccato",
            register=2,
        ).render(chords, key, dur - 10.0),
        44,
        84,
    )
    flute = _thin(_off(flute, 6.0), dur)

    mallet = _thin(
        _clamp(
            MalletPercussionGenerator(
                GeneratorParams(density=0.45, key_range_low=72, key_range_high=96),
                instrument="marimba",
                pattern="run",
            ).render(chords, key, dur),
            44,
            82,
        ),
        dur,
    )

    strings = _thin(
        _clamp(
            StringsLegatoGenerator(
                GeneratorParams(density=0.20, key_range_low=52, key_range_high=68),
                section_size="full",
                dynamic_shape="crescendo",
            ).render(chords, key, dur),
            38,
            72,
        ),
        dur,
        intro_end=dur * 0.25,
        outro_start=dur * 0.78,
        keep=0.12,
    )

    bass = _clamp(
        ContrabassGenerator(
            GeneratorParams(density=0.55, key_range_low=24, key_range_high=38),
            articulation="pizzicato",
        ).render(chords, key, dur),
        44,
        80,
    )

    timp = _thin(
        _clamp(
            TimpaniGenerator(
                GeneratorParams(density=0.30, key_range_low=38, key_range_high=52),
                stroke_pattern="single",
            ).render(chords, key, dur),
            55,
            90,
        ),
        dur,
    )

    return {
        "Lead": _clamp(lead, 55, 92),
        "Drone": drone,
        "Ostinato": ostinato,
        "Violin1": violin,
        "Flute": flute,
        "Mallet": mallet,
        "Strings": strings,
        "Bass": bass,
        "Timpani": timp,
    }, bpm


# ===========================================================================
# IV. Iraq (B, modal shift) — mysterious, distant.
#    Slow, spacious; the modal centre on B gives a darker, more remote colour.
# ===========================================================================


def track_04_iraq():
    print("  IV. Iraq (B)")
    bpm, dur = 68.0, 108.0
    key = SIKAH_B

    phrases = [
        [(0, 1), (5, 1), (1, 1), (0, 1)],  # A: tonic - 6th - 2nd - tonic
        [(0, 1), (6, 1), (5, 1), (0, 1)],  # B: tonic - 7th - 6th - tonic
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=85, density=0.38)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    drone = _clamp(
        DroneGenerator(
            GeneratorParams(density=0.06, velocity_range=(48, 60)), variant="power", fade_in=5.0
        ).render(chords, key, dur),
        42,
        60,
    )
    drone_hi = _clamp(
        DroneGenerator(
            GeneratorParams(density=0.06, velocity_range=(38, 52)), variant="octave", fade_in=7.0
        ).render(chords, key, dur),
        36,
        52,
    )

    strings = _thin(
        _clamp(
            StringsLegatoGenerator(
                GeneratorParams(density=0.16, key_range_low=52, key_range_high=68),
                section_size="full",
                dynamic_shape="cresc_dim",
            ).render(chords, key, dur),
            32,
            64,
        ),
        dur,
    )

    tremolo = _thin(
        _clamp(
            TremoloStringsGenerator(
                GeneratorParams(density=0.12, key_range_low=52, key_range_high=66),
                variant="single",
                bow_speed=0.20,
            ).render(chords, key, dur),
            30,
            60,
        ),
        dur,
    )

    bassoon = _thin(
        _clamp(
            BassoonGenerator(
                GeneratorParams(density=0.28, key_range_low=38, key_range_high=54),
                articulation="legato",
            ).render(chords, key, dur),
            38,
            70,
        ),
        dur,
    )

    choir = _thin(
        _clamp(
            ChoirAahsGenerator(
                GeneratorParams(density=0.18, key_range_low=52, key_range_high=66),
                voice_count=6,
                dynamics="p",
                syllable="aah",
            ).render(chords, key, dur),
            36,
            64,
        ),
        dur,
    )

    harp = _thin(
        _clamp(
            HarpGenerator(
                GeneratorParams(density=0.05, key_range_low=62, key_range_high=78),
                pattern="arpeggio",
                direction="up_down",
                octave_span=2,
            ).render(chords, key, dur),
            36,
            68,
        ),
        dur,
        intro_end=dur * 0.20,
        outro_start=dur * 0.80,
        keep=0.10,
    )

    bass = _clamp(
        ContrabassGenerator(
            GeneratorParams(density=0.45, key_range_low=24, key_range_high=36),
            articulation="legato",
        ).render(chords, key, dur),
        40,
        70,
    )

    return {
        "Lead": _clamp(lead, 50, 86),
        "Drone": drone,
        "Drone2": drone_hi,
        "Strings": strings,
        "Tremolo": tremolo,
        "Bassoon": bassoon,
        "Choir": choir,
        "Harp": harp,
        "Bass": bass,
    }, bpm


# ===========================================================================
# V. Sikah return (E, grand) — climactic return home.
#    Full forces; the canonical E Sikah returns, brass and timpani added for
#    the climactic salām.
# ===========================================================================


def track_05_return():
    print("  V. Sikah return (E)")
    bpm, dur = 84.0, 112.0
    key = SIKAH_E

    phrases = [
        [(0, 1), (5, 1), (1, 1), (0, 1)],  # A: tonic - 6th - 2nd - tonic
        [(0, 1), (2, 1), (1, 1), (0, 1)],  # B: tonic - 3rd - 2nd - tonic
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=88, density=0.48)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    drone = _clamp(
        DroneGenerator(
            GeneratorParams(density=0.05, velocity_range=(48, 60)), variant="power", fade_in=4.0
        ).render(chords, key, dur),
        52,
        62,
    )

    brass = _thin(
        _clamp(
            BrassSectionGenerator(
                GeneratorParams(density=0.15, key_range_low=58, key_range_high=72),
                ensemble_mode="full",
                intensity=0.85,
            ).render(chords, key, dur - 6.0),
            50,
            84,
        ),
        dur,
    )

    violin = _thin(
        _clamp(
            ViolinGenerator(
                GeneratorParams(density=0.30, key_range_low=69, key_range_high=93),
                articulation="legato",
            ).render(chords, key, dur),
            48,
            88,
        ),
        dur,
    )

    strings = _thin(
        _clamp(
            StringsLegatoGenerator(
                GeneratorParams(density=0.12, key_range_low=56, key_range_high=72),
                section_size="full",
                dynamic_shape="crescendo",
            ).render(chords, key, dur),
            38,
            72,
        ),
        dur,
        intro_end=dur * 0.20,
        outro_start=dur * 0.80,
        keep=0.10,
    )

    choir = _thin(
        _clamp(
            ChoirAahsGenerator(
                GeneratorParams(density=0.14, key_range_low=52, key_range_high=66),
                voice_count=6,
                dynamics="f",
                syllable="aah",
            ).render(chords, key, dur),
            36,
            74,
        ),
        dur,
    )

    oboe = _clamp(
        OboeGenerator(
            GeneratorParams(density=0.25, key_range_low=69, key_range_high=88),
            articulation="legato",
            register=2,
        ).render(chords, key, dur - 8.0),
        42,
        78,
    )
    oboe = _thin(_off(oboe, 8.0), dur)

    harp = _thin(
        _filter_range(
            _clamp(
                HarpGenerator(
                    GeneratorParams(density=0.5, key_range_low=66, key_range_high=82),
                    pattern="rolled_chord",
                    direction="up",
                ).render(chords, key, dur),
                42,
                80,
            ),
            62,
            82,
        ),
        dur,
        intro_end=dur * 0.15,
        outro_start=dur * 0.82,
        keep=0.08,
    )

    bass = _clamp(
        ContrabassGenerator(
            GeneratorParams(density=0.40, key_range_low=24, key_range_high=40),
            articulation="legato",
        ).render(chords, key, dur),
        36,
        56,
    )

    timp = _thin(
        _clamp(
            TimpaniGenerator(
                GeneratorParams(density=0.22, key_range_low=44, key_range_high=58),
                stroke_pattern="single",
            ).render(chords, key, dur),
            50,
            84,
        ),
        dur,
    )

    brass = _thin(
        _clamp(
            BrassSectionGenerator(
                GeneratorParams(density=0.18, key_range_low=52, key_range_high=68),
                ensemble_mode="full",
                intensity=0.85,
            ).render(chords, key, dur - 6.0),
            48,
            82,
        ),
        dur,
    )

    violin = _thin(
        _clamp(
            ViolinGenerator(
                GeneratorParams(density=0.35, key_range_low=67, key_range_high=91),
                articulation="legato",
            ).render(chords, key, dur),
            48,
            88,
        ),
        dur,
    )

    strings = _thin(
        _clamp(
            StringsLegatoGenerator(
                GeneratorParams(density=0.16, key_range_low=54, key_range_high=70),
                section_size="full",
                dynamic_shape="crescendo",
            ).render(chords, key, dur),
            38,
            72,
        ),
        dur,
    )

    choir = _thin(
        _clamp(
            ChoirAahsGenerator(
                GeneratorParams(density=0.18, key_range_low=54, key_range_high=68),
                voice_count=6,
                dynamics="f",
                syllable="aah",
            ).render(chords, key, dur),
            38,
            78,
        ),
        dur,
    )

    oboe = _clamp(
        OboeGenerator(
            GeneratorParams(density=0.30, key_range_low=67, key_range_high=88),
            articulation="legato",
            register=2,
        ).render(chords, key, dur - 8.0),
        42,
        78,
    )
    oboe = _thin(_off(oboe, 8.0), dur)

    bass = _clamp(
        ContrabassGenerator(
            GeneratorParams(density=0.50, key_range_low=24, key_range_high=42),
            articulation="legato",
        ).render(chords, key, dur),
        40,
        78,
    )

    timp = _thin(
        _clamp(
            TimpaniGenerator(
                GeneratorParams(density=0.28, key_range_low=42, key_range_high=56),
                stroke_pattern="single",
            ).render(chords, key, dur),
            52,
            86,
        ),
        dur,
    )

    return {
        "Lead": _clamp(lead, 52, 92),
        "Drone": drone,
        "Brass": brass,
        "Violin1": violin,
        "Strings": strings,
        "Choir": choir,
        "Oboe": oboe,
        "Harp": harp,
        "Bass": bass,
        "Timpani": timp,
    }, bpm


# ---------------------------------------------------------------------------
# Instrument GM program maps per track.
# Lead = oboe (68) / sitar-ish (105) for the nasal Arabic reed timbre;
# Drone = string ensemble (48) approximating the Arabic drone foundation.
# ---------------------------------------------------------------------------

TRACKS = [
    (
        track_01_sikah,
        "01_Sikah.mid",
        {
            "Lead": 68,
            "Drone": 48,
            "Drone2": 48,
            "Strings": 48,
            "Oboe": 68,
            "Cello": 42,
            "Counter": 40,
            "Bass": 43,
        },
    ),
    (
        track_02_huzam,
        "02_Huzam.mid",
        {
            "Lead": 71,
            "Drone": 48,
            "Violin1": 40,
            "Strings": 48,
            "Choir": 52,
            "Clarinet": 71,
            "Bass": 43,
        },
    ),
    (
        track_03_baladi,
        "03_Sikah_Baladi.mid",
        {
            "Lead": 68,
            "Drone": 48,
            "Ostinato": 45,
            "Violin1": 40,
            "Flute": 73,
            "Mallet": 13,
            "Strings": 48,
            "Bass": 43,
            "Timpani": 47,
        },
    ),
    (
        track_04_iraq,
        "04_Iraq.mid",
        {
            "Lead": 68,
            "Drone": 48,
            "Drone2": 48,
            "Strings": 48,
            "Tremolo": 44,
            "Bassoon": 70,
            "Choir": 52,
            "Harp": 46,
            "Bass": 43,
        },
    ),
    (
        track_05_return,
        "05_Sikah_Return.mid",
        {
            "Lead": 68,
            "Drone": 48,
            "Brass": 61,
            "Violin1": 40,
            "Strings": 48,
            "Choir": 52,
            "Oboe": 68,
            "Harp": 46,
            "Bass": 43,
            "Timpani": 47,
        },
    ),
]


def main():
    album_dir = Path("output/album_sikah_rhapsody")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 78)
    print("      S I K A H   R H A P S O D Y :   F I V E   M O V E M E N T S")
    print("      Maqam Sikah and its branches, on a tonic drone")
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
            postprocess_arr=True,
        )
        nc = sum(len(n) for n in raw.values())
        total_notes += nc
        print(f"    -> {filename}  ({nc} notes, {bpm:.0f} BPM)")

    print()
    print("=" * 78)
    print(f"  COMPLETE: SIKAH RHAPSODY — {total_notes} notes across 5 movements")
    print(f"  Maqamat: Sikah (E) | Huzam (A) | Sikah Baladi (D) | Iraq (B) | Sikah (E)")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
