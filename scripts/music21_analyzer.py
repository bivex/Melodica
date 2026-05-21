import sys
import music21
from music21 import converter, chord, key, roman, analysis
from pathlib import Path

def analyze_midi(file_path):
    print(f"\n{'='*70}")
    print(f"DEEP ANALYSIS (music21): {file_path}")
    print(f"{'='*70}")
    
    try:
        # Load MIDI
        s = converter.parse(file_path)
        
        # 1. Key Detection
        detected_key = s.analyze('key')
        print(f"Detected Key: {detected_key}")
        print(f"Confidence: {detected_key.correlationCoefficient:.3f}")
        
        # 2. Ambitus (Range)
        print("\nAmbitus (Range):")
        for i, part in enumerate(s.parts):
            notes = part.recurse().notes
            pitches = [n.pitch.ps for n in notes if n.isNote]
            if pitches:
                p_min = music21.pitch.Pitch(min(pitches)).nameWithOctave
                p_max = music21.pitch.Pitch(max(pitches)).nameWithOctave
                print(f"  Track {i} ({part.id}): {p_min} to {p_max}")

        # 3. Chordal Analysis
        chords = s.chordify()
        print("\nChord Progression (First 10 distinct):")
        chord_sequence = []
        last_figure = None
        for c in chords.recurse().getElementsByClass(music21.chord.Chord):
            if c.duration.quarterLength < 0.5: continue
            rn = roman.romanNumeralFromChord(c, detected_key)
            if rn.figure != last_figure:
                chord_sequence.append(f"{rn.figure} ({c.pitchedCommonName})")
                last_figure = rn.figure
            if len(chord_sequence) >= 10: break
        
        print("  " + " -> ".join(chord_sequence))

        # 4. Harmonic Intervals (Check for density/clutter)
        print("\nSimultaneous Interval Analysis (Vertical Density):")
        interval_counts = {}
        for c in chords.recurse().getElementsByClass(music21.chord.Chord):
            if len(c.pitches) < 2: continue
            for i in range(len(c.pitches)):
                for j in range(i + 1, len(c.pitches)):
                    iv = music21.interval.Interval(c.pitches[i], c.pitches[j])
                    name = iv.niceName
                    interval_counts[name] = interval_counts.get(name, 0) + 1
        
        # Sort by frequency
        sorted_intervals = sorted(interval_counts.items(), key=lambda x: x[1], reverse=True)
        for name, count in sorted_intervals[:8]:
            print(f"  - {name}: {count} occurrences")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "output/pro_showcase/pro_showcase_demo.mid"
    analyze_midi(target)
