import sys
from pathlib import Path

# Add the workspace directory to the python path to import our modules
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from scripts.album_valkyrie_lp2 import (
    produce_track_1, produce_track_2, produce_track_3, produce_track_4, produce_track_5,
    produce_track_6, produce_track_7, produce_track_8, produce_track_9, produce_track_10
)

def count_notes():
    tracks = [
        ("01. Iron Wings", produce_track_1),
        ("02. Chooser of the Slain", produce_track_2),
        ("03. Mist & Armor", produce_track_3),
        ("04. Raven Protocol", produce_track_4),
        ("05. The Battlefield", produce_track_5),
        ("06. Valhalla Calling", produce_track_6),
        ("07. Winged Fury", produce_track_7),
        ("08. Between Worlds", produce_track_8),
        ("09. Norns' Thread", produce_track_9),
        ("10. Valkyrie's Return", produce_track_10),
    ]
    
    grand_total = 0
    print("=" * 60)
    print("   VALKYRIE LP2 — NOTE COUNT REPORT")
    print("=" * 60)
    
    for name, func in tracks:
        raw_tracks, _ = func()
        track_total = 0
        print(f"\n{name}:")
        for track_name, notes in raw_tracks.items():
            count = len(notes)
            track_total += count
            print(f"  - {track_name}: {count} notes")
        print(f"  * Total for track: {track_total} notes")
        grand_total += track_total
        
    print("\n" + "=" * 60)
    print(f" GRAND TOTAL FOR ALBUM: {grand_total} notes")
    print("=" * 60)

if __name__ == "__main__":
    count_notes()
