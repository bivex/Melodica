# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_epic_orchestra.py — An epic orchestral album showcase.
Focuses on dramatic progression, heavy brass, sweeping strings, and choirs.
"""

import os
from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS
from melodica.generators import (
    MelodyGenerator, BassGenerator, StringsEnsembleGenerator, 
    AmbientPadGenerator, ArpeggiatorGenerator, FluteGenerator
)
from melodica.types import Scale, Mode

def main():
    print("================================================================================")
    print("  E P I C   O R C H E S T R A   —   A L B U M   G E N E R A T O R")
    print("  Focus: Huge dynamics, deep bass, sweeping strings, and dramatic tension")
    print("================================================================================")

    out_dir = Path("output/album_epic_orchestra")
    out_dir.mkdir(exist_ok=True, parents=True)

    # 1. Configuration of the Tracks
    configs = [
        {
            "name": "01_Call_to_Arms",
            "scale": Scale(2, Mode.NATURAL_MINOR),  # D Minor
            "bars": 16,
            "tempo": 85,
            "ts": (4, 4),
            "pillars": ["Im:4.0", "bVI:4.0", "bIII:4.0", "bVII:4.0", "Im:4.0", "bVI:4.0", "IVm:4.0", "V:4.0"]
        },
        {
            "name": "02_The_Siege",
            "scale": Scale(7, Mode.PHRYGIAN),  # G Phrygian
            "bars": 16,
            "tempo": 130,
            "ts": (4, 4),
            "pillars": ["Im:2.0", "bII:2.0", "Im:4.0", "bIII:2.0", "bVII:2.0", "Im:4.0"]
        },
        {
            "name": "03_Aftermath",
            "scale": Scale(9, Mode.AEOLIAN),  # A Aeolian
            "bars": 12,
            "tempo": 60,
            "ts": (3, 4),
            "pillars": ["Im9:6.0", "bVImaj9:6.0", "Im9:6.0", "Vm9:6.0"]
        },
        {
            "name": "04_Victory_March",
            "scale": Scale(0, Mode.MAJOR),  # C Major
            "bars": 16,
            "tempo": 105,
            "ts": (4, 4),
            "pillars": ["I:4.0", "IV:4.0", "V:4.0", "I:4.0"]
        }
    ]

    # 2. Track Definitions
    tracks_common = [
        TrackConfig(
            name="Epic_Strings",
            generator=StringsEnsembleGenerator(section_size="full", articulation="legato", divisi=4),
            instrument="strings", density=0.8, octave_shift=1,
        ),
        TrackConfig(
            name="Low_Brass_Foundation",
            generator=AmbientPadGenerator(voicing="spread"),
            instrument="brass_section", density=0.6, octave_shift=-1,
        ),
        TrackConfig(
            name="Sub_Bass",
            generator=BassGenerator(style="root_only"),
            instrument="contrabass", density=0.6, octave_shift=-2,
        ),
        TrackConfig(
            name="Tension_Arp",
            generator=ArpeggiatorGenerator(pattern="up_down"),
            instrument="string_ensemble_2", density=0.5, octave_shift=0,
        ),
        TrackConfig(
            name="Solo_Flute_Melody",
            generator=FluteGenerator(),
            instrument="flute", density=0.4, octave_shift=2,
        ),
    ]

    for cfg in configs:
        print(f"\n--- Composing: {cfg['name']} ---")

        parts = [IdeaPart(
            name=cfg["name"], bars=cfg["bars"],
            scale=cfg["scale"], tempo=cfg["tempo"],
            time_signature=cfg["ts"],
            progression_type="constrained_hmm",
            progression_list=cfg["pillars"],
        )]

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            parts=parts,
            tracks=tracks_common,
            use_tension_curve=True
        )

        notes_dict = IdeaTool(tool_config).generate()
        tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

        filename = f"{cfg['name']}.mid"
        filepath = out_dir / filename
        
        from melodica.midi import export_multitrack_midi
        instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks_common}
        
        export_multitrack_midi(
            tracks_data, 
            str(filepath), 
            bpm=cfg["tempo"],
            time_sig=cfg["ts"],
            instruments=instruments_map
        )
        print(f"    ✓ Exported {filename}")

    print("\n================================================================================")
    print(f"  PRODUCTION COMPLETE. Output: {out_dir}")
    print("================================================================================")

if __name__ == "__main__":
    main()
