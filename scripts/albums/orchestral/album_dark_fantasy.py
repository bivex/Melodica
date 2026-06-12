"""
album_dark_fantasy.py — SHADOWS OF THE ANCIENT REALM

Dark fantasy orchestral album: fear, dread, dark beauty.
Five movements across haunting scales and textures.

    I.   The Cursed Gate        (D Phrygian Dominant, 72 BPM)  — dread, foreboding
    II.  Dance of the Wraiths  (B Hungarian Minor, 88 BPM)    — macabre elegance
    III. The Void Speaks       (F# Locrian, 58 BPM)           — terror, silence
    IV.  Lament of the Fallen  (A Harmonic Minor, 66 BPM)     — dark beauty, sorrow
    V.   Apotheosis of Shadow  (C# Double Harmonic, 96 BPM)   — epic darkness
"""

import random
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.orchestral_strings import (
    ViolinGenerator, ViolaGenerator, CelloGenerator, ContrabassGenerator,
)
from melodica.generators.orchestral_brass import (
    TrumpetGenerator, TromboneGenerator, FrenchHornGenerator,
)
from melodica.generators.orchestral_woodwinds import (
    FluteGenerator, OboeGenerator, ClarinetGenerator, BassoonGenerator,
)
from melodica.generators.orchestral_percussion import (
    TimpaniGenerator, MalletPercussionGenerator,
)
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.generators.tuba import TubaGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.horror_dissonance import HorrorDissonanceGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.fx_impact import FXImpactGenerator

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.midi import export_multitrack_midi
from melodica.form import MusicalForm, FormSection
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# ---------------------------------------------------------------------------
# Scales — dark fantasy palette
# ---------------------------------------------------------------------------
D_PHRYGIAN_DOM  = Scale(root=2,  mode=Mode.PHRYGIAN_DOMINANT)  # D Phrygian Dominant
B_HUNGARIAN     = Scale(root=11, mode=Mode.HUNGARIAN_MINOR)     # B Hungarian Minor
FS_LOCRIAN      = Scale(root=6,  mode=Mode.LOCRIAN)             # F# Locrian
A_HARMONIC      = Scale(root=9,  mode=Mode.HARMONIC_MINOR)      # A Harmonic Minor
CS_DOUBLE_HARM  = Scale(root=1,  mode=Mode.DOUBLE_HARMONIC)     # C# Double Harmonic

album_dir = Path("output/album_dark_fantasy")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_HARM = CoupledHMMHarmonizer(beam_width=14, chord_change="half")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _clamp(notes: list, lo: int, hi: int) -> list:
    for n in notes:
        n.velocity = max(lo, min(hi, int(n.velocity)))
    return notes

def _thin(notes: list, total: float, keep: float = 0.6,
          intro_end: float | None = None,
          outro_start: float | None = None) -> list:
    rng = random.Random(hash(str(total)) & 0xFFFF)
    ie = intro_end if intro_end is not None else total * 0.20
    os_ = outro_start if outro_start is not None else total * 0.80
    result = []
    for n in notes:
        if n.start < ie or n.start >= os_:
            if rng.random() < keep:
                result.append(n)
        else:
            result.append(n)
    return result

def _off(notes: list, offset: float) -> list:
    return [NoteInfo(pitch=n.pitch, start=n.start + offset,
                     duration=n.duration, velocity=n.velocity)
            for n in notes]

def _lead_melody(key: Scale, dur: float, lo: int = 60, hi: int = 84,
                 density: float = 0.45) -> list[NoteInfo]:
    p = GeneratorParams(density=density, key_range_low=lo, key_range_high=hi)
    gen = MelodyGenerator(p, phrase_length=8.0,
                          note_range_low=lo, note_range_high=hi,
                          register_smoothness=0.7, steps_probability=0.7,
                          motif_probability=0.6, phrase_contour="arch")
    guide = [ChordLabel(root=key.root, quality=key.parse_roman("I").quality,
                        start=0.0, duration=dur)]
    return gen.render(guide, key, dur)

