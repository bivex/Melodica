# trace_album.py
import sys
from pathlib import Path

# Create output folder if not exists
out_dir = Path("output/album_soft_machines_continuous")
out_dir.mkdir(parents=True, exist_ok=True)
trace_file = open(out_dir / "call_trace.txt", "w", encoding="utf-8")

# Trace state
depth = 0

# Set of files or helper functions to exclude to avoid massive spam
EXCLUDE_FUNCS = {
    "clamp_to_scale", "nearest_pitch", "snap_to_scale",
    "contains", "degrees", "intervals", "degree_of", "pitch_classes",
    "contains_pitch_class", "chord_at", "chord_at_beat"
}

EXCLUDE_FILES = {
    "_theory.py", "types.py", "types_pkg",
    "harmonic_verifier.py", "psychoacoustic.py",
    "voice_leading.py", "modes.py",
    "synth_bass.py", "dark_pad.py", "solo_melody.py", "lofi_hiphop.py", 
    "breakbeat.py", "arpeggiator.py", "harp.py", "fx_riser.py", "fx_impact.py", 
    "coupled_hmm.py", "functional_hmm.py", "functional_structures.py",
    "scale_navigator.py", "tension_curve.py", "midi.py", "mastering.py", 
    "form_validator.py", "style_profiles.py", "structure_parser.py"
}

WHITELIST_PRIVATE = {
    "_apply_section_moods", "_tension_boost", "_transition_pad", 
    "_get_resolved_parts", "_generate_progression"
}

def trace_calls(frame, event, arg):
    global depth
    if event == 'call':
        code = frame.f_code
        func_name = code.co_name
        filename = code.co_filename
        
        # Only trace files inside the melodica package
        if 'melodica' in filename:
            # Skip excluded files
            if any(ef in filename for ef in EXCLUDE_FILES):
                return None  # don't trace inside this function
                
            # Skip low-level helpers
            if func_name in EXCLUDE_FUNCS:
                return None
                
            # Skip generator expressions, lambdas, and list/dict comprehensions
            if func_name in ("<genexpr>", "<listcomp>", "<dictcomp>", "<setcomp>", "<lambda>"):
                return None
                
            # Skip private functions unless whitelisted
            if func_name.startswith("_") and func_name not in WHITELIST_PRIVATE:
                return None
                
            rel_path = filename.split('melodica')[-1]
            line_no = frame.f_lineno
            indent = "  " * depth
            
            # Write trace entry
            trace_file.write(f"{indent}-> {func_name} (melodica{rel_path}:{line_no})\n")
            depth += 1
            return trace_calls
            
    elif event == 'return':
        code = frame.f_code
        filename = code.co_filename
        func_name = code.co_name
        
        if 'melodica' in filename:
            if any(ef in filename for ef in EXCLUDE_FILES):
                return None
            if func_name in EXCLUDE_FUNCS:
                return None
            if func_name in ("<genexpr>", "<listcomp>", "<dictcomp>", "<setcomp>", "<lambda>"):
                return None
            if func_name.startswith("_") and func_name not in WHITELIST_PRIVATE:
                return None
                
            depth = max(0, depth - 1)
            
    return trace_calls

# Start tracing
sys.settrace(trace_calls)

try:
    # Run the album generation
    from scripts.albums.electronic.album_soft_machines_continuous import produce_soft_machines_continuous
    produce_soft_machines_continuous()
finally:
    # Stop tracing
    sys.settrace(None)
    trace_file.close()
    print(f"\nTrace successfully written to {out_dir / 'call_trace.txt'}")
