# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/electronic/album_neon_grave.py — "NEON GRAVE" Album.

A dark, heavy, cinematic analog-electronic album in the style of Lorn, Burial,
and Industrial Cyberpunk Noir.
Built with a unified, carefully sculpted GM/GM2-friendly instrumental palette:
deep sliding sub-bass (808s), gritty acid bass, detuned warm/new-age pads,
FM electric piano, eerie music box/vibraphone chimes, processed choir chops,
biting saw leads, and industrial percussion.

Atmospheric Arc:
  "Ночной мегаполис -> Индустриальная паника -> Опустевший город -> Полная тишина"

Tracklist:
  01. Neon Grave         —  78 BPM — F# Phrygian       — Synth Bass 1, Warm Pad, Synth Strings, Voice Lead
  02. Black Signal       — 128 BPM — C# Minor          — Synth Bass 2, Lead 2 Saw, Sci-Fi FX, Choir Aahs
  03. Empty District     —  92 BPM — G Phrygian        — Pad 2 Warm, Synth Brass, Electric Piano, Sub Bass
  04. Chrome Teeth       — 146 BPM (halftime 73) — D Locrian — Synth Bass 1, Lead Saw, Distortion FX, Industrial Drums
  05. Dead Channel       — 105 BPM — A Harmonic Minor  — Choir Aahs, Pad 4 Choir, Lead 1 Square, Broken Glitch Beat
  06. Ghost Hardware     — 118 BPM — E Aeolian         — FM Electric Piano, Synth Bass, Bell/Music Box, Polysynth Pad
  07. Rust Memory        —  74 BPM — B Phrygian        — Acoustic Piano, Pad 1 New Age, Strings, Vibraphone
  08. No Sleep Protocol  — 136 BPM — F Hungarian Minor — Synth Bass 2, Lead Saw, Percussion FX, Choir Stabs
  09. Cold Flesh         —  88 BPM — C Minor           — Choir Lament, Warm Pad, Bowed Pad, Doom Sub Bass
  10. After the Blackout —  68 BPM — F# Minor          — Acoustic Piano, Strings, Fading Pad, Echo Choir
