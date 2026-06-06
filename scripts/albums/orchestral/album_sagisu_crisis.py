"""
Sagisu Crisis — Symphonic Rock Album (Shiro Sagisu style)
8 tracks. Orchestral + rock fusion with heavy drums, choir, brass, power chords.
MIDI only, no WAV.
"""

import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality
from melodica.generators import GeneratorParams
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.orchestral_strings import (
    ViolinGenerator, CelloGenerator, ContrabassGenerator,
)
from melodica.generators.orchestral_brass import (
    FrenchHornGenerator, TrumpetGenerator, TromboneGenerator,
)
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.orchestral_unpitched_percussion import (
    BassDrumGenerator, TamTamGenerator,
)
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.power_chord import PowerChordGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.guitar_strumming import GuitarStrummingGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.tension import TensionGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator
from melodica.generators.victory_fanfare import VictoryFanfareGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.composer.transformers import spiceup

# ── Keys ──────────────────────────────────────────────
D_MINOR = Scale(root=2, mode=Mode.NATURAL_MINOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)
E_MINOR = Scale(root=4, mode=Mode.NATURAL_MINOR)
B_MINOR = Scale(root=11, mode=Mode.NATURAL_MINOR)
C_MINOR = Scale(root=0, mode=Mode.NATURAL_MINOR)
F_MINOR = Scale(root=5, mode=Mode.NATURAL_MINOR)
G_MINOR = Scale(root=7, mode=Mode.NATURAL_MINOR)
A_HARM  = Scale(root=9, mode=Mode.HARMONIC_MINOR)
D_PHRYG = Scale(root=2, mode=Mode.PHRYGIAN)
C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
E_MAJOR = Scale(root=4, mode=Mode.MAJOR)

# ── GM Programs ───────────────────────────────────────
PIANO       = 0
EPIANO      = 4
ORGAN       = 16
ROCK_ORGAN  = 18
JAZZ_GUITAR = 26
DIST_GUITAR = 30
BASS_PICK   = 34
VIOLIN      = 40
CELLO       = 42
CONTRABASS  = 43
TREM_STR    = 44
HARP        = 46
TIMPANI     = 47
STR_ENS1    = 48
STR_ENS2    = 49
CHOIR       = 52
FR_HORN     = 60
TRUMPET     = 56
TROMBONE    = 57
BRASS_SEC   = 62
SOPRANO     = 64
PAD_WARM    = 89
DRUMS       = 0

# ── Helpers ───────────────────────────────────────────

def _chords(progression: str, duration: float, key: Scale) -> list[ChordLabel]:
    parts = progression.split()
    beats_per = duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        chord = key.parse_roman(p)
        chord.start = i * beats_per
        chord.duration = beats_per
        chords.append(chord)
    return chords


def _clamp(notes, lo, hi):
    return [n.clone(velocity=max(lo, min(hi, n.velocity))) for n in notes]


def _mix(raw: dict, bpm: float) -> dict:
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Strings":   0.82, "Violin":   0.88, "Cello":      0.80,
        "Bass":      0.75, "Contrabass": 0.70, "Horns":     0.78,
        "Trumpet":   0.82, "Trombone":  0.78, "Brass":      0.85,
        "Choir":     0.65, "Pad":       0.50, "Drums":      0.80,
        "Ghosts":    0.55, "PowerChord": 0.82, "Guitar":    0.78,
        "Solo":      0.85, "Tension":   0.60, "Timpani":    0.72,
        "BassDrum":  0.70, "TamTam":    0.65, "Ostinato":   0.70,
        "Pedal":     0.65, "Arp":       0.60, "Piano":      0.78,
        "Comp":      0.75, "Hit":       0.80, "Fanfare":    0.85,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    m = MasteringDesk(target_lufs=-14.0)
    mastered, _ = m.apply_mastering(mixed)
    return mastered


