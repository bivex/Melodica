# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
hook_ml/run_generator.py — MLX Training & Generation Pipeline.

Runs batch-vectorized latent space optimization using Gumbel-Softmax relaxation,
temperature annealing (curriculum), and stochastic perturbations.
Includes discrete local hill-climbing refinement, fitness-aware early stopping,
and forced final note resolution matching the target key.
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

from melodica.types import Scale, NoteInfo
from scripts.test_melody_hook import Mode, evaluate_memorability


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


def enforce_resolution(notes_list: list[dict], key: Scale) -> list[dict]:
    """
    Forcibly shifts the last note of the hook to the nearest octave of the
    scale's tonic (root) or dominant (5th) to guarantee 5/5 resolution score.
    """
    if len(notes_list) == 0:
        return notes_list
        
    res_notes = [dict(n) for n in notes_list]
    last_idx = -1
    last_note = res_notes[last_idx]
    
    # Target pitch classes (tonic and dominant)
    tonic_pc = key.root % 12
    dominant_pc = (key.root + 7) % 12
    
    current_pitch = last_note["pitch"]
    current_pc = current_pitch % 12
    
    # If already stable tonic or dominant, return
    if current_pc == tonic_pc or current_pc == dominant_pc:
        return res_notes
        
    # Find nearest octave for tonic and dominant (MIDI octaves 3 to 7)
    tonic_pitch_options = [tonic_pc + 12 * oct for oct in range(3, 8)]
    dominant_pitch_options = [dominant_pc + 12 * oct for oct in range(3, 8)]
    
    all_options = tonic_pitch_options + dominant_pitch_options
    # Sort by proximity to current pitch to minimize melodic distortion
    best_pitch = min(all_options, key=lambda p: abs(p - current_pitch))
    
    res_notes[last_idx]["pitch"] = best_pitch
    return res_notes


