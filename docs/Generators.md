# Generators Reference

All generators live in `melodica/generators/`. Every class inherits `PhraseGenerator(ABC)` with optional `params: GeneratorParams`.

## GeneratorParams (dataclass)

| Field | Default | Notes |
|-------|---------|-------|
| density | 0.5 | |
| key_range_low | 48 | |
| key_range_high | 84 | |
| complexity | 0.5 | |
| leap_probability | 0.2 | |
| velocity_range | None | |
| intel | MelodicIntelligenceConfig() | |

---

## Orchestral Strings

| Class | File | Key params |
|-------|------|------------|
| `ViolinGenerator` | `orchestral_strings.py` | `articulation="sustained"`, `dynamic_curve="flat"`, `vibrato=True`, `con_sordino=False`, `double_stops=False`, `position=1`, `note_density=1.0` |
| `ViolaGenerator` | `orchestral_strings.py` | same as Violin |
| `CelloGenerator` | `orchestral_strings.py` | same + `bass_voice=False` |
| `ContrabassGenerator` | `orchestral_strings.py` | `vibrato=False`, `bass_voice=True` |

## Orchestral Brass

| Class | File | Key params |
|-------|------|------------|
| `TrumpetGenerator` | `orchestral_brass.py` | `articulation="sustained"`, `dynamic_curve="flat"`, `con_sordino=False`, `register=2`, `fanfare_mode=False`, `note_density=1.0` |
| `TromboneGenerator` | `orchestral_brass.py` | same + `bass_voice=False` |
| `FrenchHornGenerator` | `orchestral_brass.py` | same as Trumpet |
| `BrassSectionGenerator` | `brass_section.py` | `articulation="hit"`, `voicing="closed"`, `intensity=0.8`, `divisi_count=3`, `ensemble_mode="full"`, `breath_gap=0.25`, `mute=None`, `con_sordino=False` |

## Orchestral Woodwinds

| Class | File | Key params |
|-------|------|------------|
| `FluteGenerator` | `orchestral_woodwinds.py` | `articulation="sustained"`, `vibrato=True`, `register=2`, `breath_phrase=True`, `note_density=1.0` |
| `OboeGenerator` | `orchestral_woodwinds.py` | same + `cor_anglais=False` |
| `ClarinetGenerator` | `orchestral_woodwinds.py` | `vibrato=False`, `bass_voice=False` |
| `BassoonGenerator` | `orchestral_woodwinds.py` | `vibrato=False`, `register=1` |

## Orchestral Percussion

| Class | File | Key params |
|-------|------|------------|
| `TimpaniGenerator` | `orchestral_percussion.py` | `stroke_pattern="single"`, `drum_count=4`, `tuning_follows=True`, `roll_speed=0.125` |
| `MalletPercussionGenerator` | `orchestral_percussion.py` | `instrument="marimba"`, `pattern="arpeggio"`, `mallet_count=2` |

## Orchestral Unpitched Percussion

| Class | File | Key params |
|-------|------|------------|
| `BassDrumGenerator` | `orchestral_unpitched_percussion.py` | `pattern_type="single"` (`"single"`, `"roll"`, `"march"`) |
| `TamTamGenerator` | `orchestral_unpitched_percussion.py` | `pattern_type="strike"` (`"strike"`, `"crescendo_strike"`, `"tremolo"`) |
| `GongGenerator` | `orchestral_unpitched_percussion.py` | `pattern_type="strike"` (`"strike"`, `"roll"`, `"crescendo"`) |
| `TriangleGenerator` | `orchestral_unpitched_percussion.py` | `pattern_type="single"` (`"single"`, `"roll"`, `"trill"`) |
| `CastanetsGenerator` | `orchestral_unpitched_percussion.py` | `pattern_type="single"` (`"single"`, `"roll"`, `"rhythm"`) |

## Orchestral Score & Transitions

| Class | File | Key params |
|-------|------|------------|
| `OrchestralScoreGenerator` | `orchestral_score.py` | `sections=None`, `texture=Texture.FULL`, `include_choir=True`, `include_harp=True`, `include_brass=True` |
| `OrchestralTransitionGenerator` | `orchestral_transition.py` | `transition_type="crescendo_build"`, `target_chord=None`, `intensity_curve="crescendo"` |
| `OrchestralHitGenerator` | `orchestral_hit.py` | `hit_type="staccato"`, `voicing="chord"`, `duration=0.5`, `reverb_tail=2.0` |
| `OrchestralCymbalGenerator` | `orchestral_cymbal.py` | `pattern_type="crash"` |

## String Ensembles

