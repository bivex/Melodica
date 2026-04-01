"""
composer/instrument_resolver.py — Auto-selects MIDI instruments from context.

Instead of hardcoding track_name → GM program, this resolves instruments
from generator type, mood, register, and density. Each script calls
resolver.resolve(track_name, generator_type, mood, register) and gets
the right GM program automatically.

Usage:
    resolver = InstrumentResolver(style="downtempo")
    program = resolver.resolve("melody", "melody", "flow", "mid")
    # → 88 (New Age Pad, because downtempo+flow = soft pad)

Styles: "downtempo", "dark_fantasy", "ambient", "pop", "rock", "jazz", "classical"
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# GM Program families (0-indexed)
# ---------------------------------------------------------------------------
_PIANO = range(0, 8)
_CHROMATIC_PERC = range(8, 16)
_ORGAN = range(16, 24)
_GUITAR = range(24, 32)
_BASS = range(32, 40)
_STRINGS = range(40, 48)
_ENSEMBLE = range(48, 56)
_BRASS = range(56, 64)
_REED = range(64, 72)
_PIPE = range(72, 80)
_SYNTH_LEAD = range(80, 88)
_SYNTH_PAD = range(88, 96)
_SYNTH_FX = range(96, 104)
_WORLD = range(104, 112)
_PERCUSSIVE = range(112, 120)
_SOUND_FX = range(120, 128)


# ---------------------------------------------------------------------------
# Generator type → base instrument family
# ---------------------------------------------------------------------------
_GEN_FAMILY: dict[str, range] = {
    # Melody / Lead
    "melody": _STRINGS,
    "neural_melody": _SYNTH_LEAD,
    "markov_melody": _STRINGS,
    "countermelody": _ENSEMBLE,
    "sequence": _STRINGS,
    # Bass
    "bass": _BASS,
    "walking_bass": _BASS,
    "dark_bass": _BASS,
    "synth_bass": _BASS,
    "bass_wobble": _BASS,
    "stride_piano": _BASS,
    # Chords / Pads
    "chord": _ENSEMBLE,
    "dark_pad": _SYNTH_PAD,
    "ambient": _SYNTH_PAD,
    "chorale": _ENSEMBLE,
    "voice_leading": _ENSEMBLE,
    "counterpoint": _ENSEMBLE,
    # Arpeggio
    "arpeggiator": _CHROMATIC_PERC,
    "ostinato": _CHROMATIC_PERC,
    "harp_gliss": _CHROMATIC_PERC,
    # Percussion
    "percussion": _PERCUSSIVE,
    "drum_kit": _PERCUSSIVE,
    # Guitar
    "fingerpicking": _GUITAR,
    "strum": _GUITAR,
    "riff": _GUITAR,
    "power_chord": _GUITAR,
    "guitar_sweep": _GUITAR,
    "guitar_tapping": _GUITAR,
    # Texture
    "dyads": _SYNTH_PAD,
    "tremolo": _STRINGS,
    "call_response": _ENSEMBLE,
    "canon": _ENSEMBLE,
    # FX
    "fx_riser": _SYNTH_FX,
    "fx_impact": _SOUND_FX,
    # Transition
    "transition": _SYNTH_FX,
    "hemiola": _STRINGS,
    # Groove
    "groove": _CHROMATIC_PERC,
    "swing": _CHROMATIC_PERC,
}


# ---------------------------------------------------------------------------
# Mood → specific program within family
# ---------------------------------------------------------------------------
_MOOD_OVERRIDES: dict[str, dict[int, int]] = {
    # mood: {family_range_start: specific_program}
    "fog": {
        _STRINGS.start: 92,
        _ENSEMBLE.start: 92,
        _BASS.start: 39,
        _SYNTH_PAD.start: 92,
    },  # Halo Pad
    "sleep": {
        _STRINGS.start: 89,
        _ENSEMBLE.start: 89,
        _BASS.start: 38,
        _SYNTH_PAD.start: 89,
    },  # Warm Pad
    "pulse": {
        _STRINGS.start: 49,
        _ENSEMBLE.start: 49,
        _BASS.start: 33,
        _SYNTH_PAD.start: 88,
    },  # String Ens 1
    "flow": {
        _STRINGS.start: 50,
        _ENSEMBLE.start: 50,
        _BASS.start: 32,
        _SYNTH_PAD.start: 88,
    },  # String Ens 2
    "depth": {
        _STRINGS.start: 49,
        _ENSEMBLE.start: 49,
        _BASS.start: 38,
        _SYNTH_PAD.start: 93,
    },  # Metallic Pad
    "glow": {
        _STRINGS.start: 51,
        _ENSEMBLE.start: 51,
        _BASS.start: 33,
        _SYNTH_PAD.start: 88,
    },  # Synth Strings 1
    "fade": {
        _STRINGS.start: 49,
        _ENSEMBLE.start: 49,
        _BASS.start: 32,
        _SYNTH_PAD.start: 89,
    },  # Warm Pad
    "mystery": {
        _STRINGS.start: 49,
        _ENSEMBLE.start: 49,
        _BASS.start: 43,
        _SYNTH_PAD.start: 91,
    },  # Sweep Pad
    "ominous": {
        _STRINGS.start: 49,
        _ENSEMBLE.start: 48,
        _BASS.start: 43,
        _SYNTH_PAD.start: 93,
    },  # Metallic Pad
    "tension": {
        _STRINGS.start: 44,
        _ENSEMBLE.start: 44,
        _BASS.start: 38,
        _SYNTH_PAD.start: 94,
    },  # Tremolo Strings
    "battle": {
        _STRINGS.start: 49,
        _ENSEMBLE.start: 49,
        _BASS.start: 43,
        _SYNTH_PAD.start: 80,
    },  # Lead Square
    "despair": {
        _STRINGS.start: 49,
        _ENSEMBLE.start: 49,
        _BASS.start: 43,
        _SYNTH_PAD.start: 90,
    },  # Polysynth Pad
    "ritual": {
        _STRINGS.start: 49,
        _ENSEMBLE.start: 49,
        _BASS.start: 32,
        _SYNTH_PAD.start: 88,
    },  # New Age Pad
    "climax": {
        _STRINGS.start: 51,
        _ENSEMBLE.start: 51,
        _BASS.start: 38,
        _SYNTH_PAD.start: 81,
    },  # Saw Lead
    "whisper": {
        _STRINGS.start: 49,
        _ENSEMBLE.start: 52,
        _BASS.start: 32,
        _SYNTH_PAD.start: 89,
    },  # Warm Pad
}


# ---------------------------------------------------------------------------
# Style → default overrides
# ---------------------------------------------------------------------------
_STYLE_DEFAULTS: dict[str, dict[str, int]] = {
    "downtempo": {
        "melody": 88,
        "melody2": 54,
        "counter": 89,
        "countermelody": 89,
        "bass": 32,
        "walking_bass": 32,
        "dark_bass": 38,
        "chord": 88,
        "chords": 88,
        "dark_pad": 92,
        "ambient": 89,
        "arp": 46,
        "arpeggiator": 46,
        "ostinato": 45,
        "fingerpicking": 25,
        "percussion": 0,
        "groove": 45,
        "dyads": 46,
        "swing": 45,
        "call_response": 49,
    },
    "dark_fantasy": {
        "melody": 49,
        "melody2": 52,
        "counter": 51,
        "countermelody": 51,
        "bass": 43,
        "walking_bass": 43,
        "chord": 48,
        "chords": 48,
        "dark_pad": 88,
        "ambient": 91,
        "arp": 46,
        "arpeggiator": 46,
        "fingerpicking": 25,
        "percussion": 0,
        "riff": 30,
        "ostinato": 45,
        "dyads": 46,
        "groove": 45,
        "canon": 49,
        "harp_gliss": 46,
        "piano_sweep": 0,
        "choir": 52,
        "tremolo": 44,
        "staccato": 45,
        "call_response": 49,
    },
}


class InstrumentResolver:
    """
    Resolves MIDI program numbers from context.

    Priority chain:
        1. Style defaults (exact track_name match)
        2. Mood overrides (family → specific program)
        3. Generator family (base instrument group)
        4. Register-based fallback (low=bass, mid=strings, high=lead)
        5. Default: 0 (Acoustic Grand Piano)
    """

    def __init__(self, style: str = "dark_fantasy") -> None:
        self.style = style
        self._style_defaults = _STYLE_DEFAULTS.get(style, {})
        self._cache: dict[str, int] = {}

    def resolve(
        self,
        track_name: str,
        generator_type: str = "",
        mood: str = "",
        register: str = "mid",
    ) -> int:
        """Resolve GM program number for a track."""
        cache_key = f"{track_name}:{generator_type}:{mood}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Normalize: try both track_name and generator_type as keys
        lookup_keys = [track_name, generator_type]

        # 1. Style defaults (exact match on track_name or generator_type)
        for key in lookup_keys:
            if key in self._style_defaults:
                prog = self._style_defaults[key]
                self._cache[cache_key] = prog
                return prog

        # 2. Generator family
        family = _GEN_FAMILY.get(generator_type, _PIANO)

        # 3. Mood override within family
        prog = family[0]  # first in family as default
        if mood and mood in _MOOD_OVERRIDES:
            mood_map = _MOOD_OVERRIDES[mood]
            for range_start, specific_prog in mood_map.items():
                if range_start in family:
                    prog = specific_prog
                    break

        self._cache[cache_key] = prog
        return prog

    def resolve_batch(
        self,
        tracks: dict[str, str],
        mood: str = "",
        register: str = "mid",
    ) -> dict[str, int]:
        """Resolve instruments for multiple tracks. tracks = {name: generator_type}."""
        return {
            name: self.resolve(name, gen_type, mood, register) for name, gen_type in tracks.items()
        }
