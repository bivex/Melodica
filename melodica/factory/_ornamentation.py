"""Ornamentation and articulation generator mapping."""

from melodica.generators import (
    TrillTremoloGenerator,
    OrnamentationGenerator,
    FillGenerator,
    PickupGenerator,
    GlissandoGenerator,
)

ORNAMENTATION_GENERATORS = {
    "trill": lambda p, cfg: TrillTremoloGenerator(
        params=p,
        ornament_type=cfg.get("ornament_type", "trill"),
        speed=cfg.get("speed", 0.125),
        base_note_strategy=cfg.get("base_note_strategy", "chord_tone"),
        neighbor_interval=cfg.get("neighbor_interval", "auto"),
        probability=cfg.get("probability", 0.8),
    ),
    "tremolo": lambda p, cfg: TrillTremoloGenerator(
        params=p,
        ornament_type=cfg.get("ornament_type", "tremolo"),
        speed=cfg.get("speed", 0.125),
        base_note_strategy=cfg.get("base_note_strategy", "chord_tone"),
        neighbor_interval=cfg.get("neighbor_interval", "auto"),
        probability=cfg.get("probability", 0.8),
    ),
    "ornamentation": lambda p, cfg: OrnamentationGenerator(
        params=p,
        ornament_type=cfg.get("ornament_type", "mordent"),
        neighbor_interval=cfg.get("neighbor_interval", 0),
        speed=cfg.get("speed", 0.125),
        base_note=cfg.get("base_note", "chord_tone"),
        density_ornaments=cfg.get("density_ornaments", 0.8),
    ),
    "fill": lambda p, cfg: FillGenerator(
        params=p,
        fill_type=cfg.get("fill_type", "descending"),
        fill_length=cfg.get("fill_length", 2.0),
        fill_every_bars=cfg.get("fill_every_bars", 4.0),
        beats_per_bar=cfg.get("beats_per_bar", 4),
        position=cfg.get("position", "end"),
        velocity_curve=cfg.get("velocity_curve", "crescendo"),
    ),
    "turnaround": lambda p, cfg: FillGenerator(
        params=p,
        fill_type=cfg.get("fill_type", "descending"),
        fill_length=cfg.get("fill_length", 2.0),
        fill_every_bars=cfg.get("fill_every_bars", 4.0),
        beats_per_bar=cfg.get("beats_per_bar", 4),
        position=cfg.get("position", "end"),
        velocity_curve=cfg.get("velocity_curve", "crescendo"),
    ),
    "pickup": lambda p, cfg: PickupGenerator(
        params=p,
        pickup_type=cfg.get("pickup_type", "scale_down"),
        pickup_length=cfg.get("pickup_length", 1.0),
        target_on_downbeat=cfg.get("target_on_downbeat", True),
    ),
    "glissando": lambda p, cfg: GlissandoGenerator(
        params=p,
        gliss_type=cfg.get("gliss_type", "chromatic"),
        speed=cfg.get("speed", 0.0625),
        gliss_length=cfg.get("gliss_length", 1.0),
        start_note=cfg.get("start_note", "octave"),
    ),
}
