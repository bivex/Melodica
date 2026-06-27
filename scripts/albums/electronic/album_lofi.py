# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/electronic/album_lofi.py — "Tape Dust" Cozy Lo-Fi Analog Album.

A cozy, warm, and nostalgic lo-fi analog album featuring soft drum grooves, mellow basslines,
dusty vinyl textures, smooth melodic progressions, organic imperfections, and humanized timing.

Built using the Melodica IdeaTool, TrackConfig, and IdeaPart frameworks.
"""

import random
import sys
from pathlib import Path

from melodica.types import Scale, Mode, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.lofi_hiphop import LoFiHipHopGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.generators.breakbeat import BreakbeatGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.modifiers import HumanizeModifier, VelocityScalingModifier

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

random.seed(1995)
OUT = Path("output/album_lofi")
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# Diagnostic & Post-processing Helpers
# ------------------------------------------------------------------
def scale_velocity_spread(notes: list[NoteInfo], target_min=45, target_max=85) -> list[NoteInfo]:
    """Clamp velocities to a lower, gentler range to avoid harsh transients/peaks."""
    if not notes:
        return notes
    vels = [n.velocity for n in notes]
    min_v, max_v = min(vels), max(vels)
    if max_v == min_v:
        for n in notes:
            n.velocity = target_min
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

    # Pads should stay in the low-mid register (MIDI 36-57)
    for n in pads:
        if n.pitch < 36:
            n.pitch += 12
        elif n.pitch > 57:
            n.pitch -= 12

    # Leads should stay strictly in the mid-high registers (MIDI 64-84)
    for n in leads:
        if n.pitch < 64:
            n.pitch += 12
        if n.pitch < 64:
            n.pitch += 12


# =====================================================================
# Track 1: Morning Coffee — 74 BPM — Eb Major
# =====================================================================
def produce_morning_coffee():
    print("  1. Morning Coffee [Eb Major — 74 BPM]")
    key = Scale(root=3, mode=Mode.MAJOR)  # Eb Major

    parts = [
        IdeaPart(
            name="Intro",
            bars=4,
            scale=key,
            tempo=74,
            progression_type="coupled_hmm",
            track_mute=["soft_drums", "harp_shimmer", "solo_melody"]
        ),
        IdeaPart(
            name="Main",
            bars=16,
            scale=key,
            tempo=74,
            progression_type="coupled_hmm"
        ),
        IdeaPart(
            name="Outro",
            bars=4,
            scale=key,
            tempo=74,
            progression_type="coupled_hmm",
            track_mute=["soft_drums", "harp_shimmer", "solo_melody"]
        )
    ]

    track_list = [
        TrackConfig(
            name="lofi_keys",
            generator=LoFiHipHopGenerator(variant="chill", chord_voicing="ninth", include_bass=False, include_drums=False),
            instrument="piano",
            density=0.6,
            modifiers=[
                HumanizeModifier(timing_std=0.018, velocity_std=4),
                VelocityScalingModifier(scale=0.65)
            ]
        ),
        TrackConfig(
            name="mellow_bass",
            generator=SynthBassGenerator(waveform="sine", pattern="plucked"),
            instrument="synth_bass",
            density=0.6,
            octave_shift=-1,
            modifiers=[
                HumanizeModifier(timing_std=0.015, velocity_std=3),
                VelocityScalingModifier(scale=0.70)
            ]
        ),
        TrackConfig(
            name="soft_drums",
            generator=BreakbeatGenerator(variant="funky", chop_probability=0.05, ghost_notes=True),
            instrument="drums",
            density=0.6,
            modifiers=[
                HumanizeModifier(timing_std=0.022, velocity_std=5),
                VelocityScalingModifier(scale=0.70)
            ]
        ),
        TrackConfig(
            name="ambient_pad",
            generator=DarkPadGenerator(mode="minor_pad", register="low", velocity_level=0.25, chord_dur=8.0),
            instrument="dark_pad",
            density=0.5,
            octave_shift=-1,
            modifiers=[
                VelocityScalingModifier(scale=0.60)
            ]
        ),
        TrackConfig(
            name="harp_shimmer",
            generator=HarpGenerator(params=GeneratorParams(density=0.25)),
            instrument="harp",
            density=0.4,
            octave_shift=2,
            modifiers=[
                HumanizeModifier(timing_std=0.020, velocity_std=3),
                VelocityScalingModifier(scale=0.60)
            ]
        ),
        TrackConfig(
            name="solo_melody",
            generator=SoloMelodyGenerator(params=GeneratorParams(key_range_low=60, key_range_high=80), style="modal_ambient", vibrato_depth=0.3),
            instrument="synth_lead",
            density=0.5,
            octave_shift=1,
            modifiers=[
                HumanizeModifier(timing_std=0.018, velocity_std=4),
                VelocityScalingModifier(scale=0.65)
            ]
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

    # Soft dynamic mapping & separation
    scale_velocity_spread(tracks_data.get("soft_drums", []), 45, 80)
    scale_velocity_spread(tracks_data.get("lofi_keys", []), 40, 75)
    scale_velocity_spread(tracks_data.get("solo_melody", []), 45, 80)
    resolve_register_crossing(tracks_data.get("mellow_bass", []), tracks_data.get("ambient_pad", []), tracks_data.get("solo_melody", []))

    inst = {
        "lofi_keys": PIANO,
        "mellow_bass": SYNTH_BASS,
        "soft_drums": DRUMS,
        "ambient_pad": DARK_PAD,
        "harp_shimmer": HARP,
        "solo_melody": SYNTH_LEAD,
    }

    produce_track(
        tracks=tracks_data,
        bpm=74.0,
        instruments=inst,
        path=OUT / "01_Morning_Coffee.mid",
        mood=Mood.INTIMATE,
        key=key,
        verbose=False,
        sections=[(0.0, "Intro"), (16.0, "Theme"), (32.0, "Variation"), (64.0, "Climax"), (96.0, "Breakdown"), (112.0, "Fade")],
    )


# =====================================================================
# Track 2: Rainy Window — 78 BPM — G Minor
# =====================================================================
def produce_rainy_window():
    print("  2. Rainy Window [G Minor — 78 BPM]")
    key = Scale(root=7, mode=Mode.NATURAL_MINOR)  # G Minor

    parts = [
        IdeaPart(
            name="Intro",
            bars=4,
            scale=key,
            tempo=78,
            progression_type="coupled_hmm",
            track_mute=["soft_drums", "glock_shimmer", "solo_melody"]
        ),
        IdeaPart(
            name="Main",
            bars=16,
            scale=key,
            tempo=78,
            progression_type="coupled_hmm"
        ),
        IdeaPart(
            name="Outro",
            bars=4,
            scale=key,
            tempo=78,
            progression_type="coupled_hmm",
            track_mute=["soft_drums", "glock_shimmer", "solo_melody"]
        )
    ]

    track_list = [
        TrackConfig(
            name="lofi_keys",
            generator=LoFiHipHopGenerator(variant="jazzy", chord_voicing="eleventh", include_bass=False, include_drums=False),
            instrument="piano",
            density=0.6,
            modifiers=[
                HumanizeModifier(timing_std=0.020, velocity_std=4),
                VelocityScalingModifier(scale=0.65)
            ]
        ),
        TrackConfig(
            name="mellow_bass",
            generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
            instrument="synth_bass",
            density=0.6,
            octave_shift=-1,
            modifiers=[
                HumanizeModifier(timing_std=0.015, velocity_std=3),
                VelocityScalingModifier(scale=0.70)
            ]
        ),
        TrackConfig(
            name="soft_drums",
            generator=ElectronicDrumsGenerator(kit="808", pattern="minimal", groove_swing=0.60),
            instrument="drums",
            density=0.6,
            modifiers=[
                HumanizeModifier(timing_std=0.024, velocity_std=5),
                VelocityScalingModifier(scale=0.65)
            ]
        ),
        TrackConfig(
            name="scifi_texture",
            generator=SciFiUnderscoreGenerator(variant="blade_runner", pad_density=0.4, include_bass_synth=False),
            instrument="dark_pad",
            density=0.5,
            modifiers=[
                VelocityScalingModifier(scale=0.60)
            ]
        ),
        TrackConfig(
            name="glock_shimmer",
            generator=GlockenspielGenerator(params=GeneratorParams(density=0.20)),
            instrument="glockenspiel",
            density=0.3,
            octave_shift=2,
            modifiers=[
                HumanizeModifier(timing_std=0.022, velocity_std=3),
                VelocityScalingModifier(scale=0.55)
            ]
        ),
        TrackConfig(
            name="solo_melody",
            generator=SoloMelodyGenerator(params=GeneratorParams(key_range_low=62, key_range_high=82), style="modal_ambient", vibrato_depth=0.35),
            instrument="synth_lead",
            density=0.5,
            octave_shift=1,
            modifiers=[
                HumanizeModifier(timing_std=0.018, velocity_std=4),
                VelocityScalingModifier(scale=0.65)
            ]
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

    # Soft dynamic mapping & separation
    scale_velocity_spread(tracks_data.get("soft_drums", []), 45, 80)
    scale_velocity_spread(tracks_data.get("lofi_keys", []), 40, 75)
    scale_velocity_spread(tracks_data.get("solo_melody", []), 45, 80)
    resolve_register_crossing(tracks_data.get("mellow_bass", []), tracks_data.get("scifi_texture", []), tracks_data.get("solo_melody", []))

    inst = {
        "lofi_keys": PIANO,
        "mellow_bass": SYNTH_BASS,
        "soft_drums": DRUMS,
        "scifi_texture": DARK_PAD,
        "glock_shimmer": GLOCKENSPIEL,
        "solo_melody": SYNTH_LEAD,
    }

    produce_track(
        tracks=tracks_data,
        bpm=78.0,
        instruments=inst,
        path=OUT / "02_Rainy_Window.mid",
        mood=Mood.INTIMATE,
        key=key,
        verbose=False,
        sections=[(0.0, "Intro"), (16.0, "Theme"), (32.0, "Variation"), (64.0, "Climax"), (96.0, "Breakdown"), (112.0, "Fade")],
    )


# =====================================================================
# Track 3: Midnight Vinyl — 70 BPM — C Major
# =====================================================================
def produce_midnight_vinyl():
    print("  3. Midnight Vinyl [C Major — 70 BPM]")
    key = Scale(root=0, mode=Mode.MAJOR)  # C Major

    parts = [
        IdeaPart(
            name="Intro",
            bars=8,
            scale=key,
            tempo=70,
            progression_type="coupled_hmm",
            track_mute=["soft_drums", "harp_shimmer", "solo_melody"]
        ),
        IdeaPart(
            name="Main",
            bars=16,
            scale=key,
            tempo=70,
            progression_type="coupled_hmm"
        ),
        IdeaPart(
            name="Outro",
            bars=8,
            scale=key,
            tempo=70,
            progression_type="coupled_hmm",
            track_mute=["soft_drums", "harp_shimmer", "solo_melody"]
        )
    ]

    track_list = [
        TrackConfig(
            name="lofi_keys",
            generator=LoFiHipHopGenerator(variant="chill", chord_voicing="ninth", include_bass=False, include_drums=False),
            instrument="piano",
            density=0.6,
            modifiers=[
                HumanizeModifier(timing_std=0.022, velocity_std=4),
                VelocityScalingModifier(scale=0.65)
            ]
        ),
        TrackConfig(
            name="mellow_bass",
            generator=SynthBassGenerator(waveform="sine", pattern="plucked"),
            instrument="synth_bass",
            density=0.6,
            octave_shift=-1,
            modifiers=[
                HumanizeModifier(timing_std=0.018, velocity_std=3),
                VelocityScalingModifier(scale=0.70)
            ]
        ),
        TrackConfig(
            name="soft_drums",
            generator=BreakbeatGenerator(variant="funky", chop_probability=0.08, ghost_notes=True),
            instrument="drums",
            density=0.6,
            modifiers=[
                HumanizeModifier(timing_std=0.026, velocity_std=5),
                VelocityScalingModifier(scale=0.68)
            ]
        ),
        TrackConfig(
            name="ambient_pad",
            generator=DarkPadGenerator(mode="minor_pad", register="low", velocity_level=0.28, chord_dur=8.0),
            instrument="dark_pad",
            density=0.5,
            octave_shift=-1,
            modifiers=[
                VelocityScalingModifier(scale=0.60)
            ]
        ),
        TrackConfig(
            name="harp_shimmer",
            generator=HarpGenerator(params=GeneratorParams(density=0.30)),
            instrument="harp",
            density=0.4,
            octave_shift=2,
            modifiers=[
                HumanizeModifier(timing_std=0.024, velocity_std=3),
                VelocityScalingModifier(scale=0.58)
            ]
        ),
        TrackConfig(
            name="solo_melody",
            generator=SoloMelodyGenerator(params=GeneratorParams(key_range_low=60, key_range_high=80), style="modal_ambient", vibrato_depth=0.25),
            instrument="synth_lead",
            density=0.5,
            octave_shift=1,
            modifiers=[
                HumanizeModifier(timing_std=0.020, velocity_std=4),
                VelocityScalingModifier(scale=0.65)
            ]
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

    # Soft dynamic mapping & separation
    scale_velocity_spread(tracks_data.get("soft_drums", []), 45, 80)
    scale_velocity_spread(tracks_data.get("lofi_keys", []), 40, 75)
    scale_velocity_spread(tracks_data.get("solo_melody", []), 45, 80)
    resolve_register_crossing(tracks_data.get("mellow_bass", []), tracks_data.get("ambient_pad", []), tracks_data.get("solo_melody", []))

    inst = {
        "lofi_keys": PIANO,
        "mellow_bass": SYNTH_BASS,
        "soft_drums": DRUMS,
        "ambient_pad": DARK_PAD,
        "harp_shimmer": HARP,
        "solo_melody": SYNTH_LEAD,
    }

    produce_track(
        tracks=tracks_data,
        bpm=70.0,
        instruments=inst,
        path=OUT / "03_Midnight_Vinyl.mid",
        mood=Mood.INTIMATE,
        key=key,
        verbose=False,
        sections=[(0.0, "Intro"), (16.0, "Theme"), (32.0, "Variation"), (64.0, "Climax"), (96.0, "Breakdown"), (112.0, "Fade")],
    )


def generate_album():
    print("\n" + "=" * 80)
    print("        T A P E   D U S T")
    print("        Cozy Lo-Fi Analog & Atmospheric Tape Album")
    print("=" * 80)

    produce_morning_coffee()
    produce_rainy_window()
    produce_midnight_vinyl()

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: TAPE DUST")
    print(f"  Output folder: {OUT.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    generate_album()
