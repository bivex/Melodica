# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_sixty_six_days.py — SIXTY-SIX DAYS: THE ORDER

A 20-movement dark cinematic orchestral album (~60 min) telling the story of
You're Soul, an elite assassin of The Order, framed for the patriarch's murder,
given 66 days of borrowed life to uncover the truth.

Five acts:
    I.   The Blade That Betrayed  (framing, flight, near-death, the healer's bargain)
    II.  The Waning Clock         (investigation, paranoia, the first clues)
    III. Bloodhounds & Monstrosities  (pursuit, inhuman foes, escalating danger)
    IV.  The Puppet Master        (revelation, conspiracy, the true enemy)
    V.   Day Sixty-Six            (confrontation, resolution, the final breath)

Modes: PHRYGIAN, AEOLIAN, HARMONIC_MINOR, LOCRIAN, DORIAN, PHRYGIAN_DOMINANT,
       DOUBLE_HARMONIC, MELODIC_MINOR, HUNGARIAN_MINOR, BYZANTINE.
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

E_PD   = Scale(4,  Mode.PHRYGIAN_DOMINANT)
A_PD   = Scale(9,  Mode.PHRYGIAN_DOMINANT)
B_PD   = Scale(11, Mode.PHRYGIAN_DOMINANT)
D_PD   = Scale(2,  Mode.PHRYGIAN_DOMINANT)

A_DBH  = Scale(9,  Mode.DOUBLE_HARMONIC)
E_DBH  = Scale(4,  Mode.DOUBLE_HARMONIC)

E_MEL  = Scale(4,  Mode.MELODIC_MINOR)
B_MEL  = Scale(11, Mode.MELODIC_MINOR)

E_HU   = Scale(4,  Mode.HUNGARIAN_MINOR)
A_HU   = Scale(9,  Mode.HUNGARIAN_MINOR)
B_HU   = Scale(11, Mode.HUNGARIAN_MINOR)

A_BYZ  = Scale(9,  Mode.BYZANTINE)
B_BYZ  = Scale(11, Mode.BYZANTINE)


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


# ===========================================================================
# I. THE BLADE THAT BETRAYED — Framing, flight, near-death  (tracks 1–4)
# ===========================================================================

def t01():
    """The Order — The patriarch's chamber, the blood on his hands, the alarm."""
    print("  01. Blood on the Altar")
    dur, key = 72.0, E_PH
    ch = _bc("i bII i v i bVI bVII i v i bII bVI i", dur, key)
    cello = _cl(CelloGenerator(GeneratorParams(density=0.3, key_range_low=36, key_range_high=55), articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.0).render(ch, key, dur), 30, 65)
    drone = _cl(DroneGenerator(GeneratorParams(density=0.02, key_range_low=20, key_range_high=32), velocity=40).render(ch, key, dur), 20, 45)
    tension = _cl(TensionGenerator(GeneratorParams(density=0.25, key_range_low=32, key_range_high=64), mode="major7_tension", note_duration=4.0, velocity_level=0.25, register="low").render(ch, key, dur), 20, 45)
    return {"Cello": cello, "Drone": drone, "Tension": tension}, 38.0

def t02():
    """The manhunt — Steel and shadow close in from all sides."""
    print("  02. The Hounds Are Loosed")
    dur, key = 56.0, B_HM
    ch = _bc("i iv V i bVI bVII V i iv bVI V i bVII V i", dur, key)
    brass = _cl(BrassSectionGenerator(GeneratorParams(density=0.55, key_range_low=36, key_range_high=72), articulation="sustained", voicing="closed", divisi_count=4).render(ch, key, dur), 40, 80)
    snare = _cl(SnareDrumGenerator(GeneratorParams(density=0.45), pattern_type="march").render(ch, key, dur), 40, 70)
    timp = _cl(TimpaniGenerator(GeneratorParams(density=0.4), stroke_pattern="single", drum_count=5).render(ch, key, dur), 40, 75)
    return {"Brass": brass, "Snare": snare, "Timpani": timp}, 62.0

def t03():
    """Gravely wounded — Bleeding out in the rain, the world dimming."""
    print("  03. A Thousand Cuts")
    dur, key = 68.0, D_LOC
    ch = _bc("i bII bv bvii i bII bv i bvii i bII bv bvii i", dur, key)
    trem = _cl(TremoloStringsGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=60), bow_speed=0.0625, dynamic_swell=True).render(ch, key, dur), 20, 45)
    tension = _cl(TensionGenerator(GeneratorParams(density=0.3, key_range_low=28, key_range_high=68), mode="chromatic_fall", note_duration=3.0, velocity_level=0.25, register="low").render(ch, key, dur), 20, 48)
    bsn = _cl(BassoonGenerator(GeneratorParams(density=0.25, key_range_low=34, key_range_high=50), articulation="sustained", vibrato=False, dynamic_curve="flat", note_density=1.0).render(ch, key, dur), 25, 50)
    return {"Tremolo": trem, "Tension": tension, "Bassoon": bsn}, 42.0

