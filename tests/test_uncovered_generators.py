"""Tests for 47 generators not covered by existing test files."""

import pytest

from melodica.types import ChordLabel, Quality, Scale, Mode, NoteInfo
from melodica.generators import GeneratorParams

# --- Uncovered generators ---
from melodica.generators.afrobeats import AfrobeatsGenerator
from melodica.generators.afro_drill import AfroDrillGenerator
from melodica.generators.afro_house import AfroHouseGenerator
from melodica.generators.afro_percussion import AfroPercussionGenerator
from melodica.generators.afro_samba import AfroSambaGenerator
from melodica.generators.amapiano_logdrum import AmapianoLogDrumGenerator
from melodica.generators.baile_funk import BaileFunkGenerator
from melodica.generators.bongo_flava import BongoFlavaGenerator
from melodica.generators.boom_bap import BoomBapGenerator
from melodica.generators.boss_battle import BossBattleGenerator
from melodica.generators.bpm_adaptive import BPMAdaptiveGenerator
from melodica.generators.chiptune import ChiptuneGenerator
from melodica.generators.cloud_rap import CloudRapGenerator
from melodica.generators.combat_escalation import CombatEscalationGenerator
from melodica.generators.dembow import DembowGenerator
from melodica.generators.dnb_jungle import DnBJungleGenerator
from melodica.generators.drill_pattern import DrillPatternGenerator
from melodica.generators.future_bass import FutureBassGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.gqom import GqomGenerator
from melodica.generators.grime import GrimeGenerator
from melodica.generators.hardstyle import HardstyleGenerator
from melodica.generators.highlife_guitar import HighlifeGuitarGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.hyperpop import HyperpopGenerator
from melodica.generators.jersey_club import JerseyClubGenerator
from melodica.generators.kuduro import KuduroGenerator
from melodica.generators.latin_trap import LatinTrapGenerator
from melodica.generators.lofi_hiphop import LoFiHipHopGenerator
from melodica.generators.medieval_tavern import MedievalTavernGenerator
from melodica.generators.melodic_rap import MelodicRapGenerator
from melodica.generators.phonk import PhonkGenerator
from melodica.generators.phonk_house import PhonkHouseGenerator
from melodica.generators.pluggnb import PluggnbGenerator
from melodica.generators.procedural_exploration import ProceduralExplorationGenerator
from melodica.generators.puzzle_loop import PuzzleLoopGenerator
from melodica.generators.rage_beat import RageBeatGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.soukous_guitar import SoukousGuitarGenerator
from melodica.generators.stealth_state import StealthStateGenerator
from melodica.generators.stinger import StingerGenerator
from melodica.generators.synthwave import SynthwaveGenerator
from melodica.generators.uk_garage import UKGarageGenerator
from melodica.generators.victory_fanfare import VictoryFanfareGenerator
from melodica.generators.vocal_melody_auto import VocalMelodyAutoGenerator
from melodica.generators.witch_house import WitchHouseGenerator


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)
F_SHARP_MINOR = Scale(root=6, mode=Mode.NATURAL_MINOR)


def _chords() -> list[ChordLabel]:
    return [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0),
    ]


def _one_chord() -> list[ChordLabel]:
    return [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]


def _valid(notes: list[NoteInfo]) -> None:
    for n in notes:
        assert 0 <= n.pitch <= 127, f"pitch {n.pitch} out of range"
        assert n.duration > 0, f"duration {n.duration} not positive"
        assert n.start >= 0, f"start {n.start} negative"
        assert 1 <= n.velocity <= 127, f"velocity {n.velocity} out of range"


# =====================================================================
# Afro / Latin
# =====================================================================

class TestAfrobeatsGenerator:
    def test_produces_notes(self):
        notes = AfrobeatsGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_empty_chords(self):
        assert AfrobeatsGenerator().render([], C_MAJOR, 8.0) == []

    def test_no_piano(self):
        notes = AfrobeatsGenerator(include_piano=False).render(_chords(), C_MAJOR, 8.0)
        assert isinstance(notes, list)

    def test_variant(self):
        notes = AfrobeatsGenerator(variant="afrobeats").render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestAfroDrillGenerator:
    def test_produces_notes(self):
        notes = AfroDrillGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_empty_chords(self):
        assert AfroDrillGenerator().render([], A_MINOR, 8.0) == []


class TestAfroHouseGenerator:
    def test_produces_notes(self):
        notes = AfroHouseGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_marimba(self):
        notes = AfroHouseGenerator(include_marimba=False).render(_chords(), C_MAJOR, 8.0)
        assert isinstance(notes, list)


