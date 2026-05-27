# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-23
# Last Updated: 2026-05-23
#
# Licensed under the MIT License.

"""
album_15_symphonic_works.py — "The Symphonic Legacy".

A monumental masterpiece album comprising 15 complete symphonic works showcasing our
premium continuous expression engines, physical-model articulation curves, and custom orchestral generators.
"""

import random
from pathlib import Path

from melodica import types
from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator
from melodica.generators.tuba import TubaGenerator
from melodica.generators.snare_drum import SnareDrumGenerator
from melodica.generators.orchestral_cymbal import OrchestralCymbalGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# Standard scale shortcuts
SCALE_D_MAJOR = Scale(root=2, mode=Mode.IONIAN)
SCALE_D_MINOR = Scale(root=2, mode=Mode.AEOLIAN)
SCALE_A_MINOR = Scale(root=9, mode=Mode.AEOLIAN)
SCALE_A_MAJOR = Scale(root=9, mode=Mode.IONIAN)
SCALE_C_MAJOR = Scale(root=0, mode=Mode.IONIAN)
SCALE_C_MINOR = Scale(root=0, mode=Mode.AEOLIAN)
SCALE_F_SHARP_MINOR = Scale(root=6, mode=Mode.AEOLIAN)
SCALE_E_FLAT_MAJOR = Scale(root=3, mode=Mode.IONIAN)
SCALE_B_MINOR = Scale(root=11, mode=Mode.AEOLIAN)
SCALE_G_MINOR = Scale(root=7, mode=Mode.AEOLIAN)
SCALE_G_MAJOR = Scale(root=7, mode=Mode.IONIAN)
SCALE_F_MAJOR = Scale(root=5, mode=Mode.IONIAN)
SCALE_F_MINOR = Scale(root=5, mode=Mode.AEOLIAN)
SCALE_D_BEMOL_MAJOR = Scale(root=1, mode=Mode.IONIAN)
SCALE_G_SHARP_MINOR = Scale(root=8, mode=Mode.AEOLIAN)


def _build_chords(progression: str, duration: float, key: Scale) -> list[ChordLabel]:
    """Parse a Roman numeral progression into ChordLabels."""
    parts = progression.split()
    beats_per = duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        chord = key.parse_roman(p)
        chord.start = i * beats_per
        chord.duration = beats_per
        chords.append(chord)
    return chords


def apply_orchestral_mix(raw_tracks, bpm, lufs=-14.0):
    """Mix and master the raw tracks using the MixingDesk and MasteringDesk."""
    desk = MixingDesk(niche_cfg={})
    
    # Gain staging config
    desk.track_gains.update({
        "Violins": 0.85,
        "Violins_II": 0.75,
        "Viola": 0.80,
        "Cello": 0.88,
        "Bass": 0.95,
        "Pizzicato": 0.90,
        "Tremolo": 0.82,
        "Brass": 0.88,
        "Woodwinds": 0.86,
        "Choir": 0.82,
        "Hits": 0.95,
        "Tuba": 1.15,
        "Snare": 0.90,
        "Cymbal": 0.85,
        "Bells": 0.92,
        "Harp": 0.90,
    })
    
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan_events = master.apply_mastering(mixed)
    return mastered, pan_events


# ===========================================================================
# 1. Celestial Dominion
# ===========================================================================
def produce_celestial_dominion():
    print("Writing Work 1: Celestial Dominion...")
    duration = 48.0
    chords = _build_chords("I IV V I vi ii V I", duration, SCALE_D_MAJOR)
    
    # Intro high cosmic harmonics (Violins staccato/harmonics)
    violins = [NoteInfo(pitch=86 + (i % 3) * 4, start=i * 2.0, duration=0.5, velocity=85, articulation="staccato") for i in range(4)]
    
    # Dev: woodwinds & cello countermelody
    wood_params = GeneratorParams(density=0.6, key_range_low=72, key_range_high=96)
    wood_gen = WoodwindsEnsembleGenerator(wood_params, section="quartet", articulation="legato")
    woodwinds = wood_gen.render(chords, SCALE_D_MAJOR, duration)
    
    strings_params = GeneratorParams(density=0.5, key_range_low=48, key_range_high=68)
    strings_gen = StringsLegatoGenerator(strings_params, section_size="ensemble")
    cello = strings_gen.render(chords, SCALE_D_MAJOR, duration)
    violins.extend(cello)
    
    # Climax Brass + Choir
    brass_params = GeneratorParams(density=0.5, key_range_low=50, key_range_high=76)
    brass_gen = BrassSectionGenerator(brass_params, articulation="sustained", intensity=0.9)
    brass = brass_gen.render(chords, SCALE_D_MAJOR, duration)
    
    choir_params = GeneratorParams(density=0.4, key_range_low=55, key_range_high=79)
    choir_gen = ChoirAahsGenerator(choir_params, voice_count=4, syllable="aah")
    choir = choir_gen.render(chords, SCALE_D_MAJOR, duration)
    
    snare_params = GeneratorParams(density=0.4)
    snare_gen = SnareDrumGenerator(snare_params, pattern_type="march")
    snare = snare_gen.render(chords, SCALE_D_MAJOR, duration)
    
    # Coda solo violin + bell
    violins.append(NoteInfo(pitch=82, start=44.0, duration=3.5, velocity=70, articulation="arco"))
    bells = [NoteInfo(pitch=74, start=46.0, duration=2.0, velocity=80)]
    
    return {
        "Violins": violins,
        "Woodwinds": woodwinds,
        "Brass": brass,
        "Choir": choir,
        "Snare": snare,
        "Bells": bells,
    }, 72.0


