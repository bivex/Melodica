from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode
from melodica.generators.orchestral_strings import ContrabassGenerator, CelloGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.countermelody import CountermelodyGenerator

def debug_track_01():
    print("Debugging Track 01 Velocity...")
    parts = [
        IdeaPart(name="Crypt", bars=48, scale=Scale(root=2, mode=Mode.AEOLIAN), tempo=90),
        IdeaPart(name="First Light", bars=48, scale=Scale(root=2, mode=Mode.DORIAN), tempo=95),
        IdeaPart(name="Desolate Vista", bars=32, scale=Scale(root=4, mode=Mode.AEOLIAN), tempo=85),
    ]
    
    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all", use_tension_curve=True,
        use_voice_leading=True, use_texture_control=True, use_mixing=True, target_lufs=-16.0,
        parts=parts,
        tracks=[
            TrackConfig(name="Harp Arpeggios", generator=HarpGenerator(), instrument="harp", arrangement="ABAB", density=0.7, rhythm_rests=0.8),
            TrackConfig(name="Woodwinds Motif", generator=WoodwindsEnsembleGenerator(), instrument="oboe", arrangement="AABB", density=0.5, octave_shift=1, variations=["humanize"], rhythm_rests=0.7),
            TrackConfig(name="Cello Solo", generator=CelloGenerator(), instrument="cello", arrangement="ABCD", density=0.6, variations=["humanize"], rhythm_swing=0.55),
            TrackConfig(name="Viola Counter", generator=CountermelodyGenerator(motion_preference="contrary"), instrument="viola", arrangement="ABCD", density=0.5, depends_on="Cello Solo", rhythm_rotate=0.125),
            TrackConfig(name="Tremolo Tension", generator=TremoloStringsGenerator(), instrument="strings", arrangement="AABB", density=0.8, octave_shift=1),
            TrackConfig(name="Choir Ahhs", generator=ChoirAahsGenerator(), instrument="choir", arrangement="AABB", density=0.4, rhythm_rests=0.6),
            TrackConfig(name="Contrabass Sub", generator=ContrabassGenerator(), instrument="contrabass", arrangement="AABB", density=0.8, octave_shift=-1),
        ]
    )
    
    notes_dict = IdeaTool(config).generate()
    from melodica.shorts_mastering import MasteringDesk
    desk = MasteringDesk(target_lufs=config.target_lufs)
    
    all_notes_flat = []
    for tn, notes in notes_dict.items():
        if not tn.startswith("_"):
            all_notes_flat.extend(notes)
            
    rms = desk._compute_rms(all_notes_flat)
    target = desk.target_rms_velocity
    gain = target / rms if rms > 0 else 1.0
    
    print(f"Overall RMS = {rms:.2f}")
    print(f"Target RMS  = {target}")
    print(f"Global Gain = {gain:.2f}")
    
    for tname, notes in notes_dict.items():
        if tname.startswith("_") or not isinstance(notes, list):
            continue
            
        print(f"Track: {tname}")
        # Divide track into 8 time segments and show average velocity
        total_beats = sum(p.bars * 4 for p in parts)
        seg_len = total_beats / 8
        for i in range(8):
            start = i * seg_len
            end = (i + 1) * seg_len
            seg_notes = [n for n in notes if start <= n.start < end]
            if seg_notes:
                avg_vel = sum(n.velocity for n in seg_notes) / len(seg_notes)
                print(f"  Segment {i} ({start:.0f}-{end:.0f}b): Avg Vel = {avg_vel:.1f}")
            else:
                print(f"  Segment {i} ({start:.0f}-{end:.0f}b): NO NOTES")

if __name__ == "__main__":
    debug_track_01()