def _export(tracks: dict, bpm: float, instruments: dict, path: str):
    export_multitrack_midi(
        tracks, path,
        bpm=bpm,
        instruments=instruments,
        humanize=True,
    )


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "output", "sagisu_crisis"))
os.makedirs(BASE_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════
# Track 1 — Decent Into Darkness  (atmospheric intro)
# ══════════════════════════════════════════════════════
def track_01():
    print("  1. Descent Into Darkness")
    dur = 56.0
    key = D_MINOR
    bpm = 68.0
    chords = _chords("i III VII i iv III VII i", dur, key)

    # Dark orchestral pad
    pad = DarkPadGenerator(
        GeneratorParams(density=0.15, key_range_low=36, key_range_high=60),
        mode="minor_pad", chord_dur=7.0, velocity_level=0.25, register="low",
    ).render(chords, key, dur)

    # Cello melody — brooding
    cello = CelloGenerator(
        GeneratorParams(density=0.35, key_range_low=36, key_range_high=55),
        articulation="sustained", dynamic_curve="cresc_dim", vibrato=True,
    ).render(chords, key, dur)

    # Timpani heartbeat
    timp = TimpaniGenerator(
        GeneratorParams(density=0.06, key_range_low=36, key_range_high=43),
        stroke_pattern="single", drum_count=2,
    ).render(chords, key, dur)

    # Bass drum pulse
    bd = BassDrumGenerator(pattern_type="single").render(chords, key, dur)

    # Tension shimmer
    tens = TensionGenerator(
        GeneratorParams(density=0.20, key_range_low=48, key_range_high=72),
        mode="tritone_pulse", velocity_level=0.25, register="mid",
    ).render(chords, key, dur)

    return {
        "Pad": pad, "Cello": cello, "Timpani": timp,
        "BassDrum": bd, "Tension": tens,
    }, bpm


# ══════════════════════════════════════════════════════
# Track 2 — Evangelion  (full orchestral rock attack)
# ══════════════════════════════════════════════════════
def track_02():
    print("  2. Evangelion")
    dur = 80.0
    key = A_HARM
    bpm = 132.0
    chords = _chords("i iv V III VI iv V i i iv V III bVI bVII i", dur, key)

    # Rock drums — heavy driving
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.10),
        style="rock", groove_swing=0.52, fill_frequency=0.25,
        auto_fills=True, section_type="chorus",
    ).render(chords, key, dur)

    # Power chord guitar — chugging
    power = PowerChordGenerator(
        GeneratorParams(density=0.60, key_range_low=28, key_range_high=52),
        pattern="chug", palm_mute_ratio=0.5, include_octave=True,
    ).render(chords, key, dur)

    # Strings ensemble — dramatic legato
    strings = StringsLegatoGenerator(
        GeneratorParams(density=0.50, key_range_low=48, key_range_high=79),
        section_size="ensemble", dynamic_shape="cresc_dim",
        vibrato_amount=0.15,
    ).render(chords, key, dur)

    # Brass section hits
    brass = BrassSectionGenerator(
        GeneratorParams(density=0.45, key_range_low=40, key_range_high=67),
        articulation="hit", intensity=0.9, voicing="closed",
    ).render(chords, key, dur)

    # French horn melody
    horns = FrenchHornGenerator(
        GeneratorParams(density=0.40, key_range_low=48, key_range_high=67),
        articulation="sustained", dynamic_curve="cresc_dim",
        fanfare_mode=True, note_density=1.2,
    ).render(chords, key, dur)

    # Choir backing
    choir = ChoirAahsGenerator(
        GeneratorParams(density=0.25, key_range_low=48, key_range_high=67),
        voice_count=4, dynamics="f", vibrato=0.3,
    ).render(chords, key, dur)

    # Contrabass foundation
    bass = ContrabassGenerator(
        GeneratorParams(density=0.45, key_range_low=24, key_range_high=38),
        articulation="sustained", dynamic_curve="flat",
    ).render(chords, key, dur)

    # Timpani rolls
    timp = TimpaniGenerator(
        GeneratorParams(density=0.08, key_range_low=36, key_range_high=43),
        stroke_pattern="roll", drum_count=4,
    ).render(chords, key, dur)

    return {
        "Drums": drums, "PowerChord": power, "Strings": strings,
        "Brass": brass, "Horns": horns, "Choir": choir,
        "Bass": bass, "Timpani": timp,
    }, bpm


