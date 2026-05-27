# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_meiji_kaika.py — Meiji Ishin: Civilization and Enlightenment.

Album: "Meiji Kaika" (明治開化 — Dawn of Light)
Theme: Japan's Meiji Restoration (1868-1912) — the violent collision
       between tradition and modernity. Steam trains pierce through
       ancient forests, samurai armor hangs on walls while soldiers
       march in Western uniforms, gas lamps replace paper lanterns,
       and a nation is torn between who it was and who it must become.

Tracks:
1. Падение сёгуната (Fall of the Shogunate) — thunderous drums of revolution
2. Первые рельсы (First Rails) — steam engine rhythm cutting through old Japan
3. Газовые фонари Гиндзы (Gas Lamps of Ginza) — Westernization of Tokyo nights
4. Последний самурай (The Last Samurai) — fading honor, piano + shamisen
5. Железный тигр (Iron Tiger) — battleship era, military-industrial power
6. Рассвет Мэйдзи (Meiji Dawn) — bittersweet hope, old and new united
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.generators.melody import MelodyGenerator
from melodica.generators.chord_gen import ChordGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.modifiers import (
    ModifierPipeline, ModifierContext,
    DropSilenceModifier, DrumFillModifier,
    VelocityScalingModifier,
)
from melodica.types import MusicTimeline


def generate_track(name, parts, tracks, out_dir, bpm, glue=None):
    print(f"  > {name}")
    config = IdeaToolConfig(
        style="japanese",
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
    )
    notes_dict = IdeaTool(config).generate()

    if glue:
        total_bars = sum(p.bars for p in parts)
        timeline = notes_dict.get("_timeline", MusicTimeline(chords=[], keys=[]))
        mod_ctx = ModifierContext(
            duration_beats=total_bars * 4,
            chords=timeline.chords,
            timeline=timeline,
            scale=parts[0].scale,
        )
        for track_name, modifiers in glue.items():
            if track_name in notes_dict:
                p = ModifierPipeline(base_notes=notes_dict[track_name])
                for mod in modifiers:
                    p.add_modifier(mod)
                notes_dict[track_name] = p.process(mod_ctx)

    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
    instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks}

    file_path = out_dir / f"{name}.mid"
    export_multitrack_midi(tracks_data, str(file_path), bpm=bpm, instruments=instruments_map)
    return file_path