def t04():
    """The mystic healer — Sixty-six days, no more. The bargain is struck."""
    print("  04. The Healer's Bargain")
    dur, key = 76.0, FS_AE
    ch = _bc("i iv i bVI bVII i III iv i bVI iv i bVII i", dur, key)
    harp = _cl(HarpGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=80), pattern="arpeggio", direction="up", spread_speed=0.15).render(ch, key, dur), 25, 55)
    oboe = _cl(OboeGenerator(GeneratorParams(density=0.4, key_range_low=58, key_range_high=82), articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.3).render(ch, key, dur), 30, 65)
    strings = _cl(StringsLegatoGenerator(GeneratorParams(density=0.35, key_range_low=44, key_range_high=72), ensemble_mode="section", dynamic_shape="crescendo").render(ch, key, dur), 25, 55)
    choir = _cl(ChoirAahsGenerator(GeneratorParams(density=0.3, key_range_low=40, key_range_high=64), voice_count=4, dynamics="pp", vibrato=0.15, syllable="aah").render(ch, key, dur), 20, 45)
    return {"Harp": harp, "Oboe": oboe, "Strings": strings, "Choir": choir}, 40.0


# ===========================================================================
# II. THE WANING CLOCK — Investigation, paranoia, first clues  (tracks 5–8)
# ===========================================================================

def t05():
    """Day 1 — The countdown begins. Every heartbeat is borrowed time."""
    print("  05. Borrowed Time")
    dur, key = 64.0, A_PH
    ch = _bc("i bII i v bVII bVI bVII i v i bII v i", dur, key)
    ost = _cl(OstinatoGenerator(GeneratorParams(density=0.45, key_range_low=28, key_range_high=48), pattern="repeated_figure", repeat_notes=3, changed_notes_count=2).render(ch, key, dur), 30, 55)
    pizz = _cl(StringsPizzicatoGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=60), pattern="ostinato", staccato_length=0.08).render(ch, key, dur), 30, 55)
    viola = _cl(ViolaGenerator(GeneratorParams(density=0.35, key_range_low=48, key_range_high=68), articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=1.0).render(ch, key, dur), 25, 55)
    return {"Ostinato": ost, "Pizzicato": pizz, "Viola": viola}, 50.0

def t06():
    """The Order's archive — Ancient texts, half-truths, betrayal in ink."""
    print("  06. Archives of the Damned")
    dur, key = 70.0, EF_AE
    ch = _bc("i iv i bVI bVII i III iv v i bVI iv i bVII i", dur, key)
    organ = _cl(OrganDrawbarsGenerator(GeneratorParams(density=0.4, key_range_low=28, key_range_high=56), registration="gospel", leslie_speed="slow", percussion=False).render(ch, key, dur), 25, 55)
    bsn = _cl(BassoonGenerator(GeneratorParams(density=0.3, key_range_low=34, key_range_high=52), articulation="sustained", vibrato=False, dynamic_curve="flat", note_density=1.2).render(ch, key, dur), 25, 50)
    cello = _cl(CelloGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=56), articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=1.2).render(ch, key, dur), 25, 55)
    return {"Organ": organ, "Bassoon": bsn, "Cello": cello}, 44.0

