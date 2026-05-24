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
idea_tool.py — Full Idea Tool: multi-track composition engine.

Melodica-matching workflows:
1. Generate Master Track + Independent Tracks
2. Use Existing Melody → Harmonize → Render Tracks
3. Generate Melody → Harmonize → Render Tracks

With our improvements:
- Tension curve for macro drama
- Style profiles
- Voice leading
- Non-chord tones
- Texture control
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Any

from melodica.types import (
    BarGrid,
    ChordLabel,
    NoteInfo,
    Scale,
    Mode,
    Quality,
    Track,
    MusicTimeline,
    KeyLabel,
    TimeSignatureLabel,
)
from melodica.generators import (
    MelodyGenerator,
    BassGenerator,
    ChordGenerator,
    GeneratorParams,
    CountermelodyGenerator,
    SequenceGenerator,
)
from melodica.generators.phrase_container import PhraseContainer
from melodica.generators.motive import MotiveGenerator
from melodica.harmonize import HMM3Harmonizer, FunctionalHarmonizer, RuleBasedHarmonizer
from melodica.composer import (
    TensionCurve,
    StyleProfile,
    get_style,
    TextureController,
    NonChordToneGenerator,
    PhraseMemory,
    Phrase,
    get_unified_style,
)
from melodica.modifiers import ModifierContext, VoiceLeadingModifier
from melodica.render_context import RenderContext

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# General MIDI program numbers for common instrument names
# ---------------------------------------------------------------------------
_GM_PROGRAMS: dict[str, int] = {
    "piano": 0,
    "bright_piano": 1,
    "electric_piano": 4,
    "harpsichord": 6,
    "celesta": 8,
    "glockenspiel": 9,
    "music_box": 10,
    "vibraphone": 11,
    "marimba": 12,
    "xylophone": 13,
    "tubular_bells": 14,
    "organ": 19,
    "accordion": 21,
    "harmonica": 22,
    "nylon_guitar": 24,
    "guitar": 25,
    "steel_guitar": 25,
    "jazz_guitar": 26,
    "electric_guitar": 27,
    "muted_guitar": 28,
    "overdrive_guitar": 29,
    "distortion_guitar": 30,
    "acoustic_bass": 32,
    "bass": 33,
    "electric_bass": 34,
    "fretless_bass": 35,
    "slap_bass": 36,
    "synth_bass": 38,
    "violin": 40,
    "viola": 41,
    "cello": 42,
    "contrabass": 43,
    "tremolo_strings": 44,
    "pizzicato": 45,
    "harp": 46,
    "timpani": 47,
    "strings": 48,
    "choir": 52,
    "voice": 54,
    "synth_voice": 54,
    "orchestra_hit": 55,
    "trumpet": 56,
    "trombone": 57,
    "tuba": 58,
    "french_horn": 60,
    "brass": 61,
    "synth_brass": 62,
    "soprano_sax": 64,
    "alto_sax": 65,
    "tenor_sax": 66,
    "baritone_sax": 67,
    "oboe": 68,
    "english_horn": 69,
    "bassoon": 70,
    "clarinet": 71,
    "piccolo": 72,
    "flute": 73,
    "recorder": 74,
    "pan_flute": 75,
    "shakuhachi": 77,
    "whistle": 78,
    "ocarina": 79,
    "synth_lead": 80,
    "pad": 89,
    "dark_pad": 88,
    "synth_fx": 102,
    "sitar": 104,
    "banjo": 105,
    "shamisen": 106,
    "koto": 107,
    "kalimba": 108,
    "bagpipe": 109,
    "fiddle": 110,
    "shanai": 111,
    "tinkle_bell": 112,
    "steel_drums": 114,
    "taiko": 116,
    "drums": 0,  # channel 9 is percussion
    "percussion": 0,
}


# ---------------------------------------------------------------------------
# Track configuration
# ---------------------------------------------------------------------------

# Roman numeral progressions (degree-based)
PROGRESSION_LIBRARY: dict[str, list[list[int]]] = {
    "pop": [
        [1, 5, 6, 4],  # I-V-vi-IV (Let It Be)
        [6, 4, 1, 5],  # vi-IV-I-V (Save Tonight)
        [1, 4, 6, 5],  # I-IV-vi-V
        [4, 5, 1, 6],  # IV-I-vi-V (Someone Like You)
    ],
    "jazz": [
        [2, 5, 1, 6],  # ii-V-I-vi
        [1, 6, 2, 5],  # I-vi-ii-V
        [3, 6, 2, 5],  # iii-vi-ii-V
    ],
    "rock": [
        [1, 4, 1, 5],  # I-IV-I-V
        [1, 5, 4, 5],  # I-V-IV-V
        [6, 4, 5, 5],  # vi-IV-V-V
    ],
    "cinematic": [
        [1, 5, 6, 3],  # I-V-vi-iii
        [1, 4, 5, 1],  # I-IV-V-I
        [6, 5, 4, 5],  # vi-V-IV-V
    ],
}

# Arrangement patterns
ARRANGEMENT_PATTERNS: dict[str, list[str]] = {
    "ABAB": ["A", "B", "A", "B"],
    "AABA": ["A", "A", "B", "A"],
    "AABB": ["A", "A", "B", "B"],
    "ABCD": ["A", "B", "C", "D"],
    "AABC": ["A", "A", "B", "C"],
    "ABAC": ["A", "B", "A", "C"],
    "ABCB": ["A", "B", "C", "B"],
}


@dataclass
class TrackConfig:
    """Configuration for a single track in the Idea Tool."""

    name: str = "melody"
    generator_type: str = "melody"  # "melody", "arpeggiator", "bass", "chord", etc.
    instrument: str = "piano"  # maps to GM program via _GM_PROGRAMS
    arrangement: str = "ABAB"  # arrangement pattern name
    density: float = 0.5
    octave_shift: int = 0
    variations: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    modifiers: list[Any] = field(
        default_factory=list
    )  # SDK modifier instances applied after generation
    # Pass a pre-built generator instance directly (takes priority over generator_type).
    # The instance is used as-is and NOT cached — the caller owns it.
    generator: Any = field(default=None, repr=False)
    # Name of another track whose rendered notes should be injected into this
    # track's generator before rendering (e.g. countermelody needs the melody).
    depends_on: str | None = None
    # Key inside params where the dependency notes are injected.
    depends_on_param: str = "primary_melody"

    # Rhythm Processing
    rhythm_rotate: float = 0.0  # -1.0 to 1.0 (percent of total duration)
    rhythm_dotted: bool = False
    rhythm_rests: float = 1.0  # 1.0 = all notes kept, 0.0 = none
    rhythm_swing: float = 0.5  # 0.5 = straight, 0.66 = triplet swing

    # MPE (MIDI Polyphonic Expression)
    mpe: bool = False  # Allocate per-note channels for expression control


