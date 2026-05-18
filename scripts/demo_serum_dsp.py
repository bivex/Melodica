# Copyright (c) 2026 Bivex
# Standalone Demo for Serum VST3 + DSP Mastering

import sys
import numpy as np
from pathlib import Path
from pedalboard.io import AudioFile

from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig
from melodica.types import Scale, Mode
from melodica.vst_player import VSTPlayer
from melodica.dsp_mastering import DSPMasteringDesk

def main():
    print("\n" + "="*80)
    print(" 💉  MELODICA SERUM VST3 + DSP MASTERING DEMO  💉")
    print("="*80 + "\n")
    
    # 1. Generate an aggressive Trap/Phonk bassline
    print("🎼  [COMPOSER] Generating heavy bassline in C Minor...")
    config = IdeaToolConfig(
        scale=Scale(root=0, mode=Mode.AEOLIAN),  # C Minor
        bars=4,
        tempo=140,
        style="trap",
        use_mixing=False,
        use_mastering=False,
        tracks=[
            TrackConfig(name="bass", generator_type="bass")
        ]
    )
    
    tool = IdeaTool(config)
    tool.generate()
    tracks_data = tool.render_tracks()
    bass_notes = tracks_data["bass"].notes
    print(f"✅  Generated {len(bass_notes)} MIDI notes for the bass track.\n")

    # 2. Render through Serum 2
    serum_path = "/Library/Audio/Plug-Ins/VST3/Serum2.vst3"
    if not Path(serum_path).exists():
        print(f"❌  Error: Serum VST not found at {serum_path}")
        return
        
    print(f"🎹  [VST] Loading Serum 2 from {serum_path} ...")
    
    # Render audio
    sr = 44100
    try:
        with VSTPlayer(serum_path, plugin_name="Serum 2", sample_rate=sr, normalize=False) as player:
            print("  ⚡ Rendering MIDI through Serum...")
            audio_raw = player.render_notes(bass_notes, bpm=140.0)
    except Exception as e:
        print(f"❌  Failed to load or render Serum: {e}")
        return

    # Check if audio is empty
    if audio_raw.size == 0:
        print("❌  Error: Rendered audio is empty.")
        return

    # Protect against digital clipping before mastering
    peak_raw = np.max(np.abs(audio_raw))
    if peak_raw > 0:
        audio_raw = audio_raw / peak_raw * (10 ** (-3.0 / 20.0))

    out_dir = Path("/Volumes/External/Code/Melodica/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    raw_path = out_dir / "serum_raw.wav"
    with AudioFile(str(raw_path), "w", sr, audio_raw.shape[0]) as f:
        f.write(audio_raw)
    print(f"💾  [RAW] Saved unmastered Serum audio to: {raw_path.name}\n")

    # 3. DSP Mastering with Mid/Side processing
    print("🎚️  [MASTERING DESK] Processing through DSPMasteringDesk...")
    print("  - Preset: trap_drill (Heavy clipping, low-end preservation)")
    print("  - Mid/Side: mono_bass=True (Centering the sub-bass)")
    print("  - Mid/Side: stereo_width=1.3 (Widening the high frequencies 30%)")
    print("  - LUFS Target: -10.0 (Extremely loud & competitive)\n")

    desk = DSPMasteringDesk(
        style="trap_drill",
        target_lufs=-10.0,
        sample_rate=sr,
        true_peak_ceiling=-1.0,
        stereo_width=1.3,
        mono_bass=True
    )

    mastered_audio = desk.process(audio_raw)
    
    mastered_path = out_dir / "serum_mastered.wav"
    with AudioFile(str(mastered_path), "w", sr, mastered_audio.shape[0]) as f:
        f.write(mastered_audio)
        
    print(f"💾  [MASTERED] Saved final Serum audio to: {mastered_path.name}\n")

    # 4. Telemetry Comparison
    rms_raw = 20 * np.log10(np.sqrt(np.mean(audio_raw ** 2)) + 1e-9)
    peak_raw_db = 20 * np.log10(np.max(np.abs(audio_raw)) + 1e-9)
    
    rms_mastered = 20 * np.log10(np.sqrt(np.mean(mastered_audio ** 2)) + 1e-9)
    peak_mastered_db = 20 * np.log10(np.max(np.abs(mastered_audio)) + 1e-9)

    print("📊 [PRODUCTION COMPARISON METRICS]")
    print("=" * 80)
    print(f"{'Metric':<25} | {'Raw Serum (Unmastered)':<25} | {'Mastered (DSP Desk)':<25}")
    print("-" * 80)
    print(f"{'Integrated Loudness':<25} | {rms_raw:<22.1f} dBFS | {rms_mastered:<22.1f} dBFS")
    print(f"{'Peak Amplitude':<25} | {peak_raw_db:<22.1f} dBFS | {peak_mastered_db:<22.1f} dBFS")
    print(f"{'Stereo Field':<25} | {'Normal':<25} | {'Widened (130%) & Mono Bass':<25}")
    print("=" * 80 + "\n")
    
    print("🎉  Serum generation and DSP Mastering complete!")
    print(f"🎧  Listen to raw:      file://{raw_path.absolute()}")
    print(f"🎧  Listen to mastered: file://{mastered_path.absolute()}")

if __name__ == "__main__":
    main()
