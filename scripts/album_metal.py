# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_metal.py — "Titanium Reign: Heavy & Symphonic Metal Suite"
A beautiful 5-movement heavy metal album sectionally arranged using custom FormSections.
"""

import os
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams

# Import heavy rock/metal generators
from melodica.generators.power_chord import PowerChordGenerator
from melodica.generators.bass_solo import BassSoloGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.guitar_tapping import GuitarTappingGenerator
from melodica.generators.riff import RiffGenerator

# Import classical & synth generators
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.synth_effects import SynthEffectsGenerator
from melodica.generators.synth_modern import SynthLeadGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator

# Import core arranger modules
from melodica.form import FormSection, MusicalForm
from melodica.dynamics_arc import DynamicsArc
from melodica.orchestrator import OrchestralLayer, Orchestrator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# ---------------------------------------------------------------------------
# Scales
# ---------------------------------------------------------------------------

D_MINOR = Scale(root=2, mode=Mode.AEOLIAN)       # D Minor
E_MINOR = Scale(root=4, mode=Mode.AEOLIAN)      # E Minor
A_MINOR = Scale(root=9, mode=Mode.AEOLIAN)      # A Minor
FS_PHRYGIAN = Scale(root=6, mode=Mode.PHRYGIAN)  # F# Phrygian


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
        "Chug Guitars": 0.88, "Industrial Bass": 0.86, "Heavy Drums": 0.90, "Ambient FX": 0.72,
        "Gallop Guitars": 0.88, "Power Bass": 0.86, "Metal Drums": 0.90, "Symphonic Strings": 0.84, "Screaming Solo": 0.85,
        "Tapping Shred": 0.86, "Syncopated Riffs": 0.88, "Prog Bass": 0.86, "Prog Drums": 0.90,
        "Thrash Riffs": 0.88, "Snap Bass": 0.86, "Thrash Drums": 0.90, "Sci-Fi Sweep": 0.74,
        "Sustained Riffs": 0.88, "Tutti Strings": 0.85, "Tutti Brass": 0.82, "Timpani Tremolo": 0.88, "Screaming Lead": 0.86,
    })
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan


# ===========================================================================
# TRACK GENERATORS
# ===========================================================================

def track_01_industrial():
    """1. Industrial Chug (D Minor, 130 BPM)"""
    print("  1. Industrial Chug")
    dur = 48.0
    chords = _build_chords("i iv v i VI ii i v i iv v i", dur, D_MINOR)

    # Custom sectional development
    sections = [
        FormSection("Intro", 0.0, 8.0, "mp", 0.95, ["strings"], "mysterious"),
        FormSection("Verse", 8.0, 16.0, "mf", 1.0, ["strings", "bass", "percussion"], "tense"),
        FormSection("Chorus", 24.0, 16.0, "ff", 1.0, ["strings", "bass", "percussion"], "triumphant"),
        FormSection("Outro", 40.0, 8.0, "p", 0.90, ["strings", "percussion"], "dark"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 130.0)
    arc = DynamicsArc.from_form(form)

    guitars = PowerChordGenerator(pattern="chug", palm_mute_ratio=0.7)
    bass = BassSoloGenerator(instrument="pick_bass")
    drums = DrumKitPatternGenerator(style="rock", hihat_pattern="eighth")
    ambient = SynthEffectsGenerator(fx_type="goblins")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Chug Guitars", guitars, "strings", "rhythm", "constant"),
            OrchestralLayer("Industrial Bass", bass, "bass", "bass", "constant"),
            OrchestralLayer("Heavy Drums", drums, "percussion", "rhythm", "constant"),
            OrchestralLayer("Ambient FX", ambient, "strings", "pad", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, D_MINOR, dur)
    return raw, 130.0


def track_02_gallop():
    """2. Galloping Tempest (E Minor, 140 BPM)"""
    print("  2. Galloping Tempest")
    dur = 64.0
    chords = _build_chords("i VI III VII i VI III VII i VI III VII i VI III VII", dur, E_MINOR)

    # Custom sectional development
    sections = [
        FormSection("Intro", 0.0, 8.0, "p", 0.90, ["strings"], "mysterious"),
        FormSection("Verse", 8.0, 16.0, "mf", 1.0, ["strings", "bass", "percussion"], "tense"),
        FormSection("Chorus", 24.0, 16.0, "ff", 1.0, ["strings", "bass", "percussion"], "triumphant"),
        FormSection("Guitar_Solo", 40.0, 12.0, "f", 1.05, ["strings", "bass", "percussion"], "frantic"),
        FormSection("Outro", 52.0, 12.0, "mp", 0.85, ["strings"], "mysterious"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 140.0)
    arc = DynamicsArc.from_form(form)

    guitars = PowerChordGenerator(pattern="gallop", palm_mute_ratio=0.5)
    bass = BassSoloGenerator(instrument="pick_bass")
    drums = DrumKitPatternGenerator(style="rock", hihat_pattern="open")
    strings = StringsLegatoGenerator(ensemble_mode="section")
    solo = SynthLeadGenerator(lead_type="sawtooth")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Gallop Guitars", guitars, "strings", "rhythm", "constant"),
            OrchestralLayer("Power Bass", bass, "bass", "bass", "constant"),
            OrchestralLayer("Metal Drums", drums, "percussion", "rhythm", "constant"),
            OrchestralLayer("Symphonic Strings", strings, "strings", "pad", "constant"),
            OrchestralLayer("Screaming Solo", solo, "strings", "solo", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, E_MINOR, dur)
    return raw, 140.0


def track_03_shred():
    """3. Shredding the Void (A Minor, 135 BPM)"""
    print("  3. Shredding the Void")
    dur = 48.0
    chords = _build_chords("i VI iv v i v i v i VI iv v", dur, A_MINOR)

    # Custom sectional development
    sections = [
        FormSection("Intro", 0.0, 8.0, "mf", 1.0, ["strings", "percussion"], "tense"),
        FormSection("Verse", 8.0, 16.0, "f", 1.0, ["strings", "bass", "percussion"], "frantic"),
        FormSection("Chorus", 24.0, 16.0, "ff", 1.05, ["strings", "bass", "percussion"], "triumphant"),
        FormSection("Outro", 40.0, 8.0, "mp", 0.90, ["strings"], "dark"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 135.0)
    arc = DynamicsArc.from_form(form)

    tapping = GuitarTappingGenerator(pattern="arpeggio", width_interval=12)
    riffs = PowerChordGenerator(pattern="syncopated", palm_mute_ratio=0.8)
    bass = BassSoloGenerator(instrument="pick_bass")
    drums = DrumKitPatternGenerator(style="rock", hihat_pattern="sixteenth")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Tapping Shred", tapping, "strings", "solo", "constant"),
            OrchestralLayer("Syncopated Riffs", riffs, "strings", "rhythm", "constant"),
            OrchestralLayer("Prog Bass", bass, "bass", "bass", "constant"),
            OrchestralLayer("Prog Drums", drums, "percussion", "rhythm", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, A_MINOR, dur)
    return raw, 135.0


def track_04_wrath():
    """4. Phrygian Wrath (F# Phrygian, 128 BPM)"""
    print("  4. Phrygian Wrath")
    dur = 48.0
    chords = _build_chords("i II i vii i II vii i i II i vii", dur, FS_PHRYGIAN)

    # Custom sectional development
    sections = [
        FormSection("Intro", 0.0, 8.0, "mp", 0.95, ["strings"], "mysterious"),
        FormSection("Verse", 8.0, 16.0, "mf", 1.0, ["strings", "bass", "percussion"], "tense"),
        FormSection("Chorus", 24.0, 16.0, "ff", 1.0, ["strings", "bass", "percussion"], "triumphant"),
        FormSection("Outro", 40.0, 8.0, "p", 0.85, ["strings"], "dark"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 128.0)
    arc = DynamicsArc.from_form(form)

    riffs = RiffGenerator(scale_type="blues", riff_pattern="gallop")
    bass = BassSoloGenerator(instrument="pick_bass")
    drums = DrumKitPatternGenerator(style="rock")
    sweep = SynthEffectsGenerator(fx_type="sci_fi")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Thrash Riffs", riffs, "strings", "rhythm", "constant"),
            OrchestralLayer("Snap Bass", bass, "bass", "bass", "constant"),
            OrchestralLayer("Thrash Drums", drums, "percussion", "rhythm", "constant"),
            OrchestralLayer("Sci-Fi Sweep", sweep, "strings", "pad", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, FS_PHRYGIAN, dur)
    return raw, 128.0


def track_05_finale():
    """5. Titanium Climax (Symphonic Finale) (D Minor, 145 BPM)"""
    print("  5. Titanium Climax (Symphonic Finale)")
    dur = 64.0
    chords = _build_chords("i iv v i VI ii i v i iv v i i iv v i", dur, D_MINOR)

    # Custom sectional development
    sections = [
        FormSection("Intro", 0.0, 16.0, "p", 0.85, ["strings", "brass"], "mysterious"),
        FormSection("Verse", 16.0, 16.0, "mf", 1.0, ["strings", "brass", "percussion"], "tense"),
        FormSection("Chorus", 32.0, 24.0, "ff", 1.05, ["strings", "brass", "percussion"], "triumphant"),
        FormSection("Outro", 56.0, 8.0, "pp", 0.80, ["strings"], "mysterious"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 145.0)
    arc = DynamicsArc.from_form(form)

    riffs = PowerChordGenerator(pattern="sustained")
    strings = StringsLegatoGenerator(ensemble_mode="tutti")
    brass = BrassSectionGenerator(ensemble_mode="tutti")
    timp = TimpaniGenerator(stroke_pattern="tremolo")
    solo = SynthLeadGenerator(lead_type="charang")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Sustained Riffs", riffs, "strings", "rhythm", "constant"),
            OrchestralLayer("Tutti Strings", strings, "strings", "pad", "constant"),
            OrchestralLayer("Tutti Brass", brass, "brass", "pad", "constant"),
            OrchestralLayer("Timpani Tremolo", timp, "percussion", "rhythm", "constant"),
            OrchestralLayer("Screaming Lead", solo, "strings", "solo", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, D_MINOR, dur)
    return raw, 145.0


# ===========================================================================
# MAIN COMPOSER PIPELINE
# ===========================================================================

TRACKS = [
    (track_01_industrial, "01_Industrial_Chug.mid", {
        "Chug Guitars": 29, "Industrial Bass": 34, "Heavy Drums": 0, "Ambient FX": 100,
    }),
    (track_02_gallop,     "02_Galloping_Tempest.mid", {
        "Gallop Guitars": 29, "Power Bass": 34, "Metal Drums": 0, "Symphonic Strings": 48, "Screaming Solo": 80,
    }),
    (track_03_shred,      "03_Shredding_The_Void.mid", {
        "Tapping Shred": 30, "Syncopated Riffs": 29, "Prog Bass": 34, "Prog Drums": 0,
    }),
    (track_04_wrath,      "04_Phrygian_Wrath.mid", {
        "Thrash Riffs": 29, "Snap Bass": 34, "Thrash Drums": 0, "Sci-Fi Sweep": 102,
    }),
    (track_05_finale,     "05_Titanium_Climax.mid", {
        "Sustained Riffs": 29, "Tutti Strings": 48, "Tutti Brass": 61, "Timpani Tremolo": 47, "Screaming Lead": 84,
    }),
]


def main():
    album_dir = Path("output/album_metal")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        T I T A N I U M   R E I G N")
    print("        A 5-Movement Heavy & Symphonic Metal Suite (Sectional Version)")
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
    print(f"  COMPLETE: Titanium Reign — {total_notes} total notes across 5 movements")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
