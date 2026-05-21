# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.
# Promoted to Expert-Level Compositional Diagnostic System.

import sys
import music21
from music21 import converter, chord, key, roman, interval
from pathlib import Path

def analyze_midi(file_path):
    print(f"\n{'='*80}")
    print(f" EXPERT MUSIC21 COMPOSITIONAL & HARMONIC DIAGNOSTIC SUITE")
    print(f" Target: {file_path}")
    print(f"{'='*80}")
    
    try:
        # Load MIDI file
        s = converter.parse(file_path)
        
        # =====================================================================
        # 1. KEY DETECTION & TONAL STABILITY
        # =====================================================================
        print("\n[1] TONAL ANALYSIS & STABILITY")
        overall_key = s.analyze('key')
        print(f"  - Overall Detected Key: {overall_key}")
        print(f"  - Key Detection Confidence: {overall_key.correlationCoefficient:.3f}")
        
        # Segmental Analysis (4 quarters of the timeline)
        total_duration = s.duration.quarterLength
        if total_duration > 0:
            print("  - Segmental Modulation Check (Track split into quarters):")
            quarter = total_duration / 4.0
            for q in range(4):
                start = q * quarter
                end = (q + 1) * quarter
                seg_notes = []
                for p in s.parts:
                    for n in p.recurse().notes:
                        if start <= n.offset < end:
                            seg_notes.append(n)
                if seg_notes:
                    try:
                        seg_stream = music21.stream.Stream(seg_notes)
                        seg_key = seg_stream.analyze('key')
                        print(f"    * Q{q+1} ({start:5.1f} - {end:5.1f} beats): {seg_key} (conf: {seg_key.correlationCoefficient:.2f})")
                    except Exception:
                        print(f"    * Q{q+1} ({start:5.1f} - {end:5.1f} beats): Undetermined (too few notes)")
                else:
                    print(f"    * Q{q+1} ({start:5.1f} - {end:5.1f} beats): Silent / Empty")
        
        # =====================================================================
        # 2. AMBITUS & PITCH REGISTERS
        # =====================================================================
        print("\n[2] AMBITUS & REGISTER ANALYSIS")
        ranges = []
        for i, part in enumerate(s.parts):
            notes = part.recurse().notes
            pitches = [n.pitch.ps for n in notes if n.isNote]
            if pitches:
                p_min = music21.pitch.Pitch(min(pitches)).nameWithOctave
                p_max = music21.pitch.Pitch(max(pitches)).nameWithOctave
                span = max(pitches) - min(pitches)
                ranges.append((i, part.id, min(pitches), max(pitches), p_min, p_max))
                print(f"  - Track {i} ({part.id or f'Track_{i}'}): {p_min} to {p_max} (Ambitus: {int(span)} semitones)")
        
        # Register crossover warnings
        overlap_warnings = 0
        for i in range(len(ranges)):
            for j in range(i + 1, len(ranges)):
                idx1, id1, min1, max1, p_min1, p_max1 = ranges[i]
                idx2, id2, min2, max2, p_min2, p_max2 = ranges[j]
                # If track indices are ordered but ranges cross extensively
                if (idx1 < idx2 and min1 > max2) or (idx1 > idx2 and min2 > max1):
                    # Tracks are inverted in typical order (assuming track 0 is soprano / melody)
                    pass
                # Check for absolute overlapping ranges
                overlap = min(max1, max2) - max(min1, min2)
                if overlap > 12: # Overlap of more than an octave
                    print(f"    [!] WARNING: Strong register crossover/blur between Track {idx1} and Track {idx2} ({int(overlap)} semitones of overlap)")
                    overlap_warnings += 1

        # =====================================================================
        # 3. HORIZONTAL MELODIC ANALYSIS
        # =====================================================================
        print("\n[3] MELODIC MOTION & COUNTERPOINT RESOLUTION")
        for i, part in enumerate(s.parts):
            notes = [n for n in part.recurse().notes if n.isNote]
            notes.sort(key=lambda n: n.offset)
            
            if len(notes) < 2:
                continue
                
            steps = 0
            leaps = 0
            large_leaps = 0
            resolved_leaps = 0
            
            for idx in range(len(notes) - 1):
                p1 = notes[idx].pitch.ps
                p2 = notes[idx + 1].pitch.ps
                diff = abs(p2 - p1)
                
                if diff == 0:
                    continue
                elif diff <= 2:  # Whole/half steps
                    steps += 1
                else:
                    leaps += 1
                    if diff > 8:  # Large leap (> minor 6th)
                        large_leaps += 1
                        # Check leap resolution: next note should move in the opposite direction
                        if idx + 2 < len(notes):
                            p3 = notes[idx + 2].pitch.ps
                            dir1 = p2 - p1
                            dir2 = p3 - p2
                            # Opposite directions
                            if (dir1 > 0 and dir2 < 0) or (dir1 < 0 and dir2 > 0):
                                resolved_leaps += 1
            
            total_motion = steps + leaps
            if total_motion > 0:
                step_ratio = steps / total_motion
                leap_ratio = leaps / total_motion
                resolution_pct = (resolved_leaps / large_leaps * 100) if large_leaps > 0 else 100.0
                print(f"  - Track {i} ({part.id or f'Track_{i}'}):")
                print(f"    * Stepwise Motion: {step_ratio*100:4.1f}% | Leaps: {leap_ratio*100:4.1f}%")
                if large_leaps > 0:
                    print(f"    * Large Leaps (> 8 semitones): {large_leaps} ({resolved_leaps} resolved in opposite direction — {resolution_pct:4.1f}% resolution rate)")
                    if resolution_pct < 60.0:
                        print("      [!] Note: Consider resolving large leaps in the opposite direction for more natural/vocal melody contours.")

        # =====================================================================
        # 4. CHORDAL PROGRESSION & CLASSICAL ROMAN ANALYSIS
        # =====================================================================
        chords = s.chordify()
        print("\n[4] CHORD PROGRESSION ANALYSIS")
        chord_sequence = []
        last_figure = None
        for c in chords.recurse().getElementsByClass(music21.chord.Chord):
            if c.duration.quarterLength < 0.5: 
                continue
            try:
                rn = roman.romanNumeralFromChord(c, overall_key)
                if rn.figure != last_figure:
                    chord_sequence.append(f"{rn.figure} ({c.pitchedCommonName})")
                    last_figure = rn.figure
            except Exception:
                continue
            if len(chord_sequence) >= 12: 
                break
        
        if chord_sequence:
            print("  - Discovered Progression Sequence (First 12 changes):")
            print("    " + " -> ".join(chord_sequence))
        else:
            print("  - Discovered Progression Sequence: [No clear progression]")

        # =====================================================================
        # 5. VERTICAL HARMONIC INTERVAL QUALITY (Consonance vs Dissonance)
        # =====================================================================
        print("\n[5] HARMONIC CONSONANCE & DISSONANCE PROFILE")
        pure_consonance = 0
        imperfect_consonance = 0
        mild_dissonance = 0
        sharp_dissonance = 0
        total_intervals = 0
        
        for c in chords.recurse().getElementsByClass(music21.chord.Chord):
            if len(c.pitches) < 2: 
                continue
            for i in range(len(c.pitches)):
                for j in range(i + 1, len(c.pitches)):
                    iv_obj = interval.Interval(c.pitches[i], c.pitches[j])
                    semi = iv_obj.semitones % 12
                    total_intervals += 1
                    
                    if semi in (0, 7):  # Unison, Octave, Perfect Fifth
                        pure_consonance += 1
                    elif semi in (3, 4, 8, 9):  # Minor/Major Thirds, Minor/Major Sixths
                        imperfect_consonance += 1
                    elif semi == 5:  # Perfect Fourth
                        mild_dissonance += 1
                    elif semi in (2, 10):  # Major Second, Minor Seventh
                        mild_dissonance += 1
                    elif semi in (1, 6, 11):  # Minor Second, Tritone, Major Seventh
                        sharp_dissonance += 1

        if total_intervals > 0:
            pure_pct = pure_consonance / total_intervals * 100
            imp_pct = imperfect_consonance / total_intervals * 100
            mild_pct = mild_dissonance / total_intervals * 100
            sharp_pct = sharp_dissonance / total_intervals * 100
            consonant_pct = pure_pct + imp_pct
            dissonant_pct = mild_pct + sharp_pct
            
            print(f"  - Consonance Profile: {consonant_pct:4.1f}% Consonant | {dissonant_pct:4.1f}% Dissonant")
            print(f"    * Pure Consonances (Octaves/Fifths): {pure_pct:4.1f}%")
            print(f"    * Imperfect Consonances (Thirds/Sixths): {imp_pct:4.1f}%")
            print(f"    * Mild Dissonances (Fourths/Seconds/Sevenths): {mild_pct:4.1f}%")
            print(f"    * Sharp Dissonances (Tritones/Minor Seconds/Major Sevenths): {sharp_pct:4.1f}%")
            
            if sharp_pct > 15.0:
                print("    [!] WARNING: Very high sharp dissonance ratio. Ensure this is stylistic (e.g. Modern Jazz, Phonk or Avant-Garde).")
        else:
            print("  - Consonance Profile: No overlapping vertical intervals detected.")

        # =====================================================================
        # 6. LOW-INTERVAL MUD (LIM) DETECTION
        # =====================================================================
        print("\n[6] LOW-INTERVAL MUD (LIM) CHECKS")
        mud_count = 0
        for c in chords.recurse().getElementsByClass(music21.chord.Chord):
            if len(c.pitches) < 2: 
                continue
            # Sort pitches lowest to highest
            sorted_pitches = sorted(c.pitches, key=lambda p: p.ps)
            for i in range(len(sorted_pitches) - 1):
                p1 = sorted_pitches[i]
                p2 = sorted_pitches[i+1]
                # Check if bottom note is below C3 (MIDI 48)
                if p1.ps < 48:
                    diff = p2.ps - p1.ps
                    if 0 < diff <= 4:  # Seconds/Thirds/Fourths in extreme bass
                        mud_count += 1
                        if mud_count <= 8:
                            print(f"  - LIM warning at beat {float(c.offset):5.1f}: Interval of {int(diff)} semitones between {p1.nameWithOctave} and {p2.nameWithOctave}")
        
        if mud_count > 0:
            print(f"  - Total Low-Interval Mud warnings: {mud_count}")
            print("    [!] TIP: Move bass voice to open octaves/fifths and avoid thirds/seconds below C3 for clearer mixes.")
        else:
            print("  - Low-Interval Mud: 0 warnings (Bass register is perfectly clean and open!)")

        # =====================================================================
        # 7. TAILORED SUITE RECOMMENDATIONS
        # =====================================================================
        print("\n[7] TAILORED ACTIONS TO IMPROVE COMPOSITION QUALITY")
        actions = []
        if mud_count > 3:
            actions.append("- Fix Low-Interval Mud by thinning out the bass track or transposing the third of the chord an octave up.")
        if overlap_warnings > 2:
            actions.append("- Prevent Range Overlap/Blur by setting strict instrument octave shifts or narrowing ambitus limits in layout.py.")
        if total_intervals > 0 and sharp_pct > 10.0:
            actions.append("- Smooth out Sharp Dissonances by enabling tension curves or decreasing the verifier's dissonance_tolerance (e.g., to 0.35).")
        
        # Check leap resolution rates
        low_resolution = False
        for i, part in enumerate(s.parts):
            notes = [n for n in part.recurse().notes if n.isNote]
            notes.sort(key=lambda n: n.offset)
            if len(notes) < 3: continue
            large_leaps = 0
            resolved = 0
            for idx in range(len(notes) - 1):
                diff = abs(notes[idx+1].pitch.ps - notes[idx].pitch.ps)
                if diff > 8:
                    large_leaps += 1
                    if idx + 2 < len(notes):
                        dir1 = notes[idx+1].pitch.ps - notes[idx].pitch.ps
                        dir2 = notes[idx+2].pitch.ps - notes[idx+1].pitch.ps
                        if (dir1 > 0 and dir2 < 0) or (dir1 < 0 and dir2 > 0):
                            resolved += 1
            if large_leaps > 2 and (resolved / large_leaps) < 0.6:
                low_resolution = True
        
        if low_resolution:
            actions.append("- Improve Melodic Contour: Ensure wide leaps in the melody are immediately resolved by stepwise motion in the opposite direction.")
        
        if overall_key.correlationCoefficient < 0.50:
            actions.append("- Strengthen Key Confidence: Ensure your melody generator adheres strictly to scale degrees or utilize modal mixture more intentionally.")

        if not actions:
            print("  - Perfect! The composition is highly balanced, clean, consonant, and structurally sound.")
        else:
            for act in actions:
                print(f"  {act}")

    except Exception as e:
        print(f"Error during deep analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "output/pro_showcase/pro_showcase_demo.mid"
    analyze_midi(target)
