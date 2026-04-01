"""
modifiers/voicings.py — Chord Voicing Modifiers.

Layer: Application / Domain
Handles Drop 2, Inversions, and Top-note voicing strategies.
"""

from __future__ import annotations

import typing
from dataclasses import dataclass
from melodica.types import NoteInfo
from melodica.modifiers import ModifierContext

@dataclass
class DropVoicingModifier:
    """Implements Drop 2, Drop 3, Drop 2&4 voicings for chords."""
    drop_mode: str = "drop_2" # "drop_2", "drop_3", "drop_2_4"

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        # Group notes by start time (assumed they represent a chord)
        groups = {}
        for n in notes:
            t = round(n.start, 4)
            groups.setdefault(t, []).append(n)
            
        result = []
        for t, g in groups.items():
            if len(g) >= 3:
                g.sort(key=lambda x: x.pitch, reverse=True) # Top to bottom
                # Drop rules:
                if self.drop_mode == "drop_2":
                    g[1].pitch -= 12
                elif self.drop_mode == "drop_3":
                    g[2].pitch -= 12
                elif self.drop_mode == "drop_2_4" and len(g) >= 4:
                    g[1].pitch -= 12
                    g[3].pitch -= 12
            result.extend(g)
        return result

@dataclass
class TopNoteVoicingModifier:
    """Ensures a specific chord tone (1, 3, 5, 7) is the highest in the voicing."""
    target_degree: int = 1 # 1=Root, 3=Third...

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        groups = {}
        for n in notes:
            t = round(n.start, 4)
            groups.setdefault(t, []).append(n)
            
        result = []
        for t, g in groups.items():
            if not g: continue
            if not context.chords:
                result.extend(g)
                continue
            # Find the note that is the target degree in the current chord
            # Find closest chord by time
            relevant_chord = next((c for c in context.chords if abs(c.start - t) < 0.1), context.chords[0])
            pcs = relevant_chord.pitch_classes()
            # Approximation: target_degree 1=index 0, 3=index 1, 5=index 2
            deg_idx = {1:0, 3:1, 5:2, 7:3}.get(self.target_degree, 0)
            target_pc = pcs[deg_idx % len(pcs)]
            
            # Find which note in g matches target_pc
            target_note = min(g, key=lambda x: abs(x.pitch % 12 - target_pc))
            other_notes = [x for x in g if x != target_note]
            
            # Reposition target_note to be the highest
            max_pitch = max((n.pitch for n in other_notes), default=60)
            while target_note.pitch <= max_pitch:
                target_note.pitch += 12
            while target_note.pitch > max_pitch + 12:
                target_note.pitch -= 12
                
            result.extend(g)
        return result

@dataclass
class InversionModifier:
    """Rotates chord tones for inversions."""
    inversion: int = 0 # 0=Root, 1=1st, 2=2nd, 3=3rd

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        if self.inversion == 0: return notes
        
        groups = {}
        for n in notes:
            t = round(n.start, 4)
            groups.setdefault(t, []).append(n)
            
        result = []
        for t, g in groups.items():
            if len(g) >= 2:
                g.sort(key=lambda x: x.pitch)
                for i in range(self.inversion % len(g)):
                    g[i].pitch += 12
            result.extend(g)
        return result
