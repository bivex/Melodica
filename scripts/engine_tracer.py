# Copyright (c) 2026 Bivex
# Engine Tracer: Diagnostic utility to see function calls "under the hood"

import sys
from pathlib import Path
from melodica import types
from melodica.idea_tool import IdeaTool, IdeaToolConfig

from melodica.tracer import EngineTracer

def run_traced_gen():
    print("\n" + "="*70)
    print("   STARTING SYSTEM-WIDE TRACED GENERATION (UNDER THE HOOD)")
    print("="*70 + "\n")
    
    from melodica.idea_tool import TrackConfig
    cfg = IdeaToolConfig(
        bars=4, 
        tempo=120,
        tracks=[
            TrackConfig(name="melody", generator_type="melody"),
            TrackConfig(name="chords", generator_type="chord"),
            TrackConfig(name="bass", generator_type="bass"),
            TrackConfig(name="drums", generator_type="trap_drums"),
        ],
        style="synthwave"
    )
    tool = IdeaTool(cfg)
    
    # Use our unified, profiling, and colorized tracer!
    with EngineTracer(show_duration=True, use_colors=True):
        # Generate a small 4-bar idea which triggers composer, harmonizer, generators, and modifiers
        result = tool.generate()
        
    print("\n" + "="*70)
    print(f"   TRACE COMPLETE. Generated tracks: {list(result.keys())}")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_traced_gen()
