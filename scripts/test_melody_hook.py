# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/test_melody_hook.py — CLI tool to evaluate and test melody hook memorability.

Analyzes generated melodies against 5 key dimensions of memorability:
  1. Rhythm (40%)
  2. Contour / Shape (25%)
  3. Repetition & Evolution (20%)
  4. Unexpectedness / Leaps (10%)
  5. Harmonization Resolution (5%)
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from melodica.types import Scale, Mode, parse_progression, NoteInfo
from melodica.generators.lorn_hook import LornHookGenerator


def evaluate_memorability(notes: list[NoteInfo], key: Scale, duration_beats: float) -> dict:
    if not notes:
        return {"score": 0, "metrics": {}, "suggestions": ["No notes generated."]}

    suggestions = []
    
    # Sort notes chronologically
    notes = sorted(notes, key=lambda n: n.start)
    
    # Group notes into 1-bar chunks (every 4 beats)
    bars = {}
    for n in notes:
        bar_idx = int(n.start // 4.0)
        if bar_idx not in bars:
            bars[bar_idx] = []
        bars[bar_idx].append(n)
        
    active_bars = len(bars)
    total_bars = int(duration_beats // 4.0)
    
    # ----------------------------------------------------
    # 1. RHYTHM (40%)
    # - Syncopation variety
    # - Note duration consistency
    # - Silence & breathing space (Target: 30% - 60% silence for contrast)
    # ----------------------------------------------------
    rhythm_score = 0
    
    # Duration occurrences
    durations = [round(n.duration, 2) for n in notes]
    unique_durs = set(durations)
    
    # Syncopations (notes starting on offbeats)
    syncopated_count = sum(1 for n in notes if (n.start % 1.0) != 0.0)
    syncopation_ratio = syncopated_count / len(notes) if notes else 0.0
    
    # Silence Ratio
    silence_ratio = (total_bars - active_bars) / total_bars if total_bars else 0.0
    
    # Rhythmic scoring logic
    if len(unique_durs) >= 2:
        rhythm_score += 15  # Good duration contrast
    else:
        suggestions.append("Rhythm: Add variety to note durations (e.g. mix short quarters with long sustained notes).")
        
    if 0.15 <= syncopation_ratio <= 0.60:
        rhythm_score += 15  # Nice syncopation sweet spot
    else:
        suggestions.append("Rhythm: Adjust syncopation. Too many straight onbeats feel robotic; too many offbeats feel chaotic.")
        
    if 0.30 <= silence_ratio <= 0.65:
        rhythm_score += 10  # Perfect breathing room
    else:
        if silence_ratio < 0.30:
            suggestions.append("Rhythm: Leave more silent bars. Continuous playing exhausts the listener.")
        else:
            suggestions.append("Rhythm: Gaps are too long; the listener will lose the melody thread.")
            
    # ----------------------------------------------------
    # 2. CONTOUR & SHAPE (25%)
    # - Direction changes (up/down)
    # - Step vs Leap ratio (Target: 20-40% leaps, 60-80% steps)
    # ----------------------------------------------------
    contour_score = 0
    intervals = []
    directions = []
    
    for i in range(len(notes) - 1):
        diff = notes[i+1].pitch - notes[i].pitch
        intervals.append(abs(diff))
        if diff > 0:
            directions.append(1)
        elif diff < 0:
            directions.append(-1)
            
    # Direction changes
    dir_changes = 0
    for i in range(len(directions) - 1):
        if directions[i] != directions[i+1]:
            dir_changes += 1
            
    # Step vs Leap
    step_count = sum(1 for ivl in intervals if 1 <= ivl <= 2)
    leap_count = sum(1 for ivl in intervals if ivl > 2)
    total_intervals = len(intervals) if intervals else 1
    
    leap_ratio = leap_count / total_intervals
    
    if dir_changes >= 2:
        contour_score += 10  # Up-and-down contour helps memorability
    else:
        suggestions.append("Contour: The melody is too flat or monotonic. Try moving pitch direction up and down.")
        
    if 0.15 <= leap_ratio <= 0.45:
        contour_score += 15  # Balanced leaps and steps
    else:
        if leap_ratio < 0.15:
            suggestions.append("Contour: Add a wide interval jump (e.g. perfect 5th or octave) to break stepwise monotony.")
        else:
            suggestions.append("Contour: Too many leaps. The melody feels disjointed; use steps to connect jumps.")
            
    # ----------------------------------------------------
    # 3. REPETITION & MOTIVIC EVOLUTION (20%)
    # - Hook returns
    # - Micro-variations
    # ----------------------------------------------------
    rep_score = 0
    
    # We compare note counts and average pitches of active bars to see if the theme returns
    bar_profiles = []
    for b_idx in sorted(bars.keys()):
        b_notes = bars[b_idx]
        note_count = len(b_notes)
        avg_pitch = sum(n.pitch for n in b_notes) / note_count if b_notes else 0
        bar_profiles.append((note_count, round(avg_pitch, 1)))
        
    unique_profiles = set(bar_profiles)
    repetitions = len(bar_profiles) - len(unique_profiles)
    
    if len(bar_profiles) >= 4:
        rep_score += 10  # Motif returned enough times
    else:
        suggestions.append("Repetition: Repeat the main motif more times. Listeners need exposure to register it.")
        
    if 1 <= len(unique_profiles) <= 4:
        rep_score += 10  # Good variations (not copy-paste, not totally different)
    else:
        if len(unique_profiles) == 1:
            suggestions.append("Repetition: Add variations. A literal copy-paste loop becomes boring quickly.")
        else:
            suggestions.append("Repetition: Too many completely different phrases. Maintain one central theme.")
            
    # ----------------------------------------------------
    # 4. UNEXPECTEDNESS & EXPRESSIVITY (10%)
    # - Presence of expressive leaps (Perfect 5th, Octave, Min 7th)
    # ----------------------------------------------------
    surprise_score = 0
    expressive_leaps = {5, 7, 8, 10, 12}  # 4th, 5th, m6, m7, Octave
    has_surprise = any(ivl in expressive_leaps for ivl in intervals)
    
    if has_surprise:
        surprise_score += 10  # Signature leap found!
    else:
        suggestions.append("Unexpectedness: Add a signature intervals leap (like +7 kvinte or +12 octave) to capture attention.")
        
    # ----------------------------------------------------
    # 5. RESOLUTION (5%)
    # - Stabilizing final notes
    # ----------------------------------------------------
    resolution_score = 0
    if notes:
        last_pitch = int(notes[-1].pitch)
        stable_degrees = {key.root, (key.root + 7) % 12, (key.root + 4) % 12}
        if (last_pitch % 12) in stable_degrees:
            resolution_score += 5  # Resolves stably
        else:
            suggestions.append("Resolution: End the melody on a stable tonic (root) or dominant (5th) note to resolve tension.")

    total_score = rhythm_score + contour_score + rep_score + surprise_score + resolution_score
    
    return {
        "score": total_score,
        "metrics": {
            "rhythm": rhythm_score,
            "contour": contour_score,
            "repetition": rep_score,
            "unexpectedness": surprise_score,
            "resolution": resolution_score,
            "silence_ratio": silence_ratio,
            "leap_ratio": leap_ratio,
            "syncopation_ratio": syncopation_ratio,
            "active_bars": active_bars,
            "total_notes": len(notes),
        },
        "suggestions": suggestions
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate a generated melody hook's memorability.")
    parser.add_argument("--root", type=int, default=0, help="Scale root pitch class (0 = C, 1 = C#, etc.)")
    parser.add_argument("--mode", type=str, default="phrygian", help="Scale mode (minor, phrygian, aeolian, etc.)")
    parser.add_argument("--octave", type=int, default=5, help="Lead MIDI octave")
    parser.add_argument("--hook-len", type=int, default=5, help="Hook length (number of notes)")
    parser.add_argument("--dur", type=float, default=128.0, help="Duration in beats (default 128)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for generation")
    args = parser.parse_args()

    mode_map = {
        "minor": Mode.NATURAL_MINOR,
        "phrygian": Mode.PHRYGIAN,
        "aeolian": Mode.AEOLIAN,
        "locrian": Mode.LOCRIAN,
        "harmonic_minor": Mode.HARMONIC_MINOR,
        "hungarian_minor": Mode.HUNGARIAN_MINOR,
    }
    
    sel_mode = mode_map.get(args.mode.lower(), Mode.PHRYGIAN)
    key = Scale(root=args.root, mode=sel_mode)
    
    # Generate simple test chord progression
    chords = parse_progression("i:4 VI:4 iv:4 v:4 " * 32, key)
    
    print("\n" + "=" * 60)
    print("   M E L O D Y   H O O K   A N A L Y Z E R")
    print("=" * 60)
    print(f"Scale: {args.root} {args.mode.upper()}")
    print(f"Octave: {args.octave} | Hook Length: {args.hook_len}")
    print(f"Duration: {args.dur} beats (approx. {args.dur/4:.0f} bars)")
    print(f"Seed: {args.seed if args.seed is not None else 'Random'}")
    print("-" * 60)

    # Generate hook notes
    gen = LornHookGenerator(
        hook_length=args.hook_len,
        octave=args.octave,
        seed=args.seed,
    )
    notes = gen.render(chords, key, args.dur)
    
    # Evaluate
    eval_res = evaluate_memorability(notes, key, args.dur)
    score = eval_res["score"]
    metrics = eval_res["metrics"]
    
    # Renders the ASCII Dashboard
    def get_progress_bar(val: int, max_val: int) -> str:
        blocks = int((val / max_val) * 10)
        return "█" * blocks + "░" * (10 - blocks)

    print(f"\nHOOK MEMORABILITY SCORE: {score} / 100")
    if score >= 80:
        print("Rating: 🏆 EXCELLENT (Catchy, balanced, highly memorable)")
    elif score >= 60:
        print("Rating: 👍 GOOD (Solid hooks, could use slight tweaking)")
    else:
        print("Rating: ⚠️ WEAK (Monotonic, lacks contrast or repetitions)")
        
    print("\nBreakdown:")
    print(f"  Rhythm (Max 40)        : {metrics['rhythm']:>2} [{get_progress_bar(metrics['rhythm'], 40)}] - Silence: {metrics['silence_ratio']*100:.0f}%, Sync: {metrics['syncopation_ratio']*100:.0f}%")
    print(f"  Contour (Max 25)       : {metrics['contour']:>2} [{get_progress_bar(metrics['contour'], 25)}] - Leap ratio: {metrics['leap_ratio']*100:.0f}%")
    print(f"  Repetition (Max 20)    : {metrics['repetition']:>2} [{get_progress_bar(metrics['repetition'], 20)}] - Active bars: {metrics['active_bars']}")
    print(f"  Unexpectedness (Max 10): {metrics['unexpectedness']:>2} [{get_progress_bar(metrics['unexpectedness'], 10)}]")
    print(f"  Resolution (Max 5)     : {metrics['resolution']:>2} [{get_progress_bar(metrics['resolution'], 5)}]")
    
    print(f"\nStats: Total notes generated = {metrics['total_notes']}")
    
    if eval_res["suggestions"]:
        print("\nSuggestions for improvement:")
        for sug in eval_res["suggestions"]:
            print(f"  * {sug}")
    else:
        print("\nSuggestions for improvement: None! The hook matches all stylistic criteria.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
