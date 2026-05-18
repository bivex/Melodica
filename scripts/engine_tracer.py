# Copyright (c) 2026 Bivex
# Engine Tracer: Diagnostic utility to see function calls "under the hood"

import sys
from pathlib import Path
from melodica import types
from melodica.idea_tool import IdeaTool, IdeaToolConfig

def trace_calls(frame, event, arg):
    if event != 'call':
        return
    
    code = frame.f_code
    func_name = code.co_name
    file_name = code.co_filename
    
    # Trace all melodica internal modules, but skip standard library or external packages
    if "/melodica/" in file_name and not "melodica/midi.py" in file_name:
        # Exclude dunder methods to reduce noise
        if func_name.startswith("__") and func_name != "__init__":
            return trace_calls

        line_no = frame.f_lineno
        depth = 0
        tmp_frame = frame
        while tmp_frame:
            depth += 1
            tmp_frame = tmp_frame.f_back
        
        # Calculate clean module name
        module_path = file_name.split("/melodica/")[-1]
        
        indent = "  " * (depth - 1)
        print(f"{indent}--> CALL [{module_path}]: {func_name}()")
    
    return trace_calls

def run_traced_gen():
    print("\n" + "="*70)
    print("   STARTING SYSTEM-WIDE TRACED GENERATION (UNDER THE HOOD)")
    print("="*70 + "\n")
    
    cfg = IdeaToolConfig(
        bars=4, 
        tempo=120,
        melody_gen="MelodyGenerator",
        chords_gen="ChordGenerator",
        bass_gen="BassGenerator",
        drums_gen="TrapDrumsGenerator",
        style="synthwave"
    )
    tool = IdeaTool(cfg)
    
    sys.settrace(trace_calls)
    try:
        # Generate a small 4-bar idea which triggers composer, harmonizer, generators, and modifiers
        result = tool.generate()
    finally:
        sys.settrace(None)
        
    print("\n" + "="*70)
    print(f"   TRACE COMPLETE. Generated tracks: {list(result.keys())}")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_traced_gen()
