# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_kumoi_reflections.py — 雲井の響 (Kumoi reflections)

Scale: Kumoi [0, 2, 3, 7, 9] (mysterious pentatonic)
Aesthetic: Nature, stillness, shadow, and reflection.

Tracks:
  I.   雲海 (Unkai — Sea of Clouds)
       - 48 BPM. Alto Flute, Koto, and Wind Machine.
  II.  竹林の雨 (Chikurin no Ame — Rain in the Bamboo Forest)
       - 54 BPM. Kalimba, Shamisen, Cabasa shaker, and Rainstick wind machine.
  III. 石庭の瞑想 (Sekitei no Meisō — Stone Garden Meditation)
       - 42 BPM. HandPan, Erhu, and Concert Bass Drum impacts.
  IV.  影絵 (Kage-e — Shadow Play)
       - 64 BPM. Koto, Shamisen, Tenor Drum rolls, and Maracas.
  V.   月の鏡 (Tsuki no Kagami — Mirror of the Moon)
       - 45 BPM. Glass Harp, Alto Flute, Erhu, and fading Wind Machine.
"""

import random
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.drone import DroneGenerator
from melodica.generators.east_asian_ensemble import KotoGenerator, ShamisenGenerator, ErhuGenerator
from melodica.generators.wind_brass_solo import AltoFluteGenerator
from melodica.generators.plucked_solo import KalimbaGenerator
from melodica.generators.percussion_latino import ShakerGenerator
from melodica.generators.sound_design import WindMachineGenerator
from melodica.generators.orchestral_drum import ConcertBassDrumGenerator
from melodica.generators.cinematic_ethereal import HandPanGenerator, GlassHarpGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# KEY: D Kumoi (D-E-F-A-B)
KEY = types.Scale(root=2, mode=types.Mode.KUMOI)

# GM Programs mapping
ALTO_FLUTE = 73       # Flute
KOTO = 107             # Koto
SHAMISEN = 106         # Shamisen
ERHU = 110             # Fiddle (used for Erhu)
KALIMBA = 108          # Kalimba
GLASS_HARP = 98        # Crystal (used for Glass Harp)
HANDPAN = 96           # Synth Rain/Pad (used for Handpan)
WIND_MACHINE = 122     # Seashore (used for Wind/Rain SFX)
DRONE_PAD = 89         # New Age Pad

random.seed(888)
OUT = Path("output/album_kumoi_reflections")
OUT.mkdir(parents=True, exist_ok=True)


def _chords(key, progression: str, duration: float, beats_per_chord: float | None = None):
    parts = progression.split()
    bpc = beats_per_chord if beats_per_chord else duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        c = key.parse_roman(p)
        c.start = i * bpc
        c.duration = bpc
        chords.append(c)
    return chords


def _master(raw: dict, bpm: float, lufs: float = -14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "alto_flute": 0.85,
        "koto": 0.7,
        "shamisen": 0.65,
        "erhu": 0.75,
        "kalimba": 0.8,
        "glass_harp": 0.65,
        "handpan": 0.7,
        "wind_machine": 0.5,
        "shaker_perc": 0.45,
        "bass_drum": 0.8,
        "tenor_drum": 0.75,
        "pad": 0.35,
    })
    # Mix with subtle master dynamics
    mixed = desk.apply_mixing(raw, [("Dynamics", 400, [])], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def _export(tracks: dict, path: Path, bpm: float, instruments: dict, key=KEY):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)


# =====================================================================
# I. 雲海 (Unkai — Sea of Clouds) — 48 BPM
# =====================================================================
def produce_unkai():
    print("  I. 雲海 (Unkai) [Kumoi — 48 BPM — D]")
    dur = 160.0
    chords = _chords(KEY, "i i iv i " * 10, dur)

    # 1. Wind Machine - long sweeps simulating cloud movements
    wind = WindMachineGenerator(
        effect_type="wind", intensity_curve="swell", note_density=1.0
    ).render(chords, KEY, dur)

    # 2. Alto Flute - breathy melodies floating above clouds
    flute = AltoFluteGenerator(
        breath_vibrato=True, note_density=0.4
    ).render(chords, KEY, dur)

    # 3. Koto - occasional double-plucks dripping down
    koto = KotoGenerator(
        tremolo_probability=0.0, double_pluck=True
    ).render(chords, KEY, dur)

    # 4. Pad - deep static background drone
    pad = DroneGenerator(
        GeneratorParams(density=0.03, key_range_low=45, key_range_high=57)
    ).render(chords, KEY, dur)

    tracks = {
        "wind_machine": wind,
        "alto_flute": flute,
        "koto": koto,
        "pad": pad,
    }
    inst = {
        "wind_machine": WIND_MACHINE,
        "alto_flute": ALTO_FLUTE,
        "koto": KOTO,
        "pad": DRONE_PAD,
    }
    _export(tracks, OUT / "01_Unkai.mid", 48, inst)


# =====================================================================
# II. 竹林の雨 (Chikurin no Ame — Rain in the Bamboo Forest) — 54 BPM
# =====================================================================
def produce_chikurin():
    print("  II. 竹林の雨 (Chikurin no Ame) [Kumoi — 54 BPM — A]")
    # Transpose key to A Kumoi
    key_a = types.Scale(root=9, mode=types.Mode.KUMOI)
    dur = 144.0
    chords = _chords(key_a, "i iv i v " * 9, dur)

    # 1. Wind Machine - steady rustling rain/rainstick texture
    rain = WindMachineGenerator(
        effect_type="rainstick", intensity_curve="steady", note_density=1.0
    ).render(chords, key_a, dur)

    # 2. Kalimba - delicate, water-like thudding pluck transients
    kalimba = KalimbaGenerator(
        pop_intensity=0.85, note_density=0.5
    ).render(chords, key_a, dur)

    # 3. Shamisen - sharp buzzy strokes cutting through the rain
    shamisen = ShamisenGenerator(
        sawari_buzz=0.6, strike_velocity=75
    ).render(chords, key_a, dur)

    # 4. Shaker - steady 8th note cabasa shake simulating raindrops
    shaker = ShakerGenerator(
        instrument="cabasa", rhythm_style="8th", note_density=0.9
    ).render(chords, key_a, dur)

    tracks = {
        "wind_machine": rain,
        "kalimba": kalimba,
        "shamisen": shamisen,
        "shaker_perc": shaker,
    }
    inst = {
        "wind_machine": WIND_MACHINE,
        "kalimba": KALIMBA,
        "shamisen": SHAMISEN,
        "shaker_perc": 0,
    }
    _export(tracks, OUT / "02_Chikurin_no_Ame.mid", 54, inst, key=key_a)


# =====================================================================
# III. 石庭 of the Meditation (Sekitei no Meisō — Stone Garden Meditation) — 42 BPM
# =====================================================================
def produce_sekitei():
    print("  III. 石庭の瞑想 (Sekitei no Meisō) [Kumoi — 42 BPM — E]")
    # Transpose key to E Kumoi
    key_e = types.Scale(root=4, mode=types.Mode.KUMOI)
    dur = 180.0
    chords = _chords(key_e, "i i i i " * 10, dur)

    # 1. Handpan - central resonant strike pattern
    handpan = HandPanGenerator(
        strike_damping=0.6
    ).render(chords, key_e, dur)

    # 2. Erhu - monophonic expressive line with wide vibrato
    erhu = ErhuGenerator(
        glide_probability=0.45, vibrato_depth=0.35
    ).render(chords, key_e, dur)

    # 3. Concert Bass Drum - slow spaced single impacts
    bass_drum = ConcertBassDrumGenerator(
        drum_type="bass_drum", pattern_type="single_impact"
    ).render(chords, key_e, dur)

    tracks = {
        "handpan": handpan,
        "erhu": erhu,
        "bass_drum": bass_drum,
    }
    inst = {
        "handpan": HANDPAN,
        "erhu": ERHU,
        "bass_drum": 0,
    }
    _export(tracks, OUT / "03_Sekitei_no_Meiso.mid", 42, inst, key=key_e)


# =====================================================================
# IV. 影絵 (Kage-e — Shadow Play) — 64 BPM
# =====================================================================
def produce_kage_e():
    print("  IV. 影絵 (Kage-e) [Kumoi — 64 BPM — B]")
    # Transpose key to B Kumoi
    key_b = types.Scale(root=11, mode=types.Mode.KUMOI)
    dur = 128.0
    chords = _chords(key_b, "i iv i iv v v i i" * 4, dur)

    # 1. Koto - rapid tremolo picking lines
    koto = KotoGenerator(
        tremolo_probability=0.5, double_pluck=False
    ).render(chords, key_b, dur)

    # 2. Shamisen - sharp virtuoso syncopations
    shamisen = ShamisenGenerator(
        sawari_buzz=0.3, strike_velocity=95
    ).render(chords, key_b, dur)

    # 3. Tenor Drum - rolls and crescendo builds
    tenor_drum = ConcertBassDrumGenerator(
        drum_type="tenor_drum", pattern_type="crescendo", roll_subdivision=0.125
    ).render(chords, key_b, dur)

    # 4. Shaker - accented maracas pattern
    shaker = ShakerGenerator(
        instrument="maracas", rhythm_style="accented", note_density=0.85
    ).render(chords, key_b, dur)

    tracks = {
        "koto": koto,
        "shamisen": shamisen,
        "tenor_drum": tenor_drum,
        "shaker_perc": shaker,
    }
    inst = {
        "koto": KOTO,
        "shamisen": SHAMISEN,
        "tenor_drum": 0,
        "shaker_perc": 0,
    }
    _export(tracks, OUT / "04_Kage-e.mid", 64, inst, key=key_b)


# =====================================================================
# V. 月の鏡 (Tsuki no Kagami — Mirror of the Moon) — 45 BPM
# =====================================================================
def produce_tsuki_no_kagami():
    print("  V. 月の鏡 (Tsuki no Kagami) [Kumoi — 45 BPM — D]")
    dur = 200.0
    chords = _chords(KEY, "i i i iv i i v i " * 5, dur)

    # 1. Glass Harp - crystal clear slow pads with CC 1 friction flutter
    glass_harp = GlassHarpGenerator(
        friction_noise=0.35
    ).render(chords, KEY, dur)

    # 2. Alto Flute - low breathy background responses
    flute = AltoFluteGenerator(
        breath_vibrato=True, note_density=0.35
    ).render(chords, KEY, dur)

    # 3. Erhu - slow expressive final bowings
    erhu = ErhuGenerator(
        glide_probability=0.3, vibrato_depth=0.3
    ).render(chords, KEY, dur)

    # 4. Wind Machine - fading seashore sweeps into final silence
    wind = WindMachineGenerator(
        effect_type="wind", intensity_curve="fade", note_density=0.8
    ).render(chords, KEY, dur)

    tracks = {
        "glass_harp": glass_harp,
        "alto_flute": flute,
        "erhu": erhu,
        "wind_machine": wind,
    }
    inst = {
        "glass_harp": GLASS_HARP,
        "alto_flute": ALTO_FLUTE,
        "erhu": ERHU,
        "wind_machine": WIND_MACHINE,
    }
    _export(tracks, OUT / "05_Tsuki_no_Kagami.mid", 45, inst)


def main():
    print("\n" + "=" * 60)
    print("   雲井の響 — KUMOI REFLECTIONS")
    print("   Japanese Evocative Album (Kumoi Pentatonic Scale)")
    print("   Featuring New Wave 1-5 Generators")
    print("=" * 60 + "\n")

    produce_unkai()
    produce_chikurin()
    produce_sekitei()
    produce_kage_e()
    produce_tsuki_no_kagami()

    print("\n" + "=" * 60)
    print("   雲井の響 — ALBUM GENERATION COMPLETE.")
    print(f"   MIDI output saved to: {OUT.absolute()}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
