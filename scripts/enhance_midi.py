#!/usr/bin/env python3
"""
enhance_midi.py — Post-processing script to add professional expression and humanization to MIDI.
Adds jitter to note timing and CC11 (Expression) swells to long notes.
"""

import sys
import math
import random
from pathlib import Path
import mido

def enhance_midi(input_path: str, output_path: str, jitter_ms: float = 15.0, cc_interval_ticks: int = 40):
    mid = mido.MidiFile(input_path)
    new_mid = mido.MidiFile(ticks_per_beat=mid.ticks_per_beat)
    
    tpb = mid.ticks_per_beat
    # Convert jitter_ms to ticks (assuming 120 BPM for simplicity: 500ms per beat)
    # 1 beat = tpb ticks = 500 ms => 1 ms = tpb / 500 ticks
    jitter_ticks_max = int(tpb * (jitter_ms / 500.0))

    for track in mid.tracks:
        new_track = mido.MidiTrack()
        new_mid.tracks.append(new_track)
        
        abs_time = 0
        events = []
        
        for msg in track:
            abs_time += msg.time
            events.append({"msg": msg, "abs_time": abs_time})
            
        # 1. Jitter
        note_on_pending = {} # note -> abs_time
        
        for e in events:
            msg = e["msg"]
            if msg.type == 'note_on' and msg.velocity > 0:
                # Add jitter
                jitter = random.randint(-jitter_ticks_max, jitter_ticks_max)
                e["abs_time"] = max(0, e["abs_time"] + jitter)
                note_on_pending[msg.note] = e["abs_time"]
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in note_on_pending:
                    jitter = random.randint(-jitter_ticks_max, jitter_ticks_max)
                    e["abs_time"] = max(note_on_pending[msg.note] + 1, e["abs_time"] + jitter)
                    del note_on_pending[msg.note]

        # Sort events by absolute time to process CC insertion
        events.sort(key=lambda x: x["abs_time"])
        
        # 2. CC11 Swells for long notes
        # We need to find long notes. Let's rebuild note pairs
        active_notes = {}
        processed_events = []
        cc_events = []
        
        for e in events:
            msg = e["msg"]
            abs_time = e["abs_time"]
            
            if msg.type == 'note_on' and msg.velocity > 0:
                active_notes[msg.note] = abs_time
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in active_notes:
                    start_time = active_notes.pop(msg.note)
                    duration = abs_time - start_time
                    # If note is longer than 1.5 beats, add CC11 swell
                    if duration > tpb * 1.5:
                        steps = max(3, int(duration / cc_interval_ticks))
                        for i in range(steps + 1):
                            t = start_time + int((i / steps) * duration)
                            # Sine swell 60 -> 120 -> 60
                            phase = (i / steps) * math.pi
                            val = 60 + int(math.sin(phase) * 60)
                            
                            # Check if channel exists on msg
                            channel = getattr(msg, 'channel', 0)
                            cc_msg = mido.Message('control_change', channel=channel, control=11, value=val, time=0)
                            cc_events.append({"msg": cc_msg, "abs_time": t})
                            
        # Combine all events
        all_events = events + cc_events
        
        # Sort by time. Important: CC before Note On before Note Off at same tick
        def sort_key(e):
            m = e["msg"]
            order = 3
            if m.type == 'control_change': order = 1
            elif m.type == 'note_off': order = 2
            elif m.type == 'note_on' and m.velocity == 0: order = 2
            elif m.type == 'note_on': order = 4
            return (e["abs_time"], order)
            
        all_events.sort(key=sort_key)
        
        # Convert back to relative time
        prev_time = 0
        for e in all_events:
            msg = e["msg"].copy()
            delta = e["abs_time"] - prev_time
            msg.time = int(delta)
            new_track.append(msg)
            prev_time = e["abs_time"]
            
    new_mid.save(output_path)
    print(f"Enhanced MIDI saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python enhance_midi.py <input.mid> <output.mid>")
        sys.argv.append("input.mid")
        sys.argv.append("output.mid")
        sys.exit(1)
        
    enhance_midi(sys.argv[1], sys.argv[2])
