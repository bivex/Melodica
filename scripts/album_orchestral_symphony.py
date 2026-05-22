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
album_orchestral_symphony.py — "Symphony No. 1 in G Minor (The Mechanical Awakening)".

A monumental 4-movement symphonic masterpiece showcasing our premium continuous expression engines, 
physical-model articulation curves, and the 5 new orchestration components.

Movements:
  I.   Allegro con brio (G Minor, Aeolian)     — Energetic sonata form featuring legato string lines,
                                                 majestic brass swells, and walking Tuba basses.
  II.  Adagio cantabile (Eb Major, Lydian)     — Slow, emotional lyrical movement with expressive legato strings,
                                                 breathing woodwinds ensemble dialogue, and choral vowel formants.
  III. Scherzo: Presto (G Minor, Aeolian)      — Fast, playful scherzo driven by Bartók snaps, pizzicato chords,
                                                 and sharp snare drum rolls/march grooves.
  IV.  Finale: Allegro maestoso (G Major, Ionian)— Triumphant epic climax blending BRAAM orchestral hits, tremolo builds,
                                                 heroic brass fanfares, tubular bells chime motifs, and cymbal crescendos.
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
from melodica.generators.choir_ahhs import ChoirAhhsGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator
from melodica.generators.tuba import TubaGenerator
from melodica.generators.snare_drum import SnareDrumGenerator
from melodica.generators.orchestral_cymbal import OrchestralCymbalGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.composer.transformers import spiceup

# Scales Setup
KEY_G_MINOR = Scale(root=7, mode=Mode.AEOLIAN)       # G Minor (Aeolian)
KEY_EB_MAJOR = Scale(root=3, mode=Mode.LYDIAN)      # Eb Major (Lydian)
KEY_G_MAJOR = Scale(root=7, mode=Mode.IONIAN)        # G Major (Ionian)


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


# ---------------------------------------------------------------------------
# Movement I: Allegro con brio
# ---------------------------------------------------------------------------

def produce_movement_1():
    """Movement I: Allegro con brio (G Minor, Aeolian) at 120 BPM. Legato Strings + Brass swells + Walking Tuba."""
    print("Writing Movement I: Allegro con brio (Sonata-Allegro / Legato Strings & Brass Swells)...")
    
    duration = 64.0
    progression = "i iv V i VI iv V i" * 2
    chords = _build_chords(progression, duration, KEY_G_MINOR)
    
    # 1. Soaring Legato Violin melody (Portamento CC pitch bends)
    strings_params = GeneratorParams(density=0.6, key_range_low=60, key_range_high=82)
    strings_gen = StringsLegatoGenerator(strings_params, section_size="ensemble", portamento_speed=0.15)
    strings = strings_gen.render(chords, KEY_G_MINOR, duration)
    
    # 2. Majestic Brass backing chord pads with smooth CC11 swells
    brass_params = GeneratorParams(density=0.4, key_range_low=48, key_range_high=72)
    brass_gen = BrassSectionGenerator(brass_params, articulation="sustained", voicing="open", intensity=0.75)
    brass = brass_gen.render(chords, KEY_G_MINOR, duration)
    
    # 3. Mighty walking low Tuba bass line
    tuba_params = GeneratorParams(density=0.5, key_range_low=29, key_range_high=45)
    tuba_gen = TubaGenerator(tuba_params, articulation="walking", growl=False)
    tuba = tuba_gen.render(chords, KEY_G_MINOR, duration)
    
    # 4. Crisp marching snare grooves (flams and rolls)
    snare_params = GeneratorParams(density=0.5)
    snare_gen = SnareDrumGenerator(snare_params, pattern_type="march")
    snare = snare_gen.render(chords, KEY_G_MINOR, duration)
    
    # 5. Dramatic Orchestral Crash hits at the beginning of phrases
    cymbal_params = GeneratorParams(density=0.15)
    cymbal_gen = OrchestralCymbalGenerator(cymbal_params, pattern_type="crash")
    cymbal = cymbal_gen.render(chords, KEY_G_MINOR, duration)
    
    # 6. Periodic decorative bell chimes
    bells_params = GeneratorParams(density=0.25, key_range_low=54, key_range_high=75)
    bells_gen = TubularBellsGenerator(bells_params, stroke_pattern="motif", dampen=True)
    bells = bells_gen.render(chords, KEY_G_MINOR, duration)
    
    raw_tracks = {
        "Violins": strings,
        "Brass": brass,
        "Tuba": tuba,
        "Snare": snare,
        "Cymbal": cymbal,
        "Bells": bells,
    }
    return raw_tracks, 120.0


