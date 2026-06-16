# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
composer/transition_coordinator.py — TransitionCoordinator.

Orchestrates multi-track section-level transitions, allowing for coordinated swells,
ducking of low frequencies (vacuum effect), and lead-in fills.
"""

from __future__ import annotations

from dataclasses import replace

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
                        # Duck on a copy so the caller's NoteInfo objects in the
                        # original tracks dict are not mutated in place.
                        note = replace(note, velocity=max(1, min(127, int(note.velocity * duck_factor))))
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
        Overwrites a window in the target track with fill_notes.
        
        The fill_notes should be relative to 0.0, and they will be 
        placed starting at start_beat. Any existing notes that overlap
        the range [start_beat, start_beat + fill_duration] are removed.
        """
        if target_track not in tracks or not fill_notes:
            return

        track_obj = tracks[target_track]
        is_track = isinstance(track_obj, Track)
        notes = track_obj.notes if is_track else track_obj

        # Calculate fill window
        fill_duration = max(fn.start + fn.duration for fn in fill_notes)
        end_beat = start_beat + fill_duration

        # Carve out space: keep only notes that don't overlap the fill window
        retained_notes = []
        for note in notes:
            note_end = note.start + note.duration
            # Check for overlap
            overlaps = max(0.0, min(end_beat, note_end) - max(start_beat, note.start))
            if overlaps <= 0.0:
                retained_notes.append(note)
        
        # Shift and add fill notes
        shifted_fill = []
        for fn in fill_notes:
            new_note = NoteInfo(
                pitch=fn.pitch,
                start=round(start_beat + fn.start, 6),
                duration=fn.duration,
                velocity=fn.velocity,
                articulation=fn.articulation,
                expression=fn.expression,
            )
            shifted_fill.append(new_note)

        retained_notes.extend(shifted_fill)
        retained_notes.sort(key=lambda note: note.start)

        if is_track:
            track_obj.notes = retained_notes
        else:
            tracks[target_track] = retained_notes

    @staticmethod
    def orchestrate_transition(
        tracks: dict[str, "Track | list[NoteInfo]"],
        cc_events: dict[str, list[tuple[float, int, int]]],
        boundary_beat: float,
        pre_duration: float = 4.0,
        _post_duration: float = 2.0,
        duck_tracks: list[str] | None = None,
        duck_factor: float = 0.0,
        sweep_tracks: list[str] | None = None,
        sweep_cc: int = 74,
        sweep_start_val: int = 40,
        sweep_end_val: int = 110,
        sweep_curve: str = "exponential",
        fill_track: str | None = None,
        fill_notes: "list[NoteInfo] | None" = None,
    ) -> None:
        """
        Unified high-level transition coordinator.

        Orchestrates all three transition effects in a single call at a section boundary:
        1. Bass/drum **pre-drop ducking** over the window before the boundary.
        2. **CC automation sweeps** (cutoff/volume) leading into the boundary.
        3. **Lead-in fill** insertion starting at the boundary beat.

        Parameters
        ----------
        tracks : dict
            Multi-track note dictionary (Track objects or bare NoteInfo lists).
        cc_events : dict
            CC event dictionary to be mutated with sweep automation.
        boundary_beat : float
            The downbeat where the new section begins.
        pre_duration : float
            How many beats before the boundary to start ducking and sweeping (default 4).
        post_duration : float
            Reserved for future: post-boundary tail handling (default 2).
        duck_tracks : list[str], optional
            Track names to duck/silence before the boundary (e.g. ["bass", "kick"]).
        duck_factor : float
            0.0 = complete silence, 0.0–1.0 = scaled velocity during the duck window.
        sweep_tracks : list[str], optional
            Track names to apply an automation CC sweep to (e.g. ["pad", "strings"]).
        sweep_cc : int
            MIDI CC number for the sweep (74 = filter cutoff, 7 = volume).
        sweep_start_val : int
            Initial CC value at the start of the sweep window.
        sweep_end_val : int
            Final CC value at the boundary beat.
        sweep_curve : str
            Curve type: "exponential", "linear", or "sine".
        fill_track : str, optional
            Track name to inject the lead-in fill into.
        fill_notes : list[NoteInfo], optional
            Notes for the lead-in fill (relative to 0.0 — they will be shifted to boundary_beat).
        """
        duck_start = max(0.0, boundary_beat - pre_duration)
        duck_end = boundary_beat

        # 1. Pre-drop bass/drum ducking
        if duck_tracks:
            TransitionCoordinator.apply_ducking(
                tracks, duck_tracks,
                start_beat=duck_start,
                end_beat=duck_end,
                duck_factor=duck_factor,
            )

        # 2. Filter / volume sweep leading into the boundary
        if sweep_tracks:
            TransitionCoordinator.apply_sweeps(
                tracks, cc_events, sweep_tracks,
                cc_num=sweep_cc,
                start_val=sweep_start_val,
                end_val=sweep_end_val,
                start_beat=duck_start,
                end_beat=duck_end,
                curve_type=sweep_curve,
                steps=20,
            )

        # 3. Melodic / percussive lead-in fill
        if fill_track and fill_notes:
            TransitionCoordinator.apply_lead_in_fill(
                tracks, fill_track, fill_notes, start_beat=boundary_beat
            )
