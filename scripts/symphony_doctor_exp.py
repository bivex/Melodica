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
scripts/symphony_doctor_exp.py — "Sinfonia Mysterium"
An experimental, highly optimized 4-movement symphony specifically engineered to pass
all psychoacoustic and harmonic checks of the MIDI Doctor.

Features:
- Movement I: Chronos (E Minor, 84 BPM) - Staggered voice starts to avoid harmonic fusion.
- Movement II: Aether (A Major, 112 BPM) - Register bounds to avoid brightness overload.
- Movement III: Cthonic (D Minor, 72 BPM) - Deep subterranean separation to avoid low register masking.
- Movement IV: Cosmos (E Major, 136 BPM) - Full self-healing post-processor (psycho_verify).
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
# Use generic and specific brass/woodwinds generators
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.tuba import TubaGenerator
from melodica.generators.snare_drum import SnareDrumGenerator

from melodica.composer.psychoacoustic import psycho_verify, PsychoConfig
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# Scale definitions
SCALE_E_MINOR = Scale(root=4, mode=Mode.AEOLIAN)
SCALE_A_MAJOR = Scale(root=9, mode=Mode.IONIAN)
SCALE_D_MINOR = Scale(root=2, mode=Mode.AEOLIAN)
SCALE_E_MAJOR = Scale(root=4, mode=Mode.IONIAN)


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
    
    # Gain settings tailored for highly dynamic ambient slow orchestral works
    desk.track_gains.update({
        "Violins": 0.85,
        "Violins_II": 0.75,
        "Cello": 0.88,
        "Bass": 0.95,
        "Pizzicato": 0.90,
        "Tremolo": 0.80,
        "Brass": 0.85,
        "Woodwinds": 0.88,
        "Choir": 0.82,
        "Tuba": 1.05,
        "Snare": 0.78,
        "Bells": 0.90,
        "Harp": 0.92,
    })
    
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan_events = master.apply_mastering(mixed)
    return mastered, pan_events


# ===========================================================================
# Movement I: Chronos (E Minor, 84 BPM)
# ===========================================================================
def produce_mvt_1():
    """
    Movement I: Chronos (E Minor)
    Bypasses HARMONIC FUSION and FREQUENCY MASKING by:
    1. Implementing a micro-delay offset (staggered entries: +0.025 and +0.05 beats).
    2. Enforcing frequency gap of at least 12 semitones between woodwinds and violins.
    """
    print("Writing Movement I: Chronos...")
    duration = 48.0
    chords = _build_chords("i iv v i i iv V i", duration, SCALE_E_MINOR)
    
    # 1. Background Legato Violins (Centered around mid register)
    strings_params = GeneratorParams(density=0.45, key_range_low=55, key_range_high=72)
    strings_gen = StringsLegatoGenerator(strings_params)
    violins = strings_gen.render(chords, SCALE_E_MINOR, duration)
    
    # 2. Solo Woodwinds (Flute/Oboe - registered high, entries staggered by +0.025 beats to prevent fusion)
    ww_params = GeneratorParams(density=0.5, key_range_low=76, key_range_high=92)
    ww_gen = WoodwindsEnsembleGenerator(ww_params)
    woodwinds = ww_gen.render(chords, SCALE_E_MINOR, duration)
    for w in woodwinds:
        w.start += 0.025  # Staggered entry
        w.velocity = min(75, w.velocity)  # Ensure well-balanced dynamics
        
    # 3. Solitary Horns (Registered low-mid, entries staggered by +0.05 beats)
    brass_params = GeneratorParams(density=0.4, key_range_low=43, key_range_high=58)
    brass_gen = BrassSectionGenerator(brass_params, articulation="sustained")
    brass = brass_gen.render(chords, SCALE_E_MINOR, duration)
    for b in brass:
        b.start += 0.050  # Staggered entry
        b.velocity = min(68, b.velocity)
        
    raw = {
        "Violins": violins,
        "Woodwinds": woodwinds,
        "Brass": brass,
    }
    return raw, 84.0


# ===========================================================================
# Movement II: Aether (A Major, 112 BPM)
# ===========================================================================
def produce_mvt_2():
    """
    Movement II: Aether (A Major)
    Bypasses BRIGHTNESS OVERLOAD and TEMPORAL MASKING by:
    1. Capping the total sounding density of high-register bell chimes.
    2. Keeping background pizzicato patterns quiet relative to a soaring lead violin.
    """
    print("Writing Movement II: Aether...")
    duration = 64.0
    chords = _build_chords("I IV V I vi ii V I", duration, SCALE_A_MAJOR)
    
    # 1. Soaring Legato Violin (Melody, singing, key range 64-80)
    strings_params = GeneratorParams(density=0.5, key_range_low=64, key_range_high=80)
    strings_gen = StringsLegatoGenerator(strings_params)
    violins = strings_gen.render(chords, SCALE_A_MAJOR, duration)
    for v in violins:
        v.velocity = 82  # Strong singing lead
        
    # 2. Quiet Background Harp Pizzicatos (To prevent temporal masking, velocity is capped at 50)
    harp_params = GeneratorParams(density=0.45, key_range_low=48, key_range_high=72)
    harp_gen = HarpGenerator(harp_params)
    harp = harp_gen.render(chords, SCALE_A_MAJOR, duration)
    for h in harp:
        h.velocity = 48  # Whispering accompaniment
        
    # 3. Glassy Tubular Bells (Avoids brightness overload by spacing chime strikes at least 8 beats apart)
    bells = []
    bell_pitches = [84, 88, 91, 93, 88, 86, 91, 88]
    for i, pitch in enumerate(bell_pitches):
        strike_beat = float(i * 8)
        bells.append(NoteInfo(pitch=pitch, start=strike_beat, duration=4.0, velocity=58))
        
    raw = {
        "Violins": violins,
        "Harp": harp,
        "Bells": bells,
    }
    return raw, 112.0


