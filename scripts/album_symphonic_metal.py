# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_symphonic_metal.py — A massive 10-track Symphonic Metal epic.
Blends academic orchestral arrangements with heavy metal guitars and drums.
Showcases the 12-chord Cinematic HMM, complex forms, and extreme tension curves.
"""

import os
from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS
from melodica.generators import (
    StringsEnsembleGenerator, BrassSectionGenerator, ChoirAahsGenerator,
    TimpaniGenerator, PowerChordGenerator, RiffGenerator, TremoloPickingGenerator,
    TrapDrumsGenerator, BassGenerator, ArpeggiatorGenerator, SynthChoirGenerator,
    WoodwindsEnsembleGenerator
)
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

def main():
    print("================================================================================")
    print("  S Y M P H O N Y   O F   S T E E L   &   F I R E")
    print("  10-Track Symphonic Metal Epic | 12-Chord Constrained HMM")
    print("================================================================================")

    out_dir = Path("output/album_symphonic_metal")
    out_dir.mkdir(exist_ok=True, parents=True)

    # The Massive Hybrid Arrangement (Final Balanced 5-Star Spacing)
    hybrid_orchestra = [
        # --- The Orchestra ---
        # Choir moved to high register (Shift +2)
        TrackConfig(name="Epic_Choir", generator=ChoirAahsGenerator(voice_count=10, dynamics="ff"), instrument="choir", density=0.8, octave_shift=2),
        
        # Violins shifted to +3 (safe range)
        TrackConfig(name="Violins_Spiccato", generator=StringsEnsembleGenerator(articulation="staccato", divisi=1), instrument="violin", density=0.9, octave_shift=3),
        TrackConfig(name="Cellos_Legato", generator=StringsEnsembleGenerator(articulation="legato", divisi=2), instrument="cello", density=0.7, octave_shift=0),
        
        # Brass switched to RiffGenerator to anchor the low-mid "wall"
        TrackConfig(name="Doom_Brass", generator=RiffGenerator(riff_pattern="gallop", power_chord=True), instrument="brass", density=0.9, octave_shift=-1),
        
        # Woodwinds high but not extreme
        TrackConfig(name="Woodwinds", generator=WoodwindsEnsembleGenerator(ensemble_mode="full"), instrument="flute", density=0.6, octave_shift=2),
        
        # Timpani dropped deep for impact
        TrackConfig(name="Timpani_Strikes", generator=TimpaniGenerator(stroke_pattern="single"), instrument="timpani", density=1.0, octave_shift=-3),
        
        # Harpsichord isolated
        TrackConfig(name="Gothic_Harpsichord", generator=ArpeggiatorGenerator(pattern="up_down", octaves=1), instrument="harpsichord", density=0.4, octave_shift=1),
        
        # --- The Metal Band ---
        # Rhythm chugs provide the mid-low foundation
        TrackConfig(name="Rhythm_Guitars", generator=PowerChordGenerator(pattern="chug"), instrument="distortion_guitar", density=0.7, octave_shift=-1),
        
        # Lead Tremolo shifted higher to clear the center
        TrackConfig(name="Lead_Tremolo", generator=TremoloPickingGenerator(speed=0.1875), instrument="overdrive_guitar", density=0.4, octave_shift=1),
        
        # Metal Bass: Constant driving gallop at -1 (fills 36-48 zone)
        TrackConfig(name="Metal_Bass", generator=RiffGenerator(riff_pattern="gallop", power_chord=False), instrument="electric_bass", density=1.0, octave_shift=-1),
        TrackConfig(name="Double_Kick_Drums", generator=TrapDrumsGenerator(variant="heavy"), instrument="drums", density=1.0, octave_shift=-1),
    ]

    # Track 1: Overture - The Awakening (E Minor)
    t1 = [
        IdeaPart(name="Dark_Intro", bars=8, scale=Scale(4, Mode.NATURAL_MINOR), progression_type="constrained_hmm", progression_list=["Im9:8.0"], track_mute=["Rhythm_Guitars", "Lead_Tremolo", "Double_Kick_Drums"]),
        IdeaPart(name="The_Blast", bars=8, scale=Scale(4, Mode.NATURAL_MINOR), progression_type="constrained_hmm", progression_list=["Im:4.0", "bVImaj7:4.0", "V7alt:4.0"])
    ]

    # Track 2: Blood on the Snow (C Phrygian Dominant)
    t2 = [
        IdeaPart(name="March", bars=16, scale=Scale(0, Mode.PHRYGIAN_DOMINANT), progression_type="constrained_hmm", progression_list=["Im:8.0", "bIImaj7:4.0", "viidim:4.0"]),
        IdeaPart(name="Chorus", bars=8, scale=Scale(0, Mode.PHRYGIAN_DOMINANT), progression_type="constrained_hmm", progression_list=["bVImaj9:4.0", "bVIIadd9:4.0", "Im:4.0"])
    ]

    # Track 3: The Clockwork God (F# Locrian - Extreme Dissonance)
    t3 = [
        IdeaPart(name="Grind", bars=12, scale=Scale(6, Mode.LOCRIAN), progression_type="constrained_hmm", progression_list=["Idim:4.0", "bVmaj7:4.0", "bIImaj9:4.0"])
    ]

    # Track 4: Ballad of the Fallen (A Aeolian)
    t4 = [
        IdeaPart(name="Acoustic", bars=16, scale=Scale(9, Mode.AEOLIAN), progression_type="constrained_hmm", progression_list=["Im9:8.0", "IVm9:4.0", "bVImaj9:4.0"], track_mute=["Rhythm_Guitars", "Double_Kick_Drums", "Doom_Brass"])
    ]

    # Track 5: Ride of the Valkyries (D Dorian)
    t5 = [
        IdeaPart(name="Gallop", bars=16, scale=Scale(2, Mode.DORIAN), progression_type="constrained_hmm", progression_list=["Im:8.0", "IVmaj9:4.0", "Im:4.0"])
    ]

    # Track 6: Interlude - Whispers in the Dark (G Harmonic Minor)
    t6 = [
        IdeaPart(name="Whispers", bars=8, scale=Scale(7, Mode.HARMONIC_MINOR), progression_type="constrained_hmm", progression_list=["Im9:4.0", "Vaug:4.0"], track_mute=["Rhythm_Guitars", "Lead_Tremolo", "Double_Kick_Drums", "Timpani_Strikes"])
    ]

    # Track 7: Siege of the Iron Citadel (B Minor)
    t7 = [
        IdeaPart(name="Assault", bars=16, scale=Scale(11, Mode.NATURAL_MINOR), progression_type="constrained_hmm", progression_list=["Im:4.0", "bVImaj7:4.0", "IVm7:4.0", "V7:4.0"]),
        IdeaPart(name="Breach", bars=8, scale=Scale(11, Mode.NATURAL_MINOR), progression_type="constrained_hmm", progression_list=["bVImaj9:4.0", "V7alt:4.0"])
    ]

    # Track 8: The Oracle's Prophecy (Eb Lydian)
    t8 = [
        IdeaPart(name="Vision", bars=16, scale=Scale(3, Mode.LYDIAN), progression_type="constrained_hmm", progression_list=["Imaj9:8.0", "IIadd9:4.0", "viidim:4.0"])
    ]

    # Track 9: Final Stand (E Harmonic Minor)
    t9 = [
        IdeaPart(name="Pre_Battle", bars=8, scale=Scale(4, Mode.HARMONIC_MINOR), progression_type="constrained_hmm", progression_list=["Im9:4.0", "V7:4.0"], track_mute=["Rhythm_Guitars", "Double_Kick_Drums"]),
        IdeaPart(name="Apocalypse", bars=24, scale=Scale(4, Mode.HARMONIC_MINOR), progression_type="constrained_hmm", progression_list=["Im:8.0", "bVImaj9:4.0", "Idim:4.0", "V7alt:8.0"])
    ]

    # Track 10: Ashes to Ashes (C Ionian)
    t10 = [
        IdeaPart(name="Requiem", bars=16, scale=Scale(0, Mode.MAJOR), progression_type="constrained_hmm", progression_list=["Imaj9:8.0", "IVadd9:4.0", "V7:4.0"]),
        IdeaPart(name="Fade", bars=8, scale=Scale(0, Mode.MAJOR), progression_type="constrained_hmm", progression_list=["Iadd9:8.0"], track_mute=["Rhythm_Guitars", "Lead_Tremolo", "Double_Kick_Drums", "Doom_Brass", "Timpani_Strikes"])
    ]

    album_configs = [
        ("01_Overture", 85, (4, 4), t1),
        ("02_Blood_On_Snow", 130, (4, 4), t2),
        ("03_Clockwork_God", 110, (5, 4), t3),
        ("04_Ballad_Fallen", 65, (3, 4), t4),
        ("05_Valkyrie_Ride", 150, (4, 4), t5),
        ("06_Whispers_Dark", 70, (4, 4), t6),
        ("07_Iron_Citadel", 140, (4, 4), t7),
        ("08_Oracles_Prophecy", 95, (4, 4), t8),
        ("09_Final_Stand", 160, (4, 4), t9),
        ("10_Ashes_to_Ashes", 60, (4, 4), t10),
    ]

    for name, tempo, ts, parts in album_configs:
        print(f"\n--- Composing: {name} ({ts[0]}/{ts[1]}, {tempo} BPM) ---")
        
        tool_config = IdeaToolConfig(
            style="orchestral", # Use orchestral base for voice leading rules
            parts=parts,
            tracks=hybrid_orchestra,
            use_tension_curve=True,
            use_voice_leading=True,
            tempo=tempo,
            time_signature=ts
        )

        try:
            notes_dict = IdeaTool(tool_config).generate()
            tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

            filepath = out_dir / f"{name}.mid"
            instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in hybrid_orchestra}
            
            export_multitrack_midi(
                tracks_data, 
                str(filepath), 
                bpm=tempo,
                time_sig=ts,
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
