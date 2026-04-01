import pytest
from melodica.types import ChordLabel, Quality, Scale, Mode, NoteInfo
from melodica.composer.phrase_memory import PhraseMemory, Phrase, Transform
from melodica.composer.harmonic_awareness import (
    pitch_class_weights,
    guide_tones,
    avoid_notes,
    chord_tone_pcs,
    weight_pitch,
    best_chord_tone,
    guide_tone_resolution,
)
from melodica.composer.candidate_scorer import CandidateScorer, ScoringContext, pick_best_note
from melodica.composer.unified_style import (
    get_unified_style,
    list_styles,
    register_style,
    UnifiedStyle,
    HarmonyProfile,
    MelodyProfile,
    RhythmProfile,
    InstrumentationProfile,
)
from melodica.rhythm.markov_rhythm import MarkovRhythmGenerator, RhythmEvent


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


# ─── PhraseMemory ─────────────────────────────────────────────────────────


class TestPhraseMemory:
    def test_store_and_size(self):
        pm = PhraseMemory(max_size=10)
        notes = (NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),)
        phrase = Phrase(notes=notes)
        pm.store(phrase)
        assert pm.size == 1
        assert pm.has_phrases()

    def test_store_notes(self):
        pm = PhraseMemory()
        notes = [NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80)]
        pm.store_notes(notes, section="A", bar=1, chord_root=0, tag="melody")
        assert pm.size == 1

    def test_clear(self):
        pm = PhraseMemory()
        pm.store(Phrase(notes=(NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),)))
        pm.clear()
        assert pm.size == 0
        assert not pm.has_phrases()

    def test_get_all(self):
        pm = PhraseMemory()
        pm.store_notes([NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80)], "A", 1, 0)
        pm.store_notes([NoteInfo(pitch=64, start=0.0, duration=0.5, velocity=80)], "B", 2, 0)
        all_phrases = pm.get_all()
        assert len(all_phrases) == 2

    def test_get_by_section(self):
        pm = PhraseMemory()
        pm.store_notes([NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80)], "A", 1, 0)
        pm.store_notes([NoteInfo(pitch=64, start=0.0, duration=0.5, velocity=80)], "B", 2, 0)
        a_phrases = pm.get_by_section("A")
        assert len(a_phrases) == 1

    def test_get_by_tag(self):
        pm = PhraseMemory()
        pm.store_notes(
            [NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80)], "A", 1, 0, tag="melody"
        )
        pm.store_notes(
            [NoteInfo(pitch=64, start=0.0, duration=0.5, velocity=80)], "A", 1, 0, tag="bass"
        )
        melody_phrases = pm.get_by_tag("melody")
        assert len(melody_phrases) == 1

    def test_get_most_recent(self):
        pm = PhraseMemory()
        for i in range(5):
            pm.store_notes(
                [NoteInfo(pitch=60 + i, start=0.0, duration=0.5, velocity=80)], "A", i, 0
            )
        recent = pm.get_most_recent(2)
        assert len(recent) == 2

    def test_recall_original(self):
        pm = PhraseMemory()
        notes = [NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80)]
        pm.store_notes(notes, "A", 1, 0)
        recalled = pm.recall(section="A", transform=Transform.ORIGINAL)
        assert recalled is not None
        assert len(recalled) == 1
        assert recalled[0].pitch == 60

    def test_recall_transpose(self):
        pm = PhraseMemory()
        notes = [NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80)]
        pm.store_notes(notes, "A", 1, 0)
        recalled = pm.recall(section="A", transform=Transform.TRANSPOSE, transpose=5)
        assert recalled is not None
        assert recalled[0].pitch == 65

    def test_recall_inversion(self):
        pm = PhraseMemory()
        notes = [NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80)]
        pm.store_notes(notes, "A", 1, 0)
        recalled = pm.recall(section="A", transform=Transform.INVERSION)
        assert recalled is not None
        assert len(recalled) == 1

    def test_recall_retrograde(self):
        pm = PhraseMemory()
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),
            NoteInfo(pitch=64, start=0.5, duration=0.5, velocity=80),
            NoteInfo(pitch=67, start=1.0, duration=0.5, velocity=80),
        ]
        pm.store_notes(notes, "A", 1, 0)
        recalled = pm.recall(section="A", transform=Transform.RETROGRADE)
        assert recalled is not None
        assert len(recalled) == 3
        assert recalled[0].pitch == 67
        assert recalled[-1].pitch == 60

    def test_recall_augmentation(self):
        pm = PhraseMemory()
        notes = [NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80)]
        pm.store_notes(notes, "A", 1, 0)
        recalled = pm.recall(section="A", transform=Transform.AUGMENTATION)
        assert recalled is not None
        assert recalled[0].duration == 1.0

    def test_recall_diminution(self):
        pm = PhraseMemory()
        notes = [NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80)]
        pm.store_notes(notes, "A", 1, 0)
        recalled = pm.recall(section="A", transform=Transform.DIMINUTION)
        assert recalled is not None
        assert recalled[0].duration == 0.5

    def test_recall_with_pitch_range(self):
        pm = PhraseMemory()
        notes = [NoteInfo(pitch=48, start=0.0, duration=0.5, velocity=80)]
        pm.store_notes(notes, "A", 1, 0)
        recalled = pm.recall(section="A", low=55, high=80)
        assert recalled is not None
        assert recalled[0].pitch >= 55

    def test_recall_no_match_returns_none(self):
        pm = PhraseMemory()
        recalled = pm.recall(section="X")
        assert recalled is None

    def test_recall_as_new_sequence(self):
        pm = PhraseMemory()
        notes = [NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80)]
        pm.store_notes(notes, "A", 1, 0)
        recalled = pm.recall_as_new_sequence(section="A", start_at=4.0)
        assert recalled is not None
        assert recalled[0].start == 4.0

    def test_find_similar(self):
        pm = PhraseMemory()
        notes1 = [NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80)]
        notes2 = [NoteInfo(pitch=72, start=0.0, duration=0.5, velocity=80)]
        pm.store_notes(notes1, "A", 1, 0)
        pm.store_notes(notes2, "B", 1, 0)
        target = Phrase(notes=tuple(notes1))
        similar = pm.find_similar(target, top_k=1)
        assert len(similar) == 1

    def test_max_size_eviction(self):
        pm = PhraseMemory(max_size=2)
        for i in range(5):
            pm.store_notes([NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80)], "A", i, 0)
        assert pm.size == 2


