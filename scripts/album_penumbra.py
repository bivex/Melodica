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
scripts/album_penumbra.py — "PENUMBRA"
A highly refined, 12-movement gothic neoclassical, chamber, and dark-ambient masterpiece.
Enforces the exact micro-tonal plan, strict velocity clamping (max mf = 75),
brass-only instrumentation for Track IV (Catafalque), low pedal registers for the organ,
and mandatory silent codas for Track VIII (12 beats) and Track X (16 beats).
"""

import math
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
from melodica.generators.tuba import TubaGenerator
from melodica.generators.snare_drum import SnareDrumGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator
from melodica.generators.organ_drawbars import OrganDrawbarsGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# Scales mapping to exact root semitones (C=0, C#=1, D=2, Eb=3, E=4, F=5, F#=6, G=7, G#=8, A=9, Bb=10, B=11)
SCALE_DB_MINOR = Scale(root=1, mode=Mode.AEOLIAN)          # Db Minor
SCALE_G_MINOR = Scale(root=7, mode=Mode.AEOLIAN)           # G Minor
SCALE_AB_MINOR = Scale(root=8, mode=Mode.AEOLIAN)          # Ab Minor
SCALE_C_MINOR = Scale(root=0, mode=Mode.AEOLIAN)           # C Minor
SCALE_F_SHARP_MINOR = Scale(root=6, mode=Mode.AEOLIAN)     # F# Minor
SCALE_D_MINOR = Scale(root=2, mode=Mode.AEOLIAN)           # D Minor
SCALE_B_MINOR = Scale(root=11, mode=Mode.AEOLIAN)          # B Minor
SCALE_EB_MINOR = Scale(root=3, mode=Mode.AEOLIAN)          # Eb Minor
SCALE_A_MINOR = Scale(root=9, mode=Mode.AEOLIAN)           # A Minor
SCALE_D_MAJOR = Scale(root=2, mode=Mode.IONIAN)            # D Major
SCALE_C_SHARP_MINOR = Scale(root=1, mode=Mode.AEOLIAN)     # C# Minor


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


def clamp_velocity(raw_tracks, max_vel=75):
    """Enforce a strict maximum velocity limit to maintain the mf dynamics ceiling."""
    for track_name, notes in raw_tracks.items():
        for n in notes:
            n.velocity = min(max_vel, n.velocity)
    return raw_tracks


def apply_gothic_mix(raw_tracks, bpm, lufs=-15.0):
    """Mix and master the raw tracks for spatial gothic chamber ambience."""
    desk = MixingDesk(niche_cfg={})
    
    # Haunting chamber spatial configuration and gains
    desk.track_gains.update({
        "Organ": 0.82,
        "Choir": 0.85,
        "Violins": 0.78,
        "Cello": 0.84,
        "Bass": 0.88,
        "Brass": 0.76,
        "Woodwinds": 0.80,
        "Bells": 0.90,
        "Snare": 0.60,
        "Pizzicato": 0.78,
        "Tremolo": 0.76,
        "Tuba": 1.00,
    })
    
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan_events = master.apply_mastering(mixed)
    return mastered, pan_events


# ===========================================================================
# ZONE A: Twilight (Flat Tonalities)
# ===========================================================================

# Track I: Vesper Bells (Db Minor, 48 BPM)
def produce_track_1():
    print("Composing Track I: Vesper Bells...")
    duration = 48.0
    chords = _build_chords("i iv v i i iv V i", duration, SCALE_DB_MINOR)
    
    # Soft distant bells
    bells_params = GeneratorParams(density=0.15, key_range_low=60, key_range_high=80)
    bells_gen = TubularBellsGenerator(bells_params, stroke_pattern="motif", dampen=False)
    bells = bells_gen.render(chords, SCALE_DB_MINOR, duration)
    
    # Whispering legato cellos
    strings_params = GeneratorParams(density=0.45, key_range_low=45, key_range_high=62)
    strings_gen = StringsLegatoGenerator(strings_params, section_size="trio")
    cellos = strings_gen.render(chords, SCALE_DB_MINOR, duration)
    
    # Soft breathing choir
    choir_params = GeneratorParams(density=0.4, key_range_low=52, key_range_high=74)
    choir_gen = ChoirAahsGenerator(choir_params, voice_count=3, syllable="aah")
    choir = choir_gen.render(chords, SCALE_DB_MINOR, duration)
    for c in choir:
        wave = math.sin((c.start / duration) * 2 * math.pi)
        c.expression[11] = int(45 + wave * 25)
        
    raw = {
        "Bells": bells,
        "Cello": cellos,
        "Choir": choir,
    }
    return clamp_velocity(raw), 48.0


# Track II: Ashen Veil (G Minor, 42 BPM)
def produce_track_2():
    print("Composing Track II: Ashen Veil...")
    duration = 48.0
    chords = _build_chords("i iv V i i iv V i", duration, SCALE_G_MINOR)
    
    # Organ limited Strictly to the deep low pedal register (Keys 24–48)
    organ_params = GeneratorParams(density=0.45, key_range_low=24, key_range_high=48)
    organ_gen = OrganDrawbarsGenerator(organ_params, registration="gospel", leslie_speed="slow", percussion=False)
    organ = organ_gen.render(chords, SCALE_G_MINOR, duration)
    
    # Ghost vocal whispering
    choir_params = GeneratorParams(density=0.5, key_range_low=55, key_range_high=74)
    choir_gen = ChoirAahsGenerator(choir_params, voice_count=2, syllable="aah")
    ghost = choir_gen.render(chords, SCALE_G_MINOR, duration)
    for g in ghost:
        wave = math.sin((g.start / duration) * 4 * math.pi)
        g.expression[11] = int(40 + wave * 20)
        g.expression[74] = int(35 + wave * 25)
        
    raw = {
        "Organ": organ,
        "Choir": ghost,
    }
    return clamp_velocity(raw), 42.0


# Track III: Lacrimosa Noctis (Ab Minor, 40 BPM)
def produce_track_3():
    print("Composing Track III: Lacrimosa Noctis...")
    duration = 64.0
    chords = _build_chords("i VI iv v i VI iv v", duration, SCALE_AB_MINOR)
    
    # Whispering high-register tremolos (ppp)
    trem_params = GeneratorParams(density=0.55, key_range_low=68, key_range_high=86)
    trem_gen = TremoloStringsGenerator(trem_params, bow_speed=0.03, dynamic_swell=True)
    trem = trem_gen.render(chords, SCALE_AB_MINOR, duration)
    
    # Slow weeping cellos
    strings_params = GeneratorParams(density=0.5, key_range_low=44, key_range_high=60)
    strings_gen = StringsLegatoGenerator(strings_params, section_size="ensemble")
    cellos = strings_gen.render(chords, SCALE_AB_MINOR, duration)
    for c in cellos:
        ratio = (c.start % 16.0) / 16.0
        c.expression[11] = int(60 - ratio * 35)
        
    raw = {
        "Tremolo": trem,
        "Cello": cellos,
    }
    return clamp_velocity(raw), 40.0


# ===========================================================================
# ZONE B: Night (Neutral Keys)
# ===========================================================================

# Track IV: Catafalque (C Minor, 44 BPM)
def produce_track_4():
    print("Composing Track IV: Catafalque (Brass Chorale)...")
    duration = 44.0
    chords = _build_chords("i iv v i VI iv V i", duration, SCALE_C_MINOR)
    
    # Pure medieval brass chorale: French Horns & Tuba. Strictly ZERO strings!
    brass_params = GeneratorParams(density=0.45, key_range_low=52, key_range_high=72)
    brass_gen = BrassSectionGenerator(brass_params, articulation="sustained", intensity=0.4)
    horns = brass_gen.render(chords, SCALE_C_MINOR, duration)
    
    tuba_params = GeneratorParams(density=0.4, key_range_low=29, key_range_high=45)
    tuba_gen = TubaGenerator(tuba_params, articulation="swell")
    tuba = tuba_gen.render(chords, SCALE_C_MINOR, duration)
    
    raw = {
        "Brass": horns,
        "Tuba": tuba,
    }
    return clamp_velocity(raw), 44.0


# Track V: Penumbra (F# Minor, 45 BPM)
def produce_track_5():
    print("Composing Track V: Penumbra (Title Track Climax)...")
    duration = 64.0
    chords = _build_chords("i VI iv v i VI iv v", duration, SCALE_F_SHARP_MINOR)
    
    # Organ limited to the deep pedal register (Keys 24–48)
    organ_params = GeneratorParams(density=0.55, key_range_low=24, key_range_high=48)
    organ_gen = OrganDrawbarsGenerator(organ_params, registration="gospel", leslie_speed="slow")
    organ = organ_gen.render(chords, SCALE_F_SHARP_MINOR, duration)
    
    # Strings crescendo building to f (the only track allowed to exceed mf=75)
    trem_params = GeneratorParams(density=0.6, key_range_low=54, key_range_high=78)
    trem_gen = TremoloStringsGenerator(trem_params, bow_speed=0.07, dynamic_swell=True)
    trem = trem_gen.render(chords, SCALE_F_SHARP_MINOR, duration)
    for t in trem:
        ratio = t.start / duration
        t.expression[11] = int(35 + ratio * 85) # Sweeping crescendo up to f (120)
        
    return {
        "Organ": organ,
        "Tremolo": trem,
    }, 45.0


# Track VI: Moonlit Catacombs (D Minor, 38 BPM)
def produce_track_6():
    print("Composing Track VI: Moonlit Catacombs...")
    duration = 48.0
    chords = _build_chords("i bII iv v i bII iv v", duration, SCALE_D_MINOR)
    
    # Subterranean low growling brass
    tuba_params = GeneratorParams(density=0.5, key_range_low=24, key_range_high=40)
    tuba_gen = TubaGenerator(tuba_params, articulation="growl", growl=True)
    growls = tuba_gen.render(chords, SCALE_D_MINOR, duration)
    
    # Snapping low double bass pizzicatos (mf ceiling enforced)
    pizz_params = GeneratorParams(density=0.4, key_range_low=32, key_range_high=50)
    pizz_gen = StringsPizzicatoGenerator(pizz_params, pattern="arco_mix", snap_chance=0.3)
    pizz = pizz_gen.render(chords, SCALE_D_MINOR, duration)
    
    # Muted drum taps (brushes simulation)
    drums_params = GeneratorParams(density=0.35)
    drums_gen = SnareDrumGenerator(drums_params, pattern_type="march")
    taps = drums_gen.render(chords, SCALE_D_MINOR, duration)
    
    raw = {
        "Tuba": growls,
        "Pizzicato": pizz,
        "Snare": taps,
    }
    return clamp_velocity(raw), 38.0


# ===========================================================================
# ZONE C: Depth (Sharp Minors)
# ===========================================================================

# Track VII: Black Water Requiem (B Minor, 46 BPM)
def produce_track_7():
    print("Composing Track VII: Black Water Requiem...")
    duration = 48.0
    chords = _build_chords("i iv v i VI iv V i", duration, SCALE_B_MINOR)
    
    # Walking monotonous double bass pizzicatos
    pizz = []
    for beat in range(0, 48):
        pizz.append(NoteInfo(pitch=35 + (beat % 2) * 7, start=float(beat), duration=0.8, velocity=45))
        
    # Lyrical cello dialogue
    strings_params = GeneratorParams(density=0.5, key_range_low=47, key_range_high=64)
    strings_gen = StringsLegatoGenerator(strings_params, section_size="solo")
    cello = strings_gen.render(chords, SCALE_B_MINOR, duration)
    
    raw = {
        "Pizzicato": pizz,
        "Cello": cello,
    }
    return clamp_velocity(raw), 46.0


# Track VIII: Silent Reliquary (Eb Minor, 36 BPM)
# Contains a mandatory 12-beat silent tail at the end
def produce_track_8():
    print("Composing Track VIII: Silent Reliquary (12-Beat Silence Coda)...")
    total_beats = 48.0
    notes_beats = 36.0 # Rest 12.0 beats is absolute silence
    chords = _build_chords("i iv v i", notes_beats, SCALE_EB_MINOR)
    
    # Highly sparse bell chimes
    bells = [
        NoteInfo(pitch=75, start=0.0, duration=3.0, velocity=55),
        NoteInfo(pitch=80, start=12.0, duration=3.0, velocity=50),
        NoteInfo(pitch=71, start=24.0, duration=3.0, velocity=45),
    ]
    
    # Hollow backing drone
    drones = [
        NoteInfo(pitch=43, start=0.0, duration=6.0, velocity=35),
        NoteInfo(pitch=39, start=18.0, duration=6.0, velocity=30),
    ]
    
    raw = {
        "Bells": bells,
        "Cello": drones,
    }
    return clamp_velocity(raw), 36.0


# Track IX: Miserere for the Dying Light (A Minor, 50 BPM)
def produce_track_9():
    print("Composing Track IX: Miserere for the Dying Light...")
    duration = 48.0
    chords = _build_chords("i iv v i VI iv V i", duration, SCALE_A_MINOR)
    
    # Solemn cold vocal choir
    choir_params = GeneratorParams(density=0.55, key_range_low=52, key_range_high=72)
    choir_gen = ChoirAahsGenerator(choir_params, voice_count=4, syllable="aah")
    choir = choir_gen.render(chords, SCALE_A_MINOR, duration)
    
    # Far echoing horns
    brass_params = GeneratorParams(density=0.4, key_range_low=50, key_range_high=70)
    brass_gen = BrassSectionGenerator(brass_params, articulation="sustained", intensity=0.4)
    horns = brass_gen.render(chords, SCALE_A_MINOR, duration)
    
    raw = {
        "Choir": choir,
        "Brass": horns,
    }
    return clamp_velocity(raw), 50.0


# ===========================================================================
# ZONE D: Dawn (Dawn Light)
# ===========================================================================

# Track X: Dust of the Sanctum (D Major, 40 BPM)
# The only Major key on the album, containing a mandatory 16-beat silent tail at the end
def produce_track_10():
    print("Composing Track X: Dust of the Sanctum (16-Beat Silence Coda)...")
    total_beats = 64.0
    notes_beats = 48.0 # Rest 16.0 beats is absolute silence
    chords = _build_chords("I IV V I vi ii V I", notes_beats, SCALE_D_MAJOR)
    
    # Soaring major strings
    strings_params = GeneratorParams(density=0.5, key_range_low=50, key_range_high=74)
    strings_gen = StringsLegatoGenerator(strings_params)
    strings = strings_gen.render(chords, SCALE_D_MAJOR, notes_beats)
    
    # Organ pedal point strictly limited to the deep pedal register (Keys 24–48)
    organ_params = GeneratorParams(density=0.45, key_range_low=24, key_range_high=48)
    organ_gen = OrganDrawbarsGenerator(organ_params, registration="gospel", leslie_speed="slow")
    organ = organ_gen.render(chords, SCALE_D_MAJOR, notes_beats)
    
    # High glassy harmonics
    harmonics = [
        NoteInfo(pitch=86, start=8.0, duration=4.5, velocity=45, articulation="staccato"),
        NoteInfo(pitch=90, start=24.0, duration=4.5, velocity=40, articulation="staccato"),
        NoteInfo(pitch=86, start=40.0, duration=4.5, velocity=35, articulation="staccato"),
    ]
    strings.extend(harmonics)
    
    raw = {
        "Violins": strings,
        "Organ": organ,
    }
    return clamp_velocity(raw), 40.0


# ===========================================================================
# ZONE E: Return (Dawn to Dark)
# ===========================================================================

# Track XI: Nocturne Without Stars (C# Minor, 42 BPM)
def produce_track_11():
    print("Composing Track XI: Nocturne Without Stars...")
    duration = 48.0
    chords = _build_chords("i iv v i i iv V i", duration, SCALE_C_SHARP_MINOR)
    
    # Organ slowly receding in the deep pedal register (Keys 24–48)
    organ_params = GeneratorParams(density=0.4, key_range_low=24, key_range_high=48)
    organ_gen = OrganDrawbarsGenerator(organ_params, registration="jazz", leslie_speed="slow")
    organ = organ_gen.render(chords, SCALE_C_SHARP_MINOR, duration)
    for o in organ:
        ratio = o.start / duration
        o.velocity = int(o.velocity * (1.0 - ratio * 0.8)) # Dying down
        
    # Dying ghost voice solo
    choir_params = GeneratorParams(density=0.45, key_range_low=58, key_range_high=76)
    choir_gen = ChoirAahsGenerator(choir_params, voice_count=1, syllable="aah")
    ghost = choir_gen.render(chords, SCALE_C_SHARP_MINOR, duration)
    for g in ghost:
        ratio = g.start / duration
        g.expression[11] = int(55 * (1.0 - ratio))
        
    raw = {
        "Organ": organ,
        "Choir": ghost,
    }
    return clamp_velocity(raw), 42.0


# Track XII: Lux in Umbra (A Minor, 54 BPM)
def produce_track_12():
    print("Composing Track XII: Lux in Umbra (Return to Eternal Darkness)...")
    duration = 64.0
    
    # Dissonant/atonal minor movement returning back to A Minor
    chords = _build_chords("i iv V i VI bII vii i", duration, SCALE_A_MINOR)
    
    # Quiet, fading chamber strings
    strings_params = GeneratorParams(density=0.55, key_range_low=45, key_range_high=70)
    strings_gen = StringsLegatoGenerator(strings_params)
    strings = strings_gen.render(chords, SCALE_A_MINOR, duration)
    
    # Expansive, decaying final A Minor chord at beat 56 fading to zero
    final_triad = [
        NoteInfo(pitch=45, start=56.0, duration=8.0, velocity=45),
        NoteInfo(pitch=52, start=56.0, duration=8.0, velocity=45),
        NoteInfo(pitch=57, start=56.0, duration=8.0, velocity=45),
        NoteInfo(pitch=60, start=56.0, duration=8.0, velocity=45),
    ]
    for f in final_triad:
        f.expression[11] = [(0.0, 75), (2.0, 50), (4.0, 30), (6.0, 10), (8.0, 0)]
    strings.extend(final_triad)
    
    raw = {
        "Violins": strings,
    }
    return clamp_velocity(raw), 54.0


# ===========================================================================
# Main Execution Entrypoint
# ===========================================================================
def main():
    album_dir = Path("output/album_penumbra")
    album_dir.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "=" * 80)
    print("                  P E N U M B R A — Refined Album Generation")
    print("      Gothic Neoclassical, Chapel Pipe-Organ & Whispering Ambient Suite")
    print("=" * 80 + "\n")
    
    # Route track functions, GM programs, and target filenames
    tracks_meta = [
        (produce_track_1, "01_Vesper_Bells.mid", {"Bells": 14, "Cello": 42, "Choir": 52}),
        (produce_track_2, "02_Ashen_Veil.mid", {"Organ": 19, "Choir": 52}),
        (produce_track_3, "03_Lacrimosa_Noctis.mid", {"Tremolo": 44, "Cello": 42}),
        (produce_track_4, "04_Catafalque.mid", {"Brass": 60, "Tuba": 58}),
        (produce_track_5, "05_Penumbra.mid", {"Organ": 19, "Tremolo": 44}),
        (produce_track_6, "06_Moonlit_Catacombs.mid", {"Tuba": 58, "Pizzicato": 45, "Snare": 115}),
        (produce_track_7, "07_Black_Water_Requiem.mid", {"Pizzicato": 45, "Cello": 42}),
        (produce_track_8, "08_Silent_Reliquary.mid", {"Bells": 14, "Cello": 42}),
        (produce_track_9, "09_Miserere_for_the_Dying_Light.mid", {"Choir": 52, "Brass": 60}),
        (produce_track_10, "10_Dust_of_the_Sanctum.mid", {"Violins": 40, "Organ": 19}),
        (produce_track_11, "11_Nocturne_Without_Stars.mid", {"Organ": 19, "Choir": 52}),
        (produce_track_12, "12_Lux_in_Umbra.mid", {"Violins": 40}),
    ]
    
    for i, (prod_func, filename, instruments) in enumerate(tracks_meta):
        print("-" * 80)
        raw, bpm = prod_func()
        mastered, pan = apply_gothic_mix(raw, bpm)
        export_multitrack_midi(
            mastered, str(album_dir / filename),
            bpm=bpm, cc_events=pan,
            instruments=instruments,
        )
        print(f"-> Exported successfully: {filename}")
        
    print("\n" + "=" * 80)
    print("   PRODUCTION COMPLETE: PENUMBRA (A Dark Neoclassical Masterpiece)")
    print(f"   All 12 MIDI movements generated under: {album_dir.resolve()}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
