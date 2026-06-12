# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_roblox_jazz.py — Pixel Jazz Club

9-track kid-friendly jazz album for Roblox. Bright, bouncy, playful.
Uses the new jazz generators: GuideTone, Enclosure, SideSlipping,
TradingFours, StopTime, WalkingBassLine, ShellVoicing.
MIDI output only.
"""

import random
from pathlib import Path

import numpy as np

from melodica import types
from melodica.types import Scale, Mode, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.guide_tone import GuideToneGenerator
from melodica.generators.enclosure import EnclosureGenerator
from melodica.generators.side_slipping import SideSlippingGenerator
from melodica.generators.trading_fours import TradingFoursGenerator
from melodica.generators.stop_time import StopTimeGenerator
from melodica.generators.walking_bass_line import WalkingBassLineGenerator
from melodica.generators.shell_voicing import ShellVoicingGenerator
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.sax_solo import SaxSoloGenerator
from melodica.generators.swing import SwingGenerator
from melodica.generators.blues_lick import BluesLickGenerator
from melodica.generators.bebop_scale import BebopScaleGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.reaper_player import ReaperPlayer

# GM Programs
PIANO = 0
EPIANO = 4
ORGAN = 16
JAZZ_GUITAR = 26
ACOUSTIC_BASS = 32
FRETLESS_BASS = 35
TRUMPET = 56
TROMBONE = 57
SOPRANO_SAX = 64
ALTO_SAX = 65
TENOR_SAX = 66
BARI_SAX = 67
CLARINET = 71
FLUTE = 73
VIBRAPHONE = 11
MARIMBA = 12
XYLOPHONE = 13
DRUMS = 0

random.seed(7777)
OUT = Path("output/roblox_jazz")
OUT.mkdir(parents=True, exist_ok=True)

_harmonizer = CoupledHMMHarmonizer(beam_width=14, chord_change="half")

# ── Surge XT VST3 render (track 01 instruments) ─────────────────────────
# Backend: REAPER batch render. REAPER loads Surge XT .fxp presets natively
# (it stores Surge's sub3 state chunk in the project), so we get real timbres
# automatically — no GUI step. ReaperPlayer splices each .fxp into a reference
# VST state block and renders headless via `REAPER -renderproject`.
SURGE_PRESETS = "/Library/Application Support/Surge XT"

# Instruments of track 01 to route through the VST (drums excluded).
_TRACK01_INSTRUMENTS: tuple[str, ...] = ("shell", "bass", "enclosure")

_TRACK01_GAINS: dict[str, float] = {
    "shell": 0.75, "bass": 0.65, "enclosure": 0.70,
}

# Real Surge XT .fxp presets per instrument (loaded natively by REAPER).
_TRACK01_FXP: dict[str, str] = {
    "shell":     f"{SURGE_PRESETS}/patches_3rdparty/Dan Maurer/Keys/FM Acoustic Piano 1.fxp",
    "bass":      f"{SURGE_PRESETS}/patches_3rdparty/Malfunction/Basses/Jazz Man.fxp",
    "enclosure": f"{SURGE_PRESETS}/patches_3rdparty/Malfunction/Brass/Clean Trumpet.fxp",
}


def _load_wav(path: str) -> np.ndarray:
    """Load a WAV (16/24/32-bit PCM) as float32 (channels, samples)."""
    import wave

    w = wave.open(path, "rb")
    n, ch, sw = w.getnframes(), w.getnchannels(), w.getsampwidth()
    raw = w.readframes(n)
    w.close()
    if sw == 2:
        a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        a = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        a = np.where(a & 0x800000, a - 0x1000000, a).astype(np.float32) / 8388608.0
    else:
        a = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2**31
    return a.reshape(-1, ch).T  # (channels, samples)


def _render_track01_mp3(
    tracks: dict[str, list[NoteInfo]],
    path: Path,
    bpm: float,
) -> None:
    """Render track 01 through Surge XT via REAPER (real .fxp presets) → MP3.

    Each instrument is rendered separately with its own .fxp preset, then mixed
    and encoded to MP3. Drums are excluded (no melodic VST).
    """
    import subprocess
    import tempfile
    import wave

    sr = 44100
    player = ReaperPlayer(sample_rate=sr)
    mix_buf: np.ndarray | None = None

    for name in _TRACK01_INSTRUMENTS:
        notes = tracks.get(name)
        if not notes:
            continue
        fxp = _TRACK01_FXP.get(name)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            stem_wav = tmp.name
        try:
            player.render_wav(notes, stem_wav, bpm=bpm, fxp=fxp)
            audio = _load_wav(stem_wav)
            print(f"  [VST] {name}: {'preset ' + Path(fxp).stem if fxp else 'default'}")
        finally:
            Path(stem_wav).unlink(missing_ok=True)

        audio = audio * _TRACK01_GAINS.get(name, 0.7)

        if mix_buf is None:
            mix_buf = audio
        else:
            len_mix, len_trk = mix_buf.shape[1], audio.shape[1]
            if len_trk > len_mix:
                mix_buf = np.pad(mix_buf, ((0, 0), (0, len_trk - len_mix)))
            elif len_trk < len_mix:
                audio = np.pad(audio, ((0, 0), (0, len_mix - len_trk)))
            mix_buf = mix_buf + audio

    if mix_buf is None:
        print("  [VST] no audio rendered for track 01")
        return

    peak = np.max(np.abs(mix_buf))
    if peak > 0:
        mix_buf = mix_buf / peak * 0.9

    assert mix_buf is not None
    mp3_path = Path(path).with_suffix(".mp3")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name
    try:
        # (channels, samples) float32 → 16-bit PCM WAV (stdlib)
        interleaved = np.clip(mix_buf.T, -1.0, 1.0)
        pcm = (interleaved * 32767.0).astype("<i2")
        with wave.open(wav_path, "wb") as w:
            w.setnchannels(mix_buf.shape[0])
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(pcm.tobytes())
        subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path,
             "-codec:a", "libmp3lame", "-b:a", "320k", str(mp3_path)],
            check=True,
            capture_output=True,
        )
        print(f"  → {mp3_path} ({mix_buf.shape[1] / sr:.1f}s)")
    finally:
        Path(wav_path).unlink(missing_ok=True)


def _off(notes, offset):
    return [NoteInfo(pitch=n.pitch, start=n.start + offset,
                     duration=n.duration, velocity=n.velocity)
            for n in notes]


def _get_chords(scale: Scale, dur: float):
    degs = scale.degrees()
    guide = [NoteInfo(pitch=60 + int(degs[0]), start=0.0, duration=dur)]
    return _harmonizer.harmonize(melody=guide, initial_scale=scale, duration_beats=dur)


def _master(raw: dict, bpm: float, lufs: float = -16.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.8, "comp": 0.65, "bass": 0.7, "sax": 0.7,
        "trumpet": 0.65, "drums": 0.55, "guide": 0.5, "shell": 0.65,
        "enclosure": 0.7, "slip": 0.7, "trade_a": 0.7, "trade_b": 0.7,
        "stop": 0.65, "walk_line": 0.7, "blues": 0.7, "bebop": 0.65,
        "vibes": 0.55, "flute": 0.6, "marimba": 0.6, "swing": 0.5,
        "melody": 0.7, "ghosts": 0.35,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def _export(tracks: dict, path: Path, bpm: float, key: Scale, instruments: dict):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)


# =====================================================================
# Track 1 — Welcome to the Club
# C Major, 140 BPM. Shell voicings + walking bass line + enclosure melody.
# Bright opener — the doors open and the jazz club comes alive.
def produce_01_welcome():
    print("--- 01_Welcome_to_the_Club ---")
    bpm, dur = 140, 128.0
    key = Scale(0, Mode.IONIAN)
    chords = _get_chords(key, dur)

    shell = ShellVoicingGenerator(
        params=GeneratorParams(density=0.07, key_range_low=54, key_range_high=72),
        voicing_type="root_shell", rhythm="charleston", voice_leading=True
    ).render(chords, key, dur)

    bass = WalkingBassLineGenerator(
        params=GeneratorParams(density=0.08, key_range_low=28, key_range_high=36),
        contour="ascending", target_note="root", passing_tones="mixed"
    ).render(chords, key, dur)

    melody = EnclosureGenerator(
        params=GeneratorParams(density=0.09, velocity_range=(55, 90), key_range_low=60, key_range_high=84),
        enclosure_type="mixed", target="chord_tones", density=0.8
    ).render(chords, key, dur - 24.0)
    melody = _off(melody, 16.0)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.08), style="jazz", groove_swing=0.67,
        fill_frequency=0.15, auto_fills=True
    ).render(chords, key, dur)

    _export({"shell": shell, "bass": bass, "enclosure": melody, "drums": drums},
            OUT / "01_Welcome_to_the_Club.mid", bpm, key,
            {"shell": PIANO, "bass": ACOUSTIC_BASS, "enclosure": TRUMPET, "drums": DRUMS})
    print("  Rendering MP3 via Surge XT...")
    _render_track01_mp3(
        {"shell": shell, "bass": bass, "enclosure": melody},
        OUT / "01_Welcome_to_the_Club.mid",
        bpm,
    )


# =====================================================================
# Track 2 — Trading Places
# F Major, 155 BPM. Trading fours between trumpet and sax. Call-and-response.
# Two instruments battling it out — playful competition.
def produce_02_trading():
    print("--- 02_Trading_Places ---")
    bpm, dur = 155, 128.0
    key = Scale(5, Mode.IONIAN)
    chords = _get_chords(key, dur)

    trade = TradingFoursGenerator(
        params=GeneratorParams(density=0.1, velocity_range=(50, 90)),
        trade_length=4, style="call_response", density=1.2,
        player_a_range=(60, 84), player_b_range=(52, 72)
    ).render(chords, key, dur)

    shell = ShellVoicingGenerator(
        params=GeneratorParams(density=0.06, key_range_low=54, key_range_high=72),
        voicing_type="rootless", rhythm="half_note", voice_leading=True
    ).render(chords, key, dur)

    bass = WalkingBassGenerator(
        GeneratorParams(density=0.07, key_range_low=28, key_range_high=36),
        approach_style="mixed", swing_eighth_ratio=0.67
    ).render(chords, key, dur)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.09), style="jazz", groove_swing=0.67,
        fill_frequency=0.2, auto_fills=True
    ).render(chords, key, dur)

    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.04), pattern="jazz", target="snare",
        ghost_velocity=30, ghost_density=0.4
    ).render(chords, key, dur)

    _export({"trade_a": trade, "shell": shell, "bass": bass, "drums": drums, "ghosts": ghosts},
            OUT / "02_Trading_Places.mid", bpm, key,
            {"trade_a": TRUMPET, "shell": EPIANO, "bass": ACOUSTIC_BASS, "drums": DRUMS, "ghosts": DRUMS})


# =====================================================================
# Track 3 — Slip and Slide
# G Dorian, 135 BPM. Side-slipping sax over guide tone comping.
# Slippery outside notes that always come back home.
def produce_03_slip_slide():
    print("--- 03_Slip_and_Slide ---")
    bpm, dur = 135, 144.0
    key = Scale(7, Mode.DORIAN)
    chords = _get_chords(key, dur)

    slip = SideSlippingGenerator(
        params=GeneratorParams(density=0.09, velocity_range=(52, 88), key_range_low=56, key_range_high=78),
        slip_direction="both", resolution_style="chromatic",
        pattern_source="mixed", phrase_length=5
    ).render(chords, key, dur - 20.0)
    slip = _off(slip, 12.0)

    guide = GuideToneGenerator(
        params=GeneratorParams(density=0.05, key_range_low=52, key_range_high=60),
        voice="both", connect=True, velocity_profile="legato"
    ).render(chords, key, dur)

    bass = WalkingBassLineGenerator(
        params=GeneratorParams(density=0.07, key_range_low=28, key_range_high=36),
        contour="scalar", target_note="root"
    ).render(chords, key, dur)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.06), style="jazz", groove_swing=0.67,
        fill_frequency=0.12, auto_fills=True
    ).render(chords, key, dur)

    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.03), pattern="jazz", target="snare",
        ghost_velocity=28, ghost_density=0.35
    ).render(chords, key, dur)

    _export({"slip": slip, "guide": guide, "bass": bass, "drums": drums, "ghosts": ghosts},
            OUT / "03_Slip_and_Slide.mid", bpm, key,
            {"slip": TENOR_SAX, "guide": VIBRAPHONE, "bass": ACOUSTIC_BASS, "drums": DRUMS, "ghosts": DRUMS})


# =====================================================================
# Track 4 — Stop Go Dance
# Bb Major, 150 BPM. Stop-time comping + bebop scale runs.
# The band stops and you dance — classic big band energy for Roblox.
def produce_04_stop_go():
    print("--- 04_Stop_Go_Dance ---")
    bpm, dur = 150, 128.0
    key = Scale(10, Mode.IONIAN)
    chords = _get_chords(key, dur)

    stop = StopTimeGenerator(
        params=GeneratorParams(density=0.08, key_range_low=54, key_range_high=72),
        pattern="shuffle", accent_note="shell", fill_last_beat=True
    ).render(chords, key, dur)

    bebop = BebopScaleGenerator(
        params=GeneratorParams(density=0.1, velocity_range=(55, 92), key_range_low=60, key_range_high=84),
        scale_type="dominant", direction="mixed", accent_chord_tones=True
    ).render(chords, key, dur - 32.0)
    bebop = _off(bebop, 20.0)

    bass = WalkingBassGenerator(
        GeneratorParams(density=0.08, key_range_low=28, key_range_high=36),
        approach_style="chromatic", swing_eighth_ratio=0.67
    ).render(chords, key, dur)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.1), style="jazz", groove_swing=0.67,
        fill_frequency=0.25, auto_fills=True
    ).render(chords, key, dur)

    _export({"stop": stop, "bebop": bebop, "bass": bass, "drums": drums},
            OUT / "04_Stop_Go_Dance.mid", bpm, key,
            {"stop": PIANO, "bebop": TRUMPET, "bass": ACOUSTIC_BASS, "drums": DRUMS})


# =====================================================================
# Track 5 — Crystal Chimes
# C Lydian, 120 BPM. Guide tone vibes + enclosure flute + shell piano.
# Dreamy, sparkly — perfect for a magical Roblox world.
def produce_05_crystal():
    print("--- 05_Crystal_Chimes ---")
    bpm, dur = 120, 160.0
    key = Scale(0, Mode.LYDIAN)
    chords = _get_chords(key, dur)

    guide = GuideToneGenerator(
        params=GeneratorParams(density=0.05, key_range_low=60, key_range_high=84),
        voice="alternate", connect=True, velocity_profile="legato"
    ).render(chords, key, dur)

    enc = EnclosureGenerator(
        params=GeneratorParams(density=0.06, velocity_range=(48, 75), key_range_low=72, key_range_high=96),
        enclosure_type="diatonic_above_below", target="guide_tones", density=0.6
    ).render(chords, key, dur - 28.0)
    enc = _off(enc, 16.0)

    shell = ShellVoicingGenerator(
        params=GeneratorParams(density=0.04, key_range_low=54, key_range_high=72),
        voicing_type="spread", rhythm="whole_note", voice_leading=True,
        include_extensions=True
    ).render(chords, key, dur)

    bass = WalkingBassLineGenerator(
        params=GeneratorParams(density=0.05, key_range_low=24, key_range_high=36),
        contour="mixed", target_note="guide_tones", passing_tones="diatonic"
    ).render(chords, key, dur)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.03), style="jazz", groove_swing=0.55,
        fill_frequency=0.08, auto_fills=True
    ).render(chords, key, dur)

    _export({"guide": guide, "enclosure": enc, "shell": shell, "bass": bass, "drums": drums},
            OUT / "05_Crystal_Chimes.mid", bpm, key,
            {"guide": VIBRAPHONE, "enclosure": FLUTE, "shell": EPIANO, "bass": FRETLESS_BASS, "drums": DRUMS})


# =====================================================================
# Track 6 — Pizza Party Blues
# Eb Blues, 130 BPM. Walking bass line + blues licks + shell comping.
# A blues for pizza-eating Robloxians. Fun and greasy.
def produce_06_pizza_blues():
    print("--- 06_Pizza_Party_Blues ---")
    bpm, dur = 130, 144.0
    key = Scale(3, Mode.BLUES)
    chords = _get_chords(key, dur)

    bass_line = WalkingBassLineGenerator(
        params=GeneratorParams(density=0.1, key_range_low=28, key_range_high=36),
        contour="mixed", target_note="root", passing_tones="chromatic"
    ).render(chords, key, dur)

    shell = ShellVoicingGenerator(
        params=GeneratorParams(density=0.07, key_range_low=54, key_range_high=72),
        voicing_type="root_shell", rhythm="freddie_green", voice_leading=True
    ).render(chords, key, dur)

    blues = BluesLickGenerator(
        GeneratorParams(density=0.09, velocity_range=(52, 88), key_range_low=60, key_range_high=84),
        lick_style="standard", phrase_length=4, rest_probability=0.2
    ).render(chords, key, dur - 32.0)
    blues = _off(blues, 20.0)

    sax = SaxSoloGenerator(
        GeneratorParams(density=0.07, velocity_range=(48, 82), key_range_low=56, key_range_high=78),
        style="bebop", blues_notes=True, chromaticism=0.5
    ).render(chords, key, dur - 56.0)
    sax = _off(sax, 40.0)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.08), style="jazz", groove_swing=0.67,
        fill_frequency=0.18, auto_fills=True
    ).render(chords, key, dur)

    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.04), pattern="jazz", target="snare",
        ghost_velocity=32, ghost_density=0.45
    ).render(chords, key, dur)

    _export({"shell": shell, "bass": bass_line, "blues": blues, "sax": sax, "drums": drums, "ghosts": ghosts},
            OUT / "06_Pizza_Party_Blues.mid", bpm, key,
            {"shell": PIANO, "bass": ACOUSTIC_BASS, "blues": TRUMPET, "sax": TENOR_SAX, "drums": DRUMS, "ghosts": DRUMS})


# =====================================================================
# Track 7 — Escalation Station
# D Mixolydian, 160 BPM. Trading fours escalating + stop-time + enclosure.
# Energy builds and builds — the train is leaving the station!
def produce_07_escalation():
    print("--- 07_Escalation_Station ---")
    bpm, dur = 160, 112.0
    key = Scale(2, Mode.MIXOLYDIAN)
    chords = _get_chords(key, dur)

    trade = TradingFoursGenerator(
        params=GeneratorParams(density=0.12, velocity_range=(50, 95)),
        trade_length=4, style="escalating", density=1.4,
        player_a_range=(58, 82), player_b_range=(52, 66)
    ).render(chords, key, dur)

    stop = StopTimeGenerator(
        params=GeneratorParams(density=0.06, key_range_low=54, key_range_high=60),
        pattern="big_four", accent_note="root", fill_last_beat=True
    ).render(chords, key, dur)

    enc = EnclosureGenerator(
        params=GeneratorParams(density=0.08, velocity_range=(52, 90), key_range_low=60, key_range_high=84),
        enclosure_type="double_chromatic", target="all", density=0.9
    ).render(chords, key, dur - 24.0)
    enc = _off(enc, 16.0)

    bass = WalkingBassLineGenerator(
        params=GeneratorParams(density=0.09, key_range_low=24, key_range_high=36),
        contour="arpeggiated", target_note="root", passing_tones="chromatic"
    ).render(chords, key, dur)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.11), style="jazz", groove_swing=0.67,
        fill_frequency=0.22, auto_fills=True
    ).render(chords, key, dur)

    _export({"trade_a": trade, "stop": stop, "enclosure": enc, "bass": bass, "drums": drums},
            OUT / "07_Escalation_Station.mid", bpm, key,
            {"trade_a": TRUMPET, "stop": PIANO, "enclosure": ALTO_SAX, "bass": ACOUSTIC_BASS, "drums": DRUMS})


# =====================================================================
# Track 8 — Starlight Lounge
# Ab Major, 105 BPM. Side-slipping flute + guide tones + shell spread.
# Chill evening in the Roblox jazz lounge. Smooth and sparkly.
def produce_08_starlight():
    print("--- 08_Starlight_Lounge ---")
    bpm, dur = 105, 176.0
    key = Scale(8, Mode.IONIAN)
    chords = _get_chords(key, dur)

    slip = SideSlippingGenerator(
        params=GeneratorParams(density=0.05, velocity_range=(46, 72), key_range_low=72, key_range_high=96),
        slip_direction="both", resolution_style="scale",
        pattern_source="scale", phrase_length=6
    ).render(chords, key, dur - 32.0)
    slip = _off(slip, 20.0)

    guide = GuideToneGenerator(
        params=GeneratorParams(density=0.04, key_range_low=52, key_range_high=60),
        voice="both", connect=True, velocity_profile="legato"
    ).render(chords, key, dur)

    shell = ShellVoicingGenerator(
        params=GeneratorParams(density=0.04, key_range_low=54, key_range_high=60),
        voicing_type="B_form", rhythm="syncopated", voice_leading=True,
        drop_2=True, include_extensions=True
    ).render(chords, key, dur)

    bass = WalkingBassGenerator(
        GeneratorParams(density=0.05, key_range_low=24, key_range_high=36),
        approach_style="diatonic", swing_eighth_ratio=0.55
    ).render(chords, key, dur)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.03), style="jazz", groove_swing=0.55,
        fill_frequency=0.06, auto_fills=True
    ).render(chords, key, dur)

    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.02), pattern="jazz", target="snare",
        ghost_velocity=22, ghost_density=0.25
    ).render(chords, key, dur)

    _export({"slip": slip, "guide": guide, "shell": shell, "bass": bass, "drums": drums, "ghosts": ghosts},
            OUT / "08_Starlight_Lounge.mid", bpm, key,
            {"slip": FLUTE, "guide": VIBRAPHONE, "shell": EPIANO, "bass": FRETLESS_BASS, "drums": DRUMS, "ghosts": DRUMS})


# =====================================================================
# Track 9 — Pixel Jazz Finale
# F Major, 170 BPM. Full band using ALL new generators.
# Everyone plays — the grand finale of the Pixel Jazz Club.
def produce_09_finale():
    print("--- 09_Pixel_Jazz_Finale ---")
    bpm, dur = 170, 136.0
    key = Scale(5, Mode.IONIAN)
    chords = _get_chords(key, dur)

    shell = ShellVoicingGenerator(
        params=GeneratorParams(density=0.08, key_range_low=54, key_range_high=72),
        voicing_type="root_shell", rhythm="charleston", voice_leading=True
    ).render(chords, key, dur)

    guide = GuideToneGenerator(
        params=GeneratorParams(density=0.04, key_range_low=52, key_range_high=60),
        voice="alternate", connect=True
    ).render(chords, key, dur)

    trade = TradingFoursGenerator(
        params=GeneratorParams(density=0.1, velocity_range=(52, 92)),
        trade_length=4, style="escalating", density=1.2,
        player_a_range=(60, 84), player_b_range=(52, 72)
    ).render(chords, key, dur - 48.0)
    trade = _off(trade, 32.0)

    enc = EnclosureGenerator(
        params=GeneratorParams(density=0.07, velocity_range=(50, 85), key_range_low=60, key_range_high=84),
        enclosure_type="mixed", target="guide_tones", density=0.7
    ).render(chords, key, dur - 72.0)
    enc = _off(enc, 52.0)

    bass = WalkingBassLineGenerator(
        params=GeneratorParams(density=0.09, key_range_low=28, key_range_high=36),
        contour="mixed", target_note="root", passing_tones="mixed"
    ).render(chords, key, dur)

    bebop = BebopScaleGenerator(
        params=GeneratorParams(density=0.08, velocity_range=(50, 88), key_range_low=72, key_range_high=96),
        scale_type="major", direction="ascending", accent_chord_tones=True
    ).render(chords, key, dur - 56.0)
    bebop = _off(bebop, 40.0)

    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.1), style="jazz", groove_swing=0.67,
        fill_frequency=0.2, auto_fills=True
    ).render(chords, key, dur)

    ghosts = GhostNotesGenerator(
        GeneratorParams(density=0.05), pattern="jazz", target="snare",
        ghost_velocity=32, ghost_density=0.45
    ).render(chords, key, dur)

    _export({
        "shell": shell, "guide": guide, "trade_a": trade,
        "enclosure": enc, "bass": bass, "bebop": bebop,
        "drums": drums, "ghosts": ghosts,
    }, OUT / "09_Pixel_Jazz_Finale.mid", bpm, key, {
        "shell": PIANO, "guide": MARIMBA, "trade_a": TRUMPET,
        "enclosure": ALTO_SAX, "bass": ACOUSTIC_BASS, "bebop": FLUTE,
        "drums": DRUMS, "ghosts": DRUMS,
    })


def main():
    produce_01_welcome()
    produce_02_trading()
    produce_03_slip_slide()
    produce_04_stop_go()
    produce_05_crystal()
    produce_06_pizza_blues()
    produce_07_escalation()
    produce_08_starlight()
    produce_09_finale()
    print(f"\nAlbum 'Pixel Jazz Club' complete. Files in {OUT}/")


if __name__ == "__main__":
    main()
