# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-18 13:59
# Last Updated: 2026-05-18 13:59
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
demo_traced_symphony.py — Diagnostic runner to trace the Virtuoso Symphony orchestral generator.
Uses the unified EngineTracer to check time signatures, spectral reports, and balancer filters.
"""

from melodica.tracer import EngineTracer
from demos.demo_virtuoso_symphony import main as run_symphony

def main():
    print("==================================================================")
    print("   RUNNING FULL VIRTUOSO ORCHESTRAL SYMPHONY ENGINE TRACE")
    print("==================================================================")
    
    # We trace up to depth 5 with duration profiling and colorized terminal logs.
    with EngineTracer(show_private=False, show_duration=True, max_depth=5, use_colors=True):
        run_symphony()
        
    print("==================================================================")
    print("   VIRTUOSO SYMPHONY ENGINE TRACE COMPLETE")
    print("==================================================================")

if __name__ == "__main__":
    main()
