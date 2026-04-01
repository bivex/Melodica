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
    ArpeggiatorGenerator,
    BassGenerator,
    ChordGenerator,
    OstinatoGenerator,
    StrumPatternGenerator,
    FingerpickingGenerator,
    RiffGenerator,
    GrooveGenerator,
    PercussionGenerator,
    PianoRunGenerator,
    GeneratorParams,
    MarkovMelodyGenerator,
    NeuralMelodyGenerator,
    DyadGenerator,
    AmbientPadGenerator,
    CanonGenerator,
    CallResponseGenerator,
    ModernChordPatternGenerator,
    WalkingBassGenerator,
    AlbertiBassGenerator,
    DroneGenerator,
    CountermelodyGenerator,
    SequenceGenerator,
    BluesLickGenerator,
    HocketGenerator,
    TrillTremoloGenerator,
    OrnamentationGenerator,
    FillGenerator,
    PickupGenerator,
    GlissandoGenerator,
    BoogieWoogieGenerator,
    StridePianoGenerator,
    TremoloPickingGenerator,
    TangoGenerator,
    ReggaeSkankGenerator,
    MontunoGenerator,
    AcciaccaturaGenerator,
    PedalBassGenerator,
    RagtimeGenerator,
    PowerChordGenerator,
    BrokenChordGenerator,
    PedalMelodyGenerator,
    BeatRepeatGenerator,
    TremoloStringsGenerator,
    PolyrhythmGenerator,
    WaltzGenerator,
    ChoraleGenerator,
    NebulaGenerator,
    HarmonicsGenerator,
    BendGenerator,
    ClusterGenerator,
    CadenceGenerator,
    SynthBassGenerator,
    SupersawPadGenerator,
    PluckSequenceGenerator,
    StringsLegatoGenerator,
    StringsPizzicatoGenerator,
    BrassSectionGenerator,
    SaxSoloGenerator,
    TrapDrumsGenerator,
    FourOnFloorGenerator,
    BreakbeatGenerator,
    FXRiserGenerator,
    FXImpactGenerator,
    ReharmonizationGenerator,
    ModalInterchangeGenerator,
    VocalChopsGenerator,
    VocalOohsGenerator,
    GuitarLegatoGenerator,
    GuitarTappingGenerator,
    ArrangerGenerator,
    HumanizerGenerator,
    PianoCompGenerator,
    OrganDrawbarsGenerator,
    KeysArpeggioGenerator,
    GuitarStrummingGenerator,
    BassSlapGenerator,
    GuitarSweepGenerator,
    VocalMelismaGenerator,
    VocalAdlibsGenerator,
    ChoirAahsGenerator,
    DrumKitPatternGenerator,
    PercussionEnsembleGenerator,
    ElectronicDrumsGenerator,
    WoodwindsEnsembleGenerator,
    StringsEnsembleGenerator,
    OrchestralHitGenerator,
    LeadSynthGenerator,
    SidechainPumpGenerator,
    VoiceLeadingGenerator,
    CounterpointGenerator,
    MotifDevelopmentGenerator,
    FilterSweepGenerator,
    EuclideanRhythmGenerator,
    BassWobbleGenerator,
)
from melodica.generators.rest import RestGenerator
from melodica.generators.step_seq import StepSequencer
from melodica.generators.dyads_run import DyadsRunGenerator
from melodica.generators.generic_gen import GenericGenerator
from melodica.generators.phrase_container import PhraseContainer
from melodica.generators.phrase_morpher import PhraseMorpher
from melodica.generators.random_note import RandomNoteGenerator
from melodica.generators.motive import MotiveGenerator
from melodica.generators.staccato import StringsStaccatoGenerator
from melodica.harmonize import HMM3Harmonizer, FunctionalHarmonizer
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
    "electric_piano": 4,
    "harpsichord": 6,
    "vibraphone": 11,
    "marimba": 12,
    "organ": 19,
    "accordion": 21,
    "nylon_guitar": 24,
    "guitar": 25,
    "electric_guitar": 27,
    "muted_guitar": 28,
    "acoustic_bass": 32,
    "bass": 33,
    "electric_bass": 34,
    "violin": 40,
    "viola": 41,
    "cello": 42,
    "contrabass": 43,
    "strings": 48,
    "pizzicato": 45,
    "harp": 46,
    "choir": 52,
    "trumpet": 56,
    "trombone": 57,
    "tuba": 58,
    "brass": 61,
    "sax": 66,
    "oboe": 68,
    "bassoon": 70,
    "clarinet": 71,
    "flute": 73,
    "pad": 89,
    "synth_lead": 80,
    "synth_bass": 38,
    "drums": 0,  # channel 9 (0-indexed) is percussion
    "percussion": 0,
    "timpani": 47,
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

    # Progression
    progression_type: str = "from_list"  # "from_list", "rules", "hmm3", "random"
    progression_list: list[list[int]] | None = None

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

    def generate(self) -> dict[str, Any]:
        """
        Generate full composition. Returns dict of track_name → notes.
        "_chords" key contains the chord progression (list[ChordLabel]).

        Respects config.workflow:
          "generate_all"                  — default; generate progression + all tracks
          "harmonize_melody"              — harmonize config.seed_melody, render other tracks
          "generate_melody_then_harmonize"— generate melody first, harmonize it, render rest
        """
        total_beats = self.config.bars * self.config.time_signature[0]
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
            harmonizer = HMM3Harmonizer()
            chords = (
                harmonizer.harmonize(seed, self.config.scale, total_beats)
                if seed
                else self._generate_progression()
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

            self._generate_all_tracks(chords, tension_curve, result, skip=seed_assigned_name)

        elif self.config.workflow == "generate_melody_then_harmonize":
            # Step 1: render ALL melody tracks with bootstrap progression
            bootstrap_chords = self._generate_progression()
            melody_tracks = [t for t in self.config.tracks if t.generator_type == "melody"]
            if not melody_tracks:
                melody_tracks = [
                    TrackConfig(name="_auto_melody", generator_type="melody", density=0.6)
                ]

            all_melody_notes: list[NoteInfo] = []
            for mel_cfg in melody_tracks:
                mel_notes = self._generate_track(mel_cfg, bootstrap_chords, tension_curve)
                result[mel_cfg.name] = mel_notes
                all_melody_notes.extend(mel_notes)

            # Step 2: harmonize the combined melody output
            harmonizer = HMM3Harmonizer()
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
            self._generate_all_tracks(chords, tension_curve, result, skip_set=melody_names)

        else:
            # "generate_all" — default
            chords = self._generate_progression()
            self._chords = chords
            result["_chords"] = chords

            self._generate_all_tracks(chords, tension_curve, result)

        # ---- Post-processing (all workflows) ----
        from melodica._postprocess import apply_texture_control, apply_velocity_shaping

        apply_texture_control(
            result, self.config.tracks, tension_curve, self.config.use_texture_control
        )
        apply_velocity_shaping(result, self.config.tracks, tension_curve)

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
            if report.clashes_detected > 0:
                import logging

                logging.getLogger(__name__).info(
                    "HarmonicVerifier: %d clashes detected, %d fixed (%d transposed, %d vel-reduced)",
                    report.clashes_detected,
                    report.clashes_fixed,
                    report.notes_transposed,
                    report.notes_velocity_reduced,
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

    def _generate_progression(self) -> list[ChordLabel]:
        """Generate chord progression based on config."""
        scale = self.config.scale
        beats_per_bar = self.config.time_signature[0]
        bars = self.config.bars
        total_beats = bars * beats_per_bar

        # HMM3 harmonizer — beam-search over diatonic + secondary dominants
        if self.config.progression_type == "hmm3":
            harmonizer = HMM3Harmonizer(
                beam_width=self.config.hmm3_beam_width,
                chord_change=self.config.hmm3_chord_change,
                allow_extensions=self.config.hmm3_allow_extensions,
                allow_secondary_dom=self.config.hmm3_allow_secondary_dom,
            )
            contour = self._build_melody_contour(scale, bars, beats_per_bar)
            return harmonizer.harmonize(contour, scale, total_beats)

        # Rules-based harmonizer
        if self.config.progression_type == "rules":
            harmonizer = FunctionalHarmonizer(start_with="I", end_with="I")
            contour = self._build_melody_contour(scale, bars, beats_per_bar)
            return harmonizer.harmonize(contour, scale, total_beats)

        # From list or random — static degree-based
        if self.config.progression_type == "from_list" and self.config.progression_list:
            degrees = random.choice(self.config.progression_list)
        else:
            pool = PROGRESSION_LIBRARY.get(self.config.style, PROGRESSION_LIBRARY["pop"])
            degrees = random.choice(pool)

        # Expand degrees to fill bars
        full_degrees = []
        while len(full_degrees) < bars:
            full_degrees.extend(degrees)
        full_degrees = full_degrees[:bars]

        # Build ChordLabels
        chords = []
        degs = scale.degrees()
        for i, deg in enumerate(full_degrees):
            root_pc = degs[(deg - 1) % len(degs)]
            quality = self._quality_for_degree(deg)
            chords.append(
                ChordLabel(
                    root=root_pc,
                    quality=quality,
                    start=round(i * beats_per_bar, 6),
                    duration=round(beats_per_bar, 6),
                    degree=deg,
                )
            )

        return chords

    def _build_melody_contour(self, scale, bars, beats_per_bar) -> list[NoteInfo]:
        """Build a synthetic melody contour for harmonizers."""
        degs = scale.degrees()
        if not degs:
            return [NoteInfo(pitch=60, start=0.0, duration=beats_per_bar, velocity=80)]

        notes = []
        t = 0.0
        total = bars * beats_per_bar
        prev_pc = int(degs[0])

        while t < total:
            # On strong beats (every 2 beats), use root or chord tone
            beat_in_bar = t % beats_per_bar
            if beat_in_bar < 0.01:
                pc = int(degs[0])  # root on beat 1
            elif beat_in_bar < beats_per_bar / 2 + 0.01:
                pc = int(random.choice(degs[:3])) if len(degs) >= 3 else int(degs[0])
            else:
                pc = int(random.choice(degs))

            pitch = 60 + pc
            while pitch - prev_pc > 7:
                pitch -= 12
            while prev_pc - pitch > 7:
                pitch += 12
            pitch = max(36, min(84, pitch))

            dur = min(2.0, total - t)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=round(max(0.5, dur), 6),
                    velocity=80,
                )
            )
            prev_pc = pitch
            t += 2.0

        return notes

    def _quality_for_degree(self, degree: int) -> Quality:
        """Get chord quality for a degree based on style."""
        if self._style.extensions and degree in (1, 4):
            return Quality.MAJOR7
        elif self._style.extensions and degree in (2, 3, 6):
            return Quality.MINOR7
        elif self._style.extensions and degree == 5:
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
    ) -> list[NoteInfo]:
        """Generate notes for a single track."""
        scale = self.config.scale
        total_beats = self.config.bars * self.config.time_signature[0]
        params = GeneratorParams(density=cfg.density)

        # Obtain generator — from cache, direct instance, or freshly created
        gen = self._get_generator(cfg, params)
        if gen is None:
            return []

        # Apply arrangement pattern; thread context across sections (and across calls)
        pattern = ARRANGEMENT_PATTERNS.get(cfg.arrangement, ["A", "B", "A", "B"])
        notes: list[NoteInfo] = []
        section_length = total_beats / len(pattern)
        ctx = self._track_contexts.get(cfg.name, RenderContext())

        n_sections = len(pattern)
        for i, section in enumerate(pattern):
            section_start = i * section_length
            phrase_pos = i / max(1, n_sections - 1)  # 0.0 at A, 1.0 at last section
            # Rebuild context preserving continuity but updating phrase_position
            ctx = RenderContext(
                prev_pitch=ctx.prev_pitch,
                prev_velocity=ctx.prev_velocity,
                prev_chord=ctx.prev_chord,
                prev_pitches=list(ctx.prev_pitches),
                phrase_position=phrase_pos,
            )
            section_end = section_start + section_length
            section_chords = [c for c in chords if c.start < section_end and c.end > section_start]
            if not section_chords:
                # Use last chord that started before this section ends (not first-ever chord)
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

            section_notes = gen.render(adjusted, scale, section_length, ctx)

            # Phrase memory: store first occurrence, recall on repeat sections
            from melodica._postprocess import handle_phrase_memory

            mem_key = f"{cfg.name}:{section}"
            section_notes = handle_phrase_memory(
                section_notes,
                self._phrase_memory,
                mem_key,
                section,
                i,
                adjusted,
                cfg,
                self.config.scale.root,
            )

            # Offset to global time
            for n in section_notes:
                notes.append(
                    NoteInfo(
                        pitch=n.pitch + cfg.octave_shift * 12,
                        start=round(n.start + section_start, 6),
                        duration=n.duration,
                        velocity=n.velocity,
                        articulation=n.articulation,
                        expression=dict(n.expression),
                    )
                )

            # Thread context to next section — prefer generator's own tracked state
            if hasattr(gen, "_last_context") and gen._last_context is not None:
                ctx = gen._last_context
            elif notes:
                ctx = RenderContext().with_end_state(
                    last_pitch=notes[-1].pitch,
                    last_velocity=notes[-1].velocity,
                    last_chord=section_chords[-1] if section_chords else None,
                )

        # Persist context for next generate() call
        self._track_contexts[cfg.name] = ctx

        # Apply built-in named variations
        for var_name in cfg.variations:
            notes = self._apply_variation(var_name, notes, chords)

        # Apply SDK modifier instances from TrackConfig.modifiers
        from melodica._postprocess import (
            apply_track_modifiers,
            apply_voice_leading,
            apply_non_chord_tones,
        )

        notes = apply_track_modifiers(
            notes, cfg, chords, scale, self.config.time_signature, total_beats
        )

        # Voice leading: smooth out octave leaps between notes
        if self.config.use_voice_leading and cfg.generator_type in (
            "melody",
            "chord",
            "arpeggiator",
        ):
            notes = apply_voice_leading(
                notes, cfg, chords, scale, self.config.time_signature, total_beats
            )

        # Non-chord tones: melody and melodic bass lines
        if self.config.use_non_chord_tones and cfg.generator_type in (
            "melody",
            "bass",
            "arpeggiator",
        ):
            notes = apply_non_chord_tones(notes, cfg, chords, scale)

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
            result[cfg.name] = self._generate_track(cfg, chords, tension_curve)

        for cfg in dependent:
            dep_notes = result.get(cfg.depends_on, [])
            cfg.params[cfg.depends_on_param] = dep_notes
            # Invalidate cache so the generator is rebuilt with injected notes
            self._generator_cache.pop(cfg.name, None)
            result[cfg.name] = self._generate_track(cfg, chords, tension_curve)

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
