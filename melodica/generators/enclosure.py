"""Enclosure (approach note) generator.

Generates chromatic/diatonic enclosures around target chord tones —
the signature sound of bebop vocabulary. An enclosure surrounds a
target note from above and/or below before landing on it.

Enclosure types:
    "chromatic_above_below" — approach from semitone above, then below
    "chromatic_below_above" — below then above
    "diatonic_above_below"  — scale step above, then below
    "double_chromatic"      — two chromatic notes from one direction
    "delayed"               — approach on beat, target on off-beat

Players: Charlie Parker, Clifford Brown, John Coltrane, Barry Harris.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Scale
from melodica.utils import nearest_pitch, snap_to_scale


@dataclass
class EnclosureGenerator(PhraseGenerator):
    """Generate enclosure patterns around chord tones.

    Parameters
    ----------
    enclosure_type : str
        Type of enclosure pattern.
    target : str
        "chord_tones" — enclose 3rds, 5ths, 7ths.
        "roots" — enclose chord roots.
        "guide_tones" — enclose 3rds and 7ths only.
        "all" — any scale or chord tone.
    rhythm_placement : str
        "on_beat" — land on the beat.
        "off_beat" — land on the & (upbeat).
        "mixed" — varied placement.
    density : float
        Probability of enclosing a given target (0–1).
    connection_style : str
        "stepwise" — approach by step.
        "leap" — allow wider intervals.
    """

    name: str = field(default="enclosure", init=False)
    enclosure_type: str = "chromatic_above_below"
    target: str = "chord_tones"
    rhythm_placement: str = "mixed"
    density: float = 0.7
    connection_style: str = "stepwise"
    params: GeneratorParams = field(default_factory=GeneratorParams)

    def __post_init__(self) -> None:
        valid_types = {
            "chromatic_above_below", "chromatic_below_above",
            "diatonic_above_below", "double_chromatic",
            "delayed", "mixed",
        }
        if self.enclosure_type not in valid_types:
            raise ValueError(
                f"enclosure_type must be one of {valid_types}, got {self.enclosure_type!r}"
            )

    def _get_targets(self, chord: ChordLabel, key: Scale) -> list[int]:
        """Get target pitch classes for this chord."""
        root = chord.root
        pcs = chord.pitch_classes()

        if self.target == "roots":
            return [root]
        if self.target == "guide_tones":
            # 3rd and 7th
            gt = []
            if len(pcs) > 1:
                gt.append(int(pcs[1]))
            if len(pcs) > 3:
                gt.append(int(pcs[3]))
            elif len(pcs) > 1:
                gt.append(int(pcs[1]))
            return gt if gt else [root]
        if self.target == "all":
            degs = key.degrees()
            return [int(d) % 12 for d in degs] if degs else pcs
        # chord_tones
        return [int(p) for p in pcs]

    def _enclose(self, target_pitch: int, key: Scale) -> list[int]:
        """Generate enclosure notes around target_pitch, ending on target."""
        etype = self.enclosure_type
        if etype == "mixed":
            etype = random.choice([
                "chromatic_above_below", "chromatic_below_above",
                "diatonic_above_below", "double_chromatic",
            ])

        if etype == "chromatic_above_below":
            return [target_pitch + 1, target_pitch - 1, target_pitch]
        if etype == "chromatic_below_above":
            return [target_pitch - 1, target_pitch + 1, target_pitch]
        if etype == "double_chromatic":
            direction = random.choice([-1, 1])
            return [target_pitch + direction * 2, target_pitch + direction, target_pitch]
        # diatonic_above_below — use scale steps
        degs = key.degrees()
        if degs:
            above = snap_to_scale(target_pitch + 2, key)
            below = snap_to_scale(target_pitch - 2, key)
            return [above, below, target_pitch]
        return [target_pitch + 1, target_pitch - 1, target_pitch]

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

        for chord in chords:
            targets = self._get_targets(chord, key)
            chord_start = chord.start
            chord_dur = chord.duration

            # Pick 1–3 targets per chord
            n_targets = random.randint(1, min(3, len(targets)))
            chosen = random.sample(targets, min(n_targets, len(targets)))

            # Space targets evenly within chord duration
            for ti, target_pc in enumerate(chosen):
                anchor = (low + high) // 2
                target_pitch = nearest_pitch(target_pc, anchor)
                target_pitch = max(low, min(high, target_pitch))

                # Decide: enclose or just play the target
                if random.random() < self.density:
                    enclosed = self._enclose(target_pitch, key)
                else:
                    enclosed = [target_pitch]

                # Place in time
                t_base = chord_start + (ti / max(1, len(chosen))) * chord_dur
                beat_dur = chord_dur / max(1, len(chosen)) / max(1, len(enclosed))

                for ei, p in enumerate(enclosed):
                    p = max(low, min(high, p))
                    onset = t_base + ei * beat_dur
                    if onset >= chord_start + chord_dur or onset >= duration_beats:
                        break

                    # Velocity: approach notes quieter, target louder
                    is_target = (ei == len(enclosed) - 1)
                    vel = base_vel if is_target else max(1, base_vel - 12)

                    # Rhythm placement
                    dur = beat_dur * 0.85
                    if self.rhythm_placement == "off_beat" and not is_target:
                        onset += beat_dur * 0.5

                    notes.append(NoteInfo(
                        pitch=p,
                        start=round(onset, 4),
                        duration=max(0.1, dur),
                        velocity=vel,
                    ))

        return notes
