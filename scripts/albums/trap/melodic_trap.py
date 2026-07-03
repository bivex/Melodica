#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
melodic_trap.py — dark melodic trap (C minor, half-time @140, ~1.4 min).

Sparse, heavy, atmospheric: the i-♭VI-♭III-♭VII rap/trap axis (Cm - Ab - Eb -
Bb). Triadic minor harmony via the ``pop`` profile (trap is harmonically
minimal — simple minor triads, no jazz extensions). 140 BPM half-time feel,
808 sliding bass, trap drums with hat rolls, dark sub pad, and an autotuned-
style melodic lead hook.

Run:  .venv_dd/bin/python scripts/albums/trap/melodic_trap.py
Out:  output/trap/Melodic_Trap_Cm.mid
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
random.seed(41)

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.harmonize import harmonizer_profile
from melodica.generators import GeneratorParams
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.midi import export_multitrack_midi
from melodica.theory import name_chord_label
from melodica.types import NoteInfo, Scale, Mode

KEY = Scale(root=0, mode=Mode.NATURAL_MINOR)  # C minor
BPM = 140  # half-time feel
LOOPS = 12
BARS_PER_LOOP = 4
BARS_PER_CHORD = 4.0
DUR = float(LOOPS * BARS_PER_LOOP * BARS_PER_CHORD)  # 192 beats = 48 bars

SYNTH_BASS, DRUMS, LEAD_SYNTH, SYNTH_PAD = 38, 0, 85, 88

# i-♭VI-♭III-♭VII trap axis (C minor), minor triad tones.
FORM = ["i", "bVI", "bIII", "bVII"]
ARP = {
    "i":    [0, 3, 7],    # Cm:  C Eb G
    "bVI":  [8, 0, 3],    # Ab:  Ab C Eb
    "bIII": [3, 7, 10],   # Eb:  Eb G Bb
    "bVII": [10, 2, 5],   # Bb:  Bb D F
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


def build_trap(chords, key, dur):
    bass808 = Bass808SlidingGenerator(
        GeneratorParams(density=0.45, key_range_low=24, key_range_high=40),
        pattern="trap_basic", slide_probability=0.50, octave_range=2,
    ).render(chords, key, dur)
    drums = TrapDrumsGenerator(
        GeneratorParams(density=0.40),
        variant="standard", hat_roll_density=0.60, kick_pattern="standard",
        open_hat_probability=0.20, groove_swing=0.50,
    ).render(chords, key, dur)
    hats = HiHatStutterGenerator(
        GeneratorParams(density=0.25),
        pattern="trap_eighth", roll_density=0.40, open_hat_probability=0.15,
    ).render(chords, key, dur)
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.08, key_range_low=36, key_range_high=60),
        voicing="spread", overlap=0.4,
    ).render(chords, key, dur)
    lead = _gate(SoloMelodyGenerator(
        GeneratorParams(density=0.18, key_range_low=55, key_range_high=76),
        style="blues_lick", blues_notes=True, chromaticism=0.25, vibrato_depth=0.3,
    ).render(chords, key, dur), start_at=8 * BARS_PER_CHORD)
    return {"808": bass808, "Drums": drums, "Hats": hats, "Pad": pad, "Lead": lead}


def _mix(raw, bpm):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "808": 0.92, "Drums": 0.66, "Hats": 0.50, "Pad": 0.46, "Lead": 0.64,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=-14.0).apply_mastering(mixed)
    return mastered


def main():
    out_dir = REPO / "output" / "trap"
    out_dir.mkdir(parents=True, exist_ok=True)
    chords = make_chords(KEY, DUR)
    names, n_min = [], 0
    for c in chords:
        nm = name_chord_label(c, key=KEY)
        q = (nm.chosen.interpretation.quality if (nm and nm.chosen) else c.quality)
        rp = (nm.chosen.interpretation.root_pc if (nm and nm.chosen) else c.root)
        names.append(f"{rp}:{q}")
        if q in ("min", "m", "min7"):
            n_min += 1
    print(f"### Melodic Trap | C minor | i-bVI-bIII-bVII x{LOOPS} | BPM {BPM} | "
          f"{len(chords)} chords | pop profile")
    print("  chords:", " ".join(names))
    print(f"  minor chords:{n_min}/{len(chords)}")
    raw = build_trap(chords, KEY, DUR)
    mixed = _mix(raw, BPM)
    out = out_dir / "Melodic_Trap_Cm.mid"
    instruments = {"808": SYNTH_BASS, "Drums": DRUMS, "Hats": DRUMS,
                   "Pad": SYNTH_PAD, "Lead": LEAD_SYNTH}
    export_multitrack_midi(mixed, out, bpm=BPM, key=KEY, instruments=instruments)
    print(f"  -> {out}")
    print("  tracks: " + ", ".join(f"{k}={len(v)}" for k, v in mixed.items()))


if __name__ == "__main__":
    main()
