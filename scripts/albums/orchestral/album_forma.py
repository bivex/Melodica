# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_forma.py — FORMA: FIVE STUDIES IN CLASSICAL ARCHITECTURE

Demonstrates P4+P5 features: FormTemplate, SonataFormPlan, CanonGenerator,
AntiphonySectionBuilder, ChordVoicingLayout, VariationPlan, melodic_transforms.

    I.   Sonata Appassionata  (G Minor, 108 BPM)  — SonataFormPlan P/T/S/C zones
    II.  Canon Perpetuus      (D Major, 84 BPM)   — CanonGenerator at the fifth
    III. Rondo Brillante      (Bb Major, 120 BPM) — FormTemplate.RONDO, antiphony
    IV.  Theme & Variations   (E Minor, 72 BPM)   — VariationPlan, melodic_transforms
    V.   Arch of Eternity     (C Major, 96 BPM)   — FormTemplate.ARCH, chord voicing
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
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.canon import CanonGenerator, canon_at_fifth
from melodica.generators.chromatic_percussion import GlockenspielGenerator
from melodica.generators.tuba import TubaGenerator
from melodica.generators.pedal_bass import PedalBassGenerator

from melodica.composer.form_template import FormTemplate, form_plan
from melodica.composer.sonata_plan import SonataFormPlan
from melodica.composer.variation_plan import VariationPlan
from melodica.composer.antiphony import AntiphonyBuilder, InstrumentGroup
from melodica.composer.chord_voicing import ChordVoicingLayout, voice_chord
from melodica.composer.melodic_transforms import (
    inversion, retrograde, augmentation, diatonic_transposition,
)

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer, HMMConfig
from melodica.midi import export_multitrack_midi
from melodica.form import MusicalForm
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

random.seed(2027)

# ---------------------------------------------------------------------------
# Scales
# ---------------------------------------------------------------------------
G_MINOR  = Scale(root=7,  mode=Mode.NATURAL_MINOR)
D_MAJOR  = Scale(root=2,  mode=Mode.MAJOR)
BB_MAJOR = Scale(root=10, mode=Mode.MAJOR)
E_MINOR  = Scale(root=4,  mode=Mode.NATURAL_MINOR)
C_MAJOR  = Scale(root=0,  mode=Mode.MAJOR)

_HARM = CoupledHMMHarmonizer(beam_width=14, chord_change="half")


# ---------------------------------------------------------------------------
# Shared utilities (same pattern as album_virtuoso)
# ---------------------------------------------------------------------------

def _harmonize(melody: list[NoteInfo], scale: Scale, dur: float) -> list[ChordLabel]:
    return _HARM.harmonize(melody, scale, duration_beats=dur)


def _lead_melody(scale: Scale, dur: float, *, lo: int, hi: int,
                 density: float, seed_off: int = 0) -> list[NoteInfo]:
    p = GeneratorParams(density=density, velocity_range=(60, 100),
                        key_range_low=lo, key_range_high=hi)
    gen = MelodyGenerator(p, phrase_length=8.0,
                          note_range_low=lo, note_range_high=hi,
                          register_smoothness=0.7, steps_probability=0.7,
                          motif_probability=0.6, phrase_contour="arch")
    guide = [ChordLabel(root=scale.root, quality=scale.parse_roman("I").quality,
                        start=0.0, duration=dur)]
    return gen.render(guide, scale, dur)


def _clamp(notes: list[NoteInfo], lo: int = 1, hi: int = 127) -> list[NoteInfo]:
    for n in notes:
        n.velocity = max(lo, min(hi, int(n.velocity)))
    return notes


def _off(notes: list[NoteInfo], offset: float) -> list[NoteInfo]:
    return [NoteInfo(pitch=n.pitch, start=n.start + offset,
                     duration=n.duration, velocity=n.velocity)
            for n in notes]


def _thin(notes: list[NoteInfo], dur: float, *,
          intro_end: float | None = None,
          outro_start: float | None = None,
          keep: float = 0.25) -> list[NoteInfo]:
    rng = random.Random(42)
    intro_end    = intro_end    if intro_end    is not None else dur * 0.20
    outro_start  = outro_start  if outro_start  is not None else dur * 0.80
    result = []
    for n in notes:
        if n.start < intro_end or n.start >= outro_start:
            if rng.random() < keep:
                result.append(n)
        else:
            result.append(n)
    return result


