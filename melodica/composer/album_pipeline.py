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


_ROLE_HEURISTICS = {
    # (avg_pitch_range, density_range, keyword_patterns) → Role
    "bass":   (lambda p, d: p < 48),
    "lead":   (lambda p, d: p > 60 and d > 0.15),
    "pad":    (lambda p, d: d < 0.1),
    "perc":   (lambda p, d: d > 0.3 and p > 70),
    "strings":(lambda p, d: 40 < p < 75 and 0.05 < d < 0.3),
    "choir":  (lambda p, d: 50 < p < 70 and d < 0.15),
    "fx":     (lambda p, d: p > 80 and d < 0.05),
}

# Name-based role hints (substring match, case-insensitive)
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


def _analyze_track(name: str, notes: List[NoteInfo]) -> _TrackProfile:
    """Analyze a track's register, density, and assign a role."""
    if not notes:
        return _TrackProfile(60, 0, 0, 0, Role.PAD)

    avg_pitch = sum(n.pitch for n in notes) / len(notes)
    min_p = min(n.pitch for n in notes)
    max_p = max(n.pitch for n in notes)
    total_dur = max(n.start + n.duration for n in notes) - notes[0].start
    density = len(notes) / max(total_dur, 1.0)
    rms = math.sqrt(sum(n.velocity ** 2 for n in notes) / len(notes))

    # Name hint first
    name_lower = name.lower()
    for hint, role in _NAME_HINTS.items():
        if hint in name_lower:
            role_final = role
            break
    else:
        # Heuristic: pitch + density
        for _, predicate in _ROLE_HEURISTICS.items():
            pass
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

    return _TrackProfile(avg_pitch, max_p - min_p, density, rms, role_final)


# ---------------------------------------------------------------------------
# Auto-mixing: role-based gain, pan, and register shaping
# ---------------------------------------------------------------------------

# Role → default gain multiplier
_ROLE_GAINS: Dict[Role, float] = {
    Role.LEAD:    0.85,
    Role.BASS:    0.55,
    Role.PAD:     0.35,
    Role.PERC:    0.70,
    Role.STRINGS: 0.65,
    Role.CHOIR:   0.45,
    Role.FX:      0.50,
}

# Role → default pan (-1 to +1)
_ROLE_PAN: Dict[Role, float] = {
    Role.LEAD:    0.0,
    Role.BASS:    0.0,
    Role.PAD:    -0.30,
    Role.PERC:    0.15,
    Role.STRINGS: 0.20,
    Role.CHOIR:  -0.10,
    Role.FX:      0.30,
}


def _auto_mix(tracks: Dict[str, List[NoteInfo]], mood_profile: _MoodProfile
              ) -> Tuple[Dict[str, List[NoteInfo]], Dict[str, _TrackProfile]]:
    """Analyze tracks, assign gains by role, apply register shaping."""
    profiles = {}
    for name, notes in tracks.items():
        if not notes or name.startswith("_"):
            continue
        profiles[name] = _analyze_track(name, notes)

    # Build gain map: role default × register tweak × mood bass boost
    gains: Dict[str, float] = {}
    for name, prof in profiles.items():
        base = _ROLE_GAINS.get(prof.role, 0.80)
        # Register tweak: low reg needs perceived loudness boost
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
        gains[name] = base * reg_tweak

    # Detect register overlap: if two non-perc tracks share pitch space,
    # attenuate the one with lower RMS
    names = [n for n in profiles if profiles[n].role not in (Role.PERC, Role.FX)]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = profiles[names[i]], profiles[names[j]]
            if abs(a.avg_pitch - b.avg_pitch) < 8:  # within ~half octave
                quieter = names[i] if a.rms_velocity < b.rms_velocity else names[j]
                gains[quieter] *= 0.75  # duck the competing track

    # Apply MixingDesk
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update(gains)
    mixed = desk.apply_mixing(tracks, [], 120)  # BPM irrelevant with empty sections

    return mixed, profiles


# ---------------------------------------------------------------------------
# Auto-mastering with mood-aware settings
# ---------------------------------------------------------------------------

def _auto_master(tracks: Dict[str, List[NoteInfo]], profiles: Dict[str, _TrackProfile],
                 mood_profile: _MoodProfile
                 ) -> Tuple[Dict[str, List[NoteInfo]], Dict[str, List[Tuple[float, int, int]]]]:
    """Master with mood-aware LUFS, role-based pan, and brightness ceiling."""
    # Build pan map from role profiles
    pan_map = {}
    for name, prof in profiles.items():
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

def _shape_dynamics(tracks: Dict[str, List[NoteInfo]], mood_profile: _MoodProfile
                    ) -> Dict[str, List[NoteInfo]]:
    """Widen or compress velocity range based on mood dynamics setting."""
    rng = mood_profile.dynamics_range
    if rng >= 0.95:
        return tracks  # nothing to do

    result = {}
    for name, notes in tracks.items():
        if not notes or name.startswith("_"):
            result[name] = notes
            continue
        vels = [n.velocity for n in notes]
        mn, mx = min(vels), max(vels)
        if mx - mn < 5:
            result[name] = notes
            continue
        center = (mn + mx) / 2
        half = (mx - mn) / 2
        # Compress toward center by dynamics_range factor
        shaped = []
        for n in notes:
            offset = n.velocity - center
            new_vel = int(round(center + offset * rng))
            new_vel = max(10, min(127, new_vel))
            shaped.append(NoteInfo(
                pitch=n.pitch, start=n.start, duration=n.duration,
                velocity=new_vel, articulation=n.articulation, expression=n.expression,
            ))
        result[name] = shaped
    return result


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

    Returns
    -------
    dict with keys: profiles, report
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mood_profile = _MOOD_PROFILES[mood]

    # 1. Analyze + auto-mix
    mixed, profiles = _auto_mix(tracks, mood_profile)

    # 2. Dynamics shaping
    shaped = _shape_dynamics(mixed, mood_profile)

    # 3. Psychoacoustic verification
    if psycho_verify_enabled:
        config = PsychoConfig(aggressive_fix=mood_profile.psycho_aggressive)
        shaped, psycho_report = psycho_verify(shaped, config)
        if verbose and psycho_report.issues_detected > 0:
            print(f"   Psycho: {psycho_report.issues_detected} issues, "
                  f"{psycho_report.issues_fixed} fixed "
                  f"({psycho_report.notes_velocity_reduced} vel-, "
                  f"{psycho_report.notes_removed} removed, "
                  f"{psycho_report.notes_transposed} transposed)")
    else:
        psycho_report = None

    # 4. Auto-master
    mastered, cc_events = _auto_master(shaped, profiles, mood_profile)

    # 5. Export
    export_multitrack_midi(mastered, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)

    # 6. Report
    report = {
        "profiles": {name: {"role": p.role.value, "avg_pitch": round(p.avg_pitch, 1),
                            "density": round(p.density, 3), "rms": round(p.rms_velocity, 1)}
                     for name, p in profiles.items()},
        "psycho": psycho_report,
        "mood": mood.value,
        "lufs": mood_profile.lufs,
    }

    if verbose:
        roles = {name: p.role.value for name, p in profiles.items()}
        print(f"   Roles: {roles} | LUFS: {mood_profile.lufs}")

    return report


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
