# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/albums/electronic/album_coupled_hmm_great_melody.py — "Melodic HMM Journey" Album.

A continuous listening experience showcasing the power of the Coupled HMM Harmonizer
combined with expressive melodic themes (the Motif Memory Engine).
"""

from pathlib import Path
from melodica.types import NoteInfo, Scale, Mode
from melodica.idea_tool import TrackConfig, structure_to_schedule
from melodica.composer.album_pipeline import AlbumNarrative, Mood
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.breakbeat import BreakbeatGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator, VibraphoneGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator

# GM Programs mapping
PIANO = 0
SYNTH_BASS = 38
DARK_PAD = 88
SYNTH_LEAD = 80
POLYSYNTH = 90
EFFECTS = 96
DRUMS = 0
GLOCKENSPIEL = 9
VIBRAPHONE = 11
HARP = 46


def produce_melodic_hmm_album():
    print("================================================================================")
    print("        M E L O D I C   H M M   J O U R N E Y")
    print("        AI-Directed Long-Form Melodic & Ambient Listening Experience")
    print("================================================================================")

    # 1. Seed Motif: A beautiful, emotional rising and cascading melody
    seed_motif = [
        NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=85),   # C4
        NoteInfo(pitch=62, start=1.0, duration=0.5, velocity=85),   # D4
        NoteInfo(pitch=63, start=1.5, duration=0.5, velocity=85),   # Eb4
        NoteInfo(pitch=67, start=2.0, duration=1.5, velocity=90),   # G4
        NoteInfo(pitch=65, start=3.5, duration=0.5, velocity=90),   # F4
        NoteInfo(pitch=67, start=4.0, duration=1.5, velocity=95),   # G4
        NoteInfo(pitch=70, start=5.5, duration=0.5, velocity=95),   # Bb4
        NoteInfo(pitch=72, start=6.0, duration=2.0, velocity=100),  # C5
    ]

    # 2. Harmonic Journey — all four roots are distinct so each movement
    # lives in its own tonal centre (no two tracks share a key).
    harmonic_journey = [
        Scale(root=0, mode=Mode.AEOLIAN),   # Track 1: C minor
        Scale(root=7, mode=Mode.DORIAN),    # Track 2: G Dorian
        Scale(root=5, mode=Mode.PHRYGIAN),  # Track 3: F Phrygian
        Scale(root=2, mode=Mode.AEOLIAN),   # Track 4: D minor Return
    ]

    # Tempos are spread apart so each movement has a distinct pulse.
    tempos = [80.0, 92.0, 66.0, 84.0]

    # 3. Track Configurations
    track_configs = [
        # Track 1: Emerging Waves (C Aeolian) — 4-bar phrases, classic ABAB arc
        [
            TrackConfig(
                name="ambient_pad",
                generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.30, chord_dur=8.0),
                generator_type="pad",
                instrument="synth_pad",
                density=0.45,
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
                name="glockenspiel",
                generator=GlockenspielGenerator(params=None),
                instrument="glockenspiel",
                density=0.4,
                octave_shift=2,
                phrase_schedule=structure_to_schedule("A B R B C C' R R", 4)
            ),
            TrackConfig(
                name="lead_synth",
                generator=SoloMelodyGenerator(style="modal_ambient", vibrato_depth=0.45),
                instrument="synth_lead",
                density=0.6,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("R B R B C C' A R", 4)
            ),
            TrackConfig(
                name="breakbeat_drum",
                generator=BreakbeatGenerator(variant="funky", chop_probability=0.1, ghost_notes=True),
                instrument="drums",
                density=0.65,
                phrase_schedule=structure_to_schedule("R R A B C C' R R", 4)
            )
        ],
        # Track 2: Oceanic Whispers (G Dorian) — 8-bar phrases, slow ABA climax arc
        [
            TrackConfig(
                name="vintage_strings",
                generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.32, chord_dur=4.0),
                generator_type="pad",
                instrument="synth_pad",
                density=0.4,
                phrase_schedule=structure_to_schedule("A B A C R", 8)
            ),
            TrackConfig(
                name="reese_bass",
                generator=SynthBassGenerator(waveform="saw", pattern="reese", slide_probability=0.25),
                instrument="synth_bass",
                density=0.65,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("R B A C R", 8)
            ),
            TrackConfig(
                name="arpeggio_synth",
                generator=ArpeggiatorGenerator(pattern="up_down", note_duration=0.25),
                instrument="piano",
                density=0.45,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("A R A C R", 8)
            ),
            TrackConfig(
                name="lead_synth",
                generator=SoloMelodyGenerator(style="space_synth", vibrato_depth=0.5),
                instrument="synth_lead",
                density=0.6,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("R A B C R", 8)
            ),
            TrackConfig(
                name="swung_groove_drum",
                generator=BreakbeatGenerator(variant="think", chop_probability=0.12, ghost_notes=True),
                instrument="drums",
                density=0.7,
                phrase_schedule=structure_to_schedule("R R B C C", 8)
            )
        ],
        # Track 3: Tidal Reflections (F Phrygian) — 2-bar phrases, asymmetric ABABC drift
        [
            TrackConfig(
                name="space_pad",
                generator=DarkPadGenerator(mode="phrygian_pad", register="low", velocity_level=0.35, chord_dur=8.0),
                generator_type="pad",
                instrument="synth_pad",
                density=0.4,
                phrase_schedule=structure_to_schedule("A B A B C R A B", 2)
            ),
            TrackConfig(
                name="sub_bass",
                generator=SynthBassGenerator(waveform="sine", pattern="sub_kick"),
                instrument="synth_bass",
                density=0.55,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("R A A B C R A B", 2)
            ),
            TrackConfig(
                name="harp_arpeggio",
                generator=HarpGenerator(pattern="cascade"),
                instrument="harp",
                density=0.45,
                phrase_schedule=structure_to_schedule("A B R B C R A R", 2)
            ),
            TrackConfig(
                name="cinematic_lead",
                generator=SoloMelodyGenerator(style="cinematic_strings", vibrato_depth=0.6),
                instrument="synth_lead",
                density=0.55,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("R B A B C A B R", 2)
            ),
            TrackConfig(
                name="breakbeat_drum",
                generator=BreakbeatGenerator(variant="think", chop_probability=0.08, ghost_notes=True),
                instrument="drums",
                density=0.65,
                phrase_schedule=structure_to_schedule("R R A B C R R B", 2)
            )
        ],
        # Track 4: Return to the Depths (D Aeolian) — distinct palette from T1:
        # warm supersaw pad, wobble bass, vibraphone color, neo-soul lead, lofi
        # drums. Sparse 8-bar A A' A'' reprise with 3-bar phrase segments.
        [
            TrackConfig(
                name="warm_pad",
                generator=DarkPadGenerator(mode="minor_pad", register="mid", velocity_level=0.26, chord_dur=4.0),
                generator_type="pad",
                instrument="synth_pad",
                density=0.40,
                phrase_schedule=structure_to_schedule("A A' A'' R", 3)
            ),
            TrackConfig(
                name="wobble_bass",
                generator=SynthBassGenerator(waveform="square", pattern="wobble"),
                instrument="synth_bass",
                density=0.50,
                octave_shift=-1,
                phrase_schedule=structure_to_schedule("R A A' R", 3)
            ),
            TrackConfig(
                name="vibraphone",
                generator=VibraphoneGenerator(params=None),
                instrument="vibraphone",
                density=0.35,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("A R A'' R", 3)
            ),
            TrackConfig(
                name="neo_soul_lead",
                generator=SoloMelodyGenerator(style="neo_soul_keys", vibrato_depth=0.35),
                instrument="synth_lead",
                density=0.55,
                octave_shift=1,
                phrase_schedule=structure_to_schedule("R A' A R", 3)
            ),
            TrackConfig(
                name="lofi_drum",
                generator=ElectronicDrumsGenerator(kit="lofi"),
                instrument="drums",
                density=0.50,
                phrase_schedule=structure_to_schedule("R R A' R", 3)
            )
        ]
    ]

    # Each movement weaves the seed motif in a different transformation so the
    # thematic core is recognisable yet sounds different on every track.
    transformations = ["original", "inversion", "retrograde", "fragmented"]

    # Each movement has a DIFFERENT length (so the .mid files differ in size)
    # and a different section-name arc (so each gets its own energy/reverb/
    # density curve via SECTION_PROFILES). max_beat differs per track on
    # purpose → AlbumNarrative derives total_beats from it. Arcs are built from
    # register-balanced profiles (each carries BASS + LEAD) so strict validation
    # keeps LOW/HIGH coverage within target.
    sections_list = [
        # T1 Emerging Waves — ~112 beats: classic rise + release + dissolve
        [(0.0, "Emergence"), (16.0, "Expansion"), (32.0, "Tension"), (64.0, "Release"), (96.0, "Dissolve")],
        # T2 Oceanic Whispers — ~144 beats: slow burn via Variation→Climax
        [(0.0, "Emergence"), (24.0, "Expansion"), (56.0, "Variation"), (96.0, "Climax"), (128.0, "Dissolve")],
        # T3 Tidal Reflections — ~136 beats: Variation→Tension→Climax, asymmetric bars
        [(0.0, "Emergence"), (24.0, "Variation"), (56.0, "Tension"), (88.0, "Climax"), (120.0, "Dissolve")],
        # T4 Return to the Depths — ~70 beats: short reprise. Balanced profiles
        # (Emergence/Expansion/Variation/Dissolve) keep BASS+LEAD active so the
        # LOW/HIGH register coverage passes strict validation; D Aeolian centres
        # this movement away from T1's C Aeolian.
        [(0.0, "Emergence"), (12.0, "Expansion"), (30.0, "Variation"), (54.0, "Dissolve")],
    ]

    instruments_maps = [
        {
            "ambient_pad": POLYSYNTH,
            "sub_bass": SYNTH_BASS,
            "glockenspiel": GLOCKENSPIEL,
            "lead_synth": SYNTH_LEAD,
            "breakbeat_drum": DRUMS
        },
        {
            "vintage_strings": POLYSYNTH,
            "reese_bass": SYNTH_BASS,
            "arpeggio_synth": PIANO,
            "lead_synth": SYNTH_LEAD,
            "swung_groove_drum": DRUMS
        },
        {
            "space_pad": POLYSYNTH,
            "sub_bass": SYNTH_BASS,
            "harp_arpeggio": HARP,
            "cinematic_lead": SYNTH_LEAD,
            "breakbeat_drum": DRUMS
        },
        {
            "warm_pad": POLYSYNTH,
            "wobble_bass": SYNTH_BASS,
            "vibraphone": VIBRAPHONE,
            "neo_soul_lead": SYNTH_LEAD,
            "lofi_drum": DRUMS
        }
    ]

    moods = [Mood.INTIMATE, Mood.CINEMATIC, Mood.INTIMATE, Mood.AMBIENT]
    names = ["Emerging Waves", "Oceanic Whispers", "Tidal Reflections", "Return to the Depths"]

    narrative = AlbumNarrative(
        output_dir="output/album_coupled_hmm_great_melody",
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
    produce_melodic_hmm_album()
