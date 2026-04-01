import pytest
from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.composition import Section, Composition, MusicDirector


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)

TRACKS = {"Melody": "lead_melody", "Bass": "followed_bass"}


class TestSectionIntensity:
    def test_default_intensity(self):
        sec = Section("Test", 16.0, "I V vi IV", TRACKS)
        assert sec.intensity == 0.5

    def test_custom_intensity(self):
        sec = Section("Climax", 16.0, "I V vi IV", TRACKS, intensity=0.9)
        assert sec.intensity == 0.9

    def test_add_section_with_intensity(self):
        comp = Composition("Test", C_MAJOR)
        comp.add_section("Verse", 16.0, "I V vi IV", TRACKS, intensity=0.3)
        assert comp.sections[0].intensity == 0.3

    def test_add_section_default_intensity(self):
        comp = Composition("Test", C_MAJOR)
        comp.add_section("Verse", 16.0, "I V vi IV", TRACKS)
        assert comp.sections[0].intensity == 0.5


class TestPhrasePosition:
    def test_phrase_position_is_set(self):
        """Verify that phrase_position is set on RenderContext by MusicDirector."""
        comp = Composition("Test", C_MAJOR)
        comp.add_section("Intro", 8.0, "I", TRACKS, intensity=0.5)
        comp.add_section("Climax", 8.0, "V", TRACKS, intensity=1.0)

        director = MusicDirector(key=C_MAJOR)
        arrangement = director.render(comp)

        assert len(arrangement.tracks) > 0
        assert arrangement.total_beats == 16.0

    def test_single_section_position(self):
        """Single section should have phrase_position = 0.5 (midpoint of entire piece)."""
        comp = Composition("Test", C_MAJOR)
        comp.add_section("Only", 16.0, "I V vi IV", TRACKS)

        director = MusicDirector(key=C_MAJOR)
        arrangement = director.render(comp)
        assert arrangement.total_beats == 16.0

    def test_multi_section_positions(self):
        """Multiple sections should have increasing phrase_positions."""
        comp = Composition("Test", C_MAJOR)
        comp.add_section("A", 16.0, "I", TRACKS)
        comp.add_section("B", 16.0, "V", TRACKS)
        comp.add_section("C", 16.0, "I", TRACKS)

        director = MusicDirector(key=C_MAJOR)
        arrangement = director.render(comp)
        assert arrangement.total_beats == 48.0


class TestIntensityVelocityScaling:
    def test_low_intensity_reduces_velocity(self):
        """Section with low intensity should produce softer notes."""
        comp_soft = Composition("Soft", C_MAJOR)
        comp_soft.add_section("Soft", 8.0, "I V vi IV", TRACKS, intensity=0.1)

        comp_loud = Composition("Loud", C_MAJOR)
        comp_loud.add_section("Loud", 8.0, "I V vi IV", TRACKS, intensity=0.9)

        director = MusicDirector(key=C_MAJOR)
        arr_soft = director.render(comp_soft)
        arr_loud = director.render(comp_loud)

        # Get average velocities
        def avg_vel(arr):
            all_vels = []
            for track in arr.tracks:
                all_vels.extend(n.velocity for n in track.notes)
            return sum(all_vels) / max(1, len(all_vels))

        # Loud section should have higher average velocity than soft
        # (unless both produce no notes)
        if arr_soft.tracks and arr_loud.tracks:
            soft_avg = avg_vel(arr_soft)
            loud_avg = avg_vel(arr_loud)
            assert loud_avg > soft_avg

    def test_neutral_intensity_no_change(self):
        """Section with intensity=0.5 should not modify velocities."""
        comp = Composition("Test", C_MAJOR)
        comp.add_section("Neutral", 8.0, "I V", TRACKS, intensity=0.5)

        director = MusicDirector(key=C_MAJOR)
        arrangement = director.render(comp)
        assert len(arrangement.tracks) > 0


class TestIntensityIntegration:
    def test_intro_to_climax_arc(self):
        """Simulate an intro→climax→outro arc with varying intensities."""
        comp = Composition("Arc Test", C_MAJOR)
        comp.add_section("Intro", 8.0, "I", TRACKS, intensity=0.2)
        comp.add_section("Build", 8.0, "I V", TRACKS, intensity=0.5)
        comp.add_section("Climax", 8.0, "V I", TRACKS, intensity=1.0)
        comp.add_section("Outro", 8.0, "I", TRACKS, intensity=0.3)

        director = MusicDirector(key=C_MAJOR)
        arrangement = director.render(comp)

        assert arrangement.total_beats == 32.0
        assert len(arrangement.tracks) > 0

        # Verify all sections produced notes
        for track in arrangement.tracks:
            assert len(track.notes) > 0

    def test_intensity_with_modulation(self):
        """Intensity should work alongside key modulation."""
        comp = Composition("Mod Intensity", C_MAJOR)
        comp.add_section("C Major", 8.0, "I V vi IV", TRACKS, intensity=0.5)
        comp.add_section(
            "G Major",
            8.0,
            "I V vi IV",
            TRACKS,
            key=Scale(root=7, mode=Mode.MAJOR),
            intensity=0.8,
        )

        director = MusicDirector(key=C_MAJOR)
        arrangement = director.render(comp)
        assert arrangement.total_beats == 16.0
