# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_dracula_ch3.py — ДРАКУЛА: Глава III (Dracula: Chapter III - Gothic Album in Hungarian Minor)

Musical adaptation of Chapter III of Bram Stoker's gothic masterpiece "Dracula"
(Jonathan Harker's captivity, Dracula climbing down the castle walls, the three vampire brides,
and the child in the sack).

Scale: B Hungarian Minor (root=11, Mode.HUNGARIAN_MINOR) and B Phrygian (root=11, Mode.PHRYGIAN)

Tracks:
  I.   Пленник замка (Prisoner of the Castle) — 70 BPM. B Hungarian Minor.
       Atmosphere: dread, heavy stone doors closing. Heavy filter sweeps on cutoff (CC 74).
  II.  Сползающий во мрак (Crawling into the Void) — 60 BPM. B Phrygian.
       Atmosphere: Dracula crawling lizard-like down the cliff. Creepy strings, syncopated contrabass.
  III. Три искусительницы (The Three Temptresses) — 76 BPM. B Hungarian Minor.
       Atmosphere: the beautiful brides. Call-and-response whispers using Leitmotif sharing.
  IV.  Красный мешок (The Crimson Sack) — 90 BPM. B Hungarian Minor.
       Atmosphere: Dracula's rage, the child in the sack. Thundering timpani gallop and organ swell.
  V.   Безумие рассвета (Dawn of Sanity) — 54 BPM. B Phrygian.
       Atmosphere: tragic sunrise. Waltz accents, flute solo fading out under the sunlight.
