"""Shell voicing generator.

Generates jazz shell voicings — the fundamental piano/guitar comping
voicings built from root + 3rd + 7th (sometimes omitting root for
rootless voicings). These are the building blocks of jazz harmony.

Shell voicing types:
    "root_shell" — root + 3rd + 7th (3-note shell).
    "rootless"   — 3rd + 7th (2-note, for piano with bass player).
    "spread"     — root + 7th in LH, 3rd + extension in RH.
    "A_form"     — close position rootless (3-7 or 7-3).
    "B_form"     — spread position rootless.

Players: Bud Powell, Thelonious Monk, Bill Evans, Wynton Kelly,
         Red Garland, Ahmad Jamal.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Quality, Scale
from melodica.utils import nearest_pitch


@dataclass
class ShellVoicingGenerator(PhraseGenerator):
    """Generate shell voicings for jazz comping.

    Parameters
    ----------
    voicing_type : str
        "root_shell" — root + 3rd + 7th.
        "rootless" — 3rd + 7th (no root).
        "spread" — root + 7th low, 3rd high.
        "A_form" — close rootless (3 below 7).
        "B_form" — spread rootless (7 below 3).
    rhythm : str
        "whole_note" — one chord per bar.
        "half_note" — two chords per bar.
        "charleston" — beat 1 and & of 2.
        "syncopated" — varied syncopation.
        "freddie_green" — quarter note pulse.
    voice_leading : bool
        Smooth voice leading between successive chords.
    drop_2 : bool
        Apply drop-2 technique (drop 2nd voice an octave).
    include_extensions : bool
        Add 9ths, 11ths, 13ths where appropriate.
    """

    name: str = field(default="shell_voicing", init=False)
    voicing_type: str = "root_shell"
    rhythm: str = "charleston"
    voice_leading: bool = True
    drop_2: bool = False
    include_extensions: bool = False
    params: GeneratorParams = field(default_factory=GeneratorParams)

    def __post_init__(self) -> None:
        valid = ("root_shell", "rootless", "spread", "A_form", "B_form")
        if self.voicing_type not in valid:
            raise ValueError(f"voicing_type must be one of {valid}, got {self.voicing_type!r}")
        valid_rhythm = ("whole_note", "half_note", "charleston", "syncopated", "freddie_green")
        if self.rhythm not in valid_rhythm:
            raise ValueError(f"rhythm must be one of {valid_rhythm}")

    def _chord_3rd_7th(self, chord: ChordLabel) -> tuple[int, int]:
        root = chord.root
        quality = chord.quality

        if quality in (Quality.MAJOR, Quality.MAJOR7):
            return (root + 4) % 12, (root + 11) % 12
        if quality in (Quality.MINOR, Quality.MINOR7):
            return (root + 3) % 12, (root + 10) % 12
        if quality == Quality.DOMINANT7:
            return (root + 4) % 12, (root + 10) % 12
        if quality == Quality.HALF_DIM7:
            return (root + 3) % 12, (root + 10) % 12
        if quality == Quality.DIMINISHED:
            return (root + 3) % 12, (root + 9) % 12
        if quality == Quality.AUGMENTED:
            return (root + 4) % 12, (root + 10) % 12
        return (root + 4) % 12, (root + 10) % 12

    def _extension_pc(self, chord: ChordLabel) -> int | None:
        if not self.include_extensions:
            return None
        exts = chord.extensions
        if exts:
            return int(exts[0]) % 12
        # Default: 9th for dominant, 11th for minor, 9th for major
        quality = chord.quality
        if quality == Quality.DOMINANT7:
            return (chord.root + 2) % 12
        if quality in (Quality.MINOR, Quality.MINOR7):
            return (chord.root + 5) % 12
        return (chord.root + 2) % 12

    def _build_voicing(
        self,
        chord: ChordLabel,
        prev_voicing: list[int] | None,
        low: int,
        high: int,
    ) -> list[int]:
        root = chord.root
        third_pc, seventh_pc = self._chord_3rd_7th(chord)

        # Anchor for voice leading
        anchor = (low + high) // 2
        if prev_voicing and self.voice_leading:
            anchor = prev_voicing[len(prev_voicing) // 2] if prev_voicing else anchor

        vtype = self.voicing_type

        if vtype == "root_shell":
            p_root = nearest_pitch(root, anchor - 12)
            p_3 = nearest_pitch(third_pc, p_root)
            p_7 = nearest_pitch(seventh_pc, p_3)
            voicing = [p_root, p_3, p_7]

        elif vtype == "rootless":
            p_3 = nearest_pitch(third_pc, anchor)
            p_7 = nearest_pitch(seventh_pc, p_3)
            voicing = [p_3, p_7]

        elif vtype == "spread":
            p_root = nearest_pitch(root, anchor - 12)
            p_7 = nearest_pitch(seventh_pc, p_root)
            p_3 = nearest_pitch(third_pc, p_7 + 7)
            voicing = [p_root, p_7, p_3]

        elif vtype == "A_form":
            # Close: 3 below 7
            p_3 = nearest_pitch(third_pc, anchor)
            p_7 = nearest_pitch(seventh_pc, p_3)
            if p_7 < p_3:
                p_7 += 12
            voicing = [p_3, p_7]

        else:  # B_form
            # Spread: 7 below 3
            p_7 = nearest_pitch(seventh_pc, anchor)
            p_3 = nearest_pitch(third_pc, p_7)
            if p_3 < p_7:
                p_3 += 12
            voicing = [p_7, p_3]

        # Voice leading: move to closest octave
        if prev_voicing and self.voice_leading:
            for i in range(min(len(voicing), len(prev_voicing))):
                target = voicing[i]
                prev = prev_voicing[i] if i < len(prev_voicing) else prev_voicing[-1]
                # Find closest octave of target to prev
                while target < prev - 6:
                    target += 12
                while target > prev + 6:
                    target -= 12
                voicing[i] = max(low, min(high, target))

        # Drop-2: lower the second voice by an octave
        if self.drop_2 and len(voicing) >= 2:
            voicing[1] = max(low, voicing[1] - 12)

        # Extensions
        ext_pc = self._extension_pc(chord)
        if ext_pc is not None and len(voicing) >= 2:
            top = voicing[-1]
            ext_pitch = nearest_pitch(ext_pc, top + 2)
            ext_pitch = max(low, min(high, ext_pitch))
            voicing.append(ext_pitch)

        # Clamp all
        return [max(low, min(high, p)) for p in voicing]

    def _rhythm_hits(self, chord_dur: float) -> list[tuple[float, float]]:
        """Return list of (onset_offset, duration) for hits within a chord."""
        if self.rhythm == "whole_note":
            return [(0.0, chord_dur * 0.95)]

        if self.rhythm == "half_note":
            d = chord_dur / 2 * 0.9
            return [(0.0, d), (chord_dur / 2, d)]

        if self.rhythm == "charleston":
            # Beat 1 and & of 2
            return [(0.0, 1.8), (2.5, min(1.5, chord_dur - 2.5))]

        if self.rhythm == "freddie_green":
            hits = []
            for beat in range(4):
                offset = float(beat)
                if offset >= chord_dur:
                    break
                hits.append((offset, 0.8))
            return hits

        # syncopated
        positions = [0.0]
        if chord_dur >= 4.0:
            positions.append(random.choice([1.5, 2.0, 2.5, 3.0, 3.5]))
        hits = []
        for pos in sorted(positions):
            if pos < chord_dur:
                hits.append((pos, min(1.5, chord_dur - pos) * 0.85))
        return hits

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        base_vel = self.base_velocity()
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        prev_voicing: list[int] | None = None

        for chord in chords:
            chord_start = chord.start
            chord_dur = min(chord.duration, duration_beats - chord_start) if chord_start < duration_beats else chord.duration

            if chord_start >= duration_beats:
                break

            voicing = self._build_voicing(chord, prev_voicing, low, high)
            prev_voicing = voicing

            hits = self._rhythm_hits(chord_dur)

            for offset, dur in hits:
                onset = chord_start + offset
                if onset >= duration_beats:
                    continue

                vel = base_vel + random.randint(-4, 4)

                for pi, pitch in enumerate(voicing):
                    # Stagger slightly for piano-like spread
                    note_onset = onset + pi * 0.015
                    if note_onset >= duration_beats:
                        break

                    v = vel
                    if pi == 0:
                        v = max(1, vel - 5)  # root slightly quieter
                    if pi == len(voicing) - 1 and len(voicing) > 1:
                        v = min(127, vel + 3)  # top note slightly louder

                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(note_onset, 4),
                        duration=max(0.1, dur),
                        velocity=max(1, min(127, v)),
                    ))

        return notes
