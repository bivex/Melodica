# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
generate_prologue_symphony.py
Renders the complete 6-track Symphonic Album representing the Prologue and Chapter 1
of the romance novel "The Vow of St. James".
"""

from __future__ import annotations

from melodica.types import Scale, Mode, ChordLabel, Quality
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart


def generate_full_prologue_album():
    # Define minor scale for the heavy emotional/dramatic sections
    minor_scale = Scale(0, Mode.NATURAL_MINOR)  # C Minor
    major_scale = Scale(7, Mode.MAJOR)          # G Major for Emerald Shipping Co.

    # 1. We will construct a configuration with tracks representing all instruments
    # and parts representing each of the 6 movements/tracks of our album.
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
            IdeaPart(name="Mvt1_HostileHall", bars=4, scale=minor_scale),
            IdeaPart(name="Mvt2_SarahsLullaby", bars=4, scale=minor_scale),
            # Act II: London, 1816
            IdeaPart(name="Mvt3_EmeraldShipping", bars=4, scale=major_scale),
            IdeaPart(name="Mvt4_EscapeWinchester", bars=4, scale=minor_scale),
            IdeaPart(name="Mvt5_RescuingNorah", bars=4, scale=minor_scale),
            IdeaPart(name="Mvt6_TavernStorm", bars=4, scale=minor_scale),
        ]
    )

    # 2. Add custom mutes to make sure instruments only play in their corresponding movements:
    # - Mvt 1 (Hostile Hall): double_bass, cello, violin, flute
    # - Mvt 2 (Sarah's Lullaby): violin, glockenspiel (silent double_bass/cello/flute)
    # - Mvt 3 (Emerald Shipping): flute, cello, violin
    # - Mvt 4 (Escape): violin, canon_voice (canon counterpoint)
    # - Mvt 5 (Rescuing Norah): cello, violin, double_bass
    # - Mvt 6 (Tavern Storm): double_bass, cello, violin, glockenspiel
    
    # We apply this by configuring the track_mute dictionary per part
    config.parts[0].track_mute = {"glockenspiel", "canon_voice"}
    config.parts[1].track_mute = {"double_bass", "cello", "flute", "canon_voice"}
    config.parts[2].track_mute = {"double_bass", "glockenspiel", "canon_voice"}
    config.parts[3].track_mute = {"double_bass", "cello", "flute", "glockenspiel"}
    config.parts[4].track_mute = {"flute", "glockenspiel", "canon_voice"}
    config.parts[5].track_mute = {"flute", "canon_voice"}

    print("Generating full concept album tracks using Melodica IdeaEngine...")
    tool = IdeaTool(config)
    tracks = list(tool.render_tracks().values())

    from melodica.midi import export_midi
    output_path = "output/prologue_symphony.mid"
    export_midi(tracks, output_path)
    print("Symphony generated successfully!")
    print(f"MIDI file containing all 6 movements exported to: {output_path}")


if __name__ == "__main__":
    generate_full_prologue_album()