def _pedal_tone(chords: list[ChordLabel], scale: Scale, dur: float, *,
                pitch: int, note_dur: float = 4.0, velocity: int = 52) -> list[NoteInfo]:
    notes = []
    t = 0.0
    while t < dur:
        actual_dur = min(note_dur, dur - t)
        notes.append(NoteInfo(pitch=pitch, start=t, duration=actual_dur, velocity=velocity))
        t += note_dur
    return notes


def _vel_scale(notes: list[NoteInfo], lo: int, hi: int) -> list[NoteInfo]:
    """Re-scale velocities to [lo, hi] range for dynamics-per-section effect."""
    if not notes:
        return notes
    vels = [n.velocity for n in notes]
    v_min, v_max = min(vels), max(vels)
    span = max(v_max - v_min, 1)
    target_span = hi - lo
    for n in notes:
        n.velocity = lo + int((n.velocity - v_min) / span * target_span)
    return notes


def _mix(raw: dict, bpm: float, lufs: float = -14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Lead": 0.84, "Lead2": 0.80, "Violin1": 0.82, "Violin2": 0.78,
        "Viola": 0.76, "Cello": 0.80, "Bass": 0.84, "Pedal": 0.80,
        "Brass": 0.78, "Horns": 0.80, "Trumpet": 0.76, "Trombone": 0.74,
        "Tuba": 0.84, "Woodwinds": 0.76, "Flute": 0.74, "Oboe": 0.74,
        "Clarinet": 0.76, "Bassoon": 0.78, "Choir": 0.80, "Harp": 0.82,
        "Timpani": 0.84, "Glock": 0.74, "Ostinato": 0.76, "Counter": 0.74,
        "Canon": 0.76, "Strings": 0.78, "Theme": 0.84, "Var1": 0.80,
        "Var2": 0.78, "Var3": 0.76, "Var4": 0.74, "CallGroup": 0.82,
        "ResponseGroup": 0.76,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def apply_pipeline(
    tracks: dict,
    bpm: float,
    chords: list | None = None,
    key=None,
    section_breaks: list | None = None,
    form=None,
) -> dict:
    """Apply production pipeline stages to a raw tracks dict.

    Runs the subset of DEFAULT_PIPELINE stages that operate purely on
    tracks/chords/key — skipping mixing/mastering/export which are handled
    separately by _mix() and export_multitrack_midi().\n
    Stages applied (in order):
      section_dynamics  — scale velocity per note to match FormSection.dynamics
      humanize          — per-instrument micro-timing + velocity scatter
      phrase_dynamics   — per-phrase crescendo/diminuendo arch
      articulations     — articulation string → CC11/CC1/CC64 + duration shaping
      non_chord_tones   — passing/neighbour tones on LEAD+STRINGS tracks
      tension           — global tension boost/duck based on chord complexity
      texture           — density automation via TensionCurve
      transitions       — CC11 expression sweeps at section boundaries
      harmonic_verify   — detect & fix m2/tritone clashes across tracks
    """
    from melodica.composer.album_pipeline import (
        _apply_humanization,
        _TrackProfile,
        Role,
    )
    from melodica.composer.phrase_dynamics import apply_phrase_dynamics_to_pipeline
    from melodica.composer.articulations import ArticulationEngine
    from melodica.composer.harmonic_verifier import verify_and_fix, VerifierConfig
    import statistics

    # Compute total duration first — needed for density in profiles
    total_dur = max(
        (n.start + n.duration) for notes in tracks.values() for n in notes
        if notes
    ) if any(tracks.values()) else 64.0

    # Build _TrackProfile from actual note data so humanization works correctly
    profiles: dict[str, _TrackProfile] = {}
    for tname, notes in tracks.items():
        tl = tname.lower()
        if any(x in tl for x in ("bass", "tuba", "pedal", "contrabass")):
            role = Role.BASS
        elif any(x in tl for x in ("lead", "melody", "theme", "trumpet", "flute", "oboe")):
            role = Role.LEAD
        elif any(x in tl for x in ("strings", "violin", "viola", "cello")):
            role = Role.STRINGS
        elif any(x in tl for x in ("choir",)):
            role = Role.CHOIR
        elif any(x in tl for x in ("timpani", "perc", "glock")):
            role = Role.PERC
        elif any(x in tl for x in ("brass", "horn", "trombone")):
            role = Role.PAD
        else:
            role = Role.PAD
        if notes:
            pitches = [int(n.pitch) for n in notes]
            vels = [int(n.velocity) for n in notes]
            avg_p = statistics.mean(pitches)
            p_range = max(pitches) - min(pitches)
            rms_vel = statistics.mean(vels)
            density = len(notes) / max(total_dur, 1.0)
        else:
            avg_p, p_range, rms_vel, density = 60.0, 24.0, 80.0, 0.5
        profiles[tname] = _TrackProfile(
            avg_pitch=avg_p,
            pitch_range=p_range,
            density=density,
            rms_velocity=rms_vel,
            role=role,
        )

    # 0. Section dynamics — scale velocity per note to match FormSection.dynamics
    if form is not None:
        # dynamics string → target velocity range (mid, half-width)
        _DYN_RANGE = {
            "ppp": (20, 10), "pp": (32, 12), "p": (47, 13),
            "mp": (62, 13), "mf": (72, 13), "f":  (88, 12),
            "ff": (104, 11), "fff": (116, 8),
        }
        scaled: dict = {}
        for tname, notes in tracks.items():
            if not notes:
                scaled[tname] = notes
                continue
            new_notes = []
            for n in notes:
                beat = float(n.start)
                sec = next(
                    (s for s in reversed(form.sections) if s.start_beat <= beat),
                    form.sections[0] if form.sections else None,
                )
                if sec is None:
                    new_notes.append(n)
                    continue
                mid, hw = _DYN_RANGE.get(sec.dynamics, (72, 13))
                lo, hi = mid - hw, mid + hw
                # Scale current velocity into target range preserving relative shape
                cur = float(n.velocity)
                # Soft scaling: blend 60% toward target mid, keep 40% original shape
                target = mid + (cur - 80.0) * (hw / 35.0)
                target = max(lo, min(hi, target))
                new_vel = int(round(0.55 * target + 0.45 * cur))
                new_vel = max(1, min(127, new_vel))
                new_notes.append(n.__replace__(velocity=new_vel))
            scaled[tname] = new_notes
        tracks = scaled

    # 1. Humanize
    tracks = _apply_humanization(tracks, profiles)

    # 2. Phrase dynamics
    tracks = apply_phrase_dynamics_to_pipeline(tracks)

    # 3. Articulations — per-instrument CC shaping
    engine = ArticulationEngine()
    tracks = {
        tname: engine.apply(notes, instrument=tname.lower(), total_beats=total_dur)
        if notes else notes
        for tname, notes in tracks.items()
    }

    # 4. Non-chord tones on melodic tracks
    if chords and key:
        from melodica.composer.non_chord_tones import NonChordToneGenerator
        gen = NonChordToneGenerator(
            passing_prob=0.18, neighbor_prob=0.08,
            suspension_prob=0.06, anticipation_prob=0.04,
        )
        tracks = {
            tname: gen.add_non_chord_tones(notes, chords, key)
            if profiles.get(tname) and profiles[tname].role in (Role.LEAD, Role.STRINGS) and notes
            else notes
            for tname, notes in tracks.items()
        }

    # 5. Texture automation
    if chords:
        try:
            from melodica.composer.texture_controller import TextureController
            from melodica.composer.tension_curve import TensionCurve
            tc = TensionCurve(
                total_beats=total_dur, curve_type="classical",
                peak_position=0.65, peak_intensity=0.9, resolution_length=0.25,
            )
            ctrl = TextureController(tension_curve=tc)
            tracks = ctrl.apply_texture(tracks, total_dur)
        except Exception:
            pass

    # 6. Transition sweeps at section boundaries (no-op if none provided)
    if section_breaks:
        try:
            from melodica.composer.transition_coordinator import TransitionCoordinator
            cc_dummy: dict = {}
            non_bass = [t for t in tracks if "bass" not in t.lower()]
            for beat, _label in section_breaks:
                TransitionCoordinator.apply_sweeps(
                    tracks, cc_dummy, target_tracks=non_bass,
                    cc_num=11, start_val=100, end_val=60,
                    start_beat=max(0.0, beat - 2.0), end_beat=beat,
                    curve_type="exponential", steps=12,
                )
                TransitionCoordinator.apply_sweeps(
                    tracks, cc_dummy, target_tracks=non_bass,
                    cc_num=11, start_val=60, end_val=100,
                    start_beat=beat, end_beat=beat + 2.0,
                    curve_type="exponential", steps=12,
                )
        except Exception:
            pass

    # 7. Harmonic verification — fix clashes
    config = VerifierConfig(
        dissonance_tolerance=0.6, fix_transpose=True,
        fix_remove=False, fix_velocity=True,
        fix_shorten=True, apply_shading=True,
    )
    tracks, _ = verify_and_fix(tracks, config)

    return tracks


# ===========================================================================
# I. Sonata Appassionata — G Minor, 108 BPM
#    Uses SonataFormPlan to allocate P/T/S/C zones with correct dynamics.
#    Exposition: tonic → relative major (Bb). Development: unstable keys.
#    Recapitulation: all themes return in G minor.
# ===========================================================================

def track_01_sonata():
    print("  I. Sonata Appassionata")
    bpm, total_dur = 108.0, 128.0
    key = G_MINOR

    # Build SonataFormPlan
    # Build SonataFormPlan
    plan = SonataFormPlan(key, total_bars=32)
    alloc_parts = plan.build()   # list[IdeaPart]
    # Derive zone beat boundaries from IdeaPart sequence
    beats_per_bar = 4.0
    # Collect cumulative beats per section label
    zone_beats: dict[str, float] = {}
    t = 0.0
    for part in alloc_parts:
        zone_beats[part.name] = t
        t += (part.bars or 0) * beats_per_bar
    expo_end  = zone_beats.get("Development", total_dur * 0.40)
    dev_end   = zone_beats.get("Recapitulation", total_dur * 0.70)
    recap_end = total_dur
    # Generate lead melody for full duration
    lead = _lead_melody(key, total_dur, lo=62, hi=86, density=0.55)
    chords = _harmonize(lead, key, total_dur)

    # Apply per-section velocity shaping (FORM-4 compliance)
    def _apply_zone_vel(notes: list[NoteInfo], lo: int, hi: int,
                        start: float, end: float) -> list[NoteInfo]:
        for n in notes:
            if start <= n.start < end:
                n.velocity = max(lo, min(hi, int(n.velocity)))
        return notes

    lead = _apply_zone_vel(lead, 80, 100, 0.0, expo_end)         # ff exposition
    lead = _apply_zone_vel(lead, 55, 80,  expo_end, dev_end)     # mp development
    lead = _apply_zone_vel(lead, 75, 100, dev_end, recap_end)    # f recapitulation

    # Strings — legato, keep BELOW violin (hi=66 < violin lo=69) — ARR-10 fix
    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.45, key_range_low=50, key_range_high=66),
        section_size="full", dynamic_shape="cresc_dim").render(chords, key, total_dur), 40, 85),
        total_dur, intro_end=total_dur*0.40, outro_start=total_dur*0.85, keep=0.15)

    # Violin — virtuosic runs
    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.6, key_range_low=69, key_range_high=91),
        articulation="legato").render(chords, key, total_dur - 8.0), 45, 92), total_dur)
    violin = _off(violin, 8.0)

    # Horns — keep below MIDI 62 to avoid crossing bass — ARR-10 fix
    horns_raw = _clamp(FrenchHornGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=62),
        articulation="legato").render(chords, key, total_dur - expo_end), 40, 82)
    horns = _off(horns_raw, expo_end)

    # Brass fanfare in recapitulation — keep above Strings (hi=66), lo=67
    brass_raw = _clamp(BrassSectionGenerator(
        GeneratorParams(density=0.35, key_range_low=67, key_range_high=84),
        ensemble_mode="full", intensity=0.95).render(chords, key, total_dur - dev_end), 55, 100)
    brass = _off(brass_raw, dev_end)

    # Bass + pedal
    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.85, key_range_low=24, key_range_high=40),
        articulation="legato").render(chords, key, total_dur), 45, 82)
    pedal = _pedal_tone(chords, key, total_dur, pitch=19, note_dur=4.0, velocity=50)

    # Glock for HIGH register
    glock_raw = _clamp(GlockenspielGenerator(
        GeneratorParams(density=0.4, key_range_low=84, key_range_high=104),
        pattern="sparkling_run", note_density=1.0).render(chords, key, total_dur - 12.0), 38, 72)
    glock = _thin(_off(glock_raw, 12.0), total_dur)

    # Timpani in development + recap
    timp_raw = _clamp(TimpaniGenerator(
        GeneratorParams(density=0.35, key_range_low=36, key_range_high=48),
        stroke_pattern="roll").render(chords, key, total_dur - expo_end), 55, 95)
    timp = _off(timp_raw, expo_end)

    return {
        "Lead": _clamp(lead, 50, 100), "Strings": strings, "Violin1": violin,
        "Horns": horns, "Brass": brass, "Bass": bass, "Pedal": pedal,
        "Glock": glock, "Timpani": timp,
    }, bpm, MusicalForm.sonata(G_MINOR, 128.0, base_bpm=108.0)


