# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
hook_ml/generator_model.py — Apple MLX Neural Network Model.

Defines a HookGeneratorMLX neural network using Apple's MLX framework.
Includes a Straight-Through Estimator (STE) in the loss function to optimize discrete notes directly.
Step and leap losses are highly weighted to force balanced melody contours.
"""

import sys

try:
    import mlx.core as mx
    import mlx.nn as nn
except ImportError:
    print("\n[!] Error: Apple MLX is not installed. To run this neural network on Apple Silicon, run:")
    print("    pip install mlx")
    sys.exit(1)


class HookGeneratorMLX(nn.Module):
    """
    Generative neural network in MLX.
    Outputs pitch class probabilities, note onsets (via cumulative gaps), and durations.
    """
    def __init__(self, num_notes: int = 5, scale_size: int = 7):
        super().__init__()
        # Input layer (latent space vector of size 16)
        self.fc1 = nn.Linear(16, 32)
        self.fc2 = nn.Linear(32, 64)
        
        # Outputs:
        # Pitches logits: [num_notes, scale_size]
        self.fc_pitches = nn.Linear(64, num_notes * scale_size)
        # Gaps between notes: [num_notes]
        self.fc_gaps = nn.Linear(64, num_notes)
        # Durations: [num_notes]
        self.fc_durations = nn.Linear(64, num_notes)
        
        self.num_notes = num_notes
        self.scale_size = scale_size

    def __call__(self, x: mx.array) -> tuple[mx.array, mx.array, mx.array]:
        h = mx.maximum(self.fc1(x), 0.0)
        h = mx.maximum(self.fc2(h), 0.0)
        
        pitches_logits = self.fc_pitches(h).reshape(self.num_notes, self.scale_size)
        
        # Gaps between notes (between 0.5 and 1.25 beats)
        gaps = 0.5 + mx.sigmoid(self.fc_gaps(h)) * 0.75
        
        # Cumulative sum ensures strictly increasing onsets starting at 0.0
        onsets = mx.cumsum(gaps) - gaps[0]
        
        # Durations are generated independently (between 0.3 and 1.2 beats) to ensure duration variety
        durations = 0.3 + mx.sigmoid(self.fc_durations(h)) * 0.9
        
        return pitches_logits, onsets, durations


def differentiable_loss(
    model: HookGeneratorMLX,
    x: mx.array,
    scale_pitches: mx.array
) -> mx.array:
    """
    Differentiable loss function in MLX using Straight-Through Estimators (STE).
    Directly aligns continuous gradients with discrete argmax outputs.
    """
    logits, onsets, durations = model(x)
    
    # 1. Straight-Through Estimator for discrete pitch selection
    probs = mx.softmax(logits, axis=-1)
    hard_idx = mx.argmax(logits, axis=-1)
    one_hot = mx.eye(logits.shape[-1])[hard_idx]
    
    # Forward pass uses discrete one_hot, backward pass uses continuous probs
    probs_ste = one_hot + probs - mx.stop_gradient(probs)
    expected_pitches = probs_ste @ scale_pitches
    
    # 2. Rhythm Loss
    # Syncopation: reward starts that land on fractional beats (onsets % 1.0 != 0.0)
    syncopation_loss = -mx.mean(mx.sin(mx.pi * onsets) ** 2)
    # Duration variety: penalize uniform durations (reward standard deviation)
    duration_loss = -mx.std(durations)
    
    # 3. Contour Loss (Step vs Leap balance)
    abs_diffs = mx.abs(expected_pitches[1:] - expected_pitches[:-1])
    
    # Force at least one leap >= 3 semitones (heavily penalized if missing)
    leap_loss = mx.maximum(0.0, 3.0 - mx.max(abs_diffs))
    # Force at least one step <= 2 semitones (excluding unisons, heavily penalized if missing)
    nonzero_diffs = mx.where(abs_diffs > 0.1, abs_diffs, 99.0)
    step_loss = mx.maximum(0.0, mx.min(nonzero_diffs) - 2.0)
    
    # Standard deviation of intervals in sweet-spot
    contour_std_loss = mx.square(mx.std(abs_diffs) - 3.5)
    
    # 4. Resolution Loss
    # Last pitch should resolve to stable tonic/dominant (C5=60, G5=67, E5=64)
    last_pitch = expected_pitches[-1]
    resolution_loss = mx.min(mx.square(last_pitch - mx.array([60.0, 67.0, 64.0])))
    
    total_loss = (
        1.5 * syncopation_loss +
        1.0 * duration_loss +
        10.0 * leap_loss +  # Heavily weighted to guarantee steps/leaps constraint
        10.0 * step_loss +  # Heavily weighted to guarantee steps/leaps constraint
        1.5 * contour_std_loss +
        1.0 * resolution_loss
    )
    
    return total_loss
