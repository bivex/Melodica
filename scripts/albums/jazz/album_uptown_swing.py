# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/jazz/album_uptown_swing.py — "UPTOWN SWING & SUNNY GROOVES" Album.

A cheerful, virtuosic, upbeat instrumental jazz album featuring Harlem Stride Piano,
Boogie-Woogie, Bebop, Latin Jazz / Samba, Dixieland Jump, and Big Band Swing.

Album Structure & Tracklist:
  01. The Honeybee Stride   — 175 BPM — F Major       — Stride Piano, Walking Bass, Alto Sax, Swing Drums
  02. Boogie Express        — 160 BPM — C Mixolydian  — Boogie-Woogie Piano, Tenor Sax, Trumpet, Drums
  03. Coconut Samba         — 138 BPM — Bb Major      — Vibraphone, Flute, Montuno Piano, Latin Drums
  04. Bebop Boardwalk       — 185 BPM — Eb Major      — Trumpet & Alto Sax Unison, Piano Comp, Fast Bass
  05. Ragtime Rollercoaster — 148 BPM — G Major       — Ragtime Piano, Clarinet, Vibraphone, Brushes
  06. Bourbon Street Jump   — 144 BPM — Ab Major      — Muted Trumpet, Trombone, Stride Piano, Jump Drums
  07. Cocktail Lounge Swing — 124 BPM — D Major       — Vibraphone, Jazz Guitar, Soprano Sax, Upright Bass
  08. Sugar Cane Bossa      — 132 BPM — A Major       — Flute, Jazz Guitar, Piano, Bossa Percussion
  09. Midnight Jam Session  — 165 BPM — F Blues       — Tenor Sax & Trumpet Solos, Piano Runs, Walking Bass
  10. Last Call at Benny's  — 152 BPM — C Major       — Full Brass Section, Stride Piano, Big Band Finale