def _harmonize(lead: list[NoteInfo], key: Scale, dur: float) -> list[ChordLabel]:
    return _HARM.harmonize(lead, key, duration_beats=dur)

def _pedal_tone(chords: list, key: Scale, dur: float,
                pitch: int = 21, note_dur: float = 4.0,
                velocity: int = 45) -> list[NoteInfo]:
    notes = []
    t = 0.0
    while t < dur:
        notes.append(NoteInfo(pitch=pitch, velocity=velocity,
                               start=t, duration=note_dur,
                               articulation="legato"))
        t += note_dur
    return notes

def _mix(raw: dict, bpm: float, lufs: float = -14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Lead":   0.82, "Melody": 0.82,
        "Violin": 0.78, "Viola":  0.74, "Cello":  0.76,
        "Strings": 0.76, "Choir":  0.80,
        "Horror": 0.65, "Nebula": 0.60, "Pad":    0.62,
        "Horns":  0.78, "Brass":  0.74, "Tuba":   0.80,
        "Trombone": 0.72, "Trumpet": 0.70,
        "Bassoon": 0.74, "Clarinet": 0.72, "Oboe": 0.70, "Flute": 0.72,
        "Harp":   0.80, "Glock":  0.72, "Marimba": 0.72,
        "Bass":   0.85, "Pedal":  0.78, "Ostinato": 0.74,
        "Timpani": 0.84, "Impact": 0.70,
        "Counter": 0.72,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def apply_pipeline(tracks: dict, bpm: float, form=None, key=None) -> dict:
    """Apply production pipeline: section dynamics, humanize, phrase dynamics,
    articulations, harmonic verify, density reshaping, cadential silence, V→I."""
    from melodica.composer.album_pipeline import _apply_humanization, _TrackProfile, Role
    from melodica.composer.phrase_dynamics import apply_phrase_dynamics_to_pipeline
    from melodica.composer.articulations import ArticulationEngine
    from melodica.composer.harmonic_verifier import verify_and_fix, VerifierConfig
    import statistics, random as _rng

    total_dur = max(
        (n.start + n.duration) for notes in tracks.values() for n in notes
        if notes
    ) if any(tracks.values()) else 64.0

    # Build profiles
    profiles: dict[str, _TrackProfile] = {}
    for tname, notes in tracks.items():
        tl = tname.lower()
        if any(x in tl for x in ("bass", "tuba", "pedal", "contrabass")):
            role = Role.BASS
        elif any(x in tl for x in ("lead", "melody", "trumpet", "flute", "oboe")):
            role = Role.LEAD
        elif any(x in tl for x in ("strings", "violin", "viola", "cello")):
            role = Role.STRINGS
        elif any(x in tl for x in ("choir",)):
            role = Role.CHOIR
        elif any(x in tl for x in ("timpani", "perc", "glock", "marimba", "impact")):
            role = Role.PERC
        else:
            role = Role.PAD
        if notes:
            pitches = [int(n.pitch) for n in notes]
            vels    = [int(n.velocity) for n in notes]
            avg_p   = statistics.mean(pitches)
            p_range = max(pitches) - min(pitches)
            rms_vel = statistics.mean(vels)
            density = len(notes) / max(total_dur, 1.0)
        else:
            avg_p, p_range, rms_vel, density = 48.0, 24.0, 60.0, 0.3
        profiles[tname] = _TrackProfile(
            avg_pitch=avg_p, pitch_range=p_range,
            density=density, rms_velocity=rms_vel, role=role,
        )

    # 0. Section dynamics scaling
    if form is not None:
        _DYN_RANGE = {
            "ppp": (18, 8),  "pp": (30, 10), "p": (45, 12),
            "mp":  (60, 12), "mf": (70, 12), "f": (86, 11),
            "ff":  (102, 10), "fff": (114, 7),
        }
        scaled: dict = {}
        for tname, notes in tracks.items():
            if not notes:
                scaled[tname] = notes
                continue
            new_notes = []
            for n in notes:
                sec = next(
                    (s for s in reversed(form.sections) if s.start_beat <= float(n.start)),
                    form.sections[0] if form.sections else None,
                )
                if sec is None:
                    new_notes.append(n)
                    continue
                mid, hw = _DYN_RANGE.get(sec.dynamics, (70, 12))
                lo, hi = mid - hw, mid + hw
                cur = float(n.velocity)
                target = mid + (cur - 75.0) * (hw / 35.0)
                target = max(lo, min(hi, target))
                new_vel = int(round(0.55 * target + 0.45 * cur))
                new_notes.append(n.__replace__(velocity=max(1, min(127, new_vel))))
            scaled[tname] = new_notes
        tracks = scaled

    # 1. Humanize
    tracks = _apply_humanization(tracks, profiles)

    # 2. Phrase dynamics
    tracks = apply_phrase_dynamics_to_pipeline(tracks)

    # 3. Articulations
    engine = ArticulationEngine()
    tracks = {
        tname: engine.apply(notes, instrument=tname.lower(), total_beats=total_dur)
        if notes else notes
        for tname, notes in tracks.items()
    }

    # 4. Harmonic verification
    config = VerifierConfig(
        dissonance_tolerance=0.55, fix_transpose=True,
        fix_remove=False, fix_velocity=True,
        fix_shorten=True, apply_shading=True,
    )
    tracks, _ = verify_and_fix(tracks, config)

    # 5. Density reshaping — push peak toward 65%
    _rng_inst = _rng.Random(77)
    peak_target = 0.65
    reshaped: dict = {}
    for tname, notes in tracks.items():
        tl = tname.lower()
        if any(x in tl for x in ("bass", "pedal", "tuba", "contrabass", "ostinato")):
            reshaped[tname] = notes
            continue
        kept = []
        for n in notes:
            pos = float(n.start) / max(total_dur, 1.0)
            if pos < peak_target * 0.5:
                if _rng_inst.random() < 0.50:
                    kept.append(n)
            elif pos < peak_target:
                t = (pos - peak_target * 0.5) / (peak_target * 0.5)
                if _rng_inst.random() < (0.50 + t * 0.50):
                    kept.append(n)
            else:
                kept.append(n)
        reshaped[tname] = kept if kept else notes
    tracks = reshaped

    # 6. Cadential silence at section boundaries
    if form is not None:
        gap = 1.5
        boundaries = {s.end_beat for s in form.sections if s.end_beat < total_dur - 0.5}
        silenced: dict = {}
        for tname, notes in tracks.items():
            tl = tname.lower()
            if any(x in tl for x in ("bass", "pedal", "tuba", "contrabass", "timpani")):
                silenced[tname] = notes
                continue
            silenced[tname] = [
                n for n in notes
                if not any((b - gap) <= float(n.start) < b for b in boundaries)
            ]
        tracks = silenced

    # 7. V→I cadence injection
    if key is not None:
        from melodica.types_pkg._notes import NoteInfo as _NI
        _cw = 8.0
        dom_root = (key.root + 7) % 12
        lead_t = next((t for t in tracks if "lead" in t.lower() or "melody" in t.lower()),
                      next((t for t in tracks), None))
        if lead_t and tracks.get(lead_t):
            ln = tracks[lead_t]
            cs = total_dur - _cw
            mid = total_dur - _cw / 2.0
            late = [(float(n.start), int(n.pitch) % 12) for n in ln if float(n.start) >= cs]
            f_pcs = {pc for t, pc in late if t < mid}
            s_pcs = {pc for t, pc in late if t >= mid}
            ok = any(
                ((tp + 7) % 12 in f_pcs or (tp + 11) % 12 in f_pcs) and tp in s_pcs
                for tp in range(12)
            )
            if not ok:
                bv = 72
                dp = 48 + dom_root
                tp_p = 48 + key.root
                tracks[lead_t] = ln + [
                    _NI(pitch=dp,     velocity=bv,     start=cs,       duration=1.5, articulation="legato"),
                    _NI(pitch=dp + 4, velocity=bv - 5, start=cs + 0.5, duration=1.0, articulation="legato"),
                    _NI(pitch=dp + 7, velocity=bv - 8, start=cs + 1.0, duration=1.0, articulation="legato"),
                    _NI(pitch=tp_p,   velocity=bv + 8, start=mid,      duration=3.0, articulation="legato"),
                    _NI(pitch=tp_p+7, velocity=bv + 4, start=mid,      duration=3.0, articulation="legato"),
                ]

    return tracks


# ===========================================================================
# I. The Cursed Gate — D Phrygian Dominant, 72 BPM
#    Foreboding, heavy, gate of doom. Ostinato bass, horror cluster textures,
#    haunting oboe melody, brass fanfare of doom.
# ===========================================================================
def track_01_cursed_gate():
    print("  I. The Cursed Gate")
    bpm, dur = 72.0, 112.0
    key = D_PHRYGIAN_DOM

    lead = _lead_melody(key, dur, lo=62, hi=82, density=0.38)
    chords = _harmonize(lead, key, dur)

    # Haunting oboe melody — solo protagonist
    oboe = _clamp(OboeGenerator(
        GeneratorParams(density=0.38, key_range_low=62, key_range_high=82),
        articulation="legato").render(chords, key, dur), 48, 88)

    # Bassoon counter-voice — dark and heavy
    bassoon = _clamp(BassoonGenerator(
        GeneratorParams(density=0.30, key_range_low=45, key_range_high=64),
        articulation="legato").render(chords, key, dur), 45, 80)

    # Horror dissonance texture — fear/dread layer
    horror = _clamp(_thin(HorrorDissonanceGenerator(
        GeneratorParams(density=0.25, key_range_low=48, key_range_high=72),
        variant="psychological", dissonance_level=0.85).render(chords, key, dur),
        dur, 0.55), 30, 65)

    # Nebula pad — slow swelling darkness
    nebula = _clamp(NebulaGenerator(
        GeneratorParams(density=0.20, key_range_low=36, key_range_high=60),
        variant="swell").render(chords, key, dur), 25, 58)

    # Strings — heavy, slow tremolo
    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.40, key_range_low=48, key_range_high=66),
        dynamic_shape="cresc_dim").render(chords, key, dur),
        35, 78), dur, 0.7)

    # Choir — distant, ominous aah
    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.25, key_range_low=52, key_range_high=69),
        syllable="aah", dynamics="mp").render(chords, key, dur - 16.0),
        dur - 16.0, 0.55), dur - 16.0)
    choir = _off(choir, 16.0)

    # Horns — low, brooding
    horns = _thin(_clamp(FrenchHornGenerator(
        GeneratorParams(density=0.28, key_range_low=43, key_range_high=60),
        articulation="legato").render(chords, key, dur - 24.0), 40, 75),
        dur - 24.0, 0.65)
    horns = _off(horns, 24.0)

    # Tuba — deep rumble
    tuba = _clamp(TubaGenerator(
        GeneratorParams(density=0.30, key_range_low=24, key_range_high=40),
        articulation="legato").render(chords, key, dur), 45, 72)

    # Ostinato — relentless dread pulse
    ostinato = _clamp(OstinatoGenerator(
        GeneratorParams(density=0.85, key_range_low=26, key_range_high=38),
        pattern=[1, 1, 5, 1],
        accent_pattern=[1.3, 0.8, 1.0, 0.9]).render(chords, key, dur), 42, 70)

    # Timpani — doom strikes
    timp = _thin(_clamp(TimpaniGenerator(
        GeneratorParams(density=0.30, key_range_low=36, key_range_high=45),
        stroke_pattern="roll").render(chords, key, dur - 8.0), 50, 95),
        dur - 8.0, 0.6)
    timp = _off(timp, 8.0)

    # Bass
    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.82, key_range_low=24, key_range_high=38),
        articulation="legato").render(chords, key, dur), 42, 72)
    pedal = _pedal_tone(chords, key, dur, pitch=26, note_dur=4.0, velocity=48)

    form = MusicalForm.through_composed(key, dur, base_bpm=bpm)

    return {
        "Lead": _clamp(lead, 45, 85), "Oboe": oboe, "Bassoon": bassoon,
        "Horror": horror, "Nebula": nebula,
        "Strings": strings, "Choir": choir, "Horns": horns,
        "Tuba": tuba, "Ostinato": ostinato, "Timpani": timp,
        "Bass": bass, "Pedal": pedal,
    }, bpm, form


