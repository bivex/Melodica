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
from melodica.types import ChordLabel, NoteInfo, Scale, SectionRole
from melodica.utils import nearest_pitch, chord_at, snap_to_scale
from melodica.generators._postprocess import post_process_808


# GM-ish mapping
KICK = 36
SNARE = 38
HH_CLOSED = 42
HH_OPEN = 46
CLAP = 39
# 808 sub-bass notes use the chord root (see render()); there is no fixed
# SUB_808 GM pitch — the previous SUB_808 = 36 was identical to KICK and
# never applied to the actual 808 notes (they use nearest_pitch on the
# chord root). It only appeared in the sidechain ducking check, where it
# was harmless because the real 808 notes never matched 36 anyway.


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
    section_type: SectionRole | str = SectionRole.VERSE
    auto_fills: bool = True
    groove_template: any = None
    slide_curve: str = "exponential"
    transient_ducking: bool = True
    ducking_duration: float = 0.02
    envelope_gating: bool = True
    mute_boundaries: bool = True
    kick_less_verse: bool = True
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
        section_type: SectionRole | str = SectionRole.VERSE,
        auto_fills: bool = True,
        groove_template: any = None,
        slide_curve: str = "exponential",
        transient_ducking: bool = True,
        ducking_duration: float = 0.02,
        envelope_gating: bool = True,
        mute_boundaries: bool = True,
        kick_less_verse: bool = True,
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
        self.groove_template = groove_template
        self.slide_curve = slide_curve
        self.transient_ducking = transient_ducking
        self.ducking_duration = max(0.0, ducking_duration)
        self.envelope_gating = envelope_gating
        self.mute_boundaries = mute_boundaries
        self.kick_less_verse = kick_less_verse

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
        s_type = context.section_role if context else self.section_type
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

                self._add_note(notes, sub_pitch, bar_start, sub_dur, self._velocity(1.1), duration_beats, articulation="808")
                
                # Beat 3 is at offset 2, which is >= 2.0. In final bar, second half is silenced, so we do not add sub on beat 3.
                if active_kick_pattern != "sparse" and not is_final_bar:
                    chord_3 = chord_at(chords, bar_start + 2.0)
                    sub_pitch_3 = max(low, nearest_pitch(chord_3.root if chord_3 is not None else chord.root, low + 12))
                    self._add_note(notes, sub_pitch_3, bar_start + 2, 1.5, self._velocity(1.0), duration_beats, articulation="808")

            # Kick
            is_kick_less_bar = (bar_start == 0.0 and s_type == "verse" and self.kick_less_verse)
            if not is_kick_less_bar:
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
                        # Choose roll parameters (including quintuplet & septuplet stutters)
                        roll_type = random.choices(
                            ["32nd", "32nd_triplet", "64th", "quintuplet", "septuplet"],
                            weights=[30, 25, 20, 15, 10]
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
                        elif roll_type == "quintuplet":
                            roll_step = 0.10
                            roll_len = 5
                        else: # septuplet
                            roll_step = 0.071428
                            roll_len = 7
                            
                        # Tune sweep: previously this added pitch_offset to
                        # HH_CLOSED (42) and snap_to_scale'd the result,
                        # which landed on unrelated GM percussion pitches
                        # (35=bd, 37=side stick, 38=snare, 41-49=toms/crash).
                        # Hi-hats do not pitch-shift in real trap; the roll
                        # stays on HH_CLOSED with an occasional HH_OPEN for
                        # tonal variation. Velocity curve carries the "sweep".
                        use_open = random.random() < 0.15  # sparse open-hat accents
                        use_sweep = False  # disabled: pitch sweeps on hats were spurious instrument changes
                            
                        # Velocity curve: 70% crescendo (swell), 30% decrescendo
                        use_crescendo = random.random() < 0.7
                        
                        # Generate the roll notes
                        for r in range(roll_len):
                            r_onset = onset + r * roll_step
                            if r_onset >= duration_beats:
                                break

                            # Roll pitch: stay on HH_CLOSED (42), with a sparse
                            # HH_OPEN (46) accent for timbral variation. No
                            # pitch offsets — those previously walked into other
                            # GM percussion instruments.
                            if roll_len > 1:
                                interp = r / (roll_len - 1)
                            else:
                                interp = 1.0
                            roll_pitch = HH_OPEN if (use_open and r == roll_len - 1) else HH_CLOSED

                            # Calculate dynamic velocity curve
                            if use_crescendo:
                                curve = 0.35 + 0.65 * (interp ** 2)
                            else:
                                curve = 0.9 - 0.5 * (interp ** 1.5)

                            roll_vel = max(1, min(127, int(self._velocity(0.85) * curve)))

                            # Alternating CC 10 wide stereo micro-panning
                            pan_val = 32 if r % 2 == 0 else 96
                            self._add_note(
                                notes,
                                roll_pitch,
                                r_onset,
                                round(roll_step * 0.8, 6),
                                roll_vel,
                                duration_beats,
                                expression={10: pan_val}
                            )
                            
                        # Advance step pointer past the roll duration
                        roll_duration_beats = roll_len * roll_step
                        steps_to_skip = int(round(roll_duration_beats / step_duration))
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
                        
                        # Subtle center-ish panning humanization
                        pan_val = random.randint(54, 74)
                        self._add_note(notes, hat, onset, dur, vel, duration_beats, expression={10: pan_val})
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
                    
                    # Hi-hat 32nd-triplet sweep: 5 notes from 3.5 to 3.9167.
                    # Stay on HH_CLOSED — the previous pitch_offset = step walked
                    # the pitch 42->46 (through toms/crash on GM kits). The
                    # "sweep" feel now comes from the velocity curve.
                    for step in range(5):
                        onset = bar_start + 3.5 + step * 0.083333
                        vel_ratio = 0.65 + 0.25 * (step / 4)
                        self._add_note(notes, HH_CLOSED, onset, 0.07, self._velocity(vel_ratio), duration_beats)
                    
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

        # 1. Post-process 808 sub-bass glides, transient ducking, and envelope gating
        notes = post_process_808(
            notes,
            chords,
            duration_beats,
            slide_curve=self.slide_curve,
            transient_ducking=self.transient_ducking,
            ducking_duration=self.ducking_duration,
            envelope_gating=self.envelope_gating,
        )

        # 2. Apply mute_boundaries phrase dropouts (complete silence of non-808 drums in the last beat)
        if self.mute_boundaries and duration_beats > 4.0:
            notes = [
                n for n in notes
                if n.start < duration_beats - 1.0 or getattr(n, "articulation", None) == "808"
            ]

        # 3. Apply swing, pocket timing, hi-hat choking, and sidechain ducking passes
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
        self,
        notes: list[NoteInfo],
        pitch: int,
        onset: float,
        dur: float,
        vel: int,
        total: float,
        articulation: str | None = None,
        expression: dict[int, int] | None = None,
    ) -> None:
        if 0 <= onset < total:
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=dur,
                    velocity=max(1, min(127, vel)),
                    articulation=articulation,
                    expression=expression or {},
                )
            )

    def _apply_pro_features(self, notes: list[NoteInfo]) -> list[NoteInfo]:
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

            # Apply pocket delays. Only apply the hi-hat delay to actual
            # hi-hat pitches (42/46); the previous 40-48 range also caught
            # toms (41/43/45/47) and electric snare (40), shifting their
            # timing out of the groove.
            if n.pitch in (SNARE, CLAP):
                shift += self.snare_delay
            elif n.pitch in (HH_CLOSED, HH_OPEN):
                shift += self.hihat_delay

            n.start = round(max(0.0, n.start + shift), 6)

        # 1.5. Physical Hand-to-Foot Coordination Limits Safeguard
        hand_struck_pitches = {SNARE, CLAP, HH_CLOSED, HH_OPEN, 39, 41, 45, 50, 49, 37, 51}
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
            49: 2,
            50: 3,
            45: 3,
            41: 3,
            37: 4,
            HH_OPEN: 5,
            HH_CLOSED: 5,
        }
        
        filtered_notes = []
        for group in groups:
            hand_struck = [n for n in group if n.pitch in hand_struck_pitches]
            other = [n for n in group if n.pitch not in hand_struck_pitches]
            
            if len(hand_struck) > 2:
                # Sort by priority
                hand_struck.sort(key=lambda n: priority_map.get(n.pitch, 99))
                # Keep top 2, drop the rest
                filtered_notes.extend(hand_struck[:2])
                filtered_notes.extend(other)
            else:
                filtered_notes.extend(group)
        
        notes = filtered_notes

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
            # Sidechain: duck non-kick notes around kick onsets. The 808
            # sub-bass notes (computed from the chord root) are NOT kicked
            # here — they sustain through. Only the percussive KICK (36)
            # triggers ducking.
            kick_onsets = [n.start for n in notes if n.pitch == KICK]
            for n in notes:
                # Don't duck the kick itself, nor the 808 sub-bass (which is
                # marked with articulation="808" and sustains through kicks).
                if n.pitch == KICK or getattr(n, "articulation", None) == "808":
                    continue
                for kick_start in kick_onsets:
                        if abs(n.start - kick_start) < 0.20 or (n.start <= kick_start < n.start + n.duration):
                            n.velocity = max(1, int(n.velocity * (1.0 - self.sidechain_depth)))
                            break

        return notes
