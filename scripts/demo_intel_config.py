# Copyright (c) 2026 Bivex
# Demo: Controlling "The Brain" via MelodicIntelligenceConfig

from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams, MelodicIntelligenceConfig, MelodyGenerator
from melodica.midi import export_multitrack_midi

def generate_comparison():
    output_dir = Path("output/intel_demo")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR) # D Minor
    chords = [key.parse_roman("i"), key.parse_roman("VI"), key.parse_roman("iv"), key.parse_roman("V")] * 2
    for i, c in enumerate(chords):
        c.start = i * 4
        c.duration = 4
    
    duration = 32.0
    
    # --- 1. MECHANICAL VERSION (Robotic) ---
    # Disable all intelligence to show "raw" output
    intel_robotic = MelodicIntelligenceConfig(
        enable_interval_weights=False,
        enable_leading_tone_resolution=False,
        enable_rhythmic_phrasing=False,
        enable_micro_groove=False,
        tonal_gravity_strength=0.0
    )
    params_robotic = GeneratorParams(density=0.6, complexity=0.5, intel=intel_robotic)
    gen_robotic = MelodyGenerator(params_robotic)
    notes_robotic = gen_robotic.render(chords, key, duration)
    
    export_multitrack_midi({"robotic": notes_robotic}, str(output_dir / "01_Mechanical_Robot.mid"), bpm=120)
    
    # --- 2. VIRTUOSO VERSION (Intelligent) ---
    # Enable and tune intelligence for "Massive/Pro" feel
    intel_pro = MelodicIntelligenceConfig(
        enable_interval_weights=True,
        enable_leading_tone_resolution=True,
        tonal_gravity_strength=1.0,      # Strong pull to tonic/fifth
        chord_tone_bias=1.0,             # Solid harmonic foundation
        enable_rhythmic_phrasing=True,   # Accelerando/Ritardando
        enable_micro_groove=True,        # Human feel
        tension_subdivision_boost=0.8,   # Triplets during drama
        time_humanization=0.02,          # Slight "loose" feel
        velocity_humanization=0.2        # Dynamic expression
    )
    params_pro = GeneratorParams(density=0.6, complexity=0.7, intel=intel_pro)
    # We can also add drama to see tension-aware subdivisions
    gen_pro = MelodyGenerator(params_pro, drama_shape="crescendo", drama_peak=0.9)
    notes_pro = gen_pro.render(chords, key, duration)
    
    export_multitrack_midi({"virtuoso": notes_pro}, str(output_dir / "02_Virtuoso_Massive.mid"), bpm=120)

    print(f"\n   Demo generated: {output_dir}")
    print("   Compare 01_Mechanical_Robot (flat/dry) vs 02_Virtuoso_Massive (musical/alive)\n")

if __name__ == "__main__":
    generate_comparison()