# ─── HarmonicAwareness ───────────────────────────────────────────────────


class TestPitchClassWeights:
    def test_major_chord_weights(self):
        weights = pitch_class_weights(0, Quality.MAJOR, 1.0)
        assert 0 in weights  # root
        assert 4 in weights  # major third
        assert 7 in weights  # fifth
        assert weights[0] > 0

    def test_minor_chord_weights(self):
        weights = pitch_class_weights(0, Quality.MINOR, 1.0)
        assert 0 in weights
        assert 3 in weights  # minor third
        assert 7 in weights

    def test_beat_strength_affects_weights(self):
        w_strong = pitch_class_weights(0, Quality.MAJOR, 1.0)
        w_weak = pitch_class_weights(0, Quality.MAJOR, 0.25)
        # Root weight should be present for both
        assert w_strong[0] >= w_weak[0]


class TestGuideTones:
    def test_major_guide_tones(self):
        gt = guide_tones(0, Quality.MAJOR)
        assert "3rd" in gt

    def test_minor_guide_tones(self):
        gt = guide_tones(0, Quality.MINOR)
        assert gt["3rd"] == 3  # minor third

    def test_dominant_guide_tones(self):
        gt = guide_tones(7, Quality.DOMINANT7)
        assert gt["7th"] == 5  # F (pitch class of minor 7th of G)


class TestAvoidNotes:
    def test_major_avoid_notes(self):
        avoid = avoid_notes(0, Quality.MAJOR)
        assert isinstance(avoid, list)

    def test_minor_avoid_notes(self):
        avoid = avoid_notes(0, Quality.MINOR)
        assert isinstance(avoid, list)


class TestChordTonePcs:
    def test_major_chord_tones(self):
        pcs = chord_tone_pcs(0, Quality.MAJOR)
        assert 0 in pcs  # root
        assert 4 in pcs  # third
        assert 7 in pcs  # fifth

    def test_minor_chord_tones(self):
        pcs = chord_tone_pcs(0, Quality.MINOR)
        assert 0 in pcs
        assert 3 in pcs  # minor third
        assert 7 in pcs


