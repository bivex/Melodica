# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/electronic/album_melodic_downtempo.py — "Pulse & Atmosphere" Melodic Downtempo Album.

An album combining melodic elements, slow down-tempo breakbeats, drum-driven pacing,
atmospheric textures, deep sub-basslines, evolving synth pads, minimal percussion,
emotional progressions, and cinematic breaks.

Fully structured using the Melodica IdeaTool and IdeaPart framework for dynamic chord progressions
and section-based orchestration.
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
from melodica.generators.tension import TensionGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
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

random.seed(2026)
OUT = Path("output/album_melodic_downtempo")
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
    # Bass should stay strictly in the low registers
    for n in bass:
        if n.pitch > 48:
            n.pitch -= 12
        if n.pitch > 48:
            n.pitch -= 12

    # Pads should stay in the low-mid register
    for n in pads:
        if n.pitch < 36:
            n.pitch += 12
        elif n.pitch > 60:
            n.pitch -= 12

    # Leads should stay strictly in the mid-high registers
    for n in leads:
        if n.pitch < 64:
            n.pitch += 12
        if n.pitch < 64:
            n.pitch += 12


# =====================================================================
# Track 1: Velvet Echoes — 88 BPM — C Minor
# =====================================================================
def produce_velvet_echoes():
    print("  1. Velvet Echoes [C Minor — 88 BPM]")
    key = Scale(root=0, mode=Mode.AEOLIAN)  # C Aeolian

    # Section-based structural parts (IdeaParts)
    parts = [
        IdeaPart(
            name="Intro",
            bars=4,
            scale=key,
            tempo=88,
            progression_type="coupled_hmm",
            track_mute=["drums", "tension_fx", "lead_synth", "fx_riser"]
        ),
        IdeaPart(
            name="Main",
            bars=16,
            scale=key,
            tempo=88,
            progression_type="coupled_hmm"
        ),
        IdeaPart(
            name="Outro",
            bars=4,
            scale=key,
            tempo=88,
            progression_type="coupled_hmm",
            track_mute=["drums", "tension_fx", "lead_synth", "fx_riser"]
        )
    ]

    track_list = [
        TrackConfig(
            name="drums",
            generator=BreakbeatGenerator(variant="funky", chop_probability=0.15, ghost_notes=True),
            instrument="drums",
            density=0.7
        ),
        TrackConfig(
            name="synth_bass",
            generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
            instrument="synth_bass",
            density=0.7,
            octave_shift=-1
        ),
        TrackConfig(
            name="dark_pad",
            generator=DarkPadGenerator(mode="minor_pad", register="low", velocity_level=0.30, chord_dur=8.0),
            instrument="dark_pad",
            density=0.6,
            octave_shift=-1
        ),
        TrackConfig(
            name="glockenspiel",
            generator=GlockenspielGenerator(params=GeneratorParams(density=0.35)),
            instrument="glockenspiel",
            density=0.4,
            octave_shift=2
        ),
        TrackConfig(
            name="tension_fx",
            generator=TensionGenerator(mode="major7_tension", note_duration=4.0, velocity_level=0.25, register="high", density=0.4),
            instrument="synth_lead",
            density=0.4,
            octave_shift=1
        ),
        TrackConfig(
            name="lead_synth",
            generator=SoloMelodyGenerator(params=GeneratorParams(key_range_low=64, key_range_high=88), style="modal_ambient", vibrato_depth=0.5),
            instrument="synth_lead",
            density=0.6,
            octave_shift=1
        ),
        TrackConfig(
            name="fx_riser",
            generator=FXRiserGenerator(params=GeneratorParams(density=0.40), riser_type="synth", length_beats=8.0, pitch_curve="exponential", peak_velocity=90),
            instrument="synth_fx",
            density=0.4
        ),
        TrackConfig(
            name="fx_impact",
            generator=FXImpactGenerator(params=GeneratorParams(density=0.25), impact_type="boom", tail_length=8.0, pitch_drop=12),
            instrument="synth_fx",
            density=0.3
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

    # Apply dynamic fixes & register separation
    scale_velocity_spread(tracks_data.get("drums", []), 50, 110)
    scale_velocity_spread(tracks_data.get("lead_synth", []), 60, 100)
    scale_velocity_spread(tracks_data.get("glockenspiel", []), 45, 95)
    resolve_register_crossing(tracks_data.get("synth_bass", []), tracks_data.get("dark_pad", []), tracks_data.get("lead_synth", []))

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "glockenspiel": GLOCKENSPIEL,
        "tension_fx": POLYSYNTH,
        "lead_synth": SYNTH_LEAD,
        "fx_riser": EFFECTS,
        "fx_impact": EFFECTS,
    }

    produce_track(
        tracks=tracks_data,
        bpm=88.0,
        instruments=inst,
        path=OUT / "01_Velvet_Echoes.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=False,
        sections=[(0.0, Mood.CINEMATIC), (16.0, Mood.CINEMATIC), (80.0, Mood.CINEMATIC)],
    )


# =====================================================================
# Track 2: Lost in the Static — 94 BPM — F# Dorian
# =====================================================================
def produce_lost_in_the_static():
    print("  2. Lost in the Static [F# Dorian — 94 BPM]")
    key = Scale(root=6, mode=Mode.DORIAN)  # F# Dorian

    parts = [
        IdeaPart(
            name="Intro",
            bars=4,
            scale=key,
            tempo=94,
            progression_type="coupled_hmm",
            track_mute=["drums", "harp_shimmer", "lead_strings", "arpeggio", "fx_riser"]
        ),
        IdeaPart(
            name="Main",
            bars=16,
            scale=key,
            tempo=94,
            progression_type="coupled_hmm"
        ),
        IdeaPart(
            name="Outro",
            bars=4,
            scale=key,
            tempo=94,
            progression_type="coupled_hmm",
            track_mute=["drums", "harp_shimmer", "lead_strings", "arpeggio", "fx_riser"]
        )
    ]

    track_list = [
        TrackConfig(
            name="drums",
            generator=BreakbeatGenerator(variant="think", chop_probability=0.20, ghost_notes=True),
            instrument="drums",
            density=0.7
        ),
        TrackConfig(
            name="synth_bass",
            generator=SynthBassGenerator(waveform="saw", pattern="reese", slide_probability=0.25, octave_variation=0.1),
            instrument="synth_bass",
            density=0.7,
            octave_shift=-1
        ),
        TrackConfig(
            name="dark_pad",
            generator=DarkPadGenerator(mode="phrygian_pad", register="low", velocity_level=0.25, chord_dur=4.0),
            instrument="dark_pad",
            density=0.6,
            octave_shift=-1
        ),
        TrackConfig(
            name="scifi_texture",
            generator=SciFiUnderscoreGenerator(variant="blade_runner", pad_density=0.5, arp_speed=0.5, include_bass_synth=False),
            instrument="synth_lead",
            density=0.5
        ),
        TrackConfig(
            name="harp_shimmer",
            generator=HarpGenerator(params=GeneratorParams(density=0.30)),
            instrument="harp",
            density=0.4,
            octave_shift=2
        ),
        TrackConfig(
            name="lead_strings",
            generator=SoloMelodyGenerator(params=GeneratorParams(key_range_low=64, key_range_high=86), style="cinematic_strings", vibrato_depth=0.6),
            instrument="synth_lead",
            density=0.6,
            octave_shift=1
        ),
        TrackConfig(
            name="arpeggio",
            generator=ArpeggiatorGenerator(params=GeneratorParams(density=0.50), pattern="up_down", note_duration=0.5),
            instrument="synth_lead",
            density=0.5,
            octave_shift=1
        ),
        TrackConfig(
            name="fx_riser",
            generator=FXRiserGenerator(params=GeneratorParams(density=0.35), riser_type="synth", length_beats=4.0, pitch_curve="linear", peak_velocity=85),
            instrument="synth_fx",
            density=0.4
        ),
        TrackConfig(
            name="fx_impact",
            generator=FXImpactGenerator(params=GeneratorParams(density=0.20), impact_type="boom", tail_length=6.0, pitch_drop=15),
            instrument="synth_fx",
            density=0.3
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

    # Apply dynamic fixes & register separation
    scale_velocity_spread(tracks_data.get("drums", []), 50, 110)
    scale_velocity_spread(tracks_data.get("arpeggio", []), 55, 100)
    scale_velocity_spread(tracks_data.get("lead_strings", []), 60, 105)
    scale_velocity_spread(tracks_data.get("harp_shimmer", []), 45, 95)
    resolve_register_crossing(tracks_data.get("synth_bass", []), tracks_data.get("dark_pad", []), tracks_data.get("lead_strings", []))

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "scifi_texture": POLYSYNTH,
        "harp_shimmer": HARP,
        "lead_strings": SYNTH_LEAD,
        "arpeggio": POLYSYNTH,
        "fx_riser": EFFECTS,
        "fx_impact": EFFECTS,
    }

    produce_track(
        tracks=tracks_data,
        bpm=94.0,
        instruments=inst,
        path=OUT / "02_Lost_in_the_Static.mid",
        mood=Mood.INTIMATE,
        key=key,
        verbose=False,
        sections=[(0.0, Mood.INTIMATE), (16.0, Mood.INTIMATE), (80.0, Mood.INTIMATE)],
    )


# =====================================================================
# Track 3: Cinematic Drift — 82 BPM — G Minor
# =====================================================================
def produce_cinematic_drift():
    print("  3. Cinematic Drift [G Minor — 82 BPM]")
    key = Scale(root=7, mode=Mode.AEOLIAN)  # G Aeolian

    parts = [
        IdeaPart(
            name="Intro",
            bars=8,
            scale=key,
            tempo=82,
            progression_type="coupled_hmm",
            track_mute=["drums", "tension_rub", "glock_shimmer", "lead_synth", "fx_riser"]
        ),
        IdeaPart(
            name="Main",
            bars=16,
            scale=key,
            tempo=82,
            progression_type="coupled_hmm"
        ),
        IdeaPart(
            name="Outro",
            bars=8,
            scale=key,
            tempo=82,
            progression_type="coupled_hmm",
            track_mute=["drums", "tension_rub", "glock_shimmer", "lead_synth", "fx_riser"]
        )
    ]

    track_list = [
        TrackConfig(
            name="drums",
            generator=BreakbeatGenerator(variant="idm", chop_probability=0.30, ghost_notes=True),
            instrument="drums",
            density=0.7
        ),
        TrackConfig(
            name="synth_bass",
            generator=SynthBassGenerator(waveform="sine", pattern="plucked"),
            instrument="synth_bass",
            density=0.7,
            octave_shift=-1
        ),
        TrackConfig(
            name="dark_pad",
            generator=DarkPadGenerator(mode="minor_pad", register="low", velocity_level=0.35, chord_dur=8.0),
            instrument="dark_pad",
            density=0.6,
            octave_shift=-1
        ),
        TrackConfig(
            name="tension_rub",
            generator=TensionGenerator(mode="semitone_cluster", note_duration=2.0, velocity_level=0.35, register="mid", density=0.5),
            instrument="synth_lead",
            density=0.5
        ),
        TrackConfig(
            name="scifi_drone",
            generator=SciFiUnderscoreGenerator(variant="space", pad_density=0.6, include_bass_synth=False),
            instrument="synth_lead",
            density=0.6
        ),
        TrackConfig(
            name="glock_shimmer",
            generator=GlockenspielGenerator(params=GeneratorParams(density=0.30)),
            instrument="glockenspiel",
            density=0.3,
            octave_shift=2
        ),
        TrackConfig(
            name="lead_synth",
            generator=SoloMelodyGenerator(params=GeneratorParams(key_range_low=64, key_range_high=88), style="space_synth", vibrato_depth=0.5),
            instrument="synth_lead",
            density=0.6,
            octave_shift=1
        ),
        TrackConfig(
            name="fx_riser",
            generator=FXRiserGenerator(params=GeneratorParams(density=0.45), riser_type="synth", length_beats=12.0, pitch_curve="exponential", peak_velocity=95),
            instrument="synth_fx",
            density=0.4
        ),
        TrackConfig(
            name="fx_impact",
            generator=FXImpactGenerator(params=GeneratorParams(density=0.30), impact_type="boom", tail_length=10.0, pitch_drop=18),
            instrument="synth_fx",
            density=0.3
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

    # Apply dynamic fixes & register separation
    scale_velocity_spread(tracks_data.get("drums", []), 50, 110)
    scale_velocity_spread(tracks_data.get("lead_synth", []), 60, 105)
    scale_velocity_spread(tracks_data.get("glock_shimmer", []), 45, 95)
    resolve_register_crossing(tracks_data.get("synth_bass", []), tracks_data.get("dark_pad", []), tracks_data.get("lead_synth", []))

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "tension_rub": POLYSYNTH,
        "scifi_drone": POLYSYNTH,
        "glock_shimmer": GLOCKENSPIEL,
        "lead_synth": SYNTH_LEAD,
        "fx_riser": EFFECTS,
        "fx_impact": EFFECTS,
    }

    produce_track(
        tracks=tracks_data,
        bpm=82.0,
        instruments=inst,
        path=OUT / "03_Cinematic_Drift.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=False,
        sections=[(0.0, Mood.CINEMATIC), (32.0, Mood.CINEMATIC), (96.0, Mood.CINEMATIC)],
    )


def generate_album():
    print("\n" + "=" * 80)
    print("        P U L S E   &   A T M O S P H E R E")
    print("        Melodic Downtempo & Atmospheric Breakbeat Album")
    print("=" * 80)

    produce_velvet_echoes()
    produce_lost_in_the_static()
    produce_cinematic_drift()

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: PULSE & ATMOSPHERE")
    print(f"  Output folder: {OUT.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    generate_album()
