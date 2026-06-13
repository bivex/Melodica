# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_tin_soldier.py — СТОЙКИЙ ОЛОВЯННЫЙ СОЛДАТИК (PRO ARRANGEMENT)

Advanced orchestral adaptation of Hans Christian Andersen's fairy tale.
Showcases professional arranging techniques:
- Layering (combining Music Box + Glockenspiel + Celesta for a unique timbre)
- Ostinatos (fast 16th note string patterns for driving tension)
- Counter-melodies (Flute answered by Clarinet)
- Brass sections layered with String Ensembles
- Dynamic tempo curves (Accelerando & Ritardando)
- Humanization and velocity scaling to create "breath"

Modes: LYDIAN and HUNGARIAN_MAJOR
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
from melodica.generators.orchestral_brass import TrumpetGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.composer.automation import AutomationCurve
from melodica.composer.album_pipeline import produce_track, Mood

# Scales
KEY_LYDIAN = types.Scale(root=0, mode=types.Mode.LYDIAN)
KEY_HUNGARIAN_MAJOR = types.Scale(root=0, mode=types.Mode.HUNGARIAN_MAJOR)

random.seed(1838)
OUT = Path("output/album_tin_soldier")
OUT.mkdir(parents=True, exist_ok=True)


# =====================================================================
# I. Бумажная балерина (The Paper Ballerina) — 90 BPM
# =====================================================================
def produce_paper_ballerina():
    """
    PRO: Thick, shimmering Lydian dreamscape.
    Layering: Music Box + Glockenspiel + Celesta.
    Melody: Flute with Clarinet counter-melody.
    Bed: Warm Pad + Slow Strings + Harp sweeps.
    """
    bpm, dur = 90, 64.0
    prog_str = "I:4.0 - II:4.0 - vi:4.0 - I:4.0"
    chords = types.parse_progression(prog_str, KEY_LYDIAN)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # --- THE SHIMMER LAYER (Music Box, Glockenspiel, Celesta) ---
    box_gen = ArpeggiatorGenerator(GeneratorParams(density=0.6, velocity_range=(55, 75), key_range_low=72, key_range_high=96), pattern="up_down")
    box = types.Track(name="musicbox", notes=box_gen.render(full_chords, KEY_LYDIAN, dur)).humanize(0.02, 3.0)
    
    glock_gen = ArpeggiatorGenerator(GeneratorParams(density=0.3, velocity_range=(60, 80), key_range_low=84, key_range_high=108), pattern="random")
    glock = types.Track(name="glockenspiel", notes=glock_gen.render(full_chords, KEY_LYDIAN, dur)).humanize(0.03, 5.0)

    celesta_gen = ArpeggiatorGenerator(GeneratorParams(density=0.4, velocity_range=(50, 70), key_range_low=60, key_range_high=84), pattern="up")
    celesta = types.Track(name="celesta", notes=celesta_gen.render(full_chords, KEY_LYDIAN, dur)).humanize(0.01, 2.0)

    # --- THE MELODY & COUNTER-MELODY ---
    flute_gen = MelodyGenerator(GeneratorParams(density=0.4, complexity=0.4, velocity_range=(75, 95), key_range_low=72, key_range_high=96), phrase_length=8.0)
    flute = types.Track(name="flute", notes=flute_gen.render(full_chords, KEY_LYDIAN, dur)).humanize(0.01, 4.0)

    clarinet_gen = MelodyGenerator(GeneratorParams(density=0.25, complexity=0.3, velocity_range=(65, 85), key_range_low=60, key_range_high=79), phrase_length=8.0)
    clarinet = types.Track(name="clarinet", notes=clarinet_gen.render(full_chords, KEY_LYDIAN, dur)).humanize(0.02, 3.0)

    # --- THE BED (Harp, Pad, Strings) ---
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.5, velocity_range=(55, 80), key_range_low=48, key_range_high=84), pattern="up").render(full_chords, KEY_LYDIAN, dur)
    pad = AmbientPadGenerator(GeneratorParams(density=0.3, velocity_range=(45, 60), key_range_low=48, key_range_high=72)).render(full_chords, KEY_LYDIAN, dur)
    strings = StringsEnsembleGenerator(GeneratorParams(density=0.4, velocity_range=(40, 55), key_range_low=36, key_range_high=60)).render(full_chords, KEY_LYDIAN, dur)

    # Fairy tale trumpet — a distant fanfare announcing the ballerina's entrance
    trumpet = TrumpetGenerator(
        GeneratorParams(density=0.15, velocity_range=(55, 80), key_range_low=60, key_range_high=79),
        articulation="legato", con_sordino=True, register=60
    ).render(full_chords, KEY_LYDIAN, dur)

    # Glockenspiel — fairy tale bells shimmering over the shimmer layer
    glock_bells = GlockenspielGenerator(
        GeneratorParams(density=0.35, velocity_range=(50, 70), key_range_low=84, key_range_high=108),
        pattern="random"
    ).render(full_chords, KEY_LYDIAN, dur)

    cc_events = {
        "flute": AutomationCurve.sine_lfo(11, 50, 110, 0.0, dur, period=8.0),
        "strings": AutomationCurve.sine_lfo(11, 40, 80, 0.0, dur, period=16.0)
    }

    produce_track(
        tracks={"box": box.notes, "glock": glock.notes, "celesta": celesta.notes,
                "flute": flute.notes, "clarinet": clarinet.notes,
                "harp": harp, "pad": pad, "strings": strings,
                "trumpet": trumpet, "glock_bells": glock_bells},
        bpm=bpm,
        instruments={"box": 10, "glock": 9, "celesta": 8, "flute": 73, "clarinet": 71,
                     "harp": 46, "pad": 88, "strings": 48,
                     "trumpet": 56, "glock_bells": 9},
        path=OUT / "01_The_Paper_Ballerina.mid",
        mood=Mood.CHAMBER, key=KEY_LYDIAN, chords=full_chords, cc_events=cc_events
    )

