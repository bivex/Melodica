# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/albums/electronic/album_soft_machines_continuous.py — "Soft Machines" Album.
Organic long-form continuous listening experience with motif memory engine,
relative harmonic continuum, and dynamic entropy.
"""

from pathlib import Path
from melodica.types import NoteInfo, Scale, Mode
from melodica.idea_tool import TrackConfig, structure_to_schedule
from melodica.composer.album_pipeline import AlbumNarrative, Mood
from melodica.generators.lofi_hiphop import LoFiHipHopGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.breakbeat import BreakbeatGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator

# GM Programs mapping
PIANO = 0
RHODES = 4
SYNTH_BASS = 38
DARK_PAD = 88
SYNTH_LEAD = 80
POLYSYNTH = 90
EFFECTS = 96
DRUMS = 0
HARP = 46


def produce_soft_machines_continuous():
    print("================================================================================")
    print("        S O F T   M A C H I N E S   ( C O N T I N U U M )")
    print("        AI-Directed Long-Form Ambient & Electronic listening experience")
    print("================================================================================")

    # 1. Motif Memory Engine: Define seed motif (A C E G relative pitches)
    seed_motif = [
        NoteInfo(pitch=69, start=0.0, duration=1.0, velocity=85),
        NoteInfo(pitch=72, start=1.0, duration=1.0, velocity=85),
        NoteInfo(pitch=76, start=2.0, duration=2.0, velocity=90),
        NoteInfo(pitch=79, start=4.0, duration=4.0, velocity=95),
    ]

    # 2. Harmonic Journey: relative modal transition path
    harmonic_journey = [
        Scale(root=9, mode=Mode.AEOLIAN),   # Track 1: A minor (Velvet Circuit)
        Scale(root=2, mode=Mode.DORIAN),    # Track 2: D Dorian (Static Bloom)
        Scale(root=4, mode=Mode.PHRYGIAN),  # Track 3: E Phrygian (Memory Foam)
        Scale(root=9, mode=Mode.AEOLIAN),   # Track 4: A minor Return (Velvet Return)
    ]

    tempos = [78.0, 84.0, 72.0, 76.0]

    # 3. Track Configurations
    track_configs = [
        # Track 1: Velvet Circuit
        [
            TrackConfig(
                name="rhodes_texture",
                generator=LoFiHipHopGenerator(include_drums=False, include_bass=False),
                instrument="rhodes",
                density=0.55,
                phrase_schedule=structure_to_schedule("A B A B C C' R R", 4)
            ),
            TrackConfig(
                name="sub_bass",
                generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
                instrument="synth_bass",
                density=0.6,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("R A A B C C' R R", 4)
            ),
            TrackConfig(
                name="analog_wash",
                generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.30, chord_dur=8.0),
                generator_type="pad",
                instrument="synth_pad",
                density=0.45,
                phrase_schedule=structure_to_schedule("A B A B C C' R R", 4)
            ),
            TrackConfig(
                name="tape_lead",
                generator=SoloMelodyGenerator(style="modal_ambient", vibrato_depth=0.4),
                instrument="synth_lead",
                density=0.55,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("R B R B C C' A R", 4)
            ),
            TrackConfig(
                name="electronic_drums",
                generator=ElectronicDrumsGenerator(kit="lofi"),
                instrument="drums",
                density=0.65,
                phrase_schedule=structure_to_schedule("R R A B C C' R R", 4)
            )
        ],
        # Track 2: Static Bloom
        [
            TrackConfig(
                name="analog_plucks",
                generator=ArpeggiatorGenerator(pattern="up_down", note_duration=0.25),
                instrument="piano",
                density=0.4,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("A B A B C R R", 4)
            ),
            TrackConfig(
                name="reese_bass",
                generator=SynthBassGenerator(waveform="saw", pattern="reese", slide_probability=0.20),
                instrument="synth_bass",
                density=0.65,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("A B A B C R R", 4)
            ),
            TrackConfig(
                name="vintage_strings",
                generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.32, chord_dur=4.0),
                generator_type="pad",
                instrument="synth_pad",
                density=0.4,
                phrase_schedule=structure_to_schedule("A B A B C R R", 4)
            ),
            TrackConfig(
                name="harp_notes",
                generator=HarpGenerator(pattern="cascade"),
                instrument="harp",
                density=0.45,
                phrase_schedule=structure_to_schedule("A R A B C R R", 4)
            ),
            TrackConfig(
                name="swung_groove",
                generator=BreakbeatGenerator(variant="funky", chop_probability=0.08, ghost_notes=True),
                instrument="drums",
                density=0.7,
                phrase_schedule=structure_to_schedule("R A A B C R R", 4)
            )
        ],
        # Track 3: Memory Foam
        [
            TrackConfig(
                name="ambient_pad",
                generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.35, chord_dur=8.0),
                generator_type="pad",
                instrument="synth_pad",
                density=0.45,
                phrase_schedule=structure_to_schedule("A B B C C R R R R", 4)
            ),
            TrackConfig(
                name="rhodes_chords",
                generator=LoFiHipHopGenerator(include_drums=False, include_bass=False),
                instrument="rhodes",
                density=0.55,
                phrase_schedule=structure_to_schedule("A A B B C C R R R", 4)
            ),
            TrackConfig(
                name="sub_bass",
                generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
                instrument="synth_bass",
                density=0.6,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("R A A B B C C R R", 4)
            ),
            TrackConfig(
                name="nostalgic_lead",
                generator=SoloMelodyGenerator(style="modal_ambient", vibrato_depth=0.55),
                instrument="synth_lead",
                density=0.6,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("R B R B C C A R R", 4)
            ),
            TrackConfig(
                name="fx_riser",
                generator=FXRiserGenerator(length_beats=16.0),
                instrument="effects",
                density=0.3,
                phrase_schedule=structure_to_schedule("R R A R B R C R R", 4)
            ),
            TrackConfig(
                name="fx_impact",
                generator=FXImpactGenerator(),
                instrument="effects",
                density=0.3,
                phrase_schedule=structure_to_schedule("R R R A R B R C R", 4)
            )
        ],
        # Track 4: Velvet Return
        [
            TrackConfig(
                name="rhodes_texture",
                generator=LoFiHipHopGenerator(include_drums=False, include_bass=False),
                instrument="rhodes",
                density=0.45,
                phrase_schedule=structure_to_schedule("A B C R R R", 4)
            ),
            TrackConfig(
                name="sub_bass",
                generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
                instrument="synth_bass",
                density=0.5,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("R A C R R R", 4)
            ),
            TrackConfig(
                name="analog_wash",
                generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.28, chord_dur=8.0),
                generator_type="pad",
                instrument="synth_pad",
                density=0.4,
                phrase_schedule=structure_to_schedule("A B C R R R", 4)
            ),
            TrackConfig(
                name="tape_lead",
                generator=SoloMelodyGenerator(style="modal_ambient", vibrato_depth=0.35),
                instrument="synth_lead",
                density=0.5,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("R B C A R R", 4)
            ),
            TrackConfig(
                name="electronic_drums",
                generator=ElectronicDrumsGenerator(kit="lofi"),
                instrument="drums",
                density=0.5,
                phrase_schedule=structure_to_schedule("R R C R R R", 4)
            )
        ]
    ]

    # Motif transformations matching narrative evolution
    transformations = ["original", "inversion", "stretched", "fragmented"]

    # 4. Dramaturgical Arc Sections
    sections_list = [
        # Track 1
        [(0.0, "Emergence"), (16.0, "Expansion"), (32.0, "Tension"), (64.0, "Release"), (96.0, "Dissolve")],
        # Track 2
        [(0.0, "Emergence"), (16.0, "Expansion"), (32.0, "Tension"), (64.0, "Release"), (96.0, "Dissolve")],
        # Track 3
        [(0.0, "Emergence"), (16.0, "Expansion"), (48.0, "Tension"), (80.0, "Release"), (112.0, "Dissolve")],
        # Track 4
        [(0.0, "Emergence"), (16.0, "Release"), (48.0, "Dissolve")]
    ]

    instruments_maps = [
        # Track 1
        {
            "rhodes_texture": RHODES,
            "sub_bass": SYNTH_BASS,
            "analog_wash": POLYSYNTH,
            "tape_lead": SYNTH_LEAD,
            "electronic_drums": DRUMS
        },
        # Track 2
        {
            "analog_plucks": PIANO,
            "reese_bass": SYNTH_BASS,
            "vintage_strings": POLYSYNTH,
            "harp_notes": HARP,
            "swung_groove": DRUMS
        },
        # Track 3
        {
            "ambient_pad": POLYSYNTH,
            "rhodes_chords": RHODES,
            "sub_bass": SYNTH_BASS,
            "nostalgic_lead": SYNTH_LEAD,
            "fx_riser": EFFECTS,
            "fx_impact": EFFECTS
        },
        # Track 4
        {
            "rhodes_texture": RHODES,
            "sub_bass": SYNTH_BASS,
            "analog_wash": POLYSYNTH,
            "tape_lead": SYNTH_LEAD,
            "electronic_drums": DRUMS
        }
    ]

    moods = [Mood.INTIMATE, Mood.CINEMATIC, Mood.INTIMATE, Mood.AMBIENT]
    names = ["Velvet Circuit", "Static Bloom", "Memory Foam", "Velvet Return"]

    narrative = AlbumNarrative(
        output_dir="output/album_soft_machines_continuous",
        seed_motif=seed_motif,
        harmonic_journey=harmonic_journey,
        tempos=tempos,
        track_configs=track_configs,
        transformations=transformations,
        sections_list=sections_list,
        instruments_maps=instruments_maps,
        moods=moods,
        names=names,
        rhythm="straight_quarters",
        time_signature=(4, 4),
        strict_validation=True
    )

    narrative.generate()


if __name__ == "__main__":
    produce_soft_machines_continuous()
