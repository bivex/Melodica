#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
melodic_trap_180.py — fast melodic trap with through-composed harmony (180 BPM).

Distinct from the 140-BPM static-axis melodic_trap.py: this one is built around
*interesting transitions* — a 48-bar through-composed C-minor form in four
contrasting sections (no exact loop):

  A  (0–15)  dark trap axis: i - ♭VI - ♭III - ♭VII, then iv / V7/iv sneak in
  T  (16–23) tension transition: iv-V7-i, Neapolitan ♭II, secondary dominants
  B  (24–35) lift: ♭III-led brighter phrasing, more melodic
  O  (36–47) cadential outro: i-iv-V7-i, hold the tonic

Profile is ``funk`` (dom7+min7 per-type completion {8:5, 7:4}) — NOT pop — so the
transition dominants (G7, Bb7) and the dark m7 sonorities (Cm7, Fm7) are
retained. Every spelled chord is one funk can anchor: min7 / dom7 / major triad
(no maj7 or half-dim, which funk's bonus set can't pin). Chromatic chords (G7,
Bb7, Db) are forced by the chord-tone contour despite being non-diatonic to C
natural minor — same mechanism as the blues/afrobeat tracks.

Rhodes comp is included so the chord changes are audible under the 808+drums.
~1.1 min at 180 BPM (half-time felt at 90).

Run:  .venv_dd/bin/python scripts/albums/trap/melodic_trap_180.py
Out:  output/trap/Melodic_Trap_180_Cm.mid
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
random.seed(181)

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.harmonize import harmonizer_profile
from melodica.generators import GeneratorParams
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.midi import export_multitrack_midi
from melodica.theory import name_chord_label
from melodica.types import NoteInfo, Scale, Mode

KEY = Scale(root=0, mode=Mode.NATURAL_MINOR)  # C minor
BPM = 180  # half-time felt ~90
BARS_PER_CHORD = 4.0

SYNTH_BASS, DRUMS, EPIANO, SYNTH_PAD, LEAD_SYNTH = 38, 0, 4, 88, 85

# 48-bar through-composed form (C minor). Sections: A (axis) / T (transition) /
# B (lift) / O (outro). See module docstring.
FORM = [
    # --- A: dark trap axis (bars 0–15) ---
    "i", "bVI", "bIII", "bVII",   "i", "bVI", "bIII", "bVII",
    "i", "bVI", "bIII", "V7",     "i", "iv", "V7iv", "i",
    # --- T: chromatic tension transition (bars 16–23) ---
    "iv", "V7", "i", "bVI",       "bII", "V7", "i", "V7iv",
    # --- B: brighter lift (bars 24–35) ---
    "bIII", "bVII", "i", "bVI",   "bIII", "iv", "V7", "i",
    "bIII", "bVII", "iv", "V7iv",
    # --- O: cadential outro (bars 36–47) ---
    "i", "bVI", "bIII", "bVII",   "i", "iv", "V7", "i",
    "i", "V7", "i", "i",
]
N_BARS = len(FORM)
DUR = float(N_BARS * BARS_PER_CHORD)  # 192 beats

# Chord-tone pcs (in C). Only types funk's {8:5,7:4} can anchor: min7, dom7, maj triad.
ARP = {
    "i":    [0, 3, 7, 10],   # Cm7
    "bVI":  [8, 0, 3],       # Ab
    "bIII": [3, 7, 10],      # Eb
    "bVII": [10, 2, 5],      # Bb
    "iv":   [5, 8, 0, 3],    # Fm7
    "V7":   [7, 11, 2, 5],   # G7   (V7 of Cm — secondary/color)
    "V7iv": [10, 2, 5, 8],   # Bb7  (V7/iv -> resolves to Fm7)
    "bII":  [1, 5, 8],       # Db   (Neapolitan / chromatic mediant)
}