# ===========================================================================
# II. Canon Perpetuus — D Major, 84 BPM
#    CanonGenerator: 3-voice canon at the fifth with 4-beat delay.
#    Demonstrates imitative counterpoint across violin/viola/cello.
# ===========================================================================

def track_02_canon():
    print("  II. Canon Perpetuus")
    bpm, dur = 84.0, 96.0
    key = D_MAJOR

    # Generate the canonic subject (dux)
    lead = _lead_melody(key, dur, lo=62, hi=81, density=0.45)
    chords = _harmonize(lead, key, dur)

    # Build 3-voice canon: dux + comes + third
    gen = CanonGenerator(
        delay_beats=4.0,
        n_voices=3,
        interval_semitones=7,
        velocity_decay=0.88,
        canon_type="fifth",
    )
    voices = gen.generate(lead, key)  # list[list[NoteInfo]] — one per voice
    if not voices:
        voices = [list(lead), [], []]

    # Apply melodic inversion to third voice for variety (P5.15)
    if len(voices) >= 3 and voices[2]:
        voices[2] = _clamp(inversion(voices[2], key), 30, 85)

    # Harp II — keep below Lead (lo=62), ARR-10 fix
    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.3, key_range_low=43, key_range_high=60),
        pattern="arpeggio", direction="up").render(chords, key, dur), 30, 68), dur)

    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.75, key_range_low=26, key_range_high=38),
        articulation="pizzicato").render(chords, key, dur), 42, 70)  # hi=38 stays below Harp lo=43
    pedal = _pedal_tone(chords, key, dur, pitch=26, note_dur=4.0, velocity=48)

    # Glock sparkle
    glock_raw = _clamp(GlockenspielGenerator(
        GeneratorParams(density=0.35, key_range_low=84, key_range_high=104),
        pattern="sparkling_run", note_density=0.9).render(chords, key, dur - 8.0), 35, 68)
    glock = _thin(_off(glock_raw, 8.0), dur)

    # Flute — keep ABOVE Lead (lead hi=81, flute lo=76) — ARR-10 fix
    flute_raw = _clamp(FluteGenerator(
        GeneratorParams(density=0.4, key_range_low=76, key_range_high=93),
        articulation="legato", register=3).render(chords, key, dur - 16.0), 40, 80)
    flute_retro = _clamp(retrograde(flute_raw), 40, 80)
    flute = _thin(_off(flute_retro, 16.0), dur)

    # Assemble voices
    dux   = _clamp(_thin(voices[0], dur), 50, 92) if voices else []
    comes = _clamp(_thin(voices[1], dur), 45, 85) if len(voices) > 1 else []
    third = voices[2] if len(voices) > 2 else []

    return {
        "Lead": dux, "Canon": comes, "Viola": third,
        "Harp": harp, "Flute": flute, "Glock": glock,
        "Bass": bass, "Pedal": pedal,
    }, bpm, MusicalForm.through_composed(D_MAJOR, 96.0, base_bpm=84.0)


