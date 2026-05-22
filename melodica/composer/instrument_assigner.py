# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
composer/instrument_assigner.py -- Intelligent helper to map generators to tracks automatically based on roles, styles, and registers.

Layer: Application / Composer
Style: Standard orchestral orchestrator helper.
"""

from __future__ import annotations

from typing import Dict, List, Any
from melodica.generators import PhraseGenerator
from melodica.composer.orchestrator import GM_PROFILES


class InstrumentAssigner:
    """
    InstrumentAssigner: Helper tool to automatically assign generators
    to MIDI tracks based on their natural registers, tag roles, and style profiles.
    """

    def __init__(self) -> None:
        pass

    def assign_generators(
        self,
        generators: List[PhraseGenerator],
        track_names: List[str]
    ) -> Dict[str, PhraseGenerator]:
        """
        Map a list of PhraseGenerator instances to a list of track names.
        Uses key ranges (ambitus) and naming heuristics.
        """
        assignments: Dict[str, PhraseGenerator] = {}
        if not generators or not track_names:
            return assignments

        # Classify track names into register categories: low, mid, high, percussion, chordal
        low_tracks = []
        mid_tracks = []
        high_tracks = []
        perc_tracks = []
        chord_tracks = []
        
        for name in track_names:
            lower = name.lower()
            if "bass" in lower or "tuba" in lower or "low" in lower or "contrabass" in lower or "cello" in lower:
                low_tracks.append(name)
            elif "perc" in lower or "drum" in lower or "snare" in lower or "cymbal" in lower or "timpani" in lower:
                perc_tracks.append(name)
            elif "chord" in lower or "pad" in lower or "harmony" in lower or "brass" in lower or "ensemble" in lower:
                chord_tracks.append(name)
            elif "melody" in lower or "lead" in lower or "solo" in lower or "soprano" in lower or "high" in lower:
                high_tracks.append(name)
            else:
                # Default bucket
                mid_tracks.append(name)

        # Classify generators
        for gen in generators:
            # Check register range
            p = gen.params
            avg_pitch = (p.key_range_low + p.key_range_high) / 2
            
            is_perc = "percussion" in gen.name.lower() or "drum" in gen.name.lower() or "cymbal" in gen.name.lower() or "timpani" in gen.name.lower() or "snare" in gen.name.lower()
            
            assigned_track = None
            
            if is_perc:
                if perc_tracks:
                    assigned_track = perc_tracks.pop(0)
            elif avg_pitch < 50:
                if low_tracks:
                    assigned_track = low_tracks.pop(0)
                elif mid_tracks:
                    assigned_track = mid_tracks.pop(0)
            elif avg_pitch > 72:
                if high_tracks:
                    assigned_track = high_tracks.pop(0)
                elif mid_tracks:
                    assigned_track = mid_tracks.pop(0)
            else:
                # Mid register
                if chord_tracks and "chord" in gen.name.lower():
                    assigned_track = chord_tracks.pop(0)
                elif mid_tracks:
                    assigned_track = mid_tracks.pop(0)
                elif high_tracks:
                    assigned_track = high_tracks.pop(0)

            # Fallback if no matching bucket or bucket was exhausted
            if assigned_track is None:
                all_remaining = low_tracks + perc_tracks + chord_tracks + high_tracks + mid_tracks
                if all_remaining:
                    assigned_track = all_remaining[0]
                    # Remove it from whatever list it was in
                    for lst in [low_tracks, perc_tracks, chord_tracks, high_tracks, mid_tracks]:
                        if assigned_track in lst:
                            lst.remove(assigned_track)
                            break
            
            if assigned_track:
                assignments[assigned_track] = gen

        return assignments

    def assign_gm_programs(self, track_roles: Dict[str, str]) -> Dict[str, int]:
        """
        Map a dict of track names and their roles ("bass", "melody", "harmony", "percussion")
        to standard General MIDI (GM) program numbers based on balanced orchestration.
        """
        gm_assignments: Dict[str, int] = {}
        
        # Categorized lists of instruments from GM_PROFILES
        low_sustained = [58, 43, 70, 57]  # Tuba, Contrabass, Bassoon, Trombone
        low_plucked = [32, 33, 34]       # Acoustic Bass, Finger Bass, Pick Bass
        high_sustained = [73, 68, 56, 40] # Flute, Oboe, Trumpet, Violin
        mid_sustained = [60, 41, 61, 48]  # Horn, Viola, Brass Section, String Ensemble
        chordal_percussive = [0, 4, 6]    # Grand Piano, E-Piano, Harpsichord
        ambient_pads = [89, 95, 91]       # Warm Pad, Sweep Pad, Choir Pad
        percussive = [47, 12, 14, 115]    # Timpani, Marimba, Tubular Bells, Woodblock

        for track_name, role in track_roles.items():
            r = role.lower()
            if "bass" in r:
                # Bass role
                if "synth" in track_name.lower() or "pad" in track_name.lower():
                    gm_assignments[track_name] = 38  # Synth Bass 1
                elif any(kw in track_name.lower() for kw in ["brass", "orchestra", "bassoon", "tuba"]):
                    gm_assignments[track_name] = 58  # Tuba
                else:
                    gm_assignments[track_name] = 32  # Acoustic Bass
            elif "melody" in r or "lead" in r:
                # Melody/Lead role
                if "string" in track_name.lower() or "violin" in track_name.lower():
                    gm_assignments[track_name] = 40  # Violin
                elif "wind" in track_name.lower() or "flute" in track_name.lower():
                    gm_assignments[track_name] = 73  # Flute
                elif "brass" in track_name.lower() or "trumpet" in track_name.lower():
                    gm_assignments[track_name] = 56  # Trumpet
                else:
                    gm_assignments[track_name] = 68  # Oboe
            elif "harmony" in r or "chord" in r or "pad" in r:
                # Chordal/Harmonic pad
                if "pad" in track_name.lower() or "choir" in track_name.lower():
                    gm_assignments[track_name] = 89  # Warm Pad
                elif "brass" in track_name.lower():
                    gm_assignments[track_name] = 61  # Brass Section
                elif "string" in track_name.lower() or "ensemble" in track_name.lower():
                    gm_assignments[track_name] = 48  # String Ensemble 1
                else:
                    gm_assignments[track_name] = 0   # Acoustic Grand Piano
            elif "perc" in r or "rhythm" in r or "drum" in r:
                # Percussion / Transient
                if "bell" in track_name.lower() or "chime" in track_name.lower():
                    gm_assignments[track_name] = 14  # Tubular Bells
                elif "timp" in track_name.lower() or "bass" in track_name.lower():
                    gm_assignments[track_name] = 47  # Timpani
                else:
                    gm_assignments[track_name] = 115 # Woodblock
            else:
                # Default fallback
                gm_assignments[track_name] = 0       # Acoustic Grand Piano

        return gm_assignments
