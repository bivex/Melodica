#!/usr/bin/env python3
"""
scripts/render_melody_wav.py — Convert generated MIDI melody to WAV using FluidSynth.

Requires:
  - fluidsynth package: pip install fluidsynth
  - SoundFont file (e.g., GeneralUser GS, Timbres of Heaven)

Usage:
  python3.11 scripts/render_melody_wav.py input.mid output.wav [soundfont.sf2]
"""

import sys
import subprocess
from pathlib import Path


def check_fluidsynth():
    try:
        import fluidsynth

        return True
    except ImportError:
        return False


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python3.11 scripts/render_melody_wav.py <input.mid> <output.wav> [soundfont.sf2]"
        )
        print("\nExample:")
        print("  python3.11 scripts/render_melody_wav.py /tmp/melody_retro.mid retro.wav")
        print("\nOptional soundfont (if not provided, tries to find common ones):")
        print("  /usr/share/sounds/sf2/GeneralUser.sf2")
        print("  /usr/share/sounds/sf2/FluidR3_GM.sf2")
        print("  ./soundfonts/GeneralUser_GS.sf2")
        sys.exit(1)

    midi_path = Path(sys.argv[1])
    wav_path = Path(sys.argv[2])
    soundfont = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    if not midi_path.exists():
        print(f"❌ MIDI file not found: {midi_path}")
        sys.exit(1)

    # Auto-detect soundfont if not provided
    if soundfont is None:
        candidates = [
            Path("/usr/share/sounds/sf2/GeneralUser_GS.sf2"),
            Path("/usr/share/sounds/sf2/GeneralUser.sf2"),
            Path("/usr/share/sounds/sf2/FluidR3_GM.sf2"),
            Path("./soundfonts/GeneralUser_GS.sf2"),
            Path("./soundfonts/TimbresOfHeaven.sf2"),
        ]
        for cand in candidates:
            if cand.exists():
                soundfont = cand
                print(f"🔍 Found soundfont: {soundfont}")
                break
        if soundfont is None:
            print("⚠️  No soundfont provided or auto-detected.")
            print("   Install fluidsynth and a General MIDI SoundFont:")
            print("   - Download: https://schristiancollins.com/generaluser.php")
            print("   - Or: sudo apt install fluid-soundfont-gm")
            print("   Then pass path: python render_melody_wav.py in.mid out.wav /path/to/sf2")
            sys.exit(1)

    if not check_fluidsynth():
        print("❌ fluidsynth not installed. Install with:")
        print("   pip install fluidsynth")
        print("   Also need a SoundFont (.sf2) file")
        sys.exit(1)

    import fluidsynth

    print(f"🎵 Rendering {midi_path.name} → {wav_path.name}")
    print(f"   Using SoundFont: {soundfont.name}")

    # Create FluidSynth instance
    fs = fluidsynth.Synth()
    fs.start(driver="file", filename=str(wav_path), sample_rate=44100)

    # Load soundfont (preset 0 = bank 0, instrument 0)
    sfid = fs.sfload(str(soundfont))
    fs.program_select(0, sfid, 0, 0)  # channel 0, bank 0, program 0 (Grand Piano)

    # Actually we want lead (GM 81 = Synth Lead), not piano.
    # So we should select preset 81 (bank 0, program 81)
    fs.program_select(0, sfid, 0, 81)

    # Play MIDI file
    fs.midi_load(str(midi_path))
    fs.midi_play()

    # Wait for playback to finish
    import time

    duration = 0
    while fs.get_status():
        time.sleep(0.1)
        duration += 0.1
        if duration > 60:
            break

    fs.delete()
    print(f"✅ Rendered: {wav_path} ({duration:.1f}s)")


if __name__ == "__main__":
    main()
