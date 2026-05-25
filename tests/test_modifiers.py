# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import pytest
from melodica.types import NoteInfo, ChordLabel, Quality, Scale, Mode, MusicTimeline, KeyLabel
from melodica.modifiers import ModifierContext
from melodica.modifiers.rhythmic import (
    QuantizeModifier,
    HumanizeModifier,
    SwingController,
    AdjustNoteLengthsModifier,
    FollowRhythmModifier,
)
from melodica.types import NoteInfo, ChordLabel, Quality, Scale, Mode, MusicTimeline, KeyLabel
from melodica.modifiers import ModifierContext
from melodica.modifiers.rhythmic import (
    QuantizeModifier,
    HumanizeModifier,
    SwingController,
    AdjustNoteLengthsModifier,
)
from melodica.modifiers.harmonic import (
    NoteDoublerModifier,
    TransposeModifier,
    LimitNoteRangeModifier,
)
from melodica.modifiers.dynamic import VelocityScalingModifier, CrescendoModifier


@pytest.fixture
def dummy_context():
    key = Scale(root=0, mode=Mode.MAJOR)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=4)]
    timeline = MusicTimeline(chords=chords, keys=[KeyLabel(scale=key, start=0, duration=4)])
    return ModifierContext(duration_beats=4.0, chords=chords, timeline=timeline, scale=key)


def test_quantize_modifier(dummy_context):
    notes = [
        NoteInfo(pitch=60, start=0.12, duration=0.22),
        NoteInfo(pitch=62, start=0.6, duration=0.6),
    ]
    mod = QuantizeModifier(grid_resolution=0.25, quantize_durations=True)
    out = mod.modify(notes, dummy_context)

    # 0.12 rounds to 0.0, 0.22 rounds to 0.25
    assert out[0].start == 0.0
    assert out[0].duration == 0.25

    # 0.6 rounds to 0.5, 0.6 rounds to 0.5
    assert out[1].start == 0.5
    assert out[1].duration == 0.5


def test_humanize_modifier(dummy_context):
    notes = [NoteInfo(pitch=60, start=1.0, duration=1.0, velocity=100)]
    mod = HumanizeModifier(timing_std=0.05, velocity_std=10.0)
    out = mod.modify(notes, dummy_context)

    assert len(out) == 1
    # Random, but likely changed
    assert out[0].pitch == 60


def test_swing_controller(dummy_context):
    # Straight 8ths: 0.0, 0.5, 1.0, 1.5
    notes = [
        NoteInfo(60, 0.0, 0.5),
        NoteInfo(62, 0.5, 0.5),
        NoteInfo(64, 1.0, 0.5),
        NoteInfo(65, 1.5, 0.5),
    ]
    mod = SwingController(swing_ratio=0.66, grid=1.0)
    out = mod.modify(notes, dummy_context)

    # Onbeats unchanged
    assert out[0].start == 0.0
    assert out[2].start == 1.0

    # Offbeats delayed: ratio=0.66 -> delay is (0.66-0.5)*2 * 0.25 = 0.32*0.25 = 0.08
    # Exact: delay = 0.16 * 2 * 0.25 = 0.08
    # Wait, swing_ratio 0.66 means downbeat takes ~66% of the grid, upbeat takes ~33%.
    # If beat is 0.5, 0.5 * 0.66 = 0.33. Offbeat moves from 0.25 to 0.33?
    # Ah, grid=0.5 means the division is 0.5. So 0.5/2 = 0.25.
    # delay = (0.66 - 0.5)*2 * 0.25 = 0.32 * 0.25 = 0.08
    assert out[1].start > 0.5
    assert out[3].start > 1.5


def test_adjust_lengths_modifier(dummy_context):
    notes = [NoteInfo(60, 0.0, 1.0)]
    mod = AdjustNoteLengthsModifier(gate_factor=0.5)
    out = mod.modify(notes, dummy_context)
    assert out[0].duration == 0.5

    mod2 = AdjustNoteLengthsModifier(set_fixed=0.1)
    out2 = mod2.modify(notes, dummy_context)
    assert out2[0].duration == 0.1


