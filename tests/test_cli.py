# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
tests/test_cli.py — Unit tests for melodica CLI commands.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from melodica.cli import main


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "Melodica — Algorithmic Music Composition" in captured.out


def test_cli_no_args_prints_help(capsys):
    res = main([])
    assert res == 0
    captured = capsys.readouterr()
    assert "Melodica — Algorithmic Music Composition" in captured.out


def test_cli_list_instruments(capsys):
    res = main(["list-instruments"])
    assert res == 0
    captured = capsys.readouterr()
    assert "Available Melodica Instruments" in captured.out
    assert "celesta" in captured.out
    assert "grand_piano" in captured.out
    assert "muted_trumpet" in captured.out


def test_cli_list_instruments_filter(capsys):
    res = main(["list-instruments", "-f", "mallet"])
    assert res == 0
    captured = capsys.readouterr()
    assert "Filtered by family 'mallet'" in captured.out
    assert "celesta" in captured.out
    assert "grand_piano" not in captured.out


def test_cli_check_song(capsys):
    song_file = Path("songs/night_drive.song")
    res = main(["check", str(song_file)])
    assert res == 0
    captured = capsys.readouterr()
    assert "Valid score: Night Drive" in captured.out
    assert "Total bars: 32" in captured.out


def test_cli_check_nonexistent(capsys):
    res = main(["check", "nonexistent.song"])
    assert res == 1


def test_cli_build_and_inspect(tmp_path, capsys):
    song_file = Path("songs/night_drive.song")
    out_midi = tmp_path / "cli_test_out.mid"

    res = main(["build", str(song_file), "-o", str(out_midi)])
    assert res == 0
    assert out_midi.is_file()
    assert out_midi.stat().st_size > 0

    res_inspect = main(["inspect", str(out_midi)])
    assert res_inspect == 0
    captured = capsys.readouterr()
    assert "MIDI Inspection: cli_test_out.mid" in captured.out
    assert "Type: 1" in captured.out
