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
album_nocturne_adagio.py — "Adagios and Nocturnes of the Cosmic Night".

A beautifully slow, expressive, and long symphonic album comprising 5 expansive movements
utilizing our physical-modeling engines, continuous expressions, and spatial mastering desks.
"""

import math
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

# Scales
SCALE_C_SHARP_MINOR = Scale(root=1, mode=Mode.AEOLIAN)
SCALE_F_MAJOR = Scale(root=5, mode=Mode.IONIAN)
SCALE_G_SHARP_MINOR = Scale(root=8, mode=Mode.AEOLIAN)
SCALE_B_FLAT_MINOR = Scale(root=10, mode=Mode.AEOLIAN)
SCALE_D_MAJOR = Scale(root=2, mode=Mode.IONIAN)
SCALE_C_MAJOR = Scale(root=0, mode=Mode.IONIAN)


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


def apply_orchestral_mix(raw_tracks, bpm, lufs=-15.0):
    """Mix and master the raw tracks using the MixingDesk and MasteringDesk."""
    desk = MixingDesk(niche_cfg={})
    
    # Gain settings tailored for highly dynamic ambient slow orchestral works
    desk.track_gains.update({
        "Violins": 0.85,
        "Violins_II": 0.75,
        "Viola": 0.80,
        "Cello": 0.88,
        "Bass": 0.95,
        "Pizzicato": 0.90,
        "Tremolo": 0.80,
        "Brass": 0.85,
        "Woodwinds": 0.88,
        "Choir": 0.82,
        "Hits": 0.95,
        "Tuba": 1.10,
        "Snare": 0.80,
        "Cymbal": 0.75,
        "Bells": 0.92,
        "Harp": 0.95,
    })
    
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan_events = master.apply_mastering(mixed)
    return mastered, pan_events


# ===========================================================================
# Movement I: Adagio Sostenuto (The Deep Void)
# ===========================================================================
def produce_mvt_1():
    print("Writing Movement I: Adagio Sostenuto (The Deep Void)...")
    duration = 64.0
    chords = _build_chords("i iv v i i iv V i", duration, SCALE_C_SHARP_MINOR)
    
    # Background Legato Strings & Choir with slow, breathing CC 11 sweeps
    strings_params = GeneratorParams(density=0.5, key_range_low=52, key_range_high=74)
    strings_gen = StringsLegatoGenerator(strings_params, section_size="ensemble")
    strings = strings_gen.render(chords, SCALE_C_SHARP_MINOR, duration)
    for s in strings:
        # 1-cycle sine wave swell representing cosmic breathing
        wave = math.sin((s.start / duration) * 2 * math.pi)
        s.expression[11] = int(60 + wave * 40)
        
    choir_params = GeneratorParams(density=0.45, key_range_low=49, key_range_high=71)
    choir_gen = ChoirAahsGenerator(choir_params, voice_count=4, syllable="aah")
    choir = choir_gen.render(chords, SCALE_C_SHARP_MINOR, duration)
    for c in choir:
        wave = math.sin((c.start / duration) * 2 * math.pi)
        c.expression[11] = int(50 + wave * 35)
        
    # Solo lyrical Oboe entering in the mid section
    wood_params = GeneratorParams(density=0.5, key_range_low=60, key_range_high=80)
    wood_gen = WoodwindsEnsembleGenerator(wood_params, section="trio")
    oboe = wood_gen.render(chords[2:6], SCALE_C_SHARP_MINOR, 32.0)
    for o in oboe:
        o.start += 16.0
        
    # High-register cosmic violin harmonics
    harmonics = [
        NoteInfo(pitch=88 + (i % 2) * 5, start=4.0 + i * 8.0, duration=3.5, velocity=60, articulation="staccato")
        for i in range(7)
    ]
    strings.extend(harmonics)
    
    return {
        "Violins": strings,
        "Choir": choir,
        "Woodwinds": oboe,
    }, 44.0


# ===========================================================================
# Movement II: Andante Cantabile (Silver Moonlight)
# ===========================================================================
def produce_mvt_2():
    print("Writing Movement II: Nocturne: Andante Cantabile (Silver Moonlight)...")
    duration = 48.0
    chords = _build_chords("I IV V I vi ii V I", duration, SCALE_F_MAJOR)
    
    # Harp arpeggios: fast plucked runs sweeping up and down
    harp = []
    for beat in range(0, 48, 4):
        # Ascending arpeggio
        harp.extend([
            NoteInfo(pitch=57 + s * 3, start=beat + s * 0.25, duration=0.3, velocity=70)
            for s in range(6)
        ])
        
    # Shimmering Bells
    bells_params = GeneratorParams(density=0.2, key_range_low=60, key_range_high=80)
    bells_gen = TubularBellsGenerator(bells_params, stroke_pattern="single", dampen=False)
    bells = bells_gen.render(chords, SCALE_F_MAJOR, duration)
    
    # Lyrical solo Violin
    strings_params = GeneratorParams(density=0.55, key_range_low=60, key_range_high=84)
    strings_gen = StringsLegatoGenerator(strings_params, section_size="solo", portamento_speed=0.2)
    solo_violin = strings_gen.render(chords, SCALE_F_MAJOR, duration)
    
    # Warm French Horn counterpoint
    brass_params = GeneratorParams(density=0.45, key_range_low=50, key_range_high=72)
    brass_gen = BrassSectionGenerator(brass_params, articulation="sustained", intensity=0.7)
    horn = brass_gen.render(chords, SCALE_F_MAJOR, duration)
    
    return {
        "Harp": harp,
        "Bells": bells,
        "Violins": solo_violin,
        "Brass": horn,
    }, 52.0


# ===========================================================================
# Movement III: Adagio Doloroso (Chronicles of a Lost Star)
# ===========================================================================
def produce_mvt_3():
    print("Writing Movement III: Adagio Doloroso (Chronicles of a Lost Star)...")
    duration = 64.0
    chords = _build_chords("i VI iv v i VI iv v", duration, SCALE_G_SHARP_MINOR)
    
    # Shimmering Tremolo Strings
    trem_params = GeneratorParams(density=0.6, key_range_low=56, key_range_high=78)
    trem_gen = TremoloStringsGenerator(trem_params, bow_speed=0.06, dynamic_swell=True)
    tremolo = trem_gen.render(chords, SCALE_G_SHARP_MINOR, duration)
    for t in tremolo:
        # Dynamic CC 11 sweeps
        ratio = t.start / duration
        t.expression[11] = int(50 + 60 * math.sin(ratio * math.pi))
        
    # Foundation: Deep low Tuba growls
    tuba_params = GeneratorParams(density=0.5, key_range_low=29, key_range_high=45)
    tuba_gen = TubaGenerator(tuba_params, articulation="swell", growl=True)
    tuba = tuba_gen.render(chords, SCALE_G_SHARP_MINOR, duration)
    
    # Crescendo Snare rolls building up to beat 48
    snare_params = GeneratorParams(density=0.65)
    snare_gen = SnareDrumGenerator(snare_params, pattern_type="roll")
    snare = snare_gen.render(chords[:6], SCALE_G_SHARP_MINOR, 48.0)
    for sn in snare:
        # Increase velocity over time (crescendo)
        ratio = sn.start / 48.0
        sn.velocity = int(45 + ratio * 70)
        
    # Climax BRAAM Hit at beat 48
    hit_params = GeneratorParams(density=1.0, key_range_low=32, key_range_high=56)
    hit_gen = OrchestralHitGenerator(hit_params, hit_type="braam", duration=3.0, reverb_tail=4.0)
    climax_hit = hit_gen.render([chords[6]], SCALE_G_SHARP_MINOR, 8.0)
    for h in climax_hit:
        h.start = 48.0
        h.velocity = 127
        
    return {
        "Tremolo": tremolo,
        "Tuba": tuba,
        "Snare": snare,
        "Hits": climax_hit,
    }, 40.0


# ===========================================================================
# Movement IV: Nocturne: Mysterioso (Starlight Dance)
# ===========================================================================
def produce_mvt_4():
    print("Writing Movement IV: Nocturne: Mysterioso (Starlight Dance)...")
    duration = 48.0
    chords = _build_chords("i iv VI v i iv VI v", duration, SCALE_B_FLAT_MINOR)
    
    # Sparse pizzicatos (arco_mix pattern)
    pizz_params = GeneratorParams(density=0.45, key_range_low=52, key_range_high=74)
    pizz_gen = StringsPizzicatoGenerator(pizz_params, pattern="arco_mix", snap_chance=0.2)
    pizz = pizz_gen.render(chords, SCALE_B_FLAT_MINOR, duration)
    for p in pizz:
        p.velocity = max(1, int(p.velocity * 0.65)) # Soft starlight velocity
        
    # Breathing Woodwinds (Clarinet & Bassoon)
    wood_params = GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)
    wood_gen = WoodwindsEnsembleGenerator(wood_params, section="trio", breath_interval=4.0)
    woodwinds = wood_gen.render(chords, SCALE_B_FLAT_MINOR, duration)
    
    # Rare high bell chimes
    bells_params = GeneratorParams(density=0.15, key_range_low=65, key_range_high=84)
    bells_gen = TubularBellsGenerator(bells_params, stroke_pattern="motif", dampen=False)
    bells = bells_gen.render(chords, SCALE_B_FLAT_MINOR, duration)
    
    return {
        "Pizzicato": pizz,
        "Woodwinds": woodwinds,
        "Bells": bells,
    }, 48.0


# ===========================================================================
# Movement V: Adagio Maestoso (Dawn of the Infinite)
# ===========================================================================
def produce_mvt_5():
    print("Writing Movement V: Adagio Maestoso (Dawn of the Infinite)...")
    duration = 80.0
    
    # C Major to D Major modulation
    chords_c = _build_chords("I IV V I vi ii V I", 40.0, SCALE_C_MAJOR)
    chords_d = _build_chords("I IV V I vi ii V I", 40.0, SCALE_D_MAJOR)
    for c in chords_d: c.start += 40.0
    
    chords_all = chords_c + chords_d
    
    # Grand slow-building legato crescendo
    strings_params = GeneratorParams(density=0.6, key_range_low=54, key_range_high=80)
    strings_gen = StringsLegatoGenerator(strings_params)
    strings = strings_gen.render(chords_all, SCALE_D_MAJOR, duration)
    for s in strings:
        ratio = s.start / duration
        s.expression[11] = int(35 + ratio * 85) # Sweeping crescendo
        
    # Brass Fanfare Swells
    brass_params = GeneratorParams(density=0.5, key_range_low=50, key_range_high=74)
    brass_gen = BrassSectionGenerator(brass_params, articulation="fanfare")
    brass = brass_gen.render(chords_all, SCALE_D_MAJOR, duration)
    for b in brass:
        ratio = b.start / duration
        b.expression[11] = int(20 + ratio * 100)
        
    # Swelling Choir
    choir_params = GeneratorParams(density=0.45, key_range_low=52, key_range_high=76)
    choir_gen = ChoirAahsGenerator(choir_params, voice_count=4, syllable="aah")
    choir = choir_gen.render(chords_all, SCALE_D_MAJOR, duration)
    for c in choir:
        ratio = c.start / duration
        c.expression[11] = int(30 + ratio * 90)
        c.expression[74] = int(40 + ratio * 75)
        
    # Cymbal rolls and crash hits at the phrase edges
    cymbal_params = GeneratorParams(density=0.35)
    cymbal_gen = OrchestralCymbalGenerator(cymbal_params, pattern_type="rolls")
    cymbal = cymbal_gen.render(chords_all, SCALE_D_MAJOR, duration)
    
    # Heavy chimes
    bells_params = GeneratorParams(density=0.35, key_range_low=55, key_range_high=78)
    bells_gen = TubularBellsGenerator(bells_params, stroke_pattern="motif", dampen=False)
    bells = bells_gen.render(chords_all, SCALE_D_MAJOR, duration)
    
    # Expansive final chord (D Major, beat 72) slowly fading to 0
    final_strings = [
        NoteInfo(pitch=50, start=72.0, duration=8.0, velocity=90),
        NoteInfo(pitch=57, start=72.0, duration=8.0, velocity=90),
        NoteInfo(pitch=62, start=72.0, duration=8.0, velocity=90),
        NoteInfo(pitch=66, start=72.0, duration=8.0, velocity=90),
        NoteInfo(pitch=69, start=72.0, duration=8.0, velocity=90),
    ]
    # Sweeping final chord CC 11 down to 0
    for f in final_strings:
        f.expression[11] = [(0.0, 100), (2.0, 80), (4.0, 50), (6.0, 20), (8.0, 0)]
    strings.extend(final_strings)
    
    return {
        "Violins": strings,
        "Brass": brass,
        "Choir": choir,
        "Cymbal": cymbal,
        "Bells": bells,
    }, 60.0


# ===========================================================================
# Main Execution Entrypoint
# ===========================================================================
def main():
    album_dir = Path("output/album_nocturne_adagio")
    album_dir.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "=" * 80)
    print("   ADAGIOS & NOCTURNES OF THE COSMIC NIGHT — 5-Movement Atmospheric Album")
    print("   Continuous Expressions, Swells & Physical-Modeling Articulations")
    print("=" * 80 + "\n")
    
    # Movement I
    w1_raw, w1_bpm = produce_mvt_1()
    w1_m, w1_pan = apply_orchestral_mix(w1_raw, w1_bpm)
    export_multitrack_midi(
        w1_m, str(album_dir / "01_Mvt_I_Adagio_Sostenuto_The_Deep_Void.mid"),
        bpm=w1_bpm, cc_events=w1_pan,
        instruments={"Violins": 40, "Choir": 52, "Woodwinds": 73},
    )
    
    # Movement II
    w2_raw, w2_bpm = produce_mvt_2()
    w2_m, w2_pan = apply_orchestral_mix(w2_raw, w2_bpm)
    export_multitrack_midi(
        w2_m, str(album_dir / "02_Mvt_II_Nocturne_Andante_Cantabile_Silver_Moonlight.mid"),
        bpm=w2_bpm, cc_events=w2_pan,
        instruments={"Harp": 46, "Bells": 14, "Violins": 40, "Brass": 60},
    )
    
    # Movement III
    w3_raw, w3_bpm = produce_mvt_3()
    w3_m, w3_pan = apply_orchestral_mix(w3_raw, w3_bpm)
    export_multitrack_midi(
        w3_m, str(album_dir / "03_Mvt_III_Adagio_Doloroso_Chronicles_of_a_Lost_Star.mid"),
        bpm=w3_bpm, cc_events=w3_pan,
        instruments={"Tremolo": 44, "Tuba": 58, "Snare": 115, "Hits": 55},
    )
    
    # Movement IV
    w4_raw, w4_bpm = produce_mvt_4()
    w4_m, w4_pan = apply_orchestral_mix(w4_raw, w4_bpm)
    export_multitrack_midi(
        w4_m, str(album_dir / "04_Mvt_IV_Nocturne_Mysterioso_Starlight_Dance.mid"),
        bpm=w4_bpm, cc_events=w4_pan,
        instruments={"Pizzicato": 45, "Woodwinds": 73, "Bells": 14},
    )
    
    # Movement V
    w5_raw, w5_bpm = produce_mvt_5()
    w5_m, w5_pan = apply_orchestral_mix(w5_raw, w5_bpm)
    export_multitrack_midi(
        w5_m, str(album_dir / "05_Mvt_V_Adagio_Maestoso_Dawn_of_the_Infinite.mid"),
        bpm=w5_bpm, cc_events=w5_pan,
        instruments={"Violins": 40, "Brass": 61, "Choir": 52, "Cymbal": 115, "Bells": 14},
    )
    
    print("\n" + "=" * 80)
    print("   PRODUCTION COMPLETE: ADAGIOS & NOCTURNES OF THE COSMIC NIGHT")
    print(f"   MIDI outputs saved under: {album_dir.resolve()}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
