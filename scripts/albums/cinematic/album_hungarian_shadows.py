# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_hungarian_shadows.py — Five études in the Hungarian (Gypsy) minor scale
[0, 2, 3, 6, 7, 8, 11], voiced so the geometric voice-leading is audible,
with a real sectional arrangement (staggered entrances + energy arc).

WHERE THE GEOMETRY LIVES
------------------------
The `Geometry_Piano` track runs `ChordGenerator`. Its `render()` chains
`prev_pitches` from one chord to the next and, for every chord, selects the
inversion that minimises `voice_leading_distance(prev_pitches, pitches)` —
the corrected bijective Tymoczko metric (Hungarian-algorithm assignment
over all voice permutations; see melodica/utils.py). Each chord is connected
to its predecessor by the globally minimal voice displacement.

WHERE THE ARRANGEMENT LIVES
---------------------------
Each movement is four concatenated IdeaParts — INTRO (BUILD) -> VERSE (BUILD)
-> CLIMAX (SUSTAIN) -> CODA (FADE) — with per-section `track_mute` so
instruments enter staggered (not all at beat 0) and `track_density` so the
intro/coda breathe. IdeaTool turns the section roles into an energy curve.
Harmony is `coupled_hmm` (mode-aware, no roman-numeral pitfalls on exotic
scales); melody tracks get the octave voice-leading smoother.
"""

from pathlib import Path

from melodica.idea_tool import (
    IdeaTool,
    IdeaToolConfig,
    TrackConfig,
    IdeaPart,
    _GM_PROGRAMS,
)
from melodica.generators import (
    ChordGenerator,
    StringsEnsembleGenerator,
    StringsPizzicatoGenerator,
    AmbientPadGenerator,
    BassGenerator,
    MelodyGenerator,
)
from melodica.rhythm import ProbabilisticRhythmGenerator
from melodica.types import Scale, Mode, SectionRole, SectionFunction
from melodica.midi import export_multitrack_midi


ALL_TRACKS = ["Geometry_Piano", "String_Chorus", "Pizz_Strings", "Dark_Pad", "Contrabass", "Lead_Melody"]


def _mute(*keep: str) -> list[str]:
    """Tracks to silence = all tracks except the ones named in `keep`."""
    return [t for t in ALL_TRACKS if t not in keep]


def _part(
    name: str,
    role: str,
    function: str,
    root: int,
    tempo: int,
    ts: tuple[int, int],
    bars: int,
    mute: list[str] | None = None,
    density: dict[str, float] | None = None,
) -> IdeaPart:
    return IdeaPart(
        name=f"{name}_{role}",
        bars=bars,
        scale=Scale(root, Mode.HUNGARIAN_MINOR),
        tempo=tempo,
        time_signature=ts,
        progression_type="coupled_hmm",
        section_type=SectionRole[role],
        section_function=SectionFunction[function],
        track_mute=mute or [],
        track_density=density or {},
    )


def _movement_sections(m: dict) -> list[IdeaPart]:
    """Build the four-section arc for one movement.

    INTRO  — rhythmic piano + contrabass only, thinned (BUILD); melody silent
    VERSE  — add pad + pizz ostinato + melody enters (BUILD)
    CLIMAX — full ensemble, sustained strings join, densest (SUSTAIN)
    CODA   — melody + strings + pizz drop out, piano + pad + bass fade (FADE)
    """
    name, root, tempo, ts = m["name"], m["root"], m["tempo"], m["ts"]
    b = m["bars"]  # {"intro","verse","climax","coda"}
    return [
        _part(
            name, "INTRO", "BUILD", root, tempo, ts, b["intro"],
            mute=_mute("Geometry_Piano", "Contrabass"),
            density={"Geometry_Piano": 0.55, "Contrabass": 0.45},
        ),
        _part(
            name, "VERSE", "BUILD", root, tempo, ts, b["verse"],
            mute=_mute("Geometry_Piano", "Dark_Pad", "Contrabass", "Lead_Melody", "Pizz_Strings"),
        ),
        _part(
            name, "CLIMAX", "SUSTAIN", root, tempo, ts, b["climax"],
            mute=[],
            density={"Geometry_Piano": 0.95, "String_Chorus": 0.85, "Pizz_Strings": 0.85, "Lead_Melody": 0.7},
        ),
        _part(
            name, "CODA", "FADE", root, tempo, ts, b["coda"],
            mute=_mute("Geometry_Piano", "Dark_Pad", "Contrabass"),
            density={"Geometry_Piano": 0.5, "Dark_Pad": 0.4, "Contrabass": 0.35},
        ),
    ]


def main() -> None:
    print("=" * 80)
    print("  H U N G A R I A N   S H A D O W S")
    print("  Five études in Hungarian minor  |  geometric voice-leading + arc")
    print("=" * 80)

    out_dir = Path("output/album_hungarian_shadows")
    out_dir.mkdir(exist_ok=True, parents=True)

    # Five movements across roots of the Hungarian minor scale (D, A, C, F, E).
    # bars layout per section sums to the movement length.
    movements = [
        {"name": "01_Litany",            "root": 2, "tempo": 60, "ts": (4, 4),
         "bars": {"intro": 2, "verse": 4, "climax": 4, "coda": 2}},
        {"name": "02_The_Magnetar",      "root": 9, "tempo": 76, "ts": (4, 4),
         "bars": {"intro": 2, "verse": 4, "climax": 4, "coda": 2}},
        {"name": "03_Glass_Cartographer","root": 0, "tempo": 88, "ts": (4, 4),
         "bars": {"intro": 2, "verse": 4, "climax": 4, "coda": 2}},
        {"name": "04_Augmented_Seconds", "root": 5, "tempo": 96, "ts": (4, 4),
         "bars": {"intro": 2, "verse": 4, "climax": 6, "coda": 2}},
        {"name": "05_Apocrypha",         "root": 4, "tempo": 64, "ts": (3, 4),
         "bars": {"intro": 2, "verse": 3, "climax": 3, "coda": 2}},
    ]

    # Geometry carrier first: closed block chords + doubled bass octave.
    # ChordGenerator.render() chains prev_pitches across the progression and
    # picks each inversion via voice_leading_distance() — the audible geometry.
    tracks_common = [
        TrackConfig(
            name="Geometry_Piano",
            generator=ChordGenerator(
                voicing="closed",
                add_bass_note=-2,
                rhythm=ProbabilisticRhythmGenerator(
                    grid_resolution=1.0, density=0.65, downbeat_weight=0.3,
                    gate=0.55, seed=7,
                ),
            ),
            instrument="piano",
            density=0.9,
        ),
        TrackConfig(
            name="String_Chorus",
            generator=StringsEnsembleGenerator(
                section_size="full", articulation="legato", divisi=4
            ),
            instrument="strings",
            density=0.7,
        ),
        TrackConfig(
            name="Pizz_Strings",
            generator=StringsPizzicatoGenerator(pattern="ostinato", section_divisi=2),
            instrument="strings",
            density=0.7,
            octave_shift=-1,
        ),
        TrackConfig(
            name="Dark_Pad",
            generator=AmbientPadGenerator(voicing="spread"),
            instrument="dark_pad",
            density=0.6,
            octave_shift=-1,
        ),
        TrackConfig(
            name="Contrabass",
            generator=BassGenerator(style="root_only"),
            instrument="contrabass",
            density=0.6,
            octave_shift=-2,
        ),
        TrackConfig(
            name="Lead_Melody",
            generator_type="melody",
            generator=MelodyGenerator(
                prefer_chord_tones=0.7,
                note_range_low=74,
                note_range_high=96,
                allow_2nd=True,
                allow_7th=True,
            ),
            instrument="flute",
            density=0.6,
        ),
    ]

    instruments_map = {
        t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks_common
    }

    for m in movements:
        print(f"\n--- Composing: {m['name']}  (root={m['root']} Hungarian minor) ---")
        parts = _movement_sections(m)
        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            workflow="generate_melody_then_harmonize",
            scale=Scale(m["root"], Mode.HUNGARIAN_MINOR),
            parts=parts,
            tracks=tracks_common,
            use_voice_leading=True,
            use_tension_curve=True,
        )

        notes_dict = IdeaTool(tool_config).generate()
        tracks_data = {
            k: v
            for k, v in notes_dict.items()
            if not k.startswith("_") and isinstance(v, list)
        }

        filepath = out_dir / f"{m['name']}.mid"
        export_multitrack_midi(
            tracks_data,
            str(filepath),
            bpm=m["tempo"],
            time_sig=m["ts"],
            instruments=instruments_map,
        )
        print(f"    exported {filepath.name}")

    print("\n" + "=" * 80)
    print(f"  PRODUCTION COMPLETE. Output: {out_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
