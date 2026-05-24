# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_qw3762.py — "QW3762: Warm Evening"
A cozy, beautiful 10-movement symphonic album for a warm evening, utilizing the new Orchestral Arranger System.
"""

import os
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
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator
from melodica.generators.organ_drawbars import OrganDrawbarsGenerator

# Speciality generators
from melodica.generators.harp import HarpGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.canon import CanonGenerator
from melodica.generators.chorale import ChoraleGenerator
from melodica.generators.waltz import WaltzGenerator

# Core Arranger modules
from melodica.form import MusicalForm
from melodica.dynamics_arc import DynamicsArc
from melodica.orchestrator import OrchestralLayer, Orchestrator

from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer


# ---------------------------------------------------------------------------
# Scales
# ---------------------------------------------------------------------------

G_MAJOR = Scale(root=7, mode=Mode.IONIAN)
C_MAJOR = Scale(root=0, mode=Mode.IONIAN)
F_MAJOR = Scale(root=5, mode=Mode.IONIAN)
A_MINOR = Scale(root=9, mode=Mode.AEOLIAN)
E_MINOR = Scale(root=4, mode=Mode.AEOLIAN)
D_MINOR = Scale(root=2, mode=Mode.AEOLIAN)
BB_MAJOR = Scale(root=10, mode=Mode.IONIAN)
EB_MAJOR = Scale(root=3, mode=Mode.IONIAN)
D_MAJOR = Scale(root=2, mode=Mode.IONIAN)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

_harmonizer = CoupledHMMHarmonizer()


def _build_chords(progression: str, duration: float, key: Scale) -> list[ChordLabel]:
    """Generate chords via CoupledHMMHarmonizer from a seed melody."""
    # Build a simple seed melody from the scale degrees in the progression
    seed_melody = _make_seed_melody(progression, duration, key)
    return _harmonizer.harmonize(seed_melody, key, duration)


def _make_seed_melody(progression: str, duration: float, key: Scale) -> list[NoteInfo]:
    """Create a seed melody from roman numeral degrees for the HMM to harmonize."""
    parts = progression.split()
    beats_per = duration / len(parts)
    melody = []
    for i, p in enumerate(parts):
        chord = key.parse_roman(p)
        pitch = chord.root + 60
        melody.append(NoteInfo(
            pitch=pitch,
            start=i * beats_per,
            duration=beats_per * 0.8,
            velocity=70,
        ))
    return melody


def _clamp(notes: list[NoteInfo], lo: int = 1, hi: int = 127) -> list[NoteInfo]:
    for n in notes:
        n.velocity = max(lo, min(hi, n.velocity))
    return notes


def apply_symphonic_mix(raw_tracks: dict, bpm: float, lufs: float = -14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Violins": 0.82, "Viola": 0.80, "Cellos": 0.84, "Cello": 0.84, "Bass": 0.88,
        "Brass": 0.78, "Horns": 0.80, "Woodwinds": 0.82, "Flute": 0.80, "Oboe": 0.78,
        "Clarinet": 0.80, "Bassoon": 0.82, "Organ": 0.75, "Harp": 0.88, "Timpani": 0.90,
        "Mallet": 0.82, "Bells": 0.86, "String Ensemble": 0.85, "Brass Section": 0.80,
        "Pizzicato": 0.78, "Drone": 0.70, "Canon": 0.80, "Chorale": 0.82, "Waltz": 0.82,
    })
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan


# ===========================================================================
# TRACK GENERATORS
# ===========================================================================

def track_01_sunset():
    """1. Sunset Overture (G Major, 60 BPM)"""
    print("  1. Sunset Overture")
    dur = 48.0
    chords = _build_chords("I IV V I vi ii V I", dur, G_MAJOR)

    # Orchestrator
    form = MusicalForm.ternary(G_MAJOR, dur, base_bpm=60.0)
    arc = DynamicsArc.from_form(form)

    violins = ViolinGenerator(articulation="sustained", note_density=2.0)
    cellos = CelloGenerator(articulation="sustained", note_density=1.5, bass_voice=True)
    flute = FluteGenerator(articulation="legato", note_density=2.0)
    harp = HarpGenerator(spread_speed=0.1)

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Violins", violins, "strings", "melody", "constant"),
            OrchestralLayer("Cellos", cellos, "strings", "bass", "constant"),
            OrchestralLayer("Flute", flute, "woodwinds", "solo", "sparse_to_dense"),
            OrchestralLayer("Harp", harp, "strings", "harmony", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, G_MAJOR, dur)
    return raw, 60.0


def track_02_ember():
    """2. Warm Ember Dance (C Major, 76 BPM)"""
    print("  2. Warm Ember Dance")
    dur = 56.0
    chords = _build_chords("I V vi IV I V IV I", dur, C_MAJOR)

    flute_p = GeneratorParams(density=0.6)
    flute = FluteGenerator(flute_p, articulation="staccato", note_density=3.0)
    flute_notes = _clamp(flute.render(chords, C_MAJOR, dur), 40, 85)

    clar_p = GeneratorParams(density=0.55)
    clar = ClarinetGenerator(clar_p, articulation="staccato", note_density=3.0)
    clar_notes = _clamp(clar.render(chords, C_MAJOR, dur), 35, 80)

    pizz_p = GeneratorParams(density=0.6)
    pizz = StringsPizzicatoGenerator(pizz_p, pattern="ostinato")
    pizz_notes = _clamp(pizz.render(chords, C_MAJOR, dur), 35, 75)

    return {
        "Flute": flute_notes,
        "Clarinet": clar_notes,
        "Pizzicato": pizz_notes,
    }, 76.0


def track_03_fireplace():
    """3. Cozy Fireplace (F Major, 54 BPM)"""
    print("  3. Cozy Fireplace")
    dur = 64.0
    chords = _build_chords("I vi IV V I vi V I", dur, F_MAJOR)

    form = MusicalForm.sonata(F_MAJOR, dur, base_bpm=54.0)
    arc = DynamicsArc.from_form(form)

    strings = StringsLegatoGenerator(ensemble_mode="tutti")
    cellos = CelloGenerator(articulation="sustained", note_density=2.2, bass_voice=True)
    horns = FrenchHornGenerator(articulation="sustained", note_density=2.0)

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("String Ensemble", strings, "strings", "pad", "constant"),
            OrchestralLayer("Cellos", cellos, "strings", "bass", "constant"),
            OrchestralLayer("Horns", horns, "brass", "harmony", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, F_MAJOR, dur)
    return raw, 54.0


def track_04_promenade():
    """4. Starlight Promenade (G Major, 66 BPM)"""
    print("  4. Starlight Promenade")
    dur = 48.0
    chords = _build_chords("I IV V I I IV V I", dur, G_MAJOR)

    strings = StringsLegatoGenerator(ensemble_mode="chamber")
    strings_notes = _clamp(strings.render(chords, G_MAJOR, dur), 35, 75)

    clar = ClarinetGenerator(articulation="staccato", note_density=2.5)
    clar_notes = _clamp(clar.render(chords, G_MAJOR, dur), 40, 85)

    gl_p = GeneratorParams(density=0.45)
    glock = MalletPercussionGenerator(gl_p, instrument="glockenspiel", pattern="arpeggio")
    glock_notes = _clamp(glock.render(chords, G_MAJOR, dur), 35, 65)

    return {
        "String Ensemble": strings_notes,
        "Clarinet": clar_notes,
        "Mallet": glock_notes,
    }, 66.0


def track_05_solitude():
    """5. Twilight Solitude (A Minor, 48 BPM)"""
    print("  5. Twilight Solitude")
    dur = 64.0
    chords = _build_chords("i iv v i VI iv V i", dur, A_MINOR)

    oboe = OboeGenerator(articulation="sustained", note_density=2.2, vibrato=True)
    oboe_notes = _clamp(oboe.render(chords, A_MINOR, dur), 30, 80)

    drone_p = GeneratorParams(density=0.4)
    drone = DroneGenerator(drone_p, variant="tonic")
    drone_notes = _clamp(drone.render(chords, A_MINOR, dur), 25, 45)

    organ_p = GeneratorParams(density=0.35)
    organ = OrganDrawbarsGenerator(organ_p, registration="jazz")
    organ_notes = _clamp(organ.render(chords, A_MINOR, dur), 25, 50)

    return {
        "Oboe": oboe_notes,
        "Drone": drone_notes,
        "Organ": organ_notes,
    }, 48.0


def track_06_valleys():
    """6. Misty Valleys (E Minor, 50 BPM)"""
    print("  6. Misty Valleys")
    dur = 60.0
    chords = _build_chords("i iv v i VI iv V i", dur, E_MINOR)

    form = MusicalForm.ternary(E_MINOR, dur, base_bpm=50.0)
    arc = DynamicsArc.from_form(form)

    strings = StringsLegatoGenerator(ensemble_mode="chamber")
    cellos = CelloGenerator(articulation="sustained", note_density=2.0)
    timp = TimpaniGenerator(stroke_pattern="roll")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("String Ensemble", strings, "strings", "pad", "constant"),
            OrchestralLayer("Cellos", cellos, "strings", "melody", "constant"),
            OrchestralLayer("Timpani", timp, "percussion", "rhythm", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, E_MINOR, dur)
    return raw, 50.0


def track_07_echoes():
    """7. Evening Echoes (D Minor, 58 BPM)"""
    print("  7. Evening Echoes")
    dur = 56.0
    chords = _build_chords("i iv v i VI iv V i", dur, D_MINOR)

    canon_p = GeneratorParams(density=0.55)
    canon = CanonGenerator(canon_p, canon_type="tonal", delay_beats=3.0)
    canon_notes = _clamp(canon.render(chords, D_MINOR, dur), 35, 75)

    harp_p = GeneratorParams(density=0.45)
    harp = HarpGenerator(harp_p, pattern="arpeggio")
    harp_notes = _clamp(harp.render(chords, D_MINOR, dur), 30, 65)

    viola = ViolaGenerator(note_density=2.0)
    viola_notes = _clamp(viola.render(chords, D_MINOR, dur), 30, 65)

    return {
        "Canon": canon_notes,
        "Harp": harp_notes,
        "Viola": viola_notes,
    }, 58.0


def track_08_serenade():
    """8. Serenade under the Moon (Bb Major, 52 BPM)"""
    print("  8. Serenade under the Moon")
    dur = 64.0
    chords = _build_chords("I IV V I vi ii V I", dur, BB_MAJOR)

    chorale_p = GeneratorParams(density=0.5)
    chorale = ChoraleGenerator(chorale_p, voice_spacing=12)
    chorale_notes = _clamp(chorale.render(chords, BB_MAJOR, dur), 35, 70)

    cello = CelloGenerator(articulation="legato", note_density=2.0)
    cello_notes = _clamp(cello.render(chords, BB_MAJOR, dur), 30, 75)

    bells_p = GeneratorParams(density=0.2)
    bells = TubularBellsGenerator(bells_p, stroke_pattern="chime")
    bells_notes = _clamp(bells.render(chords, BB_MAJOR, dur), 35, 60)

    return {
        "Chorale": chorale_notes,
        "Cello": cello_notes,
        "Bells": bells_notes,
    }, 52.0


def track_09_dreams():
    """9. Nocturne of Dreams (Eb Major, 46 BPM)"""
    print("  9. Nocturne of Dreams")
    dur = 72.0
    chords = _build_chords("I IV V I vi ii V I", dur, EB_MAJOR)

    form = MusicalForm.ternary(EB_MAJOR, dur, base_bpm=46.0)
    arc = DynamicsArc.from_form(form)

    strings = StringsLegatoGenerator(ensemble_mode="tutti")
    woodwinds = WoodwindsEnsembleGenerator(ensemble_mode="tutti")
    horns = FrenchHornGenerator(articulation="sustained", note_density=1.5)

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("String Ensemble", strings, "strings", "pad", "constant"),
            OrchestralLayer("Woodwinds", woodwinds, "woodwinds", "harmony", "constant"),
            OrchestralLayer("Horns", horns, "brass", "melody", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, EB_MAJOR, dur)
    return raw, 46.0


def track_10_resolution():
    """10. Dawn Resolution (D Major, 62 BPM)"""
    print("  10. Dawn Resolution")
    dur = 80.0
    chords = _build_chords("I IV V I vi ii V I I IV V I", dur, D_MAJOR)

    form = MusicalForm.sonata(D_MAJOR, dur, base_bpm=62.0)
    arc = DynamicsArc.from_form(form)

    strings = StringsLegatoGenerator(ensemble_mode="tutti")
    brass = BrassSectionGenerator(ensemble_mode="tutti")
    woodwinds = WoodwindsEnsembleGenerator(ensemble_mode="tutti")
    timp = TimpaniGenerator(stroke_pattern="single")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("String Ensemble", strings, "strings", "pad", "constant"),
            OrchestralLayer("Brass Section", brass, "brass", "rhythm", "constant"),
            OrchestralLayer("Woodwinds", woodwinds, "woodwinds", "harmony", "constant"),
            OrchestralLayer("Timpani", timp, "percussion", "rhythm", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, D_MAJOR, dur)
    return raw, 62.0


# ===========================================================================
# MAIN COMPOSER
# ===========================================================================

TRACKS = [
    (track_01_sunset,     "01_Sunset_Overture.mid", {
        "Violins": 40, "Cellos": 42, "Flute": 73, "Harp": 46,
    }),
    (track_02_ember,      "02_Warm_Ember_Dance.mid", {
        "Flute": 73, "Clarinet": 71, "Pizzicato": 45,
    }),
    (track_03_fireplace,  "03_Cozy_Fireplace.mid", {
        "String Ensemble": 48, "Cellos": 42, "Horns": 60,
    }),
    (track_04_promenade,  "04_Starlight_Promenade.mid", {
        "String Ensemble": 48, "Clarinet": 71, "Mallet": 9,
    }),
    (track_05_solitude,   "05_Twilight_Solitude.mid", {
        "Oboe": 68, "Drone": 43, "Organ": 19,
    }),
    (track_06_valleys,    "06_Misty_Valleys.mid", {
        "String Ensemble": 48, "Cellos": 42, "Timpani": 47,
    }),
    (track_07_echoes,     "07_Evening_Echoes.mid", {
        "Canon": 73, "Harp": 46, "Viola": 41,
    }),
    (track_08_serenade,   "08_Serenade_Under_The_Moon.mid", {
        "Chorale": 48, "Cello": 42, "Bells": 14,
    }),
    (track_09_dreams,     "09_Nocturne_Of_Dreams.mid", {
        "String Ensemble": 48, "Woodwinds": 71, "Horns": 60,
    }),
    (track_10_resolution, "10_Dawn_Resolution.mid", {
        "String Ensemble": 48, "Brass Section": 61, "Woodwinds": 68, "Timpani": 47,
    }),
]


def main():
    album_dir = Path("output/album_qw3762")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        Q W 3 7 6 2   —   W A R M   E V E N I N G")
    print("        A 10-Movement Symphonic Cozy Suite")
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
    print(f"  COMPLETE: QW3762 — {total_notes} total notes across 10 movements")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
