# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-18 13:58
# Last Updated: 2026-05-18 13:58
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
demo_traced_song.py — Diagnostic runner to trace the full Multi-Track Demo Song generator.
Uses the unified EngineTracer to profile and visualize the complete pipeline.
"""

from melodica.tracer import EngineTracer
from demos.demo_song_generator import create_demo_song

def main():
    print("==================================================================")
    print("   RUNNING FULL MULTI-TRACK SONG GENERATION UNDER DETAILED TRACE")
    print("==================================================================")
    
    # We turn on the EngineTracer with colors and duration profiling.
    # We trace up to depth 5 to keep the log clean and high-level.
    with EngineTracer(show_private=False, show_duration=True, max_depth=5, use_colors=True):
        create_demo_song()
        
    print("==================================================================")
    print("   TRACED SONG GENERATION COMPLETE")
    print("==================================================================")

if __name__ == "__main__":
    main()