def t07():
    """The first thread — A name, a face, a shadow behind the throne."""
    print("  07. A Thread in the Dark")
    dur, key = 66.0, A_DOR
    ch = _bc("i IV i V i III VII iv i i IV VII i III IV V i", dur, key)
    flute = _cl(FluteGenerator(GeneratorParams(density=0.45, key_range_low=60, key_range_high=90), articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.5).render(ch, key, dur), 30, 65)
    harp = _cl(HarpGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=80), pattern="arpeggio", direction="up", spread_speed=0.12).render(ch, key, dur), 25, 50)
    strings = _cl(StringsLegatoGenerator(GeneratorParams(density=0.4, key_range_low=40, key_range_high=72), ensemble_mode="section", dynamic_shape="crescendo").render(ch, key, dur), 25, 60)
    return {"Flute": flute, "Harp": harp, "Strings": strings}, 52.0

def t08():
    """Day 22 — Paranoia. Trust no one. The walls have ears of steel."""
    print("  08. Ears of Steel")
    dur, key = 58.0, FS_PH
    ch = _bc("i bII i v i bVI bVII i v i bII bVI i v i", dur, key)
    tension = _cl(TensionGenerator(GeneratorParams(density=0.4, key_range_low=28, key_range_high=68), mode="tritone_pulse", note_duration=2.5, velocity_level=0.3, register="mid").render(ch, key, dur), 25, 55)
    trem = _cl(TremoloStringsGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=60), bow_speed=0.04, dynamic_swell=True).render(ch, key, dur), 20, 48)
    pizz = _cl(StringsPizzicatoGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=60), pattern="ostinato", staccato_length=0.1).render(ch, key, dur), 25, 50)
    return {"Tension": tension, "Tremolo": trem, "Pizzicato": pizz}, 54.0


# ===========================================================================
# III. BLOODHOUNDS & MONSTROSITIES — Pursuit, inhuman foes  (tracks 9–12)
# ===========================================================================

def t09():
    """The first abomination — Something that was once human, twisted beyond recognition."""
    print("  09. The Thing That Was Once a Man")
    dur, key = 52.0, E_HU
    ch = _bc("i bII iv V i bVI iv bII i V bVI iv i bII V i", dur, key)
    brass = _cl(BrassSectionGenerator(GeneratorParams(density=0.55, key_range_low=36, key_range_high=72), articulation="sustained", voicing="closed", divisi_count=4).render(ch, key, dur), 40, 80)
    hit = _cl(OrchestralHitGenerator(GeneratorParams(density=0.3, key_range_low=36, key_range_high=72), hit_type="staccato", voicing="chord").render(ch, key, dur), 45, 85)
    snare = _cl(SnareDrumGenerator(GeneratorParams(density=0.4), pattern_type="march").render(ch, key, dur), 40, 70)
    tension = _cl(TensionGenerator(GeneratorParams(density=0.35, key_range_low=28, key_range_high=64), mode="atonal_scatter", note_duration=2.0, velocity_level=0.3, register="low").render(ch, key, dur), 20, 50)
    return {"Brass": brass, "Hit": hit, "Snare": snare, "Tension": tension}, 66.0

def t10():
    """A narrow escape — Through catacombs wet with something that isn't water."""
    print("  10. The Catacombs")
    dur, key = 60.0, B_LOC
    ch = _bc("i bII iv bvii i bv bVI bvii i bII bv i bVI bvii i", dur, key)
    drone = _cl(DroneGenerator(GeneratorParams(density=0.02, key_range_low=18, key_range_high=30), velocity=35).render(ch, key, dur), 18, 40)
    ost = _cl(OstinatoGenerator(GeneratorParams(density=0.45, key_range_low=28, key_range_high=48), pattern="repeated_figure", repeat_notes=4, changed_notes_count=1).render(ch, key, dur), 30, 55)
    trem = _cl(TremoloStringsGenerator(GeneratorParams(density=0.3, key_range_low=36, key_range_high=60), bow_speed=0.04, dynamic_swell=True).render(ch, key, dur), 20, 45)
    bsn = _cl(BassoonGenerator(GeneratorParams(density=0.25, key_range_low=34, key_range_high=50), articulation="staccato", vibrato=False, dynamic_curve="flat", note_density=1.2).render(ch, key, dur), 25, 50)
    return {"Drone": drone, "Ostinato": ost, "Tremolo": trem, "Bassoon": bsn}, 48.0

