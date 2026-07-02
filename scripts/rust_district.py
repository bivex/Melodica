from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import NoteInfo, Scale, Mode, MusicTimeline
from melodica.generators import GeneratorParams
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.sax_solo import SaxSoloGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.harmonize import harmonizer_profile
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.midi import export_multitrack_midi


def make_chords(key: Scale, dur: float, bars_per_chord: float = 4.0):
    total_bars = int(dur / bars_per_chord)
    harmonizer = CoupledHMMHarmonizer(
        beam_width=14,
        config=harmonizer_profile("jazz"),
    )
    contour = []
    degrees = key.degrees()
    steps_per_bar = 2
    step = bars_per_chord / steps_per_bar
    for bar in range(total_bars):
        for s in range(steps_per_bar):
            deg = degrees[(bar + s) % len(degrees)]
            contour.append(
                NoteInfo(
                    pitch=60 + int(deg),
                    start=bar * bars_per_chord + s * step,
                    duration=step - 0.05,
                    velocity=60 + s * 5,
                )
            )
    return harmonizer.harmonize(contour, key, dur)


def _mix(raw: dict[str, list[NoteInfo]], bpm: float) -> dict[str, list[NoteInfo]]:
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update(
        {
            "Bass": 0.85,
            "Comp": 0.65,
            "Sax": 0.82,
            "Drums": 0.45,
            "Ghosts": 0.50,
            "Pad": 0.60,
        }
    )
    mixed = desk.apply_mixing(raw, [], int(bpm))
    m = MasteringDesk(target_lufs=-16.0)
    return m.apply_mastering(mixed)[0]


def build_rust_district(chords, key, dur):
    bass = WalkingBassGenerator(
        params=GeneratorParams(density=0.40, key_range_low=28, key_range_high=46),
        approach_style="chromatic",
        connect_roots=True,
        swing_eighth_ratio=0.66,
    )
    comp = PianoCompGenerator(
        params=GeneratorParams(density=0.30, key_range_low=48, key_range_high=68),
        comp_style="jazz",
        voicing_type="shell",
    )
    sax = SaxSoloGenerator(
        params=GeneratorParams(density=0.25, key_range_low=58, key_range_high=78),
        style="ballad",
    )
    drums = DrumKitPatternGenerator(
        params=GeneratorParams(density=0.30),
        style="jazz",
        groove_swing=0.66,
    )
    ghosts = GhostNotesGenerator(
        params=GeneratorParams(density=0.20, key_range_low=38, key_range_high=70),
        pattern="jazz",
        ghost_velocity=25,
    )
    pad = AmbientPadGenerator(
        params=GeneratorParams(density=0.15, key_range_low=36, key_range_high=54),
        voicing="spread",
        overlap=0.1,
    )
    return {
        "Bass": bass.render(chords, key, dur),
        "Comp": comp.render(chords, key, dur),
        "Sax": sax.render(chords, key, dur),
        "Drums": drums.render(chords, key, dur),
        "Ghosts": ghosts.render(chords, key, dur),
        "Pad": pad.render(chords, key, dur),
    }


def main():
    out_dir = Path("output/rust_district")
    out_dir.mkdir(exist_ok=True, parents=True)

    key = Scale(root=2, mode=Mode.HARMONIC_MINOR)
    bpm = 65.0
    dur = 64.0

    chords = make_chords(key, dur)
    print(f"\n### Rust District | root={key.root} {key.mode.value} | BPM {bpm} | jazz profile")
    for c in chords:
        q = c.quality.name
        print(f"  {c.start:4.1f}  root={c.root}  {q}")

    raw = build_rust_district(chords, key, dur)
    mixed = _mix(raw, bpm)

    out = out_dir / "rust_district.mid"
    instruments = {
        "Bass": 32,
        "Comp": 0,
        "Sax": 66,
        "Drums": 0,
        "Ghosts": 0,
        "Pad": 88,
    }
    export_multitrack_midi(
        mixed,
        out,
        bpm=bpm,
        key=key,
        time_sig=(4, 4),
        instruments=instruments,
        diagnose=True,
        validate_form=False,
    )
    print(f"Exported: {out}")


if __name__ == "__main__":
    main()
