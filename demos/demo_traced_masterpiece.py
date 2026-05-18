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
demo_traced_masterpiece.py — Diagnostic runner to trace the full Orchestral Dark Fantasy Masterpiece.
Traces deeper into the Core Composer, MusicDirector, Orchestration, and Automation systems.
"""

from melodica.tracer import EngineTracer
from demos.demo_masterpiece_dark_fantasy import main as run_masterpiece

def main():
    print("==================================================================")
    print("   RUNNING FULL ORCHESTRAL DARK FANTASY MASTERPIECE CORE TRACE")
    print("==================================================================")
    
    # Trace with maximum depth 6, showing all function entries, durations and exits in the core
    with EngineTracer(show_private=False, show_duration=True, max_depth=6, use_colors=True):
        run_masterpiece()
        
    print("==================================================================")
    print("   CORE TRACE COMPLETE")
    print("==================================================================")

if __name__ == "__main__":
    main()
