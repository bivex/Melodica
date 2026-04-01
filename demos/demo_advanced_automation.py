"""
demo_advanced_automation.py — Ultimate control demo: Pitch Bend, Pan, Velocity, Sustain.
"""

from melodica.types import Scale, Mode
from melodica.composition import Composition, MusicDirector
from melodica.midi import export_midi
from melodica.application.automation import ExpressionCurve
from pathlib import Path

def main():
    key = Scale(root=0, mode=Mode.MAJOR) # C Major
    comp = Composition(name="Automation_Masterclass", key=key)
    
    # --- 1. Panning & Velocity Fade ---
    pan_wave = ExpressionCurve.sinusoidal(target="pan", start_val=20, end_val=110, duration=16.0, freq=0.5)
    velocity_fade = ExpressionCurve.linear(target="velocity", start_val=30, end_val=127, duration=16.0)
    
    comp.add_section(
        name="Intro_Movement",
        duration=16.0,
        progression="I IV",
        tracks={"Strings": "ambient_pad"},
        automation=[pan_wave, velocity_fade]
    )
    
    # --- 2. Pitch Bend & Sustain ---
    # Pitch bend dip (0 -> -4000 -> 0)
    # val 0-127. target 64 is center. 32 is a big dip.
    pitch_dip = ExpressionCurve.surge(target="pitch_bend", peak_val=32, duration=16.0)
    sustain_pedal = ExpressionCurve.linear(target="sustain", start_val=127, end_val=127, duration=16.0) # Always ON
    
    comp.add_section(
        name="Warped_Part",
        duration=16.0,
        progression="I V",
        tracks={"Lead": "lead_melody"},
        automation=[pitch_dip, sustain_pedal]
    )

    director = MusicDirector(key=key)
    arrangement = director.render(comp)
    
    out_file = "output/advanced_automation.mid"
    Path("output").mkdir(exist_ok=True)
    export_midi(arrangement.tracks, out_file)
    
    print(f"🚀 Advanced automation score: {out_file}")

if __name__ == "__main__":
    main()