| Class | File | Key params |
|-------|------|------------|
| `StringsEnsembleGenerator` | `strings_ensemble.py` | `section_size="full"`, `articulation="sustained"`, `divisi=4`, `dynamic_curve="flat"` |
| `StringsLegatoGenerator` | `strings_legato.py` | (params present) |
| `StringsPizzicatoGenerator` | `strings_pizzicato.py` | `pattern="ostinato"`, `staccato_length=0.15`, `velocity_variation=0.3`, `section_divisi=2` |
| `StringsStaccatoGenerator` | `staccato.py` | `style="octaves"`, `note_range_low/high=None` |
| `TremoloStringsGenerator` | `tremolo_strings.py` | `variant="chord"`, `bow_speed=0.0625`, `dynamic_swell=True`, `attack_time=0.5`, `decay_time=0.5` |

## Woodwinds Ensemble

| Class | File | Key params |
|-------|------|------------|
| `WoodwindsEnsembleGenerator` | `woodwinds_ensemble.py` | `section="quartet"`, `ensemble_mode="full"`, `articulation="legato"`, `dynamic_range=0.5`, `breath_interval=6.0` |

## Plucked / Keyboard Solo

| Class | File | Key params |
|-------|------|------------|
| `PianoSoloGenerator` | `plucked_solo.py` | `instrument="grand_piano"`, `pedal=True`, `note_density=1.0` |
| `AcousticGuitarGenerator` | `plucked_solo.py` | `style="fingerpicking"`, `acoustic_type="nylon"`, `note_density=1.0` |
| `EthnicPluckedGenerator` | `plucked_solo.py` | `instrument="sitar"`, `note_density=1.0` |

## Wind / Brass Solo

| Class | File | Key params |
|-------|------|------------|
| `MutedTrumpetGenerator` | `wind_brass_solo.py` | `plunger_wah=True`, `note_density=1.0` |
| `SynthBrassGenerator` | `wind_brass_solo.py` | `brass_type="synth_brass_1"`, `harmony_count=3`, `note_density=1.0` |
| `WoodwindSoloGenerator` | `wind_brass_solo.py` | `instrument="recorder"`, `breath_vibrato=True`, `note_density=1.0` |

## Saxophone

| Class | File | Key params |
|-------|------|------------|
| `SaxSoloGenerator` | `sax_solo.py` | `style="bebop"`, `vibrato_depth=0.3` |

## Chromatic Percussion

| Class | File | Key params |
|-------|------|------------|
| `CelestaGenerator` | `chromatic_percussion.py` | `note_density=1.0` |
| `GlockenspielGenerator` | `chromatic_percussion.py` | `note_density=1.0` |
| `MusicBoxGenerator` | `chromatic_percussion.py` | `note_density=1.0` |
| `VibraphoneGenerator` | `chromatic_percussion.py` | `note_density=1.0` |
| `MarimbaGenerator` | `chromatic_percussion.py` | `note_density=1.0` |
| `XylophoneGenerator` | `chromatic_percussion.py` | `note_density=1.0` |
| `DulcimerGenerator` | `chromatic_percussion.py` | `note_density=1.0` |

## SFX Percussion

| Class | File | Key params |
|-------|------|------------|
| `SFXPercussionGenerator` | `sfx_percussion.py` | `instrument="tinkle_bell"`, `note_density=1.0` |

## Tubular Bells & Timpani

| Class | File | Key params |
|-------|------|------------|
| `TubularBellsGenerator` | `tubular_bells.py` | `stroke_pattern="single"`, `dampen=False` |
| `TubaGenerator` | `tuba.py` | `articulation="sustained"`, `mute=False`, `growl=False`, `breath_gap=0.3` |

## Keyboard Sustained

| Class | File | Key params |
|-------|------|------------|
| `ChurchOrganGenerator` | `keyboard_sustained.py` | `stops="diapason"`, `note_density=1.0` |
| `AccordionGenerator` | `keyboard_sustained.py` | `register="master"`, `tango_mode=False`, `note_density=1.0` |
| `HarmonicaGenerator` | `keyboard_sustained.py` | `blues_harp=True`, `note_density=1.0` |
| `PercussiveOrganGenerator` | `keyboard_sustained.py` | `click_octave_offset=2`, `note_density=1.0` |
| `RockOrganGenerator` | `keyboard_sustained.py` | `leslie_speed_hz=6.5`, `note_density=1.0` |
| `ReedOrganGenerator` | `keyboard_sustained.py` | `note_density=1.0` |

## Piano / Keys

| Class | File | Key params |
|-------|------|------------|
| `PianoCompGenerator` | `piano_comp.py` | `comp_style="jazz"`, `voicing_type="shell"`, `accent_pattern="2_4"`, `chord_density=0.7` |
| `KeysArpeggioGenerator` | `keys_arpeggio.py` | `arp_pattern="up"`, `rate=0.125`, `octave_spread=2`, `swing=0.0` |
| `StridePianoGenerator` | `stride_piano.py` | `pattern="standard"` |
| `PianoRunGenerator` | `piano_run.py` | `direction="up"`, `scale_steps=False`, `technique=None`, `motion="up_down"`, `notes_per_run=4` |
| `OrganDrawbarsGenerator` | `organ_drawbars.py` | `registration="jazz"`, `leslie_speed="slow"`, `percussion=True`, `sustain_bars=1.0` |

