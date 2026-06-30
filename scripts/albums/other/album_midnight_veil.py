# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/other/album_midnight_veil.py
    — "Midnight Veil" (Покров полуночи)

Пятичастный цикл в A натуральном миноре.  Четыре голоса, каждый из которых
несёт свою функцию в ансамбле:

    Lead     — скрипка (MelodyGenerator):   сольная мелодия, «голос».
    Counter  — виолончель (CounterpointGenerator): нижний контрапункт.
    Pad      — легато-струнные (StringsLegatoGenerator): harmonic bed,
               фактура, задаёт плотность секции.
    Bass     — контрабас (BassGenerator):  якорь гармонии, окрашивает
               функцию каждого аккорда.

Пять движений — пять состояний ночи:

    I.   Dusk          — Сумерки.     54 BPM, 4/4, 32 такта.
         AABA, мелодия нисходящая, динамика pp→mp.
         Скрипка вступает одна, виолончель входит на B-части.

    II.  Restless      — Беспокойство. 80 BPM, 3/4, 36 тактов.
         ABAB, синкопы, виолончель в контрдвижении, bass walking.
         Центральный конфликт цикла.

    III. The Witching Hour — Апогей.  92 BPM, 4/4, 40 тактов.
         AABB, высокая плотность, тремоло вместо легато.
         Драматическая вершина — fortissimo, register climb.

    IV.  Before Dawn   — Истощение.   58 BPM, 4/4, 32 такта.
         A A' A (вариация), мелодия разреженная, нисходящие контуры.
         Бас уходит в root_only, pad — pianissimo.

    V.   First Light   — Разрешение.  66 BPM, 4/4, 40 тактов.
         A B A C A (рондо), восходящий контур, climax='up_5th',
         финальный унисон скрипки и виолончели.

