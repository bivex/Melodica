#!/usr/bin/env python3
"""
scripts/shorts_casino_audio.py — Casino/Gambling YouTube Shorts audio using Melodica SDK.

 Themes: slot machine wins, roulette spins, high rollers, lucky strikes, all-in moments.
 Mood: exciting, tense, celebratory, flashing lights.

 3-section structure:
   HOOK      (0–2s): intense SFX (slot chimes, winning bells), driving beat
   DYNAMICS  (2–T-2.5s): groove builds, periodic win SFX
   LOOP      (T-2.5–T): celebratory peak → smooth transition to start

 Key: C major (bright, celebratory)
 Variants: slots (classic casino), roulette (sophisticated), high_roller (luxury)
"""

import sys, random, argparse
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo, MusicTimeline
from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.modifiers import (
    HumanizeModifier,
    VelocityScalingModifier,
    CrescendoModifier,
    ModifierContext,
)
from melodica.composer import ArticulationEngine
from melodica.midi import export_multitrack_midi
from melodica.render_context import RenderContext
from melodica.utils import chord_at

from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# ── Casino niche config ───────────────────────────────────────────────────────
NICHE_CONFIG = {
    "slots": {
        "tempo": 155,  # steady, hypnotic
        "hook_sfx": ["slot_win", "bell_win", "cherry_chime", "coin_drop"],
        "sfx_interval": 2.8,
        "voice_tone": "exciting",
        "music_volume": 0.35,
        "sfx_volume": 0.9,
        "bass_style": "walking",  # blues walking bass
        "pad_style": "bright",
    },
    "roulette": {
        "tempo": 128,  # slower, tension
        "hook_sfx": ["roulette_spin", "ball_click", "card_shuffle", "chip_stack"],
        "sfx_interval": 3.5,
        "voice_tone": "sophisticated",
        "music_volume": 0.3,
        "sfx_volume": 0.85,
        "bass_style": "pulsing",
        "pad_style": "dark",
    },
    "high_roller": {
        "tempo": 168,  # fast, energetic
        "hook_sfx": ["win_bell", "jackpot_win", "dice_roll", "card_shuffle"],
        "sfx_interval": 2.2,
        "voice_tone": "luxury",
        "music_volume": 0.4,
        "sfx_volume": 1.0,
        "bass_style": "driving",
        "pad_style": "bright",
    },
}

# Casino SFX presets (mapped to melodic MIDI notes)
SFX_PRESETS = {
    "slot_win": {"note": 72, "velocity": 100, "duration": 0.2},  # high sparkle
    "bell_win": {"note": 84, "velocity": 110, "duration": 0.3},  # celebratory bell
    "cherry_chime": {"note": 96, "velocity": 85, "duration": 0.4},  # classic slots
    "coin_drop": {"note": 60, "velocity": 90, "duration": 0.15},
    "roulette_spin": {"note": 120, "velocity": 70, "duration": 0.5},
    "ball_click": {"note": 100, "velocity": 95, "duration": 0.1},
    "card_shuffle": {"note": 36, "velocity": 80, "duration": 0.3},
    "chip_stack": {"note": 48, "velocity": 95, "duration": 0.2},
    "win_bell": {"note": 88, "velocity": 110, "duration": 0.4},
    "jackpot_win": {"note": 108, "velocity": 115, "duration": 0.6},
    "dice_roll": {"note": 54, "velocity": 85, "duration": 0.4},
}

# Voice accent markers (for voice-over sync points)
VOICE_ACCENTS = {
    "exciting": [(1.5, +8), (4.5, +10), (8.0, +12)],
    "sophisticated": [(2.5, +5), (6.0, +8), (10.0, +10)],
    "luxury": [(1.0, +10), (3.5, +12), (6.0, +15)],
}