class TestAfroPercussionGenerator:
    def test_produces_notes(self):
        notes = AfroPercussionGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_pitched(self):
        notes = AfroPercussionGenerator(include_pitched=False).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestAfroSambaGenerator:
    def test_produces_notes(self):
        notes = AfroSambaGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_guitar(self):
        notes = AfroSambaGenerator(include_guitar=False).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestAmapianoLogDrumGenerator:
    def test_produces_notes(self):
        notes = AmapianoLogDrumGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_empty_chords(self):
        assert AmapianoLogDrumGenerator().render([], C_MAJOR, 8.0) == []


class TestBaileFunkGenerator:
    def test_produces_notes(self):
        notes = BaileFunkGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_mc_chops(self):
        notes = BaileFunkGenerator(mc_chops=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


class TestBongoFlavaGenerator:
    def test_produces_notes(self):
        notes = BongoFlavaGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_percussion(self):
        notes = BongoFlavaGenerator(include_percussion=False).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestDembowGenerator:
    def test_produces_notes(self):
        notes = DembowGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_bass(self):
        notes = DembowGenerator(include_bass=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


class TestGqomGenerator:
    def test_produces_notes(self):
        notes = GqomGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_vocal_stabs(self):
        notes = GqomGenerator(include_vocal_stabs=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


class TestKuduroGenerator:
    def test_produces_notes(self):
        notes = KuduroGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_empty_chords(self):
        assert KuduroGenerator().render([], A_MINOR, 8.0) == []


class TestLatinTrapGenerator:
    def test_produces_notes(self):
        notes = LatinTrapGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_percussion(self):
        notes = LatinTrapGenerator(include_percussion=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


class TestJerseyClubGenerator:
    def test_produces_notes(self):
        notes = JerseyClubGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_stutter(self):
        notes = JerseyClubGenerator(stutter_breaks=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


class TestHighlifeGuitarGenerator:
    def test_produces_notes(self):
        notes = HighlifeGuitarGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_octave_doubling(self):
        notes = HighlifeGuitarGenerator(octave_doubling=False).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestSoukousGuitarGenerator:
    def test_produces_notes(self):
        notes = SoukousGuitarGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_empty_chords(self):
        assert SoukousGuitarGenerator().render([], C_MAJOR, 8.0) == []


# =====================================================================
# Electronic / Dance
# =====================================================================

class TestSynthwaveGenerator:
    def test_produces_notes(self):
        notes = SynthwaveGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_gated_pads(self):
        notes = SynthwaveGenerator(gated_pads=False).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)

    def test_no_lead(self):
        notes = SynthwaveGenerator(include_lead=False).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestFutureBassGenerator:
    def test_produces_notes(self):
        notes = FutureBassGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_vocal_chops(self):
        notes = FutureBassGenerator(include_vocal_chops=False).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestDnBJungleGenerator:
    def test_produces_notes(self):
        notes = DnBJungleGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)


class TestHardstyleGenerator:
    def test_produces_notes(self):
        notes = HardstyleGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_lead(self):
        notes = HardstyleGenerator(include_lead=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


class TestHyperpopGenerator:
    def test_produces_notes(self):
        notes = HyperpopGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_leads(self):
        notes = HyperpopGenerator(include_leads=False).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestLoFiHipHopGenerator:
    def test_produces_notes(self):
        notes = LoFiHipHopGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_drums(self):
        notes = LoFiHipHopGenerator(include_drums=False).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)

    def test_no_bass(self):
        notes = LoFiHipHopGenerator(include_bass=False).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestChiptuneGenerator:
    def test_produces_notes(self):
        notes = ChiptuneGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_custom_channels(self):
        notes = ChiptuneGenerator(channels=["pulse1", "triangle"]).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestWitchHouseGenerator:
    def test_produces_notes(self):
        notes = WitchHouseGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_empty_chords(self):
        assert WitchHouseGenerator().render([], A_MINOR, 8.0) == []


class TestUKGarageGenerator:
    def test_produces_notes(self):
        notes = UKGarageGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_stabs(self):
        notes = UKGarageGenerator(include_stabs=False).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


# =====================================================================
# Hip-Hop / Trap
# =====================================================================

class TestMelodicRapGenerator:
    def test_produces_notes(self):
        notes = MelodicRapGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)


class TestCloudRapGenerator:
    def test_produces_notes(self):
        notes = CloudRapGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)


class TestDrillPatternGenerator:
    def test_produces_notes(self):
        notes = DrillPatternGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_piano(self):
        notes = DrillPatternGenerator(include_piano=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


class TestRageBeatGenerator:
    def test_produces_notes(self):
        notes = RageBeatGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_synth_lead(self):
        notes = RageBeatGenerator(include_synth_lead=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


class TestPhonkGenerator:
    def test_produces_notes(self):
        notes = PhonkGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_memphis_chops(self):
        notes = PhonkGenerator(memphis_chops=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


class TestPhonkHouseGenerator:
    def test_produces_notes(self):
        notes = PhonkHouseGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_bass_slides(self):
        notes = PhonkHouseGenerator(bass_slides=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


class TestPluggnbGenerator:
    def test_produces_notes(self):
        notes = PluggnbGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_808(self):
        notes = PluggnbGenerator(include_808=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


class TestBoomBapGenerator:
    def test_produces_notes(self):
        notes = BoomBapGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_ghost_snares(self):
        notes = BoomBapGenerator(ghost_snares=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


# =====================================================================
# Cinematic / Game
# =====================================================================

class TestBossBattleGenerator:
    def test_produces_notes(self):
        notes = BossBattleGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_choir(self):
        notes = BossBattleGenerator(choir_stabs=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


class TestCombatEscalationGenerator:
    def test_produces_notes(self):
        notes = CombatEscalationGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)


class TestStealthStateGenerator:
    def test_produces_notes(self):
        notes = StealthStateGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_empty_chords(self):
        assert StealthStateGenerator().render([], A_MINOR, 8.0) == []

    def test_alert_state(self):
        notes = StealthStateGenerator(stealth_state="alert").render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


class TestVictoryFanfareGenerator:
    def test_produces_notes(self):
        notes = VictoryFanfareGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)


class TestMedievalTavernGenerator:
    def test_produces_notes(self):
        notes = MedievalTavernGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_flute(self):
        notes = MedievalTavernGenerator(include_flute=False).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestSciFiUnderscoreGenerator:
    def test_produces_notes(self):
        notes = SciFiUnderscoreGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_bass_synth(self):
        notes = SciFiUnderscoreGenerator(include_bass_synth=False).render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)


# =====================================================================
# Utility / Meta
# =====================================================================

class TestBPMAdaptiveGenerator:
    def test_produces_notes(self):
        notes = BPMAdaptiveGenerator(bpm=140.0).render(_chords(), C_MAJOR, 8.0)
        assert isinstance(notes, list)

    def test_wraps_generator(self):
        from melodica.generators.drone import DroneGenerator
        notes = BPMAdaptiveGenerator(
            wrapped_generator=DroneGenerator(), bpm=160.0
        ).render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestProceduralExplorationGenerator:
    def test_produces_notes(self):
        notes = ProceduralExplorationGenerator().render(_chords(), C_MAJOR, 8.0)
        assert isinstance(notes, list)

    def test_variant(self):
        notes = ProceduralExplorationGenerator(variant="underwater").render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestPuzzleLoopGenerator:
    def test_produces_notes(self):
        notes = PuzzleLoopGenerator().render(_chords(), C_MAJOR, 8.0)
        assert isinstance(notes, list)


class TestStingerGenerator:
    def test_produces_notes(self):
        notes = StingerGenerator().render(_one_chord(), C_MAJOR, 4.0)
        assert isinstance(notes, list)

    def test_empty_chords(self):
        notes = StingerGenerator().render([], C_MAJOR, 4.0)
        assert isinstance(notes, list)


# =====================================================================
# Other
# =====================================================================

class TestGhostNotesGenerator:
    def test_produces_notes(self):
        notes = GhostNotesGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_ghost_velocity_low(self):
        notes = GhostNotesGenerator(ghost_velocity=20).render(_chords(), C_MAJOR, 4.0)
        for n in notes:
            assert n.velocity <= 60


class TestHiHatStutterGenerator:
    def test_produces_notes(self):
        notes = HiHatStutterGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_pattern(self):
        notes = HiHatStutterGenerator(pattern="trap_sixteenth").render(_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestVocalMelodyAutoGenerator:
    def test_produces_notes(self):
        notes = VocalMelodyAutoGenerator().render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        _valid(notes)


class TestSoloMelodyGenerator:
    def test_produces_notes(self):
        notes = SoloMelodyGenerator().render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_style_neo_soul(self):
        notes = SoloMelodyGenerator(style="neo_soul_keys").render(_chords(), A_MINOR, 4.0)
        assert isinstance(notes, list)

    def test_invalid_style_raises(self):
        with pytest.raises(ValueError):
            SoloMelodyGenerator(style="nonexistent")