# ══════════════════════════════════════════════════════
# Track 3 — Serenity  (piano + strings ballad)
# ══════════════════════════════════════════════════════
def track_03():
    print("  3. Serenity")
    dur = 64.0
    key = C_MAJOR
    bpm = 76.0
    chords = _chords("I vi IV V iii IV ii V I vi IV V", dur, key)

    # Piano arpeggiated comp
    comp = PianoCompGenerator(
        GeneratorParams(density=0.40, key_range_low=48, key_range_high=72),
        comp_style="pop", voicing_type="close",
        accent_pattern="syncopated", chord_density=0.7,
    ).render(chords, key, dur)

    # Violin melody — lyrical
    violin = ViolinGenerator(
        GeneratorParams(density=0.45, key_range_low=55, key_range_high=84),
        articulation="sustained", dynamic_curve="cresc_dim",
        vibrato=True, note_density=1.5,
    ).render(chords, key, dur)

    # Cello counter-melody
    cello = CelloGenerator(
        GeneratorParams(density=0.35, key_range_low=36, key_range_high=55),
        articulation="sustained", dynamic_curve="flat", vibrato=True,
    ).render(chords, key, dur)

    # Strings pad
    strings = StringsLegatoGenerator(
        GeneratorParams(density=0.20, key_range_low=43, key_range_high=67),
        section_size="ensemble", dynamic_shape="sustained",
        vibrato_amount=0.08,
    ).render(chords, key, dur)

    # Subtle bass
    bass = ContrabassGenerator(
        GeneratorParams(density=0.30, key_range_low=24, key_range_high=36),
        articulation="sustained", dynamic_curve="flat",
    ).render(chords, key, dur)

    # Light drums — jazz brushes
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.05),
        style="jazz", groove_swing=0.60, fill_frequency=0.08,
        auto_fills=True, section_type="verse",
    ).render(chords, key, dur)

    return {
        "Comp": comp, "Violin": violin, "Cello": cello,
        "Strings": strings, "Bass": bass, "Drums": drums,
    }, bpm


# ══════════════════════════════════════════════════════
# Track 4 — NERV March  (dark military orchestral)
# ══════════════════════════════════════════════════════
def track_04():
    print("  4. NERV March")
    dur = 72.0
    key = F_MINOR
    bpm = 108.0
    chords = _chords("i iv V i bVI bVII i iv bVI bVII i V i", dur, key)

    # Snare-like drums via DrumKit rock pattern
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.10),
        style="rock", groove_swing=0.50, fill_frequency=0.20,
        auto_fills=True, section_type="verse",
    ).render(chords, key, dur)

    # Bass drum march
    bd = BassDrumGenerator(pattern_type="march").render(chords, key, dur)

    # TamTam doom hits
    tamtam = TamTamGenerator(pattern_type="crescendo_strike").render(chords, key, dur)

    # Brass fanfare
    brass = BrassSectionGenerator(
        GeneratorParams(density=0.50, key_range_low=40, key_range_high=67),
        articulation="hit", intensity=0.95, voicing="open", divisi_count=4,
    ).render(chords, key, dur)

    # French horn sustained
    horns = FrenchHornGenerator(
        GeneratorParams(density=0.45, key_range_low=41, key_range_high=60),
        articulation="sustained", dynamic_curve="cresc_dim",
        fanfare_mode=True, note_density=1.0,
    ).render(chords, key, dur)

    # Ostinato strings — relentless
    ost = OstinatoGenerator(
        GeneratorParams(density=0.55, key_range_low=48, key_range_high=67),
        pattern="minor_third", use_scale_degrees=True,
        accent_pattern=[1.0, 0.6, 0.8, 0.6],
    ).render(chords, key, dur)

    # Choir — ominous
    choir = ChoirAahsGenerator(
        GeneratorParams(density=0.20, key_range_low=43, key_range_high=60),
        voice_count=4, dynamics="mp", vibrato=0.4,
    ).render(chords, key, dur)

    # Contrabass
    bass = ContrabassGenerator(
        GeneratorParams(density=0.40, key_range_low=24, key_range_high=36),
        articulation="sustained", dynamic_curve="flat", bass_voice=True,
    ).render(chords, key, dur)

    return {
        "Drums": drums, "BassDrum": bd, "TamTam": tamtam,
        "Brass": brass, "Horns": horns, "Ostinato": ost,
        "Choir": choir, "Bass": bass,
    }, bpm


