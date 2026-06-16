# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_ampir_v.py — 吸血鬼・V (Kyuuketsuki V — Empire V Japanese Reading Soundtrack)

Scale: Kumoi & Hirajoshi
Aesthetic: Vampirism, elite transition, post-modern mystery, and Japanese minimal stillness.

Tracks:
  I.   緑の矢印 (Midori no Yajirushi — The Green Arrow)
       - 50 BPM. Key: A Kumoi. Mysterious invitation on the summer solstice.
       - Feat. WindMachine (rainstick), Kalimba (footsteps), Alto Flute, and Shaker.
  II.  黒い仮面と赤い室 (Kuroi Kamen to Akai Shitsu — Black Mask and Red Room)
       - 44 BPM. Key: D Hirajoshi. Waking up tied to the wall facing Brama.
       - Feat. Glass Harp (creepy pad), Shamisen (tense plucks), and Concert Bass Drum (rolls).
  III. 舌の目覚め (Shita no Mezame — Awakening of the Tongue)
       - 40 BPM. Key: E Kumoi. Brama's bite and the transfer of the vampire tongue.
       - Feat. Erhu (crying portamento), Koto (pulsing tremolos), and Concert Bass Drum (impacts).
  IV.  太陽の都市 (Taiyō no Toshi — Sunny City)
       - 55 BPM. Key: G Hirojoshi. Nostalgia of childhood, grasshoppers, and the vampire-dog fan.
       - Feat. Handpan, Alto Flute, and Kalimba (music box feel).
  V.   赤い液体の高貴 (Akai Ekitai no Kōki — Nobility of the Red Liquid)
       - 46 BPM. Key: D Kumoi. Transcendent realization of vampire nature and blood.
       - Feat. Glass Harp, Erhu, and fading Wind Machine.
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

# GM Programs mapping
ALTO_FLUTE = 73
KOTO = 107
SHAMISEN = 106
ERHU = 110
KALIMBA = 108
GLASS_HARP = 98
HANDPAN = 96
WIND_MACHINE = 122
DRONE_PAD = 89

random.seed(999)
OUT = Path("output/album_ampir_v")
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


def _master(raw: dict, bpm: float, lufs: float = -15.0):
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
    mixed = desk.apply_mixing(raw, [("Dynamics", 400, [])], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def _export(tracks: dict, path: Path, bpm: float, instruments: dict, key):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)


# =====================================================================
# I. 緑の矢印 (The Green Arrow) — 50 BPM — A Kumoi
# =====================================================================
def produce_green_arrow():
    print("  I. 緑の矢印 (The Green Arrow) [Kumoi — 50 BPM — A]")
    key_a = types.Scale(root=9, mode=types.Mode.KUMOI)
    dur = 150.0
    chords = _chords(key_a, "i i iv i " * 8, dur)

    # Footsteps and mysterious raindrop transients
    kalimba = KalimbaGenerator(
        pop_intensity=0.8, note_density=0.4
    ).render(chords, key_a, dur)

    # Searching breathy alto flute melody
    flute = AltoFluteGenerator(
        breath_vibrato=True, note_density=0.45
    ).render(chords, key_a, dur)

    # Steady rustling rainstick in the background
    rain = WindMachineGenerator(
        effect_type="rainstick", intensity_curve="steady", note_density=0.9
    ).render(chords, key_a, dur)

    # Subtle cabasa shake dynamics
    shaker = ShakerGenerator(
        instrument="cabasa", rhythm_style="8th", note_density=0.8
    ).render(chords, key_a, dur)

    tracks = {
        "kalimba": kalimba,
        "alto_flute": flute,
        "wind_machine": rain,
        "shaker_perc": shaker,
    }
    inst = {
        "kalimba": KALIMBA,
        "alto_flute": ALTO_FLUTE,
        "wind_machine": WIND_MACHINE,
        "shaker_perc": 0,
    }
    _export(tracks, OUT / "01_Midori_no_Yajirushi.mid", 50, inst, key_a)


# =====================================================================
# II. 黒い仮面と赤い室 (Black Mask and Red Room) — 44 BPM — D Hirajoshi
# =====================================================================
def produce_red_room():
    print("  II. 黒い仮面と赤い室 (Black Mask and Red Room) [Hirajoshi — 44 BPM — D]")
    key_d = types.Scale(root=2, mode=types.Mode.HIROJOSHI)
    dur = 160.0
    chords = _chords(key_d, "i i iv v i i i i" * 5, dur)

    # Creepy crystal pad representing Brama's plague doctor mask
    glass = GlassHarpGenerator(
        friction_noise=0.45
    ).render(chords, key_d, dur)

    # Sudden tense shamisen strokes representing Roman's confusion
    shamisen = ShamisenGenerator(
        sawari_buzz=0.7, strike_velocity=85
    ).render(chords, key_d, dur)

    # Heartbeat/tenor drum crescendos building suspense
    tenor = ConcertBassDrumGenerator(
        drum_type="tenor_drum", pattern_type="crescendo", roll_subdivision=0.25
    ).render(chords, key_d, dur)

    tracks = {
        "glass_harp": glass,
        "shamisen": shamisen,
        "tenor_drum": tenor,
    }
    inst = {
        "glass_harp": GLASS_HARP,
        "shamisen": SHAMISEN,
        "tenor_drum": 0,
    }
    _export(tracks, OUT / "02_Kuroi_Kamen_to_Akai_Shitsu.mid", 44, inst, key_d)