# ---------------------------------------------------------------------------
# Movement II: Adagio cantabile
# ---------------------------------------------------------------------------

def produce_movement_2():
    """Movement II: Adagio cantabile (Eb Major, Lydian) at 72 BPM. Legato Strings + Woodwinds dialogue + Choral vowel formants."""
    print("Writing Movement II: Adagio cantabile (Lyrical Cantabile / Woodwinds & Choral Vowels)...")
    
    duration = 48.0
    progression = "I V vi IV I IV V I"
    chords = _build_chords(progression, duration, KEY_EB_MAJOR)
    
    # 1. Tender, warm Legato Strings
    strings_params = GeneratorParams(density=0.45, key_range_low=58, key_range_high=78)
    strings_gen = StringsLegatoGenerator(strings_params, section_size="chamber", portamento_speed=0.25)
    strings = strings_gen.render(chords, KEY_EB_MAJOR, duration)
    
    # 2. Lyrical woodwinds ensemble (breathing gaps, oboe/flute sweet spots)
    woodwind_params = GeneratorParams(density=0.5, key_range_low=60, key_range_high=84)
    woodwind_gen = WoodwindsEnsembleGenerator(woodwind_params, section="quartet", articulation="legato", breath_interval=5.0)
    woodwinds = woodwind_gen.render(chords, KEY_EB_MAJOR, duration)
    
    # 3. Dynamic background Choir Aahs with formant vowel CC 74 changes
    choir_params = GeneratorParams(density=0.35, key_range_low=48, key_range_high=72)
    choir_gen = ChoirAhhsGenerator(choir_params, voice_count=4, dynamics="p", syllable="aah")
    choir = choir_gen.render(chords, KEY_EB_MAJOR, duration)
    
    # 4. Long tubular bell chimes ring-outs marking key cadential changes
    bells_params = GeneratorParams(density=0.15, key_range_low=53, key_range_high=77)
    bells_gen = TubularBellsGenerator(bells_params, stroke_pattern="single", dampen=False)
    bells = bells_gen.render(chords, KEY_EB_MAJOR, duration)
    
    raw_tracks = {
        "Violins": strings,
        "Woodwinds": woodwinds,
        "Choir": choir,
        "Bells": bells,
    }
    return raw_tracks, 72.0


# ---------------------------------------------------------------------------
# Movement III: Scherzo: Presto
# ---------------------------------------------------------------------------

