# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/demo_glue_transitions.py — Micro-arrangement and Transitions Demo.

Demonstrates the new 'Glue' modifiers:
1. DrumFillModifier: Automatically inserts a fast snare roll 1 beat before a drop.
2. DropSilenceModifier: Instantly mutes basses, chords, and pads right before the drop
   to create a massive "vacuum" effect (Drop Silence).
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.generators.melody import MelodyGenerator
from melodica.generators.chord_gen import ChordGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

# Import the new Glue modifiers
from melodica.modifiers import (
    ModifierPipeline, ModifierContext, 
    DrumFillModifier, DropSilenceModifier
)
from melodica.types import MusicTimeline

def main():
    print("================================================================================")
    print("  M I C R O - A R R A N G E M E N T   &   T R A N S I T I O N S")
    print("================================================================================")

    out_dir = Path("output/demo_glue_transitions")
    out_dir.mkdir(exist_ok=True, parents=True)

    scale = Scale(0, Mode.NATURAL_MINOR) # C Minor

    tracks = [
        TrackConfig(
            name="Main_Drums",
            generator=TrapDrumsGenerator(hat_roll_density=0.8),
            instrument="drums", density=1.0
        ),
        TrackConfig(
            name="Huge_Bass",
            generator=BassGenerator(style="root_fifth"),
            instrument="synth_bass", density=1.0, octave_shift=-2
        ),
        TrackConfig(
            name="EDM_Chords",
            generator=ChordGenerator(voicing="closed", rhythm=get_rhythm("straight_8ths")),
            instrument="synth_lead", density=1.0
        ),
        TrackConfig(
            name="Sweep_FX",
            generator=FXRiserGenerator(riser_type="white_noise", length_beats=16.0),
            instrument="synth_fx", density=1.0
        )
    ]

    parts = [
        # 1. Build Up (4 bars = 16 beats)
        IdeaPart(
            name="BuildUp", bars=4, scale=scale, tempo=128,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Main_Drums": structure_to_schedule("A", 4),
                "Huge_Bass":  structure_to_schedule("A", 4),
                "EDM_Chords": structure_to_schedule("A", 4),
                "Sweep_FX":   structure_to_schedule("A", 4),
            }
        ),
        # 2. The Drop (4 bars = 16 beats)
        IdeaPart(
            name="TheDrop", bars=4, scale=scale, tempo=128,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Main_Drums": structure_to_schedule("B", 4),
                "Huge_Bass":  structure_to_schedule("B", 4),
                "EDM_Chords": structure_to_schedule("B", 4),
                "Sweep_FX":   structure_to_schedule("R", 4),
            }
        )
    ]

    print("  Generating Base Arrangement (8 bars total)...")
    config = IdeaToolConfig(
        style="edm", 
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
    )
    
    notes_dict = IdeaTool(config).generate()
    
    # ---------------------------------------------------------
    # APPLYING GLUE MODIFIERS
    # ---------------------------------------------------------
    print("  Applying Micro-Arrangement Glue (Fills & Silence)...")
    
    total_bars = sum(p.bars for p in parts)
    timeline = notes_dict.get("_timeline", MusicTimeline(chords=[], keys=[]))
    mod_context = ModifierContext(
        duration_beats=total_bars * 4,
        chords=timeline.chords,
        timeline=timeline,
        scale=scale,
    )

    # The drop happens exactly at beat 16.0 (end of 4th bar)
    drop_beat = 16.0

    pipelines = {
        # 1. Mute bass, chords, and sweep FX for exactly 1 beat before the drop
        "Huge_Bass":  [DropSilenceModifier(silence_duration=1.0, specific_beats=[drop_beat], apply_at_end=False)],
        "EDM_Chords": [DropSilenceModifier(silence_duration=1.0, specific_beats=[drop_beat], apply_at_end=False)],
        "Sweep_FX":   [DropSilenceModifier(silence_duration=1.0, specific_beats=[drop_beat], apply_at_end=False)],
        
        # 2. Override the last beat of the drums with a fast 16th note snare fill
        "Main_Drums": [DrumFillModifier(fill_duration=1.0, subdivision=0.25, fill_pitch=38, specific_beats=[drop_beat], apply_at_end=False)]
    }

    for name, modifiers in pipelines.items():
        if name in notes_dict:
            p = ModifierPipeline(base_notes=notes_dict[name])
            for mod in modifiers:
                p.add_modifier(mod)
            notes_dict[name] = p.process(mod_context)

    # Export
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
    instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks}
    
    file_path = out_dir / "Glue_Transitions_Demo.mid"
    export_multitrack_midi(tracks_data, str(file_path), bpm=128, instruments=instruments_map)

    print()
    print("  SUCCESS! Transitions applied.")
    print("  Listen to beat 15.0 - 16.0: All synths cut out, snare roll builds up,")
    print("  and then the Drop hits exactly at beat 16.0!")
    print(f"  Exported to: {file_path.absolute()}")
    print("================================================================================")

if __name__ == "__main__":
    main()
