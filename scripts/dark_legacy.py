"""
dark_legacy.py — "The Fallen Kingdom"
A cinematic dark fantasy OST piece, ~3 minutes at 65 BPM.

Scale: A Harmonic Minor (root=9, HARMONIC_MINOR)
  — Characteristic V→Im resolution (E major → A minor) for
    that "ancient evil" drama; bII (Bb) for Phrygian flavour.

Structure (total 176 beats ≈ 2m 42s at 65 BPM):
  1. Mist of Ages   (16b) — solo strings pad, volume swell
  2. The Kingdom    (32b) — lead enters over pad + bass
  3. Ancient Curse  (32b) — add texture arp + open choir
  4. Battle         (48b) — full arrangement, walking bass, timpani
  5. Ruins          (32b) — strip to lead + pad + bass
  6. Into Darkness  (16b) — pad alone, fade to silence

All tracks now use rhythm-engine driven generators:
  fast_arp       → EuclideanRhythm E(11,16), up_down, 2 oct
  followed_bass  → EuclideanRhythm E(5,8) tresillo, root_fifth
  walking_bass   → walking bass (for battle)
  lead_melody    → ProbabilisticRhythm + Swing
  followed_chords→ SubdivisionGenerator 8th+ties, open voicing
"""

from pathlib import Path

from melodica.application.automation import ExpressionCurve
from melodica.application.orchestration import OrchestralBalancer
from melodica.composition import Composition, MusicDirector
from melodica.midi import export_midi
from melodica.modifiers import HumanizeModifier, ModifierContext
from melodica.types import Mode, Scale


KEY = Scale(root=9, mode=Mode.HARMONIC_MINOR)   # A Harmonic Minor
BPM = 65.0

# ---------------------------------------------------------------------------
# Automation helpers
# ---------------------------------------------------------------------------

def _swell(start: int, end: int, dur: float) -> ExpressionCurve:
    return ExpressionCurve.linear("volume", start, end, dur)

def _mod(start: int, end: int, dur: float) -> ExpressionCurve:
    return ExpressionCurve.linear("modulation", start, end, dur)

def _pan_drift(lo: int, hi: int, dur: float, freq: float = 0.2) -> ExpressionCurve:
    return ExpressionCurve.sinusoidal("pan", lo, hi, dur, freq=freq)


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------

