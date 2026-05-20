# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_edo_tragic.py — 浮世悲歌 (Ukiyo Elegy)
A tragic 3-track album inspired by Hiroshige's ukiyo-e landscapes.

Each track is a virtuoso composition built around Japanese pentatonic scales,
featuring koto, shakuhachi, shamisen, strings, and taiko.

  I.   霧の渡り (Fog Crossing)       — Mist over Tokaido road, 62 BPM, D Hirajoshi
  II.  波の墓 (Grave of Waves)       — The great wave consumes, 78 BPM, D Kumoi
  III. 暮れ残る (Dusk Remains)       — Fading light on Edo, 54 BPM, D Japanese

Virtuoso settings: high density, wide ranges, motivic development,
ornamentation, dramatic arcs with tension_release and epic shapes.
"""

from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


def _chords(progression: str, key: types.Scale, duration: float):
    parts = progression.split()
    bpc = duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        c = key.parse_roman(p)
        c.start = i * bpc
        c.duration = bpc
        chords.append(c)
    return chords


def _master(raw: dict, bpm: float, lufs: float = -12.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "koto": 1.0, "shakuhachi": 0.95, "shamisen": 1.05,
        "strings": 0.7, "taiko": 0.85, "drone": 0.4,
        "arp": 0.6, "ostinato": 0.55, "bass": 0.9,
    })
    mixed = desk.apply_mixing(raw, [("Dynamics", 400, [])], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# =====================================================================
# Track I — 霧の渡り (Fog Crossing)
# 62 BPM, D Hirajoshi [0,2,3,7,8], ~4:30
# A lone traveler on the Tokaido road, fog obscuring the path.
# Koto melody emerges from drone like a figure from mist.
# =====================================================================
def produce_fog_crossing():
    """Sparse opening → desperate wandering → acceptance in fog."""
    print("  I. 霧の渡り (Fog Crossing) [Hirajoshi — 62 BPM — D]")

    key = types.Scale(root=2, mode=types.Mode.HIROJOSHI)
    dur = 168.0  # ~4:30 at 62 BPM

    # Three-section progression: sparse → tense → dissolving
    prog_a = ("i i iv v " * 4).strip()     # 16 chords — static, frozen
    prog_b = ("i iv v i iv v i v " * 3).strip()    # 24 chords — searching
    prog_c = ("i iv i iv i i iv i " * 2).strip()   # 16 chords — dissolving
    prog = (prog_a + " " + prog_b + " " + prog_c).strip()
    chords_full = _chords(prog, key, dur)

    n_a = len(prog_a.split())
    n_b = len(prog_b.split())
    bpc = dur / len(prog.split())
    split_1 = n_a * bpc
    split_2 = (n_a + n_b) * bpc

    chords_a = [c for c in chords_full if c.start < split_1]
    chords_b = [c for c in chords_full if split_1 <= c.start < split_2]
    chords_c = [c for c in chords_full if c.start >= split_2]
    dur_a = split_1
    dur_b = split_2 - split_1
    dur_c = dur - split_2

    # 1. Koto — virtuosic melody with three emotional phases
    koto_a = MelodyGenerator(
        GeneratorParams(density=0.15, leap_probability=0.1),
        drama_shape="crescendo", drama_peak=0.35,
        motif_probability=0.9, motif_variation="any",
        harmony_note_probability=0.95,
        note_range_low=62, note_range_high=79,
        phrase_length=16.0,
        register_smoothness=0.95,
        steps_probability=0.92,
        first_note="tonic",
    ).render(chords_a, key, dur_a)

    koto_b = MelodyGenerator(
        GeneratorParams(density=0.72, leap_probability=0.55),
        drama_shape="dramatic", drama_peak=0.85,
        motif_probability=0.85, motif_variation="any",
        ornament_probability=0.5,
        harmony_note_probability=0.4,
        note_range_low=57, note_range_high=91,
        syncopation=0.65, rhythm_variety=0.85,
        after_leap="step_any",
        random_movement=0.5,
        phrase_length=4.0,
    ).render(chords_b, key, dur_b)

    koto_c = MelodyGenerator(
        GeneratorParams(density=0.2, leap_probability=0.05),
        drama_shape="crescendo", drama_peak=0.25,
        motif_probability=0.95, motif_variation="fragment",
        harmony_note_probability=0.92,
        note_range_low=60, note_range_high=72,
        phrase_length=20.0,
        register_smoothness=0.98,
        steps_probability=0.95,
        first_note="tonic",
    ).render(chords_c, key, dur_c)

    for n in koto_b:
        n.start += split_1
    for n in koto_c:
        n.start += split_2
    koto = koto_a + koto_b + koto_c

    # 2. Shakuhachi — breath-like phrases, sparse and mournful
    shakuhachi_a = MelodyGenerator(
        GeneratorParams(density=0.08, leap_probability=0.05),
        drama_shape="crescendo", drama_peak=0.3,
        harmony_note_probability=0.95,
        note_range_low=55, note_range_high=70,
        phrase_length=24.0,
        register_smoothness=0.98,
        steps_probability=0.95,
        first_note="tonic",
    ).render(chords_a, key, dur_a)

    shakuhachi_b = MelodyGenerator(
        GeneratorParams(density=0.45, leap_probability=0.4),
        drama_shape="tension_release", drama_peak=0.7,
        harmony_note_probability=0.5,
        ornament_probability=0.4,
        note_range_low=50, note_range_high=79,
        syncopation=0.5, rhythm_variety=0.7,
        phrase_length=6.0,
        motif_probability=0.7, motif_variation="any",
    ).render(chords_b, key, dur_b)

    shakuhachi_c = MelodyGenerator(
        GeneratorParams(density=0.06, leap_probability=0.02),
        drama_shape="crescendo", drama_peak=0.15,
        harmony_note_probability=0.98,
        note_range_low=55, note_range_high=67,
        phrase_length=32.0,
        register_smoothness=0.99,
        steps_probability=0.98,
        first_note="tonic",
    ).render(chords_c, key, dur_c)

    for n in shakuhachi_b:
        n.start += split_1
    for n in shakuhachi_c:
        n.start += split_2
    shakuhachi = shakuhachi_a + shakuhachi_b + shakuhachi_c

    # 3. Strings — sustained, building through sections
    strings_a = StringsEnsembleGenerator(
        GeneratorParams(density=0.15, key_range_low=48, key_range_high=67),
        articulation="sustained", divisi=2,
        dynamic_curve="crescendo",
    ).render(chords_a, key, dur_a)

    strings_b = StringsEnsembleGenerator(
        GeneratorParams(density=0.6, key_range_low=41, key_range_high=79),
        articulation="sustained", divisi=4,
        dynamic_curve="swell",
    ).render(chords_b, key, dur_b)

    strings_c = StringsEnsembleGenerator(
        GeneratorParams(density=0.25, key_range_low=48, key_range_high=72),
        articulation="sustained", divisi=3,
        dynamic_curve="crescendo",
    ).render(chords_c, key, dur_c)

    for n in strings_b:
        n.start += split_1
    for n in strings_c:
        n.start += split_2
    strings = strings_a + strings_b + strings_c

    # 4. Drone — sub-bass D pedal throughout
    drone = DroneGenerator(
        GeneratorParams(density=0.1),
        variant="tonic",
    ).render(chords_full, key, dur)

    # 5. Taiko — minimal in A, thunderous in B, fading in C
    taiko_a = ElectronicDrumsGenerator(
        GeneratorParams(density=0.1),
        kit="808", pattern="minimal",
    ).render(chords_a, key, dur_a)

    taiko_b = ElectronicDrumsGenerator(
        GeneratorParams(density=0.65),
        kit="909", pattern="four_on_floor",
        sidechain=True,
    ).render(chords_b, key, dur_b)

    taiko_c = ElectronicDrumsGenerator(
        GeneratorParams(density=0.15),
        kit="808", pattern="minimal",
    ).render(chords_c, key, dur_c)

    for n in taiko_b:
        n.start += split_1
    for n in taiko_c:
        n.start += split_2
    taiko = taiko_a + taiko_b + taiko_c

    raw = {"koto": koto, "shakuhachi": shakuhachi, "strings": strings,
           "drone": drone, "taiko": taiko}
    mastered, pan = _master(raw, 62.0, lufs=-16.0)
    return mastered, pan, 62.0, key, {
        "koto": 107,       # Koto
        "shakuhachi": 77,  # Shakuhachi
        "strings": 49,     # String Ensemble 1
        "drone": 89,       # New Age Pad
        "taiko": 0,        # Channel 10
    }


# =====================================================================
# Track II — 波の墓 (Grave of Waves)
# 78 BPM, D Kumoi [0,2,5,7,10], ~5:00
# The great wave — nature's fury and the fishermen's doom.
# Building from uneasy calm to catastrophic climax, then silence.
# =====================================================================
def produce_grave_of_waves():
    """Calm sea → storm rising → the wave → aftermath silence."""
    print("  II. 波の墓 (Grave of Waves) [Kumoi — 78 BPM — D]")

    key = types.Scale(root=2, mode=types.Mode.KUMOI)
    dur = 192.0  # ~5:00 at 78 BPM

    # Four-section: calm → storm building → the wave → drowned silence
    prog_a = ("i iv v i " * 4).strip()          # 16 — uneasy calm
    prog_b = ("i iv v i iv v i v " * 3).strip()  # 24 — storm gathering
    prog_c = ("i v iv v i v iv v " * 4).strip()  # 32 — THE WAVE
    prog_d = ("i i iv i " * 2).strip()            # 8 — drowned
    prog = (prog_a + " " + prog_b + " " + prog_c + " " + prog_d).strip()
    chords_full = _chords(prog, key, dur)

    bpc = dur / len(prog.split())
    n_a = len(prog_a.split())
    n_b = len(prog_b.split())
    n_c = len(prog_c.split())
    s1 = n_a * bpc
    s2 = (n_a + n_b) * bpc
    s3 = (n_a + n_b + n_c) * bpc

    chords = [
        [c for c in chords_full if c.start < s1],
        [c for c in chords_full if s1 <= c.start < s2],
        [c for c in chords_full if s2 <= c.start < s3],
        [c for c in chords_full if c.start >= s3],
    ]
    durs = [s1, s2 - s1, s3 - s2, dur - s3]
    offsets = [0, s1, s2, s3]

    # 1. Shamisen — the storyteller's voice, escalating desperation
    shamisen_params = [
        # Calm: measured, traditional
        (GeneratorParams(density=0.25, leap_probability=0.15),
         "crescendo", 0.3, 0.85, "any", 0.1, 0.92, 57, 74, 12.0, 0.95, 0.9),
        # Storm building: increasing urgency
        (GeneratorParams(density=0.7, leap_probability=0.5),
         "dramatic", 0.75, 0.8, "any", 0.45, 0.5, 50, 84, 4.0, 0.8, 0.7),
        # THE WAVE: maximum virtuosity, cascading
        (GeneratorParams(density=0.92, leap_probability=0.7),
         "epic", 0.95, 0.75, "any", 0.65, 0.3, 45, 96, 2.0, 0.5, 0.5),
        # Drowned: single fading notes
        (GeneratorParams(density=0.05, leap_probability=0.02),
         "crescendo", 0.1, 0.98, "fragment", 0.0, 0.98, 57, 67, 24.0, 0.99, 0.98),
    ]

    shamisen = []
    for i, (gp, ds, dp, mp, mv, op, hnp, lo, hi, pl, rs, sp) in enumerate(shamisen_params):
        section = MelodyGenerator(
            gp,
            drama_shape=ds, drama_peak=dp,
            motif_probability=mp, motif_variation=mv,
            ornament_probability=op,
            harmony_note_probability=hnp,
            note_range_low=lo, note_range_high=hi,
            phrase_length=pl,
            register_smoothness=rs,
            steps_probability=sp,
            syncopation=0.6 if i == 2 else 0.3,
            rhythm_variety=0.8 if i >= 1 else 0.4,
            after_leap="step_any" if i >= 1 else "step_opposite",
            random_movement=0.45 if i >= 1 else 0.2,
            first_note="tonic",
        ).render(chords[i], key, durs[i])
        for n in section:
            n.start += offsets[i]
        shamisen.extend(section)

    # 2. Koto — arpeggiated waves, building from gentle to violent
    arp_params = [
        (GeneratorParams(density=0.3), "up", 1.0, "open", 1),
        (GeneratorParams(density=0.6), "up_down", 0.5, "closed", 2),
        (GeneratorParams(density=0.9), "alberti", 0.25, "spread", 3),
        (GeneratorParams(density=0.1), "up", 2.0, "open", 1),
    ]
    arp = []
    for i, (gp, pat, nd, voi, oct) in enumerate(arp_params):
        section = ArpeggiatorGenerator(
            gp, pattern=pat, note_duration=nd, voicing=voi, octaves=oct,
        ).render(chords[i], key, durs[i])
        for n in section:
            n.start += offsets[i]
        arp.extend(section)

    # 3. Strings — ocean swell
    str_params = [
        (GeneratorParams(density=0.2, key_range_low=48, key_range_high=67), "sustained", 2, "crescendo"),
        (GeneratorParams(density=0.5, key_range_low=43, key_range_high=74), "sustained", 4, "swell"),
        (GeneratorParams(density=0.85, key_range_low=36, key_range_high=84), "tremolo", 6, "swell"),
        (GeneratorParams(density=0.1, key_range_low=48, key_range_high=65), "sustained", 2, "crescendo"),
    ]
    strings = []
    for i, (gp, art, div, dc) in enumerate(str_params):
        section = StringsEnsembleGenerator(
            gp, articulation=art, divisi=div, dynamic_curve=dc,
        ).render(chords[i], key, durs[i])
        for n in section:
            n.start += offsets[i]
        strings.extend(section)

    # 4. Bass — deep ocean current
    bass = BassGenerator(
        GeneratorParams(density=0.45, key_range_low=28, key_range_high=43),
        style="root_fifth_octave",
    ).render(chords_full, key, dur)

    # 5. Taiko — waves of drums
    taiko_params = [
        (GeneratorParams(density=0.08), "808", "minimal"),
        (GeneratorParams(density=0.5), "909", "four_on_floor"),
        (GeneratorParams(density=0.9), "909", "four_on_floor"),
        (GeneratorParams(density=0.03), "808", "minimal"),
    ]
    taiko = []
    for i, (gp, kit, pat) in enumerate(taiko_params):
        section = ElectronicDrumsGenerator(
            gp, kit=kit, pattern=pat, sidechain=(i >= 1),
        ).render(chords[i], key, durs[i])
        for n in section:
            n.start += offsets[i]
        taiko.extend(section)

    raw = {"shamisen": shamisen, "koto": arp, "strings": strings,
           "bass": bass, "taiko": taiko}
    mastered, pan = _master(raw, 78.0, lufs=-9.0)
    return mastered, pan, 78.0, key, {
        "shamisen": 106,  # Shamisen
        "koto": 107,      # Koto
        "strings": 48,    # String Ensemble 2
        "bass": 36,       # Fretless Bass
        "taiko": 0,
    }


# =====================================================================
# Track III — 暮れ残る (Dusk Remains)
# 54 BPM, D Japanese [0,1,5,7,8], ~6:00
# The last light fades on Edo. A mother's lullaby for a child
# who will not return. The most tragic, the most sparse.
# =====================================================================
def produce_dusk_remains():
    """Lullaby — grief — hollow acceptance — silence."""
    print("  III. 暮れ残る (Dusk Remains) [Japanese — 54 BPM — D]")

    key = types.Scale(root=2, mode=types.Mode.JAPANESE)
    dur = 200.0  # ~6:00 at 54 BPM

    prog = ("i iv v i " * 8).strip()
    chords = _chords(prog, key, dur)

    # 1. Shakuhachi — the lullaby voice, intimate and heartbroken
    shakuhachi = MelodyGenerator(
        GeneratorParams(density=0.3, leap_probability=0.2),
        drama_shape="tension_release", drama_peak=0.7,
        motif_probability=0.95, motif_variation="any",
        ornament_probability=0.35,
        harmony_note_probability=0.7,
        note_range_low=55, note_range_high=79,
        phrase_length=8.0,
        register_smoothness=0.92,
        steps_probability=0.88,
        syncopation=0.25,
        rhythm_variety=0.5,
        after_leap="step_opposite",
        first_note="tonic",
        last_note="last_chord_root",
    ).render(chords, key, dur)

    # 2. Koto — delicate, sparse accompaniment, like raindrops on a lantern
    koto = MelodyGenerator(
        GeneratorParams(density=0.15, leap_probability=0.1),
        drama_shape="crescendo", drama_peak=0.4,
        motif_probability=0.9, motif_variation="transpose",
        harmony_note_probability=0.95,
        note_range_low=60, note_range_high=84,
        phrase_length=12.0,
        register_smoothness=0.95,
        steps_probability=0.9,
        first_note="scale",
    ).render(chords, key, dur)

    # 3. Strings — sustained grief, weeping quality
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.35, key_range_low=41, key_range_high=72),
        articulation="sustained", divisi=4,
        dynamic_curve="crescendo",
    ).render(chords, key, dur)

    # 4. Drone — deep hum of twilight
    drone = DroneGenerator(
        GeneratorParams(density=0.08),
        variant="tonic",
    ).render(chords, key, dur)

    # 5. Ostinato — slow repeating pattern like a prayer wheel
    ostinato = OstinatoGenerator(
        GeneratorParams(density=0.2, key_range_low=48, key_range_high=60),
        pattern="1-3-5-3",
        repeat_notes=2,
    ).render(chords, key, dur)

    raw = {"shakuhachi": shakuhachi, "koto": koto, "strings": strings,
           "drone": drone, "ostinato": ostinato}
    mastered, pan = _master(raw, 54.0, lufs=-18.0)
    return mastered, pan, 54.0, key, {
        "shakuhachi": 77,   # Shakuhachi
        "koto": 107,        # Koto
        "strings": 49,      # String Ensemble 1
        "drone": 89,        # New Age Pad
        "ostinato": 46,     # Harp (as koto accompaniment)
    }


# =====================================================================
# Main
# =====================================================================
def main():
    album_dir = Path("output/album_edo_tragic")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   浮世悲歌 (UKIYO ELEGY)")
    print("   Tragic Edo Album — Hiroshige-inspired — 3 tracks")
    print("=" * 60 + "\n")

    tracks = [
        ("01_Fog_Crossing_霧の渡り",     produce_fog_crossing),
        ("02_Grave_of_Waves_波の墓",     produce_grave_of_waves),
        ("03_Dusk_Remains_暮れ残る",     produce_dusk_remains),
    ]

    for name, producer in tracks:
        print(f"\n--- {name} ---")
        mastered, pan, bpm, key, instr = producer()
        export_multitrack_midi(
            mastered,
            str(album_dir / f"{name}.mid"),
            bpm=bpm,
            key=key,
            cc_events=pan,
            instruments=instr,
        )
        print(f"    -> {name}.mid  ({bpm} BPM, {len(mastered)} tracks)")
        inst_names = {
            107: "Koto", 77: "Shakuhachi", 106: "Shamisen",
            49: "Strings Ens 1", 48: "Strings Ens 2", 89: "New Age Pad",
            36: "Fretless Bass", 46: "Harp", 0: "Drums",
        }
        for track_name, program in instr.items():
            gm_name = inst_names.get(program, f"GM#{program}")
            note_count = sum(len(v) for k, v in mastered.items() if k == track_name)
            print(f"       {track_name:16s}  {gm_name:20s}  {note_count:>4d} notes")

    print("\n" + "=" * 60)
    print(f"   浮世悲歌 — COMPLETE. Files in: {album_dir}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
