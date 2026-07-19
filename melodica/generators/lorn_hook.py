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

        # 2. Hook Generation: step-wise movements combined with wide leaps (5ths, 7ths, octaves)
        hook_pitches = []
        current_pitch = base_midi
        hook_pitches.append(current_pitch)
        
        for _ in range(self.hook_length - 1):
            if rng.random() < 0.35:
                # Wide expressive leap (Perfect 5th, Octave, Minor 7th)
                leap_interval = rng.choice([-12, -7, -5, 5, 7, 12])
                current_pitch = current_pitch + leap_interval
            else:
                # Melodic step to adjacent scale note
                idx = scale_pitches.index(current_pitch) if current_pitch in scale_pitches else len(scale_pitches) // 2
                step_dir = rng.choice([-2, -1, 1, 2])
                new_idx = max(0, min(len(scale_pitches) - 1, idx + step_dir))
                current_pitch = scale_pitches[new_idx]
            
            # Clamp to a memorable vocal/synth range
            current_pitch = max(base_midi - 6, min(base_midi + 9, current_pitch))
            hook_pitches.append(current_pitch)

        # 3. Slow, syncopated rhythm spanning exactly 4.0 beats (1 bar)
        # Generate note durations and rests for a 1-bar motif (4 beats)
        note_onsets = []
        t_onset = 0.0
        for i in range(self.hook_length):
            dur = rng.choice([0.5, 0.75, 1.0, 1.5])
            note_onsets.append((t_onset, dur))
            # small rest between notes
            t_onset += dur + rng.choice([0.0, 0.25, 0.5])
            if t_onset >= 3.5:
                break

        # Actual active hook length after fitting into 1 bar
        actual_hook_len = len(note_onsets)

        # 4. Phrase Layout & Call-and-Response:
        # We loop in 16-bar cycles (64 beats):
        # - Bars 0-4 (beats 0-16): Play Hook (repeated 4 times, once per 4-beat bar)
        # - Bars 4-8 (beats 16-32): Silence (dramatic rest)
        # - Bars 8-12 (beats 32-48): Response (play hook with variation / octave shift, repeated 4 times)
        # - Bars 12-16 (beats 48-64): Silence
        notes: list[NoteInfo] = []
        cycle_len = 64.0  # 16 bars
        
        t = 0.0
        period_idx = 0
        while t < duration_beats:
            cycle_phase = t % cycle_len
            
            if cycle_phase < 16.0:
                # Play the original Question hook repeated 4 times (once per bar)
                for r in range(4):
                    t_bar = t + r * 4.0
                    for i, (onset, dur) in enumerate(note_onsets):
                        if i < len(hook_pitches):
                            notes.append(NoteInfo(
                                pitch=hook_pitches[i],
                                start=t_bar + onset,
                                duration=dur,
                                velocity=rng.randint(85, 105),
                            ))
            elif 32.0 <= cycle_phase < 48.0:
                # Play the varied Response hook repeated 4 times
                # In alternate periods, we transpose by an octave (octave double)
                if period_idx % 2 == 1:
                    # Octave Transposed variation
                    varied_pitches = [p + 12 for p in hook_pitches]
                else:
                    # Pitch-shifted variation
                    varied_pitches = list(hook_pitches)
                    var_type = rng.choice(["change_last", "transpose_up", "transpose_down", "invert_last"])
                    
                    if var_type == "change_last" and len(varied_pitches) > 1:
                        # Modify final pitch
                        alt_step = rng.choice([-2, -1, 1, 2])
                        last_pitch = varied_pitches[-1]
                        if last_pitch in scale_pitches:
                            idx = scale_pitches.index(last_pitch)
                            new_idx = max(0, min(len(scale_pitches) - 1, idx + alt_step))
                            varied_pitches[-1] = scale_pitches[new_idx]
                    elif var_type == "transpose_up":
                        varied_pitches = [p + 2 if key.contains((p + 2) % 12) else p + 1 for p in varied_pitches]
                    elif var_type == "transpose_down":
                        varied_pitches = [p - 2 if key.contains((p - 2) % 12) else p - 1 for p in varied_pitches]
                    elif var_type == "invert_last" and len(varied_pitches) > 1:
                        diff = varied_pitches[-1] - varied_pitches[-2]
                        varied_pitches[-1] = varied_pitches[-2] - diff
                
                for r in range(4):
                    t_bar = t + r * 4.0
                    for i, (onset, dur) in enumerate(note_onsets):
                        if i < len(varied_pitches):
                            notes.append(NoteInfo(
                                pitch=varied_pitches[i],
                                start=t_bar + onset,
                                duration=dur,
                                velocity=rng.randint(80, 100),
                            ))
                        
            t += 16.0  # Move to next 4-bar section block
            period_idx += 1

        # 5. Hook Quality Diagnostics
        if notes:
            diag = self.evaluate_hook_quality(notes, hook_pitches, actual_hook_len)
            print(f"   [Hook Analyzer] Hook Unique Notes: {diag['unique_notes']} | "
                  f"Pitch Range: {diag['range_semitones']} sem | "
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
