from typing import Dict, List

GM_PROFILES = {
    0: {"name": "Acoustic Grand Piano", "band": "Full", "type": "Percussive"},
    1: {"name": "Bright Acoustic Piano", "band": "Full", "type": "Percussive"},
    2: {"name": "Electric Grand Piano", "band": "Full", "type": "Percussive"},
    3: {"name": "Honky-tonk Piano", "band": "Full", "type": "Percussive"},
    4: {"name": "Electric Piano 1", "band": "Full", "type": "Percussive"},
    5: {"name": "Electric Piano 2", "band": "Full", "type": "Percussive"},
    6: {"name": "Harpsichord", "band": "Full", "type": "Percussive"},
    7: {"name": "Clavinet", "band": "Full", "type": "Percussive"},
    8: {"name": "Celesta", "band": "High", "type": "Transient"},
    9: {"name": "Glockenspiel", "band": "High", "type": "Transient"},
    10: {"name": "Music Box", "band": "High", "type": "Transient"},
    11: {"name": "Vibraphone", "band": "High", "type": "Transient"},
    12: {"name": "Marimba", "band": "High", "type": "Transient"},
    13: {"name": "Xylophone", "band": "High", "type": "Transient"},
    14: {"name": "Tubular Bells", "band": "High", "type": "Transient"},
    15: {"name": "Dulcimer", "band": "High", "type": "Transient"},
    16: {"name": "Drawbar Organ", "band": "Full", "type": "Sustained"},
    17: {"name": "Percussive Organ", "band": "Full", "type": "Sustained"},
    18: {"name": "Rock Organ", "band": "Full", "type": "Sustained"},
    19: {"name": "Church Organ", "band": "Full", "type": "Sustained"},
    20: {"name": "Reed Organ", "band": "Full", "type": "Sustained"},
    21: {"name": "Accordion", "band": "Full", "type": "Sustained"},
    22: {"name": "Harmonica", "band": "Full", "type": "Sustained"},
    23: {"name": "Tango Accordion", "band": "Full", "type": "Sustained"},
    24: {"name": "Acoustic Guitar (nylon)", "band": "Mid", "type": "Plucked"},
    25: {"name": "Acoustic Guitar (steel)", "band": "Mid", "type": "Plucked"},
    26: {"name": "Electric Guitar (jazz)", "band": "Mid", "type": "Plucked"},
    27: {"name": "Electric Guitar (clean)", "band": "Mid", "type": "Plucked"},
    28: {"name": "Electric Guitar (muted)", "band": "Mid", "type": "Plucked"},
    29: {"name": "Overdriven Guitar", "band": "Mid", "type": "Plucked"},
    30: {"name": "Distortion Guitar", "band": "Mid", "type": "Plucked"},
    31: {"name": "Guitar Harmonics", "band": "Mid", "type": "Plucked"},
    32: {"name": "Acoustic Bass", "band": "Low", "type": "Plucked"},
    33: {"name": "Electric Bass (finger)", "band": "Low", "type": "Plucked"},
    34: {"name": "Electric Bass (pick)", "band": "Low", "type": "Plucked"},
    35: {"name": "Fretless Bass", "band": "Low", "type": "Sustained"},
    36: {"name": "Slap Bass 1", "band": "Low", "type": "Plucked"},
    37: {"name": "Slap Bass 2", "band": "Low", "type": "Plucked"},
    38: {"name": "Synth Bass 1", "band": "Low", "type": "Sustained"},
    39: {"name": "Synth Bass 2", "band": "Low", "type": "Sustained"},
    40: {"name": "Violin", "band": "High", "type": "Sustained"},
    41: {"name": "Viola", "band": "Mid_High", "type": "Sustained"},
    42: {"name": "Cello", "band": "Low_Mid", "type": "Sustained"},
    43: {"name": "Contrabass", "band": "Low", "type": "Sustained"},
    44: {"name": "Tremolo Strings", "band": "Mid_High", "type": "Sustained"},
    45: {"name": "Pizzicato Strings", "band": "Mid_High", "type": "Plucked"},
    46: {"name": "Orchestral Harp", "band": "Mid_High", "type": "Plucked"},
    47: {"name": "Timpani", "band": "Low", "type": "Percussive"},
    48: {"name": "String Ensemble 1", "band": "Full", "type": "Sustained"},
    49: {"name": "String Ensemble 2", "band": "Full", "type": "Sustained"},
    50: {"name": "Synth Strings 1", "band": "Full", "type": "Sustained"},
    51: {"name": "Synth Strings 2", "band": "Full", "type": "Sustained"},
    52: {"name": "Choir Aahs", "band": "Full", "type": "Sustained"},
    53: {"name": "Voice Oohs", "band": "Full", "type": "Sustained"},
    54: {"name": "Synth Choir", "band": "Full", "type": "Sustained"},
    55: {"name": "Orchestra Hit", "band": "Full", "type": "Sustained"},
    56: {"name": "Trumpet", "band": "Mid", "type": "Sustained"},
    57: {"name": "Trombone", "band": "Low_Mid", "type": "Sustained"},
    58: {"name": "Tuba", "band": "Low", "type": "Sustained"},
    59: {"name": "Muted Trumpet", "band": "Mid", "type": "Sustained"},
    60: {"name": "French Horn", "band": "Mid", "type": "Sustained"},
    61: {"name": "Brass Section", "band": "Mid", "type": "Sustained"},
    62: {"name": "Synth Brass 1", "band": "Mid", "type": "Sustained"},
    63: {"name": "Synth Brass 2", "band": "Mid", "type": "Sustained"},
    64: {"name": "Soprano Sax", "band": "Mid", "type": "Sustained"},
    65: {"name": "Alto Sax", "band": "Mid", "type": "Sustained"},
    66: {"name": "Tenor Sax", "band": "Mid", "type": "Sustained"},
    67: {"name": "Baritone Sax", "band": "Low_Mid", "type": "Sustained"},
    68: {"name": "Oboe", "band": "Mid", "type": "Sustained"},
    69: {"name": "English Horn", "band": "Mid", "type": "Sustained"},
    70: {"name": "Bassoon", "band": "Low_Mid", "type": "Sustained"},
    71: {"name": "Clarinet", "band": "Mid", "type": "Sustained"},
    72: {"name": "Piccolo", "band": "High", "type": "Sustained"},
    73: {"name": "Flute", "band": "High", "type": "Sustained"},
    74: {"name": "Recorder", "band": "High", "type": "Sustained"},
    75: {"name": "Pan Flute", "band": "High", "type": "Sustained"},
    76: {"name": "Blown Bottle", "band": "High", "type": "Sustained"},
    77: {"name": "Shakuhachi", "band": "High", "type": "Sustained"},
    78: {"name": "Whistle", "band": "High", "type": "Sustained"},
    79: {"name": "Ocarina", "band": "High", "type": "Sustained"},
    80: {"name": "Lead 1 (square)", "band": "Mid_High", "type": "Sustained"},
    81: {"name": "Lead 2 (sawtooth)", "band": "Mid_High", "type": "Sustained"},
    82: {"name": "Lead 3 (calliope)", "band": "Mid_High", "type": "Sustained"},
    83: {"name": "Lead 4 (chiff)", "band": "Mid_High", "type": "Sustained"},
    84: {"name": "Lead 5 (charang)", "band": "Mid_High", "type": "Sustained"},
    85: {"name": "Lead 6 (voice)", "band": "Mid_High", "type": "Sustained"},
    86: {"name": "Lead 7 (fifths)", "band": "Mid_High", "type": "Sustained"},
    87: {"name": "Lead 8 (bass + lead)", "band": "Mid_High", "type": "Sustained"},
    88: {"name": "Pad 1 (new age)", "band": "Full", "type": "Pad"},
    89: {"name": "Pad 2 (warm)", "band": "Full", "type": "Pad"},
    90: {"name": "Pad 3 (polysynth)", "band": "Full", "type": "Pad"},
    91: {"name": "Pad 4 (choir)", "band": "Full", "type": "Pad"},
    92: {"name": "Pad 5 (bowed)", "band": "Full", "type": "Pad"},
    93: {"name": "Pad 6 (metallic)", "band": "Full", "type": "Pad"},
    94: {"name": "Pad 7 (halo)", "band": "Full", "type": "Pad"},
    95: {"name": "Pad 8 (sweep)", "band": "Full", "type": "Pad"},
    96: {"name": "FX 1 (rain)", "band": "Full", "type": "Pad"},
    97: {"name": "FX 2 (soundtrack)", "band": "Full", "type": "Pad"},
    98: {"name": "FX 3 (crystal)", "band": "Full", "type": "Pad"},
    99: {"name": "FX 4 (atmosphere)", "band": "Full", "type": "Pad"},
    100: {"name": "FX 5 (brightness)", "band": "Full", "type": "Pad"},
    101: {"name": "FX 6 (goblins)", "band": "Full", "type": "Pad"},
    102: {"name": "FX 7 (echoes)", "band": "Full", "type": "Pad"},
    103: {"name": "FX 8 (sci-fi)", "band": "Full", "type": "Pad"},
    104: {"name": "Sitar", "band": "Mid", "type": "Plucked"},
    105: {"name": "Banjo", "band": "Mid", "type": "Plucked"},
    106: {"name": "Shamisen", "band": "Mid", "type": "Plucked"},
    107: {"name": "Koto", "band": "Mid", "type": "Plucked"},
    108: {"name": "Kalimba", "band": "Mid", "type": "Plucked"},
    109: {"name": "Bagpipe", "band": "Mid", "type": "Plucked"},
    110: {"name": "Fiddle", "band": "Mid", "type": "Plucked"},
    111: {"name": "Shanai", "band": "Mid", "type": "Plucked"},
    112: {"name": "Tinkle Bell", "band": "Mid", "type": "Percussive"},
    113: {"name": "Agogo", "band": "Mid", "type": "Percussive"},
    114: {"name": "Steel Drums", "band": "Mid", "type": "Percussive"},
    115: {"name": "Woodblock", "band": "Mid", "type": "Percussive"},
    116: {"name": "Taiko Drum", "band": "Mid", "type": "Percussive"},
    117: {"name": "Melodic Tom", "band": "Mid", "type": "Percussive"},
    118: {"name": "Synth Drum", "band": "Mid", "type": "Percussive"},
    119: {"name": "Reverse Cymbal", "band": "Mid", "type": "Percussive"},
    120: {"name": "Guitar Fret Noise", "band": "Full", "type": "Transient"},
    121: {"name": "Breath Noise", "band": "Full", "type": "Transient"},
    122: {"name": "Seashore", "band": "Full", "type": "Transient"},
    123: {"name": "Bird Tweet", "band": "Full", "type": "Transient"},
    124: {"name": "Telephone Ring", "band": "Full", "type": "Transient"},
    125: {"name": "Helicopter", "band": "Full", "type": "Transient"},
    126: {"name": "Applause", "band": "Full", "type": "Transient"},
    127: {"name": "Gunshot", "band": "Full", "type": "Transient"}
}

