# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_epic_orchestra.py — An epic orchestral album showcase.
Focuses on dramatic progression, heavy brass, sweeping strings, and choirs.
Now utilizes the advanced Arrangement & Expression pipeline.
"""

import os
from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS, structure_to_schedule
)
from melodica.generators import (
    MelodyGenerator, BassGenerator, StringsEnsembleGenerator, 
    AmbientPadGenerator, ArpeggiatorGenerator, FluteGenerator
)
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.sfx_percussion import SFXPercussionGenerator
from melodica.modifiers import (
    ModifierPipeline, ModifierContext, HumanizeModifier,
    VelocityCurveModifier, MetricAccentModifier
)
from melodica.types import Scale, Mode, MusicTimeline

def main():
    print("================================================================================")
    print("  E P I C   S Y M P H O N Y   —   A L B U M   G E N E R A T O R")
    print("  Focus: Advanced Arrangement, Dynamics, and Expression")
    print("================================================================================")

    out_dir = Path("output/album_epic_orchestra")
    out_dir.mkdir(exist_ok=True, parents=True)

    scale = Scale(2, Mode.NATURAL_MINOR)  # D Minor

    # 1. Track Definitions
    tracks = [
        TrackConfig(
            name="Epic_Strings",
            generator=StringsEnsembleGenerator(section_size="full", articulation="legato", divisi=4),
            instrument="strings", density=0.8, octave_shift=1,
        ),
        TrackConfig(
            name="Low_Brass_Foundation",
            generator=AmbientPadGenerator(voicing="spread"),
            instrument="brass_section", density=0.6, octave_shift=-1,
        ),
        TrackConfig(
            name="Sub_Bass",
            generator=BassGenerator(style="root_only"),
            instrument="contrabass", density=0.6, octave_shift=-2,
        ),
        TrackConfig(
            name="Tension_Arp",
            generator=ArpeggiatorGenerator(pattern="up_down"),
            instrument="string_ensemble_2", density=0.5, octave_shift=0,
        ),
        TrackConfig(
            name="Solo_Flute_Melody",
            generator=FluteGenerator(),
            instrument="flute", density=0.4, octave_shift=2,
        ),
        TrackConfig(
            name="Epic_Choir",
            generator=ChoirAahsGenerator(voice_count=4),
            instrument="choir_aahs", density=0.7, octave_shift=0,
        ),
        TrackConfig(
            name="Cinematic_Percussion",
            generator=SFXPercussionGenerator(instrument="taiko_drum"),
            instrument="taiko_drum", density=0.4, octave_shift=0,
        ),
        TrackConfig(
            name="High_Percussion",
            generator=SFXPercussionGenerator(instrument="reverse_cymbal"),
            instrument="reverse_cymbal", density=0.3, octave_shift=1,
        ),
    ]

    # 2. Structure & Schedule
    parts = [
        # === 1. Intro (8 bars) — sparse and dark ===
        IdeaPart(
            name="Intro", bars=8, scale=scale, tempo=85,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Epic_Strings":         structure_to_schedule("R", 8),
                "Low_Brass_Foundation": structure_to_schedule("A", 8),
                "Sub_Bass":             structure_to_schedule("A", 8),
                "Tension_Arp":          structure_to_schedule("R", 8),
                "Solo_Flute_Melody":    structure_to_schedule("A", 8),
                "Epic_Choir":           structure_to_schedule("R", 8),
                "Cinematic_Percussion": structure_to_schedule("A", 8),
                "High_Percussion":      structure_to_schedule("R", 8),
            },
        ),

        # === 2. Build (8 bars) — tension rising ===
        IdeaPart(
            name="Build", bars=8, scale=scale, tempo=88,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Epic_Strings":         structure_to_schedule("B", 8),
                "Low_Brass_Foundation": structure_to_schedule("A", 8),
                "Sub_Bass":             structure_to_schedule("B", 8),
                "Tension_Arp":          structure_to_schedule("B", 8),
                "Solo_Flute_Melody":    structure_to_schedule("R", 8),
                "Epic_Choir":           structure_to_schedule("B:var", 8),
                "Cinematic_Percussion": structure_to_schedule("B", 8),
                "High_Percussion":      structure_to_schedule("B", 8),
            },
        ),

        # === 3. Climax (16 bars) — full orchestra ===
        IdeaPart(
            name="Climax", bars=16, scale=scale, tempo=92,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Epic_Strings":         structure_to_schedule("C", 16),
                "Low_Brass_Foundation": structure_to_schedule("C", 16),
                "Sub_Bass":             structure_to_schedule("C", 16),
                "Tension_Arp":          structure_to_schedule("C", 16),
                "Solo_Flute_Melody":    structure_to_schedule("C:var", 16),
                "Epic_Choir":           structure_to_schedule("C", 16),
                "Cinematic_Percussion": structure_to_schedule("C:var", 16),
                "High_Percussion":      structure_to_schedule("C:var", 16),
            },
        ),

        # === 4. Outro (8 bars) — decompress and fade ===
        IdeaPart(
            name="Outro", bars=8, scale=scale, tempo=80,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Epic_Strings":         structure_to_schedule("R", 8),
                "Low_Brass_Foundation": structure_to_schedule("A:inv", 8),
                "Sub_Bass":             structure_to_schedule("A:retro", 8),
                "Tension_Arp":          structure_to_schedule("R", 8),
                "Solo_Flute_Melody":    structure_to_schedule("A R", 4, loop=False),
                "Epic_Choir":           structure_to_schedule("R", 8),
                "Cinematic_Percussion": structure_to_schedule("R", 8),
                "High_Percussion":      structure_to_schedule("R", 8),
            },
        ),
    ]

    print(f"\n--- Generating Structure... ---")
    config = IdeaToolConfig(
        style="cinematic_hybrid",
        parts=parts,
        tracks=tracks,
        use_tension_curve=True
    )

    notes_dict = IdeaTool(config).generate()
    
    # 3. Post-Processing: Expression Pipeline
    total_bars = sum(p.bars for p in parts if p.bars is not None)
    timeline = notes_dict.get("_timeline", MusicTimeline(chords=[], keys=[]))
    mod_context = ModifierContext(
        duration_beats=total_bars * 4,
        chords=timeline.chords,
        timeline=timeline,
        scale=scale,
    )

    pipelines = {
        "Epic_Strings": ([
            HumanizeModifier(timing_std=0.015, velocity_std=6.0),
            VelocityCurveModifier(start_vel=40, end_vel=100, curve="crescendo"),
            MetricAccentModifier(strength=0.2)
        ], "Humanize + Crescendo + Accent"),
        
        "Low_Brass_Foundation": ([
            HumanizeModifier(timing_std=0.02, velocity_std=5.0),
            MetricAccentModifier(strength=0.3)
        ], "Humanize + Accent"),
        
        "Sub_Bass": ([
            HumanizeModifier(timing_std=0.03, velocity_std=10.0),
            MetricAccentModifier(strength=0.3)
        ], "Humanize + Accent"),
        
        "Tension_Arp": ([
            HumanizeModifier(timing_std=0.01, velocity_std=4.0),
            VelocityCurveModifier(start_vel=50, end_vel=95, curve="exponential"),
        ], "Humanize + Exp Crescendo"),
        
        "Solo_Flute_Melody": ([
            HumanizeModifier(timing_std=0.03, velocity_std=8.0),
            VelocityCurveModifier(start_vel=60, end_vel=80, curve="swell"),
            MetricAccentModifier(strength=0.15)
        ], "Humanize + Swell + Accent"),
        
        "Epic_Choir": ([
            HumanizeModifier(timing_std=0.03, velocity_std=4.0),
            VelocityCurveModifier(start_vel=50, end_vel=110, curve="exponential"),
            MetricAccentModifier(strength=0.1)
        ], "Humanize + Epic Crescendo"),
        
        "Cinematic_Percussion": ([
            HumanizeModifier(timing_std=0.01, velocity_std=12.0),
            MetricAccentModifier(strength=0.5)
        ], "Humanize + Punchy Accent"),
        
        "High_Percussion": ([
            HumanizeModifier(timing_std=0.02, velocity_std=5.0),
            VelocityCurveModifier(start_vel=60, end_vel=100, curve="swell")
        ], "Humanize + Swell"),
    }

    print("\n  Applying Expression Pipeline...")
    for name, (modifiers, desc) in pipelines.items():
        if name in notes_dict:
            p = ModifierPipeline(base_notes=notes_dict[name])
            for mod in modifiers:
                p.add_modifier(mod)
            notes_dict[name] = p.process(mod_context)
            print(f"  > {name}: {desc}")

    # 4. Export
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
    filename = "01_Epic_Symphony.mid"
    filepath = out_dir / filename
    
    from melodica.midi import export_multitrack_midi
    instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks}
    
    export_multitrack_midi(
        tracks_data, 
        str(filepath), 
        bpm=85, # Base tempo, though parts have their own
        instruments=instruments_map
    )
    print(f"\n    ✓ Exported {filename}")

    print("\n================================================================================")
    print(f"  PRODUCTION COMPLETE. Output: {out_dir}")
    print("================================================================================")

if __name__ == "__main__":
    main()