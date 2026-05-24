# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_abyssal_shadows.py — A 4-track cinematic album "Abyssal Shadows".
Explores various minor modes using Dmitri Tymoczko's 'First Principles' via the Coupled HMM,
orchestrated using the expressive Phrase Scheduling system.
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    PhraseSlot, PhraseSchedule,
)
from melodica.generators import (
    MelodyGenerator, BassGenerator, StringsEnsembleGenerator, 
    AmbientPadGenerator, ArpeggiatorGenerator, FluteGenerator, 
    ChoirAahsGenerator, TimpaniGenerator, DrumKitPatternGenerator, 
    ChurchOrganGenerator, BrassSectionGenerator, LeadSynthGenerator, 
    PluckSequenceGenerator, DarkPadGenerator, Bass808SlidingGenerator,
    TrapDrumsGenerator, TubularBellsGenerator
)
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

# ---------------------------------------------------------------------------
# Phrase Schedule Helpers
# ---------------------------------------------------------------------------

def _rest(bars: int) -> PhraseSchedule:
    """Full silence for N bars."""
    return PhraseSchedule(slots=[PhraseSlot(kind="rest", bars=bars)], loop=False)

def _play(bars: int, label: str = "A") -> PhraseSchedule:
    """Full play for N bars."""
    return PhraseSchedule(slots=[PhraseSlot(kind="play", bars=bars, label=label)], loop=False)

def _play_rest(play_bars: int, rest_bars: int, label: str = "A", loop: bool = True) -> PhraseSchedule:
    """Alternating play and rest pattern."""
    return PhraseSchedule(slots=[
        PhraseSlot(kind="play", bars=play_bars, label=label),
        PhraseSlot(kind="rest", bars=rest_bars),
    ], loop=loop)

