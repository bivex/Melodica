
# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
dark_textures_v2.py — Надрыв (Nadryv) Dark Textures Generator.

Кинематографический генератор тёмных текстур с акцентом на эмоциональный
«надрыв» — вокальную расщеплённость, фриссон, кульминационные пики и
драматические паузы (цезуры).

9-актовая драматургия:
    1. Тишина (Молчание)    — почти тишина, едва слышный дрон
    2. Сквозняк              — первый звук, как вдох
    3. Туман                 — нарастание диссонансов, полутоновые кластеры
    4. Трещина               — расщепление: хриплые тремоло, глитчи
    5. Надрыв                — кульминация: forte, фрай-тремоло, срывы
    6. Падение               — обвал: цезура, затем тихий отголосок
    7. Пульс                 — механический ритм, индустриальный
    8. Агония                — последний всплеск, гроулинг-бас
    9. Тлен                  — растворение в ничто

Музыкальные концепты:
    - Расщепление (distortion): velocity-спайки, хроматические кластеры
    - Фрай (fry): низкочастотное тремоло с глитчами
    - Гроулинг (growling): сверхнизкий бас с тритоновым движением
    - Фриссон (frisson): неожиданные интервальные скачки
    - Крещендо → Кульминация: экспоненциальный рост плотности
    - Цезура (caesura): драматические паузы
