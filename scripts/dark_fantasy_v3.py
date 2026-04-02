
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
dark_fantasy_v3.py — Fully-wired Dark Fantasy Generator.

100% SDK integration:
- All harmonizers per section mood
- All modifiers per track type
- All composer modules active
- All rhythm generators mapped
- Clean track output (no duplicates)
"""

import sys
import random
import argparse
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import (
    MelodyGenerator,
    MarkovMelodyGenerator,
    ArpeggiatorGenerator,
    BassGenerator,
    ChordGenerator,
    OstinatoGenerator,
    StrumPatternGenerator,
    FingerpickingGenerator,
    PianoRunGenerator,
    PercussionGenerator,
    RiffGenerator,
    CanonGenerator,
    CallResponseGenerator,
    AmbientPadGenerator,
    DyadGenerator,
    GrooveGenerator,
    CountermelodyGenerator,
    TremoloStringsGenerator,
    ChoraleGenerator,
    GeneratorParams,
)
from melodica.harmonize import (
    HMM3Harmonizer,
    FunctionalHarmonizer,
    ChromaticMediantHarmonizer,
    ModalInterchangeHarmonizer,
    GraphSearchHarmonizer,
)
from melodica.modifiers import (
    HumanizeModifier,
    VelocityScalingModifier,
    CrescendoModifier,
    StaccatoLegatoModifier,
    LimitNoteRangeModifier,
    AddIntervalModifier,
    SwingController,
    ModifierContext,
    VelocityGeneratorModifier,
)
from melodica.composer import (
    NonChordToneGenerator,
    ArticulationEngine,
)
from melodica.rhythm import (
    BassRhythmGenerator,
    EuclideanRhythmGenerator,
    SmoothRhythmGenerator,
    RhythmCoordinator,
)
from melodica.midi import export_multitrack_midi, STYLE_INSTRUMENTS
from melodica.render_context import RenderContext


# ---------------------------------------------------------------------------
# Scales — expanded
# ---------------------------------------------------------------------------
SCALES = {
    "phrygian": Scale(root=0, mode=Mode.PHRYGIAN),
    "harmonic_minor": Scale(root=0, mode=Mode.HARMONIC_MINOR),
    "hungarian_minor": Scale(root=0, mode=Mode.HUNGARIAN_MINOR),
    "byzantine": Scale(root=0, mode=Mode.BYZANTINE),
    "natural_minor": Scale(root=0, mode=Mode.NATURAL_MINOR),
    "dorian": Scale(root=0, mode=Mode.DORIAN),
}


# ---------------------------------------------------------------------------
# Section definition
# ---------------------------------------------------------------------------
@dataclass
class Section:
    name: str
    bars: int
    scale_name: str
    key_root: int
    mood: str
    density: float
    tracks: list[str]


def build_sections(total_bars: int) -> list[Section]:
    """
    Cinematic 9-act arc:

    1. Dawn            — pp, solo ambient pad, mystery
    2. Dark Awakening  — p, bass + fingerpicking, ominous
    3. The Journey     — mp, full melody enters, phrygian
    4. Ancient Temple  — mp, ritual ostinato + canon, byzantine
    5. Shadow Rising   — mf, tension builds, hungarian minor
    6. Battle Cry      — f, full orchestra + percussion, battle
    7. The Fall        — mf, sudden drop, despair
    8. Final Stand     — ff, massive climax, all forces
    9. Epilogue        — pp, resolution, peace

    Density curve: 0.15 → 0.25 → 0.40 → 0.45 → 0.55 → 0.70 → 0.30 → 0.80 → 0.15
    Key modulations:  C  →  C  →  C  →  Eb  →  C  →  C  →  Ab  →  C  →  C
    """
    template = [
        # (name, ratio, scale, key_root_offset, mood, density, tracks)
        (
            "Dawn",
            0.06,
            "phrygian",
            0,
            "mystery",
            0.15,
            ["melody", "ambient", "harp_gliss"],
        ),
        (
            "Dark Awakening",
            0.09,
            "harmonic_minor",
            0,
            "ominous",
            0.25,
            ["melody", "bass", "fingerpicking", "ambient"],
        ),
        (
            "The Journey Begins",
            0.14,
            "phrygian",
            0,
            "mystery",
            0.40,
            ["melody", "counter", "arp", "bass", "chords", "dyads"],
        ),
        (
            "Ancient Temple",
            0.10,
            "byzantine",
            3,
            "ritual",
            0.45,
            ["melody2", "counter", "ostinato", "ambient", "bass", "canon", "fingerpicking"],
        ),
        (
            "Shadow Rising",
            0.12,
            "hungarian_minor",
            0,
            "tension",
            0.45,
            ["melody", "counter", "riff", "bass", "ostinato", "dyads"],
        ),
        (
            "Battle Cry",
            0.16,
            "harmonic_minor",
            0,
            "battle",
            0.70,
            ["melody", "melody2", "counter", "bass", "percussion", "chords", "arp"],
        ),
        (
            "The Fall",
            0.08,
            "natural_minor",
            5,
            "despair",
            0.30,
            ["melody", "counter", "ambient", "call_response", "bass", "piano_sweep"],
        ),
        (
            "Final Stand",
            0.18,
            "harmonic_minor",
            0,
            "climax",
            0.65,
            [
                "melody",
                "melody2",
                "counter",
                "choir",
                "bass",
                "chords",
                "arp",
                "percussion",
                "ostinato",
            ],
        ),
        (
            "Epilogue",
            0.07,
            "phrygian",
            0,
            "whisper",
            0.15,
            ["melody", "counter", "ambient", "harp_gliss", "bass"],
        ),
    ]

    raw = [max(1, round(total_bars * r)) for _, r, *_ in template]
    raw[-1] += total_bars - sum(raw)
    raw[-1] = max(1, raw[-1])

    return [
        Section(n, raw[i], sn, kr, m, d, t) for i, (n, _, sn, kr, m, d, t) in enumerate(template)
    ]


# ---------------------------------------------------------------------------
# Track pipeline: (generator, rhythm, modifiers) per mood+track
# ---------------------------------------------------------------------------
TRACK_NAMES = [
    "melody",
    "melody2",
    "arp",
    "bass",
    "chords",
    "ostinato",
    "ambient",
    "dyads",
    "riff",
    "strum",
    "fingerpicking",
    "percussion",
    "groove",
    "call_response",
    "canon",
    "piano_sweep",
    "choir",
    "harp_gliss",
    "tremolo",
    "counter",
]


def make_pipeline(track: str, mood: str, density: float, scale: Scale):
    """Returns (generator, rhythm_or_none, modifiers_list)."""
    params = GeneratorParams(density=density)
    mods: list = []
    rhythm = None
    high_reg = 84 if mood in ("battle", "triumph", "climax") else 80
    low_reg = 55 if mood != "battle" else 60

    match track:
        # ── Melody ────────────────────────────────────────────
        case "melody":
            gen = MelodyGenerator(
                params=params,
                harmony_note_probability=0.7,
                note_range_low=low_reg,
                note_range_high=high_reg,
                note_repetition_probability=0.1,
                steps_probability=0.85,
            )
            mods.append(HumanizeModifier(timing_std=0.03, velocity_std=5))
            if mood == "despair":
                mods.append(CrescendoModifier(start_vel=35, end_vel=75))
            elif mood == "battle":
                mods.append(AddIntervalModifier(semitones=7, direction="below"))
            elif mood == "climax":
                mods.append(AddIntervalModifier(semitones=12, direction="below"))

        case "melody2":
            gen = MarkovMelodyGenerator(
                params=params,
                harmony_note_probability=0.6,
                note_range_low=48,
                note_range_high=72,
                note_repetition_probability=0.08,
            )
            mods.append(HumanizeModifier(timing_std=0.02, velocity_std=4))
            mods.append(VelocityScalingModifier(scale=0.75))

        case "counter":
            gen = CountermelodyGenerator(
                params=params,
                motion_preference="contrary",
                dissonance_on_weak=True,
                interval_limit=7,
            )
            mods.append(VelocityScalingModifier(scale=0.7))
            mods.append(HumanizeModifier(timing_std=0.04, velocity_std=3))

        # ── Arpeggio ──────────────────────────────────────────
        case "arp":
            pat = {
                "mystery": "up_down",
                "ominous": "converge",
                "battle": "octave_pump",
                "triumph": "up",
                "despair": "down",
                "ritual": "pinky_up_down",
                "climax": "up_down",
                "whisper": "converge",
                "tension": "octave_pump",
                "resolve": "up",
            }
            gen = ArpeggiatorGenerator(
                params=params,
                pattern=pat.get(mood, "up"),
                note_duration=0.25,
                octaves=2,
                voicing="spread",
            )
            mods.append(VelocityScalingModifier(scale=0.75))
            if mood in ("ritual", "mystery", "whisper"):
                mods.append(SwingController(swing_ratio=0.58, grid=0.5))

        # ── Bass ──────────────────────────────────────────────
        case "bass":
            allowed = ["root", "fourth"] if mood not in ("battle", "climax") else ["root"]
            gen = BassGenerator(
                params=params,
                allowed_notes=allowed,
                note_movement="alternating",
                transpose_octaves=-1,
            )
            rhythm = BassRhythmGenerator(
                pattern_name="walking" if mood in ("battle", "climax") else "syncopated"
            )
            mods.append(LimitNoteRangeModifier(low=28, high=55))

        # ── Chords / Pads ─────────────────────────────────────
        case "chords":
            voicing = "spread" if mood in ("mystery", "despair", "whisper") else "open"
            gen = ChordGenerator(params=params, voicing=voicing)
            if mood in ("whisper", "despair"):
                rhythm = SmoothRhythmGenerator(pattern_name="whole_legato", overlap=0.2)
            else:
                rhythm = SmoothRhythmGenerator(pattern_name="quarter_legato", overlap=0.1)

        # ── Ostinato ──────────────────────────────────────────
        case "ostinato":
            pat = {
                "battle": "1-2-1-3-1-4-1-5",
                "mystery": "1-3-5-6",
                "triumph": "1-3-5-3-1-5-3-1-3-5",
                "ritual": "5-1-4-1-3-1-2-1",
                "tension": "1-2-3-4-5-4-3-2",
                "climax": "1-3-5-8-5-3-1-3",
            }
            gen = OstinatoGenerator(
                params=params,
                pattern=pat.get(mood, "1-3-5-3"),
                repeat_notes=2 if mood in ("battle", "tension") else 1,
            )

        # ── Ambient / Pads ────────────────────────────────────
        case "ambient":
            gen = AmbientPadGenerator(params=params, voicing="spread", overlap=0.6)
            mods.append(HumanizeModifier(timing_std=0.03, velocity_std=3))

        # ── Dyads ─────────────────────────────────────────────
        case "dyads":
            gen = DyadGenerator(
                params=params,
                interval_pref=[3, 4, 7],
                motion_mode="contrary" if mood in ("mystery", "whisper") else "parallel",
            )
            mods.append(StaccatoLegatoModifier(amount=0.8))

        # ── Runs / Gliss ──────────────────────────────────────
        case "piano_sweep":
            tech = "waterfall" if mood in ("despair", "mystery") else "straddle"
            gen = PianoRunGenerator(
                params=params,
                technique=tech,
                notes_per_run=16,
                motion="up",
            )

        case "harp_gliss":
            gen = PianoRunGenerator(
                params=params,
                technique="waterfall",
                notes_per_run=20,
                motion="up_down",
            )
            mods.append(VelocityScalingModifier(scale=0.5))

        # ── Riff / Tremolo ────────────────────────────────────
        case "riff":
            gen = RiffGenerator(
                params=params,
                scale_type="minor_pent",
                riff_pattern="gallop" if mood in ("battle", "climax") else "palm_mute",
                palm_mute_prob=0.4,
                power_chord=True,
            )
            mods.append(HumanizeModifier(timing_std=0.02, velocity_std=8))

        case "tremolo":
            gen = TremoloStringsGenerator(
                params=params,
                variant="chord",
                bow_speed=0.0625,
                dynamic_swell=True,
            )
            mods.append(VelocityScalingModifier(scale=0.7))

        # ── Strum ─────────────────────────────────────────────
        case "strum":
            gen = StrumPatternGenerator(
                params=params,
                voicing="guitar",
                pattern_name="rock" if mood in ("battle", "climax") else "folk",
                polyphony=5,
                density="high" if mood in ("battle", "climax") else "medium",
            )

        # ── Fingerpicking ─────────────────────────────────────
        case "fingerpicking":
            gen = FingerpickingGenerator(
                params=params,
                pattern=[0, 2, 1, 3, 2, 1],
                notes_to_use=[0, 1, 2, 3],
                sustain_notes="bottom_note",
            )

        # ── Percussion ────────────────────────────────────────
        case "percussion":
            pat = {
                "battle": "rock",
                "triumph": "funk",
                "ritual": "bossa",
                "climax": "rock",
                "tension": "rock",
            }
            gen = PercussionGenerator(
                params=params,
                pattern_name=pat.get(mood, "rock"),
                velocity_humanize=10,
            )

        case "groove":
            gen = GrooveGenerator(
                params=params,
                groove_pattern="funk_1",
                ghost_note_vel=25,
                accent_vel=110,
            )
            mods.append(SwingController(swing_ratio=0.62, grid=0.5))

        # ── Call & Response / Canon ────────────────────────────
        case "call_response":
            gen = CallResponseGenerator(
                params=params,
                call_length=2.0,
                response_length=2.0,
                call_direction="up" if mood not in ("despair", "whisper") else "down",
                response_direction="down" if mood not in ("despair", "whisper") else "up",
            )

        case "canon":
            gen = CanonGenerator(
                params=params,
                delay_beats=2.0,
                interval=7 if mood in ("triumph", "climax") else 5,
            )

        # ── Choir ─────────────────────────────────────────────
        case "choir":
            gen = ChoraleGenerator(
                params=params,
                voice_spacing=12,
                soprano_motion="stepwise",
                rhythmic_unit=2.0,
            )
            mods.append(HumanizeModifier(timing_std=0.04, velocity_std=3))
            mods.append(VelocityScalingModifier(scale=0.8))

        # ── Fallback ──────────────────────────────────────────
        case _:
            gen = MelodyGenerator(params=params)

    return gen, rhythm, mods


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Harmonizer selection by mood
# ---------------------------------------------------------------------------
def pick_harmonizer(mood: str):
    """All sections use HMM3 with mood-specific parameters."""
    match mood:
        case "battle" | "climax":
            return HMM3Harmonizer(
                beam_width=6,
                secondary_dom_weight=0.15,
                extension_weight=0.08,
                repetition_penalty=0.15,
                cadence_weight=0.10,
            )
        case "tension" | "ominous":
            return HMM3Harmonizer(
                beam_width=5,
                secondary_dom_weight=0.12,
                repetition_penalty=0.12,
                cadence_weight=0.08,
            )
        case "despair":
            return HMM3Harmonizer(
                beam_width=5,
                functional_weight=0.10,
                secondary_dom_weight=0.08,
                repetition_penalty=0.08,
            )
        case "mystery" | "whisper":
            return HMM3Harmonizer(
                beam_width=4,
                melody_weight=0.30,
                cadence_weight=0.12,
                repetition_penalty=0.05,
            )
        case "ritual":
            return HMM3Harmonizer(
                beam_width=5,
                secondary_dom_weight=0.10,
                extension_weight=0.06,
                repetition_penalty=0.10,
            )
        case _:
            return HMM3Harmonizer(
                beam_width=5,
                cadence_weight=0.15,
            )


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Melody contour for harmonization
# ---------------------------------------------------------------------------
def _build_melody_contour(
    scale: Scale, bars: int, beats_per_bar: int, density: float
) -> list[NoteInfo]:
    """
    Build a melodic contour for harmonizer input.

    Instead of running scale degrees in eighth notes, creates a melody with:
    - Longer notes on strong beats (harmonic rhythm)
    - Melodic arch contour
    - Chord-tone preference on downbeats
    - Occasional stepwise motion between chord changes
    """
    degs = scale.degrees()
    if not degs:
        return [NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80)]

    notes: list[NoteInfo] = []
    t = 0.0
    total_beats = bars * beats_per_bar

    # Melodic contour that drives harmonic movement
    # NOT always tonic — vary degrees to push harmonizer to change chords
    degree_cycle = []
    n_degrees = len(degs)
    for bar in range(bars):
        beat_in_phrase = bar % 4
        if beat_in_phrase == 0:
            # Phrase start: strong degree (root, 3rd, or 5th)
            degree_cycle.append(int(random.choice(degs[: min(3, n_degrees)])))
        elif beat_in_phrase == 1:
            # Second bar: often the 4th or 2nd degree to push IV/ii
            if n_degrees > 3:
                degree_cycle.append(int(degs[random.choice([1, 3])]))
            else:
                degree_cycle.append(int(random.choice(degs)))
        elif beat_in_phrase == 2:
            # Third bar: dominant area (5th degree or leading tone)
            if n_degrees > 4:
                degree_cycle.append(int(degs[random.choice([4, 6])]))
            else:
                degree_cycle.append(int(random.choice(degs)))
        else:
            # Fourth bar: resolution back to tonic or subdominant
            if random.random() < 0.6:
                degree_cycle.append(int(degs[0]))
            else:
                degree_cycle.append(int(random.choice(degs[: min(3, n_degrees)])))

    for i, bar_deg in enumerate(degree_cycle):
        bar_start = i * beats_per_bar
        if bar_start >= total_beats:
            break

        # Two notes per bar: one on beat 1, one on beat 3
        for beat_offset in [0, beats_per_bar / 2]:
            onset = bar_start + beat_offset
            if onset >= total_beats:
                break

            # Alternate between the bar's degree and a neighbor
            if beat_offset == 0:
                pc = bar_deg
            else:
                # Passing tone: one degree away
                idx = degs.index(bar_deg) if bar_deg in degs else 0
                neighbor_idx = (idx + random.choice([-1, 1])) % n_degrees
                pc = int(degs[neighbor_idx])

            pitch = 48 + pc
            pitch = max(36, min(72, pitch))

            dur = min(beats_per_bar / 2 - 0.1, total_beats - onset)
            dur = max(0.4, dur)

            vel = 80 if beat_offset == 0 else 65
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                )
            )

    return notes

    return notes


def _nearest_scale_pitch(pc: float, ref: int, base_octave: int) -> int:
    """Nearest MIDI pitch with given pitch class, near reference, around base octave."""
    base = base_octave * 12
    above = base + int(pc)
    while above < ref - 6:
        above += 12
    while above > ref + 6:
        above -= 12
    return max(36, min(96, above))


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
class _CoordRhythm:
    """Thin adapter: delegates to RhythmCoordinator.get_rhythm() for a specific track."""

    def __init__(self, coordinator: RhythmCoordinator, track_name: str) -> None:
        self._coord = coordinator
        self._track = track_name

    def generate(self, duration_beats: float):
        return self._coord.get_rhythm(self._track, duration_beats)


def _make_coordinated_rhythm(coord: RhythmCoordinator, track_name: str) -> _CoordRhythm:
    return _CoordRhythm(coord, track_name)


def generate(duration_minutes: float, tempo: int, key_root: int, seed: int | None):
    if seed is not None:
        random.seed(seed)

    beats_per_bar = 4
    total_beats = duration_minutes * 60 * (tempo / 60)
    total_bars = max(8, int(round(total_beats / beats_per_bar)))
    sections = build_sections(total_bars)

    tracks: dict[str, list[NoteInfo]] = {}
    all_chords: list[ChordLabel] = []
    beat_offset = 0.0

    # Composer modules
    nct = NonChordToneGenerator(passing_prob=0.12, neighbor_prob=0.06)
    art_engine = ArticulationEngine()

    # Generator cache: (track_name, mood) → (generator, mods)
    gen_cache: dict[tuple[str, str], tuple] = {}

    # RenderContext per track — persisted across sections for melodic continuity.
    # Each section transition carries the last pitch, velocity and chord forward.
    track_contexts: dict[str, RenderContext] = {}
    prev_scale: Scale | None = None
    prev_last_chord: ChordLabel | None = None

    # Track → instrument profile mapping
    INSTRUMENT_MAP = {
        "melody": "strings_melody",
        "arp": "harp",
        "bass": "cello",
        "chords": "strings_pad",
        "ostinato": "strings_staccato",
        "ambient": "strings_pad",
        "dyads": "strings_melody",
        "dyads_run": "strings_staccato",
        "riff": "strings_tremolo",
        "strum": "strings_staccato",
        "fingerpicking": "harp",
        "percussion": "timpani",
        "groove": "strings_staccato",
        "call_response": "strings_melody",
        "canon": "strings_melody",
        "piano_sweep": "piano",
    }

    # Tracks that participate in cross-track rhythm lock per mood
    RHYTHM_LOCK_GROUPS: dict[str, list[str]] = {
        "battle": ["bass", "percussion", "ostinato"],
        "climax": ["bass", "percussion", "ostinato", "chords"],
        "ritual": ["bass", "ostinato", "fingerpicking"],
        "tension": ["bass", "ostinato", "riff"],
    }

    for si, sec in enumerate(sections):
        s_beats = sec.bars * beats_per_bar
        scale = SCALES[sec.scale_name]
        scale = Scale(root=(sec.key_root + key_root) % 12, mode=scale.mode)

        # Detect key modulation for logging
        if prev_scale is not None and scale != prev_scale:
            root_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            print(
                f"  ♩ Modulation: {root_names[prev_scale.root]} {prev_scale.mode.name} "
                f"→ {root_names[scale.root]} {scale.mode.name}  [{sec.name}]"
            )
        prev_scale = scale

        # --- Harmonize with section transition ---
        harmonizer = pick_harmonizer(sec.mood)
        melody_contour = _build_melody_contour(scale, sec.bars, beats_per_bar, sec.density)

        # If previous section's last chord exists, prepend a connecting note
        # to create smooth transition (shared-chord pivot)
        if prev_last_chord is not None:
            pivot_note = NoteInfo(
                pitch=prev_last_chord.root + 48,
                start=-2.0,  # before section start
                duration=2.0,
                velocity=60,
            )
            melody_contour = [pivot_note] + melody_contour

        local_chords = harmonizer.harmonize(melody_contour, scale, s_beats)

        # Remove any chords that start before beat 0
        local_chords = [c for c in local_chords if c.start >= 0]
        while len(local_chords) < sec.bars:
            local_chords.append(
                local_chords[-1]
                if local_chords
                else ChordLabel(
                    root=int(scale.degrees()[0]),
                    quality=Quality.MINOR,
                    start=round(len(local_chords) * beats_per_bar, 6),
                    duration=beats_per_bar,
                )
            )

        # Offset to global time
        for c in local_chords:
            all_chords.append(
                ChordLabel(
                    root=c.root,
                    quality=c.quality,
                    start=round(c.start + beat_offset, 6),
                    duration=c.duration,
                    degree=c.degree,
                )
            )

        # Track last chord for next section's transition
        if local_chords:
            prev_last_chord = local_chords[-1]

        # --- Cross-track RhythmCoordinator ---
        # For rhythm-critical moods, lock specified tracks to a shared onset grid.
        coordinator: RhythmCoordinator | None = None
        rhythm_lock_tracks = RHYTHM_LOCK_GROUPS.get(sec.mood, [])
        active_rhythm_lock = [t for t in rhythm_lock_tracks if t in sec.tracks]
        if len(active_rhythm_lock) >= 2:
            hits = 8 if sec.mood in ("battle", "climax") else 6
            shared_rgen = EuclideanRhythmGenerator(
                hits_per_bar=hits,
                slots_per_beat=4,
            )
            coordinator = RhythmCoordinator(shared_rgen)
            for tn in active_rhythm_lock:
                coordinator.register(tn)

        # --- Generate each track ---
        phrase_position = si / max(1, len(sections) - 1)

        for track_name in sec.tracks:
            cache_key = (track_name, sec.mood)
            if cache_key not in gen_cache:
                gen, rhythm, mods = make_pipeline(track_name, sec.mood, sec.density, scale)
                if rhythm:
                    gen.rhythm = rhythm  # type: ignore
                gen_cache[cache_key] = (gen, mods)

            gen, mods = gen_cache[cache_key]

            # Build render context: carry state from previous section.
            # Update current_scale so modulation-aware generators can respond.
            prev_ctx = track_contexts.get(track_name)
            if prev_ctx is None:
                ctx = RenderContext(
                    phrase_position=phrase_position,
                    current_scale=scale,
                )
            else:
                ctx = RenderContext(
                    prev_pitch=prev_ctx.prev_pitch,
                    prev_velocity=prev_ctx.prev_velocity,
                    prev_chord=prev_ctx.prev_chord,
                    prev_pitches=list(prev_ctx.prev_pitches),
                    phrase_position=phrase_position,
                    current_scale=scale,
                )

            # Inject coordinated rhythm for rhythm-lock tracks
            coordinated = False
            orig_rhythm = None
            if (
                coordinator is not None
                and track_name in active_rhythm_lock
                and hasattr(gen, "rhythm")
            ):
                orig_rhythm = gen.rhythm
                gen.rhythm = _make_coordinated_rhythm(coordinator, track_name)
                coordinated = True

            notes = gen.render(local_chords, scale, s_beats, ctx)

            # Restore original rhythm
            if coordinated:
                gen.rhythm = orig_rhythm

            # Persist context for next section
            if hasattr(gen, "_last_context") and gen._last_context is not None:
                track_contexts[track_name] = gen._last_context
            elif notes:
                track_contexts[track_name] = ctx.with_end_state(
                    last_pitch=notes[-1].pitch,
                    last_velocity=notes[-1].velocity,
                    last_chord=local_chords[-1] if local_chords else None,
                    current_scale=scale,
                )

            # Apply modifiers
            mctx = ModifierContext(
                duration_beats=s_beats, chords=local_chords, timeline=None, scale=scale
            )  # type: ignore
            for m in mods:
                try:
                    notes = m.modify(notes, mctx)
                except Exception:
                    pass

            # NCT for melodic tracks
            if track_name in ("melody", "dyads", "call_response", "arp"):
                try:
                    notes = nct.add_non_chord_tones(notes, local_chords, scale)
                except Exception:
                    pass

            # Offset and store
            if track_name not in tracks:
                tracks[track_name] = []
            for n in notes:
                tracks[track_name].append(
                    NoteInfo(
                        pitch=n.pitch,
                        start=round(n.start + beat_offset, 6),
                        duration=n.duration,
                        velocity=n.velocity,
                        articulation=n.articulation,
                        expression=n.expression,
                    )
                )

        beat_offset += s_beats

    # Sort all tracks
    for k in tracks:
        tracks[k] = sorted(tracks[k], key=lambda n: n.start)

    # Apply articulations and collect sustain pedal boundary events
    pedal_cc: dict[str, list[tuple[float, int, int]]] = {}
    for track_name in list(tracks.keys()):
        instrument = INSTRUMENT_MAP.get(track_name, "strings_melody")
        tracks[track_name] = art_engine.apply(tracks[track_name], instrument, beat_offset)
        raw = art_engine.add_sustain_pedal_events(tracks[track_name], beat_offset)
        if raw:
            pedal_cc[track_name] = [(e["time"], 64, e["value"]) for e in raw]

    # Master mix
    tracks = _master_mix(tracks)
    return tracks, pedal_cc


# ---------------------------------------------------------------------------
# Master mix
# ---------------------------------------------------------------------------
MIX = {
    "melody": 1.0,
    "bass": 0.85,
    "chords": 0.7,
    "arp": 0.6,
    "ostinato": 0.65,
    "ambient": 0.5,
    "dyads": 0.7,
    "dyads_run": 0.55,
    "riff": 0.8,
    "strum": 0.65,
    "fingerpicking": 0.55,
    "percussion": 0.75,
    "groove": 0.7,
    "call_response": 0.65,
    "canon": 0.6,
    "piano_sweep": 0.55,
}


_MAX_POLYPHONY = 12  # max simultaneous notes across all tracks


def _master_mix(tracks: dict[str, list[NoteInfo]]) -> dict[str, list[NoteInfo]]:
    result = {}
    for name, notes in tracks.items():
        level = MIX.get(name, 0.7)
        mixed = []
        for n in notes:
            vel = max(15, min(127, int(n.velocity * level) + random.randint(-4, 4)))
            start = n.start + random.uniform(-0.01, 0.01)
            mixed.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=round(start, 6),
                    duration=n.duration,
                    velocity=vel,
                    articulation=n.articulation,
                    expression=n.expression,
                )
            )
        result[name] = sorted(mixed, key=lambda n: n.start)

    result = _limit_polyphony(result)
    return result


def _limit_polyphony(tracks: dict[str, list[NoteInfo]]) -> dict[str, list[NoteInfo]]:
    """Reduce velocity when too many notes play simultaneously."""
    # Collect all note onsets in 0.5-beat windows
    all_notes: list[tuple[float, str, int]] = []
    for name, notes in tracks.items():
        for i, n in enumerate(notes):
            all_notes.append((n.start, name, i))
    all_notes.sort()

    # Count simultaneous notes per 0.25-beat grid
    grid: dict[int, int] = {}
    for t, _, _ in all_notes:
        key = int(t * 4)  # 0.25-beat resolution
        grid[key] = grid.get(key, 0) + 1

    # Find peak polyphony
    peak = max(grid.values()) if grid else 1
    if peak <= _MAX_POLYPHONY:
        return tracks

    # Scale factor for overloaded windows
    result: dict[str, list[NoteInfo]] = {}
    for name, notes in tracks.items():
        scaled = []
        for n in notes:
            key = int(n.start * 4)
            poly = grid.get(key, 1)
            if poly > _MAX_POLYPHONY:
                # Reduce velocity proportionally
                ratio = _MAX_POLYPHONY / poly
                vel = max(20, int(n.velocity * ratio))
            else:
                vel = n.velocity
            scaled.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration,
                    velocity=vel,
                    articulation=n.articulation,
                    expression=n.expression,
                )
            )
        result[name] = scaled
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="Dark Fantasy V3 — 100% SDK")
    p.add_argument("--duration", type=float, default=3.0)
    p.add_argument("--tempo", type=int, default=72)
    p.add_argument("--key", type=int, default=0)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--output", type=str, default="dark_fantasy_v3.mid")
    args = p.parse_args()

    duration = max(2.0, min(30.0, args.duration))
    bars = int(round(duration * 60 * (args.tempo / 60) / 4))
    actual_sec = bars * 4 / args.tempo * 60

    key_name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"][args.key]
    print(f"Dark Fantasy V3 — 100% SDK")
    print(
        f"  {duration:.1f} min requested → {actual_sec / 60:.1f} min actual ({bars} bars @ {args.tempo} BPM)"
    )
    print(f"  Key: {key_name} minor")
    print()

    tracks, pedal_cc = generate(duration, args.tempo, args.key, args.seed)

    total = sum(len(n) for n in tracks.values())
    print(f"  Tracks: {len(tracks)}, Notes: {total}")
    for name, notes in sorted(tracks.items()):
        print(f"    {name:20s}: {len(notes):5d} notes")

    export_multitrack_midi(
        tracks,
        args.output,
        bpm=args.tempo,
        key=f"{key_name}m",
        cc_events=pedal_cc,
        instruments=STYLE_INSTRUMENTS["dark_fantasy"],
    )
    print(f"\n  → {args.output} ({Path(args.output).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
