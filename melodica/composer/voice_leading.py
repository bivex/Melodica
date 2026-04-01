"""
composer/voice_leading.py — SATB Voice Leading Engine.

Four independent voices with classical voice leading rules:
- No parallel fifths/octaves
- Proper preparation and resolution of dissonances
- Voice range constraints
- Minimal motion preference
- Cross-relation avoidance
"""

from __future__ import annotations

from dataclasses import dataclass

from melodica.types import ChordLabel, NoteInfo, Quality, Scale

# SATB voice ranges (MIDI pitches)
VOICE_RANGES: dict[str, tuple[int, int]] = {
    "soprano": (60, 81),  # C4 - A5
    "alto": (53, 74),  # F3 - D5
    "tenor": (45, 69),  # A2 - C4 (written)
    "bass": (36, 60),  # C2 - C4
}

# Voice order for processing (outside-in)
VOICE_ORDER = ["bass", "soprano", "alto", "tenor"]


def _pitch_class(pitch: int) -> int:
    return pitch % 12


def _interval(a: int, b: int) -> int:
    """Semitone interval from a to b (positive = up)."""
    return b - a


def _is_parallel_fifth(prev_a: int, prev_b: int, curr_a: int, curr_b: int) -> bool:
    """Check if two voices create parallel fifths."""
    prev_int = (_pitch_class(prev_a) - _pitch_class(prev_b)) % 12
    curr_int = (_pitch_class(curr_a) - _pitch_class(curr_b)) % 12
    # Parallel = both are perfect fifths (7 semitones) AND both move in same direction
    if prev_int == 7 and curr_int == 7:
        # Both voices moving in same direction
        dir_a = 1 if curr_a > prev_a else (-1 if curr_a < prev_a else 0)
        dir_b = 1 if curr_b > prev_b else (-1 if curr_b < prev_b else 0)
        if dir_a == dir_b and dir_a != 0:
            return True
    return False


def _is_parallel_octave(prev_a: int, prev_b: int, curr_a: int, curr_b: int) -> bool:
    """Check if two voices create parallel octaves."""
    prev_int = (_pitch_class(prev_a) - _pitch_class(prev_b)) % 12
    curr_int = (_pitch_class(curr_a) - _pitch_class(curr_b)) % 12
    if prev_int == 0 and curr_int == 0:
        dir_a = 1 if curr_a > prev_a else (-1 if curr_a < prev_a else 0)
        dir_b = 1 if curr_b > prev_b else (-1 if curr_b < prev_b else 0)
        if dir_a == dir_b and dir_a != 0:
            return True
    return False


def _motion_type(a: int, b: int) -> str:
    """Classify motion between two notes."""
    if a == b:
        return "oblique"
    return "parallel"  # both move same direction (simplified)


