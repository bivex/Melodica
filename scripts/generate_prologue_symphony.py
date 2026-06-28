# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
generate_prologue_symphony.py
Renders the complete 6-track Symphonic Album representing the Prologue and Chapter 1
of the romance novel "The Vow of St. James". Uses advanced, high-level general-midi
orchestral generators (strings, woodwinds, brass, timpani, harp) with specific
articulations for every movement.
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

    # 1. Configuration with pro orchestral tracks matching each movement
    config = IdeaToolConfig(
        scale=minor_scale,
        bars=192,  # 6 parts * 32 bars each
        tracks=[
            # --- Movement 1: The Hostile Hall (1802) ---
            TrackConfig(
                name="m1_contrabass",
                generator_type="contrabass",
                instrument="contrabass",
                params={"articulation": "sustained", "bass_voice": True}
            ),
            TrackConfig(
                name="m1_cello",
                generator_type="cello",
                instrument="cello",
                params={"articulation": "sustained"}
            ),
            TrackConfig(
                name="m1_violin",
                generator_type="violin",
                instrument="violin",
                params={"articulation": "sustained", "con_sordino": True}
            ),
            TrackConfig(
                name="m1_french_horn",
                generator_type="french_horn",
                instrument="french_horn",
                params={"articulation": "sustained"}
            ),
            TrackConfig(
                name="m1_oboe",
                generator_type="oboe",
                instrument="oboe",
                params={"articulation": "sustained", "vibrato": True}
            ),

            # --- Movement 2: Sarah's Lullaby (1802) ---
            TrackConfig(
                name="m2_violin_pizz",
                generator_type="violin",
                instrument="violin",
                params={"articulation": "pizzicato", "position": 3}
            ),
            TrackConfig(
                name="m2_glock",
                generator_type="chord_layout",
                instrument="glockenspiel",
                params={"instrument_name": "glockenspiel"}
            ),
            TrackConfig(
                name="m2_harp",
                generator_type="harp",
                instrument="harp",
                params={"pattern": "arpeggio", "direction": "up"}
            ),

            # --- Movement 3: Emerald Shipping Co. (1816) ---
            TrackConfig(
                name="m3_flute",
                generator_type="flute",
                instrument="flute",
                params={"articulation": "legato", "vibrato": True}
            ),
            TrackConfig(
                name="m3_clarinet",
                generator_type="clarinet",
                instrument="clarinet",
                params={"articulation": "legato", "vibrato": False}
            ),
            TrackConfig(
                name="m3_violin_spic",
                generator_type="violin",
                instrument="violin",
                params={"articulation": "spiccato"}
            ),
            TrackConfig(
                name="m3_cello_pizz",
                generator_type="cello",
                instrument="cello",
                params={"articulation": "pizzicato"}
            ),

            # --- Movement 4: Escape from Winchester House (1816) ---
            TrackConfig(
                name="m4_violin_dux",
                generator_type="violin",
                instrument="violin",
                params={"articulation": "legato"}
            ),
            TrackConfig(
                name="m4_viola_canon",
                generator_type="canon",
                instrument="viola",
                params={"delay_beats": 4.0, "interval": 12}
            ),

            # --- Movement 5: Rescuing Norah (1816) ---
            TrackConfig(
                name="m5_violin_trem",
                generator_type="violin",
                instrument="violin",
                params={"articulation": "tremolo", "con_sordino": True}
            ),
            TrackConfig(
                name="m5_viola_trem",
                generator_type="viola",
                instrument="viola",
                params={"articulation": "tremolo", "con_sordino": True}
            ),
            TrackConfig(
                name="m5_cello_legato",
                generator_type="cello",
                instrument="cello",
                params={"articulation": "legato", "position": 2}
            ),
            TrackConfig(
                name="m5_contrabass",
                generator_type="contrabass",
                instrument="contrabass",
                params={"articulation": "sustained"}
            ),

            # --- Movement 6: Storm in the Harbor Tavern (1816) ---
            TrackConfig(
                name="m6_violin_stac",
                generator_type="violin",
                instrument="violin",
                params={"articulation": "staccato", "double_stops": True}
            ),
            TrackConfig(
                name="m6_french_horn",
                generator_type="french_horn",
                instrument="french_horn",
                params={"articulation": "staccato"}
            ),
            TrackConfig(
                name="m6_trumpet_fanfare",
                generator_type="trumpet",
                instrument="trumpet",
                params={"articulation": "staccato", "fanfare_mode": True}
            ),
            TrackConfig(
                name="m6_timpani",
                generator_type="timpani",
                instrument="timpani",
                params={"stroke_pattern": "roll"}
            ),
        ],
        parts=[
            # Act I: England, 1802
            IdeaPart(name="HostileHall", bars=32, scale=minor_scale),
            IdeaPart(name="SarahsLullaby", bars=32, scale=minor_scale),
            # Act II: London, 1816
            IdeaPart(name="EmeraldShipping", bars=32, scale=major_scale),
            IdeaPart(name="EscapeWinchester", bars=32, scale=minor_scale),
            IdeaPart(name="RescuingNorah", bars=32, scale=minor_scale),
            IdeaPart(name="TavernStorm", bars=32, scale=minor_scale),
        ]
    )

    # Automatically compute track mutes based on the movement prefix
    all_track_names = [tc.name for tc in config.tracks]
    for idx, part in enumerate(config.parts):
        prefix = f"m{idx+1}_"
        part.track_mute = [name for name in all_track_names if not name.startswith(prefix)]

    print("Generating pro-level orchestral concept album using Melodica...")
    tool = IdeaTool(config)
    tracks_dict = tool.render_tracks()

    # Create output directory
    output_dir = Path("output/prologue_symphony")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Slice notes by movement boundaries and export to MIDI
    from melodica.midi import export_midi

    current_start = 0.0
    for idx, part in enumerate(config.parts):
        ts = part.time_signature or (4, 4)
        duration_beats = part.bars * ts[0]
        part_end = current_start + duration_beats

        sliced_tracks = []
        for name, track in tracks_dict.items():
            sliced_notes = []
            for note in track.notes:
                if current_start <= note.start < part_end:
                    new_note = copy.deepcopy(note)
                    new_note.start -= current_start
                    sliced_notes.append(new_note)

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

        filename = f"{idx+1:02d}_{part.name.lower()}.mid"
        dest_path = output_dir / filename
        export_midi(sliced_tracks, dest_path)
        print(f" -> Exported movement {idx+1} [Pro Orchestration]: {dest_path}")

        current_start = part_end

    print("\nAll movements with advanced arrangements exported successfully!")


if __name__ == "__main__":
    generate_full_prologue_album()
