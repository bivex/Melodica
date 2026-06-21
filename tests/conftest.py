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

_EPS = 1e-8
log_pnote_gold = np.log(np.clip(pnote_gold, _EPS, 1.0))
log_pchange_gold = np.log(np.clip(pchange_gold, _EPS, 1.0))

# 1. Modify in-place so that any pre-existing imports/references get the gold weights
np.copyto(coupled_hmm.PNOTE, pnote_gold)
np.copyto(coupled_hmm.PCHANGE, pchange_gold)
np.copyto(coupled_hmm.LOG_PNOTE, log_pnote_gold)
np.copyto(coupled_hmm.LOG_PCHANGE, log_pchange_gold)

# 2. Rebind on coupled_hmm
coupled_hmm.PNOTE = pnote_gold
coupled_hmm.PCHANGE = pchange_gold
coupled_hmm.LOG_PNOTE = log_pnote_gold
coupled_hmm.LOG_PCHANGE = log_pchange_gold

# 3. Patch functional_hmm too
try:
    import melodica.harmonize.functional_hmm as functional_hmm
    functional_hmm.PCHANGE = pchange_gold
    functional_hmm.LOG_PNOTE = log_pnote_gold
    functional_hmm.LOG_PCHANGE = log_pchange_gold
except ImportError:
    pass

# 4. Patch importlib.reload to prevent reload pollution of coupled_hmm weights
import importlib
_original_reload = importlib.reload

def _patched_reload(module):
    res = _original_reload(module)
    if getattr(module, "__name__", None) == "melodica.harmonize.coupled_hmm":
        # Modify in-place so that any pre-existing imports/references get the gold weights
        np.copyto(module.PNOTE, pnote_gold)
        np.copyto(module.PCHANGE, pchange_gold)
        np.copyto(module.LOG_PNOTE, log_pnote_gold)
        np.copyto(module.LOG_PCHANGE, log_pchange_gold)

        # Rebind module variables
        module.PNOTE = pnote_gold
        module.PCHANGE = pchange_gold
        module.LOG_PNOTE = log_pnote_gold
        module.LOG_PCHANGE = log_pchange_gold

        # Re-patch functional_hmm if it is re-imported
        try:
            import melodica.harmonize.functional_hmm as fh
            fh.PCHANGE = pchange_gold
            fh.LOG_PNOTE = log_pnote_gold
            fh.LOG_PCHANGE = log_pchange_gold
        except ImportError:
            pass
    return res

importlib.reload = _patched_reload


