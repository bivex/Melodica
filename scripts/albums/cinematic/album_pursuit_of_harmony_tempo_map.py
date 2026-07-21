# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/cinematic/album_pursuit_of_harmony_tempo_map.py — "Погоня за
гармонией (Dynamic Tempo Map Edition)": a 7-movement cinematic suite tracing a
search for harmonic resolution across the modal-brightness axis. Each movement
steps from the most unstable mode (Locrian, diminished tonic — harmony
perpetually out of reach) to the most consonant (Ionian — harmony finally found).
Cadences tighten as the suite advances: avoidance → Phrygian descent → exotic
detour → deceptive resolution → Dorian lift → Mixolydian openness → definitive
I–vi–IV–ii–V–I. Uses the core Melodica TempoModulator profiles (chaotic,
agitato, madness, rubato, combat, industrial, requiem) — one per movement,
written as native MIDI tempo automation.

Refinement pass — "virtuosic playing, non-dry transitions":
  * Progressions enriched to 6 chords each with applied dominants (V7),
    secondary chords (vi / ii7 / VImaj7) and a full I–vi–IV–ii–V–I arrival, so
    harmony breathes instead of block-cadencing one bar at a time.
  * Leads play legato with vibrato, swell dynamics, double-stops and raised
    ornament density — agile, expressive lines.
  * A post-generation non-chord-tone pass (passing/neighbor tones) glues the
    chord-to-chord transitions on melodic voices (use_non_chord_tones is inert
    in the generate_all path, so it is applied explicitly here).
