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
_postprocess.py — Shared post-processing helpers for IdeaTool.generate().

Extracted from idea_tool.py to reduce method complexity.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from melodica.types import NoteInfo

if TYPE_CHECKING:
    from melodica.composer import TextureController
    from melodica.tension import TensionCurve


def apply_texture_control(
    result: dict[str, list[NoteInfo]],
    tracks,
    tension_curve: TensionCurve,
    use_texture_control: bool,
) -> None:
    """Filter chord/pad/strum/arpeggiator notes based on tension-driven density.

    Harmonic-aware: prefers dropping notes that create clashes with other tracks
    rather than randomly culling notes.
    """
    if not use_texture_control or not tension_curve:
        return
    from melodica.composer import TextureController

    import bisect

    ctrl = TextureController(tension_curve=tension_curve)

    def is_chord_track(cfg) -> bool:
        """Check if a track produces chord-like (polyphonic simultaneous) notes."""
        if cfg.generator_type in ("chord", "strum", "arpeggiator"):
            return True
        if cfg.generator is not None:
            from melodica.generators.ambient import AmbientPadGenerator

            if isinstance(cfg.generator, AmbientPadGenerator):
                return True
        return False

    # Build index of all non-chord notes (melody, bass, etc.) for clash checking
    reference_notes: list[tuple[float, float, int]] = []
    chord_track_names = set()
    max_ref_duration = 0.0
    for track_cfg in tracks:
        if is_chord_track(track_cfg):
            chord_track_names.add(track_cfg.name)
        elif track_cfg.name in result:
            for n in result[track_cfg.name]:
                reference_notes.append((n.start, n.start + n.duration, n.pitch))
                if n.duration > max_ref_duration:
                    max_ref_duration = n.duration

    reference_notes.sort(key=lambda x: x[0])
    ref_starts = [x[0] for x in reference_notes]

    for track_cfg in tracks:
        if track_cfg.name not in result or track_cfg.name not in chord_track_names:
            continue

        filtered = []
        for n in result[track_cfg.name]:
            density = ctrl.get_density_at(n.start)

            # Check if this note clashes with any reference note
            creates_clash = False
            lo = bisect.bisect_left(ref_starts, n.start - max_ref_duration - 0.1)
            hi = bisect.bisect_right(ref_starts, n.start + n.duration)

            for ref_start, ref_end, ref_pitch in reference_notes[lo:hi]:
                if n.start < ref_end and (n.start + n.duration) > ref_start:
                    interval = abs(n.pitch - ref_pitch) % 12
                    if interval in (1, 6, 11):  # m2, tritone, M7
                        creates_clash = True
                        break

            if creates_clash:
                # Slightly higher chance of dropping clashing notes, but not extreme
                keep_prob = density * 0.8
            else:
                keep_prob = density

            if random.random() < keep_prob:
                filtered.append(n)

        result[track_cfg.name] = filtered


def apply_velocity_shaping(
    result: dict[str, list[NoteInfo]],
    tracks,
    tension_curve: TensionCurve,
) -> None:
    """Scale all track velocities by tension level (0.4–1.0 factor).

    Low tension (quiet sections) → velocity scaled down to 40%.
    High tension (climaxes) → velocity at 100%.
    """
    if not tension_curve:
        return
    for track_cfg in tracks:
        if track_cfg.name not in result:
            continue
        shaped = []
        for n in result[track_cfg.name]:
            t_val = tension_curve.tension_at(n.start)  # 0.0–1.0
            # Full dynamic range: 0.4 (piano) to 1.0 (forte)
            scale_factor = 0.4 + 0.6 * t_val
            shaped.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=max(25, min(127, int(n.velocity * scale_factor))),
                    articulation=n.articulation,
                    expression=n.expression,
                )
            )
        result[track_cfg.name] = shaped


def apply_track_modifiers(notes, cfg, chords, scale, time_signature, total_beats,
                          all_tracks=None):
    """Apply SDK modifier instances from TrackConfig.modifiers to notes."""
    if not cfg.modifiers:
        return notes
    from melodica.modifiers import ModifierContext
    from melodica.types import MusicTimeline, KeyLabel, TimeSignatureLabel
    import logging

    logger = logging.getLogger(__name__)
    timeline = MusicTimeline(
        chords=chords,
        keys=[KeyLabel(scale=scale, start=0, duration=total_beats)],
        time_signatures=[
            TimeSignatureLabel(
                numerator=time_signature[0],
                denominator=time_signature[1],
                start=0,
            )
        ],
        markers=[],
    )
    mctx = ModifierContext(
        duration_beats=total_beats,
        chords=chords,
        timeline=timeline,
        scale=scale,
        tracks=all_tracks or {},
    )
    for mod in cfg.modifiers:
        if hasattr(mod, "modify"):
            try:
                notes = mod.modify(notes, mctx)
            except Exception:
                logger.debug(
                    "Modifier %s failed on track %s, skipping",
                    type(mod).__name__,
                    cfg.name,
                    exc_info=True,
                )
    return notes


