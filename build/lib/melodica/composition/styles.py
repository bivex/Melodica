# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

from melodica.composition import Style
from melodica.types import Scale, Mode

# ---------------------------------------------------------------------------
# Dark Fantasy (existing)
# ---------------------------------------------------------------------------

DARK_FANTASY_STYLE = Style(
    name="Dark Fantasy",
    allowed_scales=[
        Scale(9, Mode.NATURAL_MINOR),  # A Minor
        Scale(4, Mode.HARMONIC_MINOR),  # E Harmonic Minor
        Scale(2, Mode.MESSIAEN_2),  # D Messiaen 2
        Scale(7, Mode.PHRYGIAN),  # G Phrygian
    ],
    track_mapping={
        "Pads": "ambient_pad",
        "Lead": "lead_melody",
        "Bass": "followed_bass",
        "Texture": "fast_arp",
        "Percussion": "orch_timpani_bass",
    },
    instrument_mapping={
        "Pads": 48,  # String Ensemble
        "Lead": 73,  # Flute
        "Bass": 32,  # Acoustic Bass
        "Texture": 11,  # Vibraphone
        "Percussion": 47,  # Timpani
    },
    progressions={
        "Intro": ["Im", "Im VI", "Im VII", "Im bII"],
        "Main": ["Im VI III VII", "Im IVm VII Im", "Im bII Im", "Im IIIb VI VII"],
        "Battle": ["Im bII Im VIIb", "Im VI IVm V", "Im IVm VII IIIb VI V", "Im bVI bIII bVII Im"],
        "Exploration": ["Im IVm VII IIIb", "Im VI VII Im", "Im bIII bVII IVm"],
        "Mystery": ["Im bII", "Im VII VI", "Im bVI bIII", "Im bII Im VII"],
        "Outro": ["Im", "Im VII VI V", "Im IVm Im", "Im bII Im"],
    },
    typical_bpm=70.0,
)

SYMPHONIC_DARK_FANTASY_STYLE = Style(
    name="Symphonic Dark Fantasy",
    allowed_scales=[
        Scale(2, Mode.MESSIAEN_2),
        Scale(4, Mode.HARMONIC_MINOR),
    ],
    track_mapping={
        "Violins_I": "orch_violins_i_melody",
        "Violins_II": "orch_violins_ii_chords",
        "Viola": "orch_viola_chords",
        "Cello": "orch_cello_bass",
        "Contrabass": "orch_contrabass_bass",
        "Flute": "orch_flute_arp",
        "Oboe": "orch_oboe_melody",
        "Horn": "orch_horn_chords",
        "Trumpet": "orch_trumpet_melody",
        "Trombone": "orch_trombone_bass",
        "Timpani": "orch_timpani_bass",
        "Harp": "orch_harp_arp",
    },
    instrument_mapping={
        "Violins_I": 40,
        "Violins_II": 40,
        "Viola": 41,
        "Cello": 42,
        "Contrabass": 43,
        "Flute": 73,
        "Oboe": 68,
        "Horn": 60,
        "Trumpet": 56,
        "Trombone": 57,
        "Timpani": 47,
        "Harp": 46,
    },
    progressions={
        "Intro": ["Im", "Im bII", "Im VII"],
        "Theme_A": ["Im VI III VII", "Im IVm VII Im"],
        "Climax": ["Im bII Im VIIb", "Im VI IVm V"],
        "Outro": ["Im", "Im VII VI V", "Im IVm Im"],
    },
    typical_bpm=65.0,
)

# ---------------------------------------------------------------------------
# Classical
# ---------------------------------------------------------------------------

CLASSICAL_STYLE = Style(
    name="Classical",
    allowed_scales=[
        Scale(0, Mode.MAJOR),  # C Major
        Scale(7, Mode.MAJOR),  # G Major
        Scale(2, Mode.NATURAL_MINOR),  # D Minor
        Scale(9, Mode.HARMONIC_MINOR),  # A Harmonic Minor
    ],
    track_mapping={
        "Melody": "orch_violins_i_melody",
        "Harmony": "orch_viola_chords",
        "Bass": "orch_cello_bass",
        "Arp": "orch_harp_arp",
    },
    instrument_mapping={
        "Melody": 40,  # Violin
        "Harmony": 41,  # Viola
        "Bass": 42,  # Cello
        "Arp": 46,  # Harp
    },
    progressions={
        "Intro": ["I", "I IV V I", "I V I"],
        "Theme_A": ["I IV V I", "I vi IV V", "I V vi iii IV I V"],
        "Theme_B": ["vi IV I V", "ii V I vi", "IV V I iii"],
        "Recap": ["I IV V I", "I V I"],
        "Coda": ["I", "I64 V I", "V I"],
    },
    typical_bpm=100.0,
)

# ---------------------------------------------------------------------------
# Jazz
# ---------------------------------------------------------------------------

