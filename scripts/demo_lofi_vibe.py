# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/demo_lofi_vibe.py — Lo-Fi Masterpiece Generator.

A sophisticated 8-part arrangement with:
- Multiple layers (Core, Sub-Bass, Cloud Pads, Lead Sax, Vocal Chops, FX)
- Dynamic song structure (Intro, Verse, Hook, Breakdown, Outro)
- Advanced post-processing (Humanization, Swells, Metric Accents)
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.generators.lofi_hiphop import LoFiHipHopGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi


def _build_tracks():
    # Rhythms from library
    lead_rhythm = get_rhythm("markov:ballad", syncopation=0.25)
    vocal_rhythm = get_rhythm("probabilistic:sparse", density=0.35)

    return [
        # Foundation: Keys & Lo-Fi Drums
        TrackConfig(
            name="LoFi_Core",
            generator=LoFiHipHopGenerator(
                variant="jazzy",
                swing_ratio=0.62,
                chord_voicing="ninth",
                vinyl_noise=0.5,
                tape_stop=0.1
            ),
            instrument="electric_piano",
            density=1.0,
        ),
        
        # Deep Sub warmth to anchor the low end
        TrackConfig(
            name="Sub_Bass",
            generator=Bass808SlidingGenerator(pattern="sub_only", slide_probability=0.2),
            instrument="synth_bass",
            density=0.7,
            octave_shift=-2
        ),

        # Atmospheric Cloud Pads
        TrackConfig(
            name="Cloud_Pad",
            generator=NebulaGenerator(variant="swell", density_notes=5, pitch_spread=12),
            instrument="dark_pad",
            density=0.4,
            octave_shift=-1
        ),
        
        # Expressive Lead
        TrackConfig(
            name="Lead_Sax",
            generator=MelodyGenerator(
                mode="downbeat_chord",
                rhythm=lead_rhythm,
                climax="auto",
                ornament_probability=0.3
            ),
            instrument="alto_sax",
            density=0.55,
        ),

        # Atmospheric Vocal Texture
        TrackConfig(
            name="Vocal_Chops",
            generator=VocalChopsGenerator(
                density=0.5,
                chop_pattern="syncopated",
                rhythm=vocal_rhythm
            ),
            instrument="synth_voice",
            density=0.45,
        ),

        # Transition FX
        TrackConfig(
            name="FX_Riser",
            generator=FXRiserGenerator(riser_type="white_noise", length_beats=8.0),
            instrument="synth_fx",
            density=0.3,
        ),
        TrackConfig(
            name="FX_Impact",
            generator=FXImpactGenerator(impact_type="vinyl_static", tail_length=4.0),
            instrument="synth_fx",
            density=0.2,
        ),
    ]


