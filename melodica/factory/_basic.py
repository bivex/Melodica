"""Basic generator mapping."""

from melodica.generators import (
    MelodyGenerator,
    ArpeggiatorGenerator,
    BassGenerator,
    ChordGenerator,
    OstinatoGenerator,
    StrumPatternGenerator,
    PercussionGenerator,
    RiffGenerator,
    GrooveGenerator,
    PianoRunGenerator,
    DyadGenerator,
    AmbientPadGenerator,
)

BASIC_GENERATORS = {
    "melody": lambda p, cfg: MelodyGenerator(
        params=p,
        harmony_note_probability=cfg.get("harmony_note_probability", 0.64),
        note_range_low=cfg.get("note_range_low"),
        note_range_high=cfg.get("note_range_high"),
    ),
    "arpeggiator": lambda p, cfg: ArpeggiatorGenerator(
        params=p,
        pattern=cfg.get("pattern", "up"),
        note_duration=cfg.get("note_duration", 0.25),
    ),
    "bass": lambda p, cfg: BassGenerator(
        params=p,
        allowed_notes=cfg.get("allowed_notes", ["root", "fourth"]),
        global_movement=cfg.get("global_movement", "none"),
        note_movement=cfg.get("note_movement", "alternating"),
    ),
    "chord": lambda p, cfg: ChordGenerator(
        params=p,
        voicing=cfg.get("voicing", "open"),
    ),
    "ostinato": lambda p, cfg: OstinatoGenerator(
        params=p,
        pattern=cfg.get("pattern", "1-3-5-3"),
    ),
    "strum": lambda p, cfg: StrumPatternGenerator(
        params=p,
        voicing=cfg.get("voicing", "guitar"),
        pattern_name=cfg.get("pattern_name", "folk"),
    ),
    "percussion": lambda p, cfg: PercussionGenerator(
        params=p,
        pattern_name=cfg.get("pattern_name", "rock"),
    ),
    "riff": lambda p, cfg: RiffGenerator(
        params=p,
        scale_type=cfg.get("scale_type", "minor_pent"),
        riff_pattern=cfg.get("riff_pattern", "gallop"),
    ),
    "groove": lambda p, cfg: GrooveGenerator(
        params=p,
        groove_pattern=cfg.get("groove_pattern", "funk_1"),
    ),
    "piano_run": lambda p, cfg: PianoRunGenerator(
        params=p,
        technique=cfg.get("technique", "straddle"),
        notes_per_run=cfg.get("notes_per_run", 8),
    ),
    "dyads": lambda p, cfg: DyadGenerator(
        params=p,
        interval_pref=cfg.get("interval_pref", [3, 4, 7]),
        motion_mode=cfg.get("motion_mode", "parallel"),
    ),
    "ambient": lambda p, cfg: AmbientPadGenerator(
        params=p,
        voicing=cfg.get("voicing", "spread"),
        overlap=cfg.get("overlap", 0.5),
    ),
}
