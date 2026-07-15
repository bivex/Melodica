#!/usr/bin/env python3
"""
lorn_album.py — «Ash & Iron» · 6-track dark low-register album in the style of Lorn.
======================================================================================
Character:
  - Все ноты в MIDI 24–72 (суббас, нижний-средний регистр — ничего выше C5)
  - Лады: Phrygian, Phrygian Dominant, Double Harmonic, Locrian, Natural Minor,
          Hungarian Minor — тёмные, с характерными b2/b5/b6
  - Барабаны: 808-кит, breakbeat/minimal паттерны, ghost notes, свинг
  - Бас: тяжёлый pedal_tone / root_fifth_octave в низком регистре
  - Текстура: NebulaGenerator(granular/stasis) + AmbientPad в тени
  - Мелодия: MelodyGenerator с direction_bias < 0 (тяготение вниз),
             phrase_contour="descent"/"wave", редкие ноты, много пространства
  - Темпы: 60–78 BPM — медленно, тяжело, неотвратимо
  - Арпеджио: down / down_up — падающее движение

Musical arc:
  1. Marrow          — открывается как туман, тихие гранулы + редкий бас
  2. Sunder          — тяжёлый breakbeat, давящий педальный бас
  3. Pale Cartridge  — самое медленное, почти дрон, Locrian
  4. Corrode         — движение возвращается, Hungarian Minor, broken pattern
  5. Husk            — Phrygian Dominant, горькая мелодия, спад
  6. Erase           — финал, Double Harmonic, всё растворяется в тишине

Run:  .venv_dd/bin/python scratch/lorn_album.py
Out:  output/lorn/*.mid
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
random.seed(666)

from melodica.types import Scale, Mode, Quality, ChordLabel, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# ── GM programs — тёмная палитра ────────────────────────────────────────────
PAD_DARK    = 89   # Pad 2 (Warm)
PAD_VOICE   = 54   # Voice Oohs  — зловещий хор
SYNTH_LEAD  = 81   # Lead 1 (Square) — холодный синт
STRINGS     = 49   # String Ensemble 2
BASS_SYNTH  = 39   # Synth Bass 2 — тяжёлый
BASS_FRETLESS = 36 # Fretless Bass
FX_RAIN     = 97   # FX 1 (Rain) — атмосфера

OUT      = REPO / "output" / "lorn"
KEYNAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


# ── helpers ───────────────────────────────────────────────────────────────────

def _off(notes: list[NoteInfo], offset: float) -> list[NoteInfo]:
    return [NoteInfo(pitch=n.pitch, start=n.start + offset,
                     duration=n.duration, velocity=n.velocity) for n in notes]


def _clip_low(notes: list[NoteInfo], lo: int = 24) -> list[NoteInfo]:
    """Ensure nothing goes below MIDI lo (default C1)."""
    return [NoteInfo(pitch=max(lo, n.pitch), start=n.start,
                     duration=n.duration, velocity=n.velocity) for n in notes]


def _master(raw: dict, bpm: float, lufs: float = -13.0,
            gains: dict | None = None) -> tuple:
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update(gains or {
        "drums": 0.72, "bass": 0.80, "pad": 0.40,
        "texture": 0.35, "lead": 0.60,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    return MasteringDesk(target_lufs=lufs).apply_mastering(mixed)


def _chords(root: int, mode: Mode, dur: float,
            progression: list[tuple[int, Quality]]) -> list[ChordLabel]:
    n   = len(progression)
    seg = dur / n
    return [
        ChordLabel(root=(root + offset) % 12, quality=qual,
                   start=i * seg, duration=seg)
        for i, (offset, qual) in enumerate(progression)
    ]


# ── track builder ─────────────────────────────────────────────────────────────

def build_track(
    key: Scale,
    chords: list[ChordLabel],
    dur: float,
    *,
    # drums
    drum_kit: str       = "808",
    drum_pattern: str   = "breakbeat",
    drum_swing: float   = 0.58,
    drum_ghost_snare: float = 0.18,
    drum_ghost_ride: float  = 0.08,
    # bass
    bass_style: str     = "pedal_tone",
    bass_low: int       = 24,
    bass_high: int      = 48,
    bass_density: float = 0.55,
    bass_transpose: int = 0,
    # pad / texture
    pad_low: int        = 36,
    pad_high: int       = 60,
    pad_density: float  = 0.06,
    pad_overlap: float  = 1.2,
    nebula_variant: str = "granular",
    nebula_spread: int  = 10,
    nebula_dur: float   = 6.0,
    nebula_density: int = 4,
    nebula_low: int     = 36,
    nebula_high: int    = 60,
    # lead melody
    lead_density: float     = 0.04,
    lead_phrase: float      = 18.0,
    lead_low: int           = 48,
    lead_high: int          = 66,
    lead_bias: float        = -0.45,
    lead_contour: str       = "descent",
    lead_climax: str        = "auto",
    lead_smooth: float      = 0.78,
    lead_harmony_prob: float = 0.45,
    lead_steps_prob: float  = 0.80,
    lead_accent: str        = "natural",
    lead_offset: float      = 32.0,
    # arp (optional, may be absent)
    use_arp: bool           = False,
    arp_pattern: str        = "down",
    arp_low: int            = 36,
    arp_high: int           = 60,
    arp_density: float      = 0.07,
    arp_note_dur: float     = 2.5,
    arp_octaves: int        = 2,
) -> dict:
    # 808-drums — тяжёлый кит, слегка в свинг
    drums = ElectronicDrumsGenerator(
        GeneratorParams(density=0.9),
        kit=drum_kit,
        pattern=drum_pattern,
        groove_swing=drum_swing,
        ghost_snare_prob=drum_ghost_snare,
        ghost_ride_prob=drum_ghost_ride,
        choke_hats=True,
        auto_fills=True,
        envelope_gating=True,
    ).render(chords, key, dur)

    # суббас — тяжёлый, низкий
    bass = BassGenerator(
        GeneratorParams(density=bass_density, key_range_low=bass_low, key_range_high=bass_high),
        style=bass_style,
        transpose_octaves=bass_transpose,
    ).render(chords, key, dur)
    bass = _clip_low(bass, 24)

    # тёмный пэд — широко, долго, тихо
    pad = AmbientPadGenerator(
        GeneratorParams(density=pad_density, key_range_low=pad_low, key_range_high=pad_high),
        voicing="spread", overlap=pad_overlap,
    ).render(chords, key, dur)

    # гранулярная текстура — песок и туман
    texture = NebulaGenerator(
        GeneratorParams(density=0.06, key_range_low=nebula_low, key_range_high=nebula_high),
        variant=nebula_variant,
        density_notes=nebula_density,
        pitch_spread=nebula_spread,
        note_duration=nebula_dur,
        overlap=0.6,
        use_scale_tones=True,
    ).render(chords, key, dur)

    # редкая мелодия — появляется после паузы
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
    lead = _clip_low(lead, 36)

    result = {"drums": drums, "bass": bass, "pad": pad, "texture": texture, "lead": lead}

    if use_arp:
        arp = ArpeggiatorGenerator(
            GeneratorParams(density=arp_density, key_range_low=arp_low, key_range_high=arp_high),
            pattern=arp_pattern, note_duration=arp_note_dur, octaves=arp_octaves,
        ).render(chords, key, dur)
        arp = _clip_low(arp, 30)
        result["arp"] = arp

    return result


# ── 6 треков — тёмный арк «Ash & Iron» ──────────────────────────────────────
TRACKS = [
    # ── 1. Dusk Protocol ─────────────────────────────────────────────────────
    # Тихое открытие — гранулы и педальный бас. Phrygian, медленно.
    dict(
        name="01_Marrow", root=9, mode=Mode.PHRYGIAN, bpm=66, dur_beats=224,
        progression=[(0, Quality.MINOR), (1, Quality.MAJOR), (0, Quality.MINOR)],
        drum_kit="808",    drum_pattern="minimal",
        drum_swing=0.54,   drum_ghost_snare=0.10,
        bass_style="pedal_tone", bass_low=24, bass_high=45, bass_density=0.40,
        pad_low=36, pad_high=58, pad_density=0.05, pad_overlap=1.4,
        nebula_variant="granular", nebula_spread=8, nebula_dur=8.0, nebula_density=3,
        nebula_low=36, nebula_high=56,
        lead_density=0.03, lead_phrase=22.0, lead_low=48, lead_high=63,
        lead_bias=-0.50, lead_contour="descent", lead_climax="auto",
        lead_smooth=0.85, lead_harmony_prob=0.40, lead_steps_prob=0.82,
        lead_accent="natural", lead_offset=48.0,
        use_arp=False,
        gains={"drums": 0.60, "bass": 0.75, "pad": 0.45, "texture": 0.38, "lead": 0.58},
    ),
    # ── 2. Iron Lung ──────────────────────────────────────────────────────────
    # Главный удар альбома — тяжёлый breakbeat, давящий суббас.
    # Natural Minor, 72 BPM. Арпеджио падает вниз.
    dict(
        name="02_Sunder", root=2, mode=Mode.NATURAL_MINOR, bpm=72, dur_beats=216,
        progression=[(0, Quality.MINOR), (10, Quality.MAJOR),
                     (8, Quality.MAJOR), (5, Quality.MINOR)],
        drum_kit="808",    drum_pattern="breakbeat",
        drum_swing=0.60,   drum_ghost_snare=0.22, drum_ghost_ride=0.10,
        bass_style="root_fifth_octave", bass_low=24, bass_high=48, bass_density=0.65,
        pad_low=36, pad_high=60, pad_density=0.07, pad_overlap=1.0,
        nebula_variant="stasis", nebula_spread=9, nebula_dur=5.0, nebula_density=4,
        nebula_low=36, nebula_high=55,
        lead_density=0.05, lead_phrase=16.0, lead_low=48, lead_high=66,
        lead_bias=-0.40, lead_contour="wave", lead_climax="auto",
        lead_smooth=0.72, lead_harmony_prob=0.50, lead_steps_prob=0.78,
        lead_accent="strong_weak", lead_offset=28.0,
        use_arp=True, arp_pattern="down", arp_low=36, arp_high=60,
        arp_density=0.09, arp_note_dur=2.0, arp_octaves=2,
        gains={"drums": 0.78, "bass": 0.85, "pad": 0.38, "texture": 0.30, "lead": 0.62, "arp": 0.45},
    ),
    # ── 3. Void Signal ────────────────────────────────────────────────────────
    # Самое медленное. Locrian — нестабильность, тревога.
    # Почти дрон: minimal drums, stasis nebula, очень редкая мелодия.
    dict(
        name="03_Pale_Cartridge", root=7, mode=Mode.LOCRIAN, bpm=60, dur_beats=240,
        progression=[(0, Quality.DIMINISHED), (1, Quality.MAJOR),
                     (0, Quality.DIMINISHED), (8, Quality.MAJOR)],
        drum_kit="808",    drum_pattern="minimal",
        drum_swing=0.52,   drum_ghost_snare=0.08, drum_ghost_ride=0.04,
        bass_style="pedal_tone", bass_low=24, bass_high=42, bass_density=0.35,
        pad_low=30, pad_high=54, pad_density=0.05, pad_overlap=1.8,
        nebula_variant="stasis", nebula_spread=12, nebula_dur=10.0, nebula_density=3,
        nebula_low=30, nebula_high=52,
        lead_density=0.025, lead_phrase=24.0, lead_low=45, lead_high=60,
        lead_bias=-0.60, lead_contour="descent", lead_climax="auto",
        lead_smooth=0.90, lead_harmony_prob=0.35, lead_steps_prob=0.88,
        lead_accent="natural", lead_offset=60.0,
        use_arp=False,
        gains={"drums": 0.55, "bass": 0.70, "pad": 0.50, "texture": 0.42, "lead": 0.55},
    ),
    # ── 4. Acid Rain ──────────────────────────────────────────────────────────
    # Hungarian Minor — экзотическое, острое. Движение возвращается.
    # Breakbeat + down_up арп, более плотная мелодия.
    dict(
        name="04_Corrode", root=5, mode=Mode.HUNGARIAN_MINOR, bpm=76, dur_beats=208,
        progression=[(0, Quality.MINOR), (6, Quality.MAJOR),
                     (5, Quality.MINOR), (8, Quality.MAJOR)],
        drum_kit="808",    drum_pattern="breakbeat",
        drum_swing=0.62,   drum_ghost_snare=0.25, drum_ghost_ride=0.12,
        bass_style="root_fifth_octave", bass_low=28, bass_high=52, bass_density=0.70,
        pad_low=36, pad_high=60, pad_density=0.07, pad_overlap=0.9,
        nebula_variant="cascade", nebula_spread=10, nebula_dur=4.0, nebula_density=5,
        nebula_low=36, nebula_high=58,
        lead_density=0.06, lead_phrase=14.0, lead_low=48, lead_high=68,
        lead_bias=-0.30, lead_contour="wave", lead_climax="auto",
        lead_smooth=0.65, lead_harmony_prob=0.55, lead_steps_prob=0.75,
        lead_accent="syncopated", lead_offset=24.0,
        use_arp=True, arp_pattern="down_up", arp_low=36, arp_high=62,
        arp_density=0.10, arp_note_dur=1.75, arp_octaves=2,
        gains={"drums": 0.80, "bass": 0.82, "pad": 0.36, "texture": 0.32, "lead": 0.65, "arp": 0.48},
    ),
    # ── 5. Ash ────────────────────────────────────────────────────────────────
    # Phrygian Dominant — горькая мелодия, чуть восточный привкус.
    # Спад: барабаны тише, бас медленнее. Арп исчезает.
    dict(
        name="05_Husk", root=0, mode=Mode.PHRYGIAN_DOMINANT, bpm=68, dur_beats=220,
        progression=[(0, Quality.MAJOR), (1, Quality.MAJOR),
                     (10, Quality.MINOR), (0, Quality.MAJOR)],
        drum_kit="808",    drum_pattern="minimal",
        drum_swing=0.57,   drum_ghost_snare=0.14, drum_ghost_ride=0.06,
        bass_style="chord_tone", bass_low=26, bass_high=48, bass_density=0.50,
        pad_low=33, pad_high=57, pad_density=0.06, pad_overlap=1.3,
        nebula_variant="swell", nebula_spread=11, nebula_dur=7.0, nebula_density=4,
        nebula_low=33, nebula_high=56,
        lead_density=0.05, lead_phrase=18.0, lead_low=45, lead_high=65,
        lead_bias=-0.35, lead_contour="descent", lead_climax="auto",
        lead_smooth=0.80, lead_harmony_prob=0.50, lead_steps_prob=0.82,
        lead_accent="natural", lead_offset=30.0,
        use_arp=False,
        gains={"drums": 0.65, "bass": 0.78, "pad": 0.44, "texture": 0.38, "lead": 0.68},
    ),
    # ── 6. Ghost Protocol ─────────────────────────────────────────────────────
    # Double Harmonic — самый экзотический лад. Финал, всё растворяется.
    # Очень медленно. Drums почти нет. Только бас, туман, одинокая мелодия.
    dict(
        name="06_Erase", root=9, mode=Mode.DOUBLE_HARMONIC, bpm=60, dur_beats=256,
        progression=[(0, Quality.MAJOR), (1, Quality.DIMINISHED),
                     (8, Quality.MAJOR), (0, Quality.MAJOR)],
        drum_kit="808",    drum_pattern="minimal",
        drum_swing=0.50,   drum_ghost_snare=0.06, drum_ghost_ride=0.03,
        bass_style="pedal_tone", bass_low=24, bass_high=42, bass_density=0.30,
        pad_low=30, pad_high=55, pad_density=0.06, pad_overlap=2.0,
        nebula_variant="stasis", nebula_spread=14, nebula_dur=12.0, nebula_density=3,
        nebula_low=30, nebula_high=54,
        lead_density=0.03, lead_phrase=26.0, lead_low=43, lead_high=62,
        lead_bias=-0.65, lead_contour="descent", lead_climax="auto",
        lead_smooth=0.92, lead_harmony_prob=0.35, lead_steps_prob=0.90,
        lead_accent="natural", lead_offset=64.0,
        use_arp=False,
        gains={"drums": 0.48, "bass": 0.68, "pad": 0.52, "texture": 0.46, "lead": 0.60},
    ),
]

INST_NAME = {
    PAD_DARK: "pad_warm", PAD_VOICE: "pad_voice",
    SYNTH_LEAD: "lead_square", STRINGS: "strings",
    BASS_SYNTH: "bass_synth", BASS_FRETLESS: "bass_fretless",
}


def main() -> None:
    print("=" * 76)
    print("  « M A R R O W »  —  6-track dark low-register album")
    print("  Lorn-style · Phrygian/Locrian/Double Harmonic · MIDI 24-72")
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
            drum_kit           = t.get("drum_kit", "808"),
            drum_pattern       = t.get("drum_pattern", "breakbeat"),
            drum_swing         = t.get("drum_swing", 0.58),
            drum_ghost_snare   = t.get("drum_ghost_snare", 0.18),
            drum_ghost_ride    = t.get("drum_ghost_ride", 0.08),
            bass_style         = t.get("bass_style", "pedal_tone"),
            bass_low           = t.get("bass_low", 24),
            bass_high          = t.get("bass_high", 48),
            bass_density       = t.get("bass_density", 0.55),
            bass_transpose     = t.get("bass_transpose", 0),
            pad_low            = t.get("pad_low", 36),
            pad_high           = t.get("pad_high", 60),
            pad_density        = t.get("pad_density", 0.06),
            pad_overlap        = t.get("pad_overlap", 1.2),
            nebula_variant     = t.get("nebula_variant", "granular"),
            nebula_spread      = t.get("nebula_spread", 10),
            nebula_dur         = t.get("nebula_dur", 6.0),
            nebula_density     = t.get("nebula_density", 4),
            nebula_low         = t.get("nebula_low", 36),
            nebula_high        = t.get("nebula_high", 60),
            lead_density       = t.get("lead_density", 0.04),
            lead_phrase        = t.get("lead_phrase", 18.0),
            lead_low           = t.get("lead_low", 48),
            lead_high          = t.get("lead_high", 66),
            lead_bias          = t.get("lead_bias", -0.45),
            lead_contour       = t.get("lead_contour", "descent"),
            lead_climax        = t.get("lead_climax", "auto"),
            lead_smooth        = t.get("lead_smooth", 0.78),
            lead_harmony_prob  = t.get("lead_harmony_prob", 0.45),
            lead_steps_prob    = t.get("lead_steps_prob", 0.80),
            lead_accent        = t.get("lead_accent", "natural"),
            lead_offset        = t.get("lead_offset", 32.0),
            use_arp            = t.get("use_arp", False),
            arp_pattern        = t.get("arp_pattern", "down"),
            arp_low            = t.get("arp_low", 36),
            arp_high           = t.get("arp_high", 60),
            arp_density        = t.get("arp_density", 0.07),
            arp_note_dur       = t.get("arp_note_dur", 2.5),
            arp_octaves        = t.get("arp_octaves", 2),
        )

        final, cc = _master(raw, bpm, gains=t.get("gains"))
        out = OUT / f"{t['name']}.mid"

        instruments: dict[str, int] = {
            "drums":   0,           # channel 9 (drums)
            "bass":    BASS_SYNTH,
            "pad":     PAD_DARK,
            "texture": PAD_VOICE,
            "lead":    SYNTH_LEAD,
        }
        if "arp" in raw:
            instruments["arp"] = STRINGS

        export_multitrack_midi(final, str(out), bpm=bpm, key=key,
                               instruments=instruments, cc_events=cc)

        all_notes = [n for k, v in final.items() if k != "drums" for n in v]
        lo = min((n.pitch for n in all_notes), default=0)
        hi = max((n.pitch for n in all_notes), default=0)
        prog_str = "→".join(
            f"{KEYNAMES[(t['root'] + o) % 12]}" for o, _ in t["progression"]
        )
        has_arp = "arp" in raw
        print(
            f"\n✦ {t['name']}"
            f"  ({KEYNAMES[t['root']]} {t['mode'].name} · {bpm} BPM · ~{secs:.0f}s)\n"
            f"  drums={t.get('drum_pattern','?')}  bass={t.get('bass_style','?')}"
            f"  nebula={t.get('nebula_variant','?')}"
            + (f"  arp={t.get('arp_pattern','?')}" if has_arp else "")
            + f"\n  chords={prog_str}  register {lo}–{hi} (MIDI)\n"
            + "  notes: " + ", ".join(f"{k}={len(v)}" for k, v in raw.items())
            + f"\n  ✓ {out.name}"
        )

    print("\n" + "=" * 76)
    print(f"  ALBUM DONE · 6 tracks · ~{total_s:.0f}s (~{total_s / 60:.1f} min)")
    print(f"  Output: output/lorn/")
    print("=" * 76)


if __name__ == "__main__":
    main()
