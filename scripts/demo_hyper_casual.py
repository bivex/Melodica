# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/demo_hyper_casual.py — Hyper-Casual Game Music Generator.

Showcases bouncy, upbeat, and repetitive rhythms using the custom hc_* library.
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.generators.melody import MelodyGenerator
from melodica.generators.chord_gen import ChordGenerator
from melodica.generators.bass import BassGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

def main():
    print("================================================================================")
    print("  H Y P E R - C A S U A L   B E A T   G E N E R A T O R  (Custom Library)")
    print("================================================================================")

    out_dir = Path("output/demo_hyper_casual")
    out_dir.mkdir(exist_ok=True, parents=True)

    # Bright, happy major scale
    scale = Scale(0, Mode.MAJOR) # C Major

    tracks = [
        # Main drum beat using a chip/8-bit loop
        TrackConfig(
            name="Bouncy_Drums",
            generator=MelodyGenerator(mode="chord_tones", rhythm=get_rhythm("hc_chip_8bit_loop")),
            instrument="drums", density=1.0
        ),
        # Plucky arcade melody
        TrackConfig(
            name="Marimba_Plucks",
            generator=MelodyGenerator(mode="scale_walk", rhythm=get_rhythm("hc_arcade_simple")),
            instrument="marimba", density=0.9, octave_shift=1
        ),
        # High-energy bouncy chords
        TrackConfig(
            name="Synth_Bounce",
            generator=ChordGenerator(voicing="closed", rhythm=get_rhythm("hc_fever_mode")),
            instrument="synth_lead", density=1.0
        ),
        # Springy, jumping bass
        TrackConfig(
            name="Jump_Bass",
            generator=BassGenerator(style="root_fifth"),
            instrument="synth_bass", density=0.8, octave_shift=-1
        )
    ]

    parts = [
        IdeaPart(
            name="Gameplay_Loop", bars=16, scale=scale, tempo=135,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Bouncy_Drums":   structure_to_schedule("A B A B", 4),
                "Marimba_Plucks": structure_to_schedule("A A B B:var", 4),
                "Synth_Bounce":   structure_to_schedule("A A A B", 4),
                "Jump_Bass":      structure_to_schedule("A A A A", 4),
            }
        )
    ]

    print("  Generating Hyper-Casual gameplay loop with 'hc_' presets...")
    config = IdeaToolConfig(
        style="pop", # Poppy, happy harmony
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
    )
    
    notes_dict = IdeaTool(config).generate()
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
    instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks}
    
    file_path = out_dir / "Hyper_Casual_Loop.mid"
    export_multitrack_midi(tracks_data, str(file_path), bpm=135, instruments=instruments_map)

    print()
    print("  SUCCESS! Hyper-Casual loop exported to:")
    print(f"  {file_path.absolute()}")
    print("================================================================================")

if __name__ == "__main__":
    main()
