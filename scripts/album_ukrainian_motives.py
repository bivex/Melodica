# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_ukrainian_motives.py — "Криниця Душ: Ukrainian Motives Symphony"
A 38-minute, 7-track orchestral album with Ukrainian folk dramaturgy.

Dramaturgy arc (classical 4-act structure through Ukrainian cultural lens):

  Act I  — Земля (The Land):       Tracks 1-2  [tension 0.15 → 0.40]
    Exposition of the steppe, its people, and folk themes.

  Act II — Дух (The Spirit):       Tracks 3-4  [tension 0.35 → 0.70]
    Cossack dumy, historical memory, rising tension toward conflict.

  Act III— Вогонь (The Fire):      Tracks 5-6  [tension 0.75 → 1.00 → 0.30]
    Climactic battle and sacrifice. Full orchestral force.
    Tragedy burns down to embers.

  Act IV— Відродження (Rebirth):   Track 7     [tension 0.30 → 0.10]
    Resolution. Modal shift to Dorian brightness. The land endures.

Scale palette:
  D Aeolian, G Dorian, C Dorian — core Ukrainian folk tonalities
  D/A Harmonic Minor — dumy dramatic mode (augmented 2nd interval)
  A/E Phrygian — tension, conflict, martial
  Byzantine, Hungarian Minor — exotic folk colour

Instruments mapped via GM:
  Sopilka  → flute (73)     Bandura  → harp (46)
  Trembita → french horn    Bayan    → accordion (21)
  Cossack horn → brass      Violin, Cello, Contrabass, Choir
  Timpani, Woodwinds, Piano
