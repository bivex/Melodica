"""
demo_polished_fantasy.py — Demo of smooth transitions and expressive articulations.
"""

from melodica.types import Scale, Mode
from melodica.composition import Composition, MusicDirector
from melodica.midi import export_midi
from melodica.application.automation import ExpressionCurve
from pathlib import Path

def main():
    key_intro = Scale(root=9, mode=Mode.NATURAL_MINOR) # A Minor
    
    comp = Composition(name="Polished_Quest", key=key_intro)
    
    # 1. Atmospheric Intro with Crescendo
    # CC 1 = Modulation Wheel (Expression)
    crescendo = ExpressionCurve.linear(cc=1, start_val=30, end_val=100, duration=16.0)
    
    comp.add_section(
        name="Intro",
        duration=16.0,
        progression="Im VI",
        tracks={"Strings": "ambient_pad"},
        articulation="legato",
        automation=[crescendo]
    )
    
    # 2. Staccato Action Section
    comp.add_section(
        name="Staccato_March",
        duration=16.0,
        progression="Im V Im V",
        tracks={"Bass": "followed_bass", "Strings_Hit": "followed_chords"},
        articulation="staccato"
    )
    
    # 3. Smooth Outro
    # No modulation for now, but using the director's render logic
    comp.add_section(
        name="Outro",
        duration=16.0,
        progression="Im",
        tracks={"Final_Pad": "ambient_pad"},
        articulation="legato"
    )

    director = MusicDirector(key=key_intro)
    arrangement = director.render(comp)
    
    out_file = "output/polished_fantasy.mid"
    Path("output").mkdir(exist_ok=True)
    export_midi(arrangement.tracks, out_file)
    
    print(f"✨ Polished score generated: {out_file}")

if __name__ == "__main__":
    main()
