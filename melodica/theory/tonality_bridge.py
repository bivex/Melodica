# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-07-02 00:00
# Last Updated: 2026-07-02 00:00
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
tonality_bridge.py — Adapter to the Tonality (``mts``) analysis engine.

Tonality is vendored as a git submodule at ``vendor/tonality``. It is a
pure music-theory *analysis* engine (no generation): it returns plural,
ranked, evidenced results. This bridge is the integration seam between
Melodica's generation types (``ChordLabel`` / ``Scale``) and ``mts``'s
analysis API, used as a verification/quality oracle over generated output.

Layer: Domain (pure, no I/O). Optional dependency — every function degrades
gracefully when ``mts`` is unavailable (``HAVE_TONALITY`` is False).

References:
  - mts.analysis.name_chord        — plural ranked chord naming
  - mts.analysis.voice_leading     — exact minimal voice-leading distance
  - mts.analysis.recommend_next_chord — ranked next-chord candidates
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # avoid runtime import (melodica.types <-> melodica.theory cycle)
    from melodica.types import ChordLabel, Scale

__all__ = [
    "HAVE_TONALITY",
    "ensure_mts",
    "name_chord_label",
    "voice_leading_distance",
    "voice_lead_exact",
    "voice_lead_progression",
    "ExactVoiceLeading",
    "recommend_next",
    "analyze_progression",
    "verify_progression",
]


# -- engine loader -----------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VENDOR_PATH = _REPO_ROOT / "vendor" / "tonality"

mts: Any = None


def ensure_mts() -> Any:
    """Import ``mts``, falling back to the vendored submodule path.

    Idiomatic path is ``pip install -e vendor/tonality``; the path fallback
    makes the bridge work on a fresh clone without that install step.
    """
    global mts
    if mts is not None:
        return mts
    try:
        import mts as _mts  # type: ignore[import-not-found]
    except ImportError:
        path = str(_VENDOR_PATH)
        if path not in sys.path:
            sys.path.insert(0, path)
        import mts as _mts  # type: ignore[import-not-found]
    mts = _mts
    return mts


try:
    ensure_mts()
    HAVE_TONALITY = True
except Exception:  # pragma: no cover - optional dep, absent in minimal envs
    HAVE_TONALITY = False


# -- conversions -------------------------------------------------------------

def _to_pcs(chord: "ChordLabel | Iterable[int]") -> list[int]:
    """Coerce a ChordLabel (duck-typed via ``.pitch_classes()``) or pc iterable."""
    if hasattr(chord, "pitch_classes"):
        return sorted({int(pc) % 12 for pc in chord.pitch_classes()})
    return sorted({int(p) % 12 for p in chord})


def _mode_for_succession(key: Scale) -> str | None:
    """Map a Melodica mode to the major/minor label ``mts`` succession accepts.

    ``recommend_next_chord`` supports major/minor only and *raises* on modal
    keys rather than guessing; we return ``None`` to signal "skip".
    """
    value = key.mode.value
    if value in {"major", "ionian"}:
        return "major"
    if value in {"natural_minor", "aeolian", "harmonic_minor", "melodic_minor"}:
        return "minor"
    return None


# -- analysis API ------------------------------------------------------------

def name_chord_label(chord: ChordLabel | Iterable[int]) -> Any:
    """Rank every valid naming of *chord* (ChordLabel or pc iterable).

    Returns ``mts.analysis.results.ChordNaming`` (``.chosen``, ``.alternatives``,
    ``.is_ambiguous``, ``.weights_version``). Intrinsic-only ranking — no key
    is fabricated. Returns ``None`` if ``mts`` is unavailable.
    """
    if not HAVE_TONALITY:
        return None
    from mts.analysis import name_chord  # type: ignore[import-not-found]

    return name_chord(_to_pcs(chord), None)


def voice_leading_distance(
    a: ChordLabel | Iterable[int],
    b: ChordLabel | Iterable[int],
) -> int:
    """Exact minimal voice-leading distance (semitones) between two pc-sets."""
    if not HAVE_TONALITY:
        raise RuntimeError("mts (Tonality) is not available.")
    from mts.analysis import voice_leading  # type: ignore[import-not-found]

    return voice_leading(_to_pcs(a), _to_pcs(b)).distance


