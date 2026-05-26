# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_witch_house.py — Witch House Album Generator.

Album: "✝✝✝ R I T U A L ✝✝✝"
A descent into the void — from whispered sigils to the final summoning.

Tracks:
 1. ▲ S I G I L S ▲          — Dark pad + plucked arpeggios, drawing the circle
 2. V O I D   W A L K        — 808 sub-bass + witch house drums, entering the dark
 3. C H O P P E D   G O D S  — Pitched-down vocals + glitch percussion
 4. H E X   O N   Y O U      — Aggressive occult bass + distorted leads
 5. S L O W E D   S P I R I T S — Drag tempo + ethereal pads, communion
 6. ▼ D E S C E N T ▼        — Industrial drone + minimal beats, going deeper
 7. B L O O D   M O O N      — Full witch house ritual, peak intensity
 8. S P E C T R A L           — Ghostly arpeggios + silence, spirits speak
 9. S U M M O N I N G         — Building occult crescendo
10. ✝ R I T U A L ✝          — Full reprise, the circle closes

Powered by WitchHouseGenerator, DarkPad, DarkBass, and 10 dark scales.
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
from melodica.generators.drone import DroneGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.witch_house import WitchHouseGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi


def generate_track(name, parts, tracks, out_dir, bpm):
    print(f"  > {name}")
    config = IdeaToolConfig(
        style="cinematic",
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
        run_doctor=True,
        doctor_register=True,
    )
    notes_dict = IdeaTool(config).generate()
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

    instruments_map = {t.name: FLUID_R3_PROGRAMS.get(t.instrument, 0) for t in tracks}

    file_path = out_dir / f"{name.replace(' ', '_').replace('▲', '').replace('▼', '').replace('✝', '').strip()}.mid"
    export_multitrack_midi(tracks_data, str(file_path), bpm=bpm, instruments=instruments_map)
    return file_path


