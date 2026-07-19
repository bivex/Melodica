# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
hook_ml/generator_model.py — Advanced Apple MLX Generative Decoder.

Defines:
  - MelodyDecoder: MLP Decoder mapping z [batch, 32] to a 1-bar motif
    (pitches, onsets, durations) AND a learned structure plan over `num_plan_bars`
    bars (per-bar play/rest gate, motif-variant id, octave-shift). The renderer
    tiles the plan to cover the full arrangement so the model can optimize
    silence ratio and motivic repetition — points the motif alone cannot reach.
  - LatentVariable: Native MLX container for trainable latent parameters.
  - batch_differentiable_loss: Fully continuous, batch-vectorized loss function
    using Gumbel-Softmax relaxation, soft ratios, entropy regularization, and
    structure-plan terms (silence + repetition).
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
    Melody Decoder mapping a latent vector z [batch_size, 32] to a motif
    ([batch, num_notes, scale_size] pitches + onsets + durations) and a
    structure plan over `num_plan_bars` bars that the renderer tiles to 32 bars.
    """
    def __init__(self, num_notes: int = 5, scale_size: int = 7,
                 num_plan_bars: int = 8, num_variants: int = 3):
        super().__init__()
        # Shared MLP trunk
        self.fc1 = nn.Linear(32, 64)
        self.fc2 = nn.Linear(64, 128)

        # ---- Motif heads (per note) ----
        self.fc_pitches = nn.Linear(128, num_notes * scale_size)
        self.fc_gaps = nn.Linear(128, num_notes)
        self.fc_durations = nn.Linear(128, num_notes)

        # ---- Structure-plan heads (per bar) ----
        self.fc_play_gate = nn.Linear(128, num_plan_bars)                       # play/rest per bar
        self.fc_variant = nn.Linear(128, num_plan_bars * num_variants)          # motif variant per bar
        self.fc_octshift = nn.Linear(128, num_plan_bars * 3)                    # octave shift per bar

        self.num_notes = num_notes
        self.scale_size = scale_size
        self.num_plan_bars = num_plan_bars
        self.num_variants = num_variants
        # Categorical values for the octave-shift head (argmax indexes these)
        self.octshift_values = (-12, 0, 12)

    def __call__(self, z: mx.array):
        # z shape: [batch_size, 32]
        h = mx.maximum(self.fc1(z), 0.0)
        h = mx.maximum(self.fc2(h), 0.0)

        batch_size = z.shape[0]

        # --- Motif ---
        pitches_logits = self.fc_pitches(h).reshape(batch_size, self.num_notes, self.scale_size)
        # Gaps between notes (between 0.5 and 1.25 beats)
        gaps = 0.5 + mx.sigmoid(self.fc_gaps(h)) * 0.75
        # Cumulative sum along the note dimension (axis=1) guarantees strictly increasing onsets
        onsets = mx.cumsum(gaps, axis=1) - gaps[:, :1]
        # Durations are generated independently (between 0.3 and 1.2 beats)
        durations = 0.3 + mx.sigmoid(self.fc_durations(h)) * 0.9

        # --- Structure plan (per bar) ---
        plan = {
            "play_gate": self.fc_play_gate(h),                                                   # [B, P]
            "variant_logits": self.fc_variant(h).reshape(batch_size, self.num_plan_bars, self.num_variants),   # [B, P, V]
            "octshift_logits": self.fc_octshift(h).reshape(batch_size, self.num_plan_bars, 3),                 # [B, P, 3]
        }

        return pitches_logits, onsets, durations, plan


class LatentVariable(nn.Module):
    """Native MLX module wrapping the trainable latent parameters z."""
    def __init__(self, batch_size: int = 16, dim: int = 32):
        super().__init__()
        self.z = mx.random.normal((batch_size, dim))


def gumbel_softmax(logits: mx.array, temperature: float = 1.0) -> mx.array:
    """Computes differentiable categorical selection via Gumbel-Softmax relaxation."""
    u = mx.random.uniform(shape=logits.shape)
    # stop_gradient: Gumbel noise is a constant perturbation, not a learned param
    gumbel = mx.stop_gradient(-mx.log(-mx.log(u + 1e-20) + 1e-20))
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
    resolutions (aligned with key/genre), entropy exploration, AND a structure plan that
    lands silence ratio and motivic repetition in the scorer's sweet spots.
    """
    logits, onsets, durations, plan = model(z)

    # 1. Gumbel-Softmax relaxation for pitch classes
    probs = gumbel_softmax(logits, temperature)
    expected_pitches = probs @ scale_pitches

    # 2. Rhythm Loss
    sync_soft = mx.sum(mx.sigmoid(20.0 * (mx.sin(mx.pi * onsets) ** 2 - 0.15)), axis=1)
    num_notes = float(onsets.shape[1])
    sync_ratio = sync_soft / num_notes
    syncopation_loss = mx.square(sync_ratio - sync_target)

    duration_loss = -mx.std(durations, axis=1)

    # 3. Contour Loss (Step vs Leap balance)
    abs_diffs = mx.abs(expected_pitches[:, 1:] - expected_pitches[:, :-1])
    steps_soft = mx.sum(mx.sigmoid(2.5 - abs_diffs) * mx.sigmoid(abs_diffs - 0.5), axis=1)
    leaps_soft = mx.sum(mx.sigmoid(abs_diffs - 2.5), axis=1)
    total_intervals = float(abs_diffs.shape[1])
    step_ratio = steps_soft / total_intervals
    leap_ratio = leaps_soft / total_intervals
    contour_loss = mx.square(step_ratio - step_target) + mx.square(leap_ratio - leap_target)

    # 4. Resolution Loss (last note resolves to target resolution midi)
    last_pitch = expected_pitches[:, -1]
    resolution_loss = mx.square((last_pitch - target_resolution_midi) / 12.0)

    # 5. Entropy Regularization
    p = mx.softmax(logits, axis=-1)
    entropy = -mx.mean(mx.sum(p * mx.log(p + 1e-9), axis=-1), axis=1)
    entropy_loss = -0.15 * entropy

    # 6. Structure-plan losses — silence ratio + motivic repetition.
    # These target score buckets the motif alone cannot reach: silence_ratio (Rhythm)
    # and bar-profile repetition. The scorer rewards silence in [0.30, 0.65] and
    # repetition when active bars >= 4 with <= 4 distinct bar profiles.
    play = mx.sigmoid(plan["play_gate"])                              # [B, P]
    vp = mx.softmax(plan["variant_logits"], axis=-1)                 # [B, P, V]
    op = mx.softmax(plan["octshift_logits"], axis=-1)                # [B, P, 3]

    active_ratio = mx.mean(play, axis=1)                             # [B]
    silence_ratio = 1.0 - active_ratio
    # Center silence at 0.45 (inside the scorer's 0.30–0.65 band; ~4.4 active of 8 bars).
    silence_loss = mx.square(silence_ratio - 0.45)

    # Soft pairwise profile-match across bars: probability two active bars share both
    # variant and octave-shift. High agreement => few distinct profiles => the scorer's
    # "1..4 unique profiles" condition is satisfied (active>=4 comes from the silence term).
    var_agree = mx.matmul(vp, mx.swapaxes(vp, -1, -2))               # [B, P, P]
    oct_agree = mx.matmul(op, mx.swapaxes(op, -1, -2))              # [B, P, P]
    match = var_agree * oct_agree
    pair_w = play[:, :, None] * play[:, None, :]                     # both bars active
    num_plan_bars = plan["play_gate"].shape[1]
    off_diag = 1.0 - mx.eye(num_plan_bars)
    denom = mx.sum(pair_w * off_diag, axis=[1, 2])
    mean_match = mx.sum(match * pair_w * off_diag, axis=[1, 2]) / (denom + 1e-9)
    rep_loss = -mean_match                                           # maximize agreement (minimize loss)

    # Combine losses per candidate
    total_loss = (
        12.0 * syncopation_loss +
        3.0 * duration_loss +
        15.0 * contour_loss +
        8.0 * resolution_loss +
        1.0 * entropy_loss +
        8.0 * silence_loss +
        2.0 * rep_loss
    )

    # Sum across batch dimension for autograd
    return mx.sum(total_loss)