def test_note_doubler(dummy_context):
    notes = [NoteInfo(60, 0.0, 1.0, 100)]
    mod = NoteDoublerModifier(octaves=[-1, 1])
    out = mod.modify(notes, dummy_context)

    # Original + 2 octave shifts
    assert len(out) == 3
    pitches = sorted([n.pitch for n in out])
    assert pitches == [48, 60, 72]

    # Original velocity = 100, shifts scaled by 0.8 = 80
    vels = [n.velocity for n in out]
    assert 100 in vels
    assert 80 in vels


def test_transpose_modifier(dummy_context):
    notes = [NoteInfo(60, 0.0, 1.0)]
    mod = TransposeModifier(semitones=7)
    out = mod.modify(notes, dummy_context)
    assert out[0].pitch == 67


def test_limit_range_modifier(dummy_context):
    notes = [
        NoteInfo(36, 0.0, 1.0),  # Too low
        NoteInfo(96, 1.0, 1.0),  # Too high
        NoteInfo(60, 2.0, 1.0),  # Just right
    ]
    mod = LimitNoteRangeModifier(low=48, high=72)
    out = mod.modify(notes, dummy_context)

    assert out[0].pitch == 48  # 36 + 12
    assert out[1].pitch == 72  # 96 - 24
    assert out[2].pitch == 60


def test_velocity_scaling(dummy_context):
    notes = [NoteInfo(60, 0.0, 1.0, velocity=80)]
    mod = VelocityScalingModifier(scale=0.5, add_val=10)
    out = mod.modify(notes, dummy_context)
    assert out[0].velocity == 50  # 80/2 + 10


def test_crescendo_modifier(dummy_context):
    notes = [NoteInfo(60, 0.0, 1.0), NoteInfo(62, 2.0, 1.0), NoteInfo(64, 4.0, 1.0)]
    # Context duration is 4.0
    mod = CrescendoModifier(start_vel=40, end_vel=100)
    out = mod.modify(notes, dummy_context)

    # Wait, note ending at 4.0 + 1.0 = 5.0.
    # The total total_len calculated in modifier is max(context.duration_beats, highest_end, 0.1)
    # highest_end = 5.0
    # at start 0.0 -> progress 0.0 -> vel 40
    # at start 2.0 -> progress 0.4 -> 40 + (60 * 0.4) = 64
    # at start 4.0 -> progress 0.8 -> 40 + (60 * 0.8) = 88

    assert out[0].velocity == 40
    assert out[1].velocity == 64
    assert out[2].velocity == 88


# ---------------------------------------------------------------------------
# 17 new variation modifiers
# ---------------------------------------------------------------------------

from melodica.modifiers.rc_variations import (
    AddChordNotesModifier,
    AddIntervalModifier,
    DelayNotesModifier,
    DoublePhraseModifier,
    TriplePhraseModifier,
    ExtractRhythmModifier,
    JoinNotesModifier,
    RemoveShortNotesModifier,
    RotateNotesModifier,
    SimplifyPhraseModifier,
    SpreadOutChordNotesModifier,
    SwapChordNotesModifier,
    VelocityGeneratorModifier,
    PermuteChordNotesModifier,
    AudioGainModifier,
    RemoveDuplicatesModifier,
    FillGapsModifier,
)
from melodica.modifiers.variations import MirrorModifier, StaccatoLegatoModifier, MIDIEchoModifier


def _make_notes():
    return [
        NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),
        NoteInfo(pitch=64, start=0.5, duration=0.5, velocity=80),
        NoteInfo(pitch=67, start=1.0, duration=0.5, velocity=80),
        NoteInfo(pitch=72, start=1.5, duration=0.5, velocity=80),
    ]


def test_add_chord_notes(dummy_context):
    mod = AddChordNotesModifier(count=1)
    result = mod.modify(_make_notes(), dummy_context)
    assert len(result) >= 4


def test_add_interval_above(dummy_context):
    mod = AddIntervalModifier(semitones=7, direction="above")
    result = mod.modify(_make_notes(), dummy_context)
    assert len(result) == 8
    assert result[4].pitch == 67  # 60 + 7


