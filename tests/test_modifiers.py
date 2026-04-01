import pytest
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
