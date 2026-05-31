import urllib.request
import json
import mido
import os

# 1. Get random MIDI info
print("Fetching random MIDI info...")
req = urllib.request.Request("https://bitmidi.com/api/midi/random", headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())

download_path = data['result']['result']['downloadUrl']
full_url = "https://bitmidi.com" + download_path
name = data['result']['result']['name']

print(f"Chosen song: {name}")
print(f"Downloading from: {full_url}")

# 2. Download the file
midi_filename = "random_song.mid"
req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    with open(midi_filename, 'wb') as f:
        f.write(response.read())

print("Download complete. Analyzing structure...\n")

# 3. Analyze MIDI structure
try:
    mid = mido.MidiFile(midi_filename)
    print(f"MIDI Type: {mid.type}")
    print(f"Ticks per beat: {mid.ticks_per_beat}")
    print(f"Number of tracks: {len(mid.tracks)}\n")

    for i, track in enumerate(mid.tracks):
        track_name = "Unknown"
        channels = set()
        programs = set()
        msg_count = len(track)
        
        for msg in track:
            if msg.type == 'track_name':
                track_name = msg.name
            if hasattr(msg, 'channel'):
                channels.add(msg.channel)
            if msg.type == 'program_change':
                programs.add(msg.program)
                
        print(f"Track {i}: '{track_name}'")
        print(f"  Messages: {msg_count}")
        if channels:
            print(f"  Channels: {sorted(list(channels))}")
        if programs:
            print(f"  Instruments (Program Changes): {sorted(list(programs))}")
        print()
except Exception as e:
    print(f"Error parsing MIDI: {e}")
