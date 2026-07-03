#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
blues.py — a 12-bar blues track, two choruses.

Standard I7-IV7-V7 blues with dominant 7ths throughout (the "blues 7th"). The
contour outlines a dom7 arpeggio per bar following the 12-bar form, so the
``blues`` harmonizer profile's per-type completion_bonus ({8: 5.0}) retains
C7/F7/G7 as dom7 (a uniform bonus couldn't favor dom7 over maj7). ~120 BPM
shuffle: blues-piano comp, blue-note tenor sax, walking bass, ride+backbeat.

Run:  .venv_dd/bin/python scripts/albums/jazz/blues.py
Out:  output/blues/Blues_in_C.mid
"""
from __future__ import annotations

import random
import sys
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]  # scripts/albums/jazz/<file> -> repo root
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

warnings.filterwarnings("ignore")
random.seed(13)

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.harmonize import harmonizer_profile
from melodica.generators import GeneratorParams
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.sax_solo import SaxSoloGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.midi import export_multitrack_midi
from melodica.theory import name_chord_label
from melodica.types import NoteInfo, Scale, Mode

# --- Blues parameters ---
KEY = Scale(root=0, mode=Mode.MAJOR)  # C — tonal center; blues dom7s are chromatic to it (normal)
BPM = 120
CHORUSES = 2
BARS_PER_CHORD = 4.0
BARS_PER_CHORUS = 12
DUR = float(CHORUSES * BARS_PER_CHORUS * BARS_PER_CHORD)  # 96 beats = 24 bars

# GM programs
ACOUSTIC_BASS, PIANO, TENOR_SAX, DRUMS = 32, 0, 66, 0

# 12-bar blues form + dom7 arpeggios (pcs) per chord degree (in C).
FORM = ["I", "I", "I", "I", "IV", "IV", "I", "I", "V", "IV", "I", "V"]
DOM7 = {
    "I":  [0, 4, 7, 10],    # C7: C E G Bb
    "IV": [5, 9, 0, 3],     # F7: F A C Eb
    "V":  [7, 11, 2, 5],    # G7: G B D F
}


def make_chords(key: Scale, dur: float) -> list:
    """12-bar dom7 contour so the blues profile's per-type completion ({8:5})
    retains C7/F7/G7 as dom7. The contour spells dom7 chord tones -> M subset
    chord_tones(dom7) -> bonus fires only for type 8 (not triads/maj7)."""
    total_bars = int(dur / BARS_PER_CHORD)
    harmonizer = CoupledHMMHarmonizer(
        beam_width=14,
        chord_change="bars",
        config=harmonizer_profile("blues"),
    )
    contour = []
    for bar in range(total_bars):
        arp = DOM7[FORM[bar % BARS_PER_CHORUS]]
        for j, pc in enumerate(arp):
            contour.append(NoteInfo(
                pitch=60 + int(pc),
                start=bar * BARS_PER_CHORD + j,
                duration=1.0, velocity=60,
            ))
    return harmonizer.harmonize(contour, key, dur)


def build_blues(chords, key, dur):
    bass = WalkingBassGenerator(
        GeneratorParams(density=0.65, key_range_low=28, key_range_high=40),
        approach_style="mixed", add_chromatic_passing=True, swing_eighth_ratio=0.67,
    ).render(chords, key, dur)
    comp = PianoCompGenerator(
        GeneratorParams(density=0.45, key_range_low=48, key_range_high=72),
        comp_style="jazz", voicing_type="shell", accent_pattern="2_4", chord_density=0.6,
    ).render(chords, key, dur)
    melody = SaxSoloGenerator(
        GeneratorParams(density=0.40, key_range_low=54, key_range_high=84),
        style="cool", vibrato_depth=0.5, chromaticism=0.4, blues_notes=True,
    ).render(chords, key, dur)
    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.04),
        target="snare", pattern="jazz", ghost_velocity=30, ghost_density=0.4,
    ).render(chords, key, dur)
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.10),
        style="jazz", groove_swing=0.67, fill_frequency=0.12, auto_fills=True,
    ).render(chords, key, dur)
    return {"Bass": bass, "Comp": comp, "Melody": melody, "Ghosts": ghosts, "Drums": drums}


def _mix(raw, bpm):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Bass": 0.85, "Comp": 0.80, "Melody": 0.86, "Drums": 0.60, "Ghosts": 0.45,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=-18.0).apply_mastering(mixed)
    return mastered


def main():
    out_dir = REPO / "output" / "blues"
    out_dir.mkdir(parents=True, exist_ok=True)

    chords = make_chords(KEY, DUR)

    names = []
    for c in chords:
        nm = name_chord_label(c, key=KEY)
        if nm and nm.chosen:
            ri = nm.chosen.interpretation
            names.append(f"{ri.root_pc}:{ri.quality}")
        else:
            names.append(f"{c.root}:{c.quality}")
    n7 = sum(1 for c in chords if len(set(c.pitch_classes())) >= 4)
    ndom7 = sum(1 for c in chords if len(set(c.pitch_classes())) >= 4 and len(set(c.pitch_classes())) == 4)
    print(f"### Blues in C | 12-bar x{CHORUSES} | BPM {BPM} | {len(chords)} chords | blues profile")
    print("  chords:", " ".join(names))
    print(f"  7th/extended chords: {n7}/{len(chords)}")

    raw = build_blues(chords, KEY, DUR)
    mixed = _mix(raw, BPM)
    out = out_dir / "Blues_in_C.mid"
    instruments = {
        "Bass": ACOUSTIC_BASS, "Comp": PIANO, "Melody": TENOR_SAX,
        "Ghosts": DRUMS, "Drums": DRUMS,
    }
    export_multitrack_midi(mixed, out, bpm=BPM, key=KEY, instruments=instruments)
    print(f"  -> {out}")
    print("  tracks: " + ", ".join(f"{k}={len(v)}" for k, v in mixed.items()))


if __name__ == "__main__":
    main()
