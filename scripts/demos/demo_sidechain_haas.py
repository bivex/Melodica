# Copyright (c) 2026 Bivex
# Standalone Demo for AutoPumper (Sidechain) and Haas Widener

import sys
import numpy as np
from pathlib import Path
from pedalboard.io import AudioFile

from melodica.dsp_effects import AutoPumper, HaasWidener

def main():
    print("\n" + "="*80)
    print(" 🌊  MELODICA AUTO-SIDECHAIN & HAAS WIDENER DEMO  🌊")
    print("="*80 + "\n")
    
    # We will use the previously generated raw multitrack (or serum raw)
    # Let's try serum_raw.wav first as it's a bassline!
    input_path = Path("/Volumes/External/Code/Melodica/output/serum_raw.wav")
    if not input_path.exists():
        input_path = Path("/Volumes/External/Code/Melodica/output/demo_raw.wav")
        if not input_path.exists():
            print("❌ Error: No raw WAV found. Run demo_serum_dsp.py or demo_dsp_mastering.py first!")
            return

    output_path = Path("/Volumes/External/Code/Melodica/output/demo_sidechain_haas.wav")

    print(f"📥 Loading raw audio: {input_path.name} ...")
    with AudioFile(str(input_path)) as f:
        audio = f.read(f.frames)
        sr = f.samplerate

    # Effect 1: HAAS EFFECT (Insane Stereo Width)
    # We delay the right channel by 15ms
    print("🌌  [DSP] Applying Haas Stereo Effect...")
    print("   - Delaying Right Channel by 15.0 ms")
    haas = HaasWidener(delay_ms=15.0, delay_right=True, sample_rate=sr)
    audio = haas.process(audio)

    # Effect 2: AUTO-PUMPER (EDM Sidechain Ducking)
    # We duck the volume every quarter note at 140 BPM (or 120 depending on track, we'll use 140 for Serum Trap)
    # If the track is demo_raw.wav (120 BPM), we use 120.
    bpm = 140.0 if "serum" in input_path.name else 120.0
    
    print(f"📈  [DSP] Applying Auto-Pumper (Sidechain Ducking) at {bpm} BPM...")
    print("   - Depth: 100% (Complete silence on the kick hit)")
    print("   - Curve Shape: 3.0 (Stays down slightly longer, then bounces up)")
    
    pumper = AutoPumper(bpm=bpm, depth=1.0, shape=3.0, sample_rate=sr)
    audio = pumper.process(audio)

    print(f"💾 Saving processed audio to: {output_path.name} ...\n")
    with AudioFile(str(output_path), "w", sr, audio.shape[0]) as f:
        f.write(audio)

    print("🎉  Effects Processing Complete!")
    print("🎧  Listen to the bouncy, impossibly wide result here:")
    print(f"   file://{output_path.absolute()}\n")

if __name__ == "__main__":
    main()