## Guitar

| Class | File | Key params |
|-------|------|------------|
| `GuitarStrummingGenerator` | `guitar_strumming.py` | `strum_pattern="folk"`, `palm_mute_ratio=0.2`, `accent_velocity=1.2`, `strum_delay=0.015`, `string_count=6` |
| `GuitarLegatoGenerator` | `guitar_legato.py` | `direction="ascending"`, `notes_per_string=4` |
| `GuitarSweepGenerator` | `guitar_sweep.py` | `sweep_direction="down"`, `note_count=5`, `speed=0.08`, `let_ring=False` |
| `GuitarTappingGenerator` | `guitar_tapping.py` | `pattern="arpeggio"`, `width_interval=12`, `notes_per_cycle=6` |
| `FingerpickingGenerator` | `fingerpicking.py` | `pattern=None`, `retrigger=0.0`, `sustain_notes="no"`, `strum_delay=0.0` |

## Bass

| Class | File | Key params |
|-------|------|------------|
| `BassGenerator` | `bass.py` | `style="root_only"`, `allowed_notes=None`, `global_movement="none"` |
| `BassSoloGenerator` | `bass_solo.py` | `instrument="finger"`, `style="groove"`, `note_density=1.0` |
| `BassSlapGenerator` | `bass_slap.py` | `slap_pattern="funky"`, `ghost_note_prob=0.3`, `pop_probability=0.4` |
| `BassWobbleGenerator` | `bass_wobble.py` | `wobble_rate="1/8"`, `waveform="saw"`, `lfo_shape="sine"` |
| `WalkingBassGenerator` | `walking_bass.py` | `approach_style="mixed"`, `connect_roots=True` |
| `AlbertiBassGenerator` | `alberti_bass.py` | `pattern="1-5-3-5"`, `subdivision=0.5`, `voice_lead=True` |
| `PedalBassGenerator` | `pedal_bass.py` | `pedal_note="root"`, `sustain=0.0`, `velocity_level=0.8` |
| `ModernBass2025Generator` | `modern_bass_2025.py` | `style="walking"` |

## Synth

| Class | File | Key params |
|-------|------|------------|
| `SynthBassGenerator` | `synth_bass.py` | `waveform="acid"`, `pattern="acid_line"` |
| `SynthLeadGenerator` | `synth_modern.py` | `lead_type="sawtooth"`, `glide_speed=0.1`, `note_density=1.0` |
| `SynthPadGenerator` | `synth_modern.py` | `pad_type="warm"`, `swell=True`, `note_density=1.0` |
| `SynthEffectsGenerator` | `synth_effects.py` | `fx_type="crystal"`, `note_density=1.0` |
| `LeadSynthGenerator` | `lead_synth.py` | `style="trance"`, `portamento=0.15` |
| `SupersawPadGenerator` | `supersaw_pad.py` | `variant="trance"` |
| `DarkPadGenerator` | `dark_pad.py` | `mode="minor_pad"`, `chord_dur=8.0` |
| `FilterSweepGenerator` | `filter_sweep.py` | `sweep_type="lowpass_open"`, `resonance=0.5`, `duration=4.0` |
| `SidechainPumpGenerator` | `sidechain_pump.py` | `rate="1/4"`, `depth=0.7`, `attack=0.01`, `release=0.2` |

## Synth Strings / Choir

| Class | File | Key params |
|-------|------|------------|
| `SynthStringsGenerator` | `synth_choir_strings.py` | `string_type="synth_strings_1"`, `harmony_count=3`, `note_density=1.0` |
| `VoiceOohsGMGenerator` | `synth_choir_strings.py` | (params present) |
| `SynthChoirGenerator` | `synth_choir_strings.py` | (params present) |

## Vocal

| Class | File | Key params |
|-------|------|------------|
| `VocalOohsGenerator` | `vocal_oohs.py` | `syllable="ooh"`, `harmony_count=3`, `vibrato=0.4`, `breath_phasing=True` |
| `ChoirAahsGenerator` | `choir_ahhs.py` | `voice_count=4`, `dynamics="mf"`, `vibrato=0.3`, `syllable="aah"` |
| `VocalAdlibsGenerator` | `vocal_adlibs.py` | `density_adlib=0.3`, `register="mid"`, `style="adlib"`, `phrase_variety=0.5` |
| `VocalChopsGenerator` | `vocal_chops.py` | `processing="pitch_shift"`, `density=0.6` |
| `VocalMelismaGenerator` | `vocal_melisma.py` | `style="rnb"`, `run_length=4`, `ornament_prob=0.4`, `vibrato_depth=0.3`, `register_center=60` |
| `VocalMelodyAutoGenerator` | `vocal_melody_auto.py` | `variant="travis"`, `register="mid"`, `sustain_preference=0.5`, `octave_jump_probability=0.15`, `grace_note_probability=0.2`, `repetition_amount=0.4` |