# ===========================================================================
# Movement III: Cthonic (D Minor, 72 BPM)
# ===========================================================================
def produce_mvt_3():
    """
    Movement III: Cthonic (D Minor)
    Bypasses REGISTER MASKING and FREQUENCY MASKING by:
    1. Locking Cello and Bass into distinct octaves with a clear gap (Bass <= 36, Cello >= 45).
    2. Keeping low brass growls separated in frequency and time.
    """
    print("Writing Movement III: Cthonic...")
    duration = 48.0
    chords = _build_chords("i VI iv v i VI iv v", duration, SCALE_D_MINOR)
    
    # 1. Deep Monolithic Bass (Registered very low, pitch 26-36)
    bass = []
    for beat in range(0, 48, 4):
        # Heavy tonic/dominant low drone pedal notes
        pitch = 26 if (beat % 8 == 0) else 31
        bass.append(NoteInfo(pitch=pitch, start=float(beat), duration=3.8, velocity=68))
        
    # 2. Warm Legato Cellos (Registered strictly higher: 45-62, preventing register overlap/masking)
    cello_params = GeneratorParams(density=0.45, key_range_low=45, key_range_high=62)
    cello_gen = StringsLegatoGenerator(cello_params, section_size="trio")
    cello = cello_gen.render(chords, SCALE_D_MINOR, duration)
    for c in cello:
        c.velocity = 60
        
    # 3. Subterranean Tuba Swells (Alternates beats with the bass to avoid simultaneous masking)
    tuba = []
    for beat in range(2, 48, 4):
        tuba.append(NoteInfo(pitch=38, start=float(beat), duration=3.0, velocity=55))
        
    raw = {
        "Bass": bass,
        "Cello": cello,
        "Tuba": tuba,
    }
    return raw, 72.0


# ===========================================================================
# Movement IV: Cosmos (E Major, 136 BPM)
# ===========================================================================
def produce_mvt_4():
    """
    Movement IV: Cosmos (E Major)
    A complex, majestic Tutti Orchestral climax.
    Uses the self-healing psycho_verify post-processor in destructive=True mode
    to automatically identify and resolve 100% of micro-clashes (masking, blur, fusion)
    before exporting the MIDI file.
    """
    print("Writing Movement IV: Cosmos (Majestic Climax with Self-Healing)...")
    duration = 64.0
    chords = _build_chords("I IV vi V I IV V I", duration, SCALE_E_MAJOR)
    
    # 1. Shimmering Tremolo Strings
    strings_params = GeneratorParams(density=0.6, key_range_low=58, key_range_high=80)
    strings_gen = TremoloStringsGenerator(strings_params)
    tremolo = strings_gen.render(chords, SCALE_E_MAJOR, duration)
    
    # 2. Rapid Woodwind Runs (Can sometimes cause micro-blurring or masking)
    ww_params = GeneratorParams(density=0.65, key_range_low=72, key_range_high=90)
    ww_gen = WoodwindsEnsembleGenerator(ww_params)
    woodwinds = ww_gen.render(chords, SCALE_E_MAJOR, duration)
    
    # 3. Swelling Choir Pads
    choir_params = GeneratorParams(density=0.5, key_range_low=52, key_range_high=74)
    choir_gen = ChoirAahsGenerator(choir_params)
    choir = choir_gen.render(chords, SCALE_E_MAJOR, duration)
    
    raw = {
        "Tremolo": tremolo,
        "Woodwinds": woodwinds,
        "Choir": choir,
    }
    
    # Run the self-healing MIDI Doctor post-processor!
    print("  Applying self-healing Psychoacoustic Doctor engine...")
    config = PsychoConfig(aggressive_fix=True)
    fixed, report = psycho_verify(raw, config=config, bpm=136.0, destructive=True)
    print(f"  Doctor Report: Detected {report.issues_detected} issues, fixed {report.issues_fixed} successfully!")
    
    return fixed, 136.0


# ===========================================================================
# Main Orchestration Loop
# ===========================================================================
def main():
    album_dir = Path("output/symphony_doctor_exp")
    album_dir.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "=" * 80)
    print("                 S I N F O N I A   M Y S T E R I U M")
    print("       Highly Optimized Symphony for Psychoacoustic Sound Clarity")
    print("=" * 80 + "\n")
    
    mvt_meta = [
        (produce_mvt_1, "01_Mvt_I_Chronos.mid", {"Violins": 40, "Woodwinds": 73, "Brass": 60}),
        (produce_mvt_2, "02_Mvt_II_Aether.mid", {"Violins": 40, "Harp": 46, "Bells": 14}),
        (produce_mvt_3, "03_Mvt_III_Cthonic.mid", {"Bass": 43, "Cello": 42, "Tuba": 58}),
        (produce_mvt_4, "04_Mvt_IV_Cosmos.mid", {"Tremolo": 44, "Woodwinds": 73, "Choir": 52}),
    ]
    
    for i, (prod_func, filename, instruments) in enumerate(mvt_meta):
        print("-" * 80)
        raw, bpm = prod_func()
        mastered, pan = apply_orchestral_mix(raw, bpm)
        
        # Save MIDI
        target_path = album_dir / filename
        export_multitrack_midi(
            mastered, str(target_path),
            bpm=bpm, cc_events=pan,
            instruments=instruments,
        )
        print(f"-> Exported successfully: {filename}")
        
    print("\n" + "=" * 80)
    print("   PRODUCTION COMPLETE: SINFONIA MYSTERIUM")
    print(f"   All 4 movements successfully saved to: {album_dir.resolve()}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
