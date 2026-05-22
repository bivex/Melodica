# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/film_score.py -- Meta-generator for film scoring.

Produces orchestral arrangements synchronized to dramatic hit points
and emotional arcs. Generates per-instrument tracks with mood-appropriate
texture, articulation, and dynamics.

Layer: Application / Domain (meta-generator)
Style: Cinematic, film scoring, orchestral underscore.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale


# ---------------------------------------------------------------------------
# Texture levels (shared with orchestral_score)
# ---------------------------------------------------------------------------

class Texture:
    SOLO = "solo"
    CHAMBER = "chamber"
    SMALL_ENSEMBLE = "small"
    FULL = "full"
    THIN = "thin"


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

@dataclass
class HitPoint:
    """A dramatic event in the film timeline."""
    beat: float
    event_type: str   # "action", "tension", "emotion", "reveal", "impact", "calm"
    intensity: float  # 0.0-1.0
    label: str = ""


@dataclass
class EmotionalArc:
    """Defines emotional trajectory over a time range."""
    start_beat: float
    end_beat: float
    start_mood: str   # "calm", "tense", "dark", "heroic", "mysterious", "joyful", "sad"
    end_mood: str
    curve: str = "linear"  # "linear", "exponential", "sudden_shift"


# ---------------------------------------------------------------------------
# Mood → musical parameter mapping
# ---------------------------------------------------------------------------

_MOOD_PARAMS = {
    "calm": {
        "texture": Texture.THIN,
        "articulation": "legato",
        "register": 1,
        "vel_range": (40, 60),
        "dynamic_curve": "flat",
    },
    "tense": {
        "texture": Texture.CHAMBER,
        "articulation": "tremolo",
        "register": 3,
        "vel_range": (60, 85),
        "dynamic_curve": "crescendo",
    },
    "dark": {
        "texture": Texture.CHAMBER,
        "articulation": "sustained",
        "register": 1,
        "vel_range": (50, 70),
        "dynamic_curve": "flat",
    },
    "heroic": {
        "texture": Texture.FULL,
        "articulation": "fanfare",
        "register": 3,
        "vel_range": (80, 110),
        "dynamic_curve": "crescendo",
    },
    "mysterious": {
        "texture": Texture.SMALL_ENSEMBLE,
        "articulation": "pizzicato",
        "register": 2,
        "vel_range": (45, 65),
        "dynamic_curve": "swell",
    },
    "joyful": {
        "texture": Texture.SMALL_ENSEMBLE,
        "articulation": "legato",
        "register": 3,
        "vel_range": (70, 90),
        "dynamic_curve": "flat",
    },
    "sad": {
        "texture": Texture.CHAMBER,
        "articulation": "sustained",
        "register": 1,
        "vel_range": (40, 65),
        "dynamic_curve": "diminuendo",
    },
    "neutral": {
        "texture": Texture.CHAMBER,
        "articulation": "sustained",
        "register": 2,
        "vel_range": (55, 75),
        "dynamic_curve": "flat",
    },
}

# GM program numbers and stage pan (same as orchestral_score.py)
_GM = {
    "violin": 40, "viola": 41, "cello": 42, "contrabass": 43,
    "flute": 73, "oboe": 68, "clarinet": 71, "bassoon": 70,
    "french_horn": 60, "trumpet": 56, "trombone": 57, "tuba": 58,
    "choir_aahs": 52, "choir_oohs": 53,
    "harp": 46, "timpani": 47, "orchestral_hit": 55,
    "string_ensemble": 48, "brass_section": 61,
}

_STAGE_PAN = {
    "violin": -0.30, "viola": -0.10, "cello": 0.15, "contrabass": 0.25,
    "flute": -0.20, "oboe": -0.05, "clarinet": 0.05, "bassoon": 0.20,
    "french_horn": 0.30, "trumpet": -0.15, "trombone": 0.10, "tuba": 0.20,
    "choir_aahs": 0.0, "choir_oohs": 0.0,
    "harp": -0.35, "timpani": 0.00,
}

