# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_cinematic_lush.py — Showcase for the 12-chord Cinematic HMM.
Focuses on Major9, Minor9, and Add9 textures.
"""

import os
from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS
from melodica.generators import (
    MelodyGenerator, BassGenerator, StringsEnsembleGenerator, 
    AmbientPadGenerator, ArpeggiatorGenerator, SynthEffectsGenerator,
    CelestaGenerator, FluteGenerator
)
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

def main():
    print("================================================================================")
    print("  C I N E M A T I C   L U S H   —   H M M   9 t h s   S h o w c a s e")
    print("  Focus: Major9, Minor9, Add9  |  Lush Orchestral Textures")
    print("================================================================================")

    out_dir = Path("output/album_cinematic_lush")
    out_dir.mkdir(exist_ok=True, parents=True)

    # 1. Configuration
    configs = [
        {
            "name": "01_Ethereal_Dawn",
            "scale": Scale(0, Mode.LYDIAN), # C Lydian for that dreamy shimmer
            "bars": 8,
            "tempo": 65,
            "ts": (4, 4),
            "pillars": ["Imaj9:4.0", "IIadd9:4.0", "IVmaj9:4.0"]
        },
        {
            "name": "02_Neon_Nocturne",
            "scale": Scale(2, Mode.DORIAN), # D Dorian for urban melancholy
            "bars": 8,
            "tempo": 72,
            "ts": (4, 4),
            "pillars": ["Im9:4.0", "IVadd9:4.0", "bVIImaj9:4.0"]
        },
        {
            "name": "03_Glacial_Solitude",
            "scale": Scale(9, Mode.AEOLIAN), # A Minor for cold depth
            "bars": 12,
            "tempo": 58,
            "ts": (3, 4),
            "pillars": ["Im9:6.0", "bVImaj9:6.0", "bIIIadd9:6.0"]
        },
        {
            "name": "04_Climax_of_Tandumi",
            "scale": Scale(4, Mode.ARABIC_SIKAH), # E Sikah
            "bars": 16,
            "tempo": 110,
            "ts": (4, 4),
            "pillars": ["Im7:4.0"] # Just start with minor, let HMM build tension
        }
    ]

    # 2. Track Definitions
    tracks_common = [
        TrackConfig(
            name="Lush_Strings",
            generator=StringsEnsembleGenerator(section_size="full", articulation="legato", divisi=4),
            instrument="strings", density=0.8,
        ),
        TrackConfig(
            name="Cinematic_Pad",
            generator=AmbientPadGenerator(voicing="spread"),
            instrument="dark_pad", density=0.7, octave_shift=-1,
        ),
        TrackConfig(
            name="Deep_Bass",
            generator=BassGenerator(style="root_only"),
            instrument="contrabass", density=0.6, octave_shift=-2,
        ),
        TrackConfig(
            name="Sparkle_Arp",
            generator=ArpeggiatorGenerator(pattern="up_down"),
            instrument="celesta", density=0.4, octave_shift=2,
        ),
        TrackConfig(
            name="Lead_Flute",
            generator=FluteGenerator(),
            instrument="flute", density=0.5, octave_shift=1,
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
        
        # Simple MIDI export logic
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
