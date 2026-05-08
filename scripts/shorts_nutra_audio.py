#!/usr/bin/env python3
"""
scripts/shorts_nutra_audio.py — Audio pattern generator for YouTube Shorts (Nutra niche).

Генерирует MIDI-файлы с аудиопатернами, соответствующими требованиям Shorts:
  - 100% занятости звуком (нет тишин)
  - Хук 0–2 сек: резкий SFX/смена тональности
  - Динамика 2–80%: фоновая музыка + SFX каждые 2–4 сек
  - Лупа 2–3 сек в конце: зацикленный бит, плавный переход в начало
  - Темп быстрее обычной речи (140–180 BPM)

Использование:
    python scripts/shorts_nutra_audio.py --niche weight_loss --duration 20 --output nutra_20s.mid

 Nichе варианты:
  - weight_loss    — похудание (мотивация, цифры)
  - supplements    — БАДы, витамины
  - fitness        — тренировки, спорт
  - biohacking     — биохакер, омоложение
  - detox          — детокс, чистка организма
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import mido


# ============================================================================
# Конфигурация ниш
# ============================================================================

NICHE_CONFIG = {
    "weight_loss": {
        "tempo": 165,
        "hook_sfx": ["whoosh", "punch", "ding"],
        "background_style": "pulsing_bass",
        "sfx_interval": 2.5,
        "voice_tone": "motivational",
        "drum_kit": "trap",
    },
    "supplements": {
        "tempo": 150,
        "hook_sfx": ["sparkle", "chime", "sci-fi"],
        "background_style": "ambient_pad",
        "sfx_interval": 3.0,
        "voice_tone": "scientific",
        "drum_kit": "minimal",
    },
    "fitness": {
        "tempo": 175,
        "hook_sfx": ["drum_hit", "strike", "power"],
        "background_style": "driving_beat",
        "sfx_interval": 2.0,
        "voice_tone": "energetic",
        "drum_kit": "rock",
    },
    "biohacking": {
        "tempo": 155,
        "hook_sfx": ["cyber", "glitch", "digital"],
        "background_style": "synthwave",
        "sfx_interval": 3.5,
        "voice_tone": "calm_tech",
        "drum_kit": "four_on_floor",
    },
    "detox": {
        "tempo": 140,
        "hook_sfx": ["water", "clean", "chime"],
        "background_style": "liquid_ambient",
        "sfx_interval": 3.0,
        "voice_tone": "healing",
        "drum_kit": "tribal",
    },
}

SFX_PRESETS = {
    "whoosh": {"note": 100, "velocity": 80, "duration": 0.1},
    "punch": {"note": 60, "velocity": 100, "duration": 0.1},
    "ding": {"note": 84, "velocity": 90, "duration": 0.2},
    "sparkle": {"note": 120, "velocity": 70, "duration": 0.3},
    "chime": {"note": 96, "velocity": 85, "duration": 0.4},
    "sci-fi": {"note": 105, "velocity": 75, "duration": 0.2},
    "drum_hit": {"note": 36, "velocity": 110, "duration": 0.05},
    "strike": {"note": 38, "velocity": 100, "duration": 0.05},
    "power": {"note": 50, "velocity": 105, "duration": 0.1},
    "cyber": {"note": 110, "velocity": 70, "duration": 0.15},
    "glitch": {"note": 70, "velocity": 90, "duration": 0.05},
    "digital": {"note": 88, "velocity": 80, "duration": 0.1},
    "water": {"note": 50, "velocity": 60, "duration": 0.5},
    "clean": {"note": 60, "velocity": 65, "duration": 0.4},
    "tribal": {"note": 45, "velocity": 95, "duration": 0.1},
}

BASSLINE_PATTERNS = {
    "pulsing_bass": [
        (0.0, 36),
        (0.25, 36),
        (0.5, 36),
        (0.75, 36),
        (1.0, 40),
        (1.25, 36),
        (1.5, 40),
        (1.75, 36),
    ],
    "ambient_pad": [(0.0, 48), (2.0, 52), (4.0, 48), (6.0, 52)],
    "driving_beat": [
        (0.0, 36),
        (0.5, 36),
        (1.0, 39),
        (1.5, 36),
        (2.0, 40),
        (2.5, 36),
        (3.0, 39),
        (3.5, 36),
    ],
    "synthwave": [
        (0.0, 36),
        (0.5, 43),
        (1.0, 36),
        (1.5, 47),
        (2.0, 36),
        (2.5, 43),
        (3.0, 36),
        (3.5, 47),
    ],
    "liquid_ambient": [(0.0, 44), (1.5, 47), (3.0, 44), (4.5, 47)],
}

DRUM_PATTERNS = {
    "trap": {
        "kick": [(0.0, 1.0), (0.5, 0.8), (1.0, 1.0), (1.5, 0.8)],
        "snare": [(1.0, 1.0), (3.0, 1.0)],
        "hihat": [
            (0.0, 0.5),
            (0.25, 0.4),
            (0.5, 0.5),
            (0.75, 0.4),
            (1.0, 0.5),
            (1.25, 0.4),
            (1.5, 0.5),
            (1.75, 0.4),
        ],
    },
    "minimal": {
        "kick": [(0.0, 1.0), (2.0, 0.9)],
        "snare": [],
        "hihat": [(0.5, 0.4), (1.5, 0.4), (2.5, 0.4), (3.5, 0.4)],
    },
    "rock": {
        "kick": [(0.0, 1.0), (1.0, 1.0), (2.0, 1.0), (3.0, 1.0)],
        "snare": [(1.0, 1.0), (3.0, 1.0)],
        "hihat": [
            (0.0, 0.7),
            (0.5, 0.5),
            (1.0, 0.7),
            (1.5, 0.5),
            (2.0, 0.7),
            (2.5, 0.5),
            (3.0, 0.7),
            (3.5, 0.5),
        ],
    },
    "four_on_floor": {
        "kick": [
            (0.0, 1.0),
            (0.5, 0.9),
            (1.0, 1.0),
            (1.5, 0.9),
            (2.0, 1.0),
            (2.5, 0.9),
            (3.0, 1.0),
            (3.5, 0.9),
        ],
        "snare": [(1.0, 1.0), (3.0, 1.0)],
        "hihat": [
            (0.0, 0.6),
            (0.25, 0.4),
            (0.5, 0.6),
            (0.75, 0.4),
            (1.0, 0.6),
            (1.25, 0.4),
            (1.5, 0.6),
            (1.75, 0.4),
        ],
    },
    "tribal": {
        "kick": [(0.0, 1.0), (1.5, 0.9), (3.0, 1.0)],
        "snare": [(2.5, 0.8)],
        "hihat": [(0.5, 0.5), (1.0, 0.5), (2.0, 0.5), (2.5, 0.5), (3.5, 0.5)],
    },
}

VOICE_ACCENTS = {
    "motivational": [(2.0, +5), (6.0, +7), (12.0, +12)],
    "scientific": [(2.5, +3), (7.0, +5), (12.0, +7)],
    "energetic": [(1.5, +7), (5.0, +10), (9.0, +12)],
    "calm_tech": [(3.0, +4), (8.0, +6), (14.0, +8)],
    "healing": [(4.0, +3), (10.0, +5), (15.0, +7)],
}


# ============================================================================
# Shorts Audio Pattern Generator
# ============================================================================


@dataclass
class ShortsAudioPattern:
    niche: str
    duration: float
    music_volume: float = 0.3
    sfx_volume: float = 0.8
    hook_sfx_count: int = 2

    config: dict = field(init=False)
    _midi: mido.MidiFile = field(init=False)
    _tempo: int = field(init=False)

    def __post_init__(self):
        self.config = NICHE_CONFIG[self.niche]
        self._midi = mido.MidiFile()
        self._midi.ticks_per_beat = 480  # type: ignore
        self._tempo = mido.bpm2tempo(self.config["tempo"])

    def _seconds_to_ticks(self, seconds: float) -> int:
        beat_seconds = self._tempo / 1_000_000
        ticks_per_second = self._midi.ticks_per_beat / beat_seconds  # type: ignore
        return int(seconds * ticks_per_second)

    def _add_track(self, name: str, channel: int, program: int = 0) -> mido.MidiTrack:
        track = mido.MidiTrack()
        track.append(mido.MetaMessage("track_name", name=name))
        track.append(mido.Message("program_change", channel=channel, program=program, time=0))
        self._midi.tracks.append(track)  # type: ignore
        return track

    def _note_on(self, track, note: int, velocity: int, time_sec: float, channel: int = 0):
        ticks = self._seconds_to_ticks(time_sec)
        track.append(
            mido.Message("note_on", channel=channel, note=note, velocity=velocity, time=ticks)
        )

    def _note_off(self, track, note: int, time_sec: float, channel: int = 0):
        ticks = self._seconds_to_ticks(time_sec)
        track.append(mido.Message("note_off", channel=channel, note=note, velocity=0, time=ticks))

    def _control_change(self, track, control: int, value: int, time_sec: float, channel: int = 0):
        ticks = self._seconds_to_ticks(time_sec)
        track.append(
            mido.Message(
                "control_change", channel=channel, control=control, value=value, time=ticks
            )
        )

    def generate(self) -> mido.MidiFile:
        dur = self.duration
        loop_start = max(0, dur - 2.5)
        sfx_interval = self.config["sfx_interval"]

        # Bass track
        bass_track = self._add_track("Bass", channel=0, program=33)
        pattern = BASSLINE_PATTERNS[self.config["background_style"]]
        beat_duration = 60.0 / self.config["tempo"]
        for i in range(int(dur / beat_duration) + 1):
            for rel_beat, note in pattern:
                t = i * beat_duration + rel_beat
                if t < dur:
                    self._note_on(bass_track, note, 100, t, channel=0)
                    self._note_off(bass_track, note, t + 0.2, channel=0)

        # Drums track
        drum_track = self._add_track("Drums", channel=1, program=9)
        drum_pat = DRUM_PATTERNS[self.config["drum_kit"]]
        for kit, events in drum_pat.items():
            note_map = {"kick": 36, "snare": 38, "hihat": 42}
            for rel_beat, vel in events:
                for i in range(int(dur / 0.5) + 10):
                    t = i * 0.5 + rel_beat
                    if t < dur:
                        note_val = note_map[kit]
                        vel_val = int(vel * 100)
                        self._note_on(drum_track, note_val, vel_val, t, channel=1)
                        dur_sec = 0.05 if kit == "kick" else 0.1
                        self._note_off(drum_track, note_val, t + dur_sec, channel=1)

        # SFX track
        sfx_track = self._add_track("SFX", channel=2, program=10)
        sfx_list = self.config["hook_sfx"]

        # Hook: first 2 sec
        t = 0.1
        for _ in range(self.hook_sfx_count):
            sfx_name = random.choice(sfx_list)
            sfx = SFX_PRESETS[sfx_name]
            self._note_on(sfx_track, sfx["note"], sfx["velocity"], t, channel=2)
            self._note_off(sfx_track, sfx["note"], t + sfx["duration"], channel=2)
            t += sfx["duration"] + 0.1

        # Dynamics: periodic SFX
        next_sfx = sfx_interval
        while next_sfx < loop_start:
            sfx_name = random.choice(sfx_list)
            sfx = SFX_PRESETS[sfx_name]
            v = int(self.sfx_volume * sfx["velocity"])
            self._note_on(sfx_track, sfx["note"], v, next_sfx, channel=2)
            self._note_off(sfx_track, sfx["note"], next_sfx + sfx["duration"], channel=2)
            next_sfx += sfx_interval

        # Loop: last 2.5 sec
        for i in range(3):
            sfx_t = loop_start + i * 0.3
            sfx = SFX_PRESETS[random.choice(sfx_list)]
            v = int(self.sfx_volume * sfx["velocity"] * (1.0 - i * 0.2))
            self._note_on(sfx_track, sfx["note"], v, sfx_t, channel=2)
            self._note_off(sfx_track, sfx["note"], sfx_t + sfx["duration"] * 1.5, channel=2)

        # Pad track
        pad_track = self._add_track("Pad", channel=3, program=88)
        pad_note = 48
        for t_marker in [0.0, 5.0, 10.0, 15.0]:
            if t_marker < dur:
                self._note_on(pad_track, pad_note, int(self.music_volume * 60), t_marker, channel=3)
                self._note_off(pad_track, pad_note, min(t_marker + 8.0, dur), channel=3)

        # Voice accent track
        voice_track = self._add_track("VoiceAccent", channel=4, program=54)
        accents = VOICE_ACCENTS[self.config["voice_tone"]]
        for t_accent, semitones in accents:
            if t_accent < dur:
                self._control_change(voice_track, 74, 100, t_accent, channel=4)
                self._note_on(voice_track, 60, int(0.7 * 100), t_accent, channel=4)
                self._note_off(voice_track, 60, t_accent + 0.15, channel=4)

        # Clicks track
        click_track = self._add_track("Clicks", channel=5, program=10)
        tick = 0.5
        while tick < dur:
            click_note = 72 if random.random() > 0.7 else 56
            self._note_on(click_track, click_note, 70, tick, channel=5)
            self._note_off(click_track, click_note, tick + 0.03, channel=5)
            tick += 0.5

        for track in self._midi.tracks:  # type: ignore
            track.append(mido.MetaMessage("end_of_track", time=self._seconds_to_ticks(dur)))

        return self._midi

    def save(self, path: Path):
        self._midi.save(str(path))  # type: ignore
        print(
            f"✅ Saved: {path} ({self.duration}s, {self.config['tempo']} BPM, niche={self.niche})"
        )
        print("📋 Structure:")
        print(f"  0–2s   : HOOK  ({self.config['hook_sfx']} SFX)")
        print(
            f"  2–{self.duration - 2.5:.0f}s : DYNAMICS (SFX every {self.config['sfx_interval']}s, {self.config['background_style']})"
        )
        print(f"  {self.duration - 2.5:.0f}–{self.duration}s : LOOP (fade + seamless start)")
        print()
        print("🎯 Tips:")
        print(f"  • Voice tone: {self.config['voice_tone']}")
        print(
            f"  • Music volume: {self.music_volume * 100:.0f}%, SFX: {self.sfx_volume * 100:.0f}%"
        )
        print("  • Last phrase should transition into first for loop")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Shorts-compatible audio pattern for nutra creatives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Niche options: weight_loss, supplements, fitness, biohacking, detox

Example:
  python scripts/shorts_nutra_audio.py --niche weight_loss --duration 20 --output wl_20s.mid

Then import MIDI into DAW and add voiceover following hook-dynamics-loop structure.
""",
    )
    parser.add_argument(
        "--niche", required=True, help="Niche: weight_loss, supplements, fitness, biohacking, detox"
    )
    parser.add_argument(
        "--duration", type=float, default=20.0, help="Duration in seconds (default: 20)"
    )
    parser.add_argument(
        "--output", type=str, default="nutra_shorts.mid", help="Output MIDI file path"
    )
    parser.add_argument("--tempo", type=int, default=None, help="Override tempo (BPM)")

    args = parser.parse_args()

    if args.niche not in NICHE_CONFIG:
        print(f"❌ Unknown niche '{args.niche}'. Available: {list(NICHE_CONFIG.keys())}")
        return 1

    if args.tempo:
        NICHE_CONFIG[args.niche]["tempo"] = args.tempo

    generator = ShortsAudioPattern(niche=args.niche, duration=args.duration)
    generator.generate()
    generator.save(Path(args.output))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
