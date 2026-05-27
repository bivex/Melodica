# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/fetch_arabic_poetry.py — Fetch random Arabic poems from Qafiyah API.
Formats the output as Markdown for easy reading.
"""

import requests
import argparse
from typing import List, Tuple

BASE_URL = "https://api.qafiyah.com/poems/random"

def fetch_random_poems(count: int) -> List[Tuple[str, str]]:
    """Fetch N random poems from the API."""
    poems = []
    for _ in range(count):
        try:
            response = requests.get(BASE_URL, timeout=10)
            response.raise_for_status()
            text = response.text.strip()
            
            # The API returns "Poem Text\n\nAuthor Name"
            parts = text.split("\n\n")
            if len(parts) >= 2:
                body = parts[0].strip()
                author = parts[1].strip()
            else:
                # Fallback if split fails
                lines = text.split("\n")
                author = lines[-1].strip()
                body = "\n".join(lines[:-1]).strip()
                
            poems.append((author, body))
        except Exception as e:
            print(f"Error fetching poem: {e}")
    return poems

def format_markdown(poems: List[Tuple[str, str]]) -> str:
    """Format the list of poems as Markdown."""
    md = "# Арабская поэзия: Случайная подборка\n"
    md += "*Источник: Qafiyah API (Classical Arabic)*\n\n---\n\n"
    
    for i, (author, body) in enumerate(poems):
        md += f"## {i+1}. Автор: {author}\n\n"
        md += "> " + body.replace("\n", "\n> ") + "\n\n"
        md += "---\n\n"
    
    return md

def main():
    parser = argparse.ArgumentParser(description="Fetch random Arabic poems.")
    parser.add_argument("-n", "--count", type=int, default=3, help="Number of poems to fetch")
    parser.add_argument("-o", "--output", help="Save to file")

    args = parser.parse_args()

    print(f"Fetching {args.count} random Arabic poems...")
    poems = fetch_random_poems(args.count)
    
    if not poems:
        print("No poems found.")
        return
        
    md_output = format_markdown(poems)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md_output)
        print(f"Results saved to {args.output}")
    else:
        print("\n" + md_output)

if __name__ == "__main__":
    main()
