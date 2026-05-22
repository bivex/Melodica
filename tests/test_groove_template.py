# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

from melodica.rhythm import RhythmEvent, GrooveTemplate, GrooveSlot, GROOVE_PRESETS
from melodica.rhythm.groove_template import STRAIGHT, SWING_60, HARD_SWING, SHUFFLE, LAID_BACK


class TestGrooveSlot:
    def test_creation(self):
        s = GrooveSlot(position=0.5, timing_offset=3.5, velocity_factor=0.88)
        assert s.position == 0.5
        assert s.timing_offset == 3.5
        assert s.velocity_factor == 0.88

    def test_frozen(self):
        s = GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=1.0)
        try:
            s.position = 0.5
            assert False, "Should be frozen"
        except AttributeError:
            pass


class TestGrooveTemplate:
    def test_straight_no_change(self):
        events = [
            RhythmEvent(onset=0.0, duration=1.0, velocity_factor=1.0),
            RhythmEvent(onset=1.0, duration=1.0, velocity_factor=1.0),
        ]
        result = STRAIGHT.apply(events)
        assert len(result) == 2
        assert result[0].onset == 0.0
        assert result[1].onset == 1.0

    def test_empty_slots_returns_copy(self):
        gt = GrooveTemplate(name="empty")
        events = [RhythmEvent(onset=0.0, duration=1.0, velocity_factor=1.0)]
        result = gt.apply(events)
        assert result is not events
        assert len(result) == 1

    def test_swing_shifts_offbeats(self):
        events = [
            RhythmEvent(onset=0.0, duration=0.5, velocity_factor=1.0),
            RhythmEvent(onset=0.5, duration=0.5, velocity_factor=1.0),
        ]
        result = SWING_60.apply(events)
        assert len(result) == 2
        # On-beat (position 0.0) unchanged
        assert result[0].onset == 0.0
        # Off-beat (position 0.5) shifted later
        assert result[1].onset > 0.5

    def test_swing_reduces_velocity(self):
        events = [
            RhythmEvent(onset=0.5, duration=0.5, velocity_factor=1.0),
        ]
        result = SWING_60.apply(events)
        assert result[0].velocity_factor < 1.0

    def test_hard_swing_more_shift(self):
        events = [
            RhythmEvent(onset=0.5, duration=0.5, velocity_factor=1.0),
        ]
        swing_result = SWING_60.apply(events)
        hard_result = HARD_SWING.apply(events)
        assert hard_result[0].onset > swing_result[0].onset

    def test_empty_events(self):
        result = SWING_60.apply([])
        assert result == []

    def test_non_matching_position_unchanged(self):
        events = [
            RhythmEvent(onset=0.33, duration=0.5, velocity_factor=1.0),
        ]
        result = SWING_60.apply(events)
        assert result[0].onset == 0.33
        assert result[0].velocity_factor == 1.0


class TestGroovePresets:
    def test_all_presets_exist(self):
        assert "straight" in GROOVE_PRESETS
        assert "swing_60" in GROOVE_PRESETS
        assert "hard_swing" in GROOVE_PRESETS
        assert "shuffle" in GROOVE_PRESETS
        assert "laid_back" in GROOVE_PRESETS
        assert "push" in GROOVE_PRESETS
        assert "reggae" in GROOVE_PRESETS
        assert "bossa" in GROOVE_PRESETS
        assert "hip_hop" in GROOVE_PRESETS
        assert "dnb" in GROOVE_PRESETS
        assert "waltz_rubato" in GROOVE_PRESETS
        assert "mazurka" in GROOVE_PRESETS
        assert "bolero" in GROOVE_PRESETS
        assert "samba" in GROOVE_PRESETS
        assert "funk" in GROOVE_PRESETS
        assert "afro_6_8" in GROOVE_PRESETS

    def test_preset_count(self):
        assert len(GROOVE_PRESETS) >= 16

    def test_straight_has_no_slots(self):
        assert len(STRAIGHT.slots) == 0

    def test_swing_has_two_slots(self):
        assert len(SWING_60.slots) == 2

    def test_shuffle_has_three_slots(self):
        assert len(SHUFFLE.slots) == 3

    def test_laid_back_has_four_slots(self):
        assert len(LAID_BACK.slots) == 4


class TestGrooveValidator:
    def test_verify_accuracy(self):
        from melodica.types import NoteInfo
        # SWING_60 has slot 0.5 shifted by 3.5ms (0.035 beats)
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=64),
            NoteInfo(pitch=62, start=0.535, duration=0.5, velocity=64),
            NoteInfo(pitch=64, start=1.0, duration=0.5, velocity=64),
            NoteInfo(pitch=65, start=1.535, duration=0.5, velocity=64),
        ]
        res = SWING_60.verify_accuracy(notes)
        assert res["accuracy"] == 1.0
        assert res["total_notes"] == 4
        assert res["matched_notes"] == 4
        assert len(res["details"]) > 0


