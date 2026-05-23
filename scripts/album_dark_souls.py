# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_dark_souls.py — "Lord of Cinder: A Dark Fantasy Symphony"
A massive 40-minute, 7-track orchestral album generated via IdeaTool.
Showcases dynamic Tempo Maps, Scale Modulations (Aeolian, Phrygian, Locrian),
and massive multi-part suites using the `IdeaPart` hierarchical structure.
"""

from pathlib import Path

from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

# Generators
from melodica.generators.orchestral_strings import (
    ViolinGenerator,
    ViolaGenerator,
    CelloGenerator,
    ContrabassGenerator,
)
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.orchestral_brass import FrenchHornGenerator, TrumpetGenerator, TromboneGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.piano_run import PianoRunGenerator
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator


# ---------------------------------------------------------------------------
# Track Builders
# ---------------------------------------------------------------------------

def generate_track_01():
    """1. The Ashen Awakening (128 bars, ~5.5 mins) - Slow, melancholic"""
    print("  -> 1. The Ashen Awakening")
    
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
            TrackConfig(name="Harp", generator=HarpGenerator(), instrument="harp", arrangement="ABAB", density=0.5),
            TrackConfig(name="Woodwinds", generator=WoodwindsEnsembleGenerator(), instrument="oboe", arrangement="AABB", density=0.6, octave_shift=1),
            TrackConfig(name="Cello Solo", generator=CelloGenerator(), instrument="cello", arrangement="ABCD", density=0.7),
            TrackConfig(name="Choir", generator=ChoirAahsGenerator(), instrument="choir", arrangement="AABB", density=0.4),
            TrackConfig(name="Contrabass", generator=ContrabassGenerator(), instrument="contrabass", arrangement="AABB", density=0.8, octave_shift=-1),
        ]
    )
    return IdeaTool(config).generate(), parts


def generate_track_02():
    """2. Pilgrimage of the Hollows (176 bars, ~6.5 mins) - Creeping, descending scales"""
    print("  -> 2. Pilgrimage of the Hollows")
    
    parts = [
        IdeaPart(name="The Trek", bars=64, scale=Scale(root=9, mode=Mode.AEOLIAN), tempo=100),
        IdeaPart(name="Ambush", bars=64, scale=Scale(root=9, mode=Mode.PHRYGIAN), tempo=115),
        IdeaPart(name="Ruins", bars=48, scale=Scale(root=9, mode=Mode.LOCRIAN), tempo=105), # Darkest mode
    ]
    
    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all", use_tension_curve=True,
        use_voice_leading=True, use_texture_control=True, use_mixing=True, target_lufs=-14.0,
        parts=parts,
        tracks=[
            TrackConfig(name="Violins Pizzicato", generator=StringsPizzicatoGenerator(), instrument="pizzicato", arrangement="ABCD", density=0.8),
            TrackConfig(name="Low Strings", generator=StringsLegatoGenerator(), instrument="strings", arrangement="AABB", density=0.9, octave_shift=-1),
            TrackConfig(name="Trombones", generator=TromboneGenerator(), instrument="trombone", arrangement="ABAC", density=0.7, octave_shift=-1),
            TrackConfig(name="Timpani", generator=TimpaniGenerator(), instrument="timpani", arrangement="ABAB", density=0.8),
            TrackConfig(name="Choir", generator=ChoirAahsGenerator(), instrument="choir", arrangement="AABB", density=0.6),
        ]
    )
    return IdeaTool(config).generate(), parts


def generate_track_03():
    """3. Knight of the Abyss (192 bars, ~6.0 mins) - Fast, aggressive boss fight"""
    print("  -> 3. Knight of the Abyss")
    
    parts = [
        IdeaPart(name="Phase 1", bars=64, scale=Scale(root=0, mode=Mode.HARMONIC_MINOR), tempo=120),
        IdeaPart(name="Phase 2", bars=64, scale=Scale(root=2, mode=Mode.HARMONIC_MINOR), tempo=135),
        IdeaPart(name="Despair", bars=64, scale=Scale(root=4, mode=Mode.PHRYGIAN), tempo=150),
    ]
    
    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all", use_tension_curve=True,
        use_voice_leading=True, use_texture_control=True, use_mixing=True, target_lufs=-12.0,
        parts=parts,
        tracks=[
            TrackConfig(name="Ostinato Cellos", generator=OstinatoGenerator(pattern="driving"), instrument="cello", arrangement="ABAB", density=1.0, octave_shift=-1),
            TrackConfig(name="Ostinato Violas", generator=OstinatoGenerator(pattern="gallop"), instrument="viola", arrangement="ABAB", density=1.0),
            TrackConfig(name="French Horns", generator=FrenchHornGenerator(), instrument="brass", arrangement="AABC", density=0.9),
            TrackConfig(name="Trumpets", generator=TrumpetGenerator(), instrument="trumpet", arrangement="AABB", density=0.8, octave_shift=1),
            TrackConfig(name="Timpani", generator=TimpaniGenerator(), instrument="timpani", arrangement="ABCD", density=1.0),
            TrackConfig(name="Orchestral Hits", generator=OrchestralHitGenerator(hit_type="staccato"), instrument="orchestral_hit", arrangement="ABAB", density=0.5),
            TrackConfig(name="Choir Epic", generator=ChoirAahsGenerator(), instrument="choir", arrangement="ABCD", density=0.9),
        ]
    )
    return IdeaTool(config).generate(), parts


def generate_track_04():
    """4. Catacombs of Despair (144 bars, ~7.0 mins) - Slow, ambient, terrifying"""
    print("  -> 4. Catacombs of Despair")
    
    parts = [
        IdeaPart(name="Descent", bars=48, scale=Scale(root=1, mode=Mode.LOCRIAN), tempo=80),
        IdeaPart(name="The Deep", bars=48, scale=Scale(root=6, mode=Mode.PHRYGIAN), tempo=85),
        IdeaPart(name="Pitch Black", bars=48, scale=Scale(root=11, mode=Mode.LOCRIAN), tempo=75),
    ]
    
    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all", use_tension_curve=True,
        use_voice_leading=True, use_texture_control=True, use_mixing=True, target_lufs=-15.0,
        parts=parts,
        tracks=[
            TrackConfig(name="Contrabass Drone", generator=ContrabassGenerator(), instrument="contrabass", arrangement="AABB", density=0.9, octave_shift=-2),
            TrackConfig(name="Woodwinds Dissonant", generator=WoodwindsEnsembleGenerator(), instrument="bassoon", arrangement="ABCD", density=0.4, octave_shift=-1),
            TrackConfig(name="Choir Whispers", generator=ChoirAahsGenerator(), instrument="choir", arrangement="AABB", density=0.3),
            TrackConfig(name="Harp", generator=HarpGenerator(), instrument="harp", arrangement="ABAC", density=0.4),
            TrackConfig(name="Pizzicato Creep", generator=StringsPizzicatoGenerator(), instrument="pizzicato", arrangement="ABAB", density=0.5),
        ]
    )
    return IdeaTool(config).generate(), parts


def generate_track_05():
    """5. The Nameless King's Fury (224 bars, ~6.5 mins) - Epic modulation boss fight"""
    print("  -> 5. The Nameless King's Fury")
    
    parts = [
        IdeaPart(name="Storm Approaches", bars=64, scale=Scale(root=7, mode=Mode.AEOLIAN), tempo=120),
        IdeaPart(name="Dragon Rider", bars=64, scale=Scale(root=9, mode=Mode.AEOLIAN), tempo=130),
        IdeaPart(name="Lightning Strike", bars=64, scale=Scale(root=11, mode=Mode.HARMONIC_MINOR), tempo=145),
        IdeaPart(name="Fallen God", bars=32, scale=Scale(root=4, mode=Mode.AEOLIAN), tempo=100), # Sudden slow down
    ]
    
    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all", use_tension_curve=True,
        use_voice_leading=True, use_texture_control=True, use_mixing=True, target_lufs=-11.5,
        parts=parts,
        tracks=[
            TrackConfig(name="Piano Runs", generator=PianoRunGenerator(), instrument="piano", arrangement="ABCD", density=0.8, octave_shift=1),
            TrackConfig(name="Strings Legato", generator=StringsLegatoGenerator(), instrument="strings", arrangement="AABC", density=1.0, octave_shift=1),
            TrackConfig(name="French Horns", generator=FrenchHornGenerator(), instrument="brass", arrangement="AABB", density=0.9),
            TrackConfig(name="Trombones", generator=TromboneGenerator(), instrument="trombone", arrangement="AABB", density=0.9, octave_shift=-1),
            TrackConfig(name="Timpani", generator=TimpaniGenerator(), instrument="timpani", arrangement="ABCD", density=1.0),
            TrackConfig(name="Choir Epic", generator=ChoirAahsGenerator(), instrument="choir", arrangement="ABCD", density=1.0),
            TrackConfig(name="Contrabass", generator=ContrabassGenerator(), instrument="contrabass", arrangement="AABB", density=1.0, octave_shift=-2),
        ]
    )
    return IdeaTool(config).generate(), parts


