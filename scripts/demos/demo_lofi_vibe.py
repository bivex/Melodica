# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/demo_lofi_vibe.py — Down-tempo Masterpiece.

A cinematic, slow-evolving atmospheric arrangement with:
- Deep Noir vibe (Muted Trumpet, Dark Drones)
- Cinematic layering (Nebula Clouds, Ghostly Vocals)
- Ultra-slow tempos (65-78 BPM)
- Sophisticated song structure with long evolutions
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
from melodica.generators.drone import DroneGenerator
from melodica.generators.wind_brass_solo import MutedTrumpetGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi


def _build_tracks():
    # Ultra-slow, breathing rhythms
    lead_rhythm = get_rhythm("markov:ballad", syncopation=0.15, phrase_length=12)
    vocal_rhythm = get_rhythm("probabilistic:sparse", density=0.25)
    groove_rhythm = get_rhythm("lofi_lazy_hats") # Using new JSON preset

    return [
        # Atmospheric Foundation: Continuous Drone
        TrackConfig(
            name="Dark_Drone",
            generator=DroneGenerator(variant="tonic", fade_in=4.0, fade_out=4.0),
            instrument="dark_pad",
            density=1.0,
            octave_shift=-1
        ),

        # Core Groove: Slow, heavy Lo-Fi
        TrackConfig(
            name="LoFi_Groove",
            generator=LoFiHipHopGenerator(
                variant="nostalgic",
                swing_ratio=0.66,
                chord_voicing="eleventh",
                vinyl_noise=0.6,
                tape_stop=0.15
            ),
            instrument="electric_piano",
            density=1.0,
        ),
        
        # Deep Sub Bass (breathing with the groove)
        TrackConfig(
            name="Sub_Bass",
            generator=Bass808SlidingGenerator(pattern="sub_only", slide_probability=0.3),
            instrument="synth_bass",
            density=0.6,
            octave_shift=-2
        ),

        # Evolving Nebula Clouds
        TrackConfig(
            name="Nebula_Clouds",
            generator=NebulaGenerator(
                variant="cloud", 
                density_notes=4, 
                pitch_spread=24,
                use_scale_tones=False,
                rhythm=get_rhythm("downtempo_piano_stabs")
            ),
            instrument="pad",
            density=0.35,
            octave_shift=0
        ),
        
        # Noir Lead: Muted Trumpet
        TrackConfig(
            name="Noir_Lead",
            generator=MutedTrumpetGenerator(
                plunger_wah=True,
                note_density=0.4
            ),
            instrument="trumpet",
            density=0.45,
            octave_shift=0
        ),

        # Ghostly Vocal Textures
        TrackConfig(
            name="Ghost_Vocals",
            generator=VocalChopsGenerator(
                density=0.3,
                chop_pattern="syncopated",
                rhythm=vocal_rhythm
            ),
            instrument="voice",
            density=0.35,
        ),

        # Cinematic FX
        TrackConfig(
            name="FX_Sweep",
            generator=FXRiserGenerator(riser_type="synth", length_beats=16.0),
            instrument="synth_fx",
            density=0.2,
        ),
        TrackConfig(
            name="FX_Vinyl",
            generator=FXImpactGenerator(impact_type="vinyl_static", tail_length=8.0),
            instrument="synth_fx",
            density=0.15,
        ),
    ]


