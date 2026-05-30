---
name: write-ideatool-album
description: Generate albums using the IdeaTool high-level pipeline. Best for cinematic, literary, Japanese, Arabic, and world music. Uses TrackConfig + IdeaPart for arrangement, CoupledHMM for harmony.
---

# Write IdeaTool Album

Use this skill for albums that need the **IdeaTool** high-level pipeline with `TrackConfig`, `IdeaPart`, and automatic harmony via CoupledHMM. This is the best approach for cinematic scores, literary adaptations, Japanese/Asian music, Arabic/microtonal music, and world music.

## 1. When to Use IdeaTool vs Direct Generators

| Use IdeaTool | Use Direct Generators |
|---|---|
| Cinematic / hybrid scores | R&B / Soul / Jazz |
| Literary / poetry adaptations | Electronic / Techno |
| Japanese / Asian music | Metal / Rock |
| Arabic / microtonal music | Folk with simple arrangements |
| World / ethnic music | Ambient (minimal layers) |
| Complex multi-movement works | Albums needing section-by-section control |

## 2. Required Imports

```python
from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

# Import generators as needed
from melodica.generators.orchestral_strings import ViolinGenerator, CelloGenerator, ContrabassGenerator, ViolaGenerator
from melodica.generators.orchestral_brass import FrenchHornGenerator, TromboneGenerator, TrumpetGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.snare_drum import SnareDrumGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.tension import TensionGenerator
from melodica.generators.ethnic_world import EthnicWorldGenerator
from melodica.generators.plucked_solo import EthnicPluckedGenerator
from melodica.generators.wind_brass_solo import WoodwindSoloGenerator
from melodica.generators.chromatic_percussion import CelestaGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.fx_riser import FXRiserGenerator

# For phrase scheduling
from melodica.idea_tool import structure_to_schedule

# For Japanese rhythm patterns
from melodica.rhythm import get_rhythm

# For modifiers (optional)
from melodica.modifiers import (
    ModifierPipeline, ModifierContext,
    DropSilenceModifier, DrumFillModifier,
    CrescendoModifier, HumanizeModifier,
)
from melodica.types import MusicTimeline
```

## 3. Core Pattern

```python
def main():
    album_dir = Path("output/album_name")
    album_dir.mkdir(exist_ok=True, parents=True)

    tracks_configs = [
        {
            "id": "01",
            "name": "Track_Name",
            "description": "Description of the track mood.",
            "tempo": 80,
            "scale": Scale(root=0, mode=Mode.MINOR),
            "bars": 48,
            # Optional:
            "time_signature": (6, 8),  # Non-standard time
        },
        # ... more tracks
    ]

    for cfg in tracks_configs:
        parts = [IdeaPart(
            name=cfg['name'],
            bars=cfg['bars'],
            scale=cfg['scale'],
            tempo=cfg['tempo'],
            progression_type="coupled_hmm",  # or "hmm3"
            # Optional:
            time_signature=cfg.get("time_signature"),
        )]

        track_list = [
            TrackConfig(name="Track_Name", generator=SomeGenerator(), instrument="instrument_key",
                        density=0.5, octave_shift=-1, mpe=True),
            # ... more tracks
        ]

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",  # or "japanese", etc.
            workflow="generate_all",
            use_tension_curve=True,
            use_harmonic_verifier=True,
            target_lufs=-14.0,
            parts=parts,
            tracks=track_list,
        )

        notes_dict = IdeaTool(tool_config).generate()
        tracks_data = {k: v for k, v in notes_dict.items()
                       if not k.startswith("_") and isinstance(v, list)}

        export_multitrack_midi(
            tracks_data,
            str(album_dir / f"{cfg['id']}_{cfg['name']}.mid"),
            bpm=cfg['tempo'],
            key=cfg['scale'],
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set()),
        )

if __name__ == "__main__":
    with EngineTracer(max_depth=1, use_colors=True):
        main()
```

## 4. TrackConfig Reference

```python
TrackConfig(
    name="Unique_Name",       # Track identifier (used in scheduling)
    generator=SomeGenerator(), # Generator instance
    instrument="piano",        # GM instrument key name (see below)
    density=0.5,               # 0.0-1.0 note density
    octave_shift=0,            # Transpose by N octaves (-2 to +2)
    mpe=False,                 # Enable MPE expression
    params={},                 # Generator-specific params
)
```

