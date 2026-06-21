# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/other/album_elegies_for_piano.py — "Elegies of the Heart"
A 4-movement tragic, beautiful piano suite leveraging the CoupledHMMHarmonizer.
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

# Generators
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.broken_chord import BrokenChordGenerator

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def generate_elegies_for_piano():
    album_dir = Path("output/album_elegies_for_piano")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("        E L E G I E S   O F   T H E   H E A R T")
    print("        A Beautiful Tragic Piano Suite (4 Movements)")
    print("=" * 80)

    tracks_configs = [
        {
            "id": "01",
            "name": "Requiem_for_a_Lost_Friend",
            "description": "Movement I: Slow, heavy grief. G minor. Left hand plays romantic arpeggios, right hand weeps.",
            "tempo": 52,
            "scale": Scale(root=7, mode=Mode.NATURAL_MINOR),  # G Minor
            "bars": 32,
            "pattern": "romantic",
            "subdivision": 0.5,  # 8th notes at 52 BPM
            "melody_density": 0.35
        },
        {
            "id": "02",
            "name": "Cold_Autumn_Rain",
            "description": "Movement II: Flowing arpeggios of sadness. C# minor. Left hand plays Chopin-style arpeggios.",
            "tempo": 76,
            "scale": Scale(root=1, mode=Mode.NATURAL_MINOR),  # C# Minor
            "bars": 40,
            "pattern": "chopin",
            "subdivision": 0.25,  # 16th notes
            "melody_density": 0.45
        },
        {
            "id": "03",
            "name": "Solitary_Shadow",
            "description": "Movement III: Introspective chill, fragile high register. F minor. Left hand rolling arpeggios.",
            "tempo": 45,
            "scale": Scale(root=5, mode=Mode.NATURAL_MINOR),  # F Minor
            "bars": 24,
            "pattern": "rolling",
            "subdivision": 0.5,  # 8th notes
            "melody_density": 0.30
        },
        {
            "id": "04",
            "name": "Echoes_of_Farewell",
            "description": "Movement IV: Grand tragic climax, final release. D minor. Left hand plays dramatic Liszt sweeps.",
            "tempo": 60,
            "scale": Scale(root=2, mode=Mode.NATURAL_MINOR),  # D Minor
            "bars": 48,
            "pattern": "liszt",
            "subdivision": 0.25,  # 16th notes
            "melody_density": 0.55
        }
    ]

    for cfg in tracks_configs:
        print(f"\n--- Constructing Movement {cfg['id']}: {cfg['name']} ---")
        print(f"  {cfg['description']}")
        
        parts = [IdeaPart(
            name=cfg['name'], 
            bars=cfg['bars'], 
            scale=cfg['scale'], 
            tempo=cfg['tempo'],
            progression_type="coupled_hmm"
        )]

        track_list = [
            TrackConfig(
                name="Left_Hand_Arp", 
                generator=BrokenChordGenerator(
                    params=GeneratorParams(density=0.85),
                    pattern=cfg['pattern'], 
                    subdivision=cfg['subdivision'],
                    spread=2,
                    velocity_envelope="arch"
                ), 
                instrument="piano", 
                density=0.85, 
                octave_shift=-1
            ),
            TrackConfig(
                name="Right_Hand_Melody", 
                generator=MelodyGenerator(
                    params=GeneratorParams(
                        density=cfg['melody_density'],
                        leap_probability=0.25
                    ),
                    motif_probability=0.8,
                    note_range_low=58,
                    note_range_high=86,
                    first_note="tonic",
                    last_note="last_chord_root"
                ), 
                instrument="piano", 
                density=0.6,
                octave_shift=0
            )
        ]

        tool_config = IdeaToolConfig(
            style="classical_solo",  # Piano solo style
            workflow="generate_all",
            use_tension_curve=True,
            use_harmonic_verifier=True,
            target_lufs=-15.0,
            parts=parts,
            tracks=track_list
        )

        notes_dict = IdeaTool(tool_config).generate()
        tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
        
        # Display the generated HMM chords
        chords = notes_dict.get("_chords", [])
        chord_names = [f"{NOTE_NAMES[c.root]} {c.quality.name}" for c in chords]
        print(f"  ➔ Generated chords: {' ➔ '.join(chord_names)}")

        export_multitrack_midi(
            tracks_data,
            str(album_dir / f"{cfg['id']}_{cfg['name']}.mid"),
            bpm=cfg['tempo'],
            key=cfg['scale'],
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set()),
            instruments={"Left_Hand_Arp": 1, "Right_Hand_Melody": 1}
        )
        
        print(f"  ➔ Movement '{cfg['name']}' finalized.")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: ELEGIES OF THE HEART")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)

if __name__ == "__main__":
    generate_elegies_for_piano()
