import cProfile
import pstats
import io
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig
from melodica.types import Scale, Mode

def profile_engine():
    print("Generating a dense 32-bar composition to profile the engine...")
    config = IdeaToolConfig(
        scale=Scale(root=0, mode=Mode.AEOLIAN),
        style="cinematic",
        bars=32,
        tempo=120,
        workflow="generate_all",
        use_tension_curve=True,
        use_voice_leading=True,
        use_texture_control=True,
        use_harmonic_verifier=True,
        run_doctor=True, # enable psychoacoustic and harmonic checks
        tracks=[
            TrackConfig(name="Melody", generator_type="melody", arrangement="ABCD", density=0.8),
            TrackConfig(name="Counter", generator_type="melody", arrangement="ABCD", density=0.8),
            TrackConfig(name="Arp", generator_type="arpeggiator", arrangement="ABCD", density=1.0),
            TrackConfig(name="Chord", generator_type="chord", arrangement="AABB", density=1.0),
            TrackConfig(name="Bass", generator_type="bass", arrangement="AABB", density=0.8),
        ]
    )
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    IdeaTool(config).generate()
    
    profiler.disable()
    
    s = io.StringIO()
    # Sort by cumulative time
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumtime')
    ps.print_stats(30)
    
    with open("output/profile_report.txt", "w") as f:
        f.write(s.getvalue())
        
    print(s.getvalue())

if __name__ == "__main__":
    profile_engine()
