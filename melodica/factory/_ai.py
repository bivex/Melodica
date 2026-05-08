"""AI/Markov/Neural generator mapping."""

from melodica.generators import (
    MarkovMelodyGenerator,
    NeuralMelodyGenerator,
)

AI_GENERATORS = {
    "markov": lambda p, cfg: MarkovMelodyGenerator(
        params=p,
        note_repetition_probability=cfg.get("note_repetition_probability", 0.14),
        harmony_note_probability=cfg.get("harmony_note_probability", 0.64),
        direction_bias=cfg.get("direction_bias", 0.0),
    ),
    "neural": lambda p, cfg: NeuralMelodyGenerator(
        params=p,
        model_path=cfg.get("model_path"),
        temperature=cfg.get("temperature", 1.0),
        top_p=cfg.get("top_p", 0.92),
        harmony_prob=cfg.get("harmony_prob", 0.55),
        direction_bias=cfg.get("direction_bias", 0.0),
        note_range_low=cfg.get("note_range_low"),
        note_range_high=cfg.get("note_range_high"),
        device=cfg.get("device", "cpu"),
    ),
}
