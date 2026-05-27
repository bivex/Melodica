# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_black_prince.py — ЧЕРНЫЙ ПРИНЦ (Black Prince)

Genre: Progressive Rock / Fusion
Scale: Hungarian Minor [0, 2, 3, 6, 7, 8, 11]
Характер: Тьма, благородство, техническая сложность, ломаные ритмы.

  I.   Coronation of Shadows (Коронация теней) — 144 BPM, 11/8.
  II.  Alchemy of Blood      (Алхимия крови)   — 96 BPM, 4/4 (Polyrhythmic).
  III. Mirror Throne         (Зеркальный трон) — 128 BPM, 7/4.
  IV.  Eclipse of the Heart  (Затмение сердца) — 66 BPM, 5/4.
  V.   The Final Stand       (Последняя битва) — 160 BPM, Dynamic Meter.
"""

import random
import math
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.midi import export_multitrack_midi
from melodica.composer.articulations import ArticulationEngine
from melodica.composer.harmonic_verifier import verify_and_fix, VerifierConfig
from melodica.composer.tension_curve import TensionCurve, TensionPhase
from melodica.composer.voice_leading import VoiceLeadingEngine

# KEY: E Hungarian Minor (E-F#-G-A#-B-C-D#) - standard "heavy" key
KEY = types.Scale(root=4, mode=types.Mode.HUNGARIAN_MINOR)

# GM Programs
HAMMOND_ORGAN = 18
MOOG_LEAD = 81 # Square Lead
SAW_LEAD = 80  # Sawtooth Lead
GUITAR_OVERDRIVE = 29
GUITAR_DISTORTION = 30
BASS_PICK = 34
BASS_SYNTH = 38
CHOIR = 52
DRUMS = 0 # Percussion

random.seed(777)
OUT = Path("output/album_black_prince")
OUT.mkdir(parents=True, exist_ok=True)

_ART = ArticulationEngine()

# Instrument → articulation profile mapping
_ART_MAP = {
    "organ": "brass_legato",       # sustain, CC11 crescendo, pitch_bend slide-in
    "guitar_l": "strings_melody",  # sustain, vibrato_in, swell
    "guitar_r": "strings_melody",
    "lead": "flute",               # sustain, vibrato_in, swell (synth lead)
    "bass": "cello",               # sustain, vibrato_in, crescendo, pitch_bend slide
    "drums": "snare",              # staccato, short duration
    "pad": "strings_pad",          # fade_in, sustain pedal always
    "fx": "strings_pad",
}

def _art(tracks: dict, dur: float) -> dict:
    """Apply articulation profiles to all tracks."""
    return {
        name: _ART.apply(notes, _ART_MAP.get(name, "strings_melody"), dur)
        for name, notes in tracks.items()
    }

def _smooth_voice_leading(tracks: dict, max_jump: int = 9) -> dict:
    """Reduce large interval jumps in melodic tracks for smoother voice leading.
    Drums excluded — percussion doesn't have voice leading.
    """
    drum_names = {"drums", "percussion", "kick", "snare", "hihat"}
    result = {}
    for name, notes in tracks.items():
        if name in drum_names or not notes:
            result[name] = notes
            continue
        sorted_notes = sorted(notes, key=lambda n: n.start)
        smoothed = []
        prev_pitch = sorted_notes[0].pitch
        for n in sorted_notes:
            jump = n.pitch - prev_pitch
            if abs(jump) > max_jump:
                # Snap to same pitch class within a gentler range
                direction = 1 if jump > 0 else -1
                # Try bringing the note closer by octaves
                candidate = n.pitch
                while abs(candidate - prev_pitch) > max_jump and 0 <= candidate - direction * 12 <= 127:
                    candidate -= direction * 12
                if abs(candidate - prev_pitch) <= max_jump:
                    n = types.NoteInfo(
                        pitch=candidate, start=n.start, duration=n.duration,
                        velocity=n.velocity, articulation=n.articulation,
                        expression=n.expression,
                    )
            smoothed.append(n)
            prev_pitch = n.pitch
        result[name] = smoothed
    return result

def _generate_satb_pad(chords: list, key, vel: int = 40) -> list:
    """Generate a low-register SATB pad from chord progression.
    Drops all voices into register 36-58 to avoid masking melody/guitar/organ.
    """
    engine = VoiceLeadingEngine(strict_mode=True)
    voices = engine.voicize_progression(chords, key)
    pad_notes = []
    for voice_notes in voices.values():
        for n in voice_notes:
            pitch = n.pitch
            # Drop into low register: 36 (C2) to 58 (A#3)
            while pitch > 58:
                pitch -= 12
            while pitch < 36:
                pitch += 12
            pad_notes.append(types.NoteInfo(
                pitch=pitch, start=n.start, duration=n.duration,
                velocity=vel,
            ))
    return pad_notes

# ---------------------------------------------------------------------------
# Tension-aware velocity shaping (replaces fake LUFS mastering)
# ---------------------------------------------------------------------------
# Per-instrument weight: lower register perceived quieter → boost more
_PERCEIVED_WEIGHT = {
    "bass": 1.15, "drums": 1.10, "organ": 0.95,
    "guitar_l": 0.90, "guitar_r": 0.90, "lead": 0.85,
    "pad": 0.60, "fx": 0.65, "choir": 0.80,
}

def _apply_tension_velocity(tracks: dict, dur: float, curve: TensionCurve) -> dict:
    """Shape velocity per-track based on tension curve and perceived loudness."""
    result = {}
    for name, notes in tracks.items():
        weight = _PERCEIVED_WEIGHT.get(name, 0.90)
        shaped = []
        for n in notes:
            tension = curve.tension_at(n.start)
            # tension 0.0→quiet (vel×0.5), 1.0→loud (vel×1.0), shaped by weight
            factor = (0.5 + 0.5 * tension) * weight
            vel = max(15, min(127, int(n.velocity * factor)))
            shaped.append(types.NoteInfo(
                pitch=n.pitch, start=n.start, duration=n.duration,
                velocity=vel, articulation=n.articulation,
                expression=n.expression,
            ))
        result[name] = shaped
    return result

def _balance_tracks(tracks: dict) -> dict:
    """Honest track balancing: RMS normalization + brickwall, no fake LUFS."""
    result = {}
    for name, notes in tracks.items():
        if not notes:
            result[name] = notes
            continue
        rms = math.sqrt(sum(n.velocity ** 2 for n in notes) / len(notes))
        target_rms = 90  # comfortable MIDI velocity RMS
        gain = target_rms / max(rms, 1)
        balanced = []
        for n in notes:
            vel = int(round(n.velocity * gain))
            # Soft-knee above 112
            if vel > 112:
                vel = int(112 + (vel - 112) * 0.4)
            # Brickwall
            vel = max(15, min(126, vel))
            balanced.append(types.NoteInfo(
                pitch=n.pitch, start=n.start, duration=n.duration,
                velocity=vel, articulation=n.articulation,
                expression=n.expression,
            ))
        result[name] = balanced
    return result

def _generate_pan_cc(tracks: dict) -> dict:
    """Static pan CC10 per track (real stereo positioning)."""
    PAN_MAP = {
        "organ": 64, "lead": 58, "bass": 64, "drums": 64,
        "guitar_l": 42, "guitar_r": 86, "pad": 50, "fx": 78, "choir": 60,
    }
    cc_events = {}
    for name, notes in tracks.items():
        if not notes:
            continue
        pan = PAN_MAP.get(name, 64)
        cc_events[name] = [(notes[0].start, 10, pan)]
    return cc_events

# ---------------------------------------------------------------------------
# Full pipeline: generate → articulate → verify → tension → balance → export
# ---------------------------------------------------------------------------
def _pipeline(tracks: dict, path: Path, bpm: float, instruments: dict,
              chords: list = None, curve_type: str = "classical", peak_position: float = 0.7):
    dur = max((n.start + n.duration for ns in tracks.values() for n in ns), default=0)

    # 0. Add SATB pad from voice leading engine (if chords provided)
    if chords:
        pad = _generate_satb_pad(chords, KEY, vel=45)
        if pad:
            tracks = {**tracks, "pad": pad}
            instruments = {**instruments, "pad": 88}  # New Age Pad

    # 1. Smooth voice leading (reduce wild jumps)
    tracks = _smooth_voice_leading(tracks)

    # 2. Articulation (CC automation per instrument)
    tracks = _art(tracks, dur)

    # 3. Harmonic verification (detect + fix cross-track clashes)
    tracks, report = verify_and_fix(tracks, VerifierConfig(dissonance_tolerance=0.4))
    print(f"   Verifier: {report.clashes_detected} clashes, {report.clashes_fixed} fixed "
          f"({report.notes_transposed} transposed, {report.notes_velocity_reduced} vel- reduced)")

    # 4. Tension curve velocity shaping
    curve = TensionCurve(total_beats=dur, curve_type=curve_type,
                         peak_position=peak_position, peak_intensity=0.95)
    tracks = _apply_tension_velocity(tracks, dur, curve)

    # 5. Track balance (RMS normalization + brickwall)
    tracks = _balance_tracks(tracks)

    # 6. Pan CC events
    cc_events = _generate_pan_cc(tracks)

    # 7. Export
    export_multitrack_midi(tracks, str(path), bpm=bpm, key=KEY,
                           instruments=instruments, cc_events=cc_events)

def _off(notes, offset):
    return [
        types.NoteInfo(pitch=n.pitch, start=n.start + offset,
                       duration=n.duration, velocity=n.velocity)
        for n in notes
    ]

# =====================================================================
# I. Coronation of Shadows — 11/8 (3+3+3+2)
# =====================================================================
def produce_coronation():
    print("--- 01_Coronation_of_Shadows ---")
    bpm = 144
    bpc = 5.5 # 11/8 bar
    dur = 220.0
    
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*bpc), duration=bpc) for i in range(int(dur/bpc))]

    # Organ: mid-register (48-67) — below lead, above bass
    organ_riff = MelodyGenerator(
        GeneratorParams(density=0.7, complexity=0.9, velocity_range=(90, 115)),
        phrase_length=bpc, note_range_low=48, note_range_high=67,
        syncopation=0.4
    ).render(chords, KEY, dur)

    # Guitar: lower-mid (36-55) — below organ, above bass
    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.4, velocity_range=(100, 120),
                        key_range_low=36, key_range_high=55),
        pattern="power", note_duration=0.5
    ).render(chords, KEY, dur)

    # Lead Synth Solo (Virtuoso)
    lead = MelodyGenerator(
        GeneratorParams(density=0.8, complexity=1.0, velocity_range=(95, 127)),
        phrase_length=11.0, note_range_low=64, note_range_high=93,
        steps_probability=0.4, random_movement=0.2
    ).render(chords[8:], KEY, dur - 44.0)

    # Active Prog Bass
    bass = BassGenerator(
        GeneratorParams(density=0.6, velocity_range=(100, 120),
                        key_range_low=28, key_range_high=45),
        style="walking"
    ).render(chords, KEY, dur)

    # Drums: 11/8 pattern
    drum_notes = []
    for i in range(int(dur/bpc)):
        t = i * bpc
        drum_notes.append(types.NoteInfo(36, t, 0.5, 110)) # Kick
        drum_notes.append(types.NoteInfo(38, t + 1.5, 0.3, 100)) # Snare
        drum_notes.append(types.NoteInfo(38, t + 3.0, 0.3, 100)) # Snare
        drum_notes.append(types.NoteInfo(42, t + 4.5, 0.2, 90)) # Hihat

    tracks = {"organ": organ_riff, "guitar_l": guitar, "lead": _off(lead, 44.0), "bass": bass, "drums": drum_notes}
    inst = {"organ": HAMMOND_ORGAN, "guitar_l": GUITAR_DISTORTION, "lead": MOOG_LEAD, "bass": BASS_PICK, "drums": 36}
    _pipeline(tracks, OUT / "01_Coronation.mid", bpm, inst, chords=chords, curve_type="classical", peak_position=0.6)

# =====================================================================
# II. Alchemy of Blood — 96 BPM, 4/4
# =====================================================================
def produce_alchemy():
    print("--- 02_Alchemy_of_Blood ---")
    bpm = 96
    dur = 160.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=0, duration=dur)]

    # Polyrhythmic Synth: mid-high (60-79)
    synth_poly = ArpeggiatorGenerator(
        GeneratorParams(density=0.6, velocity_range=(60, 85),
                        key_range_low=60, key_range_high=79),
        pattern="up_down", note_duration=0.333
    ).render(chords, KEY, dur)

    # Guitar: lower-mid (36-55)
    guitar_riff = MelodyGenerator(
        GeneratorParams(density=0.3, complexity=0.6, velocity_range=(95, 120)),
        phrase_length=4.0, note_range_low=36, note_range_high=55
    ).render(chords, KEY, dur)

    # Bass: low register (28-43)
    bass = MelodyGenerator(
        GeneratorParams(density=0.45, complexity=0.7),
        note_range_low=28, note_range_high=43
    ).render(chords, KEY, dur)

    tracks = {"lead": synth_poly, "guitar_l": guitar_riff, "bass": bass}
    inst = {"lead": SAW_LEAD, "guitar_l": GUITAR_OVERDRIVE, "bass": BASS_SYNTH}
    _pipeline(tracks, OUT / "02_Alchemy.mid", bpm, inst, chords=chords, curve_type="build_release", peak_position=0.55)

# =====================================================================
# III. Mirror Throne — 128 BPM, 7/4
# =====================================================================
def produce_throne():
    print("--- 03_Mirror_Throne ---")
    bpm = 128
    bpc = 7.0
    dur = 196.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*bpc), duration=bpc) for i in range(int(dur/bpc))]

    # Keys: mid-register (53-72)
    keys_arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.7, velocity_range=(75, 100),
                        key_range_low=53, key_range_high=72),
        pattern="converge", note_duration=0.25
    ).render(chords, KEY, dur)

    # Guitar: lower-mid (40-58)
    guitar_arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.55, velocity_range=(85, 110),
                        key_range_low=40, key_range_high=58),
        pattern="diverge", note_duration=0.5
    ).render(chords, KEY, dur)

    # Bass Solo: low register (28-48) — below guitar
    bass_solo = MelodyGenerator(
        GeneratorParams(density=0.75, complexity=1.0, velocity_range=(100, 127)),
        note_range_low=28, note_range_high=48
    ).render(chords[16:20], KEY, 28.0)

    tracks = {"organ": keys_arp, "guitar_r": guitar_arp, "bass": _off(bass_solo, 112.0)}
    inst = {"organ": HAMMOND_ORGAN, "guitar_r": GUITAR_DISTORTION, "bass": BASS_PICK}
    _pipeline(tracks, OUT / "03_Throne.mid", bpm, inst, chords=chords, curve_type="edm", peak_position=0.75)

# =====================================================================
# IV. Eclipse of the Heart — 66 BPM, 5/4
# =====================================================================
def produce_eclipse():
    print("--- 04_Eclipse ---")
    bpm = 66
    bpc = 5.0
    dur = 150.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=0, duration=dur)]

    # Melancholic Lead: high (64-81)
    lead = MelodyGenerator(
        GeneratorParams(density=0.15, complexity=0.5),
        phrase_length=10.0, note_range_low=64, note_range_high=81,
        ornament_probability=0.2
    ).render(chords, KEY, dur)

    # Metal Guitar: mid (36-58)
    metal_dur = 40.0
    metal_start = 60.0
    c_metal = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=0, duration=metal_dur)]

    guitar_metal = MelodyGenerator(
        GeneratorParams(density=0.8, velocity_range=(110, 127)),
        phrase_length=5.0, note_range_low=36, note_range_high=58
    ).render(c_metal, KEY, metal_dur)

    tracks = {"lead": lead, "guitar_l": _off(guitar_metal, metal_start)}
    inst = {"lead": MOOG_LEAD, "guitar_l": GUITAR_DISTORTION}
    _pipeline(tracks, OUT / "04_Eclipse.mid", bpm, inst, chords=chords, curve_type="ambient", peak_position=0.6)

# =====================================================================
# V. The Final Stand — 160 BPM, Epic Finale
# =====================================================================
def produce_final():
    print("--- 05_Final_Stand ---")
    bpm = 160
    dur = 320.0
    # Modulating chord sequence (prog standard)
    p = "i iv v vii " * 8 + "i bII iv bVI " * 8
    from melodica.utils import chord_at
    chords = []
    for i, roman in enumerate(p.split()):
        c = KEY.parse_roman(roman)
        c.start = i * 4.0
        c.duration = 4.0
        chords.append(c)

    # Organ: mid-register (48-67), longer notes to reduce note count
    organ = ArpeggiatorGenerator(
        GeneratorParams(density=0.35, velocity_range=(100, 125),
                        key_range_low=48, key_range_high=67),
        pattern="chord", note_duration=2.0
    ).render(chords, KEY, dur)

    # Dual Guitar: lower-mid (36-55)
    g_gen = MelodyGenerator(GeneratorParams(density=0.6, complexity=0.8,
                                            key_range_low=36, key_range_high=55))
    g1 = g_gen.render(chords, KEY, dur)
    g2 = [types.NoteInfo(n.pitch + 7, n.start, n.duration, n.velocity) for n in g1] # 5th harmony
    # Re-snap g2
    from melodica.utils import snap_to_scale
    for n in g2:
        n.pitch = snap_to_scale(n.pitch, KEY)

    # Final Ascending Run (high register lead)
    climax = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, key_range_low=64, key_range_high=100, velocity_range=(120, 127)),
        pattern="up", note_duration=0.1
    ).render(chords[-8:], KEY, 32.0)

    tracks = {
        "organ": organ,
        "guitar_l": g1 + _off(climax, dur-32.0),
        "guitar_r": g2 + _off(climax, dur-32.0),
        "lead": _off(climax, dur-32.0)
    }
    inst = {"organ": HAMMOND_ORGAN, "guitar_l": GUITAR_DISTORTION, "guitar_r": GUITAR_OVERDRIVE, "lead": SAW_LEAD}
    _pipeline(tracks, OUT / "05_Final.mid", bpm, inst, chords=chords, curve_type="classical", peak_position=0.85)

# =====================================================================
# EXECUTION
# =====================================================================
print("=" * 60)
print("   ЧЕРНЫЙ ПРИНЦ (BLACK PRINCE)")
print("   Prog Rock / Hungarian Minor")
print("=" * 60)

produce_coronation()
produce_alchemy()
produce_throne()
produce_eclipse()
produce_final()

print("\n" + "=" * 60)
print("   ALBUM COMPLETE.")
print(f"   Files in: {OUT}")
print("=" * 60)
