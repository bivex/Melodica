import sys
import os
import numpy as np

# Ensure root of project is in sys.path
sys.path.insert(0, "/Volumes/External/Code/Melodica")

# Load conftest
import tests.conftest

import melodica.harmonize.coupled_hmm as coupled_hmm
from tests.test_coupled_hmm import _prog, C_MAJOR

print("coupled_hmm.PNOTE[0,0] =", coupled_hmm.PNOTE[0,0])

# Generate progress
chords = _prog(C_MAJOR, bars=16, seed=1)
for i, c in enumerate(chords):
    print(f"Chord {i}: root={c.root}, quality={c.quality.name}, start={c.start}, duration={c.duration}")
