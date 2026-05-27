# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_hurricane.py — HURRICANE-style Pop/Hip-Hop/Rap/Guitar Album.

Album: "H U R R I C A N E"
Pop · Hip-Hop · Rap · Guitar · Hit — 136 BPM, D♭m

Formula per track:
  Intro      — guitar motif + pad atmosphere, sparse drums
  Verse      — 808 bass locks in, trap hats, vocal melody, guitar strums
  Pre-Chorus — build energy, layers stack, drums intensify
  Chorus     — full arrangement, hook hits, everything fires
  Break      — strip to basics, contrast, breathe
  Final      — bring it home, crescendo or fade

Key principles:
  - Guitar-driven hooks with hip-hop drum programming
  - 808 sub-bass as the low-end anchor
  - Pop song structure with rap rhythmic sensibility
  - Contrast between stripped verses and massive choruses
  - Vocal melody as the topline focal point
"""

from pathlib import Path

from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart,
    structure_to_schedule,
)
from melodica.fluid_r3_profile import FLUID_R3_PROGRAMS
from melodica.generators.melody import MelodyGenerator
from melodica.generators.chord_gen import ChordGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.guitar_strumming import GuitarStrummingGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.vocal_melody_auto import VocalMelodyAutoGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode, SectionRole, SectionFunction
from melodica.midi import export_multitrack_midi


def generate_track(name, parts, tracks, out_dir, bpm, scale):
    print(f"  > {name}")
    config = IdeaToolConfig(
        style="pop",
        parts=parts,
        tracks=tracks,
        scale=scale,
        use_voice_leading=True,
        run_doctor=True,
        doctor_register=True,
    )
    notes_dict = IdeaTool(config).generate()
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

    instruments_map = {t.name: FLUID_R3_PROGRAMS.get(t.instrument, 0) for t in tracks}

    safe = name.translate(str.maketrans("", "", "")).strip().replace(" ", "_")
    file_path = out_dir / f"{safe}.mid"
    export_multitrack_midi(tracks_data, str(file_path), bpm=bpm, instruments=instruments_map)
    return file_path


def main():
    print("=" * 80)
    print("  H U R R I C A N E")
    print("  8 tracks — pop / hip-hop / rap / guitar / hit (136 BPM)")
    print("=" * 80)

    out_dir = Path("output/album_hurricane")
    out_dir.mkdir(exist_ok=True, parents=True)

    bpm = 136
    # D♭m = Db minor (pitch class 1)
    scale = Scale(1, Mode.NATURAL_MINOR)

    # ──────────────────────────────────────────────────────────────────────
    # TRACK TEMPLATES
    # ──────────────────────────────────────────────────────────────────────

    # Guitar — the main hook instrument
    guitar_track = TrackConfig(
        name="Guitar",
        generator_type="guitar_strumming",
        instrument="electric_guitar",
        density=0.6,
        params={"strum_pattern": "pop", "velocity_humanize": 12},
    )

    # 808 Bass — the low-end anchor
    bass_808_track = TrackConfig(
        name="808 Bass",
        generator_type="bass_808_sliding",
        instrument="synth_bass",
        density=0.5,
        octave_shift=-1,
        params={"slide_curve": "exponential", "decay": 0.7},
    )

    # Trap Drums — hi-hat rolls, 808 kicks
    drums_track = TrackConfig(
        name="Drums",
        generator_type="trap_drums",
        instrument="piano",  # GM drum map
        density=0.5,
        params={"variant": "standard", "hat_roll_density": 0.4},
    )

    # Vocal Melody — topline
    vocal_track = TrackConfig(
        name="Vocal",
        generator_type="vocal_melody_auto",
        instrument="synth_voice",
        density=0.4,
    )

    # Pad — atmosphere and harmonic bed
    pad_track = TrackConfig(
        name="Pad",
        generator_type="dark_pad",
        instrument="pad",
        density=0.3,
    )

    # Chord stabs — rhythmic harmonic hits
    chords_track = TrackConfig(
        name="Chords",
        generator_type="chord",
        instrument="electric_piano",
        density=0.4,
    )

    # Counter — countermelody riding on top
    counter_track = TrackConfig(
        name="Counter",
        generator_type="countermelody",
        instrument="synth_lead",
        density=0.35,
        depends_on="Vocal",
        depends_on_param="primary_melody",
    )

    # Arpeggio — subtle rhythmic motion
    arp_track = TrackConfig(
        name="Arp",
        generator_type="arpeggiator",
        instrument="electric_piano",
        density=0.3,
        params={"direction": "up", "rate": 0.25},
    )

    # ──────────────────────────────────────────────────────────────────────
    # ARRANGEMENT: Intro → Verse → Pre-Chorus → Chorus → Break → Final
    # ──────────────────────────────────────────────────────────────────────

    def make_parts(
        intro_bars=8, verse_bars=16, prechorus_bars=8,
        chorus_bars=16, break_bars=8, final_bars=8,
    ):
        return [
            IdeaPart(
                "Intro", bars=intro_bars,
                section_type=SectionRole.INTRO,
                section_function=SectionFunction.SUSTAIN,
                track_mute=["Drums", "808 Bass", "Counter"],
                track_density={"Guitar": 0.3, "Vocal": 0.0, "Pad": 0.5, "Chords": 0.2, "Arp": 0.15},
            ),
            IdeaPart(
                "Verse", bars=verse_bars,
                section_type=SectionRole.VERSE,
                section_function=SectionFunction.SUSTAIN,
                track_density={"Guitar": 0.5, "Vocal": 0.4, "Drums": 0.6, "808 Bass": 0.5, "Pad": 0.25, "Chords": 0.3, "Arp": 0.2},
            ),
            IdeaPart(
                "Pre-Chorus", bars=prechorus_bars,
                section_type=SectionRole.PRE_CHORUS,
                section_function=SectionFunction.BUILD,
                track_density={"Guitar": 0.65, "Vocal": 0.5, "Drums": 0.75, "808 Bass": 0.6, "Pad": 0.35, "Chords": 0.45, "Counter": 0.3, "Arp": 0.3},
            ),
            IdeaPart(
                "Chorus", bars=chorus_bars,
                section_type=SectionRole.CHORUS,
                section_function=SectionFunction.RELEASE,
                track_density={"Guitar": 0.85, "Vocal": 0.7, "Drums": 0.9, "808 Bass": 0.8, "Pad": 0.45, "Chords": 0.6, "Counter": 0.5, "Arp": 0.4},
            ),
            IdeaPart(
                "Break", bars=break_bars,
                section_type=SectionRole.BREAKDOWN,
                section_function=SectionFunction.BREAK,
                track_mute=["Drums", "808 Bass", "Counter"],
                track_density={"Guitar": 0.3, "Vocal": 0.2, "Pad": 0.5, "Chords": 0.2, "Arp": 0.15},
            ),
            IdeaPart(
                "Final", bars=final_bars,
                section_type=SectionRole.CODA,
                section_function=SectionFunction.FADE,
                track_density={"Guitar": 0.4, "Vocal": 0.3, "Drums": 0.5, "808 Bass": 0.4, "Pad": 0.4, "Chords": 0.3, "Arp": 0.2},
            ),
        ]

    # ──────────────────────────────────────────────────────────────────────
    # TRACKS
    # ──────────────────────────────────────────────────────────────────────

    all_tracks = [guitar_track, bass_808_track, drums_track, vocal_track,
                  pad_track, chords_track, counter_track, arp_track]

    # ──────────────────────────────────────────────────────────────────────
    # 8 TRACKS — each with a different character
    # ──────────────────────────────────────────────────────────────────────

    tracks_def = [
        # 1. EYE OF THE STORM — classic guitar-driven pop/rap
        ("EYE OF THE STORM", make_parts(), all_tracks),

        # 2. LANDSLIDE — heavier 808s, more trap influence
        ("LANDSLIDE", make_parts(verse_bars=16, chorus_bars=16), [
            guitar_track, bass_808_track,
            TrackConfig(name="Drums", generator_type="trap_drums", instrument="piano", density=0.6,
                        params={"variant": "drill", "hat_roll_density": 0.55}),
            vocal_track, pad_track, chords_track, counter_track, arp_track,
        ]),

        # 3. DOWNPOUR — melodic rap, vocal-forward
        ("DOWNPOUR", make_parts(verse_bars=16, prechorus_bars=8, chorus_bars=16), [
            guitar_track, bass_808_track, drums_track,
            TrackConfig(name="Vocal", generator_type="vocal_melody_auto", instrument="synth_voice", density=0.55),
            pad_track,
            TrackConfig(name="Chords", generator_type="chord", instrument="electric_piano", density=0.5),
            counter_track, arp_track,
        ]),

        # 4. GUST — minimal, spacious, guitar + 808 only
        ("GUST", make_parts(intro_bars=8, verse_bars=16, prechorus_bars=4, chorus_bars=12, break_bars=8, final_bars=8), [
            guitar_track, bass_808_track,
            TrackConfig(name="Drums", generator_type="trap_drums", instrument="piano", density=0.4,
                        params={"variant": "minimal", "hat_roll_density": 0.2}),
            vocal_track, pad_track,
        ]),

        # 5. CROSSWIND — aggressive, high-energy
        ("CROSSWIND", make_parts(intro_bars=4, verse_bars=16, prechorus_bars=8, chorus_bars=16, break_bars=4, final_bars=8), [
            guitar_track,
            TrackConfig(name="808 Bass", generator_type="bass_808_sliding", instrument="synth_bass", density=0.65, octave_shift=-1,
                        params={"slide_curve": "exponential"}),
            TrackConfig(name="Drums", generator_type="trap_drums", instrument="piano", density=0.7,
                        params={"variant": "standard", "hat_roll_density": 0.6, "kick_pattern": "syncopated"}),
            vocal_track, pad_track, chords_track, counter_track, arp_track,
        ]),

        # 6. FLOOD — dark, atmospheric, guitar arpeggios
        ("FLOOD", make_parts(verse_bars=16, chorus_bars=16, break_bars=12), [
            TrackConfig(name="Guitar", generator_type="guitar_strumming", instrument="electric_guitar", density=0.45,
                        params={"strum_pattern": "ballad"}),
            bass_808_track,
            TrackConfig(name="Drums", generator_type="trap_drums", instrument="piano", density=0.45,
                        params={"variant": "melodic", "hat_roll_density": 0.35}),
            vocal_track,
            TrackConfig(name="Pad", generator_type="dark_pad", instrument="dark_pad", density=0.45),
            chords_track, counter_track, arp_track,
        ]),

        # 7. SUPERCELL — maximal, everything at full
        ("SUPERCELL", make_parts(intro_bars=4, verse_bars=12, prechorus_bars=8, chorus_bars=16, break_bars=4, final_bars=12), [
            guitar_track,
            TrackConfig(name="808 Bass", generator_type="bass_808_sliding", instrument="synth_bass", density=0.7, octave_shift=-1),
            TrackConfig(name="Drums", generator_type="trap_drums", instrument="piano", density=0.75,
                        params={"variant": "standard", "hat_roll_density": 0.65, "kick_pattern": "syncopated"}),
            TrackConfig(name="Vocal", generator_type="vocal_melody_auto", instrument="synth_voice", density=0.6),
            pad_track,
            TrackConfig(name="Chords", generator_type="chord", instrument="electric_piano", density=0.55),
            counter_track, arp_track,
        ]),

        # 8. AFTERMATH — emotional closer, guitar-led
        ("AFTERMATH", make_parts(intro_bars=12, verse_bars=16, prechorus_bars=8, chorus_bars=16, break_bars=12, final_bars=16), [
            TrackConfig(name="Guitar", generator_type="guitar_strumming", instrument="electric_guitar", density=0.5,
                        params={"strum_pattern": "pop", "velocity_humanize": 15}),
            bass_808_track,
            TrackConfig(name="Drums", generator_type="trap_drums", instrument="piano", density=0.4,
                        params={"variant": "minimal", "hat_roll_density": 0.25}),
            TrackConfig(name="Vocal", generator_type="vocal_melody_auto", instrument="synth_voice", density=0.45),
            TrackConfig(name="Pad", generator_type="dark_pad", instrument="pad", density=0.5),
            chords_track,
            TrackConfig(name="Counter", generator_type="countermelody", instrument="synth_lead", density=0.4, depends_on="Vocal"),
            arp_track,
        ]),
    ]

    # ──────────────────────────────────────────────────────────────────────
    # GENERATE
    # ──────────────────────────────────────────────────────────────────────

    for name, parts, tracks in tracks_def:
        generate_track(name, parts, tracks, out_dir, bpm, scale)

    print()
    print("=" * 80)
    print("  H U R R I C A N E   C O M P L E T E")
    print(f"  Output: {out_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
