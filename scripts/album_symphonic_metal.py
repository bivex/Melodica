# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_symphonic_metal.py — A massive 10-track Symphonic Metal epic.
Blends academic orchestral arrangements with heavy metal guitars and drums.
Showcases the 12-chord Cinematic HMM, complex forms, and extreme tension curves.

Phrase scheduling replaces track_mute: instruments have expressive play/rest/ghost
patterns per part via PhraseSchedule, giving each track a living, breathing presence
rather than a simple binary on/off mute.
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    PhraseSlot, PhraseSchedule,
)
from melodica.generators import (
    StringsEnsembleGenerator, ChoirAahsGenerator,
    TimpaniGenerator, PowerChordGenerator, RiffGenerator, TremoloPickingGenerator,
    TrapDrumsGenerator, ArpeggiatorGenerator,
    WoodwindsEnsembleGenerator,
)
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi


# ---------------------------------------------------------------------------
# Helpers — build common PhraseSchedule patterns concisely
# ---------------------------------------------------------------------------

def _rest(bars: int) -> PhraseSchedule:
    """Full silence for N bars — replaces track_mute for a specific part."""
    return PhraseSchedule(slots=[PhraseSlot(kind="rest", bars=bars)], loop=False)


def _play(bars: int, label: str = "A") -> PhraseSchedule:
    """Full play for N bars with the given label."""
    return PhraseSchedule(slots=[PhraseSlot(kind="play", bars=bars, label=label)], loop=False)


def _play_rest(play_bars: int, rest_bars: int, label: str = "A", loop: bool = True) -> PhraseSchedule:
    """Alternating play / rest pattern, optionally looping."""
    return PhraseSchedule(slots=[
        PhraseSlot(kind="play", bars=play_bars, label=label),
        PhraseSlot(kind="rest", bars=rest_bars),
    ], loop=loop)


