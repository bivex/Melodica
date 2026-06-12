# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
form_validator.py — Musical form and arrangement validator.

Checks tracks_data + optional MusicalForm against established composition
rules (Grove Music / Kostka & Payne / Aldwell & Schachter) and prints
warnings when the arrangement deviates.

Two usage modes:

1. Automatic — via export_multitrack_midi(..., validate_form=True):
       Runs after MIDI is written, prints warnings to stdout.

2. Manual — call validate() directly:
       from melodica.form_validator import validate
       issues = validate(tracks_data, bpm=120.0, form=my_form)

Rules checked
─────────────
Arrangement rules (always, no MusicalForm needed):
  ARR-1  All instruments play from beat 0 — no textural buildup
  ARR-2  No bass / low register present (below MIDI 48)
  ARR-3  No high register present (above MIDI 84)
  ARR-4  Register imbalance — LOW or HIGH band out of 15-35% range
  ARR-5  Percussion active throughout entire piece (should rest in quiet sections)
  ARR-6  Dynamic range too narrow (velocity spread < 20)
  ARR-7  Single-density throughout — no energy curve (density variance < 0.05)

Form rules (require MusicalForm):
  FORM-1  Sonata: development has no key modulation (< 2 distinct keys)
  FORM-2  Sonata: recapitulation does not return to tonic key
  FORM-3  Sonata: exposition missing second theme (< 2 distinct melodic layers)
  FORM-4  Section dynamics ignored — all tracks same velocity across sections
  FORM-5  Percussion plays in pp/p sections (should rest)
  FORM-6  No cadential silence at end of section (notes run into barline)
  FORM-7  Tempo multiplier = 1.0 for all sections (no tempo shaping)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from melodica.types import NoteInfo
    from melodica.form import MusicalForm, FormSection


# ---------------------------------------------------------------------------
# Issue dataclass
# ---------------------------------------------------------------------------

@dataclass
class FormIssue:
    code: str        # e.g. "ARR-1"
    severity: str    # "WARNING" | "INFO"
    message: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.code}  {self.message}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PERC_KEYWORDS = ("drum", "percussion", "perc", "kit", "taiko", "ghost",
                  "snare", "kick", "cymbal", "hihat")


def _is_percussion(name: str) -> bool:
    low = name.lower()
    return any(k in low for k in _PERC_KEYWORDS)


def _track_density(notes: list[NoteInfo], start: float, end: float) -> float:
    """Notes per beat in [start, end)."""
    span = max(end - start, 0.001)
    count = sum(1 for n in notes if start <= float(n.start) < end)
    return count / span


def _track_entry_beat(notes: list[NoteInfo]) -> float:
    if not notes:
        return 0.0
    return min(float(n.start) for n in notes)


def _total_duration(tracks_data: dict[str, list[NoteInfo]]) -> float:
    end = 0.0
    for notes in tracks_data.values():
        for n in notes:
            e = float(n.start) + float(n.duration)
            if e > end:
                end = e
    return end


def _velocity_range(notes: list[NoteInfo]) -> tuple[int, int]:
    if not notes:
        return (64, 64)
    vels = [int(n.velocity) for n in notes]
    return (min(vels), max(vels))


def _pitch_band_fractions(tracks_data: dict[str, list[NoteInfo]]) -> dict[str, float]:
    """Fraction of total note events in LOW (<48) / MID (48-84) / HIGH (>84)."""
    low = mid = high = 0
    for name, notes in tracks_data.items():
        if _is_percussion(name):
            continue
        for n in notes:
            p = int(round(float(n.pitch)))
            if p < 48:
                low += 1
            elif p <= 84:
                mid += 1
            else:
                high += 1
    total = max(low + mid + high, 1)
    return {"low": low / total, "mid": mid / total, "high": high / total}


# ---------------------------------------------------------------------------
# Arrangement rules (no MusicalForm needed)
# ---------------------------------------------------------------------------

