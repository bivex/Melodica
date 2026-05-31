"""Sokki — Brainrot Casual Game Soundtrack (9 tracks)

A quirky, playful ambient album for the casual game "Sokki".
Dreamy pads, bouncy arpeggios, mysterious void zones, and sleepy
night-mode vibes. Leitmotif system ties the whole game together.

Run: python scripts/albums/ambient/album_sokki.py
"""

import random
from pathlib import Path

from melodica.types import Scale, Mode, Quality, ChordLabel, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators import (
    BassDrumGenerator, TriangleGenerator, GongGenerator,
)
from melodica.composer import Motif, LeitmotifRegistry
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

random.seed(777)
OUT = Path("output/sokki")
OUT.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Scales
# ------------------------------------------------------------------
C_MAJ    = Scale(root=0, mode=Mode.MAJOR)
G_LYD    = Scale(root=7, mode=Mode.LYDIAN)
D_DOR    = Scale(root=2, mode=Mode.DORIAN)
A_DOR    = Scale(root=9, mode=Mode.DORIAN)
F_LYD    = Scale(root=5, mode=Mode.LYDIAN)
E_PHRYG  = Scale(root=4, mode=Mode.PHRYGIAN)
C_ACO    = Scale(root=0, mode=Mode.ACOUSTIC_MAJOR)

# ------------------------------------------------------------------
# GM Programs
# ------------------------------------------------------------------
PIANO       = 0
HARP        = 46
FLUTE       = 73
CELLO       = 42
PAD_WARM    = 89
PAD_SPACE   = 91
CHOIR       = 52
TUBULAR     = 14
XYLOPHONE   = 13
MUSIC_BOX   = 10
NYLON       = 24
VIBRAPHONE  = 11
SITAR       = 104

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _off(notes, offset):
    return [
        NoteInfo(pitch=n.pitch, start=n.start + offset,
                 duration=n.duration, velocity=n.velocity)
        for n in notes
    ]


def _master(raw, bpm, lufs=-16.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "bowl": 0.6, "pad": 0.4, "flute": 0.65, "cello": 0.45,
        "harp": 0.55, "drone": 0.3, "bells": 0.5, "piano": 0.6,
        "arp": 0.45, "choir": 0.4, "vibes": 0.5, "xbox": 0.55,
        "melody": 0.6, "mbox": 0.5, "bdrum": 0.25, "gong": 0.3,
        "sitar": 0.5, "nylon": 0.55, "tri": 0.3,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def _export(tracks, path, bpm, key, instruments, lufs=-16.0):
    final_notes, cc_events = _master(tracks, bpm, lufs)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)


# ------------------------------------------------------------------
# Leitmotifs — Sokki's thematic DNA
# ------------------------------------------------------------------
registry = LeitmotifRegistry()

# Main theme — Sokki's signature (bouncy, 5-note)
sokki_theme = Motif.from_notes([
    NoteInfo(pitch=72, start=0.0, duration=1.0, velocity=65),
    NoteInfo(pitch=76, start=1.0, duration=1.0, velocity=60),
    NoteInfo(pitch=74, start=2.0, duration=0.5, velocity=55),
    NoteInfo(pitch=79, start=2.5, duration=1.0, velocity=65),
    NoteInfo(pitch=72, start=3.5, duration=1.5, velocity=60),
])

# Mystery motif — the void, the unknown
void_motif = Motif.from_notes([
    NoteInfo(pitch=60, start=0.0, duration=3.0, velocity=45),
    NoteInfo(pitch=63, start=3.0, duration=2.0, velocity=40),
    NoteInfo(pitch=58, start=5.0, duration=4.0, velocity=45),
])

# Victory jingle
victory_motif = Motif.from_notes([
    NoteInfo(pitch=72, start=0.0, duration=0.5, velocity=75),
    NoteInfo(pitch=76, start=0.5, duration=0.5, velocity=70),
    NoteInfo(pitch=79, start=1.0, duration=0.5, velocity=75),
    NoteInfo(pitch=84, start=1.5, duration=2.0, velocity=80),
])

registry.register("sokki", sokki_theme,
    tags=["hero", "playful", "main"], instrument=XYLOPHONE, velocity=65)
