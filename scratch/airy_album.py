#!/usr/bin/env python3
"""
airy_album.py — «Skyward» · 6-track airy high-register ambient album.
=====================================================================
Pure air: everything lives in MIDI 60-108 (no low drone, no bass). Bright
Lydian/Major harmony, slow tempos (48-60 BPM), and three things that pull the
ear upward — ArpeggiatorGenerator(pattern="up", octaves=2) climbing across
octaves, MelodyGenerator(direction_bias=+0.55, phrase_contour="ascending",
climax="end"), and a ladder of high tubular-bell strikes that step up through
the track. Bed = high space pad; sparkle = triangle. Sparse density, lots of
space.

Run:  .venv_dd/bin/python scratch/airy_album.py
Out:  output/airy/*.mid
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
random.seed(108)

from melodica.types import Scale, Mode, Quality, ChordLabel, NoteInfo
from melodica.generators import GeneratorParams, TriangleGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# ── GM programs (all bright / high timbres) ─────────────────────────────────
PAD_SPACE, CELESTA, HARP, GLOCK, FLUTE, PICCOLO, TUBULAR_BELLS = 91, 8, 46, 9, 73, 72, 14

OUT = REPO / "output" / "airy"
KEYNAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _off(notes: list[NoteInfo], offset: float) -> list[NoteInfo]:
    return [NoteInfo(pitch=n.pitch, start=n.start + offset,
                     duration=n.duration, velocity=n.velocity) for n in notes]


def _master(raw: dict, bpm: float, lufs: float = -16.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({           # lead + bells ride above the airy pad
        "pad": 0.46, "arp": 0.52, "lead": 0.64, "bells": 0.56, "tri": 0.30,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    return MasteringDesk(target_lufs=lufs).apply_mastering(mixed)  # (notes, cc)


def _bells(pitches: list[int], first_beat: float, step_beats: float,
           ring: float = 14.0, vel0: int = 58) -> list[NoteInfo]:
    """A ladder of high tubular-bell strikes stepping upward through the track."""
    return [NoteInfo(pitch=p, start=first_beat + i * step_beats,
                     duration=ring, velocity=min(95, vel0 + i * 5))
            for i, p in enumerate(pitches)]


def build_track(key: Scale, chords: list[ChordLabel], dur: float,
                arp_inst: int, lead_inst: int, bell_pitches: list[int]) -> dict:
    # high space-pad bed (no low drone — air only)
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.08, key_range_low=60, key_range_high=84),
        voicing="spread", overlap=1.0,
    ).render(chords, key, dur)
    # the upward pull: arpeggio climbing across two octaves
    arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.10, key_range_low=72, key_range_high=96),
        pattern="up", note_duration=1.75, octaves=2,
    ).render(chords, key, dur)
    # slow ascending melody (flute/piccolo), enters after a breath of pad
    lead = MelodyGenerator(
        GeneratorParams(density=0.06),
        phrase_length=14.0, note_range_low=72, note_range_high=96,
        direction_bias=0.55, phrase_contour="rise", climax="up_octave",
        register_smoothness=0.7, harmony_note_probability=0.7,
        steps_probability=0.9,
    ).render(chords, key, dur - 32.0)
    lead = _off(lead, 28.0)
    bells = _bells(bell_pitches, first_beat=24.0, step_beats=dur / (len(bell_pitches) + 1))
    # silver shimmer, very sparse
    tri = TriangleGenerator(GeneratorParams(density=0.05), pattern_type="trill").render(chords, key, dur)
    return {"pad": pad, "arp": arp, "lead": lead, "bells": bells, "tri": tri}


# ── 6 bright Lydian/Major tracks, climbing in register across the album ─────
TRACKS = [
    {"name": "01_First_Light", "root": 5,  "mode": Mode.LYDIAN, "bpm": 56,
     "arp": CELESTA, "lead": FLUTE,   "bells": [84, 88, 91, 96]},
    {"name": "02_Ascension",   "root": 0,  "mode": Mode.LYDIAN, "bpm": 52,
     "arp": HARP,    "lead": PICCOLO, "bells": [86, 89, 93, 98]},
    {"name": "03_Cirrus",      "root": 7,  "mode": Mode.MAJOR,  "bpm": 60,
     "arp": GLOCK,   "lead": FLUTE,   "bells": [88, 91, 96, 100]},
    {"name": "04_Spire",       "root": 2,  "mode": Mode.LYDIAN, "bpm": 54,
     "arp": CELESTA, "lead": PICCOLO, "bells": [89, 93, 98, 103]},
    {"name": "05_Halo",        "root": 11, "mode": Mode.LYDIAN, "bpm": 50,
     "arp": HARP,    "lead": FLUTE,   "bells": [91, 96, 100, 105]},
    {"name": "06_Aperture",    "root": 9,  "mode": Mode.LYDIAN, "bpm": 48,
     "arp": GLOCK,   "lead": PICCOLO, "bells": [93, 98, 103, 108]},
]

INST_NAME = {CELESTA: "celesta", HARP: "harp", GLOCK: "glock", FLUTE: "flute", PICCOLO: "piccolo"}


def main() -> None:
    print("=" * 76)
    print("  « S K Y W A R D »  —  6-track airy high-register ambient album")
    print("  Lydian/Major · MIDI 60-108 · ascending · pulls the ear upward")
    print("=" * 76)
    OUT.mkdir(parents=True, exist_ok=True)

    total_s = 0.0
    for t in TRACKS:
        bpm = t["bpm"]
        dur = 180.0 if t is not TRACKS[-1] else 208.0
        secs = dur * 60 / bpm
        total_s += secs
        key = Scale(root=t["root"], mode=t["mode"])

        # gentle 2-chord Lydian lift: I → II (the floating major-two) or I → V
        deg2 = (t["root"] + (2 if t["mode"] == Mode.LYDIAN else 7)) % 12
        chords = [
            ChordLabel(root=t["root"], quality=Quality.MAJOR, start=0.0, duration=dur / 2),
            ChordLabel(root=deg2, quality=Quality.MAJOR, start=dur / 2, duration=dur / 2),
        ]

        raw = build_track(key, chords, dur, t["arp"], t["lead"], t["bells"])
        final, cc = _master(raw, bpm)
        out = OUT / f"{t['name']}.mid"
        instruments = {"pad": PAD_SPACE, "arp": t["arp"], "lead": t["lead"],
                       "bells": TUBULAR_BELLS, "tri": 0}
        export_multitrack_midi(final, str(out), bpm=bpm, key=key,
                               instruments=instruments, cc_events=cc)

        lo = min(n.pitch for n in final if n.pitch) if final else 0
        hi = max(n.pitch for n in final) if final else 0
        print(f"\n✦ {t['name']}  ({KEYNAMES[t['root']]} {t['mode'].name.title()} · {bpm} BPM · "
              f"arp={INST_NAME[t['arp']]} lead={INST_NAME[t['lead']]} · ~{secs:.0f}s)")
        print(f"  register {lo}-{hi} (MIDI)  |  "
              + ", ".join(f"{k}={len(v)}" for k, v in raw.items()))
        print(f"  ✓ {out.name}")

    print("\n" + "=" * 76)
    print(f"  ALBUM DONE · 6 tracks · ~{total_s:.0f}s (~{total_s/60:.1f} min)")
    print(f"  Output: output/airy/")
    print("=" * 76)


if __name__ == "__main__":
    main()