class TestWeightPitch:
    def test_chord_tone_high_weight(self):
        w = weight_pitch(60, 0, Quality.MAJOR, 1.0)  # C4 over C major
        assert w > 0

    def test_non_chord_tone_lower_weight(self):
        w_chord = weight_pitch(60, 0, Quality.MAJOR, 1.0)
        w_non = weight_pitch(61, 0, Quality.MAJOR, 1.0)  # C#4
        assert w_chord >= w_non


class TestBestChordTone:
    def test_returns_valid_pitch(self):
        pitch = best_chord_tone(60, 0, Quality.MAJOR, 48, 84)
        assert 48 <= pitch <= 84
        assert pitch % 12 in chord_tone_pcs(0, Quality.MAJOR)

    def test_different_root(self):
        pitch = best_chord_tone(60, 7, Quality.MAJOR, 48, 84)
        assert 48 <= pitch <= 84


class TestGuideToneResolution:
    def test_resolves_to_valid_pc(self):
        resolved = guide_tone_resolution(11, 0, 7, Quality.MAJOR)  # B over C -> G chord
        assert 0 <= resolved <= 11

    def test_dominant_to_tonic(self):
        resolved = guide_tone_resolution(10, 7, 0, Quality.MAJOR)  # F over G7 -> C
        assert resolved in chord_tone_pcs(0, Quality.MAJOR)


# ─── CandidateScorer ─────────────────────────────────────────────────────


class TestCandidateScorer:
    def _make_context(self) -> ScoringContext:
        return ScoringContext(
            prev_pitch=60,
            chord_root=0,
            chord_quality=Quality.MAJOR,
            scale_pcs=[0, 2, 4, 5, 7, 9, 11],
            beat_strength=1.0,
            recent_pitches=[60, 64, 67],
            preferred_contour="rising",
            low=48,
            high=84,
        )

    def test_score_returns_float(self):
        scorer = CandidateScorer()
        ctx = self._make_context()
        s = scorer.score(64, ctx)
        assert isinstance(s, float)

    def test_chord_tone_scores_higher(self):
        scorer = CandidateScorer()
        ctx = self._make_context()
        s_chord = scorer.score(64, ctx)  # E (major third of C)
        s_non = scorer.score(61, ctx)  # C# (not in C major)
        assert s_chord >= s_non

    def test_pick_best(self):
        scorer = CandidateScorer()
        ctx = self._make_context()
        candidates = [60, 61, 64, 67]
        best = scorer.pick_best(candidates, ctx)
        assert best in candidates

    def test_pick_best_note(self):
        scorer = CandidateScorer()
        ctx = self._make_context()
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),
            NoteInfo(pitch=64, start=0.0, duration=0.5, velocity=80),
            NoteInfo(pitch=67, start=0.0, duration=0.5, velocity=80),
        ]
        best = scorer.pick_best_note(notes, ctx)
        assert isinstance(best, NoteInfo)

    def test_convenience_pick_best_note(self):
        best = pick_best_note(
            [60, 64, 67],
            prev_pitch=60,
            chord_root=0,
            quality=Quality.MAJOR,
            scale_pcs=[0, 2, 4, 5, 7, 9, 11],
            beat_strength=1.0,
        )
        assert isinstance(best, int)
        assert best in [60, 64, 67]

    def test_contour_preference(self):
        scorer = CandidateScorer()
        ctx_rising = ScoringContext(
            prev_pitch=60,
            chord_root=0,
            chord_quality=Quality.MAJOR,
            scale_pcs=[0, 2, 4, 5, 7, 9, 11],
            beat_strength=1.0,
            recent_pitches=[60],
            preferred_contour="rising",
            low=48,
            high=84,
        )
        ctx_falling = ScoringContext(
            prev_pitch=60,
            chord_root=0,
            chord_quality=Quality.MAJOR,
            scale_pcs=[0, 2, 4, 5, 7, 9, 11],
            beat_strength=1.0,
            recent_pitches=[60],
            preferred_contour="falling",
            low=48,
            high=84,
        )
        s_up = scorer.score(67, ctx_rising)
        s_down = scorer.score(55, ctx_falling)
        # Higher notes should score better with rising contour
        assert s_up > scorer.score(55, ctx_rising)

    def test_range_penalty(self):
        scorer = CandidateScorer()
        ctx = ScoringContext(
            prev_pitch=60,
            chord_root=0,
            chord_quality=Quality.MAJOR,
            scale_pcs=[0, 2, 4, 5, 7, 9, 11],
            beat_strength=1.0,
            recent_pitches=[60],
            preferred_contour="neutral",
            low=48,
            high=72,
        )
        s_in = scorer.score(60, ctx)
        s_out = scorer.score(90, ctx)
        assert s_in > s_out


