# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_witcher_contempt_tempo_map.py — "Time of Contempt: A Witcher Saga Symphony (Dynamic Tempo Map Edition)"
Inspired by Andrzej Sapkowski's fourth book.
Features Slavic folk elements, Imperial Nilfgaardian brass, and the tragic theme of Ciri.
Uses the core Melodica TempoModulator profiles (rubato, agitato, industrial, chaotic, combat, madness, requiem).
Bar-aware: per-track time signatures via BarGrid (6/8, 3/4, 4/4, 5/4, 7/8).
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool,
    IdeaToolConfig,
    TrackConfig,
    IdeaPart,
    PhraseSchedule,
    PhraseSlot,
)
from melodica.modifiers import LimitNoteRangeModifier, ModifierContext
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

# Generators
from melodica.generators.orchestral_strings import (
    ViolinGenerator,
    CelloGenerator,
    ContrabassGenerator,
)
from melodica.generators.orchestral_brass import (
    FrenchHornGenerator,
    TromboneGenerator,
)
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.snare_drum import SnareDrumGenerator
from melodica.generators.piano_comp import PianoCompGenerator


# Role-based register bands (low, high MIDI). Strategy: isolate ONE sub-bass
# voice (clears ARR-11 sub-bass mud) and push leads above the mid cluster
# (clears ARR-10 register crossings). Mid-range sections (horns/choir/organ/
# brass) deliberately overlap — that's correct orchestration; clamping them
# into non-overlapping bands would destroy the voicing and concentrate notes
# into worse clashes. Notes outside a band are octave-shifted into it.
_REGISTER_BANDS: dict[str, tuple[int, int]] = {
    "Low Strings": (24, 40),        # sole sub-bass voice
    "Cimbasso Heavy": (45, 60),     # low brass, cleared of sub zone
    "French Horns": (48, 64),       # tenor
    "Imperial Trombones": (53, 67), # tenor
    "Solo Cello": (48, 67),         # tenor
    "Prophecy Choir": (52, 70),     # mid
    "Brass Majesty": (52, 74),      # mid
    "Cathedral Organ": (55, 79),    # mid
    "Violins Ensemble": (74, 96),   # high — above the mid cluster
    "Fast Violins": (74, 96),       # high
    "Vocal Lead": (55, 82),         # mid-high lead
    "Taiko Drums": (40, 60),
    "Orchestral Perc": (45, 62),
}

# Periodic rest for melodic leads so a line never runs 100+ beats without
# breathing room (ARR-13). Tiles play/rest across the whole part.
_LEAD_REST_SCHEDULE = PhraseSchedule(
    slots=[PhraseSlot(kind="play", bars=8), PhraseSlot(kind="rest", bars=1)],
    loop=True,
)

# Hand-authored functional progressions per movement ("master's voice"). Used as
# constraints for constrained_hmm: the HMM still fits each track's melody contour
# and voice-leading, but anchors to these chords + durations — replacing the
# generic statistical progressions from plain coupled_hmm. Each chord = 1 bar
# (duration = time_signature numerator beats). Roman numerals are relative to
# each movement's scale (parse_progression / Scale.parse_roman).
_PROGRESSIONS: dict[str, list[str]] = {
    # NB: numerals are DIATONIC to each mode (parse_roman flats/raises by
    # semitone), so e.g. Dorian "b7" is written VII, Phrygian "b2" is II, etc.
    "frantic_strings":     ["Im9:6.0", "VII:6.0",     "IVmaj9:6.0", "VII:6.0"],     # Dm9-C-G-C Dorian gallop
    "lyrical_tragedy":     ["Im9:3.0", "VImaj9:3.0",   "IIImaj7:3.0","VII:3.0"],     # Dm9-Bb-F-C noble elegy
    "imperial_industrial": ["Im:4.0",  "II:4.0",      "VImaj7:4.0", "II:4.0"],       # Em-F-C-F Phrygian dread
    "magic_chaos":         ["Idim:5.0","II:5.0",      "V:5.0",      "VII:5.0"],      # Gdim-Ab-Db-F Locrian betrayal
    "witcher_combat":      ["Im:6.0",  "iv7:6.0",     "V7:6.0",     "Im:6.0"],       # Dm-Gm-A7-Dm harmonic-minor battle
    "madness_folk":        ["Im:7.0",  "IVaug:7.0",   "Idim:7.0",   "IVaug:7.0"],    # Hungarian-minor exotic madness
    "epic_requiem":        ["Im9:3.0", "VII:3.0",     "VImaj9:3.0", "V:3.0"],        # Em9-D-C-Bb Andalusian cadence
}

