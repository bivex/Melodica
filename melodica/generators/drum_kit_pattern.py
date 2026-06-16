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
generators/drum_kit_pattern.py — Full drum kit pattern generator across genres.

Layer: Application / Domain
Style: Rock, jazz, latin, funk, hip-hop.

Produces bar-length drum patterns using General MIDI drum map pitches.
Each style has a characteristic kick/snare/hat pattern with optional fills.

Drum map (MIDI):
    kick=36, snare=38, hh_closed=42, hh_open=46,
    tom_low=41, tom_mid=45, tom_high=50, crash=49, ride=51
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.generators._postprocess import post_process_808
from melodica.rhythm import RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, SectionRole
from melodica.utils import nearest_pitch, chord_at


KICK = 36
SNARE = 38
HH_CLOSED = 42
HH_OPEN = 46
TOM_LOW = 41
TOM_MID = 45
TOM_HIGH = 50
CRASH = 49
RIDE = 51
CLAP = 39

STYLE_PATTERNS: dict[str, list[tuple[int, float, int]]] = {
    "rock": [
        (KICK, 0.0, 110),
        (HH_CLOSED, 0.0, 70),
        (HH_CLOSED, 0.5, 55),
        (SNARE, 1.0, 110),
        (HH_CLOSED, 1.0, 65),
        (HH_CLOSED, 1.5, 55),
        (KICK, 2.0, 105),
        (HH_CLOSED, 2.0, 70),
        (HH_CLOSED, 2.5, 55),
        (SNARE, 3.0, 110),
        (HH_CLOSED, 3.0, 65),
        (KICK, 3.5, 95),
        (HH_CLOSED, 3.5, 55),
    ],
    "jazz": [
        (KICK, 0.0, 85),
        (RIDE, 0.0, 70),
        (RIDE, 0.5, 60),
        (SNARE, 0.75, 50),
        (RIDE, 1.0, 70),
        (RIDE, 1.5, 60),
        (KICK, 1.5, 80),
        (SNARE, 1.75, 50),
        (RIDE, 2.0, 70),
        (RIDE, 2.5, 60),
        (KICK, 2.5, 85),
        (SNARE, 2.75, 50),
        (RIDE, 3.0, 70),
        (RIDE, 3.5, 60),
        (KICK, 3.5, 80),
    ],
    "latin": [
        (KICK, 0.0, 100),
        (HH_CLOSED, 0.0, 65),
        (SNARE, 0.5, 80),
        (HH_CLOSED, 0.5, 55),
        (KICK, 1.0, 95),
        (HH_CLOSED, 1.0, 65),
        (SNARE, 1.5, 80),
        (HH_CLOSED, 1.5, 55),
        (KICK, 2.0, 100),
        (HH_CLOSED, 2.0, 65),
        (SNARE, 2.5, 85),
        (HH_CLOSED, 2.5, 55),
        (KICK, 3.0, 95),
        (HH_CLOSED, 3.0, 65),
        (SNARE, 3.5, 80),
        (HH_CLOSED, 3.5, 55),
    ],
    "funk": [
        (KICK, 0.0, 110),
        (KICK, 2.0, 105),
        (KICK, 2.75, 95),
        (SNARE, 1.0, 110),
        (SNARE, 1.75, 50),
        (SNARE, 2.25, 45),
        (SNARE, 3.0, 112),
        (SNARE, 3.75, 55),
        (HH_CLOSED, 0.0, 75),
        (HH_CLOSED, 0.25, 50),
        (HH_CLOSED, 0.5, 65),
        (HH_CLOSED, 0.75, 52),
        (HH_CLOSED, 1.0, 72),
        (HH_CLOSED, 1.25, 48),
        (HH_CLOSED, 1.5, 68),
        (HH_CLOSED, 1.75, 50),
        (HH_CLOSED, 2.0, 75),
        (HH_CLOSED, 2.25, 52),
        (HH_CLOSED, 2.5, 65),
        (HH_CLOSED, 2.75, 48),
        (HH_CLOSED, 3.0, 72),
        (HH_CLOSED, 3.25, 50),
        (HH_CLOSED, 3.5, 68),
        (HH_CLOSED, 3.75, 52),
    ],
    "hiphop": [
        (KICK, 0.0, 115),
        (SNARE, 1.0, 110),
        (KICK, 2.0, 110),
        (SNARE, 3.0, 105),
        (HH_CLOSED, 0.0, 60),
        (HH_CLOSED, 1.0, 55),
        (HH_CLOSED, 2.0, 60),
        (HH_CLOSED, 3.0, 55),
    ],
}