## Melody

| Class | File | Key params |
|-------|------|------------|
| `MelodyGenerator` | `melody.py` | `mode="downbeat_chord"`, `phrase_length=4.0`, `harmony_note_probability=0.64`, `random_movement=0.35`, `direction_bias=0.0`, `climax="auto"`, `after_leap="step_opposite"` |
| `MarkovMelodyGenerator` | `markov.py` | `transitions=None`, `note_repetition_probability=0.14`, `harmony_note_probability=0.64` |
| `NeuralMelodyGenerator` | `neural_melody.py` | `model_path=None`, `temperature=1.0`, `top_p=0.92`, `harmony_prob=0.55`, `device="cpu"` |
| `MicrotonalMelodyGenerator` | `microtonal_melody.py` | `phrase_length=8.0`, `bend_range=2`, `note_duration=2.0`, `velocity_range=(50,80)` |
| `SoloMelodyGenerator` | `solo_melody.py` | `style="blues_lick"`, `vibrato_depth=0.5`, `blues_notes=True`, `chromaticism=0.4` |
| `CountermelodyGenerator` | `countermelody.py` | `primary_melody=None` |

## Chords & Harmony

| Class | File | Key params |
|-------|------|------------|
| `ChordGenerator` | `chord_gen.py` | `voicing="closed"`, `notes_to_use=None`, `add_bass_note=0` |
| `ChordVoicingGenerator` | `chord_voicing.py` | (params present) |
| `ModernChordPatternGenerator` | `modern_chord.py` | `extension="add9"`, `stab_pattern="syncopated"`, `voicing="closed"` |
| `BrokenChordGenerator` | `broken_chord.py` | (params present) |
| `CadenceGenerator` | `cadence.py` | (params present) |
| `SecondaryDominantGenerator` | `secondary_dominant.py` | `strategy="secondary"` |
| `ModalInterchangeGenerator` | `modal_interchange.py` | `source_mode="minor"`, `frequency=0.3`, `voice_leading=True` |
| `ReharmonizationGenerator` | `reharmonization.py` | `strategy="tritone"`, `preservation="melody"`, `substitution_frequency=0.5` |
| `VoiceLeadingGenerator` | `voice_leading.py` | `voices=4`, `prefer_stepwise=True`, `avoid_parallels=True`, `range_style="close"` |
| `ChoraleGenerator` | `chorale.py` | `voice_spacing=12`, `soprano_motion="stepwise"`, `rhythmic_unit=1.0`, `doubling_preference="auto"` |
| `CounterpointGenerator` | `counterpoint.py` | `species=1`, `voices=2`, `cantus_position="below"` |

## Arpeggio & Ostinato

| Class | File | Key params |
|-------|------|------------|
| `ArpeggiatorGenerator` | `arpeggiator.py` | `pattern="up"`, `note_duration=0.25`, `voicing="closed"`, `octaves=1` |
| `OstinatoGenerator` | `ostinato.py` | `pattern=None`, `shape=None`, `use_scale_degrees=True`, `repeat_notes=1`, `pattern_length=None` |
| `PluckSequenceGenerator` | `pluck_sequence.py` | `pattern="offbeat"`, `decay_time=0.3`, `pitch_randomization=0.0`, `pitch_range=3` |

## Drums & Percussion