# ===========================================================================
# III. Rondo Brillante — Bb Major, 120 BPM
#    FormTemplate.RONDO: A-B-A-C-A structure.
#    AntiphonyBuilder: strings call, woodwinds respond.
# ===========================================================================

def track_03_rondo():
    print("  III. Rondo Brillante")
    bpm, dur = 120.0, 100.0
    key = BB_MAJOR

    lead = _lead_melody(key, dur, lo=65, hi=86, density=0.6)
    chords = _harmonize(lead, key, dur)

    # FormTemplate.RONDO divides into 5 sections: A-B-A-C-A
    sections = form_plan(FormTemplate.RONDO, key, total_bars=25)
    # Each section is ~20 beats (5 bars × 4 beats)
    sec_dur = dur / max(len(sections), 1)

    # Strings group (CALL) — violins + strings
    violin = _thin(_clamp(ViolinGenerator(
        GeneratorParams(density=0.55, key_range_low=65, key_range_high=89),
        articulation="spiccato").render(chords, key, dur), 50, 92), dur,
        intro_end=dur*0.15, outro_start=dur*0.85)

    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.35, key_range_low=50, key_range_high=72),
        section_size="chamber", dynamic_shape="flat").render(chords, key, dur), 40, 80), dur)

    # Woodwinds group (RESPONSE) — flute + clarinet + oboe
    flute_raw = _clamp(FluteGenerator(
        GeneratorParams(density=0.5, key_range_low=72, key_range_high=93),
        articulation="staccato", register=3).render(chords, key, dur - 8.0), 45, 85)
    flute = _thin(_off(flute_raw, 8.0), dur)

    clar = _thin(_clamp(ClarinetGenerator(
        GeneratorParams(density=0.45, key_range_low=57, key_range_high=69),
        articulation="staccato").render(chords, key, dur), 40, 82), dur)

    oboe_raw = _clamp(OboeGenerator(
        GeneratorParams(density=0.4, key_range_low=67, key_range_high=88),
        articulation="legato", register=2).render(chords, key, dur - 12.0), 42, 80)
    oboe = _thin(_off(oboe_raw, 12.0), dur)

    # Antiphony: strings call, woodwinds respond with 8-beat windows
    # Antiphony: strings call, woodwinds respond with 8-beat windows
    strings_group = {"Violin1": violin, "Strings": strings}
    winds_group   = {"Flute": flute, "Clarinet": clar, "Oboe": oboe}
    builder = AntiphonyBuilder(
        phrase_bars=2.0,
        beats_per_bar=4.0,
        overlap_bars=0.25,
        echo_velocity_scale=0.88,
    )
    all_tracks = {**strings_group, **winds_group}
    all_ant = builder.apply(all_tracks, total_beats=dur)
    call_tracks = {k: v for k, v in all_ant.items() if k in strings_group}
    resp_tracks = {k: v for k, v in all_ant.items() if k in winds_group}

    # Bass + pedal (Bb = MIDI 22 → use 34 = Bb1)
    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.8, key_range_low=22, key_range_high=38),
        articulation="pizzicato").render(chords, key, dur), 48, 85)
    pedal = _pedal_tone(chords, key, dur, pitch=22, note_dur=4.0, velocity=50)

    # Glock
    glock_raw = _clamp(GlockenspielGenerator(
        GeneratorParams(density=0.45, key_range_low=86, key_range_high=106),
        pattern="sparkling_run", note_density=1.1).render(chords, key, dur - 8.0), 38, 72)
    glock = _thin(_off(glock_raw, 8.0), dur)

    # Horns for B/C episodes
    horns_raw = _clamp(FrenchHornGenerator(
        GeneratorParams(density=0.25, key_range_low=50, key_range_high=67),
        articulation="legato").render(chords, key, dur - sec_dur), 38, 75)
    horns = _off(horns_raw, sec_dur)

    out: dict[str, list[NoteInfo]] = {}
    out.update(call_tracks)
    out.update(resp_tracks)
    out["Lead"] = _clamp(lead, 55, 95)
    out["Bass"] = bass
    out["Pedal"] = pedal
    out["Glock"] = glock
    out["Horns"] = horns

    return out, bpm, MusicalForm.rondo(BB_MAJOR, 100.0, base_bpm=120.0)