def _get_section_multiplier(s_type: SectionRole | str, onset: float, total_beats: float) -> float:
    if s_type == "intro":
        return 0.75
    elif s_type == "verse":
        return 0.90
    elif s_type == "chorus":
        return 1.05
    elif s_type == "bridge":
        return 0.92
    elif s_type == "pre_chorus":
        # crescendo ramp: 0.85 -> 1.05
        ratio = onset / max(1.0, total_beats)
        return 0.85 + (1.05 - 0.85) * min(1.0, max(0.0, ratio))
    elif s_type == "outro":
        # decrescendo ramp: 0.85 -> 0.50
        ratio = onset / max(1.0, total_beats)
        return 0.85 - (0.85 - 0.50) * min(1.0, max(0.0, ratio))
    return 0.90  # Default to verse


@dataclass
class DrumKitPatternGenerator(PhraseGenerator):
    """
    Full drum kit patterns across genres.

    style:
        "rock", "jazz", "latin", "funk", "hiphop"
    hihat_pattern:
        "eighth", "sixteenth", "open"
    fill_frequency:
        Probability of a fill at the end of a bar (0.0–1.0).
    """

    name: str = "Drum Kit Pattern Generator"
    style: str = "rock"
    hihat_pattern: str = "eighth"
    fill_frequency: float = 0.2
    rhythm: RhythmGenerator | None = None
    sidechain_depth: float = 0.0
    snare_delay: float = 0.0
    hihat_delay: float = 0.0
    groove_swing: float = 0.5
    swing_grid: float = 0.25
    choke_hats: bool = True
    section_type: SectionRole | str = SectionRole.VERSE
    auto_fills: bool = True
    groove_template: any = None
    flam_probability: float = 0.0
    drag_probability: float = 0.0
    # 808 transient-ducking upgrades
    transient_ducking: bool = False
    ducking_duration: float = 0.02
    envelope_gating: bool = True
    # Arrangement upgrades
    mute_boundaries: bool = False
    kick_less_verse: bool = False
    # CC10 panning
    pan_mode: str = "off"
    pan_alternation_rate: float = 0.5
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        style: str = "rock",
        hihat_pattern: str = "eighth",
        fill_frequency: float = 0.2,
        rhythm: RhythmGenerator | None = None,
        sidechain_depth: float = 0.0,
        snare_delay: float = 0.0,
        hihat_delay: float = 0.0,
        groove_swing: float = 0.5,
        swing_grid: float = 0.25,
        choke_hats: bool = True,
        section_type: SectionRole | str = SectionRole.VERSE,
        auto_fills: bool = True,
        groove_template: any = None,
        flam_probability: float = 0.0,
        drag_probability: float = 0.0,
        transient_ducking: bool = False,
        ducking_duration: float = 0.02,
        envelope_gating: bool = True,
        mute_boundaries: bool = False,
        kick_less_verse: bool = False,
        pan_mode: str = "off",
        pan_alternation_rate: float = 0.5,
    ) -> None:
        super().__init__(params)
        self.style = style
        self.hihat_pattern = hihat_pattern
        self.fill_frequency = max(0.0, min(1.0, fill_frequency))
        self.rhythm = rhythm
        self.sidechain_depth = sidechain_depth
        self.snare_delay = snare_delay
        self.hihat_delay = hihat_delay
        self.groove_swing = groove_swing
        self.swing_grid = swing_grid
        self.choke_hats = choke_hats
        self.section_type = section_type
        self.auto_fills = auto_fills
        self.groove_template = groove_template
        self.flam_probability = max(0.0, min(1.0, flam_probability))
        self.drag_probability = max(0.0, min(1.0, drag_probability))
        self.transient_ducking = transient_ducking
        self.ducking_duration = ducking_duration
        self.envelope_gating = envelope_gating
        self.mute_boundaries = mute_boundaries
        self.kick_less_verse = kick_less_verse
        self.pan_mode = pan_mode
        self.pan_alternation_rate = pan_alternation_rate

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        # Resolve section_type and auto_fills from context if available, otherwise use instance defaults
        s_type = context.section_role if context else self.section_type
        fills_enabled = getattr(context, "auto_fills", self.auto_fills)

        notes: list[NoteInfo] = []
        last_chord = chords[-1]
        bar_idx = 0
        t = 0.0

        bar_idx = 0
        while t < duration_beats:
            is_actual_final_bar = (duration_beats > 4.0 and (t >= duration_beats - 4.0))
            is_final_bar = fills_enabled and is_actual_final_bar
            is_final_bar_mute = self.mute_boundaries and is_actual_final_bar
            is_verse_start = (s_type == "verse" and bar_idx == 0 and self.kick_less_verse)

            pattern = STYLE_PATTERNS.get(self.style, STYLE_PATTERNS["rock"])
            for pitch, offset, vel in pattern:
                if is_final_bar_mute and offset >= 2.0:
                    continue  # Mute all percussion in second half of final bar for drop contrast

                # Kick-less verse: suppress kick note on chord downbeat of first verse bar
                if is_verse_start and pitch == KICK and offset < 0.15:
                    continue

                onset = t + offset
                if onset < duration_beats:
                    dur = 0.12 if pitch in (HH_CLOSED, HH_OPEN, RIDE) else 0.25
                    articulation = "808" if (self.transient_ducking and pitch == KICK) else None
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(onset, 6),
                            duration=dur,
                            velocity=max(1, min(127, vel)),
                            articulation=articulation,
                        )
                    )

            if is_verse_start:
                is_verse_start = False

            # Extra hi-hat subdivision (skip in intro and outro sections to simplify density)
            if s_type not in ("intro", "outro"):
                if self.hihat_pattern == "sixteenth":
                    for sub in [0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75]:
                        if is_final_bar and sub >= 2.0:
                            continue
                        onset = t + sub
                        if onset < duration_beats:
                            notes.append(
                                NoteInfo(
                                    pitch=HH_CLOSED,
                                    start=round(onset, 6),
                                    duration=0.08,
                                    velocity=random.randint(40, 55),
                                )
                            )
                elif self.hihat_pattern == "open":
                    for sub in [0.5, 1.5, 2.5, 3.5]:
                        if is_final_bar and sub >= 2.0:
                            continue
                        onset = t + sub
                        if onset < duration_beats:
                            notes.append(
                                NoteInfo(
                                    pitch=HH_OPEN,
                                    start=round(onset, 6),
                                    duration=0.4,
                                    velocity=random.randint(55, 70),
                                )
                            )

            # Phrase-boundary transitions
            if is_final_bar and not is_final_bar_mute:
                if s_type in ("chorus", "pre_chorus"):
                    # Heavy descending 16th tom fills + snare double punch + crash
                    fill_notes = [
                        (TOM_HIGH, 2.0, 105, 0.2),
                        (TOM_HIGH, 2.25, 105, 0.2),
                        (TOM_MID, 2.5, 110, 0.2),
                        (TOM_MID, 2.75, 110, 0.2),
                        (TOM_LOW, 3.0, 115, 0.2),
                        (TOM_LOW, 3.25, 115, 0.2),
                        (SNARE, 3.5, 120, 0.25),
                        (SNARE, 3.75, 120, 0.25),
                        (CRASH, 3.85, 120, 0.6),
                    ]
                elif s_type in ("intro", "outro"):
                    # Sparse fill
                    fill_notes = [
                        (RIDE, 2.0, 55, 0.15),
                        (RIDE, 3.0, 50, 0.3),
                        (TOM_LOW, 3.75, 45, 0.15),
                    ]
                else:  # "verse", "bridge", etc.
                    # Tasteful syncopated snare ghost roll + tom
                    fill_notes = [
                        (SNARE, 2.0, 80, 0.15),
                        (HH_OPEN, 2.25, 70, 0.2),
                        (SNARE, 2.5, 45, 0.1),
                        (SNARE, 2.75, 48, 0.1),
                        (TOM_MID, 3.0, 95, 0.2),
                        (SNARE, 3.25, 50, 0.1),
                        (SNARE, 3.5, 90, 0.15),
                        (TOM_LOW, 3.75, 100, 0.2),
                    ]

                for pitch, offset, vel, dur in fill_notes:
                    onset = t + offset
                    if onset < duration_beats:
                        notes.append(
                            NoteInfo(
                                pitch=pitch,
                                start=round(onset, 6),
                                duration=dur,
                                velocity=max(1, min(127, vel)),
                            )
                        )
            # Normal fill at end of bar (only if not phrase final bar or auto_fills is disabled)
            elif random.random() < self.fill_frequency and not is_final_bar_mute:
                fill_start = t + 3.0
                for i, tom in enumerate([TOM_HIGH, TOM_MID, TOM_LOW]):
                    onset = fill_start + i * 0.25
                    if onset < duration_beats:
                        notes.append(
                            NoteInfo(
                                pitch=tom,
                                start=round(onset, 6),
                                duration=0.2,
                                velocity=random.randint(80, 110),
                            )
                        )

            bar_idx += 1
            t += 4.0

        # 808 transient-ducking post-processing
        if self.transient_ducking and any(getattr(n, "articulation", None) == "808" for n in notes):
            notes = post_process_808(
                notes,
                chords,
                duration_beats,
                slide_curve="linear",
                transient_ducking=True,
                ducking_duration=self.ducking_duration,
                envelope_gating=self.envelope_gating,
            )

        # Pro-grade dynamic velocity and transient scaling
        for n in notes:
            # 1. Structural transient accentuation
            if n.pitch == KICK:
                beat_in_bar = n.start % 4.0
                if abs(beat_in_bar) < 0.01 or abs(beat_in_bar - 2.0) < 0.01:
                    n.velocity = int(n.velocity * 1.12)
            elif n.pitch == SNARE:
                beat_in_bar = n.start % 4.0
                if abs(beat_in_bar - 1.0) < 0.01 or abs(beat_in_bar - 3.0) < 0.01:
                    n.velocity = int(n.velocity * 1.15)
            # 2. Hi-hat/Ride dynamics (breathing offbeats)
            elif n.pitch in (HH_CLOSED, HH_OPEN, RIDE):
                sub_pos = n.start % 1.0
                if abs(sub_pos - 0.5) < 0.01:
                    n.velocity = int(n.velocity * 0.85)
                elif abs(sub_pos - 0.25) < 0.01 or abs(sub_pos - 0.75) < 0.01:
                    n.velocity = int(n.velocity * 0.72)

            # Apply section-aware dynamic scaling
            mult = _get_section_multiplier(s_type, n.start, duration_beats)
            n.velocity = int(n.velocity * mult)

            n.velocity = max(1, min(127, n.velocity + random.randint(-4, 4)))

        # Apply swing, micro-timing pocket delays, hi-hat choking, and sidechain ducking passes
        notes = self._apply_pro_features(notes)

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    @staticmethod
    def _hat_pan_value(mode: str, alt_count: int, spread: int = 12) -> int:
        """Return a CC10 pan value for a hi-hat note."""
        r = alt_count % 4
        if mode == "off":
            return 64
        elif mode == "mono":
            return 64
        elif mode == "alternate":
            return 76 if (alt_count % 2) == 0 else 52
        elif mode == "sweep_lr":
            return min(76, max(52, 52 + r * 8))
        elif mode == "sweep_rl":
            return min(76, max(52, 76 - r * 8))
        elif mode == "breathe":
            # Sine LFO across hits — hi-hat "breathes" left-right
            phase = (alt_count / 8) * 2 * math.pi
            offset = int(math.sin(phase) * spread)
            return max(1, min(127, 64 + offset))
        elif mode == "humanize":
            # Gaussian drift — subtle random micro-panning
            drift = random.gauss(0, spread * 0.4)
            return max(1, min(127, int(64 + drift)))
        return 64

    def _apply_pro_features(self, notes: list[NoteInfo]) -> list[NoteInfo]:
        # 0. Flam & Drag Rudiments
        grace_notes = []
        for n in notes:
            if n.pitch in (SNARE, TOM_LOW, TOM_MID, TOM_HIGH) and getattr(n, "articulation", None) != "grace":
                r_val = random.random()
                if r_val < self.drag_probability:
                    g1 = NoteInfo(pitch=n.pitch, start=n.start, duration=0.02, velocity=max(1, int(n.velocity * 0.30)), articulation="grace")
                    grace_notes.append(g1)
                    n.start += 0.02
                elif r_val < self.drag_probability + self.flam_probability:
                    g1 = NoteInfo(pitch=n.pitch, start=n.start, duration=0.02, velocity=max(1, int(n.velocity * 0.40)), articulation="grace")
                    grace_notes.append(g1)
                    n.start += 0.03
        notes.extend(grace_notes)

        # 1. Swing / Groove Timing & Pocket Timing Offsets
        for n in notes:
            shift = 0.0
            if self.groove_template is not None:
                frac = n.start % 1.0
                for slot in self.groove_template.slots:
                    if abs(frac - slot.position) < 0.05:
                        shift += slot.timing_offset * 0.01
                        n.velocity = max(1, min(127, int(n.velocity * slot.velocity_factor)))
                        break
            elif self.groove_swing > 0.5 and self.swing_grid > 0:
                swing_delay = (self.groove_swing - 0.5) * 2.0 * (self.swing_grid / 2.0)
                grid_pos = n.start % (2.0 * self.swing_grid)
                is_offbeat = abs(grid_pos - self.swing_grid) < 0.01
                if is_offbeat:
                    shift += swing_delay
            if n.pitch in (SNARE, TOM_LOW, TOM_MID, TOM_HIGH):
                shift += self.snare_delay
            elif n.pitch in (HH_CLOSED, HH_OPEN, RIDE):
                shift += self.hihat_delay
            n.start = round(max(0.0, n.start + shift), 6)

        # 2. Physical Hand-to-Foot Coordination Limits Safeguard (+ CLAP + RIDE)
        hand_struck_pitches = {SNARE, CLAP, HH_CLOSED, HH_OPEN, TOM_LOW, TOM_MID, TOM_HIGH, CRASH, RIDE}
        notes.sort(key=lambda x: x.start)
        groups: list[list[NoteInfo]] = []
        for n in notes:
            added = False
            for group in groups:
                if abs(n.start - group[0].start) < 0.01:
                    group.append(n)
                    added = True
                    break
            if not added:
                groups.append([n])
        priority_map = {
            SNARE: 1, CLAP: 1, CRASH: 2,
            TOM_HIGH: 3, TOM_MID: 3, TOM_LOW: 3,
            RIDE: 4, HH_OPEN: 5, HH_CLOSED: 5,
        }
        filtered_notes = []
        for group in groups:
            hand_struck = [n for n in group if n.pitch in hand_struck_pitches]
            other = [n for n in group if n.pitch not in hand_struck_pitches]
            if len(hand_struck) > 2:
                hand_struck.sort(key=lambda n: priority_map.get(n.pitch, 99))
                filtered_notes.extend(hand_struck[:2])
                filtered_notes.extend(other)
            else:
                filtered_notes.extend(group)
        notes = filtered_notes

        # 3. Hi-Hat Auto-Choking (RIDE also chokes open hat)
        if self.choke_hats:
            notes.sort(key=lambda x: x.start)
            for i, n in enumerate(notes):
                if n.pitch == HH_OPEN:
                    for j in range(i + 1, len(notes)):
                        next_n = notes[j]
                        if next_n.start >= n.start + n.duration:
                            break
                        if next_n.pitch in (HH_CLOSED, RIDE):
                            n.duration = round(max(0.01, next_n.start - n.start - 0.005), 6)
                            break

        # 4. CC10 Hi-Hat Stereo Panning
        if self.pan_mode != "off":
            _hat_alt = 0
            for n in notes:
                if n.pitch in (HH_CLOSED, HH_OPEN):
                    n.expression = {**(n.expression or {}), "cc10": self._hat_pan_value(self.pan_mode, _hat_alt)}
                    _hat_alt += 1

        # 5. Sidechain Ducking (restrict to real kicks, not tagged articulation="808")
        if self.sidechain_depth > 0.0:
            kick_onsets = [n.start for n in notes if n.pitch == KICK and getattr(n, "articulation", None) != "808"]
            for n in notes:
                if n.pitch != KICK:
                    for kick_start in kick_onsets:
                        if abs(n.start - kick_start) < 0.20 or (n.start <= kick_start < n.start + n.duration):
                            n.velocity = max(1, int(n.velocity * (1.0 - self.sidechain_depth)))
                            break

        return notes

