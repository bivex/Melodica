# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
demo_masterpiece_dark_fantasy.py — Ultimate Dark Fantasy showcase.
Full automation, gradual orchestral buildup, percussion, and spatial effects.
"""

from melodica.types import Scale, Mode
from melodica.composition import Composition, MusicDirector
from melodica.composition.styles import STYLES
from melodica.modifiers import HumanizeModifier, ModifierContext
from melodica.application.orchestration import OrchestralBalancer
from melodica.midi import export_midi
from melodica.application.automation import ExpressionCurve
from pathlib import Path


def main():
    key = Scale(root=2, mode=Mode.MESSIAEN_2)
    director = MusicDirector(key=key)
    style = STYLES["dark_fantasy"]

    comp = Composition(name="Shadow_Emperor_Theme", key=key)

    # --- Automation Curves ---
    # Section 1: Mist (creeping swell)
    mist_swell = ExpressionCurve.linear("volume", 10, 60, 24.0)
    mist_pan = ExpressionCurve.sinusoidal("pan", 15, 110, 24.0, freq=0.2)

    # Section 2: Gathering (build to moderate)
    gather_vol = ExpressionCurve.linear("volume", 55, 85, 32.0)
    gather_mod = ExpressionCurve.linear("modulation", 20, 55, 32.0)

    # Section 3: Approach (tension rise)
    approach_vol = ExpressionCurve.linear("volume", 75, 105, 32.0)
    approach_mod = ExpressionCurve.surge("modulation", 75, 32.0)

    # Section 4: Throne Room (climax)
    throne_vol = ExpressionCurve.linear("volume", 100, 127, 48.0)
    throne_mod = ExpressionCurve.surge("modulation", 100, 48.0)
    throne_pitch = ExpressionCurve.surge("pitch_bend", 28, 48.0)
    throne_sustain = ExpressionCurve.linear("sustain", 100, 127, 48.0)
    throne_pan = ExpressionCurve.sinusoidal("pan", 20, 107, 48.0, freq=0.4)

    # Section 5: Aftermath (slow decay)
    decay_vol = ExpressionCurve.linear("volume", 100, 40, 32.0)

    # Section 6: Cursed Exit (fade to silence)
    outro_vol = ExpressionCurve.linear("volume", 35, 0, 24.0)

    # --- Structure (208 beats, ~3 min at 60 BPM) ---
    # Gradual orchestral layering: 1 -> 2 -> 3 -> 6 -> 4 -> 1 tracks

    comp.add_section(
        name="Mist",
        duration=24.0,
        progression="Im bII",
        tracks={"Pads": "ambient_pad"},
        articulation="legato",
        automation=[mist_swell, mist_pan],
    )

    comp.add_section(
        name="Gathering",
        duration=32.0,
        progression="Im bII IIIb VII",
        tracks={"Pads": "ambient_pad", "Texture": "fast_arp"},
        articulation="sustain",
        automation=[gather_vol, gather_mod],
    )

    comp.add_section(
        name="Approach",
        duration=32.0,
        progression="Im bVI bIII bVII Im",
        tracks={"Pads": "ambient_pad", "Texture": "fast_arp",
                "Bass": "followed_bass"},
        articulation="sustain",
        automation=[approach_vol, approach_mod],
    )

    comp.add_section(
        name="Throne",
        duration=48.0,
        progression="Im bII Im VIIb Im VI IVm V",
        tracks={
            "Pads": "ambient_pad",
            "Lead": "lead_melody",
            "Bass": "followed_bass",
            "Texture": "fast_arp",
            "Choir": "followed_chords",
            "Drums": "orch_timpani_bass",
        },
        articulation="marcato",
        automation=[throne_vol, throne_mod, throne_pitch, throne_sustain, throne_pan],
    )

    comp.add_section(
        name="Aftermath",
        duration=32.0,
        progression="Im IVm VII Im",
        tracks={"Pads": "ambient_pad", "Lead": "lead_melody",
                "Bass": "followed_bass"},
        articulation="legato",
        automation=[decay_vol],
    )

    comp.add_section(
        name="Cursed_Exit",
        duration=24.0,
        progression="Im",
        tracks={"Pads": "ambient_pad"},
        articulation="legato",
        automation=[outro_vol],
    )

    # --- Render ---
    arrangement = director.render(comp)

    # Humanize
    humanizer = HumanizeModifier(timing_std=0.012, velocity_std=4.0)
    for track in arrangement.tracks:
        if track.notes:
            ctx = ModifierContext(
                duration_beats=192.0,
                chords=[],
                timeline=None,
                scale=key,
            )
            track.notes = humanizer.modify(track.notes, ctx)

    # Spectral balancing
    arrangement.tracks = OrchestralBalancer.apply_balancing(arrangement.tracks)

    # Apply style instrument mapping
    for track in arrangement.tracks:
        if track.name in style.instrument_mapping:
            track.program = style.instrument_mapping[track.name]

    # --- Export ---
    out_file = "output/masterpiece_dark_fantasy.mid"
    Path("output").mkdir(exist_ok=True)
    export_midi(arrangement.tracks, out_file, bpm=60.0)

    total_notes = sum(len(t.notes) for t in arrangement.tracks)
    duration_sec = 192.0 / 60.0 * 60  # 192 beats at 60 BPM = 192s
    print(f"Dark Fantasy MASTERPIECE generated: {out_file}")
    print(f"Scale: {key.root} {key.mode.value}")
    print(f"Tracks: {len(arrangement.tracks)} | Notes: {total_notes} | Duration: {duration_sec:.0f}s")


if __name__ == "__main__":
    main()
