# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
composer/album_pipeline.py — One-call track production pipeline.

Generates → mixes → masters → exports a single track or full album.
Album scripts only write generators and call produce_track().

Usage:
    from melodica.composer.album_pipeline import produce_track, Mood

    produce_track(
        tracks={"flute": notes, "pad": pad_notes},
        bpm=48,
        instruments={"flute": 73, "pad": 89},
        path="output/album/01_Track.mid",
        mood=Mood.AMBIENT,
        key=KEY,
    )
"""

from __future__ import annotations

import math
import random
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

from melodica.types import NoteInfo, Scale
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.composer.psychoacoustic import psycho_verify, PsychoConfig, PsychoReport
from melodica.composer.automation import AutomationCurve


# ---------------------------------------------------------------------------
# Pipeline infrastructure — pluggable stage architecture
# ---------------------------------------------------------------------------


@dataclass
class TrackState:
    """Mutable state passed between pipeline stages."""

    tracks: Dict[str, List[NoteInfo]]
    profiles: Dict = field(default_factory=dict)
    mood_profile: _MoodProfile | None = None
    pan_overrides: Dict = field(default_factory=dict)
    psycho_report: PsychoReport | None = None
    mastered: Dict[str, List[NoteInfo]] | None = None
    cc_events: Dict[str, List[Tuple[float, int, int]]] = field(default_factory=dict)


@dataclass
class Stage:
    """A single pipeline stage."""

    name: str
    fn: "callable"
    enabled: bool = True


# ---------------------------------------------------------------------------
# Mood presets — define loudness, dynamics, and psychoacoustic strictness
# ---------------------------------------------------------------------------


class Mood(Enum):
    AMBIENT = "ambient"
    INTIMATE = "intimate"
    CINEMATIC = "cinematic"
    AGGRESSIVE = "aggressive"
    CHAMBER = "chamber"
    EXPERIMENTAL = "experimental"


@dataclass
class _MoodProfile:
    lufs: float
    dynamics_range: float  # 0.0=compressed, 1.0=wide dynamics
    psycho_aggressive: bool  # remove masked notes vs just reduce velocity
    bass_boost: float  # extra gain for sub-bass tracks
    brightness_ceiling: int  # max velocity for high register


_MOOD_PROFILES = {
    Mood.AMBIENT: _MoodProfile(-20.0, 0.8, False, 0.95, 110),
    Mood.INTIMATE: _MoodProfile(-18.0, 0.7, False, 0.90, 112),
    Mood.CINEMATIC: _MoodProfile(-14.0, 0.5, True, 1.10, 120),
    Mood.AGGRESSIVE: _MoodProfile(-12.0, 0.3, True, 1.15, 125),
    Mood.CHAMBER: _MoodProfile(-16.0, 0.6, False, 1.00, 115),
    Mood.EXPERIMENTAL: _MoodProfile(-15.0, 0.9, False, 1.00, 127),
}


# ---------------------------------------------------------------------------
# Track analysis — auto-detect role from register + density
# ---------------------------------------------------------------------------


class Role(Enum):
    LEAD = "lead"
    PAD = "pad"
    BASS = "bass"
    PERC = "perc"
    STRINGS = "strings"
    CHOIR = "choir"
    FX = "fx"


@dataclass
class _TrackProfile:
    avg_pitch: float
    pitch_range: float
    density: float  # notes per beat
    rms_velocity: float
    role: Role
    entry_beat: float = 0.0  # [FIX 2] when this track first plays
    note_count: int = 0


_ROLE_HEURISTICS = {
    "bass": (lambda p, d: p < 48),
    "lead": (lambda p, d: p > 60 and d > 0.15),
    "pad": (lambda p, d: d < 0.1),
    "perc": (lambda p, d: d > 0.3 and p > 70),
    "strings": (lambda p, d: 40 < p < 75 and 0.05 < d < 0.3),
    "choir": (lambda p, d: 50 < p < 70 and d < 0.15),
    "fx": (lambda p, d: p > 80 and d < 0.05),
}

_NAME_HINTS: Dict[str, Role] = {
    "bass": Role.BASS,
    "kick": Role.PERC,
    "snare": Role.PERC,
    "hihat": Role.PERC,
    "hat": Role.PERC,
    "perc": Role.PERC,
    "drum": Role.PERC,
    "pad": Role.PAD,
    "wash": Role.PAD,
    "texture": Role.PAD,
    "chords": Role.PAD,
    "keys": Role.PAD,
    "rhodes": Role.PAD,
    "choir": Role.CHOIR,
    "voice": Role.CHOIR,
    "string": Role.STRINGS,
    "cello": Role.STRINGS,
    "viola": Role.STRINGS,
    "violin": Role.STRINGS,
    "lead": Role.LEAD,
    "solo": Role.LEAD,
    "flute": Role.LEAD,
    "clarinet": Role.LEAD,
    "harp": Role.STRINGS,
    "organ": Role.STRINGS,
    "guitar": Role.LEAD,
    "fx": Role.FX,
    "glass": Role.FX,
    "banjo": Role.LEAD,
    "koto": Role.LEAD,
    "bowl": Role.FX,
    "riser": Role.FX,
    "impact": Role.FX,
}


def _analyze_track(name: str, notes: List[NoteInfo], total_dur: float = 0.0) -> _TrackProfile:
    """Analyze a track's register, density, and assign a role."""
    if not notes:
        return _TrackProfile(60, 0, 0, 0, Role.PAD)

    avg_pitch = sum(n.pitch for n in notes) / len(notes)
    min_p = min(n.pitch for n in notes)
    max_p = max(n.pitch for n in notes)
    span = max(n.start + n.duration for n in notes) - notes[0].start
    total_dur = max(total_dur, span, 1.0)
    density = len(notes) / total_dur
    rms = math.sqrt(sum(n.velocity**2 for n in notes) / len(notes))
    entry = min(n.start for n in notes)

    name_lower = name.lower()
    role_final = Role.LEAD
    for hint, role in _NAME_HINTS.items():
        if hint in name_lower:
            role_final = role
            break
    else:
        if avg_pitch < 48:
            role_final = Role.BASS
        elif density < 0.08:
            role_final = Role.PAD
        elif avg_pitch > 75 and density < 0.05:
            role_final = Role.FX
        elif avg_pitch > 60 and density > 0.15:
            role_final = Role.LEAD
        elif 40 < avg_pitch < 75 and 0.05 < density < 0.3:
            role_final = Role.STRINGS
        else:
            role_final = Role.LEAD

    return _TrackProfile(
        avg_pitch, max_p - min_p, density, rms, role_final, entry_beat=entry, note_count=len(notes)
    )


# ---------------------------------------------------------------------------
# Genre-based pan profiles
# ---------------------------------------------------------------------------

_ROLE_PAN_PROFILES: Dict[str, Dict[Role, float]] = {
    "techno": {
        Role.LEAD: 0.08,
        Role.BASS: 0.0,
        Role.PAD: -0.30,
        Role.PERC: 0.15,
        Role.STRINGS: 0.20,
        Role.CHOIR: -0.10,
        Role.FX: 0.30,
    },
    "rnb": {
        Role.LEAD: 0.10,
        Role.BASS: 0.0,
        Role.PAD: -0.20,
        Role.STRINGS: 0.25,
        Role.CHOIR: -0.15,
        Role.PERC: 0.05,
    },
    "trap": {
        Role.LEAD: 0.12,
        Role.BASS: 0.0,
        Role.PAD: -0.40,
        Role.FX: 0.45,
        Role.PERC: 0.08,
    },
    "neosoul": {
        Role.LEAD: 0.06,
        Role.BASS: 0.0,
        Role.PAD: -0.25,
        Role.STRINGS: 0.30,
        Role.CHOIR: -0.20,
        Role.PERC: 0.10,
    },
    "hip_hop": {
        Role.LEAD: 0.10,
        Role.BASS: 0.0,
        Role.PAD: -0.35,
        Role.STRINGS: 0.20,
        Role.CHOIR: -0.15,
        Role.PERC: 0.05,
        Role.FX: 0.40,
    },
    "lofi": {
        Role.LEAD: 0.05,
        Role.BASS: 0.0,
        Role.PAD: -0.15,
        Role.STRINGS: 0.18,
        Role.CHOIR: -0.12,
        Role.PERC: -0.08,
    },
    "gospel": {
        Role.LEAD: 0.08,
        Role.BASS: 0.0,
        Role.PAD: -0.20,
        Role.STRINGS: 0.25,
        Role.CHOIR: -0.18,
        Role.PERC: 0.0,
    },
}

# Fallback default (kept separate from profiles so every entry stays in one place)
_ROLE_PAN: Dict[Role, float] = _ROLE_PAN_PROFILES["techno"]

# Neutral default genre: 'lofi' has the most centred pan profile (smallest
# deviations), so it is the safest fallback when a caller omits `genre`.
DEFAULT_GENRE = "lofi"


def _get_role_pan_map(genre: str | None = None) -> Dict[Role, float]:
    """Return the pan map for a given genre, falling back to DEFAULT_GENRE."""
    return _ROLE_PAN_PROFILES.get(genre or DEFAULT_GENRE, _ROLE_PAN_PROFILES[DEFAULT_GENRE])


def _get_pan_for_role(role: Role, genre: str | None = None) -> float:
    """Single-role lookup — used outside the full-stage pipeline."""
    return _get_role_pan_map(genre).get(role, 0.0)


# ---------------------------------------------------------------------------
# Auto-spread: resolve pan conflicts with role-aware priority rules
# ---------------------------------------------------------------------------

# Protected roles always centred — never moved by spread logic
_PROTECTED_CENTER: set = {Role.BASS}


def _auto_spread_panning(
    tracks: "Dict[str, List[NoteInfo]]",
    profiles: "Dict[str, _TrackProfile]",
    role_pan_map: "Dict[Role, float]",
) -> "Dict[str, float]":
    """Resolve register conflicts — role-aware priority, no Role keys in output.

    Returns {track_name: pan_norm} so MasteringDesk receives plain string keys.
    Rules:
      1. BASS always sits at centre.
      2. PERC gets genre default (slight offset allowed).
      3. PAD vs PAD in same register -> wide +/-0.40 spread.
      4. FX gets outermost alternating edges +/-0.60.
      5. LEAD: multiple LEADs in same register -> spread +/-0.15.
      6. Remaining LEAD, STRINGS, CHOIR keep genre-default pan.
    """
    result: Dict[str, float] = {}
    fxs: List[str] = []
    pads: List[str] = []
    leads: List[str] = []

    for name, prof in profiles.items():
        if prof.role == Role.FX:
            fxs.append(name)
        elif prof.role == Role.PAD:
            pads.append(name)
        elif prof.role == Role.LEAD:
            leads.append(name)

    # 1. BASS — permanently centre
    for name, prof in profiles.items():
        if prof.role in _PROTECTED_CENTER:
            result[name] = 0.0

    # 2. PERC — genre default (slight offset)
    for name, prof in profiles.items():
        if prof.role == Role.PERC and name not in result:
            result[name] = role_pan_map.get(Role.PERC, 0.0)

    # 3. FX — alternating outer edges
    for idx, name in enumerate(fxs):
        result[name] = 0.60 if idx % 2 == 0 else -0.60

    # 4. PAD — detect same-register pair conflicts -> +/-0.40 wide
    paired: set = set()
    for i, a in enumerate(pads):
        if a in paired:
            continue
        for b in pads[i + 1:]:
            if b in paired:
                continue
            if abs(profiles[a].avg_pitch - profiles[b].avg_pitch) < 8:
                result[a] = -0.40
                result[b] = +0.40
                paired.update([a, b])
                break
    for name in pads:
        if name not in result:
            result[name] = role_pan_map.get(Role.PAD, -0.30)  # genre default

    # 5. LEAD — spread multiple LEADs if they share a register
    lead_default = role_pan_map.get(Role.LEAD, 0.08)
    if len(leads) >= 2:
        paired_l: set = set()
        for i, a in enumerate(leads):
            if a in paired_l:
                continue
            for b in leads[i + 1:]:
                if b in paired_l:
                    continue
                if abs(profiles[a].avg_pitch - profiles[b].avg_pitch) < 10:
                    result[a] = lead_default - 0.15
                    result[b] = lead_default + 0.15
                    paired_l.update([a, b])
                    break
    for name in leads:
        if name not in result:
            result[name] = lead_default

    # 6. STRINGS, CHOIR and any remaining -> genre default
    for name, prof in profiles.items():
        if name not in result:
            result[name] = role_pan_map.get(prof.role, 0.0)

    return result




# ---------------------------------------------------------------------------
# PanValidator — post-master verification of all pan assignments
# ---------------------------------------------------------------------------

_PAN_RULES: Dict[Role, tuple[float, float]] = {
    Role.BASS: (-0.05, 0.05),  # strict centre
    Role.LEAD: (-0.15, 0.15),  # slight offset allowed per genre
    Role.PAD: (-0.60, 0.60),   # flexible — genre decides
    Role.PERC: (-0.20, 0.20),  # near centre
    Role.STRINGS: (-0.45, 0.45),
    Role.CHOIR: (-0.40, 0.40),
    Role.FX: (-0.65, 0.65),    # widest range
}


