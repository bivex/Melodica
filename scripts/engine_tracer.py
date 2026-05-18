# Copyright (c) 2026 Bivex
# Engine Tracer: Diagnostic utility to see function calls "under the hood"

import sys
from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams, MelodyGenerator

def trace_calls(frame, event, arg):
    if event != 'call':
        return
    
    code = frame.f_code
    func_name = code.co_name
    file_name = code.co_filename
    
    # Only trace our engine files
    if "melodica/generators" in file_name or "melodica/types_pkg" in file_name:
        line_no = frame.f_lineno
        depth = 0
        tmp_frame = frame
        while tmp_frame:
            depth += 1
            tmp_frame = tmp_frame.f_back
        
        indent = "  " * (depth - 1)
        print(f"{indent}--> CALL: {func_name} in {Path(file_name).name}:{line_no}")
    
    return trace_calls

def run_traced_gen():
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)
    chords = [key.parse_roman("i")]
    chords[0].start = 0
    chords[0].duration = 4.0
    
    params = GeneratorParams(density=0.5)
    gen = MelodyGenerator(params)
    
    print("\n" + "="*70)
    print("   STARTING TRACED GENERATION (UNDER THE HOOD)")
    print("="*70 + "\n")
    
    sys.settrace(trace_calls)
    try:
        # We only generate 1 bar to keep the trace readable
        gen.render(chords, key, 4.0)
    finally:
        sys.settrace(None)
        
    print("\n" + "="*70)
    print("   TRACE COMPLETE.")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_traced_gen()
