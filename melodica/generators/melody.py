# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-16
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/melody.py — MelodyGenerator.

Layer: Application / Domain

Core pitch parameters:
  steps_probability        0.86  — fraction of moves that are steps (<=2 semitones)
  note_repetition_probability 0.14 — probability of repeating the last pitch
  random_movement          0.80  — fraction of selections made randomly (vs. closest)
  harmony_note_probability 0.64  — fraction from chord tones (vs. scale tones)
  note_range_low/high      54/76 — range override (beats params.key_range)
  first_note               "chord_root"      — strategy for the very first pitch
  last_note                "last_chord_root"  — strategy for the very last pitch
  after_leap               "any"              — constraint on move following a leap
  allowed_up/down_intervals None (= all)      — frozenset of semitone distances

Phrasing & contour:
  phrase_length            0.0   — beats per phrase (0 = no phrasing)
  phrase_rest_probability  0.2   — chance of rest between phrases
  phrase_contour           "arch" — "arch", "rise_fall", "flat", "rise"
  accent_pattern           "natural" — "natural", "strong_weak", "syncopated"

Rhythm:
  syncopation              0.0   — 0-1, shift notes off-beat
  rhythm_variety           0.0   — 0-1, mix of durations
  rhythm_motif             None  — list of duration ratios, e.g. [1.0, 0.5, 0.5, 1.0]

Register & smoothness:
  register_smoothness      0.5   — 0-1, penalize large interval jumps
  direction_bias           0.0   — -1 to 1, up/down tendency (weighted)

Motivic development:
  motif_probability        0.0   — 0-1, chance of referencing stored motif
  motif_variation           "transpose" — "transpose", "invert", "retrograde", "any"

Ornamentation:
  ornament_probability     0.0   — 0-1, grace notes before strong beats
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica import types
from melodica.render_context import RenderContext
from melodica.utils import nearest_pitch, nearest_pitch_above, pitch_class, chord_at, snap_to_scale
from melodica.generators._melody_pitch import (
    MelodyPitchSelector,
    STEP_SEMITONES,
    LEAP_SEMITONES,
    ALL_INTERVALS,
    DEFAULT_UP_INTERVALS,
    DEFAULT_DOWN_INTERVALS,
    _all_pitches_in_range,
    _all_pitches_in_range_pc_list,
)


# Interval constants and utility helpers re-exported from _melody_pitch

FIRST_NOTE_OPTIONS = frozenset(
    {
        "chord_root",
        "any_chord",
        "scale",
        "tonic",
        "step_above_tonic",
        "step_below_tonic",
    }
)
LAST_NOTE_OPTIONS = frozenset(
    {
        "last_chord_root",
        "any_chord",
        "scale",
        "any",
    }
)
AFTER_LEAP_OPTIONS = frozenset(
    {
        "step_opposite",
        "step_any",
        "step_or_smaller_opposite",
        "leap_opposite",
        "any",
    }
)
CONTOUR_OPTIONS = frozenset({"arch", "rise_fall", "flat", "rise"})
ACCENT_OPTIONS = frozenset({"natural", "strong_weak", "syncopated"})
MOTIF_VARIATION_OPTIONS = frozenset({"transpose", "invert", "retrograde", "any"})


# ---------------------------------------------------------------------------
# MelodyGenerator
# ---------------------------------------------------------------------------


