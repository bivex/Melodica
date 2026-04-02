
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
nadryv_10min.py — 10-минутная аранжировка «Надрыв».

Полная HMM3-гармонизация с прогрессиями, переходами и драматургическим
арком. Каждая секция имеет свой mood, шкалу, плотность и набор треков.

Гармонизатор: HMM3Harmonizer с настроенными весами per-section.
Прогрессии: beam-search через диатонические + secondary dominants + extensions.
Переходы: shared-chord pivots между модуляциями.

Драматургия (150 bars @ 60 BPM = 10 min):
    1. Тишина (8 bars)          — pp, drone
    2. Дыхание (12 bars)        — p, первый бас
    3. Туман (16 bars)          — mp, текстуры
    4. Скитание (16 bars)       — mp, мелодия входит
    5. Тревога (16 bars)        — mf, напряжение
    6. Надрыв (20 bars)         — f, кульминация
    7. Падение (10 bars)        — mp→p, обвал
    8. Пульс (14 bars)          — mf, механика
    9. Агония (18 bars)         — f, последний всплеск
    10. Тлен (20 bars)          — pp, растворение
"""

from __future__ import annotations

import math
import random
import argparse
from pathlib import Path
from dataclasses import dataclass

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import (
    MelodyGenerator,
    MarkovMelodyGenerator,
    BassGenerator,
    ChordGenerator,
    OstinatoGenerator,
    AmbientPadGenerator,
    DyadGenerator,
    ArpeggiatorGenerator,
    TremoloStringsGenerator,
    ChoraleGenerator,
    CountermelodyGenerator,
    CallResponseGenerator,
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
from melodica.generators.swing import SwingGenerator
from melodica.generators.section_builder import SectionBuilderGenerator
from melodica.harmonize import (
    HMM3Harmonizer,
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
# Шкалы
# ---------------------------------------------------------------------------
SCALES = {
    "phrygian": Scale(root=0, mode=Mode.PHRYGIAN),
    "harmonic_minor": Scale(root=0, mode=Mode.HARMONIC_MINOR),
    "hungarian_minor": Scale(root=0, mode=Mode.HUNGARIAN_MINOR),
    "diminished": Scale(root=0, mode=Mode.DIMINISHED),
    "persian": Scale(root=0, mode=Mode.PERSIAN),
    "horror_cluster": Scale(root=0, mode=Mode.HORROR_CLUSTER),
    "suspense": Scale(root=0, mode=Mode.SUSPENSE),
    "natural_minor": Scale(root=0, mode=Mode.NATURAL_MINOR),
    "dorian": Scale(root=0, mode=Mode.DORIAN),
    "byzantine": Scale(root=0, mode=Mode.BYZANTINE),
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
    """
    10-актовая драматургия с HMM3-гармонизацией.

    Модуляционная схема:
        C → C → C → D → Eb → C → Ab → C → C# → C
    """
    template = [
        ("Тишина", 0.053, "horror_cluster", 0, "silence", 0.10, ["drone"]),
        ("Дыхание", 0.080, "suspense", 0, "breath", 0.22, ["dark_bass", "drone", "dynamics_up"]),
        (
            "Туман",
            0.107,
            "hungarian_minor",
            0,
            "fog",
            0.40,
            ["dark_pad", "tension", "dark_bass", "tremolo", "arp"],
        ),
        (
            "Скитание",
            0.107,
            "dorian",
            2,
            "wander",
            0.50,
            ["melody", "dark_bass", "dark_pad", "arp", "dyads"],
        ),
        (
            "Тревога",
            0.107,
            "phrygian",
            3,
            "anxiety",
            0.55,
            ["melody", "tension_distort", "dark_bass", "ostinato", "tremolo", "dyads"],
        ),
        (
            "Надрыв",
            0.133,
            "hungarian_minor",
            0,
            "nadryv",
            0.80,
            [
                "melody",
                "melody2",
                "dark_bass_growl",
                "dark_pad",
                "tension_distort",
                "chord_stab",
                "tremolo",
                "arp",
            ],
        ),
        (
            "Падение",
            0.067,
            "natural_minor",
            8,
            "fall",
            0.20,
            ["caesura", "dynamics_down", "drone", "call_response"],
        ),
        (
            "Пульс",
            0.093,
            "diminished",
            0,
            "pulse",
            0.55,
            ["dark_bass", "ostinato", "dark_pad", "tension", "swing"],
        ),
        (
            "Агония",
            0.120,
            "persian",
            1,
            "agony",
            0.65,
            ["melody", "dark_bass_growl", "tension_distort", "tremolo", "hemiola"],
        ),
        ("Тлен", 0.133, "horror_cluster", 0, "dissolve", 0.10, ["drone", "dynamics_down"]),
    ]
    raw = [max(1, round(total_bars * r)) for _, r, *_ in template]
    # Fix rounding: give/take from last section
    diff = total_bars - sum(raw)
    raw[-1] = max(1, raw[-1] + diff)
    return [
        Section(n, raw[i], sn, kr, m, d, t) for i, (n, _, sn, kr, m, d, t) in enumerate(template)
    ]


# ---------------------------------------------------------------------------
# HMM3 гармонизатор per mood
# ---------------------------------------------------------------------------
def make_harmonizer(mood: str) -> HMM3Harmonizer:
    """Создаёт HMM3Harmonizer с настроенными весами для mood."""
    match mood:
        case "silence" | "dissolve":
            return HMM3Harmonizer(
                beam_width=3,
                melody_weight=0.15,
                functional_weight=0.25,
                cadence_weight=0.20,
                secondary_dom_weight=0.05,
                repetition_penalty=0.05,
                phrase_length=4,
                chord_change="bars",
            )
        case "breath" | "fall":
            return HMM3Harmonizer(
                beam_width=4,
                melody_weight=0.20,
                functional_weight=0.20,
                cadence_weight=0.18,
                secondary_dom_weight=0.08,
                phrase_length=4,
                chord_change="bars",
            )
        case "fog" | "wander":
            return HMM3Harmonizer(
                beam_width=5,
                melody_weight=0.25,
                transition_weight=0.20,
                functional_weight=0.15,
                cadence_weight=0.12,
                secondary_dom_weight=0.10,
                allow_extensions=True,
                allow_secondary_dom=True,
                phrase_length=4,
                chord_change="bars",
            )
        case "anxiety":
            return HMM3Harmonizer(
                beam_width=5,
                melody_weight=0.30,
                transition_weight=0.15,
                functional_weight=0.10,
                cadence_weight=0.08,
                secondary_dom_weight=0.12,
                repetition_penalty=0.15,
                allow_extensions=True,
                allow_secondary_dom=True,
                phrase_length=4,
                chord_change="bars",
            )
        case "nadryv":
            return HMM3Harmonizer(
                beam_width=6,
                melody_weight=0.30,
                transition_weight=0.18,
                functional_weight=0.12,
                cadence_weight=0.10,
                secondary_dom_weight=0.12,
                extension_weight=0.08,
                repetition_penalty=0.12,
                allow_extensions=True,
                allow_secondary_dom=True,
                phrase_length=2,
                chord_change="strong_beats",
            )
        case "pulse":
            return HMM3Harmonizer(
                beam_width=5,
                melody_weight=0.20,
                transition_weight=0.22,
                functional_weight=0.18,
                cadence_weight=0.15,
                secondary_dom_weight=0.10,
                allow_extensions=True,
                allow_secondary_dom=True,
                phrase_length=4,
                chord_change="bars",
            )
        case "agony":
            return HMM3Harmonizer(
                beam_width=6,
                melody_weight=0.28,
                transition_weight=0.15,
                functional_weight=0.10,
                cadence_weight=0.08,
                secondary_dom_weight=0.15,
                extension_weight=0.08,
                repetition_penalty=0.18,
                allow_extensions=True,
                allow_secondary_dom=True,
                phrase_length=2,
                chord_change="strong_beats",
            )
        case _:
            return HMM3Harmonizer()


# ---------------------------------------------------------------------------
# Мелодический контур
# ---------------------------------------------------------------------------
def _build_melody_contour(scale, bars, beats_per_bar, density, mood):
    """Строит мелодический контур для гармонизатора."""
    degs = scale.degrees()
    if not degs:
        return [NoteInfo(pitch=48, start=0.0, duration=4.0, velocity=60)]

    notes = []
    t = 0.0
    total = bars * beats_per_bar
    prev_pitch = int(degs[0]) + 48

    # Настройки по mood
    if mood in ("silence", "dissolve"):
        change_every = 8.0
        vel_base = 30
    elif mood in ("breath", "fall"):
        change_every = 4.0
        vel_base = 45
    elif mood in ("nadryv", "agony"):
        change_every = 1.0
        vel_base = 70
    elif mood in ("anxiety",):
        change_every = 2.0
        vel_base = 60
    else:
        change_every = 2.0 if density > 0.3 else 4.0
        vel_base = int(40 + 40 * density)

    while t < total:
        dur = min(change_every, total - t)

        # На сильных долях — тоника или аккордовая нота
        strong_beat = t % (beats_per_bar * 4) == 0
        if strong_beat or random.random() < 0.4:
            pc = int(degs[0])
        else:
            pc = int(random.choice(degs))

        pitch = nearest_pitch(pc, prev_pitch)
        pitch = max(24, min(84, pitch))

        # Фриссон-скачки в агонии
        if mood in ("agony", "nadryv") and random.random() < 0.15:
            pitch = max(24, min(84, pitch + random.choice([-6, -1, 1, 6])))

        vel = vel_base + random.randint(-10, 10)
        vel = max(20, min(100, vel))

        notes.append(
            NoteInfo(
                pitch=pitch,
                start=round(t, 6),
                duration=round(max(0.5, dur - 0.1), 6),
                velocity=vel,
            )
        )
        prev_pitch = pitch
        t += dur

    return notes


# ---------------------------------------------------------------------------
# Кастомные рендереры
# ---------------------------------------------------------------------------
def _render_nadryv_melody(chords, key, dur, dens, mood):
    notes = []
    t = 0.0
    degs = key.degrees()
    if not degs:
        return notes
    climax = dur * 0.6
    prev = int(degs[0]) + 48

    while t < dur:
        progress = t / max(0.1, dur)
        note_dur = max(0.25, 2.0 * (1.0 - progress * 0.85))
        if abs(t - climax) < dur * 0.15:
            note_dur *= 0.4

        vel = 35 + int(85 * (progress**1.3))
        if random.random() < 0.2 * progress:
            vel = min(127, vel + random.randint(15, 30))

        chord = chord_at(chords, t)
        pcs = chord.pitch_classes()
        if random.random() < 0.12 and progress > 0.25:
            pitch = prev + random.choice([1, 6, 10, 11])
        elif pcs:
            pc = random.choice(pcs) if random.random() > 0.6 else int(random.choice(degs))
            pitch = nearest_pitch(pc, prev)
        else:
            pitch = prev

        pitch = max(36, min(96, pitch))
        notes.append(
            NoteInfo(
                pitch=pitch,
                start=round(t, 6),
                duration=round(note_dur * 0.85, 6),
                velocity=max(1, min(127, vel)),
            )
        )
        prev = pitch
        t += note_dur
    return notes


def _render_tension_distort(chords, key, dur, dens, mood):
    notes = []
    t = 0.0
    nd = max(0.5, 2.0 - dens * 1.5)
    while t < dur:
        chord = chord_at(chords, t)
        pcs = chord.pitch_classes()
        if not pcs:
            t += nd
            continue
        base = nearest_pitch(random.choice(pcs), 48)
        for off in range(random.choice([2, 2, 3])):
            p = base + off
            if p > 96:
                p -= 12
            vel = int(50 * dens) + random.randint(-15, 25)
            notes.append(
                NoteInfo(
                    pitch=max(0, min(127, p)),
                    start=round(t, 6),
                    duration=round(nd, 6),
                    velocity=max(1, min(127, vel)),
                )
            )
        t += nd
    return notes


def _render_frisson_stab(chords, key, dur, dens, mood):
    notes = []
    t = 0.0
    while t < dur:
        t += 4.0 + random.uniform(0, 4.0)
        if t >= dur:
            break
        chord = chord_at(chords, t)
        pcs = chord.pitch_classes()
        if not pcs:
            continue
        fpc = (random.choice(pcs) + random.choice([1, 6, 10])) % 12
        pitch = nearest_pitch(fpc, 60)
        vel = random.randint(70, 110)
        for off in [0, random.choice([1, 6])]:
            p = nearest_pitch((fpc + off) % 12, pitch)
            notes.append(
                NoteInfo(
                    pitch=max(0, min(127, p)),
                    start=round(t, 6),
                    duration=round(random.uniform(0.5, 2.0), 6),
                    velocity=max(1, min(127, vel)),
                )
            )
    return notes


def _render_caesura(chords, key, dur, dens, mood):
    notes = []
    silence = dur * 0.6
    chord = chord_at(chords, silence)
    pcs = chord.pitch_classes()
    if not pcs:
        return notes
    notes.append(
        NoteInfo(
            pitch=max(0, min(127, nearest_pitch(pcs[0], 36))),
            start=round(silence, 6),
            duration=round(dur - silence, 6),
            velocity=random.randint(15, 28),
        )
    )
    return notes


def _render_dark_bass_growl(chords, key, dur, dens, mood):
    notes = []
    t = 0.0
    while t < dur:
        chord = chord_at(chords, t)
        pcs = chord.pitch_classes()
        if not pcs:
            t += 4.0
            continue
        root = (pcs[0] + 6) % 12 if random.random() < 0.3 else pcs[0]
        pitch = max(12, min(48, nearest_pitch(root, 24)))
        vel = int(40 + 30 * dens)
        if random.random() < 0.2:
            vel = min(127, vel + random.randint(25, 50))
        d = 4.0 + random.uniform(0, 2.0)
        notes.append(
            NoteInfo(
                pitch=pitch,
                start=round(t, 6),
                duration=round(min(d, dur - t), 6),
                velocity=max(1, min(127, vel)),
            )
        )
        t += d
    return notes


def _render_chord_stab(chords, key, dur, dens, mood):
    notes = []
    t = 0.0
    while t < dur:
        chord = chord_at(chords, t)
        pcs = chord.pitch_classes()
        if not pcs:
            t += 1.0
            continue
        if random.random() < 0.4:
            t += random.choice([0.5, 1.5])
        if t >= dur:
            break
        pitches = [nearest_pitch(pc, 48 + (i % 2) * 12) for i, pc in enumerate(pcs[:4])]
        vel = int(80 * dens) + random.randint(0, 30)
        nd = random.uniform(0.2, 0.5)
        for p in pitches:
            notes.append(
                NoteInfo(
                    pitch=max(0, min(127, p)),
                    start=round(t, 6),
                    duration=round(nd, 6),
                    velocity=max(1, min(127, vel)),
                )
            )
        t += 2.0 + random.uniform(0, 2.0)
    return notes


def _render_tremolo_fry(chords, key, dur, dens, mood):
    notes = []
    t = 0.0
    speed = 0.125
    while t < dur:
        chord = chord_at(chords, t)
        pcs = chord.pitch_classes()
        if not pcs:
            t += speed
            continue
        progress = t / max(0.1, dur)
        pitch = nearest_pitch(random.choice(pcs), 48 + int(progress * 24))
        if random.random() < 0.08:
            pitch = min(127, pitch + random.choice([1, 6, 11]))
        vel = int(40 + 50 * dens)
        if random.random() < 0.15:
            vel = min(127, vel + random.randint(20, 40))
        notes.append(
            NoteInfo(
                pitch=max(0, min(127, pitch)),
                start=round(t, 6),
                duration=round(speed * (0.7 + random.random() * 0.3), 6),
                velocity=max(1, min(127, vel)),
            )
        )
        t += speed
    return notes


def _render_dynamics(chords, key, dur, dens, mood, direction="up"):
    notes = []
    t = 0.0
    chord = chord_at(chords, 0) if chords else None
    pcs = chord.pitch_classes() if chord else [key.root]
    root = nearest_pitch(pcs[0], 36)
    while t < dur:
        progress = t / max(0.1, dur)
        if direction == "up":
            vel = max(10, int(80 * (progress**2)))
        else:
            vel = max(10, int(80 * ((1 - progress) ** 2)))
        nd = max(0.5, dur / 8)
        notes.append(NoteInfo(pitch=root, start=round(t, 6), duration=round(nd, 6), velocity=vel))
        t += nd
    return notes


CUSTOM_RENDERERS = {
    "nadryv_melody": lambda mood: lambda c, k, d, dn: _render_nadryv_melody(c, k, d, dn, mood),
    "tension_distort": lambda mood: lambda c, k, d, dn: _render_tension_distort(c, k, d, dn, mood),
    "frisson_stab": lambda mood: lambda c, k, d, dn: _render_frisson_stab(c, k, d, dn, mood),
    "caesura": lambda mood: lambda c, k, d, dn: _render_caesura(c, k, d, dn, mood),
    "dark_bass_growl": lambda mood: lambda c, k, d, dn: _render_dark_bass_growl(c, k, d, dn, mood),
    "chord_stab": lambda mood: lambda c, k, d, dn: _render_chord_stab(c, k, d, dn, mood),
    "tremolo": lambda mood: lambda c, k, d, dn: _render_tremolo_fry(c, k, d, dn, mood),
    "dynamics_up": lambda mood: lambda c, k, d, dn: _render_dynamics(c, k, d, dn, mood, "up"),
    "dynamics_down": lambda mood: lambda c, k, d, dn: _render_dynamics(c, k, d, dn, mood, "down"),
}


# ---------------------------------------------------------------------------
# Трековый пайплайн
# ---------------------------------------------------------------------------
def make_pipeline(track, mood, density, scale):
    params = GeneratorParams(density=density)
    mods = []
    renderer = None

    if track in CUSTOM_RENDERERS:
        return None, CUSTOM_RENDERERS[track](mood), mods

    match track:
        case "drone":
            gen = DarkPadGenerator(
                params=params,
                mode="tritone_drone" if mood in ("silence",) else "minor_pad",
                chord_dur=16.0 if mood in ("silence", "dissolve") else 8.0,
                velocity_level=0.12 if mood == "silence" else 0.22,
                register="low",
                overlap=0.5,
            )

        case "dark_bass":
            bm = {
                "breath": "doom",
                "fog": "dub",
                "wander": "doom",
                "anxiety": "doom",
                "pulse": "industrial",
            }.get(mood, "doom")
            gen = DarkBassGenerator(
                params=params,
                mode=bm,
                octave=2,
                note_duration=8.0 if mood in ("breath",) else 4.0,
                velocity_level=0.6,
                movement="tritone_walk" if mood in ("anxiety",) else "root_only",
            )
            mods.append(LimitNoteRangeModifier(low=24, high=52))

        case "dark_pad":
            pm = {
                "fog": "phrygian_pad",
                "wander": "minor_pad",
                "anxiety": "dim_cluster",
                "nadryv": "dim_cluster",
                "pulse": "minor_pad",
                "agony": "tritone_drone",
            }.get(mood, "minor_pad")
            gen = DarkPadGenerator(
                params=params,
                mode=pm,
                chord_dur=8.0,
                velocity_level=0.35 if mood in ("nadryv", "agony") else 0.25,
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

        case "melody":
            gen = MelodyGenerator(
                params=params,
                harmony_note_probability=0.7,
                note_range_low=55,
                note_range_high=84,
                note_repetition_probability=0.1,
                steps_probability=0.85,
            )
            mods.append(HumanizeModifier(timing_std=0.03, velocity_std=5))
            if mood == "nadryv":
                mods.append(AddIntervalModifier(semitones=7, direction="below"))
            elif mood == "agony":
                mods.append(CrescendoModifier(start_vel=40, end_vel=110))

        case "melody2":
            gen = MarkovMelodyGenerator(
                params=params,
                harmony_note_probability=0.6,
                note_range_low=48,
                note_range_high=72,
                note_repetition_probability=0.08,
            )
            mods.append(VelocityScalingModifier(scale=0.75))

        case "arp":
            gen = ArpeggiatorGenerator(
                params=params,
                pattern="up_down" if mood in ("fog", "wander") else "octave_pump",
                note_duration=0.25,
                octaves=2,
                voicing="spread",
            )
            mods.append(VelocityScalingModifier(scale=0.65))

        case "dyads":
            gen = DyadGenerator(
                params=params,
                interval_pref=[1, 6, 10],
                motion_mode="contrary" if mood in ("fog", "wander") else "parallel",
            )
            mods.append(StaccatoLegatoModifier(amount=0.7))

        case "ostinato":
            gen = OstinatoGenerator(
                params=params,
                pattern="5-1-4-1-3-1-2-1",
                repeat_notes=2 if mood in ("anxiety", "pulse") else 1,
            )

        case "swing":
            gen = SwingGenerator(
                params=params,
                swing_ratio=0.62,
                subdivision=0.5,
                pitch_strategy="chord_tone",
                accent_pattern="backbeat",
            )

        case "hemiola":
            gen = HemiolaGenerator(
                params=params,
                pattern="3_over_4",
                pitch_strategy="chord_tone",
                velocity_accent=1.1,
            )
            mods.append(VelocityScalingModifier(scale=0.7))

        case "call_response":
            gen = CallResponseGenerator(
                params=params,
                call_length=2.0,
                response_length=2.0,
                call_direction="down",
                response_direction="up",
            )

        case "downbeat_rest":
            gen = DownbeatRestGenerator(
                params=params,
                mode="caesura",
                caesura_length=1.5,
                subdivision=1.0,
                pitch_strategy="chord_tone",
            )

        case _:
            gen = AmbientPadGenerator(params=params)

    return gen, renderer, mods


# ---------------------------------------------------------------------------
# Мастер-микс
# ---------------------------------------------------------------------------
MIX = {
    "drone": 0.85,
    "dark_bass": 0.8,
    "dark_pad": 0.65,
    "tension": 0.45,
    "tension_distort": 0.5,
    "tremolo": 0.55,
    "dyads": 0.55,
    "ostinato": 0.6,
    "arp": 0.55,
    "melody": 0.9,
    "melody2": 0.7,
    "nadryv_melody": 0.9,
    "frisson_stab": 0.7,
    "caesura": 0.4,
    "dark_bass_growl": 0.85,
    "chord_stab": 0.8,
    "dynamics_up": 0.35,
    "dynamics_down": 0.35,
    "swing": 0.6,
    "hemiola": 0.55,
    "call_response": 0.6,
    "downbeat_rest": 0.55,
}
_MAX_POLY = 12


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
    all_n = []
    for name, notes in tracks.items():
        for i, n in enumerate(notes):
            all_n.append((n.start, name, i))
    all_n.sort()
    grid = {}
    for t, _, _ in all_n:
        k = int(t * 4)
        grid[k] = grid.get(k, 0) + 1
    peak = max(grid.values()) if grid else 1
    if peak <= _MAX_POLY:
        return tracks
    result = {}
    for name, notes in tracks.items():
        scaled = []
        for n in notes:
            k = int(n.start * 4)
            poly = grid.get(k, 1)
            vel = max(15, int(n.velocity * _MAX_POLY / poly)) if poly > _MAX_POLY else n.velocity
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

    INST = {
        "drone": "strings_pad",
        "dark_bass": "cello",
        "dark_pad": "strings_pad",
        "tension": "strings_tremolo",
        "tension_distort": "strings_tremolo",
        "tremolo": "strings_tremolo",
        "dyads": "strings_melody",
        "ostinato": "strings_staccato",
        "arp": "harp",
        "melody": "strings_melody",
        "melody2": "strings_melody",
        "nadryv_melody": "strings_melody",
        "dark_bass_growl": "cello",
        "chord_stab": "strings_staccato",
        "frisson_stab": "strings_tremolo",
        "caesura": "cello",
        "dynamics_up": "strings_pad",
        "dynamics_down": "strings_pad",
        "swing": "strings_staccato",
        "hemiola": "strings_melody",
        "call_response": "strings_melody",
        "downbeat_rest": "strings_melody",
    }

    for si, sec in enumerate(sections):
        s_beats = sec.bars * beats_per_bar
        base = SCALES[sec.scale_name]
        scale = Scale(root=(sec.key_root + key_root) % 12, mode=base.mode)

        if prev_scale is not None and scale != prev_scale:
            rn = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            print(
                f"  ♩ {rn[prev_scale.root]} {prev_scale.mode.name} "
                f"→ {rn[scale.root]} {scale.mode.name}  [{sec.name}]"
            )
        prev_scale = scale

        # HMM3 гармонизация
        harmonizer = make_harmonizer(sec.mood)
        contour = _build_melody_contour(scale, sec.bars, beats_per_bar, sec.density, sec.mood)
        local_chords = harmonizer.harmonize(contour, scale, s_beats)

        # Паддинг если не хватает аккордов
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

        # Переходный аккорд: последний аккорд секции → первый аккорд следующей
        # уже обеспечивается HMM3 через beam search
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
            ctx = RenderContext(
                prev_pitch=prev_ctx.prev_pitch if prev_ctx else None,
                prev_velocity=prev_ctx.prev_velocity if prev_ctx else None,
                prev_chord=prev_ctx.prev_chord if prev_ctx else None,
                prev_pitches=list(prev_ctx.prev_pitches) if prev_ctx else [],
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

            if track_name in ("melody", "dyads", "arp"):
                try:
                    notes = nct.add_non_chord_tones(notes, local_chords, scale)
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
        inst = INST.get(tn, "strings_pad")
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
    p = argparse.ArgumentParser(description="Надрыв — 10 min HMM3 arrangement")
    p.add_argument("--duration", type=float, default=10.0)
    p.add_argument("--tempo", type=int, default=60)
    p.add_argument("--key", type=int, default=0)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--output", type=str, default="nadryv_10min.mid")
    args = p.parse_args()

    duration = max(1.0, min(30.0, args.duration))
    bars = int(round(duration * 60 * (args.tempo / 60) / 4))
    actual = bars * 4 / args.tempo * 60
    key_name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"][args.key]

    print(f"Надрыв — 10 min HMM3 arrangement")
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
