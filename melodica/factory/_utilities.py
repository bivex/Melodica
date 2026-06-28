"""Utility and special-case generator mapping."""

from melodica.generators.rest import RestGenerator
from melodica.generators.step_seq import StepSequencer
from melodica.generators.dyads_run import DyadsRunGenerator
from melodica.generators.generic_gen import GenericGenerator
from melodica.generators.phrase_container import PhraseContainer
from melodica.generators.phrase_morpher import PhraseMorpher
from melodica.generators.random_note import RandomNoteGenerator
from melodica.generators.motive import MotiveGenerator
from melodica.generators.chord_layout import ChordLayoutGenerator

UTILITY_GENERATORS = {
    "rest": lambda p, cfg: RestGenerator(),
    "step_sequencer": lambda p, cfg: StepSequencer(
        params=p,
        steps=cfg.get("steps", 16),
        gate_prob=cfg.get("gate_prob", 0.8),
        velocity_map=cfg.get("velocity_map"),
        ties=cfg.get("ties"),
        root_note=cfg.get("root_note", 60),
    ),
    "dyads_run": lambda p, cfg: DyadsRunGenerator(
        params=p,
        interval=cfg.get("interval", 3),
        technique=cfg.get("technique", "up"),
        notes_per_run=cfg.get("notes_per_run", 8),
        scale_steps=cfg.get("scale_steps", False),
    ),
    "generic": lambda p, cfg: GenericGenerator(
        params=p,
        chord_note_ratio=cfg.get("chord_note_ratio", 0.7),
        partial_polyphony=cfg.get("partial_polyphony", True),
        max_polyphony=cfg.get("max_polyphony", 3),
        repeat_last=cfg.get("repeat_last", False),
    ),
    "phrase_container": lambda p, cfg: PhraseContainer(
        params=p,
        mode=cfg.get("mode", "sequential"),
    ),
    "phrase_morpher": lambda p, cfg: PhraseMorpher(
        params=p,
        steps=cfg.get("steps", 8),
        vertical_snap=cfg.get("vertical_snap", "scale"),
    ),
    "random_note": lambda p, cfg: RandomNoteGenerator(
        params=p,
        velocity_range=cfg.get("velocity_range", (40, 100)),
        note_range=cfg.get("note_range", (36, 84)),
    ),
    "motive": lambda p, cfg: MotiveGenerator(
        params=p,
        motive_length=cfg.get("motive_length", 4),
        development=cfg.get("development", "repeat"),
        scale_steps=cfg.get("scale_steps", True),
        interval_seed=cfg.get("interval_seed"),
    ),
    "chord_layout": lambda p, cfg: ChordLayoutGenerator(
        params=p,
        instrument_name=cfg.get("instrument_name", "violin"),
        instruments=cfg.get("instruments"),
        primary_melody=cfg.get("primary_melody"),
    ),
}
