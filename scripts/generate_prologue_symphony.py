# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
generate_prologue_symphony.py
Renders the complete 6-track Symphonic Album representing the Prologue and Chapter 1
of the romance novel "The Vow of St. James". Combines Chord Layout voicings
for harmonic backing tracks and solo instruments for clean, clash-free arrangements.
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

    # Configuration using ChordVoicingLayout for clean harmony and solo woodwinds/brass for melody
    config = IdeaToolConfig(
        scale=minor_scale,
        bars=192,  # 6 parts * 32 bars each
        tracks=[
            # --- Movement 1: The Hostile Hall (1802) ---
            TrackConfig(
                name="m1_contrabass",
                generator_type="chord_layout",
                instrument="contrabass",
                params={"instrument_name": "double_bass", "instruments": ["double_bass", "cello", "violin"]}
            ),
            TrackConfig(
                name="m1_cello",
                generator_type="chord_layout",
                instrument="cello",
                params={"instrument_name": "cello", "instruments": ["double_bass", "cello", "violin"]}
            ),
            TrackConfig(
                name="m1_violin",
                generator_type="chord_layout",
                instrument="violin",
                params={"instrument_name": "violin", "instruments": ["double_bass", "cello", "violin"]}
            ),
            TrackConfig(
                name="m1_oboe_solo",
                generator_type="melody",  # Solo melody line
                instrument="oboe",
                density=0.4,
                params={"harmony_note_probability": 0.85}
            ),

            # --- Movement 2: Sarah's Lullaby (1802) ---
            TrackConfig(
                name="m2_harp",
                generator_type="chord_layout",
                instrument="harp",
                params={"instrument_name": "harp", "instruments": ["double_bass", "cello", "violin", "harp"]}
            ),
            TrackConfig(
                name="m2_glock",
                generator_type="chord_layout",
                instrument="glockenspiel",
                params={"instrument_name": "glockenspiel", "instruments": ["double_bass", "cello", "violin", "glockenspiel"]}
            ),
            TrackConfig(
                name="m2_violin_solo",
                generator_type="melody",  # Pizzicato solo
                instrument="violin",
                density=0.3,
                params={"articulation": "pizzicato", "harmony_note_probability": 0.85}
            ),

            # --- Movement 3: Emerald Shipping Co. (1816) ---
            TrackConfig(
                name="m3_violin_spic",
                generator_type="chord_layout",
                instrument="violin",
                params={"instrument_name": "violin", "instruments": ["cello", "violin"]}
            ),
            TrackConfig(
                name="m3_cello_pizz",
                generator_type="chord_layout",
                instrument="cello",
                params={"instrument_name": "cello", "instruments": ["cello", "violin"]}
            ),
            TrackConfig(
                name="m3_flute_solo",
                generator_type="melody",
                instrument="flute",
                density=0.4,
                params={"harmony_note_probability": 0.85}
            ),

            # --- Movement 4: Escape from Winchester House (1816) ---
            TrackConfig(
                name="m4_violin_dux",
                generator_type="melody",  # Dux melody
                instrument="violin",
                density=0.5,
                params={"harmony_note_probability": 0.85}
            ),
            TrackConfig(
                name="m4_viola_canon",
                generator_type="canon",
                instrument="viola",
                params={"delay_beats": 4.0, "interval": 12}
            ),

            # --- Movement 5: Rescuing Norah (1816) ---
            TrackConfig(
                name="m5_contrabass",
                generator_type="chord_layout",
                instrument="contrabass",
                params={"instrument_name": "double_bass", "instruments": ["double_bass", "cello", "viola"]}
            ),
            TrackConfig(
                name="m5_cello",
                generator_type="chord_layout",
                instrument="cello",
                params={"instrument_name": "cello", "instruments": ["double_bass", "cello", "viola"]}
            ),
            TrackConfig(
                name="m5_viola",
                generator_type="chord_layout",
                instrument="viola",
                params={"instrument_name": "viola", "instruments": ["double_bass", "cello", "viola"]}
            ),
            TrackConfig(
                name="m5_violin_solo",
                generator_type="melody",
                instrument="violin",
                density=0.35,
                params={"articulation": "tremolo", "harmony_note_probability": 0.85}
            ),

            # --- Movement 6: Storm in the Harbor Tavern (1816) ---
            TrackConfig(
                name="m6_contrabass",
                generator_type="chord_layout",
                instrument="contrabass",
                params={"instrument_name": "double_bass", "instruments": ["double_bass", "cello", "french_horn"]}
            ),
            TrackConfig(
                name="m6_cello",
                generator_type="chord_layout",
                instrument="cello",
                params={"instrument_name": "cello", "instruments": ["double_bass", "cello", "french_horn"]}
            ),
            TrackConfig(
                name="m6_horn",
                generator_type="chord_layout",
                instrument="french_horn",
                params={"instrument_name": "french_horn", "instruments": ["double_bass", "cello", "french_horn"]}
            ),
            TrackConfig(
                name="m6_trumpet_solo",
                generator_type="melody",
                instrument="trumpet",
                density=0.45,
                params={"fanfare_mode": True, "harmony_note_probability": 0.85}
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

    # Configure conversational antiphony (call-and-response) to prevent overlapping/masking
    config.parts[0].antiphony = {
        "group_a": ["m1_violin", "m1_cello", "m1_contrabass"],
        "group_b": ["m1_oboe_solo"],
        "bars_a": 2.0,
        "bars_b": 2.0,
        "overlap_beats": 0.5
    }
    config.parts[2].antiphony = {
        "group_a": ["m3_flute_solo"],
        "group_b": ["m3_violin_spic", "m3_cello_pizz"],
        "bars_a": 2.0,
        "bars_b": 2.0,
        "overlap_beats": 0.5
    }
    config.parts[4].antiphony = {
        "group_a": ["m5_violin_solo"],
        "group_b": ["m5_viola", "m5_cello", "m5_contrabass"],
        "bars_a": 4.0,
        "bars_b": 4.0,
        "overlap_beats": 1.0
    }
    config.parts[5].antiphony = {
        "group_a": ["m6_trumpet_solo"],
        "group_b": ["m6_horn", "m6_cello", "m6_contrabass"],
        "bars_a": 2.0,
        "bars_b": 2.0,
        "overlap_beats": 0.0
    }

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
        print(f" -> Exported movement {idx+1} [Clean Voicing & Solo Dialog]: {dest_path}")

        current_start = part_end

    print("\nAll movements with advanced arrangements exported successfully!")


if __name__ == "__main__":
    generate_full_prologue_album()
