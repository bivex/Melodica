# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_matsuri_procession.py — Japanese Festival Album Generator.

Album: "Matsuri Procession: Spirits of the Night"
Tracks:
1. Gathering at the Shrine (Eskibeat x Gagaku hybrid)
2. The Golden Float (High-energy Yatai Bayashi)
3. Night Dance of the Spirits (Bon Odori)
4. Departure of the Gods (Post-festive Downtempo)
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.generators.melody import MelodyGenerator
from melodica.generators.chord_gen import ChordGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.drone import DroneGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

def generate_track(name, parts, tracks, out_dir, bpm):
    print(f"  > Generating Track: '{name}'...")
    config = IdeaToolConfig(
        style="japanese",
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
    )
    notes_dict = IdeaTool(config).generate()
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
    instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks}
    
    file_path = out_dir / f"{name.replace(' ', '_')}.mid"
    export_multitrack_midi(tracks_data, str(file_path), bpm=bpm, instruments=instruments_map)
    return file_path

def main():
    print("================================================================================")
    print("  A L B U М   G E N E R A T O R :   M A T S U R I   P R O C E S S I O N")
    print("================================================================================")

    out_dir = Path("output/album_matsuri_procession")
    out_dir.mkdir(exist_ok=True, parents=True)

    # Common Scale: Japanese In-Sen (Approximate A Minor)
    scale = Scale(9, Mode.NATURAL_MINOR)

    # --- TRACK 1: Gathering at the Shrine ---
    t1_tracks = [
        TrackConfig("Shrine_Drone", "drone", "dark_pad", density=0.6, octave_shift=-1, params={"variant": "tonic"}),
        TrackConfig("Gagaku_Stabs", "chord", "harpsichord", density=0.7, params={"rhythm": get_rhythm("gagaku_kakko_pattern")}),
        TrackConfig("Distant_Taiko", "melody", "drums", density=0.5, params={"mode": "chord_tones", "rhythm": get_rhythm("noh_taiko_mitsuji")})
    ]
    t1_parts = [IdeaPart("Opening", 16, scale, 75)]
    generate_track("1 Gathering at the Shrine", t1_parts, t1_tracks, out_dir, 75)

    # --- TRACK 2: The Golden Float ---
    t2_tracks = [
        TrackConfig("Festival_Drums", "melody", "drums", density=1.0, params={"mode": "chord_tones", "rhythm": get_rhythm("yatai_bayashi")}),
        TrackConfig("Shamisen_Lead", "melody", "shamisen", density=0.9, params={"mode": "scale_walk", "rhythm": get_rhythm("shamisen_jongara")}),
        TrackConfig("Heavy_Bass", "bass", "synth_bass", density=0.8, octave_shift=-1, params={"style": "root_fifth"}),
        TrackConfig("Flute_Call", "melody", "flute", density=0.6, params={"mode": "downbeat_chord", "rhythm": get_rhythm("markov:ballad")})
    ]
    t2_parts = [
        IdeaPart("Procession", 8, scale, 140),
        IdeaPart("Climax", 8, scale, 145)
    ]
    generate_track("2 The Golden Float", t2_parts, t2_tracks, out_dir, 140)

    # --- TRACK 3: Night Dance ---
    t3_tracks = [
        TrackConfig("Bon_Odori_Groove", "melody", "drums", density=0.9, params={"mode": "chord_tones", "rhythm": get_rhythm("bon_odori")}),
        TrackConfig("Koto_Arp", "melody", "koto", density=0.8, params={"mode": "scale_walk", "rhythm": get_rhythm("koto_sakura_sakura")}),
        TrackConfig("Spirit_Voices", "nebula", "voice", density=0.4, params={"variant": "cloud"})
    ]
    t3_parts = [IdeaPart("Dance", 16, scale, 120)]
    generate_track("3 Night Dance of the Spirits", t3_parts, t3_tracks, out_dir, 120)

    # --- TRACK 4: Departure of the Gods ---
    t4_tracks = [
        TrackConfig("Fading_Drone", "drone", "dark_pad", density=0.5, octave_shift=-2, params={"variant": "dominant"}),
        TrackConfig("Lone_Shakuhachi", "melody", "flute", density=0.4, params={"mode": "downbeat_chord", "rhythm": get_rhythm("shakuhachi_ma")}),
        TrackConfig("Vinyl_Crackle", "nebula", "synth_fx", density=0.2, params={"variant": "swell"})
    ]
    t4_parts = [IdeaPart("Ending", 8, scale, 65)]
    generate_track("4 Departure of the Gods", t4_parts, t4_tracks, out_dir, 65)

    print("\n  SUCCESS! Album 'Matsuri Procession' generated.")
    print(f"  Files saved in: {out_dir.absolute()}")
    print("================================================================================")

if __name__ == "__main__":
    main()
