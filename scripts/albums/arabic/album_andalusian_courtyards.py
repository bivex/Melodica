# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/arabic/album_andalusian_courtyards.py
    — "Andalusian Courtyards (بistas الأندلس)"

A journey across Moorish Al-Andalus, where each movement inhabits a different
maqam (Arabic modal scale) and a different courtyard of the imagination.

Emotional arc:
    01 The Gate of Alhambra      — Hijaz Kar  (double-harmonic, grand)
    02 Courtyard Dance           — Hijaz      (phrygian-dominant, fiery)
    03 Fountain of the Lions     — Bayati     (lyrical, watery)
    04 Sunset over Guadalquivir  — Kurd       (hungarian-minor, melancholic)
    05 Starlit Courtyard         — Nahawand   (natural-minor, nocturnal)

Unlike the existing sikah albums, every movement lives in its OWN maqam so the
tonal centres and modal colours rotate across the album. Mixed time signatures
and tempos, CoupledHMM progressions.
"""

from pathlib import Path

from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

from melodica.generators.orchestral_strings import (
    ViolinGenerator, ViolaGenerator, CelloGenerator, ContrabassGenerator,
)
from melodica.generators.orchestral_brass import FrenchHornGenerator
from melodica.generators.orchestral_woodwinds import FluteGenerator, OboeGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.plucked_solo import PianoSoloGenerator, EthnicPluckedGenerator
from melodica.generators.chromatic_percussion import VibraphoneGenerator, CelestaGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.vocal_oohs import VocalOohsGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ethnic_world import EthnicWorldGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.wind_brass_solo import WoodwindSoloGenerator
from melodica.generators.ambient import AmbientPadGenerator


# Distinct maqamat — the album's harmonic journey. Roots are spread across the
# circle so no two consecutive movements share a tonal centre.
HIJAZ_KAR    = Scale(root=2, mode=Mode.DOUBLE_HARMONIC)   # D double-harmonic
HIJAZ        = Scale(root=4, mode=Mode.PHRYGIAN_DOMINANT) # E Hijaz
BAYATI       = Scale(root=5, mode=Mode.BAYATI)            # F Bayati
KURD         = Scale(root=7, mode=Mode.HUNGARIAN_MINOR)   # G Kurd-ish (aug-2 colour)
NAHAWAND     = Scale(root=9, mode=Mode.NATURAL_MINOR)     # A Nahawand (minor)


def generate_andalusian_courtyards():
    album_dir = Path("output/album_andalusian_courtyards")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("    A N D A L U S I A N   C O U R T Y A R D S")
    print("    بistas الأندلس  —  A Maqam Journey through Moorish Spain")
    print("=" * 80)

    movements = [
        # name, maqam, tempo, time-signature, bars
        ("01_Gate_of_Alhambra",     HIJAZ_KAR, 76,  (4, 4), 48),
        ("02_Courtyard_Dance",      HIJAZ,     108, (6, 8), 44),
        ("03_Fountain_of_Lions",    BAYATI,    88,  (3, 4), 52),
        ("04_Sunset_Guadalquivir",  KURD,      64,  (4, 4), 56),
        ("05_Starlit_Courtyard",    NAHAWAND,  96,  (6, 8), 48),
    ]

    # ── 01: Gate of Alhambra (Hijaz Kar) — grand, ceremonial entry ─────────
    # Brass fanfare, hand-drum procession, solo nay, choir.
    tracks_map = {
        "01_Gate_of_Alhambra": [
            TrackConfig(name="Procession_Drum", generator=ElectronicDrumsGenerator(kit="ethnic"), instrument="taiko", density=0.7),
            TrackConfig(name="Royal_Horn",      generator=FrenchHornGenerator(articulation="sustained", dynamic_curve="swell"), instrument="french_horn", density=0.45),
            TrackConfig(name="Gate_Strings",    generator=StringsEnsembleGenerator(section_size="full", articulation="legato", dynamic_curve="crescendo"), instrument="strings", density=0.55),
            TrackConfig(name="Ceremonial_Nay",  generator=WoodwindSoloGenerator(instrument="recorder", breath_vibrato=True), instrument="shakuhachi", density=0.4, mpe=True),
            TrackConfig(name="Procession_Choir", generator=ChoirAahsGenerator(voice_count=4, dynamics="mf", syllable="aah"), instrument="choir", density=0.3),
        ],

        # ── 02: Courtyard Dance (Hijaz) — fiery, rhythmic, castanets ───────
        # Oud riff drives, trumpet soars, frame-drum groove, hand-claps.
        "02_Courtyard_Dance": [
            TrackConfig(name="Oud_Riff",        generator=EthnicPluckedGenerator(instrument="sitar"), instrument="sitar", density=0.65, mpe=True),
            TrackConfig(name="Dance_Trumpet",   generator=MelodyGenerator(phrase_length=6.0, direction_bias=0.3), instrument="trumpet", density=0.55, mpe=True),
            TrackConfig(name="Frame_Drum",      generator=ElectronicDrumsGenerator(kit="ethnic"), instrument="steel_drums", density=0.7),
            TrackConfig(name="Dance_Strings",   generator=StringsLegatoGenerator(), instrument="strings", density=0.45),
            TrackConfig(name="Hand_Clap_Voice", generator=VocalOohsGenerator(syllable="aah", harmony_count=2), instrument="voice", density=0.35),
        ],

        # ── 03: Fountain of the Lions (Bayati) — watery, lyrical, limpid ───
        # Harp cascades like water, ney rises, cello aches, vibraphone halos.
        "03_Fountain_of_Lions": [
            TrackConfig(name="Water_Harp",     generator=ArpeggiatorGenerator(pattern="up", note_duration=0.375, voicing="spread"), instrument="harp", density=0.7),
            TrackConfig(name="Ney_Rising",     generator=EthnicWorldGenerator(instrument="shanai"), instrument="shanai", density=0.5, mpe=True),
            TrackConfig(name="Aching_Cello",   generator=CelloGenerator(articulation="sustained", vibrato=True), instrument="cello", density=0.35),
            TrackConfig(name="Water_Halo",     generator=VibraphoneGenerator(note_density=0.3), instrument="vibraphone", density=0.3),
            TrackConfig(name="Tender_Violin",  generator=ViolinGenerator(articulation="legato", vibrato=True), instrument="violin", density=0.4, mpe=True),
        ],

        # ── 04: Sunset over Guadalquivir (Kurd) — melancholic, slow ────────
        # Solo piano, contrabass weight, choir mourns, shakuhachi wails.
        "04_Sunset_Guadalquivir": [
            TrackConfig(name="Grief_Drone",    generator=DroneGenerator(variant="tonic", fade_in=4.0, fade_out=4.0), instrument="dark_pad", density=0.9, octave_shift=-1),
            TrackConfig(name="Lonely_Piano",   generator=PianoSoloGenerator(instrument="grand_piano", pedal=True, note_density=0.4), instrument="piano", density=0.45, mpe=True),
            TrackConfig(name="Wailing_Wind",   generator=EthnicWorldGenerator(instrument="shanai"), instrument="shanai", density=0.35, mpe=True),
            TrackConfig(name="Heavy_Bass",     generator=ContrabassGenerator(vibrato=False), instrument="contrabass", density=0.3),
            TrackConfig(name="Mourning_Choir", generator=ChoirAahsGenerator(voice_count=4, dynamics="mp", syllable="aah"), instrument="choir", density=0.3),
        ],

        # ── 05: Starlit Courtyard (Nahawand) — nocturnal, resolving, warm ──
        # Full strings sweep, flute dances, oud celebrates, choir rises.
        "05_Starlit_Courtyard": [
            TrackConfig(name="Night_Strings",   generator=StringsEnsembleGenerator(section_size="full", articulation="legato", dynamic_curve="crescendo"), instrument="strings", density=0.6),
            TrackConfig(name="Dancing_Flute",   generator=FluteGenerator(articulation="legato", vibrato=True, breath_phrase=True), instrument="flute", density=0.5, mpe=True),
            TrackConfig(name="Oud_Celebration", generator=EthnicPluckedGenerator(instrument="sitar"), instrument="sitar", density=0.55, mpe=True),
            TrackConfig(name="Starlight_Vibes", generator=VibraphoneGenerator(note_density=0.35), instrument="vibraphone", density=0.3),
            TrackConfig(name="Rising_Choir",    generator=ChoirAahsGenerator(voice_count=4, dynamics="f", syllable="aah"), instrument="choir", density=0.35),
            TrackConfig(name="Joyful_Drums",    generator=ElectronicDrumsGenerator(kit="ethnic"), instrument="steel_drums", density=0.55),
        ],
    }

    for name, maqam, tempo, ts, bars in movements:
        print(f"\n--- Composing: {name} [{maqam.mode.value}, {ts[0]}/{ts[1]}, {tempo} BPM] ---")

        parts = [IdeaPart(
            name=name, bars=bars,
            scale=maqam, tempo=tempo,
            time_signature=ts,
            progression_type="coupled_hmm",
        )]

        track_list = tracks_map[name]
        instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in track_list}

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            time_signature=ts,
            tempo=tempo,
            use_tension_curve=True,
            use_harmonic_verifier=True,
            parts=parts,
            tracks=track_list,
        )

        notes_dict = IdeaTool(tool_config).generate()
        tracks_data = {k: v for k, v in notes_dict.items()
                       if not k.startswith("_") and isinstance(v, list)}

        export_multitrack_midi(
            tracks_data, str(album_dir / f"{name}.mid"),
            bpm=tempo, key=maqam,
            instruments=instruments_map,
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set()),
        )
        print(f"    Exported {name}.mid")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: ANDALUSIAN COURTYARDS")
    print(f"  Maqam journey: Hijaz Kar → Hijaz → Bayati → Kurd → Nahawand")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    generate_andalusian_courtyards()