def t11():
    """Day 44 — The clock is half-spent. The cure flickers. The beasts multiply."""
    print("  11. Half the Sand")
    dur, key = 64.0, D_HM
    ch = _bc("i iv V i bVI bVII V i iv bVI V i bVII V i", dur, key)
    chorale = _cl(ChoraleGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=72), voice_spacing=12, soprano_motion="stepwise", rhythmic_unit=2.0).render(ch, key, dur), 25, 60)
    horn = _cl(FrenchHornGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=60), articulation="sustained", dynamic_curve="crescendo", note_density=1.5).render(ch, key, dur), 30, 65)
    timp = _cl(TimpaniGenerator(GeneratorParams(density=0.35), stroke_pattern="roll", drum_count=4).render(ch, key, dur), 35, 60)
    return {"Chorale": chorale, "Horns": horn, "Timpani": timp}, 50.0

def t12():
    """The apex predator — A monstrosity that hunts the hunters."""
    print("  12. The Apex")
    dur, key = 48.0, A_DBH
    ch = _bc("i bII V i iv bVI bII V i iv bVI V i bII V i", dur, key)
    brass = _cl(BrassSectionGenerator(GeneratorParams(density=0.6, key_range_low=36, key_range_high=76), articulation="sustained", voicing="open", divisi_count=5).render(ch, key, dur), 50, 95)
    snare = _cl(SnareDrumGenerator(GeneratorParams(density=0.5), pattern_type="march").render(ch, key, dur), 45, 80)
    hit = _cl(OrchestralHitGenerator(GeneratorParams(density=0.35, key_range_low=36, key_range_high=76), hit_type="staccato", voicing="chord").render(ch, key, dur), 55, 100)
    choir = _cl(ChoirAahsGenerator(GeneratorParams(density=0.45, key_range_low=40, key_range_high=72), voice_count=6, dynamics="ff", vibrato=0.5, syllable="aah").render(ch, key, dur), 40, 85)
    return {"Brass": brass, "Snare": snare, "Hit": hit, "Choir": choir}, 72.0


# ===========================================================================
# IV. THE PUPPET MASTER — Revelation, conspiracy, the true enemy  (tracks 13–16)
# ===========================================================================

def t13():
    """Day 55 — The mask slips. A trusted face behind the frame."""
    print("  13. The Mask Slips")
    dur, key = 66.0, EF_HM
    ch = _bc("i iv V i bVI bVII V i iv bVI V i bVII V i", dur, key)
    cp = _cl(CounterpointGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=68), species=3, voices=2).render(ch, key, dur), 25, 55)
    organ = _cl(OrganDrawbarsGenerator(GeneratorParams(density=0.35, key_range_low=28, key_range_high=56), registration="jazz", leslie_speed="slow", percussion=True).render(ch, key, dur), 20, 50)
    viola = _cl(ViolaGenerator(GeneratorParams(density=0.3, key_range_low=48, key_range_high=68), articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.0).render(ch, key, dur), 25, 55)
    return {"Counterpoint": cp, "Organ": organ, "Viola": viola}, 46.0