registry.register("void", void_motif,
    tags=["mystery", "dark", "void"], instrument=PAD_SPACE, velocity=45)
registry.register("victory", victory_motif,
    tags=["win", "bright", "triumphant"], instrument=TUBULAR, velocity=75)

# Evolve variants for different contexts
registry.evolve("sokki", "sleepy", augment_factor=2.0, transpose=-12)
registry.evolve("sokki", "sped_up", diminish_factor=2.0, transpose=7)
registry.evolve("sokki", "void_corrupt", invert=True, transpose=-7, augment_factor=1.5)
registry.evolve("void", "deep", augment_factor=3.0, transpose=-12)


# ------------------------------------------------------------------
# Track 1: Loading Screen
# ------------------------------------------------------------------
def produce_track_01():
    print("--- 01_Loading_Screen ---")
    bpm = 44
    dur = 160.0
    key = C_MAJ
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=dur)]

    # Deep pad — the world materializing
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.06, key_range_low=48, key_range_high=72),
        voicing="spread", overlap=1.0
    ).render(chords, key, dur)

    # Sokki theme on music box, very slow, delayed entry
    mbox = registry.render("sokki", variant="sleepy", offset=20.0)
    mbox += registry.render("sokki", variant="sleepy", offset=40.0,
                            transpose=5, augment_factor=1.5)

    # Gentle drone
    drone = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=48, key_range_high=49),
        velocity=30
    ).render(chords, key, dur)

    # Bowl hits — loading indicators
    bowls = [
        NoteInfo(pitch=72, start=10.0, duration=12.0, velocity=50),
        NoteInfo(pitch=67, start=50.0, duration=14.0, velocity=45),
        NoteInfo(pitch=64, start=90.0, duration=12.0, velocity=50),
        NoteInfo(pitch=72, start=130.0, duration=16.0, velocity=55),
    ]

    _export(
        {"pad": pad, "mbox": mbox, "drone": drone, "bowl": bowls},
        OUT / "01_Loading_Screen.mid", bpm, key,
        {"pad": PAD_WARM, "mbox": MUSIC_BOX, "drone": PAD_SPACE, "bowl": TUBULAR},
    )


# ------------------------------------------------------------------
# Track 2: Main Lobby
# ------------------------------------------------------------------
def produce_track_02():
    print("--- 02_Main_Lobby ---")
    bpm = 56
    dur = 180.0
    key = G_LYD
    chords = [
        ChordLabel(root=7, quality=Quality.MAJOR, start=0, duration=90),
        ChordLabel(root=0, quality=Quality.MAJOR, start=90, duration=90),
    ]

    # Bouncy harp arpeggio — the lobby feels alive
    arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.10, key_range_low=55, key_range_high=79),
        pattern="up_down", note_duration=1.5
    ).render(chords, key, dur)

    # Sokki theme on xylophone — repeated at intervals
    melody_notes = []
    for i in range(5):
        off = 15.0 + i * 32.0
        t = i * 2 % 7  # Vary transposition
        melody_notes += registry.render("sokki", offset=off, transpose=t)

    # Warm pad
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.07, key_range_low=48, key_range_high=67),
        voicing="spread", overlap=1.0
    ).render(chords, key, dur)

    # Bass drone
    drone = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=36, key_range_high=37),
        velocity=35
    ).render(chords, key, dur)

    _export(
        {"arp": arp, "melody": melody_notes, "pad": pad, "drone": drone},
        OUT / "02_Main_Lobby.mid", bpm, key,
        {"arp": HARP, "melody": XYLOPHONE, "pad": PAD_WARM, "drone": CELLO},
    )


