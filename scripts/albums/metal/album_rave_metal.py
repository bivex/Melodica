# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_rave_metal.py — "Rave Inferno: Metal-Rave Crossover"
A multi-part dynamic arc:
Part 1: The Escalation (Tracks 1-6)
Part 2: The Reset & Harmonic Build (Tracks 7-9)
Part 3: The Aftermath / Outro (Track 10)
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
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.synth_choir_strings import SynthChoirGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator

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
G_MINOR = Scale(root=7, mode=Mode.AEOLIAN)


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
        # Track 7
        "Stripped Beat": 0.90, "Pluck Bass": 0.86, "Noise FX": 0.75,
        # Track 8
        "Choir Pad": 0.82, "Atmosphere": 0.78, "Bell Arp": 0.85,
        # Track 9
        "Epic Chords": 0.86, "Driving Beat": 0.90, "Rolling Bass": 0.86, "Sweep Rise": 0.75,
        # Track 10
        "Ambient Drone": 0.85, "Slow Sweep": 0.78, "Deep Sub": 0.80,
    })
    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan


# ===========================================================================
# PART 1: The Escalation
# ===========================================================================

def track_01_chug_rave():
    """1. Chug Rave (D Minor, 135 BPM)"""
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
    return orchestrator.render(chords, D_MINOR, dur), 135.0


def track_02_tremelo_breaks():
    """2. Tremolo Breaks (E Minor, 150 BPM)"""
    print("  2. Tremolo Breaks")
    dur = 48.0
    chords = _build_chords("i VI III VII i VI III VII i VI III VII i VI III VII", dur, E_MINOR)

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
    return orchestrator.render(chords, E_MINOR, dur), 150.0


