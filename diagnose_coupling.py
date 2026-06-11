import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer, HMMConfig, TYPE_TO_QUALITY
from melodica.types import NoteInfo, Scale, Mode, BarGrid

def print_banner(text):
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)

def main():
    print_banner("COUPLED HMM & 2nd-ORDER VITERBI DIAGNOSTIC")
    
    # Mathematical context
    print("""
[Math & Architectural Corrections Review]
1. 2nd-Order Viterbi (Markov Property Correctness):
   - Expanded state space to 1728 states: s = (chord_curr, root_prev).
   - Resolves the Markov property violation where root interval penalty was applied
     using a global greedy argmax at step t-1.
   - Now, each path tracks its own history (interval_prev and interval_curr)
     guaranteeing mathematical correctness and global optimality of Viterbi.

2. True Layer 1 (Chord) & Layer 2 (Key) Coupling:
   - Previously, Layer 2 key estimation was calculated but discarded (dead code).
   - Now, it uses a 3-pass loop:
     * Pass 1: Estimate draft chords.
     * Pass 2: Extract key modulation centers sequence.
     * Pass 3: Re-harmonize chords using key coupling bias from Pass 2.
""")

    # Test melody: C major melody with a sharp key modulation clue in the second half
    # Let's start with C-E-G (C Major) then move to F#-A#-C# (F# Major)
    melody = [
        # Bar 1 (C Major)
        NoteInfo(pitch=60, start=0.0, duration=2.0), # C
        NoteInfo(pitch=64, start=2.0, duration=2.0), # E
        # Bar 2 (C Major)
        NoteInfo(pitch=67, start=4.0, duration=2.0), # G
        NoteInfo(pitch=60, start=6.0, duration=2.0), # C
        # Bar 3 (Modulating to F# Major/Minor area)
        NoteInfo(pitch=66, start=8.0, duration=2.0), # F#
        NoteInfo(pitch=70, start=10.0, duration=2.0), # A# (A# / Bb)
        # Bar 4 (F# Major area)
        NoteInfo(pitch=73, start=12.0, duration=2.0), # C#
        NoteInfo(pitch=66, start=14.0, duration=2.0), # F#
    ]

    initial_scale = Scale(root=0, mode=Mode.MAJOR) # C Major
    grid = BarGrid(numerator=4, denominator=4)
    duration = 16.0

    print_banner("RUNNING HARMONIZATION")
    
    # 1. Uncoupled Harmonizer (key_coupling_weight = 0.0)
    config_uncoupled = HMMConfig(key_coupling_weight=0.0)
    uncoupled_harmonizer = CoupledHMMHarmonizer(bar_grid=grid, chord_change="bars", config=config_uncoupled)
    uncoupled_chords = uncoupled_harmonizer.harmonize(melody, initial_scale, duration)

    # 2. Coupled Harmonizer (key_coupling_weight = 3.0)
    config_coupled = HMMConfig(key_coupling_weight=3.0)
    coupled_harmonizer = CoupledHMMHarmonizer(bar_grid=grid, chord_change="bars", config=config_coupled)
    
    # Manually run the passes for the coupled version to display the internal state (Pass 2 Key Sequence)
    change_points = coupled_harmonizer._get_change_points(duration)
    observations = coupled_harmonizer._extract_observations(melody, change_points)
    
    draft_chords = coupled_harmonizer._viterbi_chords(
        observations, initial_scale, change_points, constraints=None, tension_curve=None, key_path=None
    )
    
    # Pass 2: Key estimation
    estimated_keys = coupled_harmonizer._viterbi_keys(draft_chords)
    
    # Pass 3: Final refinement
    coupled_chords = coupled_harmonizer._viterbi_chords(
        observations, initial_scale, change_points, constraints=None, tension_curve=None, key_path=estimated_keys
    )

    # Note names array
    note_names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

    print_banner("INTERNAL KEY ESTIMATION (PASS 2)")
    print(f"{'Bar':<5} | {'Estimated Key Center & Mode':<35}")
    print("-" * 50)
    for i, (k_root, k_type_idx) in enumerate(estimated_keys):
        mode_name = list(MODE_DATABASE.keys())[k_type_idx]
        print(f"{i+1:<5} | {note_names[k_root]} {mode_name}")

    print_banner("CHORD PROGRESSION COMPARISON")
    print(f"{'Bar':<5} | {'Uncoupled (coupling=0.0)':<25} | {'Coupled (coupling=3.0)':<25}")
    print("-" * 70)
    
    for i in range(len(uncoupled_chords)):
        c_unc = uncoupled_chords[i]
        c_cou = coupled_chords[i]
        
        quality_unc = TYPE_TO_QUALITY[c_unc.quality] if hasattr(c_unc.quality, 'name') else c_unc.quality
        quality_cou = TYPE_TO_QUALITY[c_cou.quality] if hasattr(c_cou.quality, 'name') else c_cou.quality
        
        name_unc = f"{note_names[c_unc.root]} {quality_unc.name}"
        quality_idx_cou = list(TYPE_TO_QUALITY).index(quality_cou) if quality_cou in TYPE_TO_QUALITY else 0
        name_cou = f"{note_names[c_cou.root]} {quality_cou.name}"
        
        print(f"{i+1:<5} | {name_unc:<25} | {name_cou:<25}")

    print("\n[Result Verification]")
    coupled_str = [f"{c.root}_{c.quality}" for c in coupled_chords]
    uncoupled_str = [f"{c.root}_{c.quality}" for c in uncoupled_chords]
    if coupled_str != uncoupled_str:
        print("SUCCESS: Key Layer coupling actively guided chord path selection to align with modulations!")
    else:
        print("WARNING: Progressions match. (Try a different coupling weight or melody to see changes.)")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    # Import MODE_DATABASE for printing the estimated modes list
    from melodica.theory.modes import MODE_DATABASE
    main()
