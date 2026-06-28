# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
composer/polyphony_coordinator.py — Polyphonic Voice Coordinator.
Automatically post-processes track notes to resolve vertical harmonic clashes
(unisons, minor/major 2nds, tritones) by diatonically shifting lower-priority voices.
"""

from __future__ import annotations

import copy
from melodica.types import NoteInfo, Scale


class PolyphonicVoiceCoordinator:
    """Coordinates pitches vertically across multiple tracks to avoid masking and clashes."""

    def __init__(self, scale: Scale) -> None:
        self.scale = scale

    def _get_priority(self, track_name: str) -> int:
        """Get priority weight for a track (higher priority stays fixed)."""
        name_l = track_name.lower()
        if "solo" in name_l or "melody" in name_l or "vocals" in name_l or "dux" in name_l:
            return 100
        if "bass" in name_l or "contrabass" in name_l:
            return 10  # Bass is harmonic foundation, do not shift diatonically
        return 50  # Backing tracks, arpeggios, pads

    def coordinate(self, tracks: dict[str, list[NoteInfo]]) -> dict[str, list[NoteInfo]]:
        """Resolve clashes by shifting lower-priority notes diatonically."""
        # Deep copy to avoid mutating inputs
        result = {k: [copy.deepcopy(n) for n in v] for k, v in tracks.items()}
        track_names = sorted(result.keys(), key=self._get_priority)

        for i in range(len(track_names)):
            track_b_name = track_names[i]
            priority_b = self._get_priority(track_b_name)

            # Do not shift bass diatonically (could break chord root reference)
            if priority_b <= 10:
                continue

            for j in range(i + 1, len(track_names)):
                track_a_name = track_names[j]

                for note_b in result[track_b_name]:
                    for note_a in result[track_a_name]:
                        # Check temporal overlap
                        overlap_start = max(note_b.start, note_a.start)
                        overlap_end = min(note_b.start + note_b.duration, note_a.start + note_a.duration)
                        if overlap_start < overlap_end:
                            # Overlap detected! Check interval clash
                            interval = abs(note_b.pitch - note_a.pitch) % 12
                            if interval in (0, 1, 2, 6):  # Unison, m2, M2, Tritone
                                # Shift note_b by 1 diatonic degree
                                degs = [int(round(d)) for d in self.scale.degrees()]
                                n_degs = len(degs)
                                
                                # Convert pitch_b to continuous degree index
                                oct_b = note_b.pitch // 12
                                pc_b = note_b.pitch % 12
                                idx_b = min(range(n_degs), key=lambda i: min(abs(degs[i] - pc_b), 12 - abs(degs[i] - pc_b)))
                                deg_idx_b = oct_b * n_degs + idx_b
                                
                                # Try shifting by different scale degree offsets until we find one that does not clash
                                resolved = False
                                for offset in (2, -2, 3, -3, 4, -4, 1, -1):
                                    new_deg_idx = deg_idx_b + offset
                                    new_oct, new_pc_idx = divmod(new_deg_idx, n_degs)
                                    candidate_pitch = max(0, min(127, new_oct * 12 + degs[new_pc_idx]))
                                    
                                    if abs(candidate_pitch - note_a.pitch) % 12 not in (0, 1, 2, 6):
                                        note_b.pitch = candidate_pitch
                                        resolved = True
                                        break

        return result
