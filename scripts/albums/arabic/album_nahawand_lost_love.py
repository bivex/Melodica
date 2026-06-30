# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/arabic/album_nahawand_lost_love.py
    — "Nahawand: Lost Love (نهاوند — حب ضائع)"

A song-cycle on the Nahawand maqam (A natural-minor) tracing the anatomy of a
heartbreak. Each movement is a stage of grieving, with a DIFFERENT musical
structure and melodic character so the cycle develops rather than repeats:

    01 The Last Letter      — Denial    (AABA ballad, sparse, questioning)
    02 Empty Room           — Anger     (ostinato-driven, sharp, syncopated)
    03 Memory in Rain       — Bargaining(canonical counterpoint, weeping canon)
    04 Insomnia             — Depression(nocturne, sparse piano + drone, dark)
    05 Acceptance           — Resolve   (rondo A-B-A-C-A, open, cadential)

CoupledHMM harmony (which is diatonic & functional on Nahawand), A as the tonal
centre throughout. The melodic interest comes from per-movement contour, motif
development, direction bias, and drama shapes — not from changing the mode.
"""

from pathlib import Path

from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

from melodica.generators.melody import MelodyGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.canon import CanonGenerator
from melodica.generators.plucked_solo import PianoSoloGenerator
from melodica.generators.orchestral_strings import (
    ViolinGenerator, ViolaGenerator, CelloGenerator, ContrabassGenerator,
)
from melodica.generators.orchestral_brass import FrenchHornGenerator
from melodica.generators.orchestral_woodwinds import OboeGenerator
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.chromatic_percussion import VibraphoneGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.bass import BassGenerator


# The single tonal centre of the whole cycle — A Nahawand (A natural-minor).
NAHAWAND = Scale(root=9, mode=Mode.NATURAL_MINOR)


def generate_nahawand_lost_love():
    album_dir = Path("output/album_nahawand_lost_love")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("    N A H A W A N D   :   L O S T   L O V E")
    print("    نهاوند — حب ضائع   A Song-Cycle of Heartbreak on A minor")
    print("=" * 80)

    movements = [
        # name, tempo, time-sig, bars, stage
        ("01_The_Last_Letter", 66, (4, 4), 32, "Denial"),
        ("02_Empty_Room",      96, (4, 4), 32, "Anger"),
        ("03_Memory_in_Rain",  72, (3, 4), 36, "Bargaining"),
        ("04_Insomnia",        54, (4, 4), 32, "Depression"),
        ("05_Acceptance",      78, (4, 4), 40, "Resolve"),
    ]

    tracks_map = {
        # ── 01: The Last Letter (Denial) — AABA ballad ─────────────────────
        # A questioning oboe melody over sparse piano; the AABA form mirrors
        # reading a letter again and again. Arch contour, gentle climb.
        "01_The_Last_Letter": [
            TrackConfig(
                name="Letter_Oboe",
                generator=MelodyGenerator(
                    direction_bias=0.15, phrase_contour="arch",
                    phrase_length=8.0, climax="auto", drama_shape="crescendo",
                    motif_probability=0.5, after_leap="step_opposite",
                    note_range_low=67, note_range_high=84,
                ),
                instrument="oboe", density=0.45, mpe=True,
                phrase_schedule=structure_to_schedule("A A B A", 8),
            ),
            TrackConfig(
                name="Reading_Piano",
                generator=PianoSoloGenerator(instrument="grand_piano", pedal=True, note_density=0.35),
                instrument="piano", density=0.4,
            ),
            TrackConfig(
                name="Quiet_Cello",
                generator=CelloGenerator(articulation="sustained", vibrato=True),
                instrument="cello", density=0.3,
            ),
            TrackConfig(
                name="Letter_Bass",
                generator=BassGenerator(style="root_only"),
                instrument="contrabass", density=0.35, octave_shift=-1,
            ),
        ],

        # ── 02: Empty Room (Anger) — ostinato-driven, sharp ────────────────
        # A grinding ostinato anchors frustration; a jagged, descending lead
        # (negative direction bias) fights against it; percussion stabs.
        "02_Empty_Room": [
            TrackConfig(
                name="Anger_Ostinato",
                generator=OstinatoGenerator(pattern="chromatic_pulse"),
                instrument="piano", density=0.7,
            ),
            TrackConfig(
                name="Jagged_Lead",
                generator=MelodyGenerator(
                    direction_bias=-0.35, phrase_contour="rise_fall",
                    phrase_length=4.0, syncopation=0.35, rhythm_variety=0.5,
                    allow_2nd=True, ornament_probability=0.15,
                    note_range_low=64, note_range_high=84,
                ),
                instrument="trumpet", density=0.55, mpe=True,
            ),

            TrackConfig(
                name="Anger_Bass",
                generator=BassGenerator(style="walking"),
                instrument="contrabass", density=0.6, octave_shift=-1,
            ),
            TrackConfig(
                name="Tense_Strings",
                generator=StringsLegatoGenerator(),
                instrument="strings", density=0.4,
            ),
        ],

        # ── 03: Memory in Rain (Bargaining) — canonical counterpoint ───────
        # Two voices in canon (violin & viola) chase each other like memories
        # that won't settle; harp-like rain; the canon itself is the structure.
        "03_Memory_in_Rain": [
            TrackConfig(
                name="Memory_Violin",
                generator=ViolinGenerator(articulation="legato", vibrato=True),
                instrument="violin", density=0.45, mpe=True,
            ),
            TrackConfig(
                name="Echo_Viola",
                generator=ViolaGenerator(articulation="legato", vibrato=True),
                instrument="viola", density=0.4, mpe=True,
            ),
            TrackConfig(
                name="Rain_Harp",
                generator=CanonGenerator(n_voices=2, interval=7, delay_beats=4.0),
                instrument="harp", density=0.4,
            ),
            TrackConfig(
                name="Rain_Cello",
                generator=CelloGenerator(articulation="sustained", vibrato=False),
                instrument="cello", density=0.3,
            ),
        ],

        # ── 04: Insomnia (Depression) — nocturne, sparse & dark ────────────
        # A lone piano in the dark; a low drone of dread; a single oboe cry.
        # Very low density — silence is the point. No bass pulse, no drums.
        "04_Insomnia": [
            TrackConfig(
                name="Sleepless_Piano",
                generator=PianoSoloGenerator(instrument="grand_piano", pedal=True, note_density=0.25),
                instrument="piano", density=0.35, octave_shift=-1,
            ),
            TrackConfig(
                name="Dread_Drone",
                generator=DroneGenerator(variant="tonic", fade_in=6.0, fade_out=6.0),
                instrument="dark_pad", density=0.9, octave_shift=-2,
            ),
            TrackConfig(
                name="Night_Oboe",
                generator=MelodyGenerator(
                    direction_bias=0.0, phrase_contour="spiral",
                    phrase_length=12.0, motif_probability=0.3,
                    note_range_low=62, note_range_high=79,
                ),
                instrument="oboe", density=0.3, mpe=True,
            ),
            TrackConfig(
                name="Mourning_Choir",
                generator=ChoirAahsGenerator(voice_count=4, dynamics="pp", syllable="aah"),
                instrument="choir", density=0.25,
            ),
        ],

        # ── 05: Acceptance (Resolve) — rondo A-B-A-C-A, cadential ──────────
        # Warm horn, full strings, a rising melody that finally breathes.
        # The rondo returns to A (acceptance) after each digression; the lead
        # has a positive bias and a mountain contour — reaching upward.
        "05_Acceptance": [
            TrackConfig(
                name="Resolve_Horn",
                generator=MelodyGenerator(
                    direction_bias=0.3, phrase_contour="rise",
                    phrase_length=8.0, climax="up_5th", drama_shape="epic",
                    motif_probability=0.45, penultimate_step_above=True,
                    note_range_low=65, note_range_high=84,
                ),
                instrument="french_horn", density=0.5, mpe=True,
                phrase_schedule=structure_to_schedule("A B A C A", 8),
            ),
            TrackConfig(
                name="Warm_Strings",
                generator=StringsEnsembleGenerator(section_size="full", articulation="legato", dynamic_curve="crescendo"),
                instrument="strings", density=0.55,
            ),
            TrackConfig(
                name="Resolve_Cello",
                generator=CelloGenerator(articulation="sustained", vibrato=True),
                instrument="cello", density=0.35,
            ),
            TrackConfig(
                name="Resolve_Bass",
                generator=BassGenerator(style="root_only"),
                instrument="contrabass", density=0.4, octave_shift=-1,
            ),
            TrackConfig(
                name="Hope_Vibes",
                generator=VibraphoneGenerator(note_density=0.3),
                instrument="vibraphone", density=0.3,
            ),
        ],
    }

    for name, tempo, ts, bars, stage in movements:
        print(f"\n--- Composing: {name} [{stage}, A Nahawand, {ts[0]}/{ts[1]}, {tempo} BPM] ---")

        parts = [IdeaPart(
            name=name, bars=bars,
            scale=NAHAWAND, tempo=tempo,
            time_signature=ts,
            progression_type="coupled_hmm",
        )]

        track_list = tracks_map[name]
        instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in track_list}

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            time_signature=ts,
            tempo=tempo,
            scale=NAHAWAND,
            use_tension_curve=True,
            use_harmonic_verifier=True,
            parts=parts,
            tracks=track_list,
        )

        notes_dict = IdeaTool(tool_config).generate()
        tracks_data = {k: v for k, v in notes_dict.items()
                       if not k.startswith("_") and isinstance(v, list)}

        export_multitrack_midi(
            tracks_data, str(album_dir / f"{name}.mid"),
            bpm=tempo, key=NAHAWAND,
            instruments=instruments_map,
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set()),
        )
        # Report the harmony actually generated for this movement.
        chords = notes_dict.get("_chords") or []
        if chords:
            NOTE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            prog = " ".join(f"{NOTE[c.root % 12]}{c.quality.name}" for c in chords)
            print(f"    Harmony ({len(chords)} chords): {prog}")
        print(f"    Exported {name}.mid")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: NAHAWAND — LOST LOVE")
    print("  Cycle: Denial → Anger → Bargaining → Depression → Acceptance")
    print("  Maqam: Nahawand (A natural-minor) throughout")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    generate_nahawand_lost_love()
