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

import typing
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from melodica.types import (
    Scale,
    Mode,
    MusicTimeline,
    KeyLabel,
    ChordLabel,
    Arrangement,
    Track,
    NoteInfo,
    parse_progression,
    MarkerLabel,
    TimeSignatureLabel,
)
from melodica.presets import load_preset
from melodica.render_context import RenderContext
from melodica.theory.modulation import apply_articulation, ModulationEngine
from melodica.application.automation import apply_automation, ExpressionCurve
from melodica.application.orchestration import OrchestralBalancer

# Forward declaration / later import support
if typing.TYPE_CHECKING:
    from .styles import Style


@dataclass
class Style:
    """Defines a genre's typical instrumentation and harmonic language."""

    name: str
    allowed_scales: List[Scale]
    track_mapping: Dict[str, str]  # e.g., "Bass" -> "followed_bass"
    instrument_mapping: Dict[str, int] = field(
        default_factory=dict
    )  # e.g., "Bass" -> 32 (Acoustic Bass)
    progressions: Dict[str, List[str]] = field(
        default_factory=dict
    )  # e.g., "Intro" -> ["Im IVm", "Im VI"]
    typical_bpm: float = 120.0
    typical_time_signature: tuple[int, int] = (4, 4)


@dataclass
class Section:
    """A musical section like Intro, Verse, Chorus."""

    name: str
    duration_beats: float
    progression: str
    tracks: Dict[str, str]  # track_name -> preset_name
    mood: Optional[str] = None
    tempo_hint: Optional[float] = None
    articulation: str = "sustain"  # 'staccato', 'legato', etc.
    automation: List[ExpressionCurve] = field(default_factory=list)
    time_signature: tuple[int, int] = (4, 4)  # (numerator, denominator)
    key: Optional[Scale] = None  # per-section key override (None = use Composition.key)
    shared_rhythm: Optional[Any] = None  # RhythmGenerator — shared across all tracks in section
    intensity: float = 0.5  # 0.0=sparse/quiet, 1.0=dense/loud; modulates velocity


@dataclass
class Composition:
    """A full song structure made of sections."""

    name: str
    key: Scale
    sections: List[Section] = field(default_factory=list)

    def add_section(
        self,
        name: str,
        duration: float,
        progression: str,
        tracks: Dict[str, str],
        articulation: str = "sustain",
        automation: List[ExpressionCurve] = None,
        time_signature: tuple[int, int] = (4, 4),
        key: Optional[Scale] = None,
        shared_rhythm: Optional[Any] = None,
        intensity: float = 0.5,
    ):
        if automation is None:
            automation = []
        self.sections.append(
            Section(
                name,
                duration,
                progression,
                tracks,
                articulation=articulation,
                automation=automation,
                time_signature=time_signature,
                key=key,
                shared_rhythm=shared_rhythm,
                intensity=intensity,
            )
        )

    def apply_style(self, style: Style, structure: List[tuple[str, float]]):
        """
        Builds a composition based on a Style template.
        structure: [("Intro", 16.0), ("Main", 32.0), ...]
        """
        import random

        for sec_name, duration in structure:
            # Pick a progression if the style has one for this name, else fallback
            progs = style.progressions.get(sec_name, ["Im"])
            prog = random.choice(progs)

            self.add_section(
                name=sec_name,
                duration=duration,
                progression=prog,
                tracks=style.track_mapping,
                time_signature=style.typical_time_signature
                if hasattr(style, "typical_time_signature")
                else (4, 4),
            )


class _CoordinatedRhythm:
    """
    Thin RhythmGenerator adapter that delegates to a RhythmCoordinator for a
    specific track.  Injected temporarily into a generator's `rhythm` attribute
    so all tracks in a section share the same onset grid.
    """

    def __init__(self, coordinator: Any, track_name: str) -> None:
        self._coordinator = coordinator
        self._track_name = track_name

    def generate(self, duration_beats: float) -> list:
        return self._coordinator.get_rhythm(self._track_name, duration_beats)


