"""
grand_30min.py — «Архив Бесконечности» (Archive of Infinity)
=============================================================
Grand 30-minute orchestral suite in 12 movements across six harmonic worlds.
Each movement = INTRO → VERSE → CLIMAX → OUTRO structure with full ensemble.

Harmonic worlds:
  I   Hungarian Minor  — dark, augmented seconds, gypsy fire
  II  Phrygian         — modal, Spanish / ancient, tense finality
  III Lydian           — bright, floating, otherworldly
  IV  Double Harmonic  — Byzantine, exotic tension
  V   Natural Minor    — classical, melancholic
  VI  Harmonic Minor   — yearning, cinematic resolution

Run with:
    .venv_dd/bin/python scratch/grand_30min.py
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS
from melodica.generators import (
    ChordGenerator, StringsEnsembleGenerator, AmbientPadGenerator,
    BassGenerator, MelodyGenerator,
)
from melodica.generators.orchestral_strings import ViolinGenerator, CelloGenerator
from melodica.generators.orchestral_brass import TromboneGenerator, FrenchHornGenerator
from melodica.generators.orchestral_woodwinds import FluteGenerator, ClarinetGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.rhythm import ProbabilisticRhythmGenerator
from melodica.types import Scale, Mode, SectionRole, SectionFunction
from melodica.midi import export_multitrack_midi

NOTE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
QSHORT = {
    "MAJOR": "", "MINOR": "m", "DIMINISHED": "dim", "AUGMENTED": "+",
    "DOMINANT7": "7", "MAJOR7": "maj7", "MINOR7": "m7", "MINOR_MAJOR7": "mMaj7",
    "SUSPENDED4": "sus4", "SUSPENDED2": "sus2",
    "DIMINISHED7": "dim7", "HALF_DIMINISHED": "m7b5", "DOMINANT9": "9",
}

ALL_TRACKS = [
    "Grand_Piano", "Violin_I", "Cello", "Pizz_Strings",
    "French_Horn", "Trombone", "Clarinet", "Flute_Lead",
    "Harp", "Choir_Aahs", "Dark_Pad", "Contrabass", "Counter_Melody",
]


def _mute(*keep: str) -> list[str]:
    return [t for t in ALL_TRACKS if t not in keep]


def _part(
    name: str, role: str, function: str,
    root: int, mode: Mode, tempo: int,
    ts: tuple[int, int], bars: int,
    mute: list[str] | None = None,
    density: dict[str, float] | None = None,
) -> IdeaPart:
    return IdeaPart(
        name=f"{name}_{role}",
        bars=bars,
        scale=Scale(root, mode),
        tempo=tempo,
        time_signature=ts,
        progression_type="coupled_hmm",
        section_type=SectionRole[role],
        section_function=SectionFunction[function],
        track_mute=mute or [],
        track_density=density or {},
    )


def _movement_sections(m: dict) -> list[IdeaPart]:
    name, root, mode = m["name"], m["root"], m["mode"]
    tempo, ts, b = m["tempo"], m["ts"], m["bars"]
    return [
        _part(name, "INTRO", "BUILD", root, mode, tempo, ts, b["intro"],
              mute=_mute("Grand_Piano", "Contrabass", "Harp", "Dark_Pad"),
              density={"Grand_Piano": 0.40, "Contrabass": 0.35, "Harp": 0.30, "Dark_Pad": 0.25}),
        _part(name, "VERSE", "BUILD", root, mode, tempo, ts, b["verse"],
              mute=_mute("Grand_Piano", "Violin_I", "Pizz_Strings",
                         "Dark_Pad", "Contrabass", "Flute_Lead", "Harp")),
        _part(name, "CLIMAX", "SUSTAIN", root, mode, tempo, ts, b["climax"],
              mute=[],
              density={"Grand_Piano": 0.95, "Violin_I": 0.90, "Trombone": 0.85,
                       "French_Horn": 0.80, "Choir_Aahs": 0.75,
                       "Flute_Lead": 0.80, "Counter_Melody": 0.65}),
        _part(name, "OUTRO", "FADE", root, mode, tempo, ts, b["outro"],
              mute=_mute("Grand_Piano", "Violin_I", "Dark_Pad", "Contrabass", "Harp"),
              density={"Grand_Piano": 0.40, "Violin_I": 0.45,
                       "Dark_Pad": 0.30, "Contrabass": 0.25, "Harp": 0.25}),
    ]


def label(c) -> str:
    q = QSHORT.get(c.quality.name, c.quality.name)
    inv = f"/{NOTE[c.bass]}" if getattr(c, "bass", None) and c.bass != c.root else ""
    return f"{NOTE[c.root]}{q}{inv}"


TRACKS_COMMON = [
    TrackConfig(
        name="Grand_Piano",
        generator=ChordGenerator(
            voicing="closed", add_bass_note=-2,
            rhythm=ProbabilisticRhythmGenerator(
                grid_resolution=0.5, density=0.70, downbeat_weight=0.35, gate=0.60, seed=42
            ),
        ),
        instrument="piano", density=0.90,
    ),
    TrackConfig(
        name="Violin_I",
        generator=ViolinGenerator(articulation="legato", dynamic_curve="arch", vibrato=True),
        instrument="strings", density=0.75,
    ),
    TrackConfig(
        name="Cello",
        generator=CelloGenerator(articulation="legato", dynamic_curve="swell", bass_voice=True),
        instrument="strings", density=0.65, octave_shift=-1,
    ),
    TrackConfig(
        name="Pizz_Strings",
        generator=StringsPizzicatoGenerator(pattern="ostinato", section_divisi=2),
        instrument="strings", density=0.60, octave_shift=-1,
    ),
    TrackConfig(
        name="French_Horn",
        generator=FrenchHornGenerator(articulation="sustained", dynamic_curve="swell"),
        instrument="brass", density=0.60,
    ),
    TrackConfig(
        name="Trombone",
        generator=TromboneGenerator(articulation="sustained", dynamic_curve="flat"),
        instrument="brass", density=0.55, octave_shift=-1,
    ),
    TrackConfig(
        name="Clarinet",
        generator=ClarinetGenerator(articulation="legato", dynamic_curve="arch"),
        instrument="woodwind", density=0.55,
    ),
    TrackConfig(
        name="Flute_Lead",
        generator_type="melody",
        generator=MelodyGenerator(
            prefer_chord_tones=0.65, phrase_contour="arch",
            note_range_low=72, note_range_high=96,
            allow_2nd=True, allow_7th=True,
        ),
        instrument="flute", density=0.65,
    ),
    TrackConfig(
        name="Harp",
        generator=HarpGenerator(pattern="arpeggio", direction="up", octave_span=2),
        instrument="harp", density=0.50,
    ),
    TrackConfig(
        name="Choir_Aahs",
        generator=ChoirAahsGenerator(voice_count=4, vibrato=True, dynamics="mp"),
        instrument="choir", density=0.55,
    ),
    TrackConfig(
        name="Dark_Pad",
        generator=AmbientPadGenerator(voicing="spread"),
        instrument="dark_pad", density=0.50, octave_shift=-1,
    ),
    TrackConfig(
        name="Contrabass",
        generator=BassGenerator(style="root_only"),
        instrument="contrabass", density=0.65, octave_shift=-2,
    ),
    TrackConfig(
        name="Counter_Melody",
        generator=CountermelodyGenerator(motion_preference="contrary", interval_limit=12),
        instrument="oboe", density=0.50,
    ),
]

# ──────────────────────────────────────────────────────────────────────────────
# 12 MOVEMENTS — ~30 MINUTES TOTAL
# duration_sec = total_bars × beats_per_bar × 60 / tempo
# ──────────────────────────────────────────────────────────────────────────────
MOVEMENTS = [
    # I. Hungarian Minor world
    {"name": "01_Dark_Overture",       "root": 2,  "mode": Mode.HUNGARIAN_MINOR,
     "tempo": 60,  "ts": (4, 4), "bars": {"intro": 4,  "verse": 8,  "climax": 12, "outro": 4}},
    {"name": "02_Gypsy_Tempest",       "root": 9,  "mode": Mode.HUNGARIAN_MINOR,
     "tempo": 104, "ts": (4, 4), "bars": {"intro": 4,  "verse": 12, "climax": 16, "outro": 4}},

    # II. Phrygian world
    {"name": "03_Ancient_Threshold",   "root": 4,  "mode": Mode.PHRYGIAN,
     "tempo": 56,  "ts": (4, 4), "bars": {"intro": 6,  "verse": 12, "climax": 16, "outro": 6}},
    {"name": "04_Iberian_Fire",        "root": 0,  "mode": Mode.PHRYGIAN,
     "tempo": 120, "ts": (3, 4), "bars": {"intro": 6,  "verse": 12, "climax": 18, "outro": 6}},

    # III. Lydian world
    {"name": "05_Celestial_Drift",     "root": 5,  "mode": Mode.LYDIAN,
     "tempo": 72,  "ts": (4, 4), "bars": {"intro": 4,  "verse": 10, "climax": 14, "outro": 4}},
    {"name": "06_Starfield_Canon",     "root": 7,  "mode": Mode.LYDIAN,
     "tempo": 88,  "ts": (4, 4), "bars": {"intro": 6,  "verse": 12, "climax": 16, "outro": 6}},

    # IV. Double Harmonic (Byzantine)
    {"name": "07_Byzantine_Gate",      "root": 0,  "mode": Mode.DOUBLE_HARMONIC,
     "tempo": 76,  "ts": (4, 4), "bars": {"intro": 4,  "verse": 10, "climax": 14, "outro": 4}},
    {"name": "08_Silk_Road_Elegy",     "root": 5,  "mode": Mode.DOUBLE_HARMONIC,
     "tempo": 54,  "ts": (4, 4), "bars": {"intro": 4,  "verse": 8,  "climax": 12, "outro": 4}},

    # V. Natural Minor
    {"name": "09_Moonlit_Plains",      "root": 9,  "mode": Mode.NATURAL_MINOR,
     "tempo": 66,  "ts": (4, 4), "bars": {"intro": 4,  "verse": 10, "climax": 14, "outro": 4}},
    {"name": "10_Autumn_Fugue",        "root": 2,  "mode": Mode.NATURAL_MINOR,
     "tempo": 96,  "ts": (4, 4), "bars": {"intro": 4,  "verse": 12, "climax": 16, "outro": 4}},

    # VI. Harmonic Minor — grand finale
    {"name": "11_Yearning_Tide",       "root": 11, "mode": Mode.HARMONIC_MINOR,
     "tempo": 60,  "ts": (4, 4), "bars": {"intro": 6,  "verse": 12, "climax": 18, "outro": 6}},
    {"name": "12_Infinite_Archive",    "root": 7,  "mode": Mode.HARMONIC_MINOR,
     "tempo": 48,  "ts": (4, 4), "bars": {"intro": 8,  "verse": 16, "climax": 24, "outro": 8}},
]

instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in TRACKS_COMMON}


def main() -> None:
    print("=" * 80)
    print("  А Р Х И В   Б Е С К О Н Е Ч Н О С Т И  —  «Archive of Infinity»")
    print("  Grand 30-minute orchestral suite · 12 movements · 6 harmonic worlds")
    print("=" * 80)

    out_dir = Path("output/grand_30min")
    out_dir.mkdir(exist_ok=True, parents=True)

    total_duration_s = 0.0
    chord_report = []

    for idx, m in enumerate(MOVEMENTS, 1):
        mode_name = m["mode"].name.replace("_", " ").title()
        root_name = NOTE[m["root"]]
        total_bars = sum(m["bars"].values())
        beats = m["ts"][0]
        dur_s = total_bars * beats * 60 / m["tempo"]
        total_duration_s += dur_s

        print(f"\n[{idx:02d}/12] ✦ {m['name']}  ({root_name} {mode_name})  "
              f"tempo={m['tempo']}  {total_bars} bars  ~{dur_s:.0f}s")

        parts = _movement_sections(m)
        cfg = IdeaToolConfig(
            style="cinematic_hybrid",
            workflow="generate_melody_then_harmonize",
            scale=Scale(m["root"], m["mode"]),
            parts=parts,
            tracks=TRACKS_COMMON,
            use_voice_leading=True,
            use_tension_curve=True,
        )

        tool = IdeaTool(cfg)
        notes_dict = tool.generate()

        chords = getattr(tool, "_chords", [])
        chord_str = " → ".join(label(c) for c in chords)
        print(f"         ♩ Harmony: {chord_str}")
        chord_report.append((m["name"], root_name, mode_name, chord_str))

        tracks_data = {
            k: v for k, v in notes_dict.items()
            if not k.startswith("_") and isinstance(v, list)
        }
        filepath = out_dir / f"{m['name']}.mid"
        export_multitrack_midi(
            tracks_data, str(filepath),
            bpm=m["tempo"], time_sig=m["ts"],
            instruments=instruments_map,
        )
        print(f"         ✓  {filepath.name}")

    print("\n" + "=" * 80)
    print(f"  TOTAL DURATION: ~{total_duration_s:.0f}s  (~{total_duration_s/60:.1f} minutes)")
    print(f"  Output: output/grand_30min/")
    print("=" * 80)
    print("\n  ═══ FULL CHORD PROGRESSION REPORT ═══\n")
    for name, root, mode, chords in chord_report:
        print(f"  ♩ {name}  [{root} {mode}]")
        print(f"    {chords}\n")
    print("=" * 80)
    print("  PRODUCTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
