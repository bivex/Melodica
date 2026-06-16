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
generators/electronic_drums.py — Electronic drum machine patterns.

Layer: Application / Domain
Style: House, techno, electro, synthwave, trap.

Produces drum patterns using classic electronic drum machine kits.
Supports 909, 808, CR-78, and LinnDrum style kits with
characteristic patterns and optional sidechain ducking simulation.

Drum map (MIDI):
    kick=36, snare=38, hh_closed=42, hh_open=46,
    clap=39, tom_low=41, tom_mid=45, tom_high=50,
    crash=49, ride=51, rim=37
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from melodica.generators import GeneratorParams, PhraseGenerator

if TYPE_CHECKING:
    from melodica.rhythm.groove_template import GrooveTemplate
from melodica.generators._postprocess import post_process_808
from melodica.rhythm import RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, SectionRole
from melodica.utils import nearest_pitch, chord_at


KICK = 36
SNARE = 38
HH_CLOSED = 42
HH_OPEN = 46
CLAP = 39
TOM_LOW = 41
TOM_MID = 45
TOM_HIGH = 50
CRASH = 49
RIM = 37
COWBELL = 56

KIT_CHARACTER: dict[str, dict] = {
    "909": {"kick_vel": 115, "snare_vel": 110, "hat_vel": 70, "use_clap": True},
    "808": {"kick_vel": 120, "snare_vel": 95, "hat_vel": 60, "use_clap": False},
    "cr78": {"kick_vel": 95, "snare_vel": 85, "hat_vel": 55, "use_clap": False},
    "linn": {"kick_vel": 110, "snare_vel": 108, "hat_vel": 65, "use_clap": True},
}

