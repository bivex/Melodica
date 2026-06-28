# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
generate_prologue_symphony.py
Renders the complete 6-track Symphonic Album representing the Prologue and Chapter 1
of the romance novel "The Vow of St. James". Saves each movement as a separate,
correctly structured MIDI file inside output/prologue_symphony/.
"""

from __future__ import annotations

import copy
from pathlib import Path
from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.midi import Track


def generate_full_prologue_album():
    # Define minor scale for the heavy emotional/dramatic sections
    minor_scale = Scale(0, Mode.NATURAL_MINOR)  # C Minor
    major_scale = Scale(7, Mode.MAJOR)          # G Major for Emerald Shipping Co.

    # 1. Configuration with tracks representing all instruments
    config = IdeaToolConfig(
        scale=minor_scale,
        bars=24,  # 6 parts * 4 bars each
        tracks=[
            # String section tracks
            TrackConfig(
                name="double_bass",
                generator_type="chord_layout",
                instrument="double_bass",
                params={
                    "instrument_name": "double_bass",
                    "instruments": ["double_bass", "cello", "viola", "violin"]
                }
            ),
            TrackConfig(
                name="cello",
                generator_type="chord_layout",
                instrument="cello",
                params={
                    "instrument_name": "cello",
                    "instruments": ["double_bass", "cello", "viola", "violin"]
                }
            ),
            TrackConfig(
                name="violin",
                generator_type="chord_layout",
                instrument="violin",
                params={
                    "instrument_name": "violin",
                    "instruments": ["double_bass", "cello", "viola", "violin"]
                }
            ),
            TrackConfig(
                name="glockenspiel",
                generator_type="chord_layout",
                instrument="glockenspiel",
                params={
                    "instrument_name": "glockenspiel",
                    "instruments": ["double_bass", "cello", "viola", "violin"]
                }
            ),
            # Canon track for Track 4 (Escape from Winchester House)
            TrackConfig(
                name="canon_voice",
                generator_type="canon",
                instrument="violin",
                params={
                    "delay_beats": 4.0,
                    "interval": 12  # octave canon
                }
            ),
            # Woodwind track for Track 3 (Emerald Shipping Co.)
            TrackConfig(
                name="flute",
                generator_type="generic",
                instrument="flute"
            )
        ],
        parts=[
            # Act I: England, 1802
            IdeaPart(name="HostileHall", bars=4, scale=minor_scale),
            IdeaPart(name="SarahsLullaby", bars=4, scale=minor_scale),
            # Act II: London, 1816
            IdeaPart(name="EmeraldShipping", bars=4, scale=major_scale),
            IdeaPart(name="EscapeWinchester", bars=4, scale=minor_scale),
            IdeaPart(name="RescuingNorah", bars=4, scale=minor_scale),
            IdeaPart(name="TavernStorm", bars=4, scale=minor_scale),
        ]
    )

    # Apply track mutes to ensure instruments only play in their corresponding movements
    config.parts[0].track_mute = ["glockenspiel", "canon_voice"]
    config.parts[1].track_mute = ["double_bass", "cello", "flute", "canon_voice"]
    config.parts[2].track_mute = ["double_bass", "glockenspiel", "canon_voice"]
    config.parts[3].track_mute = ["double_bass", "cello", "flute", "glockenspiel"]
    config.parts[4].track_mute = ["flute", "glockenspiel", "canon_voice"]
    config.parts[5].track_mute = ["flute", "canon_voice"]

    print("Generating full concept album tracks using Melodica IdeaEngine...")
    tool = IdeaTool(config)
    
    # Generate all fully-wired Track objects
    tracks_dict = tool.render_tracks()

    # Create output directory
    output_dir = Path("output/prologue_symphony")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Slice notes by movement boundaries
    from melodica.midi import export_midi

    current_start = 0.0
    for idx, part in enumerate(config.parts):
        ts = part.time_signature or (4, 4)
        duration_beats = part.bars * ts[0]
        part_end = current_start + duration_beats

        # Create sliced Track objects for this part
        sliced_tracks = []
        for name, track in tracks_dict.items():
            sliced_notes = []
            for note in track.notes:
                if current_start <= note.start < part_end:
                    # Deep copy and shift time to start at 0.0
                    new_note = copy.deepcopy(note)
                    new_note.start -= current_start
                    sliced_notes.append(new_note)

            # Only export track if it has notes in this movement
            if sliced_notes:
                sliced_track = Track(
                    name=track.name,
                    notes=sliced_notes,
                    channel=track.channel,
                    program=track.program,
                    volume=track.volume,
                    pan=track.pan,
                    instrument_name=track.instrument_name,
                )
                sliced_tracks.append(sliced_track)

        # Export movement MIDI
        filename = f"{idx+1:02d}_{part.name.lower()}.mid"
        dest_path = output_dir / filename
        export_midi(sliced_tracks, dest_path)
        print(f" -> Exported movement {idx+1}: {dest_path}")

        current_start = part_end

    print("\nAll movements exported successfully into output/prologue_symphony/!")


if __name__ == "__main__":
    generate_full_prologue_album()
