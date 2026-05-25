# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/demo_dramatic_epic.py — Dramatic Cinematic Trap Generator.

Features:
1. Orchestral + Hybrid Trap arrangement.
2. Coupled HMM for emotional, minor-key harmonic tension.
3. Dramatic macro-dynamics: Crescendos, Swells, and Silent Drops.
4. Rich layering: Cinematic Strings, Dark Pads, Heavy 808s, and Piano.
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.generators.melody import MelodyGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi


def _build_tracks():
    # Rhythms for drama
    dramatic_piano = get_rhythm("downtempo_piano_stabs")
    lead_rhythm = get_rhythm("markov:ballad", syncopation=0.1, phrase_length=16)

    return [
        # 1. Foundation: Deep Orchestral Strings
        TrackConfig(
            name="Epic_Strings",
            generator=StringsEnsembleGenerator(
                section_size="full",
                divisi=4,
                articulation="sustained"
            ),
            instrument="strings",
            density=0.8,
            octave_shift=-1
        ),

        # 2. Emotional Core: Cinematic Piano
        TrackConfig(
            name="Drama_Piano",
            generator=MelodyGenerator(
                mode="chord_tones",
                rhythm=dramatic_piano,
                climax="none"
            ),
            instrument="bright_piano",
            density=0.6,
            octave_shift=0
        ),
        
        # 3. Heavy Impact: Dark Bass / 808
        TrackConfig(
            name="Power_808",
            generator=Bass808SlidingGenerator(
                pattern="half_time",
                slide_probability=0.3,
                accent_velocity=1.25
            ),
            instrument="synth_bass",
            density=0.7,
            octave_shift=-2
        ),

        # 4. Driving Force: Hybrid Trap Drums
        TrackConfig(
            name="Impact_Drums",
            generator=TrapDrumsGenerator(
                hat_roll_density=0.5,
                ghost_snare_prob=0.2,
                kick_pattern="heavy"
            ),
            instrument="drums",
            density=1.0,
        ),
        
        # 5. Emotional Lead: Cello / Solo String
        TrackConfig(
            name="Cello_Lead",
            generator=MelodyGenerator(
                mode="downbeat_chord",
                rhythm=lead_rhythm,
                climax="auto",
                ornament_probability=0.2
            ),
            instrument="cello",
            density=0.5,
            octave_shift=0
        ),

        # 6. Atmospheric Nebula (High tension)
        TrackConfig(
            name="Tension_Nebula",
            generator=NebulaGenerator(
                variant="swell", 
                density_notes=6, 
                pitch_spread=18,
                use_scale_tones=False
            ),
            instrument="dark_pad",
            density=0.4,
            octave_shift=1
        ),

        # 7. Cinematic FX
        TrackConfig(
            name="Cinematic_Riser",
            generator=FXRiserGenerator(riser_type="orchestral", length_beats=16.0),
            instrument="synth_fx",
            density=0.2,
        ),
        TrackConfig(
            name="Power_Impact",
            generator=FXImpactGenerator(impact_type="heavy_drum", tail_length=4.0),
            instrument="percussion",
            density=0.2,
        ),
    ]


