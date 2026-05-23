# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_symphonia.py — "Symphonia: A 7-Track Orchestral Journey"
An album generated purely using Melodica's internal IdeaTool structural engine.
Showcases AABA macro-forms, voice-leading, tension curves, and rich orchestral textures.
"""

from pathlib import Path

from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig
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
from melodica.generators.orchestral_brass import FrenchHornGenerator, TrumpetGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.piano_run import PianoRunGenerator
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator


def generate_track_01():
    print("  -> 1. The Grand Overture (C Major, 115 BPM)")
    config = IdeaToolConfig(
        scale=Scale(root=0, mode=Mode.MAJOR),
        style="cinematic",
        bars=32,
        tempo=115,
        workflow="generate_all",
        use_tension_curve=True,
        use_voice_leading=True,
        use_texture_control=True,
        use_mixing=True,
        target_lufs=-14.0,
        tracks=[
            TrackConfig(name="Violins Legato", generator=StringsLegatoGenerator(), instrument="strings", arrangement="AABA", density=0.8, octave_shift=1),
            TrackConfig(name="Trumpet Melody", generator=TrumpetGenerator(), instrument="trumpet", arrangement="AABA", density=0.6, octave_shift=1),
            TrackConfig(name="French Horns", generator=FrenchHornGenerator(), instrument="brass", arrangement="AABB", density=0.7),
            TrackConfig(name="Violas Ostinato", generator=OstinatoGenerator(pattern="rhythmic"), instrument="viola", arrangement="ABAB", density=1.0),
            TrackConfig(name="Cellos", generator=CelloGenerator(), instrument="cello", arrangement="AABB", density=0.8),
            TrackConfig(name="Contrabass", generator=ContrabassGenerator(), instrument="contrabass", arrangement="AABB", density=0.9, octave_shift=-1),
            TrackConfig(name="Timpani", generator=TimpaniGenerator(), instrument="timpani", arrangement="ABCD", density=0.6),
        ]
    )
    return IdeaTool(config).generate(), 115.0


def generate_track_02():
    print("  -> 2. Shadows of the Forest (D Minor, 85 BPM)")
    config = IdeaToolConfig(
        scale=Scale(root=2, mode=Mode.AEOLIAN),
        style="cinematic",
        bars=24,
        tempo=85,
        workflow="generate_all",
        use_tension_curve=True,
        use_voice_leading=True,
        use_mixing=True,
        target_lufs=-16.0, # Quieter track
        tracks=[
            TrackConfig(name="Woodwinds", generator=WoodwindsEnsembleGenerator(), instrument="oboe", arrangement="ABAC", density=0.5, octave_shift=1),
            TrackConfig(name="Choir", generator=ChoirAahsGenerator(), instrument="choir", arrangement="AABB", density=0.8),
            TrackConfig(name="Harp", generator=HarpGenerator(), instrument="harp", arrangement="ABAB", density=0.9),
            TrackConfig(name="Cellos", generator=CelloGenerator(), instrument="cello", arrangement="AABB", density=0.6, octave_shift=-1),
        ]
    )
    return IdeaTool(config).generate(), 85.0


def generate_track_03():
    print("  -> 3. The Royal Waltz (G Major, 130 BPM)")
    config = IdeaToolConfig(
        scale=Scale(root=7, mode=Mode.MAJOR),
        style="cinematic",
        bars=32,
        time_signature=(3, 4),
        tempo=130,
        workflow="generate_all",
        use_tension_curve=True,
        use_voice_leading=True,
        use_mixing=True,
        target_lufs=-14.0,
        tracks=[
            TrackConfig(name="Violins Melody", generator=ViolinGenerator(), instrument="violin", arrangement="AABA", density=0.7, octave_shift=1),
            TrackConfig(name="Pizzicato Strings", generator=StringsPizzicatoGenerator(), instrument="pizzicato", arrangement="AABB", density=1.0),
            TrackConfig(name="Violas", generator=ViolaGenerator(), instrument="viola", arrangement="AABB", density=0.8),
            TrackConfig(name="Contrabass", generator=ContrabassGenerator(), instrument="contrabass", arrangement="AABB", density=0.8, octave_shift=-1),
        ]
    )
    return IdeaTool(config).generate(), 130.0


def generate_track_04():
    print("  -> 4. Battle Preparations (E Minor, 140 BPM)")
    config = IdeaToolConfig(
        scale=Scale(root=4, mode=Mode.AEOLIAN),
        style="cinematic",
        bars=40,
        tempo=140,
        workflow="generate_all",
        use_tension_curve=True,
        use_voice_leading=True,
        use_mixing=True,
        target_lufs=-12.0, # Loud, aggressive track
        tracks=[
            TrackConfig(name="Staccato Violas", generator=OstinatoGenerator(pattern="gallop"), instrument="viola", arrangement="ABAB", density=1.0),
            TrackConfig(name="Staccato Cellos", generator=OstinatoGenerator(pattern="driving"), instrument="cello", arrangement="ABAB", density=1.0, octave_shift=-1),
            TrackConfig(name="French Horns", generator=FrenchHornGenerator(), instrument="brass", arrangement="AABB", density=0.8),
            TrackConfig(name="Timpani", generator=TimpaniGenerator(), instrument="timpani", arrangement="AABB", density=0.9),
            TrackConfig(name="Orchestral Hits", generator=OrchestralHitGenerator(), instrument="orchestral_hit", arrangement="AABA", density=0.4),
        ]
    )
    return IdeaTool(config).generate(), 140.0


def generate_track_05():
    print("  -> 5. The Queen's Lament (F# Minor, 75 BPM)")
    config = IdeaToolConfig(
        scale=Scale(root=6, mode=Mode.AEOLIAN),
        style="cinematic",
        bars=24,
        tempo=75,
        workflow="generate_all",
        use_tension_curve=True,
        use_voice_leading=True,
        use_mixing=True,
        target_lufs=-16.0,
        tracks=[
            TrackConfig(name="Cello Solo", generator=CelloGenerator(), instrument="cello", arrangement="ABAC", density=0.6),
            TrackConfig(name="Choir", generator=ChoirAahsGenerator(), instrument="choir", arrangement="AABB", density=0.8),
            TrackConfig(name="Violins Legato", generator=StringsLegatoGenerator(), instrument="strings", arrangement="AABB", density=0.7, octave_shift=1),
            TrackConfig(name="Harp", generator=HarpGenerator(), instrument="harp", arrangement="ABAB", density=0.5),
        ]
    )
    return IdeaTool(config).generate(), 75.0


def generate_track_06():
    print("  -> 6. March of the Knights (Bb Major, 110 BPM)")
    config = IdeaToolConfig(
        scale=Scale(root=10, mode=Mode.MAJOR),
        style="cinematic",
        bars=32,
        tempo=110,
        workflow="generate_all",
        use_tension_curve=True,
        use_voice_leading=True,
        use_mixing=True,
        target_lufs=-13.0,
        tracks=[
            TrackConfig(name="Trumpet Melody", generator=TrumpetGenerator(), instrument="trumpet", arrangement="AABA", density=0.8, octave_shift=1),
            TrackConfig(name="Trombone Chords", generator=FrenchHornGenerator(), instrument="brass", arrangement="AABB", density=0.9),
            TrackConfig(name="Pizzicato Strings", generator=StringsPizzicatoGenerator(), instrument="pizzicato", arrangement="AABB", density=0.8),
            TrackConfig(name="Timpani", generator=TimpaniGenerator(), instrument="timpani", arrangement="ABAB", density=0.8),
        ]
    )
    return IdeaTool(config).generate(), 110.0


def generate_track_07():
    print("  -> 7. Finale - The Ascent (C Minor -> Epic, 125 BPM)")
    config = IdeaToolConfig(
        scale=Scale(root=0, mode=Mode.HARMONIC_MINOR),
        style="cinematic",
        bars=48,
        tempo=125,
        workflow="generate_all",
        use_tension_curve=True,
        use_voice_leading=True,
        use_texture_control=True,
        use_mixing=True,
        target_lufs=-12.0,
        tracks=[
            TrackConfig(name="Violins Legato", generator=StringsLegatoGenerator(), instrument="strings", arrangement="ABCD", density=0.9, octave_shift=1),
            TrackConfig(name="Choir Epic", generator=ChoirAahsGenerator(), instrument="choir", arrangement="ABCD", density=1.0),
            TrackConfig(name="French Horns", generator=FrenchHornGenerator(), instrument="brass", arrangement="AABC", density=0.9),
            TrackConfig(name="Piano Runs", generator=PianoRunGenerator(), instrument="piano", arrangement="ABCD", density=0.4, octave_shift=1),
            TrackConfig(name="Cellos", generator=CelloGenerator(), instrument="cello", arrangement="AABB", density=0.9, octave_shift=-1),
            TrackConfig(name="Contrabass", generator=ContrabassGenerator(), instrument="contrabass", arrangement="AABB", density=0.9, octave_shift=-2),
            TrackConfig(name="Timpani", generator=TimpaniGenerator(), instrument="timpani", arrangement="ABAB", density=0.8),
        ]
    )
    return IdeaTool(config).generate(), 125.0


def main():
    album_dir = Path("output/album_symphonia_idea")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        S Y M P H O N I A")
    print("        A 7-Track Orchestral IdeaTool Album")
    print("=" * 80)

    tracks = [
        (generate_track_01, "01_The_Grand_Overture.mid"),
        (generate_track_02, "02_Shadows_of_the_Forest.mid"),
        (generate_track_03, "03_The_Royal_Waltz.mid"),
        (generate_track_04, "04_Battle_Preparations.mid"),
        (generate_track_05, "05_The_Queens_Lament.mid"),
        (generate_track_06, "06_March_of_the_Knights.mid"),
        (generate_track_07, "07_Finale_The_Ascent.mid"),
    ]

    total_notes = 0

    with EngineTracer(show_private=False, show_duration=True, max_depth=2, use_colors=True):
        for producer, filename in tracks:
            print("-" * 80)
            notes_dict, bpm = producer()
            
            # Filter out non-track keys like '_chords' and '_doctor_report'
            tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

            export_multitrack_midi(
                tracks_data,
                str(album_dir / filename),
                bpm=bpm,
            )
            
            # Count notes
            note_count = sum(len(n) for k, n in notes_dict.items() if k != "_chords" and isinstance(n, list))
            total_notes += note_count
            print(f"    Exported {filename} ({note_count} notes, {bpm} BPM)")

    print()
    print("=" * 80)
    print(f"  COMPLETE: Symphonia Album — {total_notes} total notes across 7 tracks")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
