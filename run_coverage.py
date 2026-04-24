#!/usr/bin/env python3
"""Run coverage analysis for melody generators."""
import coverage
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Start coverage
cov = coverage.Coverage(
    source=['melodica.generators.melody', 'melodica.generators.neural_melody', 'melodica.generators'],
    branch=True,
)
cov.start()

# Import and run tests
print("=" * 60)
print("Running MelodyGenerator tests...")
print("=" * 60)

from melodica.types import ChordLabel, Mode, NoteInfo, Quality, Scale
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.neural_melody import NeuralMelodyGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)

def _simple_chords():
    c = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    g = ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0)
    return [c, g]

# Run all test scenarios
tests_passed = 0
tests_failed = 0

def test(name, func):
    global tests_passed, tests_failed
    try:
        func()
        print(f"✓ {name}")
        tests_passed += 1
    except Exception as e:
        print(f"✗ {name}: {e}")
        tests_failed += 1

# TestMelodyGenerator scenarios
def test_produces_notes():
    gen = MelodyGenerator()
    notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
    assert len(notes) > 0
    assert all(isinstance(n, NoteInfo) for n in notes)

def test_pitches_in_range():
    params = GeneratorParams(key_range_low=48, key_range_high=72)
    gen = MelodyGenerator(params=params)
    notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
    for n in notes:
        assert 48 <= n.pitch <= 72

def test_explicit_rhythm_pattern():
    from melodica.rhythm import RhythmEvent, RhythmGenerator
    class MockRhythm(RhythmGenerator):
        def __init__(self, onsets):
            self.onsets = onsets
        def generate(self, duration_beats):
            return [RhythmEvent(onset=o, duration=0.5, velocity_factor=1.0) for o in self.onsets if o < duration_beats]

    gen = MelodyGenerator(rhythm=MockRhythm([0.0, 1.0, 2.0, 3.0]))
    notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
    assert len(notes) >= 4

def test_empty_chords():
    gen = MelodyGenerator()
    assert gen.render([], C_MAJOR, 4.0) == []

def test_harmony_note_probability():
    gen = MelodyGenerator(harmony_note_probability=1.0)
    notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
    assert len(notes) > 0
    chord_pcs = {0, 4, 7, 2, 11}
    in_chord = sum(1 for n in notes if n.pitch % 12 in chord_pcs)
    assert in_chord >= len(notes) * 0.7

def test_harmony_note_probability_zero():
    gen = MelodyGenerator(harmony_note_probability=0.0)
    notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
    assert len(notes) > 0
    for n in notes:
        assert C_MAJOR.contains(n.pitch % 12)

def test_note_repetition_probability_high():
    gen = MelodyGenerator(note_repetition_probability=0.95)
    notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
    assert len(notes) > 1
    repeated = sum(1 for i in range(1, len(notes)) if notes[i].pitch == notes[i - 1].pitch)
    assert repeated > len(notes) * 0.5

def test_note_range_override():
    gen = MelodyGenerator(note_range_low=60, note_range_high=72)
    notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
    for n in notes:
        assert 60 <= n.pitch <= 72

def test_neural_fallback():
    gen = NeuralMelodyGenerator()
    notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
    assert len(notes) > 0
    assert all(0 <= n.pitch <= 127 for n in notes)

def test_neural_note_range():
    gen = NeuralMelodyGenerator(note_range_low=60, note_range_high=72)
    notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
    for n in notes:
        assert 60 <= n.pitch <= 72

# Run tests
test("produces_notes", test_produces_notes)
test("pitches_in_range", test_pitches_in_range)
test("explicit_rhythm_pattern", test_explicit_rhythm_pattern)
test("empty_chords", test_empty_chords)
test("harmony_note_probability", test_harmony_note_probability)
test("harmony_note_probability_zero", test_harmony_note_probability_zero)
test("note_repetition_probability_high", test_note_repetition_probability_high)
test("note_range_override", test_note_range_override)
test("neural_fallback", test_neural_fallback)
test("neural_note_range", test_neural_note_range)

# Stop coverage
cov.stop()

print()
print("=" * 60)
print(f"Tests: {tests_passed} passed, {tests_failed} failed")
print("=" * 60)

# Report coverage
print()
print("COVERAGE REPORT:")
print("=" * 60)
cov.report(show_missing=True)

# Save HTML report
cov.html_report(directory='coverage_html')
print()
print(f"HTML report saved to: coverage_html/index.html")

sys.exit(0 if tests_failed == 0 else 1)
