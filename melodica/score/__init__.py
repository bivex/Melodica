# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.score — Lead-sheet score format parser, IR, and MIDI compiler.

Allows writing and editing compositions in human-readable .song notation:
- Bar, Section, Song, TrackArrange IR
- parse_song: parses .song strings and files
- serialize_song: writes Song IR back to .song text
- song_to_midi: compiles Song IR to multitrack MIDI with section markers and feel modifiers
"""

from __future__ import annotations

from melodica.score.chord_parser import (
    parse_chord_symbol,
    parse_key_signature,
)
from melodica.score.compiler import (
    compile_song_tracks,
    song_to_midi,
)
from melodica.score.ir import (
    Bar,
    Section,
    Song,
    TrackArrange,
)
from melodica.score.parser import parse_song
from melodica.score.serializer import serialize_song

__all__ = [
    "Bar",
    "Section",
    "Song",
    "TrackArrange",
    "parse_chord_symbol",
    "parse_key_signature",
    "parse_song",
    "serialize_song",
    "compile_song_tracks",
    "song_to_midi",
]
