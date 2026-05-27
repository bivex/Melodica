# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_exotic_civilizations.py — Three Exotic Scales, Three Lost Civilizations.

Each track uses one of the most exotic scales in music history:

  I.   Zoroaster's Fire     — Persian [0,1,4,5,6,8,11], 3000 years old
                           Ancient fire temples of Persepolis.
  II.  Hagia Echoes         — Byzantine [0,1,4,5,7,8,11], Eastern Orthodox hymns
                           Echoes through the dome of Hagia Sophia.
  III. Siq of Maqam         — Arabic_Sikah [0,1.5,3.5,5,7,8.5,10.5], microtonal
                           The narrow gorge into Petra, quarter-tone maqam.

Instruments chosen for cultural resonance:
  Persian:    Santur (dulcimer), Ney (flute), Duduk, Strings, Frame Drum
  Byzantine:  Choir, PSaltery, Strings, Organ drone, Hand drum
  Arabic:     Oud, Nay (flute), Qanun (zither), Strings, Darbuka
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
        "melody": 1.0, "flute": 0.9, "strings": 0.7,
        "drums": 0.85, "drone": 0.4, "arp": 0.6,
        "bass": 0.95, "ostinato": 0.55, "choir": 0.8,
        "zither": 0.65,
    })
    mixed = desk.apply_mixing(raw, [("Dynamics", 400, [])], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# =====================================================================
# Track I — Zoroaster's Fire
# 68 BPM, E Persian [0,1,4,5,6,8,11], ~4:30
# Ancient fire ritual. The flame reveals, the flame consumes.
# Persian scale: three semitone clusters create perpetual tension.
# =====================================================================
def produce_zoroasters_fire():
    """Fire ritual: ignition → sacred dance → transcendence."""
    print("  I. Zoroaster's Fire [Persian — 68 BPM — E]")

    key = types.Scale(root=4, mode=types.Mode.PERSIAN)  # E Persian
    dur = 180.0

    # Three phases: kindling → sacred dance → eternal flame
    prog_a = ("i i iv i " * 4).strip()      # 16 — stillness
    prog_b = ("i iv v i iv v i v " * 3).strip()  # 24 — ritual dance
    prog_c = ("i i i i " * 3).strip()       # 12 — eternal drone
    prog = (prog_a + " " + prog_b + " " + prog_c).strip()
    chords_full = _chords(prog, key, dur)

    bpc = dur / len(prog.split())
    n_a = len(prog_a.split())
    n_b = len(prog_b.split())
    s1 = n_a * bpc
    s2 = (n_a + n_b) * bpc

    chords_a = [c for c in chords_full if c.start < s1]
    chords_b = [c for c in chords_full if s1 <= c.start < s2]
    chords_c = [c for c in chords_full if c.start >= s2]
    dur_a, dur_b, dur_c = s1, s2 - s1, dur - s2

    # 1. Santur (dulcimer) — hammered zither, the ritual voice
    melody_a = MelodyGenerator(
        GeneratorParams(density=0.2, leap_probability=0.15),
        drama_shape="crescendo", drama_peak=0.4,
        motif_probability=0.9, motif_variation="any",
        harmony_note_probability=0.85,
        note_range_low=64, note_range_high=79,
        phrase_length=12.0, register_smoothness=0.93,
        steps_probability=0.85, first_note="tonic",
    ).render(chords_a, key, dur_a)

    melody_b = MelodyGenerator(
        GeneratorParams(density=0.75, leap_probability=0.55),
        drama_shape="dramatic", drama_peak=0.8,
        motif_probability=0.85, motif_variation="any",
        ornament_probability=0.5, harmony_note_probability=0.4,
        note_range_low=57, note_range_high=91,
        syncopation=0.6, rhythm_variety=0.8,
        after_leap="step_any", random_movement=0.45,
        phrase_length=4.0,
    ).render(chords_b, key, dur_b)

    melody_c = MelodyGenerator(
        GeneratorParams(density=0.12, leap_probability=0.05),
        drama_shape="crescendo", drama_peak=0.2,
        motif_probability=0.95, motif_variation="fragment",
        harmony_note_probability=0.95,
        note_range_low=64, note_range_high=76,
        phrase_length=24.0, register_smoothness=0.97,
        steps_probability=0.95, first_note="tonic",
    ).render(chords_c, key, dur_c)

    for n in melody_b:
        n.start += s1
    for n in melody_c:
        n.start += s2
    melody = melody_a + melody_b + melody_c

    # 2. Ney (reed flute) — breath of the fire priest
    flute_a = MelodyGenerator(
        GeneratorParams(density=0.1, leap_probability=0.08),
        drama_shape="crescendo", drama_peak=0.25,
        harmony_note_probability=0.95,
        note_range_low=57, note_range_high=72,
        phrase_length=20.0, register_smoothness=0.97,
        steps_probability=0.93, first_note="tonic",
        motif_probability=0.8, motif_variation="transpose",
    ).render(chords_a, key, dur_a)

    flute_b = MelodyGenerator(
        GeneratorParams(density=0.55, leap_probability=0.45),
        drama_shape="tension_release", drama_peak=0.7,
        harmony_note_probability=0.5, ornament_probability=0.4,
        note_range_low=52, note_range_high=79,
        syncopation=0.5, rhythm_variety=0.7,
        phrase_length=5.0, motif_probability=0.75, motif_variation="any",
    ).render(chords_b, key, dur_b)

    flute_c = MelodyGenerator(
        GeneratorParams(density=0.06, leap_probability=0.02),
        drama_shape="crescendo", drama_peak=0.12,
        harmony_note_probability=0.98,
        note_range_low=57, note_range_high=69,
        phrase_length=32.0, register_smoothness=0.99,
        steps_probability=0.97, first_note="tonic",
    ).render(chords_c, key, dur_c)

    for n in flute_b:
        n.start += s1
    for n in flute_c:
        n.start += s2
    flute = flute_a + flute_b + flute_c

    # 3. Strings — ancient ensemble
    strings_a = StringsEnsembleGenerator(
        GeneratorParams(density=0.15, key_range_low=48, key_range_high=67),
        articulation="sustained", divisi=2, dynamic_curve="crescendo",
    ).render(chords_a, key, dur_a)

    strings_b = StringsEnsembleGenerator(
        GeneratorParams(density=0.55, key_range_low=41, key_range_high=79),
        articulation="sustained", divisi=4, dynamic_curve="swell",
    ).render(chords_b, key, dur_b)

    strings_c = StringsEnsembleGenerator(
        GeneratorParams(density=0.2, key_range_low=48, key_range_high=72),
        articulation="sustained", divisi=2, dynamic_curve="crescendo",
    ).render(chords_c, key, dur_c)

    for n in strings_b:
        n.start += s1
    for n in strings_c:
        n.start += s2
    strings = strings_a + strings_b + strings_c

    # 4. Drone — eternal flame hum
    drone = DroneGenerator(
        GeneratorParams(density=0.08), variant="tonic",
    ).render(chords_full, key, dur)

    # 5. Frame drum — daf-like ritual rhythm
    drums_a = ElectronicDrumsGenerator(
        GeneratorParams(density=0.08), kit="808", pattern="minimal",
    ).render(chords_a, key, dur_a)

    drums_b = ElectronicDrumsGenerator(
        GeneratorParams(density=0.6), kit="909", pattern="four_on_floor", sidechain=True,
    ).render(chords_b, key, dur_b)

    drums_c = ElectronicDrumsGenerator(
        GeneratorParams(density=0.05), kit="808", pattern="minimal",
    ).render(chords_c, key, dur_c)

    for n in drums_b:
        n.start += s1
    for n in drums_c:
        n.start += s2
    drums = drums_a + drums_b + drums_c

    raw = {"melody": melody, "flute": flute, "strings": strings,
           "drone": drone, "drums": drums}
    mastered, pan = _master(raw, 68.0, lufs=-14.0)
    return mastered, pan, 68.0, key, {
        "melody": 15,   # Dulcimer (Santur)
        "flute": 73,    # Flute (Ney)
        "strings": 49,  # String Ensemble 1
        "drone": 89,    # New Age Pad
        "drums": 0,
    }


# =====================================================================
# Track II — Hagia Echoes
# 56 BPM, D Byzantine [0,1,4,5,7,8,11], ~5:30
# Orthodox chant echoing through Hagia Sophia's dome.
# Byzantine scale: the double-augmented second creates sacred gravity.
# =====================================================================
def produce_hagia_echoes():
    """Sacred space: chant → antiphonal response → divine silence."""
    print("  II. Hagia Echoes [Byzantine — 56 BPM — D]")

    key = types.Scale(root=2, mode=types.Mode.BYZANTINE)  # D Byzantine
    dur = 200.0

    prog = ("i iv v i " * 8).strip()
    chords = _chords(prog, key, dur)

    # 1. Choir — Orthodox chant melody
    choir = MelodyGenerator(
        GeneratorParams(density=0.3, leap_probability=0.2),
        drama_shape="epic", drama_peak=0.65,
        motif_probability=0.9, motif_variation="any",
        ornament_probability=0.2, harmony_note_probability=0.75,
        note_range_low=55, note_range_high=77,
        phrase_length=10.0, register_smoothness=0.92,
        steps_probability=0.85, syncopation=0.15,
        rhythm_variety=0.4, first_note="tonic",
        last_note="last_chord_root",
    ).render(chords, key, dur)

    # 2. Psaltery — angelic zither arpeggios
    zither = ArpeggiatorGenerator(
        GeneratorParams(density=0.35),
        pattern="up", note_duration=0.75,
        voicing="open", octaves=2,
    ).render(chords, key, dur)

    # 3. Strings — cathedral resonance
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.4, key_range_low=41, key_range_high=72),
        articulation="sustained", divisi=4, dynamic_curve="crescendo",
    ).render(chords, key, dur)

    # 4. Organ drone — the breath of God through pipes
    drone = DroneGenerator(
        GeneratorParams(density=0.06), variant="tonic",
    ).render(chords, key, dur)

    # 5. Hand drum — deep, sparse cathedral heartbeats
    drums = ElectronicDrumsGenerator(
        GeneratorParams(density=0.15), kit="808", pattern="minimal",
    ).render(chords, key, dur)

    raw = {"choir": choir, "zither": zither, "strings": strings,
           "drone": drone, "drums": drums}
    mastered, pan = _master(raw, 56.0, lufs=-17.0)
    return mastered, pan, 56.0, key, {
        "choir": 52,    # Choir Aahs
        "zither": 15,   # Dulcimer (Psaltery)
        "strings": 48,  # String Ensemble 2
        "drone": 19,    # Church Organ
        "drums": 0,
    }


