# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/harmony_analyzer.py — MIDI Harmony Analysis Tool.

Analyzes MIDI files for:
- Key/Scale detection
- Chord progression identification (Roman numerals)
- Dissonance and clash statistics
- Voice leading patterns
- Harmonic density and complexity
"""

import sys
import argparse
from pathlib import Path
from collections import Counter

# Add parent dir to path to find melodica package
sys.path.insert(0, str(Path(__file__).parent.parent))

import mido
from melodica.types import NoteInfo, Scale, Mode, Quality
from melodica.theory import CHORD_TEMPLATES
from melodica.utils import nearest_pitch, snap_to_scale
from melodica.composer.harmonic_verifier import detect_clashes, VerifierConfig

# ---------------------------------------------------------------------------
# Logic: Chord Identification
# ---------------------------------------------------------------------------

def identify_chord(pitch_classes: list[int]):
    """Identify chord quality and root from a list of pitch classes."""
    if not pitch_classes:
        return None

    pcs = set(pitch_classes)
    best_match = None
    best_score = -1

    # Try each pitch class as a potential root
    for root in pcs:
        # Normalize intervals relative to this root
        intervals = sorted([(pc - root) % 12 for pc in pcs])

        # Compare against templates
        for quality, template in CHORD_TEMPLATES.items():
            # A match score based on how many notes from template are present
            # and if there are extra notes
            template_set = set(template)
            intersection = template_set.intersection(set(intervals))

            # Perfect match: all template notes present, no extras (except maybe 1-2 color tones)
            score = len(intersection) * 10 - len(set(intervals) - template_set)

            # Boost score if the root is in the template (usually 0 is there)
            if 0 in intersection:
                score += 5

            if score > best_score:
                best_score = score
                best_match = (root, quality)

    if best_match:
        root, quality = best_match
        # Return a simple object with name and root properties
        class DetectedChord:
            def __init__(self, r, q):
                self.root = r
                self.quality = q
                self.name = f"{['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][r]} {q.name}"
        return DetectedChord(root, quality)

    return None


def load_midi_notes(path: str) -> dict[str, list[NoteInfo]]:
    """Parse MIDI file into {track_name: [NoteInfo]}."""
    mid = mido.MidiFile(path)
    tracks = {}

    for track in mid.tracks:
        name = "Unknown"
        notes_on = {}  # (pitch, channel) -> (tick, velocity)
        note_list = []

        tick = 0
        for msg in track:
            tick += msg.time
            if msg.type == "track_name":
                name = msg.name
            elif msg.type == "note_on" and msg.velocity > 0:
                key = (msg.note, msg.channel)
                notes_on[key] = (tick, msg.velocity)
            elif msg.type in ("note_off",) or (msg.type == "note_on" and msg.velocity == 0):
                key = (msg.note, msg.channel)
                if key in notes_on:
                    on_tick, vel = notes_on.pop(key)
                    duration = (tick - on_tick) / mid.ticks_per_beat
                    start = on_tick / mid.ticks_per_beat
                    note_list.append(
                        NoteInfo(
                            pitch=msg.note,
                            start=round(start, 6),
                            duration=round(duration, 6),
                            velocity=vel,
                        )
                    )

        if note_list:
            tracks[name] = sorted(note_list, key=lambda n: n.start)

    return tracks, mid

# ---------------------------------------------------------------------------
# Analysis: Chord Detection
# ---------------------------------------------------------------------------

def analyze_chords(tracks: dict[str, list[NoteInfo]], ticks_per_beat: int):
    """Detect chords in slices of time."""
    # Combine all notes into a single timeline of events
    all_notes = []
    for tname, notes in tracks.items():
        # Skip percussion for harmonic analysis
        if "percussion" in tname.lower() or "drums" in tname.lower() or "timpani" in tname.lower():
            continue
        for n in notes:
            all_notes.append(n)
    
    if not all_notes:
        return []

    all_notes.sort(key=lambda n: n.start)
    max_beat = max(n.start + n.duration for n in all_notes)
    
    # Slice by beats (or half-beats)
    step = 1.0 # Analyze every 1 beat
    slices = []
    
    for t in range(0, int(max_beat), int(step)):
        beat_start = float(t)
        beat_end = beat_start + step
        
        # Get notes active in this slice
        active_pitches = set()
        for n in all_notes:
            if n.start < beat_end and (n.start + n.duration) > beat_start:
                active_pitches.add(n.pitch % 12)
        
        if not active_pitches:
            slices.append((beat_start, None))
            continue
            
        # Try to identify chord
        pcs = sorted(list(active_pitches))
        chord = identify_chord(pcs)
        slices.append((beat_start, chord))
        
    return slices

# ---------------------------------------------------------------------------
# Analysis: Key Detection
# ---------------------------------------------------------------------------

def detect_key(tracks: dict[str, list[NoteInfo]]):
    """Simple heuristic for key detection based on pitch distribution."""
    all_pcs = []
    for tname, notes in tracks.items():
        if "percussion" in tname.lower() or "drums" in tname.lower():
            continue
        for n in notes:
            all_pcs.append(n.pitch % 12)
            
    if not all_pcs:
        return None
        
    counts = Counter(all_pcs)
    # Most common pitch is likely the tonic or part of the tonic chord
    # In a more advanced version, we'd match against scale degree weights
    
    tonic = counts.most_common(1)[0][0]
    
    # Check if major or minor (3rd degree)
    third_maj = (tonic + 4) % 12
    third_min = (tonic + 3) % 12
    
    if counts[third_min] >= counts[third_maj]:
        mode = Mode.AEOLIAN
    else:
        mode = Mode.IONIAN
        
    return Scale(root=tonic, mode=mode)

# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------

def run_analysis(path: str):
    print(f"\n{'=' * 80}")
    print(f"        H A R M O N Y   A N A L Y Z E R")
    print(f"        File: {Path(path).name}")
    print(f"{'=' * 80}")

    tracks, mid = load_midi_notes(path)
    if not tracks:
        print("Error: No tracks found in MIDI file.")
        return

    # 1. Key Detection
    key = detect_key(tracks)
    print(f"\n  DETECTED KEY: {key if key else 'Unknown'}")
    
    # 2. Chord Analysis
    chords_slices = analyze_chords(tracks, mid.ticks_per_beat)
    print(f"\n  CHORD PROGRESSION (Estimated):")
    
    prog_line = ""
    last_chord_name = ""
    for beat, chord in chords_slices:
        if chord:
            chord_name = chord.name if hasattr(chord, 'name') else str(chord)
            if chord_name != last_chord_name:
                # Get Roman numeral if key is known
                roman = ""
                if key:
                    try:
                        # Attempt to find roman numeral
                        for degree in range(7):
                            root = (key.root + key.mode.value[degree]) % 12
                            if root == chord.root:
                                roman = f" [{['I','II','III','IV','V','VI','VII'][degree]}]"
                                break
                    except: pass
                
                prog_line += f"| {beat:5.1f}b: {chord_name}{roman} "
                last_chord_name = chord_name
        else:
            if last_chord_name != "N/C":
                prog_line += f"| {beat:5.1f}b: N/C "
                last_chord_name = "N/C"
                
        if len(prog_line) > 60:
            print(f"    {prog_line}")
            prog_line = ""
    if prog_line:
        print(f"    {prog_line}")

    # 3. Dissonance Analysis
    config = VerifierConfig(dissonance_tolerance=0.0) # Strict for analysis
    clashes = detect_clashes(tracks, config)
    
    print(f"\n  DISSONANCE METRICS:")
    print(f"    Total Note Clashes: {len(clashes)}")
    
    if clashes:
        iv_counts = Counter(c.interval for c in clashes)
        print(f"    Interval Distribution:")
        interval_names = {1: "m2 (Sharp)", 2: "M2 (Dissonant)", 6: "TT (Tritone)", 11: "M7 (Tense)"}
        for iv, count in sorted(iv_counts.items()):
            name = interval_names.get(iv, f"{iv} semitones")
            print(f"      - {name:20s}: {count:5d}")

    # 4. Complexity & Density
    total_notes = sum(len(n) for n in tracks.values())
    avg_poly = total_notes / (mid.length / 60 * 120 / 4) if mid.length > 0 else 0
    
    print(f"\n  DENSITY & COMPLEXITY:")
    print(f"    Total Notes: {total_notes}")
    print(f"    Harmonic Density Index: {len(chords_slices) / max(1, total_notes):.4f}")
    
    print(f"\n{'=' * 80}")
    print(f"  Analysis Complete.")
    print(f"{'=' * 80}\n")

def main():
    parser = argparse.ArgumentParser(description="Analyze MIDI harmony.")
    parser.add_argument("midi_file", help="Path to MIDI file")
    args = parser.parse_args()
    
    run_analysis(args.midi_file)

if __name__ == "__main__":
    main()
