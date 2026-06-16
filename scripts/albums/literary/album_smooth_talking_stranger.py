# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_smooth_talking_stranger.py — SMOOTH TALKING STRANGER

A 5-movement contemporary jazz-R&B romantic suite after Lisa Kleypas's novel
"Smooth Talking Stranger". The movements trace Ella and Jack's arc: the
Houston heat, the stranger in the office, the slow-burn attraction, the
intimate dinner (with the steak betrayal), and the moment of surrender.

The harmonic language is jazz romanticism — ii-V-I progressions, dorian
colours, major-7 voicings, walking bass — the Austin/Elephant Room jazz
that brings Ella and Jack together in the book. Sax carries the longing,
piano comps the conversation, walking bass the steady heartbeat.

    I.   281 (The Call)          D dorian — the 3am call that upends her life
    II.  The Stranger             D dorian — meeting Jack; smooth, charged
    III. The Elephant Room        Eb major — jazz-club warmth; banter, wine
    IV. The Dinner                Bb major — the steak betrayal; slow seduction
    V.  Smooth Talking Stranger   A major — surrender; the album's climax
"""

import random
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.piano_run import PianoRunGenerator
from melodica.generators.sax_solo import SaxSoloGenerator
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.orchestral_strings import (
    ViolinGenerator, CelloGenerator, ContrabassGenerator,
)
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer, HMMConfig
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

random.seed(281)  # Houston area code — the call that starts it all

# ---------------------------------------------------------------------------
# Keys — the slow-burn arc, dorian coolth warming to major heat
# ---------------------------------------------------------------------------
D_DORIAN = Scale(root=2, mode=Mode.DORIAN)    # I + II: cool, charged
EB_MAJOR = Scale(root=3, mode=Mode.MAJOR)     # III: jazz-club warmth
BB_MAJOR = Scale(root=10, mode=Mode.MAJOR)    # IV: dinner seduction
A_MAJOR  = Scale(root=9, mode=Mode.MAJOR)     # V: climax, surrender

_HARM = CoupledHMMHarmonizer(beam_width=14, chord_change="bars")


# ---------------------------------------------------------------------------
# Diatonic chord-quality tables per mode
# ---------------------------------------------------------------------------
_DIATONIC: dict[Mode, list[Quality]] = {
    Mode.DORIAN: [Quality.MINOR, Quality.MINOR, Quality.MAJOR, Quality.MAJOR, Quality.MINOR, Quality.DIMINISHED, Quality.MAJOR],
    Mode.MAJOR:  [Quality.MAJOR, Quality.MINOR, Quality.MINOR, Quality.MAJOR, Quality.MAJOR, Quality.MINOR, Quality.DIMINISHED],
}


def _phrase_constraints(scale, phrases, form, dur):
    """Tile AAB jazz phrases. Dorian movements use the i-IV-vamp (modal jazz);
    major movements use ii-V-I (the jazz cadence)."""
    letter_to_idx = {c: i for i, c in enumerate("ABCDEFGHIJ")}
    cycle = [phrases[letter_to_idx[c]] for c in form]
    deg = [int(d) % 12 for d in scale.degrees()]
    qualities = _DIATONIC[scale.mode]
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

def _harmonize(melody, scale, dur, constraints=None):
    return _HARM.harmonize(melody, scale, duration_beats=dur, constraints=constraints)


def _lead_melody(scale, dur, *, lo, hi, density, contour="arch"):
    """Singing lead — cantabile legato, the Ella voice."""
    p = GeneratorParams(density=density, velocity_range=(60, 100),
                        key_range_low=lo, key_range_high=hi)
    gen = MelodyGenerator(p, phrase_length=8.0,
                          note_range_low=lo, note_range_high=hi,
                          register_smoothness=0.85, steps_probability=0.8,
                          motif_probability=0.6, phrase_contour=contour)
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
    desk.track_gains.update({
        "Lead": 0.86, "Piano": 0.82, "Sax": 0.84, "Bass": 0.84,
        "WalkBass": 0.84, "Violin1": 0.78, "Cello": 0.80, "Strings": 0.76,
        "Choir": 0.74, "Brass": 0.78, "Glock": 0.66, "Bells": 0.72, "Comp": 0.74,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# ===========================================================================
# I. 281 (The Call) — D dorian, 76 BPM.
#    The 3am phone call; Ella's world upends. Cool dorian, a lone sax in the
#    dark, walking bass like a restless heartbeat.
#    Cadence: i - IV - i - VII (the dorian modal vamp, restless, unresolved).
# ===========================================================================

def track_01_the_call():
    print("  I. 281 (The Call)")
    bpm, dur = 76.0, 104.0
    key = D_DORIAN

    # Dorian modal vamp: i - IV - i - VII. A and B both circle the tonic
    # without a true V-I resolution — the restlessness of the call.
    phrases = [
        [(0, 1), (3, 1), (0, 1), (6, 1)],   # A: i - IV - i - VII
        [(0, 1), (3, 1), (6, 1), (0, 1)],   # B: i - IV - VII - i
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=62, hi=84, density=0.40, contour="arch")
    chords = _harmonize(lead, key, dur, constraints=constraints)

    sax = _thin(_clamp(SaxSoloGenerator(
        GeneratorParams(density=0.4, key_range_low=58, key_range_high=86),
        style="ballad", vibrato_depth=0.6
    ).render(chords, key, dur), 45, 84), dur, intro_end=dur*0.25, keep=0.15)

    piano = _thin(_clamp(PianoCompGenerator(
        GeneratorParams(density=0.6, key_range_low=38, key_range_high=72),
        comp_style="jazz", voicing_type="rootless", chord_density=0.6
    ).render(chords, key, dur), 42, 78), dur)

    walk = _clamp(WalkingBassGenerator(
        GeneratorParams(density=0.85, key_range_low=28, key_range_high=48),
        approach_style="chromatic"
    ).render(chords, key, dur), 48, 84)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.25, key_range_low=48, key_range_high=67),
        section_size="chamber", dynamic_shape="cresc_dim").render(chords, key, dur), 35, 66), dur)

    return {
        "Lead": _clamp(lead, 50, 86), "Sax": sax, "Piano": piano,
        "WalkBass": walk, "Strings": strings,
    }, bpm


# ===========================================================================
# II. The Stranger — D dorian, 84 BPM.
#    Meeting Jack Travis; the charged office encounter. Smooth, the dorian
#    coolth now with undercurrents of heat. Sax and piano trade lines.
#    Cadence: i - IV vamp with the VII pulling back (his pull on her).
# ===========================================================================

def track_02_the_stranger():
    print("  II. The Stranger")
    bpm, dur = 84.0, 100.0
    key = D_DORIAN

    phrases = [
        [(0, 1), (3, 1), (0, 1), (3, 1)],   # A: i - IV - i - IV (the back-and-forth)
        [(0, 1), (6, 1), (3, 1), (0, 1)],   # B: i - VII - IV - i (he pulls, she returns)
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=86, density=0.42)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    sax = _thin(_clamp(SaxSoloGenerator(
        GeneratorParams(density=0.45, key_range_low=58, key_range_high=88),
        style="smooth", vibrato_depth=0.5
    ).render(chords, key, dur), 46, 86), dur)

    piano = _thin(_clamp(PianoCompGenerator(
        GeneratorParams(density=0.65, key_range_low=40, key_range_high=76),
        comp_style="jazz", voicing_type="shell", chord_density=0.65
    ).render(chords, key, dur), 44, 82), dur)

    walk = _clamp(WalkingBassGenerator(
        GeneratorParams(density=0.85, key_range_low=28, key_range_high=48),
        approach_style="chromatic"
    ).render(chords, key, dur), 48, 84)

    cello = _thin(_clamp(CelloGenerator(
        GeneratorParams(density=0.3, key_range_low=38, key_range_high=52),
        articulation="legato").render(chords, key, dur), 40, 72), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.28, key_range_low=50, key_range_high=70),
        section_size="chamber", dynamic_shape="crescendo").render(chords, key, dur), 38, 72), dur)

    return {
        "Lead": _clamp(lead, 52, 88), "Sax": sax, "Piano": piano,
        "WalkBass": walk, "Cello": cello, "Strings": strings,
    }, bpm


# ===========================================================================
# III. The Elephant Room — Eb major, 100 BPM.
#    The Austin jazz club; banter and wine; the warmth of shared taste.
#    Brighter major, ii-V-I cadences, sax soaring. The conversation flows.
# ===========================================================================

def track_03_elephant_room():
    print("  III. The Elephant Room")
    bpm, dur = 100.0, 96.0
    key = EB_MAJOR

    # Jazz ii-V-I: I - vi - ii - V, resolving home. Bright, swinging.
    phrases = [
        [(0, 1), (5, 1), (1, 1), (4, 1)],   # A: I - vi - ii - V
        [(0, 1), (1, 1), (4, 1), (0, 1)],   # B: I - ii - V - I
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=88, density=0.46)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    sax = _thin(_clamp(SaxSoloGenerator(
        GeneratorParams(density=0.5, key_range_low=60, key_range_high=90),
        style="bebop", vibrato_depth=0.4
    ).render(chords, key, dur), 48, 90), dur)

    piano = _thin(_clamp(PianoCompGenerator(
        GeneratorParams(density=0.7, key_range_low=40, key_range_high=80),
        comp_style="jazz", voicing_type="rootless", chord_density=0.7
    ).render(chords, key, dur), 46, 86), dur)

    walk = _clamp(WalkingBassGenerator(
        GeneratorParams(density=0.9, key_range_low=28, key_range_high=50),
        approach_style="chromatic"
    ).render(chords, key, dur), 50, 88)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.3, key_range_low=52, key_range_high=72),
        section_size="chamber", dynamic_shape="crescendo").render(chords, key, dur), 40, 76), dur)

    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.35, key_range_low=68, key_range_high=90),
        articulation="legato").render(chords, key, dur), 44, 82), dur,
        intro_end=dur*0.30, outro_start=dur*0.75, keep=0.15)

    glock_raw = _clamp(GlockenspielGenerator(
        GeneratorParams(density=0.25, key_range_low=84, key_range_high=104),
        pattern="sparkling_run", note_density=0.8).render(chords, key, dur - 10.0), 36, 66)
    glock = _thin(_off(glock_raw, 10.0), dur)

    return {
        "Lead": _clamp(lead, 52, 92), "Sax": sax, "Piano": piano,
        "WalkBass": walk, "Strings": strings, "Violin1": violin, "Glock": glock,
    }, bpm


# ===========================================================================
# IV. The Dinner — Bb major, 78 BPM.
#    The steak betrayal; Ella breaks veganism; the slow seduction over wine.
#    Warm major, slower, intimate. ii-V-I in Bb. The sensuous middle.
# ===========================================================================

def track_04_the_dinner():
    print("  IV. The Dinner")
    bpm, dur = 78.0, 108.0
    key = BB_MAJOR

    phrases = [
        [(0, 1), (3, 1), (1, 1), (4, 1)],   # A: I - IV - ii - V (the lush turn)
        [(0, 1), (1, 1), (4, 1), (0, 1)],   # B: I - ii - V - I (resolution)
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=62, hi=86, density=0.40, contour="rise_fall")
    chords = _harmonize(lead, key, dur, constraints=constraints)

    sax = _thin(_clamp(SaxSoloGenerator(
        GeneratorParams(density=0.42, key_range_low=56, key_range_high=86),
        style="smooth", vibrato_depth=0.7
    ).render(chords, key, dur), 44, 84), dur, intro_end=dur*0.30, keep=0.18)

    piano = _thin(_clamp(PianoCompGenerator(
        GeneratorParams(density=0.6, key_range_low=38, key_range_high=74),
        comp_style="jazz", voicing_type="close", chord_density=0.6
    ).render(chords, key, dur), 42, 80), dur)

    walk = _clamp(WalkingBassGenerator(
        GeneratorParams(density=0.8, key_range_low=26, key_range_high=48),
        approach_style="diatonic"
    ).render(chords, key, dur), 46, 82)

    cello = _thin(_clamp(CelloGenerator(
        GeneratorParams(density=0.35, key_range_low=36, key_range_high=52),
        articulation="legato").render(chords, key, dur), 40, 72), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=70),
        section_size="chamber", dynamic_shape="cresc_dim").render(chords, key, dur), 36, 70), dur)

    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.25, key_range_low=50, key_range_high=68),
        voice_count=4, dynamics="p", syllable="aah").render(chords, key, dur), 36, 64), dur,
        intro_end=dur*0.35, keep=0.15)

    return {
        "Lead": _clamp(lead, 50, 86), "Sax": sax, "Piano": piano,
        "WalkBass": walk, "Cello": cello, "Strings": strings, "Choir": choir,
    }, bpm


# ===========================================================================
# V. Smooth Talking Stranger — A major, 88 BPM.
#    The surrender; the album's climax. Bright major, full forces — sax
#    soaring, brass entering, the warmth of A major opening up.
#    ii-V-I cadence resolving into light. The title track.
# ===========================================================================

def track_05_smooth_stranger():
    print("  V. Smooth Talking Stranger")
    bpm, dur = 88.0, 112.0
    key = A_MAJOR

    phrases = [
        [(0, 1), (4, 1), (1, 1), (4, 1)],   # A: I - V - ii - V (suspended longing)
        [(0, 1), (1, 1), (4, 1), (0, 1)],   # B: I - ii - V - I (the release)
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=89, density=0.48)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    sax = _thin(_clamp(SaxSoloGenerator(
        GeneratorParams(density=0.5, key_range_low=60, key_range_high=92),
        style="smooth", vibrato_depth=0.6
    ).render(chords, key, dur), 48, 92), dur)

    piano = _thin(_clamp(PianoCompGenerator(
        GeneratorParams(density=0.7, key_range_low=40, key_range_high=82),
        comp_style="pop", voicing_type="close", chord_density=0.7
    ).render(chords, key, dur), 48, 90), dur)

    walk = _clamp(WalkingBassGenerator(
        GeneratorParams(density=0.85, key_range_low=28, key_range_high=50),
        approach_style="chromatic"
    ).render(chords, key, dur), 50, 88)

    brass = _thin(_clamp(BrassSectionGenerator(
        GeneratorParams(density=0.35, key_range_low=48, key_range_high=72),
        ensemble_mode="full", intensity=0.85).render(chords, key, dur - 8.0), 48, 92), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.4, key_range_low=52, key_range_high=76),
        section_size="full", dynamic_shape="crescendo").render(chords, key, dur), 44, 84), dur)

    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.5, key_range_low=68, key_range_high=92),
        articulation="legato").render(chords, key, dur), 50, 92), dur)

    glock = _thin(_clamp(GlockenspielGenerator(
        GeneratorParams(density=0.35, key_range_low=88, key_range_high=108),
        pattern="sparkling_run", note_density=1.0).render(chords, key, dur), 42, 78), dur)

    return {
        "Lead": _clamp(lead, 54, 95), "Sax": sax, "Piano": piano,
        "WalkBass": walk, "Brass": brass, "Strings": strings,
        "Violin1": violin, "Glock": glock,
    }, bpm


# ---------------------------------------------------------------------------
# Instrument GM program maps per track.
# Sax = 66 (Tenor Sax) / 65 (Soprano Sax); Piano = 0 (Acoustic Grand);
# Bass = 33 (Electric Bass finger) for the walking lines.
# ---------------------------------------------------------------------------

TRACKS = [
    (track_01_the_call, "01_The_Call.mid", {
        "Lead": 0, "Sax": 66, "Piano": 0, "WalkBass": 33, "Strings": 48,
    }),
    (track_02_the_stranger, "02_The_Stranger.mid", {
        "Lead": 0, "Sax": 65, "Piano": 0, "WalkBass": 33, "Cello": 42, "Strings": 48,
    }),
    (track_03_elephant_room, "03_The_Elephant_Room.mid", {
        "Lead": 0, "Sax": 66, "Piano": 0, "WalkBass": 33, "Strings": 48, "Violin1": 40, "Glock": 9,
    }),
    (track_04_the_dinner, "04_The_Dinner.mid", {
        "Lead": 0, "Sax": 65, "Piano": 0, "WalkBass": 33, "Cello": 42, "Strings": 48, "Choir": 52,
    }),
    (track_05_smooth_stranger, "05_Smooth_Talking_Stranger.mid", {
        "Lead": 0, "Sax": 66, "Piano": 0, "WalkBass": 33, "Brass": 61,
        "Strings": 48, "Violin1": 40, "Glock": 9,
    }),
]


def main():
    album_dir = Path("output/album_smooth_talking_stranger")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 78)
    print("  S M O O T H   T A L K I N G   S T R A N G E R")
    print("  A contemporary jazz-R&B romance after Lisa Kleypas")
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
    print(f"  COMPLETE: SMOOTH TALKING STRANGER — {total_notes} notes, 5 movements")
    print(f"  Arc: The Call > The Stranger > The Elephant Room >")
    print(f"        The Dinner > Smooth Talking Stranger")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