def _check_arrangement(
    tracks_data: dict[str, list[NoteInfo]],
    bpm: float,
) -> list[FormIssue]:
    issues: list[FormIssue] = []
    total_dur = _total_duration(tracks_data)
    if total_dur < 1.0:
        return issues

    pitched = {n: v for n, v in tracks_data.items() if not _is_percussion(n) and v}
    perc    = {n: v for n, v in tracks_data.items() if _is_percussion(n) and v}

    # ARR-1: all pitched instruments enter at beat 0 (no buildup)
    entry_beats = {n: _track_entry_beat(v) for n, v in pitched.items()}
    if entry_beats and max(entry_beats.values()) < 0.5:
        issues.append(FormIssue(
            "ARR-1", "WARNING",
            "All instruments enter at beat 0 — no textural buildup. "
            "Consider staggering entrances (intro should start sparse)."
        ))

    # ARR-2: no bass register
    has_bass = any(
        any(float(n.pitch) < 48 for n in v)
        for n, v in pitched.items()
    )
    if not has_bass and pitched:
        issues.append(FormIssue(
            "ARR-2", "WARNING",
            "No notes below MIDI 48 (C3) — bass register is empty. "
            "Add contrabass, bass guitar, or low brass for sub-bass foundation."
        ))

    # ARR-3: no high register
    has_high = any(
        any(float(n.pitch) > 84 for n in v)
        for n, v in pitched.items()
    )
    if not has_high and pitched:
        issues.append(FormIssue(
            "ARR-3", "INFO",
            "No notes above MIDI 84 (C6) — high register is empty. "
            "Consider flute, glockenspiel, or violin harmonics for air/shimmer."
        ))

    # ARR-4: frequency balance
    bands = _pitch_band_fractions(tracks_data)
    if bands["low"] < 0.10:
        issues.append(FormIssue(
            "ARR-4", "WARNING",
            f"LOW register only {bands['low']*100:.1f}% of notes (target 15-35%). "
            "Add contrabass or pedal bass."
        ))
    if bands["high"] < 0.10:
        issues.append(FormIssue(
            "ARR-4", "INFO",
            f"HIGH register only {bands['high']*100:.1f}% of notes (target 15-35%). "
            "Add glockenspiel, piccolo, or high strings."
        ))
    if bands["mid"] > 0.80:
        issues.append(FormIssue(
            "ARR-4", "WARNING",
            f"MID register is {bands['mid']*100:.1f}% of notes — overcrowded. "
            "Spread instruments into low and high registers."
        ))

    # ARR-5: percussion plays throughout (should rest in quiet sections)
    if perc:
        # check if percussion has notes in the first 10% of the piece
        first_window = total_dur * 0.10
        perc_early = any(
            any(float(n.start) < first_window for n in v)
            for v in perc.values()
        )
        if perc_early:
            issues.append(FormIssue(
                "ARR-5", "INFO",
                "Percussion enters in the first 10% of the piece. "
                "Intros typically start without percussion to build tension."
            ))

    # ARR-6: dynamic range
    all_vels: list[int] = []
    for notes in pitched.values():
        all_vels.extend(int(n.velocity) for n in notes)
    if all_vels:
        spread = max(all_vels) - min(all_vels)
        if spread < 20:
            issues.append(FormIssue(
                "ARR-6", "WARNING",
                f"Velocity spread is only {spread} (min={min(all_vels)}, max={max(all_vels)}). "
                "Target ≥40 for expressive dynamics. Apply crescendo/decrescendo curves."
            ))

    # ARR-7: energy curve — split into thirds, check density variance
    third = total_dur / 3.0
    densities: list[float] = []
    for start in (0.0, third, third * 2):
        end = start + third
        d = sum(
            _track_density(v, start, end)
            for n, v in pitched.items()
        )
        densities.append(d)
    if densities:
        mean_d = sum(densities) / len(densities)
        variance = sum((d - mean_d) ** 2 for d in densities) / len(densities)
        if mean_d > 0 and (variance / (mean_d ** 2 + 1e-9)) < 0.05:
            issues.append(FormIssue(
                "ARR-7", "INFO",
                f"Density is uniform across the piece (variance ratio {variance/(mean_d**2+1e-9):.3f}). "
                "A strong energy curve requires buildup → climax → release. "
                "Thin out the intro and coda."
            ))

    return issues


# ---------------------------------------------------------------------------
# Form rules (require MusicalForm)
# ---------------------------------------------------------------------------

