# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_afro_symphony.py — "Symphony of the Savannah: African Symphonic Suite"
A beautiful 5-movement suite merging classical symphonic orchestration with polyrhythmic African generators.
"""

import os
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams

# Import classical generators
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.orchestral_brass import FrenchHornGenerator
from melodica.generators.orchestral_woodwinds import FluteGenerator
from melodica.generators.orchestral_percussion import (
    TimpaniGenerator,
    MalletPercussionGenerator,
)

# Import African generators
from melodica.generators.highlife_guitar import HighlifeGuitarGenerator
from melodica.generators.soukous_guitar import SoukousGuitarGenerator
from melodica.generators.amapiano_logdrum import AmapianoLogDrumGenerator
from melodica.generators.afro_percussion import AfroPercussionGenerator

# Import core modules
from melodica.form import MusicalForm
from melodica.dynamics_arc import DynamicsArc
from melodica.orchestrator import OrchestralLayer, Orchestrator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# ---------------------------------------------------------------------------
# Scales
# ---------------------------------------------------------------------------

D_MAJOR = Scale(root=2, mode=Mode.IONIAN)       # D Major
G_MINOR = Scale(root=7, mode=Mode.AEOLIAN)      # G Minor
A_MAJOR = Scale(root=9, mode=Mode.IONIAN)       # A Major
E_MINOR = Scale(root=4, mode=Mode.AEOLIAN)      # E Minor
D_PHRYGIAN = Scale(root=2, mode=Mode.PHRYGIAN)   # D Phrygian


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _build_chords(progression: str, duration: float, key: Scale) -> list[ChordLabel]:
    parts = progression.split()
    beats_per = duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        chord = key.parse_roman(p)
        chord.start = i * beats_per
        chord.duration = beats_per
        chords.append(chord)
    return chords


def apply_symphonic_mix(raw_tracks: dict, bpm: float, lufs: float = -14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Symphonic Strings": 0.84, "Highlife Guitar": 0.85, "Afro Percussion": 0.82, "Symphonic Flute": 0.80,
        "Tutti Brass": 0.82, "Samba Drums": 0.84, "Timpani": 0.90, "Strings Pizzicato": 0.80,
        "Soukous Guitar": 0.86, "Woodwind Dialogue": 0.82,
        "Amapiano Logdrum": 0.88, "French Horns": 0.82, "Strings Legato": 0.84, "Campfire Chimes": 0.80,
        "Tutti Strings": 0.85, "Afro Drum Ensemble": 0.84, "Highlife Lead": 0.86,
    })
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan


# ===========================================================================
# TRACK GENERATORS
# ===========================================================================

def track_01_awakening():
    """1. Awakening Savannah (D Major, 115 BPM)"""
    print("  1. Awakening Savannah")
    dur = 48.0
    chords = _build_chords("I IV V I vi ii V I", dur, D_MAJOR)

    form = MusicalForm.ternary(D_MAJOR, dur, base_bpm=115.0)
    arc = DynamicsArc.from_form(form)

    strings = StringsLegatoGenerator(ensemble_mode="chamber")
    guitar = HighlifeGuitarGenerator()
    perc = AfroPercussionGenerator(ensemble="west_african")
    flute = FluteGenerator()

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Symphonic Strings", strings, "strings", "pad", "constant"),
            OrchestralLayer("Highlife Guitar", guitar, "strings", "melody", "constant"),
            OrchestralLayer("Afro Percussion", perc, "percussion", "rhythm", "constant"),
            OrchestralLayer("Symphonic Flute", flute, "woodwinds", "solo", "sparse_to_dense"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, D_MAJOR, dur)
    return raw, 115.0


def track_02_djembe_dance():
    """2. Dance of the Djembe (G Minor, 120 BPM)"""
    print("  2. Dance of the Djembe")
    dur = 48.0
    chords = _build_chords("i VI iv v i VI iv v", dur, G_MINOR)

    form = MusicalForm.sonata(G_MINOR, dur, base_bpm=120.0)
    arc = DynamicsArc.from_form(form)

    brass = BrassSectionGenerator(ensemble_mode="section")
    perc = AfroPercussionGenerator(ensemble="cuban_afro")
    timp = TimpaniGenerator(stroke_pattern="single")
    pizz = StringsPizzicatoGenerator()

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Tutti Brass", brass, "brass", "pad", "constant"),
            OrchestralLayer("Samba Drums", perc, "percussion", "rhythm", "constant"),
            OrchestralLayer("Timpani", timp, "percussion", "rhythm", "constant"),
            OrchestralLayer("Strings Pizzicato", pizz, "strings", "harmony", "sparse_to_dense"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, G_MINOR, dur)
    return raw, 120.0


def track_03_soukous_sunset():
    """3. Soukous Sunset (A Major, 118 BPM)"""
    print("  3. Soukous Sunset")
    dur = 40.0
    chords = _build_chords("I IV V I I IV V I", dur, A_MAJOR)

    form = MusicalForm.rondo(A_MAJOR, dur, base_bpm=118.0)
    arc = DynamicsArc.from_form(form)

    guitar = SoukousGuitarGenerator()
    woodwinds = WoodwindsEnsembleGenerator(ensemble_mode="chamber")
    pizz = StringsPizzicatoGenerator()

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Soukous Guitar", guitar, "strings", "melody", "constant"),
            OrchestralLayer("Woodwind Dialogue", woodwinds, "woodwinds", "harmony", "constant"),
            OrchestralLayer("Strings Pizzicato", pizz, "strings", "rhythm", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, A_MAJOR, dur)
    return raw, 118.0


def track_04_earthy_echoes():
    """4. Earthy Echoes (Amapiano Nocturne) (E Minor, 122 BPM)"""
    print("  4. Earthy Echoes (Amapiano Nocturne)")
    dur = 48.0
    chords = _build_chords("i VI III VII i VI III VII", dur, E_MINOR)

    form = MusicalForm.ternary(E_MINOR, dur, base_bpm=122.0)
    arc = DynamicsArc.from_form(form)

    logdrum = AmapianoLogDrumGenerator()
    horns = FrenchHornGenerator()
    strings = StringsLegatoGenerator(ensemble_mode="section")
    chimes = MalletPercussionGenerator(instrument="glockenspiel")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Amapiano Logdrum", logdrum, "bass", "bass", "constant"),
            OrchestralLayer("French Horns", horns, "brass", "harmony", "constant"),
            OrchestralLayer("Strings Legato", strings, "strings", "pad", "constant"),
            OrchestralLayer("Campfire Chimes", chimes, "percussion", "melody", "sparse_to_dense"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, E_MINOR, dur)
    return raw, 122.0


def track_05_triumph():
    """5. Savannah Triumph (D Phrygian, 125 BPM)"""
    print("  5. Savannah Triumph")
    dur = 64.0
    chords = _build_chords("i II i vii i II vii i i II i vii", dur, D_PHRYGIAN)

    form = MusicalForm.sonata(D_PHRYGIAN, dur, base_bpm=125.0)
    arc = DynamicsArc.from_form(form)

    strings = StringsLegatoGenerator(ensemble_mode="tutti")
    brass = BrassSectionGenerator(ensemble_mode="tutti")
    timp = TimpaniGenerator(stroke_pattern="tremolo")
    perc = AfroPercussionGenerator(ensemble="west_african", density=0.8)
    guitar = HighlifeGuitarGenerator()

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Tutti Strings", strings, "strings", "pad", "constant"),
            OrchestralLayer("Tutti Brass", brass, "brass", "pad", "constant"),
            OrchestralLayer("Timpani", timp, "percussion", "rhythm", "constant"),
            OrchestralLayer("Afro Drum Ensemble", perc, "percussion", "rhythm", "constant"),
            OrchestralLayer("Highlife Lead", guitar, "strings", "melody", "sparse_to_dense"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, D_PHRYGIAN, dur)
    return raw, 125.0


# ===========================================================================
# MAIN COMPOSER PIPELINE
# ===========================================================================

TRACKS = [
    (track_01_awakening,      "01_Awakening_Savannah.mid", {
        "Symphonic Strings": 48, "Highlife Guitar": 24, "Afro Percussion": 114, "Symphonic Flute": 73,
    }),
    (track_02_djembe_dance,   "02_Dance_Of_The_Djembe.mid", {
        "Tutti Brass": 61, "Samba Drums": 114, "Timpani": 47, "Strings Pizzicato": 45,
    }),
    (track_03_soukous_sunset, "03_Soukous_Sunset.mid", {
        "Soukous Guitar": 26, "Woodwind Dialogue": 71, "Strings Pizzicato": 45,
    }),
    (track_04_earthy_echoes,  "04_Earthy_Echoes.mid", {
        "Amapiano Logdrum": 38, "French Horns": 60, "Strings Legato": 48, "Campfire Chimes": 9,
    }),
    (track_05_triumph,        "05_Savannah_Triumph.mid", {
        "Tutti Strings": 48, "Tutti Brass": 61, "Timpani": 47, "Afro Drum Ensemble": 114, "Highlife Lead": 24,
    }),
]


def main():
    album_dir = Path("output/album_afro_symphony")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        S Y M P H O N Y   O F   T H E   S A V A N N A H")
    print("        A 5-Movement African Symphonic Suite")
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
    print(f"  COMPLETE: Symphony of the Savannah — {total_notes} total notes across 5 movements")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