# =====================================================================
# III. 舌の目覚め (Awakening of the Tongue) — 40 BPM — E Kumoi
# =====================================================================
def produce_tongue_awakening():
    print("  III. 舌の目覚め (Awakening of the Tongue) [Kumoi — 40 BPM — E]")
    key_e = types.Scale(root=4, mode=types.Mode.KUMOI)
    dur = 180.0
    chords = _chords(key_e, "i i i iv i i v i" * 5, dur)

    # Lyrical, crying erhu representing the pain and transformation of the bite
    erhu = ErhuGenerator(
        glide_probability=0.55, vibrato_depth=0.4
    ).render(chords, key_e, dur)

    # Pulsing koto tremolos representing blood flow
    koto = KotoGenerator(
        tremolo_probability=0.6, double_pluck=False
    ).render(chords, key_e, dur)

    # Massive concert bass drum impacts at major boundaries
    bass_drum = ConcertBassDrumGenerator(
        drum_type="bass_drum", pattern_type="single_impact"
    ).render(chords, key_e, dur)

    tracks = {
        "erhu": erhu,
        "koto": koto,
        "bass_drum": bass_drum,
    }
    inst = {
        "erhu": ERHU,
        "koto": KOTO,
        "bass_drum": 0,
    }
    _export(tracks, OUT / "03_Shita_no_Mezame.mid", 40, inst, key_e)


# =====================================================================
# IV. 太陽の都市 (Sunny City) — 55 BPM — G Hirojoshi
# =====================================================================
def produce_sunny_city():
    print("  IV. 太陽の都市 (Sunny City) [Hirojoshi — 55 BPM — G]")
    key_g = types.Scale(root=7, mode=types.Mode.HIROJOSHI)
    dur = 150.0
    chords = _chords(key_g, "i iv i v i iv v i" * 4, dur)

    # Meditative childhood handpan patterns
    handpan = HandPanGenerator(
        strike_damping=0.5
    ).render(chords, key_g, dur)

    # Low breathy flute representing the summer breeze of the past
    flute = AltoFluteGenerator(
        breath_vibrato=False, note_density=0.4
    ).render(chords, key_g, dur)

    # Music box-like kalimba representing memory fragments
    kalimba = KalimbaGenerator(
        pop_intensity=0.6, note_density=0.5
    ).render(chords, key_g, dur)

    tracks = {
        "handpan": handpan,
        "alto_flute": flute,
        "kalimba": kalimba,
    }
    inst = {
        "handpan": HANDPAN,
        "alto_flute": ALTO_FLUTE,
        "kalimba": KALIMBA,
    }
    _export(tracks, OUT / "04_Taiyo_no_Toshi.mid", 55, inst, key_g)


# =====================================================================
# V. 赤い液体の高貴 (Nobility of the Red Liquid) — 46 BPM — D Kumoi
# =====================================================================
def produce_red_liquid():
    print("  V. 赤い液体の高貴 (Nobility of the Red Liquid) [Kumoi — 46 BPM — D]")
    key_d = types.Scale(root=2, mode=types.Mode.KUMOI)
    dur = 200.0
    chords = _chords(key_d, "i i i iv i i v i" * 5, dur)

    # Shimmering glass harp pad indicating high nobility
    glass = GlassHarpGenerator(
        friction_noise=0.3
    ).render(chords, key_d, dur)

    # Lyrical floating erhu bows
    erhu = ErhuGenerator(
        glide_probability=0.35, vibrato_depth=0.3
    ).render(chords, key_d, dur)

    # Seashore sweeps fading out as Roman drifts into unconsciousness
    wind = WindMachineGenerator(
        effect_type="wind", intensity_curve="fade", note_density=0.85
    ).render(chords, key_d, dur)

    tracks = {
        "glass_harp": glass,
        "erhu": erhu,
        "wind_machine": wind,
    }
    inst = {
        "glass_harp": GLASS_HARP,
        "erhu": ERHU,
        "wind_machine": WIND_MACHINE,
    }
    _export(tracks, OUT / "05_Akai_Ekitai_no_Koki.mid", 46, inst, key_d)


def main():
    print("\n" + "=" * 60)
    print("   吸血鬼・V — EMPIRE V SOUNDTRACK")
    print("   Evocative Reading Companionship (Japanese Ambient)")
    print("=" * 60 + "\n")

    produce_green_arrow()
    produce_red_room()
    produce_tongue_awakening()
    produce_sunny_city()
    produce_red_liquid()

    print("\n" + "=" * 60)
    print("   吸血鬼・V — COMPLETE.")
    print(f"   MIDI output saved to: {OUT.absolute()}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
