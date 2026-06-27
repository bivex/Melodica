# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/electronic/album_imperative.py — "The Command Protocol" Album.

A conceptual, melodic downtempo album featuring organic drum-driven rhythms, deep
atmospheric textures, and emotional cinematic progression. Integrated with powerful
call-to-action lyrics in the imperative mood.

Fully refactored using the Melodica IdeaTool and IdeaPart framework for dynamic chord
progressions and clean section mutes.
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
from melodica.generators.vocal_melody_auto import VocalMelodyAutoGenerator
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

random.seed(4242)
OUT = Path("output/album_imperative")
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# Diagnostic & Post-processing Helpers
# ------------------------------------------------------------------
def scale_velocity_spread(notes: list[NoteInfo], target_min=50, target_max=115) -> list[NoteInfo]:
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
# Track 1: Command (Awaken) — 84 BPM — D Minor
# =====================================================================
def produce_command_awaken():
    print("  1. Command (Awaken) [D Minor — 84 BPM]")
    key = Scale(root=2, mode=Mode.AEOLIAN)  # D Minor

    # Dynamic parts
    parts = [
        IdeaPart(
            name="Intro",
            bars=4,
            scale=key,
            tempo=84,
            progression_type="coupled_hmm",
            track_mute=["drums", "vocal_guide", "lead_synth", "fx_riser"]
        ),
        IdeaPart(
            name="Main",
            bars=16,
            scale=key,
            tempo=84,
            progression_type="coupled_hmm"
        ),
        IdeaPart(
            name="Outro",
            bars=4,
            scale=key,
            tempo=84,
            progression_type="coupled_hmm",
            track_mute=["drums", "vocal_guide", "lead_synth", "fx_riser"]
        )
    ]

    track_list = [
        TrackConfig(
            name="drums",
            generator=BreakbeatGenerator(variant="funky", chop_probability=0.20, ghost_notes=True),
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
            generator=GlockenspielGenerator(params=GeneratorParams(density=0.30)),
            instrument="glockenspiel",
            density=0.4,
            octave_shift=2
        ),
        TrackConfig(
            name="vocal_guide",
            generator=VocalMelodyAutoGenerator(params=GeneratorParams(density=0.55), variant="travis", register="mid", sustain_preference=0.7, octave_jump_probability=0.3),
            instrument="synth_lead",
            density=0.6,
            octave_shift=1
        ),
        TrackConfig(
            name="lead_synth",
            generator=SoloMelodyGenerator(params=GeneratorParams(key_range_low=60, key_range_high=84), style="modal_ambient", vibrato_depth=0.5),
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
            generator=FXImpactGenerator(params=GeneratorParams(density=0.25), impact_type="boom", tail_length=8.0),
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

    # Apply processing
    scale_velocity_spread(tracks_data.get("drums", []), 50, 115)
    scale_velocity_spread(tracks_data.get("vocal_guide", []), 60, 110)
    scale_velocity_spread(tracks_data.get("lead_synth", []), 55, 105)
    resolve_register_crossing(tracks_data.get("synth_bass", []), tracks_data.get("dark_pad", []), tracks_data.get("vocal_guide", []))

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "glockenspiel": GLOCKENSPIEL,
        "vocal_guide": SYNTH_LEAD,
        "lead_synth": POLYSYNTH,
        "fx_riser": EFFECTS,
        "fx_impact": EFFECTS,
    }

    produce_track(
        tracks=tracks_data,
        bpm=84.0,
        instruments=inst,
        path=OUT / "01_Command_Awaken.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=False,
        sections=[(0.0, Mood.CINEMATIC), (16.0, Mood.CINEMATIC), (80.0, Mood.CINEMATIC)],
    )


# =====================================================================
# Track 2: Protocol (Reclaim) — 90 BPM — A Phrygian
# =====================================================================
def produce_protocol_reclaim():
    print("  2. Protocol (Reclaim) [A Phrygian — 90 BPM]")
    key = Scale(root=9, mode=Mode.PHRYGIAN)  # A Phrygian

    parts = [
        IdeaPart(
            name="Intro",
            bars=4,
            scale=key,
            tempo=90,
            progression_type="coupled_hmm",
            track_mute=["drums", "vocal_guide", "arpeggio", "fx_riser"]
        ),
        IdeaPart(
            name="Main",
            bars=16,
            scale=key,
            tempo=90,
            progression_type="coupled_hmm"
        ),
        IdeaPart(
            name="Outro",
            bars=4,
            scale=key,
            tempo=90,
            progression_type="coupled_hmm",
            track_mute=["drums", "vocal_guide", "arpeggio", "fx_riser"]
        )
    ]

    track_list = [
        TrackConfig(
            name="drums",
            generator=BreakbeatGenerator(variant="think", chop_probability=0.25, ghost_notes=True),
            instrument="drums",
            density=0.7
        ),
        TrackConfig(
            name="synth_bass",
            generator=SynthBassGenerator(waveform="saw", pattern="reese", slide_probability=0.30, octave_variation=0.1),
            instrument="synth_bass",
            density=0.7,
            octave_shift=-1
        ),
        TrackConfig(
            name="dark_pad",
            generator=DarkPadGenerator(mode="phrygian_pad", register="low", velocity_level=0.30, chord_dur=4.0),
            instrument="dark_pad",
            density=0.6,
            octave_shift=-1
        ),
        TrackConfig(
            name="scifi_texture",
            generator=SciFiUnderscoreGenerator(variant="cyberpunk", pad_density=0.5, arp_speed=0.5, include_bass_synth=False),
            instrument="synth_lead",
            density=0.5
        ),
        TrackConfig(
            name="harp_shimmer",
            generator=HarpGenerator(params=GeneratorParams(density=0.35)),
            instrument="harp",
            density=0.4,
            octave_shift=2
        ),
        TrackConfig(
            name="vocal_guide",
            generator=VocalMelodyAutoGenerator(params=GeneratorParams(density=0.60), variant="future", register="high", sustain_preference=0.8, octave_jump_probability=0.4),
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
            generator=FXRiserGenerator(params=GeneratorParams(density=0.40), riser_type="synth", length_beats=4.0, pitch_curve="linear", peak_velocity=85),
            instrument="synth_fx",
            density=0.4
        ),
        TrackConfig(
            name="fx_impact",
            generator=FXImpactGenerator(params=GeneratorParams(density=0.20), impact_type="boom", tail_length=6.0),
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

    # Processing
    scale_velocity_spread(tracks_data.get("drums", []), 50, 115)
    scale_velocity_spread(tracks_data.get("vocal_guide", []), 60, 110)
    scale_velocity_spread(tracks_data.get("arpeggio", []), 55, 100)
    resolve_register_crossing(tracks_data.get("synth_bass", []), tracks_data.get("dark_pad", []), tracks_data.get("vocal_guide", []))

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "scifi_texture": POLYSYNTH,
        "harp_shimmer": HARP,
        "vocal_guide": SYNTH_LEAD,
        "arpeggio": POLYSYNTH,
        "fx_riser": EFFECTS,
        "fx_impact": EFFECTS,
    }

    produce_track(
        tracks=tracks_data,
        bpm=90.0,
        instruments=inst,
        path=OUT / "02_Protocol_Reclaim.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=False,
        sections=[(0.0, Mood.CINEMATIC), (16.0, Mood.CINEMATIC), (80.0, Mood.CINEMATIC)],
    )


# =====================================================================
# Track 3: Horizon (Release) — 76 BPM — G Lydian
# =====================================================================
def produce_horizon_release():
    print("  3. Horizon (Release) [G Lydian — 76 BPM]")
    key = Scale(root=7, mode=Mode.LYDIAN)  # G Lydian

    parts = [
        IdeaPart(
            name="Intro",
            bars=8,
            scale=key,
            tempo=76,
            progression_type="coupled_hmm",
            track_mute=["drums", "tension_rub", "glock_shimmer", "vocal_guide", "fx_riser"]
        ),
        IdeaPart(
            name="Main",
            bars=16,
            scale=key,
            tempo=76,
            progression_type="coupled_hmm"
        ),
        IdeaPart(
            name="Outro",
            bars=8,
            scale=key,
            tempo=76,
            progression_type="coupled_hmm",
            track_mute=["drums", "tension_rub", "glock_shimmer", "vocal_guide", "fx_riser"]
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
            name="vocal_guide",
            generator=VocalMelodyAutoGenerator(params=GeneratorParams(density=0.55), variant="don_toliver", register="mid", sustain_preference=0.8, octave_jump_probability=0.3),
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
            generator=FXImpactGenerator(params=GeneratorParams(density=0.30), impact_type="boom", tail_length=10.0),
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

    # Processing
    scale_velocity_spread(tracks_data.get("drums", []), 50, 115)
    scale_velocity_spread(tracks_data.get("vocal_guide", []), 60, 110)
    scale_velocity_spread(tracks_data.get("glock_shimmer", []), 45, 95)
    resolve_register_crossing(tracks_data.get("synth_bass", []), tracks_data.get("dark_pad", []), tracks_data.get("vocal_guide", []))

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "tension_rub": POLYSYNTH,
        "scifi_drone": POLYSYNTH,
        "glock_shimmer": GLOCKENSPIEL,
        "vocal_guide": SYNTH_LEAD,
        "fx_riser": EFFECTS,
        "fx_impact": EFFECTS,
    }

    produce_track(
        tracks=tracks_data,
        bpm=76.0,
        instruments=inst,
        path=OUT / "03_Horizon_Release.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=False,
        sections=[(0.0, Mood.CINEMATIC), (32.0, Mood.CINEMATIC), (96.0, Mood.CINEMATIC)],
    )


def generate_album():
    print("\n" + "=" * 80)
    print("        T H E   C O M M A N D   P R O T O C O L")
    print("        Unique Conceptual Lyrical Downtempo Album")
    print("=" * 80)

    produce_command_awaken()
    produce_protocol_reclaim()
    produce_horizon_release()

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: THE COMMAND PROTOCOL")
    print(f"  Output folder: {OUT.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    generate_album()