def _check_frequency_pan_conflicts(
    pan_map: Dict[str, float],
    profiles: Dict[str, _TrackProfile],
    register_threshold: float = 6.0,
    pan_threshold: float = 0.15,
) -> list[tuple[str, str, str]]:
    """Detect masking: two tracks in same register AND same pan position.

    Returns list of (track_a, track_b, severity) tuples.
    """
    conflicts: list[tuple[str, str, str]] = []
    names = list(pan_map.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            pa, pb = profiles.get(a), profiles.get(b)
            if not pa or not pb:
                continue
            same_register = abs(pa.avg_pitch - pb.avg_pitch) < register_threshold
            same_pan = abs(pan_map[a] - pan_map[b]) < pan_threshold
            if same_register and same_pan:
                # Skip bass/perc centre pairs
                if pa.role in (Role.BASS, Role.PERC) and pb.role in (Role.BASS, Role.PERC):
                    continue
                severity = "HIGH" if abs(pa.avg_pitch - pb.avg_pitch) < 3 else "MED"
                conflicts.append((a, b, severity))
    return conflicts


@dataclass
class PanReport:
    """Structured result from PanValidator."""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    width_score: float = 0.0
    mono_compatible: bool = True


class PanValidator:
    """Validates pan map for role boundaries, frequency conflicts, and stereo width."""

    def validate(self, pan_map: Dict[str, float], profiles: Dict[str, _TrackProfile]) -> list[str]:
        """Return list of warning strings for backward compatibility."""
        report = self.full_validate(pan_map, profiles)
        return report.errors + report.warnings

    def full_validate(self, pan_map: Dict[str, float], profiles: Dict[str, _TrackProfile]) -> PanReport:
        """Full validation returning structured PanReport."""
        import statistics as _stat

        errors: list[str] = []
        warnings: list[str] = []
        seen: list[tuple[str, float, Role]] = []

        for name, pan in pan_map.items():
            prof = profiles.get(name)
            if not prof:
                continue
            role = prof.role
            lo, hi = _PAN_RULES.get(role, (-1.0, 1.0))
            if not (lo <= pan <= hi):
                errors.append(
                    f"pan={pan:+.2f} вне [{lo},{hi}] для {name} ({role.value})"
                )
            seen.append((name, pan, role))

        # Detect identical pan positions (except bass/perc centre)
        for i in range(len(seen)):
            for j in range(i + 1, len(seen)):
                a_name, a_pan, a_role = seen[i]
                b_name, b_pan, b_role = seen[j]
                if abs(a_pan - b_pan) < 0.005:
                    if not (a_role in (Role.BASS, Role.PERC) and abs(a_pan) < 0.1):
                        warnings.append(
                            f"{a_name} и {b_name} стоят на одной точке: pan={a_pan:+.2f}"
                        )

        # Frequency-pan conflict detection
        conflicts = _check_frequency_pan_conflicts(pan_map, profiles)
        for a, b, sev in conflicts:
            warnings.append(f"Маскировка ({sev}): {a} ↔ {b} — один регистр и pan")

        # Stereo width score
        non_bass_pans = [pan for (_, pan, role) in seen if role != Role.BASS]
        width_score = round(_stat.stdev(non_bass_pans), 3) if len(non_bass_pans) > 1 else 0.0
        if width_score < 0.10 and len(non_bass_pans) >= 3:
            warnings.append(f"Stereo width={width_score:.2f} — очень узкий микс")
        elif width_score > 0.50:
            warnings.append(f"Stereo width={width_score:.2f} — очень широкий микс")

        # Mono compatibility: sum to mono, check if any pair cancels
        mono_compatible = all(abs(pan) < 0.80 for _, pan, _ in seen)

        return PanReport(
            errors=errors,
            warnings=warnings,
            width_score=width_score,
            mono_compatible=mono_compatible,
        )




# ---------------------------------------------------------------------------
# Pretty-print pan map for verbose output
# ---------------------------------------------------------------------------

def _print_pan_map(
    profiles: Dict[str, _TrackProfile],
    pan_map: Dict[str, float],
    mood_profile: _MoodProfile,
) -> None:
    """Print a human-readable pan map: bar-chart + per-track position."""
    BAR_LEN = 10  # characters per half-width

    def _bar(pan_norm: float) -> str:
        """12-char bar: C=centre, L=left, R=right."""
        mid = BAR_LEN
        if abs(pan_norm) < 0.02:
            centre = "█" * BAR_LEN
            return f"  {centre}  C"
        if pan_norm < 0:
            left_px  = int(abs(pan_norm) * BAR_LEN)
            rest     = BAR_LEN - left_px
            bar = "█" * left_px + "░" * rest
            return f"  {bar}  L({pan_norm:+.2f})"
        else:
            right_px = int(pan_norm * BAR_LEN)
            rest     = BAR_LEN - right_px
            bar = "░" * rest + "█" * right_px
            return f"  {bar}  R({pan_norm:+.2f})"

    print("   Pan Map:")
    max_len = max((len(n) for n in pan_map), default=5)
    for name in sorted(pan_map.keys()):
        pan = pan_map[name]
        role = profiles.get(name)
        role_str = f"({role.role.value})" if role else ""
        print(f"   {name:<{max_len+1}s} {_bar(pan)}  {role_str}")

    non_centre = [abs(v) for v in pan_map.values() if abs(v) > 0.05]
    if non_centre:
        width = round(sum(non_centre) / len(non_centre), 3)
        print(f"   Stereo Width: {width:.3f}")
    else:
        print("   Stereo Width: 0.000  (mono)")


# ---------------------------------------------------------------------------
# Auto-mix: role-based gain, density-adaptive, entry/exit, register shaping
# ---------------------------------------------------------------------------

_ROLE_GAINS: Dict[Role, float] = {
    Role.LEAD: 0.85,
    Role.BASS: 0.55,
    Role.PAD: 0.35,
    Role.PERC: 1.00,
    Role.STRINGS: 0.65,
    Role.CHOIR: 0.45,
    Role.FX: 0.50,
}

_ROLE_PAN: Dict[Role, float] = {
    Role.LEAD: 0.0,
    Role.BASS: 0.0,
    Role.PAD: -0.30,
    Role.PERC: 0.15,
    Role.STRINGS: 0.20,
    Role.CHOIR: -0.10,
    Role.FX: 0.30,
}


def _density_gain_factor(density: float) -> float:
    """[FIX 6] Sparse tracks need boost, dense tracks need duck."""
    if density < 0.05:
        return 1.25
    elif density < 0.15:
        return 1.10
    elif density < 0.5:
        return 1.0
    elif density < 2.0:
        return 0.90
    elif density < 10.0:
        return 0.80
    else:
        return 0.70


def _auto_mix(
    tracks: Dict[str, List[NoteInfo]],
    mood_profile: _MoodProfile,
    genre: str | None = None,
) -> Tuple[Dict[str, List[NoteInfo]], Dict[str, _TrackProfile], Dict[str, float]]:
    """Analyze tracks, assign gains by role + density, apply register shaping."""
    # Compute total duration from all tracks
    total_dur = 0.0
    for name, notes in tracks.items():
        if name.startswith("_") or not notes:
            continue
        for n in notes:
            total_dur = max(total_dur, n.start + n.duration)

    profiles = {}
    for name, notes in tracks.items():
        if not notes or name.startswith("_"):
            continue
        profiles[name] = _analyze_track(name, notes, total_dur)

    # Build gain map: role default x density x register tweak x mood bass boost
    gains: Dict[str, float] = {}
    for name, prof in profiles.items():
        base = _ROLE_GAINS.get(prof.role, 0.80)
        density_factor = _density_gain_factor(prof.density)

        # Register tweak
        if prof.avg_pitch < 48:
            reg_tweak = 1.10 * mood_profile.bass_boost
        elif prof.avg_pitch < 60:
            reg_tweak = 1.03
        elif prof.avg_pitch > 84:
            reg_tweak = 0.85
        elif prof.avg_pitch > 72:
            reg_tweak = 0.92
        else:
            reg_tweak = 1.0

        gains[name] = base * density_factor * reg_tweak

    # [FIX 4] Register overlap: same-register non-perc/non-fx → duck quieter one
    names = [n for n in profiles if profiles[n].role not in (Role.PERC, Role.FX)]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = profiles[names[i]], profiles[names[j]]
            if abs(a.avg_pitch - b.avg_pitch) < 8:
                quieter = names[i] if a.rms_velocity < b.rms_velocity else names[j]
                gains[quieter] *= 0.75

    # [FIX 1] Single MixingDesk pass
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update(gains)
    mixed = desk.apply_mixing(tracks, [], 120)

    # Role-based pan map for this genre
    role_pan_map = _get_role_pan_map(genre)

    return mixed, profiles, role_pan_map


# ---------------------------------------------------------------------------
# [FIX 1] Sidechain ducking — bass/pad duck when perc hits
# ---------------------------------------------------------------------------


def _sidechain_duck(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    duck_amount: float = 0.45,
    window: float = 0.15,
) -> Dict[str, List[NoteInfo]]:
    """Reduce velocity of bass/pad notes that overlap perc hits within window."""
    perc_names = [n for n, p in profiles.items() if p.role == Role.PERC]
    duck_names = [n for n, p in profiles.items() if p.role in (Role.BASS, Role.PAD)]

    if not perc_names or not duck_names:
        return tracks

    # Collect perc hit times
    hit_times: List[float] = []
    for pn in perc_names:
        for n in tracks.get(pn, []):
            hit_times.append(n.start)

    if not hit_times:
        return tracks

    hit_times.sort()
    result = {}
    for tname, notes in tracks.items():
        if tname.startswith("_") or tname not in duck_names:
            result[tname] = notes
            continue

        new_notes = []
        for n in notes:
            # Check if any perc hit falls within the sounding range of the note [n.start, n.start + n.duration]
            # [FIX] Also account for a small look-ahead/look-behind window
            lo = n.start - window
            hi = n.start + n.duration + window

            # Binary search for closest hit
            import bisect

            idx = bisect.bisect_left(hit_times, lo)
            duck = False
            if idx < len(hit_times) and hit_times[idx] <= hi:
                duck = True

            if duck:
                new_vel = max(10, int(n.velocity * (1.0 - duck_amount)))
                new_notes.append(
                    NoteInfo(
                        pitch=n.pitch,
                        start=n.start,
                        duration=n.duration,
                        velocity=new_vel,
                        articulation=n.articulation,
                        expression=n.expression,
                    )
                )
            else:
                new_notes.append(n)
        result[tname] = new_notes

    return result


# ---------------------------------------------------------------------------
# [FIX 7] Swing / humanization — timing + velocity jitter for dense tracks
# ---------------------------------------------------------------------------



# Per-instrument humanization profiles:
#   (timing_beats, vel_jitter, dur_factor, groove)
# timing_beats  — max onset offset in beats (at 120bpm: 0.02=10ms, 0.05=25ms)
# vel_jitter    — max ±velocity randomisation
# dur_factor    — duration scale jitter (0.0=none, 0.12=±12%)
# groove        — "straight"|"lay_back"|"push"
_HUMANIZE_PROFILES: Dict[str, tuple[float, int, float, str]] = {
    # Solo / lead woodwinds — expressive, slight push
    "flute":     (0.025, 6,  0.08, "push"),
    "oboe":      (0.022, 5,  0.07, "push"),
    "clarinet":  (0.025, 6,  0.08, "push"),
    "bassoon":   (0.020, 5,  0.07, "lay_back"),
    # Strings — warm lay-back, noticeable dur variation (bow length)
    "violin":    (0.035, 8,  0.12, "lay_back"),
    "viola":     (0.030, 7,  0.12, "lay_back"),
    "cello":     (0.025, 6,  0.10, "lay_back"),
    "strings":   (0.030, 7,  0.12, "lay_back"),
    # Brass — slightly late, wide vel (breath support variation)
    "horn":      (0.030, 8,  0.06, "lay_back"),
    "brass":     (0.025, 9,  0.06, "lay_back"),
    "trumpet":   (0.020, 7,  0.05, "straight"),
    "trombone":  (0.030, 8,  0.07, "lay_back"),
    # Keyboard / harp — tight timing, light vel, minimal dur jitter
    "harp":      (0.015, 5,  0.04, "straight"),
    "piano":     (0.018, 6,  0.04, "straight"),
    "celesta":   (0.015, 4,  0.03, "straight"),
    "glock":     (0.012, 4,  0.03, "straight"),
    "glockenspiel": (0.012, 4, 0.03, "straight"),
    # Bass — very tight, minimal timing, slight vel variation
    "bass":      (0.012, 4,  0.03, "lay_back"),
    "contrabass":(0.010, 3,  0.03, "lay_back"),
    "pedal":     (0.008, 2,  0.02, "straight"),
    # Choir — loose timing, wide vel, long dur
    "choir":     (0.040, 10, 0.15, "lay_back"),
    "voice":     (0.040, 10, 0.15, "lay_back"),
    # Timpani / perc — tight timing, wide vel
    "timp":      (0.010, 10, 0.02, "straight"),
    "perc":      (0.010, 10, 0.02, "straight"),
    # Generic lead
    "lead":      (0.025, 6,  0.08, "straight"),
    "canon":     (0.030, 7,  0.10, "lay_back"),
}

_HUMANIZE_ROLE_DEFAULTS: Dict[Role, tuple[float, int, float, str]] = {
    Role.LEAD:    (0.025, 6,  0.08, "straight"),
    Role.STRINGS: (0.030, 7,  0.12, "lay_back"),
    Role.CHOIR:   (0.040, 10, 0.15, "lay_back"),
    Role.BASS:    (0.012, 4,  0.03, "lay_back"),
    Role.PAD:     (0.020, 5,  0.06, "straight"),
    Role.PERC:    (0.010, 10, 0.02, "straight"),
    Role.FX:      (0.015, 3,  0.02, "straight"),
}


def _humanize_profile(tname: str, role: Role) -> tuple[float, int, float, str]:
    """Return (timing, vel_jitter, dur_factor, groove) for this track."""
    name_lower = tname.lower()
    for key, profile in _HUMANIZE_PROFILES.items():
        if key in name_lower:
            return profile
    return _HUMANIZE_ROLE_DEFAULTS.get(role, (0.020, 5, 0.06, "straight"))


def _apply_humanization(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    swing_amount: float = 0.02,   # kept for backward compat; overridden by per-instrument
    vel_jitter: int = 4,          # kept for backward compat; overridden by per-instrument
) -> Dict[str, List[NoteInfo]]:
    """Add per-instrument humanization: micro-timing, velocity scatter, duration jitter.

    Each instrument family gets its own profile:
      - timing_beats: onset jitter (strings lay_back ±0.035, harp tight ±0.015)
      - vel_jitter:   velocity scatter (choir ±10, pedal ±2)
      - dur_factor:   duration variation (strings ±12%, harp ±4%)
      - groove:       push/lay_back/straight bias

    Density-adaptive: at density ≥ 2.0 timing jitter drops to 10% to prevent
    note ordering inversion in fast passages.
    """
    result = {}
    for tname, notes in tracks.items():
        if tname.startswith("_"):
            result[tname] = notes
            continue

        prof = profiles.get(tname)
        if not prof:
            result[tname] = notes
            continue

        # Skip FX tracks — no humanization needed
        if prof.role == Role.FX:
            result[tname] = notes
            continue

        t_base, v_base, dur_base, groove = _humanize_profile(tname, prof.role)

        # Density-adaptive timing scale: fast passages get tighter timing
        density_factor = min(1.0, prof.density / 2.0)
        t_scale = 1.0 - 0.90 * density_factor   # 1.0 → 0.10
        effective_t = t_base * t_scale

        # Velocity jitter scales UP at high density (expression via dynamics)
        v_scale = 1.0 + 1.0 * density_factor    # 1.0 → 2.0
        effective_v = max(1, int(v_base * v_scale))

        rng = random.Random(hash(tname) & 0xFFFFFFFF)
        new_notes = []
        for n in notes:
            # Timing offset with groove bias
            t_jitter = rng.gauss(0.0, effective_t * 0.4)
            if groove == "lay_back":
                t_jitter += effective_t * 0.25
            elif groove == "push":
                t_jitter -= effective_t * 0.20

            # Velocity scatter (gaussian, clamped)
            v_jit = int(rng.gauss(0.0, effective_v * 0.5))

            # Duration jitter (articulation humanization)
            dur_jit = 1.0 + rng.gauss(0.0, dur_base * 0.4)
            dur_jit = max(0.85, min(1.20, dur_jit))

            new_notes.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=max(0.0, n.start + t_jitter),
                    duration=max(0.05, n.duration * dur_jit),
                    velocity=max(10, min(127, n.velocity + v_jit)),
                    articulation=n.articulation,
                    expression=n.expression,
                )
            )
        result[tname] = new_notes

    return result


