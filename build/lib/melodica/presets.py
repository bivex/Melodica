"""
presets.py — Save/Load Idea Tool presets (JSON).

Layer: Infrastructure (Persistence)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from melodica.generators import (
    ArpeggiatorGenerator,
    BassGenerator,
    CallResponseGenerator,
    CanonGenerator,
    ChordGenerator,
    DyadGenerator,
    DyadsRunGenerator,
    FingerpickingGenerator,
    GenericGenerator,
    GrooveGenerator,
    MarkovMelodyGenerator,
    MelodyGenerator,
    ModernChordPatternGenerator,
    MotiveGenerator,
    OstinatoGenerator,
    PedalBassGenerator,
    PercussionGenerator,
    PhraseContainer,
    PhraseMorpher,
    PianoRunGenerator,
    RiffGenerator,
    RandomNoteGenerator,
    StepSequencer,
    StrumPatternGenerator,
    GeneratorParams,
    StringsStaccatoGenerator,
    RestGenerator,
    AmbientPadGenerator,
)
from melodica.modifiers import (
    CrescendoModifier,
    HumanizeModifier,
    QuantizeModifier,
    SwingController,
    TransposeModifier,
    LimitNoteRangeModifier,
    VelocityScalingModifier,
    AdjustNoteLengthsModifier,
    NoteDoublerModifier,
    VoiceLeadingModifier,
    GrooveModifier,
    PolishedOctaveModifier,
    FollowRhythmModifier,
)
from melodica.rhythm import (
    EuclideanRhythmGenerator,
    ProbabilisticRhythmGenerator,
    SubdivisionGenerator,
    SchillingerGenerator,
    MotifRhythmGenerator,
    StaticRhythmGenerator,
)


GENERATOR_CLASSES = {
    "ArpeggiatorGenerator": ArpeggiatorGenerator,
    "BassGenerator": BassGenerator,
    "ChordGenerator": ChordGenerator,
    "DyadGenerator": DyadGenerator,
    "FingerpickingGenerator": FingerpickingGenerator,
    "MarkovMelodyGenerator": MarkovMelodyGenerator,
    "MelodyGenerator": MelodyGenerator,
    "OstinatoGenerator": OstinatoGenerator,
    "PianoRunGenerator": PianoRunGenerator,
    "StrumPatternGenerator": StrumPatternGenerator,
    "StringsStaccatoGenerator": StringsStaccatoGenerator,
    "RestGenerator": RestGenerator,
    "AmbientPadGenerator": AmbientPadGenerator,
    "RiffGenerator": RiffGenerator,
    "StepSequencer": StepSequencer,
    "CanonGenerator": CanonGenerator,
    "CallResponseGenerator": CallResponseGenerator,
    "PedalBassGenerator": PedalBassGenerator,
    "GrooveGenerator": GrooveGenerator,
    "DyadsRunGenerator": DyadsRunGenerator,
    "GenericGenerator": GenericGenerator,
    "ModernChordPatternGenerator": ModernChordPatternGenerator,
    "MotiveGenerator": MotiveGenerator,
    "PhraseContainer": PhraseContainer,
    "PercussionGenerator": PercussionGenerator,
    "PhraseMorpher": PhraseMorpher,
    "RandomNoteGenerator": RandomNoteGenerator,
}

RHYTHM_CLASSES = {
    "EuclideanRhythmGenerator": EuclideanRhythmGenerator,
    "ProbabilisticRhythmGenerator": ProbabilisticRhythmGenerator,
    "SubdivisionGenerator": SubdivisionGenerator,
    "SchillingerGenerator": SchillingerGenerator,
    "MotifRhythmGenerator": MotifRhythmGenerator,
    "StaticRhythmGenerator": StaticRhythmGenerator,
}

MODIFIER_CLASSES = {
    "CrescendoModifier": CrescendoModifier,
    "HumanizeModifier": HumanizeModifier,
    "QuantizeModifier": QuantizeModifier,
    "SwingController": SwingController,
    "TransposeModifier": TransposeModifier,
    "LimitNoteRangeModifier": LimitNoteRangeModifier,
    "VelocityScalingModifier": VelocityScalingModifier,
    "AdjustNoteLengthsModifier": AdjustNoteLengthsModifier,
    "NoteDoublerModifier": NoteDoublerModifier,
    "VoiceLeadingModifier": VoiceLeadingModifier,
    "GrooveModifier": GrooveModifier,
    "PolishedOctaveModifier": PolishedOctaveModifier,
    "FollowRhythmModifier": FollowRhythmModifier,
}


def _serialize_value(v: Any) -> Any:
    """Serialize a config value, converting RhythmGenerator instances to dicts."""
    cls_name = type(v).__name__
    if cls_name in RHYTHM_CLASSES:
        return {
            "type": cls_name,
            "config": {k: val for k, val in vars(v).items() if not k.startswith("_")},
        }
    return v


def _deserialize_rhythm(v: Any) -> Any:
    """Reconstruct a RhythmGenerator from a serialized dict, or return v unchanged."""
    if not isinstance(v, dict):
        return v
    cls = RHYTHM_CLASSES.get(v.get("type", ""))
    if cls is None:
        return v
    return cls(**v["config"])


def serialize_preset(generator: Any, modifiers: list[Any]) -> str:
    """Converts a generator and its modifiers into a JSON string."""
    data = {
        "generator": {
            "type": generator.__class__.__name__,
            "params": vars(generator.params),
            "config": {
                k: _serialize_value(v)
                for k, v in vars(generator).items()
                if k != "params" and not k.startswith("_")
            },
        },
        "modifiers": [
            {
                "type": m.__class__.__name__,
                "config": {k: v for k, v in vars(m).items() if not k.startswith("_")},
            }
            for m in modifiers
        ],
    }
    return json.dumps(data, indent=2)


def deserialize_preset(json_str: str) -> tuple[Any, list[Any]]:
    """Reconstructs a generator and modifiers from a JSON string."""
    data = json.loads(json_str)

    gen_data = data["generator"]
    gen_cls = GENERATOR_CLASSES[gen_data["type"]]
    params = GeneratorParams(**gen_data["params"])
    config = {
        k: _deserialize_rhythm(v) if k == "rhythm" else v for k, v in gen_data["config"].items()
    }
    generator = gen_cls(params=params, **config)

    modifiers = []
    for m_data in data["modifiers"]:
        m_cls = MODIFIER_CLASSES[m_data["type"]]
        modifiers.append(m_cls(**m_data["config"]))

    return generator, modifiers


def save_preset(name: str, generator: Any, modifiers: list[Any], folder: str = "presets") -> Path:
    path = Path(folder) / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_preset(generator, modifiers))
    return path


def load_preset(name: str, folder: str = "presets") -> tuple[Any, list[Any]]:
    path = Path(folder) / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Preset {name} not found in {folder}")
    return deserialize_preset(path.read_text())