def t14():
    """The conspiracy unfolds — Every ally was a pawn. Every mercy was a leash."""
    print("  14. All Pawns, No King")
    dur, key = 58.0, B_BYZ
    ch = _bc("i bII V i iv bVI bII V i iv bVI V i bII V i", dur, key)
    tension = _cl(TensionGenerator(GeneratorParams(density=0.45, key_range_low=28, key_range_high=68), mode="chromatic_rise", note_duration=2.0, velocity_level=0.35, register="mid").render(ch, key, dur), 25, 55)
    brass = _cl(BrassSectionGenerator(GeneratorParams(density=0.5, key_range_low=36, key_range_high=72), articulation="sustained", voicing="closed", divisi_count=4).render(ch, key, dur), 35, 75)
    ost = _cl(OstinatoGenerator(GeneratorParams(density=0.5, key_range_low=28, key_range_high=48), pattern="repeated_figure", repeat_notes=3, changed_notes_count=2).render(ch, key, dur), 30, 55)
    timp = _cl(TimpaniGenerator(GeneratorParams(density=0.35), stroke_pattern="roll", drum_count=4).render(ch, key, dur), 35, 65)
    return {"Tension": tension, "Brass": brass, "Ostinato": ost, "Timpani": timp}, 56.0

def t15():
    """The name spoken aloud — The patriarch's own blood orchestrated his fall."""
    print("  15. Blood of the Patriarch")
    dur, key = 62.0, CS_HM
    ch = _bc("i iv V i bVI bVII V i iv bVI V i bVII V i", dur, key)
    chorale = _cl(ChoraleGenerator(GeneratorParams(density=0.4, key_range_low=32, key_range_high=72), voice_spacing=14, soprano_motion="stepwise", rhythmic_unit=2.5).render(ch, key, dur), 30, 70)
    horn = _cl(FrenchHornGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=65), articulation="sustained", dynamic_curve="crescendo", note_density=1.5).render(ch, key, dur), 30, 70)
    strings = _cl(StringsLegatoGenerator(GeneratorParams(density=0.45, key_range_low=40, key_range_high=72), ensemble_mode="section", dynamic_shape="crescendo").render(ch, key, dur), 30, 65)
    return {"Chorale": chorale, "Horns": horn, "Strings": strings}, 48.0

def t16():
    """Day 60 — The final approach. Six days remain. No more room for doubt."""
    print("  16. Six Days")
    dur, key = 54.0, A_PD
    ch = _bc("i bII V i iv bVI bII V i iv bVI V i bII V i", dur, key)
    brass = _cl(BrassSectionGenerator(GeneratorParams(density=0.55, key_range_low=36, key_range_high=72), articulation="sustained", voicing="open", divisi_count=5).render(ch, key, dur), 45, 85)
    timp = _cl(TimpaniGenerator(GeneratorParams(density=0.5), stroke_pattern="single", drum_count=5).render(ch, key, dur), 40, 80)
    snare = _cl(SnareDrumGenerator(GeneratorParams(density=0.4), pattern_type="march").render(ch, key, dur), 40, 70)
    strings = _cl(StringsLegatoGenerator(GeneratorParams(density=0.5, key_range_low=40, key_range_high=76), ensemble_mode="section", dynamic_shape="flat").render(ch, key, dur), 35, 70)
    return {"Brass": brass, "Timpani": timp, "Snare": snare, "Strings": strings}, 64.0


# ===========================================================================
# V. DAY SIXTY-SIX — Confrontation, resolution, the final breath  (tracks 17–20)
# ===========================================================================

def t17():
    """The citadel — The puppet master's fortress. Steel and shadow given form."""
    print("  17. The Citadel of Shadows")
    dur, key = 56.0, E_DBH
    ch = _bc("i bII V i iv bVI bII V i iv bVI V i bII V i", dur, key)
    tension = _cl(TensionGenerator(GeneratorParams(density=0.4, key_range_low=28, key_range_high=68), mode="semitone_cluster", note_duration=3.0, velocity_level=0.3, register="low").render(ch, key, dur), 20, 50)
    drone = _cl(DroneGenerator(GeneratorParams(density=0.02, key_range_low=20, key_range_high=32), velocity=38).render(ch, key, dur), 20, 42)
    choir = _cl(ChoirAahsGenerator(GeneratorParams(density=0.35, key_range_low=40, key_range_high=68), voice_count=4, dynamics="mp", vibrato=0.3, syllable="ooh").render(ch, key, dur), 25, 55)
    organ = _cl(OrganDrawbarsGenerator(GeneratorParams(density=0.35, key_range_low=28, key_range_high=56), registration="rock", leslie_speed="fast", percussion=True).render(ch, key, dur), 25, 55)
    return {"Tension": tension, "Drone": drone, "Choir": choir, "Organ": organ}, 52.0

