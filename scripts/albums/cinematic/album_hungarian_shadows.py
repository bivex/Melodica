# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_hungarian_shadows.py — Five études in the Hungarian (Gypsy) minor scale
[0, 2, 3, 6, 7, 8, 11], voiced so the geometric voice-leading is audible.

WHERE THE GEOMETRY LIVES
------------------------
The `Geometry_Piano` track runs `ChordGenerator`. Its `render()` chains
`prev_pitches` from one chord to the next and, for every chord, selects the
inversion that minimises `voice_leading_distance(prev_pitches, pitches)` —
the *corrected bijective* Tymoczko metric (Hungarian-algorithm assignment
over all voice permutations; see melodica/utils.py). So each chord is
connected to its predecessor by the globally minimal voice displacement,
not a greedy nearest-note match. That smooth, common-tone chaining is the
audible signature of the geometry.

Harmony comes from `progression_type="coupled_hmm"` — the mode-aware
Tymoczko/Newman harmonizer — which sidesteps roman-numeral pitfalls on an
exotic scale. Melody tracks get the octave voice-leading smoother
(`use_voice_leading=True`).

Movements modulate through five roots of the Hungarian minor scale for
colour, all over the same dark-orchestral ensemble.
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
    AmbientPadGenerator,
    BassGenerator,
    FluteGenerator,
)
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi


def main() -> None:
    print("=" * 80)
    print("  H U N G A R I A N   S H A D O W S")
    print("  Five études in Hungarian minor  |  geometric voice-leading")
    print("=" * 80)

    out_dir = Path("output/album_hungarian_shadows")
    out_dir.mkdir(exist_ok=True, parents=True)

    # Five movements, each in a different root of the Hungarian minor scale.
    # roots: D, A, C, F, E  — spreads colour across the circle.
    movements = [
        {"name": "01_Litany",        "root": 2, "bars": 10, "tempo": 60, "ts": (4, 4)},
        {"name": "02_The_Magnetar",  "root": 9, "bars": 12, "tempo": 76, "ts": (4, 4)},
        {"name": "03_Glass_Cartographer", "root": 0, "bars": 12, "tempo": 88, "ts": (4, 4)},
        {"name": "04_Augmented_Seconds", "root": 5, "bars": 14, "tempo": 96, "ts": (4, 4)},
        {"name": "05_Apocrypha",     "root": 4, "bars": 12, "tempo": 64, "ts": (3, 4)},
    ]

    # Geometry carrier: closed block chords with a doubled bass octave.
    # ChordGenerator.render() chains prev_pitches across the progression and
    # picks each inversion via voice_leading_distance() — the audible geometry.
    tracks_common = [
        TrackConfig(
            name="Geometry_Piano",
            generator=ChordGenerator(voicing="closed", add_bass_note=-2),
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
            name="Lead_Flute",
            generator=FluteGenerator(),
            instrument="flute",
            density=0.45,
            octave_shift=1,
        ),
    ]

    instruments_map = {
        t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks_common
    }

    for m in movements:
        print(f"\n--- Composing: {m['name']}  (root={m['root']} Hungarian minor) ---")
        parts = [
            IdeaPart(
                name=m["name"],
                bars=m["bars"],
                scale=Scale(m["root"], Mode.HUNGARIAN_MINOR),
                tempo=m["tempo"],
                time_signature=m["ts"],
                progression_type="coupled_hmm",
            )
        ]
        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
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