| Class | File | Key params |
|-------|------|------------|
| `ElectronicDrumsGenerator` | `electronic_drums.py` | `style="rock"`, `hihat_pattern="eighth"`, `fill_frequency=0.2`, `section_type="verse"`, `auto_fills=True`, `groove_swing=0.5` |
| `DrumKitPatternGenerator` | `drum_kit_pattern.py` | `kit="909"`, `pattern="four_on_floor"`, `sidechain=False`, `section_type="verse"`, `auto_fills=True`, `groove_swing=0.5` |
| `TrapDrumsGenerator` | `trap_drums.py` | `variant="standard"`, `hat_roll_density=0.5`, `kick_pattern="standard"`, `open_hat_probability=0.2`, `clap_on_two=True`, `sidechain_depth=0.6` |
| `BoomBapGenerator` | `boom_bap.py` | `variant="classic"`, `swing_ratio=0.58`, `chop_density=0.4` |
| `BreakbeatGenerator` | `breakbeat.py` | `variant="amen"`, `chop_probability=0.3`, `ghost_notes=True`, `double_time=False` |
| `FourOnFloorGenerator` | `four_on_floor.py` | `variant="house"`, `hihat_style="mixed"`, `clap_location="2_4"`, `swing=0.0` |
| `PercussionGenerator` | `percussion.py` | `pattern_name="rock"`, `instruments=None`, `velocity_humanize=10` |
| `PercussionEnsembleGenerator` | `percussion_ensemble.py` | `instruments=None`, `density=0.6`, `polyrhythm_ratio="3x2"` |
| `SnareDrumGenerator` | `snare_drum.py` | `pattern_type="march"` |
| `HiHatStutterGenerator` | `hihat_stutter.py` | `pattern="trap_eighth"`, `roll_density=0.4`, `open_hat_probability=0.15`, `instrument="hh_closed"`, `pan_mode="alternate"` |
| `GhostNotesGenerator` | `ghost_notes.py` | `target="snare"`, `pattern="funk"`, `ghost_velocity=35` |
| `RhythmicAccentGenerator` | `accent.py` | `preset="march"`, `pitch=None`, `octave=3`, `accent_strength=1.0` |
| `BackbeatGenerator` | `backbeat.py` | `mode="accent"`, `accent_velocity=1.0` |

## Ethnic / World

| Class | File | Key params |
|-------|------|------------|
| `EthnicWorldGenerator` | `ethnic_world.py` | `instrument="banjo"`, `note_density=1.0` |
| `HarpGenerator` | `harp.py` | (params present) |

## Drone & Ambient

| Class | File | Key params |
|-------|------|------------|
| `DroneGenerator` | `drone.py` | `variant="tonic"`, `fade_in=0.0`, `fade_out=0.0` |
| `AmbientPadGenerator` | `ambient.py` | `voicing="spread"`, `overlap=0.1`, `note_range_low/high=None` |
| `NebulaGenerator` | `nebula.py` | `variant="cloud"`, `density_notes=5`, `pitch_spread=12`, `note_duration=3.0`, `overlap=0.5` |
| `SciFiUnderscoreGenerator` | `scifi_underscore.py` | `variant="blade_runner"`, `pad_density=0.6`, `arp_speed=0.25`, `include_bass_synth=True` |

## FX

| Class | File | Key params |
|-------|------|------------|
| `FXImpactGenerator` | `fx_impact.py` | `impact_type="boom"`, `tail_length=2.0`, `pitch_drop=12`, `placement="downbeat"` |
| `FXRiserGenerator` | `fx_riser.py` | `riser_type="synth"`, `length_beats=4.0`, `pitch_curve="exponential"` |
| `TransitionGenerator` | `transition.py` | `transition_type="build"`, `length_beats=8.0` |
| `BeatRepeatGenerator` | `beat_repeat.py` | `repeat_type="accelerate"`, `stutter_length=2.0` |
| `StingerGenerator` | `stinger.py` | `stinger_type="discovery"` |

## 808 / Trap Bass

| Class | File | Key params |
|-------|------|------------|
| `Bass808SlidingGenerator` | `bass_808_sliding.py` | `pattern="trap_basic"`, `slide_type="overlap"`, `slide_probability=0.4`, `slide_curve="exponential"` |
| `DarkBassGenerator` | `dark_bass.py` | (params present) |

## Genre: Hip-Hop / Rap

| Class | File | Key params |
|-------|------|------------|
| `MelodicRapGenerator` | `melodic_rap.py` | `variant="sing_rap"`, `repetition_factor=0.5`, `stepwise_bias=0.7`, `bend_probability=0.15`, `phrase_length=4.0` |
| `CloudRapGenerator` | `cloud_rap.py` | `variant="cloud"`, `pad_density=0.6`, `drum_sparseness=0.5`, `arp_speed="slow"` |
| `DrillPatternGenerator` | `drill_pattern.py` | `variant="uk_drill"`, `slide_amount=7`, `stutter_intensity=0.5` |
| `RageBeatGenerator` | `rage_beat.py` | `variant="carti"`, `synth_distortion=0.8`, `hat_speed="sixteenth"` |

## Genre: Electronic / Dance

