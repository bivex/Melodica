"""
demo_auto_fantasy.py — One-click generation of a Dark Fantasy track.
Uses the expanded Dark Fantasy style with section intensity, humanization,
and orchestral balancing.
"""

from melodica.composition import MusicDirector
from melodica.composition.styles import STYLES
from melodica.modifiers import HumanizeModifier, ModifierContext, SectionIntensityModifier
from melodica.application.orchestration import OrchestralBalancer
from melodica.application.automation import ExpressionCurve
from melodica.midi import export_midi
from melodica.types import Scale, Mode
from pathlib import Path


def main():
    # 1. Initialize director
    director = MusicDirector(key=Scale(0, Mode.MAJOR))

    # 2. Pick the expanded Dark Fantasy style
    style = STYLES["dark_fantasy"]

    # 3. Define structure — longer form with more sections
    structure = [
        ("Intro",       16.0),   # Quiet, atmospheric
        ("Mystery",     32.0),   # Building tension
        ("Main",        32.0),   # Full theme
        ("Battle",      48.0),   # Climax, maximum intensity
        ("Exploration", 32.0),   # Development / variation
        ("Main",        32.0),   # Recap
        ("Outro",       16.0),   # Fade to silence
    ]
    total_beats = sum(d for _, d in structure)  # 208 beats

    # 4. Generate arrangement from style
    arrangement = director.render_auto_song(style, structure)

    # 5. Apply section intensity arc (Intro 0.25 -> Battle 1.0 -> Outro 0.15)
    t = 0.0
    intensity_map = {}
    intensity_targets = {
        "Intro":       0.25,
        "Mystery":     0.50,
        "Main":        0.75,
        "Battle":      1.00,
        "Exploration": 0.60,
        "Outro":       0.15,
    }
    for sec_name, duration in structure:
        target = intensity_targets.get(sec_name, 0.7)
        intensity_map[(t, t + duration)] = target
        t += duration

    intensity_mod = SectionIntensityModifier(sections=intensity_map)
    for track in arrangement.tracks:
        if track.notes:
            ctx = ModifierContext(
                duration_beats=total_beats,
                chords=[],
                timeline=None,
                scale=director.key,
            )
            track.notes = intensity_mod.modify(track.notes, ctx)

    # 6. Humanize (micro-timing + velocity variation)
    humanizer = HumanizeModifier(timing_std=0.015, velocity_std=5.0)
    for track in arrangement.tracks:
        if track.notes:
            ctx = ModifierContext(
                duration_beats=total_beats,
                chords=[],
                timeline=None,
                scale=director.key,
            )
            track.notes = humanizer.modify(track.notes, ctx)

    # 7. Orchestral balancing
    arrangement.tracks = OrchestralBalancer.apply_balancing(arrangement.tracks)

    # 8. Export
    out_file = "output/auto_dark_fantasy.mid"
    Path("output").mkdir(exist_ok=True)
    export_midi(arrangement.tracks, out_file, bpm=style.typical_bpm)

    total_notes = sum(len(t.notes) for t in arrangement.tracks)
    duration_sec = total_beats / style.typical_bpm * 60
    print(f"Dark Fantasy generated: {out_file}")
    print(f"Key: {director.key.root} {director.key.mode.value}")
    print(f"Tracks: {len(arrangement.tracks)} | Notes: {total_notes} | Duration: {duration_sec:.0f}s")


if __name__ == "__main__":
    main()
