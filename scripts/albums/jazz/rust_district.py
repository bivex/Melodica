#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
rust_district.py — "Rust District", a single dark-jazz track.

Vibe: Bohren & der Club of Gore / Dale Cooper Quartet / Kilimanjaro Darkjazz
Ensemble — slow, noir, sparse, modal. D Dorian, ~62 BPM, long sustained 7th
harmonies via the jazz harmonizer profile (completion_bonus=5). Tenor sax lead
over spread piano comp, fretless half-time bass, sparse brush ghosts.

Run:  .venv_dd/bin/python scripts/albums/jazz/rust_district.py
Out:  output/rust_district/Rust_District.mid
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
random.seed(7)

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

# --- Dark jazz parameters ---
KEY = Scale(root=2, mode=Mode.DORIAN)  # D Dorian — modal-dark ("So What" tint)
BPM = 62
DUR = 96.0  # 24 bars
BARS_PER_CHORD = 4.0

# GM programs
FRETLESS, PIANO, TENOR_SAX, DRUMS = 35, 0, 66, 0


def make_chords(key: Scale, dur: float) -> list:
    """Dense diatonic-7th contour so the jazz profile's set-completion term
    fires -> 7th harmony. A 1-note/bar contour can't discriminate 7ths
    (completion_bonus needs several chord-tone pcs per slot)."""
    total_bars = int(dur / BARS_PER_CHORD)
    harmonizer = CoupledHMMHarmonizer(
        beam_width=14,
        chord_change="bars",  # one chord per bar (sustained, dark jazz)
        config=harmonizer_profile("jazz"),  # completion_bonus=5 -> 7th retention
    )
    deg = key.degrees()  # absolute pitch classes
    n = len(deg)
    contour = []
    for bar in range(total_bars):
        arp = [deg[(bar + k) % n] for k in (0, 2, 4, 6)]  # diatonic 7th, stacked thirds
        for j, pc in enumerate(arp):
            contour.append(NoteInfo(
                pitch=60 + int(pc),
                start=bar * BARS_PER_CHORD + j,
                duration=1.0, velocity=55,
            ))
    return harmonizer.harmonize(contour, key, dur)


def build_rust_district(chords, key, dur):
    bass = WalkingBassGenerator(
        GeneratorParams(density=0.50, key_range_low=28, key_range_high=40),
        approach_style="mixed", add_chromatic_passing=True, swing_eighth_ratio=0.62,
    ).render(chords, key, dur)
    comp = PianoCompGenerator(
        GeneratorParams(density=0.28, key_range_low=44, key_range_high=67),
        comp_style="jazz", voicing_type="shell", accent_pattern="2_4", chord_density=0.4,
    ).render(chords, key, dur)
    melody = SaxSoloGenerator(
        GeneratorParams(density=0.32, key_range_low=54, key_range_high=82),
        style="cool", vibrato_depth=0.6, chromaticism=0.3, blues_notes=True,
    ).render(chords, key, dur)
    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.03),
        target="snare", pattern="jazz", ghost_velocity=26, ghost_density=0.3,
    ).render(chords, key, dur)
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.05),
        style="jazz", groove_swing=0.60, fill_frequency=0.08, auto_fills=True,
    ).render(chords, key, dur)
    return {
        "Bass": bass, "Comp": comp, "Melody": melody,
        "Ghosts": ghosts, "Drums": drums,
    }


def _mix(raw, bpm):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Bass": 0.82, "Comp": 0.62, "Melody": 0.92, "Drums": 0.40, "Ghosts": 0.38,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=-19.0).apply_mastering(mixed)
    return mastered


def main():
    out_dir = REPO / "output" / "rust_district"
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
    print(f"### Rust District | D Dorian | BPM {BPM} | {len(chords)} chords | jazz profile")
    print("  chords:", " ".join(names))
    print(f"  7th/extended chords: {n7}/{len(chords)}")

    raw = build_rust_district(chords, KEY, DUR)
    mixed = _mix(raw, BPM)
    out = out_dir / "Rust_District.mid"
    instruments = {
        "Bass": FRETLESS, "Comp": PIANO, "Melody": TENOR_SAX,
        "Ghosts": DRUMS, "Drums": DRUMS,
    }
    export_multitrack_midi(mixed, out, bpm=BPM, key=KEY, instruments=instruments)
    print(f"  -> {out}")
    print("  tracks: " + ", ".join(f"{k}={len(v)}" for k, v in mixed.items()))


if __name__ == "__main__":
    main()
