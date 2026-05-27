# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/fetch_poetry.py — Utility to fetch poems from PoeTree API.
Fetches N poems from a specific author and formats them as Markdown.
"""

import sys
import requests
import argparse
from typing import List, Dict, Any

BASE_URL = "https://versologie.cz/poetree/api/"

def get_author_id(name_query: str, corpus: str = "ru") -> int | None:
    """Find author ID by name."""
    url = f"{BASE_URL}authors?corpus={corpus}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        authors = response.json()
        
        # Exact match or fuzzy match
        for author in authors:
            if name_query.lower() in author['name'].lower():
                return author['id_']
    except Exception as e:
        print(f"Error fetching authors: {e}")
    return None

def fetch_poems(author_id: int, count: int, corpus: str = "ru") -> List[Dict[str, Any]]:
    """Fetch metadata for N poems of an author."""
    url = f"{BASE_URL}poems?corpus={corpus}&id_author={author_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        poems = response.json()
        return poems[:count]
    except Exception as e:
        print(f"Error fetching poem list: {e}")
        return []

def fetch_poem_body(poem_id_int: int, corpus: str = "ru") -> str:
    """Fetch the full text of a specific poem."""
    url = f"{BASE_URL}poem?corpus={corpus}&id_poem={poem_id_int}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # PoeTree returns body as a list of lines/stanzas
        lines = []
        for line in data.get('body', []):
            lines.append(line.get('text', ''))
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching poem text: {e}"

def format_markdown(author_name: str, poems_data: List[Dict[str, Any]], corpus: str) -> str:
    """Generate the final Markdown report."""
    md = f"# Поэзия: {author_name}\n"
    md += f"*Источник: PoeTree API ({corpus})*\n\n---\n\n"
    
    for i, p in enumerate(poems_data):
        title = p.get('title', 'Без названия').strip('«»')
        year = p.get('year_created_from', 'Неизвестно')
        body = fetch_poem_body(p['id_'], corpus)
        
        md += f"## {i+1}. {title}\n"
        md += f"*Год: {year}*\n\n"
        md += "> " + body.replace("\n", "\n> ") + "\n\n"
        md += "---\n\n"
    
    return md

def main():
    parser = argparse.ArgumentParser(description="Fetch poems from PoeTree API.")
    parser.add_argument("author", help="Author name (e.g., 'Ahmatova')")
    parser.add_argument("-n", "--count", type=int, default=3, help="Number of poems to fetch")
    parser.add_argument("-c", "--corpus", default="ru", help="Corpus (ru, en, etc.)")
    parser.add_argument("-o", "--output", help="Save to file")

    args = parser.parse_args()

    print(f"Searching for author: {args.author}...")
    author_id = get_author_id(args.author, args.corpus)
    
    if author_id is None:
        print(f"Author '{args.author}' not found in {args.corpus} corpus.")
        sys.exit(1)
        
    print(f"Found author ID: {author_id}. Fetching {args.count} poems...")
    poems_meta = fetch_poems(author_id, args.count, args.corpus)
    
    if not poems_meta:
        print("No poems found.")
        sys.exit(0)
        
    md_output = format_markdown(args.author, poems_meta, args.corpus)
    
    if args.output:
        Path(args.output).write_text(md_output)
        print(f"Results saved to {args.output}")
    else:
        print("\n" + md_output)

if __name__ == "__main__":
    main()
