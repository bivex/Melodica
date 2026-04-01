"""conftest.py for mutmut — ensure local mutants/melodica is imported, not installed package."""

import sys
import os

# When running from mutants/ directory, ensure local melodica takes precedence
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)
