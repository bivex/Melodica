"""
generate_dark_fantasy_ost.py — Automated OST generator for Dark Fantasy games.
Generates 3 distinct tracks: Ambient, Crypt, and Battle.

Improvements over v1:
- Section intensity arcs (Intro quiet -> Climax loud -> Outro fade)
- Articulation per section (legato pads, staccato battle, etc.)
- Humanization (timing jitter + velocity variation)
- Volume automation (crescendos, fadeouts)
- Panning for spatial depth
"""

import os
from pathlib import Path
from melodica.types import Scale, Mode
from melodica.composition import Composition, MusicDirector
from melodica.modifiers import HumanizeModifier, ModifierContext
from melodica.application.automation import ExpressionCurve
from melodica.midi import export_midi


def apply_post_processing(arrangement, bpm: float):
    """Apply humanization and spectral balancing to the full arrangement."""
    from melodica.application.orchestration import OrchestralBalancer

    # Humanize all tracks
    humanizer = HumanizeModifier(timing_std=0.012, velocity_std=4.0)
    for track in arrangement.tracks:
        if track.notes:
            ctx = ModifierContext(
                duration_beats=max(n.start + n.duration for n in track.notes),
                chords=[],
                timeline=None,
                scale=Scale(0, Mode.MAJOR),
            )
            track.notes = humanizer.modify(track.notes, ctx)

    # Spectral balancing
    arrangement.tracks = OrchestralBalancer.apply_balancing(arrangement.tracks)


def generate_track(name, key, bpm, structure):
    print(f"--- Generating: {name} ({key.mode.value}) ---")
    composition = Composition(name=name, key=key)

    for entry in structure:
        sec_name = entry[0]
        duration = entry[1]
        progression = entry[2]
        tracks = entry[3]
        articulation = entry[4] if len(entry) > 4 else "sustain"
        automation = entry[5] if len(entry) > 5 else []

        composition.add_section(
            name=sec_name,
            duration=duration,
            progression=progression,
            tracks=tracks,
            articulation=articulation,
            automation=automation,
        )

    director = MusicDirector(key=key)
    arrangement = director.render(composition)

    apply_post_processing(arrangement, bpm)

    out_dir = Path("output/dark_fantasy_ost")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"{name.lower().replace(' ', '_')}.mid"
    export_midi(arrangement.tracks, out_file, bpm=bpm)

    total_notes = sum(len(t.notes) for t in arrangement.tracks)
    print(f"  {len(arrangement.tracks)} tracks, {total_notes} notes -> {out_file}\n")


