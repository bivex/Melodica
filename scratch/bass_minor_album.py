#!/usr/bin/env python3
"""
bass_minor_album.py — «Sub Pressure» · 6-track bass-heavy minor-key trap album.
================================================================================
Built to flex the low end: sliding 808 sub-bass parked in MIDI 24-38 (C1-D2,
~33-73 Hz sub/bass region) at high density with heavy pitch slides and hard
accents, pushed to the front of the mix. Dark minor-key harmony (natural-minor
i-♭VI-♭III-♭VII axis, clean triads via the ``pop`` profile) so the 808 carries
the root motion and the lows are the star. Half-time trap feel.

Run:  .venv_dd/bin/python scratch/bass_minor_album.py
Out:  output/bass_minor/*.mid
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
random.seed(41)

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

# ── GM programs ─────────────────────────────────────────────────────────────
SYNTH_BASS, DRUMS, EPIANO, SYNTH_PAD, LEAD_SYNTH = 38, 0, 4, 88, 85
INSTRUMENTS = {"Sub808": SYNTH_BASS, "Drums": DRUMS, "Keys": EPIANO,
               "Pad": SYNTH_PAD, "Lead": LEAD_SYNTH}

BARS_PER_CHORD = 4.0
CONTOUR_BASE = 48  # multiple of 12 → no transposition artifact

# natural-minor scale-degree → semitone offset from the tonic
DEG = {"i": 0, "bII": 1, "bIII": 3, "iv": 5, "v": 7, "V7": 7,
       "bVI": 8, "bVII": 10, "V7iv": 0}


def _pcs(root: int, sym: str) -> list[int]:
    """Chord-tone pitch classes (mod 12) for a minor-key degree symbol."""
    b = (root + DEG[sym]) % 12
    if sym in ("i", "iv", "v"):                       # minor triad
        return [b, (b + 3) % 12, (b + 7) % 12]
    if sym in ("V7", "V7iv"):                         # dominant 7th
        return [b, (b + 4) % 12, (b + 7) % 12, (b + 10) % 12]
    return [b, (b + 4) % 12, (b + 7) % 12]            # major triad (bII,bIII,bVI,bVII)


def make_chords(key: Scale, root: int, dur: float, form: list[str], profile: str) -> list:
    total_bars = int(dur / BARS_PER_CHORD)
    harmonizer = CoupledHMMHarmonizer(
        beam_width=14, chord_change="bars",
        config=harmonizer_profile(profile),
    )
    contour = []
    for bar in range(total_bars):
        for j, pc in enumerate(_pcs(root, form[bar % len(form)])):
            contour.append(NoteInfo(
                pitch=CONTOUR_BASE + pc, duration=1.0, velocity=55,
                start=bar * BARS_PER_CHORD + j,
            ))
    return harmonizer.harmonize(contour, key, dur)


def build_tracks(chords, key, dur) -> dict:
    # ── the star: deep sliding 808 sub-bass ────────────────────────────────
    sub808 = Bass808SlidingGenerator(
        GeneratorParams(density=0.55, key_range_low=24, key_range_high=38),
        pattern="trap_basic", slide_type="overlap", slide_probability=0.65,
        octave_range=1, accent_velocity=1.25, slide_curve="exponential",
        transient_ducking=True, envelope_gating=True,
    ).render(chords, key, dur)
    drums = TrapDrumsGenerator(
        GeneratorParams(density=0.42),
        variant="standard", hat_roll_density=0.55, kick_pattern="standard",
        open_hat_probability=0.18, groove_swing=0.50,
    ).render(chords, key, dur)
    keys = PianoCompGenerator(
        GeneratorParams(density=0.24, key_range_low=48, key_range_high=72),
        comp_style="pop", voicing_type="close", accent_pattern="syncopated", chord_density=0.45,
    ).render(chords, key, dur)
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.08, key_range_low=36, key_range_high=60),
        voicing="spread", overlap=0.4,
    ).render(chords, key, dur)
    lead = SoloMelodyGenerator(
        GeneratorParams(density=0.18, key_range_low=60, key_range_high=84),
        style="blues_lick", blues_notes=True, chromaticism=0.30, vibrato_depth=0.3,
    ).render(chords, key, dur)
    return {"Sub808": sub808, "Drums": drums, "Keys": keys, "Pad": pad, "Lead": lead}


def _mix(raw: dict, bpm: int, lufs: float = -13.0) -> dict:
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({           # 808 loudest → lows dominate
        "Sub808": 1.00, "Drums": 0.72, "Keys": 0.48, "Pad": 0.38, "Lead": 0.50,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=lufs).apply_mastering(mixed)
    return mastered


# ── 6 dark minor keys, low BPMs for heavy half-time low-end pocket ──────────
TRACKS = [
    {"name": "01_Deep_C",      "root": 0, "bpm": 140, "bars": 40, "profile": "pop",
     "form": ["i", "bVI", "bIII", "bVII"]},
    {"name": "02_Sub_Fusion",  "root": 5, "bpm": 138, "bars": 40, "profile": "pop",
     "form": ["i", "bVII", "bVI", "bIII"]},
    {"name": "03_Gravity_G",   "root": 7, "bpm": 142, "bars": 40, "profile": "pop",
     "form": ["i", "bVI", "iv", "bVII"]},
    {"name": "04_Nightline_D", "root": 2, "bpm": 144, "bars": 40, "profile": "funk",
     "form": ["i", "bVI", "bIII", "V7", "i", "iv", "V7iv", "i"]},
    {"name": "05_Vault_A",     "root": 9, "bpm": 140, "bars": 40, "profile": "pop",
     "form": ["i", "bIII", "bVII", "bVI"]},
    {"name": "06_Abyss_E",     "root": 4, "bpm": 134, "bars": 48, "profile": "pop",
     "form": ["i", "bVI", "bIII", "bVII"]},
]

KEYNAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def main() -> None:
    print("=" * 78)
    print("  « S U B   P R E S S U R E »  —  6-track bass-heavy minor-key trap")
    print("  808 sub-bass · MIDI 24-38 (C1-D2) · sliding · pushed to the front")
    print("=" * 78)

    out_dir = REPO / "output" / "bass_minor"
    out_dir.mkdir(parents=True, exist_ok=True)

    total_s = 0.0
    for t in TRACKS:
        key = Scale(root=t["root"], mode=Mode.NATURAL_MINOR)
        dur = float(t["bars"] * BARS_PER_CHORD)
        secs = dur * 60 / t["bpm"]
        total_s += secs

        chords = make_chords(key, t["root"], dur, t["form"], t["profile"])
        names = []
        for c in chords:
            nm = name_chord_label(c, key=key)
            q = (nm.chosen.interpretation.quality if (nm and nm.chosen) else c.quality)
            rp = (nm.chosen.interpretation.root_pc if (nm and nm.chosen) else c.root)
            names.append(f"{rp}:{q}")

        raw = build_tracks(chords, key, dur)
        mixed = _mix(raw, t["bpm"])
        out = out_dir / f"{t['name']}.mid"
        export_multitrack_midi(mixed, out, bpm=t["bpm"], key=key, instruments=INSTRUMENTS)

        form_str = "-".join(t["form"])
        print(f"\n♫ {t['name']}  ({KEYNAMES[t['root']]} minor · {t['bpm']} BPM · "
              f"{t['profile']} · {form_str} · {t['bars']} bars · ~{secs:.0f}s)")
        print(f"  lows: Sub808={len(raw['Sub808'])} notes  |  "
              + ", ".join(f"{k}={len(v)}" for k, v in mixed.items()))
        print(f"  chords: {' '.join(names[:16])}{' ...' if len(names) > 16 else ''}")
        print(f"  ✓ {out.name}")

    print("\n" + "=" * 78)
    print(f"  ALBUM DONE · 6 tracks · ~{total_s:.0f}s (~{total_s/60:.1f} min)")
    print(f"  Output: output/bass_minor/")
    print("=" * 78)


if __name__ == "__main__":
    main()
