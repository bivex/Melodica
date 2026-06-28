# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/albums/electronic/album_roblox_brainrot.py — "Skibidi Rizz & Gyatt" Album.
Roblox Hyperpop / Chiptune / Happy Hardcore / Phonk Meme continuous listening experience.
"""

from pathlib import Path
from melodica.types import NoteInfo, Scale, Mode
from melodica.idea_tool import TrackConfig, structure_to_schedule
from melodica.composer.album_pipeline import AlbumNarrative, Mood
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator

# GM Programs mapping
PIANO = 0
CELESTA = 8
MUSIC_BOX = 10
GLOCKENSPIEL = 9
SYNTH_BASS = 38
STRINGS = 48
CHOIR = 52
SYNTH_VOICE = 54
SYNTH_LEAD = 80
DRUMS = 0


def produce_roblox_brainrot_album():
    print("================================================================================")
    print("        S K I B I D I   R I Z Z   &   G Y A T T")
    print("        Roblox Brainrot & Hyperpop Continuous Album Experience")
    print("================================================================================")

    # 1. Hyperactive meme seed motif
    seed_motif = [
        NoteInfo(pitch=60, start=0.0, duration=0.25, velocity=95),
        NoteInfo(pitch=64, start=0.25, duration=0.25, velocity=90),
        NoteInfo(pitch=67, start=0.5, duration=0.25, velocity=100),
        NoteInfo(pitch=72, start=0.75, duration=0.5, velocity=110),
    ]

    # 2. Global Narrative Journey
    # Track 1: Skibidi Toilet Rush [C Major — 142 BPM]
    # Track 2: Sigma Grindset [F# Phrygian — 130 BPM]
    # Track 3: Baby Gronk's Rizz [G Lydian — 150 BPM]
    # Track 4: Gyatt Return [C Major — 138 BPM]
    harmonic_journey = [
        Scale(root=0, mode=Mode.MAJOR),     # C Major
        Scale(root=6, mode=Mode.PHRYGIAN),   # F# Phrygian
        Scale(root=7, mode=Mode.LYDIAN),     # G Lydian
        Scale(root=0, mode=Mode.MAJOR)      # C Major
    ]
    tempos = [142.0, 130.0, 150.0, 138.0]

    # 3. Track configurations
    track_configs = [
        # Track 1: Skibidi Toilet Rush
        [
            TrackConfig(
                name="meme_pad",
                generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.35, chord_dur=4.0),
                generator_type="pad",
                instrument="synth_voice",
                density=0.45,
                phrase_schedule=structure_to_schedule("A B A B C C' R R", 4)
            ),
            TrackConfig(
                name="bass_808",
                generator=SynthBassGenerator(waveform="saw", pattern="sub_kick"),
                generator_type="bass",
                instrument="synth_bass",
                density=0.6,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("A B A B C C' R R", 4)
            ),
            TrackConfig(
                name="chiptune_arp",
                generator=ArpeggiatorGenerator(pattern="up_down", note_duration=0.25),
                generator_type="arpeggiator",
                instrument="celesta",
                density=0.4,
                octave_shift=2,
                phrase_schedule=structure_to_schedule("A B A B C C' R R", 4)
            ),
            TrackConfig(
                name="skibidi_lead_melody",
                generator=SoloMelodyGenerator(style="jazz_fusion", vibrato_depth=0.7),
                generator_type="melody",
                instrument="synth_lead",
                density=0.45,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("R B R B C C' A R", 4)
            ),
            TrackConfig(
                name="roblox_drums",
                generator=ElectronicDrumsGenerator(kit="909", pattern="techno"),
                generator_type="drums",
                instrument="drums",
                density=0.7,
                phrase_schedule=structure_to_schedule("R A A B C C' R R", 4)
            )
        ],
        # Track 2: Sigma Grindset (Phonk Version)
        [
            TrackConfig(
                name="sigma_pad",
                generator=DarkPadGenerator(mode="phrygian_pad", register="mid", velocity_level=0.3, chord_dur=8.0),
                generator_type="pad",
                instrument="strings",
                density=0.45,
                phrase_schedule=structure_to_schedule("A B A B C R R", 4)
            ),
            TrackConfig(
                name="phonk_bass",
                generator=SynthBassGenerator(waveform="saw", pattern="reese", slide_probability=0.3),
                generator_type="bass",
                instrument="synth_bass",
                density=0.65,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("A B A B C R R", 4)
            ),
            TrackConfig(
                name="cowbell_lead_solo",
                generator=SoloMelodyGenerator(style="shred_guitar", vibrato_depth=0.5),
                generator_type="melody",
                instrument="glockenspiel",
                density=0.5,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("R A B B C R R", 4)
            ),
            TrackConfig(
                name="phonk_drums",
                generator=ElectronicDrumsGenerator(kit="808", pattern="breakbeat"),
                generator_type="drums",
                instrument="drums",
                density=0.65,
                phrase_schedule=structure_to_schedule("R A A B C R R", 4)
            )
        ],
        # Track 3: Baby Gronk's Rizz
        [
            TrackConfig(
                name="rizz_pad",
                generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.32, chord_dur=4.0),
                generator_type="pad",
                instrument="synth_voice",
                density=0.45,
                phrase_schedule=structure_to_schedule("A B B C C R R R R", 4)
            ),
            TrackConfig(
                name="hyper_bass",
                generator=SynthBassGenerator(waveform="saw", pattern="acid_line"),
                generator_type="bass",
                instrument="synth_bass",
                density=0.6,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("A B B C C R R R R", 4)
            ),
            TrackConfig(
                name="laser_arp",
                generator=ArpeggiatorGenerator(pattern="up_down", note_duration=0.25),
                generator_type="arpeggiator",
                instrument="music_box",
                density=0.4,
                octave_shift=2,
                phrase_schedule=structure_to_schedule("A B B C C R R R R", 4)
            ),
            TrackConfig(
                name="rizz_lead_melody",
                generator=SoloMelodyGenerator(style="space_synth", vibrato_depth=0.65),
                generator_type="melody",
                instrument="synth_lead",
                density=0.5,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("R B R B C C A R R", 4)
            ),
            TrackConfig(
                name="hyper_drums",
                generator=ElectronicDrumsGenerator(kit="909", pattern="techno"),
                generator_type="drums",
                instrument="drums",
                density=0.7,
                phrase_schedule=structure_to_schedule("A B B C C R R R R", 4)
            )
        ],
        # Track 4: Gyatt Return
        [
            TrackConfig(
                name="outro_pad",
                generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.3, chord_dur=8.0),
                generator_type="pad",
                instrument="strings",
                density=0.4,
                phrase_schedule=structure_to_schedule("A B C R R R", 4)
            ),
            TrackConfig(
                name="outro_bass",
                generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
                generator_type="bass",
                instrument="synth_bass",
                density=0.5,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("A B C R R R", 4)
            ),
            TrackConfig(
                name="chiptune_outro_arp",
                generator=ArpeggiatorGenerator(pattern="up_down", note_duration=0.25),
                generator_type="arpeggiator",
                instrument="celesta",
                density=0.35,
                octave_shift=2,
                phrase_schedule=structure_to_schedule("A B C R R R", 4)
            ),
            TrackConfig(
                name="outro_lead_solo",
                generator=SoloMelodyGenerator(style="jazz_fusion", vibrato_depth=0.6),
                generator_type="melody",
                instrument="synth_lead",
                density=0.45,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("R B C A R R", 4)
            ),
            TrackConfig(
                name="outro_drums",
                generator=ElectronicDrumsGenerator(kit="linn", pattern="four_on_floor"),
                generator_type="drums",
                instrument="drums",
                density=0.6,
                phrase_schedule=structure_to_schedule("A B C R R R", 4)
            )
        ]
    ]

    transformations = ["original", "inversion", "stretched", "fragmented"]

    sections_list = [
        [(0.0, "Emergence"), (16.0, "Expansion"), (32.0, "Tension"), (64.0, "Release"), (96.0, "Dissolve")],
        [(0.0, "Emergence"), (16.0, "Expansion"), (32.0, "Tension"), (64.0, "Release"), (96.0, "Dissolve")],
        [(0.0, "Emergence"), (16.0, "Expansion"), (48.0, "Tension"), (80.0, "Release"), (112.0, "Dissolve")],
        [(0.0, "Emergence"), (16.0, "Release"), (48.0, "Dissolve")]
    ]

    instruments_maps = [
        {
            "meme_pad": SYNTH_VOICE,
            "bass_808": SYNTH_BASS,
            "chiptune_arp": CELESTA,
            "skibidi_lead_melody": SYNTH_LEAD,
            "roblox_drums": DRUMS
        },
        {
            "sigma_pad": STRINGS,
            "phonk_bass": SYNTH_BASS,
            "cowbell_lead_solo": GLOCKENSPIEL,
            "phonk_drums": DRUMS
        },
        {
            "rizz_pad": SYNTH_VOICE,
            "hyper_bass": SYNTH_BASS,
            "laser_arp": MUSIC_BOX,
            "rizz_lead_melody": SYNTH_LEAD,
            "hyper_drums": DRUMS
        },
        {
            "outro_pad": STRINGS,
            "outro_bass": SYNTH_BASS,
            "chiptune_outro_arp": CELESTA,
            "outro_lead_solo": SYNTH_LEAD,
            "outro_drums": DRUMS
        }
    ]

    moods = [Mood.CINEMATIC, Mood.INTIMATE, Mood.CINEMATIC, Mood.AMBIENT]
    names = ["Skibidi Toilet Rush", "Sigma Grindset", "Baby Gronk Rizz", "Gyatt Return"]

    narrative = AlbumNarrative(
        output_dir="output/album_roblox_brainrot",
        seed_motif=seed_motif,
        harmonic_journey=harmonic_journey,
        tempos=tempos,
        track_configs=track_configs,
        transformations=transformations,
        sections_list=sections_list,
        instruments_maps=instruments_maps,
        moods=moods,
        names=names,
        strict_validation=True
    )

    narrative.generate()


if __name__ == "__main__":
    produce_roblox_brainrot_album()