def track_03_hardstyle_gallop():
    """3. Hardstyle Gallop (B Minor, 155 BPM) - Added intro breakdown to avoid plateau."""
    print("  3. Hardstyle Gallop")
    dur = 56.0
    chords = _build_chords("i VI III VII i VI III VII i VI III VII i VI III VII i VI III VII", dur, B_MINOR)

    sections = [
        # Added a sudden breakdown to contrast with Track 02
        FormSection("Breakdown", 0.0, 8.0, "p", 0.70, ["strings", "pad"], "mysterious"),
        FormSection("Build", 8.0, 8.0, "mf", 1.0, ["strings", "bass", "percussion"], "tense"),
        FormSection("Drop", 16.0, 32.0, "fff", 1.15, ["strings", "bass", "percussion"], "triumphant"),
        FormSection("Outro", 48.0, 8.0, "mp", 0.85, ["strings"], "dark"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 155.0)
    arc = DynamicsArc.from_form(form)

    gallop = PowerChordGenerator(pattern="gallop", palm_mute_ratio=0.5, gallop_speed=0.20)
    hard = HardstyleGenerator(variant="euphoric", kick_distortion=0.9, reverse_bass_weight=0.6)
    bass = SynthBassGenerator(waveform="reese", pattern="wobble", slide_probability=0.2)
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
    return orchestrator.render(chords, B_MINOR, dur), 155.0


def track_04_neuro_phrygian():
    """4. Neuro Phrygian (F# Phrygian, 160 BPM) - Fixed empty drop with a focused silence section"""
    print("  4. Neuro Phrygian")
    dur = 48.0
    chords = _build_chords("i II i vii i II vii i i II i vii", dur, FS_PHRYGIAN)

    sections = [
        FormSection("Intro", 0.0, 8.0, "mp", 0.90, ["strings"], "mysterious"),
        FormSection("Verse", 8.0, 16.0, "f", 1.0, ["strings", "bass", "percussion"], "frantic"),
        # Replaced the unmotivated gap with an intentional momentary mute
        FormSection("Silence", 24.0, 2.0, "ppp", 0.1, ["bass"], "dark"), 
        FormSection("Chorus", 26.0, 14.0, "ff", 1.10, ["strings", "bass", "percussion"], "triumphant"),
        FormSection("Outro", 40.0, 8.0, "p", 0.80, ["strings"], "dark"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 160.0)
    arc = DynamicsArc.from_form(form)

    riff = RiffGenerator(scale_type="blues", riff_pattern="gallop", palm_mute_prob=0.4)
    dnb = DnBJungleGenerator(variant="neurofunk", break_density=0.8, reese_amount=0.7)
    bass = SynthBassGenerator(waveform="saw", pattern="wobble", filter_accent=1.5)
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
    return orchestrator.render(chords, FS_PHRYGIAN, dur), 160.0


def track_05_sweep_techno():
    """5. Sweep Techno (C Harmonic Minor, 170 BPM)"""
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
    return orchestrator.render(chords, C_HARM_MINOR, dur), 170.0


def track_06_inferno_peak():
    """6. Inferno Peak (A Minor, 175 BPM)"""
    print("  6. Inferno Peak")
    dur = 64.0
    chords = _build_chords("i VI III VII i VI III VII i VI III VII i VI III VII", dur, A_MINOR)

    sections = [
        FormSection("Build", 0.0, 16.0, "p", 0.85, ["strings"], "mysterious"),
        FormSection("Ramp", 16.0, 16.0, "mf", 1.0, ["strings", "bass", "percussion"], "tense"),
        FormSection("Peak", 32.0, 24.0, "fff", 1.15, ["strings", "bass", "percussion"], "triumphant"),
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
    return orchestrator.render(chords, A_MINOR, dur), 175.0


# ===========================================================================
# PART 2: The Reset & Build
# ===========================================================================

def track_07_rhythmic_reset():
    """7. Rhythmic Reset (G Minor, 140 BPM) - Stripped down after the peak."""
    print("  7. Rhythmic Reset")
    dur = 40.0
    chords = _build_chords("i i i i v v v v i i", dur, G_MINOR)

    sections = [
        FormSection("Reset", 0.0, 16.0, "p", 0.8, ["percussion", "bass"], "dark"),
        FormSection("Groove", 16.0, 16.0, "mp", 0.9, ["percussion", "bass", "strings"], "tense"),
        FormSection("Fade", 32.0, 8.0, "pp", 0.7, ["percussion", "bass"], "dark"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 140.0)
    arc = DynamicsArc.from_form(form)

    drums = ElectronicDrumsGenerator(kit="808", pattern="four_on_floor", sidechain=False)
    bass = SynthBassGenerator(waveform="square", pattern="plucked", filter_accent=0.5)
    noise = SynthEffectsGenerator(fx_type="atmosphere")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Stripped Beat", drums, "percussion", "rhythm", "constant"),
            OrchestralLayer("Pluck Bass", bass, "bass", "bass", "constant"),
            OrchestralLayer("Noise FX", noise, "strings", "pad", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    return orchestrator.render(chords, G_MINOR, dur), 140.0


def track_08_atmospheric_theme():
    """8. Atmospheric Theme (G Minor, 140 BPM) - Melodic & harmonic exploration."""
    print("  8. Atmospheric Theme")
    dur = 48.0
    chords = _build_chords("i VI III VII i VI v iv i VI III VII VI VII i i", dur, G_MINOR)

    sections = [
        FormSection("Intro", 0.0, 16.0, "mp", 0.85, ["strings", "pad"], "mysterious"),
        FormSection("Theme", 16.0, 16.0, "mf", 0.95, ["strings", "pad", "solo"], "triumphant"),
        FormSection("Outro", 32.0, 16.0, "p", 0.8, ["strings", "pad"], "dark"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 140.0)
    arc = DynamicsArc.from_form(form)

    choir = SynthChoirGenerator(harmony_count=3)
    atmos = AmbientPadGenerator(voicing="spread", overlap=0.2)
    arp = ArpeggiatorGenerator(pattern="up_down", note_duration=0.25, octaves=2)

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Choir Pad", choir, "strings", "pad", "constant"),
            OrchestralLayer("Atmosphere", atmos, "strings", "pad", "constant"),
            OrchestralLayer("Bell Arp", arp, "strings", "solo", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    return orchestrator.render(chords, G_MINOR, dur), 140.0


def track_09_harmonic_build():
    """9. Harmonic Build (C Harmonic Minor, 155 BPM) - Ramping back up to energy."""
    print("  9. Harmonic Build")
    dur = 48.0
    chords = _build_chords("i VI iv V i VI iv V i VI iv V VI VII i i", dur, C_HARM_MINOR)

    sections = [
        FormSection("Rise", 0.0, 16.0, "mf", 0.9, ["strings", "pad"], "tense"),
        FormSection("Drive", 16.0, 16.0, "f", 1.05, ["strings", "percussion", "bass"], "frantic"),
        FormSection("Climax", 32.0, 16.0, "ff", 1.15, ["strings", "percussion", "bass", "pad"], "triumphant"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 155.0)
    arc = DynamicsArc.from_form(form)

    chords_gen = SupersawPadGenerator(variant="trance", voice_count=5)
    drums = BreakbeatGenerator(variant="amen", chop_probability=0.3)
    bass = DarkBassGenerator(mode="industrial", octave=1)
    sweep = FXRiserGenerator(riser_type="synth", length_beats=16.0)

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Epic Chords", chords_gen, "strings", "pad", "constant"),
            OrchestralLayer("Driving Beat", drums, "percussion", "rhythm", "constant"),
            OrchestralLayer("Rolling Bass", bass, "bass", "bass", "constant"),
            OrchestralLayer("Sweep Rise", sweep, "strings", "solo", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    return orchestrator.render(chords, C_HARM_MINOR, dur), 155.0


# ===========================================================================
# PART 3: The Aftermath
# ===========================================================================

def track_10_ambient_outro():
    """10. Ambient Outro (D Minor, 100 BPM) - Slow, dark, fading out."""
    print("  10. Ambient Outro")
    dur = 32.0
    chords = _build_chords("i v VI iv i v VI iv i i i i", dur, D_MINOR)

    sections = [
        FormSection("Tail", 0.0, 16.0, "p", 0.8, ["pad", "bass"], "dark"),
        FormSection("Fade", 16.0, 16.0, "ppp", 0.5, ["pad"], "mysterious"),
    ]
    form = MusicalForm._create_with_tempo_map(sections, 100.0)
    arc = DynamicsArc.from_form(form)

    drone = AmbientPadGenerator(voicing="spread", overlap=0.3)
    sweep = FilterSweepGenerator(sweep_type="lowpass_close", duration=16.0)
    sub = SynthBassGenerator(waveform="sine", pattern="sub_kick")

    orchestrator = Orchestrator(
        layers=[
            OrchestralLayer("Ambient Drone", drone, "strings", "pad", "constant"),
            OrchestralLayer("Slow Sweep", sweep, "strings", "pad", "constant"),
            OrchestralLayer("Deep Sub", sub, "bass", "bass", "constant"),
        ],
        form=form,
        dynamics=arc,
    )
    return orchestrator.render(chords, D_MINOR, dur), 100.0


# ===========================================================================
# MAIN
# ===========================================================================

TRACKS = [
    # PART 1
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
    # PART 2
    (track_07_rhythmic_reset, "07_Rhythmic_Reset.mid", {
        "Stripped Beat": 0, "Pluck Bass": 38, "Noise FX": 100,
    }),
    (track_08_atmospheric_theme, "08_Atmospheric_Theme.mid", {
        "Choir Pad": 91, "Atmosphere": 95, "Bell Arp": 14,
    }),
    (track_09_harmonic_build, "09_Harmonic_Build.mid", {
        "Epic Chords": 89, "Driving Beat": 0, "Rolling Bass": 34, "Sweep Rise": 97,
    }),
    # PART 3
    (track_10_ambient_outro, "10_Ambient_Outro.mid", {
        "Ambient Drone": 95, "Slow Sweep": 92, "Deep Sub": 38,
    }),
]


def main():
    album_dir = Path("output/album_rave_metal")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        R A V E   I N F E R N O")
    print("        A 10-Track Metal-Rave Crossover Arc")
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
    print(f"  COMPLETE: Rave Inferno — {total_notes} total notes across 10 tracks")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
