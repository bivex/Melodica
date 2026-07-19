# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
hook_ml/generator_model.py — Advanced Apple MLX Generative Decoder.

Defines:
  - MelodyDecoder: MLP Decoder mapping z [batch, 32] to pitches, onsets, and durations.
  - LatentVariable: Native MLX container for trainable latent parameters.
  - batch_differentiable_loss: Fully continuous, batch-vectorized loss function
    using Gumbel-Softmax relaxation, soft ratios, and entropy regularization.
"""

import sys

try:
    import mlx.core as mx
    import mlx.nn as nn
except ImportError:
    print("\n[!] Error: Apple MLX is not installed.")
    sys.exit(1)


class MelodyDecoder(nn.Module):
    """
    Melody Decoder mapping a latent vector z [batch_size, 32]
    to notes sequences of shape [batch_size, num_notes, scale_size].
    """
    def __init__(self, num_notes: int = 5, scale_size: int = 7):
        super().__init__()
        # MLP Layers acting as a smooth Deep Melody Prior projector
        self.fc1 = nn.Linear(32, 64)
        self.fc2 = nn.Linear(64, 128)
        
        self.fc_pitches = nn.Linear(128, num_notes * scale_size)
        self.fc_gaps = nn.Linear(128, num_notes)
        self.fc_durations = nn.Linear(128, num_notes)
        
        self.num_notes = num_notes
        self.scale_size = scale_size

    def __call__(self, z: mx.array) -> tuple[mx.array, mx.array, mx.array]:
        # z shape: [batch_size, 32]
        h = mx.maximum(self.fc1(z), 0.0)
        h = mx.maximum(self.fc2(h), 0.0)
        
        batch_size = z.shape[0]
        
        pitches_logits = self.fc_pitches(h).reshape(batch_size, self.num_notes, self.scale_size)
        
        # Gaps between notes (between 0.5 and 1.25 beats)
        gaps = 0.5 + mx.sigmoid(self.fc_gaps(h)) * 0.75
        
        # Cumulative sum along the note dimension (axis=1) guarantees strictly increasing onsets
        onsets = mx.cumsum(gaps, axis=1) - gaps[:, :1]
        
        # Durations are generated independently (between 0.3 and 1.2 beats)
        durations = 0.3 + mx.sigmoid(self.fc_durations(h)) * 0.9
        
        return pitches_logits, onsets, durations


class LatentVariable(nn.Module):
    """Native MLX module wrapping the trainable latent parameters z."""
    def __init__(self, batch_size: int = 16, dim: int = 32):
        super().__init__()
        self.z = mx.random.normal((batch_size, dim))


def gumbel_softmax(logits: mx.array, temperature: float = 1.0) -> mx.array:
    """Computes differentiable categorical selection via Gumbel-Softmax relaxation."""
    u = mx.random.uniform(shape=logits.shape)
    gumbel = -mx.log(-mx.log(u + 1e-20) + 1e-20)
    return mx.softmax((logits + gumbel) / temperature, axis=-1)


def batch_differentiable_loss(
    model: MelodyDecoder,
    z: mx.array,
    scale_pitches: mx.array,
    target_resolution_midi: float,
    sync_target: float = 0.40,
    step_target: float = 0.70,
    leap_target: float = 0.30,
    temperature: float = 1.0
) -> mx.array:
    """
    Batch-vectorized fully continuous loss function.
    Rewards syncopations (targeted ratio), duration variance, step-leap balance (soft ratios),
    resolutions (aligned with key/genre), and entropy exploration.
    """
    logits, onsets, durations = model(z)
    
    # 1. Gumbel-Softmax relaxation for pitch classes
    probs = gumbel_softmax(logits, temperature)
    expected_pitches = probs @ scale_pitches
    
    # 2. Rhythm Loss
    # Soft syncopation ratio target: keep syncopated notes around target
    sync_soft = mx.sum(mx.sigmoid(20.0 * (mx.sin(mx.pi * onsets) ** 2 - 0.15)), axis=1)
    sync_ratio = sync_soft / 5.0
    syncopation_loss = mx.square(sync_ratio - sync_target)
    
    # Duration variety: reward standard deviation of durations
    duration_loss = -mx.std(durations, axis=1)
    
    # 3. Contour Loss (Step vs Leap balance)
    abs_diffs = mx.abs(expected_pitches[:, 1:] - expected_pitches[:, :-1])
    
    # Soft step count (intervals in [0.5, 2.5] semitones)
    steps_soft = mx.sum(mx.sigmoid(2.5 - abs_diffs) * mx.sigmoid(abs_diffs - 0.5), axis=1)
    # Soft leap count (intervals > 2.5 semitones)
    leaps_soft = mx.sum(mx.sigmoid(abs_diffs - 2.5), axis=1)
    
    # Ratios
    total_intervals = float(abs_diffs.shape[1])
    step_ratio = steps_soft / total_intervals
    leap_ratio = leaps_soft / total_intervals
    
    # Quadratic targets
    contour_loss = mx.square(step_ratio - step_target) + mx.square(leap_ratio - leap_target)
    
    # 4. Resolution Loss (last note resolves to target resolution midi)
    last_pitch = expected_pitches[:, -1]
    resolution_loss = mx.square(last_pitch - target_resolution_midi)
    
    # 5. Entropy Regularization
    p = mx.softmax(logits, axis=-1)
    entropy = -mx.mean(mx.sum(p * mx.log(p + 1e-9), axis=-1), axis=1)
    entropy_loss = -0.15 * entropy
    
    # Combine losses per candidate
    total_loss = (
        12.0 * syncopation_loss +
        3.0 * duration_loss +
        15.0 * contour_loss +
        8.0 * resolution_loss +  # Pulled to the target resolution midi
        1.0 * entropy_loss
    )
    
    # Sum across batch dimension for autograd
    return mx.sum(total_loss)