# ---------------------------------------------------------------------------
# [FIX 2] Instrument entry/exit — CC11 fade-in for late-entering tracks
# ---------------------------------------------------------------------------


def _generate_entry_fades(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    total_dur: float,
    fade_beats: float = 8.0,
) -> Dict[str, List[Tuple[float, int, int]]]:
    """Generate CC11 expression events for tracks that enter late."""
    cc_events: Dict[str, List[Tuple[float, int, int]]] = {}
    threshold = total_dur * 0.1  # enter after 10% of track

    for tname, prof in profiles.items():
        if prof.entry_beat < threshold or prof.role in (Role.PERC, Role.FX):
            continue

        notes = tracks.get(tname, [])
        if not notes:
            continue

        events = []
        entry = prof.entry_beat
        # Ramp CC11 from 20 → 100 over fade_beats
        steps = max(4, int(fade_beats / 0.5))
        for i in range(steps + 1):
            t = entry - fade_beats + (i / steps) * fade_beats
            if t < 0:
                continue
            val = int(20 + (80 * i / steps))
            events.append((t, 11, val))

        # Set full expression at entry
        events.append((entry + 0.01, 11, 100))
        cc_events[tname] = events

    return cc_events


# ---------------------------------------------------------------------------
# [FIX 9] Reverb CC91 — role-based reverb send
# ---------------------------------------------------------------------------

_ROLE_REVERB: Dict[Role, int] = {
    Role.LEAD: 50,
    Role.BASS: 20,
    Role.PAD: 70,
    Role.PERC: 25,
    Role.STRINGS: 55,
    Role.CHOIR: 65,
    Role.FX: 40,
}


