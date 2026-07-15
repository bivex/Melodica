#!/usr/bin/env python3
"""
bass_minor_album.py — «Sub Pressure» · 9-track bass-heavy minor-key album (trap · four-on-the-floor · hardstyle).
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
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.fills import FillGenerator
from melodica.generators.four_on_floor import FourOnFloorGenerator
from melodica.generators.hardstyle import HardstyleGenerator
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.midi import export_multitrack_midi
from melodica.theory import name_chord_label
from melodica.types import NoteInfo, Scale, Mode

# ── GM programs ─────────────────────────────────────────────────────────────
SYNTH_BASS, DRUMS, EPIANO, SYNTH_PAD, LEAD_SYNTH = 38, 0, 4, 88, 85
INSTRUMENTS = {"Sub808": SYNTH_BASS, "Drums": DRUMS, "Keys": EPIANO,
               "Pad": SYNTH_PAD, "Lead": LEAD_SYNTH,
               "Fills": DRUMS, "Riser": LEAD_SYNTH, "Impact": SYNTH_BASS}

# ── section plan: intro → drop → verse → build → drop → outro ───────────────
# sparse intro builds tension; riser→impact at each drop = the "wow" transition.
PROF = {  # per-section density by generator
    "intro": {"drums": 0.30, "bass": 0.30, "keys": 0.22, "pad": 0.10, "lead": 0.00},
    "drop":  {"drums": 0.50, "bass": 0.72, "keys": 0.28, "pad": 0.10, "lead": 0.24},
    "verse": {"drums": 0.44, "bass": 0.60, "keys": 0.26, "pad": 0.08, "lead": 0.20},
    "build": {"drums": 0.36, "bass": 0.55, "keys": 0.22, "pad": 0.16, "lead": 0.10},
    "outro": {"drums": 0.32, "bass": 0.50, "keys": 0.20, "pad": 0.10, "lead": 0.16},
}


def _sections(total_bars: int) -> list[tuple[str, int]]:
    if total_bars >= 48:
        return [("intro", 8), ("drop", 8), ("verse", 8),
                ("build", 8), ("drop", 8), ("outro", 8)]
    return [("intro", 8), ("drop", 8), ("verse", 8),
            ("build", 4), ("drop", 8), ("outro", 4)]


def _offset(notes: list, delta: float) -> list:
    """Shift a freshly-rendered note list forward by `delta` beats (in place)."""
    for n in notes:
        n.start += delta
    return notes


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


def _render_drums(kick: str, ch, key, dur: float, density: float, swing: float):
    """Pick the drum engine by kick mode — 'trap' | 'four_floor' | 'hardstyle'."""
    if kick == "four_floor":                       # relentless kick every beat + claps 2&4
        return FourOnFloorGenerator(
            GeneratorParams(density=density),
            variant="house", hihat_style="mixed", clap_location="2_4", swing=swing,
        ).render(ch, key, dur)
    if kick == "hardstyle":                        # distorted pumping kick
        return HardstyleGenerator(
            GeneratorParams(density=density),
            variant="euphoric", kick_distortion=0.85, include_lead=False,
            reverse_bass_weight=0.5,
        ).render(ch, key, dur)
    return TrapDrumsGenerator(                      # default trap half-time
        GeneratorParams(density=density),
        variant="standard", hat_roll_density=0.58, kick_pattern="standard",
        open_hat_probability=0.20, groove_swing=swing,
    ).render(ch, key, dur)


def build_track(chords_all: list, key: Scale, total_bars: int, kick: str = "trap") -> dict:
    """Section-by-section render: builds, risers, impacts, fills at transitions."""
    tracks = {k: [] for k in ("Sub808", "Drums", "Keys", "Pad", "Lead",
                              "Fills", "Riser", "Impact")}
    bar_cursor = 0
    for sec_type, sec_bars in _sections(total_bars):
        cslice = chords_all[bar_cursor:bar_cursor + sec_bars]
        dur = float(sec_bars * BARS_PER_CHORD)
        off = float(bar_cursor * BARS_PER_CHORD)
        ch = cslice   # chord_at() now resolves localized slices in-core (no rebase needed)
        p = PROF[sec_type]

        bass = Bass808SlidingGenerator(
            GeneratorParams(density=p["bass"], key_range_low=24, key_range_high=38),
            pattern="trap_basic", slide_type="overlap", slide_probability=0.65,
            octave_range=1, accent_velocity=1.25, slide_curve="exponential",
            transient_ducking=True, envelope_gating=True,
        ).render(ch, key, dur)
        drums = _render_drums(kick, ch, key, dur, p["drums"], 0.58)
        keys = PianoCompGenerator(
            GeneratorParams(density=p["keys"], key_range_low=48, key_range_high=72),
            comp_style="pop", voicing_type="close", accent_pattern="syncopated", chord_density=0.45,
        ).render(ch, key, dur)
        pad = AmbientPadGenerator(
            GeneratorParams(density=p["pad"], key_range_low=36, key_range_high=60),
            voicing="spread", overlap=0.4,
        ).render(ch, key, dur)
        lead = (SoloMelodyGenerator(
            GeneratorParams(density=p["lead"], key_range_low=60, key_range_high=84),
            style="blues_lick", blues_notes=True, chromaticism=0.30, vibrato_depth=0.3,
        ).render(ch, key, dur) if p["lead"] > 0 else [])

        for name, notes in (("Sub808", bass), ("Drums", drums), ("Keys", keys),
                            ("Pad", pad), ("Lead", lead)):
            tracks[name] += _offset(notes, off)

        # one drum fill rolling out of the last bar of drops/verses
        if sec_type in ("drop", "verse") and sec_bars >= 4:
            fills = FillGenerator(
                GeneratorParams(density=0.30, key_range_low=36, key_range_high=60),
                fill_type="descending", fill_length=2.0, position="end",
                velocity_curve="crescendo",
            ).render(ch[-1:], key, 4.0)
            tracks["Fills"] += _offset(fills, off + dur - 4.0)

        # riser sweeping up across the whole build → lands on the next drop
        if sec_type == "build":
            riser = FXRiserGenerator(
                GeneratorParams(density=0.50, key_range_low=48, key_range_high=84),
                riser_type="synth", length_beats=min(dur, 4.0),
                pitch_curve="exponential", peak_velocity=118,
            ).render(ch, key, dur)
            tracks["Riser"] += _offset(riser, off)

        # impact boom on the downbeat of every drop (the "slam")
        if sec_type == "drop":
            impact = FXImpactGenerator(
                GeneratorParams(density=0.50, key_range_low=24, key_range_high=48),
                impact_type="boom", tail_length=2.5, pitch_drop=12, placement="downbeat",
            ).render(ch, key, min(dur, 4.0))
            tracks["Impact"] += _offset(impact, off)

        bar_cursor += sec_bars
    return tracks


def _mix(raw: dict, bpm: int, lufs: float = -13.0) -> dict:
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({           # 808 loudest → lows dominate; impacts punch through
        "Sub808": 1.00, "Drums": 0.74, "Keys": 0.48, "Pad": 0.38, "Lead": 0.50,
        "Fills": 0.58, "Riser": 0.52, "Impact": 0.85,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=lufs).apply_mastering(mixed)
    return mastered


# ── 6 dark minor keys, low BPMs for heavy half-time low-end pocket ──────────
TRACKS = [
    {"name": "01_Trench",     "root": 0, "bpm": 140, "bars": 40, "profile": "pop",
     "form": ["i", "bVI", "bIII", "bVII"]},
    {"name": "02_Undertow",   "root": 5, "bpm": 138, "bars": 40, "profile": "pop",
     "form": ["i", "bVII", "bVI", "bIII"]},
    {"name": "03_Subzero",    "root": 7, "bpm": 142, "bars": 40, "profile": "pop",
     "form": ["i", "bVI", "iv", "bVII"]},
    {"name": "04_Lowburn",    "root": 2, "bpm": 144, "bars": 40, "profile": "funk",
     "form": ["i", "bVI", "bIII", "V7", "i", "iv", "V7iv", "i"]},
    {"name": "05_Concrete",   "root": 9, "bpm": 140, "bars": 40, "profile": "pop",
     "form": ["i", "bIII", "bVII", "bVI"]},
    {"name": "06_Mariana",    "root": 4, "bpm": 134, "bars": 48, "profile": "pop",
     "form": ["i", "bVI", "bIII", "bVII"]},
    # ── +3 kick-forward tracks: the drum is the point ──────────────────────
    {"name": "07_Piston",     "root": 1, "bpm": 128, "bars": 40, "profile": "pop",
     "kick": "four_floor", "form": ["i", "bVI", "bIII", "bVII"]},
    {"name": "08_Overdrive",  "root": 6, "bpm": 150, "bars": 40, "profile": "funk",
     "kick": "hardstyle", "form": ["i", "bVI", "bIII", "V7", "i", "iv", "V7iv", "i"]},
    {"name": "09_Locomotive", "root": 8, "bpm": 130, "bars": 40, "profile": "pop",
     "kick": "four_floor", "form": ["i", "bVII", "bVI", "bIII"]},
]

KEYNAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def main() -> None:
    print("=" * 78)
    print("  « S U B   P R E S S U R E »  —  9-track bass-heavy minor-key · trap + four-on-the-floor + hardstyle")
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

        raw = build_track(chords, key, t["bars"], kick=t.get("kick", "trap"))
        mixed = _mix(raw, t["bpm"])
        out = out_dir / f"{t['name']}.mid"
        export_multitrack_midi(mixed, out, bpm=t["bpm"], key=key, instruments=INSTRUMENTS)

        form_str = "-".join(t["form"])
        kick = t.get("kick", "trap")
        kick_tag = {"trap": "half-time trap", "four_floor": "FOUR-ON-THE-FLOOR",
                    "hardstyle": "hardstyle pump"}[kick]
        print(f"\n♫ {t['name']}  ({KEYNAMES[t['root']]} minor · {t['bpm']} BPM · "
              f"{t['profile']} · {form_str} · {kick_tag} · {t['bars']} bars · ~{secs:.0f}s)")
        print(f"  kick+drums={len(raw['Drums'])} notes · impacts={len(raw['Impact'])} · "
              f"riser={len(raw['Riser'])} · Sub808={len(raw['Sub808'])} low notes")
        print(f"  ✓ {out.name}")

    print("\n" + "=" * 78)
    print(f"  ALBUM DONE · 9 tracks · ~{total_s:.0f}s (~{total_s/60:.1f} min)")
    print(f"  Output: output/bass_minor/")
    print("=" * 78)


if __name__ == "__main__":
    main()