# ===========================================================================
# 2. Echoes of the Eternal Orchestra
# ===========================================================================
def produce_echoes_eternal():
    print("Writing Work 2: Echoes of the Eternal Orchestra...")
    duration = 40.0
    chords = _build_chords("i iv V i VI iv V i", duration, SCALE_A_MINOR)
    
    # Core theme
    strings_params = GeneratorParams(density=0.5, key_range_low=60, key_range_high=80)
    strings_gen = StringsLegatoGenerator(strings_params, section_size="ensemble")
    theme_notes = strings_gen.render(chords, SCALE_A_MINOR, duration)
    
    # Create echoing voices
    v1, v2, viola, cello = [], [], [], []
    for n in theme_notes:
        # Violins I (Theme A)
        v1.append(NoteInfo(pitch=n.pitch, start=n.start, duration=n.duration, velocity=n.velocity, articulation=n.articulation))
        
        # Violins II (Echo 1: +2 beats delay, pp)
        v2.append(NoteInfo(pitch=n.pitch - 12 if n.pitch > 72 else n.pitch, start=n.start + 2.0, duration=n.duration, velocity=max(1, int(n.velocity * 0.5)), articulation=n.articulation))
        
        # Viola (Echo 2: +4 beats delay, ppp)
        viola.append(NoteInfo(pitch=n.pitch - 7, start=n.start + 4.0, duration=n.duration, velocity=max(1, int(n.velocity * 0.3)), articulation=n.articulation))
        
    # Pizzicato col legno snaps
    pizz_params = GeneratorParams(density=0.6, key_range_low=45, key_range_high=65)
    pizz_gen = StringsPizzicatoGenerator(pizz_params, pattern="ostinato", snap_chance=0.8)
    pizz = pizz_gen.render(chords, SCALE_A_MINOR, duration)
    
    return {
        "Violins": v1,
        "Violins_II": v2,
        "Viola": viola,
        "Pizzicato": pizz,
    }, 58.0


# ===========================================================================
# 3. Symphony of the Four Horizons
# ===========================================================================
def produce_horizon_mvt(mvt_num):
    print(f"Writing Horizon Movement {mvt_num}...")
    duration = 32.0
    
    # 5-note leitmotif: [62, 64, 65, 67, 69] (D Minor / F Major Scale degree mapping)
    if mvt_num == 1: # North: D Minor, 132 BPM, Bassoon + French Horn
        chords = _build_chords("i iv V i", duration, SCALE_D_MINOR)
        wood_params = GeneratorParams(density=0.5, key_range_low=40, key_range_high=60) # Low Bassoon
        wood_gen = WoodwindsEnsembleGenerator(wood_params, section="trio", articulation="staccato")
        bassoon = wood_gen.render(chords, SCALE_D_MINOR, duration)
        
        brass_params = GeneratorParams(density=0.45, key_range_low=50, key_range_high=72)
        brass_gen = BrassSectionGenerator(brass_params, articulation="sustained", intensity=0.7)
        horn = brass_gen.render(chords, SCALE_D_MINOR, duration)
        return {"Woodwinds": bassoon, "Brass": horn}, 132.0
        
    elif mvt_num == 2: # East: A Minor, 54 BPM, Oboe + Tremolo Strings
        chords = _build_chords("i v VI iv i v i", duration, SCALE_A_MINOR)
        wood_params = GeneratorParams(density=0.4, key_range_low=60, key_range_high=80) # Mid Oboe
        wood_gen = WoodwindsEnsembleGenerator(wood_params, section="trio")
        oboe = wood_gen.render(chords, SCALE_A_MINOR, duration)
        
        trem_params = GeneratorParams(density=0.6, key_range_low=55, key_range_high=75)
        trem_gen = TremoloStringsGenerator(trem_params, bow_speed=0.05)
        trem = trem_gen.render(chords, SCALE_A_MINOR, duration)
        
        harp = [NoteInfo(pitch=62 + (i % 3) * 5, start=i * 4.0, duration=3.0, velocity=75) for i in range(8)]
        return {"Woodwinds": oboe, "Tremolo": trem, "Harp": harp}, 54.0
        
    elif mvt_num == 3: # South: F Major, 176 BPM, Clarinet + Maracas (Rimshots)
        chords = _build_chords("I IV V I IV I V I", duration, SCALE_F_MAJOR)
        wood_params = GeneratorParams(density=0.6, key_range_low=55, key_range_high=78)
        wood_gen = WoodwindsEnsembleGenerator(wood_params, section="trio", articulation="staccato")
        clarinet = wood_gen.render(chords, SCALE_F_MAJOR, duration)
        
        snare_params = GeneratorParams(density=0.7)
        snare_gen = SnareDrumGenerator(snare_params, pattern_type="rimshot")
        snare = snare_gen.render(chords, SCALE_F_MAJOR, duration)
        return {"Woodwinds": clarinet, "Snare": snare}, 176.0
        
    else: # West: G Major, 160 BPM, Tutti
        chords = _build_chords("I vi IV V I vi ii V I", duration, SCALE_G_MAJOR)
        
        strings_params = GeneratorParams(density=0.65, key_range_low=60, key_range_high=82)
        strings_gen = StringsLegatoGenerator(strings_params)
        strings = strings_gen.render(chords, SCALE_G_MAJOR, duration)
        
        brass_params = GeneratorParams(density=0.55, key_range_low=50, key_range_high=75)
        brass_gen = BrassSectionGenerator(brass_params, articulation="fanfare")
        brass = brass_gen.render(chords, SCALE_G_MAJOR, duration)
        
        bells_params = GeneratorParams(density=0.35, key_range_low=60, key_range_high=80)
        bells_gen = TubularBellsGenerator(bells_params, stroke_pattern="motif")
        bells = bells_gen.render(chords, SCALE_G_MAJOR, duration)
        
        return {"Violins": strings, "Brass": brass, "Bells": bells}, 160.0


