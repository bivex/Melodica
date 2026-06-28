# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
generate_prologue_symphony.py
Renders the symphonic album themes for the Prologue of "The Vow of St. James".
"""

from __future__ import annotations

from melodica.types import Scale, Mode, ChordLabel, Quality
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart


def generate_prologue_album():
    scale = Scale(0, Mode.NATURAL_MINOR)  # C Minor

    # Configuration for Movement I & II
    config = IdeaToolConfig(
        scale=scale,
        bars=8,
        tracks=[
            # Bass track playing the root (Tension)
            TrackConfig(
                name="double_bass_track",
                generator_type="chord_layout",
                instrument="double_bass",
                params={
                    "instrument_name": "double_bass",
                    "instruments": ["double_bass", "cello", "viola", "violin"]
                }
            ),
            # Cello track (Warm inner voice)
            TrackConfig(
                name="cello_track",
                generator_type="chord_layout",
                instrument="cello",
                params={
                    "instrument_name": "cello",
                    "instruments": ["double_bass", "cello", "viola", "violin"]
                }
            ),
            # Violin (Melody and top voice)
            TrackConfig(
                name="violin_track",
                generator_type="chord_layout",
                instrument="violin",
                params={
                    "instrument_name": "violin",
                    "instruments": ["double_bass", "cello", "viola", "violin"]
                }
            ),
            # Glockenspiel (Sparkling doubling for Sarah's childlike theme)
            TrackConfig(
                name="glockenspiel_track",
                generator_type="chord_layout",
                instrument="glockenspiel",
                params={
                    "instrument_name": "glockenspiel",
                    "instruments": ["double_bass", "cello", "viola", "violin"]
                }
            )
        ],
        parts=[
            IdeaPart(name="HostileHall", bars=4),
            IdeaPart(name="SarahsLullaby", bars=4)
        ]
    )

    tool = IdeaTool(config)
    tracks = list(tool.render_tracks().values())

    from melodica.midi import export_midi
    output_path = "output/prologue_symphony.mid"
    export_midi(tracks, output_path)
    print("Symphony generated successfully!")
    print(f"MIDI file exported to: {output_path}")


if __name__ == "__main__":
    generate_prologue_album()
