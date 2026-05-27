# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/demo_tracer_harmony.py — Coupled HMM Harmony Tracer.

This script demonstrates how the "coupled_hmm" progression engine works under the hood.
It generates a 16-bar progression in 3 different styles ("pop", "cinematic", "grime")
using the exact same input parameters (D Harmonic Minor, 120 BPM) and compares
how the Hidden Markov Model (HMM) makes completely different harmonic choices based 
on the active style profile's rules (dissonance tolerance, extensions, chord rates).
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode

def trace_style_progression(style_name: str, scale: Scale):
    print(f"\n============================================================")
    print(f"  TRACING HMM HARMONY ENGINE : STYLE '{style_name.upper()}'")
    print(f"============================================================")
    
    # Minimal config: We don't even need tracks, just an IdeaPart to trigger the progression engine.
    parts = [
        IdeaPart(
            name="AnalysisBlock", 
            bars=16, 
            scale=scale, 
            tempo=120, 
            progression_type="coupled_hmm"
        )
    ]
    
    config = IdeaToolConfig(
        style=style_name,
        parts=parts,
        tracks=[], # No tracks needed, we just want the chords!
        use_tension_curve=True # Let tension shape the HMM probabilities
    )
    
    # Run the engine
    result = IdeaTool(config).generate()
    chords = result.get("_chords", [])
    
    if not chords:
        print("  [!] No chords generated.")
        return

    print(f"  Generated {len(chords)} chords for 16 bars (64 beats):")
    print("  Onset | Quality    | Root | Deg | Extensions | Note")
    print("  ------------------------------------------------------------")
    
    # Trace logic
    for i, c in enumerate(chords):
        ext_str = f"+{c.extensions}" if c.extensions else ""
        deg_str = f"({c.degree_roman})" if hasattr(c, "degree_roman") else f"deg:{c.degree}"
        
        # Look ahead for duration/transitions
        dur = c.duration
        
        # Analyze stability / tension
        is_dissonant = c.quality.name in ["DIMINISHED", "HALF_DIM7", "FULL_DIM7", "AUGMENTED"]
        tension_mark = "⚠️ TENSION" if is_dissonant else ""
        
        print(f"  {c.start:5.1f}b | {c.quality.name:10} | {c.root:4} | {deg_str:5} | {ext_str:10} | {tension_mark}")
        

def main():
    print("Initializing Coupled HMM Tracer...\n")
    
    # Let's use a very emotional scale: D Harmonic Minor
    scale = Scale(2, Mode.HARMONIC_MINOR)
    
    print(f"Base Key: D Harmonic Minor (Root: {scale.root}, Mode: {scale.mode.name})")
    
    # 1. Pop Style (Safe, triad-focused, fast harmonic rhythm)
    trace_style_progression("pop", scale)
    
    # 2. Cinematic Style (Dark, slow-moving, suspended/diminished chords allowed)
    trace_style_progression("cinematic", scale)
    
    # 3. Grime Style (Aggressive, extremely slow harmonic rhythm, highly dissonant)
    trace_style_progression("grime", scale)
    
    print("\n============================================================")
    print("  TRACE COMPLETE.")
    print("  Notice how the HMM dynamically alters the chord vocabulary,")
    print("  extension usage, and chord duration based on the Unified Style!")
    print("============================================================")


if __name__ == "__main__":
    main()
