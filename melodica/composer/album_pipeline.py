# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.composer.album_pipeline — Unified track production and album orchestrator.

Generates → mixes → masters → exports a single track or full album.
Decomposed into:
- melodica.render.mix: Acoustic analysis, panning, auto-mix, and mastering
- melodica.plan.album: Album narrative, section progression, continuous album
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Tuple

from melodica.plan.album import (
    Mood,
    SectionProfile,
    SECTION_PROFILES,
    AlbumNarrative,
    clamp_to_scale,
    compile_continuous_album,
    detect_sections_intelligently,
    generate_narrative_motif,
    produce_album,
    _MOOD_PROFILES,
    _MoodProfile,
    _apply_section_moods,
    _build_section_cc_automation,
    _compute_tension,
    _detect_role_from_track_name,
    _quantize_onsets,
    _resolve_leaps,
    _resolve_rhythm,
    _resolve_section_profile,
    _soft_blend,
    _stage_articulations,
    _stage_breathing_room,
    _stage_diagnostics,
    _stage_harmonic_verify,
    _stage_leap_resolve,
    _stage_non_chord_tones,
    _stage_phrase_dynamics,
    _stage_rhythm,
    _stage_sections,
    _stage_tension,
    _stage_texture,
    _stage_transitions,
    _tension_boost,
    _weave_narrative_motif,
)
from melodica.render.mix import (
    DEFAULT_GENRE,
    PanReport,
    PanValidator,
    Role,
    _DYNAMICS_WINDOW_BEATS,
    _HUMANIZE_PROFILES,
    _HUMANIZE_ROLE_DEFAULTS,
    _NAME_HINTS,
    _PAN_RULES,
    _POLY_SLOT_RESOLUTION,
    _PROTECTED_CENTER,
    _ROLE_GAINS,
    _ROLE_HEURISTICS,
    _ROLE_PAN,
    _ROLE_PAN_PROFILES,
    _ROLE_REVERB,
    _SPARSE_THRESHOLD,
    _TrackProfile,
    _analyze_track,
    _apply_humanization,
    _auto_master,
    _auto_mix,
    _auto_spread_panning,
    _check_frequency_pan_conflicts,
    _density_gain_factor,
    _generate_delay_sends,
    _generate_entry_fades,
    _generate_pan_automation,
    _generate_reverb_sends,
    _get_pan_for_role,
    _get_role_pan_map,
    _humanize_profile,
    _merge_cc_events,
    _polyphony_limit,
    _print_pan_map,
    _shape_dynamics,
    _sidechain_duck,
    _sparse_safeguard,
    _stage_auto_mix,
    _stage_dynamics,
    _stage_export,
    _stage_humanize,
    _stage_master,
    _stage_pan_spread,
    _stage_polyphony,
    _stage_psycho,
    _stage_report,
    _stage_sidechain,
    _stage_sparse_safeguard,
)
from melodica.types import NoteInfo, Scale

if TYPE_CHECKING:
    from melodica.composer.psychoacoustic import PsychoReport


# ---------------------------------------------------------------------------
# Pipeline infrastructure
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
    """A single pipeline stage with execution gates and ordering dependencies."""

    name: str
    fn: "callable"
    enabled: bool = True
    requires_keys: tuple[str, ...] = ()
    config_flag: str | None = None
    requires_stages: tuple[str, ...] = ()


DEFAULT_PIPELINE: list[Stage] = [
    Stage("rhythm", _stage_rhythm, requires_keys=("rhythm",)),
    Stage("auto_mix", _stage_auto_mix, config_flag="use_mixing"),
    Stage("pan_spread", _stage_pan_spread, requires_stages=("auto_mix",)),
    Stage("dynamics", _stage_dynamics),
    Stage("sidechain", _stage_sidechain),
    Stage("humanize", _stage_humanize),
    Stage("phrase_dynamics", _stage_phrase_dynamics),
    Stage("articulations", _stage_articulations),
    Stage("harmonic_verify", _stage_harmonic_verify, config_flag="use_harmonic_verifier"),
    Stage(
        "non_chord_tones",
        _stage_non_chord_tones,
        requires_keys=("chords", "key"),
        requires_stages=("harmonic_verify",),
    ),
    Stage("sections", _stage_sections, requires_keys=("sections",)),
    Stage("tension", _stage_tension, requires_keys=("chords",)),
    Stage("texture", _stage_texture, requires_keys=("chords",)),
    Stage("transitions", _stage_transitions, requires_keys=("section_breaks",)),
    Stage("leap_resolve", _stage_leap_resolve, requires_stages=("texture",)),
    Stage("breathing_room", _stage_breathing_room, requires_stages=("texture",)),
    Stage("polyphony", _stage_polyphony),
    Stage("psycho", _stage_psycho),
    Stage("sparse_safeguard", _stage_sparse_safeguard),
    Stage("master", _stage_master, config_flag="use_mastering"),
    Stage("export", _stage_export, requires_stages=("master",)),
    Stage("report", _stage_report),
    Stage("diagnostics", _stage_diagnostics),
]


