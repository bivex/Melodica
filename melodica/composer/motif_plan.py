"""composer/motif_plan.py — Bind a motif to an instrument across a full composition.

MotifDevelopmentPlan describes HOW a named leitmotif should appear in each
structural part (IdeaPart) of a track.  Each entry specifies:
  - which part (by index or name)
  - which transform to apply (develop() kwargs)
  - which instrument track receives the rendered notes
  - optional tension-driven velocity envelope

Usage
-----
    from melodica.composer.motif_plan import MotifDevelopmentPlan, MotifEntry

    plan = MotifDevelopmentPlan(
        registry=my_registry,
        motif_name="hero",
        default_instrument="flute",
    )
    plan.add(part_index=0, instrument="flute", transform={})
    plan.add(part_index=1, instrument="strings", transform={"augment_factor": 2.0})
    plan.add(part_index=2, instrument="strings", transform={"invert": True, "transpose": -5})

    # Render — returns {instrument_name: [NoteInfo, ...]}
    tracks_patch = plan.render(parts, part_offsets)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from melodica.composer.leitmotif import LeitmotifRegistry
from melodica.types_pkg._notes import NoteInfo

if TYPE_CHECKING:
    from melodica.composer.tension_curve import TensionCurve


@dataclass
class MotifEntry:
    """One appearance of a motif in a specific structural part."""

    part_index: int
    instrument: str          # track name in the album dict
    transform: dict          # kwargs forwarded to Motif.develop()
    # Optional: velocity envelope built from a TensionCurve.
    # When set, notes rendered by this entry are shaped by it.
    tension_curve: "TensionCurve | None" = None
    # Override instrument role for envelope shaping (default: "lead")
    role: str = "lead"
    # Silence this entry (mute without removing)
    muted: bool = False


@dataclass
class MotifDevelopmentPlan:
    """Binds a named leitmotif to an instrument track across form sections.

    Parameters
    ----------
    registry : LeitmotifRegistry
        Registry containing the motif.
    motif_name : str
        Name of the motif inside the registry.
    default_instrument : str
        Fallback instrument track name when MotifEntry.instrument is empty.
    """

    registry: LeitmotifRegistry
    motif_name: str
    default_instrument: str = "lead"
    _entries: list[MotifEntry] = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------
    # Building
    # ------------------------------------------------------------------

    def add(
        self,
        part_index: int,
        instrument: str | None = None,
        transform: dict | None = None,
        tension_curve: "TensionCurve | None" = None,
        role: str = "lead",
        muted: bool = False,
    ) -> MotifDevelopmentPlan:
        """Register one motif appearance.  Returns self for chaining."""
        self._entries.append(MotifEntry(
            part_index=part_index,
            instrument=instrument or self.default_instrument,
            transform=transform or {},
            tension_curve=tension_curve,
            role=role,
            muted=muted,
        ))
        return self

    def add_arc(
        self,
        part_indices: list[int],
        instruments: list[str] | str,
        transforms: list[dict] | None = None,
        tension_curves: "list[TensionCurve | None] | None" = None,
        role: str = "lead",
    ) -> MotifDevelopmentPlan:
        """Convenience — register multiple entries at once for a dramatic arc.

        If *instruments* is a single string it is used for all parts.
        If *transforms* is shorter than *part_indices*, the last entry repeats.
        """
        instr_list = (
            [instruments] * len(part_indices)
            if isinstance(instruments, str)
            else list(instruments)
        )
        xforms = transforms or [{}] * len(part_indices)
        tcurves = tension_curves or [None] * len(part_indices)

        for i, pidx in enumerate(part_indices):
            self.add(
                part_index=pidx,
                instrument=instr_list[i] if i < len(instr_list) else self.default_instrument,
                transform=xforms[i] if i < len(xforms) else xforms[-1],
                tension_curve=tcurves[i] if i < len(tcurves) else None,
                role=role,
            )
        return self

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(
        self,
        parts: list,
        part_offsets: list[float],
        *,
        merge_into: dict[str, list[NoteInfo]] | None = None,
    ) -> dict[str, list[NoteInfo]]:
        """Render all entries and return {instrument: [NoteInfo]}.

        Parameters
        ----------
        parts : list[IdeaPart]
            Ordered parts from IdeaToolConfig.
        part_offsets : list[float]
            Beat offset for each part (same order).
        merge_into : dict, optional
            If given, rendered notes are APPENDED into this dict and it is
            returned.  Useful for adding motif layers to an existing track dict.

        Returns
        -------
        dict[str, list[NoteInfo]]
            {track_name: notes_to_add}
        """
        from melodica.composer.velocity_envelope import tension_curve_to_envelope

        out: dict[str, list[NoteInfo]] = {}
        if merge_into is not None:
            out = merge_into

        for entry in self._entries:
            if entry.muted:
                continue
            if entry.part_index >= len(parts):
                continue

            offset = part_offsets[entry.part_index] if entry.part_index < len(part_offsets) else 0.0
            part = parts[entry.part_index]
            scale = getattr(part, "scale", None)

            # Build transform — inject scale for diatonic ops if available
            kw = dict(entry.transform)
            if scale is not None:
                if "transpose_diatonic_degrees" in kw and "transpose_diatonic_scale" not in kw:
                    kw["transpose_diatonic_scale"] = scale
                if "invert_diatonic" in kw and "invert_diatonic_scale" not in kw:
                    kw["invert_diatonic_scale"] = scale

            notes = self.registry.render(self.motif_name, offset=offset, **kw)
            if not notes:
                continue

            # Apply tension envelope if provided
            if entry.tension_curve is not None:
                env = tension_curve_to_envelope(
                    entry.tension_curve, role=entry.role
                )
                notes = env.apply(notes)

            tname = entry.instrument
            if tname not in out:
                out[tname] = []
            out[tname].extend(notes)

        return out

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def summary(self) -> str:
        """Human-readable summary of the plan."""
        lines = [f"MotifDevelopmentPlan: '{self.motif_name}'"]
        for e in self._entries:
            status = "MUTED" if e.muted else "active"
            xf = ", ".join(f"{k}={v!r}" for k, v in e.transform.items()) or "identity"
            tc = "w/tension" if e.tension_curve else ""
            lines.append(
                f"  part[{e.part_index}] → {e.instrument} [{status}] {xf} {tc}"
            )
        return "\n".join(lines)
