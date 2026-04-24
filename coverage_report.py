#!/usr/bin/env python3
"""Coverage analysis for melody generators."""
import subprocess
import sys
import os

os.chdir('/Volumes/External/Code/Melodica')

# Run pytest with coverage
result = subprocess.run([
    sys.executable, '-m', 'pytest',
    'tests/test_generators.py::TestMelodyGenerator',
    '-v',
    '--tb=short'
], capture_output=True, text=True)

print("TEST OUTPUT:")
print("=" * 70)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:1000])

print()
print("=" * 70)
print("COVERAGE GAPS IN MelodyGenerator:")
print("=" * 70)

gaps = """
❌ UNTESTED FEATURES (from reviewing test file and source):

1. RHYTHM PARAMETERS (lines 171-173, 651-701):
   - syncopation - shifts notes off-beat
   - rhythm_variety - mixes durations  
   - rhythm_motif - custom duration patterns
   - _build_motif_events() - motif-based rhythm generation

2. PHRASING & CONTOUR (lines 165-169, 263-274, 527-557):
   - phrase_length > 0 (currently always 0.0 in tests)
   - phrase_rest_probability
   - phrase_contour modes: "rise_fall", "rise", "flat" (only "arch" tested implicitly)
   - accent_pattern modes: "strong_weak", "syncopated" (only "natural")
   - _register_target() for phrase positioning

3. MOTIVIC DEVELOPMENT (lines 175-177, 382-388, 604-645):
   - motif_probability > 0
   - motif_variation modes: "invert", "retrograde", "any"
   - _apply_motif() with variations
   - Context motif memory (lines 331-332, 436-437, 456-465)

4. ORNAMENTATION (lines 179-180, 770-799):
   - ornament_probability > 0
   - _add_ornaments() - grace notes generation

5. CLIMAX & PHRASE ARCH (lines 151-152, 334-335, 368-375, 754-764):
   - climax modes: "up_3rd", "up_5th", "up_octave", "none"
   - _compute_climax()
   - Per-phrase climax calculation (lines 369-375)

6. DIRECTION & CONSTRAINTS (lines 127-128, 138, 148, 160-162):
   - steps_probability (None vs value)
   - direction_bias (other than 0.0)
   - after_leap constraints (lines 148, 394-409 logic)
   - allowed_up_intervals / allowed_down_intervals

7. MODE PARAMETER (line 120, 254):
   - mode values other than "downbeat_chord"

8. PENULTIMATE NOTES (line 154, 357, 392):
   - penultimate_step_above logic
   - _last_pitch() with constraints

9. FIRST NOTE STRATEGIES (lines 144, 239-252, 517-518):
   - first_note modes: "any_chord", "scale", "tonic", etc.
   - _first_pitch() strategies

10. VELOCITY DYNAMICS (lines 563-598):
    - _apply_velocity() - accent patterns
    - Phrase contour dynamics (lines 586-593)

11. POST-PROCESSING (lines 805-856):
    - _fill_leaps() - only called when harmony_note_probability < 1.0
    - apply_phrase_arch() (lines 449-453)

12. RENDER CONTEXT (lines 292-294, 305, 328, 456-465):
    - context parameter usage
    - _last_context storage
"""

print(gaps)

print("=" * 70)
print("CURRENT TEST COVERAGE (from test_generators.py):")
print("=" * 70)
print("""
✓ test_produces_notes - basic render() with defaults
✓ test_pitches_in_range - GeneratorParams key_range
✓ test_explicit_rhythm_pattern - custom MockRhythm
✓ test_empty_chords_returns_empty - empty chords handling
✓ test_harmony_note_probability - 1.0 (chord tones)
✓ test_harmony_note_probability_zero - 0.0 (scale tones)
✓ test_prefer_chord_tones_backward_compat - legacy alias
✓ test_note_repetition_probability_high - 0.95 repetition
✓ test_note_repetition_probability_zero - 0.0 no repetition
✓ test_note_range_override - note_range_low/high params
✓ test_note_range_melodica_defaults - F#3-E5 range
✓ test_note_range_overrides_params - priority override
""")