| Class | File | Key params |
|-------|------|------------|
| `SynthwaveGenerator` | `synthwave.py` | `variant="outrun"`, `arp_pattern="up"`, `gated_pads=True` |
| `FutureBassGenerator` | `future_bass.py` | `variant="standard"`, `chord_chop_rate=0.5`, `sidechain_feel=True` |
| `DnBJungleGenerator` | `dnb_jungle.py` | `variant="liquid"`, `break_density=0.6`, `reese_amount=0.5`, `sub_weight=0.7` |
| `HardstyleGenerator` | `hardstyle.py` | `variant="euphoric"`, `kick_distortion=0.8`, `include_lead=True`, `reverse_bass_weight=0.5` |
| `HyperpopGenerator` | `hyperpop.py` | `variant="standard"`, `pitch_shift_range=12`, `glitch_density=0.4`, `distortion_amount=0.5`, `chaos_factor=0.3` |
| `LoFiHipHopGenerator` | `lofi_hiphop.py` | `variant="chill"`, `swing_ratio=0.62`, `chord_voicing="ninth"`, `vinyl_noise=0.3`, `tape_stop=0.1` |
| `ChiptuneGenerator` | `chiptune.py` | `variant="nes_classic"`, `channels=None` |
| `WitchHouseGenerator` | `witch_house.py` | `variant="classic"`, `slowdown_factor=0.5`, `pad_darkness=0.8` |

## Genre: Afro / Latin

| Class | File | Key params |
|-------|------|------------|
| `AfroHouseGenerator` | `afro_house.py` | `variant="deep"`, `percussion_density=0.6`, `include_marimba=True`, `bass_depth=0.7` |
| `AfroDrillGenerator` | `afro_drill.py` | `variant="burna"`, `slide_amount=7`, `melody_density=0.6` |
| `AfroPercussionGenerator` | `afro_percussion.py` | `ensemble="west_african"`, `density=0.6`, `include_pitched=True` |
| `AfroSambaGenerator` | `afro_samba.py` | `variant="samba_afro"`, `perc_density=0.7`, `include_guitar=True` |
| `AfrobeatsGenerator` | `afrobeats.py` | (params present) |
| `AmapianoLogDrumGenerator` | `amapiano_logdrum.py` | (params present) |
| `DembowGenerator` | `dembow.py` | `variant="classic"`, `shaker_density=0.7`, `include_bass=True` |
| `LatinTrapGenerator` | `latin_trap.py` | `variant="reggaeton_trap"`, `dembow_influence=0.6`, `hat_rolls=True`, `include_percussion=True` |
| `BaileFunkGenerator` | `baile_funk.py` | `variant="classic"`, `bass_distortion=0.7`, `percussion_density=0.6` |
| `BongoFlavaGenerator` | `bongo_flava.py` | `variant="modern"`, `melody_density=0.6`, `include_percussion=True` |
| `GqomGenerator` | `gqom.py` | `variant="classic"`, `kick_weight=0.8`, `include_vocal_stabs=True` |
| `KuduroGenerator` | `kuduro.py` | `variant="kuduro"`, `intensity=0.7` |
| `JerseyClubGenerator` | `jersey_club.py` | `variant="classic"`, `kick_triplet_density=0.7`, `stutter_breaks=True` |
| `HighlifeGuitarGenerator` | `highlife_guitar.py` | (params present) |
| `SoukousGuitarGenerator` | `soukous_guitar.py` | `variant="soukous"`, `run_speed="sixteenth"`, `note_density=0.8` |
| `MontunoGenerator` | `montuno.py` | (params present) |

## Genre: Phonk / UK

| Class | File | Key params |
|-------|------|------------|
| `PhonkGenerator` | `phonk.py` | `variant="classic_phonk"`, `cowbell_density=0.7`, `bass_slide_amount=5`, `filter_cutoff=0.4`, `aggression=0.6` |
| `PhonkHouseGenerator` | `phonk_house.py` | `variant="drift_house"`, `cowbell_density=0.6`, `bass_slides=True` |
| `GrimeGenerator` | `grime.py` | `variant="classic"`, `synth_aggression=0.7`, `include_melody=True` |
| `PluggnbGenerator` | `pluggnb.py` | `variant="pluggnb"`, `pad_voicing="ninth"`, `include_808=True` |
| `UKGarageGenerator` | `uk_garage.py` | (params present) |

## Genre: Metal / Rock

| Class | File | Key params |
|-------|------|------------|
| `PowerChordGenerator` | `power_chord.py` | `pattern="chug"`, `include_octave=True` |
| `RiffGenerator` | `riff.py` | `scale_type="minor_pent"`, `riff_pattern="gallop"`, `palm_mute_prob=0.3`, `power_chord=True` |
| `TremoloPickingGenerator` | `tremolo_picking.py` | `variant="single"`, `speed=0.125`, `palm_mute_probability=0.0`, `note_strategy="chord_root"` |

## Genre: Cinematic / Game

