# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
visualize_arrangement.py — Melodica Composition Intelligence Suite.

A symbolic music interpretation system that transforms raw MIDI data into
musicological reports, orchestration diagnostics, and narrative analysis.

Usage:
    python3 scripts/visualize_arrangement.py scripts/album_dracula.py
"""

import sys
import os
import argparse
import importlib.util
import io
import math
from pathlib import Path
from collections import defaultdict, Counter

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

import melodica.midi as midi
import melodica.composer.album_pipeline as album_pipeline
from melodica import types
from melodica.detection import detect_chord, detect_scale
from melodica.utils import pitch_class

_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"]

def note_name(pc):
    """MIDI pitch class → note name."""
    return _NOTE_NAMES[pc % 12]

def get_roman(chord, key):
    """Simple Roman Numeral converter."""
    if not key: return "?"
    degs = key.degrees()
    try:
        idx = degs.index(chord.root % 12)
        num = _ROMAN[idx]
        if chord.quality == types.Quality.MINOR: return num.lower()
        if chord.quality == types.Quality.DIMINISHED: return num.lower() + "°"
        if chord.quality == types.Quality.AUGMENTED: return num + "+"
        return num
    except ValueError:
        return f"#{_ROMAN[0]}" # Simple fallback for chromatic

# Global list to store captured compositions
captured_compositions = []

def mock_export_multitrack_midi(tracks, filename, bpm=120, instruments=None, **kwargs):
    """Hook into MIDI export to capture composition data."""
    comp_info = {
        "name": Path(filename).name,
        "bpm": bpm,
        "tracks": tracks,
        "instruments": instruments or {},
        "key": kwargs.get("key")
    }
    captured_compositions.append(comp_info)
    print(f"   [Cognition] Captured composition: {comp_info['name']}")

midi.export_multitrack_midi = mock_export_multitrack_midi
album_pipeline.export_multitrack_midi = mock_export_multitrack_midi

def get_sparkline(values, max_val=None):
    """Monospace-safe Unicode sparkline."""
    if not values: return ""
    chars = " ▂▃▄▅▆▇█"
    if max_val is None:
        max_val = max(values) if max(values) > 0 else 1
    if max_val == 0: return " " * len(values)
    line = "".join([chars[max(0, min(int((v / max_val) * (len(chars) - 1)), len(chars) - 1))] for v in values])
    return line

def get_intensity_char(velocity):
    """Velocity gradient mapping."""
    if velocity < 30: return " "
    if velocity < 55: return "░"
    if velocity < 80: return "▒"
    if velocity < 105: return "▓"
    return "█"

def classify_role(name, notes, max_beats):
    """Advanced instrument role inference."""
    if not notes: return "SILENT"
    dur = max(n.start + n.duration for n in notes)
    density = len(notes) / dur
    pitches = [n.pitch for n in notes]
    avg_pitch = sum(pitches) / len(pitches)
    avg_len = sum(n.duration for n in notes) / len(notes)
    
    # Rhythmic variety (pitch recurrence)
    pc_variety = len(set(n.pitch % 12 for n in notes))
    
    name_low = name.lower()
    
    if "perc" in name_low or "drum" in name_low: return "PERC"
    if avg_pitch < 45 or "bass" in name_low: return "BASS"
    if avg_len > 6.0 or "pad" in name_low or "choir" in name_low: return "PAD"
    
    # Ostinato: high rhythmic activity, low pitch variety
    if density > 1.5 and pc_variety <= 4: return "OSTI"
    
    # Counterpoint: significant density, distinct register, not lead
    if density > 0.8 and "lead" not in name_low: return "CNTR"
    
    if density > 0.5 or "lead" in name_low or "melody" in name_low: return "LEAD"
    
    return "SUPP"

def analyze_structure_cognition(tracks, duration, width):
    """Heuristic structural segmentation using orchestration change detection."""
    step = duration / width
    fingerprints = []
    for i in range(width):
        t_s, t_e = i * step, (i+1) * step
        active = set()
        for name, t_obj in tracks.items():
            notes = t_obj.notes if hasattr(t_obj, "notes") else t_obj
            if any(n.start < t_e and n.start + n.duration > t_s for n in notes):
                active.add(name)
        fingerprints.append(frozenset(active))
        
    sections = []
    curr_start = 0
    for i in range(1, width):
        if fingerprints[i] != fingerprints[curr_start]:
            sections.append((curr_start, i, fingerprints[curr_start]))
            curr_start = i
    sections.append((curr_start, width, fingerprints[curr_start]))
    
    # Semantic Labeling
    named = []
    seen_fingerprints = {}
    label_counts = Counter()
    
    for i, (start, end, fprint) in enumerate(sections):
        if (end - start) < (width * 0.04): continue # Filter glitches
        
        # Recurrence detection
        if fprint in seen_fingerprints:
            base_label = seen_fingerprints[fprint]
            label = f"{base_label}'" # Variation
        else:
            if not fprint: label = "Silence"
            elif i == 0: label = "Intro"
            elif i == len(sections)-1: label = "Outro"
            elif len(fprint) >= len(tracks) * 0.7: label = "Climax"
            else:
                label_counts["Theme"] += 1
                label = f"Theme {_ROMAN[label_counts['Theme']-1]}"
                seen_fingerprints[fprint] = label
        
        named.append((start, end, label))
    return named

def synthesize_mood(comp_data):
    """Synthesize emotional descriptor profile."""
    bpm = comp_data["bpm"]
    key = comp_data["key"]
    tracks = comp_data["tracks"]
    
    mode_str = "Neutral"
    if key:
        if "minor" in str(key.mode).lower(): mode_str = "Minor"
        if "major" in str(key.mode).lower(): mode_str = "Major"
        if "hungarian" in str(key.mode).lower(): mode_str = "Exotic/Dark"
        
    energy = "Moderate"
    if bpm > 115: energy = "High-Energy"
    elif bpm < 75: energy = "Ambient/Slow"
    
    traits = []
    if mode_str == "Exotic/Dark": traits.append("Ritualistic")
    if energy == "High-Energy": traits.append("Relentless")
    if energy == "Ambient/Slow": traits.append("Brooding")
    
    if len(tracks) < 3: traits.append("Intimate")
    if len(tracks) > 5: traits.append("Orchestral")
    
    return f"{' / '.join(traits)} ({mode_str})"

def generate_critique_musicological(comp_data):
    """Professional musical-semantic critique engine."""
    critiques = []
    tracks = comp_data["tracks"]
    all_notes = []
    track_stats = {}
    
    for name, t_obj in tracks.items():
        notes = t_obj.notes if hasattr(t_obj, "notes") else t_obj
        if notes:
            all_notes.extend(notes)
            end = max(n.start + n.duration for n in notes)
            pitches = [n.pitch for n in notes]
            track_stats[name] = {
                "range": (min(pitches), max(pitches)),
                "role": classify_role(name, notes, end),
                "notes": notes
            }

    # 1. Orchestral Spacing (Musicological)
    low_max = max([s["range"][1] for s in track_stats.values() if s["role"] == "BASS"] or [0])
    mid_min = min([s["range"][0] for s in track_stats.values() if s["role"] in ("SUPP", "CNTR", "PAD")] or [127])
    if low_max > 0 and mid_min < 127 and (mid_min - low_max) < 7:
        critiques.append({
            "sev": "WARNING", "conf": 75,
            "msg": "NARROW ORCHESTRAL SPACING: Bass and harmony layers are clustered too tightly.",
            "reason": "Arrangement lacks vertical clarity; consider transposing the harmonic bed up one octave."
        })

    # 2. Lead Phrasing (Professional Tone)
    for name, s in track_stats.items():
        if s["role"] == "LEAD":
            sorted_n = sorted(s["notes"], key=lambda x: x.start)
            max_p = 0
            curr_p = 0
            for i in range(1, len(sorted_n)):
                gap = sorted_n[i].start - (sorted_n[i-1].start + sorted_n[i-1].duration)
                if gap < 1.5: curr_p += (sorted_n[i].start - sorted_n[i-1].start)
                else: 
                    max_p = max(max_p, curr_p)
                    curr_p = 0
            if max_p > 40:
                critiques.append({
                    "sev": "INFO", "conf": 90,
                    "msg": f"EXTENDED MELODIC EXPOSURE in '{name}': PHRASE LENGTH {max_p:.1f} BEATS.",
                    "reason": "Continuous lead phrasing may reduce expressive contrast and listener engagement."
                })

    # 3. Spectral Occupancy
    mid_count = sum(1 for n in all_notes if 50 <= n.pitch <= 70)
    if (mid_count / len(all_notes)) > 0.7:
        critiques.append({
            "sev": "WARNING", "conf": 80,
            "msg": "MIDRANGE CONGESTION DETECTED.",
            "reason": f"{int(mid_count/len(all_notes)*100)}% of note events occur in the MIDI 50-70 range, risking a 'boxy' mix."
        })

    return critiques

def visualize_composition(comp_data, width=100, out_stream=sys.stdout):
    """Primary interpretation and visualization engine."""
    name = comp_data["name"]
    bpm = comp_data["bpm"]
    tracks = comp_data["tracks"]
    key = comp_data["key"]
    
    all_notes = []
    max_beats = 0
    for t_obj in tracks.values():
        notes = t_obj.notes if hasattr(t_obj, "notes") else t_obj
        if notes:
            all_notes.extend(notes)
            max_beats = max(max_beats, max(n.start + n.duration for n in notes))
            
    if max_beats == 0: return

    out_stream.write(f"\n{'='*width}\n")
    out_stream.write(f" COMPOSITION: {name} | BPM: {bpm} | Length: {max_beats:.1f} beats\n")
    out_stream.write(f" MOOD PROFILE: {synthesize_mood(comp_data)}\n")
    out_stream.write(f"{'='*width}\n")
    
    grid_width = width - 28
    
    # 1. Structure (Novelty/Recurrence)
    sections = analyze_structure_cognition(tracks, max_beats, grid_width)
    row = [" "] * grid_width
    for s, e, label in sections:
        if e-s < 2: continue
        row[s] = "|"
        txt = label[:(e-s-1)]
        for j, c in enumerate(txt): row[s+1+j] = c
    out_stream.write(f"{'Structure':<25} | {''.join(row)}\n")

    # 2. Harmony Flow (Functional/Semantic)
    step = max_beats / 12 # Coarse steps for harmony row
    h_row = []
    last_h = None
    for i in range(12):
        t_s, t_e = i * step, (i+1) * step
        win = [n for n in all_notes if n.start < t_e and n.start + n.duration > t_s]
        chord = detect_chord(win)
        if chord:
            name_h = f"{note_name(chord.root)}{chord.quality.value}"
            func = get_roman(chord, key)
            label = f"{name_h} ({func})"
            if label != last_h:
                h_row.append(label)
                last_h = label
    out_stream.write(f"{'Harmony Flow':<25} | {' -> '.join(h_row)}\n")
    
    out_stream.write("-" * width + "\n")

    # 3. Track Layers
    track_roles = {}
    for t_name, t_obj in sorted(tracks.items()):
        notes = t_obj.notes if hasattr(t_obj, "notes") else t_obj
        if not notes: continue
        role = classify_role(t_name, notes, max_beats)
        track_roles[t_name] = role
        
        grid, heat = [" "] * grid_width, [" "] * grid_width
        pitches = [n.pitch for n in notes]
        for n in notes:
            s_idx = int((n.start / max_beats) * (grid_width - 1))
            e_idx = int(((n.start + n.duration) / max_beats) * (grid_width - 1))
            char = "#"
            if n.pitch < 48: char = "="
            elif n.pitch > 72: char = "*"
            h_char = get_intensity_char(n.velocity)
            for j in range(s_idx, min(e_idx + 1, grid_width)):
                grid[j] = char
                if h_char > heat[j]: heat[j] = h_char
        
        label = f"{t_name[:12]} [{role}]"
        out_stream.write(f"{label:<25} |{''.join(grid)}  [{min(pitches)}-{max(pitches)}]\n")
        out_stream.write(f"{'  (intensity)':<25} |{''.join(heat)}\n")

    out_stream.write("-" * width + "\n")
    
    # 4. Metrics
    voice_counts, onsets, tensions = [], [], []
    step = max_beats / grid_width
    for i in range(grid_width):
        t_s, t_e = i * step, (i+1) * step
        active = [n for n in all_notes if n.start < t_e and n.start + n.duration > t_s]
        ons = [n for n in all_notes if t_s <= n.start < t_e]
        v_c = len(active)
        o_c = len(ons)
        avg_v = sum(n.velocity for n in active)/v_c if active else 0
        voice_counts.append(v_c)
        onsets.append(o_c)
        tensions.append((v_c * 12) + (avg_v * 0.4) + (o_c * 7)) # Weighted Tension

    out_stream.write(f"{'Voices (Density)':<25} | {get_sparkline(voice_counts, 16)}\n")
    out_stream.write(f"{'Rhythm Activity':<25} | {get_sparkline(onsets)}\n")
    out_stream.write(f"{'Narrative Tension':<25} | {get_sparkline(tensions)}\n")
    
    # 5. Register Spread
    low = len([n for n in all_notes if n.pitch < 48])
    mid = len([n for n in all_notes if 48 <= n.pitch <= 72])
    high = len([n for n in all_notes if n.pitch > 72])
    tot = len(all_notes)
    out_stream.write(f"{'Register Spread':<25} | Low: {int(low/tot*100)}%  Mid: {int(mid/tot*100)}%  High: {int(high/tot*100)}%\n")
    
    out_stream.write("-" * width + "\n")

    # 6. Critique
    out_stream.write("\nCOMPOSER'S ANALYSIS & CRITIQUE:\n")
    for c in generate_critique_musicological(comp_data):
        out_stream.write(f" [{c['sev']}] {c['msg']} (Confidence: {c['conf']}%)\n")
        out_stream.write(f"   > Reasoning: {c['reason']}\n")

def generate_album_analytics(comps):
    """Synthesis of album-wide consistency."""
    if not comps: return ""
    total_beats = sum(max(n.start + n.duration for ns in c["tracks"].values() for n in (ns.notes if hasattr(ns, "notes") else ns)) for c in comps)
    avg_bpm = sum(c["bpm"] for c in comps) / len(comps)
    
    roles = Counter()
    for c in comps:
        dur = max(n.start + n.duration for ns in c["tracks"].values() for n in (ns.notes if hasattr(ns, "notes") else ns))
        for name, t_obj in c["tracks"].items():
            notes = t_obj.notes if hasattr(t_obj, "notes") else t_obj
            roles[classify_role(name, notes, dur)] += 1
            
    summary = "\n" + "="*70 + "\n"
    summary += "   ALBUM-WIDE COHESION ANALYTICS\n"
    summary += "="*70 + "\n"
    summary += f" - Composite Tempo:    {avg_bpm:.1f} BPM\n"
    summary += f" - Orchestral Focus:   " + ", ".join([f"{v}x {k}" for k, v in roles.items()]) + "\n"
    summary += f" - Key Centers:        " + ", ".join(set([str(c.get("key", "Unknown")) for c in comps])) + "\n"
    summary += "="*70 + "\n"
    return summary

def run_script(script_path):
    """Dynamic script execution."""
    path = Path(script_path).resolve()
    if not path.exists(): return
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        if hasattr(module, "main"): module.main()
        else:
            funcs = [f for f in dir(module) if f.startswith("produce_") and callable(getattr(module, f))]
            for f_name in sorted(funcs):
                func = getattr(module, f_name)
                import inspect
                if len(inspect.signature(func).parameters) == 0:
                    func()
    except Exception as e: print(f"Execution Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Melodica Composition Intelligence Suite")
    parser.add_argument("script", help="Script to interpret")
    parser.add_argument("--width", type=int, default=115, help="Report width")
    parser.add_argument("--output", help="Save report to Markdown")
    args = parser.parse_args()
    
    buffer = io.StringIO()
    class DualWriter:
        def write(self, s): sys.stdout.write(s); buffer.write(s)
        def flush(self): sys.stdout.flush()
    writer = DualWriter()

    print("=" * 70)
    print("   MELODICA COMPOSITION INTELLIGENCE SUITE")
    print("=" * 70)
    run_script(args.script)
    
    if captured_compositions:
        print(f"\nInterpreting {len(captured_compositions)} tracks...\n")
        for comp in captured_compositions:
            visualize_composition(comp, width=args.width, out_stream=writer)
        writer.write(generate_album_analytics(captured_compositions))
        
        legend = "\nLegend: '=': Bass, '#': Mid, '*': High | ░▒▓█: Intensity | ▂▃▅▆▇: Activity\n"
        writer.write(legend)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(f"# Composition Intelligence Report\n\nSource: `{args.script}`\n\n```text\n{buffer.getvalue()}\n```\n")
        print(f"\n[Success] Intelligence report saved to: {args.output}")

if __name__ == "__main__":
    main()