def _build_parts(scale):
    # Progressions with 9ths ("девятки")
    prog_intro = ["im9 ivm9 VII9 IIImaj9"]
    prog_verse = ["im9 bVImaj9 iim7b5 V9", "im9 ivm9 bVII9 IIImaj9"]
    prog_hook  = ["im9 ivm9 V9 im9", "bVImaj9 bIImaj9 iim9 V9"]
    
    return [
        # 1. Opening (8 bars) — Sparse Drone & Vinyl
        IdeaPart(
            name="Opening", bars=8, scale=scale, tempo=68,
            progression_type="from_list",
            progression_list=prog_intro,
            track_phrase_schedules={
                "Dark_Drone":    structure_to_schedule("A", 8),
                "LoFi_Groove":   structure_to_schedule("R", 8),
                "Sub_Bass":      structure_to_schedule("R", 8),
                "Nebula_Clouds": structure_to_schedule("A", 8),
                "Noir_Lead":     structure_to_schedule("R", 8),
                "Ghost_Vocals":  structure_to_schedule("R", 8),
                "FX_Sweep":      structure_to_schedule("R", 8),
                "FX_Vinyl":      structure_to_schedule("A", 8),
            },
        ),

        # 2. Arrival (8 bars) — Groove enters
        IdeaPart(
            name="Arrival", bars=8, scale=scale, tempo=70,
            progression_type="from_list",
            progression_list=prog_intro,
            track_phrase_schedules={
                "Dark_Drone":    structure_to_schedule("A", 8),
                "LoFi_Groove":   structure_to_schedule("A", 8),
                "Sub_Bass":      structure_to_schedule("A", 8),
                "Nebula_Clouds": structure_to_schedule("A", 8),
                "Noir_Lead":     structure_to_schedule("R", 8),
                "Ghost_Vocals":  structure_to_schedule("A", 8),
                "FX_Sweep":      structure_to_schedule("R", 8),
                "FX_Vinyl":      structure_to_schedule("R", 8),
            },
        ),

        # 3. Verse 1 (16 bars)
        IdeaPart(
            name="Verse1", bars=16, scale=scale, tempo=72,
            progression_type="coupled_hmm", # Let the HMM decide
            track_phrase_schedules={
                "Dark_Drone":    structure_to_schedule("A", 16),
                "LoFi_Groove":   structure_to_schedule("A B", 8),
                "Sub_Bass":      structure_to_schedule("B", 16),
                "Nebula_Clouds": structure_to_schedule("B", 16),
                "Noir_Lead":     structure_to_schedule("R A", 8),
                "Ghost_Vocals":  structure_to_schedule("B", 16),
                "FX_Sweep":      structure_to_schedule("R", 16),
                "FX_Vinyl":      structure_to_schedule("R", 16),
            },
        ),

        # 4. Deep Vibe (12 bars) — Peak Atmosphere
        IdeaPart(
            name="DeepVibe", bars=12, scale=scale, tempo=74,
            progression_type="from_list",
            progression_list=prog_hook,
            track_phrase_schedules={
                "Dark_Drone":    structure_to_schedule("A", 12),
                "LoFi_Groove":   structure_to_schedule("C", 12),
                "Sub_Bass":      structure_to_schedule("C", 12),
                "Nebula_Clouds": structure_to_schedule("C", 12),
                "Noir_Lead":     structure_to_schedule("C", 12),
                "Ghost_Vocals":  structure_to_schedule("C", 12),
                "FX_Sweep":      structure_to_schedule("B", 12),
                "FX_Vinyl":      structure_to_schedule("C R", 6),
            },
        ),

        # 5. Submerged (8 bars) — Breakdown
        IdeaPart(
            name="Submerged", bars=8, scale=scale, tempo=65,
            progression_type="from_list",
            progression_list=prog_intro,
            track_phrase_schedules={
                "Dark_Drone":    structure_to_schedule("B", 8),
                "LoFi_Groove":   structure_to_schedule("D", 8),
                "Sub_Bass":      structure_to_schedule("R", 8),
                "Nebula_Clouds": structure_to_schedule("D", 8),
                "Noir_Lead":     structure_to_schedule("R", 8),
                "Ghost_Vocals":  structure_to_schedule("D", 8),
                "FX_Sweep":      structure_to_schedule("R", 8),
                "FX_Vinyl":      structure_to_schedule("R", 8),
            },
        ),

        # 6. Rebuild (12 bars)
        IdeaPart(
            name="Rebuild", bars=12, scale=scale, tempo=72,
            progression_type="from_list",
            progression_list=prog_verse,
            track_phrase_schedules={
                "Dark_Drone":    structure_to_schedule("A", 12),
                "LoFi_Groove":   structure_to_schedule("A:var", 12),
                "Sub_Bass":      structure_to_schedule("B:var", 12),
                "Nebula_Clouds": structure_to_schedule("A:var", 12),
                "Noir_Lead":     structure_to_schedule("B:var", 12),
                "Ghost_Vocals":  structure_to_schedule("R B:var", 6),
                "FX_Sweep":      structure_to_schedule("R B", 6),
                "FX_Vinyl":      structure_to_schedule("R", 12),
            },
        ),

        # 7. Climax (8 bars) — Peak Energy with 9ths
        IdeaPart(
            name="Climax", bars=8, scale=scale, tempo=78,
            progression_type="from_list",
            progression_list=prog_hook,
            track_phrase_schedules={
                "Dark_Drone":    structure_to_schedule("A", 8),
                "LoFi_Groove":   structure_to_schedule("C:var", 8),
                "Sub_Bass":      structure_to_schedule("C:var", 8),
                "Nebula_Clouds": structure_to_schedule("C:var", 8),
                "Noir_Lead":     structure_to_schedule("C:var", 8),
                "Ghost_Vocals":  structure_to_schedule("C:var", 8),
                "FX_Sweep":      structure_to_schedule("R", 8),
                "FX_Vinyl":      structure_to_schedule("A R", 4),
            },
        ),

        # 8. Dissolve (8 bars) — Fade Out
        IdeaPart(
            name="Dissolve", bars=8, scale=scale, tempo=68,
            progression_type="from_list",
            progression_list=prog_intro,
            track_phrase_schedules={
                "Dark_Drone":    structure_to_schedule("A", 8),
                "LoFi_Groove":   structure_to_schedule("D R", 4),
                "Sub_Bass":      structure_to_schedule("R", 8),
                "Nebula_Clouds": structure_to_schedule("A R", 4),
                "Noir_Lead":     structure_to_schedule("R", 8),
                "Ghost_Vocals":  structure_to_schedule("E", 8),
                "FX_Sweep":      structure_to_schedule("R", 8),
                "FX_Vinyl":      structure_to_schedule("R", 8),
            },
        ),
    ]


