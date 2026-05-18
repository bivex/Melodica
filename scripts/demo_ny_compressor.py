# Copyright (c) 2026 Bivex
# Standalone Demo for New York (Parallel) Compression

import sys
import numpy as np
from pathlib import Path
from pedalboard.io import AudioFile
from melodica.ny_compressor import NewYorkCompressor

def main():
    print("\n" + "="*80)
    print(" 🗽  MELODICA NEW YORK (PARALLEL) COMPRESSION DEMO  🗽")
    print("="*80 + "\n")
    
    input_path = Path("/Volumes/External/Code/Melodica/output/demo_raw.wav")
    output_path = Path("/Volumes/External/Code/Melodica/output/demo_ny_compressed.wav")
    
    if not input_path.exists():
        print(f"❌ Error: Could not find '{input_path.name}'. Please run scripts/demo_dsp_mastering.py first!")
        sys.exit(1)

    print(f"📥 [LOAD] Loading raw, unmastered mix: {input_path.name} ...")
    with AudioFile(str(input_path)) as f:
        audio = f.read(f.frames)
        sr = f.samplerate

    # Calculate initial stats
    rms_raw = np.sqrt(np.mean(audio ** 2))
    rms_db_raw = 20 * np.log10(rms_raw + 1e-9)
    peak_db_raw = 20 * np.log10(np.max(np.abs(audio)) + 1e-9)
    
    print(f"   - Initial RMS Loudness:  {rms_db_raw:>6.1f} dBFS")
    print(f"   - Initial Peak Level:    {peak_db_raw:>6.1f} dBFS\n")

    print("🎛️  [DSP] Applying Heavy New York (Parallel) Compression...")
    print("   - Dry Mix: 75% (Preserving the punchy transient attacks)")
    print("   - Wet Mix: 65% (Squashed parallel signal blended in)")
    print("   - Ratio: 10:1 (Brickwall crushing on the wet path)")
    print("   - Threshold: -24 dBFS (Catching all low-level details)")
    print("   - Makeup Gain: +14 dB (Massive body and sustain boost)\n")

    ny_comp = NewYorkCompressor(
        dry_mix=0.75,
        wet_mix=0.65,
        threshold_db=-24.0,
        ratio=10.0,
        attack_ms=1.5,
        release_ms=80.0,
        makeup_gain_db=14.0,
        sample_rate=sr
    )

    processed_audio = ny_comp.process(audio)

    # Save processed audio
    with AudioFile(str(output_path), "w", sr, processed_audio.shape[0]) as f:
        f.write(processed_audio)

    # Calculate processed stats
    rms_proc = np.sqrt(np.mean(processed_audio ** 2))
    rms_db_proc = 20 * np.log10(rms_proc + 1e-9)
    peak_db_proc = 20 * np.log10(np.max(np.abs(processed_audio)) + 1e-9)
    
    print(f"💾 [SAVE] Saved NY Compressed mix to: {output_path.name}")
    print(f"   - Final RMS Loudness:    {rms_db_proc:>6.1f} dBFS")
    print(f"   - Final Peak Level:      {peak_db_proc:>6.1f} dBFS\n")
    
    print(f"🔥 RESULT: Added {rms_db_proc - rms_db_raw:+.1f} dB of dense RMS power!")
    print("   Notice how the mix sounds incredibly 'fat' and 'in-your-face',")
    print("   but the original sharp attacks of the synths/drums remain intact.")
    print("\n🎧 Listen to the magic here:")
    print(f"   file://{output_path.absolute()}\n")

if __name__ == "__main__":
    main()
