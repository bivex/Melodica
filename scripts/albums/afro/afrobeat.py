#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
afrobeat.py — Fela-style Afrobeat dom7 vamp (F, ~1.8 min).

Layered, hypnotic, dom7-driven: I7-IV7-I7-V7 vamp (F7 - Bb7 - F7 - C7). The
``funk`` profile (dom7+min7 per-type completion {8:5, 7:4}) retains the dom7
chords spelt in the contour — same mechanism as the minor-blues track, now
applied to afrobeat's bluesy dom7 vamps. 108 BPM, layered Afro percussion
(AfrobeatsGenerator + AfroPercussionGenerator), pocket bass, Rhodes comp,
clean-guitar ostinato (Arpeggiator), and brass-section horn stabs.

Run:  .venv_dd/bin/python scripts/albums/afro/afrobeat.py
Out:  output/afro/Afrobeat_F.mid
"""
from __future__ import annotations

import random
import sys
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

warnings.filterwarnings("ignore")
random.seed(67)

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.harmonize import harmonizer_profile
from melodica.generators import GeneratorParams
from melodica.generators.afrobeats import AfrobeatsGenerator
from melodica.generators.afro_percussion import AfroPercussionGenerator
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.midi import export_multitrack_midi
from melodica.theory import name_chord_label
from melodica.types import NoteInfo, Scale, Mode

KEY = Scale(root=5, mode=Mode.MAJOR)  # F major (afrobeat classic; dom7s chromatic, forced by contour)
BPM = 108
LOOPS = 12
BARS_PER_LOOP = 4
BARS_PER_CHORD = 4.0
DUR = float(LOOPS * BARS_PER_LOOP * BARS_PER_CHORD)  # 192 beats = 48 bars

DRUMS, ELEC_BASS, EPIANO, CLEAN_GUITAR, BRASS = 0, 33, 4, 27, 62

# I7-IV7-I7-V7 dom7 vamp (in F), dom7 chord tones.
FORM = ["I7", "IV7", "I7", "V7"]
ARP = {
    "I7":  [5, 9, 0, 3],    # F7:  F A C Eb
    "IV7": [10, 2, 5, 8],   # Bb7: Bb D F Ab
    "V7":  [0, 4, 7, 10],   # C7:  C E G Bb
}


def make_chords(key: Scale, dur: float) -> list:
    total_bars = int(dur / BARS_PER_CHORD)
    harmonizer = CoupledHMMHarmonizer(
        beam_width=14, chord_change="bars",
        config=harmonizer_profile("funk"),
    )
    contour = []
    for bar in range(total_bars):
        for j, pc in enumerate(ARP[FORM[bar % BARS_PER_LOOP]]):
            contour.append(NoteInfo(
                pitch=48 + int(pc), duration=1.0, velocity=55,
                start=bar * BARS_PER_CHORD + j,
            ))
    return harmonizer.harmonize(contour, key, dur)


def build_afrobeat(chords, key, dur):
    groove = AfrobeatsGenerator(
        GeneratorParams(density=0.50),
        variant="afrobeats", log_drum_density=0.60, shaker_pattern="sixteenth",
        include_piano=False, bounce_amount=0.60, percussion_layer=True,
    ).render(chords, key, dur)
    perc = AfroPercussionGenerator(
        GeneratorParams(density=0.50),
        ensemble="west_african", include_pitched=False, call_response=True, swing=0.55,
    ).render(chords, key, dur)
    bass = WalkingBassGenerator(
        GeneratorParams(density=0.60, key_range_low=28, key_range_high=43),
        approach_style="mixed", add_chromatic_passing=True, swing_eighth_ratio=0.56,
    ).render(chords, key, dur)
    keys = PianoCompGenerator(
        GeneratorParams(density=0.30, key_range_low=48, key_range_high=72),
        comp_style="pop", voicing_type="close", accent_pattern="syncopated", chord_density=0.55,
    ).render(chords, key, dur)
    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.55, key_range_low=50, key_range_high=67),
        pattern="up", note_duration=0.5, octaves=1,
    ).render(chords, key, dur)
    horns = BrassSectionGenerator(
        GeneratorParams(density=0.14, key_range_low=54, key_range_high=72),
        articulation="hit", voicing="closed", intensity=0.70, divisi_count=3,
    ).render(chords, key, dur)
    return {"Groove": groove, "Perc": perc, "Bass": bass, "Keys": keys,
            "Guitar": guitar, "Horns": horns}


def _mix(raw, bpm):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Groove": 0.62, "Perc": 0.58, "Bass": 0.84, "Keys": 0.60,
        "Guitar": 0.58, "Horns": 0.56,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=-15.0).apply_mastering(mixed)
    return mastered


def main():
    out_dir = REPO / "output" / "afro"
    out_dir.mkdir(parents=True, exist_ok=True)
    chords = make_chords(KEY, DUR)
    names, n_dom7 = [], 0
    for c in chords:
        nm = name_chord_label(c, key=KEY)
        q = (nm.chosen.interpretation.quality if (nm and nm.chosen) else c.quality)
        rp = (nm.chosen.interpretation.root_pc if (nm and nm.chosen) else c.root)
        names.append(f"{rp}:{q}")
        if q in ("7", "9", "13"):
            n_dom7 += 1
    print(f"### Afrobeat | F major | I7-IV7-I7-V7 vamp x{LOOPS} | BPM {BPM} | "
          f"{len(chords)} chords | funk profile (dom7+min7)")
    print("  chords:", " ".join(names))
    print(f"  dom7-family:{n_dom7}/{len(chords)}")
    raw = build_afrobeat(chords, KEY, DUR)
    mixed = _mix(raw, BPM)
    out = out_dir / "Afrobeat_F.mid"
    instruments = {"Groove": DRUMS, "Perc": DRUMS, "Bass": ELEC_BASS, "Keys": EPIANO,
                   "Guitar": CLEAN_GUITAR, "Horns": BRASS}
    export_multitrack_midi(mixed, out, bpm=BPM, key=KEY, instruments=instruments)
    print(f"  -> {out}")
    print("  tracks: " + ", ".join(f"{k}={len(v)}" for k, v in mixed.items()))


if __name__ == "__main__":
    main()