# ===========================================================================
# 4. The Grand Imperial Suite
# ===========================================================================
def produce_imperial_suite():
    print("Writing Work 4: The Grand Imperial Suite...")
    # 6 movements combined in one master sequence (6 x 16 = 96 beats total)
    total_duration = 96.0
    
    # 1. Fanfare: beats 0-16
    chords_fanfare = _build_chords("I V I V", 16.0, SCALE_C_MAJOR)
    brass_params = GeneratorParams(density=0.6, key_range_low=52, key_range_high=78)
    brass_gen = BrassSectionGenerator(brass_params, articulation="fanfare", intensity=0.9)
    brass_notes = brass_gen.render(chords_fanfare, SCALE_C_MAJOR, 16.0)
    
    snare_params = GeneratorParams(density=0.6)
    snare_gen = SnareDrumGenerator(snare_params, pattern_type="march")
    snare_notes = snare_gen.render(chords_fanfare, SCALE_C_MAJOR, 16.0)
    
    # 2. Processional: beats 16-32
    chords_proc = _build_chords("I IV vi V", 16.0, SCALE_C_MAJOR)
    for c in chords_proc: c.start += 16.0
    strings_params = GeneratorParams(density=0.5, key_range_low=55, key_range_high=78)
    strings_gen = StringsLegatoGenerator(strings_params)
    strings_proc = strings_gen.render(chords_proc, SCALE_C_MAJOR, 16.0)
    
    # 3. Court Dance (3/4 minuet): beats 32-48
    chords_dance = _build_chords("I V vi iii IV I ii V", 16.0, SCALE_C_MAJOR)
    for c in chords_dance: c.start += 32.0
    wood_params = GeneratorParams(density=0.55, key_range_low=60, key_range_high=82)
    wood_gen = WoodwindsEnsembleGenerator(wood_params, section="trio", articulation="staccato")
    dance_notes = wood_gen.render(chords_dance, SCALE_C_MAJOR, 16.0)
    
    # 4. The Battle: beats 48-64
    chords_battle = _build_chords("ii v bII v I IV V bII", 16.0, SCALE_C_MAJOR)
    for c in chords_battle: c.start += 48.0
    pizz_params = GeneratorParams(density=0.7, key_range_low=50, key_range_high=75)
    pizz_gen = StringsPizzicatoGenerator(pizz_params, pattern="ostinato", snap_chance=0.9)
    battle_pizz = pizz_gen.render(chords_battle, SCALE_C_MAJOR, 16.0)
    
    # 5. Lament: beats 64-80
    chords_lament = _build_chords("vi iv I V vi iv I", 16.0, SCALE_C_MAJOR)
    for c in chords_lament: c.start += 64.0
    wood_lament_params = GeneratorParams(density=0.4, key_range_low=60, key_range_high=80)
    wood_lament_gen = WoodwindsEnsembleGenerator(wood_lament_params, section="trio")
    lament_wood = wood_lament_gen.render(chords_lament, SCALE_C_MAJOR, 16.0)
    
    # 6. Triumph: beats 80-96
    chords_triumph = _build_chords("I IV V I vi ii V I", 16.0, SCALE_C_MAJOR)
    for c in chords_triumph: c.start += 80.0
    triumph_brass = brass_gen.render(chords_triumph, SCALE_C_MAJOR, 16.0)
    
    # Collate
    brass = brass_notes + triumph_brass
    snare = snare_notes
    violins = strings_proc + battle_pizz
    woodwinds = dance_notes + lament_wood
    
    return {
        "Violins": violins,
        "Brass": brass,
        "Snare": snare,
        "Woodwinds": woodwinds,
    }, 120.0


# ===========================================================================
# 5. Nocturne of the Silver Kingdom
# ===========================================================================
def produce_nocturne():
    print("Writing Work 5: Nocturne of the Silver Kingdom...")
    duration = 48.0
    chords = _build_chords("i iv VI v i iv v i", duration, SCALE_F_SHARP_MINOR)
    
    # Harp/Bells Prologue & Epilogue
    harp = [NoteInfo(pitch=54 + (i % 4) * 3, start=i * 2.0, duration=1.5, velocity=65) for i in range(8)]
    # Epilogue Harp
    harp.extend([NoteInfo(pitch=50 + (i % 3) * 4, start=40.0 + i * 2.0, duration=1.5, velocity=50) for i in range(4)])
    
    # Sordino main theme (Strings Legato, mute=True)
    strings_params = GeneratorParams(density=0.45, key_range_low=54, key_range_high=74)
    strings_gen = StringsLegatoGenerator(strings_params, section_size="chamber", portamento_speed=0.25)
    strings = strings_gen.render(chords, SCALE_F_SHARP_MINOR, duration)
    for s in strings:
        s.velocity = max(1, int(s.velocity * 0.7)) # Soft dynamic
        s.expression["mute"] = True
        
    # Middle part (Flute + Clarinet in thirds)
    wood_params = GeneratorParams(density=0.5, key_range_low=60, key_range_high=80)
    wood_gen = WoodwindsEnsembleGenerator(wood_params, section="trio")
    woodwinds = wood_gen.render(chords[2:6], SCALE_F_SHARP_MINOR, 24.0) # active in mid section
    for w in woodwinds:
        w.start += 12.0
        
    # Pizzicato double bass
    pizz_params = GeneratorParams(density=0.35, key_range_low=32, key_range_high=48)
    pizz_gen = StringsPizzicatoGenerator(pizz_params, pattern="random")
    pizz = pizz_gen.render(chords, SCALE_F_SHARP_MINOR, duration)
    
    return {
        "Harp": harp,
        "Violins": strings,
        "Woodwinds": woodwinds,
        "Pizzicato": pizz,
    }, 46.0


