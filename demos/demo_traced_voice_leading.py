# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-18 14:01
# Last Updated: 2026-05-18 14:01
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
demo_traced_voice_leading.py — Diagnostic runner to trace Voice Leading smoothing modifier.
Checks semitone distance minimization algorithms under the EngineTracer.
"""

from melodica.tracer import EngineTracer
from demos.demo_voice_leading import run_demo

def main():
    print("==================================================================")
    print("   RUNNING FULL VOICE LEADING ENGINE TRACE")
    print("==================================================================")
    
    with EngineTracer(show_private=False, show_duration=True, max_depth=5, use_colors=True):
        run_demo()
        
    print("==================================================================")
    print("   VOICE LEADING ENGINE TRACE COMPLETE")
    print("==================================================================")

if __name__ == "__main__":
    main()
