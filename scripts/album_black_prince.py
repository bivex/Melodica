# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_black_prince.py — ЧЕРНЫЙ ПРИНЦ (Black Prince)

Genre: Progressive Rock / Fusion
Scale: Hungarian Minor [0, 2, 3, 6, 7, 8, 11]
Характер: Тьма, благородство, техническая сложность, ломаные ритмы.

  I.   Coronation of Shadows (Коронация теней) — 144 BPM, 11/8.
  II.  Alchemy of Blood      (Алхимия крови)   — 96 BPM, 4/4 (Polyrhythmic).
  III. Mirror Throne         (Зеркальный трон) — 128 BPM, 7/4.
  IV.  Eclipse of the Heart  (Затмение сердца) — 66 BPM, 5/4.
  V.   The Final Stand       (Последняя битва) — 160 BPM, Dynamic Meter.
"""

import random
import math
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.composer.articulations import ArticulationEngine

# KEY: E Hungarian Minor (E-F#-G-A#-B-C-D#) - standard "heavy" key
KEY = types.Scale(root=4, mode=types.Mode.HUNGARIAN_MINOR)

# GM Programs
HAMMOND_ORGAN = 18
MOOG_LEAD = 81 # Square Lead
SAW_LEAD = 80  # Sawtooth Lead
GUITAR_OVERDRIVE = 29
GUITAR_DISTORTION = 30
BASS_PICK = 34
BASS_SYNTH = 38
CHOIR = 52
DRUMS = 0 # Percussion

random.seed(777)
OUT = Path("output/album_black_prince")
OUT.mkdir(parents=True, exist_ok=True)

_ART = ArticulationEngine()

# Instrument → articulation profile mapping
_ART_MAP = {
    "organ": "brass_legato",       # sustain, CC11 crescendo, pitch_bend slide-in
    "guitar_l": "strings_melody",  # sustain, vibrato_in, swell
    "guitar_r": "strings_melody",
    "lead": "flute",               # sustain, vibrato_in, swell (synth lead)
    "bass": "cello",               # sustain, vibrato_in, crescendo, pitch_bend slide
    "drums": "snare",              # staccato, short duration
    "pad": "strings_pad",          # fade_in, sustain pedal always
    "fx": "strings_pad",
}

def _art(tracks: dict, dur: float) -> dict:
    """Apply articulation profiles to all tracks."""
    return {
        name: _ART.apply(notes, _ART_MAP.get(name, "strings_melody"), dur)
        for name, notes in tracks.items()
    }

def _off(notes, offset):
    return [
        types.NoteInfo(pitch=n.pitch, start=n.start + offset,
                       duration=n.duration, velocity=n.velocity)
        for n in notes
    ]

def _master(raw: dict, bpm: float, lufs: float = -10.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "lead": 0.95, "organ": 0.8, "guitar_l": 0.75, "guitar_r": 0.75,
        "bass": 0.9, "drums": 1.1, "pad": 0.5, "fx": 0.6
    })
    # Prog rock needs more compression/limiting for energy
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)

def _export(tracks: dict, path: Path, bpm: float, instruments: dict):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=KEY,
                           instruments=instruments, cc_events=cc_events)

# =====================================================================
# I. Coronation of Shadows — 11/8 (3+3+3+2)
# =====================================================================
def produce_coronation():
    print("--- 01_Coronation_of_Shadows ---")
    bpm = 144
    bpc = 5.5 # 11/8 bar
    dur = 220.0
    
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*bpc), duration=bpc) for i in range(int(dur/bpc))]

    # Organ Intro Riff
    organ_riff = MelodyGenerator(
        GeneratorParams(density=0.7, complexity=0.9, velocity_range=(90, 115)),
        phrase_length=bpc, note_range_low=40, note_range_high=64,
        syncopation=0.4
    ).render(chords, KEY, dur)

    # Heavy Guitar Chords
    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.4, velocity_range=(100, 120)),
        pattern="power", note_duration=0.5
    ).render(chords, KEY, dur)

    # Lead Synth Solo (Virtuoso)
    lead = MelodyGenerator(
        GeneratorParams(density=0.8, complexity=1.0, velocity_range=(95, 127)),
        phrase_length=11.0, note_range_low=64, note_range_high=93,
        steps_probability=0.4, random_movement=0.2
    ).render(chords[8:], KEY, dur - 44.0)

    # Active Prog Bass
    bass = BassGenerator(
        GeneratorParams(density=0.6, velocity_range=(100, 120),
                        key_range_low=28, key_range_high=45),
        style="walking"
    ).render(chords, KEY, dur)

    # Drums: 11/8 pattern
    drum_notes = []
    for i in range(int(dur/bpc)):
        t = i * bpc
        drum_notes.append(types.NoteInfo(36, t, 0.5, 110)) # Kick
        drum_notes.append(types.NoteInfo(38, t + 1.5, 0.3, 100)) # Snare
        drum_notes.append(types.NoteInfo(38, t + 3.0, 0.3, 100)) # Snare
        drum_notes.append(types.NoteInfo(42, t + 4.5, 0.2, 90)) # Hihat

    tracks = _art({"organ": organ_riff, "guitar_l": guitar, "lead": _off(lead, 44.0), "bass": bass, "drums": drum_notes}, dur)
    inst = {"organ": HAMMOND_ORGAN, "guitar_l": GUITAR_DISTORTION, "lead": MOOG_LEAD, "bass": BASS_PICK, "drums": 36}
    _export(tracks, OUT / "01_Coronation.mid", bpm, inst)

# =====================================================================
# II. Alchemy of Blood — 96 BPM, 4/4
# =====================================================================
def produce_alchemy():
    print("--- 02_Alchemy_of_Blood ---")
    bpm = 96
    dur = 160.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=0, duration=dur)]

    # Polyrhythmic Synth (3 against 4)
    synth_poly = ArpeggiatorGenerator(
        GeneratorParams(density=0.6, velocity_range=(60, 85)),
        pattern="up_down", note_duration=0.333 # Triplet feel
    ).render(chords, KEY, dur)

    # Heavy Slow Guitar Riff
    guitar_riff = MelodyGenerator(
        GeneratorParams(density=0.3, complexity=0.6, velocity_range=(95, 120)),
        phrase_length=4.0, note_range_low=40, note_range_high=55
    ).render(chords, KEY, dur)

    # Melodic Bass
    bass = MelodyGenerator(
        GeneratorParams(density=0.45, complexity=0.7),
        note_range_low=28, note_range_high=45
    ).render(chords, KEY, dur)

    tracks = _art({"lead": synth_poly, "guitar_l": guitar_riff, "bass": bass}, dur)
    inst = {"lead": SAW_LEAD, "guitar_l": GUITAR_OVERDRIVE, "bass": BASS_SYNTH}
    _export(tracks, OUT / "02_Alchemy.mid", bpm, inst)

# =====================================================================
# III. Mirror Throne — 128 BPM, 7/4
# =====================================================================
def produce_throne():
    print("--- 03_Mirror_Throne ---")
    bpm = 128
    bpc = 7.0
    dur = 196.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*bpc), duration=bpc) for i in range(int(dur/bpc))]

    # Complex Arpeggio across keys and guitar
    keys_arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.7, velocity_range=(75, 100)),
        pattern="converge", note_duration=0.25
    ).render(chords, KEY, dur)

    # Guitar response
    guitar_arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.55, velocity_range=(85, 110)),
        pattern="diverge", note_duration=0.5
    ).render(chords, KEY, dur)

    # Bass Solo section (beat 112)
    bass_solo = MelodyGenerator(
        GeneratorParams(density=0.75, complexity=1.0, velocity_range=(100, 127)),
        note_range_low=33, note_range_high=57
    ).render(chords[16:20], KEY, 28.0)

    tracks = _art({"organ": keys_arp, "guitar_r": guitar_arp, "bass": _off(bass_solo, 112.0)}, dur)
    inst = {"organ": HAMMOND_ORGAN, "guitar_r": GUITAR_DISTORTION, "bass": BASS_PICK}
    _export(tracks, OUT / "03_Throne.mid", bpm, inst)

# =====================================================================
# IV. Eclipse of the Heart — 66 BPM, 5/4
# =====================================================================
def produce_eclipse():
    print("--- 04_Eclipse ---")
    bpm = 66
    bpc = 5.0
    dur = 150.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=0, duration=dur)]

    # Melancholic Lead
    lead = MelodyGenerator(
        GeneratorParams(density=0.15, complexity=0.5),
        phrase_length=10.0, note_range_low=64, note_range_high=81,
        ornament_probability=0.2
    ).render(chords, KEY, dur)

    # Explosive Metal Section (middle)
    metal_dur = 40.0
    metal_start = 60.0
    c_metal = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=0, duration=metal_dur)]
    
    guitar_metal = MelodyGenerator(
        GeneratorParams(density=0.8, velocity_range=(110, 127)),
        phrase_length=5.0, note_range_low=40, note_range_high=64
    ).render(c_metal, KEY, metal_dur)

    tracks = _art({"lead": lead, "guitar_l": _off(guitar_metal, metal_start)}, dur)
    inst = {"lead": MOOG_LEAD, "guitar_l": GUITAR_DISTORTION}
    _export(tracks, OUT / "04_Eclipse.mid", bpm, inst)

# =====================================================================
# V. The Final Stand — 160 BPM, Epic Finale
# =====================================================================
def produce_final():
    print("--- 05_Final_Stand ---")
    bpm = 160
    dur = 320.0
    # Modulating chord sequence (prog standard)
    p = "i iv v vii " * 8 + "i bII iv bVI " * 8
    from melodica.utils import chord_at
    chords = []
    for i, roman in enumerate(p.split()):
        c = KEY.parse_roman(roman)
        c.start = i * 4.0
        c.duration = 4.0
        chords.append(c)

    # Wall of Sound Organ
    organ = ArpeggiatorGenerator(
        GeneratorParams(density=0.9, velocity_range=(100, 125)),
        pattern="chord", note_duration=1.0
    ).render(chords, KEY, dur)

    # Dual Guitar Attack (Harmony)
    g_gen = MelodyGenerator(GeneratorParams(density=0.6, complexity=0.8))
    g1 = g_gen.render(chords, KEY, dur)
    g2 = [types.NoteInfo(n.pitch + 7, n.start, n.duration, n.velocity) for n in g1] # 5th harmony
    # Re-snap g2
    from melodica.utils import snap_to_scale
    for n in g2:
        n.pitch = snap_to_scale(n.pitch, KEY)

    # Final Ascending Run
    climax = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, key_range_low=40, key_range_high=100, velocity_range=(120, 127)),
        pattern="up", note_duration=0.1
    ).render(chords[-8:], KEY, 32.0)

    tracks = _art({
        "organ": organ,
        "guitar_l": g1 + _off(climax, dur-32.0),
        "guitar_r": g2 + _off(climax, dur-32.0),
        "lead": _off(climax, dur-32.0)
    }, dur)
    inst = {"organ": HAMMOND_ORGAN, "guitar_l": GUITAR_DISTORTION, "guitar_r": GUITAR_OVERDRIVE, "lead": SAW_LEAD}
    _export(tracks, OUT / "05_Final.mid", bpm, inst)

# =====================================================================
# EXECUTION
# =====================================================================
print("=" * 60)
print("   ЧЕРНЫЙ ПРИНЦ (BLACK PRINCE)")
print("   Prog Rock / Hungarian Minor")
print("=" * 60)

produce_coronation()
produce_alchemy()
produce_throne()
produce_eclipse()
produce_final()

print("\n" + "=" * 60)
print("   ALBUM COMPLETE.")
print(f"   Files in: {OUT}")
print("=" * 60)
