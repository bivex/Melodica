# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/demo_grime_beat.py — UK Grime / Eskibeat Generator.

Showcases:
1. GrimeGenerator for square-wave stabs and sparse, aggressive drums.
2. Bass808SlidingGenerator tuned for aggressive sliding Grime bass.
3. 140 BPM syncopated energy.
4. Professional Grime song structure.
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.generators.grime import GrimeGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi


def _build_tracks():
    # Rhythms for the Grime vibe
    lead_rhythm = get_rhythm("straight_16ths") # High energy but gated
    
    return [
        # The core Grime engine (Drums + Stabs)
        TrackConfig(
            name="Grime_Core",
            generator=GrimeGenerator(
                variant="eskibeat", # Minimal, dark Wiley style
                synth_aggression=0.8,
                include_melody=True
            ),
            instrument="synth_lead", # Square wave vibe
            density=1.0,
        ),
        
        # Aggressive Sliding Bass
        TrackConfig(
            name="Grime_Bass",
            generator=Bass808SlidingGenerator(
                pattern="drill_sliding",
                slide_type="overlap",
                slide_probability=0.6,
                accent_velocity=1.2
            ),
            instrument="synth_bass",
            density=0.8,
            octave_shift=-2
        ),

        # Piercing High Lead
        TrackConfig(
            name="High_Lead",
            generator=LeadSynthGenerator(
                style="trance", # Fast syncopated runs
                portamento=0.2,
                note_length="staccato",
                rhythm=lead_rhythm
            ),
            instrument="synth_lead",
            density=0.4,
            octave_shift=1
        ),

        # Dark Transition FX
        TrackConfig(
            name="FX_Riser",
            generator=FXRiserGenerator(riser_type="white_noise", length_beats=16.0),
            instrument="synth_fx",
            density=0.2,
        ),
    ]


def _build_parts(scale):
    # Dark, dissonant progressions (Grime style)
    prog_dark   = ["im bIImaj7", "im VII", "im bV"]
    prog_verse  = ["im ivm bV im", "im bII im VII"]
    prog_hook   = ["im bII im bII", "im bII bIII bII"]
    
    return [
        # 1. Intro (8 bars) — Sparse
        IdeaPart(
            name="Intro", bars=8, scale=scale, tempo=140,
            progression_type="from_list",
            progression_list=prog_dark,
            track_phrase_schedules={
                "Grime_Core":    structure_to_schedule("A", 8),
                "Grime_Bass":    structure_to_schedule("R", 8),
                "High_Lead":     structure_to_schedule("R", 8),
                "FX_Riser":      structure_to_schedule("R", 8),
            },
        ),

        # 2. Verse 1 (16 bars)
        IdeaPart(
            name="Verse1", bars=16, scale=scale, tempo=140,
            progression_type="from_list",
            progression_list=prog_verse,
            track_phrase_schedules={
                "Grime_Core":    structure_to_schedule("A B", 8),
                "Grime_Bass":    structure_to_schedule("A", 16),
                "High_Lead":     structure_to_schedule("R A", 8),
                "FX_Riser":      structure_to_schedule("R", 16),
            },
        ),

        # 3. Hook (8 bars) — Peak Aggression
        IdeaPart(
            name="Hook", bars=8, scale=scale, tempo=140,
            progression_type="from_list",
            progression_list=prog_hook,
            track_phrase_schedules={
                "Grime_Core":    structure_to_schedule("C", 8),
                "Grime_Bass":    structure_to_schedule("C", 8),
                "High_Lead":     structure_to_schedule("C", 8),
                "FX_Riser":      structure_to_schedule("A", 8),
            },
        ),

        # 4. Breakdown (8 bars)
        IdeaPart(
            name="Breakdown", bars=8, scale=scale, tempo=138,
            progression_type="from_list",
            progression_list=prog_dark,
            track_phrase_schedules={
                "Grime_Core":    structure_to_schedule("D", 8),
                "Grime_Bass":    structure_to_schedule("R", 8),
                "High_Lead":     structure_to_schedule("R", 8),
                "FX_Riser":      structure_to_schedule("R", 8),
            },
        ),

        # 5. Outro (8 bars)
        IdeaPart(
            name="Outro", bars=8, scale=scale, tempo=140,
            progression_type="from_list",
            progression_list=prog_dark,
            track_phrase_schedules={
                "Grime_Core":    structure_to_schedule("A R", 4),
                "Grime_Bass":    structure_to_schedule("R", 8),
                "High_Lead":     structure_to_schedule("R", 8),
                "FX_Riser":      structure_to_schedule("R", 8),
            },
        ),
    ]


def main():
    print("================================================================================")
    print("  G R I M E   B E A T   G E N E R A T O R  (140 BPM Energy)")
    print("================================================================================")

    out_dir = Path("output/demo_grime_beat")
    out_dir.mkdir(exist_ok=True, parents=True)

    # F Minor (classic Grime key)
    scale = Scale(5, Mode.PHRYGIAN)
    
    tracks = _build_tracks()
    parts = _build_parts(scale)

    print("  Generating Grime arrangement...")
    config = IdeaToolConfig(
        style="grime",
        parts=parts,
        tracks=tracks,
        use_voice_leading=False,
        use_harmonic_verifier=True
    )
    
    notes_dict = IdeaTool(config).generate()

    # Print chords for analysis
    print("\n  [ANALYSIS] Generated Chord Progression:")
    chords = notes_dict.get("_chords", [])
    for c in chords:
        deg_str = f"({c.degree_roman})" if hasattr(c, "degree_roman") else f"(deg:{c.degree})"
        print(f"    {c.start:5.1f}b | {c.quality.name:8} on {c.root:2} {deg_str:8}")
    print()

    # Post-processing
    from melodica.modifiers import (
        ModifierPipeline, ModifierContext, HumanizeModifier,
        VelocityCurveModifier, MetricAccentModifier,
    )
    from melodica.types import MusicTimeline

    total_bars = sum(p.bars for p in parts)
    timeline = notes_dict.get("_timeline", MusicTimeline(chords=[], keys=[]))
    mod_context = ModifierContext(
        duration_beats=total_bars * 4,
        chords=timeline.chords,
        timeline=timeline,
        scale=scale,
    )

    print("  Applying Aggressive Expression Pipeline...")
    pipelines = {
        "High_Lead": [
            HumanizeModifier(timing_std=0.015, velocity_std=8.0), # Tighter timing
            MetricAccentModifier(strength=0.3)
        ],
        "Grime_Bass": [
            HumanizeModifier(timing_std=0.02, velocity_std=10.0),
            MetricAccentModifier(strength=0.4)
        ]
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
    
    export_multitrack_midi(
        tracks_data,
        str(out_dir / "Grime_Beat_140.mid"),
        bpm=140,
        instruments=instruments_map,
    )

    print()
    print("  SUCCESS! Grime beat exported to:")
    print(f"  {out_dir / 'Grime_Beat_140.mid'}")
    print("================================================================================")


if __name__ == "__main__":
    main()