# ===========================================================================
# IV. Theme & Variations — E Minor, 72 BPM
#    VariationPlan: theme + 4 variations using melodic_transforms.
#    Variation 1: melodic inversion, Var 2: augmentation,
#    Var 3: retrograde counterpoint, Var 4: diatonic transposition up 3rd.
# ===========================================================================

def track_04_variations():
    print("  IV. Theme & Variations")
    bpm, dur = 72.0, 96.0
    key = E_MINOR

    theme_dur = dur / 5.0   # 5 sections: theme + 4 vars = ~19.2 beats each

    theme = _lead_melody(key, theme_dur, lo=64, hi=83, density=0.4)
    chords = _harmonize(theme, key, theme_dur)

    # Theme (p, quiet opening)
    theme_track = _vel_scale(_clamp(list(theme), 35, 62), 35, 62)

    # Var 1 — melodic inversion (mp)
    var1_notes = _vel_scale(_clamp(inversion(theme, key), 45, 72), 45, 72)
    var1_notes = _off(var1_notes, theme_dur)

    # Var 2 — augmentation × 2 (f, slower notes fill longer space)
    var2_raw = augmentation(theme, factor=2.0)
    # scale to fit var_dur
    var2_notes = _vel_scale(_clamp(var2_raw, 55, 82), 55, 82)
    var2_notes = _off(var2_notes, theme_dur * 2)

    # Var 3 — retrograde at ff
    var3_notes = _vel_scale(_clamp(retrograde(theme), 65, 90), 65, 90)
    var3_notes = _off(var3_notes, theme_dur * 3)

    # Var 4 — diatonic transposition up a third (ff → climax)
    var4_notes = _vel_scale(_clamp(diatonic_transposition(theme, key, degrees=2), 72, 100), 72, 100)
    var4_notes = _off(var4_notes, theme_dur * 4)

    # Combine theme + vars into single Lead track
    all_lead = theme_track + var1_notes + var2_notes + var3_notes + var4_notes

    # Chords for full duration
    full_chords = _harmonize(all_lead, key, dur)

    # Strings — keep below Lead (lead lo=64, strings hi=63) — ARR-10 fix
    strings = _thin(_clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=63),
        section_size="chamber", dynamic_shape="cresc_dim").render(full_chords, key, dur), 30, 80), dur)

    # Harp in theme + var1 — keep below Lead (harp hi=60) — ARR-10 fix
    harp_raw = _clamp(HarpGenerator(
        GeneratorParams(density=0.25, key_range_low=43, key_range_high=60),
        pattern="arpeggio", direction="up_down").render(full_chords, key, theme_dur * 2), 28, 58)
    harp = harp_raw  # plays in first two sections only

    # Choir enters in var3 + var4
    choir_raw = _clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.3, key_range_low=48, key_range_high=69),
        voice_count=4, dynamics="mf", syllable="aah").render(full_chords, key, theme_dur * 2), 45, 82)
    choir = _off(choir_raw, theme_dur * 3)

    # Cello countermelody — keep below Strings (strings lo=48, cello hi=47)
    cello = _thin(_clamp(CelloGenerator(
        GeneratorParams(density=0.35, key_range_low=36, key_range_high=47),
        articulation="legato").render(full_chords, key, dur), 38, 72), dur)

    # Bass + pedal
    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.75, key_range_low=24, key_range_high=40),
        articulation="legato").render(full_chords, key, dur), 42, 78)
    pedal = _pedal_tone(full_chords, key, dur, pitch=16, note_dur=4.0, velocity=48)

    # Glock — full dur for HIGH register + late climax thin (ARR-4 + ARR-7 fix)
    glock_full = _clamp(GlockenspielGenerator(
        GeneratorParams(density=0.3, key_range_low=84, key_range_high=104),
        pattern="sparkling_run", note_density=0.8).render(full_chords, key, dur - 8.0), 32, 72)
    glock_raw = _thin(_off(glock_full, 8.0), dur, intro_end=dur*0.30, outro_start=dur*0.82, keep=0.25)

    return {
        "Lead": all_lead, "Strings": strings, "Harp": harp,
        "Choir": choir, "Cello": cello, "Bass": bass,
        "Pedal": pedal, "Glock": glock_raw,
    }, bpm, MusicalForm.through_composed(E_MINOR, 96.0, base_bpm=72.0)


