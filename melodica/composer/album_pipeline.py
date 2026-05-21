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
from melodica.composer.psychoacoustic import psycho_verify, PsychoConfig


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
    dynamics_range: float      # 0.0=compressed, 1.0=wide dynamics
    psycho_aggressive: bool    # remove masked notes vs just reduce velocity
    bass_boost: float          # extra gain for sub-bass tracks
    brightness_ceiling: int    # max velocity for high register


_MOOD_PROFILES = {
    Mood.AMBIENT:       _MoodProfile(-20.0, 0.8, False, 0.95, 110),
    Mood.INTIMATE:      _MoodProfile(-18.0, 0.7, False, 0.90, 112),
    Mood.CINEMATIC:     _MoodProfile(-14.0, 0.5, True,  1.10, 120),
    Mood.AGGRESSIVE:    _MoodProfile(-12.0, 0.3, True,  1.15, 125),
    Mood.CHAMBER:       _MoodProfile(-16.0, 0.6, False, 1.00, 115),
    Mood.EXPERIMENTAL:  _MoodProfile(-15.0, 0.9, False, 1.00, 127),
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
    entry_beat: float = 0.0   # [FIX 2] when this track first plays
    note_count: int = 0


_ROLE_HEURISTICS = {
    "bass":   (lambda p, d: p < 48),
    "lead":   (lambda p, d: p > 60 and d > 0.15),
    "pad":    (lambda p, d: d < 0.1),
    "perc":   (lambda p, d: d > 0.3 and p > 70),
    "strings":(lambda p, d: 40 < p < 75 and 0.05 < d < 0.3),
    "choir":  (lambda p, d: 50 < p < 70 and d < 0.15),
    "fx":     (lambda p, d: p > 80 and d < 0.05),
}

_NAME_HINTS: Dict[str, Role] = {
    "bass": Role.BASS, "kick": Role.PERC, "snare": Role.PERC,
    "hihat": Role.PERC, "hat": Role.PERC, "perc": Role.PERC,
    "drum": Role.PERC, "pad": Role.PAD, "choir": Role.CHOIR,
    "voice": Role.CHOIR, "string": Role.STRINGS, "cello": Role.STRINGS,
    "viola": Role.STRINGS, "violin": Role.STRINGS,
    "lead": Role.LEAD, "solo": Role.LEAD, "flute": Role.LEAD,
    "clarinet": Role.LEAD, "harp": Role.STRINGS, "organ": Role.STRINGS,
    "guitar": Role.LEAD, "fx": Role.FX, "glass": Role.FX,
    "banjo": Role.LEAD, "koto": Role.LEAD, "bowl": Role.FX,
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
    rms = math.sqrt(sum(n.velocity ** 2 for n in notes) / len(notes))
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

    return _TrackProfile(avg_pitch, max_p - min_p, density, rms, role_final,
                         entry_beat=entry, note_count=len(notes))


# ---------------------------------------------------------------------------
# Auto-mixing: role-based gain, density-adaptive, entry/exit, register shaping
# ---------------------------------------------------------------------------

_ROLE_GAINS: Dict[Role, float] = {
    Role.LEAD:    0.85,
    Role.BASS:    0.55,
    Role.PAD:     0.35,
    Role.PERC:    0.70,
    Role.STRINGS: 0.65,
    Role.CHOIR:   0.45,
    Role.FX:      0.50,
}

_ROLE_PAN: Dict[Role, float] = {
    Role.LEAD:    0.0,
    Role.BASS:    0.0,
    Role.PAD:    -0.30,
    Role.PERC:    0.15,
    Role.STRINGS: 0.20,
    Role.CHOIR:  -0.10,
    Role.FX:      0.30,
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


def _auto_mix(tracks: Dict[str, List[NoteInfo]], mood_profile: _MoodProfile
              ) -> Tuple[Dict[str, List[NoteInfo]], Dict[str, _TrackProfile], Dict[str, float]]:
    """Analyze tracks, assign gains by role + density, apply register shaping."""
    # Compute total duration from all tracks
    total_dur = 0.0
    for notes in tracks.values():
        if notes and not tracks.keys():
            continue
        for n in notes:
            total_dur = max(total_dur, n.start + n.duration)

    profiles = {}
    for name, notes in tracks.items():
        if not notes or name.startswith("_"):
            continue
        profiles[name] = _analyze_track(name, notes, total_dur)

    # Build gain map: role default × density × register tweak × mood bass boost
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

    # [FIX 4 + FIX 5] Register overlap: same-register non-perc → pan apart + duck
    names = [n for n in profiles if profiles[n].role not in (Role.PERC, Role.FX)]
    dialogue_pairs: List[Tuple[str, str]] = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = profiles[names[i]], profiles[names[j]]
            if abs(a.avg_pitch - b.avg_pitch) < 8:
                quieter = names[i] if a.rms_velocity < b.rms_velocity else names[j]
                gains[quieter] *= 0.75
                dialogue_pairs.append((names[i], names[j]))

    # [FIX 5] Auto-pan dialogue pairs hard L/R
    pan_overrides: Dict[str, float] = {}
    for ai, (a_name, b_name) in enumerate(dialogue_pairs):
        spread = 0.6 + min(0.35, ai * 0.05)  # vary spread to avoid stacking
        pan_overrides[a_name] = -spread
        pan_overrides[b_name] = spread

    # [FIX 1] Single MixingDesk pass — was erroneously called twice (double compression bug)
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update(gains)
    mixed = desk.apply_mixing(tracks, [], 120)

    return mixed, profiles, pan_overrides


# ---------------------------------------------------------------------------
# [FIX 1] Sidechain ducking — bass/pad duck when perc hits
# ---------------------------------------------------------------------------

def _sidechain_duck(tracks: Dict[str, List[NoteInfo]],
                    profiles: Dict[str, _TrackProfile],
                    duck_amount: float = 0.45,
                    window: float = 0.15) -> Dict[str, List[NoteInfo]]:
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
                new_notes.append(NoteInfo(
                    pitch=n.pitch, start=n.start, duration=n.duration,
                    velocity=new_vel, articulation=n.articulation,
                    expression=n.expression,
                ))
            else:
                new_notes.append(n)
        result[tname] = new_notes

    return result


# ---------------------------------------------------------------------------
# [FIX 7] Swing / humanization — timing + velocity jitter for dense tracks
# ---------------------------------------------------------------------------

def _apply_humanization(tracks: Dict[str, List[NoteInfo]],
                        profiles: Dict[str, _TrackProfile],
                        swing_amount: float = 0.02,
                        vel_jitter: int = 4) -> Dict[str, List[NoteInfo]]:
    """Add density-adaptive timing and velocity variation to tracks.

    [FIX 3] At high note density the timing jitter is scaled DOWN to prevent
    notes from overtaking each other, while velocity jitter is scaled UP to
    preserve groove expressiveness through dynamics instead of timing.

    density < 0.5  → full timing jitter, minimal velocity jitter
    density 0.5–2  → linearly interpolated
    density > 2    → minimal timing jitter (1/10th), maximum velocity jitter
    """
    result = {}
    for tname, notes in tracks.items():
        if tname.startswith("_"):
            result[tname] = notes
            continue

        prof = profiles.get(tname)
        if not prof or prof.role in (Role.PAD, Role.FX):
            result[tname] = notes
            continue

        # Only humanize tracks with density > 0.3 or role is LEAD/STRINGS
        if prof.density < 0.3 and prof.role not in (Role.LEAD, Role.STRINGS):
            result[tname] = notes
            continue

        # [FIX 3] Density-adaptive scaling
        # At density >= 2.0 timing jitter drops to 10%; velocity jitter rises to 2.5×
        density_factor = min(1.0, prof.density / 2.0)  # 0.0 at sparse, 1.0 at dense
        t_scale = 1.0 - 0.9 * density_factor           # 1.0 → 0.10
        v_scale = 1.0 + 1.5 * density_factor           # 1.0 → 2.50
        effective_t = swing_amount * t_scale
        effective_v = max(1, int(vel_jitter * v_scale))

        rng = random.Random(hash(tname) & 0xFFFFFFFF)
        new_notes = []
        for n in notes:
            t_jitter = rng.uniform(-effective_t, effective_t)
            v_jit = rng.randint(-effective_v, effective_v)
            new_notes.append(NoteInfo(
                pitch=n.pitch,
                start=max(0.0, n.start + t_jitter),
                duration=n.duration,
                velocity=max(10, min(127, n.velocity + v_jit)),
                articulation=n.articulation,
                expression=n.expression,
            ))
        result[tname] = new_notes

    return result


# ---------------------------------------------------------------------------
# [FIX 2] Instrument entry/exit — CC11 fade-in for late-entering tracks
# ---------------------------------------------------------------------------

def _generate_entry_fades(tracks: Dict[str, List[NoteInfo]],
                          profiles: Dict[str, _TrackProfile],
                          total_dur: float,
                          fade_beats: float = 8.0) -> Dict[str, List[Tuple[float, int, int]]]:
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
    Role.LEAD:    50,
    Role.BASS:    20,
    Role.PAD:     70,
    Role.PERC:    25,
    Role.STRINGS: 55,
    Role.CHOIR:   65,
    Role.FX:      40,
}


def _generate_reverb_sends(tracks: Dict[str, List[NoteInfo]],
                           profiles: Dict[str, _TrackProfile],
                           mood_profile: _MoodProfile) -> Dict[str, List[Tuple[float, int, int]]]:
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

def _generate_delay_sends(tracks: Dict[str, List[NoteInfo]],
                          profiles: Dict[str, _TrackProfile]) -> Dict[str, List[Tuple[float, int, int]]]:
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

    HIGH_TENSION = {Q.TONE_CLUSTER, Q.DIMINISHED, Q.AUGMENTED,
                    Q.FULL_DIM7, Q.HALF_DIM7,
                    Q.CLUSTER_MINOR_2, Q.CLUSTER_MAJOR_2,
                    Q.CLUSTER_4TH, Q.OCTATONIC_CLUSTER}
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
                Role.LEAD: 0, Role.STRINGS: 1, Role.PERC: 2,
                Role.BASS: 3, Role.CHOIR: 4, Role.PAD: 5, Role.FX: 6,
            }
            active.sort(
                key=lambda x: (
                    -x[1].velocity,
                    role_priority.get(profiles.get(x[0], _TrackProfile(60, 0, 0, 0, Role.PAD)).role, 5),
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


def _sparse_safeguard(tracks: Dict[str, List[NoteInfo]],
                      profiles: Dict[str, _TrackProfile]) -> Dict[str, List[NoteInfo]]:
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
                    clamped.append(NoteInfo(
                        pitch=n.pitch, start=n.start, duration=n.duration,
                        velocity=90, articulation=n.articulation, expression=n.expression,
                    ))
                else:
                    clamped.append(n)
            result[tname] = clamped
        else:
            result[tname] = notes

    return result


# ---------------------------------------------------------------------------
# Auto-mastering with mood-aware settings
# ---------------------------------------------------------------------------

def _auto_master(tracks: Dict[str, List[NoteInfo]], profiles: Dict[str, _TrackProfile],
                 mood_profile: _MoodProfile,
                 pan_overrides: Dict[str, float] | None = None
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
                        pitch=n.pitch, start=n.start, duration=n.duration,
                        velocity=mood_profile.brightness_ceiling,
                        articulation=n.articulation, expression=n.expression,
                    )

    return mastered, cc_events


# ---------------------------------------------------------------------------
# Dynamics shaping — mood-aware velocity range compression/expansion
# ---------------------------------------------------------------------------

_DYNAMICS_WINDOW_BEATS = 32.0  # sliding window size for local normalization


def _shape_dynamics(tracks: Dict[str, List[NoteInfo]], mood_profile: _MoodProfile
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
        t_end   = notes[-1].start + notes[-1].duration
        span    = t_end - t_start

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
                shaped.append(NoteInfo(
                    pitch=n.pitch, start=n.start, duration=n.duration,
                    velocity=new_vel, articulation=n.articulation, expression=n.expression,
                ))
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
                shaped.append(NoteInfo(
                    pitch=n.pitch, start=n.start, duration=n.duration,
                    velocity=new_vel, articulation=n.articulation, expression=n.expression,
                ))
            result[name] = shaped
    return result


# ---------------------------------------------------------------------------
# Merge CC events from multiple sources
# ---------------------------------------------------------------------------

def _merge_cc_events(*sources: Dict[str, List[Tuple[float, int, int]]]
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
    sections: List[Tuple[float, Mood]] | None = None,
    chords: List | None = None,
    cc_events: Dict[str, List[Tuple[float, int, int]]] | None = None,
    tempo_events: List[Tuple[float, float]] | None = None,
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
    sections : list of (beat, Mood), optional
        [FIX 3] Section-aware mood changes. Each tuple is (start_beat, mood).
        Allows mood to change mid-track.
    chords : list of ChordLabel, optional
        [FIX 11] Chord progression for harmonic tension analysis.

    Returns
    -------
    dict with keys: profiles, report
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mood_profile = _MOOD_PROFILES[mood]

    # 1. Analyze + auto-mix
    mixed, profiles, pan_overrides = _auto_mix(tracks, mood_profile)

    # 2. Dynamics shaping
    shaped = _shape_dynamics(mixed, mood_profile)

    # 3. [FIX 1] Sidechain ducking
    shaped = _sidechain_duck(shaped, profiles)

    # 4. [FIX 7] Humanization / swing
    shaped = _apply_humanization(shaped, profiles)

    # 5. [FIX 3] Section-aware mood: apply per-section dynamics shaping
    if sections:
        shaped = _apply_section_moods(shaped, sections, profiles)

    # 6. [FIX 11] Harmonic tension: adjust dynamics based on chord analysis
    if chords:
        tension = _compute_tension(chords)
        if tension > 0.7:
            # High tension — boost velocity by 10%
            shaped = _tension_boost(shaped, 1.10)
        elif tension < 0.3:
            # Low tension — gentle reduction
            shaped = _tension_boost(shaped, 0.92)

    # 7. [FIX 5] Polyphony limiter — drop quietest notes beyond 16 voices
    shaped = _polyphony_limit(shaped, profiles, max_voices=16)

    # 8. Psychoacoustic verification (bpm-aware for blur threshold)
    if psycho_verify_enabled:
        config = PsychoConfig(aggressive_fix=mood_profile.psycho_aggressive)
        shaped, psycho_report = psycho_verify(shaped, config, bpm=bpm)
        
        # Analyze orchestration
        from melodica.composer.orchestrator import analyze_orchestration
        alerts = analyze_orchestration(instruments)
        
        if verbose:
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
        psycho_report = None

    # 9. [FIX 12] Sparse normalization safeguard
    shaped = _sparse_safeguard(shaped, profiles)

    # 10. Auto-master
    mastered, master_cc = _auto_master(shaped, profiles, mood_profile, pan_overrides)

    # 11. Generate CC events
    total_dur = max((n.start + n.duration for ns in mastered.values() for n in ns), default=0.0)
    entry_cc = _generate_entry_fades(mastered, profiles, total_dur)
    reverb_cc = _generate_reverb_sends(mastered, profiles, mood_profile)
    delay_cc = _generate_delay_sends(mastered, profiles)
    all_cc = _merge_cc_events(master_cc, entry_cc, reverb_cc, delay_cc, cc_events or {})

    # 12. Export
    export_multitrack_midi(mastered, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=all_cc,
                           tempo_events=tempo_events)

    # 13. Report
    report = {
        "profiles": {name: {"role": p.role.value, "avg_pitch": round(p.avg_pitch, 1),
                            "density": round(p.density, 3), "rms": round(p.rms_velocity, 1),
                            "entry": round(p.entry_beat, 1)}
                     for name, p in profiles.items()},
        "psycho": psycho_report,
        "mood": mood.value,
        "lufs": mood_profile.lufs,
        "cc_events": {k: len(v) for k, v in all_cc.items()},
    }

    if verbose:
        roles = {name: p.role.value for name, p in profiles.items()}
        print(f"   Roles: {roles} | LUFS: {mood_profile.lufs}")

    return report


# ---------------------------------------------------------------------------
# [FIX 3] Section-aware mood changes
# ---------------------------------------------------------------------------

def _apply_section_moods(tracks: Dict[str, List[NoteInfo]],
                         sections: List[Tuple[float, Mood]],
                         profiles: Dict[str, _TrackProfile]) -> Dict[str, List[NoteInfo]]:
    """Apply per-section dynamics shaping based on mood changes."""
    if not sections:
        return tracks

    result = {}
    for tname, notes in tracks.items():
        if tname.startswith("_") or not notes:
            result[tname] = notes
            continue

        new_notes = []
        for n in notes:
            # Find which section this note belongs to
            section_mood = sections[0][1]  # default to first mood
            for sec_start, sec_mood in sections:
                if n.start >= sec_start:
                    section_mood = sec_mood

            mood_profile = _MOOD_PROFILES[section_mood]
            # Apply dynamics compression based on section mood
            center = 64
            offset = n.velocity - center
            new_vel = int(round(center + offset * mood_profile.dynamics_range))
            new_vel = max(10, min(127, new_vel))

            new_notes.append(NoteInfo(
                pitch=n.pitch, start=n.start, duration=n.duration,
                velocity=new_vel, articulation=n.articulation,
                expression=n.expression,
            ))
        result[tname] = new_notes

    return result


def _tension_boost(tracks: Dict[str, List[NoteInfo]], factor: float
                   ) -> Dict[str, List[NoteInfo]]:
    """Apply velocity scaling based on harmonic tension."""
    result = {}
    for tname, notes in tracks.items():
        if tname.startswith("_") or not notes:
            result[tname] = notes
            continue
        new_notes = []
        for n in notes:
            new_vel = max(10, min(127, int(n.velocity * factor)))
            new_notes.append(NoteInfo(
                pitch=n.pitch, start=n.start, duration=n.duration,
                velocity=new_vel, articulation=n.articulation,
                expression=n.expression,
            ))
        result[tname] = new_notes
    return result


def produce_album(
    tracks_list: List[Tuple[Dict[str, List[NoteInfo]], float, Dict[str, int], str, Mood]],
    key: Scale | None = None,
    album_name: str = "Album",
    output_dir: str = "output/album",
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

    print("=" * 60)
    print(f"   {album_name}")
    print("=" * 60)

    reports = []
    for i, (tracks, bpm, instruments, filename, mood) in enumerate(tracks_list, 1):
        print(f"\n--- {i:02d}. {filename} ({mood.value}) ---")
        report = produce_track(
            tracks=tracks, bpm=bpm, instruments=instruments,
            path=out / filename, mood=mood, key=key,
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

    combined_tracks: Dict[str, List[NoteInfo]] = {}
    combined_instruments: Dict[str, int] = {}
    combined_cc_events: Dict[str, List[Tuple[float, int, int]]] = {}
    combined_tempo_events: List[Tuple[float, float]] = []

    current_start_beat = 0.0
    first_bpm = tracks_metadata[0].get("bpm", 120.0) if tracks_metadata else 120.0
    first_key = tracks_metadata[0].get("key", None) if tracks_metadata else None

    for i, meta in enumerate(tracks_metadata):
        track_dict = meta.get("tracks", {})
        bpm = meta.get("bpm", 120.0)
        inst_dict = meta.get("instruments", {})
        cc_events = meta.get("cc_events", {})
        tempo_events = meta.get("tempo_events", [])
        this_key = meta.get("key", None)

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
                if prev_key is not None and this_key is not None and (
                    prev_key.root != this_key.root or prev_key.mode != this_key.mode
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
                                bridge_notes.append(NoteInfo(
                                    pitch=pitch,
                                    start=chord.start,
                                    duration=chord.duration * 0.95,  # slight gap between chords
                                    velocity=55,
                                ))

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
        next_start = current_start_beat + track_dur - (overlap_beats if i < len(tracks_metadata) - 1 else 0.0)
        current_start_beat = max(0.0, next_start)

    # Sort all notes and CC events
    for name in combined_tracks.keys():
        combined_tracks[name].sort(key=lambda note: note.start)
    for name in combined_cc_events.keys():
        combined_cc_events[name].sort(key=lambda ev: ev[0])
    combined_tempo_events.sort(key=lambda ev: ev[0])

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
    )
