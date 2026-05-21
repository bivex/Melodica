# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
visualize_arrangement.py — Advanced Universal Visualization for Melodica Arrangements.

Usage:
    python3 scripts/visualize_arrangement.py scripts/album_dracula.py
    python3 scripts/visualize_arrangement.py scripts/album_city_that_hears.py --output report.md

Features:
    - Gantt-style Track Activity with Register Encoding
    - Phrase/Section Auto-detection
    - Sliding-window Harmonic Analysis (Chord detection)
    - Velocity Intensity Heatmaps
    - Overall Vertical Density (Voice count)
    - Rhythmic Activity (Onsets)
    - Automated Musician's Critique
"""

import sys
import os
import argparse
import importlib.util
import io
import math
from pathlib import Path
from collections import defaultdict

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

import melodica.midi as midi
import melodica.composer.album_pipeline as album_pipeline
from melodica import types
from melodica.detection import detect_chord, detect_scale
from melodica.utils import pitch_class

_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def note_name(pc):
    """MIDI pitch class → note name."""
    return _NOTE_NAMES[pc % 12]

# Global list to store captured compositions
captured_compositions = []

def mock_export_multitrack_midi(tracks, filename, bpm=120, instruments=None, **kwargs):
    """Replacement for export_multitrack_midi that captures data for visualization."""
    comp_info = {
        "name": Path(filename).name,
        "bpm": bpm,
        "tracks": tracks,
        "instruments": instruments or {},
        "key": kwargs.get("key")
    }
    captured_compositions.append(comp_info)
    print(f"   [Visualizer] Captured: {comp_info['name']}")

# Monkey-patch the core MIDI export function
midi.export_multitrack_midi = mock_export_multitrack_midi
album_pipeline.export_multitrack_midi = mock_export_multitrack_midi

def get_sparkline(values, max_val=None):
    """Converts a list of numbers into a Unicode sparkline."""
    if not values: return ""
    chars = " ▂▃▄▅▆▇█"
    if max_val is None:
        max_val = max(values) if max(values) > 0 else 1
    
    line = ""
    for v in values:
        idx = int((v / max_val) * (len(chars) - 1))
        idx = max(0, min(idx, len(chars) - 1))
        line += chars[idx]
    return line

def get_intensity_char(velocity):
    """Maps velocity to intensity character."""
    # ░▒▓█
    if velocity < 40: return " "
    if velocity < 60: return "░"
    if velocity < 85: return "▒"
    if velocity < 110: return "▓"
    return "█"

def analyze_harmonies(all_notes, duration, width):
    """Sliding window chord detection."""
    harmonies = []
    step = duration / width
    for i in range(width):
        t_start = i * step
        t_end = t_start + step
        window_notes = [n for n in all_notes if n.start < t_end and (n.start + n.duration) > t_start]
        chord = detect_chord(window_notes)
        if chord:
            name = f"{note_name(chord.root)}{chord.quality.value}"
            harmonies.append(name)
        else:
            harmonies.append("-")
    return harmonies

def detect_sections(tracks, duration, width):
    """Heuristic section detection."""
    sections = []
    step = duration / width
    
    # Calculate track activity per cell
    activity = []
    for i in range(width):
        t_start = i * step
        t_end = t_start + step
        active_set = set()
        for t_name, t_obj in tracks.items():
            notes = t_obj.notes if hasattr(t_obj, "notes") else t_obj
            if any(n.start < t_end and (n.start + n.duration) > t_start for n in notes):
                active_set.add(t_name)
        activity.append(active_set)
    
    current_start = 0
    current_set = activity[0]
    
    for i in range(1, width):
        if activity[i] != current_set:
            sections.append((current_start, i, current_set))
            current_start = i
            current_set = activity[i]
    sections.append((current_start, width, current_set))
    
    # Filter very short sections and give them names
    named_sections = []
    for start, end, t_set in sections:
        if (end - start) < (width * 0.05): continue # Skip tiny glitches
        
        # Heuristic names
        label = "Theme"
        if not t_set: label = "Silence"
        elif len(t_set) <= 2 and start == 0: label = "Intro"
        elif len(t_set) <= 2 and end == width: label = "Outro"
        elif len(t_set) >= len(tracks) * 0.8: label = "Climax"
        elif any("drums" in n.lower() or "perc" in n.lower() for n in t_set):
            label = "Main"
        
        named_sections.append((start, end, label))
    
    return named_sections

def generate_critique(comp_data):
    """Automated Musician's Critique."""
    critique = []
    tracks = comp_data["tracks"]
    
    # Range stats
    all_notes = []
    track_ranges = {}
    for t_name, t_obj in tracks.items():
        notes = t_obj.notes if hasattr(t_obj, "notes") else t_obj
        if notes:
            all_notes.extend(notes)
            pitches = [n.pitch for n in notes]
            track_ranges[t_name] = (min(pitches), max(pitches))

    # 1. Low-interval mud
    mud_count = 0
    bass_notes = [n for n in all_notes if n.pitch < 48]
    # Simple check for simultaneous notes in bass
    for i, n1 in enumerate(bass_notes):
        for n2 in bass_notes[i+1:i+20]: # Scoped check
            if abs(n1.start - n2.start) < 0.1 and 0 < abs(n1.pitch - n2.pitch) <= 4:
                mud_count += 1
    if mud_count > 10:
        critique.append(f"⚠️ LOW-INTERVAL MUD: Detected {mud_count} tight intervals in bass (< C3). Potential for harmonic blur.")

    # 2. Spectral Collisions
    names = list(track_ranges.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            r1 = track_ranges[names[i]]
            r2 = track_ranges[names[j]]
            overlap = min(r1[1], r2[1]) - max(r1[0], r2[0])
            span = max(r1[1], r2[1]) - min(r1[0], r2[0])
            if overlap > 0 and (overlap / span) > 0.7:
                critique.append(f"ℹ️ SPECTRAL OVERLAP: '{names[i]}' and '{names[j]}' occupy very similar pitch ranges. Consider panning or different registers.")

    # 3. Lead Exhaustion
    for t_name, t_obj in tracks.items():
        if "lead" in t_name.lower() or "violin" in t_name.lower() or "flute" in t_name.lower():
            notes = sorted(t_obj.notes if hasattr(t_obj, "notes") else t_obj, key=lambda x: x.start)
            if not notes: continue
            max_continuous = 0
            curr_continuous = 0
            for k in range(1, len(notes)):
                gap = notes[k].start - (notes[k-1].start + notes[k-1].duration)
                if gap < 2.0:
                    curr_continuous += (notes[k].start - notes[k-1].start)
                else:
                    max_continuous = max(max_continuous, curr_continuous)
                    curr_continuous = 0
            if max_continuous > 32.0:
                critique.append(f"⚠️ LEAD EXHAUSTION: Track '{t_name}' plays for {max_continuous:.1f} beats without significant rest. Consider breathing space.")

    # 4. Foundation Check
    has_bass = any(r[0] < 45 for r in track_ranges.values())
    if not has_bass:
        critique.append("⚠️ THIN MIX: No significant bass foundation detected. The arrangement might sound hollow.")

    # 5. Dynamic range
    vels = [n.velocity for n in all_notes]
    if vels:
        v_span = max(vels) - min(vels)
        if v_span < 20:
            critique.append(f"ℹ️ DYNAMIC COMPRESSION: Overall velocity span is narrow ({v_span} units). Consider more expression (MIDI CC11).")

    if not critique:
        critique.append("✅ Arrangement seems balanced and clear.")
        
    return critique

def visualize_composition(comp_data, width=100, out_stream=sys.stdout):
    """Comprehensive musical analysis and visualization."""
    name = comp_data["name"]
    bpm = comp_data["bpm"]
    tracks = comp_data["tracks"]
    
    all_notes_flat = []
    max_beats = 0
    for t_obj in tracks.values():
        notes = t_obj.notes if hasattr(t_obj, "notes") else t_obj
        if notes:
            all_notes_flat.extend(notes)
            end = max(n.start + n.duration for n in notes)
            max_beats = max(max_beats, end)
    
    if max_beats == 0:
        out_stream.write(f"   [Warning] No note data found in {name}\n")
        return

    out_stream.write(f"\n{'='*width}\n")
    out_stream.write(f" COMPOSITION: {name} | BPM: {bpm} | Duration: {max_beats:.1f} beats\n")
    out_stream.write(f"{'='*width}\n")
    
    grid_width = width - 18
    
    # Header: Sections
    sections = detect_sections(tracks, max_beats, grid_width)
    section_row = [" "] * grid_width
    for start, end, label in sections:
        section_row[start] = "["
        label_text = label[:(end-start-2)]
        for j, char in enumerate(label_text):
            section_row[start+1+j] = char
        if end-start > 1: section_row[end-1] = "]"
    
    out_stream.write(f"{'Sections':<15} | {''.join(section_row)}\n")

    # Header: Harmony
    harmonies = analyze_harmonies(all_notes_flat, max_beats, grid_width)
    harmony_row = [" "] * grid_width
    last_h = ""
    for i, h in enumerate(harmonies):
        if h != last_h and h != "-":
            harmony_row[i] = h[0]
            if len(h) > 1 and i+1 < grid_width: harmony_row[i+1] = h[1:]
            last_h = h
    out_stream.write(f"{'Harmony':<15} | {''.join(harmony_row)}\n")
    
    out_stream.write("-" * width + "\n")

    # Track Layers
    for t_name, t_obj in sorted(tracks.items()):
        notes = t_obj.notes if hasattr(t_obj, "notes") else t_obj
        if not notes: continue
            
        grid = [" "] * grid_width
        heat = [" "] * grid_width
        
        pitches = [n.pitch for n in notes]
        avg_pitch = sum(pitches) / len(pitches)
        min_p, max_p = min(pitches), max(pitches)
        
        # Sample velocity and activity
        for n in notes:
            start_idx = int((n.start / max_beats) * (grid_width - 1))
            end_idx = int(((n.start + n.duration) / max_beats) * (grid_width - 1))
            
            char = "#"
            if n.pitch < 48: char = "="
            elif n.pitch > 72: char = "*"
            
            h_char = get_intensity_char(n.velocity)
            
            for i in range(start_idx, min(end_idx + 1, grid_width)):
                grid[i] = char
                # Layer intensity: if cell already has heat, keep highest
                heat[i] = h_char if h_char > heat[i] else heat[i]
        
        out_stream.write(f"{t_name:<15} |{''.join(grid)}  [{min_p}-{max_p}]\n")
        out_stream.write(f"{'  (intensity)':<15} |{''.join(heat)}  avg vel:{int(sum(n.velocity for n in notes)/len(notes))}\n")

    out_stream.write("-" * width + "\n")
    
    # Global Metrics
    # Voice Count
    voice_counts = [0] * grid_width
    onsets = [0] * grid_width
    step = max_beats / grid_width
    for i in range(grid_width):
        t_s, t_e = i * step, (i+1) * step
        active = [n for n in all_notes_flat if n.start < t_e and (n.start + n.duration) > t_s]
        voice_counts[i] = len(active)
        onsets[i] = len([n for n in all_notes_flat if t_s <= n.start < t_e])

    out_stream.write(f"{'Voices (Density)':<15} | {get_sparkline(voice_counts, max_val=max(12, max(voice_counts or [0])))}\n")
    out_stream.write(f"{'Rhythm Activity':<15} | {get_sparkline(onsets)}\n")
    out_stream.write("-" * width + "\n")

    # Critique Section
    out_stream.write("\nARRANGEMENT CRITIQUE:\n")
    critique = generate_critique(comp_data)
    for line in critique:
        out_stream.write(f" - {line}\n")

def run_script(script_path):
    """Dynamically loads and runs a script."""
    path = Path(script_path).resolve()
    if not path.exists():
        print(f"Error: Script {script_path} not found.")
        return

    print(f"Loading script: {path.name}...")
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(module)
        if hasattr(module, "main"):
            module.main()
        else:
            funcs = [f for f in dir(module) if f.startswith("produce_") and callable(getattr(module, f))]
            if funcs:
                for f_name in funcs:
                    func = getattr(module, f_name)
                    import inspect
                    sig = inspect.signature(func)
                    if len(sig.parameters) == 0: func()
    except Exception as e:
        print(f"Error during script execution: {e}")

def main():
    parser = argparse.ArgumentParser(description="Advanced Universal Melodica Arrangement Visualizer")
    parser.add_argument("script", help="Path to the Melodica script to visualize")
    parser.add_argument("--width", type=int, default=100, help="Visualization width")
    parser.add_argument("--output", help="Save output to a file (e.g. report.md)")
    
    args = parser.parse_args()
    buffer = io.StringIO()
    
    class DualWriter:
        def write(self, s):
            sys.stdout.write(s)
            buffer.write(s)
        def flush(self):
            sys.stdout.flush()

    writer = DualWriter()

    print("=" * 70)
    print("   MELODICA ADVANCED ARRANGEMENT ANALYZER")
    print("=" * 70)
    
    run_script(args.script)
    
    if not captured_compositions:
        print("\nNo composition data captured.")
    else:
        print(f"\nCaptured {len(captured_compositions)} compositions.\n")
        for comp in captured_compositions:
            visualize_composition(comp, width=args.width, out_stream=writer)
            
        legend = """
Visualization Legend:
  '=' : Low register (< 48)   '#' : Mid (48-72)   '*' : High (> 72)
  '░▒▓█' : Velocity Intensity Heatmap (light to dark)
  Sparklines: ▂▃▅▆▇ (Higher block = higher value)
"""
        writer.write(legend)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"# Melodica Arrangement Analysis Report\n\n")
            f.write(f"**Script:** `{args.script}`  \n")
            f.write(f"**Generated:** 2026-05-21  \n\n")
            f.write("```text\n")
            f.write(buffer.getvalue())
            f.write("\n```\n\n---\n*Generated by Melodica Advanced Visualizer*")
        print(f"\n[Success] Report saved to: {out_path.resolve()}")

if __name__ == "__main__":
    main()