def test_add_interval_below(dummy_context):
    mod = AddIntervalModifier(semitones=12, direction="below")
    result = mod.modify(_make_notes(), dummy_context)
    assert result[4].pitch == 48  # 60 - 12


def test_delay_notes(dummy_context):
    mod = DelayNotesModifier(delay_beats=1.0)
    result = mod.modify(_make_notes(), dummy_context)
    assert result[0].start == 1.0
    assert result[1].start == 1.5


def test_double_phrase(dummy_context):
    mod = DoublePhraseModifier()
    result = mod.modify(
        _make_notes(), ModifierContext(duration_beats=4.0, chords=[], timeline=None, scale=None)
    )
    assert len(result) == 8
    assert result[4].start == 4.0


def test_triple_phrase(dummy_context):
    mod = TriplePhraseModifier()
    result = mod.modify(
        _make_notes(), ModifierContext(duration_beats=4.0, chords=[], timeline=None, scale=None)
    )
    assert len(result) == 12


def test_extract_rhythm(dummy_context):
    mod = ExtractRhythmModifier(target_pitch=36)
    result = mod.modify(_make_notes(), dummy_context)
    assert all(n.pitch == 36 for n in result)
    assert len(result) == 4


def test_join_notes(dummy_context):
    notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),
        NoteInfo(pitch=60, start=0.55, duration=0.5, velocity=80),
        NoteInfo(pitch=64, start=1.5, duration=0.5, velocity=80),
    ]
    mod = JoinNotesModifier(max_gap=0.1)
    result = mod.modify(notes, dummy_context)
    assert len(result) == 2
    assert result[0].duration > 0.5


def test_remove_short_notes(dummy_context):
    notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.05, velocity=80),
        NoteInfo(pitch=64, start=0.5, duration=0.5, velocity=80),
    ]
    mod = RemoveShortNotesModifier(min_duration=0.1)
    result = mod.modify(notes, dummy_context)
    assert len(result) == 1
    assert result[0].pitch == 64


def test_rotate_notes(dummy_context):
    mod = RotateNotesModifier(beats=0.5)
    ctx = ModifierContext(duration_beats=4.0, chords=[], timeline=None, scale=None)
    result = mod.modify(_make_notes(), ctx)
    assert len(result) == 4
    assert result[0].start == 0.5


def test_simplify_phrase(dummy_context):
    mod = SimplifyPhraseModifier(keep_every=2)
    result = mod.modify(_make_notes(), dummy_context)
    assert len(result) == 2


def test_spread_out_chord_notes(dummy_context):
    mod = SpreadOutChordNotesModifier(spread_semitones=12)
    result = mod.modify(_make_notes(), dummy_context)
    assert len(result) >= 4


def test_swap_chord_notes(dummy_context):
    mod = SwapChordNotesModifier()
    result = mod.modify(_make_notes(), dummy_context)
    assert result[0].pitch == 64  # swapped with index 1
    assert result[1].pitch == 60


@pytest.mark.parametrize("pattern", ["crescendo", "decrescendo", "accent_beats", "random"])
def test_velocity_generator(dummy_context, pattern):
    mod = VelocityGeneratorModifier(pattern=pattern)
    result = mod.modify(_make_notes(), dummy_context)
    assert len(result) == 4
    for n in result:
        assert 1 <= n.velocity <= 127


def test_velocity_generator_crescendo(dummy_context):
    mod = VelocityGeneratorModifier(pattern="crescendo")
    result = mod.modify(_make_notes(), dummy_context)
    assert result[0].velocity < result[-1].velocity


def test_permute_chord_notes(dummy_context):
    mod = PermuteChordNotesModifier()
    result = mod.modify(_make_notes(), dummy_context)
    assert len(result) == 4


def test_audio_gain_boost(dummy_context):
    mod = AudioGainModifier(gain=1.5)
    result = mod.modify(_make_notes(), dummy_context)
    assert result[0].velocity == 120  # 80 * 1.5


def test_audio_gain_reduce(dummy_context):
    mod = AudioGainModifier(gain=0.5)
    result = mod.modify(_make_notes(), dummy_context)
    assert result[0].velocity == 40  # 80 * 0.5