def main():
    # ---------------------------------------------------------------
    # Track 1: "Cursed Forest" (Ambient/Mystical)
    # A Natural Minor, slow build from silence to gentle melody
    # ---------------------------------------------------------------
    forest_structure = [
        ("Foggy Intro", 16.0, "Im Im7",
         {"Background": "ambient_pad"},
         "legato",
         [ExpressionCurve.linear("volume", 10, 60, 16.0),
          ExpressionCurve.sinusoidal("pan", 20, 100, 16.0, freq=0.25)]),

        ("First Steps", 32.0, "Im VI III VII",
         {"Pads": "ambient_pad", "Wind_Echo": "fast_arp"},
         "legato",
         [ExpressionCurve.linear("volume", 50, 80, 32.0),
          ExpressionCurve.linear("modulation", 20, 50, 32.0)]),

        ("Ancient Tree", 32.0, "Im IVm VII Im",
         {"Pads": "ambient_pad", "Lead_Flute": "lead_melody", "Bass": "followed_bass"},
         "sustain",
         [ExpressionCurve.linear("volume", 70, 100, 32.0),
          ExpressionCurve.surge("modulation", 70, 32.0)]),

        ("Deeper", 32.0, "Im VI VII VIb",
         {"Pads": "ambient_pad", "Echo": "fast_arp", "Bass": "followed_bass"},
         "sustain",
         [ExpressionCurve.linear("volume", 80, 90, 32.0)]),

        ("Fading Out", 16.0, "Im",
         {"Background": "ambient_pad"},
         "legato",
         [ExpressionCurve.linear("volume", 80, 5, 16.0)]),
    ]
    generate_track(
        "Cursed Forest",
        Scale(root=9, mode=Mode.NATURAL_MINOR),
        bpm=60.0,
        structure=forest_structure,
    )

    # ---------------------------------------------------------------
    # Track 2: "Shadow Crypt" (Tense/Dark)
    # D Messiaen Mode 2 (half-whole diminished) for dissonance
    # ---------------------------------------------------------------
    crypt_structure = [
        ("The Gate", 16.0, "Im bII Im",
         {"Low_Hum": "ambient_pad"},
         "legato",
         [ExpressionCurve.linear("volume", 15, 50, 16.0),
          ExpressionCurve.sinusoidal("pan", 10, 110, 16.0, freq=0.15)]),

        ("Cold Stone", 32.0, "Im bII IIIb VII",
         {"Tension_Strings": "followed_chords", "Bass": "followed_bass"},
         "staccato",
         [ExpressionCurve.linear("volume", 40, 80, 32.0),
          ExpressionCurve.surge("modulation", 60, 32.0)]),

        ("Whispers", 32.0, "Im bV Im IVm",
         {"Whispers": "fast_arp", "Distant_Bell": "lead_melody"},
         "sustain",
         [ExpressionCurve.linear("volume", 60, 100, 32.0),
          ExpressionCurve.sinusoidal("pan", 15, 115, 32.0, freq=0.3)]),

        ("The Descent", 32.0, "Im bII Im bII",
         {"Low_Cello": "followed_bass", "Swell": "ambient_pad", "Tension_Strings": "followed_chords"},
         "marcato",
         [ExpressionCurve.linear("volume", 80, 120, 32.0),
          ExpressionCurve.surge("modulation", 80, 32.0),
          ExpressionCurve.surge("pitch_bend", 24, 32.0)]),

        ("Darkness", 16.0, "Im",
         {"Final_Hum": "ambient_pad"},
         "legato",
         [ExpressionCurve.linear("volume", 100, 0, 16.0)]),
    ]
    generate_track(
        "Shadow Crypt",
        Scale(root=2, mode=Mode.MESSIAEN_2),
        bpm=50.0,
        structure=crypt_structure,
    )

    # ---------------------------------------------------------------
    # Track 3: "Citadel Siege" (Epic/Aggressive)
    # E Harmonic Minor, fast, dramatic with full orchestra
    # ---------------------------------------------------------------
    siege_structure = [
        ("War Drums", 16.0, "Im",
         {"Bass_Pulse": "followed_bass", "Tension": "ambient_pad", "Drums": "orch_timpani_bass"},
         "staccato",
         [ExpressionCurve.linear("volume", 40, 80, 16.0),
          ExpressionCurve.linear("modulation", 30, 60, 16.0)]),

        ("Citadel Walls", 32.0, "Im VI IVm V",
         {"Lead_Brass": "lead_melody", "Harmony": "followed_chords",
          "Bass": "followed_bass", "Drums": "orch_timpani_bass"},
         "marcato",
         [ExpressionCurve.linear("volume", 70, 100, 32.0),
          ExpressionCurve.surge("modulation", 70, 32.0)]),

        ("The Charge", 32.0, "Im IVm VII IIIb VI V",
         {"Fast_Arp": "fast_arp", "Lead_Brass": "lead_melody",
          "Bass": "followed_bass", "Drums": "orch_timpani_bass",
          "Choir": "ambient_pad"},
         "marcato",
         [ExpressionCurve.linear("volume", 90, 127, 32.0),
          ExpressionCurve.surge("modulation", 90, 32.0),
          ExpressionCurve.sinusoidal("pan", 20, 107, 32.0, freq=0.5)]),

        ("Final Stand", 32.0, "Im VI V/V V",
         {"Full_Orchestra": "followed_chords", "Lead": "lead_melody",
          "Bass": "followed_bass", "Drums": "orch_timpani_bass",
          "Choir": "ambient_pad", "Arp": "fast_arp"},
         "marcato",
         [ExpressionCurve.surge("volume", 127, 32.0),
          ExpressionCurve.surge("modulation", 100, 32.0)]),

        ("Victory/Loss", 16.0, "Im",
         {"Aftermath": "ambient_pad", "Bass": "followed_bass"},
         "legato",
         [ExpressionCurve.linear("volume", 90, 5, 16.0),
          ExpressionCurve.linear("modulation", 80, 10, 16.0)]),
    ]
    generate_track(
        "Citadel Siege",
        Scale(root=4, mode=Mode.HARMONIC_MINOR),
        bpm=120.0,
        structure=siege_structure,
    )

    print("Dark Fantasy OST Generation Complete!")


if __name__ == "__main__":
    main()
