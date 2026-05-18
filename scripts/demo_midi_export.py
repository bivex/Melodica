# Copyright (c) 2026 Bivex
# Standalone Demo: Generating an Epic Multi-Track GM MIDI File

import sys
from pathlib import Path

from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig
from melodica.types import Scale, Mode

def main():
    print("\n" + "="*80)
    print(" 🎹  MELODICA GENERAL MIDI (GM) EXPORT DEMO  🎹")
    print("="*80 + "\n")
    
    out_dir = Path("/Volumes/External/Code/Melodica/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate an epic 8-bar Dark Fantasy / Orchestral composition
    print("🎼  Generating 8-bar Epic Dark Fantasy composition...")
    config = IdeaToolConfig(
        scale=Scale(root=2, mode=Mode.DORIAN),  # D Dorian (Epic / Medieval)
        bars=8,
        tempo=100,
        style="dark_fantasy",  # Automatically assigns orchestral GM instruments
        
        # We define multiple tracks that will automatically get GM instruments
        tracks=[
            # String Ensemble / Contrabass
            TrackConfig(name="dark_bass", generator_type="bass"),
            # Choir / Warm Pad
            TrackConfig(name="dark_pad", generator_type="chord"),
            # Harp
            TrackConfig(name="arp", generator_type="arpeggio"),
            # Pizzicato Strings / Spiccato
            TrackConfig(name="ostinato", generator_type="ostinato"),
            # Lead Synth/Voice or Flute
            TrackConfig(name="melody", generator_type="melody"),
        ]
    )
    
    tool = IdeaTool(config)
    result_midi = tool.generate()
    
    # IdeaTool automatically writes out the composition to a generic path, 
    # but we can explicitly save it to our own target file!
    target_path = out_dir / "epic_orchestral_gm.mid"
    
    from melodica.midi import export_multitrack_midi, STYLE_INSTRUMENTS
    
    # render_tracks() gives us dict[str, TrackData], we need dict[str, list[NoteInfo]]
    tracks_data = {name: track.notes for name, track in tool.render_tracks().items() if track.notes}
    
    # We pass the instruments dictionary directly so it assigns the exact GM patches
    instruments_map = STYLE_INSTRUMENTS.get("dark_fantasy", {})
    
    export_multitrack_midi(
        tracks_data, 
        str(target_path), 
        bpm=100.0, 
        instruments=instruments_map
    )
    
    print(f"✅  Composition generated with {len(tracks_data)} instrument tracks!\n")
    
    print("🎧  The MIDI file has been saved with full General MIDI instrument mapping:")
    print("   - Track 'dark_bass': GM Patch 38 (Synth Bass 1)")
    print("   - Track 'dark_pad':  GM Patch 92 (Halo Pad)")
    print("   - Track 'arp':       GM Patch 46 (Harp)")
    print("   - Track 'ostinato':  GM Patch 45 (Pizzicato Strings)")
    print("   - Track 'melody':    GM Patch 88 (New Age Pad)")
    
    print("\n💾  Direct link to file:")
    print(f"   file://{target_path.absolute()}")
    print("\n💡  You can drop this .mid file directly into your DAW (Ableton, Logic, Reaper) ")
    print("    and it will automatically split into 5 tracks. Or just double click to play ")
    print("    it through the standard OS MIDI player!")

if __name__ == "__main__":
    main()
