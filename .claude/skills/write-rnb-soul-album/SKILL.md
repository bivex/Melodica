---
name: write-rnb-soul-album
description: Generate R&B, Soul, Neo-Soul, Trap-Soul, New Jack Swing, Gospel-Soul, and Lo-Fi R&B albums. Uses section-based arrangement with produce_track pipeline, vocal generators (melisma, chops, oohs, adlibs), groove drums, slap bass, and swing modifiers.
---

# Write R&B / Soul Album

Use this skill for R&B, Neo-Soul, New Jack Swing, Trap-Soul, Gospel-Soul, Lo-Fi R&B, and related vocal-driven genres. Uses the **section-based arrangement** pattern with `produce_track()` for auto-mix/master.

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

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.groove import GrooveGenerator
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.bass_slap import BassSlapGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.modern_chord import ModernChordPatternGenerator
from melodica.generators.organ_drawbars import OrganDrawbarsGenerator
from melodica.generators.backbeat import BackbeatGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.vocal_melisma import VocalMelismaGenerator
from melodica.generators.vocal_oohs import VocalOohsGenerator
from melodica.generators.vocal_adlibs import VocalAdlibsGenerator
from melodica.generators.vocal_melody_auto import VocalMelodyAutoGenerator
from melodica.generators.piano_run import PianoRunGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.beat_repeat import BeatRepeatGenerator
from melodica.generators.filter_sweep import FilterSweepGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.lofi_hiphop import LoFiHipHopGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.guitar_strumming import GuitarStrummingGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.harmonize import HMM3Harmonizer
from melodica.modifiers import (
    HumanizeModifier, VelocityScalingModifier,
    LimitNoteRangeModifier, SwingController, CrescendoModifier,
    ModifierContext,
)
from melodica.composer import ArticulationEngine
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.render_context import RenderContext
from melodica.rhythm.groove_template import SWING_60, LAID_BACK, HIP_HOP, SHUFFLE, FUNK, PUSH
```

## 3. Harmony Engine

```python
def harmonize(scale, bars, bpb=4):
    harmonizer = HMM3Harmonizer(
        beam_width=5, melody_weight=0.22,
        secondary_dom_weight=0.12, extension_weight=0.10,
        repetition_penalty=0.06, cadence_weight=0.10,
    )
    degs = scale.degrees()
    contour = []
    for b in range(bars):
        p = b % 4
        if p == 0: pc = int(degs[0])
        elif p == 1: pc = int(degs[min(3, len(degs) - 1)])
        elif p == 2: pc = int(degs[min(4, len(degs) - 1)] if len(degs) > 4 else degs[min(2, len(degs) - 1)])
        else: pc = int(degs[0]) if random.random() < 0.5 else int(degs[min(2, len(degs) - 1)])
        contour.append(NoteInfo(pitch=46 + pc, start=b * bpb, duration=bpb - 0.1, velocity=48))
    chords = harmonizer.harmonize(contour, scale, bars * bpb)
    while len(chords) < bars:
        chords.append(
            chords[-1] if chords
            else ChordLabel(root=int(degs[0]), quality=Quality.MINOR,
                            start=len(chords) * bpb, duration=bpb))
    return chords
