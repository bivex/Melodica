"""
generators/_neural_training.py — Training logic for NeuralMelodyGenerator.

Layer: Application / Domain

Extracted from neural_melody.py so the generator stays focused on inference.
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from melodica.generators import PhraseGenerator

from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale

# ---------------------------------------------------------------------------
# Token constants (duplicated to avoid circular imports — kept in sync with
# neural_melody.py)
# ---------------------------------------------------------------------------

_PAD = 0
_BOS = 1
_EOS = 2
_BAR = 3
_POS_BASE = 4
_PITCH_BASE = 20
_DUR_BASE = 148
_CROOT_BASE = 164
_CQUAL_BASE = 176
_KROOT_BASE = 182
_KMODE_BASE = 194
VOCAB_SIZE = 201


# ---------------------------------------------------------------------------
# Encoding helpers (copied from neural_melody.py to keep this module self-
# contained for training)
# ---------------------------------------------------------------------------

from melodica.types import Mode, Quality

_QUAL_ORDER = [
    Quality.MAJOR,
    Quality.MINOR,
    Quality.DOMINANT7,
    Quality.MAJOR7,
    Quality.MINOR7,
    Quality.DIMINISHED,
]
_QUAL_TO_IDX: dict[Quality, int] = {q: i for i, q in enumerate(_QUAL_ORDER)}

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
    tokens.append(_KROOT_BASE + key.root)
    tokens.append(_KMODE_BASE + _MODE_TO_IDX.get(key.mode, 0))
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
    step = 0.25

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


# ---------------------------------------------------------------------------
# Model builder (copied from neural_melody.py)
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


# ---------------------------------------------------------------------------
# Training class
# ---------------------------------------------------------------------------


class NeuralTrainer:
    """Standalone training logic consumed by NeuralMelodyGenerator classmethods."""

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
        """
        if len(keys) == 1:
            pairs = [(chords, keys[0]) for chords in chord_sets]
        else:
            pairs = list(zip(chord_sets, keys))

        if n_samples is not None:
            reps = (n_samples + len(pairs) - 1) // len(pairs)
            pairs = (pairs * reps)[:n_samples]

        dataset: list[tuple[list[NoteInfo], list[ChordLabel], Scale]] = []
        for chords, key in pairs:
            ctx = RenderContext(phrase_position=random.random())
            notes = generator.render(chords, key, duration_beats, ctx)
            if notes:
                dataset.append((notes, chords, key))
        return dataset

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
    ) -> Any:
        """
        Train from a dataset of (notes, chords, key) tuples.

        Returns a NeuralMelodyGenerator loaded with the trained weights.
        The caller must pass the actual NeuralMelodyGenerator class as cls.
        """
        # Deferred import to avoid circular dependency
        from melodica.generators.neural_melody import NeuralMelodyGenerator

        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim
        except ImportError:
            raise ImportError("Training requires torch. pip install torch>=2.0")

        if not dataset:
            raise ValueError("Dataset is empty.")

        all_tokens: list[int] = []
        for notes, chords, key in dataset:
            if not notes:
                continue
            sorted_notes = sorted(notes, key=lambda n: n.start)
            duration = sorted_notes[-1].start + sorted_notes[-1].duration
            prefix = _encode_chords(chords, key)
            melody = _encode_notes(sorted_notes, duration)
            all_tokens.extend(prefix + melody)

        if len(all_tokens) < seq_len + 1:
            raise ValueError(
                f"Dataset too small: {len(all_tokens)} tokens, need >{seq_len}. "
                "Use more samples or shorter seq_len."
            )

        tok_tensor = torch.tensor(all_tokens, dtype=torch.long, device=device)

        xs, ys = [], []
        for start in range(0, len(tok_tensor) - seq_len):
            chunk = tok_tensor[start : start + seq_len + 1]
            xs.append(chunk[:-1])
            ys.append(chunk[1:])

        if verbose:
            print(
                f"[NeuralMelody] dataset: {len(dataset)} sequences, "
                f"{len(all_tokens)} tokens, {len(xs)} training windows"
            )

        model = _build_model()
        if model is None:
            raise RuntimeError("Could not build model.")
        model = model.to(device)
        model.train()

        optimizer = optim.AdamW(model.parameters(), lr=lr)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
        loss_fn = nn.CrossEntropyLoss(ignore_index=_PAD)

        for epoch in range(epochs):
            total_loss, n_batches = 0.0, 0
            perm = list(range(len(xs)))
            random.shuffle(perm)
            for i in range(0, len(perm), batch_size):
                batch_idx = perm[i : i + batch_size]
                x_batch = torch.stack([xs[j] for j in batch_idx])
                y_batch = torch.stack([ys[j] for j in batch_idx])
                logits = model(x_batch)
                B, T, V = logits.shape
                loss = loss_fn(logits.reshape(B * T, V), y_batch.reshape(B * T))
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                total_loss += loss.item()
                n_batches += 1
            scheduler.step()
            if verbose:
                print(
                    f"  epoch {epoch + 1:3d}/{epochs}  loss={total_loss / n_batches:.4f}  "
                    f"lr={scheduler.get_last_lr()[0]:.2e}"
                )

        torch.save(model.state_dict(), output_path)
        if verbose:
            print(f"[NeuralMelody] saved → {output_path}")

        return NeuralMelodyGenerator(model_path=output_path, device=device)

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
    ) -> Any:
        """
        Train the tiny transformer on a list of NoteInfo notes and save weights.

        Returns a NeuralMelodyGenerator loaded with the new weights.
        The caller must pass the actual NeuralMelodyGenerator class as cls.
        """
        from melodica.generators.neural_melody import NeuralMelodyGenerator

        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim
        except ImportError:
            raise ImportError("Training requires torch. pip install torch>=2.0")

        if key is None:
            from melodica.types import Scale, Mode

            key = Scale(root=0, mode=Mode.MAJOR)
        if chords is None:
            from melodica.types import ChordLabel, Quality

            chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]

        sorted_notes = sorted(notes, key=lambda n: n.start)
        duration = sorted_notes[-1].start + sorted_notes[-1].duration if sorted_notes else 4.0
        prefix = _encode_chords(chords, key)
        melody = _encode_notes(sorted_notes, duration)
        full_seq = prefix + melody

        if not sorted_notes:
            raise ValueError("Need at least a few notes to train.")
        if len(full_seq) < 4:
            raise ValueError("Need at least a few notes to train.")

        tok_tensor = torch.tensor(full_seq, dtype=torch.long, device=device)

        def _make_batches():
            windows_x, windows_y = [], []
            for start in range(0, max(1, len(tok_tensor) - seq_len)):
                chunk = tok_tensor[start : start + seq_len + 1]
                if len(chunk) < 2:
                    continue
                windows_x.append(chunk[:-1])
                windows_y.append(chunk[1:])
            if not windows_x:
                windows_x = [tok_tensor[:-1]]
                windows_y = [tok_tensor[1:]]
            return windows_x, windows_y

        xs, ys = _make_batches()

        model = _build_model()
        if model is None:
            raise RuntimeError("Could not build model (torch not available?)")
        model = model.to(device)
        model.train()

        optimizer = optim.AdamW(model.parameters(), lr=lr)
        loss_fn = nn.CrossEntropyLoss(ignore_index=_PAD)

        for epoch in range(epochs):
            total_loss = 0.0
            perm = list(range(len(xs)))
            random.shuffle(perm)
            for i in range(0, len(perm), batch_size):
                batch_idx = perm[i : i + batch_size]
                max_l = max(xs[j].size(0) for j in batch_idx)
                x_batch = torch.stack(
                    [
                        torch.nn.functional.pad(xs[j], (0, max_l - xs[j].size(0)), value=_PAD)
                        for j in batch_idx
                    ]
                )
                y_batch = torch.stack(
                    [
                        torch.nn.functional.pad(ys[j], (0, max_l - ys[j].size(0)), value=_PAD)
                        for j in batch_idx
                    ]
                )
                logits = model(x_batch)  # (B, T, V)
                B, T, V = logits.shape
                loss = loss_fn(logits.reshape(B * T, V), y_batch.reshape(B * T))
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                total_loss += loss.item()
            if verbose:
                avg = total_loss / max(1, math.ceil(len(perm) / batch_size))
                print(f"[NeuralMelody] epoch {epoch + 1}/{epochs}  loss={avg:.4f}")

        torch.save(model.state_dict(), output_path)
        if verbose:
            print(f"[NeuralMelody] saved → {output_path}")

        return NeuralMelodyGenerator(model_path=output_path, device=device)
