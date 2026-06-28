# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
generate_prologue_symphony.py
Renders the complete 6-track Dream Pop / Slowcore Album (style: Cigarettes After Sex)
representing the Prologue and Chapter 1 of the romance novel "The Vow of St. James".
Uses slow tempos, ambient pads, warm bass, arpeggios, and minimalist drum beats.
"""

from __future__ import annotations

import copy
from pathlib import Path
from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.midi import Track


def generate_full_prologue_album():
    # Define minor scale for the emotional sections and major scale for port scene
    minor_scale = Scale(0, Mode.NATURAL_MINOR)  # C Minor
    major_scale = Scale(7, Mode.MAJOR)          # G Major

    # Configuration for the Dream Pop / Slowcore arrangement
    config = IdeaToolConfig(
        scale=minor_scale,
        bars=192,  # 6 parts * 32 bars each
        tempo=64,  # Slow dream pop tempo (64 BPM)
        use_tempo_modulation=True,
        ritardando_beats=4.0,
        ritardando_factor=0.85,
        use_tension_tempo=True,
        tension_tempo_range=10.0,
        tracks=[
            # --- Movement 1: The Muted Hall (1802) ---
            TrackConfig(
                name="m1_pad",
                generator_type="ambient",
                instrument="choir_ahhs",
                params={"voicing": "spread", "overlap": 0.8}
            ),
            TrackConfig(
                name="m1_bass",
                generator_type="chord_layout",
                instrument="contrabass",
                params={"instrument_name": "double_bass", "instruments": ["double_bass"]}
            ),
            TrackConfig(
                name="m1_guitar_arp",
                generator_type="arpeggiator",
                instrument="guitar",
                params={"pattern": "up", "note_duration": 0.5}
            ),
            TrackConfig(
                name="m1_vocals",
                generator_type="melody",
                instrument="flute",
                density=0.3,
                params={"harmony_note_probability": 0.9}
            ),

            # --- Movement 2: The Horse Blanket (1802) ---
            TrackConfig(
                name="m2_pad",
                generator_type="ambient",
                instrument="piano",
                params={"voicing": "close", "overlap": 0.5}
            ),
            TrackConfig(
                name="m2_bass",
                generator_type="chord_layout",
                instrument="contrabass",
                params={"instrument_name": "double_bass", "instruments": ["double_bass"]}
            ),
            TrackConfig(
                name="m2_harp_arp",
                generator_type="harp",
                instrument="harp",
                params={"pattern": "arpeggio", "direction": "up"}
            ),
            TrackConfig(
                name="m2_vocals",
                generator_type="melody",
                instrument="flute",
                density=0.25,
                params={"harmony_note_probability": 0.9}
            ),

            # --- Movement 3: Emerald Port (1816) ---
            TrackConfig(
                name="m3_drums",
                generator_type="drum_kit_pattern",
                instrument="drums",
                params={"style": "hiphop"}
            ),
            TrackConfig(
                name="m3_bass",
                generator_type="chord_layout",
                instrument="contrabass",
                params={"instrument_name": "double_bass", "instruments": ["double_bass"]}
            ),
            TrackConfig(
                name="m3_guitar_arp",
                generator_type="arpeggiator",
                instrument="guitar",
                params={"pattern": "up_down", "note_duration": 0.5}
            ),
            TrackConfig(
                name="m3_vocals",
                generator_type="melody",
                instrument="oboe",
                density=0.35,
                params={"harmony_note_probability": 0.95}
            ),

            # --- Movement 4: The Midnight Cardboard Window (1816) ---
            TrackConfig(
                name="m4_drums",
                generator_type="drum_kit_pattern",
                instrument="drums",
                params={"style": "hiphop"}
            ),
            TrackConfig(
                name="m4_bass",
                generator_type="chord_layout",
                instrument="contrabass",
                params={"instrument_name": "double_bass", "instruments": ["double_bass"]}
            ),
            TrackConfig(
                name="m4_guitar_dux",
                generator_type="melody",
                instrument="guitar",
                density=0.4,
                params={"harmony_note_probability": 0.9}
            ),
            TrackConfig(
                name="m4_guitar_canon",
                generator_type="canon",
                instrument="guitar",
                params={"delay_beats": 4.0, "interval": 12}
            ),

            # --- Movement 5: Norah's Ring (1816) ---
            TrackConfig(
                name="m5_pad",
                generator_type="ambient",
                instrument="organ",
                params={"voicing": "spread", "overlap": 0.9}
            ),
            TrackConfig(
                name="m5_bass",
                generator_type="chord_layout",
                instrument="contrabass",
                params={"instrument_name": "double_bass", "instruments": ["double_bass"]}
            ),
            TrackConfig(
                name="m5_guitar_arp",
                generator_type="arpeggiator",
                instrument="guitar",
                params={"pattern": "up", "note_duration": 0.5}
            ),
            TrackConfig(
                name="m5_vocals",
                generator_type="melody",
                instrument="cello",
                density=0.3,
                params={"harmony_note_probability": 0.9}
            ),

            # --- Movement 6: Ale & Whiplash (1816) ---
            TrackConfig(
                name="m6_drums",
                generator_type="drum_kit_pattern",
                instrument="drums",
                params={"style": "hiphop"}
            ),
            TrackConfig(
                name="m6_bass",
                generator_type="chord_layout",
                instrument="contrabass",
                params={"instrument_name": "double_bass", "instruments": ["double_bass"]}
            ),
            TrackConfig(
                name="m6_guitar_arp",
                generator_type="arpeggiator",
                instrument="guitar",
                params={"pattern": "up_down", "note_duration": 0.5}
            ),
            TrackConfig(
                name="m6_vocals",
                generator_type="melody",
                instrument="trumpet",
                density=0.4,
                params={"harmony_note_probability": 0.9}
            ),
        ],
        parts=[
            # Act I: England, 1802
            IdeaPart(name="MutedHall", bars=32, scale=minor_scale, tempo=64, time_signature=(4, 4)),
            IdeaPart(name="HorseBlanket", bars=32, scale=minor_scale, tempo=60, time_signature=(4, 4)),
            # Act II: London, 1816
            IdeaPart(name="EmeraldPort", bars=32, scale=major_scale, tempo=68, time_signature=(4, 4)),
            # nocturnal waltz
            IdeaPart(name="MidnightWindow", bars=32, scale=minor_scale, tempo=64, time_signature=(3, 4)),
            IdeaPart(name="NorahsRing", bars=32, scale=minor_scale, tempo=60, time_signature=(4, 4)),
            IdeaPart(name="AleWhiplash", bars=32, scale=minor_scale, tempo=70, time_signature=(4, 4)),
        ]
    )

    # Automatically compute track mutes based on the movement prefix
    all_track_names = [tc.name for tc in config.tracks]
    for idx, part in enumerate(config.parts):
        prefix = f"m{idx+1}_"
        part.track_mute = [name for name in all_track_names if not name.startswith(prefix)]

    # Configure conversational antiphony to prevent overlapping/masking in dream pop texture
    config.parts[0].antiphony = {
        "group_a": ["m1_vocals"],
        "group_b": ["m1_guitar_arp"],
        "bars_a": 2.0,
        "bars_b": 2.0,
        "overlap_beats": 1.0
    }
    config.parts[2].antiphony = {
        "group_a": ["m3_vocals"],
        "group_b": ["m3_guitar_arp"],
        "bars_a": 2.0,
        "bars_b": 2.0,
        "overlap_beats": 1.0
    }
    config.parts[4].antiphony = {
        "group_a": ["m5_vocals"],
        "group_b": ["m5_guitar_arp"],
        "bars_a": 2.0,
        "bars_b": 2.0,
        "overlap_beats": 1.0
    }
    config.parts[5].antiphony = {
        "group_a": ["m6_vocals"],
        "group_b": ["m6_guitar_arp"],
        "bars_a": 2.0,
        "bars_b": 2.0,
        "overlap_beats": 1.0
    }

    print("Generating Dream Pop / Slowcore concept album (style: Cigarettes After Sex)...")
    tool = IdeaTool(config)
    tracks_dict = tool.render_tracks()

    # Create output directory
    output_dir = Path("output/prologue_symphony")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build boundaries list
    boundaries = [0.0]
    for part in config.parts:
        ts = part.time_signature or (4, 4)
        duration_beats = part.bars * ts[0]
        boundaries.append(boundaries[-1] + duration_beats)

    # Slice notes by movement boundaries with tying and export to MIDI
    from melodica.midi import export_midi, slice_notes_with_tying

    # Pre-slice all track notes
    sliced_tracks_by_part = [[] for _ in range(len(config.parts))]
    
    for name, track in tracks_dict.items():
        track_slices = slice_notes_with_tying(track.notes, boundaries)
        for idx in range(len(config.parts)):
            part_notes = track_slices[idx]
            if part_notes:
                sliced_track = Track(
                    name=track.name,
                    notes=part_notes,
                    channel=track.channel,
                    program=track.program,
                    volume=track.volume,
                    pan=track.pan,
                    instrument_name=track.instrument_name,
                )
                sliced_tracks_by_part[idx].append(sliced_track)

    for idx, part in enumerate(config.parts):
        sliced_tracks = sliced_tracks_by_part[idx]
        part_start = boundaries[idx]
        part_end = boundaries[idx + 1]

        # Slice tempo events for this specific part
        sliced_tempo_events = []
        if tool.tempo_events:
            for beat, bpm in tool.tempo_events:
                if part_start <= beat < part_end:
                    sliced_tempo_events.append((beat - part_start, bpm))

        from melodica.types import MusicTimeline, TimeSignatureLabel
        slice_timeline = MusicTimeline(
            time_signatures=[
                TimeSignatureLabel(
                    numerator=part.time_signature[0],
                    denominator=part.time_signature[1],
                    start=0.0
                )
            ]
        )

        filename = f"{idx+1:02d}_{part.name.lower()}.mid"
        dest_path = output_dir / filename
        export_midi(
            sliced_tracks,
            dest_path,
            bpm=part.tempo,
            timeline=slice_timeline,
            tempo_events=sliced_tempo_events if sliced_tempo_events else None
        )
        print(f" -> Exported movement {idx+1} [Dream Pop Style] - Tempo: {part.tempo} BPM, Time Sig: {part.time_signature[0]}/{part.time_signature[1]}: {dest_path}")

        # Integrate MIDI Doctor checks on the sliced tracks dict
        try:
            from melodica.composer.psychoacoustic import detect_frequency_masking, detect_temporal_masking, detect_fusion
            from melodica.composer.harmonic_verifier import detect_clashes, VerifierConfig
            
            sliced_dict = {t.name: t.notes for t in sliced_tracks}
            freq_mask = detect_frequency_masking(sliced_dict)
            temp_mask = detect_temporal_masking(sliced_dict)
            fusion = detect_fusion(sliced_dict)
            clashes = detect_clashes(sliced_dict, VerifierConfig(dissonance_tolerance=0.5))
            
            print(f"    [MIDI Doctor Diagnostics] Freq Masking: {len(freq_mask)} | Temp Masking: {len(temp_mask)} | Fusion: {len(fusion)} | Clashes: {len(clashes)}")
            if len(freq_mask) > 0 or len(clashes) > 50:
                print(f"    WARNING: High density of anomalies detected in {filename}. Check voice-leading alignment.")
        except Exception as e:
            print(f"    [MIDI Doctor Diagnostics failed]: {e}")

    print("\nAll movements in Dream Pop style exported successfully!")


if __name__ == "__main__":
    generate_full_prologue_album()