def main():
    print("=" * 80)
    print("  ✝✝✝ R I T U A L ✝✝✝")
    print("  10 tracks — witch house album")
    print("=" * 80)

    out_dir = Path("output/album_witch_house")
    out_dir.mkdir(exist_ok=True, parents=True)

    # Dark scales for witch house
    scales = {
        "sigils":      Scale(9, Mode.PHRYGIAN),           # A Phrygian — dark, exotic
        "void":        Scale(0, Mode.LOCRIAN),             # C Locrian — unstable, sinister
        "chopped":     Scale(2, Mode.HARMONIC_MINOR),      # D harmonic minor — occult
        "hex":         Scale(4, Mode.PHRYGIAN),            # E Phrygian — aggressive
        "slowed":      Scale(7, Mode.NATURAL_MINOR),       # G natural minor — melancholy
        "descent":     Scale(0, Mode.DOUBLE_HARMONIC),     # C double harmonic — middle eastern
        "blood":       Scale(9, Mode.HARMONIC_MINOR),      # A harmonic minor — ritual
        "spectral":    Scale(5, Mode.LOCRIAN),             # F Locrian — ghostly
        "summoning":   Scale(2, Mode.PHRYGIAN),            # D Phrygian — building tension
        "ritual":      Scale(9, Mode.HUNGARIAN_MINOR),     # A Hungarian minor — climax
    }

    # ------------------------------------------------------------------
    # Track 1: ▲ S I G I L S ▲ — Dark pad + plucked arpeggios
    # ------------------------------------------------------------------
    generate_track("1 SIGILS",
        parts=[IdeaPart(
            name="Drawing", bars=16, scale=scales["sigils"], tempo=70,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Pad":      structure_to_schedule("A", 16),
                "Pluck":    structure_to_schedule("R A R A:var", 4),
                "Arp":      structure_to_schedule("R R A A", 4),
                "Bass":     structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="minor_pad"),
                instrument="dark_pad", density=0.4, octave_shift=-1),
            TrackConfig(name="Pluck", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="pluck", density=0.3, octave_shift=1),
            TrackConfig(name="Arp", generator=ArpeggiatorGenerator(pattern="up",
                rhythm=get_rhythm("straight_8ths")), instrument="bright_piano", density=0.4, octave_shift=1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="doom"),
                instrument="synth_bass", density=0.3, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=70)

    # ------------------------------------------------------------------
    # Track 2: V O I D   W A L K — 808 sub-bass + witch house drums
    # ------------------------------------------------------------------
    generate_track("2 VOID WALK",
        parts=[IdeaPart(
            name="Entering", bars=16, scale=scales["void"], tempo=65,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Drums":    structure_to_schedule("A B", 8),
                "808":      structure_to_schedule("A", 16),
                "Pad":      structure_to_schedule("A", 16),
                "Lead":     structure_to_schedule("R A R B", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="classic"),
                instrument="percussion", density=0.5, octave_shift=-1),
            TrackConfig(name="808", generator=DarkBassGenerator(mode="dark_pulse"),
                instrument="synth_bass", density=0.4, octave_shift=-2),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="tritone_drone"),
                instrument="dark_pad", density=0.3, octave_shift=-1),
            TrackConfig(name="Lead", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("half_note")), instrument="sawtooth", density=0.3),
        ],
        out_dir=out_dir, bpm=65)

    # ------------------------------------------------------------------
    # Track 3: C H O P P E D   G O D S — Pitched-down + glitch
    # ------------------------------------------------------------------
    generate_track("3 CHOPPED GODS",
        parts=[
            IdeaPart("Phase1_Chop", 12, scales["chopped"], 60,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Vocal":    structure_to_schedule("A B", 6),
                    "Glitch":   structure_to_schedule("A B A:var", 4),
                    "Sub":      structure_to_schedule("A", 12),
                    "Pad":      structure_to_schedule("A", 12),
                }),
            IdeaPart("Phase2_Break", 8, scales["chopped"], 60,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Vocal":    structure_to_schedule("C D", 4),
                    "Glitch":   structure_to_schedule("C D", 4),
                    "Sub":      structure_to_schedule("C", 8),
                    "Pad":      structure_to_schedule("C", 8),
                }),
        ],
        tracks=[
            TrackConfig(name="Vocal", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="choir", density=0.4, octave_shift=-1),
            TrackConfig(name="Glitch", generator=WitchHouseGenerator(variant="drag"),
                instrument="percussion", density=0.5),
            TrackConfig(name="Sub", generator=DarkBassGenerator(mode="dub"),
                instrument="synth_bass", density=0.3, octave_shift=-2),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="chromatic_pad"),
                instrument="dark_pad", density=0.4, octave_shift=-1),
        ],
        out_dir=out_dir, bpm=60)

    # ------------------------------------------------------------------
    # Track 4: H E X   O N   Y O U — Aggressive occult bass
    # ------------------------------------------------------------------
    generate_track("4 HEX ON YOU",
        parts=[
            IdeaPart("Phase1_Curse", 12, scales["hex"], 75,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Bass":     structure_to_schedule("A B", 6),
                    "Lead":     structure_to_schedule("R A R B", 3),
                    "Drums":    structure_to_schedule("A B", 6),
                    "Pad":      structure_to_schedule("A", 12),
                }),
            IdeaPart("Phase2_Hex", 8, scales["hex"], 80,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Bass":     structure_to_schedule("C D", 4),
                    "Lead":     structure_to_schedule("C D", 4),
                    "Drums":    structure_to_schedule("C D", 4),
                    "Pad":      structure_to_schedule("C", 8),
                }),
        ],
        tracks=[
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="industrial"),
                instrument="synth_bass", density=0.6, octave_shift=-2),
            TrackConfig(name="Lead", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("straight_8ths")), instrument="sawtooth", density=0.5),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="occult"),
                instrument="percussion", density=0.6, octave_shift=-1),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="dim_cluster"),
                instrument="dark_pad", density=0.3, octave_shift=-1),
        ],
        out_dir=out_dir, bpm=75)

    # ------------------------------------------------------------------
    # Track 5: S L O W E D   S P I R I T S — Drag tempo + ethereal
    # ------------------------------------------------------------------
    generate_track("5 SLOWED SPIRITS",
        parts=[IdeaPart(
            name="Communion", bars=20, scale=scales["slowed"], tempo=50,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Pad":      structure_to_schedule("A", 20),
                "Ethereal": structure_to_schedule("R A R A:var R B", 4),
                "Choir":    structure_to_schedule("R R A B", 5),
                "Sub":      structure_to_schedule("A", 20),
            },
        )],
        tracks=[
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="phrygian_pad"),
                instrument="dark_pad", density=0.4, octave_shift=-1),
            TrackConfig(name="Ethereal", generator=AmbientPadGenerator(),
                instrument="pad", density=0.3, octave_shift=1),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="spread",
                rhythm=get_rhythm("whole_note")), instrument="choir", density=0.3, octave_shift=1),
            TrackConfig(name="Sub", generator=DarkBassGenerator(mode="doom"),
                instrument="synth_bass", density=0.2, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=50)

    # ------------------------------------------------------------------
    # Track 6: ▼ D E S C E N T ▼ — Industrial drone + minimal beats
    # ------------------------------------------------------------------
    generate_track("6 DESCENT",
        parts=[IdeaPart(
            name="GoingDeeper", bars=16, scale=scales["descent"], tempo=55,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Drone":    structure_to_schedule("A", 16),
                "Perc":     structure_to_schedule("R A R A:var", 4),
                "Hit":      structure_to_schedule("R R R A", 4),
                "Bass":     structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Drone", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.5, octave_shift=-2),
            TrackConfig(name="Perc", generator=WitchHouseGenerator(variant="dark_ambient"),
                instrument="percussion", density=0.3, octave_shift=-1),
            TrackConfig(name="Hit", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="orchestral_hit", density=0.2, octave_shift=-1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="dub"),
                instrument="synth_bass", density=0.3, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=55)

    # ------------------------------------------------------------------
    # Track 7: B L O O D   M O O N — Full witch house ritual
    # ------------------------------------------------------------------
    generate_track("7 BLOOD MOON",
        parts=[
            IdeaPart("Phase1_Ritual", 12, scales["blood"], 70,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Witch":    structure_to_schedule("A B", 6),
                    "Bass":     structure_to_schedule("A B", 6),
                    "Drums":    structure_to_schedule("A B", 6),
                    "Pad":      structure_to_schedule("A", 12),
                    "Choir":    structure_to_schedule("R A", 6),
                }),
            IdeaPart("Phase2_Eclipse", 8, scales["blood"], 80,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Witch":    structure_to_schedule("C D", 4),
                    "Bass":     structure_to_schedule("C D", 4),
                    "Drums":    structure_to_schedule("C D", 4),
                    "Pad":      structure_to_schedule("C", 8),
                    "Choir":    structure_to_schedule("C", 8),
                }),
        ],
        tracks=[
            TrackConfig(name="Witch", generator=WitchHouseGenerator(variant="occult"),
                instrument="sawtooth", density=0.6, octave_shift=1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="dark_pulse"),
                instrument="synth_bass", density=0.6, octave_shift=-2),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="classic"),
                instrument="percussion", density=0.6, octave_shift=-1),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="dim_cluster"),
                instrument="dark_pad", density=0.4, octave_shift=-1),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir", density=0.4, octave_shift=1),
        ],
        out_dir=out_dir, bpm=70)

    # ------------------------------------------------------------------
    # Track 8: S P E C T R A L — Ghostly arpeggios + silence
    # ------------------------------------------------------------------
    generate_track("8 SPECTRAL",
        parts=[IdeaPart(
            name="Spirits", bars=16, scale=scales["spectral"], tempo=60,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Arp":      structure_to_schedule("R A R A:var", 4),
                "Ghost":    structure_to_schedule("R R A R", 4),
                "Pad":      structure_to_schedule("A", 16),
                "Sub":      structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Arp", generator=ArpeggiatorGenerator(pattern="up_down",
                rhythm=get_rhythm("straight_8ths")), instrument="bright_piano", density=0.4, octave_shift=1),
            TrackConfig(name="Ghost", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("half_note")), instrument="sweep_pad", density=0.2, octave_shift=2),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="minor_pad"),
                instrument="dark_pad", density=0.3, octave_shift=-1),
            TrackConfig(name="Sub", generator=DarkBassGenerator(mode="doom"),
                instrument="synth_bass", density=0.2, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=60)

    # ------------------------------------------------------------------
    # Track 9: S U M M O N I N G — Building occult crescendo
    # ------------------------------------------------------------------
    generate_track("9 SUMMONING",
        parts=[
            IdeaPart("Phase1_Whisper", 8, scales["summoning"], 65,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Pad":      structure_to_schedule("A", 8),
                    "Pluck":    structure_to_schedule("R A", 4),
                    "Bass":     structure_to_schedule("A", 8),
                }),
            IdeaPart("Phase2_Chant", 8, scales["summoning"], 70,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Pad":      structure_to_schedule("B", 8),
                    "Pluck":    structure_to_schedule("A B", 4),
                    "Choir":    structure_to_schedule("R A", 4),
                    "Bass":     structure_to_schedule("B", 8),
                }),
            IdeaPart("Phase3_Summon", 8, scales["summoning"], 80,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Pad":      structure_to_schedule("C", 8),
                    "Pluck":    structure_to_schedule("C D", 4),
                    "Choir":    structure_to_schedule("C D", 4),
                    "Drums":    structure_to_schedule("C D", 4),
                    "Bass":     structure_to_schedule("C", 8),
                }),
        ],
        tracks=[
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="phrygian_pad"),
                instrument="dark_pad", density=0.4, octave_shift=-1),
            TrackConfig(name="Pluck", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_8ths")), instrument="pluck", density=0.4, octave_shift=1),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir", density=0.4, octave_shift=1),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="classic"),
                instrument="percussion", density=0.5, octave_shift=-1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="dark_pulse"),
                instrument="synth_bass", density=0.5, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=65)

    # ------------------------------------------------------------------
    # Track 10: ✝ R I T U A L ✝ — Full reprise, the circle closes
    # ------------------------------------------------------------------
    generate_track("10 RITUAL",
        parts=[
            IdeaPart("Phase1_Open", 12, scales["ritual"], 72,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Witch":    structure_to_schedule("A B", 6),
                    "Bass":     structure_to_schedule("A B", 6),
                    "Drums":    structure_to_schedule("A B", 6),
                    "Pad":      structure_to_schedule("A", 12),
                    "Arp":      structure_to_schedule("R A R B", 3),
                    "Choir":    structure_to_schedule("R A", 6),
                }),
            IdeaPart("Phase2_Climax", 8, scales["ritual"], 85,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Witch":    structure_to_schedule("C D", 4),
                    "Bass":     structure_to_schedule("C D", 4),
                    "Drums":    structure_to_schedule("C D", 4),
                    "Pad":      structure_to_schedule("C", 8),
                    "Arp":      structure_to_schedule("C D", 4),
                    "Choir":    structure_to_schedule("C D", 4),
                }),
            IdeaPart("Phase3_Close", 8, scales["ritual"], 60,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Witch":    structure_to_schedule("E R", 4),
                    "Bass":     structure_to_schedule("E", 8),
                    "Pad":      structure_to_schedule("E", 8),
                    "Arp":      structure_to_schedule("R E", 4),
                }),
        ],
        tracks=[
            TrackConfig(name="Witch", generator=WitchHouseGenerator(variant="occult"),
                instrument="sawtooth", density=0.6, octave_shift=1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="industrial"),
                instrument="synth_bass", density=0.6, octave_shift=-2),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="classic"),
                instrument="percussion", density=0.6, octave_shift=-1),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="dim_cluster"),
                instrument="dark_pad", density=0.4, octave_shift=-1),
            TrackConfig(name="Arp", generator=ArpeggiatorGenerator(pattern="up",
                rhythm=get_rhythm("straight_8ths")), instrument="bright_piano", density=0.5, octave_shift=1),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="spread",
                rhythm=get_rhythm("whole_note")), instrument="choir", density=0.4, octave_shift=1),
        ],
        out_dir=out_dir, bpm=72)

    print("\n" + "=" * 80)
    print("  ✝✝✝ R I T U A L  C O M P L E T E ✝✝✝")
    print(f"  Output: {out_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