"""

from __future__ import annotations

import math
import random
import argparse
from pathlib import Path
from dataclasses import dataclass, field

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import (
    MelodyGenerator,
    BassGenerator,
    OstinatoGenerator,
    AmbientPadGenerator,
    DyadGenerator,
    TremoloStringsGenerator,
    ChoraleGenerator,
    CountermelodyGenerator,
    GeneratorParams,
)
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.tension import TensionGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.dynamics import DynamicsCurveGenerator
from melodica.generators.hemiola import HemiolaGenerator
from melodica.generators.downbeat_rest import DownbeatRestGenerator
from melodica.generators.transition import TransitionGenerator
from melodica.generators.chord_voicing import ChordVoicingGenerator
from melodica.harmonize import (
    FunctionalHarmonizer,
    ChromaticMediantHarmonizer,
    ModalInterchangeHarmonizer,
    GraphSearchHarmonizer,
)
from melodica.modifiers import (
    HumanizeModifier,
    VelocityScalingModifier,
    CrescendoModifier,
    StaccatoLegatoModifier,
    LimitNoteRangeModifier,
    AddIntervalModifier,
    ModifierContext,
)
from melodica.composer import NonChordToneGenerator, ArticulationEngine
from melodica.rhythm import SmoothRhythmGenerator
from melodica.midi import export_multitrack_midi, GM_INSTRUMENTS
from melodica.render_context import RenderContext
from melodica.utils import nearest_pitch, chord_at


# ---------------------------------------------------------------------------
# Шкалы — тёмная палитра
# ---------------------------------------------------------------------------
DARK_SCALES = {
    "phrygian": Scale(root=0, mode=Mode.PHRYGIAN),
    "harmonic_minor": Scale(root=0, mode=Mode.HARMONIC_MINOR),
    "hungarian_minor": Scale(root=0, mode=Mode.HUNGARIAN_MINOR),
    "diminished": Scale(root=0, mode=Mode.DIMINISHED),
    "persian": Scale(root=0, mode=Mode.PERSIAN),
    "horror_cluster": Scale(root=0, mode=Mode.HORROR_CLUSTER),
    "suspense": Scale(root=0, mode=Mode.SUSPENSE),
    "natural_minor": Scale(root=0, mode=Mode.NATURAL_MINOR),
}


# ---------------------------------------------------------------------------
# Секция
# ---------------------------------------------------------------------------
@dataclass
class Section:
    name: str
    bars: int
    scale_name: str
    key_root: int
    mood: str
    density: float
    tracks: list[str]


def build_sections(total_bars: int) -> list[Section]:
    template = [
        # (name, ratio, scale, key_root, mood, density, tracks)
        ("Тишина", 0.08, "horror_cluster", 0, "silence", 0.08, ["drone", "frisson_stab"]),
        ("Сквозняк", 0.10, "suspense", 0, "breath", 0.20, ["dark_bass", "drone", "dynamics_swell"]),
        (
            "Туман",
            0.14,
            "hungarian_minor",
            0,
            "fog",
            0.40,
            ["dark_pad", "tension", "dark_bass", "tremolo_fry", "dyads"],
        ),
        (
            "Трещина",
            0.12,
            "persian",
            0,
            "crack",
            0.55,
            ["tension_distort", "dark_bass", "hemiola", "tremolo_fry", "frisson_stab"],
        ),
        (
            "Надрыв",
            0.16,
            "hungarian_minor",
            0,
            "nadryv",
            0.80,
            [
                "nadryv_melody",
                "dark_bass_growl",
                "dark_pad",
                "tension_distort",
                "chord_stab",
                "tremolo_fry",
                "frisson_stab",
            ],
        ),
        ("Падение", 0.08, "natural_minor", 5, "fall", 0.15, ["caesura", "dynamics_swell", "drone"]),
        (
            "Пульс",
            0.12,
            "diminished",
            0,
            "pulse",
            0.50,
            ["dark_bass", "ostinato", "dark_pad", "tension"],
        ),
        (
            "Агония",
            0.12,
            "persian",
            0,
            "agony",
            0.65,
            ["nadryv_melody", "dark_bass_growl", "tension_distort", "tremolo_fry", "hemiola"],
        ),
        ("Тлен", 0.08, "horror_cluster", 0, "dissolve", 0.10, ["drone", "dynamics_swell"]),
    ]
    raw = [max(1, round(total_bars * r)) for _, r, *_ in template]
    diff = total_bars - sum(raw)
    raw[-1] = max(1, raw[-1] + diff)
    return [
        Section(n, raw[i], sn, kr, m, d, t) for i, (n, _, sn, kr, m, d, t) in enumerate(template)
    ]


# ---------------------------------------------------------------------------
# Надрыв-генераторы (не входящие в SDK)
# ---------------------------------------------------------------------------


def _render_nadryv_melody(chords, key, duration_beats, density):
    """
    Мелодия надрыва: экспоненциальный crescendo с фрикционными срывами.
    Ноты становятся громче, плотнее и выше по мере приближения к кульминации.
    """
    notes = []
    t = 0.0
    degs = key.degrees()
    if not degs:
        return notes

    climax_point = duration_beats * 0.65  # кульминация на 65%
    prev_pitch = int(degs[0]) + 48

    while t < duration_beats:
        progress = t / max(0.1, duration_beats)
        chord = chord_at(chords, t)
        pcs = chord.pitch_classes()

        # Exponential density — больше нот ближе к кульминации
        note_dur = max(0.25, 2.0 * (1.0 - progress * 0.8))
        if abs(t - climax_point) < duration_beats * 0.15:
            note_dur *= 0.5  # ускорение вблизи кульминации

        # Velocity: crescendo с фрикционными спайками
        base_vel = 30 + int(90 * (progress**1.5))
        if random.random() < 0.2 * progress:
            base_vel = min(127, base_vel + random.randint(15, 30))  # фрай-спайк

        # Pitch: восходящее движение с неожиданными скачками (фриссон)
        if random.random() < 0.15 and progress > 0.3:
            # Фриссон: неожиданный скачок на тритон или септиму
            frisson_intervals = [6, 10, 1, 11]
            interval = random.choice(frisson_intervals)
            pitch = nearest_pitch((prev_pitch + interval) % 12, prev_pitch + interval)
        elif pcs:
            pc = random.choice(pcs) if random.random() > 0.7 else int(random.choice(degs))
            pitch = nearest_pitch(pc, prev_pitch)
        else:
            pitch = prev_pitch

        pitch = max(36, min(96, pitch))
        notes.append(
            NoteInfo(
                pitch=pitch,
                start=round(t, 6),
                duration=round(note_dur * 0.85, 6),
                velocity=max(1, min(127, base_vel)),
            )
        )
        prev_pitch = pitch
        t += note_dur

    return notes


def _render_tremolo_fry(chords, key, duration_beats, density):
    """
    Фрай-тремоло: быстрое тремоло с глитчами и velocity-спайками.
    Имитация расщеплённого вокала через инструмент.
    """
    notes = []
    t = 0.0
    speed = 0.125  # 32-е ноты

    while t < duration_beats:
        chord = chord_at(chords, t)
        pcs = chord.pitch_classes()
        if not pcs:
            t += speed
            continue

        progress = t / max(0.1, duration_beats)
        pitch = nearest_pitch(random.choice(pcs), 48 + int(progress * 24))

        # Глитч: иногда резкий срыв вверх
        if random.random() < 0.08:
            pitch = min(127, pitch + random.choice([1, 6, 11]))  # полутон, тритон, септима

        # Velocity: базовый tremolo + фрай-спайки
        vel = int(40 + 50 * density)
        if random.random() < 0.15:
            vel = min(127, vel + random.randint(20, 40))  # distortion spike

        dur = speed * (0.7 + random.random() * 0.3)
        notes.append(
            NoteInfo(
                pitch=max(0, min(127, pitch)),
                start=round(t, 6),
                duration=round(dur, 6),
                velocity=max(1, min(127, vel)),
            )
        )
        t += speed

    return notes


def _render_tension_distort(chords, key, duration_beats, density):
    """
    Дисторшн-напряжение: кластеры полутонов с хаотичными velocity-спайками.
    Имитация расщеплённого звука.
    """
    notes = []
    t = 0.0
    note_dur = max(0.5, 2.0 - density * 1.5)

    while t < duration_beats:
        chord = chord_at(chords, t)
        pcs = chord.pitch_classes()
        if not pcs:
            t += note_dur
            continue

        # Кластер из 2-3 близких нот
        base_pc = random.choice(pcs)
        base_pitch = nearest_pitch(base_pc, 48)
        cluster_size = random.choice([2, 2, 3])

        for offset in range(cluster_size):
            p = base_pitch + offset
            if p > 96:
                p -= 12
            vel = int(50 * density) + random.randint(-15, 25)
            vel = max(1, min(127, vel))
            notes.append(
                NoteInfo(
                    pitch=max(0, min(127, p)),
                    start=round(t, 6),
                    duration=round(note_dur, 6),
                    velocity=vel,
                )
            )

        t += note_dur

    return notes


def _render_frisson_stab(chords, key, duration_beats, density):
    """
    Фриссон-стаб: редкие, неожиданные аккордовые удары.
    Создаёт эффект «мурашек» через неожиданные интервалы.
    """
    notes = []
    t = 0.0

    while t < duration_beats:
        # Редкие стабы (каждые 4-8 beats)
        gap = 4.0 + random.uniform(0, 4.0)
        t += gap
        if t >= duration_beats:
            break

        chord = chord_at(chords, t)
        pcs = chord.pitch_classes()
        if not pcs:
            continue

        # Фриссон: неожиданный интервал
        frisson_pc = (random.choice(pcs) + random.choice([1, 6, 10, 11])) % 12
        pitch = nearest_pitch(frisson_pc, 60)
        vel = random.randint(70, 110)

        # Двойной стаб: основа + фриссон
        for pc_offset in [0, random.choice([1, 6])]:
            p = nearest_pitch((frisson_pc + pc_offset) % 12, pitch)
            notes.append(
                NoteInfo(
                    pitch=max(0, min(127, p)),
                    start=round(t, 6),
                    duration=round(random.uniform(0.5, 2.0), 6),
                    velocity=max(1, min(127, vel)),
                )
            )

    return notes


def _render_caesura(chords, key, duration_beats, density):
    """
    Цезура: драматическая пауза, затем один тихий отголосок.
    """
    notes = []
    silence_dur = duration_beats * 0.6  # 60% тишины
    chord = chord_at(chords, silence_dur)
    pcs = chord.pitch_classes()
    if not pcs:
        return notes

    # Один тихий отголосок после паузы
    pitch = nearest_pitch(pcs[0], 36)
    notes.append(
        NoteInfo(
            pitch=max(0, min(127, pitch)),
            start=round(silence_dur, 6),
            duration=round(duration_beats - silence_dur, 6),
            velocity=random.randint(15, 30),
        )
    )
    return notes


def _render_dark_bass_growl(chords, key, duration_beats, density):
    """
    Гроулинг-бас: сверхнизкий, утробный рык.
    Тритоновое движение + velocity-спайки.
    """
    notes = []
    t = 0.0
    prev_pitch = 24  # C1

    while t < duration_beats:
        chord = chord_at(chords, t)
        pcs = chord.pitch_classes()
        if not pcs:
            t += 4.0
            continue

        progress = t / max(0.1, duration_beats)

        # Гроулинг: чередование корня и тритона
        if random.random() < 0.3:
            root = (pcs[0] + 6) % 12  # тритон
        else:
            root = pcs[0]

        pitch = nearest_pitch(root, 24)
        pitch = max(12, min(48, pitch))

        # Velocity: утробный рык = низкая, но с гроулинг-спайками
        vel = int(40 + 30 * density)
        if random.random() < 0.2:
            vel = min(127, vel + random.randint(25, 50))

        dur = 4.0 + random.uniform(0, 2.0)
        notes.append(
            NoteInfo(
                pitch=pitch,
                start=round(t, 6),
                duration=round(min(dur, duration_beats - t), 6),
                velocity=max(1, min(127, vel)),
            )
        )
        prev_pitch = pitch
        t += dur

    return notes


def _render_chord_stab(chords, key, duration_beats, density):
    """
    Аккордовый стаб: резкие, громкие удары аккордов (как ударные).
    Синкопированный ритм.
    """
    notes = []
    t = 0.0

    while t < duration_beats:
        chord = chord_at(chords, t)
        pcs = chord.pitch_classes()
        if not pcs:
            t += 1.0
            continue

        # Синкопа: не на долю
        if random.random() < 0.4:
            t += random.choice([0.5, 1.5, 0.75])

        if t >= duration_beats:
            break

        # Аккорд в drop-2 раскладке
        pitches = []
        for i, pc in enumerate(pcs[:4]):
            p = nearest_pitch(pc, 48 + (i % 2) * 12)
            pitches.append(max(0, min(127, p)))

        vel = int(80 * density) + random.randint(0, 30)
        dur = random.uniform(0.2, 0.5)

        for p in pitches:
            notes.append(
                NoteInfo(
                    pitch=p,
                    start=round(t, 6),
                    duration=round(dur, 6),
                    velocity=max(1, min(127, vel)),
                )
            )

        t += 2.0 + random.uniform(0, 2.0)

    return notes


def _render_dynamics_swell(chords, key, duration_beats, density, direction="up"):
    """
    Динамический свелл: crescendo или decrescendo на одном тоне.
    """
    notes = []
    t = 0.0
    chord = chord_at(chords, 0) if chords else None
    pcs = chord.pitch_classes() if chord else [key.root]
    root = nearest_pitch(pcs[0], 36)

    while t < duration_beats:
        progress = t / max(0.1, duration_beats)
        if direction == "up":
            vel = max(10, int(80 * (progress**2)))
        else:
            vel = max(10, int(80 * ((1 - progress) ** 2)))

        dur = max(0.5, duration_beats / 8)
        notes.append(
            NoteInfo(
                pitch=root,
                start=round(t, 6),
                duration=round(dur, 6),
                velocity=vel,
            )
        )
        t += dur

    return notes


# ---------------------------------------------------------------------------
# Пайплайн треков
# ---------------------------------------------------------------------------
TRACK_RENDERERS = {
    "nadryv_melody": _render_nadryv_melody,
    "tremolo_fry": _render_tremolo_fry,
    "tension_distort": _render_tension_distort,
    "frisson_stab": _render_frisson_stab,
    "caesura": _render_caesura,
    "dark_bass_growl": _render_dark_bass_growl,
    "chord_stab": _render_chord_stab,
}


def make_pipeline(track: str, mood: str, density: float, scale: Scale):
    """Возвращает (generator или None, custom_renderer или None, модификаторы)."""
    params = GeneratorParams(density=density)
    mods: list = []
    renderer = None

    # Кастомные рендереры
    if track in TRACK_RENDERERS:

        def _wrap(r=TRACK_RENDERERS[track]):
            return r

        renderer = _wrap()
        return None, renderer, mods

    match track:
        case "drone":
            mode = "tritone_drone" if mood in ("silence", "dissolve") else "minor_pad"
            gen = DarkPadGenerator(
                params=params,
                mode=mode,
                chord_dur=16.0 if mood in ("silence", "dissolve") else 8.0,
                velocity_level=0.12 if mood in ("silence",) else 0.22,
                register="low",
                overlap=0.5,
            )

        case "dark_bass":
            bass_mode = {
                "breath": "doom",
                "fog": "dub",
                "crack": "doom",
                "nadryv": "doom",
                "pulse": "industrial",
                "agony": "doom",
            }.get(mood, "doom")
            gen = DarkBassGenerator(
                params=params,
                mode=bass_mode,
                octave=2,
                note_duration=8.0 if mood in ("breath", "crack") else 4.0,
                velocity_level=0.6,
                movement="tritone_walk" if mood in ("crack", "agony") else "root_only",
            )
            mods.append(LimitNoteRangeModifier(low=24, high=52))

        case "dark_pad":
            pad_mode = {
                "fog": "phrygian_pad",
                "crack": "dim_cluster",
                "nadryv": "dim_cluster",
                "pulse": "minor_pad",
                "agony": "tritone_drone",
            }.get(mood, "minor_pad")
            gen = DarkPadGenerator(
                params=params,
                mode=pad_mode,
                chord_dur=8.0,
                velocity_level=0.35 if mood == "nadryv" else 0.25,
                register="low",
                overlap=0.4,
            )

        case "tension":
            gen = TensionGenerator(
                params=params,
                mode="semitone_cluster",
                note_duration=4.0,
                velocity_level=0.3,
                register="mid",
                density=0.5,
            )

        case "dyads":
            gen = DyadGenerator(
                params=params,
                interval_pref=[1, 6, 10],  # m2, тритон, m7
                motion_mode="contrary",
            )
            mods.append(StaccatoLegatoModifier(amount=0.6))

        case "ostinato":
            gen = OstinatoGenerator(
                params=params,
                pattern="5-1-4-1-3-1-2-1",
                repeat_notes=2,
            )
            mods.append(VelocityScalingModifier(scale=0.75))

        case "dynamics_swell":
            direction = "down" if mood == "dissolve" else "up"

            def _swell(d=direction):
                return lambda chords, key, dur, dens: _render_dynamics_swell(
                    chords, key, dur, dens, direction=d
                )

            renderer = _swell()
            return None, renderer, mods

        case _:
            gen = AmbientPadGenerator(params=params)

    return gen, renderer, mods


# ---------------------------------------------------------------------------
# Гармонизатор
# ---------------------------------------------------------------------------
def pick_harmonizer(mood: str):
    match mood:
        case "silence" | "dissolve":
            return FunctionalHarmonizer(start_with="i", end_with="i")
        case "breath":
            return FunctionalHarmonizer(start_with="i", end_with="i")
        case "fog":
            return ModalInterchangeHarmonizer(borrow_prob=0.4)
        case "crack" | "agony":
            return ChromaticMediantHarmonizer(chromatic_prob=0.4)
        case "nadryv":
            return GraphSearchHarmonizer()
        case "fall":
            return FunctionalHarmonizer(start_with="i", end_with="i")
        case "pulse":
            return GraphSearchHarmonizer()
        case _:
            return FunctionalHarmonizer(start_with="i", end_with="i")


# ---------------------------------------------------------------------------
# Мелодический контур
# ---------------------------------------------------------------------------
def _build_melody_contour(scale, bars, beats_per_bar, density):
    degs = scale.degrees()
    if not degs:
        return [NoteInfo(pitch=36, start=0.0, duration=8.0, velocity=40)]
    notes = []
    t = 0.0
    total = bars * beats_per_bar
    while t < total:
        change = 4.0 if density < 0.3 else 2.0
        dur = min(change, total - t)
        pc = int(degs[0]) if t % (beats_per_bar * 4) == 0 else int(random.choice(degs))
        pitch = max(24, min(60, 36 + pc))
        notes.append(
            NoteInfo(
                pitch=pitch, start=round(t, 6), duration=round(max(1.0, dur - 0.1), 6), velocity=40
            )
        )
        t += dur
    return notes


# ---------------------------------------------------------------------------
# Мастер-микс
# ---------------------------------------------------------------------------
MIX = {
    "drone": 0.85,
    "dark_bass": 0.8,
    "dark_pad": 0.65,
    "tension": 0.45,
    "tremolo_fry": 0.55,
    "dyads": 0.55,
    "ostinato": 0.6,
    "nadryv_melody": 0.9,
    "tension_distort": 0.5,
    "frisson_stab": 0.7,
    "caesura": 0.4,
    "dark_bass_growl": 0.85,
    "chord_stab": 0.8,
    "dynamics_swell": 0.35,
}
_MAX_POLY = 10


def _master_mix(tracks):
    result = {}
    for name, notes in tracks.items():
        level = MIX.get(name, 0.5)
        mixed = []
        for n in notes:
            vel = max(10, min(127, int(n.velocity * level) + random.randint(-3, 3)))
            start = n.start + random.uniform(-0.015, 0.015)
            mixed.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=round(start, 6),
                    duration=n.duration,
                    velocity=vel,
                    articulation=n.articulation,
                    expression=n.expression,
                )
            )
        result[name] = sorted(mixed, key=lambda n: n.start)
    return _limit_poly(result)


def _limit_poly(tracks):
    all_notes = []
    for name, notes in tracks.items():
        for i, n in enumerate(notes):
            all_notes.append((n.start, name, i))
    all_notes.sort()
    grid = {}
    for t, _, _ in all_notes:
        key = int(t * 4)
        grid[key] = grid.get(key, 0) + 1
    peak = max(grid.values()) if grid else 1
    if peak <= _MAX_POLY:
        return tracks
    result = {}
    for name, notes in tracks.items():
        scaled = []
        for n in notes:
            key = int(n.start * 4)
            poly = grid.get(key, 1)
            if poly > _MAX_POLY:
                vel = max(15, int(n.velocity * _MAX_POLY / poly))
            else:
                vel = n.velocity
            scaled.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=vel,
                    articulation=n.articulation,
                    expression=n.expression,
                )
            )
        result[name] = scaled
    return result


# ---------------------------------------------------------------------------
# Главный генератор
# ---------------------------------------------------------------------------
def generate(duration_minutes, tempo, key_root, seed):
    if seed is not None:
        random.seed(seed)

    beats_per_bar = 4
    total_beats = duration_minutes * 60 * (tempo / 60)
    total_bars = max(8, int(round(total_beats / beats_per_bar)))
    sections = build_sections(total_bars)

    tracks = {}
    all_chords = []
    beat_offset = 0.0
    nct = NonChordToneGenerator(passing_prob=0.08, neighbor_prob=0.04)
    art_engine = ArticulationEngine()
    track_contexts = {}
    prev_scale = None

    INST_MAP = {
        "drone": "strings_pad",
        "dark_bass": "cello",
        "dark_pad": "strings_pad",
        "tension": "strings_tremolo",
        "tremolo_fry": "strings_tremolo",
        "dyads": "strings_melody",
        "ostinato": "strings_staccato",
        "nadryv_melody": "strings_melody",
        "tension_distort": "strings_tremolo",
        "frisson_stab": "strings_tremolo",
        "caesura": "cello",
        "dark_bass_growl": "cello",
        "chord_stab": "strings_staccato",
        "dynamics_swell": "strings_pad",
    }

    for si, sec in enumerate(sections):
        s_beats = sec.bars * beats_per_bar
        base = DARK_SCALES[sec.scale_name]
        scale = Scale(root=(sec.key_root + key_root) % 12, mode=base.mode)

        if prev_scale is not None and scale != prev_scale:
            rn = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            print(
                f"  ♩ Модуляция: {rn[prev_scale.root]} {prev_scale.mode.name} "
                f"→ {rn[scale.root]} {scale.mode.name}  [{sec.name}]"
            )
        prev_scale = scale

        harmonizer = pick_harmonizer(sec.mood)
        contour = _build_melody_contour(scale, sec.bars, beats_per_bar, sec.density)
        local_chords = harmonizer.harmonize(contour, scale, s_beats)
        while len(local_chords) < sec.bars:
            local_chords.append(
                local_chords[-1]
                if local_chords
                else ChordLabel(
                    root=int(scale.degrees()[0]) if scale.degrees() else 0,
                    quality=Quality.MINOR,
                    start=round(len(local_chords) * beats_per_bar, 6),
                    duration=beats_per_bar,
                )
            )

        for c in local_chords:
            all_chords.append(
                ChordLabel(
                    root=c.root,
                    quality=c.quality,
                    start=round(c.start + beat_offset, 6),
                    duration=c.duration,
                    degree=c.degree,
                )
            )

        phrase_pos = si / max(1, len(sections) - 1)

        for track_name in sec.tracks:
            gen, renderer, mods = make_pipeline(track_name, sec.mood, sec.density, scale)

            prev_ctx = track_contexts.get(track_name)
            if prev_ctx is None:
                ctx = RenderContext(phrase_position=phrase_pos, current_scale=scale)
            else:
                ctx = RenderContext(
                    prev_pitch=prev_ctx.prev_pitch,
                    prev_velocity=prev_ctx.prev_velocity,
                    prev_chord=prev_ctx.prev_chord,
                    prev_pitches=list(prev_ctx.prev_pitches),
                    phrase_position=phrase_pos,
                    current_scale=scale,
                )

            if renderer:
                notes = renderer(local_chords, scale, s_beats, sec.density)
            else:
                notes = gen.render(local_chords, scale, s_beats, ctx)
                if hasattr(gen, "_last_context") and gen._last_context is not None:
                    track_contexts[track_name] = gen._last_context

            mctx = ModifierContext(
                duration_beats=s_beats,
                chords=local_chords,
                timeline=None,
                scale=scale,
            )
            for m in mods:
                try:
                    notes = m.modify(notes, mctx)
                except Exception:
                    pass

            if track_name not in tracks:
                tracks[track_name] = []
            for n in notes:
                tracks[track_name].append(
                    NoteInfo(
                        pitch=n.pitch,
                        start=round(n.start + beat_offset, 6),
                        duration=n.duration,
                        velocity=n.velocity,
                        articulation=n.articulation,
                        expression=n.expression,
                    )
                )

        beat_offset += s_beats

    for k in tracks:
        tracks[k] = sorted(tracks[k], key=lambda n: n.start)

    pedal_cc = {}
    for tn in list(tracks.keys()):
        inst = INST_MAP.get(tn, "strings_pad")
        tracks[tn] = art_engine.apply(tracks[tn], inst, beat_offset)
        raw = art_engine.add_sustain_pedal_events(tracks[tn], beat_offset)
        if raw:
            pedal_cc[tn] = [(e["time"], 64, e["value"]) for e in raw]

    tracks = _master_mix(tracks)
    return tracks, pedal_cc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="Dark Textures V2 — Надрыв")
    p.add_argument("--duration", type=float, default=3.0)
    p.add_argument("--tempo", type=int, default=60)
    p.add_argument("--key", type=int, default=0)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--output", type=str, default="dark_textures_v2.mid")
    args = p.parse_args()

    duration = max(1.0, min(30.0, args.duration))
    bars = int(round(duration * 60 * (args.tempo / 60) / 4))
    actual = bars * 4 / args.tempo * 60
    key_name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"][args.key]

    print(f"Dark Textures V2 — Надрыв")
    print(f"  {duration:.1f} min → {actual / 60:.1f} min actual ({bars} bars @ {args.tempo} BPM)")
    print(f"  Key: {key_name}")
    print()

    tracks, pedal_cc = generate(duration, args.tempo, args.key, args.seed)

    total = sum(len(n) for n in tracks.values())
    print(f"  Tracks: {len(tracks)}, Notes: {total}")
    for name, notes in sorted(tracks.items()):
        print(f"    {name:20s}: {len(notes):5d} notes")

    export_multitrack_midi(
        tracks, args.output, bpm=args.tempo, key=f"{key_name}m", cc_events=pedal_cc
    )
    print(f"\n  → {args.output} ({Path(args.output).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
