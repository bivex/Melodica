# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_sakinfo.py — "Sakinfo" Concept Album.

Genre: Neo-classical + Ambient + Dark Electronic + Ethnic textures
Shared Theme/Leitmotif: Dm – Bb – F – C (Chords) | D → F → E → C (4-note DNA)
Narrative: Cold information → Memory → Digital noise → Human inside the system.
"""

import random
from pathlib import Path

from melodica.types import Scale, Mode, ChordLabel, NoteInfo, parse_progression
from melodica.generators import GeneratorParams
from melodica.composer import Motif, LeitmotifRegistry
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.breakbeat import BreakbeatGenerator
from melodica.composer.antiphony import AntiphonyBuilder, InstrumentGroup
from melodica.composer.album_pipeline import produce_track, Mood

# ------------------------------------------------------------------
# GM Programs
# ------------------------------------------------------------------
PIANO = 0           # Felt piano / Acoustic lead
CELLO = 42          # Low cello ostinato / counterpoint
VIOLA = 41          # Viola textures
VIOLIN = 40         # Aggressive / sharp strings
STRINGS = 48        # Strings ensemble (glue)
BRASS = 61          # Brass stabs / section
CHOIR = 52          # Choir Aahs (vocal chops)
MARIMBA = 12        # Memory grid polyrhythm
BELLS = 14          # Tubular bells / distant bells
SYNTH_BASS = 38     # Analog / Reese bass
SYNTH_LEAD = 80     # Pulse / Lead synth
FX_SOUND = 97       # Granular noise / texture
DRUMS = 0           # Drum kit channel
PAD_BOWED = 92      # Bowed pad
PAD_WARM = 89       # Warm pad


random.seed(2026)
OUT = Path("output/album_sakinfo")
OUT.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Leitmotif definition — The Genetic DNA of Sakinfo
# ------------------------------------------------------------------
# 4-note motif: D4 (62) -> F4 (65) -> E4 (64) -> C4 (60)
sakinfo_theme = Motif.from_notes([
    NoteInfo(pitch=62, start=0.0, duration=1.0, velocity=75),
    NoteInfo(pitch=65, start=1.0, duration=1.0, velocity=70),
    NoteInfo(pitch=64, start=2.0, duration=1.0, velocity=70),
    NoteInfo(pitch=60, start=3.0, duration=1.0, velocity=75),
])

registry = LeitmotifRegistry()
registry.register("sakinfo", sakinfo_theme, instrument=PIANO, velocity=70, register=1)

# Evolve the theme into different variations
registry.evolve("sakinfo", "inverse", invert=True)
registry.evolve("sakinfo", "retrograde", retrograde=True)
registry.evolve("sakinfo", "augmented_x4", augment_factor=4.0)
registry.evolve("sakinfo", "fragmented", fragment_end=2.0)
registry.evolve("sakinfo", "speedy", diminish_factor=2.0)
registry.evolve("sakinfo", "triumphant_major", transpose=3)  # Shift relative minor to relative major shadow


# =====================================================================
# Track 1: Signal Birth — 72 BPM — D Aeolian (Intro)
# =====================================================================
def produce_signal_birth():
    print("  1. Signal Birth [D Aeolian — 72 BPM]")
    key = Scale(root=2, mode=Mode.AEOLIAN)  # D Aeolian
    dur = 64.0  # 16 bars
    chords = parse_progression("i:4 VI:4 III:4 VII:4 " * 4, key)

    # 1. Drone Pad (very low registers, avoiding mid frequencies)
    drone = DroneGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=38),
        velocity=40
    ).render(chords, key, dur)

    # 1. Drone Pad (very low registers, avoiding mid frequencies)
    drone = DroneGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=38),
        velocity=40
    ).render(chords, key, dur)

    # 2. Granular Noise / Atmosphere
    granular = DarkPadGenerator(
        params=GeneratorParams(key_range_low=20, key_range_high=32),
        mode="tritone_drone", register="low", velocity_level=0.30, chord_dur=8.0
    ).render(chords, key, dur)

    # 3. Lead Piano: Single felt piano playing the direct theme (staggered entrance)
    lead = []
    for bar in range(4, 16, 4):  # starts at beat 16.0
        lead.extend(registry.render("sakinfo", offset=bar * 4.0, transpose=12))

    # 4. Support Cello: countermelody through contrary motion (staggered entrance)
    cello_gen = CountermelodyGenerator(
        primary_melody=lead,
        motion_preference="contrary",
        dissonance_on_weak=True
    )
    cello_gen.params.key_range_low = 40
    cello_gen.params.key_range_high = 55
    cello = cello_gen.render(chords, key, dur)

    tracks = {
        "drone_pad": drone,
        "granular_noise": granular,
        "lead_piano": lead,
        "cello_ostinato": cello,
    }

    inst = {
        "drone_pad": PAD_BOWED,
        "granular_noise": FX_SOUND,
        "lead_piano": PIANO,
        "cello_ostinato": CELLO,
    }

    produce_track(
        tracks=tracks,
        bpm=72.0,
        instruments=inst,
        path=OUT / "01_Signal_Birth.mid",
        mood=Mood.AMBIENT,
        key=key,
    )


# =====================================================================
# Track 2: Static Veins — 88 BPM — D Aeolian
# =====================================================================
def produce_static_veins():
    print("  2. Static Veins [D Aeolian — 88 BPM]")
    key = Scale(root=2, mode=Mode.AEOLIAN)
    dur = 64.0
    chords = parse_progression("i:4 VI:4 III:4 VII:4 " * 4, key)

    # 1. Analog Bass: repeating the speedy (diminished) leitmotif in the low register
    bass = []
    for bar in range(16):
        bass.extend(registry.render("sakinfo", variant="speedy", offset=bar * 4.0, transpose=-24))

    # 2. Muted drums (minimal electronic drum machine)
    drums = ElectronicDrumsGenerator(
        params=GeneratorParams(),
        kit="cr78",
        pattern="minimal",
        ghost_snare_prob=0.3
    ).render(chords, key, dur)

    # 3. Pulse Synth & Viola Textures: Call-and-response dialog via AntiphonyBuilder
    pulse_raw = SoloMelodyGenerator(
        params=GeneratorParams(key_range_low=60, key_range_high=76),
        style="modal_ambient"
    ).render(chords, key, dur)

    viola_raw = CountermelodyGenerator(
        primary_melody=pulse_raw,
        motion_preference="oblique"  # Keep viola holding notes while pulse moves
    ).render(chords, key, dur)

    antiphony = AntiphonyBuilder(
        call_group=InstrumentGroup.KEYS,       # Pulse synth (GM 80 mapped temporarily to keys range)
        response_group=InstrumentGroup.STRINGS, # Viola (GM 41)
        phrase_bars=2.0,
        track_group_map={
            "pulse_synth": InstrumentGroup.KEYS,
            "viola_textures": InstrumentGroup.STRINGS
        }
    )

    raw_tracks = {
        "pulse_synth": pulse_raw,
        "viola_textures": viola_raw
    }
    coordinated = antiphony.apply(raw_tracks)

    tracks = {
        "analog_bass": bass,
        "drums": drums,
        "pulse_synth": coordinated["pulse_synth"],
        "viola_textures": coordinated["viola_textures"],
    }

    inst = {
        "analog_bass": SYNTH_BASS,
        "drums": DRUMS,
        "pulse_synth": SYNTH_LEAD,
        "viola_textures": VIOLA,
    }

    produce_track(
        tracks=tracks,
        bpm=88.0,
        instruments=inst,
        path=OUT / "02_Static_Veins.mid",
        mood=Mood.INTIMATE,
        key=key,
    )


# =====================================================================
# Track 3: Archive of Skin — 76 BPM — D Aeolian
# =====================================================================
def produce_archive_of_skin():
    print("  3. Archive of Skin [D Aeolian — 76 BPM]")
    key = Scale(root=2, mode=Mode.AEOLIAN)
    dur = 64.0
    # Longer chords for a slower, more intimate harmonic movement
    chords = parse_progression("i:8 VI:8 III:8 VII:8 " * 2, key)

    # 1. Felt Piano: Theme in augment mode (stretched 4 times to ring out slowly)
    piano = []
    piano.extend(registry.render("sakinfo", variant="augmented_x4", offset=0.0))
    piano.extend(registry.render("sakinfo", variant="augmented_x4", offset=16.0, transpose=-5))
    piano.extend(registry.render("sakinfo", variant="augmented_x4", offset=32.0, transpose=3))
    piano.extend(registry.render("sakinfo", variant="augmented_x4", offset=48.0))

    # 2. Soft Strings (AmbientPad) in a lower octave, providing emotional glue
    strings = AmbientPadGenerator(
        params=GeneratorParams(key_range_low=48, key_range_high=64),
        voicing="spread",
        overlap=1.5
    ).render(chords, key, dur)

    # 3. Reverse Bells: Slow, atmospheric bell hits (using tension scatter but low density)
    bells = DroneGenerator(
        params=GeneratorParams(key_range_low=60, key_range_high=72),
        velocity=35
    ).render(chords, key, dur)

    tracks = {
        "felt_piano": piano,
        "soft_strings": strings,
        "reverse_bells": bells,
    }

    inst = {
        "felt_piano": PIANO,
        "soft_strings": STRINGS,
        "reverse_bells": BELLS,
    }

    produce_track(
        tracks=tracks,
        bpm=76.0,
        instruments=inst,
        path=OUT / "03_Archive_of_Skin.mid",
        mood=Mood.INTIMATE,
        key=key,
    )


# =====================================================================
# Track 4: Machine Psalms — 102 BPM — D Aeolian (First Energy Peak)
# =====================================================================
def produce_machine_psalms():
    print("  4. Machine Psalms [D Aeolian — 102 BPM]")
    key = Scale(root=2, mode=Mode.AEOLIAN)
    dur = 64.0
    chords = parse_progression("i:4 VI:4 III:4 VII:4 " * 4, key)

    # 1. Industrial Percussion (Breakbeat Generator with high chop and drive)
    drums = BreakbeatGenerator(
        variant="amen",
        chop_probability=0.45,
        ghost_notes=True
    ).render(chords, key, dur)

    # 2. Distorted Synth Bass
    bass = SynthBassGenerator(
        waveform="saw",
        pattern="wobble",
        octave_variation=0.25
    ).render(chords, key, dur)

    # 3. Brass Stabs (using short chords, outlining the progression)
    brass = []
    for bar in range(16):
        onset = bar * 4.0
        # Quick brass stabs on beats 1 and 2.5
        brass.append(NoteInfo(pitch=50, start=onset, duration=0.25, velocity=85))
        brass.append(NoteInfo(pitch=53, start=onset + 1.5, duration=0.25, velocity=80))

    # 4. Aggressive Strings: species counterpoint (3rd species: 4:1 quarter notes)
    strings_gen = CounterpointGenerator(
        species=3,
        cantus_position="below",
        dissonance_rules=True
    )
    strings = strings_gen.render(chords, key, dur)

    tracks = {
        "industrial_perc": drums,
        "distorted_bass": bass,
        "brass_stabs": brass,
        "aggressive_strings": strings,
    }

    inst = {
        "industrial_perc": DRUMS,
        "distorted_bass": SYNTH_BASS,
        "brass_stabs": BRASS,
        "aggressive_strings": VIOLIN,
    }

    produce_track(
        tracks=tracks,
        bpm=102.0,
        instruments=inst,
        path=OUT / "04_Machine_Psalms.mid",
        mood=Mood.AGGRESSIVE,
        key=key,
    )


# =====================================================================
# Track 5: Ghost Channel — 68 BPM — D Aeolian (Breakdown)
# =====================================================================
def produce_ghost_channel():
    print("  5. Ghost Channel [D Aeolian — 68 BPM]")
    key = Scale(root=2, mode=Mode.AEOLIAN)
    dur = 64.0
    chords = parse_progression("i:4 VI:4 III:4 VII:4 " * 4, key)

    # 1. Tape Hiss (Drone)
    hiss = DroneGenerator(
        params=GeneratorParams(key_range_low=60, key_range_high=72),
        velocity=25
    ).render(chords, key, dur)

    # 2. Vocal Chops (Choir aahs playing slow, breathy textures)
    vocals = AmbientPadGenerator(
        params=GeneratorParams(key_range_low=55, key_range_high=72),
        voicing="open",
        overlap=1.0
    ).render(chords, key, dur)

    # 3. Piano Echoes: theme played in retrograde (backward)
    piano = []
    for bar in range(0, 16, 4):
        piano.extend(registry.render("sakinfo", variant="retrograde", offset=bar * 4.0))

    # 4. Sub Bass (Sine wave)
    sub = SynthBassGenerator(
        waveform="sine",
        pattern="sub_kick"
    ).render(chords, key, dur)

    tracks = {
        "tape_hiss": hiss,
        "vocal_chops": vocals,
        "piano_echoes": piano,
        "sub_bass": sub,
    }

    inst = {
        "tape_hiss": FX_SOUND,
        "vocal_chops": CHOIR,
        "piano_echoes": PIANO,
        "sub_bass": SYNTH_BASS,
    }

    produce_track(
        tracks=tracks,
        bpm=68.0,
        instruments=inst,
        path=OUT / "05_Ghost_Channel.mid",
        mood=Mood.AMBIENT,
        key=key,
    )


# =====================================================================
# Track 6: Sakinfo Core — 95 BPM — D Aeolian (Culmination / Drop)
# =====================================================================
def produce_sakinfo_core():
    print("  6. Sakinfo Core [D Aeolian — 95 BPM]")
    key = Scale(root=2, mode=Mode.AEOLIAN)
    dur = 96.0  # 24 bars
    chords = parse_progression("i:4 VI:4 III:4 VII:4 " * 6, key)

    # Build layers of the main leitmotif
    piano = []
    choir = []
    strings = []
    
    # Layer direct, inverse, and octave transpositions across the track
    for bar in range(0, 24, 4):
        offset = bar * 4.0
        piano.extend(registry.render("sakinfo", offset=offset, transpose=12))      # Lead piano in higher octave
        choir.extend(registry.render("sakinfo", variant="inverse", offset=offset, transpose=0))    # Choir in mid register
        strings.extend(registry.render("sakinfo", variant="inverse", offset=offset, transpose=12)) # Strings in higher octave

    # Aggressive drum beat (electronic / hybrid)
    drums = BreakbeatGenerator(
        variant="funky",
        chop_probability=0.30,
        ghost_notes=True
    ).render(chords, key, dur)

    # Solid analog bass (low octave range - clean sine wave Reese bass)
    bass = SynthBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        waveform="sine",
        pattern="reese"
    ).render(chords, key, dur)

    # Cinematic Brass Section (mid-high range - spread voicing to avoid clutter)
    brass_notes = AmbientPadGenerator(
        params=GeneratorParams(key_range_low=53, key_range_high=68),
        voicing="spread"
    ).render(chords, key, dur)

    tracks = {
        "piano_lead": piano,
        "choir_layer": choir,
        "strings_layer": strings,
        "drums": drums,
        "synth_bass": bass,
        "brass_pad": brass_notes,
    }

    inst = {
        "piano_lead": PIANO,
        "choir_layer": CHOIR,
        "strings_layer": STRINGS,
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "brass_pad": BRASS,
    }

    produce_track(
        tracks=tracks,
        bpm=95.0,
        instruments=inst,
        path=OUT / "06_Sakinfo_Core.mid",
        mood=Mood.CINEMATIC,
        key=key,
    )


# =====================================================================
# Track 7: Memory Grid — 84 BPM — D Aeolian (Polyrhythm)
# =====================================================================
def produce_memory_grid():
    print("  7. Memory Grid [D Aeolian — 84 BPM]")
    key = Scale(root=2, mode=Mode.AEOLIAN)
    dur = 64.0
    chords = parse_progression("i:4 VI:4 III:4 VII:4 " * 4, key)

    # 1. Marimba playing 3-against-4 polyrhythm pattern
    marimba = []
    for step in range(0, 128):
        if step % 3 == 0:  # Triggers every 3 sixteenths (polyrhythmic grid)
            pitch = 74 + (step % 4) * 2  # Higher octave
            marimba.append(NoteInfo(pitch=pitch, start=step * 0.25, duration=0.20, velocity=65))

    # 2. Pizzicato Strings countermelodies (staggered: enters at beat 16.0)
    pizz = []
    for step in range(64, 128):  # starts at beat 16.0
        if step % 4 == 0:  # 4/4 grid response
            pitch = 50 + (step % 3) * 4
            pizz.append(NoteInfo(pitch=pitch, start=step * 0.25, duration=0.20, velocity=55))

    # 3. Modular Synth (Arpeggiator) (staggered: enters at beat 8.0)
    arp = ArpeggiatorGenerator(
        params=GeneratorParams(key_range_low=60, key_range_high=84),
        pattern="up_down",
        note_duration=0.5
    ).render(chords, key, dur)
    # Stagger: filter out notes before beat 8.0
    arp = [n for n in arp if n.start >= 8.0]

    # 4. Minimal percussion / click rhythm
    drums = ElectronicDrumsGenerator(
        params=GeneratorParams(),
        kit="linn",
        pattern="minimal"
    ).render(chords, key, dur)

    # 5. Low-end foundation bass/drone (fixes missing low-end warning)
    bass = DroneGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=38),
        velocity=35
    ).render(chords, key, dur)

    tracks = {
        "marimba": marimba,
        "pizz_strings": pizz,
        "modular_synth": arp,
        "drums": drums,
        "synth_bass": bass,
    }

    inst = {
        "marimba": MARIMBA,
        "pizz_strings": CELLO,
        "modular_synth": SYNTH_LEAD,
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
    }

    produce_track(
        tracks=tracks,
        bpm=84.0,
        instruments=inst,
        path=OUT / "07_Memory_Grid.mid",
        mood=Mood.EXPERIMENTAL,
        key=key,
    )


# =====================================================================
# Track 8: Zero Bloom — 110 BPM — D Aeolian (Fast Techno Drive)
# =====================================================================
def produce_zero_bloom():
    print("  8. Zero Bloom [D Aeolian — 110 BPM]")
    key = Scale(root=2, mode=Mode.AEOLIAN)
    dur = 96.0
    chords = parse_progression("i:4 VI:4 III:4 VII:4 " * 6, key)

    # 1. Rapid arpeggiator playing speedy variants of the theme (transposed higher for air)
    arp = []
    for bar in range(24):
        arp.extend(registry.render("sakinfo", variant="speedy", offset=bar * 4.0, transpose=24))

    # 2. Hard Techno Kick & Hats
    drums = ElectronicDrumsGenerator(
        params=GeneratorParams(),
        kit="909",
        pattern="four_on_floor"
    ).render(chords, key, dur)

    # 3. Reese Bass (Sawtooth slides in lower octave)
    bass = SynthBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=45),
        waveform="saw",
        pattern="reese",
        slide_probability=0.3
    ).render(chords, key, dur)

    # 4. Sharp aggressive violins (Outline accents)
    strings = []
    for bar in range(24):
        # Accents on 1 and 3
        strings.append(NoteInfo(pitch=74, start=bar * 4.0, duration=0.5, velocity=95))
        strings.append(NoteInfo(pitch=77, start=bar * 4.0 + 2.0, duration=0.5, velocity=90))

    tracks = {
        "synth_arp": arp,
        "drums": drums,
        "reese_bass": bass,
        "sharp_strings": strings,
    }

    inst = {
        "synth_arp": SYNTH_LEAD,
        "drums": DRUMS,
        "reese_bass": SYNTH_BASS,
        "sharp_strings": VIOLIN,
    }

    produce_track(
        tracks=tracks,
        bpm=110.0,
        instruments=inst,
        path=OUT / "08_Zero_Bloom.mid",
        mood=Mood.AGGRESSIVE,
        key=key,
    )


# =====================================================================
# Track 9: Last Transmission — 74 BPM — F Major (Emotional Shift)
# =====================================================================
def produce_last_transmission():
    print("  9. Last Transmission [F Major — 74 BPM]")
    # Shift key to relative major: F Major (root=5, mode=Mode.MAJOR)
    key = Scale(root=5, mode=Mode.MAJOR)
    dur = 64.0
    # Progression: F – C – Dm – Bb (I – V – vi – IV in F Major)
    chords = parse_progression("I:4 V:4 vi:4 IV:4 " * 4, key)

    # 1. Lead Piano: Theme returns in the relative major context (transposed up an octave for air)
    piano = []
    for bar in range(0, 16, 4):
        piano.extend(registry.render("sakinfo", variant="triumphant_major", offset=bar * 4.0, transpose=12))

    # 2. Soft Strings (emotional chords)
    strings = AmbientPadGenerator(
        params=GeneratorParams(key_range_low=48, key_range_high=64),
        voicing="spread",
        overlap=1.2
    ).render(chords, key, dur)

    # 3. Warm ambient pad
    pad = AmbientPadGenerator(
        params=GeneratorParams(key_range_low=36, key_range_high=48),
        voicing="chords"
    ).render(chords, key, dur)

    # 4. Low-end bass drone (fixes missing low register warning)
    bass = DroneGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=35),
        velocity=35
    ).render(chords, key, dur)

    tracks = {
        "lead_piano": piano,
        "soft_strings": strings,
        "warm_pad": pad,
        "bass_drone": bass,
    }

    inst = {
        "lead_piano": PIANO,
        "soft_strings": STRINGS,
        "warm_pad": PAD_WARM,
        "bass_drone": CELLO,
    }

    produce_track(
        tracks=tracks,
        bpm=74.0,
        instruments=inst,
        path=OUT / "09_Last_Transmission.mid",
        mood=Mood.INTIMATE,
        key=key,
    )


# =====================================================================
# Track 10: Afterimage — 60 BPM — D Aeolian (Outro)
# =====================================================================
def produce_afterimage():
    print("  10. Afterimage [D Aeolian — 60 BPM]")
    key = Scale(root=2, mode=Mode.AEOLIAN)
    dur = 48.0
    chords = parse_progression("i:8 VI:8 III:8 VII:8 i:16", key)

    # 1. Tape Drone
    drone = DroneGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=38),
        velocity=30
    ).render(chords, key, dur)

    # 2. Fragmented Motif (only plays parts of the theme, leaving it unresolved)
    piano = []
    piano.extend(registry.render("sakinfo", variant="fragmented", offset=0.0))
    piano.extend(registry.render("sakinfo", variant="fragmented", offset=16.0, transpose=-5))
    piano.extend(registry.render("sakinfo", variant="fragmented", offset=32.0, transpose=12))

    # 3. Distant Bells (Final unresolved note D ringing out at the end)
    bells = [
        NoteInfo(pitch=62, start=4.0, duration=4.0, velocity=50),
        NoteInfo(pitch=65, start=20.0, duration=6.0, velocity=45),
        NoteInfo(pitch=50, start=36.0, duration=12.0, velocity=60),  # Low unresolved D50
    ]

    tracks = {
        "tape_drone": drone,
        "fragmented_piano": piano,
        "distant_bells": bells,
    }

    inst = {
        "tape_drone": FX_SOUND,
        "fragmented_piano": PIANO,
        "distant_bells": BELLS,
    }

    produce_track(
        tracks=tracks,
        bpm=60.0,
        instruments=inst,
        path=OUT / "10_Afterimage.mid",
        mood=Mood.AMBIENT,
        key=key,
    )


# ------------------------------------------------------------------
# Main Orchestration Loop
# ------------------------------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("   SAKINFO — Concept Album Production")
    print("   Shared DNA / Theme Motif: D → F → E → C")
    print("=" * 60 + "\n")

    produce_signal_birth()
    produce_static_veins()
    produce_archive_of_skin()
    produce_machine_psalms()
    produce_ghost_channel()
    produce_sakinfo_core()
    produce_memory_grid()
    produce_zero_bloom()
    produce_last_transmission()
    produce_afterimage()

    print("\n" + "=" * 60)
    print("   PRODUCTION COMPLETE: SAKINFO")
    print(f"   MIDI files saved to: {OUT.absolute()}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
