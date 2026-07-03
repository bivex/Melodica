#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
neo_soul.py — a single neo-soul track.

Vibe: D'Angelo / Erykah Badu / Robert Glasper / Maxwell — warm, behind-the-beat,
7th/9th/11th harmony with secondary dominants and tritone subs. E Dorian,
~78 BPM, Rhodes comp, cool tenor sax, lazy acoustic bass, laid-back drums.
Uses the neo_soul harmonizer profile (completion_bonus=5, key_coupling=0.3,
extended_chord_penalty=0 -> chromatic extended 7ths).

Run:  .venv_dd/bin/python scripts/albums/jazz/neo_soul.py
Out:  output/neo_soul/Neo_Soul.mid
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
random.seed(11)

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

# --- Neo-soul parameters ---
KEY = Scale(root=4, mode=Mode.DORIAN)  # E Dorian — warm modal (neo-soul tint)
BPM = 78
DUR = 128.0  # 32 bars
BARS_PER_CHORD = 4.0

# GM programs
ACOUSTIC_BASS, EPIANO, TENOR_SAX, DRUMS = 32, 4, 66, 0  # 4 = Rhodes (epiano)


def make_chords(key: Scale, dur: float) -> list:
    """Dense diatonic-7th contour so the neo_soul profile's set-completion term
    fires -> 7th retention; the low key_coupling then lets secondary dominants /
    tritone subs in (chromatic neo-soul harmony)."""
    total_bars = int(dur / BARS_PER_CHORD)
    harmonizer = CoupledHMMHarmonizer(
        beam_width=14,
        chord_change="bars",
        config=harmonizer_profile("neo_soul"),
    )
    deg = key.degrees()
    n = len(deg)
    contour = []
    for bar in range(total_bars):
        arp = [deg[(bar + k) % n] for k in (0, 2, 4, 6)]  # diatonic 7th, stacked thirds
        for j, pc in enumerate(arp):
            contour.append(NoteInfo(
                pitch=60 + int(pc),
                start=bar * BARS_PER_CHORD + j,
                duration=1.0, velocity=58,
            ))
    return harmonizer.harmonize(contour, key, dur)


def build_neo_soul(chords, key, dur):
    bass = WalkingBassGenerator(
        GeneratorParams(density=0.55, key_range_low=28, key_range_high=41),
        approach_style="mixed", add_chromatic_passing=True, swing_eighth_ratio=0.58,
    ).render(chords, key, dur)
    comp = PianoCompGenerator(
        GeneratorParams(density=0.40, key_range_low=48, key_range_high=72),
        comp_style="jazz", voicing_type="shell", accent_pattern="2_4", chord_density=0.5,
    ).render(chords, key, dur)
    melody = SaxSoloGenerator(
        GeneratorParams(density=0.35, key_range_low=54, key_range_high=84),
        style="cool", vibrato_depth=0.5, chromaticism=0.4, blues_notes=True,
    ).render(chords, key, dur)
    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.04),
        target="snare", pattern="jazz", ghost_velocity=30, ghost_density=0.35,
    ).render(chords, key, dur)
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.07),
        style="jazz", groove_swing=0.56, fill_frequency=0.10, auto_fills=True,
    ).render(chords, key, dur)
    return {
        "Bass": bass, "Comp": comp, "Melody": melody,
        "Ghosts": ghosts, "Drums": drums,
    }


def _mix(raw, bpm):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Bass": 0.85, "Comp": 0.88, "Melody": 0.86, "Drums": 0.55, "Ghosts": 0.42,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=-18.0).apply_mastering(mixed)
    return mastered


def main():
    out_dir = REPO / "output" / "neo_soul"
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
    print(f"### Neo Soul | E Dorian | BPM {BPM} | {len(chords)} chords | neo_soul profile")
    print("  chords:", " ".join(names))
    print(f"  7th/extended chords: {n7}/{len(chords)}")

    raw = build_neo_soul(chords, KEY, DUR)
    mixed = _mix(raw, BPM)
    out = out_dir / "Neo_Soul.mid"
    instruments = {
        "Bass": ACOUSTIC_BASS, "Comp": EPIANO, "Melody": TENOR_SAX,
        "Ghosts": DRUMS, "Drums": DRUMS,
    }
    export_multitrack_midi(mixed, out, bpm=BPM, key=KEY, instruments=instruments)
    print(f"  -> {out}")
    print("  tracks: " + ", ".join(f"{k}={len(v)}" for k, v in mixed.items()))


if __name__ == "__main__":
    main()
