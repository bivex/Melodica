# Copyright (c) 2026 Bivex
# Standalone Demo Runner: Showcasing IdeaTool with Auto-Mixing and Auto-Mastering

import sys
from pathlib import Path
from melodica.types import Scale, Mode
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig
from melodica.tracer import EngineTracer
from melodica.shorts_mastering import MasteringDesk

def main():
    print("\n" + "="*80)
    print(" 🎹  MELODICA ADVANCED COMPOSITION & SOUND ENGINEERING DEMO  🎹")
    print("="*80 + "\n")

    # 1. Setup high-end composition config with auto-mixing and auto-mastering enabled!
    config = IdeaToolConfig(
        scale=Scale(root=9, mode=Mode.AEOLIAN),  # A Natural Minor
        bars=8,
        tempo=125,
        style="synthwave",
        
        # 🌟 Sound Engineering & Post-Production Suite
        use_mixing=True,        # Section faders, automations, loop-boundary fades
        use_mastering=True,     # LUFS RMS normalization, multiband compression, panning, limiting
        target_lufs=-12.0,      # High-density streaming loudness target
        
        tracks=[
            TrackConfig(name="melody", generator_type="melody", instrument="synth_lead"),
            TrackConfig(name="chords", generator_type="chord", instrument="polysynth"),
            TrackConfig(name="bass", generator_type="bass", instrument="synth_bass"),
            TrackConfig(name="drums", generator_type="trap_drums", instrument="acoustic_grand"),
        ]
    )

    print("🛠️  Configured IdeaTool with Auto-Mixing & Auto-Mastering (-12.0 LUFS Target)")
    print("🎼  Scale: A Minor (Aeolian) | Tempo: 125 BPM | Duration: 8 Bars\n")

    # 2. Run generation under unified tracer
    print("🔍 [TRACER] Starting multi-track generation with performance profiling:")
    print("-" * 80)
    
    tool = IdeaTool(config)
    
    with EngineTracer(show_private=False, show_duration=True, max_depth=4, use_colors=True):
        result = tool.generate()
        
    print("-" * 80)
    print("✅ Generation & Engineering Complete!\n")

    # 3. Print Track Metadata and Stereo Panning Dashboard
    print("📊 [PRODUCTION DASHBOARD]")
    print("="*80)
    print(f"{'Track Name':<12} | {'MIDI Ch':<7} | {'GM Prog':<7} | {'Pan (CC10)':<10} | {'Notes':<6} | {'RMS Vel':<7} | {'Peak Vel':<8}")
    print("-" * 80)

    tracks = tool.render_tracks()
    
    # Calculate RMS/Peak per track from mixed/mastered result
    for name, track_cfg in tracks.items():
        notes = track_cfg.notes
        if not notes:
            continue
            
        # Calculate RMS
        sum_sq = sum(n.velocity**2 for n in notes)
        rms = (sum_sq / len(notes)) ** 0.5
        peak = max(n.velocity for n in notes)
        
        # Retrieve target panning
        pan_val = tool._pan_cc_events.get(name, [(0, 10, 64)])[0][2]
        pan_str = f"{pan_val} (Center)" if pan_val == 64 else (f"{pan_val} (Left)" if pan_val < 64 else f"{pan_val} (Right)")
        
        print(f"{name:<12} | {track_cfg.channel:<7} | {track_cfg.program:<7} | {pan_str:<10} | {len(notes):<6} | {rms:<7.1f} | {peak:<8}")
        
    print("="*80)

    # 4. Generate mastering report
    mastering_desk = MasteringDesk(target_lufs=config.target_lufs)
    report = mastering_desk.quality_report(result)
    
    print("\n🔊 [MASTERING QUALITY CONTROL REPORT]")
    print(f"  - Target LUFS Volume:     {report['target_lufs']} LUFS")
    print(f"  - Target RMS Velocity:    {report['target_rms']}")
    print(f"  - Achieved RMS Velocity:  {report['rms_velocity']:.2f}")
    print(f"  - Peak Brickwall Ceiling: {report['peak_velocity']} / 125")
    print(f"  - Clipping Notes Prevented: {report['clipping_notes']}")
    print(f"  - Total Audited Notes:    {report['total_notes']}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
