# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_new_gens.py — "Echoes of the World: Electronic & Ethnic Symphony"
A beautiful 5-movement album showcasing our final phase General MIDI generators.
"""

import os
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams

# Import new generators
from melodica.generators.synth_effects import SynthEffectsGenerator
from melodica.generators.ethnic_world import EthnicWorldGenerator
from melodica.generators.sfx_percussion import SFXPercussionGenerator

# Import core modules
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.form import MusicalForm
from melodica.dynamics_arc import DynamicsArc
from melodica.orchestrator import OrchestralLayer, Orchestrator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# ---------------------------------------------------------------------------
# Scales
# ---------------------------------------------------------------------------

FS_MINOR = Scale(root=6, mode=Mode.AEOLIAN)   # F# Minor (root = 6)
D_MAJOR = Scale(root=2, mode=Mode.IONIAN)    # D Major (root = 2)
G_MINOR = Scale(root=7, mode=Mode.AEOLIAN)   # G Minor (root = 7)
A_MINOR = Scale(root=9, mode=Mode.AEOLIAN)   # A Minor (root = 9)
E_PHRYGIAN = Scale(root=4, mode=Mode.PHRYGIAN) # E Phrygian (root = 4)


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
        "Rain FX": 0.72, "Shamisen": 0.86, "Percussion": 0.80, "Deep Taiko": 0.90, "Strings Pad": 0.84,
        "Bagpipe": 0.85, "Steel Drums": 0.83, "Atmosphere FX": 0.74, "Tinkle Bell": 0.80,
        "Banjo Roll": 0.84, "Crystal FX": 0.78, "Agogo": 0.80, "Woodblock": 0.82,
        "Fiddle Solo": 0.88, "Sci-Fi Sweep": 0.76, "Goblins FX": 0.74, "Reverse Cymbal": 0.82, "Taiko Climax": 0.92,
        "Shanai Melodies": 0.86, "Soundtrack Pad": 0.84, "Ocean Waves": 0.76, "Breath Noise": 0.70, "Applause Climax": 0.80,
    })
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan


# ===========================================================================
# TRACK GENERATORS
# ===========================================================================

def track_01_rain_over_shamisen():
    """1. Rain over Shamisen (F# Minor, 68 BPM)"""
    print("  1. Rain over Shamisen")
    dur = 48.0
    chords = _build_chords("i iv v i VI ii i v", dur, FS_MINOR)

    form = MusicalForm.ternary(FS_MINOR, dur, base_bpm=68.0)
    arc = DynamicsArc.from_form(form)

    # Generators
    rain = SynthEffectsGenerator(fx_type="rain")
    shamisen = EthnicWorldGenerator(instrument="shamisen")
    woodblock = SFXPercussionGenerator(instrument="woodblock")
    taiko = SFXPercussionGenerator(instrument="taiko_drum")
    strings = StringsLegatoGenerator(ensemble_mode="section")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Rain FX", rain, "strings", "pad", "constant"),
            OrchestralLayer("Shamisen", shamisen, "strings", "melody", "sparse_to_dense"),
            OrchestralLayer("Percussion", woodblock, "percussion", "rhythm", "constant"),
            OrchestralLayer("Deep Taiko", taiko, "percussion", "rhythm", "constant"),
            OrchestralLayer("Strings Pad", strings, "strings", "pad", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, FS_MINOR, dur)
    return raw, 68.0


def track_02_highland_winds():
    """2. Highland Winds (D Major, 72 BPM)"""
    print("  2. Highland Winds")
    dur = 48.0
    chords = _build_chords("I IV V I vi ii V I", dur, D_MAJOR)

    form = MusicalForm.sonata(D_MAJOR, dur, base_bpm=72.0)
    arc = DynamicsArc.from_form(form)

    bagpipe = EthnicWorldGenerator(instrument="bagpipe")
    steel_drum = SFXPercussionGenerator(instrument="steel_drums")
    atmosphere = SynthEffectsGenerator(fx_type="atmosphere")
    bell = SFXPercussionGenerator(instrument="tinkle_bell")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Bagpipe", bagpipe, "woodwinds", "solo", "constant"),
            OrchestralLayer("Steel Drums", steel_drum, "percussion", "rhythm", "constant"),
            OrchestralLayer("Atmosphere FX", atmosphere, "strings", "pad", "constant"),
            OrchestralLayer("Tinkle Bell", bell, "percussion", "melody", "sparse_to_dense"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, D_MAJOR, dur)
    return raw, 72.0


def track_03_steampunk_clockwork():
    """3. Steampunk Clockwork (G Minor, 80 BPM)"""
    print("  3. Steampunk Clockwork")
    dur = 40.0
    chords = _build_chords("i VI iv v i v i v", dur, G_MINOR)

    form = MusicalForm.rondo(G_MINOR, dur, base_bpm=80.0)
    arc = DynamicsArc.from_form(form)

    banjo = EthnicWorldGenerator(instrument="banjo")
    crystal = SynthEffectsGenerator(fx_type="crystal")
    agogo = SFXPercussionGenerator(instrument="agogo")
    woodblock = SFXPercussionGenerator(instrument="woodblock")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Banjo Roll", banjo, "strings", "melody", "constant"),
            OrchestralLayer("Crystal FX", crystal, "strings", "harmony", "constant"),
            OrchestralLayer("Agogo", agogo, "percussion", "rhythm", "constant"),
            OrchestralLayer("Woodblock", woodblock, "percussion", "rhythm", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, G_MINOR, dur)
    return raw, 80.0


def track_04_fiddle_in_the_tempest():
    """4. Fiddle in the Tempest (A Minor, 85 BPM)"""
    print("  4. Fiddle in the Tempest")
    dur = 48.0
    chords = _build_chords("i VI III VII iv VI v i", dur, A_MINOR)

    form = MusicalForm.through_composed(A_MINOR, dur, base_bpm=85.0)
    arc = DynamicsArc.from_form(form)

    fiddle = EthnicWorldGenerator(instrument="fiddle")
    sci_fi = SynthEffectsGenerator(fx_type="sci_fi")
    goblins = SynthEffectsGenerator(fx_type="goblins")
    cymbal = SFXPercussionGenerator(instrument="reverse_cymbal")
    taiko = SFXPercussionGenerator(instrument="taiko_drum")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Fiddle Solo", fiddle, "strings", "solo", "constant"),
            OrchestralLayer("Sci-Fi Sweep", sci_fi, "strings", "pad", "constant"),
            OrchestralLayer("Goblins FX", goblins, "strings", "harmony", "constant"),
            OrchestralLayer("Reverse Cymbal", cymbal, "percussion", "rhythm", "constant"),
            OrchestralLayer("Taiko Climax", taiko, "percussion", "rhythm", "sparse_to_dense"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, A_MINOR, dur)
    return raw, 85.0


def track_05_eastern_dawn():
    """5. The Eastern Dawn (E Phrygian, 65 BPM)"""
    print("  5. The Eastern Dawn")
    dur = 56.0
    chords = _build_chords("i II i vii i II vii i", dur, E_PHRYGIAN)

    form = MusicalForm.sonata(E_PHRYGIAN, dur, base_bpm=65.0)
    arc = DynamicsArc.from_form(form)

    shanai = EthnicWorldGenerator(instrument="shanai")
    soundtrack = SynthEffectsGenerator(fx_type="soundtrack")
    seashore = SFXPercussionGenerator(instrument="seashore")
    breath = SFXPercussionGenerator(instrument="breath_noise")
    applause = SFXPercussionGenerator(instrument="applause")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Shanai Melodies", shanai, "woodwinds", "solo", "constant"),
            OrchestralLayer("Soundtrack Pad", soundtrack, "strings", "pad", "constant"),
            OrchestralLayer("Ocean Waves", seashore, "percussion", "pad", "constant"),
            OrchestralLayer("Breath Noise", breath, "woodwinds", "pad", "constant"),
            OrchestralLayer("Applause Climax", applause, "percussion", "harmony", "sparse_to_dense"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, E_PHRYGIAN, dur)
    return raw, 65.0


# ===========================================================================
# MAIN COMPOSER PIPELINE
# ===========================================================================

TRACKS = [
    (track_01_rain_over_shamisen,     "01_Rain_Over_Shamisen.mid", {
        "Rain FX": 95, "Shamisen": 105, "Percussion": 114, "Deep Taiko": 115, "Strings Pad": 48,
    }),
    (track_02_highland_winds,         "02_Highland_Winds.mid", {
        "Bagpipe": 108, "Steel Drums": 113, "Atmosphere FX": 98, "Tinkle Bell": 111,
    }),
    (track_03_steampunk_clockwork,    "03_Steampunk_Clockwork.mid", {
        "Banjo Roll": 104, "Crystal FX": 97, "Agogo": 112, "Woodblock": 114,
    }),
    (track_04_fiddle_in_the_tempest,  "04_Fiddle_In_The_Tempest.mid", {
        "Fiddle Solo": 109, "Sci-Fi Sweep": 102, "Goblins FX": 100, "Reverse Cymbal": 118, "Taiko Climax": 115,
    }),
    (track_05_eastern_dawn,           "05_The_Eastern_Dawn.mid", {
        "Shanai Melodies": 110, "Soundtrack Pad": 96, "Ocean Waves": 121, "Breath Noise": 120, "Applause Climax": 125,
    }),
]


def main():
    album_dir = Path("output/album_new_gens")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        E C H O E S   O F   T H E   W O R L D")
    print("        A 5-Movement Electronic & Ethnic World Symphony Suite")
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
    print(f"  COMPLETE: Echoes of the World — {total_notes} total notes across 5 movements")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
