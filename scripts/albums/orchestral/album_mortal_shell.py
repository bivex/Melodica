# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_mortal_shell.py — MORTAL SHELL: ECHOES OF FLESH

A 30-movement dark atmospheric orchestral album (~90 min) inspired by
Mortal Shell: flesh, shells, corruption, forgotten temples, mist,
and the slow decay of a world without hope.

Five movements:
    I.   Fallgrim           (awakening, mist, the swamp)
    II.  The Shells          (four vessels, four souls)
    III. The Temples         (crypts, shrines, sanctums, infinity)
    IV.  Combat & Corruption (clashes, bosses, the unchained)
    V.   Transcendence       (resolution, sacrifice, silence)

Modes: PHRYGIAN, AEOLIAN, HARMONIC_MINOR, LOCRIAN, DORIAN, HUNGARIAN_MINOR,
       PHRYGIAN_DOMINANT, DOUBLE_HARMONIC, ALTERED, BYZANTINE, MELODIC_MINOR,
       PERSIAN, BLUES, GYPSY, NEAPOLITAN_MINOR.
"""

from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams

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
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.tuba import TubaGenerator
from melodica.generators.snare_drum import SnareDrumGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator
from melodica.generators.organ_drawbars import OrganDrawbarsGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.tension import TensionGenerator
from melodica.generators.chorale import ChoraleGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.canon import CanonGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator

from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# ---------------------------------------------------------------------------
# Scales
# ---------------------------------------------------------------------------
E_PH   = Scale(4,  Mode.PHRYGIAN)
A_PH   = Scale(9,  Mode.PHRYGIAN)
B_PH   = Scale(11, Mode.PHRYGIAN)
D_PH   = Scale(2,  Mode.PHRYGIAN)
FS_PH  = Scale(6,  Mode.PHRYGIAN)
CS_PH  = Scale(1,  Mode.PHRYGIAN)
BB_PH  = Scale(10, Mode.PHRYGIAN)
EF_PH  = Scale(3,  Mode.PHRYGIAN)

D_AE   = Scale(2,  Mode.AEOLIAN)
E_AE   = Scale(4,  Mode.AEOLIAN)
A_AE   = Scale(9,  Mode.AEOLIAN)
B_AE   = Scale(11, Mode.AEOLIAN)
C_AE   = Scale(0,  Mode.AEOLIAN)
F_AE   = Scale(5,  Mode.AEOLIAN)
FS_AE  = Scale(6,  Mode.AEOLIAN)
CS_AE  = Scale(1,  Mode.AEOLIAN)
BB_AE  = Scale(10, Mode.AEOLIAN)
EF_AE  = Scale(3,  Mode.AEOLIAN)
G_AE   = Scale(7,  Mode.AEOLIAN)
AB_AE  = Scale(8,  Mode.AEOLIAN)

E_HM   = Scale(4,  Mode.HARMONIC_MINOR)
A_HM   = Scale(9,  Mode.HARMONIC_MINOR)
B_HM   = Scale(11, Mode.HARMONIC_MINOR)
D_HM   = Scale(2,  Mode.HARMONIC_MINOR)
F_HM   = Scale(5,  Mode.HARMONIC_MINOR)
CS_HM  = Scale(1,  Mode.HARMONIC_MINOR)
EF_HM  = Scale(3,  Mode.HARMONIC_MINOR)
FS_HM  = Scale(6,  Mode.HARMONIC_MINOR)
AB_HM  = Scale(8,  Mode.HARMONIC_MINOR)
G_HM   = Scale(7,  Mode.HARMONIC_MINOR)

D_LOC  = Scale(2,  Mode.LOCRIAN)
E_LOC  = Scale(4,  Mode.LOCRIAN)
B_LOC  = Scale(11, Mode.LOCRIAN)

A_DOR  = Scale(9,  Mode.DORIAN)
E_DOR  = Scale(4,  Mode.DORIAN)
D_DOR  = Scale(2,  Mode.DORIAN)

E_HU   = Scale(4,  Mode.HUNGARIAN_MINOR)
A_HU   = Scale(9,  Mode.HUNGARIAN_MINOR)
B_HU   = Scale(11, Mode.HUNGARIAN_MINOR)
D_HU   = Scale(2,  Mode.HUNGARIAN_MINOR)

E_PD   = Scale(4,  Mode.PHRYGIAN_DOMINANT)
A_PD   = Scale(9,  Mode.PHRYGIAN_DOMINANT)
B_PD   = Scale(11, Mode.PHRYGIAN_DOMINANT)
D_PD   = Scale(2,  Mode.PHRYGIAN_DOMINANT)

A_DBH  = Scale(9,  Mode.DOUBLE_HARMONIC)
E_DBH  = Scale(4,  Mode.DOUBLE_HARMONIC)

E_ALT  = Scale(4,  Mode.ALTERED)
B_ALT  = Scale(11, Mode.ALTERED)

A_BYZ  = Scale(9,  Mode.BYZANTINE)
B_BYZ  = Scale(11, Mode.BYZANTINE)

E_MEL  = Scale(4,  Mode.MELODIC_MINOR)

E_PER  = Scale(4,  Mode.PERSIAN)

B_BL   = Scale(11, Mode.BLUES)

CS_NM  = Scale(1,  Mode.NEAPOLITAN_MINOR)

E_GY   = Scale(4,  Mode.GYPSY)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def _bc(progression: str, duration: float, key: Scale) -> list[ChordLabel]:
    parts = progression.split()
    b = duration / len(parts)
    return [
        (lambda c: ChordLabel(root=c.root, quality=c.quality, start=i * b, duration=b))(key.parse_roman(p))
        for i, p in enumerate(parts)
    ]

def _cl(notes, lo=1, hi=127):
    for n in notes:
        n.velocity = max(lo, min(hi, n.velocity))
    return notes

def _sw(note, dur, pk=0.5):
    pt = note.start + dur * pk
    note.expression[11] = [(round(note.start, 3), 40), (round(pt, 3), 100), (round(note.start + dur, 3), 30)]

def _mix(raw, bpm, lufs=-16.0):
    desk = MixingDesk(niche_cfg={})
    for k in raw:
        desk.track_gains.setdefault(k, 0.78)
    mixed = desk.apply_mixing(raw, [], int(bpm))
    m = MasteringDesk(target_lufs=lufs)
    return m.apply_mastering(mixed)


# ===========================================================================
# I. FALLGRIM — Awakening, mist, the swamp  (tracks 1–6)
# ===========================================================================

def t01():
    print("  01. Awakening")
    dur, key = 80.0, E_PH
    ch = _bc("i bII i v i bVI bVII i", dur, key)
    cello = _cl(CelloGenerator(GeneratorParams(density=0.3, key_range_low=36, key_range_high=55), articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.0).render(ch, key, dur), 30, 65)
    drone = _cl(DroneGenerator(GeneratorParams(density=0.02, key_range_low=20, key_range_high=32), velocity=40).render(ch, key, dur), 20, 45)
    return {"Cello": cello, "Drone": drone}, 36.0

def t02():
    print("  02. The Mist Descends")
    dur, key = 76.0, D_LOC
    ch = _bc("i bII bv bvii i bII bv i bvii i", dur, key)
    tension = _cl(TensionGenerator(GeneratorParams(density=0.4, key_range_low=28, key_range_high=68), mode="semitone_cluster", note_duration=3.0, velocity_level=0.3, register="low").render(ch, key, dur), 20, 50)
    trem = _cl(TremoloStringsGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=60), bow_speed=0.0625, dynamic_swell=True).render(ch, key, dur), 20, 45)
    return {"Tension": tension, "Tremolo": trem}, 40.0

def t03():
    print("  03. Fallgrim Approach")
    dur, key = 64.0, A_PH
    ch = _bc("i bII i v bVII bVI bVII i v i bII v i", dur, key)
    ost = _cl(OstinatoGenerator(GeneratorParams(density=0.45, key_range_low=28, key_range_high=52), pattern="repeated_figure", repeat_notes=3, changed_notes_count=2).render(ch, key, dur), 30, 55)
    viola = _cl(ViolaGenerator(GeneratorParams(density=0.35, key_range_low=48, key_range_high=68), articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=1.2).render(ch, key, dur), 30, 60)
    pedal = _cl(PedalBassGenerator(GeneratorParams(density=0.2, key_range_low=24, key_range_high=36), pedal_note="root", sustain=2.0, velocity_level=0.4).render(ch, key, dur), 25, 45)
    return {"Ostinato": ost, "Viola": viola, "Pedal": pedal}, 48.0

def t04():
    print("  04. Sester's Song")
    dur, key = 72.0, FS_AE
    ch = _bc("i iv i bVI bVII i III iv i bVI iv i", dur, key)
    harp = _cl(HarpGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=80), pattern="arpeggio", direction="up", spread_speed=0.15).render(ch, key, dur), 25, 55)
    flute = _cl(FluteGenerator(GeneratorParams(density=0.45, key_range_low=60, key_range_high=90), articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.3).render(ch, key, dur), 30, 70)
    strings = _cl(StringsLegatoGenerator(GeneratorParams(density=0.35, key_range_low=44, key_range_high=72), ensemble_mode="section", dynamic_shape="crescendo").render(ch, key, dur), 25, 60)
    return {"Harp": harp, "Flute": flute, "Strings": strings}, 44.0

def t05():
    print("  05. The Sickened")
    dur, key = 68.0, BB_PH
    ch = _bc("i bII iv v i bVI iv bII i v bVI i", dur, key)
    bsn = _cl(BassoonGenerator(GeneratorParams(density=0.3, key_range_low=34, key_range_high=50), articulation="staccato", vibrato=False, dynamic_curve="flat", note_density=1.2).render(ch, key, dur), 25, 50)
    tension = _cl(TensionGenerator(GeneratorParams(density=0.3, key_range_low=28, key_range_high=60), mode="chromatic_rise", note_duration=2.5, velocity_level=0.25, register="low").render(ch, key, dur), 20, 45)
    drone = _cl(DroneGenerator(GeneratorParams(density=0.02, key_range_low=22, key_range_high=34), velocity=35).render(ch, key, dur), 20, 40)
    return {"Bassoon": bsn, "Tension": tension, "Drone": drone}, 42.0

def t06():
    print("  06. Swamp Crossing")
    dur, key = 60.0, D_PD
    ch = _bc("i bII V i iv bVI bII V i iv bVI i", dur, key)
    pizz = _cl(StringsPizzicatoGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=60), pattern="ostinato", staccato_length=0.1).render(ch, key, dur), 30, 55)
    timp = _cl(TimpaniGenerator(GeneratorParams(density=0.25), stroke_pattern="single", drum_count=4).render(ch, key, dur), 35, 55)
    cb = _cl(ContrabassGenerator(GeneratorParams(density=0.3, key_range_low=24, key_range_high=40), articulation="sustained", dynamic_curve="flat", note_density=1.0).render(ch, key, dur), 25, 50)
    return {"Pizzicato": pizz, "Timpani": timp, "Bass": cb}, 50.0


# ===========================================================================
# II. THE SHELLS — Four vessels, four souls  (tracks 7–10)
# ===========================================================================

def t07():
    print("  07. Harros, the Vessel")
    dur, key = 70.0, C_AE
    ch = _bc("i iv i bVI bVII i III iv v i bVI iv i", dur, key)
    chorale = _cl(ChoraleGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=72), voice_spacing=12, soprano_motion="stepwise", rhythmic_unit=2.0).render(ch, key, dur), 30, 65)
    horn = _cl(FrenchHornGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=60), articulation="sustained", dynamic_curve="crescendo", note_density=1.5).render(ch, key, dur), 30, 65)
    pedal = _cl(PedalBassGenerator(GeneratorParams(density=0.2, key_range_low=24, key_range_high=36), pedal_note="root", sustain=2.0, velocity_level=0.4).render(ch, key, dur), 25, 45)
    return {"Chorale": chorale, "Horns": horn, "Pedal": pedal}, 46.0

def t08():
    print("  08. Tiel, the Acolyte")
    dur, key = 66.0, E_DOR
    ch = _bc("i IV i V i III VII iv i i IV VII i", dur, key)
    flute = _cl(FluteGenerator(GeneratorParams(density=0.5, key_range_low=60, key_range_high=90), articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.8).render(ch, key, dur), 30, 70)
    harp = _cl(HarpGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=80), pattern="arpeggio", direction="up", spread_speed=0.12).render(ch, key, dur), 25, 55)
    strings = _cl(StringsLegatoGenerator(GeneratorParams(density=0.4, key_range_low=40, key_range_high=72), ensemble_mode="section", dynamic_shape="crescendo").render(ch, key, dur), 25, 60)
    return {"Flute": flute, "Harp": harp, "Strings": strings}, 52.0

def t09():
    print("  09. Solomon, the Scholar")
    dur, key = 74.0, A_HM
    ch = _bc("i iv V i bVI bVII V i iv bVI V i bVII V i", dur, key)
    organ = _cl(OrganDrawbarsGenerator(GeneratorParams(density=0.4, key_range_low=28, key_range_high=56), registration="gospel", leslie_speed="slow", percussion=False).render(ch, key, dur), 25, 55)
    bsn = _cl(BassoonGenerator(GeneratorParams(density=0.3, key_range_low=34, key_range_high=52), articulation="sustained", vibrato=False, dynamic_curve="flat", note_density=1.2).render(ch, key, dur), 25, 55)
    cello = _cl(CelloGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=56), articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=1.3).render(ch, key, dur), 25, 55)
    return {"Organ": organ, "Bassoon": bsn, "Cello": cello}, 40.0

def t10():
    print("  10. Eredrim, the Last")
    dur, key = 68.0, D_HU
    ch = _bc("i bII iv V i bVI iv bII i V bVI iv i", dur, key)
    brass = _cl(BrassSectionGenerator(GeneratorParams(density=0.5, key_range_low=36, key_range_high=68), articulation="sustained", voicing="closed", divisi_count=4).render(ch, key, dur), 35, 75)
    choir = _cl(ChoirAahsGenerator(GeneratorParams(density=0.4, key_range_low=40, key_range_high=68), voice_count=4, dynamics="mp", vibrato=0.3, syllable="ooh").render(ch, key, dur), 25, 60)
    timp = _cl(TimpaniGenerator(GeneratorParams(density=0.3), stroke_pattern="single", drum_count=4).render(ch, key, dur), 35, 60)
    return {"Brass": brass, "Choir": choir, "Timpani": timp}, 44.0


# ===========================================================================
# III. THE TEMPLES — Crypts, shrines, sanctums, infinity  (tracks 11–20)
# ===========================================================================

def t11():
    print("  11. Temple Gate")
    dur, key = 78.0, B_PH
    ch = _bc("i bII i v i bVI bVII i v i bII bVI i", dur, key)
    drone = _cl(DroneGenerator(GeneratorParams(density=0.02, key_range_low=20, key_range_high=32), velocity=38).render(ch, key, dur), 20, 42)
    choir = _cl(ChoirAahsGenerator(GeneratorParams(density=0.3, key_range_low=40, key_range_high=64), voice_count=4, dynamics="pp", vibrato=0.15, syllable="aah").render(ch, key, dur), 20, 45)
    tension = _cl(TensionGenerator(GeneratorParams(density=0.3, key_range_low=32, key_range_high=64), mode="major7_tension", note_duration=3.0, velocity_level=0.25, register="low").render(ch, key, dur), 20, 42)
    return {"Drone": drone, "Choir": choir, "Tension": tension}, 38.0

def t12():
    print("  12. Crypt of Martyrs — Entrance")
    dur, key = 64.0, F_AE
    ch = _bc("i iv i bVI bVII i III iv v i bVI iv i", dur, key)
    ost = _cl(OstinatoGenerator(GeneratorParams(density=0.45, key_range_low=28, key_range_high=48), pattern="repeated_figure", repeat_notes=3, changed_notes_count=2).render(ch, key, dur), 30, 55)
    viola = _cl(ViolaGenerator(GeneratorParams(density=0.3, key_range_low=48, key_range_high=68), articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=1.0).render(ch, key, dur), 25, 55)
    bsn = _cl(BassoonGenerator(GeneratorParams(density=0.25, key_range_low=34, key_range_high=50), articulation="sustained", vibrato=False, dynamic_curve="flat", note_density=1.0).render(ch, key, dur), 25, 50)
    return {"Ostinato": ost, "Viola": viola, "Bassoon": bsn}, 42.0

def t13():
    print("  13. Crypt — The Warden")
    dur, key = 56.0, F_HM
    ch = _bc("i iv V i bVI bVII V i iv bVI V i", dur, key)
    brass = _cl(BrassSectionGenerator(GeneratorParams(density=0.55, key_range_low=36, key_range_high=72), articulation="sustained", voicing="closed", divisi_count=4).render(ch, key, dur), 40, 80)
    snare = _cl(SnareDrumGenerator(GeneratorParams(density=0.5), pattern_type="march").render(ch, key, dur), 40, 70)
    timp = _cl(TimpaniGenerator(GeneratorParams(density=0.45), stroke_pattern="single", drum_count=5).render(ch, key, dur), 40, 75)
    return {"Brass": brass, "Snare": snare, "Timpani": timp}, 56.0

def t14():
    print("  14. Shrine of Ash — Descent")
    dur, key = 72.0, E_ALT
    ch = _bc("i bII biii iv bv bvi bvii i bII bv i bvi bvii i", dur, key)
    tension = _cl(TensionGenerator(GeneratorParams(density=0.4, key_range_low=32, key_range_high=68), mode="chromatic_fall", note_duration=2.0, velocity_level=0.3, register="mid").render(ch, key, dur), 20, 50)
    organ = _cl(OrganDrawbarsGenerator(GeneratorParams(density=0.35, key_range_low=28, key_range_high=56), registration="jazz", leslie_speed="slow", percussion=True).render(ch, key, dur), 20, 50)
    cp = _cl(CounterpointGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=68), species=3, voices=2).render(ch, key, dur), 20, 50)
    return {"Tension": tension, "Organ": organ, "Counterpoint": cp}, 40.0

def t15():
    print("  15. Shrine — The Fire Within")
    dur, key = 66.0, E_MEL
    ch = _bc("i II IV V i vi IV V i II IV i V i", dur, key)
    canon = _cl(CanonGenerator(GeneratorParams(density=0.5, key_range_low=48, key_range_high=84), canon_type="tonal", delay_beats=4.0, interval=4, num_followers=2).render(ch, key, dur), 30, 70)
    harp = _cl(HarpGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=80), pattern="arpeggio", direction="up", spread_speed=0.1).render(ch, key, dur), 25, 55)
    strings = _cl(StringsLegatoGenerator(GeneratorParams(density=0.45, key_range_low=40, key_range_high=72), ensemble_mode="section", dynamic_shape="crescendo").render(ch, key, dur), 25, 65)
    return {"Canon": canon, "Harp": harp, "Strings": strings}, 48.0

def t16():
    print("  16. Enshrined Sanctum — Halls")
    dur, key = 70.0, AB_AE
    ch = _bc("i iv i bVI bVII i III iv v i bVI iv i bVII i", dur, key)
    chorale = _cl(ChoraleGenerator(GeneratorParams(density=0.4, key_range_low=32, key_range_high=72), voice_spacing=14, soprano_motion="stepwise", rhythmic_unit=2.5).render(ch, key, dur), 25, 60)
    trem = _cl(TremoloStringsGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=60), bow_speed=0.0625, dynamic_swell=True).render(ch, key, dur), 20, 50)
    pedal = _cl(PedalBassGenerator(GeneratorParams(density=0.2, key_range_low=24, key_range_high=36), pedal_note="root", sustain=2.0, velocity_level=0.4).render(ch, key, dur), 20, 40)
    return {"Chorale": chorale, "Tremolo": trem, "Pedal": pedal}, 38.0

def t17():
    print("  17. Sanctum — The Guardian")
    dur, key = 58.0, AB_HM
    ch = _bc("i iv V i bVI bVII V i iv bVI V i", dur, key)
    brass = _cl(BrassSectionGenerator(GeneratorParams(density=0.55, key_range_low=36, key_range_high=72), articulation="sustained", voicing="open", divisi_count=4).render(ch, key, dur), 40, 80)
    hit = _cl(OrchestralHitGenerator(GeneratorParams(density=0.3, key_range_low=36, key_range_high=72), hit_type="staccato", voicing="chord").render(ch, key, dur), 45, 85)
    snare = _cl(SnareDrumGenerator(GeneratorParams(density=0.4), pattern_type="march").render(ch, key, dur), 40, 70)
    return {"Brass": brass, "Hit": hit, "Snare": snare}, 54.0

def t18():
    print("  18. Seat of Infinity — Steps")
    dur, key = 68.0, CS_AE
    ch = _bc("i iv i bVI bVII i III iv v i bVI iv i", dur, key)
    ost = _cl(OstinatoGenerator(GeneratorParams(density=0.45, key_range_low=28, key_range_high=48), pattern="repeated_figure", repeat_notes=4, changed_notes_count=1).render(ch, key, dur), 30, 55)
    pizz = _cl(StringsPizzicatoGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=60), pattern="ostinato", staccato_length=0.08).render(ch, key, dur), 25, 50)
    bsn = _cl(BassoonGenerator(GeneratorParams(density=0.25, key_range_low=34, key_range_high=50), articulation="sustained", vibrato=False, dynamic_curve="flat", note_density=1.0).render(ch, key, dur), 25, 50)
    return {"Ostinato": ost, "Pizzicato": pizz, "Bassoon": bsn}, 36.0

def t19():
    print("  19. Seat — The Unseen")
    dur, key = 74.0, CS_PH
    ch = _bc("i bII i v i bVI bVII i v i bII bVI i v i", dur, key)
    tension = _cl(TensionGenerator(GeneratorParams(density=0.4, key_range_low=28, key_range_high=68), mode="atonal_scatter", note_duration=2.0, velocity_level=0.3, register="low").render(ch, key, dur), 20, 48)
    drone = _cl(DroneGenerator(GeneratorParams(density=0.02, key_range_low=18, key_range_high=30), velocity=35).render(ch, key, dur), 18, 40)
    choir = _cl(ChoirAahsGenerator(GeneratorParams(density=0.3, key_range_low=40, key_range_high=64), voice_count=4, dynamics="pp", vibrato=0.2, syllable="ooh").render(ch, key, dur), 20, 45)
    return {"Tension": tension, "Drone": drone, "Choir": choir}, 44.0

def t20():
    print("  20. Seat — The Final Gate")
    dur, key = 52.0, CS_HM
    ch = _bc("i iv V i bVI bVII V i iv bVI V i", dur, key)
    brass = _cl(BrassSectionGenerator(GeneratorParams(density=0.55, key_range_low=36, key_range_high=72), articulation="sustained", voicing="closed", divisi_count=5).render(ch, key, dur), 40, 80)
    timp = _cl(TimpaniGenerator(GeneratorParams(density=0.5), stroke_pattern="single", drum_count=5).render(ch, key, dur), 40, 75)
    strings = _cl(StringsLegatoGenerator(GeneratorParams(density=0.5, key_range_low=36, key_range_high=76), ensemble_mode="section", dynamic_shape="flat").render(ch, key, dur), 35, 70)
    return {"Brass": brass, "Timpani": timp, "Strings": strings}, 58.0


# ===========================================================================
# IV. COMBAT & CORRUPTION  (tracks 21–25)
# ===========================================================================

def t21():
    print("  21. Clash of Shells")
    dur, key = 56.0, B_HM
    ch = _bc("i iv V i bVI bVII V i iv bVI V i bVII V i", dur, key)
    brass = _cl(BrassSectionGenerator(GeneratorParams(density=0.6, key_range_low=36, key_range_high=76), articulation="sustained", voicing="open", divisi_count=5).render(ch, key, dur), 45, 90)
    snare = _cl(SnareDrumGenerator(GeneratorParams(density=0.45), pattern_type="march").render(ch, key, dur), 45, 75)
    hit = _cl(OrchestralHitGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=76), hit_type="staccato", voicing="chord").render(ch, key, dur), 50, 95)
    strings = _cl(StringsLegatoGenerator(GeneratorParams(density=0.5, key_range_low=40, key_range_high=76), ensemble_mode="section", dynamic_shape="flat").render(ch, key, dur), 35, 75)
    return {"Brass": brass, "Snare": snare, "Hit": hit, "Strings": strings}, 64.0

def t22():
    print("  22. The Corrupted")
    dur, key = 62.0, A_HU
    ch = _bc("i bII iv V i bVI iv bII i V bVI iv i", dur, key)
    tension = _cl(TensionGenerator(GeneratorParams(density=0.45, key_range_low=28, key_range_high=68), mode="chromatic_rise", note_duration=2.0, velocity_level=0.35, register="mid").render(ch, key, dur), 25, 55)
    choir = _cl(ChoirAahsGenerator(GeneratorParams(density=0.4, key_range_low=40, key_range_high=68), voice_count=6, dynamics="mf", vibrato=0.4, syllable="aah").render(ch, key, dur), 30, 65)
    ost = _cl(OstinatoGenerator(GeneratorParams(density=0.5, key_range_low=28, key_range_high=48), pattern="repeated_figure", repeat_notes=3, changed_notes_count=2).render(ch, key, dur), 30, 55)
    timp = _cl(TimpaniGenerator(GeneratorParams(density=0.35), stroke_pattern="roll", drum_count=4).render(ch, key, dur), 35, 65)
    return {"Tension": tension, "Choir": choir, "Ostinato": ost, "Timpani": timp}, 56.0

def t23():
    print("  23. Unchained Fury")
    dur, key = 52.0, B_PD
    ch = _bc("i bII V i iv bVI bII V i iv bVI V i", dur, key)
    brass = _cl(BrassSectionGenerator(GeneratorParams(density=0.6, key_range_low=36, key_range_high=76), articulation="sustained", voicing="open", divisi_count=5).render(ch, key, dur), 50, 95)
    snare = _cl(SnareDrumGenerator(GeneratorParams(density=0.5), pattern_type="march").render(ch, key, dur), 45, 80)
    hit = _cl(OrchestralHitGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=76), hit_type="staccato", voicing="chord").render(ch, key, dur), 55, 100)
    choir = _cl(ChoirAahsGenerator(GeneratorParams(density=0.5, key_range_low=40, key_range_high=72), voice_count=6, dynamics="ff", vibrato=0.5, syllable="aah").render(ch, key, dur), 40, 85)
    return {"Brass": brass, "Snare": snare, "Hit": hit, "Choir": choir}, 68.0

def t24():
    print("  24. The Miasma")
    dur, key = 66.0, E_LOC
    ch = _bc("i bII iv bvii i bv bVI bvii i bII bv i bVI bvii i", dur, key)
    tension = _cl(TensionGenerator(GeneratorParams(density=0.4, key_range_low=28, key_range_high=64), mode="semitone_cluster", note_duration=3.0, velocity_level=0.3, register="low").render(ch, key, dur), 20, 48)
    drone = _cl(DroneGenerator(GeneratorParams(density=0.02, key_range_low=18, key_range_high=30), velocity=35).render(ch, key, dur), 18, 40)
    trem = _cl(TremoloStringsGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=60), bow_speed=0.04, dynamic_swell=True).render(ch, key, dur), 20, 48)
    organ = _cl(OrganDrawbarsGenerator(GeneratorParams(density=0.3, key_range_low=28, key_range_high=56), registration="jazz", leslie_speed="slow", percussion=True).render(ch, key, dur), 20, 45)
    return {"Tension": tension, "Drone": drone, "Tremolo": trem, "Organ": organ}, 48.0

def t25():
    print("  25. Ven, the Husk")
    dur, key = 54.0, B_BYZ
    ch = _bc("i bII V i iv bVI bII V i iv bVI V i", dur, key)
    brass = _cl(BrassSectionGenerator(GeneratorParams(density=0.55, key_range_low=36, key_range_high=72), articulation="sustained", voicing="closed", divisi_count=5).render(ch, key, dur), 45, 85)
    choir = _cl(ChoirAahsGenerator(GeneratorParams(density=0.45, key_range_low=40, key_range_high=68), voice_count=6, dynamics="f", vibrato=0.4, syllable="ooh").render(ch, key, dur), 35, 75)
    snare = _cl(SnareDrumGenerator(GeneratorParams(density=0.4), pattern_type="march").render(ch, key, dur), 40, 70)
    bells = _cl(TubularBellsGenerator(GeneratorParams(density=0.2, key_range_low=60, key_range_high=84), stroke_pattern="chime").render(ch, key, dur), 40, 70)
    return {"Brass": brass, "Choir": choir, "Snare": snare, "Bells": bells}, 60.0


# ===========================================================================
# V. TRANSCENDENCE — Resolution, sacrifice, silence  (tracks 26–30)
# ===========================================================================

def t26():
    print("  26. Shell Mended")
    dur, key = 74.0, A_DOR
    ch = _bc("i IV i V i III VII iv i i IV VII i", dur, key)
    harp = _cl(HarpGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=80), pattern="arpeggio", direction="up", spread_speed=0.15).render(ch, key, dur), 25, 55)
    oboe = _cl(OboeGenerator(GeneratorParams(density=0.45, key_range_low=58, key_range_high=82), articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.5).render(ch, key, dur), 30, 70)
    strings = _cl(StringsLegatoGenerator(GeneratorParams(density=0.4, key_range_low=40, key_range_high=72), ensemble_mode="section", dynamic_shape="crescendo").render(ch, key, dur), 25, 60)
    return {"Harp": harp, "Oboe": oboe, "Strings": strings}, 40.0

def t27():
    print("  27. The Old Prisoner")
    dur, key = 78.0, FS_HM
    ch = _bc("i iv V i bVI bVII V i iv bVI V i bVII V i", dur, key)
    organ = _cl(OrganDrawbarsGenerator(GeneratorParams(density=0.4, key_range_low=28, key_range_high=56), registration="gospel", leslie_speed="slow", percussion=False).render(ch, key, dur), 25, 55)
    bsn = _cl(BassoonGenerator(GeneratorParams(density=0.3, key_range_low=34, key_range_high=50), articulation="sustained", vibrato=False, dynamic_curve="flat", note_density=1.0).render(ch, key, dur), 25, 50)
    drone = _cl(DroneGenerator(GeneratorParams(density=0.02, key_range_low=20, key_range_high=32), velocity=38).render(ch, key, dur), 20, 42)
    return {"Organ": organ, "Bassoon": bsn, "Drone": drone}, 38.0

def t28():
    print("  28. Flesh Remembered")
    dur, key = 72.0, D_AE
    ch = _bc("i iv i bVI bVII i III iv v i bVI iv i", dur, key)
    violin = _cl(ViolinGenerator(GeneratorParams(density=0.4, key_range_low=55, key_range_high=84), articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.5).render(ch, key, dur), 30, 70)
    cello = _cl(CelloGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=56), articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=1.2).render(ch, key, dur), 25, 55)
    canon = _cl(CanonGenerator(GeneratorParams(density=0.35, key_range_low=48, key_range_high=80), canon_type="tonal", delay_beats=4.0, interval=5, num_followers=2).render(ch, key, dur), 25, 55)
    return {"Violins": violin, "Cello": cello, "Canon": canon}, 36.0

def t29():
    print("  29. The Unchained")
    dur = 80.0
    half = dur / 2.0
    dark = _bc("i bII i v i bVI bVII i v i", half, E_PH)
    light = _bc("i IV V I ii IV V I", half, E_DOR)
    ch = dark + light
    canon = _cl(CanonGenerator(GeneratorParams(density=0.5, key_range_low=48, key_range_high=84), canon_type="tonal", delay_beats=4.0, interval=4, num_followers=3).render(ch, E_PH, dur), 30, 75)
    strings = _cl(StringsLegatoGenerator(GeneratorParams(density=0.5, key_range_low=40, key_range_high=76), ensemble_mode="section", dynamic_shape="crescendo").render(ch, E_PH, dur), 25, 70)
    horn = _cl(FrenchHornGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=65), articulation="sustained", dynamic_curve="crescendo", note_density=1.5).render(ch, E_PH, dur), 25, 70)
    timp = _cl(TimpaniGenerator(GeneratorParams(density=0.35), stroke_pattern="single", drum_count=4).render(ch, E_PH, dur), 30, 60)
    harp = _cl(HarpGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=80), pattern="arpeggio", direction="up", spread_speed=0.1).render(ch, E_PH, dur), 25, 55)
    return {"Canon": canon, "Strings": strings, "Horns": horn, "Timpani": timp, "Harp": harp}, 44.0

def t30():
    print("  30. Mortal Shell")
    dur, key = 88.0, BB_AE
    ch = _bc("i iv i bVI bVII i III iv v i bVI iv i bVII i", dur, key)
    chorale = _cl(ChoraleGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=76), voice_spacing=14, soprano_motion="stepwise", rhythmic_unit=2.5).render(ch, key, dur), 25, 60)
    bells = _cl(TubularBellsGenerator(GeneratorParams(density=0.15, key_range_low=60, key_range_high=84), stroke_pattern="chime").render(ch, key, dur), 30, 60)
    choir = _cl(ChoirAahsGenerator(GeneratorParams(density=0.3, key_range_low=40, key_range_high=68), voice_count=4, dynamics="pp", vibrato=0.15, syllable="aah").render(ch, key, dur), 20, 45)
    violin = _cl(ViolinGenerator(GeneratorParams(density=0.25, key_range_low=55, key_range_high=84), articulation="sustained", vibrato=True, dynamic_curve="decrescendo", note_density=0.8).render(ch, key, dur), 20, 55)
    drone = _cl(DroneGenerator(GeneratorParams(density=0.02, key_range_low=22, key_range_high=34), velocity=32).render(ch, key, dur), 18, 38)
    return {"Chorale": chorale, "Bells": bells, "Choir": choir, "Violins": violin, "Drone": drone}, 34.0


# ===========================================================================
# Registry
# ===========================================================================

I = {
    "Cello": 42, "Drone": 43, "Tension": 99, "Tremolo": 44, "Ostinato": 43,
    "Viola": 41, "Pedal": 43, "Harp": 46, "Flute": 73, "Strings": 48,
    "Bassoon": 70, "Pizzicato": 45, "Timpani": 47, "Bass": 43,
    "Chorale": 48, "Horns": 60, "Organ": 19, "Brass": 61, "Choir": 52,
    "Hit": 55, "Snare": 115, "Counterpoint": 40, "Canon": 40, "Bells": 14,
    "WoodwindsEns": 68,
}

TRACKS = [
    # I. Fallgrim
    (t01, "01_Awakening.mid",                      {"Cello": 42, "Drone": 43}),
    (t02, "02_The_Mist_Descends.mid",              {"Tension": 99, "Tremolo": 44}),
    (t03, "03_Fallgrim_Approach.mid",              {"Ostinato": 43, "Viola": 41, "Pedal": 43}),
    (t04, "04_Sesters_Song.mid",                   {"Harp": 46, "Flute": 73, "Strings": 48}),
    (t05, "05_The_Sickened.mid",                   {"Bassoon": 70, "Tension": 99, "Drone": 43}),
    (t06, "06_Swamp_Crossing.mid",                 {"Pizzicato": 45, "Timpani": 47, "Bass": 43}),
    # II. The Shells
    (t07, "07_Harros_the_Vessel.mid",              {"Chorale": 48, "Horns": 60, "Pedal": 43}),
    (t08, "08_Tiel_the_Acolyte.mid",               {"Flute": 73, "Harp": 46, "Strings": 48}),
    (t09, "09_Solomon_the_Scholar.mid",            {"Organ": 19, "Bassoon": 70, "Cello": 42}),
    (t10, "10_Eredrim_the_Last.mid",               {"Brass": 61, "Choir": 52, "Timpani": 47}),
    # III. The Temples
    (t11, "11_Temple_Gate.mid",                    {"Drone": 43, "Choir": 52, "Tension": 99}),
    (t12, "12_Crypt_of_Martyrs_Entrance.mid",      {"Ostinato": 43, "Viola": 41, "Bassoon": 70}),
    (t13, "13_Crypt_The_Warden.mid",               {"Brass": 61, "Snare": 115, "Timpani": 47}),
    (t14, "14_Shrine_of_Ash_Descent.mid",           {"Tension": 99, "Organ": 19, "Counterpoint": 40}),
    (t15, "15_Shrine_The_Fire_Within.mid",          {"Canon": 40, "Harp": 46, "Strings": 48}),
    (t16, "16_Enshrined_Sanctum_Halls.mid",         {"Chorale": 48, "Tremolo": 44, "Pedal": 43}),
    (t17, "17_Sanctum_The_Guardian.mid",            {"Brass": 61, "Hit": 55, "Snare": 115}),
    (t18, "18_Seat_of_Infinity_Steps.mid",          {"Ostinato": 43, "Pizzicato": 45, "Bassoon": 70}),
    (t19, "19_Seat_The_Unseen.mid",                 {"Tension": 99, "Drone": 43, "Choir": 52}),
    (t20, "20_Seat_The_Final_Gate.mid",             {"Brass": 61, "Timpani": 47, "Strings": 48}),
    # IV. Combat & Corruption
    (t21, "21_Clash_of_Shells.mid",                 {"Brass": 61, "Snare": 115, "Hit": 55, "Strings": 48}),
    (t22, "22_The_Corrupted.mid",                   {"Tension": 99, "Choir": 52, "Ostinato": 43, "Timpani": 47}),
    (t23, "23_Unchained_Fury.mid",                  {"Brass": 61, "Snare": 115, "Hit": 55, "Choir": 52}),
    (t24, "24_The_Miasma.mid",                      {"Tension": 99, "Drone": 43, "Tremolo": 44, "Organ": 19}),
    (t25, "25_Ven_the_Husk.mid",                    {"Brass": 61, "Choir": 52, "Snare": 115, "Bells": 14}),
    # V. Transcendence
    (t26, "26_Shell_Mended.mid",                    {"Harp": 46, "Oboe": 68, "Strings": 48}),
    (t27, "27_The_Old_Prisoner.mid",                {"Organ": 19, "Bassoon": 70, "Drone": 43}),
    (t28, "28_Flesh_Remembered.mid",                {"Violins": 40, "Cello": 42, "Canon": 40}),
    (t29, "29_The_Unchained.mid",                   {"Canon": 40, "Strings": 48, "Horns": 60, "Timpani": 47, "Harp": 46}),
    (t30, "30_Mortal_Shell.mid",                    {"Chorale": 48, "Bells": 14, "Choir": 52, "Violins": 40, "Drone": 43}),
]


def main():
    album_dir = Path("output/album_mortal_shell")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("      M O R T A L   S H E L L :   E C H O E S   O F   F L E S H")
    print("      A 30-Movement Dark Atmospheric Orchestral Suite (~90 min)")
    print("      I: Fallgrim | II: The Shells | III: The Temples")
    print("      IV: Combat & Corruption | V: Transcendence")
    print("=" * 80)

    total_notes = 0
    for i, (producer, filename, instruments) in enumerate(TRACKS):
        print("-" * 80)
        raw, bpm = producer()
        desk = MixingDesk(niche_cfg={})
        for k in raw:
            desk.track_gains.setdefault(k, 0.78)
        mixed = desk.apply_mixing(raw, [], int(bpm))
        m = MasteringDesk(target_lufs=-16.0)
        mastered, pan = m.apply_mastering(mixed)

        export_multitrack_midi(
            mastered,
            str(album_dir / filename),
            bpm=bpm,
            cc_events=pan,
            instruments=instruments,
        )
        note_count = sum(len(n) for n in raw.values())
        total_notes += note_count
        print(f"    -> {filename}  ({note_count} notes, {bpm} BPM)")

    print()
    print("=" * 80)
    print(f"  COMPLETE: Mortal Shell — Echoes of Flesh")
    print(f"  {total_notes} total notes across 30 movements")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
