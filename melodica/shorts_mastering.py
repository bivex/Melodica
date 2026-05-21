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

    # Frequency-band compression: threshold (velocity) + ratio
    band_compression: Dict[str, dict] = field(
        default_factory=lambda: {
            "sub":  {"threshold": 88,  "ratio": 3.0},
            "low":  {"threshold": 92,  "ratio": 2.5},
            "mid":  {"threshold": 98,  "ratio": 2.0},
            "high": {"threshold": 104, "ratio": 1.5},
        }
    )

    @property
    def target_rms_velocity(self) -> int:
        """Convert LUFS target to RMS velocity (curved mapping, clamped)."""
        # -23→58  -18→73  -14→86  -10→99  -6→108
        raw = 86.0 + (self.target_lufs + 14.0) * 4.8
        return int(round(max(45, min(115, raw))))

    @staticmethod
    def _split_band(pitch: int) -> str:
        """Categorize note into frequency band for multiband compression."""
        if pitch < 36:   # Below C2 — sub-bass
            return "sub"
        elif pitch < 60: # C2–B3 — bass/low-mid
            return "low"
        elif pitch < 84: # C4–B5 — midrange
            return "mid"
        else:            # C6+ — high/air
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
        """Soft-knee limiter: 2:1 compression above 90% of ceiling, hard brickwall at ceiling."""
        ceiling = self.limiter_threshold
        knee_start = int(ceiling * 0.9)
        if vel <= knee_start:
            return vel
        if vel >= ceiling:
            return ceiling
        # Quadratic curve: output < input in knee zone, reaches ceiling at boundary
        range_ = ceiling - knee_start
        t = (vel - knee_start) / range_
        return int(round(knee_start + range_ * t * t))

    def _compress(self, vel: int, band: str) -> int:
        """Downward compression: above threshold, reduce by ratio."""
        cfg = self.band_compression.get(band)
        if not cfg:
            return vel
        threshold = cfg["threshold"]
        ratio = cfg["ratio"]
        if vel <= threshold:
            return vel
        excess = vel - threshold
        return int(round(threshold + excess / ratio))

    def _get_pan(self, track_name: str) -> float:
        """Get pan for track; auto-assign deterministic spread for unknown tracks."""
        if track_name in self.track_pan:
            return self.track_pan[track_name]
        h = hash(track_name) & 0xFFFF
        return (h / 0xFFFF - 0.5) * 0.8

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
        # 1. Compute overall RMS across ALL notes in all tracks combined
        all_notes = []
        for tn, notes in tracks.items():
            if not tn.startswith("_"):
                all_notes.extend(notes)

        overall_rms = self._compute_rms(all_notes)
        target = self.target_rms_velocity

        # Calculate a unified global gain factor, capped at 2.0x to avoid extreme distortion
        global_gain = (target / overall_rms) if overall_rms > 5 else 1.0
        global_gain = min(2.0, max(0.5, global_gain))

        # 2. Map global gain to all tracks (preserving relative mix proportions perfectly)
        gain_factors = {tn: global_gain for tn in tracks.keys() if not tn.startswith("_")}

        # 3. Per-note processing: band compression → gain → limiter
        mastered: Dict[str, List[NoteInfo]] = {}
        for track_name, notes in tracks.items():
            if track_name.startswith("_"):
                mastered[track_name] = notes
                continue
            gain = gain_factors.get(track_name, 1.0)
            new_notes: List[NoteInfo] = []
            for n in notes:
                # Band compression → gain → limiter
                compressed = self._compress(n.velocity, self._split_band(n.pitch))
                boosted = int(round(compressed * gain))

                # Soft-knee limiter
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

        # 4. Stereo imaging: generate CC10 pan events per track (skip metadata channels)
        pan_cc_events: Dict[str, List[Tuple[float, int, int]]] = {}
        for track_name, notes in mastered.items():
            if track_name.startswith("_"):
                continue
            pan_val = self._get_pan(track_name)
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
            "band_distribution": {"sub": 0, "low": 0, "mid": 0, "high": 0},
            "target_lufs": self.target_lufs,
            "target_rms": self.target_rms_velocity,
        }
        for track_name, notes in tracks.items():
            if track_name.startswith("_"):
                continue
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
