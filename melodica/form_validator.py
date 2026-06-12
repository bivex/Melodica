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
  ARR-4  Register imbalance — duration-weighted LOW/MID/HIGH out of target range
  ARR-5  Percussion active throughout entire piece (should rest in quiet sections)
  ARR-6  Dynamic range too narrow (p5–p95 velocity spread < 20)
  ARR-7  Single-density throughout — no energy curve; climax position check
  ARR-8  Parallel fifths or octaves between adjacent voices
  ARR-9  No authentic cadence (V→I) at the end of the piece
  ARR-10 Register crossing — lower voice sounds above higher voice > 2 beats

Form rules (require MusicalForm):
  FORM-1  Sonata: development has no key modulation (< 2 distinct keys)
  FORM-2  Sonata: recapitulation does not return to tonic key
  FORM-3  Sonata: exposition missing second theme (< 2 distinct melodic layers)
  FORM-4  Section dynamics ignored — velocity spread < 15 across sections
  FORM-5  Percussion plays in pp/p sections (should rest)
  FORM-6  No cadential silence at end of section (tail window = 2 beats)
  FORM-7  Tempo multiplier = 1.0 for all sections (no tempo shaping)
  FORM-8  Rondo: refrain (A) does not return in tonic each time
  FORM-9  Ternary: B section lacks tonal or dynamic contrast with A
