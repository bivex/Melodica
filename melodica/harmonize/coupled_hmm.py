# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
coupled_hmm.py — Hierarchical HMM Harmonizer (12 chord types).
Based on research by Dmitri Tymoczko and Mark Newman (2024).

Layer 1: Notes -> Chords via Viterbi over 144 states (12 roots x 12 types).
Layer 2: Chords -> Keys via Viterbi over 12 roots x N key types.

Weights loaded from melodica/harmonize/weights/ (trained by train_full_modes.py).
"""

from __future__ import annotations

import math
import warnings
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from melodica.theory.modes import MODE_DATABASE, get_mode_intervals, Mode
from melodica.types import BarGrid, ChordLabel, Quality, Scale, NoteInfo

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

N_TONES = 12
N_TYPES = 12  # Maj, Min, Dim, Aug, sus2, sus4, Maj7, Min7, Dom7, Maj9, Min9, Add9

# Chord-tone interval sets per type (offsets above root). MUST match
# train_full_modes.py CHORD_NOTES — used by the optional set-completion bonus.
CHORD_NOTES = {
    0: {0, 4, 7}, 1: {0, 3, 7}, 2: {0, 3, 6}, 3: {0, 4, 8},
    4: {0, 2, 7}, 5: {0, 5, 7}, 6: {0, 4, 7, 11}, 7: {0, 3, 7, 10},
    8: {0, 4, 7, 10}, 9: {0, 4, 7, 11, 2}, 10: {0, 3, 7, 10, 2}, 11: {0, 4, 7, 2},
}

# List of all supported modes for Layer 2
MODES_LIST = list(MODE_DATABASE.keys())
N_KEY_TYPES = len(MODES_LIST)

# Mapping from training type index to Quality enum
TYPE_TO_QUALITY = [
    Quality.MAJOR,       # 0
    Quality.MINOR,       # 1
    Quality.DIMINISHED,  # 2
    Quality.AUGMENTED,   # 3
    Quality.SUS2,        # 4
    Quality.SUS4,        # 5
    Quality.MAJOR7,      # 6
    Quality.MINOR7,      # 7
    Quality.DOMINANT7,   # 8
    Quality.MAJOR9,      # 9
    Quality.MINOR9,      # 10
    Quality.ADD9,        # 11
]

# Reverse map: Quality → type index (for constraints)
_QUALITY_TO_TYPE = {q: i for i, q in enumerate(TYPE_TO_QUALITY)}

# Fallback map for unsupported qualities → closest supported type
_QUALITY_FALLBACK = {
    Quality.HALF_DIM7: Quality.MINOR7,
    Quality.FULL_DIM7: Quality.DIMINISHED,
    Quality.POWER: Quality.MAJOR,
    Quality.DOM7_FLAT9: Quality.DOMINANT7,
    Quality.DOM7_SHARP9: Quality.DOMINANT7,
    Quality.DOM7_SHARP11: Quality.DOMINANT7,
    Quality.ALTERED_DOMINANT: Quality.DOMINANT7,
    Quality.PHRYGIAN_MAJOR: Quality.MAJOR,
    Quality.LYDIAN_AUG: Quality.AUGMENTED,
}


def _resolve_type_idx(quality: Quality) -> int:
    """Map any Quality to a valid HMM type index, with fallback."""
    idx = _QUALITY_TO_TYPE.get(quality)
    if idx is not None:
        return idx
    fallback = _QUALITY_FALLBACK.get(quality, Quality.MAJOR)
    return _QUALITY_TO_TYPE[fallback]

# ---------------------------------------------------------------------------
# Weight Loading
# ---------------------------------------------------------------------------

_WEIGHTS_DIR = Path(__file__).parent / "weights"


def _load_weights():
    """Load trained HMM weights from files."""
    pnote_path = _WEIGHTS_DIR / "pnote_full.txt"
    pchange_path = _WEIGHTS_DIR / "pchange_full.npy"

    if not pnote_path.exists() or not pchange_path.exists():
        raise FileNotFoundError(
            f"Trained weights not found in {_WEIGHTS_DIR}. "
            "Run scripts/train_full_modes.py first."
        )

    # pnote: shape [12, 12] — pnote[pitch_offset, chord_type]
    #   pitch_offset = (pitch_class - chord_root) % 12, chord_type in 0..11 (see TYPE_TO_QUALITY)
    pnote = np.loadtxt(pnote_path)

    # pchange: shape [12, 12, 12] — pchange[type_prev, root_interval, type_next]
    #   root_interval = (root_next - root_prev) % 12
    pchange = np.load(pchange_path)

    return pnote, pchange


# Load once at module level
PNOTE, PCHANGE = _load_weights()

# Pre-compute log versions for Viterbi (add small epsilon to avoid log(0))
_EPS = 1e-8
LOG_PNOTE = np.log(np.clip(PNOTE, _EPS, 1.0))
LOG_PCHANGE = np.log(np.clip(PCHANGE, _EPS, 1.0))

# ---------------------------------------------------------------------------
# Universal Modal Priors (Layer 2)
# ---------------------------------------------------------------------------

# Modes whose interval sets contain microtonal (non-integer-semitone) steps.
# The HMM operates on 12 pitch classes, so `_init_modal_priors` snaps such
# steps to the nearest semitone — e.g. ARABIC_SIKAH [0,1.5,3.5,5,7,8.5,10.5]
# collapses to NATURAL_MINOR's {0,2,3,5,7,8,10}. These modes are therefore
# silently misrepresented in the prior tables; they are kept in MODES_LIST
# for the Layer-1 (chord) Viterbi, which works on melody pitch classes
# directly, but Layer-2 (key) detection for them is unreliable. Populated by
# `_init_modal_priors`; read by tests and diagnostics.
_MICROTONAL_MODES: set[Mode] = set()


def _init_modal_priors():
    """Dynamically build priors for all 78 modes."""
    # ν: P(chord_type | key_type)
    type_priors = np.full((N_KEY_TYPES, N_TYPES), 0.05)
    # κ: P(root_offset | key_type)
    offset_logs = np.full((N_KEY_TYPES, N_TONES), math.log(0.01))
    
    # Chord type definitions (3rd, 5th, 7th, 9th) for compatibility checking
    type_intervals = [
        (4, 7, None, None), # Major
        (3, 7, None, None), # Minor
        (3, 6, None, None), # Dim
        (4, 8, None, None), # Aug
        (2, 7, None, None), # sus2
        (5, 7, None, None), # sus4
        (4, 7, 11, None),   # Major7
        (3, 7, 10, None),   # Minor7
        (4, 7, 10, None),   # Dominant7
        (4, 7, 11, 2),      # Major9
        (3, 7, 10, 2),      # Minor9
        (4, 7, None, 2),    # Add9
    ]

    for m_idx, mode in enumerate(MODES_LIST):
        intervals = get_mode_intervals(mode)
        # Detect microtonal (non-integer-semitone) intervals. The HMM Layer-1
        # (chord) state space is 12-TET only, but Layer 2 (key) priors can still
        # represent the quarter-tone colour via fuzzy membership (see below).
        is_microtonal = any(abs(iv - round(iv)) > 0.01 for iv in intervals)
        if is_microtonal:
            _MICROTONAL_MODES.add(mode)

        # Build the 12-TET pitch-class membership of the mode. Integer steps get
        # full membership (1.0); a quarter-tone step like 1.5 splits its
        # membership 0.5/0.5 between pc 1 and pc 2. This is the 24-EDO-aware
        # replacement for the old `round(iv) % 12` snap: a neutral 3rd (3.5) is
        # now "half minor 3rd + half major 3rd" instead of being forced to one,
        # so Layer 2 can distinguish e.g. ARABIC_SIKAH from NATURAL_MINOR (whose
        # 3rd is a pure minor 3rd). Layer 1 still emits 12-TET chords only — the
        # fuzzy weights live in the *key* prior table (KEY_OFFSET_LOG), which
        # never has to produce a sound, only a likelihood. Note: this does NOT
        # make the HMM synthesize quarter-tone pitches in the output; it only
        # preserves the mode's distinctness on Layer 2 detection. The output
        # chords remain 12-TET (a known limitation, see _warn_mode_limitations).
        pc_weights: dict[int, float] = {}
        for iv in intervals:
            iv_mod = iv % 12.0
            lo = int(math.floor(iv_mod)) % 12
            frac = iv_mod - math.floor(iv_mod)
            if frac < 0.01:
                pc_weights[lo] = pc_weights.get(lo, 0.0) + 1.0
            elif frac > 0.99:
                hi = (lo + 1) % 12
                pc_weights[hi] = pc_weights.get(hi, 0.0) + 1.0
            else:
                hi = (lo + 1) % 12
                pc_weights[lo] = pc_weights.get(lo, 0.0) + (1.0 - frac)
                pc_weights[hi] = pc_weights.get(hi, 0.0) + frac
        scale_pcs = set(pc_weights)

        # 1. Root offsets: high weight for notes in scale, preferring the tonic
        # (offset 0). For microtonal modes the weight is proportional to the
        # fuzzy membership, so a quarter-tone step contributes half-weight to
        # each of its two 12-TET neighbours (e.g. sikah's neutral 3rd boosts
        # both pc 3 and pc 4 by 0.5x, rather than snapping to one).
        total_non_tonic = sum(pc_weights.values()) - pc_weights.get(0, 0.0)
        for pc in scale_pcs:
            wt = pc_weights[pc]
            if pc == 0:
                offset_logs[m_idx, pc] = math.log(0.25)
            else:
                # proportional to membership, normalized over non-tonic weight
                offset_logs[m_idx, pc] = math.log(0.55 * wt / total_non_tonic)

        # 2. Chord types: prior reflects how completely the chord's tones fit
        #    the mode (built on the tonic, offset 0). The score is the RATIO of
        #    matched chord tones to total chord tones — NOT an absolute count.
        #    (Absolute counts were unreachable for triads: a triad has only a
        #    3rd and 5th, max 2 matches, so the old `fit_score >= 3` threshold
        #    could never fire for triads — they were stuck at 0.05-0.10 while
        #    7ths/9ths got 0.25, inverting the intended "prefer basic triads
        #    then 7ths then 9ths" preference and biasing the key layer toward
        #    extended chords.)
        for t_idx, (third, fifth, seventh, ninth) in enumerate(type_intervals):
            tones = [third, fifth]
            if seventh is not None:
                tones.append(seventh)
            if ninth is not None:
                tones.append(ninth)
            matched = sum(1 for x in tones if x in scale_pcs)
            total = len(tones)
            ratio = matched / total

            if ratio >= 0.999:  # fully diatonic on the tonic
                if t_idx < 3:    # Major, Minor, Diminished triads
                    type_priors[m_idx, t_idx] = 0.35
                elif t_idx < 9:  # Augmented, sus, 7ths
                    type_priors[m_idx, t_idx] = 0.25
                else:            # 9ths, add9
                    type_priors[m_idx, t_idx] = 0.15
            elif ratio >= 0.66:
                type_priors[m_idx, t_idx] = 0.10

            # Special case for Dominant 7 (often used even if not strictly diatonic)
            if t_idx == 8 and 4 in scale_pcs and 10 in scale_pcs:
                type_priors[m_idx, t_idx] = 0.20

        # Normalize priors (DEPRECATED: Normalization per-mode causes pentatonic scale-size bias
        # by boosting incompatible chords in smaller scales).
        # type_priors[m_idx] /= type_priors[m_idx].sum()

    return type_priors, offset_logs

KEY_TYPE_PRIOR, KEY_OFFSET_LOG = _init_modal_priors()
LOG_KEY_TYPE_PRIOR = np.log(KEY_TYPE_PRIOR + _EPS)


def _init_mode_priors() -> np.ndarray:
    """Build prior log-probabilities for each mode based on its category.

    Two-stage: (1) assign a base prior from the mode's MODE_DATABASE category;
    (2) apply alias-group consistency so that two names declared as the same
    scale (see theory.modes._INTENTIONAL_ALIASES) are treated identically by
    Layer 2. Without stage 2 the database contradicts itself: e.g. YAMAN is
    declared an alias of LYDIAN, yet Yaman sat in the −10 bucket while Lydian
    was at 0.0 — so requesting Yaman would still detect as Lydian/Major on
    free-detection material, and a Yaman/Lydian ambiguity could never resolve
    to Yaman. The rule is purely a consistency fix: within each alias group,
    every member inherits the BEST (highest) prior of the group, so the
    database's own "these are the same scale" declarations are honoured.
    """
    # Modes whose MODE_DATABASE category understates their harmonic centrality.
    # Lydian is a core church mode but is tagged "Film"; without this override
    # it lands in the −10 bucket and collapses to Major on free detection,
    # losing the raised-4th colour even when explicitly requested.
    COMMON_OVERRIDES = {Mode.LYDIAN}

    priors = np.zeros(N_KEY_TYPES)
    for m_idx, mode in enumerate(MODES_LIST):
        defn = MODE_DATABASE.get(mode)
        if not defn:
            category = "Exotic"
        else:
            category = defn.category

        if mode in COMMON_OVERRIDES or category == "Common":
            priors[m_idx] = 0.0      # High priority (Major, Minor, Lydian)
        elif category in ("Jazz", "Blues", "Symmetric"):
            priors[m_idx] = -3.0     # Medium priority
        elif category in ("Atmospheric", "Verdi", "Classical", "Pentatonic"):
            priors[m_idx] = -5.0     # Low priority
        else:
            priors[m_idx] = -10.0    # Very low priority (Ethnic/Exotic like Pelog, Slendro, Messiaen)

    # Alias-group consistency: every member of a declared alias group inherits
    # the group's best (highest) prior. Imports _INTENTIONAL_ALIASES lazily to
    # avoid a module-load cycle. This lifts e.g. YAMAN to Lydian's 0.0,
    # SUPER_LOCRIAN to Altered's −3.0, ACOUSTIC_MAJOR to Lydian Dominant's
    # −3.0, and the Messiaen modes to their Symmetric/Jazz peers' levels —
    # removing the internal contradiction where two names for the same scale
    # received different Layer-2 priors.
    from melodica.theory.modes import _INTENTIONAL_ALIASES
    mode_to_idx = {m: i for i, m in enumerate(MODES_LIST)}
    for group in _INTENTIONAL_ALIASES:
        members = [mode_to_idx[m] for m in group if m in mode_to_idx]
        if len(members) < 2:
            continue
        best = max(priors[i] for i in members)
        for i in members:
            priors[i] = best

    return priors

MODE_PRIORS = _init_mode_priors()

# Warn once at import time about microtonal modes. Their quarter-tone colour
# is now PRESERVED on Layer 2 via fuzzy PC membership (a 1.5-semitone step
# splits 0.5/0.5 between its two 12-TET neighbours instead of snapping to one),
# so they are distinguishable from neighbouring common scales. They still
# cannot produce quarter-tone pitches in the OUTPUT (Layer 1 emits 12-TET
# chords only); this is the remaining limitation. The warning is informational.
if _MICROTONAL_MODES:
    warnings.warn(
        "CoupledHMMHarmonizer: the following modes contain microtonal "
        "intervals; their Layer-2 distinctness is preserved via fuzzy 24-EDO "
        "membership, but output chords remain 12-TET (quarter-tone pitches "
        "are not synthesized): "
        + ", ".join(sorted(m.value for m in _MICROTONAL_MODES)),
        stacklevel=1,
    )


# ---------------------------------------------------------------------------
# Modal cadence map (Layer 1 penultimate attraction)
# ---------------------------------------------------------------------------
# Characteristic pre-cadential scale degree (as a semitone offset from the
# tonic) for each mode. The Layer-1 Viterbi biases the penultimate step toward
# (key_root + PENULTIMATE_DEGREE[mode]) % 12 instead of a hardcoded dominant.
# A hardcoded +7 (V->I) is only correct for major/common-minor harmony; for
# Phrygian the characteristic cadence is bII->i (+1), for Dorian IV->i (+5),
# for Mixolydian bVII->I (+10), etc. Without this, every modal piece is
# pulled toward a major V-I and loses its color. See _hmm_helpers.MODAL_CADENCES
# for the full cadence grammar (used by functional_hmm; coupled_hmm only needs
# the penultimate degree here).
PENULTIMATE_DEGREE: dict[Mode, int] = {
    # V -> I / V -> i  (authentic cadence)
    Mode.MAJOR: 7, Mode.IONIAN: 7,
    Mode.NATURAL_MINOR: 7, Mode.AEOLIAN: 7, Mode.AEOLIAN_BB7: 7,
    Mode.HARMONIC_MINOR: 7, Mode.MELODIC_MINOR: 7,
    Mode.LYDIAN: 7,
    # bII -> i  (Phrygian / double-harmonic / Neapolitan cadence)
    Mode.PHRYGIAN: 1, Mode.PHRYGIAN_DOMINANT: 1, Mode.BAYATI: 1,
    Mode.DOUBLE_HARMONIC: 1, Mode.DOUBLE_HARM_MAJOR: 1,
    Mode.BYZANTINE: 1, Mode.PERSIAN: 1, Mode.HUNGARIAN_MINOR: 1,
    Mode.GYPSY: 1, Mode.SPANISH_8_TONE: 1,
    Mode.NEAPOLITAN_MINOR: 1, Mode.NEAPOLITAN_MAJOR: 1,
    # IV -> i  (Dorian / modal plagal cadence)
    Mode.DORIAN: 5, Mode.DORIAN_PENTATONIC: 5, Mode.DORIAN_B2: 5,
    # bVII -> I  (Mixolydian cadence)
    Mode.MIXOLYDIAN: 10, Mode.MIXOLYDIAN_B6: 10,
}
# Fallback for modes not listed above: standard dominant (V).
_PENULT_DEFAULT = 7


def _penultimate_degree(mode: Mode) -> int:
    """Characteristic pre-cadential degree offset for a mode."""
    return PENULTIMATE_DEGREE.get(mode, _PENULT_DEFAULT)


# ---------------------------------------------------------------------------
# Coupled HMM Configuration & Harmonizer
# ---------------------------------------------------------------------------

@dataclass
class HMMConfig:
    """Configuration hyperparameters for CoupledHMMHarmonizer."""
    anti_stagnation_penalty: float = 2.0      # Recommended range: [1.0, 4.0]. Penalty for repeating the same chord type consecutively.
    interval_diversity_penalty: float = 1.5   # Recommended range: [0.5, 3.0]. Penalty for repeating the same root motion interval.
    tension_weight: float = 4.0               # Recommended range: [2.0, 8.0]. Weight for the tension-curve stability bias.
    key_coupling_weight: float = 0.5          # Recommended range: [0.1, 4.0]. Feedback strength from Layer 2 (Key) to Layer 1 (Chords).
    tonic_bias: float = 2.0                   # Recommended range: [1.0, 4.0]. Starting bias favoring the initial scale root.
    epsilon: float = 1e-8                     # Small constant to prevent log(0) errors.
    emission_weight: float = 20.0             # Recommended range: [1.0, 24.0]. Scaling factor for the active note log emissions. NOTE: emissions are normalized to ~[-1,0] (divided by total note weight), so they must be scaled up to compete with the structural biases below (tension/anti-stagnation/coupling on a log scale of 2-4). Too low → chords ignore the melody; ~20 keeps harmonization tracking the notes while structure still breaks ties.
    tonic_end_bias: float = 2.5               # Recommended range: [1.0, 5.0]. Cadential attraction to the key tonic on the final step.
    dominant_penultimate_bias: float = 1.5    # Recommended range: [0.5, 3.0]. Cadential attraction to the dominant root on the penultimate step.
    cadence_transition_bias: float = 4.5      # Recommended range: [0.0, 8.0]. Per-step bonus added to the *transition* (not emission) for the key-specific penultimate→tonic root motion at the FINAL step. This is the structural driver of the V→I / bII→i / IV→i / bVII→I cadence: because the melody's final pitch is rarely the tonic, emission alone resists resolving to the tonic chord, and additive biases (tonic_end_bias) saturate at ~50-60% reliability. Folding the reward into the transition makes the cadential resolution a path property (chord→chord) rather than a per-frame preference, so it wins regardless of melody contour. Scaled with the mode's characteristic penultimate degree (see _penultimate_degree).
    extended_chord_penalty: float = 1.0       # Recommended range: [0.0, 2.0]. Penalty for extended/9th chords to prevent their overuse.
    completion_bonus: float | dict = 0.0      # set-completion inductive bias (default 0.0 = off). Scalar λ adds λ to the log-score of every (root,type) whose chord-tone set COVERS all active melody pcs (M ⊆ chord_tones(r,k)) — lets 7ths win when the melody spells them. A dict {type_idx: weight} gives PER-TYPE completion (e.g. {8: 5.0} = dom7-only for blues/funk; unspecified types get no bonus) — uniform bonus can't favor dom7 over maj7, the dict can. Recommended range [2.0, 8.0]. See docs/HARMONIZATION_CEILING.md.
    color_chord_penalty: float = 0.0          # Recommended range: [0.0, 12.0] (~8.0–10.0 to suppress color-chord dominance). Emission penalty for color/non-functional types — diminished, augmented, sus2, sus4 (type idx 2,3,4,5). The trained PNOTE has near-deterministic spikes (PNOTE[2,sus2]≈PNOTE[3,dim]≈PNOTE[4,aug]≈PNOTE[5,sus4]≈1.0); because emissions are scaled by emission_weight (×20) before this penalty applies, a value in the ~8–10 range is needed to overcome a spike advantage, not ~1–2. Penalizing one type alone is whack-a-mole (sus→dim→aug); a flat penalty on all four restores functional major/minor harmony. Leave 0.0 for genres that want color. Opt-in (default 0.0 keeps prior behavior).
    requested_key_bias: float = 6.0           # Recommended range: [2.0, 12.0]. Per-step Layer-2 emission bonus for the exact (root, mode) the caller requested (initial_scale). Honors the composer's mode (prevents collapse of Phrygian/Dorian/Mixolydian to major). The requested mode's MODE_PRIORS penalty is cancelled out for this mode (see _viterbi_keys), so this bonus is the sole arbiter of the requested mode against the (prior-weighted) common modes; it must therefore comfortably exceed a typical per-step offset/type-prior gap to win. Additive, so strong chord evidence can still overcome it; favors modal fidelity over free modulation detection.
    requested_key_mode_bias: float = 2.0      # Recommended range: [0.0, 6.0]. Milder per-step Layer-2 bonus for the requested MODE on any other root, so the harmonization keeps the modality even if the tonal center shifts.


@dataclass
class WeightedNote:
    pitch_class: int
    weight: float


# ---------------------------------------------------------------------------
# Mode-limitation warnings (per-call, covers all mode sources)
# ---------------------------------------------------------------------------

def _is_microtonal_mode(mode: Mode | str) -> bool:
    """True if the mode's interval set contains a non-integer-semitone step.

    Covers every mode source (Mode enum, EXOTIC_SCALE_DATABASE strings,
    Melakarta names) because it inspects the resolved intervals directly,
    not the membership of _MICROTONAL_MODES (which is only populated for the
    78 enum modes during prior building). For enum modes the quarter-tone
    colour is now preserved on Layer 2 via fuzzy membership; for string
    modes (not in MODES_LIST) the colour is lost on both layers.
    """
    try:
        intervals = get_mode_intervals(mode)
    except Exception:
        return False
    return any(abs(iv - round(iv)) > 0.01 for iv in intervals)


def _warn_mode_limitations(scale: Scale, *, force: bool = False) -> None:
    """Warn once per call about modes the HMM cannot faithfully represent.

    Two limitations are surfaced, both for modes NOT in MODES_LIST (the 78
    enum modes that populate Layer 2's state space):

    1. **Unknown-mode limitation.** Layer 2 (key detection) operates over
       MODES_LIST only. A mode that resolves via EXOTIC_SCALE_DATABASE or
       MELAKARTA_NAMES (219 + 72 string modes) is harmonizable on Layer 1
       (chords, which read melody pitch classes directly) but can NEVER be
       detected as itself on Layer 2 — it is silently mapped to the nearest
       enum (e.g. 'flamenco' -> harmonic_minor). When `force` is True the
       situation is worse: force_key silently falls back to MAJOR (m_idx=0).

    2. **Microtonal limitation (string modes only).** String modes with
       non-integer-semitone steps lose their quarter-tone colour entirely
       (Layer 1 has no state for them and Layer 2 cannot see them). Enum
       microtonal modes (ARABIC_SIKAH, etc.) are PRESERVED on Layer 2 via
       fuzzy 24-EDO membership — they are distinguishable from neighbouring
       common scales — but output chords remain 12-TET (no quarter-tone
       pitches synthesized). The remaining limitation for enum microtonal
       modes is output-only.

    The module-level import warning (_MICROTONAL_MODES) covers enum modes;
    this per-call check covers everything the caller actually passed.

    Mode matching is by `.value` (e.g. Mode.MAJOR.value == 'major'), so a
    string mode 'major' is correctly recognised as the MAJOR enum and does
    NOT trigger a spurious warning.
    """
    mode = scale.mode
    name = mode.value if hasattr(mode, "value") else str(mode)
    # Match by value, not identity: Scale accepts both Mode enums and raw
    # strings, and 'major' (str) should match Mode.MAJOR (enum).
    in_modes_list = any(
        (m.value if hasattr(m, "value") else str(m)) == name
        for m in MODES_LIST
    )
    if in_modes_list:
        # Enum mode: microtonal colour is preserved via fuzzy membership
        # (warned at import time); output limitation is informational.
        return
    msgs = []
    msgs.append(
        f"mode {name!r} is not in MODES_LIST (Layer-2 key-detection state "
        f"space); it will be detected as the nearest enum mode, not as itself"
        + ("; force_key will silently fall back to MAJOR" if force else "")
    )
    if _is_microtonal_mode(mode):
        msgs.append(
            f"mode {name!r} has microtonal intervals that are fully lost "
            "(no fuzzy preservation for string modes; output is 12-TET)"
        )
    warnings.warn("; ".join(msgs), stacklevel=3)


# ---------------------------------------------------------------------------
# Coupled HMM Harmonizer
# ---------------------------------------------------------------------------

@dataclass
class CoupledHMMHarmonizer:
    """Hierarchical HMM Harmonizer with Duration and Metric Weighting."""
    beam_width: int = 12
    chord_change: str = "bars"
    bar_grid: BarGrid | None = None
    config: HMMConfig = field(default_factory=HMMConfig)

    def __post_init__(self) -> None:
        # CoupledHMM runs an exact Viterbi over all 1728 states (12x12x12);
        # beam_width is accepted for API compatibility with other engines but
        # has no effect here. Warn (rather than silently ignore) so callers
        # relying on beam pruning are not misled.
        if self.beam_width != 12:
            warnings.warn(
                "CoupledHMMHarmonizer uses exact Viterbi (no beam pruning); "
                "beam_width=%r is ignored." % (self.beam_width,),
                stacklevel=2,
            )

    def harmonize(
        self,
        melody: list[NoteInfo],
        initial_scale: Scale,
        duration_beats: float,
        constraints: list[ChordLabel] | None = None,
        tension_curve: Any | None = None,
        force_key: Scale | tuple[int, Mode | str] | None = None,
        debug: bool = False
    ) -> list[ChordLabel]:
        if not melody:
            return []

        # Warn if the requested mode cannot be faithfully represented by the
        # 78-enum Layer-2 state space (string modes from EXOTIC_SCALE_DATABASE
        # or MELAKARTA_NAMES, plus microtonal modes). See _warn_mode_limitations.
        _warn_mode_limitations(initial_scale)

        # 1. Prepare observations
        change_points = self._get_change_points(duration_beats)
        observations = self._extract_observations(melody, change_points)
        T = len(observations)

        # 1b. Snap constraints to change points
        if constraints and change_points:
            constraints = self._snap_constraints(constraints, change_points)

        # 2. Key sequence resolution (forced or estimated via multi-pass)
        if force_key:
            if isinstance(force_key, Scale):
                f_scale = force_key
            else:
                f_root, f_mode = force_key
                if isinstance(f_mode, str):
                    # Find matching mode enum
                    f_mode = next((m for m in Mode if m.value == f_mode), Mode.MAJOR)
                f_scale = Scale(root=f_root, mode=f_mode)

            # Warn specifically about force_key's silent MAJOR fallback, which
            # is more damaging than the Layer-2 mapping in the free path.
            _warn_mode_limitations(f_scale, force=True)

            # Map the forced scale to root and mode index
            m_idx = MODES_LIST.index(f_scale.mode) if f_scale.mode in MODES_LIST else 0
            key_path = [(f_scale.root, m_idx)] * T
        else:
            # Pass 1: Get initial draft chord sequence (unbiased by key layer)
            draft_chords = self._viterbi_chords(
                observations, initial_scale, change_points, constraints, tension_curve, key_path=None
            )

            # Pass 2: Estimate key center sequence (Layer 2) from initial chords.
            # initial_scale is forwarded so Layer 2 respects the requested mode
            # instead of collapsing modal input to major/minor.
            key_path = self._viterbi_keys(draft_chords, requested_scale=initial_scale, debug=debug)

        # 3. Pass 3: Refined chord sequence, now coupled to key centers
        chord_path = self._viterbi_chords(
            observations, initial_scale, change_points, constraints, tension_curve, key_path=key_path
        )

        # 4. Build result
        result = []
        for i, (root, t_idx) in enumerate(chord_path):
            quality = TYPE_TO_QUALITY[t_idx]

            start = change_points[i]
            dur = (change_points[i + 1] - start) if i + 1 < len(change_points) else duration_beats - start

            result.append(ChordLabel(
                root=root, quality=quality,
                start=round(start, 6), duration=round(dur, 6)
            ))

        return result

    def _viterbi_chords(
        self, 
        obs: list[list[WeightedNote]], 
        scale: Scale,
        change_points: list[float],
        constraints: list[ChordLabel] | None = None,
        tension_curve: Any | None = None,
        key_path: list[tuple[int, int]] | None = None
    ) -> list[tuple[int, int]]:
        """Find most likely chord sequence using 2nd-order state-expanded Viterbi (1728 states)."""
        T = len(obs)
        if T == 0:
            return []

        NEG_INF = -1e12

        # Pre-compute emissions inline (vectorized). This mirrors the reference
        # implementation in _log_emit_chord; the invariant that both agree is
        # locked by tests/test_coupled_hmm.py::TestEmissionParity.
        emit = np.zeros((T, N_TONES, N_TYPES))

        for t_step in range(T):
            wpcs = obs[t_step]
            if not wpcs:
                emit[t_step] = -20.0
                continue
            
            step_emit = np.zeros((N_TONES, N_TYPES))
            total_w = 0.0

            for wn in wpcs:
                off = np.arange(N_TONES, dtype=np.intp)
                off = (wn.pitch_class - off) % N_TONES
                step_emit += wn.weight * LOG_PNOTE[off]
                total_w += wn.weight

            emit[t_step] = (step_emit / (total_w + 1e-6)) * self.config.emission_weight
            
            # Apply extended chord penalty to 9th/add9 chords (indices 9, 10, 11) to prevent overuse
            emit[t_step, :, 9:] -= self.config.extended_chord_penalty

            # Optional color-chord penalty (dim/aug/sus2/sus4 = indices 2..5) — see
            # HMMConfig.color_chord_penalty. Breaks the degenerate PNOTE spikes that
            # otherwise swamp functional major/minor on pentatonic-ish melodies.
            if self.config.color_chord_penalty:
                emit[t_step, :, 2:6] -= self.config.color_chord_penalty

            # Optional set-completion bonus (see HMMConfig.completion_bonus).
            # Reward (root,type) hypotheses whose chord tones cover ALL active
            # melody pcs. completion_bonus may be a scalar λ (uniform across
            # types) or a dict {type_idx: weight} for per-type completion (e.g.
            # dom7-only for blues). Default 0.0 / empty = no change.
            cb = self.config.completion_bonus
            if cb:
                mset = {wn.pitch_class % N_TONES for wn in wpcs}
                cb_map = isinstance(cb, dict)
                for k in range(N_TYPES):
                    w = cb.get(k, 0.0) if cb_map else cb
                    if not w:
                        continue
                    valid = None
                    for m in mset:
                        roots_m = {(m - o) % N_TONES for o in CHORD_NOTES[k]}
                        valid = roots_m if valid is None else (valid & roots_m)
                        if not valid:
                            break
                    for r in (valid or ()):
                        emit[t_step, r, k] += w

        # Tension indices
        STABLE_INDICES = {0, 1, 11}
        UNSTABLE_INDICES = {2, 3, 8}

        # DP table of shape [T, 12, 12, 12] where dimensions are:
        # dp[t, r_curr, k_curr, r_prev]
        # backtrack stores predecessor state's (k_prev, r_prevprev) encoded as: k_prev * 12 + r_prevprev
        dp = np.full((T, 12, 12, 12), NEG_INF)
        backtrack = np.zeros((T, 12, 12, 12), dtype=np.int32)

        # Init step (t = 0)
        init_scores = emit[0].copy()
        if scale.root is not None:
            init_scores[scale.root, :] += self.config.tonic_bias

        if tension_curve:
            tau = tension_curve.tension_at(change_points[0])
            for k in range(N_TYPES):
                if k in UNSTABLE_INDICES:
                    init_scores[:, k] += tau * self.config.tension_weight
                elif k in STABLE_INDICES:
                    init_scores[:, k] += (1.0 - tau) * self.config.tension_weight

        if key_path:
            key_root, key_type = key_path[0]
            for r in range(N_TONES):
                bias = self.config.key_coupling_weight * (
                    KEY_OFFSET_LOG[key_type, (r - key_root) % 12] 
                    + LOG_KEY_TYPE_PRIOR[key_type]
                )
                if T == 1 and r == key_root:
                    bias += self.config.tonic_end_bias
                init_scores[r, :] += bias

        if constraints:
            cp = change_points[0]
            target = next((c for c in constraints if c.start <= cp < c.start + c.duration), None)
            if target:
                t_idx = _resolve_type_idx(target.quality)
                for r in range(N_TONES):
                    for k in range(N_TYPES):
                        if r != target.root or k != t_idx:
                            init_scores[r, k] = NEG_INF

        # Initialize all possible predecessor roots with the same initial score
        for r_prev in range(12):
            dp[0, :, :, r_prev] = init_scores

        # Forward pass
        for t_step in range(1, T):
            cp = change_points[t_step]
            tau = tension_curve.tension_at(cp) if tension_curve else 0.5

            target_chord = None
            if constraints:
                target_chord = next((c for c in constraints if c.start <= cp < c.start + c.duration), None)

            dp_prev_reshaped = dp[t_step - 1]
            dp_new = np.full((12, 12, 12), NEG_INF)

            # Pre-compute the cadence target pair for the FINAL step. The
            # cadence is a chord->chord resolution (penult -> tonic), so it is
            # implemented as a transition-level bonus, NOT an additive emission
            # bias. Additive biases (tonic_end_bias) saturate at ~50-60%
            # reliability because the melody's final pitch is rarely the tonic,
            # so emission alone resists resolving to the tonic chord; folding
            # the reward into the transition makes the cadence a path property
            # that wins regardless of melody contour. Only fires when we have a
            # key_path (i.e. this is the coupled/refined pass), so the draft
            # pass is unaffected.
            cadence_final_pair = None
            if t_step == T - 1 and key_path is not None and T >= 2:
                key_root_f, key_type_f = key_path[t_step]
                penult = _penultimate_degree(MODES_LIST[key_type_f])
                cadence_final_pair = ((key_root_f + penult) % 12, key_root_f % 12)

            for r_prev in range(12):
                for r_curr in range(12):
                    interval = (r_curr - r_prev) % 12

                    # Copy predecessor slice [k_prev, r_prevprev]
                    dp_slice = dp_prev_reshaped[r_prev].copy()

                    # Apply path-dependent interval diversity penalty
                    if t_step >= 2:
                        r_prevprev_penalized = (r_prev - interval) % 12
                        dp_slice[:, r_prevprev_penalized] -= self.config.interval_diversity_penalty

                    # Max over r_prevprev
                    best_r_prevprev = np.argmax(dp_slice, axis=1)
                    max_prevprev = dp_slice[np.arange(12), best_r_prevprev]

                    # Base transition matrix lookup [k_prev, k_curr]
                    trans_base = LOG_PCHANGE[:, interval, :].copy()
                    # Anti-stagnation: penalize a LITERALLY repeated chord
                    # (same root AND same type). Only the root-static case
                    # (interval == 0) is true stagnation; a type repeat across
                    # a changed root (e.g. C major -> F major -> G major, the
                    # I-IV-V backbone) is normal harmony and must NOT be
                    # penalized, or diatonic progressions get pushed off their
                    # own tonic.
                    if interval == 0:
                        np.fill_diagonal(
                            trans_base,
                            trans_base.diagonal() - self.config.anti_stagnation_penalty,
                        )

                    # Cadence transition bonus: at the final step, reward the
                    # characteristic penultimate->tonic root motion (e.g. V->I
                    # in major, bII->i in Phrygian, IV->i in Dorian). Boosts
                    # every (k_prev, k_curr) pair uniformly so the Viterbi
                    # picks the dominant-quality predecessor that best
                    # resolves, rather than hard-coding a single type.
                    if cadence_final_pair is not None and (r_prev, r_curr) == cadence_final_pair:
                        trans_base = trans_base + self.config.cadence_transition_bias

                    # Combine path scores and transitions
                    scores = max_prevprev[:, None] + trans_base
                    
                    # Max over k_prev for each k_curr
                    best_k_prev = np.argmax(scores, axis=0)
                    best_scores = scores[best_k_prev, np.arange(12)]
                    
                    dp_new[r_curr, :, r_prev] = best_scores
                    
                    # Backtrack encoding: k_prev * 12 + r_prevprev
                    best_r_prevprev_for_best_k = best_r_prevprev[best_k_prev]
                    backtrack[t_step, r_curr, :, r_prev] = best_k_prev * 12 + best_r_prevprev_for_best_k

            # Add emissions and step biases
            for r_curr in range(12):
                for k_curr in range(12):
                    score_emit = emit[t_step, r_curr, k_curr]
                    
                    # Tension bias
                    t_bias = 0.0
                    if tension_curve:
                        if k_curr in UNSTABLE_INDICES:
                            t_bias = tau * self.config.tension_weight
                        elif k_curr in STABLE_INDICES:
                            t_bias = (1.0 - tau) * self.config.tension_weight
                            
                    # Key coupling bias
                    coupling_bias = 0.0
                    if key_path:
                        key_root, key_type = key_path[t_step]
                        coupling_bias = self.config.key_coupling_weight * (
                            KEY_OFFSET_LOG[key_type, (r_curr - key_root) % 12] 
                            + LOG_KEY_TYPE_PRIOR[key_type, k_curr]
                        )
                        
                        # Cadential attraction
                        if t_step == T - 1:
                            if r_curr == key_root:
                                coupling_bias += self.config.tonic_end_bias
                        elif t_step == T - 2:
                            # Modal: attract to the characteristic pre-cadential
                            # degree of the current key's mode, not a hardcoded
                            # dominant (V). Phrygian -> bII, Dorian -> IV,
                            # Mixolydian -> bVII, major/minor -> V, etc.
                            penult = _penultimate_degree(MODES_LIST[key_type])
                            if r_curr == (key_root + penult) % 12:
                                coupling_bias += self.config.dominant_penultimate_bias
                        
                    dp_new[r_curr, k_curr, :] += score_emit + t_bias + coupling_bias

            # Constraints filtering
            if target_chord:
                t_idx = _resolve_type_idx(target_chord.quality)
                for r in range(N_TONES):
                    for k in range(N_TYPES):
                        if r != target_chord.root or k != t_idx:
                            dp_new[r, k, :] = NEG_INF

            dp[t_step] = dp_new

        # Backtrack
        best_flat_idx = np.argmax(dp[T - 1])
        r_curr, k_curr, r_prev = np.unravel_index(best_flat_idx, (12, 12, 12))
        
        path = [(r_curr, k_curr)]
        
        for t_step in range(T - 1, 0, -1):
            back_val = backtrack[t_step, r_curr, k_curr, r_prev]
            k_prev = back_val // 12
            r_prevprev = back_val % 12
            
            r_curr, k_curr, r_prev = r_prev, k_prev, r_prevprev
            path.append((r_curr, k_curr))
            
        path.reverse()
        return path

    # ------------------------------------------------------------------
    # Layer 2: Key Viterbi
    # ------------------------------------------------------------------

    def _viterbi_keys(
        self,
        chords: list[tuple[int, int]],
        requested_scale: Scale | None = None,
        debug: bool = False,
    ) -> list[tuple[int, int]]:
        """Find most likely key sequence given chord observations.

        requested_scale: the key the caller asked for (initial_scale in
        harmonize()). When supplied, a Bayesian bias is added to the emissions
        of the matching (root, mode) state so Layer 2 respects the composer's
        intent instead of collapsing to major/minor — while still allowing the
        Viterbi path to modulate away where the evidence is strong. This is
        distinct from force_key, which freezes the path entirely.
        """
        n_s = N_TONES * N_KEY_TYPES  # 24
        T = len(chords)

        STAY_LOG = math.log(0.98)
        SWITCH_LOG = math.log(0.02 / (n_s - 1))
        log_key_priors = np.tile(MODE_PRIORS, N_TONES)

        # If a mode is requested, cancel its prior in the per-step emissions
        # (see the requested_bias block below). The init step also adds
        # log_key_priors on top of emit_all[0], so without cancelling here
        # too the requested mode's prior leaks back in at t=0 and (for an
        # extreme prior) re-introduces the Layer-2 collapse that fix #1
        # was meant to remove. `log_key_priors_cancelled` is what actually
        # feeds the init dp below.
        log_key_priors_cancelled = log_key_priors

        # Transition matrix is a clean Markovian STAY/SWITCH. Mode priors are
        # applied per-step in the emissions (below) and at init, NOT in the
        # transition matrix: adding them only to the off-diagonal (the diagonal
        # was overwritten by fill_diagonal) made the prior ineffective once a
        # key was entered, because STAY_LOG (≈-0.02) dominates SWITCH_LOG
        # (≈-10.75) regardless of the prior. Folding the prior into every
        # emission keeps it acting symmetrically at every step instead.
        trans = np.full((n_s, n_s), SWITCH_LOG)
        np.fill_diagonal(trans, STAY_LOG)

        roots = np.array([c[0] for c in chords])
        ctypes = np.array([c[1] for c in chords])

        key_roots = np.arange(N_TONES)
        key_types = np.arange(N_KEY_TYPES)
        offsets = (roots[:, None] - key_roots[None, :]) % N_TONES  # [T, 12]

        # Emissions carry the per-mode prior so exotic modes are penalized at
        # every step (and rewarded for common modes), symmetrically.
        emit_all = np.empty((T, n_s))
        for kt in range(N_KEY_TYPES):
            emit_all[:, kt::N_KEY_TYPES] = (
                KEY_OFFSET_LOG[kt][offsets]
                + LOG_KEY_TYPE_PRIOR[kt, ctypes[:, None]]
                + MODE_PRIORS[kt]
            )

        # Respect the caller's requested key. Without this, Layer 2 ignores
        # initial_scale and collapses modal input (Phrygian/Dorian/Mixolydian)
        # to major ~100% of the time, because MODE_PRIORS strongly favors
        # major/minor and the chord evidence alone is often ambiguous.
        #
        # This favors modal fidelity over free modulation detection: when the
        # composer explicitly sets a mode (the common case in the album
        # generators), the harmonization should honor that mode rather than
        # silently rewrite it to major. The bias is additive (not a hard
        # constraint), so overwhelmingly strong chord evidence can still
        # overcome it; in practice modulations are detected less aggressively,
        # which is the intended trade-off for modal material.
        requested_bias = np.zeros(n_s)
        if requested_scale is not None and requested_scale.mode in MODES_LIST:
            req_kt = MODES_LIST.index(requested_scale.mode)
            # The requested mode's MODE_PRIORS penalty is stacked AGAINST the
            # requested_key_bias reward. For exotic modes (prior = −10) the
            # penalty dominated the +6 reward, so the requested mode lost to
            # major/minor at every step and was detected ~0% of the time.
            # Cancel the requested mode's own prior everywhere (on every root)
            # so the requested_key_bias / requested_key_mode_bias act as the
            # sole arbiters of the requested mode. Other modes keep their
            # priors, so unrelated exotic scales are still penalized and free
            # modulation detection still works.
            requested_bias[req_kt::N_KEY_TYPES] = -MODE_PRIORS[req_kt]
            # The init step adds log_key_priors on top of emit_all[0], so
            # cancel the requested mode's prior there too — otherwise it
            # leaks back in at t=0 (the per-step cancellation in emit_all
            # only affects t>=0 emissions, but log_key_priors is added once
            # more at init, double-counting the requested mode's prior).
            log_key_priors_cancelled = log_key_priors.copy()
            log_key_priors_cancelled[req_kt::N_KEY_TYPES] = 0.0
            # Add the strong exact-key reward on top of the cancellation, and
            # the milder same-mode-on-other-roots reward elsewhere. These ADD
            # to the (already zeroed) prior, they do not overwrite the
            # cancellation.
            for req_root in range(N_TONES):
                req_state = req_root * N_KEY_TYPES + req_kt
                if req_root == requested_scale.root:
                    # Strong pull toward the exact requested key.
                    requested_bias[req_state] += self.config.requested_key_bias
                else:
                    # Milder pull toward the same mode on any root.
                    requested_bias[req_state] += self.config.requested_key_mode_bias
            emit_all += requested_bias[None, :]

        NEG_INF = -1e9
        backtrack = np.zeros((T, n_s), dtype=np.int32)

        # Apply mode prior log probabilities to initial state
        dp = emit_all[0] + log_key_priors_cancelled

        if debug:
            print("\n[Layer 2 Debug: Top 3 Key Centers per Step]")
            note_names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
            top_indices = np.argsort(dp)[-3:][::-1]
            top_keys = []
            for idx in top_indices:
                kr = idx // N_KEY_TYPES
                kt = idx % N_KEY_TYPES
                mode_name = MODES_LIST[kt].value
                top_keys.append(f"{note_names[kr]} {mode_name} (score: {dp[idx]:.2f})")
            print(f"Step 1: {', '.join(top_keys)}")

        for t_step in range(1, T):
            scores = dp[:, None] + trans
            backtrack[t_step] = np.argmax(scores, axis=0)
            dp = emit_all[t_step] + np.max(scores, axis=0)

            if debug:
                top_indices = np.argsort(dp)[-3:][::-1]
                top_keys = []
                for idx in top_indices:
                    kr = idx // N_KEY_TYPES
                    kt = idx % N_KEY_TYPES
                    mode_name = MODES_LIST[kt].value
                    top_keys.append(f"{note_names[kr]} {mode_name} (score: {dp[idx]:.2f})")
                print(f"Step {t_step + 1}: {', '.join(top_keys)}")

        best_last = int(np.argmax(dp))
        path = [best_last]
        for t_step in range(T - 1, 0, -1):
            path.append(int(backtrack[t_step, path[-1]]))
        path.reverse()

        return [(s // N_KEY_TYPES, s % N_KEY_TYPES) for s in path]

    # ------------------------------------------------------------------
    # Emission helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _log_emit_chord(weighted_pcs: list[WeightedNote], root: int, type_idx: int) -> float:
        """log P(weighted_pitch_classes | chord root, type) with normalization.

        REFERENCE implementation. The hot path in _viterbi_chords computes the
        same quantity vectorized over all (root, type) at once for speed; this
        scalar form is the canonical definition and is the oracle that
        TestEmissionParity checks the vectorized path against. Keep them in sync.
        """
        if not weighted_pcs:
            return -1.0

        log_p = 0.0
        total_weight = 0.0

        for wn in weighted_pcs:
            off = (wn.pitch_class - root) % N_TONES
            weight = wn.weight
            log_p += weight * LOG_PNOTE[off, type_idx]
            total_weight += weight

        # Normalization to keep likelihoods comparable across different densities
        return log_p / (total_weight + 1e-6)

    @staticmethod
    def _log_emit_key(chord: tuple[int, int], key_root: int, key_type: int) -> float:
        """log P(chord | key) using key offset distribution + type prior."""
        cr, ct = chord
        off = (cr - key_root) % N_TONES
        log_off = KEY_OFFSET_LOG[key_type, off]
        log_type = LOG_KEY_TYPE_PRIOR[key_type, ct]
        return log_off + log_type

    # ------------------------------------------------------------------
    # Observation extraction
    # ------------------------------------------------------------------

    def _get_change_points(self, duration: float) -> list[float]:
        if self.bar_grid:
            mode_map = {"bars": "bars", "half": "strong_beats", "beats": "beats"}
            return self.bar_grid.change_points(duration, mode=mode_map.get(self.chord_change, "bars"))

        # Fallback if no bar_grid
        step = 4.0 if self.chord_change == "bars" else 2.0
        pts = []
        t = 0.0
        while t < duration - 0.01:
            pts.append(round(t, 6))
            t += step
        return pts

    @staticmethod
    def _snap_constraints(constraints: list[ChordLabel], change_points: list[float]) -> list[ChordLabel]:
        """Snap constraint start/duration to the nearest change points."""
        if not change_points:
            return constraints
        snapped = []
        for c in constraints:
            # Find nearest change point to constraint start
            best_cp = min(change_points, key=lambda cp: abs(cp - c.start))
            # Find the change point that covers the constraint end
            c_end = c.start + c.duration
            # Pick the first cp >= c_end, or last cp + step
            end_cp = None
            for i, cp in enumerate(change_points):
                if cp >= c_end - 0.01:
                    end_cp = cp
                    break
            if end_cp is None:
                end_cp = c_end
            new_dur = max(end_cp - best_cp, change_points[1] - change_points[0] if len(change_points) > 1 else 4.0)
            snapped.append(ChordLabel(
                root=c.root, quality=c.quality, extensions=c.extensions,
                bass=c.bass, inversion=c.inversion,
                start=round(best_cp, 6), duration=round(new_dur, 6),
            ))
        return snapped

    def _extract_observations(self, melody: list[NoteInfo], change_points: list[float]) -> list[list[WeightedNote]]:
        observations = []
        bpb = self.bar_grid.beats_per_bar if self.bar_grid else 4.0

        for i, cp in enumerate(change_points):
            next_cp = change_points[i + 1] if i + 1 < len(change_points) else float("inf")

            # Use dict to consolidate same pitch classes in this window
            pc_weights: dict[int, float] = {}

            for n in melody:
                n_end = n.start + n.duration
                # Find overlap between note [n.start, n_end] and window [cp, next_cp]
                overlap_start = max(cp, n.start)
                overlap_end = min(next_cp, n_end)

                if overlap_end > overlap_start:
                    active_dur = overlap_end - overlap_start
                    pc = n.pitch % 12

                    # 1. Duration Weighting (sqrt to avoid domination)
                    duration_weight = math.sqrt(active_dur)

                    # 2. Metric Weighting
                    # Calculate position within bar
                    pos_in_bar = self.bar_grid.beat_in_bar(n.start) if self.bar_grid else (n.start % 4.0)

                    metric_weight = 1.0
                    if abs(pos_in_bar) < 0.01: # Beat 1
                        metric_weight = 1.5
                    elif abs(pos_in_bar - (bpb / 2.0)) < 0.01: # Beat 3 (in 4/4)
                        metric_weight = 1.2
                    elif abs(pos_in_bar % 1.0) > 0.01: # Syncopated / Off-beat
                        metric_weight = 0.8

                    weight = duration_weight * metric_weight
                    pc_weights[pc] = pc_weights.get(pc, 0.0) + weight

            obs_list = [WeightedNote(pc, w) for pc, w in pc_weights.items()]
            observations.append(obs_list)

        return observations