class TestProDrumUpgrades:
    def test_drum_generators_groove_template(self):
        from melodica.generators.trap_drums import TrapDrumsGenerator
        from melodica.generators.electronic_drums import ElectronicDrumsGenerator
        from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
        from melodica.generators import GeneratorParams
        from melodica.types import ChordLabel, Scale, Mode

        chords = [ChordLabel(root=0, quality="major", start=0.0, duration=4.0)]
        key = Scale(root=0, mode=Mode.MAJOR)
        params = GeneratorParams()

        # 1. TrapDrumsGenerator with groove template
        tg = TrapDrumsGenerator(params, groove_template=SWING_60)
        t_notes = tg.render(chords, key, duration_beats=4.0)
        # Assert some notes exist and are shifted off standard straight grid if they are offbeats
        assert len(t_notes) > 0
        swung_notes = [n for n in t_notes if abs((n.start % 1.0) - 0.535) < 0.01]
        assert len(swung_notes) > 0 or any(n.start % 0.5 != 0.0 for n in t_notes)

        # 2. ElectronicDrumsGenerator with groove template
        eg = ElectronicDrumsGenerator(params, groove_template=SWING_60)
        e_notes = eg.render(chords, key, duration_beats=4.0)
        assert len(e_notes) > 0
        e_swung = [n for n in e_notes if abs((n.start % 1.0) - 0.535) < 0.01]
        assert len(e_swung) > 0 or any(n.start % 0.5 != 0.0 for n in e_notes)

        # 3. DrumKitPatternGenerator with groove template
        dg = DrumKitPatternGenerator(params, groove_template=SWING_60)
        d_notes = dg.render(chords, key, duration_beats=4.0)
        assert len(d_notes) > 0
        d_swung = [n for n in d_notes if abs((n.start % 1.0) - 0.535) < 0.01]
        assert len(d_swung) > 0 or any(n.start % 0.5 != 0.0 for n in d_notes)

    def test_808_legato_glides(self):
        from melodica.generators.trap_drums import TrapDrumsGenerator
        from melodica.generators import GeneratorParams
        from melodica.types import ChordLabel, Scale, Mode

        # Force consecutive 808 notes with different pitches
        chords = [
            ChordLabel(root=0, quality="major", start=0.0, duration=2.0),
            ChordLabel(root=7, quality="major", start=2.0, duration=2.0),
        ]
        key = Scale(root=0, mode=Mode.MAJOR)
        params = GeneratorParams(key_range_low=36)

        tg = TrapDrumsGenerator(params, section_type="verse")
        notes = tg.render(chords, key, duration_beats=4.0)
        
        # Check if we have multiple 808 sub-bass notes
        sub_notes = [n for n in notes if getattr(n, "articulation", None) == "808"]
        # Standard rendering should produce slide notes for overlapping consecutive 808s
        slide_notes = [n for n in sub_notes if n.duration < 0.2]
        assert len(slide_notes) > 0
        # Ensure they have pitches intermediate or equal to the target chord root pitches
        assert any(36 <= n.pitch <= 50 for n in slide_notes)

    def test_snare_tom_flams_and_drags(self):
        from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
        from melodica.generators import GeneratorParams
        from melodica.types import ChordLabel, Scale, Mode

        chords = [ChordLabel(root=0, quality="major", start=0.0, duration=4.0)]
        key = Scale(root=0, mode=Mode.MAJOR)
        params = GeneratorParams()

        # Flam only
        dg_flam = DrumKitPatternGenerator(params, flam_probability=1.0, drag_probability=0.0)
        notes_flam = dg_flam.render(chords, key, duration_beats=4.0)
        graces_flam = [n for n in notes_flam if getattr(n, "articulation", None) == "grace"]
        assert len(graces_flam) > 0

        # Drag only
        dg_drag = DrumKitPatternGenerator(params, flam_probability=0.0, drag_probability=1.0)
        notes_drag = dg_drag.render(chords, key, duration_beats=4.0)
        graces_drag = [n for n in notes_drag if getattr(n, "articulation", None) == "grace"]
        assert len(graces_drag) >= 2

    def test_hand_struck_coordination_safeguards(self):
        from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
        from melodica.generators import GeneratorParams
        from melodica.types import ChordLabel, Scale, NoteInfo

        # Manually verify coordinating logic
        params = GeneratorParams()
        dg = DrumKitPatternGenerator(params)
        
        # Build impossible simultaneous struck notes (SNARE, HH_CLOSED, HH_OPEN, TOM_LOW, CRASH, RIDE)
        impossible_notes = [
            NoteInfo(pitch=38, start=1.0, duration=0.2, velocity=80), # SNARE (Priority 1)
            NoteInfo(pitch=49, start=1.0, duration=0.2, velocity=80), # CRASH (Priority 2)
            NoteInfo(pitch=42, start=1.0, duration=0.2, velocity=80), # HH_CLOSED (Priority 5)
            NoteInfo(pitch=46, start=1.0, duration=0.2, velocity=80), # HH_OPEN (Priority 5)
        ]
        
        processed = dg._apply_pro_features(impossible_notes)
        # Verify that only up to 2 hand-struck notes starting at 1.0 are kept
        hand_struck_at_1 = [n for n in processed if abs(n.start - 1.0) < 0.05 and n.pitch in {38, 49, 42, 46}]
        assert len(hand_struck_at_1) <= 2
        # Verify that higher priority notes (SNARE and CRASH) are preserved while lower priority are dropped
        preserved_pitches = {n.pitch for n in hand_struck_at_1}
        assert 38 in preserved_pitches
        assert 49 in preserved_pitches
        assert 42 not in preserved_pitches
        assert 46 not in preserved_pitches

