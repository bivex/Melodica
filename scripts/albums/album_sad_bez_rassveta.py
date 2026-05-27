# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_sad_bez_rassveta.py — Garden Without Dawn.

Album: "Sad bez rassveta" (Сад без рассвета)
Character: A thin Edo-period man, introverted scholar-musician,
           hiding a storm beneath still water.

Tracks:
1. Чернила на снегу (Ink on Snow) — a memory being erased
2. Последний фонарь квартала (The Last Lantern) — anxious night Edo
3. Комната без имени (Nameless Room) — silence as pain
4. Письмо, которое не отправили (Letter Never Sent) — hidden feelings
5. Луна за рисовой бумагой (Moon Behind Rice Paper) — cold hypnosis
6. Пустой сад после дождя (Empty Garden After Rain) — beauty of dying
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.generators.drone import DroneGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.modifiers import (
    ModifierPipeline, ModifierContext,
    VelocityScalingModifier, HumanizeModifier,
)
from melodica.types import MusicTimeline


def generate_track(name, parts, tracks, out_dir, bpm, vel_scale=1.0):
    print(f"  > {name}")
    config = IdeaToolConfig(
        style="japanese",
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
    )
    notes_dict = IdeaTool(config).generate()

    if vel_scale != 1.0:
        total_bars = sum(p.bars for p in parts)
        timeline = notes_dict.get("_timeline", MusicTimeline(chords=[], keys=[]))
        mod_ctx = ModifierContext(
            duration_beats=total_bars * 4,
            chords=timeline.chords,
            timeline=timeline,
            scale=parts[0].scale,
        )
        for tname in notes_dict:
            if not tname.startswith("_") and isinstance(notes_dict[tname], list):
                p = ModifierPipeline(base_notes=notes_dict[tname])
                p.add_modifier(VelocityScalingModifier(scale=vel_scale))
                p.add_modifier(HumanizeModifier(timing_std=0.05, velocity_std=8))
                notes_dict[tname] = p.process(mod_ctx)

    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
    instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks}

    file_path = out_dir / f"{name}.mid"
    export_multitrack_midi(tracks_data, str(file_path), bpm=bpm, instruments=instruments_map)
    return file_path