```

## 4. Build Function Pattern

```python
def build_track(name):
    mods = []
    params = GeneratorParams(density=0.45)

    match name:
        case "keys_comp":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.38), comp_style="jazz",
                voicing_type="rootless", accent_pattern="syncopated", chord_density=0.65,
            )
            mods += [LimitNoteRangeModifier(low=48, high=76), VelocityScalingModifier(scale=0.45),
                     HumanizeModifier(timing_std=0.02, velocity_std=5),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "keys_hook":
            gen = ModernChordPatternGenerator(
                params=GeneratorParams(density=0.44), extension="maj9",
                stab_pattern="syncopated", voicing="open",
            )
            mods += [LimitNoteRangeModifier(low=48, high=76), VelocityScalingModifier(scale=0.52),
                     HumanizeModifier(timing_std=0.015, velocity_std=4),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "bass_walk":
            gen = WalkingBassGenerator(
                params=GeneratorParams(density=0.45), approach_style="mixed",
                connect_roots=True, add_chromatic_passing=True, swing_eighth_ratio=0.65,
            )
            mods += [LimitNoteRangeModifier(low=28, high=52), VelocityScalingModifier(scale=0.78),
                     HumanizeModifier(timing_std=0.015, velocity_std=5)]

        case "bass_slap":
            gen = BassSlapGenerator(
                params=GeneratorParams(density=0.50), slap_pattern="funky",
                ghost_note_prob=0.35, pop_probability=0.40, octave_range=2,
            )
            mods += [LimitNoteRangeModifier(low=28, high=52), VelocityScalingModifier(scale=0.82),
                     HumanizeModifier(timing_std=0.015, velocity_std=5)]

        case "groove":
            gen = GrooveGenerator(
                params=GeneratorParams(density=0.45), groove_pattern="soul",
                ghost_note_vel=30, accent_vel=105,
            )
            mods.append(HumanizeModifier(timing_std=0.01, velocity_std=6))

        case "groove_full":
            gen = GrooveGenerator(
                params=GeneratorParams(density=0.55), groove_pattern="funk_1",
                ghost_note_vel=32, accent_vel=110,
            )
            mods += [HumanizeModifier(timing_std=0.01, velocity_std=5),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "melody":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.35), harmony_note_probability=0.70,
                note_range_low=58, note_range_high=79, syncopation=0.35,
                phrase_length=8.0, drama_shape="crescendo", drama_peak=0.55,
                groove_template=SWING_60, beats_per_bar=4, denominator=4,
            )
            mods += [LimitNoteRangeModifier(low=58, high=79), VelocityScalingModifier(scale=0.72),
                     HumanizeModifier(timing_std=0.02, velocity_std=5),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "vocal_melisma":
            gen = VocalMelismaGenerator(
                params=GeneratorParams(density=0.30), style="rnb",
                run_length=4, ornament_prob=0.4, vibrato_depth=0.3, register_center=65,
            )
            mods += [LimitNoteRangeModifier(low=58, high=77), VelocityScalingModifier(scale=0.45),
                     HumanizeModifier(timing_std=0.02, velocity_std=4)]

        case "vocal_oohs":
            gen = VocalOohsGenerator(
                params=GeneratorParams(density=0.20),
                register="mid", vibrato_depth=0.2,
            )
            mods += [VelocityScalingModifier(scale=0.35), HumanizeModifier(timing_std=0.03, velocity_std=3)]

        case "vocal_adlibs":
            gen = VocalAdlibsGenerator(
                params=GeneratorParams(density=0.15),
                style="rnb", phrase_length=4.0,
            )
            mods += [VelocityScalingModifier(scale=0.30), HumanizeModifier(timing_std=0.025, velocity_std=4)]

        case "chops":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.35), processing="pitch_shift",
                density=0.40, chop_pattern="syncopated", source_pitch=65,
            )
            mods += [VelocityScalingModifier(scale=0.45), HumanizeModifier(timing_std=0.025, velocity_std=4),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "counter":
            gen = CountermelodyGenerator(
                params=GeneratorParams(density=0.30), motion_preference="mixed",
                dissonance_on_weak=True, interval_limit=7,
            )
            mods += [LimitNoteRangeModifier(low=65, high=84), VelocityScalingModifier(scale=0.42),
                     HumanizeModifier(timing_std=0.025, velocity_std=4),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "brass_stab":
            gen = BrassSectionGenerator(
                params=GeneratorParams(density=0.15), articulation="hit",
                voicing="closed", intensity=0.9, divisi_count=3,
            )
            mods += [VelocityScalingModifier(scale=0.35), HumanizeModifier(timing_std=0.01, velocity_std=3)]

        case "strings_pad":
            gen = StringsEnsembleGenerator(
                params=GeneratorParams(density=0.10), section_size="chamber",
                articulation="sustained", divisi=2, dynamic_curve="flat",
            )
            mods.append(VelocityScalingModifier(scale=0.35))

        case "organ_soft":
            gen = OrganDrawbarsGenerator(
                params=GeneratorParams(density=0.12), registration="ballad",
                leslie_speed="slow", percussion=False, vibrato=True, sustain_bars=1.5,
            )
            mods.append(VelocityScalingModifier(scale=0.22))

        case "organ":
            gen = OrganDrawbarsGenerator(
                params=GeneratorParams(density=0.22), registration="gospel",
                leslie_speed="slow", percussion=True, vibrato=False, sustain_bars=1.0,
            )
            mods.append(VelocityScalingModifier(scale=0.55))

        case "pad_ambient":
            gen = AmbientPadGenerator(
                params=GeneratorParams(density=0.08), voicing="spread",
                note_range_low=36, note_range_high=60,
            )
            mods += [VelocityScalingModifier(scale=0.25), HumanizeModifier(timing_std=0.04, velocity_std=3)]

        case "filter_sweep":
            gen = FilterSweepGenerator(
                params=GeneratorParams(density=0.20), sweep_type="lowpass_open",
                resonance=0.5, duration=4.0, curve="exponential",
            )
            mods += [VelocityScalingModifier(scale=0.30)]

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.25), riser_type="synth",
                length_beats=4.0, pitch_curve="exponential", peak_velocity=48,
            )
            mods += [VelocityScalingModifier(scale=0.30)]

        case _:
            return None

    return gen, mods
