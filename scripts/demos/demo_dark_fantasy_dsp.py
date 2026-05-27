# Copyright (c) 2026 Bivex
# Standalone Demo: Epic Orchestral VST Rendering + Haas Widener + DSP Mastering

import sys
import numpy as np
from pathlib import Path
from pedalboard.io import AudioFile

from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig
from melodica.types import Scale, Mode
from melodica.vst_player import VSTPlayer
from melodica.dsp_mastering import DSPMasteringDesk
from melodica.dsp_effects import HaasWidener

def main():
    print("\n" + "="*80)
    print(" 🏰  MELODICA DARK FANTASY VST RENDERING & DSP MASTERING  🏰")
    print("="*80 + "\n")
    
    out_dir = Path("/Volumes/External/Code/Melodica/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate the composition
    print("🎼  [COMPOSER] Generating 8-bar Epic Dark Fantasy composition...")
    config = IdeaToolConfig(
        scale=Scale(root=2, mode=Mode.DORIAN),  # D Dorian
        bars=8,
        tempo=100,
        style="dark_fantasy",
        use_mixing=False,
        use_mastering=False,
        tracks=[
            TrackConfig(name="dark_bass", generator_type="bass"),
            TrackConfig(name="dark_pad", generator_type="chord"),
            TrackConfig(name="arp", generator_type="arpeggio"),
            TrackConfig(name="melody", generator_type="melody"),
        ]
    )
    
    tool = IdeaTool(config)
    tool.generate()
    tracks_data = tool.render_tracks()
    
    # 2. VST Rendering Definitions
    vst_path = "/Library/Audio/Plug-Ins/VST3/Surge XT.vst3"
    
    patches = {
        "dark_bass": "/Library/Application Support/Surge XT/patches_factory/Basses/Deep End.fxp",
        "dark_pad": "/Library/Application Support/Surge XT/patches_factory/Pads/Choir Pad Thing.fxp",
        "arp": "/Library/Application Support/Surge XT/patches_factory/Pads/Bell Pad.fxp",
        "melody": "/Library/Application Support/Surge XT/patches_factory/Pads/Subtle Comb Strings.fxp"
    }

    print("\n🎹  [VIRTUAL SYNTHS] Rendering individual tracks via Surge XT...")
    sr = 44100
    bpm = float(config.tempo)
    audio_tracks = []
    max_len = 0

    for track_name, patch_path in patches.items():
        if track_name not in tracks_data or not tracks_data[track_name].notes:
            continue
            
        print(f"  ⚡ Rendering '{track_name}' -> Patch: {Path(patch_path).stem}")
        try:
            with VSTPlayer(vst_path, sample_rate=sr, normalize=False) as player:
                player.load_preset(patch_path)
                audio = player.render_notes(tracks_data[track_name].notes, bpm=bpm)
                
                # Apply Track-Level DSP! 
                # Let's apply HaasWidener exclusively to the Choir Pad to make it gigantic!
                if track_name == "dark_pad":
                    print("     🌌 Applying Haas Stereo Widener exclusively to the Choir Pad...")
                    haas = HaasWidener(delay_ms=25.0, delay_right=True, sample_rate=sr)
                    audio = haas.process(audio)
                
                audio_tracks.append((track_name, audio))
                max_len = max(max_len, audio.shape[1])
        except Exception as e:
            print(f"❌ Failed to render {track_name}: {e}")

    if not audio_tracks:
        print("❌ No audio rendered.")
        return

    # 3. Mixing / Summing
    print("\n🎛️  [MIX BUS] Summing tracks into an epic raw mix...")
    summed_audio = np.zeros((2, max_len), dtype=np.float32)
    for name, audio in audio_tracks:
        length = audio.shape[1]
        summed_audio[:, :length] += audio

    # Protect against digital clipping
    peak_raw = np.max(np.abs(summed_audio))
    if peak_raw > 0:
        summed_audio = summed_audio / peak_raw * (10 ** (-3.0 / 20.0))

    raw_path = out_dir / "dark_fantasy_raw.wav"
    with AudioFile(str(raw_path), "w", sr, summed_audio.shape[0]) as f:
        f.write(summed_audio)
    print(f"💾  [RAW] Saved unmastered orchestral mix: {raw_path.name}")

    # 4. Cinematic DSP Mastering
    print("\n🎚️  [MASTERING DESK] Processing final mix through DSPMasteringDesk...")
    print("  - Preset: ambient_classical (Preserves orchestral dynamics, adds lush reverb)")
    print("  - Mid/Side: stereo_width=1.2 (Making the entire orchestra massive)")
    print("  - LUFS Target: -14.0 (Spotify Cinematic Standard)")
    
    desk = DSPMasteringDesk(
        style="ambient_classical",
        target_lufs=-14.0,
        sample_rate=sr,
        true_peak_ceiling=-1.0,
        stereo_width=1.2
    )

    mastered_audio = desk.process(summed_audio)
    
    mastered_path = out_dir / "dark_fantasy_mastered.wav"
    with AudioFile(str(mastered_path), "w", sr, mastered_audio.shape[0]) as f:
        f.write(mastered_audio)
        
    print(f"💾  [MASTERED] Saved Spotify-ready cinematic audio: {mastered_path.name}")
    print("\n🎉  Cinematic production pipeline complete!")
    print(f"🎧  Listen to the epic result: file://{mastered_path.absolute()}\n")

if __name__ == "__main__":
    main()
