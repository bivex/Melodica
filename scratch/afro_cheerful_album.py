#!/usr/bin/env python3
"""
afro_cheerful_album.py — «Sunlight Engine» · 6-track upbeat Afrobeat album.
=========================================================================
Bright, danceable, dom7-vamp Afrobeat in six major keys. Each track layers
AfrobeatsGenerator + AfroPercussionGenerator (log drums + west-african
percussion), pocket walking bass, Rhodes comp, guitar ostinato, and brass
stabs. The ``funk`` profile (dom7+min7 completion) retains the dom7 chords
spelt in the contour — the authentic Fela-style bluesy vamp.

Run:  .venv_dd/bin/python scratch/afro_cheerful_album.py
Out:  output/afro_cheerful/*.mid
"""
from __future__ import annotations

import random
import sys
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
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

# ── GM programs ─────────────────────────────────────────────────────────────
DRUMS, ELEC_BASS, EPIANO, CLEAN_GUITAR, BRASS = 0, 33, 4, 27, 62
INSTRUMENTS = {"Groove": DRUMS, "Perc": DRUMS, "Bass": ELEC_BASS,
               "Keys": EPIANO, "Guitar": CLEAN_GUITAR, "Horns": BRASS}

BARS_PER_CHORD = 4.0

# scale-degree → semitone offset within the key
DEG = {"I": 0, "II": 2, "III": 4, "IV": 5, "V": 7, "VI": 9, "VII": 11}


def _pcs(key_root: int, degree: str, kind: str) -> list[int]:
    """Absolute pitch classes (mod 12) of a dom7/min7 chord on `degree`."""
    r = (key_root + DEG[degree]) % 12
    if kind == "m7":
        return [r, (r + 3) % 12, (r + 7) % 12, (r + 10) % 12]
    return [r, (r + 4) % 12, (r + 7) % 12, (r + 10) % 12]  # dom7


def make_chords(key: Scale, key_root: int, dur: float, form: list[tuple[str, str]]) -> list:
    """Harmonize a dom7 vamp contour (base 48 = multiple of 12)."""
    total_bars = int(dur / BARS_PER_CHORD)
    harmonizer = CoupledHMMHarmonizer(
        beam_width=14, chord_change="bars",
        config=harmonizer_profile("funk"),
    )
    contour = []
    for bar in range(total_bars):
        degree, kind = form[bar % len(form)]
        for j, pc in enumerate(_pcs(key_root, degree, kind)):
            contour.append(NoteInfo(
                pitch=48 + pc, duration=1.0, velocity=55,
                start=bar * BARS_PER_CHORD + j,
            ))
    return harmonizer.harmonize(contour, key, dur)


def build_tracks(chords, key, dur) -> dict:
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


def _mix(raw: dict, bpm: int, lufs: float = -15.0) -> dict:
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Groove": 0.62, "Perc": 0.58, "Bass": 0.84, "Keys": 0.60,
        "Guitar": 0.58, "Horns": 0.56,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=lufs).apply_mastering(mixed)
    return mastered


# ── 6 bright major-key tracks, upbeat tempos, varied vamp forms ─────────────
TRACKS = [
    {"name": "01_Sunrise_Lagos",  "root": 5,  "bpm": 108, "loops": 12,
     "form": [("I", "7"), ("IV", "7"), ("I", "7"), ("V", "7")]},
    {"name": "02_Palm_Groove",    "root": 10, "bpm": 112, "loops": 10,
     "form": [("I", "7"), ("IV", "7"), ("I", "7"), ("V", "7")]},
    {"name": "03_Mango_Dance",    "root": 0,  "bpm": 116, "loops": 10,
     "form": [("I", "7"), ("IV", "7"), ("I", "7"), ("V", "7")]},
    {"name": "04_Yellow_Sky",     "root": 7,  "bpm": 104, "loops": 10,
     "form": [("I", "7"), ("IV", "7"), ("VI", "m7"), ("V", "7")]},
    {"name": "05_Joy_Engine",     "root": 2,  "bpm": 110, "loops": 12,
     "form": [("I", "7"), ("IV", "7"), ("I", "7"), ("V", "7")]},
    {"name": "06_Carnival_Home",  "root": 9,  "bpm": 114, "loops": 10,
     "form": [("I", "7"), ("IV", "7"), ("I", "7"), ("V", "7")]},
]

KEYNAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def main() -> None:
    print("=" * 78)
    print("  « S U N L I G H T   E N G I N E »  —  6-track upbeat Afrobeat album")
    print("=" * 78)

    out_dir = REPO / "output" / "afro_cheerful"
    out_dir.mkdir(parents=True, exist_ok=True)

    total_s = 0.0
    for t in TRACKS:
        key = Scale(root=t["root"], mode=Mode.MAJOR)
        bars = t["loops"] * len(t["form"])
        dur = float(bars * BARS_PER_CHORD)          # beats
        secs = dur * 60 / t["bpm"]
        total_s += secs

        chords = make_chords(key, t["root"], dur, t["form"])
        names, n_dom = [], 0
        for c in chords:
            nm = name_chord_label(c, key=key)
            q = (nm.chosen.interpretation.quality if (nm and nm.chosen) else c.quality)
            rp = (nm.chosen.interpretation.root_pc if (nm and nm.chosen) else c.root)
            names.append(f"{rp}:{q}")
            if q in ("7", "9", "13"):
                n_dom += 1

        raw = build_tracks(chords, key, dur)
        mixed = _mix(raw, t["bpm"])
        out = out_dir / f"{t['name']}.mid"
        export_multitrack_midi(mixed, out, bpm=t["bpm"], key=key, instruments=INSTRUMENTS)

        form_str = "-".join(f"{d}{'7' if k=='7' else 'm7'}" for d, k in t["form"])
        print(f"\n♪ {t['name']}  ({KEYNAMES[t['root']]} major · {t['bpm']} BPM · "
              f"{form_str} · {bars} bars · ~{secs:.0f}s)")
        print(f"  dom7-family:{n_dom}/{len(chords)}  |  "
              + ", ".join(f"{k}={len(v)}" for k, v in mixed.items()))
        print(f"  chords: {' '.join(names[:16])}{' ...' if len(names) > 16 else ''}")
        print(f"  ✓ {out.name}")

    print("\n" + "=" * 78)
    print(f"  ALBUM DONE · 6 tracks · ~{total_s:.0f}s (~{total_s/60:.1f} min)")
    print(f"  Output: output/afro_cheerful/")
    print("=" * 78)


if __name__ == "__main__":
    main()