# Bass patterns by style
BASSLINE_PATTERNS = {
    "walking": [  # bluesy walking bass (root-5-6-b3)
        (0.0, 36),
        (0.5, 43),
        (1.0, 45),
        (1.5, 39),
        (2.0, 36),
        (2.5, 43),
        (3.0, 45),
        (3.5, 39),
    ],
    "pulsing": [
        (0.0, 36),
        (0.25, 36),
        (0.5, 36),
        (0.75, 36),
        (1.0, 40),
        (1.25, 36),
        (1.5, 40),
        (1.75, 36),
    ],
    "driving": [
        (0.0, 36),
        (0.5, 36),
        (1.0, 39),
        (1.5, 36),
        (2.0, 40),
        (2.5, 36),
        (3.0, 39),
        (3.5, 36),
    ],
}
BASS_CYCLE = 4  # bars

# Drum variants
DRUM_VARIANTS = {
    "standard": {"variant": "standard", "hat_roll": 0.3, "kick": "standard", "open_hat": 0.10},
    "aggressive": {"variant": "drill", "hat_roll": 0.6, "kick": "syncopated", "open_hat": 0.15},
    "smooth": {"variant": "melodic", "hat_roll": 0.4, "kick": "standard", "open_hat": 0.20},
}

PERC_TRACKS = {"drums", "sfx", "clicks", "voice"}


# ── Custom Generators ────────────────────────────────────────────────────────


@dataclass
class BasslineGenerator(PhraseGenerator):
    """Casino bass: walking (bluesy) or pulsing/driving depending on style."""

    niche_cfg: dict
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(self, params: GeneratorParams | None = None, *, niche_cfg: dict):
        super().__init__(params)
        self.niche_cfg = niche_cfg

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        style = self.niche_cfg.get("bass_style", "walking")
        pattern = BASSLINE_PATTERNS.get(style, BASSLINE_PATTERNS["walking"])
        cycle = BASS_CYCLE
        tempo = self.niche_cfg["tempo"]
        sec_per_beat = 60.0 / tempo
        note_dur = 0.25 / sec_per_beat  # 16th-note feel
        notes: list[NoteInfo] = []
        t = 0.0
        while t < duration_beats:
            for offset, midi_note in pattern:
                start = t + offset
                if start >= duration_beats:
                    continue
                d = min(note_dur, duration_beats - start)
                vel = 100 if style == "walking" else 112
                notes.append(
                    NoteInfo(
                        pitch=midi_note, start=round(start, 6), duration=round(d, 6), velocity=vel
                    )
                )
            t += cycle
        if notes:
            self._last_context = RenderContext(
                prev_pitch=notes[-1].pitch,
                prev_velocity=notes[-1].velocity,
                prev_chord=chords[-1] if chords else None,
                prev_pitches=[],
                current_scale=key,
            )
        return notes


@dataclass
class DrumsGenerator(PhraseGenerator):
    """Casino drums — section-based variants."""

    niche_cfg: dict
    section: str = "Dynamics"
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self, params: GeneratorParams | None = None, *, niche_cfg: dict, section: str = "Dynamics"
    ):
        super().__init__(params)
        self.niche_cfg = niche_cfg
        self.section = section

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if self.section == "Hook":
            cfg = DRUM_VARIANTS["aggressive"]
        elif self.section == "Loop":
            cfg = DRUM_VARIANTS["smooth"]
        else:
            cfg = DRUM_VARIANTS["standard"]
        gen = TrapDrumsGenerator(
            params=GeneratorParams(density=0.55 if self.section == "Hook" else 0.45),
            variant=cfg["variant"],
            hat_roll_density=cfg["hat_roll"],
            kick_pattern=cfg["kick"],
            open_hat_probability=cfg["open_hat"],
        )
        notes = gen.render(chords, key, duration_beats, context)
        if notes:
            self._last_context = RenderContext(
                prev_pitch=notes[-1].pitch,
                prev_velocity=notes[-1].velocity,
                prev_chord=chords[-1] if chords else None,
                prev_pitches=[],
                current_scale=key,
            )
        return notes