def handle_phrase_memory(
    section_notes, phrase_memory, mem_key, section, i, adjusted, cfg, scale_root
):
    """Store first occurrence or recall with variation on repeat sections."""
    import random
    from melodica.composer import Phrase

    if not section_notes:
        return section_notes
    if not phrase_memory.get_by_tag(mem_key):
        phrase_memory.store(
            Phrase(
                notes=tuple(section_notes),
                section=section,
                bar=i,
                chord_root=adjusted[0].root if adjusted else 0,
                tag=mem_key,
            )
        )
    elif i > 0 and random.random() < 0.35:
        transforms = ["retrograde", "inversion", "retrograde_inversion"]
        transform = random.choice(transforms)
        low = (
            cfg.params.get("note_range_low", scale_root + 48)
            if isinstance(cfg.params, dict)
            else scale_root + 48
        )
        high = (
            cfg.params.get("note_range_high", scale_root + 84)
            if isinstance(cfg.params, dict)
            else scale_root + 84
        )
        recalled = phrase_memory.recall(tag=mem_key, transform=transform, low=low, high=high)
        if recalled and len(recalled) >= 3:
            section_notes = recalled
    return section_notes


def apply_voice_leading(notes, cfg, chords, scale, time_signature, total_beats):
    """Apply voice leading to smooth octave leaps."""
    from melodica.modifiers import ModifierContext, VoiceLeadingModifier
    from melodica.types import MusicTimeline, KeyLabel, TimeSignatureLabel
    import logging

    logger = logging.getLogger(__name__)
    timeline = MusicTimeline(
        chords=chords,
        keys=[KeyLabel(scale=scale, start=0, duration=total_beats)],
        time_signatures=[
            TimeSignatureLabel(
                numerator=time_signature[0],
                denominator=time_signature[1],
                start=0,
            )
        ],
        markers=[],
    )
    mctx = ModifierContext(
        duration_beats=total_beats,
        chords=chords,
        timeline=timeline,
        scale=scale,
    )
    vl = VoiceLeadingModifier()
    try:
        notes = vl.modify(notes, mctx)
    except Exception:
        logger.debug("Voice leading failed on track %s, skipping", cfg.name, exc_info=True)
    return notes


def apply_non_chord_tones(notes, cfg, chords, scale):
    """Add non-chord tones (passing tones, neighbors) to melody/bass lines."""
    from melodica.composer import NonChordToneGenerator
    import logging

    logger = logging.getLogger(__name__)
    nct = NonChordToneGenerator(passing_prob=0.15, neighbor_prob=0.08)
    try:
        notes = nct.add_non_chord_tones(notes, chords, scale)
    except Exception:
        logger.debug(
            "Non-chord tone generation failed on track %s, skipping",
            cfg.name,
            exc_info=True,
        )
    return notes


def apply_mpe_expression(result, tracks):
    """Inject per-note MPE expression curves (CC11, CC74, CC1) for tracks with mpe=True."""
    from melodica.expression_envelope import mpe_expression_for_instrument
    import logging

    logger = logging.getLogger(__name__)
    for track_cfg in tracks:
        if not getattr(track_cfg, "mpe", False):
            continue
        if track_cfg.name not in result:
            continue

        new_notes = []
        for n in result[track_cfg.name]:
            mpe_expr = mpe_expression_for_instrument(track_cfg.instrument, n.duration, n.velocity)
            merged = dict(n.expression)
            for k, v in mpe_expr.items():
                if k not in merged:
                    merged[k] = v
            new_notes.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=n.velocity,
                    articulation=n.articulation,
                    expression=merged,
                )
            )
        result[track_cfg.name] = new_notes


def apply_portamento(result, tracks):
    """Add pitch bend portamento curves for MPE tracks at large interval jumps.

    When a note follows another with >2 semitone gap and starts within 0.5 beats,
    a pitch bend curve glides from the previous pitch to the current one.
    """
    import math

    for track_cfg in tracks:
        if not getattr(track_cfg, "mpe", False):
            continue
        if track_cfg.name not in result:
            continue

        notes = sorted(result[track_cfg.name], key=lambda n: n.start)
        if len(notes) < 2:
            continue

        modified = [notes[0]]
        for i in range(1, len(notes)):
            prev = notes[i - 1]
            curr = notes[i]
            gap = curr.start - (prev.start + prev.duration)
            interval = curr.pitch - prev.pitch

            # Only portamento: close timing (< 0.5 beats gap) and significant jump (3-11 semitones)
            if -12 < interval < 12 and abs(interval) >= 3 and gap < 0.5:
                # Pitch bend range: ±48 semitones (set by MPE zone in midi.py)
                # 8192 per 48 semitones = ~171 per semitone
                bend_start = int(interval * -171)  # Negative: start bent toward previous pitch
                glide_beats = min(0.25, curr.duration * 0.3)  # Glide over 30% of note or 0.25 beats
                steps = max(3, int(glide_beats * 8))

                points = []
                for s in range(steps + 1):
                    t = (s / steps) * glide_beats
                    frac = s / steps
                    # Exponential ease-out curve
                    eased = 1.0 - math.exp(-3.0 * frac)
                    val = int(bend_start * (1.0 - eased))
                    points.append((round(t, 4), max(-8192, min(8191, val))))

                merged = dict(curr.expression)
                # Prepend portamento to existing pitch_bend or create new
                if "pitch_bend" in merged:
                    existing = merged["pitch_bend"]
                    if isinstance(existing, list):
                        merged["pitch_bend"] = points + existing
                else:
                    merged["pitch_bend"] = points

                modified.append(
                    NoteInfo(
                        pitch=curr.pitch,
                        start=curr.start,
                        duration=curr.duration,
                        velocity=curr.velocity,
                        articulation=curr.articulation,
                        expression=merged,
                    )
                )
            else:
                modified.append(curr)

        result[track_cfg.name] = modified
