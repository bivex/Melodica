# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/melody.py — MelodyGenerator (refactored facade).

Orchestrates components:
  - RhythmBuilder     → rhythm/event generation
  - PhraseContour     → phrase shape, climax, register target
  - VelocityProcessor → accent patterns + phrase dynamics
  - MotifManager      → motivic development
  - OrnamentProcessor → grace notes
  - FillProcessor     → passing tones over leaps
  - MelodyPitchSelector → core pitch selection (from _melody_pitch.py)
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica import types
from melodica.render_context import RenderContext
from melodica.utils import chord_at, snap_to_scale

# Core pitch selector (already existed)
from melodica.generators._melody_pitch import MelodyPitchSelector

# New submodules
from melodica.generators._melody_rhythm import RhythmBuilder, GrooveProfile
from melodica.generators._melody_phrase import PhraseContour
from melodica.generators._melody_velocity import VelocityProcessor, _velocity_from_params
from melodica.generators._melody_motif import MotifManager
from melodica.generators._melody_ornament import OrnamentProcessor
from melodica.generators._melody_fill import FillProcessor
from melodica.generators._melody_drama import DramaticArc, DRAMA_SHAPE_OPTIONS

# Option sets
FIRST_NOTE_OPTIONS = frozenset(
    {"chord_root", "any_chord", "scale", "tonic", "step_above_tonic", "step_below_tonic"}
)
LAST_NOTE_OPTIONS = frozenset({"last_chord_root", "any_chord", "scale", "any"})
AFTER_LEAP_OPTIONS = frozenset(
    {"step_opposite", "step_any", "step_or_smaller_opposite", "leap_opposite", "any"}
)
CONTOUR_OPTIONS = frozenset({"arch", "rise_fall", "flat", "rise", "wave", "spiral"})
ACCENT_OPTIONS = frozenset({"natural", "strong_weak", "syncopated"})
MOTIF_VARIATION_OPTIONS = frozenset({"transpose", "invert", "retrograde", "sequence", "fragment", "any"})