def analyze_orchestration(instruments: Dict[str, int]) -> List[str]:
    """Returns a list of alerts/warnings about the orchestration."""
    alerts = []
    
    used_profiles = []
    for track_name, prog in instruments.items():
        if prog in GM_PROFILES:
            used_profiles.append(GM_PROFILES[prog])

    low_count = sum(1 for p in used_profiles if p["band"] in ("Low", "Low_Mid"))
    mid_count = sum(1 for p in used_profiles if p["band"] in ("Mid", "Mid_High", "Low_Mid"))
    full_count = sum(1 for p in used_profiles if p["band"] == "Full")

    sustained_count = sum(1 for p in used_profiles if p["type"] in ("Sustained", "Pad"))
    transient_count = sum(1 for p in used_profiles if p["type"] in ("Transient", "Percussive", "Plucked"))
    
    if low_count + full_count > 2:
        alerts.append("⚠️ Low-end Clash: Слишком много басовых/полночастотных инструментов.")
    elif low_count == 0 and full_count == 0:
        alerts.append("⚠️ Thin Mix: Отсутствуют инструменты басового регистра.")

    if mid_count + full_count > 3:
        alerts.append("⚠️ Mid-range Clutter: Перегрузка средних частот.")

    if sustained_count == 0:
        alerts.append("ℹ️ Dry Mix: Нет педальных/тянущихся звуков.")
    elif transient_count == 0:
        alerts.append("ℹ️ Ambient Mix: Нет перкуссионных/щипковых звуков.")

    return alerts