# ===========================================================================
# II. Dance of the Wraiths — B Hungarian Minor, 88 BPM
#    Macabre elegance — wraiths waltzing in moonlight.
#    Violin solo, pizzicato strings, harpsichord-like harp.
# ===========================================================================
def track_02_dance_of_wraiths():
    print("  II. Dance of the Wraiths")
    bpm, dur = 88.0, 96.0
    key = B_HUNGARIAN

    lead = _lead_melody(key, dur, lo=64, hi=86, density=0.50)
    chords = _harmonize(lead, key, dur)

    # Violin solo — eerie, beautiful
    violin = _clamp(ViolinGenerator(
        GeneratorParams(density=0.55, key_range_low=64, key_range_high=88),
        articulation="legato").render(chords, key, dur), 50, 92)

    # Viola — dark middle voice
    viola = _clamp(ViolaGenerator(
        GeneratorParams(density=0.40, key_range_low=55, key_range_high=72),
        articulation="pizzicato").render(chords, key, dur), 40, 78)

    # Cello — countermelody
    cello = _clamp(CelloGenerator(
        GeneratorParams(density=0.38, key_range_low=45, key_range_high=62),
        articulation="legato").render(chords, key, dur), 38, 76)

    # Strings — pizzicato pulse — ghostly dance rhythm
    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.55, key_range_low=50, key_range_high=66),
        dynamic_shape="flat").render(chords, key, dur),
        40, 72), dur, 0.75)

    # Harp — harpsichord-like plucks
    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.45, key_range_low=55, key_range_high=76),
        pattern="arpeggio").render(chords, key, dur), 38, 72), dur, 0.7)

    # Flute — high ghostly wisps
    flute = _thin(_clamp(FluteGenerator(
        GeneratorParams(density=0.28, key_range_low=74, key_range_high=92),
        articulation="staccato").render(chords, key, dur - 8.0), 35, 72),
        dur - 8.0, 0.45)
    flute = _off(flute, 8.0)

    # Horror dissonance — lurking beneath
    horror = _clamp(_thin(HorrorDissonanceGenerator(
        GeneratorParams(density=0.15, key_range_low=44, key_range_high=62),
        variant="psychological", dissonance_level=0.45).render(chords, key, dur),
        dur, 0.35), 22, 50)

    # Choir — distant wordless voices
    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.20, key_range_low=54, key_range_high=68),
        syllable="aah", dynamics="p").render(chords, key, dur - 20.0),
        dur - 20.0, 0.45), dur - 20.0)
    choir = _off(choir, 20.0)

    # Bass + pedal
    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.78, key_range_low=26, key_range_high=40),
        articulation="pizzicato").render(chords, key, dur), 40, 68)
    pedal = _pedal_tone(chords, key, dur, pitch=23, note_dur=2.0, velocity=40)

    form = MusicalForm.ternary(key, dur, base_bpm=bpm)

    return {
        "Lead": _clamp(lead, 48, 88), "Violin": violin, "Viola": viola,
        "Cello": cello, "Strings": strings, "Harp": harp,
        "Flute": flute, "Horror": horror, "Choir": choir,
        "Bass": bass, "Pedal": pedal,
    }, bpm, form


