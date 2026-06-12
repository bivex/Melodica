import pytest
from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer, HMMConfig
from melodica.types import NoteInfo, Scale, Mode, BarGrid

def test_c_major_melody_snapshot():
    """Verify that a standard diatonic C Major melody generates the golden reference progression."""
    grid = BarGrid(numerator=4, denominator=4)
    note_names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    
    # Pure diatonic C Major melody (same as Melody B in diagnose_coupling.py)
    melody = [
        NoteInfo(pitch=60, start=0.0, duration=2.0),
        NoteInfo(pitch=64, start=2.0, duration=2.0),
        NoteInfo(pitch=65, start=4.0, duration=2.0),
        NoteInfo(pitch=69, start=6.0, duration=2.0),
        NoteInfo(pitch=67, start=8.0, duration=2.0),
        NoteInfo(pitch=71, start=10.0, duration=2.0),
        NoteInfo(pitch=72, start=12.0, duration=2.0),
        NoteInfo(pitch=64, start=14.0, duration=2.0),
    ]

    # Harmonize with standard configuration and biases
    config = HMMConfig(key_coupling_weight=3.0, tonic_end_bias=2.5, dominant_penultimate_bias=1.5)
    h = CoupledHMMHarmonizer(bar_grid=grid, chord_change="bars", config=config)
    
    chords = h.harmonize(
        melody, Scale(root=0, mode=Mode.MAJOR), 16.0, force_key=Scale(root=0, mode=Mode.MAJOR)
    )
    
    result = [f"{note_names[c.root]} {c.quality.name}" for c in chords]

    # Golden reference progression.
    # Updated 2026-06: default emission_weight raised 1.0 -> 20.0 to fix a
    # scale-imbalance bug where normalized emissions (~[-1,0]) were drowned out
    # by structural biases (2-4), causing chords to ignore the melody. Each
    # chord now contains both notes of its bar window:
    #   [C E]->Cmaj7  [F A]->Fadd9  [G B]->Cmaj7  [C E]->Cmaj7
    # (Previously bar2 gave C SUS4 — missing the A — and bar3 gave G7.)
    expected = ['C MAJOR7', 'F ADD9', 'C MAJOR7', 'C MAJOR7']

    assert result == expected, f"Progression changed! Got {result}, expected {expected}"
