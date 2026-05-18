# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-18 14:02
# Last Updated: 2026-05-18 14:02
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
demo_traced_album.py — Diagnostic runner to trace "City That Hears" Album production.
Tracks all three tracks (Isolation, Conflict, Acceptance) under EngineTracer.
"""

from melodica.tracer import EngineTracer
from scripts.album_city_that_hears import main as run_album

def main():
    print("==================================================================")
    print("   RUNNING FULL 'CITY THAT HEARS' ALBUM PRODUCTION CORE TRACE")
    print("==================================================================")
    
    with EngineTracer(show_private=False, show_duration=True, max_depth=5, use_colors=True):
        run_album()
        
    print("==================================================================")
    print("   ALBUM PRODUCTION CORE TRACE COMPLETE")
    print("==================================================================")

if __name__ == "__main__":
    main()