@dataclass
class IdeaPart:
    """A structural section of a composition (e.g., Intro, Verse, Chorus)."""

    name: str = "Part"
    bars: int | None = None
    scale: Scale | None = None
    tempo: int | None = None
    time_signature: tuple[int, int] | None = None
    style: str | None = None
    progression_type: str | None = None
    progression_list: list[list[int]] | None = None
    # Per-part track overrides (None = use track default)
    track_density: dict[str, float] | None = None  # {"TrackName": 0.3}
    track_mute: list[str] | None = None  # ["TrackName1", ...]
    track_velocity_scale: dict[str, float] | None = None  # {"TrackName": 0.5}


@dataclass
class IdeaToolConfig:
    """Full Idea Tool configuration."""

    # Workflow
    workflow: str = (
        "generate_all"  # "generate_all", "harmonize_melody", "generate_melody_then_harmonize"
    )

    # Master track
    scale: Scale = field(default_factory=lambda: Scale(root=0, mode=Mode.MAJOR))
    style: str = "pop"
    bars: int = 8
    time_signature: tuple[int, int] = (4, 4)
    tempo: int = 120

    # Parts (Hierarchical Structure)
    parts: list[IdeaPart] = field(default_factory=list)

    # Progression
    progression_type: str = "coupled_hmm"  # "coupled_hmm", "hmm3", "rules", "from_list", "random"
    progression_list: list[list[int]] | None = None

    # Harmonic risk: continuous 0.0–1.0 controlling how expected vs surprising
    # the chord progression is. Only affects RuleBasedHarmonizer.
    # 0.0 = always pick the most expected next chord, 1.0 = fully random.
    harmonic_risk: float | None = None

    # HMM3 harmonizer options (used when progression_type="hmm3")
    hmm3_beam_width: int = 5
    hmm3_chord_change: str = "bars"  # "bars", "strong_beats", "beats"
    hmm3_allow_extensions: bool = True
    hmm3_allow_secondary_dom: bool = True

    # Tracks
    tracks: list[TrackConfig] = field(default_factory=list)

    # Composer features
    use_voice_leading: bool = False
    use_tension_curve: bool = False
    use_texture_control: bool = False
    use_non_chord_tones: bool = False
    use_harmonic_verifier: bool = True
    dissonance_tolerance: float = 0.5  # 0.0=strict classical, 1.0=permissive jazz

    # MIDI Doctor: run existing diagnostics after generation
    run_doctor: bool = False
    doctor_psycho: bool = True
    doctor_harmonic: bool = True

    # Mixing & Mastering
    use_mixing: bool = True
    use_mastering: bool = True
    target_lufs: float = -14.0

    # For "harmonize_melody" workflow: caller-supplied melody to harmonize
    seed_melody: list[NoteInfo] | None = None


# ---------------------------------------------------------------------------
# Idea Tool Engine
# ---------------------------------------------------------------------------