"""

from __future__ import annotations

import math
import statistics
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


def _percentile(values: list[float], pct: float) -> float:
    """Return the pct-th percentile of a sorted list (0–100)."""
    if not values:
        return 0.0
    sv = sorted(values)
    idx = (pct / 100.0) * (len(sv) - 1)
    lo, hi = int(idx), min(int(idx) + 1, len(sv) - 1)
    frac = idx - lo
    return sv[lo] + frac * (sv[hi] - sv[lo])


def _pitch_band_fractions_duration(
    tracks_data: dict[str, list[NoteInfo]]
) -> dict[str, float]:
    """Duration-weighted fraction of pitched notes in LOW/MID/HIGH bands.

    LOW  < MIDI 48
    MID  48–84
    HIGH > 84
    """
    low_dur = mid_dur = high_dur = 0.0
    for name, notes in tracks_data.items():
        if _is_percussion(name):
            continue
        for n in notes:
            p = int(round(float(n.pitch)))
            d = float(n.duration)
            if p < 48:
                low_dur += d
            elif p <= 84:
                mid_dur += d
            else:
                high_dur += d
    total = max(low_dur + mid_dur + high_dur, 1e-9)
    return {"low": low_dur / total, "mid": mid_dur / total, "high": high_dur / total}


# Dynamics → expected mean velocity range
_DYNAMICS_VELOCITY: dict[str, tuple[int, int]] = {
    "ppp": (10,  35),
    "pp":  (20,  45),
    "p":   (35,  60),
    "mp":  (50,  75),
    "mf":  (60,  85),
    "f":   (75, 100),
    "ff":  (90, 115),
    "fff": (100, 127),
}


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

    # ARR-4: duration-weighted register balance
    bands = _pitch_band_fractions_duration(tracks_data)
    if bands["low"] < 0.10:
        issues.append(FormIssue(
            "ARR-4", "WARNING",
            f"LOW register only {bands['low']*100:.1f}% of duration (target 15–35%). "
            "Add contrabass or pedal bass."
        ))
    if bands["high"] < 0.05:
        issues.append(FormIssue(
            "ARR-4", "INFO",
            f"HIGH register only {bands['high']*100:.1f}% of duration (target 15–35%). "
            "Add glockenspiel, piccolo, or high strings."
        ))
    if bands["mid"] > 0.80:
        issues.append(FormIssue(
            "ARR-4", "WARNING",
            f"MID register is {bands['mid']*100:.1f}% of duration — overcrowded. "
            "Spread instruments into low and high registers."
        ))

    # ARR-5: percussion in intro (first 10%)
    if perc:
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

    # ARR-6: p5–p95 percentile velocity spread
    all_vels: list[float] = []
    for notes in pitched.values():
        all_vels.extend(float(n.velocity) for n in notes)
    if all_vels:
        p5  = _percentile(all_vels, 5)
        p95 = _percentile(all_vels, 95)
        spread = p95 - p5
        if spread < 20:
            issues.append(FormIssue(
                "ARR-6", "WARNING",
                f"Velocity p5–p95 spread is only {spread:.0f} "
                f"(p5={p5:.0f}, p95={p95:.0f}). "
                "Target ≥40 for expressive dynamics. Apply crescendo/decrescendo curves."
            ))

    # ARR-7: energy curve — 12 windows + climax position check
    n_windows = 12
    window = total_dur / n_windows
    densities: list[float] = []
    for i in range(n_windows):
        start = i * window
        end   = start + window
        d = sum(_track_density(v, start, end) for v in pitched.values())
        densities.append(d)

    if densities:
        mean_d   = sum(densities) / len(densities)
        variance = sum((d - mean_d) ** 2 for d in densities) / len(densities)
        vr = variance / (mean_d ** 2 + 1e-9)
        if vr < 0.05:
            issues.append(FormIssue(
                "ARR-7", "INFO",
                f"Density is uniform across the piece (variance ratio {vr:.3f}). "
                "A strong energy curve requires buildup → climax → release. "
                "Thin out the intro and coda."
            ))

        # Climax position check: peak density should be in 55–80% range
        peak_idx  = densities.index(max(densities))
        peak_pos  = (peak_idx + 0.5) / n_windows   # centre of window
        if not (0.55 <= peak_pos <= 0.80):
            issues.append(FormIssue(
                "ARR-7", "INFO",
                f"Peak density at {peak_pos*100:.0f}% of piece "
                f"(ideal: 55–80% for sonata/arch forms). "
                "Consider moving the climax later for better dramatic tension."
            ))

    # ARR-8: parallel fifths/octaves
    issues += _check_parallel_motion(pitched)

    # ARR-9: cadence detection — V→I at end
    issues += _check_cadence(pitched, total_dur)

    # ARR-10: register crossing
    issues += _check_register_crossing(pitched)

    return issues


# ---------------------------------------------------------------------------
# ARR-9 — Cadence detection
# ---------------------------------------------------------------------------

def _check_cadence(
    pitched: dict[str, list[NoteInfo]],
    total_dur: float,
    window_beats: float = 8.0,
) -> list[FormIssue]:
    """Detect presence of an authentic cadence (V or V7 → I) near the end.

    Splits the final window into two halves.  For each candidate tonic (0–11),
    checks whether the dominant PC appears in the first half and the tonic PC
    appears in the second half.  Reports only if NO tonic candidate satisfies
    both conditions.
    """
    if total_dur < window_beats * 2:
        return []

    all_end: list[tuple[float, int]] = []
    for notes in pitched.values():
        for n in notes:
            s = float(n.start)
            if s >= total_dur - window_beats:
                all_end.append((s, int(round(float(n.pitch))) % 12))

    if len(all_end) < 4:
        return []

    mid = total_dur - window_beats / 2.0
    first_pcs  = {pc for t, pc in all_end if t < mid}
    second_pcs = {pc for t, pc in all_end if t >= mid}

    # Try all 12 possible tonics — if any gives V→I, cadence is present
    for tonic_pc in range(12):
        dominant_pc = (tonic_pc + 7) % 12
        leading_pc  = (tonic_pc + 11) % 12
        has_dom = dominant_pc in first_pcs or leading_pc in first_pcs
        has_ton = tonic_pc in second_pcs
        if has_dom and has_ton:
            return []   # cadence found

    # Estimate most likely tonic for the message
    from collections import Counter
    pc_counts = Counter(pc for _, pc in all_end)
    tonic_pc = pc_counts.most_common(1)[0][0]

    return [FormIssue(
        "ARR-9", "INFO",
        f"No authentic cadence (V→I) detected in the final {window_beats:.0f} beats. "
        f"Estimated tonic: pitch class {tonic_pc}. "
        "Consider ending with a clear dominant → tonic resolution."
    )]


# ---------------------------------------------------------------------------
# ARR-10 — Register crossing
# ---------------------------------------------------------------------------

def _check_register_crossing(
    pitched: dict[str, list[NoteInfo]],
    sample_beats: float = 0.5,
    min_crossing_slots: int = 4,   # 4 × 0.5 = 2 beats
    max_warnings: int = 2,
) -> list[FormIssue]:
    """Detect register crossings: lower voice sounds above higher voice > 2 beats.

    Compares each pair of voices by their median pitch to establish
    expected ordering, then finds slots where that ordering is violated.
    """
    track_names = list(pitched.keys())
    if len(track_names) < 2:
        return []

    # Build time grids
    def _snap(notes: list[NoteInfo]) -> dict[int, float]:
        grid: dict[int, float] = {}
        for n in notes:
            t_start = float(n.start)
            t_end   = t_start + float(n.duration)
            s0 = int(t_start / sample_beats)
            s1 = max(s0 + 1, int(t_end / sample_beats))
            for s in range(s0, s1):
                p = float(n.pitch)
                if s not in grid or p > grid[s]:
                    grid[s] = p   # highest pitch active at this slot
        return grid

    snapped = {name: _snap(pitched[name]) for name in track_names}

    def _median_pitch(notes: list[NoteInfo]) -> float:
        ps = sorted(float(n.pitch) for n in notes)
        return ps[len(ps) // 2] if ps else 60.0

    issues: list[FormIssue] = []

    for i, name_a in enumerate(track_names):
        for name_b in track_names[i + 1:]:
            med_a = _median_pitch(pitched[name_a])
            med_b = _median_pitch(pitched[name_b])

            # Determine which voice is "lower" by median pitch
            # Only flag pairs with clear register separation (≥8 semitones)
            # — pairs closer than that legitimately overlap in orchestral writing
            if abs(med_a - med_b) < 8:
                continue

            lower_name  = name_a if med_a < med_b else name_b
            higher_name = name_b if med_a < med_b else name_a
            grid_low    = snapped[lower_name]
            grid_high   = snapped[higher_name]

            common = set(grid_low) & set(grid_high)
            crossing_slots = sum(
                1 for s in common if grid_low[s] > grid_high[s] + 1
            )

            if crossing_slots >= min_crossing_slots:
                duration_beats = crossing_slots * sample_beats
                issues.append(FormIssue(
                    "ARR-10", "WARNING",
                    f"Register crossing: '{lower_name}' sounds above '{higher_name}' "
                    f"for {duration_beats:.1f} beats. "
                    "Voice crossing destroys register clarity — use contrary motion."
                ))
            if len(issues) >= max_warnings:
                return issues

    return issues


# ---------------------------------------------------------------------------
# ARR-8 — Parallel motion
# ---------------------------------------------------------------------------

def _check_parallel_motion(
    pitched: dict[str, list[NoteInfo]],
    *,
    sample_beats: float = 0.25,
    max_warnings: int = 3,
) -> list[FormIssue]:
    """ARR-8 — detect parallel fifths and octaves between adjacent voices."""
    _TEXTURAL = ("ostinato", "tremolo", "pizz", "pizzicato", "arpeggio",
                 "pedal", "harp", "glock", "bell", "mallet", "timp",
                 "strings", "cello", "viola", "bass", "bass2")

    def _is_textural(name: str) -> bool:
        low = name.lower()
        return any(k in low for k in _TEXTURAL)

    def _median_pitch(notes: list[NoteInfo]) -> float:
        if not notes:
            return 60.0
        pitches = sorted(float(n.pitch) for n in notes)
        return pitches[len(pitches) // 2]

    track_names = [n for n, v in pitched.items() if v]
    if len(track_names) < 2:
        return []

    issues: list[FormIssue] = []
    seen_pairs: set[frozenset[str]] = set()

    def _snap(notes: list[NoteInfo]) -> dict[int, int]:
        grid: dict[int, int] = {}
        for n in notes:
            t_start = float(n.start)
            t_end   = t_start + float(n.duration)
            slot_start = int(t_start / sample_beats)
            slot_end   = max(slot_start + 1, int(t_end / sample_beats))
            for slot in range(slot_start, slot_end):
                p = int(round(float(n.pitch)))
                if slot not in grid or p < grid[slot]:
                    grid[slot] = p
        return grid

    snapped = {name: _snap(pitched[name]) for name in track_names}

    for i, name_a in enumerate(track_names):
        for name_b in track_names[i + 1:]:
            pair = frozenset({name_a, name_b})
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            if _is_textural(name_a) or _is_textural(name_b):
                continue

            med_a = _median_pitch(pitched[name_a])
            med_b = _median_pitch(pitched[name_b])
            if med_a < 48 and med_b < 48:
                continue

            grid_a = snapped[name_a]
            grid_b = snapped[name_b]
            common_slots = sorted(set(grid_a) & set(grid_b))
            if len(common_slots) < 2:
                continue

            parallels_fifth = parallels_octave = 0

            for idx in range(len(common_slots) - 1):
                s0, s1 = common_slots[idx], common_slots[idx + 1]
                if s1 - s0 > 4:
                    continue

                p_a0, p_a1 = grid_a[s0], grid_a[s1]
                p_b0, p_b1 = grid_b[s0], grid_b[s1]

                interval0 = abs(p_a0 - p_b0) % 12
                interval1 = abs(p_a1 - p_b1) % 12
                raw0 = abs(p_a0 - p_b0)
                raw1 = abs(p_a1 - p_b1)

                is_fifth  = (interval0 == 7 and interval1 == 7)
                is_octave = (raw0 in {0, 12, 24} and raw1 in {0, 12, 24})

                if not (is_fifth or is_octave):
                    continue

                move_a = p_a1 - p_a0
                move_b = p_b1 - p_b0
                if move_a == 0 and move_b == 0:
                    continue
                if (move_a > 0) == (move_b > 0):
                    if is_octave:
                        parallels_octave += 1
                    else:
                        parallels_fifth += 1

            if parallels_fifth >= 2:
                issues.append(FormIssue(
                    "ARR-8", "WARNING",
                    f"Parallel fifths between '{name_a}' and '{name_b}' "
                    f"({parallels_fifth} instances). "
                    "Use contrary or oblique motion to preserve voice independence."
                ))
            if parallels_octave >= 2:
                issues.append(FormIssue(
                    "ARR-8", "WARNING",
                    f"Parallel octaves between '{name_a}' and '{name_b}' "
                    f"({parallels_octave} instances). "
                    "Parallel octaves merge two voices into one — use contrary motion."
                ))
            if len(issues) >= max_warnings:
                return issues

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

    # FORM-7: all tempo multipliers = 1.0 or range too narrow
    multipliers = [s.tempo_multiplier for s in form.sections]
    if multipliers:
        if len(set(multipliers)) == 1 and multipliers[0] == 1.0:
            issues.append(FormIssue(
                "FORM-7", "WARNING",
                "All FormSections have tempo_multiplier=1.0 — no tempo shaping. "
                "Intros/outros should be slower (0.8–0.9), climaxes faster (1.1–1.2)."
            ))
        elif max(multipliers) - min(multipliers) < 0.10:
            issues.append(FormIssue(
                "FORM-7", "INFO",
                f"Tempo multiplier range is only "
                f"{min(multipliers):.2f}–{max(multipliers):.2f} — effectively flat. "
                "Aim for at least one section below 0.90 or above 1.10."
            ))

    # FORM-5: percussion in pp/p sections
    quiet = {"pp", "p", "ppp"}
    for sec in form.sections:
        if sec.dynamics not in quiet:
            continue
        sec_perc_notes = [
            n for track_notes in perc.values()
            for n in track_notes
            if sec.start_beat <= float(n.start) < sec.end_beat
            and int(n.velocity) >= 40   # velocity < 40 = soft roll, allowed
        ]
        if sec_perc_notes:
            issues.append(FormIssue(
                "FORM-5", "WARNING",
                f"Section '{sec.name}' (dynamics={sec.dynamics}): "
                f"{len(sec_perc_notes)} percussion note(s) above vel=40 "
                "during a quiet section — should rest."
            ))

    # FORM-6: no cadential gap before section boundary (tail window = 2 beats)
    tail_window = 2.0
    for sec in form.sections:
        section_end  = sec.end_beat
        window_start = section_end - tail_window
        bleed: list[NoteInfo] = []
        for notes in pitched.values():
            for n in notes:
                note_end = float(n.start) + float(n.duration)
                if float(n.start) >= window_start and note_end > section_end - 0.1:
                    bleed.append(n)
        if bleed:
            issues.append(FormIssue(
                "FORM-6", "INFO",
                f"Section '{sec.name}': {len(bleed)} note(s) extend to boundary "
                f"(beat {section_end:.1f}) without a cadential gap. "
                "Classical form expects silence before section change."
            ))

    # FORM-4: track velocities differ < 15 across sections + dynamics→velocity check
    if len(form.sections) >= 2:
        violations: list[str] = []
        for track_name, notes in pitched.items():
            sec_vels: list[float] = []
            for sec in form.sections:
                sec_notes = [n for n in notes
                             if sec.start_beat <= float(n.start) < sec.end_beat]
                if sec_notes:
                    mean_vel = sum(n.velocity for n in sec_notes) / len(sec_notes)
                    sec_vels.append(mean_vel)

                    # Check dynamics→velocity mapping
                    if sec.dynamics and sec.dynamics in _DYNAMICS_VELOCITY:
                        lo, hi = _DYNAMICS_VELOCITY[sec.dynamics]
                        if not (lo <= mean_vel <= hi):
                            issues.append(FormIssue(
                                "FORM-4", "INFO",
                                f"Track '{track_name}', section '{sec.name}' "
                                f"(dynamics={sec.dynamics}): mean velocity {mean_vel:.0f} "
                                f"outside expected range {lo}–{hi}."
                            ))

            if len(sec_vels) >= 2:
                spread = max(sec_vels) - min(sec_vels)
                if spread < 15:
                    violations.append(track_name)

        if violations:
            issues.append(FormIssue(
                "FORM-4", "WARNING",
                f"Tracks {violations}: mean velocity spread < 15 across sections. "
                "Section dynamics are not reflected in note velocities — "
                "apply velocity scaling per section."
            ))

    # FORM-1/2/3: sonata-specific checks
    section_names = [s.name.lower() for s in form.sections]
    is_sonata = any("development" in n or "exposition" in n for n in section_names)

    if is_sonata:
        # FORM-1: development modulates through ≥2 keys
        # Group all development sub-sections (development, development_1, development_2, ...)
        # into a single logical block and count distinct keys across all of them.
        dev_sections = [s for s in form.sections if "development" in s.name.lower()]
        if dev_sections:
            keys_in_dev = set()
            for dev in dev_sections:
                if dev.key is not None:
                    keys_in_dev.add(dev.key)
                # Also collect keys of any nested sections within this dev range
                for s in form.sections:
                    if s.key is not None and dev.start_beat <= s.start_beat < dev.end_beat:
                        keys_in_dev.add(s.key)
            if len(keys_in_dev) < 2:
                issues.append(FormIssue(
                    "FORM-1", "WARNING",
                    f"Sonata development has {len(keys_in_dev)} key(s). "
                    "Development should modulate through ≥2 keys "
                    "(relative major/minor, subdominant, dominant)."
                ))

        # FORM-2: recapitulation in tonic
        recap_sections = [s for s in form.sections
                          if "recapitulation" in s.name.lower() or "recap" in s.name.lower()]
        expo_sections  = [s for s in form.sections if "exposition" in s.name.lower()]
        for recap in recap_sections:
            if recap.key is not None and expo_sections:
                expo_key = expo_sections[0].key
                if expo_key is not None and recap.key.root != expo_key.root:
                    issues.append(FormIssue(
                        "FORM-2", "WARNING",
                        f"Sonata recapitulation '{recap.name}' key (root={recap.key.root}) "
                        f"differs from exposition (root={expo_key.root}). "
                        "Recapitulation must restate themes in the tonic key."
                    ))

        # FORM-3: exposition has ≥2 melodic voices
        expo = next((s for s in form.sections if "exposition" in s.name.lower()), None)
        if expo is not None:
            active = [
                name for name, notes in pitched.items()
                if any(expo.start_beat <= float(n.start) < expo.end_beat for n in notes)
            ]
            if len(active) < 2:
                issues.append(FormIssue(
                    "FORM-3", "WARNING",
                    f"Sonata exposition has only {len(active)} melodic voice(s). "
                    "Classical exposition requires ≥2 distinct themes "
                    "(primary + secondary in contrasting key)."
                ))

    # FORM-8: Rondo — refrain (A) returns in tonic each time
    is_rondo = any("rondo" in n or "refrain" in n for n in section_names)
    if is_rondo:
        issues += _check_rondo_refrain(form)

    # FORM-9: Ternary — B section contrast
    is_ternary = (
        any("ternary" in n for n in section_names)
        or (
            sum(1 for n in section_names if n.startswith("a")) >= 2
            and any(n.startswith("b") for n in section_names)
        )
    )
    if is_ternary:
        issues += _check_ternary_contrast(form, pitched)

    return issues


# ---------------------------------------------------------------------------
# FORM-8 — Rondo refrain check
# ---------------------------------------------------------------------------

def _check_rondo_refrain(form: MusicalForm) -> list[FormIssue]:
    """FORM-8: each refrain (A) section must return in the same tonic key."""
    refrains = [
        s for s in form.sections
        if s.name.lower().startswith("a") or "refrain" in s.name.lower()
    ]
    if len(refrains) < 2:
        return []

    keyed = [r for r in refrains if r.key is not None]
    if len(keyed) < 2:
        return []

    tonic = keyed[0].key
    assert tonic is not None  # guaranteed by keyed filter above
    issues: list[FormIssue] = []
    for ref in keyed[1:]:
        assert ref.key is not None  # guaranteed by keyed filter above
        if ref.key.root != tonic.root:
            issues.append(FormIssue(
                "FORM-8", "WARNING",
                f"Rondo refrain '{ref.name}' returns in key root={ref.key.root} "
                f"instead of tonic root={tonic.root}. "
                "In rondo form, the refrain must always return in the home key."
            ))
    return issues


# ---------------------------------------------------------------------------
# FORM-9 — Ternary B-section contrast
# ---------------------------------------------------------------------------

def _check_ternary_contrast(
    form: MusicalForm,
    pitched: dict[str, list[NoteInfo]],
) -> list[FormIssue]:
    """FORM-9: B section should contrast A in tonality or mean velocity."""
    a_sections = [s for s in form.sections if s.name.lower().startswith("a")]
    b_sections = [s for s in form.sections if s.name.lower().startswith("b")]
    if not a_sections or not b_sections:
        return []

    a = a_sections[0]
    b = b_sections[0]
    issues: list[FormIssue] = []

    # Tonal contrast: keys should differ
    if a.key is not None and b.key is not None:
        if a.key.root == b.key.root and a.key.mode == b.key.mode:
            issues.append(FormIssue(
                "FORM-9", "WARNING",
                f"Ternary B section '{b.name}' is in the same key as A (root={a.key.root}). "
                "B section should provide tonal contrast "
                "(relative minor, dominant, or parallel mode)."
            ))

    # Dynamic contrast: mean velocity should differ by ≥15

    # Dynamic contrast: mean velocity should differ by ≥15
    def _mean_vel_in_section(sec: FormSection) -> float | None:
        vels: list[float] = []
        for notes in pitched.values():
            for n in notes:
                if sec.start_beat <= float(n.start) < sec.end_beat:
                    vels.append(float(n.velocity))
        return sum(vels) / len(vels) if vels else None

    vel_a = _mean_vel_in_section(a)
    vel_b = _mean_vel_in_section(b)
    if vel_a is not None and vel_b is not None:
        if abs(vel_a - vel_b) < 15:
            issues.append(FormIssue(
                "FORM-9", "INFO",
                f"Ternary B section '{b.name}' has similar mean velocity to A "
                f"(A={vel_a:.0f}, B={vel_b:.0f}, diff={abs(vel_a-vel_b):.0f}). "
                "B section should contrast dynamically — consider pp vs mf."
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