def main():
    print("================================================================================")
    print("  D O W N - T E M P O   M A S T E R P I E C E   (Cinematic Vibe)")
    print("================================================================================")

    out_dir = Path("output/demo_lofi_vibe")
    out_dir.mkdir(exist_ok=True, parents=True)

    # C# Minor (Aeolian) — Deep, dark, spacey
    scale = Scale(1, Mode.NATURAL_MINOR)
    
    tracks = _build_tracks()
    parts = _build_parts(scale)

    print("  Generating Pro-level Down-tempo arrangement...")
    config = IdeaToolConfig(
        style="lofi_hiphop",
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
        use_harmonic_verifier=True
    )
    
    notes_dict = IdeaTool(config).generate()

    # Print chords for analysis
    print("\n  [ANALYSIS] Generated Chord Progression:")
    chords = notes_dict.get("_chords", [])
    for c in chords:
        ext_str = f"+{c.extensions}" if c.extensions else ""
        deg_str = f"({c.degree_roman})" if hasattr(c, "degree_roman") else f"(deg:{c.degree})"
        print(f"    {c.start:5.1f}b | {c.quality.name:8} on {c.root:2} {deg_str:8} {ext_str}")
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

    print("  Applying Atmospheric Expression Pipeline...")
    pipelines = {
        "Noir_Lead": [
            HumanizeModifier(timing_std=0.045, velocity_std=12.0),
            VelocityCurveModifier(start_vel=40, end_vel=90, curve="swell"),
            MetricAccentModifier(strength=0.2)
        ],
        "Ghost_Vocals": [
            HumanizeModifier(timing_std=0.06, velocity_std=18.0),
            VelocityCurveModifier(start_vel=25, end_vel=70, curve="linear"),
        ],
        "Nebula_Clouds": [
            HumanizeModifier(timing_std=0.015, velocity_std=6.0),
            VelocityCurveModifier(start_vel=20, end_vel=55, curve="exponential"),
        ],
        "Sub_Bass": [
            HumanizeModifier(timing_std=0.05, velocity_std=10.0),
            MetricAccentModifier(strength=0.3)
        ],
        "Dark_Drone": [
            VelocityCurveModifier(start_vel=30, end_vel=50, curve="linear")
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
        str(out_dir / "Downtempo_Masterpiece.mid"),
        bpm=72,
        instruments=instruments_map,
    )

    print()
    print("  SUCCESS! Downtempo Masterpiece exported to:")
    print(f"  {out_dir / 'Downtempo_Masterpiece.mid'}")
    print("================================================================================")


if __name__ == "__main__":
    main()