# Active voices per texture level
_TEXTURE_VOICES = {
    Texture.THIN: [
        ("violin", "melody"),
        ("cello", "bass"),
    ],
    Texture.SOLO: [
        ("violin", "melody"),
    ],
    Texture.CHAMBER: [
        ("violin", "melody"),
        ("cello", "bass"),
        ("viola", "harmony"),
    ],
    Texture.SMALL_ENSEMBLE: [
        ("violin", "melody"),
        ("viola", "harmony"),
        ("cello", "bass"),
        ("contrabass", "bass"),
        ("flute", "countermelody"),
        ("harp", "pad"),
    ],
    Texture.FULL: [
        ("violin", "melody"),
        ("viola", "harmony"),
        ("cello", "bass"),
        ("contrabass", "bass"),
        ("flute", "countermelody"),
        ("oboe", "countermelody"),
        ("clarinet", "harmony"),
        ("bassoon", "bass"),
        ("french_horn", "pad"),
        ("trumpet", "melody"),
        ("trombone", "harmony"),
        ("choir_aahs", "pad"),
        ("harp", "pad"),
    ],
}

# Voice overrides per hit-point event type
_HIT_VOICES = {
    "action": ["trumpet", "trombone", "timpani", "violin", "cello"],
    "tension": ["violin", "viola", "cello", "french_horn"],
    "emotion": ["violin", "cello", "flute"],
    "reveal": ["violin", "flute", "oboe", "choir_aahs"],
    "impact": ["trumpet", "trombone", "french_horn", "timpani", "violin",
               "viola", "cello", "contrabass"],
    "calm": ["violin", "harp", "flute"],
}


# ---------------------------------------------------------------------------
# Segment data
# ---------------------------------------------------------------------------

@dataclass
class _Segment:
    start: float
    end: float
    mood: str
    texture: str
    articulation: str
    register: int
    vel_range: tuple[int, int]
    dynamic_curve: str
    hit_point: HitPoint | None = None


# ---------------------------------------------------------------------------
# Film Score Generator
# ---------------------------------------------------------------------------

