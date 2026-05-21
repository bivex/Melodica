# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_black_danube_dreams.py — BLACK DANUBE DREAMS

Concept: A dark-folk, neoclassical, ethnic cinematic album in A Hungarian Minor.
Instruments (8): Cello, Synth Bass 1, Acoustic Guitar (nylon), Viola, French Horn, Flute, Music Box, Pad 7 (halo).
"""

import random
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.accent import RhythmicAccentGenerator
from melodica.composer.automation import AutomationCurve
from melodica.composer.album_pipeline import produce_track, Mood

# A Hungarian Minor: Root = 9 (A)
KEY_A_HUNGARIAN = types.Scale(root=9, mode=types.Mode.HUNGARIAN_MINOR)

random.seed(1010)
OUT = Path("output/album_black_danube_dreams")
OUT.mkdir(parents=True, exist_ok=True)

# INSTRUMENT MAPPING
INST = {
    "piano": 0, "musicbox": 10, "guitar": 24, "bass": 38,
    "viola": 41, "cello": 42, "horn": 60, "flute": 73, "pad": 94
}

# =====================================================================
# 1. Ashes Over Budapest (82 BPM)
# =====================================================================
def produce_ashes_over_budapest():
    """
    Main: Cello, French Horn, Pad 7.
    Mood: Anxious intro.
    """
    bpm, dur = 82, 64.0
    chords = types.parse_progression("i:4.0 - iv:4.0 - VI:4.0 - V:4.0", KEY_A_HUNGARIAN)
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Cello - Main Riff
    cello = MelodyGenerator(GeneratorParams(density=0.5, complexity=0.4, velocity_range=(65, 85), key_range_low=36, key_range_high=60), phrase_length=8.0).render(full_chords, KEY_A_HUNGARIAN, dur)
    # Pad 7 - Background
    pad = AmbientPadGenerator(GeneratorParams(density=0.3, velocity_range=(45, 65), key_range_low=60, key_range_high=84)).render(full_chords, KEY_A_HUNGARIAN, dur)
    # French Horn - Big phrases
    horn = MelodyGenerator(GeneratorParams(density=0.3, complexity=0.2, velocity_range=(75, 100), key_range_low=45, key_range_high=65), phrase_length=8.0).render(full_chords, KEY_A_HUNGARIAN, dur)
    # Music Box - Sparse high notes
    box = ArpeggiatorGenerator(GeneratorParams(density=0.2, velocity_range=(50, 70), key_range_low=84, key_range_high=108), pattern="random").render(full_chords, KEY_A_HUNGARIAN, dur)

    cc_events = {"horn": AutomationCurve.sine_lfo(11, 50, 110, 0.0, dur, period=8.0)}

    produce_track(
        tracks={"cello": cello, "pad": pad, "horn": horn, "musicbox": box},
        bpm=bpm, instruments={"cello": INST["cello"], "pad": INST["pad"], "horn": INST["horn"], "musicbox": INST["musicbox"]},
        path=OUT / "01_Ashes_Over_Budapest.mid", mood=Mood.CHAMBER, key=KEY_A_HUNGARIAN, chords=full_chords, cc_events=cc_events
    )

# =====================================================================
# 2. Moonlit Caravan (110 BPM)
# =====================================================================
def produce_moonlit_caravan():
    """
    Main: Nylon Guitar, Viola, Flute.
    Mood: Night journey. Fast arpeggios, oriental flute.
    """
    bpm, dur = 110, 64.0
    chords = types.parse_progression("i:4.0 - II:4.0 - i:4.0 - vii:4.0", KEY_A_HUNGARIAN)
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    guitar = ArpeggiatorGenerator(GeneratorParams(density=0.8, velocity_range=(65, 85), key_range_low=48, key_range_high=72), pattern="up_down").render(full_chords, KEY_A_HUNGARIAN, dur)
    viola = MelodyGenerator(GeneratorParams(density=0.4, complexity=0.5, velocity_range=(70, 90), key_range_low=60, key_range_high=84), phrase_length=4.0).render(full_chords, KEY_A_HUNGARIAN, dur)
    flute = MelodyGenerator(GeneratorParams(density=0.6, complexity=0.7, velocity_range=(80, 105), key_range_low=72, key_range_high=96), phrase_length=8.0).render(full_chords, KEY_A_HUNGARIAN, dur)
    bass = BassGenerator(GeneratorParams(density=0.6, velocity_range=(70, 90), key_range_low=24, key_range_high=36)).render(full_chords, KEY_A_HUNGARIAN, dur)

    produce_track(
        tracks={"guitar": guitar, "viola": viola, "flute": flute, "bass": bass},
        bpm=bpm, instruments={"guitar": INST["guitar"], "viola": INST["viola"], "flute": INST["flute"], "bass": INST["bass"]},
        path=OUT / "02_Moonlit_Caravan.mid", mood=Mood.CHAMBER, key=KEY_A_HUNGARIAN, chords=full_chords
    )

# =====================================================================
# 3. Cathedral of Smoke (68 BPM)
# =====================================================================
def produce_cathedral_of_smoke():
    """
    Main: Pad 7, Horn, Music Box.
    Mood: Dark mystical atmosphere. Very wide ambient.
    """
    bpm, dur = 68, 64.0
    chords = types.parse_progression("i:8.0 - iv:8.0 - i:8.0 - V:8.0", KEY_A_HUNGARIAN)
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    pad = AmbientPadGenerator(GeneratorParams(density=0.5, velocity_range=(50, 75), key_range_low=48, key_range_high=84)).render(full_chords, KEY_A_HUNGARIAN, dur)
    horn = MelodyGenerator(GeneratorParams(density=0.2, complexity=0.2, velocity_range=(75, 100), key_range_low=45, key_range_high=60), phrase_length=8.0).render(full_chords, KEY_A_HUNGARIAN, dur)
    box = ArpeggiatorGenerator(GeneratorParams(density=0.3, velocity_range=(40, 60), key_range_low=84, key_range_high=108), pattern="random").render(full_chords, KEY_A_HUNGARIAN, dur)
    cello = StringsEnsembleGenerator(GeneratorParams(density=0.4, velocity_range=(55, 80), key_range_low=36, key_range_high=48)).render(full_chords, KEY_A_HUNGARIAN, dur)

    cc_events = {"pad": AutomationCurve.sine_lfo(74, 30, 85, 0.0, dur, period=16.0)}

    produce_track(
        tracks={"pad": pad, "horn": horn, "musicbox": box, "cello": cello},
        bpm=bpm, instruments={"pad": INST["pad"], "horn": INST["horn"], "musicbox": INST["musicbox"], "cello": INST["cello"]},
        path=OUT / "03_Cathedral_of_Smoke.mid", mood=Mood.CINEMATIC, key=KEY_A_HUNGARIAN, chords=full_chords, cc_events=cc_events
    )

# =====================================================================
# 4. Dance of the Hollow King (132 BPM)
# =====================================================================
def produce_dance_of_hollow_king():
    """
    Main: Viola, Guitar, Synth Bass.
    Mood: Insane ritual dance. Aggressive ostinato.
    """
    bpm, dur = 132, 64.0
    chords = types.parse_progression("i:2.0 - VI:2.0 - V:2.0 - i:2.0", KEY_A_HUNGARIAN)
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    guitar = ArpeggiatorGenerator(GeneratorParams(density=0.9, velocity_range=(75, 100), key_range_low=48, key_range_high=72), pattern="up_down").render(full_chords, KEY_A_HUNGARIAN, dur)
    viola = MelodyGenerator(GeneratorParams(density=0.8, complexity=0.9, velocity_range=(85, 110), key_range_low=60, key_range_high=84), phrase_length=2.0).render(full_chords, KEY_A_HUNGARIAN, dur)
    bass = ArpeggiatorGenerator(GeneratorParams(density=0.8, velocity_range=(80, 105), key_range_low=24, key_range_high=36), pattern="up").render(full_chords, KEY_A_HUNGARIAN, dur)
    
    # Flute as sharp staccato accents
    flute = RhythmicAccentGenerator(preset="gallop", pitch=84, velocity_humanize=15, accent_strength=1.5).render(full_chords, KEY_A_HUNGARIAN, dur)

    produce_track(
        tracks={"guitar": guitar, "viola": viola, "bass": bass, "flute": flute},
        bpm=bpm, instruments={"guitar": INST["guitar"], "viola": INST["viola"], "bass": INST["bass"], "flute": INST["flute"]},
        path=OUT / "04_Dance_of_the_Hollow_King.mid", mood=Mood.CINEMATIC, key=KEY_A_HUNGARIAN, chords=full_chords
    )

# =====================================================================
# 5. Last Train to Transylvania (90 BPM)
# =====================================================================
def produce_last_train():
    """
    Main: Full Ensemble.
    Structure: Intro (0-16) -> Verse (16-48) -> Climax (48-80) -> Outro (80-96)
    """
    bpm, dur = 90, 96.0
    chords = types.parse_progression("i:4.0 - iv:4.0 - VI:4.0 - V:4.0", KEY_A_HUNGARIAN)
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # Generate full tracks first
    box_full = ArpeggiatorGenerator(GeneratorParams(density=0.5, velocity_range=(50, 70), key_range_low=84, key_range_high=108), pattern="random").render(full_chords, KEY_A_HUNGARIAN, dur)
    pad_full = AmbientPadGenerator(GeneratorParams(density=0.4, velocity_range=(50, 70), key_range_low=60, key_range_high=84)).render(full_chords, KEY_A_HUNGARIAN, dur)
    guitar_full = ArpeggiatorGenerator(GeneratorParams(density=0.7, velocity_range=(65, 85), key_range_low=48, key_range_high=72), pattern="up_down").render(full_chords, KEY_A_HUNGARIAN, dur)
    viola_full = MelodyGenerator(GeneratorParams(density=0.4, complexity=0.4, velocity_range=(75, 95), key_range_low=60, key_range_high=84), phrase_length=8.0).render(full_chords, KEY_A_HUNGARIAN, dur)
    horn_full = MelodyGenerator(GeneratorParams(density=0.5, complexity=0.3, velocity_range=(85, 110), key_range_low=45, key_range_high=65), phrase_length=4.0).render(full_chords, KEY_A_HUNGARIAN, dur)
    flute_full = MelodyGenerator(GeneratorParams(density=0.5, complexity=0.6, velocity_range=(80, 105), key_range_low=72, key_range_high=96), phrase_length=8.0).render(full_chords, KEY_A_HUNGARIAN, dur)
    cello_full = StringsEnsembleGenerator(GeneratorParams(density=0.6, velocity_range=(70, 95), key_range_low=36, key_range_high=60)).render(full_chords, KEY_A_HUNGARIAN, dur)
    bass_full = BassGenerator(GeneratorParams(density=0.6, velocity_range=(80, 100), key_range_low=24, key_range_high=36)).render(full_chords, KEY_A_HUNGARIAN, dur)

    # Filter notes by section
    def filter_beats(notes, start_b, end_b):
        return [n for n in notes if start_b <= n.start < end_b]

    # Structure Assembly
    # Intro: 0-16 -> box, pad
    # Verse: 16-48 -> guitar, viola, cello, pad
    # Climax: 48-80 -> all 8
    # Outro: 80-96 -> pad, flute(distant), box
    
    box = filter_beats(box_full, 0, 16) + filter_beats(box_full, 48, 80) + filter_beats(box_full, 80, 96)
    pad = filter_beats(pad_full, 0, 96)
    guitar = filter_beats(guitar_full, 16, 80)
    viola = filter_beats(viola_full, 16, 80)
    cello = filter_beats(cello_full, 16, 80)
    horn = filter_beats(horn_full, 48, 80)
    bass = filter_beats(bass_full, 48, 80)
    
    # Flute in Climax + Distant Outro
    flute_climax = filter_beats(flute_full, 48, 80)
    flute_outro = filter_beats(flute_full, 80, 96)
    for n in flute_outro:
        n.velocity = int(n.velocity * 0.6) # make it distant
    flute = flute_climax + flute_outro

    # Master Fade out for the outro
    cc_events = {
        "pad": AutomationCurve.linear(7, 100, 0, 88.0, 96.0, steps=10),
        "flute": AutomationCurve.linear(7, 100, 0, 88.0, 96.0, steps=10),
        "musicbox": AutomationCurve.linear(7, 100, 0, 88.0, 96.0, steps=10)
    }

    produce_track(
        tracks={"musicbox": box, "pad": pad, "guitar": guitar, "viola": viola, "cello": cello, "horn": horn, "bass": bass, "flute": flute},
        bpm=bpm, 
        instruments={"musicbox": INST["musicbox"], "pad": INST["pad"], "guitar": INST["guitar"], "viola": INST["viola"], 
                     "cello": INST["cello"], "horn": INST["horn"], "bass": INST["bass"], "flute": INST["flute"]},
        path=OUT / "05_Last_Train_to_Transylvania.mid", mood=Mood.CINEMATIC, key=KEY_A_HUNGARIAN, chords=full_chords, cc_events=cc_events
    )

if __name__ == "__main__":
    print("================================================================================")
    print("   BLACK DANUBE DREAMS (A Hungarian Minor Cinematic Album)")
    print("================================================================================")
    
    print("\n-> Compiling Track 1: Ashes Over Budapest...")
    produce_ashes_over_budapest()
    
    print("\n-> Compiling Track 2: Moonlit Caravan...")
    produce_moonlit_caravan()
    
    print("\n-> Compiling Track 3: Cathedral of Smoke...")
    produce_cathedral_of_smoke()
    
    print("\n-> Compiling Track 4: Dance of the Hollow King...")
    produce_dance_of_hollow_king()

    print("\n-> Compiling Track 5: Last Train to Transylvania...")
    produce_last_train()
    
    print("\n================================================================================")
    print("   ALBUM SUCCESSFULLY COMPILED!")
    print("   MIDI output saved in: " + str(OUT.resolve()))
    print("================================================================================")
