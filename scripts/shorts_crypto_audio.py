#!/usr/bin/env python3
"""
scripts/shorts_crypto_audio.py — Crypto/Web3 YouTube Shorts audio using Melodica SDK.

 Crypto themes:bull runs, FOMO, blockchain, trustless,DeFi,dips,钻石手, пламя.

 15-30 секунд, 3-секционная структура:
   HOOK      (0–2с): мощные SFX, хайп-бит
   DYNAMICS  (2–T-2.5с): периодические SFX, грув
   LOOP      (T-2.5–Tс): плавный переход в начало

 Инструменты: raised bass, synthwave, glitch SFX, pluck arp, future pad.
 Ключ: C major (positive / hype energy).
"""

import sys, random, argparse
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo, MusicTimeline
from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.modifiers import HumanizeModifier, VelocityScalingModifier, ModifierContext
from melodica.composer import ArticulationEngine
from melodica.midi import export_multitrack_midi
from melodica.render_context import RenderContext
from melodica.utils import chord_at

from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# ── Crypto niche config ──────────────────────────────────────────────────────
NICHE_CONFIG = {
    "crypto": {
        "tempo": 158,  # medium-fast, driving
        "hook_sfx": ["cyber", "glitch", "digital", "scan", "lock"],  # cyber SFX palette
        "sfx_interval": 3.0,  # periodic SFX spacing
        "voice_tone": "futuristic",  # placeholder for voice markers
        "music_volume": 0.35,
        "sfx_volume": 0.9,
        "bass_style": "synthwave",  # pulsing bass pattern
    },
    "bull": {  # bull market variant — more aggressive
        "tempo": 165,
        "hook_sfx": ["power", "drum_hit", "strike"],
        "sfx_interval": 2.0,
        "voice_tone": "energetic",
        "music_volume": 0.4,
        "sfx_volume": 0.95,
        "bass_style": "driving",
    },
    "bear": {  # bear market — darker, slower
        "tempo": 132,
        "hook_sfx": ["water", "clean", "whoosh"],  # down / correction sounds
        "sfx_interval": 4.0,
        "voice_tone": "serious",
        "music_volume": 0.25,
        "sfx_volume": 0.7,
        "bass_style": "pulsing",
    },
}

# SFX preset library
SFX_PRESETS = {
    "cyber": {"note": 110, "velocity": 70, "duration": 0.15},
    "glitch": {"note": 70, "velocity": 90, "duration": 0.05},
    "digital": {"note": 88, "velocity": 80, "duration": 0.1},
    "scan": {"note": 120, "velocity": 65, "duration": 0.3},
    "lock": {"note": 60, "velocity": 100, "duration": 0.1},
    "power": {"note": 50, "velocity": 105, "duration": 0.1},
    "drum_hit": {"note": 36, "velocity": 110, "duration": 0.05},
    "strike": {"note": 38, "velocity": 100, "duration": 0.05},
    "whoosh": {"note": 100, "velocity": 80, "duration": 0.1},
    "water": {"note": 50, "velocity": 60, "duration": 0.5},
    "clean": {"note": 60, "velocity": 65, "duration": 0.4},
}

# Voice accent markers (pitch-bend markers for voice-over sync)
VOICE_ACCENTS = {
    "futuristic": [(1.5, +5), (5.0, +8), (10.0, +12)],
    "energetic": [(1.0, +7), (4.0, +10), (8.0, +12)],
    "serious": [(2.5, +3), (7.0, +5), (12.0, +7)],
}

# Bass pattern variants (root-fifth, different rhythmic feels)
BASSLINE_PATTERNS = {
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
}
BASS_CYCLE = 4  # bars

# Drum pattern variants (using TrapDrumsGenerator internally)
DRUM_VARIANTS = {
    "standard": {"variant": "standard", "hat_roll": 0.3, "kick": "standard", "open_hat": 0.1},
    "aggressive": {"variant": "drill", "hat_roll": 0.6, "kick": "syncopated", "open_hat": 0.15},
    "glitchy": {"variant": "melodic", "hat_roll": 0.5, "kick": "standard", "open_hat": 0.2},
}

PERC_TRACKS = {"drums", "sfx", "clicks", "voice"}


# ── Custom Generators ────────────────────────────────────────────────────────


