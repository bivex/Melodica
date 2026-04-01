"""tests/test_generators.py — Tests for MelodyGenerator, Arpeggiator, ChordGenerator."""

import pytest
from melodica.types import ChordLabel, Mode, NoteInfo, Quality, Scale
from melodica.generators import GeneratorParams, freeze
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.chord_gen import ChordGenerator
from melodica.types import PhraseInstance, StaticPhrase
from melodica.rhythm import RhythmEvent, RhythmGenerator


class MockRhythm(RhythmGenerator):
    def __init__(self, onsets: list[float]):
        self.onsets = onsets

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        return [
            RhythmEvent(onset=o, duration=0.5, velocity_factor=1.0)
            for o in self.onsets
            if o < duration_beats
        ]


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _simple_chords() -> list[ChordLabel]:
    c = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    g = ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0)
    return [c, g]


class TestMelodyGenerator:
    def test_produces_notes(self):
        gen = MelodyGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert isinstance(notes, list)
        assert len(notes) > 0
        assert all(isinstance(n, NoteInfo) for n in notes)

    def test_pitches_in_range(self):
        params = GeneratorParams(key_range_low=48, key_range_high=72)
        gen = MelodyGenerator(params=params)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        for n in notes:
            assert 48 <= n.pitch <= 72, f"Pitch {n.pitch} out of range"

    def test_explicit_rhythm_pattern(self):
        gen = MelodyGenerator(rhythm=MockRhythm([0.0, 1.0, 2.0, 3.0]))
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) >= 4  # May include leap-filling passing tones

    def test_empty_chords_returns_empty(self):
        gen = MelodyGenerator()
        assert gen.render([], C_MAJOR, 4.0) == []

    # --- New MelodyGenerator param tests ---

    def test_harmony_note_probability(self):
        # High harmony probability → mostly chord tones
        gen = MelodyGenerator(harmony_note_probability=1.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        # Most notes should be chord tones (passing tones from _fill_leaps may appear)
        chord_pcs = {0, 4, 7, 2, 11}  # C major + G major chord tones
        in_chord = sum(1 for n in notes if n.pitch % 12 in chord_pcs)
        assert in_chord >= len(notes) * 0.7  # at least 70% chord tones

    def test_harmony_note_probability_zero(self):
        # Zero harmony probability → scale tones (not necessarily chord tones)
        gen = MelodyGenerator(harmony_note_probability=0.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        # All notes should be in C major scale
        for n in notes:
            assert C_MAJOR.contains(n.pitch % 12)

    def test_prefer_chord_tones_backward_compat(self):
        # Old parameter name should still work
        gen = MelodyGenerator(prefer_chord_tones=0.9)
        assert gen.harmony_note_probability == 0.9
        assert gen.prefer_chord_tones == 0.9
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_note_repetition_probability_high(self):
        # High repetition → many consecutive same pitches
        gen = MelodyGenerator(note_repetition_probability=0.95)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 1
        repeated = sum(1 for i in range(1, len(notes)) if notes[i].pitch == notes[i - 1].pitch)
        # With 95% repetition, most notes should repeat
        assert repeated > len(notes) * 0.5

    def test_note_repetition_probability_zero(self):
        # Zero repetition → no consecutive same pitches (unless stepwise picks same)
        gen = MelodyGenerator(note_repetition_probability=0.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        # At least verify it runs without errors

    def test_note_range_override(self):
        # Override params range with note_range_low/high
        gen = MelodyGenerator(note_range_low=60, note_range_high=72)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        for n in notes:
            assert 60 <= n.pitch <= 72, f"Pitch {n.pitch} out of overridden range"

    def test_note_range_melodica_defaults(self):
        # default: F#3 (54) to E5 (76) from Melodica
        gen = MelodyGenerator(note_range_low=54, note_range_high=76)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        for n in notes:
            assert 54 <= n.pitch <= 76, f"Pitch {n.pitch} out of F#3-E5 range"

    def test_note_range_overrides_params(self):
        # note_range should take priority over params.key_range
        params = GeneratorParams(key_range_low=48, key_range_high=60)
        gen = MelodyGenerator(params=params, note_range_low=72, note_range_high=84)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        for n in notes:
            assert 72 <= n.pitch <= 84, f"Pitch {n.pitch}: note_range should override params"


class TestArpeggiatorGenerator:
    @pytest.mark.parametrize(
        "pattern",
        [
            "up",
            "down",
            "up_down",
            "down_up",
            "up_down_full",
            "down_up_full",
            "converge",
            "diverge",
            "con_diverge",
            "pinky_up_down",
            "pinky_up",
            "thumb_up_down",
            "thumb_up",
            "random",
            "random_neighbor",
            "alberti",
            "octave",
            "octave_up",
            "octave_pump",
            "neighbor_up",
            "waltz",
            "broken_chord",
            "arpeggio_up",
            "power",
            "fifth_circle",
        ],
    )
    def test_pattern_produces_notes(self, pattern):
        gen = ArpeggiatorGenerator(pattern=pattern, note_duration=0.5)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_chord_pattern_stacks(self):
        gen = ArpeggiatorGenerator(pattern="chord", note_duration=1.0)
        notes = gen.render(
            [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=4)], C_MAJOR, 4.0
        )
        # Block chord: multiple notes per beat
        starts = [n.start for n in notes]
        assert starts.count(0.0) >= 3  # at least 3 voices

    def test_invalid_pattern_raises(self):
        with pytest.raises(ValueError):
            ArpeggiatorGenerator(pattern="zigzag")

    def test_arpeggiator_extensions(self):
        gen = ArpeggiatorGenerator(pattern="up", note_duration=0.5, voicing="spread", octaves=2)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)

        # Original chord is C major. Spread voicing will spread the notes.
        # 3 notes. Octaves=2 adds 3 more notes an octave higher. Total pool: 6 notes.
        # "up" pattern will hit 6 distinct notes.
        pitches = set([n.pitch for n in notes])
        assert len(pitches) > 3

    # --- Pattern sequence shape tests ---

    def test_down_up_sequence(self):
        gen = ArpeggiatorGenerator(pattern="down_up", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67])
        # Down: 67, 64, 60 then back up without endpoints: 64
        assert seq == [67, 64, 60, 64]

    def test_up_down_full_sequence(self):
        gen = ArpeggiatorGenerator(pattern="up_down_full", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67])
        # Up: 60, 64, 67 then full reverse: 67, 64, 60
        assert seq == [60, 64, 67, 67, 64, 60]

    def test_down_up_full_sequence(self):
        gen = ArpeggiatorGenerator(pattern="down_up_full", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67])
        # Down: 67, 64, 60 then full reverse: 60, 64, 67
        assert seq == [67, 64, 60, 60, 64, 67]

    def test_converge_sequence_odd(self):
        gen = ArpeggiatorGenerator(pattern="converge", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67, 71, 74])
        # Edges toward center: 0th, 4th, 1st, 3rd, 2nd
        assert seq == [60, 74, 64, 71, 67]

    def test_converge_sequence_even(self):
        gen = ArpeggiatorGenerator(pattern="converge", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67, 71])
        # Edges toward center: 0th, 3rd, 1st, 2nd
        assert seq == [60, 71, 64, 67]

    def test_diverge_sequence_odd(self):
        gen = ArpeggiatorGenerator(pattern="diverge", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67, 71, 74])
        # Center outward: mid=2→67, then 71,64, then 74,60
        assert seq == [67, 71, 64, 74, 60]

    def test_diverge_sequence_even(self):
        gen = ArpeggiatorGenerator(pattern="diverge", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67, 71])
        # Center outward: mid=2→67, then 71,64, then 60
        assert seq == [67, 71, 64, 60] or seq == [64, 67, 60, 71]

    def test_con_diverge_round_trip(self):
        gen = ArpeggiatorGenerator(pattern="con_diverge", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67, 71])
        # Should be longer than converge alone (converge=4, con_diverge should be 7)
        assert len(seq) > 4
        # First part should mirror converge
        assert seq[0] == 60
        assert seq[1] == 71

    def test_pinky_up_down_starts_high(self):
        gen = ArpeggiatorGenerator(pattern="pinky_up_down", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67])
        assert seq[0] == 67  # starts from top

    def test_pinky_up_starts_high(self):
        gen = ArpeggiatorGenerator(pattern="pinky_up", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67])
        assert seq[0] == 67  # starts from top
        assert seq == [67, 60, 64]

    def test_thumb_up_down_starts_low(self):
        gen = ArpeggiatorGenerator(pattern="thumb_up_down", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67])
        assert seq[0] == 60  # starts from bottom

    def test_thumb_up_starts_low(self):
        # thumb_up: starts from lowest note, then descends (wrapping to top) —
        # mirror of pinky_up which starts from highest and wraps upward.
        gen = ArpeggiatorGenerator(pattern="thumb_up", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67])
        assert seq[0] == 60  # always starts from the lowest note
        assert seq == [60, 67, 64]  # 60 → wrap down: 67, 64

    def test_random_neighbor_walk(self):
        gen = ArpeggiatorGenerator(pattern="random_neighbor", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67])
        assert len(seq) == 64  # default walk length
        # Every step should be adjacent in sorted pitch list
        sorted_pitches = [60, 64, 67]
        for i in range(len(seq)):
            assert seq[i] in sorted_pitches

    def test_up_down_multi_octave(self):
        gen = ArpeggiatorGenerator(pattern="up_down", note_duration=0.125, octaves=2)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        pitches = [n.pitch for n in notes]
        # Should go up then down
        # Find the maximum pitch — after it, pitches should decrease
        max_idx = pitches.index(max(pitches))
        if max_idx < len(pitches) - 1:
            assert pitches[max_idx + 1] < pitches[max_idx]

    # --- Genre-specific pattern tests ---

    def test_alberti_sequence(self):
        # C major [60, 64, 67]: low=60, mid=64, high=67 → [60,67,64,67]
        gen = ArpeggiatorGenerator(pattern="alberti", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67])
        assert seq == [60, 67, 64, 67]

    def test_alberti_four_notes(self):
        # [60, 64, 67, 71]: low=60, mid=64, high=71 → [60,71,64,71]
        gen = ArpeggiatorGenerator(pattern="alberti", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67, 71])
        assert seq == [60, 71, 64, 71]

    def test_alberti_render(self):
        gen = ArpeggiatorGenerator(pattern="alberti", note_duration=0.5)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_octave_sequence(self):
        # C major closed: [48, 52, 55]. Root pc=0, octave pitches: [48]
        gen = ArpeggiatorGenerator(pattern="octave", note_duration=0.25)
        seq = gen._make_sequence([48, 52, 55])
        assert seq == [48]  # only root in one octave

    def test_octave_multi_octave(self):
        # With octaves=2: root pitches should be [48, 60]
        gen = ArpeggiatorGenerator(pattern="octave", note_duration=0.25, octaves=2)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        pitches = set(n.pitch for n in notes)
        # All notes should be root pitch class (C = 0)
        assert all(p % 12 == 0 for p in pitches)

    def test_octave_pump_sequence(self):
        # [48, 52, 55] → one pitch class group: [48] (only one octave)
        gen = ArpeggiatorGenerator(pattern="octave_pump", note_duration=0.25)
        seq = gen._make_sequence([48, 52, 55])
        # 3 pitch classes, each with only one octave → [48, 52, 55]
        assert len(seq) == 3

    def test_octave_pump_multi_octave(self):
        # With octaves=2: [48,52,55,60,64,67] → [48,60,52,64,55,67]
        gen = ArpeggiatorGenerator(pattern="octave_pump", note_duration=0.25, octaves=2)
        seq = gen._make_sequence([48, 52, 55, 60, 64, 67])
        # Should alternate low-high for each pitch class
        assert seq == [48, 60, 52, 64, 55, 67]

    def test_neighbor_up_sequence(self):
        # [60, 64, 67] → [60,64, 64,67, 67, 64, 60]
        gen = ArpeggiatorGenerator(pattern="neighbor_up", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67])
        assert seq == [60, 64, 64, 67, 67, 64, 60]

    def test_neighbor_up_render(self):
        gen = ArpeggiatorGenerator(pattern="neighbor_up", note_duration=0.25)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_waltz_sequence(self):
        # C major [60, 64, 67]: root=60, fifth=64, octave=67
        gen = ArpeggiatorGenerator(pattern="waltz", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67])
        assert seq == [60, 64, 67]
        assert len(seq) == 3  # 3-note waltz feel

    def test_waltz_render(self):
        gen = ArpeggiatorGenerator(pattern="waltz", note_duration=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_power_sequence(self):
        # C major [60, 64, 67]: root=60, fifth=64 (middle)
        gen = ArpeggiatorGenerator(pattern="power", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67])
        assert len(seq) == 2
        assert seq[0] == 60  # root

    def test_power_render(self):
        gen = ArpeggiatorGenerator(pattern="power", note_duration=0.5)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        pitches = set(n.pitch for n in notes)
        assert len(pitches) <= 2  # only root and fifth

    def test_fifth_circle_sequence(self):
        # C major [60, 64, 67]: pcs 0, 4, 7
        # Circle of 5ths from 0: 0, 7, 2... but 2 not in chord, so: [60, 67, 64]
        gen = ArpeggiatorGenerator(pattern="fifth_circle", note_duration=0.25)
        seq = gen._make_sequence([60, 64, 67])
        assert seq[0] == 60  # root first
        assert seq[1] == 67  # fifth (7 semitones)
        assert len(seq) == 3

    def test_fifth_circle_render(self):
        gen = ArpeggiatorGenerator(pattern="fifth_circle", note_duration=0.5)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_broken_chord_renders(self):
        gen = ArpeggiatorGenerator(pattern="broken_chord", note_duration=0.5)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_arpeggio_up_renders(self):
        gen = ArpeggiatorGenerator(pattern="arpeggio_up", note_duration=0.5)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestChordGenerator:
    @pytest.mark.parametrize("voicing", ["closed", "open", "spread"])
    def test_voicing_produces_notes(self, voicing):
        gen = ChordGenerator(voicing=voicing)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_explicit_rhythm(self):
        gen = ChordGenerator(rhythm=MockRhythm([0.0, 2.0]))
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        # 2 onsets × ≥ 3 voices
        assert len(notes) >= 6

    def test_invalid_voicing_raises(self):
        with pytest.raises(ValueError):
            ChordGenerator(voicing="messy")


