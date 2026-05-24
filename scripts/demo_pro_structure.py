# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/demo_pro_structure.py — PRO ARRANGEMENT MASTERCLASS
Demonstrates professional arrangement architecture across a multi-part structure:
Intro -> Verse -> Chorus -> Climax -> Outro.

Leverages:
1. Deterministic Seeding: Recalling thematic motifs using slot labels ("Theme_A", "Theme_B").
2. Call and Response: Arranging tracks to "breathe" by trading plays and rests.
3. Coupled HMM progressions: Creating organic transitions and tension curves.
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    PhraseSlot, PhraseSchedule,
)
from melodica.generators import (
    MelodyGenerator, BassGenerator, StringsEnsembleGenerator, 
    AmbientPadGenerator, ArpeggiatorGenerator, FluteGenerator, 
    ChoirAahsGenerator, TimpaniGenerator, DrumKitPatternGenerator, 
    BrassSectionGenerator, LeadSynthGenerator, PluckSequenceGenerator
)
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

# ---------------------------------------------------------------------------
# Professional Arrangement Phrase Schedules
# ---------------------------------------------------------------------------

# Helper to create precise non-looping schedules for individual parts
def _phrase(slots: list[PhraseSlot], loop: bool = False) -> PhraseSchedule:
    return PhraseSchedule(slots=slots, loop=loop)