@dataclass
class CasinoSFXGenerator(PhraseGenerator):
    """Casino-themed SFX hits (slot wins, bells, chips, roulette)."""

    niche_cfg: dict
    section: str = "Dynamics"
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self, params: GeneratorParams | None = None, *, niche_cfg: dict, section: str = "Dynamics"
    ):
        super().__init__(params)
        self.niche_cfg = niche_cfg
        self.section = section

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        sfx_list = self.niche_cfg["hook_sfx"]
        tempo = self.niche_cfg["tempo"]
        sec_per_beat = 60.0 / tempo
        notes: list[NoteInfo] = []

        if self.section == "Hook":
            # Front-loaded heavy SFX (multiple hits)
            t_sec = 0.1
            for i in range(4):
                sfx = SFX_PRESETS[random.choice(sfx_list)]
                d = sfx["duration"]
                vel = sfx["velocity"]
                notes.append(
                    NoteInfo(
                        pitch=sfx["note"],
                        start=round(t_sec / sec_per_beat, 6),
                        duration=round(d / sec_per_beat, 6),
                        velocity=vel,
                    )
                )
                t_sec += d + 0.08

        elif self.section == "Dynamics":
            # Periodic SFX throughout, more frequent for high_roller
            interval = self.niche_cfg["sfx_interval"]
            t_sec = 0.0
            while t_sec < duration_beats * sec_per_beat:
                sfx = SFX_PRESETS[random.choice(sfx_list)]
                d = sfx["duration"]
                vel = int(self.niche_cfg.get("sfx_volume", 0.9) * sfx["velocity"])
                notes.append(
                    NoteInfo(
                        pitch=sfx["note"],
                        start=round(t_sec / sec_per_beat, 6),
                        duration=round(d / sec_per_beat, 6),
                        velocity=vel,
                    )
                )
                t_sec += interval

        else:  # Loop — big finish, then sparse
            # One big celebratory hit at loop start
            t_sec = 0.0
            big_sfx = random.choice(["jackpot_win", "bell_win", "win_bell"])
            sfx = SFX_PRESETS[big_sfx]
            vel = int(self.niche_cfg.get("sfx_volume", 0.9) * sfx["velocity"])
            notes.append(
                NoteInfo(
                    pitch=sfx["note"],
                    start=round(t_sec / sec_per_beat, 6),
                    duration=round(
                        min(sfx["duration"] * 2, (duration_beats * sec_per_beat - t_sec))
                        / sec_per_beat,
                        6,
                    ),
                    velocity=vel,
                )
            )
            # Optional second smaller hit
            if duration_beats * sec_per_beat > 1.5:
                t_sec = 1.2
                sfx2 = SFX_PRESETS[random.choice(sfx_list)]
                vel2 = int(vel * 0.7)
                notes.append(
                    NoteInfo(
                        pitch=sfx2["note"],
                        start=round(t_sec / sec_per_beat, 6),
                        duration=round(sfx2["duration"] / sec_per_beat, 6),
                        velocity=vel2,
                    )
                )

        if notes:
            self._last_context = RenderContext(
                prev_pitch=notes[-1].pitch,
                prev_velocity=notes[-1].velocity,
                prev_chord=chords[-1] if chords else None,
                prev_pitches=[],
                current_scale=key,
            )
        return notes


@dataclass
class CasinoPadGenerator(PhraseGenerator):
    """Lush pad — bright (slots/high_roller) or dark (roulette)."""

    niche_cfg: dict
    _last_context = None

    def __init__(self, params: GeneratorParams | None = None, *, niche_cfg: dict):
        super().__init__(params)
        self.niche_cfg = niche_cfg

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []
        notes: list[NoteInfo] = []
        style = self.niche_cfg.get("pad_style", "bright")
        base_velocity = int(
            self.niche_cfg.get("music_volume", 0.35) * (28 if style == "bright" else 18)
        )
        for c in chords:
            # Triad only
            if c.quality == Quality.MAJOR:
                intervals = [0, 4, 7]
            elif c.quality == Quality.MINOR:
                intervals = [0, 3, 7]
            else:
                intervals = [0, 4, 7]
            # Bright style = higher register (C5+), dark = lower (C4)
            base_pitch = (72 if style == "bright" else 60) + c.root
            for i in intervals:
                pitch = base_pitch + i
                if pitch > 127:
                    continue
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(c.start, 6),
                        duration=round(c.duration * (0.9 if style == "bright" else 0.95), 6),
                        velocity=base_velocity,
                    )
                )
        return notes


