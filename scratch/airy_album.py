#!/usr/bin/env python3
"""
airy_album.py — «Skyward» · 6-track airy high-register ambient album.
======================================================================
Pure air: everything lives in MIDI 60–108 (no bass, no low drone).
Bright Lydian/Major harmony, slow tempos (48–62 BPM).

Musical arc across the album:
  1. First Light  — awakening, sparse, just breath and light
  2. Ascension    — gentle lift, the air begins to move
  3. Cirrus       — floating, wispy, the world below disappears
  4. Spire        — tension at the peak, a single point of altitude
  5. Halo         — suspended, weightless, pure resonance
  6. Aperture     — the vault opens, held tones, silence between stars

Each track has its own arp pattern, melody contour, chord palette and
density — they share register (60–108) but differ in character.

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
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# ── GM programs ──────────────────────────────────────────────────────────────
PAD_SPACE    = 91   # Pad 4 (Choir)  — airy shimmer bed
PAD_STRINGS  = 49   # String Ensemble 2 — richer pad option
CELESTA      = 8    # Celesta
HARP         = 46   # Orchestral Harp
GLOCK        = 9    # Glockenspiel
VIBRAPHONE   = 11   # Vibraphone
FLUTE        = 73   # Flute
PICCOLO      = 72   # Piccolo
TUBULAR_BELLS = 14  # Tubular Bells

OUT      = REPO / "output" / "airy"
KEYNAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


# ── helpers ───────────────────────────────────────────────────────────────────

def _off(notes: list[NoteInfo], offset: float) -> list[NoteInfo]:
    return [NoteInfo(pitch=n.pitch, start=n.start + offset,
                     duration=n.duration, velocity=n.velocity) for n in notes]


def _vel(notes: list[NoteInfo], scale: float) -> list[NoteInfo]:
    """Scale all velocities by factor (clamped 1–127)."""
    return [NoteInfo(pitch=n.pitch, start=n.start, duration=n.duration,
                     velocity=max(1, min(127, int(n.velocity * scale)))) for n in notes]


def _master(raw: dict, bpm: float, lufs: float = -16.0,
            gains: dict | None = None) -> tuple:
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update(gains or {
        "pad": 0.44, "arp": 0.52, "lead": 0.62, "bells": 0.54,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    return MasteringDesk(target_lufs=lufs).apply_mastering(mixed)


def _bells(pitches: list[int], first_beat: float, step_beats: float,
           ring: float = 16.0, vel0: int = 52) -> list[NoteInfo]:
    """Tubular-bell ladder: each strike higher, each slightly louder."""
    return [
        NoteInfo(pitch=p, start=first_beat + i * step_beats,
                 duration=ring, velocity=min(92, vel0 + i * 6))
        for i, p in enumerate(pitches)
    ]


def _chords(root: int, mode: Mode, dur: float,
            progression: list[tuple[int, Quality]]) -> list[ChordLabel]:
    """Build a chord progression from (semitone_offset, quality) pairs."""
    n   = len(progression)
    seg = dur / n
    return [
        ChordLabel(root=(root + offset) % 12, quality=qual,
                   start=i * seg, duration=seg)
        for i, (offset, qual) in enumerate(progression)
    ]


# ── per-track build ───────────────────────────────────────────────────────────

def build_track(
    key: Scale,
    chords: list[ChordLabel],
    dur: float,
    *,
    pad_inst: int       = PAD_SPACE,
    arp_inst: int,
    lead_inst: int,
    bell_pitches: list[int],
    # arp
    arp_pattern: str    = "up",
    arp_voicing: str    = "spread",
    arp_octaves: int    = 2,
    arp_note_dur: float = 1.75,
    arp_density: float  = 0.10,
    arp_low: int        = 72,
    arp_high: int       = 96,
    # lead
    lead_density: float        = 0.06,
    lead_phrase: float         = 14.0,
    lead_low: int              = 72,
    lead_high: int             = 96,
    lead_bias: float           = 0.55,
    lead_contour: str          = "rise",
    lead_climax: str           = "up_octave",
    lead_smooth: float         = 0.7,
    lead_harmony_prob: float   = 0.7,
    lead_steps_prob: float     = 0.9,
    lead_accent: str           = "natural",
    lead_offset: float         = 28.0,
    # pad
    pad_density: float  = 0.08,
    pad_low: int        = 60,
    pad_high: int       = 84,
    pad_overlap: float  = 1.0,
    # bells
    bell_first: float   = 24.0,
    bell_ring: float    = 16.0,
) -> dict:
    pad = AmbientPadGenerator(
        GeneratorParams(density=pad_density, key_range_low=pad_low, key_range_high=pad_high),
        voicing="spread", overlap=pad_overlap,
    ).render(chords, key, dur)

    arp = ArpeggiatorGenerator(
        GeneratorParams(density=arp_density, key_range_low=arp_low, key_range_high=arp_high),
        pattern=arp_pattern, note_duration=arp_note_dur,
        octaves=arp_octaves, voicing=arp_voicing,
    ).render(chords, key, dur)

    lead_dur = max(32.0, dur - lead_offset)
    lead = MelodyGenerator(
        GeneratorParams(density=lead_density),
        phrase_length=lead_phrase,
        note_range_low=lead_low,
        note_range_high=lead_high,
        direction_bias=lead_bias,
        phrase_contour=lead_contour,
        climax=lead_climax,
        register_smoothness=lead_smooth,
        harmony_note_probability=lead_harmony_prob,
        steps_probability=lead_steps_prob,
        accent_pattern=lead_accent,
    ).render(chords, key, lead_dur)
    lead = _off(lead, lead_offset)

    step = dur / (len(bell_pitches) + 1)
    bells = _bells(bell_pitches, first_beat=bell_first, step_beats=step, ring=bell_ring)

    return {"pad": pad, "arp": arp, "lead": lead, "bells": bells}


# ── 6 tracks — shared register 60-108, individual character ─────────────────
#
#  Track design:
#  1. First Light  — celesta up, flute rises gently     — F Lydian  56 BPM
#  2. Ascension    — harp up_down, piccolo spirals       — C Lydian  52 BPM
#  3. Cirrus       — vibraphone diverge, flute waves     — G Major   60 BPM
#  4. Spire        — celesta pinky_up, piccolo rise_fall — D Lydian  54 BPM
#  5. Halo         — harp neighbor_up, flute arch        — B Lydian  50 BPM
#  6. Aperture     — glock octave_up, piccolo spiral     — A Lydian  48 BPM

TRACKS = [
    # ── 1. First Light ───────────────────────────────────────────────────────
    dict(
        name="01_First_Light", root=5, mode=Mode.LYDIAN, bpm=56, dur_beats=192,
        pad_inst=PAD_SPACE,
        arp_inst=CELESTA,   lead_inst=FLUTE,
        bell_pitches=[84, 88, 91, 96],
        # very sparse opening — light touches of celesta climbing upward
        arp_pattern="up",       arp_octaves=2,  arp_density=0.08,
        arp_low=72, arp_high=93,
        lead_contour="rise",    lead_climax="up_octave",
        lead_bias=0.50,         lead_density=0.05,
        lead_low=72, lead_high=93, lead_offset=36.0,
        lead_phrase=16.0,       lead_smooth=0.8,
        lead_harmony_prob=0.6,  lead_steps_prob=0.92,
        lead_accent="natural",
        # 2-chord drift: I → ♭VII (Lydian warmth)
        progression=[(0, Quality.MAJOR), (10, Quality.MAJOR)],
        gains={"pad": 0.50, "arp": 0.46, "lead": 0.60, "bells": 0.50},
        bell_ring=18.0,
    ),
    # ── 2. Ascension ─────────────────────────────────────────────────────────
    dict(
        name="02_Ascension", root=0, mode=Mode.LYDIAN, bpm=52, dur_beats=176,
        pad_inst=PAD_SPACE,
        arp_inst=HARP,      lead_inst=PICCOLO,
        bell_pitches=[86, 90, 93, 98],
        # harp up_down — the air begins to move
        arp_pattern="up_down",  arp_octaves=2,  arp_density=0.10,
        arp_low=72, arp_high=96, arp_note_dur=1.5,
        lead_contour="spiral",  lead_climax="up_octave",
        lead_bias=0.55,         lead_density=0.06,
        lead_low=74, lead_high=96, lead_offset=28.0,
        lead_phrase=12.0,       lead_smooth=0.65,
        lead_harmony_prob=0.65, lead_steps_prob=0.88,
        lead_accent="natural",
        # I → II → V — classic Lydian suspension
        progression=[(0, Quality.MAJOR), (2, Quality.MAJOR), (7, Quality.MAJOR)],
        gains={"pad": 0.44, "arp": 0.54, "lead": 0.64, "bells": 0.52},
        bell_ring=16.0,
    ),
    # ── 3. Cirrus ─────────────────────────────────────────────────────────────
    dict(
        name="03_Cirrus", root=7, mode=Mode.MAJOR, bpm=60, dur_beats=180,
        pad_inst=PAD_SPACE,
        arp_inst=VIBRAPHONE, lead_inst=FLUTE,
        bell_pitches=[88, 91, 96, 100],
        # vibraphone diverge — wispy, spreading outward from center
        arp_pattern="diverge",  arp_octaves=2,  arp_density=0.09,
        arp_low=72, arp_high=98, arp_note_dur=2.0, arp_voicing="open",
        lead_contour="wave",    lead_climax="auto",
        lead_bias=0.30,         lead_density=0.07,
        lead_low=72, lead_high=98, lead_offset=24.0,
        lead_phrase=14.0,       lead_smooth=0.72,
        lead_harmony_prob=0.60, lead_steps_prob=0.85,
        lead_accent="strong_weak",
        # I → IV → I — stable pastoral
        progression=[(0, Quality.MAJOR), (5, Quality.MAJOR), (0, Quality.MAJOR)],
        gains={"pad": 0.46, "arp": 0.50, "lead": 0.63, "bells": 0.54},
        bell_ring=15.0,
    ),
    # ── 4. Spire ──────────────────────────────────────────────────────────────
    dict(
        name="04_Spire", root=2, mode=Mode.LYDIAN, bpm=54, dur_beats=188,
        pad_inst=PAD_SPACE,
        arp_inst=CELESTA,   lead_inst=PICCOLO,
        bell_pitches=[89, 93, 98, 103],
        # celesta pinky_up — crystalline high accent on each beat
        arp_pattern="pinky_up",  arp_octaves=2,  arp_density=0.11,
        arp_low=74, arp_high=100, arp_note_dur=1.25, arp_voicing="closed",
        lead_contour="rise_fall", lead_climax="up_octave",
        lead_bias=0.60,           lead_density=0.06,
        lead_low=76, lead_high=100, lead_offset=30.0,
        lead_phrase=13.0,         lead_smooth=0.68,
        lead_harmony_prob=0.72,   lead_steps_prob=0.90,
        lead_accent="natural",
        # I → ♯IV → II — Lydian tension at the spire
        progression=[(0, Quality.MAJOR), (6, Quality.MAJOR), (2, Quality.MAJOR)],
        gains={"pad": 0.42, "arp": 0.56, "lead": 0.65, "bells": 0.56},
        bell_ring=14.0,
    ),
    # ── 5. Halo ───────────────────────────────────────────────────────────────
    dict(
        name="05_Halo", root=11, mode=Mode.LYDIAN, bpm=50, dur_beats=200,
        pad_inst=PAD_SPACE,
        arp_inst=HARP,      lead_inst=FLUTE,
        bell_pitches=[91, 96, 100, 105],
        # harp neighbor_up — gentle oscillation, suspended in air
        arp_pattern="neighbor_up", arp_octaves=2, arp_density=0.09,
        arp_low=72, arp_high=102, arp_note_dur=2.0, arp_voicing="spread",
        lead_contour="arch",   lead_climax="auto",
        lead_bias=0.25,        lead_density=0.055,
        lead_low=74, lead_high=102, lead_offset=32.0,
        lead_phrase=18.0,      lead_smooth=0.82,
        lead_harmony_prob=0.75, lead_steps_prob=0.93,
        lead_accent="natural",
        # I → VI — Lydian halo (just two colours, very still)
        progression=[(0, Quality.MAJOR), (8, Quality.MAJOR)],
        gains={"pad": 0.48, "arp": 0.50, "lead": 0.61, "bells": 0.52},
        bell_ring=20.0,
    ),
    # ── 6. Aperture ───────────────────────────────────────────────────────────
    dict(
        name="06_Aperture", root=9, mode=Mode.LYDIAN, bpm=48, dur_beats=216,
        pad_inst=PAD_SPACE,
        arp_inst=GLOCK,     lead_inst=PICCOLO,
        bell_pitches=[93, 98, 103, 108],
        # glock octave_up — single clear bell, the sky opens
        arp_pattern="octave_up", arp_octaves=2, arp_density=0.07,
        arp_low=72, arp_high=105, arp_note_dur=2.5, arp_voicing="spread",
        lead_contour="rise",   lead_climax="up_octave",
        lead_bias=0.70,        lead_density=0.05,
        lead_low=76, lead_high=108, lead_offset=40.0,
        lead_phrase=20.0,      lead_smooth=0.88,
        lead_harmony_prob=0.80, lead_steps_prob=0.95,
        lead_accent="natural",
        # I → II — the classic Lydian float; hold this through the end
        progression=[(0, Quality.MAJOR), (2, Quality.MAJOR)],
        gains={"pad": 0.46, "arp": 0.48, "lead": 0.62, "bells": 0.54},
        bell_ring=22.0,
    ),
]

INST_NAME = {
    CELESTA: "celesta", HARP: "harp", GLOCK: "glock",
    VIBRAPHONE: "vibraphone", FLUTE: "flute", PICCOLO: "piccolo",
}


def main() -> None:
    print("=" * 76)
    print("  « S K Y W A R D »  —  6-track airy high-register ambient album")
    print("  Lydian/Major · MIDI 60-108 · each track its own character")
    print("=" * 76)
    OUT.mkdir(parents=True, exist_ok=True)

    total_s = 0.0
    for t in TRACKS:
        bpm      = t["bpm"]
        dur      = float(t["dur_beats"])
        secs     = dur * 60 / bpm
        total_s += secs
        key      = Scale(root=t["root"], mode=t["mode"])
        chords   = _chords(t["root"], t["mode"], dur, t["progression"])

        raw = build_track(
            key, chords, dur,
            pad_inst     = t.get("pad_inst", PAD_SPACE),
            arp_inst     = t["arp_inst"],
            lead_inst    = t["lead_inst"],
            bell_pitches = t["bell_pitches"],
            arp_pattern  = t.get("arp_pattern", "up"),
            arp_voicing  = t.get("arp_voicing", "spread"),
            arp_octaves  = t.get("arp_octaves", 2),
            arp_note_dur = t.get("arp_note_dur", 1.75),
            arp_density  = t.get("arp_density", 0.10),
            arp_low      = t.get("arp_low", 72),
            arp_high     = t.get("arp_high", 96),
            lead_density      = t.get("lead_density", 0.06),
            lead_phrase       = t.get("lead_phrase", 14.0),
            lead_low          = t.get("lead_low", 72),
            lead_high         = t.get("lead_high", 96),
            lead_bias         = t.get("lead_bias", 0.55),
            lead_contour      = t.get("lead_contour", "rise"),
            lead_climax       = t.get("lead_climax", "up_octave"),
            lead_smooth       = t.get("lead_smooth", 0.7),
            lead_harmony_prob = t.get("lead_harmony_prob", 0.7),
            lead_steps_prob   = t.get("lead_steps_prob", 0.9),
            lead_accent       = t.get("lead_accent", "natural"),
            lead_offset       = t.get("lead_offset", 28.0),
            pad_low    = t.get("pad_low", 60),
            pad_high   = t.get("pad_high", 84),
            pad_density   = t.get("pad_density", 0.08),
            pad_overlap   = t.get("pad_overlap", 1.0),
            bell_first = t.get("bell_first", 24.0),
            bell_ring  = t.get("bell_ring", 16.0),
        )

        final, cc = _master(raw, bpm, gains=t.get("gains"))
        out = OUT / f"{t['name']}.mid"
        instruments = {
            "pad":   t.get("pad_inst", PAD_SPACE),
            "arp":   t["arp_inst"],
            "lead":  t["lead_inst"],
            "bells": TUBULAR_BELLS,
        }
        export_multitrack_midi(final, str(out), bpm=bpm, key=key,
                               instruments=instruments, cc_events=cc)

        all_notes = [n for v in final.values() for n in v]
        lo = min((n.pitch for n in all_notes), default=0)
        hi = max((n.pitch for n in all_notes), default=0)
        prog_str = "→".join(
            f"{KEYNAMES[(t['root'] + o) % 12]}" for o, _ in t["progression"]
        )
        print(
            f"\n✦ {t['name']}"
            f"  ({KEYNAMES[t['root']]} {t['mode'].name.title()} · {bpm} BPM · ~{secs:.0f}s)\n"
            f"  arp={INST_NAME[t['arp_inst']]}({t.get('arp_pattern','up')})  "
            f"lead={INST_NAME[t['lead_inst']]}({t.get('lead_contour','rise')})  "
            f"chords={prog_str}\n"
            f"  register {lo}–{hi} (MIDI)  |  "
            + ", ".join(f"{k}={len(v)}" for k, v in raw.items())
            + f"\n  ✓ {out.name}"
        )

    print("\n" + "=" * 76)
    print(f"  ALBUM DONE · 6 tracks · ~{total_s:.0f}s (~{total_s / 60:.1f} min)")
    print(f"  Output: output/airy/")
    print("=" * 76)


if __name__ == "__main__":
    main()
