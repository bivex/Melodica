import os
from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS, structure_to_schedule
from melodica.generators import (
    StringsEnsembleGenerator, AmbientPadGenerator, BassGenerator, 
    ArpeggiatorGenerator, FluteGenerator
)
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.sfx_percussion import SFXPercussionGenerator
from melodica.modifiers import (
    ModifierPipeline, ModifierContext, HumanizeModifier,
    VelocityCurveModifier, MetricAccentModifier
)
from melodica.types import Scale, Mode, MusicTimeline
from melodica.midi import export_multitrack_midi

def generate_symphonic_piece(name: str, key_root: int, tempo_base: int, filename: str):
    out_dir = Path("output/symphonic_album")
    out_dir.mkdir(exist_ok=True, parents=True)
    
    scale = Scale(key_root, Mode.NATURAL_MINOR)

    # Differentiate arrangement by "Symphony Profile"
    if "Awakening" in name:
        tracks = [
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(section_size="small", articulation="legato"), instrument="strings", density=0.4, octave_shift=1),
            TrackConfig(name="Choir", generator=ChoirAahsGenerator(voice_count=2), instrument="choir_aahs", density=0.5, octave_shift=0),
            TrackConfig(name="Bass", generator=AmbientPadGenerator(voicing="root"), instrument="contrabass", density=0.3, octave_shift=-1),
        ]
        parts = [
            IdeaPart("Intro", 8, scale, tempo_base, progression_type="coupled_hmm", track_phrase_schedules={"Strings": structure_to_schedule("R", 8), "Choir": structure_to_schedule("A", 8), "Bass": structure_to_schedule("A", 8)}),
            IdeaPart("Develop", 16, scale, tempo_base+2, progression_type="coupled_hmm", track_phrase_schedules={"Strings": structure_to_schedule("B", 16), "Choir": structure_to_schedule("C", 16), "Bass": structure_to_schedule("B", 16)}),
            IdeaPart("Outro", 8, scale, tempo_base-2, progression_type="coupled_hmm", track_phrase_schedules={"Strings": structure_to_schedule("R", 8), "Choir": structure_to_schedule("A", 8), "Bass": structure_to_schedule("A", 8)}),
        ]
    elif "Storm" in name:
        tracks = [
            TrackConfig(name="Perc", generator=SFXPercussionGenerator(instrument="taiko_drum"), instrument="taiko_drum", density=0.8, octave_shift=0),
            TrackConfig(name="Arp", generator=ArpeggiatorGenerator(pattern="up_down"), instrument="string_ensemble_2", density=0.9, octave_shift=0),
            TrackConfig(name="Bass", generator=BassGenerator(style="root_fifth"), instrument="contrabass", density=0.7, octave_shift=-2),
        ]
        parts = [
            IdeaPart("Intro", 4, scale, tempo_base, progression_type="coupled_hmm", track_phrase_schedules={"Perc": structure_to_schedule("A", 4), "Arp": structure_to_schedule("R", 4), "Bass": structure_to_schedule("A", 4)}),
            IdeaPart("Climax", 16, scale, tempo_base+10, progression_type="coupled_hmm", track_phrase_schedules={"Perc": structure_to_schedule("C", 16), "Arp": structure_to_schedule("C", 16), "Bass": structure_to_schedule("C", 16)}),
            IdeaPart("Outro", 4, scale, tempo_base, progression_type="coupled_hmm", track_phrase_schedules={"Perc": structure_to_schedule("R", 4), "Arp": structure_to_schedule("R", 4), "Bass": structure_to_schedule("A", 4)}),
        ]
    else: # Empire (Full)
        tracks = [
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(section_size="full"), instrument="strings", density=0.9, octave_shift=1),
            TrackConfig(name="Choir", generator=ChoirAahsGenerator(voice_count=4), instrument="choir_aahs", density=0.8, octave_shift=0),
            TrackConfig(name="Perc", generator=SFXPercussionGenerator(instrument="taiko_drum"), instrument="taiko_drum", density=0.6, octave_shift=0),
            TrackConfig(name="Bass", generator=BassGenerator(style="root_only"), instrument="contrabass", density=0.5, octave_shift=-2),
        ]
        parts = [
            IdeaPart("Intro", 8, scale, tempo_base, progression_type="coupled_hmm", track_phrase_schedules={"Perc": structure_to_schedule("A", 8), "Strings": structure_to_schedule("R", 8), "Choir": structure_to_schedule("R", 8), "Bass": structure_to_schedule("A", 8)}),
            IdeaPart("Build", 8, scale, tempo_base+5, progression_type="coupled_hmm", track_phrase_schedules={"Perc": structure_to_schedule("B", 8), "Strings": structure_to_schedule("B", 8), "Choir": structure_to_schedule("A", 8), "Bass": structure_to_schedule("B", 8)}),
            IdeaPart("Climax", 16, scale, tempo_base+10, progression_type="coupled_hmm", track_phrase_schedules={"Perc": structure_to_schedule("C", 16), "Strings": structure_to_schedule("C", 16), "Choir": structure_to_schedule("C", 16), "Bass": structure_to_schedule("C", 16)}),
            IdeaPart("Outro", 8, scale, tempo_base-5, progression_type="coupled_hmm", track_phrase_schedules={"Perc": structure_to_schedule("R", 8), "Strings": structure_to_schedule("R", 8), "Choir": structure_to_schedule("A", 8), "Bass": structure_to_schedule("A", 8)}),
        ]

    config = IdeaToolConfig(style="cinematic_hybrid", parts=parts, tracks=tracks, use_tension_curve=True)
    notes_dict = IdeaTool(config).generate()
    
    # Post-processing
    total_bars = sum(p.bars for p in parts if p.bars is not None)
    timeline = notes_dict.get("_timeline", MusicTimeline(chords=[], keys=[]))
    mod_context = ModifierContext(duration_beats=total_bars * 4, chords=timeline.chords, timeline=timeline, scale=scale)

    for tname in tracks:
        if tname.name in notes_dict:
            p = ModifierPipeline(base_notes=notes_dict[tname.name])
            p.add_modifier(HumanizeModifier(timing_std=0.02, velocity_std=6.0))
            if tname.generator_type != "percussion" and tname.name != "Sub_Bass":
                p.add_modifier(VelocityCurveModifier(start_vel=50, end_vel=100, curve="swell"))
            notes_dict[tname.name] = p.process(mod_context)

    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
    instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks}
    export_multitrack_midi(tracks_data, str(out_dir / filename), bpm=tempo_base, instruments=instruments_map)
    print(f"  > Generated: {filename}")

def main():
    pieces = [
        ("Symphony No.1: The Awakening", 2, 80, "01_Awakening.mid"),
        ("Symphony No.2: Storm Rising", 5, 95, "02_Storm.mid"),
        ("Symphony No.3: Fallen Empire", 10, 75, "03_Empire.mid"),
    ]
    for name, root, bpm, fname in pieces:
        print(f"Generating {name}...")
        generate_symphonic_piece(name, root, bpm, fname)

if __name__ == "__main__":
    main()