class FilmScoreGenerator(PhraseGenerator):
    """
    Meta-generator for film scoring that produces orchestral arrangements
    synchronized to dramatic cues (hit points) and emotional arcs.

    Populates self.tracks, self.instruments, and self.pan_map after render(),
    identical to OrchestralScoreGenerator.
    """

    name: str = "Film Score"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        hit_points: list[HitPoint] | None = None,
        emotional_arcs: list[EmotionalArc] | None = None,
        default_mood: str = "neutral",
        include_choir: bool = True,
        include_brass: bool = True,
        include_harp: bool = True,
    ) -> None:
        super().__init__(params)
        self.hit_points = hit_points or []
        self.emotional_arcs = emotional_arcs or []
        self.default_mood = default_mood
        self.include_choir = include_choir
        self.include_brass = include_brass
        self.include_harp = include_harp
        self.tracks: dict[str, list[NoteInfo]] = {}
        self.instruments: dict[str, int] = {}
        self.pan_map: dict[str, float] = {}
        self._last_context = None

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        self.tracks = {}
        self.instruments = {}
        self.pan_map = {}

        segments = self._build_segments(duration_beats)

        for seg in segments:
            seg_chords = self._chords_in_range(chords, seg.start, seg.end - seg.start)
            if not seg_chords:
                continue

            voices = self._voices_for_segment(seg)
            for inst_name, role in voices:
                if inst_name == "choir_aahs" and not self.include_choir:
                    continue
                if inst_name == "harp" and not self.include_harp:
                    continue
                if inst_name in ("french_horn", "trumpet", "trombone") and not self.include_brass:
                    continue

                gen = self._make_generator(inst_name, role, seg)
                if gen is None:
                    continue

                seg_notes = gen.render(seg_chords, key, seg.end - seg.start)
                for n in seg_notes:
                    n.shift_time(seg.start)
                self._accumulate(inst_name, seg_notes)

            # Add hit-point accent notes at exact beat position
            if seg.hit_point is not None:
                accent_notes = self._hit_accent(seg.hit_point, chords, key, seg)
                for n in accent_notes:
                    self._accumulate("_accent", [n])

        # Combine all notes for return value
        all_notes: list[NoteInfo] = []
        for track_notes in self.tracks.values():
            all_notes.extend(track_notes)
        all_notes.sort(key=lambda n: n.start)

        if all_notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=all_notes[-1].pitch,
                last_velocity=all_notes[-1].velocity,
                last_chord=chords[-1] if chords else None,
            )

        return all_notes

    # ------------------------------------------------------------------
    # Timeline construction
    # ------------------------------------------------------------------

    def _build_segments(self, total_duration: float) -> list[_Segment]:
        boundaries: set[float] = {0.0, total_duration}

        for hp in self.hit_points:
            boundaries.add(max(0.0, hp.beat))
            # Small lookahead window before hit point
            lookahead = max(0.0, hp.beat - 0.5)
            if lookahead > 0.0:
                boundaries.add(lookahead)

        for arc in self.emotional_arcs:
            boundaries.add(arc.start_beat)
            boundaries.add(arc.end_beat)

        sorted_bounds = sorted(boundaries)
        segments: list[_Segment] = []

        for i in range(len(sorted_bounds) - 1):
            seg_start = sorted_bounds[i]
            seg_end = sorted_bounds[i + 1]
            if seg_end - seg_start < 0.01:
                continue

            mid = (seg_start + seg_end) / 2.0
            mood = self._mood_at_beat(mid)
            mp = _MOOD_PARAMS.get(mood, _MOOD_PARAMS["neutral"])

            # Check if this segment contains a hit point
            hp = None
            for h in self.hit_points:
                if seg_start <= h.beat < seg_end:
                    hp = h
                    break

            segments.append(_Segment(
                start=seg_start,
                end=seg_end,
                mood=mood,
                texture=mp["texture"],
                articulation=mp["articulation"],
                register=mp["register"],
                vel_range=mp["vel_range"],
                dynamic_curve=mp["dynamic_curve"],
                hit_point=hp,
            ))

        return segments

    def _mood_at_beat(self, beat: float) -> str:
        active_arc = None
        for arc in self.emotional_arcs:
            if arc.start_beat <= beat < arc.end_beat:
                active_arc = arc
                break
        if active_arc is None:
            return self.default_mood

        span = active_arc.end_beat - active_arc.start_beat
        if span <= 0:
            return active_arc.start_mood

        t = (beat - active_arc.start_beat) / span

        if active_arc.curve == "exponential":
            t = t * t
        elif active_arc.curve == "sudden_shift":
            t = 1.0 if t > 0.7 else 0.0

        # If interpolation is near the end mood, use end_mood
        if t > 0.5:
            return active_arc.end_mood
        return active_arc.start_mood

    # ------------------------------------------------------------------
    # Voice selection
    # ------------------------------------------------------------------

    def _voices_for_segment(self, seg: _Segment) -> list[tuple[str, str]]:
        base_voices = list(_TEXTURE_VOICES.get(
            seg.texture, _TEXTURE_VOICES[Texture.CHAMBER],
        ))

        # Override for hit-point segments: prioritize specific instruments
        if seg.hit_point is not None:
            priority = _HIT_VOICES.get(seg.hit_point.event_type, [])
            if priority:
                result: list[tuple[str, str]] = []
                for inst in priority:
                    for v_name, v_role in base_voices:
                        if v_name == inst:
                            result.append((v_name, v_role))
                            break
                # Fill remaining voices from base list
                used = {r[0] for r in result}
                for v_name, v_role in base_voices:
                    if v_name not in used:
                        result.append((v_name, v_role))
                return result

        # Random variation for chamber texture
        if seg.texture == Texture.CHAMBER and random.random() < 0.3:
            base_voices[0] = ("cello", "melody")
        return base_voices

    # ------------------------------------------------------------------
    # Hit-point accents
    # ------------------------------------------------------------------

    def _hit_accent(
        self,
        hp: HitPoint,
        chords: list[ChordLabel],
        key: Scale,
        seg: _Segment,
    ) -> list[NoteInfo]:
        # Find chord at hit point
        target_chord = None
        for c in chords:
            if c.start <= hp.beat < c.start + c.duration:
                target_chord = c
                break
        if target_chord is None and chords:
            target_chord = chords[-1]
        if target_chord is None:
            return []

        pcs = target_chord.pitch_classes()
        if not pcs:
            return []

        scale_pcs = [int(d) % 12 for d in key.degrees()]
        accent_notes: list[NoteInfo] = []

        if hp.event_type == "action":
            accent_notes = self._tutti_accent(hp, pcs, scale_pcs, key)
        elif hp.event_type == "tension":
            accent_notes = self._tension_hit(hp, pcs, scale_pcs, key)
        elif hp.event_type == "emotion":
            accent_notes = self._emotion_hit(hp, pcs, scale_pcs, key)
        elif hp.event_type == "reveal":
            accent_notes = self._reveal_hit(hp, pcs, scale_pcs, key)
        elif hp.event_type == "impact":
            accent_notes = self._impact_hit(hp, pcs, scale_pcs, key)
        elif hp.event_type == "calm":
            accent_notes = self._calm_hit(hp, pcs, scale_pcs, key)

        return accent_notes

    def _tutti_accent(
        self,
        hp: HitPoint,
        pcs: list[int],
        scale_pcs: list[int],
        key: Scale,
    ) -> list[NoteInfo]:
        vel = int(90 + hp.intensity * 37)
        vel = max(1, min(127, vel))
        notes: list[NoteInfo] = []
        registers = [36, 48, 60, 72, 84]
        for reg in registers:
            pc = pcs[0] if random.random() < 0.7 else random.choice(pcs)
            pitch = nearest_pitch(pc, reg)
            pitch = snap_to_scale(pitch, key)
            notes.append(NoteInfo(
                pitch=pitch,
                start=round(hp.beat, 6),
                duration=0.5,
                velocity=vel,
            ))
        return notes

    def _tension_hit(
        self,
        hp: HitPoint,
        pcs: list[int],
        scale_pcs: list[int],
        key: Scale,
    ) -> list[NoteInfo]:
        base_vel = int(65 + hp.intensity * 30)
        notes: list[NoteInfo] = []
        # Sustained dissonant cluster in strings
        cluster_root = nearest_pitch(pcs[0], 60)
        offsets = [0, 1, 6, 7]  # semitone cluster for dissonance
        for i, offset in enumerate(offsets):
            pitch = snap_to_scale(cluster_root + offset, key)
            vel = max(1, min(127, base_vel + random.randint(-5, 10)))
            notes.append(NoteInfo(
                pitch=pitch,
                start=round(hp.beat, 6),
                duration=2.0,
                velocity=vel,
            ))
        # Tremolo layer
        trem_pc = random.choice(pcs)
        trem_pitch = nearest_pitch(trem_pc, 72)
        trem_pitch = snap_to_scale(trem_pitch, key)
        t = hp.beat
        while t < hp.beat + 2.0:
            t_vel = max(1, min(127, base_vel + random.randint(-3, 8)))
            notes.append(NoteInfo(
                pitch=trem_pitch,
                start=round(t, 6),
                duration=0.1,
                velocity=t_vel,
            ))
            t += 0.125
        return notes

    def _emotion_hit(
        self,
        hp: HitPoint,
        pcs: list[int],
        scale_pcs: list[int],
        key: Scale,
    ) -> list[NoteInfo]:
        vel = int(50 + hp.intensity * 30)
        vel = max(1, min(127, vel))
        notes: list[NoteInfo] = []
        # Solo melody — violin register
        pc = random.choice(pcs)
        pitch = nearest_pitch(pc, 72)
        pitch = snap_to_scale(pitch, key)
        notes.append(NoteInfo(
            pitch=pitch,
            start=round(hp.beat, 6),
            duration=3.0,
            velocity=vel,
        ))
        # Cello counterpoint below
        second_pc = pcs[1] if len(pcs) > 1 else pcs[0]
        second_pitch = nearest_pitch(second_pc, 48)
        second_pitch = snap_to_scale(second_pitch, key)
        notes.append(NoteInfo(
            pitch=second_pitch,
            start=round(hp.beat + 0.1, 6),
            duration=3.0,
            velocity=max(1, vel - 10),
        ))
        return notes

    def _reveal_hit(
        self,
        hp: HitPoint,
        pcs: list[int],
        scale_pcs: list[int],
        key: Scale,
    ) -> list[NoteInfo]:
        vel = int(60 + hp.intensity * 40)
        vel = max(1, min(127, vel))
        notes: list[NoteInfo] = []
        # Dramatic pause: rest before, then high sustained note
        onset = hp.beat + 0.5  # pause before the reveal
        pc = pcs[0]
        pitch = nearest_pitch(pc, 84)  # high register
        pitch = snap_to_scale(pitch, key)
        notes.append(NoteInfo(
            pitch=pitch,
            start=round(onset, 6),
            duration=2.5,
            velocity=vel,
        ))
        # Lower support
        low_pitch = nearest_pitch(pcs[-1] if len(pcs) > 1 else pcs[0], 48)
        low_pitch = snap_to_scale(low_pitch, key)
        notes.append(NoteInfo(
            pitch=low_pitch,
            start=round(onset + 0.05, 6),
            duration=2.0,
            velocity=max(1, vel - 15),
        ))
        return notes

    def _impact_hit(
        self,
        hp: HitPoint,
        pcs: list[int],
        scale_pcs: list[int],
        key: Scale,
    ) -> list[NoteInfo]:
        vel = int(100 + hp.intensity * 27)
        vel = max(1, min(127, vel))
        notes: list[NoteInfo] = []
        # Full orchestral stab — every register hits
        for reg_center in [36, 48, 60, 72, 84]:
            for pc in pcs[:3]:  # first 3 chord tones
                pitch = nearest_pitch(pc, reg_center)
                pitch = snap_to_scale(pitch, key)
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(hp.beat, 6),
                    duration=0.4,
                    velocity=max(1, min(127, vel + random.randint(-5, 5))),
                ))
        # Timpani hit
        timp_pitch = nearest_pitch(pcs[0], 36)
        timp_pitch = snap_to_scale(timp_pitch, key)
        notes.append(NoteInfo(
            pitch=timp_pitch,
            start=round(hp.beat, 6),
            duration=0.8,
            velocity=vel,
        ))
        return notes

    def _calm_hit(
        self,
        hp: HitPoint,
        pcs: list[int],
        scale_pcs: list[int],
        key: Scale,
    ) -> list[NoteInfo]:
        vel = int(35 + hp.intensity * 20)
        vel = max(1, min(127, vel))
        notes: list[NoteInfo] = []
        # Gentle arpeggiation
        for i, pc in enumerate(pcs[:4]):
            pitch = nearest_pitch(pc, 60 + i * 4)
            pitch = snap_to_scale(pitch, key)
            notes.append(NoteInfo(
                pitch=pitch,
                start=round(hp.beat + i * 0.5, 6),
                duration=2.0,
                velocity=max(1, vel - i * 5),
            ))
        return notes

    # ------------------------------------------------------------------
    # Generator factory (lazy imports to avoid circular dependencies)
    # ------------------------------------------------------------------

    def _make_generator(
        self,
        inst_name: str,
        role: str,
        segment: _Segment,
    ) -> PhraseGenerator | None:
        from melodica.generators.orchestral_strings import (
            ViolinGenerator, ViolaGenerator, CelloGenerator, ContrabassGenerator,
        )
        from melodica.generators.orchestral_woodwinds import (
            FluteGenerator, OboeGenerator, ClarinetGenerator, BassoonGenerator,
        )
        from melodica.generators.orchestral_brass import (
            TrumpetGenerator, TromboneGenerator, FrenchHornGenerator,
        )
        from melodica.generators.orchestral_percussion import (
            TimpaniGenerator,
        )
        from melodica.generators.choir_ahhs import ChoirAahsGenerator
        from melodica.generators.harp import HarpGenerator

        art = segment.articulation
        dyn = segment.dynamic_curve
        v_range = segment.vel_range
        density = self._role_density(role) * (0.5 + segment.register * 0.2)

        # Resolve fanfare articulation to appropriate brass flag
        fanfare = False
        brass_art = art
        if art == "fanfare":
            fanfare = True
            brass_art = "sustained"

        # --- Strings ---
        if inst_name == "violin":
            return ViolinGenerator(
                params=GeneratorParams(
                    density=density,
                    key_range_low=55, key_range_high=96,
                    complexity=self.params.complexity,
                    leap_probability=self.params.leap_probability,
                    velocity_range=v_range,
                ),
                articulation=art if art != "fanfare" else "sustained",
                dynamic_curve=dyn,
            )

        if inst_name == "viola":
            return ViolaGenerator(
                params=GeneratorParams(
                    density=density * 0.8,
                    key_range_low=48, key_range_high=84,
                    complexity=self.params.complexity * 0.8,
                    leap_probability=self.params.leap_probability * 0.7,
                    velocity_range=v_range,
                ),
                articulation=art if art != "fanfare" else "sustained",
                dynamic_curve=dyn,
            )

        if inst_name == "cello":
            return CelloGenerator(
                params=GeneratorParams(
                    density=density,
                    key_range_low=36, key_range_high=72,
                    complexity=self.params.complexity * 0.7,
                    leap_probability=self.params.leap_probability * 0.5,
                    velocity_range=v_range,
                ),
                articulation=art if art != "fanfare" else "sustained",
                dynamic_curve=dyn,
                bass_voice=(role == "bass"),
            )

        if inst_name == "contrabass":
            return ContrabassGenerator(
                params=GeneratorParams(
                    density=density,
                    key_range_low=28, key_range_high=55,
                    complexity=self.params.complexity * 0.5,
                    leap_probability=self.params.leap_probability * 0.3,
                    velocity_range=v_range,
                ),
                articulation=art if art not in ("fanfare", "tremolo") else "sustained",
                dynamic_curve=dyn,
                bass_voice=True,
            )

        # --- Woodwinds ---
        if inst_name == "flute":
            return FluteGenerator(
                params=GeneratorParams(
                    density=density * 0.7,
                    key_range_low=60, key_range_high=96,
                    complexity=self.params.complexity,
                    leap_probability=self.params.leap_probability * 0.8,
                    velocity_range=v_range,
                ),
                articulation=art if art not in ("fanfare", "tremolo") else "legato",
                dynamic_curve=dyn,
                vibrato=True,
            )

        if inst_name == "oboe":
            return OboeGenerator(
                params=GeneratorParams(
                    density=density * 0.6,
                    key_range_low=58, key_range_high=91,
                    complexity=self.params.complexity * 0.8,
                    leap_probability=self.params.leap_probability * 0.6,
                    velocity_range=v_range,
                ),
                articulation=art if art not in ("fanfare", "tremolo") else "legato",
                dynamic_curve=dyn,
                vibrato=True,
            )

        if inst_name == "clarinet":
            return ClarinetGenerator(
                params=GeneratorParams(
                    density=density * 0.6,
                    key_range_low=50, key_range_high=91,
                    complexity=self.params.complexity * 0.8,
                    leap_probability=self.params.leap_probability * 0.6,
                    velocity_range=v_range,
                ),
                articulation=art if art not in ("fanfare", "tremolo") else "legato",
                dynamic_curve=dyn,
                vibrato=False,
            )

        if inst_name == "bassoon":
            return BassoonGenerator(
                params=GeneratorParams(
                    density=density * 0.5,
                    key_range_low=34, key_range_high=72,
                    complexity=self.params.complexity * 0.5,
                    leap_probability=self.params.leap_probability * 0.3,
                    velocity_range=v_range,
                ),
                articulation=art if art not in ("fanfare", "tremolo") else "sustained",
                dynamic_curve=dyn,
                vibrato=False,
            )

        # --- Brass ---
        if inst_name == "french_horn":
            return FrenchHornGenerator(
                params=GeneratorParams(
                    density=density * 0.4,
                    key_range_low=34, key_range_high=70,
                    complexity=self.params.complexity * 0.6,
                    leap_probability=self.params.leap_probability * 0.4,
                    velocity_range=v_range,
                ),
                articulation=brass_art,
                dynamic_curve=dyn,
                fanfare_mode=fanfare,
            )

        if inst_name == "trumpet":
            return TrumpetGenerator(
                params=GeneratorParams(
                    density=density * 0.6,
                    key_range_low=55, key_range_high=82,
                    complexity=self.params.complexity,
                    leap_probability=self.params.leap_probability * 0.7,
                    velocity_range=v_range,
                ),
                articulation=brass_art,
                dynamic_curve=dyn,
                fanfare_mode=fanfare,
            )

        if inst_name == "trombone":
            return TromboneGenerator(
                params=GeneratorParams(
                    density=density * 0.5,
                    key_range_low=40, key_range_high=70,
                    complexity=self.params.complexity * 0.7,
                    leap_probability=self.params.leap_probability * 0.4,
                    velocity_range=v_range,
                ),
                articulation=brass_art,
                dynamic_curve=dyn,
                bass_voice=(role == "bass"),
                fanfare_mode=fanfare,
            )

        # --- Timpani ---
        if inst_name == "timpani":
            return TimpaniGenerator(
                params=GeneratorParams(
                    density=density * 0.3,
                    key_range_low=36, key_range_high=60,
                    velocity_range=(max(1, v_range[0] + 10), min(127, v_range[1] + 20)),
                ),
            )

        # --- Choir ---
        if inst_name == "choir_aahs":
            return ChoirAahsGenerator(
                params=GeneratorParams(
                    density=density * 0.2,
                    key_range_low=48, key_range_high=79,
                    velocity_range=v_range,
                ),
            )

        # --- Harp ---
        if inst_name == "harp":
            return HarpGenerator(
                params=GeneratorParams(
                    density=density * 0.4,
                    key_range_low=24, key_range_high=91,
                    velocity_range=v_range,
                ),
                pattern="arpeggio",
                direction=random.choice(["up", "up_down"]),
            )

        return None

    def _role_density(self, role: str) -> float:
        multipliers = {
            "melody": 1.3,
            "countermelody": 0.7,
            "bass": 0.8,
            "pad": 0.3,
            "harmony": 0.5,
            "fx": 0.15,
        }
        return min(1.0, self.params.density * multipliers.get(role, 1.0))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _chords_in_range(
        self,
        chords: list[ChordLabel],
        start: float,
        dur: float,
    ) -> list[ChordLabel]:
        end = start + dur
        result: list[ChordLabel] = []
        for c in chords:
            if c.start + c.duration > start and c.start < end:
                shifted = ChordLabel(
                    root=c.root,
                    quality=c.quality,
                    extensions=list(c.extensions) if c.extensions else [],
                    bass=c.bass,
                    inversion=c.inversion,
                    start=c.start - start,
                    duration=c.duration,
                    degree=c.degree,
                    function=c.function,
                )
                result.append(shifted)
        return result

    def _accumulate(self, inst_name: str, notes: list[NoteInfo]) -> None:
        if inst_name not in self.tracks:
            self.tracks[inst_name] = []
        self.tracks[inst_name].extend(notes)
        self.instruments[inst_name] = _GM.get(inst_name, 48)
        if inst_name in _STAGE_PAN:
            self.pan_map[inst_name] = _STAGE_PAN[inst_name]
