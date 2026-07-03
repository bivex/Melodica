#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
evening_blues.py — slow minor "night blues" (4 choruses, ~3 min).

Vibe: night blues by the window — late B.B. King × Bill Evans × J.J. Cale.
C minor, ~62 BPM, brushed swing (~58%). The contour spells the minor-blues
form as actual chord-tone arpeggios — Im7 / IVm7 / V7 — so the ``funk``
profile (per-type completion {8:5, 7:4} = dom7+min7) retains Cm7/Fm7 as m7
and G7 as dom7. Note: the ``blues`` profile is dom7-only ({8:5}) and is the
wrong tool here — it can't retain m7, so Im7/IVm7 collapse to min triads.
Minor blues is dom7+min7 harmony, which is exactly the ``funk`` profile.

Development across 4 choruses (lead voices enter by ``start``-gate):
  c1 (0–48)    bass + brushes + pad + sparse Rhodes   — calm, lots of space
  c2 (48–96)   + clean guitar blues phrases
  c3 (96–144)  + vibraphone call/response, fuller
  c4 (144–192) full ensemble — soft climax, V7 turnaround resolves

Run:  .venv_dd/bin/python scripts/albums/jazz/evening_blues.py
Out:  output/evening_blues/Night_Blues_in_Cm.mid
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
random.seed(71)

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.harmonize import harmonizer_profile
from melodica.generators import GeneratorParams
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.blues_lick import BluesLickGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.midi import export_multitrack_midi
from melodica.theory import name_chord_label
from melodica.types import NoteInfo, Scale, Mode

# --- Evening blues parameters ---
KEY = Scale(root=0, mode=Mode.NATURAL_MINOR)  # C minor
BPM = 62
CHORUSES = 4
BARS_PER_CHORD = 4.0
BARS_PER_CHORUS = 12
DUR = float(CHORUSES * BARS_PER_CHORUS * BARS_PER_CHORD)  # 192 beats = 48 bars
BEATS_PER_CHORUS = BARS_PER_CHORUS * BARS_PER_CHORD  # 48
SWING = 0.58  # relaxed blues shuffle (55–62%)

# GM programs
ACOUSTIC_BASS, EPIANO, CLEAN_GUITAR, ORGAN, VIBES, DRUMS = 32, 4, 27, 16, 11, 0

# 12-bar minor-blues form + chord-tone arpeggios (pitch classes, in C).
# Im7/IVm7 are diatonic to C natural minor; V7 (G7) is the harmonic-minor dominant.
FORM = ["Im7", "Im7", "Im7", "Im7", "IVm7", "IVm7", "Im7", "Im7",
        "V7", "IVm7", "Im7", "V7"]
ARP = {
    "Im7":  [0, 3, 7, 10],   # Cm7: C Eb G Bb
    "IVm7": [5, 8, 0, 3],    # Fm7: F Ab C Eb
    "V7":   [7, 11, 2, 5],   # G7:  G B D F
}


def make_chords(key: Scale, dur: float) -> list:
    """Minor-blues arpeggio contour -> funk profile harmonization.
    Each bar spells the target chord's actual 7th-chord tones, so m7 vs dom7
    is decided by the pitch classes (not guessed): Cm7 [0,3,7,10] can only
    complete to m7 (type 7), never dom7 [0,4,7,10] (type 8). The funk profile's
    {8:5, 7:4} completion rewards both, so Im7/IVm7 -> m7 and V7 -> dom7."""
    total_bars = int(dur / BARS_PER_CHORD)
    harmonizer = CoupledHMMHarmonizer(
        beam_width=14,
        chord_change="bars",
        config=harmonizer_profile("funk"),
    )
    contour = []
    for bar in range(total_bars):
        arp = ARP[FORM[bar % BARS_PER_CHORUS]]
        for j, pc in enumerate(arp):
            contour.append(NoteInfo(
                pitch=48 + int(pc),   # low-mid register contour
                start=bar * BARS_PER_CHORD + j,
                duration=1.0, velocity=58,
            ))
    return harmonizer.harmonize(contour, key, dur)