def main():
    print("================================================================================")
    print("  P R O   S T R U C T U R E   &   A R R A N G E M E N T   M A S T E R C L A S S")
    print("  Multi-Part Cinematic Suite | Advanced Phrase Scheduling | Coupled HMM")
    print("================================================================================")

    out_dir = Path("output/demo_pro_structure")
    out_dir.mkdir(exist_ok=True, parents=True)

    # ---------------------------------------------------------------------------
    # Global Scale & Track Setup
    # We define a 5-part structure:
    # 1. Intro (8 bars)   - Ambient, sparse, introduces Theme A.
    # 2. Verse (8 bars)   - Legato flow, rhythmic anchor, solidifies Theme A.
    # 3. Chorus (12 bars) - Peak thick energy, choir, brass stabs, Theme B.
    # 4. Climax (8 bars)  - Utter tension, arpeggiators, double density, Theme B variation.
    # 5. Outro (8 bars)   - Falling energy, solo woodwind, fading Theme A.
    # ---------------------------------------------------------------------------
    
    # We'll use D Dorian for a cool, heroic, neoclassical cinematic vibe.
    scale = Scale(2, Mode.DORIAN)

    # We define our 6 primary orchestral tracks.
    # Instead of static muting, we will control their play/rest/ghost states
    # inside each IdeaPart using 'track_phrase_schedules' overrides!
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
    # Defining the Multi-Part Structural Journey
    # ---------------------------------------------------------------------------
    parts = [
        # --- Part 1: Intro (8 bars) ---
        # Very sparse. Pad and Bass build tension.
        # Woodwind plays the primary theme ("Theme_A") for the first 4 bars, then rests.
        IdeaPart(
            name="Intro",
            bars=8,
            scale=scale,
            tempo=75,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Cinematic_Pad": _phrase([PhraseSlot("play", 8, "Pad")]),
                "Deep_Bass": _phrase([PhraseSlot("play", 8, "Bass")]),
                "Lead_Melody": _phrase([PhraseSlot("rest", 8)]),  # Lead waits
                "Woodwind_Counter": _phrase([
                    PhraseSlot("play", 4, "Theme_A"),  # Call: introduces Theme A
                    PhraseSlot("rest", 4)
                ]),
                "Orchestral_Strings": _phrase([PhraseSlot("rest", 8)]),
                "Epic_Choir": _phrase([PhraseSlot("rest", 8)]),
            }
        ),

        # --- Part 2: Verse (8 bars) ---
        # Strings enter. Deep Bass locks in.
        # Lead Melody takes over the primary theme ("Theme_A") to establish continuity.
        # Woodwind rests while Lead plays, then plays a counter-phrase ("Response") in the second half.
        # This is a classic "Call & Response" trade-off!
        IdeaPart(
            name="Verse",
            bars=8,
            scale=scale,
            tempo=80,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Cinematic_Pad": _phrase([PhraseSlot("play", 8, "Pad")]),
                "Deep_Bass": _phrase([PhraseSlot("play", 8, "Bass")]),
                "Orchestral_Strings": _phrase([PhraseSlot("play", 8, "Strings")]),
                "Lead_Melody": _phrase([
                    PhraseSlot("play", 4, "Theme_A"),  # Returns here under new chords!
                    PhraseSlot("rest", 4)
                ]),
                "Woodwind_Counter": _phrase([
                    PhraseSlot("rest", 4),
                    PhraseSlot("play", 4, "Response_A")  # Fills the gap when Lead rests
                ]),
                "Epic_Choir": _phrase([PhraseSlot("rest", 8)]),
            }
        ),

        # --- Part 3: Chorus (12 bars) ---
        # Full energy. Epic Choir enters.
        # Strings and Pads play high-density block chords.
        # Lead Melody plays a brand new, highly emotional chorus melody ("Theme_B").
        # Woodwind plays counterpoint in alternating 4-bar segments.
        IdeaPart(
            name="Chorus",
            bars=12,
            scale=scale,
            tempo=95,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Cinematic_Pad": _phrase([PhraseSlot("play", 12, "Pad_Chorus")]),
                "Deep_Bass": _phrase([PhraseSlot("play", 12, "Bass_Chorus")]),
                "Orchestral_Strings": _phrase([PhraseSlot("play", 12, "Strings_Chorus")]),
                "Epic_Choir": _phrase([PhraseSlot("play", 12, "Choir_Chorus")]),
                "Lead_Melody": _phrase([
                    PhraseSlot("play", 8, "Theme_B"),  # Bold new chorus line
                    PhraseSlot("rest", 4)
                ]),
                "Woodwind_Counter": _phrase([
                    PhraseSlot("rest", 4),
                    PhraseSlot("play", 4, "Counter_B"),
                    PhraseSlot("play", 4, "Theme_B")  # Woodwind echoes the main chorus melody
                ]),
            }
        ),

        # --- Part 4: Climax (8 bars) ---
        # Peak tension. Strings switch to fast driving motion.
        # Lead Melody plays an intense variation of the Chorus theme ("Theme_B_Var").
        # Choir swells.
        IdeaPart(
            name="Climax",
            bars=8,
            scale=scale,
            tempo=110,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Cinematic_Pad": _phrase([PhraseSlot("play", 8, "Pad_Climax")]),
                "Deep_Bass": _phrase([PhraseSlot("play", 8, "Bass_Climax")]),
                "Orchestral_Strings": _phrase([PhraseSlot("play", 8, "Strings_Drive")]),
                "Epic_Choir": _phrase([PhraseSlot("play", 8, "Choir_Swell")]),
                "Lead_Melody": _phrase([PhraseSlot("play", 8, "Theme_B_Var")]),  # Peak variant
                "Woodwind_Counter": _phrase([PhraseSlot("play", 8, "Counter_Climax")]),
            }
        ),

        # --- Part 5: Outro (8 bars) ---
        # Resolution. Strings, Choir, and Bass fade out.
        # Solo Woodwind plays the original Theme A one last time ("Theme_A") for a nostalgic, circular ending.
        IdeaPart(
            name="Outro",
            bars=8,
            scale=scale,
            tempo=75,
            progression_type="coupled_hmm",
            track_phrase_schedules={
                "Cinematic_Pad": _phrase([
                    PhraseSlot("play", 4, "Pad_Fade"),
                    PhraseSlot("rest", 4)
                ]),
                "Deep_Bass": _phrase([
                    PhraseSlot("play", 4, "Bass_Fade"),
                    PhraseSlot("rest", 4)
                ]),
                "Orchestral_Strings": _phrase([PhraseSlot("rest", 8)]),
                "Epic_Choir": _phrase([PhraseSlot("rest", 8)]),
                "Lead_Melody": _phrase([PhraseSlot("rest", 8)]),
                "Woodwind_Counter": _phrase([
                    PhraseSlot("play", 4, "Theme_A"),  # Recalls the original Theme A deterministically
                    PhraseSlot("rest", 4)
                ]),
            }
        ),
    ]

    # Configure the full suite!
    config = IdeaToolConfig(
        style="cinematic_hybrid",
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
        use_harmonic_verifier=True,
    )

    notes_dict = IdeaTool(config).generate()
    
    # ---------------------------------------------------------------------------
    # Using the Non-Destructive Modifier Pipeline (Variation Stack)
    # ---------------------------------------------------------------------------
    print("  Applying Advanced Non-Destructive Modifier Pipeline...")
    from melodica.modifiers import (
        ModifierPipeline, ModifierContext, 
        SwingController, QuantizeModifier, HumanizeModifier,
        VelocityCurveModifier, ChordToneSnapModifier, SlideLegatoModifier,
        RhythmicDensityModifier, ChordVoicingSpreadModifier, NoteDoublerModifier
    )

    # Derived context for modifiers
    total_bars = sum(p.bars for p in parts)
    
    # Extract the generated timeline (chords/keys) from the tool output
    # Notes dict often contains hidden keys with timeline data
    # If not, we'll construct a simple one for the demo
    from melodica.types import MusicTimeline
    timeline = notes_dict.get("_timeline", MusicTimeline(chords=[], keys=[]))

    mod_context = ModifierContext(
        duration_beats=total_bars * 4,
        chords=timeline.chords,
        timeline=timeline,
        scale=scale
    )

    if "Lead_Melody" in notes_dict:
        pipeline = ModifierPipeline(base_notes=notes_dict["Lead_Melody"])
        
        # 1. Harmonic integrity: Snap all melody notes to current chord tones!
        pipeline.add_modifier(ChordToneSnapModifier())
        
        # 2. Expression: Use S-Curve velocity ramp instead of linear
        pipeline.add_modifier(VelocityCurveModifier(start_vel=45, end_vel=115, curve="s_curve"))
        
        # 3. Articulation: Add violin-style pitch slides between close notes
        pipeline.add_modifier(SlideLegatoModifier(slide_beats=0.15))
        
        # 4. Feel: Triplet swing and quantization
        pipeline.add_modifier(SwingController(swing_ratio=0.6))
        pipeline.add_modifier(QuantizeModifier(grid_resolution=0.125))

        notes_dict["Lead_Melody"] = pipeline.process(mod_context)
        print(f"  > Lead_Melody: Snapped to chords + S-Curve dynamics + Legato Slides applied!")

    if "Orchestral_Strings" in notes_dict:
        str_pipeline = ModifierPipeline(base_notes=notes_dict["Orchestral_Strings"])
        
        # 1. Spacing: Widening the string section voicing
        str_pipeline.add_modifier(ChordVoicingSpreadModifier(spread_mode="open"))
        
        # 2. Thickness: Octave doubling
        str_pipeline.add_modifier(NoteDoublerModifier(octaves=[-1]))
        
        notes_dict["Orchestral_Strings"] = str_pipeline.process(mod_context)
        print(f"  > Orchestral_Strings: Open voicings + Octave doubling applied!")

    if "Deep_Bass" in notes_dict:
        bass_pipeline = ModifierPipeline(base_notes=notes_dict["Deep_Bass"])
        
        # 1. Density: Let's thin out the bass a bit to make it less "busy"
        bass_pipeline.add_modifier(RhythmicDensityModifier(density=0.8))
        
        # 2. Humanize
        bass_pipeline.add_modifier(HumanizeModifier(timing_std=0.03, velocity_std=12.0))
        
        notes_dict["Deep_Bass"] = bass_pipeline.process(mod_context)
        print(f"  > Deep_Bass: Rhythmic thinning + Humanization applied!")


    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
    
    instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks}
    
    export_multitrack_midi(
        tracks_data,
        str(out_dir / "Pro_Structure_Masterclass.mid"),
        bpm=75,
        instruments=instruments_map
    )

    print("\n================================================================================")
    print(f"  SUCCESS! Structural Masterclass Suite exported to:")
    print(f"  {out_dir / 'Pro_Structure_Masterclass.mid'}")
    print("================================================================================")

if __name__ == "__main__":
    main()
