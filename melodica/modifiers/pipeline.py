# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-24
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
modifiers/pipeline.py — Non-Destructive Modifier Pipeline.

Layer: Application / Domain

Provides a Variation Stack (Pipeline) architecture for musical phrases.
This allows chaining modifiers like inserts in a mixer, preserving the base notes
so that variations can be dynamically reordered, bypassed, or adjusted.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
import typing

if typing.TYPE_CHECKING:
    from melodica.types import NoteInfo
    from melodica.modifiers import PhraseModifier, ModifierContext


@dataclass
class ModifierPipeline:
    """
    A non-destructive variation stack for musical phrases.
    Works like 'inserts' in a mixer: you add modifiers (rhythm, strumming, velocity, etc.),
    and the pipeline processes them sequentially.
    
    The original base notes are never mutated. You can change, reorder, or bypass
    modifiers in the chain, and instantly recalculate the result.
    """

    base_notes: list[NoteInfo]
    modifiers: list[PhraseModifier] = field(default_factory=list)
    bypassed_indices: set[int] = field(default_factory=set)

    def add_modifier(self, modifier: PhraseModifier) -> None:
        """Appends a modifier to the end of the chain."""
        self.modifiers.append(modifier)

    def insert_modifier(self, index: int, modifier: PhraseModifier) -> None:
        """Inserts a modifier at the specified position."""
        self.modifiers.insert(index, modifier)

    def remove_modifier(self, index: int) -> PhraseModifier:
        """Removes and returns the modifier at the specified position."""
        # Cleanup bypass state if we remove a modifier
        if index in self.bypassed_indices:
            self.bypassed_indices.remove(index)
        
        # Shift bypassed indices down
        new_bypassed = set()
        for b_idx in self.bypassed_indices:
            if b_idx > index:
                new_bypassed.add(b_idx - 1)
            else:
                new_bypassed.add(b_idx)
        self.bypassed_indices = new_bypassed

        return self.modifiers.pop(index)

    def replace_modifier(self, index: int, modifier: PhraseModifier) -> None:
        """Replaces a modifier at the specified position."""
        self.modifiers[index] = modifier

    def set_bypass(self, index: int, bypass: bool = True) -> None:
        """Enables or disables bypass for a specific modifier."""
        if bypass:
            self.bypassed_indices.add(index)
        else:
            self.bypassed_indices.discard(index)

    def clear_modifiers(self) -> None:
        """Removes all modifiers from the pipeline."""
        self.modifiers.clear()
        self.bypassed_indices.clear()

    def process(self, context: ModifierContext) -> list[NoteInfo]:
        """
        Passes the base notes through the modifier chain.
        Uses a fast deep copy of the base notes initially to ensure complete
        non-destruction, preventing in-place mutations inside modifiers from
        affecting the base notes.
        """
        # Optimized clone step to avoid the heavy copy.deepcopy
        current_notes = self._clone_notes(self.base_notes)

        for idx, modifier in enumerate(self.modifiers):
            if idx in self.bypassed_indices:
                continue
            
            # Apply transformation
            current_notes = modifier.modify(current_notes, context)

        return current_notes

    @staticmethod
    def _clone_notes(notes: list[NoteInfo]) -> list[NoteInfo]:
        """Fast deep-clone of NoteInfo list to preserve original phrase state."""
        cloned = []
        for n in notes:
            # Dataclasses replace does a shallow copy
            new_n = dataclasses.replace(n)
            # Ensure the expression dict is also copied to avoid reference sharing
            new_n.expression = dict(n.expression)
            cloned.append(new_n)
        return cloned
