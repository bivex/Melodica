# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/electronic/album_structured.py — "Patterns of Time" Structured Breakbeat Album.

An album featuring 3 tracks with complex, staggered arrangements built using the
structure_to_schedule method of the Melodica IdeaTool.

Tracks:
  1. Grid Theory — 86 BPM — F Minor (32 bars structured via AABB/CC/R)
  2. Staggered State — 92 BPM — D Dorian (24 bars structured via ABAC/R)
  3. Climax Protocol — 80 BPM — G Minor (32 bars structured via ABC/Climax/R)
"""

import random
import sys
from pathlib import Path

from melodica.types import Scale, Mode, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.breakbeat import BreakbeatGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, structure_to_schedule
from melodica.composer.album_pipeline import produce_track, Mood

# GM Programs mapping
PIANO = 0
SYNTH_BASS = 38
DARK_PAD = 88
SYNTH_LEAD = 80
POLYSYNTH = 90
EFFECTS = 96
DRUMS = 0
GLOCKENSPIEL = 9
HARP = 46

random.seed(9876)
OUT = Path("output/album_structured")
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# Diagnostic & Post-processing Helpers
# ------------------------------------------------------------------
def scale_velocity_spread(notes: list[NoteInfo], target_min=50, target_max=110) -> list[NoteInfo]:
    """Ensure dynamic expression by scaling velocity to fit a wider range."""
    if not notes:
        return notes
    vels = [n.velocity for n in notes]
    min_v, max_v = min(vels), max(vels)
    if max_v == min_v:
        for n in notes:
            n.velocity = target_max
        return notes
    for n in notes:
        scaled = target_min + (n.velocity - min_v) / (max_v - min_v) * (target_max - target_min)
        n.velocity = int(max(1, min(127, scaled)))
    return notes


def resolve_register_crossing(bass: list[NoteInfo], pads: list[NoteInfo], leads: list[NoteInfo]):
    """Force clean register separation to prevent voice crossings."""
    # Bass should stay strictly in the low registers (MIDI 28-48)
    for n in bass:
        if n.pitch > 48:
            n.pitch -= 12
        if n.pitch > 48:
            n.pitch -= 12
        if n.pitch < 28:
            n.pitch += 12

    # Pads should stay in the low-mid register (MIDI 36-57)
    for n in pads:
        if n.pitch < 36:
            n.pitch += 12
        elif n.pitch > 57:
            n.pitch -= 12

    # Leads should stay strictly in the mid-high registers (MIDI 64-88)
    for n in leads:
        if n.pitch < 64:
            n.pitch += 12
        if n.pitch < 64:
            n.pitch += 12


# =====================================================================
# Track 1: Grid Theory — 86 BPM — F Minor
# =====================================================================
def produce_grid_theory():
    print("  1. Grid Theory [F Minor — 86 BPM]")
    key = Scale(root=5, mode=Mode.AEOLIAN)  # F Minor
    dur_bars = 32

    parts = [
        IdeaPart(
            name="MainTheme",
            bars=dur_bars,
            scale=key,
            tempo=86,
            progression_type="coupled_hmm"
        )
    ]

    track_list = [
        TrackConfig(
            name="lofi_keys",
            generator=BreakbeatGenerator(variant="think", chop_probability=0.0), # used as a chord rhythm guide
            instrument="piano",
            density=0.6,
            phrase_schedule=structure_to_schedule("A B A B' C C' R R", 4)
        ),
        TrackConfig(
            name="drums",
            generator=BreakbeatGenerator(variant="funky", chop_probability=0.15, ghost_notes=True),
            instrument="drums",
            density=0.7,
            phrase_schedule=structure_to_schedule("R A A B C C' R R", 4)
        ),
        TrackConfig(
            name="synth_bass",
            generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
            instrument="synth_bass",
            density=0.7,
            octave_shift=-1,
            phrase_schedule=structure_to_schedule("A A B B C C' R R", 4)
        ),
        TrackConfig(
            name="dark_pad",
            generator=DarkPadGenerator(mode="minor_pad", register="low", velocity_level=0.30, chord_dur=8.0),
            instrument="dark_pad",
            density=0.6,
            octave_shift=-1,
            phrase_schedule=structure_to_schedule("A B A B C C' A R", 4)
        ),
        TrackConfig(
            name="glockenspiel",
            generator=GlockenspielGenerator(params=GeneratorParams(density=0.35)),
            instrument="glockenspiel",
            density=0.4,
            octave_shift=2,
            phrase_schedule=structure_to_schedule("R R R A C C' R R", 4)
        ),
        TrackConfig(
            name="lead_synth",
            generator=SoloMelodyGenerator(params=GeneratorParams(key_range_low=64, key_range_high=88), style="modal_ambient", vibrato_depth=0.5),
            instrument="synth_lead",
            density=0.6,
            octave_shift=1,
            phrase_schedule=structure_to_schedule("R B R B' C C' R R", 4)
        )
    ]

    tool_config = IdeaToolConfig(
        style="electronic",
        workflow="generate_all",
        use_tension_curve=True,
        use_harmonic_verifier=True,
        use_mixing=True,
        parts=parts,
        tracks=track_list
    )

    notes_dict = IdeaTool(tool_config).generate()
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

    # Dynamic post-processing
    scale_velocity_spread(tracks_data.get("drums", []), 50, 115)
    scale_velocity_spread(tracks_data.get("lead_synth", []), 60, 105)
    scale_velocity_spread(tracks_data.get("glockenspiel", []), 45, 95)
    resolve_register_crossing(tracks_data.get("synth_bass", []), tracks_data.get("dark_pad", []), tracks_data.get("lead_synth", []))

    inst = {
        "lofi_keys": PIANO,
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "glockenspiel": GLOCKENSPIEL,
        "lead_synth": SYNTH_LEAD,
    }

    produce_track(
        tracks=tracks_data,
        bpm=86.0,
        instruments=inst,
        path=OUT / "01_Grid_Theory.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=False,
    )


# =====================================================================
# Track 2: Staggered State — 92 BPM — D Dorian
# =====================================================================
def produce_staggered_state():
    print("  2. Staggered State [D Dorian — 92 BPM]")
    key = Scale(root=2, mode=Mode.DORIAN)  # D Dorian
    dur_bars = 24

    parts = [
        IdeaPart(
            name="MainTheme",
            bars=dur_bars,
            scale=key,
            tempo=92,
            progression_type="coupled_hmm"
        )
    ]

    track_list = [
        TrackConfig(
            name="keys",
            generator=ArpeggiatorGenerator(params=GeneratorParams(density=0.50), pattern="up_down", note_duration=0.5),
            instrument="piano",
            density=0.5,
            phrase_schedule=structure_to_schedule("A B A B C R", 4)
        ),
        TrackConfig(
            name="drums",
            generator=BreakbeatGenerator(variant="think", chop_probability=0.20, ghost_notes=True),
            instrument="drums",
            density=0.7,
            phrase_schedule=structure_to_schedule("R A A B C R", 4)
        ),
        TrackConfig(
            name="synth_bass",
            generator=SynthBassGenerator(waveform="saw", pattern="reese", slide_probability=0.25),
            instrument="synth_bass",
            density=0.7,
            octave_shift=-1,
            phrase_schedule=structure_to_schedule("A A B B C R", 4)
        ),
        TrackConfig(
            name="dark_pad",
            generator=DarkPadGenerator(mode="minor_pad", register="low", velocity_level=0.25, chord_dur=4.0),
            instrument="dark_pad",
            density=0.6,
            octave_shift=-1,
            phrase_schedule=structure_to_schedule("A A A A C R", 4)
        ),
        TrackConfig(
            name="harp",
            generator=HarpGenerator(params=GeneratorParams(density=0.30)),
            instrument="harp",
            density=0.4,
            octave_shift=2,
            phrase_schedule=structure_to_schedule("R R A B C R", 4)
        ),
        TrackConfig(
            name="strings",
            generator=SoloMelodyGenerator(params=GeneratorParams(key_range_low=64, key_range_high=86), style="cinematic_strings", vibrato_depth=0.6),
            instrument="synth_lead",
            density=0.6,
            octave_shift=1,
            phrase_schedule=structure_to_schedule("R B R B C R", 4)
        )
    ]

    tool_config = IdeaToolConfig(
        style="electronic",
        workflow="generate_all",
        use_tension_curve=True,
        use_harmonic_verifier=True,
        use_mixing=True,
        parts=parts,
        tracks=track_list
    )

    notes_dict = IdeaTool(tool_config).generate()
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

    # Dynamic post-processing
    scale_velocity_spread(tracks_data.get("drums", []), 50, 115)
    scale_velocity_spread(tracks_data.get("keys", []), 55, 100)
    scale_velocity_spread(tracks_data.get("strings", []), 60, 105)
    scale_velocity_spread(tracks_data.get("harp", []), 45, 95)
    resolve_register_crossing(tracks_data.get("synth_bass", []), tracks_data.get("dark_pad", []), tracks_data.get("strings", []))

    inst = {
        "keys": PIANO,
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "harp": HARP,
        "strings": SYNTH_LEAD,
    }

    produce_track(
        tracks=tracks_data,
        bpm=92.0,
        instruments=inst,
        path=OUT / "02_Staggered_State.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=False,
    )


# =====================================================================
# Track 3: Climax Protocol — 80 BPM — G Minor
# =====================================================================
def produce_climax_protocol():
    print("  3. Climax Protocol [G Minor — 80 BPM]")
    key = Scale(root=7, mode=Mode.NATURAL_MINOR)  # G Minor
    dur_bars = 32

    parts = [
        IdeaPart(
            name="MainTheme",
            bars=dur_bars,
            scale=key,
            tempo=80,
            progression_type="coupled_hmm"
        )
    ]

    track_list = [
        TrackConfig(
            name="keys",
            generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.30, chord_dur=4.0),
            instrument="piano",
            density=0.6,
            phrase_schedule=structure_to_schedule("A B A B C C' A R", 4)
        ),
        TrackConfig(
            name="drums",
            generator=BreakbeatGenerator(variant="idm", chop_probability=0.30, ghost_notes=True),
            instrument="drums",
            density=0.7,
            phrase_schedule=structure_to_schedule("R R A B C C' R R", 4)
        ),
        TrackConfig(
            name="synth_bass",
            generator=SynthBassGenerator(waveform="sine", pattern="plucked"),
            instrument="synth_bass",
            density=0.7,
            octave_shift=-1,
            phrase_schedule=structure_to_schedule("R A A B C C' R R", 4)
        ),
        TrackConfig(
            name="dark_pad",
            generator=DarkPadGenerator(mode="minor_pad", register="low", velocity_level=0.35, chord_dur=8.0),
            instrument="dark_pad",
            density=0.6,
            octave_shift=-1,
            phrase_schedule=structure_to_schedule("A B A B C C' A R", 4)
        ),
        TrackConfig(
            name="harp",
            generator=HarpGenerator(params=GeneratorParams(density=0.30)),
            instrument="harp",
            density=0.4,
            octave_shift=2,
            phrase_schedule=structure_to_schedule("A R A R C C' R R", 4)
        ),
        TrackConfig(
            name="melody",
            generator=SoloMelodyGenerator(params=GeneratorParams(key_range_low=64, key_range_high=88), style="space_synth", vibrato_depth=0.5),
            instrument="synth_lead",
            density=0.6,
            octave_shift=1,
            phrase_schedule=structure_to_schedule("R B R B' C C' R R", 4)
        )
    ]

    tool_config = IdeaToolConfig(
        style="electronic",
        workflow="generate_all",
        use_tension_curve=True,
        use_harmonic_verifier=True,
        use_mixing=True,
        parts=parts,
        tracks=track_list
    )

    notes_dict = IdeaTool(tool_config).generate()
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

    # Dynamic post-processing
    scale_velocity_spread(tracks_data.get("drums", []), 50, 115)
    scale_velocity_spread(tracks_data.get("melody", []), 60, 105)
    scale_velocity_spread(tracks_data.get("harp", []), 45, 95)
    resolve_register_crossing(tracks_data.get("synth_bass", []), tracks_data.get("dark_pad", []), tracks_data.get("melody", []))

    inst = {
        "keys": PIANO,
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "harp": HARP,
        "melody": SYNTH_LEAD,
    }

    produce_track(
        tracks=tracks_data,
        bpm=80.0,
        instruments=inst,
        path=OUT / "03_Climax_Protocol.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=False,
    )


def generate_album():
    print("\n" + "=" * 80)
    print("        P A T T E R N S   O F   T I M E")
    print("        Structured Electronic & Breakbeat Album")
    print("=" * 80)

    produce_grid_theory()
    produce_staggered_state()
    produce_climax_protocol()

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: PATTERNS OF TIME")
    print(f"  Output folder: {OUT.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    generate_album()
