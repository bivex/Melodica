import mido

midi_filename = "random_song.mid"
try:
    mid = mido.MidiFile(midi_filename)
    
    for i, track in enumerate(mid.tracks):
        track_name = "Unknown"
        channel = -1
        
        note_count = 0
        total_pitch = 0
        
        for msg in track:
            if msg.type == 'track_name':
                track_name = msg.name
            if hasattr(msg, 'channel'):
                channel = msg.channel
            if msg.type == 'note_on' and msg.velocity > 0:
                note_count += 1
                total_pitch += msg.note
                
        if note_count > 0:
            avg_pitch = total_pitch / note_count
            print(f"Track {i} ('{track_name}'): {note_count} notes, Avg Pitch: {avg_pitch:.1f}, Channel: {channel}")
            
except Exception as e:
    print(f"Error: {e}")
