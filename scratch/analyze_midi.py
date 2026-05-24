import mido
from collections import defaultdict

def analyze(midi_file):
    mid = mido.MidiFile(midi_file)
    print(f"Loaded {midi_file}")
    
    total_anomalies = 0
    for i, track in enumerate(mid.tracks):
        active_notes = {}
        anomalies = []
        abs_time = 0
        
        for msg in track:
            abs_time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                if msg.note in active_notes:
                    anomalies.append(f"Note {msg.note} started again at {abs_time}. Prev: {active_notes[msg.note]}")
                active_notes[msg.note] = abs_time
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in active_notes:
                    del active_notes[msg.note]
        
        if anomalies:
            print(f"  Track {i} ({track.name}): {len(anomalies)} anomalies")
            total_anomalies += len(anomalies)
            for a in anomalies[:2]:
                print(f"    {a}")
                
    if total_anomalies == 0:
        print("SUCCESS: 0 anomalies found in all tracks!")
            
analyze("output/demo_pro_structure/Pro_Structure_Masterclass.mid")
