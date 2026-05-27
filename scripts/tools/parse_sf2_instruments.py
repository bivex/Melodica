# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/parse_sf2_instruments.py — SoundFont (.sf2) Preset Extractor.

This script parses a SoundFont 2 file and exports a neatly formatted
list of all contained instruments, sorted by Bank and Program.
"""

import sys
import argparse
from pathlib import Path

try:
    from sf2utils.sf2parse import Sf2File
except ImportError:
    print("Error: 'sf2utils' is required.")
    print("Please install it via: pip install sf2utils audioop-lts")
    sys.exit(1)


def parse_and_save_sf2(sf2_path: Path, output_txt: Path):
    if not sf2_path.exists():
        print(f"Error: File not found -> {sf2_path}")
        sys.exit(1)

    print(f"Reading SoundFont: {sf2_path.name}...")
    
    with open(sf2_path, 'rb') as f:
        sf2 = Sf2File(f)
        
    # Extract valid presets (ignoring the technical 'EOP' End Of Presets marker)
    presets = [p for p in sf2.presets if p.name != 'EOP']
    
    # Sort primarily by Bank, then by Preset (Program) number
    presets.sort(key=lambda p: (p.bank, p.preset))
    
    # Ensure output directory exists
    output_txt.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_txt, 'w', encoding='utf-8') as out:
        out.write(f"SOUNDFONT INSTRUMENT MAP\n")
        out.write(f"File: {sf2_path.name}\n")
        out.write(f"Total Instruments: {len(presets)}\n")
        out.write("=" * 60 + "\n")
        
        current_bank = -1
        
        for p in presets:
            # Print Bank Header when bank changes
            if p.bank != current_bank:
                current_bank = p.bank
                
                # Identify standard GM banks
                if current_bank == 0:
                    bank_label = "General MIDI (Melodic)"
                elif current_bank == 128:
                    bank_label = "Percussion / Drum Kits"
                else:
                    bank_label = f"Variation / Custom Bank"
                    
                out.write(f"\n--- BANK {current_bank:03d} : {bank_label} ---\n")
            
            # Print Instrument (Program) line
            out.write(f"  Program {p.preset:03d} | {p.name}\n")

    print(f"✅ Successfully saved {len(presets)} presets to: {output_txt}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse SF2 and save layout to TXT")
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to the .sf2 file")
    parser.add_argument("--output", "-o", type=str, default="output/sf2_instruments.txt", help="Path to save the output .txt")
    
    args = parser.parse_args()
    parse_and_save_sf2(Path(args.input), Path(args.output))
