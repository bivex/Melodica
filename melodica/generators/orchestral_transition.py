# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
generators/orchestral_transition.py — OrchestralTransitionGenerator.

PhraseGenerator that produces smooth transitions between orchestral sections.
Supports crescendo builds, ritardando/accelerando, fermata, pedal point,
retransition, and bridge passage types.

Layer: Application / Domain
Style: Classical, cinematic, film scoring.
"""

from __future__ import annotations

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale, chord_at

_GM = {
    "violin": 40, "viola": 41, "cello": 42, "contrabass": 43,
    "flute": 73, "trumpet": 56, "french_horn": 60,
}

_VALID_TYPES = frozenset({
    "crescendo_build", "ritardando", "accelerando",
    "fermata", "pedal_point", "retransition", "bridge_passage",
})

_VALID_CURVES = frozenset({"flat", "crescendo", "diminuendo"})


class OrchestralTransitionGenerator(PhraseGenerator):
    """
    Generates smooth transitions between orchestral sections.

    transition_type:
        Style of transition (see module docstring).
    target_chord:
        Chord the transition leads into (used by retransition/bridge_passage).
    intensity_curve:
        Dynamic shape: "flat", "crescendo", "diminuendo".
    sustain_instruments:
        Instruments that sustain through the entire transition.
    entry_order:
        Instruments that enter one-by-one during crescendo_build.

    After render(), self.tracks and self.instruments are populated with
    per-instrument data for multi-track export.
    """

    name: str = "Orchestral Transition"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        transition_type: str = "crescendo_build",
        target_chord: ChordLabel | None = None,
        intensity_curve: str = "crescendo",
        sustain_instruments: list[str] | None = None,
        entry_order: list[str] | None = None,
    ) -> None:
        super().__init__(params)
        if transition_type not in _VALID_TYPES:
            raise ValueError(f"Unknown transition_type: {transition_type!r}")
        if intensity_curve not in _VALID_CURVES:
            raise ValueError(f"Unknown intensity_curve: {intensity_curve!r}")
        self.transition_type = transition_type
        self.target_chord = target_chord
        self.intensity_curve = intensity_curve
        self.sustain_instruments = sustain_instruments or ["violin", "viola", "cello"]
        self.entry_order = entry_order or [
            "cello", "viola", "violin", "flute", "trumpet",
        ]
        self._last_context: RenderContext | None = None
        self.tracks: dict[str, list[NoteInfo]] = {}
        self.instruments: dict[str, int] = {}

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords or duration_beats <= 0:
            return []

        self.tracks = {}
        self.instruments = {}

        dispatch = {
            "crescendo_build": self._crescendo_build,
            "ritardando": self._ritardando,
            "accelerando": self._accelerando,
            "fermata": self._fermata,
            "pedal_point": self._pedal_point,
            "retransition": self._retransition,
            "bridge_passage": self._bridge_passage,
        }
        notes = dispatch[self.transition_type](chords, key, duration_beats)

        for inst, prog in self.instruments.items():
            if inst not in self.tracks:
                self.tracks[inst] = []

        if notes:
            last = notes[-1]
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=last.pitch,
                last_velocity=last.velocity,
                last_chord=chord_at(chords, duration_beats),
            )

        return notes

    # ------------------------------------------------------------------
    # Velocity helpers
    # ------------------------------------------------------------------

    def _vel_at(self, progress: float, base: int = 80) -> int:
        """Apply intensity_curve to a base velocity at a given progress 0-1."""
        if self.intensity_curve == "crescendo":
            vel = int(base * 0.4 + base * 0.6 * progress)
        elif self.intensity_curve == "diminuendo":
            vel = int(base * 0.4 + base * 0.6 * (1.0 - progress))
        else:
            vel = base
        return max(1, min(127, vel))

    def _vel_range(self, progress: float, lo: int = 40, hi: int = 110) -> int:
        if self.intensity_curve == "crescendo":
            vel = int(lo + (hi - lo) * progress)
        elif self.intensity_curve == "diminuendo":
            vel = int(lo + (hi - lo) * (1.0 - progress))
        else:
            vel = (lo + hi) // 2
        return max(1, min(127, vel))

    def _register_for(self, inst: str) -> tuple[int, int]:
        """Return (low, high) MIDI range for an instrument."""
        ranges = {
            "contrabass": (28, 55),
            "cello": (36, 72),
            "viola": (48, 84),
            "violin": (55, 96),
            "flute": (60, 96),
            "trumpet": (55, 82),
            "french_horn": (34, 70),
        }
        return ranges.get(inst, (self.params.key_range_low, self.params.key_range_high))

    def _add_track_note(self, inst: str, pitch: int, start: float,
                        duration: float, velocity: int) -> NoteInfo:
        """Create a NoteInfo, register instrument, and store in tracks."""
        self.instruments[inst] = _GM.get(inst, 48)
        note = NoteInfo(
            pitch=max(0, min(127, pitch)),
            start=round(start, 6),
            duration=round(max(0.01, duration), 6),
            velocity=max(1, min(127, velocity)),
        )
        if inst not in self.tracks:
            self.tracks[inst] = []
        self.tracks[inst].append(note)
        return note

    # ------------------------------------------------------------------
    # Transition types
    # ------------------------------------------------------------------

    def _crescendo_build(self, chords: list[ChordLabel],
                         key: Scale, dur: float) -> list[NoteInfo]:
        """Sustained pedal tone with instruments entering one by one."""
        all_notes: list[NoteInfo] = []
        chord = chord_at(chords, 0) or chords[0]
        root_pc = chord.bass if chord.bass is not None else chord.root

        n_instruments = len(self.entry_order)
        entry_interval = dur / max(n_instruments, 1)

        for idx, inst in enumerate(self.entry_order):
            low, high = self._register_for(inst)
            entry_time = idx * entry_interval

            if inst == "cello":
                pitch = nearest_pitch(root_pc, low + 12)
            elif inst == "viola":
                pitch = nearest_pitch(root_pc, (low + high) // 2)
            elif inst == "violin":
                pitch = nearest_pitch(root_pc, (low + high) // 2)
            elif inst == "flute":
                pitch = nearest_pitch(root_pc, high - 12)
            elif inst == "trumpet":
                pitch = nearest_pitch(root_pc, high - 12)
            else:
                pitch = nearest_pitch(root_pc, (low + high) // 2)

            pitch = snap_to_scale(max(low, min(high, pitch)), key)

            remaining = dur - entry_time
            if remaining <= 0:
                continue

            entry_progress = entry_time / dur
            entry_vel = self._vel_range(entry_progress, 30, 80)

            build_vel = self._vel_range(min(1.0, entry_progress + 0.3), 50, 110)

            # Initial entry note (softer)
            self._add_track_note(inst, pitch, entry_time,
                                 remaining * 0.4, entry_vel)
            # Sustained build (louder)
            build_start = entry_time + remaining * 0.4
            if build_start < dur:
                self._add_track_note(inst, pitch, build_start,
                                     dur - build_start, build_vel)

        # Sustain instruments hold through entire duration
        for inst in self.sustain_instruments:
            if inst in [e for e in self.entry_order]:
                continue
            low, high = self._register_for(inst)
            pitch = nearest_pitch(root_pc, (low + high) // 2)
            pitch = snap_to_scale(max(low, min(high, pitch)), key)
            vel = self._vel_range(0.5, 40, 90)
            self._add_track_note(inst, pitch, 0.0, dur, vel)

        for track_notes in self.tracks.values():
            all_notes.extend(track_notes)
        all_notes.sort(key=lambda n: (n.start, n.pitch))
        return all_notes

    def _ritardando(self, chords: list[ChordLabel],
                    key: Scale, dur: float) -> list[NoteInfo]:
        """Slowing down feel with increasing note durations."""
        all_notes: list[NoteInfo] = []
        scale_pcs = key.degrees()
        t = 0.0

        while t < dur:
            progress = t / max(0.1, dur)
            # Duration factor: 0.5 at start → 1.5 at end
            dur_factor = 0.5 + progress * 1.0
            note_dur = dur_factor
            note_dur = min(note_dur, dur - t)
            if note_dur <= 0:
                break

            chord = chord_at(chords, t) or chords[0]
            pcs = chord.pitch_classes()
            root_pc = chord.bass if chord.bass is not None else chord.root
            pitch = nearest_pitch(root_pc, self.params.key_range_low + 12)
            pitch = snap_to_scale(
                max(self.params.key_range_low, min(self.params.key_range_high, pitch)),
                key,
            )

            # Velocity: rises slightly then falls (urgency → arrival)
            if progress < 0.6:
                vel = self._vel_range(progress / 0.6, 50, 100)
            else:
                vel = self._vel_range((progress - 0.6) / 0.4, 100, 60)

            inst = "violin"
            self._add_track_note(inst, pitch, t, note_dur, vel)

            # Add harmony voice (viola) on a chord tone
            if len(pcs) > 1:
                third_pc = pcs[1]
                low, high = self._register_for("viola")
                harm_pitch = nearest_pitch(third_pc, (low + high) // 2)
                harm_pitch = snap_to_scale(max(low, min(high, harm_pitch)), key)
                self._add_track_note("viola", harm_pitch, t, note_dur, max(1, vel - 15))

            t += note_dur

        for track_notes in self.tracks.values():
            all_notes.extend(track_notes)
        all_notes.sort(key=lambda n: (n.start, n.pitch))
        return all_notes

    def _accelerando(self, chords: list[ChordLabel],
                     key: Scale, dur: float) -> list[NoteInfo]:
        """Speeding up with decreasing note durations."""
        all_notes: list[NoteInfo] = []
        t = 0.0

        while t < dur:
            progress = t / max(0.1, dur)
            # Duration factor: 1.5 at start → 0.25 at end
            dur_factor = 1.5 - progress * 1.25
            dur_factor = max(0.125, dur_factor)
            note_dur = min(dur_factor, dur - t)
            if note_dur <= 0:
                break

            chord = chord_at(chords, t) or chords[0]
            pcs = chord.pitch_classes()
            root_pc = chord.bass if chord.bass is not None else chord.root
            pitch = nearest_pitch(root_pc, self.params.key_range_low + 24)
            pitch = snap_to_scale(
                max(self.params.key_range_low, min(self.params.key_range_high, pitch)),
                key,
            )

            vel = self._vel_range(progress, 50, 120)

            self._add_track_note("violin", pitch, t, note_dur, vel)

            # Bass (cello) follows root
            low, high = self._register_for("cello")
            bass_pitch = nearest_pitch(root_pc, low + 12)
            bass_pitch = snap_to_scale(max(low, min(high, bass_pitch)), key)
            self._add_track_note("cello", bass_pitch, t, note_dur, max(1, vel - 20))

            t += note_dur

        for track_notes in self.tracks.values():
            all_notes.extend(track_notes)
        all_notes.sort(key=lambda n: (n.start, n.pitch))
        return all_notes

    def _fermata(self, chords: list[ChordLabel],
                 key: Scale, dur: float) -> list[NoteInfo]:
        """Sustained chord with held tones and velocity variation."""
        all_notes: list[NoteInfo] = []
        chord = chord_at(chords, 0) or chords[0]
        pcs = chord.pitch_classes()

        # Map pitch classes to instruments for voice coverage
        voice_map = [
            ("cello", pcs[0] if pcs else chord.root, 12),
            ("viola", pcs[1] if len(pcs) > 1 else pcs[0] if pcs else chord.root, 0),
            ("violin", pcs[min(2, len(pcs) - 1)] if pcs else chord.root, 12),
        ]

        for inst, pc, octave_offset in voice_map:
            low, high = self._register_for(inst)
            center = (low + high) // 2 + octave_offset
            pitch = nearest_pitch(pc, center)
            pitch = snap_to_scale(max(low, min(high, pitch)), key)

            base_vel = self._vel_at(0.5, 70)

            # Main sustained note
            self._add_track_note(inst, pitch, 0.0, dur, base_vel)

            # Wavering layer: overlapping sustained notes with slight vel variation
            segment_count = max(2, int(dur / 2.0))
            seg_dur = dur / segment_count
            for seg in range(segment_count):
                seg_start = seg * seg_dur
                seg_progress = seg_start / max(0.1, dur)
                seg_vel = self._vel_at(seg_progress, base_vel)
                # Alternate slightly louder/softer for "wavering" effect
                variation = 8 if seg % 2 == 0 else -8
                seg_vel = max(1, min(127, seg_vel + variation))
                self._add_track_note(inst, pitch, seg_start, seg_dur, seg_vel)

        for track_notes in self.tracks.values():
            all_notes.extend(track_notes)
        all_notes.sort(key=lambda n: (n.start, n.pitch))
        return all_notes

    def _pedal_point(self, chords: list[ChordLabel],
                     key: Scale, dur: float) -> list[NoteInfo]:
        """Sustained bass root/fifth with chords changing above."""
        all_notes: list[NoteInfo] = []
        first_chord = chords[0]
        root_pc = first_chord.bass if first_chord.bass is not None else first_chord.root
        fifth_pc = (root_pc + 7) % 12

        # Bass holds root for entire duration
        bass_low, bass_high = self._register_for("cello")
        bass_pitch = nearest_pitch(root_pc, bass_low + 12)
        bass_pitch = snap_to_scale(max(bass_low, min(bass_high, bass_pitch)), key)
        bass_vel = self._vel_at(0.0, 75)
        self._add_track_note("cello", bass_pitch, 0.0, dur, bass_vel)

        # Optional fifth in bass
        fifth_pitch = nearest_pitch(fifth_pc, bass_low + 12)
        fifth_pitch = snap_to_scale(max(bass_low, min(bass_high, fifth_pitch)), key)
        self._add_track_note("contrabass", fifth_pitch, 0.0, dur, max(1, bass_vel - 10))

        # Upper voices follow chord changes
        for chord in chords:
            chord_start = chord.start
            chord_dur = chord.duration
            if chord_start >= dur:
                continue
            effective_dur = min(chord_dur, dur - chord_start)
            if effective_dur <= 0:
                continue

            pcs = chord.pitch_classes()
            upper_pcs = [pc for pc in pcs if pc != root_pc]
            if not upper_pcs:
                upper_pcs = pcs[1:1] if len(pcs) > 1 else [pcs[0]] if pcs else []

            progress = chord_start / max(0.1, dur)
            vel = self._vel_at(progress, 70)

            for i, pc in enumerate(upper_pcs[:3]):
                if i == 0:
                    inst = "viola"
                elif i == 1:
                    inst = "violin"
                else:
                    inst = "flute"
                low, high = self._register_for(inst)
                center = (low + high) // 2
                pitch = nearest_pitch(pc, center)
                pitch = snap_to_scale(max(low, min(high, pitch)), key)
                self._add_track_note(inst, pitch, chord_start, effective_dur, vel)

        for track_notes in self.tracks.values():
            all_notes.extend(track_notes)
        all_notes.sort(key=lambda n: (n.start, n.pitch))
        return all_notes

    def _retransition(self, chords: list[ChordLabel],
                      key: Scale, dur: float) -> list[NoteInfo]:
        """Dominant preparation: V chord buildup with increasing density."""
        all_notes: list[NoteInfo] = []
        scale_pcs = key.degrees()

        # Use target_chord root if available, otherwise build on V
        if self.target_chord is not None:
            target_root = self.target_chord.root
        else:
            target_root = key.root

        # Dominant is 7 semitones above target
        dominant_pc = (target_root + 7) % 12
        # Dominant 7th: root, major 3rd, fifth, minor 7th
        dom7_pcs = [
            dominant_pc,
            (dominant_pc + 4) % 12,  # major third
            (dominant_pc + 7) % 12,  # fifth
            (dominant_pc + 10) % 12,  # minor seventh
        ]
        # Leading tone (tritone resolution hint)
        leading_pc = (target_root + 11) % 12

        # Build density: start sparse, end dense
        t = 0.0
        note_count = 0
        while t < dur:
            progress = t / max(0.1, dur)

            # Increasing density: shorter notes as we progress
            base_note_dur = 2.0 - progress * 1.5
            base_note_dur = max(0.25, base_note_dur)
            note_dur = min(base_note_dur, dur - t)
            if note_dur <= 0:
                break

            vel = self._vel_range(progress, 40, 115)

            # Choose tone: cycle through dominant tones, add leading tone near end
            if progress > 0.7 and note_count % 3 == 0:
                pc = leading_pc
            else:
                pc = dom7_pcs[note_count % len(dom7_pcs)]

            # Violin: dominant tones
            vlow, vhigh = self._register_for("violin")
            pitch = nearest_pitch(pc, (vlow + vhigh) // 2)
            pitch = snap_to_scale(max(vlow, min(vhigh, pitch)), key)
            self._add_track_note("violin", pitch, t, note_dur, vel)

            # Cello: sustained dominant root
            if note_count == 0:
                clow, chigh = self._register_for("cello")
                bass_pitch = nearest_pitch(dominant_pc, clow + 12)
                bass_pitch = snap_to_scale(max(clow, min(chigh, bass_pitch)), key)
                self._add_track_note("cello", bass_pitch, t, dur - t,
                                     self._vel_range(progress, 50, 100))

            # French horn: added from halfway point
            if progress > 0.5:
                hlow, hhigh = self._register_for("french_horn")
                horn_pc = dom7_pcs[(note_count + 2) % len(dom7_pcs)]
                horn_pitch = nearest_pitch(horn_pc, (hlow + hhigh) // 2)
                horn_pitch = snap_to_scale(max(hlow, min(hhigh, horn_pitch)), key)
                self._add_track_note("french_horn", horn_pitch, t, note_dur,
                                     max(1, vel - 15))

            t += note_dur
            note_count += 1

        for track_notes in self.tracks.values():
            all_notes.extend(track_notes)
        all_notes.sort(key=lambda n: (n.start, n.pitch))
        return all_notes

    def _bridge_passage(self, chords: list[ChordLabel],
                        key: Scale, dur: float) -> list[NoteInfo]:
        """Stepwise melody connecting last chord root to target_chord root."""
        all_notes: list[NoteInfo] = []
        scale_pcs = key.degrees()

        # Determine start and end pitch classes
        last_chord = chords[-1]
        start_pc = last_chord.bass if last_chord.bass is not None else last_chord.root

        if self.target_chord is not None:
            end_pc = self.target_chord.root
        else:
            end_pc = chords[0].root

        # Build stepwise path through scale degrees
        start_deg = None
        end_deg = None
        for i, pc in enumerate(scale_pcs):
            if pc == start_pc and start_deg is None:
                start_deg = i
            if pc == end_pc and end_deg is None:
                end_deg = i
        if start_deg is None:
            start_deg = 0
        if end_deg is None:
            end_deg = 0

        # Determine shortest stepwise path
        n_degrees = len(scale_pcs)
        forward_steps = (end_deg - start_deg) % n_degrees
        backward_steps = (start_deg - end_deg) % n_degrees

        if forward_steps <= backward_steps:
            path_length = forward_steps
            direction = 1
        else:
            path_length = backward_steps
            direction = -1

        # If same degree, just hold the note
        if path_length == 0:
            path_length = n_degrees
            direction = 1

        total_notes = path_length
        if total_notes == 0:
            total_notes = 1
        note_dur = dur / total_notes

        # Bass voice (cello): stepwise
        clow, chigh = self._register_for("cello")
        c_center = clow + 12
        current_deg = start_deg

        for i in range(total_notes):
            t = i * note_dur
            progress = t / max(0.1, dur)
            vel = self._vel_at(progress, 75)

            pc = scale_pcs[current_deg % n_degrees]
            pitch = nearest_pitch(pc, c_center)
            pitch = snap_to_scale(max(clow, min(chigh, pitch)), key)
            self._add_track_note("cello", pitch, t, note_dur, vel)

            # Melody voice (violin): follows stepwise in higher register
            vlow, vhigh = self._register_for("violin")
            v_center = (vlow + vhigh) // 2
            mel_pitch = nearest_pitch(pc, v_center)
            mel_pitch = snap_to_scale(max(vlow, min(vhigh, mel_pitch)), key)
            self._add_track_note("violin", mel_pitch, t, note_dur, max(1, vel + 10))

            # Harmony voice (viola): a third above
            third_deg = (current_deg + 2) % n_degrees
            third_pc = scale_pcs[third_deg]
            alow, ahigh = self._register_for("viola")
            a_center = (alow + ahigh) // 2
            harm_pitch = nearest_pitch(third_pc, a_center)
            harm_pitch = snap_to_scale(max(alow, min(ahigh, harm_pitch)), key)
            self._add_track_note("viola", harm_pitch, t, note_dur, max(1, vel - 5))

            # Advance step
            current_deg = (current_deg + direction) % n_degrees

        # Ensure final note lands on target root
        if total_notes > 0:
            final_t = (total_notes - 1) * note_dur
            final_pc = end_pc
            clow, chigh = self._register_for("cello")
            c_center = clow + 12
            pitch = nearest_pitch(final_pc, c_center)
            pitch = snap_to_scale(max(clow, min(chigh, pitch)), key)
            if self.tracks.get("cello"):
                last_cello = self.tracks["cello"][-1]
                last_cello.pitch = pitch

        for track_notes in self.tracks.values():
            all_notes.extend(track_notes)
        all_notes.sort(key=lambda n: (n.start, n.pitch))
        return all_notes