def produce_movement_3():
    """Movement III: Scherzo: Presto (G Minor, Aeolian) at 144 BPM. Bartók snaps + Pizzicato runs + snare crescendos."""
    print("Writing Movement III: Scherzo: Presto (Fast Playful / Pizzicato Snaps & Snare Rolls)...")
    
    duration = 96.0
    progression = "i VI iv VII III VI iv V" * 3
    chords = _build_chords(progression, duration, KEY_G_MINOR)
    
    # 1. Playful Pizzicato Strings with arco/pizz mix and violent Bartók snap accents
    pizz_params = GeneratorParams(density=0.65, key_range_low=50, key_range_high=80)
    pizz_gen = StringsPizzicatoGenerator(pizz_params, arco_mix=0.3, snap_pizzicato=True)
    pizz = pizz_gen.render(chords, KEY_G_MINOR, duration)
    
    # 2. Staccato Woodwinds responding in counterpoint dialogue
    woodwind_params = GeneratorParams(density=0.6, key_range_low=62, key_range_high=86)
    woodwind_gen = WoodwindsEnsembleGenerator(woodwind_params, section="trio", articulation="staccato")
    woodwinds = woodwind_gen.render(chords, KEY_G_MINOR, duration)
    
    # 3. Dynamic Tuba staccato stepping bass
    tuba_params = GeneratorParams(density=0.6, key_range_low=29, key_range_high=45)
    tuba_gen = TubaGenerator(tuba_params, articulation="staccato", growl=False)
    tuba = tuba_gen.render(chords, KEY_G_MINOR, duration)
    
    # 4. Rapid snare crescendos (alternate hand roll techniques)
    snare_params = GeneratorParams(density=0.7)
    snare_gen = SnareDrumGenerator(snare_params, pattern_type="roll")
    snare = snare_gen.render(chords, KEY_G_MINOR, duration)
    
    raw_tracks = {
        "Pizzicato": pizz,
        "Woodwinds": woodwinds,
        "Tuba": tuba,
        "Snare": snare,
    }
    return raw_tracks, 144.0


# ---------------------------------------------------------------------------
# Movement IV: Finale: Allegro maestoso
# ---------------------------------------------------------------------------

def produce_movement_4():
    """Movement IV: Finale: Allegro maestoso (G Major, Ionian) at 128 BPM. BRAAM hits + Tremolo tension + Heroic fanfares."""
    print("Writing Movement IV: Finale: Allegro maestoso (Triumphant Grand Climax / BRAAM Hits & Chime Motifs)...")
    
    duration = 64.0
    progression = "I IV V I vi ii V I" * 2
    chords = _build_chords(progression, duration, KEY_G_MAJOR)
    
    # 1. Opening epic Orchestral Hits / low BRAAM growls and pitch falls
    hit_params = GeneratorParams(density=0.4, key_range_low=32, key_range_high=64)
    hit_gen = OrchestralHitGenerator(hit_params, hit_type="riser", voicing="ensemble", duration=1.5, reverb_tail=4.0)
    hits = hit_gen.render(chords, KEY_G_MAJOR, duration)
    
    # 2. Intense high Tremolo Strings building massive polyphonic dynamic layers
    tremolo_params = GeneratorParams(density=0.7, key_range_low=60, key_range_high=84)
    tremolo_gen = TremoloStringsGenerator(tremolo_params, variant="chord", bow_speed=0.08, dynamic_swell=True)
    tremolo = tremolo_gen.render(chords, KEY_G_MAJOR, duration)
    
    # 3. Heroic Brass Section fanfares with swelling CC11 dynamics
    brass_params = GeneratorParams(density=0.55, key_range_low=52, key_range_high=76)
    brass_gen = BrassSectionGenerator(brass_params, articulation="fanfare", voicing="open", intensity=0.9)
    brass = brass_gen.render(chords, KEY_G_MAJOR, duration)
    
    # 4. Growling low Tuba backing foundation (8Hz LFO growls on CC74)
    tuba_params = GeneratorParams(density=0.5, key_range_low=29, key_range_high=45)
    tuba_gen = TubaGenerator(tuba_params, articulation="swell", growl=True)
    tuba = tuba_gen.render(chords, KEY_G_MAJOR, duration)
    
    # 5. Accent Snare rimshots and rolls
    snare_params = GeneratorParams(density=0.6)
    snare_gen = SnareDrumGenerator(snare_params, pattern_type="rimshot")
    snare = snare_gen.render(chords, KEY_G_MAJOR, duration)
    
    # 6. High-sizzle Orchestral Cymbal rolls and washes
    cymbal_params = GeneratorParams(density=0.4)
    cymbal_gen = OrchestralCymbalGenerator(cymbal_params, pattern_type="roll")
    cymbal = cymbal_gen.render(chords, KEY_G_MAJOR, duration)
    
    # 7. Resonant tubular bell chime melodies
    bells_params = GeneratorParams(density=0.35, key_range_low=54, key_range_high=78)
    bells_gen = TubularBellsGenerator(bells_params, stroke_pattern="motif", dampen=False)
    bells = bells_gen.render(chords, KEY_G_MAJOR, duration)
    
    raw_tracks = {
        "Hits": hits,
        "Tremolo": tremolo,
        "Brass": brass,
        "Tuba": tuba,
        "Snare": snare,
        "Cymbal": cymbal,
        "Bells": bells,
    }
    return raw_tracks, 128.0


