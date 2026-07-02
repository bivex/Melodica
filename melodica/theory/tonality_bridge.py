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


def _key_context(key: "Scale") -> Any:
    """Build an mts ``AnalyticalContext`` from a Melodica key (Scale).

    Lets ``name_chord`` score candidate namings against the active key
    (scale-degree fit). Required, alongside a bass realization, to resolve
    pc-set equivalences such as Cm7 ≡ Eb6 or augmented symmetry. Returns
    ``None`` if the key cannot be mapped (caller then names intrinsically).
    """
    try:
        from mts.analysis.analytical_context import (
            AnalyticalContext,
            Scale as MtsScale,
        )
    except Exception:  # pragma: no cover - mts layout drift
        return None
    abs_pcs = sorted({int(d) for d in key.degrees() if abs(d - round(d)) < 0.01})
    if not abs_pcs:
        return None
    root = int(key.root) % 12
    degrees = tuple(sorted({(p - root) % 12 for p in abs_pcs}))
    mask = sum(1 << p for p in abs_pcs)
    mode_val = getattr(getattr(key, "mode", None), "value", "key")
    try:
        mts_key = MtsScale(name=str(mode_val), degrees=degrees, mask=mask)
    except Exception:  # pragma: no cover - mts rejects the degree/mask shape
        return None
    return AnalyticalContext(tonic_pc=root, key=mts_key)


def _actual_bass_pc(chord: "ChordLabel | Iterable[int]", root: int) -> int:
    """The true sounding bass pc of *chord*: slash bass > inversion > root.

    Inversions matter for the m7 ≡ maj6 disambiguation (a first-inversion Cm7
    has bass Eb and really does resemble Eb6), so the bass fed to ``name_chord``
    must be the actual lowest tone, not an assumed root. Plain pc iterables have
    no bass/voice information, so they fall back to *root*.
    """
    slash = getattr(chord, "bass", None)
    if slash is not None:
        return int(slash) % 12
    inv = getattr(chord, "inversion", 0) or 0
    if inv == 0:
        return int(root) % 12
    try:  # N-th chord tone (ascending interval) is the bass in inversion N
        from melodica.types_pkg._theory import CHORD_TEMPLATES

        ivls = sorted(
            set(CHORD_TEMPLATES.get(chord.quality, [0]))
            | set(getattr(chord, "extensions", []) or [])
        )
    except Exception:  # pragma: no cover - plain iterable / missing template
        return int(root) % 12
    return (int(root) + ivls[inv]) % 12 if inv < len(ivls) else int(root) % 12


def _bass_realization(pcs: list[int], bass_pc: int, root_pc: int) -> Any:
    """Build an mts ``Realization`` with *bass_pc* as the lowest pitch.

    The bass is the disambiguator for equivalences like Cm7 (bass C) vs Eb6
    (bass Eb), or which augmented-triad root is in play. The remaining chord
    tones sit an octave above so the bass is unambiguously lowest; ``root_pc``
    records the true root (which may differ from the bass in an inversion).
    """
    from mts.analysis import Pitch, Realization

    b = int(bass_pc) % 12
    pitches = [Pitch(midi=60 + b, pc=b, octave=(60 + b) // 12 - 1)]
    for p in sorted({int(x) % 12 for x in pcs}):
        if p == b:
            continue
        pitches.append(Pitch(midi=72 + p, pc=p, octave=(72 + p) // 12 - 1))
    return Realization(pitches=tuple(pitches), root_pc=int(root_pc) % 12)


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

def name_chord_label(chord: ChordLabel | Iterable[int], key: Scale | None = None) -> Any:
    """Rank every valid naming of *chord* (ChordLabel or pc iterable).

    Returns ``mts.analysis.results.ChordNaming`` (``.chosen``, ``.alternatives``,
    ``.is_ambiguous``, ``.weights_version``). Returns ``None`` if ``mts`` is
    unavailable.

    With ``key=None`` (default) the ranking is intrinsic-only — no key is
    fabricated, so pc-set equivalences (Cm7 ≡ Eb6, augmented symmetry) are
    reported ambiguous. Pass the active *key* together with a ``ChordLabel``
    (which carries its root) to also supply key context and a bass realization;
    together they resolve those equivalences. The effect is monotone: ambiguity
    can only decrease, never increase, since context scores interpretations
    rather than adding them.
    """
    if not HAVE_TONALITY:
        return None
    from mts.analysis import name_chord  # type: ignore[import-not-found]

    pcs = _to_pcs(chord)
    if key is None:
        return name_chord(pcs, None)

    context = _key_context(key)
    if context is None:
        return name_chord(pcs, None)
    root = getattr(chord, "root", None)
    bass = _actual_bass_pc(chord, root) if root is not None else None
    realization = _bass_realization(pcs, bass, root) if bass is not None else None
    return name_chord(pcs, context, realization=realization)


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
        naming = name_chord_label(chord, key=key)
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


def verify_progression(chords: list[ChordLabel], key: Scale | None = None) -> dict[str, Any]:
    """Summarize a progression's theory-coherence for generation feedback.

    Counts parseable / ambiguous / unparseable chords and accumulates total
    voice-leading motion — a cheap "did the generator stay coherent?" signal.
    Pass the active *key* so chord naming uses key context + bass, resolving
    pc-set equivalences (Cm7 ≡ Eb6, aug symmetry) instead of flagging them
    ambiguous. With ``key=None`` naming stays intrinsic-only.
    """
    reports = analyze_progression(chords, key=key)
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