"""

import math
import random
from pathlib import Path

from melodica.composer.album_pipeline import Mood, produce_track
from melodica.composer.tempo_modulator import TempoModulator
from melodica.generators import GeneratorParams
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.lorn_hook import LornHookGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.idea_tool import IdeaPart
from melodica.types import ChordLabel, Mode, NoteInfo, Scale, parse_progression
from melodica.utils import chord_at, nearest_pitch, snap_to_scale

# ------------------------------------------------------------------
# Unified GM/GM2 Instrument Palette (0-indexed GM numbers)
# ------------------------------------------------------------------
ACOUSTIC_PIANO = 0       # GM 1 Acoustic Grand Piano
ELECTRIC_PIANO_1 = 4     # GM 5 Electric Piano 1 (Rhodes)
ELECTRIC_PIANO_2 = 5     # GM 6 Electric Piano 2 (FM EP / DX7)
MUSIC_BOX = 10           # GM 11 Music Box
VIBRAPHONE = 11          # GM 12 Vibraphone
DISTORTION_GUITAR = 30   # GM 31 Distortion Guitar (Industrial distortion/noise)
ELECTRIC_BASS_FINGER = 33# GM 34 Electric Bass
SYNTH_BASS_1 = 38        # GM 39 Synth Bass 1 (Sub 808 / Analog Reese)
SYNTH_BASS_2 = 39        # GM 40 Synth Bass 2 (Gritty / Acid Pulse Bass)
STRINGS = 48             # GM 49 String Ensemble 1
SLOW_STRINGS = 49        # GM 50 String Ensemble 2
SYNTH_STRINGS_1 = 50     # GM 51 Synth Strings 1
CHOIR_AAHS = 52          # GM 53 Choir Aahs
VOICE_OOHS = 53          # GM 54 Voice Oohs
SYNTH_BRASS_1 = 62       # GM 63 Synth Brass 1
LEAD_SQUARE = 80         # GM 81 Lead 1 Square
LEAD_SAW = 81            # GM 82 Lead 2 Sawtooth
LEAD_VOICE = 85          # GM 86 Lead 6 Voice
PAD_NEW_AGE = 88         # GM 89 Pad 1 New Age
PAD_WARM = 89            # GM 90 Pad 2 Warm
PAD_POLYSYNTH = 90       # GM 91 Pad 3 Polysynth
PAD_CHOIR = 91           # GM 92 Pad 4 Choir
PAD_BOWED = 92           # GM 93 Pad 5 Bowed
FX_SOUNDTRACK = 97       # GM 98 FX 2 Soundtrack
FX_CRYSTAL = 98          # GM 99 FX 3 Crystal
FX_ATMOSPHERE = 99       # GM 100 FX 4 Atmosphere
FX_ECHOES = 102          # GM 103 FX 7 Echoes
FX_SCIFI = 103           # GM 104 FX 8 Sci-Fi
DRUMS = 0                # Drum Channel (Channel 10)

# Drum Key Map (Standard GM Drum Kit)
KICK = 36
KICK_ACOUSTIC = 35
RIM = 37
SNARE = 38
CLAP = 39
SNARE_ELEC = 40
LOW_TOM = 41
HH_CLOSED = 42
LOW_MID_TOM = 45
HH_OPEN = 46
HIGH_TOM = 48
CRASH_CYMBAL = 49
RIDE_CYMBAL = 51
TAMBOURINE = 54
COWBELL = 56
CRASH_2 = 57

random.seed(2026)
OUT = Path("output/album_neon_grave")
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# Pass-through Rhythm Generator to preserve syncopations
# ------------------------------------------------------------------
class PassThroughRhythmGenerator:
    """Bypasses snapping stage to preserve custom-generated syncopations and microtiming."""

    def generate(self, duration_beats: float) -> list:
        return []


_PASSTHROUGH_RHYTHM = PassThroughRhythmGenerator()


# ------------------------------------------------------------------
# Custom Heavy / Industrial Drum Generator
# ------------------------------------------------------------------
def make_neon_drums(dur_beats: float, style: str, time_signature=(4, 4)) -> list[NoteInfo]:
    """Generates rich, styled drum patterns tailored for dark electronic aesthetics."""
    notes = []
    bar_len = time_signature[0]
    t = 0.0
    bar_index = 0

    while t < dur_beats:
        if style == "halftime_heavy":
            # Slow heavy halftime beat (beats 1, 2.5/3.5 kicks, snare on 2.0 or 3.0)
            if bar_index % 2 == 0:
                notes.append(NoteInfo(pitch=KICK, start=t + 0.0, duration=0.45, velocity=118))
                if random.random() < 0.75:
                    notes.append(NoteInfo(pitch=KICK, start=t + 1.5, duration=0.4, velocity=98))
            else:
                notes.append(NoteInfo(pitch=KICK, start=t + 0.0, duration=0.45, velocity=118))
                notes.append(NoteInfo(pitch=KICK, start=t + 2.5, duration=0.4, velocity=105))
                notes.append(NoteInfo(pitch=KICK, start=t + 3.5, duration=0.4, velocity=92))

            # Heavy Snare on beat 2.0 (halftime center)
            notes.append(NoteInfo(pitch=SNARE, start=t + 2.0, duration=0.35, velocity=112))
            if bar_index % 4 == 3 and random.random() < 0.6:
                notes.append(NoteInfo(pitch=CLAP, start=t + 3.75, duration=0.2, velocity=90))

            # Ticking Hats with slight humanized jitter
            for h in range(8):
                hat_t = t + h * 0.5
                if hat_t < dur_beats:
                    vel = 65 + random.randint(-12, 12)
                    notes.append(NoteInfo(pitch=HH_CLOSED, start=hat_t, duration=0.15, velocity=vel))

        elif style == "industrial_groove":
            # Relentless 4-on-the-floor kick with mechanical syncopation
            for k in range(4):
                vel = 120 if k % 2 == 0 else 112
                notes.append(NoteInfo(pitch=KICK, start=t + k, duration=0.35, velocity=vel))

            # Snare/Clap on 2.0
            notes.append(NoteInfo(pitch=SNARE, start=t + 2.0, duration=0.3, velocity=114))
            notes.append(NoteInfo(pitch=CLAP, start=t + 2.0, duration=0.25, velocity=95))

            # Glitch Rimshots on 16th offbeats
            for r in [0.75, 1.75, 2.75, 3.5]:
                if random.random() < 0.65:
                    notes.append(NoteInfo(pitch=RIM, start=t + r, duration=0.12, velocity=88))

            # Closed/Open Hats
            for h in range(8):
                hat_t = t + h * 0.5
                if hat_t < dur_beats:
                    is_open = (h % 2 == 1) and random.random() < 0.4
                    pitch = HH_OPEN if is_open else HH_CLOSED
                    vel = 80 if is_open else (68 + random.randint(-8, 8))
                    notes.append(NoteInfo(pitch=pitch, start=hat_t, duration=0.25 if is_open else 0.12, velocity=vel))

        elif style == "drag_trap":
            # Loose dragging trap rhythm
            notes.append(NoteInfo(pitch=KICK, start=t + 0.0, duration=0.5, velocity=115))
            if bar_index % 2 == 1:
                notes.append(NoteInfo(pitch=KICK, start=t + 2.75, duration=0.4, velocity=98))
            elif random.random() < 0.5:
                notes.append(NoteInfo(pitch=KICK, start=t + 3.25, duration=0.35, velocity=88))

            notes.append(NoteInfo(pitch=SNARE, start=t + 2.0, duration=0.35, velocity=110))

            # Hi-hat rolls
            h = 0.0
            while h < 4.0:
                hat_t = t + h
                if hat_t >= dur_beats:
                    break
                if h in (1.5, 3.5) and random.random() < 0.6:
                    for roll in range(4):
                        rt = hat_t + roll * 0.25
                        if rt < dur_beats:
                            notes.append(NoteInfo(pitch=HH_CLOSED, start=rt, duration=0.1, velocity=72 - roll * 6))
                    h += 1.0
                else:
                    notes.append(NoteInfo(pitch=HH_CLOSED, start=hat_t, duration=0.15, velocity=70 + random.randint(-10, 10)))
                    h += 0.5

        elif style == "halftime_crush":
            # Abrasive, heavy halftime industrial drill
            notes.append(NoteInfo(pitch=KICK, start=t + 0.0, duration=0.6, velocity=127))
            if bar_index % 2 == 0:
                notes.append(NoteInfo(pitch=KICK, start=t + 1.75, duration=0.4, velocity=105))
            else:
                notes.append(NoteInfo(pitch=KICK, start=t + 2.5, duration=0.45, velocity=115))
                notes.append(NoteInfo(pitch=KICK, start=t + 3.5, duration=0.35, velocity=100))

            # Crushing layered snare + clap
            notes.append(NoteInfo(pitch=SNARE, start=t + 2.0, duration=0.4, velocity=120))
            notes.append(NoteInfo(pitch=CLAP, start=t + 2.0, duration=0.3, velocity=110))

            # Machine stutter hats
            for h_idx in range(16):
                hat_t = t + h_idx * 0.25
                if hat_t < dur_beats and random.random() < 0.75:
                    vel = 60 + (15 if h_idx % 4 == 0 else 0) + random.randint(-6, 6)
                    notes.append(NoteInfo(pitch=HH_CLOSED, start=hat_t, duration=0.08, velocity=vel))

        elif style == "broken_glitch":
            # Broken syncopated trip-hop beat
            notes.append(NoteInfo(pitch=KICK, start=t + 0.0, duration=0.4, velocity=114))
            if bar_index % 2 == 0:
                notes.append(NoteInfo(pitch=KICK, start=t + 2.25, duration=0.35, velocity=102))
            else:
                notes.append(NoteInfo(pitch=KICK, start=t + 1.5, duration=0.35, velocity=98))
                notes.append(NoteInfo(pitch=KICK, start=t + 3.25, duration=0.3, velocity=90))

            notes.append(NoteInfo(pitch=SNARE, start=t + 2.0, duration=0.3, velocity=108))
            if random.random() < 0.4:
                notes.append(NoteInfo(pitch=RIM, start=t + 3.75, duration=0.1, velocity=85))

            for h in range(8):
                hat_t = t + h * 0.5
                if hat_t < dur_beats:
                    notes.append(NoteInfo(pitch=HH_CLOSED, start=hat_t, duration=0.12, velocity=64 + random.randint(-10, 10)))

        elif style == "rolling_electro":
            # Steady hypnotic rolling groove
            for k in [0.0, 1.5, 2.5]:
                notes.append(NoteInfo(pitch=KICK, start=t + k, duration=0.35, velocity=115))
            notes.append(NoteInfo(pitch=SNARE, start=t + 2.0, duration=0.3, velocity=110))

            for h_idx in range(8):
                hat_t = t + h_idx * 0.5
                if hat_t < dur_beats:
                    vel = 75 if h_idx % 2 == 1 else 60
                    notes.append(NoteInfo(pitch=HH_CLOSED, start=hat_t, duration=0.14, velocity=vel + random.randint(-5, 5)))

        elif style == "ambient_sparse":
            # Very sparse distant acoustic percussion
            if bar_index % 2 == 0:
                notes.append(NoteInfo(pitch=KICK_ACOUSTIC, start=t + 0.0, duration=0.8, velocity=88))
            if bar_index % 2 == 1:
                notes.append(NoteInfo(pitch=RIM, start=t + 2.0, duration=0.2, velocity=70))
            if random.random() < 0.3:
                notes.append(NoteInfo(pitch=RIDE_CYMBAL, start=t + 3.0, duration=1.2, velocity=55))

        elif style == "nervous_panic":
            # Fast driving industrial 4-on-the-floor with panic percussion
            for k in range(4):
                notes.append(NoteInfo(pitch=KICK, start=t + k, duration=0.3, velocity=122))
            notes.append(NoteInfo(pitch=SNARE, start=t + 2.0, duration=0.3, velocity=115))
            notes.append(NoteInfo(pitch=CLAP, start=t + 2.0, duration=0.2, velocity=105))

            # Fast 16th hats + open hats on offbeats
            for h in range(16):
                hat_t = t + h * 0.25
                if hat_t < dur_beats:
                    is_offbeat = (h % 4 == 2)
                    pitch = HH_OPEN if is_offbeat else HH_CLOSED
                    vel = 95 if is_offbeat else (65 + random.randint(-8, 8))
                    notes.append(NoteInfo(pitch=pitch, start=hat_t, duration=0.18 if is_offbeat else 0.08, velocity=vel))

        elif style == "slow_doom":
            # Slow doom heavy beat
            notes.append(NoteInfo(pitch=KICK, start=t + 0.0, duration=0.6, velocity=120))
            if bar_index % 2 == 1:
                notes.append(NoteInfo(pitch=KICK, start=t + 2.5, duration=0.5, velocity=102))
            notes.append(NoteInfo(pitch=SNARE, start=t + 2.0, duration=0.4, velocity=115))

            for h in range(8):
                hat_t = t + h * 0.5
                if hat_t < dur_beats:
                    notes.append(NoteInfo(pitch=HH_CLOSED, start=hat_t, duration=0.18, velocity=62 + random.randint(-8, 8)))

        t += bar_len
        bar_index += 1

    return notes


# ------------------------------------------------------------------
# Helper: Filter notes by time range for structured arrangements
# ------------------------------------------------------------------
def keep_in_range(notes: list[NoteInfo], start: float, end: float) -> list[NoteInfo]:
    return [n for n in notes if n.start >= start and n.start < end]


# ------------------------------------------------------------------
# Custom Melodic Generators for Specialized GM Instruments
# ------------------------------------------------------------------
def make_ghostly_piano(chords: list[ChordLabel], key: Scale, dur_beats: float, seed: int = 101) -> list[NoteInfo]:
    """Generates sparse, expressive, ghostly acoustic piano chords and upper-register drops."""
    rng = random.Random(seed)
    notes = []
    t = 0.0

    while t < dur_beats:
        ch = chord_at(chords, t)
        pcs = ch.pitch_classes() if ch else key.pitch_classes[:3]

        # Chord block in octave 3/4
        base_octave = 48
        chord_pitches = [base_octave + pc for pc in pcs]
        for p in chord_pitches:
            vel = rng.randint(52, 74)
            notes.append(NoteInfo(pitch=p, start=t + 0.0, duration=3.8, velocity=vel))

        # Rare high-register lonely drop (octave 6)
        if rng.random() < 0.6:
            high_p = snap_to_scale(base_octave + 24 + rng.choice(pcs), key)
            drop_start = t + rng.choice([1.5, 2.5, 3.0])
            if drop_start < dur_beats:
                notes.append(NoteInfo(pitch=high_p, start=drop_start, duration=2.2, velocity=rng.randint(60, 82)))

        t += 4.0

    return notes


def make_rhodes_chords(chords: list[ChordLabel], key: Scale, dur_beats: float, seed: int = 202) -> list[NoteInfo]:
    """Generates smooth, melancholic Rhodes/EP chords with gentle velocity variation."""
    rng = random.Random(seed)
    notes = []
    t = 0.0

    while t < dur_beats:
        ch = chord_at(chords, t)
        pcs = ch.pitch_classes() if ch else key.pitch_classes[:4]
        base_pitch = 48

        for i, pc in enumerate(pcs):
            p = base_pitch + pc
            vel = 62 + i * 4 + rng.randint(-5, 5)
            notes.append(NoteInfo(pitch=p, start=t + 0.0, duration=3.6, velocity=vel))

        if rng.random() < 0.45:
            grace_t = t + 2.5
            if grace_t < dur_beats:
                for pc in pcs[:2]:
                    notes.append(NoteInfo(pitch=base_pitch + 12 + pc, start=grace_t, duration=1.2, velocity=rng.randint(50, 68)))

        t += 4.0

    return notes


def make_fm_ep_arpeggio(chords: list[ChordLabel], key: Scale, dur_beats: float, seed: int = 303) -> list[NoteInfo]:
    """Generates hypnotic FM Electric Piano (DX7) 16th ostinato arpeggios."""
    rng = random.Random(seed)
    notes = []
    t = 0.0

    pattern = [0, 2, 1, 2, 0, 3, 2, 1]  # 8-step ostinato
    while t < dur_beats:
        ch = chord_at(chords, t)
        pcs = ch.pitch_classes() if ch else key.pitch_classes[:4]
        if len(pcs) < 4:
            pcs = pcs + [pcs[0] + 12]

        for step, offset in enumerate([0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]):
            note_t = t + offset
            if note_t >= dur_beats:
                break
            idx = pattern[step % len(pattern)] % len(pcs)
            p = 60 + pcs[idx]
            vel = 68 + (10 if step % 2 == 0 else 0) + rng.randint(-6, 6)
            notes.append(NoteInfo(pitch=p, start=note_t, duration=0.42, velocity=vel))

        t += 4.0

    return notes


def make_bell_chimes(chords: list[ChordLabel], key: Scale, dur_beats: float, seed: int = 404) -> list[NoteInfo]:
    """Generates high-frequency, delicate music box / vibraphone chimes."""
    rng = random.Random(seed)
    notes = []
    t = 0.0

    while t < dur_beats:
        ch = chord_at(chords, t)
        pcs = ch.pitch_classes() if ch else key.pitch_classes[:3]

        if rng.random() < 0.7:
            step_t = t + rng.choice([1.0, 2.0, 2.5])
            p = snap_to_scale(72 + rng.choice(pcs), key)
            notes.append(NoteInfo(pitch=p, start=step_t, duration=2.5, velocity=rng.randint(65, 88)))

            if rng.random() < 0.5:
                p2 = snap_to_scale(p + rng.choice([-2, -3, 2, 3]), key)
                notes.append(NoteInfo(pitch=p2, start=step_t + 0.5, duration=2.0, velocity=rng.randint(58, 78)))

        t += 4.0

    return notes


def make_strings_swell(chords: list[ChordLabel], key: Scale, dur_beats: float, seed: int = 505) -> list[NoteInfo]:
    """Generates slow, ominous cinematic string swells."""
    notes = []
    t = 0.0

    while t < dur_beats:
        ch = chord_at(chords, t)
        pcs = ch.pitch_classes() if ch else key.pitch_classes[:3]
        root = pcs[0]

        notes.append(NoteInfo(pitch=36 + root, start=t + 0.0, duration=4.0, velocity=68))
        fifth = (root + 7) % 12
        notes.append(NoteInfo(pitch=48 + fifth, start=t + 0.0, duration=4.0, velocity=72))
        if len(pcs) > 1:
            notes.append(NoteInfo(pitch=60 + pcs[1], start=t + 0.0, duration=4.0, velocity=76))

        t += 4.0

    return notes


def make_distortion_texture(chords: list[ChordLabel], key: Scale, dur_beats: float) -> list[NoteInfo]:
    """Generates aggressive, distorted guitar/noise power drones."""
    notes = []
    t = 0.0

    while t < dur_beats:
        ch = chord_at(chords, t)
        pcs = ch.pitch_classes() if ch else key.pitch_classes[:2]
        root = pcs[0]

        notes.append(NoteInfo(pitch=24 + root, start=t + 0.0, duration=3.9, velocity=95))
        notes.append(NoteInfo(pitch=31 + root, start=t + 0.0, duration=3.9, velocity=90))

        t += 4.0

    return notes


def make_sci_fi_fx(dur_beats: float, seed: int = 707) -> list[NoteInfo]:
    """Generates mysterious industrial sci-fi atmospheric textures."""
    rng = random.Random(seed)
    notes = []
    t = 0.0

    while t < dur_beats:
        if rng.random() < 0.5:
            p = rng.randint(48, 72)
            notes.append(NoteInfo(pitch=p, start=t + rng.choice([0.0, 2.0]), duration=3.5, velocity=rng.randint(55, 75)))
        t += 8.0

    return notes


# ==================================================================
# 10 ALBUM TRACK PRODUCTIONS
# ==================================================================


# ------------------------------------------------------------------
# Track 1: Neon Grave — 78 BPM — F# Phrygian
# ------------------------------------------------------------------
def produce_track_01_neon_grave():
    print("  01. Neon Grave [F# Phrygian — 78 BPM]")
    key = Scale(root=6, mode=Mode.PHRYGIAN)
    dur = 320.0  # 80 bars (~4.1 min)
    chords = parse_progression("i:4 bII:4 iv:4 v:4 " * 20, key)

    drums = make_neon_drums(dur, "halftime_heavy")

    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        mode="industrial",
        octave=2,
        note_duration=2.0,
        velocity_level=0.85,
    )
    bass = bass_gen.render(chords, key, dur)

    pad_gen = DarkPadGenerator(mode="phrygian_pad", chord_dur=4.0)
    pads = pad_gen.render(chords, key, dur)

    synth_strings = make_strings_swell(chords, key, dur, seed=101)

    lead_gen = LornHookGenerator(hook_length=5, octave=5, seed=101)
    leads = lead_gen.render(chords, key, dur)

    # Arrangement
    pads = keep_in_range(pads, 0.0, 320.0)
    synth_strings = keep_in_range(synth_strings, 0.0, 160.0) + keep_in_range(synth_strings, 224.0, 320.0)
    bass = keep_in_range(bass, 32.0, 256.0) + keep_in_range(bass, 288.0, 320.0)
    drums = keep_in_range(drums, 64.0, 256.0)
    leads = keep_in_range(leads, 96.0, 288.0)

    for n in pads:
        n.scale_velocity(1.35)
    for n in leads:
        n.scale_velocity(1.45)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "warm_pad": pads,
        "synth_strings": synth_strings,
        "lead_voice": leads,
    }
    instruments = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS_1,
        "warm_pad": PAD_WARM,
        "synth_strings": SYNTH_STRINGS_1,
        "lead_voice": LEAD_VOICE,
    }

    parts = [IdeaPart(name="Neon Grave", bars=80, tempo=78, time_signature=(4, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=78, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=78.0,
        instruments=instruments,
        path=OUT / "01_Neon_Grave.mid",
        mood=Mood.AMBIENT,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ------------------------------------------------------------------
# Track 2: Black Signal — 128 BPM — C# Minor
# ------------------------------------------------------------------
def produce_track_02_black_signal():
    print("  02. Black Signal [C# Minor — 128 BPM]")
    key = Scale(root=1, mode=Mode.AEOLIAN)
    dur = 320.0  # 80 bars (~2.5 min)
    chords = parse_progression("i:4 VI:4 III:4 VII:4 " * 20, key)

    drums = make_neon_drums(dur, "industrial_groove")

    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        mode="dark_pulse",
        octave=2,
        note_duration=1.0,
        velocity_level=0.9,
    )
    bass = bass_gen.render(chords, key, dur)

    lead_gen = LornHookGenerator(hook_length=6, octave=5, seed=202)
    lead_saw = lead_gen.render(chords, key, dur)

    choir_gen = VocalChopsGenerator(
        params=GeneratorParams(key_range_low=58, key_range_high=72),
        processing="stutter",
        chop_pattern="syncopated",
        density=0.6,
    )
    choir = choir_gen.render(chords, key, dur)

    fx_noise = make_sci_fi_fx(dur, seed=202)

    # Arrangement
    bass = keep_in_range(bass, 0.0, 256.0) + keep_in_range(bass, 288.0, 320.0)
    drums = keep_in_range(drums, 32.0, 256.0) + keep_in_range(drums, 288.0, 320.0)
    lead_saw = keep_in_range(lead_saw, 64.0, 224.0)
    choir = keep_in_range(choir, 32.0, 160.0) + keep_in_range(choir, 192.0, 288.0)
    fx_noise = keep_in_range(fx_noise, 0.0, 320.0)

    for n in lead_saw:
        n.scale_velocity(1.4)
    for n in choir:
        n.scale_velocity(1.3)

    tracks = {
        "drums": drums,
        "synth_bass_2": bass,
        "lead_saw": lead_saw,
        "choir_aahs": choir,
        "fx_scifi": fx_noise,
    }
    instruments = {
        "drums": DRUMS,
        "synth_bass_2": SYNTH_BASS_2,
        "lead_saw": LEAD_SAW,
        "choir_aahs": CHOIR_AAHS,
        "fx_scifi": FX_SCIFI,
    }

    parts = [IdeaPart(name="Black Signal", bars=80, tempo=128, time_signature=(4, 4), tempo_profile="industrial")]
    modulator = TempoModulator(default_tempo=128, tempo_profile="industrial")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=128.0,
        instruments=instruments,
        path=OUT / "02_Black_Signal.mid",
        mood=Mood.EXPERIMENTAL,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ------------------------------------------------------------------
# Track 3: Empty District — 92 BPM — G Phrygian
# ------------------------------------------------------------------
def produce_track_03_empty_district():
    print("  03. Empty District [G Phrygian — 92 BPM]")
    key = Scale(root=7, mode=Mode.PHRYGIAN)
    dur = 256.0  # 64 bars (~2.8 min)
    chords = parse_progression("i:4 bII:4 vdim:4 i:4 " * 16, key)

    drums = make_neon_drums(dur, "drag_trap")

    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=40),
        mode="dub",
        octave=1,
        note_duration=4.0,
        velocity_level=0.9,
    )
    bass = bass_gen.render(chords, key, dur)

    ep_notes = make_rhodes_chords(chords, key, dur, seed=303)

    pad_gen = DarkPadGenerator(mode="phrygian_pad", chord_dur=8.0)
    pads = pad_gen.render(chords, key, dur)

    drone_gen = DroneGenerator(
        params=GeneratorParams(key_range_low=48, key_range_high=64),
        variant="fifth",
    )
    synth_brass = drone_gen.render(chords, key, dur)

    # Arrangement
    ep_notes = keep_in_range(ep_notes, 0.0, 256.0)
    pads = keep_in_range(pads, 0.0, 256.0)
    bass = keep_in_range(bass, 32.0, 224.0)
    drums = keep_in_range(drums, 64.0, 224.0)
    synth_brass = keep_in_range(synth_brass, 128.0, 224.0)

    for n in ep_notes:
        n.scale_velocity(1.25)
    for n in pads:
        n.scale_velocity(1.3)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "electric_piano": ep_notes,
        "warm_pad": pads,
        "synth_brass": synth_brass,
    }
    instruments = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS_1,
        "electric_piano": ELECTRIC_PIANO_1,
        "warm_pad": PAD_WARM,
        "synth_brass": SYNTH_BRASS_1,
    }

    parts = [IdeaPart(name="Empty District", bars=64, tempo=92, time_signature=(4, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=92, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=92.0,
        instruments=instruments,
        path=OUT / "03_Empty_District.mid",
        mood=Mood.INTIMATE,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ------------------------------------------------------------------
# Track 4: Chrome Teeth — 146 BPM (halftime) — D Locrian
# ------------------------------------------------------------------
def produce_track_04_chrome_teeth():
    print("  04. Chrome Teeth [D Locrian — 146 BPM halftime]")
    key = Scale(root=2, mode=Mode.LOCRIAN)
    dur = 320.0  # 80 bars (~2.2 min)
    chords = parse_progression("idim:4 bII:4 vdim:4 bV:4 " * 20, key)

    drums = make_neon_drums(dur, "halftime_crush")

    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        mode="industrial",
        octave=2,
        note_duration=2.0,
        velocity_level=0.95,
    )
    bass = bass_gen.render(chords, key, dur)

    lead_gen = LornHookGenerator(hook_length=6, octave=5, seed=404)
    lead_saw = lead_gen.render(chords, key, dur)

    distortion_drone = make_distortion_texture(chords, key, dur)

    drone_gen = DroneGenerator(
        params=GeneratorParams(key_range_low=48, key_range_high=60),
        variant="power",
    )
    fx_track = drone_gen.render(chords, key, dur)

    # Arrangement
    distortion_drone = keep_in_range(distortion_drone, 0.0, 320.0)
    bass = keep_in_range(bass, 32.0, 288.0)
    drums = keep_in_range(drums, 64.0, 256.0) + keep_in_range(drums, 288.0, 320.0)
    lead_saw = keep_in_range(lead_saw, 64.0, 256.0)
    fx_track = keep_in_range(fx_track, 128.0, 288.0)

    for n in lead_saw:
        n.scale_velocity(1.5)
    for n in distortion_drone:
        n.scale_velocity(1.2)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "lead_saw": lead_saw,
        "distortion_fx": distortion_drone,
        "fx_soundtrack": fx_track,
    }
    instruments = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS_1,
        "lead_saw": LEAD_SAW,
        "distortion_fx": DISTORTION_GUITAR,
        "fx_soundtrack": FX_SOUNDTRACK,
    }

    parts = [IdeaPart(name="Chrome Teeth", bars=80, tempo=146, time_signature=(4, 4), tempo_profile="madness")]
    modulator = TempoModulator(default_tempo=146, tempo_profile="madness")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=146.0,
        instruments=instruments,
        path=OUT / "04_Chrome_Teeth.mid",
        mood=Mood.EXPERIMENTAL,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ------------------------------------------------------------------
# Track 5: Dead Channel — 105 BPM — A Harmonic Minor
# ------------------------------------------------------------------
def produce_track_05_dead_channel():
    print("  05. Dead Channel [A Harmonic Minor — 105 BPM]")
    key = Scale(root=9, mode=Mode.HARMONIC_MINOR)
    dur = 288.0  # 72 bars (~2.7 min)
    chords = parse_progression("i:4 iv:4 V7:4 i:4 " * 18, key)

    drums = make_neon_drums(dur, "broken_glitch")

    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        mode="dark_pulse",
        octave=2,
        note_duration=1.0,
        velocity_level=0.85,
    )
    bass = bass_gen.render(chords, key, dur)

    choir_gen = VocalChopsGenerator(
        params=GeneratorParams(key_range_low=58, key_range_high=72),
        processing="stutter",
        chop_pattern="syncopated",
        density=0.7,
    )
    choir_chops = choir_gen.render(chords, key, dur)

    pad_gen = DarkPadGenerator(mode="dim_cluster", chord_dur=4.0)
    pad_choir = pad_gen.render(chords, key, dur)

    lead_gen = LornHookGenerator(hook_length=5, octave=5, seed=505)
    lead_square = lead_gen.render(chords, key, dur)

    # Arrangement
    pad_choir = keep_in_range(pad_choir, 0.0, 288.0)
    choir_chops = keep_in_range(choir_chops, 32.0, 256.0)
    bass = keep_in_range(bass, 32.0, 256.0)
    drums = keep_in_range(drums, 64.0, 256.0)
    lead_square = keep_in_range(lead_square, 96.0, 224.0)

    for n in choir_chops:
        n.scale_velocity(1.35)
    for n in lead_square:
        n.scale_velocity(1.4)

    tracks = {
        "drums": drums,
        "synth_bass_2": bass,
        "choir_aahs": choir_chops,
        "pad_choir": pad_choir,
        "lead_square": lead_square,
    }
    instruments = {
        "drums": DRUMS,
        "synth_bass_2": SYNTH_BASS_2,
        "choir_aahs": CHOIR_AAHS,
        "pad_choir": PAD_CHOIR,
        "lead_square": LEAD_SQUARE,
    }

    parts = [IdeaPart(name="Dead Channel", bars=72, tempo=105, time_signature=(4, 4), tempo_profile="chaotic")]
    modulator = TempoModulator(default_tempo=105, tempo_profile="chaotic")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=105.0,
        instruments=instruments,
        path=OUT / "05_Dead_Channel.mid",
        mood=Mood.EXPERIMENTAL,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ------------------------------------------------------------------
# Track 6: Ghost Hardware — 118 BPM — E Aeolian
# ------------------------------------------------------------------
def produce_track_06_ghost_hardware():
    print("  06. Ghost Hardware [E Aeolian — 118 BPM]")
    key = Scale(root=4, mode=Mode.AEOLIAN)
    dur = 288.0  # 72 bars (~2.4 min)
    chords = parse_progression("i:4 VI:4 iv:4 v:4 " * 18, key)

    drums = make_neon_drums(dur, "rolling_electro")

    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=40),
        mode="industrial",
        octave=2,
        note_duration=2.0,
        velocity_level=0.85,
    )
    bass = bass_gen.render(chords, key, dur)

    fm_ep = make_fm_ep_arpeggio(chords, key, dur, seed=606)
    bell_motif = make_bell_chimes(chords, key, dur, seed=606)

    pad_gen = DarkPadGenerator(mode="minor_pad", chord_dur=8.0)
    pads = pad_gen.render(chords, key, dur)

    # Arrangement
    fm_ep = keep_in_range(fm_ep, 0.0, 288.0)
    pads = keep_in_range(pads, 0.0, 288.0)
    bass = keep_in_range(bass, 32.0, 256.0)
    drums = keep_in_range(drums, 64.0, 256.0)
    bell_motif = keep_in_range(bell_motif, 64.0, 224.0)

    for n in fm_ep:
        n.scale_velocity(1.2)
    for n in bell_motif:
        n.scale_velocity(1.4)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "fm_ep": fm_ep,
        "bell_hook": bell_motif,
        "pad_polysynth": pads,
    }
    instruments = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS_1,
        "fm_ep": ELECTRIC_PIANO_2,
        "bell_hook": MUSIC_BOX,
        "pad_polysynth": PAD_POLYSYNTH,
    }

    parts = [IdeaPart(name="Ghost Hardware", bars=72, tempo=118, time_signature=(4, 4), tempo_profile="industrial")]
    modulator = TempoModulator(default_tempo=118, tempo_profile="industrial")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=118.0,
        instruments=instruments,
        path=OUT / "06_Ghost_Hardware.mid",
        mood=Mood.CINEMATIC,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ------------------------------------------------------------------
# Track 7: Rust Memory — 74 BPM — B Phrygian
# ------------------------------------------------------------------
def produce_track_07_rust_memory():
    print("  07. Rust Memory [B Phrygian — 74 BPM]")
    key = Scale(root=11, mode=Mode.PHRYGIAN)
    dur = 224.0  # 56 bars (~3.0 min)
    chords = parse_progression("i:4 bII:4 bvii:4 i:4 " * 14, key)

    drums = make_neon_drums(dur, "ambient_sparse")

    piano = make_ghostly_piano(chords, key, dur, seed=707)

    pad_gen = DarkPadGenerator(mode="phrygian_pad", chord_dur=8.0)
    pads = pad_gen.render(chords, key, dur)

    strings = make_strings_swell(chords, key, dur, seed=707)
    vibes = make_bell_chimes(chords, key, dur, seed=707)

    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=38),
        mode="doom",
        octave=1,
        note_duration=8.0,
        velocity_level=0.8,
    )
    bass = bass_gen.render(chords, key, dur)

    # Arrangement
    piano = keep_in_range(piano, 0.0, 224.0)
    pads = keep_in_range(pads, 0.0, 224.0)
    strings = keep_in_range(strings, 32.0, 192.0)
    bass = keep_in_range(bass, 32.0, 192.0)
    drums = keep_in_range(drums, 64.0, 160.0)
    vibes = keep_in_range(vibes, 64.0, 192.0)

    for n in piano:
        n.scale_velocity(1.3)
    for n in vibes:
        n.scale_velocity(1.35)

    tracks = {
        "drums": drums,
        "acoustic_piano": piano,
        "pad_new_age": pads,
        "strings": strings,
        "vibraphone": vibes,
        "sub_bass": bass,
    }
    instruments = {
        "drums": DRUMS,
        "acoustic_piano": ACOUSTIC_PIANO,
        "pad_new_age": PAD_NEW_AGE,
        "strings": SLOW_STRINGS,
        "vibraphone": VIBRAPHONE,
        "sub_bass": SYNTH_BASS_1,
    }

    parts = [IdeaPart(name="Rust Memory", bars=56, tempo=74, time_signature=(4, 4), tempo_profile="requiem")]
    modulator = TempoModulator(default_tempo=74, tempo_profile="requiem")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=74.0,
        instruments=instruments,
        path=OUT / "07_Rust_Memory.mid",
        mood=Mood.AMBIENT,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ------------------------------------------------------------------
# Track 8: No Sleep Protocol — 136 BPM — F Hungarian Minor
# ------------------------------------------------------------------
def produce_track_08_no_sleep_protocol():
    print("  08. No Sleep Protocol [F Hungarian Minor — 136 BPM]")
    key = Scale(root=5, mode=Mode.HUNGARIAN_MINOR)
    dur = 320.0  # 80 bars (~2.35 min)
    chords = parse_progression("i:4 iv:4 vdim:4 i:4 " * 20, key)

    drums = make_neon_drums(dur, "nervous_panic")

    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        mode="dark_pulse",
        octave=2,
        note_duration=1.0,
        velocity_level=0.95,
    )
    bass = bass_gen.render(chords, key, dur)

    lead_gen = LornHookGenerator(hook_length=6, octave=6, seed=808)
    lead_saw = lead_gen.render(chords, key, dur)

    fx_glitch = make_sci_fi_fx(dur, seed=808)

    choir_gen = VocalChopsGenerator(
        params=GeneratorParams(key_range_low=60, key_range_high=74),
        processing="stutter",
        chop_pattern="offbeat",
        density=0.8,
    )
    choir_stabs = choir_gen.render(chords, key, dur)

    # Arrangement
    bass = keep_in_range(bass, 0.0, 288.0)
    drums = keep_in_range(drums, 32.0, 256.0) + keep_in_range(drums, 288.0, 320.0)
    lead_saw = keep_in_range(lead_saw, 64.0, 256.0)
    choir_stabs = keep_in_range(choir_stabs, 64.0, 224.0)
    fx_glitch = keep_in_range(fx_glitch, 0.0, 320.0)

    for n in lead_saw:
        n.scale_velocity(1.5)
    for n in choir_stabs:
        n.scale_velocity(1.3)

    tracks = {
        "drums": drums,
        "synth_bass_2": bass,
        "lead_saw": lead_saw,
        "fx_scifi": fx_glitch,
        "choir_aahs": choir_stabs,
    }
    instruments = {
        "drums": DRUMS,
        "synth_bass_2": SYNTH_BASS_2,
        "lead_saw": LEAD_SAW,
        "fx_scifi": FX_SCIFI,
        "choir_aahs": CHOIR_AAHS,
    }

    parts = [IdeaPart(name="No Sleep Protocol", bars=80, tempo=136, time_signature=(4, 4), tempo_profile="madness")]
    modulator = TempoModulator(default_tempo=136, tempo_profile="madness")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=136.0,
        instruments=instruments,
        path=OUT / "08_No_Sleep_Protocol.mid",
        mood=Mood.EXPERIMENTAL,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ------------------------------------------------------------------
# Track 9: Cold Flesh — 88 BPM — C Minor
# ------------------------------------------------------------------
def produce_track_09_cold_flesh():
    print("  09. Cold Flesh [C Minor — 88 BPM]")
    key = Scale(root=0, mode=Mode.AEOLIAN)
    dur = 256.0  # 64 bars (~2.9 min)
    chords = parse_progression("i:4 VI:4 iv:4 v:4 " * 16, key)

    drums = make_neon_drums(dur, "slow_doom")

    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=40),
        mode="doom",
        octave=1,
        note_duration=4.0,
        velocity_level=0.9,
    )
    bass = bass_gen.render(chords, key, dur)

    pad_gen = DarkPadGenerator(mode="minor_pad", chord_dur=8.0)
    warm_pad = pad_gen.render(chords, key, dur)

    lead_gen = LornHookGenerator(hook_length=4, octave=4, seed=909)
    choir_lament = lead_gen.render(chords, key, dur)

    drone_gen = DroneGenerator(
        params=GeneratorParams(key_range_low=48, key_range_high=60),
        variant="octave",
    )
    bowed_pad = drone_gen.render(chords, key, dur)

    # Arrangement
    warm_pad = keep_in_range(warm_pad, 0.0, 256.0)
    bowed_pad = keep_in_range(bowed_pad, 0.0, 256.0)
    bass = keep_in_range(bass, 32.0, 224.0)
    drums = keep_in_range(drums, 64.0, 224.0)
    choir_lament = keep_in_range(choir_lament, 64.0, 224.0)

    for n in choir_lament:
        n.scale_velocity(1.4)
    for n in warm_pad:
        n.scale_velocity(1.3)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "warm_pad": warm_pad,
        "choir_aahs": choir_lament,
        "pad_bowed": bowed_pad,
    }
    instruments = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS_1,
        "warm_pad": PAD_WARM,
        "choir_aahs": CHOIR_AAHS,
        "pad_bowed": PAD_BOWED,
    }

    parts = [IdeaPart(name="Cold Flesh", bars=64, tempo=88, time_signature=(4, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=88, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=88.0,
        instruments=instruments,
        path=OUT / "09_Cold_Flesh.mid",
        mood=Mood.AMBIENT,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ------------------------------------------------------------------
# Track 10: After the Blackout — 68 BPM — F# Minor
# ------------------------------------------------------------------
def produce_track_10_after_the_blackout():
    print("  10. After the Blackout [F# Minor — 68 BPM]")
    key = Scale(root=6, mode=Mode.AEOLIAN)
    dur = 192.0  # 48 bars (~2.8 min)
    chords = parse_progression("i:4 VI:4 III:4 VII:4 " * 12, key)

    # Pure ambient / neoclassical chamber doom — No drums
    piano = make_ghostly_piano(chords, key, dur, seed=1010)

    strings = make_strings_swell(chords, key, dur, seed=1010)

    pad_gen = DarkPadGenerator(mode="minor_pad", chord_dur=8.0)
    pads = pad_gen.render(chords, key, dur)

    lead_gen = LornHookGenerator(hook_length=3, octave=4, seed=1010)
    choir = lead_gen.render(chords, key, dur)

    fx_echoes = make_sci_fi_fx(dur, seed=1010)

    # Arrangement
    piano = keep_in_range(piano, 0.0, 192.0)
    pads = keep_in_range(pads, 0.0, 192.0)
    strings = keep_in_range(strings, 24.0, 168.0)
    choir = keep_in_range(choir, 48.0, 144.0)
    fx_echoes = keep_in_range(fx_echoes, 0.0, 192.0)

    for n in piano:
        n.scale_velocity(1.3)
    for n in choir:
        n.scale_velocity(1.35)

    tracks = {
        "acoustic_piano": piano,
        "strings": strings,
        "pad_new_age": pads,
        "choir_aahs": choir,
        "fx_echoes": fx_echoes,
    }
    instruments = {
        "acoustic_piano": ACOUSTIC_PIANO,
        "strings": STRINGS,
        "pad_new_age": PAD_NEW_AGE,
        "choir_aahs": CHOIR_AAHS,
        "fx_echoes": FX_ECHOES,
    }

    parts = [IdeaPart(name="After the Blackout", bars=48, tempo=68, time_signature=(4, 4), tempo_profile="requiem")]
    modulator = TempoModulator(default_tempo=68, tempo_profile="requiem")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=68.0,
        instruments=instruments,
        path=OUT / "10_After_the_Blackout.mid",
        mood=Mood.AMBIENT,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ------------------------------------------------------------------
# Main Production Album Loop
# ------------------------------------------------------------------
def main():
    print("\n" + "=" * 80)
    print("   N E O N   G R A V E   (ALBUM PRODUCTION)")
    print("   Dark Analog / Industrial Cyberpunk Noir Electronic Suite")
    print("   Unified GM/GM2 Instrumental Set & Atmospheric Narrative Arc")
    print("=" * 80 + "\n")

    produce_track_01_neon_grave()
    produce_track_02_black_signal()
    produce_track_03_empty_district()
    produce_track_04_chrome_teeth()
    produce_track_05_dead_channel()
    produce_track_06_ghost_hardware()
    produce_track_07_rust_memory()
    produce_track_08_no_sleep_protocol()
    produce_track_09_cold_flesh()
    produce_track_10_after_the_blackout()

    print("\n" + "=" * 80)
    print("   PRODUCTION COMPLETE: NEON GRAVE")
    print(f"   All 10 MIDI tracks saved to: {OUT.absolute()}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
