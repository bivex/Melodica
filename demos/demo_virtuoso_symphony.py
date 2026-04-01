"""
demo_virtuoso_symphony.py -- Orchestral showcase with proper instrument ranges.

Each instrument gets a preset tuned to its physical range from
ORCHESTRAL_PROFILES, so notes are generated in-bounds from the start.
RenderContext seeds each instrument in its comfortable register.
"""

from melodica.types import Scale, Mode
from melodica.composition import Composition, MusicDirector
from melodica.composition.styles import STYLES
from melodica.midi import export_midi
from melodica.application.automation import ExpressionCurve
from melodica.application.orchestration import OrchestralBalancer
from melodica.application.spectral import SpectralAnalyzer
from melodica.modifiers import HumanizeModifier, ModifierContext
from melodica.render_context import RenderContext
from pathlib import Path


def main():
    # -- 1. Key & Style ---------------------------------------------------
    key = Scale(root=2, mode=Mode.MESSIAEN_2)
    director = MusicDirector(key=key)
    style = STYLES["symphonic"]

    # -- 2. Build Composition ---------------------------------------------
    comp = Composition(name="Eternal_Darkness_Symphony", key=key)

    sections = [
        ("Intro",   16.0),
        ("Theme_A", 32.0),
        ("Climax",  32.0),
        ("Theme_A", 16.0),
        ("Outro",   32.0),
    ]
    comp.apply_style(style, sections)

    # Time signatures per section
    comp.sections[0].time_signature = (4, 4)   # Intro
    comp.sections[1].time_signature = (4, 4)   # Theme A
    comp.sections[2].time_signature = (5, 4)   # Climax -- odd meter
    comp.sections[3].time_signature = (4, 4)   # Recap
    comp.sections[4].time_signature = (3, 4)   # Outro -- waltz

    # Articulations per section
    comp.sections[0].articulation = "sustain"
    comp.sections[1].articulation = "legato"
    comp.sections[2].articulation = "marcato"
    comp.sections[3].articulation = "sustain"
    comp.sections[4].articulation = "staccato"

    # Automation: expression swell in Climax, pitch bend accent
    comp.sections[2].automation.append(
        ExpressionCurve.linear(target=11, start_val=30, end_val=127, duration=16.0)
    )
    comp.sections[2].automation.append(
        ExpressionCurve.surge(target="pitch_bend", peak_val=32, duration=8.0)
    )

    # -- 3. Seed RenderContexts for each orchestral section ----------------
    # Each instrument starts in its sweet spot so the first phrase is in-range.
    initial_contexts = {
        "Violins_I":   RenderContext(prev_pitch=76, prev_velocity=80),   # E5 -- violin I sweet spot
        "Violins_II":  RenderContext(prev_pitch=72, prev_velocity=75),   # C5 -- violin II center
        "Viola":       RenderContext(prev_pitch=64, prev_velocity=75),   # E4 -- viola sweet spot
        "Cello":       RenderContext(prev_pitch=48, prev_velocity=85),   # C3 -- cello core
        "Contrabass":  RenderContext(prev_pitch=36, prev_velocity=90),   # C2 -- bass fundamental
        "Flute":       RenderContext(prev_pitch=74, prev_velocity=70),   # D5 -- flute sweet spot
        "Oboe":        RenderContext(prev_pitch=70, prev_velocity=75),   # Bb4 -- oboe center
        "Horn":        RenderContext(prev_pitch=55, prev_velocity=80),   # G3 -- horn mid
        "Trumpet":     RenderContext(prev_pitch=65, prev_velocity=90),   # F4 -- trumpet range
        "Trombone":    RenderContext(prev_pitch=52, prev_velocity=85),   # E3 -- trombone tenor
        "Timpani":     RenderContext(prev_pitch=41, prev_velocity=100),  # F2 -- timpani
        "Harp":        RenderContext(prev_pitch=60, prev_velocity=65),   # C4 -- harp mid
    }

    # -- 4. Render (RenderContext threads through sections automatically) --
    arrangement = director.render(comp, initial_contexts=initial_contexts)

    # -- 5. Mix settings (all explicit, from profiles) -------------------
    OrchestralBalancer.apply_balancing(arrangement.tracks)

    # Octave correction -- safety net for any remaining outliers
    OrchestralBalancer.shift_octaves_into_range(arrangement.tracks)

    # Velocity scaling -- spectral priority, no hidden boost
    OrchestralBalancer.scale_velocities(arrangement.tracks, boost=1.0)

    # -- 6. Humanize ------------------------------------------------------
    humanizer = HumanizeModifier(timing_std=0.012, velocity_std=4.0)
    for track in arrangement.tracks:
        ctx = ModifierContext(
            duration_beats=arrangement.total_beats,
            chords=[], timeline=arrangement.timeline, scale=key,
        )
        track.notes = humanizer.modify(track.notes, ctx)

    # -- 7. Instruments ---------------------------------------------------
    for track in arrangement.tracks:
        if track.name in style.instrument_mapping:
            track.program = style.instrument_mapping[track.name]

    # -- 8. Export --------------------------------------------------------
    out_file = "output/virtuoso_symphony.mid"
    Path("output").mkdir(exist_ok=True)
    export_midi(arrangement.tracks, out_file, bpm=style.typical_bpm, timeline=arrangement.timeline)

    print(f"Exported: {out_file}")
    print(f"Tracks: {len(arrangement.tracks)}")
    print(f"Sections: {[s.name for s in comp.sections]}")
    print(f"Time Signatures: {[s.time_signature for s in comp.sections]}")

    # -- 9. Spectral report -----------------------------------------------
    SpectralAnalyzer.analyze(arrangement).print_report()


if __name__ == "__main__":
    main()
