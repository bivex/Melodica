# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
theory/functional_plus.py — Advanced Functional Harmony & Counterpoint.

Extends the basic Theory Engine with:
- Secondary Dominants (V/x, vii°/x)
- Modal Mixture (Borrowed chords from parallel minor/major)
- Advanced Cadences (Deceptive, Plagal, Picardy)
- Counterpoint Scoring Heuristics
"""

from __future__ import annotations
from enum import Enum
from melodica.types import ChordLabel, Quality, Scale, HarmonicFunction, Mode
from melodica.theory.chord_registry import CHORD_TEMPLATES

class CadenceType(Enum):
    AUTHENTIC = "authentic"     # V -> I
    PLAGAL = "plagal"           # IV -> I
    DECEPTIVE = "deceptive"     # V -> vi
    HALF = "half"               # x -> V
    PICARDY = "picardy"         # v -> I (Major)

def get_secondary_dominant(target_degree: int, key: Scale) -> ChordLabel:
    """
    Returns the dominant chord (V or V7) for a given scale degree.
    Example: In C Major, target_degree=5 (G) returns D7 (V/V).
    """
    # 1. Find the root of the target chord
    target_chord = key.diatonic_chord(target_degree)
    target_root = target_chord.root
    
    # 2. The dominant is 7 semitones (perfect fifth) above the target root
    dom_root = (target_root + 7) % 12
    
    # 3. Secondary dominants are always Major or Dominant7
    return ChordLabel(
        root=dom_root,
        quality=Quality.DOMINANT7,
        degree=target_degree, # Store as V/target
        function=HarmonicFunction.DOMINANT
    )

def get_borrowed_chord(degree: int, key: Scale) -> ChordLabel | None:
    """
    Returns a chord borrowed from the parallel mode.
    Example: In C Major, degree=6 returns Ab Major (bVI).
    """
    parallel_mode = Mode.NATURAL_MINOR if key.mode == Mode.MAJOR else Mode.MAJOR
    parallel_key = Scale(root=key.root, mode=parallel_mode)
    
    # Borrowed chords often involve flat degrees (bIII, bVI, bVII in Major)
    # or major degrees (IV, V in Minor)
    return parallel_key.diatonic_chord(degree)

def score_counterpoint(melody_note: int, bass_note: int, prev_melody: int, prev_bass: int) -> float:
    """
    Evaluate a melodic move against a bass line using counterpoint rules.
    Returns a score multiplier (0.0 to 2.0).
    """
    score = 1.0
    
    curr_interval = abs(melody_note - bass_note) % 12
    prev_interval = abs(prev_melody - prev_bass) % 12
    
    # 1. Avoid Parallel Fifths/Octaves
    if prev_interval in (0, 7) and curr_interval == prev_interval:
        # Check if they move in the same direction
        mel_dir = melody_note - prev_melody
        bass_dir = bass_note - prev_bass
        if (mel_dir > 0 and bass_dir > 0) or (mel_dir < 0 and bass_dir < 0):
            return 0.1 # Severe penalty
            
    # 2. Prefer Contrary Motion
    mel_dir = melody_note - prev_melody
    bass_dir = bass_note - prev_bass
    if (mel_dir > 0 and bass_dir < 0) or (mel_dir < 0 and bass_dir > 0):
        score += 0.3 # Bonus
        
    # 3. Resolving Dissonance
    # If previous was tritone (6) or minor second (1), current should be consonant
    if prev_interval in (1, 6, 11):
        if curr_interval in (3, 4, 7, 8, 9):
            score += 0.5 # Good resolution
        else:
            score -= 0.5 # Unresolved dissonance
            
    # 4. Leap Resolution
    # If melody leaped > 4 semitones, it should move in opposite direction by step
    if abs(mel_dir) > 4:
        # Check next note (requires future awareness, simplified here)
        pass

    return max(0.0, score)

def analyze_cadence(chords: list[ChordLabel], key: Scale) -> CadenceType | None:
    """Detect the type of cadence at the end of a sequence."""
    if len(chords) < 2: return None
    
    c1, c2 = chords[-2], chords[-1]
    
    # Get degrees (simplified)
    d1 = ((c1.root - key.root) % 12)
    d2 = ((c2.root - key.root) % 12)
    
    # Scale degrees (C Major: 0=I, 2=II, 4=III, 5=IV, 7=V, 9=VI, 11=VII)
    # V -> I (7 -> 0)
    if d1 == 7 and d2 == 0: return CadenceType.AUTHENTIC
    # IV -> I (5 -> 0)
    if d1 == 5 and d2 == 0: return CadenceType.PLAGAL
    # V -> vi (7 -> 9)
    if d1 == 7 and d2 == 9: return CadenceType.DECEPTIVE
    # x -> V (x -> 7)
    if d2 == 7: return CadenceType.HALF
    
    return None
