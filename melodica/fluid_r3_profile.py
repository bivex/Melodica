# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
melodica/fluid_r3_profile.py — FluidR3 GM Instrument Profile.

This profile maps standard Melodica instrument names to the optimal
Program (Preset) numbers specifically found in the FluidR3_GM.sf2 SoundFont.
"""

FLUID_R3_PROGRAMS: dict[str, int] = {
    # Keyboards
    "piano": 0,             # Yamaha Grand Piano
    "bright_piano": 1,      # Bright Yamaha Grand
    "electric_piano": 4,    # Rhodes EP
    "harpsichord": 6,       # Harpsichord
    
    # Chromatic Percussion
    "celesta": 8,           # Celesta
    "glockenspiel": 9,      # Glockenspiel
    "music_box": 10,        # Music Box
    "vibraphone": 11,       # Vibraphone
    "marimba": 12,          # Marimba
    "xylophone": 13,        # Xylophone
    "tubular_bells": 14,    # Tubular Bells
    
    # Organs
    "organ": 16,            # DrawbarOrgan
    "accordion": 21,        # Accordion
    "harmonica": 22,        # Harmonica
    
    # Guitars
    "nylon_guitar": 24,     # Nylon Guitar
    "guitar": 25,           # Steel Guitar
    "steel_guitar": 25,     # Steel Guitar
    "jazz_guitar": 26,      # Jazz Guitar
    "electric_guitar": 27,  # Clean Guitar
    "muted_guitar": 28,     # Muted Guitar
    "overdrive_guitar": 29, # Overdriven Guitar
    "distortion_guitar": 30,# Distortion Guitar
    
    # Basses
    "acoustic_bass": 32,    # Acoustic Bass
    "bass": 33,             # Finger Bass
    "electric_bass": 34,    # Picked Bass
    "fretless_bass": 35,    # Fretless Bass
    "slap_bass": 36,        # Slap Bass 1
    "synth_bass": 38,       # Synth Bass 1
    "acid_bass": 39,        # Synth Bass 2 (often more resonant)
    
    # Strings
    "violin": 40,           # Violin
    "viola": 41,            # Viola
    "cello": 42,            # Cello
    "contrabass": 43,       # Contrabass
    "tremolo_strings": 44,  # Tremolo Strings
    "pizzicato": 45,        # Pizzicato Strings
    "harp": 46,             # Orchestral Harp
    "timpani": 47,          # Timpani
    "strings": 48,          # String Ensemble 1
    
    # Brass / Woodwinds
    "choir": 52,            # Choir Aahs
    "voice": 54,            # Synth Voice
    "synth_voice": 54,      # Synth Voice
    "orchestra_hit": 55,    # Orchestra Hit
    "trumpet": 56,          # Trumpet
    "trombone": 57,         # Trombone
    "tuba": 58,             # Tuba
    "french_horn": 60,      # French Horn
    "brass": 61,            # Brass Section
    "synth_brass": 62,      # Synth Brass 1
    "soprano_sax": 64,      # Soprano Sax
    "alto_sax": 65,         # Alto Sax
    "tenor_sax": 66,        # Tenor Sax
    "baritone_sax": 67,     # Baritone Sax
    "oboe": 68,             # Oboe
    "english_horn": 69,     # English Horn
    "bassoon": 70,          # Bassoon
    "clarinet": 71,         # Clarinet
    
    # Pipes
    "piccolo": 72,          # Piccolo
    "flute": 73,            # Flute
    "recorder": 74,         # Recorder
    "pan_flute": 75,        # Pan Flute
    "shakuhachi": 77,       # Shakuhachi
    "whistle": 78,          # Whistle
    "ocarina": 79,          # Ocarina
    
    # Synth Leads (Optimized for FluidR3)
    "synth_lead": 80,       # Square Lead
    "saw_lead": 81,         # Saw Wave
    "calliope_lead": 82,    # Calliope Lead (Great for hyper-casual!)
    "chiff_lead": 83,       # Chiffer Lead
    "charang": 84,          # Charang
    
    # Synth Pads
    "pad": 89,              # Warm Pad
    "dark_pad": 88,         # New Age Pad
    "choir_pad": 91,        # Halo Pad
    "sweep_pad": 95,        # Sweep Pad
    
    # FX
    "synth_fx": 102,        # Echoes
    "crystal_fx": 98,       # Crystal
    "atmosphere_fx": 99,    # Atmosphere
    
    # Ethnic
    "sitar": 104,           # Sitar
    "banjo": 105,           # Banjo
    "shamisen": 106,        # Shamisen
    "koto": 107,            # Koto
    "kalimba": 108,         # Kalimba
    "bagpipe": 109,         # Bagpipe
    "fiddle": 110,          # Fiddle
    "shanai": 111,          # Shanai
    
    # Percussive
    "tinkle_bell": 112,     # Tinkle Bell
    "agogo": 113,           # Agogo
    "steel_drums": 114,     # Steel Drums
    "woodblock": 115,       # Woodblock
    "taiko": 116,           # Taiko Drum
    "melodic_tom": 117,     # Melodic Tom
    
    # Drums (Channel 10)
    "drums": 0,             # Standard Kit
    "percussion": 0,        # Standard Kit
}