"""

import random
from pathlib import Path

from melodica import types
from melodica.theory import Quality
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.accent import RhythmicAccentGenerator
from melodica.composer.automation import AutomationCurve
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.utils import chord_at

# B Hungarian Minor: 11, HUNGARIAN_MINOR (B, C#, D, E#, F#, G, A#)
KEY_MINOR = types.Scale(root=11, mode=types.Mode.HUNGARIAN_MINOR)
# B Phrygian: 11, PHRYGIAN (B, C, D, E, F#, G, A)
KEY_PHRYGIAN = types.Scale(root=11, mode=types.Mode.PHRYGIAN)

random.seed(1897)  # Year of Dracula's first publication
OUT = Path("output/album_dracula_ch3")
OUT.mkdir(parents=True, exist_ok=True)


# =====================================================================
# I. Пленник замка (Prisoner of the Castle) — 70 BPM
# =====================================================================
def produce_prisoner_of_castle():
    """
    Heavy, claustrophobic opening. Uses custom chord durations, heavy automation filter sweeps on CC 74,
    and heavy percussion accents.
    """
    bpm, dur = 70, 128.0

    # Diatonic progression with custom durations (representing shifting rooms and heavy doors closing)
    # Bm(4) -> Em(2) -> F#(2) -> Bm(4) -> G(4) -> C#dim(2) -> F#(2) -> Bm(8)
    prog_str = "i:4.0 - iv:2.0 - V:2.0 - i:4.0 - VI:4.0 - iidim:2.0 - V:2.0 - i:8.0"
    chords = types.parse_progression(prog_str, KEY_MINOR)
    # Replicate chords to fill duration
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Melancholic Violin Solo (Violin - Program 40)
    violin_gen = MelodyGenerator(
        GeneratorParams(
            density=0.48, complexity=0.72,
            velocity_range=(70, 100),
            key_range_low=62, key_range_high=86
        ),
        phrase_length=8.0,
        motif_probability=0.85,
        ornament_probability=0.30
    )
    violin = violin_gen.render(full_chords, KEY_MINOR, dur)

    # Dark atmospheric pad (Pad 89)
    pad = AmbientPadGenerator(
        GeneratorParams(
            density=0.18, velocity_range=(45, 65),
            key_range_low=47, key_range_high=71
        ),
        voicing="spread", overlap=0.2
    ).render(full_chords, KEY_MINOR, dur)

    # Contrasting Contrabass (Acoustic Bass - Program 32)
    # We render bass using BassGenerator, then use chainable algebraic transformations
    bass_notes = BassGenerator(
        GeneratorParams(
            density=0.40, velocity_range=(60, 80),
            key_range_low=23, key_range_high=43
        ),
        style="walking"
    ).render(full_chords, KEY_MINOR, dur)
    
    # Pack bass notes into a Track, then chain algebraic transformations:
    # 1. Transpose down 12 semitones (1 octave) for deep sub frequencies
    # 2. Shift time by 0.05 beats for a slightly lazy, sluggish walking groove
    # 3. Soften velocity to keep sub frequencies clean
    bass_track = types.Track(name="bass", notes=bass_notes)
    bass_track.transpose(-12).shift_time(0.05).scale_velocity(0.85)

    # Timpani (Timpani - Program 47) using RhythmicAccentGenerator (heavy preset)
    timpani = RhythmicAccentGenerator(
        preset="heavy", pitch=35, velocity_humanize=12, accent_strength=1.1
    ).render(full_chords, KEY_MINOR, dur)

    # CC 74 (Filter Cutoff brightness) automation using AutomationCurve.linear and sine_lfo
    # Create slow swelling/sweeping filters representing Jonathan's despair and suffocating walls
    cc_filt = []
    # Every 16 beats, we sweep filter up and down
    for block in range(0, int(dur), 16):
        cc_filt.extend(AutomationCurve.linear(74, 30, 95, float(block), float(block + 8), steps=15))
        cc_filt.extend(AutomationCurve.linear(74, 95, 30, float(block + 8), float(block + 16), steps=15))
    
    # CC 11 (Expression) LFO for string expression swelling
    cc_expr = AutomationCurve.sine_lfo(11, 60, 110, 0.0, dur, period=8.0)

    cc_events = {
        "violin": cc_expr,
        "pad": cc_filt,
        "bass": AutomationCurve.linear(7, 85, 60, 0.0, dur, steps=30)  # volume fade-out
    }

    produce_track(
        tracks={"violin": violin, "pad": pad, "bass": bass_track.notes, "timpani": timpani},
        bpm=bpm,
        instruments={"violin": 40, "pad": 89, "bass": 32, "timpani": 47},
        path=OUT / "01_Prisoner_of_the_Castle.mid",
        mood=Mood.CHAMBER, key=KEY_MINOR,
        chords=full_chords, cc_events=cc_events
    )


# =====================================================================
# II. Сползающий во мрак (Crawling into the Void) — 60 BPM
# =====================================================================
def produce_crawling_into_void():
    """
    Representing Dracula crawling down the castle wall lizard-like.
    Uses B Phrygian scale, high register sliding strings, slow-crawling time offsets,
    syncopated contrabass pulse, and tremolo LFO CC automation.
    """
    bpm, dur = 60, 128.0

    # B Phrygian: Bm -> C -> Am -> Bm -> C -> Dm -> C -> Bm
    prog_str = "i:4.0 - II:4.0 - vii:4.0 - i:4.0 - II:4.0 - iv:4.0 - II:4.0 - i:4.0"
    chords = types.parse_progression(prog_str, KEY_PHRYGIAN)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # High-register crawling strings (Violin - Program 40)
    str_gen = MelodyGenerator(
        GeneratorParams(
            density=0.45, complexity=0.65,
            velocity_range=(65, 88),
            key_range_low=67, key_range_high=91
        ),
        phrase_length=4.0,
        phrase_contour="wave",
        ornament_probability=0.25
    )
    violin_crawling = str_gen.render(full_chords, KEY_PHRYGIAN, dur)

    # Offset creepy strings (Viola - Program 41)
    # We duplicate the crawling melody, shift it by 0.5 beats, transpose it by 3 semitones (minor third)
    # and lower its velocity to create a shivering, out-of-phase round-robin delay
    viola_crawling = [
        types.NoteInfo(pitch=n.pitch, start=n.start, duration=n.duration, velocity=n.velocity)
        for n in violin_crawling
    ]
    viola_track = types.Track(name="viola", notes=viola_crawling)
    viola_track.shift_time(0.5).transpose(3).scale_velocity(0.70)

    # Contrabass (Contrabass - Program 43) syncopated pulse using RhythmicAccentGenerator
    contrabass = RhythmicAccentGenerator(
        preset="syncopated", pitch=None, octave=2, velocity_humanize=8, accent_strength=0.9
    ).render(full_chords, KEY_PHRYGIAN, dur)

    # Solo Flute (Flute - Program 73) whispering theme
    flute = MelodyGenerator(
        GeneratorParams(
            density=0.20, complexity=0.50,
            velocity_range=(50, 75),
            key_range_low=60, key_range_high=79
        ),
        phrase_length=12.0,
        motif_probability=0.75
    ).render(full_chords, KEY_PHRYGIAN, dur)

    # CC 1 (Modulation/vibrato depth) sine LFO to represent the trembling, shivering fear
    cc_vibrato = AutomationCurve.sine_lfo(1, 40, 110, 0.0, dur, period=4.0, steps_per_period=16)

    # CC 74 (Filter Cutoff) exponential swell up to a climax
    cc_filt = AutomationCurve.exponential(74, 40, 100, 0.0, dur, exponent=1.6, steps=40)

    cc_events = {
        "violin": cc_vibrato,
        "viola": cc_vibrato,
        "flute": cc_filt
    }

    produce_track(
        tracks={"violin": violin_crawling, "viola": viola_track.notes, "contrabass": contrabass, "flute": flute},
        bpm=bpm,
        instruments={"violin": 40, "viola": 41, "contrabass": 43, "flute": 73},
        path=OUT / "02_Crawling_into_the_Void.mid",
        mood=Mood.CINEMATIC, key=KEY_PHRYGIAN,
        chords=full_chords, cc_events=cc_events
    )


# =====================================================================
# III. Три искусительницы (The Three Temptresses) — 76 BPM
# =====================================================================
def produce_three_temptresses():
    """
    Representing the three vampire brides in the moonlit chamber.
    Showcases Shared Leitmotif technique:
      - First bride theme rendered, motif captured.
      - Second bride theme response on another instrument with transposed base motif.
      - Third bride theme polyphonic harmony using the same motif.
    Also utilizes delicate nylon guitar pads and harpsichord arpeggios.
    """
    bpm, dur = 76, 144.0

    # Gothic Romance chord progression: Bm -> G -> Em -> F# -> Bm -> D -> Em -> F#
    prog_str = "i:4.0 - VI:4.0 - iv:4.0 - V:4.0 - i:4.0 - III:4.0 - iv:4.0 - V:4.0"
    chords = types.parse_progression(prog_str, KEY_MINOR)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # 1. First Bride Theme (Violin - Program 40)
    violin_gen = MelodyGenerator(
        GeneratorParams(
            density=0.45, complexity=0.68,
            velocity_range=(75, 105),
            key_range_low=62, key_range_high=81
        ),
        phrase_length=8.0,
        motif_probability=0.90,
        ornament_probability=0.35
    )
    first_bride = violin_gen.render(full_chords, KEY_MINOR, dur)

    # Capture the generated leitmotif
    leitmotif = violin_gen._stored_motif
    leitmotif_rhythm = violin_gen._stored_rhythm

    # 2. Second Bride Theme (Oboe - Program 68) - Call and response
    # We pre-inject the captured leitmotif, transposed by 3 semitones (minor third)
    second_gen = MelodyGenerator(
        GeneratorParams(
            density=0.38, complexity=0.60,
            velocity_range=(70, 95),
            key_range_low=59, key_range_high=76
        ),
        phrase_length=8.0,
        motif_probability=0.85,
        base_motif=[m + 3 for m in leitmotif] if leitmotif else None,
        base_motif_rhythm=leitmotif_rhythm
    )
    second_bride = second_gen.render(full_chords, KEY_MINOR, dur)

    # 3. Third Bride Theme (Flute - Program 73) - High-register golden bride
    # She harmonizes using the exact same base motif, shifted down an octave (transposed -12)
    third_gen = MelodyGenerator(
        GeneratorParams(
            density=0.35, complexity=0.55,
            velocity_range=(65, 90),
            key_range_low=71, key_range_high=86
        ),
        phrase_length=8.0,
        motif_probability=0.80,
        base_motif=[m - 12 for m in leitmotif] if leitmotif else None,
        base_motif_rhythm=leitmotif_rhythm
    )
    third_bride = third_gen.render(full_chords, KEY_MINOR, dur)

    # Harpsichord (Harpsichord - Program 6) for delicate shimmering moonlit texture
    harpsichord = ArpeggiatorGenerator(
        GeneratorParams(
            density=0.45, velocity_range=(45, 68),
            key_range_low=59, key_range_high=83
        ),
        pattern="up_down", note_duration=0.25
    ).render(full_chords, KEY_MINOR, dur)

    # Nylon Guitar pad (Nylon Guitar - Program 24)
    guitar = AmbientPadGenerator(
        GeneratorParams(
            density=0.03, velocity_range=(45, 60),
            key_range_low=47, key_range_high=67
        ),
        voicing="spread", overlap=0.1
    ).render(full_chords, KEY_MINOR, dur)

    # Contrabass (Acoustic Bass - Program 32)
    bass = BassGenerator(
        GeneratorParams(
            density=0.35, velocity_range=(55, 75),
            key_range_low=23, key_range_high=45
        ),
        style="walking"
    ).render(full_chords, KEY_MINOR, dur)

    # CC 11 (Expression) sine LFO for sensual swelling on woodwinds and strings
    cc_expr_slow = AutomationCurve.sine_lfo(11, 55, 95, 0.0, dur, period=16.0)

    cc_events = {
        "first_bride": cc_expr_slow,
        "second_bride": AutomationCurve.sine_lfo(11, 50, 90, 0.0, dur, period=12.0),
        "third_bride": AutomationCurve.sine_lfo(11, 45, 88, 0.0, dur, period=8.0)
    }

    produce_track(
        tracks={
            "first_bride": first_bride, "second_bride": second_bride, "third_bride": third_bride,
            "harpsichord": harpsichord, "guitar": guitar, "bass": bass
        },
        bpm=bpm,
        instruments={
            "first_bride": 40, "second_bride": 68, "third_bride": 73,
            "harpsichord": 6, "guitar": 24, "bass": 32
        },
        path=OUT / "03_The_Three_Temptresses.mid",
        mood=Mood.CHAMBER, key=KEY_MINOR,
        chords=full_chords, cc_events=cc_events
    )


# =====================================================================
# IV. Красный мешок (The Crimson Sack) — 90 BPM
# =====================================================================
def produce_crimson_sack():
    """
    Dracula's thundering fury and the wriggling child in the sack.
    Thundering timpani gallop, heavy church organ chords, furious violin theme scaled using scale_velocity(1.35),
    and exponential expression builds.
    """
    bpm, dur = 90, 160.0

    # Furious high-tempo dramatic progression: Bm -> Em -> C#dim -> F# -> G -> C#dim -> F# -> Bm
    prog_str = "i:4.0 - iv:4.0 - iidim:4.0 - V:4.0 - VI:4.0 - iidim:4.0 - V:4.0 - i:4.0"
    chords = types.parse_progression(prog_str, KEY_MINOR)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Furious Lead Violin (Violin - Program 40)
    furious_violin = MelodyGenerator(
        GeneratorParams(
            density=0.68, complexity=0.88,
            velocity_range=(80, 105),
            key_range_low=62, key_range_high=88
        ),
        phrase_length=4.0,
        motif_probability=0.70,
        syncopation=0.35,
        ornament_probability=0.50
    ).render(full_chords, KEY_MINOR, dur)

    # Scale the violin velocities using track transformations for maximum aggression
    violin_track = types.Track(name="furious_violin", notes=furious_violin)
    violin_track.scale_velocity(1.35)  # Scale up velocities for sharp biting sound

    # Church Organ (Church Organ - Program 19) — heavy, ominous chords
    organ = AmbientPadGenerator(
        GeneratorParams(
            density=0.18, velocity_range=(75, 110),
            key_range_low=47, key_range_high=71
        ),
        voicing="cluster", overlap=0.3
    ).render(full_chords, KEY_MINOR, dur)

    # Contrabass (Acoustic Bass - Program 32)
    bass = BassGenerator(
        GeneratorParams(
            density=0.60, velocity_range=(85, 110),
            key_range_low=23, key_range_high=45
        ),
        style="walking"
    ).render(full_chords, KEY_MINOR, dur)

    # Thundering timpani gallop rhythm using RhythmicAccentGenerator (gallop preset)
    timpani = RhythmicAccentGenerator(
        preset="gallop", pitch=36, velocity_humanize=15, accent_strength=1.2
    ).render(full_chords, KEY_MINOR, dur)

    # CC 11 (Expression) exponential swells to mimic terrifying screams of Dracula and child
    cc_expr_swell = []
    # Swell up dynamically every 32 beats
    for block in range(0, int(dur), 32):
        cc_expr_swell.extend(AutomationCurve.exponential(11, 40, 125, float(block), float(block + 24), exponent=2.0, steps=25))
        # Instant duck back to 40
        cc_expr_swell.append((float(block + 24.1), 11, 40))
        # Keep low until next block
        cc_expr_swell.extend(AutomationCurve.linear(11, 40, 50, float(block + 25), float(block + 32), steps=5))

    cc_events = {
        "furious_violin": cc_expr_swell,
        "organ": cc_expr_swell,
        "timpani": AutomationCurve.linear(7, 95, 115, 0.0, dur, steps=20)  # volume crescendo
    }

    produce_track(
        tracks={"furious_violin": violin_track.notes, "organ": organ, "bass": bass, "timpani": timpani},
        bpm=bpm,
        instruments={"furious_violin": 40, "organ": 19, "bass": 32, "timpani": 47},
        path=OUT / "04_The_Crimson_Sack.mid",
        mood=Mood.AGGRESSIVE, key=KEY_MINOR,
        chords=full_chords, cc_events=cc_events
    )


# =====================================================================
# V. Безумие рассвета (Dawn of Sanity) — 54 BPM
# =====================================================================
def produce_dawn_of_sanity():
    """
    Sunrise and tragic return to conscious sanity.
    Uses B Phrygian scale, tragic waltz accent generator rhythm for low cello,
    slow flute solo fading out under the sunrise using exponential volume CC 7 curves,
    and luminous glass pad.
    """
    bpm, dur = 54, 144.0

    # Phrygian Tragic Waltz Chord Progression (3/4 time signature feeling, parsed with durations):
    # Bm(3) -> C(3) -> Dm(3) -> Bm(3) -> Am(3) -> C(3) -> F#(3) -> Bm(3)
    prog_str = "i:3.0 - II:3.0 - iv:3.0 - i:3.0 - vii:3.0 - II:3.0 - V:3.0 - i:3.0"
    chords = types.parse_progression(prog_str, KEY_PHRYGIAN)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Solo Flute (Flute - Program 73) — tragic, crying melody
    flute = MelodyGenerator(
        GeneratorParams(
            density=0.22, complexity=0.55,
            velocity_range=(50, 75),
            key_range_low=60, key_range_high=80
        ),
        phrase_length=6.0,
        motif_probability=0.88,
        ornament_probability=0.20
    ).render(full_chords, KEY_PHRYGIAN, dur)

    # Waltz accent generator for deep cello (Cello - Program 42) acting as waltz accompaniment
    cello_waltz = RhythmicAccentGenerator(
        preset="waltz", pitch=None, octave=3, velocity_humanize=6, accent_strength=0.9
    ).render(full_chords, KEY_PHRYGIAN, dur)

    # Luminous glass pad (Pad 92 - Metallic Pad / Glass)
    glass_pad = AmbientPadGenerator(
        GeneratorParams(
            density=0.03, velocity_range=(40, 55),
            key_range_low=59, key_range_high=83
        ),
        voicing="spread", overlap=0.25
    ).render(full_chords, KEY_PHRYGIAN, dur)

    # Deep contrabass (Acoustic Bass - Program 32) playing on the downbeats (first beat of waltz)
    bass_custom = []
    for block in range(0, int(dur), 3):
        chord = chord_at(full_chords, float(block))
        pitch = (chord.root % 12) + 24 if chord else 23
        bass_custom.append(types.NoteInfo(pitch=pitch, start=float(block), duration=1.5, velocity=85))

    # CC 7 (Volume) exponential fade-out to represent the sunrise melting the horrors of the night
    cc_fade_out = AutomationCurve.exponential(7, 100, 0, 0.0, dur, exponent=1.8, steps=40)

    cc_events = {
        "flute": cc_fade_out,
        "glass_pad": cc_fade_out,
        "cello_waltz": cc_fade_out,
        "bass": cc_fade_out
    }

    produce_track(
        tracks={"flute": flute, "cello_waltz": cello_waltz, "glass_pad": glass_pad, "bass": bass_custom},
        bpm=bpm,
        instruments={"flute": 73, "cello_waltz": 42, "glass_pad": 92, "bass": 32},
        path=OUT / "05_Dawn_of_Sanity.mid",
        mood=Mood.AMBIENT, key=KEY_PHRYGIAN,
        chords=full_chords, cc_events=cc_events
    )


# =====================================================================
# Album Compilation Runner
# =====================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("   БРЭМ СТОКЕР — ДРАКУЛА: ГЛАВА III (Gothic Album in Hungarian Minor)")
    print("   Дневник Джонатана Харкера (продолжение) — В плену, Три вампирши, рассвет")
    print("=" * 80)

    print("\n-> Compiling Track 1: Пленник замка (Prisoner of the Castle)...")
    produce_prisoner_of_castle()

    print("\n-> Compiling Track 2: Сползающий во мрак (Crawling into the Void)...")
    produce_crawling_into_void()

    print("\n-> Compiling Track 3: Три искусительницы (The Three Temptresses)...")
    produce_three_temptresses()

    print("\n-> Compiling Track 4: Красный мешок (The Crimson Sack)...")
    produce_crimson_sack()

    print("\n-> Compiling Track 5: Безумие рассвета (Dawn of Sanity)...")
    produce_dawn_of_sanity()

    print("\n" + "=" * 80)
    print("   CHAPTER III GOTHIC ALBUM SUCCESSFULLY COMPILED!")
    print(f"   MIDI output saved in: {OUT.resolve()}")
    print("=" * 80)