### Instrument Key Names

| Key | GM# | Description |
|---|---|---|
| `"piano"` | 0 | Acoustic Grand Piano |
| `"violin"` | 40 | Violin |
| `"viola"` | 41 | Viola |
| `"cello"` | 42 | Cello |
| `"contrabass"` | 43 | Contrabass |
| `"tremolo_strings"` | 44 | Tremolo Strings |
| `"harp"` | 46 | Orchestral Harp |
| `"timpani"` | 47 | Timpani |
| `"strings"` | 48 | String Ensemble |
| `"french_horn"` / `"horn"` | 60 | French Horn |
| `"trumpet"` | 56 | Trumpet |
| `"trombone"` | 57 | Trombone |
| `"flute"` | 73 | Flute |
| `"oboe"` | 68 | Oboe |
| `"clarinet"` | 71 | Clarinet |
| `"bassoon"` | 70 | Bassoon |
| `"choir"` | 52 | Choir Aahs |
| `"dark_pad"` | 88 | Synth Pad (New Age) |
| `"synth_pad"` | 89 | Synth Pad (Warm) |
| `"synth_fx"` | 99 | FX Atmosphere |
| `"synth_voice"` | 54 | Synth Voice |
| `"shamisen"` | 106 | Shamisen |
| `"koto"` | 107 | Koto |
| `"sitar"` | 104 | Sitar |
| `"shakuhachi"` | 77 | Shakuhachi |
| `"taiko"` | 116 | Taiko Drum |
| `"tubular_bells"` | 14 | Tubular Bells |
| `"drums"` | 0 | Drum Kit (Ch 10) |
| `"percussion"` | 0 | Percussion (Ch 10) |
| `"steel_drums"` | 114 | Steel Drums |
| `"orchestra_hit"` | 55 | Orchestra Hit |
| `"voice"` | 54 | Synth Voice |
| `"dark_bass"` | 38 | Synth Bass |
| `"synth_bass"` | 38 | Synth Bass |

## 5. Phrase Scheduling (Multi-Part Tracks)

For tracks with multiple sections (e.g., Intro + Rising + Climax):

```python
parts = [
    IdeaPart(
        name="Intro",
        bars=16,
        scale=in_sen,
        tempo=55,
        track_phrase_schedules={
            "Drone":       structure_to_schedule("A", 16),      # Always active
            "Taiko":       structure_to_schedule("R A R B", 4), # Rest, Play, Rest, Play
            "Shakuhachi":  structure_to_schedule("R R R A", 4), # Only at end
        }
    ),
    IdeaPart(
        name="Climax",
        bars=16,
        scale=in_sen,
        tempo=75,
        track_phrase_schedules={
            "Drone":       structure_to_schedule("A", 16),
            "Taiko":       structure_to_schedule("A B", 8),     # Two phrases
            "Shakuhachi":  structure_to_schedule("B", 16),       # Full section
        }
    ),
]
```

Schedule codes: `A` = first phrase, `B` = second, `C` = third, `R` = rest/silence.

## 6. Genre-Specific Configs

### Japanese Music

```python
# Scales
in_sen = Scale(0, Mode.JAPANESE)       # C In-Sen: dark, angular
kumoi = Scale(7, Mode.KUMOI)           # G Kumoi: mysterious pentatonic

# Rhythm patterns (via get_rhythm)
get_rhythm("jp_noh_taiko_8th")         # Noh theater taiko
get_rhythm("jp_noh_kotsuzumi_8th")     # Noh hand drum
get_rhythm("jp_shakuhachi_free")       # Free-tempo shakuhachi
get_rhythm("jp_koto_dan_8th")          # Koto dan performance
get_rhythm("jp_taiko_festival_16th")   # Festival taiko
get_rhythm("jp_shamisen_tsugaru_16th") # Tsugaru shamisen
get_rhythm("jp_kabuki_odaiko_4_4")    # Kabuki odaiko
get_rhythm("jp_kagura_drums_4_4")     # Kagura ceremonial drums

# Typical instruments
TrackConfig("Noh_Drone", "drone", "dark_pad", density=0.6, octave_shift=-1)
TrackConfig("Shakuhachi", "melody", "shakuhachi", density=0.4,
            params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_shakuhachi_free")})
TrackConfig("Koto", "melody", "koto", density=0.7,
            params={"mode": "scale_walk", "rhythm": get_rhythm("jp_koto_dan_8th")})
```

