# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/demo_coupled_hmm.py — Demo of the new Coupled HMM Harmonizer.
Uses Dmitri Tymoczko's 'First Principles' logic for smarter modulations and chord choices.
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

# Generators
from melodica.generators.orchestral_strings import CelloGenerator, ViolinGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator

def main():
    output_dir = Path("output/demo_coupled_hmm")
    output_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        D E M O :   C O U P L E D   H M M   H A R M O N Y")
    print("        Based on Dmitri Tymoczko's 'First Principles'")
    print("=" * 80)

    # We'll create a track that starts in D Minor and modulates
    parts = [
        IdeaPart(
            name="Dark Intro", 
            bars=8, 
            scale=Scale(root=2, mode=Mode.AEOLIAN), 
            tempo=70,
            progression_type="coupled_hmm" # Using the new engine!
        ),
        IdeaPart(
            name="Rising Tension", 
            bars=8, 
            scale=Scale(root=2, mode=Mode.PHRYGIAN), 
            tempo=85,
            progression_type="coupled_hmm"
        ),
        IdeaPart(
            name="Epic Modulation", 
            bars=16, 
            scale=Scale(root=7, mode=Mode.AEOLIAN), # Modulate to G Minor
            tempo=110,
            progression_type="coupled_hmm"
        ),
    ]

    config = IdeaToolConfig(
        style="cinematic",
        parts=parts,
        use_voice_leading=True,
        use_harmonic_verifier=True,
        dissonance_tolerance=0.3,
        tracks=[
            TrackConfig(name="Cellos", generator=CelloGenerator(), instrument="cello", density=0.7),
            TrackConfig(name="Violins", generator=ViolinGenerator(), instrument="violin", density=0.6),
            TrackConfig(name="Choir", generator=ChoirAahsGenerator(), instrument="choir", density=0.5),
        ]
    )

    with EngineTracer(max_depth=2, use_colors=True):
        notes_dict = IdeaTool(config).generate()
        
        # Filter and export
        tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
        filename = "Coupled_HMM_Demo.mid"
        
        export_multitrack_midi(
            tracks_data,
            str(output_dir / filename),
            bpm=70,
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set())
        )

        print(f"\n  Success! Exported to {output_dir / filename}")
        
        # Run analyzer on the result to see the detected chords
        from scripts.harmony_analyzer import run_analysis
        run_analysis(str(output_dir / filename))

if __name__ == "__main__":
    main()