Bar-aware: per-track time signatures via BarGrid (5/4, 6/8, 7/8, 3/4, 4/4).
"""

import dataclasses
import random
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
from melodica.types import Scale, Mode, BarGrid

# Role-based register bands (low, high MIDI). Same orchestration strategy as the
# Witcher suite: isolate ONE sub-bass voice (clears low-end mud) and lift leads
# above the mid cluster (clears register crossings). Mid-range sections (horn /
# brass / choir / organ) deliberately overlap — that's correct voicing; clamping
# them apart would destroy the sound and concentrate notes into worse clashes.
# Notes outside a band are octave-shifted into it.
_REGISTER_BANDS: dict[str, tuple[int, int]] = {
    "Sub Bass": (24, 40),          # sole sub-bass voice
    "Tension Pad": (40, 55),       # low drone, below the mid cluster
    "Timpani": (40, 60),
    "Solo Cello": (48, 67),        # tenor
    "French Horn": (48, 64),       # tenor
    "Piano": (48, 84),             # wide-range comp
    "Choir": (52, 70),             # mid
    "Brass Section": (52, 74),     # mid
    "Cathedral Organ": (55, 79),   # mid
    "Vocal Lead": (55, 82),        # mid-high lead
    "Anxious Violins": (74, 96),   # high — above the mid cluster
    "Violins": (74, 96),           # high
    "Bright Violins": (74, 96),    # high
}

# Periodic rest for melodic leads so a line never runs 100+ beats without
# breathing room. Tiles play/rest across the whole part.
_LEAD_REST_SCHEDULE = PhraseSchedule(
    slots=[PhraseSlot(kind="play", bars=8), PhraseSlot(kind="rest", bars=1)],
    loop=True,
)

# Hand-authored functional progressions per movement ("master's voice"). Used as
# constraints for constrained_hmm: the HMM still fits each track's melody contour
# and voice-leading, but anchors to these chords + durations — replacing the
# generic statistical progressions from plain coupled_hmm. Each chord = 1 bar
# (duration = time_signature numerator beats). Roman numerals are relative to
# each movement's scale (parse_progression / Scale.parse_roman) and are DIATONIC
# to each mode. Six chords per movement give the harmony room to breathe and let
# applied dominants / secondary chords smooth the cadences (non-dry transitions).
_PROGRESSIONS: dict[str, list[str]] = {
    # Locrian: diminished tonic — harmony perpetually out of reach. Restless
    # wandering via bVI and applied colour; never cadences onto I.
    "disquiet":         ["Idim:5.0", "V:5.0",     "VI:5.0",     "II:5.0",    "IV:5.0",     "Idim:5.0"],
    # Phrygian: descending slip with a V applied-dominant pulling back to Im.
    "fleeing_shadow":   ["Im:6.0",   "VII:6.0",   "VI:6.0",     "II:6.0",    "V:6.0",      "Im:6.0"],
    # Hungarian minor: augmented-fourth wrinkle with a parallel-colour return.
    "crooked_path":     ["Im:7.0",   "IVaug:7.0", "VII:7.0",    "II:7.0",    "IVaug:7.0",  "Im:7.0"],
    # Aeolian: V7 applied dominant sets up a deceptive resolution to VI (false dawn).
    "false_dawn":       ["Im9:3.0",  "IVm9:3.0",  "V7:3.0",     "VImaj9:3.0","IIImaj7:3.0","VI:3.0"],
    # Dorian: raised-sixth lift coloured by VImaj7 before returning.
    "lifting_gaze":     ["Im9:6.0",  "IVmaj9:6.0","VII:6.0",    "IIImaj7:6.0","VImaj7:6.0","IVmaj9:6.0"],
    # Mixolydian: flat-7 walk with a V→IV bluesy approach back to the tonic.
    "open_horizon":     ["I:4.0",    "VII:4.0",   "IV:4.0",     "I:4.0",     "V:4.0",      "IV:4.0"],
    # Ionian: full I–vi–IV–ii–V–I — the smoothest cadence, harmony found.
    "harmony_found":    ["Imaj9:4.0","vi:4.0",    "IVmaj9:4.0", "ii7:4.0",   "V7:4.0",     "Imaj9:4.0"],
}

# Mapping each movement to a core TempoModulator profile (one per movement).
# The arc mirrors the modal progression: unstable unrest → driving chase →
# erratic detour → breathed lyricism → struggle-toward-light → open road →
# solemn fading arrival. Emits native MIDI tempo automation per track.
_PROFILE_MAP = {
    "disquiet":       "chaotic",    # unstable swings + jitter — unrest
    "fleeing_shadow": "agitato",    # gallop + build + ritard — the chase
    "crooked_path":   "madness",    # erratic cyclic swings — the twisted detour
    "false_dawn":     "rubato",     # breathed push/pull — deceptive lyricism
    "lifting_gaze":   "combat",     # build + breather + climax — rising toward light
    "open_horizon":   "industrial", # mechanical drive — open-road momentum
    "harmony_found":  "requiem",    # solemn breathing + fading outro ritard — arrival
}


def _tile_chords(progression_list, scale, total_beats):
    """Tile a progression_list (["Im9:4.0", ...]) into absolute-timed
    ChordLabels covering total_beats — for post-generation non-chord-tone
    smoothing (the NCT matcher keys on chord.start <= note.start)."""
    parsed = []
    for _item in (progression_list or []):
        _name, _, _dur = _item.partition(":")
        try:
            _d = float(_dur) if _dur else 4.0
        except ValueError:
            _d = 4.0
        try:
            parsed.append((scale.parse_roman(_name.strip()), _d))
        except Exception:
            continue
    if not parsed:
        return []
    _cycle = sum(_d for _, _d in parsed)
    if _cycle <= 0:
        return []
    _chords, _t = [], 0.0
    while _t < total_beats:
        for _c, _d in parsed:
            _chords.append(dataclasses.replace(_c, start=_t, duration=_d))
            _t += _d
            if _t >= total_beats:
                break
    return _chords


# Names of the melodic lead voices that receive passing/neighbor tones.
_NCT_LEADS = ("Anxious Violins", "Violins", "Bright Violins", "Solo Cello", "Vocal Lead")

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
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.snare_drum import SnareDrumGenerator
from melodica.generators.piano_comp import PianoCompGenerator


def generate_pursuit_album_tempo_map():
    album_dir = Path("output/album_pursuit_of_harmony_tempo_map")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        П О Г О Н Я   З А   Г А Р М О Н И Е Й  (TEMPO MAP EDITION)")
    print("        Pursuit of Harmony — a modal-brightness suite")
    print("=" * 80)

    # 7-movement arc: Locrian -> Ionian (dissonance converging on consonance).
    tracks_configs = [
        {
            "name": "01_The_Disquiet",
            "tempo": 96,
            "scale": Scale(root=2, mode=Mode.LOCRIAN),
            "bars": 56,
            "description": "Unrest. Diminished tonic — harmony perpetually out of reach.",
            "style_hint": "disquiet",
            "progression_type": "coupled_hmm",
            "time_signature": (5, 4),
        },
        {
            "name": "02_Fleeing_Shadow",
            "tempo": 132,
            "scale": Scale(root=2, mode=Mode.PHRYGIAN),
            "bars": 64,
            "description": "The chase. Descending Phrygian — the cadence slips away.",
            "style_hint": "fleeing_shadow",
            "progression_type": "coupled_hmm",
            "time_signature": (6, 8),
        },
        {
            "name": "03_The_Crooked_Path",
            "tempo": 104,
            "scale": Scale(root=4, mode=Mode.HUNGARIAN_MINOR),
            "bars": 56,
            "description": "Detour. Hungarian-minor augmented fourths twist the pursuit.",
            "style_hint": "crooked_path",
            "progression_type": "coupled_hmm",
            "time_signature": (7, 8),
        },
        {
            "name": "04_False_Dawn",
            "tempo": 72,
            "scale": Scale(root=2, mode=Mode.AEOLIAN),
            "bars": 48,
            "description": "Deceptive cadence to VI — a resolution that isn't.",
            "style_hint": "false_dawn",
            "progression_type": "coupled_hmm",
            "time_signature": (3, 4),
        },
        {
            "name": "05_The_Lifting_Gaze",
            "tempo": 88,
            "scale": Scale(root=2, mode=Mode.DORIAN),
            "bars": 64,
            "description": "Hope. The raised sixth lifts the line toward consonance.",
            "style_hint": "lifting_gaze",
            "progression_type": "coupled_hmm",
            "time_signature": (6, 8),
        },
        {
            "name": "06_Open_Horizon",
            "tempo": 120,
            "scale": Scale(root=7, mode=Mode.MIXOLYDIAN),
            "bars": 64,
            "description": "Clarity. Flat-seven openness — the tonic finally returns.",
            "style_hint": "open_horizon",
            "progression_type": "coupled_hmm",
            "time_signature": (4, 4),
        },
        {
            "name": "07_Harmony_Found",
            "tempo": 60,
            "scale": Scale(root=0, mode=Mode.IONIAN),
            "bars": 56,
            "description": "Arrival. Definitive I–vi–IV–ii–V–I — the pursuit ends in consonance.",
            "style_hint": "harmony_found",
            "progression_type": "coupled_hmm",
            "time_signature": (4, 4),
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

        hint = cfg["style_hint"]
        track_list = []

        # 1. Foundation — single sub-bass voice (darker where there's no resolution)
        track_list.append(
            TrackConfig(
                name="Sub Bass",
                generator=ContrabassGenerator(),
                instrument="contrabass",
                arrangement="AABB",
                density=0.7 if hint == "disquiet" else 0.6,
                octave_shift=-2 if hint == "disquiet" else -1,
            )
        )

        # 2. Percussion
        track_list.append(
            TrackConfig(
                name="Timpani",
                generator=TimpaniGenerator(),
                instrument="timpani",
                arrangement="ABAB",
                density=0.55 if hint in ("disquiet", "fleeing_shadow") else 0.45,
            )
        )
        if hint in ("fleeing_shadow", "open_horizon"):
            # Driving march under the chase / the open road
            track_list.append(
                TrackConfig(
                    name="Military Snare",
                    generator=SnareDrumGenerator(pattern_type="march"),
                    instrument="drums",
                    arrangement="AABB",
                    density=0.32,
                )
            )

        # 3. Melodic layers — strings brighten as the suite advances; leads
        #    play legato with vibrato + swell dynamics for expressive, agile lines.
        if hint == "disquiet":
            violins_name = "Anxious Violins"
            violins_curve = "crescendo"   # building tension
        elif hint in ("open_horizon", "harmony_found"):
            violins_name = "Bright Violins"
            violins_curve = "swell"
        else:
            violins_name = "Violins"
            violins_curve = "swell"
        track_list.append(
            TrackConfig(
                name=violins_name,
                generator=ViolinGenerator(
                    articulation="legato",
                    vibrato=True,
                    dynamic_curve=violins_curve,
                    note_density=1.2,       # more active, virtuosic line
                    double_stops=True,      # richer, double-stop passages
                ),
                instrument="violin",
                arrangement="AABC",
                density=0.55 if hint == "disquiet" else 0.6,
            )
        )

        if hint in ("false_dawn", "lifting_gaze", "crooked_path"):
            track_list.append(
                TrackConfig(
                    name="Solo Cello",
                    generator=CelloGenerator(
                        articulation="legato",
                        vibrato=True,
                        dynamic_curve="swell",
                        double_stops=True,
                    ),
                    instrument="cello",
                    arrangement="ABCD",
                    density=0.5,
                    mpe=True,
                )
            )

        # 4. Brass & keys — entering gradually, fullest at the arrival
        if hint in ("open_horizon", "harmony_found"):
            track_list.append(
                TrackConfig(
                    name="Brass Section",
                    generator=BrassSectionGenerator(),
                    instrument="brass",
                    arrangement="AABC",
                    density=0.65,
                )
            )
        elif hint in ("crooked_path", "false_dawn", "lifting_gaze"):
            track_list.append(
                TrackConfig(
                    name="French Horn",
                    generator=FrenchHornGenerator(),
                    instrument="french_horn",
                    arrangement="AABC",
                    density=0.4,
                )
            )

        if hint == "crooked_path":
            # Piano lays bare the harmonic twist the HMM is steering through
            track_list.append(
                TrackConfig(
                    name="Piano",
                    generator=PianoCompGenerator(),
                    instrument="piano",
                    arrangement="AAAA",
                    density=0.45,
                )
            )
        elif hint == "harmony_found":
            track_list.append(
                TrackConfig(
                    name="Cathedral Organ",
                    generator=PianoCompGenerator(),
                    instrument="organ",
                    arrangement="AAAA",
                    density=0.5,
                )
            )

        if hint in ("false_dawn", "harmony_found"):
            track_list.append(
                TrackConfig(
                    name="Choir",
                    generator=ChoirAahsGenerator(),
                    instrument="choir",
                    arrangement="ABCD",
                    density=0.6,
                    mpe=True,
                )
            )

        # 5. Specialized — dissonant pad for unrest, vocal for the two poles
        if hint == "disquiet":
            track_list.append(
                TrackConfig(
                    name="Tension Pad",
                    generator=DroneGenerator(),
                    instrument="dark_pad",
                    arrangement="AAAA",
                    density=0.65,
                    octave_shift=-2,
                )
            )

        if hint in ("false_dawn", "harmony_found"):
            track_list.append(
                TrackConfig(
                    name="Vocal Lead",
                    generator=MelodyGenerator(
                        phrase_length=6.0,            # shorter → more agile phrasing
                        phrase_rest_probability=0.45,
                        ornament_probability=0.5,     # denser grace notes
                        note_range_low=55,
                        note_range_high=82,
                    ),
                    instrument="voice",
                    arrangement="ABCD",
                    density=0.35,
                    mpe=True,
                )
            )

        # Lead breathing room + accompaniment thinning (clash/density reduction).
        _accomp = {"Brass Section": 0.6, "Choir": 0.6, "Cathedral Organ": 0.6,
                   "French Horn": 0.5, "Tension Pad": 0.55}
        for _t in track_list:
            if _t.name in ("Anxious Violins", "Violins", "Bright Violins", "Vocal Lead"):
                _t.phrase_schedule = _LEAD_REST_SCHEDULE
            _r = _accomp.get(_t.name)
            if _r is not None:
                _t.rhythm_rests = _r

        from melodica.composer.chord_enrichers import applied_dominant_enricher

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            time_signature=cfg["time_signature"],
            workflow="generate_melody_then_harmonize",
            use_tension_curve=True,
            use_voice_leading=True,
            use_texture_control=True,
            use_non_chord_tones=True,     # intent flag (applied explicitly below)
            use_mixing=True,
            use_mastering=True,
            target_lufs=-12.0,
            use_polyphony_coordinator=True,
            progression_enrichers=[applied_dominant_enricher],
            parts=parts,
            tracks=track_list,
            use_tempo_modulation=True,  # Enable core tempo modulator
        )

        # Explicit GM instrument mapping for high-fidelity playback
        from melodica.idea_tool import _GM_PROGRAMS

        instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in track_list}

        # Generate with the tool
        tool = IdeaTool(tool_config)
        notes_dict = tool.generate()

        # Register separation. IdeaTool does NOT apply TrackConfig.modifiers in
        # the generate_all path, so clamp each track's notes to its role band
        # post-generation.
        _mctx = ModifierContext(
            duration_beats=0, chords=[], timeline=None, scale=cfg["scale"], tracks={}
        )
        for _t in track_list:
            _band = _REGISTER_BANDS.get(_t.name)
            if _band is not None and isinstance(notes_dict.get(_t.name), list):
                _mod = LimitNoteRangeModifier(low=_band[0], high=_band[1])
                notes_dict[_t.name] = _mod.modify(notes_dict[_t.name], _mctx)

        # Non-chord-tone smoothing on melodic leads — passing/neighbor tones
        # glue the chord-to-chord transitions (non-dry cadences). use_non_chord_
        # tones is inert in generate_all, so apply it explicitly here.
        from melodica._postprocess import apply_non_chord_tones

        _total_beats = cfg["bars"] * cfg["time_signature"][0]
        _chords_tiled = _tile_chords(
            _PROGRESSIONS.get(cfg["style_hint"]), cfg["scale"], _total_beats
        )
        for _t in track_list:
            if _t.name in _NCT_LEADS and isinstance(notes_dict.get(_t.name), list):
                notes_dict[_t.name] = apply_non_chord_tones(
                    notes_dict[_t.name], _t, _chords_tiled, cfg["scale"]
                )

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
    print(f"  ALBUM COMPLETE: Pursuit of Harmony (Tempo Map Edition)")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    with EngineTracer(max_depth=1, use_colors=True):
        generate_pursuit_album_tempo_map()
