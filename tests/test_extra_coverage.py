import pytest
from unittest.mock import patch, MagicMock

from melodica.types import Note, NoteInfo, Scale, Mode, Quality, ChordLabel, HarmonizationRequest, IdeaTrack, PhraseInstance
from melodica.detection import _match_score, detect_chords_from_midi, _degree_to_function, HarmonicFunction, _merge_consecutive
from melodica.idea import _chords_for_slot

def test_note_velocity_out_of_range():
    with pytest.raises(ValueError):
        Note(pitch=60, start=0, duration=1, velocity=130)

def test_noteinfo_pitch_out_of_range():
    with pytest.raises(ValueError):
        NoteInfo(pitch=-1, start=0, duration=1)

def test_noteinfo_duration_out_of_range():
    with pytest.raises(ValueError):
        NoteInfo(pitch=60, start=0, duration=-1)

def test_scale_root_out_of_range():
    with pytest.raises(ValueError):
        Scale(root=12, mode=Mode.MAJOR)

def test_scale_contains():
    s = Scale(root=0, mode=Mode.MAJOR)
    assert s.contains(0)
    assert not s.contains(1)

def test_scale_degree_of_not_found():
    # Trigger the except ValueError to return None explicitly
    s = Scale(root=0, mode=Mode.MAJOR) # C, D, E, F, G, A, B (0, 2, 4, 5, 7, 9, 11)
    assert s.degree_of(1) is None # 1 is C#

def test_scale_diatonic_chord_invalid_degree():
    s = Scale(root=0, mode=Mode.MAJOR)
    with pytest.raises(ValueError):
        s.diatonic_chord(0)

def test_scale_diatonic_chord_augmented():
    s = Scale(root=9, mode=Mode.HARMONIC_MINOR)
    chord = s.diatonic_chord(3) # C E G# -> augmented
    assert chord.quality == Quality.AUGMENTED

def test_scale_diatonic_chord_fallback():
    s = Scale(root=0, mode=Mode.MAJOR)
    with patch.object(Scale, 'degrees', return_value=[0, 1, 2, 3, 4, 5, 6]):
        # index 0 is 0. 3rd is index 2 -> 2. 5th is index 4 -> 4.
        # Intervals are 2 and 4. (not 4,7 or 3,7 etc.)
        c = s.diatonic_chord(1)
        assert c.quality == Quality.MAJOR

def test_chordlabel_duration_out_of_range():
    with pytest.raises(ValueError):
        ChordLabel(root=0, quality=Quality.MAJOR, duration=0)

def test_chordlabel_contains_pitch_class():
    c = ChordLabel(root=0, quality=Quality.MAJOR)
    assert c.contains_pitch_class(4)
    assert not c.contains_pitch_class(1)

def test_harmonizationrequest_chord_rhythm():
    with pytest.raises(ValueError):
        HarmonizationRequest(melody=[Note(0,0,1)], key=Scale(0, Mode.MAJOR), chord_rhythm=0)

def test_ideatrack_empty_seeds():
    generator = MagicMock()
    with pytest.raises(ValueError, match="seed_phrases must not be empty"):
        IdeaTrack(seed_phrases=[], generator=generator)

def test_phrase_instance_render_parametric():
    generator = MagicMock()
    generator.render.return_value = []
    pi = PhraseInstance(generator=generator)
    c = ChordLabel(root=0, quality=Quality.MAJOR, duration=4)
    out = pi.render([c], Scale(0, Mode.MAJOR), 0)
    assert isinstance(out, list)
    generator.render.assert_called_once()

def test_phrase_instance_render_static():
    from melodica.types import StaticPhrase, NoteInfo
    notes = [NoteInfo(pitch=60, start=0, duration=1)]
    pi = PhraseInstance(static=StaticPhrase(notes=notes))
    out = pi.render([], Scale(0, Mode.MAJOR), 0)
    assert len(out) == 1
    assert out[0].pitch == 60

def test_detection_match_score_unknown_quality():
    # Cast 999 to Quality to bypass type checking here,
    # or just rely on passing int to trigger dict lookup failure.
    s = _match_score({0, 4, 7}, 0, 999, True)
    assert s == 0.0

def test_detection_chords_from_midi_empty():
    assert detect_chords_from_midi([]) == []

def test_detection_degree_to_function():
    assert _degree_to_function(2, Mode.MAJOR) == HarmonicFunction.SUBDOMINANT
    assert _degree_to_function(4, Mode.MAJOR) == HarmonicFunction.SUBDOMINANT
    assert _degree_to_function(5, Mode.MAJOR) == HarmonicFunction.DOMINANT
    assert _degree_to_function(7, Mode.MAJOR) == HarmonicFunction.DOMINANT

def test_detection_merge_consecutive():
    assert _merge_consecutive([]) == []
    # Test not merging when different
    c1 = ChordLabel(root=0, quality=Quality.MAJOR, duration=1)
    c2 = ChordLabel(root=5, quality=Quality.MAJOR, duration=1)
    res = _merge_consecutive([c1, c2])
    assert len(res) == 2
    # Test merging when the same
    c3 = ChordLabel(root=0, quality=Quality.MAJOR, duration=1)
    c4 = ChordLabel(root=0, quality=Quality.MAJOR, duration=1)
    res2 = _merge_consecutive([c3, c4])
    assert len(res2) == 1
    assert res2[0].duration == 2

def test_idea_chords_for_slot_fallback():
    c = ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=4)
    # Slot 1 is [8, 16) if beats_per_slot=8
    # c is [0, 4). They don't overlap.
    res = _chords_for_slot([c], 1, 8.0)
    assert len(res) == 1
    assert res[0].duration == 8.0
