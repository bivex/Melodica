#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
pop_rnb.py — modern radio Pop R&B (Ab major, ~2 min).

Bright, catchy, mid-tempo: the I-V-vi-IV axis (Ab - Eb - Fm - Db) that powers
most modern pop. Triadic harmony via the ``pop`` profile (completion_bonus=0 ->
clean pop triads, no jazz 7th color). 98 BPM backbeat, Rhodes comp, electric
bass pocket, clean guitar stabs, sub pad, and a synth lead hook that enters
after bar 8.

Run:  .venv_dd/bin/python scripts/albums/rnb/pop_rnb.py
Out:  output/rnb/Pop_RnB_Ab.mid
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
random.seed(23)

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.harmonize import harmonizer_profile
from melodica.generators import GeneratorParams
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.blues_lick import BluesLickGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.midi import export_multitrack_midi
from melodica.theory import name_chord_label
from melodica.types import NoteInfo, Scale, Mode

KEY = Scale(root=8, mode=Mode.MAJOR)  # Ab major
BPM = 98
LOOPS = 12
BARS_PER_LOOP = 4
BARS_PER_CHORD = 4.0
DUR = float(LOOPS * BARS_PER_LOOP * BARS_PER_CHORD)  # 192 beats = 48 bars
SWING = 0.56

EPIANO, ELEC_BASS, CLEAN_GUITAR, SYNTH_PAD, DRUMS, LEAD_SYNTH = 4, 33, 27, 88, 0, 85

# I-V-vi-IV pop axis (Ab major), triad tones.
FORM = ["I", "V", "vi", "IV"]
ARP = {
    "I":  [8, 0, 3],    # Ab: Ab C Eb
    "V":  [3, 7, 10],   # Eb: Eb G Bb
    "vi": [5, 8, 0],    # Fm: F Ab C
    "IV": [1, 5, 8],    # Db: Db F Ab
}


def make_chords(key: Scale, dur: float) -> list:
    total_bars = int(dur / BARS_PER_CHORD)
    harmonizer = CoupledHMMHarmonizer(
        beam_width=14, chord_change="bars",
        config=harmonizer_profile("pop"),
    )
    contour = []
    for bar in range(total_bars):
        for j, pc in enumerate(ARP[FORM[bar % BARS_PER_LOOP]]):
            contour.append(NoteInfo(
                pitch=48 + int(pc), duration=1.0, velocity=55,
                start=bar * BARS_PER_CHORD + j,
            ))
    return harmonizer.harmonize(contour, key, dur)


def _gate(notes, start_at: float):
    try:
        kept = [n for n in notes if getattr(n, "start", 0.0) >= start_at]
        return kept if kept else notes
    except TypeError:
        return notes


def build_pop_rnb(chords, key, dur):
    rhodes = PianoCompGenerator(
        GeneratorParams(density=0.32, key_range_low=48, key_range_high=72),
        comp_style="pop", voicing_type="close", accent_pattern="syncopated", chord_density=0.60,
    ).render(chords, key, dur)
    bass = WalkingBassGenerator(
        GeneratorParams(density=0.55, key_range_low=28, key_range_high=40),
        approach_style="mixed", add_chromatic_passing=True, swing_eighth_ratio=SWING,
    ).render(chords, key, dur)
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.10),
        style="hiphop", groove_swing=SWING, fill_frequency=0.12, auto_fills=True,
    ).render(chords, key, dur)
    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.04),
        target="snare", pattern="jazz", ghost_velocity=30, ghost_density=0.40,
    ).render(chords, key, dur)
    guitar = BluesLickGenerator(
        GeneratorParams(density=0.20, key_range_low=50, key_range_high=70),
        lick_style="standard", rest_probability=0.55, bend_probability=0.10,
    ).render(chords, key, dur)
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.10, key_range_low=36, key_range_high=60),
        voicing="spread", overlap=0.3,
    ).render(chords, key, dur)
    lead = _gate(SoloMelodyGenerator(
        GeneratorParams(density=0.24, key_range_low=60, key_range_high=81),
        style="blues_lick", blues_notes=False, chromaticism=0.20, vibrato_depth=0.4,
    ).render(chords, key, dur), start_at=8 * BARS_PER_CHORD)
    return {"Comp": rhodes, "Bass": bass, "Drums": drums, "Ghosts": ghosts,
            "Guitar": guitar, "Pad": pad, "Melody": lead}


def _mix(raw, bpm):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Comp": 0.72, "Bass": 0.82, "Drums": 0.64, "Ghosts": 0.42,
        "Guitar": 0.60, "Pad": 0.44, "Melody": 0.70,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=-14.0).apply_mastering(mixed)  # loud pop master
    return mastered


def main():
    out_dir = REPO / "output" / "rnb"
    out_dir.mkdir(parents=True, exist_ok=True)
    chords = make_chords(KEY, DUR)
    names, n_triad, n_ext = [], 0, 0
    for c in chords:
        nm = name_chord_label(c, key=KEY)
        q = (nm.chosen.interpretation.quality if (nm and nm.chosen) else c.quality)
        rp = (nm.chosen.interpretation.root_pc if (nm and nm.chosen) else c.root)
        names.append(f"{rp}:{q}")
        if len(set(c.pitch_classes())) <= 3:
            n_triad += 1
        if len(set(c.pitch_classes())) >= 4:
            n_ext += 1
    print(f"### Pop R&B | Ab major | I-V-vi-IV x{LOOPS} | BPM {BPM} | {len(chords)} chords | pop profile")
    print("  chords:", " ".join(names))
    print(f"  triads:{n_triad}  7th+:{n_ext}/{len(chords)}")
    raw = build_pop_rnb(chords, KEY, DUR)
    mixed = _mix(raw, BPM)
    out = out_dir / "Pop_RnB_Ab.mid"
    instruments = {"Comp": EPIANO, "Bass": ELEC_BASS, "Drums": DRUMS, "Ghosts": DRUMS,
                   "Guitar": CLEAN_GUITAR, "Pad": SYNTH_PAD, "Melody": LEAD_SYNTH}
    export_multitrack_midi(mixed, out, bpm=BPM, key=KEY, instruments=instruments)
    print(f"  -> {out}")
    print("  tracks: " + ", ".join(f"{k}={len(v)}" for k, v in mixed.items()))


if __name__ == "__main__":
    main()