def _generate_reverb_sends(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    mood_profile: _MoodProfile,
    mood: Mood | None = None,
) -> Dict[str, List[Tuple[float, int, int]]]:
    """Generate CC91 reverb send events per track."""
    cc_events: Dict[str, List[Tuple[float, int, int]]] = {}

    # Dense mixes need more reverb
    total_notes = sum(p.note_count for p in profiles.values())
    density_boost = min(20, total_notes // 200)

    for tname, prof in profiles.items():
        notes = tracks.get(tname, [])
        if not notes:
            continue

        base_reverb = _ROLE_REVERB.get(prof.role, 40)
        reverb = min(127, base_reverb + density_boost)

        # Ambient moods get more reverb, aggressive gets less
        if mood_profile.lufs < -18:
            reverb = min(127, reverb + 15)
        elif mood_profile.lufs > -13:
            reverb = max(10, reverb - 10)

        first_time = notes[0].start
        cc_events[tname] = [(first_time, 91, reverb)]

    return cc_events


# ---------------------------------------------------------------------------
# [FIX 10] Echo/delay CC93 — detect echo tracks and add delay send
# ---------------------------------------------------------------------------


def _generate_delay_sends(
    tracks: Dict[str, List[NoteInfo]], profiles: Dict[str, _TrackProfile]
) -> Dict[str, List[Tuple[float, int, int]]]:
    """Generate CC93 delay send for tracks with 'echo' or 'delay' in name."""
    cc_events: Dict[str, List[Tuple[float, int, int]]] = {}

    for tname, notes in tracks.items():
        name_lower = tname.lower()
        if "echo" not in name_lower and "delay" not in name_lower:
            continue

        if not notes:
            continue

        # Delay send level based on how different the track is from the source
        delay_level = 60 if "far" in name_lower else 40
        first_time = notes[0].start
        cc_events[tname] = [(first_time, 93, delay_level)]

    return cc_events





def _generate_pan_automation(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    mood_profile: _MoodProfile,
    mood: Mood | None = None,
    spread_map: Dict[str, float] | None = None,
    tension: float | None = None,
    section_breaks: List[Tuple[float, str]] | None = None,
) -> Dict[str, List[Tuple[float, int, int]]]:
    """Generate CC10 pan automation with anchors, tension-aware width, and section events.

    Features:
      - CC10 anchors every 4 bars for DAW seek reliability
      - PAD: sine-LFO with tension-aware width (narrow=calm, wide=energy)
      - FX: right-to-centre sweep at entry beat
      - Section events: drop=spread, break=collapse, intro/outro=gradual

    Args:
        tension: 0.0 (calm) to 1.0 (chaotic) from harmonic analysis.
        section_breaks: [(beat_position, section_name), ...] e.g. [(0,"intro"),(16,"drop")].
    """
    cc_events: Dict[str, List[Tuple[float, int, int]]] = {}
    spread_map = spread_map or {}

    _MOOD_WIDTH = {Mood.AMBIENT: 5, Mood.INTIMATE: 3,
                   Mood.CHAMBER: 7, Mood.EXPERIMENTAL: 12,
                   Mood.CINEMATIC: 9, Mood.AGGRESSIVE: 11}

    if mood is not None:
        eff_mood = mood
    else:
        lufs = mood_profile.lufs
        if   lufs <= -20:    eff_mood = Mood.AMBIENT
        elif lufs <= -18:    eff_mood = Mood.INTIMATE
        elif lufs <= -16:    eff_mood = Mood.CHAMBER
        elif lufs <= -15:    eff_mood = Mood.EXPERIMENTAL
        elif lufs <= -14:    eff_mood = Mood.CINEMATIC
        else:                 eff_mood = Mood.AGGRESSIVE

    base_spread = _MOOD_WIDTH.get(eff_mood, 9)
    # Tension-aware: low tension narrows, high tension widens
    if tension is not None:
        pad_cc_spread = int(base_spread * (0.5 + 0.5 * tension))
    else:
        pad_cc_spread = base_spread
    fx_cc_spread = 12

    # Find global span for anchors
    all_ends = []
    for tname in profiles:
        notes = tracks.get(tname, [])
        if notes:
            all_ends.append(notes[-1].start + notes[-1].duration)
    global_end = max(all_ends) if all_ends else 0.0

    # Section-aware: precompute section transition beats
    section_map: Dict[float, str] = {}
    if section_breaks:
        for beat, name in section_breaks:
            section_map[round(beat, 2)] = name.lower()

    for tname, prof in profiles.items():
        notes = tracks.get(tname, [])
        if not notes:
            continue

        t_start = notes[0].start
        t_end   = notes[-1].start + notes[-1].duration
        span    = t_end - t_start
        evts: list[tuple[float, int, int]] = []

        # --- CC10 anchors every 4 bars (16 beats at 4/4) ---
        pan_norm = spread_map.get(tname, 0.0)
        anchor_cc10 = max(0, min(127, int(64 + pan_norm * 63)))
        anchor_interval = 16.0  # 4 bars
        beat = t_start
        while beat <= t_end:
            evts.append((round(beat, 6), 10, anchor_cc10))
            beat += anchor_interval

        # --- PAD: tension-aware sine-LFO ---
        if prof.role == Role.PAD and span > 2.0:
            ctr = anchor_cc10
            lo  = max(20, ctr - pad_cc_spread)
            hi  = min(107, ctr + pad_cc_spread)
            period = max(4.0, span / 2)
            lfo = AutomationCurve.sine_lfo(
                cc_num=10, min_val=lo, max_val=hi,
                start_beat=t_start, end_beat=t_end,
                period=period, steps_per_period=8,
            )
            evts.extend(lfo)

        # --- FX: right-to-centre sweep at entry ---
        elif prof.role == Role.FX and prof.entry_beat < t_end:
            entry     = prof.entry_beat
            sweep_dur = min(1.5, t_end - entry)
            sweep_end = entry + sweep_dur
            right     = min(107, 64 + fx_cc_spread)
            sweep = AutomationCurve.linear(
                cc_num=10, start_val=right, end_val=64,
                start_beat=entry, end_beat=sweep_end, steps=6,
            )
            evts.extend(sweep)

        # --- Section-aware pan events ---
        if section_breaks:
            for sec_beat, sec_name in section_breaks:
                if sec_beat < t_start or sec_beat > t_end:
                    continue
                if sec_name == "drop" and prof.role == Role.PAD:
                    # Instant spread: jump to wide pan
                    spread_cc10 = max(0, min(127, int(64 + pan_norm * 63 * 1.5)))
                    evts.append((round(sec_beat, 6), 10, spread_cc10))
                elif sec_name in ("break", "bridge") and prof.role in (Role.PAD, Role.STRINGS):
                    # Collapse to center
                    evts.append((round(sec_beat, 6), 10, 64))
                elif sec_name == "intro":
                    # Slow spread from center over 8 beats
                    spread_end_beat = min(sec_beat + 8.0, t_end)
                    spread_to = anchor_cc10
                    intro_curve = AutomationCurve.linear(
                        cc_num=10, start_val=64, end_val=spread_to,
                        start_beat=sec_beat, end_beat=spread_end_beat, steps=8,
                    )
                    evts.extend(intro_curve)
                elif sec_name == "outro":
                    # Slow collapse to center over 8 beats
                    collapse_end = min(sec_beat + 8.0, t_end)
                    outro_curve = AutomationCurve.linear(
                        cc_num=10, start_val=anchor_cc10, end_val=64,
                        start_beat=sec_beat, end_beat=collapse_end, steps=8,
                    )
                    evts.extend(outro_curve)

        # Sort and deduplicate by (beat, cc) keeping last value
        if evts:
            evts.sort(key=lambda e: (e[0], e[1]))
            cc_events[tname] = evts

    return cc_events


# ---------------------------------------------------------------------------
# [FIX 11] Harmonic tension tracking — detect chaos vs order in chords
# ---------------------------------------------------------------------------

_DISSONANT_INTERVALS = {1, 6}  # minor second, tritone — high tension
_CONSONANT_INTERVALS = {3, 4, 5, 7, 8, 9, 12}  # thirds, fourths, fifths, sixths, octave


def _compute_tension(chords: List) -> float:
    """Analyze chord list and return tension 0.0 (calm) to 1.0 (chaotic)."""
    if not chords:
        return 0.5

    from melodica.theory import Quality as Q

    HIGH_TENSION = {
        Q.TONE_CLUSTER,
        Q.DIMINISHED,
        Q.AUGMENTED,
        Q.FULL_DIM7,
        Q.HALF_DIM7,
        Q.CLUSTER_MINOR_2,
        Q.CLUSTER_MAJOR_2,
        Q.CLUSTER_4TH,
        Q.OCTATONIC_CLUSTER,
    }
    MID_TENSION = {Q.MINOR, Q.HALF_DIM7, Q.LYDIAN_AUG}

    dissonant = 0
    total = 0
    for ch in chords:
        total += 1
        if ch.quality in HIGH_TENSION:
            dissonant += 2
        elif ch.quality in MID_TENSION:
            dissonant += 1

    if total == 0:
        return 0.5
    return min(1.0, dissonant / total)


# ---------------------------------------------------------------------------
# [FIX 12] Sparse normalization safeguard
# ---------------------------------------------------------------------------

_SPARSE_THRESHOLD = 10  # fewer than this many notes = sparse


# ---------------------------------------------------------------------------
# [FIX 5] Polyphony limiter — cap simultaneous voices per track slot
# ---------------------------------------------------------------------------

_POLY_SLOT_RESOLUTION = 4.0  # subdivisions per beat for voice counting (1/16 at 4/4)


def _polyphony_limit(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    max_voices: int = 16,
) -> Dict[str, List[NoteInfo]]:
    """Cap the number of simultaneously sounding notes across all tracks.

    [FIX 5] Builds a timeline of active notes per 1/16-beat slot. When more
    than ``max_voices`` notes are active in a slot, the quietest ones are
    silenced (velocity set to 0 then filtered). Priority order:
    1. Higher velocity → kept
    2. Lead/Strings role → kept over PAD/CHOIR in ties
    """
    import bisect

    # Collect all notes with track context, sorted by start
    all_notes: List[Tuple[float, float, str, NoteInfo]] = []
    for tname, notes in tracks.items():
        if tname.startswith("_") or not notes:
            continue
        for n in notes:
            all_notes.append((n.start, n.start + n.duration, tname, n))
    all_notes.sort(key=lambda x: x[0])

    if not all_notes:
        return tracks

    # Build a set of note IDs to drop
    drop_ids: set = set()
    t_min = all_notes[0][0]
    t_max = max(x[1] for x in all_notes)
    slot_dur = 1.0 / _POLY_SLOT_RESOLUTION

    starts = [x[0] for x in all_notes]

    slot = t_min
    while slot < t_max:
        slot_end = slot + slot_dur
        # Only look at notes that started before slot_end, and potentially extend into this slot.
        # Most notes are shorter than 10 beats.
        lo = bisect.bisect_left(starts, slot - 10.0)
        hi = bisect.bisect_right(starts, slot_end)

        # Active notes whose sounding range overlaps this slot
        active = [
            (tname, n)
            for (ns, ne, tname, n) in all_notes[lo:hi]
            if ns < slot_end and ne > slot and id(n) not in drop_ids
        ]
        if len(active) > max_voices:
            # Sort: keep loudest / highest-priority first
            role_priority = {
                Role.LEAD: 0,
                Role.STRINGS: 1,
                Role.PERC: 2,
                Role.BASS: 3,
                Role.CHOIR: 4,
                Role.PAD: 5,
                Role.FX: 6,
            }
            active.sort(
                key=lambda x: (
                    role_priority.get(
                        profiles.get(x[0], _TrackProfile(60, 0, 0, 0, Role.PAD)).role, 5
                    ),
                    -x[1].velocity,
                ),
            )
            for tname, n in active[max_voices:]:
                drop_ids.add(id(n))
        slot = slot_end

    if not drop_ids:
        return tracks

    result = {}
    for tname, notes in tracks.items():
        result[tname] = [n for n in notes if id(n) not in drop_ids]
    return result


def _sparse_safeguard(
    tracks: Dict[str, List[NoteInfo]], profiles: Dict[str, _TrackProfile]
) -> Dict[str, List[NoteInfo]]:
    """For extremely sparse tracks, clamp velocity to avoid over-amplification."""
    result = {}
    for tname, notes in tracks.items():
        if tname.startswith("_"):
            result[tname] = notes
            continue

        prof = profiles.get(tname)
        if prof and prof.note_count < _SPARSE_THRESHOLD and notes:
            # Clamp max velocity to 90 to prevent RMS normalization explosion
            clamped = []
            for n in notes:
                if n.velocity > 90:
                    clamped.append(
                        NoteInfo(
                            pitch=n.pitch,
                            start=n.start,
                            duration=n.duration,
                            velocity=90,
                            articulation=n.articulation,
                            expression=n.expression,
                        )
                    )
                else:
                    clamped.append(n)
            result[tname] = clamped
        else:
            result[tname] = notes

    return result


# ---------------------------------------------------------------------------
# Auto-mastering with mood-aware settings
# ---------------------------------------------------------------------------


def _auto_master(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    mood_profile: _MoodProfile,
    pan_overrides: Dict[str, float] | None = None,
) -> Tuple[Dict[str, List[NoteInfo]], Dict[str, List[Tuple[float, int, int]]]]:
    """Master with mood-aware LUFS, role-based pan, and brightness ceiling."""
    pan_map = {}
    for name, prof in profiles.items():
        # [FIX 5] Apply dialogue pan overrides if available
        if pan_overrides and name in pan_overrides:
            pan_map[name] = pan_overrides[name]
        else:
            pan_map[name] = _ROLE_PAN.get(prof.role, 0.0)

    master = MasteringDesk(
        target_lufs=mood_profile.lufs,
        track_pan=pan_map,
    )
    mastered, cc_events = master.apply_mastering(tracks)

    # Brightness ceiling: clamp high-register velocity
    if mood_profile.brightness_ceiling < 127:
        for name, notes in mastered.items():
            if name.startswith("_"):
                continue
            for i, n in enumerate(notes):
                if n.pitch >= 84 and n.velocity > mood_profile.brightness_ceiling:
                    notes[i] = NoteInfo(
                        pitch=n.pitch,
                        start=n.start,
                        duration=n.duration,
                        velocity=mood_profile.brightness_ceiling,
                        articulation=n.articulation,
                        expression=n.expression,
                    )

    return mastered, cc_events


# ---------------------------------------------------------------------------
# Dynamics shaping — mood-aware velocity range compression/expansion
# ---------------------------------------------------------------------------

_DYNAMICS_WINDOW_BEATS = 32.0  # sliding window size for local normalization


def _shape_dynamics(
    tracks: Dict[str, List[NoteInfo]], mood_profile: _MoodProfile
) -> Dict[str, List[NoteInfo]]:
    """Widen or compress velocity range based on mood dynamics setting.

    [FIX 4] Uses a sliding window of 32 beats for computing the local velocity
    center instead of the global min/max. This preserves crescendo and decrescendo
    contours which would otherwise be flattened by a single global normalization.

    For short tracks (< 2× window) falls back to the global approach.
    """
    dyn = mood_profile.dynamics_range
    if dyn >= 0.95:
        return tracks

    result = {}
    for name, notes in tracks.items():
        if not notes or name.startswith("_"):
            result[name] = notes
            continue

        vels = [n.velocity for n in notes]
        if max(vels) - min(vels) < 5:
            result[name] = notes
            continue

        # Determine track span
        t_start = notes[0].start
        t_end = notes[-1].start + notes[-1].duration
        span = t_end - t_start

        # [FIX 4] Windowed normalization for long/dense tracks
        if span > _DYNAMICS_WINDOW_BEATS * 2:
            shaped = []
            for n in notes:
                # Gather notes within ±window/2 around this note
                lo = n.start - _DYNAMICS_WINDOW_BEATS / 2
                hi = n.start + _DYNAMICS_WINDOW_BEATS / 2
                local_vels = [x.velocity for x in notes if lo <= x.start <= hi]
                if not local_vels:
                    shaped.append(n)
                    continue
                local_center = (min(local_vels) + max(local_vels)) / 2
                offset = n.velocity - local_center
                new_vel = int(round(local_center + offset * dyn))
                new_vel = max(10, min(127, new_vel))
                shaped.append(
                    NoteInfo(
                        pitch=n.pitch,
                        start=n.start,
                        duration=n.duration,
                        velocity=new_vel,
                        articulation=n.articulation,
                        expression=n.expression,
                    )
                )
            result[name] = shaped
        else:
            # Short track: global approach (original behaviour)
            mn, mx = min(vels), max(vels)
            center = (mn + mx) / 2
            shaped = []
            for n in notes:
                offset = n.velocity - center
                new_vel = int(round(center + offset * dyn))
                new_vel = max(10, min(127, new_vel))
                shaped.append(
                    NoteInfo(
                        pitch=n.pitch,
                        start=n.start,
                        duration=n.duration,
                        velocity=new_vel,
                        articulation=n.articulation,
                        expression=n.expression,
                    )
                )
            result[name] = shaped
    return result


# ---------------------------------------------------------------------------
# Merge CC events from multiple sources
# ---------------------------------------------------------------------------


def _merge_cc_events(
    *sources: Dict[str, List[Tuple[float, int, int]]],
) -> Dict[str, List[Tuple[float, int, int]]]:
    """Merge multiple CC event dicts into one, sorted by time."""
    merged: Dict[str, List[Tuple[float, int, int]]] = {}
    for src in sources:
        for tname, events in src.items():
            if tname not in merged:
                merged[tname] = []
            merged[tname].extend(events)
    # Sort each track's events by time
    for tname in merged:
        merged[tname].sort(key=lambda e: e[0])
    return merged


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Pipeline stages — thin wrappers over existing functions
# ---------------------------------------------------------------------------


def _resolve_rhythm(rhythm):
    """Resolve a rhythm spec (name or generator) into a RhythmGenerator.

    ``str`` is looked up in the rhythm library / dynamic registry; an unknown
    name raises ``ValueError``. Any object exposing a ``generate(duration_beats)``
    method (the :class:`~melodica.rhythm.RhythmGenerator` protocol) is returned
    as-is.
    """
    from melodica.rhythm.library import RHYTHM_LIBRARY, DYNAMIC_RHYTHM_REGISTRY, get_rhythm

    if isinstance(rhythm, str):
        if rhythm not in RHYTHM_LIBRARY and rhythm not in DYNAMIC_RHYTHM_REGISTRY:
            raise ValueError(
                f"Unknown rhythm name {rhythm!r}. Use a name from RHYTHM_LIBRARY/"
                f"DYNAMIC_RHYTHM_REGISTRY or pass a RhythmGenerator instance."
            )
        return get_rhythm(rhythm)
    if callable(getattr(rhythm, "generate", None)):
        return rhythm
    raise ValueError(
        f"rhythm must be a name (str) or RhythmGenerator; got {type(rhythm).__name__}."
    )


def _quantize_onsets(notes, snap_points, entry, max_snap=0.6):
    """Snap each note's onset to the nearest rhythm grid point.

    ``snap_points`` are local-grid onsets in [0, span]; ``entry`` is the track's
    first beat, so the absolute grid is ``p + entry`` for each ``p``. Only onsets
    within ``max_snap`` beats of a grid point are moved (loose notes far from any
    slot keep their timing rather than jumping). Pitch, duration, velocity and
    the number of notes are preserved.
    """
    import bisect

    out = []
    for n in notes:
        # Distance of this note from the local grid origin.
        local = n.start - entry
        # Nearest grid point via binary search.
        idx = bisect.bisect_left(snap_points, local)
        candidates = []
        if idx > 0:
            candidates.append(snap_points[idx - 1])
        if idx < len(snap_points):
            candidates.append(snap_points[idx])
        nearest = min(candidates, key=lambda p: abs(p - local))
        if abs(nearest - local) <= max_snap:
            new_start = round(nearest + entry, 6)
        else:
            new_start = n.start
        out.append(
            NoteInfo(
                pitch=n.pitch,
                start=new_start,
                duration=n.duration,
                velocity=n.velocity,
                articulation=n.articulation,
                expression=dict(n.expression) if n.expression else {},
            )
        )
    return out


def _stage_rhythm(kw):
    """Impose a master rhythm onto the rhythm section only, by quantization.

    Only rhythmic roles (PERC, BASS, LEAD) are snapped onto the shared grid —
    their existing note onsets move to the nearest rhythm slot. Sustained layers
    (PAD / CHOIR / STRINGS / FX / drones) keep their free timing: a pad or choir
    should not pulse like a drum, and forcing them onto the grid flattens the
    arrangement and homogenises every movement.

    This stage *quantizes* rather than *replaces*: it never changes pitch,
    duration, velocity or the number of notes — it only snaps onsets, so the
    generated melodic contour is preserved while the groove locks.
    """
    rhythm = kw.get("rhythm")
    if rhythm is None:
        raise ValueError("rhythm is required for album production.")

    gen = _resolve_rhythm(rhythm)

    # Rhythm-section roles that should lock to the master groove.
    rhythm_roles = {Role.PERC, Role.BASS, Role.LEAD}

    result = {}
    for tname, notes in kw["tracks"].items():
        if tname.startswith("_") or not notes:
            result[tname] = notes
            continue

        role = _detect_role_from_track_name(tname)
        if role not in rhythm_roles:
            # Sustained / textural layer — leave its timing intact.
            result[tname] = notes
            continue

        entry = min(n.start for n in notes)
        end = max(n.start + n.duration for n in notes)
        span = max(0.5, end - entry)

        events = gen.generate(span)
        snap_points = sorted({round(e.onset, 4) for e in events})
        if not snap_points:
            result[tname] = notes
            continue

        result[tname] = _quantize_onsets(notes, snap_points, entry)

    kw["tracks"] = result
    return kw


def _stage_auto_mix(kw):
    mixed, profiles, role_pan_map = _auto_mix(
        kw["tracks"], kw["mood_profile"],
        genre=kw.get("genre"),
    )
    kw["tracks"] = mixed
    kw["_profiles"] = profiles
    kw["_role_pan_map"] = role_pan_map
    return kw


def _stage_pan_spread(kw):
    spread_map = _auto_spread_panning(
        kw["tracks"], kw["_profiles"], kw["_role_pan_map"],
    )
    kw["_pan_spread_map"] = spread_map
    return kw


def _stage_dynamics(kw):
    kw["tracks"] = _shape_dynamics(kw["tracks"], kw["mood_profile"])
    return kw


def _stage_sidechain(kw):
    kw["tracks"] = _sidechain_duck(kw["tracks"], kw["_profiles"])
    return kw


def _stage_humanize(kw):
    kw["tracks"] = _apply_humanization(kw["tracks"], kw["_profiles"])
    return kw


def _stage_phrase_dynamics(kw):
    from melodica.composer.phrase_dynamics import apply_phrase_dynamics_to_pipeline
    kw["tracks"] = apply_phrase_dynamics_to_pipeline(kw["tracks"])
    return kw


def _stage_articulations(kw):
    """Apply ArticulationEngine: articulation string → CC events + duration shaping."""
    from melodica.composer.articulations import ArticulationEngine
    engine = ArticulationEngine()
    total_dur = max(
        (n.start + n.duration)
        for tname, notes in kw["tracks"].items()
        if not tname.startswith("_") and notes
        for n in notes
    ) if any(not k.startswith("_") and v for k, v in kw["tracks"].items()) else 64.0
    result_tracks = {}
    for tname, notes in kw["tracks"].items():
        if tname.startswith("_"):
            result_tracks[tname] = notes
            continue
        if notes:
            result_tracks[tname] = engine.apply(notes, instrument=tname.lower(),
                                                total_beats=total_dur)
        else:
            result_tracks[tname] = notes
    kw["tracks"] = result_tracks
    return kw


def _stage_harmonic_verify(kw):
    """Run harmonic verifier: detect & fix m2/tritone clashes across tracks."""
    from melodica.composer.harmonic_verifier import verify_and_fix, VerifierConfig
    config = VerifierConfig(
        dissonance_tolerance=0.6,
        fix_transpose=True,
        fix_remove=False,
        fix_velocity=True,
        fix_shorten=True,
        apply_shading=True,
    )
    fixed_tracks, report = verify_and_fix(kw["tracks"], config)
    kw["tracks"] = fixed_tracks
    kw["_harmonic_report"] = report
    if kw.get("verbose") and report.clashes_detected > 0:
        print(f"   HarmonicVerifier: {report.clashes_detected} clashes, "
              f"{report.clashes_fixed} fixed")
    return kw


def _stage_transitions(kw):
    """TransitionCoordinator: apply CC11 sweeps at section boundaries."""
    section_breaks = kw.get("section_breaks") or []
    if not section_breaks:
        return kw
    from melodica.composer.transition_coordinator import TransitionCoordinator
    cc_events: dict = dict(kw.get("cc_events") or {})
    for beat, _label in section_breaks:
        sweep_start = max(0.0, beat - 2.0)
        sweep_end = beat + 2.0
        non_bass = [t for t in kw["tracks"] if "bass" not in t.lower()]
        TransitionCoordinator.apply_sweeps(
            kw["tracks"], cc_events, target_tracks=non_bass,
            cc_num=11, start_val=100, end_val=60,
            start_beat=sweep_start, end_beat=beat,
            curve_type="exponential", steps=12,
        )
        TransitionCoordinator.apply_sweeps(
            kw["tracks"], cc_events, target_tracks=non_bass,
            cc_num=11, start_val=60, end_val=100,
            start_beat=beat, end_beat=sweep_end,
            curve_type="exponential", steps=12,
        )
    kw["cc_events"] = cc_events
    return kw


def _stage_texture(kw):
    """TextureController: density automation driven by tension curve."""
    chords = kw.get("chords")
    if not chords:
        return kw
    from melodica.composer.texture_controller import TextureController
    from melodica.composer.tension_curve import TensionCurve
    total_dur = max(
        (n.start + n.duration)
        for tname, notes in kw["tracks"].items()
        if not tname.startswith("_") and notes
        for n in notes
    ) if any(not k.startswith("_") and v for k, v in kw["tracks"].items()) else 64.0
    tc = TensionCurve(
        total_beats=total_dur,
        curve_type="classical",
        peak_position=0.65,
        peak_intensity=0.9,
        resolution_length=0.25,
    )
    ctrl = TextureController(tension_curve=tc)
    kw["tracks"] = ctrl.apply_texture(kw["tracks"], total_dur)
    return kw


def _stage_non_chord_tones(kw):
    """NonChordTones: add passing/neighbour tones to LEAD tracks."""
    chords = kw.get("chords")
    key = kw.get("key")
    if not chords or not key:
        return kw
    from melodica.composer.non_chord_tones import NonChordToneGenerator
    gen = NonChordToneGenerator(
        passing_prob=0.18,
        neighbor_prob=0.08,
        suspension_prob=0.06,
        anticipation_prob=0.04,
    )
    result = {}
    for tname, notes in kw["tracks"].items():
        prof = kw.get("_profiles", {}).get(tname)
        # Only apply to LEAD and STRINGS — not bass/perc/pad
        if prof and prof.role in (Role.LEAD, Role.STRINGS) and notes:
            result[tname] = gen.add_non_chord_tones(notes, chords, key)
        else:
            result[tname] = notes
    kw["tracks"] = result
    return kw


def _stage_diagnostics(kw):
    """Post-export diagnostics report."""
    if not kw.get("verbose"):
        return kw
    try:
        from melodica.composer.diagnostics import diagnose_tracks
        diagnose_tracks(kw["tracks"], bpm=kw.get("bpm", 120.0))
    except Exception:
        pass  # diagnostics are informational — never block the pipeline
    return kw


def _stage_sections(kw):
    sections = kw.get("sections")
    tracks = kw.get("tracks")
    cc_events = kw.get("cc_events", {})

    if sections and tracks:
        # 1. Apply note-level profiles (velocity, register, density, humanization, active layers)
        kw["tracks"] = _apply_section_moods(tracks, sections, kw["_profiles"])

        # 2. Apply section-level CC automation (Reverb & Filter Cutoff)
        total_beats = 0.0
        for tname, notes in kw["tracks"].items():
            if tname.startswith("_") or not notes:
                continue
            end = max(n.start + n.duration for n in notes)
            if end > total_beats:
                total_beats = end

        # Generate CC automation for every track
        for tname in list(kw["tracks"].keys()):
            if tname.startswith("_"):
                continue
            if tname not in cc_events:
                cc_events[tname] = []

            # Clean existing reverb (CC 91) and filter (CC 74) events
            cc_events[tname] = [evt for evt in cc_events[tname] if evt[1] not in (74, 91)]

            for idx, (sec_start, sec_key) in enumerate(sections):
                profile = None
                if isinstance(sec_key, str):
                    profile = SECTION_PROFILES.get(sec_key)
                elif isinstance(sec_key, Mood):
                    for name, p in SECTION_PROFILES.items():
                        if p.mood == sec_key:
                            profile = p
                            break
                if profile is None:
                    profile = SECTION_PROFILES["Theme"]

                cc_events[tname].append((sec_start, 91, profile.reverb_amount))
                cc_events[tname].append((sec_start, 74, profile.filter_cutoff))

                if idx < len(sections) - 1:
                    next_start = sections[idx + 1][0]
                    transition_time = max(sec_start, next_start - 1.0)
                    cc_events[tname].append((transition_time, 91, profile.reverb_amount))
                    cc_events[tname].append((transition_time, 74, profile.filter_cutoff))
                else:
                    cc_events[tname].append((total_beats, 91, profile.reverb_amount))
                    cc_events[tname].append((total_beats, 74, profile.filter_cutoff))

            cc_events[tname].sort(key=lambda x: x[0])

        kw["cc_events"] = cc_events

    return kw


def _stage_tension(kw):
    chords = kw.get("chords")
    if chords:
        tension = _compute_tension(chords)
        kw["_tension"] = tension
        if tension > 0.7:
            kw["tracks"] = _tension_boost(kw["tracks"], 1.10)
        elif tension < 0.3:
            kw["tracks"] = _tension_boost(kw["tracks"], 0.92)
    return kw


def _stage_polyphony(kw):
    kw["tracks"] = _polyphony_limit(kw["tracks"], kw["_profiles"], max_voices=16)
    return kw


def _stage_psycho(kw):
    if kw.get("psycho_verify_enabled", True):
        config = PsychoConfig(aggressive_fix=kw["mood_profile"].psycho_aggressive)
        kw["tracks"], psycho_report = psycho_verify(kw["tracks"], config, bpm=kw["bpm"])
        kw["_psycho_report"] = psycho_report

        from melodica.composer.orchestrator import analyze_orchestration
        alerts = analyze_orchestration(kw["instruments"], tracks=kw["tracks"], chords=kw.get("chords"))

        if kw.get("verbose"):
            if psycho_report.issues_detected > 0:
                print(f"   Psycho: {psycho_report.issues_detected} issues, "
                      f"{psycho_report.issues_fixed} fixed "
                      f"({psycho_report.notes_velocity_reduced} vel-, "
                      f"{psycho_report.notes_removed} removed, "
                      f"{psycho_report.notes_transposed} transposed)")
            if alerts:
                print("   Orchestration Alerts:")
                for alert in alerts:
                    print(f"     {alert}")
    else:
        kw["_psycho_report"] = None
    return kw


def _stage_sparse_safeguard(kw):
    kw["tracks"] = _sparse_safeguard(kw["tracks"], kw["_profiles"])
    return kw


def _stage_master(kw):
    spread_map = kw.get("_pan_spread_map", {})
    master = MasteringDesk(
        target_lufs=kw["mood_profile"].lufs,
        track_pan=spread_map,
    )
    mastered, master_cc = master.apply_mastering(kw["tracks"])
    total_dur = max(
        (n.start + n.duration for name, ns in mastered.items() if not name.startswith("_") for n in ns), default=0.0
    )
    entry_cc = _generate_entry_fades(mastered, kw["_profiles"], total_dur)
    reverb_cc = _generate_reverb_sends(mastered, kw["_profiles"], kw["mood_profile"])
    delay_cc = _generate_delay_sends(mastered, kw["_profiles"])
    pan_auto_cc = _generate_pan_automation(
        mastered, kw["_profiles"], kw["mood_profile"],
        mood=kw.get("mood"),
        spread_map=spread_map,
        tension=kw.get("_tension"),
        section_breaks=kw.get("section_breaks"),
    )
    all_cc = _merge_cc_events(
        master_cc, entry_cc, reverb_cc, delay_cc, pan_auto_cc, kw.get("cc_events", {})
    )

    # Pan validation
    validator = PanValidator()
    pan_warnings = validator.validate(spread_map, kw["_profiles"])
    if pan_warnings and kw.get("verbose"):
        for w in pan_warnings:
            print(f"   Pan warning: {w}")

    kw["_mastered"] = mastered
    kw["_all_cc"] = all_cc
    return kw


def _stage_export(kw):
    export_multitrack_midi(
        kw["_mastered"],
        str(kw["path"]),
        bpm=kw["bpm"],
        key=kw.get("key"),
        time_sig=kw.get("time_signature", (4, 4)),
        instruments=kw["instruments"],
        cc_events=kw["_all_cc"],
        tempo_events=kw.get("tempo_events"),
        diagnose=kw.get("verbose", True),
        strict_validation=kw.get("strict_validation", False),
    )
    return kw


def _stage_report(kw):
    profiles = kw["_profiles"]
    psycho_report = kw.get("_psycho_report")
    mood = kw["mood"]
    mood_profile = kw["mood_profile"]
    all_cc = kw.get("_all_cc", {})

    report = {
        "profiles": {
            name: {
                "role": p.role.value,
                "avg_pitch": round(p.avg_pitch, 1),
                "density": round(p.density, 3),
                "rms": round(p.rms_velocity, 1),
                "entry": round(p.entry_beat, 1),
            }
            for name, p in profiles.items()
        },
        "psycho": psycho_report,
        "mood": mood.value,
        "lufs": mood_profile.lufs,
        "cc_events": {k: len(v) for k, v in all_cc.items()},
    }

    # Verbose output
    if kw.get("verbose"):
        roles = {name: p.role.value for name, p in profiles.items()}
        pan_map = kw.get("_pan_spread_map", {})
        print(f"   Roles: {roles} | LUFS: {mood_profile.lufs}")
        _print_pan_map(profiles, pan_map, mood_profile)

    # Pan map in report
    spread_map = kw.get("_pan_spread_map", {})
    report["pan_map"] = {
        name: {
            "role":  profiles[name].role.value,
            "pan":   round(spread_map.get(name, 0.0), 3),
        }
        for name in profiles
    }
    # Stereo width: avg absolute pan for all non-centre tracks
    non_centre_pans = [abs(v) for v in spread_map.values()
                       if abs(v) > 0.05]
    if non_centre_pans:
        report["stereo_width"] = round(sum(non_centre_pans) / len(non_centre_pans), 3)
    else:
        report["stereo_width"] = 0.0

    kw["_report"] = report
    return kw


DEFAULT_PIPELINE: list[Stage] = [
    Stage("rhythm", _stage_rhythm),
    Stage("auto_mix", _stage_auto_mix),
    Stage("pan_spread", _stage_pan_spread),
    Stage("dynamics", _stage_dynamics),
    Stage("sidechain", _stage_sidechain),
    Stage("humanize", _stage_humanize),
    Stage("phrase_dynamics", _stage_phrase_dynamics),
    Stage("articulations", _stage_articulations),
    # harmonic_verify must run BEFORE non_chord_tones: the verifier removes
    # clashes from the base harmony, then ornamentation (passing/neighbor/
    # suspension tones) is added on top. The old order (non_chord_tones then
    # harmonic_verify) caused the verifier to delete exactly the ornamentation
    # it had just inserted.
    Stage("harmonic_verify", _stage_harmonic_verify),
    Stage("non_chord_tones", _stage_non_chord_tones),
    Stage("sections", _stage_sections),
    Stage("tension", _stage_tension),
    Stage("texture", _stage_texture),
    Stage("transitions", _stage_transitions),
    Stage("polyphony", _stage_polyphony),
    Stage("psycho", _stage_psycho),
    Stage("sparse_safeguard", _stage_sparse_safeguard),
    Stage("master", _stage_master),
    Stage("export", _stage_export),
    Stage("report", _stage_report),
    Stage("diagnostics", _stage_diagnostics),
]


def detect_sections_intelligently(
    tracks: Dict[str, List[NoteInfo]],
    bpm: float,
    time_signature: tuple[int, int] = (4, 4),
) -> List[Tuple[float, str]]:
    """
    Intelligently analyzes note densities, velocities, and active track counts
    across the timeline to reconstruct the song's structural sections.
    """
    import math
    total_beats = 0.0
    for notes in tracks.values():
        if notes:
            end = max(n.start + n.duration for n in notes)
            if end > total_beats:
                total_beats = end

    if total_beats <= 0.0:
        return [(0.0, "Theme")]

    beats_per_bar = time_signature[0]
    chunk_size = 4.0 * beats_per_bar  # 4 bars chunk size (usually 16 beats)
    if total_beats < chunk_size * 2:
        chunk_size = 1.0 * beats_per_bar

    num_chunks = int(math.ceil(total_beats / chunk_size))
    if num_chunks == 0:
        return [(0.0, "Theme")]

    chunk_metrics = []
    for chunk_idx in range(num_chunks):
        c_start = chunk_idx * chunk_size
        c_end = min(total_beats, c_start + chunk_size)

        chunk_notes = []
        active_tracks = set()
        total_vel = 0.0
        for tname, notes in tracks.items():
            if tname.startswith("_") or not isinstance(notes, list):
                continue
            for n in notes:
                if c_start <= n.start < c_end:
                    chunk_notes.append(n)
                    active_tracks.add(tname)
                    total_vel += n.velocity

        note_count = len(chunk_notes)
        avg_vel = total_vel / note_count if note_count > 0 else 0.0
        track_density = len(active_tracks)
        energy = track_density * avg_vel

        chunk_metrics.append({
            "idx": chunk_idx,
            "start": c_start,
            "note_count": note_count,
            "track_density": track_density,
            "avg_velocity": avg_vel,
            "energy": energy
        })

    max_energy = max(c["energy"] for c in chunk_metrics) if chunk_metrics else 0.0
    peak_idx = -1
    if max_energy > 0:
        for c in chunk_metrics:
            if c["energy"] == max_energy:
                peak_idx = c["idx"]
                break

    detected_sections = []
    for idx, c in enumerate(chunk_metrics):
        ratio = c["start"] / total_beats
        label = "Theme"

        if idx == 0:
            if c["track_density"] <= 2 or c["avg_velocity"] < 60:
                label = "Intro"
        elif idx == num_chunks - 1:
            if c["track_density"] <= 2 or c["avg_velocity"] < 60:
                label = "Fade"
        elif idx == peak_idx:
            label = "Climax"
        elif idx > 0 and chunk_metrics[idx - 1]["energy"] > 0 and c["energy"] == 0:
            label = "Breakdown"
        elif idx > 0 and c["energy"] < chunk_metrics[idx - 1]["energy"] * 0.4:
            label = "Breakdown"
        elif idx > 0 and chunk_metrics[idx - 1]["energy"] > 0 and c["energy"] > chunk_metrics[idx - 1]["energy"] * 1.5:
            label = "Climax" if idx >= num_chunks * 0.5 else "Variation"
        else:
            if idx > 0 and detected_sections[-1][1] == "Theme":
                label = "Variation"
            else:
                label = "Theme"

        detected_sections.append((c["start"], label))

    collapsed_sections = []
    for start, label in detected_sections:
        if not collapsed_sections or collapsed_sections[-1][1] != label:
            collapsed_sections.append((start, label))

    return collapsed_sections


# Public API
# ---------------------------------------------------------------------------


def produce_track(
    tracks: Dict[str, List[NoteInfo]],
    bpm: float,
    instruments: Dict[str, int],
    path: str | Path,
    mood: Mood = Mood.CINEMATIC,
    key: Scale | None = None,
    psycho_verify_enabled: bool = True,
    verbose: bool = True,
    genre: str = DEFAULT_GENRE,
    sections: List[Tuple[float, Mood | str]] | None = None,
    chords: List | None = None,
    cc_events: Dict[str, List[Tuple[float, int, int]]] | None = None,
    tempo_events: List[Tuple[float, float]] | None = None,
    pipeline: list | None = None,
    engine: str = "hmm",
    style: str = "academic",
    section_breaks: List[Tuple[float, str]] | None = None,
    return_state: bool = False,
    strict_validation: bool = False,
    rhythm: str | object | None = None,
    time_signature: tuple[int, int] | None = None,
) -> dict:
    """
    Full production pipeline: analyze → mix → dynamics → psycho → master → export.

    Parameters
    ----------
    tracks : dict[str, list[NoteInfo]]
        Raw generated tracks {track_name: [notes]}.
    bpm : float
        Tempo in beats per minute.
    instruments : dict[str, int]
        GM program numbers {track_name: program}.
    path : str or Path
        Output .mid file path.
    mood : Mood
        Mood preset — controls LUFS, dynamics, psychoacoustic strictness.
    key : Scale, optional
        Key signature for MIDI metadata.
    psycho_verify_enabled : bool
        Run psychoacoustic masking detection and fixes.
    verbose : bool
        Print processing report.
    genre : str, optional
        Genre tag that selects the pan profile: "techno", "rnb", or "trap".
        Defaults to "techno" if not specified.
    sections : list of (beat, Mood), optional
        [FIX 3] Section-aware mood changes. Each tuple is (start_beat, mood).
    chords : list of ChordLabel, optional
        [FIX 11] Chord progression for harmonic tension analysis.
    pipeline : list of Stage, optional
        Custom pipeline stages. If None, uses DEFAULT_PIPELINE.
    engine : str
        Harmonization engine to use (default "hmm").
    style : str
        Engine-specific style (default "academic").

    Returns
    -------
    dict with keys: profiles, report
    """
    if rhythm is None:
        raise ValueError(
            "rhythm is required for produce_track. Pass a rhythm name (str from "
            "RHYTHM_LIBRARY/DYNAMIC_RHYTHM_REGISTRY) or a RhythmGenerator instance."
        )
    if key is None:
        raise ValueError(
            "key is required for produce_track. Pass a Scale instance."
        )
    if chords is None:
        raise ValueError(
            "chords is required for produce_track. Pass a chord progression "
            "(list[ChordLabel]); without it the harmonic stages (texture, "
            "non_chord_tones, tension) are silently skipped."
        )
    if genre not in _ROLE_PAN_PROFILES:
        raise ValueError(
            f"Unknown genre {genre!r}; must be one of {sorted(_ROLE_PAN_PROFILES)}."
        )
    if time_signature is None:
        raise ValueError("time_signature is required for produce_track, e.g. (4, 4).")
    if (
        not isinstance(time_signature, (tuple, list))
        or len(time_signature) != 2
        or not isinstance(time_signature[0], int)
        or not isinstance(time_signature[1], int)
        or time_signature[0] <= 0
        or time_signature[1] not in (1, 2, 4, 8, 16)
    ):
        raise ValueError(
            f"time_signature must be (numerator>0, denominator in {{1,2,4,8,16}}); "
            f"got {time_signature!r}."
        )

    if not sections:
        sections = detect_sections_intelligently(tracks, bpm, time_signature)
        if verbose:
            print(f"   [AI Section Analyzer] Auto-detected arrangement: {', '.join(f'{lbl} (@{start}b)' for start, lbl in sections)}")

    # Validate section ordering
    last_beat = -1.0
    for idx, sec in enumerate(sections):
        if not isinstance(sec, (list, tuple)) or len(sec) < 2:
            raise ValueError(
                f"Section at index {idx} must be a tuple/list of (start_beat, mood)."
            )
        beat, sec_mood = sec
        if beat < last_beat:
            raise ValueError(
                f"Sections are not in chronological order: section at index {idx} starts at beat {beat}, which is less than preceding beat {last_beat}."
            )
        last_beat = beat

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mood_profile = _MOOD_PROFILES[mood]

    # Build pipeline
    stages = pipeline if pipeline is not None else DEFAULT_PIPELINE

    # Common kwargs passed to every stage
    kw = dict(
        tracks=tracks,
        bpm=bpm,
        instruments=instruments,
        path=path,
        mood=mood,
        mood_profile=mood_profile,
        key=key,
        verbose=verbose,
        psycho_verify_enabled=psycho_verify_enabled,
        genre=genre,
        sections=sections,
        chords=chords,
        cc_events=cc_events or {},
        tempo_events=tempo_events,
        engine=engine,
        style=style,
        section_breaks=section_breaks,
        strict_validation=strict_validation,
        rhythm=rhythm,
        time_signature=time_signature,
    )

    # Run stages sequentially
    for stage in stages:
        if not stage.enabled:
            continue
        kw = stage.fn(kw)

    if return_state:
        return {
            "tracks": kw["tracks"],
            "bpm": kw["bpm"],
            "instruments": kw["instruments"],
            "cc_events": kw.get("_all_cc", {}),
            "tempo_events": kw.get("tempo_events", []),
            "key": kw.get("key"),
            "genre": kw.get("genre"),
            "time_signature": kw.get("time_signature"),
            "sections": kw.get("sections", []),
            "_report": kw.get("_report", {})
        }
    return kw.get("_report", {})


# ---------------------------------------------------------------------------
# [FIX 3] Section-aware mood changes
# ---------------------------------------------------------------------------


@dataclass
class SectionProfile:
    mood: Mood
    dynamics_range: float
    brightness_ceiling: int
    energy_target: float       # relative loudness scale (1.0 = normal)
    note_density: float        # 1.0 = keep all notes, < 1.0 = thin out notes
    timing_drift: float        # timing humanization scaling factor
    velocity_drift: float      # random velocity offset range
    reverb_amount: int         # CC 91 value (0-127)
    filter_cutoff: int         # CC 74 value (0-127)
    active_roles: list[Role] | None = None  # If specified, only tracks with these roles play
    entropy: float = 0.0       # dynamic entropy level (0.0 = low/stable, 1.0 = high/unstable)


SECTION_PROFILES = {
    "Intro": SectionProfile(
        mood=Mood.AMBIENT,
        dynamics_range=0.8,
        brightness_ceiling=95,
        energy_target=0.5,
        note_density=0.5,
        timing_drift=0.0,
        velocity_drift=8,
        reverb_amount=85,
        filter_cutoff=70,
        active_roles=[Role.PAD],
    ),
    "Theme": SectionProfile(
        mood=Mood.INTIMATE,
        dynamics_range=0.7,
        brightness_ceiling=112,
        energy_target=0.7,
        note_density=0.8,
        timing_drift=0.0,
        velocity_drift=4,
        reverb_amount=45,
        filter_cutoff=100,
        active_roles=[Role.PAD, Role.BASS],
    ),
    "Variation": SectionProfile(
        mood=Mood.EXPERIMENTAL,
        dynamics_range=0.9,
        brightness_ceiling=120,
        energy_target=0.85,
        note_density=0.9,
        timing_drift=0.0,
        velocity_drift=6,
        reverb_amount=50,
        filter_cutoff=110,
        active_roles=[Role.PAD, Role.BASS, Role.LEAD],
    ),
    "Breakdown": SectionProfile(
        mood=Mood.AMBIENT,
        dynamics_range=0.8,
        brightness_ceiling=100,
        energy_target=0.4,
        note_density=0.4,
        timing_drift=0.0,
        velocity_drift=10,
        reverb_amount=95,
        filter_cutoff=60,
        active_roles=[Role.PAD, Role.LEAD],
    ),
    "Climax": SectionProfile(
        mood=Mood.CINEMATIC,
        dynamics_range=0.5,
        brightness_ceiling=127,
        energy_target=1.1,
        note_density=1.0,
        timing_drift=0.0,
        velocity_drift=2,
        reverb_amount=25,
        filter_cutoff=127,
        active_roles=[Role.PAD, Role.BASS, Role.LEAD, Role.PERC],
    ),
    "Fade": SectionProfile(
        mood=Mood.AMBIENT,
        dynamics_range=0.8,
        brightness_ceiling=90,
        energy_target=0.3,
        note_density=0.3,
        timing_drift=0.0,
        velocity_drift=10,
        reverb_amount=70,
        filter_cutoff=65,
        active_roles=[Role.PAD],
    ),
    "Emergence": SectionProfile(
        mood=Mood.AMBIENT,
        dynamics_range=0.8,
        brightness_ceiling=90,
        energy_target=0.4,
        note_density=0.4,
        timing_drift=0.0,
        velocity_drift=8,
        reverb_amount=95,
        filter_cutoff=55,
        active_roles=[Role.PAD],
        entropy=0.1,
    ),
    "Expansion": SectionProfile(
        mood=Mood.INTIMATE,
        dynamics_range=0.7,
        brightness_ceiling=105,
        energy_target=0.65,
        note_density=0.7,
        timing_drift=0.0,
        velocity_drift=5,
        reverb_amount=60,
        filter_cutoff=85,
        active_roles=[Role.PAD, Role.BASS],
        entropy=0.2,
    ),
    "Tension": SectionProfile(
        mood=Mood.EXPERIMENTAL,
        dynamics_range=0.9,
        brightness_ceiling=118,
        energy_target=0.85,
        note_density=0.9,
        timing_drift=0.0,
        velocity_drift=7,
        reverb_amount=50,
        filter_cutoff=110,
        active_roles=[Role.PAD, Role.BASS, Role.LEAD],
        entropy=0.6,
    ),
    "Release": SectionProfile(
        mood=Mood.CINEMATIC,
        dynamics_range=0.5,
        brightness_ceiling=127,
        energy_target=1.15,
        note_density=1.0,
        timing_drift=0.0,
        velocity_drift=3,
        reverb_amount=30,
        filter_cutoff=127,
        active_roles=[Role.PAD, Role.BASS, Role.LEAD, Role.PERC],
        entropy=0.3,
    ),
    "Dissolve": SectionProfile(
        mood=Mood.AMBIENT,
        dynamics_range=0.8,
        brightness_ceiling=85,
        energy_target=0.35,
        note_density=0.3,
        timing_drift=0.0,
        velocity_drift=12,
        reverb_amount=80,
        filter_cutoff=60,
        active_roles=[Role.PAD],
        entropy=0.8,
    ),
}


def _detect_role_from_track_name(tname: str) -> Role:
    name_lower = tname.lower()
    if "bass" in name_lower:
        return Role.BASS
    if any(k in name_lower for k in ("drum", "kick", "snare", "perc", "hihat", "shaker")):
        return Role.PERC
    if any(k in name_lower for k in ("lead", "melody", "solo", "vocal", "strings", "viol", "arpeggio")):
        return Role.LEAD
    return Role.PAD


def _apply_section_moods(
    tracks: Dict[str, List[NoteInfo]],
    sections: List[Tuple[float, Mood | str]],
    profiles: Dict[str, _TrackProfile],
) -> Dict[str, List[NoteInfo]]:
    """Apply rich per-section dynamics and velocity-based shaping based on SectionProfile."""
    if not sections:
        return tracks

    import random
    rng = random.Random(42)

    result = {}
    for tname, notes in tracks.items():
        if tname.startswith("_") or not notes:
            result[tname] = notes
            continue

        role = _detect_role_from_track_name(tname)
        new_notes = []

        for n in notes:
            # Find which section this note belongs to
            section_key = sections[0][1]
            for sec_start, sec_mood_or_str in sections:
                if n.start >= sec_start:
                    section_key = sec_mood_or_str

            # Retrieve the profile (or map Mood to key)
            profile = None
            if isinstance(section_key, str):
                profile = SECTION_PROFILES.get(section_key)
            elif isinstance(section_key, Mood):
                # Fallback mapping from Mood back to section key
                for name, p in SECTION_PROFILES.items():
                    if p.mood == section_key:
                        profile = p
                        break

            if profile is None:
                profile = SECTION_PROFILES["Theme"]

            # 1. Layer Activation (Role-based active layers)
            if profile.active_roles is not None:
                has_any_match = False
                for other_tname in tracks.keys():
                    other_role = _detect_role_from_track_name(other_tname)
                    if other_role in profile.active_roles:
                        has_any_match = True
                        break
                if has_any_match and role not in profile.active_roles:
                    continue

            # 3. Micro-dynamics (velocity compression)
            center = 64
            offset = n.velocity - center
            vel = int(round(center + offset * profile.dynamics_range))

            # 4. Energy Target / Relative Loudness
            vel = int(vel * profile.energy_target)

            # 5. Velocity Drift (Humanization)
            if profile.velocity_drift > 0:
                vel_offset = int(rng.uniform(-profile.velocity_drift, profile.velocity_drift))
                vel += vel_offset

            # 2. Musical Note Thinning (Velocity-based dynamic damping instead of deletion!)
            if profile.note_density < 1.0:
                beat_in_bar = n.start % 4.0
                if role == Role.PERC:
                    if profile.note_density <= 0.4:
                        if abs(beat_in_bar - 0.0) > 0.05 and abs(beat_in_bar - 2.0) > 0.05:
                            vel = int(vel * 0.2)
                    elif profile.note_density <= 0.7:
                        if abs(beat_in_bar * 2 - round(beat_in_bar * 2)) > 0.05:
                            vel = int(vel * 0.4)
                elif role in (Role.LEAD, Role.PAD):
                    if profile.note_density <= 0.5:
                        if abs(beat_in_bar - round(beat_in_bar)) > 0.05:
                            vel = int(vel * 0.4)
                elif role == Role.BASS:
                    if profile.note_density <= 0.5:
                        if abs(beat_in_bar - 0.0) > 0.05 and abs(beat_in_bar - 2.0) > 0.05:
                            vel = int(vel * 0.3)

            # 6. Dynamic Entropy (Micro-variations, velocity/duration deviations based on section entropy)
            duration = n.duration
            n_start = n.start
            if hasattr(profile, "entropy") and profile.entropy > 0.0:
                entropy = profile.entropy
                seed = int(float(n.start) * 100) + int(n.pitch)
                note_rng = random.Random(seed)

                # Randomize velocity offset
                vel_change = int(note_rng.uniform(-20 * entropy, 20 * entropy))
                vel = max(10, min(127, vel + vel_change))

                # Randomize duration offset slightly (e.g. +/- 15% of duration * entropy)
                dur_change = note_rng.uniform(-0.15 * n.duration * entropy, 0.15 * n.duration * entropy)
                duration = max(0.05, n.duration + dur_change)

                # Randomize start time micro-jitter (entropy-driven)
                start_change = note_rng.uniform(-0.04 * entropy, 0.04 * entropy)
                n_start = max(0.0, n.start + start_change)

            # Clamp velocity within brightness ceiling and MIDI range
            vel = max(10, min(profile.brightness_ceiling, vel))

            new_notes.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n_start,
                    duration=duration,
                    velocity=vel,
                    articulation=n.articulation,
                    expression=n.expression,
                )
            )

        new_notes.sort(key=lambda x: x.start)
        result[tname] = new_notes

    return result