PATTERN_DEFS: dict[str, list[tuple[int, float, int, float]]] = {
    "four_on_floor": [
        (KICK, 0.0, 115, 0.3),
        (HH_CLOSED, 0.5, 65, 0.12),
        (KICK, 1.0, 110, 0.3),
        (HH_CLOSED, 1.5, 60, 0.12),
        (KICK, 2.0, 115, 0.3),
        (HH_CLOSED, 2.5, 65, 0.12),
        (KICK, 3.0, 110, 0.3),
        (HH_CLOSED, 3.5, 60, 0.12),
    ],
    "breakbeat": [
        (KICK, 0.0, 115, 0.3),
        (HH_CLOSED, 0.0, 65, 0.1),
        (HH_CLOSED, 0.5, 50, 0.1),
        (SNARE, 1.0, 110, 0.25),
        (HH_CLOSED, 1.0, 60, 0.1),
        (KICK, 1.5, 95, 0.25),
        (HH_CLOSED, 1.5, 50, 0.1),
        (KICK, 2.0, 110, 0.3),
        (HH_CLOSED, 2.0, 65, 0.1),
        (SNARE, 2.5, 90, 0.25),
        (HH_CLOSED, 2.75, 45, 0.1),
        (SNARE, 3.0, 100, 0.25),
        (KICK, 3.5, 90, 0.25),
        (HH_CLOSED, 3.5, 55, 0.1),
    ],
    "minimal": [
        (KICK, 0.0, 115, 0.35),
        (HH_CLOSED, 1.0, 60, 0.1),
        (KICK, 2.0, 110, 0.35),
        (HH_CLOSED, 3.0, 55, 0.1),
    ],
    "techno": [
        (KICK, 0.0, 120, 0.3),
        (HH_CLOSED, 0.25, 55, 0.08),
        (HH_CLOSED, 0.5, 60, 0.08),
        (HH_CLOSED, 0.75, 50, 0.08),
        (KICK, 1.0, 115, 0.3),
        (HH_CLOSED, 1.25, 55, 0.08),
        (HH_CLOSED, 1.5, 60, 0.08),
        (HH_CLOSED, 1.75, 50, 0.08),
        (KICK, 2.0, 120, 0.3),
        (CLAP, 2.0, 90, 0.2),
        (HH_CLOSED, 2.25, 55, 0.08),
        (HH_CLOSED, 2.5, 60, 0.08),
        (KICK, 3.0, 115, 0.3),
        (HH_CLOSED, 3.25, 55, 0.08),
        (HH_OPEN, 3.5, 65, 0.3),
        (HH_CLOSED, 3.75, 50, 0.08),
    ],
    "garage_2step": [
        (KICK, 0.0, 115, 0.3),
        (HH_CLOSED, 0.0, 70, 0.1),
        (HH_CLOSED, 0.5, 65, 0.1),
        (HH_CLOSED, 0.75, 75, 0.1),
        (SNARE, 1.0, 112, 0.2),
        (HH_CLOSED, 1.0, 68, 0.1),
        (HH_OPEN, 1.5, 80, 0.25),
        (RIM, 1.5, 60, 0.1),
        (KICK, 1.75, 95, 0.2),
        (KICK, 2.0, 110, 0.3),
        (HH_CLOSED, 2.0, 70, 0.1),
        (HH_CLOSED, 2.5, 65, 0.1),
        (HH_CLOSED, 2.75, 78, 0.1),
        (RIM, 2.75, 65, 0.1),
        (SNARE, 3.0, 115, 0.2),
        (HH_CLOSED, 3.0, 68, 0.1),
        (HH_OPEN, 3.5, 80, 0.25),
    ],
    "rnb_slowjam": [
        (KICK, 0.0, 115, 0.3),
        (HH_CLOSED, 0.0, 72, 0.12),
        (HH_CLOSED, 0.5, 58, 0.12),
        (SNARE, 1.0, 110, 0.25),
        (HH_CLOSED, 1.0, 70, 0.12),
        (KICK, 1.25, 90, 0.2),
        (HH_CLOSED, 1.5, 60, 0.12),
        (KICK, 2.0, 105, 0.3),
        (HH_CLOSED, 2.0, 72, 0.12),
        (KICK, 2.5, 95, 0.2),
        (HH_CLOSED, 2.5, 58, 0.12),
        (SNARE, 3.0, 112, 0.25),
        (HH_CLOSED, 3.0, 70, 0.12),
        (HH_CLOSED, 3.5, 62, 0.12),
        (RIM, 3.75, 60, 0.12),
    ],
    "afrobeats_bounce": [
        (KICK, 0.0, 115, 0.3),
        (HH_CLOSED, 0.0, 60, 0.1),
        (HH_CLOSED, 0.25, 50, 0.1),
        (HH_CLOSED, 0.5, 58, 0.1),
        (HH_CLOSED, 0.75, 50, 0.1),
        (RIM, 0.75, 95, 0.2),
        (HH_CLOSED, 1.0, 60, 0.1),
        (HH_CLOSED, 1.25, 50, 0.1),
        (HH_CLOSED, 1.5, 58, 0.1),
        (KICK, 1.5, 105, 0.3),
        (SNARE, 1.5, 105, 0.2),
        (HH_CLOSED, 1.75, 50, 0.1),
        (KICK, 2.0, 110, 0.3),
        (HH_CLOSED, 2.0, 60, 0.1),
        (HH_CLOSED, 2.25, 50, 0.1),
        (RIM, 2.25, 90, 0.2),
        (HH_CLOSED, 2.5, 58, 0.1),
        (HH_CLOSED, 2.75, 50, 0.1),
        (RIM, 2.75, 95, 0.2),
        (HH_CLOSED, 3.0, 60, 0.1),
        (SNARE, 3.0, 105, 0.2),
        (HH_CLOSED, 3.25, 50, 0.1),
        (HH_CLOSED, 3.5, 58, 0.1),
        (KICK, 3.5, 100, 0.3),
        (HH_CLOSED, 3.75, 50, 0.1),
    ],
    "trap_basic": [
        (KICK, 0.0, 120, 0.25),
        (HH_CLOSED, 0.0, 65, 0.1),
        (HH_CLOSED, 0.5, 55, 0.1),
        (SNARE, 1.0, 110, 0.2),
        (CLAP, 1.0, 85, 0.15),
        (HH_CLOSED, 1.0, 60, 0.1),
        (HH_CLOSED, 1.5, 50, 0.1),
        (KICK, 2.0, 115, 0.25),
        (HH_CLOSED, 2.0, 60, 0.1),
        (HH_CLOSED, 2.5, 50, 0.1),
        (SNARE, 3.0, 108, 0.2),
        (CLAP, 3.0, 82, 0.15),
        (HH_CLOSED, 3.0, 55, 0.1),
        (HH_CLOSED, 3.5, 48, 0.1),
    ],
    "trap_syncopated": [
        (KICK, 0.0, 125, 0.25),
        (HH_CLOSED, 0.0, 65, 0.1),
        (HH_CLOSED, 0.5, 50, 0.1),
        (SNARE, 1.0, 112, 0.2),
        (CLAP, 1.0, 85, 0.15),
        (HH_CLOSED, 1.5, 55, 0.1),
        (KICK, 1.5, 90, 0.2),
        (KICK, 2.0, 120, 0.25),
        (HH_CLOSED, 2.0, 60, 0.1),
        (HH_CLOSED, 2.5, 48, 0.1),
        (SNARE, 3.0, 108, 0.2),
        (CLAP, 3.0, 82, 0.15),
        (HH_CLOSED, 3.25, 52, 0.1),
        (KICK, 3.5, 85, 0.2),
        (HH_CLOSED, 3.75, 45, 0.1),
    ],
    "drill_basic": [
        (KICK, 0.0, 125, 0.25),
        (HH_CLOSED, 0.0, 60, 0.08),
        (HH_CLOSED, 0.33, 45, 0.08),
        (HH_CLOSED, 0.66, 48, 0.08),
        (SNARE, 1.0, 115, 0.2),
        (HH_CLOSED, 1.0, 58, 0.08),
        (KICK, 2.0, 115, 0.25),
        (HH_CLOSED, 2.0, 55, 0.08),
        (HH_CLOSED, 2.33, 48, 0.08),
        (HH_CLOSED, 2.66, 52, 0.08),
        (SNARE, 3.0, 112, 0.2),
        (HH_CLOSED, 3.0, 56, 0.08),
    ],
    "phonk_cowbell": [
        (KICK, 0.0, 120, 0.3),
        (COWBELL, 0.0, 80, 0.15),
        (HH_CLOSED, 0.5, 60, 0.08),
        (SNARE, 1.0, 110, 0.25),
        (COWBELL, 1.0, 75, 0.15),
        (CLAP, 1.0, 85, 0.15),
        (HH_CLOSED, 1.5, 50, 0.08),
        (COWBELL, 2.0, 82, 0.15),
        (KICK, 2.0, 115, 0.3),
        (HH_CLOSED, 2.5, 55, 0.08),
        (SNARE, 3.0, 108, 0.25),
        (COWBELL, 3.0, 78, 0.15),
        (CLAP, 3.0, 80, 0.15),
        (HH_CLOSED, 3.5, 48, 0.08),
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
class ElectronicDrumsGenerator(PhraseGenerator):
    """
    Electronic drum patterns (909/808 style).

    kit:
        "909", "808", "cr78", "linn"
    pattern:
        "four_on_floor", "breakbeat", "minimal", "techno",
        "garage_2step", "rnb_slowjam", "afrobeats_bounce"
    sidechain:
        If True, simulate sidechain ducking by reducing velocity on
        non-kick hits that coincide with kick onsets.
    """

    name: str = "Electronic Drums Generator"
    kit: str = "909"
    pattern: str = "four_on_floor"
    sidechain: bool = False
    rhythm: RhythmGenerator | None = None
    sidechain_depth: float = 0.0
    snare_delay: float = 0.0
    hihat_delay: float = 0.0
    groove_swing: float = 0.5
    swing_grid: float = 0.25
    choke_hats: bool = True
    ghost_snare_prob: float = 0.0
    ghost_ride_prob: float = 0.0
    section_type: SectionRole | str = SectionRole.VERSE
    auto_fills: bool = True
    groove_template: "GrooveTemplate | None" = None
    # 808 / transient upgrades
    transient_ducking: bool = False
    ducking_duration: float = 0.02
    envelope_gating: bool = True
    # Arrangement
    mute_boundaries: bool = False
    kick_less_verse: bool = False
    # CC10 hi-hat panning
    pan_mode: str = "off"  # off | alternate | sweep_lr | sweep_rl | mono | random | breathe | humanize
    pan_alternation_rate: float = 0.5
    pan_width: float = 0.20  # 0.0=narrow (no spread) → 1.0=full stereo width
    # Flam & drag rudiments
    flam_probability: float = 0.0
    drag_probability: float = 0.0
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        kit: str = "909",
        pattern: str = "four_on_floor",
        sidechain: bool = False,
        rhythm: RhythmGenerator | None = None,
        sidechain_depth: float = 0.0,
        snare_delay: float = 0.0,
        hihat_delay: float = 0.0,
        groove_swing: float = 0.5,
        swing_grid: float = 0.25,
        choke_hats: bool = True,
        ghost_snare_prob: float = 0.0,
        ghost_ride_prob: float = 0.0,
        section_type: SectionRole | str = SectionRole.VERSE,
        auto_fills: bool = True,
        groove_template: "GrooveTemplate | None" = None,
        transient_ducking: bool = False,
        ducking_duration: float = 0.02,
        envelope_gating: bool = True,
        mute_boundaries: bool = False,
        kick_less_verse: bool = False,
        pan_mode: str = "off",
        pan_alternation_rate: float = 0.5,
        flam_probability: float = 0.0,
        drag_probability: float = 0.0,
    ) -> None:
        super().__init__(params)
        self.kit = kit
        self.pattern = pattern
        self.sidechain = sidechain
        self.rhythm = rhythm
        self.sidechain_depth = sidechain_depth
        self.snare_delay = snare_delay
        self.hihat_delay = hihat_delay
        self.groove_swing = groove_swing
        self.swing_grid = swing_grid
        self.choke_hats = choke_hats
        self.ghost_snare_prob = ghost_snare_prob
        self.ghost_ride_prob = ghost_ride_prob
        self.section_type = section_type
        self.auto_fills = auto_fills
        self.groove_template = groove_template
        self.transient_ducking = transient_ducking
        self.ducking_duration = ducking_duration
        self.envelope_gating = envelope_gating
        self.mute_boundaries = mute_boundaries
        self.kick_less_verse = kick_less_verse
        self.pan_mode = pan_mode
        self.pan_alternation_rate = pan_alternation_rate
        self.pan_width = 0.20
        self.flam_probability = flam_probability
        self.drag_probability = drag_probability

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
        char = KIT_CHARACTER.get(self.kit, KIT_CHARACTER["909"])
        pattern_def = PATTERN_DEFS.get(self.pattern, PATTERN_DEFS["four_on_floor"])

        t = 0.0
        # Determine global velocity scaling
        if self.params.velocity_range:
            v_min, v_max = self.params.velocity_range
            scale_factor = ((v_min + v_max) / 2) / 100.0
        else:
            scale_factor = 0.8 + self.params.density * 0.4

        bar_idx = 0

        while t < duration_beats:
            is_final_bar = fills_enabled and duration_beats > 4.0 and (t >= duration_beats - 4.0)
            is_final_bar_mute = self.mute_boundaries and is_final_bar
            is_verse_start = (s_type == "verse" and bar_idx == 0 and self.kick_less_verse)

            for pitch, offset, base_vel, dur in pattern_def:
                if is_final_bar_mute and offset >= 2.0:
                    continue

                # Intro density: skip claps/rims, fold open hats into closed
                if s_type == "intro" and pitch in (CLAP, RIM):
                    continue
                if s_type == "intro" and pitch == HH_OPEN:
                    pitch = HH_CLOSED

                # Kick-less verse: suppress chord-onset kick on first verse bar
                if is_verse_start and pitch == KICK and offset < 0.15:
                    continue

                onset = t + offset
                if onset >= duration_beats:
                    continue
                vel = int(base_vel * scale_factor)
                # Kit character velocity adjustments
                if pitch == KICK:
                    vel = int(char["kick_vel"] * scale_factor)
                elif pitch == SNARE:
                    vel = int(char["snare_vel"] * scale_factor)
                elif pitch in (HH_CLOSED, HH_OPEN):
                    vel = int(char["hat_vel"] * scale_factor)
                elif pitch == CLAP and not char["use_clap"]:
                    pitch = SNARE
                    vel = int(char["snare_vel"] * scale_factor)
                else:
                    vel = int(base_vel * scale_factor)

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

            # Generate low-velocity snare ghost notes if requested (skip in intro and outro)
            if self.ghost_snare_prob > 0.0 and s_type not in ("intro", "outro"):
                for sub in [0.75, 1.75, 2.25, 2.75, 3.75]:
                    if is_final_bar and sub >= 2.0:
                        continue
                    if random.random() < self.ghost_snare_prob:
                        onset = t + sub
                        if onset < duration_beats:
                            notes.append(
                                NoteInfo(
                                    pitch=RIM if char.get("use_clap") else SNARE,
                                    start=round(onset, 6),
                                    duration=0.08,
                                    velocity=random.randint(22, 38),
                                )
                            )

            # Phrase-boundary transitions
            if is_final_bar:
                if s_type in ("chorus", "pre_chorus"):
                    # Accelerating crescendo snare and clap rolls
                    fill_notes = [
                        (SNARE, 2.0, 75, 0.12),
                        (SNARE, 2.5, 85, 0.12),
                        (SNARE, 3.0, 95, 0.08),
                        (CLAP, 3.0, 90, 0.08),
                        (SNARE, 3.25, 100, 0.08),
                        (SNARE, 3.5, 110, 0.05),
                        (CLAP, 3.5, 105, 0.05),
                        (SNARE, 3.625, 115, 0.05),
                        (SNARE, 3.75, 120, 0.05),
                        (CLAP, 3.75, 115, 0.05),
                        (SNARE, 3.875, 125, 0.05),
                    ]
                elif s_type in ("intro", "outro"):
                    # Soft fading shaker or rim shot (no kick)
                    fill_notes = [
                        (RIM, 2.0, 50, 0.12),
                        (HH_CLOSED, 2.5, 45, 0.08),
                        (RIM, 3.0, 40, 0.12),
                        (HH_CLOSED, 3.5, 30, 0.08),
                    ]
                else:  # "verse", "bridge", etc.
                    # Quick double-step kick rush + closed hat rolls
                    fill_notes = [
                        (KICK, 2.0, 100, 0.2),
                        (HH_CLOSED, 2.0, 80, 0.08),
                        (KICK, 2.5, 110, 0.2),
                        (KICK, 2.75, 115, 0.2),
                        (HH_CLOSED, 3.0, 85, 0.08),
                        (HH_CLOSED, 3.25, 90, 0.08),
                        (HH_CLOSED, 3.5, 95, 0.08),
                        (HH_CLOSED, 3.75, 100, 0.08),
                    ]

                for pitch, offset, vel, dur in fill_notes:
                    if pitch == CLAP and not char["use_clap"]:
                        pitch = SNARE

                    onset = t + offset
                    if onset < duration_beats:
                        notes.append(
                            NoteInfo(
                                pitch=pitch,
                                start=round(onset, 6),
                                duration=dur,
                                velocity=max(1, min(127, int(vel * scale_factor))),
                            )
                        )

            bar_idx += 1
            t += 4.0

        # 808 transient-ducking post-processing
        if self.transient_ducking and any(getattr(n, "articulation", None) == "808" for n in notes):
            from melodica.generators._postprocess import post_process_808
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
            if n.pitch == KICK:
                beat_in_bar = n.start % 4.0
                if abs(beat_in_bar) < 0.01 or abs(beat_in_bar - 2.0) < 0.01:
                    n.velocity = int(n.velocity * 1.12)
            elif n.pitch in (SNARE, CLAP):
                beat_in_bar = n.start % 4.0
                if abs(beat_in_bar - 1.0) < 0.01 or abs(beat_in_bar - 3.0) < 0.01:
                    n.velocity = int(n.velocity * 1.14)
            elif n.pitch in (HH_CLOSED, HH_OPEN):
                sub_pos = n.start % 1.0
                if abs(sub_pos - 0.5) < 0.01:
                    n.velocity = int(n.velocity * 0.85)
                elif abs(sub_pos - 0.25) < 0.01 or abs(sub_pos - 0.75) < 0.01:
                    n.velocity = int(n.velocity * 0.72)

            # Apply section-aware dynamic scaling
            mult = _get_section_multiplier(s_type, n.start, duration_beats)
            n.velocity = int(n.velocity * mult)

            n.velocity = max(1, min(127, n.velocity + random.randint(-4, 4)))

        # Apply swing, pocket timing, hi-hat choking, and sidechain ducking passes
        notes = self._apply_pro_features(notes)

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_flam_drag(self, notes: list[NoteInfo]) -> None:
        """Apply flam and drag rudiments in-place: add grace notes and shift parent hits."""
        grace_notes = []
        for n in notes:
            if n.pitch in (SNARE, TOM_LOW, TOM_MID, TOM_HIGH) and getattr(n, "articulation", None) != "grace":
                r_val = random.random()
                if r_val < self.drag_probability:
                    g1 = NoteInfo(pitch=n.pitch, start=n.start, duration=0.02, velocity=max(1, int(n.velocity * 0.30)), articulation="grace")
                    g2 = NoteInfo(pitch=n.pitch, start=n.start + 0.02, duration=0.02, velocity=max(1, int(n.velocity * 0.45)), articulation="grace")
                    grace_notes.extend([g1, g2])
                    n.start += 0.04
                elif r_val < self.drag_probability + self.flam_probability:
                    g1 = NoteInfo(pitch=n.pitch, start=n.start, duration=0.02, velocity=max(1, int(n.velocity * 0.40)), articulation="grace")
                    grace_notes.append(g1)
                    n.start += 0.03
        notes.extend(grace_notes)

    @staticmethod
    def _hat_pan_value(mode: str, alt_count: int, rate: float, width: float = 0.20) -> int:
        """Return a CC10 pan value (0-127) for a hi-hat note.

        Parameters
        ----------
        mode   : alternate | sweep_lr | sweep_rl | random | mono | off
        alt_count : sequential index of the current hi-hat hit (0-based)
        rate   : alternation rate (kept for API compat, not used here)
        width  : 0.0 = no spread (±0 CC units) → 1.0 = full stereo edge-to-edge (±63 CC)
        """
        spread = int(width * 63)   # max ± spread CC units around centre 64
        L = 64 - spread             # left bound
        R = 64 + spread             # right bound
        # For multi-step patterns, compute a 4-step sub-increment
        sub = min(3, int(spread // 32) * 4 or 4)   # 4 steps across the span
        step = (R - L) // max(sub - 1, 1)

        def _clamp(v: int) -> int:
            return min(R, max(L, v))

        if mode == "off":
            return 64
        elif mode == "mono":
            return 64
        elif mode == "alternate":
            return R if alt_count % 2 == 0 else L
        elif mode == "sweep_lr":
            # 52, 60, 68, 76  ← 4-step left-to-right climb
            target = L + (alt_count % sub) * step
            return _clamp(L + target) if L == R else _clamp(target)
        elif mode == "sweep_rl":
            # 76, 68, 60, 52  ← 4-step right-to-left
            target = R - (alt_count % sub) * step
            return _clamp(target)
        elif mode == "random":
            import random as _rnd
            # True random across full width (re-seeded each call for variety)
            _rnd.seed()
            return int(_rnd.uniform(L, R))
        elif mode == "breathe":
            # Sine LFO across hits — hi-hat breathes left-right
            import math as _math
            phase = (alt_count / 8) * 2 * _math.pi
            offset = int(_math.sin(phase) * spread)
            return max(1, min(127, 64 + offset))
        elif mode == "humanize":
            # Gaussian drift — subtle random micro-panning
            import random as _rnd
            drift = _rnd.gauss(0, spread * 0.4)
            return max(1, min(127, int(64 + drift)))
        else:
            return 64

    def _apply_pro_features(self, notes: list[NoteInfo]) -> list[NoteInfo]:
        # 0. Flam & drag rudiments (renders grace notes and shifts parent hits by 3-4 ms)
        self._render_flam_drag(notes)

        # 1. Swing / Groove Timing & Pocket Timing Offsets
        for n in notes:
            shift = 0.0

            # Apply groove template if present
            if self.groove_template is not None:
                frac = n.start % 1.0
                for slot in self.groove_template.slots:
                    if abs(frac - slot.position) < 0.05:
                        shift += slot.timing_offset * 0.01
                        n.velocity = max(1, min(127, int(n.velocity * slot.velocity_factor)))
                        break
            elif self.groove_swing > 0.5 and self.swing_grid > 0:
                # Apply standard swing delay
                swing_delay = (self.groove_swing - 0.5) * 2.0 * (self.swing_grid / 2.0)
                grid_pos = n.start % (2.0 * self.swing_grid)
                is_offbeat = abs(grid_pos - self.swing_grid) < 0.01
                if is_offbeat:
                    shift += swing_delay

            # Apply pocket delays
            if n.pitch in (SNARE, CLAP, RIM):
                shift += self.snare_delay
            elif n.pitch in (HH_CLOSED, HH_OPEN):
                shift += self.hihat_delay

            n.start = round(max(0.0, n.start + shift), 6)

        # 1.5. Physical Hand-to-Foot Coordination Limits Safeguard
        hand_struck_pitches = {
            SNARE,
            CLAP,
            HH_CLOSED,
            HH_OPEN,
            TOM_LOW,
            TOM_MID,
            TOM_HIGH,
            CRASH,
            RIM,
            51,
        }
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
            SNARE: 1,
            CLAP: 1,
            CRASH: 2,
            TOM_HIGH: 3,
            TOM_MID: 3,
            TOM_LOW: 3,
            RIM: 4,
            HH_OPEN: 5,
            HH_CLOSED: 5,
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

        # 2. Hi-Hat Auto-Choking
        if self.choke_hats:
            notes.sort(key=lambda x: x.start)
            for i, n in enumerate(notes):
                if n.pitch == HH_OPEN:
                    for j in range(i + 1, len(notes)):
                        next_n = notes[j]
                        if next_n.start >= n.start + n.duration:
                            break
                        if next_n.pitch == HH_CLOSED:
                            n.duration = round(max(0.01, next_n.start - n.start - 0.005), 6)
                            break

        # 3. CC10 Hi-Hat Stereo Panning
        if self.pan_mode != "off":
            _hat_alt = 0
            for n in notes:
                if n.pitch in (HH_CLOSED, HH_OPEN):
                    n.expression = {**(n.expression or {}), "cc10": self._hat_pan_value(self.pan_mode, _hat_alt, self.pan_alternation_rate, self.pan_width)}
                    _hat_alt += 1

        # 4. Post-Process Sidechain / Transient Ducking Pass
        depth = self.sidechain_depth
        if self.sidechain and depth == 0.0:
            depth = 0.5

        if depth > 0.0:
            kick_onsets = [n.start for n in notes if n.pitch == KICK and getattr(n, "articulation", None) != "808"]
            for n in notes:
                if n.pitch != KICK:
                    for kick_start in kick_onsets:
                        if abs(n.start - kick_start) < 0.20 or (n.start <= kick_start < n.start + n.duration):
                            n.velocity = max(1, int(n.velocity * (1.0 - depth)))
                            break

        return notes
