# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
visualize_arrangement.py — Universal Visualization for Melodica Arrangements.

Usage:
    python3 scripts/visualize_arrangement.py scripts/album_dracula.py
    python3 scripts/visualize_arrangement.py scripts/album_city_that_hears.py

This script hooks into Melodica's MIDI export system to capture and visualize 
the phrase structure, register distribution, and vertical density of any 
composition script.
"""

import sys
import os
import argparse
import importlib.util
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

import melodica.midi as midi
from melodica import types

# Global list to store captured compositions
captured_compositions = []

def mock_export_multitrack_midi(tracks, filename, bpm=120, instruments=None, **kwargs):
    """Replacement for export_multitrack_midi that captures data for visualization."""
    comp_info = {
        "name": Path(filename).name,
        "bpm": bpm,
        "tracks": tracks,
        "instruments": instruments or {}
    }
    captured_compositions.append(comp_info)
    # We don't call the original because we only want visualization
    print(f"   [Visualizer] Captured: {comp_info['name']}")

# Monkey-patch the core MIDI export function
midi.export_multitrack_midi = mock_export_multitrack_midi

def visualize_composition(comp_data, width=100):
    """Prints an ASCII Gantt chart and density map for a composition."""
    name = comp_data["name"]
    bpm = comp_data["bpm"]
    tracks = comp_data["tracks"]
    
    # Calculate total duration in beats
    max_beats = 0
    # tracks can be dict[str, list[NoteInfo]] or dict[str, Track]
    for t_obj in tracks.values():
        # Handle both Track objects and raw NoteInfo lists
        notes = t_obj.notes if hasattr(t_obj, "notes") else t_obj
        if notes:
            end = max(n.start + n.duration for n in notes)
            max_beats = max(max_beats, end)
    
    if max_beats == 0:
        print(f"   [Warning] No note data found in {name}")
        return

    print(f"\n{'='*width}")
    print(f" COMPOSITION: {name} | BPM: {bpm} | Duration: {max_beats:.1f} beats")
    print(f"{'='*width}")
    
    header_beats = "".join([f"{b:<8}"[:8] for b in range(0, int(max_beats) + 8, 8)])
    print(f"{'Track Name':<15} | {header_beats}")
    print("-" * width)

    grid_width = width - 18

    for t_name, t_obj in sorted(tracks.items()):
        notes = t_obj.notes if hasattr(t_obj, "notes") else t_obj
        if not notes:
            continue
            
        grid = [" "] * grid_width
        pitches = [n.pitch for n in notes]
        avg_pitch = sum(pitches) / len(pitches)
        min_p, max_p = min(pitches), max(pitches)
        
        for n in notes:
            start_idx = int((n.start / max_beats) * (grid_width - 1))
            end_idx = int(((n.start + n.duration) / max_beats) * (grid_width - 1))
            
            char = "#"
            if n.pitch < 48: char = "="
            elif n.pitch > 72: char = "*"
            
            for i in range(start_idx, min(end_idx + 1, grid_width)):
                grid[i] = char
        
        print(f"{t_name:<15} |{''.join(grid)}  [{min_p}-{max_p}] avg:{int(avg_pitch)}")

    # Vertical Density
    density_grid = [0] * grid_width
    for t_obj in tracks.values():
        notes = t_obj.notes if hasattr(t_obj, "notes") else t_obj
        if not notes: continue
        for n in notes:
            start_idx = int((n.start / max_beats) * (grid_width - 1))
            end_idx = int(((n.start + n.duration) / max_beats) * (grid_width - 1))
            for i in range(start_idx, min(end_idx + 1, grid_width)):
                density_grid[i] += 1
    
    density_str = "".join([str(min(9, d)) if d > 0 else " " for d in density_grid])
    print("-" * width)
    print(f"{'OVERALL VOICES':<15} | {density_str}")

def run_script(script_path):
    """Dynamically loads and runs the main() function of a given script."""
    path = Path(script_path).resolve()
    if not path.exists():
        print(f"Error: Script {script_path} not found.")
        return

    print(f"Loading script: {path.name}...")
    
    # Set up module spec and load
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    
    # We must ensure produce_track in album_pipeline also points to our mock
    # because some scripts might have imported it before we patched midi.py
    # But usually scripts run code in if __name__ == "__main__" or main()
    
    try:
        spec.loader.exec_module(module)
        
        # Look for main() or run individual functions if it's a specific known script
        if hasattr(module, "main"):
            print(f"Executing {module_name}.main()...")
            module.main()
        else:
            # Fallback: if no main, maybe it already executed on import?
            # Or we can try to find all produce_* functions if it's like album_dracula
            funcs = [f for f in dir(module) if f.startswith("produce_") and callable(getattr(module, f))]
            if funcs:
                print(f"Found {len(funcs)} produce functions. Executing...")
                for f_name in funcs:
                    func = getattr(module, f_name)
                    # Check if it takes arguments
                    import inspect
                    sig = inspect.signature(func)
                    if len(sig.parameters) == 0:
                        func()
            else:
                print(f"Finished executing {module_name}. No main() or produce_* functions called manually.")
                
    except Exception as e:
        print(f"Error during script execution: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description="Universal Melodica Arrangement Visualizer")
    parser.add_argument("script", help="Path to the Melodica script to visualize")
    parser.add_argument("--width", type=int, default=100, help="Visualization width")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("   MELODICA UNIVERSAL ARRANGEMENT VISUALIZER")
    print("=" * 70)
    
    run_script(args.script)
    
    if not captured_compositions:
        print("\nNo composition data captured. Ensure the script calls produce_track() or export_multitrack_midi().")
    else:
        print(f"\nCaptured {len(captured_compositions)} compositions.\n")
        for comp in captured_compositions:
            visualize_composition(comp, width=args.width)
            
    print("\nVisualization Legend:")
    print("  '=' : Low register (MIDI < 48)")
    print("  '#' : Mid register (48 - 72)")
    print("  '*' : High register (MIDI > 72)")
    print("  [min-max] : MIDI pitch range")
    print("  Density Row: 1-9 indicates number of simultaneous instruments")

if __name__ == "__main__":
    main()
