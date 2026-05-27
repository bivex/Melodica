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

import numpy as np
from melodica.theory.modes import MODE_DATABASE, Mode
from melodica.detection import _KS_MAJOR, _KS_MINOR

# ---------------------------------------------------------------------------
# Logic: Modal Key Detection (Expanded Krumhansl-Schmuckler)
# ---------------------------------------------------------------------------

def get_modal_profile(mode: Mode) -> np.ndarray:
    """Generate a pseudo-KS profile for any mode based on its intervals."""
    profile = np.zeros(12)
    intervals = MODE_DATABASE[mode].intervals
    # Basic weighting: Tonic=5.0, Fifths=4.0, Others=3.0, Non-scale=0.5
    for iv in range(12):
        if iv in intervals:
            if iv == 0: profile[iv] = 6.0
            elif iv == 7: profile[iv] = 5.0
            elif iv in {3, 4}: profile[iv] = 4.5
            else: profile[iv] = 3.5
        else:
            profile[iv] = 1.0
    return profile

def detect_key_modal(notes: list[NoteInfo], window: tuple[float, float] | None = None):
    """
    Advanced key detection supporting all modes and time windows.
    """
    if not notes:
        return None, 0.0

    histogram = np.zeros(12)
    total_dur = 0.0
    
    for n in notes:
        if window:
            start = max(n.start, window[0])
            end = min(n.start + n.duration, window[1])
            if start >= end: continue
            dur = end - start
        else:
            dur = n.duration
            
        histogram[n.pitch % 12] += dur
        total_dur += dur

    if total_dur == 0:
        return None, 0.0

    histogram /= total_dur

    best_corr = -2.0
    best_scale = None

    # Check common modes first for speed, then others
    check_modes = [Mode.MAJOR, Mode.AEOLIAN, Mode.DORIAN, Mode.PHRYGIAN, Mode.LYDIAN, Mode.MIXOLYDIAN, Mode.LOCRIAN, Mode.HARMONIC_MINOR]
    
    for root in range(12):
        rotated = np.roll(histogram, -root)
        for mode in check_modes:
            if mode == Mode.MAJOR: profile = _KS_MAJOR
            elif mode == Mode.AEOLIAN: profile = _KS_MINOR
            else: profile = get_modal_profile(mode)
            
            corr = float(np.corrcoef(rotated, profile)[0, 1])
            if corr > best_corr:
                best_corr = corr
                best_scale = Scale(root=root, mode=mode)

    return best_scale, best_corr

# ---------------------------------------------------------------------------
# Logic: Modulation Analysis
# ---------------------------------------------------------------------------

def analyze_modulations(tracks: dict[str, list[NoteInfo]], duration: float):
    """Detect key changes over time using a sliding window."""
    all_notes = [n for notes in tracks.values() for n in notes]
    
    window_size = 16.0 # 4 bars
    step_size = 4.0   # 1 bar
    
    modulations = []
    last_key = None
    
    for t in np.arange(0, duration, step_size):
        key, confidence = detect_key_modal(all_notes, window=(t, t + window_size))
        if key and (last_key is None or key.root != last_key.root or key.mode != last_key.mode):
            if confidence > 0.6: # Only record high-confidence changes
                modulations.append((t, key, confidence))
                last_key = key
                
    return modulations

# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------

def run_analysis(path: str):
    print(f"\n{'=' * 80}")
    print(f"        H A R M O N Y   A N A L Y Z E R   v2.0")
    print(f"        File: {Path(path).name}")
    print(f"{'=' * 80}")

    tracks, mid = load_midi_notes(path)
    if not tracks:
        print("Error: No tracks found in MIDI file.")
        return

    all_notes = [n for nt in tracks.values() for n in nt]
    duration_beats = mid.length * 120 / 60 # Approx for analysis

    # 1. Key & Modulation Detection
    main_key, confidence = detect_key_modal(all_notes)
    modulations = analyze_modulations(tracks, mid.length * 120 / 60)
    
    print(f"\n  DETECTED MAIN KEY: {main_key if main_key else 'Unknown'}")
    print(f"  Confidence: {confidence:.2f}")
    
    if len(modulations) > 1:
        print(f"\n  MODULATIONS DETECTED:")
        for t, k, c in modulations:
            print(f"    - At {t:5.1f}b: {str(k):30s} (Confidence: {c:.2f})")
    
    # Use the first detected key as the global key for chord analysis if needed
    key = main_key

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
