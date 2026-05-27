#!/usr/bin/env python3
"""
scripts/shorts_nutra_audio.py — Nutra YouTube Shorts audio using Melodica SDK (improved).

Major-key, raised bass, proper chord progression, and richer instrumentation.
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


# ── niche config ─────────────────────────────────────────────────────────────
NICHE_CONFIG = {
    "weight_loss": {
        "tempo": 165,
        "hook_sfx": ["whoosh", "punch", "ding"],
        "sfx_interval": 2.5,
        "voice_tone": "motivational",
        "music_volume": 0.3,
        "sfx_volume": 0.8,
    },
    "supplements": {
        "tempo": 150,
        "hook_sfx": ["sparkle", "chime", "sci-fi"],
        "sfx_interval": 3.0,
        "voice_tone": "scientific",
        "music_volume": 0.3,
        "sfx_volume": 0.8,
    },
    "fitness": {
        "tempo": 175,
        "hook_sfx": ["drum_hit", "strike", "power"],
        "sfx_interval": 2.0,
        "voice_tone": "energetic",
        "music_volume": 0.3,
        "sfx_volume": 0.8,
    },
    "biohacking": {
        "tempo": 155,
        "hook_sfx": ["cyber", "glitch", "digital"],
        "sfx_interval": 3.5,
        "voice_tone": "calm_tech",
        "music_volume": 0.3,
        "sfx_volume": 0.8,
    },
    "detox": {
        "tempo": 140,
        "hook_sfx": ["water", "clean", "chime"],
        "sfx_interval": 3.0,
        "voice_tone": "healing",
        "music_volume": 0.3,
        "sfx_volume": 0.8,
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

VOICE_ACCENTS = {
    "motivational": [(2.0, +5), (6.0, +7), (12.0, +12)],
    "scientific": [(2.5, +3), (7.0, +5), (12.0, +7)],
    "energetic": [(1.5, +7), (5.0, +10), (9.0, +12)],
    "calm_tech": [(3.0, +4), (8.0, +6), (14.0, +8)],
    "healing": [(4.0, +3), (10.0, +5), (15.0, +7)],
}

# I - V - vi - IV  (C major)
PROGRESSION = [
    (0, Quality.MAJOR),  # I  C
    (7, Quality.MAJOR),  # V  G
    (9, Quality.MINOR),  # vi Am
    (5, Quality.MAJOR),  # IV F
]

PERC_TRACKS = {"drums", "sfx", "clicks", "voice"}


# ── Custom Generators ────────────────────────────────────────────────────────


@dataclass
class BasslineGenerator(PhraseGenerator):
    """Root-fifth bass pattern following chord progression, raised octave."""

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
        note_dur_sec = 0.2
        note_dur = note_dur_sec / sec_per_beat
        notes: list[NoteInfo] = []
        t = 0.0
        while t < duration_beats:
            chord = chord_at(chords, t)
            if chord is not None:
                # beat within bar (4/4)
                beat_in_bar = t % 4
                # root on 1 & 3, fifth on 2 & 4
                if beat_in_bar < 0.5 or (beat_in_bar >= 2 and beat_in_bar < 2.5):
                    pc = chord.root % 12
                else:
                    pc = (chord.root + 7) % 12
                pitch = 36 + 12 + pc  # C2 + 12 = C3 region
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(t, 6),
                        duration=round(min(note_dur, duration_beats - t), 6),
                        velocity=112,
                    )
                )
            t += 0.5  # eighth-note grid
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
        if self.section == "Hook":
            gen = TrapDrumsGenerator(
                params=GeneratorParams(density=0.55),
                variant="drill",
                hat_roll_density=0.6,
                kick_pattern="syncopated",
                open_hat_probability=0.15,
            )
        elif self.section == "Loop":
            gen = TrapDrumsGenerator(
                params=GeneratorParams(density=0.5),
                variant="melodic",
                hat_roll_density=0.4,
                kick_pattern="standard",
                open_hat_probability=0.2,
            )
        else:
            gen = TrapDrumsGenerator(
                params=GeneratorParams(density=0.45),
                variant="standard",
                hat_roll_density=0.3,
                kick_pattern="standard",
                open_hat_probability=0.1,
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
class SFXGenerator(PhraseGenerator):
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
            t_sec = 0.1
            for _ in range(2):
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
                vel = int(self.niche_cfg.get("sfx_volume", 0.8) * sfx["velocity"])
                notes.append(
                    NoteInfo(
                        pitch=sfx["note"],
                        start=round(t_sec / sec_per_beat, 6),
                        duration=round(d / sec_per_beat, 6),
                        velocity=vel,
                    )
                )
                t_sec += interval
        else:  # Loop
            step = 0.3
            for i in range(3):
                t_sec = i * step
                if t_sec >= duration_beats * sec_per_beat:
                    break
                sfx = SFX_PRESETS[random.choice(sfx_list)]
                d = sfx["duration"] * 1.5
                vel = int(self.niche_cfg.get("sfx_volume", 0.8) * sfx["velocity"] * (1.0 - i * 0.2))
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
class ChordalPadGenerator(PhraseGenerator):
    """Sustained chord pad in mid register, very quiet."""

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
        base_velocity = int(self.niche_cfg.get("music_volume", 0.3) * 30)
        for c in chords:
            # Only triad tones
            if c.quality == Quality.MAJOR:
                intervals = [0, 4, 7]
            elif c.quality == Quality.MINOR:
                intervals = [0, 3, 7]
            elif c.quality == Quality.DIMINISHED:
                intervals = [0, 3, 6]
            else:
                intervals = [0, 4, 7]
            # Higher register (C5+) to avoid masking bass/drums
            base_pitch = 72 + c.root
            for i in intervals:
                pitch = base_pitch + i
                if pitch > 127:
                    continue
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(c.start, 6),
                        duration=round(c.duration * 0.95, 6),  # slight legato overlap
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
                    pitch=60,
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
            note = 72 if random.random() > 0.7 else 56
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
class LeadGenerator(PhraseGenerator):
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
            params=GeneratorParams(density=0.4),  # lower density
            style="techno",
            note_length="staccato",
            portamento=0.0,
            vibrato_rate=0.5,
            vibrato_depth=0.3,
        )
        notes = base_gen.render(chords, key, duration_beats, context)
        # Filter to chord tones only (reduce harmonic clashes)
        filtered: list[NoteInfo] = []
        for n in notes:
            chord = chord_at(chords, n.start)
            if chord is not None:
                # Build set of chord tones (root + third + fifth) in octave span
                root_pc = chord.root % 12
                third_pc = (chord.root + (3 if chord.quality == Quality.MINOR else 4)) % 12
                fifth_pc = (chord.root + 7) % 12
                allowed = {root_pc, third_pc, fifth_pc}
                if n.pitch % 12 in allowed:
                    n.velocity = int(n.velocity * 0.8)  # lower vel to sit back
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


# ── Sections & Harmony ───────────────────────────────────────────────────────

TRACKS = ["bass", "drums", "sfx", "pad", "voice", "clicks", "lead"]


def make_sections(duration_sec: float, bpm: int) -> list[tuple[str, int, list[str]]]:
    """Create 3-part structure (Hook/Dynamics/Loop) bar counts."""
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
    """Predefined I-V-vi-IV progression cycling."""
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
            return SFXGenerator(params=params, niche_cfg=niche_cfg, section=section), []
        case "pad":
            return ChordalPadGenerator(params=params, niche_cfg=niche_cfg), [
                VelocityScalingModifier(scale=0.8)
            ]
        case "voice":
            return VoiceAccentGenerator(params=params, niche_cfg=niche_cfg), []
        case "clicks":
            return ClicksGenerator(params=params, niche_cfg=niche_cfg), []
        case "lead":
            return LeadGenerator(params=GeneratorParams(density=0.5), niche_cfg=niche_cfg), [
                HumanizeModifier(timing_std=0.01, velocity_std=5)
            ]
        case _:
            return None, []


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Generate Shorts audio (improved arrangement) using Melodica SDK",
        epilog="Niche options: weight_loss, supplements, fitness, biohacking, detox",
    )
    parser.add_argument("--niche", required=True)
    parser.add_argument("--duration", type=float, default=15.0)
    parser.add_argument("--output", type=str, default="nutra_shorts_v2.mid")
    parser.add_argument("--tempo", type=int, default=None)
    args = parser.parse_args()

    if args.niche not in NICHE_CONFIG:
        print(f"❌ Unknown niche '{args.niche}'. Available: {list(NICHE_CONFIG.keys())}")
        return 1

    niche_cfg = NICHE_CONFIG[args.niche].copy()
    if args.tempo:
        niche_cfg["tempo"] = args.tempo

    bpm = niche_cfg["tempo"]
    bpb = 4
    SECTIONS = make_sections(args.duration, bpm)
    total_bars = sum(b for _, b, _ in SECTIONS)

    # Build global chord list
    all_chords: list[ChordLabel] = []
    cur_bar = 0
    for bars in [b for _, b, _ in SECTIONS]:
        sec_chords = harmonize(bars, bpb)
        # shift chords to absolute positions
        for c in sec_chords:
            all_chords.append(
                ChordLabel(
                    root=c.root, quality=c.quality, start=(cur_bar + c.start), duration=c.duration
                )
            )
        cur_bar += bars

    # Main orchestration
    engine = ArticulationEngine()
    tracks: dict[str, list[NoteInfo]] = {}
    contexts: dict[str, RenderContext] = {}
    beat_offset = 0.0
    scale = Scale(root=0, mode=Mode.MAJOR)

    print(f"🎬 {args.niche} | {args.duration}s | {bpm} BPM | C major")
    for section_name, bars, track_names in SECTIONS:
        s_beats = bars * bpb
        # chords active during this section
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

    # Fade-out at the very end of LOOP section
    loop_start_beat = sum(b for _, b, _ in SECTIONS[:2]) * 4  # Hook+Dynamics bars in beats
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
        cc_events[tn].sort(key=lambda ev: ev[0])  # sort by time

    INSTRUMENTS = {
        "bass": 33,  # Electric Bass (finger)
        "drums": 117,  # Synth Drum (for melodic channel)
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
    print(f"\n✅ Saved: {output_path} ({args.duration}s, {bpm} BPM, niche={args.niche}, key=C)")
    print("📋 Structure:")
    print(f"  0–{hook_sec:.1f}s   : HOOK  (heavy SFX, drums)")
    print(f"  {hook_sec:.1f}–{hook_sec + dyn_sec:.1f}s : DYNAMICS (full groove, chordal pad, lead)")
    print(f"  {hook_sec + dyn_sec:.1f}–{args.duration:.1f}s : LOOP  (transition to start)")
    print("\n🎯 Tips:")
    print(f"  • Voice tone: {niche_cfg['voice_tone']}")
    print(
        f"  • Music volume: {niche_cfg['music_volume'] * 100:.0f}%, SFX: {niche_cfg['sfx_volume'] * 100:.0f}%"
    )
    print("  • Improved: raised bass, chord progression I-V-vi-IV, lead synth, percussive SFX\n")


if __name__ == "__main__":
    sys.exit(main())