@dataclass
class MelodyGenerator(PhraseGenerator):
    name: str = "Melody Generator"
    rhythm: RhythmGenerator | None = None

    # Mode: how chord/scale tones are used
    mode: str = "downbeat_chord"

    # Pitch-pool control
    harmony_note_probability: float = 0.64
    prefer_chord_tones: float = 0.64  # legacy alias

    # Step / leap / repetition balance
    steps_probability: float | None = None
    note_repetition_probability: float = 0.14

    # Random vs. directed selection
    random_movement: float = 0.80

    # Note-range override
    note_range_low: int | None = None
    note_range_high: int | None = None

    # Direction tendency
    direction_bias: float = 0.0

    # Register smoothness: penalize large jumps
    register_smoothness: float = 0.5

    # Phrase-boundary strategies
    first_note: str = "chord_root"
    last_note: str = "last_chord_root"

    # Post-leap constraint
    after_leap: str = "any"

    # Climax
    climax: str = "first_plus_maj3"

    # Penultimate note resolves to tonic
    penultimate_step_above: bool = True

    # Allow 2nd/7th as melody notes even in chord-only mode
    allow_2nd: bool = True
    allow_7th: bool = True

    # Interval filters
    allowed_up_intervals: frozenset[int] | None = None
    allowed_down_intervals: frozenset[int] | None = None

    # Phrasing & contour
    phrase_length: float = 0.0
    phrase_rest_probability: float = 0.2
    phrase_contour: str = "arch"
    accent_pattern: str = "natural"

    # Rhythm
    syncopation: float = 0.0
    rhythm_variety: float = 0.0
    rhythm_motif: list[float] | None = None

    # Motivic development
    motif_probability: float = 0.0
    motif_variation: str = "transpose"

    # Ornaments
    ornament_probability: float = 0.0

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        rhythm: RhythmGenerator | None = None,
        mode: str = "downbeat_chord",
        prefer_chord_tones: float | None = None,
        harmony_note_probability: float = 0.64,
        steps_probability: float | None = None,
        note_repetition_probability: float = 0.14,
        random_movement: float = 0.80,
        note_range_low: int | None = None,
        note_range_high: int | None = None,
        direction_bias: float = 0.0,
        register_smoothness: float = 0.5,
        first_note: str = "chord_root",
        last_note: str = "last_chord_root",
        after_leap: str = "any",
        climax: str = "first_plus_maj3",
        penultimate_step_above: bool = True,
        allow_2nd: bool = True,
        allow_7th: bool = True,
        allowed_up_intervals: frozenset[int] | None = None,
        allowed_down_intervals: frozenset[int] | None = None,
        # phrasing & contour
        phrase_length: float = 0.0,
        phrase_rest_probability: float = 0.2,
        phrase_contour: str = "arch",
        accent_pattern: str = "natural",
        # rhythm
        syncopation: float = 0.0,
        rhythm_variety: float = 0.0,
        rhythm_motif: list[float] | None = None,
        # motivic development
        motif_probability: float = 0.0,
        motif_variation: str = "transpose",
        # ornaments
        ornament_probability: float = 0.0,
    ) -> None:
        super().__init__(params)
        self.rhythm = rhythm

        if prefer_chord_tones is not None:
            self.harmony_note_probability = prefer_chord_tones
            self.prefer_chord_tones = prefer_chord_tones
        else:
            self.harmony_note_probability = harmony_note_probability
            self.prefer_chord_tones = harmony_note_probability

        self.steps_probability = steps_probability
        self.note_repetition_probability = max(0.0, min(1.0, note_repetition_probability))
        self.random_movement = max(0.0, min(1.0, random_movement))
        self.note_range_low = note_range_low
        self.note_range_high = note_range_high
        self.direction_bias = direction_bias
        self.register_smoothness = max(0.0, min(1.0, register_smoothness))

        if first_note not in FIRST_NOTE_OPTIONS:
            raise ValueError(
                f"first_note must be one of {sorted(FIRST_NOTE_OPTIONS)}; got {first_note!r}"
            )
        if last_note not in LAST_NOTE_OPTIONS:
            raise ValueError(
                f"last_note must be one of {sorted(LAST_NOTE_OPTIONS)}; got {last_note!r}"
            )
        if after_leap not in AFTER_LEAP_OPTIONS:
            raise ValueError(
                f"after_leap must be one of {sorted(AFTER_LEAP_OPTIONS)}; got {after_leap!r}"
            )
        self.first_note = first_note
        self.last_note = last_note
        self.after_leap = after_leap
        self.mode = mode
        self.climax = climax
        self.penultimate_step_above = penultimate_step_above
        self.allow_2nd = allow_2nd
        self.allow_7th = allow_7th
        self.allowed_up_intervals = allowed_up_intervals
        self.allowed_down_intervals = allowed_down_intervals

        # Phrasing & contour
        self.phrase_length = max(0.0, phrase_length)
        self.phrase_rest_probability = max(0.0, min(1.0, phrase_rest_probability))
        if phrase_contour not in CONTOUR_OPTIONS:
            raise ValueError(
                f"phrase_contour must be one of {sorted(CONTOUR_OPTIONS)}; got {phrase_contour!r}"
            )
        self.phrase_contour = phrase_contour
        if accent_pattern not in ACCENT_OPTIONS:
            raise ValueError(
                f"accent_pattern must be one of {sorted(ACCENT_OPTIONS)}; got {accent_pattern!r}"
            )
        self.accent_pattern = accent_pattern

        # Rhythm
        self.syncopation = max(0.0, min(1.0, syncopation))
        self.rhythm_variety = max(0.0, min(1.0, rhythm_variety))
        self.rhythm_motif = rhythm_motif

        # Motivic development
        self.motif_probability = max(0.0, min(1.0, motif_probability))
        if motif_variation not in MOTIF_VARIATION_OPTIONS:
            raise ValueError(
                f"motif_variation must be one of {sorted(MOTIF_VARIATION_OPTIONS)}; got {motif_variation!r}"
            )
        self.motif_variation = motif_variation

        # Ornaments
        self.ornament_probability = max(0.0, min(1.0, ornament_probability))

        self._last_context: RenderContext | None = None
        self._stored_motif: list[int] = []  # pitches of stored motif
        self._pitch_selector: MelodyPitchSelector = MelodyPitchSelector(self)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def render(
        self,
        chords: list[types.ChordLabel],
        key: types.Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[types.NoteInfo]:
        if not chords:
            return []

        events = self._build_events(duration_beats)
        if not events:
            return []

        notes: list[types.NoteInfo] = []

        low = self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        high = (
            self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        )

        steps_prob = (
            self.steps_probability
            if self.steps_probability is not None
            else 1.0 - self.params.leap_probability
        )

        # Initialise prev_pitch via first_note strategy
        prev_pitch = self._first_pitch(chords[0], key, low, high, context)

        # Restore motif from previous render if available
        if context and hasattr(context, "prev_pitches") and len(context.prev_pitches) >= 3:
            self._stored_motif = list(context.prev_pitches[-6:])

        # Compute base climax pitch
        base_climax = self._compute_climax(prev_pitch, low, high)

        last_interval = 0
        last_chord: types.ChordLabel | None = None
        range_span = high - low

        # Phrase boundaries for contour
        phrase_len = self.phrase_length if self.phrase_length > 0 else duration_beats
        # Global climax: rises across phrases, peaks ~60-70% through duration
        total_phrases = max(1, int(duration_beats / phrase_len)) if phrase_len > 0 else 1

        # Store first phrase as motif
        motif_notes: list[int] = []
        first_phrase_end = phrase_len

        for i, event in enumerate(events):
            chord = chord_at(chords, event.onset)
            last_chord = chord
            is_last = i == len(events) - 1

            is_downbeat = event.onset % 1.0 < 0.1
            is_on_beat = event.onset % 0.5 < 0.1
            is_penultimate = i == len(events) - 2 and self.penultimate_step_above and not is_last

            # Progress metrics
            progress = event.onset / duration_beats if duration_beats > 0 else 0.0
            phrase_pos = (event.onset % phrase_len) / phrase_len if phrase_len > 0 else 0.0
            phrase_idx = int(event.onset / phrase_len) if phrase_len > 0 else 0
            phrase_frac = phrase_idx / max(1, total_phrases - 1)

            # Resolve active key (handle both Scale and MusicTimeline)
            active_key = key.get_key_at(event.onset) if hasattr(key, "get_key_at") else key

            # Per-phrase climax
            if phrase_frac < 0.65:
                climax_offset = int((base_climax - low) * 0.4 * (phrase_frac / 0.65))
            else:
                climax_offset = int(
                    (base_climax - low) * 0.4 * (1.0 - (phrase_frac - 0.65) / 0.35) * 0.5
                )
            climax_pitch = min(high, base_climax + climax_offset)

            register_center = self._register_target(phrase_pos, progress, low, high, climax_pitch)
            next_chord = (
                chord_at(chords, event.onset + 2.0) if event.onset + 2.0 < duration_beats else None
            )

            # ---- Motif reference ----
            if (
                self.motif_probability > 0
                and len(self._stored_motif) >= 3
                and random.random() < self.motif_probability
            ):
                pitch = self._apply_motif(self._stored_motif, i, prev_pitch, low, high, active_key)
            elif notes and random.random() < self.note_repetition_probability:
                pitch = prev_pitch
            elif is_last and self.last_note != "any":
                pitch = self._last_pitch(last_chord, active_key, prev_pitch, low, high)
            else:
                pitch = self._pick_pitch(
                    chord,
                    active_key,
                    prev_pitch,
                    low,
                    high,
                    last_interval,
                    steps_prob,
                    is_downbeat,
                    is_on_beat,
                    is_penultimate,
                    progress=progress,
                    climax_pitch=climax_pitch,
                    next_chord=next_chord,
                    register_center=register_center,
                    range_span=range_span,
                )

            # Clamp to range and snap to scale
            pitch = snap_to_scale(max(low, min(high, pitch)), active_key)

            # Compute velocity with accent pattern and phrase contour
            base_vel = _velocity_from_density(self.params.density)
            vel = self._apply_velocity(base_vel, event, phrase_pos, progress)

            notes.append(
                types.NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(0, min(types.MIDI_MAX, vel)),
                )
            )

            # Collect first phrase pitches as motif
            if event.onset < first_phrase_end and len(motif_notes) < 8:
                motif_notes.append(pitch)

            last_interval = pitch - prev_pitch
            prev_pitch = pitch

        # Store motif for future renders
        if motif_notes and len(motif_notes) >= 3:
            self._stored_motif = motif_notes

        # Post-processing
        # Skip fills when using shared rhythm to maintain aligned onsets across tracks
        if self.harmony_note_probability < 1.0 and not hasattr(self.rhythm, "_coordinator"):
            notes = self._fill_leaps(notes, key)

        if self.ornament_probability > 0:
            notes = self._add_ornaments(notes, key, low, high)

        # Phrase arch velocity contour — only when _apply_velocity didn't already do it
        if self.phrase_contour == "flat" or self.phrase_length <= 0:
            from melodica.generators._postprocess import apply_phrase_arch

            notes = apply_phrase_arch(
                notes, duration_beats, context.phrase_position if context else 0.0
            )

        # Context with motif memory
        motif_memory = self._stored_motif[-8:] if self._stored_motif else []
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
                last_pitches=motif_memory,
            )
        else:
            self._last_context = None

        return notes

    # ------------------------------------------------------------------
    # Pitch selection (delegates to MelodyPitchSelector)
    # ------------------------------------------------------------------

    def _pick_pitch(
        self,
        chord: types.ChordLabel | None,
        key: types.Scale,
        prev_pitch: int,
        low: int,
        high: int,
        last_interval: int,
        steps_prob: float,
        is_downbeat: bool = False,
        is_on_beat: bool = False,
        is_penultimate: bool = False,
        progress: float = 0.0,
        climax_pitch: int | None = None,
        next_chord: types.ChordLabel | None = None,
        register_center: int | None = None,
        range_span: int = 20,
    ) -> int:
        return self._pitch_selector.pick_pitch(
            chord,
            key,
            prev_pitch,
            low,
            high,
            last_interval,
            steps_prob,
            is_downbeat,
            is_on_beat,
            is_penultimate,
            progress=progress,
            climax_pitch=climax_pitch,
            next_chord=next_chord,
            register_center=register_center,
            range_span=range_span,
        )

    def _build_candidates(self, pool, prev_pitch, low, high, interval_set, required_direction):
        return self._pitch_selector.build_candidates(
            pool, prev_pitch, low, high, interval_set, required_direction
        )

    def _get_pitch_pool(self, chord, key, is_downbeat=False, is_on_beat=False):
        return self._pitch_selector.get_pitch_pool(chord, key, is_downbeat, is_on_beat)

    def _first_pitch(self, first_chord, key, low, high, context):
        return self._pitch_selector.first_pitch(first_chord, key, low, high, context)

    def _last_pitch(self, last_chord, key, prev_pitch, low, high):
        return self._pitch_selector.last_pitch(last_chord, key, prev_pitch, low, high)

    # ------------------------------------------------------------------
    # Register target (phrase contour)
    # ------------------------------------------------------------------

    def _register_target(
        self, phrase_pos: float, global_progress: float, low: int, high: int, climax_pitch: int
    ) -> int:
        """Compute the target register center based on phrase contour position."""
        mid = (low + high) // 2
        if self.climax == "none" and self.phrase_contour == "flat":
            return mid

        if self.phrase_contour == "arch":
            # Rise to 60%, peak, fall to 100%
            if phrase_pos < 0.6:
                frac = phrase_pos / 0.6
                return int(mid + (climax_pitch - mid) * frac)
            else:
                frac = (phrase_pos - 0.6) / 0.4
                return int(climax_pitch - (climax_pitch - mid) * frac * 0.7)

        elif self.phrase_contour == "rise_fall":
            # Symmetric: rise first half, fall second half
            if phrase_pos < 0.5:
                frac = phrase_pos / 0.5
                return int(mid + (climax_pitch - mid) * frac)
            else:
                frac = (phrase_pos - 0.5) / 0.5
                return int(climax_pitch - (climax_pitch - low) * frac * 0.5)

        elif self.phrase_contour == "rise":
            # Only rise, no fall
            return int(mid + (climax_pitch - mid) * phrase_pos)

        return mid  # "flat"

    # ------------------------------------------------------------------
    # Velocity dynamics
    # ------------------------------------------------------------------

    def _apply_velocity(
        self, base_vel: int, event: RhythmEvent, phrase_pos: float, global_progress: float
    ) -> int:
        """Apply accent pattern and phrase contour to velocity."""
        vel = base_vel * event.velocity_factor

        # Accent pattern
        is_downbeat = event.onset % 1.0 < 0.1
        is_on_beat = event.onset % 0.5 < 0.1
        is_offbeat = not is_on_beat

        if self.accent_pattern == "strong_weak":
            if is_downbeat:
                vel *= 1.15
            elif is_offbeat:
                vel *= 0.80
        elif self.accent_pattern == "syncopated":
            if is_offbeat:
                vel *= 1.10
            elif is_downbeat:
                vel *= 0.90

        # Phrase contour dynamics: crescendo to climax, diminuendo after
        if self.phrase_contour != "flat" and self.phrase_length > 0:
            if phrase_pos < 0.6:
                # Crescendo: 0.85 → 1.0
                contour_factor = 0.85 + 0.15 * (phrase_pos / 0.6)
            else:
                # Diminuendo: 1.0 → 0.75
                contour_factor = 1.0 - 0.25 * ((phrase_pos - 0.6) / 0.4)
            vel *= contour_factor

        # Small random touch variation
        vel *= random.uniform(0.92, 1.08)

        return max(1, min(127, int(vel)))

    # ------------------------------------------------------------------
    # Motivic development
    # ------------------------------------------------------------------

    def _apply_motif(
        self,
        motif: list[int],
        index: int,
        prev_pitch: int,
        low: int,
        high: int,
        key: types.Scale,
    ) -> int:
        """Apply a stored motif with variation (transpose, invert, retrograde)."""
        if not motif:
            return prev_pitch

        # Pick variation
        variation = self.motif_variation
        if variation == "any":
            variation = random.choice(["transpose", "invert", "retrograde"])

        motif_idx = index % len(motif)

        if variation == "transpose":
            # Transpose motif so first note matches prev_pitch
            offset = prev_pitch - motif[0]
            pitch = motif[motif_idx] + offset
        elif variation == "invert":
            # Invert intervals around motif center
            center = sum(motif) // len(motif)
            interval = motif[motif_idx] - center
            pitch = prev_pitch + (center - motif[motif_idx])  # inverted interval
            # Snap toward prev_pitch for first note
            if motif_idx == 0:
                pitch = prev_pitch
            else:
                pitch = prev_pitch - interval
        elif variation == "retrograde":
            reversed_motif = list(reversed(motif))
            offset = prev_pitch - reversed_motif[0]
            pitch = reversed_motif[motif_idx] + offset
        else:
            pitch = motif[motif_idx]

        return snap_to_scale(max(low, min(high, pitch)), key)

    # ------------------------------------------------------------------
    # Rhythm / events
    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        # Motif-based rhythm
        if self.rhythm_motif is not None and len(self.rhythm_motif) >= 2:
            return self._build_motif_events(duration_beats)

        base_step = max(0.25, (1.0 - self.params.density) * 2.0)
        events: list[RhythmEvent] = []
        t = 0.0
        dur_pool = self._duration_pool(base_step)
        # Step multipliers for rhythmic variety — vary the *advance*, not just duration
        step_pool = [base_step * 0.5, base_step * 0.75, base_step, base_step, base_step * 1.5]

        while t < duration_beats:
            # Phrase gap
            if self.phrase_length > 0 and t > 0 and t % self.phrase_length < base_step:
                if random.random() < self.phrase_rest_probability:
                    gap = random.choice([0.25, 0.5, 0.5, 1.0])
                    t += gap
                    continue

            # Pick duration with variety
            if self.rhythm_variety > 0 and random.random() < self.rhythm_variety:
                dur = random.choice(dur_pool)
            else:
                dur = max(0.125, base_step - 0.01)

            # Syncopation
            onset = t
            if self.syncopation > 0 and random.random() < self.syncopation:
                shift = random.choice([0.125, 0.25, 0.25, 0.375])
                onset = t + shift

            is_downbeat = onset % 1.0 < 0.1
            vel_factor = random.uniform(1.05, 1.15) if is_downbeat else random.uniform(0.85, 1.0)

            events.append(
                RhythmEvent(
                    onset=round(onset, 6), duration=max(0.1, dur), velocity_factor=vel_factor
                )
            )

            # Vary the step to create true rhythmic variety
            if self.rhythm_variety > 0 and random.random() < self.rhythm_variety:
                t += random.choice(step_pool)
            else:
                t += base_step

        return events

    def _build_motif_events(self, duration_beats: float) -> list[RhythmEvent]:
        """Build events from a repeating rhythm_motif pattern."""
        motif = self.rhythm_motif
        base_step = max(0.25, (1.0 - self.params.density) * 2.0)

        events: list[RhythmEvent] = []
        t = 0.0
        motif_idx = 0

        while t < duration_beats:
            # Phrase gap
            if self.phrase_length > 0 and t > 0 and t % self.phrase_length < base_step:
                if random.random() < self.phrase_rest_probability:
                    gap = random.choice([0.25, 0.5, 0.5, 1.0])
                    t += gap
                    continue

            ratio = motif[motif_idx % len(motif)]
            dur = max(0.1, base_step * ratio)

            # Slight syncopation on some repeats
            onset = t
            if self.syncopation > 0 and random.random() < self.syncopation:
                shift = random.choice([0.125, 0.25])
                onset = t + shift

            is_downbeat = onset % 1.0 < 0.1
            vel_factor = random.uniform(1.05, 1.15) if is_downbeat else random.uniform(0.85, 1.0)

            events.append(
                RhythmEvent(onset=round(onset, 6), duration=dur, velocity_factor=vel_factor)
            )
            t += dur
            motif_idx += 1

        return events

    def _duration_pool(self, base_step: float) -> list[float]:
        return [
            max(0.1, base_step * 0.5),
            max(0.125, base_step),
            max(0.125, base_step),
            base_step * 1.5,
            base_step * 2.0,
            max(0.1, base_step * 0.25),
        ]

    # ------------------------------------------------------------------
    # Climax
    # ------------------------------------------------------------------

    def _compute_climax(self, first_pitch: int, low: int, high: int) -> int:
        offset_map: dict[str, int] = {
            "first_plus_maj3": 4,
            "up_3rd": 4,
            "up_5th": 7,
            "up_octave": 12,
        }
        if self.climax == "none":
            return first_pitch
        offset = offset_map.get(self.climax, 4)
        return min(high, first_pitch + offset)

    # ------------------------------------------------------------------
    # Ornamentation
    # ------------------------------------------------------------------

    def _add_ornaments(
        self, notes: list[types.NoteInfo], key: types.Scale, low: int, high: int
    ) -> list[types.NoteInfo]:
        if not notes or self.ornament_probability <= 0:
            return notes

        scale_pcs = set(key.degrees())
        result: list[types.NoteInfo] = []
        for note in notes:
            is_strong = note.start % 1.0 < 0.15
            if is_strong and random.random() < self.ornament_probability:
                approach_above = random.random() < 0.5
                for offset in [2, 1, 3]:
                    grace_pc = (note.pitch + offset * (1 if approach_above else -1)) % 12
                    if grace_pc in scale_pcs:
                        grace_pitch = note.pitch + offset * (1 if approach_above else -1)
                        if low <= grace_pitch <= high:
                            grace_start = max(0, note.start - 0.125)
                            result.append(
                                types.NoteInfo(
                                    pitch=grace_pitch,
                                    start=round(grace_start, 6),
                                    duration=0.0625,
                                    velocity=max(1, int(note.velocity * 0.6)),
                                )
                            )
                        break
            result.append(note)
        result.sort(key=lambda n: n.start)
        return result

    # ------------------------------------------------------------------
    # Post-processing
    # ------------------------------------------------------------------

    def _fill_leaps(self, notes: list[types.NoteInfo], key) -> list[types.NoteInfo]:
        if len(notes) < 2:
            return notes

        low = self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        high = (
            self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        )

        result = [notes[0]]
        fills_added = 0
        max_fills = max(4, len(notes) // 2)

        for i in range(1, len(notes)):
            gap = notes[i].pitch - notes[i - 1].pitch
            abs_gap = abs(gap)

            if abs_gap > 4 and fills_added < max_fills:
                direction = 1 if gap > 0 else -1
                num_fills = min(abs_gap // 3, 4) if abs_gap > 7 else 1
                span = notes[i].start - notes[i - 1].start

                for fill_idx in range(num_fills):
                    if num_fills == 1:
                        frac = 0.5
                        step = min(abs_gap // 2, 4)
                    else:
                        frac = (fill_idx + 1) / (num_fills + 1)
                        step = round(abs_gap * frac)

                    pass_pitch = notes[i - 1].pitch + direction * max(1, step)
                    pass_start = notes[i - 1].start + span * frac

                    # Resolve key at fill position
                    active_key = key.get_key_at(pass_start) if hasattr(key, "get_key_at") else key
                    pass_pitch = snap_to_scale(max(low, min(high, pass_pitch)), active_key)

                    pass_dur = min(notes[i - 1].duration, 0.25)

                    result.append(
                        types.NoteInfo(
                            pitch=pass_pitch,
                            start=round(pass_start, 6),
                            duration=pass_dur,
                            velocity=max(1, min(127, int(notes[i].velocity * 0.65))),
                        )
                    )
                    fills_added += 1

            result.append(notes[i])

        return result


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _velocity_from_density(density: float) -> int:
    return int(50 + density * 50)
