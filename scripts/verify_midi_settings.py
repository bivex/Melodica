# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import mido
from pathlib import Path

def inspect_midi(path):
    print(f"--- Inspecting: {path} ---")
    mid = mido.MidiFile(path)
    for i, track in enumerate(mid.tracks):
        print(f"Track {i}: {track.name}")
        for msg in track:
            if msg.is_meta:
                 continue # Ignore meta messages like track_name
            
            # Check for interesting MIDI messages
            if msg.type in ['program_change', 'control_change', 'pitchwheel']:
                print(f"  {msg}")
        print("-" * 10)

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "output/auto_dark_fantasy.mid"
    inspect_midi(path)