# ══════════════════════════════════════════════════════
# Track 5 — Berserker  (aggressive guitar + orchestra)
# ══════════════════════════════════════════════════════
def track_05():
    print("  5. Berserker")
    dur = 88.0
    key = D_PHRYG
    bpm = 148.0
    chords = _chords("i bII VII i iv bVI bVII i i bII VII iv bVI bVII i", dur, key)

    # Heavy drums
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.12),
        style="rock", groove_swing=0.50, fill_frequency=0.30,
        auto_fills=True, section_type="chorus",
    ).render(chords, key, dur)

    # Galloping power chords
    power = PowerChordGenerator(
        GeneratorParams(density=0.70, key_range_low=28, key_range_high=52),
        pattern="gallop", palm_mute_ratio=0.4, gallop_speed=0.12,
    ).render(chords, key, dur)

    # Guitar solo — shred
    solo = SoloMelodyGenerator(
        GeneratorParams(density=0.60, key_range_low=48, key_range_high=80),
        style="shred_guitar", vibrato_depth=0.7, chromaticism=0.5,
    ).render(chords, key, dur)
    solo = spiceup(solo, key, depth=1)

    # Strings tremolo backing
    strings = StringsLegatoGenerator(
        GeneratorParams(density=0.55, key_range_low=43, key_range_high=72),
        section_size="ensemble", dynamic_shape="sustained",
        vibrato_amount=0.20,
    ).render(chords, key, dur)

    # Trumpet stabs
    trumpet = TrumpetGenerator(
        GeneratorParams(density=0.35, key_range_low=50, key_range_high=70),
        articulation="marcato", dynamic_curve="flat",
        fanfare_mode=True, note_density=1.5,
    ).render(chords, key, dur)

    # Trombone power
    trombone = TromboneGenerator(
        GeneratorParams(density=0.30, key_range_low=34, key_range_high=55),
        articulation="sustained", dynamic_curve="flat", bass_voice=False,
    ).render(chords, key, dur)

    # Timpani roll
    timp = TimpaniGenerator(
        GeneratorParams(density=0.10, key_range_low=36, key_range_high=43),
        stroke_pattern="roll", drum_count=4, roll_speed=0.1,
    ).render(chords, key, dur)

    # Bass
    bass = ContrabassGenerator(
        GeneratorParams(density=0.50, key_range_low=24, key_range_high=36),
        articulation="spiccato", dynamic_curve="flat",
    ).render(chords, key, dur)

    return {
        "Drums": drums, "PowerChord": power, "Solo": solo,
        "Strings": strings, "Trumpet": trumpet, "Trombone": trombone,
        "Timpani": timp, "Bass": bass,
    }, bpm


# ══════════════════════════════════════════════════════
# Track 6 — Fly Me To The Moon  (noir jazz-orchestral)
# ══════════════════════════════════════════════════════
def track_06():
    print("  6. Fly Me To The Moon")
    dur = 56.0
    key = C_MAJOR
    bpm = 126.0
    chords = _chords("I vi ii V I vi ii V iii VI ii V I vi ii V", dur, key)

    # Piano comp — jazz voicings
    comp = PianoCompGenerator(
        GeneratorParams(density=0.45, key_range_low=48, key_range_high=72),
        comp_style="jazz", voicing_type="rootless",
        accent_pattern="charleston", chord_density=0.8,
    ).render(chords, key, dur)

    # Strings legato
    strings = StringsLegatoGenerator(
        GeneratorParams(density=0.35, key_range_low=48, key_range_high=72),
        section_size="ensemble", dynamic_shape="sustained",
        vibrato_amount=0.10,
    ).render(chords, key, dur)

    # Trumpet melody — cool jazz
    trumpet = TrumpetGenerator(
        GeneratorParams(density=0.45, key_range_low=55, key_range_high=79),
        articulation="sustained", dynamic_curve="cresc_dim",
        note_density=1.3,
    ).render(chords, key, dur)

    # Walking bass
    bass = ContrabassGenerator(
        GeneratorParams(density=0.50, key_range_low=28, key_range_high=40),
        articulation="spiccato", dynamic_curve="flat",
    ).render(chords, key, dur)

    # Jazz drums
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.08),
        style="jazz", groove_swing=0.67, fill_frequency=0.15,
        auto_fills=True, section_type="verse",
    ).render(chords, key, dur)

    # French horn accent
    horns = FrenchHornGenerator(
        GeneratorParams(density=0.25, key_range_low=41, key_range_high=60),
        articulation="sustained", dynamic_curve="flat", note_density=0.8,
    ).render(chords, key, dur)

    return {
        "Comp": comp, "Strings": strings, "Trumpet": trumpet,
        "Bass": bass, "Drums": drums, "Horns": horns,
    }, bpm


