#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
slow_jam.py — quiet-storm / slow-jam R&B (Eb Dorian, ~2.6 min).

Vibe: D'Angelo × Sade × early Erykah — deep pocket, warm Rhodes, fretless
bass, laid-back funk kit with ghost notes, sparse clean guitar, sub pad, and
a smooth trumpet-style lead that enters after the second loop. Eb Dorian
keeps it distinct from the existing E-Dorian neo-soul track (1987fe5).

Harmony: 4-bar Dorian R&B loop — Im7 / IVm7 / Im7 / V7 — spelt as actual
7th-chord-tone arpeggios so the ``neo_soul`` profile (uniform
completion_bonus=5.0, low key coupling 0.3, extended_chord_penalty=0.0 ->
lush 9ths) retains Ebm7/Abm7 (m7) and Bb7 (dom7). Same chord-tone-contour
technique proven on the blues tracks; contour pc sets disambiguate quality.

Run:  .venv_dd/bin/python scripts/albums/rnb/slow_jam.py
Out:  output/rnb/Slow_Jam_EbDor.mid
"""
from __future__ import annotations

import random
import sys
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]  # scripts/albums/rnb/<file> -> repo root
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

warnings.filterwarnings("ignore")
random.seed(91)

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

# --- Slow-jam parameters ---
KEY = Scale(root=3, mode=Mode.DORIAN)  # Eb Dorian (distinct from E Dorian neo-soul)
BPM = 74
LOOPS = 12
BARS_PER_LOOP = 4
BARS_PER_CHORD = 4.0
DUR = float(LOOPS * BARS_PER_LOOP * BARS_PER_CHORD)  # 192 beats = 48 bars
SWING = 0.56  # laid-back R&B pocket

# GM programs
EPIANO, ELEC_BASS, CLEAN_GUITAR, TRUMPET, SYNTH_PAD, DRUMS = 4, 33, 27, 56, 88, 0

# 4-bar Dorian R&B loop: Im7 - IVm7 - Im7 - V7 (chord-tone pcs, in Eb).
FORM = ["Im7", "IVm7", "Im7", "V7"]
ARP = {
    "Im7":  [3, 6, 10, 1],    # Ebm7: Eb Gb Bb Db
    "IVm7": [8, 11, 3, 6],    # Abm7: Ab Cb Eb Gb
    "V7":   [10, 2, 5, 8],    # Bb7:  Bb D F Ab
}


def make_chords(key: Scale, dur: float) -> list:
    """Dorian R&B arpeggio contour -> neo_soul profile harmonization.
    Each bar spells the target 7th chord's tones, so m7 vs dom7 is decided by
    pitch class: Ebm7 [3,6,10,1] only completes to m7; Bb7 [10,2,5,8] to dom7.
    neo_soul's uniform completion_bonus=5.0 rewards all 7th types and its
    extended_chord_penalty=0.0 lets lush 9ths color the voicings."""
    total_bars = int(dur / BARS_PER_CHORD)
    harmonizer = CoupledHMMHarmonizer(
        beam_width=14,
        chord_change="bars",
        config=harmonizer_profile("neo_soul"),
    )
    contour = []
    for bar in range(total_bars):
        arp = ARP[FORM[bar % BARS_PER_LOOP]]
        for j, pc in enumerate(arp):
            contour.append(NoteInfo(
                pitch=48 + int(pc),  # base must be a multiple of 12 to preserve pcs
                start=bar * BARS_PER_CHORD + j,
                duration=1.0, velocity=55,
            ))
    return harmonizer.harmonize(contour, key, dur)


def _gate(notes, start_at: float):
    """Keep notes beginning at/after `start_at` (beats); fall back to full."""
    try:
        kept = [n for n in notes if getattr(n, "start", 0.0) >= start_at]
        return kept if kept else notes
    except TypeError:
        return notes


def build_slow_jam(chords, key, dur):
    rhodes = PianoCompGenerator(
        GeneratorParams(density=0.28, key_range_low=48, key_range_high=72),
        comp_style="jazz", voicing_type="rootless", accent_pattern="syncopated",
        chord_density=0.50,
    ).render(chords, key, dur)
    bass = WalkingBassGenerator(
        GeneratorParams(density=0.50, key_range_low=28, key_range_high=40),
        approach_style="mixed", add_chromatic_passing=True, swing_eighth_ratio=SWING,
    ).render(chords, key, dur)
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.07),
        style="funk", groove_swing=SWING, fill_frequency=0.06, auto_fills=True,
    ).render(chords, key, dur)
    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.03),
        target="snare", pattern="jazz", ghost_velocity=26, ghost_density=0.35,
    ).render(chords, key, dur)
    guitar = BluesLickGenerator(
        GeneratorParams(density=0.18, key_range_low=50, key_range_high=70),
        lick_style="standard", rest_probability=0.60, bend_probability=0.12,
    ).render(chords, key, dur)
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.10, key_range_low=36, key_range_high=60),
        voicing="spread", overlap=0.3,
    ).render(chords, key, dur)
    # Lead enters after the 2nd loop (beat 32) for a gradual build.
    lead = _gate(SoloMelodyGenerator(
        GeneratorParams(density=0.20, key_range_low=58, key_range_high=79),
        style="blues_lick", blues_notes=True, chromaticism=0.30, vibrato_depth=0.5,
    ).render(chords, key, dur), start_at=8 * BARS_PER_CHORD)            # after bar 8

    return {
        "Comp": rhodes, "Bass": bass, "Drums": drums, "Ghosts": ghosts,
        "Guitar": guitar, "Pad": pad, "Melody": lead,
    }


def _mix(raw, bpm):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Comp": 0.74, "Bass": 0.82, "Drums": 0.60, "Ghosts": 0.40,
        "Guitar": 0.64, "Pad": 0.42, "Melody": 0.66,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=-16.0).apply_mastering(mixed)  # hotter than jazz
    return mastered


def main():
    out_dir = REPO / "output" / "rnb"
    out_dir.mkdir(parents=True, exist_ok=True)

    chords = make_chords(KEY, DUR)

    names, n_m7, n_dom7, n_maj7, n_ext = [], 0, 0, 0, 0
    for c in chords:
        nm = name_chord_label(c, key=KEY)
        if nm and nm.chosen:
            ri = nm.chosen.interpretation
            q = ri.quality
            names.append(f"{ri.root_pc}:{q}")
            if q in ("m7", "min7", "m9"):
                n_m7 += 1
            elif q in ("7", "9", "13"):
                n_dom7 += 1
            elif q in ("maj7", "maj9"):
                n_maj7 += 1
            if len(set(c.pitch_classes())) >= 4:
                n_ext += 1
        else:
            names.append(f"{c.root}:{c.quality}")
    print(f"### Slow Jam | Eb Dorian | i-iv-i-V loop x{LOOPS} | BPM {BPM} | "
          f"swing {SWING} | {len(chords)} chords | neo_soul profile")
    print("  chords:", " ".join(names))
    print(f"  m7/m9:{n_m7}  dom7/9/13:{n_dom7}  maj7/9:{n_maj7}  extended(>=4pc):{n_ext}/{len(chords)}")

    raw = build_slow_jam(chords, KEY, DUR)
    mixed = _mix(raw, BPM)
    out = out_dir / "Slow_Jam_EbDor.mid"
    instruments = {
        "Comp": EPIANO, "Bass": ELEC_BASS, "Drums": DRUMS, "Ghosts": DRUMS,
        "Guitar": CLEAN_GUITAR, "Pad": SYNTH_PAD, "Melody": TRUMPET,
    }
    export_multitrack_midi(mixed, out, bpm=BPM, key=KEY, instruments=instruments)
    print(f"  -> {out}")
    print("  tracks: " + ", ".join(f"{k}={len(v)}" for k, v in mixed.items()))


if __name__ == "__main__":
    main()