@dataclass
class VoiceAccentGenerator(PhraseGenerator):
    niche_cfg: dict
    _last_context = None

    def __init__(self, params: GeneratorParams | None = None, *, niche_cfg: dict):
        super().__init__(params)
        self.niche_cfg = niche_cfg

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        tempo = self.niche_cfg["tempo"]
        sec_per_beat = 60.0 / tempo
        notes: list[NoteInfo] = []
        for t_sec, _ in VOICE_ACCENTS[self.niche_cfg["voice_tone"]]:
            t = t_sec / sec_per_beat
            if t >= duration_beats:
                continue
            d = 0.15 / sec_per_beat
            notes.append(
                NoteInfo(
                    pitch=72,
                    start=round(t, 6),
                    duration=round(d, 6),
                    velocity=70,
                    expression={74: 100},
                )
            )
        return notes


@dataclass
class ClicksGenerator(PhraseGenerator):
    niche_cfg: dict
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(self, params: GeneratorParams | None = None, *, niche_cfg: dict):
        super().__init__(params)
        self.niche_cfg = niche_cfg

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        tempo = self.niche_cfg["tempo"]
        sec_per_beat = 60.0 / tempo
        step = 0.5 / sec_per_beat
        t = step
        notes: list[NoteInfo] = []
        # Shuffle feel: uneven eighths
        shuffle_offset = 0.08 / sec_per_beat
        while t < duration_beats:
            note = 72 if random.random() > 0.5 else 56
            d = 0.03 / sec_per_beat
            notes.append(
                NoteInfo(
                    pitch=note,
                    start=round(t + (shuffle_offset if random.random() > 0.5 else 0), 6),
                    duration=round(d, 6),
                    velocity=70,
                )
            )
            t += step
        if notes:
            self._last_context = RenderContext(
                prev_pitch=notes[-1].pitch,
                prev_velocity=notes[-1].velocity,
                prev_chord=chords[-1] if chords else None,
                prev_pitches=[],
                current_scale=key,
            )
        return notes


@dataclass
class CasinoLeadGenerator(PhraseGenerator):
    """Synth lead — bright, celebratory, chord-tone based."""

    niche_cfg: dict
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(self, params: GeneratorParams | None = None, *, niche_cfg: dict):
        super().__init__(params)
        self.niche_cfg = niche_cfg

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        base_gen = LeadSynthGenerator(
            params=GeneratorParams(density=0.45),
            style="retro" if self.niche_cfg.get("bass_style") == "walking" else "techno",
            note_length="staccato",
            portamento=0.1,
            vibrato_rate=0.6,
            vibrato_depth=0.3,
        )
        notes = base_gen.render(chords, key, duration_beats, context)
        # Filter to chord tones only
        filtered: list[NoteInfo] = []
        for n in notes:
            chord = chord_at(chords, n.start)
            if chord is not None:
                root_pc = chord.root % 12
                third_pc = (chord.root + (3 if chord.quality == Quality.MINOR else 4)) % 12
                fifth_pc = (chord.root + 7) % 12
                allowed = {root_pc, third_pc, fifth_pc}
                if n.pitch % 12 in allowed:
                    n.velocity = int(n.velocity * 0.88)
                    filtered.append(n)
        if filtered:
            self._last_context = RenderContext(
                prev_pitch=filtered[-1].pitch,
                prev_velocity=filtered[-1].velocity,
                prev_chord=chords[-1] if chords else None,
                prev_pitches=[],
                current_scale=key,
            )
        return filtered


