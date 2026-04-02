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
factory.py — Generator factory and variation applicator.

Extracted from idea_tool.py to keep that module under control.
"""

from __future__ import annotations

import random
from typing import Any

from melodica.types import NoteInfo
from melodica.generators import (
    MelodyGenerator,
    ArpeggiatorGenerator,
    BassGenerator,
    ChordGenerator,
    OstinatoGenerator,
    StrumPatternGenerator,
    FingerpickingGenerator,
    RiffGenerator,
    GrooveGenerator,
    PercussionGenerator,
    PianoRunGenerator,
    GeneratorParams,
    MarkovMelodyGenerator,
    NeuralMelodyGenerator,
    DyadGenerator,
    AmbientPadGenerator,
    CanonGenerator,
    CallResponseGenerator,
    ModernChordPatternGenerator,
    WalkingBassGenerator,
    AlbertiBassGenerator,
    DroneGenerator,
    CountermelodyGenerator,
    SequenceGenerator,
    BluesLickGenerator,
    HocketGenerator,
    TrillTremoloGenerator,
    OrnamentationGenerator,
    FillGenerator,
    PickupGenerator,
    GlissandoGenerator,
    BoogieWoogieGenerator,
    StridePianoGenerator,
    TremoloPickingGenerator,
    TangoGenerator,
    ReggaeSkankGenerator,
    MontunoGenerator,
    AcciaccaturaGenerator,
    PedalBassGenerator,
    RagtimeGenerator,
    PowerChordGenerator,
    BrokenChordGenerator,
    PedalMelodyGenerator,
    BeatRepeatGenerator,
    TremoloStringsGenerator,
    PolyrhythmGenerator,
    WaltzGenerator,
    ChoraleGenerator,
    NebulaGenerator,
    HarmonicsGenerator,
    BendGenerator,
    ClusterGenerator,
    CadenceGenerator,
    SynthBassGenerator,
    SupersawPadGenerator,
    PluckSequenceGenerator,
    StringsLegatoGenerator,
    StringsPizzicatoGenerator,
    BrassSectionGenerator,
    SaxSoloGenerator,
    TrapDrumsGenerator,
    FourOnFloorGenerator,
    BreakbeatGenerator,
    FXRiserGenerator,
    FXImpactGenerator,
    ReharmonizationGenerator,
    ModalInterchangeGenerator,
    VocalChopsGenerator,
    VocalOohsGenerator,
    GuitarLegatoGenerator,
    GuitarTappingGenerator,
    ArrangerGenerator,
    HumanizerGenerator,
    PianoCompGenerator,
    OrganDrawbarsGenerator,
    KeysArpeggioGenerator,
    GuitarStrummingGenerator,
    BassSlapGenerator,
    GuitarSweepGenerator,
    VocalMelismaGenerator,
    VocalAdlibsGenerator,
    ChoirAahsGenerator,
    DrumKitPatternGenerator,
    PercussionEnsembleGenerator,
    ElectronicDrumsGenerator,
    WoodwindsEnsembleGenerator,
    StringsEnsembleGenerator,
    OrchestralHitGenerator,
    LeadSynthGenerator,
    SidechainPumpGenerator,
    VoiceLeadingGenerator,
    CounterpointGenerator,
    MotifDevelopmentGenerator,
    FilterSweepGenerator,
    EuclideanRhythmGenerator,
    BassWobbleGenerator,
)
from melodica.generators.rest import RestGenerator
from melodica.generators.step_seq import StepSequencer
from melodica.generators.dyads_run import DyadsRunGenerator
from melodica.generators.generic_gen import GenericGenerator
from melodica.generators.phrase_container import PhraseContainer
from melodica.generators.phrase_morpher import PhraseMorpher
from melodica.generators.random_note import RandomNoteGenerator
from melodica.generators.motive import MotiveGenerator
from melodica.generators.staccato import StringsStaccatoGenerator
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


def create_generator(
    generator_type: str,
    params: GeneratorParams,
    cfg_params: dict[str, Any],
):
    """Create a generator instance based on type string and config params."""

    p = cfg_params

    _GENERATOR_MAP: dict[str, Any] = {
        "melody": lambda: MelodyGenerator(
            params=params,
            harmony_note_probability=p.get("harmony_note_probability", 0.64),
            note_range_low=p.get("note_range_low"),
            note_range_high=p.get("note_range_high"),
        ),
        "arpeggiator": lambda: ArpeggiatorGenerator(
            params=params,
            pattern=p.get("pattern", "up"),
            note_duration=p.get("note_duration", 0.25),
        ),
        "bass": lambda: BassGenerator(
            params=params,
            allowed_notes=p.get("allowed_notes", ["root", "fourth"]),
            global_movement=p.get("global_movement", "none"),
            note_movement=p.get("note_movement", "alternating"),
        ),
        "chord": lambda: ChordGenerator(
            params=params,
            voicing=p.get("voicing", "open"),
        ),
        "ostinato": lambda: OstinatoGenerator(
            params=params,
            pattern=p.get("pattern", "1-3-5-3"),
        ),
        "strum": lambda: StrumPatternGenerator(
            params=params,
            voicing=p.get("voicing", "guitar"),
            pattern_name=p.get("pattern_name", "folk"),
        ),
        "percussion": lambda: PercussionGenerator(
            params=params,
            pattern_name=p.get("pattern_name", "rock"),
        ),
        "riff": lambda: RiffGenerator(
            params=params,
            scale_type=p.get("scale_type", "minor_pent"),
            riff_pattern=p.get("riff_pattern", "gallop"),
        ),
        "groove": lambda: GrooveGenerator(
            params=params,
            groove_pattern=p.get("groove_pattern", "funk_1"),
        ),
        "piano_run": lambda: PianoRunGenerator(
            params=params,
            technique=p.get("technique", "straddle"),
            notes_per_run=p.get("notes_per_run", 8),
        ),
        "markov": lambda: MarkovMelodyGenerator(
            params=params,
            note_repetition_probability=p.get("note_repetition_probability", 0.14),
            harmony_note_probability=p.get("harmony_note_probability", 0.64),
            direction_bias=p.get("direction_bias", 0.0),
        ),
        "neural": lambda: NeuralMelodyGenerator(
            params=params,
            model_path=p.get("model_path"),
            temperature=p.get("temperature", 1.0),
            top_p=p.get("top_p", 0.92),
            harmony_prob=p.get("harmony_prob", 0.55),
            direction_bias=p.get("direction_bias", 0.0),
            note_range_low=p.get("note_range_low"),
            note_range_high=p.get("note_range_high"),
            device=p.get("device", "cpu"),
        ),
        "dyads": lambda: DyadGenerator(
            params=params,
            interval_pref=p.get("interval_pref", [3, 4, 7]),
            motion_mode=p.get("motion_mode", "parallel"),
        ),
        "ambient": lambda: AmbientPadGenerator(
            params=params,
            voicing=p.get("voicing", "spread"),
            overlap=p.get("overlap", 0.5),
        ),
        "canon": lambda: CanonGenerator(
            params=params,
            delay_beats=p.get("delay_beats", 2.0),
            interval=p.get("interval", 7),
        ),
        "call_response": lambda: CallResponseGenerator(
            params=params,
            call_length=p.get("call_length", 2.0),
            response_length=p.get("response_length", 2.0),
        ),
        "modern_chord": lambda: ModernChordPatternGenerator(
            params=params,
            stab_pattern=p.get("stab_pattern", "syncopated"),
        ),
        "fingerpicking": lambda: FingerpickingGenerator(
            params=params,
            pattern=p.get("pattern", [0, 2, 1, 3]),
        ),
        "walking_bass": lambda: WalkingBassGenerator(
            params=params,
            approach_style=p.get("approach_style", "mixed"),
            connect_roots=p.get("connect_roots", True),
            add_chromatic_passing=p.get("add_chromatic_passing", True),
        ),
        "alberti_bass": lambda: AlbertiBassGenerator(
            params=params,
            pattern=p.get("pattern", "1-5-3-5"),
            subdivision=p.get("subdivision", 0.5),
            voice_lead=p.get("voice_lead", True),
        ),
        "drone": lambda: DroneGenerator(
            params=params,
            variant=p.get("variant", "tonic"),
            fade_in=p.get("fade_in", 0.0),
            fade_out=p.get("fade_out", 0.0),
            retrigger_on_chord=p.get("retrigger_on_chord", True),
        ),
        "countermelody": lambda: CountermelodyGenerator(
            params=params,
            primary_melody=p.get("primary_melody"),
            motion_preference=p.get("motion_preference", "mixed"),
            dissonance_on_weak=p.get("dissonance_on_weak", True),
            interval_limit=p.get("interval_limit", 7),
        ),
        "sequence": lambda: SequenceGenerator(
            params=params,
            motif_length=p.get("motif_length", 4),
            sequence_type=p.get("sequence_type", "descending"),
            interval_steps=p.get("interval_steps", 1),
            repetitions=p.get("repetitions", 0),
            generate_motif=p.get("generate_motif", True),
            motif_notes=p.get("motif_notes"),
        ),
        "blues_lick": lambda: BluesLickGenerator(
            params=params,
            lick_style=p.get("lick_style", "standard"),
            phrase_length=p.get("phrase_length", 4),
            rest_probability=p.get("rest_probability", 0.3),
            enclosure_probability=p.get("enclosure_probability", 0.2),
            bend_probability=p.get("bend_probability", 0.15),
        ),
        "hocket": lambda: HocketGenerator(
            params=params,
            hocket_pattern=p.get("hocket_pattern", "alternating"),
            voice_index=p.get("voice_index", 0),
            euclidean_pulses=p.get("euclidean_pulses", 3),
            euclidean_steps=p.get("euclidean_steps", 4),
        ),
        "trill": lambda: TrillTremoloGenerator(
            params=params,
            ornament_type=p.get("ornament_type", generator_type),
            speed=p.get("speed", 0.125),
            base_note_strategy=p.get("base_note_strategy", "chord_tone"),
            neighbor_interval=p.get("neighbor_interval", "auto"),
            probability=p.get("probability", 0.8),
        ),
        "tremolo": lambda: TrillTremoloGenerator(
            params=params,
            ornament_type=p.get("ornament_type", generator_type),
            speed=p.get("speed", 0.125),
            base_note_strategy=p.get("base_note_strategy", "chord_tone"),
            neighbor_interval=p.get("neighbor_interval", "auto"),
            probability=p.get("probability", 0.8),
        ),
        "ornamentation": lambda: OrnamentationGenerator(
            params=params,
            ornament_type=p.get("ornament_type", "mordent"),
            neighbor_interval=p.get("neighbor_interval", 0),
            speed=p.get("speed", 0.125),
            base_note=p.get("base_note", "chord_tone"),
            density_ornaments=p.get("density_ornaments", 0.8),
        ),
        "fill": lambda: FillGenerator(
            params=params,
            fill_type=p.get("fill_type", "descending"),
            fill_length=p.get("fill_length", 2.0),
            position=p.get("position", "end"),
            velocity_curve=p.get("velocity_curve", "crescendo"),
        ),
        "turnaround": lambda: FillGenerator(
            params=params,
            fill_type=p.get("fill_type", "descending"),
            fill_length=p.get("fill_length", 2.0),
            position=p.get("position", "end"),
            velocity_curve=p.get("velocity_curve", "crescendo"),
        ),
        "pickup": lambda: PickupGenerator(
            params=params,
            pickup_type=p.get("pickup_type", "scale_down"),
            pickup_length=p.get("pickup_length", 1.0),
            target_on_downbeat=p.get("target_on_downbeat", True),
        ),
        "glissando": lambda: GlissandoGenerator(
            params=params,
            gliss_type=p.get("gliss_type", "chromatic"),
            speed=p.get("speed", 0.0625),
            gliss_length=p.get("gliss_length", 1.0),
            start_note=p.get("start_note", "octave"),
        ),
        "boogie_woogie": lambda: BoogieWoogieGenerator(
            params=params,
            pattern=p.get("pattern", "standard"),
            octave_bass=p.get("octave_bass", True),
            swing=p.get("swing", 0.67),
        ),
        "stride_piano": lambda: StridePianoGenerator(
            params=params,
            pattern=p.get("pattern", "standard"),
            bass_octave_doubled=p.get("bass_octave_doubled", True),
            chord_voicing=p.get("chord_voicing", "closed"),
        ),
        "tremolo_picking": lambda: TremoloPickingGenerator(
            params=params,
            variant=p.get("variant", "single"),
            speed=p.get("speed", 0.125),
            palm_mute_probability=p.get("palm_mute_probability", 0.0),
            note_strategy=p.get("note_strategy", "chord_root"),
        ),
        "tango": lambda: TangoGenerator(
            params=params,
            pattern=p.get("pattern", "marcato"),
            accent=p.get("accent", 1.15),
            staccato_chords=p.get("staccato_chords", True),
        ),
        "reggae_skank": lambda: ReggaeSkankGenerator(
            params=params,
            variant=p.get("variant", "skank"),
            staccato=p.get("staccato", True),
            mute_probability=p.get("mute_probability", 0.1),
        ),
        "montuno": lambda: MontunoGenerator(
            params=params,
            pattern=p.get("pattern", "son"),
            clave_type=p.get("clave_type", "none"),
            octave_doubling=p.get("octave_doubling", True),
            tumbao_bass=p.get("tumbao_bass", False),
            dynamic_pattern=p.get("dynamic_pattern", False),
        ),
        "acciaccatura": lambda: AcciaccaturaGenerator(
            params=params,
            grace_type=p.get("grace_type", "lower"),
            grace_duration=p.get("grace_duration", 0.08),
            main_duration=p.get("main_duration", 0.75),
            interval=p.get("interval", 0),
            density=p.get("density", 0.7),
        ),
        "pedal_bass": lambda: PedalBassGenerator(
            params=params,
            pedal_note=p.get("pedal_note", "root"),
            sustain=p.get("sustain", 0.0),
            velocity_level=p.get("velocity_level", 0.8),
        ),
        "ragtime": lambda: RagtimeGenerator(
            params=params,
            pattern=p.get("pattern", "classic"),
            melody_density=p.get("melody_density", 0.8),
            left_hand=p.get("left_hand", True),
            right_hand=p.get("right_hand", True),
            chromatic_approach=p.get("chromatic_approach", True),
        ),
        "power_chord": lambda: PowerChordGenerator(
            params=params,
            pattern=p.get("pattern", "chug"),
            include_octave=p.get("include_octave", True),
            palm_mute_ratio=p.get("palm_mute_ratio", 0.6),
        ),
        "broken_chord": lambda: BrokenChordGenerator(
            params=params,
            pattern=p.get("pattern", "chopin"),
            subdivision=p.get("subdivision", 0.25),
            voice_lead=p.get("voice_lead", True),
            velocity_envelope=p.get("velocity_envelope", "arch"),
        ),
        "pedal_melody": lambda: PedalMelodyGenerator(
            params=params,
            pedal_pc=p.get("pedal_pc"),
            melody_style=p.get("melody_style", "stepwise"),
            melody_rhythm=p.get("melody_rhythm", 0.5),
        ),
        "beat_repeat": lambda: BeatRepeatGenerator(
            params=params,
            repeat_type=p.get("repeat_type", "accelerate"),
            stutter_length=p.get("stutter_length", 2.0),
            pitch_shift=p.get("pitch_shift", False),
        ),
        "tremolo_strings": lambda: TremoloStringsGenerator(
            params=params,
            variant=p.get("variant", "chord"),
            bow_speed=p.get("bow_speed", 0.0625),
            dynamic_swell=p.get("dynamic_swell", True),
        ),
        "polyrhythm": lambda: PolyrhythmGenerator(
            params=params,
            ratio=p.get("ratio", "3x2"),
            stream_a_pitch=p.get("stream_a_pitch", "chord_root"),
            stream_b_pitch=p.get("stream_b_pitch", "fifth"),
        ),
        "waltz": lambda: WaltzGenerator(
            params=params,
            variant=p.get("variant", "viennese"),
            include_bass_octave=p.get("include_bass_octave", True),
            staccato_chords=p.get("staccato_chords", True),
        ),
        "chorale": lambda: ChoraleGenerator(
            params=params,
            voice_spacing=p.get("voice_spacing", 12),
            soprano_motion=p.get("soprano_motion", "stepwise"),
            rhythmic_unit=p.get("rhythmic_unit", 1.0),
        ),
        "nebula": lambda: NebulaGenerator(
            params=params,
            variant=p.get("variant", "cloud"),
            density_notes=p.get("density_notes", 5),
            pitch_spread=p.get("pitch_spread", 12),
            note_duration=p.get("note_duration", 3.0),
        ),
        "harmonics": lambda: HarmonicsGenerator(
            params=params,
            harmonic_type=p.get("harmonic_type", "natural"),
            use_chord_tones=p.get("use_chord_tones", True),
            duration_per_note=p.get("duration_per_note", 2.0),
        ),
        "bend": lambda: BendGenerator(
            params=params,
            bend_type=p.get("bend_type", "bend_up"),
            bend_range=p.get("bend_range", 2),
            bend_speed=p.get("bend_speed", 0.06),
        ),
        "clusters": lambda: ClusterGenerator(
            params=params,
            cluster_type=p.get("cluster_type", "second"),
            cluster_width=p.get("cluster_width", 3),
            duration_per_cluster=p.get("duration_per_cluster", 2.0),
        ),
        "cadence": lambda: CadenceGenerator(
            params=params,
            cadence_type=p.get("cadence_type", "PAC"),
            voice_count=p.get("voice_count", 4),
            cadence_length=p.get("cadence_length", 2.0),
        ),
        "synth_bass": lambda: SynthBassGenerator(
            params=params,
            waveform=p.get("waveform", "acid"),
            pattern=p.get("pattern", "acid_line"),
            slide_probability=p.get("slide_probability", 0.3),
        ),
        "supersaw_pad": lambda: SupersawPadGenerator(
            params=params,
            variant=p.get("variant", "trance"),
            voice_count=p.get("voice_count", 5),
            sidechain_feel=p.get("sidechain_feel", False),
        ),
        "pluck_sequence": lambda: PluckSequenceGenerator(
            params=params,
            pattern=p.get("pattern", "offbeat"),
            decay_time=p.get("decay_time", 0.3),
        ),
        "strings_legato": lambda: StringsLegatoGenerator(
            params=params,
            section_size=p.get("section_size", "ensemble"),
            portamento_speed=p.get("portamento_speed", 0.15),
            dynamic_shape=p.get("dynamic_shape", "cresc_dim"),
            interval_preference=p.get("interval_preference", "step"),
        ),
        "strings_pizzicato": lambda: StringsPizzicatoGenerator(
            params=params,
            pattern=p.get("pattern", "ostinato"),
            staccato_length=p.get("staccato_length", 0.15),
            velocity_variation=p.get("velocity_variation", 0.3),
        ),
        "brass_section": lambda: BrassSectionGenerator(
            params=params,
            articulation=p.get("articulation", "hit"),
            voicing=p.get("voicing", "closed"),
            intensity=p.get("intensity", 0.8),
        ),
        "sax_solo": lambda: SaxSoloGenerator(
            params=params,
            style=p.get("style", "bebop"),
            vibrato_depth=p.get("vibrato_depth", 0.3),
            chromaticism=p.get("chromaticism", 0.5),
        ),
        "trap_drums": lambda: TrapDrumsGenerator(
            params=params,
            variant=p.get("variant", "standard"),
            hat_roll_density=p.get("hat_roll_density", 0.5),
            kick_pattern=p.get("kick_pattern", "standard"),
        ),
        "four_on_floor": lambda: FourOnFloorGenerator(
            params=params,
            variant=p.get("variant", "house"),
            hihat_style=p.get("hihat_style", "mixed"),
            swing=p.get("swing", 0.0),
        ),
        "breakbeat": lambda: BreakbeatGenerator(
            params=params,
            variant=p.get("variant", "amen"),
            chop_probability=p.get("chop_probability", 0.3),
            ghost_notes=p.get("ghost_notes", True),
            double_time=p.get("double_time", False),
        ),
        "fx_riser": lambda: FXRiserGenerator(
            params=params,
            riser_type=p.get("riser_type", "synth"),
            length_beats=p.get("length_beats", 4.0),
            pitch_curve=p.get("pitch_curve", "exponential"),
        ),
        "fx_impact": lambda: FXImpactGenerator(
            params=params,
            impact_type=p.get("impact_type", "boom"),
            tail_length=p.get("tail_length", 2.0),
            pitch_drop=p.get("pitch_drop", 12),
        ),
        "reharmonization": lambda: ReharmonizationGenerator(
            params=params,
            strategy=p.get("strategy", "tritone"),
            preservation=p.get("preservation", "melody"),
            substitution_frequency=p.get("substitution_frequency", 0.5),
        ),
        "modal_interchange": lambda: ModalInterchangeGenerator(
            params=params,
            source_mode=p.get("source_mode", "minor"),
            frequency=p.get("frequency", 0.3),
        ),
        "vocal_chops": lambda: VocalChopsGenerator(
            params=params,
            processing=p.get("processing", "pitch_shift"),
            density=p.get("density", 0.6),
            chop_pattern=p.get("chop_pattern", "syncopated"),
        ),
        "vocal_oohs": lambda: VocalOohsGenerator(
            params=params,
            syllable=p.get("syllable", "ooh"),
            harmony_count=p.get("harmony_count", 3),
            vibrato=p.get("vibrato", 0.4),
        ),
        "guitar_legato": lambda: GuitarLegatoGenerator(
            params=params,
            direction=p.get("direction", "ascending"),
            notes_per_string=p.get("notes_per_string", 4),
            speed=p.get("speed", 0.125),
        ),
        "guitar_tapping": lambda: GuitarTappingGenerator(
            params=params,
            pattern=p.get("pattern", "arpeggio"),
            width_interval=p.get("width_interval", 12),
        ),
        "arranger": lambda: ArrangerGenerator(
            params=params,
            form=p.get("form", "verse_chorus"),
            section_length=p.get("section_length", 8),
            variation_seed=p.get("variation_seed", 0),
        ),
        "humanizer": lambda: HumanizerGenerator(
            params=params,
            timing_variance=p.get("timing_variance", 0.03),
            velocity_variance=p.get("velocity_variance", 0.1),
            groove_type=p.get("groove_type", "straight"),
        ),
        "piano_comp": lambda: PianoCompGenerator(
            params=params,
            comp_style=p.get("comp_style", "jazz"),
            voicing_type=p.get("voicing_type", "shell"),
            accent_pattern=p.get("accent_pattern", "syncopated"),
        ),
        "organ_drawbars": lambda: OrganDrawbarsGenerator(
            params=params,
            registration=p.get("registration", "jazz"),
            leslie_speed=p.get("leslie_speed", "slow"),
            percussion=p.get("percussion", False),
        ),
        "keys_arpeggio": lambda: KeysArpeggioGenerator(
            params=params,
            arp_pattern=p.get("arp_pattern", "up"),
            rate=p.get("rate", 0.125),
            octave_spread=p.get("octave_spread", 2),
        ),
        "guitar_strumming": lambda: GuitarStrummingGenerator(
            params=params,
            strum_pattern=p.get("strum_pattern", "folk"),
            palm_mute_ratio=p.get("palm_mute_ratio", 0.2),
            dead_strums=p.get("dead_strums", True),
        ),
        "bass_slap": lambda: BassSlapGenerator(
            params=params,
            slap_pattern=p.get("slap_pattern", "funky"),
            ghost_note_prob=p.get("ghost_note_prob", 0.3),
            pop_probability=p.get("pop_probability", 0.4),
        ),
        "guitar_sweep": lambda: GuitarSweepGenerator(
            params=params,
            sweep_direction=p.get("sweep_direction", "up"),
            note_count=p.get("note_count", 5),
            speed=p.get("speed", 0.08),
        ),
        "vocal_melisma": lambda: VocalMelismaGenerator(
            params=params,
            style=p.get("style", "rnb"),
            run_length=p.get("run_length", 4),
            vibrato_depth=p.get("vibrato_depth", 0.3),
        ),
        "vocal_adlibs": lambda: VocalAdlibsGenerator(
            params=params,
            density_adlib=p.get("density_adlib", 0.3),
            register=p.get("register", "mid"),
            style=p.get("style", "adlib"),
        ),
        "choir_ahhs": lambda: ChoirAahsGenerator(
            params=params,
            voice_count=p.get("voice_count", 4),
            dynamics=p.get("dynamics", "mf"),
            vibrato=p.get("vibrato", 0.3),
        ),
        "drum_kit_pattern": lambda: DrumKitPatternGenerator(
            params=params,
            style=p.get("style", "rock"),
            hihat_pattern=p.get("hihat_pattern", "eighth"),
            fill_frequency=p.get("fill_frequency", 0.2),
        ),
        "percussion_ensemble": lambda: PercussionEnsembleGenerator(
            params=params,
            instruments=p.get("instruments", ["conga", "bongo", "shaker", "tambourine"]),
            density=p.get("density", 0.6),
        ),
        "electronic_drums": lambda: ElectronicDrumsGenerator(
            params=params,
            kit=p.get("kit", "909"),
            pattern=p.get("pattern", "four_on_floor"),
            sidechain=p.get("sidechain", False),
        ),
        "woodwinds_ensemble": lambda: WoodwindsEnsembleGenerator(
            params=params,
            section=p.get("section", "quartet"),
            articulation=p.get("articulation", "legato"),
        ),
        "strings_ensemble": lambda: StringsEnsembleGenerator(
            params=params,
            section_size=p.get("section_size", "full"),
            articulation=p.get("articulation", "sustained"),
            divisi=p.get("divisi", 4),
        ),
        "orchestral_hit": lambda: OrchestralHitGenerator(
            params=params,
            hit_type=p.get("hit_type", "staccato"),
            voicing=p.get("voicing", "chord"),
            duration=p.get("duration", 0.5),
        ),
        "lead_synth": lambda: LeadSynthGenerator(
            params=params,
            style=p.get("style", "trance"),
            portamento=p.get("portamento", 0.15),
            vibrato_depth=p.get("vibrato_depth", 0.2),
        ),
        "sidechain_pump": lambda: SidechainPumpGenerator(
            params=params,
            rate=p.get("rate", "1/4"),
            depth=p.get("depth", 0.7),
        ),
        "voice_leading": lambda: VoiceLeadingGenerator(
            params=params,
            voices=p.get("voices", 4),
            prefer_stepwise=p.get("prefer_stepwise", True),
            range_style=p.get("range_style", "close"),
        ),
        "counterpoint": lambda: CounterpointGenerator(
            params=params,
            species=p.get("species", 1),
            voices=p.get("voices", 2),
            cantus_position=p.get("cantus_position", "below"),
        ),
        "motif_development": lambda: MotifDevelopmentGenerator(
            params=params,
            transformations=p.get("transformations", ["original", "inversion", "retrograde"]),
            motif_length=p.get("motif_length", 4),
            development_style=p.get("development_style", "sequential"),
        ),
        "filter_sweep": lambda: FilterSweepGenerator(
            params=params,
            sweep_type=p.get("sweep_type", "lowpass_open"),
            resonance=p.get("resonance", 0.5),
            duration=p.get("duration", 4.0),
        ),
        "euclidean_rhythm": lambda: EuclideanRhythmGenerator(
            params=params,
            pulses=p.get("pulses", 5),
            steps=p.get("steps", 8),
            pitch=p.get("pitch", "chord_root"),
        ),
        "markov_rhythm": lambda: _create_markov_rhythm(p),
        "bass_wobble": lambda: BassWobbleGenerator(
            params=params,
            wobble_rate=p.get("wobble_rate", "1/8"),
            waveform=p.get("waveform", "saw"),
            lfo_shape=p.get("lfo_shape", "sine"),
            pitch_slide=p.get("pitch_slide", False),
        ),
        "rest": lambda: RestGenerator(),
        "step_sequencer": lambda: StepSequencer(
            params=params,
            steps=p.get("steps", 16),
            gate_prob=p.get("gate_prob", 0.8),
            velocity_map=p.get("velocity_map"),
            ties=p.get("ties"),
            root_note=p.get("root_note", 60),
        ),
        "dyads_run": lambda: DyadsRunGenerator(
            params=params,
            interval=p.get("interval", 3),
            technique=p.get("technique", "up"),
            notes_per_run=p.get("notes_per_run", 8),
            scale_steps=p.get("scale_steps", False),
        ),
        "generic": lambda: GenericGenerator(
            params=params,
            chord_note_ratio=p.get("chord_note_ratio", 0.7),
            partial_polyphony=p.get("partial_polyphony", True),
            max_polyphony=p.get("max_polyphony", 3),
            repeat_last=p.get("repeat_last", False),
        ),
        "phrase_container": lambda: PhraseContainer(
            params=params,
            mode=p.get("mode", "sequential"),
        ),
        "phrase_morpher": lambda: PhraseMorpher(
            params=params,
            steps=p.get("steps", 8),
            vertical_snap=p.get("vertical_snap", "scale"),
        ),
        "random_note": lambda: RandomNoteGenerator(
            params=params,
            velocity_range=p.get("velocity_range", (40, 100)),
            note_range=p.get("note_range", (36, 84)),
        ),
        "motive": lambda: MotiveGenerator(
            params=params,
            motive_length=p.get("motive_length", 4),
            development=p.get("development", "repeat"),
            scale_steps=p.get("scale_steps", True),
            interval_seed=p.get("interval_seed"),
        ),
        "strings_staccato": lambda: StringsStaccatoGenerator(
            params=params,
            style=p.get("style", "octaves"),
            note_range_low=p.get("note_range_low"),
            note_range_high=p.get("note_range_high"),
        ),
        "hemiola": lambda: HemiolaGenerator(
            params=params,
            pattern=p.get("pattern", "3_over_2"),
            pitch_strategy=p.get("pitch_strategy", "chord_tone"),
            velocity_accent=p.get("velocity_accent", 1.15),
            note_duration=p.get("note_duration"),
            cycles_per_chord=p.get("cycles_per_chord", 1),
        ),
        "backbeat": lambda: BackbeatGenerator(
            params=params,
            mode=p.get("mode", "accent"),
            accent_velocity=p.get("accent_velocity", 1.0),
            ghost_velocity=p.get("ghost_velocity", 0.4),
            subdivision=p.get("subdivision", 1.0),
            pitch_strategy=p.get("pitch_strategy", "chord_tone"),
        ),
        "chord_voicing": lambda: ChordVoicingGenerator(
            params=params,
            voicing=p.get("voicing", "drop2"),
            rhythm_pattern=p.get("rhythm_pattern", "sustained"),
            octave=p.get("octave", 4),
            velocity_curve=p.get("velocity_curve", "flat"),
        ),
        "dynamics": lambda: DynamicsCurveGenerator(
            params=params,
            curve_type=p.get("curve_type", "crescendo"),
            note_duration=p.get("note_duration", 1.0),
            pitch_strategy=p.get("pitch_strategy", "chord_tone"),
            strength=p.get("strength", 1.0),
        ),
        "secondary_dominant": lambda: SecondaryDominantGenerator(
            params=params,
            strategy=p.get("strategy", "secondary"),
            voicing=p.get("voicing", "root_position"),
            octave=p.get("octave", 4),
        ),
        "section_builder": lambda: SectionBuilderGenerator(
            params=params,
            section_type=p.get("section_type", "verse"),
            pattern=p.get("pattern", "melody"),
            bars_per_section=p.get("bars_per_section", 4),
        ),
        "transition": lambda: TransitionGenerator(
            params=params,
            transition_type=p.get("transition_type", "build"),
            length_beats=p.get("length_beats", 8.0),
            octave_range=p.get("octave_range", 2),
            rhythm_acceleration=p.get("rhythm_acceleration", 1.0),
        ),
        "swing": lambda: SwingGenerator(
            params=params,
            swing_ratio=p.get("swing_ratio", 0.67),
            subdivision=p.get("subdivision", 0.5),
            pitch_strategy=p.get("pitch_strategy", "chord_tone"),
            accent_pattern=p.get("accent_pattern", "downbeat"),
        ),
        "downbeat_rest": lambda: DownbeatRestGenerator(
            params=params,
            mode=p.get("mode", "skip"),
            delay_amount=p.get("delay_amount", 0.5),
            caesura_length=p.get("caesura_length", 1.0),
            subdivision=p.get("subdivision", 1.0),
            pitch_strategy=p.get("pitch_strategy", "chord_tone"),
        ),
        "dark_pad": lambda: DarkPadGenerator(
            params=params,
            mode=p.get("mode", "minor_pad"),
            chord_dur=p.get("chord_dur", 8.0),
            velocity_level=p.get("velocity_level", 0.35),
            register=p.get("register", "low"),
            overlap=p.get("overlap", 0.3),
        ),
        "tension": lambda: TensionGenerator(
            params=params,
            mode=p.get("mode", "semitone_cluster"),
            note_duration=p.get("note_duration", 2.0),
            velocity_level=p.get("velocity_level", 0.4),
            register=p.get("register", "mid"),
        ),
        "dark_bass": lambda: DarkBassGenerator(
            params=params,
            mode=p.get("mode", "doom"),
            octave=p.get("octave", 2),
            note_duration=p.get("note_duration", 4.0),
            velocity_level=p.get("velocity_level", 0.7),
            movement=p.get("movement", "root_only"),
        ),
        "bass_808_sliding": lambda: Bass808SlidingGenerator(
            params=params,
            pattern=p.get("pattern", "trap_basic"),
            slide_type=p.get("slide_type", "overlap"),
            slide_probability=p.get("slide_probability", 0.4),
            octave_range=p.get("octave_range", 2),
            accent_velocity=p.get("accent_velocity", 1.1),
            ghost_velocity_ratio=p.get("ghost_velocity_ratio", 0.55),
        ),
        "hihat_stutter": lambda: HiHatStutterGenerator(
            params=params,
            pattern=p.get("pattern", "trap_eighth"),
            roll_density=p.get("roll_density", 0.4),
            open_hat_probability=p.get("open_hat_probability", 0.15),
            velocity_accent=p.get("velocity_accent", True),
            pitch_variation=p.get("pitch_variation", True),
            stutter_lengths=p.get("stutter_lengths"),
            instrument=p.get("instrument", "hh_closed"),
        ),
        "drill_pattern": lambda: DrillPatternGenerator(
            params=params,
            variant=p.get("variant", "uk_drill"),
            slide_amount=p.get("slide_amount", 7),
            stutter_intensity=p.get("stutter_intensity", 0.5),
            snare_displacement=p.get("snare_displacement", 1),
            include_piano=p.get("include_piano", True),
        ),
        "ghost_notes": lambda: GhostNotesGenerator(
            params=params,
            target=p.get("target", "snare"),
            pattern=p.get("pattern", "funk"),
            ghost_velocity=p.get("ghost_velocity", 35),
            ghost_density=p.get("ghost_density", 0.6),
            placement=p.get("placement", "sixteenth"),
        ),
        "lofi_hiphop": lambda: LoFiHipHopGenerator(
            params=params,
            variant=p.get("variant", "chill"),
            swing_ratio=p.get("swing_ratio", 0.62),
            chord_voicing=p.get("chord_voicing", "ninth"),
            include_drums=p.get("include_drums", True),
            include_bass=p.get("include_bass", True),
            vinyl_noise=p.get("vinyl_noise", 0.3),
            tape_stop=p.get("tape_stop", 0.1),
        ),
        "afrobeats": lambda: AfrobeatsGenerator(
            params=params,
            variant=p.get("variant", "afrobeats"),
            log_drum_density=p.get("log_drum_density", 0.6),
            shaker_pattern=p.get("shaker_pattern", "sixteenth"),
            include_piano=p.get("include_piano", True),
            bounce_amount=p.get("bounce_amount", 0.5),
            percussion_layer=p.get("percussion_layer", True),
        ),
        "phonk": lambda: PhonkGenerator(
            params=params,
            variant=p.get("variant", "classic_phonk"),
            cowbell_density=p.get("cowbell_density", 0.7),
            bass_slide_amount=p.get("bass_slide_amount", 5),
            filter_cutoff=p.get("filter_cutoff", 0.4),
            memphis_chops=p.get("memphis_chops", True),
            aggression=p.get("aggression", 0.6),
        ),
        "melodic_rap": lambda: MelodicRapGenerator(
            params=params,
            variant=p.get("variant", "sing_rap"),
            repetition_factor=p.get("repetition_factor", 0.5),
            stepwise_bias=p.get("stepwise_bias", 0.7),
            bend_probability=p.get("bend_probability", 0.15),
            phrase_length=p.get("phrase_length", 4.0),
            rest_probability=p.get("rest_probability", 0.25),
            octave_register=p.get("octave_register", 5),
        ),
        "uk_garage": lambda: UKGarageGenerator(
            params=params,
            variant=p.get("variant", "2step"),
            shuffle_amount=p.get("shuffle_amount", 0.55),
            skippy_hats=p.get("skippy_hats", True),
            include_stabs=p.get("include_stabs", True),
            bass_wobble=p.get("bass_wobble", True),
            chop_density=p.get("chop_density", 0.3),
        ),
        "hyperpop": lambda: HyperpopGenerator(
            params=params,
            variant=p.get("variant", "standard"),
            pitch_shift_range=p.get("pitch_shift_range", 12),
            glitch_density=p.get("glitch_density", 0.4),
            distortion_amount=p.get("distortion_amount", 0.5),
            chaos_factor=p.get("chaos_factor", 0.3),
            include_leads=p.get("include_leads", True),
        ),
        "advanced_step_seq": lambda: AdvancedStepSequencer(
            params=params,
            pattern=p.get("pattern", "four_on_floor"),
            steps=p.get("steps", 16),
            humanize_timing=p.get("humanize_timing", 0.02),
            humanize_velocity=p.get("humanize_velocity", 8),
            swing=p.get("swing", 0.5),
        ),
        "bpm_adaptive": lambda: BPMAdaptiveGenerator(
            params=params,
            bpm=p.get("bpm", 120.0),
            reference_bpm=p.get("reference_bpm", 120.0),
            scaling_mode=p.get("scaling_mode", "logarithmic"),
            min_density=p.get("min_density", 0.3),
            max_density=p.get("max_density", 1.5),
        ),
        "genre_fusion": lambda: GenreFusionEngine(
            params=params,
            genre_a=p.get("genre_a", "trap"),
            genre_b=p.get("genre_b", "jazz"),
            blend_ratio=p.get("blend_ratio", 0.5),
            fusion_mode=p.get("fusion_mode", "interleave"),
            morph_steps=p.get("morph_steps", 8),
        ),
        "vocal_melody_auto": lambda: VocalMelodyAutoGenerator(
            params=params,
            variant=p.get("variant", "travis"),
            register=p.get("register", "mid"),
            sustain_preference=p.get("sustain_preference", 0.5),
            octave_jump_probability=p.get("octave_jump_probability", 0.15),
            grace_note_probability=p.get("grace_note_probability", 0.2),
            repetition_amount=p.get("repetition_amount", 0.4),
        ),
        "jersey_club": lambda: JerseyClubGenerator(
            params=params,
            variant=p.get("variant", "classic"),
            kick_triplet_density=p.get("kick_triplet_density", 0.7),
            stutter_breaks=p.get("stutter_breaks", True),
            chopped_samples=p.get("chopped_samples", True),
            birdman_sample=p.get("birdman_sample", False),
        ),
        "dembow": lambda: DembowGenerator(
            params=params,
            variant=p.get("variant", "classic"),
            shaker_density=p.get("shaker_density", 0.7),
            include_bass=p.get("include_bass", True),
            cowbell_accent=p.get("cowbell_accent", True),
            swing_amount=p.get("swing_amount", 0.1),
        ),
        "baile_funk": lambda: BaileFunkGenerator(
            params=params,
            variant=p.get("variant", "classic"),
            bass_distortion=p.get("bass_distortion", 0.7),
            percussion_density=p.get("percussion_density", 0.6),
            mc_chops=p.get("mc_chops", True),
            slide_amount=p.get("slide_amount", 7),
        ),
        "rage_beat": lambda: RageBeatGenerator(
            params=params,
            variant=p.get("variant", "carti"),
            synth_distortion=p.get("synth_distortion", 0.8),
            hat_speed=p.get("hat_speed", "sixteenth"),
            aggression=p.get("aggression", 0.7),
            include_synth_lead=p.get("include_synth_lead", True),
        ),
        "pluggnb": lambda: PluggnbGenerator(
            params=params,
            variant=p.get("variant", "pluggnb"),
            pad_voicing=p.get("pad_voicing", "ninth"),
            include_808=p.get("include_808", True),
            hat_style=p.get("hat_style", "gentle"),
            melody_register=p.get("melody_register", 5),
        ),
        "latin_trap": lambda: LatinTrapGenerator(
            params=params,
            variant=p.get("variant", "reggaeton_trap"),
            dembow_influence=p.get("dembow_influence", 0.6),
            hat_rolls=p.get("hat_rolls", True),
            include_percussion=p.get("include_percussion", True),
        ),
        "cloud_rap": lambda: CloudRapGenerator(
            params=params,
            variant=p.get("variant", "cloud"),
            pad_density=p.get("pad_density", 0.6),
            drum_sparseness=p.get("drum_sparseness", 0.5),
            arp_speed=p.get("arp_speed", "slow"),
        ),
        "dnb_jungle": lambda: DnBJungleGenerator(
            params=params,
            variant=p.get("variant", "liquid"),
            break_density=p.get("break_density", 0.6),
            reese_amount=p.get("reese_amount", 0.5),
            sub_weight=p.get("sub_weight", 0.7),
        ),
        "hardstyle": lambda: HardstyleGenerator(
            params=params,
            variant=p.get("variant", "euphoric"),
            kick_distortion=p.get("kick_distortion", 0.8),
            include_lead=p.get("include_lead", True),
            reverse_bass_weight=p.get("reverse_bass_weight", 0.5),
        ),
        "synthwave": lambda: SynthwaveGenerator(
            params=params,
            variant=p.get("variant", "outrun"),
            arp_pattern=p.get("arp_pattern", "up"),
            gated_pads=p.get("gated_pads", True),
            include_lead=p.get("include_lead", True),
            gate_rate=p.get("gate_rate", 0.5),
        ),
        "boom_bap": lambda: BoomBapGenerator(
            params=params,
            variant=p.get("variant", "classic"),
            swing_ratio=p.get("swing_ratio", 0.58),
            chop_density=p.get("chop_density", 0.4),
            ghost_snares=p.get("ghost_snares", True),
            dusty_velocities=p.get("dusty_velocities", True),
        ),
        "future_bass": lambda: FutureBassGenerator(
            params=params,
            variant=p.get("variant", "standard"),
            chord_chop_rate=p.get("chord_chop_rate", 0.5),
            sidechain_feel=p.get("sidechain_feel", True),
            include_vocal_chops=p.get("include_vocal_chops", True),
            supersaw_voices=p.get("supersaw_voices", 5),
        ),
        "grime": lambda: GrimeGenerator(
            params=params,
            variant=p.get("variant", "classic"),
            synth_aggression=p.get("synth_aggression", 0.7),
            include_melody=p.get("include_melody", True),
        ),
        "witch_house": lambda: WitchHouseGenerator(
            params=params,
            variant=p.get("variant", "classic"),
            slowdown_factor=p.get("slowdown_factor", 0.5),
            pad_darkness=p.get("pad_darkness", 0.8),
        ),
        "phonk_house": lambda: PhonkHouseGenerator(
            params=params,
            variant=p.get("variant", "drift_house"),
            cowbell_density=p.get("cowbell_density", 0.6),
            bass_slides=p.get("bass_slides", True),
        ),
        "amapiano_logdrum": lambda: AmapianoLogDrumGenerator(
            params=params,
            pattern=p.get("pattern", "classic"),
            pitch_variation=p.get("pitch_variation", 0.4),
            velocity_humanize=p.get("velocity_humanize", 0.3),
            ghost_probability=p.get("ghost_probability", 0.2),
            swing=p.get("swing", 0.55),
            note_length_variation=p.get("note_length_variation", 0.3),
        ),
        "afro_percussion": lambda: AfroPercussionGenerator(
            params=params,
            ensemble=p.get("ensemble", "west_african"),
            density=p.get("density", 0.6),
            include_pitched=p.get("include_pitched", True),
            call_response=p.get("call_response", True),
            swing=p.get("swing", 0.55),
        ),
        "highlife_guitar": lambda: HighlifeGuitarGenerator(
            params=params,
            variant=p.get("variant", "highlife"),
            riff_density=p.get("riff_density", 0.7),
            palm_mute_ratio=p.get("palm_mute_ratio", 0.3),
            octave_doubling=p.get("octave_doubling", True),
            interlocking=p.get("interlocking", False),
            pentatonic_bias=p.get("pentatonic_bias", 0.6),
        ),
        "afro_house": lambda: AfroHouseGenerator(
            params=params,
            variant=p.get("variant", "deep"),
            percussion_density=p.get("percussion_density", 0.6),
            include_marimba=p.get("include_marimba", True),
            bass_depth=p.get("bass_depth", 0.7),
        ),
        "gqom": lambda: GqomGenerator(
            params=params,
            variant=p.get("variant", "classic"),
            kick_weight=p.get("kick_weight", 0.8),
            include_vocal_stabs=p.get("include_vocal_stabs", True),
        ),
        "kuduro": lambda: KuduroGenerator(
            params=params,
            variant=p.get("variant", "kuduro"),
            intensity=p.get("intensity", 0.7),
        ),
        "afro_drill": lambda: AfroDrillGenerator(
            params=params,
            variant=p.get("variant", "burna"),
            slide_amount=p.get("slide_amount", 7),
            melody_density=p.get("melody_density", 0.6),
        ),
        "soukous_guitar": lambda: SoukousGuitarGenerator(
            params=params,
            variant=p.get("variant", "soukous"),
            run_speed=p.get("run_speed", "sixteenth"),
            note_density=p.get("note_density", 0.8),
        ),
        "bongo_flava": lambda: BongoFlavaGenerator(
            params=params,
            variant=p.get("variant", "modern"),
            melody_density=p.get("melody_density", 0.6),
            include_percussion=p.get("include_percussion", True),
        ),
        "afro_samba": lambda: AfroSambaGenerator(
            params=params,
            variant=p.get("variant", "samba_afro"),
            perc_density=p.get("perc_density", 0.7),
            include_guitar=p.get("include_guitar", True),
        ),
        "combat_escalation": lambda: CombatEscalationGenerator(
            params=params,
            intensity=p.get("intensity", 0.5),
            layers=p.get("layers"),
            tempo_factor=p.get("tempo_factor", 1.0),
            key_change_on_climax=p.get("key_change_on_climax", True),
        ),
        "stinger": lambda: StingerGenerator(
            params=params,
            stinger_type=p.get("stinger_type", "discovery"),
            root_note=p.get("root_note", 0),
            register=p.get("register", 5),
            velocity_multiplier=p.get("velocity_multiplier", 1.0),
            variation=p.get("variation", True),
        ),
        "chiptune": lambda: ChiptuneGenerator(
            params=params,
            variant=p.get("variant", "nes_classic"),
            channels=p.get("channels"),
            duty_cycle=p.get("duty_cycle", "50%"),
            arpeggio_speed=p.get("arpeggio_speed", 0.125),
            melody_style=p.get("melody_style", "stepwise"),
        ),
        "horror_dissonance": lambda: HorrorDissonanceGenerator(
            params=params,
            variant=p.get("variant", "psychological"),
            dissonance_level=p.get("dissonance_level", 0.7),
            silence_probability=p.get("silence_probability", 0.15),
            pitch_drift=p.get("pitch_drift", 0.3),
            density=p.get("density", 0.4),
        ),
        "stealth_state": lambda: StealthStateGenerator(
            params=params,
            stealth_state=p.get("stealth_state", "hidden"),
            transition_speed=p.get("transition_speed", 0.5),
            heartbeat=p.get("heartbeat", True),
        ),
        "procedural_exploration": lambda: ProceduralExplorationGenerator(
            params=params,
            variant=p.get("variant", "nature"),
            mood=p.get("mood", "peaceful"),
            loop_length_bars=p.get("loop_length_bars", 4),
            density=p.get("density", 0.35),
        ),
        "boss_battle": lambda: BossBattleGenerator(
            params=params,
            phase=p.get("phase", "fight"),
            variant=p.get("variant", "epic"),
            choir_stabs=p.get("choir_stabs", True),
            brass_fanfare=p.get("brass_fanfare", True),
            timpani_drive=p.get("timpani_drive", True),
        ),
        "puzzle_loop": lambda: PuzzleLoopGenerator(
            params=params,
            variant=p.get("variant", "bells"),
            complexity=p.get("complexity", 0.3),
            loop_bars=p.get("loop_bars", 4),
            register=p.get("register", "mid"),
        ),
        "medieval_tavern": lambda: MedievalTavernGenerator(
            params=params,
            variant=p.get("variant", "tavern"),
            mode=p.get("mode", "dorian"),
            lute_density=p.get("lute_density", 0.7),
            include_flute=p.get("include_flute", True),
            dance_rhythm=p.get("dance_rhythm", True),
        ),
        "scifi_underscore": lambda: SciFiUnderscoreGenerator(
            params=params,
            variant=p.get("variant", "blade_runner"),
            pad_density=p.get("pad_density", 0.6),
            arp_speed=p.get("arp_speed", 0.25),
            include_bass_synth=p.get("include_bass_synth", True),
        ),
        "victory_fanfare": lambda: VictoryFanfareGenerator(
            params=params,
            variant=p.get("variant", "victory"),
            register=p.get("register", 5),
            dynamics=p.get("dynamics", "forte"),
        ),
    }
    factory_fn = _GENERATOR_MAP.get(generator_type)
    if factory_fn is None:
        return None
    return factory_fn()


def _create_markov_rhythm(p: dict[str, Any]):
    from melodica.rhythm.markov_rhythm import MarkovRhythmGenerator as MRG

    return MRG(
        style=p.get("markov_style", "straight"),
        syncopation=p.get("syncopation", 0.15),
        phrase_length=p.get("phrase_length", 8),
        seed=p.get("seed", None),
    )


def apply_variation(
    var_name: str,
    notes: list[NoteInfo],
) -> list[NoteInfo]:
    """Apply a named variation transformation to a list of notes."""
    match var_name:
        case "transpose_up":
            return [
                NoteInfo(
                    pitch=n.pitch + 12,
                    start=n.start,
                    duration=n.duration,
                    velocity=n.velocity,
                    articulation=n.articulation,
                    expression=dict(n.expression),
                )
                for n in notes
            ]
        case "transpose_down":
            return [
                NoteInfo(
                    pitch=n.pitch - 12,
                    start=n.start,
                    duration=n.duration,
                    velocity=n.velocity,
                    articulation=n.articulation,
                    expression=dict(n.expression),
                )
                for n in notes
            ]
        case "staccato":
            return [
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration * 0.3,
                    velocity=n.velocity,
                    articulation="staccato",
                    expression=dict(n.expression),
                )
                for n in notes
            ]
        case "legato":
            return [
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration * 1.5,
                    velocity=n.velocity,
                    articulation="legato",
                    expression=dict(n.expression),
                )
                for n in notes
            ]
        case "humanize":
            return [
                NoteInfo(
                    pitch=n.pitch,
                    start=round(n.start + random.uniform(-0.05, 0.05), 6),
                    duration=n.duration,
                    velocity=max(1, min(127, n.velocity + random.randint(-10, 10))),
                    articulation=n.articulation,
                    expression=dict(n.expression),
                )
                for n in notes
            ]
        case "octave_double":
            result = list(notes)
            for n in notes:
                result.append(
                    NoteInfo(
                        pitch=n.pitch + 12,
                        start=n.start,
                        duration=n.duration,
                        velocity=max(1, n.velocity - 15),
                        articulation=n.articulation,
                        expression=dict(n.expression),
                    )
                )
            return result
        case _:
            return notes
