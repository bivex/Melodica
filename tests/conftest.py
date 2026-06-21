# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""conftest.py for mutmut — ensure local mutants/melodica is imported, not installed package."""

import sys
import os

# When running from mutants/ directory, ensure local melodica takes precedence
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

# Force tests to use immutable gold synthetic weights instead of active training weights
import numpy as np
from pathlib import Path

_weights_dir = Path(_here).parent / "melodica" / "harmonize" / "weights"

import melodica.harmonize.coupled_hmm as coupled_hmm

pnote_gold = np.loadtxt(_weights_dir / "pnote_synth_gold.txt")
pchange_gold = np.load(_weights_dir / "pchange_synth_gold.npy")

coupled_hmm.PNOTE = pnote_gold
coupled_hmm.PCHANGE = pchange_gold

_EPS = 1e-8
coupled_hmm.LOG_PNOTE = np.log(np.clip(pnote_gold, _EPS, 1.0))
coupled_hmm.LOG_PCHANGE = np.log(np.clip(pchange_gold, _EPS, 1.0))