def _build_parts(scale):
    return [
        # 1. Intro (8 bars)
        IdeaPart(
            name="Intro", bars=8, scale=scale, tempo=80,
            track_phrase_schedules={
                "LoFi_Core":     structure_to_schedule("A", 8),
                "Sub_Bass":      structure_to_schedule("R", 8),
                "Cloud_Pad":     structure_to_schedule("A", 8),
                "Lead_Sax":      structure_to_schedule("R", 8),
                "Vocal_Chops":   structure_to_schedule("A R", 4),
                "FX_Riser":      structure_to_schedule("R", 8),
                "FX_Impact":     structure_to_schedule("A R", 4),
            },
        ),

        # 2. Verse 1 (16 bars)
        IdeaPart(
            name="Verse1", bars=16, scale=scale, tempo=82,
            track_phrase_schedules={
                "LoFi_Core":     structure_to_schedule("A B", 8),
                "Sub_Bass":      structure_to_schedule("A", 16),
                "Cloud_Pad":     structure_to_schedule("A", 16),
                "Lead_Sax":      structure_to_schedule("R A", 8),
                "Vocal_Chops":   structure_to_schedule("B", 16),
                "FX_Riser":      structure_to_schedule("R", 16),
                "FX_Impact":     structure_to_schedule("R", 16),
            },
        ),

        # 3. Hook (8 bars) — Peak Energy
        IdeaPart(
            name="Hook", bars=8, scale=scale, tempo=85,
            track_phrase_schedules={
                "LoFi_Core":     structure_to_schedule("C", 8),
                "Sub_Bass":      structure_to_schedule("C", 8),
                "Cloud_Pad":     structure_to_schedule("B", 8),
                "Lead_Sax":      structure_to_schedule("C", 8),
                "Vocal_Chops":   structure_to_schedule("C", 8),
                "FX_Riser":      structure_to_schedule("R", 8),
                "FX_Impact":     structure_to_schedule("C R", 4),
            },
        ),

        # 4. Breakdown (8 bars)
        IdeaPart(
            name="Breakdown", bars=8, scale=scale, tempo=78,
            track_phrase_schedules={
                "LoFi_Core":     structure_to_schedule("D", 8),
                "Sub_Bass":      structure_to_schedule("R", 8),
                "Cloud_Pad":     structure_to_schedule("C", 8),
                "Lead_Sax":      structure_to_schedule("R", 8),
                "Vocal_Chops":   structure_to_schedule("D", 8),
                "FX_Riser":      structure_to_schedule("R", 8),
                "FX_Impact":     structure_to_schedule("R", 8),
            },
        ),

        # 5. Verse 2 (12 bars) — Rebuild with variations
        IdeaPart(
            name="Verse2", bars=12, scale=scale, tempo=82,
            track_phrase_schedules={
                "LoFi_Core":     structure_to_schedule("A:var", 12),
                "Sub_Bass":      structure_to_schedule("B", 12),
                "Cloud_Pad":     structure_to_schedule("A:var", 12),
                "Lead_Sax":      structure_to_schedule("B:var", 12),
                "Vocal_Chops":   structure_to_schedule("R B:var", 6),
                "FX_Riser":      structure_to_schedule("R B", 6),
                "FX_Impact":     structure_to_schedule("R", 12),
            },
        ),

        # 6. Outro (8 bars)
        IdeaPart(
            name="Outro", bars=8, scale=scale, tempo=75,
            track_phrase_schedules={
                "LoFi_Core":     structure_to_schedule("A R", 4),
                "Sub_Bass":      structure_to_schedule("R", 8),
                "Cloud_Pad":     structure_to_schedule("A R", 4),
                "Lead_Sax":      structure_to_schedule("R", 8),
                "Vocal_Chops":   structure_to_schedule("E", 8),
                "FX_Riser":      structure_to_schedule("R", 8),
                "FX_Impact":     structure_to_schedule("R", 8),
            },
        ),
    ]


def main():
    print("================================================================================")
    print("  L O - F I   M A S T E R P I E C E   (Advanced Arrangement)")
    print("================================================================================")

    out_dir = Path("output/demo_lofi_vibe")
    out_dir.mkdir(exist_ok=True, parents=True)

    scale = Scale(8, Mode.NATURAL_MINOR) # G# Minor
    
    tracks = _build_tracks()
    parts = _build_parts(scale)

    print("  Generating Pro-level Lo-Fi arrangement...")
    config = IdeaToolConfig(
        style="lofi_hiphop",
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
        use_harmonic_verifier=True
    )
    
    notes_dict = IdeaTool(config).generate()

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

    print("  Polishing tracks with Expression Pipeline...")
    pipelines = {
        "Lead_Sax": [
            HumanizeModifier(timing_std=0.035, velocity_std=10.0),
            VelocityCurveModifier(start_vel=45, end_vel=95, curve="swell"),
            MetricAccentModifier(strength=0.25)
        ],
        "Vocal_Chops": [
            HumanizeModifier(timing_std=0.05, velocity_std=15.0),
            VelocityCurveModifier(start_vel=30, end_vel=75, curve="linear"),
        ],
        "Cloud_Pad": [
            HumanizeModifier(timing_std=0.01, velocity_std=5.0),
            VelocityCurveModifier(start_vel=25, end_vel=60, curve="exponential"),
        ],
        "Sub_Bass": [
            HumanizeModifier(timing_std=0.04, velocity_std=8.0),
            MetricAccentModifier(strength=0.35)
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
        str(out_dir / "LoFi_Masterpiece.mid"),
        bpm=82,
        instruments=instruments_map,
    )

    print()
    print("  SUCCESS! Lo-Fi Masterpiece exported to:")
    print(f"  {out_dir / 'LoFi_Masterpiece.mid'}")
    print("================================================================================")


if __name__ == "__main__":
    main()