# ------------------------------------------------------------------
# Track 3: First Level — Playful
# ------------------------------------------------------------------
def produce_track_03():
    print("--- 03_First_Level ---")
    bpm = 64
    dur = 200.0
    key = C_MAJ
    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=50),
        ChordLabel(root=7, quality=Quality.MAJOR, start=50, duration=50),
        ChordLabel(root=9, quality=Quality.MINOR, start=100, duration=50),
        ChordLabel(root=0, quality=Quality.MAJOR, start=150, duration=50),
    ]

    # Sped-up Sokki theme as recurring element
    melody_notes = []
    for i in range(7):
        off = 8.0 + i * 26.0
        melody_notes += registry.render("sokki", variant="sped_up", offset=off)

    # Bouncy arpeggio — level music energy
    arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.12, key_range_low=60, key_range_high=84),
        pattern="up", note_duration=0.8
    ).render(chords, key, dur)

    # Light pad
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.05, key_range_low=48, key_range_high=72),
        voicing="close", overlap=0.8
    ).render(chords, key, dur)

    # Bass
    bass = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=36, key_range_high=40),
        velocity=40
    ).render(chords, key, dur)

    _export(
        {"melody": melody_notes, "arp": arp, "pad": pad, "drone": bass},
        OUT / "03_First_Level.mid", bpm, key,
        {"melody": XYLOPHONE, "arp": VIBRAPHONE, "pad": PAD_WARM, "drone": CELLO},
    )


# ------------------------------------------------------------------
# Track 4: The Void Zone — Mysterious
# ------------------------------------------------------------------
def produce_track_04():
    print("--- 04_The_Void_Zone ---")
    bpm = 48
    dur = 220.0
    key = E_PHRYG
    chords = [
        ChordLabel(root=4, quality=Quality.MINOR, start=0, duration=110),
        ChordLabel(root=0, quality=Quality.MINOR, start=110, duration=110),
    ]

    # Void motif — corrupted Sokki theme
    void_notes = registry.render("void", offset=30.0)
    void_notes += registry.render("sokki", variant="void_corrupt", offset=80.0)
    void_notes += registry.render("void", variant="deep", offset=140.0)

    # Dark pad
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.04, key_range_low=36, key_range_high=60),
        voicing="spread", overlap=1.0
    ).render(chords, key, dur)

    # Low drone
    drone = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=24, key_range_high=25),
        velocity=30
    ).render(chords, key, dur)

    # Gong swells — void presence
    gong = GongGenerator(pattern_type="crescendo").render(chords, key, dur)

    # Sparse creepy melody
    flute = MelodyGenerator(
        GeneratorParams(density=0.03, velocity_range=(30, 50)),
        phrase_length=20.0, note_range_low=60, note_range_high=72,
        register_smoothness=0.95
    ).render(chords, key, dur - 60.0)
    flute = _off(flute, 40.0)

    _export(
        {"melody": void_notes, "pad": pad, "drone": drone,
         "gong": gong, "flute": flute},
        OUT / "04_The_Void_Zone.mid", bpm, key,
        {"melody": PAD_SPACE, "pad": PAD_WARM, "drone": CELLO,
         "gong": 0, "flute": FLUTE},
        lufs=-18.0,
    )


# ------------------------------------------------------------------
# Track 5: Speed Run — Energetic
# ------------------------------------------------------------------
def produce_track_05():
    print("--- 05_Speed_Run ---")
    bpm = 100
    dur = 120.0
    key = D_DOR
    chords = [
        ChordLabel(root=2, quality=Quality.MINOR, start=0, duration=30),
        ChordLabel(root=7, quality=Quality.MAJOR, start=30, duration=30),
        ChordLabel(root=0, quality=Quality.MAJOR, start=60, duration=30),
        ChordLabel(root=9, quality=Quality.MINOR, start=90, duration=30),
    ]

    # Fast Sokki theme variations
    melody_notes = []
    for i in range(5):
        off = 5.0 + i * 22.0
        t = [0, 5, 7, -2, 0][i]
        melody_notes += registry.render("sokki", variant="sped_up",
                                        offset=off, transpose=t)

    # Fast arp
    arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.15, key_range_low=55, key_range_high=79),
        pattern="up", note_duration=0.5
    ).render(chords, key, dur)

    # Pad
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.06, key_range_low=48, key_range_high=72),
        voicing="close", overlap=0.8
    ).render(chords, key, dur)

    # Light bass drum pulse
    bdrum = BassDrumGenerator(pattern_type="march").render(chords, key, dur)

    # Nylon guitar counter
    nylon_mel = MelodyGenerator(
        GeneratorParams(density=0.08, velocity_range=(40, 60)),
        phrase_length=12.0, note_range_low=60, note_range_high=72,
        register_smoothness=0.85
    ).render(chords, key, dur)

    _export(
        {"melody": melody_notes, "arp": arp, "pad": pad,
         "bdrum": bdrum, "nylon": nylon_mel},
        OUT / "05_Speed_Run.mid", bpm, key,
        {"melody": XYLOPHONE, "arp": HARP, "pad": PAD_WARM,
         "bdrum": 0, "nylon": NYLON},
    )


