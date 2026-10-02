# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

from pathlib import Path
import pytest
import mido

from melodica.score import (
    Song,
    Section,
    Bar,
    TrackArrange,
    parse_chord_symbol,
    parse_key_signature,
    parse_song,
    serialize_song,
    song_to_midi,
)
from melodica.types import Mode, Scale
from melodica.theory.chords import Quality


def test_chord_parser_standard():
    c_maj = parse_key_signature("C")
    
    # Major triad & 7th
    c1 = parse_chord_symbol("C", c_maj)
    assert c1.root == 0 and c1.quality == Quality.MAJOR

    c2 = parse_chord_symbol("Fmaj7", c_maj)
    assert c2.root == 5 and c2.quality == Quality.MAJOR7

    # Minor triad & 7th
    c3 = parse_chord_symbol("Am7", c_maj)
    assert c3.root == 9 and c3.quality == Quality.MINOR7

    # Dominant & suspended
    c4 = parse_chord_symbol("G7", c_maj)
    assert c4.root == 7 and c4.quality == Quality.DOMINANT7

    c5 = parse_chord_symbol("E7sus4", c_maj)
    assert c5.root == 4 and c5.quality == Quality.SUS4

    # Slash chord
    c6 = parse_chord_symbol("C/E", c_maj)
    assert c6.root == 0 and c6.bass == 4

    # Rests
    assert parse_chord_symbol("-", c_maj) is None
    assert parse_chord_symbol("|", c_maj) is None


def test_chord_parser_roman_numerals():
    am = parse_key_signature("Am")
    c1 = parse_chord_symbol("i", am)
    assert c1.root == 9 and c1.quality == Quality.MINOR

    c2 = parse_chord_symbol("iv7", am)
    assert c2.root == 2 and c2.quality == Quality.MINOR7

    c3 = parse_chord_symbol("V7", am)
    assert c3.root == 4 and c3.quality == Quality.DOMINANT7


def test_key_signature_parser():
    s1 = parse_key_signature("Am")
    assert s1.root == 9 and s1.mode == Mode.NATURAL_MINOR

    s2 = parse_key_signature("C major")
    assert s2.root == 0 and s2.mode == Mode.MAJOR

    s3 = parse_key_signature("D dorian")
    assert s3.root == 2 and s3.mode == Mode.DORIAN

    s4 = parse_key_signature("F#m")
    assert s4.root == 6 and s4.mode == Mode.NATURAL_MINOR


def test_parse_song_full_structure():
    song_text = """
title: Test Track
key: Dm
tempo: 105
time: 4/4
feel: swing8
seed: 12345

[Intro] x2
| Dm7 | Gm7 | Bbmaj7 | A7 |

[Chorus] 8
| Dm | F | C | G |

form: Intro Chorus Intro

arrange:
  drums: {groove: rock, intensity: 0.8}
  bass: {style: walking}
  keys: {instrument: vibraphone}
"""
    song = parse_song(song_text)
    assert song.title == "Test Track"
    assert song.key.root == 2
    assert song.tempo == 105.0
    assert song.time_signature == (4, 4)
    assert song.feel == "swing8"
    assert song.seed == 12345
    assert song.form == ["Intro", "Chorus", "Intro"]

    # Section unrolling:
    # Intro: 4 bars * 2 repeats = 8 bars
    assert song.sections["Intro"].bar_count() == 8
    # Chorus: 4 bars padded to target 8 bars = 8 bars
    assert song.sections["Chorus"].bar_count() == 8
    # Total bars = 8 + 8 + 8 = 24 bars
    assert song.total_bars() == 24
    assert song.total_beats() == 24 * 4.0

    # Arrange tracks
    assert "drums" in song.arrange
    assert "bass" in song.arrange
    assert "keys" in song.arrange
    assert song.arrange["keys"].instrument == "vibraphone"


def test_song_roundtrip_serialization():
    song_text = """title: Night Drive
key: Am
tempo: 92
time: 4/4
feel: swing8
seed: 42

[Intro] x2
| Am7 | Fmaj7 | Dm7 | E7sus4 E7 |

[Verse] 8
| Am7 | Am7 | Fmaj7 | Fmaj7 |
| Dm7 | G7 | Cmaj7 | E7 |

[Chorus]
| Fmaj7 | G | Am | Am |

form: Intro Verse Chorus

arrange:
  drums: {groove: rock, intensity: 0.6}
  bass: {style: walking}
  pad: {instrument: ambient_pad}
  lead: {style: lyrical, range: C4-A5}
"""
    song1 = parse_song(song_text)
    serialized = serialize_song(song1)
    song2 = parse_song(serialized)

    assert song1.title == song2.title
    assert song1.key.root == song2.key.root
    assert song1.tempo == song2.tempo
    assert song1.form == song2.form
    assert song1.total_bars() == song2.total_bars()
    assert list(song1.arrange.keys()) == list(song2.arrange.keys())


def test_song_to_midi_export(tmp_path: Path):
    song_text = """title: Mini Score
key: C
tempo: 120
time: 4/4
seed: 99

[Main]
| C | F | G | C |

form: Main

arrange:
  bass: {style: walking}
  keys: {instrument: celesta}
"""
    song = parse_song(song_text)
    out_midi = tmp_path / "test_mini.mid"
    mid = song_to_midi(song, output_path=out_midi)

    assert out_midi.is_file()
    assert len(mid.tracks) >= 3  # Global + bass + keys

    # Verify global track has markers and tempo
    global_track = mid.tracks[0]
    track_names = [tr.name for tr in mid.tracks]
    assert "Global" in track_names
    assert "bass" in track_names
    assert "keys" in track_names

    # Check marker presence
    marker_messages = [msg for msg in global_track if msg.type == "marker"]
    assert len(marker_messages) >= 1
    assert marker_messages[0].text == "Main"
