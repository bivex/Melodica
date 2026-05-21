# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
visualize_dracula_arrangement.py — Visualization of the "Dracula" Album structure.

This script runs the Dracula album generation logic but instead of exporting MIDI,
it captures the note data and prints a professional arrangement timeline (Gantt-style)
to the console. This helps the senior arranger see the orchestration balance,
track activity, and density distribution.
"""

import sys
from pathlib import Path
from collections import defaultdict

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from melodica import types
from melodica.composer import album_pipeline
import scripts.album_dracula as album_dracula

# Store captured data: (track_name, notes, bpm, path_name)
captured_tracks = []

def mock_produce_track(tracks, bpm, instruments, path, **kwargs):
    track_info = {
        "name": path.name,
        "bpm": bpm,
        "tracks": tracks,
        "instruments": instruments
    }
    captured_tracks.append(track_info)

# Monkey-patch produce_track to capture data
album_pipeline.produce_track = mock_produce_track
album_dracula.produce_track = mock_produce_track

def visualize_track_activity(track_data, width=100):
    """Prints an ASCII Gantt chart for a single track (movement)."""
    name = track_data["name"]
    bpm = track_data["bpm"]
    tracks = track_data["tracks"]
    
    # Calculate total duration in beats
    max_beats = 0
    for t_notes in tracks.values():
        if t_notes:
            end = max(n.start + n.duration for n in t_notes)
            max_beats = max(max_beats, end)
    
    if max_beats == 0:
        print(f"DEBUG: No notes found in {name}")
        return

    print(f"\n{'='*width}")
    print(f" MOVEMENT: {name} | BPM: {bpm} | Duration: {max_beats:.1f} beats")
    print(f"{'='*width}")
    
    # Header: Beat markers
    # Simpler header
    header_beats = "".join([f"{b:<8}"[:8] for b in range(0, int(max_beats) + 8, 8)])
    print(f"{'Track Name':<15} | {header_beats}")
    print("-" * width)

    for t_name, notes in sorted(tracks.items()):
        if not notes:
            continue
            
        # Create a timeline grid
        grid_width = width - 18
        grid = [" "] * grid_width
        
        # Calculate pitch range and average
        pitches = [n.pitch for n in notes]
        avg_pitch = sum(pitches) / len(pitches)
        min_p, max_p = min(pitches), max(pitches)
        
        # Populate grid
        for n in notes:
            start_idx = int((n.start / max_beats) * (grid_width - 1))
            end_idx = int(((n.start + n.duration) / max_beats) * (grid_width - 1))
            
            # Use different symbols for different pitch ranges
            # Low: =, Mid: #, High: *
            char = "#"
            if n.pitch < 48: char = "="
            elif n.pitch > 72: char = "*"
            
            for i in range(start_idx, min(end_idx + 1, grid_width)):
                grid[i] = char
        
        row_label = f"{t_name:<15} |"
        print(f"{row_label}{''.join(grid)}  [{min_p}-{max_p}] avg:{int(avg_pitch)}")

    # Add Vertical Density (how many instruments playing at once)
    grid_width = width - 18
    density_grid = [0] * grid_width
    for t_name, notes in tracks.items():
        if not notes: continue
        for n in notes:
            start_idx = int((n.start / max_beats) * (grid_width - 1))
            end_idx = int(((n.start + n.duration) / max_beats) * (grid_width - 1))
            for i in range(start_idx, min(end_idx + 1, grid_width)):
                density_grid[i] += 1
    
    density_str = "".join([str(min(9, d)) if d > 0 else " " for d in density_grid])
    print("-" * width)
    print(f"{'OVERALL VOICES':<15} | {density_str}")

def main():
    print("=" * 70)
    print("   MELODICA ARRANGEMENT VISUALIZER")
    print("   Project: BRAM STOKER — DRACULA")
    print("=" * 70)
    print("Capturing arrangement data...")
    
    # Run all movements
    album_dracula.produce_carpathian_castle()
    album_dracula.produce_counts_archives()
    album_dracula.produce_blood_is_life()
    album_dracula.produce_highgate_vault()
    album_dracula.produce_vampire_hunt()
    
    print(f"\nCaptured {len(captured_tracks)} movements.\n")
    
    for movement in captured_tracks:
        visualize_track_activity(movement)
        
    print("\nVisualization Legend:")
    print("  '=' : Low register (MIDI < 48)")
    print("  '#' : Mid register (48 - 72)")
    print("  '*' : High register (MIDI > 72)")
    print("  [min-max] : MIDI pitch range")

if __name__ == "__main__":
    main()