def _gate(notes, start_at: float):
    """Keep only notes beginning at/after `start_at` (beats) — for chorus
    development. Falls back to the full track if notes lack a usable start."""
    try:
        kept = [n for n in notes if getattr(n, "start", 0.0) >= start_at]
        return kept if kept else notes
    except TypeError:
        return notes


def build_evening_blues(chords, key, dur):
    # Bed (full duration): upright bass + brushed kit + Hammond pad + sparse Rhodes.
    bass = WalkingBassGenerator(
        GeneratorParams(density=0.55, key_range_low=28, key_range_high=40),
        approach_style="mixed", add_chromatic_passing=True, swing_eighth_ratio=SWING,
    ).render(chords, key, dur)
    rhodes = PianoCompGenerator(
        GeneratorParams(density=0.28, key_range_low=48, key_range_high=72),
        comp_style="jazz", voicing_type="rootless", accent_pattern="syncopated",
        chord_density=0.35,
    ).render(chords, key, dur)
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.12, key_range_low=36, key_range_high=60),
        voicing="spread", overlap=0.3,
    ).render(chords, key, dur)
    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.03),
        target="snare", pattern="jazz", ghost_velocity=26, ghost_density=0.3,
    ).render(chords, key, dur)
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.06),
        style="jazz", groove_swing=SWING, fill_frequency=0.08, auto_fills=True,
    ).render(chords, key, dur)

    # Lead voices — enter by chorus for the build.
    guitar = _gate(BluesLickGenerator(
        GeneratorParams(density=0.32, key_range_low=50, key_range_high=72),
        lick_style="standard", rest_probability=0.45, bend_probability=0.18,
    ).render(chords, key, dur), start_at=1 * BEATS_PER_CHORUS)          # chorus 2
    vibes = _gate(BluesLickGenerator(
        GeneratorParams(density=0.15, key_range_low=72, key_range_high=88),
        lick_style="standard", rest_probability=0.55, bend_probability=0.10,
    ).render(chords, key, dur), start_at=2 * BEATS_PER_CHORUS)          # chorus 3

    return {
        "Bass": bass, "Comp": rhodes, "Pad": pad,
        "Ghosts": ghosts, "Drums": drums,
        "Guitar": guitar, "Vibes": vibes,
    }


def _mix(raw, bpm):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Bass": 0.80, "Comp": 0.72, "Pad": 0.40,
        "Ghosts": 0.42, "Drums": 0.55,
        "Guitar": 0.72, "Vibes": 0.60,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=-18.0).apply_mastering(mixed)
    return mastered


def main():
    out_dir = REPO / "output" / "evening_blues"
    out_dir.mkdir(parents=True, exist_ok=True)

    chords = make_chords(KEY, DUR)

    names, n_m7, n_dom7, n_ext = [], 0, 0, 0
    for c in chords:
        nm = name_chord_label(c, key=KEY)
        if nm and nm.chosen:
            ri = nm.chosen.interpretation
            q = ri.quality
            names.append(f"{ri.root_pc}:{q}")
            if q == "m7":
                n_m7 += 1
            elif q == "7":
                n_dom7 += 1
            if len(set(c.pitch_classes())) >= 4:
                n_ext += 1
        else:
            names.append(f"{c.root}:{c.quality}")
    print(f"### Night Blues in Cm | minor-blues 12-bar x{CHORUSES} | BPM {BPM} | "
          f"swing {SWING} | {len(chords)} chords | funk profile (min7+dom7)")
    print("  chords:", " ".join(names))
    print(f"  m7:{n_m7}  dom7:{n_dom7}  extended(>=4pc):{n_ext}/{len(chords)}")

    raw = build_evening_blues(chords, KEY, DUR)
    mixed = _mix(raw, BPM)
    out = out_dir / "Night_Blues_in_Cm.mid"
    instruments = {
        "Bass": ACOUSTIC_BASS, "Comp": EPIANO, "Pad": ORGAN,
        "Ghosts": DRUMS, "Drums": DRUMS,
        "Guitar": CLEAN_GUITAR, "Vibes": VIBES,
    }
    export_multitrack_midi(mixed, out, bpm=BPM, key=KEY, instruments=instruments)
    print(f"  -> {out}")
    print("  tracks: " + ", ".join(f"{k}={len(v)}" for k, v in mixed.items()))


if __name__ == "__main__":
    main()
