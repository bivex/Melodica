from typing import Dict, List, Any

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

def get_interval_name(semitones: int) -> str:
    """Map semitone count to a beautiful interval name, matching music21 style."""
    octaves = semitones // 12
    base_semitones = semitones % 12
    base_names = {
        0: "Unison",
        1: "Minor Second",
        2: "Major Second",
        3: "Minor Third",
        4: "Major Third",
        5: "Perfect Fourth",
        6: "Tritone",
        7: "Perfect Fifth",
        8: "Minor Sixth",
        9: "Major Sixth",
        10: "Minor Seventh",
        11: "Major Seventh"
    }
    base_name = base_names[base_semitones]
    if octaves == 0:
        return base_name if base_name == "Tritone" else f"{base_name}"
    elif octaves == 1:
        if base_semitones == 0:
            return "Perfect Octave"
        elif base_semitones == 7:
            return "Perfect Twelfth"
        else:
            return f"Octave + {base_name}"
    elif octaves == 2:
        if base_semitones == 0:
            return "Perfect Double-octave"
        elif base_semitones == 7:
            return "Perfect Nineteenth"
        else:
            return f"Double-octave + {base_name}"
    elif octaves == 3:
        if base_semitones == 0:
            return "Perfect Triple-octave"
        else:
            return f"Triple-octave + {base_name}"
    else:
        return f"{octaves} Octaves + {base_name}"


def analyze_orchestration(
    instruments: Dict[str, int],
    tracks: dict[str, list[Any]] | None = None,
    chords: list[Any] | None = None
) -> List[str]:
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

    # Deep analysis if tracks are provided
    if tracks:
        from melodica.types import NoteInfo
        note_tracks = {k: v for k, v in tracks.items() if isinstance(v, list) and len(v) > 0 and isinstance(v[0], NoteInfo)}
        
        # 1. Conflict Ambitus (Orchestration Blur)
        sustained_ambitus = {}
        for tname, notes in note_tracks.items():
            prog = instruments.get(tname)
            if prog in GM_PROFILES:
                profile = GM_PROFILES[prog]
                if profile["type"] in ("Sustained", "Pad") and len(notes) >= 3:
                    pitches = [n.pitch for n in notes]
                    sustained_ambitus[tname] = (min(pitches), max(pitches))
        
        t_names = list(sustained_ambitus.keys())
        for i in range(len(t_names)):
            for j in range(i + 1, len(t_names)):
                t1, t2 = t_names[i], t_names[j]
                min1, max1 = sustained_ambitus[t1]
                min2, max2 = sustained_ambitus[t2]
                
                range1 = max1 - min1 + 1
                range2 = max2 - min2 + 1
                overlap = max(0, min(max1, max2) - max(min1, min2) + 1)
                
                if range1 > 0 and range2 > 0:
                    pct = overlap / min(range1, range2)
                    if pct > 0.5:
                        alerts.append(
                            f"⚠️ Orchestration Blur: Инструменты {t1} и {t2} (Sustained) "
                            f"имеют пересекающийся диапазон {pct*100:.1f}%. Рекомендуется развести их."
                        )

        # 2. Vertical Interval Profile & Low-Interval Mud (LIM)
        onsets = sorted(list({n.start for notes in note_tracks.values() for n in notes}))
        
        total_intervals = 0
        count_octaves = 0
        count_fifths = 0
        count_thirds = 0
        count_dissonances = 0
        muddy_thirds = 0
        mid_clutter_count = 0
        
        interval_distribution = {}
        
        for t in onsets:
            # Find all notes sounding at t
            sounding = []
            for tname, notes in note_tracks.items():
                for n in notes:
                    if n.start <= t < n.start + n.duration:
                        sounding.append((tname, n))
            
            # Mid-Range Clutter Check (Golden Mean)
            mid_tracks = {tname for tname, n in sounding if 36 <= n.pitch <= 60}
            if len(mid_tracks) > 3:
                mid_clutter_count += 1
            
            # Pairwise intervals
            pitches = sorted(list({n.pitch for _, n in sounding}))
            if len(pitches) >= 2:
                for idx1 in range(len(pitches)):
                    for idx2 in range(idx1 + 1, len(pitches)):
                        p1, p2 = pitches[idx1], pitches[idx2]
                        iv = p2 - p1
                        
                        total_intervals += 1
                        interval_distribution[iv] = interval_distribution.get(iv, 0) + 1
                        
                        base_iv = iv % 12
                        if base_iv == 0:
                            count_octaves += 1
                        elif base_iv in (5, 7):
                            count_fifths += 1
                        elif base_iv in (3, 4, 8, 9):
                            count_thirds += 1
                            if base_iv in (3, 4) and p1 < 48:
                                muddy_thirds += 1
                        elif base_iv in (1, 2, 6, 10, 11):
                            count_dissonances += 1
        
        if muddy_thirds > 3:
            alerts.append(
                f"⚠️ Low-Interval Mud: Обнаружено {muddy_thirds} терций в низком регистре (ниже C3). "
                "Это создает гул и 'мыло' в басу."
            )
            
        if mid_clutter_count > 2:
            alerts.append(
                f"⚠️ Mid-Range Clutter (Dynamic): В {mid_clutter_count} моментах более 3-х инструментов "
                "играют в диапазоне 36-60 одновременно. Активировано динамическое сжатие диссонансов."
            )
            
        if total_intervals > 10:
            pct_oct = count_octaves / total_intervals
            pct_fifths = count_fifths / total_intervals
            pct_thirds = count_thirds / total_intervals
            pct_diss = count_dissonances / total_intervals
            
            # Cinematic vs Jazz scoring
            cinematic_score = (pct_oct * 0.4 + pct_fifths * 0.3 + (1.0 - pct_thirds) * 0.3) * 100
            jazz_score = (pct_thirds * 0.5 + pct_diss * 0.5) * 100
            
            if cinematic_score > jazz_score:
                alerts.append(
                    f"ℹ️ Interval Profile: Cinematic Preset (Octaves: {pct_oct*100:.1f}%, "
                    f"Fifths: {pct_fifths*100:.1f}%, Thirds: {pct_thirds*100:.1f}%)."
                )
            else:
                alerts.append(
                    f"ℹ️ Interval Profile: Jazz/Modern Preset (Thirds/Sixths: {pct_thirds*100:.1f}%, "
                    f"Dissonances: {pct_diss*100:.1f}%)."
                )
                
            sorted_ivs = sorted(interval_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
            top_intervals = [f"{get_interval_name(iv)} ({count}x)" for iv, count in sorted_ivs]
            alerts.append(f"ℹ️ Top intervals detected: {', '.join(top_intervals)}.")

    return alerts
