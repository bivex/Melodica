# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import os
from melodica.types import Scale, Mode, ChordLabel
from melodica.form import MusicalForm
from melodica.dynamics_arc import DynamicsArc
from melodica.orchestrator import OrchestralLayer, Orchestrator
from melodica.generators.orchestral_strings import ViolinGenerator, ViolaGenerator, CelloGenerator, ContrabassGenerator
from melodica.generators.orchestral_woodwinds import FluteGenerator
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.midi import export_multitrack_midi


def main():
    print("Initializing Orchestral Arranger Demonstration...")
    
    # Use D Phrygian for a rich, dramatic, cinematic sound
    scale = Scale(root=2, mode=Mode.PHRYGIAN)
    
    # 240 beats total duration (at 120 bpm, this is exactly 2 minutes; at slower tempo, it's ~3 minutes)
    duration_beats = 240.0
    
    # 1. Define Musical Form (Sonata form)
    form = MusicalForm.sonata(scale, duration_beats=duration_beats, base_bpm=100.0)
    print(f"Musical form initialized: {len(form.sections)} sections.")
    for sec in form.sections:
        print(f"  - {sec.name}: start={sec.start_beat}, duration={sec.duration_beats}, dynamics={sec.dynamics}, mood={sec.mood}, families={sec.active_families}")
        
    # 2. Define global Dynamics Arc
    dynamics_arc = DynamicsArc.from_form(form)
    print("Global Dynamics Arc created with smooth sectional interpolation.")
    
    # 3. Create Orchestral Layers
    # Layer 1: Violins (Melody/Solo)
    violins = ViolinGenerator(articulation="legato", vibrato=True)
    layer_violins = OrchestralLayer(
        name="Violins",
        generator=violins,
        family="strings",
        role="melody",
        density_curve="sparse_to_dense",
        default_params={"double_stops": False}
    )
    
    # Layer 2: Violas (Harmony)
    violas = ViolaGenerator(articulation="sustained")
    layer_violas = OrchestralLayer(
        name="Violas",
        generator=violas,
        family="strings",
        role="harmony",
        density_curve="constant",
    )
    
    # Layer 3: Legato String Section (Pads / thick strings)
    strings_pad = StringsLegatoGenerator(ensemble_mode="tutti")
    layer_strings_pad = OrchestralLayer(
        name="String Ensemble",
        generator=strings_pad,
        family="strings",
        role="pad",
        density_curve="constant",
    )
    
    # Layer 4: Cellos (Bass)
    cellos = CelloGenerator(articulation="sustained", bass_voice=True)
    layer_cellos = OrchestralLayer(
        name="Cellos",
        generator=cellos,
        family="strings",
        role="bass",
        density_curve="constant",
    )
    
    # Layer 5: Woodwinds (Solo / Flute runs)
    flute = FluteGenerator(articulation="legato")
    layer_woodwinds = OrchestralLayer(
        name="Woodwinds (Flute)",
        generator=flute,
        family="woodwinds",
        role="solo",
        density_curve="sparse_to_dense",
    )
    
    # Layer 6: Brass Section (Rhythm / Hits)
    brass = BrassSectionGenerator(ensemble_mode="tutti", articulation="sustained")
    layer_brass = OrchestralLayer(
        name="Brass Section",
        generator=brass,
        family="brass",
        role="rhythm",
        density_curve="sparse_to_dense",
    )
    
    # 4. Instantiate Orchestrator
    orchestrator = Orchestrator(
        layers=[
            layer_violins,
            layer_violas,
            layer_strings_pad,
            layer_cellos,
            layer_woodwinds,
            layer_brass,
        ],
        form=form,
        dynamics=dynamics_arc,
    )
    
    # 5. Build rich cinematic Chord Progression (60 chords of 4 beats each = 240 beats)
    # i - VI - bVII - v - i - iv - bII - V7 - ...
    harmonic_pattern = [
        (0, "min"),   # Dm
        (8, "maj"),   # Bb
        (10, "maj"),  # C
        (7, "min"),   # Am
        (0, "min"),   # Dm
        (5, "min"),   # Gm
        (1, "maj"),   # Eb
        (7, "maj"),   # A major (V in minor/phrygian)
    ]
    
    chords = []
    current_beat = 0.0
    chord_duration = 4.0
    
    while current_beat < duration_beats:
        pat_idx = int(current_beat / chord_duration) % len(harmonic_pattern)
        root_offset, quality = harmonic_pattern[pat_idx]
        
        # Calculate root pitch class snapped to D Phrygian scale
        chord_root = (scale.root + root_offset) % 12
        
        chords.append(
            ChordLabel(
                root=chord_root,
                quality=quality,
                start=current_beat,
                duration=chord_duration
            )
        )
        current_beat += chord_duration
        
    print(f"Chord progression created with {len(chords)} chord segments.")
    
    # 6. Render Multitrack Orchestration
    print("Rendering orchestral layers...")
    tracks = orchestrator.render(chords, scale, duration_beats)
    
    # Report note counts
    print("Orchestration rendering complete! Note counts per track:")
    total_notes = 0
    for name, notes in tracks.items():
        print(f"  - {name}: {len(notes)} notes")
        total_notes += len(notes)
    print(f"Total rendered notes: {total_notes}")
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    output_path = "output/demo_orchestrator.mid"
    
    # 7. Export to Type 1 Multitrack MIDI file
    print(f"Exporting multitrack MIDI file to: {output_path}...")
    export_multitrack_midi(
        tracks_data=tracks,
        path=output_path,
        bpm=100.0,
        key=scale,
        tempo_events=form.tempo_map,
        instruments={
            "Violins": 40,
            "Violas": 41,
            "String Ensemble": 48,  # Orchestral Strings
            "Cellos": 42,
            "Woodwinds (Flute)": 73,
            "Brass Section": 61,    # Brass Section
        }
    )
    
    file_size_kb = os.path.getsize(output_path) / 1024.0
    print(f"MIDI file exported successfully! File Size: {file_size_kb:.2f} KB.")
    print("Process finished successfully.")


if __name__ == "__main__":
    main()
