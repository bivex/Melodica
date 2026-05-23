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
generators/tremolo_strings.py — Sustained string tremolo (bow tremolo) generator.

Layer: Application / Domain
Style: Orchestral, film scoring, ambient.

Unlike tremolo_picking (guitar), this produces sustained bowed tremolo:
rapid bow strokes on sustained notes/chords, creating a shimmering texture.

Variants:
    "single"  — tremolo on one note
    "chord"   — tremolo on chord voicing (divisi strings)
    "octave"  — tremolo on octave doubling
    "cluster" — tremolo on adjacent scale tones (dissonant shimmer)
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, chord_pitches_closed, snap_to_scale


@dataclass
class TremoloStringsGenerator(PhraseGenerator):
    """
    Sustained bowed string tremolo generator.

    variant:
        "single", "chord", "octave", "cluster"
    bow_speed:
        Subdivision in beats (0.0625 = very fast shimmer).
    dynamic_swell:
        If True, apply slow dynamic swells across the tremolo.
    """

    name: str = "Tremolo Strings Generator"
    variant: str = "chord"
    bow_speed: float = 0.0625
    dynamic_swell: bool = True
    attack_time: float = 0.5
    decay_time: float = 0.5
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "chord",
        bow_speed: float = 0.0625,
        dynamic_swell: bool = True,
        attack_time: float = 0.5,
        decay_time: float = 0.5,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.bow_speed = max(0.02, min(0.2, bow_speed))
        self.dynamic_swell = dynamic_swell
        self.attack_time = max(0.0, attack_time)
        self.decay_time = max(0.0, decay_time)
        self.rhythm = rhythm

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pitches = self._pick_pitches(chord, mid, key)
            end = min(event.onset + event.duration, duration_beats)
            t = event.onset
            total_dur = end - event.onset
            note_idx = 0

            base_vel = int(45 + self.params.density * 25)

            # Pre-compute total stroke count so _dynamic knows event length
            total_strokes = max(1, int(total_dur / self.bow_speed))

            while t < end:
                elapsed = t - event.onset

                # Per-stroke dynamic envelope returns velocity and speed factors
                vel_factor, speed_factor = self._dynamic(
                    note_idx, total_strokes, elapsed, total_dur,
                )

                # Phrase-level attack/decay envelope factors
                attack_factor = 1.0
                if elapsed < self.attack_time and self.attack_time > 0:
                    attack_factor = elapsed / self.attack_time

                decay_factor = 1.0
                time_left = end - t
                if time_left < self.decay_time and self.decay_time > 0:
                    decay_factor = time_left / self.decay_time

                # Dynamic swell factor
                swell_factor = 1.0
                if self.dynamic_swell and total_dur > 0:
                    progress = elapsed / total_dur
                    swell_factor = 0.7 + 0.3 * (1.0 - abs(2.0 * progress - 1.0))

                intensity = attack_factor * decay_factor * swell_factor

                # Effective bow speed: base speed * dynamic speed factor
                effective_speed = self.bow_speed * speed_factor
                effective_speed = max(0.02, min(0.3, effective_speed))

                # Alternating bow direction (down-bow is heavy, up-bow is light)
                is_down_bow = (note_idx % 2 == 0)
                bow_vel_offset = 3 if is_down_bow else -3
                bow_brightness = 85 if is_down_bow else 70

                # Sample CC 11 value at this moment in the envelope
                cc11_val = int(40 + 80 * intensity)
                cc11_val = max(1, min(127, cc11_val))

                for i, p in enumerate(pitches):
                    if t >= end:
                        break
                    n_dur = min(effective_speed, end - t)
                    vel = int(base_vel * intensity * vel_factor) + bow_vel_offset
                    vel += random.randint(-2, 2)
                    
                    # Micro-timing jitter per pitch to prevent Harmonic Fusion
                    pitch_jitter = random.uniform(-0.005, 0.005)
                    onset = max(0.0, t + pitch_jitter)

                    # Dynamic brightness and expression values for the bow stroke
                    expression = {
                        11: cc11_val,
                        74: bow_brightness
                    }

                    note = NoteInfo(
                        pitch=p,
                        start=round(onset, 6),
                        duration=round(n_dur * 0.95, 6),  # More overlap for seamless blending
                        velocity=max(1, min(127, vel)),
                    )
                    note.expression = expression
                    notes.append(note)
                    
                t += effective_speed
                note_idx += 1

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _dynamic(
        self,
        note_idx: int,
        total_strokes: int,
        elapsed: float,
        total_dur: float,
    ) -> tuple[float, float]:
        """Return (velocity_factor, speed_factor) for a single bow stroke.

        velocity_factor: multiplier applied to base velocity for per-stroke envelope.
        speed_factor:    multiplier applied to self.bow_speed for phrasing shape.
        """
        # --- Phrase-level speed envelope (attack/release) ---
        speed_factor = 1.0
        if total_dur > 0:
            progress = elapsed / total_dur
            if progress < 0.1:
                speed_factor = 1.5      # slower attack
            elif progress > 0.9:
                speed_factor = 1.3      # slower release

        # --- Per-stroke velocity envelope ---
        if total_strokes <= 6:
            # Short event: skip per-stroke envelope
            vel_factor = 1.0
        elif note_idx < 3:
            # Attack: first 3 strokes get +10 each (2, 1, 0 offset)
            vel_factor = 1.0 + (3 - note_idx) * (10 / 45)
        elif note_idx >= total_strokes - 3:
            # Decay: last 3 strokes get -8 per stroke from the end
            strokes_from_end = total_strokes - note_idx
            vel_factor = 1.0 - strokes_from_end * (8 / 45)
            vel_factor = max(0.2, vel_factor)
        else:
            vel_factor = 1.0

        return vel_factor, speed_factor

    def _pick_pitches(self, chord: ChordLabel, anchor: int, key: Scale) -> list[int]:
        low = self.params.key_range_low
        high = self.params.key_range_high

        if self.variant == "single":
            root = nearest_pitch(chord.root, anchor)
            root = snap_to_scale(root, key)
            return [max(low, min(high, root))]
        elif self.variant == "chord":
            return [max(low, min(high, snap_to_scale(p, key))) for p in chord_pitches_closed(chord, anchor)]
        elif self.variant == "octave":
            root = nearest_pitch(chord.root, anchor)
            root = snap_to_scale(root, key)
            return [max(low, min(high, root)), min(127, snap_to_scale(root + 12, key))]
        elif self.variant == "cluster":
            root = nearest_pitch(chord.root, anchor)
            root = snap_to_scale(root, key)
            return [max(low, min(high, snap_to_scale(root + i, key))) for i in range(3)]
        return [max(low, min(high, snap_to_scale(nearest_pitch(chord.root, anchor), key)))]

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            dur = min(4.0, duration_beats - t)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += 4.0
        return events