Все части используют coupled_hmm для прогрессии аккордов.
ARR-12 / ARR-13 исправляются через postprocess_arr=True.
"""

from pathlib import Path

from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

from melodica.generators.melody import MelodyGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.bass import BassGenerator


# ---------------------------------------------------------------------------
# Тональность — A натуральный минор (ля, ноябрь, ночь).
# ---------------------------------------------------------------------------
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)


# ---------------------------------------------------------------------------
# Аранжировочные блоки по движениям
# ---------------------------------------------------------------------------

def _tracks_dusk():
    """I. Dusk — Сумерки. Скрипка + виолончель-контрапункт + легато + бас."""
    return [
        # Основная мелодия: нисходящий контур (новый параметр!), тихое начало.
        TrackConfig(
            name="Lead_Violin",
            generator=MelodyGenerator(
                direction_bias=-0.25,
                phrase_contour="descent",          # ← новый контур
                phrase_length=8.0,
                drama_shape="swell",               # ← новая форма
                motif_probability=0.55,
                after_leap="step_opposite",
                note_range_low=64,
                note_range_high=86,
                ornament_probability=0.08,
                penultimate_step_above=True,
            ),
            instrument="violin",
            density=0.48,
            mpe=True,
            phrase_schedule=structure_to_schedule("A A B A", 8),
        ),
        # Контрапункт: contrary motion, предпочтение терциям и секстам.
        TrackConfig(
            name="Counter_Cello",
            generator=CounterpointGenerator(
                species=3,
                interval_preference="thirds_sixths",  # ← новый параметр
                motion="contrary",                    # ← новый параметр
                voice_crossing=False,                 # ← новый параметр
            ),
            instrument="cello",
            depends_on="Lead_Violin",
            density=0.30,
            mpe=True,
        ),
        # Harmonic bed: тихий pad, pianissimo через dynamic_base.
        TrackConfig(
            name="Strings_Pad",
            generator=StringsLegatoGenerator(
                dynamic_curve="crescendo",     # ← новый параметр
                dynamic_base=38,               # ← новый параметр: pp
            ),
            instrument="strings",
            density=0.35,
        ),
        # Бас: только корень.
        TrackConfig(
            name="Bass_CB",
            generator=BassGenerator(style="root_only"),
            instrument="contrabass",
            density=0.32,
            octave_shift=-1,
        ),
    ]


def _tracks_restless():
    """II. Restless — Беспокойство. 3/4, zigzag, bass walking."""
    return [
        TrackConfig(
            name="Lead_Violin",
            generator=MelodyGenerator(
                direction_bias=0.0,
                phrase_contour="zigzag",       # ← новый контур
                phrase_length=6.0,
                syncopation=0.30,
                rhythm_variety=0.55,
                drama_shape="tension_release",
                motif_probability=0.40,
                after_leap="step_opposite",
                note_range_low=65,
                note_range_high=88,
                allow_2nd=True,
            ),
            instrument="violin",
            density=0.55,
            mpe=True,
            phrase_schedule=structure_to_schedule("A B A B", 9),
        ),
        TrackConfig(
            name="Counter_Cello",
            generator=CounterpointGenerator(
                species=3,
                interval_preference="sixths",  # ← открытые сексты
                motion="contrary",
                voice_crossing=False,
            ),
            instrument="cello",
            depends_on="Lead_Violin",
            density=0.45,
            mpe=True,
        ),
        TrackConfig(
            name="Strings_Pad",
            generator=StringsLegatoGenerator(
                dynamic_curve="cresc_dim",
                dynamic_base=48,
            ),
            instrument="strings",
            density=0.40,
        ),
        # Walking bass — главный носитель ритма в этом движении.
        TrackConfig(
            name="Bass_CB",
            generator=BassGenerator(style="walking"),
            instrument="contrabass",
            density=0.65,
            octave_shift=-1,
        ),
    ]


def _tracks_witching_hour():
    """III. The Witching Hour — Апогей. Тремоло fortissimo, педальный бас."""
    return [
        TrackConfig(
            name="Lead_Violin",
            generator=MelodyGenerator(
                direction_bias=0.40,
                phrase_contour="rise",
                phrase_length=8.0,
                climax="up_5th",
                drama_shape="epic",
                motif_probability=0.50,
                after_leap="step_opposite",
                note_range_low=67,
                note_range_high=91,
                ornament_probability=0.12,
            ),
            instrument="violin",
            density=0.65,
            mpe=True,
            phrase_schedule=structure_to_schedule("A A B B", 10),
        ),
        TrackConfig(
            name="Counter_Cello",
            generator=CounterpointGenerator(
                species=3,
                interval_preference="sixths",
                motion="contrary",
                voice_crossing=False,
            ),
            instrument="cello",
            depends_on="Lead_Violin",
            density=0.60,
            mpe=True,
        ),
        # Тремоло вместо легато — жёсткая фактура апогея.
        TrackConfig(
            name="Tremolo_Pad",
            generator=TremoloStringsGenerator(
                variant="chord",
                tremolo_speed="fast",          # ← новый параметр
                dynamic_curve="fortissimo",    # ← новый параметр
                dynamic_swell=True,
            ),
            instrument="strings",
            density=0.70,
        ),
        # Педальный бас — держит тонику под всей бурей.
        TrackConfig(
            name="Bass_CB",
            generator=BassGenerator(style="pedal_tone"),  # ← новый стиль
            instrument="contrabass",
            density=0.75,
            octave_shift=-1,
        ),
    ]


def _tracks_before_dawn():
    """IV. Before Dawn — Истощение. Descent, diminuendo, root_only."""
    return [
        TrackConfig(
            name="Lead_Violin",
            generator=MelodyGenerator(
                direction_bias=-0.40,
                phrase_contour="descent",      # ← новый контур
                phrase_length=12.0,
                drama_shape="diminuendo",      # ← новая форма
                motif_probability=0.25,
                after_leap="step_opposite",
                note_range_low=60,
                note_range_high=79,
                ornament_probability=0.03,
            ),
            instrument="violin",
            density=0.28,
            mpe=True,
            phrase_schedule=structure_to_schedule("A A' A", 10),
        ),
        TrackConfig(
            name="Counter_Cello",
            generator=CounterpointGenerator(
                species=2,
                interval_preference="thirds_sixths",
                motion="oblique",              # ← один голос неподвижен
                voice_crossing=False,
            ),
            instrument="cello",
            depends_on="Lead_Violin",
            density=0.22,
            mpe=True,
        ),
        TrackConfig(
            name="Strings_Pad",
            generator=StringsLegatoGenerator(
                dynamic_curve="diminuendo",    # ← синоним для dynamic_shape
                dynamic_base=30,               # ← явный pianissimo
            ),
            instrument="strings",
            density=0.28,
        ),
        TrackConfig(
            name="Bass_CB",
            generator=BassGenerator(style="root_only"),
            instrument="contrabass",
            density=0.25,
            octave_shift=-1,
        ),
    ]


def _tracks_first_light():
    """V. First Light — Разрешение. Рондо, восходящий контур, chord_tone bass."""
    return [
        TrackConfig(
            name="Lead_Violin",
            generator=MelodyGenerator(
                direction_bias=0.35,
                phrase_contour="rise",
                phrase_length=8.0,
                climax="up_5th",
                drama_shape="epic",
                motif_probability=0.50,
                penultimate_step_above=True,
                after_leap="step_opposite",
                note_range_low=64,
                note_range_high=88,
                ornament_probability=0.10,
            ),
            instrument="violin",
            density=0.55,
            mpe=True,
            phrase_schedule=structure_to_schedule("A B A C A", 8),
        ),
        # Параллельное движение = единство голосов в финале.
        TrackConfig(
            name="Counter_Cello",
            generator=CounterpointGenerator(
                species=3,
                interval_preference="thirds_sixths",
                motion="parallel",             # ← унисон/терции = катарсис
                voice_crossing=False,
            ),
            instrument="cello",
            depends_on="Lead_Violin",
            density=0.50,
            mpe=True,
        ),
        TrackConfig(
            name="Strings_Pad",
            generator=StringsLegatoGenerator(
                dynamic_curve="crescendo",
                dynamic_base=55,
            ),
            instrument="strings",
            density=0.55,
        ),
        # Chord-tone bass — гармонически богатый финал.
        TrackConfig(
            name="Bass_CB",
            generator=BassGenerator(style="chord_tone"),  # ← новый стиль
            instrument="contrabass",
            density=0.50,
            octave_shift=-1,
        ),
    ]


# ---------------------------------------------------------------------------
# Таблица движений
# ---------------------------------------------------------------------------

MOVEMENTS = [
    # (name,              bpm, ts,   bars, section_title,        build_fn)
    ("01_Dusk",           54,  (4,4), 32,  "Сумерки",            _tracks_dusk),
    ("02_Restless",       80,  (3,4), 36,  "Беспокойство",       _tracks_restless),
    ("03_Witching_Hour",  92,  (4,4), 40,  "Полночь",            _tracks_witching_hour),
    ("04_Before_Dawn",    58,  (4,4), 32,  "Перед рассветом",    _tracks_before_dawn),
    ("05_First_Light",    66,  (4,4), 40,  "Первый свет",        _tracks_first_light),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_midnight_veil():
    album_dir = Path("output/album_midnight_veil")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 72)
    print("  M I D N I G H T   V E I L   —   П О К Р О В   П О Л У Н О Ч И")
    print("  A Natural Minor  ·  4 voices  ·  5 movements")
    print("=" * 72)

    total_notes = 0

    for name, bpm, ts, bars, title, build_fn in MOVEMENTS:
        print(f"\n── {name}  [{title}, A minor, {ts[0]}/{ts[1]}, {bpm} BPM, {bars} bars] ──")

        track_list = build_fn()

        instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in track_list}

        parts = [IdeaPart(
            name=name,
            bars=bars,
            scale=A_MINOR,
            tempo=bpm,
            time_signature=ts,
            progression_type="coupled_hmm",
        )]

        config = IdeaToolConfig(
            style="cinematic_hybrid",
            time_signature=ts,
            tempo=bpm,
            scale=A_MINOR,
            use_tension_curve=True,
            use_harmonic_verifier=True,
            use_texture_control=True,
            use_non_chord_tones=True,
            parts=parts,
            tracks=track_list,
        )

        notes_dict = IdeaTool(config).generate()

        tracks_data = {
            k: v for k, v in notes_dict.items()
            if not k.startswith("_") and isinstance(v, list)
        }

        out_path = album_dir / f"{name}.mid"
        export_multitrack_midi(
            tracks_data,
            str(out_path),
            bpm=bpm,
            key=A_MINOR,
            time_sig=ts,
            instruments=instruments_map,
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set()),
            postprocess_arr=True,
        )

        n = sum(len(v) for v in tracks_data.values())
        total_notes += n

        chords = notes_dict.get("_chords") or []
        if chords:
            NOTE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            prog = " → ".join(
                f"{NOTE[c.root % 12]}{c.quality.name[:3]}"
                for c in chords[:8]
            )
            ellipsis = " ..." if len(chords) > 8 else ""
            print(f"    Harmony:  {prog}{ellipsis}")

        print(f"    Notes:    {n}  |  Exported: {out_path.name}")

    print("\n" + "=" * 72)
    print("  COMPLETE: MIDNIGHT VEIL")
    print(f"  {len(MOVEMENTS)} movements  ·  {total_notes} total notes")
    print(f"  Tonal centre: A natural minor throughout")
    print(f"  Arc: stillness → unrest → climax → exhaustion → dawn")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    generate_midnight_veil()