# =====================================================================
# II. Полночный тролль (The Midnight Troll) — 110 BPM
# =====================================================================
def produce_midnight_troll():
    """
    PRO: Mischievous Hungarian Major.
    Orchestration: Marimba + Xylophone running fast 16ths. Oboe melody. 
    Staccato Brass stabs. Walking Bassoon and Tuba.
    """
    bpm, dur = 110, 64.0
    prog_str = "I:2.0 - IV:2.0 - II:2.0 - V:2.0"
    chords = types.parse_progression(prog_str, KEY_HUNGARIAN_MAJOR)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # --- MALLETS (Marimba & Xylophone Ostinato) ---
    marimba_gen = ArpeggiatorGenerator(GeneratorParams(density=0.85, velocity_range=(75, 100), key_range_low=48, key_range_high=72), pattern="up_down")
    marimba = types.Track(name="marimba", notes=marimba_gen.render(full_chords, KEY_HUNGARIAN_MAJOR, dur)).humanize(0.01, 5.0)

    xylo_gen = MelodyGenerator(GeneratorParams(density=0.7, complexity=0.9, velocity_range=(80, 110), key_range_low=72, key_range_high=96), phrase_length=4.0)
    xylo = types.Track(name="xylo", notes=xylo_gen.render(full_chords, KEY_HUNGARIAN_MAJOR, dur)).humanize(0.02, 6.0)

    # --- WINDS & BRASS ---
    oboe = MelodyGenerator(GeneratorParams(density=0.6, complexity=0.6, velocity_range=(85, 105), key_range_low=60, key_range_high=84), phrase_length=4.0).render(full_chords, KEY_HUNGARIAN_MAJOR, dur)
    
    # Brass stabs (playing block chords but short duration)
    brass_gen = StringsEnsembleGenerator(GeneratorParams(density=0.4, velocity_range=(80, 105), key_range_low=48, key_range_high=72))
    brass_notes = brass_gen.render(full_chords, KEY_HUNGARIAN_MAJOR, dur)
    for n in brass_notes:
        n.duration = min(n.duration, 0.5)  # Make them staccato stabs
    brass = types.Track(name="brass", notes=brass_notes).humanize(0.01, 8.0)

    # --- LOW END (Bassoon + Tuba + Woodblock) ---
    bassoon = BassGenerator(GeneratorParams(density=0.7, velocity_range=(70, 90), key_range_low=36, key_range_high=55)).render(full_chords, KEY_HUNGARIAN_MAJOR, dur)
    tuba = BassGenerator(GeneratorParams(density=0.4, velocity_range=(85, 110), key_range_low=24, key_range_high=40)).render(full_chords, KEY_HUNGARIAN_MAJOR, dur)
    woodblock = RhythmicAccentGenerator(preset="gallop", pitch=76, velocity_humanize=15, accent_strength=1.5).render(full_chords, KEY_HUNGARIAN_MAJOR, dur)

    # Military trumpet — mischievous staccato stabs, the troll's herald
    trumpet = TrumpetGenerator(
        GeneratorParams(density=0.2, velocity_range=(80, 105), key_range_low=60, key_range_high=79),
        articulation="staccato", con_sordino=False, register=60
    ).render(full_chords, KEY_HUNGARIAN_MAJOR, dur)

    # Glockenspiel — the troll's treasure chest, glinting in the dark
    glock_bells = GlockenspielGenerator(
        GeneratorParams(density=0.4, velocity_range=(65, 90), key_range_low=72, key_range_high=96),
        pattern="up_down"
    ).render(full_chords, KEY_HUNGARIAN_MAJOR, dur)

    produce_track(
        tracks={"marimba": marimba.notes, "xylo": xylo.notes, "oboe": oboe,
                "brass": brass.notes, "bassoon": bassoon, "tuba": tuba, "woodblock": woodblock,
                "trumpet": trumpet, "glock_bells": glock_bells},
        bpm=bpm,
        instruments={"marimba": 12, "xylo": 13, "oboe": 68, "brass": 61,
                     "bassoon": 70, "tuba": 58, "woodblock": 115,
                     "trumpet": 56, "glock_bells": 9},
        path=OUT / "02_The_Midnight_Troll.mid",
        mood=Mood.CHAMBER, key=KEY_HUNGARIAN_MAJOR, chords=full_chords
    )