JAZZ_STYLE = Style(
    name="Jazz",
    allowed_scales=[
        Scale(0, Mode.BEBOP_DOMINANT),  # C Bebop Dominant
        Scale(9, Mode.BEBOP_MAJOR),  # A Bebop Major
        Scale(9, Mode.DORIAN),  # A Dorian
        Scale(0, Mode.MIXOLYDIAN),  # C Mixolydian
    ],
    track_mapping={
        "Melody": "lead_melody",
        "Chords": "followed_chords",
        "Bass": "madonna_groove",
        "Arp": "fast_arp",
    },
    instrument_mapping={
        "Melody": 65,  # Alto Sax
        "Chords": 1,  # Acoustic Grand Piano
        "Bass": 32,  # Acoustic Bass
        "Arp": 24,  # Acoustic Guitar (nylon)
    },
    progressions={
        "Head": ["Imaj7 vi7 ii7 V7", "Imaj7 iii7 vi7 ii7 V7", "I7 IV7 I7 V7"],
        "Solo_A": ["ii7 V7 Imaj7 vi7", "iii7 VI7 ii7 V7", "I7 IV7 I7"],
        "Solo_B": ["vi7 ii7 V7 Imaj7", "IV7 bVIIdim7 Imaj7 V7"],
        "Outro": ["Imaj7", "I6 Imaj7 I6 Imaj7", "ii7 V7 Imaj7"],
    },
    typical_bpm=140.0,
)

# ---------------------------------------------------------------------------
# Film Score
# ---------------------------------------------------------------------------

FILM_STYLE = Style(
    name="Film Score",
    allowed_scales=[
        Scale(0, Mode.MAJOR),  # C Major (heroic)
        Scale(9, Mode.NATURAL_MINOR),  # A Minor (tension)
        Scale(7, Mode.HARMONIC_MINOR),  # G Harmonic Minor (dramatic)
        Scale(0, Mode.LYDIAN),  # C Lydian (wonder/magic)
    ],
    track_mapping={
        "Melody": "orch_violins_i_melody",
        "Chords": "orch_horn_chords",
        "Bass": "orch_contrabass_bass",
        "Texture": "ambient_pad",
        "Percussion": "orch_timpani_bass",
    },
    instrument_mapping={
        "Melody": 40,  # Violins
        "Chords": 60,  # French Horn
        "Bass": 43,  # Contrabass
        "Texture": 48,  # String Ensemble
        "Percussion": 47,  # Timpani
    },
    progressions={
        "Intro": ["I", "I V vi iii", "Im", "Im bVI bIII bVII"],
        "Build": ["I V vi IV", "Im bVI bVII Im", "I IV I V"],
        "Climax": ["I V Im bVI", "Im bIII bVI bVII Im", "I IV V I"],
        "Resolve": ["I vi IV V", "Im bVI bIII bVII"],
        "Outro": ["I", "I64 V I", "Im V Im"],
    },
    typical_bpm=85.0,
)

# ---------------------------------------------------------------------------
# Pop
# ---------------------------------------------------------------------------

POP_STYLE = Style(
    name="Pop",
    allowed_scales=[
        Scale(0, Mode.MAJOR),  # C Major
        Scale(7, Mode.MAJOR),  # G Major
        Scale(9, Mode.NATURAL_MINOR),  # A Minor
        Scale(5, Mode.MAJOR),  # F Major
    ],
    track_mapping={
        "Melody": "lead_melody",
        "Chords": "followed_chords",
        "Bass": "madonna_groove",
        "Drums": "rock_drums",
        "Synth": "fast_arp",
    },
    instrument_mapping={
        "Melody": 81,  # Lead Synth (Square)
        "Chords": 4,  # Electric Piano
        "Bass": 33,  # Electric Bass (Finger)
        "Drums": 0,  # Acoustic Grand (channel 10 for drums)
        "Synth": 89,  # Synth Pad (Warm)
    },
    progressions={
        "Intro": ["I", "I V", "I vi IV V"],
        "Verse": ["I V vi IV", "vi IV I V", "I vi IV V"],
        "Pre-Chorus": ["IV V", "vi IV V", "ii IV V"],
        "Chorus": ["I V vi IV", "IV I V vi", "vi IV I V"],
        "Bridge": ["vi ii IV V", "IV V iii vi", "I V IV V"],
        "Outro": ["I V vi IV I", "I vi IV I", "I"],
    },
    typical_bpm=120.0,
)

# ---------------------------------------------------------------------------
# Ambient
# ---------------------------------------------------------------------------

AMBIENT_STYLE = Style(
    name="Ambient",
    allowed_scales=[
        Scale(0, Mode.MAJOR),  # C Major
        Scale(9, Mode.NATURAL_MINOR),  # A Minor
        Scale(2, Mode.DORIAN),  # D Dorian
        Scale(0, Mode.LYDIAN),  # C Lydian
    ],
    track_mapping={
        "Pad": "ambient_pad",
        "Texture": "fast_arp",
        "Drone": "followed_bass",
        "Lead": "lead_melody",
    },
    instrument_mapping={
        "Pad": 89,  # Synth Pad (Warm)
        "Texture": 92,  # Synth Pad (Choir)
        "Drone": 48,  # String Ensemble 1
        "Lead": 75,  # Pan Flute
    },
    progressions={
        "Intro": ["I", "Im", "I IV"],
        "Floating": ["I IV", "Im IV", "I vi"],
        "Emerge": ["I V IV", "vi IV I", "Im bVI bVII"],
        "Drone": ["I", "Im", "IV"],
        "Outro": ["I", "Im", "I IV I"],
    },
    typical_bpm=70.0,
    typical_time_signature=(4, 4),
)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

STYLES: dict[str, Style] = {
    "dark_fantasy": DARK_FANTASY_STYLE,
    "symphonic": SYMPHONIC_DARK_FANTASY_STYLE,
    "classical": CLASSICAL_STYLE,
    "jazz": JAZZ_STYLE,
    "film": FILM_STYLE,
    "pop": POP_STYLE,
    "ambient": AMBIENT_STYLE,
}