class MelodyGenerator(PhraseGenerator):
    """Melody generator — refactored into component orchestration."""

    name = "Melody Generator"

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
        random_movement: float = 0.35,
        note_range_low: int | None = None,
        note_range_high: int | None = None,
        direction_bias: float = 0.0,
        register_smoothness: float = 0.5,
        first_note: str = "chord_root",
        last_note: str = "last_chord_root",
        after_leap: str = "step_opposite",
        climax: str = "auto",
        penultimate_step_above: bool = True,
        allow_2nd: bool = True,
        allow_7th: bool = True,
        allowed_up_intervals: frozenset[int] | None = None,
        allowed_down_intervals: frozenset[int] | None = None,
        # phrasing & contour
        phrase_length: float = 4.0,
        phrase_rest_probability: float = 0.2,
        phrase_contour: str = "arch",
        accent_pattern: str = "natural",
        # rhythm
        syncopation: float = 0.15,
        rhythm_variety: float = 0.35,
        rhythm_motif: list[float] | None = None,
        # motivic development
        motif_probability: float = 0.40,
        motif_variation: str = "any",
        # ornaments
        ornament_probability: float = 0.0,
        # dramatic arc
        drama_shape: str = "none",
        drama_peak: float = 0.70,
        # shared motif injection
        base_motif: list[int] | None = None,
        base_motif_rhythm: list[float] | None = None,
        # groove template & meter
        groove_template=None,
        beats_per_bar: int = 4,
        denominator: int = 4,
        # reproducibility
        seed: int | None = None,
        # note density gate
        min_note_gap: float = 0.0,
    ) -> None:
        super().__init__(params)
        self.rhythm = rhythm
        self.mode = mode

        # Core
        if prefer_chord_tones is not None:
            self.harmony_note_probability = prefer_chord_tones
        else:
            self.harmony_note_probability = harmony_note_probability
        self.prefer_chord_tones = self.harmony_note_probability  # backward-compat alias

        self.steps_probability = steps_probability
        self.note_repetition_probability = max(0.0, min(1.0, note_repetition_probability))
        self.random_movement = max(0.0, min(1.0, random_movement))
        self.note_range_low = note_range_low
        self.note_range_high = note_range_high
        self.direction_bias = direction_bias
        self.register_smoothness = max(0.0, min(1.0, register_smoothness))

        # Boundary note strategies
        if first_note not in FIRST_NOTE_OPTIONS:
            raise ValueError(
                f"first_note must be in {sorted(FIRST_NOTE_OPTIONS)}; got {first_note!r}"
            )
        if last_note not in LAST_NOTE_OPTIONS:
            raise ValueError(f"last_note must be in {sorted(LAST_NOTE_OPTIONS)}; got {last_note!r}")
        if after_leap not in AFTER_LEAP_OPTIONS:
            raise ValueError(
                f"after_leap must be in {sorted(AFTER_LEAP_OPTIONS)}; got {after_leap!r}"
            )
        self.first_note = first_note
        self.last_note = last_note
        self.after_leap = after_leap

        # Climax & voice-leading
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
                f"phrase_contour must be in {sorted(CONTOUR_OPTIONS)}; got {phrase_contour!r}"
            )
        self.phrase_contour = phrase_contour
        if accent_pattern not in ACCENT_OPTIONS:
            raise ValueError(
                f"accent_pattern must be in {sorted(ACCENT_OPTIONS)}; got {accent_pattern!r}"
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
                f"motif_variation must be in {sorted(MOTIF_VARIATION_OPTIONS)}; got {motif_variation!r}"
            )
        self.motif_variation = motif_variation

        # Ornaments
        self.ornament_probability = max(0.0, min(1.0, ornament_probability))

        # Dramatic arc
        if drama_shape not in DRAMA_SHAPE_OPTIONS:
            raise ValueError(
                f"drama_shape must be in {sorted(DRAMA_SHAPE_OPTIONS)}; got {drama_shape!r}"
            )
        self.drama_shape = drama_shape
        self.drama_peak = max(0.3, min(0.9, drama_peak))

        # Helpers (lazy-initialized in render)
        self._pitch_selector = MelodyPitchSelector(self)
        self._last_context: RenderContext | None = None
        self._stored_motif: list[int] = []
        self._stored_rhythm: list[float] = []
        self.base_motif = base_motif
        self.base_motif_rhythm = base_motif_rhythm

        # Groove template & meter
        self.groove_template = groove_template
        self.beats_per_bar = beats_per_bar
        self.denominator = denominator

        # Reproducibility seed
        self.seed = seed

        # Minimum gap between note onsets (beats) — prevents cluster mud
        self.min_note_gap = max(0.0, min_note_gap)

    @classmethod
    def from_style(cls, style, **overrides):
        """Create a MelodyGenerator pre-configured from a UnifiedStyle."""
        from melodica.composer.unified_style import UnifiedStyle
        if not isinstance(style, UnifiedStyle):
            raise TypeError(f"Expected UnifiedStyle, got {type(style).__name__}")

        rp = style.rhythm
        mp = style.melody
        hp = style.harmony

        defaults = dict(
            params=GeneratorParams(density=rp.density),
            syncopation=rp.syncopation,
            phrase_length=float(rp.phrase_length),
            steps_probability=mp.steps_probability,
            harmony_note_probability=mp.harmony_note_probability,
            note_repetition_probability=mp.note_repetition_probability,
            direction_bias=mp.direction_bias,
            note_range_low=mp.register_low,
            note_range_high=mp.register_high,
        )
        defaults.update(overrides)
        return cls(**defaults)

    def _build_groove(self):
        """Build a GrooveProfile matching this generator's meter settings."""
        from melodica.generators._melody_rhythm import GrooveProfile
        return GrooveProfile(beats_per_bar=self.beats_per_bar, denominator=self.denominator)

    # ------------------------------------------------------------------
    # Render
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

        # Deterministic render when seed is set
        if self.seed is not None:
            random.seed(self.seed)

        # Components
        groove = self._build_groove()

        # Global position for section buildup
        global_pos = context.phrase_position if context else 0.0

        # Section-based density buildup: increase density in later sections
        eff_density = self.params.density
        if global_pos > 0.3:
            eff_density = min(1.0, eff_density + (global_pos - 0.3) * 0.3)

        rhythm_builder = RhythmBuilder(
            self.params,
            self.phrase_length,
            self.phrase_rest_probability,
            self.syncopation + (global_pos * 0.15),  # sync buildup
            self.rhythm_variety,
            self.rhythm_motif,
            self.rhythm,
            groove=groove,
            density=eff_density,
            groove_template=self.groove_template,
        )
        contour = PhraseContour(
            phrase_contour=self.phrase_contour,
            phrase_length=self.phrase_length,
            climax=self.climax,
        )
        velocity_proc = VelocityProcessor(
            accent_pattern=self.accent_pattern,
            phrase_contour=self.phrase_contour,
            phrase_length=self.phrase_length,
        )
        motif_mgr = MotifManager(
            motif_probability=self.motif_probability, motif_variation=self.motif_variation
        )
        if self.base_motif:
            motif_mgr.store_motif(self.base_motif, self.base_motif_rhythm)
        ornament_proc = OrnamentProcessor(ornament_probability=self.ornament_probability)
        fill_proc = FillProcessor(self.note_range_low, self.note_range_high, self.params)

        # Dramatic arc aware of global position
        drama = DramaticArc(self.drama_shape, duration_beats, self.drama_peak, global_offset=global_pos)

        events = rhythm_builder.build_events(duration_beats, drama=drama)
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

        # Restore motif from previous render
        if context and hasattr(context, "prev_pitches") and len(context.prev_pitches) >= 3:
            motif_mgr._stored_motif = list(context.prev_pitches[-6:])
            pitches = list(context.prev_pitches[-6:])
            if len(pitches) >= 3:
                motif_mgr._stored_intervals = [
                    pitches[j + 1] - pitches[j] for j in range(len(pitches) - 1)
                ]

        # First pitch
        prev_pitch = self._pitch_selector.first_pitch(chords[0], key, low, high, context)

        base_climax = contour.compute_climax(prev_pitch, low, high)

        last_interval = 0
        last_chord: types.ChordLabel | None = None
        range_span = high - low

        # Phrase boundaries
        phrase_len = self.phrase_length if self.phrase_length > 0 else duration_beats
        total_phrases = max(1, int(duration_beats / phrase_len)) if phrase_len > 0 else 1
        first_phrase_end = phrase_len

        motif_notes: list[int] = []
        motif_durations: list[float] = []

        # Dramatic pause tracking
        skip_until = -1.0

        for i, event in enumerate(events):
            # Skip events during dramatic pauses
            if event.onset < skip_until:
                continue

            chord = chord_at(chords, event.onset)
            last_chord = chord
            is_last = i == len(events) - 1

            beat_str = groove.beat_strength(event.onset)
            is_downbeat = beat_str > 0.85
            is_on_beat = beat_str > 0.5
            is_penultimate = i == len(events) - 2 and self.penultimate_step_above and not is_last

            progress = event.onset / duration_beats if duration_beats > 0 else 0.0
            phrase_pos = (event.onset % phrase_len) / phrase_len if phrase_len > 0 else 0.0
            phrase_idx = int(event.onset / phrase_len) if phrase_len > 0 else 0
            phrase_frac = phrase_idx / max(1, total_phrases - 1)

            active_key = key.get_key_at(event.onset) if hasattr(key, "get_key_at") else key

            # ---- Dramatic arc shaping ----
            tension = drama.tension(event.onset)

            # Register shift from drama
            reg_shift = drama.register_shift(event.onset, range_span)
            effective_low = max(self.params.key_range_low, low)
            effective_high = min(self.params.key_range_high + reg_shift, high + reg_shift)
            effective_climax = min(effective_high, base_climax + reg_shift)

            # Phrase climax (drama-enhanced)
            # intensity builds up globally
            climax_int = 0.3 + (global_pos * 0.4)
            if phrase_frac < 0.65:
                climax_offset = int((effective_climax - effective_low) * climax_int * (phrase_frac / 0.65))
            else:
                climax_offset = int(
                    (effective_climax - effective_low) * climax_int * (1.0 - (phrase_frac - 0.65) / 0.35) * 0.5
                )
            climax_pitch = min(effective_high, effective_climax + climax_offset)

            register_center = contour.register_target(phrase_pos, progress, effective_low, effective_high, climax_pitch)
            next_chord = (
                chord_at(chords, event.onset + 2.0) if event.onset + 2.0 < duration_beats else None
            )

            # Cadence target — drama shapes cadence strength
            cadence_target = contour.cadence_target(
                phrase_pos, chord, active_key, prev_pitch, effective_low, effective_high
            )

            # Drama-shaped leap probability
            effective_steps_prob = 1.0 - drama.leap_probability(
                event.onset, 1.0 - steps_prob
            )
            effective_steps_prob = max(0.3, min(0.95, effective_steps_prob))

            # Drama-shaped harmony preference (lower at high tension)
            effective_harmony_prob = self.harmony_note_probability
            if drama.shape != "none":
                # Nudge toward more expressive (non-chord) tones at high tension
                effective_harmony_prob *= (1.0 - tension * 0.4)

            # Motif strategy from drama arc — use clean API
            if self.drama_shape != "none":
                motif_strategy = drama.motif_strategy(event.onset)
                if motif_strategy == "full":
                    motif_mgr.set_variation("transpose")
                elif motif_strategy == "fragment":
                    motif_mgr.set_variation("fragment")
                elif motif_strategy == "invert":
                    motif_mgr.set_variation("invert")
                elif motif_strategy == "return":
                    motif_mgr.set_variation("transpose")
                    motif_mgr.boost_probability(0.3)

            # Cadence strength from drama
            cadence_str = drama.cadence_strength(event.onset)

            # ---- Pick pitch ----
            pitch = motif_mgr.apply(prev_pitch, effective_low, effective_high, active_key, i)
            if pitch == prev_pitch:
                if notes and random.random() < self.note_repetition_probability:
                    pitch = prev_pitch
                elif is_last and self.last_note != "any":
                    pitch = self._pitch_selector.last_pitch(
                        last_chord, active_key, prev_pitch, effective_low, effective_high
                    )
                else:
                    pitch = self._pitch_selector.pick_pitch(
                        chord,
                        active_key,
                        prev_pitch,
                        effective_low,
                        effective_high,
                        last_interval,
                        effective_steps_prob,
                        is_downbeat,
                        is_on_beat,
                        is_penultimate,
                        progress=progress,
                        climax_pitch=climax_pitch,
                        next_chord=next_chord,
                        register_center=register_center,
                        range_span=effective_high - effective_low,
                        beat_strength=beat_str,
                        cadence_target=cadence_target,
                        cadence_strength=cadence_str,
                        harmony_prob=effective_harmony_prob,
                        context=context,
                    )

            pitch = snap_to_scale(max(effective_low, min(effective_high, pitch)), active_key)

            # Velocity: phrase contour + beat strength + dramatic arc
            base_vel = _velocity_from_params(self.params)
            vel = velocity_proc.apply(base_vel, event, phrase_pos, progress, beat_strength=beat_str)

            # Drama velocity shaping
            drama_vel_scale = drama.velocity_scale(event.onset)
            vel = int(vel * drama_vel_scale)

            # Interval accent: boost velocity on large leaps
            if abs(pitch - prev_pitch) >= 7:
                vel = min(127, int(vel * 1.2))

            # Rhythm compression from drama
            compression = drama.rhythm_compression(event.onset)
            dur = max(0.1, event.duration * compression)

            notes.append(
                types.NoteInfo(
                    pitch=int(round(pitch)),
                    start=round(event.onset, 6),
                    duration=dur,
                    velocity=max(0, min(types.MIDI_MAX, vel)),
                )
            )

            # Collect first phrase motif (pitches + durations)
            if event.onset < first_phrase_end and len(motif_notes) < 8:
                motif_notes.append(pitch)
                motif_durations.append(event.duration)

            last_interval = pitch - prev_pitch
            prev_pitch = pitch

            # Post-note dramatic pause check (uses real interval)
            if drama.shape != "none" and drama.is_dramatic_pause(
                event.onset, last_interval, i, len(events)
            ):
                skip_until = event.onset + drama.pause_duration(event.onset)

        # Store motif for next call (with rhythm)
        if motif_notes and len(motif_notes) >= 3:
            motif_mgr.store_motif(motif_notes, motif_durations if motif_durations else None)
            self._stored_motif = list(motif_notes)
            self._stored_rhythm = list(motif_durations) if motif_durations else []

        # Post-processing
        if self.harmony_note_probability < 1.0 and not hasattr(self.rhythm, "_coordinator"):
            notes = fill_proc.fill_leaps(notes, key)

        # Ornaments: explicit probability OR auto-enabled when drama_shape is active
        eff_ornament_prob = self.ornament_probability
        if drama and drama.shape != "none" and eff_ornament_prob == 0.0:
            eff_ornament_prob = 0.08  # light auto-ornament in dramatic mode
        if eff_ornament_prob > 0:
            notes = ornament_proc.add_ornaments(notes, key, low, high, drama=drama)

        # Phrase arch (only when velocity didn't already apply contour — flat phrase)
        if self.phrase_contour == "flat" or self.phrase_length <= 0:
            from melodica.generators._postprocess import apply_phrase_arch

            notes = apply_phrase_arch(
                notes, duration_beats, context.phrase_position if context else 0.0,
                section_type=context.section_role if context else None,
            )

        # Context
        motif_memory = motif_mgr._stored_motif[-8:] if motif_mgr._stored_motif else []
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
                last_pitches=motif_memory,
                duration_beats=duration_beats,
                total_duration=duration_beats,
            )
        else:
            self._last_context = None

        return notes
