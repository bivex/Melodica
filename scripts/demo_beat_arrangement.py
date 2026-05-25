# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/demo_beat_arrangement.py — Beat Arrangement Masterclass

Classic hip-hop/pop structure: Intro → Verse → Hook → Verse 2 → Hook 2 → Outro.
Uses RC-style notation for phrase management across parts.

Key concepts:
  A = verse material, B = hook material, R = rest
  Letter Rule: same letter = same phrase across parts
  Transforms: :var, :retro for development without new material
"""

from pathlib import Path

from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.generators import (
    MelodyGenerator, SynthBassGenerator, AmbientPadGenerator,
    LeadSynthGenerator, CountermelodyGenerator,
)
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi


def main():
    print("================================================================================")
    print("  B E A T   A R R A N G E M E N T — Classic Structure")
    print("  Intro → Verse → Hook → Verse 2 → Hook 2 → Outro")
    print("================================================================================")

    out_dir = Path("output/demo_beat_arrangement")
    out_dir.mkdir(exist_ok=True, parents=True)

    scale = Scale(2, Mode.NATURAL_MINOR)

    # ---------------------------------------------------------------------------
    # Tracks
    # ---------------------------------------------------------------------------
    tracks = [
        TrackConfig(
            name="Ambient_Pad",
            generator=AmbientPadGenerator(voicing="spread"),
            instrument="dark_pad", density=0.4, octave_shift=-1,
        ),
        TrackConfig(
            name="Synth_Bass",
            generator=SynthBassGenerator(pattern="acid_line", slide_probability=0.3),
            instrument="synth_bass", density=0.6, octave_shift=-2,
        ),
        TrackConfig(
            name="Trap_Drums",
            generator=TrapDrumsGenerator(hat_roll_density=0.7),
            instrument="drums", density=0.8,
        ),
        TrackConfig(
            name="Lead_Melody",
            generator=MelodyGenerator(motif_probability=0.7),
            instrument="synth_lead", density=0.6, octave_shift=1,
        ),
        TrackConfig(
            name="Synth_Counter",
            generator=CountermelodyGenerator(interval_limit=7),
            instrument="synth_lead", density=0.5,
        ),
    ]

    # ---------------------------------------------------------------------------
    # Arrangement — A = verse, B = hook, R = rest
    # ---------------------------------------------------------------------------
    parts = [
        # Intro (8 bars) — sparse: pad + bass drone, no drums
        IdeaPart(
            name="Intro",
            bars=8,
            scale=scale,
            tempo=85,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":   structure_to_schedule("A", 8),
                "Synth_Bass":    structure_to_schedule("A", 8),
                "Trap_Drums":    structure_to_schedule("R", 8),
                "Lead_Melody":   structure_to_schedule("R", 8),
                "Synth_Counter": structure_to_schedule("R", 8),
            },
        ),

        # Verse (16 bars) — drums enter, lead plays theme A
        IdeaPart(
            name="Verse",
            bars=16,
            scale=scale,
            tempo=85,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":   structure_to_schedule("A", 16),
                "Synth_Bass":    structure_to_schedule("A", 16),
                "Trap_Drums":    structure_to_schedule("A", 16),
                "Lead_Melody":   structure_to_schedule("A R", 8),
                "Synth_Counter": structure_to_schedule("R", 16),
            },
        ),

        # Hook (8 bars) — full energy, new theme B
        IdeaPart(
            name="Hook",
            bars=8,
            scale=scale,
            tempo=90,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":   structure_to_schedule("A", 8),
                "Synth_Bass":    structure_to_schedule("B", 8),
                "Trap_Drums":    structure_to_schedule("B", 8),
                "Lead_Melody":   structure_to_schedule("B", 8),
                "Synth_Counter": structure_to_schedule("B:var", 8),
            },
        ),

        # Verse 2 (16 bars) — development: counter enters, lead varies
        IdeaPart(
            name="Verse2",
            bars=16,
            scale=scale,
            tempo=85,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":   structure_to_schedule("A", 16),
                "Synth_Bass":    structure_to_schedule("A", 16),
                "Trap_Drums":    structure_to_schedule("A", 16),
                "Lead_Melody":   structure_to_schedule("R A:var", 8),
                "Synth_Counter": structure_to_schedule("A", 16),
            },
        ),

        # Hook 2 (8 bars) — same hook B, retro counter
        IdeaPart(
            name="Hook2",
            bars=8,
            scale=scale,
            tempo=90,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":   structure_to_schedule("A", 8),
                "Synth_Bass":    structure_to_schedule("B", 8),
                "Trap_Drums":    structure_to_schedule("B", 8),
                "Lead_Melody":   structure_to_schedule("B", 8),
                "Synth_Counter": structure_to_schedule("B:retro", 8),
            },
        ),

        # Outro (8 bars) — fade out, return to theme A
        IdeaPart(
            name="Outro",
            bars=8,
            scale=scale,
            tempo=80,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Ambient_Pad":   structure_to_schedule("A R", 4),
                "Synth_Bass":    structure_to_schedule("A R", 4),
                "Trap_Drums":    structure_to_schedule("R", 8),
                "Lead_Melody":   structure_to_schedule("A R", 4),
                "Synth_Counter": structure_to_schedule("R", 8),
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
    # Post-processing — humanize all tracks
    # ---------------------------------------------------------------------------
    print("  Applying Humanize Pipeline...")
    from melodica.modifiers import (
        ModifierPipeline, ModifierContext, HumanizeModifier,
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

    humanize_params = {
        "Lead_Melody":   (0.02, 8.0),
        "Synth_Bass":    (0.03, 12.0),
        "Synth_Counter": (0.02, 6.0),
        "Ambient_Pad":   (0.005, 2.0),
        "Trap_Drums":    (0.01, 5.0),
    }

    for name, (timing_std, vel_std) in humanize_params.items():
        if name in notes_dict:
            p = ModifierPipeline(base_notes=notes_dict[name])
            p.add_modifier(HumanizeModifier(timing_std=timing_std, velocity_std=vel_std))
            notes_dict[name] = p.process(mod_context)
            print(f"  > {name}: Humanize")

    # ---------------------------------------------------------------------------
    # Export
    # ---------------------------------------------------------------------------
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
    instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks}

    export_multitrack_midi(
        tracks_data,
        str(out_dir / "Beat_Arrangement.mid"),
        bpm=85,
        instruments=instruments_map,
    )

    print()
    print("================================================================================")
    print(f"  SUCCESS! Beat arrangement exported to:")
    print(f"  {out_dir / 'Beat_Arrangement.mid'}")
    print()
    print("  Structure:  Intro(8) → Verse(16) → Hook(8) → Verse2(16) → Hook2(8) → Outro(8)")
    print("  Total:      64 bars")
    print()
    print("  RC features used:")
    print("    - Letter Rule:   Hook B == Hook2 B (identical)")
    print("    - Development:   Verse2 lead uses A:var (not raw A)")
    print("    - Contrast:      Hook2 counter uses B:retro")
    print("    - Crescendo:     Intro empty → Verse +drums → Hook +all")
    print("================================================================================")


if __name__ == "__main__":
    main()