# ===========================================================================
# III. The Void Speaks — F# Locrian, 58 BPM
#    Pure terror. Sparse, dissonant, unpredictable silences.
#    The emptiness between notes IS the music.
# ===========================================================================
def track_03_void_speaks():
    print("  III. The Void Speaks")
    bpm, dur = 58.0, 100.0
    key = FS_LOCRIAN

    lead = _lead_melody(key, dur, lo=58, hi=80, density=0.28)
    chords = _harmonize(lead, key, dur)

    # Solo clarinet — fragile, terrified
    clarinet = _thin(_clamp(ClarinetGenerator(
        GeneratorParams(density=0.28, key_range_low=58, key_range_high=80),
        articulation="legato").render(chords, key, dur), 42, 82), dur, 0.60)

    # Horror dissonance — the void
    horror = _clamp(HorrorDissonanceGenerator(
        GeneratorParams(density=0.30, key_range_low=42, key_range_high=70),
        variant="psychological", dissonance_level=0.95).render(chords, key, dur), 28, 62)

    # Nebula — slow terror clouds
    nebula = _clamp(NebulaGenerator(
        GeneratorParams(density=0.18, key_range_low=30, key_range_high=56),
        variant="cloud").render(chords, key, dur), 20, 52)

    # Strings — col legno extended technique approximation
    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.25, key_range_low=46, key_range_high=62),
        dynamic_shape="cresc_dim").render(chords, key, dur),
        25, 58), dur, keep=0.40)

    # Trombone — low growl
    trombone = _thin(_clamp(TromboneGenerator(
        GeneratorParams(density=0.18, key_range_low=36, key_range_high=52),
        articulation="legato").render(chords, key, dur - 16.0), 35, 68),
        dur - 16.0, 0.50)
    trombone = _off(trombone, 16.0)

    # Ambient pad — underlying dread
    pad = _thin(_clamp(AmbientPadGenerator(
        GeneratorParams(density=0.22, key_range_low=32, key_range_high=55),
        ).render(chords, key, dur), 18, 48), dur, 0.55)

    # Harp — isolated plucks like drops of water in darkness
    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.18, key_range_low=48, key_range_high=70),
        pattern="arpeggio").render(chords, key, dur), 30, 65), dur, 0.30)

    # Bass — subterranean rumble
    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.65, key_range_low=22, key_range_high=36),
        articulation="legato").render(chords, key, dur), 38, 62)
    pedal = _pedal_tone(chords, key, dur, pitch=18, note_dur=8.0, velocity=40)

    form = MusicalForm.through_composed(key, dur, base_bpm=bpm)

    return {
        "Lead": _clamp(lead, 40, 78), "Clarinet": clarinet,
        "Horror": horror, "Nebula": nebula,
        "Strings": strings, "Trombone": trombone,
        "Pad": pad, "Harp": harp,
        "Bass": bass, "Pedal": pedal,
    }, bpm, form