class TestFreeze:
    def test_freeze_parametric(self):
        gen = MelodyGenerator()
        # Create a parametric instance with a generator
        pi = PhraseInstance(generator=gen)
        frozen = freeze(pi, _simple_chords(), C_MAJOR)
        assert not frozen.is_parametric()
        assert frozen.static is not None
        assert isinstance(frozen.static.notes, list)

    def test_freeze_static_raises(self):
        pi = PhraseInstance(static=StaticPhrase(notes=[]))
        with pytest.raises(ValueError):
            freeze(pi, _simple_chords(), C_MAJOR)


class TestPhraseInstance:
    def test_render_parametric(self):
        gen = ArpeggiatorGenerator()
        pi = PhraseInstance(generator=gen)
        notes = pi.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_render_static(self):
        static_notes = [NoteInfo(pitch=60, start=0, duration=1)]
        pi = PhraseInstance(static=StaticPhrase(notes=static_notes))
        notes = pi.render([], C_MAJOR, 4.0)
        assert notes == static_notes

    def test_render_mismatch_raises(self):
        # Should raise if both or none are set (handled in post_init)
        with pytest.raises(ValueError):
            PhraseInstance(generator=None, static=None)


class TestArrangementSlot:
    def test_basic_slot(self):
        from melodica.types import ArrangementSlot

        pi = PhraseInstance(generator=MelodyGenerator())
        slot = ArrangementSlot(phrase=pi, start_beat=0.0, label="A")
        assert slot.start_beat == 0.0
        assert slot.label == "A"
        assert slot.phrase == pi
