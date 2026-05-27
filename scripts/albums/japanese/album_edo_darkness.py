# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_edo_darkness.py — Dark Edo Period Album Generator.

Album: "Edo Darkness: Shadows of the Shogunate"
Theme: The dark side of Japan's Edo period (1603-1868) —
       forbidden quarters, haunted temples, Ronin wandering moonlit roads,
       and the oppressive silence beneath the Shogun's rule.

Tracks:
1. Kagemusha — Shadow Warrior's Oath (Noh theatre + darkness)
2. Yūrei Yokocho — Ghost Alley of Yoshiwara (Haunted pleasure quarter)
3. Ronin no Michi — Path of the Masterless Samurai (Tension, wandering)
4. Jigoku Mon — The Gate of Hell (Kabuki dramatic climax)
5. Gokurakuji — Temple of Lost Prayers (Final requiem, fading embers)
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
from melodica.generators.tension import TensionGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.modifiers import (
    ModifierPipeline, ModifierContext,
    DropSilenceModifier, DrumFillModifier,
    CrescendoModifier, HumanizeModifier,
)
from melodica.types import MusicTimeline


def generate_track(name, parts, tracks, out_dir, bpm, glue=None):
    print(f"  > Generating: '{name}'...")
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
        scale_ref = parts[0].scale
        mod_ctx = ModifierContext(
            duration_beats=total_bars * 4,
            chords=timeline.chords,
            timeline=timeline,
            scale=scale_ref,
        )
        for track_name, modifiers in glue.items():
            if track_name in notes_dict:
                p = ModifierPipeline(base_notes=notes_dict[track_name])
                for mod in modifiers:
                    p.add_modifier(mod)
                notes_dict[track_name] = p.process(mod_ctx)

    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
    instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks}

    file_path = out_dir / f"{name.replace(' ', '_')}.mid"
    export_multitrack_midi(tracks_data, str(file_path), bpm=bpm, instruments=instruments_map)
    return file_path


