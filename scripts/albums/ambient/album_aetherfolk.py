# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/albums/ambient/album_aetherfolk.py — "ÆTHERFOLK: Songs of the Hollow Stars"

A continuous mystical / magical-toned album. Five movements trace a pilgrimage
across liminal spaces — a hollow star, a glass forest, a choir of pale moons, a
crystalline waltz, and a final dissolve into starlight.

Palette: glass harp, nebula pad, music box, choir aahs, tubular bells, harp and
sustained drones — over modal / whole-tone harmony in 3/4 and 6/8.

Built on AlbumNarrative, so it honours the mandatory rhythm / genre /
time_signature contract (rhythm imposed per-track, key + chords threaded into
the harmonic stages, a shared meter).
"""

from melodica.types import NoteInfo, Scale, Mode
from melodica.idea_tool import TrackConfig, structure_to_schedule
from melodica.composer.album_pipeline import AlbumNarrative, Mood

# Generators — the magical palette
from melodica.generators import GeneratorParams
from melodica.generators.cinematic_ethereal import GlassHarpGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.chromatic_percussion import MusicBoxGenerator, CelestaGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.bass import BassGenerator

# GM Programs
PAD_NEW_AGE = 88
PAD_WARM = 89
POLYSYNTH = 90
SYNTH_VOICE = 91             # "voice oohs / aahs" — used for the choir pad bed
HARP = 46
GLOCKENSPIEL = 9
CELESTA = 8
MUSIC_BOX = 10              # GM "Glockenspiel" alt / music box shimmer (percussive)
TUBULAR_BELLS = 14
GLASS_HARP = 98             # GM "Applause"/pad-ish shimmer; we use it as a bright FX pad
SYNTH_PAD_BOWED = 92
BOWED_SYNTH = 92
SYNTH_BASS = 38          # warm sub foundation for the pedal bass track


def _schedule(letters: str, bars: int = 4):
    """Tiny helper so the schedules read like an arrangement lead-sheet."""
    return structure_to_schedule(letters, bars)


def produce_aetherfolk():
    print("=" * 84)
    print("           Æ T H E R F O L K   —   Songs of the Hollow Stars")
    print("           A continuous album of magic, glass and starlight")
    print("=" * 84)

    # ------------------------------------------------------------------
    # Motif Memory Engine — the "spell" that recurs, transformed, across
    # the whole journey. A rising, open whole-tone-flavoured figure.
    # ------------------------------------------------------------------
    seed_motif = [
        NoteInfo(pitch=72, start=0.0, duration=2.0, velocity=78),   # C5
        NoteInfo(pitch=76, start=2.0, duration=1.0, velocity=80),   # E5
        NoteInfo(pitch=79, start=3.0, duration=1.0, velocity=84),   # G5
        NoteInfo(pitch=83, start=4.0, duration=4.0, velocity=90),   # B5 — the wish
        NoteInfo(pitch=72, start=8.0, duration=4.0, velocity=72),   # return
    ]

    # ------------------------------------------------------------------
    # Harmonic Journey — modal/whole-tone path through liminal keys.
    # ------------------------------------------------------------------
    harmonic_journey = [
        Scale(root=11, mode=Mode.LYDIAN),      # I  — B Lydian (bright, floating)
        Scale(root=1,  mode=Mode.PHRYGIAN),    # II — C# Phrygian (shadowed, exotic)
        Scale(root=9,  mode=Mode.AEOLIAN),     # III — A Aeolian (pale moon choir)
        Scale(root=7,  mode=Mode.LYDIAN),      # IV — G Lydian (crystalline waltz)
        Scale(root=11, mode=Mode.LYDIAN),      # V  — B Lydian (return / dissolve)
    ]

    tempos = [54.0, 60.0, 50.0, 66.0, 48.0]

    # ------------------------------------------------------------------
    # Per-movement track configs.
    # ------------------------------------------------------------------
    track_configs = [
        # ── I. The Hollow Star (B Lydian) — gentle emergence ───────────
        [
            TrackConfig(
                name="pedal_bass",
                generator=BassGenerator(
                    params=GeneratorParams(key_range_low=28, key_range_high=43,
                                           density=0.6, velocity_range=(45, 65))
                ),
                instrument="bass",
                density=0.6,
                octave_shift=0,
                phrase_schedule=_schedule("A A B A B C R", 4),
            ),
            TrackConfig(
                name="nebula_wash",
                generator=NebulaGenerator(variant="cloud", density_notes=3,
                                          pitch_spread=5, note_duration=5.0,
                                          overlap=0.6),
                instrument="pad",
                density=0.5,
                phrase_schedule=_schedule("A B A B A C R", 4),
            ),
            TrackConfig(
                name="glass_harp",
                generator=GlassHarpGenerator(friction_noise=0.35, note_density=0.7),
                instrument="lead",
                density=0.5,
                octave_shift=1,
                phrase_schedule=_schedule("R A R B A C R", 4),
            ),
            TrackConfig(
                name="tonic_drone_pad",
                generator=DroneGenerator(variant="tonic", fade_in=8.0, fade_out=8.0),
                instrument="pad",
                density=0.9,
                octave_shift=-1,
                phrase_schedule=_schedule("A A B A B C R", 4),
            ),
        ],
        # ── II. Glass Forest (C# Phrygian) — shadowed sparkle ──────────
        [
            TrackConfig(
                name="pedal_bass",
                generator=BassGenerator(
                    params=GeneratorParams(key_range_low=28, key_range_high=43,
                                           density=0.6, velocity_range=(45, 65))
                ),
                instrument="bass",
                density=0.6,
                octave_shift=0,
                phrase_schedule=_schedule("A B C A B R R", 4),
            ),
            TrackConfig(
                name="music_box_mallet",
                generator=MusicBoxGenerator(pattern="clockwork_ostinato", note_density=0.8),
                instrument="glockenspiel",
                density=0.55,
                octave_shift=1,
                phrase_schedule=_schedule("A B A C A R R", 4),
            ),
            TrackConfig(
                name="celesta_haze_pad",
                generator=CelestaGenerator(note_density=0.5),
                instrument="celesta",
                density=0.4,
                phrase_schedule=_schedule("R A B A C R R", 4),
            ),
            TrackConfig(
                name="minor_pad",
                generator=DarkPadGenerator(mode="minor_pad", register="low",
                                           velocity_level=0.30, chord_dur=6.0),
                generator_type="pad",
                instrument="synth_pad",
                density=0.45,
                phrase_schedule=_schedule("A B B C A R R", 4),
            ),
            TrackConfig(
                name="harp_gliss",
                generator=HarpGenerator(pattern="cascade"),
                instrument="harp",
                density=0.35,
                phrase_schedule=_schedule("R R A R B C R", 4),
            ),
        ],
        # ── III. Choir of the Pale Moons (A Aeolian) — sacred stillness ─
        [
            TrackConfig(
                name="pedal_bass",
                generator=BassGenerator(
                    params=GeneratorParams(key_range_low=28, key_range_high=43,
                                           density=0.5, velocity_range=(40, 60))
                ),
                instrument="bass",
                density=0.5,
                octave_shift=0,
                phrase_schedule=_schedule("A A A A B C R", 4),
            ),
            TrackConfig(
                name="choir_aahs",
                generator=ChoirAahsGenerator(voice_count=5, dynamics="mp",
                                             vibrato=0.4, syllable="aah"),
                instrument="choir",
                density=0.5,
                phrase_schedule=_schedule("A A A A B C R", 4),
            ),
            TrackConfig(
                name="pad_bed",
                generator=DarkPadGenerator(mode="minor_pad", register="mid",
                                           velocity_level=0.32, chord_dur=8.0),
                generator_type="pad",
                instrument="synth_pad",
                density=0.4,
                phrase_schedule=_schedule("A A B A B C R", 4),
            ),
            TrackConfig(
                name="sacred_drone_pad",
                generator=DroneGenerator(variant="power", fade_in=6.0, fade_out=6.0),
                instrument="pad",
                density=0.85,
                octave_shift=-1,
                phrase_schedule=_schedule("A A A A A C R", 4),
            ),
            TrackConfig(
                name="bell_toll",
                generator=TubularBellsGenerator(stroke_pattern="single", dampen=True),
                instrument="tubular_bells",
                density=0.25,
                octave_shift=0,
                phrase_schedule=_schedule("R R R A R C R", 4),
            ),
        ],
        # ── IV. The Crystalline Waltz (G Lydian) — dancing light ───────
        [
            TrackConfig(
                name="pedal_bass",
                generator=BassGenerator(
                    params=GeneratorParams(key_range_low=28, key_range_high=43,
                                           density=0.65, velocity_range=(45, 65))
                ),
                instrument="bass",
                density=0.65,
                octave_shift=0,
                phrase_schedule=_schedule("A B A C A B R", 4),
            ),
            TrackConfig(
                name="glass_lead",
                generator=GlassHarpGenerator(
                    params=GeneratorParams(key_range_low=72, key_range_high=84,
                                           density=0.4),
                    friction_noise=0.25, note_density=0.4,
                ),
                instrument="lead",
                density=0.5,
                octave_shift=0,
                phrase_schedule=_schedule("A B A C A B R", 4),
            ),
            TrackConfig(
                name="celesta_run_mallet",
                generator=CelestaGenerator(note_density=0.8),
                instrument="celesta",
                density=0.55,
                octave_shift=1,
                phrase_schedule=_schedule("A B C A B A R", 4),
            ),
            TrackConfig(
                name="lydian_cloud_pad",
                generator=NebulaGenerator(variant="cloud", density_notes=4,
                                          pitch_spread=12, note_duration=4.0,
                                          overlap=0.4),
                instrument="synth_pad",
                density=0.45,
                phrase_schedule=_schedule("A A B A C B R", 4),
            ),
            TrackConfig(
                name="harp_arpeggio",
                generator=HarpGenerator(pattern="arpeggio"),
                instrument="harp",
                density=0.5,
                phrase_schedule=_schedule("A B A B C A R", 4),
            ),
        ],
        # ── V. Dissolve into Starlight (B Lydian) — fading return ──────
        [
            TrackConfig(
                name="pedal_bass",
                generator=BassGenerator(
                    params=GeneratorParams(key_range_low=28, key_range_high=43,
                                           density=0.45, velocity_range=(35, 55))
                ),
                instrument="bass",
                density=0.45,
                octave_shift=0,
                phrase_schedule=_schedule("A B C A R R R", 4),
            ),
            TrackConfig(
                name="nebula_drift_wash",
                generator=NebulaGenerator(variant="cloud", density_notes=3,
                                          pitch_spread=7, note_duration=7.0,
                                          overlap=0.7),
                instrument="pad",
                density=0.4,
                phrase_schedule=_schedule("A B C R R R R", 4),
            ),
            TrackConfig(
                name="glass_harp",
                generator=GlassHarpGenerator(friction_noise=0.4, note_density=0.5),
                instrument="lead",
                density=0.4,
                octave_shift=1,
                phrase_schedule=_schedule("R B C R R R R", 4),
            ),
            TrackConfig(
                name="choir_aahs",
                generator=ChoirAahsGenerator(voice_count=4, dynamics="p",
                                             vibrato=0.45, syllable="aah"),
                instrument="choir",
                density=0.4,
                phrase_schedule=_schedule("A R C R R R R", 4),
            ),
            TrackConfig(
                name="tonic_drone_pad",
                generator=DroneGenerator(variant="tonic", fade_in=4.0, fade_out=16.0),
                instrument="pad",
                density=0.8,
                octave_shift=-1,
                phrase_schedule=_schedule("A B C R R R R", 4),
            ),
        ],
    ]

    # Motif transformations across the pilgrimage.
    transformations = ["original", "stretched", "inversion", "fragmented", "retrograde"]

    # Dramaturgical arcs — each movement has a DISTINCT shape, so the album
    # does not feel like the same wave replayed in five keys. Energy/density
    # targets come from SECTION_PROFILES (Emergence≈0.4, Expansion≈0.65,
    # Variation≈0.85, Tension≈0.85, Release≈1.15, Breakdown≈0.4, Theme≈0.7,
    # Fade≈0.3, Dissolve≈0.35).
    sections_list = [
        # I. The Hollow Star — long, slow bloom with no hard climax (meditative shimmer).
        [(0.0, "Emergence"), (24.0, "Expansion"), (60.0, "Theme"),
         (84.0, "Expansion"), (108.0, "Fade")],
        # II. Glass Forest — two nervous swells (flicker, recede, flare, crumble).
        [(0.0, "Emergence"), (18.0, "Variation"), (42.0, "Breakdown"),
         (60.0, "Tension"), (90.0, "Dissolve")],
        # III. Choir of the Pale Moons — flat sustained hymn, climax at the very end.
        [(0.0, "Theme"), (36.0, "Theme"), (72.0, "Release"), (96.0, "Fade")],
        # IV. The Crystalline Waltz — early peak then a long mirage-like dissolve.
        [(0.0, "Expansion"), (24.0, "Release"), (48.0, "Breakdown"),
         (66.0, "Variation"), (90.0, "Fade")],
        # V. Dissolve into Starlight — fading from the start, the shortest movement.
        [(0.0, "Emergence"), (18.0, "Fade"), (42.0, "Dissolve")],
    ]

    instruments_maps = [
        # I. The Hollow Star
        {"pedal_bass": SYNTH_BASS, "nebula_wash": PAD_NEW_AGE,
         "glass_harp": GLASS_HARP, "tonic_drone_pad": PAD_WARM},
        # II. Glass Forest
        {"pedal_bass": SYNTH_BASS, "music_box_mallet": GLOCKENSPIEL, "celesta_haze_pad": CELESTA,
         "minor_pad": POLYSYNTH, "harp_gliss": HARP},
        # III. Choir of the Pale Moons
        {"pedal_bass": SYNTH_BASS, "choir_aahs": SYNTH_VOICE, "pad_bed": POLYSYNTH,
         "sacred_drone_pad": PAD_WARM, "bell_toll": TUBULAR_BELLS},
        # IV. The Crystalline Waltz
        {"pedal_bass": SYNTH_BASS, "glass_lead": GLASS_HARP, "celesta_run_mallet": CELESTA,
         "lydian_cloud_pad": POLYSYNTH, "harp_arpeggio": HARP},
        # V. Dissolve into Starlight
        {"pedal_bass": SYNTH_BASS, "nebula_drift_wash": PAD_NEW_AGE, "glass_harp": GLASS_HARP,
         "choir_aahs": SYNTH_VOICE, "tonic_drone_pad": PAD_WARM},
    ]

    moods = [Mood.AMBIENT, Mood.CINEMATIC, Mood.INTIMATE, Mood.CINEMATIC, Mood.AMBIENT]
    names = [
        "The Hollow Star",
        "Glass Forest",
        "Choir of the Pale Moons",
        "The Crystalline Waltz",
        "Dissolve into Starlight",
    ]

    narrative = AlbumNarrative(
        output_dir="output/album_aetherfolk",
        seed_motif=seed_motif,
        harmonic_journey=harmonic_journey,
        tempos=tempos,
        track_configs=track_configs,
        transformations=transformations,
        sections_list=sections_list,
        instruments_maps=instruments_maps,
        moods=moods,
        names=names,
        # --- mandatory production parameters ---
        rhythm="cls_elegant_waltz_3_4",   # graceful 3/4 pulse across the album
        time_signature=(3, 4),
        genre="lofi",                      # centred, non-aggressive pan profile
        strict_validation=True,
    )

    narrative.generate()
    print()
    print("=" * 84)
    print("  ÆTHERFOLK — the pilgrimage is complete. Find it in output/album_aetherfolk")
    print("=" * 84)


if __name__ == "__main__":
    produce_aetherfolk()