# ===========================================================================
# V. Arch of Eternity — C Major, 96 BPM
#    FormTemplate.ARCH: A-B-C-B'-A' form (palindromic).
#    ChordVoicingLayout: orchestral voicing for climax chord progression.
# ===========================================================================

def track_05_arch():
    print("  V. Arch of Eternity")
    bpm, dur = 96.0, 112.0
    key = C_MAJOR

    lead = _lead_melody(key, dur, lo=64, hi=86, density=0.5)
    chords = _harmonize(lead, key, dur)

    # ARCH form: A(sparse) → B(build) → C(climax) → B'(echo) → A'(quiet close)
    sections = form_plan(FormTemplate.ARCH, key, total_bars=28)
    arch_sec = dur / max(len(sections), 5)  # ~22.4 beats each section

    # A section — violin BELOW Lead (lead lo=64, violin hi=63)
    violin_a = _vel_scale(_clamp(ViolinGenerator(
        GeneratorParams(density=0.3, key_range_low=55, key_range_high=63),
        articulation="legato").render(chords, key, arch_sec), 30, 60), 30, 60)

    # B section (build, mp → mf)
    strings_b_raw = _clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.4, key_range_low=50, key_range_high=74),
        section_size="chamber", dynamic_shape="crescendo").render(chords, key, arch_sec), 45, 78)
    strings_b = _off(strings_b_raw, arch_sec)

    # C section (climax, ff) — full orchestra
    brass_c_raw = _clamp(BrassSectionGenerator(
        GeneratorParams(density=0.4, key_range_low=48, key_range_high=72),
        ensemble_mode="full", intensity=1.0).render(chords, key, arch_sec), 65, 105)
    brass_c = _off(brass_c_raw, arch_sec * 2)

    choir_c_raw = _clamp(ChoirAahsGenerator(
        GeneratorParams(density=0.35, key_range_low=64, key_range_high=79),
        voice_count=6, dynamics="ff", syllable="aah").render(chords, key, arch_sec), 62, 100)
    choir_c = _off(choir_c_raw, arch_sec * 2)

    timp_c_raw = _clamp(TimpaniGenerator(
        GeneratorParams(density=0.4, key_range_low=36, key_range_high=48),
        stroke_pattern="roll").render(chords, key, arch_sec), 60, 100)
    timp_c = _off(timp_c_raw, arch_sec * 2)

    # B' section (echo of B, mp → mf)
    strings_bp_raw = _clamp(StringsLegatoGenerator(
        GeneratorParams(density=0.35, key_range_low=50, key_range_high=74),
        section_size="chamber", dynamic_shape="cresc_dim").render(chords, key, arch_sec), 40, 72)
    strings_bp = _off(strings_bp_raw, arch_sec * 3)

    horns_bp_raw = _clamp(FrenchHornGenerator(
        GeneratorParams(density=0.25, key_range_low=48, key_range_high=67),
        articulation="legato").render(chords, key, arch_sec), 38, 70)
    horns_bp = _off(horns_bp_raw, arch_sec * 3)

    # A' section — same register as A (below Lead)
    violin_ap_raw = _vel_scale(_clamp(ViolinGenerator(
        GeneratorParams(density=0.25, key_range_low=55, key_range_high=63),
        articulation="legato").render(chords, key, arch_sec), 25, 52), 25, 52)
    violin_ap = _off(violin_ap_raw, arch_sec * 4)

    # Harp — keep below Lead (lead lo=64, harp hi=62) — ARR-10 fix
    harp = _thin(_clamp(HarpGenerator(
        GeneratorParams(density=0.3, key_range_low=43, key_range_high=62),
        pattern="arpeggio", direction="up_down").render(chords, key, dur), 28, 65), dur)

    # Glock HIGH register throughout
    glock_raw = _clamp(GlockenspielGenerator(
        GeneratorParams(density=0.35, key_range_low=86, key_range_high=106),
        pattern="sparkling_run", note_density=0.9).render(chords, key, dur - 8.0), 32, 68)
    glock = _thin(_off(glock_raw, 8.0), dur)

    # Bass + pedal
    bass = _clamp(ContrabassGenerator(
        GeneratorParams(density=0.8, key_range_low=24, key_range_high=40),
        articulation="legato").render(chords, key, dur), 42, 80)
    pedal = _pedal_tone(chords, key, dur, pitch=24, note_dur=4.0, velocity=50)

    # Combine full lead
    return {
        "Lead":     _clamp(lead, 45, 98),
        "Violin1":  violin_a + violin_ap,
        "Strings":  strings_b + strings_bp,
        "Brass":    brass_c,
        "Choir":    choir_c,
        "Horns":    horns_bp,
        "Harp":     harp,
        "Glock":    glock,
        "Bass":     bass,
        "Pedal":    pedal,
        "Timpani":  timp_c,
    }, bpm, MusicalForm.ternary(C_MAJOR, 112.0, base_bpm=96.0)