| Class | File | Key params |
|-------|------|------------|
| `FilmScoreGenerator` | `film_score.py` | `hit_points=None`, `emotional_arcs=None`, `default_mood="neutral"`, `include_choir=True`, `include_brass=True`, `include_harp=True` |
| `BossBattleGenerator` | `boss_battle.py` | `phase="fight"`, `variant="epic"`, `choir_stabs=True` |
| `CombatEscalationGenerator` | `combat_escalation.py` | `intensity=0.5`, `layers=None`, `tempo_factor=1.0`, `key_change_on_climax=True` |
| `StealthStateGenerator` | `stealth_state.py` | `stealth_state="hidden"`, `transition_speed=0.5`, `heartbeat=True` |
| `VictoryFanfareGenerator` | `victory_fanfare.py` | `variant="victory"`, `register=5`, `dynamics="forte"` |
| `HorrorDissonanceGenerator` | `horror_dissonance.py` | `variant="psychological"`, `dissonance_level=0.7` |
| `MedievalTavernGenerator` | `medieval_tavern.py` | `variant="tavern"`, `mode="dorian"`, `lute_density=0.7` |

## Theory / Composition Tools

| Class | File | Key params |
|-------|------|------------|
| `AleatoricGenerator` | `aleatoric.py` | `mode="tone_cluster"` (`"tone_cluster"`, `"chance_operations"`, `"repeat_ad_lib"`, `"graphic_score"`, `"pointillist"`, `"textural_cloud"`) |
| `CanonGenerator` | `canon.py` | `canon_type="tonal"`, `delay_beats=DEFAULT`, `interval=7`, `num_followers=1`, `subject_length=4.0` |
| `CallResponseGenerator` | `call_response.py` | `call_length=2.0`, `response_length=2.0`, `call_direction="up"`, `response_direction="down"` |
| `HemiolaGenerator` | `hemiola.py` | (params present) |
| `PolyrhythmGenerator` | `polyrhythm.py` | `ratio="3x2"`, `stream_a_pitch="chord_root"` |
| `EuclideanRhythmGenerator` | `euclidean_rhythm.py` | `pulses=5`, `steps=8`, `pitch="chord_root"`, `velocity_accent=True` |
| `TensionGenerator` | `tension.py` | `mode="semitone_cluster"`, `note_duration=2.0` |
| `SwingGenerator` | `swing.py` | `swing_ratio=0.67`, `subdivision=0.5`, `pitch_strategy="chord_tone"`, `accent_pattern="downbeat"` |
| `GrooveGenerator` | `groove.py` | `groove_pattern="funk_1"`, `ghost_note_vel=30`, `accent_vel=110` |
| `SequenceGenerator` | `sequence.py` | (params present) |
| `MotifDevelopmentGenerator` | `motif_development.py` | (params present) |
| `MotiveGenerator` | `motive.py` | `motive_length=4`, `development="transpose"`, `interval_seed=None` |
| `PhraseContainer` | `phrase_container.py` | `mode="sequential"`, `layers=None` |
| `PhraseMorpher` | `phrase_morpher.py` | `source_notes=None`, `target_notes=None`, `steps=8` |

## Ornaments & Articulation

| Class | File | Key params |
|-------|------|------------|
| `TrillTremoloGenerator` | `trill.py` | `ornament_type="trill"`, `speed=0.125`, `base_note_strategy="chord_tone"`, `neighbor_interval="auto"` |
| `AcciaccaturaGenerator` | `acciaccatura.py` | `grace_type="lower"`, `grace_duration=0.08`, `main_duration=0.75`, `interval=0`, `density=0.7` |
| `BendGenerator` | `bend.py` | `bend_type="bend_up"`, `bend_range=2` |
| `GlissandoGenerator` | `glissando.py` | `gliss_type="chromatic"`, `speed=0.0625` |
| `OrnamentationGenerator` | `ornamentation.py` | (params present) |
| `HarmonicsGenerator` | `harmonics.py` | `harmonic_type="natural"`, `use_chord_tones=True`, `duration_per_note=2.0`, `velocity_pp=True` |

## Utility / Meta