# =====================================================================
# Track III — Siq of Maqam
# 72 BPM, D Arabic_Sikah [0,1.5,3.5,5,7,8.5,10.5], ~4:00
# Walking through the narrow Siq gorge into Petra.
# Arabic Sikah: microtonal quarter-tones — neither East nor West.
# The gorge whispers in intervals that don't exist on a piano.
# =====================================================================
def produce_siq_of_maqam():
    """Desert canyon: shadows → maqam dance → vanishing into sand."""
    print("  III. Siq of Maqam [Arabic Sikah — 72 BPM — D]")

    key = types.Scale(root=2, mode=types.Mode.ARABIC_SIKAH)  # D Sikah
    dur = 168.0

    # Two sections: shadow gorge → maqam dance
    prog_a = ("i i iv i " * 4).strip()   # 16 — canyon shadows
    prog_b = ("i iv v i iv v i v " * 3).strip()  # 24 — maqam dance
    prog = (prog_a + " " + prog_b).strip()
    chords_full = _chords(prog, key, dur)

    bpc = dur / len(prog.split())
    n_a = len(prog_a.split())
    s1 = n_a * bpc

    chords_a = [c for c in chords_full if c.start < s1]
    chords_b = [c for c in chords_full if c.start >= s1]
    dur_a, dur_b = s1, dur - s1

    # 1. Oud — the desert lute, master of microtonal expression
    melody_a = MelodyGenerator(
        GeneratorParams(density=0.2, leap_probability=0.12),
        drama_shape="crescendo", drama_peak=0.35,
        motif_probability=0.9, motif_variation="any",
        harmony_note_probability=0.88,
        note_range_low=57, note_range_high=74,
        phrase_length=14.0, register_smoothness=0.94,
        steps_probability=0.9, first_note="tonic",
    ).render(chords_a, key, dur_a)

    melody_b = MelodyGenerator(
        GeneratorParams(density=0.7, leap_probability=0.5),
        drama_shape="dramatic", drama_peak=0.8,
        motif_probability=0.85, motif_variation="any",
        ornament_probability=0.45, harmony_note_probability=0.45,
        note_range_low=52, note_range_high=86,
        syncopation=0.55, rhythm_variety=0.75,
        after_leap="step_any", random_movement=0.4,
        phrase_length=4.0,
    ).render(chords_b, key, dur_b)

    for n in melody_b:
        n.start += s1
    melody = melody_a + melody_b

    # 2. Nay — desert reed flute, haunting
    flute_a = MelodyGenerator(
        GeneratorParams(density=0.08, leap_probability=0.05),
        drama_shape="crescendo", drama_peak=0.2,
        harmony_note_probability=0.95,
        note_range_low=55, note_range_high=70,
        phrase_length=24.0, register_smoothness=0.98,
        steps_probability=0.95, first_note="tonic",
        motif_probability=0.7, motif_variation="transpose",
    ).render(chords_a, key, dur_a)

    flute_b = MelodyGenerator(
        GeneratorParams(density=0.5, leap_probability=0.4),
        drama_shape="tension_release", drama_peak=0.65,
        harmony_note_probability=0.5, ornament_probability=0.35,
        note_range_low=50, note_range_high=77,
        syncopation=0.45, rhythm_variety=0.6,
        phrase_length=6.0, motif_probability=0.7, motif_variation="any",
    ).render(chords_b, key, dur_b)

    for n in flute_b:
        n.start += s1
    flute = flute_a + flute_b

    # 3. Qanun (zither) — rapid plucked arpeggios
    arp_a = ArpeggiatorGenerator(
        GeneratorParams(density=0.2), pattern="up",
        note_duration=1.0, voicing="open", octaves=1,
    ).render(chords_a, key, dur_a)

    arp_b = ArpeggiatorGenerator(
        GeneratorParams(density=0.7), pattern="up_down",
        note_duration=0.25, voicing="closed", octaves=2,
    ).render(chords_b, key, dur_b)

    for n in arp_b:
        n.start += s1
    arp = arp_a + arp_b

    # 4. Strings — desert wind
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.35, key_range_low=43, key_range_high=72),
        articulation="sustained", divisi=3, dynamic_curve="crescendo",
    ).render(chords_full, key, dur)

    # 5. Darbuka — hand drum patterns
    drums_a = ElectronicDrumsGenerator(
        GeneratorParams(density=0.1), kit="808", pattern="minimal",
    ).render(chords_a, key, dur_a)

    drums_b = ElectronicDrumsGenerator(
        GeneratorParams(density=0.6), kit="909", pattern="four_on_floor", sidechain=True,
    ).render(chords_b, key, dur_b)

    for n in drums_b:
        n.start += s1
    drums = drums_a + drums_b

    raw = {"melody": melody, "flute": flute, "arp": arp,
           "strings": strings, "drums": drums}
    mastered, pan = _master(raw, 72.0, lufs=-11.0)
    return mastered, pan, 72.0, key, {
        "melody": 24,   # Acoustic Guitar (Nylon) as Oud
        "flute": 73,    # Flute (Nay)
        "arp": 15,      # Dulcimer (Qanun)
        "strings": 45,  # Pizzicato Strings
        "drums": 0,
    }