@dataclass
class FanfareGenerator(PhraseGenerator):
    """Short celebratory brass stabs — plays on downbeats of chord changes."""

    niche_cfg: dict
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(self, params: GeneratorParams | None = None, *, niche_cfg: dict):
        super().__init__(params)
        self.niche_cfg = niche_cfg

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        if not chords:
            return notes
        # Play a short stab on beat 1 of every 4-bar cycle (or every chord change)
        beat_dur = 1.0  # quarter note
        for c in chords:
            # Only on downbeat
            if c.start % 4 == 0:
                # Root + 3rd in mid-high register (trumpet range)
                root_pc = c.root % 12
                third_pc = (c.root + (3 if c.quality == Quality.MINOR else 4)) % 12
                # Two-note stab: root then third
                t = c.start
                vel = 105
                dur = 0.15  # short staccato
                notes.append(
                    NoteInfo(
                        pitch=60 + root_pc, start=round(t, 6), duration=round(dur, 6), velocity=vel
                    )
                )
                notes.append(
                    NoteInfo(
                        pitch=60 + third_pc + 12,
                        start=round(t, 6),
                        duration=round(dur, 6),
                        velocity=vel,
                    )
                )
        if notes:
            self._last_context = RenderContext(
                prev_pitch=notes[-1].pitch,
                prev_velocity=notes[-1].velocity,
                prev_chord=chords[-1] if chords else None,
                prev_pitches=[],
                current_scale=key,
            )
        return notes


@dataclass
class CoinDropGenerator(PhraseGenerator):
    """Random coin drop sounds — sporadic, celebratory micro-SFX."""

    niche_cfg: dict
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(self, params: GeneratorParams | None = None, *, niche_cfg: dict):
        super().__init__(params)
        self.niche_cfg = niche_cfg

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        tempo = self.niche_cfg["tempo"]
        sec_per_beat = 60.0 / tempo
        notes: list[NoteInfo] = []
        # Random interval between 0.5 and 1.5 seconds
        t_sec = random.uniform(0.3, 0.8)
        coin_notes = [72, 60, 48]  # high, mid, low coin drops
        while t_sec < duration_beats * sec_per_beat:
            note = random.choice(coin_notes)
            vel = random.randint(65, 85)
            d = 0.15
            notes.append(
                NoteInfo(
                    pitch=note,
                    start=round(t_sec / sec_per_beat, 6),
                    duration=round(d / sec_per_beat, 6),
                    velocity=vel,
                )
            )
            t_sec += random.uniform(0.5, 1.5)
        if notes:
            self._last_context = RenderContext(
                prev_pitch=notes[-1].pitch,
                prev_velocity=notes[-1].velocity,
                prev_chord=chords[-1] if chords else None,
                prev_pitches=[],
                current_scale=key,
            )
        return notes


# ── Harmony & Sections ───────────────────────────────────────────────────────

# Chord progression for casino tension/release — I–V–vi–IV
PROGRESSION = [
    (0, Quality.MAJOR),  # C
    (7, Quality.MAJOR),  # G
    (9, Quality.MINOR),  # Am
    (5, Quality.MAJOR),  # F
]

TRACKS = ["bass", "drums", "sfx", "pad", "voice", "clicks", "lead", "fanfare", "coins"]


def make_sections(duration_sec: float, bpm: int) -> list[tuple[str, int, list[str]]]:
    hook_sec = 2.0
    loop_sec = 2.5
    dyn_sec = max(0.0, duration_sec - hook_sec - loop_sec)
    hook_bars = max(1, round(hook_sec * bpm / 240))
    loop_bars = max(1, round(loop_sec * bpm / 240))
    dyn_bars = max(1, round(dyn_sec * bpm / 240))
    return [
        ("Hook", hook_bars, TRACKS),
        ("Dynamics", dyn_bars, TRACKS),
        ("Loop", loop_bars, TRACKS),
    ]


def harmonize(bars: int, bpb: int = 4) -> list[ChordLabel]:
    chords: list[ChordLabel] = []
    for i in range(bars):
        root, qual = PROGRESSION[i % 4]
        chords.append(ChordLabel(root=root, quality=qual, start=i * bpb, duration=bpb))
    return chords