# ------------------------------------------------------------------
# Track 6: Boss Room — Tension
# ------------------------------------------------------------------
def produce_track_06():
    print("--- 06_Boss_Room ---")
    bpm = 72
    dur = 180.0
    key = A_DOR
    chords = [
        ChordLabel(root=9, quality=Quality.MINOR, start=0, duration=60),
        ChordLabel(root=2, quality=Quality.MINOR, start=60, duration=60),
        ChordLabel(root=7, quality=Quality.MAJOR, start=120, duration=60),
    ]

    # Dark Sokki variant for boss fight
    boss_notes = registry.render_for("sokki", "aggressive", offset=10.0)
    boss_notes += registry.render("sokki", variant="void_corrupt",
                                  offset=50.0, transpose=-3)
    boss_notes += registry.render_for("sokki", "dark", offset=100.0)
    boss_notes += registry.render("sokki", offset=150.0,
                                  retrograde=True, transpose=5,
                                  augment_factor=1.5)

    # Dark pad
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.05, key_range_low=36, key_range_high=60),
        voicing="spread", overlap=1.0
    ).render(chords, key, dur)

    # Bass drone
    drone = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=24, key_range_high=28),
        velocity=35
    ).render(chords, key, dur)

    # Triangle shimmer
    tri = TriangleGenerator(pattern_type="trill").render(chords, key, dur)

    # Gong
    gong = GongGenerator(pattern_type="crescendo").render(chords, key, dur)

    _export(
        {"melody": boss_notes, "pad": pad, "drone": drone,
         "tri": tri, "gong": gong},
        OUT / "06_Boss_Room.mid", bpm, key,
        {"melody": XYLOPHONE, "pad": PAD_SPACE, "drone": CELLO,
         "tri": 0, "gong": 0},
        lufs=-16.0,
    )


# ------------------------------------------------------------------
# Track 7: Victory Screen
# ------------------------------------------------------------------
def produce_track_07():
    print("--- 07_Victory_Screen ---")
    bpm = 60
    dur = 140.0
    key = F_LYD
    chords = [ChordLabel(root=5, quality=Quality.MAJOR, start=0, duration=dur)]

    # Victory motif — bright and celebratory
    victory_notes = registry.render("victory", offset=10.0)
    victory_notes += registry.render("victory", offset=40.0, transpose=5)
    victory_notes += registry.render("victory", offset=80.0, transpose=7,
                                     augment_factor=1.5)
    victory_notes += registry.render("victory", offset=110.0,
                                     retrograde=True)

    # Layered Sokki triumphant mood
    sokki_bright = registry.render_for("sokki", "triumphant", offset=20.0)
    sokki_bright += registry.render_for("sokki", "triumphant", offset=60.0,
                                         intensity=1.3)

    # Bright pad
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.07, key_range_low=55, key_range_high=79),
        voicing="spread", overlap=1.0
    ).render(chords, key, dur)

    # Harp arpeggio
    arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.10, key_range_low=60, key_range_high=84),
        pattern="up", note_duration=1.5
    ).render(chords, key, dur)

    # Tubular bells
    bells = [
        NoteInfo(pitch=72, start=10.0, duration=6.0, velocity=70),
        NoteInfo(pitch=76, start=40.0, duration=5.0, velocity=65),
        NoteInfo(pitch=79, start=80.0, duration=6.0, velocity=70),
        NoteInfo(pitch=84, start=110.0, duration=8.0, velocity=75),
    ]

    _export(
        {"bells": victory_notes, "melody": sokki_bright,
         "pad": pad, "arp": arp, "chime": bells},
        OUT / "07_Victory_Screen.mid", bpm, key,
        {"bells": TUBULAR, "melody": XYLOPHONE, "pad": PAD_WARM,
         "arp": HARP, "chime": TUBULAR},
    )