# ══════════════════════════════════════════════════════
# Track 7 — Angel Attack  (epic orchestral rock climax)
# ══════════════════════════════════════════════════════
def track_07():
    print("  7. Angel Attack")
    dur = 96.0
    key = B_MINOR
    bpm = 140.0
    chords = _chords(
        "i iv V i VI III VII i i iv V III VI iv V i VII i", dur, key
    )

    # Full driving drums
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.12),
        style="rock", groove_swing=0.52, fill_frequency=0.25,
        auto_fills=True, section_type="chorus", flam_probability=0.05,
    ).render(chords, key, dur)

    # Power chord wall
    power = PowerChordGenerator(
        GeneratorParams(density=0.65, key_range_low=28, key_range_high=52),
        pattern="chug", palm_mute_ratio=0.35, include_octave=True,
    ).render(chords, key, dur)

    # Full string ensemble — soaring
    strings = StringsLegatoGenerator(
        GeneratorParams(density=0.55, key_range_low=43, key_range_high=79),
        section_size="ensemble", dynamic_shape="cresc_dim",
        vibrato_amount=0.15,
    ).render(chords, key, dur)

    # Brass section — massive hits
    brass = BrassSectionGenerator(
        GeneratorParams(density=0.50, key_range_low=40, key_range_high=67),
        articulation="hit", intensity=0.95, voicing="open", divisi_count=4,
    ).render(chords, key, dur)

    # French horns — heroic
    horns = FrenchHornGenerator(
        GeneratorParams(density=0.45, key_range_low=41, key_range_high=65),
        articulation="sustained", dynamic_curve="cresc_dim",
        fanfare_mode=True, note_density=1.3,
    ).render(chords, key, dur)

    # Trumpet fanfare
    trumpet = TrumpetGenerator(
        GeneratorParams(density=0.40, key_range_low=53, key_range_high=74),
        articulation="marcato", dynamic_curve="flat",
        fanfare_mode=True, note_density=1.5,
    ).render(chords, key, dur)

    # Choir — full power
    choir = ChoirAahsGenerator(
        GeneratorParams(density=0.30, key_range_low=43, key_range_high=65),
        voice_count=4, dynamics="ff", vibrato=0.4,
    ).render(chords, key, dur)

    # Ostinato drive
    ost = OstinatoGenerator(
        GeneratorParams(density=0.60, key_range_low=48, key_range_high=72),
        pattern="minor_second", use_scale_degrees=True,
        accent_pattern=[1.0, 0.7, 0.9, 0.5],
    ).render(chords, key, dur)

    # Timpani
    timp = TimpaniGenerator(
        GeneratorParams(density=0.10, key_range_low=36, key_range_high=43),
        stroke_pattern="roll", drum_count=4,
    ).render(chords, key, dur)

    # Contrabass
    bass = ContrabassGenerator(
        GeneratorParams(density=0.45, key_range_low=24, key_range_high=36),
        articulation="sustained", dynamic_curve="flat", bass_voice=True,
    ).render(chords, key, dur)

    # TamTam impact
    tamtam = TamTamGenerator(pattern_type="strike").render(chords, key, dur)

    return {
        "Drums": drums, "PowerChord": power, "Strings": strings,
        "Brass": brass, "Horns": horns, "Trumpet": trumpet,
        "Choir": choir, "Ostinato": ost, "Timpani": timp,
        "Bass": bass, "TamTam": tamtam,
    }, bpm


# ══════════════════════════════════════════════════════
# Track 8 — Requiem  (resolution — choir + orchestra)
# ══════════════════════════════════════════════════════
def track_08():
    print("  8. Requiem")
    dur = 72.0
    key = E_MAJOR
    bpm = 72.0
    chords = _chords("I vi IV V I iii IV V I vi IV V iii IV ii V", dur, key)

    # Choir — sustained, reverent
    choir = ChoirAahsGenerator(
        GeneratorParams(density=0.30, key_range_low=43, key_range_high=65),
        voice_count=4, dynamics="mf", vibrato=0.35,
    ).render(chords, key, dur)

    # Strings ensemble — warm
    strings = StringsLegatoGenerator(
        GeneratorParams(density=0.40, key_range_low=43, key_range_high=72),
        section_size="ensemble", dynamic_shape="cresc_dim",
        vibrato_amount=0.12,
    ).render(chords, key, dur)

    # French horn — noble
    horns = FrenchHornGenerator(
        GeneratorParams(density=0.35, key_range_low=41, key_range_high=60),
        articulation="sustained", dynamic_curve="cresc_dim",
        fanfare_mode=False, note_density=0.8,
    ).render(chords, key, dur)

    # Piano — gentle arpeggiated
    comp = PianoCompGenerator(
        GeneratorParams(density=0.35, key_range_low=48, key_range_high=72),
        comp_style="pop", voicing_type="close",
        accent_pattern="syncopated", chord_density=0.5,
    ).render(chords, key, dur)

    # Cello counter-melody
    cello = CelloGenerator(
        GeneratorParams(density=0.30, key_range_low=36, key_range_high=55),
        articulation="sustained", dynamic_curve="cresc_dim", vibrato=True,
    ).render(chords, key, dur)

    # Contrabass pedal
    bass = ContrabassGenerator(
        GeneratorParams(density=0.25, key_range_low=24, key_range_high=36),
        articulation="sustained", dynamic_curve="flat",
    ).render(chords, key, dur)

    # Timpani — final rolls
    timp = TimpaniGenerator(
        GeneratorParams(density=0.06, key_range_low=36, key_range_high=43),
        stroke_pattern="roll", drum_count=3,
    ).render(chords, key, dur)

    # Light drums
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.04),
        style="jazz", groove_swing=0.55, fill_frequency=0.05,
        auto_fills=True, section_type="outro",
    ).render(chords, key, dur)

    return {
        "Choir": choir, "Strings": strings, "Horns": horns,
        "Comp": comp, "Cello": cello, "Bass": bass,
        "Timpani": timp, "Drums": drums,
    }, bpm


