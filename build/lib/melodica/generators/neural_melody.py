# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/neural_melody.py — NeuralMelodyGenerator.

Layer: Application / Domain
Style: All genres — learned from MIDI data.

GPT-2–style causal Transformer melody generator with REMI tokenization.
Chord sequence is prepended as a conditioning prefix; melody is sampled
autoregressively.

Two execution modes (same public API, chosen automatically):

  NEURAL mode  — torch is installed AND model_path points to a .pt file.
                 Transformer forward pass + top-p / temperature sampling.

  FALLBACK mode — torch missing OR no model_path.
                 2nd-order Markov + chord-tone attraction + phrase shaping.
                 Produces musical output immediately with no weights needed.

Quick start:
    gen = NeuralMelodyGenerator()                # fallback, works instantly
    gen = NeuralMelodyGenerator(model_path="melody.pt")  # neural

Training:
    NeuralMelodyGenerator.train_from_notes(notes, output_path="melody.pt")

Install neural deps:
    pip install -e '.[neural]'    # torch>=2.0, no other requirement
"""

from __future__ import annotations

import math
import os
import random
from dataclasses import dataclass, field
from typing import Any

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Quality, Scale
from melodica.utils import nearest_pitch, chord_at


# ---------------------------------------------------------------------------
# REMI-style token vocabulary (self-contained, no miditok dependency)
# ---------------------------------------------------------------------------

_PAD = 0
_BOS = 1
_EOS = 2
_BAR = 3
_POS_BASE = 4  # tokens 4..19  → 16 position slots (16th-note grid)
_PITCH_BASE = 20  # tokens 20..147 → MIDI pitches 0..127
_DUR_BASE = 148  # tokens 148..163 → durations in 16th-note units 1..16
_CROOT_BASE = 164  # tokens 164..175 → chord root 0..11
_CQUAL_BASE = 176  # tokens 176..181 → chord quality (6 types)
_KROOT_BASE = 182  # tokens 182..193 → key root 0..11
_KMODE_BASE = 194  # tokens 194..200 → key mode (7 values)
VOCAB_SIZE = 201

_QUAL_ORDER = [
    Quality.MAJOR,
    Quality.MINOR,
    Quality.DOMINANT7,
    Quality.MAJOR7,
    Quality.MINOR7,
    Quality.DIMINISHED,
]
_QUAL_TO_IDX: dict[Quality, int] = {q: i for i, q in enumerate(_QUAL_ORDER)}

from melodica.types import Mode

_MODE_ORDER = [
    Mode.MAJOR,
    Mode.NATURAL_MINOR,
    Mode.HARMONIC_MINOR,
    Mode.DORIAN,
    Mode.PHRYGIAN,
    Mode.LYDIAN,
    Mode.MIXOLYDIAN,
]
_MODE_TO_IDX: dict[Mode, int] = {m: i for i, m in enumerate(_MODE_ORDER)}


def _encode_chords(chords: list[ChordLabel], key: Scale) -> list[int]:
    """Encode chord + key context as prefix tokens."""
    tokens: list[int] = [_BOS]
    # Key
    tokens.append(_KROOT_BASE + key.root)
    tokens.append(_KMODE_BASE + _MODE_TO_IDX.get(key.mode, 0))
    # Chords (max 16 unique changes)
    seen_starts: set[float] = set()
    for c in chords[:16]:
        if c.start in seen_starts:
            continue
        seen_starts.add(c.start)
        tokens.append(_CROOT_BASE + (c.root % 12))
        tokens.append(_CQUAL_BASE + _QUAL_TO_IDX.get(c.quality, 0))
    tokens.append(_BAR)
    return tokens


def _encode_notes(notes: list[NoteInfo], duration_beats: float) -> list[int]:
    """Encode a melody sequence as REMI tokens."""
    tokens: list[int] = []
    beats_per_bar = 4.0
    step = 0.25  # 16th note

    for note in notes:
        bar_idx = int(note.start / beats_per_bar)
        pos_in_bar = note.start - bar_idx * beats_per_bar
        pos_slot = max(0, min(15, int(round(pos_in_bar / step))))
        dur_slots = max(1, min(16, int(round(note.duration / step))))
        pitch = max(0, min(127, note.pitch))

        tokens.append(_POS_BASE + pos_slot)
        tokens.append(_PITCH_BASE + pitch)
        tokens.append(_DUR_BASE + dur_slots - 1)

    tokens.append(_EOS)
    return tokens


def _decode_tokens(
    tokens: list[int],
    chords: list[ChordLabel],
    duration_beats: float,
    events: list[RhythmEvent],
) -> list[NoteInfo]:
    """Decode REMI tokens back to NoteInfo, aligned to rhythm events."""
    pitches: list[int] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == _EOS:
            break
        if _PITCH_BASE <= tok < _PITCH_BASE + 128:
            pitches.append(tok - _PITCH_BASE)
        i += 1

    notes: list[NoteInfo] = []
    for j, event in enumerate(events):
        if j >= len(pitches):
            break
        notes.append(
            NoteInfo(
                pitch=max(0, min(127, pitches[j])),
                start=round(event.onset, 6),
                duration=event.duration,
                velocity=80,
            )
        )
    return notes


# ---------------------------------------------------------------------------
# Tiny GPT-2 Transformer (optional, requires torch)
# ---------------------------------------------------------------------------


def _build_model(
    vocab_size: int = VOCAB_SIZE,
    d_model: int = 128,
    n_heads: int = 4,
    n_layers: int = 4,
    ffn_dim: int = 256,
    max_len: int = 512,
) -> Any:
    """Build a small causal transformer. Returns None if torch missing."""
    try:
        import torch
        import torch.nn as nn

        class _CausalSelfAttention(nn.Module):
            def __init__(self):
                super().__init__()
                self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
                self.register_buffer(
                    "mask",
                    torch.triu(torch.ones(max_len, max_len), diagonal=1).bool(),
                )

            def forward(self, x):
                T = x.size(1)
                mask = self.mask[:T, :T]
                out, _ = self.attn(x, x, x, attn_mask=mask, is_causal=True)
                return out

        class _Block(nn.Module):
            def __init__(self):
                super().__init__()
                self.ln1 = nn.LayerNorm(d_model)
                self.attn = _CausalSelfAttention()
                self.ln2 = nn.LayerNorm(d_model)
                self.ff = nn.Sequential(
                    nn.Linear(d_model, ffn_dim),
                    nn.GELU(),
                    nn.Linear(ffn_dim, d_model),
                )

            def forward(self, x):
                x = x + self.attn(self.ln1(x))
                x = x + self.ff(self.ln2(x))
                return x

        class MelodyTransformer(nn.Module):
            def __init__(self):
                super().__init__()
                self.tok_emb = nn.Embedding(vocab_size, d_model)
                self.pos_emb = nn.Embedding(max_len, d_model)
                self.blocks = nn.Sequential(*[_Block() for _ in range(n_layers)])
                self.ln_f = nn.LayerNorm(d_model)
                self.head = nn.Linear(d_model, vocab_size, bias=False)

            def forward(self, x):
                import torch

                T = x.size(1)
                pos = torch.arange(T, device=x.device).unsqueeze(0)
                h = self.tok_emb(x) + self.pos_emb(pos)
                h = self.blocks(h)
                h = self.ln_f(h)
                return self.head(h)

        return MelodyTransformer()
    except ImportError:
        return None


def _top_p_sample(logits: Any, temperature: float, top_p: float, rng: Any) -> int:
    """Nucleus (top-p) sampling. Requires torch."""
    import torch
    import torch.nn.functional as F

    logits = logits / max(temperature, 1e-6)
    probs = F.softmax(logits, dim=-1)
    sorted_probs, sorted_idx = torch.sort(probs, descending=True)
    cum_probs = torch.cumsum(sorted_probs, dim=-1)
    cutoff = (cum_probs - sorted_probs) > top_p
    sorted_probs[cutoff] = 0.0
    sorted_probs /= sorted_probs.sum()
    choice = torch.multinomial(sorted_probs, 1).item()
    return int(sorted_idx[choice].item())


# ---------------------------------------------------------------------------
# 2nd-order Markov fallback
# ---------------------------------------------------------------------------

_MARKOV2: dict[tuple[int, int], dict[int, float]] = {
    # (prev_interval, cur_interval) → {next_interval: prob}
    (0, 0): {0: 0.15, 1: 0.25, -1: 0.25, 2: 0.15, -2: 0.15, 3: 0.05},
    (0, 1): {1: 0.30, 2: 0.25, 0: 0.20, 3: 0.15, -1: 0.10},
    (0, -1): {-1: 0.30, -2: 0.25, 0: 0.20, -3: 0.15, 1: 0.10},
    (1, 1): {1: 0.25, 2: 0.20, 0: 0.25, -1: 0.20, 3: 0.10},
    (1, 2): {1: 0.30, 0: 0.25, -1: 0.20, 2: 0.15, -2: 0.10},
    (1, -1): {0: 0.30, -1: 0.25, 1: 0.25, -2: 0.20},
    (-1, -1): {-1: 0.25, -2: 0.20, 0: 0.25, 1: 0.20, -3: 0.10},
    (-1, -2): {-1: 0.30, 0: 0.25, 1: 0.20, -2: 0.15, 2: 0.10},
    (-1, 1): {0: 0.30, 1: 0.25, -1: 0.25, 2: 0.20},
    (2, 2): {1: 0.30, 0: 0.25, -1: 0.20, 2: 0.15, -2: 0.10},
    (2, 1): {0: 0.30, 1: 0.25, 2: 0.20, -1: 0.25},
    (-2, -2): {-1: 0.30, 0: 0.25, 1: 0.20, -2: 0.15, 2: 0.10},
    (-2, -1): {0: 0.30, -1: 0.25, -2: 0.20, 1: 0.25},
    (3, 3): {0: 0.35, -1: 0.25, 1: 0.25, 2: 0.15},
    (-3, -3): {0: 0.35, 1: 0.25, -1: 0.25, -2: 0.15},
}

_MARKOV1: dict[int, dict[int, float]] = {
    0: {0: 0.15, 1: 0.25, -1: 0.25, 2: 0.12, -2: 0.12, 3: 0.06, -3: 0.05},
    1: {1: 0.28, 2: 0.20, 0: 0.22, -1: 0.18, 3: 0.07, -2: 0.05},
    -1: {-1: 0.28, -2: 0.20, 0: 0.22, 1: 0.18, -3: 0.07, 2: 0.05},
    2: {1: 0.28, 0: 0.22, -1: 0.18, 2: 0.18, 3: 0.08, -2: 0.06},
    -2: {-1: 0.28, 0: 0.22, 1: 0.18, -2: 0.18, -3: 0.08, 2: 0.06},
    3: {1: 0.30, 0: 0.28, -1: 0.22, 2: 0.12, -2: 0.08},
    -3: {-1: 0.30, 0: 0.28, 1: 0.22, -2: 0.12, 2: 0.08},
    4: {0: 0.35, -1: 0.25, -2: 0.20, 1: 0.15, -3: 0.05},
    -4: {0: 0.35, 1: 0.25, 2: 0.20, -1: 0.15, 3: 0.05},
    7: {-1: 0.30, -2: 0.25, 0: 0.25, -3: 0.10, 1: 0.10},
    -7: {1: 0.30, 2: 0.25, 0: 0.25, 3: 0.10, -1: 0.10},
}


def _markov2_step(prev_iv: int, cur_iv: int) -> int:
    key = (max(-3, min(3, prev_iv)), max(-3, min(3, cur_iv)))
    if key in _MARKOV2:
        d = _MARKOV2[key]
    else:
        k1 = max(-3, min(3, cur_iv))
        d = _MARKOV1.get(k1, _MARKOV1[0])
    return random.choices(list(d), weights=list(d.values()), k=1)[0]


def _snap_to_key(pitch: int, key: Scale, low: int, high: int) -> int:
    if key.contains(pitch % 12):
        return pitch
    for offset in [1, -1, 2, -2]:
        if key.contains((pitch + offset) % 12):
            return max(low, min(high, pitch + offset))
    return pitch


def _snap_to_chord(pitch: int, chord: ChordLabel, threshold: int = 2) -> int:
    pcs = chord.pitch_classes()
    if not pcs or (pitch % 12) in pcs:
        return pitch
    best = min((nearest_pitch(pc, pitch) for pc in pcs), key=lambda p: abs(p - pitch))
    if abs(best - pitch) <= threshold:
        return best
    return pitch


def _fallback_render(
    chords: list[ChordLabel],
    key: Scale,
    duration_beats: float,
    context: RenderContext | None,
    events: list[RhythmEvent],
    params: GeneratorParams,
    harmony_prob: float,
    direction_bias: float,
    note_range_low: int | None,
    note_range_high: int | None,
) -> list[NoteInfo]:
    low = note_range_low if note_range_low is not None else params.key_range_low
    high = note_range_high if note_range_high is not None else params.key_range_high

    prev_pitch = (
        context.prev_pitch
        if context and context.prev_pitch is not None
        else nearest_pitch(chords[0].root if chords else 0, (low + high) // 2)
    )

    prev_iv, cur_iv = 0, 0
    notes: list[NoteInfo] = []

    for idx, event in enumerate(events):
        chord = chord_at(chords, event.onset)

        # Chord-tone attraction on strong beats or randomly
        is_strong = (event.onset % 2.0) < 0.1
        if chord and (is_strong or random.random() < harmony_prob):
            pcs = chord.pitch_classes()
            if pcs:
                ct = min(
                    (nearest_pitch(pc, prev_pitch) for pc in pcs), key=lambda p: abs(p - prev_pitch)
                )
                next_iv = max(-12, min(12, ct - prev_pitch))
            else:
                next_iv = _markov2_step(prev_iv, cur_iv)
        else:
            next_iv = _markov2_step(prev_iv, cur_iv)

        # Direction bias
        if next_iv == 0 and direction_bias != 0.0 and random.random() < abs(direction_bias):
            next_iv = 1 if direction_bias > 0 else -1

        pitch = prev_pitch + next_iv

        # Octave bounce
        if pitch < low:
            pitch += 12
        elif pitch > high:
            pitch -= 12

        # Key snap
        active_key = key.get_key_at(event.onset) if hasattr(key, "get_key_at") else key
        pitch = _snap_to_key(pitch, active_key, low, high)

        # Final clamp
        pitch = max(low, min(high, pitch))

        # Phrase-position velocity
        phrase_pos = context.phrase_position if context else 0.0
        base_vel = int(60 + params.density * 30)
        progress = event.onset / max(duration_beats, 0.001)
        arch = 1.0 - 0.3 + 0.3 * math.sin(progress * math.pi * 0.7)
        intensity = 0.7 + 0.3 * phrase_pos
        vel = max(1, min(127, int(base_vel * arch * intensity * event.velocity_factor)))

        notes.append(
            NoteInfo(
                pitch=pitch,
                start=round(event.onset, 6),
                duration=event.duration,
                velocity=vel,
            )
        )

        prev_iv, cur_iv = cur_iv, max(-12, min(12, pitch - prev_pitch))
        prev_pitch = pitch

    return notes


# ---------------------------------------------------------------------------
# NeuralMelodyGenerator
# ---------------------------------------------------------------------------


@dataclass
class NeuralMelodyGenerator(PhraseGenerator):
    """
    Transformer-based melody generator.

    Parameters
    ----------
    model_path:
        Path to a .pt file saved by ``train_from_notes()``.
        If None or file absent, falls back to 2nd-order Markov.
    temperature:
        Sampling temperature for the neural path (0.5 = conservative,
        1.2 = creative).  Clamped to [0.1, 2.0].
    top_p:
        Nucleus sampling cutoff (0.9 = keep tokens covering 90% mass).
    harmony_prob:
        Fallback mode — probability of snapping to chord tone at any event.
    direction_bias:
        Fallback mode — gentle pitch tendency (+1 = upward, −1 = downward).
    note_range_low / note_range_high:
        Override params range for this generator.
    rhythm:
        RhythmGenerator for event timing.  None → density-based 8th notes.
    device:
        'cpu' or 'cuda'.  Ignored in fallback mode.
    """

    name: str = "Neural Melody Generator"
    model_path: str | None = None
    temperature: float = 1.0
    top_p: float = 0.92
    harmony_prob: float = 0.55
    direction_bias: float = 0.0
    note_range_low: int | None = None
    note_range_high: int | None = None
    rhythm: RhythmGenerator | None = None
    device: str = "cpu"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        model_path: str | None = None,
        temperature: float = 1.0,
        top_p: float = 0.92,
        harmony_prob: float = 0.55,
        direction_bias: float = 0.0,
        note_range_low: int | None = None,
        note_range_high: int | None = None,
        rhythm: RhythmGenerator | None = None,
        device: str = "cpu",
    ) -> None:
        super().__init__(params)
        self.model_path = model_path
        self.temperature = max(0.1, min(2.0, temperature))
        self.top_p = max(0.1, min(1.0, top_p))
        self.harmony_prob = max(0.0, min(1.0, harmony_prob))
        self.direction_bias = direction_bias
        self.note_range_low = note_range_low
        self.note_range_high = note_range_high
        self.rhythm = rhythm
        self.device = device
        self._model: Any = None
        self._last_context: RenderContext | None = None
        self._try_load_model()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        events = self._build_events(duration_beats)
        if not events:
            return []

        if self._model is not None:
            notes = self._neural_render(chords, key, duration_beats, context, events)
        else:
            notes = _fallback_render(
                chords,
                key,
                duration_beats,
                context,
                events,
                self.params,
                self.harmony_prob,
                self.direction_bias,
                self.note_range_low,
                self.note_range_high,
            )

        last_chord = chord_at(chords, events[-1].onset) or chords[-1]
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    @property
    def is_neural(self) -> bool:
        """True when the transformer model is loaded and active."""
        return self._model is not None

    # ------------------------------------------------------------------
    # Training (delegates to _neural_training.NeuralTrainer)
    # ------------------------------------------------------------------

    @classmethod
    def generate_training_data(
        cls,
        generator: "PhraseGenerator",
        chord_sets: list[list[ChordLabel]],
        keys: list[Scale],
        duration_beats: float = 8.0,
        n_samples: int | None = None,
    ) -> list[tuple[list[NoteInfo], list[ChordLabel], Scale]]:
        """
        Generate a training dataset by rendering *generator* over every
        (chord_set, key) combination.

        Parameters
        ----------
        generator:
            Any PhraseGenerator — MelodyGenerator, MarkovMelodyGenerator, etc.
        chord_sets:
            List of chord progressions.  Each item is a list of ChordLabel.
        keys:
            List of Scale objects.  Paired with chord_sets via zip (or cross-product
            if len(keys) == 1).
        duration_beats:
            Length of each generated phrase.
        n_samples:
            Cap total samples (None = all combinations).

        Returns
        -------
        List of (notes, chords, key) tuples ready for train_from_dataset().

        Example
        -------
        >>> from melodica.generators import MelodyGenerator, MarkovMelodyGenerator
        >>> from melodica.types import Scale, Mode, ChordLabel, Quality
        >>> key = Scale(root=0, mode=Mode.MAJOR)
        >>> progressions = [
        ...     [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ...      ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0)],
        ...     [ChordLabel(root=5, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ...      ChordLabel(root=0, quality=Quality.MAJOR, start=4.0, duration=4.0)],
        ... ]
        >>> dataset = NeuralMelodyGenerator.generate_training_data(
        ...     MelodyGenerator(), progressions, [key], n_samples=200
        ... )
        >>> NeuralMelodyGenerator.train_from_dataset(dataset, "melody.pt", epochs=30)
        """
        from melodica.generators._neural_training import NeuralTrainer

        return NeuralTrainer.generate_training_data(
            generator,
            chord_sets,
            keys,
            duration_beats=duration_beats,
            n_samples=n_samples,
        )

    @classmethod
    def train_from_dataset(
        cls,
        dataset: list[tuple[list[NoteInfo], list[ChordLabel], Scale]],
        output_path: str,
        *,
        epochs: int = 30,
        lr: float = 3e-4,
        batch_size: int = 32,
        seq_len: int = 256,
        device: str = "cpu",
        verbose: bool = True,
    ) -> "NeuralMelodyGenerator":
        """
        Train from a dataset of (notes, chords, key) tuples.

        Each tuple is tokenized independently as ``chord_prefix + melody_tokens``.
        All sequences are concatenated into one long token stream and trained
        with sliding windows (same as ``train_from_notes``).

        Parameters
        ----------
        dataset:    list of (notes, chords, key) — from generate_training_data()
                    or assembled manually.
        output_path: where to save the .pt weights file.
        epochs:     training epochs.
        lr:         AdamW learning rate.
        batch_size: sequences per gradient step.
        seq_len:    context window length in tokens.
        device:     'cpu' or 'cuda'.
        verbose:    print loss per epoch.

        Returns a NeuralMelodyGenerator loaded with the trained weights.

        Example
        -------
        >>> dataset = NeuralMelodyGenerator.generate_training_data(
        ...     MarkovMelodyGenerator(), progressions, keys, n_samples=500
        ... )
        >>> gen = NeuralMelodyGenerator.train_from_dataset(
        ...     dataset, "melody.pt", epochs=50, device="cpu"
        ... )
        >>> notes = gen.render(chords, key, 8.0)
        """
        from melodica.generators._neural_training import NeuralTrainer

        return NeuralTrainer.train_from_dataset(
            dataset,
            output_path,
            epochs=epochs,
            lr=lr,
            batch_size=batch_size,
            seq_len=seq_len,
            device=device,
            verbose=verbose,
        )

    @classmethod
    def train_from_notes(
        cls,
        notes: list[NoteInfo],
        output_path: str,
        *,
        chords: list[ChordLabel] | None = None,
        key: Scale | None = None,
        epochs: int = 20,
        lr: float = 3e-4,
        batch_size: int = 16,
        seq_len: int = 128,
        device: str = "cpu",
        verbose: bool = True,
    ) -> "NeuralMelodyGenerator":
        """
        Train the tiny transformer on a list of NoteInfo notes and save weights.

        Parameters
        ----------
        notes:     melody notes (sorted by start)
        output_path: where to save the .pt file
        chords:    optional chord context for conditioning
        key:       optional key for conditioning
        epochs:    training epochs
        lr:        learning rate
        device:    'cpu' or 'cuda'
        verbose:   print loss per epoch

        Returns a NeuralMelodyGenerator loaded with the new weights.
        """
        from melodica.generators._neural_training import NeuralTrainer

        return NeuralTrainer.train_from_notes(
            notes,
            output_path,
            chords=chords,
            key=key,
            epochs=epochs,
            lr=lr,
            batch_size=batch_size,
            seq_len=seq_len,
            device=device,
            verbose=verbose,
        )

    # ------------------------------------------------------------------
    # Neural render
    # ------------------------------------------------------------------

    def _neural_render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None,
        events: list[RhythmEvent],
    ) -> list[NoteInfo]:
        try:
            import torch
        except ImportError:
            return _fallback_render(
                chords,
                key,
                duration_beats,
                context,
                events,
                self.params,
                self.harmony_prob,
                self.direction_bias,
                self.note_range_low,
                self.note_range_high,
            )

        model = self._model
        model.eval()

        prefix = _encode_chords(chords, key)

        # Seed pitch from context
        low = self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        high = (
            self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        )
        seed_pitch = (
            context.prev_pitch
            if context and context.prev_pitch is not None
            else nearest_pitch(chords[0].root, (low + high) // 2)
        )
        prefix.append(_PITCH_BASE + max(0, min(127, seed_pitch)))

        device = self.device
        tokens = prefix[:]
        generated_pitches: list[int] = []

        with torch.no_grad():
            for _ in range(len(events)):
                x = torch.tensor([tokens[-512:]], dtype=torch.long, device=device)
                logits = model(x)[0, -1]  # (V,)

                # Mask non-pitch tokens during pitch selection
                mask = torch.full((VOCAB_SIZE,), float("-inf"), device=device)
                mask[_PITCH_BASE : _PITCH_BASE + 128] = logits[_PITCH_BASE : _PITCH_BASE + 128]

                # Encourage chord tones at strong beats
                beat_idx = len(generated_pitches)
                if beat_idx < len(events):
                    chord = chord_at(chords, events[beat_idx].onset)
                    is_strong = (events[beat_idx].onset % 2.0) < 0.1
                    if chord and is_strong:
                        pcs = chord.pitch_classes()
                        for pc in pcs:
                            for oct_ in range(low // 12, high // 12 + 2):
                                p = pc + oct_ * 12
                                if low <= p <= high:
                                    mask[_PITCH_BASE + p] += 2.0  # boost chord tones

                # Encourage in-range pitches
                for p in range(128):
                    if not (low <= p <= high):
                        mask[_PITCH_BASE + p] -= 5.0

                next_tok = _top_p_sample(mask, self.temperature, self.top_p, None)
                tokens.append(next_tok)

                if _PITCH_BASE <= next_tok < _PITCH_BASE + 128:
                    generated_pitches.append(next_tok - _PITCH_BASE)
                else:
                    # Model generated a non-pitch token — use nearest chord tone
                    chord = (
                        chord_at(chords, events[len(generated_pitches)].onset) if events else None
                    )
                    fallback_pitch = nearest_pitch(
                        chord.root if chord else chords[0].root, seed_pitch
                    )
                    generated_pitches.append(max(low, min(high, fallback_pitch)))

        # Build NoteInfo
        notes: list[NoteInfo] = []
        phrase_pos = context.phrase_position if context else 0.0
        base_vel = int(60 + self.params.density * 30)
        for i, (event, pitch) in enumerate(zip(events, generated_pitches)):
            progress = event.onset / max(duration_beats, 0.001)
            arch = 1.0 - 0.3 + 0.3 * math.sin(progress * math.pi * 0.7)
            intensity = 0.7 + 0.3 * phrase_pos
            vel = max(1, min(127, int(base_vel * arch * intensity * event.velocity_factor)))
            notes.append(
                NoteInfo(
                    pitch=max(0, min(127, pitch)),
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=vel,
                )
            )
        return notes

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _try_load_model(self) -> None:
        if not self.model_path or not os.path.isfile(self.model_path):
            return
        try:
            import torch

            model = _build_model()
            if model is None:
                return
            state = torch.load(self.model_path, map_location=self.device, weights_only=True)
            model.load_state_dict(state)
            model.eval()
            model.to(self.device)
            self._model = model
        except Exception as exc:
            import warnings

            warnings.warn(f"[NeuralMelody] could not load model: {exc}. Using fallback.")
            self._model = None

    # ------------------------------------------------------------------
    # Rhythm / events
    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Density-adaptive: low density → quarter notes, high → 8th notes
        step = 0.5 if self.params.density >= 0.4 else 1.0
        gate = step * 0.9
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=gate))
            t = round(t + step, 9)
        return events
