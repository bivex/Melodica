---
name: write-electronic-album
description: Generate electronic music albums (techno, house, trap, witch house, synthwave). Uses section-based arrangement with produce_track pipeline, ElectronicDrumsGenerator, 808 bass, dark pads, and FX.
---

# Write Electronic Album

Use this skill for techno, house, deep house, acid, industrial, trap, drill, witch house, and other electronic music. Uses the **section-based arrangement** pattern with `produce_track()` for auto-mix/master.

## 1. Architecture

Each album has:
- **Per-track build function** (`match`/`case` pattern) returning `(generator, modifiers)`
- **Section list** defining arrangement: `[("Section", bars, ["track_names"])]`
- **Track registry** with scale, sections, build function, instruments, BPM, mood

## 2. Required Imports

```python
import sys, random, warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo, KeyLabel, MusicTimeline
from melodica.generators import GeneratorParams
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.lofi_hiphop import LoFiHipHopGenerator
from melodica.generators.beat_repeat import BeatRepeatGenerator
from melodica.generators.filter_sweep import FilterSweepGenerator
from melodica.harmonize import HMM3Harmonizer
from melodica.modifiers import (
    HumanizeModifier, VelocityScalingModifier,
    LimitNoteRangeModifier, SwingController, CrescendoModifier,
    ModifierContext,
)
from melodica.composer import ArticulationEngine
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.render_context import RenderContext
```

## 3. Harmony Engine

```python
def harmonize(scale, bars, bpb=4):
    harmonizer = HMM3Harmonizer(
        beam_width=5, melody_weight=0.20,
        secondary_dom_weight=0.10, extension_weight=0.06,
        repetition_penalty=0.10, cadence_weight=0.12,
    )
    degs = scale.degrees()
    contour = []
    for bar in range(bars):
        pos = bar % 8
        if pos < 2: pc = int(degs[0])
        elif pos < 4: pc = int(degs[min(2, len(degs) - 1)])
        elif pos < 6: pc = int(degs[min(4, len(degs) - 1)])
        else: pc = int(degs[0]) if random.random() < 0.7 else int(degs[min(5, len(degs) - 1)])
        contour.append(NoteInfo(pitch=44 + pc, start=bar * bpb, duration=bpb - 0.05, velocity=52))
    chords = harmonizer.harmonize(contour, scale, bars * bpb)
    while len(chords) < bars:
        chords.append(chords[-1] if chords else ChordLabel(
            root=int(degs[0]), quality=Quality.MINOR, start=len(chords) * bpb, duration=bpb))
    return chords
```

## 4. Build Function Pattern

```python
def build_track(name):
    mods = []
    params = GeneratorParams(density=0.50)

    match name:
        case "909_drums":
            gen = ElectronicDrumsGenerator(
                params=params,
                kit="909",                  # "909", "808", "linn", "ethnic", "industrial"
                pattern="four_on_floor",     # "four_on_floor", "techno", "breakbeat", "minimal"
                sidechain=True,
                sidechain_depth=0.40,
                groove_swing=0.57,           # 0.50 = straight, 0.57 = swung
                swing_grid=0.25,
                choke_hats=True,
                ghost_snare_prob=0.20,
                section_type="verse",        # "intro", "verse", "chorus", "outro"
                auto_fills=True,
                transient_ducking=True,
                ducking_duration=0.020,
                envelope_gating=True,
                mute_boundaries=False,
                pan_mode="sweep_lr",         # "sweep_lr", "sweep_rl", "alternate", "off"
                flam_probability=0.04,
                drag_probability=0.02,
            )
            mods.append(VelocityScalingModifier(scale=0.78))
            mods.append(HumanizeModifier(timing_std=0.012, velocity_std=3))

        case "bass_808":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_basic",         # "trap_basic", "rolling", "drill_sliding"
                slide_type="overlap",         # "overlap", "chromatic", "octave_jump"
                slide_probability=0.30,
                slide_curve="exponential",    # "exponential", "logarithmic", "octave_whip"
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=28, high=52))
            mods.append(VelocityScalingModifier(scale=0.80))

        case "dark_pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.20),
                mode="minor_pad",             # "minor_pad", "tritone_drone", "phrygian_pad", "dim_cluster", "chromatic_pad"
                chord_dur=4.0,
                velocity_level=0.14,
                register="mid",              # "low", "mid", "high"
                overlap=0.5,
            )

        case "arp":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.55),
                pattern="up",                # "up", "down", "up_down", "converge"
                note_duration=0.25,
            )
            mods += [
                HumanizeModifier(timing_std=0.008, velocity_std=2),
                VelocityScalingModifier(scale=0.60),
                LimitNoteRangeModifier(low=60, high=84),
            ]

        case "acid_bass":
            gen = SynthBassGenerator(
                params=params,
                waveform="acid",             # "acid", "saw", "square", "sine"
                pattern="acid_line",         # "acid_line", "plucked"
                slide_probability=0.20,
            )
            mods += [
                HumanizeModifier(timing_std=0.015, velocity_std=5),
                VelocityScalingModifier(scale=0.70),
                LimitNoteRangeModifier(low=32, high=55),
            ]

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.40),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",   # "exponential", "linear"
                peak_velocity=100,
            )

        case "impact":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.25),
                impact_type="boom",           # "boom"
                tail_length=4.0,
                pitch_drop=18,
            )

        case "hats":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.35),
                pattern="trap_eighth",       # "trap_eighth", "drill_stutter", "sparse", "techno_straight"
                roll_density=0.30,
                open_hat_probability=0.10,
                pan_mode="sweep_lr",
            )
            mods.append(SwingController(swing_ratio=0.57, grid=0.5))

        case "ghost_snare":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.25),
                target="snare",
                pattern="hiphop",
                ghost_velocity=20,
                ghost_density=0.35,
                placement="sixteenth",
            )

        case _:
            return None

    return gen, mods
```