"""

from pathlib import Path

from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

# Generators
from melodica.generators.orchestral_strings import (
    ViolinGenerator,
    ViolaGenerator,
    CelloGenerator,
    ContrabassGenerator,
)
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.orchestral_brass import (
    FrenchHornGenerator,
    TrumpetGenerator,
    TromboneGenerator,
)
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.orchestral_woodwinds import FluteGenerator
from melodica.generators.piano_run import PianoRunGenerator
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.keyboard_sustained import AccordionGenerator


# ---------------------------------------------------------------------------
# Act I: Земля (The Land)
# ---------------------------------------------------------------------------

def generate_track_01():
    """1. Пробудження Степу (Steppe Awakening) — 80 bars, ~4.5 min.
    Dawn over endless wheat fields. Solo sopilka calls across the mist.
    Drone on D. Slow, pastoral, melancholy beauty."""
    print("  -> 1. Пробудження Степу (Steppe Awakening)")

    parts = [
        IdeaPart(name="Туман (Mist)", bars=48, scale=Scale(root=2, mode=Mode.AEOLIAN), tempo=72),
        IdeaPart(name="Схід (Sunrise)", bars=32, scale=Scale(root=7, mode=Mode.DORIAN), tempo=80),
    ]

    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all",
        use_tension_curve=True, use_voice_leading=True, use_texture_control=True,
        use_mixing=True, use_mastering=True, target_lufs=-16.0,
        parts=parts,
        tracks=[
            # Sopilka — folk flute, the first voice of morning
            TrackConfig(name="Sopilka", generator=FluteGenerator(), instrument="flute",
                        arrangement="ABAB", density=0.5, octave_shift=1,
                        variations=["humanize"], rhythm_rests=0.7, mpe=True),
            # Bandura — harp-like zither, gentle arpeggios
            TrackConfig(name="Bandura", generator=HarpGenerator(), instrument="harp",
                        arrangement="AABB", density=0.6, rhythm_rests=0.8),
            # Cello — warm foundation, sings below the sopilka
            TrackConfig(name="Cello", generator=CelloGenerator(), instrument="cello",
                        arrangement="ABCD", density=0.5, octave_shift=-1,
                        variations=["humanize"], mpe=True),
            # Drone — tonic pedal, the earth itself
            TrackConfig(name="Steppe Drone", generator=DroneGenerator(variant="tonic"),
                        instrument="contrabass", arrangement="AABB", density=0.9,
                        octave_shift=-2),
            # Choir — distant, like wind across the plain
            TrackConfig(name="Wind Choir", generator=ChoirAahsGenerator(), instrument="choir",
                        arrangement="AABB", density=0.3, rhythm_rests=0.6, mpe=True),
            TrackConfig(name="Contrabass", generator=ContrabassGenerator(), instrument="contrabass",
                        arrangement="AABB", density=0.7, octave_shift=-1),
        ],
    )
    return IdeaTool(config).generate(), parts


def generate_track_02():
    """2. Душа Полів (Soul of the Fields) — 128 bars, ~5 min.
    Kolomyika rhythm. Folk dance in G Dorian. Joy with undercurrent of melancholy.
    Strings pizzicato, accordion, woodwinds interplay."""
    print("  -> 2. Душа Полів (Soul of the Fields)")

    parts = [
        IdeaPart(name="Коломийка (Kolomyika)", bars=48, scale=Scale(root=7, mode=Mode.DORIAN), tempo=108),
        IdeaPart(name="Пшениця (Wheat)", bars=48, scale=Scale(root=0, mode=Mode.DORIAN), tempo=100),
        IdeaPart(name="Танок (Dance)", bars=32, scale=Scale(root=7, mode=Mode.MIXOLYDIAN), tempo=118),
    ]

    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all",
        use_tension_curve=True, use_voice_leading=True, use_texture_control=True,
        use_mixing=True, use_mastering=True, target_lufs=-14.0,
        parts=parts,
        tracks=[
            # Violins — folk fiddle, the dance leader
            TrackConfig(name="Violins", generator=ViolinGenerator(), instrument="violin",
                        arrangement="ABAB", density=0.8, variations=["humanize"],
                        rhythm_swing=0.55, mpe=True),
            # Pizzicato — rhythmic pulse of the dance
            TrackConfig(name="Pizzicato", generator=StringsPizzicatoGenerator(), instrument="pizzicato",
                        arrangement="AABB", density=0.9, rhythm_dotted=True),
            # Bayan (accordion) — soul of Ukrainian folk
            TrackConfig(name="Bayan", generator=AccordionGenerator(), instrument="accordion",
                        arrangement="ABCD", density=0.6, octave_shift=0, mpe=True),
            # Sopilka returns — woodwind counter-theme
            TrackConfig(name="Flute Echo", generator=WoodwindsEnsembleGenerator(), instrument="flute",
                        arrangement="AABB", density=0.5, octave_shift=1, rhythm_rests=0.5),
            # Cello — bass line, kolomyika bounce
            TrackConfig(name="Cello Bass", generator=CelloGenerator(), instrument="cello",
                        arrangement="ABAB", density=0.7, octave_shift=-1),
            # Harp glissandi
            TrackConfig(name="Harp", generator=HarpGenerator(), instrument="harp",
                        arrangement="ABAC", density=0.4, rhythm_rests=0.7),
            TrackConfig(name="Contrabass", generator=ContrabassGenerator(), instrument="contrabass",
                        arrangement="AABB", density=0.8, octave_shift=-1),
        ],
    )
    return IdeaTool(config).generate(), parts


# ---------------------------------------------------------------------------
# Act II: Дух (The Spirit)
# ---------------------------------------------------------------------------

def generate_track_03():
    """3. Дума про Козаків (Cossack Dumy) — 128 bars, ~6.5 min.
    Deep historical melancholy. Dumy tradition — free recitative over drone.
    Solo cello and violin trade lament themes. The weight of centuries."""
    print("  -> 3. Дума про Козаків (Cossack Dumy)")

    parts = [
        IdeaPart(name="Старець (The Elder)", bars=48, scale=Scale(root=2, mode=Mode.HARMONIC_MINOR), tempo=76),
        IdeaPart(name="Слава (Glory)", bars=48, scale=Scale(root=9, mode=Mode.AEOLIAN), tempo=84),
        IdeaPart(name="Відлуння (Echoes)", bars=32, scale=Scale(root=2, mode=Mode.DORIAN), tempo=68),
    ]

    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all",
        use_tension_curve=True, use_voice_leading=True, use_texture_control=True,
        use_mixing=True, use_mastering=True, target_lufs=-15.0,
        parts=parts,
        tracks=[
            # Solo Cello — the kobzar's voice, heart of the dumy
            TrackConfig(name="Kobzar Cello", generator=CelloGenerator(), instrument="cello",
                        arrangement="ABCD", density=0.5, variations=["humanize"],
                        rhythm_swing=0.55, mpe=True),
            # Solo Violin — responding voice, like the bandura's song
            TrackConfig(name="Bandura Violin", generator=ViolinGenerator(), instrument="violin",
                        arrangement="ABCD", density=0.4, octave_shift=1,
                        depends_on="Kobzar Cello", variations=["humanize"], mpe=True),
            # Choir — male voice choir, Orthodox chant tradition
            TrackConfig(name="Monastery Choir", generator=ChoirAahsGenerator(), instrument="choir",
                        arrangement="AABB", density=0.5, rhythm_rests=0.6, mpe=True),
            # French Horn — trembita, the mountain horn
            TrackConfig(name="Trembita", generator=FrenchHornGenerator(), instrument="french_horn",
                        arrangement="ABCD", density=0.4, octave_shift=-1, rhythm_rests=0.8, mpe=True),
            # Drone — sustained D, the eternal steppe
            TrackConfig(name="Drone", generator=DroneGenerator(variant="tonic"),
                        instrument="contrabass", arrangement="AABB", density=0.9, octave_shift=-2),
            # Harp — sparse, like tears
            TrackConfig(name="Harp Tears", generator=HarpGenerator(), instrument="harp",
                        arrangement="ABAC", density=0.3, rhythm_rests=0.7),
            TrackConfig(name="Contrabass", generator=ContrabassGenerator(), instrument="contrabass",
                        arrangement="AABB", density=0.6, octave_shift=-1),
        ],
    )
    return IdeaTool(config).generate(), parts


def generate_track_04():
    """4. Гайдамацький Степ (Haydamaky Steppe) — 128 bars, ~5 min.
    Military energy. Cossack uprising. Ostinato driving patterns.
    Phrygian mode = tension, unrest, martial character."""
    print("  -> 4. Гайдамацький Стep (Haydamaky Steppe)")

    parts = [
        IdeaPart(name="Марш (March)", bars=48, scale=Scale(root=9, mode=Mode.PHRYGIAN), tempo=112),
        IdeaPart(name="Сутичка (Skirmish)", bars=48, scale=Scale(root=4, mode=Mode.HARMONIC_MINOR), tempo=124),
        IdeaPart(name="Перемога (Victory)", bars=32, scale=Scale(root=9, mode=Mode.DORIAN), tempo=120),
    ]

    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all",
        use_tension_curve=True, use_voice_leading=True, use_texture_control=True,
        use_mixing=True, use_mastering=True, target_lufs=-13.0,
        parts=parts,
        tracks=[
            # Ostinato — Cossack march pattern, relentless
            TrackConfig(name="March Ostinato", generator=OstinatoGenerator(pattern="driving"),
                        instrument="cello", arrangement="ABAB", density=1.0,
                        octave_shift=-1, rhythm_swing=0.55),
            # Gallop rhythm — horse hooves
            TrackConfig(name="Gallop", generator=OstinatoGenerator(pattern="gallop"),
                        instrument="viola", arrangement="ABAB", density=1.0),
            # Brass — Cossack war horns
            TrackConfig(name="War Horns", generator=BrassSectionGenerator(), instrument="brass",
                        arrangement="AABC", density=0.8),
            # Timpani — martial heartbeat
            TrackConfig(name="Timpani", generator=TimpaniGenerator(), instrument="timpani",
                        arrangement="ABCD", density=0.9, rhythm_rests=0.9),
            # Trumpet lead — battle cry
            TrackConfig(name="Battle Trumpet", generator=TrumpetGenerator(), instrument="trumpet",
                        arrangement="AABB", density=0.7, octave_shift=1),
            # Choir — Cossack war song
            TrackConfig(name="Cossack Choir", generator=ChoirAahsGenerator(), instrument="choir",
                        arrangement="ABCD", density=0.7, mpe=True),
            # Tremolo strings — tension bed
            TrackConfig(name="Tension Strings", generator=TremoloStringsGenerator(), instrument="strings",
                        arrangement="AABB", density=0.9, octave_shift=1),
            TrackConfig(name="Contrabass", generator=ContrabassGenerator(), instrument="contrabass",
                        arrangement="AABB", density=0.9, octave_shift=-1),
        ],
    )
    return IdeaTool(config).generate(), parts


# ---------------------------------------------------------------------------
# Act III: Вогонь (The Fire)
# ---------------------------------------------------------------------------

def generate_track_05():
    """5. Полум'я Свободи (Flame of Freedom) — 192 bars, ~7 min.
    CLIMAX. Full orchestral force. The defining battle.
    4-part structure: threat → battle → sacrifice → pyrrhic dawn.
    Highest density, maximum tension, massive choir."""
    print("  -> 5. Полум'я Свободи (Flame of Freedom)")

    parts = [
        IdeaPart(name="Загроза (Threat)", bars=48, scale=Scale(root=4, mode=Mode.PHRYGIAN), tempo=116),
        IdeaPart(name="Бій (Battle)", bars=64, scale=Scale(root=9, mode=Mode.HARMONIC_MINOR), tempo=138),
        IdeaPart(name="Жертва (Sacrifice)", bars=48, scale=Scale(root=2, mode=Mode.AEOLIAN), tempo=100),
        IdeaPart(name="Світанок (Dawn)", bars=32, scale=Scale(root=2, mode=Mode.DORIAN), tempo=88),
    ]

    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all",
        use_tension_curve=True, use_voice_leading=True, use_texture_control=True,
        use_mixing=True, use_mastering=True, target_lufs=-11.5,
        parts=parts,
        tracks=[
            # Piano — runs through the chaos
            TrackConfig(name="Piano Fire", generator=PianoRunGenerator(), instrument="piano",
                        arrangement="ABCD", density=0.8, octave_shift=1,
                        variations=["humanize"], mpe=True),
            # Violins — searing melody
            TrackConfig(name="Violins Blaze", generator=ViolinGenerator(), instrument="violin",
                        arrangement="AABC", density=0.9, octave_shift=1,
                        variations=["octave_double"], mpe=True),
            # Strings legato — wall of sound
            TrackConfig(name="Strings Wall", generator=StringsLegatoGenerator(), instrument="strings",
                        arrangement="AABC", density=1.0, octave_shift=1, mpe=True),
            # Viola countermelody
            TrackConfig(name="Viola Counter", generator=CountermelodyGenerator(motion_preference="mixed"),
                        instrument="viola", arrangement="AABC", density=0.7,
                        depends_on="Violins Blaze"),
            # Brass section — war horns
            TrackConfig(name="Brass Fury", generator=BrassSectionGenerator(), instrument="brass",
                        arrangement="AABB", density=1.0),
            # French Horns — heroic
            TrackConfig(name="Hero Horns", generator=FrenchHornGenerator(), instrument="french_horn",
                        arrangement="AABB", density=0.9),
            # Trombones — weight and gravity
            TrackConfig(name="Trombones", generator=TromboneGenerator(), instrument="trombone",
                        arrangement="AABB", density=0.9, octave_shift=-1),
            # Tremolo — maximum tension
            TrackConfig(name="Tremolo Peak", generator=TremoloStringsGenerator(), instrument="strings",
                        arrangement="ABCD", density=1.0, octave_shift=2),
            # Timpani — thunder
            TrackConfig(name="Thunder Timpani", generator=TimpaniGenerator(), instrument="timpani",
                        arrangement="ABCD", density=1.0),
            # Full choir — massed voices
            TrackConfig(name="Freedom Choir", generator=ChoirAahsGenerator(), instrument="choir",
                        arrangement="ABCD", density=1.0, mpe=True),
            # Contrabass — foundation
            TrackConfig(name="Contrabass", generator=ContrabassGenerator(), instrument="contrabass",
                        arrangement="AABB", density=1.0, octave_shift=-2),
        ],
    )
    return IdeaTool(config).generate(), parts


def generate_track_06():
    """6. Колискова Попелища (Lullaby of the Ashes) — 128 bars, ~5.5 min.
    Post-devastation. Intimate grief. Solo bandura over ruins.
    The lullaby a mother sings to a burned village. Extreme tenderness."""
    print("  -> 6. Колискова Попелища (Lullaby of the Ashes)")

    parts = [
        IdeaPart(name="Руїни (Ruins)", bars=48, scale=Scale(root=6, mode=Mode.AEOLIAN), tempo=72),
        IdeaPart(name="Колискова (Lullaby)", bars=48, scale=Scale(root=11, mode=Mode.AEOLIAN), tempo=68),
        IdeaPart(name="Попіл до Зірок (Ashes to Stars)", bars=32, scale=Scale(root=6, mode=Mode.PHRYGIAN), tempo=64),
    ]

    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all",
        use_tension_curve=True, use_voice_leading=True, use_texture_control=True,
        use_mixing=True, use_mastering=True, target_lufs=-16.0,
        parts=parts,
        tracks=[
            # Solo Bandura — the lone survivor's song
            TrackConfig(name="Bandura Solo", generator=HarpGenerator(), instrument="harp",
                        arrangement="ABCD", density=0.4, variations=["humanize"], mpe=True),
            # Cello — mournful, intimate
            TrackConfig(name="Cello Grief", generator=CelloGenerator(), instrument="cello",
                        arrangement="ABAC", density=0.4, variations=["humanize"], mpe=True),
            # Choir whispers — ghosts of the village
            TrackConfig(name="Ghost Choir", generator=ChoirAahsGenerator(), instrument="choir",
                        arrangement="ABCD", density=0.25, rhythm_rests=0.7, mpe=True),
            # Flute — like a child's voice
            TrackConfig(name="Child Flute", generator=FluteGenerator(), instrument="flute",
                        arrangement="AABB", density=0.3, octave_shift=2, rhythm_rests=0.6, mpe=True),
            # Drone — the silence after fire
            TrackConfig(name="Ash Drone", generator=DroneGenerator(variant="fifth"),
                        instrument="contrabass", arrangement="AABB", density=0.7, octave_shift=-2),
            # Contrabass — barely there
            TrackConfig(name="Contrabass", generator=ContrabassGenerator(), instrument="contrabass",
                        arrangement="AABB", density=0.5, octave_shift=-1),
        ],
    )
    return IdeaTool(config).generate(), parts


# ---------------------------------------------------------------------------
# Act IV: Відродження (Rebirth)
# ---------------------------------------------------------------------------

def generate_track_07():
    """7. Нова Весна (New Spring) — 144 bars, ~6 min.
    Resolution. The land endures. Bright Dorian modality.
    Cyclical return to D (opening key) but now in Dorian (raised 6th = hope).
    All instruments return. Choir sings not of grief but of spring."""
    print("  -> 7. Нова Весна (New Spring)")

    parts = [
        IdeaPart(name="Перший Тан (First Thaw)", bars=48, scale=Scale(root=2, mode=Mode.DORIAN), tempo=84),
        IdeaPart(name="Квіти (Wildflowers)", bars=48, scale=Scale(root=7, mode=Mode.MAJOR), tempo=92),
        IdeaPart(name="Земля Пам'ятає (The Land Remembers)", bars=48, scale=Scale(root=2, mode=Mode.DORIAN), tempo=80),
    ]

    config = IdeaToolConfig(
        style="cinematic", workflow="generate_all",
        use_tension_curve=True, use_voice_leading=True, use_texture_control=True,
        use_mixing=True, use_mastering=True, target_lufs=-14.0,
        parts=parts,
        tracks=[
            # Sopilka returns — the morning call from Track 1
            TrackConfig(name="Sopilka Rebirth", generator=FluteGenerator(), instrument="flute",
                        arrangement="ABAB", density=0.6, octave_shift=1,
                        variations=["humanize"], mpe=True),
            # Bandura — same instrument, now bright
            TrackConfig(name="Bandura Spring", generator=HarpGenerator(), instrument="harp",
                        arrangement="AABB", density=0.5),
            # Violins — singing, not weeping
            TrackConfig(name="Violins Hope", generator=ViolinGenerator(), instrument="violin",
                        arrangement="ABCD", density=0.7, octave_shift=1, mpe=True),
            # Cello — warm, grounding
            TrackConfig(name="Cello Root", generator=CelloGenerator(), instrument="cello",
                        arrangement="ABAC", density=0.6, mpe=True),
            # Accordion — folk joy returns
            TrackConfig(name="Bayan Joy", generator=AccordionGenerator(), instrument="accordion",
                        arrangement="AABB", density=0.5, mpe=True),
            # Choir — from grief to hope
            TrackConfig(name="Spring Choir", generator=ChoirAahsGenerator(), instrument="choir",
                        arrangement="ABCD", density=0.6, mpe=True),
            # French Horn — nature's voice
            TrackConfig(name="Horn Dawn", generator=FrenchHornGenerator(), instrument="french_horn",
                        arrangement="ABCD", density=0.5, rhythm_rests=0.7, mpe=True),
            # Contrabass — the earth, constant
            TrackConfig(name="Contrabass", generator=ContrabassGenerator(), instrument="contrabass",
                        arrangement="AABB", density=0.7, octave_shift=-1),
        ],
    )
    return IdeaTool(config).generate(), parts


# ---------------------------------------------------------------------------
# Main Builder
# ---------------------------------------------------------------------------

def main():
    album_dir = Path("output/album_ukrainian_motives")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        К Р И Н И Ц Я   Д У Ш")
    print("        Ukrainian Motives — A Dramaturgy Symphony")
    print("=" * 80)
    print()
    print("  Act I   — Земля (The Land):       Tracks 1-2")
    print("  Act II  — Дух (The Spirit):        Tracks 3-4")
    print("  Act III — Вогонь (The Fire):       Tracks 5-6")
    print("  Act IV  — Відродження (Rebirth):   Track 7")
    print("=" * 80)

    tracks = [
        (generate_track_01, "01_Steppe_Awakening.mid"),
        (generate_track_02, "02_Soul_of_the_Fields.mid"),
        (generate_track_03, "03_Cossack_Dumy.mid"),
        (generate_track_04, "04_Haydamaky_Steppe.mid"),
        (generate_track_05, "05_Flame_of_Freedom.mid"),
        (generate_track_06, "06_Lullaby_of_the_Ashes.mid"),
        (generate_track_07, "07_New_Spring.mid"),
    ]

    total_notes = 0
    time_signature = (4, 4)

    with EngineTracer(show_private=False, show_duration=True, max_depth=2, use_colors=True):
        for producer, filename in tracks:
            print("-" * 80)
            notes_dict, parts_config = producer()

            # Construct Tempo Map
            tempo_map = []
            current_beat = 0.0
            for p in parts_config:
                tempo_map.append((current_beat, p.tempo))
                current_beat += p.bars * time_signature[0]

            # Filter non-track keys
            tracks_data = {k: v for k, v in notes_dict.items()
                           if not k.startswith("_") and isinstance(v, list)}

            # Extract automation
            cc_events = notes_dict.get("_cc_events", {})
            mpe_tracks = notes_dict.get("_mpe_tracks", set())

            export_multitrack_midi(
                tracks_data,
                str(album_dir / filename),
                bpm=parts_config[0].tempo,
                tempo_events=tempo_map,
                cc_events=cc_events,
                mpe_tracks=mpe_tracks,
            )

            note_count = sum(len(n) for n in tracks_data.values())
            total_notes += note_count
            mpe_count = sum(1 for k in mpe_tracks if k in tracks_data)
            print(f"    Exported {filename}")
            print(f"      - Notes: {note_count}")
            print(f"      - MPE voices: {mpe_count}")
            print(f"      - Tempo: {', '.join(f'{bpm}bpm@{beat}b' for beat, bpm in tempo_map)}")

    print()
    print("=" * 80)
    print(f"  COMPLETE: Криниця Душ — {total_notes} total notes across 7 tracks")
    print(f"  Dramaturgy: Land → Spirit → Fire → Rebirth")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
