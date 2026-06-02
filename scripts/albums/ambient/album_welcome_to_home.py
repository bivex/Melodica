# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_welcome_to_home.py — Welcome to Home

Warm, cheerful 9-track ambient album for the Roblox game "Welcome to Home".
Every track feels like coming home — sunlight through windows, cozy rooms,
a garden in bloom, a fireplace crackling, a cup of tea on the table.

UPGRADED: Now uses the optimized Coupled HMM Harmonizer (Engine 4).
"""

import random
from pathlib import Path

import numpy as np

from melodica import types
from melodica.types import Scale, Mode, Quality, ChordLabel, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.rest import RestGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.composer import Motif, LeitmotifRegistry
from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.vst_player import VSTPlayer

# GM Programs
PIANO = 0
HARP = 46
CELLO = 42
FLUTE = 73
PAD_WARM = 89
PAD_SPACE = 91
CHOIR = 52
BOWL = 14
NYLON_GUITAR = 24
XYLOPHONE = 13
VIBRAPHONE = 11
GLOCKENSPIEL = 9
ACOUSTIC_BASS = 32

random.seed(2026)
OUT = Path("output/welcome_to_home")
OUT.mkdir(parents=True, exist_ok=True)

# Shared harmonizer
_harmonizer = CoupledHMMHarmonizer(beam_width=12, chord_change="half")

# ── Leitmotif: "Home" theme ──────────────────────────────────────────
_home_motif = Motif.from_notes([
    NoteInfo(pitch=60, start=0.0, duration=3.0, velocity=55),
    NoteInfo(pitch=64, start=3.0, duration=2.5, velocity=50),
    NoteInfo(pitch=67, start=5.5, duration=3.0, velocity=55),
    NoteInfo(pitch=69, start=8.5, duration=2.0, velocity=50),
    NoteInfo(pitch=72, start=10.5, duration=5.0, velocity=55),
])

LM = LeitmotifRegistry()
LM.register("home", _home_motif,
            tags=["comfort", "belonging", "safe"], instrument=PIANO, velocity=50)
LM.register("home_choir", _home_motif,
            tags=["comfort", "belonging"], instrument=CHOIR, velocity=40)
LM.register("home_flute", _home_motif,
            tags=["comfort", "joy"], instrument=FLUTE, velocity=48)
LM.register("home_harp", _home_motif,
            tags=["comfort", "light"], instrument=HARP, velocity=45)
LM.register("home_bells", _home_motif,
            tags=["comfort", "memory"], instrument=BOWL, velocity=42)

# ── Surge XT VST3 preset mapping ───────────────────────────────────
SURGE_VST = "/Library/Audio/Plug-Ins/VST3/Surge XT.vst3"
SURGE_PRESETS = "/Library/Application Support/Surge XT"

VST_PRESETS = {
    "pad":   f"{SURGE_PRESETS}/patches_3rdparty/Vincent Zauhar/Pads/Classic Warm Jupiters.fxp",
    "piano": f"{SURGE_PRESETS}/patches_3rdparty/Luna/Keys/Alias Glass Piano 1.fxp",
    "harp":  f"{SURGE_PRESETS}/patches_3rdparty/Kinsey Dulcet/Plucks/No Frills Harp Pluck.fxp",
    "flute": f"{SURGE_PRESETS}/patches_3rdparty/Argitoth/Winds/Asian Flute.fxp",
    "cello": f"{SURGE_PRESETS}/patches_3rdparty/Malfunction/Strings/Solo Cello.fxp",
    "choir": f"{SURGE_PRESETS}/patches_factory/Pads/Retro Choir.fxp",
    "bowl":  f"{SURGE_PRESETS}/patches_3rdparty/Jacky Ligon/Mallets/Chimes 1.fxp",
    "guitar": f"{SURGE_PRESETS}/patches_3rdparty/John Valentine/Guitars/Nylon Acoustic Guitar.fxp",
    "glock": f"{SURGE_PRESETS}/patches_3rdparty/Jacky Ligon/Mallets/Cymbell 1.fxp",
    "vibes": f"{SURGE_PRESETS}/patches_3rdparty/Jacky Ligon/Mallets/Bass Marimba 1.fxp",
    "bass":  f"{SURGE_PRESETS}/patches_3rdparty/LinnStrument MPE/Basses/String Bass.fxp",
    "strings": f"{SURGE_PRESETS}/patches_3rdparty/LinnStrument MPE/Strings/Ensemble Strings.fxp",
    "bells": f"{SURGE_PRESETS}/patches_3rdparty/Luna/Bells/Tubular Bellsish But Less.fxp",
    "motif": f"{SURGE_PRESETS}/patches_3rdparty/Luna/Keys/Alias Glass Piano 1.fxp",
    # Alternate pad for spacey tracks
    "pad_space": f"{SURGE_PRESETS}/patches_3rdparty/TNMG/Pads/In Motion.fxp",
}


def _render_mp3(
    tracks: dict[str, list[NoteInfo]],
    path: Path,
    bpm: float,
    track_presets: dict[str, str] | None = None,
):
    """Render all tracks through Surge XT VST3 → mix → MP3."""
    import subprocess, tempfile

    sr = 44100
    presets = track_presets or VST_PRESETS
    mix_buf: np.ndarray | None = None
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.8, "harp": 0.7, "flute": 0.75, "cello": 0.55,
        "pad": 0.45, "choir": 0.5, "drone": 0.4, "bowl": 0.55,
        "guitar": 0.65, "strings": 0.55, "arp": 0.5, "bass": 0.4,
        "bells": 0.45, "vibes": 0.5, "glock": 0.4, "motif": 0.6,
        "pad_space": 0.45,
    })

    with VSTPlayer(SURGE_VST, sample_rate=sr, normalize=False) as player:
        for name, notes in tracks.items():
            if not notes:
                continue
            preset = presets.get(name)
            if not preset:
                continue
            try:
                player.load_preset(preset)
            except Exception as e:
                print(f"  [VST] preset {name}: {e}, skipping")
                continue
            audio = player.render_notes(notes, bpm=bpm)
            # Apply gain
            gain = desk.track_gains.get(name, 0.7)
            audio = audio * gain
            # Pad/trim to same length
            if mix_buf is None:
                mix_buf = np.zeros_like(audio)
            if audio.shape[1] > mix_buf.shape[1]:
                mix_buf = np.pad(mix_buf, ((0, 0), (0, audio.shape[1] - mix_buf.shape[1])))
            elif audio.shape[1] < mix_buf.shape[1]:
                audio = np.pad(audio, ((0, 0), (0, mix_buf.shape[1] - audio.shape[1])))
            mix_buf = mix_buf + audio

    if mix_buf is None:
        print(f"  [VST] no audio rendered for {path}")
        return

    # Normalize mix
    peak = np.max(np.abs(mix_buf))
    if peak > 0:
        mix_buf = mix_buf / peak * 0.9

    path = Path(path).with_suffix(".wav")
    from pedalboard.io import AudioFile
    with AudioFile(str(path), "w", sr, mix_buf.shape[0]) as f:
        f.write(mix_buf)
    print(f"  → {path} ({mix_buf.shape[1] / sr:.1f}s)")


def _off(notes, offset):
    return [
        NoteInfo(pitch=n.pitch, start=n.start + offset,
                 duration=n.duration, velocity=n.velocity)
        for n in notes
    ]


def _master(raw: dict, bpm: float, lufs: float = -18.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.8, "harp": 0.7, "flute": 0.75, "cello": 0.55,
        "pad": 0.45, "choir": 0.5, "drone": 0.4, "bowl": 0.55,
        "guitar": 0.65, "strings": 0.55, "arp": 0.5, "bass": 0.4,
        "bells": 0.45, "vibes": 0.5, "glock": 0.4,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def _export(tracks: dict, path: Path, bpm: float, key: Scale, instruments: dict,
            render_audio: bool = True, vst_overrides: dict[str, str] | None = None):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)
    if render_audio:
        print(f"  Rendering MP3 via Surge XT...")
        presets = dict(VST_PRESETS)
        if vst_overrides:
            presets.update(vst_overrides)
        _render_mp3(final_notes, path, bpm, track_presets=presets)

def _get_chords(scale: Scale, dur: float):
    # Guide melody using scale degrees to help HMM pick musical chords
    degs = scale.degrees()
    guide = [NoteInfo(pitch=60 + int(degs[0]), start=0.0, duration=dur)]
    return _harmonizer.harmonize(melody=guide, initial_scale=scale, duration_beats=dur)

# =====================================================================
def produce_01_morning_light():
    print("--- 01_Morning_Light ---")
    bpm, dur = 56, 200.0
    key = Scale(0, Mode.MAJOR)
    chords = _get_chords(key, dur)

    pad = AmbientPadGenerator(GeneratorParams(density=0.08, key_range_low=48, key_range_high=72), overlap=1.0).render(chords, key, dur)
    piano = MelodyGenerator(GeneratorParams(density=0.06, velocity_range=(45, 65)), phrase_length=12.0, note_range_low=60, note_range_high=84, register_smoothness=0.9).render(chords, key, dur - 48.0)
    piano = _off(piano, 24.0)
    bells = [NoteInfo(pitch=84, start=float(i * 25), duration=6.0, velocity=50) for i in range(8)]
    motif = LM.render("home", offset=160.0, augment_factor=1.5)

    _export({"pad": pad, "piano": piano, "bells": bells, "motif": motif}, OUT / "01_Morning_Light.mid", bpm, key, {"pad": PAD_WARM, "piano": PIANO, "bells": BOWL, "motif": PIANO})

def produce_02_open_door():
    print("--- 02_Open_Door ---")
    bpm, dur = 52, 180.0
    key = Scale(7, Mode.LYDIAN)
    chords = _get_chords(key, dur)

    harp = ArpeggiatorGenerator(GeneratorParams(density=0.12, key_range_low=60, key_range_high=84), pattern="up", note_duration=3.0).render(chords, key, dur)
    strings = StringsEnsembleGenerator(GeneratorParams(density=0.04, key_range_low=36, key_range_high=60)).render(chords, key, dur)
    flute = MelodyGenerator(GeneratorParams(density=0.05, velocity_range=(40, 58)), phrase_length=16.0, note_range_low=72, note_range_high=84, register_smoothness=0.85).render(chords, key, dur - 60.0)
    flute = _off(flute, 40.0)
    motif = LM.render("home_flute", offset=120.0, transpose=7, invert=True)

    _export({"harp": harp, "strings": strings, "flute": flute, "motif": motif}, OUT / "02_Open_Door.mid", bpm, key, {"harp": HARP, "strings": 49, "flute": FLUTE, "motif": FLUTE})

def produce_03_kitchen_warmth():
    print("--- 03_Kitchen_Warmth ---")
    bpm, dur = 60, 160.0
    key = Scale(5, Mode.LYDIAN)
    chords = _get_chords(key, dur)

    guitar = ArpeggiatorGenerator(GeneratorParams(density=0.15, key_range_low=48, key_range_high=72), pattern="up_down", note_duration=2.5).render(chords, key, dur)
    pad = AmbientPadGenerator(GeneratorParams(density=0.06, key_range_low=36, key_range_high=60), overlap=1.0).render(chords, key, dur)
    glock = MelodyGenerator(GeneratorParams(density=0.07, velocity_range=(35, 55)), phrase_length=8.0, note_range_low=72, note_range_high=96, register_smoothness=0.8).render(chords, key, dur - 40.0)
    glock = _off(glock, 24.0)
    motif = LM.render("home_bells", offset=100.0, transpose=5, fragment_start=0.0, fragment_end=5.5, sequence_intervals=[0, 4], sequence_spacing=12.0)

    _export({"guitar": guitar, "pad": pad, "glock": glock, "motif": motif}, OUT / "03_Kitchen_Warmth.mid", bpm, key, {"guitar": NYLON_GUITAR, "pad": PAD_WARM, "glock": GLOCKENSPIEL, "motif": BOWL})

def produce_04_garden_outside():
    print("--- 04_Garden_Outside ---")
    bpm, dur = 64, 180.0
    key = Scale(2, Mode.MAJOR)
    chords = _get_chords(key, dur)

    flute = MelodyGenerator(GeneratorParams(density=0.08, velocity_range=(45, 65)), phrase_length=12.0, note_range_low=72, note_range_high=84, register_smoothness=0.85, harmony_note_probability=0.7, steps_probability=0.85).render(chords, key, dur - 32.0)
    flute = _off(flute, 16.0)
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.12, key_range_low=60, key_range_high=84), pattern="up", note_duration=2.0).render(chords, key, dur)
    bass = DroneGenerator(GeneratorParams(density=0.01, key_range_low=36, key_range_high=38), velocity=40).render(chords, key, dur)
    motif = LM.render("home_harp", offset=140.0, transpose=2, retrograde=True, diminish_factor=1.5)

    _export({"flute": flute, "harp": harp, "bass": bass, "motif": motif}, OUT / "04_Garden_Outside.mid", bpm, key, {"flute": FLUTE, "harp": HARP, "bass": ACOUSTIC_BASS, "motif": HARP})

def produce_05_living_room():
    print("--- 05_Living_Room ---")
    bpm, dur = 54, 200.0
    key = Scale(9, Mode.DORIAN)
    chords = _get_chords(key, dur)

    pad = AmbientPadGenerator(GeneratorParams(density=0.07, key_range_low=36, key_range_high=60), overlap=1.0).render(chords, key, dur)
    piano = MelodyGenerator(GeneratorParams(density=0.05, velocity_range=(40, 60)), phrase_length=16.0, note_range_low=60, note_range_high=84, register_smoothness=0.9).render(chords, key, dur - 60.0)
    piano = _off(piano, 32.0)
    cello = DroneGenerator(GeneratorParams(density=0.01, key_range_low=36, key_range_high=40), velocity=38).render(chords, key, dur)
    choir = MelodyGenerator(GeneratorParams(density=0.03, velocity_range=(30, 48)), phrase_length=20.0, note_range_low=48, note_range_high=60, register_smoothness=0.95).render(chords, key, dur - 40.0)
    choir = _off(choir, 24.0)
    motif = LM.render("home_choir", offset=160.0, transpose=9, augment_factor=2.0)

    _export({"pad": pad, "piano": piano, "cello": cello, "choir": choir, "motif": motif}, OUT / "05_Living_Room.mid", bpm, key, {"pad": PAD_WARM, "piano": PIANO, "cello": CELLO, "choir": CHOIR, "motif": CHOIR})

def produce_06_rainy_window():
    print("--- 06_Rainy_Window ---")
    bpm, dur = 50, 220.0
    key = Scale(4, Mode.AEOLIAN)
    chords = _get_chords(key, dur)

    pad = AmbientPadGenerator(GeneratorParams(density=0.06, key_range_low=36, key_range_high=60), overlap=1.0).render(chords, key, dur)
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.08, key_range_low=60, key_range_high=84), pattern="down", note_duration=3.0).render(chords, key, dur)
    flute = MelodyGenerator(GeneratorParams(density=0.04, velocity_range=(35, 52)), phrase_length=20.0, note_range_low=72, note_range_high=84, register_smoothness=0.9).render(chords, key, dur - 64.0)
    flute = _off(flute, 48.0)
    motif = LM.render("home_choir", offset=170.0, transpose=4, invert=True, diminish_factor=1.5)

    _export({"pad": pad, "harp": harp, "flute": flute, "motif": motif}, OUT / "06_Rainy_Window.mid", bpm, key, {"pad": PAD_SPACE, "harp": HARP, "flute": FLUTE, "motif": CHOIR},
            vst_overrides={"pad": VST_PRESETS["pad_space"]})

def produce_07_sunroom():
    print("--- 07_Sunroom ---")
    bpm, dur = 58, 180.0
    key = Scale(7, Mode.MAJOR)
    chords = _get_chords(key, dur)

    guitar = ArpeggiatorGenerator(GeneratorParams(density=0.12, key_range_low=48, key_range_high=72), pattern="up", note_duration=2.0).render(chords, key, dur)
    vibes = MelodyGenerator(GeneratorParams(density=0.06, velocity_range=(40, 58)), phrase_length=12.0, note_range_low=60, note_range_high=84, register_smoothness=0.85).render(chords, key, dur - 36.0)
    vibes = _off(vibes, 20.0)
    strings = StringsEnsembleGenerator(GeneratorParams(density=0.04, key_range_low=36, key_range_high=60)).render(chords, key, dur)
    bass = DroneGenerator(GeneratorParams(density=0.01, key_range_low=36, key_range_high=38), velocity=35).render(chords, key, dur)
    motif = LM.render("home_flute", offset=130.0, transpose=7, sequence_intervals=[0, 5, -2], sequence_spacing=16.0)

    _export({"guitar": guitar, "vibes": vibes, "strings": strings, "bass": bass, "motif": motif}, OUT / "07_Sunroom.mid", bpm, key, {"guitar": NYLON_GUITAR, "vibes": VIBRAPHONE, "strings": 49, "bass": ACOUSTIC_BASS, "motif": FLUTE})

def produce_08_fireplace():
    print("--- 08_Fireplace ---")
    bpm, dur = 48, 240.0
    key = Scale(0, Mode.LYDIAN)
    chords = _get_chords(key, dur)

    pad = AmbientPadGenerator(GeneratorParams(density=0.05, key_range_low=36, key_range_high=60), overlap=1.0).render(chords, key, dur)
    piano = MelodyGenerator(GeneratorParams(density=0.04, velocity_range=(35, 55)), phrase_length=20.0, note_range_low=60, note_range_high=84, register_smoothness=0.9).render(chords, key, dur - 80.0)
    piano = _off(piano, 40.0)
    cello = DroneGenerator(GeneratorParams(density=0.01, key_range_low=36, key_range_high=40), velocity=35).render(chords, key, dur)
    choir = MelodyGenerator(GeneratorParams(density=0.03, velocity_range=(28, 45)), phrase_length=24.0, note_range_low=48, note_range_high=60, register_smoothness=0.95).render(chords, key, dur - 60.0)
    choir = _off(choir, 36.0)
    motif = LM.render("home", offset=180.0, augment_factor=2.5)

    _export({"pad": pad, "piano": piano, "cello": cello, "choir": choir, "motif": motif}, OUT / "08_Fireplace.mid", bpm, key, {"pad": PAD_WARM, "piano": PIANO, "cello": CELLO, "choir": CHOIR, "motif": PIANO})

def produce_09_goodnight():
    print("--- 09_Goodnight ---")
    bpm, dur = 44, 260.0
    key = Scale(5, Mode.MAJOR)
    chords = _get_chords(key, dur)

    pad = AmbientPadGenerator(GeneratorParams(density=0.04, key_range_low=36, key_range_high=60), overlap=1.0).render(chords, key, dur)
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.06, key_range_low=60, key_range_high=84), pattern="up", note_duration=4.0).render(chords, key, dur - 80.0)
    choir = MelodyGenerator(GeneratorParams(density=0.03, velocity_range=(25, 42)), phrase_length=24.0, note_range_low=48, note_range_high=60, register_smoothness=0.95).render(chords, key, dur - 100.0)
    choir = _off(choir, 60.0)
    bowl = [NoteInfo(pitch=72, start=float(i * 40), duration=12.0, velocity=45) for i in range(7)]
    motif_a = LM.render("home_choir", offset=200.0, transpose=5, augment_factor=1.5)
    motif_b = LM.render("home", offset=230.0, augment_factor=3.0)
    motif = motif_a + motif_b

    _export({"pad": pad, "harp": harp, "choir": choir, "bowl": bowl, "motif": motif}, OUT / "09_Goodnight.mid", bpm, key, {"pad": PAD_SPACE, "harp": HARP, "choir": CHOIR, "bowl": BOWL, "motif": CHOIR},
            vst_overrides={"pad": VST_PRESETS["pad_space"]})

def main():
    produce_01_morning_light()
    produce_02_open_door()
    produce_03_kitchen_warmth()
    produce_04_garden_outside()
    produce_05_living_room()
    produce_06_rainy_window()
    produce_07_sunroom()
    produce_08_fireplace()
    produce_09_goodnight()
    print(f"\nAlbum 'Welcome to Home' complete. Files in {OUT}/")

if __name__ == "__main__":
    main()