def generate_track_06():
    """6. Lord of Cinder (192 bars, ~7.5 mins) - The tragic final boss. Tempo & emotion shifts."""
    print("  -> 6. Lord of Cinder")
    
    parts = [
        IdeaPart(name="The Old King", bars=32, scale=Scale(root=0, mode=Mode.AEOLIAN), tempo=85),
        IdeaPart(name="Rekindled Flame", bars=64, scale=Scale(root=2, mode=Mode.HARMONIC_MINOR), tempo=120),
        IdeaPart(name="Desperation", bars=64, scale=Scale(root=4, mode=Mode.AEOLIAN), tempo=140),
        IdeaPart(name="Fading Embers", bars=32, scale=Scale(root=9, mode=Mode.AEOLIAN), tempo=75),
    ]
    
    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all", use_tension_curve=True,
        use_voice_leading=True, use_texture_control=True, use_mixing=True, target_lufs=-12.5,
        parts=parts,
        tracks=[
            TrackConfig(name="Solo Piano", generator=PianoRunGenerator(), instrument="piano", arrangement="ABCD", density=0.7),
            TrackConfig(name="Cello Solo", generator=CelloGenerator(), instrument="cello", arrangement="ABAC", density=0.6),
            TrackConfig(name="Strings Legato", generator=StringsLegatoGenerator(), instrument="strings", arrangement="AABB", density=0.8),
            TrackConfig(name="Brass Section", generator=FrenchHornGenerator(), instrument="brass", arrangement="ABCD", density=0.7),
            TrackConfig(name="Choir Epic", generator=ChoirAahsGenerator(), instrument="choir", arrangement="ABCD", density=0.8),
            TrackConfig(name="Timpani", generator=TimpaniGenerator(), instrument="timpani", arrangement="AABB", density=0.7),
            TrackConfig(name="Contrabass", generator=ContrabassGenerator(), instrument="contrabass", arrangement="AABB", density=0.8, octave_shift=-1),
        ]
    )
    return IdeaTool(config).generate(), parts


