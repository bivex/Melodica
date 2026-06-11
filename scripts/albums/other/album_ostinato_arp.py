# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_ostinato_arp.py — Ostinato & Arpeggio Odysseys

A 4-track concept album showcasing the interplay between Ostinato (fixed repeating patterns)
and Arpeggiator (chord-tone cycling) generators.
MIDI output only. Uses CoupledHMMHarmonizer for backing harmonies.
"""

import random
from pathlib import Path

from melodica import types
from melodica.types import Scale, Mode, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.bass import BassGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer

# General MIDI Programs
ACOUSTIC_GRAND_PIANO = 0
GLOCKENSPIEL = 9
VIBRAPHONE = 11
HARP = 46
SYNTH_LEAD = 80
SYNTH_SAW = 81
PAD_WARM = 89
OVERDRIVEN_GUITAR = 29
ACOUSTIC_BASS = 32
FRETLESS_BASS = 35
SYNTH_BASS = 38
DRUMS = 0 # General MIDI percussion channel 10 trigger

random.seed(42)
OUT = Path("output/ostinato_arp")
OUT.mkdir(parents=True, exist_ok=True)

_harmonizer = CoupledHMMHarmonizer(beam_width=14, chord_change="half")

def _off(notes, offset):
    return [NoteInfo(pitch=n.pitch, start=n.start + offset,
                     duration=n.duration, velocity=n.velocity)
            for n in notes]

def _get_chords(scale: Scale, dur: float):
    degs = scale.degrees()
    guide = [NoteInfo(pitch=60 + int(degs[0]), start=0.0, duration=dur)]
    return _harmonizer.harmonize(melody=guide, initial_scale=scale, duration_beats=dur)

def _master(raw: dict, bpm: float, lufs: float = -16.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.75, "glock": 0.60, "bass": 0.70, "drums": 0.65,
        "lead": 0.75, "synth_bass": 0.70, "pad": 0.55,
        "harp": 0.70, "vibes": 0.60,
        "guitar": 0.75, "saw": 0.65
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)

def _export(tracks: dict, path: Path, bpm: float, key: Scale, instruments: dict):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)

# =====================================================================
# Track 1 — Clockwork Dreams (110 BPM, A Minor)
# Neoclassical/Minimalist. Alberti arpeggios + clockwork glockenspiel.
# =====================================================================
def produce_01_clockwork_dreams():
    print("--- 01_Clockwork_Dreams ---")
    bpm, dur = 110, 128.0
    key = Scale(9, Mode.NATURAL_MINOR)
    chords = _get_chords(key, dur)

    piano = ArpeggiatorGenerator(
        GeneratorParams(density=0.08, key_range_low=48, key_range_high=76),
        pattern="alberti", note_duration=0.25, voicing="closed"
    ).render(chords, key, dur)

    glock = OstinatoGenerator(
        GeneratorParams(density=0.06, key_range_low=72, key_range_high=96),
        pattern="1-3-5-3", repeat_notes=1
    ).render(chords, key, dur - 16.0)
    glock = _off(glock, 8.0)

    bass = WalkingBassGenerator(
        GeneratorParams(density=0.06, key_range_low=28, key_range_high=45),
        approach_style="diatonic", swing_eighth_ratio=0.55
    ).render(chords, key, dur)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.05), style="jazz", groove_swing=0.55,
        fill_frequency=0.1, auto_fills=True
    ).render(chords, key, dur)

    _export({"piano": piano, "glock": glock, "bass": bass, "drums": drums},
            OUT / "01_Clockwork_Dreams.mid", bpm, key,
            {"piano": ACOUSTIC_GRAND_PIANO, "glock": GLOCKENSPIEL, "bass": ACOUSTIC_BASS, "drums": DRUMS})


# =====================================================================
# Track 2 — Neon Horizons (125 BPM, D Minor)
# Synthwave. Pumping octave arps + rolling bass ostinato.
# =====================================================================
def produce_02_neon_horizons():
    print("--- 02_Neon_Horizons ---")
    bpm, dur = 125, 128.0
    key = Scale(2, Mode.NATURAL_MINOR)
    chords = _get_chords(key, dur)

    lead = ArpeggiatorGenerator(
        GeneratorParams(density=0.1, key_range_low=60, key_range_high=84),
        pattern="octave_pump", note_duration=0.25, voicing="open", octaves=2
    ).render(chords, key, dur - 16.0)
    lead = _off(lead, 8.0)

    synth_bass = OstinatoGenerator(
        GeneratorParams(density=0.1, key_range_low=36, key_range_high=52),
        pattern="5-1-5-1", repeat_notes=2
    ).render(chords, key, dur)

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.04, key_range_low=48, key_range_high=72),
        voicing="open"
    ).render(chords, key, dur)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.08), style="rock", fill_frequency=0.15, auto_fills=True
    ).render(chords, key, dur)

    _export({"lead": lead, "synth_bass": synth_bass, "pad": pad, "drums": drums},
            OUT / "02_Neon_Horizons.mid", bpm, key,
            {"lead": SYNTH_LEAD, "synth_bass": SYNTH_BASS, "pad": PAD_WARM, "drums": DRUMS})


# =====================================================================
# Track 3 — Cascading Rain (90 BPM, G Major)
# Ambient/Minimalist. Swelling harp arps + vibraphone ostinatos.
# =====================================================================
def produce_03_cascading_rain():
    print("--- 03_Cascading_Rain ---")
    bpm, dur = 90, 160.0
    key = Scale(7, Mode.IONIAN)
    chords = _get_chords(key, dur)

    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.06, key_range_low=48, key_range_high=84),
        pattern="up_down", note_duration=0.5, voicing="spread", octaves=2
    ).render(chords, key, dur)

    vibes = OstinatoGenerator(
        GeneratorParams(density=0.05, key_range_low=60, key_range_high=84),
        pattern="1-3-1-5", repeat_notes=1
    ).render(chords, key, dur - 32.0)
    vibes = _off(vibes, 16.0)

    bass = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=28, key_range_high=40),
        velocity=50
    ).render(chords, key, dur)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.03), style="jazz", groove_swing=0.5,
        fill_frequency=0.05, auto_fills=True
    ).render(chords, key, dur)

    _export({"harp": harp, "vibes": vibes, "bass": bass, "drums": drums},
            OUT / "03_Cascading_Rain.mid", bpm, key,
            {"harp": HARP, "vibes": VIBRAPHONE, "bass": FRETLESS_BASS, "drums": DRUMS})


# =====================================================================
# Track 4 — Power Surge (140 BPM, E Minor)
# Prog Rock/Fusion. Power chord sweeps + high-density saw ostinato.
# =====================================================================
def produce_04_power_surge():
    print("--- 04_Power_Surge ---")
    bpm, dur = 140, 128.0
    key = Scale(4, Mode.NATURAL_MINOR)
    chords = _get_chords(key, dur)

    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.1, key_range_low=48, key_range_high=72),
        pattern="power", note_duration=0.25, voicing="spread"
    ).render(chords, key, dur)

    saw = OstinatoGenerator(
        GeneratorParams(density=0.08, key_range_low=60, key_range_high=84),
        pattern="1-3-5-6", repeat_notes=1
    ).render(chords, key, dur - 24.0)
    saw = _off(saw, 12.0)

    bass = BassGenerator(
        GeneratorParams(density=0.08, key_range_low=28, key_range_high=48),
        style="root_fifth"
    ).render(chords, key, dur)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.1), style="rock", fill_frequency=0.2, auto_fills=True
    ).render(chords, key, dur)

    _export({"guitar": guitar, "saw": saw, "bass": bass, "drums": drums},
            OUT / "04_Power_Surge.mid", bpm, key,
            {"guitar": OVERDRIVEN_GUITAR, "saw": SYNTH_SAW, "bass": SYNTH_BASS, "drums": DRUMS})


def main():
    print("======================================================================")
    print("  Generating 'Ostinato & Arpeggio Odysseys' Album (4 Tracks)")
    print("======================================================================")
    produce_01_clockwork_dreams()
    produce_02_neon_horizons()
    produce_03_cascading_rain()
    produce_04_power_surge()
    print("======================================================================")
    print(f"  ✓ Production complete. Output folder: {OUT}/")
    print("======================================================================")

if __name__ == "__main__":
    main()