# ===========================================================================
# IV. Lament of the Fallen — A Harmonic Minor, 66 BPM
#    Dark beauty. A fallen hero remembered. Most melodically beautiful track.
#    Cello solo over string choir, harp, distant choir.
# ===========================================================================
def track_04_lament():
    print("  IV. Lament of the Fallen")
    bpm, dur = 66.0, 108.0
    key = A_HARMONIC

    lead = _lead_melody(key, dur, lo=55, hi=79, density=0.45)
    chords = _harmonize(lead, key, dur)

    # Cello solo — the most beautiful dark melody
    cello = _clamp(CelloGenerator(
        GeneratorParams(density=0.48, key_range_low=48, key_range_high=72),
        articulation="legato").render(chords, key, dur), 50, 90)

    # Violin — tender answer to cello
    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.38, key_range_low=67, key_range_high=86),
        articulation="legato").render(chords, key, dur - 12.0), 42, 82),
        dur - 12.0, keep=0.65)
    violin = _off(violin, 12.0)

    # Strings — full sorrow
    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.42, key_range_low=50, key_range_high=66),
        dynamic_shape="cresc_dim").render(chords, key, dur),
        35, 78), dur, 0.70)

    # Choir — wordless lament
    choir = _thin(_clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.30, key_range_low=52, key_range_high=68),
        syllable="aah", dynamics="mf").render(chords, key, dur - 8.0),
        dur - 8.0, 0.60), dur - 8.0)
    choir = _off(choir, 8.0)

    # Harp — delicate tears
    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.35, key_range_low=55, key_range_high=79),
        pattern="arpeggio").render(chords, key, dur), 32, 68), dur, 0.65)

    # Oboe — distant, plaintive
    oboe = _thin(_clamp(OboeGenerator(
        GeneratorParams(density=0.28, key_range_low=60, key_range_high=78),
        articulation="legato").render(chords, key, dur - 20.0), 38, 72),
        dur - 20.0, 0.55)
    oboe = _off(oboe, 20.0)

    # Horns — far away, mournful
    horns = _thin(_clamp(FrenchHornGenerator(
        GeneratorParams(density=0.22, key_range_low=45, key_range_high=59),
        articulation="legato").render(chords, key, dur - 32.0), 35, 65),
        dur - 32.0, 0.50)
    horns = _off(horns, 32.0)

    # Nebula — ethereal mourning
    nebula = _thin(_clamp(NebulaGenerator(
        GeneratorParams(density=0.18, key_range_low=40, key_range_high=60),
        variant="swell").render(chords, key, dur), 20, 50), dur, 0.50)

    # Bass + pedal
    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.72, key_range_low=24, key_range_high=38),
        articulation="legato").render(chords, key, dur), 38, 65)
    pedal = _pedal_tone(chords, key, dur, pitch=21, note_dur=4.0, velocity=42)

    form = MusicalForm.sonata(key, dur, base_bpm=bpm)

    return {
        "Lead": _clamp(lead, 45, 85), "Cello": cello, "Violin": violin,
        "Strings": strings, "Choir": choir, "Harp": harp,
        "Oboe": oboe, "Horns": horns, "Nebula": nebula,
        "Bass": bass, "Pedal": pedal,
    }, bpm, form