def _tension_boost(tracks: Dict[str, List[NoteInfo]], factor: float) -> Dict[str, List[NoteInfo]]:
    """Apply velocity scaling based on harmonic tension."""
    result = {}
    for tname, notes in tracks.items():
        if tname.startswith("_") or not notes:
            result[tname] = notes
            continue
        new_notes = []
        for n in notes:
            new_vel = max(10, min(127, int(n.velocity * factor)))
            new_notes.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=new_vel,
                    articulation=n.articulation,
                    expression=n.expression,
                )
            )
        result[tname] = new_notes
    return result


def produce_album(
    tracks_list: List[Tuple[Dict[str, List[NoteInfo]], float, Dict[str, int], str, Mood]],
    key: Scale | None = None,
    album_name: str = "Album",
    output_dir: str = "output/album",
    rhythm: str | object | None = None,
    chords: List | None = None,
    genre: str = DEFAULT_GENRE,
    time_signature: tuple[int, int] | None = None,
) -> List[dict]:
    """
    Produce multiple tracks as an album.

    Parameters
    ----------
    tracks_list : list of (tracks, bpm, instruments, filename, mood) tuples
    key : Scale, optional
    album_name : str
    output_dir : str

    Returns
    -------
    list of per-track report dicts
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if rhythm is None:
        raise ValueError(
            "rhythm is required for produce_album. Pass a rhythm name (str) or "
            "RhythmGenerator instance."
        )
    if key is None:
        raise ValueError("key is required for produce_album. Pass a Scale instance.")
    if chords is None:
        raise ValueError(
            "chords is required for produce_album. Pass a chord progression (list[ChordLabel])."
        )
    if time_signature is None:
        raise ValueError("time_signature is required for produce_album, e.g. (4, 4).")

    print("=" * 60)
    print(f"   {album_name}")
    print("=" * 60)

    reports = []
    for i, (tracks, bpm, instruments, filename, mood) in enumerate(tracks_list, 1):
        print(f"\n--- {i:02d}. {filename} ({mood.value}) ---")
        report = produce_track(
            tracks=tracks,
            bpm=bpm,
            instruments=instruments,
            path=out / filename,
            mood=mood,
            key=key,
            rhythm=rhythm,
            chords=chords,
            genre=genre,
            time_signature=time_signature,
        )
        reports.append(report)

    print("\n" + "=" * 60)
    print(f"   {album_name} — COMPLETE.")
    print(f"   Files in: {out}")
    print("=" * 60)
    return reports


def compile_continuous_album(
    tracks_metadata: List[Dict],
    output_path: str | Path,
    overlap_beats: float = 8.0,
    mood: Mood = Mood.CINEMATIC,
    modulation_strategy: str | None = None,
    transition_instrument: int = 89,
    rhythm: str | object | None = None,
    chords: List | None = None,
    genre: str = DEFAULT_GENRE,
    time_signature: tuple[int, int] | None = None,
) -> dict:
    """
    Stitches multiple tracks into a single continuous arrangement with crossfades
    and optional diatonic modulation bridges at key transitions.

    Each metadata dict should have:
      - "tracks": dict[str, list[NoteInfo]]
      - "bpm": float
      - "instruments": dict[str, int]
      - "cc_events": dict[str, list[tuple[float, int, int]]], optional
      - "tempo_events": list[tuple[float, float]], optional
      - "key": Scale, optional

    Parameters
    ----------
    tracks_metadata : list[dict]
        One dict per track in album order.
    output_path : str or Path
        Destination .mid file.
    overlap_beats : float
        How many beats of overlap/crossfade to use between tracks (default 8).
    mood : Mood
        Mixing and mastering preset applied to the compiled result.
    modulation_strategy : str or None
        If set ("pivot", "dominant", or "chromatic") and adjacent tracks have
        different keys, a diatonic modulation bridge is automatically generated
        and inserted as a ``_transition_pad`` track in the overlap zone.
    transition_instrument : int
        GM program number for the auto-generated modulation bridge track
        (default 89 — Pad 2 Warm).
    """
    import copy
    from melodica.composer.automation import AutomationCurve
    from melodica.theory.modulation import ModulationEngine

    if not tracks_metadata:
        raise ValueError("tracks_metadata cannot be empty.")

    if rhythm is None:
        raise ValueError(
            "rhythm is required for compile_continuous_album. Pass a rhythm name "
            "(str) or RhythmGenerator instance."
        )
    if chords is None:
        raise ValueError(
            "chords is required for compile_continuous_album. Pass a chord progression (list[ChordLabel])."
        )
    if time_signature is None:
        raise ValueError("time_signature is required for compile_continuous_album, e.g. (4, 4).")

    # Mandatory sectioning check (with AI auto-detection fallback)
    for idx, meta in enumerate(tracks_metadata):
        if "sections" not in meta or not meta["sections"]:
            meta["sections"] = detect_sections_intelligently(
                meta.get("tracks", {}), meta.get("bpm", 120.0), time_signature
            )
        sections = meta["sections"]
        last_beat = -1.0
        for sec_idx, section in enumerate(sections):
            if not isinstance(section, (tuple, list)) or len(section) < 2:
                raise ValueError(
                    f"Track {idx} section {sec_idx} must be a tuple/list of (start_beat, mood_or_str)."
                )
            beat, sec_mood = section
            if beat < last_beat:
                raise ValueError(
                    f"Track {idx} sections are not in chronological order: "
                    f"section at index {sec_idx} starts at beat {beat}, which is less than preceding beat {last_beat}."
                )
            last_beat = beat

    combined_tracks: Dict[str, List[NoteInfo]] = {}
    combined_instruments: Dict[str, int] = {}
    combined_cc_events: Dict[str, List[Tuple[float, int, int]]] = {}
    combined_tempo_events: List[Tuple[float, float]] = []
    combined_sections: List[Tuple[float, Mood]] = []

    current_start_beat = 0.0
    first_bpm = tracks_metadata[0].get("bpm", 120.0) if tracks_metadata else 120.0
    first_key = tracks_metadata[0].get("key", None) if tracks_metadata else None

    for i, meta in enumerate(tracks_metadata):
        track_dict = {k: v for k, v in meta.get("tracks", {}).items() if not k.startswith("_")}
        bpm = meta.get("bpm", 120.0)
        inst_dict = meta.get("instruments", {})
        cc_events = meta.get("cc_events", {})
        tempo_events = meta.get("tempo_events", [])
        this_key = meta.get("key", None)
        sections = meta.get("sections", [])

        # Accumulate and shift sections
        for beat, sec_mood in sections:
            combined_sections.append((beat + current_start_beat, sec_mood))

        # Calculate track duration in beats
        track_dur = 0.0
        for name, notes in track_dict.items():
            if notes:
                end_beat = max(n.start + n.duration for n in notes)
                if end_beat > track_dur:
                    track_dur = end_beat

        # Copy and shift notes
        for name, notes in track_dict.items():
            notes_copy = copy.deepcopy(notes)
            for note in notes_copy:
                note.shift_time(current_start_beat)
            if name not in combined_tracks:
                combined_tracks[name] = []
            combined_tracks[name].extend(notes_copy)

        # Merge instruments
        combined_instruments.update(inst_dict)

        # Merge and shift CC events
        if cc_events:
            for name, events in cc_events.items():
                shifted = [(ev[0] + current_start_beat, ev[1], ev[2]) for ev in events]
                if name not in combined_cc_events:
                    combined_cc_events[name] = []
                combined_cc_events[name].extend(shifted)

        # Apply crossfades and optional diatonic modulation bridge in the overlap region
        if i > 0 and overlap_beats > 0.0:
            overlap_start = current_start_beat
            overlap_end = current_start_beat + overlap_beats

            # Fade-in incoming tracks on CC 7 (Volume) from 0 to 100
            for name in track_dict.keys():
                fade_in = AutomationCurve.exponential(
                    7, 0, 100, overlap_start, overlap_end, exponent=1.5, steps=10
                )
                if name not in combined_cc_events:
                    combined_cc_events[name] = []
                combined_cc_events[name].extend(fade_in)

            # Fade-out outgoing tracks from the PREVIOUS track on CC 7 (Volume) from 100 to 0
            prev_meta = tracks_metadata[i - 1]
            prev_track_dict = prev_meta.get("tracks", {})
            for name in prev_track_dict.keys():
                fade_out = AutomationCurve.exponential(
                    7, 100, 0, overlap_start, overlap_end, exponent=1.5, steps=10
                )
                if name not in combined_cc_events:
                    combined_cc_events[name] = []
                combined_cc_events[name].extend(fade_out)

            # --- Diatonic modulation bridge ---
            if modulation_strategy is not None:
                prev_key = tracks_metadata[i - 1].get("key", None)
                if (
                    prev_key is not None
                    and this_key is not None
                    and (prev_key.root != this_key.root or prev_key.mode != this_key.mode)
                ):
                    bridge_chords = ModulationEngine.generate_modulation_bridge(
                        from_scale=prev_key,
                        to_scale=this_key,
                        length_beats=overlap_beats,
                        strategy=modulation_strategy,
                        start_beat=overlap_start,
                    )

                    # Build pad notes for each bridge chord (root + third + fifth, 3 octaves up from 48)
                    from melodica.theory import CHORD_TEMPLATES

                    bridge_notes: List[NoteInfo] = []
                    for chord in bridge_chords:
                        template = CHORD_TEMPLATES.get(chord.quality, [0, 4, 7])
                        base_midi = 48 + chord.root  # C3 + semitones
                        for interval in template:
                            pitch = base_midi + interval
                            if 0 <= pitch <= 127:
                                bridge_notes.append(
                                    NoteInfo(
                                        pitch=pitch,
                                        start=chord.start,
                                        duration=chord.duration * 0.95,  # slight gap between chords
                                        velocity=55,
                                    )
                                )

                    pad_track = "transition_pad"
                    if pad_track not in combined_tracks:
                        combined_tracks[pad_track] = []
                        combined_instruments[pad_track] = transition_instrument
                    combined_tracks[pad_track].extend(bridge_notes)

                    # Fade the transition pad in and out smoothly within the overlap
                    pad_fade_in = AutomationCurve.linear(
                        7, 0, 80, overlap_start, overlap_start + overlap_beats * 0.5, steps=5
                    )
                    pad_fade_out = AutomationCurve.linear(
                        7, 80, 0, overlap_start + overlap_beats * 0.5, overlap_end, steps=5
                    )
                    if pad_track not in combined_cc_events:
                        combined_cc_events[pad_track] = []
                    combined_cc_events[pad_track].extend(pad_fade_in)
                    combined_cc_events[pad_track].extend(pad_fade_out)
                    # Warm filter sweep on the transition pad
                    pad_sweep = AutomationCurve.exponential(
                        74, 35, 95, overlap_start, overlap_end, exponent=1.8, steps=8
                    )
                    combined_cc_events[pad_track].extend(pad_sweep)

        # Merge and shift tempo events
        if tempo_events:
            for ev in tempo_events:
                combined_tempo_events.append((ev[0] + current_start_beat, ev[1]))
        else:
            combined_tempo_events.append((current_start_beat, bpm))

        # Advance timeline
        next_start = (
            current_start_beat
            + track_dur
            - (overlap_beats if i < len(tracks_metadata) - 1 else 0.0)
        )
        current_start_beat = max(0.0, next_start)

    # Sort all notes, CC events, and combined sections
    for name in combined_tracks.keys():
        combined_tracks[name].sort(key=lambda note: note.start)
    for name in combined_cc_events.keys():
        combined_cc_events[name].sort(key=lambda ev: ev[0])
    combined_tempo_events.sort(key=lambda ev: ev[0])
    combined_sections.sort(key=lambda ev: ev[0])

    # Produce the continuous multi-track MIDI
    return produce_track(
        tracks=combined_tracks,
        bpm=first_bpm,
        instruments=combined_instruments,
        path=output_path,
        mood=mood,
        key=first_key,
        cc_events=combined_cc_events,
        tempo_events=combined_tempo_events,
        sections=combined_sections,
        rhythm=rhythm,
        chords=chords,
        genre=genre,
        time_signature=time_signature,
    )


def clamp_to_scale(pitch: int, scale: Scale) -> int:
    """Clamps a MIDI pitch to the nearest scale degree."""
    degrees = scale.degrees()
    pc = pitch % 12
    # Find scale degree with minimum distance to pc (wrapping around octave)
    nearest_pc = min(degrees, key=lambda d: min(abs(pc - d), 12 - abs(pc - d)))
    diff = nearest_pc - pc
    if diff > 6:
        diff -= 12
    elif diff < -6:
        diff += 12
    return max(0, min(127, int(round(pitch + diff))))


def generate_narrative_motif(
    motif_notes: list[NoteInfo],
    scale: Scale,
    transformation: str,
    offset_beats: float = 16.0,
    duration_beats: float = 64.0,
) -> list[NoteInfo]:
    """Apply narrative transformations (inversion, stretched, fragmented, retrograde, original) to a motif and snap to scale."""
    if not motif_notes:
        return []

    transformed = []
    first_pitch = motif_notes[0].pitch
    total_dur = max(x.start + x.duration for x in motif_notes) if motif_notes else 8.0

    for n in motif_notes:
        pitch = n.pitch
        start = n.start
        duration = n.duration
        velocity = n.velocity

        if transformation == "inversion":
            diff = pitch - first_pitch
            pitch = first_pitch - diff
        elif transformation == "stretched":
            start = start * 2.0
            duration = duration * 2.0
        elif transformation == "fragmented":
            # Deterministic gating: drop notes starting at odd integer beats
            if int(round(start)) % 2 == 1:
                continue
            velocity = int(velocity * 0.7)
        elif transformation == "retrograde":
            start = total_dur - (start + duration)

        pitch = clamp_to_scale(pitch, scale)

        transformed.append(
            NoteInfo(
                pitch=pitch,
                start=start,
                duration=duration,
                velocity=velocity,
                articulation=n.articulation,
                expression=dict(n.expression),
            )
        )

    transformed.sort(key=lambda x: x.start)
    if not transformed:
        return []

    motif_len = max(x.start + x.duration for x in transformed)
    if motif_len <= 0:
        motif_len = 8.0
    # Add a rest period: pad the loop length to avoid continuous monotony
    padded_len = max(motif_len + 4.0, 16.0)
    motif_len = float(int((padded_len + 7) / 8) * 8)

    looped_notes = []
    current_time = offset_beats
    end_time = offset_beats + duration_beats

    while current_time < end_time:
        for n in transformed:
            note_start = current_time + n.start
            if note_start + n.duration <= end_time:
                looped_notes.append(
                    NoteInfo(
                        pitch=n.pitch,
                        start=note_start,
                        duration=n.duration,
                        velocity=n.velocity,
                        articulation=n.articulation,
                        expression=dict(n.expression),
                    )
                )
        current_time += motif_len

    return looped_notes


@dataclass
class AlbumNarrative:
    """
    Core engine for AI-directed long-form listening experiences.
    Manages global emotional curves, motif memory evolution, harmonic continuity,
    and cross-track transitions.
    """
    output_dir: Path | str
    seed_motif: list[NoteInfo]
    harmonic_journey: list[Scale]
    tempos: list[float]
    track_configs: list[list[TrackConfig]]
    transformations: list[str]  # e.g. ["original", "inversion", "stretched", "fragmented", "retrograde"]
    sections_list: list[list[tuple[float, str]]]
    instruments_maps: list[dict[str, int]]
    moods: list[Mood]
    names: list[str]
    # Rhythm is mandatory for all album production. Pass a rhythm name (str)
    # from RHYTHM_LIBRARY/DYNAMIC_RHYTHM_REGISTRY or a RhythmGenerator instance.
    rhythm: str | object
    # Time signature shared across the album, e.g. (4, 4) or (3, 4).
    time_signature: tuple[int, int]
    # Optional genre override selecting the pan profile; defaults to
    # DEFAULT_GENRE ('lofi'). Must be a key of _ROLE_PAN_PROFILES if set.
    genre: str = DEFAULT_GENRE
    strict_validation: bool = True

    def generate(self) -> dict:
        """Generates all tracks and compiles them into a single continuous album."""
        import shutil
        from melodica.idea_tool import IdeaTool, IdeaToolConfig, IdeaPart
        out_path = Path(self.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        tracks_metadata = []
        per_track_chords = []  # chord progression of each track (for the compiled album)

        for i in range(len(self.harmonic_journey)):
            key = self.harmonic_journey[i]
            tempo = self.tempos[i]
            configs = self.track_configs[i]
            transform = self.transformations[i]
            sections = self.sections_list[i]
            instr_map = self.instruments_maps[i]
            mood = self.moods[i]
            name = self.names[i]

            print(f"  Generating narrative track {i+1}: {name} [{key.mode.value} — {tempo} BPM] with motif: {transform}")

            # 1. Setup IdeaParts
            max_beat = max(sec[0] for sec in sections)
            total_beats = max_beat + 16.0
            dur_bars = int(total_beats / 4)

            parts = [
                IdeaPart(
                    name=f"Part_{i}",
                    bars=dur_bars,
                    scale=key,
                    tempo=tempo,
                    progression_type="coupled_hmm"
                )
            ]

            # Setup tool and config
            config = IdeaToolConfig(
                parts=parts,
                tracks=configs,
                scale=key,
                tempo=tempo,
                use_tension_curve=True
            )

            tool = IdeaTool(config)
            result = tool.generate()
            tracks_dict = {k: v for k, v in result.items() if not k.startswith("_")}
            # Chord progression generated for this track — required by the
            # harmonic pipeline stages (texture / non_chord_tones / tension).
            part_chords = result.get("_chords") or tool.get_chords()
            per_track_chords.append(part_chords)

            # 2. Motif Memory Engine Integration
            lead_track_name = None
            for cfg in configs:
                if any(x in cfg.name for x in ("lead", "solo", "pluck", "melody")):
                    lead_track_name = cfg.name
                    break

            if lead_track_name:
                print(f"    -> Weaving motif {transform!r} into track {lead_track_name!r}")
                motif_notes = generate_narrative_motif(
                    self.seed_motif,
                    scale=key,
                    transformation=transform,
                    offset_beats=0.0,
                    duration_beats=total_beats
                )
                # Apply octave shift from TrackConfig if any
                target_cfg = next((c for c in configs if c.name == lead_track_name), None)
                if target_cfg and target_cfg.octave_shift:
                    for n in motif_notes:
                        n.pitch = max(0, min(127, n.pitch + target_cfg.octave_shift * 12))
                tracks_dict[lead_track_name] = motif_notes

            # 3. Produce and register metadata
            meta = produce_track(
                tracks_dict,
                bpm=tempo,
                instruments=instr_map,
                path=out_path / f"temp_{i}.mid",
                mood=mood,
                key=key,
                verbose=False,
                sections=sections,
                return_state=True,
                strict_validation=self.strict_validation,
                rhythm=self.rhythm,
                chords=part_chords,
                genre=self.genre,
                time_signature=self.time_signature,
            )

            tracks_metadata.append(meta)

        print("\n  Stitching tracks into a continuous narrative continuum...")
        # 4. Compile continuous album with 4-bar (16-beat) tail overlaps and modulation
        compiled_result = compile_continuous_album(
            tracks_metadata=tracks_metadata,
            output_path=out_path / "continuous_album.mid",
            overlap_beats=16.0,
            mood=Mood.CINEMATIC,
            modulation_strategy="pivot",
            rhythm=self.rhythm,
            chords=per_track_chords[0] if per_track_chords else [],
            genre=self.genre,
            time_signature=self.time_signature,
        )

        # Move individual tracks to their final home
        for i, name in enumerate(self.names):
            clean_filename = f"{i+1:02d}_{name.replace(' ', '_')}.mid"
            shutil.move(str(out_path / f"temp_{i}.mid"), str(out_path / clean_filename))

        print(f"  Narrative album compilation successful! Output at: {out_path / 'continuous_album.mid'}")
        return compiled_result