def t18():
    """The confrontation — Blade to blade with the architect of ruin."""
    print("  18. The Architect Falls")
    dur, key = 46.0, B_HM
    ch = _bc("i iv V i bVI bVII V i iv bVI V i", dur, key)
    brass = _cl(BrassSectionGenerator(GeneratorParams(density=0.6, key_range_low=36, key_range_high=76), articulation="sustained", voicing="open", divisi_count=5).render(ch, key, dur), 50, 95)
    hit = _cl(OrchestralHitGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=76), hit_type="staccato", voicing="chord").render(ch, key, dur), 55, 100)
    snare = _cl(SnareDrumGenerator(GeneratorParams(density=0.5), pattern_type="march").render(ch, key, dur), 45, 80)
    timp = _cl(TimpaniGenerator(GeneratorParams(density=0.5), stroke_pattern="single", drum_count=5).render(ch, key, dur), 45, 85)
    choir = _cl(ChoirAahsGenerator(GeneratorParams(density=0.5, key_range_low=40, key_range_high=72), voice_count=6, dynamics="ff", vibrato=0.5, syllable="aah").render(ch, key, dur), 40, 90)
    return {"Brass": brass, "Hit": hit, "Snare": snare, "Timpani": timp, "Choir": choir}, 78.0

def t19():
    """The truth revealed — The patriarch lives. The frame was the test."""
    print("  19. The Patriarch Lives")
    dur, key = 74.0, E_DOR
    ch = _bc("i IV V I ii IV V I i IV V I iii IV V I", dur, key)
    canon = _cl(CanonGenerator(GeneratorParams(density=0.5, key_range_low=48, key_range_high=84), canon_type="tonal", delay_beats=4.0, interval=4, num_followers=3).render(ch, key, dur), 30, 75)
    strings = _cl(StringsLegatoGenerator(GeneratorParams(density=0.5, key_range_low=40, key_range_high=76), ensemble_mode="section", dynamic_shape="crescendo").render(ch, key, dur), 25, 70)
    horn = _cl(FrenchHornGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=65), articulation="sustained", dynamic_curve="crescendo", note_density=1.5).render(ch, key, dur), 25, 70)
    harp = _cl(HarpGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=80), pattern="arpeggio", direction="up", spread_speed=0.1).render(ch, key, dur), 25, 55)
    timp = _cl(TimpaniGenerator(GeneratorParams(density=0.35), stroke_pattern="single", drum_count=4).render(ch, key, dur), 30, 60)
    return {"Canon": canon, "Strings": strings, "Horns": horn, "Harp": harp, "Timpani": timp}, 48.0

def t20():
    """Day 66 — The cure fades. The last breath. The soul, at last, is free."""
    print("  20. Day Sixty-Six")
    dur, key = 84.0, BB_AE
    ch = _bc("i iv i bVI bVII i III iv v i bVI iv i bVII i", dur, key)
    chorale = _cl(ChoraleGenerator(GeneratorParams(density=0.4, key_range_low=36, key_range_high=76), voice_spacing=14, soprano_motion="stepwise", rhythmic_unit=2.5).render(ch, key, dur), 25, 60)
    bells = _cl(TubularBellsGenerator(GeneratorParams(density=0.15, key_range_low=60, key_range_high=84), stroke_pattern="chime").render(ch, key, dur), 30, 60)
    choir = _cl(ChoirAahsGenerator(GeneratorParams(density=0.3, key_range_low=40, key_range_high=68), voice_count=4, dynamics="pp", vibrato=0.15, syllable="aah").render(ch, key, dur), 20, 45)
    violin = _cl(ViolinGenerator(GeneratorParams(density=0.25, key_range_low=55, key_range_high=84), articulation="sustained", vibrato=True, dynamic_curve="decrescendo", note_density=0.8).render(ch, key, dur), 20, 55)
    drone = _cl(DroneGenerator(GeneratorParams(density=0.02, key_range_low=22, key_range_high=34), velocity=32).render(ch, key, dur), 18, 38)
    return {"Chorale": chorale, "Bells": bells, "Choir": choir, "Violins": violin, "Drone": drone}, 36.0