# ── Track Registry ────────────────────────────────────

TRACKS = [
    # (function, filename, instruments_dict)
    (
        track_01,
        "01_Descent_Into_Darkness.mid",
        {
            "Pad": PAD_WARM, "Cello": CELLO, "Timpani": TIMPANI,
            "BassDrum": DRUMS, "Tension": ORGAN,
        },
    ),
    (
        track_02,
        "02_Evangelion.mid",
        {
            "Drums": DRUMS, "PowerChord": DIST_GUITAR, "Strings": STR_ENS1,
            "Brass": BRASS_SEC, "Horns": FR_HORN, "Choir": CHOIR,
            "Bass": CONTRABASS, "Timpani": TIMPANI,
        },
    ),
    (
        track_03,
        "03_Serenity.mid",
        {
            "Comp": PIANO, "Violin": VIOLIN, "Cello": CELLO,
            "Strings": STR_ENS1, "Bass": CONTRABASS, "Drums": DRUMS,
        },
    ),
    (
        track_04,
        "04_NERV_March.mid",
        {
            "Drums": DRUMS, "BassDrum": DRUMS, "TamTam": DRUMS,
            "Brass": BRASS_SEC, "Horns": FR_HORN, "Ostinato": STR_ENS2,
            "Choir": CHOIR, "Bass": CONTRABASS,
        },
    ),
    (
        track_05,
        "05_Berserker.mid",
        {
            "Drums": DRUMS, "PowerChord": DIST_GUITAR, "Solo": DIST_GUITAR,
            "Strings": STR_ENS1, "Trumpet": TRUMPET, "Trombone": TROMBONE,
            "Timpani": TIMPANI, "Bass": CONTRABASS,
        },
    ),
    (
        track_06,
        "06_Fly_Me_To_The_Moon.mid",
        {
            "Comp": PIANO, "Strings": STR_ENS1, "Trumpet": TRUMPET,
            "Bass": CONTRABASS, "Drums": DRUMS, "Horns": FR_HORN,
        },
    ),
    (
        track_07,
        "07_Angel_Attack.mid",
        {
            "Drums": DRUMS, "PowerChord": DIST_GUITAR, "Strings": STR_ENS1,
            "Brass": BRASS_SEC, "Horns": FR_HORN, "Trumpet": TRUMPET,
            "Choir": CHOIR, "Ostinato": STR_ENS2, "Timpani": TIMPANI,
            "Bass": CONTRABASS, "TamTam": DRUMS,
        },
    ),
    (
        track_08,
        "08_Requiem.mid",
        {
            "Choir": CHOIR, "Strings": STR_ENS1, "Horns": FR_HORN,
            "Comp": PIANO, "Cello": CELLO, "Bass": CONTRABASS,
            "Timpani": TIMPANI, "Drums": DRUMS,
        },
    ),
]


# ── Main ──────────────────────────────────────────────

def main():
    print("Sagisu Crisis — Symphonic Rock Album")
    print("=" * 50)

    for func, filename, instruments in TRACKS:
        raw, bpm = func()
        mastered = _mix(raw, bpm)
        out_path = os.path.join(BASE_DIR, filename)
        _export(mastered, bpm, instruments, out_path)
        print(f"    -> {out_path}")

    print(f"\nDone. {len(TRACKS)} tracks in {BASE_DIR}")


if __name__ == "__main__":
    main()
