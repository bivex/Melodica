# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_downtempo_trap.py — "Downtempo Trap & Phonk" Album.

A chill, atmospheric trap album featuring deep sub-bass lines, crisp trap drums,
vocal chops, and smoky leads, all mixed and mastered via the core album pipeline.

Tracks:
  1. Midnight Static — 70 BPM — G Aeolian (Smoky Jazz Trumpet & Deep Sub)
  2. Neon Drift      — 76 BPM — C Aeolian (Chill Trap/Wave with High Arps & Choir Chops)
  3. Ghost Grid      — 65 BPM — E Aeolian (Dark Downtempo Phonk with Memphis Cowbells)
"""

import random
from pathlib import Path

from melodica.types import Scale, Mode, ChordLabel, NoteInfo, parse_progression
from melodica.generators import GeneratorParams
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.composer.album_pipeline import produce_track, Mood

# ------------------------------------------------------------------
# GM Programs mapping
# ------------------------------------------------------------------
ELECTRIC_PIANO = 4
TRUMPET = 56
SYNTH_LEAD = 80
CELLO = 42
CHOIR = 52
PAD_WARM = 89
BELLS = 14
SYNTH_BASS = 38
DRUMS = 0

random.seed(2026)
OUT = Path("output/album_downtempo_trap")
OUT.mkdir(parents=True, exist_ok=True)


# =====================================================================
# Track 1: Midnight Static — 70 BPM — G Aeolian
# =====================================================================
def produce_midnight_static():
    print("  1. Midnight Static [G Aeolian — 70 BPM]")
    key = Scale(root=7, mode=Mode.AEOLIAN)  # G Aeolian
    dur = 96.0  # 24 bars
    chords = parse_progression("i:4 VI:4 III:4 v:4 " * 6, key)

    # 1. Warm ambient pad (mid register to avoid bass clutter)
    pad = DarkPadGenerator(
        params=GeneratorParams(key_range_low=55, key_range_high=72),
        mode="minor_pad",
        chord_dur=8.0,
        velocity_level=0.30,
        register="mid"
    ).render(chords, key, dur)

    # 2. Electric Piano Chords (spread voicing, mid range)
    piano = AmbientPadGenerator(
        params=GeneratorParams(key_range_low=48, key_range_high=64),
        voicing="spread",
        overlap=1.2
    ).render(chords, key, dur)

    # 3. Clean sub synth bass (monophonic sine wave, strictly low-end)
    bass = SynthBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        waveform="sine",
        pattern="sub_kick"
    ).render(chords, key, dur)

    # 4. Smoky Jazz Trumpet (lead melody, enters staggered at bar 4)
    lead_gen = SoloMelodyGenerator(
        params=GeneratorParams(key_range_low=64, key_range_high=84),
        style="bebop_horn",
        vibrato_depth=0.5
    )
    lead = lead_gen.render(chords, key, dur)
    # Stagger: filter out notes before beat 16.0 (bar 4)
    lead = [n for n in lead if n.start >= 16.0]

    # 5. Minimal Trap Drums (enters staggered at bar 2)
    drums_gen = TrapDrumsGenerator(
        variant="minimal",
        hat_roll_density=0.35,
        kick_pattern="standard",
        sidechain_depth=0.5,
        ghost_snare_prob=0.3
    )
    drums = drums_gen.render(chords, key, dur)
    # Stagger: filter out notes before beat 8.0 (bar 2)
    drums = [n for n in drums if n.start >= 8.0]

    tracks = {
        "ambient_pad": pad,
        "electric_piano": piano,
        "synth_bass": bass,
        "lead_trumpet": lead,
        "drums": drums,
    }

    inst = {
        "ambient_pad": PAD_WARM,
        "electric_piano": ELECTRIC_PIANO,
        "synth_bass": SYNTH_BASS,
        "lead_trumpet": TRUMPET,
        "drums": DRUMS,
    }

    produce_track(
        tracks=tracks,
        bpm=70.0,
        instruments=inst,
        path=OUT / "01_Midnight_Static.mid",
        mood=Mood.AMBIENT,
        key=key,
    )


# =====================================================================
# Track 2: Neon Drift — 76 BPM — C Aeolian
# =====================================================================
def produce_neon_drift():
    print("  2. Neon Drift [C Aeolian — 76 BPM]")
    key = Scale(root=0, mode=Mode.AEOLIAN)  # C Aeolian
    dur = 96.0  # 24 bars
    chords = parse_progression("i:4 v:4 VI:4 VII:4 " * 6, key)

    # 1. Warm bass (sustained Reese bass, sine-saw hybrid style in low end)
    bass = SynthBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=40),
        waveform="sine",
        pattern="reese"
    ).render(chords, key, dur)

    # 2. Vocal chops (choir pad playing airy vocal-like melodies, mid register)
    vocals = AmbientPadGenerator(
        params=GeneratorParams(key_range_low=60, key_range_high=72),
        voicing="spread",
        overlap=1.0
    ).render(chords, key, dur)

    # 3. High arpeggiator synth (staggered entrance, starts at bar 4)
    arp = ArpeggiatorGenerator(
        params=GeneratorParams(key_range_low=72, key_range_high=96),
        pattern="up_down",
        note_duration=0.25
    ).render(chords, key, dur)
    arp = [n for n in arp if n.start >= 16.0]

    # 4. Melodic trap drums (complex rolls, syncopated kick, starts at bar 2)
    drums_gen = TrapDrumsGenerator(
        variant="melodic",
        hat_roll_density=0.75,
        kick_pattern="syncopated",
        sidechain_depth=0.7,
        ghost_snare_prob=0.35
    )
    drums = drums_gen.render(chords, key, dur)
    drums = [n for n in drums if n.start >= 8.0]

    tracks = {
        "synth_bass": bass,
        "vocal_chops": vocals,
        "arp_synth": arp,
        "drums": drums,
    }

    inst = {
        "synth_bass": SYNTH_BASS,
        "vocal_chops": CHOIR,
        "arp_synth": SYNTH_LEAD,
        "drums": DRUMS,
    }

    produce_track(
        tracks=tracks,
        bpm=76.0,
        instruments=inst,
        path=OUT / "02_Neon_Drift.mid",
        mood=Mood.CINEMATIC,
        key=key,
    )


# =====================================================================
# Track 3: Ghost Grid — 65 BPM — E Aeolian
# =====================================================================
def produce_ghost_grid():
    print("  3. Ghost Grid [E Aeolian — 65 BPM]")
    key = Scale(root=4, mode=Mode.AEOLIAN)  # E Aeolian
    dur = 96.0  # 24 bars
    chords = parse_progression("i:4 VI:4 VII:4 i:4 " * 6, key)

    # 1. Wobble sub synth bass (monophonic, low register)
    bass = SynthBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        waveform="sine",
        pattern="wobble"
    ).render(chords, key, dur)

    # 2. Dark pad (phrygian / suspension texture, mid register)
    pad = DarkPadGenerator(
        params=GeneratorParams(key_range_low=53, key_range_high=68),
        mode="phrygian_pad",
        chord_dur=8.0,
        velocity_level=0.35,
        register="mid"
    ).render(chords, key, dur)

    # 3. Phonk cowbells (arpeggiator on bells, high-mid register)
    cowbells = ArpeggiatorGenerator(
        params=GeneratorParams(key_range_low=72, key_range_high=84),
        pattern="up",
        note_duration=0.5
    ).render(chords, key, dur)
    # Stagger: enters at beat 16.0 (bar 4)
    cowbells = [n for n in cowbells if n.start >= 16.0]

    # 4. Standard trap drums (syncopated, heavy sidechain, enters at bar 2)
    drums_gen = TrapDrumsGenerator(
        variant="standard",
        hat_roll_density=0.45,
        kick_pattern="syncopated",
        sidechain_depth=0.8,
        ghost_snare_prob=0.3
    )
    drums = drums_gen.render(chords, key, dur)
    drums = [n for n in drums if n.start >= 8.0]

    tracks = {
        "wobble_bass": bass,
        "dark_pad": pad,
        "phonk_cowbells": cowbells,
        "drums": drums,
    }

    inst = {
        "wobble_bass": SYNTH_BASS,
        "dark_pad": PAD_WARM,
        "phonk_cowbells": BELLS,
        "drums": DRUMS,
    }

    produce_track(
        tracks=tracks,
        bpm=65.0,
        instruments=inst,
        path=OUT / "03_Ghost_Grid.mid",
        mood=Mood.EXPERIMENTAL,
        key=key,
    )


# ------------------------------------------------------------------
# Main production script
# ------------------------------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("   DOWNTEMPO TRAP & PHONK — Album Production")
    print("   Lush Atmospheres, Crisp Beats & Warm Subs")
    print("=" * 60 + "\n")

    produce_midnight_static()
    produce_neon_drift()
    produce_ghost_grid()

    print("\n" + "=" * 60)
    print("   PRODUCTION COMPLETE: DOWNTEMPO TRAP")
    print(f"   MIDI output saved to: {OUT.absolute()}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