def main():
    print("=" * 80)
    print("  M E I J I   K A I K A   —   Dawn of Light")
    print("  明治開化")
    print("=" * 80)

    out_dir = Path("output/album_meiji_kaika")
    out_dir.mkdir(exist_ok=True, parents=True)

    # Scales — collision of worlds
    in_sen = Scale(0, Mode.JAPANESE)              # traditional
    kumoi = Scale(7, Mode.KUMOI)                  # traditional pentatonic
    minor_penta = Scale(9, Mode.MINOR_PENTATONIC) # bluesy, Western-adjacent
    dorian = Scale(0, Mode.DORIAN)                # Western modal
    major = Scale(0, Mode.MAJOR)                  # Western major — the "new world"

    # =========================================================================
    # 1. Падение сёгуната — Fall of the Shogunate
    # Thunderous taiko, kagura war drums, gagaku brass stabs.
    # The old order collapses in fire. Kabuki tension meets raw power.
    # =========================================================================
    print("\n  [1/6] Падение сёгуната")

    t1_tracks = [
        TrackConfig("War_Taiko", "melody", "taiko", density=1.0,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_taiko_festival_16th")}),
        TrackConfig("Kagura_War", "melody", "drums", density=0.8,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_kagura_drums_4_4")}),
        TrackConfig("Gagaku_Brass", "chord", "strings", density=0.7,
                     params={"voicing": "open", "rhythm": get_rhythm("jp_gagaku_shoko_4_4")}),
        TrackConfig("Dark_Drone", "drone", "dark_pad", density=0.6, octave_shift=-1,
                     params={"variant": "dominant"}),
        TrackConfig("Battle_Shamisen", "melody", "shamisen", density=0.8,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_shamisen_tsugaru_16th")}),
    ]
    t1_parts = [
        IdeaPart(
            name="Storm_Gathering", bars=8, scale=in_sen, tempo=80,
            track_phrase_schedules={
                "War_Taiko":       structure_to_schedule("R A", 4),
                "Kagura_War":      structure_to_schedule("R A", 4),
                "Gagaku_Brass":    structure_to_schedule("A", 8),
                "Dark_Drone":      structure_to_schedule("A", 8),
                "Battle_Shamisen": structure_to_schedule("R R A B", 2),
            }
        ),
        IdeaPart(
            name="Collapse", bars=16, scale=in_sen, tempo=90,
            track_phrase_schedules={
                "War_Taiko":       structure_to_schedule("A B C B", 4),
                "Kagura_War":      structure_to_schedule("A B", 8),
                "Gagaku_Brass":    structure_to_schedule("A B C B", 4),
                "Dark_Drone":      structure_to_schedule("A", 16),
                "Battle_Shamisen": structure_to_schedule("B C", 8),
            }
        ),
    ]

    t1_drop = 32.0  # transition between parts
    t1_glue = {
        "Gagaku_Brass":    [DropSilenceModifier(silence_duration=2.0, specific_beats=[t1_drop], apply_at_end=False)],
        "Dark_Drone":      [DropSilenceModifier(silence_duration=2.0, specific_beats=[t1_drop], apply_at_end=False)],
        "Battle_Shamisen": [DropSilenceModifier(silence_duration=2.0, specific_beats=[t1_drop], apply_at_end=False)],
        "War_Taiko":       [DrumFillModifier(fill_duration=2.0, subdivision=0.25, fill_pitch=36,
                                              velocity_start=35, velocity_end=127, accent_on_drop=True,
                                              specific_beats=[t1_drop], apply_at_end=False)],
    }
    generate_track("1 Падение сёгуната", t1_parts, t1_tracks, out_dir, 80, glue=t1_glue)

    # =========================================================================
    # 2. Первые рельсы — First Rails
    # The steam train arrives. Mechanical 4/4 chug cut with traditional
    # flute. Forests fall, iron rises. A nation's heartbeat changes.
    # =========================================================================
    print("\n  [2/6] Первые рельсы")

    t2_tracks = [
        TrackConfig("Steam_Engine", "melody", "drums", density=0.9,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("straight_8ths")}),
        TrackConfig("Iron_Bass", "bass", "synth_bass", density=0.8, octave_shift=-1,
                     params={"style": "walking"}),
        TrackConfig("Forest_Flute", "melody", "shakuhachi", density=0.5,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_enka_ballad_free")}),
        TrackConfig("Progression_Piano", "chord", "harp", density=0.7,
                     params={"voicing": "closed", "rhythm": get_rhythm("straight_quarters")}),
    ]
    t2_parts = [
        IdeaPart(
            name="Arrival", bars=8, scale=dorian, tempo=100,
            track_phrase_schedules={
                "Steam_Engine":      structure_to_schedule("R A", 4),
                "Iron_Bass":         structure_to_schedule("R A", 4),
                "Forest_Flute":      structure_to_schedule("A B", 4),
                "Progression_Piano": structure_to_schedule("A", 8),
            }
        ),
        IdeaPart(
            name="Full_Speed", bars=16, scale=major, tempo=108,
            track_phrase_schedules={
                "Steam_Engine":      structure_to_schedule("A B", 8),
                "Iron_Bass":         structure_to_schedule("A B", 8),
                "Forest_Flute":      structure_to_schedule("R A R B", 4),
                "Progression_Piano": structure_to_schedule("A B C B", 4),
            }
        ),
    ]
    generate_track("2 Первые рельсы", t2_parts, t2_tracks, out_dir, 100)

    # =========================================================================
    # 3. Газовые фонари Гиндзы — Gas Lamps of Ginza
    # Westernization of Tokyo. Brass band meets koto. Waltz-time
    # ballroom dances in kimono. The bizarre beautiful collision.
    # =========================================================================
    print("\n  [3/6] Газовые фонари Гиндзы")

    t3_tracks = [
        TrackConfig("Brass_Band", "chord", "strings", density=0.8,
                     params={"voicing": "open", "rhythm": get_rhythm("straight_quarters")}),
        TrackConfig("Koto_Waltz", "melody", "koto", density=0.7,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_koto_dan_8th")}),
        TrackConfig("Walking_Bass", "bass", "synth_bass", density=0.7, octave_shift=-1,
                     params={"style": "walking"}),
        TrackConfig("Lantern_Pad", "drone", "pad", density=0.5,
                     params={"variant": "tonic"}),
        TrackConfig("City_Pulse", "melody", "drums", density=0.6,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_city_pop_groove_16th")}),
    ]
    t3_parts = [
        IdeaPart(
            name="Dusk", bars=8, scale=major, tempo=88,
            track_phrase_schedules={
                "Brass_Band":   structure_to_schedule("A", 8),
                "Koto_Waltz":   structure_to_schedule("R A", 4),
                "Walking_Bass": structure_to_schedule("A", 8),
                "Lantern_Pad":  structure_to_schedule("A", 8),
                "City_Pulse":   structure_to_schedule("R R A B", 2),
            }
        ),
        IdeaPart(
            name="Ballroom", bars=16, scale=dorian, tempo=95,
            track_phrase_schedules={
                "Brass_Band":   structure_to_schedule("A B", 8),
                "Koto_Waltz":   structure_to_schedule("A B C B", 4),
                "Walking_Bass": structure_to_schedule("A B", 8),
                "Lantern_Pad":  structure_to_schedule("A B", 8),
                "City_Pulse":   structure_to_schedule("A B", 8),
            }
        ),
    ]
    generate_track("3 Газовые фонари Гиндзы", t3_parts, t3_tracks, out_dir, 88)

    # =========================================================================
    # 4. Последний самурай — The Last Samurai
    # A warrior watches his world vanish. Piano (West) and shamisen (East)
    # trade phrases over a dying drone. Honor becomes nostalgia.
    # Sparse, intimate, devastating.
    # =========================================================================
    print("\n  [4/6] Последний самурай")

    t4_tracks = [
        TrackConfig("Memory_Drone", "drone", "strings", density=0.5, octave_shift=-1,
                     params={"variant": "tonic"}),
        TrackConfig("Western_Piano", "melody", "harp", density=0.6,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_enka_ballad_free")}),
        TrackConfig("Eastern_Shamisen", "melody", "shamisen", density=0.5,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_shamisen_jongara_16th")}),
        TrackConfig("Fading_Taiko", "melody", "taiko", density=0.3,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_noh_taiko_8th")}),
        TrackConfig("Dust_Wind", "nebula", "synth_fx", density=0.2,
                     params={"variant": "swell"}),
    ]
    t4_parts = [
        IdeaPart(
            name="Armor", bars=12, scale=in_sen, tempo=65,
            track_phrase_schedules={
                "Memory_Drone":     structure_to_schedule("A", 12),
                "Western_Piano":    structure_to_schedule("R A R B", 3),
                "Eastern_Shamisen": structure_to_schedule("R R A R", 3),
                "Fading_Taiko":     structure_to_schedule("R R R A", 3),
                "Dust_Wind":        structure_to_schedule("R A R B", 3),
            }
        ),
        IdeaPart(
            name="Renunciation", bars=12, scale=kumoi, tempo=60,
            track_phrase_schedules={
                "Memory_Drone":     structure_to_schedule("A", 12),
                "Western_Piano":    structure_to_schedule("A B", 6),
                "Eastern_Shamisen": structure_to_schedule("B A", 6),
                "Fading_Taiko":     structure_to_schedule("R A R B", 3),
                "Dust_Wind":        structure_to_schedule("A B", 6),
            }
        ),
    ]
    generate_track("4 Последний самурай", t4_parts, t4_tracks, out_dir, 65)

    # =========================================================================
    # 5. Железный тигр — Iron Tiger
    # Naval build-up, factories, military parades. Full industrial power.
    # Massive taiko + brass + bass. The nation becomes a machine.
    # Aggressive, relentless, majestic.
    # =========================================================================
    print("\n  [5/6] Железный тигр")

    t5_tracks = [
        TrackConfig("War_Machine_Taiko", "melody", "taiko", density=1.0,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_kabuki_odaiko_4_4")}),
        TrackConfig("Factory_Bass", "bass", "synth_bass", density=0.9, octave_shift=-2,
                     params={"style": "root_fifth"}),
        TrackConfig("Imperial_Brass", "chord", "strings", density=0.8,
                     params={"voicing": "spread", "rhythm": get_rhythm("straight_quarters")}),
        TrackConfig("Iron_Hihat", "melody", "drums", density=0.8,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("straight_16ths")}),
        TrackConfig("Engine_Riser", "melody", "synth_fx", density=0.6,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_taiko_matsuri_8th")}),
        TrackConfig("War_Shamisen", "melody", "shamisen", density=0.7,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_tsugaru_fast_32nd")}),
    ]
    t5_parts = [
        IdeaPart(
            name="Mobilization", bars=8, scale=minor_penta, tempo=110,
            track_phrase_schedules={
                "War_Machine_Taiko": structure_to_schedule("R A", 4),
                "Factory_Bass":      structure_to_schedule("A", 8),
                "Imperial_Brass":    structure_to_schedule("R A", 4),
                "Iron_Hihat":        structure_to_schedule("R A", 4),
                "Engine_Riser":      structure_to_schedule("R R A B", 2),
                "War_Shamisen":      structure_to_schedule("R R A B", 2),
            }
        ),
        IdeaPart(
            name="Full_Power", bars=16, scale=dorian, tempo=120,
            track_phrase_schedules={
                "War_Machine_Taiko": structure_to_schedule("A B", 8),
                "Factory_Bass":      structure_to_schedule("A B", 8),
                "Imperial_Brass":    structure_to_schedule("A B C B", 4),
                "Iron_Hihat":        structure_to_schedule("A B", 8),
                "Engine_Riser":      structure_to_schedule("R A R B", 4),
                "War_Shamisen":      structure_to_schedule("B C", 8),
            }
        ),
    ]

    t5_drop = 32.0
    t5_glue = {
        "Imperial_Brass":    [DropSilenceModifier(silence_duration=2.0, specific_beats=[t5_drop], apply_at_end=False)],
        "Factory_Bass":      [DropSilenceModifier(silence_duration=2.0, specific_beats=[t5_drop], apply_at_end=False)],
        "Engine_Riser":      [DropSilenceModifier(silence_duration=2.0, specific_beats=[t5_drop], apply_at_end=False)],
        "War_Shamisen":      [DropSilenceModifier(silence_duration=2.0, specific_beats=[t5_drop], apply_at_end=False)],
        "War_Machine_Taiko": [DrumFillModifier(fill_duration=2.0, subdivision=0.125, fill_pitch=36,
                                                velocity_start=25, velocity_end=127, accent_on_drop=True,
                                                specific_beats=[t5_drop], apply_at_end=False)],
    }
    generate_track("5 Железный тигр", t5_parts, t5_tracks, out_dir, 110, glue=t5_glue)

    # =========================================================================
    # 6. Рассвет Мэйдзи — Meiji Dawn
    # Bittersweet resolution. Old instruments and new harmonies find peace.
    # Shakuhachi, koto, piano, strings — all breathing together.
    # A new era begins, carrying the weight of what was lost.
    # =========================================================================
    print("\n  [6/6] Рассвет Мэйдзи")

    t6_tracks = [
        TrackConfig("Dawn_Pad", "drone", "strings", density=0.6, octave_shift=-1,
                     params={"variant": "tonic"}),
        TrackConfig("Old_Skakuhachi", "melody", "shakuhachi", density=0.5,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_gagaku_slow_free")}),
        TrackConfig("New_Piano", "melody", "harp", density=0.6,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_enka_ballad_free")}),
        TrackConfig("Bridge_Koto", "melody", "koto", density=0.5,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_koto_dan_8th")}),
        TrackConfig("Hope_Bass", "bass", "synth_bass", density=0.5, octave_shift=-1,
                     params={"style": "root_fifth"}),
        TrackConfig("Morning_Bell", "melody", "tubular_bells", density=0.15,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_ma_pause_free")}),
    ]
    t6_parts = [
        IdeaPart(
            name="Embers", bars=8, scale=in_sen, tempo=60,
            track_phrase_schedules={
                "Dawn_Pad":       structure_to_schedule("A", 8),
                "Old_Skakuhachi": structure_to_schedule("R A R B", 2),
                "New_Piano":      structure_to_schedule("R R A B", 2),
                "Bridge_Koto":    structure_to_schedule("R R R A", 2),
                "Hope_Bass":      structure_to_schedule("R A", 4),
                "Morning_Bell":   structure_to_schedule("R R R A", 2),
            }
        ),
        IdeaPart(
            name="Sunrise", bars=16, scale=major, tempo=72,
            track_phrase_schedules={
                "Dawn_Pad":       structure_to_schedule("A", 16),
                "Old_Skakuhachi": structure_to_schedule("A B", 8),
                "New_Piano":      structure_to_schedule("A B C B", 4),
                "Bridge_Koto":    structure_to_schedule("A B", 8),
                "Hope_Bass":      structure_to_schedule("A B", 8),
                "Morning_Bell":   structure_to_schedule("R A R B", 4),
            }
        ),
    ]
    generate_track("6 Рассвет Мэйдзи", t6_parts, t6_tracks, out_dir, 60)

    print()
    print("  Meiji Kaika — old world dies, new world is born.")
    print(f"  6 tracks: {out_dir.absolute()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