@dataclass(frozen=True)
class ExactVoiceLeading:
    """Result of exact minimal-motion voice-leading into a target chord.

    ``voicing`` is the realized target (MIDI pitches) with provably minimal
    per-voice motion under the optimal pc-assignment from ``mts``;
    ``realized_distance`` is the total semitone motion of that realization;
    ``identity_distance``/``mapping``/``policy`` are the ``mts`` evidence
    (identity-level optimal assignment + the doubling convention cited).
    """

    voicing: list[int]
    realized_distance: int
    identity_distance: int
    mapping: list[list[int]] = field(default_factory=list)
    policy: str = ""


def voice_lead_exact(
    prev: "ChordLabel | list[int] | tuple[int, ...]",
    target: "ChordLabel | Iterable[int]",
    *,
    keep_source_cardinality: bool = True,
) -> ExactVoiceLeading:
    """Voice-lead *target* from *prev* with minimal total motion.

    Improvement over ``theory.voicing.voice_lead``: instead of searching only
    chord inversions under a greedy motion cost, this takes the **optimal
    pc-assignment** from ``mts.voice_leading`` (exact bijection/surjection,
    ``doubling.1`` policy) and realizes each source voice onto its mapped
    target pitch class at the nearest octave — so per-voice motion is minimal
    for the optimal assignment, and the assignment itself is provably optimal
    at the pc level.

    Args:
        prev: previous voicing as MIDI pitches, or a ``ChordLabel``.
        target: target chord as a ``ChordLabel`` or any pc/MIDI iterable.
        keep_source_cardinality: keep one output voice per source voice
            (smoothest for sequential voice-leading). When False, output one
            voice per distinct target pc.

    Returns:
        ``ExactVoiceLeading``. Raises ``RuntimeError`` if ``mts`` is absent,
        ``ValueError`` if either side is empty.
    """
    if not HAVE_TONALITY:
        raise RuntimeError("mts (Tonality) is not available.")

    # Resolve source voicing to MIDI (chord_to_notes imported lazily to avoid
    # a theory.voicing -> ... cycle at module import time).
    if isinstance(prev, (list, tuple)):
        source_midi = [int(p) for p in prev]
    else:
        from melodica.theory.voicing import chord_to_notes

        source_midi = list(chord_to_notes(prev))

    if not source_midi:
        raise ValueError("voice_lead_exact needs a non-empty source voicing.")
    target_pcs = _to_pcs(target)
    if not target_pcs:
        raise ValueError("voice_lead_exact needs a non-empty target chord.")

    from mts.analysis import voice_leading  # type: ignore[import-not-found]

    source_pcs = sorted({int(m) % 12 for m in source_midi})
    vl = voice_leading(source_pcs, target_pcs)

    # Optimal pc correspondence [from_pc, to_pc]; realize each source voice
    # onto its target pc at the nearest octave (minimal per-voice motion).
    pc_map = {int(f): int(t) for f, t in vl.mapping}

    if keep_source_cardinality:
        anchors = source_midi
    else:
        # One voice per distinct target pc, anchored at the source median
        # octave so the realization stays in register.
        anchor_octave = sorted(source_midi)[len(source_midi) // 2] // 12
        anchors = [12 * anchor_octave + tpc for tpc in target_pcs]

    voicing: list[int] = []
    for m in anchors:
        tpc = pc_map.get(int(m) % 12, target_pcs[0])
        # Nearest octave placement of tpc to the anchor pitch m.
        voicing.append(tpc + 12 * round((m - tpc) / 12))

    voicing = sorted(set(voicing))
    realized = sum(abs(s - o) for s, o in zip(anchors, voicing))
    return ExactVoiceLeading(
        voicing=voicing,
        realized_distance=int(realized),
        identity_distance=int(vl.distance),
        mapping=[list(pair) for pair in vl.mapping],
        policy=str(vl.policy),
    )


def voice_lead_progression(
    chords: list["ChordLabel"],
    *,
    start_voicing: list[int] | None = None,
    keep_source_cardinality: bool = True,
) -> list[list[int]]:
    """Voice a whole chord progression with chained minimal-motion voice-leading.

    Each chord is voice-led from the *realized* previous voicing, so total
    motion across the progression stays minimal — the album-assembly helper
    over an engine's ``list[ChordLabel]`` output. The first chord is seeded at
    root position (or by ``start_voicing``). Returns one MIDI voicing per chord.

    Raises ``RuntimeError`` if ``mts`` is unavailable.
    """
    if not chords:
        return []
    if start_voicing is not None:
        voicings: list[list[int]] = [sorted(start_voicing)]
    else:
        from melodica.theory.voicing import chord_to_notes

        voicings = [list(chord_to_notes(chords[0]))]
    for chord in chords[1:]:
        voicings.append(
            voice_lead_exact(
                voicings[-1], chord, keep_source_cardinality=keep_source_cardinality
            ).voicing
        )
    return voicings


def recommend_next(chord: ChordLabel, key: Scale) -> Any:
    """Ranked next-chord candidates for *chord* in *key* (major/minor only).

    Returns ``NextChordRecommendation`` or ``None`` (engine absent or modal key,
    which ``mts`` declines to guess).
    """
    if not HAVE_TONALITY:
        return None
    mode = _mode_for_succession(key)
    if mode is None:
        return None
    from mts.analysis import recommend_next_chord  # type: ignore[import-not-found]

    naming = name_chord_label(chord)
    quality = naming.chosen.interpretation.quality if naming and naming.chosen else "maj"
    root_pc = naming.chosen.interpretation.root_pc if naming and naming.chosen else chord.root
    return recommend_next_chord(
        (root_pc, quality),
        tonic_pc=key.root,
        mode=mode,
    )


# -- verification oracle -----------------------------------------------------

def analyze_progression(chords: list[ChordLabel], key: Scale | None = None) -> list[dict[str, Any]]:
    """Analyze each chord in a generated progression.

    Per-chord report: chosen name, ambiguity flag, ``None`` chosen when the set
    matches nothing in the catalog (an honesty signal — the generator produced
    something the theory cannot parse).
    """
    reports: list[dict[str, Any]] = []
    for chord in chords:
        naming = name_chord_label(chord)
        if naming is None:
            reports.append({"pcs": _to_pcs(chord), "chosen": None, "ambiguous": None})
            continue
        chosen = naming.chosen
        reports.append(
            {
                "pcs": _to_pcs(chord),
                "root": chord.root,
                "chosen": (
                    chosen.interpretation.root_pc,
                    chosen.interpretation.quality,
                )
                if chosen
                else None,
                "alternatives": [
                    (a.interpretation.root_pc, a.interpretation.quality)
                    for a in naming.alternatives
                ],
                "ambiguous": naming.is_ambiguous,
                "functional_role": chosen.functional_role if chosen else None,
                "weights_version": naming.weights_version,
            }
        )
    return reports


def verify_progression(chords: list[ChordLabel]) -> dict[str, Any]:
    """Summarize a progression's theory-coherence for generation feedback.

    Counts parseable / ambiguous / unparseable chords and accumulates total
    voice-leading motion — a cheap "did the generator stay coherent?" signal.
    """
    reports = analyze_progression(chords)
    unparseable = sum(1 for r in reports if r["chosen"] is None)
    ambiguous = sum(1 for r in reports if r.get("ambiguous"))
    total_vl = 0
    if HAVE_TONALITY and len(chords) >= 2:
        for prev, cur in zip(chords, chords[1:]):
            try:
                total_vl += voice_leading_distance(prev, cur)
            except ValueError:
                continue
    return {
        "n": len(chords),
        "parseable": len(reports) - unparseable,
        "unparseable": unparseable,
        "ambiguous": ambiguous,
        "total_voice_leading": total_vl,
        "per_chord": reports,
    }
