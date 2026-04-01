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

    ctrl = TextureController(tension_curve=tension_curve)

    # Build index of all non-chord notes (melody, bass, etc.) for clash checking
    reference_notes: list[tuple[float, float, int]] = []
    chord_track_names = set()
    for track_cfg in tracks:
        if track_cfg.generator_type in ("chord", "strum", "arpeggiator"):
            chord_track_names.add(track_cfg.name)
        elif track_cfg.name in result:
            for n in result[track_cfg.name]:
                reference_notes.append((n.start, n.start + n.duration, n.pitch))

    for track_cfg in tracks:
        if track_cfg.name not in result or track_cfg.name not in chord_track_names:
            continue

        filtered = []
        for n in result[track_cfg.name]:
            density = ctrl.get_density_at(n.start)

            # Check if this note clashes with any reference note
            creates_clash = False
            for ref_start, ref_end, ref_pitch in reference_notes:
                if n.start < ref_end and (n.start + n.duration) > ref_start:
                    interval = abs(n.pitch - ref_pitch) % 12
                    if interval in (1, 6, 11):  # m2, tritone, M7
                        creates_clash = True
                        break

            if creates_clash:
                # Higher chance of dropping clashing notes
                keep_prob = density * 0.5
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
    """Scale all track velocities by tension level (0.6–1.0 factor)."""
    if not tension_curve:
        return
    for track_cfg in tracks:
        if track_cfg.name not in result:
            continue
        shaped = []
        for n in result[track_cfg.name]:
            t_val = tension_curve.tension_at(n.start)  # 0.0–1.0
            scale_factor = 0.6 + 0.4 * t_val  # 0.6–1.0
            shaped.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=max(1, min(127, int(n.velocity * scale_factor))),
                    articulation=n.articulation,
                    expression=n.expression,
                )
            )
        result[track_cfg.name] = shaped


def apply_track_modifiers(notes, cfg, chords, scale, time_signature, total_beats):
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
            cfg.params.get("note_range_low", scale_root * 12 + 48)
            if isinstance(cfg.params, dict)
            else scale_root * 12 + 48
        )
        high = (
            cfg.params.get("note_range_high", scale_root * 12 + 84)
            if isinstance(cfg.params, dict)
            else scale_root * 12 + 84
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