```

## 5. Section Arrangement

```python
SECTIONS = [
    ("Intro",      4, ["arp_sparp", "pad_ambient", "organ_soft"]),
    ("V1",         8, ["keys_comp", "bass_walk", "groove", "melody"]),
    ("Pre",        4, ["keys_hook", "organ", "bass_slap", "groove_full", "melody", "riser"]),
    ("Hook",       8, ["keys_hook", "bass_slap", "groove_full", "melody",
                       "counter", "vocal_melisma", "brass_stab", "chops"]),
    ("Breakdown",  4, ["keys_comp", "strings_pad"]),
    ("Hook 2",     8, ["keys_hook", "bass_slap", "groove_full", "melody",
                       "counter", "chops", "riser", "filter_sweep"]),
    ("Outro",      4, ["pad_ambient", "organ_soft", "bass_walk"]),
]
```

## 6. Track Registry and Production

```python
TRACKS = [
    {
        "title": "01_Track_Name",
        "scale": Scale(root=3, mode=Mode.DORIAN),
        "sections": SECTIONS,
        "build": build_track,
        "instruments": {
            "keys_comp": 4, "keys_hook": 4,
            "bass_walk": 33, "bass_slap": 33,
            "groove": 0, "groove_full": 0,
            "melody": 56, "counter": 52,
            "vocal_melisma": 85, "chops": 54,
            "brass_stab": 62, "strings_pad": 48,
            "organ_soft": 16, "organ": 16,
            "pad_ambient": 98, "arp_sparp": 88,
            "riser": 97, "filter_sweep": 95,
        },
        "bpm": 75,
        "mood": Mood.INTIMATE,
        "perc": {"groove", "groove_full"},
        "key_label": "Eb Dor",
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

## 7. Groove Templates

```python
from melodica.rhythm.groove_template import SWING_60, LAID_BACK, HIP_HOP, SHUFFLE, FUNK, PUSH

# Apply to any melody/bass generator via params:
MelodyGenerator(
    ...,
    groove_template=SWING_60,   # Classic R&B swing
    beats_per_bar=4, denominator=4,
)

# Or via SwingController modifier:
SwingController(swing_ratio=0.58, grid=0.5)   # Subtle R&B swing
SwingController(swing_ratio=0.61, grid=0.5)   # New Jack Swing
SwingController(swing_ratio=0.65, grid=0.5)   # Deep swing / gospel
```

| Template | Feel |
|---|---|
| `SWING_60` | Classic R&B / Neo-Soul |
| `LAID_BACK` | Behind the beat, bedroom R&B |
| `HIP_HOP` | Trap-Soul, modern R&B |
| `SHUFFLE` | Gospel shuffle |
| `FUNK` | Funk bass lines |
| `PUSH` | Anticipated, energetic |

## 8. R&B Subgenre Configs

### Neo-Soul Slow Jam

```python
Scale(root=3, mode=Mode.DORIAN)   # Eb Dorian
bpm = 72-78
# Keys: PianoCompGenerator jazz + WalkingBassGenerator
# Vocal: VocalMelismaGenerator(style="rnb")
# Drums: GrooveGenerator(pattern="soul")
```

### New Jack Swing

```python
Scale(root=6, mode=Mode.MAJOR)    # Gb Major
bpm = 88-96
# Keys: ModernChordPatternGenerator maj7
# Bass: BassSlapGenerator(slap_pattern="funky")
# Drums: GrooveGenerator(pattern="funk_1")
# Swing: ratio 0.61
```

### Trap-Soul

```python
Scale(root=10, mode=Mode.DORIAN)  # Bb Dorian
bpm = 95-105
# Bass: Bass808SlidingGenerator
# Drums: TrapDrumsGenerator
# Vocal: VocalChopsGenerator
# Hi-hats: HiHatStutterGenerator
```

### Gospel-Soul

```python
Scale(root=1, mode=Mode.LYDIAN)   # Db Lydian
bpm = 74-82
# Keys: OrganDrawbarsGenerator(registration="gospel")
# Choir: ChoirAahsGenerator
# Vocal: VocalOohsGenerator + VocalMelismaGenerator
```

### Lo-Fi R&B / Bedroom

```python
Scale(root=5, mode=Mode.MINOR)    # F Minor
bpm = 68-76
# Drums: LoFiHipHopGenerator
# Keys: PianoCompGenerator soft voicing
# Bass: SynthBassGenerator(waveform="sine")
# Vocal: VocalAdlibsGenerator
```

## 9. BPM Guide by Subgenre

| Subgenre | BPM |
|---|---|
| Slow Jam | 65-78 |
| Neo-Soul | 70-85 |
| New Jack Swing | 88-100 |
| Trap-Soul | 90-110 |
| Gospel-Soul | 72-85 |
| Lo-Fi R&B | 65-78 |
| Bedroom R&B | 68-80 |
| Funk R&B | 95-110 |

## 10. Common GM Programs

| Instrument | GM# |
|---|---|
| Piano Comp | 4 (Electric Piano) |
| Organ Ballad | 16 |
| Organ Gospel | 16 |
| Synth Bass | 38 |
| Electric Bass | 33 |
| Trumpet / Lead | 56 |
| Choir Aahs | 52 |
| Vocal Chops | 54 |
| Vocal Melisma | 85 |
| Strings Pad | 48 |
| Brass Section | 62 |
| Synth Pad | 88/98 |
| FX Riser | 97 |
| Drums (Ch10) | 0 |

## 11. Key Instrument Combinations

| Role | Generator | Notes |
|---|---|---|
| Harmony | `PianoCompGenerator(comp_style="jazz")` | Rootless voicings |
| Hook harmony | `ModernChordPatternGenerator(extension="maj9")` | Syncopated stabs |
| Bass groove | `WalkingBassGenerator` or `BassSlapGenerator` | Walking for slow, slap for energy |
| Drum pocket | `GrooveGenerator(groove_pattern="soul")` | Ghost notes essential |
| Lead vocal | `VocalMelismaGenerator(style="rnb")` | Runs + ornaments |
| Background vocals | `VocalOohsGenerator` or `VocalAdlibsGenerator` | Layered |
| Vocal texture | `VocalChopsGenerator(processing="pitch_shift")` | Syncopated chops |
| Counter-melody | `CountermelodyGenerator` | Interval limit 7 |
| Atmosphere | `AmbientPadGenerator` or `StringsEnsembleGenerator` | Low velocity |
| Transitions | `FXRiserGenerator` + `FilterSweepGenerator` | Section glue |

## 12. Common Pitfalls

| Issue | Fix |
|---|---|
| No swing feel | Add `SwingController(swing_ratio=0.58, grid=0.5)` to melody/bass/keys |
| Drums too robotic | Add `HumanizeModifier(timing_std=0.01, velocity_std=6)` to groove tracks |
| Bass too high | Always add `LimitNoteRangeModifier(low=28, high=52)` |
| Keys too loud | Use `VelocityScalingModifier(scale=0.45)` for comp |
| Pads overpowering | Use `VelocityScalingModifier(scale=0.25)` |
| Vocal melisma sounds random | Set `register_center=65`, `run_length=4`, `ornament_prob=0.4` |
| Organ registration invalid | Valid: `"ballad"`, `"gospel"`, `"jazz"`, `"rock"` |
| GrooveGenerator pattern not found | Valid: `"soul"`, `"funk_1"`, `"hiphop"`, `"rnb"` |
| Sections don't connect | Use `beat_offset` accumulation in `generate_track()` |

## 13. Running

```bash
python scripts/albums/rnb/album_name.py
```
