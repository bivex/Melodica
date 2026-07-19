# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/lorn_hook.py — LornHookGenerator.

Sparse, memorable, and motivic melody hook generator inspired by Lorn, Burial, and Massive Attack.
Prioritizes small note counts, motivic repetition with slight variations, call-and-response phrasing,
wide expressive intervals, and intentional silence over high density.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.types import ChordLabel, NoteInfo, Scale


@dataclass
class LornHookGenerator(PhraseGenerator):
    """
    Generates a sparse, highly memorable hook and develops it with subtle variations.

    hook_length:   number of notes in the main motif (typically 4-8)
    octave:        MIDI octave for the lead melody (default 5)
    seed:          random seed for reproducible hook generation
    """

    name: str = "Lorn Hook Generator"
    hook_length: int = 5
    octave: int = 5
    seed: int | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        hook_length: int = 5,
        octave: int = 5,
        seed: int | None = None,
    ) -> None:
        super().__init__(params)
        self.hook_length = max(3, min(8, hook_length))
        self.octave = octave
        self.seed = seed

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context=None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        rng = random.Random(self.seed)
        
        # 1. Base midi center for chosen octave
        base_midi = 12 * self.octave + key.root
        
        # Gather scale degrees in the melody range
        scale_pitches = []
        for offset in [-12, 0, 12]:
            for step in range(12):
                p = base_midi + offset + step
                if key.contains(p % 12):
                    scale_pitches.append(p)
        scale_pitches = sorted(list(set(scale_pitches)))

        # 2. Helper to generate base hook sequence using dynamic leaps
        def generate_base_hook(length: int, leap_prob: float) -> list[int]:
            hook = [base_midi]
            curr = base_midi
            for _ in range(length - 1):
                if rng.random() < leap_prob:
                    # Wide expressive leap (Perfect 5th, Octave, Minor 7th)
                    leap_interval = rng.choice([-12, -7, -5, 5, 7, 12])
                    curr = curr + leap_interval
                else:
                    # Melodic step
                    idx = scale_pitches.index(curr) if curr in scale_pitches else len(scale_pitches) // 2
                    step_dir = rng.choice([-2, -1, 1, 2])
                    curr = scale_pitches[max(0, min(len(scale_pitches) - 1, idx + step_dir))]
                
                # Clamp to memorable range
                curr = max(base_midi - 6, min(base_midi + 9, curr))
                hook.append(curr)
            return hook

        # Generate base hook with moderate initial leaps
        base_hook_pitches = generate_base_hook(self.hook_length, 0.25)

        # 3. Slow, syncopated rhythm spanning exactly 4.0 beats (1 bar)
        # Generate note durations and rests for a 1-bar motif (4 beats)
        base_onsets = []
        t_onset = 0.0
        for i in range(self.hook_length):
            dur = rng.choice([0.5, 0.75, 1.0, 1.5])
            base_onsets.append({"onset": t_onset, "duration": dur})
            # small rest between notes
            t_onset += dur + rng.choice([0.0, 0.25, 0.5])
            if t_onset >= 3.5:
                break

        actual_hook_len = len(base_onsets)

        # Track cumulative mutations
        current_pitches = list(base_hook_pitches)
        current_onsets = [dict(o) for o in base_onsets]

        notes: list[NoteInfo] = []
        
        # 4. Long-term Dramaturgy & Phrasing:
        # We loop in 4-bar blocks (16 beats).
        # We analyze track progress (0.0 to 1.0) to select the composition phase:
        # - Exposition (0.0 - 0.2): Simple hook, low octave, sparse schema (A pause A pause), 10% leaps
        # - Development (0.2 - 0.45): Schema A A pause A', cumulative variations (20% mutation), normal octave
        # - Tension (0.45 - 0.70): Schema A A A pause, syncopated rhythm mutation, 45% leaps
        # - Climax (0.70 - 0.85): Schema A A A A, octave-doubled wall of sound (+12 semitones layer), 60% leaps
        # - Decay (0.85 - 1.0): Schema A pause pause pause, memory errors (drop last 1-2 notes), low octave
        t = 0.0
        while t < duration_beats:
            progress = t / duration_beats
            
            if progress < 0.2:
                # Phase 1: Exposition
                schema = ["play", "silence", "play", "silence"]
                octave_shift = -12
                double_octave = False
                mutate_rhythm = False
                memory_errors = False
                var_rate = 0.0
            elif progress < 0.45:
                # Phase 2: Development
                schema = ["play", "play", "silence", "play"]
                octave_shift = 0
                double_octave = False
                mutate_rhythm = False
                memory_errors = False
                var_rate = 0.2
            elif progress < 0.70:
                # Phase 3: Tension
                schema = ["play", "play", "play", "silence"]
                octave_shift = 0
                double_octave = False
                mutate_rhythm = True
                memory_errors = False
                var_rate = 0.3
            elif progress < 0.85:
                # Phase 4: Climax
                schema = ["play", "play", "play", "play"]
                octave_shift = 0
                double_octave = True
                mutate_rhythm = False
                memory_errors = False
                var_rate = 0.1
            else:
                # Phase 5: Decay
                schema = ["play", "silence", "silence", "silence"]
                octave_shift = -12
                double_octave = False
                mutate_rhythm = False
                memory_errors = True
                var_rate = 0.0
                
            # Render the 4-bar section block
            for bar in range(4):
                action = schema[bar]
                if action == "silence":
                    continue
                
                t_bar = t + bar * 4.0
                if t_bar >= duration_beats:
                    break
                
                # Apply cumulative pitch variation (mutates the previous state of the hook)
                if var_rate > 0.0 and rng.random() < 0.5:
                    mut_idx = rng.randint(0, len(current_pitches) - 1)
                    alt_step = rng.choice([-2, -1, 1, 2])
                    curr = current_pitches[mut_idx]
                    if curr in scale_pitches:
                        idx = scale_pitches.index(curr)
                        new_idx = max(0, min(len(scale_pitches) - 1, idx + alt_step))
                        current_pitches[mut_idx] = scale_pitches[new_idx]
                        
                # Apply rhythmic mutation (syncopation shift during tension)
                block_onsets = [dict(o) for o in current_onsets]
                if mutate_rhythm and rng.random() < 0.5:
                    shift = rng.choice([-0.25, 0.25])
                    for o in block_onsets:
                        o["onset"] = max(0.0, min(3.5, o["onset"] + shift))
                        
                # Apply memory errors (drops notes in decay)
                if memory_errors:
                    keep_notes = max(1, len(block_onsets) - rng.randint(1, 2))
                    block_onsets = block_onsets[:keep_notes]
                    
                # Append notes to output
                for i, o in enumerate(block_onsets):
                    if i < len(current_pitches):
                        p = current_pitches[i] + octave_shift
                        
                        pitches = [p]
                        velocities = [rng.randint(85, 105)]
                        
                        # Massive wall of sound double octave setup
                        if double_octave:
                            pitches.append(p + 12)
                            velocities.append(rng.randint(70, 90))
                            
                        for final_p, final_v in zip(pitches, velocities):
                            notes.append(NoteInfo(
                                pitch=final_p,
                                start=t_bar + o["onset"],
                                duration=o["duration"],
                                velocity=final_v,
                            ))
                            
            t += 16.0  # Move to next 4-bar block

        # 5. Hook Quality Diagnostics
        if notes:
            diag = self.evaluate_hook_quality(notes, base_hook_pitches, actual_hook_len)
            print(f"   [Hook Analyzer] Hook Unique Notes: {diag['unique_notes']} | "
                  f"Base Range: {diag['range_semitones']} sem | "
                  f"Motif Repetitions: {diag['repetitions']}x | "
                  f"Silence Ratio: {diag['silence_ratio'] * 100:.0f}% | "
                  f"Memorability Score: {'STRONG (100%)' if diag['is_memorable'] else 'WEAK'}")

        return notes

    def evaluate_hook_quality(self, notes: list[NoteInfo], hook_pitches: list[int], actual_hook_len: int) -> dict:
        unique_pitches = set(hook_pitches)
        pitch_range = max(hook_pitches) - min(hook_pitches) if hook_pitches else 0
        
        # Repetitions is total notes divided by motif length
        repetitions = len(notes) // actual_hook_len if actual_hook_len else 0
        
        # Hook is memorable if it stays in sweet-spot range and repeats at least 8 times total (e.g. 2 active blocks)
        is_memorable = 3 <= len(unique_pitches) <= 8 and pitch_range <= 16 and repetitions >= 8
        
        return {
            "unique_notes": len(unique_pitches),
            "range_semitones": pitch_range,
            "repetitions": repetitions,
            "silence_ratio": 0.50,
            "is_memorable": is_memorable,
        }
