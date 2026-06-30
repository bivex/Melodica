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

"""
composer/texture_controller.py — Texture/density automation.

Controls musical texture dynamically:
- Full chord (all voices)
- Chord without bass
- Bass only
- Unison/melody only
- Silence/rest
- Building/thinning

Uses tension curve to modulate density automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from melodica.types import NoteInfo, ChordLabel
from melodica.composer.tension_curve import TensionCurve, TensionPhase


class TextureLevel(Enum):
    SILENCE = 0  # no notes
    BASS_ONLY = 1  # just bass note
    THIN = 2  # bass + one chord tone
    MELODY_ONLY = 3  # melody line only
    FULL = 4  # full chord (all voices)
    DOUBLE = 5  # doubled full chord (loudest)


@dataclass
class TextureController:
    """
    Dynamically controls texture density based on tension curve.

    Controls how many voices play at each moment:
    - Rest phase → bass only or silence
    - Build phase → gradually add voices
    - Climax → full chord, doubled
    - Resolution → thin out

    base_texture:    default texture level
    tension_mapping: maps tension 0-1 to TextureLevel
    """

    base_texture: TextureLevel = TextureLevel.FULL
    tension_curve: TensionCurve | None = None

    def apply_texture(
        self,
        all_notes: dict[str, list[NoteInfo]],
        duration_beats: float,
    ) -> dict[str, list[NoteInfo]]:
        """
        Apply texture dynamics to voice tracks.
        """
        if self.tension_curve is None:
            return all_notes

        result: dict[str, list[NoteInfo]] = {v: [] for v in all_notes}
        
        # Track role detection based on name
        roles = {}
        for name in all_notes:
            name_lower = name.lower()
            if any(x in name_lower for x in ("bass", "cello", "low")):
                roles[name] = "bass"
            elif any(x in name_lower for x in ("soprano", "lead", "melody", "flute")):
                roles[name] = "soprano"
            elif any(x in name_lower for x in ("alto", "viola")):
                roles[name] = "alto"
            else:
                roles[name] = "tenor"

        for voice_name, notes in all_notes.items():
            role = roles.get(voice_name, "tenor")
            for note in notes:
                tension = self.tension_curve.tension_at(note.start)
                level = self._tension_to_texture(tension)

                # Rule: never silence the bass root during BASS_ONLY or higher
                if level != TextureLevel.SILENCE and role == "bass":
                    result[voice_name].append(note)
                    continue

                if self._voice_is_active(role, level):
                    result[voice_name].append(note)

        return result

    def _tension_to_texture(self, tension: float) -> TextureLevel:
        """Map tension value to texture level.

        Note: SILENCE is intentionally never returned. The classical tension
        curve starts near zero, so mapping the lowest tension to SILENCE muted
        every voice (including the bass) for the first ~30+ s of each track —
        a long opening gap. Low tension now resolves to BASS_ONLY so the bass
        anchors the intro audibly while upper voices enter as tension rises.
        """
        if tension < 0.15:
            return TextureLevel.BASS_ONLY
        elif tension < 0.3:
            return TextureLevel.BASS_ONLY
        elif tension < 0.5:
            return TextureLevel.THIN
        elif tension < 0.7:
            return TextureLevel.MELODY_ONLY
        elif tension < 0.9:
            return TextureLevel.FULL
        else:
            return TextureLevel.DOUBLE

    def _voice_is_active(self, voice: str, level: TextureLevel) -> bool:
        """Check if a voice should be active at a given texture level."""
        if level == TextureLevel.SILENCE:
            return False
        elif level == TextureLevel.BASS_ONLY:
            return voice == "bass"
        elif level == TextureLevel.THIN:
            return voice in ("bass", "soprano")
        elif level == TextureLevel.MELODY_ONLY:
            return voice == "soprano"
        elif level in (TextureLevel.FULL, TextureLevel.DOUBLE):
            return True
        return True

    def get_density_at(self, beat: float) -> float:
        """Get normalized density (0-1) at a specific beat."""
        if self.tension_curve is None:
            return 0.8
        tension = self.tension_curve.tension_at(beat)
        # Map tension to density (non-linear)
        if tension < 0.3:
            return 0.2  # sparse
        elif tension < 0.6:
            return 0.5 + tension * 0.3
        else:
            return 0.8 + tension * 0.2  # dense at climax