# ===========================================================================
# V. Apotheosis of Shadow — C# Double Harmonic, 96 BPM
#    Epic, triumphant darkness. The shadow rises to godhood.
#    Full orchestra, massive brass, choir, relentless drive.
# ===========================================================================
def track_05_apotheosis():
    print("  V. Apotheosis of Shadow")
    bpm, dur = 96.0, 120.0
    key = CS_DOUBLE_HARM

    lead = _lead_melody(key, dur, lo=60, hi=84, density=0.52)
    chords = _harmonize(lead, key, dur)

    # Violin — soaring dark melody
    violin = _clamp(ViolinGenerator(
        GeneratorParams(density=0.55, key_range_low=66, key_range_high=88),
        articulation="legato").render(chords, key, dur), 48, 92)

    # Strings — full power
    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.50, key_range_low=50, key_range_high=66),
        dynamic_shape="cresc_dim").render(chords, key, dur),
        40, 85), dur, 0.75)

    # Choir — triumphant darkness
    choir = _clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.40, key_range_low=52, key_range_high=70),
        syllable="aah", dynamics="f").render(chords, key, dur - 12.0), 45, 90)
    choir = _off(choir, 12.0)

    # Brass section — apocalyptic fanfare
    brass = _thin(_clamp(BrassSectionGenerator(
        GeneratorParams(density=0.42, key_range_low=52, key_range_high=74),
        ensemble_mode="full").render(chords, key, dur - 24.0), 55, 100),
        dur - 24.0, 0.70)
    brass = _off(brass, 24.0)

    # Horns — dark heroic
    horns = _clamp(FrenchHornGenerator(
        GeneratorParams(density=0.38, key_range_low=46, key_range_high=62),
        articulation="legato").render(chords, key, dur - 16.0), 42, 82)
    horns = _off(horns, 16.0)

    # Tuba — foundation of darkness
    tuba = _clamp(TubaGenerator(
        GeneratorParams(density=0.35, key_range_low=24, key_range_high=40),
        articulation="legato").render(chords, key, dur), 45, 75)

    # Ostinato — relentless driving force
    ostinato = _clamp(OstinatoGenerator(
        GeneratorParams(density=0.90, key_range_low=28, key_range_high=42),
        pattern=[1, 5, 1, 3],
        accent_pattern=[1.4, 0.8, 1.1, 0.9]).render(chords, key, dur), 45, 75)

    # Horror dissonance — the shadow's presence
    horror = _thin(_clamp(HorrorDissonanceGenerator(
        GeneratorParams(density=0.22, key_range_low=44, key_range_high=66),
        variant="psychological", dissonance_level=0.7).render(chords, key, dur),
        dur, 0.40), 25, 55)

    # Timpani — thunderous
    timp = _clamp(TimpaniGenerator(
        GeneratorParams(density=0.45, key_range_low=37, key_range_high=48),
        stroke_pattern="roll").render(chords, key, dur - 8.0), 55, 100)
    timp = _off(timp, 8.0)

    # Harp — dramatic glissandos
    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.30, key_range_low=50, key_range_high=76),
        pattern="arpeggio").render(chords, key, dur), 35, 72), dur, keep=0.60)

    # Bass + pedal
    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.88, key_range_low=24, key_range_high=40),
        articulation="legato").render(chords, key, dur), 48, 80)
    pedal = _pedal_tone(chords, key, dur, pitch=25, note_dur=2.0, velocity=52)

    form = MusicalForm.ternary(key, dur, base_bpm=bpm)

    return {
        "Lead": _clamp(lead, 48, 90), "Violin": violin, "Strings": strings,
        "Choir": choir, "Brass": brass, "Horns": horns,
        "Tuba": tuba, "Ostinato": ostinato, "Horror": horror,
        "Timpani": timp, "Harp": harp,
        "Bass": bass, "Pedal": pedal,
    }, bpm, form


