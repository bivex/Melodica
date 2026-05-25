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
from melodica.generators import (
    MelodyGenerator, AmbientPadGenerator, CountermelodyGenerator,
)
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.fills import FillGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi


def main():
    print("================================================================================")
    print("  B E A T   A R R A N G E M E N T   v2 — Dynamic 10-Part Structure")
    print("================================================================================")

    out_dir = Path("output/demo_beat_arrangement")
    out_dir.mkdir(exist_ok=True, parents=True)

    scale = Scale(2, Mode.NATURAL_MINOR)

    # ---------------------------------------------------------------------------
    # Tracks — wider palette for contrast
    # ---------------------------------------------------------------------------
    tracks = [
        # -- Core --
        TrackConfig(
            name="Dark_Pad",
            generator=DarkPadGenerator(mode="minor_pad", register="low"),
            instrument="dark_pad", density=0.4, octave_shift=-1,
        ),
        TrackConfig(
            name="Sub_808",
            generator=Bass808SlidingGenerator(pattern="trap_basic", slide_probability=0.4),
            instrument="synth_bass", density=0.6, octave_shift=-2,
        ),
        TrackConfig(
            name="Trap_Drums",
            generator=TrapDrumsGenerator(hat_roll_density=0.7, ghost_snare_prob=0.3),
            instrument="drums", density=0.8,
        ),
        TrackConfig(
            name="Lead_Synth",
            generator=LeadSynthGenerator(style="trance", portamento=0.15, note_length="legato"),
            instrument="synth_lead", density=0.6, octave_shift=1,
        ),
        TrackConfig(
            name="Vocal_Chops",
            generator=VocalChopsGenerator(density=0.6, chop_pattern="syncopated"),
            instrument="synth_voice", density=0.5,
        ),
        # -- Accent --
        TrackConfig(
            name="Brass_Hits",
            generator=BrassSectionGenerator(articulation="hit", intensity=0.9),
            instrument="brass", density=0.3,
        ),
        # -- FX --
        TrackConfig(
            name="FX_Riser",
            generator=FXRiserGenerator(riser_type="synth", length_beats=8.0),
            instrument="synth_fx", density=0.3,
        ),
        TrackConfig(
            name="FX_Impact",
            generator=FXImpactGenerator(impact_type="boom", tail_length=2.0),
            instrument="synth_fx", density=0.2,
        ),
        # -- Counter --
        TrackConfig(
            name="Counter_Lead",
            generator=CountermelodyGenerator(interval_limit=7),
            instrument="synth_lead", density=0.4,
        ),
        TrackConfig(
            name="HiHat_Stutter",
            generator=HiHatStutterGenerator(pattern="trap_eighth", roll_density=0.5),
            instrument="drums", density=0.4,
        ),
    ]

    # ---------------------------------------------------------------------------
    # 10-Part Arrangement
    #
    # Themes:  A = dark intro motif
    #          B = main verse melody
    #          C = hook anthem
    #          D = bridge/rift material
    #          E = breakdown ambient
    #
    # Energy curve:  _/¯¯\_/¯\__
    # ---------------------------------------------------------------------------
    parts = [
        # === 1. Intro (8 bars) — sparse, dark, atmospheric ===
        # Only pad + sub drone. Stutter hi-hat teases rhythm.
        IdeaPart(
            name="Intro",
            bars=8,
            scale=scale,
            tempo=78,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Dark_Pad":      structure_to_schedule("A", 8),
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

        # === 2. Build (4 bars) — tension rising toward verse ===
        # Riser starts, drums filter in, no melody yet.
        IdeaPart(
            name="Build",
            bars=4,
            scale=scale,
            tempo=80,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Dark_Pad":      structure_to_schedule("A", 4),
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
        # Lead plays B theme (8 bars), rests 4, then variation.
        # Vocal chops echo in gaps.
        IdeaPart(
            name="Verse",
            bars=16,
            scale=scale,
            tempo=85,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Dark_Pad":      structure_to_schedule("A", 16),
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
        # Riser + brass build tension. Lead plays ascending variation.
        # Drums drop to half-time feel (rest 2 bars, then fill).
        IdeaPart(
            name="PreHook",
            bars=4,
            scale=scale,
            tempo=88,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Dark_Pad":      structure_to_schedule("A", 4),
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
        # Everything plays. New anthem theme C. Impact hits on bar 1.
        IdeaPart(
            name="Hook",
            bars=8,
            scale=scale,
            tempo=92,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Dark_Pad":      structure_to_schedule("A", 8),
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
        # Only pad + 808 + vocal chops. Drums gone.
        # New ambient theme E. Feels like breathing room.
        IdeaPart(
            name="Breakdown",
            bars=8,
            scale=scale,
            tempo=78,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Dark_Pad":      structure_to_schedule("E", 8),
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
        # Drums return. Lead plays retrograde of B for freshness.
        # Counter enters on B theme. Vocal chops fill gaps.
        IdeaPart(
            name="Verse2",
            bars=12,
            scale=scale,
            tempo=85,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Dark_Pad":      structure_to_schedule("A", 12),
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

        # === 8. Bridge (8 bars) — new material, mode shift feel ===
        # Theme D — completely new melody. 808 pattern changes.
        # Lead plays D, counter plays D retrograde inversion.
        IdeaPart(
            name="Bridge",
            bars=8,
            scale=scale,
            tempo=82,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Dark_Pad":      structure_to_schedule("D", 8),
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

        # === 9. Hook 2 (8 bars) — second peak, bigger ===
        # Same C theme (Letter Rule!) but with brass accents + stutter.
        # Impact on bar 1 for maximum drop energy.
        IdeaPart(
            name="Hook2",
            bars=8,
            scale=scale,
            tempo=92,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Dark_Pad":      structure_to_schedule("A", 8),
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
        # Return to A theme (callback to intro). Pad fades.
        # Drums gone. Last breath.
        IdeaPart(
            name="Outro",
            bars=8,
            scale=scale,
            tempo=75,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Dark_Pad":      structure_to_schedule("A R", 4),
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

    config = IdeaToolConfig(
        style="hip_hop_trap",
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
        use_harmonic_verifier=True,
    )

    notes_dict = IdeaTool(config).generate()

    # ---------------------------------------------------------------------------
    # Post-processing — humanize + velocity curves per track
    # ---------------------------------------------------------------------------
    print("  Applying Expression Pipeline...")
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
        "Lead_Synth":    ([HumanizeModifier(timing_std=0.02, velocity_std=8.0)], "Humanize"),
        "Sub_808":       ([HumanizeModifier(timing_std=0.03, velocity_std=10.0)], "Humanize"),
        "Trap_Drums":    ([HumanizeModifier(timing_std=0.01, velocity_std=5.0),
                          MetricAccentModifier()], "Humanize + Metric Accent"),
        "Vocal_Chops":   ([HumanizeModifier(timing_std=0.015, velocity_std=6.0)], "Humanize"),
        "Dark_Pad":      ([HumanizeModifier(timing_std=0.005, velocity_std=2.0)], "Humanize"),
        "Counter_Lead":  ([HumanizeModifier(timing_std=0.02, velocity_std=7.0)], "Humanize"),
        "Brass_Hits":    ([HumanizeModifier(timing_std=0.005, velocity_std=3.0)], "Humanize"),
        "HiHat_Stutter": ([HumanizeModifier(timing_std=0.008, velocity_std=4.0)], "Humanize"),
    }

    for name, (modifiers, desc) in pipelines.items():
        if name in notes_dict:
            p = ModifierPipeline(base_notes=notes_dict[name])
            for mod in modifiers:
                p.add_modifier(mod)
            notes_dict[name] = p.process(mod_context)
            print(f"  > {name}: {desc}")

    # ---------------------------------------------------------------------------
    # Export
    # ---------------------------------------------------------------------------
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
    print("  Tracks: 10 — pad, 808, drums, lead, vocal chops, brass,")
    print("          riser, impact, counter, hihat stutter")
    print()
    print("  Energy curve: _/¯¯\\_/¯\\__")
    print("    Intro _ | Build / | Verse ¯ | PreHook / | Hook ¯¯")
    print("    Breakdown _ | Verse2 / | Bridge ~ | Hook2 ¯¯ | Outro __")
    print("================================================================================")


if __name__ == "__main__":
    main()
