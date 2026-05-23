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
generators/canon.py — Canon/imitation generator with counterpoint rules.

Layer: Application / Domain
Style: Classical counterpoint, fugal writing.

Canon types:
    "strict"    — exact intervallic transposition
    "tonal"     — diatonic transposition preserving scale function
    "contrary"  — follower moves in opposite direction
    "free"      — follower adapts to fit harmony
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OCTAVE = 12
_CONSONANT = {0, 3, 4, 5, 7, 8, 9}
_STRONG_CONSONANT = {0, 3, 4, 7, 8, 9}
_STEP_WEIGHT = 0.5
_VALID_CANON_TYPES = frozenset({"strict", "tonal", "contrary", "free", "fugue"})
_DEFAULT_DELAY = 2.0


# ---------------------------------------------------------------------------
# Follower config
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _FollowerCfg:
    """Configuration for a single follower voice."""

    interval: int
    delay: float
    index: int


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


@dataclass
class CanonGenerator(PhraseGenerator):
    """
    Canon/imitation generator with counterpoint rules.

    canon_type:
        "strict", "tonal", "contrary", "free", "fugue"
    delay_beats:
        How many beats the follower lags behind.
    interval:
        Semitone offset for the first follower.
    num_followers:
        Number of follower voices (1-3).
    subject_length:
        For fugue mode: how many beats the subject lasts.
    augmentation:
        For fugue mode: duration multiplier for augmented entries (2.0 = double).
    """

    name: str = "Canon Generator"
    canon_type: str = "tonal"
    delay_beats: float = _DEFAULT_DELAY
    interval: int = 7
    num_followers: int = 1
    subject_length: float = 4.0
    augmentation: float = 2.0
    lead_rhythm: RhythmGenerator | None = None
    follower_rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        canon_type: str = "tonal",
        delay_beats: float = _DEFAULT_DELAY,
        interval: int = 7,
        num_followers: int = 1,
        subject_length: float = 4.0,
        augmentation: float = 2.0,
        lead_rhythm: RhythmGenerator | None = None,
        follower_rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if canon_type not in _VALID_CANON_TYPES:
            raise ValueError(
                f"canon_type must be one of {sorted(_VALID_CANON_TYPES)}; got {canon_type!r}"
            )
        self.canon_type = canon_type
        self.delay_beats = max(0.25, delay_beats)
        self.interval = interval
        self.num_followers = max(1, min(3, num_followers))
        self.subject_length = max(1.0, subject_length)
        self.augmentation = max(1.0, augmentation)
        self.lead_rhythm = lead_rhythm
        self.follower_rhythm = follower_rhythm

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        if self.canon_type == "fugue":
            all_notes = self._render_fugue(chords, key, duration_beats, context)
        else:
            lead = self._generate_lead(chords, key, duration_beats, context)
            all_notes = list(lead)
            for cfg in self._follower_configs(key):
                follower = self._generate_follower(lead, chords, key, duration_beats, cfg)
                all_notes.extend(follower)

        all_notes.sort(key=lambda n: n.start)
        last_chord = chords[-1] if chords else None
        if all_notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=all_notes[-1].pitch,
                last_velocity=all_notes[-1].velocity,
                last_chord=last_chord,
            )
        return all_notes

    # ------------------------------------------------------------------
    # Fugue rendering
    # ------------------------------------------------------------------

    def _render_fugue(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None,
    ) -> list[NoteInfo]:
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2
        all_notes: list[NoteInfo] = []

        # Generate subject from first chord
        subject = self._generate_subject(chords, key, context, anchor)

        # Entry plan: subject entries at staggered intervals (stretto overlap possible)
        entries = self._fugue_entry_plan(duration_beats)

        for entry_idx, (entry_delay, entry_interval, entry_aug) in enumerate(entries):
            voice_anchor = anchor + entry_idx * 5  # separate registers
            voice_low = max(low, voice_anchor - 12)
            voice_high = min(high, voice_anchor + 12)

            for note in subject:
                onset = note.start + entry_delay
                if onset >= duration_beats:
                    break
                # Transpose to entry interval
                pitch = _tonal_transpose(note.pitch, entry_interval, key)
                # Apply augmentation: stretch duration
                dur = note.duration * entry_aug
                pitch = max(voice_low, min(voice_high, pitch))
                vel = max(1, min(127, int(note.velocity * (0.9 - entry_idx * 0.1))))
                all_notes.append(NoteInfo(
                    pitch=pitch, start=round(onset, 6),
                    duration=dur, velocity=vel,
                ))

        # Episode: free counterpoint between subject entries
        episode_notes = self._fugue_episode(chords, key, subject, entries, duration_beats)
        all_notes.extend(episode_notes)

        return all_notes

    def _generate_subject(
        self, chords: list[ChordLabel], key: Scale,
        context: RenderContext | None, anchor: int,
    ) -> list[NoteInfo]:
        events = self._build_events(self.subject_length)
        notes: list[NoteInfo] = []
        prev = context.prev_pitch if context and context.prev_pitch is not None else anchor
        for ev in events:
            chord = chord_at(chords, ev.onset)
            if chord is None:
                continue
            pitch = _pick_lead_pitch(chord, key, prev,
                                     self.params.key_range_low, self.params.key_range_high)
            vel = int(65 + self.params.density * 30)
            notes.append(NoteInfo(
                pitch=pitch, start=round(ev.onset, 6),
                duration=ev.duration, velocity=max(1, min(127, vel)),
            ))
            prev = pitch
        return notes

    def _fugue_entry_plan(self, duration: float) -> list[tuple[float, int, float]]:
        plan: list[tuple[float, int, float]] = []
        delay = 0.0
        for i in range(self.num_followers + 1):
            ivl = self.interval if i % 2 == 0 else (self.interval + 7) % 12
            aug = 1.0 if i == 0 or random.random() > 0.3 else self.augmentation
            plan.append((delay, ivl, aug))
            delay += self.delay_beats
            if delay >= duration * 0.8:
                break
        return plan

    def _fugue_episode(
        self, chords: list[ChordLabel], key: Scale,
        subject: list[NoteInfo], entries: list[tuple],
        duration: float,
    ) -> list[NoteInfo]:
        if not entries or not subject:
            return []
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        # Countersubject: invert subject direction
        for note in subject:
            onset = note.start + entries[-1][0] + self.delay_beats
            if onset >= duration:
                break
            inverted_pitch = note.pitch - (note.pitch - (low + high) // 2) * 2
            inverted_pitch = max(low, min(high, inverted_pitch))
            vel = max(1, min(127, note.velocity - 15))
            notes.append(NoteInfo(
                pitch=inverted_pitch, start=round(onset, 6),
                duration=note.duration, velocity=vel,
            ))
        return notes

    # ------------------------------------------------------------------
    # Follower configs
    # ------------------------------------------------------------------

    def _follower_configs(self, key: Scale) -> list[_FollowerCfg]:
        configs: list[_FollowerCfg] = []
        for i in range(self.num_followers):
            ivl = self._follower_interval(i)
            delay = self.delay_beats * (i + 1)
            configs.append(_FollowerCfg(interval=ivl, delay=delay, index=i))
        return configs

    def _follower_interval(self, idx: int) -> int:
        if idx == 0:
            return self.interval
        if idx == 1:
            offset = 7 if self.interval < 7 else 5
            return self.interval + offset
        return self.interval + _OCTAVE

    # ------------------------------------------------------------------
    # Lead melody
    # ------------------------------------------------------------------

    def _generate_lead(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None,
    ) -> list[NoteInfo]:
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2
        prev = context.prev_pitch if context and context.prev_pitch is not None else anchor

        if self.canon_type == "fugue":
            # 1. Generate core subject
            subject_events = self._build_events(self.subject_length, self.lead_rhythm)
            subject_notes = []
            for ev in subject_events:
                chord = chord_at(chords, ev.onset)
                pitch = _pick_lead_pitch(chord or chords[0], key, prev, low, high)
                vel = int((70 + self.params.density * 30) * ev.velocity_factor)
                subject_notes.append(NoteInfo(pitch=pitch, start=round(ev.onset, 6), duration=ev.duration, velocity=max(1, min(127, vel))))
                prev = pitch
            
            # 2. Generate countersubject
            cs_events = self._build_events(self.subject_length, self.lead_rhythm)
            cs_notes = []
            for ev in cs_events:
                onset = ev.onset + self.subject_length
                chord = chord_at(chords, onset)
                pitch = _pick_lead_pitch(chord or chords[0], key, prev, low, high)
                vel = int((65 + self.params.density * 25) * ev.velocity_factor)
                cs_notes.append(NoteInfo(pitch=pitch, start=round(onset, 6), duration=ev.duration, velocity=max(1, min(127, vel))))
                prev = pitch

            notes = subject_notes + cs_notes
            
            # 3. Generate episodic / remainder up to duration_beats
            t_rem = 2 * self.subject_length
            if duration_beats > t_rem:
                rem_events = self._build_events(duration_beats - t_rem, self.lead_rhythm)
                for ev in rem_events:
                    onset = ev.onset + t_rem
                    if onset >= duration_beats:
                        break
                    chord = chord_at(chords, onset)
                    pitch = _pick_lead_pitch(chord or chords[0], key, prev, low, high)
                    vel = int((60 + self.params.density * 25) * ev.velocity_factor)
                    notes.append(NoteInfo(pitch=pitch, start=round(onset, 6), duration=ev.duration, velocity=max(1, min(127, vel))))
                    prev = pitch
            return notes

        events = self._build_events(duration_beats, self.lead_rhythm)
        notes: list[NoteInfo] = []
        for ev in events:
            chord = chord_at(chords, ev.onset)
            if chord is None:
                continue
            pitch = _pick_lead_pitch(chord, key, prev, low, high)
            vel = int((70 + self.params.density * 30) * ev.velocity_factor)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ev.onset, 6),
                    duration=ev.duration,
                    velocity=max(1, min(127, vel)),
                )
            )
            prev = pitch
        return notes

    # ------------------------------------------------------------------
    # Follower generation
    # ------------------------------------------------------------------

    def _generate_follower(
        self,
        lead: list[NoteInfo],
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        cfg: _FollowerCfg,
    ) -> list[NoteInfo]:
        low = self.params.key_range_low
        high = self.params.key_range_high

        if self.canon_type == "fugue":
            follower_notes = []
            subject_notes = [n for n in lead if n.start < self.subject_length]
            cs_notes = [n for n in lead if self.subject_length <= n.start < 2 * self.subject_length]
            ep_notes = [n for n in lead if n.start >= 2 * self.subject_length]
            
            if cfg.index == 0:
                # Answer: plays subject shifted by subject_length, transposed by fifth
                for note in subject_notes:
                    onset = note.start + self.subject_length
                    if onset >= duration_beats:
                        break
                    pitch = _tonal_transpose(note.pitch, 7, key)
                    pitch = max(low, min(high, pitch))
                    chord = chord_at(chords, onset)
                    if chord is not None:
                        pitch = _ensure_consonance(pitch, note.pitch, chord, low, high)
                    follower_notes.append(NoteInfo(pitch=pitch, start=round(onset, 6), duration=note.duration, velocity=max(1, min(127, int(note.velocity * 0.85)))))
                
                # Plays countersubject next
                for note in cs_notes:
                    onset = note.start + self.subject_length
                    if onset >= duration_beats:
                        break
                    pitch = _free_imitation(note, chords, key, 0, onset)
                    pitch = max(low, min(high, pitch))
                    chord = chord_at(chords, onset)
                    if chord is not None:
                        pitch = _ensure_consonance(pitch, note.pitch, chord, low, high)
                    follower_notes.append(NoteInfo(pitch=pitch, start=round(onset, 6), duration=note.duration, velocity=max(1, min(127, int(note.velocity * 0.8)))))

                # Remainder
                for note in ep_notes:
                    onset = note.start + self.subject_length
                    if onset >= duration_beats:
                        break
                    pitch = _free_imitation(note, chords, key, -5, onset)
                    pitch = max(low, min(high, pitch))
                    chord = chord_at(chords, onset)
                    if chord is not None:
                        pitch = _ensure_consonance(pitch, note.pitch, chord, low, high)
                    follower_notes.append(NoteInfo(pitch=pitch, start=round(onset, 6), duration=note.duration, velocity=max(1, min(127, int(note.velocity * 0.75)))))
            
            elif cfg.index == 1:
                # Voice 3: Augmentation entry (plays subject at half speed / augmented)
                aug_delay = 1.5 * self.subject_length
                for note in subject_notes:
                    onset = note.start * self.augmentation + aug_delay
                    if onset >= duration_beats:
                        break
                    pitch = _tonal_transpose(note.pitch, -12, key)
                    pitch = max(low, min(high, pitch))
                    chord = chord_at(chords, onset)
                    if chord is not None:
                        pitch = _ensure_consonance(pitch, note.pitch, chord, low, high)
                    follower_notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=note.duration * self.augmentation,
                        velocity=max(1, min(127, int(note.velocity * 0.8))),
                    ))
            
            else:
                # Voice 4: Stretto entry (enters very early, e.g. delay of only 0.5 * subject_length)
                stretto_delay = 0.5 * self.subject_length
                for note in subject_notes:
                    onset = note.start + stretto_delay
                    if onset >= duration_beats:
                        break
                    pitch = _tonal_transpose(note.pitch, 12, key)
                    pitch = max(low, min(high, pitch))
                    chord = chord_at(chords, onset)
                    if chord is not None:
                        pitch = _ensure_consonance(pitch, note.pitch, chord, low, high)
                    follower_notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=note.duration,
                        velocity=max(1, min(127, int(note.velocity * 0.75))),
                    ))
            return follower_notes

        notes: list[NoteInfo] = []
        for note in lead:
            onset = note.start + cfg.delay
            if onset >= duration_beats:
                break
            pitch = self._follower_pitch(note, lead, chords, key, cfg, onset)
            pitch = max(low, min(high, pitch))

            chord = chord_at(chords, onset)
            if chord is not None:
                pitch = _ensure_consonance(pitch, note.pitch, chord, low, high)

            vel = max(1, min(127, int(note.velocity * (0.9 - cfg.index * 0.05))))
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=note.duration,
                    velocity=vel,
                )
            )
        return notes

    def _follower_pitch(
        self,
        note: NoteInfo,
        lead: list[NoteInfo],
        chords: list[ChordLabel],
        key: Scale,
        cfg: _FollowerCfg,
        onset: float,
    ) -> int:
        ct = self.canon_type
        if ct == "strict":
            return note.pitch + cfg.interval
        if ct == "tonal":
            return _tonal_transpose(note.pitch, cfg.interval, key)
        if ct == "contrary":
            return _contrary_pitch(note, lead, cfg.interval)
        return _free_imitation(note, chords, key, cfg.interval, onset)

    # ------------------------------------------------------------------
    # Rhythm
    # ------------------------------------------------------------------

    def _build_events(
        self,
        duration_beats: float,
        rhythm: RhythmGenerator | None,
    ) -> list[RhythmEvent]:
        if rhythm is not None:
            return rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.45))
            t += 0.5
        return events


