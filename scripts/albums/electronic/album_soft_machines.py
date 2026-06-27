# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/albums/electronic/album_soft_machines.py — "Soft Machines" Album.
Organic long-form nocturnal electronics / tape ambient / broken beat album.
"""

from pathlib import Path
from melodica.types import NoteInfo, Scale, Mode
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, structure_to_schedule
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.generators.lofi_hiphop import LoFiHipHopGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.breakbeat import BreakbeatGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator

# GM Programs mapping
PIANO = 0
RHODES = 4
SYNTH_BASS = 38
DARK_PAD = 88
SYNTH_LEAD = 80
POLYSYNTH = 90
EFFECTS = 96
DRUMS = 0
GLOCKENSPIEL = 9
HARP = 46


# =====================================================================
# Track 1: Velvet Circuit — 78 BPM — A Minor
# =====================================================================
def produce_velvet_circuit():
    print("  1. Velvet Circuit [A Minor — 78 BPM]")
    key = Scale(root=9, mode=Mode.AEOLIAN)  # A Minor
    dur_bars = 32

    parts = [
        IdeaPart(
            name="VelvetTheme",
            bars=dur_bars,
            scale=key,
            tempo=78,
            progression_type="coupled_hmm"
        )
    ]

    track_list = [
        TrackConfig(
            name="rhodes_texture",
            generator=LoFiHipHopGenerator(),
            instrument="rhodes",
            density=0.55,
            phrase_schedule=structure_to_schedule("A B A B C C' R R", 4)
        ),
        TrackConfig(
            name="sub_bass",
            generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
            instrument="synth_bass",
            density=0.6,
            octave_shift=-1,
            phrase_schedule=structure_to_schedule("R A A B C C' R R", 4)
        ),
        TrackConfig(
            name="analog_wash",
            generator=DarkPadGenerator(mode="minor_pad", register="low", velocity_level=0.30, chord_dur=8.0),
            instrument="synth_pad",
            density=0.45,
            phrase_schedule=structure_to_schedule("A B A B C C' R R", 4)
        ),
        TrackConfig(
            name="tape_lead",
            generator=SoloMelodyGenerator(style="modal_ambient", vibrato_depth=0.4),
            instrument="synth_lead",
            density=0.55,
            phrase_schedule=structure_to_schedule("R B R B C C' A R", 4)
        ),
        TrackConfig(
            name="electronic_drums",
            generator=ElectronicDrumsGenerator(kit="lofi"),
            instrument="drums",
            density=0.65,
            phrase_schedule=structure_to_schedule("R R A B C C' R R", 4)
        )
    ]

    config = IdeaToolConfig(
        parts=parts,
        tracks=track_list,
        scale=key,
        tempo=78,
        use_tension_curve=True
    )

    tool = IdeaTool(config)
    tracks_dict = tool.generate()

    produce_track(
        tracks_dict,
        bpm=78,
        instruments={
            "rhodes_texture": RHODES,
            "sub_bass": SYNTH_BASS,
            "analog_wash": POLYSYNTH,
            "tape_lead": SYNTH_LEAD,
            "electronic_drums": DRUMS
        },
        path="01_Velvet_Circuit.mid",
        mood=Mood.INTIMATE,
        key=key,
        verbose=False,
        sections=[(0.0, "Intro"), (16.0, "Theme"), (32.0, "Variation"), (64.0, "Climax"), (96.0, "Breakdown"), (112.0, "Fade")],
    )


# =====================================================================
# Track 2: Static Bloom — 84 BPM — D Dorian
# =====================================================================
def produce_static_bloom():
    print("  2. Static Bloom [D Dorian — 84 BPM]")
    key = Scale(root=2, mode=Mode.DORIAN)  # D Dorian
    dur_bars = 28  # 7 slots * 4 bars

    parts = [
        IdeaPart(
            name="BloomTheme",
            bars=dur_bars,
            scale=key,
            tempo=84,
            progression_type="coupled_hmm"
        )
    ]

    track_list = [
        TrackConfig(
            name="analog_plucks",
            generator=ArpeggiatorGenerator(pattern="up_down", note_duration=0.25),
            instrument="piano",
            density=0.6,
            phrase_schedule=structure_to_schedule("A B A B C R R", 4)
        ),
        TrackConfig(
            name="reese_bass",
            generator=SynthBassGenerator(waveform="saw", pattern="reese", slide_probability=0.20),
            instrument="synth_bass",
            density=0.65,
            octave_shift=-1,
            phrase_schedule=structure_to_schedule("R A A B C R R", 4)
        ),
        TrackConfig(
            name="vintage_strings",
            generator=DarkPadGenerator(mode="minor_pad", register="low", velocity_level=0.32, chord_dur=4.0),
            instrument="synth_pad",
            density=0.5,
            phrase_schedule=structure_to_schedule("A B A B C R R", 4)
        ),
        TrackConfig(
            name="harp_notes",
            generator=HarpGenerator(pattern="cascade"),
            instrument="harp",
            density=0.45,
            phrase_schedule=structure_to_schedule("A R A B C R R", 4)
        ),
        TrackConfig(
            name="swung_groove",
            generator=BreakbeatGenerator(variant="funky", chop_probability=0.08, ghost_notes=True),
            instrument="drums",
            density=0.7,
            phrase_schedule=structure_to_schedule("R A A B C R R", 4)
        )
    ]

    config = IdeaToolConfig(
        parts=parts,
        tracks=track_list,
        scale=key,
        tempo=84,
        use_tension_curve=True
    )

    tool = IdeaTool(config)
    tracks_dict = tool.generate()

    produce_track(
        tracks_dict,
        bpm=84,
        instruments={
            "analog_plucks": PIANO,
            "reese_bass": SYNTH_BASS,
            "vintage_strings": POLYSYNTH,
            "harp_notes": HARP,
            "swung_groove": DRUMS
        },
        path="02_Static_Bloom.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=False,
        sections=[(0.0, "Intro"), (16.0, "Theme"), (48.0, "Variation"), (64.0, "Climax"), (80.0, "Breakdown"), (96.0, "Fade")],
    )


# =====================================================================
# Track 3: Memory Foam — 72 BPM — F Minor
# =====================================================================
def produce_memory_foam():
    print("  3. Memory Foam [F Minor — 72 BPM]")
    key = Scale(root=5, mode=Mode.AEOLIAN)  # F Minor
    dur_bars = 36  # 9 slots * 4 bars = 144 beats

    parts = [
        IdeaPart(
            name="MemoryTheme",
            bars=dur_bars,
            scale=key,
            tempo=72,
            progression_type="coupled_hmm"
        )
    ]

    track_list = [
        TrackConfig(
            name="ambient_pad",
            generator=DarkPadGenerator(mode="minor_pad", register="low", velocity_level=0.35, chord_dur=8.0),
            instrument="synth_pad",
            density=0.45,
            phrase_schedule=structure_to_schedule("A B B C C R R R R", 4)
        ),
        TrackConfig(
            name="rhodes_chords",
            generator=LoFiHipHopGenerator(),
            instrument="rhodes",
            density=0.55,
            phrase_schedule=structure_to_schedule("A A B B C C R R R", 4)
        ),
        TrackConfig(
            name="sub_bass",
            generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
            instrument="synth_bass",
            density=0.6,
            octave_shift=-1,
            phrase_schedule=structure_to_schedule("R A A B B C C R R", 4)
        ),
        TrackConfig(
            name="nostalgic_lead",
            generator=SoloMelodyGenerator(style="space_synth", vibrato_depth=0.55),
            instrument="synth_lead",
            density=0.6,
            phrase_schedule=structure_to_schedule("R B R B C C A R R", 4)
        ),
        TrackConfig(
            name="fx_riser",
            generator=FXRiserGenerator(length_beats=16.0),
            instrument="effects",
            density=0.3,
            phrase_schedule=structure_to_schedule("R R A R B R C R R", 4)
        ),
        TrackConfig(
            name="fx_impact",
            generator=FXImpactGenerator(),
            instrument="effects",
            density=0.3,
            phrase_schedule=structure_to_schedule("R R R A R B R C R", 4)
        )
    ]

    config = IdeaToolConfig(
        parts=parts,
        tracks=track_list,
        scale=key,
        tempo=72,
        use_tension_curve=True
    )

    tool = IdeaTool(config)
    tracks_dict = tool.generate()

    produce_track(
        tracks_dict,
        bpm=72,
        instruments={
            "ambient_pad": POLYSYNTH,
            "rhodes_chords": RHODES,
            "sub_bass": SYNTH_BASS,
            "nostalgic_lead": SYNTH_LEAD,
            "fx_riser": EFFECTS,
            "fx_impact": EFFECTS
        },
        path="03_Memory_Foam.mid",
        mood=Mood.INTIMATE,
        key=key,
        verbose=False,
        sections=[(0.0, "Intro"), (16.0, "Theme"), (48.0, "Variation"), (80.0, "Climax"), (112.0, "Fade")],
    )


# =====================================================================
# Main execution
# =====================================================================
if __name__ == "__main__":
    import os
    print("================================================================================")
    print("        S O F T   M A C H I N E S")
    print("        Organic Long-form Listening Electronic Album")
    print("================================================================================")

    # Clean existing folder
    out_dir = Path("output/album_soft_machines")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Compile tracks
    produce_velvet_circuit()
    produce_static_bloom()
    produce_memory_foam()

    # Move output files to output/album_soft_machines/
    import shutil
    for f in ["01_Velvet_Circuit.mid", "02_Static_Bloom.mid", "03_Memory_Foam.mid"]:
        src = Path(f)
        if src.exists():
            shutil.move(str(src), str(out_dir / f))

    print("\n================================================================================")
    print("  PRODUCTION COMPLETE: SOFT MACHINES")
    print("  Output folder: " + str(out_dir.resolve()))
    print("================================================================================")
