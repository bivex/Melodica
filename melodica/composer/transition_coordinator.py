# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
composer/transition_coordinator.py — TransitionCoordinator.

Orchestrates multi-track section-level transitions, allowing for coordinated swells,
ducking of low frequencies (vacuum effect), and lead-in fills.
"""

from __future__ import annotations

from melodica.types import NoteInfo, Track
from melodica.composer.automation import AutomationCurve


class TransitionCoordinator:
    """
    Expert-level coordinator to automate multi-track transitions and tension swells.
    """

    @staticmethod
    def apply_ducking(
        tracks: dict[str, Track | list[NoteInfo]],
        target_tracks: list[str],
        start_beat: float,
        end_beat: float,
        duck_factor: float = 0.0,
    ) -> None:
        """
        Ducks or silences notes on specific tracks that fall within a beat range.
        If a note starts or is active during the [start_beat, end_beat] window,
        its velocity is scaled by duck_factor (0.0 = complete silence/removal).
        """
        for name in target_tracks:
            if name not in tracks:
                continue

            track_obj = tracks[name]
            # Handle both Track objects and raw list[NoteInfo]
            is_track = isinstance(track_obj, Track)
            notes = track_obj.notes if is_track else track_obj

            new_notes: list[NoteInfo] = []
            for note in notes:
                note_end = note.start + note.duration
                # Check for overlap with the ducking window
                overlap = max(0.0, min(end_beat, note_end) - max(start_beat, note.start))
                if overlap > 0.0:
                    if duck_factor <= 0.0:
                        # Silence: omit the note entirely
                        continue
                    else:
                        note.scale_velocity(duck_factor)
                new_notes.append(note)

            if is_track:
                track_obj.notes = new_notes
            else:
                tracks[name] = new_notes

    @staticmethod
    def apply_sweeps(
        tracks: dict[str, Track | list[NoteInfo]],
        cc_events: dict[str, list[tuple[float, int, int]]],
        target_tracks: list[str],
        cc_num: int,
        start_val: int,
        end_val: int,
        start_beat: float,
        end_beat: float,
        curve_type: str = "exponential",
        exponent: float = 2.0,
        steps: int = 20,
    ) -> None:
        """
        Synchronously generates and injects automation curves (CC events) for target tracks.
        Updates the cc_events dictionary in-place.
        """
        for name in target_tracks:
            if name not in tracks:
                continue

            # Generate the curve
            if curve_type == "linear":
                curve = AutomationCurve.linear(cc_num, start_val, end_val, start_beat, end_beat, steps)
            elif curve_type == "sine":
                # LFO cycle period is the entire sweep duration
                period = max(0.1, end_beat - start_beat)
                curve = AutomationCurve.sine_lfo(cc_num, start_val, end_val, start_beat, end_beat, period, steps)
            else:
                # exponential
                curve = AutomationCurve.exponential(cc_num, start_val, end_val, start_beat, end_beat, exponent, steps)

            if name not in cc_events:
                cc_events[name] = []
            cc_events[name].extend(curve)
            # Sort chronologically to prevent timing glitches
            cc_events[name].sort(key=lambda ev: ev[0])

    @staticmethod
    def apply_lead_in_fill(
        tracks: dict[str, Track | list[NoteInfo]],
        target_track: str,
        fill_notes: list[NoteInfo],
        start_beat: float,
    ) -> None:
        """
        Overwrites or appends a percussive roll or melodic lead-in run to the target track
        starting at the transition boundary.
        Any existing notes in the target track starting after start_beat are replaced
        by the fill_notes.
        """
        if target_track not in tracks:
            return

        track_obj = tracks[target_track]
        is_track = isinstance(track_obj, Track)
        notes = track_obj.notes if is_track else track_obj

        # Filter out any notes in the track that start at or after start_beat
        retained_notes = [note for note in notes if note.start < start_beat]
        
        # Adjust fill note starts relative to start_beat if necessary
        for fn in fill_notes:
            # If the fill notes are relative to 0.0, shift them by start_beat
            if fn.start < start_beat:
                fn.shift_time(start_beat)

        retained_notes.extend(fill_notes)
        retained_notes.sort(key=lambda note: note.start)

        if is_track:
            track_obj.notes = retained_notes
        else:
            tracks[target_track] = retained_notes