# ---------------------------------------------------------------------------
# Post-production, Mixing and Mastering
# ---------------------------------------------------------------------------

def apply_orchestral_mix(raw_tracks, bpm, lufs=-14.0):
    """Mix and master the raw tracks using the MixingDesk and MasteringDesk."""
    desk = MixingDesk(niche_cfg={})
    
    # Explicit gain staging for massive premium orchestral balance
    desk.track_gains.update({
        "Violins": 0.85,
        "Pizzicato": 0.90,
        "Tremolo": 0.82,
        "Brass": 0.88,
        "Woodwinds": 0.86,
        "Choir": 0.80,
        "Hits": 0.98,
        "Tuba": 1.15,      # Deep low-end warmth
        "Snare": 0.90,
        "Cymbal": 0.85,
        "Bells": 0.92,
    })
    
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan_events = master.apply_mastering(mixed)
    return mastered, pan_events


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

def main():
    album_dir = Path("output/album_orchestral_symphony")
    album_dir.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "=" * 80)
    print("   SYMPHONY NO. 1 IN G MINOR — 4-Movement Masterpiece Album")
    print("   Showcasing Physical-Model Generative Articulations & Custom Instruments")
    print("=" * 80 + "\n")
    
    # Movement I
    t1_raw, t1_bpm = produce_movement_1()
    t1_m, t1_pan = apply_orchestral_mix(t1_raw, t1_bpm, lufs=-13.0)
    export_multitrack_midi(
        t1_m, str(album_dir / "01_Mvt_I_Allegro_con_brio.mid"),
        bpm=t1_bpm, cc_events=t1_pan,
        instruments={"Violins": 40, "Brass": 61, "Tuba": 58, "Snare": 115, "Cymbal": 115, "Bells": 14},
    )
    
    # Movement II
    t2_raw, t2_bpm = produce_movement_2()
    t2_m, t2_pan = apply_orchestral_mix(t2_raw, t2_bpm, lufs=-15.0)
    export_multitrack_midi(
        t2_m, str(album_dir / "02_Mvt_II_Adagio_cantabile.mid"),
        bpm=t2_bpm, cc_events=t2_pan,
        instruments={"Violins": 40, "Woodwinds": 73, "Choir": 52, "Bells": 14},
    )
    
    # Movement III
    t3_raw, t3_bpm = produce_movement_3()
    t3_m, t3_pan = apply_orchestral_mix(t3_raw, t3_bpm, lufs=-14.0)
    export_multitrack_midi(
        t3_m, str(album_dir / "03_Mvt_III_Scherzo_Presto.mid"),
        bpm=t3_bpm, cc_events=t3_pan,
        instruments={"Pizzicato": 45, "Woodwinds": 73, "Tuba": 58, "Snare": 115},
    )
    
    # Movement IV
    t4_raw, t4_bpm = produce_movement_4()
    t4_m, t4_pan = apply_orchestral_mix(t4_raw, t4_bpm, lufs=-12.0)
    export_multitrack_midi(
        t4_m, str(album_dir / "04_Mvt_IV_Finale_Allegro_maestoso.mid"),
        bpm=t4_bpm, cc_events=t4_pan,
        instruments={"Hits": 55, "Tremolo": 44, "Brass": 61, "Tuba": 58, "Snare": 115, "Cymbal": 115, "Bells": 14},
    )
    
    print("\n" + "=" * 80)
    print("   PRODUCTION COMPLETE: SYMPHONY NO. 1 (THE MECHANICAL AWAKENING)")
    print(f"   MIDI output saved under: {album_dir.resolve()}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