# ===========================================================================
# 6. Aurora Triumphalis
# ===========================================================================
def produce_aurora():
    print("Writing Work 6: Aurora Triumphalis...")
    duration = 64.0
    chords = _build_chords("I IV V I I IV V I", duration, SCALE_E_FLAT_MAJOR)
    
    # Full orchestral sweep build up via CC 11 expression
    strings_params = GeneratorParams(density=0.6, key_range_low=58, key_range_high=82)
    strings_gen = StringsLegatoGenerator(strings_params)
    strings = strings_gen.render(chords, SCALE_E_FLAT_MAJOR, duration)
    
    # Set linear CC 11 crescendo sweep from 25 to 125 across the duration
    for s in strings:
        ratio = s.start / duration
        s.expression[11] = int(25 + ratio * 100)
        
    brass_params = GeneratorParams(density=0.45, key_range_low=50, key_range_high=74)
    brass_gen = BrassSectionGenerator(brass_params, articulation="sustained")
    brass = brass_gen.render(chords, SCALE_E_FLAT_MAJOR, duration)
    for b in brass:
        ratio = b.start / duration
        b.expression[11] = int(20 + ratio * 105)
        
    choir_params = GeneratorParams(density=0.4, key_range_low=52, key_range_high=76)
    choir_gen = ChoirAahsGenerator(choir_params, voice_count=4, syllable="oh")
    choir = choir_gen.render(chords, SCALE_E_FLAT_MAJOR, duration)
    for c in choir:
        ratio = c.start / duration
        # CC 74 modulation representing vowel formants opening up
        c.expression[74] = int(40 + ratio * 80)
        c.expression[11] = int(30 + ratio * 95)
        
    bells_params = GeneratorParams(density=0.25, key_range_low=55, key_range_high=80)
    bells_gen = TubularBellsGenerator(bells_params, stroke_pattern="motif", dampen=False)
    bells = bells_gen.render(chords, SCALE_E_FLAT_MAJOR, duration)
    
    return {
        "Violins": strings,
        "Brass": brass,
        "Choir": choir,
        "Bells": bells,
    }, 60.0


# ===========================================================================
# 7. Chronicles of the Crimson Symphony
# ===========================================================================
def produce_crimson():
    print("Writing Work 7: Chronicles of the Crimson Symphony...")
    # Ch I: beats 0-24, Ch II: beats 24-48, Ch III: beats 48-72
    total_dur = 72.0
    
    # Ch I: A Major Allegretto Pastorele
    chords_ch1 = _build_chords("I IV V I vi ii V I", 24.0, SCALE_A_MAJOR)
    wood_params = GeneratorParams(density=0.55, key_range_low=60, key_range_high=82)
    wood_gen = WoodwindsEnsembleGenerator(wood_params, section="quartet", articulation="legato")
    pastoral_wood = wood_gen.render(chords_ch1, SCALE_A_MAJOR, 24.0)
    
    # Ch II: A Minor Presto Furioso (5/4 + 7/8 syncopated)
    chords_ch2 = _build_chords("i iv V VI i iv V VI", 24.0, SCALE_A_MINOR)
    for c in chords_ch2: c.start += 24.0
    brass_params = GeneratorParams(density=0.7, key_range_low=48, key_range_high=72)
    brass_gen = BrassSectionGenerator(brass_params, articulation="hit", intensity=0.95)
    battle_brass = brass_gen.render(chords_ch2, SCALE_A_MINOR, 24.0)
    
    snare_params = GeneratorParams(density=0.75)
    snare_gen = SnareDrumGenerator(snare_params, pattern_type="roll")
    battle_snare = snare_gen.render(chords_ch2, SCALE_A_MINOR, 24.0)
    
    # Ch III: Aftermath (broken, fragmented phrases)
    chords_ch3 = _build_chords("i iv v i i iv v i", 24.0, SCALE_A_MINOR)
    for c in chords_ch3: c.start += 48.0
    strings_params = GeneratorParams(density=0.3, key_range_low=58, key_range_high=78)
    strings_gen = StringsLegatoGenerator(strings_params, section_size="solo")
    after_strings = strings_gen.render(chords_ch3, SCALE_A_MINOR, 24.0)
    # Fragment the phrases by cutting notes shorter
    for s in after_strings:
        s.duration = max(0.1, s.duration * 0.4)
        s.velocity = max(1, int(s.velocity * 0.6))
        
    return {
        "Woodwinds": pastoral_wood,
        "Brass": battle_brass,
        "Snare": battle_snare,
        "Violins": after_strings,
    }, 90.0


# ===========================================================================
# 8. Obsidian Reverie
# ===========================================================================
def produce_obsidian():
    print("Writing Work 8: Obsidian Reverie...")
    duration = 32.0
    chords = _build_chords("i VI iv v i VI iv v", duration, SCALE_B_MINOR)
    
    # Basses snapped pizzicato
    pizz_params = GeneratorParams(density=0.35, key_range_low=26, key_range_high=43)
    pizz_gen = StringsPizzicatoGenerator(pizz_params, pattern="ostinato", snap_chance=0.95)
    basses = pizz_gen.render(chords, SCALE_B_MINOR, duration)
    
    # Chromatic leaps in Bassoon
    wood_params = GeneratorParams(density=0.4, key_range_low=43, key_range_high=65)
    wood_gen = WoodwindsEnsembleGenerator(wood_params, section="trio", articulation="staccato")
    bassoon = wood_gen.render(chords, SCALE_B_MINOR, duration)
    
    # Shimmering chimes with long decays
    bells_params = GeneratorParams(density=0.2, key_range_low=60, key_range_high=80)
    bells_gen = TubularBellsGenerator(bells_params, stroke_pattern="single", dampen=False)
    chimes = bells_gen.render(chords, SCALE_B_MINOR, duration)
    
    # Solo violin soaring
    strings_params = GeneratorParams(density=0.4, key_range_low=64, key_range_high=88)
    strings_gen = StringsLegatoGenerator(strings_params, section_size="solo", portamento_speed=0.25)
    violin = strings_gen.render(chords, SCALE_B_MINOR, duration)
    
    # End on unison B
    basses.append(NoteInfo(pitch=35, start=28.0, duration=4.0, velocity=50))
    violin.append(NoteInfo(pitch=59, start=28.0, duration=4.0, velocity=50))
    
    return {
        "Pizzicato": basses,
        "Woodwinds": bassoon,
        "Bells": chimes,
        "Violins": violin,
    }, 48.0


