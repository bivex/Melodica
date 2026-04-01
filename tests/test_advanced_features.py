import pytest
import json
from melodica.types import ChordLabel, Quality, Scale, Mode, Note
from melodica.rhythm import MotifRhythmGenerator, SubdivisionGenerator
from melodica.detection import detect_scale_from_chords
from melodica.generators import MelodyGenerator
from melodica.modifiers import SwingController, HumanizeModifier
from melodica.presets import serialize_preset, deserialize_preset


def test_motif_rhythm():
    # Inner: 1 note at start of motif
    inner = SubdivisionGenerator(divisions_per_beat=1)
    # Motif: 2 beats long (has 2 notes), Total: 8 beats phrase (loops 4 times)
    motif_gen = MotifRhythmGenerator(inner, motif_length=2.0)
    events = motif_gen.generate(8.0)
    
    # 4 repetitions * 2 notes per motif = 8 notes
    assert len(events) == 8
    assert events[2].onset == 2.0  # start of 2nd motif
    assert events[6].onset == 6.0  # start of 4th motif


def test_key_detection_from_chords():
    # Am - F - G - Am (C Major relative or A Minor)
    chords = [
        ChordLabel(root=9, quality=Quality.MINOR, start=0, duration=4),
        ChordLabel(root=5, quality=Quality.MAJOR, start=4, duration=4),
        ChordLabel(root=7, quality=Quality.MAJOR, start=8, duration=4),
        ChordLabel(root=9, quality=Quality.MINOR, start=12, duration=4),
    ]
    scale = detect_scale_from_chords(chords)
    # Should detect A Minor (9, NATURAL_MINOR)
    assert scale.root == 9
    assert scale.mode == Mode.NATURAL_MINOR


def test_preset_serialization():
    gen = MelodyGenerator(prefer_chord_tones=0.5)
    mods = [
        SwingController(swing_ratio=0.6, grid=1.0),
        HumanizeModifier(timing_std=0.01)
    ]
    
    # Save to string
    json_data = serialize_preset(gen, mods)
    data = json.loads(json_data)
    
    assert data["generator"]["type"] == "MelodyGenerator"
    assert len(data["modifiers"]) == 2
    
    # Load back
    loaded_gen, loaded_mods = deserialize_preset(json_data)
    
    assert isinstance(loaded_gen, MelodyGenerator)
    assert loaded_gen.prefer_chord_tones == 0.5
    assert isinstance(loaded_mods[0], SwingController)
    assert loaded_mods[0].swing_ratio == 0.6
