# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/orchestral/album_cosmic_voyage.py
    — "Cosmic Voyage (Космическое Путешествие)"

A 6-movement orchestral suite tracing a deep-space mission: from the launch
pad to the silence between galaxies and the lonely return home. Each movement
inhabits a different mode that paints its physical/emotional reality, and a
different ensemble + structural device so the voyage develops rather than
repeats.

    01 Countdown / Liftoff   — D Lydian    (anticipation → ignition, fanfares)
    02 Weightless             — F# Whole-Tone (zero-g, floating, no gravity)
    03 First Light of Distant Suns — A Lydian-Augmented (alien beauty, awe)
    04 Into the Nebula        — C# Phrygian  (danger, the unknown, darkness)
    05 The Silent Void        — G# Aeolian   (isolation, immensity, dread)
    06 Homecoming             — D Lydian     (warmth, relief, cadential return)

CoupledHMM harmony. Real per-movement structure (fanfare build, pointillist
weightlessness, chorale awe, ostinato danger, sparse void, rondo return).
"""

from pathlib import Path

from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

# Solo orchestral instruments
from melodica.generators.orchestral_strings import (
    ViolinGenerator, ViolaGenerator, CelloGenerator, ContrabassGenerator,
)
from melodica.generators.orchestral_brass import (
    TrumpetGenerator, TromboneGenerator, FrenchHornGenerator,
)
from melodica.generators.orchestral_woodwinds import (
    FluteGenerator, OboeGenerator, ClarinetGenerator, BassoonGenerator,
)
from melodica.generators.orchestral_percussion import TimpaniGenerator

# Sections / texture
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator

# Cosmic / specialty
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.chorale import ChoraleGenerator
from melodica.generators.canon import CanonGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator


# ── The voyage's harmonic map ──────────────────────────────────────────────
# Modes chosen to paint each environment: Lydian = open/soaring hope,
# whole-tone = weightless/hanging, lydian-augmented = alien beauty,
# phrygian = dark unknown, aeolian = cold isolation.
D_LYD  = Scale(root=2,  mode=Mode.LYDIAN)             # 01 + 06
FS_WT  = Scale(root=6,  mode=Mode.WHOLE_TONE)         # 02 weightless
A_LYA  = Scale(root=9,  mode=Mode.LYDIAN_AUG_MODE)    # 03 alien beauty
CS_PHY = Scale(root=1,  mode=Mode.PHRYGIAN)           # 04 nebula danger
GS_AEO = Scale(root=8,  mode=Mode.AEOLIAN)            # 05 void


def generate_cosmic_voyage():
    album_dir = Path("output/album_cosmic_voyage")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("    C O S M I C   V O Y A G E")
    print("    Космическое Путешествие  —  An Orchestral Space Mission")
    print("=" * 80)

    movements = [
        # name, scale, tempo, ts, bars
        ("01_Countdown_Liftoff", D_LYD,  72, (4, 4), 40),
        ("02_Weightless",        FS_WT,  60, (3, 4), 36),
        ("03_Distant_Suns",      A_LYA,  66, (4, 4), 40),
        ("04_Into_the_Nebula",   CS_PHY, 80, (4, 4), 40),
        ("05_The_Silent_Void",   GS_AEO, 52, (4, 4), 36),
        ("06_Homecoming",        D_LYD,  84, (4, 4), 44),
    ]

    tracks_map = {
        # ── 01: Countdown / Liftoff (D Lydian) — fanfare build to ignition ─
        # A pedal-bass countdown, then horns/trumpets climb, timpani rolls,
        # an orchestral hit at "ignition", full choir soars. Structure = build.
        "01_Countdown_Liftoff": [
            TrackConfig(
                name="Countdown_Pedal",
                generator=PedalBassGenerator(pedal_note="root", sustain=4.0),
                instrument="contrabass", density=0.5, octave_shift=-1,
            ),
            TrackConfig(
                name="Ascent_Horn",
                generator=FrenchHornGenerator(articulation="sustained", dynamic_curve="swell", fanfare_mode=True),
                instrument="french_horn", density=0.45,
                phrase_schedule=structure_to_schedule("A A B C", 8),
            ),
            TrackConfig(
                name="Ignition_Trumpet",
                generator=TrumpetGenerator(articulation="legato", register=3),
                instrument="trumpet", density=0.4,
            ),
            TrackConfig(
                name="Launch_Timpani",
                generator=TimpaniGenerator(),
                instrument="timpani", density=0.5,
            ),
            TrackConfig(
                name="Ignition_Hit",
                generator=OrchestralHitGenerator(hit_type="staccato", voicing="chord", reverb_tail=3.0),
                instrument="orchestral_hit", density=0.2,
            ),
            TrackConfig(
                name="Liftoff_Choir",
                generator=ChoirAahsGenerator(voice_count=4, dynamics="f", syllable="aah"),
                instrument="choir", density=0.4,
            ),
        ],

        # ── 02: Weightless (F# Whole-Tone) — zero-g, floating, hanging ──────
        # Whole-tone = no leading tones, nothing resolves, everything hangs.
        # Pointillist flutes/clarinet, nebula cloud, suspended strings, no bass.
        "02_Weightless": [
            TrackConfig(
                name="Floating_Flute",
                generator=FluteGenerator(articulation="legato", vibrato=True, breath_phrase=True, register=3),
                instrument="flute", density=0.35, mpe=True,
            ),
            TrackConfig(
                name="Drifting_Clarinet",
                generator=ClarinetGenerator(articulation="legato", register=2),
                instrument="clarinet", density=0.3, mpe=True,
            ),
            TrackConfig(
                name="Star_Cloud",
                generator=NebulaGenerator(variant="cloud", density_notes=6, pitch_spread=18, note_duration=4.0, overlap=0.7),
                instrument="dark_pad", density=0.5,
            ),
            TrackConfig(
                name="Suspended_Strings",
                generator=StringsLegatoGenerator(),
                instrument="strings", density=0.35,
            ),
        ],

        # ── 03: First Light of Distant Suns (A Lydian-Aug) — alien beauty ──
        # Lydian-augmented = the augmented-4th + raised-5th paints a sky with
        # two suns. A reverent chorale of strings/choir; solo oboe melody of
        # awe; glockenspiel = starlight; tubular bells = cosmic grandeur.
        "03_Distant_Suns": [
            TrackConfig(
                name="Awe_Oboe",
                generator=OboeGenerator(articulation="legato", register=2),
                instrument="oboe", density=0.35, mpe=True,
            ),
            TrackConfig(
                name="Awe_Choral_Strings",
                generator=ChoraleGenerator(voice_spacing=16),
                instrument="strings", density=0.45,
            ),
            TrackConfig(
                name="Starlight_Glock",
                generator=GlockenspielGenerator(),
                instrument="glockenspiel", density=0.3, octave_shift=1,
            ),
            TrackConfig(
                name="Cosmic_Bells",
                generator=TubularBellsGenerator(stroke_pattern="single"),
                instrument="tubular_bells", density=0.25,
            ),
            TrackConfig(
                name="Reverent_Choir",
                generator=ChoirAahsGenerator(voice_count=4, dynamics="mp", syllable="ooh"),
                instrument="choir", density=0.3,
            ),
        ],

        # ── 04: Into the Nebula (C# Phrygian) — danger, the unknown ────────
        # Phrygian = dark, tense (lowered-2nd). A grinding ostinato, low
        # brass menace, timpani pulse, nebula as threat. Structure = ostinato.
        "04_Into_the_Nebula": [
            TrackConfig(
                name="Nebula_Ostinato",
                generator=OstinatoGenerator(pattern="chromatic_pulse"),
                instrument="piano", density=0.6,
            ),
            TrackConfig(
                name="Menace_Trombone",
                generator=TromboneGenerator(articulation="sustained", register=1),
                instrument="trombone", density=0.35,
            ),
            TrackConfig(
                name="Dark_Strings",
                generator=StringsLegatoGenerator(),
                instrument="strings", density=0.4,
            ),
            TrackConfig(
                name="Threat_Timpani",
                generator=TimpaniGenerator(),
                instrument="timpani", density=0.45,
            ),
            TrackConfig(
                name="Dark_Cloud",
                generator=NebulaGenerator(variant="cloud", density_notes=4, pitch_spread=12, note_duration=3.0),
                instrument="dark_pad", density=0.4, octave_shift=-1,
            ),
        ],

        # ── 05: The Silent Void (G# Aeolian) — isolation, immensity, dread ─
        # Aeolian = cold minor. Very sparse — silence IS the void. Solo cello
        # as a lone voice, contrabass weight, distant choir, nebula as emptiness.
        "05_The_Silent_Void": [
            TrackConfig(
                name="Lonely_Cello",
                generator=CelloGenerator(articulation="sustained", vibrato=True),
                instrument="cello", density=0.25, mpe=True,
            ),
            TrackConfig(
                name="Void_Bass",
                generator=ContrabassGenerator(vibrato=False),
                instrument="contrabass", density=0.2,
            ),
            TrackConfig(
                name="Distant_Choir",
                generator=ChoirAahsGenerator(voice_count=4, dynamics="pp", syllable="aah"),
                instrument="choir", density=0.2, octave_shift=-1,
            ),
            TrackConfig(
                name="Emptiness_Cloud",
                generator=NebulaGenerator(variant="cloud", density_notes=3, pitch_spread=24, note_duration=6.0, overlap=0.8),
                instrument="dark_pad", density=0.35, octave_shift=-1,
            ),
        ],

        # ── 06: Homecoming (D Lydian) — warmth, relief, cadential return ───
        # Return to the opening D Lydian = home. Rondo A-B-A-C-A so the theme
        # keeps coming back like the thought of Earth. Full ensemble, warm horn,
        # cascading strings, celebratory bells.
        "06_Homecoming": [
            TrackConfig(
                name="Home_Horn",
                generator=FrenchHornGenerator(articulation="sustained", dynamic_curve="swell", fanfare_mode=True),
                instrument="french_horn", density=0.45,
                phrase_schedule=structure_to_schedule("A B A C A", 8),
            ),
            TrackConfig(
                name="Cascade_Strings",
                generator=StringsEnsembleGenerator(section_size="full", articulation="legato", dynamic_curve="crescendo"),
                instrument="strings", density=0.55,
            ),
            TrackConfig(
                name="Joy_Trumpet",
                generator=TrumpetGenerator(articulation="legato", register=2),
                instrument="trumpet", density=0.4,
            ),
            TrackConfig(
                name="Joy_Choir",
                generator=ChoirAahsGenerator(voice_count=4, dynamics="f", syllable="aah"),
                instrument="choir", density=0.4,
            ),
            TrackConfig(
                name="Celebration_Bells",
                generator=TubularBellsGenerator(stroke_pattern="single"),
                instrument="tubular_bells", density=0.3,
            ),
        ],
    }

    for name, scale, tempo, ts, bars in movements:
        print(f"\n--- Composing: {name} [{scale.mode.value}, {ts[0]}/{ts[1]}, {tempo} BPM] ---")

        parts = [IdeaPart(
            name=name, bars=bars,
            scale=scale, tempo=tempo,
            time_signature=ts,
            progression_type="coupled_hmm",
        )]

        track_list = tracks_map[name]
        instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in track_list}

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            time_signature=ts,
            tempo=tempo,
            scale=scale,
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
            bpm=tempo, key=scale,
            instruments=instruments_map,
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set()),
        )
        chords = notes_dict.get("_chords") or []
        if chords:
            NOTE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            prog = " ".join(f"{NOTE[c.root % 12]}{c.quality.name}" for c in chords)
            print(f"    Harmony ({len(chords)} chords): {prog}")
        print(f"    Exported {name}.mid")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: COSMIC VOYAGE")
    print("  Mission: Liftoff → Weightless → Distant Suns → Nebula → Void → Home")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    generate_cosmic_voyage()