def _check_form(
    tracks_data: dict[str, list[NoteInfo]],
    bpm: float,
    form: MusicalForm,
) -> list[FormIssue]:
    issues: list[FormIssue] = []

    pitched = {n: v for n, v in tracks_data.items() if not _is_percussion(n) and v}
    perc    = {n: v for n, v in tracks_data.items() if _is_percussion(n) and v}

    # FORM-7: all tempo multipliers = 1.0
    multipliers = {s.tempo_multiplier for s in form.sections}
    if len(multipliers) == 1 and list(multipliers)[0] == 1.0:
        issues.append(FormIssue(
            "FORM-7", "WARNING",
            "All FormSections have tempo_multiplier=1.0 — no tempo shaping. "
            "Intros/outros should be slower (0.8-0.9), climaxes faster (1.1-1.2)."
        ))

    # FORM-5: percussion in pp/p sections
    quiet = {"pp", "p"}
    for sec in form.sections:
        if sec.dynamics not in quiet:
            continue
        sec_perc_notes = [
            n for track_notes in perc.values()
            for n in track_notes
            if sec.start_beat <= float(n.start) < sec.end_beat
        ]
        if sec_perc_notes:
            issues.append(FormIssue(
                "FORM-5", "WARNING",
                f"Section '{sec.name}' (dynamics={sec.dynamics}): percussion plays "
                f"during a quiet section — should rest. "
                f"({len(sec_perc_notes)} percussion notes found)"
            ))

    # FORM-6: no silence before section boundary (notes bleed across barlines)
    beats_per_bar = 4.0
    tail_window = beats_per_bar  # look at last bar of each section
    for sec in form.sections:
        section_end = sec.end_beat
        window_start = section_end - tail_window
        notes_in_tail: list[NoteInfo] = []
        for notes in pitched.values():
            for n in notes:
                note_end = float(n.start) + float(n.duration)
                if float(n.start) >= window_start and note_end > section_end - 0.1:
                    notes_in_tail.append(n)
        if notes_in_tail:
            issues.append(FormIssue(
                "FORM-6", "INFO",
                f"Section '{sec.name}': {len(notes_in_tail)} note(s) extend to the "
                f"section boundary (beat {section_end:.1f}) without a cadential gap. "
                "Classical form expects a clear cadence before section change."
            ))

    # FORM-4: track velocities identical across sections (dynamics ignored)
    if len(form.sections) >= 2:
        for track_name, notes in pitched.items():
            sec_vels: list[float] = []
            for sec in form.sections:
                sec_notes = [n for n in notes
                             if sec.start_beat <= float(n.start) < sec.end_beat]
                if sec_notes:
                    sec_vels.append(sum(n.velocity for n in sec_notes) / len(sec_notes))
            if len(sec_vels) >= 2:
                spread = max(sec_vels) - min(sec_vels)
                if spread < 8:
                    issues.append(FormIssue(
                        "FORM-4", "WARNING",
                        f"Track '{track_name}': mean velocity barely changes across sections "
                        f"(spread={spread:.1f}). FormSection.dynamics is defined but not "
                        "reflected in note velocities — apply velocity scaling per section."
                    ))
                    break  # one warning is enough

    # FORM-1/2: sonata-specific checks
    section_names = [s.name.lower() for s in form.sections]
    is_sonata = any("development" in n or "exposition" in n for n in section_names)

    if is_sonata:
        # FORM-1: development should use multiple keys
        dev_sections = [s for s in form.sections if "development" in s.name.lower()]
        for dev in dev_sections:
            keys_in_dev = {
                s.key for s in form.sections
                if s.key is not None
                and dev.start_beat <= s.start_beat < dev.end_beat
            }
            # Also count the dev section's own key
            if dev.key is not None:
                keys_in_dev.add(dev.key)
            if len(keys_in_dev) < 2:
                issues.append(FormIssue(
                    "FORM-1", "WARNING",
                    f"Sonata development section '{dev.name}' has "
                    f"{len(keys_in_dev)} key(s). "
                    "Development should modulate through ≥2 keys "
                    "(e.g. relative major/minor, subdominant, dominant)."
                ))

        # FORM-2: recapitulation should return to tonic
        recap_sections = [s for s in form.sections
                          if "recapitulation" in s.name.lower() or "recap" in s.name.lower()]
        expo_sections  = [s for s in form.sections if "exposition" in s.name.lower()]
        for recap in recap_sections:
            if recap.key is not None and expo_sections:
                expo_key = expo_sections[0].key
                if expo_key is not None and recap.key.root != expo_key.root:
                    issues.append(FormIssue(
                        "FORM-2", "WARNING",
                        f"Sonata recapitulation '{recap.name}' key "
                        f"(root={recap.key.root}) differs from exposition "
                        f"(root={expo_key.root}). "
                        "Recapitulation must restate themes in the tonic key."
                    ))

        # FORM-3: exposition should have ≥2 melodic voices
        expo = next((s for s in form.sections if "exposition" in s.name.lower()), None)
        if expo is not None:
            active_in_expo = [
                name for name, notes in pitched.items()
                if any(expo.start_beat <= float(n.start) < expo.end_beat for n in notes)
            ]
            if len(active_in_expo) < 2:
                issues.append(FormIssue(
                    "FORM-3", "WARNING",
                    f"Sonata exposition has only {len(active_in_expo)} melodic "
                    "voice(s). Classical exposition requires ≥2 distinct themes "
                    "(primary theme + secondary theme in contrasting key)."
                ))

    return issues


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate(
    tracks_data: dict[str, list[NoteInfo]],
    bpm: float = 120.0,
    form: MusicalForm | None = None,
    *,
    label: str | None = None,
) -> list[FormIssue]:
    """
    Validate tracks_data against composition rules.

    Returns a list of FormIssue objects. Also prints them to stdout so
    album scripts see warnings during generation without extra code.

    label: optional name shown in the header (e.g. the .mid filename).
    """
    issues = _check_arrangement(tracks_data, bpm)
    if form is not None:
        issues += _check_form(tracks_data, bpm, form)

    if issues:
        header = f"  {label}" if label else "  (unnamed track)"
        print()
        print("┌─ FORM VALIDATOR " + "─" * 60)
        print(f"│  {header}")
        print("├" + "─" * 77)
        for issue in issues:
            for line in str(issue).split(". "):
                print(f"│  {line}.")
            print("│")
        print("└" + "─" * 77)

    return issues
