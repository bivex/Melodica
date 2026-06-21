# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/ambient/album_abyssal_relaxation.py — "Abyssal Relaxation"
A deep ambient sub-bass album designed for deep relaxation, sleep, and meditation.
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

# Generators
from melodica.generators import GeneratorParams
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator
from melodica.generators.harp import HarpGenerator

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def generate_abyssal_relaxation():
    album_dir = Path("output/album_abyssal_relaxation")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("        A B Y S S A L   R E L A X A T I O N")
    print("        Deep Sub-Bass Ambient Album for Drowning & Relaxation")
    print("=" * 80)

    tracks_configs = [
        {
            "id": "01",
            "name": "Abyssal_Plain",
            "description": "Movement I: Warm, slow waves of sub-bass. C Lydian. Pulsing doom-style bass.",
            "tempo": 50,
            "scale": Scale(root=0, mode=Mode.LYDIAN),  # C Lydian (spacey and bright but set ultra low)
            "bars": 32,
            "bass_mode": "doom",
            "bass_octave": 1,
            "note_duration": 8.0,
            "has_sparkles": False
        },
        {
            "id": "02",
            "name": "Subterranean_Currents",
            "description": "Movement II: Deep dub pulses. A minor. Safe, rhythmic sub-bass waves.",
            "tempo": 60,
            "scale": Scale(root=9, mode=Mode.NATURAL_MINOR),  # A Minor
            "bars": 40,
            "bass_mode": "dub",
            "bass_octave": 2,
            "note_duration": 4.0,
            "has_sparkles": False
        },
        {
            "id": "03",
            "name": "Bioluminescent_Depths",
            "description": "Movement III: Echoing depths. Eb major. Extremely slow bass with sparse high-register sparkles.",
            "tempo": 45,
            "scale": Scale(root=3, mode=Mode.MAJOR),  # Eb Major
            "bars": 24,
            "bass_mode": "doom",
            "bass_octave": 1,
            "note_duration": 12.0,
            "has_sparkles": True
        },
        {
            "id": "04",
            "name": "Weightless",
            "description": "Movement IV: Infinite floating. F Lydian. Clean sub-bass and warm celestial drones.",
            "tempo": 55,
            "scale": Scale(root=5, mode=Mode.LYDIAN),  # F Lydian
            "bars": 36,
            "bass_mode": "doom",
            "bass_octave": 2,
            "note_duration": 6.0,
            "has_sparkles": True
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
            # 1. Warm Analog Drone (Foundation)
            TrackConfig(
                name="Sub_Drone",
                generator=DroneGenerator(
                    params=GeneratorParams(density=0.9),
                    variant="power"
                ),
                instrument="pad",
                density=0.9,
                octave_shift=-1
            ),
            # 2. Deep Sub-Bass (Active melody/pulse)
            TrackConfig(
                name="Deep_Bass",
                generator=DarkBassGenerator(
                    params=GeneratorParams(density=0.7),
                    mode=cfg['bass_mode'],
                    octave=cfg['bass_octave'],
                    note_duration=cfg['note_duration'],
                    velocity_level=0.6,
                    movement="root_only"
                ),
                instrument="bass",
                density=0.7,
                octave_shift=-1
            ),
            # 3. Ambient Filter Sweeps (Atmosphere)
            TrackConfig(
                name="Ambient_Pad",
                generator=SciFiUnderscoreGenerator(
                    params=GeneratorParams(density=0.65)
                ),
                instrument="pad",
                density=0.65,
                octave_shift=0
            )
        ]

        if cfg['has_sparkles']:
            # 4. Sparse High Sparkles (Glow effect)
            track_list.append(
                TrackConfig(
                    name="Luminescent_Sparkles",
                    generator=HarpGenerator(
                        params=GeneratorParams(density=0.25)
                    ),
                    instrument="harp",
                    density=0.25,
                    octave_shift=1
                )
            )

        tool_config = IdeaToolConfig(
            style="ambient_relaxation",  # Ambient relax style
            workflow="generate_all",
            use_tension_curve=False,  # Keep it completely flat/hypnotic
            use_harmonic_verifier=True,
            target_lufs=-18.0,  # Very quiet and dynamic
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
            instruments={
                "Sub_Drone": 90,        # Warm Pad
                "Deep_Bass": 39,        # Synth Bass 2 (warm/sub)
                "Ambient_Pad": 89,      # Pad (New Age)
                "Luminescent_Sparkles": 46 # Harp
            }
        )
        
        print(f"  ➔ Movement '{cfg['name']}' finalized.")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: ABYSSAL RELAXATION")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)

if __name__ == "__main__":
    generate_abyssal_relaxation()
