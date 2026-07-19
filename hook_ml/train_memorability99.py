# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
hook_ml/train_memorability99.py — Supervised policy training script for MelodyDecoder.
Trains the decoder parameters so that drawing random latent vectors z ~ N(0, I)
naturally generates elite melodic hooks with Memorability Score >= 99.
"""

import os
import sys

# Add project root to path
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    import mlx.core as mx
    import mlx.nn as nn
    import mlx.optimizers as optim
except ImportError:
    print("\n[!] Error: Apple MLX is not installed.")
    sys.exit(1)

from hook_ml.generator_model import MelodyDecoder, batch_differentiable_loss
from hook_ml.server import MODE_MAP, GENRE_PROFILES
from melodica.types import Scale, Mode

def flatten_params(d, prefix=""):
    flat = {}
    for k, v in d.items():
        name = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            flat.update(flatten_params(v, name))
        else:
            flat[name] = v
    return flat

def train_model(epochs=600, batch_size=128):
    print("==============================================================")
    print("🚀  T R A I N I N G   M E M O R A B I L I T Y 9 9   M O D E L")
    print("==============================================================")
    print("Initializing MelodyDecoder model for continuous policy gradient training...")
    
    model = MelodyDecoder(num_notes=5, scale_size=7)
    mx.eval(model.parameters())
    
    opt = optim.Adam(learning_rate=0.005)
    
    # Precompute scale intervals
    mode_intervals_map = {}
    for name, mode_enum in MODE_MAP.items():
        key_dummy = Scale(root=0, mode=mode_enum)
        intervals = [step for step in range(12) if key_dummy.contains(step)]
        if len(intervals) > 7:
            intervals = intervals[:7]
        elif len(intervals) < 7:
            while len(intervals) < 7:
                intervals.append(intervals[-1] + 1)
        mode_intervals_map[name] = intervals

    genre_names = list(GENRE_PROFILES.keys())
    mode_names = list(MODE_MAP.keys())
    
    print(f"Training parameters: epochs={epochs}, batch_size={batch_size}")
    print("Running training iterations across all 25 scale modes and 6 genres...")
    
    for epoch in range(epochs):
        # 1. Randomly sample key, mode, and genre parameters for this step
        root = mx.random.randint(0, 12).item()
        # BUG FIX: mx.random.randint upper bound is exclusive but .item() can
        # theoretically hit len() on boundary — use modulo for safety
        mode_name  = mode_names[mx.random.randint(0, 10000).item() % len(mode_names)]
        genre_name = genre_names[mx.random.randint(0, 10000).item() % len(genre_names)]
        
        # 2. Get scale pitches list
        intervals = mode_intervals_map[mode_name]
        scale_pitches_list = [60 + root + step for step in intervals]
        scale_pitches = mx.array(scale_pitches_list, dtype=mx.float32)
        
        # 3. Load genre profile targets
        profile = GENRE_PROFILES[genre_name]
        sync_t = profile["sync_target"]
        step_t = profile["step_target"]
        leap_t = profile["leap_target"]
        resolve_to = profile["resolve_to"]
        
        if resolve_to == "mediant":
            target_res = scale_pitches_list[2]
        elif resolve_to == "dominant":
            target_res = scale_pitches_list[4]
        else:
            target_res = scale_pitches_list[0]
            
        # 4. Generate random latents
        z = mx.random.normal(shape=(batch_size, 32))
        
        # 5. Anneal Gumbel-Softmax temperature
        temp = max(0.4, 2.0 - (epoch / epochs) * 1.6)
        
        # 6. Optimization step
        def loss_fn(model_instance):
            return batch_differentiable_loss(
                model_instance, z, scale_pitches,
                target_res, sync_t, step_t, leap_t, temp
            )
            
        loss_and_grad = nn.value_and_grad(model, loss_fn)
        loss, grads = loss_and_grad(model)
        opt.update(model, grads)
        
        mx.eval(model.parameters(), loss)
        
        if (epoch + 1) % 50 == 0:
            avg_loss = loss.item() / batch_size
            print(f"  Step {epoch+1:>3} / {epochs} | Loss per sample: {avg_loss:.4f} (Temp: {temp:.2f})")
            
    # Save the trained model weights
    save_path = "hook_ml/memorability99_model.npz"
    flat_params = flatten_params(model.parameters())
    mx.savez(save_path, **flat_params)
    
    print("==============================================================")
    print(f"🎉 Training complete! Model saved successfully to '{save_path}'!")
    print("==============================================================")

if __name__ == "__main__":
    train_model()
