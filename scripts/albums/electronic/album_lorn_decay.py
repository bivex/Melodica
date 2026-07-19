# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/electronic/album_lorn_decay.py — "Decay" Album.

A dark, heavy, melancholic electronic album in the style of Lorn.
Features slow, dragging halftime rhythms, deep analog sliding sub-bass (808s), detuned synth pads,
distorted vocal chops, and gritty machine glitch textures.
Leverages the new core-level tempo_profile configurations for natural, breathing tempo automation.
All tracks are extended to a full, professional length (2 to 3 minutes each) with gradual staggering.

Tracks:
  1. Acid Rain    — 165 BPM (halftime feel) — C Phrygian (agitato tempo map)
  2. Grave Dirt    — 84 BPM                  — D Aeolian (rubato tempo map)
  3. Iron Lungs   — 132 BPM                 — E Locrian (industrial tempo map)
  4. Sega Sunset  — 96 BPM                  — A Harmonic Minor (chaotic tempo map)
  5. Dystopia     — 110 BPM                 — F Hungarian Minor (madness tempo map)
  6. Decay        — 72 BPM                  — B Phrygian (requiem tempo map)
"""

import random
from pathlib import Path
import math

from melodica.types import Scale, Mode, ChordLabel, NoteInfo, parse_progression
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.witch_house import WitchHouseGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.composer.tempo_modulator import TempoModulator
from melodica.idea_tool import IdeaPart
from melodica.fluid_r3_profile import FLUID_R3_PROGRAMS

# ------------------------------------------------------------------
# GM Instruments Mapping
# ------------------------------------------------------------------
PIANO = 0
SYNTH_BASS = 38
SYNTH_PAD = 89
SYNTH_LEAD = 80
SYNTH_CHOIR = 52
DRUMS = 0

random.seed(2026)
OUT = Path("output/album_lorn_decay")
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
# Intercepting WitchHouseGenerator for accurate track routing
# ------------------------------------------------------------------
class InterceptWitchHouseGenerator(WitchHouseGenerator):
    def render_separated(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float
    ) -> dict[str, list[NoteInfo]]:
        pads_list = []
        bass_list = []
        drums_list = []

        orig_pad = self._render_pad
        orig_bass = self._render_bass
        orig_drums = self._render_drums

        self._render_pad = lambda notes, *args: orig_pad(pads_list, *args)
        self._render_bass = lambda notes, *args: orig_bass(bass_list, *args)
        self._render_drums = lambda notes, *args: orig_drums(drums_list, *args)

        self.render(chords, key, duration_beats)

        self._render_pad = orig_pad
        self._render_bass = orig_bass
        self._render_drums = orig_drums

        return {"pads": pads_list, "synth_bass": bass_list, "drums": drums_list}


# ------------------------------------------------------------------
# Track 1: Acid Rain — 165 BPM (halftime 82.5) — C Phrygian
# ------------------------------------------------------------------
def produce_acid_rain():
    print("  1. Acid Rain [C Phrygian — 165 BPM]")
    key = Scale(root=0, mode=Mode.PHRYGIAN)
    dur = 384.0  # 96 bars (approx. 2.3 minutes)
    chords = parse_progression("i:4 VI:4 iv:4 v:4 " * 24, key)

    # 1. Halftime Occult Witch House drums
    wh_gen = InterceptWitchHouseGenerator(
        variant="occult",
        slowdown_factor=0.5,
    )
    parted = wh_gen.render_separated(chords, key, dur)
    drums = parted["drums"]

    # 2. Deep heavy industrial bass
    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        mode="industrial",
        octave=2,
        note_duration=2.0,
        velocity_level=0.8,
    )
    bass = bass_gen.render(chords, key, dur)

    # 3. Detuned hollow analog pads
    pad_gen = DarkPadGenerator(
        mode="phrygian_pad",
        chord_dur=4.0,
    )
    pads = pad_gen.render(chords, key, dur)

    # 4. Melancholic high-tension lead
    lead_gen = MelodyGenerator(
        params=GeneratorParams(key_range_low=60, key_range_high=80),
        phrase_length=4.0,
        phrase_rest_probability=0.4,
    )
    leads = lead_gen.render(chords, key, dur)

    # Mix balancing & Staggering entrances
    for n in pads:
        n.scale_velocity(1.4)
    for n in leads:
        n.scale_velocity(1.5)

    # Gradual build-up for the extended track length
    bass = [n for n in bass if n.start >= 64.0]    # bass enters bar 16 (64 beats)
    drums = [n for n in drums if n.start >= 128.0]  # drums enter bar 32 (128 beats)
    leads = [n for n in leads if n.start >= 192.0]  # lead enters bar 48 (192 beats)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "pads": pads,
        "leads": leads,
    }

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "pads": SYNTH_PAD,
        "leads": SYNTH_LEAD,
    }

    # Generate core tempo events
    parts = [IdeaPart(name="Acid Rain", bars=96, tempo=165, time_signature=(4, 4), tempo_profile="agitato")]
    modulator = TempoModulator(default_tempo=165, tempo_profile="agitato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=165.0,
        instruments=inst,
        path=OUT / "01_Acid_Rain.mid",
        mood=Mood.EXPERIMENTAL,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
    )


# ------------------------------------------------------------------
# Track 2: Grave Dirt — 84 BPM — D Aeolian
# ------------------------------------------------------------------
def produce_grave_dirt():
    print("  2. Grave Dirt [D Aeolian — 84 BPM]")
    key = Scale(root=2, mode=Mode.AEOLIAN)
    dur = 192.0  # 64 bars of 3/4 (approx. 2.3 minutes)
    chords = parse_progression("i:3 III:3 VI:3 VII:3 " * 16, key)

    # 1. Dark ambient halftime drums
    wh_gen = InterceptWitchHouseGenerator(
        variant="dark_ambient",
        slowdown_factor=0.5,
    )
    parted = wh_gen.render_separated(chords, key, dur)
    drums = parted["drums"]

    # 2. Slow heavy doom sub bass
    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        mode="doom",
        octave=1,
        note_duration=3.0,
        velocity_level=0.9,
    )
    bass = bass_gen.render(chords, key, dur)

    # 3. Ominous background pads
    pad_gen = DarkPadGenerator(
        mode="tritone_drone",
        chord_dur=6.0,
    )
    pads = pad_gen.render(chords, key, dur)

    # 4. Reversed/syncopated vocal chop leads
    vocal_gen = VocalChopsGenerator(
        params=GeneratorParams(key_range_low=58, key_range_high=74),
        processing="reverse",
        density=0.5,
        source_pitch=64,
        chop_pattern="syncopated",
    )
    leads = vocal_gen.render(chords, key, dur)

    for n in pads:
        n.scale_velocity(1.3)
    for n in leads:
        n.scale_velocity(1.4)

    bass = [n for n in bass if n.start >= 48.0]    # bass enters bar 16 (48 beats)
    drums = [n for n in drums if n.start >= 96.0]  # drums enter bar 32 (96 beats)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "pads": pads,
        "leads": leads,
    }

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "pads": SYNTH_PAD,
        "leads": SYNTH_CHOIR,
    }

    parts = [IdeaPart(name="Grave Dirt", bars=64, tempo=84, time_signature=(3, 4), tempo_profile="rubato")]
    modulator = TempoModulator(default_tempo=84, tempo_profile="rubato")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=84.0,
        instruments=inst,
        path=OUT / "02_Grave_Dirt.mid",
        mood=Mood.INTIMATE,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(3, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
    )


# ------------------------------------------------------------------
# Track 3: Iron Lungs — 132 BPM — E Locrian
# ------------------------------------------------------------------
def produce_iron_lungs():
    print("  3. Iron Lungs [E Locrian — 132 BPM]")
    key = Scale(root=4, mode=Mode.LOCRIAN)
    dur = 320.0  # 80 bars (approx. 2.4 minutes)
    chords = parse_progression("idim:4 bII:4 vdim:4 bII:4 " * 20, key)

    # 1. Aggressive occult drums
    wh_gen = InterceptWitchHouseGenerator(
        variant="occult",
        slowdown_factor=0.7,
    )
    parted = wh_gen.render_separated(chords, key, dur)
    drums = parted["drums"]

    # 2. Percussive mechanical industrial bass
    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        mode="industrial",
        octave=2,
        note_duration=1.0,
        velocity_level=0.8,
    )
    bass = bass_gen.render(chords, key, dur)

    # 3. Dissonant machine drone
    drone_gen = DroneGenerator(
        params=GeneratorParams(key_range_low=48, key_range_high=60),
        variant="power",
    )
    pads = drone_gen.render(chords, key, dur)

    # 4. Glitchy stuttered vocal chops
    vocal_gen = VocalChopsGenerator(
        params=GeneratorParams(key_range_low=58, key_range_high=70),
        processing="stutter",
        density=0.7,
        source_pitch=58,
        chop_pattern="offbeat",
    )
    leads = vocal_gen.render(chords, key, dur)

    for n in pads:
        n.scale_velocity(1.2)
    for n in leads:
        n.scale_velocity(1.5)

    bass = [n for n in bass if n.start >= 80.0]     # bass enters bar 20 (80 beats)
    leads = [n for n in leads if n.start >= 160.0]  # vocal chops enter bar 40 (160 beats)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "pads": pads,
        "leads": leads,
    }

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "pads": SYNTH_PAD,
        "leads": SYNTH_CHOIR,
    }

    parts = [IdeaPart(name="Iron Lungs", bars=80, tempo=132, time_signature=(4, 4), tempo_profile="industrial")]
    modulator = TempoModulator(default_tempo=132, tempo_profile="industrial")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=132.0,
        instruments=inst,
        path=OUT / "03_Iron_Lungs.mid",
        mood=Mood.EXPERIMENTAL,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
    )


# ------------------------------------------------------------------
# Track 4: Sega Sunset — 96 BPM — A Harmonic Minor
# ------------------------------------------------------------------
def produce_sega_sunset():
    print("  4. Sega Sunset [A Harmonic Minor — 96 BPM]")
    key = Scale(root=9, mode=Mode.HARMONIC_MINOR)
    dur = 256.0  # 64 bars (approx. 2.7 minutes)
    chords = parse_progression("i:4 iv:4 V7:4 i:4 " * 16, key)

    # 1. Slow dragged drag-style drums
    wh_gen = InterceptWitchHouseGenerator(
        variant="drag",
        slowdown_factor=0.4,
    )
    parted = wh_gen.render_separated(chords, key, dur)
    drums = parted["drums"]

    # 2. Deep sub-bass with space and echo gaps (dub style)
    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        mode="dub",
        octave=1,
        note_duration=4.0,
        velocity_level=0.9,
    )
    bass = bass_gen.render(chords, key, dur)

    # 3. Detuned spacey pads
    pad_gen = DarkPadGenerator(
        mode="dim_cluster",
        chord_dur=8.0,
    )
    pads = pad_gen.render(chords, key, dur)

    # 4. Eerie rising and falling arpeggiator keys
    arp_gen = ArpeggiatorGenerator(
        params=GeneratorParams(key_range_low=60, key_range_high=84),
        pattern="up_down",
        note_duration=0.25,
    )
    leads = arp_gen.render(chords, key, dur)

    for n in pads:
        n.scale_velocity(1.4)
    for n in leads:
        n.scale_velocity(1.5)

    bass = [n for n in bass if n.start >= 64.0]     # bass enters bar 16 (64 beats)
    drums = [n for n in drums if n.start >= 128.0]  # drums enter bar 32 (128 beats)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "pads": pads,
        "leads": leads,
    }

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "pads": SYNTH_PAD,
        "leads": SYNTH_LEAD,
    }

    parts = [IdeaPart(name="Sega Sunset", bars=64, tempo=96, time_signature=(4, 4), tempo_profile="chaotic")]
    modulator = TempoModulator(default_tempo=96, tempo_profile="chaotic")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=96.0,
        instruments=inst,
        path=OUT / "04_Sega_Sunset.mid",
        mood=Mood.AMBIENT,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
    )


# ------------------------------------------------------------------
# Track 5: Dystopia — 110 BPM — F Hungarian Minor
# ------------------------------------------------------------------
def produce_dystopia():
    print("  5. Dystopia [F Hungarian Minor — 110 BPM]")
    key = Scale(root=5, mode=Mode.HUNGARIAN_MINOR)
    dur = 288.0  # 72 bars (approx. 2.6 minutes)
    chords = parse_progression("i:4 iv:4 vdim:4 i:4 " * 18, key)

    # 1. Massive aggressive drums
    wh_gen = InterceptWitchHouseGenerator(
        variant="occult",
        slowdown_factor=0.6,
    )
    parted = wh_gen.render_separated(chords, key, dur)
    drums = parted["drums"]

    # 2. Pulsing heavy detuned bass
    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        mode="dark_pulse",
        octave=2,
        note_duration=2.0,
        velocity_level=0.8,
    )
    bass = bass_gen.render(chords, key, dur)

    # 3. Thick analog wall pad
    pad_gen = DarkPadGenerator(
        mode="chromatic_pad",
        chord_dur=4.0,
    )
    pads = pad_gen.render(chords, key, dur)

    # 4. Piercing distorted lead melody
    lead_gen = MelodyGenerator(
        params=GeneratorParams(key_range_low=58, key_range_high=86),
        phrase_length=8.0,
        phrase_rest_probability=0.3,
    )
    leads = lead_gen.render(chords, key, dur)

    for n in pads:
        n.scale_velocity(1.3)
    for n in leads:
        n.scale_velocity(1.6)

    drums = [n for n in drums if n.start >= 64.0]    # drums enter bar 16 (64 beats)
    leads = [n for n in leads if n.start >= 144.0]  # lead enters bar 36 (144 beats)

    tracks = {
        "drums": drums,
        "synth_bass": bass,
        "pads": pads,
        "leads": leads,
    }

    inst = {
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
        "pads": SYNTH_PAD,
        "leads": SYNTH_LEAD,
    }

    parts = [IdeaPart(name="Dystopia", bars=72, tempo=110, time_signature=(4, 4), tempo_profile="madness")]
    modulator = TempoModulator(default_tempo=110, tempo_profile="madness")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=110.0,
        instruments=inst,
        path=OUT / "05_Dystopia.mid",
        mood=Mood.CINEMATIC,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(4, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
    )


# ------------------------------------------------------------------
# Track 6: Decay — 72 BPM — B Phrygian
# ------------------------------------------------------------------
def produce_decay():
    print("  6. Decay [B Phrygian — 72 BPM]")
    key = Scale(root=11, mode=Mode.PHRYGIAN)
    dur = 144.0  # 48 bars of 3/4 (approx. 2.0 minutes)
    chords = parse_progression("i:3 iv:3 v:3 i:3 " * 12, key)

    # 1. Slow, long sustained doom sub-bass
    bass_gen = DarkBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        mode="doom",
        octave=1,
        note_duration=6.0,
        velocity_level=0.9,
    )
    bass = bass_gen.render(chords, key, dur)

    # 2. Ethereal atmospheric clean drone
    drone_gen = DroneGenerator(
        params=GeneratorParams(key_range_low=36, key_range_high=48),
        variant="octave",
    )
    pads = drone_gen.render(chords, key, dur)

    # 3. Floating, sparse, melancholic melody
    lead_gen = MelodyGenerator(
        params=GeneratorParams(key_range_low=60, key_range_high=72),
        phrase_length=6.0,
        phrase_rest_probability=0.5,
    )
    leads = lead_gen.render(chords, key, dur)

    # No drums for this track — it's a decaying ambient coda

    for n in pads:
        n.scale_velocity(1.4)
    for n in leads:
        n.scale_velocity(1.5)

    bass = [n for n in bass if n.start >= 36.0]   # bass enters bar 12 (36 beats)
    leads = [n for n in leads if n.start >= 72.0]  # melody enters bar 24 (72 beats)

    tracks = {
        "synth_bass": bass,
        "pads": pads,
        "leads": leads,
    }

    inst = {
        "synth_bass": SYNTH_BASS,
        "pads": SYNTH_PAD,
        "leads": SYNTH_LEAD,
    }

    parts = [IdeaPart(name="Decay", bars=48, tempo=72, time_signature=(3, 4), tempo_profile="requiem")]
    modulator = TempoModulator(default_tempo=72, tempo_profile="requiem")
    tempo_events = modulator.generate_events(parts)

    produce_track(
        tracks=tracks,
        bpm=72.0,
        instruments=inst,
        path=OUT / "06_Decay.mid",
        mood=Mood.AMBIENT,
        key=key,
        genre="trap",
        tempo_events=tempo_events,
        time_signature=(3, 4),
        rhythm=_PASSTHROUGH_RHYTHM,
        chords=chords,
    )


# ------------------------------------------------------------------
# Main Production Album Loop
# ------------------------------------------------------------------
def main():
    print("\n" + "=" * 80)
    print("   L O R N   —   D E C A Y   (NEW ALBUM)")
    print("   Dystopian, heavy, analog halftime electronic album")
    print("=" * 80 + "\n")

    produce_acid_rain()
    produce_grave_dirt()
    produce_iron_lungs()
    produce_sega_sunset()
    produce_dystopia()
    produce_decay()

    print("\n" + "=" * 80)
    print("   PRODUCTION COMPLETE: LORN — DECAY")
    print(f"   MIDI output saved to: {OUT.absolute()}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