def main():
    print("=" * 80)
    print("  E D O   D A R K N E S S :   Shadows of the Shogunate")
    print("=" * 80)

    out_dir = Path("output/album_edo_darkness")
    out_dir.mkdir(exist_ok=True, parents=True)

    # Scales
    in_sen = Scale(0, Mode.JAPANESE)        # C In-Sen: dark, angular
    kumoi = Scale(7, Mode.KUMOI)            # G Kumoi: mysterious pentatonic
    phrygian_dark = Scale(6, Mode.PHRYGIAN) # F# Phrygian: tension, Spanish-dark
    locrian = Scale(11, Mode.LOCRIAN)        # B Locrian: unstable, haunted

    # =========================================================================
    # TRACK 1: Kagemusha — Shadow Warrior's Oath
    # Slow, ritualistic Noh-inspired opening. Deep drums, distant flute,
    # unsettling drones. The ghost of a samurai rises.
    # =========================================================================
    print("\n  [1/5] Kagemusha — Shadow Warrior's Oath")

    t1_tracks = [
        TrackConfig("Noh_Drone", "drone", "dark_pad", density=0.6, octave_shift=-1,
                     params={"variant": "tonic"}),
        TrackConfig("Noh_Taiko", "melody", "taiko", density=0.5,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_noh_taiko_8th")}),
        TrackConfig("Kotsuzumi_Pulse", "melody", "drums", density=0.6,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_noh_kotsuzumi_8th")}),
        TrackConfig("Shakuhachi_Lament", "melody", "shakuhachi", density=0.4,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_shakuhachi_free")}),
    ]
    t1_parts = [
        IdeaPart(
            name="Summoning", bars=16, scale=in_sen, tempo=55,
            track_phrase_schedules={
                "Noh_Drone":       structure_to_schedule("A", 16),
                "Noh_Taiko":       structure_to_schedule("R A R B", 4),
                "Kotsuzumi_Pulse": structure_to_schedule("R R A B", 4),
                "Shakuhachi_Lament": structure_to_schedule("R R R A", 4),
            }
        ),
        IdeaPart(
            name="Rising", bars=8, scale=in_sen, tempo=60,
            track_phrase_schedules={
                "Noh_Drone":       structure_to_schedule("A", 8),
                "Noh_Taiko":       structure_to_schedule("B", 8),
                "Kotsuzumi_Pulse": structure_to_schedule("B", 8),
                "Shakuhachi_Lament": structure_to_schedule("B", 8),
            }
        ),
    ]
    generate_track("1 Kagemusha", t1_parts, t1_tracks, out_dir, 55)

    # =========================================================================
    # TRACK 2: Yurei Yokocho — Ghost Alley of Yoshiwara
    # Haunted pleasure quarter. Dissonant koto, spectral voices,
    # flickering lantern rhythm. Uneven, ghostly 3/4 feel.
    # =========================================================================
    print("\n  [2/5] Yurei Yokocho — Ghost Alley of Yoshiwara")

    t2_tracks = [
        TrackConfig("Ghost_Drone", "drone", "dark_pad", density=0.5, octave_shift=-2,
                     params={"variant": "dominant"}),
        TrackConfig("Haunted_Koto", "melody", "koto", density=0.7,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_koto_dan_8th")}),
        TrackConfig("Yurei_Voice", "nebula", "synth_voice", density=0.3,
                     params={"variant": "cloud"}),
        TrackConfig("Otsuzumi_Ghost", "melody", "drums", density=0.5,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_noh_otsuzumi_8th")}),
        TrackConfig("Tubular_Bell", "melody", "tubular_bells", density=0.2,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_ma_pause_free")}),
    ]
    t2_parts = [
        IdeaPart(
            name="Lanterns", bars=16, scale=locrian, tempo=70,
            track_phrase_schedules={
                "Ghost_Drone":    structure_to_schedule("A", 16),
                "Haunted_Koto":   structure_to_schedule("R A B A", 4),
                "Yurei_Voice":    structure_to_schedule("R R A R", 4),
                "Otsuzumi_Ghost": structure_to_schedule("R A R B", 4),
                "Tubular_Bell":   structure_to_schedule("R R R A", 4),
            }
        ),
        IdeaPart(
            name="Possession", bars=12, scale=kumoi, tempo=75,
            track_phrase_schedules={
                "Ghost_Drone":    structure_to_schedule("A", 12),
                "Haunted_Koto":   structure_to_schedule("B C B C", 3),
                "Yurei_Voice":    structure_to_schedule("A B A B", 3),
                "Otsuzumi_Ghost": structure_to_schedule("B", 12),
                "Tubular_Bell":   structure_to_schedule("A", 12),
            }
        ),
    ]
    generate_track("2 Yurei Yokocho", t2_parts, t2_tracks, out_dir, 70)

    # =========================================================================
    # TRACK 3: Ronin no Michi — Path of the Masterless Samurai
    # Tension-driven. Shamisen + driving taiko, Phrygian darkness.
    # Long build into a climactic confrontation.
    # =========================================================================
    print("\n  [3/5] Ronin no Michi — Path of the Masterless Samurai")

    t3_tracks = [
        TrackConfig("Ronin_Shamisen", "melody", "shamisen", density=0.8,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_shamisen_tsugaru_16th")}),
        TrackConfig("March_Taiko", "melody", "taiko", density=0.9,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_taiko_festival_16th")}),
        TrackConfig("Dark_Bass", "bass", "synth_bass", density=0.7, octave_shift=-1,
                     params={"style": "root_fifth"}),
        TrackConfig("Tension_Pad", "drone", "dark_pad", density=0.5, octave_shift=-1,
                     params={"variant": "tonic"}),
        TrackConfig("Distant_Kagura", "melody", "drums", density=0.4,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_kagura_drums_4_4")}),
    ]
    t3_parts = [
        IdeaPart(
            name="Departure", bars=8, scale=phrygian_dark, tempo=85,
            track_phrase_schedules={
                "Ronin_Shamisen": structure_to_schedule("R A", 4),
                "March_Taiko":    structure_to_schedule("R A", 4),
                "Dark_Bass":      structure_to_schedule("A", 8),
                "Tension_Pad":    structure_to_schedule("A", 8),
                "Distant_Kagura": structure_to_schedule("R R A B", 2),
            }
        ),
        IdeaPart(
            name="Confrontation", bars=16, scale=phrygian_dark, tempo=95,
            track_phrase_schedules={
                "Ronin_Shamisen": structure_to_schedule("A B", 8),
                "March_Taiko":    structure_to_schedule("A B C B", 4),
                "Dark_Bass":      structure_to_schedule("A B", 8),
                "Tension_Pad":    structure_to_schedule("A", 16),
                "Distant_Kagura": structure_to_schedule("A B", 8),
            }
        ),
    ]

    # Glue: silence before final clash, drum fill into climax at beat 64
    t3_drop = 64.0  # end of "Departure" + halfway into "Confrontation"
    t3_glue = {
        "Ronin_Shamisen": [DropSilenceModifier(silence_duration=3.0, specific_beats=[t3_drop], apply_at_end=False)],
        "Dark_Bass":      [DropSilenceModifier(silence_duration=3.0, specific_beats=[t3_drop], apply_at_end=False)],
        "Tension_Pad":    [DropSilenceModifier(silence_duration=3.0, specific_beats=[t3_drop], apply_at_end=False)],
        "March_Taiko":    [DrumFillModifier(fill_duration=3.0, subdivision=0.25, fill_pitch=36,
                                             velocity_start=30, velocity_end=127, accent_on_drop=True,
                                             specific_beats=[t3_drop], apply_at_end=False)],
    }
    generate_track("3 Ronin no Michi", t3_parts, t3_tracks, out_dir, 85, glue=t3_glue)

    # =========================================================================
    # TRACK 4: Jigoku Mon — The Gate of Hell
    # Kabuki-inspired maximal drama. Massive odaiko, clappers, full orchestral
    # tension. The gates of Buddhist hell tear open.
    # =========================================================================
    print("\n  [4/5] Jigoku Mon — The Gate of Hell")

    t4_tracks = [
        TrackConfig("Odaiko_Rage", "melody", "taiko", density=1.0,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_kabuki_odaiko_4_4")}),
        TrackConfig("Ki_Clappers", "melody", "drums", density=0.9,
                     params={"mode": "chord_tones", "rhythm": get_rhythm("jp_kabuki_ki_claps_8th")}),
        TrackConfig("Nagauta_Strings", "melody", "tremolo_strings", density=0.7,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_kabuki_nagauta_8th")}),
        TrackConfig("Hell_Bass", "bass", "synth_bass", density=0.8, octave_shift=-2,
                     params={"style": "root_fifth"}),
        TrackConfig("Doom_Choir", "nebula", "choir", density=0.4,
                     params={"variant": "cloud"}),
        TrackConfig("Shamisen_Fury", "melody", "shamisen", density=0.9,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_tsugaru_fast_32nd")}),
    ]
    t4_parts = [
        IdeaPart(
            name="Portent", bars=8, scale=in_sen, tempo=80,
            track_phrase_schedules={
                "Odaiko_Rage":      structure_to_schedule("R A", 4),
                "Ki_Clappers":      structure_to_schedule("R R A B", 2),
                "Nagauta_Strings":  structure_to_schedule("A", 8),
                "Hell_Bass":        structure_to_schedule("A", 8),
                "Doom_Choir":       structure_to_schedule("R A", 4),
                "Shamisen_Fury":    structure_to_schedule("R R A B", 2),
            }
        ),
        IdeaPart(
            name="Inferno", bars=16, scale=phrygian_dark, tempo=100,
            track_phrase_schedules={
                "Odaiko_Rage":      structure_to_schedule("A B", 8),
                "Ki_Clappers":      structure_to_schedule("A B", 8),
                "Nagauta_Strings":  structure_to_schedule("A B C B", 4),
                "Hell_Bass":        structure_to_schedule("A B", 8),
                "Doom_Choir":       structure_to_schedule("A B", 8),
                "Shamisen_Fury":    structure_to_schedule("B C", 8),
            }
        ),
    ]

    # Glue: dramatic silence before hell gates open at beat 32
    t4_gate = 32.0
    t4_glue = {
        "Nagauta_Strings": [DropSilenceModifier(silence_duration=2.0, specific_beats=[t4_gate], apply_at_end=False)],
        "Hell_Bass":       [DropSilenceModifier(silence_duration=2.0, specific_beats=[t4_gate], apply_at_end=False)],
        "Doom_Choir":      [DropSilenceModifier(silence_duration=2.0, specific_beats=[t4_gate], apply_at_end=False)],
        "Shamisen_Fury":   [DropSilenceModifier(silence_duration=2.0, specific_beats=[t4_gate], apply_at_end=False)],
        "Odaiko_Rage":     [DrumFillModifier(fill_duration=2.0, subdivision=0.125, fill_pitch=36,
                                              velocity_start=20, velocity_end=127, accent_on_drop=True,
                                              specific_beats=[t4_gate], apply_at_end=False)],
    }
    generate_track("4 Jigoku Mon", t4_parts, t4_tracks, out_dir, 80, glue=t4_glue)

    # =========================================================================
    # TRACK 5: Gokurakuji — Temple of Lost Prayers
    # Final requiem. Fading embers of incense, solitary shakuhachi,
    # drone dissolving into nothing. The Edo night swallows all.
    # =========================================================================
    print("\n  [5/5] Gokurakuji — Temple of Lost Prayers")

    t5_tracks = [
        TrackConfig("Incense_Drone", "drone", "dark_pad", density=0.5, octave_shift=-2,
                     params={"variant": "tonic"}),
        TrackConfig("Temple_Bell", "melody", "tubular_bells", density=0.15,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_ma_pause_free")}),
        TrackConfig("Final_Shakuhachi", "melody", "shakuhachi", density=0.3,
                     params={"mode": "downbeat_chord", "rhythm": get_rhythm("jp_shakuhachi_free")}),
        TrackConfig("Fading_Strings", "melody", "strings", density=0.4,
                     params={"mode": "scale_walk", "rhythm": get_rhythm("jp_gagaku_slow_free")}),
        TrackConfig("Ash_Wind", "nebula", "synth_fx", density=0.2,
                     params={"variant": "swell"}),
    ]
    t5_parts = [
        IdeaPart(
            name="Embers", bars=24, scale=kumoi, tempo=50,
            track_phrase_schedules={
                "Incense_Drone":    structure_to_schedule("A", 24),
                "Temple_Bell":      structure_to_schedule("R A R B", 6),
                "Final_Shakuhachi": structure_to_schedule("R R A B A R", 4),
                "Fading_Strings":   structure_to_schedule("R A R B", 6),
                "Ash_Wind":         structure_to_schedule("R A R B", 6),
            }
        ),
    ]
    generate_track("5 Gokurakuji", t5_parts, t5_tracks, out_dir, 50)

    print()
    print("  SUCCESS! Album 'Edo Darkness: Shadows of the Shogunate' generated.")
    print(f"  5 tracks saved in: {out_dir.absolute()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