# =====================================================================
# Main
# =====================================================================
def main():
    album_dir = Path("output/album_exotic_civilizations")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   EXOTIC CIVILIZATIONS")
    print("   3 tracks x 3 ancient scales")
    print("=" * 60 + "\n")

    tracks = [
        ("01_Zoroasters_Fire",    produce_zoroasters_fire),
        ("02_Hagia_Echoes",       produce_hagia_echoes),
        ("03_Siq_of_Maqam",      produce_siq_of_maqam),
    ]

    for name, producer in tracks:
        print(f"\n--- {name} ---")
        mastered, pan, bpm, key, instr = producer()
        export_multitrack_midi(
            mastered,
            str(album_dir / f"{name}.mid"),
            bpm=bpm, key=key, cc_events=pan, instruments=instr,
        )
        inst_names = {
            15: "Dulcimer/Santur", 73: "Flute/Ney", 49: "Strings Ens 1",
            89: "New Age Pad", 52: "Choir Aahs", 48: "Strings Ens 2",
            19: "Church Organ", 24: "Oud/Nylon", 45: "Pizz Strings", 0: "Drums",
        }
        print(f"    -> {name}.mid  ({bpm} BPM, {len(mastered)} tracks)")
        for track_name, program in instr.items():
            gm_name = inst_names.get(program, f"GM#{program}")
            note_count = sum(len(v) for k, v in mastered.items() if k == track_name)
            print(f"       {track_name:16s}  {gm_name:20s}  {note_count:>4d} notes")

    print("\n" + "=" * 60)
    print(f"   EXOTIC CIVILIZATIONS — COMPLETE.")
    print(f"   Files in: {album_dir}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