## 5. Section Arrangement

```python
SECTIONS = [
    ("Intro",      4, ["dark_pad", "drums_hint"]),
    ("Verse 1",    8, ["909_drums", "bass_808", "dark_pad", "arp"]),
    ("Buildup",    4, ["dark_pad", "arp_build", "hats_only", "riser"]),
    ("Drop",       8, ["909_drums_hard", "bass_808_slide", "dark_pad", "arp", "ghost_snare"]),
    ("Break",      4, ["dark_pad", "acid_bass_solo"]),
    ("Verse 2",    8, ["909_drums", "bass_808", "dark_pad", "arp"]),
    ("Drop 2",     8, ["909_drums_hard", "bass_808_slide", "dark_pad", "arp", "ghost_snare", "riser"]),
    ("Outro",      4, ["dark_pad", "drums_out", "impact"]),
]
```

## 6. Track Registry and Production

```python
TRACKS = [
    {
        "title": "01_Track_Name",
        "scale": Scale(root=9, mode=Mode.NATURAL_MINOR),
        "sections": SECTIONS,
        "build": build_track,
        "instruments": {"909_drums": 0, "bass_808": 38, "dark_pad": 92, ...},
        "bpm": 127,
        "mood": Mood.INTIMATE,       # Mood.INTIMATE, Mood.AGGRESSIVE, Mood.EXPERIMENTAL, Mood.CINEMATIC
        "perc": {"909_drums"},       # Set of percussion track names
        "key_label": "Am",
    },
]

def main():
    album_dir = Path("output/album_name")
    album_dir.mkdir(exist_ok=True, parents=True)

    for t in TRACKS:
        raw, cc, total_beats = generate_track(t["scale"], t["sections"], t["build"])
        out_path = album_dir / f"{t['title']}.mid"
        produce_track(
            tracks=raw, bpm=t["bpm"], instruments=t["instruments"],
            path=str(out_path), mood=t["mood"], key=t["scale"],
            cc_events=cc, verbose=False,
        )

if __name__ == "__main__":
    main()
```

## 7. BPM Guide by Subgenre

| Subgenre | BPM |
|---|---|
| Deep House | 120-125 |
| Melodic Techno | 125-130 |
| Acid Techno | 130-135 |
| Hard Techno / Industrial | 135-145 |
| Trap / Drill | 130-160 |
| Witch House | 100-120 |
| Lo-Fi Electronic | 70-90 |
| Synthwave | 100-120 |

## 8. Common DarkPad Modes

| Mode | Mood |
|---|---|
| `"minor_pad"` | Standard dark, moody |
| `"phrygian_pad"` | Tense, Spanish-flavored |
| `"tritone_drone"` | Dissonant, unsettling |
| `"dim_cluster"` | Cluster chord tension |
| `"chromatic_pad"` | Atonal, industrial |

## 9. Common Pitfalls

| Issue | Fix |
|---|---|
| `RhythmGenerator` not found | Don't import — use `groove_swing` param in ElectronicDrumsGenerator |
| 808 bass too high | Always add `LimitNoteRangeModifier(low=28, high=52)` |
| Pads too loud | Use `VelocityScalingModifier(scale=0.25)` for pads |
| Drums sound robotic | Add `HumanizeModifier(timing_std=0.012, velocity_std=3)` |
| No swing feel | Add `SwingController(swing_ratio=0.57, grid=0.25)` |
| Sections don't connect | Use `beat_offset` accumulation in `generate_track()` |

## 10. Running

```bash
python scripts/albums/electronic/album_name.py
```
