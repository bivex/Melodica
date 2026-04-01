"""
melodica_cli.py — Command Line Interface for Melodica.
Usage: python3 melodica_cli.py arrange --progression "Im VII V" --preset "bass"
"""

import argparse
import sys
import re
from pathlib import Path

# Add current dir to path to ensure melodica package is findable
sys.path.append(str(Path(__file__).parent))

from melodica.types import Note, HarmonizationRequest, Scale, Mode, NoteInfo, parse_progression, MusicTimeline, KeyLabel
from melodica.modifiers import ModifierContext
from melodica.presets import load_preset
from melodica.midi import notes_to_midi, export_multitrack_midi
from melodica.layout import PhraseOrderParser, PhraseOrderUnit

def parse_chords(chord_str: str, key: Scale) -> list:
    """Very simple parser for chord strings like 'Am F C G'."""
    from melodica.types import Quality, ChordLabel
    
    parts = chord_str.split()
    chords = []
    
    QUALITIES = {
        "m": Quality.MINOR,
        "": Quality.MAJOR,
        "7": Quality.DOMINANT7,
        "maj7": Quality.MAJOR7,
        "m7": Quality.MINOR7,
        "dim": Quality.DIMINISHED,
        "sus2": Quality.SUS2,
        "sus4": Quality.SUS4,
    }
    
    NOTES = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
    
    t = 0.0
    for p in parts:
        match = re.match(r"^([A-G][#b]?)(.*)$", p)
        if not match: continue
        root_name, q_str = match.groups()
        root = NOTES.get(root_name, 0)
        quality = QUALITIES.get(q_str, Quality.MAJOR)
        c = ChordLabel(root=root, quality=quality, start=t, duration=4.0)
        c.degree = key.degree_of(root)
        chords.append(c)
        t += 4.0
    return chords

def parse_keys(key_str: str) -> list[KeyLabel]:
    """Parses keys like '0:C:major 16:G:major'."""
    from melodica.types import Scale, Mode, KeyLabel
    parts = key_str.split()
    keys = []
    root_map = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
    for p in parts:
        bits = p.split(":")
        if len(bits) == 3:
            t, root_name, mode_name = bits
            root = root_map.get(root_name, 0)
            mode = Mode(mode_name)
            keys.append(KeyLabel(scale=Scale(root=root, mode=mode), start=float(t)))
    return keys

def cmd_generate(args):
    root_map = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
    root = root_map.get(args.root, 0)
    mode = Mode(args.mode)
    key = Scale(root=root, mode=mode)
    
    keys = parse_keys(args.keys) if args.keys else [KeyLabel(scale=key, start=0.0)]
    
    if args.chords:
        chords = parse_chords(args.chords, key)
    elif args.progression:
        chords = parse_progression(args.progression, key)
    else:
        print("Error: No chords or progression provided.")
        return

    timeline = MusicTimeline(chords=chords, keys=keys)

    try:
        generator, modifiers = load_preset(args.preset)
        print(f"Loaded preset: {args.preset}")
    except Exception as e:
        print(f"Preset {args.preset} not found. using default.")
        from melodica.generators import MelodyGenerator
        generator = MelodyGenerator()
        modifiers = []

    total_beats = sum(c.duration for c in chords)
    notes = generator.render(chords, timeline, total_beats)
    
    ctx = ModifierContext(duration_beats=total_beats, chords=chords, timeline=timeline, scale=key)
    for m in modifiers:
        notes = m.modify(notes, ctx)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    notes_to_midi(notes, str(out_path))
    print(f"✨ MIDI saved to: {out_path.absolute()}")

def cmd_arrange(args):
    root_map = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
    root = root_map.get(args.root, 0)
    mode = Mode(args.mode)
    key = Scale(root=root, mode=mode)
    
    keys = parse_keys(args.keys) if args.keys else [KeyLabel(scale=key, start=0.0)]
    
    if args.chords:
        chords = parse_chords(args.chords, key)
    elif args.progression:
        chords = parse_progression(args.progression, key)
    else:
        print("Error: No chords or progression provided.")
        return
        
    timeline = MusicTimeline(chords=chords, keys=keys)
    duration = sum(c.duration for c in chords)
    layout_units = []
    if args.layout:
        parser = PhraseOrderParser()
        layout_units = parser.parse(args.layout)
        duration = sum(u.length for u in layout_units)
    
    final_arrangement = {}
    for track_info in args.tracks.split():
        preset_name, track_label = track_info.split(":")
        print(f"Adding track '{track_label}' with preset '{preset_name}'")
        
        try:
            gen, mods = load_preset(preset_name)
            track_notes = []
            if layout_units:
                t = 0.0
                for unit in layout_units:
                    if unit.label != "R":
                        local_key = timeline.get_key_at(t)
                        phrase_notes = gen.render(chords, local_key, unit.length)
                        for n in phrase_notes:
                            n.start += t
                        track_notes.extend(phrase_notes)
                    t += unit.length
            else:
                track_notes = gen.render(chords, timeline, duration)
                
            ctx = ModifierContext(duration_beats=duration, chords=chords, timeline=timeline, tracks=final_arrangement, scale=key)
            for m in mods:
                track_notes = m.modify(track_notes, ctx)
            final_arrangement[track_label] = track_notes
        except Exception as e:
            print(f"Error loading preset '{preset_name}': {e}")

    if args.voice_leading:
        from melodica.modifiers import VoiceLeadingModifier
        print("Applying Global Voice Leading...")
        ctx = ModifierContext(duration_beats=duration, chords=chords, timeline=timeline, scale=key)
        for label, notes in final_arrangement.items():
            target = 3 if "bass" in label.lower() else 5
            vl = VoiceLeadingModifier(target_octave=target)
            final_arrangement[label] = vl.modify(notes, ctx)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    export_multitrack_midi(final_arrangement, out_path)
    print(f"✨ Multitrack arrangement saved to: {out_path.absolute()}")

def main():
    parser = argparse.ArgumentParser(description="Melodica CLI")
    subparsers = parser.add_subparsers(dest="command")

    gen_parser = subparsers.add_parser("generate")
    gen_parser.add_argument("--chords", type=str)
    gen_parser.add_argument("--progression", type=str)
    gen_parser.add_argument("--preset", type=str, default="default")
    gen_parser.add_argument("--out", type=str, default="output/result.mid")
    gen_parser.add_argument("--root", type=str, default="C")
    gen_parser.add_argument("--mode", type=str, default="major")
    gen_parser.add_argument("--keys", type=str, help="Timed keys e.g. '0:C:major 16:G:major'")

    arr_parser = subparsers.add_parser("arrange")
    arr_parser.add_argument("--chords", type=str)
    arr_parser.add_argument("--progression", type=str)
    arr_parser.add_argument("--tracks", type=str, required=True)
    arr_parser.add_argument("--out", type=str, default="output/arrangement.mid")
    arr_parser.add_argument("--root", type=str, default="C")
    arr_parser.add_argument("--mode", type=str, default="major")
    arr_parser.add_argument("--keys", type=str, help="Timed keys")
    arr_parser.add_argument("--layout", type=str)
    arr_parser.add_argument("--voice-leading", action="store_true")

    args = parser.parse_args()
    if args.command == "generate": cmd_generate(args)
    elif args.command == "arrange": cmd_arrange(args)
    else: parser.print_help()

if __name__ == "__main__":
    main()
