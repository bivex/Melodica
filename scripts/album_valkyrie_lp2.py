# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-22
# Last Updated: 2026-05-22
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
album_valkyrie_lp2.py — "VALKYRIE LP2".

A stunning 10-track cinematic jazz-noir and modern jazz album combining
Scandinavian mythology, jazz fusion, and dark ambient textures.
Scale & Key Settings: D minor -> F# minor -> Bb minor.
Tempos range from 58 BPM (rubato interlude) to 142 BPM (aggressive hard bop).
Dynamics span ppp to fff.
"""

import random
from pathlib import Path

from melodica import types
from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.modern_bass_2025 import ModernBass2025Generator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.composer.transformers import spiceup, serialize_canon, OneToThree
from melodica.harmonize.predictive import PredictiveHarmonizer
from melodica.rhythm.groove_template import SWING_60, LAID_BACK

# Keys Config
KEY_D_MINOR = Scale(root=2, mode=Mode.AEOLIAN)       # D minor (Aeolian)
KEY_D_DORIAN = Scale(root=2, mode=Mode.DORIAN)       # D Dorian
KEY_F_SHARP_DORIAN = Scale(root=6, mode=Mode.DORIAN) # F# Dorian
KEY_F_SHARP_PHRYGIAN = Scale(root=6, mode=Mode.PHRYGIAN) # F# Phrygian
KEY_F_SHARP_MINOR = Scale(root=6, mode=Mode.AEOLIAN) # F# minor (Aeolian)
KEY_B_FLAT_DORIAN = Scale(root=10, mode=Mode.DORIAN) # Bb Dorian
KEY_B_FLAT_MINOR = Scale(root=10, mode=Mode.AEOLIAN)  # Bb minor (Aeolian)


def _build_chords(progression: str, duration: float, key: Scale) -> list[ChordLabel]:
    """Parse Roman numeral progression into ChordLabels."""
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
# SIDE A — "Ascent" (Восхождение)
# ---------------------------------------------------------------------------

# 01. Iron Wings (Intro)
def produce_track_1():
    """Cold awakening. Single Rhodes pedal line, low Upright E pedal, brushed snare."""
    print("Producing 01. Iron Wings (Intro / Cold D minor Awakening)...")
    duration = 64.0
    # i - v - i - v progression (long pedal drone)
    chords = _build_chords("i v i v" * 2, duration, KEY_D_MINOR)

    # Slow cold Rhodes melody
    solo_params = GeneratorParams(density=0.25, key_range_low=55, key_range_high=74)
    solo_gen = SoloMelodyGenerator(solo_params, style="modal_ambient", vibrato_depth=0.5)
    raw_melody = solo_gen.render(chords, KEY_D_MINOR, duration)
    # Long pedal holds: make notes longer
    for n in raw_melody:
        n.duration *= 1.8
        n.velocity = 50  # piano dynamics

    # Upright Bass holding E pedal
    bass = [
        NoteInfo(pitch=16, start=i * 8.0, duration=7.5, velocity=45)
        for i in range(int(duration / 8.0))
    ]

    # Soft brushed snare
    drums = [
        NoteInfo(pitch=38, start=i * 2.0 + 1.0, duration=0.2, velocity=35)
        for i in range(int(duration / 2.0))
    ]

    return {"piano": raw_melody, "bass": bass, "drums": drums}, 60.0


# 02. Chooser of the Slain
def produce_track_2():
    """Aggressive Coltrane-style Tenor Sax + Broken Funk Slap Bass."""
    print("Producing 02. Chooser of the Slain (Coltrane Sax + Slap Broken Funk)...")
    duration = 112.0
    # i - iv - VII - i in D Dorian modulating to Phrygian at bridge (VII becomes bII)
    progression = "i iv VII i " * 5 + "bII bII i i " * 2
    chords = _build_chords(progression, duration, KEY_D_DORIAN)

    # Tenor Sax virtuoso solo
    solo_params = GeneratorParams(density=0.6, key_range_low=50, key_range_high=78)
    solo_gen = SoloMelodyGenerator(solo_params, style="jazz_fusion", vibrato_depth=0.75)
    raw_sax = solo_gen.render(chords, KEY_D_DORIAN, duration)
    # Coltrane style peaks
    for n in raw_sax:
        if n.velocity > 80:
            n.velocity = 110

    # Comping Rhodes chords
    rhodes = [
        NoteInfo(pitch=p, start=c.start + 0.5, duration=1.5, velocity=75)
        for c in chords
        for p in [c.root + 48, c.root + 52, c.root + 55]
    ]

    # Modern 2025 Slap Bass (D Dorian, broken funk)
    bass_params = GeneratorParams(density=0.72, key_range_low=32, key_range_high=52)
    bass_gen = ModernBass2025Generator(bass_params, style="slap")
    bass = bass_gen.render(chords, KEY_D_DORIAN, duration)

    return {"lead": raw_sax, "piano": rhodes, "bass": bass}, 115.0


# 03. Mist & Armor
def produce_track_3():
    """Lyrical swing Flugelhorn, Vibraphone echo, Acoustic bass walking."""
    print("Producing 03. Mist & Armor (Flugelhorn Swing / Vibraphone echo)...")
    duration = 96.0
    # i - ii - V - i in F# Dorian
    progression = "i ii V i " * 6
    chords = _build_chords(progression, duration, KEY_F_SHARP_DORIAN)

    # Soft singing flugelhorn
    solo_params = GeneratorParams(density=0.36, key_range_low=52, key_range_high=74)
    solo_gen = SoloMelodyGenerator(solo_params, style="vocal_mimic", vibrato_depth=0.8)
    raw_flugel = solo_gen.render(chords, KEY_F_SHARP_DORIAN, duration)

    # Vibraphone answering stabs
    vibes = []
    for i, c in enumerate(chords):
        if i % 2 == 1:
            vibes.extend([
                NoteInfo(pitch=c.root + 60, start=c.start + 2.0, duration=2.0, velocity=55),
                NoteInfo(pitch=c.root + 64, start=c.start + 2.0, duration=2.0, velocity=55),
            ])

    # Dynamic walking bass (Pocket lock: Avg 68, Max 88)
    bass_params = GeneratorParams(density=0.55, key_range_low=28, key_range_high=48)
    bass_gen = ModernBass2025Generator(bass_params, style="walking")
    bass = bass_gen.render(chords, KEY_F_SHARP_DORIAN, duration)

    return {"lead": raw_flugel, "pad": vibes, "bass": bass}, 76.0


# 04. Raven Protocol
def produce_track_4():
    """Alto & Soprano Sax counterpoint, Prepared Piano, Sliding Fretless Bass."""
    print("Producing 04. Raven Protocol (Alto + Soprano counterpoint / Fretless Bass)...")
    duration = 120.0
    progression = "i i iv iv bII bII i i " * 3
    chords = _build_chords(progression, duration, KEY_F_SHARP_PHRYGIAN)

    # Alto Sax Lead
    alto_params = GeneratorParams(density=0.45, key_range_low=52, key_range_high=76)
    alto_gen = SoloMelodyGenerator(alto_params, style="jazz_fusion", vibrato_depth=0.7)
    raw_alto = alto_gen.render(chords, KEY_F_SHARP_PHRYGIAN, duration)

    # Soprano Sax delayed Canon
    canon_lead = serialize_canon(
        voices=[raw_alto, raw_alto],
        delay_beats=8.0,
        transpositions=[0, 12],
        duration_beats=duration,
    )

    # Prepared piano staccato metal clangs
    p_piano = [
        NoteInfo(pitch=c.root + 36 + (i % 3) * 7, start=c.start + i * 1.5, duration=0.2, velocity=68)
        for c in chords
        for i in range(3)
    ]

    # Modern 2025 Fretless Bass (Self modifying sliding register)
    bass_params = GeneratorParams(density=0.58, key_range_low=26, key_range_high=46)
    bass_gen = ModernBass2025Generator(bass_params, style="self_modifying")
    bass = bass_gen.render(chords, KEY_F_SHARP_PHRYGIAN, duration)

    # Electronics granular texture pad
    pad = [
        NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration * 1.05, velocity=36)
        for c in chords
    ]

    return {"lead": raw_alto, "canon_lead": canon_lead, "piano": p_piano, "bass": bass, "pad": pad}, 98.0


# 05. The Battlefield (Interlude)
def produce_track_5():
    """Solo Upright Bass медленная импровизация, отдаленный Moog дрон."""
    print("Producing 05. The Battlefield (Solo Bass Improv + Moog Drone)...")
    duration = 48.0
    chords = _build_chords("i i iv iv v v i i", duration, KEY_F_SHARP_MINOR)

    # Solo Upright Bass improvisation (Adaptive style)
    bass_params = GeneratorParams(density=0.5, key_range_low=32, key_range_high=55)
    bass_gen = ModernBass2025Generator(bass_params, style="adaptive")
    bass = bass_gen.render(chords, KEY_F_SHARP_MINOR, duration)
    for n in bass:
        n.duration *= 1.3  # Rubato holds
        n.velocity = random.randint(40, 68)  # very dynamic, quiet ppp

    # Distant Moog Drone
    moog = [
        NoteInfo(pitch=c.root + 24, start=c.start, duration=c.duration * 1.1, velocity=30)
        for c in chords
    ]

    return {"bass": bass, "pad": moog}, 58.0


# ---------------------------------------------------------------------------
# SIDE B — "Descent" (Нисхождение)
# ---------------------------------------------------------------------------

# 06. Valhalla Calling
def produce_track_6():
    """Standard jazz trio + Harmon-muted trumpet entering at 2:30 + string quartet at 4:00."""
    print("Producing 06. Valhalla Calling (Jazz Trio + Harmon Mute + Cinematic Strings)...")
    duration = 144.0
    # i - iv - VII - III - VI - ii - V - i (grand circle of fifths)
    progression = "i iv VII III VI ii V i " * 3
    chords = _build_chords(progression, duration, KEY_B_FLAT_DORIAN)

    # Piano trio: Piano theme
    piano_params = GeneratorParams(density=0.38, key_range_low=48, key_range_high=72)
    piano_gen = SoloMelodyGenerator(piano_params, style="neo_soul_keys", vibrato_depth=0.6)
    piano_melody = piano_gen.render(chords, KEY_B_FLAT_DORIAN, duration)

    # Walking bass
    bass_params = GeneratorParams(density=0.55, key_range_low=28, key_range_high=48)
    bass_gen = ModernBass2025Generator(bass_params, style="walking")
    bass = bass_gen.render(chords, KEY_B_FLAT_DORIAN, duration)

    # Harmon-muted Trumpet enters from afar (beat 48 onwards)
    trumpet = []
    trumpet_params = GeneratorParams(density=0.48, key_range_low=58, key_range_high=78)
    trumpet_gen = SoloMelodyGenerator(trumpet_params, style="bebop_horn", vibrato_depth=0.8)
    raw_trumpet = trumpet_gen.render(chords, KEY_B_FLAT_DORIAN, duration)
    for n in raw_trumpet:
        if n.start >= 48.0:
            n.velocity = int(n.velocity * 0.85)  # muted feel
            trumpet.append(n)

    # String Quartet transforms it into cinematic at beat 80 onwards
    strings = []
    for c in chords:
        if c.start >= 80.0:
            strings.extend([
                NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration * 1.1, velocity=48),
                NoteInfo(pitch=c.root + 52, start=c.start, duration=c.duration * 1.1, velocity=48),
                NoteInfo(pitch=c.root + 55, start=c.start, duration=c.duration * 1.1, velocity=48),
            ])

    return {"piano": piano_melody, "bass": bass, "lead": trumpet, "pad": strings}, 88.0


# 07. Winged Fury
def produce_track_7():
    """Baritone Sax, Hammond B3, Hard Bop high-energy drums."""
    print("Producing 07. Winged Fury (Baritone Sax + Hammond B3 Organ Max Energy)...")
    duration = 120.0
    progression = "i i iv iv v v i i " * 3
    chords = _build_chords(progression, duration, KEY_B_FLAT_MINOR)

    # Low, heavy Baritone Sax solo
    solo_params = GeneratorParams(density=0.68, key_range_low=36, key_range_high=64)
    solo_gen = SoloMelodyGenerator(solo_params, style="shred_guitar", vibrato_depth=0.8)
    raw_bari = solo_gen.render(chords, KEY_B_FLAT_MINOR, duration)
    # Pitch shift down to emulate Baritone saxophone register
    for n in raw_bari:
        n.pitch -= 12
        n.velocity = min(120, n.velocity + 15)  # aggressive fff

    # Hammond B3 Organ dirty backing stabs
    organ = []
    for c in chords:
        for offset in [0.0, 1.0, 2.0, 3.0]:
            organ.extend([
                NoteInfo(pitch=c.root + 48, start=c.start + offset, duration=0.8, velocity=88),
                NoteInfo(pitch=c.root + 52, start=c.start + offset, duration=0.8, velocity=88),
            ])

    # Aggressive heavy saw bass
    bass_params = GeneratorParams(density=0.75, key_range_low=24, key_range_high=44)
    bass_gen = ModernBass2025Generator(bass_params, style="saw")
    bass = bass_gen.render(chords, KEY_B_FLAT_MINOR, duration)

    return {"lead": raw_bari, "piano": organ, "bass": bass}, 142.0


# 08. Between Worlds
def produce_track_8():
    """Lyrical Tenor Sax, Marimba woody comp, Arco bowed bass, mallets."""
    print("Producing 08. Between Worlds (Tenor Sax + Marimba + Arco Bass)...")
    duration = 112.0
    progression = "i i iv iv VI VI i i " * 2
    chords = _build_chords(progression, duration, KEY_B_FLAT_MINOR)

    # Lyrical Tenor Sax
    solo_params = GeneratorParams(density=0.35, key_range_low=52, key_range_high=74)
    solo_gen = SoloMelodyGenerator(solo_params, style="modal_ambient", vibrato_depth=0.7)
    raw_sax = solo_gen.render(chords, KEY_B_FLAT_MINOR, duration)

    # Marimba woody stabs
    marimba = [
        NoteInfo(pitch=c.root + 48 + (i % 2) * 4, start=c.start + i * 2.0, duration=0.4, velocity=58)
        for c in chords
        for i in range(2)
    ]

    # Arco bowed bass (represented by cinematic low sustain strings)
    arco_bass = [
        NoteInfo(pitch=c.root + 36, start=c.start, duration=c.duration * 1.05, velocity=48)
        for c in chords
    ]

    return {"lead": raw_sax, "piano": marimba, "bass": arco_bass}, 70.0


# 09. Norns' Thread
def produce_track_9():
    """Solo Piano with complex extensions, Upright bass entering late, soft snare."""
    print("Producing 09. Norns' Thread (Solo Piano fate chords + Late Bass)...")
    duration = 96.0
    progression = "i iv VII III VI ii V i " * 2
    chords = _build_chords(progression, duration, KEY_D_MINOR)

    # Complex extended chord piano stabs (9ths, 11ths, 13ths)
    piano_solo = []
    for c in chords:
        # voiced complex chords
        piano_solo.extend([
            NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration * 0.95, velocity=58),
            NoteInfo(pitch=c.root + 52, start=c.start + 0.25, duration=c.duration * 0.95, velocity=62),
            NoteInfo(pitch=c.root + 55, start=c.start + 0.5, duration=c.duration * 0.9, velocity=65),
            NoteInfo(pitch=c.root + 59, start=c.start + 0.75, duration=c.duration * 0.85, velocity=68),
        ])

    # Upright bass entering late (after beat 32.0)
    bass = []
    bass_params = GeneratorParams(density=0.45, key_range_low=28, key_range_high=48)
    bass_gen = ModernBass2025Generator(bass_params, style="walking")
    raw_bass = bass_gen.render(chords, KEY_D_MINOR, duration)
    for n in raw_bass:
        if n.start >= 32.0:
            n.velocity = int(n.velocity * 0.8)
            bass.append(n)

    # Brushed snare entering at very tail (after beat 80.0)
    drums = []
    for i in range(int(duration)):
        if i >= 80:
            drums.append(NoteInfo(pitch=38, start=i + 0.5, duration=0.1, velocity=25))

    return {"piano": piano_solo, "bass": bass, "drums": drums}, 65.0


# 10. Valkyrie's Return (Outro)
def produce_track_10():
    """Full ensemble homecoming, Rhodes, Upright, Drums, Flugelhorn, Strings. Rhodes fade."""
    print("Producing 10. Valkyrie's Return (Outro / Full Ensemble Homecoming)...")
    duration = 96.0
    progression = "i v i v " * 6
    chords = _build_chords(progression, duration, KEY_D_MINOR)

    # Flugelhorn leading the epic homecoming theme
    solo_params = GeneratorParams(density=0.38, key_range_low=55, key_range_high=76)
    solo_gen = SoloMelodyGenerator(solo_params, style="cinematic_strings", vibrato_depth=0.9)
    raw_flugel = solo_gen.render(chords, KEY_D_MINOR, duration)

    # Rhodes keyboard (fades out solo in the final 20 beats)
    rhodes = []
    for c in chords:
        vel = 75 if c.start < 76.0 else int(75 * (96.0 - c.start) / 20.0)
        rhodes.extend([
            NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration * 0.95, velocity=vel),
            NoteInfo(pitch=c.root + 52, start=c.start + 0.5, duration=c.duration * 0.95, velocity=vel),
        ])

    # Upright bass
    bass_params = GeneratorParams(density=0.5, key_range_low=28, key_range_high=48)
    bass_gen = ModernBass2025Generator(bass_params, style="fingerstyle")
    bass = bass_gen.render(chords, KEY_D_MINOR, duration)
    # Stop bass early for Rhodes fadeout
    bass = [n for n in bass if n.start < 76.0]

    # String Quartet
    strings = []
    for c in chords:
        if c.start < 76.0:
            strings.extend([
                NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration, velocity=48),
                NoteInfo(pitch=c.root + 55, start=c.start, duration=c.duration, velocity=48),
            ])

    # Brushed Drums
    drums = [
        NoteInfo(pitch=38, start=i * 2.0, duration=0.2, velocity=38)
        for i in range(int(76.0 / 2.0))
    ]

    return {"lead": raw_flugel, "piano": rhodes, "bass": bass, "pad": strings, "drums": drums}, 62.0


# ---------------------------------------------------------------------------
# Post-production
# ---------------------------------------------------------------------------

def apply_post_production(raw_tracks, bpm, lufs=-14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.88,
        "lead": 0.92,
        "canon_lead": 0.88,
        "bass": 1.12,  # Warm acoustic/upright presence
        "pad": 0.44,
        "drums": 0.70,
    })

    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan_events = master.apply_mastering(mixed)
    return mastered, pan_events


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    album_dir = Path("output/album_valkyrie_lp2")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   VALKYRIE LP2 — Cinematic Jazz-Noir Masterpiece")
    print("   Scandinavian Mythology x Modern Jazz")
    print("=" * 60 + "\n")

    # 01. Iron Wings
    t1_raw, t1_bpm = produce_track_1()
    t1_m, t1_pan = apply_post_production(t1_raw, t1_bpm, lufs=-18.0) # ppp
    export_multitrack_midi(
        t1_m, str(album_dir / "01_Iron_Wings.mid"),
        bpm=t1_bpm, cc_events=t1_pan,
        instruments={"piano": 5, "bass": 33, "drums": 117},
    )

    # 02. Chooser of the Slain
    t2_raw, t2_bpm = produce_track_2()
    t2_m, t2_pan = apply_post_production(t2_raw, t2_bpm, lufs=-12.0) # fff
    export_multitrack_midi(
        t2_m, str(album_dir / "02_Chooser_of_the_Slain.mid"),
        bpm=t2_bpm, cc_events=t2_pan,
        instruments={"lead": 67, "piano": 5, "bass": 37},
    )

    # 03. Mist & Armor
    t3_raw, t3_bpm = produce_track_3()
    t3_m, t3_pan = apply_post_production(t3_raw, t3_bpm, lufs=-15.0)
    export_multitrack_midi(
        t3_m, str(album_dir / "03_Mist_&_Armor.mid"),
        bpm=t3_bpm, cc_events=t3_pan,
        instruments={"lead": 57, "pad": 12, "bass": 33},
    )

    # 04. Raven Protocol
    t4_raw, t4_bpm = produce_track_4()
    t4_m, t4_pan = apply_post_production(t4_raw, t4_bpm, lufs=-14.0)
    export_multitrack_midi(
        t4_m, str(album_dir / "04_Raven_Protocol.mid"),
        bpm=t4_bpm, cc_events=t4_pan,
        instruments={"lead": 66, "canon_lead": 65, "piano": 1, "bass": 36, "pad": 91},
    )

    # 05. The Battlefield
    t5_raw, t5_bpm = produce_track_5()
    t5_m, t5_pan = apply_post_production(t5_raw, t5_bpm, lufs=-19.0) # ppp
    export_multitrack_midi(
        t5_m, str(album_dir / "05_The_Battlefield.mid"),
        bpm=t5_bpm, cc_events=t5_pan,
        instruments={"bass": 33, "pad": 81},
    )

    # 06. Valhalla Calling
    t6_raw, t6_bpm = produce_track_6()
    t6_m, t6_pan = apply_post_production(t6_raw, t6_bpm, lufs=-14.0)
    export_multitrack_midi(
        t6_m, str(album_dir / "06_Valhalla_Calling.mid"),
        bpm=t6_bpm, cc_events=t6_pan,
        instruments={"piano": 1, "bass": 33, "lead": 60, "pad": 49},
    )

    # 07. Winged Fury
    t7_raw, t7_bpm = produce_track_7()
    t7_m, t7_pan = apply_post_production(t7_raw, t7_bpm, lufs=-11.0) # fff organized hammer
    export_multitrack_midi(
        t7_m, str(album_dir / "07_Winged_Fury.mid"),
        bpm=t7_bpm, cc_events=t7_pan,
        instruments={"lead": 68, "piano": 17, "bass": 39},
    )

    # 08. Between Worlds
    t8_raw, t8_bpm = produce_track_8()
    t8_m, t8_pan = apply_post_production(t8_raw, t8_bpm, lufs=-15.0)
    export_multitrack_midi(
        t8_m, str(album_dir / "08_Between_Worlds.mid"),
        bpm=t8_bpm, cc_events=t8_pan,
        instruments={"lead": 67, "piano": 13, "bass": 41},
    )

    # 09. Norns' Thread
    t9_raw, t9_bpm = produce_track_9()
    t9_m, t9_pan = apply_post_production(t9_raw, t9_bpm, lufs=-16.0)
    export_multitrack_midi(
        t9_m, str(album_dir / "09_Norns'_Thread.mid"),
        bpm=t9_bpm, cc_events=t9_pan,
        instruments={"piano": 1, "bass": 33, "drums": 117},
    )

    # 10. Valkyrie's Return
    t10_raw, t10_bpm = produce_track_10()
    t10_m, t10_pan = apply_post_production(t10_raw, t10_bpm, lufs=-14.0)
    export_multitrack_midi(
        t10_m, str(album_dir / "10_Valkyrie's_Return.mid"),
        bpm=t10_bpm, cc_events=t10_pan,
        instruments={"lead": 57, "piano": 5, "bass": 33, "pad": 49, "drums": 117},
    )

    print("\n" + "=" * 60)
    print("   PRODUCTION COMPLETE: VALKYRIE LP2")
    print(f"   MIDI output saved under: {album_dir.resolve()}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
