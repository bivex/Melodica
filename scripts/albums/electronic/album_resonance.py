# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/albums/electronic/album_resonance.py — "Resonance Spectrum" Album.
Juicy and well-performing electronic breakbeat and downtempo album.
"""

from pathlib import Path
from melodica.types import NoteInfo, Scale, Mode
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, structure_to_schedule
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.breakbeat import BreakbeatGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
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


# =====================================================================
# Track 1: Solar Flare — 88 BPM — C Dorian
# =====================================================================
def produce_solar_flare():
    print("  1. Solar Flare [C Dorian — 88 BPM]")
    key = Scale(root=0, mode=Mode.DORIAN)  # C Dorian
    dur_bars = 32

    parts = [
        IdeaPart(
            name="ResonanceTheme",
            bars=dur_bars,
            scale=key,
            tempo=88,
            progression_type="coupled_hmm"
        )
    ]

    track_list = [
        TrackConfig(
            name="ambient_pad",
            generator=DarkPadGenerator(mode="minor_pad", register="low", velocity_level=0.32, chord_dur=8.0),
            instrument="synth_pad",
            density=0.5,
            phrase_schedule=structure_to_schedule("A B A B C C' R R", 4)
        ),
        TrackConfig(
            name="synth_bass",
            generator=SynthBassGenerator(waveform="saw", pattern="reese", slide_probability=0.30, octave_variation=0.1),
            instrument="synth_bass",
            density=0.6,
            octave_shift=-1,
            phrase_schedule=structure_to_schedule("R A A B C C' R R", 4)
        ),
        TrackConfig(
            name="drums",
            generator=BreakbeatGenerator(variant="think", chop_probability=0.10, ghost_notes=True),
            instrument="drums",
            density=0.7,
            phrase_schedule=structure_to_schedule("R R A B C C' R R", 4)
        ),
        TrackConfig(
            name="keys",
            generator=ArpeggiatorGenerator(pattern="up_down", note_duration=0.25),
            instrument="piano",
            density=0.6,
            phrase_schedule=structure_to_schedule("A B A B C C' R R", 4)
        ),
        TrackConfig(
            name="lead_solo",
            generator=SoloMelodyGenerator(style="space_synth", vibrato_depth=0.5),
            instrument="synth_lead",
            density=0.6,
            phrase_schedule=structure_to_schedule("R B R B C C' A R", 4)
        )
    ]

    config = IdeaToolConfig(
        parts=parts,
        tracks=track_list,
        scale=key,
        tempo=88,
        use_tension_curve=True
    )

    tool = IdeaTool(config)
    tracks_dict = tool.generate()

    # Produce output using the rich Section Orchestrator Layer
    produce_track(
        tracks_dict,
        bpm=88,
        instruments={
            "ambient_pad": POLYSYNTH,
            "synth_bass": SYNTH_BASS,
            "drums": DRUMS,
            "keys": PIANO,
            "lead_solo": SYNTH_LEAD
        },
        path="01_Solar_Flare.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=False,
        sections=[(0.0, "Intro"), (16.0, "Theme"), (32.0, "Variation"), (64.0, "Climax"), (96.0, "Breakdown"), (112.0, "Fade")],
    )


# =====================================================================
# Track 2: Neon Rain — 96 BPM — G Aeolian
# =====================================================================
def produce_neon_rain():
    print("  2. Neon Rain [G Minor — 96 BPM]")
    key = Scale(root=7, mode=Mode.AEOLIAN)  # G Minor
    dur_bars = 32

    parts = [
        IdeaPart(
            name="DrizzleTheme",
            bars=dur_bars,
            scale=key,
            tempo=96,
            progression_type="coupled_hmm"
        )
    ]

    track_list = [
        TrackConfig(
            name="warm_pad",
            generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.28, chord_dur=4.0),
            instrument="synth_pad",
            density=0.5,
            phrase_schedule=structure_to_schedule("A B A B C C' R R", 4)
        ),
        TrackConfig(
            name="plucked_bass",
            generator=SynthBassGenerator(waveform="sine", pattern="plucked"),
            instrument="synth_bass",
            density=0.7,
            octave_shift=-1,
            phrase_schedule=structure_to_schedule("A A B B C C' R R", 4)
        ),
        TrackConfig(
            name="breakbeat",
            generator=BreakbeatGenerator(variant="funky", chop_probability=0.15, ghost_notes=True),
            instrument="drums",
            density=0.7,
            phrase_schedule=structure_to_schedule("R A A B C C' R R", 4)
        ),
        TrackConfig(
            name="glock_shimmer",
            generator=GlockenspielGenerator(pattern="arpeggio"),
            instrument="glockenspiel",
            density=0.5,
            phrase_schedule=structure_to_schedule("R R B B C C' R R", 4)
        ),
        TrackConfig(
            name="vocal_lead",
            generator=SoloMelodyGenerator(style="modal_ambient", vibrato_depth=0.35),
            instrument="synth_lead",
            density=0.6,
            phrase_schedule=structure_to_schedule("R B R B C C' A R", 4)
        )
    ]

    config = IdeaToolConfig(
        parts=parts,
        tracks=track_list,
        scale=key,
        tempo=96,
        use_tension_curve=True
    )

    tool = IdeaTool(config)
    tracks_dict = tool.generate()

    produce_track(
        tracks_dict,
        bpm=96,
        instruments={
            "warm_pad": POLYSYNTH,
            "plucked_bass": SYNTH_BASS,
            "breakbeat": DRUMS,
            "glock_shimmer": GLOCKENSPIEL,
            "vocal_lead": SYNTH_LEAD
        },
        path="02_Neon_Rain.mid",
        mood=Mood.INTIMATE,
        key=key,
        verbose=False,
        sections=[(0.0, "Intro"), (16.0, "Theme"), (32.0, "Variation"), (64.0, "Climax"), (96.0, "Breakdown"), (112.0, "Fade")],
    )


# =====================================================================
# Track 3: Quantum Shift — 78 BPM — D Phrygian
# =====================================================================
def produce_quantum_shift():
    print("  3. Quantum Shift [D Phrygian — 78 BPM]")
    key = Scale(root=2, mode=Mode.PHRYGIAN)  # D Phrygian
    dur_bars = 32

    parts = [
        IdeaPart(
            name="ShiftTheme",
            bars=dur_bars,
            scale=key,
            tempo=78,
            progression_type="coupled_hmm"
        )
    ]

    track_list = [
        TrackConfig(
            name="drone_pad",
            generator=DarkPadGenerator(mode="phrygian_pad", register="low", velocity_level=0.35, chord_dur=8.0),
            instrument="synth_pad",
            density=0.4,
            phrase_schedule=structure_to_schedule("A B A B C C' R R", 4)
        ),
        TrackConfig(
            name="sub_bass",
            generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
            instrument="synth_bass",
            density=0.6,
            octave_shift=-1,
            phrase_schedule=structure_to_schedule("A A B B C C' R R", 4)
        ),
        TrackConfig(
            name="drums",
            generator=BreakbeatGenerator(variant="think", chop_probability=0.08, ghost_notes=True),
            instrument="drums",
            density=0.7,
            phrase_schedule=structure_to_schedule("R R A B C C' R R", 4)
        ),
        TrackConfig(
            name="harp_ripple",
            generator=HarpGenerator(pattern="cascade"),
            instrument="harp",
            density=0.5,
            phrase_schedule=structure_to_schedule("A B R B C C' R R", 4)
        ),
        TrackConfig(
            name="strings_lead",
            generator=SoloMelodyGenerator(style="cinematic_strings", vibrato_depth=0.6),
            instrument="synth_lead",
            density=0.6,
            phrase_schedule=structure_to_schedule("R B R B' C C' A R", 4)
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
            "drone_pad": POLYSYNTH,
            "sub_bass": SYNTH_BASS,
            "drums": DRUMS,
            "harp_ripple": HARP,
            "strings_lead": SYNTH_LEAD
        },
        path="03_Quantum_Shift.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=False,
        sections=[(0.0, "Intro"), (16.0, "Theme"), (32.0, "Variation"), (64.0, "Climax"), (96.0, "Breakdown"), (112.0, "Fade")],
    )


# =====================================================================
# Main execution
# =====================================================================
if __name__ == "__main__":
    import os
    print("================================================================================")
    print("        R E S O N A N C E   S P E C T R U M")
    print("        Juicy & Well-Performing Section-aware Electronic Album")
    print("================================================================================")

    # Clean existing folder
    out_dir = Path("output/album_resonance")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Compile tracks
    produce_solar_flare()
    produce_neon_rain()
    produce_quantum_shift()

    # Move output files to output/album_resonance/
    import shutil
    for f in ["01_Solar_Flare.mid", "02_Neon_Rain.mid", "03_Quantum_Shift.mid"]:
        src = Path(f)
        if src.exists():
            shutil.move(str(src), str(out_dir / f))

    print("\n================================================================================")
    print("  PRODUCTION COMPLETE: RESONANCE SPECTRUM")
    print("  Output folder: " + str(out_dir.resolve()))
    print("================================================================================")
