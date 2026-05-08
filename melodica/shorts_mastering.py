#!/usr/bin/env python3
"""
melodica/shorts_mastering.py — Shared mastering system for Shorts audio generators.

Applies final loudness normalization (LUFS-target simulation via RMS),
real stereo panning (MIDI CC10), multiband compression, and brickwall limiting.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from melodica.types import NoteInfo


@dataclass
class MasteringDesk:
    """Final mastering chain: loudness → compression → imaging → limiting."""

    # LUFS target (simulated via RMS velocity). Spotify/YouTube recommend ~ -14 LUFS.
    # We map LUFS to RMS velocity scale: lower LUFS → lower RMS target.
    # -14 LUFS  ≈  RMS velocity 85
    # -12 LUFS  ≈  RMS velocity 95
    # -10 LUFS  ≈  RMS velocity 105
    target_lufs: float = -14.0

    # Peak ceiling (MIDI velocity 0-127, 125 = brickwall)
    limiter_threshold: int = 125

    # Per-track panning: -1.0 (full left) → 0.0 (center) → +1.0 (full right)
    # Stored as MIDI CC10 values: 0=left, 64=center, 127=right
    track_pan: Dict[str, float] = field(
        default_factory=lambda: {
            "bass": 0.0,  # center (mono bass)
            "drums": 0.0,  # center (kick/snare)
            "sfx": 0.25,  # slight right
            "pad": -0.35,  # wide left
            "voice": 0.0,  # center
            "clicks": 0.1,  # near-center
            "lead": 0.0,  # center
            "fanfare": 0.2,  # right
            "coins": -0.25,  # left
        }
    )

    # Frequency-band compression ratios (RMS-based)
    band_compression: Dict[str, float] = field(
        default_factory=lambda: {
            "low": 0.88,  # bass/drums — gentle compression
            "mid": 0.94,  # lead/voice — light compression
            "high": 0.98,  # SFX/pad — leave mostly intact
        }
    )

    @property
    def target_rms_velocity(self) -> int:
        """Convert LUFS target to RMS velocity (approximate mapping)."""
        # Rough mapping: -14 LUFS → 85 RMS, linear per 2 LUFS ≈ +10 RMS
        # -16 LUFS → 75, -12 → 95, -10 → 105
        return int(round(85 + (self.target_lufs + 14) * 5))

    @staticmethod
    def _split_band(pitch: int) -> str:
        """Categorize note into frequency band for multiband compression."""
        if pitch < 48:  # C2 and below — sub-bass
            return "low"
        elif pitch < 72:  # C2-C4 — low-mid/bass
            return "low"
        elif pitch < 96:  # C4-C6 — midrange (vocals, lead, snare)
            return "mid"
        else:  # C6+ — highs (cymbals, FX)
            return "high"

    @staticmethod
    def _compute_rms(notes: List[NoteInfo]) -> float:
        """Calculate RMS velocity of track."""
        if not notes:
            return 0.0
        import math

        sum_sq = sum(n.velocity**2 for n in notes)
        return math.sqrt(sum_sq / len(notes))

    def _pan_to_cc10(self, pan_norm: float) -> int:
        """Convert normalized pan (-1…+1) to MIDI CC10 value (0…127)."""
        # pan_norm: -1=left, 0=center, +1=right
        # CC10: 0=left, 64=center, 127=right
        return int(round(64 + pan_norm * 63))

    def _apply_limiter(self, vel: int) -> int:
        """Brickwall limiter at threshold with soft-knee approach."""
        if vel > self.limiter_threshold:
            return self.limiter_threshold
        return vel

    def apply_mastering(
        self, tracks: Dict[str, List[NoteInfo]]
    ) -> Tuple[Dict[str, List[NoteInfo]], Dict[str, List[Tuple[float, int, int]]]]:
        """
        Apply full mastering chain.

        Returns
        -------
        (mastered_tracks, pan_cc_events)
            pan_cc_events: {track_name: [(time, cc10_value), ...]}
        """
        # 1. RMS analysis per track
        rms_by_track = {tn: self._compute_rms(notes) for tn, notes in tracks.items()}

        # 2. Gain factors to match target RMS
        target = self.target_rms_velocity
        gain_factors = {}
        for tn, rms in rms_by_track.items():
            gain_factors[tn] = (target / rms) if rms > 5 else 1.0

        # 3. Per-note processing: band compression → gain → limiter
        mastered: Dict[str, List[NoteInfo]] = {}
        for track_name, notes in tracks.items():
            gain = gain_factors.get(track_name, 1.0)
            band_factor_map = self.band_compression
            new_notes: List[NoteInfo] = []
            for n in notes:
                band = self._split_band(n.pitch)
                band_factor = band_factor_map.get(band, 1.0)
                total_gain = gain * band_factor

                # Apply gain with soft-knee
                boosted = int(round(n.velocity * total_gain))
                if boosted > 110:
                    boosted = int(round(110 + (boosted - 110) * 0.5))

                # Brickwall limiter
                new_vel = self._apply_limiter(boosted)

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
            new_notes.sort(key=lambda n: n.start)
            mastered[track_name] = new_notes

        # 4. Stereo imaging: generate CC10 pan events per track
        pan_cc_events: Dict[str, List[Tuple[float, int, int]]] = {}
        for track_name, notes in mastered.items():
            pan_val = self.track_pan.get(track_name, 0.0)
            cc10_val = self._pan_to_cc10(pan_val)
            if notes:
                # Place pan CC at first note time of track
                first_time = notes[0].start
                pan_cc_events[track_name] = [(first_time, 10, cc10_val)]

        return mastered, pan_cc_events

    def quality_report(self, tracks: Dict[str, List[NoteInfo]]) -> dict[str, object]:
        """Generate mastering quality metrics."""
        report: dict[str, object] = {
            "peak_velocity": 0,
            "rms_velocity": 0.0,
            "clipping_notes": 0,
            "total_notes": 0,
            "band_distribution": {"low": 0, "mid": 0, "high": 0},
            "target_lufs": self.target_lufs,
            "target_rms": self.target_rms_velocity,
        }
        for notes in tracks.values():
            for n in notes:
                report["total_notes"] += 1
                report["peak_velocity"] = max(report["peak_velocity"], n.velocity)
                report["rms_velocity"] += n.velocity**2
                if n.velocity >= self.limiter_threshold:
                    report["clipping_notes"] += 1
                band = self._split_band(n.pitch)
                report["band_distribution"][band] += 1
        if report["total_notes"] > 0:
            report["rms_velocity"] = (report["rms_velocity"] / report["total_notes"]) ** 0.5
        return report