def main():
    print("================================================================================")
    print("  A B Y S S A L   S H A D O W S   —   C O U P L E D   H M M   M I N O R s")
    print("  4-Track Dark Cinematic Album | Phrase-Scheduled Arrangement | Coupled HMM")
    print("================================================================================")

    out_dir = Path("output/album_abyssal_shadows")
    out_dir.mkdir(exist_ok=True, parents=True)

    # ---------------------------------------------------------------------------
    # Track 1: Tenebrous Intro (D Dorian - Melancholy, Slow)
    # ---------------------------------------------------------------------------
    print("\n--- Composing Track 1: 01_Tenebrous_Intro ---")
    
    t1_tracks = [
        TrackConfig(
            name="Lush_Strings",
            generator=StringsEnsembleGenerator(section_size="full", articulation="legato", divisi=2),
            instrument="strings", density=0.8,
        ),
        TrackConfig(
            name="Deep_Bass",
            generator=BassGenerator(style="root_only"),
            instrument="contrabass", density=0.7, octave_shift=-2,
        ),
        TrackConfig(
            name="Cinematic_Pad",
            generator=AmbientPadGenerator(voicing="spread"),
            instrument="dark_pad", density=0.6, octave_shift=-1,
        ),
        TrackConfig(
            name="Lead_Flute",
            generator=FluteGenerator(),
            instrument="flute", density=0.5, octave_shift=1,
            phrase_schedule=_play_rest(4, 4, label="F", loop=True)
        ),
    ]

    t1_parts = [
        IdeaPart(
            name="Tenebrous Intro",
            bars=8,
            scale=Scale(2, Mode.DORIAN),
            tempo=70,
            time_signature=(4, 4),
            progression_type="coupled_hmm",
        )
    ]

    t1_config = IdeaToolConfig(
        style="cinematic",
        parts=t1_parts,
        tracks=t1_tracks,
        use_voice_leading=True,
        use_harmonic_verifier=True,
    )

    t1_notes = IdeaTool(t1_config).generate()
    t1_tracks_data = {k: v for k, v in t1_notes.items() if not k.startswith("_") and isinstance(v, list)}
    
    t1_instruments = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in t1_tracks}
    export_multitrack_midi(
        t1_tracks_data,
        str(out_dir / "01_Tenebrous_Intro.mid"),
        bpm=70,
        time_sig=(4, 4),
        instruments=t1_instruments
    )
    print("    ✓ Exported 01_Tenebrous_Intro.mid")

    # ---------------------------------------------------------------------------
    # Track 2: Phrygian Chasm (G Phrygian - Intense, Rhythmic, Dramatic)
    # ---------------------------------------------------------------------------
    print("\n--- Composing Track 2: 02_Phrygian_Chasm ---")
    
    t2_tracks = [
        TrackConfig(
            name="Staccato_Strings",
            generator=StringsEnsembleGenerator(section_size="full", articulation="staccato", divisi=1),
            instrument="violin", density=0.8, octave_shift=1,
            phrase_schedule=_play_rest(4, 2, label="S", loop=True)
        ),
        TrackConfig(
            name="Epic_Choir",
            generator=ChoirAahsGenerator(voice_count=8, dynamics="ff"),
            instrument="choir", density=0.7, octave_shift=1,
            phrase_schedule=_play_rest(4, 4, label="C", loop=True)
        ),
        TrackConfig(
            name="Tension_Brass",
            generator=BrassSectionGenerator(),
            instrument="french_horn", density=0.6,
            phrase_schedule=_play_rest(8, 8, label="B", loop=True)
        ),
        TrackConfig(
            name="Timpani",
            generator=TimpaniGenerator(),
            instrument="timpani", density=0.5, octave_shift=-1,
            phrase_schedule=_play_rest(2, 2, label="T", loop=True)
        ),
        TrackConfig(
            name="Drums",
            generator=DrumKitPatternGenerator(style="cinematic_epic"),
            instrument="synth_drum", density=0.8,
        ),
    ]

    t2_parts = [
        IdeaPart(
            name="Phrygian Chasm",
            bars=16,
            scale=Scale(7, Mode.PHRYGIAN),
            tempo=115,
            time_signature=(4, 4),
            progression_type="coupled_hmm",
        )
    ]

    t2_config = IdeaToolConfig(
        style="cinematic_hybrid",
        parts=t2_parts,
        tracks=t2_tracks,
        use_voice_leading=True,
        use_harmonic_verifier=True,
    )

    t2_notes = IdeaTool(t2_config).generate()
    t2_tracks_data = {k: v for k, v in t2_notes.items() if not k.startswith("_") and isinstance(v, list)}
    
    t2_instruments = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in t2_tracks}
    export_multitrack_midi(
        t2_tracks_data,
        str(out_dir / "02_Phrygian_Chasm.mid"),
        bpm=115,
        time_sig=(4, 4),
        instruments=t2_instruments
    )
    print("    ✓ Exported 02_Phrygian_Chasm.mid")

    # ---------------------------------------------------------------------------
    # Track 3: Hungarian Requiem (A Hungarian Minor - Gothic, Tragic)
    # ---------------------------------------------------------------------------
    print("\n--- Composing Track 3: 03_Hungarian_Requiem ---")
    
    t3_tracks = [
        TrackConfig(
            name="Gothic_Organ",
            generator=ChurchOrganGenerator(),
            instrument="church_organ", density=0.7,
        ),
        TrackConfig(
            name="Requiem_Strings",
            generator=StringsEnsembleGenerator(section_size="full", articulation="legato", divisi=3),
            instrument="cello", density=0.8, octave_shift=-1,
            phrase_schedule=_play_rest(8, 8, label="RS", loop=True)
        ),
        TrackConfig(
            name="Tragic_Choir",
            generator=ChoirAahsGenerator(voice_count=6, dynamics="p"),
            instrument="choir", density=0.6, octave_shift=1,
            phrase_schedule=_play_rest(4, 4, label="TC", loop=True)
        ),
        TrackConfig(
            name="Tubular_Bells",
            generator=TubularBellsGenerator(),
            instrument="tubular_bells", density=0.4, octave_shift=2,
            phrase_schedule=_play_rest(2, 6, label="TB", loop=True)
        ),
    ]

    t3_parts = [
        IdeaPart(
            name="Hungarian Requiem",
            bars=16,
            scale=Scale(9, Mode.HUNGARIAN_MINOR),
            tempo=60,
            time_signature=(3, 4),
            progression_type="coupled_hmm",
        )
    ]

    t3_config = IdeaToolConfig(
        style="cinematic",
        parts=t3_parts,
        tracks=t3_tracks,
        use_voice_leading=True,
        use_harmonic_verifier=True,
    )

    t3_notes = IdeaTool(t3_config).generate()
    t3_tracks_data = {k: v for k, v in t3_notes.items() if not k.startswith("_") and isinstance(v, list)}
    
    t3_instruments = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in t3_tracks}
    export_multitrack_midi(
        t3_tracks_data,
        str(out_dir / "03_Hungarian_Requiem.mid"),
        bpm=60,
        time_sig=(3, 4),
        instruments=t3_instruments
    )
    print("    ✓ Exported 03_Hungarian_Requiem.mid")

    # ---------------------------------------------------------------------------
    # Track 4: Super Locrian Eclipse (E Super Locrian - Electronic Climax)
    # ---------------------------------------------------------------------------
    print("\n--- Composing Track 4: 04_Super_Locrian_Eclipse ---")
    
    t4_tracks = [
        TrackConfig(
            name="Sliding_808",
            generator=Bass808SlidingGenerator(),
            instrument="synth_bass", density=0.8, octave_shift=-2,
        ),
        TrackConfig(
            name="Lead_Synth",
            generator=LeadSynthGenerator(),
            instrument="lead_synth", density=0.7, octave_shift=1,
            phrase_schedule=_play_rest(8, 4, label="LS", loop=True)
        ),
        TrackConfig(
            name="Dark_Pad",
            generator=DarkPadGenerator(),
            instrument="dark_pad", density=0.6, octave_shift=-1,
        ),
        TrackConfig(
            name="Pluck_Arp",
            generator=PluckSequenceGenerator(),
            instrument="celesta", density=0.5, octave_shift=2,
            phrase_schedule=_play_rest(4, 4, label="PA", loop=True)
        ),
        TrackConfig(
            name="Trap_Drums",
            generator=TrapDrumsGenerator(),
            instrument="synth_drum", density=0.9,
        ),
    ]

    t4_parts = [
        IdeaPart(
            name="Super Locrian Eclipse",
            bars=24,
            scale=Scale(4, Mode.SUPER_LOCRIAN),
            tempo=140,
            time_signature=(4, 4),
            progression_type="coupled_hmm",
        )
    ]

    t4_config = IdeaToolConfig(
        style="electronic",
        parts=t4_parts,
        tracks=t4_tracks,
        use_voice_leading=True,
        use_harmonic_verifier=True,
    )

    t4_notes = IdeaTool(t4_config).generate()
    t4_tracks_data = {k: v for k, v in t4_notes.items() if not k.startswith("_") and isinstance(v, list)}
    
    t4_instruments = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in t4_tracks}
    export_multitrack_midi(
        t4_tracks_data,
        str(out_dir / "04_Super_Locrian_Eclipse.mid"),
        bpm=140,
        time_sig=(4, 4),
        instruments=t4_instruments
    )
    print("    ✓ Exported 04_Super_Locrian_Eclipse.mid")

    print("\n================================================================================")
    print(f"  PRODUCTION COMPLETE. Output: {out_dir}")
    print("================================================================================")

if __name__ == "__main__":
    main()