class IdeaTool:
    """
    Full multi-track composition engine.

    Generates:
    - Master track chord progression
    - Melody track
    - Bass track
    - Chord/pad track
    - Percussion track (optional)
    - Additional tracks (arpeggiator, ostinato, etc.)
    """

    def __init__(self, config: IdeaToolConfig | None = None) -> None:
        self.config = config or IdeaToolConfig()
        self._style = get_style(self.config.style)
        self._chords: list[ChordLabel] = []
        # Per-track render context preserved across generate() calls for continuity
        self._track_contexts: dict[str, RenderContext] = {}
        # Generator cache: created once per track name, reused across generate() calls.
        # Preserves stateful generators (MotiveGenerator, MarkovMelody, PhraseContainer…).
        # Cleared for a track when its TrackConfig changes or depends_on is resolved.
        self._generator_cache: dict[str, Any] = {}

        # Phrase memory: stores generated phrases for recall in later sections
        self._phrase_memory = PhraseMemory()
        self._pan_cc_events: dict[str, list[tuple[float, int, int]]] = {}

    def _get_resolved_parts(self) -> list[IdeaPart]:
        if self.config.parts:
            parts = []
            for i, p in enumerate(self.config.parts):
                parts.append(
                    IdeaPart(
                        name=p.name or f"Part {i + 1}",
                        bars=p.bars if p.bars is not None else self.config.bars,
                        scale=p.scale if p.scale is not None else self.config.scale,
                        tempo=p.tempo if p.tempo is not None else self.config.tempo,
                        time_signature=p.time_signature
                        if p.time_signature is not None
                        else self.config.time_signature,
                        style=p.style if p.style is not None else self.config.style,
                        progression_type=p.progression_type
                        if p.progression_type is not None
                        else self.config.progression_type,
                        progression_list=p.progression_list
                        if p.progression_list is not None
                        else self.config.progression_list,
                    )
                )
            return parts
        else:
            return [
                IdeaPart(
                    name="Main",
                    bars=self.config.bars,
                    scale=self.config.scale,
                    tempo=self.config.tempo,
                    time_signature=self.config.time_signature,
                    style=self.config.style,
                    progression_type=self.config.progression_type,
                    progression_list=self.config.progression_list,
                )
            ]

    def generate(self) -> dict[str, Any]:
        """
        Generate full composition. Returns dict of track_name → notes.
        "_chords" key contains the chord progression (list[ChordLabel]).
        "_tempo_map" key contains the tempo changes if applicable.
        """
        parts = self._get_resolved_parts()

        # Calculate total beats across all parts
        total_beats = 0.0
        for p in parts:
            total_beats += p.bars * p.time_signature[0]
        scale = self.config.scale
        result: dict[str, Any] = {}

        # Remove stale contexts and cached generators for tracks no longer in config
        active_names = {t.name for t in self.config.tracks}
        for stale in set(self._track_contexts) - active_names:
            del self._track_contexts[stale]
        for stale in set(self._generator_cache) - active_names:
            del self._generator_cache[stale]

        # Tension curve (shared across workflows)
        tension_curve = None
        if self.config.use_tension_curve:
            tension_curve = TensionCurve(
                total_beats=total_beats,
                curve_type=self._style.tension_curve,
            )

        # ---- Workflow branching ----
        if self.config.workflow == "harmonize_melody":
            # Caller supplied a melody; harmonize it, then render other tracks
            seed = self.config.seed_melody or []
            bar_grid = BarGrid(numerator=self.config.time_signature[0], denominator=self.config.time_signature[1])
            
            # Use CoupledHMMHarmonizer for advanced tension-aware harmonization
            from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
            harmonizer = CoupledHMMHarmonizer(bar_grid=bar_grid)
            chords = (
                harmonizer.harmonize(seed, self.config.scale, total_beats, tension_curve=tension_curve)
                if seed
                else self._generate_progression(parts)
            )
            self._chords = chords
            result["_chords"] = chords

            # Assign seed melody to the first melody track; all others generate normally
            seed_assigned_name: str | None = None
            if seed:
                first_mel = next(
                    (t for t in self.config.tracks if t.generator_type == "melody"), None
                )
                if first_mel:
                    seed_notes: list[NoteInfo] = list(seed)
                    # Apply octave shift
                    if first_mel.octave_shift:
                        seed_notes = [
                            NoteInfo(
                                pitch=n.pitch + first_mel.octave_shift * 12,
                                start=n.start,
                                duration=n.duration,
                                velocity=n.velocity,
                                articulation=n.articulation,
                                expression=dict(n.expression),
                            )
                            for n in seed_notes
                        ]
                    # Apply named variations
                    for var_name in first_mel.variations:
                        seed_notes = self._apply_variation(var_name, seed_notes, chords)
                    # Apply SDK modifier instances
                    if first_mel.modifiers:
                        _timeline = MusicTimeline(
                            chords=chords,
                            keys=[KeyLabel(scale=scale, start=0, duration=total_beats)],
                            time_signatures=[
                                TimeSignatureLabel(
                                    numerator=self.config.time_signature[0],
                                    denominator=self.config.time_signature[1],
                                    start=0,
                                )
                            ],
                        )
                        _mctx = ModifierContext(
                            duration_beats=total_beats,
                            chords=chords,
                            timeline=_timeline,
                            scale=scale,
                        )
                        for mod in first_mel.modifiers:
                            if hasattr(mod, "modify"):
                                try:
                                    seed_notes = mod.modify(seed_notes, _mctx)
                                except Exception:
                                    logger.debug(
                                        "Modifier %s failed on seed melody, skipping",
                                        type(mod).__name__,
                                        exc_info=True,
                                    )
                    result[first_mel.name] = seed_notes
                    seed_assigned_name = first_mel.name

            self._generate_all_tracks(chords, tension_curve, result, parts, skip=seed_assigned_name)

        elif self.config.workflow == "generate_melody_then_harmonize":
            # Step 1: render ALL melody tracks with bootstrap progression
            bootstrap_chords = self._generate_progression(parts)
            melody_tracks = [t for t in self.config.tracks if t.generator_type == "melody"]
            if not melody_tracks:
                melody_tracks = [
                    TrackConfig(name="_auto_melody", generator_type="melody", density=0.6)
                ]

            all_melody_notes: list[NoteInfo] = []
            for mel_cfg in melody_tracks:
                mel_notes = self._generate_track(mel_cfg, bootstrap_chords, tension_curve, parts)
                result[mel_cfg.name] = mel_notes
                all_melody_notes.extend(mel_notes)

            # Step 2: harmonize the combined melody output
            bar_grid = BarGrid(numerator=self.config.time_signature[0], denominator=self.config.time_signature[1])
            harmonizer = HMM3Harmonizer(bar_grid=bar_grid)
            chords = harmonizer.harmonize(
                sorted(all_melody_notes, key=lambda n: n.start),
                self.config.scale,
                total_beats,
            )
            if not chords:
                chords = bootstrap_chords
            self._chords = chords
            result["_chords"] = chords

            # Step 3: render all non-melody tracks using harmonized chords
            melody_names = {t.name for t in melody_tracks}
            self._generate_all_tracks(chords, tension_curve, result, parts, skip_set=melody_names)

        else:
            # "generate_all" — default
            chords = self._generate_progression(parts)
            self._chords = chords
            result["_chords"] = chords

            self._generate_all_tracks(chords, tension_curve, result, parts)

        # ---- Post-processing (all workflows) ----
        from melodica._postprocess import apply_texture_control, apply_velocity_shaping

        apply_texture_control(
            result, self.config.tracks, tension_curve, self.config.use_texture_control
        )

        # ---- Harmonic verification (cross-track cacophony check) ----
        if self.config.use_harmonic_verifier:
            from melodica.composer.harmonic_verifier import verify_and_fix, VerifierConfig

            verifier_cfg = VerifierConfig(
                dissonance_tolerance=self.config.dissonance_tolerance,
            )
            fixed_tracks, report = verify_and_fix(result, verifier_cfg)
            # Merge fixed tracks back (preserving _chords and other non-note entries)
            for k, v in fixed_tracks.items():
                result[k] = v
            if report.clashes_detected > 0 or report.notes_shaded > 0:
                import logging

                logging.getLogger(__name__).info(
                    "HarmonicVerifier: %d clashes detected, %d fixed (%d transposed, %d vel-reduced), %d shaded",
                    report.clashes_detected,
                    report.clashes_fixed,
                    report.notes_transposed,
                    report.notes_velocity_reduced,
                    report.notes_shaded,
                )

        # ---- Psychoacoustic verification (perceptual masking check) ----
        if self.config.use_harmonic_verifier:
            from melodica.composer.psychoacoustic import psycho_verify, PsychoConfig

            psycho_cfg = PsychoConfig()
            result, psycho_report = psycho_verify(result, psycho_cfg)
            if psycho_report.issues_detected > 0:
                import logging

                logging.getLogger(__name__).info(
                    "PsychoVerifier: %d issues detected, %d fixed "
                    "(%d vel-reduced, %d transposed, %d removed)",
                    psycho_report.issues_detected,
                    psycho_report.issues_fixed,
                    psycho_report.notes_velocity_reduced,
                    psycho_report.notes_transposed,
                    psycho_report.notes_removed,
                )

        # ---- Mixing Desk (Gain staging & Section faders) ----
        if self.config.use_mixing:
            from melodica.shorts_mixing import MixingDesk

            # Part-aware section segmentation mapped to mixing roles
            # First part → Hook (intro energy), last part → Loop (outro fade), middle → Dynamics
            sections = []
            for i, part in enumerate(parts):
                if len(parts) == 1:
                    role = "Dynamics"
                elif i == 0:
                    role = "Hook"
                elif i == len(parts) - 1:
                    role = "Loop"
                else:
                    role = "Dynamics"
                sections.append((role, part.bars, []))

            desk = MixingDesk(niche_cfg={})
            result = desk.apply_mixing(result, sections, self.config.tempo)

            # Apply fade-out on the last part
            total_beats_all = sum(p.bars * p.time_signature[0] for p in parts)
            last_part_beats = parts[-1].bars * parts[-1].time_signature[0]
            fade_start = total_beats_all - min(4.0, last_part_beats * 0.25)
            result = desk.apply_fade_loop_end(
                result, fade_start, fade_beats=min(2.0, last_part_beats * 0.15)
            )

        # ---- Artistic Post-processing (Tension-based swell) ----
        # Apply this AFTER all verifiers so the swells are preserved
        apply_velocity_shaping(result, self.config.tracks, tension_curve)

        # ---- MPE Expression (per-note CC11/CC74/CC1 curves) ----
        from melodica._postprocess import apply_mpe_expression, apply_portamento

        apply_mpe_expression(result, self.config.tracks)
        apply_portamento(result, self.config.tracks)

        # ---- Production Pipeline (humanization, sidechain, dynamics, polyphony, CC) ----
        cc_events: dict[str, list[tuple[float, int, int]]] = {}
        if self.config.use_mixing or self.config.use_mastering:
            from melodica.composer.album_pipeline import (
                _analyze_track,
                _apply_humanization,
                _sidechain_duck,
                _polyphony_limit,
                _shape_dynamics,
                _generate_reverb_sends,
                _generate_entry_fades,
                Mood,
                _MOOD_PROFILES,
            )

            total_dur = sum(p.bars * p.time_signature[0] for p in parts)
            profiles = {}
            for track_cfg in self.config.tracks:
                if track_cfg.name in result and not track_cfg.name.startswith("_"):
                    profiles[track_cfg.name] = _analyze_track(
                        track_cfg.name, result[track_cfg.name], total_dur
                    )

            if profiles:
                # Humanization: timing + velocity jitter for dense tracks
                result = _apply_humanization(result, profiles)

                # Sidechain ducking: bass/pad duck when percussion hits
                result = _sidechain_duck(result, profiles)

                # Mood-aware dynamics shaping
                mood = (
                    Mood.CINEMATIC if self.config.style in ("cinematic", "epic") else Mood.CHAMBER
                )
                mood_profile = _MOOD_PROFILES[mood]
                result = _shape_dynamics(result, mood_profile)

                # Polyphony limiting: cap simultaneous voices at 16
                result = _polyphony_limit(result, profiles, max_voices=16)

                # CC11 expression ramps for late-entering instruments
                entry_cc = _generate_entry_fades(result, profiles, total_dur)
                cc_events.update(entry_cc)

                # CC91 reverb sends (role-based)
                reverb_cc = _generate_reverb_sends(result, profiles, mood_profile)
                for tname, evts in reverb_cc.items():
                    cc_events.setdefault(tname, []).extend(evts)

        # CC11 ramps at part boundaries for muted/unmuted track transitions
        if self.config.parts:
            part_boundary_cc = self._generate_part_transition_cc(parts)
            for tname, evts in part_boundary_cc.items():
                cc_events.setdefault(tname, []).extend(evts)

        if cc_events:
            result["_cc_events"] = cc_events

        # Expose MPE track names for MIDI export
        mpe_track_names = {tc.name for tc in self.config.tracks if getattr(tc, "mpe", False)}
        if mpe_track_names:
            result["_mpe_tracks"] = mpe_track_names

        # ---- Mastering Desk (LUFS target, Multiband Comp, Imaging, Limiter) ----
        if self.config.use_mastering:
            from melodica.shorts_mastering import MasteringDesk

            mastering_desk = MasteringDesk(target_lufs=self.config.target_lufs)
            result, pan_cc_events = mastering_desk.apply_mastering(result)
            self._pan_cc_events = pan_cc_events

        # ---- MIDI Doctor diagnostics (using existing scripts/midi_doctor.py) ----
        if self.config.run_doctor:
            import logging
            from melodica.composer.psychoacoustic import (
                detect_frequency_masking,
                detect_temporal_masking,
                detect_fusion,
                detect_blur,
                detect_register_masking,
                detect_brightness_overload,
            )
            from melodica.composer.harmonic_verifier import detect_clashes, VerifierConfig

            track_data = {
                k: v for k, v in result.items() if not k.startswith("_") and isinstance(v, list)
            }

            psycho_checks = {}
            if self.config.doctor_psycho:
                psycho_checks["frequency_masking"] = detect_frequency_masking(track_data)
                psycho_checks["temporal_masking"] = detect_temporal_masking(track_data)
                psycho_checks["fusion"] = detect_fusion(track_data)
                psycho_checks["blur"] = detect_blur(track_data)
                psycho_checks["register_masking"] = detect_register_masking(track_data)
                psycho_checks["brightness_overload"] = detect_brightness_overload(track_data)

            harmonic_clashes = []
            if self.config.doctor_harmonic:
                hcfg = VerifierConfig(dissonance_tolerance=self.config.dissonance_tolerance)
                harmonic_clashes = detect_clashes(track_data, hcfg)

            psycho_total = sum(len(v) for v in psycho_checks.values())
            total_issues = psycho_total + len(harmonic_clashes)
            result["_doctor_report"] = {
                "psycho_checks": psycho_checks,
                "harmonic_clashes": harmonic_clashes,
                "total_issues": total_issues,
            }
            if total_issues > 0:
                logging.getLogger(__name__).info(
                    "MidiDoctor: %d issues (%d psycho, %d harmonic clashes)",
                    total_issues,
                    psycho_total,
                    len(harmonic_clashes),
                )

        return result

    def get_chords(self) -> list[ChordLabel]:
        """Get the chord progression (call after generate())."""
        return self._chords

    def render_tracks(self) -> dict[str, Track]:
        """
        Generate composition and return fully-wired Track objects (with channel,
        program, volume, pan, instrument_name) ready for export_midi().

        Call this instead of generate() when you need MIDI metadata preserved.
        """
        notes_map = self.generate()
        tracks: dict[str, Track] = {}
        percussion_types = {"percussion", "drums"}

        non_perc_channel = 0
        for i, track_cfg in enumerate(self.config.tracks):
            if track_cfg.name not in notes_map:
                continue
            is_percussion = track_cfg.generator_type in percussion_types
            if is_percussion:
                channel = 9
            else:
                # Skip channel 9 (reserved for percussion); wrap at 16
                channel = non_perc_channel if non_perc_channel < 9 else non_perc_channel + 1
                channel = channel % 16
                non_perc_channel += 1
            program = _GM_PROGRAMS.get(track_cfg.instrument, 0)
            tracks[track_cfg.name] = Track(
                name=track_cfg.name,
                notes=notes_map[track_cfg.name],
                channel=channel,
                program=program,
                instrument_name=track_cfg.instrument,
            )

        return tracks

    # ------------------------------------------------------------------
    # Progression generation
    # ------------------------------------------------------------------

    def _generate_progression(self, parts: list[IdeaPart]) -> list[ChordLabel]:
        """Generate chord progression for all parts."""
        all_chords = []
        current_beat = 0.0

        # Pre-generate tension curve if enabled
        total_beats = sum(p.bars * p.time_signature[0] for p in parts)
        tension_curve = None
        if self.config.use_tension_curve:
            tension_curve = TensionCurve(
                total_beats=total_beats,
                curve_type=self._style.tension_curve,
            )


        for part in parts:
            scale = part.scale
            beats_per_bar = part.time_signature[0]
            bars = part.bars
            part_beats = bars * beats_per_bar
            style_profile = get_style(part.style)
            bar_grid = BarGrid(numerator=part.time_signature[0], denominator=part.time_signature[1])

            # HMM3 harmonizer — beam-search over diatonic + secondary dominants
            if part.progression_type == "hmm3":
                harmonizer = HMM3Harmonizer(
                    beam_width=self.config.hmm3_beam_width,
                    chord_change=self.config.hmm3_chord_change,
                    allow_extensions=self.config.hmm3_allow_extensions,
                    allow_secondary_dom=self.config.hmm3_allow_secondary_dom,
                    bar_grid=bar_grid,
                )
                contour = self._build_melody_contour(scale, bars, beats_per_bar)
                part_chords = harmonizer.harmonize(contour, scale, part_beats)

            # Coupled HMM (Tymoczko/Newman First Principles)
            elif part.progression_type == "coupled_hmm":
                from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
                harmonizer = CoupledHMMHarmonizer(
                    chord_change=self.config.hmm3_chord_change,
                    bar_grid=bar_grid,
                )
                contour = self._build_melody_contour(scale, bars, beats_per_bar)
                part_chords = harmonizer.harmonize(contour, scale, part_beats, tension_curve=tension_curve)

            # Hybrid Coupled HMM (Guided by user constraints)
            elif part.progression_type == "constrained_hmm":
                from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
                from melodica.types import parse_progression
                
                constraints = []
                if part.progression_list:
                    prog_str = " ".join(part.progression_list)
                    constraints = parse_progression(prog_str, scale)

                harmonizer = CoupledHMMHarmonizer(
                    chord_change=self.config.hmm3_chord_change,
                    bar_grid=bar_grid,
                )
                contour = self._build_melody_contour(scale, bars, beats_per_bar)
                part_chords = harmonizer.harmonize(contour, scale, part_beats, constraints=constraints, tension_curve=tension_curve)

            # Rules-based harmonizer
            elif part.progression_type == "rules":
                harmonizer = RuleBasedHarmonizer(
                    start_with="I",
                    end_with="I",
                    harmonic_risk=self.config.harmonic_risk,
                    bar_grid=bar_grid,
                )
                contour = self._build_melody_contour(scale, bars, beats_per_bar)
                part_chords = harmonizer.harmonize(contour, scale, part_beats)

            # From list or random — static degree-based
            else:
                if part.progression_type == "from_list" and part.progression_list:
                    # Support both list of lists (degrees) and list of strings (chord names)
                    first_item = part.progression_list[0]
                    if isinstance(first_item, str):
                        # It's a list of chord names like ["Im7", "IVm7"]
                        from melodica.types import parse_progression
                        part_chords = parse_progression(" ".join(part.progression_list), scale)
                    else:
                        # It's a list of lists of degrees like [[1, 4, 5, 1]]
                        degrees = random.choice(part.progression_list)
                        full_degrees = []
                        while len(full_degrees) < bars:
                            full_degrees.extend(degrees)
                        full_degrees = full_degrees[:bars]

                        part_chords = []
                        degs = scale.degrees()
                        for i, deg in enumerate(full_degrees):
                            root_pc = degs[(deg - 1) % len(degs)]
                            quality = self._quality_for_degree(deg, style_profile)
                            part_chords.append(
                                ChordLabel(
                                    root=root_pc,
                                    quality=quality,
                                    start=round(i * beats_per_bar, 6),
                                    duration=round(beats_per_bar, 6),
                                    degree=deg,
                                )
                            )
                else:
                    pool = PROGRESSION_LIBRARY.get(part.style, PROGRESSION_LIBRARY["pop"])
                    degrees = random.choice(pool)
                    full_degrees = []
                    while len(full_degrees) < bars:
                        full_degrees.extend(degrees)
                    full_degrees = full_degrees[:bars]

                    part_chords = []
                    degs = scale.degrees()
                    for i, deg in enumerate(full_degrees):
                        root_pc = degs[(deg - 1) % len(degs)]
                        quality = self._quality_for_degree(deg, style_profile)
                        part_chords.append(
                            ChordLabel(
                                root=root_pc,
                                quality=quality,
                                start=round(i * beats_per_bar, 6),
                                duration=round(beats_per_bar, 6),
                                degree=deg,
                            )
                        )

            # Shift the start times
            for c in part_chords:
                c.start += current_beat

            all_chords.extend(part_chords)
            current_beat += part_beats

        return all_chords

    def _build_melody_contour(self, scale, bars, beats_per_bar) -> list[NoteInfo]:
        """Build a synthetic melody contour for harmonizers using a smooth random walk."""
        degs = scale.degrees()
        if not degs:
            return [NoteInfo(pitch=60, start=0.0, duration=beats_per_bar, velocity=80)]

        notes = []
        t = 0.0
        total = bars * beats_per_bar

        # Start on root
        current_pitch = 60 + int(degs[0])

        while t < total:
            # On strong beats (every 2 beats), favor triad tones
            beat_in_bar = t % beats_per_bar
            is_strong = beat_in_bar < 0.01 or abs(beat_in_bar - beats_per_bar / 2) < 0.01

            # Simple random walk: step -1, 0, or +1 scale degree
            step = random.choices([-2, -1, 0, 1, 2], weights=[0.1, 0.3, 0.2, 0.3, 0.1])[0]

            # Find current degree index
            current_pc = current_pitch % 12
            if current_pc in degs:
                idx = degs.index(current_pc)
            else:
                # Snap to closest
                idx = min(range(len(degs)), key=lambda i: abs(degs[i] - current_pc))

            new_idx = (idx + step) % len(degs)
            new_pc = int(degs[new_idx])

            # Apply octave crossing
            octave_shift = 0
            if step > 0 and new_pc < current_pc:
                octave_shift = 12
            elif step < 0 and new_pc > current_pc:
                octave_shift = -12

            current_pitch = (current_pitch // 12) * 12 + new_pc + octave_shift

            # Bound the pitch to a reasonable vocal range
            if current_pitch > 79:
                current_pitch -= 12
            elif current_pitch < 55:
                current_pitch += 12

            # If strong beat, try to snap to 1, 3, 5 if we drifted
            if is_strong and new_idx not in (0, 2, 4) and len(degs) >= 5:
                if random.random() < 0.5:
                    new_idx = min((0, 2, 4), key=lambda x: abs(x - new_idx))
                    new_pc = int(degs[new_idx])
                    current_pitch = (current_pitch // 12) * 12 + new_pc

            dur = min(2.0, total - t)
            if not is_strong and random.random() < 0.3:
                dur = min(1.0, total - t)  # occasional passing tones

            notes.append(
                NoteInfo(
                    pitch=current_pitch,
                    start=round(t, 6),
                    duration=round(max(0.5, dur), 6),
                    velocity=80,
                )
            )
            t += dur

        return notes

    def _quality_for_degree(
        self, degree: int, style_profile: StyleProfile | None = None
    ) -> Quality:
        """Get chord quality for a degree based on style."""
        style = style_profile or self._style
        if style.extensions and degree in (1, 4):
            return Quality.MAJOR7
        elif style.extensions and degree in (2, 3, 6):
            return Quality.MINOR7
        elif style.extensions and degree == 5:
            return Quality.DOMINANT7
        elif degree in (1, 4, 5):
            return Quality.MAJOR
        elif degree in (2, 3, 6):
            return Quality.MINOR
        else:
            return Quality.DIMINISHED

    # ------------------------------------------------------------------
    # Track generation
    # ------------------------------------------------------------------

    def _generate_track(
        self,
        cfg: TrackConfig,
        chords: list[ChordLabel],
        tension_curve: TensionCurve | None,
        parts: list[IdeaPart],
    ) -> list[NoteInfo]:
        """Generate notes for a single track across all parts."""
        params = GeneratorParams(density=cfg.density)

        # Obtain generator — from cache, direct instance, or freshly created
        gen = self._get_generator(cfg, params)
        if gen is None:
            return []

        all_notes: list[NoteInfo] = []
        offset_beats = 0.0

        for part in parts:
            scale = part.scale
            part_beats = part.bars * part.time_signature[0]

            # Per-part mute: skip rendering this track in this part entirely
            if part.track_mute and cfg.name in part.track_mute:
                offset_beats += part_beats
                continue

            # Apply arrangement pattern per part
            pattern = ARRANGEMENT_PATTERNS.get(cfg.arrangement, ["A", "B", "A", "B"])
            part_notes: list[NoteInfo] = []
            bpb = part.time_signature[0]
            # Align sections to bar boundaries: distribute bars evenly across sections
            n_sections = len(pattern)
            if part.bars < n_sections:
                # More sections than bars: merge — treat the whole part as one section
                section_bar_counts = [part.bars]
                pattern = [pattern[0]]
                n_sections = 1
            else:
                base_section_bars = max(1, part.bars // n_sections)
                remainder_bars = part.bars - base_section_bars * n_sections
                section_bar_counts = [base_section_bars + (1 if i < remainder_bars else 0) for i in range(n_sections)]
            ctx = self._track_contexts.get(cfg.name, RenderContext())

            section_offset_beats = 0.0
            for i, section in enumerate(pattern):
                section_length = section_bar_counts[i] * bpb
                section_start = offset_beats + section_offset_beats
                phrase_pos = i / max(1, n_sections - 1) if n_sections > 1 else 0.0

                # Rebuild context preserving continuity but updating phrase_position
                ctx = RenderContext(
                    prev_pitch=ctx.prev_pitch,
                    prev_velocity=ctx.prev_velocity,
                    prev_chord=ctx.prev_chord,
                    prev_pitches=list(ctx.prev_pitches),
                    phrase_position=phrase_pos,
                )
                section_end = section_start + section_length

                # Find chords for this section (in global time)
                section_chords = [
                    c for c in chords if c.start < section_end and c.end > section_start
                ]
                if not section_chords:
                    before = [c for c in chords if c.start < section_end]
                    section_chords = [before[-1]] if before else (chords[:1] if chords else [])

                # Adjust chord times to section-local origin; clip durations at section boundary
                adjusted = [
                    ChordLabel(
                        root=c.root,
                        quality=c.quality,
                        start=max(0.0, c.start - section_start),
                        duration=min(c.end, section_end) - max(c.start, section_start),
                        degree=c.degree,
                    )
                    for c in section_chords
                ]

                # Seed the random generator to ensure that repeating sections (e.g., A, A)
                # generate the exact same rhythmic and melodic contours, but perfectly
                # adapted to the current underlying chords.
                import hashlib

                seed_str = f"{cfg.name}:{part.name}:{section}"
                seed_val = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (2**32)
                random.seed(seed_val)

                section_notes = gen.render(adjusted, scale, section_length, ctx)

                # Restore true randomness
                random.seed()

                # Apply Rhythm Processing (Rotation, Dotted, Rests, Swing)
                section_notes = self._apply_rhythm_processing(section_notes, cfg, section_length)

                # Offset to global time (including the part's offset)
                for n in section_notes:
                    part_notes.append(
                        NoteInfo(
                            pitch=n.pitch + cfg.octave_shift * 12,
                            start=round(n.start + section_start, 6),
                            duration=n.duration,
                            velocity=n.velocity,
                            articulation=n.articulation,
                            expression=dict(n.expression),
                        )
                    )

                # Thread context to next section
                if hasattr(gen, "_last_context") and gen._last_context is not None:
                    ctx = gen._last_context
                elif part_notes:
                    ctx = RenderContext().with_end_state(
                        last_pitch=part_notes[-1].pitch,
                        last_velocity=part_notes[-1].velocity,
                        last_chord=section_chords[-1] if section_chords else None,
                    )

                section_offset_beats += section_length

            # Persist context for next generate() call
            self._track_contexts[cfg.name] = ctx

            # Apply built-in named variations (per part notes? Or all notes?)
            # It's better to apply variations per part. But wait, apply_variation expects the whole track?
            # actually apply_variation can operate on slices. We'll do it on part_notes.
            # But we must shift chords to match part_notes start times. Wait, apply_variation doesn't take chords.
            for var_name in cfg.variations:
                # Need to map chords for this part only if variation needs it, but _apply_variation signature uses chords.
                part_chords = [
                    c
                    for c in chords
                    if c.start >= offset_beats and c.start < offset_beats + part_beats
                ]
                part_notes = self._apply_variation(var_name, part_notes, part_chords)

            # Per-part density thinning: reduce notes in sparse sections
            effective_density = cfg.density
            if part.track_density and cfg.name in part.track_density:
                effective_density = part.track_density[cfg.name]
            if effective_density < cfg.density:
                keep_prob = effective_density / cfg.density
                rng = random.Random(hash(f"{cfg.name}:{part.name}:density") & 0xFFFFFFFF)
                part_notes = [n for n in part_notes if rng.random() < keep_prob]

            # Per-part velocity scaling: adjust dynamics per section
            vel_scale = 1.0
            if part.track_velocity_scale and cfg.name in part.track_velocity_scale:
                vel_scale = part.track_velocity_scale[cfg.name]
            if vel_scale != 1.0:
                part_notes = [
                    NoteInfo(
                        pitch=n.pitch,
                        start=n.start,
                        duration=n.duration,
                        velocity=max(1, min(127, int(n.velocity * vel_scale))),
                        articulation=n.articulation,
                        expression=dict(n.expression),
                    )
                    for n in part_notes
                ]

            all_notes.extend(part_notes)
            offset_beats += part_beats

        # The global modifiers (SDK, voice leading, non-chord tones) should operate on the full track.
        from melodica._postprocess import (
            apply_track_modifiers,
            apply_voice_leading,
            apply_non_chord_tones,
        )

        total_beats = offset_beats
        # It's safer to use the global scale for global post-processing, but note that scale changed per part.
        # This is a limitation of the global post-processing.
        scale = self.config.scale

        all_notes = apply_track_modifiers(
            all_notes, cfg, chords, scale, self.config.time_signature, total_beats
        )

        if self.config.use_voice_leading and cfg.generator_type in (
            "melody",
            "chord",
            "arpeggiator",
        ):
            all_notes = apply_voice_leading(
                all_notes, cfg, chords, scale, self.config.time_signature, total_beats
            )

        if self.config.use_non_chord_tones and cfg.generator_type in (
            "melody",
            "bass",
            "arpeggiator",
        ):
            all_notes = apply_non_chord_tones(all_notes, cfg, chords, scale)

        return all_notes

    def _apply_rhythm_processing(
        self, notes: list[NoteInfo], cfg: TrackConfig, total_beats: float
    ) -> list[NoteInfo]:
        """Apply rhythmic processing to a list of notes."""
        if not notes:
            return notes

        import random

        # 1. Rests (Density)
        if cfg.rhythm_rests < 1.0:
            notes = [n for n in notes if random.random() < cfg.rhythm_rests]

        if not notes:
            return []

        # 2. Rotation
        if cfg.rhythm_rotate != 0:
            shift = total_beats * cfg.rhythm_rotate
            rotated = []
            for n in notes:
                new_start = (n.start + shift) % total_beats
                rotated.append(
                    NoteInfo(
                        pitch=n.pitch,
                        start=round(new_start, 6),
                        duration=n.duration,
                        velocity=n.velocity,
                        articulation=n.articulation,
                        expression=dict(n.expression),
                    )
                )
            notes = sorted(rotated, key=lambda x: x.start)

        # 3. Dotted
        if cfg.rhythm_dotted and len(notes) >= 2:
            processed = []
            i = 0
            while i < len(notes):
                if i + 1 < len(notes):
                    n1, n2 = notes[i], notes[i + 1]
                    # If they are adjacent and equal length
                    if (
                        abs(n1.duration - n2.duration) < 0.01
                        and abs((n1.start + n1.duration) - n2.start) < 0.01
                    ):
                        total_dur = n1.duration + n2.duration
                        processed.append(
                            NoteInfo(
                                pitch=n1.pitch,
                                start=n1.start,
                                duration=total_dur * 0.75,
                                velocity=n1.velocity,
                                articulation=n1.articulation,
                                expression=dict(n1.expression),
                            )
                        )
                        processed.append(
                            NoteInfo(
                                pitch=n2.pitch,
                                start=n1.start + total_dur * 0.75,
                                duration=total_dur * 0.25,
                                velocity=n2.velocity,
                                articulation=n2.articulation,
                                expression=dict(n2.expression),
                            )
                        )
                        i += 2
                        continue
                processed.append(notes[i])
                i += 1
            notes = processed

        # 4. Swing
        if cfg.rhythm_swing != 0.5:
            swung = []
            for n in notes:
                # Simple swing: shift notes that start near X.5
                beat_pos = n.start % 1.0
                if 0.4 <= beat_pos <= 0.6:
                    new_start = (n.start // 1.0) + cfg.rhythm_swing
                    swung.append(
                        NoteInfo(
                            pitch=n.pitch,
                            start=round(new_start, 6),
                            duration=n.duration,
                            velocity=n.velocity,
                            articulation=n.articulation,
                            expression=dict(n.expression),
                        )
                    )
                else:
                    swung.append(n)
            notes = swung

        return notes

    def _get_generator(self, cfg: TrackConfig, params: GeneratorParams):
        """
        Return a generator for the given track, applying a three-tier priority:

        1. cfg.generator is set → use it as-is (caller owns the instance; not cached).
        2. cfg.name is already in _generator_cache → return the cached instance.
        3. Otherwise → create via _create_generator, store in cache, return.

        Caching means stateful generators (MotiveGenerator, MarkovMelody,
        PhraseContainer, etc.) survive across multiple generate() calls and keep
        their internal state coherent.
        """
        if cfg.generator is not None:
            return cfg.generator
        if cfg.name in self._generator_cache:
            return self._generator_cache[cfg.name]
        gen = self._create_generator(cfg, params)
        if gen is not None:
            self._generator_cache[cfg.name] = gen
        return gen

    def _generate_all_tracks(
        self,
        chords: list[ChordLabel],
        tension_curve,
        result: dict,
        parts: list[IdeaPart],
        skip: str | None = None,
        skip_set: set[str] | None = None,
    ) -> None:
        """
        Two-phase track rendering that respects inter-track dependencies.

        Phase 1 — independent tracks (depends_on is None):
            Rendered in config order, skipping names in skip/skip_set.

        Phase 2 — dependent tracks (depends_on is set):
            The rendered notes of the referenced track are injected into the
            dependent track's params under depends_on_param before rendering.
            The generator cache entry is invalidated so the generator is
            re-created with the updated params (e.g. CountermelodyGenerator
            receives the actual melody notes instead of None).
        """
        _skip: set[str] = set()
        if skip is not None:
            _skip.add(skip)
        if skip_set is not None:
            _skip |= skip_set

        independent = [
            t for t in self.config.tracks if t.depends_on is None and t.name not in _skip
        ]
        dependent = [
            t for t in self.config.tracks if t.depends_on is not None and t.name not in _skip
        ]

        for cfg in independent:
            result[cfg.name] = self._generate_track(cfg, chords, tension_curve, parts)

        for cfg in dependent:
            dep_notes = result.get(cfg.depends_on, [])
            cfg.params[cfg.depends_on_param] = dep_notes
            # Invalidate cache so the generator is rebuilt with injected notes
            self._generator_cache.pop(cfg.name, None)
            result[cfg.name] = self._generate_track(cfg, chords, tension_curve, parts)

    def _create_generator(self, cfg: TrackConfig, params: GeneratorParams):
        """Create a generator based on track config."""
        from melodica.factory import create_generator

        return create_generator(cfg.generator_type, params, cfg.params)

    def _apply_variation(
        self,
        var_name: str,
        notes: list[NoteInfo],
        chords: list[ChordLabel],
    ) -> list[NoteInfo]:
        """Apply a variation to notes."""
        from melodica.factory import apply_variation

        return apply_variation(var_name, notes)

    def _generate_part_transition_cc(
        self,
        parts: list[IdeaPart],
    ) -> dict[str, list[tuple[float, int, int]]]:
        """Generate CC11 expression ramps at part boundaries where tracks enter or exit."""
        cc_events: dict[str, list[tuple[float, int, int]]] = {}
        offset_beats = 0.0
        fade_beats = 4.0

        for part_idx, part in enumerate(parts):
            part_beats = part.bars * part.time_signature[0]

            for track_cfg in self.config.tracks:
                tname = track_cfg.name

                is_muted_here = part.track_mute is not None and tname in part.track_mute
                was_muted = False
                if part_idx > 0:
                    prev_part = parts[part_idx - 1]
                    was_muted = prev_part.track_mute is not None and tname in prev_part.track_mute

                # Entry: was muted, now unmuted → CC11 fade in
                if was_muted and not is_muted_here:
                    events = []
                    steps = max(4, int(fade_beats / 0.5))
                    for i in range(steps + 1):
                        t = offset_beats + (i / steps) * fade_beats
                        val = int(20 + (80 * i / steps))
                        events.append((round(t, 6), 11, val))
                    events.append((round(offset_beats + fade_beats + 0.01, 6), 11, 100))
                    cc_events.setdefault(tname, []).extend(events)

                # Exit: was unmuted, now muted → CC11 fade out
                elif not was_muted and is_muted_here:
                    events = []
                    steps = max(4, int(fade_beats / 0.5))
                    for i in range(steps + 1):
                        t = offset_beats + (i / steps) * fade_beats
                        val = int(100 - (80 * i / steps))
                        events.append((round(t, 6), 11, val))
                    events.append((round(offset_beats + fade_beats + 0.01, 6), 11, 20))
                    cc_events.setdefault(tname, []).extend(events)

            offset_beats += part_beats

        return cc_events


# ---------------------------------------------------------------------------
# Convenience: quick composition
# ---------------------------------------------------------------------------


def quick_compose(
    style: str = "pop",
    key_root: int = 0,
    bars: int = 8,
    tracks: list[str] | None = None,
) -> dict[str, list[NoteInfo]]:
    """
    One-liner: generate a full composition.

    Returns dict with keys: "melody", "bass", "chords", "percussion" (if requested)
    """
    if tracks is None:
        tracks = ["melody", "bass", "chord"]

    track_configs = [TrackConfig(name=t, generator_type=t, density=0.5) for t in tracks]

    config = IdeaToolConfig(
        style=style,
        scale=Scale(root=key_root, mode=Mode.MAJOR),
        bars=bars,
        tracks=track_configs,
        use_tension_curve=True,
        use_non_chord_tones=True,
    )

    tool = IdeaTool(config)
    return tool.generate()
