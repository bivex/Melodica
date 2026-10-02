# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.score.parser — Parser for .song human-readable lead-sheet notation.

Converts .song files (metadata, sections, chord bars, arrangement configs)
into a validated Song IR.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from melodica.generate.profile import parse_pitch
from melodica.score.chord_parser import parse_chord_symbol, parse_key_signature
from melodica.score.ir import Bar, Section, Song, TrackArrange
from melodica.types import ChordLabel, Mode, Scale

_SECTION_HEADER_REGEX = re.compile(
    r"^\[([^\]]+)\](?:\s*(?:x(\d+)|(\d+)))?(?:\s*\((.*)\))?$"
)


def _parse_inline_dict(s: str) -> dict[str, Any]:
    """Parse inline YAML/JSON style dictionary: '{key: val, key2: val2}'."""
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1].strip()
    result: dict[str, Any] = {}
    if not s:
        return result
    for pair in s.split(","):
        if ":" in pair:
            k, v = pair.split(":", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if v.isdigit():
                result[k] = int(v)
            else:
                try:
                    result[k] = float(v)
                except ValueError:
                    if v.lower() == "true":
                        result[k] = True
                    elif v.lower() == "false":
                        result[k] = False
                    else:
                        result[k] = v
    return result


def _parse_section_header(line: str) -> Section | None:
    header_match = _SECTION_HEADER_REGEX.match(line)
    if not header_match:
        return None
    sec_name = header_match.group(1).strip()
    repeat_str = header_match.group(2)
    target_str = header_match.group(3)
    opts_str = header_match.group(4)

    repeats = int(repeat_str) if repeat_str else 1
    target_bars = int(target_str) if target_str else None

    sec_key = None
    sec_overrides: dict[str, Any] = {}
    if opts_str:
        for opt in opts_str.split(";"):
            if ":" in opt:
                k, v = opt.split(":", 1)
                k, v = k.strip().lower(), v.strip()
                if k == "key":
                    sec_key = parse_key_signature(v)
                else:
                    sec_overrides[k] = v

    return Section(
        name=sec_name,
        bars=[],
        repeats=repeats,
        target_bars=target_bars,
        key=sec_key,
        arrange_overrides=sec_overrides,
    )


def _parse_track_arrange_line(line: str) -> tuple[str, TrackArrange]:
    track_name, config_part = line.split(":", 1)
    track_name = track_name.strip()
    cfg = _parse_inline_dict(config_part)

    parsed_range = None
    raw_range = cfg.get("range")
    if isinstance(raw_range, str) and "-" in raw_range:
        r_low, r_high = raw_range.split("-", 1)
        try:
            parsed_range = (parse_pitch(r_low.strip()), parse_pitch(r_high.strip()))
        except ValueError:
            pass

    track = TrackArrange(
        name=track_name,
        instrument=cfg.get("instrument"),
        family=cfg.get("family"),
        style=cfg.get("style"),
        groove=cfg.get("groove"),
        intensity=float(cfg.get("intensity", 0.7)),
        density=float(cfg.get("density", 0.7)),
        octave_shift=int(cfg.get("octave_shift", 0)),
        range=parsed_range,
        articulation=cfg.get("articulation"),
        algorithm=cfg.get("algorithm"),
        params=cfg,
    )
    return track_name, track


def _parse_bars_from_line(
    line: str,
    time_sig: tuple[int, int],
    ref_key: Scale,
    current_section: Section,
) -> None:
    beats_per_bar = time_sig[0] * (4.0 / time_sig[1])
    bar_tokens = [t.strip() for t in line.split("|") if t.strip() != ""]
    sec_ref_key = current_section.key or ref_key

    for token in bar_tokens:
        chord_symbols = token.split()
        bar_chords: list[ChordLabel] = []
        if chord_symbols and chord_symbols != ["-"]:
            sub_dur = beats_per_bar / len(chord_symbols)
            for i, sym in enumerate(chord_symbols):
                ch = parse_chord_symbol(
                    sym,
                    scale=sec_ref_key,
                    start=round(i * sub_dur, 6),
                    duration=round(sub_dur, 6),
                )
                if ch:
                    bar_chords.append(ch)

        bar = Bar(
            index=len(current_section.bars),
            chords=bar_chords,
            beats=beats_per_bar,
            raw_text=token,
        )
        current_section.bars.append(bar)


def _load_source_text(source: str | Path) -> str:
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    s = str(source)
    if "\n" not in s and s.endswith(".song") and Path(s).is_file():
        return Path(s).read_text(encoding="utf-8")
    return s


def parse_song(source: str | Path) -> Song:
    """
    Parse a .song string or file path into a Song IR.
    """
    text = _load_source_text(source)
    lines = text.splitlines()

    title = "Untitled"
    key = Scale(root=0, mode=Mode.MAJOR)
    tempo = 120.0
    time_sig = (4, 4)
    feel = "straight"
    seed: int | None = None
    form: list[str] = []
    sections: dict[str, Section] = {}
    arrange: dict[str, TrackArrange] = {}
    metadata: dict[str, Any] = {}

    current_section: Section | None = None
    in_arrange = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        sec = _parse_section_header(line)
        if sec is not None:
            in_arrange = False
            current_section = sec
            sections[sec.name] = sec
            continue

        if line.startswith("arrange:"):
            in_arrange = True
            current_section = None
            continue

        if in_arrange and ":" in line and not line.startswith("|") and not line.startswith("["):
            t_name, t_track = _parse_track_arrange_line(line)
            arrange[t_name] = t_track
            continue

        if line.startswith("|") and current_section is not None:
            _parse_bars_from_line(line, time_sig, key, current_section)
            continue

        if ":" in line:
            in_arrange = False
            k, v = line.split(":", 1)
            k, v = k.strip().lower(), v.strip()
            if k == "title":
                title = v
            elif k == "key":
                key = parse_key_signature(v)
            elif k == "tempo":
                tempo = float(v)
            elif k == "time":
                p = v.split("/")
                time_sig = (int(p[0]), int(p[1]))
            elif k == "feel":
                feel = v
            elif k == "seed":
                seed = int(v)
            elif k == "form":
                form = [s.strip() for s in v.replace(",", " ").split() if s.strip()]
            else:
                metadata[k] = v

    if not form:
        form = list(sections.keys())

    return Song(
        title=title,
        key=key,
        tempo=tempo,
        time_signature=time_sig,
        feel=feel,
        seed=seed,
        sections=sections,
        form=form,
        arrange=arrange,
        metadata=metadata,
    )


# Alias
parse_song_file = parse_song