# ---------------------------------------------------------------------------
# Instrument GM program maps
# ---------------------------------------------------------------------------

TRACKS = [
    (track_01_sonata, "01_Sonata_Appassionata.mid", {
        "Lead": 40, "Strings": 48, "Violin1": 40, "Horns": 60,
        "Brass": 61, "Bass": 43, "Pedal": 43, "Glock": 9, "Timpani": 47,
    }),
    (track_02_canon, "02_Canon_Perpetuus.mid", {
        "Lead": 40, "Canon": 41, "Viola": 42, "Harp": 46,
        "Flute": 73, "Glock": 9, "Bass": 43, "Pedal": 43,
    }),
    (track_03_rondo, "03_Rondo_Brillante.mid", {
        "Lead": 71, "Violin1": 40, "Strings": 48, "Flute": 73,
        "Clarinet": 71, "Oboe": 68, "Horns": 60, "Bass": 43,
        "Pedal": 43, "Glock": 9,
    }),
    (track_04_variations, "04_Theme_and_Variations.mid", {
        "Lead": 40, "Strings": 48, "Harp": 46, "Choir": 52,
        "Cello": 42, "Bass": 43, "Pedal": 43, "Glock": 9,
    }),
    (track_05_arch, "05_Arch_of_Eternity.mid", {
        "Lead": 73, "Violin1": 40, "Strings": 48, "Brass": 61,
        "Choir": 52, "Horns": 60, "Harp": 46, "Glock": 9,
        "Bass": 43, "Pedal": 43, "Timpani": 47,
    }),
]


def main():
    album_dir = Path("output/album_forma")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 78)
    print("      F O R M A :   F I V E   S T U D I E S   I N   C L A S S I C A L")
    print("      A R C H I T E C T U R E")
    print("=" * 78)

    total_notes = 0
    for producer, filename, instruments in TRACKS:
        print("-" * 78)
        raw, bpm, form = producer()
        raw = apply_pipeline(raw, bpm, form=form)
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
    print(f"  COMPLETE: FORMA — {total_notes} notes across 5 movements")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
