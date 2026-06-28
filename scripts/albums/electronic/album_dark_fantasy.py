# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/albums/electronic/album_dark_fantasy.py — "Obsidian Crown" Album.
Unique Gothic Orchestral / Ritual Ambient dark fantasy continuous listening experience.
"""

from pathlib import Path
from melodica.types import NoteInfo, Scale, Mode
from melodica.idea_tool import TrackConfig, structure_to_schedule
from melodica.composer.album_pipeline import AlbumNarrative, Mood
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator

# GM Programs mapping
HARPSICHORD = 6
GLOCKENSPIEL = 9
CELESTA = 8
CHURCH_ORGAN = 19
HARP = 46
TIMPANI = 47
LOW_STRINGS = 48
CHOIR = 52
VIOLIN = 40
CELLO = 42


def produce_dark_fantasy_album():
    print("================================================================================")
    print("        O B S I D I A N   C R O W N")
    print("        Gothic Orchestral & Dark Fantasy Continuous Album Experience")
    print("================================================================================")

    # 1. Tragic Gothic Motif: rising minor triad to flat sixth
    seed_motif = [
        NoteInfo(pitch=50, start=0.0, duration=1.0, velocity=80),
        NoteInfo(pitch=53, start=1.0, duration=1.0, velocity=85),
        NoteInfo(pitch=57, start=2.0, duration=2.0, velocity=90),
        NoteInfo(pitch=58, start=4.0, duration=4.0, velocity=95),
    ]

    # 2. Global Narrative Journey
    # Track 1: Crypt of the Old Kings [D Phrygian — 58 BPM]
    # Track 2: Whispers of the Witchwood [G Aeolian — 64 BPM]
    # Track 3: The Obsidian Citadel [E Locrian — 72 BPM]
    # Track 4: Ashes of the Empire [A Aeolian — 52 BPM]
    harmonic_journey = [
        Scale(root=2, mode=Mode.PHRYGIAN),  # D Phrygian
        Scale(root=7, mode=Mode.AEOLIAN),   # G Natural Minor
        Scale(root=4, mode=Mode.LOCRIAN),   # E Locrian
        Scale(root=9, mode=Mode.AEOLIAN)    # A Natural Minor
    ]
    tempos = [58.0, 64.0, 72.0, 52.0]

    # 3. Track configurations for each dramaturgical stage
    track_configs = [
        # Track 1: Crypt of the Old Kings
        [
            TrackConfig(
                name="gothic_choir",
                generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.35, chord_dur=8.0),
                generator_type="pad",
                instrument="synth_pad",
                density=0.45,
                phrase_schedule=structure_to_schedule("A B A B C C' R R", 4)
            ),
            TrackConfig(
                name="cathedral_organ",
                generator=DarkPadGenerator(mode="phrygian_pad", register="high", velocity_level=0.28, chord_dur=4.0),
                generator_type="pad",
                instrument="organ",
                density=0.4,
                phrase_schedule=structure_to_schedule("R A A B B C R R", 4)
            ),
            TrackConfig(
                name="ruins_timpani",
                generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
                generator_type="bass",
                instrument="timpani",
                density=0.5,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("R A A B B C C' R", 4)
            ),
            TrackConfig(
                name="harpsichord_arpeggio",
                generator=ArpeggiatorGenerator(pattern="up_down", note_duration=0.5),
                generator_type="arpeggiator",
                instrument="harpsichord",
                density=0.45,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("A B A B C C' R R", 4)
            ),
            TrackConfig(
                name="ancient_lead",
                generator=SoloMelodyGenerator(style="modal_ambient", vibrato_depth=0.55),
                generator_type="melody",
                instrument="celesta",
                density=0.45,
                octave_shift=2,
                phrase_schedule=structure_to_schedule("R B R B C C' A R", 4)
            )
        ],
        # Track 2: Whispers of the Witchwood
        [
            TrackConfig(
                name="witch_forest_pad",
                generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.32, chord_dur=8.0),
                generator_type="pad",
                instrument="strings",
                density=0.45,
                phrase_schedule=structure_to_schedule("A B A B C R R", 4)
            ),
            TrackConfig(
                name="ritual_timpani",
                generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
                generator_type="bass",
                instrument="timpani",
                density=0.5,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("A B A B C R R", 4)
            ),
            TrackConfig(
                name="poison_harp_arp",
                generator=ArpeggiatorGenerator(pattern="up_down", note_duration=0.25),
                generator_type="arpeggiator",
                instrument="harp",
                density=0.4,
                octave_shift=2,
                phrase_schedule=structure_to_schedule("A B A B C R R", 4)
            ),
            TrackConfig(
                name="lost_cello_solo",
                generator=SoloMelodyGenerator(style="modal_ambient", vibrato_depth=0.5),
                generator_type="melody",
                instrument="cello",
                density=0.5,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("R A B B C R R", 4)
            )
        ],
        # Track 3: The Obsidian Citadel
        [
            TrackConfig(
                name="citadel_fortress_choir",
                generator=DarkPadGenerator(mode="dim_cluster", register="mid", velocity_level=0.38, chord_dur=8.0),
                generator_type="pad",
                instrument="choir",
                density=0.5,
                phrase_schedule=structure_to_schedule("A B B C C R R R R", 4)
            ),
            TrackConfig(
                name="doomsday_organ",
                generator=DarkPadGenerator(mode="minor_pad", register="high", velocity_level=0.35, chord_dur=4.0),
                generator_type="pad",
                instrument="organ",
                density=0.45,
                phrase_schedule=structure_to_schedule("R A B B C C R R R", 4)
            ),
            TrackConfig(
                name="siege_timpani",
                generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
                generator_type="bass",
                instrument="timpani",
                density=0.6,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("A B B C C R R R R", 4)
            ),
            TrackConfig(
                name="iron_harpsichord_arp",
                generator=ArpeggiatorGenerator(pattern="up_down", note_duration=0.25),
                generator_type="arpeggiator",
                instrument="harpsichord",
                density=0.45,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("A B B C C R R R R", 4)
            ),
            TrackConfig(
                name="doomsday_bell_lead",
                generator=SoloMelodyGenerator(style="modal_ambient", vibrato_depth=0.4),
                generator_type="melody",
                instrument="glockenspiel",
                density=0.5,
                octave_shift=2,
                phrase_schedule=structure_to_schedule("R B R B C C A R R", 4)
            )
        ],
        # Track 4: Ashes of the Empire
        [
            TrackConfig(
                name="somber_strings",
                generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.3, chord_dur=8.0),
                generator_type="pad",
                instrument="strings",
                density=0.4,
                phrase_schedule=structure_to_schedule("A B C R R R", 4)
            ),
            TrackConfig(
                name="ruined_harp_arp",
                generator=ArpeggiatorGenerator(pattern="up_down", note_duration=0.5),
                generator_type="arpeggiator",
                instrument="harp",
                density=0.35,
                octave_shift=2,
                phrase_schedule=structure_to_schedule("A B C R R R", 4)
            ),
            TrackConfig(
                name="ashes_timpani",
                generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
                generator_type="bass",
                instrument="timpani",
                density=0.5,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("A B C R R R", 4)
            ),
            TrackConfig(
                name="fragile_violin_solo",
                generator=SoloMelodyGenerator(style="modal_ambient", vibrato_depth=0.6),
                generator_type="melody",
                instrument="violin",
                density=0.45,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("R B C A R R", 4)
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
            "gothic_choir": CHOIR,
            "cathedral_organ": CHURCH_ORGAN,
            "ruins_timpani": TIMPANI,
            "harpsichord_arpeggio": HARPSICHORD,
            "ancient_lead": CELESTA,
        },
        {
            "witch_forest_pad": LOW_STRINGS,
            "ritual_timpani": TIMPANI,
            "poison_harp_arp": HARP,
            "lost_cello_solo": CELLO,
        },
        {
            "citadel_fortress_choir": CHOIR,
            "doomsday_organ": CHURCH_ORGAN,
            "siege_timpani": TIMPANI,
            "iron_harpsichord_arp": HARPSICHORD,
            "doomsday_bell_lead": GLOCKENSPIEL,
        },
        {
            "somber_strings": LOW_STRINGS,
            "ruined_harp_arp": HARP,
            "ashes_timpani": TIMPANI,
            "fragile_violin_solo": VIOLIN,
        }
    ]

    moods = [Mood.CINEMATIC, Mood.INTIMATE, Mood.CINEMATIC, Mood.AMBIENT]
    names = ["Crypt of the Old Kings", "Whispers of the Witchwood", "The Obsidian Citadel", "Ashes of the Empire"]

    narrative = AlbumNarrative(
        output_dir="output/album_dark_fantasy",
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
    produce_dark_fantasy_album()