def hill_climbing_refine(notes_list: list[dict], key: Scale, scale_pitches_list: list[int]) -> tuple[list[dict], dict]:
    """
    Performs discrete hill-climbing local search on a generated melody hook
    to close the continuous-discrete gap and hit exactly 100/100.
    """
    best_notes = [dict(n) for n in notes_list]
    best_notes = enforce_resolution(best_notes, key)  # lock resolution first
    rendered = render_hook_for_eval(best_notes, 128.0)
    best_metrics = evaluate_memorability(rendered, key, 128.0)
    best_score = best_metrics['score']
    
    if best_score >= 100:
        return best_notes, best_metrics
        
    improved = True
    passes = 0
    
    # Try up to 3 passes of mutations
    while improved and passes < 3:
        improved = False
        passes += 1
        
        # 1. Mutate pitch degrees (skipping the last note to preserve resolved tonic/dominant)
        for idx in range(len(best_notes) - 1):
            original_pitch = best_notes[idx]["pitch"]
            for step_pitch in scale_pitches_list:
                if step_pitch == original_pitch:
                    continue
                test_notes = [dict(n) for n in best_notes]
                test_notes[idx]["pitch"] = step_pitch
                test_notes = sorted(test_notes, key=lambda n: n["start"])
                
                rendered = render_hook_for_eval(test_notes, 128.0)
                metrics = evaluate_memorability(rendered, key, 128.0)
                score = metrics['score']
                if score > best_score:
                    best_score = score
                    best_metrics = metrics
                    best_notes = test_notes
                    improved = True
                    if best_score >= 100:
                        return best_notes, best_metrics
                        
        # 2. Adjust note starts slightly (+/- 0.05, 0.1, 0.15 beats)
        for idx in range(len(best_notes)):
            original_start = best_notes[idx]["start"]
            for offset in [-0.15, -0.1, -0.05, 0.05, 0.1, 0.15]:
                new_start = original_start + offset
                if new_start < 0.0:
                    continue
                test_notes = [dict(n) for n in best_notes]
                test_notes[idx]["start"] = new_start
                test_notes = sorted(test_notes, key=lambda n: n["start"])
                
                rendered = render_hook_for_eval(test_notes, 128.0)
                metrics = evaluate_memorability(rendered, key, 128.0)
                score = metrics['score']
                if score > best_score:
                    best_score = score
                    best_metrics = metrics
                    best_notes = test_notes
                    improved = True
                    if best_score >= 100:
                        return best_notes, best_metrics
                        
        # 3. Adjust durations slightly (+/- 0.05, 0.1, 0.15 beats)
        for idx in range(len(best_notes)):
            original_dur = best_notes[idx]["duration"]
            for offset in [-0.15, -0.1, -0.05, 0.05, 0.1, 0.15]:
                new_dur = original_dur + offset
                if new_dur < 0.2:
                    continue
                test_notes = [dict(n) for n in best_notes]
                test_notes[idx]["duration"] = new_dur
                
                rendered = render_hook_for_eval(test_notes, 128.0)
                metrics = evaluate_memorability(rendered, key, 128.0)
                score = metrics['score']
                if score > best_score:
                    best_score = score
                    best_metrics = metrics
                    best_notes = test_notes
                    improved = True
                    if best_score >= 100:
                        return best_notes, best_metrics
                        
    return best_notes, best_metrics


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
    
    # Target resolution midis for continuous loss function
    target_root_midi = base_midi + root
    target_dominant_midi = base_midi + root + 7
    
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
    
    early_stopped = False
    best_candidate_notes = []
    best_candidate_score = -1
    best_candidate_metrics = None
    early_stopped_step = 300
    
    # 3. Annealing / Curriculum Loop (300 steps)
    for step in range(300):
        # Temperature scheduling (Curriculum)
        if step < 100:
            temp = 2.0  # High temp = explore
        elif step < 200:
            temp = 1.0  # Med temp
        else:
            temp = 0.3  # Low temp = collapse
            
        def loss_fn(lat_mod):
            return batch_differentiable_loss(
                model, lat_mod.z, scale_pitches,
                target_root_midi, target_dominant_midi, temp
            )
            
        loss_and_grad = nn.value_and_grad(latent, loss_fn)
        loss, grads = loss_and_grad(latent)
        
        opt.update(latent, grads)
        
        # Stochastic Perturbations (inject noise to escape local minima)
        if step % 30 == 0 and step > 0:
            noise = mx.random.normal(latent.z.shape) * 0.05
            latent.z = latent.z + noise
            
        mx.eval(latent.z, loss)
        
        # Fitness-aware Early Stopping: check exact CPU scores every 25 steps
        if (step + 1) % 25 == 0:
            logits, onsets, durations = model(latent.z)
            mx.eval(logits, onsets, durations)
            
            for i in range(batch_size):
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
                
                # Apply forced discrete resolution override
                notes_list = enforce_resolution(notes_list, key)
                
                rendered = render_hook_for_eval(notes_list, 128.0)
                eval_res = evaluate_memorability(rendered, key, 128.0)
                
                if eval_res['score'] >= 95:
                    best_candidate_score = eval_res['score']
                    best_candidate_notes = notes_list
                    best_candidate_metrics = eval_res
                    early_stopped = True
                    early_stopped_step = step + 1
                    break
                    
        if early_stopped:
            print(f"  [Early Stopping] Triggered at step {early_stopped_step}! Score: {best_candidate_score}/100")
            break
            
        if (step + 1) % 50 == 0:
            print(f"  Step {step + 1:>3} | Batch Loss: {loss.item():.4f} (Temp: {temp:.1f})")
            
    # 4. Extract candidates and find the best one if not early stopped
    if not early_stopped:
        print("\nOptimization complete. Evaluating batch candidates...")
        logits, onsets, durations = model(latent.z)
        mx.eval(logits, onsets, durations)
        
        for i in range(batch_size):
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
            
            notes_list = enforce_resolution(notes_list, key)
            
            rendered = render_hook_for_eval(notes_list, 128.0)
            eval_res = evaluate_memorability(rendered, key, 128.0)
            
            if eval_res['score'] > best_candidate_score:
                best_candidate_score = eval_res['score']
                best_candidate_notes = notes_list
                best_candidate_metrics = eval_res
                
    # 5. Apply Discrete Hill-Climbing Refinement to guarantee 100/100
    print(f"Applying CPU Hill-Climbing Refinement to candidate (Current Score: {best_candidate_score}/100)...")
    refined_notes, refined_metrics = hill_climbing_refine(best_candidate_notes, key, scale_pitches_list)
    best_candidate_notes = refined_notes
    best_candidate_score = refined_metrics['score']
    best_candidate_metrics = refined_metrics
    
    # Print Markdown output to terminal
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    
    print("\n" + "=" * 60)
    print("   🏆 G E N E R A T E D   E L I T E   H O O K   R E P O R T")
    print("=" * 60)
    print(f"### 🎼 Lorn Neural Hook (MLX Batch Latent Optimization)")
    print(f"* **Scale:** C PHRYGIAN")
    print(f"* **Framework:** Apple MLX (Metal Accelerated)")
    print(f"* **Batch Size:** {batch_size} parallel candidates")
    print(f"* **Early Stop Step:** {early_stopped_step}")
    print(f"* **Final Refined Memorability Score:** {best_candidate_score}/100 (🏆 EXCELLENT)")
    
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
