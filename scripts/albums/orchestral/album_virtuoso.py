# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_virtuoso.py — VIRTUOSO: FIVE SYMPHONIC TABLEAUX

A 5-movement virtuosic orchestral suite showcasing the corrected CoupledHMM
harmonizer (emission_weight=20 — chords now track the melody) and proper GM
percussion routing (channel 9).

Each movement leads with a real generated melody line, harmonized live by the
CoupledHMM engine, then orchestrated with virtuosic textures: rapid string
runs, woodwind flourishes, brass fanfares, harp cascades, contrapuntal voices.

    I.   Aurora Borealis    (C Lydian, 92 BPM)  — shimmering, ascending
    II.  The Chase          (D Dorian, 138 BPM) — driving, virtuosic strings
    III. Cathedral of Light (F Major, 66 BPM)   — majestic, choral, brass
    IV.  Dance of Embers    (A Dorian, 126 BPM) — fiery, rhythmic, playful
    V.   Apotheosis         (D Major, 100 BPM)  — triumphant grand finale
"""

import random
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel
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
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.tuba import TubaGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.canon import CanonGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer, HMMConfig
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

random.seed(2026)

# ---------------------------------------------------------------------------
# Scales
# ---------------------------------------------------------------------------
C_LYDIAN = Scale(root=0, mode=Mode.LYDIAN)
D_DORIAN = Scale(root=2, mode=Mode.DORIAN)
F_MAJOR  = Scale(root=5, mode=Mode.MAJOR)
A_DORIAN = Scale(root=9, mode=Mode.DORIAN)
D_MAJOR  = Scale(root=2, mode=Mode.MAJOR)

# Shared harmonizer — uses the corrected emission_weight=20 default
_HARM = CoupledHMMHarmonizer(beam_width=14, chord_change="half")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _harmonize(melody: list[NoteInfo], scale: Scale, dur: float) -> list[ChordLabel]:
    """Harmonize a real melody line with the CoupledHMM engine."""
    return _HARM.harmonize(melody, scale, duration_beats=dur)


def _lead_melody(scale: Scale, dur: float, *, lo: int, hi: int,
                 density: float, seed_off: int = 0) -> list[NoteInfo]:
    """Generate a virtuosic lead melody line to harmonize against."""
    p = GeneratorParams(density=density, velocity_range=(60, 100),
                        key_range_low=lo, key_range_high=hi)
    gen = MelodyGenerator(p, phrase_length=8.0,
                          note_range_low=lo, note_range_high=hi,
                          register_smoothness=0.7, steps_probability=0.7,
                          motif_probability=0.6, phrase_contour="arch")
    # melody needs chords to render; bootstrap with a tonic-only guide first
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


def _mix(raw: dict, bpm: float, lufs: float = -14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Violin1": 0.82, "Violin2": 0.78, "Viola": 0.76, "Cello": 0.80,
        "Bass": 0.84, "Brass": 0.78, "Horns": 0.80, "Trumpet": 0.76,
        "Trombone": 0.74, "Tuba": 0.84, "Woodwinds": 0.76, "Flute": 0.74,
        "Oboe": 0.74, "Clarinet": 0.76, "Bassoon": 0.78, "Choir": 0.80,
        "Harp": 0.82, "Timpani": 0.84, "Glock": 0.74, "Bells": 0.80,
        "Tremolo": 0.76, "Pizzicato": 0.74, "Ostinato": 0.76, "Lead": 0.84,
        "Counter": 0.74, "Canon": 0.76, "Mallet": 0.74, "Pedal": 0.80,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# ===========================================================================
# I. Aurora Borealis — C Lydian, 92 BPM
#    Shimmering ascending tableau. Harp cascades, violin soaring, glock sparkle.
# ===========================================================================

def track_01_aurora():
    print("  I. Aurora Borealis")
    bpm, dur = 92.0, 96.0
    key = C_LYDIAN

    lead = _lead_melody(key, dur, lo=72, hi=91, density=0.5)
    chords = _harmonize(lead, key, dur)

    violin = _clamp(ViolinGenerator(
        GeneratorParams(density=0.45, key_range_low=67, key_range_high=91),
        articulation="legato").render(chords, key, dur), 45, 92)

    harp = _clamp(HarpGenerator(
        GeneratorParams(density=0.5, key_range_low=55, key_range_high=88),
        pattern="arpeggio", direction="up_down", octave_span=4).render(chords, key, dur), 35, 80)

    glock = _clamp(GlockenspielGenerator(
        GeneratorParams(density=0.5, key_range_low=84, key_range_high=104),
        pattern="sparkling_run", note_density=1.3).render(chords, key, dur), 40, 78)

    strings = _clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=67),
        section_size="full", dynamic_shape="cresc_dim").render(chords, key, dur), 30, 62)

    cello = _clamp(CelloGenerator(
        GeneratorParams(density=0.25, key_range_low=36, key_range_high=55),
        articulation="legato").render(chords, key, dur), 35, 65)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.45, key_range_low=28, key_range_high=43),
        articulation="legato").render(chords, key, dur), 45, 75)

    return {
        "Lead": _clamp(lead, 55, 95), "Violin1": violin, "Harp": harp,
        "Glock": glock, "Strings": strings, "Cello": cello, "Bass": bass,
    }, bpm


# ===========================================================================
# II. The Chase — D Dorian, 138 BPM
#     Driving virtuosic strings, rapid ostinato, breathless woodwind runs.
# ===========================================================================

def track_02_chase():
    print("  II. The Chase")
    bpm, dur = 138.0, 88.0
    key = D_DORIAN

    lead = _lead_melody(key, dur, lo=67, hi=88, density=0.7)
    chords = _harmonize(lead, key, dur)

    ostinato = _clamp(OstinatoGenerator(
        GeneratorParams(density=0.85, key_range_low=50, key_range_high=69),
        pattern_length=4).render(chords, key, dur), 45, 82)

    violin = _clamp(ViolinGenerator(
        GeneratorParams(density=0.7, key_range_low=67, key_range_high=91),
        articulation="spiccato").render(chords, key, dur), 50, 95)

    tremolo = _clamp(TremoloStringsGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=67),
        variant="single", bow_speed=0.22).render(chords, key, dur), 35, 68)

    flute = _clamp(FluteGenerator(
        GeneratorParams(density=0.6, key_range_low=72, key_range_high=96),
        articulation="staccato", register=3).render(chords, key, dur - 16.0), 45, 85)
    flute = _off(flute, 8.0)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.4, key_range_low=28, key_range_high=43),
        articulation="pizzicato").render(chords, key, dur), 50, 85)

    timp = _clamp(TimpaniGenerator(
        GeneratorParams(density=0.3, key_range_low=36, key_range_high=48),
        stroke_pattern="single").render(chords, key, dur), 55, 95)

    return {
        "Lead": _clamp(lead, 60, 100), "Ostinato": ostinato, "Violin1": violin,
        "Tremolo": tremolo, "Flute": flute, "Bass": bass, "Timpani": timp,
    }, bpm


# ===========================================================================
# III. Cathedral of Light — F Major, 66 BPM
#      Majestic and broad. Full choir, brass chorale, organ-like sustain.
# ===========================================================================

def track_03_cathedral():
    print("  III. Cathedral of Light")
    bpm, dur = 66.0, 104.0
    key = F_MAJOR

    lead = _lead_melody(key, dur, lo=65, hi=84, density=0.35)
    chords = _harmonize(lead, key, dur)

    choir = _clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.4, key_range_low=48, key_range_high=72),
        voice_count=6, dynamics="f", syllable="aah").render(chords, key, dur), 40, 80)

    brass = _clamp(BrassSectionGenerator(
        GeneratorParams(density=0.35, key_range_low=52, key_range_high=76),
        ensemble_mode="full", intensity=0.9).render(chords, key, dur), 45, 90)

    horns = _clamp(FrenchHornGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=67),
        articulation="legato").render(chords, key, dur), 40, 82)

    strings = _clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.35, key_range_low=55, key_range_high=79),
        section_size="full", dynamic_shape="crescendo").render(chords, key, dur), 40, 78)

    bells = _clamp(TubularBellsGenerator(
        GeneratorParams(density=0.2, key_range_low=60, key_range_high=84)
    ).render(chords, key, dur), 45, 85)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.2, key_range_low=28, key_range_high=43),
        articulation="legato").render(chords, key, dur), 45, 78)

    return {
        "Lead": _clamp(lead, 50, 88), "Choir": choir, "Brass": brass,
        "Horns": horns, "Strings": strings, "Bells": bells, "Bass": bass,
    }, bpm


# ===========================================================================
# IV. Dance of Embers — A Dorian, 126 BPM
#     Fiery and playful. Pizzicato, canon, oboe/clarinet interplay, mallets.
# ===========================================================================

def track_04_embers():
    print("  IV. Dance of Embers")
    bpm, dur = 126.0, 84.0
    key = A_DORIAN

    lead = _lead_melody(key, dur, lo=64, hi=86, density=0.65)
    chords = _harmonize(lead, key, dur)

    canon = _clamp(CanonGenerator(
        GeneratorParams(density=0.5, key_range_low=60, key_range_high=84),
        num_followers=2, delay_beats=2.0).render(chords, key, dur), 45, 85)

    pizz = _clamp(StringsPizzicatoGenerator(
        GeneratorParams(density=0.7, key_range_low=48, key_range_high=72)
    ).render(chords, key, dur), 50, 88)

    oboe = _clamp(OboeGenerator(
        GeneratorParams(density=0.5, key_range_low=68, key_range_high=89),
        articulation="staccato", register=2).render(chords, key, dur - 12.0), 45, 82)
    oboe = _off(oboe, 6.0)

    clar = _clamp(ClarinetGenerator(
        GeneratorParams(density=0.45, key_range_low=55, key_range_high=79),
        articulation="staccato").render(chords, key, dur), 40, 80)

    mallet = _clamp(MalletPercussionGenerator(
        GeneratorParams(density=0.55, key_range_low=72, key_range_high=96),
        instrument="marimba", pattern="run").render(chords, key, dur), 45, 85)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.45, key_range_low=28, key_range_high=45),
        articulation="pizzicato").render(chords, key, dur), 50, 85)

    return {
        "Lead": _clamp(lead, 58, 96), "Canon": canon, "Pizzicato": pizz,
        "Oboe": oboe, "Clarinet": clar, "Mallet": mallet, "Bass": bass,
    }, bpm


# ===========================================================================
# V. Apotheosis — D Major, 100 BPM
#    Triumphant grand finale. Everyone plays. Fanfares, full tutti, timpani rolls.
# ===========================================================================

def track_05_apotheosis():
    print("  V. Apotheosis")
    bpm, dur = 100.0, 112.0
    key = D_MAJOR

    lead = _lead_melody(key, dur, lo=69, hi=91, density=0.5)
    chords = _harmonize(lead, key, dur)

    trumpet = _clamp(TrumpetGenerator(
        GeneratorParams(density=0.45, key_range_low=60, key_range_high=84),
        register=2, fanfare_mode=True).render(chords, key, dur), 55, 100)

    brass = _clamp(BrassSectionGenerator(
        GeneratorParams(density=0.4, key_range_low=48, key_range_high=72),
        ensemble_mode="full", intensity=0.9).render(chords, key, dur), 50, 98)

    violin = _clamp(ViolinGenerator(
        GeneratorParams(density=0.6, key_range_low=67, key_range_high=91),
        articulation="legato").render(chords, key, dur), 50, 95)

    strings = _clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.4, key_range_low=48, key_range_high=72),
        section_size="full", dynamic_shape="crescendo").render(chords, key, dur), 45, 85)

    choir = _clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.35, key_range_low=50, key_range_high=74),
        voice_count=6, dynamics="ff", syllable="aah").render(chords, key, dur), 45, 88)

    harp = _clamp(HarpGenerator(
        GeneratorParams(density=0.65, key_range_low=48, key_range_high=84),
        pattern="arpeggio", direction="up_down").render(chords, key, dur), 40, 82)

    glock = _clamp(GlockenspielGenerator(
        GeneratorParams(density=0.5, key_range_low=88, key_range_high=104),
        pattern="sparkling_run", note_density=1.2).render(chords, key, dur), 45, 82)

    tuba = _clamp(TubaGenerator(
        GeneratorParams(density=0.3, key_range_low=28, key_range_high=46)
    ).render(chords, key, dur), 50, 88)

    timp = _clamp(TimpaniGenerator(
        GeneratorParams(density=0.4, key_range_low=36, key_range_high=48),
        stroke_pattern="roll").render(chords, key, dur), 55, 100)

    return {
        "Lead": _clamp(lead, 60, 100), "Trumpet": trumpet, "Brass": brass,
        "Violin1": violin, "Strings": strings, "Choir": choir,
        "Harp": harp, "Glock": glock, "Tuba": tuba, "Timpani": timp,
    }, bpm


# ---------------------------------------------------------------------------
# Instrument GM program maps per track
# ---------------------------------------------------------------------------

TRACKS = [
    (track_01_aurora, "01_Aurora_Borealis.mid", {
        "Lead": 40, "Violin1": 40, "Harp": 46, "Glock": 9,
        "Strings": 48, "Cello": 42, "Bass": 43,
    }),
    (track_02_chase, "02_The_Chase.mid", {
        "Lead": 40, "Ostinato": 45, "Violin1": 40, "Tremolo": 44,
        "Flute": 73, "Bass": 43, "Timpani": 47,
    }),
    (track_03_cathedral, "03_Cathedral_of_Light.mid", {
        "Lead": 73, "Choir": 52, "Brass": 61, "Horns": 60,
        "Strings": 48, "Bells": 14, "Bass": 43,
    }),
    (track_04_embers, "04_Dance_of_Embers.mid", {
        "Lead": 68, "Canon": 71, "Pizzicato": 45, "Oboe": 68,
        "Clarinet": 71, "Mallet": 13, "Bass": 43,
    }),
    (track_05_apotheosis, "05_Apotheosis.mid", {
        "Lead": 40, "Trumpet": 56, "Brass": 61, "Violin1": 40,
        "Strings": 48, "Choir": 52, "Harp": 46, "Glock": 9, "Tuba": 58, "Timpani": 47,
    }),
]


def main():
    album_dir = Path("output/album_virtuoso")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 78)
    print("      V I R T U O S O :   F I V E   S Y M P H O N I C   T A B L E A U X")
    print("      Harmonized live by the corrected CoupledHMM engine")
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
            validate_form=True,
        )
        nc = sum(len(n) for n in raw.values())
        total_notes += nc
        print(f"    -> {filename}  ({nc} notes, {bpm:.0f} BPM)")

    print()
    print("=" * 78)
    print(f"  COMPLETE: VIRTUOSO — {total_notes} notes across 5 movements")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
