import mido
from collections import Counter

midi_filename = "random_song.mid"
melody_track_idx = 1 # 'Anderson Vox'

try:
    mid = mido.MidiFile(midi_filename)
    track = mid.tracks[melody_track_idx]
    
    # 1. Extract sequence of notes
    notes = []
    current_time = 0
    
    for msg in track:
        current_time += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            notes.append(msg.note)

    print(f"Total notes in melody: {len(notes)}")
    
    # 2. Find repeating intervals (relative pitch changes) 
    # This is better than exact pitches because a pattern might be transposed
    intervals = []
    for i in range(1, len(notes)):
        intervals.append(notes[i] - notes[i-1])
        
    # 3. Search for repeating n-grams (sequences of intervals)
    print("\nMost common repeating melodic patterns (based on intervals):")
    
    # Look for sequences of 5 notes (which means 4 intervals)
    seq_length = 4 
    ngrams = []
    for i in range(len(intervals) - seq_length + 1):
        ngrams.append(tuple(intervals[i:i+seq_length]))
        
    counts = Counter(ngrams)
    
    # Print the top 5 most common patterns
    for pattern, count in counts.most_common(5):
        if count > 1: # Only care if it repeats
            # Convert interval pattern back to a relative example (starting at 0)
            example_notes = [0]
            for interval in pattern:
                example_notes.append(example_notes[-1] + interval)
            print(f"Pattern relative sequence {example_notes} - Repeats {count} times")
            
    print("\nMost common exact pitch sequences (5 notes):")
    exact_ngrams = []
    for i in range(len(notes) - 5 + 1):
        exact_ngrams.append(tuple(notes[i:i+5]))
        
    exact_counts = Counter(exact_ngrams)
    for pattern, count in exact_counts.most_common(5):
        if count > 1:
            print(f"Pitches {pattern} - Repeats {count} times")

except Exception as e:
    print(f"Error: {e}")
