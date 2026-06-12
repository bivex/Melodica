# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/midi_analyzer.py — Unified MIDI diagnostic & compositional analyzer.

Combines:
  - Track stats & register bands (diagnostics.py)
  - Psychoacoustic checks — masking, fusion, blur, brightness (psychoacoustic.py)
  - Harmonic clashes — interval dissonance (harmonic_verifier.py)
  - Key detection, ambitus, melodic motion, consonance, LIM (music21_analyzer.py)
  - Role assignment — BASS/LEAD/PAD/PERC/STRINGS/CHOIR/FX (album_pipeline.py)
  - Timeline overview (midi_doctor.py)

Usage:
    python3 scripts/midi_analyzer.py output/album_ainulindale/
    python3 scripts/midi_analyzer.py output/album_ainulindale/I_The_Theme_of_Eru.mid
    python3 scripts/midi_analyzer.py output/album_ainulindale/ --no-music21
"""

import sys
import argparse
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mido
from melodica.types import NoteInfo
from melodica.composer.psychoacoustic import (
    detect_frequency_masking,
    detect_temporal_masking,
    detect_fusion,
    detect_blur,
    detect_register_masking,
    detect_brightness_overload,
)
from melodica.composer.harmonic_verifier import detect_clashes, VerifierConfig


# ---------------------------------------------------------------------------
# MIDI → tracks dict
# ---------------------------------------------------------------------------

def midi_to_tracks(path: str) -> tuple[dict[str, list[NoteInfo]], "mido.MidiFile", set[str]]:
    mid = mido.MidiFile(path)
    tracks = {}
    percussion: set[str] = set()
    _PERC_KEYWORDS = ("drum", "perc", "kick", "snare", "hihat", "hat",
                      "taiko", "cymbal", "kit")
    for track in mid.tracks:
        name = None
        notes_on = {}
        note_list = []
        channels: set[int] = set()
        tick = 0
        for msg in track:
            tick += msg.time
            if msg.type == "track_name":
                name = msg.name
            elif msg.type == "note_on" and msg.velocity > 0:
                notes_on[(msg.note, msg.channel)] = (tick, msg.velocity)
                channels.add(msg.channel)
            elif msg.type in ("note_off",) or (msg.type == "note_on" and msg.velocity == 0):
                key = (msg.note, msg.channel)
                if key in notes_on:
                    on_tick, vel = notes_on.pop(key)
                    duration = (tick - on_tick) / mid.ticks_per_beat
                    start = on_tick / mid.ticks_per_beat
                    note_list.append(NoteInfo(
                        pitch=msg.note,
                        start=round(start, 6),
                        duration=round(duration, 6),
                        velocity=vel,
                    ))
        if name and note_list:
            tracks[name] = sorted(note_list, key=lambda n: n.start)
            # Percussion = GM drum channel 9, or a name that looks percussive.
            low = (name or "").lower()
            if 9 in channels or any(kw in low for kw in _PERC_KEYWORDS):
                percussion.add(name)
    return tracks, mid, percussion


# ---------------------------------------------------------------------------
# Register bands (9 zones)
# ---------------------------------------------------------------------------

_REGISTER_BANDS = [
    (0, 24, "sub"),
    (24, 36, "sub-bass"),
    (36, 48, "low"),
    (48, 60, "mid-low"),
    (60, 72, "mid"),
    (72, 84, "mid-high"),
    (84, 96, "high"),
    (96, 108, "very high"),
    (108, 128, "top"),
]


def _band_for_pitch(pitch: int) -> str:
    for lo, hi, name in _REGISTER_BANDS:
        if lo <= pitch < hi:
            return name
    return "top"


# ---------------------------------------------------------------------------
# Role assignment (from album_pipeline.py)
# ---------------------------------------------------------------------------

_ROLE_HINTS = {
    "bass": "BASS", "kick": "PERC", "snare": "PERC", "hihat": "PERC",
    "hat": "PERC", "perc": "PERC", "drum": "PERC", "taiko": "PERC",
    "pad": "PAD", "drone": "PAD", "choir": "CHOIR", "voice": "CHOIR",
    "vocal": "CHOIR", "string": "STRINGS", "cello": "STRINGS",
    "viola": "STRINGS", "violin": "STRINGS", "harp": "STRINGS",
    "lead": "LEAD", "solo": "LEAD", "flute": "LEAD", "oboe": "LEAD",
    "melody": "LEAD", "fx": "FX", "impact": "FX", "cymbal": "FX",
    "shamisen": "LEAD", "sitar": "LEAD", "koto": "LEAD",
    "pizzicato": "STRINGS", "tremolo": "STRINGS",
}


def _assign_role(name: str, notes: list[NoteInfo], total_dur: float) -> str:
    name_lower = name.lower()
    for hint, role in _ROLE_HINTS.items():
        if hint in name_lower:
            return role
    if not notes:
        return "PAD"
    avg_pitch = sum(n.pitch for n in notes) / len(notes)
    density = len(notes) / max(total_dur, 1.0)
    if avg_pitch < 48:
        return "BASS"
    if density < 0.08:
        return "PAD"
    if avg_pitch > 75 and density < 0.05:
        return "FX"
    if avg_pitch > 60 and density > 0.15:
        return "LEAD"
    if 40 < avg_pitch < 75 and 0.05 < density < 0.3:
        return "STRINGS"
    return "LEAD"


# ---------------------------------------------------------------------------
# Analysis sections
# ---------------------------------------------------------------------------

def analyze_track_stats(tracks: dict, total_dur: float):
    print(f"\n{'─' * 78}")
    print(f"  TRACK STATS & ROLES")
    print(f"{'─' * 78}")
    print(f"  {'Track':22s} {'Notes':>6s} {'Range':>12s} {'Band':>10s} "
          f"{'Vel':>9s} {'Density':>8s} {'Role':>8s}")
    print(f"  {'─' * 22} {'─' * 6} {'─' * 12} {'─' * 10} {'─' * 9} {'─' * 8} {'─' * 8}")

    for name, notes in sorted(tracks.items()):
        if not notes:
            continue
        pitches = [n.pitch for n in notes]
        vels = [n.velocity for n in notes]
        lo, hi = min(pitches), max(pitches)
        avg_p = sum(pitches) / len(pitches)
        density = len(notes) / max(total_dur, 1.0)
        band = _band_for_pitch(int(avg_p))
        role = _assign_role(name, notes, total_dur)
        print(f"  {name:22s} {len(notes):6d} {lo:>5d}-{hi:<5d}  {band:>10s} "
              f"{min(vels):>3d}-{max(vels):<3d} {density:>7.2f}f/s {role:>8s}")


def analyze_psychoacoustic(tracks: dict):
    print(f"\n{'─' * 78}")
    print(f"  PSYCHOACOUSTIC ANALYSIS")
    print(f"{'─' * 78}")

    checks = [
        ("Frequency masking", detect_frequency_masking(tracks)),
        ("Temporal masking", detect_temporal_masking(tracks)),
        ("Harmonic fusion", detect_fusion(tracks)),
        ("Rhythmic blur", detect_blur(tracks)),
        ("Register masking", detect_register_masking(tracks)),
        ("Brightness overload", detect_brightness_overload(tracks)),
    ]

    total = sum(len(evts) for _, evts in checks)
    print(f"  Total issues: {total}\n")
    for name, evts in checks:
        bar = "█" * min(len(evts) // 10, 30)
        print(f"  {name:25s}: {len(evts):5d}  {bar}")


def analyze_harmonic(tracks: dict):
    print(f"\n{'─' * 78}")
    print(f"  HARMONIC ANALYSIS")
    print(f"{'─' * 78}")

    clashes = detect_clashes(tracks, VerifierConfig(dissonance_tolerance=0.5))
    by_interval = Counter()
    by_pair = Counter()
    for c in clashes:
        by_interval[c.interval] += 1
        by_pair[f"{c.track_a} ↔ {c.track_b}"] += 1

    interval_names = {
        1: "m2", 2: "M2", 3: "m3", 4: "M3", 5: "P4", 6: "TT",
        7: "P5", 8: "m6", 9: "M6", 10: "m7", 11: "M7",
    }

    print(f"  Cross-track clashes: {len(clashes)}")
    if by_interval:
        print(f"\n  By interval:")
        for iv, count in sorted(by_interval.items()):
            name = interval_names.get(iv, f"{iv}st")
            bar = "█" * min(count // 5, 40)
            print(f"    {name:4s} ({iv:2d}st): {count:5d}  {bar}")

    if by_pair:
        print(f"\n  Top clashing pairs:")
        for pair, count in by_pair.most_common(8):
            print(f"    {pair:40s}: {count:5d}")


def analyze_register_distribution(tracks: dict, total_notes: int) -> Counter:
    print(f"\n{'─' * 78}")
    print(f"  REGISTER DISTRIBUTION")
    print(f"{'─' * 78}")

    band_counts = Counter()
    for notes in tracks.values():
        for n in notes:
            band_counts[_band_for_pitch(n.pitch)] += 1

    for lo, hi, name in _REGISTER_BANDS:
        count = band_counts.get(name, 0)
        pct = count / max(total_notes, 1) * 100
        bar = "█" * min(int(pct), 40)
        print(f"  {name:>10s} ({lo:3d}-{hi:3d}): {count:6d} {pct:5.1f}%  {bar}")

    return band_counts


# ---------------------------------------------------------------------------
# Balance verdict: LOW / MID / HIGH
# ---------------------------------------------------------------------------

# Ideal ranges for cinematic / orchestral MIDI (percentage of total notes)
_BALANCE_TARGETS = {
    "LOW":  (15.0, 35.0),   # sub + sub-bass + low
    "MID":  (35.0, 60.0),   # mid-low + mid + mid-high
    "HIGH": (15.0, 35.0),   # high + very high + top
}

_LOW_BANDS  = {"sub", "sub-bass", "low"}
_MID_BANDS  = {"mid-low", "mid", "mid-high"}
_HIGH_BANDS = {"high", "very high", "top"}


def _balance_score(pct: float, lo: float, hi: float) -> tuple[str, str]:
    """Return (emoji, verdict text) for one zone."""
    mid = (lo + hi) / 2
    if pct < lo * 0.5:
        return "🔴", "critically low"
    if pct < lo:
        deficit = lo - pct
        return "🟡", f"{deficit:.1f}% short of target"
    if pct > hi * 1.5:
        return "🔴", "critically overloaded"
    if pct > hi:
        excess = pct - hi
        return "🟡", f"{excess:.1f}% over target"
    return "🟢", "good"


def analyze_balance_verdict(band_counts: Counter, total_notes: int):
    print(f"\n{'─' * 78}")
    print(f"  FREQUENCY BALANCE VERDICT")
    print(f"{'─' * 78}")

    total = max(total_notes, 1)
    low_n  = sum(band_counts.get(b, 0) for b in _LOW_BANDS)
    mid_n  = sum(band_counts.get(b, 0) for b in _MID_BANDS)
    high_n = sum(band_counts.get(b, 0) for b in _HIGH_BANDS)

    low_pct  = low_n  / total * 100
    mid_pct  = mid_n  / total * 100
    high_pct = high_n / total * 100

    zones = [
        ("LOW  (bass foundation)",  low_pct,  *_BALANCE_TARGETS["LOW"]),
        ("MID  (body / harmony)",   mid_pct,  *_BALANCE_TARGETS["MID"]),
        ("HIGH (air / presence)",   high_pct, *_BALANCE_TARGETS["HIGH"]),
    ]

    print(f"  {'Zone':<28s} {'%':>6s}  {'Target':>12s}  Verdict")
    print(f"  {'─' * 28} {'─' * 6}  {'─' * 12}  {'─' * 30}")

    all_ok = True
    advice_lines = []
    for label, pct, lo, hi in zones:
        emoji, verdict = _balance_score(pct, lo, hi)
        target_str = f"{lo:.0f}–{hi:.0f}%"
        bar_filled = int(pct / 2)            # 1 char per 2 %
        bar_target_hi = int(hi / 2)
        bar = ("█" * bar_filled).ljust(bar_target_hi)
        print(f"  {label:<28s} {pct:>5.1f}%  {target_str:>12s}  {emoji} {verdict}")
        if emoji != "🟢":
            all_ok = False
            zone_key = label[:3].strip()
            if pct < lo:
                advice_lines.append(f"  → Add more {zone_key} content ({pct:.1f}% vs target {lo:.0f}–{hi:.0f}%)")
            else:
                advice_lines.append(f"  → Reduce {zone_key} density or lower velocity ({pct:.1f}% vs target {lo:.0f}–{hi:.0f}%)")

    # Overall rating
    score = 0
    for _, pct, lo, hi in zones:
        e, _ = _balance_score(pct, lo, hi)
        if e == "🟢":
            score += 2
        elif e == "🟡":
            score += 1

    rating_map = {6: "EXCELLENT", 5: "GOOD", 4: "ACCEPTABLE", 3: "NEEDS WORK",
                  2: "POOR", 1: "BAD", 0: "CRITICAL"}
    rating = rating_map.get(score, "CRITICAL")
    stars  = {"EXCELLENT": "★★★★★", "GOOD": "★★★★☆", "ACCEPTABLE": "★★★☆☆",
               "NEEDS WORK": "★★☆☆☆", "POOR": "★☆☆☆☆",
               "BAD": "☆☆☆☆☆", "CRITICAL": "☆☆☆☆☆"}[rating]

    print(f"\n  Overall balance: {stars}  {rating}")

    if advice_lines:
        print(f"\n  Advice:")
        for line in advice_lines:
            print(line)
    else:
        print(f"\n  Balance is solid — no major corrections needed.")


def analyze_timeline(tracks: dict, total_dur: float):
    print(f"\n{'─' * 78}")
    print(f"  TIMELINE")
    print(f"{'─' * 78}")

    labels = ["Q1 (intro)", "Q2 (dev-1)", "Q3 (dev-2)", "Q4 (climax)"]
    for qi in range(4):
        q_start = total_dur * qi / 4
        q_end = total_dur * (qi + 1) / 4
        active = []
        for name, notes in sorted(tracks.items()):
            count = sum(1 for n in notes if n.start < q_end and (n.start + n.duration) > q_start)
            if count:
                active.append(f"{name}({count})")
        print(f"  {labels[qi]:14s} ({q_start:6.0f}-{q_end:6.0f}s):")
        if active:
            line = "    " + "  ".join(active)
            for chunk in range(0, len(line), 120):
                print(line[chunk:chunk + 120])


def analyze_music21(midi_path: str):
    try:
        import music21
        from music21 import converter, chord, key, roman, interval as m21_interval
    except ImportError:
        print(f"\n  [music21 not installed — skipping advanced analysis]")
        return

    print(f"\n{'─' * 78}")
    print(f"  ADVANCED ANALYSIS (music21)")
    print(f"{'─' * 78}")

    try:
        s = converter.parse(midi_path)
    except Exception as e:
        print(f"  Error parsing: {e}")
        return

    # Key detection
    overall_key = s.analyze('key')
    print(f"\n  Detected Key: {overall_key} (confidence: {overall_key.correlationCoefficient:.3f})")

    # Segmental key
    total_dur = s.duration.quarterLength
    if total_dur > 0:
        quarter = total_dur / 4.0
        print(f"  Segmental key analysis:")
        for q in range(4):
            start, end = q * quarter, (q + 1) * quarter
            seg_notes = []
            for p in s.parts:
                for n in p.recurse().notes:
                    if start <= n.offset < end:
                        seg_notes.append(n)
            if seg_notes:
                try:
                    seg_key = music21.stream.Stream(seg_notes).analyze('key')
                    print(f"    Q{q+1} ({start:5.0f}-{end:5.0f}): {seg_key} (conf: {seg_key.correlationCoefficient:.2f})")
                except Exception:
                    print(f"    Q{q+1}: undetermined")
            else:
                print(f"    Q{q+1}: silent")

    # Ambitus
    print(f"\n  AMBITUS:")
    ranges = []
    for i, part in enumerate(s.parts):
        notes = part.recurse().notes
        pitches = [n.pitch.ps for n in notes if n.isNote]
        if pitches:
            p_min = music21.pitch.Pitch(min(pitches)).nameWithOctave
            p_max = music21.pitch.Pitch(max(pitches)).nameWithOctave
            span = int(max(pitches) - min(pitches))
            ranges.append((i, min(pitches), max(pitches)))
            print(f"    Track {i} ({part.id or '—'}): {p_min} to {p_max} ({span} semitones)")

    # Register crossover warnings
    for i in range(len(ranges)):
        for j in range(i + 1, len(ranges)):
            _, min1, max1 = ranges[i]
            _, min2, max2 = ranges[j]
            overlap = min(max1, max2) - max(min1, min2)
            if overlap > 12:
                print(f"    [!] Track {i} ↔ Track {j}: {overlap:.0f} semitone overlap")

    # Consonance profile
    chords_obj = s.chordify()
    pure = imp = mild = sharp = 0
    total_iv = 0
    for c in chords_obj.recurse().getElementsByClass(music21.chord.Chord):
        if len(c.pitches) < 2:
            continue
        for i in range(len(c.pitches)):
            for j in range(i + 1, len(c.pitches)):
                semi = m21_interval.Interval(c.pitches[i], c.pitches[j]).semitones % 12
                total_iv += 1
                if semi in (0, 7):
                    pure += 1
                elif semi in (3, 4, 8, 9):
                    imp += 1
                elif semi in (2, 5, 10):
                    mild += 1
                elif semi in (1, 6, 11):
                    sharp += 1

    if total_iv > 0:
        con_pct = (pure + imp) / total_iv * 100
        dis_pct = (mild + sharp) / total_iv * 100
        print(f"\n  CONSONANCE: {con_pct:.1f}% consonant | {dis_pct:.1f}% dissonant")
        print(f"    Pure (P1/P5):     {pure / total_iv * 100:5.1f}%")
        print(f"    Imperfect (M3/m3): {imp / total_iv * 100:5.1f}%")
        print(f"    Mild (M2/P4/m7):  {mild / total_iv * 100:5.1f}%")
        print(f"    Sharp (TT/m2/M7): {sharp / total_iv * 100:5.1f}%")

    # Low-interval mud
    mud_count = 0
    for c in chords_obj.recurse().getElementsByClass(music21.chord.Chord):
        if len(c.pitches) < 2:
            continue
        sorted_p = sorted(c.pitches, key=lambda p: p.ps)
        for i in range(len(sorted_p) - 1):
            if sorted_p[i].ps < 48:
                diff = sorted_p[i + 1].ps - sorted_p[i].ps
                if 0 < diff <= 4:
                    mud_count += 1
    if mud_count > 0:
        print(f"\n  LOW-INTERVAL MUD: {mud_count} warnings (tight intervals below C3)")
    else:
        print(f"\n  LOW-INTERVAL MUD: clean")

    # Melodic motion
    print(f"\n  MELODIC MOTION:")
    for i, part in enumerate(s.parts):
        notes = sorted(
            [n for n in part.recurse().notes if n.isNote],
            key=lambda n: n.offset,
        )
        if len(notes) < 2:
            continue
        steps = leaps = large_leaps = resolved = 0
        for idx in range(len(notes) - 1):
            diff = abs(notes[idx + 1].pitch.ps - notes[idx].pitch.ps)
            if diff == 0:
                continue
            if diff <= 2:
                steps += 1
            else:
                leaps += 1
                if diff > 8:
                    large_leaps += 1
                    if idx + 2 < len(notes):
                        d1 = notes[idx + 1].pitch.ps - notes[idx].pitch.ps
                        d2 = notes[idx + 2].pitch.ps - notes[idx + 1].pitch.ps
                        if (d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0):
                            resolved += 1
        total_motion = steps + leaps
        if total_motion > 0:
            res_pct = (resolved / large_leaps * 100) if large_leaps else 100.0
            print(f"    Track {i}: {steps / total_motion * 100:.0f}% steps, {leaps / total_motion * 100:.0f}% leaps"
                  + (f", {large_leaps} large leaps ({res_pct:.0f}% resolved)" if large_leaps else ""))


def analyze_suggestions(tracks: dict, total_notes: int, total_dur: float):
    print(f"\n{'─' * 78}")
    print(f"  SUGGESTIONS")
    print(f"{'─' * 78}")

    suggestions = []
    for name, notes in sorted(tracks.items()):
        if not notes:
            continue
        vels = [n.velocity for n in notes]
        if max(vels) < 60:
            suggestions.append(f"  {name}: max velocity {max(vels)} — raise velocity scaling")
        if min(vels) < 12 and len(notes) > 20:
            suggestions.append(f"  {name}: min velocity {min(vels)} — inaudible notes")
        if len(notes) > 800:
            suggestions.append(f"  {name}: {len(notes)} notes — reduce density to avoid clutter")

    # Register overlap check
    regs = {}
    for name, notes in sorted(tracks.items()):
        if notes:
            pitches = [n.pitch for n in notes]
            regs[name] = (min(pitches), max(pitches))
    names = list(regs.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            alo, ahi = regs[names[i]]
            blo, bhi = regs[names[j]]
            overlap = min(ahi, bhi) - max(alo, blo)
            if overlap <= 0:
                continue
            min_span = min(ahi - alo, bhi - blo) or 1
            pct = overlap / min_span * 100
            if pct > 60:
                suggestions.append(f"  {names[i]} ↔ {names[j]}: {pct:.0f}% register overlap — separate ranges")

    # Psychoacoustic hotspots
    fm = detect_frequency_masking(tracks)
    if len(fm) > 200:
        suggestions.append(f"  Frequency masking: {len(fm)} events — spread register bands")
    rm = detect_register_masking(tracks)
    if len(rm) > 200:
        suggestions.append(f"  Register masking: {len(rm)} events — bass/melody competing below C4")
    bl = detect_blur(tracks)
    if len(bl) > 100:
        blur_by_track = Counter(e.track_a for e in bl)
        for t, c in blur_by_track.most_common(3):
            suggestions.append(f"  {t}: {c} blurry notes (<30ms) — increase durations")

    if not suggestions:
        print("  No major issues detected.")
    else:
        for s in suggestions:
            print(s)


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def analyze_file(midi_path: str, no_music21: bool = False):
    tracks, mid, percussion = midi_to_tracks(midi_path)
    if not tracks:
        print(f"  No tracks found in {midi_path}")
        return

    total_notes = sum(len(n) for n in tracks.values())
    total_dur = mid.length

    # Pitched-only view: percussion (GM ch9 / drum kits) has no harmonic or
    # register meaning, so exclude it from clash + psychoacoustic analysis.
    pitched = {n: notes for n, notes in tracks.items() if n not in percussion}

    print(f"\n{'=' * 78}")
    print(f"  {Path(midi_path).name}")
    print(f"  Duration: {total_dur:.1f}s ({total_dur / 60:.1f}min)  |  "
          f"Tracks: {len(tracks)}  |  Notes: {total_notes}")
    if percussion:
        print(f"  Percussion (excluded from harmonic analysis): {', '.join(sorted(percussion))}")
    print(f"{'=' * 78}")

    analyze_track_stats(tracks, total_dur)
    band_counts = analyze_register_distribution(tracks, total_notes)
    analyze_balance_verdict(band_counts, total_notes)
    analyze_psychoacoustic(pitched)
    analyze_harmonic(pitched)
    analyze_timeline(tracks, total_dur)

    if not no_music21:
        analyze_music21(midi_path)

    analyze_suggestions(tracks, total_notes, total_dur)
    print(f"\n{'=' * 78}\n")


def main():
    parser = argparse.ArgumentParser(description="Unified MIDI Analyzer")
    parser.add_argument("path", help="MIDI file or directory of MIDI files")
    parser.add_argument("--no-music21", action="store_true", help="Skip music21 analysis")
    args = parser.parse_args()

    target = Path(args.path)

    if target.is_dir():
        midis = sorted(target.glob("*.mid"))
        if not midis:
            print(f"No MIDI files in {target}")
            return
        print(f"\n{'#' * 78}")
        print(f"  ALBUM ANALYSIS: {target.name} ({len(midis)} tracks)")
        print(f"{'#' * 78}")
        for midi in midis:
            analyze_file(str(midi), no_music21=args.no_music21)
        print(f"\n{'#' * 78}")
        print(f"  ALBUM DONE: {len(midis)} files analyzed")
        print(f"{'#' * 78}\n")
    elif target.is_file():
        analyze_file(str(target), no_music21=args.no_music21)
    else:
        print(f"Not found: {target}")
        sys.exit(1)


if __name__ == "__main__":
    main()
