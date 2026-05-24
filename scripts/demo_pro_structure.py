# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/demo_pro_structure.py — PRO ARRANGEMENT MASTERCLASS v2
RC-style Structure Notation + Phrase Pool + Transform Suffixes.

Demonstrates professional arrangement architecture across a multi-part structure:
Intro -> Verse -> Chorus -> Climax -> Outro.

Leverages:
1. The Letter Rule: same letter = same deterministic seed = identical phrase content.
2. Motive Development: A' = variation of A, suffixes (_var, _inv, _fast).
3. Phrase Pool: phrases cached by label, reused across parts (Ghost Copy).
4. Coupled HMM progressions for organic transitions.
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.generators import (
    MelodyGenerator, BassGenerator, StringsEnsembleGenerator,
    AmbientPadGenerator, FluteGenerator,
    ChoirAahsGenerator,
)
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi


def main():
    print("================================================================================")
    print("  P R O   S T R U C T U R E   v2 — RC-Style Phrase Architecture")
    print("  Structure Notation | Phrase Pool | Transform Suffixes | Coupled HMM")
    print("================================================================================")

    out_dir = Path("output/demo_pro_structure")
    out_dir.mkdir(exist_ok=True, parents=True)

    scale = Scale(2, Mode.DORIAN)

    # ---------------------------------------------------------------------------
    # Tracks — same orchestral palette as before
    # ---------------------------------------------------------------------------
    tracks = [
        TrackConfig(
            name="Cinematic_Pad",
            generator=AmbientPadGenerator(voicing="spread"),
            instrument="dark_pad", density=0.5, octave_shift=-1,
        ),
        TrackConfig(
            name="Deep_Bass",
            generator=BassGenerator(style="root_only"),
            instrument="contrabass", density=0.6, octave_shift=-2,
        ),
        TrackConfig(
            name="Orchestral_Strings",
            generator=StringsEnsembleGenerator(section_size="full", articulation="legato", divisi=2),
            instrument="strings", density=0.7,
        ),
        TrackConfig(
            name="Lead_Melody",
            generator=MelodyGenerator(motif_probability=0.8),
            instrument="violin", density=0.6, octave_shift=1,
        ),
        TrackConfig(
            name="Woodwind_Counter",
            generator=FluteGenerator(),
            instrument="flute", density=0.5, octave_shift=1,
        ),
        TrackConfig(
            name="Epic_Choir",
            generator=ChoirAahsGenerator(voice_count=6, dynamics="f"),
            instrument="choir", density=0.6, octave_shift=1,
        ),
    ]

    # ---------------------------------------------------------------------------
    # Multi-Part Structure — now using RC-style notation
    #
    # Notation guide:
    #   A      = generate phrase, store in pool
    #   A:var  = recall A from pool, apply auto-variation
    #   A:inv  = recall A, invert intervals
    #   A:fast = recall A, halve durations (rhythmic diminution)
    #   A:retro = recall A, retrograde (reverse order)
    #
    # The Letter Rule: if two slots share the same base label (e.g. "A"),
    # the second one reuses the cached notes from the pool — no re-generation.
    # ---------------------------------------------------------------------------

    parts = [
        # === Part 1: Intro (8 bars) ===
        # Sparse. Pad + Bass drone. Woodwind introduces Theme A.
        # Structure: "A----" = 4 bars play Theme_A, 4 bars rest
        IdeaPart(
            name="Intro",
            bars=8,
            scale=scale,
            tempo=75,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Cinematic_Pad": structure_to_schedule("A", 8),
                "Deep_Bass": structure_to_schedule("A", 8),
                "Lead_Melody": structure_to_schedule("R", 8),
                "Woodwind_Counter": structure_to_schedule("A R", 4),
                "Orchestral_Strings": structure_to_schedule("R", 8),
                "Epic_Choir": structure_to_schedule("R", 8),
            },
        ),

        # === Part 2: Verse (8 bars) ===
        # Strings enter. Lead takes Theme A. Woodwind plays Response in gap.
        # Lead: "A R" = play Theme_A 4 bars, rest 4 bars
        # Woodwind: "R A:var" = rest 4, then variation of Theme_A
        IdeaPart(
            name="Verse",
            bars=8,
            scale=scale,
            tempo=80,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Cinematic_Pad": structure_to_schedule("A", 8),
                "Deep_Bass": structure_to_schedule("A", 8),
                "Orchestral_Strings": structure_to_schedule("A", 8),
                "Lead_Melody": structure_to_schedule("A R", 4),
                "Woodwind_Counter": structure_to_schedule("R A:var", 4),
                "Epic_Choir": structure_to_schedule("R", 8),
            },
        ),

        # === Part 3: Chorus (12 bars) ===
        # Full energy. Choir enters. New Theme B for Lead.
        # Lead: "B R" = new theme 8 bars, rest 4
        # Woodwind: "R B R" = rest, echo Theme_B, rest
        #   (B is reused from pool — same notes as Lead's B)
        IdeaPart(
            name="Chorus",
            bars=12,
            scale=scale,
            tempo=95,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Cinematic_Pad": structure_to_schedule("A", 12),
                "Deep_Bass": structure_to_schedule("A", 12),
                "Orchestral_Strings": structure_to_schedule("A", 12),
                "Epic_Choir": structure_to_schedule("A", 12),
                "Lead_Melody": structure_to_schedule("B R", 8, loop=False),
                "Woodwind_Counter": structure_to_schedule("R B R", 4, loop=False),
            },
        ),

        # === Part 4: Climax (8 bars) ===
        # Peak tension. Lead plays variation of Theme B.
        # "B:var" = recall B from pool, apply auto-variation
        # Woodwind plays retrograde inversion of B for dramatic effect
        IdeaPart(
            name="Climax",
            bars=8,
            scale=scale,
            tempo=110,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Cinematic_Pad": structure_to_schedule("A", 8),
                "Deep_Bass": structure_to_schedule("A", 8),
                "Orchestral_Strings": structure_to_schedule("A", 8),
                "Epic_Choir": structure_to_schedule("A", 8),
                "Lead_Melody": structure_to_schedule("B:var", 8),
                "Woodwind_Counter": structure_to_schedule("B:retro", 8),
            },
        ),

        # === Part 5: Outro (8 bars) ===
        # Resolution. Pad + Bass fade. Woodwind recalls original Theme A.
        # "A" recalls the exact same notes from the Intro — the Letter Rule!
        IdeaPart(
            name="Outro",
            bars=8,
            scale=scale,
            tempo=75,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Cinematic_Pad": structure_to_schedule("A R", 4),
                "Deep_Bass": structure_to_schedule("A R", 4),
                "Orchestral_Strings": structure_to_schedule("R", 8),
                "Epic_Choir": structure_to_schedule("R", 8),
                "Lead_Melody": structure_to_schedule("R", 8),
                "Woodwind_Counter": structure_to_schedule("A R", 4),
            },
        ),
    ]

    config = IdeaToolConfig(
        style="cinematic_hybrid",
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
        use_harmonic_verifier=True,
    )

    notes_dict = IdeaTool(config).generate()

    # ---------------------------------------------------------------------------
    # Modifier Pipeline — professional post-processing
    # ---------------------------------------------------------------------------
    print("  Applying Professional Expression & Orchestration Pipeline...")
    from melodica.modifiers import (
        ModifierPipeline, ModifierContext,
        VelocityCurveModifier, ChordToneSnapModifier, SlideLegatoModifier,
        RhythmicDensityModifier, ChordVoicingSpreadModifier, NoteDoublerModifier,
        MetricAccentModifier, HumanizeModifier,
        OverlapSafetyModifier,
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

    if "Lead_Melody" in notes_dict:
        p = ModifierPipeline(base_notes=notes_dict["Lead_Melody"])
        p.add_modifier(HumanizeModifier(timing_std=0.02, velocity_std=8.0))
        notes_dict["Lead_Melody"] = p.process(mod_context)
        print("  > Lead_Melody: Humanize")

    if "Orchestral_Strings" in notes_dict:
        p = ModifierPipeline(base_notes=notes_dict["Orchestral_Strings"])
        p.add_modifier(HumanizeModifier(timing_std=0.01, velocity_std=5.0))
        notes_dict["Orchestral_Strings"] = p.process(mod_context)
        print("  > Orchestral_Strings: Humanize")

    if "Deep_Bass" in notes_dict:
        p = ModifierPipeline(base_notes=notes_dict["Deep_Bass"])
        p.add_modifier(HumanizeModifier(timing_std=0.03, velocity_std=12.0))
        notes_dict["Deep_Bass"] = p.process(mod_context)
        print("  > Deep_Bass: Humanize")

    if "Woodwind_Counter" in notes_dict:
        p = ModifierPipeline(base_notes=notes_dict["Woodwind_Counter"])
        p.add_modifier(HumanizeModifier(timing_std=0.02, velocity_std=6.0))
        notes_dict["Woodwind_Counter"] = p.process(mod_context)
        print("  > Woodwind_Counter: Humanize")

    if "Epic_Choir" in notes_dict:
        p = ModifierPipeline(base_notes=notes_dict["Epic_Choir"])
        p.add_modifier(HumanizeModifier(timing_std=0.015, velocity_std=4.0))
        notes_dict["Epic_Choir"] = p.process(mod_context)
        print("  > Epic_Choir: Humanize")

    if "Cinematic_Pad" in notes_dict:
        p = ModifierPipeline(base_notes=notes_dict["Cinematic_Pad"])
        p.add_modifier(HumanizeModifier(timing_std=0.005, velocity_std=2.0))
        notes_dict["Cinematic_Pad"] = p.process(mod_context)
        print("  > Cinematic_Pad: Humanize")

    # ---------------------------------------------------------------------------
    # Export
    # ---------------------------------------------------------------------------
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
    instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks}

    export_multitrack_midi(
        tracks_data,
        str(out_dir / "Pro_Structure_Masterclass.mid"),
        bpm=75,
        instruments=instruments_map,
    )

    print()
    print("================================================================================")
    print(f"  SUCCESS! Structural Masterclass v2 exported to:")
    print(f"  {out_dir / 'Pro_Structure_Masterclass.mid'}")
    print()
    print("  RC-style features used:")
    print("    - Letter Rule:   'A' in Intro == 'A' in Outro (identical phrase)")
    print("    - Motive Dev:    'B:var' in Climax (auto-variation of Chorus theme)")
    print("    - Transform:     'B:retro' for Woodwind counterpoint")
    print("    - Phrase Pool:   'A' in Verse reused from Intro (no re-generation)")
    print("================================================================================")


if __name__ == "__main__":
    main()