# ─── UnifiedStyle ─────────────────────────────────────────────────────────


class TestUnifiedStyle:
    @pytest.mark.parametrize(
        "name", ["baroque", "classical", "pop", "jazz", "cinematic", "edm", "ambient"]
    )
    def test_get_builtin_styles(self, name):
        style = get_unified_style(name)
        assert isinstance(style, UnifiedStyle)
        assert style.name

    def test_unknown_style_returns_pop(self):
        style = get_unified_style("nonexistent")
        assert style.name == "pop"

    def test_list_styles(self):
        styles = list_styles()
        assert "pop" in styles
        assert "jazz" in styles
        assert len(styles) >= 7

    def test_register_custom_style(self):
        custom = UnifiedStyle(
            name="test_custom",
            harmony=HarmonyProfile(),
            melody=MelodyProfile(),
            rhythm=RhythmProfile(),
            instrumentation=InstrumentationProfile(),
        )
        register_style(custom)
        retrieved = get_unified_style("test_custom")
        assert retrieved.name == "test_custom"

    def test_style_profiles_exist(self):
        style = get_unified_style("jazz")
        assert isinstance(style.harmony, HarmonyProfile)
        assert isinstance(style.melody, MelodyProfile)
        assert isinstance(style.rhythm, RhythmProfile)
        assert isinstance(style.instrumentation, InstrumentationProfile)

    def test_jazz_style_has_extensions(self):
        style = get_unified_style("jazz")
        assert style.harmony.extensions is True

    def test_pop_style_has_qualities(self):
        style = get_unified_style("pop")
        assert isinstance(style.harmony.allowed_qualities, tuple)

    def test_ambient_style_sparse(self):
        style = get_unified_style("ambient")
        assert style.rhythm.density < 0.5


# ─── MarkovRhythmGenerator ───────────────────────────────────────────────


class TestMarkovRhythmGenerator:
    def test_generates_events(self):
        gen = MarkovRhythmGenerator(seed=42)
        events = gen.generate(4.0)
        assert len(events) > 0
        assert all(isinstance(e, RhythmEvent) for e in events)

    @pytest.mark.parametrize("style", ["straight", "swing", "ballad", "driving"])
    def test_styles(self, style):
        gen = MarkovRhythmGenerator(style=style, seed=42)
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_syncopation(self):
        gen_low = MarkovRhythmGenerator(syncopation=0.0, seed=42)
        gen_high = MarkovRhythmGenerator(syncopation=1.0, seed=42)
        events_low = gen_low.generate(4.0)
        events_high = gen_high.generate(4.0)
        assert len(events_low) > 0
        assert len(events_high) > 0

    def test_phrase_length(self):
        gen = MarkovRhythmGenerator(phrase_length=4, seed=42)
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_downbeat_preference(self):
        gen = MarkovRhythmGenerator(downbeat_preference=1.0, seed=42)
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_seed_reproducibility(self):
        gen1 = MarkovRhythmGenerator(seed=123)
        gen2 = MarkovRhythmGenerator(seed=123)
        e1 = gen1.generate(4.0)
        e2 = gen2.generate(4.0)
        assert len(e1) == len(e2)

    def test_train_from_durations(self):
        durations = [0.25, 0.25, 0.5, 0.25, 0.25, 0.5]
        transitions = MarkovRhythmGenerator.train_from_durations(durations, "test_style")
        assert isinstance(transitions, dict)

    def test_events_have_valid_onset(self):
        gen = MarkovRhythmGenerator(seed=42)
        events = gen.generate(4.0)
        for e in events:
            assert e.onset >= 0.0
            assert e.duration > 0.0
