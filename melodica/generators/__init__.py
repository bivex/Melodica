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

"""
generators/__init__.py — PhraseGenerator base class, GeneratorParams, and freeze().

Layer: Application / Domain
Rules:
  - PhraseGenerator is an abstract base; no engine or infrastructure imports.
  - freeze() is a pure transformation: render → wrap in StaticPhrase.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from melodica.types import (
    ChordLabel,
    NoteInfo,
    PhraseInstance,
    Scale,
    StaticPhrase,
)
from melodica.render_context import RenderContext


# ---------------------------------------------------------------------------
# Shared generator parameters (modeled after tc_p fields)
# ---------------------------------------------------------------------------


@dataclass
class GeneratorParams:
    """Parameters shared by all phrase generators (tc_p block fields)."""

    density: float = 0.5  # 0–1: note density
    key_range_low: int = 48  # MIDI pitch lower bound
    key_range_high: int = 84  # MIDI pitch upper bound
    complexity: float = 0.5  # 0–1: melodic complexity
    leap_probability: float = 0.2  # 0–1: chance of interval > one step

    def __post_init__(self) -> None:
        for name, val in [
            ("density", self.density),
            ("complexity", self.complexity),
            ("leap_probability", self.leap_probability),
        ]:
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{name} must be 0–1, got {val}")
        if self.key_range_low >= self.key_range_high:
            raise ValueError("key_range_low must be < key_range_high")


# ---------------------------------------------------------------------------
# Abstract base class (matches PhraseGeneratorProtocol from types.py)
# ---------------------------------------------------------------------------


class PhraseGenerator(ABC):
    """
    Abstract phrase generator.
    Subclasses implement render() and set the `name` class attribute.
    """

    name: str
    params: GeneratorParams

    def __init__(self, params: GeneratorParams | None = None) -> None:
        super().__init__()
        self.params = params or GeneratorParams()

    @abstractmethod
    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]: ...


# ---------------------------------------------------------------------------
# freeze() — application service (pure transformation)
# ---------------------------------------------------------------------------


def freeze(
    instance: PhraseInstance,
    chords: list[ChordLabel],
    key: Scale,
    context: RenderContext | None = None,
) -> PhraseInstance:
    """
    Render a parametric PhraseInstance and return a new static one.
    Modeled after Melodica's Apply / Freeze button.

    The returned instance has generator=None and static=StaticPhrase(notes=...).
    Raises AssertionError if instance is already static.
    """
    if not instance.is_parametric():
        raise ValueError("freeze() called on a static PhraseInstance; nothing to render.")

    assert instance.generator is not None
    total_beats = max((c.end for c in chords), default=4.0)
    notes = instance.generator.render(chords, key, total_beats, context)
    return PhraseInstance(static=StaticPhrase(notes=notes))


from melodica.generators.melody import MelodyGenerator
from melodica.generators.chord_gen import ChordGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.fingerpicking import FingerpickingGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.strum import StrumPatternGenerator
from melodica.generators.piano_run import PianoRunGenerator
from melodica.generators.markov import MarkovMelodyGenerator
from melodica.generators.neural_melody import NeuralMelodyGenerator
from melodica.generators.dyads import DyadGenerator
from melodica.generators.staccato import StringsStaccatoGenerator
from melodica.generators.rest import RestGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.riff import RiffGenerator
from melodica.generators.step_seq import StepSequencer
from melodica.generators.canon import CanonGenerator
from melodica.generators.call_response import CallResponseGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.groove import GrooveGenerator
from melodica.generators.dyads_run import DyadsRunGenerator
from melodica.generators.generic_gen import GenericGenerator
from melodica.generators.modern_chord import ModernChordPatternGenerator
from melodica.generators.phrase_container import PhraseContainer
from melodica.generators.percussion import PercussionGenerator
from melodica.generators.phrase_morpher import PhraseMorpher
from melodica.generators.random_note import RandomNoteGenerator
from melodica.generators.motive import MotiveGenerator
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.alberti_bass import AlbertiBassGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.generators.sequence import SequenceGenerator
from melodica.generators.blues_lick import BluesLickGenerator
from melodica.generators.hocket import HocketGenerator
from melodica.generators.trill import TrillTremoloGenerator
from melodica.generators.ornamentation import OrnamentationGenerator
from melodica.generators.fills import FillGenerator
from melodica.generators.pickup import PickupGenerator
from melodica.generators.glissando import GlissandoGenerator
from melodica.generators.boogie_woogie import BoogieWoogieGenerator
from melodica.generators.stride_piano import StridePianoGenerator
from melodica.generators.tremolo_picking import TremoloPickingGenerator
from melodica.generators.tango import TangoGenerator
from melodica.generators.reggae_skank import ReggaeSkankGenerator
from melodica.generators.montuno import MontunoGenerator
from melodica.generators.acciaccatura import AcciaccaturaGenerator
from melodica.generators.ragtime import RagtimeGenerator
from melodica.generators.power_chord import PowerChordGenerator
from melodica.generators.broken_chord import BrokenChordGenerator
from melodica.generators.pedal_melody import PedalMelodyGenerator
from melodica.generators.beat_repeat import BeatRepeatGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.polyrhythm import PolyrhythmGenerator
from melodica.generators.waltz import WaltzGenerator
from melodica.generators.chorale import ChoraleGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.harmonics import HarmonicsGenerator
from melodica.generators.bend import BendGenerator
from melodica.generators.clusters import ClusterGenerator
from melodica.generators.cadence import CadenceGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.supersaw_pad import SupersawPadGenerator
from melodica.generators.pluck_sequence import PluckSequenceGenerator
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.sax_solo import SaxSoloGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.four_on_floor import FourOnFloorGenerator
from melodica.generators.breakbeat import BreakbeatGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.reharmonization import ReharmonizationGenerator
from melodica.generators.modal_interchange import ModalInterchangeGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.vocal_oohs import VocalOohsGenerator
from melodica.generators.guitar_legato import GuitarLegatoGenerator
from melodica.generators.guitar_tapping import GuitarTappingGenerator
from melodica.generators.arranger import ArrangerGenerator
from melodica.generators.humanizer import HumanizerGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.sidechain_pump import SidechainPumpGenerator
from melodica.generators.voice_leading import VoiceLeadingGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.motif_development import MotifDevelopmentGenerator
from melodica.generators.filter_sweep import FilterSweepGenerator
from melodica.generators.euclidean_rhythm import EuclideanRhythmGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.organ_drawbars import OrganDrawbarsGenerator
from melodica.generators.keys_arpeggio import KeysArpeggioGenerator
from melodica.generators.guitar_strumming import GuitarStrummingGenerator
from melodica.generators.bass_slap import BassSlapGenerator
from melodica.generators.guitar_sweep import GuitarSweepGenerator
from melodica.generators.vocal_melisma import VocalMelismaGenerator
from melodica.generators.vocal_adlibs import VocalAdlibsGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.percussion_ensemble import PercussionEnsembleGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator
from melodica.generators.bass_wobble import BassWobbleGenerator
from melodica.generators.hemiola import HemiolaGenerator
from melodica.generators.backbeat import BackbeatGenerator
from melodica.generators.downbeat_rest import DownbeatRestGenerator
from melodica.generators.chord_voicing import ChordVoicingGenerator
from melodica.generators.dynamics import DynamicsCurveGenerator
from melodica.generators.secondary_dominant import SecondaryDominantGenerator
from melodica.generators.section_builder import SectionBuilderGenerator
from melodica.generators.transition import TransitionGenerator
from melodica.generators.swing import SwingGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.tension import TensionGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.drill_pattern import DrillPatternGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.lofi_hiphop import LoFiHipHopGenerator
from melodica.generators.afrobeats import AfrobeatsGenerator
from melodica.generators.phonk import PhonkGenerator
from melodica.generators.melodic_rap import MelodicRapGenerator
from melodica.generators.uk_garage import UKGarageGenerator
from melodica.generators.hyperpop import HyperpopGenerator
from melodica.generators.advanced_step_seq import AdvancedStepSequencer
from melodica.generators.bpm_adaptive import BPMAdaptiveGenerator
from melodica.generators.genre_fusion import GenreFusionEngine
from melodica.generators.vocal_melody_auto import VocalMelodyAutoGenerator
from melodica.generators.jersey_club import JerseyClubGenerator
from melodica.generators.dembow import DembowGenerator
from melodica.generators.baile_funk import BaileFunkGenerator
from melodica.generators.rage_beat import RageBeatGenerator
from melodica.generators.pluggnb import PluggnbGenerator
from melodica.generators.latin_trap import LatinTrapGenerator
from melodica.generators.cloud_rap import CloudRapGenerator
from melodica.generators.dnb_jungle import DnBJungleGenerator
from melodica.generators.hardstyle import HardstyleGenerator
from melodica.generators.synthwave import SynthwaveGenerator
from melodica.generators.boom_bap import BoomBapGenerator
from melodica.generators.future_bass import FutureBassGenerator
from melodica.generators.grime import GrimeGenerator
from melodica.generators.witch_house import WitchHouseGenerator
from melodica.generators.phonk_house import PhonkHouseGenerator
from melodica.generators.amapiano_logdrum import AmapianoLogDrumGenerator
from melodica.generators.afro_percussion import AfroPercussionGenerator
from melodica.generators.highlife_guitar import HighlifeGuitarGenerator
from melodica.generators.afro_house import AfroHouseGenerator
from melodica.generators.gqom import GqomGenerator
from melodica.generators.kuduro import KuduroGenerator
from melodica.generators.afro_drill import AfroDrillGenerator
from melodica.generators.soukous_guitar import SoukousGuitarGenerator
from melodica.generators.bongo_flava import BongoFlavaGenerator
from melodica.generators.afro_samba import AfroSambaGenerator
from melodica.generators.combat_escalation import CombatEscalationGenerator
from melodica.generators.stinger import StingerGenerator
from melodica.generators.chiptune import ChiptuneGenerator
from melodica.generators.horror_dissonance import HorrorDissonanceGenerator
from melodica.generators.stealth_state import StealthStateGenerator
from melodica.generators.procedural_exploration import ProceduralExplorationGenerator
from melodica.generators.boss_battle import BossBattleGenerator
from melodica.generators.puzzle_loop import PuzzleLoopGenerator
from melodica.generators.medieval_tavern import MedievalTavernGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator
from melodica.generators.victory_fanfare import VictoryFanfareGenerator

__all__ = [
    "PhraseGenerator",
    "GeneratorParams",
    "RenderContext",
    "freeze",
    "MelodyGenerator",
    "ChordGenerator",
    "ArpeggiatorGenerator",
    "BassGenerator",
    "FingerpickingGenerator",
    "OstinatoGenerator",
    "StrumPatternGenerator",
    "PianoRunGenerator",
    "MarkovMelodyGenerator",
    "NeuralMelodyGenerator",
    "DyadGenerator",
    "StringsStaccatoGenerator",
    "RestGenerator",
    "AmbientPadGenerator",
    "RiffGenerator",
    "StepSequencer",
    "CanonGenerator",
    "CallResponseGenerator",
    "PedalBassGenerator",
    "GrooveGenerator",
    "DyadsRunGenerator",
    "GenericGenerator",
    "ModernChordPatternGenerator",
    "PhraseContainer",
    "PercussionGenerator",
    "PhraseMorpher",
    "RandomNoteGenerator",
    "MotiveGenerator",
    "WalkingBassGenerator",
    "AlbertiBassGenerator",
    "DroneGenerator",
    "CountermelodyGenerator",
    "SequenceGenerator",
    "BluesLickGenerator",
    "HocketGenerator",
    "TrillTremoloGenerator",
    "OrnamentationGenerator",
    "FillGenerator",
    "PickupGenerator",
    "GlissandoGenerator",
    "BoogieWoogieGenerator",
    "StridePianoGenerator",
    "TremoloPickingGenerator",
    "TangoGenerator",
    "ReggaeSkankGenerator",
    "MontunoGenerator",
    "AcciaccaturaGenerator",
    "RagtimeGenerator",
    "PowerChordGenerator",
    "BrokenChordGenerator",
    "PedalMelodyGenerator",
    "BeatRepeatGenerator",
    "TremoloStringsGenerator",
    "PolyrhythmGenerator",
    "WaltzGenerator",
    "ChoraleGenerator",
    "NebulaGenerator",
    "HarmonicsGenerator",
    "BendGenerator",
    "ClusterGenerator",
    "CadenceGenerator",
    "SynthBassGenerator",
    "SupersawPadGenerator",
    "PluckSequenceGenerator",
    "StringsLegatoGenerator",
    "StringsPizzicatoGenerator",
    "BrassSectionGenerator",
    "SaxSoloGenerator",
    "TrapDrumsGenerator",
    "FourOnFloorGenerator",
    "BreakbeatGenerator",
    "FXRiserGenerator",
    "FXImpactGenerator",
    "ReharmonizationGenerator",
    "ModalInterchangeGenerator",
    "VocalChopsGenerator",
    "VocalOohsGenerator",
    "GuitarLegatoGenerator",
    "GuitarTappingGenerator",
    "ArrangerGenerator",
    "HumanizerGenerator",
    "LeadSynthGenerator",
    "SidechainPumpGenerator",
    "VoiceLeadingGenerator",
    "CounterpointGenerator",
    "MotifDevelopmentGenerator",
    "FilterSweepGenerator",
    "EuclideanRhythmGenerator",
    "PianoCompGenerator",
    "OrganDrawbarsGenerator",
    "KeysArpeggioGenerator",
    "GuitarStrummingGenerator",
    "BassSlapGenerator",
    "GuitarSweepGenerator",
    "VocalMelismaGenerator",
    "VocalAdlibsGenerator",
    "ChoirAahsGenerator",
    "DrumKitPatternGenerator",
    "PercussionEnsembleGenerator",
    "ElectronicDrumsGenerator",
    "WoodwindsEnsembleGenerator",
    "StringsEnsembleGenerator",
    "OrchestralHitGenerator",
    "BassWobbleGenerator",
    "HemiolaGenerator",
    "BackbeatGenerator",
    "DownbeatRestGenerator",
    "ChordVoicingGenerator",
    "DynamicsCurveGenerator",
    "SecondaryDominantGenerator",
    "SectionBuilderGenerator",
    "TransitionGenerator",
    "SwingGenerator",
    "DarkPadGenerator",
    "TensionGenerator",
    "DarkBassGenerator",
    "Bass808SlidingGenerator",
    "HiHatStutterGenerator",
    "DrillPatternGenerator",
    "GhostNotesGenerator",
    "LoFiHipHopGenerator",
    "AfrobeatsGenerator",
    "PhonkGenerator",
    "MelodicRapGenerator",
    "UKGarageGenerator",
    "HyperpopGenerator",
    "AdvancedStepSequencer",
    "BPMAdaptiveGenerator",
    "GenreFusionEngine",
    "VocalMelodyAutoGenerator",
    "JerseyClubGenerator",
    "DembowGenerator",
    "BaileFunkGenerator",
    "RageBeatGenerator",
    "PluggnbGenerator",
    "LatinTrapGenerator",
    "CloudRapGenerator",
    "DnBJungleGenerator",
    "HardstyleGenerator",
    "SynthwaveGenerator",
    "BoomBapGenerator",
    "FutureBassGenerator",
    "GrimeGenerator",
    "WitchHouseGenerator",
    "PhonkHouseGenerator",
    "AmapianoLogDrumGenerator",
    "AfroPercussionGenerator",
    "HighlifeGuitarGenerator",
    "AfroHouseGenerator",
    "GqomGenerator",
    "KuduroGenerator",
    "AfroDrillGenerator",
    "SoukousGuitarGenerator",
    "BongoFlavaGenerator",
    "AfroSambaGenerator",
    "CombatEscalationGenerator",
    "StingerGenerator",
    "ChiptuneGenerator",
    "HorrorDissonanceGenerator",
    "StealthStateGenerator",
    "ProceduralExplorationGenerator",
    "BossBattleGenerator",
    "PuzzleLoopGenerator",
    "MedievalTavernGenerator",
    "SciFiUnderscoreGenerator",
    "VictoryFanfareGenerator",
]
