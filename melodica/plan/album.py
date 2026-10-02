# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.plan.album — Album narrative planning, section progression, and compilation.

Handles:
- Mood profiles and listening presets (Ambient, Intimate, Cinematic, etc.)
- SectionProfile architecture and intelligent section detection
- Harmonic tension calculation and dynamics boosting
- Cross-movement narrative motif memory transformations (inversion, retrograde, stretch)
- Continuous album multi-track compilation with modulation bridges
- Album narrative director (AlbumNarrative)
"""

from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Tuple

from melodica.render.mix import DEFAULT_GENRE, Role, _TrackProfile
from melodica.types import NoteInfo, Scale

if TYPE_CHECKING:
    from melodica.idea_tool import TrackConfig


# ---------------------------------------------------------------------------
# Mood presets
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
# Section profiles
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
    active_roles: list[Role] | None = None
    entropy: float = 0.0


SECTION_PROFILES: Dict[str, SectionProfile] = {
    "Intro": SectionProfile(
        mood=Mood.AMBIENT, dynamics_range=0.8, brightness_ceiling=95,
        energy_target=0.5, note_density=0.5, timing_drift=0.0, velocity_drift=8,
        reverb_amount=85, filter_cutoff=70, active_roles=[Role.PAD],
    ),
    "Theme": SectionProfile(
        mood=Mood.INTIMATE, dynamics_range=0.7, brightness_ceiling=112,
        energy_target=0.7, note_density=0.8, timing_drift=0.0, velocity_drift=4,
        reverb_amount=45, filter_cutoff=100, active_roles=[Role.PAD, Role.BASS],
    ),
    "Variation": SectionProfile(
        mood=Mood.EXPERIMENTAL, dynamics_range=0.9, brightness_ceiling=120,
        energy_target=0.85, note_density=0.9, timing_drift=0.0, velocity_drift=6,
        reverb_amount=50, filter_cutoff=110, active_roles=[Role.PAD, Role.BASS, Role.LEAD],
    ),
    "Breakdown": SectionProfile(
        mood=Mood.AMBIENT, dynamics_range=0.8, brightness_ceiling=100,
        energy_target=0.4, note_density=0.4, timing_drift=0.0, velocity_drift=10,
        reverb_amount=95, filter_cutoff=60, active_roles=[Role.PAD, Role.LEAD],
    ),
    "Climax": SectionProfile(
        mood=Mood.CINEMATIC, dynamics_range=0.5, brightness_ceiling=127,
        energy_target=1.1, note_density=1.0, timing_drift=0.0, velocity_drift=2,
        reverb_amount=25, filter_cutoff=127, active_roles=[Role.PAD, Role.BASS, Role.LEAD, Role.PERC],
    ),
    "Fade": SectionProfile(
        mood=Mood.AMBIENT, dynamics_range=0.8, brightness_ceiling=90,
        energy_target=0.3, note_density=0.3, timing_drift=0.0, velocity_drift=10,
        reverb_amount=70, filter_cutoff=65, active_roles=[Role.PAD],
    ),
    "Emergence": SectionProfile(
        mood=Mood.AMBIENT, dynamics_range=0.8, brightness_ceiling=90,
        energy_target=0.4, note_density=0.4, timing_drift=0.0, velocity_drift=8,
        reverb_amount=95, filter_cutoff=55, active_roles=[Role.PAD], entropy=0.1,
    ),
    "Expansion": SectionProfile(
        mood=Mood.INTIMATE, dynamics_range=0.7, brightness_ceiling=105,
        energy_target=0.65, note_density=0.7, timing_drift=0.0, velocity_drift=5,
        reverb_amount=60, filter_cutoff=85, active_roles=[Role.PAD, Role.BASS], entropy=0.2,
    ),
    "Tension": SectionProfile(
        mood=Mood.EXPERIMENTAL, dynamics_range=0.9, brightness_ceiling=118,
        energy_target=0.85, note_density=0.9, timing_drift=0.0, velocity_drift=7,
        reverb_amount=50, filter_cutoff=110, active_roles=[Role.PAD, Role.BASS, Role.LEAD], entropy=0.6,
    ),
    "Release": SectionProfile(
        mood=Mood.CINEMATIC, dynamics_range=0.5, brightness_ceiling=127,
        energy_target=1.15, note_density=1.0, timing_drift=0.0, velocity_drift=3,
        reverb_amount=30, filter_cutoff=127, active_roles=[Role.PAD, Role.BASS, Role.LEAD, Role.PERC], entropy=0.3,
    ),
    "Dissolve": SectionProfile(
        mood=Mood.AMBIENT, dynamics_range=0.8, brightness_ceiling=85,
        energy_target=0.35, note_density=0.3, timing_drift=0.0, velocity_drift=12,
        reverb_amount=80, filter_cutoff=60, active_roles=[Role.PAD], entropy=0.8,
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


def _resolve_section_profile(sec_key: Mood | str) -> SectionProfile:
    """Resolve SectionProfile from a string key or Mood enum."""
    val = getattr(sec_key, "value", sec_key)
    if str(val) in SECTION_PROFILES:
        return SECTION_PROFILES[str(val)]
    for p in SECTION_PROFILES.values():
        if p.mood == sec_key or p.mood.value == val:
            return p
    return SECTION_PROFILES["Theme"]


def _build_section_cc_automation(
    tracks: Dict[str, List[NoteInfo]],
    sections: List[Tuple[float, Mood | str]],
    cc_events: Dict[str, List[Tuple[float, int, int]]],
) -> Dict[str, List[Tuple[float, int, int]]]:
    """Generate CC automation (reverb CC 91 and filter cutoff CC 74) for each section."""
    total_beats = max(
        (n.start + n.duration for notes in tracks.values() for n in notes),
        default=0.0,
    )

    for tname in list(tracks.keys()):
        if tname.startswith("_"):
            continue
        if tname not in cc_events:
            cc_events[tname] = []

        cc_events[tname] = [evt for evt in cc_events[tname] if evt[1] not in (74, 91)]

        for idx, (sec_start, sec_key) in enumerate(sections):
            profile = _resolve_section_profile(sec_key)
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

    return cc_events


def _thin_note_density(vel: int, beat_in_bar: float, role: Role, density: float) -> int:
    """Apply dynamic note damping according to section density."""
    if density >= 1.0:
        return vel
    if role == Role.PERC:
        if density <= 0.4 and abs(beat_in_bar - 0.0) > 0.05 and abs(beat_in_bar - 2.0) > 0.05:
            return int(vel * 0.2)
        if density <= 0.7 and abs(beat_in_bar * 2 - round(beat_in_bar * 2)) > 0.05:
            return int(vel * 0.4)
    elif role in (Role.LEAD, Role.PAD):
        if density <= 0.5 and abs(beat_in_bar - round(beat_in_bar)) > 0.05:
            return int(vel * 0.4)
    elif role == Role.BASS:
        if density <= 0.5 and abs(beat_in_bar - 0.0) > 0.05 and abs(beat_in_bar - 2.0) > 0.05:
            return int(vel * 0.3)
    return vel


def _apply_note_entropy(
    n: NoteInfo, entropy: float, vel: int
) -> tuple[int, float, float]:
    """Calculate entropy-based micro-jitter for velocity, duration, and onset."""
    if entropy <= 0.0:
        return vel, n.duration, n.start
    seed = int(float(n.start) * 100) + int(n.pitch)
    note_rng = random.Random(seed)
    vel_change = int(note_rng.uniform(-20 * entropy, 20 * entropy))
    new_vel = max(10, min(127, vel + vel_change))
    dur_change = note_rng.uniform(-0.15 * n.duration * entropy, 0.15 * n.duration * entropy)
    new_dur = max(0.05, n.duration + dur_change)
    start_change = note_rng.uniform(-0.04 * entropy, 0.04 * entropy)
    new_start = max(0.0, n.start + start_change)
    return new_vel, new_dur, new_start


def _apply_section_moods(
    tracks: Dict[str, List[NoteInfo]],
    sections: List[Tuple[float, Mood | str]],
    profiles: Dict[str, _TrackProfile],
) -> Dict[str, List[NoteInfo]]:
    """Apply rich per-section dynamics and velocity-based shaping based on SectionProfile."""
    if not sections:
        return tracks

    rng = random.Random(42)
    result = {}

    for tname, notes in tracks.items():
        if tname.startswith("_") or not notes:
            result[tname] = notes
            continue

        role = _detect_role_from_track_name(tname)
        new_notes: list[NoteInfo] = []

        for n in notes:
            section_key = sections[0][1]
            for sec_start, sec_mood_or_str in sections:
                if n.start >= sec_start:
                    section_key = sec_mood_or_str

            profile = _resolve_section_profile(section_key)

            if profile.active_roles is not None:
                has_any_match = any(
                    _detect_role_from_track_name(ot) in profile.active_roles
                    for ot in tracks.keys()
                )
                if has_any_match and role not in profile.active_roles:
                    continue

            center = 64
            offset = n.velocity - center
            vel = int(round(center + offset * profile.dynamics_range))
            vel = int(vel * profile.energy_target)

            if profile.velocity_drift > 0:
                vel += int(rng.uniform(-profile.velocity_drift, profile.velocity_drift))

            vel = _thin_note_density(vel, n.start % 4.0, role, profile.note_density)
            vel, duration, n_start = _apply_note_entropy(n, profile.entropy, vel)
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


def _compute_tension(chords: List) -> float:
    """Analyze chord list and return tension 0.0 (calm) to 1.0 (chaotic)."""
    if not chords:
        return 0.5

    from melodica.theory import Quality as Q

    high_tension = {
        Q.TONE_CLUSTER, Q.DIMINISHED, Q.AUGMENTED, Q.FULL_DIM7,
        Q.HALF_DIM7, Q.CLUSTER_MINOR_2, Q.CLUSTER_MAJOR_2,
        Q.CLUSTER_4TH, Q.OCTATONIC_CLUSTER,
    }
    mid_tension = {Q.MINOR, Q.HALF_DIM7, Q.LYDIAN_AUG}

    dissonant = 0
    total = len(chords)
    for ch in chords:
        if ch.quality in high_tension:
            dissonant += 2
        elif ch.quality in mid_tension:
            dissonant += 1

    return min(1.0, dissonant / total) if total > 0 else 0.5


def _tension_boost(tracks: Dict[str, List[NoteInfo]], factor: float) -> Dict[str, List[NoteInfo]]:
    """Apply velocity scaling based on harmonic tension."""
    result = {}
    for tname, notes in tracks.items():
        if tname.startswith("_") or not notes:
            result[tname] = notes
            continue
        result[tname] = [
            NoteInfo(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=max(10, min(127, int(n.velocity * factor))),
                articulation=n.articulation,
                expression=n.expression,
            )
            for n in notes
        ]
    return result


# ---------------------------------------------------------------------------
# Section Detection
# ---------------------------------------------------------------------------


def _iter_track_notes(tracks: Dict[str, Any]) -> Iterator[tuple[str, list[NoteInfo]]]:
    for tname, notes in tracks.items():
        if not tname.startswith("_") and hasattr(notes, "__iter__"):
            yield tname, notes


@dataclass(frozen=True)
class _ChunkClassificationContext:
    idx: int
    num_chunks: int
    peak_idx: int
    last_label: str


def _classify_chunk(
    ctx: _ChunkClassificationContext,
    c: dict,
    prev_c: dict | None,
) -> str:
    """Classify a chunk into a structural section label."""
    if ctx.idx == 0 and (c["track_density"] <= 2 or c["avg_velocity"] < 60):
        return "Intro"
    if ctx.idx == ctx.num_chunks - 1 and (c["track_density"] <= 2 or c["avg_velocity"] < 60):
        return "Fade"
    if ctx.idx == ctx.peak_idx:
        return "Climax"
    if prev_c and prev_c["energy"] > 0:
        if c["energy"] == 0 or c["energy"] < prev_c["energy"] * 0.4:
            return "Breakdown"
        if c["energy"] > prev_c["energy"] * 1.5:
            return "Climax" if ctx.idx >= ctx.num_chunks * 0.5 else "Variation"
    return "Variation" if ctx.last_label == "Theme" else "Theme"


def detect_sections_intelligently(
    tracks: Dict[str, List[NoteInfo]],
    bpm: float,
    time_signature: tuple[int, int] = (4, 4),
) -> List[Tuple[float, str]]:
    """Intelligently analyzes note densities, velocities, and active track counts."""
    total_beats = max(
        (n.start + n.duration for _, notes in _iter_track_notes(tracks) for n in notes),
        default=0.0,
    )
    if total_beats <= 0.0:
        return [(0.0, "Theme")]

    beats_per_bar = time_signature[0]
    chunk_size = 4.0 * beats_per_bar
    if total_beats < chunk_size * 2:
        chunk_size = 1.0 * beats_per_bar

    num_chunks = int(math.ceil(total_beats / chunk_size))
    if num_chunks == 0:
        return [(0.0, "Theme")]

    chunk_metrics = []
    for chunk_idx in range(num_chunks):
        c_start = chunk_idx * chunk_size
        c_end = min(total_beats, c_start + chunk_size)
        active_tracks: set[str] = set()
        total_vel = 0.0
        n_count = 0
        for tname, notes in _iter_track_notes(tracks):
            for n in notes:
                if c_start <= n.start < c_end:
                    active_tracks.add(tname)
                    total_vel += n.velocity
                    n_count += 1
        avg_vel = total_vel / n_count if n_count > 0 else 0.0
        density = len(active_tracks)
        chunk_metrics.append({
            "idx": chunk_idx, "start": c_start, "track_density": density,
            "avg_velocity": avg_vel, "energy": density * avg_vel,
        })

    max_energy = max(c["energy"] for c in chunk_metrics) if chunk_metrics else 0.0
    peak_idx = next((c["idx"] for c in chunk_metrics if c["energy"] == max_energy), -1) if max_energy > 0 else -1

    detected: list[tuple[float, str]] = []
    for idx, c in enumerate(chunk_metrics):
        prev_c = chunk_metrics[idx - 1] if idx > 0 else None
        last_label = detected[-1][1] if detected else "None"
        ctx = _ChunkClassificationContext(idx, num_chunks, peak_idx, last_label)
        label = _classify_chunk(ctx, c, prev_c)
        detected.append((c["start"], label))

    collapsed: list[tuple[float, str]] = []
    for start, label in detected:
        if not collapsed or collapsed[-1][1] != label:
            collapsed.append((start, label))

    return collapsed


# ---------------------------------------------------------------------------
# Melodic motif memory & narrative weaving
# ---------------------------------------------------------------------------


def clamp_to_scale(pitch: int, scale: Scale) -> int:
    """Clamps a MIDI pitch to the nearest scale degree."""
    degrees = scale.degrees()
    pc = pitch % 12
    nearest_pc = min(degrees, key=lambda d: min(abs(pc - d), 12 - abs(pc - d)))
    diff = nearest_pc - pc
    if diff > 6:
        diff -= 12
    elif diff < -6:
        diff += 12
    return max(0, min(127, int(round(pitch + diff))))


def _transform_motif_notes(
    motif_notes: list[NoteInfo],
    scale: Scale,
    transformation: str,
) -> list[NoteInfo]:
    """Apply pitch and rhythmic narrative transformations."""
    if not motif_notes:
        return []
    first_pitch = motif_notes[0].pitch
    total_dur = max(x.start + x.duration for x in motif_notes)

    transformed: list[NoteInfo] = []
    for n in motif_notes:
        pitch, start, dur, vel = n.pitch, n.start, n.duration, n.velocity
        if transformation == "inversion":
            pitch = first_pitch - (pitch - first_pitch)
        elif transformation == "stretched":
            start *= 2.0
            dur *= 2.0
        elif transformation == "fragmented":
            if int(round(start)) % 2 == 1:
                continue
            vel = int(vel * 0.7)
        elif transformation == "retrograde":
            start = total_dur - (start + dur)

        pitch = clamp_to_scale(pitch, scale)
        transformed.append(
            NoteInfo(
                pitch=pitch, start=start, duration=dur, velocity=vel,
                articulation=n.articulation,
                expression=dict(n.expression) if n.expression else {},
            )
        )
    return transformed


def _weave_narrative_motif(
    motif_notes: list[NoteInfo],
    scale: Scale,
    transformation: str,
    total_beats: float,
    track_index: int = 0,
    num_tracks: int = 1,
    opening_only: bool = False,
) -> list[NoteInfo]:
    """Declare the seed motif at a few strategic points rather than looping it."""
    transformed = _transform_motif_notes(motif_notes, scale, transformation)
    if not transformed:
        return []

    if opening_only:
        return [
            NoteInfo(
                pitch=n.pitch, start=round(n.start, 6), duration=n.duration,
                velocity=n.velocity, articulation=n.articulation,
                expression=dict(n.expression) if n.expression else {},
            )
            for n in transformed
            if n.start + n.duration <= total_beats + 0.5
        ]

    motif_len = max((x.start + x.duration for x in transformed), default=8.0)
    n_statements = max(2, min(4, int(total_beats // (motif_len * 3)))) if total_beats >= motif_len * 4 else 2

    base_anchors = [0.04, 0.6, 0.92]
    shift = (track_index % num_tracks) * 0.08
    anchors = [
        min(0.95, max(0.02, base_anchors[0])),
        min(0.95, max(0.02, base_anchors[1] + shift - 0.08)),
        min(0.95, max(0.02, base_anchors[2] - shift * 0.5)),
    ]
    if n_statements >= 4:
        anchors.append(0.3 + shift)
    anchors = sorted(set(round(a * total_beats, 6) for a in anchors))[:n_statements]

    placed: list[NoteInfo] = []
    for anchor in anchors:
        for n in transformed:
            note_start = anchor + n.start
            if note_start + n.duration <= total_beats + 0.5:
                placed.append(
                    NoteInfo(
                        pitch=n.pitch, start=round(note_start, 6), duration=n.duration,
                        velocity=n.velocity, articulation=n.articulation,
                        expression=dict(n.expression) if n.expression else {},
                    )
                )
    return placed


def _resolve_leaps(notes: list[NoteInfo]) -> list[NoteInfo]:
    """Soften melodic leap violations (ARR-12)."""
    if len(notes) < 3:
        return notes
    out = [
        NoteInfo(
            pitch=n.pitch, start=n.start, duration=n.duration, velocity=n.velocity,
            articulation=n.articulation,
            expression=dict(n.expression) if n.expression else {},
        )
        for n in notes
    ]
    for _ in range(5):
        changed = False
        for i in range(len(out) - 2):
            p0, p1, p2 = out[i].pitch, out[i + 1].pitch, out[i + 2].pitch
            leap = p1 - p0
            if abs(leap) >= 7 and leap * (p2 - p1) >= 0:
                new_p1 = p1 - 12 if leap > 0 else p1 + 12
                out[i + 1] = NoteInfo(
                    pitch=new_p1, start=out[i + 1].start, duration=out[i + 1].duration,
                    velocity=out[i + 1].velocity, articulation=out[i + 1].articulation,
                    expression=out[i + 1].expression,
                )
                changed = True
        if not changed:
            break
    return out


def _soft_blend(
    lead_notes: list[NoteInfo],
    motif_notes: list[NoteInfo],
    total_beats: float,
    window: float = 1.5,
) -> list[NoteInfo]:
    """Layer motif statements over generated lead, dropping conflicting notes."""
    if not motif_notes:
        return list(lead_notes)
    if not lead_notes:
        return list(motif_notes)

    import bisect
    motif_starts = sorted(n.start for n in motif_notes)
    kept_lead: list[NoteInfo] = []

    for n in lead_notes:
        idx = bisect.bisect_left(motif_starts, n.start)
        near = any(
            0 <= j < len(motif_starts) and abs(motif_starts[j] - n.start) <= window
            for j in (idx - 1, idx)
        )
        if not near:
            kept_lead.append(n)

    blended = kept_lead + list(motif_notes)
    blended.sort(key=lambda x: (x.start, -x.pitch))
    return _resolve_leaps(blended)


def generate_narrative_motif(
    motif_notes: list[NoteInfo],
    scale: Scale,
    transformation: str,
    offset_beats: float = 16.0,
    duration_beats: float = 64.0,
) -> list[NoteInfo]:
    """Apply narrative transformations to a motif and snap to scale with loops."""
    transformed = _transform_motif_notes(motif_notes, scale, transformation)
    transformed.sort(key=lambda x: x.start)
    if not transformed:
        return []

    motif_len = max((x.start + x.duration for x in transformed), default=8.0)
    padded_len = max(motif_len + 4.0, 16.0)
    motif_len = float(int((padded_len + 7) / 8) * 8)

    looped_notes: list[NoteInfo] = []
    current_time = offset_beats
    end_time = offset_beats + duration_beats

    while current_time < end_time:
        for n in transformed:
            note_start = current_time + n.start
            if note_start + n.duration <= end_time:
                looped_notes.append(
                    NoteInfo(
                        pitch=n.pitch, start=note_start, duration=n.duration, velocity=n.velocity,
                        articulation=n.articulation,
                        expression=dict(n.expression) if n.expression else {},
                    )
                )
        current_time += motif_len

    return looped_notes


# ---------------------------------------------------------------------------
# Stage functions for composition / planning
# ---------------------------------------------------------------------------


def _resolve_rhythm(rhythm: str | object) -> object:
    from melodica.rhythm.library import DYNAMIC_RHYTHM_REGISTRY, RHYTHM_LIBRARY, get_rhythm
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


def _quantize_onsets(
    notes: list[NoteInfo], snap_points: list[float], entry: float, max_snap: float = 0.6
) -> list[NoteInfo]:
    import bisect
    out: list[NoteInfo] = []
    for n in notes:
        local = n.start - entry
        idx = bisect.bisect_left(snap_points, local)
        candidates = []
        if idx > 0:
            candidates.append(snap_points[idx - 1])
        if idx < len(snap_points):
            candidates.append(snap_points[idx])
        nearest = min(candidates, key=lambda p: abs(p - local))
        new_start = round(nearest + entry, 6) if abs(nearest - local) <= max_snap else n.start
        out.append(
            NoteInfo(
                pitch=n.pitch, start=new_start, duration=n.duration, velocity=n.velocity,
                articulation=n.articulation,
                expression=dict(n.expression) if n.expression else {},
            )
        )
    return out


def _stage_rhythm(kw: dict) -> dict:
    rhythm = kw.get("rhythm")
    if rhythm is None:
        raise ValueError("rhythm is required for album production.")
    gen = _resolve_rhythm(rhythm)
    rhythm_roles = {Role.PERC, Role.BASS, Role.LEAD}

    result = {}
    for tname, notes in kw["tracks"].items():
        if tname.startswith("_") or not notes:
            result[tname] = notes
            continue
        role = _detect_role_from_track_name(tname)
        if role not in rhythm_roles:
            result[tname] = notes
            continue
        entry = min(n.start for n in notes)
        span = max(0.5, max(n.start + n.duration for n in notes) - entry)
        events = gen.generate(span)
        snap_points = sorted({round(e.onset, 4) for e in events})
        result[tname] = _quantize_onsets(notes, snap_points, entry) if snap_points else notes

    kw["tracks"] = result
    return kw


def _stage_phrase_dynamics(kw: dict) -> dict:
    from melodica.composer.phrase_dynamics import apply_phrase_dynamics_to_pipeline
    kw["tracks"] = apply_phrase_dynamics_to_pipeline(kw["tracks"])
    return kw


def _stage_articulations(kw: dict) -> dict:
    from melodica.composer.articulations import ArticulationEngine
    engine = ArticulationEngine()
    total_dur = max(
        (n.start + n.duration for notes in kw["tracks"].values() for n in notes),
        default=64.0,
    )
    result = {}
    for tname, notes in kw["tracks"].items():
        if tname.startswith("_") or not notes:
            result[tname] = notes
            continue
        result[tname] = engine.apply(notes, instrument=tname.lower(), total_beats=total_dur)
    kw["tracks"] = result
    return kw


def _stage_harmonic_verify(kw: dict) -> dict:
    from melodica.composer.harmonic_verifier import VerifierConfig, verify_and_fix
    from melodica.form_validator import _is_percussion
    config = VerifierConfig(
        dissonance_tolerance=0.6, fix_transpose=True, fix_remove=False,
        fix_velocity=True, fix_shorten=True, apply_shading=True,
    )
    to_verify = {}
    perc = {}
    for tname, notes in kw["tracks"].items():
        if _is_percussion(tname):
            perc[tname] = notes
        else:
            to_verify[tname] = notes
    fixed, report = verify_and_fix(to_verify, config)
    fixed.update(perc)
    kw["tracks"] = fixed
    kw["_harmonic_report"] = report
    return kw


def _stage_transitions(kw: dict) -> dict:
    section_breaks = kw.get("section_breaks") or []
    if not section_breaks:
        return kw
    from melodica.composer.transition_coordinator import TransitionCoordinator
    cc_events: dict = dict(kw.get("cc_events") or {})
    non_bass = [t for t in kw["tracks"] if "bass" not in t.lower()]
    for beat, _ in section_breaks:
        TransitionCoordinator.apply_sweeps(
            kw["tracks"], cc_events, target_tracks=non_bass,
            cc_num=11, start_val=100, end_val=60,
            start_beat=max(0.0, beat - 2.0), end_beat=beat,
            curve_type="exponential", steps=12,
        )
        TransitionCoordinator.apply_sweeps(
            kw["tracks"], cc_events, target_tracks=non_bass,
            cc_num=11, start_val=60, end_val=100,
            start_beat=beat, end_beat=beat + 2.0,
            curve_type="exponential", steps=12,
        )
    kw["cc_events"] = cc_events
    return kw


def _stage_texture(kw: dict) -> dict:
    chords = kw.get("chords")
    if not chords:
        return kw
    from melodica.composer.tension_curve import TensionCurve
    from melodica.composer.texture_controller import TextureController
    total_dur = max(
        (n.start + n.duration for notes in kw["tracks"].values() for n in notes),
        default=64.0,
    )
    tc = TensionCurve(
        total_beats=total_dur, curve_type="classical",
        peak_position=0.65, peak_intensity=0.9, resolution_length=0.25,
    )
    ctrl = TextureController(tension_curve=tc)
    kw["tracks"] = ctrl.apply_texture(kw["tracks"], total_dur)
    return kw


def _stage_non_chord_tones(kw: dict) -> dict:
    chords, key = kw.get("chords"), kw.get("key")
    if not chords or not key:
        return kw
    from melodica.composer.non_chord_tones import NonChordToneGenerator
    gen = NonChordToneGenerator(0.18, 0.08, 0.06, 0.04)
    result = {}
    for tname, notes in kw["tracks"].items():
        prof = kw.get("_profiles", {}).get(tname)
        if prof and prof.role in (Role.LEAD, Role.STRINGS) and notes:
            result[tname] = gen.add_non_chord_tones(notes, chords, key)
        else:
            result[tname] = notes
    kw["tracks"] = result
    return kw


def _stage_leap_resolve(kw: dict) -> dict:
    result = {}
    for tname, notes in kw["tracks"].items():
        prof = kw.get("_profiles", {}).get(tname)
        if prof and prof.role in (Role.LEAD, Role.STRINGS) and notes and len(notes) >= 3:
            result[tname] = _resolve_leaps(notes)
        else:
            result[tname] = notes
    kw["tracks"] = result
    return kw


def _stage_breathing_room(kw: dict, max_block: float = 28.0, rest_gap: float = 1.6) -> dict:
    result = {}
    for tname, notes in kw["tracks"].items():
        prof = kw.get("_profiles", {}).get(tname)
        if not (prof and prof.role in (Role.LEAD, Role.STRINGS) and len(notes) >= 6):
            result[tname] = notes
            continue

        ordered = sorted(notes, key=lambda n: float(n.start))
        keep = [True] * len(ordered)
        ends = [float(n.start) + float(n.duration) for n in ordered]
        last_rest_at = float(ordered[0].start) if ordered else 0.0

        for i in range(1, len(ordered)):
            onset = float(ordered[i].start)
            silent_since = max((ends[j] for j in range(i) if keep[j]), default=0.0)
            if onset - silent_since >= rest_gap:
                last_rest_at = onset
                continue
            if onset - last_rest_at >= 20.0:
                for j in range(i, len(ordered)):
                    if float(ordered[j].start) > onset + rest_gap:
                        break
                    if ends[j] > onset:
                        keep[j] = False
                last_rest_at = onset + rest_gap

        result[tname] = [n for n, k in zip(notes, keep) if k] if not all(keep) else notes
    kw["tracks"] = result
    return kw


def _stage_diagnostics(kw: dict) -> dict:
    if not kw.get("verbose"):
        return kw
    try:
        from melodica.composer.diagnostics import diagnose_tracks
        diagnose_tracks(kw["tracks"], bpm=kw.get("bpm", 120.0))
    except Exception:
        pass
    return kw


def _stage_sections(kw: dict) -> dict:
    sections = kw.get("sections")
    tracks = kw.get("tracks")
    if sections and tracks:
        kw["tracks"] = _apply_section_moods(tracks, sections, kw["_profiles"])
        kw["cc_events"] = _build_section_cc_automation(
            kw["tracks"], sections, kw.get("cc_events", {})
        )
    return kw


def _stage_tension(kw: dict) -> dict:
    chords = kw.get("chords")
    if chords:
        tension = _compute_tension(chords)
        kw["_tension"] = tension
        if tension > 0.7:
            kw["tracks"] = _tension_boost(kw["tracks"], 1.10)
        elif tension < 0.3:
            kw["tracks"] = _tension_boost(kw["tracks"], 0.92)
    return kw


# ---------------------------------------------------------------------------
# Album orchestration & compilation
# ---------------------------------------------------------------------------


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
    """Produce multiple tracks as an album."""
    from melodica.composer.album_pipeline import produce_track

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if rhythm is None:
        raise ValueError("rhythm is required for produce_album.")
    if key is None:
        raise ValueError("key is required for produce_album.")
    if chords is None:
        raise ValueError("chords is required for produce_album.")
    if time_signature is None:
        raise ValueError("time_signature is required for produce_album, e.g. (4, 4).")

    print(f"{'='*60}\n   {album_name}\n{'='*60}")
    reports = []
    for i, (tracks, bpm, instruments, filename, mood) in enumerate(tracks_list, 1):
        print(f"\n--- {i:02d}. {filename} ({mood.value}) ---")
        rep = produce_track(
            tracks=tracks, bpm=bpm, instruments=instruments, path=out / filename,
            mood=mood, key=key, rhythm=rhythm, chords=chords, genre=genre,
            time_signature=time_signature,
        )
        reports.append(rep)

    print(f"\n{'='*60}\n   {album_name} — COMPLETE.\n   Files in: {out}\n{'='*60}")
    return reports


@dataclass(frozen=True)
class _BridgeConfig:
    overlap_start: float
    overlap_beats: float
    strategy: str = "direct"
    instrument: int = 89


def _build_modulation_bridge(
    prev_key: Scale,
    this_key: Scale,
    cfg_or_start: _BridgeConfig | float,
    overlap_beats: float = 16.0,
    strategy: str = "direct",
    instrument: int = 89,
) -> tuple[list[NoteInfo], list[tuple[float, int, int]]]:
    """Create transition pad and automation events between differing keys."""
    from melodica.composer.automation import AutomationCurve
    from melodica.theory import CHORD_TEMPLATES
    from melodica.theory.modulation import ModulationEngine

    if isinstance(cfg_or_start, _BridgeConfig):
        cfg = cfg_or_start
    else:
        cfg = _BridgeConfig(
            overlap_start=cfg_or_start,
            overlap_beats=overlap_beats,
            strategy=strategy,
            instrument=instrument,
        )

    bridge_chords = ModulationEngine.generate_modulation_bridge(
        from_scale=prev_key, to_scale=this_key, length_beats=cfg.overlap_beats,
        strategy=cfg.strategy, start_beat=cfg.overlap_start,
    )
    bridge_notes: list[NoteInfo] = []
    for chord in bridge_chords:
        template = CHORD_TEMPLATES.get(chord.quality, [0, 4, 7])
        base_midi = 48 + chord.root
        for interval in template:
            p = base_midi + interval
            if 0 <= p <= 127:
                bridge_notes.append(
                    NoteInfo(pitch=p, start=chord.start, duration=chord.duration * 0.95, velocity=55)
                )

    ol_s = cfg.overlap_start
    ol_b = cfg.overlap_beats
    fade_in = AutomationCurve.linear(7, 0, 80, ol_s, ol_s + ol_b * 0.5, steps=5)
    fade_out = AutomationCurve.linear(7, 80, 0, ol_s + ol_b * 0.5, ol_s + ol_b, steps=5)
    sweep = AutomationCurve.exponential(74, 35, 95, ol_s, ol_s + ol_b, exponent=1.8, steps=8)
    return bridge_notes, fade_in + fade_out + sweep


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
    """Stitches multiple tracks into a single continuous arrangement with crossfades."""
    from melodica.composer.album_pipeline import produce_track
    from melodica.composer.automation import AutomationCurve

    if not tracks_metadata:
        raise ValueError("tracks_metadata cannot be empty.")
    if rhythm is None:
        raise ValueError("rhythm is required for compile_continuous_album.")
    if chords is None:
        raise ValueError("chords is required for compile_continuous_album.")
    if time_signature is None:
        raise ValueError("time_signature is required for compile_continuous_album.")

    for idx, meta in enumerate(tracks_metadata):
        if not meta.get("sections"):
            meta["sections"] = detect_sections_intelligently(
                meta.get("tracks", {}), meta.get("bpm", 120.0), time_signature
            )
        sections = meta["sections"]
        last_beat = -1.0
        for sec_idx, section in enumerate(sections):
            if not isinstance(section, (tuple, list)) or len(section) < 2:
                raise ValueError(f"Track {idx} section {sec_idx} must be a tuple/list of (start_beat, mood_or_str).")
            beat, _ = section
            if beat < last_beat:
                raise ValueError(
                    f"Track {idx} sections are not in chronological order: "
                    f"section at index {sec_idx} starts at beat {beat}, which is less than preceding beat {last_beat}."
                )
            last_beat = beat

    combined_tracks: Dict[str, List[NoteInfo]] = {}
    combined_instruments: Dict[str, int] = {}
    combined_cc: Dict[str, List[Tuple[float, int, int]]] = {}
    combined_tempo: List[Tuple[float, float]] = []
    combined_sections: List[Tuple[float, Mood]] = []

    cur_start = 0.0
    first_bpm = tracks_metadata[0].get("bpm", 120.0)
    first_key = tracks_metadata[0].get("key", None)

    for i, meta in enumerate(tracks_metadata):
        track_dict = {k: v for k, v in meta.get("tracks", {}).items() if not k.startswith("_")}
        bpm = meta.get("bpm", 120.0)
        combined_instruments.update(meta.get("instruments", {}))

        for beat, sec_mood in meta.get("sections", []):
            combined_sections.append((beat + cur_start, sec_mood))

        track_dur = max(
            (n.start + n.duration for notes in track_dict.values() for n in notes),
            default=0.0,
        )

        for name, notes in track_dict.items():
            shifted = [copy.deepcopy(n) for n in notes]
            for n in shifted:
                n.shift_time(cur_start)
            combined_tracks.setdefault(name, []).extend(shifted)

        for name, events in meta.get("cc_events", {}).items():
            combined_cc.setdefault(name, []).extend((ev[0] + cur_start, ev[1], ev[2]) for ev in events)

        if i > 0 and overlap_beats > 0.0:
            ol_start, ol_end = cur_start, cur_start + overlap_beats
            for name in track_dict.keys():
                combined_cc.setdefault(name, []).extend(
                    AutomationCurve.exponential(7, 0, 100, ol_start, ol_end, exponent=1.5, steps=10)
                )
            prev_meta = tracks_metadata[i - 1]
            for name in prev_meta.get("tracks", {}).keys():
                combined_cc.setdefault(name, []).extend(
                    AutomationCurve.exponential(7, 100, 0, ol_start, ol_end, exponent=1.5, steps=10)
                )

            prev_key, this_key = prev_meta.get("key"), meta.get("key")
            if modulation_strategy and prev_key and this_key and (prev_key.root != this_key.root or prev_key.mode != this_key.mode):
                b_notes, b_cc = _build_modulation_bridge(
                    prev_key,
                    this_key,
                    _BridgeConfig(ol_start, overlap_beats, modulation_strategy, transition_instrument),
                )
                combined_tracks.setdefault("transition_pad", []).extend(b_notes)
                combined_instruments["transition_pad"] = transition_instrument
                combined_cc.setdefault("transition_pad", []).extend(b_cc)

        if meta.get("tempo_events"):
            combined_tempo.extend((ev[0] + cur_start, ev[1]) for ev in meta["tempo_events"])
        else:
            combined_tempo.append((cur_start, bpm))

        next_start = cur_start + track_dur - (overlap_beats if i < len(tracks_metadata) - 1 else 0.0)
        cur_start = max(0.0, next_start)

    for notes in combined_tracks.values():
        notes.sort(key=lambda n: n.start)
    for events in combined_cc.values():
        events.sort(key=lambda e: e[0])
    combined_tempo.sort(key=lambda e: e[0])
    combined_sections.sort(key=lambda e: e[0])

    return produce_track(
        tracks=combined_tracks, bpm=first_bpm, instruments=combined_instruments,
        path=output_path, mood=mood, key=first_key, cc_events=combined_cc,
        tempo_events=combined_tempo, sections=combined_sections, rhythm=rhythm,
        chords=chords, genre=genre, time_signature=time_signature,
    )


def _fit_notes_to_range(notes: list[NoteInfo], lo: int, hi: int) -> None:
    for n in notes:
        while n.pitch < lo - 3:
            n.pitch = min(127, n.pitch + 12)
        while n.pitch > hi + 3:
            n.pitch = max(0, n.pitch - 12)


def _splice_lead_motif(
    lead_existing: list[NoteInfo],
    opening_motif: list[NoteInfo],
) -> list[NoteInfo]:
    if not lead_existing:
        return opening_motif
    if not opening_motif:
        return lead_existing

    lo = min(n.pitch for n in lead_existing)
    hi = max(n.pitch for n in lead_existing)
    _fit_notes_to_range(opening_motif, lo, hi)
    motif_end = max(n.start + n.duration for n in opening_motif)
    tail = [n for n in lead_existing if n.start >= motif_end - 0.01]
    return opening_motif + tail


@dataclass(frozen=True)
class _LeadMotifContext:
    track_index: int
    configs: list[TrackConfig]
    key: Scale
    transform: str
    total_beats: float


# ---------------------------------------------------------------------------
# AlbumNarrative Engine
# ---------------------------------------------------------------------------


@dataclass
class AlbumNarrative:
    """Core engine for AI-directed long-form listening experiences."""
    output_dir: Path | str
    seed_motif: list[NoteInfo]
    harmonic_journey: list[Scale]
    tempos: list[float]
    track_configs: list[list[TrackConfig]]
    transformations: list[str]
    sections_list: list[list[tuple[float, str]]]
    instruments_maps: list[dict[str, int]]
    moods: list[Mood]
    names: list[str]
    rhythm: str | object
    time_signature: tuple[int, int]
    genre: str = DEFAULT_GENRE
    strict_validation: bool = True
    disable_texture: bool = False

    def _weave_lead_motif(
        self,
        ctx: _LeadMotifContext,
        tracks_dict: dict[str, list[NoteInfo]],
    ) -> None:
        lead_track_name = next(
            (c.name for c in ctx.configs if any(x in c.name for x in ("lead", "solo", "pluck", "melody"))),
            None,
        )
        if not lead_track_name:
            return

        opening_motif = _weave_narrative_motif(
            self.seed_motif, scale=ctx.key, transformation=ctx.transform,
            total_beats=ctx.total_beats, track_index=ctx.track_index,
            num_tracks=len(self.harmonic_journey), opening_only=True,
        )
        target_cfg = next((c for c in ctx.configs if c.name == lead_track_name), None)
        if target_cfg and target_cfg.octave_shift:
            for n in opening_motif:
                n.pitch = max(0, min(127, n.pitch + target_cfg.octave_shift * 12))

        lead_existing = list(tracks_dict.get(lead_track_name, []))
        tracks_dict[lead_track_name] = _splice_lead_motif(lead_existing, opening_motif)

    def generate(self) -> dict:
        """Generates all tracks and compiles them into a single continuous album."""
        import shutil
        from melodica.composer.album_pipeline import DEFAULT_PIPELINE, produce_track
        from melodica.idea_tool import IdeaPart, IdeaTool, IdeaToolConfig

        out_path = Path(self.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        tracks_metadata = []
        per_track_chords = []

        for i in range(len(self.harmonic_journey)):
            key, tempo = self.harmonic_journey[i], self.tempos[i]
            configs, transform = self.track_configs[i], self.transformations[i]
            sections = self.sections_list[i]
            instr_map, mood, name = self.instruments_maps[i], self.moods[i], self.names[i]

            print(f"  Generating narrative track {i+1}: {name} [{key.mode.value} — {tempo} BPM] with motif: {transform}")
            total_beats = max(sec[0] for sec in sections) + 16.0
            dur_bars = int(total_beats / 4)

            parts = [IdeaPart(name=f"Part_{i}", bars=dur_bars, scale=key, tempo=tempo, progression_type="coupled_hmm")]
            config = IdeaToolConfig(parts=parts, tracks=configs, scale=key, tempo=tempo, use_tension_curve=True)
            tool = IdeaTool(config)
            result = tool.generate()
            tracks_dict = {k: v for k, v in result.items() if not k.startswith("_")}
            part_chords = result.get("_chords") or tool.get_chords()
            per_track_chords.append(part_chords)

            ctx = _LeadMotifContext(i, configs, key, transform, total_beats)
            self._weave_lead_motif(ctx, tracks_dict)

            pipeline = [s for s in DEFAULT_PIPELINE if s.name != "texture"] if self.disable_texture else None
            meta = produce_track(
                tracks_dict, bpm=tempo, instruments=instr_map, path=out_path / f"temp_{i}.mid",
                mood=mood, key=key, verbose=False, sections=sections, return_state=True,
                strict_validation=self.strict_validation, rhythm=self.rhythm, chords=part_chords,
                genre=self.genre, time_signature=self.time_signature, pipeline=pipeline,
            )
            tracks_metadata.append(meta)

        compiled_result = compile_continuous_album(
            tracks_metadata=tracks_metadata, output_path=out_path / "continuous_album.mid",
            overlap_beats=16.0, mood=Mood.CINEMATIC, modulation_strategy="pivot",
            rhythm=self.rhythm, chords=per_track_chords[0] if per_track_chords else [],
            genre=self.genre, time_signature=self.time_signature,
        )

        for i, name in enumerate(self.names):
            clean_filename = f"{i+1:02d}_{name.replace(' ', '_')}.mid"
            shutil.move(str(out_path / f"temp_{i}.mid"), str(out_path / clean_filename))

        return compiled_result