# ===========================================================================
# 9. The Last Royal Overture
# ===========================================================================
def produce_royal_overture():
    print("Writing Work 9: The Last Royal Overture...")
    duration = 64.0
    chords = _build_chords("i iv V i VI III iv V", duration, SCALE_G_MINOR)
    
    # Expo Theme A (Brass military)
    brass_params = GeneratorParams(density=0.55, key_range_low=50, key_range_high=74)
    brass_gen = BrassSectionGenerator(brass_params, articulation="fanfare")
    brass = brass_gen.render(chords[:4], SCALE_G_MINOR, 32.0)
    
    # Expo Theme B (Lyrical strings)
    strings_params = GeneratorParams(density=0.6, key_range_low=60, key_range_high=82)
    strings_gen = StringsLegatoGenerator(strings_params)
    strings = strings_gen.render(chords[4:], SCALE_G_MINOR, 32.0)
    for s in strings:
        s.start += 32.0
        
    # Coda: quiet Horn + Tuba quintet modulation to G Major
    chords_coda = _build_chords("I IV V I", 16.0, SCALE_G_MAJOR)
    for c in chords_coda: c.start += 64.0
    
    tuba_params = GeneratorParams(density=0.4, key_range_low=29, key_range_high=50)
    tuba_gen = TubaGenerator(tuba_params, articulation="sustained", growl=False)
    tuba = tuba_gen.render(chords_coda, SCALE_G_MAJOR, 16.0)
    
    return {
        "Brass": brass,
        "Violins": strings,
        "Tuba": tuba,
    }, 110.0


# ===========================================================================
# 10. Infinite Harmonics
# ===========================================================================
def produce_infinite_harmonics():
    print("Writing Work 10: Infinite Harmonics...")
    duration = 48.0
    
    # Fundamental C in Double Bass
    basses = [NoteInfo(pitch=24, start=0.0, duration=48.0, velocity=75)]
    
    # Add overtones step-by-step every 4 beats: G3, C4, E4, G4, Bb4, C5, D5, E5, F#5, G5
    overtones = [43, 48, 52, 55, 58, 60, 62, 64, 66, 67]
    woodwinds = []
    for idx, overtone in enumerate(overtones):
        t_start = idx * 4.0
        # Remains active until end, decaying one by one from beat 40
        t_end = 40.0 - (idx * 2.0)
        woodwinds.append(
            NoteInfo(
                pitch=overtone,
                start=t_start,
                duration=max(1.0, t_end - t_start),
                velocity=max(10, int(80 - idx * 5)),
            )
        )
        
    # Final Piccolo flute piercing high C at beat 44
    woodwinds.append(NoteInfo(pitch=96, start=44.0, duration=4.0, velocity=125))
    
    return {
        "Pizzicato": basses,
        "Woodwinds": woodwinds,
    }, 60.0


# ===========================================================================
# 11. Empire of Strings and Thunder
# ===========================================================================
def produce_empire_strings_thunder():
    print("Writing Work 11: Empire of Strings and Thunder...")
    duration = 48.0
    chords = _build_chords("i VI iv v i VI iv v", duration, SCALE_C_MINOR)
    
    # Act I: Strings only
    strings_params = GeneratorParams(density=0.65, key_range_low=58, key_range_high=80)
    strings_gen = StringsLegatoGenerator(strings_params)
    strings = strings_gen.render(chords[:4], SCALE_C_MINOR, 24.0)
    
    # Pizz snaps
    pizz_params = GeneratorParams(density=0.6, key_range_low=45, key_range_high=65)
    pizz_gen = StringsPizzicatoGenerator(pizz_params, pattern="ostinato", snap_chance=0.9)
    pizz = pizz_gen.render(chords[:4], SCALE_C_MINOR, 24.0)
    
    # Act II: Percussion invasion
    snare_params = GeneratorParams(density=0.7)
    snare_gen = SnareDrumGenerator(snare_params, pattern_type="roll")
    snare = snare_gen.render(chords[4:6], SCALE_C_MINOR, 12.0)
    for s in snare: s.start += 24.0
    
    cymbal_params = GeneratorParams(density=0.5)
    cymbal_gen = OrchestralCymbalGenerator(cymbal_params, pattern_type="rolls")
    cymbal = cymbal_gen.render(chords[4:6], SCALE_C_MINOR, 12.0)
    for cy in cymbal: cy.start += 24.0
    
    # Act III: Union
    strings_union = strings_gen.render(chords[6:], SCALE_C_MINOR, 12.0)
    for su in strings_union: su.start += 36.0
    strings.extend(strings_union)
    
    snare_union = snare_gen.render(chords[6:], SCALE_C_MINOR, 12.0)
    for snu in snare_union: snu.start += 36.0
    snare.extend(snu for snu in snare_union)
    
    return {
        "Violins": strings,
        "Pizzicato": pizz,
        "Snare": snare,
        "Cymbal": cymbal,
    }, 152.0


