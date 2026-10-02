# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.render.mix — Audio mixing, auto-spread panning, and mastering pipeline.

Handles:
- Track role detection and acoustic profiling
- Genre-aware stereophonic panning profiles
- Frequency mask conflict detection and PanValidator
- Adaptive gain staging and dynamic velocity shaping
- Percussion sidechain ducking
- Reverb/delay/pan automation generation
- Global polyphony voice capping and mastering desk integration
"""

from __future__ import annotations

import bisect
import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Tuple

from melodica.composer.automation import AutomationCurve
from melodica.composer.psychoacoustic import PsychoConfig, PsychoReport, psycho_verify
from melodica.midi import export_multitrack_midi
from melodica.shorts_mastering import MasteringDesk
from melodica.shorts_mixing import MixingDesk
from melodica.types import NoteInfo

if TYPE_CHECKING:
    from melodica.plan.album import _MoodProfile, Mood


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
    entry_beat: float = 0.0
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


def _infer_role_from_features(avg_pitch: float, density: float) -> Role:
    """Infer track role from statistical audio features when no name hint matches."""
    if avg_pitch < 48:
        return Role.BASS
    if density < 0.08:
        return Role.PAD
    if avg_pitch > 75 and density < 0.05:
        return Role.FX
    if avg_pitch > 60 and density > 0.15:
        return Role.LEAD
    if 40 < avg_pitch < 75 and 0.05 < density < 0.3:
        return Role.STRINGS
    return Role.LEAD


def _match_role_from_name(name_lower: str) -> Role | None:
    for hint, role in _NAME_HINTS.items():
        if hint in name_lower:
            return role
    return None


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

    role_final = _match_role_from_name(name.lower()) or _infer_role_from_features(avg_pitch, density)

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

_ROLE_PAN: Dict[Role, float] = _ROLE_PAN_PROFILES["techno"]
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

_PROTECTED_CENTER: set = {Role.BASS}


def _find_pitch_conflicts(
    names: list[str],
    profiles: Dict[str, _TrackProfile],
    threshold: float,
) -> list[tuple[str, str]]:
    """Find pairs of tracks whose average pitch difference is below threshold."""
    pairs: list[tuple[str, str]] = []
    paired: set[str] = set()
    for i, a in enumerate(names):
        if a in paired:
            continue
        for b in names[i + 1:]:
            if b in paired:
                continue
            if abs(profiles[a].avg_pitch - profiles[b].avg_pitch) < threshold:
                pairs.append((a, b))
                paired.update([a, b])
                break
    return pairs


def _spread_pads(
    pads: list[str],
    profiles: Dict[str, _TrackProfile],
    role_pan_map: Dict[Role, float],
    result: Dict[str, float],
) -> None:
    """Pairwise conflict resolution for pads sharing pitch register."""
    for a, b in _find_pitch_conflicts(pads, profiles, 8.0):
        result[a], result[b] = -0.40, 0.40
    default_pan = role_pan_map.get(Role.PAD, -0.30)
    for name in pads:
        result.setdefault(name, default_pan)


def _spread_leads(
    leads: list[str],
    profiles: Dict[str, _TrackProfile],
    lead_default: float,
    result: Dict[str, float],
) -> None:
    """Pairwise conflict resolution for leads sharing register."""
    for a, b in _find_pitch_conflicts(leads, profiles, 10.0):
        result[a] = lead_default - 0.15
        result[b] = lead_default + 0.15
    for name in leads:
        result.setdefault(name, lead_default)


def _group_tracks_by_role(profiles: Dict[str, _TrackProfile]) -> dict[Role, list[str]]:
    by_role: dict[Role, list[str]] = {}
    for name, prof in profiles.items():
        by_role.setdefault(prof.role, []).append(name)
    return by_role


def _auto_spread_panning(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    role_pan_map: Dict[Role, float],
) -> Dict[str, float]:
    """Resolve register conflicts — role-aware priority, no Role keys in output."""
    result: Dict[str, float] = {}
    by_role = _group_tracks_by_role(profiles)

    # 1. BASS - permanently center
    for name in by_role.get(Role.BASS, []):
        result[name] = 0.0

    # 2. PERC - genre default
    perc_pan = role_pan_map.get(Role.PERC, 0.0)
    for name in by_role.get(Role.PERC, []):
        result.setdefault(name, perc_pan)

    # 3. FX - alternating outer edges
    for idx, name in enumerate(by_role.get(Role.FX, [])):
        result[name] = 0.60 if idx % 2 == 0 else -0.60

    # 4. PADs
    _spread_pads(by_role.get(Role.PAD, []), profiles, role_pan_map, result)

    # 5. LEADs
    lead_default = role_pan_map.get(Role.LEAD, 0.08)
    _spread_leads(by_role.get(Role.LEAD, []), profiles, lead_default, result)

    # 6. Remaining
    for role, names in by_role.items():
        default_val = role_pan_map.get(role, 0.0)
        for name in names:
            result.setdefault(name, default_val)

    return result


# ---------------------------------------------------------------------------
# PanValidator — post-master verification of all pan assignments
# ---------------------------------------------------------------------------

_PAN_RULES: Dict[Role, tuple[float, float]] = {
    Role.BASS: (-0.05, 0.05),
    Role.LEAD: (-0.15, 0.15),
    Role.PAD: (-0.60, 0.60),
    Role.PERC: (-0.20, 0.20),
    Role.STRINGS: (-0.45, 0.45),
    Role.CHOIR: (-0.40, 0.40),
    Role.FX: (-0.65, 0.65),
}


def _check_frequency_pan_conflicts(
    pan_map: Dict[str, float],
    profiles: Dict[str, _TrackProfile],
    register_threshold: float = 6.0,
    pan_threshold: float = 0.15,
) -> list[tuple[str, str, str]]:
    """Detect masking: two tracks in same register AND same pan position."""
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


def _check_role_boundaries(
    pan_map: Dict[str, float], profiles: Dict[str, _TrackProfile]
) -> tuple[list[str], list[tuple[str, float, Role]]]:
    errors: list[str] = []
    seen: list[tuple[str, float, Role]] = []
    for name, pan in pan_map.items():
        prof = profiles.get(name)
        if not prof:
            continue
        role = prof.role
        lo, hi = _PAN_RULES.get(role, (-1.0, 1.0))
        if not (lo <= pan <= hi):
            errors.append(f"pan={pan:+.2f} вне [{lo},{hi}] для {name} ({role.value})")
        seen.append((name, pan, role))
    return errors, seen


def _check_point_overlaps(seen: list[tuple[str, float, Role]]) -> list[str]:
    warnings: list[str] = []
    for i in range(len(seen)):
        for j in range(i + 1, len(seen)):
            a_name, a_pan, a_role = seen[i]
            b_name, b_pan, b_role = seen[j]
            if abs(a_pan - b_pan) < 0.005:
                if not (a_role in (Role.BASS, Role.PERC) and abs(a_pan) < 0.1):
                    warnings.append(f"{a_name} и {b_name} стоят на одной точке: pan={a_pan:+.2f}")
    return warnings


def _check_stereo_width(seen: list[tuple[str, float, Role]]) -> tuple[float, list[str]]:
    import statistics as _stat
    warnings: list[str] = []
    non_bass_pans = [pan for (_, pan, role) in seen if role != Role.BASS]
    width_score = round(_stat.stdev(non_bass_pans), 3) if len(non_bass_pans) > 1 else 0.0
    if width_score < 0.10 and len(non_bass_pans) >= 3:
        warnings.append(f"Stereo width={width_score:.2f} — очень узкий микс")
    elif width_score > 0.50:
        warnings.append(f"Stereo width={width_score:.2f} — очень широкий микс")
    return width_score, warnings


class PanValidator:
    """Validates pan map for role boundaries, frequency conflicts, and stereo width."""

    def validate(self, pan_map: Dict[str, float], profiles: Dict[str, _TrackProfile]) -> list[str]:
        report = self.full_validate(pan_map, profiles)
        return report.errors + report.warnings

    def full_validate(self, pan_map: Dict[str, float], profiles: Dict[str, _TrackProfile]) -> PanReport:
        errors, seen = _check_role_boundaries(pan_map, profiles)
        warnings = _check_point_overlaps(seen)

        conflicts = _check_frequency_pan_conflicts(pan_map, profiles)
        for a, b, sev in conflicts:
            warnings.append(f"Маскировка ({sev}): {a} ↔ {b} — один регистр и pan")

        width_score, width_warnings = _check_stereo_width(seen)
        warnings.extend(width_warnings)
        mono_compatible = all(abs(pan) < 0.80 for _, pan, _ in seen)

        return PanReport(
            errors=errors,
            warnings=warnings,
            width_score=width_score,
            mono_compatible=mono_compatible,
        )


def _format_pan_bar(pan_norm: float, bar_len: int = 10) -> str:
    if abs(pan_norm) < 0.02:
        return f"  {'█' * bar_len}  C"
    if pan_norm < 0:
        left_px = int(abs(pan_norm) * bar_len)
        return f"  {'█' * left_px + '░' * (bar_len - left_px)}  L({pan_norm:+.2f})"
    right_px = int(pan_norm * bar_len)
    return f"  {'░' * (bar_len - right_px) + '█' * right_px}  R({pan_norm:+.2f})"


def _print_pan_map(
    profiles: Dict[str, _TrackProfile],
    pan_map: Dict[str, float],
    mood_profile: _MoodProfile,
) -> None:
    """Print human-readable pan map bar chart."""
    print("   Pan Map:")
    max_len = max((len(n) for n in pan_map), default=5)
    for name in sorted(pan_map.keys()):
        pan = pan_map[name]
        role = profiles.get(name)
        role_str = f"({role.role.value})" if role else ""
        print(f"   {name:<{max_len+1}s} {_format_pan_bar(pan)}  {role_str}")

    non_centre = [abs(v) for v in pan_map.values() if abs(v) > 0.05]
    if non_centre:
        width = round(sum(non_centre) / len(non_centre), 3)
        print(f"   Stereo Width: {width:.3f}")
    else:
        print("   Stereo Width: 0.000  (mono)")


# ---------------------------------------------------------------------------
# Auto-mix & Gain staging
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


def _density_gain_factor(density: float) -> float:
    """Sparse tracks need boost, dense tracks need duck."""
    if density < 0.05:
        return 1.25
    if density < 0.15:
        return 1.10
    if density < 0.5:
        return 1.0
    if density < 2.0:
        return 0.90
    if density < 10.0:
        return 0.80
    return 0.70


def _compute_register_tweak(avg_pitch: float, bass_boost: float) -> float:
    if avg_pitch < 48:
        return 1.10 * bass_boost
    if avg_pitch < 60:
        return 1.03
    if avg_pitch > 84:
        return 0.85
    if avg_pitch > 72:
        return 0.92
    return 1.0


def _duck_overlapping_registers(
    profiles: Dict[str, _TrackProfile], gains: Dict[str, float]
) -> None:
    names = [n for n in profiles if profiles[n].role not in (Role.PERC, Role.FX)]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = profiles[names[i]], profiles[names[j]]
            if abs(a.avg_pitch - b.avg_pitch) < 8:
                quieter = names[i] if a.rms_velocity < b.rms_velocity else names[j]
                gains[quieter] *= 0.75


def _auto_mix(
    tracks: Dict[str, List[NoteInfo]],
    mood_profile: _MoodProfile,
    genre: str | None = None,
) -> Tuple[Dict[str, List[NoteInfo]], Dict[str, _TrackProfile], Dict[str, float]]:
    """Analyze tracks, assign gains by role + density, apply register shaping."""
    total_dur = 0.0
    for name, notes in tracks.items():
        if name.startswith("_") or not notes:
            continue
        for n in notes:
            total_dur = max(total_dur, n.start + n.duration)

    profiles: dict[str, _TrackProfile] = {}
    for name, notes in tracks.items():
        if not notes or name.startswith("_"):
            continue
        profiles[name] = _analyze_track(name, notes, total_dur)

    gains: Dict[str, float] = {}
    for name, prof in profiles.items():
        base = _ROLE_GAINS.get(prof.role, 0.80)
        density_factor = _density_gain_factor(prof.density)
        reg_tweak = _compute_register_tweak(prof.avg_pitch, mood_profile.bass_boost)
        gains[name] = base * density_factor * reg_tweak

    _duck_overlapping_registers(profiles, gains)

    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update(gains)
    mixed = desk.apply_mixing(tracks, [], 120)

    role_pan_map = _get_role_pan_map(genre)
    return mixed, profiles, role_pan_map


# ---------------------------------------------------------------------------
# Sidechain ducking
# ---------------------------------------------------------------------------


def _duck_track_notes(
    notes: List[NoteInfo], hit_times: List[float], window: float, duck_amount: float
) -> List[NoteInfo]:
    new_notes: List[NoteInfo] = []
    for n in notes:
        lo = n.start - window
        hi = n.start + n.duration + window
        idx = bisect.bisect_left(hit_times, lo)
        if idx < len(hit_times) and hit_times[idx] <= hi:
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
    return new_notes


def _select_duck_target_names(profiles: Dict[str, _TrackProfile]) -> tuple[list[str], set[str]]:
    perc: list[str] = []
    duck: set[str] = set()
    for n, p in profiles.items():
        if p.role == Role.PERC:
            perc.append(n)
        elif p.role in (Role.BASS, Role.PAD):
            duck.add(n)
    return perc, duck


def _collect_perc_hit_times(tracks: Dict[str, List[NoteInfo]], perc_names: list[str]) -> list[float]:
    times: list[float] = []
    for pn in perc_names:
        times.extend(n.start for n in tracks.get(pn, ()))
    times.sort()
    return times


def _sidechain_duck(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    duck_amount: float = 0.45,
    window: float = 0.15,
) -> Dict[str, List[NoteInfo]]:
    """Reduce velocity of bass/pad notes that overlap perc hits within window."""
    perc_names, duck_names = _select_duck_target_names(profiles)
    if not perc_names or not duck_names:
        return tracks

    hit_times = _collect_perc_hit_times(tracks, perc_names)
    if not hit_times:
        return tracks

    result: Dict[str, List[NoteInfo]] = {}
    for tname, notes in tracks.items():
        if not tname.startswith("_") and tname in duck_names:
            result[tname] = _duck_track_notes(notes, hit_times, window, duck_amount)
        else:
            result[tname] = notes

    return result


# ---------------------------------------------------------------------------
# Humanization
# ---------------------------------------------------------------------------

_HUMANIZE_PROFILES: Dict[str, tuple[float, int, float, str]] = {
    "flute": (0.025, 6, 0.08, "push"),
    "oboe": (0.022, 5, 0.07, "push"),
    "clarinet": (0.025, 6, 0.08, "push"),
    "bassoon": (0.020, 5, 0.07, "lay_back"),
    "violin": (0.035, 8, 0.12, "lay_back"),
    "viola": (0.030, 7, 0.12, "lay_back"),
    "cello": (0.025, 6, 0.10, "lay_back"),
    "strings": (0.030, 7, 0.12, "lay_back"),
    "horn": (0.030, 8, 0.06, "lay_back"),
    "brass": (0.025, 9, 0.06, "lay_back"),
    "trumpet": (0.020, 7, 0.05, "straight"),
    "trombone": (0.030, 8, 0.07, "lay_back"),
    "harp": (0.015, 5, 0.04, "straight"),
    "piano": (0.018, 6, 0.04, "straight"),
    "celesta": (0.015, 4, 0.03, "straight"),
    "glock": (0.012, 4, 0.03, "straight"),
    "glockenspiel": (0.012, 4, 0.03, "straight"),
    "bass": (0.012, 4, 0.03, "lay_back"),
    "contrabass": (0.010, 3, 0.03, "lay_back"),
    "pedal": (0.008, 2, 0.02, "straight"),
    "choir": (0.040, 10, 0.15, "lay_back"),
    "voice": (0.040, 10, 0.15, "lay_back"),
    "timp": (0.010, 10, 0.02, "straight"),
    "perc": (0.010, 10, 0.02, "straight"),
    "lead": (0.025, 6, 0.08, "straight"),
    "canon": (0.030, 7, 0.10, "lay_back"),
}

_HUMANIZE_ROLE_DEFAULTS: Dict[Role, tuple[float, int, float, str]] = {
    Role.LEAD: (0.025, 6, 0.08, "straight"),
    Role.STRINGS: (0.030, 7, 0.12, "lay_back"),
    Role.CHOIR: (0.040, 10, 0.15, "lay_back"),
    Role.BASS: (0.012, 4, 0.03, "lay_back"),
    Role.PAD: (0.020, 5, 0.06, "straight"),
    Role.PERC: (0.010, 10, 0.02, "straight"),
    Role.FX: (0.015, 3, 0.02, "straight"),
}


def _humanize_profile(tname: str, role: Role) -> tuple[float, int, float, str]:
    name_lower = tname.lower()
    for key, profile in _HUMANIZE_PROFILES.items():
        if key in name_lower:
            return profile
    return _HUMANIZE_ROLE_DEFAULTS.get(role, (0.020, 5, 0.06, "straight"))


def _humanize_track_notes(
    notes: list[NoteInfo],
    tname: str,
    prof: _TrackProfile,
) -> list[NoteInfo]:
    """Humanize a single track with jitter and groove offsets."""
    t_base, v_base, dur_base, groove = _humanize_profile(tname, prof.role)
    density_factor = min(1.0, prof.density / 2.0)
    effective_t = t_base * (1.0 - 0.90 * density_factor)
    effective_v = max(1, int(v_base * (1.0 + 1.0 * density_factor)))

    rng = random.Random(hash(tname) & 0xFFFFFFFF)
    new_notes: list[NoteInfo] = []
    for n in notes:
        t_jitter = rng.gauss(0.0, effective_t * 0.4)
        if groove == "lay_back":
            t_jitter += effective_t * 0.25
        elif groove == "push":
            t_jitter -= effective_t * 0.20

        v_jit = int(rng.gauss(0.0, effective_v * 0.5))
        dur_jit = max(0.85, min(1.20, 1.0 + rng.gauss(0.0, dur_base * 0.4)))

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
    return new_notes


def _apply_humanization(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    swing_amount: float = 0.02,
    vel_jitter: int = 4,
) -> Dict[str, List[NoteInfo]]:
    """Add per-instrument humanization: micro-timing, velocity scatter, duration jitter."""
    result = {}
    for tname, notes in tracks.items():
        if tname.startswith("_"):
            result[tname] = notes
            continue
        prof = profiles.get(tname)
        if not prof or prof.role == Role.FX:
            result[tname] = notes
            continue
        result[tname] = _humanize_track_notes(notes, tname, prof)
    return result


# ---------------------------------------------------------------------------
# Automation: entry fades, reverb, delay, pan
# ---------------------------------------------------------------------------


def _generate_entry_fades(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    total_dur: float,
    fade_beats: float = 8.0,
) -> Dict[str, List[Tuple[float, int, int]]]:
    """Generate CC11 expression events for tracks that enter late."""
    cc_events: Dict[str, List[Tuple[float, int, int]]] = {}
    threshold = total_dur * 0.1

    for tname, prof in profiles.items():
        if prof.entry_beat < threshold or prof.role in (Role.PERC, Role.FX):
            continue
        notes = tracks.get(tname, [])
        if not notes:
            continue

        events = []
        entry = prof.entry_beat
        steps = max(4, int(fade_beats / 0.5))
        for i in range(steps + 1):
            t = entry - fade_beats + (i / steps) * fade_beats
            if t >= 0:
                events.append((t, 11, int(20 + (80 * i / steps))))
        events.append((entry + 0.01, 11, 100))
        cc_events[tname] = events

    return cc_events


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
    total_notes = sum(p.note_count for p in profiles.values())
    density_boost = min(20, total_notes // 200)

    for tname, prof in profiles.items():
        notes = tracks.get(tname, [])
        if not notes:
            continue
        base_reverb = _ROLE_REVERB.get(prof.role, 40)
        reverb = min(127, base_reverb + density_boost)
        if mood_profile.lufs < -18:
            reverb = min(127, reverb + 15)
        elif mood_profile.lufs > -13:
            reverb = max(10, reverb - 10)
        cc_events[tname] = [(notes[0].start, 91, reverb)]

    return cc_events


def _generate_delay_sends(
    tracks: Dict[str, List[NoteInfo]], profiles: Dict[str, _TrackProfile]
) -> Dict[str, List[Tuple[float, int, int]]]:
    """Generate CC93 delay send for tracks with 'echo' or 'delay' in name."""
    cc_events: Dict[str, List[Tuple[float, int, int]]] = {}
    for tname, notes in tracks.items():
        name_lower = tname.lower()
        if ("echo" not in name_lower and "delay" not in name_lower) or not notes:
            continue
        delay_level = 60 if "far" in name_lower else 40
        cc_events[tname] = [(notes[0].start, 93, delay_level)]
    return cc_events


@dataclass(frozen=True)
class _PanWidthConfig:
    pad_spread: int
    fx_spread: int = 12


@dataclass(frozen=True)
class _BreakPanContext:
    sec_name: str
    sec_beat: float
    t_end: float
    role: Role
    anchor_cc10: int
    pan_norm: float


def _apply_section_break_pan(
    ctx: _BreakPanContext,
    evts: list[tuple[float, int, int]],
) -> None:
    if ctx.sec_name == "drop" and ctx.role == Role.PAD:
        evts.append((round(ctx.sec_beat, 6), 10, max(0, min(127, int(64 + ctx.pan_norm * 63 * 1.5)))))
    elif ctx.sec_name in ("break", "bridge") and ctx.role in (Role.PAD, Role.STRINGS):
        evts.append((round(ctx.sec_beat, 6), 10, 64))
    elif ctx.sec_name == "intro":
        evts.extend(
            AutomationCurve.linear(10, 64, ctx.anchor_cc10, ctx.sec_beat, min(ctx.sec_beat + 8.0, ctx.t_end), steps=8)
        )
    elif ctx.sec_name == "outro":
        evts.extend(
            AutomationCurve.linear(10, ctx.anchor_cc10, 64, ctx.sec_beat, min(ctx.sec_beat + 8.0, ctx.t_end), steps=8)
        )


def _build_track_pan_events(
    prof: _TrackProfile,
    notes: list[NoteInfo],
    pan_norm: float,
    cfg: _PanWidthConfig,
    section_breaks: list[tuple[float, str]] | None,
) -> list[tuple[float, int, int]]:
    """Build CC10 pan automation events for one track."""
    t_start = notes[0].start
    t_end = notes[-1].start + notes[-1].duration
    span = t_end - t_start
    evts: list[tuple[float, int, int]] = []

    anchor_cc10 = max(0, min(127, int(64 + pan_norm * 63)))
    beat = t_start
    while beat <= t_end:
        evts.append((round(beat, 6), 10, anchor_cc10))
        beat += 16.0

    if prof.role == Role.PAD and span > 2.0:
        lo = max(20, anchor_cc10 - cfg.pad_spread)
        hi = min(107, anchor_cc10 + cfg.pad_spread)
        evts.extend(
            AutomationCurve.sine_lfo(
                cc_num=10, min_val=lo, max_val=hi,
                start_beat=t_start, end_beat=t_end,
                period=max(4.0, span / 2), steps_per_period=8,
            )
        )
    elif prof.role == Role.FX and prof.entry_beat < t_end:
        sweep_end = prof.entry_beat + min(1.5, t_end - prof.entry_beat)
        evts.extend(
            AutomationCurve.linear(
                cc_num=10, start_val=min(107, 64 + cfg.fx_spread), end_val=64,
                start_beat=prof.entry_beat, end_beat=sweep_end, steps=6,
            )
        )

    if section_breaks:
        for sec_beat, sec_name in section_breaks:
            if t_start <= sec_beat <= t_end:
                ctx = _BreakPanContext(sec_name, sec_beat, t_end, prof.role, anchor_cc10, pan_norm)
                _apply_section_break_pan(ctx, evts)

    return evts


def _resolve_effective_mood(mood: Mood | None, lufs: float) -> str:
    """Resolve mood string name for width selection."""
    if mood is not None:
        return mood.value
    if lufs <= -20:
        return "ambient"
    if lufs <= -18:
        return "intimate"
    if lufs <= -16:
        return "chamber"
    if lufs <= -15:
        return "experimental"
    if lufs <= -14:
        return "cinematic"
    return "aggressive"


def _generate_pan_automation(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    mood_profile: _MoodProfile,
    mood: Mood | None = None,
    spread_map: Dict[str, float] | None = None,
    tension: float | None = None,
    section_breaks: List[Tuple[float, str]] | None = None,
) -> Dict[str, List[Tuple[float, int, int]]]:
    """Generate CC10 pan automation with anchors, tension-aware width, and section events."""
    cc_events: Dict[str, List[Tuple[float, int, int]]] = {}
    spread = spread_map or {}

    width_map = {
        "ambient": 5, "intimate": 3, "chamber": 7,
        "experimental": 12, "cinematic": 9, "aggressive": 11,
    }
    eff_key = _resolve_effective_mood(mood, mood_profile.lufs)
    base_spread = width_map.get(eff_key, 9)

    if tension is not None:
        pad_cc_spread = int(base_spread * (0.5 + 0.5 * tension))
    else:
        pad_cc_spread = base_spread
    fx_cc_spread = 12

    for tname, prof in profiles.items():
        notes = tracks.get(tname, [])
        if not notes:
            continue
        evts = _build_track_pan_events(
            prof, notes, spread.get(tname, 0.0), _PanWidthConfig(pad_cc_spread, fx_cc_spread), section_breaks
        )
        if evts:
            evts.sort(key=lambda e: (e[0], e[1]))
            cc_events[tname] = evts

    return cc_events


# ---------------------------------------------------------------------------
# Polyphony & Safeguards
# ---------------------------------------------------------------------------

_POLY_SLOT_RESOLUTION = 4.0
_SPARSE_THRESHOLD = 10


_ROLE_PRIORITY: dict[Role, int] = {
    Role.LEAD: 0,
    Role.STRINGS: 1,
    Role.PERC: 2,
    Role.BASS: 3,
    Role.CHOIR: 4,
    Role.PAD: 5,
    Role.FX: 6,
}


def _cull_slot_voices(
    active: list[tuple[str, NoteInfo]],
    max_voices: int,
    profiles: Dict[str, _TrackProfile],
    drop_ids: set,
) -> None:
    if len(active) <= max_voices:
        return
    active.sort(
        key=lambda x: (
            _ROLE_PRIORITY.get(
                profiles.get(x[0], _TrackProfile(60, 0, 0, 0, Role.PAD)).role, 5
            ),
            -x[1].velocity,
        )
    )
    for _, n in active[max_voices:]:
        drop_ids.add(id(n))


def _collect_flattened_notes(
    tracks: Dict[str, List[NoteInfo]],
) -> list[tuple[float, float, str, NoteInfo]]:
    flattened: list[tuple[float, float, str, NoteInfo]] = []
    for tname, notes in tracks.items():
        if tname.startswith("_") or not notes:
            continue
        for n in notes:
            flattened.append((n.start, n.start + n.duration, tname, n))
    flattened.sort(key=lambda x: x[0])
    return flattened


def _filter_active_slot(
    candidates: list[tuple[float, float, str, NoteInfo]],
    slot: float,
    slot_end: float,
    drop_ids: set[int],
) -> list[tuple[str, NoteInfo]]:
    active: list[tuple[str, NoteInfo]] = []
    for ns, ne, tname, n in candidates:
        if ns < slot_end and ne > slot and id(n) not in drop_ids:
            active.append((tname, n))
    return active


def _scan_polyphony_slots(
    all_notes: list[tuple[float, float, str, NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    max_voices: int,
) -> set[int]:
    drop_ids: set[int] = set()
    t_min, t_max = all_notes[0][0], max(x[1] for x in all_notes)
    slot_dur = 1.0 / _POLY_SLOT_RESOLUTION
    starts = [x[0] for x in all_notes]

    slot = t_min
    while slot < t_max:
        slot_end = slot + slot_dur
        lo = bisect.bisect_left(starts, slot - 10.0)
        hi = bisect.bisect_right(starts, slot_end)
        active = _filter_active_slot(all_notes[lo:hi], slot, slot_end, drop_ids)
        _cull_slot_voices(active, max_voices, profiles, drop_ids)
        slot = slot_end
    return drop_ids


def _polyphony_limit(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    max_voices: int = 16,
) -> Dict[str, List[NoteInfo]]:
    """Cap simultaneous voices across all tracks."""
    all_notes = _collect_flattened_notes(tracks)
    if not all_notes:
        return tracks

    drop_ids = _scan_polyphony_slots(all_notes, profiles, max_voices)
    if not drop_ids:
        return tracks

    return {
        tname: [n for n in notes if id(n) not in drop_ids]
        for tname, notes in tracks.items()
    }


def _sparse_safeguard(
    tracks: Dict[str, List[NoteInfo]], profiles: Dict[str, _TrackProfile]
) -> Dict[str, List[NoteInfo]]:
    """Clamp velocity on sparse tracks to prevent RMS normalization explosion."""
    result = {}
    for tname, notes in tracks.items():
        if tname.startswith("_"):
            result[tname] = notes
            continue
        prof = profiles.get(tname)
        if prof and prof.note_count < _SPARSE_THRESHOLD and notes:
            clamped = [
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=min(90, n.velocity),
                    articulation=n.articulation,
                    expression=n.expression,
                )
                for n in notes
            ]
            result[tname] = clamped
        else:
            result[tname] = notes
    return result


# ---------------------------------------------------------------------------
# Auto-mastering & Dynamics shaping
# ---------------------------------------------------------------------------

_DYNAMICS_WINDOW_BEATS = 32.0


def _auto_master(
    tracks: Dict[str, List[NoteInfo]],
    profiles: Dict[str, _TrackProfile],
    mood_profile: _MoodProfile,
    pan_overrides: Dict[str, float] | None = None,
) -> Tuple[Dict[str, List[NoteInfo]], Dict[str, List[Tuple[float, int, int]]]]:
    """Master with mood-aware LUFS, role-based pan, and brightness ceiling."""
    pan_map = {}
    for name, prof in profiles.items():
        if pan_overrides and name in pan_overrides:
            pan_map[name] = pan_overrides[name]
        else:
            pan_map[name] = _ROLE_PAN.get(prof.role, 0.0)

    master = MasteringDesk(
        target_lufs=mood_profile.lufs,
        track_pan=pan_map,
    )
    mastered, cc_events = master.apply_mastering(tracks)

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


def _windowed_velocity_scale(notes: list[NoteInfo], dyn: float) -> list[NoteInfo]:
    shaped: list[NoteInfo] = []
    for n in notes:
        lo = n.start - _DYNAMICS_WINDOW_BEATS / 2
        hi = n.start + _DYNAMICS_WINDOW_BEATS / 2
        local_vels = [x.velocity for x in notes if lo <= x.start <= hi]
        if not local_vels:
            shaped.append(n)
            continue
        local_center = (min(local_vels) + max(local_vels)) / 2
        new_vel = max(10, min(127, int(round(local_center + (n.velocity - local_center) * dyn))))
        shaped.append(
            NoteInfo(
                pitch=n.pitch, start=n.start, duration=n.duration,
                velocity=new_vel, articulation=n.articulation, expression=n.expression,
            )
        )
    return shaped


def _global_velocity_scale(notes: list[NoteInfo], vels: list[int], dyn: float) -> list[NoteInfo]:
    center = (min(vels) + max(vels)) / 2
    return [
        NoteInfo(
            pitch=n.pitch, start=n.start, duration=n.duration,
            velocity=max(10, min(127, int(round(center + (n.velocity - center) * dyn)))),
            articulation=n.articulation, expression=n.expression,
        )
        for n in notes
    ]


def _shape_dynamics(
    tracks: Dict[str, List[NoteInfo]], mood_profile: _MoodProfile
) -> Dict[str, List[NoteInfo]]:
    """Widen or compress velocity range based on mood dynamics setting."""
    dyn = mood_profile.dynamics_range
    if dyn >= 0.95:
        return tracks

    result: Dict[str, List[NoteInfo]] = {}
    for name, notes in tracks.items():
        if not notes or name.startswith("_"):
            result[name] = notes
            continue

        vels = [n.velocity for n in notes]
        if max(vels) - min(vels) < 5:
            result[name] = notes
            continue

        span = (notes[-1].start + notes[-1].duration) - notes[0].start
        if span > _DYNAMICS_WINDOW_BEATS * 2:
            result[name] = _windowed_velocity_scale(notes, dyn)
        else:
            result[name] = _global_velocity_scale(notes, vels, dyn)

    return result


def _merge_cc_events(
    *sources: Dict[str, List[Tuple[float, int, int]]],
) -> Dict[str, List[Tuple[float, int, int]]]:
    """Merge multiple CC event dicts into one, sorted by time."""
    merged: Dict[str, List[Tuple[float, int, int]]] = {}
    for src in sources:
        for tname, events in src.items():
            merged.setdefault(tname, []).extend(events)
    for tname in merged:
        merged[tname].sort(key=lambda e: e[0])
    return merged


# ---------------------------------------------------------------------------
# Pipeline mix stages
# ---------------------------------------------------------------------------


def _stage_auto_mix(kw: dict) -> dict:
    mixed, profiles, role_pan_map = _auto_mix(
        kw["tracks"], kw["mood_profile"], genre=kw.get("genre"),
    )
    kw["tracks"] = mixed
    kw["_profiles"] = profiles
    kw["_role_pan_map"] = role_pan_map
    return kw


def _stage_pan_spread(kw: dict) -> dict:
    spread_map = _auto_spread_panning(
        kw["tracks"], kw["_profiles"], kw["_role_pan_map"],
    )
    kw["_pan_spread_map"] = spread_map
    return kw


def _stage_dynamics(kw: dict) -> dict:
    kw["tracks"] = _shape_dynamics(kw["tracks"], kw["mood_profile"])
    return kw


def _stage_sidechain(kw: dict) -> dict:
    kw["tracks"] = _sidechain_duck(kw["tracks"], kw["_profiles"])
    return kw


def _stage_humanize(kw: dict) -> dict:
    kw["tracks"] = _apply_humanization(kw["tracks"], kw["_profiles"])
    return kw


def _stage_polyphony(kw: dict) -> dict:
    kw["tracks"] = _polyphony_limit(kw["tracks"], kw["_profiles"], max_voices=16)
    return kw


def _stage_psycho(kw: dict) -> dict:
    if kw.get("psycho_verify_enabled", True):
        config = PsychoConfig(aggressive_fix=kw["mood_profile"].psycho_aggressive)
        kw["tracks"], psycho_report = psycho_verify(kw["tracks"], config, bpm=kw["bpm"])
        kw["_psycho_report"] = psycho_report
    else:
        kw["_psycho_report"] = None
    return kw


def _stage_sparse_safeguard(kw: dict) -> dict:
    kw["tracks"] = _sparse_safeguard(kw["tracks"], kw["_profiles"])
    return kw


def _stage_master(kw: dict) -> dict:
    spread_map = kw.get("_pan_spread_map", {})
    master = MasteringDesk(
        target_lufs=kw["mood_profile"].lufs,
        track_pan=spread_map,
    )
    mastered, master_cc = master.apply_mastering(kw["tracks"])
    total_dur = max(
        (n.start + n.duration for name, ns in mastered.items() if not name.startswith("_") for n in ns),
        default=0.0,
    )

    entry_cc = _generate_entry_fades(mastered, kw["_profiles"], total_dur)
    reverb_cc = _generate_reverb_sends(mastered, kw["_profiles"], kw["mood_profile"])
    delay_cc = _generate_delay_sends(mastered, kw["_profiles"])
    pan_auto_cc = _generate_pan_automation(
        mastered,
        kw["_profiles"],
        kw["mood_profile"],
        mood=kw.get("mood"),
        spread_map=spread_map,
        tension=kw.get("_tension"),
        section_breaks=kw.get("section_breaks"),
    )

    all_cc = _merge_cc_events(
        master_cc, entry_cc, reverb_cc, delay_cc, pan_auto_cc, kw.get("cc_events", {})
    )

    validator = PanValidator()
    pan_warnings = validator.validate(spread_map, kw["_profiles"])
    if pan_warnings and kw.get("verbose"):
        for w in pan_warnings:
            print(f"   Pan warning: {w}")

    kw["_mastered"] = mastered
    kw["_all_cc"] = all_cc
    return kw


def _stage_export(kw: dict) -> dict:
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


def _build_profile_summary(profiles: dict[str, _TrackProfile]) -> dict[str, dict]:
    return {
        name: {
            "role": p.role.value,
            "avg_pitch": round(p.avg_pitch, 1),
            "density": round(p.density, 3),
            "rms": round(p.rms_velocity, 1),
            "entry": round(p.entry_beat, 1),
        }
        for name, p in profiles.items()
    }


def _compute_stereo_width(spread_map: dict[str, float]) -> float:
    non_centre = [abs(v) for v in spread_map.values() if abs(v) > 0.05]
    return round(sum(non_centre) / len(non_centre), 3) if non_centre else 0.0


def _stage_report(kw: dict) -> dict:
    profiles = kw["_profiles"]
    psycho_report = kw.get("_psycho_report")
    mood = kw["mood"]
    mood_profile = kw["mood_profile"]
    all_cc = kw.get("_all_cc", {})
    spread_map = kw.get("_pan_spread_map", {})

    report = {
        "profiles": _build_profile_summary(profiles),
        "psycho": psycho_report,
        "mood": mood.value,
        "lufs": mood_profile.lufs,
        "cc_events": {k: len(v) for k, v in all_cc.items()},
        "pan_map": {
            name: {
                "role": profiles[name].role.value,
                "pan": round(spread_map.get(name, 0.0), 3),
            }
            for name in profiles
        },
        "stereo_width": _compute_stereo_width(spread_map),
    }

    if kw.get("verbose"):
        roles = {name: p.role.value for name, p in profiles.items()}
        print(f"   Roles: {roles} | LUFS: {mood_profile.lufs}")
        _print_pan_map(profiles, spread_map, mood_profile)

    kw["_report"] = report
    return kw
