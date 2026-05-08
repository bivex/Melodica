"""Pattern-based generator mapping."""

from melodica.generators import (
    CanonGenerator,
    CallResponseGenerator,
    ModernChordPatternGenerator,
    FingerpickingGenerator,
    WalkingBassGenerator,
    AlbertiBassGenerator,
    DroneGenerator,
    CountermelodyGenerator,
    SequenceGenerator,
    BluesLickGenerator,
    HocketGenerator,
)

PATTERN_GENERATORS = {
    "canon": lambda p, cfg: CanonGenerator(
        params=p,
        delay_beats=cfg.get("delay_beats", 2.0),
        interval=cfg.get("interval", 7),
    ),
    "call_response": lambda p, cfg: CallResponseGenerator(
        params=p,
        call_length=cfg.get("call_length", 2.0),
        response_length=cfg.get("response_length", 2.0),
    ),
    "modern_chord": lambda p, cfg: ModernChordPatternGenerator(
        params=p,
        stab_pattern=cfg.get("stab_pattern", "syncopated"),
    ),
    "fingerpicking": lambda p, cfg: FingerpickingGenerator(
        params=p,
        pattern=cfg.get("pattern", [0, 2, 1, 3]),
    ),
    "walking_bass": lambda p, cfg: WalkingBassGenerator(
        params=p,
        approach_style=cfg.get("approach_style", "mixed"),
        connect_roots=cfg.get("connect_roots", True),
        add_chromatic_passing=cfg.get("add_chromatic_passing", True),
    ),
    "alberti_bass": lambda p, cfg: AlbertiBassGenerator(
        params=p,
        pattern=cfg.get("pattern", "1-5-3-5"),
        subdivision=cfg.get("subdivision", 0.5),
        voice_lead=cfg.get("voice_lead", True),
    ),
    "drone": lambda p, cfg: DroneGenerator(
        params=p,
        variant=cfg.get("variant", "tonic"),
        fade_in=cfg.get("fade_in", 0.0),
        fade_out=cfg.get("fade_out", 0.0),
        retrigger_on_chord=cfg.get("retrigger_on_chord", True),
    ),
    "countermelody": lambda p, cfg: CountermelodyGenerator(
        params=p,
        primary_melody=cfg.get("primary_melody"),
        motion_preference=cfg.get("motion_preference", "mixed"),
        dissonance_on_weak=cfg.get("dissonance_on_weak", True),
        interval_limit=cfg.get("interval_limit", 7),
    ),
    "sequence": lambda p, cfg: SequenceGenerator(
        params=p,
        motif_length=cfg.get("motif_length", 4),
        sequence_type=cfg.get("sequence_type", "descending"),
        interval_steps=cfg.get("interval_steps", 1),
        repetitions=cfg.get("repetitions", 0),
        generate_motif=cfg.get("generate_motif", True),
        motif_notes=cfg.get("motif_notes"),
    ),
    "blues_lick": lambda p, cfg: BluesLickGenerator(
        params=p,
        lick_style=cfg.get("lick_style", "standard"),
        phrase_length=cfg.get("phrase_length", 4),
        rest_probability=cfg.get("rest_probability", 0.3),
        enclosure_probability=cfg.get("enclosure_probability", 0.2),
        bend_probability=cfg.get("bend_probability", 0.15),
    ),
    "hocket": lambda p, cfg: HocketGenerator(
        params=p,
        hocket_pattern=cfg.get("hocket_pattern", "alternating"),
        voice_index=cfg.get("voice_index", 0),
        euclidean_pulses=cfg.get("euclidean_pulses", 3),
        euclidean_steps=cfg.get("euclidean_steps", 4),
    ),
}
