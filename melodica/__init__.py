# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
melodica/__init__.py — Public API surface.

This is the ONLY file that outside callers should import from.
All internal module structure is an implementation detail.

Public API:
  - Note, NoteInfo, ChordLabel, Quality, Scale, Mode
  - HarmonicFunction, HarmonizationRequest
  - PhraseInstance, StaticPhrase, IdeaTrack, ArrangementSlot
  - harmonize()       — unified entry point (§7)
  - detect_chord()    — single-frame chord detection (§3)
  - detect_chords_from_midi()
  - detect_scale()    — Krumhansl-Schmuckler (§3.3)
  - from_midi(), from_midi_bytes()
  - notes_to_midi(), chords_to_midi()
  - generate_idea()   — Idea Tool pipeline (§9)
  - slots_to_notes()  — flatten arrangement to absolute NoteInfo list
  - VirtualMidiOut    — real-time virtual MIDI port (requires [live])
  - LeadSynthGenerator — melodic lead-line generator (retro/techno/trance/supersaw)
  - CountermelodyGenerator — contrapuntal counter-melody (contrary motion)
  - MelodyGenerator — general-purpose melody facade (stepwise, arpeggiated, mixed)
  - MixingDesk        — Shorts audio mixing (gain staging, section faders, fade)
  - MasteringDesk     — Shorts audio mastering (LUFS normalization, CC10 pan, limiting)
  - VSTPlayer         — VST3/AU plugin host (requires pedalboard)
  - LiveLoopback      — real-time audio loopback (requires [live])
  - MixingDesk        — Shorts audio mixing (gain staging, section faders, fade)
  - MasteringDesk     — Shorts audio mastering (LUFS normalization, CC10 pan, limiting)
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = [
    # Domain types
    "Note",
    "NoteInfo",
    "ChordLabel",
    "Quality",
    "HarmonicFunction",
    "Mode",
    "Scale",
    "HarmonizationRequest",
    "StaticPhrase",
    "PhraseInstance",
    "IdeaTrack",
    "ArrangementSlot",
    # Core operations
    "harmonize",
    "detect_chord",
    "detect_chords_from_midi",
    "detect_scale",
    # MIDI I/O
    "from_midi",
    "from_midi_bytes",
    "notes_to_midi",
    "chords_to_midi",
    # Idea Tool
    "generate_idea",
    "slots_to_notes",
    # Virtual MIDI (requires [live])
    "VirtualMidiOut",
    # Lead & Melody Generators
    "LeadSynthGenerator",
    "MelodyGenerator",
    "CountermelodyGenerator",
    "RhythmicAccentGenerator",
    "AutomationCurve",
    # VST Player (requires pedalboard)
    "VSTPlayer",
    # Live Loopback (requires [live])
    "LiveLoopback",
    # Shorts Audio Production
    "MixingDesk",
    "MasteringDesk",
    "DSPMasteringDesk",
    "NewYorkCompressor",
]

# --- Domain types ---
from melodica.types import (
    ArrangementSlot,
    ChordLabel,
    HarmonicFunction,
    HarmonizationRequest,
    IdeaTrack,
    Mode,
    Note,
    NoteInfo,
    PhraseInstance,
    Quality,
    Scale,
    StaticPhrase,
)

# --- Detection ---
from melodica.detection import (
    detect_chord,
    detect_chords_from_midi,
    detect_scale,
)

# --- MIDI I/O (infrastructure adapter) ---
from melodica.midi import (
    chords_to_midi,
    from_midi,
    from_midi_bytes,
    notes_to_midi,
)

# --- Idea Tool ---
from melodica.idea import generate_idea, slots_to_notes

# --- Virtual MIDI (lazy — optional [live] dependency) ---
try:
    from melodica.virtual_midi import VirtualMidiOut
except ImportError:
    VirtualMidiOut = None  # type: ignore[assignment,misc]

# --- VST Player (lazy — optional pedalboard dependency) ---
try:
    from melodica.vst_player import VSTPlayer
except ImportError:
    VSTPlayer = None  # type: ignore[assignment,misc]

# --- Live Loopback (lazy — optional [live] dependency) ---
try:
    from melodica.live_loopback import LiveLoopback
except ImportError:
    LiveLoopback = None  # type: ignore[assignment,misc]

# --- Shorts Audio Suite (mixing & mastering) ---
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
try:
    from melodica.dsp_mastering import DSPMasteringDesk
    from melodica.ny_compressor import NewYorkCompressor
except ImportError:
    DSPMasteringDesk = None  # type: ignore[assignment,misc]
    NewYorkCompressor = None  # type: ignore[assignment,misc]

# --- Melody Generators ---
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.generators.accent import RhythmicAccentGenerator

# --- Automation ---
from melodica.composer.automation import AutomationCurve


# ---------------------------------------------------------------------------
# §7 — Unified harmonize() entry point
# ---------------------------------------------------------------------------


def harmonize(
    melody: list[Note],
    *,
    key: Scale | None = None,
    engine: int | str = "hmm",
    chord_rhythm: float = 4.0,
    **engine_kwargs: object,
) -> list[ChordLabel]:
    """
    Harmonize a melody and return a chord sequence.

    Parameters
    ----------
    melody:       List of Note objects.
    key:          Target Scale. Auto-detected via Krumhansl-Schmuckler if None.
    engine:       0 / "functional"  → FunctionalEngine  (18th-century)
                  1 / "rules"       → RuleBasedEngine   (Viterbi + rule graph)
                  2 / "adaptive"    → AdaptiveEngine    (heuristic search)
                  3 / "hmm"         → HMMEngine         (Hidden Markov Model, DEFAULT)
                  4 / "coupled"     → CoupledHMMEngine  (Hierarchical coupled HMM)
    chord_rhythm: Beats per chord event (default 4 = one bar at 4/4).
    **engine_kwargs: Forwarded to the engine constructor.

    Returns
    -------
    list[ChordLabel] covering the full melody duration.
    """
    _ENGINE_MAP: dict[str, int] = {
        "functional": 0,
        "rules": 1,
        "rule_based": 1,
        "adaptive": 2,
        "hmm": 3,
        "markov": 3,
        "coupled": 4,
        "coupled_hmm": 4,
    }
    if isinstance(engine, str):
        engine_id = _ENGINE_MAP.get(engine.lower())
        if engine_id is None:
            raise ValueError(
                f"Unknown engine name {engine!r}. "
                f"Use 'functional', 'rules', 'adaptive', 'hmm', 'coupled', or 0/1/2/3/4."
            )
    else:
        engine_id = int(engine)

    # Auto-detect key
    resolved_key: Scale = key if key is not None else detect_scale(melody)

    # Build request and dispatch
    req = HarmonizationRequest(
        melody=melody,
        key=resolved_key,
        engine=engine_id,
        chord_rhythm=chord_rhythm,
        rule_db=engine_kwargs.pop("rule_db", None),  # type: ignore[assignment]
        allow_secondary_dominants=engine_kwargs.pop("allow_secondary_dominants", True),  # type: ignore[assignment]
        allow_borrowed_chords=engine_kwargs.pop("allow_borrowed_chords", False),  # type: ignore[assignment]
    )

    from melodica.engines import build_engine

    eng = build_engine(engine_id, **engine_kwargs)
    return eng.harmonize(req)