def main():
    print("================================================================================")
    print("  S Y M P H O N Y   O F   S T E E L   &   F I R E")
    print("  10-Track Symphonic Metal Epic | 12-Chord Constrained HMM")
    print("================================================================================")

    out_dir = Path("output/album_symphonic_metal")
    out_dir.mkdir(exist_ok=True, parents=True)

    # ---------------------------------------------------------------------------
    # The Massive Hybrid Arrangement
    #
    # Default phrase_schedule on TrackConfig sets each instrument's baseline
    # breathing pattern for any part that doesn't override it.
    # Per-part track_phrase_schedules take priority over the TrackConfig default.
    # ---------------------------------------------------------------------------
    hybrid_orchestra = [
        # --- The Orchestra ---

        # Choir: continuous by default; per-part schedules give it arch shapes.
        TrackConfig(
            name="Epic_Choir",
            generator=ChoirAahsGenerator(voice_count=10, dynamics="ff"),
            instrument="choir",
            density=0.8,
            octave_shift=2,
        ),

        # Violins: spiccato bursts — 4 bars on, 2 bars off by default.
        TrackConfig(
            name="Violins_Spiccato",
            generator=StringsEnsembleGenerator(articulation="staccato", divisi=1),
            instrument="violin",
            density=0.9,
            octave_shift=3,
            phrase_schedule=_play_rest(4, 2, label="V", loop=True),
        ),

        # Cellos: continuous legato anchor.
        TrackConfig(
            name="Cellos_Legato",
            generator=StringsEnsembleGenerator(articulation="legato", divisi=2),
            instrument="cello",
            density=0.7,
            octave_shift=0,
        ),

        # Doom Brass: galloping riff — 4 bars on, 4 bars off by default.
        TrackConfig(
            name="Doom_Brass",
            generator=RiffGenerator(riff_pattern="gallop", power_chord=True),
            instrument="brass",
            density=0.9,
            octave_shift=-1,
            phrase_schedule=_play_rest(4, 4, label="DB", loop=True),
        ),

        # Woodwinds: call-and-response — 4 bars on, 4 bars off by default.
        TrackConfig(
            name="Woodwinds",
            generator=WoodwindsEnsembleGenerator(ensemble_mode="full"),
            instrument="flute",
            density=0.6,
            octave_shift=2,
            phrase_schedule=_play_rest(4, 4, label="WW", loop=True),
        ),

        # Timpani: continuous thunderous strikes.
        TrackConfig(
            name="Timpani_Strikes",
            generator=TimpaniGenerator(stroke_pattern="single"),
            instrument="timpani",
            density=1.0,
            octave_shift=-3,
        ),

        # Gothic Harpsichord: sparse gothic ostinato — 2 bars on, 2 bars off.
        TrackConfig(
            name="Gothic_Harpsichord",
            generator=ArpeggiatorGenerator(pattern="up_down", octaves=1),
            instrument="harpsichord",
            density=0.4,
            octave_shift=1,
            phrase_schedule=_play_rest(2, 2, label="GH", loop=True),
        ),

        # --- The Metal Band ---

        # Rhythm Guitars: continuous chug by default; silenced via per-part rest.
        TrackConfig(
            name="Rhythm_Guitars",
            generator=PowerChordGenerator(pattern="chug"),
            instrument="distortion_guitar",
            density=0.7,
            octave_shift=-1,
        ),

        # Lead Tremolo: intermittent lead fills — 4 bars on, 2 bars off by default.
        TrackConfig(
            name="Lead_Tremolo",
            generator=TremoloPickingGenerator(speed=0.1875),
            instrument="overdrive_guitar",
            density=0.4,
            octave_shift=1,
            phrase_schedule=_play_rest(4, 2, label="LT", loop=True),
        ),

        # Metal Bass: continuous driving gallop.
        TrackConfig(
            name="Metal_Bass",
            generator=RiffGenerator(riff_pattern="gallop", power_chord=False),
            instrument="electric_bass",
            density=1.0,
            octave_shift=-1,
        ),

        # Double Kick: unrelenting blast by default; silenced per-part where needed.
        TrackConfig(
            name="Double_Kick_Drums",
            generator=TrapDrumsGenerator(variant="heavy"),
            instrument="drums",
            density=1.0,
            octave_shift=-1,
        ),
    ]

    # ---------------------------------------------------------------------------
    # Track 1: Overture — The Awakening (E Minor, 85 BPM)
    #
    # Dark_Intro: pure orchestral dread — metal is completely absent.
    # Doom Brass creeps in at bar 5. Choir establishes its "A" motif then ghosts it.
    # The_Blast: metal explodes at bar 9. Ghost slots carry the intro motifs
    # forward into the new harsh harmony for thematic coherence.
    # ---------------------------------------------------------------------------
    t1 = [
        IdeaPart(
            name="Dark_Intro",
            bars=8,
            scale=Scale(4, Mode.NATURAL_MINOR),
            progression_type="constrained_hmm",
            progression_list=["Im9:8.0"],
            track_phrase_schedules={
                "Rhythm_Guitars":    _rest(8),
                "Lead_Tremolo":      _rest(8),
                "Double_Kick_Drums": _rest(8),
                # Doom Brass: 4 bars silence, then emerges ominously
                "Doom_Brass": PhraseSchedule(slots=[
                    PhraseSlot(kind="rest", bars=4),
                    PhraseSlot(kind="play", bars=4, label="DB_intro"),
                ], loop=False),
                # Choir: establishes the "choir_A" motif, then ghosts it softly
                "Epic_Choir": PhraseSchedule(slots=[
                    PhraseSlot(kind="play", bars=4, label="choir_A"),
                    PhraseSlot(kind="ghost", bars=4, label="choir_A"),
                ], loop=False),
            },
        ),
        IdeaPart(
            name="The_Blast",
            bars=8,
            scale=Scale(4, Mode.NATURAL_MINOR),
            progression_type="constrained_hmm",
            progression_list=["Im:4.0", "bVImaj7:4.0", "V7alt:4.0"],
            track_phrase_schedules={
                # Doom Brass ghosts the intro motif, then launches into full gallop
                "Doom_Brass": PhraseSchedule(slots=[
                    PhraseSlot(kind="ghost", bars=4, label="DB_intro"),
                    PhraseSlot(kind="play",  bars=4, label="DB_blast"),
                ], loop=False),
                # Choir echoes intro motif adapted to new chords, then new phrase
                "Epic_Choir": PhraseSchedule(slots=[
                    PhraseSlot(kind="ghost", bars=4, label="choir_A"),
                    PhraseSlot(kind="play",  bars=4, label="choir_B"),
                ], loop=False),
            },
        ),
    ]

    # ---------------------------------------------------------------------------
    # Track 2: Blood on the Snow (C Phrygian Dominant, 130 BPM)
    #
    # Full ensemble. Woodwinds and Harpsichord interlock in antiphonal 4-bar blocks
    # throughout the March. Chorus: Woodwinds ghost the march phrase into new chords.
    # ---------------------------------------------------------------------------
    t2 = [
        IdeaPart(
            name="March",
            bars=16,
            scale=Scale(0, Mode.PHRYGIAN_DOMINANT),
            progression_type="constrained_hmm",
            progression_list=["Im:8.0", "bIImaj7:4.0", "viidim:4.0"],
            track_phrase_schedules={
                # Harpsichord answers on bars 5–8, 13–16 (offset from woodwinds)
                "Gothic_Harpsichord": PhraseSchedule(slots=[
                    PhraseSlot(kind="rest", bars=4),
                    PhraseSlot(kind="play", bars=4, label="GH_march"),
                ], loop=True),
                # Woodwinds call on bars 1–4, 9–12
                "Woodwinds": PhraseSchedule(slots=[
                    PhraseSlot(kind="play", bars=4, label="WW_march"),
                    PhraseSlot(kind="rest", bars=4),
                ], loop=True),
            },
        ),
        IdeaPart(
            name="Chorus",
            bars=8,
            scale=Scale(0, Mode.PHRYGIAN_DOMINANT),
            progression_type="constrained_hmm",
            progression_list=["bVImaj9:4.0", "bVIIadd9:4.0", "Im:4.0"],
            track_phrase_schedules={
                # Ghost the march phrase under new chorus chords, then new statement
                "Woodwinds": PhraseSchedule(slots=[
                    PhraseSlot(kind="ghost", bars=4, label="WW_march"),
                    PhraseSlot(kind="play",  bars=4, label="WW_chorus"),
                ], loop=False),
                # Harpsichord: full presence in the chorus for gothic intensity
                "Gothic_Harpsichord": _play(8, label="GH_chorus"),
            },
        ),
    ]

    # ---------------------------------------------------------------------------
    # Track 3: The Clockwork God (F# Locrian — Extreme Dissonance, 110 BPM, 5/4)
    #
    # Harpsichord silenced (too tonal for Locrian). Woodwinds appear mid-section
    # as an eerie intrusion. Lead Tremolo overrides its default 4/2 pattern to
    # deliver an unbroken wall of dissonant picking for all 12 bars.
    # ---------------------------------------------------------------------------
    t3 = [
        IdeaPart(
            name="Grind",
            bars=12,
            scale=Scale(6, Mode.LOCRIAN),
            progression_type="constrained_hmm",
            progression_list=["Idim:4.0", "bVmaj7:4.0", "bIImaj9:4.0"],
            track_phrase_schedules={
                "Gothic_Harpsichord": _rest(12),
                # Woodwinds: silent, eerie intrusion in middle 4 bars, then gone
                "Woodwinds": PhraseSchedule(slots=[
                    PhraseSlot(kind="rest", bars=4),
                    PhraseSlot(kind="play", bars=4, label="WW_grind"),
                    PhraseSlot(kind="rest", bars=4),
                ], loop=False),
                # Lead Tremolo: override default 4/2 — relentless full 12 bars
                "Lead_Tremolo": _play(12, label="LT_grind"),
            },
        ),
    ]

    # ---------------------------------------------------------------------------
    # Track 4: Ballad of the Fallen (A Aeolian, 65 BPM, 3/4)
    #
    # Intimate orchestral-only ballad — entire metal band and brass silenced.
    # Choir delivers a full 16-bar arch and ghosts itself in the second half.
    # Violins breathe with 4/4 phrasing (override the default 4/2 pattern).
    # ---------------------------------------------------------------------------
    t4 = [
        IdeaPart(
            name="Acoustic",
            bars=16,
            scale=Scale(9, Mode.AEOLIAN),
            progression_type="constrained_hmm",
            progression_list=["Im9:8.0", "IVm9:4.0", "bVImaj9:4.0"],
            track_phrase_schedules={
                "Rhythm_Guitars":    _rest(16),
                "Lead_Tremolo":      _rest(16),
                "Double_Kick_Drums": _rest(16),
                "Doom_Brass":        _rest(16),
                "Metal_Bass":        _rest(16),
                # Choir: full 8-bar statement, then ghosted echo in same harmony
                "Epic_Choir": PhraseSchedule(slots=[
                    PhraseSlot(kind="play",  bars=8, label="choir_ballad"),
                    PhraseSlot(kind="ghost", bars=8, label="choir_ballad"),
                ], loop=False),
                # Violins: 4-bar phrases with breathing rests (wider than default)
                "Violins_Spiccato": _play_rest(4, 4, label="V_bal", loop=True),
            },
        ),
    ]

    # ---------------------------------------------------------------------------
    # Track 5: Ride of the Valkyries (D Dorian, 150 BPM)
    #
    # Full ensemble gallop. Lead Tremolo fires in 4-bar bursts separated by rests,
    # with a ghost repeat mid-track for a thrilling call-echo. Harpsichord sits out
    # the first half, then enters as a gothic decoration.
    # ---------------------------------------------------------------------------
    t5 = [
        IdeaPart(
            name="Gallop",
            bars=16,
            scale=Scale(2, Mode.DORIAN),
            progression_type="constrained_hmm",
            progression_list=["Im:8.0", "IVmaj9:4.0", "Im:4.0"],
            track_phrase_schedules={
                "Lead_Tremolo": PhraseSchedule(slots=[
                    PhraseSlot(kind="play",  bars=4, label="LT_gal"),
                    PhraseSlot(kind="rest",  bars=4),
                    PhraseSlot(kind="ghost", bars=4, label="LT_gal"),
                    PhraseSlot(kind="rest",  bars=4),
                ], loop=False),
                "Gothic_Harpsichord": PhraseSchedule(slots=[
                    PhraseSlot(kind="rest", bars=8),
                    PhraseSlot(kind="play", bars=4, label="GH_gal"),
                    PhraseSlot(kind="rest", bars=4),
                ], loop=False),
            },
        ),
    ]

    # ---------------------------------------------------------------------------
    # Track 6: Interlude — Whispers in the Dark (G Harmonic Minor, 70 BPM)
    #
    # Chamber texture — entire metal band and timpani silenced.
    # Harpsichord takes full ghosting presence. Woodwinds hold the full 8 bars.
    # ---------------------------------------------------------------------------
    t6 = [
        IdeaPart(
            name="Whispers",
            bars=8,
            scale=Scale(7, Mode.HARMONIC_MINOR),
            progression_type="constrained_hmm",
            progression_list=["Im9:4.0", "Vaug:4.0"],
            track_phrase_schedules={
                "Rhythm_Guitars":    _rest(8),
                "Lead_Tremolo":      _rest(8),
                "Double_Kick_Drums": _rest(8),
                "Timpani_Strikes":   _rest(8),
                "Metal_Bass":        _rest(8),
                # Harpsichord: plays the full first half, then ghosts it ethereally
                "Gothic_Harpsichord": PhraseSchedule(slots=[
                    PhraseSlot(kind="play",  bars=4, label="GH_whis"),
                    PhraseSlot(kind="ghost", bars=4, label="GH_whis"),
                ], loop=False),
                # Woodwinds: full 8-bar statement for maximum chamber presence
                "Woodwinds": _play(8, label="WW_whis"),
            },
        ),
    ]

    # ---------------------------------------------------------------------------
    # Track 7: Siege of the Iron Citadel (B Minor, 140 BPM)
    #
    # Assault: full metal storm — harpsichord silent. Woodwinds call in bars 1–8,
    # then rest as the assault intensifies.
    # Breach: harpsichord still silent. Woodwinds ghost the assault phrase under
    # the new altered-dominant harmony for thematic continuity.
    # ---------------------------------------------------------------------------
    t7 = [
        IdeaPart(
            name="Assault",
            bars=16,
            scale=Scale(11, Mode.NATURAL_MINOR),
            progression_type="constrained_hmm",
            progression_list=["Im:4.0", "bVImaj7:4.0", "IVm7:4.0", "V7:4.0"],
            track_phrase_schedules={
                "Gothic_Harpsichord": _rest(16),
                "Woodwinds": PhraseSchedule(slots=[
                    PhraseSlot(kind="play", bars=8, label="WW_assault"),
                    PhraseSlot(kind="rest", bars=8),
                ], loop=False),
            },
        ),
        IdeaPart(
            name="Breach",
            bars=8,
            scale=Scale(11, Mode.NATURAL_MINOR),
            progression_type="constrained_hmm",
            progression_list=["bVImaj9:4.0", "V7alt:4.0"],
            track_phrase_schedules={
                "Gothic_Harpsichord": _rest(8),
                # Woodwinds ghost the assault motif into the breach's altered harmony
                "Woodwinds": PhraseSchedule(slots=[
                    PhraseSlot(kind="ghost", bars=8, label="WW_assault"),
                ], loop=False),
            },
        ),
    ]

    # ---------------------------------------------------------------------------
    # Track 8: The Oracle's Prophecy (Eb Lydian, 95 BPM)
    #
    # Vision: starts as a pure orchestral prophecy. Metal band enters only at bar 9
    # for a cinematic build from ethereal to explosive. Choir delivers a 8-bar
    # revelation, then ghosts itself as the metal crashes in.
    # ---------------------------------------------------------------------------
    t8 = [
        IdeaPart(
            name="Vision",
            bars=16,
            scale=Scale(3, Mode.LYDIAN),
            progression_type="constrained_hmm",
            progression_list=["Imaj9:8.0", "IIadd9:4.0", "viidim:4.0"],
            track_phrase_schedules={
                # Metal enters hard at bar 9 — first 8 bars: pure orchestra
                "Rhythm_Guitars": PhraseSchedule(slots=[
                    PhraseSlot(kind="rest", bars=8),
                    PhraseSlot(kind="play", bars=8, label="RG_vision"),
                ], loop=False),
                "Lead_Tremolo": PhraseSchedule(slots=[
                    PhraseSlot(kind="rest", bars=8),
                    PhraseSlot(kind="play", bars=8, label="LT_vision"),
                ], loop=False),
                "Double_Kick_Drums": PhraseSchedule(slots=[
                    PhraseSlot(kind="rest", bars=8),
                    PhraseSlot(kind="play", bars=8, label="DK_vision"),
                ], loop=False),
                # Choir: 8-bar Lydian revelation, then ghosted echo under the metal
                "Epic_Choir": PhraseSchedule(slots=[
                    PhraseSlot(kind="play",  bars=8, label="choir_vision"),
                    PhraseSlot(kind="ghost", bars=8, label="choir_vision"),
                ], loop=False),
            },
        ),
    ]

    # ---------------------------------------------------------------------------
    # Track 9: Final Stand (E Harmonic Minor, 160 BPM)
    #
    # Pre_Battle: orchestra only — Rhythm Guitars and Kick silent. Doom Brass makes
    # a dramatic 4-bar statement then falls silent. Choir builds to a peak.
    # Apocalypse: everything unleashed at maximum force. Doom Brass ghosts the
    # battle motif before launching into relentless 16-bar gallop. Choir carries
    # thematic material through ghost + new climax + final echo.
    # ---------------------------------------------------------------------------
    t9 = [
        IdeaPart(
            name="Pre_Battle",
            bars=8,
            scale=Scale(4, Mode.HARMONIC_MINOR),
            progression_type="constrained_hmm",
            progression_list=["Im9:4.0", "V7:4.0"],
            track_phrase_schedules={
                "Rhythm_Guitars":    _rest(8),
                "Double_Kick_Drums": _rest(8),
                # Doom Brass: 4-bar dramatic declaration, then falls silent
                "Doom_Brass": PhraseSchedule(slots=[
                    PhraseSlot(kind="play", bars=4, label="DB_battle"),
                    PhraseSlot(kind="rest", bars=4),
                ], loop=False),
                # Choir: full 8-bar battle swell
                "Epic_Choir": _play(8, label="choir_battle"),
            },
        ),
        IdeaPart(
            name="Apocalypse",
            bars=24,
            scale=Scale(4, Mode.HARMONIC_MINOR),
            progression_type="constrained_hmm",
            progression_list=["Im:8.0", "bVImaj9:4.0", "Idim:4.0", "V7alt:8.0"],
            track_phrase_schedules={
                # Doom Brass: ghost the battle motif (bars 1–8), then full gallop
                "Doom_Brass": PhraseSchedule(slots=[
                    PhraseSlot(kind="ghost", bars=8,  label="DB_battle"),
                    PhraseSlot(kind="play",  bars=16, label="DB_apoc"),
                ], loop=False),
                # Choir: echoes battle cry → new climax → ghosted final echo
                "Epic_Choir": PhraseSchedule(slots=[
                    PhraseSlot(kind="ghost", bars=8, label="choir_battle"),
                    PhraseSlot(kind="play",  bars=8, label="choir_apoc"),
                    PhraseSlot(kind="ghost", bars=8, label="choir_apoc"),
                ], loop=False),
            },
        ),
    ]

    # ---------------------------------------------------------------------------
    # Track 10: Ashes to Ashes (C Ionian, 60 BPM)
    #
    # Requiem: full ensemble resolution — guitars silent for first 8 bars (grand
    # orchestral opening), then fade in for cathartic 8-bar conclusion.
    # Choir establishes "choir_req" motif and ghosts it.
    # Fade: metal, brass, and percussion stripped away completely. Choir ghosts
    # the requiem phrase as everything dissolves. Woodwinds hold the final note.
    # ---------------------------------------------------------------------------
    t10 = [
        IdeaPart(
            name="Requiem",
            bars=16,
            scale=Scale(0, Mode.MAJOR),
            progression_type="constrained_hmm",
            progression_list=["Imaj9:8.0", "IVadd9:4.0", "V7:4.0"],
            track_phrase_schedules={
                # Guitars enter only in the second half for cathartic resolution
                "Rhythm_Guitars": PhraseSchedule(slots=[
                    PhraseSlot(kind="rest", bars=8),
                    PhraseSlot(kind="play", bars=8, label="RG_req"),
                ], loop=False),
                "Lead_Tremolo": PhraseSchedule(slots=[
                    PhraseSlot(kind="rest", bars=8),
                    PhraseSlot(kind="play", bars=8, label="LT_req"),
                ], loop=False),
                # Choir: 8-bar resolution phrase, then ghosted for warmth
                "Epic_Choir": PhraseSchedule(slots=[
                    PhraseSlot(kind="play",  bars=8, label="choir_req"),
                    PhraseSlot(kind="ghost", bars=8, label="choir_req"),
                ], loop=False),
            },
        ),
        IdeaPart(
            name="Fade",
            bars=8,
            scale=Scale(0, Mode.MAJOR),
            progression_type="constrained_hmm",
            progression_list=["Iadd9:8.0"],
            track_phrase_schedules={
                "Rhythm_Guitars":    _rest(8),
                "Lead_Tremolo":      _rest(8),
                "Double_Kick_Drums": _rest(8),
                "Doom_Brass":        _rest(8),
                "Timpani_Strikes":   _rest(8),
                "Metal_Bass":        _rest(8),
                # Choir dissolves with the ghosted requiem motif
                "Epic_Choir": PhraseSchedule(slots=[
                    PhraseSlot(kind="ghost", bars=8, label="choir_req"),
                ], loop=False),
                # Woodwinds: final full statement as everything else fades
                "Woodwinds": _play(8, label="WW_fade"),
            },
        ),
    ]

    album_configs = [
        ("01_Overture",          85,  (4, 4), t1),
        ("02_Blood_On_Snow",    130,  (4, 4), t2),
        ("03_Clockwork_God",    110,  (5, 4), t3),
        ("04_Ballad_Fallen",     65,  (3, 4), t4),
        ("05_Valkyrie_Ride",    150,  (4, 4), t5),
        ("06_Whispers_Dark",     70,  (4, 4), t6),
        ("07_Iron_Citadel",     140,  (4, 4), t7),
        ("08_Oracles_Prophecy",  95,  (4, 4), t8),
        ("09_Final_Stand",      160,  (4, 4), t9),
        ("10_Ashes_to_Ashes",    60,  (4, 4), t10),
    ]

    for name, tempo, ts, parts in album_configs:
        print(f"\n--- Composing: {name} ({ts[0]}/{ts[1]}, {tempo} BPM) ---")

        tool_config = IdeaToolConfig(
            style="orchestral",
            parts=parts,
            tracks=hybrid_orchestra,
            use_tension_curve=True,
            use_voice_leading=True,
            tempo=tempo,
            time_signature=ts,
        )

        try:
            notes_dict = IdeaTool(tool_config).generate()
            tracks_data = {
                k: v for k, v in notes_dict.items()
                if not k.startswith("_") and isinstance(v, list)
            }

            filepath = out_dir / f"{name}.mid"
            instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in hybrid_orchestra}

            export_multitrack_midi(
                tracks_data,
                str(filepath),
                bpm=tempo,
                time_sig=ts,
                instruments=instruments_map,
            )
            print(f"    ✓ Exported {name}.mid")
        except Exception as e:
            print(f"    ✗ Error in {name}: {e}")

    print("\n================================================================================")
    print(f"  ALBUM COMPLETE. Output: {out_dir}")
    print("================================================================================")


if __name__ == "__main__":
    main()
