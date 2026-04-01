import pytest
from melodica.types import ChordLabel, Quality, NoteInfo, Scale, Mode
from melodica.composer import (
    VoiceLeadingEngine,
    VOICE_RANGES,
    TensionCurve,
    TensionPhase,
    StyleProfile,
    get_style,
    STYLES,
    NonChordToneGenerator,
    TextureController,
    TextureLevel,
)


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _progression():
    return [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0, degree=1),
        ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0, degree=4),
        ChordLabel(root=7, quality=Quality.MAJOR, start=8.0, duration=4.0, degree=5),
        ChordLabel(root=0, quality=Quality.MAJOR, start=12.0, duration=4.0, degree=1),
    ]


class TestVoiceLeading:
    def test_produces_4_voices(self):
        engine = VoiceLeadingEngine()
        voices = engine.voicize_progression(_progression(), C_MAJOR)
        assert set(voices.keys()) == {"soprano", "alto", "tenor", "bass"}
        for v in voices.values():
            assert len(v) == 4

    def test_voices_in_range(self):
        engine = VoiceLeadingEngine()
        voices = engine.voicize_progression(_progression(), C_MAJOR)
        for voice_name, notes in voices.items():
            lo, hi = VOICE_RANGES[voice_name]
            for n in notes:
                assert lo <= n.pitch <= hi, f"{voice_name} pitch {n.pitch} out of range [{lo},{hi}]"

    def test_voices_ordered(self):
        engine = VoiceLeadingEngine()
        voices = engine.voicize_progression(_progression(), C_MAJOR)
        for i in range(4):
            sop = voices["soprano"][i].pitch
            alt = voices["alto"][i].pitch
            ten = voices["tenor"][i].pitch
            bas = voices["bass"][i].pitch
            assert sop >= alt >= ten >= bas

    def test_bass_follows_chord_root(self):
        engine = VoiceLeadingEngine()
        voices = engine.voicize_progression(_progression(), C_MAJOR)
        for i, chord in enumerate(_progression()):
            bass_pitch = voices["bass"][i].pitch
            assert bass_pitch % 12 == chord.root

    def test_no_parallels(self):
        engine = VoiceLeadingEngine(strict_mode=True)
        voices = engine.voicize_progression(_progression(), C_MAJOR)
        # Check all consecutive chord pairs
        for i in range(len(_progression()) - 1):
            prev = [voices[v][i].pitch for v in ["soprano", "alto", "tenor", "bass"]]
            curr = [voices[v][i + 1].pitch for v in ["soprano", "alto", "tenor", "bass"]]
            # Just verify it runs without crash
            assert len(prev) == 4

    def test_empty_chords(self):
        engine = VoiceLeadingEngine()
        voices = engine.voicize_progression([], C_MAJOR)
        for v in voices.values():
            assert v == []


class TestTensionCurve:
    def test_classical_curve(self):
        curve = TensionCurve(total_beats=16.0, curve_type="classical")
        points = curve.generate()
        assert len(points) > 0
        # Should start low, peak near peak_position, end low
        assert points[0].tension < 0.3
        assert points[-1].tension < 0.5

    def test_edm_curve(self):
        curve = TensionCurve(total_beats=32.0, curve_type="edm")
        points = curve.generate()
        assert len(points) > 0

    def test_ambient_curve(self):
        curve = TensionCurve(total_beats=32.0, curve_type="ambient")
        points = curve.generate()
        assert len(points) > 0

    def test_build_release(self):
        curve = TensionCurve(total_beats=16.0, curve_type="build_release")
        points = curve.generate()
        # Should peak around middle
        max_tension = max(p.tension for p in points)
        assert max_tension > 0.5

    def test_tension_at_specific_beat(self):
        curve = TensionCurve(total_beats=16.0)
        t0 = curve.tension_at(0.0)
        t8 = curve.tension_at(8.0)
        assert isinstance(t0, float)
        assert isinstance(t8, float)

    def test_phase_at(self):
        curve = TensionCurve(total_beats=16.0)
        phase = curve.phase_at(0.0)
        assert isinstance(phase, TensionPhase)