| Class | File | Key params |
|-------|------|------------|
| `GenericGenerator` | `generic_gen.py` | `chord_note_ratio=0.7`, `partial_polyphony=0.2`, `max_polyphony=3` |
| `HumanizerGenerator` | `humanizer.py` | `timing_variance=0.03`, `velocity_variance=0.1`, `pitch_drift=0.0`, `groove_type="straight"` |
| `DynamicsCurveGenerator` | `dynamics.py` | (params present) |
| `RandomNoteGenerator` | `random_note.py` | `velocity_range=None`, `note_range=(36,84)` |
| `RestGenerator` | `rest.py` | (no extra params) |
| `DownbeatRestGenerator` | `downbeat_rest.py` | (params present) |
| `PickupGenerator` | `pickup.py` | `pickup_type="scale_down"`, `pickup_length=1.0`, `target_on_downbeat=True` |
| `HocketGenerator` | `hocket.py` | `hocket_pattern="alternating"`, `voice_index=0`, `euclidean_pulses=3`, `euclidean_steps=4` |
| `ClusterGenerator` | `clusters.py` | `cluster_type="second"`, `cluster_width=3` |
| `DyadGenerator` | `dyads.py` | `interval_pref=None`, `min_interval=3`, `motion_mode="random"` |
| `DyadsRunGenerator` | `dyads_run.py` | `interval=3`, `technique="up"`, `notes_per_run=8` |
| `StepSequencer` | `step_seq.py` | `steps=16`, `gate_prob=0.75`, `velocity_map=None`, `ties=None` |
| `AdvancedStepSequencer` | `advanced_step_seq.py` | (keyword params via StepLane) |
| `BPMAdaptiveGenerator` | `bpm_adaptive.py` | (params present) |
| `SectionBuilderGenerator` | `section_builder.py` | `section_type="verse"`, `pattern="melody"`, `bars_per_section=4` |
| `ArrangerGenerator` | `arranger.py` | `form="verse_chorus"`, `section_length=8`, `variation_seed=0`, `use_orchestral=False` |
| `GenreFusionEngine` | `genre_fusion.py` | (params present) |
| `PedalMelodyGenerator` | `pedal_melody.py` | (params present) |
| `ProceduralExplorationGenerator` | `procedural_exploration.py` | `variant="nature"`, `mood="peaceful"`, `loop_length_bars=4`, `density=0.35` |
| `PuzzleLoopGenerator` | `puzzle_loop.py` | `variant="bells"`, `complexity=0.3`, `loop_bars=4`, `register="mid"` |
| `BluesLickGenerator` | `blues_lick.py` | `lick_style="standard"`, `phrase_length=4` |
| `BoogieWoogieGenerator` | `boogie_woogie.py` | `pattern="standard"`, `octave_bass=True`, `swing=0.67` |
| `RagtimeGenerator` | `ragtime.py` | `pattern="classic"`, `melody_density=0.8` |
| `WaltzGenerator` | `waltz.py` | `variant="viennese"`, `include_bass_octave=True`, `staccato_chords=True` |
| `TangoGenerator` | `tango.py` | `pattern="marcato"`, `accent=1.15`, `staccato_chords=True` |
| `StrumPatternGenerator` | `strum.py` | `strum_delay=0.02`, `voicing="guitar"`, `direction_pattern=None`, `density="medium"`, `polyphony=6` |
| `ReggaeSkankGenerator` | `reggae_skank.py` | `variant="skank"`, `staccato=True`, `mute_probability=0.1` |
| `FillGenerator` | `fills.py` | (params present) |

---

## GM Programs (`_GM_PROGRAMS` in `idea_tool.py`)

| Name | GM# |
|------|-----|
| piano | 0 |
| bright_piano | 1 |
| electric_piano | 4 |
| harpsichord | 6 |
| celesta | 8 |
| glockenspiel | 9 |
| music_box | 10 |
| vibraphone | 11 |
| marimba | 12 |
| xylophone | 13 |
| tubular_bells | 14 |
| organ | 19 |
| accordion | 21 |
| harmonica | 22 |
| nylon_guitar | 24 |
| guitar / steel_guitar | 25 |
| jazz_guitar | 26 |
| electric_guitar | 27 |
| muted_guitar | 28 |
| overdrive_guitar | 29 |
| distortion_guitar | 30 |
| acoustic_bass | 32 |
| bass | 33 |
| electric_bass | 34 |
| fretless_bass | 35 |
| slap_bass | 36 |
| synth_bass | 38 |
| violin | 40 |
| viola | 41 |
| cello | 42 |
| contrabass | 43 |
| tremolo_strings | 44 |
| pizzicato | 45 |
| harp | 46 |
| timpani | 47 |
| strings | 48 |
| choir | 52 |
| voice / synth_voice | 54 |
| orchestra_hit | 55 |
| trumpet | 56 |
| trombone | 57 |
| tuba | 58 |
| french_horn | 60 |
| brass | 61 |
| synth_brass | 62 |
| soprano_sax | 64 |
| alto_sax | 65 |
| tenor_sax | 66 |
| baritone_sax | 67 |
| oboe | 68 |
| english_horn | 69 |
| bassoon | 70 |
| clarinet | 71 |
| piccolo | 72 |
| flute | 73 |
| recorder | 74 |
| pan_flute | 75 |
| shakuhachi | 77 |
| whistle | 78 |
| ocarina | 79 |
| synth_lead | 80 |
| dark_pad | 88 |
| pad | 89 |
| synth_fx | 102 |
| sitar | 104 |
| banjo | 105 |
| shamisen | 106 |
| koto | 107 |
| kalimba | 108 |
| bagpipe | 109 |
| fiddle | 110 |
| shanai | 111 |
| tinkle_bell | 112 |
| steel_drums | 114 |
| taiko | 116 |
| drums / percussion | 0 (ch9) |
