# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_rave_metal.py — "Rave Inferno: Metal-Rave Crossover"
6 tracks of metal guitars + electronic beats + rave synths + dark bass.
"""

import os
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams

# Metal generators
from melodica.generators.power_chord import PowerChordGenerator
from melodica.generators.tremolo_picking import TremoloPickingGenerator
from melodica.generators.guitar_tapping import GuitarTappingGenerator
from melodica.generators.guitar_sweep import GuitarSweepGenerator
from melodica.generators.riff import RiffGenerator

# Electronic / rave generators
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.hardstyle import HardstyleGenerator
from melodica.generators.breakbeat import BreakbeatGenerator
from melodica.generators.dnb_jungle import DnBJungleGenerator
from melodica.generators.supersaw_pad import SupersawPadGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.synth_effects import SynthEffectsGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.filter_sweep import FilterSweepGenerator
from melodica.generators.sidechain_pump import SidechainPumpGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator

# Core arranger
from melodica.form import FormSection, MusicalForm
from melodica.dynamics_arc import DynamicsArc
from melodica.orchestrator import OrchestralLayer, Orchestrator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# ---------------------------------------------------------------------------
# Scales
# ---------------------------------------------------------------------------

D_MINOR = Scale(root=2, mode=Mode.AEOLIAN)
E_MINOR = Scale(root=4, mode=Mode.AEOLIAN)
B_MINOR = Scale(root=11, mode=Mode.AEOLIAN)
FS_PHRYGIAN = Scale(root=6, mode=Mode.PHRYGIAN)
C_HARM_MINOR = Scale(root=0, mode=Mode.HARMONIC_MINOR)
A_MINOR = Scale(root=9, mode=Mode.AEOLIAN)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _build_chords(progression: str, duration: float, key: Scale) -> list[ChordLabel]:
    parts = progression.split()
    beats_per = duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        chord = key.parse_roman(p)
        chord.start = i * beats_per
        chord.duration = beats_per
        chords.append(chord)
    return chords


def apply_rave_mix(raw_tracks: dict, bpm: float, lufs: float = -14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        # Track 1
        "Chug Riff": 0.88, "Rave Kick": 0.92, "Saw Pad": 0.80, "Acid Bass": 0.86,
        "FX Rise": 0.70,
        # Track 2
        "Tremolo Riff": 0.88, "Breakbeat": 0.90, "Dark Sub": 0.86, "Sweep Filter": 0.72,
        "Ghost Snare": 0.65,
        # Track 3
        "Gallop Riff": 0.88, "Hardstyle Kick": 0.92, "Reese Bass": 0.86,
        "Rave Lead": 0.84, "Impact Hit": 0.75,
        # Track 4
        "Phrygian Riff": 0.88, "DnB Breaks": 0.90, "Wobble Bass": 0.86,
        "Tap Solo": 0.84, "Horror Pad": 0.70,
        # Track 5
        "Power Riff": 0.88, "Techno Beat": 0.92, "Neuro Bass": 0.86,
        "Sweep Arp": 0.82, "Saw Stab": 0.84, "Sidechain": 0.78,
        # Track 6
        "Final Riff": 0.90, "Amen Break": 0.90, "Doom Bass": 0.86,
        "Trance Pad": 0.82, "Riser": 0.72, "Boom Impact": 0.76,
    })
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan


# ===========================================================================
# TRACK GENERATORS
# ===========================================================================

def track_01_chug_rave():
    """1. Chug Rave (D Minor, 135 BPM) — industrial chug meets acid house"""
    print("  1. Chug Rave")
    dur = 48.0
    chords = _build_chords("i iv v i VI ii i v i iv v i", dur, D_MINOR)

    sections = [
        FormSection("Build", 0.0, 16.0, "mp", 0.90, ["strings"], "mysterious"),
        FormSection("Drop", 16.0, 24.0, "ff", 1.05, ["strings", "bass", "percussion"], "triumphant"),
        FormSection("Break", 40.0, 8.0, "p", 0.85, ["strings"], "dark"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 135.0)
    arc = DynamicsArc.from_form(form)

    riff = PowerChordGenerator(pattern="chug", palm_mute_ratio=0.75)
    kick = ElectronicDrumsGenerator(kit="909", pattern="four_on_floor")
    pad = SupersawPadGenerator(variant="trance", voice_count=5)
    bass = SynthBassGenerator(waveform="acid", pattern="acid_line", slide_probability=0.4)
    riser = FXRiserGenerator(riser_type="synth", length_beats=4.0)

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Chug Riff", riff, "strings", "rhythm", "constant"),
            OrchestralLayer("Rave Kick", kick, "percussion", "rhythm", "constant"),
            OrchestralLayer("Saw Pad", pad, "strings", "pad", "constant"),
            OrchestralLayer("Acid Bass", bass, "bass", "bass", "constant"),
            OrchestralLayer("FX Rise", riser, "strings", "solo", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, D_MINOR, dur)
    return raw, 135.0


def track_02_tremelo_breaks():
    """2. Tremolo Breaks (E Minor, 150 BPM) — tremolo picking over DnB breaks"""
    print("  2. Tremolo Breaks")
    dur = 48.0
    chords = _build_chords("i VI III VII i VI III VII i VI III VII", dur, E_MINOR)

    sections = [
        FormSection("Intro", 0.0, 8.0, "p", 0.85, ["strings"], "mysterious"),
        FormSection("Ramp", 8.0, 16.0, "mf", 1.0, ["strings", "bass", "percussion"], "tense"),
        FormSection("Drop", 24.0, 16.0, "ff", 1.05, ["strings", "bass", "percussion"], "triumphant"),
        FormSection("Decay", 40.0, 8.0, "mp", 0.85, ["strings", "percussion"], "dark"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 150.0)
    arc = DynamicsArc.from_form(form)

    trem = TremoloPickingGenerator(variant="single", speed=0.0625, palm_mute_probability=0.3)
    breaks = BreakbeatGenerator(variant="amen", chop_probability=0.4, ghost_notes=True)
    bass = DarkBassGenerator(mode="doom", octave=2, movement="root_fifth")
    sweep = FilterSweepGenerator(sweep_type="lowpass_open", duration=4.0, resonance=0.7)
    ghosts = GhostNotesGenerator(target="snare", pattern="funk", ghost_density=0.5)

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Tremolo Riff", trem, "strings", "rhythm", "constant"),
            OrchestralLayer("Breakbeat", breaks, "percussion", "rhythm", "constant"),
            OrchestralLayer("Dark Sub", bass, "bass", "bass", "constant"),
            OrchestralLayer("Sweep Filter", sweep, "strings", "pad", "constant"),
            OrchestralLayer("Ghost Snare", ghosts, "percussion", "rhythm", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, E_MINOR, dur)
    return raw, 150.0


def track_03_hardstyle_gallop():
    """3. Hardstyle Gallop (B Minor, 150 BPM) — gallop riff + hardstyle kick"""
    print("  3. Hardstyle Gallop")
    dur = 56.0
    chords = _build_chords("i VI III VII i VI III VII i VI III VII i VI III VII", dur, B_MINOR)

    sections = [
        FormSection("Intro", 0.0, 8.0, "p", 0.85, ["strings"], "mysterious"),
        FormSection("Build", 8.0, 16.0, "mf", 1.0, ["strings", "bass", "percussion"], "tense"),
        FormSection("Drop", 24.0, 24.0, "ff", 1.08, ["strings", "bass", "percussion"], "triumphant"),
        FormSection("Outro", 48.0, 8.0, "mp", 0.85, ["strings"], "dark"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 150.0)
    arc = DynamicsArc.from_form(form)

    gallop = PowerChordGenerator(pattern="gallop", palm_mute_ratio=0.5, gallop_speed=0.20)
    hard = HardstyleGenerator(variant="euphoric", kick_distortion=0.9, reverse_bass_weight=0.6)
    bass = SynthBassGenerator(waveform="reese", pattern="reese_line", slide_probability=0.2)
    lead = SupersawPadGenerator(variant="rhythmic", voice_count=3)
    impact = FXImpactGenerator(impact_type="boom", tail_length=2.5, pitch_drop=18)

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Gallop Riff", gallop, "strings", "rhythm", "constant"),
            OrchestralLayer("Hardstyle Kick", hard, "percussion", "rhythm", "constant"),
            OrchestralLayer("Reese Bass", bass, "bass", "bass", "constant"),
            OrchestralLayer("Rave Lead", lead, "strings", "solo", "constant"),
            OrchestralLayer("Impact Hit", impact, "percussion", "rhythm", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, B_MINOR, dur)
    return raw, 150.0


def track_04_neuro_phrygian():
    """4. Neuro Phrygian (F# Phrygian, 160 BPM) — neurofunk + phrygian riffs"""
    print("  4. Neuro Phrygian")
    dur = 48.0
    chords = _build_chords("i II i vii i II vii i i II i vii", dur, FS_PHRYGIAN)

    sections = [
        FormSection("Intro", 0.0, 8.0, "mp", 0.90, ["strings"], "mysterious"),
        FormSection("Verse", 8.0, 16.0, "f", 1.0, ["strings", "bass", "percussion"], "frantic"),
        FormSection("Chorus", 24.0, 16.0, "ff", 1.05, ["strings", "bass", "percussion"], "triumphant"),
        FormSection("Outro", 40.0, 8.0, "p", 0.80, ["strings"], "dark"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 160.0)
    arc = DynamicsArc.from_form(form)

    riff = RiffGenerator(scale_type="blues", riff_pattern="gallop", palm_mute_prob=0.4)
    dnb = DnBJungleGenerator(variant="neurofunk", break_density=0.8, reese_amount=0.7)
    bass = SynthBassGenerator(waveform="wobble", pattern="wobble_line", filter_accent=1.5)
    tap = GuitarTappingGenerator(pattern="arpeggio", width_interval=10)
    horror = SynthEffectsGenerator(fx_type="goblins")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Phrygian Riff", riff, "strings", "rhythm", "constant"),
            OrchestralLayer("DnB Breaks", dnb, "percussion", "rhythm", "constant"),
            OrchestralLayer("Wobble Bass", bass, "bass", "bass", "constant"),
            OrchestralLayer("Tap Solo", tap, "strings", "solo", "constant"),
            OrchestralLayer("Horror Pad", horror, "strings", "pad", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, FS_PHRYGIAN, dur)
    return raw, 160.0


def track_05_sweep_techno():
    """5. Sweep Techno (C Harmonic Minor, 170 BPM) — sweep arpeggios + techno"""
    print("  5. Sweep Techno")
    dur = 56.0
    chords = _build_chords("i iv V i VI iv i V i iv V i VI iv i V i", dur, C_HARM_MINOR)

    sections = [
        FormSection("Intro", 0.0, 8.0, "mp", 0.90, ["strings"], "mysterious"),
        FormSection("Verse", 8.0, 16.0, "mf", 1.0, ["strings", "bass", "percussion"], "tense"),
        FormSection("Drop", 24.0, 24.0, "ff", 1.05, ["strings", "bass", "percussion"], "triumphant"),
        FormSection("Breakdown", 48.0, 8.0, "p", 0.80, ["strings"], "dark"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 170.0)
    arc = DynamicsArc.from_form(form)

    riff = PowerChordGenerator(pattern="syncopated", palm_mute_ratio=0.7)
    techno = ElectronicDrumsGenerator(kit="909", pattern="techno", sidechain=True, sidechain_depth=0.7)
    bass = DarkBassGenerator(mode="industrial", octave=1, movement="chromatic")
    sweep = GuitarSweepGenerator(sweep_direction="both", note_count=6, speed=0.06)
    stab = SupersawPadGenerator(variant="pluck", voice_count=3)
    pump = SidechainPumpGenerator(rate="1/4", depth=0.8)

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Power Riff", riff, "strings", "rhythm", "constant"),
            OrchestralLayer("Techno Beat", techno, "percussion", "rhythm", "constant"),
            OrchestralLayer("Neuro Bass", bass, "bass", "bass", "constant"),
            OrchestralLayer("Sweep Arp", sweep, "strings", "solo", "constant"),
            OrchestralLayer("Saw Stab", stab, "strings", "pad", "constant"),
            OrchestralLayer("Sidechain", pump, "percussion", "rhythm", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, C_HARM_MINOR, dur)
    return raw, 170.0


def track_06_inferno_peak():
    """6. Inferno Peak (A Minor, 175 BPM) — everything at once, peak-time chaos"""
    print("  6. Inferno Peak")
    dur = 64.0
    chords = _build_chords("i VI III VII i VI III VII i VI III VII i VI III VII", dur, A_MINOR)

    sections = [
        FormSection("Build", 0.0, 16.0, "p", 0.85, ["strings"], "mysterious"),
        FormSection("Ramp", 16.0, 16.0, "mf", 1.0, ["strings", "bass", "percussion"], "tense"),
        FormSection("Peak", 32.0, 24.0, "fff", 1.10, ["strings", "bass", "percussion"], "triumphant"),
        FormSection("Aftermath", 56.0, 8.0, "pp", 0.75, ["strings"], "dark"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 175.0)
    arc = DynamicsArc.from_form(form)

    riff = PowerChordGenerator(pattern="gallop", palm_mute_ratio=0.4, gallop_speed=0.18)
    amen = BreakbeatGenerator(variant="amen", chop_probability=0.5, ghost_notes=True, double_time=True)
    bass = DarkBassGenerator(mode="doom", octave=1, movement="tritone_walk")
    pad = SupersawPadGenerator(variant="trance", voice_count=7, detune_amount=0.20)
    riser = FXRiserGenerator(riser_type="noise", length_beats=8.0, pitch_curve="exponential")
    impact = FXImpactGenerator(impact_type="boom", tail_length=3.0, pitch_drop=24)

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Final Riff", riff, "strings", "rhythm", "constant"),
            OrchestralLayer("Amen Break", amen, "percussion", "rhythm", "constant"),
            OrchestralLayer("Doom Bass", bass, "bass", "bass", "constant"),
            OrchestralLayer("Trance Pad", pad, "strings", "pad", "constant"),
            OrchestralLayer("Riser", riser, "strings", "solo", "constant"),
            OrchestralLayer("Boom Impact", impact, "percussion", "rhythm", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    raw = orchestrator.render(chords, A_MINOR, dur)
    return raw, 175.0


# ===========================================================================
# MAIN
# ===========================================================================

TRACKS = [
    (track_01_chug_rave, "01_Chug_Rave.mid", {
        "Chug Riff": 29, "Rave Kick": 0, "Saw Pad": 89, "Acid Bass": 38, "FX Rise": 97,
    }),
    (track_02_tremelo_breaks, "02_Tremolo_Breaks.mid", {
        "Tremolo Riff": 29, "Breakbeat": 0, "Dark Sub": 34, "Sweep Filter": 92, "Ghost Snare": 40,
    }),
    (track_03_hardstyle_gallop, "03_Hardstyle_Gallop.mid", {
        "Gallop Riff": 29, "Hardstyle Kick": 0, "Reese Bass": 38, "Rave Lead": 89, "Impact Hit": 115,
    }),
    (track_04_neuro_phrygian, "04_Neuro_Phrygian.mid", {
        "Phrygian Riff": 29, "DnB Breaks": 0, "Wobble Bass": 38, "Tap Solo": 30, "Horror Pad": 100,
    }),
    (track_05_sweep_techno, "05_Sweep_Techno.mid", {
        "Power Riff": 29, "Techno Beat": 0, "Neuro Bass": 34, "Sweep Arp": 30, "Saw Stab": 89, "Sidechain": 10,
    }),
    (track_06_inferno_peak, "06_Inferno_Peak.mid", {
        "Final Riff": 29, "Amen Break": 0, "Doom Bass": 34, "Trance Pad": 89, "Riser": 97, "Boom Impact": 115,
    }),
]


def main():
    album_dir = Path("output/album_rave_metal")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        R A V E   I N F E R N O")
    print("        A 6-Track Metal-Rave Crossover")
    print("=" * 80)

    total_notes = 0
    for i, (producer, filename, instruments) in enumerate(TRACKS):
        print("-" * 80)
        raw, bpm = producer()
        mastered, pan = apply_rave_mix(raw, bpm)
        export_multitrack_midi(
            mastered,
            str(album_dir / filename),
            bpm=bpm,
            cc_events=pan,
            instruments=instruments,
        )
        note_count = sum(len(n) for n in raw.values())
        total_notes += note_count
        print(f"    -> {filename}  ({note_count} notes, {bpm} BPM)")

    print()
    print("=" * 80)
    print(f"  COMPLETE: Rave Inferno — {total_notes} total notes across 6 tracks")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