def build(track_name: str, niche_cfg: dict, section: str):
    params = GeneratorParams(density=0.6)
    match track_name:
        case "bass":
            return BasslineGenerator(params=params, niche_cfg=niche_cfg), []
        case "drums":
            return DrumsGenerator(params=params, niche_cfg=niche_cfg, section=section), [
                HumanizeModifier(timing_std=0.008, velocity_std=4)
            ]
        case "sfx":
            return CasinoSFXGenerator(params=params, niche_cfg=niche_cfg, section=section), []
        case "pad":
            return CasinoPadGenerator(params=params, niche_cfg=niche_cfg), [
                VelocityScalingModifier(scale=0.7)
            ]
        case "voice":
            return VoiceAccentGenerator(params=params, niche_cfg=niche_cfg), []
        case "clicks":
            return ClicksGenerator(params=params, niche_cfg=niche_cfg), []
        case "lead":
            return CasinoLeadGenerator(params=GeneratorParams(density=0.4), niche_cfg=niche_cfg), [
                HumanizeModifier(timing_std=0.01, velocity_std=4)
            ]
        case "fanfare":
            return FanfareGenerator(params=GeneratorParams(density=0.3), niche_cfg=niche_cfg), []
        case "coins":
            return CoinDropGenerator(params=GeneratorParams(density=0.2), niche_cfg=niche_cfg), []
        case _:
            return None, []


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Generate Casino Shorts audio using Melodica SDK",
        epilog="Casino variants: slots, roulette, high_roller",
    )
    parser.add_argument(
        "--variant", default="slots", help="Casino variant: slots, roulette, high_roller"
    )
    parser.add_argument("--duration", type=float, default=15.0, help="Duration seconds")
    parser.add_argument("--output", type=str, default="casino_shorts.mid", help="Output MIDI path")
    parser.add_argument("--tempo", type=int, default=None, help="Override BPM")
    args = parser.parse_args()

    if args.variant not in NICHE_CONFIG:
        print(f"❌ Unknown variant '{args.variant}'. Available: {list(NICHE_CONFIG.keys())}")
        return 1

    niche_cfg = NICHE_CONFIG[args.variant].copy()
    if args.tempo:
        niche_cfg["tempo"] = args.tempo

    bpm = niche_cfg["tempo"]
    bpb = 4
    SECTIONS = make_sections(args.duration, bpm)

    # Build absolute chord list
    all_chords: list[ChordLabel] = []
    cur_bar = 0
    for bars in [b for _, b, _ in SECTIONS]:
        sec_chords = harmonize(bars, bpb)
        for c in sec_chords:
            all_chords.append(
                ChordLabel(
                    root=c.root, quality=c.quality, start=cur_bar + c.start, duration=c.duration
                )
            )
        cur_bar += bars

    engine = ArticulationEngine()
    tracks: dict[str, list[NoteInfo]] = {}
    contexts: dict[str, RenderContext] = {}
    beat_offset = 0.0
    scale = Scale(root=0, mode=Mode.MAJOR)  # C major

    print(f"🎰 {args.variant.upper()} CASINO | {args.duration}s | {bpm} BPM | C major")
    for section_name, bars, track_names in SECTIONS:
        s_beats = bars * bpb
        section_chords = [c for c in all_chords if beat_offset <= c.start < beat_offset + s_beats]
        print(f"  [{section_name:10s}] {bars:2d} bars | {', '.join(track_names)}")
        for tn in track_names:
            gen, mods = build(tn, niche_cfg, section_name)
            if gen is None:
                continue
            prev = contexts.get(tn)
            ctx = RenderContext(
                prev_pitch=prev.prev_pitch if prev else None,
                prev_velocity=prev.prev_velocity if prev else None,
                prev_chord=prev.prev_chord if prev else None,
                prev_pitches=list(prev.prev_pitches) if prev else [],
                current_scale=scale,
            )
            notes = gen.render(section_chords, scale, s_beats, ctx)
            if hasattr(gen, "_last_context") and gen._last_context is not None:
                contexts[tn] = gen._last_context
            mc = ModifierContext(
                duration_beats=s_beats, chords=section_chords, timeline=MusicTimeline(), scale=scale
            )
            for m in mods:
                try:
                    notes = m.modify(notes, mc)
                except Exception as e:
                    print(f"  ⚠️  Modifier error on {tn}: {e}")
            if tn not in tracks:
                tracks[tn] = []
            for n in notes:
                tracks[tn].append(
                    NoteInfo(
                        pitch=n.pitch,
                        start=round(n.start + beat_offset, 6),
                        duration=n.duration,
                        velocity=n.velocity,
                        articulation=n.articulation,
                        expression=dict(n.expression),
                    )
                )
        beat_offset += s_beats

    for tn in tracks:
        tracks[tn].sort(key=lambda n: n.start)

    # ============================================
    # MIXING: gain staging + section automation
    # ============================================
    desk = MixingDesk(niche_cfg)
    tracks = desk.apply_mixing(tracks, SECTIONS, bpm)

    # Fade-out at LOOP start
    loop_start_beat = sum(b for _, b, _ in SECTIONS[:2]) * 4
    tracks = desk.apply_fade_loop_end(tracks, loop_start_beat, fade_beats=2.0)

    # ============================================
    # MASTERING: LUFS normalization + real CC10 panning + limiting
    # ============================================
    master = MasteringDesk(target_lufs=-14.0)
    tracks, pan_cc_events = master.apply_mastering(tracks)

    cc_events: dict[str, list[tuple[float, int, int]]] = {}
    art = ArticulationEngine()
    for tn in list(tracks.keys()):
        if tn not in PERC_TRACKS:
            tracks[tn] = art.apply(tracks[tn], tn, beat_offset)
            raw = art.add_sustain_pedal_events(tracks[tn], beat_offset)
            if raw:
                cc_events[tn] = [(e["time"], 64, e["value"]) for e in raw]

    # Merge pan CC10 events with sustain pedal CCs
    for tn, pan_list in pan_cc_events.items():
        if tn not in cc_events:
            cc_events[tn] = []
        cc_events[tn].extend(pan_list)
        cc_events[tn].sort(key=lambda ev: ev[0])

    INSTRUMENTS = {
        "bass": 33,  # Electric Bass (finger)
        "drums": 117,  # Synth Drum
        "sfx": 10,  # Glockenspiel (bright SFX)
        "pad": 88,  # New Age Pad
        "voice": 54,  # Synth Voice
        "clicks": 14,  # Xylophone
        "lead": 81,  # Sawtooth Lead
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    export_multitrack_midi(
        tracks,
        output_path,
        bpm=bpm,
        key="C",
        instruments=INSTRUMENTS,
        cc_events=cc_events if cc_events else None,
    )

    hook_sec = SECTIONS[0][1] * 4 * 60 / bpm
    dyn_sec = SECTIONS[1][1] * 4 * 60 / bpm
    print(f"\n✅ Saved: {output_path} ({args.duration}s, {bpm} BPM, variant={args.variant}, key=C)")
    print("📋 Structure:")
    print(f"  0–{hook_sec:.1f}s   : HOOK  (heavy casino SFX, aggressive drums)")
    print(
        f"  {hook_sec:.1f}–{hook_sec + dyn_sec:.1f}s : DYNAMICS (full groove, {'bright' if niche_cfg['pad_style'] == 'bright' else 'dark'} pad, lead)"
    )
    print(f"  {hook_sec + dyn_sec:.1f}–{args.duration:.1f}s : LOOP  (transition)")
    print("\n🎯 Tips:")
    print(f"  • Bass: {niche_cfg['bass_style']} | Pad: {niche_cfg['pad_style']}")
    print(
        f"  • Music volume: {niche_cfg['music_volume'] * 100:.0f}%, SFX: {niche_cfg['sfx_volume'] * 100:.0f}%"
    )
    print("  • Chord progression: I–V–vi–IV (C–G–Am–F)\n")


if __name__ == "__main__":
    sys.exit(main())