def test_audio_gain_clamp(dummy_context):
    mod = AudioGainModifier(gain=2.0)
    notes = [NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=100)]
    result = mod.modify(notes, dummy_context)
    assert result[0].velocity == 127


def test_remove_duplicates(dummy_context):
    notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),
        NoteInfo(pitch=60, start=0.5, duration=0.5, velocity=80),
        NoteInfo(pitch=64, start=1.0, duration=0.5, velocity=80),
    ]
    mod = RemoveDuplicatesModifier()
    result = mod.modify(notes, dummy_context)
    assert len(result) == 2
    assert result[0].pitch == 60
    assert result[1].pitch == 64


def test_fill_gaps(dummy_context):
    notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),
        NoteInfo(pitch=67, start=1.0, duration=0.5, velocity=80),
    ]
    mod = FillGapsModifier(max_gap=1.0)
    result = mod.modify(notes, dummy_context)
    assert len(result) == 3
    assert result[1].pitch == 63  # midpoint


def test_mirror_horizontal(dummy_context):
    mod = MirrorModifier(axis="horizontal")
    ctx = ModifierContext(duration_beats=2.0, chords=[], timeline=None, scale=None)
    result = mod.modify(_make_notes(), ctx)
    assert len(result) == 4


def test_mirror_vertical(dummy_context):
    mod = MirrorModifier(axis="vertical", center_midi=66)
    result = mod.modify(_make_notes(), dummy_context)
    assert result[0].pitch == 72  # 66 - (60-66) = 72


def test_staccato_legato(dummy_context):
    mod = StaccatoLegatoModifier(amount=0.3)
    result = mod.modify(_make_notes(), dummy_context)
    assert result[0].duration < 0.5


def test_midi_echo(dummy_context):
    mod = MIDIEchoModifier(delay_beats=0.5, repetitions=2, decay=0.7)
    ctx = ModifierContext(duration_beats=4.0, chords=[], timeline=None, scale=None)
    result = mod.modify(_make_notes(), ctx)
    assert len(result) > 4  # originals + echoes


# ---------------------------------------------------------------------------
# FollowRhythmModifier tests
# ---------------------------------------------------------------------------


