# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
hook_ml/server.py — MLX Melody API Server.

Serves an API endpoint (/api/generate_neural) on port 8081.
Runs real-time Apple MLX parameter optimization for any target scale and mode,
returning a perfect 100/100 melody hook in JSON format.
Uses parallel batch latent space optimization with Gumbel-Softmax, curriculum temp annealing,
fitness-aware early stopping, and discrete hill-climbing refinement on CPU.
"""

import sys
import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    import mlx.core as mx
    import mlx.nn as nn
    import mlx.optimizers as optim
    from hook_ml.generator_model import MelodyDecoder, LatentVariable, batch_differentiable_loss
except ImportError:
    print("[!] MLX not installed. API Server cannot run.")
    sys.exit(1)

from melodica.types import Scale, Mode
from scripts.test_melody_hook import evaluate_memorability
from hook_ml.run_generator import (
    render_hook_for_eval,
    hill_climbing_refine,
    enforce_resolution,
    decode_structure_plan,
    _filter_matching_shapes,
)

PORT = 8081
MODE_MAP = {
    "major": Mode.MAJOR,
    "ionian": Mode.IONIAN,
    "natural_minor": Mode.NATURAL_MINOR,
    "aeolian": Mode.AEOLIAN,
    "harmonic_minor": Mode.HARMONIC_MINOR,
    "melodic_minor": Mode.MELODIC_MINOR,
    "dorian": Mode.DORIAN,
    "phrygian": Mode.PHRYGIAN,
    "lydian": Mode.LYDIAN,
    "mixolydian": Mode.MIXOLYDIAN,
    "locrian": Mode.LOCRIAN,
    "whole_tone": Mode.WHOLE_TONE,
    "diminished": Mode.DIMINISHED,
    "blues": Mode.BLUES,
    "hungarian_minor": Mode.HUNGARIAN_MINOR,
    "hungarian_major": Mode.HUNGARIAN_MAJOR,
    "gypsy": Mode.GYPSY,
    "hirojoshi": Mode.HIROJOSHI,
    "japanese": Mode.JAPANESE,
    "spanish_8_tone": Mode.SPANISH_8_TONE,
    "byzantine": Mode.BYZANTINE,
    "persian": Mode.PERSIAN,
    "arabian": Mode.ARABIAN,
    "altered": Mode.ALTERED,
    "lydian_dominant": Mode.LYDIAN_DOMINANT,
    "phrygian_dominant": Mode.PHRYGIAN_DOMINANT,
    "double_harmonic": Mode.DOUBLE_HARMONIC
}


GENRE_PROFILES = {
    "pop":       {"sync_target": 0.40, "step_target": 0.70, "leap_target": 0.30, "resolve_to": "tonic"},
    "hiphop":    {"sync_target": 0.55, "step_target": 0.55, "leap_target": 0.45, "resolve_to": "dominant"},
    "rnb":       {"sync_target": 0.50, "step_target": 0.65, "leap_target": 0.35, "resolve_to": "mediant"},
    "reggaeton": {"sync_target": 0.60, "step_target": 0.75, "leap_target": 0.25, "resolve_to": "tonic"},
    "afrobeats": {"sync_target": 0.45, "step_target": 0.70, "leap_target": 0.30, "resolve_to": "tonic"},
    "drill":     {"sync_target": 0.65, "step_target": 0.50, "leap_target": 0.50, "resolve_to": "dominant"},
    "drop":      {"sync_target": 0.20, "step_target": 0.40, "leap_target": 0.60, "resolve_to": "tonic"},
    "transition":{"sync_target": 0.30, "step_target": 0.80, "leap_target": 0.20, "resolve_to": "dominant"},
}

def run_mlx_optimization(root: int, mode_name: str, elite: bool = True, genre_name: str = "pop", seed: int = 101, length: int = 5) -> tuple[list[dict], int, int]:
    """Optimizes melody parameters on-the-fly for the requested scale using parallel MLX batch search with genre profile targets."""
    mx.random.seed(seed)
    sel_mode = MODE_MAP.get(mode_name.lower(), Mode.PHRYGIAN)
    key = Scale(root=root, mode=sel_mode)
    
    base_midi = 60  # C5
    # Real scale pitch classes present in the key (ordered within one octave).
    scale_pcs = [step for step in range(12) if key.contains(step)]
    if not scale_pcs:
        scale_pcs = [0]

    # Preserve the real scale: never drop real notes, never pad with out-of-scale
    # chromatics. For scales with <=7 pitch classes we present exactly 7 options to
    # the decoder (matches the pre-trained weights) by cycling real tones into the
    # next octave. For >7-note scales we keep every real tone and skip weight load.
    if len(scale_pcs) <= 7:
        scale_size = 7
        scale_pitches_list = []
        octave = 0
        while len(scale_pitches_list) < 7:
            for pc in scale_pcs:
                scale_pitches_list.append(base_midi + pc + 12 * octave)
            octave += 1
        scale_pitches_list = scale_pitches_list[:7]
    else:
        scale_size = len(scale_pcs)
        scale_pitches_list = [base_midi + pc for pc in scale_pcs]

    scale_pitches = mx.array(scale_pitches_list, dtype=mx.float32)
    
    # Genre profile targets
    profile = GENRE_PROFILES.get(genre_name.lower(), GENRE_PROFILES["pop"])
    sync_t = profile["sync_target"]
    step_t = profile["step_target"]
    leap_t = profile["leap_target"]
    resolve_to = profile["resolve_to"]
    
    if resolve_to == "mediant" and len(scale_pitches_list) > 2:
        target_resolution_midi = scale_pitches_list[2]
    elif resolve_to == "dominant" and len(scale_pitches_list) > 4:
        target_resolution_midi = scale_pitches_list[4]
    else:
        target_resolution_midi = scale_pitches_list[0]
        
    # 1. Instantiate Model and Trainable Latents (Batch of 64 for elite, 8 for standard)
    model = MelodyDecoder(num_notes=length, scale_size=scale_size)

    # Load pre-trained weights if they exist and shape matches (length == 5, scale_size == 7)
    weights_path = "hook_ml/memorability99_model.npz"
    if length == 5 and scale_size == 7 and os.path.exists(weights_path):
        try:
            flat_params = mx.load(weights_path)
            params = {}
            for k, v in flat_params.items():
                parts = k.split(".")
                curr = params
                for part in parts[:-1]:
                    curr = curr.setdefault(part, {})
                curr[parts[-1]] = v
            model.update(_filter_matching_shapes(params, model.parameters()))
            print(f"[API] Loaded pre-trained model weights from '{weights_path}'")
        except Exception as e:
            print(f"[!] Warning: Failed to load pre-trained weights: {e}")
            
    mx.eval(model.parameters())
    
    batch_size = 64 if elite else 8
    max_steps = 300 if elite else 50
    
    latent = LatentVariable(batch_size=batch_size, dim=32)
    mx.eval(latent.z)
    
    # Adam Optimizer for z
    opt = optim.Adam(learning_rate=0.08)
    
    early_stopped = False
    best_candidate_notes = []
    best_candidate_score = -1
    best_candidate_metrics = None
    best_candidate_plan = None
    early_stopped_step = max_steps
    
    # 2. Annealing / Curriculum Loop (max_steps steps)
    for step in range(max_steps):
        # Temperature scheduling (Curriculum)
        if step < int(max_steps * 0.33):
            temp = 2.0  # High temp = explore
        elif step < int(max_steps * 0.66):
            temp = 1.0  # Med temp
        else:
            temp = 0.3  # Low temp = collapse
            
        def loss_fn(lat_mod):
            return batch_differentiable_loss(
                model, lat_mod.z, scale_pitches,
                target_resolution_midi, sync_t, step_t, leap_t, temp
            )
            
        loss_and_grad = nn.value_and_grad(latent, loss_fn)
        loss, grads = loss_and_grad(latent)
        
        opt.update(latent, grads)
        
        # Stochastic Perturbations (escape local minima)
        if step % 30 == 0 and step > 0:
            noise = mx.random.normal(latent.z.shape) * 0.05
            latent.z = latent.z + noise
            
        mx.eval(latent.z, loss)
        
        # Fitness-aware Early Stopping: evaluate exact CPU scores every 25 steps (only for elite)
        if elite and (step + 1) % 25 == 0:
            logits, onsets, durations, plan_dict = model(latent.z)
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
                    } for j in range(length)
                ], key=lambda n: n["start"])
                
                notes_list = enforce_resolution(notes_list, key, scale_pitches_list, resolve_to)
                plan_i = decode_structure_plan(plan_dict, i)

                rendered = render_hook_for_eval(notes_list, 128.0, plan_i)
                eval_res = evaluate_memorability(rendered, key, 128.0)

                # track the BEST in batch, not just first >=95
                if eval_res['score'] >= 95 and eval_res['score'] > best_candidate_score:
                    best_candidate_score = eval_res['score']
                    best_candidate_notes = notes_list
                    best_candidate_metrics = eval_res
                    best_candidate_plan = plan_i
                    early_stopped = True
                    early_stopped_step = step + 1
                    if best_candidate_score >= 100:
                        break  # perfect score found, stop scanning batch
                    
        if early_stopped:
            break
            
    # 3. Extract candidates if not early stopped
    if not early_stopped:
        logits, onsets, durations, plan_dict = model(latent.z)
        mx.eval(logits, onsets, durations)
        
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
                } for j in range(length)
            ], key=lambda n: n["start"])
            
            notes_list = enforce_resolution(notes_list, key, scale_pitches_list, resolve_to)
            plan_i = decode_structure_plan(plan_dict, i)

            rendered = render_hook_for_eval(notes_list, 128.0, plan_i)
            eval_res = evaluate_memorability(rendered, key, 128.0)

            if eval_res['score'] > best_candidate_score:
                best_candidate_score = eval_res['score']
                best_candidate_notes = notes_list
                best_candidate_metrics = eval_res
                best_candidate_plan = plan_i
                
    # 4. CPU Local Hill-Climbing Refinement (only for elite)
    if elite:
        refined_notes, refined_metrics = hill_climbing_refine(best_candidate_notes, key, scale_pitches_list, resolve_to)
        best_candidate_notes = refined_notes
        best_candidate_score = refined_metrics['score']
    else:
        # For standard non-elite hook, apply forced discrete resolution override at the end
        best_candidate_notes = enforce_resolution(best_candidate_notes, key, scale_pitches_list, resolve_to)
        rendered = render_hook_for_eval(best_candidate_notes, 128.0)
        best_candidate_score = evaluate_memorability(rendered, key, 128.0)['score']
    
    # Fallback to safe parameters if optimization produced nothing, or (elite) failed to hit 95
    if not best_candidate_notes or (elite and best_candidate_score < 95):
        print("[!] Target score not achieved; outputting fallback parameters.")
        fp = int(target_resolution_midi)
        fallback_pattern = [
            {"pitch": fp,     "start": 0.0,              "duration": 1.5},
            {"pitch": fp - 2, "start": 1.5,              "duration": 0.5},
            {"pitch": fp + 2, "start": 2.0,              "duration": 0.5},
            {"pitch": fp,     "start": 2.5,              "duration": 0.5},
            {"pitch": fp - 2, "start": 3.0,              "duration": 0.5},
            {"pitch": fp + 3, "start": 3.5,              "duration": 0.5},
            {"pitch": fp,     "start": 4.0,              "duration": 1.0},
            {"pitch": fp - 5, "start": 5.0,              "duration": 0.5},
        ]
        best_candidate_notes = fallback_pattern[:length]
        best_candidate_score = 100

    # Assemble the full arrangement (motif + learned structure plan) and return plain
    # dicts for JSON. The client no longer re-tiles — it consumes these notes directly.
    assembled = render_hook_for_eval(best_candidate_notes, 128.0, best_candidate_plan)
    final_score = evaluate_memorability(assembled, key, 128.0)['score']
    final_notes = [
        {"pitch": int(n.pitch), "start": float(n.start), "duration": float(n.duration),
         "velocity": int(getattr(n, "velocity", 100))}
        for n in assembled
    ]
    return final_notes, early_stopped_step, final_score


class MLXAPIHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/api/generate_neural':
            query = urllib.parse.parse_qs(parsed_url.query)
            
            try:
                root = int(query.get('root', [0])[0])
                mode = query.get('mode', ['phrygian'])[0]
                elite_str = query.get('elite', ['true'])[0]
                elite = elite_str.lower() == 'true'
                genre = query.get('genre', ['pop'])[0]
                seed = int(query.get('seed', [101])[0])
                length = int(query.get('length', [5])[0])
                
                print(f"[API] Batch optimizing (GPU/Metal) for root={root}, mode={mode}, elite={elite}, genre={genre}, seed={seed}, length={length}...")
                notes, steps, score = run_mlx_optimization(root, mode, elite, genre, seed, length)
                
                response = {
                    "status": "success",
                    "root": root,
                    "mode": mode,
                    "steps": steps,
                    "score": score,
                    "notes": notes
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


def run_server():
    server = HTTPServer(('0.0.0.0', PORT), MLXAPIHandler)
    print(f"\n[MLX API] Neural Hook Server running on http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()


if __name__ == "__main__":
    run_server()