def make_chords(key: Scale, dur: float) -> list:
    total_bars = int(dur / BARS_PER_CHORD)
    harmonizer = CoupledHMMHarmonizer(
        beam_width=14, chord_change="bars",
        config=harmonizer_profile("funk"),
    )
    contour = []
    for bar in range(total_bars):
        for j, pc in enumerate(ARP[FORM[bar]]):
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


def build_trap(chords, key, dur):
    bass808 = Bass808SlidingGenerator(
        GeneratorParams(density=0.36, key_range_low=24, key_range_high=40),
        pattern="trap_basic", slide_probability=0.50, octave_range=2,
    ).render(chords, key, dur)
    drums = TrapDrumsGenerator(
        GeneratorParams(density=0.40),
        variant="standard", hat_roll_density=0.55, kick_pattern="standard",
        open_hat_probability=0.20, groove_swing=0.50,
    ).render(chords, key, dur)
    # Rhodes comp — makes the chord changes audible (the "transitions").
    comp = PianoCompGenerator(
        GeneratorParams(density=0.26, key_range_low=48, key_range_high=72),
        comp_style="pop", voicing_type="close", accent_pattern="syncopated", chord_density=0.45,
    ).render(chords, key, dur)
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.08, key_range_low=36, key_range_high=60),
        voicing="spread", overlap=0.4,
    ).render(chords, key, dur)
    # Melodic hook enters at the transition (bar 16).
    lead = _gate(SoloMelodyGenerator(
        GeneratorParams(density=0.22, key_range_low=60, key_range_high=84),
        style="blues_lick", blues_notes=True, chromaticism=0.30, vibrato_depth=0.3,
    ).render(chords, key, dur), start_at=16 * BARS_PER_CHORD)
    return {"808": bass808, "Drums": drums, "Comp": comp, "Pad": pad, "Lead": lead}


def _mix(raw, bpm):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "808": 0.90, "Drums": 0.64, "Comp": 0.60, "Pad": 0.44, "Lead": 0.66,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=-14.0).apply_mastering(mixed)
    return mastered


def _name(c):
    nm = name_chord_label(c, key=KEY)
    if nm and nm.chosen:
        ri = nm.chosen.interpretation
        return f"{ri.root_pc}:{ri.quality}", ri.quality
    return f"{c.root}:{c.quality}", c.quality


def main():
    out_dir = REPO / "output" / "trap"
    out_dir.mkdir(parents=True, exist_ok=True)
    chords = make_chords(KEY, DUR)

    names, n_m7, n_dom7 = [], 0, 0
    for c in chords:
        label, q = _name(c)
        names.append(label)
        if q in ("min7", "m7", "m9"):
            n_m7 += 1
        elif q in ("7", "9", "13"):
            n_dom7 += 1

    print(f"### Melodic Trap 180 | C minor | through-composed {N_BARS} bars | "
          f"BPM {BPM} | funk profile (dom7+min7)")
    # Section markers for readability
    sec = [("A", 0), ("T", 16), ("B", 24), ("O", 36)]
    for label, start in sec:
        print(f"  [{label} {start:>2}–] " + " ".join(names[start:{"A":16,"T":24,"B":36,"O":48}[label]]))
    print(f"  m7:{n_m7}  dom7:{n_dom7}  (of {len(chords)} chords)")

    raw = build_trap(chords, KEY, DUR)
    mixed = _mix(raw, BPM)
    out = out_dir / "Melodic_Trap_180_Cm.mid"
    instruments = {"808": SYNTH_BASS, "Drums": DRUMS, "Comp": EPIANO,
                   "Pad": SYNTH_PAD, "Lead": LEAD_SYNTH}
    export_multitrack_midi(mixed, out, bpm=BPM, key=KEY, instruments=instruments)
    print(f"  -> {out}")
    print("  tracks: " + ", ".join(f"{k}={len(v)}" for k, v in mixed.items()))


if __name__ == "__main__":
    main()