### Arabic / Middle Eastern

```python
# Scales
sikah = Scale(root=4, mode=Mode.ARABIC_SIKAH)      # Quarter-tone scale
hijaz = Scale(root=4, mode=Mode.PHRYGIAN_DOMINANT)  # Hijaz maqam

# Instruments
TrackConfig("Oud", generator=EthnicWorldGenerator(instrument="shamisen"),
            instrument="shamisen", density=0.6, mpe=True)
TrackConfig("Ney_Flute", generator=EthnicWorldGenerator(instrument="shanai"),
            instrument="shanai", density=0.5, mpe=True)
TrackConfig("Kanun", generator=EthnicPluckedGenerator(instrument="koto"),
            instrument="koto", density=0.5, mpe=True)
TrackConfig("Sitar", generator=EthnicPluckedGenerator(instrument="sitar"),
            instrument="sitar", density=0.6, mpe=True)
TrackConfig("Percussion", generator=ElectronicDrumsGenerator(kit="ethnic"),
            instrument="steel_drums", density=0.7)
```

### Cinematic Hybrid

```python
# Use IdeaToolConfig style
IdeaToolConfig(
    style="cinematic_hybrid",
    use_tension_curve=True,        # Auto tension arc
    use_harmonic_verifier=True,    # Validate harmony
    target_lufs=-12.0,            # Louder for action, -15.0 for subtle
)

# Mix acoustic + electronic
TrackConfig("Drums", generator=ElectronicDrumsGenerator(kit="industrial"),
            instrument="drums", density=0.85)
TrackConfig("Choir", generator=ChoirAahsGenerator(),
            instrument="choir", density=0.7, mpe=True)
TrackConfig("Scifi", generator=SciFiUnderscoreGenerator(),
            instrument="synth_fx", density=0.6)
```

### Literary / Poetry Cycle

```python
# One track per poem
# Match scale/mode to poem mood:
#   PHRYGIAN — mystical, dark
#   DORIAN — bittersweet, ironic
#   LYDIAN — ethereal, transcendent
#   LOCRIAN — dissonant, unstable
#   AEOLIAN — natural minor, heavy
#   MAJOR — bright, hopeful

IdeaToolConfig(
    style="cinematic_hybrid",
    progression_type="coupled_hmm",  # Smart harmony
    parts=parts,
    tracks=track_list,
)
```

## 7. Modifiers (Optional Post-Processing)

```python
from melodica.modifiers import DropSilenceModifier, DrumFillModifier

# Apply silence drops and drum fills at specific beats
glue = {
    "Track_Name": [
        DropSilenceModifier(silence_duration=2.0, specific_beats=[32.0], apply_at_end=False),
    ],
    "Drums": [
        DrumFillModifier(fill_duration=2.0, subdivision=0.125, fill_pitch=36,
                         velocity_start=20, velocity_end=127, accent_on_drop=True,
                         specific_beats=[32.0], apply_at_end=False),
    ],
}
```

## 8. Common Pitfalls

| Issue | Fix |
|---|---|
| `structure_to_schedule` not found | Import from `melodica.idea_tool` |
| `get_rhythm` not found | Import from `melodica.rhythm` |
| Generator needs `articulation` but TrackConfig has no param | Use `params={"articulation": "legato"}` |
| Non-4/4 time not working | Add `time_signature=(6, 8)` to `IdeaPart` |
| MPE instruments sound flat | Set `mpe=True` in `TrackConfig` |

## 9. Available Modes for Scale

Standard: `MAJOR`, `MINOR`, `DORIAN`, `PHRYGIAN`, `LYDIAN`, `MIXOLYDIAN`, `AEOLIAN`, `LOCRIAN`

Extended: `HARM_MINOR`, `MELODIC_MINOR`, `DOUBLE_HARM_MAJOR`, `HUNGARIAN_MINOR`, `PHRYGIAN_DOMINANT`, `GYPSY`

Ethnic: `JAPANESE`, `KUMOI`, `ARABIC_SIKAH`

**PITFALL**: `Mode.HARMONIC_MAJOR` does NOT exist. Use `Mode.DOUBLE_HARM_MAJOR`.

## 10. Running

```bash
python scripts/albums/genre/album_name.py
```

Verify output:
```bash
ls output/album_name/*.mid
```