# ---------------------------------------------------------------------------
# GM program maps
# ---------------------------------------------------------------------------
TRACKS = [
    (track_01_cursed_gate, "01_The_Cursed_Gate.mid", {
        "Lead": 68, "Oboe": 68, "Bassoon": 70,
        "Horror": 49, "Nebula": 89,
        "Strings": 48, "Choir": 52, "Horns": 60,
        "Tuba": 58, "Ostinato": 44, "Timpani": 47,
        "Bass": 43, "Pedal": 43,
    }, D_PHRYGIAN_DOM),
    (track_02_dance_of_wraiths, "02_Dance_of_the_Wraiths.mid", {
        "Lead": 40, "Violin": 40, "Viola": 41, "Cello": 42,
        "Strings": 48, "Harp": 46,
        "Flute": 73, "Horror": 49, "Choir": 52,
        "Bass": 43, "Pedal": 43,
    }, B_HUNGARIAN),
    (track_03_void_speaks, "03_The_Void_Speaks.mid", {
        "Lead": 71, "Clarinet": 71,
        "Horror": 49, "Nebula": 89,
        "Strings": 48, "Trombone": 57,
        "Pad": 88, "Harp": 46,
        "Bass": 43, "Pedal": 43,
    }, FS_LOCRIAN),
    (track_04_lament, "04_Lament_of_the_Fallen.mid", {
        "Lead": 42, "Cello": 42, "Violin": 40,
        "Strings": 48, "Choir": 52, "Harp": 46,
        "Oboe": 68, "Horns": 60, "Nebula": 89,
        "Bass": 43, "Pedal": 43,
    }, A_HARMONIC),
    (track_05_apotheosis, "05_Apotheosis_of_Shadow.mid", {
        "Lead": 40, "Violin": 40, "Strings": 48,
        "Choir": 52, "Brass": 61, "Horns": 60,
        "Tuba": 58, "Ostinato": 44, "Horror": 49,
        "Timpani": 47, "Harp": 46,
        "Bass": 43, "Pedal": 43,
    }, CS_DOUBLE_HARM),
]


def main():
    album_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("  S H A D O W S   O F   T H E   A N C I E N T   R E A L M")
    print("=" * 78)

    total_notes = 0
    for producer, filename, instruments, track_key in TRACKS:
        print("-" * 78)
        raw, bpm, form = producer()
        raw = apply_pipeline(raw, bpm, form=form, key=track_key)
        mastered, pan = _mix(raw, bpm)
        export_multitrack_midi(
            mastered,
            str(album_dir / filename),
            bpm=bpm,
            cc_events=pan,
            instruments=instruments,
            reaper_project=True,
            form=form,
        )
        nc = sum(len(n) for n in raw.values())
        total_notes += nc
        print(f"    -> {filename}  ({nc} notes, {bpm:.0f} BPM)")

    print()
    print("=" * 78)
    print(f"  COMPLETE: SHADOWS — {total_notes} notes across 5 movements")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
