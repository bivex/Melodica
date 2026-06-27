# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/electronic/album_melodic_downtempo.py — "Pulse & Atmosphere" Melodic Downtempo Album.

An album combining melodic elements, slow down-tempo breakbeats, drum-driven pacing,
atmospheric textures, deep sub-basslines, evolving synth pads, minimal percussion,
emotional progressions, and cinematic breaks.

All tracks are optimized to satisfy Form Validator and MIDI Doctor constraints (register balance,
dynamics spread, peak density, and voice crossing).
"""

import random
import sys
from pathlib import Path

from melodica.types import Scale, Mode, ChordLabel, NoteInfo, parse_progression
from melodica.generators import GeneratorParams
from melodica.generators.breakbeat import BreakbeatGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.tension import TensionGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.composer.album_pipeline import produce_track, Mood

# GM Programs mapping
PIANO = 0
SYNTH_BASS = 38
DARK_PAD = 88
SYNTH_LEAD = 80
POLYSYNTH = 90
EFFECTS = 96
DRUMS = 0
GLOCKENSPIEL = 9
HARP = 46

random.seed(2026)
OUT = Path("output/album_melodic_downtempo")
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# Diagnostic & Post-processing Helpers
# ------------------------------------------------------------------
def scale_velocity_spread(notes: list[NoteInfo], target_min=50, target_max=110) -> list[NoteInfo]:
    """Ensure dynamic expression by scaling velocity to fit a wider range."""
    if not notes:
        return notes
    vels = [n.velocity for n in notes]
    min_v, max_v = min(vels), max(vels)
    if max_v == min_v:
        for n in notes:
            n.velocity = target_max
        return notes
    for n in notes:
        scaled = target_min + (n.velocity - min_v) / (max_v - min_v) * (target_max - target_min)
        n.velocity = int(max(1, min(127, scaled)))
    return notes


def resolve_register_crossing(bass: list[NoteInfo], pads: list[NoteInfo], leads: list[NoteInfo]):
    """Force clean register separation to prevent voice crossings."""
    # Bass should stay strictly in the low registers
    for n in bass:
        if n.pitch > 48:
            n.pitch -= 12
        if n.pitch > 48:  # Still too high
            n.pitch -= 12

    # Pads should stay in the low-mid register
    for n in pads:
        if n.pitch < 36:
            n.pitch += 12
        elif n.pitch > 60:
            n.pitch -= 12

    # Leads should stay strictly in the mid-high registers
    for n in leads:
        if n.pitch < 64:
            n.pitch += 12
        if n.pitch < 64:
            n.pitch += 12


# =====================================================================
# Track 1: Velvet Echoes — 88 BPM — C Minor
# =====================================================================
def produce_velvet_echoes():
    print("  1. Velvet Echoes [C Minor — 88 BPM]")
    key = Scale(root=0, mode=Mode.AEOLIAN)  # C Aeolian
    dur = 96.0  # 24 bars
    chords = parse_progression("i:4 VI:4 III:4 VII:4 iv:4 i:4 VI:4 V7:4 " * 3, key)

    # Slow, syncopated funky breakbeat (silent in intro & outro)
    raw_drums = BreakbeatGenerator(
        variant="funky", chop_probability=0.15, ghost_notes=True
    ).render(chords, key, dur)
    drums = [n for n in raw_drums if 16.0 <= n.start < 80.0]

    # Low, warm sub synth bass hits
    bass = SynthBassGenerator(
        waveform="sine", pattern="sub_kick"
    ).render(chords, key, dur)

    # Soft ambient background pads
    pad = DarkPadGenerator(
        mode="minor_pad", register="low", velocity_level=0.30, chord_dur=8.0
    ).render(chords, key, dur)

    # High-register shimmering glockenspiel to populate high register
    glock = GlockenspielGenerator(
        params=GeneratorParams(density=0.35)
    ).render(chords, key, dur)
    # Ensure glock is high register
    for n in glock:
        if n.pitch < 76:
            n.pitch += 12
        if n.pitch < 76:
            n.pitch += 12

    # Eerie, high-register major 7th tension layer for atmosphere
    tension = TensionGenerator(
        mode="major7_tension", note_duration=4.0, velocity_level=0.25, register="high", density=0.4
    ).render(chords, key, dur)
    for n in tension:
        if n.pitch < 72:
            n.pitch += 12

    # Emotional, modal ambient solo synth lead melody (silent in outro)
    raw_lead = SoloMelodyGenerator(
        params=GeneratorParams(key_range_low=64, key_range_high=88),
        style="modal_ambient",
        vibrato_depth=0.5,
    ).render(chords, key, dur)
    lead = [n for n in raw_lead if n.start < 80.0]

    # Sound FX riser for transitional build-ups (silent in outro)
    raw_riser = FXRiserGenerator(
        params=GeneratorParams(density=0.40),
        riser_type="synth",
        length_beats=8.0,
        pitch_curve="exponential",
        peak_velocity=90,
    ).render(chords, key, dur)
    riser = [n for n in raw_riser if n.start < 80.0]

    # FX impact at boundaries
    impact = FXImpactGenerator(
        params=GeneratorParams(density=0.25),
        impact_type="boom",
        tail_length=8.0,
        pitch_drop=12,
    ).render(chords, key, dur)

    # Apply dynamic fixes
    scale_velocity_spread(drums, 50, 110)
    scale_velocity_spread(lead, 60, 100)
    scale_velocity_spread(glock, 45, 95)
    resolve_register_crossing(bass, pad, lead)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "dark_pad": pad,
        "glockenspiel": glock,
        "tension_fx": tension,
        "lead_synth": lead,
        "fx_riser": riser,
        "fx_impact": impact,
    }

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "glockenspiel": GLOCKENSPIEL,
        "tension_fx": POLYSYNTH,
        "lead_synth": SYNTH_LEAD,
        "fx_riser": EFFECTS,
        "fx_impact": EFFECTS,
    }

    produce_track(
        tracks=tracks,
        bpm=88.0,
        instruments=inst,
        path=OUT / "01_Velvet_Echoes.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=False,
    )


# =====================================================================
# Track 2: Lost in the Static — 94 BPM — F# Dorian
# =====================================================================
def produce_lost_in_the_static():
    print("  2. Lost in the Static [F# Dorian — 94 BPM]")
    key = Scale(root=6, mode=Mode.DORIAN)  # F# Dorian
    dur = 96.0  # 24 bars
    chords = parse_progression("i:4 IV:4 i7:4 v7:4 bVII:4 i:4 VI:4 VII:4 " * 3, key)

    # Subtle, glitchy minimal breakbeat rhythm (silent in intro & outro)
    raw_drums = BreakbeatGenerator(
        variant="think", chop_probability=0.20, ghost_notes=True
    ).render(chords, key, dur)
    drums = [n for n in raw_drums if 16.0 <= n.start < 80.0]

    # Sliding, evolving Reese bassline in the low-end
    bass = SynthBassGenerator(
        waveform="saw", pattern="reese", slide_probability=0.25, octave_variation=0.1
    ).render(chords, key, dur)

    # Dark Phrygian-like tension pad
    pad = DarkPadGenerator(
        mode="phrygian_pad", register="low", velocity_level=0.25, chord_dur=4.0
    ).render(chords, key, dur)

    # Blade runner atmospheric textures
    scifi = SciFiUnderscoreGenerator(
        variant="blade_runner", pad_density=0.5, arp_speed=0.5, include_bass_synth=False
    ).render(chords, key, dur)

    # High shimmer harp to populate high register
    harp = HarpGenerator(
        params=GeneratorParams(density=0.30)
    ).render(chords, key, dur)
    for n in harp:
        if n.pitch < 74:
            n.pitch += 12
        if n.pitch < 74:
            n.pitch += 12

    # Soft, emotional strings-style solo lead melody (silent in outro)
    raw_lead = SoloMelodyGenerator(
        params=GeneratorParams(key_range_low=64, key_range_high=86),
        style="cinematic_strings",
        vibrato_depth=0.6,
    ).render(chords, key, dur)
    lead = [n for n in raw_lead if n.start < 80.0]

    # Arpeggio pattern providing melodic movement (silent in intro/outro)
    raw_arp = ArpeggiatorGenerator(
        params=GeneratorParams(density=0.50),
        pattern="up_down",
        note_duration=0.5,
    ).render(chords, key, dur)
    arp = [n for n in raw_arp if 16.0 <= n.start < 80.0]
    for n in arp:
        if n.pitch < 60:
            n.pitch += 12

    # FX riser & impact for breaks (silent in outro)
    raw_riser = FXRiserGenerator(
        params=GeneratorParams(density=0.35),
        riser_type="synth",
        length_beats=4.0,
        pitch_curve="linear",
        peak_velocity=85,
    ).render(chords, key, dur)
    riser = [n for n in raw_riser if n.start < 80.0]

    impact = FXImpactGenerator(
        params=GeneratorParams(density=0.20),
        impact_type="boom",
        tail_length=6.0,
        pitch_drop=15,
    ).render(chords, key, dur)

    # Apply dynamic fixes & register separation
    scale_velocity_spread(drums, 50, 110)
    scale_velocity_spread(arp, 55, 100)
    scale_velocity_spread(lead, 60, 105)
    scale_velocity_spread(harp, 45, 95)
    resolve_register_crossing(bass, pad, lead)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "dark_pad": pad,
        "scifi_texture": scifi,
        "harp_shimmer": harp,
        "lead_strings": lead,
        "arpeggio": arp,
        "fx_riser": riser,
        "fx_impact": impact,
    }

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "scifi_texture": POLYSYNTH,
        "harp_shimmer": HARP,
        "lead_strings": SYNTH_LEAD,
        "arpeggio": POLYSYNTH,
        "fx_riser": EFFECTS,
        "fx_impact": EFFECTS,
    }

    produce_track(
        tracks=tracks,
        bpm=94.0,
        instruments=inst,
        path=OUT / "02_Lost_in_the_Static.mid",
        mood=Mood.INTIMATE,
        key=key,
        verbose=False,
    )


# =====================================================================
# Track 3: Cinematic Drift — 82 BPM — G Minor
# =====================================================================
def produce_cinematic_drift():
    print("  3. Cinematic Drift [G Minor — 82 BPM]")
    key = Scale(root=7, mode=Mode.AEOLIAN)  # G Aeolian
    dur = 128.0  # 32 bars (longer drift)
    chords = parse_progression("i:4 v:4 VI:4 III:4 iv:4 VII:4 i:4 i:4 " * 4, key)

    # Complex, glitchy IDM breakbeat (silent in intro & outro)
    raw_drums = BreakbeatGenerator(
        variant="idm", chop_probability=0.30, ghost_notes=True
    ).render(chords, key, dur)
    drums = [n for n in raw_drums if 16.0 <= n.start < 112.0]

    # Deep, plucked bassline for precision and drive
    bass = SynthBassGenerator(
        waveform="sine", pattern="plucked"
    ).render(chords, key, dur)

    # Evolving, warm dark pads
    pad = DarkPadGenerator(
        mode="minor_pad", register="low", velocity_level=0.35, chord_dur=8.0
    ).render(chords, key, dur)

    # Semitone clusters creating intense cinematic friction in the break (silent in outro)
    raw_tension = TensionGenerator(
        mode="semitone_cluster", note_duration=2.0, velocity_level=0.35, register="mid", density=0.5
    ).render(chords, key, dur)
    tension = [n for n in raw_tension if n.start < 112.0]

    # Slow, cosmic sci-fi underscore layers
    scifi = SciFiUnderscoreGenerator(
        variant="space", pad_density=0.6, include_bass_synth=False
    ).render(chords, key, dur)

    # Glockenspiel high register shimmer
    glock = GlockenspielGenerator(
        params=GeneratorParams(density=0.30)
    ).render(chords, key, dur)
    for n in glock:
        if n.pitch < 76:
            n.pitch += 12
        if n.pitch < 76:
            n.pitch += 12

    # Expressive space synth lead solo melody (silent in outro)
    raw_lead = SoloMelodyGenerator(
        params=GeneratorParams(key_range_low=64, key_range_high=88),
        style="space_synth",
        vibrato_depth=0.5,
    ).render(chords, key, dur)
    lead = [n for n in raw_lead if n.start < 112.0]

    # Larger FX transitions for deep cinematic drops (silent in outro)
    raw_riser = FXRiserGenerator(
        params=GeneratorParams(density=0.45),
        riser_type="synth",
        length_beats=12.0,
        pitch_curve="exponential",
        peak_velocity=95,
    ).render(chords, key, dur)
    riser = [n for n in raw_riser if n.start < 112.0]

    impact = FXImpactGenerator(
        params=GeneratorParams(density=0.30),
        impact_type="boom",
        tail_length=10.0,
        pitch_drop=18,
    ).render(chords, key, dur)

    # Apply dynamic fixes & register separation
    scale_velocity_spread(drums, 50, 110)
    scale_velocity_spread(lead, 60, 105)
    scale_velocity_spread(glock, 45, 95)
    resolve_register_crossing(bass, pad, lead)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "dark_pad": pad,
        "tension_rub": tension,
        "scifi_drone": scifi,
        "glock_shimmer": glock,
        "lead_synth": lead,
        "fx_riser": riser,
        "fx_impact": impact,
    }

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "dark_pad": DARK_PAD,
        "tension_rub": POLYSYNTH,
        "scifi_drone": POLYSYNTH,
        "glock_shimmer": GLOCKENSPIEL,
        "lead_synth": SYNTH_LEAD,
        "fx_riser": EFFECTS,
        "fx_impact": EFFECTS,
    }

    produce_track(
        tracks=tracks,
        bpm=82.0,
        instruments=inst,
        path=OUT / "03_Cinematic_Drift.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=False,
    )


def generate_album():
    print("\n" + "=" * 80)
    print("        P U L S E   &   A T M O S P H E R E")
    print("        Melodic Downtempo & Atmospheric Breakbeat Album")
    print("=" * 80)

    produce_velvet_echoes()
    produce_lost_in_the_static()
    produce_cinematic_drift()

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: PULSE & ATMOSPHERE")
    print(f"  Output folder: {OUT.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    generate_album()
