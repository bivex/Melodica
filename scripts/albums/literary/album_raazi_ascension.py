# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_raazi_ascension.py — RAAZI: ASCENSION

A 5-track hip-hop beat tape tracing Raazi's rise from the bottom — the block,
the hustle, the drill, the phonk-laced climb, and the triumphant summit.
Each track is a distinct sub-genre matching a stage of the come-up:

    I.   Concrete (The Block)     Lo-Fi      — cold mornings, nothing yet
    II.  Nickel Bag (The Hustle)  Trap       — first money, hi-hat rolls
    III. Slide (The Drill)        UK Drill   — 808 slides, dark, no hesitation
    IV.  Smoke (The Climb)        Phonk      — cowbells, Memphis drift
    V.   Crown (The Summit)       Trap/Epic  — triumphant, strings, the top

All beats are harmonized live by the CoupledHMM engine over minor-key
progressions, with trap drums, 808s, vocal chops, and dark leads.
"""

import random
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.phonk import PhonkGenerator
from melodica.generators.drill_pattern import DrillPatternGenerator
from melodica.generators.lofi_hiphop import LoFiHipHopGenerator
from melodica.generators.rage_beat import RageBeatGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.vocal_adlibs import VocalAdlibsGenerator
from melodica.generators.synth_modern import SynthPadGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer, HMMConfig
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

random.seed(713)  # Raazi's block number

# ---------------------------------------------------------------------------
# Keys — the rise, all dark minor, warming only at the summit
# ---------------------------------------------------------------------------
F_MINOR      = Scale(root=5,  mode=Mode.NATURAL_MINOR)   # I + II: the cold block
G_MINOR      = Scale(root=7,  mode=Mode.NATURAL_MINOR)   # III: drill, darker
C_HARM_MINOR = Scale(root=0,  mode=Mode.HARMONIC_MINOR)  # IV: phonk tension
D_MINOR      = Scale(root=2,  mode=Mode.NATURAL_MINOR)   # V: triumphant return

_HARM = CoupledHMMHarmonizer(beam_width=14, chord_change="half")

# All hip-hop progressions are minor-key, i-VI-III-VII / i-VI-iv-V, the
# emotional backbone of trap/drill/phonk.
_DIATONIC_MINOR = [
    Quality.MINOR,      # i
    Quality.DIMINISHED, # ii°
    Quality.MAJOR,      # III
    Quality.MINOR,      # iv
    Quality.MINOR,      # v
    Quality.MAJOR,      # VI
    Quality.MAJOR,      # VII
]


def _phrase_constraints(scale, phrases, form, dur):
    """Tile AAB minor phrases. Each resolves on i (the tonic minor)."""
    letter_to_idx = {c: i for i, c in enumerate("ABCDEFGHIJ")}
    cycle = [phrases[letter_to_idx[c]] for c in form]
    deg = [int(d) % 12 for d in scale.degrees()]
    constraints = []
    t = 0.0
    while t < dur - 0.01:
        for ph in cycle:
            if t >= dur - 0.01:
                break
            for deg_idx, beats in ph:
                if t >= dur - 0.01:
                    break
                chord_beats = min(beats * 2.0, dur - t)
                constraints.append(ChordLabel(
                    root=deg[deg_idx % len(deg)],
                    quality=_DIATONIC_MINOR[deg_idx % 7],
                    start=t, duration=chord_beats,
                ))
                t += beats * 2.0
    return constraints


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _harmonize(melody, scale, dur, constraints=None):
    return _HARM.harmonize(melody, scale, duration_beats=dur, constraints=constraints)


def _lead_melody(scale, dur, *, lo, hi, density):
    """Trap-style lead — short motifs, repetition, the hook."""
    p = GeneratorParams(density=density, velocity_range=(60, 100),
                        key_range_low=lo, key_range_high=hi)
    gen = MelodyGenerator(p, phrase_length=4.0,
                          note_range_low=lo, note_range_high=hi,
                          register_smoothness=0.6, steps_probability=0.55,
                          motif_probability=0.8, phrase_contour="arch")
    ql = scale.parse_roman("I").quality
    guide = [ChordLabel(root=scale.root, quality=ql, start=0.0, duration=dur)]
    return gen.render(guide, scale, dur)


def _clamp(notes, lo=1, hi=127):
    for n in notes:
        n.velocity = max(lo, min(hi, n.velocity))
    return notes


def _off(notes, offset):
    return [NoteInfo(pitch=n.pitch, start=n.start + offset,
                     duration=n.duration, velocity=n.velocity) for n in notes]


def _thin(notes, dur, *, intro_end=None, outro_start=None, keep=0.25):
    rng = random.Random(42)
    intro_end = intro_end if intro_end is not None else dur * 0.15
    outro_start = outro_start if outro_start is not None else dur * 0.85
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
    desk.track_gains.update({
        "Lead": 0.86, "Piano": 0.80, "808": 0.90, "Drums": 0.88,
        "HiHat": 0.84, "Pad": 0.72, "DarkPad": 0.74, "VocalChop": 0.76,
        "Adlibs": 0.74, "Strings": 0.76, "SynthLead": 0.80, "PhonkBell": 0.82,
        "Glock": 0.68, "Choir": 0.74, "BassSub": 0.88,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# ===========================================================================
# I. Concrete (The Block) — Lo-Fi, F minor, 80 BPM.
#    Cold mornings, nothing yet. Lo-fi piano, dusty, the block before dawn.
#    i - VI - III - VII (the lo-fi emotional loop).
# ===========================================================================

def track_01_concrete():
    print("  I. Concrete (The Block)")
    bpm, dur = 80.0, 96.0
    key = F_MINOR

    phrases = [
        [(0, 4), (5, 4), (2, 4), (6, 4)],   # A: i - VI - III - VII (2 bars each)
        [(0, 4), (5, 4), (3, 4), (6, 4)],   # B: i - VI - iv - VII
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=60, hi=84, density=0.35)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    lofi = _clamp(LoFiHipHopGenerator(
        GeneratorParams(density=0.6, key_range_low=36, key_range_high=72),
        variant="nostalgic", swing_ratio=0.6
    ).render(chords, key, dur), 44, 84)

    # Trap drums underneath the lo-fi — the block waking up
    drums = _clamp(TrapDrumsGenerator(
        GeneratorParams(density=0.7, velocity_range=(70, 110)),
        variant="minimal", hat_roll_density=0.3
    ).render(chords, key, dur), 60, 105)

    bass808 = _clamp(Bass808SlidingGenerator(
        GeneratorParams(density=0.5, key_range_low=24, key_range_high=40),
        pattern="trap_basic", slide_type="overlap", slide_probability=0.3
    ).render(chords, key, dur), 50, 90)

    darkpad = _thin(_clamp(DarkPadGenerator(
        GeneratorParams(density=0.3, key_range_low=36, key_range_high=60),
        mode="minor_pad"
    ).render(chords, key, dur), 36, 60), dur)

    vocal = _thin(_clamp(VocalChopsGenerator(
        GeneratorParams(density=0.25, key_range_low=60, key_range_high=84),
        processing="reverse", density=0.3
    ).render(chords, key, dur - 8.0), 42, 70), dur)
    vocal = _thin(vocal, dur, keep=0.3)

    return {
        "Lead": _clamp(lead, 48, 84), "Piano": lofi, "Drums": drums,
        "808": bass808, "DarkPad": darkpad, "VocalChop": vocal,
    }, bpm


# ===========================================================================
# II. Nickel Bag (The Hustle) — Trap, F minor, 140 BPM.
#    First money. Hi-hat rolls, 808 glides, the energy picking up.
#    i - VI - iv - v (the trap bounce).
# ===========================================================================

def track_02_nickel_bag():
    print("  II. Nickel Bag (The Hustle)")
    bpm, dur = 140.0, 88.0
    key = F_MINOR

    phrases = [
        [(0, 4), (5, 4), (3, 4), (4, 4)],   # A: i - VI - iv - v
        [(0, 4), (5, 4), (6, 4), (0, 4)],   # B: i - VI - VII - i
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=60, hi=86, density=0.45)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    drums = _clamp(TrapDrumsGenerator(
        GeneratorParams(density=0.85, velocity_range=(75, 115)),
        variant="standard", hat_roll_density=0.8
    ).render(chords, key, dur), 62, 112)

    bass808 = _clamp(Bass808SlidingGenerator(
        GeneratorParams(density=0.65, key_range_low=24, key_range_high=40),
        pattern="trap_syncopated", slide_type="chromatic", slide_probability=0.6
    ).render(chords, key, dur), 52, 95)

    synthlead = _thin(_clamp(LeadSynthGenerator(
        GeneratorParams(density=0.5, key_range_low=60, key_range_high=90),
        style="retro", portamento=0.3, vibrato_rate=5.0
    ).render(chords, key, dur), 46, 86), dur, intro_end=dur*0.20, keep=0.3)

    pad = _thin(_clamp(SynthPadGenerator(
        GeneratorParams(density=0.3, key_range_low=40, key_range_high=64),
        pad_type="sawtooth"
    ).render(chords, key, dur), 38, 64), dur)

    adlibs = _thin(_clamp(VocalAdlibsGenerator(
        GeneratorParams(density=0.3, key_range_low=60, key_range_high=84)
    ).render(chords, key, dur), 44, 76), dur, keep=0.4)

    return {
        "Lead": _clamp(lead, 50, 90), "Drums": drums, "808": bass808,
        "SynthLead": synthlead, "Pad": pad, "Adlibs": adlibs,
    }, bpm


# ===========================================================================
# III. Slide (The Drill) — UK Drill, G minor, 142 BPM.
#    808 slides, dark, no hesitation. The come-up gets dangerous.
#    i - III - VI - VII (the drill progression).
# ===========================================================================

def track_03_slide():
    print("  III. Slide (The Drill)")
    bpm, dur = 142.0, 84.0
    key = G_MINOR

    phrases = [
        [(0, 4), (2, 4), (5, 4), (6, 4)],   # A: i - III - VI - VII (the drill)
        [(0, 4), (5, 4), (3, 4), (6, 4)],   # B: i - VI - iv - VII
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=58, hi=84, density=0.48)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    drill = _clamp(DrillPatternGenerator(
        GeneratorParams(density=0.8, velocity_range=(72, 115)),
        variant="uk_drill", slide_amount=7, stutter_intensity=0.6
    ).render(chords, key, dur), 58, 112)

    bass808 = _clamp(Bass808SlidingGenerator(
        GeneratorParams(density=0.7, key_range_low=22, key_range_high=38),
        pattern="drill_sliding", slide_type="chromatic", slide_probability=0.85
    ).render(chords, key, dur), 50, 95)

    darkpad = _thin(_clamp(DarkPadGenerator(
        GeneratorParams(density=0.35, key_range_low=34, key_range_high=58),
        mode="phrygian_pad"
    ).render(chords, key, dur), 38, 60), dur)

    synthlead = _thin(_clamp(LeadSynthGenerator(
        GeneratorParams(density=0.45, key_range_low=58, key_range_high=88),
        style="supersaw", portamento=0.4, vibrato_rate=6.0
    ).render(chords, key, dur), 44, 84), dur, keep=0.35)

    vocal = _thin(_clamp(VocalChopsGenerator(
        GeneratorParams(density=0.3, key_range_low=58, key_range_high=84),
        processing="stutter", density=0.4
    ).render(chords, key, dur), 40, 72), dur, keep=0.3)

    return {
        "Lead": _clamp(lead, 50, 88), "Drums": drill, "808": bass808,
        "DarkPad": darkpad, "SynthLead": synthlead, "VocalChop": vocal,
    }, bpm


# ===========================================================================
# IV. Smoke (The Climb) — Phonk, C harmonic minor, 130 BPM.
#    Cowbells, Memphis drift, the climb through smoke. Tense, atmospheric.
#    i - VI - V - i (the harmonic-minor phonk tension).
# ===========================================================================

def track_04_smoke():
    print("  IV. Smoke (The Climb)")
    bpm, dur = 130.0, 88.0
    key = C_HARM_MINOR

    phrases = [
        [(0, 4), (5, 4), (4, 4), (0, 4)],   # A: i - VI - V - i (harmonic minor pull)
        [(0, 4), (2, 4), (5, 4), (0, 4)],   # B: i - III - VI - i
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=58, hi=85, density=0.42)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    phonk = _clamp(PhonkGenerator(
        GeneratorParams(density=0.8, velocity_range=(70, 115)),
        variant="drift_phonk", cowbell_density=0.7, bass_slide_amount=0.5
    ).render(chords, key, dur), 58, 112)

    bass808 = _clamp(Bass808SlidingGenerator(
        GeneratorParams(density=0.6, key_range_low=22, key_range_high=38),
        pattern="rolling", slide_type="octave_jump", slide_probability=0.5
    ).render(chords, key, dur), 48, 90)

    darkpad = _thin(_clamp(DarkPadGenerator(
        GeneratorParams(density=0.35, key_range_low=34, key_range_high=58),
        mode="phrygian_pad"
    ).render(chords, key, dur), 38, 60), dur)

    synthlead = _thin(_clamp(LeadSynthGenerator(
        GeneratorParams(density=0.4, key_range_low=60, key_range_high=88),
        style="retro", portamento=0.35, vibrato_rate=4.0
    ).render(chords, key, dur), 42, 80), dur, keep=0.3)

    vocal = _thin(_clamp(VocalChopsGenerator(
        GeneratorParams(density=0.3, key_range_low=58, key_range_high=84),
        processing="pitch_shift", density=0.35
    ).render(chords, key, dur), 40, 70), dur, keep=0.3)

    return {
        "Lead": _clamp(lead, 50, 86), "Drums": phonk, "808": bass808,
        "DarkPad": darkpad, "SynthLead": synthlead, "VocalChop": vocal,
    }, bpm


# ===========================================================================
# V. Crown (The Summit) — Trap/Epic, D minor, 138 BPM.
#    Triumphant — strings, choir, the summit reached. Dark turns to grand.
#    i - VI - III - VII then i - iv - VI - i (the victory lap).
# ===========================================================================

def track_05_crown():
    print("  V. Crown (The Summit)")
    bpm, dur = 138.0, 96.0
    key = D_MINOR

    phrases = [
        [(0, 4), (5, 4), (2, 4), (6, 4)],   # A: i - VI - III - VII (the climb recap)
        [(0, 4), (3, 4), (5, 4), (0, 4)],   # B: i - iv - VI - i (the coronation)
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=58, hi=88, density=0.5)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    drums = _clamp(TrapDrumsGenerator(
        GeneratorParams(density=0.85, velocity_range=(75, 115)),
        variant="melodic", hat_roll_density=0.7
    ).render(chords, key, dur), 60, 115)

    bass808 = _clamp(Bass808SlidingGenerator(
        GeneratorParams(density=0.65, key_range_low=22, key_range_high=40),
        pattern="trap_syncopated", slide_type="overlap", slide_probability=0.5
    ).render(chords, key, dur), 50, 92)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.4, key_range_low=40, key_range_high=68),
        section_size="full", dynamic_shape="crescendo").render(chords, key, dur), 42, 78), dur)

    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=72),
        voice_count=6, dynamics="f", syllable="aah").render(chords, key, dur), 44, 82), dur)

    synthlead = _thin(_clamp(LeadSynthGenerator(
        GeneratorParams(density=0.5, key_range_low=60, key_range_high=92),
        style="supersaw", portamento=0.25, vibrato_rate=5.0
    ).render(chords, key, dur), 46, 90), dur)

    glock = _thin(_clamp(GlockenspielGenerator(
        GeneratorParams(density=0.3, key_range_low=84, key_range_high=108),
        pattern="sparkling_run", note_density=0.9).render(chords, key, dur), 40, 78), dur,
        keep=0.3)

    adlibs = _thin(_clamp(VocalAdlibsGenerator(
        GeneratorParams(density=0.35, key_range_low=58, key_range_high=84)
    ).render(chords, key, dur), 44, 78), dur, keep=0.4)

    return {
        "Lead": _clamp(lead, 52, 92), "Drums": drums, "808": bass808,
        "Strings": strings, "Choir": choir, "SynthLead": synthlead,
        "Glock": glock, "Adlibs": adlibs,
    }, bpm


# ---------------------------------------------------------------------------
# Instrument GM program maps per track.
# Drums always on GM 0 (channel 9 handled by export). 808 = Synth Bass (38/39).
# Vocal chops = 54 (Voice Lead), synth lead = 81/82.
# ---------------------------------------------------------------------------

TRACKS = [
    (track_01_concrete, "01_Concrete.mid", {
        "Lead": 81, "Piano": 0, "Drums": 0, "808": 38, "DarkPad": 95, "VocalChop": 54,
    }),
    (track_02_nickel_bag, "02_Nickel_Bag.mid", {
        "Lead": 81, "Drums": 0, "808": 38, "SynthLead": 82, "Pad": 88, "Adlibs": 54,
    }),
    (track_03_slide, "03_Slide.mid", {
        "Lead": 81, "Drums": 0, "808": 39, "DarkPad": 95, "SynthLead": 82, "VocalChop": 54,
    }),
    (track_04_smoke, "04_Smoke.mid", {
        "Lead": 81, "Drums": 0, "808": 38, "DarkPad": 95, "SynthLead": 82, "VocalChop": 54,
    }),
    (track_05_crown, "05_Crown.mid", {
        "Lead": 81, "Drums": 0, "808": 39, "Strings": 48, "Choir": 52,
        "SynthLead": 82, "Glock": 9, "Adlibs": 54,
    }),
]


def main():
    album_dir = Path("output/album_raazi_ascension")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 78)
    print("  R A A Z I :   A S C E N S I O N")
    print("  A hip-hop beat tape — from the block to the crown")
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
        )
        nc = sum(len(n) for n in raw.values())
        total_notes += nc
        print(f"    -> {filename}  ({nc} notes, {bpm:.0f} BPM)")

    print()
    print("=" * 78)
    print(f"  COMPLETE: RAAZI ASCENSION — {total_notes} notes, 5 tracks")
    print(f"  Arc: Concrete > Nickel Bag > Slide > Smoke > Crown")
    print(f"  Genres: Lo-Fi / Trap / UK Drill / Phonk / Trap-Epic")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
