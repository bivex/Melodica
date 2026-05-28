#!/usr/bin/env python3
"""
melodica/shorts_mixing.py — Shared mixing system for Shorts audio generators.

Provides:
- MixingDesk: centralized gain staging and automation
- SectionFader: volume automation per section (Hook/Dynamics/Loop)
- VelocityNormalizer: gentle compression/limiting
- FrequencySeparator: warns about masking conflicts

Usage:
    from melodica.shorts_mixing import MixingDesk
    desk = MixingDesk(niche_cfg)
    tracks = desk.apply_mixing(tracks, sections, bpm)
"""

import math
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from melodica.types import NoteInfo


@dataclass
class MixingDesk:
    """Central mixing console — applies gain staging, automation, and balance."""

    niche_cfg: dict = field(default_factory=dict)  # deprecated, ignored
    # Per-track gain multipliers (target velocity ranges)
    track_gains: Dict[str, float] = field(
        default_factory=lambda: {
            "bass": 1.0,  # 100-120
            "drums": 1.0,  # 90-110
            "sfx": 1.0,  # 80-120 (prominent)
            "pad": 0.25,  # 20-40 (background)
            "voice": 0.6,  # 60-80 (mid)
            "clicks": 0.7,  # 70-85
            "lead": 0.75,  # 70-90
            "fanfare": 0.9,  # 85-110
            "coins": 0.65,  # 60-90
        }
    )
    # Section fader automation (gain multiplier applied on top of track_gains)
    section_faders: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: {
            "Hook": {
                "sfx": 1.15,  # punchier SFX
                "drums": 1.1,  # harder drums
                "pad": 0.7,  # quieter pad
                "bass": 1.0,
                "lead": 0.9,  # lead not dominant in hook
                "fanfare": 1.2,
                "coins": 1.1,
            },
            "Dynamics": {
                "sfx": 1.0,
                "drums": 1.0,
                "pad": 1.0,
                "bass": 1.0,
                "lead": 1.0,
                "fanfare": 1.0,
                "coins": 1.0,
            },
            "Loop": {
                "sfx": 0.8,  # SFX die down
                "drums": 0.95,
                "pad": 0.5,  # pad fades
                "bass": 0.95,
                "lead": 0.7,  # lead withdraws
                "fanfare": 0.6,
                "coins": 0.5,
            },
        }
    )

    def apply_mixing(
        self,
        tracks: Dict[str, List[NoteInfo]],
        sections: List[Tuple[str, int, List[str]]],
        bpm: int,
    ) -> Dict[str, List[NoteInfo]]:
        """Apply full mixing chain: section faders + gain staging + limiting."""
        # Calculate section beat boundaries
        beat_offset = 0.0
        section_bounds = []  # (name, start_beat, end_beat)
        for name, bars, _ in sections:
            beats = bars * 4
            section_bounds.append((name, beat_offset, beat_offset + beats))
            beat_offset += beats

        mixed = {}
        for track_name, notes in tracks.items():
            if track_name.startswith("_"):
                mixed[track_name] = notes
                continue
            gain = self.track_gains.get(track_name, self._auto_gain(notes))
            new_notes = []
            for n in notes:
                # Determine which section this note belongs to
                section = None
                for sname, sstart, send in section_bounds:
                    if sstart <= n.start < send:
                        section = sname
                        break
                fader = (
                    self.section_faders.get(section, {}).get(track_name, 1.0) if section else 1.0
                )
                total_gain = gain * fader
                new_vel = min(127, max(1, int(n.velocity * total_gain)))
                new_notes.append(
                    NoteInfo(
                        pitch=n.pitch,
                        start=n.start,
                        duration=n.duration,
                        velocity=new_vel,
                        articulation=n.articulation,
                        expression=dict(n.expression),
                    )
                )
            mixed[track_name] = new_notes
        return mixed

    @staticmethod
    def _auto_gain(notes: List[NoteInfo]) -> float:
        """Derive gain from average register: low voices need boost, high need attenuation."""
        if not notes:
            return 1.0
        avg_pitch = sum(n.pitch for n in notes) / len(notes)
        # Low register (< C4=60): boost to compensate perceived quietness
        # High register (> C5=72): attenuate to avoid masking
        if avg_pitch < 48:
            return 1.10
        elif avg_pitch < 60:
            return 1.05
        elif avg_pitch > 84:
            return 0.90
        elif avg_pitch > 72:
            return 0.95
        return 1.0

    def apply_fade_loop_end(
        self, tracks: Dict[str, List[NoteInfo]], loop_start_beat: float, fade_beats: float = 2.0
    ) -> Dict[str, List[NoteInfo]]:
        """Apply exponential fade-out for notes entering the loop transition."""
        faded = {}
        for track_name, notes in tracks.items():
            if track_name.startswith("_"):
                faded[track_name] = notes
                continue
            new_notes = []
            for n in notes:
                if n.start >= loop_start_beat:
                    # Exponential fade factor (matches docstring)
                    pos_in_loop = n.start - loop_start_beat
                    factor = math.exp(-3.0 * pos_in_loop / fade_beats) if fade_beats > 0 else 0.0
                    if factor < 0.01:
                        continue  # drop silent notes
                    new_vel = max(1, int(n.velocity * factor))
                    new_notes.append(
                        NoteInfo(
                            pitch=n.pitch,
                            start=n.start,
                            duration=min(n.duration, n.duration * factor),
                            velocity=new_vel,
                            articulation=n.articulation,
                            expression=dict(n.expression),
                        )
                    )
                else:
                    new_notes.append(n)
            faded[track_name] = new_notes
        return faded