# =====================================================================
# III. Бумажная лодочка и крыса (The Paper Boat & The Rat) — 130 BPM
# =====================================================================
def produce_paper_boat():
    """
    PRO: Fast cinematic chase in Hungarian Major.
    Orchestration: High and Low Tremolo Strings layered. 
    Fast Spiccato Violin ostinato. Epic French Horns. Pounding Timpani.
    Dynamic: Accelerando from 120 to 145 BPM.
    """
    dur = 80.0
    prog_str = "I:2.0 - vi:2.0 - IV:2.0 - V:2.0"
    chords = types.parse_progression(prog_str, KEY_HUNGARIAN_MAJOR)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # --- WATER TEXTURE (Tremolo High & Low, Fast Spiccato) ---
    trem_high = StringsEnsembleGenerator(GeneratorParams(density=0.9, velocity_range=(75, 105), key_range_low=60, key_range_high=84)).render(full_chords, KEY_HUNGARIAN_MAJOR, dur)
    trem_low = StringsEnsembleGenerator(GeneratorParams(density=0.9, velocity_range=(85, 110), key_range_low=36, key_range_high=60)).render(full_chords, KEY_HUNGARIAN_MAJOR, dur)

    # Fast driving 16th-note ostinato
    spiccato_gen = ArpeggiatorGenerator(GeneratorParams(density=0.95, velocity_range=(80, 115), key_range_low=48, key_range_high=72), pattern="up_down")
    spiccato = types.Track(name="spiccato", notes=spiccato_gen.render(full_chords, KEY_HUNGARIAN_MAJOR, dur)).humanize(0.01, 8.0)

    # --- BRASS & PERCUSSION ---
    horn = MelodyGenerator(GeneratorParams(density=0.5, complexity=0.4, velocity_range=(95, 120), key_range_low=45, key_range_high=65), phrase_length=4.0).render(full_chords, KEY_HUNGARIAN_MAJOR, dur)
    timpani = RhythmicAccentGenerator(preset="gallop", pitch=36, velocity_humanize=12, accent_strength=1.5).render(full_chords, KEY_HUNGARIAN_MAJOR, dur)
    tuba = BassGenerator(GeneratorParams(density=0.6, velocity_range=(90, 115), key_range_low=24, key_range_high=40)).render(full_chords, KEY_HUNGARIAN_MAJOR, dur)

    # Heroic trumpet — the tin soldier stands firm as the boat rushes the rapids
    trumpet = TrumpetGenerator(
        GeneratorParams(density=0.3, velocity_range=(90, 120), key_range_low=60, key_range_high=79),
        articulation="legato", con_sordino=False, register=60, fanfare_mode=True
    ).render(full_chords, KEY_HUNGARIAN_MAJOR, dur)

    # Glockenspiel — the soldier's one-legged resolve, bright and determined
    glock_bells = GlockenspielGenerator(
        GeneratorParams(density=0.45, velocity_range=(70, 95), key_range_low=72, key_range_high=96),
        pattern="up"
    ).render(full_chords, KEY_HUNGARIAN_MAJOR, dur)

    # Accelerando tempo map (120 to 145 BPM)
    tempo_events = [(float(b), 120.0 + (145.0 - 120.0) * (b / dur)) for b in range(0, int(dur), 4)]

    cc_events = {
        "horn": AutomationCurve.sine_lfo(11, 70, 127, 0.0, dur, period=4.0)
    }

    produce_track(
        tracks={"trem_high": trem_high, "trem_low": trem_low, "spiccato": spiccato.notes,
                "horn": horn, "timpani": timpani, "tuba": tuba,
                "trumpet": trumpet, "glock_bells": glock_bells},
        bpm=120,
        instruments={"trem_high": 44, "trem_low": 44, "spiccato": 45, "horn": 60,
                     "timpani": 47, "tuba": 58, "trumpet": 56, "glock_bells": 9},
        path=OUT / "03_The_Paper_Boat.mid",
        mood=Mood.CINEMATIC, key=KEY_HUNGARIAN_MAJOR, chords=full_chords, cc_events=cc_events, tempo_events=tempo_events
    )

