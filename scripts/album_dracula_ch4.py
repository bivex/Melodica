# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_dracula_ch4.py — ДРАКУЛА: Глава IV (Dracula: Chapter IV - The Desperate Leap)

Musical adaptation of Chapter IV of Bram Stoker's gothic masterpiece "Dracula"
(Secret correspondence intercepted by the Count, the tragic mother torn by wolves,
finding the blood-bloated Count in the crypt, attacking him with a shovel, and Harker's
final desperate leap into the abyss).

Scale: B Hungarian Minor (root=11, Mode.HUNGARIAN_MINOR) and B Phrygian (root=11, Mode.PHRYGIAN)

Tracks:
  I.   Тайные письма (Secret Correspondence) — 72 BPM. B Hungarian Minor.
       Atmosphere: Harker tries to bribe the gypsies. Gypsy nylon guitar and melancholic violin.
       Features: Chainable .humanize() and .swing() on gypsy guitar and violin.
  II.  Зверство у ворот (Atrocity at the Gates) — 95 to 130 BPM. B Hungarian Minor.
       Atmosphere: Mother screaming for her child, the wolf pack descending.
       Features: Dynamic tempo accelerando (tempo_events), furious violin and heavy galloping timpani.
  III. В склепе Дракулы (Dracula's Vault) — 50 BPM. B Phrygian.
       Atmosphere: Dracula lying bloated like a leech in the box. Cold, terrifying pads and low bass.
       Features: Chainable .morph_scale() transitioning a thematic melody from Hungarian Minor to Phrygian.
  IV.  Удар лопаты (The Shovel's Strike) — 80 to 120 BPM. B Hungarian Minor.
       Atmosphere: Jonathan strikes Dracula with a shovel; Count's paralyzing glare.
       Features: Heavy industrial percussion, sudden tempo accelerando, and exponential LFO filter sweeps.
  V.   Прыжок в бездну (Leap into the Abyss) — 64 BPM. B Phrygian to B Major.
       Atmosphere: Jonathan's final diary entry and his desperate leap to preserve his soul.
       Features: Waltz triplet rhythm, exponential flute fade-out, and .morph_scale() resolving to a glorious B Major chord.
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
from melodica.generators.accent import RhythmicAccentGenerator
from melodica.composer.automation import AutomationCurve
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.utils import chord_at

# B Hungarian Minor: 11, HUNGARIAN_MINOR
KEY_MINOR = types.Scale(root=11, mode=types.Mode.HUNGARIAN_MINOR)
# B Phrygian: 11, PHRYGIAN
KEY_PHRYGIAN = types.Scale(root=11, mode=types.Mode.PHRYGIAN)
# B Major: 11, MAJOR (for the final resolution/escape)
KEY_MAJOR = types.Scale(root=11, mode=types.Mode.MAJOR)

random.seed(1897)  # Year of Dracula's first publication
OUT = Path("output/album_dracula_ch4")
OUT.mkdir(parents=True, exist_ok=True)


# =====================================================================
# I. Тайные письма (Secret Correspondence) — 72 BPM
# =====================================================================
def produce_secret_correspondence():
    """
    Harker tries to bribe the gypsies. Acoustic nylon guitar and gypsy violin.
    Showcases: humanize(), swing() for organic swing feel, and linear/sine curves on filter cutoff.
    """
    bpm, dur = 72, 96.0

    # i:4.0 - iv:4.0 - V:4.0 - i:4.0 (classic minor cycle)
    prog_str = "i:4.0 - iv:4.0 - V:4.0 - i:4.0"
    chords = types.parse_progression(prog_str, KEY_MINOR)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Gypsy Nylon Guitar (Nylon Guitar - Program 24)
    guitar_gen = ArpeggiatorGenerator(
        GeneratorParams(
            density=0.65, velocity_range=(60, 85),
            key_range_low=48, key_range_high=72
        ),
        pattern="up_down"
    )
    guitar_notes = guitar_gen.render(full_chords, KEY_MINOR, dur)
    
    # Apply humanize & swing to guitar for an organic, slightly lazy acoustic groove
    guitar_track = types.Track(name="guitar", notes=guitar_notes)
    guitar_track.humanize(timing_std_beats=0.015, velocity_std=4.0).swing(factor=0.08, grid=0.25)

    # Gypsy Violin Solo (Violin - Program 40)
    violin_gen = MelodyGenerator(
        GeneratorParams(
            density=0.52, complexity=0.75,
            velocity_range=(75, 105),
            key_range_low=62, key_range_high=88
        ),
        phrase_length=8.0,
        motif_probability=0.80
    )
    violin_notes = violin_gen.render(full_chords, KEY_MINOR, dur)
    
    # Apply humanization to the violin solo for realistic intonation/attack deviations
    violin_track = types.Track(name="violin", notes=violin_notes)
    violin_track.humanize(timing_std_beats=0.01, velocity_std=3.0)

    # Cold stone pad (Pad - Program 89)
    pad = AmbientPadGenerator(
        GeneratorParams(
            density=0.20, velocity_range=(45, 60),
            key_range_low=47, key_range_high=71
        )
    ).render(full_chords, KEY_MINOR, dur)

    # Contrabass (Acoustic Bass - Program 32)
    bass = BassGenerator(
        GeneratorParams(
            density=0.45, velocity_range=(55, 75),
            key_range_low=23, key_range_high=43
        )
    ).render(full_chords, KEY_MINOR, dur)

    # CC 74 (Filter Cutoff brightness) automation for the mysterious gypsy campfire / letters burning
    cc_filt = AutomationCurve.sine_lfo(74, 40, 95, 0.0, dur, period=12.0)
    cc_events = {
        "violin": AutomationCurve.exponential(11, 70, 110, 0.0, dur, exponent=1.2, steps=40),
        "pad": cc_filt
    }

    produce_track(
        tracks={"guitar": guitar_track.notes, "violin": violin_track.notes, "pad": pad, "bass": bass},
        bpm=bpm,
        instruments={"guitar": 24, "violin": 40, "pad": 89, "bass": 32},
        path=OUT / "01_Secret_Correspondence.mid",
        mood=Mood.CHAMBER, key=KEY_MINOR,
        chords=full_chords, cc_events=cc_events
    )


# =====================================================================
# II. Зверство у ворот (Atrocity at the Gates) — 95 to 130 BPM
# =====================================================================
def produce_atrocity_at_gates():
    """
    The frantic mother screaming for her baby, and the wolves descending.
    Showcases: Dynamic tempo accelerando (tempo_events) from 95 to 130 BPM,
    furious violin scaling, and galloping timpani.
    """
    bpm, dur = 95, 64.0

    # Tragic and aggressive progression: Bm(4) -> C(4) -> C#dim(4) -> F#(4)
    prog_str = "i:4.0 - bII:4.0 - iidim:4.0 - V:4.0"
    chords = types.parse_progression(prog_str, KEY_MINOR)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Furious Screaming Violin (Violin - Program 40)
    screaming_gen = MelodyGenerator(
        GeneratorParams(
            density=0.75, complexity=0.85,
            velocity_range=(90, 115),
            key_range_low=64, key_range_high=93
        ),
        phrase_length=4.0
    )
    screaming_notes = screaming_gen.render(full_chords, KEY_MINOR, dur)
    
    # Scale violin velocities aggressively to emphasize the mother's terror (screaming effect)
    screaming_track = types.Track(name="screaming_violin", notes=screaming_notes)
    screaming_track.scale_velocity(1.30).transpose(1)  # slightly higher pitch for distress

    # Galloping Timpani (Timpani - Program 47) using RhythmicAccentGenerator
    timpani = RhythmicAccentGenerator(
        preset="gallop", pitch=35, velocity_humanize=10, accent_strength=1.2
    ).render(full_chords, KEY_MINOR, dur)

    # Wolf Pack Brass (French Horn - Program 60)
    horns = StringsEnsembleGenerator(
        GeneratorParams(
            density=0.40, velocity_range=(75, 100),
            key_range_low=47, key_range_high=71
        )
    ).render(full_chords, KEY_MINOR, dur)

    # Dynamic accelerando (the wolf pack running faster and faster)
    # Starts at 95 BPM at beat 0, speeds up to 132 BPM by beat 48
    tempo_events = []
    for beat in range(0, int(dur), 4):
        interpolated_bpm = 95.0 + (132.0 - 95.0) * (beat / dur)
        tempo_events.append((float(beat), interpolated_bpm))

    cc_events = {
        "screaming_violin": AutomationCurve.sine_lfo(1, 0, 120, 0.0, dur, period=4.0),  # heavy vibrato modulation
        "horns": AutomationCurve.exponential(11, 60, 115, 0.0, dur, exponent=2.0, steps=20)
    }

    produce_track(
        tracks={"screaming_violin": screaming_track.notes, "timpani": timpani, "horns": horns},
        bpm=bpm,
        instruments={"screaming_violin": 40, "timpani": 47, "horns": 60},
        path=OUT / "02_Atrocity_at_the_Gates.mid",
        mood=Mood.CINEMATIC, key=KEY_MINOR,
        chords=full_chords, cc_events=cc_events,
        tempo_events=tempo_events
    )


# =====================================================================
# III. В склепе Дракулы (Dracula's Vault) — 50 BPM
# =====================================================================
def produce_draculas_vault():
    """
    Harker climbs into Dracula's crypt and finds him bloated with blood.
    Showcases: Chainable .morph_scale() shifting a motif from B Hungarian Minor to B Phrygian (crypt key),
    exponential swells on CC 11.
    """
    bpm, dur = 50, 80.0

    # Phrygian dread progression: Bm(4) -> C(4) -> Am(4) -> Em(4)
    prog_str = "i:4.0 - bII:4.0 - vii:4.0 - iv:4.0"
    chords = types.parse_progression(prog_str, KEY_PHRYGIAN)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Melancholic Cello Solo (Cello - Program 42)
    # We render a melody in B Hungarian Minor, then morph it to B Phrygian to represent
    # Jonathan's descent from the sunlight into the dark, abnormal crypt atmosphere.
    cello_gen = MelodyGenerator(
        GeneratorParams(
            density=0.48, complexity=0.60,
            velocity_range=(65, 90),
            key_range_low=48, key_range_high=72
        ),
        phrase_length=8.0
    )
    # Render in minor first
    cello_notes = cello_gen.render(full_chords, KEY_MINOR, dur)
    
    # Morph to Phrygian in-place
    cello_track = types.Track(name="cello", notes=cello_notes)
    cello_track.morph_scale(from_scale=KEY_MINOR, to_scale=KEY_PHRYGIAN, strategy="degree")
    # Soften slightly for a muted, dusty cathedral/crypt aesthetic
    cello_track.scale_velocity(0.85)

    # Eerie church organ pad (Church Organ - Program 19)
    organ = AmbientPadGenerator(
        GeneratorParams(
            density=0.18, velocity_range=(45, 65),
            key_range_low=47, key_range_high=76
        )
    ).render(full_chords, KEY_PHRYGIAN, dur)

    # Sub- contrabass drone (Contrabass - Program 43)
    contrabass = BassGenerator(
        GeneratorParams(
            density=0.30, velocity_range=(50, 70),
            key_range_low=23, key_range_high=38
        )
    ).render(full_chords, KEY_PHRYGIAN, dur)
    
    # Heavy low-octave transposition for sub frequencies
    contrabass_track = types.Track(name="contrabass", notes=contrabass)
    contrabass_track.transpose(-12).scale_velocity(0.90)

    # CC 11 (Expression) swells to represent Dracula's chest rising and falling slowly as he breathes blood
    cc_expr = AutomationCurve.sine_lfo(11, 45, 105, 0.0, dur, period=10.0)

    cc_events = {
        "cello": cc_expr,
        "organ": AutomationCurve.exponential(74, 30, 85, 0.0, dur, exponent=1.5, steps=30),  # filter opening up slowly
        "contrabass": AutomationCurve.linear(7, 80, 50, 0.0, dur, steps=20)  # volume fading
    }

    produce_track(
        tracks={"cello": cello_track.notes, "organ": organ, "contrabass": contrabass_track.notes},
        bpm=bpm,
        instruments={"cello": 42, "organ": 19, "contrabass": 43},
        path=OUT / "03_Draculas_Vault.mid",
        mood=Mood.CHAMBER, key=KEY_PHRYGIAN,
        chords=full_chords, cc_events=cc_events
    )


# =====================================================================
# IV. Удар лопаты (The Shovel's Strike) — 80 to 120 BPM
# =====================================================================
def produce_shovels_strike():
    """
    Jonathan strikes Dracula with a shovel; Count's paralyzing glare.
    Showcases: RhythmicAccentGenerator (march preset), sudden tempo accelerando (tempo_events),
    and exponential LFO sweeps.
    """
    bpm, dur = 80, 48.0

    # Driving, martial progression: Bm(2) -> F#(2) -> G(2) -> Em(2)
    prog_str = "i:2.0 - V:2.0 - VI:2.0 - iv:2.0"
    chords = types.parse_progression(prog_str, KEY_MINOR)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Furious Violin (Violin - Program 40)
    violin_gen = MelodyGenerator(
        GeneratorParams(
            density=0.72, complexity=0.80,
            velocity_range=(85, 115),
            key_range_low=60, key_range_high=86
        ),
        phrase_length=4.0
    )
    violin = violin_gen.render(full_chords, KEY_MINOR, dur)
    violin_track = types.Track(name="violin", notes=violin)
    violin_track.scale_velocity(1.20)

    # Shovel strike accents (Timpani - Program 47) using RhythmicAccentGenerator
    # March preset represents the steady, heavy march of doom / shoveling
    timpani = RhythmicAccentGenerator(
        preset="march", pitch=36, velocity_humanize=8, accent_strength=1.3
    ).render(full_chords, KEY_MINOR, dur)

    # Low Cello Stabs (Cello - Program 42)
    cello = StringsEnsembleGenerator(
        GeneratorParams(
            density=0.55, velocity_range=(75, 100),
            key_range_low=36, key_range_high=60
        )
    ).render(full_chords, KEY_MINOR, dur)

    # Sudden tempo accelerando as Jonathan gets terrified and strikes desperately
    # Starts at 80 BPM, builds up to 125 BPM at the climax
    tempo_events = []
    for beat in range(0, int(dur), 2):
        interpolated_bpm = 80.0 + (125.0 - 80.0) * (beat / dur)
        tempo_events.append((float(beat), interpolated_bpm))

    # CC 74 exponential automation representing Dracula's gaze swelling
    cc_gaze = AutomationCurve.exponential(74, 40, 110, 0.0, dur, exponent=2.5, steps=30)

    cc_events = {
        "violin": AutomationCurve.sine_lfo(1, 10, 110, 0.0, dur, period=2.0),
        "cello": cc_gaze
    }

    produce_track(
        tracks={"violin": violin_track.notes, "timpani": timpani, "cello": cello},
        bpm=bpm,
        instruments={"violin": 40, "timpani": 47, "cello": 42},
        path=OUT / "04_The_Shovels_Strike.mid",
        mood=Mood.CINEMATIC, key=KEY_MINOR,
        chords=full_chords, cc_events=cc_events,
        tempo_events=tempo_events
    )


# =====================================================================
# V. Прыжок в бездну (Leap into the Abyss) — 64 BPM
# =====================================================================
def produce_leap_into_abyss():
    """
    Jonathan leaps from the castle wall.
    Showcases: Waltz accent pattern, exponential flute fade-out, and .morph_scale()
    modulating a final high-pitched chord into B Major to symbolize his soul's preservation.
    """
    bpm, dur = 64, 80.0

    # Tragic waltz progression: Bm(6) -> G(6) -> C(6) -> F#(6)
    prog_str = "i:6.0 - VI:6.0 - bII:6.0 - V:6.0"
    chords = types.parse_progression(prog_str, KEY_PHRYGIAN)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur:
                break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Haunting Flute Solo (Flute - Program 73)
    flute_gen = MelodyGenerator(
        GeneratorParams(
            density=0.45, complexity=0.65,
            velocity_range=(70, 95),
            key_range_low=67, key_range_high=91
        ),
        phrase_length=6.0
    )
    flute_notes = flute_gen.render(full_chords, KEY_PHRYGIAN, dur)
    flute_track = types.Track(name="flute", notes=flute_notes)
    
    # Humanize the flute solo for realistic breath control
    flute_track.humanize(timing_std_beats=0.012, velocity_std=3.0)

    # Waltz accompaniment (Cello - Program 42) using RhythmicAccentGenerator (waltz preset)
    cello_waltz = RhythmicAccentGenerator(
        preset="waltz", pitch=None, octave=4, velocity_humanize=8
    ).render(full_chords, KEY_PHRYGIAN, dur)

    # High airy angelic pad representing hope (Pad 92 - Metallic Pad)
    # The final chord is morphed into B Major to represent Jonathan's spiritual salvation as he leaps
    pad_gen = AmbientPadGenerator(
        GeneratorParams(
            density=0.25, velocity_range=(45, 65),
            key_range_low=60, key_range_high=84
        )
    )
    pad_notes = pad_gen.render(full_chords, KEY_PHRYGIAN, dur)
    
    # We select the final note events of the pad (after beat 70) and morph them to B Major scale
    for note in pad_notes:
        if note.start >= 70.0:
            note.morph_scale(from_scale=KEY_PHRYGIAN, to_scale=KEY_MAJOR, strategy="degree")
            note.velocity = 95  # brighten the final major chord

    # Low double bass pulses (Contrabass - Program 43)
    contrabass = BassGenerator(
        GeneratorParams(
            density=0.35, velocity_range=(55, 75),
            key_range_low=23, key_range_high=40
        )
    ).render(full_chords, KEY_PHRYGIAN, dur)

    # CC 7 (Volume) exponential fade-out on the flute as Jonathan leaps into the air and disappears
    cc_fade = AutomationCurve.exponential(7, 95, 0, 70.0, 80.0, exponent=1.8, steps=15)

    cc_events = {
        "flute": cc_fade,
        "pad": AutomationCurve.linear(74, 50, 95, 60.0, 78.0, steps=10)  # filter opens on morph
    }

    produce_track(
        tracks={"flute": flute_track.notes, "cello_waltz": cello_waltz, "pad": pad_notes, "contrabass": contrabass},
        bpm=bpm,
        instruments={"flute": 73, "cello_waltz": 42, "pad": 92, "contrabass": 43},
        path=OUT / "05_Leap_into_the_Abyss.mid",
        mood=Mood.CHAMBER, key=KEY_PHRYGIAN,
        chords=full_chords, cc_events=cc_events
    )


# =====================================================================
# Main execution
# =====================================================================
if __name__ == "__main__":
    print("================================================================================")
    print("   БРЭМ СТОКЕР — ДРАКУЛА: ГЛАВА IV (Gothic Album - The Desperate Leap)")
    print("   Дневник Джонатана Харкера (продолжение) — Побег, склеп, удар лопаты, бездна")
    print("================================================================================")
    
    print("\n-> Compiling Track 1: Тайные письма (Secret Correspondence)...")
    produce_secret_correspondence()
    
    print("\n-> Compiling Track 2: Зверство у ворот (Atrocity at the Gates)...")
    produce_atrocity_at_gates()
    
    print("\n-> Compiling Track 3: В склепе Дракулы (Dracula's Vault)...")
    produce_draculas_vault()
    
    print("\n-> Compiling Track 4: Удар лопаты (The Shovel's Strike)...")
    produce_shovels_strike()
    
    print("\n-> Compiling Track 5: Прыжок в бездну (Leap into the Abyss)...")
    produce_leap_into_abyss()
    
    print("\n================================================================================")
    print("   CHAPTER IV GOTHIC ALBUM SUCCESSFULLY COMPILED!")
    print("   MIDI output saved in: " + str(OUT.resolve()))
    print("================================================================================")