# ---------------------------------------------------------------------------
# Pure pitch-selection functions
# ---------------------------------------------------------------------------


def _pick_lead_pitch(
    chord: ChordLabel,
    key: Scale,
    prev: int,
    low: int,
    high: int,
) -> int:
    pcs = chord.pitch_classes()
    degs = key.degrees()

    if random.random() < 0.5 and pcs:
        pc = random.choice(pcs)
    elif degs:
        pc = random.choice(degs)
    else:
        pc = chord.root

    step = random.choice([-3, -2, -1, -1, 1, 1, 2, 3])
    target = prev + step
    pitch = nearest_pitch(int(pc), target)
    return max(low, min(high, pitch))


def _tonal_transpose(pitch: int, semitones: int, key: Scale) -> int:
    degs = key.degrees()
    if not degs:
        return pitch + semitones

    pc = pitch % _OCTAVE
    deg_idx = _find_scale_degree(pc, degs)
    if deg_idx is None:
        return pitch + semitones

    degree_shift = round(semitones / 2)
    new_idx = (deg_idx + degree_shift) % len(degs)
    new_pc = int(degs[new_idx])

    shift = (new_pc - pc) % _OCTAVE
    if shift > 6:
        shift -= _OCTAVE
    return pitch + shift


def _find_scale_degree(pc: int, degs: list) -> int | None:
    for i, d in enumerate(degs):
        if abs(int(d) - pc) < 2:
            return i
    return None


