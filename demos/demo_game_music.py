# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
demo_game_music.py — High-level music scripting demo for game music (Intro/Main/Outro).
"""

from melodica.types import Scale, Mode
from melodica.composition import Composition, MusicDirector
from melodica.midi import export_midi
from pathlib import Path

def main():
    # 1. Setup the key (e.g., A Minor for mystical vibes)
    key = Scale(root=9, mode=Mode.NATURAL_MINOR)
    
    # 2. Architect the song like a story
    composition = Composition(name="Shadow_Forest_Loop", key=key)
    
    # --- Part 1: Intro (4 bars) ---
    # Minimalist: just a pad and a light arp to set the mood
    composition.add_section(
        name="Intro",
        duration=16.0, # 4 bars at 4/4
        progression="Im Im7 Im",
        tracks={
            "Background": "ambient_pad",
            "Magic": "fast_arp"
        }
    )
    
    # --- Part 2: Main Exploration (8 bars) ---
    # Full arrangement: Lead melody + Harmony + Bass
    composition.add_section(
        name="Main_Exploration",
        duration=32.0, 
        progression="Im VI III VII Im IVm VII Im",
        tracks={
            "Flute_Lead": "lead_melody",
            "Strings_Section": "followed_chords",
            "Low_Cello": "followed_bass",
            "Pads": "ambient_pad"
        }
    )
    
    # --- Part 3: Danger Peak (4 bars) ---
    # More tension, chromaticism, or faster hits
    composition.add_section(
        name="Danger",
        duration=16.0,
        progression="Im bII Im VIIb",
        tracks={
            "Tense_Lead": "lead_melody",
            "Bass_Hit": "followed_bass"
        }
    )
    
    # --- Part 4: Outro (4 bars) ---
    # Fading away to silence
    composition.add_section(
        name="Outro",
        duration=16.0,
        progression="Im VII VI V",
        tracks={
            "Fading_Pads": "ambient_pad"
        }
    )

    # 3. Direct the music (Render into Arrangement)
    director = MusicDirector(key=key)
    arrangement = director.render(composition)
    
    # 4. Save to MIDI
    out_file = "output/game_music_score.mid"
    Path("output").mkdir(exist_ok=True)
    export_midi(arrangement.tracks, out_file)
    
    print(f"✨ Game score generated: {out_file}")
    print(f"Total Sections: {len(composition.sections)}")
    print(f"Total Duration: {arrangement.total_beats} beats")

if __name__ == "__main__":
    main()