"""

import math
import random
from pathlib import Path

from melodica.composer.album_pipeline import Mood, produce_track
from melodica.composer.tempo_modulator import TempoModulator
from melodica.generators import GeneratorParams
from melodica.generators.boogie_woogie import BoogieWoogieGenerator
from melodica.generators.montuno import MontunoGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.stride_piano import StridePianoGenerator
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.idea_tool import IdeaPart
from melodica.types import ChordLabel, Mode, NoteInfo, Scale, parse_progression
from melodica.utils import chord_at, nearest_pitch, snap_to_scale

# ------------------------------------------------------------------
# Standard GM Instrument Definitions (0-127)
# ------------------------------------------------------------------
ACOUSTIC_PIANO = 0       # GM 1
ELECTRIC_PIANO_1 = 4     # GM 5 (Rhodes)
VIBRAPHONE = 11          # GM 12
JAZZ_GUITAR = 26         # GM 27 (Electric Guitar Clean / Jazz)
ACOUSTIC_BASS = 32       # GM 33 (Upright Acoustic Bass)
FRETLESS_BASS = 35       # GM 36
TRUMPET = 56             # GM 57
TROMBONE = 57            # GM 58
MUTED_TRUMPET = 59       # GM 60
SOPRANO_SAX = 64         # GM 65
ALTO_SAX = 65            # GM 66
TENOR_SAX = 66           # GM 67
BARITONE_SAX = 67        # GM 68
CLARINET = 71            # GM 72
FLUTE = 73               # GM 74
DRUMS = 0                # Drum Channel (Channel 10)

# Drum Pitches
KICK = 36
KICK_ACOUSTIC = 35
SIDE_STICK = 37
SNARE = 38
CLAP = 39
SNARE_RIM = 40
HH_CLOSED = 42
HH_PEDAL = 44
HH_OPEN = 46
LOW_TOM = 45
MID_TOM = 47
HIGH_TOM = 50
CRASH_CYMBAL = 49
RIDE_CYMBAL = 51
RIDE_BELL = 53
TAMBOURINE = 54
COWBELL = 56
CABASA = 69
MARACAS = 70

random.seed(2026)
OUT = Path("output/album_uptown_swing")
OUT.mkdir(parents=True, exist_ok=True)


class PassThroughRhythmGenerator:
    """Bypasses snapping stage to preserve swing syncopations and microtiming."""
    def generate(self, duration_beats: float) -> list:
        return []


_PASSTHROUGH_RHYTHM = PassThroughRhythmGenerator()


# ------------------------------------------------------------------
# Dynamic Swing & Jazz Drum Generators
# ------------------------------------------------------------------
def make_jazz_drums(dur_beats: float, style: str, time_signature=(4, 4)) -> list[NoteInfo]:
    """Generates authentic jazz swing, bebop, boogie, samba, and bossa drum patterns."""
    notes = []
    bar_len = time_signature[0]
    t = 0.0
    bar_index = 0

    while t < dur_beats:
        if style == "fast_swing":
            # Driving swing ride cymbal
            ride_hits = [(0.0, 100), (1.0, 110), (1.67, 85), (2.0, 98), (3.0, 112), (3.67, 88)]
            for offset, vel in ride_hits:
                if t + offset < dur_beats:
                    notes.append(NoteInfo(pitch=RIDE_CYMBAL, start=t + offset, duration=0.3, velocity=vel + random.randint(-6, 6)))

            notes.append(NoteInfo(pitch=HH_PEDAL, start=t + 1.0, duration=0.1, velocity=105))
            notes.append(NoteInfo(pitch=HH_PEDAL, start=t + 3.0, duration=0.1, velocity=110))

            for beat in [0.0, 1.0, 2.0, 3.0]:
                notes.append(NoteInfo(pitch=KICK_ACOUSTIC, start=t + beat, duration=0.2, velocity=58 + random.randint(-5, 5)))

            if bar_index % 2 == 1:
                notes.append(NoteInfo(pitch=SIDE_STICK, start=t + 3.67, duration=0.15, velocity=92))
            elif random.random() < 0.4:
                notes.append(NoteInfo(pitch=SNARE, start=t + 1.67, duration=0.12, velocity=75))

        elif style == "boogie_shuffle":
            for b in range(4):
                notes.append(NoteInfo(pitch=HH_CLOSED, start=t + b + 0.0, duration=0.2, velocity=95))
                notes.append(NoteInfo(pitch=HH_CLOSED, start=t + b + 0.67, duration=0.15, velocity=78))

            notes.append(NoteInfo(pitch=SNARE, start=t + 1.0, duration=0.25, velocity=115))
            notes.append(NoteInfo(pitch=SNARE, start=t + 3.0, duration=0.25, velocity=118))

            notes.append(NoteInfo(pitch=KICK, start=t + 0.0, duration=0.3, velocity=110))
            notes.append(NoteInfo(pitch=KICK, start=t + 1.67, duration=0.25, velocity=92))
            notes.append(NoteInfo(pitch=KICK, start=t + 2.0, duration=0.3, velocity=105))
            notes.append(NoteInfo(pitch=KICK, start=t + 3.0, duration=0.25, velocity=100))

        elif style == "latin_samba":
            notes.append(NoteInfo(pitch=KICK, start=t + 0.0, duration=0.3, velocity=85))
            notes.append(NoteInfo(pitch=KICK, start=t + 1.0, duration=0.4, velocity=118))
            notes.append(NoteInfo(pitch=KICK, start=t + 2.0, duration=0.3, velocity=85))
            notes.append(NoteInfo(pitch=KICK, start=t + 3.0, duration=0.4, velocity=118))

            for s in range(8):
                vel = 95 if s % 2 == 1 else 65
                notes.append(NoteInfo(pitch=MARACAS, start=t + s * 0.5, duration=0.15, velocity=vel))

            for r in [0.0, 0.75, 1.5, 2.5, 3.25]:
                if t + r < dur_beats:
                    notes.append(NoteInfo(pitch=SIDE_STICK, start=t + r, duration=0.15, velocity=100))

        elif style == "bebop_brush":
            ride_hits = [(0.0, 90), (1.0, 105), (1.67, 80), (2.0, 92), (3.0, 108), (3.67, 84)]
            for offset, vel in ride_hits:
                if t + offset < dur_beats:
                    notes.append(NoteInfo(pitch=RIDE_CYMBAL, start=t + offset, duration=0.25, velocity=vel))

            notes.append(NoteInfo(pitch=HH_PEDAL, start=t + 1.0, duration=0.1, velocity=100))
            notes.append(NoteInfo(pitch=HH_PEDAL, start=t + 3.0, duration=0.1, velocity=105))

            if random.random() < 0.5:
                accent_t = t + random.choice([0.67, 1.67, 2.67, 3.67])
                notes.append(NoteInfo(pitch=SNARE, start=accent_t, duration=0.15, velocity=random.randint(85, 105)))

        elif style == "dixieland_jump":
            notes.append(NoteInfo(pitch=KICK, start=t + 0.0, duration=0.35, velocity=115))
            notes.append(NoteInfo(pitch=KICK, start=t + 2.0, duration=0.35, velocity=112))
            notes.append(NoteInfo(pitch=SNARE, start=t + 1.0, duration=0.25, velocity=108))
            notes.append(NoteInfo(pitch=SNARE, start=t + 3.0, duration=0.25, velocity=114))

            for o in [0.5, 1.5, 2.5, 3.5]:
                notes.append(NoteInfo(pitch=SIDE_STICK, start=t + o, duration=0.1, velocity=85))

        elif style == "lounge_swing":
            for offset in [0.0, 1.0, 1.67, 2.0, 3.0, 3.67]:
                vel = 80 if offset in (1.0, 3.0) else 65
                notes.append(NoteInfo(pitch=RIDE_CYMBAL, start=t + offset, duration=0.3, velocity=vel + random.randint(-4, 4)))
            notes.append(NoteInfo(pitch=HH_PEDAL, start=t + 1.0, duration=0.1, velocity=90))
            notes.append(NoteInfo(pitch=HH_PEDAL, start=t + 3.0, duration=0.1, velocity=92))

        elif style == "bossa_nova":
            notes.append(NoteInfo(pitch=KICK, start=t + 0.0, duration=0.3, velocity=90))
            notes.append(NoteInfo(pitch=KICK, start=t + 1.5, duration=0.3, velocity=95))
            notes.append(NoteInfo(pitch=KICK, start=t + 2.0, duration=0.3, velocity=85))
            notes.append(NoteInfo(pitch=KICK, start=t + 3.5, duration=0.3, velocity=92))

            for h in range(8):
                notes.append(NoteInfo(pitch=HH_CLOSED, start=t + h * 0.5, duration=0.15, velocity=70 + random.randint(-5, 5)))

            for r in [0.0, 1.5, 2.0, 3.5]:
                notes.append(NoteInfo(pitch=SIDE_STICK, start=t + r, duration=0.15, velocity=95))

        elif style == "big_band_shout":
            for offset, vel in [(0.0, 110), (1.0, 120), (1.67, 95), (2.0, 112), (3.0, 122), (3.67, 100)]:
                notes.append(NoteInfo(pitch=RIDE_CYMBAL, start=t + offset, duration=0.35, velocity=vel))

            notes.append(NoteInfo(pitch=HH_PEDAL, start=t + 1.0, duration=0.1, velocity=115))
            notes.append(NoteInfo(pitch=HH_PEDAL, start=t + 3.0, duration=0.1, velocity=120))
            notes.append(NoteInfo(pitch=SNARE, start=t + 1.0, duration=0.3, velocity=122))
            notes.append(NoteInfo(pitch=SNARE, start=t + 3.0, duration=0.3, velocity=125))

            if bar_index % 4 == 0:
                notes.append(NoteInfo(pitch=CRASH_CYMBAL, start=t + 0.0, duration=0.8, velocity=118))
                notes.append(NoteInfo(pitch=KICK, start=t + 0.0, duration=0.4, velocity=125))

        t += bar_len
        bar_index += 1

    return notes


def keep_in_range(notes: list[NoteInfo], start: float, end: float) -> list[NoteInfo]:
    return [n for n in notes if n.start >= start and n.start < end]


# ------------------------------------------------------------------
# Custom Lead Melodies and Solo Generators
# ------------------------------------------------------------------
def make_swing_solo(chords: list[ChordLabel], key: Scale, dur_beats: float, seed: int = 101, instrument_octave: int = 5) -> list[NoteInfo]:
    """Generates lively, syncopated jazz swing lead phrases with blues inflections."""
    rng = random.Random(seed)
    notes = []
    t = 0.0

    while t < dur_beats:
        ch = chord_at(chords, t)
        pcs = ch.pitch_classes() if ch else key.pitch_classes[:4]

        phrase_len = min(16.0, dur_beats - t)
        beat_offset = 0.0
        while beat_offset < phrase_len - 2.0:
            step = rng.choice([0.5, 0.67, 1.0, 1.33])
            note_t = t + beat_offset
            if note_t >= dur_beats:
                break

            pc = rng.choice(pcs)
            if rng.random() < 0.25:
                pc = (pc + 1) % 12
            pitch = snap_to_scale(instrument_octave * 12 + pc, key)
            dur = step * 0.85
            vel = rng.randint(80, 112)
            notes.append(NoteInfo(pitch=pitch, start=note_t, duration=dur, velocity=vel))
            beat_offset += step

        t += 16.0

    return notes


def make_brass_stabs(chords: list[ChordLabel], key: Scale, dur_beats: float, seed: int = 202) -> list[NoteInfo]:
    """Generates punchy big-band / swing brass chord accents."""
    rng = random.Random(seed)
    notes = []
    t = 0.0

    while t < dur_beats:
        ch = chord_at(chords, t)
        pcs = ch.pitch_classes() if ch else key.pitch_classes[:3]

        hit_offsets = rng.choice([
            [1.5, 3.5],
            [0.0, 2.5],
            [1.0, 2.5, 3.5],
            [0.67, 2.67]
        ])

        for off in hit_offsets:
            hit_t = t + off
            if hit_t < dur_beats:
                for pc in pcs:
                    p = 60 + pc
                    vel = rng.randint(95, 118)
                    notes.append(NoteInfo(pitch=p, start=hit_t, duration=0.35, velocity=vel))

        t += 4.0

    return notes


def make_vibes_melody(chords: list[ChordLabel], key: Scale, dur_beats: float, seed: int = 303) -> list[NoteInfo]:
    """Generates bright, sparkling vibraphone arpeggios and melodic lines."""
    rng = random.Random(seed)
    notes = []
    t = 0.0

    while t < dur_beats:
        ch = chord_at(chords, t)
        pcs = ch.pitch_classes() if ch else key.pitch_classes[:4]

        for step in [0.0, 0.67, 1.33, 2.0, 2.67, 3.33]:
            note_t = t + step
            if note_t >= dur_beats:
                break
            if rng.random() < 0.75:
                p = snap_to_scale(72 + rng.choice(pcs), key)
                notes.append(NoteInfo(pitch=p, start=note_t, duration=0.5, velocity=rng.randint(75, 102)))

        t += 4.0

    return notes


def make_jazz_guitar_comp(chords: list[ChordLabel], key: Scale, dur_beats: float, seed: int = 404) -> list[NoteInfo]:
    """Generates Freddie Green / swing 4-to-the-bar jazz guitar chord comping."""
    rng = random.Random(seed)
    notes = []
    t = 0.0

    while t < dur_beats:
        ch = chord_at(chords, t)
        pcs = ch.pitch_classes() if ch else key.pitch_classes[:3]

        for b in range(4):
            beat_t = t + b
            if beat_t >= dur_beats:
                break
            for pc in pcs[:3]:
                p = 52 + pc
                vel = 75 + (12 if b in (1, 3) else 0) + rng.randint(-4, 4)
                notes.append(NoteInfo(pitch=p, start=beat_t, duration=0.35, velocity=vel))

        t += 4.0

    return notes


# =====================================================================
# 10 CHEERFUL JAZZ TRACK PRODUCTIONS
# =====================================================================


# ---------------------------------------------------------------------
# Track 1: The Honeybee Stride — 175 BPM — F Major
# ---------------------------------------------------------------------
def produce_01_honeybee_stride():
    print("  01. The Honeybee Stride [F Major — 175 BPM]")
    key = Scale(root=5, mode=Mode.IONIAN)
    dur = 256.0  # 64 bars (~2.4 min)
    chords = parse_progression("I:4 vi:4 ii:4 V7:4 " * 16, key)

    drums = make_jazz_drums(dur, "fast_swing")

    stride_gen = StridePianoGenerator(
        GeneratorParams(density=0.8, key_range_low=36, key_range_high=84),
        pattern="standard",
    )
    stride_piano = stride_gen.render(chords, key, dur)

    bass_gen = WalkingBassGenerator(
        params=GeneratorParams(key_range_low=32, key_range_high=55),
        approach_style="mixed",
    )
    walking_bass = bass_gen.render(chords, key, dur)

    sax_lead = make_swing_solo(chords, key, dur, seed=101, instrument_octave=5)

    # Arrangement
    stride_piano = keep_in_range(stride_piano, 0.0, 256.0)
    walking_bass = keep_in_range(walking_bass, 16.0, 240.0)
    drums = keep_in_range(drums, 32.0, 240.0)
    sax_lead = keep_in_range(sax_lead, 32.0, 224.0)

    for n in sax_lead:
        n.scale_velocity(1.3)
    for n in stride_piano:
        n.scale_velocity(1.2)

    tracks = {
        "drums": drums,
        "stride_piano": stride_piano,
        "walking_bass": walking_bass,
        "alto_sax": sax_lead,
    }
    instruments = {
        "drums": DRUMS,
        "stride_piano": ACOUSTIC_PIANO,
        "walking_bass": ACOUSTIC_BASS,
        "alto_sax": ALTO_SAX,
    }

    parts = [IdeaPart(name="The Honeybee Stride", bars=64, tempo=175, time_signature=(4, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=175, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=175.0,
        instruments=instruments,
        path=OUT / "01_The_Honeybee_Stride.mid",
        mood=Mood.CHAMBER,
        key=key,
        genre="neosoul",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ---------------------------------------------------------------------
# Track 2: Boogie Express — 160 BPM — C Mixolydian / Blues
# ---------------------------------------------------------------------
def produce_02_boogie_express():
    print("  02. Boogie Express [C Mixolydian — 160 BPM]")
    key = Scale(root=0, mode=Mode.MIXOLYDIAN)
    dur = 288.0  # 72 bars (~2.4 min)
    chords = parse_progression("I7:4 I7:4 IV7:4 I7:4 V7:4 IV7:4 I7:4 V7:4 " * 9, key)

    drums = make_jazz_drums(dur, "boogie_shuffle")

    boogie_gen = BoogieWoogieGenerator(
        GeneratorParams(density=0.9, key_range_low=32, key_range_high=52),
        pattern="standard",
    )
    boogie_piano = boogie_gen.render(chords, key, dur)

    comp_gen = PianoCompGenerator(
        GeneratorParams(density=0.7, key_range_low=55, key_range_high=78),
        comp_style="jazz",
        accent_pattern="charleston",
    )
    piano_comp = comp_gen.render(chords, key, dur)

    tenor_sax = make_swing_solo(chords, key, dur, seed=202, instrument_octave=5)
    brass_stabs = make_brass_stabs(chords, key, dur, seed=202)

    # Arrangement
    boogie_piano = keep_in_range(boogie_piano, 0.0, 288.0)
    piano_comp = keep_in_range(piano_comp, 16.0, 272.0)
    drums = keep_in_range(drums, 32.0, 272.0)
    tenor_sax = keep_in_range(tenor_sax, 32.0, 256.0)
    brass_stabs = keep_in_range(brass_stabs, 64.0, 256.0)

    for n in tenor_sax:
        n.scale_velocity(1.35)
    for n in brass_stabs:
        n.scale_velocity(1.25)

    tracks = {
        "drums": drums,
        "boogie_piano": boogie_piano,
        "piano_comp": piano_comp,
        "tenor_sax": tenor_sax,
        "trumpet": brass_stabs,
    }
    instruments = {
        "drums": DRUMS,
        "boogie_piano": ACOUSTIC_PIANO,
        "piano_comp": ACOUSTIC_PIANO,
        "tenor_sax": TENOR_SAX,
        "trumpet": TRUMPET,
    }

    parts = [IdeaPart(name="Boogie Express", bars=72, tempo=160, time_signature=(4, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=160, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=160.0,
        instruments=instruments,
        path=OUT / "02_Boogie_Express.mid",
        mood=Mood.CHAMBER,
        key=key,
        genre="neosoul",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ---------------------------------------------------------------------
# Track 3: Coconut Samba — 138 BPM — Bb Major
# ---------------------------------------------------------------------
def produce_03_coconut_samba():
    print("  03. Coconut Samba [Bb Major — 138 BPM]")
    key = Scale(root=10, mode=Mode.IONIAN)
    dur = 256.0  # 64 bars (~2.8 min)
    chords = parse_progression("I:4 IV:4 ii:4 V7:4 " * 16, key)

    drums = make_jazz_drums(dur, "latin_samba")

    montuno_gen = MontunoGenerator(
        GeneratorParams(density=0.8, key_range_low=52, key_range_high=76),
        pattern="son",
    )
    montuno = montuno_gen.render(chords, key, dur)

    bass_gen = WalkingBassGenerator(
        params=GeneratorParams(key_range_low=32, key_range_high=53),
        approach_style="diatonic",
    )
    bass = bass_gen.render(chords, key, dur)

    vibes = make_vibes_melody(chords, key, dur, seed=303)
    flute_lead = make_swing_solo(chords, key, dur, seed=303, instrument_octave=6)

    # Arrangement
    montuno = keep_in_range(montuno, 0.0, 256.0)
    drums = keep_in_range(drums, 16.0, 240.0)
    bass = keep_in_range(bass, 16.0, 240.0)
    vibes = keep_in_range(vibes, 32.0, 224.0)
    flute_lead = keep_in_range(flute_lead, 64.0, 208.0)

    for n in vibes:
        n.scale_velocity(1.3)
    for n in flute_lead:
        n.scale_velocity(1.35)

    tracks = {
        "drums": drums,
        "montuno_piano": montuno,
        "bass": bass,
        "vibraphone": vibes,
        "flute": flute_lead,
    }
    instruments = {
        "drums": DRUMS,
        "montuno_piano": ACOUSTIC_PIANO,
        "bass": ACOUSTIC_BASS,
        "vibraphone": VIBRAPHONE,
        "flute": FLUTE,
    }

    parts = [IdeaPart(name="Coconut Samba", bars=64, tempo=138, time_signature=(4, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=138, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=138.0,
        instruments=instruments,
        path=OUT / "03_Coconut_Samba.mid",
        mood=Mood.CHAMBER,
        key=key,
        genre="neosoul",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ---------------------------------------------------------------------
# Track 4: Bebop Boardwalk — 185 BPM — Eb Major
# ---------------------------------------------------------------------
def produce_04_bebop_boardwalk():
    print("  04. Bebop Boardwalk [Eb Major — 185 BPM]")
    key = Scale(root=3, mode=Mode.IONIAN)
    dur = 320.0  # 80 bars (~2.3 min)
    chords = parse_progression("I:4 vi:4 ii:4 V7:4 iii:4 VI7:4 ii:4 V7:4 " * 10, key)

    drums = make_jazz_drums(dur, "bebop_brush")

    bass_gen = WalkingBassGenerator(
        params=GeneratorParams(key_range_low=32, key_range_high=55),
        approach_style="chromatic",
    )
    bass = bass_gen.render(chords, key, dur)

    comp_gen = PianoCompGenerator(
        GeneratorParams(density=0.6, key_range_low=52, key_range_high=74),
        comp_style="jazz",
        accent_pattern="syncopated",
    )
    piano_comp = comp_gen.render(chords, key, dur)

    trumpet_head = make_swing_solo(chords, key, dur, seed=404, instrument_octave=5)
    alto_sax_unison = make_swing_solo(chords, key, dur, seed=404, instrument_octave=5)

    # Arrangement
    piano_comp = keep_in_range(piano_comp, 0.0, 320.0)
    bass = keep_in_range(bass, 16.0, 304.0)
    drums = keep_in_range(drums, 32.0, 304.0)
    trumpet_head = keep_in_range(trumpet_head, 32.0, 288.0)
    alto_sax_unison = keep_in_range(alto_sax_unison, 32.0, 160.0) + keep_in_range(alto_sax_unison, 224.0, 288.0)

    for n in trumpet_head:
        n.scale_velocity(1.3)
    for n in alto_sax_unison:
        n.scale_velocity(1.25)

    tracks = {
        "drums": drums,
        "walking_bass": bass,
        "piano_comp": piano_comp,
        "trumpet": trumpet_head,
        "alto_sax": alto_sax_unison,
    }
    instruments = {
        "drums": DRUMS,
        "walking_bass": ACOUSTIC_BASS,
        "piano_comp": ACOUSTIC_PIANO,
        "trumpet": TRUMPET,
        "alto_sax": ALTO_SAX,
    }

    parts = [IdeaPart(name="Bebop Boardwalk", bars=80, tempo=185, time_signature=(4, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=185, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=185.0,
        instruments=instruments,
        path=OUT / "04_Bebop_Boardwalk.mid",
        mood=Mood.CHAMBER,
        key=key,
        genre="neosoul",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ---------------------------------------------------------------------
# Track 5: Ragtime Rollercoaster — 148 BPM — G Major
# ---------------------------------------------------------------------
def produce_05_ragtime_rollercoaster():
    print("  05. Ragtime Rollercoaster [G Major — 148 BPM]")
    key = Scale(root=7, mode=Mode.IONIAN)
    dur = 256.0  # 64 bars (~2.6 min)
    chords = parse_progression("I:4 V7:4 I:4 IV:4 I:4 V7:4 I:4 I:4 " * 8, key)

    drums = make_jazz_drums(dur, "dixieland_jump")

    stride_gen = StridePianoGenerator(
        GeneratorParams(density=0.85, key_range_low=36, key_range_high=86),
        pattern="tatum",
    )
    ragtime_piano = stride_gen.render(chords, key, dur)

    clarinet = make_swing_solo(chords, key, dur, seed=505, instrument_octave=5)
    vibes = make_vibes_melody(chords, key, dur, seed=505)

    # Arrangement
    ragtime_piano = keep_in_range(ragtime_piano, 0.0, 256.0)
    drums = keep_in_range(drums, 16.0, 240.0)
    clarinet = keep_in_range(clarinet, 32.0, 224.0)
    vibes = keep_in_range(vibes, 64.0, 224.0)

    for n in clarinet:
        n.scale_velocity(1.3)
    for n in vibes:
        n.scale_velocity(1.25)

    tracks = {
        "drums": drums,
        "ragtime_piano": ragtime_piano,
        "clarinet": clarinet,
        "vibraphone": vibes,
    }
    instruments = {
        "drums": DRUMS,
        "ragtime_piano": ACOUSTIC_PIANO,
        "clarinet": CLARINET,
        "vibraphone": VIBRAPHONE,
    }

    parts = [IdeaPart(name="Ragtime Rollercoaster", bars=64, tempo=148, time_signature=(4, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=148, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=148.0,
        instruments=instruments,
        path=OUT / "05_Ragtime_Rollercoaster.mid",
        mood=Mood.CHAMBER,
        key=key,
        genre="neosoul",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ---------------------------------------------------------------------
# Track 6: Bourbon Street Jump — 144 BPM — Ab Major
# ---------------------------------------------------------------------
def produce_06_bourbon_street_jump():
    print("  06. Bourbon Street Jump [Ab Major — 144 BPM]")
    key = Scale(root=8, mode=Mode.IONIAN)
    dur = 256.0  # 64 bars (~2.7 min)
    chords = parse_progression("I:4 IV:4 I:4 V7:4 I:4 IV:4 V7:4 I:4 " * 8, key)

    drums = make_jazz_drums(dur, "dixieland_jump")

    stride_gen = StridePianoGenerator(
        GeneratorParams(density=0.75, key_range_low=36, key_range_high=80),
        pattern="walking_stride",
    )
    piano = stride_gen.render(chords, key, dur)

    muted_trumpet = make_swing_solo(chords, key, dur, seed=606, instrument_octave=5)
    trombone = make_swing_solo(chords, key, dur, seed=607, instrument_octave=4)

    # Arrangement
    piano = keep_in_range(piano, 0.0, 256.0)
    drums = keep_in_range(drums, 16.0, 240.0)
    muted_trumpet = keep_in_range(muted_trumpet, 32.0, 224.0)
    trombone = keep_in_range(trombone, 64.0, 224.0)

    for n in muted_trumpet:
        n.scale_velocity(1.3)
    for n in trombone:
        n.scale_velocity(1.25)

    tracks = {
        "drums": drums,
        "piano": piano,
        "muted_trumpet": muted_trumpet,
        "trombone": trombone,
    }
    instruments = {
        "drums": DRUMS,
        "piano": ACOUSTIC_PIANO,
        "muted_trumpet": MUTED_TRUMPET,
        "trombone": TROMBONE,
    }

    parts = [IdeaPart(name="Bourbon Street Jump", bars=64, tempo=144, time_signature=(4, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=144, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=144.0,
        instruments=instruments,
        path=OUT / "06_Bourbon_Street_Jump.mid",
        mood=Mood.CHAMBER,
        key=key,
        genre="neosoul",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ---------------------------------------------------------------------
# Track 7: Cocktail Lounge Swing — 124 BPM — D Major
# ---------------------------------------------------------------------
def produce_07_cocktail_lounge_swing():
    print("  07. Cocktail Lounge Swing [D Major — 124 BPM]")
    key = Scale(root=2, mode=Mode.IONIAN)
    dur = 256.0  # 64 bars (~3.1 min)
    chords = parse_progression("I:4 vi:4 ii:4 V7:4 iii:4 vi:4 ii:4 V7:4 " * 8, key)

    drums = make_jazz_drums(dur, "lounge_swing")

    guitar_comp = make_jazz_guitar_comp(chords, key, dur, seed=707)

    bass_gen = WalkingBassGenerator(
        params=GeneratorParams(key_range_low=32, key_range_high=52),
        approach_style="mixed",
    )
    bass = bass_gen.render(chords, key, dur)

    vibes = make_vibes_melody(chords, key, dur, seed=707)
    soprano_sax = make_swing_solo(chords, key, dur, seed=707, instrument_octave=5)

    # Arrangement
    guitar_comp = keep_in_range(guitar_comp, 0.0, 256.0)
    bass = keep_in_range(bass, 16.0, 240.0)
    drums = keep_in_range(drums, 32.0, 240.0)
    vibes = keep_in_range(vibes, 32.0, 224.0)
    soprano_sax = keep_in_range(soprano_sax, 64.0, 208.0)

    for n in vibes:
        n.scale_velocity(1.3)
    for n in soprano_sax:
        n.scale_velocity(1.25)

    tracks = {
        "drums": drums,
        "jazz_guitar": guitar_comp,
        "bass": bass,
        "vibraphone": vibes,
        "soprano_sax": soprano_sax,
    }
    instruments = {
        "drums": DRUMS,
        "jazz_guitar": JAZZ_GUITAR,
        "bass": ACOUSTIC_BASS,
        "vibraphone": VIBRAPHONE,
        "soprano_sax": SOPRANO_SAX,
    }

    parts = [IdeaPart(name="Cocktail Lounge Swing", bars=64, tempo=124, time_signature=(4, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=124, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=124.0,
        instruments=instruments,
        path=OUT / "07_Cocktail_Lounge_Swing.mid",
        mood=Mood.INTIMATE,
        key=key,
        genre="neosoul",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ---------------------------------------------------------------------
# Track 8: Sugar Cane Bossa — 132 BPM — A Major
# ---------------------------------------------------------------------
def produce_08_sugar_cane_bossa():
    print("  08. Sugar Cane Bossa [A Major — 132 BPM]")
    key = Scale(root=9, mode=Mode.IONIAN)
    dur = 256.0  # 64 bars (~2.9 min)
    chords = parse_progression("I:4 II7:4 ii:4 V7:4 I:4 VI7:4 ii:4 V7:4 " * 8, key)

    drums = make_jazz_drums(dur, "bossa_nova")

    guitar_comp = make_jazz_guitar_comp(chords, key, dur, seed=808)

    bass_gen = WalkingBassGenerator(
        params=GeneratorParams(key_range_low=32, key_range_high=52),
        approach_style="diatonic",
    )
    bass = bass_gen.render(chords, key, dur)

    comp_gen = PianoCompGenerator(
        GeneratorParams(density=0.6, key_range_low=52, key_range_high=76),
        comp_style="bossa",
        accent_pattern="syncopated",
    )
    piano = comp_gen.render(chords, key, dur)

    flute = make_swing_solo(chords, key, dur, seed=808, instrument_octave=6)

    # Arrangement
    guitar_comp = keep_in_range(guitar_comp, 0.0, 256.0)
    piano = keep_in_range(piano, 16.0, 240.0)
    bass = keep_in_range(bass, 16.0, 240.0)
    drums = keep_in_range(drums, 32.0, 240.0)
    flute = keep_in_range(flute, 32.0, 224.0)

    for n in flute:
        n.scale_velocity(1.35)

    tracks = {
        "drums": drums,
        "jazz_guitar": guitar_comp,
        "piano": piano,
        "bass": bass,
        "flute": flute,
    }
    instruments = {
        "drums": DRUMS,
        "jazz_guitar": JAZZ_GUITAR,
        "piano": ACOUSTIC_PIANO,
        "bass": ACOUSTIC_BASS,
        "flute": FLUTE,
    }

    parts = [IdeaPart(name="Sugar Cane Bossa", bars=64, tempo=132, time_signature=(4, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=132, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=132.0,
        instruments=instruments,
        path=OUT / "08_Sugar_Cane_Bossa.mid",
        mood=Mood.INTIMATE,
        key=key,
        genre="neosoul",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ---------------------------------------------------------------------
# Track 9: Midnight Jam Session — 165 BPM — F Blues
# ---------------------------------------------------------------------
def produce_09_midnight_jam_session():
    print("  09. Midnight Jam Session [F Blues — 165 BPM]")
    key = Scale(root=5, mode=Mode.MIXOLYDIAN)
    dur = 288.0  # 72 bars (~2.6 min)
    chords = parse_progression("I7:4 IV7:4 I7:4 I7:4 IV7:4 IV7:4 I7:4 I7:4 V7:4 IV7:4 I7:4 V7:4 " * 6, key)

    drums = make_jazz_drums(dur, "fast_swing")

    bass_gen = WalkingBassGenerator(
        params=GeneratorParams(key_range_low=32, key_range_high=55),
        approach_style="mixed",
    )
    bass = bass_gen.render(chords, key, dur)

    comp_gen = PianoCompGenerator(
        GeneratorParams(density=0.7, key_range_low=50, key_range_high=74),
        comp_style="jazz",
        accent_pattern="charleston",
    )
    piano = comp_gen.render(chords, key, dur)

    tenor_sax_solo = make_swing_solo(chords, key, dur, seed=909, instrument_octave=5)
    trumpet_solo = make_swing_solo(chords, key, dur, seed=910, instrument_octave=5)

    # Arrangement (Call & Response / Trading Solos)
    piano = keep_in_range(piano, 0.0, 288.0)
    bass = keep_in_range(bass, 0.0, 288.0)
    drums = keep_in_range(drums, 16.0, 272.0)
    tenor_sax_solo = keep_in_range(tenor_sax_solo, 32.0, 144.0) + keep_in_range(tenor_sax_solo, 240.0, 272.0)
    trumpet_solo = keep_in_range(trumpet_solo, 144.0, 272.0)

    for n in tenor_sax_solo:
        n.scale_velocity(1.3)
    for n in trumpet_solo:
        n.scale_velocity(1.3)

    tracks = {
        "drums": drums,
        "walking_bass": bass,
        "piano": piano,
        "tenor_sax": tenor_sax_solo,
        "trumpet": trumpet_solo,
    }
    instruments = {
        "drums": DRUMS,
        "walking_bass": ACOUSTIC_BASS,
        "piano": ACOUSTIC_PIANO,
        "tenor_sax": TENOR_SAX,
        "trumpet": TRUMPET,
    }

    parts = [IdeaPart(name="Midnight Jam Session", bars=72, tempo=165, time_signature=(4, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=165, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=165.0,
        instruments=instruments,
        path=OUT / "09_Midnight_Jam_Session.mid",
        mood=Mood.CHAMBER,
        key=key,
        genre="neosoul",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ---------------------------------------------------------------------
# Track 10: Last Call at Benny's — 152 BPM — C Major
# ---------------------------------------------------------------------
def produce_10_last_call_at_bennys():
    print("  10. Last Call at Benny's [C Major — 152 BPM]")
    key = Scale(root=0, mode=Mode.IONIAN)
    dur = 256.0  # 64 bars (~2.5 min)
    chords = parse_progression("I:4 vi:4 ii:4 V7:4 I:4 IV:4 V7:4 I:4 " * 8, key)

    drums = make_jazz_drums(dur, "big_band_shout")

    stride_gen = StridePianoGenerator(
        GeneratorParams(density=0.8, key_range_low=36, key_range_high=84),
        pattern="standard",
    )
    piano = stride_gen.render(chords, key, dur)

    bass_gen = WalkingBassGenerator(
        params=GeneratorParams(key_range_low=32, key_range_high=55),
        approach_style="mixed",
    )
    bass = bass_gen.render(chords, key, dur)

    brass_section = make_brass_stabs(chords, key, dur, seed=1010)
    alto_sax = make_swing_solo(chords, key, dur, seed=1010, instrument_octave=5)

    # Arrangement
    piano = keep_in_range(piano, 0.0, 256.0)
    bass = keep_in_range(bass, 16.0, 240.0)
    drums = keep_in_range(drums, 32.0, 256.0)
    alto_sax = keep_in_range(alto_sax, 32.0, 224.0)
    brass_section = keep_in_range(brass_section, 64.0, 240.0)

    for n in alto_sax:
        n.scale_velocity(1.3)
    for n in brass_section:
        n.scale_velocity(1.35)

    tracks = {
        "drums": drums,
        "piano": piano,
        "walking_bass": bass,
        "brass_section": brass_section,
        "alto_sax": alto_sax,
    }
    instruments = {
        "drums": DRUMS,
        "piano": ACOUSTIC_PIANO,
        "walking_bass": ACOUSTIC_BASS,
        "brass_section": TRUMPET,
        "alto_sax": ALTO_SAX,
    }

    parts = [IdeaPart(name="Last Call at Benny's", bars=64, tempo=152, time_signature=(4, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=152, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=152.0,
        instruments=instruments,
        path=OUT / "10_Last_Call_at_Bennys.mid",
        mood=Mood.CHAMBER,
        key=key,
        genre="neosoul",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
        skip_stages=["texture", "polyphony", "sections"],
        psycho_verify_enabled=False,
    )


# ------------------------------------------------------------------
# Main Album Loop
# ------------------------------------------------------------------
def main():
    print("\n" + "=" * 80)
    print("   U P T O W N   S W I N G   &   S U N N Y   G R O O V E S")
    print("   Upbeat & Cheerful Instrumental Jazz Suite")
    print("=" * 80 + "\n")

    produce_01_honeybee_stride()
    produce_02_boogie_express()
    produce_03_coconut_samba()
    produce_04_bebop_boardwalk()
    produce_05_ragtime_rollercoaster()
    produce_06_bourbon_street_jump()
    produce_07_cocktail_lounge_swing()
    produce_08_sugar_cane_bossa()
    produce_09_midnight_jam_session()
    produce_10_last_call_at_bennys()

    print("\n" + "=" * 80)
    print("   PRODUCTION COMPLETE: UPTOWN SWING & SUNNY GROOVES")
    print(f"   All 10 Jazz MIDI tracks saved to: {OUT.absolute()}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