def validate_pipeline_order(stages: list[Stage]) -> None:
    """Assert that every ``requires_stages`` dependency precedes its stage."""
    present = {s.name for s in stages}
    seen: set[str] = set()
    for stage in stages:
        for dep in stage.requires_stages:
            if dep not in present:
                continue
            if dep not in seen:
                raise ValueError(
                    f"Pipeline ordering invariant violated: stage {stage.name!r} "
                    f"requires {dep!r} to run before it, but {dep!r} appears "
                    f"later (or equals it) in the pipeline."
                )
        seen.add(stage.name)


def _stage_skip_reason(stage: Stage, kw: dict, feature_flags: dict) -> str | None:
    """Return why a stage should be skipped, or None if it should run."""
    if not stage.enabled:
        return "disabled"
    if stage.config_flag is not None:
        if not feature_flags.get(stage.config_flag, False):
            return f"config {stage.config_flag}=False"
    for key in stage.requires_keys:
        if not kw.get(key):
            return f"no {key!r}"
    return None


def _is_valid_time_signature(ts: object) -> bool:
    try:
        num, den = ts  # type: ignore
        return (
            isinstance(num, int)
            and isinstance(den, int)
            and num > 0
            and den in (1, 2, 4, 8, 16)
        )
    except (TypeError, ValueError):
        return False


def _validate_produce_track_args(
    rhythm: str | object | None,
    key: Scale | None,
    chords: list | None,
    genre: str,
    time_signature: tuple[int, int] | None,
) -> None:
    """Validate required arguments for produce_track."""
    if rhythm is None:
        raise ValueError(
            "rhythm is required for produce_track. Pass a rhythm name (str from "
            "RHYTHM_LIBRARY/DYNAMIC_RHYTHM_REGISTRY) or a RhythmGenerator instance."
        )
    if key is None:
        raise ValueError("key is required for produce_track. Pass a Scale instance.")
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
    if not _is_valid_time_signature(time_signature):
        raise ValueError(
            f"time_signature must be (numerator>0, denominator in {{1,2,4,8,16}}); "
            f"got {time_signature!r}."
        )


def _resolve_and_validate_sections(
    sections: List[Tuple[float, Mood | str]] | None,
    tracks: Dict[str, List[NoteInfo]],
    bpm: float,
    time_signature: tuple[int, int],
    verbose: bool,
) -> List[Tuple[float, Mood | str]]:
    """Detect arrangement sections if missing and validate chronological order."""
    if not sections:
        sections = detect_sections_intelligently(tracks, bpm, time_signature)
        if verbose:
            print(
                f"   [AI Section Analyzer] Auto-detected arrangement: {', '.join(f'{lbl} (@{start}b)' for start, lbl in sections)}"
            )

    last_beat = -1.0
    for idx, sec in enumerate(sections):
        if not isinstance(sec, (list, tuple)) or len(sec) < 2:
            raise ValueError(
                f"Section at index {idx} must be a tuple/list of (start_beat, mood)."
            )
        beat, _sec_mood = sec
        if beat < last_beat:
            raise ValueError(
                f"Sections are not in chronological order: section at index {idx} starts at beat {beat}, which is less than preceding beat {last_beat}."
            )
        last_beat = beat

    return sections


def _resolve_feature_flags(feature_flags: dict | None) -> dict[str, bool]:
    """Resolve default feature flags if none provided."""
    if feature_flags is not None:
        return feature_flags
    try:
        from melodica.idea_tool import IdeaToolConfig

        _cfg = IdeaToolConfig()
        return {
            "use_mixing": _cfg.use_mixing,
            "use_mastering": _cfg.use_mastering,
            "use_harmonic_verifier": _cfg.use_harmonic_verifier,
        }
    except Exception:
        return {
            "use_mixing": True,
            "use_mastering": True,
            "use_harmonic_verifier": True,
        }