# =====================================================================
# IV. Оловянное сердце (The Tin Heart) — 75 BPM
# =====================================================================
def produce_tin_heart():
    """
    PRO: The climax. Lydian mode.
    Massive orchestration: Wide Piano, Emotional Cello, 
    Full String Ensemble + Choir + French Horn Chords.
    Dynamic: Ritardando (slowing down massively) and fade out at the end.
    """
    dur = 64.0
    prog_str = "I:4.0 - II:4.0 - vi:4.0 - I:4.0"
    chords = types.parse_progression(prog_str, KEY_LYDIAN)
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # --- THE CORE ---
    piano_gen = ArpeggiatorGenerator(GeneratorParams(density=0.7, velocity_range=(70, 100), key_range_low=36, key_range_high=84), pattern="up_down")
    piano = types.Track(name="piano", notes=piano_gen.render(full_chords, KEY_LYDIAN, dur)).humanize(0.015, 4.0)

    cello = MelodyGenerator(GeneratorParams(density=0.4, complexity=0.3, velocity_range=(85, 110), key_range_low=48, key_range_high=72), phrase_length=8.0).render(full_chords, KEY_LYDIAN, dur)

    # --- THE MASSIVE ENSEMBLE BED ---
    strings = StringsEnsembleGenerator(GeneratorParams(density=0.6, velocity_range=(75, 100), key_range_low=48, key_range_high=84)).render(full_chords, KEY_LYDIAN, dur)
    choir = AmbientPadGenerator(GeneratorParams(density=0.4, velocity_range=(60, 85), key_range_low=60, key_range_high=84)).render(full_chords, KEY_LYDIAN, dur)
    brass_chords = StringsEnsembleGenerator(GeneratorParams(density=0.4, velocity_range=(80, 105), key_range_low=36, key_range_high=60)).render(full_chords, KEY_LYDIAN, dur)

    # Timpani providing a slow, distant march heartbeat
    timpani = RhythmicAccentGenerator(preset="march", pitch=36, velocity_humanize=10, accent_strength=1.1).render(full_chords, KEY_LYDIAN, dur)
    
    # Lower Timpani velocity manually for a subtle heartbeat
    for n in timpani: n.velocity = int(n.velocity * 0.6)

    # --- DRAMATIC DYNAMICS ---
    # Tempo: Start at 75, speed up to 85, ritardando to 40
    tempo_events = []
    for beat in range(0, int(dur), 4):
        if beat < 32:
            bpm = 75.0 + (85.0 - 75.0) * (beat / 32.0)
        elif beat < 48:
            bpm = 85.0
        else: # massive slowdown as they melt
            bpm = 85.0 - (45.0) * ((beat - 48) / 16.0)
        tempo_events.append((float(beat), bpm))

    # Fade out Expression (CC 11) massively on the ensemble
    cc_fade = AutomationCurve.exponential(11, 110, 10, 48.0, 64.0, exponent=2.0, steps=20)
    cc_events = {
        "strings": cc_fade,
        "choir": cc_fade,
        "brass_chords": cc_fade
    }

    produce_track(
        tracks={"piano": piano.notes, "cello": cello, "strings": strings, "choir": choir, "brass_chords": brass_chords, "timpani": timpani},
        bpm=75,
        instruments={"piano": 0, "cello": 42, "strings": 48, "choir": 52, "brass_chords": 61, "timpani": 47},
        path=OUT / "04_The_Tin_Heart.mid",
        mood=Mood.CINEMATIC, key=KEY_LYDIAN, chords=full_chords, cc_events=cc_events, tempo_events=tempo_events
    )

# =====================================================================
# Main execution
# =====================================================================
if __name__ == "__main__":
    print("================================================================================")
    print("   Г. Х. АНДЕРСЕН — СТОЙКИЙ ОЛОВЯННЫЙ СОЛДАТИК (PRO ARRANGEMENT)")
    print("   Advanced Orchestration: Layering, Ostinatos, Counter-Melodies, Ritardandos")
    print("================================================================================")
    
    print("\n-> Compiling Track 1: Бумажная балерина (The Paper Ballerina)...")
    produce_paper_ballerina()
    
    print("\n-> Compiling Track 2: Полночный тролль (The Midnight Troll)...")
    produce_midnight_troll()
    
    print("\n-> Compiling Track 3: Бумажная лодочка и крыса (The Paper Boat & The Rat)...")
    produce_paper_boat()
    
    print("\n-> Compiling Track 4: Оловянное сердце (The Tin Heart)...")
    produce_tin_heart()
    
    print("\n================================================================================")
    print("   FAIRY TALE ALBUM SUCCESSFULLY COMPILED!")
    print("   MIDI output saved in: " + str(OUT.resolve()))
    print("================================================================================")
