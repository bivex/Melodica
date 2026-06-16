# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_tre_metri_sopra_il_cielo.py — TRE METRI SOPRA IL CIELO

A 5-movement romantic piano-orchestral suite after Federico Moccia's novel
"Tre Metri Sopra il Cielo". The movements trace the emotional arc of the
book: the melancholic flight home, the descent into a bittersweet Roman
memory, the first-love euphoria, the family betrayal, and the transcendent
ideal of love that gives the book its title ("Three metres above heaven").

Each movement uses Italian/Neapolitan romantic harmony — the minor iv,
the borrowed dominant, the i-VI-III-VII descent — anchored by AAB
cadential phrases that resolve home, the way the story keeps returning
to Babi.

    I.   Il Ritorno (The Return)      D harmonic minor — melancholy, nostalgia
    II.  Pomeriggio Romano            F major          — bittersweet, wistful
    III. Primo Amore (First Love)     D major          — euphoric, soaring
    IV.  Il Segreto (The Secret)      A Phrygian dom.  — dark, dramatic
    V.   Tre Metri Sopra il Cielo     D major          — transcendent finale
"""

import random
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.piano_run import PianoRunGenerator
from melodica.generators.orchestral_strings import (
    ViolinGenerator, ViolaGenerator, CelloGenerator, ContrabassGenerator,
)
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.orchestral_brass import FrenchHornGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer, HMMConfig
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

random.seed(3000)  # Tre Metri Sopra il Cielo

# ---------------------------------------------------------------------------
# Keys — the romantic arc, dark-to-light
# ---------------------------------------------------------------------------
D_HARM_MINOR = Scale(root=2, mode=Mode.HARMONIC_MINOR)   # I.   nostalgic
F_MAJOR      = Scale(root=5, mode=Mode.MAJOR)            # II.  bittersweet
D_MAJOR      = Scale(root=2, mode=Mode.MAJOR)            # III. + V. euphoric
A_PHRYG_DOM  = Scale(root=9, mode=Mode.PHRYGIAN_DOMINANT) # IV. dark

_HARM = CoupledHMMHarmonizer(beam_width=14, chord_change="bars")


# ---------------------------------------------------------------------------
# Diatonic chord-quality tables (degree index -> Quality)
# ---------------------------------------------------------------------------
_DIATONIC: dict[Mode, list[Quality]] = {
    Mode.HARMONIC_MINOR:    [Quality.MINOR, Quality.DIMINISHED, Quality.AUGMENTED, Quality.MINOR, Quality.MINOR, Quality.MAJOR, Quality.DIMINISHED],
    Mode.MAJOR:             [Quality.MAJOR, Quality.MINOR, Quality.MINOR, Quality.MAJOR, Quality.MAJOR, Quality.MINOR, Quality.DIMINISHED],
    Mode.PHRYGIAN_DOMINANT: [Quality.MAJOR, Quality.MAJOR, Quality.DIMINISHED, Quality.MINOR, Quality.DIMINISHED, Quality.MAJOR, Quality.MINOR],
}


def _phrase_constraints(scale, phrases, form, dur):
    """Tile AAB cadential phrases resolving on the tonic (I or i)."""
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
    """Singing, lyrical lead — high steps_probability for legato cantabile."""
    p = GeneratorParams(density=density, velocity_range=(60, 100),
                        key_range_low=lo, key_range_high=hi)
    gen = MelodyGenerator(p, phrase_length=8.0,
                          note_range_low=lo, note_range_high=hi,
                          register_smoothness=0.85, steps_probability=0.82,
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
        "Lead": 0.86, "Piano": 0.84, "Piano2": 0.78, "Violin1": 0.80,
        "Cello": 0.80, "Bass": 0.84, "Strings": 0.78, "Tremolo": 0.74,
        "Horns": 0.78, "Brass": 0.78, "Choir": 0.80, "Harp": 0.78,
        "Glock": 0.70, "Bells": 0.76, "Timpani": 0.80, "Arp": 0.74,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# ===========================================================================
# I. Il Ritorno (The Return) — D harmonic minor, 72 BPM.
#    Step returns from New York; the taxi ride through sleeping Rome; the
#    weight of two years' silence. Melancholic, nostalgic, a lone piano.
#    Cadence: i - VI - iv - i  (the Andalusian/Romantic descent home).
# ===========================================================================

def track_01_il_ritorno():
    print("  I. Il Ritorno")
    bpm, dur = 72.0, 108.0
    key = D_HARM_MINOR

    # i - VI - iv - i : the romantic descent. A = tonic-bVI-iv-tonic.
    phrases = [
        [(0, 1), (5, 1), (3, 1), (0, 1)],   # A: i - VI - iv - i
        [(0, 1), (4, 1), (5, 1), (0, 1)],   # B: i - v - VI - i
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=66, hi=86, density=0.38)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    piano = _thin(_clamp(PianoCompGenerator(
        GeneratorParams(density=0.55, key_range_low=38, key_range_high=72),
        comp_style="pop", voicing_type="shell", chord_density=0.6
    ).render(chords, key, dur), 45, 82), dur)

    cello = _thin(_clamp(CelloGenerator(
        GeneratorParams(density=0.35, key_range_low=36, key_range_high=52),
        articulation="legato").render(chords, key, dur), 38, 70), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.28, key_range_low=50, key_range_high=70),
        section_size="full", dynamic_shape="cresc_dim").render(chords, key, dur), 35, 68), dur)

    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.3, key_range_low=67, key_range_high=90),
        articulation="legato").render(chords, key, dur), 42, 78), dur,
        intro_end=dur*0.30, outro_start=dur*0.75, keep=0.15)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.5, key_range_low=26, key_range_high=40),
        articulation="legato").render(chords, key, dur), 44, 76)

    return {
        "Lead": _clamp(lead, 50, 88), "Piano": piano, "Cello": cello,
        "Strings": strings, "Violin1": violin, "Bass": bass,
    }, bpm


# ===========================================================================
# II. Pomeriggio Romano (Roman Afternoon) — F major, 80 BPM.
#    Bittersweet warmth; Roman rooftops; the memory of a Vespa ride.
#    Wistful major with borrowed minor colours. Cadence resolves on I.
# ===========================================================================

def track_02_pomeriggio():
    print("  II. Pomeriggio Romano")
    bpm, dur = 80.0, 100.0
    key = F_MAJOR

    # I - vi - IV - I : the classic pop-ballad descent, resolving home.
    phrases = [
        [(0, 1), (5, 1), (3, 1), (0, 1)],   # A: I - vi - IV - I
        [(0, 1), (3, 1), (4, 1), (0, 1)],   # B: I - IV - V - I
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=65, hi=88, density=0.42)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    piano = _thin(_clamp(PianoCompGenerator(
        GeneratorParams(density=0.6, key_range_low=40, key_range_high=76),
        comp_style="pop", voicing_type="close", chord_density=0.65
    ).render(chords, key, dur), 45, 84), dur)

    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.3, key_range_low=50, key_range_high=84),
        pattern="arpeggio", direction="up_down", octave_span=3).render(chords, key, dur), 38, 74), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.3, key_range_low=52, key_range_high=72),
        section_size="full", dynamic_shape="crescendo").render(chords, key, dur), 38, 76), dur)

    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.4, key_range_low=68, key_range_high=91),
        articulation="legato").render(chords, key, dur), 44, 82), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.55, key_range_low=26, key_range_high=40),
        articulation="legato").render(chords, key, dur), 46, 78)

    return {
        "Lead": _clamp(lead, 52, 90), "Piano": piano, "Harp": harp,
        "Strings": strings, "Violin1": violin, "Bass": bass,
    }, bpm


# ===========================================================================
# III. Primo Amore (First Love) — D major, 100 BPM.
#    The euphoric flashback: meeting Babi, the reckless joy of youth.
#    Soaring major-key, full strings, the heart racing. Arch contour rises.
# ===========================================================================

def track_03_primo_amore():
    print("  III. Primo Amore")
    bpm, dur = 100.0, 96.0
    key = D_MAJOR

    # I - V - vi - IV : the euphoric pop epic progression (axis of awesome).
    phrases = [
        [(0, 1), (4, 1), (5, 1), (3, 1)],   # A: I - V - vi - IV
        [(0, 1), (3, 1), (4, 1), (0, 1)],   # B: I - IV - V - I
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=66, hi=91, density=0.5)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    piano = _thin(_clamp(PianoCompGenerator(
        GeneratorParams(density=0.65, key_range_low=40, key_range_high=80),
        comp_style="pop", voicing_type="close", chord_density=0.7
    ).render(chords, key, dur), 48, 88), dur)

    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.55, key_range_low=68, key_range_high=92),
        articulation="legato").render(chords, key, dur), 50, 92), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.4, key_range_low=52, key_range_high=76),
        section_size="full", dynamic_shape="crescendo").render(chords, key, dur), 44, 84), dur)

    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.5, key_range_low=50, key_range_high=86),
        pattern="arpeggio", direction="up_down").render(chords, key, dur), 42, 82), dur)

    arp_raw = _clamp(ArpeggiatorGenerator(
        GeneratorParams(density=0.6, key_range_low=60, key_range_high=88),
        pattern="up").render(chords, key, dur - 8.0), 42, 78)
    arp = _thin(_off(arp_raw, 8.0), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.6, key_range_low=26, key_range_high=42),
        articulation="legato").render(chords, key, dur), 48, 84)

    return {
        "Lead": _clamp(lead, 55, 95), "Piano": piano, "Violin1": violin,
        "Strings": strings, "Harp": harp, "Arp": arp, "Bass": bass,
    }, bpm


# ===========================================================================
# IV. Il Segreto (The Secret) — A Phrygian dominant, 88 BPM.
#    The family betrayal discovered; the violence; the silence.
#    Dark, dramatic, the Phrygian bII tension. Brooding strings, low brass.
# ===========================================================================

def track_04_il_segreto():
    print("  IV. Il Segreto")
    bpm, dur = 88.0, 100.0
    key = A_PHRYG_DOM

    # I - bII - I - iv : the Phrygian dramatic cadence, resolving to tonic.
    phrases = [
        [(0, 1), (1, 1), (0, 1), (3, 1)],   # A: I - bII - I - iv
        [(0, 1), (5, 1), (1, 1), (0, 1)],   # B: I - VI - bII - I
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=86, density=0.42, contour="rise_fall")
    chords = _harmonize(lead, key, dur, constraints=constraints)

    piano = _thin(_clamp(PianoCompGenerator(
        GeneratorParams(density=0.5, key_range_low=36, key_range_high=68),
        comp_style="pop", voicing_type="shell", chord_density=0.55
    ).render(chords, key, dur), 42, 78), dur)

    cello = _thin(_clamp(CelloGenerator(
        GeneratorParams(density=0.4, key_range_low=34, key_range_high=50),
        articulation="legato").render(chords, key, dur), 40, 74), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.35, key_range_low=48, key_range_high=70),
        section_size="full", dynamic_shape="cresc_dim").render(chords, key, dur), 38, 72), dur)

    tremolo = _thin(_clamp(TremoloStringsGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=62),
        variant="single", bow_speed=0.20).render(chords, key, dur), 34, 64), dur)

    horns = _thin(_clamp(FrenchHornGenerator(
        GeneratorParams(density=0.3, key_range_low=46, key_range_high=65),
        articulation="legato").render(chords, key, dur), 42, 80), dur,
        intro_end=dur*0.30, outro_start=dur*0.75, keep=0.15)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.55, key_range_low=24, key_range_high=38),
        articulation="legato").render(chords, key, dur), 44, 76)

    return {
        "Lead": _clamp(lead, 50, 86), "Piano": piano, "Cello": cello,
        "Strings": strings, "Tremolo": tremolo, "Horns": horns, "Bass": bass,
    }, bpm


# ===========================================================================
# V. Tre Metri Sopra il Cielo (Three Metres Above Heaven) — D major, 92 BPM.
#    The title's transcendence: love as an ideal beyond reach, an ecstatic
#    ascent. Full forces — brass, choir, timpani, bells. The grand climax
#    that resolves the whole arc into light.
# ===========================================================================

def track_05_tre_metri():
    print("  V. Tre Metri Sopra il Cielo")
    bpm, dur = 92.0, 116.0
    key = D_MAJOR

    # I - V - vi - IV (euphoric) then I - IV - V - I (authentic resolution).
    phrases = [
        [(0, 1), (4, 1), (5, 1), (3, 1)],   # A: I - V - vi - IV
        [(0, 1), (3, 1), (4, 1), (0, 1)],   # B: I - IV - V - I
    ]
    constraints = _phrase_constraints(key, phrases, "AAB", dur)

    lead = _lead_melody(key, dur, lo=64, hi=91, density=0.5)
    chords = _harmonize(lead, key, dur, constraints=constraints)

    piano = _thin(_clamp(PianoCompGenerator(
        GeneratorParams(density=0.65, key_range_low=40, key_range_high=84),
        comp_style="pop", voicing_type="close", chord_density=0.7
    ).render(chords, key, dur), 48, 92), dur)

    brass = _thin(_clamp(BrassSectionGenerator(
        GeneratorParams(density=0.4, key_range_low=48, key_range_high=72),
        ensemble_mode="full", intensity=0.9).render(chords, key, dur - 6.0), 50, 98), dur)

    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.55, key_range_low=68, key_range_high=93),
        articulation="legato").render(chords, key, dur), 50, 95), dur)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.4, key_range_low=50, key_range_high=74),
        section_size="full", dynamic_shape="crescendo").render(chords, key, dur), 44, 86), dur)

    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.35, key_range_low=52, key_range_high=76),
        voice_count=6, dynamics="ff", syllable="aah").render(chords, key, dur), 45, 90), dur)

    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.55, key_range_low=50, key_range_high=86),
        pattern="arpeggio", direction="up_down").render(chords, key, dur), 42, 84), dur)

    glock = _thin(_clamp(GlockenspielGenerator(
        GeneratorParams(density=0.45, key_range_low=88, key_range_high=108),
        pattern="sparkling_run", note_density=1.1).render(chords, key, dur), 45, 84), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.65, key_range_low=24, key_range_high=42),
        articulation="legato").render(chords, key, dur), 48, 88)

    timp = _thin(_clamp(TimpaniGenerator(
        GeneratorParams(density=0.4, key_range_low=36, key_range_high=48),
        stroke_pattern="roll").render(chords, key, dur), 55, 98), dur)

    return {
        "Lead": _clamp(lead, 55, 100), "Piano": piano, "Brass": brass,
        "Violin1": violin, "Strings": strings, "Choir": choir, "Harp": harp,
        "Glock": glock, "Bass": bass, "Timpani": timp,
    }, bpm


# ---------------------------------------------------------------------------
# Instrument GM program maps per track.
# Piano = Acoustic Grand (0) throughout — the heart of the Italian romance.
# ---------------------------------------------------------------------------

TRACKS = [
    (track_01_il_ritorno, "01_Il_Ritorno.mid", {
        "Lead": 0, "Piano": 0, "Cello": 42, "Strings": 48, "Violin1": 40, "Bass": 43,
    }),
    (track_02_pomeriggio, "02_Pomeriggio_Romano.mid", {
        "Lead": 0, "Piano": 0, "Harp": 46, "Strings": 48, "Violin1": 40, "Bass": 43,
    }),
    (track_03_primo_amore, "03_Primo_Amore.mid", {
        "Lead": 0, "Piano": 0, "Violin1": 40, "Strings": 48, "Harp": 46, "Arp": 0, "Bass": 43,
    }),
    (track_04_il_segreto, "04_Il_Segreto.mid", {
        "Lead": 0, "Piano": 0, "Cello": 42, "Strings": 48, "Tremolo": 44, "Horns": 60, "Bass": 43,
    }),
    (track_05_tre_metri, "05_Tre_Metri_Sopra_il_Cielo.mid", {
        "Lead": 0, "Piano": 0, "Brass": 61, "Violin1": 40, "Strings": 48, "Choir": 52,
        "Harp": 46, "Glock": 9, "Bass": 43, "Timpani": 47,
    }),
]


def main():
    album_dir = Path("output/album_tre_metri_sopra_il_cielo")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 78)
    print("  T R E   M E T R I   S O P R A   I L   C I E L O")
    print("  A romantic piano-orchestral suite after Federico Moccia")
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
    print(f"  COMPLETE: TRE METRI SOPRA IL CIELO — {total_notes} notes, 5 movements")
    print(f"  Arc: Il Ritorno > Pomeriggio Romano > Primo Amore >")
    print(f"        Il Segreto > Tre Metri Sopra il Cielo")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