def build_composition() -> Composition:
    comp = Composition(name="The_Fallen_Kingdom", key=KEY)

    # ------------------------------------------------------------------
    # 1. Mist of Ages  (16 beats = 4 chords × 4)
    #    Solo string pad — the kingdom before its fall.
    #    Im VII bVI V : descending harmonic minor, lands on tense V.
    # ------------------------------------------------------------------
    comp.add_section(
        name="Mist_of_Ages",
        duration=16.0,
        progression="Im VII bVI V",
        tracks={
            "Strings": "ambient_pad",
        },
        articulation="legato",
        automation=[
            _swell(5, 55, 16.0),
            _pan_drift(40, 84, 16.0, freq=0.15),
        ],
    )

    # ------------------------------------------------------------------
    # 2. The Kingdom  (32 beats = 8 chords)
    #    Lead melody enters. Bass provides tresillo foundation.
    #    Im bVI bIII VII Im IVm V Im : classic tragic arc, resolves to Im.
    # ------------------------------------------------------------------
    comp.add_section(
        name="The_Kingdom",
        duration=32.0,
        progression="Im bVI bIII VII Im IVm V Im",
        tracks={
            "Strings": "ambient_pad",
            "Lead":    "lead_melody",
            "Bass":    "followed_bass",
        },
        articulation="legato",
        automation=[
            _swell(50, 80, 32.0),
            _mod(10, 35, 32.0),
        ],
    )

    # ------------------------------------------------------------------
    # 3. Ancient Curse  (32 beats = 8 chords)
    #    Texture arp enters; choir thickens harmony.
    #    Im bVI bIII VII Im bII bIII V : bII (Bb) is the Phrygian sting.
    # ------------------------------------------------------------------
    comp.add_section(
        name="Ancient_Curse",
        duration=32.0,
        progression="Im bVI bIII VII Im bII bIII V",
        tracks={
            "Strings": "ambient_pad",
            "Lead":    "lead_melody",
            "Bass":    "followed_bass",
            "Texture": "fast_arp",
            "Choir":   "followed_chords",
        },
        articulation="sustain",
        automation=[
            _swell(75, 100, 32.0),
            _mod(30, 65, 32.0),
            _pan_drift(30, 90, 32.0, freq=0.3),
        ],
    )

    # ------------------------------------------------------------------
    # 4. Battle  (48 beats = 12 chords)
    #    Full arrangement. Walking bass for harmonic motion.
    #    Timpani gives the percussive backbone.
    #    Im V Im bII  Im IVm bVI V  Im bII bIII Im
    # ------------------------------------------------------------------
    comp.add_section(
        name="Battle",
        duration=48.0,
        progression="Im V Im bII Im IVm bVI V Im bII bIII Im",
        tracks={
            "Strings":  "ambient_pad",
            "Lead":     "lead_melody",
            "Bass":     "walking_bass",
            "Texture":  "fast_arp",
            "Choir":    "followed_chords",
            "Timpani":  "orch_timpani_bass",
        },
        articulation="marcato",
        automation=[
            _swell(95, 127, 48.0),
            ExpressionCurve.surge("modulation", 90, 48.0),
            _pan_drift(20, 107, 48.0, freq=0.45),
        ],
    )

    # ------------------------------------------------------------------
    # 5. Ruins  (32 beats = 8 chords)
    #    The battle is over. Strip back to Lead + Strings + Bass.
    #    Same progression as The Kingdom — cyclical, haunting return.
    # ------------------------------------------------------------------
    comp.add_section(
        name="Ruins",
        duration=32.0,
        progression="Im bVI bIII VII Im IVm V Im",
        tracks={
            "Strings": "ambient_pad",
            "Lead":    "lead_melody",
            "Bass":    "followed_bass",
        },
        articulation="legato",
        automation=[
            _swell(110, 70, 32.0),
            _mod(70, 25, 32.0),
        ],
    )

    # ------------------------------------------------------------------
    # 6. Into Darkness  (16 beats = 4 chords)
    #    Solo pad again — mirrors the opening, but now unresolved.
    #    Im VII bVI Im : returns to tonic without V→Im, no resolution.
    # ------------------------------------------------------------------
    comp.add_section(
        name="Into_Darkness",
        duration=16.0,
        progression="Im VII bVI Im",
        tracks={
            "Strings": "ambient_pad",
        },
        articulation="legato",
        automation=[
            _swell(65, 0, 16.0),
            _pan_drift(40, 84, 16.0, freq=0.1),
        ],
    )

    return comp


# ---------------------------------------------------------------------------
# Instrument mapping
# ---------------------------------------------------------------------------

INSTRUMENT_MAP = {
    "Strings":  48,   # String Ensemble 1
    "Lead":     68,   # Oboe  (warm, slightly dark)
    "Bass":     43,   # Contrabass
    "Texture":  11,   # Vibraphone (crystalline arpeggios)
    "Choir":    52,   # Choir Aahs
    "Timpani":  47,   # Timpani
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Generating: The Fallen Kingdom")
    print(f"  Scale : A Harmonic Minor | BPM: {BPM}")

    comp  = build_composition()
    director = MusicDirector(key=KEY)
    arrangement = director.render(comp)

    # Humanize — subtle, keeps the mechanical edge of dark fantasy
    humanizer = HumanizeModifier(timing_std=0.010, velocity_std=4.0)
    for track in arrangement.tracks:
        if track.notes:
            total_beats = max(n.start + n.duration for n in track.notes)
            ctx = ModifierContext(
                duration_beats=total_beats,
                chords=[],
                timeline=None,
                scale=KEY,
            )
            track.notes = humanizer.modify(track.notes, ctx)

    # Spectral + spatial balancing
    arrangement.tracks = OrchestralBalancer.apply_balancing(arrangement.tracks)

    # Assign MIDI programs
    for track in arrangement.tracks:
        if track.name in INSTRUMENT_MAP:
            track.program = INSTRUMENT_MAP[track.name]

    # Export
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "dark_legacy.mid"
    export_midi(arrangement.tracks, str(out_path), bpm=BPM)

    total_notes = sum(len(t.notes) for t in arrangement.tracks)
    duration_s  = 176.0 / BPM * 60
    print(f"  Tracks : {len(arrangement.tracks)}")
    print(f"  Notes  : {total_notes}")
    print(f"  Length : {duration_s:.0f}s ({duration_s/60:.1f} min)")
    print(f"  Output : {out_path.resolve()}")

    for t in arrangement.tracks:
        rh = t.notes[-1].start if t.notes else 0
        print(f"    [{t.name:8s}] prog={t.program:3d}  notes={len(t.notes):4d}")


if __name__ == "__main__":
    main()
