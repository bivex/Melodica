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
generators/trap_drums.py — Trap drum pattern generator.

Layer: Application / Domain
Style: Trap, hip-hop, drill, modern rap.

Trap drums feature:
  - Rapid hi-hat rolls (32nd notes, triplet rolls)
  - 808 sub-bass on beats 1 and 3
  - Snare on beats 2 and 4 (or displaced)
  - Sparse, booming kick patterns

Variants:
    "standard"  — classic trap pattern
    "drill"     — UK/NY drill (sliding 808, syncopated)
    "melodic"   — melodic trap (more hi-hat variation)
    "minimal"   — sparse, atmospheric trap
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


# GM-ish mapping
KICK = 36
SNARE = 38
HH_CLOSED = 42
HH_OPEN = 46
CLAP = 39
SUB_808 = 36  # Low C


def _get_section_multiplier(s_type: str, onset: float, total_beats: float) -> float:
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
class TrapDrumsGenerator(PhraseGenerator):
    """
    Trap drum pattern generator.

    variant:
        "standard", "drill", "melodic", "minimal"
    hat_roll_density:
        How many hi-hat rolls per bar (0.0–1.0).
    kick_pattern:
        "standard" (beats 1, 3), "syncopated" (displaced), "sparse" (beat 1 only)
    open_hat_probability:
        Probability of open hi-hat hits.
    clap_on_two:
        If True, clap on beat 2 (standard). If False, clap on beat 3.
    """

    name: str = "Trap Drums Generator"
    variant: str = "standard"
    hat_roll_density: float = 0.5
    kick_pattern: str = "standard"
    open_hat_probability: float = 0.2
    clap_on_two: bool = True
    rhythm: RhythmGenerator | None = None
    sidechain_depth: float = 0.6
    snare_delay: float = 0.0
    hihat_delay: float = 0.0
    groove_swing: float = 0.5
    swing_grid: float = 0.25
    choke_hats: bool = True
    ghost_snare_prob: float = 0.3
    section_type: str = "verse"
    auto_fills: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "standard",
        hat_roll_density: float = 0.5,
        kick_pattern: str = "standard",
        open_hat_probability: float = 0.2,
        clap_on_two: bool = True,
        rhythm: RhythmGenerator | None = None,
        sidechain_depth: float = 0.6,
        snare_delay: float = 0.0,
        hihat_delay: float = 0.0,
        groove_swing: float = 0.5,
        swing_grid: float = 0.25,
        choke_hats: bool = True,
        ghost_snare_prob: float = 0.3,
        section_type: str = "verse",
        auto_fills: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.hat_roll_density = max(0.0, min(1.0, hat_roll_density))
        self.kick_pattern = kick_pattern
        self.open_hat_probability = max(0.0, min(1.0, open_hat_probability))
        self.clap_on_two = clap_on_two
        self.rhythm = rhythm
        self.sidechain_depth = sidechain_depth
        self.snare_delay = snare_delay
        self.hihat_delay = hihat_delay
        self.groove_swing = groove_swing
        self.swing_grid = swing_grid
        self.choke_hats = choke_hats
        self.ghost_snare_prob = ghost_snare_prob
        self.section_type = section_type
        self.auto_fills = auto_fills

    def _velocity(self, ratio: float = 1.0) -> int:
        """Standard velocity for trap drums based on base_velocity."""
        return int(self.base_velocity() * ratio)

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
        s_type = getattr(context, "section_type", self.section_type)
        fills_enabled = getattr(context, "auto_fills", self.auto_fills)

        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        last_chord = chords[-1]

        bar_start = 0.0
        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue

            # Determine if this is the final bar of the phrase
            is_final_bar = (fills_enabled and duration_beats > 4.0 and (bar_start >= duration_beats - 4.0))

            # Apply intro density cuts
            active_kick_pattern = "sparse" if s_type == "intro" else self.kick_pattern
            active_hat_roll_density = 0.0 if s_type == "intro" else self.hat_roll_density

            # 808/sub on beats 1 and (3)
            if s_type != "intro":
                sub_pitch = max(low, nearest_pitch(chord.root, low + 12))
                # Outro early truncation: shorten duration in final bar
                if s_type == "outro" and is_final_bar:
                    sub_dur = 0.8
                else:
                    sub_dur = 3.5

                self._add_note(notes, sub_pitch, bar_start, sub_dur, self._velocity(1.1), duration_beats)
                
                # Beat 3 is at offset 2, which is >= 2.0. In final bar, second half is silenced, so we do not add sub on beat 3.
                if active_kick_pattern != "sparse" and not is_final_bar:
                    self._add_note(notes, sub_pitch, bar_start + 2, 1.5, self._velocity(1.0), duration_beats)

            # Kick
            if not is_final_bar:
                if active_kick_pattern == "standard":
                    self._add_note(notes, KICK, bar_start, 0.3, self._velocity(1.2), duration_beats)
                    self._add_note(notes, KICK, bar_start + 2, 0.3, self._velocity(1.1), duration_beats)
                elif active_kick_pattern == "syncopated":
                    self._add_note(notes, KICK, bar_start, 0.3, self._velocity(1.2), duration_beats)
                    self._add_note(notes, KICK, bar_start + 2.5, 0.3, self._velocity(1.05), duration_beats)
                    self._add_note(notes, KICK, bar_start + 3.5, 0.3, self._velocity(0.95), duration_beats)
                else:
                    self._add_note(notes, KICK, bar_start, 0.3, self._velocity(1.2), duration_beats)
            else:
                # If is_final_bar, only add kick on beat 1 (onset 0.0)
                self._add_note(notes, KICK, bar_start, 0.3, self._velocity(1.2), duration_beats)

            # Snare/Clap on 2 and 4 (or 1 and 3 depending on clap_on_two)
            clap_beat = 1 if self.clap_on_two else 2
            # Beat 1 or 2
            if not is_final_bar or clap_beat < 2.0:
                self._add_note(notes, SNARE, bar_start + clap_beat, 0.3, self._velocity(1.2), duration_beats)
                self._add_note(notes, CLAP, bar_start + clap_beat, 0.3, self._velocity(1.0), duration_beats)
            
            # Beat 3
            if not is_final_bar:
                self._add_note(notes, SNARE, bar_start + 3, 0.3, self._velocity(1.2), duration_beats)
                self._add_note(notes, CLAP, bar_start + 3, 0.3, self._velocity(1.0), duration_beats)

            # Hi-hats
            if self.variant in ("standard", "drill", "melodic"):
                steps_per_bar = 16 if self.variant == "melodic" else 8
                step_duration = 0.25 if self.variant == "melodic" else 0.5
                
                i = 0
                while i < steps_per_bar:
                    onset = bar_start + i * step_duration
                    if onset >= duration_beats:
                        break
                        
                    # Silence the second half of final bar
                    if is_final_bar and (i * step_duration) >= 2.0:
                        i += 1
                        continue

                    # Determine if we should trigger a roll at this step
                    trigger_roll = random.random() < active_hat_roll_density and (i < steps_per_bar - 1)
                    
                    if trigger_roll:
                        # Choose roll parameters
                        roll_type = random.choices(
                            ["32nd", "32nd_triplet", "64th", "quintuplet"],
                            weights=[40, 30, 20, 10]
                        )[0]
                        
                        if roll_type == "32nd":
                            roll_step = 0.125
                            roll_len = 4 if self.variant != "melodic" else 2
                        elif roll_type == "32nd_triplet":
                            roll_step = 0.083333
                            roll_len = 3
                        elif roll_type == "64th":
                            roll_step = 0.0625
                            roll_len = 4
                        else: # quintuplet
                            roll_step = 0.10
                            roll_len = 5
                            
                        # Tune sweep (pitch sweeps)
                        use_sweep = random.random() < 0.5
                        if use_sweep:
                            start_pitch_offset = random.choice([-5, -4, -3, -2, 2, 3, 4, 5, 7])
                            end_pitch_offset = random.choice([-7, -5, -3, 0, 2, 5, 7])
                        else:
                            start_pitch_offset = 0
                            end_pitch_offset = 0
                            
                        # Velocity curve: 70% crescendo (swell), 30% decrescendo
                        use_crescendo = random.random() < 0.7
                        
                        # Generate the roll notes
                        for r in range(roll_len):
                            r_onset = onset + r * roll_step
                            if r_onset >= duration_beats:
                                break
                                
                            # Calculate tuned pitch
                            if roll_len > 1:
                                interp = r / (roll_len - 1)
                            else:
                                interp = 1.0
                            pitch_offset = int(start_pitch_offset + (end_pitch_offset - start_pitch_offset) * interp)
                            roll_pitch = max(0, min(127, HH_CLOSED + pitch_offset))
                            
                            # Calculate dynamic velocity curve
                            if use_crescendo:
                                curve = 0.35 + 0.65 * (interp ** 2)
                            else:
                                curve = 0.9 - 0.5 * (interp ** 1.5)
                                
                            roll_vel = max(1, min(127, int(self._velocity(0.85) * curve)))
                            
                            self._add_note(notes, roll_pitch, r_onset, round(roll_step * 0.8, 6), roll_vel, duration_beats)
                            
                        # Advance step pointer past the roll duration
                        roll_duration_beats = roll_len * roll_step
                        steps_to_skip = int(roll_duration_beats / step_duration)
                        i += max(1, steps_to_skip)
                    else:
                        # Normal hi-hat note
                        is_open = random.random() < self.open_hat_probability
                        # Intro hat simplification: open hat is simplified to closed hat
                        if s_type == "intro":
                            is_open = False
                        hat = HH_OPEN if is_open else HH_CLOSED
                        
                        # Dynamics: strong beats are accented, offbeats are slightly quieter
                        beat_pos = (onset - bar_start) % 1.0
                        if beat_pos == 0.0:
                            vel = self._velocity(0.95)
                        elif abs(beat_pos - 0.5) < 0.01:
                            vel = self._velocity(0.85)
                        else:
                            vel = self._velocity(0.7)
                            
                        dur = 0.25 if is_open else 0.12
                        self._add_note(notes, hat, onset, dur, vel, duration_beats)
                        i += 1

            elif self.variant == "minimal":
                # Sparse hats
                for beat in [0, 1, 2, 3]:
                    if is_final_bar and beat >= 2:
                        continue
                    onset = bar_start + beat
                    self._add_note(notes, HH_CLOSED, onset, 0.15, self._velocity(0.75), duration_beats)
                    if random.random() < 0.3:
                        if not (is_final_bar and (beat + 0.5) >= 2.0):
                            self._add_note(
                                notes, HH_CLOSED, onset + 0.5, 0.1, self._velocity(0.6), duration_beats
                            )

            # Generate low-velocity trap snare ghost notes if requested
            if self.ghost_snare_prob > 0.0 and s_type not in ("intro", "outro"):
                # Ghost note positions (sixteenth subdivisions)
                ghost_positions = [0.75, 1.75, 2.25, 2.75, 3.75]
                for sub in ghost_positions:
                    if is_final_bar and sub >= 2.0:
                        continue
                    if random.random() < self.ghost_snare_prob:
                        onset = bar_start + sub
                        # Make sure we don't overlap with a main snare hit
                        main_snare_beats = [clap_beat, 3.0]
                        if any(abs(sub - mb) < 0.05 for mb in main_snare_beats):
                            continue
                        
                        # Add a low velocity ghost snare
                        # With 25% probability, make it a syncopated snare roll of 2 or 3 extremely fast notes!
                        if random.random() < 0.25:
                            roll_len = random.choice([2, 3])
                            roll_step = 0.0625  # 64th note snare roll!
                            for r in range(roll_len):
                                r_onset = onset + r * roll_step
                                r_vel = int(self._velocity(0.35) * (0.5 + 0.5 * (r / (roll_len - 1))))
                                self._add_note(notes, SNARE, r_onset, 0.06, r_vel, duration_beats)
                        else:
                            # Standard single ghost hit
                            vel = int(self._velocity(random.uniform(0.25, 0.45)))
                            self._add_note(notes, SNARE, onset, 0.08, vel, duration_beats)

            # Phrase-boundary transitions
            if is_final_bar:
                sub_pitch = max(low, nearest_pitch(chord.root, low + 12)) if s_type != "intro" else 36
                if s_type in ("chorus", "pre_chorus"):
                    # Snare accents
                    self._add_note(notes, SNARE, bar_start + 2.0, 0.2, self._velocity(1.15), duration_beats)
                    self._add_note(notes, SNARE, bar_start + 2.5, 0.2, self._velocity(1.15), duration_beats)
                    
                    # 64th snare roll crescendo: 8 notes from 3.0 to 3.5
                    for step in range(8):
                        onset = bar_start + 3.0 + step * 0.0625
                        vel_ratio = 0.7 + 0.45 * (step / 7)
                        self._add_note(notes, SNARE, onset, 0.05, self._velocity(vel_ratio), duration_beats)
                    
                    # Pitched hi-hat 32nd-triplet sweep: 5 notes from 3.5 to 3.9167
                    for step in range(5):
                        onset = bar_start + 3.5 + step * 0.083333
                        pitch_offset = step
                        roll_pitch = max(0, min(127, HH_CLOSED + pitch_offset))
                        vel_ratio = 0.65 + 0.25 * (step / 4)
                        self._add_note(notes, roll_pitch, onset, 0.07, self._velocity(vel_ratio), duration_beats)
                    
                    # Final open hat accent
                    self._add_note(notes, HH_OPEN, bar_start + 3.9, 0.2, self._velocity(1.15), duration_beats)
                    
                elif s_type == "outro":
                    # Soft fading hats with no kick/sub
                    self._add_note(notes, HH_CLOSED, bar_start + 2.0, 0.15, self._velocity(0.5), duration_beats)
                    self._add_note(notes, HH_CLOSED, bar_start + 2.5, 0.15, self._velocity(0.4), duration_beats)
                    self._add_note(notes, HH_CLOSED, bar_start + 3.0, 0.15, self._velocity(0.3), duration_beats)
                    self._add_note(notes, HH_CLOSED, bar_start + 3.5, 0.15, self._velocity(0.2), duration_beats)
                    
                else: # "verse", "bridge", etc.
                    # Syncopated 808 sub triplets with a single snare punch
                    self._add_note(notes, sub_pitch, bar_start + 2.0, 0.25, self._velocity(1.0), duration_beats)
                    self._add_note(notes, sub_pitch, bar_start + 2.3333, 0.25, self._velocity(0.95), duration_beats)
                    self._add_note(notes, sub_pitch, bar_start + 2.6667, 0.25, self._velocity(0.9), duration_beats)
                    
                    # Single snare punch on beat 3.0
                    self._add_note(notes, SNARE, bar_start + 3.0, 0.3, self._velocity(1.15), duration_beats)

            bar_start += 4.0

        # Pro-grade dynamic velocity and transient scaling
        for n in notes:
            if n.pitch == KICK:
                beat_in_bar = n.start % 4.0
                if abs(beat_in_bar) < 0.01 or abs(beat_in_bar - 2.0) < 0.01:
                    n.velocity = int(n.velocity * 1.15)
            elif n.pitch in (SNARE, CLAP):
                beat_in_bar = n.start % 4.0
                if abs(beat_in_bar - 1.0) < 0.01 or abs(beat_in_bar - 3.0) < 0.01:
                    n.velocity = int(n.velocity * 1.15)
            elif n.pitch in (HH_CLOSED, HH_OPEN):
                sub_pos = n.start % 1.0
                if abs(sub_pos - 0.5) < 0.01:
                    n.velocity = int(n.velocity * 0.88)
                elif abs(sub_pos - 0.25) < 0.01 or abs(sub_pos - 0.75) < 0.01:
                    n.velocity = int(n.velocity * 0.78)

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

    def _add_note(
        self, notes: list, pitch: int, onset: float, dur: float, vel: int, total: float
    ) -> None:
        if 0 <= onset < total:
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=dur,
                    velocity=max(1, min(127, vel)),
                )
            )

    def _apply_pro_features(self, notes: list[NoteInfo]) -> list[NoteInfo]:
        # 1. Swing Timing & Pocket Timing Offsets
        swing_delay = 0.0
        if self.groove_swing > 0.5 and self.swing_grid > 0:
            swing_delay = (self.groove_swing - 0.5) * 2.0 * (self.swing_grid / 2.0)

        for n in notes:
            # Check swing
            grid_pos = n.start % (2.0 * self.swing_grid)
            is_offbeat = abs(grid_pos - self.swing_grid) < 0.01

            shift = 0.0
            if is_offbeat:
                shift += swing_delay

            # Apply pocket delays
            if n.pitch in (SNARE, CLAP):
                shift += self.snare_delay
            elif n.pitch in (HH_CLOSED, HH_OPEN) or (40 <= n.pitch <= 48 and n.pitch != SNARE and n.pitch != CLAP):
                shift += self.hihat_delay

            n.start = round(max(0.0, n.start + shift), 6)

        # 2. Hi-Hat Auto-Choking
        if self.choke_hats:
            notes.sort(key=lambda x: x.start)
            for i, n in enumerate(notes):
                if n.pitch == HH_OPEN or (43 <= n.pitch <= 48 and n.pitch != HH_CLOSED):
                    for j in range(i + 1, len(notes)):
                        next_n = notes[j]
                        if next_n.start >= n.start + n.duration:
                            break
                        if next_n.pitch == HH_CLOSED:
                            n.duration = round(max(0.01, next_n.start - n.start - 0.005), 6)
                            break

        # 3. Post-Process Sidechain Ducking Pass
        if self.sidechain_depth > 0.0:
            kick_onsets = [n.start for n in notes if n.pitch in (KICK, SUB_808)]
            for n in notes:
                if n.pitch not in (KICK, SUB_808):
                    for kick_start in kick_onsets:
                        if abs(n.start - kick_start) < 0.20 or (n.start <= kick_start < n.start + n.duration):
                            n.velocity = max(1, int(n.velocity * (1.0 - self.sidechain_depth)))
                            break

        return notes
