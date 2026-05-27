# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_five_instruments.py — 4-track demo album.
Each track uses 5 explicit instruments so you can hear how the engine
layers melody, harmony, bass, rhythm and texture together.

Instruments per track:
  1. Dawn Signal     — Melody(Piano) + Arp(Harp) + Bass(Finger Bass) + Strings + Drums
  2. Rust District   — Melody(Tenor Sax) + Walking Bass + Piano Comp + Strings + Drums
  3. Neon Veil       — Lead Synth + Bass(Synth) + Arp(Harp) + Melody(Pad) + Drums
  4. Last Frequency  — Melody(Cello) + Strings + Piano + Arp(Harp) + Drums
"""

from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


def _chords(progression: str, key: types.Scale, duration: float):
    parts = progression.split()
    bpc = duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        c = key.parse_roman(p)
        c.start = i * bpc
        c.duration = bpc
        chords.append(c)
    return chords


def _master(raw: dict, bpm: float, lufs: float = -12.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "melody": 1.0, "bass": 1.1, "arp": 0.8,
        "strings": 0.7, "drums": 0.9, "lead": 0.95,
        "piano": 0.9, "walking_bass": 1.05, "pad_melody": 0.75,
    })
    mixed = desk.apply_mixing(raw, [("Dynamics", 400, [])], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# =====================================================================
# Track 1 — Dawn Signal (Ambient Chill, 72 BPM, C Major)
# =====================================================================
def produce_dawn_signal():
    """Ambient chill: slow melody over harp arpeggios with soft strings."""
    print("  I. Dawn Signal [Ambient/Chill — 72 BPM — C Major]")

    key = types.Scale(root=0, mode=types.Mode.MAJOR)  # C Major
    dur = 96.0
    prog = ("I vi IV V " * 3).strip()
    chords = _chords(prog, key, dur)

    # 1. Melody — Piano (slow, spacious)
    melody = MelodyGenerator(
        GeneratorParams(density=0.22, leap_probability=0.15),
        drama_shape="crescendo", drama_peak=0.6,
        harmony_note_probability=0.85,
        note_range_low=60, note_range_high=79,
        phrase_length=8.0,
        register_smoothness=0.9,
        steps_probability=0.85,
        first_note="tonic",
        motif_probability=0.6,
    ).render(chords, key, dur)

    # 2. Arpeggiator — Harp (gentle up pattern)
    arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.6),
        pattern="up", note_duration=0.5,
        voicing="open", octaves=2,
    ).render(chords, key, dur)

    # 3. Bass — Finger Bass (root only, sparse)
    bass = BassGenerator(
        GeneratorParams(density=0.35, key_range_low=36, key_range_high=48),
        style="root_fifth",
    ).render(chords, key, dur)

    # 4. Strings — sustained pads
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=72),
        articulation="sustained", divisi=3,
        dynamic_curve="crescendo",
    ).render(chords, key, dur)

    # 5. Drums — minimal electronic
    drums = ElectronicDrumsGenerator(
        GeneratorParams(density=0.3),
        kit="808", pattern="minimal",
    ).render(chords, key, dur)

    raw = {"melody": melody, "arp": arp, "bass": bass, "strings": strings, "drums": drums}
    mastered, pan = _master(raw, 72.0, lufs=-16.0)
    return mastered, pan, 72.0, key, {
        "melody": 1,    # Acoustic Grand Piano
        "arp": 46,      # Harp
        "bass": 33,     # Electric Bass (finger)
        "strings": 49,  # String Ensemble 1
        "drums": 0,     # Channel 10
    }


# =====================================================================
# Track 2 — Rust District (Dark Jazz, 95 BPM, Bb Minor)
# =====================================================================
def produce_rust_district():
    """Dark jazz: walking bass, piano comp, smoky sax melody."""
    print("  II. Rust District [Dark Jazz — 95 BPM — Bb Minor]")

    key = types.Scale(root=10, mode=types.Mode.NATURAL_MINOR)  # Bb Minor
    dur = 128.0
    prog = ("i iv VII III i iv V i " * 4).strip()
    chords = _chords(prog, key, dur)

    # 1. Melody — Tenor Sax (angular, bluesy)
    melody = MelodyGenerator(
        GeneratorParams(density=0.55, leap_probability=0.4),
        drama_shape="tension_release", drama_peak=0.65,
        harmony_note_probability=0.5,
        note_range_low=54, note_range_high=74,
        phrase_length=4.0,
        syncopation=0.6,
        rhythm_variety=0.8,
        after_leap="step_any",
        random_movement=0.45,
        motif_probability=0.7,
        motif_variation="any",
        ornament_probability=0.25,
    ).render(chords, key, dur)

    # 2. Walking Bass
    walking_bass = WalkingBassGenerator(
        GeneratorParams(density=0.8, key_range_low=34, key_range_high=46),
        approach_style="mixed",
        connect_roots=True,
        add_chromatic_passing=True,
        swing_eighth_ratio=0.67,
    ).render(chords, key, dur)

    # 3. Piano Comp — jazz shell voicings
    piano = PianoCompGenerator(
        GeneratorParams(density=0.45, key_range_low=48, key_range_high=79),
        comp_style="jazz",
        voicing_type="shell",
        accent_pattern="syncopated",
        chord_density=0.7,
    ).render(chords, key, dur)

    # 4. Strings — pizzicato stabs
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.35, key_range_low=48, key_range_high=67),
        articulation="pizz", divisi=2,
        dynamic_curve="flat",
    ).render(chords, key, dur)

    # 5. Drums — brush-style (CR78 kit, minimal)
    drums = ElectronicDrumsGenerator(
        GeneratorParams(density=0.45),
        kit="cr78", pattern="minimal",
    ).render(chords, key, dur)

    raw = {"melody": melody, "walking_bass": walking_bass, "piano": piano,
           "strings": strings, "drums": drums}
    mastered, pan = _master(raw, 95.0, lufs=-11.0)
    return mastered, pan, 95.0, key, {
        "melody": 66,       # Tenor Sax
        "walking_bass": 32, # Acoustic Bass
        "piano": 1,         # Bright Piano
        "strings": 45,      # Pizzicato Strings
        "drums": 0,
    }


# =====================================================================
# Track 3 — Neon Veil (Synthwave, 128 BPM, E Minor)
# =====================================================================
def produce_neon_veil():
    """Synthwave: big lead synth, rolling arp, punchy bass, driving drums."""
    print("  III. Neon Veil [Synthwave — 128 BPM — E Minor]")

    key = types.Scale(root=4, mode=types.Mode.NATURAL_MINOR)  # E Minor
    dur = 128.0
    prog = ("i VI III VII i VI VII i " * 4).strip()
    chords = _chords(prog, key, dur)

    # 1. Lead Synth — supersaw lead
    lead = LeadSynthGenerator(
        GeneratorParams(density=0.7, leap_probability=0.5, complexity=0.7),
        style="supersaw",
        portamento=0.2,
        vibrato_rate=0.4,
        vibrato_depth=0.15,
        note_length="mixed",
    ).render(chords, key, dur)

    # 2. Bass — synth bass (wobble style would be overkill, root_fifth works)
    bass = BassGenerator(
        GeneratorParams(density=0.7, key_range_low=28, key_range_high=40),
        style="root_fifth_octave",
    ).render(chords, key, dur)

    # 3. Arp — harp-like sixteenth pattern
    arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.8),
        pattern="up_down", note_duration=0.25,
        voicing="closed", octaves=2,
    ).render(chords, key, dur)

    # 4. Pad Melody — warm pad playing a slow counter-melody
    pad_melody = MelodyGenerator(
        GeneratorParams(density=0.2, leap_probability=0.1),
        drama_shape="epic", drama_peak=0.55,
        harmony_note_probability=0.9,
        note_range_low=48, note_range_high=67,
        phrase_length=16.0,
        register_smoothness=0.95,
        steps_probability=0.9,
        first_note="tonic",
    ).render(chords, key, dur)

    # 5. Drums — 909 four on the floor
    drums = ElectronicDrumsGenerator(
        GeneratorParams(density=0.75),
        kit="909", pattern="four_on_floor",
        sidechain=True,
    ).render(chords, key, dur)

    raw = {"lead": lead, "bass": bass, "arp": arp, "pad_melody": pad_melody, "drums": drums}
    mastered, pan = _master(raw, 128.0, lufs=-8.0)
    return mastered, pan, 128.0, key, {
        "lead": 81,        # Sawtooth Lead
        "bass": 38,        # Synth Bass 1
        "arp": 46,         # Harp
        "pad_melody": 89,  # Warm Pad
        "drums": 0,
    }


# =====================================================================
# Track 4 — Last Frequency (Epic/Cinematic, 88 BPM, D Minor)
# =====================================================================
def produce_last_frequency():
    """Cinematic epic: full strings, solo cello melody, building to climax."""
    print("  IV. Last Frequency [Cinematic/Epic — 88 BPM — D Minor]")

    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)  # D Minor
    dur = 144.0

    # Two-section progression: sparse opening → massive climax
    prog_a = ("i VI iv V " * 4).strip()   # 16 chords — gentle
    prog_b = ("i ii VI VII " * 3).strip() # 12 chords — intense
    prog = prog_a + " " + prog_b
    chords_full = _chords(prog.strip(), key, dur)

    split_at = 16 * (dur / len(prog.strip().split()))
    chords_a = [c for c in chords_full if c.start < split_at]
    chords_b = [c for c in chords_full if c.start >= split_at]
    dur_a = split_at
    dur_b = dur - split_at

    # 1. Melody — Cello (two renders: gentle → intense)
    melody_a = MelodyGenerator(
        GeneratorParams(density=0.25, leap_probability=0.15),
        drama_shape="crescendo", drama_peak=0.5,
        harmony_note_probability=0.85,
        note_range_low=48, note_range_high=67,
        phrase_length=12.0,
        register_smoothness=0.92,
        steps_probability=0.88,
        first_note="tonic",
        motif_probability=0.8,
    ).render(chords_a, key, dur_a)

    melody_b = MelodyGenerator(
        GeneratorParams(density=0.65, leap_probability=0.5),
        drama_shape="epic", drama_peak=0.85,
        harmony_note_probability=0.45,
        note_range_low=55, note_range_high=84,
        phrase_length=6.0,
        syncopation=0.4,
        random_movement=0.4,
        motif_probability=0.9,
        motif_variation="any",
        ornament_probability=0.35,
    ).render(chords_b, key, dur_b)

    # Offset section B
    for n in melody_b:
        n.start += split_at
    melody = melody_a + melody_b

    # 2. Strings — full ensemble (sustained, building)
    strings_a = StringsEnsembleGenerator(
        GeneratorParams(density=0.3, key_range_low=41, key_range_high=72),
        articulation="sustained", divisi=4,
        dynamic_curve="crescendo",
    ).render(chords_a, key, dur_a)

    strings_b = StringsEnsembleGenerator(
        GeneratorParams(density=0.65, key_range_low=36, key_range_high=79),
        articulation="sustained", divisi=6,
        dynamic_curve="crescendo",
    ).render(chords_b, key, dur_b)

    for n in strings_b:
        n.start += split_at
    strings = strings_a + strings_b

    # 3. Piano — sparse octaves in A, chords in B
    piano_a = PianoCompGenerator(
        GeneratorParams(density=0.2, key_range_low=48, key_range_high=72),
        comp_style="pop", voicing_type="close",
        accent_pattern="2_4", chord_density=0.5,
    ).render(chords_a, key, dur_a)

    piano_b = PianoCompGenerator(
        GeneratorParams(density=0.6, key_range_low=36, key_range_high=84),
        comp_style="jazz", voicing_type="shell",
        accent_pattern="syncopated", chord_density=0.8,
    ).render(chords_b, key, dur_b)

    for n in piano_b:
        n.start += split_at
    piano = piano_a + piano_b

    # 4. Arp — slow in A, fast in B
    arp_a = ArpeggiatorGenerator(
        GeneratorParams(density=0.35),
        pattern="up", note_duration=1.0,
        voicing="open", octaves=1,
    ).render(chords_a, key, dur_a)

    arp_b = ArpeggiatorGenerator(
        GeneratorParams(density=0.85),
        pattern="alberti", note_duration=0.25,
        voicing="spread", octaves=2,
    ).render(chords_b, key, dur_b)

    for n in arp_b:
        n.start += split_at
    arp = arp_a + arp_b

    # 5. Drums — none in A, building in B
    drums_a = ElectronicDrumsGenerator(
        GeneratorParams(density=0.1),
        kit="808", pattern="minimal",
    ).render(chords_a, key, dur_a)

    drums_b = ElectronicDrumsGenerator(
        GeneratorParams(density=0.8),
        kit="909", pattern="four_on_floor",
        sidechain=True,
    ).render(chords_b, key, dur_b)

    for n in drums_b:
        n.start += split_at
    drums = drums_a + drums_b

    raw = {"melody": melody, "strings": strings, "piano": piano,
           "arp": arp, "drums": drums}
    mastered, pan = _master(raw, 88.0, lufs=-9.0)
    return mastered, pan, 88.0, key, {
        "melody": 42,     # Cello
        "strings": 48,    # String Ensemble 2
        "piano": 0,       # Acoustic Grand Piano
        "arp": 46,        # Harp
        "drums": 0,
    }


# =====================================================================
# Main
# =====================================================================
def main():
    album_dir = Path("output/album_five_instruments")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   ALBUM: FIVE INSTRUMENTS")
    print("   4 tracks x 5 instruments each")
    print("=" * 60 + "\n")

    tracks = [
        ("01_Dawn_Signal",     produce_dawn_signal),
        ("02_Rust_District",   produce_rust_district),
        ("03_Neon_Veil",       produce_neon_veil),
        ("04_Last_Frequency",  produce_last_frequency),
    ]

    for name, producer in tracks:
        print(f"\n--- {name} ---")
        mastered, pan, bpm, key, instr = producer()
        export_multitrack_midi(
            mastered,
            str(album_dir / f"{name}.mid"),
            bpm=bpm,
            key=key,
            cc_events=pan,
            instruments=instr,
        )
        inst_names = {v: k for k, v in {
            "Piano": 1, "Harp": 46, "Finger Bass": 33, "Strings": 49,
            "Tenor Sax": 66, "Acoustic Bass": 32, "Pizz Str": 45,
            "Sawtooth Lead": 81, "Synth Bass": 38, "Warm Pad": 89,
            "Cello": 42, "Ens 2": 48, "Grand Piano": 0,
        }.items()}
        print(f"    -> {name}.mid  ({bpm} BPM, {len(mastered)} tracks)")
        for track_name, program in instr.items():
            gm_name = inst_names.get(program, f"GM#{program}")
            note_count = sum(len(v) for k, v in mastered.items() if k == track_name)
            print(f"       {track_name:16s}  {gm_name:20s}  {note_count:>4d} notes")

    print("\n" + "=" * 60)
    print(f"   DONE. Files in: {album_dir}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
