# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_symphony_fallen.py — Advanced Structural Orchestral Album.
Showcases Multi-Part IdeaPart compositions with Constrained HMM and dynamic density.
"""

import os
from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS
from melodica.generators import (
    MelodyGenerator, BassGenerator, StringsEnsembleGenerator, 
    AmbientPadGenerator, ArpeggiatorGenerator, SynthEffectsGenerator,
    CelestaGenerator, FluteGenerator, TimpaniGenerator, BrassSectionGenerator,
    WoodwindsEnsembleGenerator
)
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

def main():
    print("================================================================================")
    print("  S Y M P H O N Y   O F   T H E   F A L L E N   —   B a t t l e   T e s t")
    print("  Structure: Multi-Part Sections | Harmonization: Constrained 12-Chord HMM")
    print("================================================================================")

    out_dir = Path("output/album_symphony_fallen")
    out_dir.mkdir(exist_ok=True, parents=True)

    # Common Orchestral Template
    orchestra = [
        TrackConfig(name="Violins", generator=StringsEnsembleGenerator(divisi=2), instrument="violin", density=0.7),
        TrackConfig(name="Cellos", generator=StringsEnsembleGenerator(divisi=2), instrument="cello", density=0.6, octave_shift=-1),
        TrackConfig(name="Contrabass", generator=BassGenerator(style="root_only"), instrument="contrabass", density=0.5, octave_shift=-2),
        TrackConfig(name="Horns", generator=BrassSectionGenerator(), instrument="french_horn", density=0.4),
        TrackConfig(name="Trombones", generator=BrassSectionGenerator(), instrument="trombone", density=0.3, octave_shift=-1),
        TrackConfig(name="Woodwinds", generator=WoodwindsEnsembleGenerator(), instrument="flute", density=0.4),
        TrackConfig(name="Timpani", generator=TimpaniGenerator(), instrument="timpani", density=0.3, octave_shift=-2),
        TrackConfig(name="Celesta", generator=ArpeggiatorGenerator(), instrument="celesta", density=0.4, octave_shift=1),
    ]

    # Track 1: The Gathering Storm (E Dorian)
    t1_parts = [
        IdeaPart(name="Mist", bars=4, scale=Scale(4, Mode.DORIAN), progression_type="constrained_hmm", progression_list=["Im9:4.0"], track_mute=["Horns", "Trombones", "Timpani"]),
        IdeaPart(name="Thunder", bars=8, scale=Scale(4, Mode.DORIAN), progression_type="constrained_hmm", progression_list=["Im9:4.0", "bVIIadd9:4.0", "IVmaj9:4.0", "V7:4.0"], style="cinematic_epic")
    ]

    # Track 2: March of the Khalsa (Arabic Sikah)
    t2_parts = [
        IdeaPart(name="Rhythm", bars=4, scale=Scale(4, Mode.ARABIC_SIKAH), progression_type="from_list", progression_list=["Im:16.0"], track_mute=["Violins", "Cellos", "Horns"]),
        IdeaPart(name="March", bars=12, scale=Scale(4, Mode.ARABIC_SIKAH), progression_type="constrained_hmm", progression_list=["Im7:4.0", "bIIadd9:12.0", "V7alt:32.0"])
    ]

    # Track 3: The Broken Throne (D Minor / Aeolian)
    t3_parts = [
        IdeaPart(name="Elegy", bars=8, scale=Scale(2, Mode.AEOLIAN), progression_type="constrained_hmm", progression_list=["Im9:4.0", "bVImaj9:4.0", "Idim:4.0"], track_density={"Violins": 0.3, "Cellos": 0.8}),
        IdeaPart(name="Rebirth", bars=8, scale=Scale(2, Mode.AEOLIAN), progression_type="constrained_hmm", progression_list=["bVImaj9:4.0", "bVIIadd9:4.0", "Imaj9:4.0"])
    ]

    # Track 4: Sky-Clad Warriors (Lydian)
    t4_parts = [
        IdeaPart(name="Ascent", bars=16, scale=Scale(0, Mode.LYDIAN), progression_type="constrained_hmm", progression_list=["Imaj9:8.0", "IIadd9:8.0"])
    ]

    # Track 5: Descent into the Crypt (Phrygian Dominant)
    t5_parts = [
        IdeaPart(name="Entrance", bars=4, scale=Scale(4, Mode.PHRYGIAN_DOMINANT), progression_type="constrained_hmm", progression_list=["Im:4.0"]),
        IdeaPart(name="Horror", bars=8, scale=Scale(4, Mode.PHRYGIAN_DOMINANT), progression_type="constrained_hmm", progression_list=["Im:2.0", "bIIaug:2.0", "Idim:2.0"], track_density={"Timpani": 0.8, "Trombones": 0.7})
    ]

    # Track 6: Eternal Light (Ionian)
    t6_parts = [
        IdeaPart(name="Final_Hymn", bars=16, scale=Scale(7, Mode.MAJOR), progression_type="constrained_hmm", progression_list=["Imaj9:8.0", "IVmaj9:4.0", "Vadd9:4.0"])
    ]

    album_configs = [
        ("01_Gathering_Storm", t1_parts),
        ("02_March_of_Khalsa", t2_parts),
        ("03_Broken_Throne", t3_parts),
        ("04_Sky_Warriors", t4_parts),
        ("05_Crypt_Descent", t5_parts),
        ("06_Eternal_Light", t6_parts),
    ]

    for name, parts in album_configs:
        print(f"\n--- Composing: {name} ---")
        
        tool_config = IdeaToolConfig(
            style="orchestral",
            parts=parts,
            tracks=orchestra,
            use_tension_curve=True,
            use_voice_leading=True
        )

        try:
            notes_dict = IdeaTool(tool_config).generate()
            tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

            filepath = out_dir / f"{name}.mid"
            instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in orchestra}
            
            export_multitrack_midi(
                tracks_data, 
                str(filepath), 
                bpm=parts[0].tempo or 100, # Fallback to 100
                time_sig=parts[0].time_signature or (4, 4),
                instruments=instruments_map
            )
            print(f"    ✓ Exported {name}.mid")
        except Exception as e:
            print(f"    ✗ Error in {name}: {e}")

    print("\n================================================================================")
    print(f"  ALBUM COMPLETE. Output: {out_dir}")
    print("================================================================================")

if __name__ == "__main__":
    main()
