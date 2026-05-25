# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_dark_souls.py — Dark Souls Thematic Album Generator.

Album: "Shadows of Lordran"
Tracks:
1. Ash and Embers (Melancholy Piano)
2. The Abyss Marches (Heavy Orchestral March)
3. Boreal Waltz (Graceful 3/2 swing tension)
4. Final Cinder (Aggressive Boss climax)

Powered by FLUID_R3_PROGRAMS, Coupled HMM, and Custom Dark Souls Rhythms.
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart,
    structure_to_schedule,
)
from melodica.fluid_r3_profile import FLUID_R3_PROGRAMS
from melodica.generators.melody import MelodyGenerator
from melodica.generators.chord_gen import ChordGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

def generate_track(name, parts, tracks, out_dir, bpm):
    print(f"  > Generating Track: '{name}'...")
    config = IdeaToolConfig(
        style="cinematic", # Dark, high tension
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
    )
    notes_dict = IdeaTool(config).generate()
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
    
    # Crucial: Using the exact FluidR3 GM mappings for highest quality
    instruments_map = {t.name: FLUID_R3_PROGRAMS.get(t.instrument, 0) for t in tracks}
    
    file_path = out_dir / f"{name.replace(' ', '_')}.mid"
    export_multitrack_midi(tracks_data, str(file_path), bpm=bpm, instruments=instruments_map)
    return file_path

def main():
    print("================================================================================")
    print("  A L B U M   G E N E R A T O R :   S H A D O W S   O F   L O R D R A N")
    print("================================================================================")

    out_dir = Path("output/album_dark_souls")
    out_dir.mkdir(exist_ok=True, parents=True)

    # Dark Souls aesthetic demands Harmonic Minor (very dark, classical tension)
    scale = Scale(2, Mode.HARMONIC_MINOR) # D Harmonic Minor

    # --- TRACK 1: Ash and Embers ---
    t1_tracks = [
        TrackConfig(name="Melancholy_Piano", generator=MelodyGenerator(mode="chord_tones", rhythm=get_rhythm("ds_tragic_piano_8ths")), instrument="piano", density=0.7),
        TrackConfig(name="Shrine_Echo", generator=NebulaGenerator(variant="cloud", rhythm=get_rhythm("ds_shrine_silence")), instrument="dark_pad", density=0.4),
        TrackConfig(name="Cello_Weep", generator=MelodyGenerator(mode="downbeat_chord", rhythm=get_rhythm("markov:ballad")), instrument="cello", density=0.5)
    ]
    t1_parts = [
        IdeaPart(
            name="Rest", bars=16, scale=scale, tempo=65, progression_type="coupled_hmm",
            track_phrase_schedules={
                "Melancholy_Piano": structure_to_schedule("A B", 8),
                "Shrine_Echo":      structure_to_schedule("A", 16),
                "Cello_Weep":       structure_to_schedule("R A", 8),
            }
        )
    ]
    generate_track("1 Ash and Embers", t1_parts, t1_tracks, out_dir, 65)

    # --- TRACK 2: The Abyss Marches ---
    t2_tracks = [
        TrackConfig(name="Abyss_March", generator=MelodyGenerator(mode="chord_tones", rhythm=get_rhythm("ds_steady_16th_charge")), instrument="timpani", density=1.0),
        TrackConfig(name="Ashen_Choir", generator=ChordGenerator(voicing="closed", rhythm=get_rhythm("ds_grim_steady_8th")), instrument="choir", density=0.8),
        TrackConfig(name="Tremolo_Tension", generator=StringsEnsembleGenerator(section_size="full", articulation="tremolo"), instrument="tremolo_strings", density=0.9, octave_shift=1),
        TrackConfig(name="Low_Brass", generator=BassGenerator(style="root_fifth"), instrument="tuba", density=0.8, octave_shift=-1)
    ]
    t2_parts = [
        IdeaPart(
            name="March", bars=16, scale=scale, tempo=85, progression_type="coupled_hmm",
            track_phrase_schedules={
                "Abyss_March":     structure_to_schedule("A B", 8),
                "Ashen_Choir":     structure_to_schedule("A", 16),
                "Tremolo_Tension": structure_to_schedule("R A", 8),
                "Low_Brass":       structure_to_schedule("A", 16),
            }
        )
    ]
    generate_track("2 The Abyss Marches", t2_parts, t2_tracks, out_dir, 85)

    # --- TRACK 3: Boreal Waltz ---
    t3_tracks = [
        TrackConfig(name="Dancer_Strings", generator=StringsEnsembleGenerator(section_size="chamber", articulation="sustained", rhythm=get_rhythm("ds_graceful_3_2_swing")), instrument="violin", density=0.9),
        TrackConfig(name="Cold_Music_Box", generator=MelodyGenerator(mode="scale_walk", rhythm=get_rhythm("ds_frozen_city_swing")), instrument="music_box", density=0.7, octave_shift=1),
        TrackConfig(name="Deep_Abyss", generator=DroneGenerator(variant="tonic"), instrument="dark_pad", density=0.5, octave_shift=-1)
    ]
    t3_parts = [
        IdeaPart(
            name="Waltz", bars=16, scale=scale, tempo=95, progression_type="coupled_hmm",
            track_phrase_schedules={
                "Dancer_Strings": structure_to_schedule("A B", 8),
                "Cold_Music_Box": structure_to_schedule("A A:var", 8),
                "Deep_Abyss":     structure_to_schedule("A", 16),
            }
        )
    ]
    generate_track("3 Boreal Waltz", t3_parts, t3_tracks, out_dir, 95)

    # --- TRACK 4: Final Cinder ---
    t4_tracks = [
        TrackConfig(name="Cinder_Drums", generator=MelodyGenerator(mode="chord_tones", rhythm=get_rhythm("ds_final_assault_mixed")), instrument="drums", density=1.0),
        TrackConfig(name="Gael_Agression", generator=MelodyGenerator(mode="scale_walk", rhythm=get_rhythm("ds_relentless_32nd")), instrument="choir", density=1.0),
        TrackConfig(name="Frantic_Strings", generator=StringsEnsembleGenerator(section_size="full", articulation="staccato", rhythm=get_rhythm("ds_relentless_combo_16th")), instrument="strings", density=0.9),
        TrackConfig(name="Boss_Brass", generator=BassGenerator(style="walking"), instrument="brass", density=0.8, octave_shift=-1)
    ]
    t4_parts = [
        IdeaPart(
            name="Phase1", bars=8, scale=scale, tempo=120, progression_type="coupled_hmm",
            track_phrase_schedules={
                "Cinder_Drums":    structure_to_schedule("A", 8),
                "Gael_Agression":  structure_to_schedule("R", 8),
                "Frantic_Strings": structure_to_schedule("A", 8),
                "Boss_Brass":      structure_to_schedule("A", 8),
            }
        ),
        IdeaPart(
            name="Phase2_Berserk", bars=16, scale=scale, tempo=135, progression_type="coupled_hmm",
            track_phrase_schedules={
                "Cinder_Drums":    structure_to_schedule("B C", 8),
                "Gael_Agression":  structure_to_schedule("A B", 8),
                "Frantic_Strings": structure_to_schedule("B", 16),
                "Boss_Brass":      structure_to_schedule("B", 16),
            }
        )
    ]
    generate_track("4 Final Cinder", t4_parts, t4_tracks, out_dir, 120)

    print("\n  SUCCESS! Dark Souls Album 'Shadows of Lordran' generated.")
    print(f"  Files saved in: {out_dir.absolute()}")
    print("================================================================================")

if __name__ == "__main__":
    main()
