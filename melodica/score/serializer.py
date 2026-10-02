# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.score.serializer — Serializer from Song IR to .song human-readable format.
"""

from __future__ import annotations

from melodica.score.ir import Song, TrackArrange

_ROOT_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

_QUALITY_SHORT = {
    "MAJOR": "",
    "MINOR": "m",
    "DIMINISHED": "dim",
    "AUGMENTED": "+",
    "MAJOR7": "maj7",
    "DOMINANT7": "7",
    "MINOR7": "m7",
    "HALF_DIM7": "m7b5",
    "FULL_DIM7": "dim7",
    "SUS2": "sus2",
    "SUS4": "sus4",
    "POWER": "5",
    "MAJOR9": "maj9",
    "MINOR9": "m9",
    "ADD9": "add9",
}


def _format_chord(chord) -> str:
    root_str = _ROOT_NAMES[chord.root % 12]
    q_str = _QUALITY_SHORT.get(chord.quality.name, chord.quality.name.lower())
    bass_str = f"/{_ROOT_NAMES[chord.bass % 12]}" if chord.bass is not None else ""
    return f"{root_str}{q_str}{bass_str}"


def _serialize_header(song: Song) -> list[str]:
    lines = [
        f"title: {song.title}",
        f"key: {_ROOT_NAMES[song.key.root % 12]}{'m' if 'minor' in song.key.mode.name.lower() else ''}",
        f"tempo: {int(song.tempo) if song.tempo.is_integer() else song.tempo}",
        f"time: {song.time_signature[0]}/{song.time_signature[1]}",
        f"feel: {song.feel}",
    ]
    if song.seed is not None:
        lines.append(f"seed: {song.seed}")
    return lines


def _serialize_sections(song: Song) -> list[str]:
    lines: list[str] = []
    for sec_name, sec in song.sections.items():
        header = f"[{sec_name}]"
        if sec.repeats > 1:
            header += f" x{sec.repeats}"
        elif sec.target_bars:
            header += f" {sec.target_bars}"
        if sec.key:
            header += f" (key: {_ROOT_NAMES[sec.key.root % 12]})"
        lines.append(header)

        bar_tokens = []
        for bar in sec.bars:
            if bar.raw_text:
                bar_tokens.append(bar.raw_text)
            elif bar.chords:
                bar_tokens.append(" ".join(_format_chord(c) for c in bar.chords))
            else:
                bar_tokens.append("-")

        for i in range(0, len(bar_tokens), 4):
            chunk = bar_tokens[i : i + 4]
            lines.append("| " + " | ".join(chunk) + " |")

        lines.append("")
    return lines


def _format_track_properties(t: TrackArrange) -> str:
    props = []
    if t.instrument:
        props.append(f"instrument: {t.instrument}")
    if t.family:
        props.append(f"family: {t.family}")
    if t.style:
        props.append(f"style: {t.style}")
    if t.groove:
        props.append(f"groove: {t.groove}")
    if t.intensity != 0.7:
        props.append(f"intensity: {t.intensity}")
    if t.density != 0.7:
        props.append(f"density: {t.density}")
    if t.octave_shift != 0:
        props.append(f"octave_shift: {t.octave_shift}")
    if t.range:
        r0 = f"{_ROOT_NAMES[t.range[0]%12]}{(t.range[0]//12)-1}"
        r1 = f"{_ROOT_NAMES[t.range[1]%12]}{(t.range[1]//12)-1}"
        props.append(f"range: {r0}-{r1}")
    for k, v in t.params.items():
        if k not in ("instrument", "family", "style", "groove", "intensity", "density", "octave_shift", "range"):
            props.append(f"{k}: {v}")
    return ", ".join(props)


def _serialize_arrange(song: Song) -> list[str]:
    if not song.arrange:
        return []
    lines = ["arrange:"]
    for name, t in song.arrange.items():
        lines.append(f"  {name}: {{{_format_track_properties(t)}}}")
    lines.append("")
    return lines


def serialize_song(song: Song) -> str:
    """Serialize a Song IR object into clean, formatted .song text."""
    lines: list[str] = _serialize_header(song)
    lines.append("")
    lines.extend(_serialize_sections(song))
    if song.form:
        lines.append(f"form: {' '.join(song.form)}")
        lines.append("")
    lines.extend(_serialize_arrange(song))
    return "\n".join(lines).strip() + "\n"