# ===========================================================================
# 12. Luminara: A Symphonic Journey
# ===========================================================================
def produce_luminara():
    print("Writing Work 12: Luminara: A Symphonic Journey...")
    duration = 80.0 # 5 episodes x 16 beats = 80 beats
    
    # Ep 1: Dawn: A Major, Flute solo
    chords_dawn = _build_chords("I IV V I", 16.0, SCALE_A_MAJOR)
    wood_params = GeneratorParams(density=0.5, key_range_low=65, key_range_high=88)
    wood_gen = WoodwindsEnsembleGenerator(wood_params, section="trio")
    flute_solo = wood_gen.render(chords_dawn, SCALE_A_MAJOR, 16.0)
    
    # Ep 2: Forest: A Minor, Clarinet + Cello
    chords_forest = _build_chords("i iv V i", 16.0, SCALE_A_MINOR)
    for c in chords_forest: c.start += 16.0
    woodwinds_forest = wood_gen.render(chords_forest, SCALE_A_MINOR, 16.0)
    
    strings_params = GeneratorParams(density=0.5, key_range_low=48, key_range_high=68)
    strings_gen = StringsLegatoGenerator(strings_params)
    cello = strings_gen.render(chords_forest, SCALE_A_MINOR, 16.0)
    
    # Ep 3: City of Light: D Major, Tutti Rhythmic
    chords_city = _build_chords("I IV V I", 16.0, SCALE_D_MAJOR)
    for c in chords_city: c.start += 32.0
    brass_params = GeneratorParams(density=0.6, key_range_low=52, key_range_high=76)
    brass_gen = BrassSectionGenerator(brass_params, articulation="fanfare")
    brass = brass_gen.render(chords_city, SCALE_D_MAJOR, 16.0)
    
    strings_city = strings_gen.render(chords_city, SCALE_D_MAJOR, 16.0)
    
    # Ep 4: The Storm: D Minor, fff, chaotic
    chords_storm = _build_chords("i iv V i", 16.0, SCALE_D_MINOR)
    for c in chords_storm: c.start += 48.0
    brass_storm = brass_gen.render(chords_storm, SCALE_D_MINOR, 16.0)
    for b in brass_storm:
        b.velocity = min(127, int(b.velocity * 1.2))
        
    cymbal_params = GeneratorParams(density=0.5)
    cymbal_gen = OrchestralCymbalGenerator(cymbal_params, pattern_type="rolls")
    cymbal_storm = cymbal_gen.render(chords_storm, SCALE_D_MINOR, 16.0)
    
    # Ep 5: Luminara Revelation: F Major, full swell + choir
    chords_reveal = _build_chords("I IV V I", 16.0, SCALE_F_MAJOR)
    for c in chords_reveal: c.start += 64.0
    
    choir_params = GeneratorParams(density=0.5, key_range_low=54, key_range_high=78)
    choir_gen = ChoirAahsGenerator(choir_params, voice_count=4)
    choir = choir_gen.render(chords_reveal, SCALE_F_MAJOR, 16.0)
    
    bells_params = GeneratorParams(density=0.4, key_range_low=58, key_range_high=80)
    bells_gen = TubularBellsGenerator(bells_params, stroke_pattern="motif")
    bells = bells_gen.render(chords_reveal, SCALE_F_MAJOR, 16.0)
    
    # Combine
    wood = flute_solo + woodwinds_forest
    violins = cello + strings_city
    brass_tutti = brass + brass_storm
    
    return {
        "Woodwinds": wood,
        "Violins": violins,
        "Brass": brass_tutti,
        "Cymbal": cymbal_storm,
        "Choir": choir,
        "Bells": bells,
    }, 110.0


# ===========================================================================
# 13. The Four Movements of Destiny
# ===========================================================================
def produce_destiny_mvt(mvt_num):
    print(f"Writing Destiny Movement {mvt_num}...")
    duration = 32.0
    
    # Fate Timpani Motif: 3 heavy hits followed by a descending motif
    fate_snare = [
        NoteInfo(pitch=40, start=0.0, duration=0.25, velocity=120),
        NoteInfo(pitch=40, start=0.5, duration=0.25, velocity=120),
        NoteInfo(pitch=40, start=1.0, duration=0.5, velocity=125)
    ]
    
    if mvt_num == 1: # Awakening: A Major, 110 BPM
        chords = _build_chords("I IV V I", duration, SCALE_A_MAJOR)
        strings_params = GeneratorParams(density=0.6, key_range_low=60, key_range_high=82)
        strings_gen = StringsLegatoGenerator(strings_params)
        strings = strings_gen.render(chords, SCALE_A_MAJOR, duration)
        return {"Violins": strings, "Snare": fate_snare}, 110.0
        
    elif mvt_num == 2: # The Weight: F Minor, 60 BPM
        chords = _build_chords("i iv v i", duration, SCALE_F_MINOR)
        strings_params = GeneratorParams(density=0.5, key_range_low=48, key_range_high=68)
        strings_gen = StringsLegatoGenerator(strings_params, section_size="full")
        strings = strings_gen.render(chords, SCALE_F_MINOR, duration)
        return {"Violins": strings, "Snare": fate_snare}, 60.0
        
    elif mvt_num == 3: # Defiance: D Major, 140 BPM
        chords = _build_chords("I IV V I", duration, SCALE_D_MAJOR)
        brass_params = GeneratorParams(density=0.6, key_range_low=52, key_range_high=74)
        brass_gen = BrassSectionGenerator(brass_params, articulation="hit")
        brass = brass_gen.render(chords, SCALE_D_MAJOR, duration)
        return {"Brass": brass, "Snare": fate_snare}, 140.0
        
    else: # Convergence: A Major, Maestoso -> Presto
        chords = _build_chords("I IV V I vi ii V I", duration, SCALE_A_MAJOR)
        strings_params = GeneratorParams(density=0.65, key_range_low=60, key_range_high=84)
        strings_gen = StringsLegatoGenerator(strings_params)
        strings = strings_gen.render(chords, SCALE_A_MAJOR, duration)
        
        brass_params = GeneratorParams(density=0.55, key_range_low=50, key_range_high=76)
        brass_gen = BrassSectionGenerator(brass_params, articulation="fanfare")
        brass = brass_gen.render(chords, SCALE_A_MAJOR, duration)
        
        return {"Violins": strings, "Brass": brass, "Snare": fate_snare}, 120.0


