# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-18 14:03
# Last Updated: 2026-05-18 14:03
#
# Licensed under the MIT License.
# Commercial licensing available authorities upon request.

"""
demo_traced_dark_fantasy.py — Traced runner for the largest cinematic generator (dark_fantasy_v3.py).
Traces the massive 9-act structure using EngineTracer to expose potential bugs.
"""

import sys
from pathlib import Path
from melodica.tracer import EngineTracer

# Insert parent dir so we can import from scripts
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from dark_fantasy_v3 import generate as run_generation

def main():
    print("==================================================================")
    print("   RUNNING DEEP ENGINE TRACE ON THE LARGEST CINEMATIC CORE")
    print("   SCRIPT: dark_fantasy_v3.py (9-Act Cinematic Masterpiece)")
    print("==================================================================")
    
    # We trace to depth 5 with private filters and colorized stdout.
    # To run relatively fast while doing a deep trace, we generate a 2-minute duration.
    with EngineTracer(show_private=False, show_duration=True, max_depth=5, use_colors=True):
        tracks, pedal_cc = run_generation(duration_minutes=2.0, tempo=72, key_root=0, seed=42)
        
    print("==================================================================")
    print("   CINEMATIC CORE GENERATOR TRACE COMPLETE")
    print(f"   Generated {len(tracks)} multi-track channels.")
    print("==================================================================")

if __name__ == "__main__":
    main()