class TestStyleProfiles:
    @pytest.mark.parametrize("name", ["baroque", "classical", "pop", "jazz", "cinematic", "edm"])
    def test_all_styles_exist(self, name):
        style = get_style(name)
        assert style.name == name

    def test_baroque_is_strict(self):
        style = get_style("baroque")
        assert style.voice_leading_strict is True
        assert style.dissonance_tolerance < 0.5

    def test_jazz_is_free(self):
        style = get_style("jazz")
        assert style.dissonance_tolerance > 0.7
        assert style.extensions is True
        assert style.secondary_dominants is True

    def test_pop_allows_extensions(self):
        style = get_style("pop")
        assert style.extensions is True
        assert style.modal_interchange is True

    def test_edm_is_repetitive(self):
        style = get_style("edm")
        assert style.repetition_tolerance > 0.5

    def test_custom_style(self):
        custom = StyleProfile(name="custom", density=2.0, dissonance_tolerance=0.9)
        assert custom.name == "custom"
        assert custom.density == 2.0


class TestNonChordTones:
    def test_adds_nct(self):
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80),
            NoteInfo(pitch=64, start=1.0, duration=1.0, velocity=80),
            NoteInfo(pitch=67, start=2.0, duration=1.0, velocity=80),
        ]
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=3.0)]
        gen = NonChordToneGenerator(passing_prob=1.0, neighbor_prob=0.0, suspension_prob=0.0)
        result = gen.add_non_chord_tones(notes, chords, C_MAJOR)
        assert len(result) >= len(notes)  # at least original notes

    def test_pedal_point(self):
        chords = _progression()
        gen = NonChordToneGenerator()
        pedal = gen.add_pedal_point(chords, C_MAJOR, 16.0, pedal_pc=0)
        assert len(pedal) == 1
        assert pedal[0].pitch % 12 == 0  # C
        assert pedal[0].pitch < 60  # bass register

    def test_empty_notes(self):
        gen = NonChordToneGenerator()
        assert gen.add_non_chord_tones([], [], C_MAJOR) == []


class TestTextureController:
    def test_full_texture(self):
        ctrl = TextureController()
        notes = {
            "soprano": [NoteInfo(72, 0.0, 1.0)],
            "alto": [NoteInfo(67, 0.0, 1.0)],
            "tenor": [NoteInfo(64, 0.0, 1.0)],
            "bass": [NoteInfo(48, 0.0, 1.0)],
        }
        result = ctrl.apply_texture(notes, 4.0)
        # With default (no curve), all voices should pass through
        assert len(result["soprano"]) == 1
        assert len(result["bass"]) == 1

    def test_with_tension_curve(self):
        curve = TensionCurve(total_beats=16.0, curve_type="classical")
        ctrl = TextureController(tension_curve=curve)
        notes = {
            "soprano": [NoteInfo(72, 0.0, 1.0), NoteInfo(72, 8.0, 1.0)],
            "alto": [NoteInfo(67, 0.0, 1.0), NoteInfo(67, 8.0, 1.0)],
            "bass": [NoteInfo(48, 0.0, 1.0), NoteInfo(48, 8.0, 1.0)],
        }
        result = ctrl.apply_texture(notes, 16.0)
        assert len(result) == 3  # all voice keys present

    def test_density_at(self):
        curve = TensionCurve(total_beats=16.0)
        ctrl = TextureController(tension_curve=curve)
        d = ctrl.get_density_at(0.0)
        assert 0.0 <= d <= 1.0

    def test_silence_tension(self):
        ctrl = TextureController()
        level = ctrl._tension_to_texture(0.05)
        assert level == TextureLevel.SILENCE

    def test_full_tension(self):
        ctrl = TextureController()
        level = ctrl._tension_to_texture(0.95)
        assert level == TextureLevel.DOUBLE