@dataclass
class BasslineGenerator(PhraseGenerator):
    """Root-fifth bass following chord progression, raised register (C3+)."""

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
        style = self.niche_cfg.get("bass_style", "synthwave")
        pattern = BASSLINE_PATTERNS.get(style, BASSLINE_PATTERNS["synthwave"])
        cycle = BASS_CYCLE
        tempo = self.niche_cfg["tempo"]
        sec_per_beat = 60.0 / tempo
        note_dur = 0.2 / sec_per_beat  # 200ms note
        notes: list[NoteInfo] = []
        t = 0.0
        while t < duration_beats:
            for offset, midi_note in pattern:
                start = t + offset
                if start >= duration_beats:
                    continue
                d = min(note_dur, duration_beats - start)
                notes.append(
                    NoteInfo(
                        pitch=midi_note, start=round(start, 6), duration=round(d, 6), velocity=112
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
    """Trap drums with section-based variation."""

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
        # Section-specific drum variants
        if self.section == "Hook":
            cfg = DRUM_VARIANTS["aggressive"]
        elif self.section == "Loop":
            cfg = DRUM_VARIANTS["glitchy"]
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
class CryptoSFXGenerator(PhraseGenerator):
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
            # Heavy SFX hits at start
            t_sec = 0.1
            for i in range(self.niche_cfg.get("hook_sfx_count", 3)):
                sfx = SFX_PRESETS[random.choice(sfx_list)]
                d = sfx["duration"]
                notes.append(
                    NoteInfo(
                        pitch=sfx["note"],
                        start=round(t_sec / sec_per_beat, 6),
                        duration=round(d / sec_per_beat, 6),
                        velocity=sfx["velocity"],
                    )
                )
                t_sec += d + 0.1
        elif self.section == "Dynamics":
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
        else:  # Loop — sparse, fading
            step = 0.4
            for i in range(2):
                t_sec = i * step
                if t_sec >= duration_beats * sec_per_beat:
                    break
                sfx = SFX_PRESETS[random.choice(sfx_list)]
                d = sfx["duration"] * 2
                vel = int(self.niche_cfg.get("sfx_volume", 0.9) * sfx["velocity"] * 0.7)
                notes.append(
                    NoteInfo(
                        pitch=sfx["note"],
                        start=round(t_sec / sec_per_beat, 6),
                        duration=round(
                            min(d, (duration_beats * sec_per_beat - t_sec)) / sec_per_beat, 6
                        ),
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
class CryptoPadGenerator(PhraseGenerator):
    """Sustained chord pad — high register, very quiet, crystal tones."""

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
        base_velocity = int(self.niche_cfg.get("music_volume", 0.35) * 25)  # 8-20 range
        for c in chords:
            # Triad only
            if c.quality == Quality.MAJOR:
                intervals = [0, 4, 7]
            elif c.quality == Quality.MINOR:
                intervals = [0, 3, 7]
            else:
                intervals = [0, 4, 7]
            base_pitch = 76 + c.root  # C6 region — very high, airy
            for i in intervals:
                pitch = base_pitch + i
                if pitch > 127:
                    continue
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(c.start, 6),
                        duration=round(c.duration * 0.9, 6),  # staccato pad
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
        while t < duration_beats:
            note = 72 if random.random() > 0.6 else 56
            d = 0.03 / sec_per_beat
            notes.append(NoteInfo(pitch=note, start=round(t, 6), duration=round(d, 6), velocity=70))
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
class CryptoLeadGenerator(PhraseGenerator):
    """Saw lead playing chord tones — futuristic but harmonic."""

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
            params=GeneratorParams(density=0.4),
            style="techno",
            note_length="staccato",
            portamento=0.0,
            vibrato_rate=0.6,
            vibrato_depth=0.35,
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
                    n.velocity = int(n.velocity * 0.82)
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


# ── Harmony & Sections ───────────────────────────────────────────────────────

# I – V – vi – IV (C major progression)
PROGRESSION = [
    (0, Quality.MAJOR),  # C
    (7, Quality.MAJOR),  # G
    (9, Quality.MINOR),  # Am
    (5, Quality.MAJOR),  # F
]

TRACKS = ["bass", "drums", "sfx", "pad", "voice", "clicks", "lead"]


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
    """I–V–vi–IV cycling across bars."""
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
            return CryptoSFXGenerator(params=params, niche_cfg=niche_cfg, section=section), []
        case "pad":
            return CryptoPadGenerator(params=params, niche_cfg=niche_cfg), [
                VelocityScalingModifier(scale=0.75)
            ]
        case "voice":
            return VoiceAccentGenerator(params=params, niche_cfg=niche_cfg), []
        case "clicks":
            return ClicksGenerator(params=params, niche_cfg=niche_cfg), []
        case "lead":
            return CryptoLeadGenerator(params=GeneratorParams(density=0.35), niche_cfg=niche_cfg), [
                HumanizeModifier(timing_std=0.01, velocity_std=4)
            ]
        case _:
            return None, []


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Generate Crypto Shorts audio using Melodica SDK",
        epilog="Crypto variants: crypto (default), bull, bear",
    )
    parser.add_argument("--variant", default="crypto", help="Crypto variant: crypto, bull, bear")
    parser.add_argument("--duration", type=float, default=15.0, help="Duration seconds")
    parser.add_argument("--output", type=str, default="crypto_shorts.mid", help="Output MIDI path")
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
    total_bars = sum(b for _, b, _ in SECTIONS)

    # Build chord list
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

    print(f"🪙 {args.variant.upper()} CRYPTO | {args.duration}s | {bpm} BPM | C major")
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
        "drums": 117,  # Synth Drum (melodic channel)
        "sfx": 10,  # Glockenspiel
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
    print(f"  0–{hook_sec:.1f}s   : HOOK  (heavy SFX, aggressive drums)")
    print(f"  {hook_sec:.1f}–{hook_sec + dyn_sec:.1f}s : DYNAMICS (full groove, high pad, lead)")
    print(f"  {hook_sec + dyn_sec:.1f}–{args.duration:.1f}s : LOOP  (transition)")
    print("\n🎯 Tips:")
    print(f"  • Bass style: {niche_cfg['bass_style']}")
    print(
        f"  • Music volume: {niche_cfg['music_volume'] * 100:.0f}%, SFX: {niche_cfg['sfx_volume'] * 100:.0f}%"
    )
    print("  • Uses I–V–vi–IV chord progression (C–G–Am–F)\n")


if __name__ == "__main__":
    sys.exit(main())