class MusicDirector:
    """
    Interprets a Composition and renders it into a final multi-track Arrangement.
    This is the 'Human-like' script interpreter.
    """

    def __init__(self, key: Scale):
        self.key = key
        self.preset_cache = {}

    def _get_preset(self, name: str):
        if name not in self.preset_cache:
            self.preset_cache[name] = load_preset(name)
        return self.preset_cache[name]

    def render(
        self, composition: Composition, initial_contexts: dict[str, RenderContext] | None = None
    ) -> Arrangement:
        global_timeline = MusicTimeline(
            chords=[], keys=[KeyLabel(scale=composition.key, start=0, duration=0)]
        )

        current_beat = 0.0
        track_notes: dict[str, list] = {}
        track_keyswitches: dict[str, list[tuple[float, int]]] = {}
        prev_articulation: str | None = None
        track_render_ctx: dict[str, RenderContext | None] = (
            dict(initial_contexts) if initial_contexts else {}
        )

        # Compute total duration for phrase_position calculation
        total_beats = sum(s.duration_beats for s in composition.sections) or 1.0

        for section in composition.sections:
            # ── Compute phrase_position for this section ────────────────────
            # Midpoint of the section as a fraction of the total arrangement.
            # Used by generators' _apply_phrase_arch() for dynamic shaping.
            section_midpoint = current_beat + section.duration_beats / 2.0
            phrase_position = min(1.0, section_midpoint / total_beats)

            # ── Determine effective key for this section ──────────────────────
            # Section.key overrides the global composition key, enabling modulation.
            effective_key: Scale = section.key if section.key is not None else composition.key

            # Emit keyswitch if articulation changed since last section
            if section.articulation != prev_articulation:
                from melodica.theory.modulation import ARTICULATION_KEYSWITCHES

                ks_pitch = ARTICULATION_KEYSWITCHES.get(section.articulation)
                if ks_pitch is not None:
                    for track_name in section.tracks:
                        if track_name not in track_keyswitches:
                            track_keyswitches[track_name] = []
                        track_keyswitches[track_name].append((current_beat, ks_pitch))
                prev_articulation = section.articulation

            # 1. Parse chords for this section using the effective key
            section_chords = parse_progression(section.progression, effective_key)
            for c in section_chords:
                c.start += current_beat
                global_timeline.chords.append(c)

            # 1b. Add Timeline Meta: Markers and Time Signatures
            global_timeline.markers.append(MarkerLabel(text=section.name, start=current_beat))
            global_timeline.time_signatures.append(
                TimeSignatureLabel(
                    numerator=section.time_signature[0],
                    denominator=section.time_signature[1],
                    start=current_beat,
                )
            )

            # 2. Add key label for the section duration (uses effective key)
            global_timeline.keys.append(
                KeyLabel(scale=effective_key, start=current_beat, duration=section.duration_beats)
            )

            # ── Build shared RhythmCoordinator if section requests one ────────
            # When Section.shared_rhythm is set, all tracks in the section receive
            # identical onset/duration events, keeping the rhythmic grid locked.
            coordinator = None
            if section.shared_rhythm is not None:
                from melodica.rhythm import RhythmCoordinator

                coordinator = RhythmCoordinator(section.shared_rhythm)
                for tn in section.tracks:
                    coordinator.register(tn)

            # 3. Render each track in the section
            from melodica.modifiers import ModifierContext

            current_section_tracks = {}
            for track_name, preset_name in section.tracks.items():
                generator, modifiers = self._get_preset(preset_name)

                # Ensure render context carries the current effective key so
                # modulation-aware generators can inspect it via context.current_scale.
                render_ctx = track_render_ctx.get(track_name)
                if render_ctx is None:
                    render_ctx = RenderContext(current_scale=effective_key)
                elif render_ctx.current_scale != effective_key:
                    render_ctx = render_ctx.with_end_state(current_scale=effective_key)

                # Set phrase_position so generators' _apply_phrase_arch() works
                render_ctx.phrase_position = phrase_position

                # Temporarily inject a coordinated rhythm into the generator so
                # all tracks share the same onset grid for this section.
                coordinated = False
                if coordinator is not None and hasattr(generator, "rhythm"):
                    _orig_rhythm = generator.rhythm
                    generator.rhythm = _CoordinatedRhythm(coordinator, track_name)
                    coordinated = True

                notes = generator.render(
                    section_chords, effective_key, section.duration_beats, context=render_ctx
                )

                # Restore original rhythm attribute
                if coordinated:
                    generator.rhythm = _orig_rhythm

                # Update render context from generator end state; always thread
                # current_scale so the next section inherits the right key.
                if hasattr(generator, "_last_context") and generator._last_context is not None:
                    saved = generator._last_context
                    if saved.current_scale != effective_key:
                        saved = saved.with_end_state(current_scale=effective_key)
                    track_render_ctx[track_name] = saved
                elif notes:
                    track_render_ctx[track_name] = (render_ctx or RenderContext()).with_end_state(
                        last_pitch=notes[-1].pitch,
                        last_velocity=notes[-1].velocity,
                        last_chord=section_chords[-1] if section_chords else None,
                        current_scale=effective_key,
                    )
                else:
                    track_render_ctx[track_name] = None

                # Apply modifiers with effective key
                section_timeline = MusicTimeline(
                    chords=section_chords,
                    keys=[KeyLabel(scale=effective_key, start=0, duration=section.duration_beats)],
                )
                ctx = ModifierContext(
                    duration_beats=section.duration_beats,
                    chords=section_chords,
                    timeline=section_timeline,
                    scale=effective_key,
                    tracks=current_section_tracks,
                )
                for m in modifiers:
                    notes = m.modify(notes, ctx)

                # 4. Apply Articulation & Automation
                notes = apply_articulation(
                    notes, section.articulation, phrase_duration=section.duration_beats
                )
                if section.automation:
                    notes = apply_automation(notes, section.automation)

                # 5. Apply section intensity scaling to velocities
                # intensity 0.5 = neutral (1.0x), 0.0 = soft (0.5x), 1.0 = loud (1.5x)
                vel_scale = 0.5 + section.intensity
                if vel_scale != 1.0:
                    for n in notes:
                        n.velocity = max(1, min(127, int(n.velocity * vel_scale)))

                current_section_tracks[track_name] = notes

                # Shift notes to global start
                if track_name not in track_notes:
                    track_notes[track_name] = []

                for n in notes:
                    n.start += current_beat
                    track_notes[track_name].append(n)

            current_beat += section.duration_beats

        # Update total timeline duration
        global_timeline.keys[0].duration = current_beat

        # Build final tracks with unique channels
        final_tracks = []
        for i, (name, notes) in enumerate(track_notes.items()):
            channel = i % 16
            ks = track_keyswitches.get(name, [])
            final_tracks.append(Track(name=name, notes=notes, channel=channel, keyswitch_events=ks))

        return Arrangement(
            name=composition.name,
            timeline=global_timeline,
            tracks=final_tracks,
            total_beats=current_beat,
        )

    def render_auto_song(self, style: "Style", structure: List[tuple[str, float]]) -> Arrangement:
        """One-click generation: Picks scales and builds song according to Style."""
        import random

        # Pick one scale from style
        scale = random.choice(style.allowed_scales)
        self.key = scale  # Update director key

        comp = Composition(name=f"Auto_{style.name}", key=scale)
        comp.apply_style(style, structure)
        arrangement = self.render(comp)

        # 4. Global Orchestral Balancing (Spectral & Spatial separation)
        arrangement.tracks = OrchestralBalancer.apply_balancing(arrangement.tracks)

        # Apply instrument mapping from style to rendered tracks
        for track in arrangement.tracks:
            if track.name in style.instrument_mapping:
                track.program = style.instrument_mapping[track.name]

        return arrangement


# --- Human-like DSL Example ---


def build_game_music_script():
    """Example of how a user-bot would write a script."""
    key = Scale(root=9, mode=Mode.NATURAL_MINOR)  # A minor
    comp = Composition("Forest Quest", key)
    comp.add_section(
        name="Intro",
        duration=8.0,
        progression="Im Im7 VI VII",
        tracks={"Pad": "ambient_pad", "Arp": "fast_arp"},
    )
    return comp