def generate_track_07():
    """7. Age of Dark (128 bars, ~6.0 mins) - Somber, resolving, fading out"""
    print("  -> 7. Age of Dark")
    
    parts = [
        IdeaPart(name="The Choice", bars=48, scale=Scale(root=9, mode=Mode.AEOLIAN), tempo=85),
        IdeaPart(name="Fading Fire", bars=48, scale=Scale(root=4, mode=Mode.AEOLIAN), tempo=80),
        IdeaPart(name="Darkness", bars=32, scale=Scale(root=11, mode=Mode.PHRYGIAN), tempo=70),
    ]
    
    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all", use_tension_curve=True,
        use_voice_leading=True, use_texture_control=True, use_mixing=True, target_lufs=-16.0,
        parts=parts,
        tracks=[
            TrackConfig(name="Harp", generator=HarpGenerator(), instrument="harp", arrangement="AABB", density=0.4),
            TrackConfig(name="Choir Whispers", generator=ChoirAahsGenerator(), instrument="choir", arrangement="ABCD", density=0.5),
            TrackConfig(name="Violins High", generator=ViolinGenerator(), instrument="violin", arrangement="AABB", density=0.6, octave_shift=2),
            TrackConfig(name="Contrabass Drone", generator=ContrabassGenerator(), instrument="contrabass", arrangement="AABB", density=0.8, octave_shift=-2),
        ]
    )
    return IdeaTool(config).generate(), parts


# ---------------------------------------------------------------------------
# Main Builder
# ---------------------------------------------------------------------------

def main():
    album_dir = Path("output/album_dark_souls")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        L O R D   O F   C I N D E R")
    print("        A 40-Minute Dark Fantasy Symphony")
    print("=" * 80)

    tracks = [
        (generate_track_01, "01_The_Ashen_Awakening.mid"),
        (generate_track_02, "02_Pilgrimage_of_the_Hollows.mid"),
        (generate_track_03, "03_Knight_of_the_Abyss.mid"),
        (generate_track_04, "04_Catacombs_of_Despair.mid"),
        (generate_track_05, "05_The_Nameless_Kings_Fury.mid"),
        (generate_track_06, "06_Lord_of_Cinder.mid"),
        (generate_track_07, "07_Age_of_Dark.mid"),
    ]

    total_notes = 0
    time_signature = (4, 4) # Hardcoded globally for the time calculation

    with EngineTracer(show_private=False, show_duration=True, max_depth=2, use_colors=True):
        for producer, filename in tracks:
            print("-" * 80)
            notes_dict, parts_config = producer()
            
            # Construct Tempo Map for automation
            tempo_map = []
            current_beat = 0.0
            for p in parts_config:
                tempo_map.append((current_beat, p.tempo))
                current_beat += p.bars * time_signature[0]

            # Filter out non-track keys
            tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

            # Export with tempo automation!
            export_multitrack_midi(
                tracks_data,
                str(album_dir / filename),
                bpm=parts_config[0].tempo, # Base BPM
                tempo_events=tempo_map,    # Dynamic BPM automation!
            )
            
            # Count notes
            note_count = sum(len(n) for k, n in tracks_data.items())
            total_notes += note_count
            print(f"    Exported {filename}")
            print(f"      - Notes: {note_count}")
            print(f"      - Tempo Map: {', '.join(f'{bpm}bpm@{beat}b' for beat, bpm in tempo_map)}")

    print()
    print("=" * 80)
    print(f"  COMPLETE: Lord of Cinder Album — {total_notes} total notes across 7 epic tracks")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