def main():
    print("=" * 80)
    print("  С А Д   Б Е З   Р А С С В Е Т А")
    print("  Garden Without Dawn")
    print("=" * 80)

    out_dir = Path("output/album_sad_bez_rassveta")
    out_dir.mkdir(exist_ok=True, parents=True)

    in_sen = Scale(0, Mode.JAPANESE)
    kumoi  = Scale(7, Mode.KUMOI)
    minor_penta = Scale(9, Mode.MINOR_PENTATONIC)

    # =========================================================================
    # 1. Чернила на снегу — Ink on Snow
    # A memory dissolving. Solo shakuhachi breath over a frozen drone.
    # Almost nothing happens. The silence IS the music.
    # =========================================================================
    print("\n  [1/6] Чернила на снегу")

    t1_tracks = [
        TrackConfig("Snow_Drone", "drone", "dark_pad", density=0.3, octave_shift=-2,
                     params={"variant": "tonic"}),
        TrackConfig("Breath", "melody", "shakuhachi", density=0.2,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_shakuhachi_free")}),
    ]
    t1_parts = [
        IdeaPart(
            name="Fading", bars=16, scale=in_sen, tempo=42,
            track_phrase_schedules={
                "Snow_Drone": structure_to_schedule("A", 16),
                "Breath":     structure_to_schedule("R A R R R B R R", 2),
            }
        ),
    ]
    generate_track("1 Чернила на снегу", t1_parts, t1_tracks, out_dir, 42, vel_scale=0.55)

    # =========================================================================
    # 2. Последний фонарь квартала — The Last Lantern of the Quarter
    # Nighttime Edo. Distant footsteps, a shamisen fragment heard through
    # paper walls. Anxiety without source.
    # =========================================================================
    print("\n  [2/6] Последний фонарь квартала")

    t2_tracks = [
        TrackConfig("Night_Drone", "drone", "dark_pad", density=0.4, octave_shift=-1,
                     params={"variant": "dominant"}),
        TrackConfig("Distant_Shamisen", "melody", "shamisen", density=0.35,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_shamisen_syncopa_8th")}),
        TrackConfig("Footsteps", "melody", "drums", density=0.25,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_ma_pause_free")}),
    ]
    t2_parts = [
        IdeaPart(
            name="Alley", bars=16, scale=kumoi, tempo=58,
            track_phrase_schedules={
                "Night_Drone":       structure_to_schedule("A", 16),
                "Distant_Shamisen":  structure_to_schedule("R A R R B R R A", 2),
                "Footsteps":         structure_to_schedule("R R A R B R R R", 2),
            }
        ),
    ]
    generate_track("2 Последний фонарь квартала", t2_parts, t2_tracks, out_dir, 58, vel_scale=0.5)

    # =========================================================================
    # 3. Комната без имени — Nameless Room
    # Almost silent. Long pauses. The creak of wood. A single koto note
    # repeated like a thought you cannot stop thinking.
    # =========================================================================
    print("\n  [3/6] Комната без имени")

    t3_tracks = [
        TrackConfig("Room_Air", "nebula", "synth_fx", density=0.15,
                     params={"variant": "swell"}),
        TrackConfig("One_Note", "melody", "koto", density=0.1,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_ma_pause_free")}),
    ]
    t3_parts = [
        IdeaPart(
            name="Stillness", bars=20, scale=in_sen, tempo=36,
            track_phrase_schedules={
                "Room_Air": structure_to_schedule("R A R R R R B R R R", 2),
                "One_Note": structure_to_schedule("R R R A R R R R R B", 2),
            }
        ),
    ]
    generate_track("3 Комната без имени", t3_parts, t3_tracks, out_dir, 36, vel_scale=0.4)

    # =========================================================================
    # 4. Письмо, которое не отправили — Letter Never Sent
    # The most emotionally loaded track. Shakuhachi and koto in dialogue,
    # like words written and crossed out. Intimacy at a distance.
    # =========================================================================
    print("\n  [4/6] Письмо, которое не отправили")

    t4_tracks = [
        TrackConfig("Lantern_Drone", "drone", "dark_pad", density=0.4, octave_shift=-1,
                     params={"variant": "tonic"}),
        TrackConfig("Voice_Flute", "melody", "shakuhachi", density=0.35,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_enka_ballad_free")}),
        TrackConfig("Reply_Koto", "melody", "koto", density=0.3,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_gagaku_slow_free")}),
        TrackConfig("Ink_Strokes", "nebula", "synth_fx", density=0.1,
                     params={"variant": "swell"}),
    ]
    t4_parts = [
        IdeaPart(
            name="Unsent", bars=16, scale=kumoi, tempo=48,
            track_phrase_schedules={
                "Lantern_Drone": structure_to_schedule("A", 16),
                "Voice_Flute":  structure_to_schedule("R A R R B R A R", 2),
                "Reply_Koto":   structure_to_schedule("R R A R R R B R", 2),
                "Ink_Strokes":  structure_to_schedule("R R R A R R R B", 2),
            }
        ),
    ]
    generate_track("4 Письмо, которое не отправили", t4_parts, t4_tracks, out_dir, 48, vel_scale=0.5)

    # =========================================================================
    # 5. Луна за рисовой бумагой — Moon Behind Rice Paper
    # Cold, hypnotic. A single repeating motif on shamisen, blurred by
    # drone. Time stops. The moon doesn't move.
    # =========================================================================
    print("\n  [5/6] Луна за рисовой бумагой")

    t5_tracks = [
        TrackConfig("Moon_Drone", "drone", "dark_pad", density=0.5, octave_shift=-2,
                     params={"variant": "tonic"}),
        TrackConfig("Hypnotic_Shamisen", "melody", "shamisen", density=0.4,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_shamisen_jongara_16th")}),
        TrackConfig("Frozen_Strings", "melody", "strings", density=0.2,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_gagaku_slow_free")}),
    ]
    t5_parts = [
        IdeaPart(
            name="Still_Moon", bars=16, scale=minor_penta, tempo=45,
            track_phrase_schedules={
                "Moon_Drone":         structure_to_schedule("A", 16),
                "Hypnotic_Shamisen":  structure_to_schedule("R A R A R A R A", 2),
                "Frozen_Strings":     structure_to_schedule("R R A R R R B R", 2),
            }
        ),
    ]
    generate_track("5 Луна за рисовой бумагой", t5_parts, t5_tracks, out_dir, 45, vel_scale=0.45)

    # =========================================================================
    # 6. Пустой сад после дождя — Empty Garden After Rain
    # The final dissolving. Everything fades. A last shakuhachi phrase,
    # then only rain and drone, then nothing. Calm and almost dead.
    # =========================================================================
    print("\n  [6/6] Пустой сад после дождя")

    t6_tracks = [
        TrackConfig("Rain_Drone", "drone", "dark_pad", density=0.4, octave_shift=-2,
                     params={"variant": "dominant"}),
        TrackConfig("Last_Breath", "melody", "shakuhachi", density=0.2,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_noh_voice_free")}),
        TrackConfig("Wet_Stone", "nebula", "synth_fx", density=0.15,
                     params={"variant": "swell"}),
        TrackConfig("Final_Bell", "melody", "tubular_bells", density=0.08,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_ma_pause_free")}),
    ]
    t6_parts = [
        IdeaPart(
            name="Dissolving", bars=24, scale=in_sen, tempo=38,
            track_phrase_schedules={
                "Rain_Drone":  structure_to_schedule("A", 24),
                "Last_Breath": structure_to_schedule("R A R R R R R B R R R R R R R R", 1),
                "Wet_Stone":   structure_to_schedule("R R A R R R B R R R R R R R R R", 1),
                "Final_Bell":  structure_to_schedule("R R R R R A R R R R R R R B R R", 1),
            }
        ),
    ]
    generate_track("6 Пустой сад после дождя", t6_parts, t6_tracks, out_dir, 38, vel_scale=0.4)

    print()
    print("  Сад без рассвета. Всё красиво, но уже потеряно.")
    print(f"  6 tracks: {out_dir.absolute()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