# ------------------------------------------------------------------
# Track 8: Night Mode — Sleepy
# ------------------------------------------------------------------
def produce_track_08():
    print("--- 08_Night_Mode ---")
    bpm = 42
    dur = 240.0
    key = C_ACO
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=dur)]

    # Sleepy Sokki — very slow, low register
    sleepy = registry.render("sokki", variant="sleepy", offset=30.0)
    sleepy += registry.render("sokki", variant="sleepy", offset=80.0,
                               transpose=-5, augment_factor=1.5)
    sleepy += registry.render("sokki", variant="sleepy", offset=150.0,
                               transpose=3)
    sleepy += registry.render("sokki", variant="sleepy", offset=200.0,
                               retrograde=True)

    # Ultra-soft pad
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.04, key_range_low=36, key_range_high=60),
        voicing="spread", overlap=1.0
    ).render(chords, key, dur)

    # Deep drone
    drone = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=24, key_range_high=25),
        velocity=25
    ).render(chords, key, dur)

    # Music box lullaby
    mbox = MelodyGenerator(
        GeneratorParams(density=0.03, velocity_range=(30, 50)),
        phrase_length=24.0, note_range_low=67, note_range_high=79,
        register_smoothness=0.95
    ).render(chords, key, dur - 80.0)
    mbox = _off(mbox, 60.0)

    _export(
        {"melody": sleepy, "pad": pad, "drone": drone, "mbox": mbox},
        OUT / "08_Night_Mode.mid", bpm, key,
        {"melody": MUSIC_BOX, "pad": PAD_WARM, "drone": CELLO,
         "mbox": MUSIC_BOX},
        lufs=-20.0,
    )


# ------------------------------------------------------------------
# Track 9: Game Over / Credits
# ------------------------------------------------------------------
def produce_track_09():
    print("--- 09_Credits ---")
    bpm = 50
    dur = 200.0
    key = D_DOR
    chords = [
        ChordLabel(root=2, quality=Quality.MINOR, start=0, duration=50),
        ChordLabel(root=0, quality=Quality.MAJOR, start=50, duration=50),
        ChordLabel(root=7, quality=Quality.MAJOR, start=100, duration=50),
        ChordLabel(root=2, quality=Quality.MINOR, start=150, duration=50),
    ]

    # Layered finale — all motifs together, evolving
    sokki_final = registry.render_for("sokki", "nostalgic", offset=10.0)
    sokki_final += registry.render("sokki", offset=60.0,
                                    augment_factor=1.5, transpose=3)
    sokki_final += registry.render("sokki", variant="sleepy", offset=120.0,
                                    transpose=7)
    sokki_final += registry.render_for("sokki", "tender", offset=160.0)

    # Void resolution — the mystery fades
    void_fade = registry.render("void", offset=40.0,
                                 augment_factor=2.0, transpose=12)

    # Full layering — all motifs
    layered = registry.layer(
        ["sokki", "void"], [100.0, 100.0],
        augment_factor=1.3
    )

    # Warm pad
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.06, key_range_low=48, key_range_high=72),
        voicing="spread", overlap=1.0
    ).render(chords, key, dur)

    # Drone
    drone = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=36, key_range_high=37),
        velocity=30
    ).render(chords, key, dur)

    # Harp — gentle ending
    arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.06, key_range_low=55, key_range_high=79),
        pattern="up", note_duration=2.0
    ).render(chords, key, dur)

    # Combine all melody layers
    all_melody = sokki_final + void_fade + layered

    _export(
        {"melody": all_melody, "pad": pad, "drone": drone, "arp": arp},
        OUT / "09_Credits.mid", bpm, key,
        {"melody": XYLOPHONE, "pad": PAD_WARM, "drone": CELLO,
         "arp": HARP},
        lufs=-18.0,
    )


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    produce_track_01()
    produce_track_02()
    produce_track_03()
    produce_track_04()
    produce_track_05()
    produce_track_06()
    produce_track_07()
    produce_track_08()
    produce_track_09()
    print(f"\nSokki album complete. Files in {OUT}/")


if __name__ == "__main__":
    main()
