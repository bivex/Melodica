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
composer/ — Advanced composition modules.

1. VoiceLeadingEngine    — SATB voice leading with parallel fifth/octave avoidance
2. TensionCurve          — Macro tension/drama planner
3. StyleProfile          — Style conditioning (baroque/pop/jazz/cinematic/edm)
4. NonChordToneGenerator — Passing tones, suspensions, neighbors, pedal
5. TextureController     — Dynamic density automation
6. PhraseMemory          — Motif recall and reuse with transformations
7. ArticulationEngine    — Per-note articulations, CC automation
"""

from melodica.composer.voice_leading import VoiceLeadingEngine, VOICE_RANGES
from melodica.composer.tension_curve import TensionCurve, TensionPhase, TensionPoint
from melodica.composer.style_profiles import StyleProfile, get_style, STYLES
from melodica.composer.non_chord_tones import NonChordToneGenerator
from melodica.composer.texture_controller import TextureController, TextureLevel
from melodica.composer.articulations import ArticulationEngine, ArticulationProfile, PROFILES
from melodica.composer.phrase_memory import PhraseMemory, Phrase, Transform
from melodica.composer.harmonic_awareness import (
    pitch_class_weights,
    guide_tones,
    avoid_notes,
    chord_tone_pcs,
    weight_pitch,
    best_chord_tone,
    guide_tone_resolution,
)
from melodica.composer.candidate_scorer import (
    CandidateScorer,
    ScoringContext,
    pick_best_note,
)
from melodica.composer.unified_style import (
    UnifiedStyle,
    HarmonyProfile,
    MelodyProfile,
    RhythmProfile,
    InstrumentationProfile,
    get_unified_style,
    list_styles,
    register_style,
)
from melodica.composer.psychoacoustic import PsychoEvent, PsychoConfig, PsychoReport
from melodica.composer.harmonic_verifier import ClashEvent, VerifierConfig, VerifierReport
from melodica.composer.diagnostics import diagnose_tracks, DiagnosticReport

__all__ = [
    "VoiceLeadingEngine",
    "VOICE_RANGES",
    "TensionCurve",
    "TensionPhase",
    "TensionPoint",
    "StyleProfile",
    "get_style",
    "STYLES",
    "NonChordToneGenerator",
    "TextureController",
    "TextureLevel",
    "ArticulationEngine",
    "ArticulationProfile",
    "PROFILES",
    "PhraseMemory",
    "Phrase",
    "Transform",
    "pitch_class_weights",
    "guide_tones",
    "avoid_notes",
    "chord_tone_pcs",
    "weight_pitch",
    "best_chord_tone",
    "guide_tone_resolution",
    "CandidateScorer",
    "ScoringContext",
    "pick_best_note",
    "UnifiedStyle",
    "HarmonyProfile",
    "MelodyProfile",
    "RhythmProfile",
    "InstrumentationProfile",
    "get_unified_style",
    "list_styles",
    "register_style",
    "PsychoEvent",
    "PsychoConfig",
    "PsychoReport",
    "ClashEvent",
    "VerifierConfig",
    "VerifierReport",
    "diagnose_tracks",
    "DiagnosticReport",
]