# ===========================================================================
# 14. Majestic Tides
# ===========================================================================
def produce_majestic_tides():
    print("Writing Work 14: Majestic Tides...")
    duration = 64.0
    chords = _build_chords("I IV V I I IV V I", duration, SCALE_D_BEMOL_MAJOR)
    
    # Harp glissandos: arpeggiated runs sweeping up and down
    harp = []
    for beat in range(0, 64, 4):
        harp.extend([
            NoteInfo(pitch=54 + s * 4, start=beat + s * 0.25, duration=0.2, velocity=75)
            for s in range(8)
        ])
        
    # Tide curves: CC 11 sweeps
    strings_params = GeneratorParams(density=0.55, key_range_low=56, key_range_high=78)
    strings_gen = StringsLegatoGenerator(strings_params)
    strings = strings_gen.render(chords, SCALE_D_BEMOL_MAJOR, duration)
    for s in strings:
        # Wave modulation
        import math
        wave = math.sin((s.start / duration) * 2 * math.pi) # Sine wave tide
        s.expression[11] = int(60 + wave * 50)
        
    brass_params = GeneratorParams(density=0.45, key_range_low=48, key_range_high=70)
    brass_gen = BrassSectionGenerator(brass_params, articulation="sustained")
    brass = brass_gen.render(chords, SCALE_D_BEMOL_MAJOR, duration)
    for b in brass:
        import math
        wave = math.sin((b.start / duration) * 2 * math.pi)
        b.expression[11] = int(50 + wave * 45)
        
    return {
        "Harp": harp,
        "Violins": strings,
        "Brass": brass,
    }, 72.0


# ===========================================================================
# 15. Orchestra of the Forgotten Stars
# ===========================================================================
def produce_forgotten_stars():
    print("Writing Work 15: Orchestra of the Forgotten Stars...")
    # Star fading: every 8 beats, an instrument fades out completely and goes silent (9 sections x 8 = 72 beats total)
    duration = 72.0
    chords = _build_chords("i iv v i i iv v i i iv v i", duration, SCALE_G_SHARP_MINOR)
    
    # Piccolo/Flute (beats 0-8)
    flute = [NoteInfo(pitch=80, start=i * 2.0, duration=1.5, velocity=85) for i in range(4)]
    
    # Oboes (beats 0-16)
    oboe = [NoteInfo(pitch=75, start=i * 2.0, duration=1.5, velocity=80) for i in range(8)]
    
    # Trumpets (beats 0-24)
    trumpets = [NoteInfo(pitch=70, start=i * 2.5, duration=2.0, velocity=85) for i in range(10)]
    
    # French Horns (beats 0-32)
    horns = [NoteInfo(pitch=63, start=i * 2.5, duration=2.0, velocity=80) for i in range(13)]
    
    # Clarinets (beats 0-40)
    clarinets = [NoteInfo(pitch=58, start=i * 2.0, duration=1.5, velocity=75) for i in range(20)]
    
    # Bassoons & Tuba (beats 0-48)
    tuba = [NoteInfo(pitch=35, start=i * 3.0, duration=2.5, velocity=90) for i in range(16)]
    
    # Violas & Violins II (beats 0-56)
    v2 = [NoteInfo(pitch=68, start=i * 2.0, duration=1.5, velocity=75) for i in range(28)]
    
    # Violins I (beats 0-64)
    v1 = [NoteInfo(pitch=73, start=i * 2.0, duration=1.5, velocity=80) for i in range(32)]
    
    # Double Bass Solo (beats 0-72, remaining final star)
    bass = [NoteInfo(pitch=28, start=i * 3.0, duration=2.5, velocity=70) for i in range(24)]
    
    # Add a final bar of 10-second silence (represented by a NoteInfo with 0 velocity and long duration at the end)
    bass.append(NoteInfo(pitch=28, start=72.0, duration=10.0, velocity=0))
    
    # Combine woodwinds, brass, strings
    wood = flute + oboe + clarinets
    brass = trumpets + horns
    
    return {
        "Woodwinds": wood,
        "Brass": brass,
        "Tuba": tuba,
        "Violins": v1,
        "Violins_II": v2,
        "Pizzicato": bass,
    }, 42.0


