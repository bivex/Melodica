# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/debug_pad_notes.py — Trace why AmbientPadGenerator loses notes.

Step-by-step isolation: render directly → render via IdeaTool (1 track) →
render via IdeaTool (full 10 tracks). Pinpoints the exact stage where notes vanish.
"""

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators.ambient import AmbientPadGenerator
from melodica.render_context import RenderContext
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, structure_to_schedule,
)


def sep(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def show_notes(notes, max_show=5):
    if not notes:
        print("  (empty)")
        return
    print(f"  Count: {len(notes)}")
    for n in notes[:max_show]:
        print(f"    pitch={n.pitch} vel={n.velocity} start={n.start:.2f} dur={n.duration:.2f}")
    if len(notes) > max_show:
        print(f"    ... +{len(notes) - max_show} more")


# ── Setup ──────────────────────────────────────────────────────────────────

scale = Scale(2, Mode.NATURAL_MINOR)
gen = AmbientPadGenerator(voicing="spread")

# ── Step 1: Direct render with minimal chords ─────────────────────────────

sep("STEP 1 — Direct render (4 beats, 1 chord)")

chords = [ChordLabel(root=2, quality=Quality.MINOR, start=0.0, duration=4.0)]
notes = gen.render(chords, scale, 4.0, RenderContext())
print(f"  Chords: {[f'root={c.root} q={c.quality} start={c.start} dur={c.duration}' for c in chords]}")
show_notes(notes)

# ── Step 2: Direct render with no chords ───────────────────────────────────

sep("STEP 2 — Direct render (empty chords)")

notes_empty = gen.render([], scale, 4.0, RenderContext())
show_notes(notes_empty)

# ── Step 3: Direct render with octave_shift=-1 ────────────────────────────

sep("STEP 3 — Direct render + manual octave shift (-1)")

shifted = [
    NoteInfo(pitch=n.pitch - 12, start=n.start, duration=n.duration,
             velocity=n.velocity, articulation=n.articulation, expression=dict(n.expression))
    for n in notes
]
show_notes(shifted)

# ── Step 4: Direct render, inspect voicing internals ──────────────────────

sep("STEP 4 — Trace voicing computation")

from melodica.utils import chord_pitches_spread, chord_pitches_open, snap_to_scale

for voicing_fn, name in [(chord_pitches_spread, "spread"), (chord_pitches_open, "open")]:
    if name == "spread":
        raw = chord_pitches_spread(chords[0], bass_midi=48)
    else:
        raw = chord_pitches_open(chords[0], bass_midi=36)
    print(f"\n  Voicing ({name}) raw pitches: {raw}")

    low, high = 48, 84
    filtered = [snap_to_scale(p, scale) for p in raw if low <= p <= high]
    print(f"  After range filter [{low},{high}]: {filtered}")

    shifted_down = [p - 12 for p in filtered]
    filtered2 = [p for p in shifted_down if 0 <= p <= 127]
    print(f"  After octave shift -1 + clamp: {filtered2}")

# ── Step 5: IdeaTool with 1 track only ────────────────────────────────────

sep("STEP 5 — IdeaTool (1 track: Ambient_Pad only)")

tracks_1 = [
    TrackConfig(name="Ambient_Pad", generator=AmbientPadGenerator(voicing="spread"),
                instrument="dark_pad", density=0.4, octave_shift=-1),
]
parts_1 = [
    IdeaPart(name="Test", bars=8, scale=scale, tempo=80,
             progression_type="coupled_hmm",
             track_phrase_schedules={
                 "Ambient_Pad": structure_to_schedule("A", 8),
             }),
]
cfg_1 = IdeaToolConfig(style="hip_hop_trap", parts=parts_1, tracks=tracks_1,
                        use_voice_leading=False, use_harmonic_verifier=False)
res_1 = IdeaTool(cfg_1).generate()
pad_1 = res_1.get("Ambient_Pad", [])
chords_1 = res_1.get("_chords", [])
print(f"  Chords generated: {len(chords_1)}")
for c in chords_1[:4]:
    print(f"    root={c.root} quality={c.quality} start={c.start:.1f} dur={c.duration:.1f}")
print(f"  Ambient_Pad notes: {len(pad_1)}")
show_notes(pad_1)

# ── Step 6: IdeaTool with 1 track, check resolved parts ──────────────────

sep("STEP 6 — Check _get_resolved_parts preserves track_phrase_schedules")

tool = IdeaTool(cfg_1)
resolved = tool._get_resolved_parts()
for p in resolved:
    scheds = p.track_phrase_schedules
    has_it = scheds is not None and "Ambient_Pad" in scheds if scheds else False
    print(f"  Part '{p.name}': track_phrase_schedules = {list(scheds.keys()) if scheds else None}")
    print(f"    Has Ambient_Pad schedule: {has_it}")

# ── Step 7: IdeaTool with 2 tracks ────────────────────────────────────────

sep("STEP 7 — IdeaTool (2 tracks: Ambient_Pad + Sub_808)")

from melodica.generators.bass_808_sliding import Bass808SlidingGenerator

tracks_2 = [
    TrackConfig(name="Ambient_Pad", generator=AmbientPadGenerator(voicing="spread"),
                instrument="dark_pad", density=0.4, octave_shift=-1),
    TrackConfig(name="Sub_808", generator=Bass808SlidingGenerator(pattern="trap_basic"),
                instrument="synth_bass", density=0.6, octave_shift=-2),
]
parts_2 = [
    IdeaPart(name="Test", bars=8, scale=scale, tempo=80,
             progression_type="coupled_hmm",
             track_phrase_schedules={
                 "Ambient_Pad": structure_to_schedule("A", 8),
                 "Sub_808": structure_to_schedule("A", 8),
             }),
]
cfg_2 = IdeaToolConfig(style="hip_hop_trap", parts=parts_2, tracks=tracks_2,
                        use_voice_leading=False, use_harmonic_verifier=False)
res_2 = IdeaTool(cfg_2).generate()
print(f"  Ambient_Pad: {len(res_2.get('Ambient_Pad', []))} notes")
print(f"  Sub_808: {len(res_2.get('Sub_808', []))} notes")

# ── Step 8: Full 10-track setup ───────────────────────────────────────────

sep("STEP 8 — IdeaTool (full 10 tracks)")

from scripts.demo_beat_arrangement import _build_tracks, _build_parts

tracks_full = _build_tracks()
parts_full = _build_parts(scale)

# Swap NebulaGenerator back to AmbientPadGenerator for this test
for t in tracks_full:
    if t.name == "Ambient_Pad":
        t.generator = AmbientPadGenerator(voicing="spread")

cfg_full = IdeaToolConfig(style="hip_hop_trap", parts=parts_full, tracks=tracks_full,
                           use_voice_leading=True, use_harmonic_verifier=False)
res_full = IdeaTool(cfg_full).generate()

print(f"  Ambient_Pad: {len(res_full.get('Ambient_Pad', []))} notes")
for name in ["Sub_808", "Lead_Synth", "Trap_Drums", "Counter_Lead"]:
    print(f"  {name}: {len(res_full.get(name, []))} notes")

# ── Step 9: Check apply_texture_control ───────────────────────────────────

sep("STEP 9 — Check if apply_texture_control filters AmbientPadGenerator")

from melodica._postprocess import apply_texture_control
from melodica.idea_tool import TensionCurve

pad_before = list(res_full.get("Ambient_Pad", []))
print(f"  Before texture control: {len(pad_before)} notes")

tc = TensionCurve(total_beats=336, curve_type="arc")
apply_texture_control(res_full, tracks_full, tc, use_texture_control=True)

pad_after = res_full.get("Ambient_Pad", [])
print(f"  After texture control: {len(pad_after)} notes")

# Check is_chord_track classification
from melodica._postprocess import apply_texture_control as _atc
import melodica._postprocess as _pp

print("\n  is_chord_track classification:")
for t in tracks_full:
    is_chord = t.generator_type in ("chord", "strum", "arpeggiator")
    is_ambient = isinstance(t.generator, AmbientPadGenerator)
    if is_chord or is_ambient:
        print(f"    {t.name}: chord={is_chord} ambient={is_ambient} → FILTERED by texture control")
    else:
        print(f"    {t.name}: chord={is_chord} ambient={is_ambient} → skipped")

# ── Step 10: Full pipeline with harmonic verifier ─────────────────────────

sep("STEP 10 — Full pipeline WITH harmonic verifier")

cfg_hv = IdeaToolConfig(style="hip_hop_trap", parts=parts_full, tracks=tracks_full,
                         use_voice_leading=True, use_harmonic_verifier=True)
res_hv = IdeaTool(cfg_hv).generate()
print(f"  Ambient_Pad (with verifier): {len(res_hv.get('Ambient_Pad', []))} notes")

# ── Summary ───────────────────────────────────────────────────────────────

sep("SUMMARY")
print(f"""
  Step 1 (direct render):        {len(notes)} notes  ← baseline
  Step 2 (empty chords):         {len(notes_empty)} notes  ← edge case
  Step 5 (1-track IdeaTool):     {len(pad_1)} notes
  Step 7 (2-track IdeaTool):     {len(res_2.get('Ambient_Pad', []))} notes
  Step 8 (10-track, no verify):  {len(res_full.get('Ambient_Pad', []))} notes
  Step 10 (10-track, full):      {len(res_hv.get('Ambient_Pad', []))} notes
""")