# Mapping styles to new kernel-level tempo profiles
_PROFILE_MAP = {
    "frantic_strings": "agitato",
    "lyrical_tragedy": "rubato",
    "imperial_industrial": "industrial",
    "magic_chaos": "chaotic",
    "witcher_combat": "combat",
    "madness_folk": "madness",
    "epic_requiem": "requiem",
}


def generate_witcher_album_tempo_map():
    album_dir = Path("output/album_witcher_contempt_tempo_map")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        T I M E   O F   C O N T E M P T  (TEMPO MAP EDITION)")
    print("        A Witcher Saga Symphony")
    print("=" * 80)

    # Full 7-track concept
    tracks_configs = [
        {
            "name": "01_Aplegatts_Ride",
            "tempo": 138,
            "scale": Scale(root=2, mode=Mode.DORIAN),
            "bars": 64,
            "description": "Fast, anxious path of the royal messenger. High-tension violins.",
            "style_hint": "frantic_strings",
            "progression_type": "coupled_hmm",
            "time_signature": (6, 8),
        },
        {
            "name": "02_Cintras_Legacy",
            "tempo": 68,
            "scale": Scale(root=2, mode=Mode.AEOLIAN),
            "bars": 48,
            "description": "Tragic theme for Ciri. Solo cello and breathy vocal.",
            "style_hint": "lyrical_tragedy",
            "progression_type": "coupled_hmm",
            "time_signature": (3, 4),
        },
        {
            "name": "03_The_Black_Wings",
            "tempo": 82,
            "scale": Scale(root=2, mode=Mode.PHRYGIAN),
            "bars": 56,
            "description": "Nilfgaardian theme. Heavy brass and industrial drones.",
            "style_hint": "imperial_industrial",
            "progression_type": "coupled_hmm",
            "time_signature": (4, 4),
        },
        {
            "name": "04_Thanedd_The_Coup",
            "tempo": 115,
            "scale": Scale(root=7, mode=Mode.LOCRIAN),
            "bars": 80,
            "description": "Magic betrayal. Dissonance, choir, and sharp hits.",
            "style_hint": "magic_chaos",
            "progression_type": "coupled_hmm",
            "time_signature": (5, 4),
        },
        {
            "name": "05_The_White_Wolf",
            "tempo": 142,
            "scale": Scale(root=2, mode=Mode.HARMONIC_MINOR),
            "bars": 72,
            "description": "Geralt's battle theme. Aggressive staccato and taiko.",
            "style_hint": "witcher_combat",
            "progression_type": "coupled_hmm",
            "time_signature": (6, 8),
        },
        {
            "name": "06_Falkas_Fire",
            "tempo": 62,
            "scale": Scale(root=4, mode=Mode.HUNGARIAN_MINOR),
            "bars": 48,
            "description": "Madness theme. Trembling vocal and dark pads.",
            "style_hint": "madness_folk",
            "progression_type": "coupled_hmm",
            "time_signature": (7, 8),
        },
        {
            "name": "07_The_Hour_of_Contempt",
            "tempo": 54,
            "scale": Scale(root=2, mode=Mode.PHRYGIAN),
            "bars": 64,
            "description": "Final requiem. Full orchestra, organ, and fading drone.",
            "style_hint": "epic_requiem",
            "progression_type": "coupled_hmm",
            "time_signature": (3, 4),
        },
    ]

    for cfg in tracks_configs:
        print(f"\n--- {cfg['name']} ---")
        print(f"  {cfg['description']}")

        parts = [
            IdeaPart(
                name=cfg["name"],
                bars=cfg["bars"],
                scale=cfg["scale"],
                tempo=cfg["tempo"],
                time_signature=cfg["time_signature"],
                progression_type="constrained_hmm",
                progression_list=_PROGRESSIONS.get(cfg["style_hint"]),
                tempo_profile=_PROFILE_MAP.get(cfg["style_hint"]),
            )
        ]

        # Dynamic track selection based on track intent
        track_list = []

        # 1. Foundation
        track_list.append(
            TrackConfig(
                name="Low Strings",
                generator=ContrabassGenerator(),
                instrument="contrabass",
                arrangement="AABB",
                density=0.8 if cfg["style_hint"] == "imperial_industrial" else 0.6,
                octave_shift=-2 if cfg["style_hint"] == "imperial_industrial" else -1,
            )
        )

        # 2. Percussion
        if cfg["style_hint"] == "witcher_combat":
            track_list.append(
                TrackConfig(
                    name="Taiko Drums",
                    generator=TimpaniGenerator(),
                    instrument="taiko",
                    arrangement="ABAB",
                    density=0.8,
                )
            )
        else:
            track_list.append(
                TrackConfig(
                    name="Orchestral Perc",
                    generator=TimpaniGenerator(),
                    instrument="timpani",
                    arrangement="ABAB",
                    density=0.5,
                )
            )

        if cfg["style_hint"] in ["frantic_strings", "witcher_combat"]:
            # Reduced density to fix register masking and blur
            track_list.append(
                TrackConfig(
                    name="Military Snare",
                    generator=SnareDrumGenerator(pattern_type="march"),
                    instrument="drums",
                    arrangement="AABB",
                    density=0.32,
                )
            )

        # 3. Melodic layers
        if cfg["style_hint"] == "lyrical_tragedy":
            track_list.append(
                TrackConfig(
                    name="Solo Cello",
                    generator=CelloGenerator(),
                    instrument="cello",
                    arrangement="ABCD",
                    density=0.5,
                    mpe=True,
                )
            )

        if cfg["style_hint"] == "frantic_strings":
            track_list.append(
                TrackConfig(
                    name="Fast Violins",
                    generator=ViolinGenerator(),
                    instrument="violin",
                    arrangement="AABC",
                    density=0.8,
                )
            )
        else:
            track_list.append(
                TrackConfig(
                    name="Violins Ensemble",
                    generator=ViolinGenerator(),
                    instrument="violin",
                    arrangement="AABC",
                    density=0.6,
                )
            )

        # 4. Brass & Choir
        if cfg["style_hint"] == "imperial_industrial":
            # Reduced density to fix rhythmic blur in low brass
            track_list.append(
                TrackConfig(
                    name="Cimbasso Heavy",
                    generator=BrassSectionGenerator(),
                    instrument="tuba",
                    arrangement="AABB",
                    density=0.5,
                    octave_shift=-1,
                )
            )
            track_list.append(
                TrackConfig(
                    name="Imperial Trombones",
                    generator=TromboneGenerator(),
                    instrument="trombone",
                    arrangement="AABB",
                    density=0.6,
                )
            )
        elif cfg["style_hint"] == "epic_requiem":
            track_list.append(
                TrackConfig(
                    name="Brass Majesty",
                    generator=BrassSectionGenerator(),
                    instrument="brass",
                    arrangement="AABC",
                    density=0.7,
                )
            )
            track_list.append(
                TrackConfig(
                    name="Cathedral Organ",
                    generator=PianoCompGenerator(),
                    instrument="organ",
                    arrangement="AAAA",
                    density=0.5,
                )
            )
        else:
            track_list.append(
                TrackConfig(
                    name="French Horns",
                    generator=FrenchHornGenerator(),
                    instrument="french_horn",
                    arrangement="AABC",
                    density=0.4,
                )
            )

        if cfg["style_hint"] in ["magic_chaos", "epic_requiem"]:
            track_list.append(
                TrackConfig(
                    name="Prophecy Choir",
                    generator=ChoirAahsGenerator(),
                    instrument="choir",
                    arrangement="ABCD",
                    density=0.6,
                    mpe=True,
                )
            )

        # 5. Specialized (Vocals, Industrial)
        if cfg["style_hint"] in ["lyrical_tragedy", "madness_folk"]:
            track_list.append(
                TrackConfig(
                    name="Vocal Lead",
                    generator=MelodyGenerator(
                        phrase_length=8.0,
                        phrase_rest_probability=0.5,
                        ornament_probability=0.4,
                        # Capping range to fix Brightness Overload (C3-C5 range roughly)
                        note_range_low=55,
                        note_range_high=82,
                    ),
                    instrument="voice",
                    arrangement="ABCD",
                    density=0.35,
                    mpe=True,
                )
            )

        if cfg["style_hint"] == "imperial_industrial":
            # Lower density for drones to prevent frequency masking
            track_list.append(
                TrackConfig(
                    name="War Drones",
                    generator=DroneGenerator(),
                    instrument="synth_pad",
                    arrangement="AAAA",
                    density=0.7,
                    octave_shift=-2,
                )
            )
        elif cfg["style_hint"] == "magic_chaos":
            track_list.append(
                TrackConfig(
                    name="Dissonant Magic",
                    generator=DroneGenerator(),
                    instrument="synth_fx",
                    arrangement="ABCD",
                    density=0.6,
                )
            )
            track_list.append(
                TrackConfig(
                    name="Magic Impacts",
                    generator=FXImpactGenerator(),
                    instrument="percussion",
                    arrangement="ABCD",
                    density=0.5,
                )
            )

        # Lead breathing room (ARR-13) + accompaniment thinning (clash/density).
        _accomp = {"Cimbasso Heavy": 0.5, "Brass Majesty": 0.6, "Prophecy Choir": 0.6,
                   "Cathedral Organ": 0.6, "Imperial Trombones": 0.65}
        for _t in track_list:
            if _t.name in ("Fast Violins", "Violins Ensemble", "Vocal Lead"):
                _t.phrase_schedule = _LEAD_REST_SCHEDULE
            _r = _accomp.get(_t.name)
            if _r is not None:
                _t.rhythm_rests = _r

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            time_signature=cfg["time_signature"],
            workflow="generate_all",
            use_tension_curve=True,
            use_voice_leading=True,
            use_texture_control=True,
            use_mixing=True,
            use_mastering=True,
            target_lufs=-12.0,
            parts=parts,
            tracks=track_list,
            use_tempo_modulation=True,  # Enable core tempo modulator
        )

        # Get explicit GM instrument mapping for high-fidelity playback
        from melodica.idea_tool import _GM_PROGRAMS

        instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in track_list}

        # Generate with the tool
        tool = IdeaTool(tool_config)
        notes_dict = tool.generate()

        # Register separation (ARR-10/11 + clash reduction). IdeaTool does NOT
        # apply TrackConfig.modifiers in the generate_all path, so clamp each
        # track's notes to its role band post-generation.
        _mctx = ModifierContext(
            duration_beats=0, chords=[], timeline=None, scale=cfg["scale"], tracks={}
        )
        for _t in track_list:
            _band = _REGISTER_BANDS.get(_t.name)
            if _band is not None and isinstance(notes_dict.get(_t.name), list):
                _mod = LimitNoteRangeModifier(low=_band[0], high=_band[1])
                notes_dict[_t.name] = _mod.modify(notes_dict[_t.name], _mctx)

        # Filter tracks and export
        tracks_data = {
            k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)
        }

        export_multitrack_midi(
            tracks_data,
            str(album_dir / f"{cfg['name']}.mid"),
            bpm=cfg["tempo"],
            instruments=instruments_map,
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set()),
            tempo_events=tool.tempo_events,  # Use core tempo events!
        )

        note_count = sum(len(n) for n in tracks_data.values())
        print(f"    Exported {cfg['name']}.mid ({note_count} notes with native tempo automation)")

    print("\n" + "=" * 80)
    print(f"  ALBUM COMPLETE: Time of Contempt (Tempo Map Edition)")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    with EngineTracer(max_depth=1, use_colors=True):
        generate_witcher_album_tempo_map()