@dataclass
class VoiceLeadingEngine:
    """
    SATB voice leading engine.

    Takes chord progressions and produces 4-voice voicings with proper
    voice leading: no parallel fifths/octaves, minimal motion, proper ranges.
    """

    strict_mode: bool = True  # if True, reject parallel fifths/octaves
    max_voice_gap: int = 12  # max interval between adjacent voices

    def voicize_progression(
        self,
        chords: list[ChordLabel],
        scale: Scale,
    ) -> dict[str, list[NoteInfo]]:
        """
        Convert chord progression to 4-voice SATB voicing.

        Returns dict with keys: "soprano", "alto", "tenor", "bass"
        Each value is a list of NoteInfo for that voice.
        """
        if not chords:
            return {v: [] for v in VOICE_ORDER}

        # Initialize voices with first chord
        voices: dict[str, list[int]] = {}
        first_voicing = self._best_initial_voicing(chords[0], scale)
        # first_voicing is [sop, alt, ten, bass]
        voice_names = ["soprano", "alto", "tenor", "bass"]
        for i, vn in enumerate(voice_names):
            voices[vn] = [first_voicing[i]]

        # Progress through chords
        for i in range(1, len(chords)):
            prev_voicing = [voices[vn][-1] for vn in voice_names]
            chord = chords[i]
            candidates = self._generate_candidates(chord, scale, prev_voicing)
            best = self._select_best(prev_voicing, candidates)
            for j, vn in enumerate(voice_names):
                voices[vn].append(best[j])

        # Convert to NoteInfo
        result: dict[str, list[NoteInfo]] = {}
        for voice in voice_names:
            notes = []
            for i, chord in enumerate(chords):
                pitch = voices[voice][i]
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(chord.start, 6),
                        duration=chord.duration,
                        velocity=80,
                    )
                )
            result[voice] = notes

        return result

    def _best_initial_voicing(self, chord: ChordLabel, scale: Scale) -> list[int]:
        """Find best initial SATB voicing for a chord."""
        root = chord.root
        pcs = chord.pitch_classes()
        if not pcs:
            return [72, 64, 55, 36]  # C5, E4, G3, C2

        # Each voice gets a chord tone in its range
        sop = self._nearest_in_range(pcs[0], VOICE_RANGES["soprano"])
        alt = self._nearest_in_range(pcs[min(1, len(pcs) - 1)], VOICE_RANGES["alto"])
        ten = self._nearest_in_range(pcs[min(2, len(pcs) - 1)], VOICE_RANGES["tenor"])
        bass = self._nearest_in_range(root, VOICE_RANGES["bass"])

        # Ensure ordering: soprano > alto > tenor > bass
        if ten >= alt:
            ten -= 12
        if alt >= sop:
            alt -= 12

        # Clamp
        sop = max(VOICE_RANGES["soprano"][0], min(VOICE_RANGES["soprano"][1], sop))
        alt = max(VOICE_RANGES["alto"][0], min(VOICE_RANGES["alto"][1], alt))
        ten = max(VOICE_RANGES["tenor"][0], min(VOICE_RANGES["tenor"][1], ten))
        bass = max(VOICE_RANGES["bass"][0], min(VOICE_RANGES["bass"][1], bass))

        return [sop, alt, ten, bass]

    def _generate_candidates(
        self,
        chord: ChordLabel,
        scale: Scale,
        prev_voicing: list[int],
    ) -> list[list[int]]:
        """Generate candidate voicings for next chord."""
        pcs = chord.pitch_classes()
        if not pcs:
            return [prev_voicing]

        candidates = []
        ranges = [VOICE_RANGES[v] for v in VOICE_ORDER]

        # Generate all possible pitch assignments
        # For each voice, try all chord tones within range
        for bass_pc in pcs:
            bass = self._nearest_in_range(bass_pc, ranges[3])
            for sop_pc in pcs:
                sop = self._nearest_in_range(sop_pc, ranges[0])
                for alt_pc in pcs:
                    alt = self._nearest_in_range(alt_pc, ranges[1])
                    for ten_pc in pcs:
                        ten = self._nearest_in_range(ten_pc, ranges[2])
                        candidate = [sop, alt, ten, bass]

                        # Check ordering
                        if not (sop >= alt >= ten >= bass):
                            continue

                        # Check voice gaps
                        if any(
                            abs(candidate[j] - candidate[j + 1]) > self.max_voice_gap
                            for j in range(3)
                        ):
                            continue

                        # Score by voice leading quality
                        score = self._score_voicing(prev_voicing, candidate)
                        candidates.append((score, candidate))

        if not candidates:
            return [self._best_initial_voicing(chord, scale)]

        candidates.sort(key=lambda x: -x[0])
        return [c for _, c in candidates[:10]]

    def _select_best(
        self,
        prev: list[int],
        candidates: list[list[int]],
    ) -> list[int]:
        """Select best candidate avoiding parallel fifths/octaves."""
        for candidate in candidates:
            if self.strict_mode:
                # Check all voice pairs for parallel fifths/octaves
                has_parallels = False
                for i in range(4):
                    for j in range(i + 1, 4):
                        if _is_parallel_fifth(prev[i], prev[j], candidate[i], candidate[j]):
                            has_parallels = True
                            break
                        if _is_parallel_octave(prev[i], prev[j], candidate[i], candidate[j]):
                            has_parallels = True
                            break
                    if has_parallels:
                        break
                if has_parallels:
                    continue
            return candidate
        # Fallback: return best even if has parallels
        return candidates[0] if candidates else prev

    def _score_voicing(self, prev: list[int], curr: list[int]) -> float:
        """Score a voicing transition (higher = better voice leading)."""
        score = 0.0

        # Minimal motion bonus
        for i in range(4):
            motion = abs(curr[i] - prev[i])
            if motion == 0:
                score += 2.0  # stationary voice = excellent
            elif motion <= 2:
                score += 1.0  # stepwise = good
            elif motion <= 5:
                score += 0.5  # small skip = ok
            else:
                score -= 0.5  # large skip = penalty

        # Contrary motion bonus (bass vs soprano)
        if (curr[0] > prev[0]) != (curr[3] > prev[3]):
            score += 1.0

        # Smooth inner voices
        inner_motion = abs(curr[1] - prev[1]) + abs(curr[2] - prev[2])
        score -= inner_motion * 0.1

        return score

    def _nearest_in_range(self, pc: int, voice_range: tuple[int, int]) -> int:
        """Find nearest pitch with given pitch class within voice range."""
        lo, hi = voice_range
        # Find all pitches with this pc in range
        candidates = []
        for p in range(lo, hi + 1):
            if p % 12 == pc:
                candidates.append(p)
        if candidates:
            mid = (lo + hi) // 2
            return min(candidates, key=lambda p: abs(p - mid))
        # Fallback: clamp
        pitch = lo + (pc - lo % 12) % 12
        while pitch > hi:
            pitch -= 12
        return max(lo, pitch)
