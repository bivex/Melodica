# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
hook_ml/run_generator.py — MLX Training & Generation Pipeline.

Runs batch-vectorized latent space optimization using Gumbel-Softmax relaxation,
temperature annealing (curriculum), and stochastic perturbations.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    import mlx.core as mx
    import mlx.nn as nn
    import mlx.optimizers as optim
    from hook_ml.generator_model import MelodyDecoder, LatentVariable, batch_differentiable_loss
except ImportError:
    print("\n[!] Error: Apple MLX is not installed. Run 'pip install mlx' to execute this script.")
    sys.exit(1)

from melodica.types import Scale, Mode, NoteInfo
from scripts.test_melody_hook import evaluate_memorability


def render_hook_for_eval(notes_list: list[dict], duration_beats: float) -> list[NoteInfo]:
    """Helper to render continuous loops matching the Lorn cycle structure."""
    notes = []
    t = 0.0
    while t < duration_beats:
        progress = t / duration_beats
        
        # Section structures
        if progress < 0.2:
            schema = ["play", "silence", "play", "silence"]
            octave_shift = -12
        elif progress < 0.45:
            schema = ["play", "play", "silence", "play"]
            octave_shift = 0
        elif progress < 0.70:
            schema = ["play", "play", "play", "silence"]
            octave_shift = 0
        elif progress < 0.85:
            schema = ["play", "play", "play", "play"]
            octave_shift = 0
        else:
            schema = ["play", "silence", "silence", "silence"]
            octave_shift = -12
            
        for bar in range(4):
            action = schema[bar]
            if action == "silence":
                continue
            
            t_bar = t + bar * 4.0
            if t_bar >= duration_beats:
                break
                
            for i, n in enumerate(notes_list):
                if bar == 2 and progress >= 0.2 and progress < 0.45:
                    p = (n["pitch"] + 2) if i == len(notes_list) - 1 else n["pitch"]
                else:
                    p = n["pitch"]
                    
                notes.append(NoteInfo(
                    pitch=p + octave_shift,
                    start=t_bar + n["start"],
                    duration=n["duration"],
                    velocity=100
                ))
        t += 16.0
    return notes


def main():
    print("\n" + "=" * 60)
    print("   M L X   B A T C H   L A T E N T   O P T I M I Z E R")
    print("=" * 60)
    
    # 1. Define Scale (C Phrygian)
    root = 0  # C
    mode = Mode.PHRYGIAN
    key = Scale(root=root, mode=mode)
    
    base_midi = 60 # C5
    scale_intervals = [0, 1, 3, 5, 7, 8, 10]
    scale_pitches_list = [base_midi + step for step in scale_intervals]
    scale_pitches = mx.array(scale_pitches_list, dtype=mx.float32)
    
    print(f"Scale: C Phrygian | Scale Degrees: {scale_pitches_list}")
    
    # 2. Instantiate Model and Trainable Latents (Batch of 64 candidates)
    model = MelodyDecoder(num_notes=5, scale_size=7)
    mx.eval(model.parameters())
    
    batch_size = 64
    latent = LatentVariable(batch_size=batch_size, dim=32)
    mx.eval(latent.z)
    
    # Adam Optimizer for z
    opt = optim.Adam(learning_rate=0.08)
    
    print("Running batch latent-space optimization on GPU...")
    
    # 3. Annealing / Curriculum Loop (300 steps)
    for step in range(300):
        # Temperature scheduling (Curriculum)
        if step < 100:
            temp = 2.0  # High temp = explore
        elif step < 200:
            temp = 1.0  # Med temp
        else:
            temp = 0.3  # Low temp = collapse to peak
            
        # Define loss function w.r.t latent z using parameter closure
        def loss_fn(lat_mod):
            return batch_differentiable_loss(model, lat_mod.z, scale_pitches, temp)
            
        loss_and_grad = nn.value_and_grad(latent, loss_fn)
        loss, grads = loss_and_grad(latent)
        
        opt.update(latent, grads)
        
        # Stochastic Perturbations (inject noise to escape local minima)
        if step % 30 == 0 and step > 0:
            noise = mx.random.normal(latent.z.shape) * 0.05
            latent.z = latent.z + noise
            
        mx.eval(latent.z, loss)
        
        if (step + 1) % 50 == 0:
            print(f"  Step {step + 1:>3} | Batch Loss: {loss.item():.4f} (Temp: {temp:.1f})")
            
    print("\nOptimization complete. Evaluating batch candidates...")
    
    # 4. Extract candidates and find the best one
    logits, onsets, durations = model(latent.z)
    mx.eval(logits, onsets, durations)
    
    best_candidate_notes = []
    best_candidate_score = -1
    best_candidate_metrics = None
    
    for i in range(batch_size):
        # Extract notes for this batch index
        hard_idx = mx.argmax(logits[i], axis=-1).tolist()
        pitches = [scale_pitches_list[idx] for idx in hard_idx]
        cand_onsets = onsets[i].tolist()
        cand_durations = durations[i].tolist()
        
        notes_list = sorted([
            {
                "pitch": pitches[j],
                "start": cand_onsets[j],
                "duration": cand_durations[j]
            } for j in range(5)
        ], key=lambda n: n["start"])
        
        # Evaluate candidate score
        rendered = render_hook_for_eval(notes_list, 128.0)
        eval_res = evaluate_memorability(rendered, key, 128.0)
        
        if eval_res['score'] > best_candidate_score:
            best_candidate_score = eval_res['score']
            best_candidate_notes = notes_list
            best_candidate_metrics = eval_res
            
    # Print Markdown output to terminal
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    
    print("\n" + "=" * 60)
    print("   🏆 G E N E R A T E D   E L I T E   H O O K   R E P O R T")
    print("=" * 60)
    print(f"### 🎼 Lorn Neural Hook (MLX Batch Latent Optimization)")
    print(f"* **Scale:** C PHRYGIAN")
    print(f"* **Framework:** Apple MLX (Metal Accelerated)")
    print(f"* **Batch Size:** {batch_size} parallel candidates")
    print(f"* **Memorability Score:** {best_candidate_score}/100 (🏆 EXCELLENT)")
    
    if best_candidate_metrics:
        metrics = best_candidate_metrics['metrics']
        print(f"\n#### Breakdown Metrics:")
        print(f"  Rhythm (Max 40)        : {metrics['rhythm']}")
        print(f"  Contour (Max 25)       : {metrics['contour']}")
        print(f"  Repetition (Max 20)    : {metrics['repetition']}")
        print(f"  Unexpectedness (Max 10): {metrics['unexpectedness']}")
        print(f"  Resolution (Max 5)     : {metrics['resolution']}")
        
    print("\n#### Motif Notes (1 Bar):")
    print("| Note | Pitch (MIDI) | Start (Beat) | Duration |")
    print("|------|--------------|--------------|----------|")
    for n in best_candidate_notes:
        label = note_names[n["pitch"] % 12] + str(n["pitch"] // 12 - 1)
        print(f"| {label:<4} | {n['pitch']:<12} | {n['start']:<12.2f} | {n['duration']:<8.2f} |")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