def _build_parts(scale):
    return [
        # 1. Darkness (8 bars) — Sparse Strings & Piano
        IdeaPart(
            name="Darkness", bars=8, scale=scale, tempo=72,
            progression_type="coupled_hmm",
            style="cinematic",
            track_phrase_schedules={
                "Epic_Strings":   structure_to_schedule("A", 8),
                "Drama_Piano":    structure_to_schedule("A R", 4),
                "Power_808":      structure_to_schedule("R", 8),
                "Impact_Drums":   structure_to_schedule("R", 8),
                "Cello_Lead":     structure_to_schedule("R", 8),
                "Tension_Nebula": structure_to_schedule("A", 8),
                "Cinematic_Riser":structure_to_schedule("R", 8),
                "Power_Impact":   structure_to_schedule("A R", 4),
            },
        ),

        # 2. Preparation (8 bars) — Tension builds
        IdeaPart(
            name="Build", bars=8, scale=scale, tempo=74,
            progression_type="coupled_hmm",
            style="cinematic",
            track_phrase_schedules={
                "Epic_Strings":   structure_to_schedule("A", 8),
                "Drama_Piano":    structure_to_schedule("A", 8),
                "Power_808":      structure_to_schedule("A", 8),
                "Impact_Drums":   structure_to_schedule("R A", 4),
                "Cello_Lead":     structure_to_schedule("R", 8),
                "Tension_Nebula": structure_to_schedule("A:var", 8),
                "Cinematic_Riser":structure_to_schedule("R A", 4),
                "Power_Impact":   structure_to_schedule("R", 8),
            },
        ),

        # 3. The Drop (16 bars) — Full Impact
        IdeaPart(
            name="Climax", bars=16, scale=scale, tempo=76,
            progression_type="coupled_hmm",
            style="cinematic",
            track_phrase_schedules={
                "Epic_Strings":   structure_to_schedule("B", 16),
                "Drama_Piano":    structure_to_schedule("B", 16),
                "Power_808":      structure_to_schedule("B", 16),
                "Impact_Drums":   structure_to_schedule("B", 16),
                "Cello_Lead":     structure_to_schedule("A", 16),
                "Tension_Nebula": structure_to_schedule("B", 16),
                "Cinematic_Riser":structure_to_schedule("R", 16),
                "Power_Impact":   structure_to_schedule("B R", 8),
            },
        ),

        # 4. Hollow (8 bars) — Dramatic silence / Breakdown
        IdeaPart(
            name="Hollow", bars=8, scale=scale, tempo=68,
            progression_type="coupled_hmm",
            style="cinematic",
            track_phrase_schedules={
                "Epic_Strings":   structure_to_schedule("A:var", 8),
                "Drama_Piano":    structure_to_schedule("R A", 4),
                "Power_808":      structure_to_schedule("R", 8),
                "Impact_Drums":   structure_to_schedule("R", 8),
                "Cello_Lead":     structure_to_schedule("R", 8),
                "Tension_Nebula": structure_to_schedule("R", 8),
                "Cinematic_Riser":structure_to_schedule("R", 8),
                "Power_Impact":   structure_to_schedule("R", 8),
            },
        ),

        # 5. Final Stand (12 bars) — Rebuild to max intensity
        IdeaPart(
            name="Finale", bars=12, scale=scale, tempo=78,
            progression_type="coupled_hmm",
            style="cinematic",
            track_phrase_schedules={
                "Epic_Strings":   structure_to_schedule("B:var", 12),
                "Drama_Piano":    structure_to_schedule("B:var", 12),
                "Power_808":      structure_to_schedule("C", 12),
                "Impact_Drums":   structure_to_schedule("C", 12),
                "Cello_Lead":     structure_to_schedule("A:var", 12),
                "Tension_Nebula": structure_to_schedule("B:var", 12),
                "Cinematic_Riser":structure_to_schedule("R B", 6),
                "Power_Impact":   structure_to_schedule("C R", 6),
            },
        ),

        # 6. Fade (8 bars)
        IdeaPart(
            name="Fade", bars=8, scale=scale, tempo=70,
            progression_type="coupled_hmm",
            style="cinematic",
            track_phrase_schedules={
                "Epic_Strings":   structure_to_schedule("A", 8),
                "Drama_Piano":    structure_to_schedule("R", 8),
                "Power_808":      structure_to_schedule("R", 8),
                "Impact_Drums":   structure_to_schedule("R", 8),
                "Cello_Lead":     structure_to_schedule("R", 8),
                "Tension_Nebula": structure_to_schedule("R", 8),
                "Cinematic_Riser":structure_to_schedule("R", 8),
                "Power_Impact":   structure_to_schedule("R", 8),
            },
        ),
    ]


def main():
    print("================================================================================")
    print("  D R A M A T I C   E P I C   B E A T   G E N E R A T O R")
    print("================================================================================")

    out_dir = Path("output/demo_dramatic_epic")
    out_dir.mkdir(exist_ok=True, parents=True)

    # A Minor (Aeolian) — Standard dramatic minor
    scale = Scale(9, Mode.NATURAL_MINOR)
    
    tracks = _build_tracks()
    parts = _build_parts(scale)

    print("  Orchestrating high-tension arrangement...")
    config = IdeaToolConfig(
        style="cinematic",
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
        use_harmonic_verifier=True,
        use_tension_curve=True
    )
    
    notes_dict = IdeaTool(config).generate()

    # Print chords for analysis
    print("\n  [ANALYSIS] Dramatic Chord Progression:")
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

    print("  Sculpting Macro-Dynamics & Humanization...")
    pipelines = {
        "Cello_Lead": [
            HumanizeModifier(timing_std=0.04, velocity_std=15.0),
            VelocityCurveModifier(start_vel=40, end_vel=100, curve="swell"),
            MetricAccentModifier(strength=0.2)
        ],
        "Drama_Piano": [
            HumanizeModifier(timing_std=0.02, velocity_std=10.0),
            VelocityCurveModifier(start_vel=50, end_vel=85, curve="linear"),
        ],
        "Epic_Strings": [
            HumanizeModifier(timing_std=0.01, velocity_std=5.0),
            VelocityCurveModifier(start_vel=30, end_vel=75, curve="exponential"),
        ],
        "Power_808": [
            HumanizeModifier(timing_std=0.03, velocity_std=8.0),
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
        str(out_dir / "Dramatic_Epic_Beat.mid"),
        bpm=75,
        instruments=instruments_map,
    )

    print()
    print("  SUCCESS! Dramatic Masterpiece exported to:")
    print(f"  {out_dir / 'Dramatic_Epic_Beat.mid'}")
    print("================================================================================")


if __name__ == "__main__":
    main()