def _contrary_pitch(
    note: NoteInfo,
    lead: list[NoteInfo],
    interval: int,
) -> int:
    direction = 1
    for i, ln in enumerate(lead):
        if abs(ln.start - note.start) < 0.01 and i > 0:
            prev_lead = lead[i - 1]
            direction = 1 if note.pitch < prev_lead.pitch else -1
            break
    base = note.pitch + interval
    contrary = direction * random.choice([2, 3, 4, 5])
    return base - contrary


def _free_imitation(
    note: NoteInfo,
    chords: list[ChordLabel],
    key: Scale,
    interval: int,
    onset: float,
) -> int:
    chord = chord_at(chords, onset)
    if chord is None:
        return note.pitch + interval

    base = note.pitch + interval
    pcs = chord.pitch_classes()
    if pcs:
        nearest_pc = min(pcs, key=lambda p: abs(int(p) - (base % _OCTAVE)))
        return nearest_pitch(int(nearest_pc), base)
    return base


def _ensure_consonance(
    follower: int,
    lead: int,
    chord: ChordLabel,
    low: int,
    high: int,
) -> int:
    ivl = abs(follower - lead) % _OCTAVE
    if ivl in _STRONG_CONSONANT:
        return follower

    pcs = chord.pitch_classes()
    best = follower
    best_dist = 999
    for pc in pcs:
        cand = nearest_pitch(int(pc), follower)
        if low <= cand <= high:
            iv = abs(cand - lead) % _OCTAVE
            if iv in _CONSONANT:
                dist = abs(cand - follower)
                if dist < best_dist:
                    best_dist = dist
                    best = cand
    return best