# ===========================================================================
# Registry
# ===========================================================================

TRACKS = [
    # I. The Blade That Betrayed
    (t01, "01_Blood_on_the_Altar.mid",         {"Cello": 42, "Drone": 43, "Tension": 99}),
    (t02, "02_The_Hounds_Are_Loosed.mid",      {"Brass": 61, "Snare": 115, "Timpani": 47}),
    (t03, "03_A_Thousand_Cuts.mid",             {"Tremolo": 44, "Tension": 99, "Bassoon": 70}),
    (t04, "04_The_Healers_Bargain.mid",         {"Harp": 46, "Oboe": 68, "Strings": 48, "Choir": 52}),
    # II. The Waning Clock
    (t05, "05_Borrowed_Time.mid",               {"Ostinato": 43, "Pizzicato": 45, "Viola": 41}),
    (t06, "06_Archives_of_the_Damned.mid",      {"Organ": 19, "Bassoon": 70, "Cello": 42}),
    (t07, "07_A_Thread_in_the_Dark.mid",        {"Flute": 73, "Harp": 46, "Strings": 48}),
    (t08, "08_Ears_of_Steel.mid",               {"Tension": 99, "Tremolo": 44, "Pizzicato": 45}),
    # III. Bloodhounds & Monstrosities
    (t09, "09_The_Thing_That_Was_Once_a_Man.mid", {"Brass": 61, "Hit": 55, "Snare": 115, "Tension": 99}),
    (t10, "10_The_Catacombs.mid",               {"Drone": 43, "Ostinato": 43, "Tremolo": 44, "Bassoon": 70}),
    (t11, "11_Half_the_Sand.mid",               {"Chorale": 48, "Horns": 60, "Timpani": 47}),
    (t12, "12_The_Apex.mid",                    {"Brass": 61, "Snare": 115, "Hit": 55, "Choir": 52}),
    # IV. The Puppet Master
    (t13, "13_The_Mask_Slips.mid",              {"Counterpoint": 40, "Organ": 19, "Viola": 41}),
    (t14, "14_All_Pawns_No_King.mid",           {"Tension": 99, "Brass": 61, "Ostinato": 43, "Timpani": 47}),
    (t15, "15_Blood_of_the_Patriarch.mid",      {"Chorale": 48, "Horns": 60, "Strings": 48}),
    (t16, "16_Six_Days.mid",                    {"Brass": 61, "Timpani": 47, "Snare": 115, "Strings": 48}),
    # V. Day Sixty-Six
    (t17, "17_The_Citadel_of_Shadows.mid",      {"Tension": 99, "Drone": 43, "Choir": 52, "Organ": 19}),
    (t18, "18_The_Architect_Falls.mid",         {"Brass": 61, "Hit": 55, "Snare": 115, "Timpani": 47, "Choir": 52}),
    (t19, "19_The_Patriarch_Lives.mid",         {"Canon": 40, "Strings": 48, "Horns": 60, "Harp": 46, "Timpani": 47}),
    (t20, "20_Day_Sixty_Six.mid",               {"Chorale": 48, "Bells": 14, "Choir": 52, "Violins": 40, "Drone": 43}),
]


def main():
    album_dir = Path("output/album_sixty_six_days")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("      S I X T Y - S I X   D A Y S :   T H E   O R D E R")
    print("      A 20-Movement Dark Cinematic Orchestral Suite (~60 min)")
    print("      I: The Blade That Betrayed | II: The Waning Clock")
    print("      III: Bloodhounds & Monstrosities | IV: The Puppet Master")
    print("      V: Day Sixty-Six")
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
    print(f"  COMPLETE: Sixty-Six Days — The Order")
    print(f"  {total_notes} total notes across 20 movements")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
