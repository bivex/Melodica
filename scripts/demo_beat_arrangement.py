# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/demo_beat_arrangement.py — Dynamic Beat Arrangement v2

10-part structure with real energy dynamics:
  Intro → Build → Verse → Pre-Hook → Hook → Breakdown →
  Verse2 → Bridge → Hook2 → Outro

Key improvements over v1:
  - More themes (A-E) = more variety
  - FX tracks: risers, impacts, fills for transitions
  - Energy curve: sparse → dense → peak → breakdown → rebuild → peak → fade
  - Density varies per section (not one-size-fits-all)
  - Tempo shifts between sections for push/pull feel
  - Transitional parts (Build, Pre-Hook, Breakdown)
"""

from pathlib import Path

from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.generators import CountermelodyGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.rhythm import get_rhythm, ProbabilisticRhythmGenerator, MarkovRhythmGenerator
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi


def _build_tracks():
    lead_rhythm = get_rhythm("markov:syncopated")
    vocal_rhythm = get_rhythm("probabilistic:dense")
    counter_rhythm = get_rhythm("markov:swing")

    return [
        TrackConfig(name="Ambient_Pad", generator=NebulaGenerator(variant="swell", density_notes=6), instrument="dark_pad", density=0.4, octave_shift=-1),
        TrackConfig(name="Sub_808", generator=Bass808SlidingGenerator(pattern="trap_basic", slide_probability=0.4), instrument="synth_bass", density=0.6, octave_shift=-2),
        TrackConfig(name="Trap_Drums", generator=TrapDrumsGenerator(hat_roll_density=0.7, ghost_snare_prob=0.3), instrument="drums", density=0.8),
        TrackConfig(name="Lead_Synth", generator=LeadSynthGenerator(style="trance", portamento=0.15, note_length="mixed", rhythm=lead_rhythm), instrument="synth_lead", density=0.6, octave_shift=1),
        TrackConfig(name="Vocal_Chops", generator=VocalChopsGenerator(density=0.6, chop_pattern="syncopated", rhythm=vocal_rhythm), instrument="synth_voice", density=0.5),
        TrackConfig(name="Brass_Hits", generator=BrassSectionGenerator(articulation="hit", intensity=0.9), instrument="brass", density=0.3, follow_rhythm_track="Lead_Synth"),
        TrackConfig(name="FX_Riser", generator=FXRiserGenerator(riser_type="synth", length_beats=8.0), instrument="synth_fx", density=0.3),
        TrackConfig(name="FX_Impact", generator=FXImpactGenerator(impact_type="boom", tail_length=2.0), instrument="synth_fx", density=0.2),
        TrackConfig(name="Counter_Lead", generator=CountermelodyGenerator(interval_limit=7, rhythm=counter_rhythm), instrument="synth_lead", density=0.4),
        TrackConfig(name="HiHat_Stutter", generator=HiHatStutterGenerator(pattern="trap_eighth", roll_density=0.5), instrument="drums", density=0.4),
    ]


def _build_parts(scale):
    return [
        # === 1. Intro (8 bars) — sparse, dark, atmospheric ===
        IdeaPart(
            name="Intro", bars=8, scale=scale, tempo=78,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":      structure_to_schedule("A", 8),
                "Sub_808":       structure_to_schedule("A", 8),
                "Trap_Drums":    structure_to_schedule("R", 8),
                "Lead_Synth":    structure_to_schedule("R", 8),
                "Vocal_Chops":   structure_to_schedule("R", 8),
                "Brass_Hits":    structure_to_schedule("R", 8),
                "FX_Riser":      structure_to_schedule("R", 8),
                "FX_Impact":     structure_to_schedule("R", 8),
                "Counter_Lead":  structure_to_schedule("R", 8),
                "HiHat_Stutter": structure_to_schedule("A R", 4),
            },
        ),

        # === 2. Build (4 bars) — tension rising ===
        IdeaPart(
            name="Build", bars=4, scale=scale, tempo=80,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":      structure_to_schedule("A", 4),
                "Sub_808":       structure_to_schedule("A", 4),
                "Trap_Drums":    structure_to_schedule("B", 4),
                "Lead_Synth":    structure_to_schedule("R", 4),
                "Vocal_Chops":   structure_to_schedule("R", 4),
                "Brass_Hits":    structure_to_schedule("R", 4),
                "FX_Riser":      structure_to_schedule("B", 4),
                "FX_Impact":     structure_to_schedule("R", 4),
                "Counter_Lead":  structure_to_schedule("R", 4),
                "HiHat_Stutter": structure_to_schedule("B", 4),
            },
        ),

        # === 3. Verse (16 bars) — full beat, lead enters ===
        IdeaPart(
            name="Verse", bars=16, scale=scale, tempo=85,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":      structure_to_schedule("A", 16),
                "Sub_808":       structure_to_schedule("B", 16),
                "Trap_Drums":    structure_to_schedule("B", 16),
                "Lead_Synth":    structure_to_schedule("B R B:var", 4, loop=False),
                "Vocal_Chops":   structure_to_schedule("R B:var", 8),
                "Brass_Hits":    structure_to_schedule("R", 16),
                "FX_Riser":      structure_to_schedule("R", 16),
                "FX_Impact":     structure_to_schedule("R", 16),
                "Counter_Lead":  structure_to_schedule("R", 16),
                "HiHat_Stutter": structure_to_schedule("R", 16),
            },
        ),

        # === 4. Pre-Hook (4 bars) — energy push ===
        IdeaPart(
            name="PreHook", bars=4, scale=scale, tempo=88,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":      structure_to_schedule("A", 4),
                "Sub_808":       structure_to_schedule("C", 4),
                "Trap_Drums":    structure_to_schedule("R B", 2),
                "Lead_Synth":    structure_to_schedule("C:fast", 4),
                "Vocal_Chops":   structure_to_schedule("C:var", 4),
                "Brass_Hits":    structure_to_schedule("C", 4),
                "FX_Riser":      structure_to_schedule("C", 4),
                "FX_Impact":     structure_to_schedule("R", 4),
                "Counter_Lead":  structure_to_schedule("R", 4),
                "HiHat_Stutter": structure_to_schedule("C", 4),
            },
        ),

        # === 5. Hook (8 bars) — PEAK ENERGY ===
        IdeaPart(
            name="Hook", bars=8, scale=scale, tempo=92,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":      structure_to_schedule("A", 8),
                "Sub_808":       structure_to_schedule("C", 8),
                "Trap_Drums":    structure_to_schedule("C", 8),
                "Lead_Synth":    structure_to_schedule("C", 8),
                "Vocal_Chops":   structure_to_schedule("C", 8),
                "Brass_Hits":    structure_to_schedule("C R", 4),
                "FX_Riser":      structure_to_schedule("R", 8),
                "FX_Impact":     structure_to_schedule("C R", 4),
                "Counter_Lead":  structure_to_schedule("C:var", 8),
                "HiHat_Stutter": structure_to_schedule("C", 8),
            },
        ),

        # === 6. Breakdown (8 bars) — drop to ambient ===
        IdeaPart(
            name="Breakdown", bars=8, scale=scale, tempo=78,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":      structure_to_schedule("E", 8),
                "Sub_808":       structure_to_schedule("A R", 4),
                "Trap_Drums":    structure_to_schedule("R", 8),
                "Lead_Synth":    structure_to_schedule("E", 8),
                "Vocal_Chops":   structure_to_schedule("E:var", 8),
                "Brass_Hits":    structure_to_schedule("R", 8),
                "FX_Riser":      structure_to_schedule("R", 8),
                "FX_Impact":     structure_to_schedule("R", 8),
                "Counter_Lead":  structure_to_schedule("R", 8),
                "HiHat_Stutter": structure_to_schedule("R", 8),
            },
        ),

        # === 7. Verse 2 (12 bars) — rebuild ===
        IdeaPart(
            name="Verse2", bars=12, scale=scale, tempo=85,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":      structure_to_schedule("A", 12),
                "Sub_808":       structure_to_schedule("B", 12),
                "Trap_Drums":    structure_to_schedule("B", 12),
                "Lead_Synth":    structure_to_schedule("B:retro R", 4, loop=False),
                "Vocal_Chops":   structure_to_schedule("R B:inv", 4),
                "Brass_Hits":    structure_to_schedule("R", 12),
                "FX_Riser":      structure_to_schedule("R", 12),
                "FX_Impact":     structure_to_schedule("R", 12),
                "Counter_Lead":  structure_to_schedule("B:var", 12),
                "HiHat_Stutter": structure_to_schedule("R", 12),
            },
        ),

        # === 8. Bridge (8 bars) — new material ===
        IdeaPart(
            name="Bridge", bars=8, scale=scale, tempo=82,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":      structure_to_schedule("D", 8),
                "Sub_808":       structure_to_schedule("D", 8),
                "Trap_Drums":    structure_to_schedule("D", 8),
                "Lead_Synth":    structure_to_schedule("D", 8),
                "Vocal_Chops":   structure_to_schedule("D:var", 8),
                "Brass_Hits":    structure_to_schedule("D R", 4),
                "FX_Riser":      structure_to_schedule("D", 8),
                "FX_Impact":     structure_to_schedule("R", 8),
                "Counter_Lead":  structure_to_schedule("D:retro", 8),
                "HiHat_Stutter": structure_to_schedule("D", 8),
            },
        ),

        # === 9. Hook 2 (8 bars) — second peak ===
        IdeaPart(
            name="Hook2", bars=8, scale=scale, tempo=92,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":      structure_to_schedule("A", 8),
                "Sub_808":       structure_to_schedule("C", 8),
                "Trap_Drums":    structure_to_schedule("C", 8),
                "Lead_Synth":    structure_to_schedule("C", 8),
                "Vocal_Chops":   structure_to_schedule("C", 8),
                "Brass_Hits":    structure_to_schedule("C", 8),
                "FX_Riser":      structure_to_schedule("R", 8),
                "FX_Impact":     structure_to_schedule("C R", 4),
                "Counter_Lead":  structure_to_schedule("C:retro", 8),
                "HiHat_Stutter": structure_to_schedule("C", 8),
            },
        ),

        # === 10. Outro (8 bars) — decompress ===
        IdeaPart(
            name="Outro", bars=8, scale=scale, tempo=75,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":      structure_to_schedule("A R", 4),
                "Sub_808":       structure_to_schedule("A R", 4),
                "Trap_Drums":    structure_to_schedule("R", 8),
                "Lead_Synth":    structure_to_schedule("A R", 4),
                "Vocal_Chops":   structure_to_schedule("R A:var", 4, loop=False),
                "Brass_Hits":    structure_to_schedule("R", 8),
                "FX_Riser":      structure_to_schedule("R", 8),
                "FX_Impact":     structure_to_schedule("R", 8),
                "Counter_Lead":  structure_to_schedule("R", 8),
                "HiHat_Stutter": structure_to_schedule("R", 8),
            },
        ),
    ]


def generate_notes():
    """Generate notes and return (notes_dict, tracks, parts, scale) for analysis."""
    scale = Scale(2, Mode.NATURAL_MINOR)
    tracks = _build_tracks()
    parts = _build_parts(scale)

    config = IdeaToolConfig(style="hip_hop_trap", parts=parts, tracks=tracks,
                            use_voice_leading=True, use_harmonic_verifier=True)
    notes_dict = IdeaTool(config).generate()
    return notes_dict, tracks, parts, scale


def _apply_post_processing(notes_dict, parts, scale):
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

    pipelines = {
        "Lead_Synth":    ([HumanizeModifier(timing_std=0.02, velocity_std=8.0),
                          VelocityCurveModifier(start_vel=50, end_vel=100, curve="crescendo"),
                          MetricAccentModifier(strength=0.25)],
                         "Humanize + Crescendo + Accent"),
        "Sub_808":       ([HumanizeModifier(timing_std=0.03, velocity_std=10.0),
                          MetricAccentModifier(strength=0.3)],
                         "Humanize + Accent"),
        "Trap_Drums":    ([HumanizeModifier(timing_std=0.01, velocity_std=5.0),
                          MetricAccentModifier(strength=0.35)],
                         "Humanize + Metric Accent"),
        "Vocal_Chops":   ([HumanizeModifier(timing_std=0.015, velocity_std=6.0),
                          VelocityCurveModifier(start_vel=40, end_vel=90, curve="swell")],
                         "Humanize + Swell"),
        "Ambient_Pad":   ([HumanizeModifier(timing_std=0.005, velocity_std=2.0),
                          VelocityCurveModifier(start_vel=30, end_vel=70, curve="linear")],
                         "Humanize + Fade"),
        "Counter_Lead":  ([HumanizeModifier(timing_std=0.02, velocity_std=7.0),
                          MetricAccentModifier(strength=0.2)],
                         "Humanize + Accent"),
        "Brass_Hits":    ([HumanizeModifier(timing_std=0.005, velocity_std=3.0),
                          MetricAccentModifier(strength=0.3)],
                         "Humanize + Accent"),
        "HiHat_Stutter": ([HumanizeModifier(timing_std=0.008, velocity_std=4.0),
                          VelocityCurveModifier(start_vel=45, end_vel=85, curve="exponential")],
                         "Humanize + Exp Curve"),
    }

    print("  Applying Expression Pipeline...")
    for name, (modifiers, desc) in pipelines.items():
        if name in notes_dict:
            p = ModifierPipeline(base_notes=notes_dict[name])
            for mod in modifiers:
                p.add_modifier(mod)
            notes_dict[name] = p.process(mod_context)
            print(f"  > {name}: {desc}")


def main():
    print("================================================================================")
    print("  B E A T   A R R A N G E M E N T   v2 — Dynamic 10-Part Structure")
    print("================================================================================")

    out_dir = Path("output/demo_beat_arrangement")
    out_dir.mkdir(exist_ok=True, parents=True)

    notes_dict, tracks, parts, scale = generate_notes()
    _apply_post_processing(notes_dict, parts, scale)

    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
    instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks}

    export_multitrack_midi(
        tracks_data,
        str(out_dir / "Beat_Arrangement_v2.mid"),
        bpm=85,
        instruments=instruments_map,
    )

    print()
    print("================================================================================")
    print(f"  SUCCESS! v2 exported to:")
    print(f"  {out_dir / 'Beat_Arrangement_v2.mid'}")
    print()
    print("  Structure (84 bars):")
    print("    Intro(8) → Build(4) → Verse(16) → PreHook(4) → Hook(8)")
    print("    → Breakdown(8) → Verse2(12) → Bridge(8) → Hook2(8) → Outro(8)")
    print()
    print("  Themes: A(intro) B(verse) C(hook) D(bridge) E(breakdown)")
    print("  Energy curve: _/¯¯\\_/¯\\__")
    print("================================================================================")


if __name__ == "__main__":
    main()