def _run_pipeline_stages(
    stages: list[Stage],
    kw: dict,
    feature_flags: dict,
    verbose: bool,
) -> tuple[dict, list[tuple[str, str]]]:
    """Execute pipeline stages sequentially and collect skipped stages."""
    skipped: list[tuple[str, str]] = []
    for stage in stages:
        reason = _stage_skip_reason(stage, kw, feature_flags)
        if reason is not None:
            skipped.append((stage.name, reason))
            continue
        kw = stage.fn(kw)

    if verbose and skipped:
        print("  Stage activation report:")
        for name, reason in skipped:
            print(f"    - {name:<18} skipped: {reason}")

    return kw, skipped


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
    feature_flags: dict | None = None,
    skip_stages: list[str] | None = None,
) -> dict:
    """Full production pipeline: analyze → mix → dynamics → psycho → master → export."""
    _validate_produce_track_args(rhythm, key, chords, genre, time_signature)
    resolved_sections = _resolve_and_validate_sections(sections, tracks, bpm, time_signature, verbose)

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mood_profile = _MOOD_PROFILES[mood]

    stages = pipeline if pipeline is not None else DEFAULT_PIPELINE
    if skip_stages:
        stages = [s for s in stages if s.name not in skip_stages]

    flags = _resolve_feature_flags(feature_flags)
    validate_pipeline_order(stages)

    kw = dict(
        tracks=tracks,
        bpm=bpm,
        instruments=instruments,
        path=out_path,
        mood=mood,
        mood_profile=mood_profile,
        key=key,
        verbose=verbose,
        psycho_verify_enabled=psycho_verify_enabled,
        genre=genre,
        sections=resolved_sections,
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

    kw, _skipped = _run_pipeline_stages(stages, kw, flags, verbose)

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
            "_report": kw.get("_report", {}),
        }
    return kw.get("_report", {})


__all__ = [
    # Core orchestration
    "produce_track",
    "produce_album",
    "compile_continuous_album",
    "AlbumNarrative",
    "TrackState",
    "Stage",
    "DEFAULT_PIPELINE",
    "validate_pipeline_order",
    "detect_sections_intelligently",
    # Mood & Sections
    "Mood",
    "_MoodProfile",
    "_MOOD_PROFILES",
    "SectionProfile",
    "SECTION_PROFILES",
    "_resolve_section_profile",
    "_build_section_cc_automation",
    "_apply_section_moods",
    "_detect_role_from_track_name",
    # Mix & Audio
    "Role",
    "_TrackProfile",
    "_ROLE_HEURISTICS",
    "_NAME_HINTS",
    "_analyze_track",
    "_ROLE_PAN_PROFILES",
    "_ROLE_PAN",
    "DEFAULT_GENRE",
    "_get_role_pan_map",
    "_get_pan_for_role",
    "_PROTECTED_CENTER",
    "_auto_spread_panning",
    "_PAN_RULES",
    "_check_frequency_pan_conflicts",
    "PanReport",
    "PanValidator",
    "_print_pan_map",
    "_ROLE_GAINS",
    "_density_gain_factor",
    "_auto_mix",
    "_sidechain_duck",
    "_HUMANIZE_PROFILES",
    "_HUMANIZE_ROLE_DEFAULTS",
    "_humanize_profile",
    "_apply_humanization",
    "_generate_entry_fades",
    "_ROLE_REVERB",
    "_generate_reverb_sends",
    "_generate_delay_sends",
    "_generate_pan_automation",
    "_POLY_SLOT_RESOLUTION",
    "_polyphony_limit",
    "_SPARSE_THRESHOLD",
    "_sparse_safeguard",
    "_auto_master",
    "_DYNAMICS_WINDOW_BEATS",
    "_shape_dynamics",
    "_merge_cc_events",
    # Stages
    "_stage_rhythm",
    "_stage_auto_mix",
    "_stage_pan_spread",
    "_stage_dynamics",
    "_stage_sidechain",
    "_stage_humanize",
    "_stage_phrase_dynamics",
    "_stage_articulations",
    "_stage_harmonic_verify",
    "_stage_non_chord_tones",
    "_stage_sections",
    "_stage_tension",
    "_stage_texture",
    "_stage_transitions",
    "_stage_leap_resolve",
    "_stage_breathing_room",
    "_stage_polyphony",
    "_stage_psycho",
    "_stage_sparse_safeguard",
    "_stage_master",
    "_stage_export",
    "_stage_report",
    "_stage_diagnostics",
    # Musical transformations
    "clamp_to_scale",
    "_weave_narrative_motif",
    "_soft_blend",
    "_resolve_leaps",
    "generate_narrative_motif",
    "_compute_tension",
    "_tension_boost",
]