def test_follow_rhythm_basic(dummy_context):
    """Basic: follower notes get source onsets and inter-onset durations."""
    source_notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.3),
        NoteInfo(pitch=64, start=0.5, duration=0.3),
        NoteInfo(pitch=67, start=1.0, duration=0.3),
    ]
    follower_notes = [
        NoteInfo(pitch=48, start=0.0, duration=1.0),
        NoteInfo(pitch=52, start=0.5, duration=1.0),
        NoteInfo(pitch=55, start=1.0, duration=1.0),
    ]
    ctx = ModifierContext(
        duration_beats=4.0, chords=[], timeline=None, scale=None, tracks={"Melody": source_notes}
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    assert len(result) == 3
    # Onsets match source
    assert result[0].start == 0.0
    assert result[1].start == 0.5
    assert result[2].start == 1.0
    # Durations are gaps to next onset (0.5, 0.5)
    # Last onset duration extends to timeline end
    assert result[0].duration == 0.5
    assert result[1].duration == 0.5


def test_follow_rhythm_polyphonic_no_duplicates(dummy_context):
    """Polyphonic source onset should produce only ONE output note, not duplicates."""
    source_notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.3),
        NoteInfo(pitch=64, start=0.0, duration=0.5),  # Same onset, different pitch/dur
        NoteInfo(pitch=67, start=0.5, duration=0.3),
    ]
    follower_notes = [
        NoteInfo(pitch=48, start=0.1, duration=1.0),
        NoteInfo(pitch=52, start=0.6, duration=1.0),
    ]
    ctx = ModifierContext(
        duration_beats=4.0, chords=[], timeline=None, scale=None, tracks={"Melody": source_notes}
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    # Should be exactly 2 notes (one per unique onset time), not 3
    assert len(result) == 2
    # All notes have unique start times
    starts = [n.start for n in result]
    assert len(set(starts)) == 2


def test_follow_rhythm_articulation_expression_preserved(dummy_context):
    """Articulation and expression should be copied from source note."""
    source_notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.3),
        NoteInfo(pitch=64, start=0.5, duration=0.3),
    ]
    follower_notes = [
        NoteInfo(
            pitch=48, start=0.0, duration=1.0, articulation="staccato", expression={1: 64, 7: 100}
        ),
        NoteInfo(pitch=52, start=0.5, duration=1.0, articulation="sustain", expression={1: 100}),
    ]
    ctx = ModifierContext(
        duration_beats=4.0, chords=[], timeline=None, scale=None, tracks={"Melody": source_notes}
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    # Both notes should have articulation and expression copied
    assert result[0].articulation == "staccato"
    assert result[0].expression == {1: 64, 7: 100}
    assert result[1].articulation == "sustain"
    assert result[1].expression == {1: 100}


def test_follow_rhythm_duration_is_inter_onset_gap(dummy_context):
    """Duration should be gap to next onset, NOT max(original duration)."""
    source_notes = [
        NoteInfo(pitch=60, start=0.0, duration=2.0),  # Long note but gap matters
        NoteInfo(pitch=64, start=0.5, duration=0.1),  # Short note
    ]
    follower_notes = [
        NoteInfo(pitch=48, start=0.25, duration=1.0),
    ]
    ctx = ModifierContext(
        duration_beats=4.0, chords=[], timeline=None, scale=None, tracks={"Melody": source_notes}
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    # First onset (0.0) duration should be gap to next onset (0.5)
    assert result[0].start == 0.0
    assert result[0].duration == 0.5  # NOT 2.0 from original
    # Second onset (0.5): timeline_end = max(src_end=0.6, duration_beats=4.0) = 4.0
    # duration = 4.0 - 0.5 = 3.5
    assert result[1].duration == 3.5


def test_follow_rhythm_empty_source_returns_original(dummy_context):
    """Empty source track should return original notes unchanged."""
    follower_notes = [
        NoteInfo(pitch=60, start=0.0, duration=1.0),
    ]
    ctx = ModifierContext(
        duration_beats=4.0, chords=[], timeline=None, scale=None, tracks={"Melody": []}
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    assert len(result) == 1
    assert result[0].start == 0.0
    assert result[0].duration == 1.0


def test_follow_rhythm_missing_source_track_returns_original(dummy_context):
    """Missing source track should return original notes unchanged."""
    follower_notes = [
        NoteInfo(pitch=60, start=0.0, duration=1.0),
    ]
    ctx = ModifierContext(
        duration_beats=4.0,
        chords=[],
        timeline=None,
        scale=None,
        tracks={},  # No Melody track
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    assert len(result) == 1
    assert result[0].start == 0.0
    assert result[0].duration == 1.0


def test_follow_rhythm_closest_note_selected(dummy_context):
    """The note whose start is closest to onset should be selected for pitch."""
    source_notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.5),
    ]
    follower_notes = [
        NoteInfo(pitch=48, start=0.01, duration=1.0),  # Closer to 0.0
        NoteInfo(pitch=52, start=0.5, duration=1.0),  # Further from 0.0
    ]
    ctx = ModifierContext(
        duration_beats=4.0, chords=[], timeline=None, scale=None, tracks={"Melody": source_notes}
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    assert result[0].pitch == 48  # Closer note selected


def test_follow_rhythm_minimum_duration(dummy_context):
    """Durations should be clamped to minimum of 0.05 beats."""
    source_notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.1),
        NoteInfo(pitch=64, start=0.01, duration=0.1),  # Very short gap
    ]
    follower_notes = [
        NoteInfo(pitch=48, start=0.005, duration=1.0),
    ]
    ctx = ModifierContext(
        duration_beats=4.0, chords=[], timeline=None, scale=None, tracks={"Melody": source_notes}
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    # Gap is 0.01, but should be clamped to 0.05
    assert result[0].duration >= 0.05


def test_follow_rhythm_preserves_velocity_and_absolute(dummy_context):
    """Velocity and absolute flag should be copied from selected follower note."""
    source_notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.5),
    ]
    follower_notes = [
        NoteInfo(pitch=48, start=0.0, duration=1.0, velocity=100, absolute=True),
    ]
    ctx = ModifierContext(
        duration_beats=4.0, chords=[], timeline=None, scale=None, tracks={"Melody": source_notes}
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    assert result[0].velocity == 100
    assert result[0].absolute == True


def test_follow_rhythm_sparse_source_long_gaps(dummy_context):
    """Sparse source with large gaps should produce long durations."""
    source_notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.5),
        NoteInfo(pitch=64, start=4.0, duration=0.5),  # Large gap
    ]
    follower_notes = [
        NoteInfo(pitch=48, start=2.0, duration=1.0),  # Midpoint
    ]
    ctx = ModifierContext(
        duration_beats=8.0, chords=[], timeline=None, scale=None, tracks={"Melody": source_notes}
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    assert len(result) == 2
    # First note duration should be 4.0 (gap to next onset)
    assert result[0].duration == 4.0
    # Second note: timeline_end = max(src_end=4.5, duration_beats=8.0) = 8.0
    # duration = 8.0 - 4.0 = 4.0
    assert result[1].duration == 4.0


def test_follow_rhythm_single_source_note(dummy_context):
    """Single source note should produce one output with appropriate duration."""
    source_notes = [
        NoteInfo(pitch=60, start=1.0, duration=0.5),
    ]
    follower_notes = [
        NoteInfo(pitch=48, start=0.5, duration=2.0),
    ]
    ctx = ModifierContext(
        duration_beats=4.0, chords=[], timeline=None, scale=None, tracks={"Melody": source_notes}
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    assert len(result) == 1
    assert result[0].start == 1.0
    # timeline_end = max(src_end=1.5, duration_beats=4.0) = 4.0
    # duration = 4.0 - 1.0 = 3.0
    assert result[0].duration == 3.0


def test_follow_rhythm_float_precision_in_onsets(dummy_context):
    """Onsets with floating point noise should be deduplicated correctly."""
    source_notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.5),
        NoteInfo(pitch=64, start=0.0000001, duration=0.5),  # Very close to 0.0
        NoteInfo(pitch=67, start=0.5, duration=0.5),
    ]
    follower_notes = [
        NoteInfo(pitch=48, start=0.25, duration=1.0),
    ]
    ctx = ModifierContext(
        duration_beats=4.0, chords=[], timeline=None, scale=None, tracks={"Melody": source_notes}
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    # Round to 4 decimals should treat 0.0 and 0.0000001 as same onset
    unique_starts = len(set(round(n.start, 4) for n in result))
    assert unique_starts == 2  # Two unique onsets after rounding


def test_follow_rhythm_source_shorter_than_follower(dummy_context):
    """Source track shorter than follower should still work correctly."""
    source_notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.25),
        NoteInfo(pitch=64, start=1.0, duration=0.25),
    ]
    follower_notes = [
        NoteInfo(pitch=48, start=0.0, duration=4.0),
        NoteInfo(pitch=52, start=2.0, duration=4.0),
    ]
    ctx = ModifierContext(
        duration_beats=8.0, chords=[], timeline=None, scale=None, tracks={"Melody": source_notes}
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    # Should have same number of notes as unique source onsets
    assert len(result) == 2
    assert result[0].start == 0.0
    assert result[1].start == 1.0


def test_follow_rhythm_identical_onset_different_pitches(dummy_context):
    """Multiple notes at same onset time should produce one output note."""
    source_notes = [
        NoteInfo(pitch=60, start=0.0, duration=0.5),
        NoteInfo(pitch=64, start=0.0, duration=0.5),  # Same start, different pitch
        NoteInfo(pitch=67, start=0.0, duration=0.3),  # Same start, different duration
    ]
    follower_notes = [
        NoteInfo(pitch=48, start=0.0, duration=1.0),
    ]
    ctx = ModifierContext(
        duration_beats=4.0, chords=[], timeline=None, scale=None, tracks={"Melody": source_notes}
    )
    mod = FollowRhythmModifier(source_track="Melody")
    result = mod.modify(follower_notes, ctx)

    # All three source notes at same onset should produce exactly one output
    assert len(result) == 1
    assert result[0].start == 0.0
