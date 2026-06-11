import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators import GeneratorParams
from melodica.types import Scale, Mode, ChordLabel, Quality

def print_banner(text):
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)

def main():
    print_banner("TESTING NEW OSTINATO GENERATOR FEATURES")
    
    key = Scale(root=0, mode=Mode.MAJOR)
    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0),
        ChordLabel(root=7, quality=Quality.MAJOR, start=8.0, duration=4.0),
        ChordLabel(root=0, quality=Quality.MAJOR, start=12.0, duration=4.0),
    ]
    duration = 16.0

    # 1. Test Humanization
    print_banner("1. TEST HUMANIZATION")
    gen_hum = OstinatoGenerator(
        GeneratorParams(density=0.1, key_range_low=60, key_range_high=96),
        pattern="1-3-5-3",
        timing_jitter=0.02,
        velocity_jitter=5,
        duration_jitter=0.03
    )
    notes_hum = gen_hum.render(chords, key, duration)
    print("Showing first 8 notes with humanized timing/velocity/duration:")
    for n in notes_hum[:8]:
        print(f"  Note: pitch={n.pitch:<3} start={n.start:<8.4f} duration={n.duration:<8.4f} velocity={n.velocity:<3}")

    # 2. Test Phrase Endings
    print_banner("2. TEST PHRASE ENDINGS")
    for ending in ["silence", "root", "fifth", "hold"]:
        print(f"\n--- Ending Mode: {ending.upper()} (phrase_length=4.0) ---")
        gen_phr = OstinatoGenerator(
            GeneratorParams(density=0.1, key_range_low=60, key_range_high=96),
            pattern="1-3-5-3",
            phrase_length=4.0,
            phrase_ending=ending
        )
        notes_phr = gen_phr.render(chords, key, duration)
        # Filter notes around the end of the first two phrases
        print("Phrase 1 ending window notes:")
        for n in notes_phr:
            if 2.5 <= n.start <= 4.2:
                print(f"  Note: start={n.start:<8.4f} pitch={n.pitch:<3} duration={n.duration:<8.4f} velocity={n.velocity:<3}")
        print("Phrase 2 ending window notes:")
        for n in notes_phr:
            if 6.5 <= n.start <= 8.2:
                print(f"  Note: start={n.start:<8.4f} pitch={n.pitch:<3} duration={n.duration:<8.4f} velocity={n.velocity:<3}")

    # 3. Test Pattern Morphing
    print_banner("3. TEST PATTERN MORPHING")
    gen_morph = OstinatoGenerator(
        GeneratorParams(density=0.1, key_range_low=60, key_range_high=96),
        patterns=["1-3-5-3", "5-1-5-1", "1-2-1-3"],
        change_pattern_every=4.0,
        pattern_transition_mode="sequential"
    )
    notes_morph = gen_morph.render(chords, key, duration)
    # Check notes in bar 1 (0-4), bar 2 (4-8), bar 3 (8-12) to see different pattern structures
    print("Bar 1 (0.0 to 2.0) - Pattern 1 ('1-3-5-3'):")
    for n in notes_morph:
        if 0.0 <= n.start <= 2.0:
            print(f"  Note: start={n.start:<8.4f} pitch={n.pitch:<3}")
    print("\nBar 2 (4.0 to 6.0) - Pattern 2 ('5-1-5-1'):")
    for n in notes_morph:
        if 4.0 <= n.start <= 6.0:
            print(f"  Note: start={n.start:<8.4f} pitch={n.pitch:<3}")
    print("\nBar 3 (8.0 to 10.0) - Pattern 3 ('1-2-1-3'):")
    for n in notes_morph:
        if 8.0 <= n.start <= 10.0:
            print(f"  Note: start={n.start:<8.4f} pitch={n.pitch:<3}")

if __name__ == "__main__":
    main()
