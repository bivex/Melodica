# Generators Reference

Все генераторы наследуют `PhraseGenerator` и реализуют `render(chords, key, duration_beats, context) -> list[NoteInfo]`.

Factory type string → class через `create_generator()`.

**Всего: 166 генераторов.**

---

## Содержание

1. [Melody & Lead](#melody--lead) — 8
2. [Bass](#bass) — 9
3. [Chords & Harmony](#chords--harmony) — 7
4. [Arpeggios & Broken Chords](#arpeggios--broken-chords) — 3
5. [Ostinato & Riff](#ostinato--riff) — 3
6. [Ornamentation & Articulation](#ornamentation--articulation) — 5
7. [Guitar Techniques](#guitar-techniques) — 6
8. [Guitar (расширенные)](#гитара-расширенные) — 3
9. [Fills & Transitions](#fills--transitions) — 2
10. [FX & Production](#fx--production) — 2
11. [Rhythm & Drums — базовые](#rhythm--drums--базовые) — 7
12. [Ударные (расширенные)](#ударные-расширенные) — 3
13. [Modern Beats — Trap/Drill/Hip-Hop](#modern-beats--trapdrillhip-hop) — 12
14. [Urban & Club](#urban--club) — 10
15. [Afro Beats](#afro-beats) — 11
16. [Game Audio / AAA](#game-audio--aaa) — 11
17. [Synth & Electronic](#synth--electronic) — 6
18. [Orchestral Articulations](#orchestral-articulations) — 4
19. [Оркестр (расширенные)](#оркестр-расширенные) — 3
20. [Клавишные](#клавишные) — 3
21. [Genre-Specific (classic)](#genre-specific-classic) — 5
22. [Texture & Ambient](#texture--ambient) — 5
23. [Vocals & Samples](#vocals--samples) — 3
24. [Вокал](#вокал) — 3
25. [Harmony & Theory](#harmony--theory) — 5
26. [Meta & Structure](#meta--structure) — 2
27. [Utility](#utility) — 7

---

## Melody & Lead — 8 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `melody` | MelodyGenerator | Основной мелодический голос. Ступеневое движение, тоника аккорда |
| `markov` | MarkovMelodyGenerator | Мелодия через цепи Маркова |
| `call_response` | CallResponseGenerator | Вопрос-ответ: фраза → контрастный ответ |
| `countermelody` | CountermelodyGenerator | Независимый контрапунктный голос (contrary/oblique motion) |
| `sequence` | SequenceGenerator | Транспозиция мотива: diatonic/chromatic/fifths/ascending/descending |
| `blues_lick` | BluesLickGenerator | Блюзовые фразы с b3/b5/b7, бенды, энклоужеры |
| `motive` | MotiveGenerator | Развитие короткой мотивной ячейки (2–6 нот) |
| `piano_run` | PianoRunGenerator | Виртуозные фортепианные пассажи |

## Bass — 9 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `bass` | BassGenerator | Универсальный бас: root/chord_tone/walking/octave |
| `walking_bass` | WalkingBassGenerator | Джазовый walking bass (1 нота на долю, хроматические подходы) |
| `alberti_bass` | AlbertiBassGenerator | Классический альберти-бас: root–5–3–5 |
| `boogie_woogie` | BoogieWoogieGenerator | Буги-вуги левая рука: 8-нотные остинато |
| `stride_piano` | StridePianoGenerator | Stride piano: бас(1,3)–аккорд(2,4) |
| `pedal_bass` | PedalBassGenerator | Органный педаль-пойнт |
| `pedal_melody` | PedalMelodyGenerator | Дрон + мелодия (pedal bass + верхний голос) |
| `synth_bass` | SynthBassGenerator | Acid/reese/sub/wobble электронный бас |
| `dark_bass` | DarkBassGenerator | Тёмный бас: doom/trip_hop/dub/drone |

## Chords & Harmony — 7 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `chord` | ChordGenerator | Блочные аккорды: closed/open/spread/shell/power/cluster |
| `modern_chord` | ModernChordPatternGenerator | Современные аккордовые паттерны |
| `strum` | StrumPatternGenerator | Гитарный бой: down/up/folk/country/ska |
| `chorale` | ChoraleGenerator | 4-голосный хорал SATB с голосоведением |
| `cadence` | CadenceGenerator | Каденции: PAC/IAC/plagal/deceptive/half/backdoor/phrygian/neapolitan |
| `reharmonization` | ReharmonizationGenerator | Замена аккордов: tritone/diatonic/secondary_dom/chromatic_mediant |
| `modal_interchange` | ModalInterchangeGenerator | Заимствованные аккорды из параллельных ладов |

## Arpeggios & Broken Chords — 3 генератора

| Тип | Класс | Описание |
|-----|-------|----------|
| `arpeggiator` | ArpeggiatorGenerator | Арпеджио: up/down/up-down/random/inside-out |
| `broken_chord` | BrokenChordGenerator | Расширенные фигурации: Chopin/Debussy/Liszt/rolling |
| `fingerpicking` | FingerpickingGenerator | Гитарный fingerpicking: Travis/classical/folk |

## Ostinato & Riff — 3 генератора

| Тип | Класс | Описание |
|-----|-------|----------|
| `ostinato` | OstinatoGenerator | Повторяющийся паттерн над меняющейся гармонией |
| `riff` | RiffGenerator | Гитарные/басовые риффы: pentatonic/power/blues |
| `groove` | GrooveGenerator | Грув-паттерны: funk/neo-soul/hip-hop |

## Ornamentation & Articulation — 5 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `ornamentation` | OrnamentationGenerator | Барочные орнаменты: mordent/turn/gruppetto/shake |
| `trill` / `tremolo` | TrillTremoloGenerator | Трели, тремоло, рулады |
| `acciaccatura` | AcciaccaturaGenerator | Grace notes: upper/lower/double/slide/chord |
| `bend` | BendGenerator | Бенды: bend_up/down, pre-bend, slide |
| `glissando` | GlissandoGenerator | Глиссандо: chromatic/diatonic/pentatonic/arpeggio |

## Guitar Techniques — 6 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `hocket` | HocketGenerator | Хоукет: чередование нот между голосами |
| `power_chord` | PowerChordGenerator | Power chords: chug/gallop/offbeat/staccato |
| `tremolo_picking` | TremoloPickingGenerator | Tremolo picking: быстрое повторение ноты |
| `harmonics` | HarmonicsGenerator | Гитарные флажолеты: natural/artificial/tap/harp |
| `guitar_legato` | GuitarLegatoGenerator | Легато: hammer-on/pull-off runs |
| `guitar_tapping` | GuitarTappingGenerator | Тэппинг двумя руками |

## Гитара (расширенные) — 3 генератора

| Тип | Класс | Описание |
|-----|-------|----------|
| `guitar_strumming` | GuitarStrummingGenerator | Продвинутый бой: динамика, palm-mute, dead strums |
| `bass_slap` | BassSlapGenerator | Слэп: thumb slap, finger pop, ghost notes |
| `guitar_sweep` | GuitarSweepGenerator | Sweep picking: арпеджио одним движением медиатора |

## Fills & Transitions — 2 генератора

| Тип | Класс | Описание |
|-----|-------|----------|
| `fill` / `turnaround` | FillGenerator | Финальные заполнения, тёрнараунды |
| `pickup` | PickupGenerator | Анакруза: вступительные ноты перед downbeat |

## FX & Production — 2 генератора

| Тип | Класс | Описание |
|-----|-------|----------|
| `fx_riser` | FXRiserGenerator | Райзеры: noise/synth/orch/arp/sub_drop |
| `fx_impact` | FXImpactGenerator | Импакты: boom/hit/reverse_cymbal/downlifter |

---

## Rhythm & Drums — базовые — 7 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `percussion` | PercussionGenerator | Универсальные перкуссионные паттерны |
| `polyrhythm` | PolyrhythmGenerator | Полиритмия: 3x2, 5x4, 3x4, 7x8 |
| `beat_repeat` | BeatRepeatGenerator | Stutter/gate: accelerate/decelerate/glitch/reverse |
| `tremolo_strings` | TremoloStringsGenerator | Струнное тремоло (bow tremolo) |
| `trap_drums` | TrapDrumsGenerator | Трэп: hi-hat rolls, 808, snare 2+4 |
| `four_on_floor` | FourOnFloorGenerator | Four-on-the-floor: house/techno/disco/progressive |
| `breakbeat` | BreakbeatGenerator | Breakbeat: amen/funky/think/dnb/idm |

## Ударные (расширенные) — 3 генератора

| Тип | Класс | Описание |
|-----|-------|----------|
| `drum_kit_pattern` | DrumKitPatternGenerator | Полноценные драм-паттерны: rock/jazz/latin/funk/hiphop |
| `percussion_ensemble` | PercussionEnsembleGenerator | Ансамбль перкуссии: конги, бонго, шейкеры |
| `electronic_drums` | ElectronicDrumsGenerator | Электронные ударные: 909/808/cr78/linn |

---

## Modern Beats — Trap/Drill/Hip-Hop — 12 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `bass_808_sliding` | Bass808SlidingGenerator | 808 bass с pitch slides: trap_basic/trap_syncopated/drill_sliding/half_time/rolling |
| `hihat_stutter` | HiHatStutterGenerator | Hi-hat stutter rolls, triplets, velocity waves: trap_eighth/trap_triplet/drill_stutter/rapid_fire/sparse/velocity_wave |
| `drill_pattern` | DrillPatternGenerator | Полный UK/NY drill: sliding 808, stutter hats, displaced snares, dark piano. Варианты: uk_drill/ny_drill/melodic_drill/dark_drill |
| `ghost_notes` | GhostNotesGenerator | Ghost notes для реалистичных drums: snare/kick/hihat/tom. Паттерны: funk/hiphop/jazz/linear |
| `lofi_hiphop` | LoFiHipHopGenerator | Lo-fi hip-hop: dusty 7th/9th chords, swing drums, vinyl noise, tape stop. Варианты: chill/jazzy/nostalgic/upbeat |
| `phonk` | PhonkGenerator | Phonk/Memphis: cowbell, drift slides, Memphis chops. Варианты: classic_phonk/drift_phonk/lofi_phonk/aggressive |
| `melodic_rap` | MelodicRapGenerator | Auto-tune friendly мелодии с grace notes. Варианты: sing_rap/auto_tune/melodic_trap/hook |
| `rage_beat` | RageBeatGenerator | Distorted synth leads, aggressive 808. Варианты: carti/destroy/ken/rage |
| `pluggnb` | PluggnbGenerator | Мягкие pads 7th/9th, 808 slides, minimal drums. Варианты: pluggnb/plugg/melodic/dark_plugg |
| `boom_bap` | BoomBapGenerator | Classic hip-hop: dusty drums, MPC swing, jazz chops. Варианты: classic/jazz_hop/golden_age/dusty |
| `advanced_step_seq` | AdvancedStepSequencer | Grid-sequencer: velocity layers, probability, ratchets, micro-timing. Пресеты: four_on_floor/breakbeat/trap/techno/dnb |
| `bpm_adaptive` | BPMAdaptiveGenerator | Обёртка для адаптации плотности к BPM. Режимы: linear/logarithmic/genre_safe |

## Urban & Club — 10 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `jersey_club` | JerseyClubGenerator | Jersey/TikTok Club: triplet kick bounce, stutter breaks, chopped samples. Варианты: classic/tiktok/dark/bedroom |
| `dembow` | DembowGenerator | Dancehall/Reggaeton: dembow rhythm, shakers, cowbell. Варианты: classic/reggaeton/dancehall/moombahton |
| `baile_funk` | BaileFunkGenerator | Brazilian Phonk/Funk: tamborzão percussion, MC chops. Варианты: classic/phonk_br/mandela/rasterinha |
| `latin_trap` | LatinTrapGenerator | Latin trap fusion: dembow + trap drums. Варианты: reggaeton_trap/urbano/spanish_trap/bachata_trap |
| `uk_garage` | UKGarageGenerator | UK Garage/2-Step: shuffle, skippy hats, vocal chops. Варианты: 2step/speed_garage/bassline/dark_garage |
| `hyperpop` | HyperpopGenerator | Hyperpop/Glitch: pitch-shifted chops, chaos. Варианты: standard/glitch/bubblegum/deconstructed |
| `dnb_jungle` | DnBJungleGenerator | DnB/Jungle: breakbeat chops, reese bass. Варианты: liquid/jungle/neurofunk/minimal |
| `hardstyle` | HardstyleGenerator | Hardstyle: distorted kick, reverse bass, screech leads. Варианты: euphoric/raw/reverse/classic |
| `synthwave` | SynthwaveGenerator | Synthwave/Retrowave: gated pads, arp bass. Варианты: outrun/chillwave/darksynth/retro_pop |
| `future_bass` | FutureBassGenerator | Future Bass: supersaw chops, sidechain feel, vocal chops. Варианты: standard/festival/chill/wave_race |
| `witch_house` | WitchHouseGenerator | Witch House: slowed, dark pads, dissonant clusters. Варианты: classic/drag/dark_ambient/occult |
| `phonk_house` | PhonkHouseGenerator | Phonk + House fusion: cowbell, drift bass. Варианты: drift_house/dark_house/brazilian/classic |
| `grime` | GrimeGenerator | UK Grime: square wave synths, 140 BPM. Варианты: classic/eskibeat/weightless/modern |

## Afro Beats — 11 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `afrobeats` | AfrobeatsGenerator | Afrobeats/Amapiano: log drums, shakers, piano. Варианты: afrobeats/amapiano/afro_pop/afro_rock |
| `amapiano_logdrum` | AmapianoLogDrumGenerator | Детальные log drum паттерны с pitch variations, ghost notes. Варианты: classic/kabza/dj_maphorisa/mellow/percussive |
| `afro_percussion` | AfroPercussionGenerator | Djembe, congas, shekere, balafon. Ансамбли: west_african/cuban_afro/south_african/east_african |
| `highlife_guitar` | HighlifeGuitarGenerator | West African guitar riffs: highlife/afrobeat/juju/palm_wine |
| `afro_house` | AfroHouseGenerator | Black Coffee style: marimba, deep bass. Варианты: deep/spiritual/tech/organic |
| `gqom` | GqomGenerator | Durban Gqom: heavy syncopated kicks. Варианты: classic/dark/minimal/sgubhu |
| `kuduro` | KuduroGenerator | Angolan kuduro + South African kwaito. Варианты: kuduro/kwaito/afro_tech/tarraxinha |
| `afro_drill` | AfroDrillGenerator | Afro мелодии поверх drill 808s (Burna Boy/Rema style). Варианты: burna/rema/central/classic |
| `soukous_guitar` | SoukousGuitarGenerator | Congolese guitar: sebene runs. Варианты: soukous/rumba/ndombolo/cavacha |
| `bongo_flava` | BongoFlavaGenerator | Tanzanian Bongo Flava. Варианты: classic/modern/singeli/taarab_pop |
| `afro_samba` | AfroSambaGenerator | Brazilian-African fusion. Варианты: samba_afro/bossa_afro/axe/maracatu |

---

## Game Audio / AAA — 11 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `combat_escalation` | CombatEscalationGenerator | Адаптивная боевая музыка: `intensity` 0.0–1.0 (exploration → climax). Слои: strings/brass/percussion/bass |
| `stinger` | StingerGenerator | Музыкальные cues (1–4 beats): discovery/achievement/danger/death/save/level_up/item_get/quest_complete/fail/stealth_alert/checkpoint/combo |
| `chiptune` | ChiptuneGenerator | 8-bit: pulse1 (melody), pulse2 (harmony), triangle (bass), noise (drums). Варианты: nes_classic/gameboy/modern_chip/megadrive |
| `horror_dissonance` | HorrorDissonanceGenerator | Horror scoring: minor 2nd clusters, tritones, chromatic crawls. Варианты: psychological/jump_scare/ambient_dread/creature |
| `stealth_state` | StealthStateGenerator | Stealth state machine: hidden/caution/alert/pursuit/evading |
| `procedural_exploration` | ProceduralExplorationGenerator | Infinite exploration loops. Варианты: nature/sci_fi/underwater/desert/forest. Моды: peaceful/curious/wonder/uneasy |
| `boss_battle` | BossBattleGenerator | Epic boss: фазы intro → build → fight → climax. Варианты: epic/dark_lord/dragon/final |
| `puzzle_loop` | PuzzleLoopGenerator | Minimal puzzle loops: bells/ambient/clockwork/zen |
| `medieval_tavern` | MedievalTavernGenerator | RPG: lute, flute, modal scales (Dorian/Mixolydian). Варианты: tavern/court/journey/battle_camp |
| `scifi_underscore` | SciFiUnderscoreGenerator | Sci-fi pads, sequenced synths. Варианты: blade_runner/space/cyberpunk/retro_sci_fi |
| `victory_fanfare` | VictoryFanfareGenerator | Victory/game_over/title_screen/level_complete/continue |

---

## Synth & Electronic — 6 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `synth_bass` | SynthBassGenerator | Acid/reese/sub/wobble электронный бас |
| `supersaw_pad` | SupersawPadGenerator | Supersaw пады: trance/ambient/stabs/plucks |
| `pluck_sequence` | PluckSequenceGenerator | Offbeat plucks: deep house/tech house |
| `bass_wobble` | BassWobbleGenerator | Dubstep wobble: LFO-модуляция фильтра |
| `lead_synth` | LeadSynthGenerator | Синтезаторный лид: monophonic, portamento, vibrato |
| `sidechain_pump` | SidechainPumpGenerator | Sidechain-качание: velocity ducking по триггеру |

## Orchestral Articulations — 4 генератора

| Тип | Класс | Описание |
|-----|-------|----------|
| `strings_legato` | StringsLegatoGenerator | Legato струнные с портменто |
| `strings_pizzicato` | StringsPizzicatoGenerator | Pizzicato: ostinato/waltz/tremolo/random |
| `strings_staccato` | StringsStaccatoGenerator | Staccato струнные |
| `brass_section` | BrassSectionGenerator | Духовая секция: hit/swell/fanfare/falls/doits |

## Оркестр (расширенные) — 3 генератора

| Тип | Класс | Описание |
|-----|-------|----------|
| `woodwinds_ensemble` | WoodwindsEnsembleGenerator | Деревянные духовые: trio/quartet/full |
| `strings_ensemble` | StringsEnsembleGenerator | Струнная секция: divisi, articulations, dynamic curves |
| `orchestral_hit` | OrchestralHitGenerator | Кинематографичные хиты: staccato/sustain/braam |

## Клавишные — 3 генератора

| Тип | Класс | Описание |
|-----|-------|----------|
| `piano_comp` | PianoCompGenerator | Джазовый/поп аккомпанемент: shell voicings, comping-ритмы |
| `organ_drawbars` | OrganDrawbarsGenerator | Hammond орган: drawbar-регистры, вибрато, лесли |
| `keys_arpeggio` | KeysArpeggioGenerator | Синтезаторные арпеджио с LFO-модуляцией |

## Genre-Specific (classic) — 5 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `ragtime` | RagtimeGenerator | Рагтайм: syncopated RH + stride LH |
| `tango` | TangoGenerator | Танго: marcato/habanera/milonga/vals |
| `reggae_skank` | ReggaeSkankGenerator | Регги: skank/ska/one_drop/rockers/dub |
| `montuno` | MontunoGenerator | Латин: son/salsa/guajira/cha_cha/mambo |
| `waltz` | WaltzGenerator | Вальс: Viennese/jazz/romantic/modern |

## Texture & Ambient — 5 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `canon` | CanonGenerator | Канон: задержанная копия мелодии |
| `drone` | DroneGenerator | Дрон: tonic/dominant/root/fifth/octave/power |
| `ambient` | AmbientPadGenerator | Ambient пады |
| `nebula` | NebulaGenerator | Текстурные облака: cloud/cascade/swell/granular/stasis |
| `clusters` | ClusterGenerator | Тоновые кластеры: second/fourth/mixed/white_key/chromatic |
| `dark_pad` | DarkPadGenerator | Тёмные пады: minor_pad/phrygian_pad/diminished_pad/suspended_pad |
| `tension` | TensionGenerator | Напряжение: sustain/pulse/rising/staccato/dissonant |

## Vocals & Samples — 3 генератора

| Тип | Класс | Описание |
|-----|-------|----------|
| `vocal_chops` | VocalChopsGenerator | Нарезка вокальных семплов |
| `vocal_oohs` | VocalOohsGenerator | Фоновый вокал: ooh/aah/hum/mm |
| `sax_solo` | SaxSoloGenerator | Саксофонное соло: ballad/bebop/fusion/smooth |

## Вокал — 3 генератора

| Тип | Класс | Описание |
|-----|-------|----------|
| `vocal_melisma` | VocalMelismaGenerator | Мелизмы, рулады (R&B, gospel, opera) |
| `vocal_adlibs` | VocalAdlibsGenerator | Импровизационные вставки, call-outs |
| `choir_ahhs` | ChoirAahsGenerator | Хоровые пэды: SATB-гармонии |

## Harmony & Theory — 5 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `reharmonization` | ReharmonizationGenerator | Субституция аккордов |
| `modal_interchange` | ModalInterchangeGenerator | Заимствованные аккорды |
| `voice_leading` | VoiceLeadingGenerator | Автоматическое плавное голосоведение |
| `counterpoint` | CounterpointGenerator | Строгий контрапункт: species 1–5 |
| `motif_development` | MotifDevelopmentGenerator | Развитие мотива: inversion/retrograde/augmentation |

## Meta & Structure — 2 генератора

| Тип | Класс | Описание |
|-----|-------|----------|
| `arranger` | ArrangerGenerator | Управление формой: verse/chorus/bridge |
| `humanizer` | HumanizerGenerator | Пост-обработка: timing/velocity/groove |

## Utility — 7 генераторов

| Тип | Класс | Описание |
|-----|-------|----------|
| `dyads` | DyadGenerator | Двухголосные интервалы |
| `dyads_run` | DyadsRunGenerator | Беглые двухголосные последовательности |
| `rest` | RestGenerator | Тишина |
| `generic` | GenericGenerator | Запасной генератор |
| `step_sequencer` | StepSequencer | Пошаговый секвенсор |
| `phrase_container` | PhraseContainer | Контейнер для фраз |
| `phrase_morpher` | PhraseMorpher | Интерполяция между фразами |
| `random_note` | RandomNoteGenerator | Случайные ноты |
| `filter_sweep` | FilterSweepGenerator | Автоматизация фильтра: cutoff envelope |
| `euclidean_rhythm` | EuclideanRhythmGenerator | Евклидовы ритмы: Bjorklund algorithm |

---

## Meta-генераторы

| Тип | Класс | Описание |
|-----|-------|----------|
| `genre_fusion` | GenreFusionEngine | Смешение жанров: trap+jazz, drill+lofi и т.д. Режимы: interleave/layer/morph/random |
| `vocal_melody_auto` | VocalMelodyAutoGenerator | Auto-tune оптимизированные мелодии. Варианты: travis/tpain/future/don_toliver |

---

## MIDI Doctor (интеграция в IdeaTool)

Параметры `IdeaToolConfig`:

| Параметр | Default | Описание |
|----------|---------|----------|
| `run_doctor` | `False` | Запустить диагностику после генерации |
| `doctor_psycho` | `True` | Psychoacoustic checks (masking, fusion, blur) |
| `doctor_harmonic` | `True` | Cross-track harmonic clash detection |

Результат в `result["_doctor_report"]`:
```python
{
    "psycho_checks": {"frequency_masking": [...], "temporal_masking": [...], ...},
    "harmonic_clashes": [...],
    "total_issues": int,
}
```

Диагностика использует существующие функции из `melodica.composer.psychoacoustic` и `melodica.composer.harmonic_verifier`.

Отдельный CLI-скрипт: `scripts/midi_doctor.py --script <script.py> --duration <min> --tempo <bpm> --key <root> --seed <int>`

---

## GeneratorParams (общие параметры)

| Поле | Default | Описание |
|---|---|---|
| `density` | 0.5 | Плотность нот / уровень velocity (0.0–1.0) |
| `complexity` | 0.5 | Ритмическая/мелодическая сложность (0.0–1.0) |
| `key_range_low` | 48 | Нижняя граница MIDI (C3) |
| `key_range_high` | 84 | Верхняя граница MIDI (C6) |
| `swing` | 0.5 | Свинг (0.0 = straight, 1.0 = полный) |
| `humanize` | 0.5 | Гуманизация тайминга/velocity (0.0–1.0) |
| `scale` | None | Переопределение тональности |