# ===========================================================================
# Main Execution Entrypoint
# ===========================================================================
def main():
    album_dir = Path("output/album_15_symphonic_works")
    album_dir.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "=" * 80)
    print("   THE SYMPHONIC LEGACY — 15 Symphonic Works Masterpiece Album")
    print("   Physical-Model Orchestration Engine & Continuous Controllers")
    print("=" * 80 + "\n")
    
    # Work 1
    w1_raw, w1_bpm = produce_celestial_dominion()
    w1_m, w1_pan = apply_orchestral_mix(w1_raw, w1_bpm)
    export_multitrack_midi(
        w1_m, str(album_dir / "01_Celestial_Dominion.mid"),
        bpm=w1_bpm, cc_events=w1_pan,
        instruments={"Violins": 40, "Woodwinds": 73, "Brass": 61, "Choir": 52, "Snare": 115, "Bells": 14},
    )
    
    # Work 2
    w2_raw, w2_bpm = produce_echoes_eternal()
    w2_m, w2_pan = apply_orchestral_mix(w2_raw, w2_bpm)
    export_multitrack_midi(
        w2_m, str(album_dir / "02_Echoes_of_the_Eternal_Orchestra.mid"),
        bpm=w2_bpm, cc_events=w2_pan,
        instruments={"Violins": 40, "Violins_II": 41, "Viola": 42, "Pizzicato": 45},
    )
    
    # Work 3 (4 Movements)
    for m in range(1, 5):
        w3_raw, w3_bpm = produce_horizon_mvt(m)
        w3_m, w3_pan = apply_orchestral_mix(w3_raw, w3_bpm)
        name_map = {1: "North", 2: "East", 3: "South", 4: "West"}
        inst_map = {
            1: {"Woodwinds": 70, "Brass": 60},
            2: {"Woodwinds": 68, "Tremolo": 44, "Harp": 46},
            3: {"Woodwinds": 71, "Snare": 115},
            4: {"Violins": 40, "Brass": 61, "Bells": 14}
        }
        export_multitrack_midi(
            w3_m, str(album_dir / f"03_Symphony_of_the_Four_Horizons_{name_map[m]}.mid"),
            bpm=w3_bpm, cc_events=w3_pan,
            instruments=inst_map[m],
        )
        
    # Work 4
    w4_raw, w4_bpm = produce_imperial_suite()
    w4_m, w4_pan = apply_orchestral_mix(w4_raw, w4_bpm)
    export_multitrack_midi(
        w4_m, str(album_dir / "04_The_Grand_Imperial_Suite.mid"),
        bpm=w4_bpm, cc_events=w4_pan,
        instruments={"Violins": 40, "Brass": 61, "Snare": 115, "Woodwinds": 73},
    )
    
    # Work 5
    w5_raw, w5_bpm = produce_nocturne()
    w5_m, w5_pan = apply_orchestral_mix(w5_raw, w5_bpm)
    export_multitrack_midi(
        w5_m, str(album_dir / "05_Nocturne_of_the_Silver_Kingdom.mid"),
        bpm=w5_bpm, cc_events=w5_pan,
        instruments={"Harp": 46, "Violins": 40, "Woodwinds": 73, "Pizzicato": 45},
    )
    
    # Work 6
    w6_raw, w6_bpm = produce_aurora()
    w6_m, w6_pan = apply_orchestral_mix(w6_raw, w6_bpm)
    export_multitrack_midi(
        w6_m, str(album_dir / "06_Aurora_Triumphalis.mid"),
        bpm=w6_bpm, cc_events=w6_pan,
        instruments={"Violins": 40, "Brass": 61, "Choir": 52, "Bells": 14},
    )
    
    # Work 7
    w7_raw, w7_bpm = produce_crimson()
    w7_m, w7_pan = apply_orchestral_mix(w7_raw, w7_bpm)
    export_multitrack_midi(
        w7_m, str(album_dir / "07_Chronicles_of_the_Crimson_Symphony.mid"),
        bpm=w7_bpm, cc_events=w7_pan,
        instruments={"Woodwinds": 73, "Brass": 61, "Snare": 115, "Violins": 40},
    )
    
    # Work 8
    w8_raw, w8_bpm = produce_obsidian()
    w8_m, w8_pan = apply_orchestral_mix(w8_raw, w8_bpm)
    export_multitrack_midi(
        w8_m, str(album_dir / "08_Obsidian_Reverie.mid"),
        bpm=w8_bpm, cc_events=w8_pan,
        instruments={"Pizzicato": 43, "Woodwinds": 70, "Bells": 14, "Violins": 40},
    )
    
    # Work 9
    w9_raw, w9_bpm = produce_royal_overture()
    w9_m, w9_pan = apply_orchestral_mix(w9_raw, w9_bpm)
    export_multitrack_midi(
        w9_m, str(album_dir / "09_The_Last_Royal_Overture.mid"),
        bpm=w9_bpm, cc_events=w9_pan,
        instruments={"Brass": 61, "Violins": 40, "Tuba": 58},
    )
    
    # Work 10
    w10_raw, w10_bpm = produce_infinite_harmonics()
    w10_m, w10_pan = apply_orchestral_mix(w10_raw, w10_bpm)
    export_multitrack_midi(
        w10_m, str(album_dir / "10_Infinite_Harmonics.mid"),
        bpm=w10_bpm, cc_events=w10_pan,
        instruments={"Pizzicato": 43, "Woodwinds": 73},
    )
    
    # Work 11
    w11_raw, w11_bpm = produce_empire_strings_thunder()
    w11_m, w11_pan = apply_orchestral_mix(w11_raw, w11_bpm)
    export_multitrack_midi(
        w11_m, str(album_dir / "11_Empire_of_Strings_and_Thunder.mid"),
        bpm=w11_bpm, cc_events=w11_pan,
        instruments={"Violins": 40, "Pizzicato": 45, "Snare": 115, "Cymbal": 115},
    )
    
    # Work 12
    w12_raw, w12_bpm = produce_luminara()
    w12_m, w12_pan = apply_orchestral_mix(w12_raw, w12_bpm)
    export_multitrack_midi(
        w12_m, str(album_dir / "12_Luminara_A_Symphonic_Journey.mid"),
        bpm=w12_bpm, cc_events=w12_pan,
        instruments={"Woodwinds": 73, "Violins": 40, "Brass": 61, "Cymbal": 115, "Choir": 52, "Bells": 14},
    )
    
    # Work 13 (4 Movements)
    for m in range(1, 5):
        w13_raw, w13_bpm = produce_destiny_mvt(m)
        w13_m, w13_pan = apply_orchestral_mix(w13_raw, w13_bpm)
        name_map = {1: "Awakening", 2: "The_Weight", 3: "Defiance", 4: "Convergence"}
        inst_map = {
            1: {"Violins": 40, "Snare": 115},
            2: {"Violins": 40, "Snare": 115},
            3: {"Brass": 61, "Snare": 115},
            4: {"Violins": 40, "Brass": 61, "Snare": 115}
        }
        export_multitrack_midi(
            w13_m, str(album_dir / f"13_The_Four_Movements_of_Destiny_{name_map[m]}.mid"),
            bpm=w13_bpm, cc_events=w13_pan,
            instruments=inst_map[m],
        )
        
    # Work 14
    w14_raw, w14_bpm = produce_majestic_tides()
    w14_m, w14_pan = apply_orchestral_mix(w14_raw, w14_bpm)
    export_multitrack_midi(
        w14_m, str(album_dir / "14_Majestic_Tides.mid"),
        bpm=w14_bpm, cc_events=w14_pan,
        instruments={"Harp": 46, "Violins": 40, "Brass": 61},
    )
    
    # Work 15
    w15_raw, w15_bpm = produce_forgotten_stars()
    w15_m, w15_pan = apply_orchestral_mix(w15_raw, w15_bpm)
    export_multitrack_midi(
        w15_m, str(album_dir / "15_Orchestra_of_the_Forgotten_Stars.mid"),
        bpm=w15_bpm, cc_events=w15_pan,
        instruments={"Woodwinds": 73, "Brass": 61, "Tuba": 58, "Violins": 40, "Violins_II": 41, "Pizzicato": 43},
    )
    
    print("\n" + "=" * 80)
    print("   PRODUCTION COMPLETE: THE SYMPHONIC LEGACY")
    print(f"   MIDI outputs saved under: {album_dir.resolve()}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
