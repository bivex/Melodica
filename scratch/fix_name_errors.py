import re
from pathlib import Path

def main():
    scripts_dir = Path("/Volumes/External/Code/Melodica/scripts")
    fixed_files = []
    
    # We want to replace "except Exception:" with "except Exception as e:"
    # only when {e} is used in the exception block.
    # A simple but safe regex to find the blocks:
    pattern = re.compile(r"except Exception:\s*\n(\s*)warnings\.warn\(f\"Modifier error: \{e\}\"", re.MULTILINE)
    
    # We should also handle cases where {e} might be formatted slightly differently
    # or other print/warning statements that might use {e} inside the block.
    # Let's search all python files in scripts/
    for filepath in scripts_dir.glob("*.py"):
        content = filepath.read_text(encoding="utf-8")
        
        # Replace occurrences of except Exception: followed by warnings.warn(f"Modifier error: {e}")
        new_content, count1 = re.subn(
            r"except Exception:\s*\n(\s*)(warnings\.warn\(f\"Modifier error: \{e\}\")",
            r"except Exception as e:\n\1\2",
            content
        )
        
        # Also check other generic except blocks using {e}
        new_content, count2 = re.subn(
            r"except Exception:\s*\n(\s*)(print\(f\".*?\{e\}.*?\"\))",
            r"except Exception as e:\n\1\2",
            new_content
        )
        
        # Let's write back if any replacements were made
        if count1 > 0 or count2 > 0:
            filepath.write_text(new_content, encoding="utf-8")
            fixed_files.append((filepath.name, count1 + count2))
            
    print(f"Fixed {len(fixed_files)} files:")
    for name, cnt in fixed_files:
        print(f" - {name}: {cnt} replacement(s)")

if __name__ == "__main__":
    main()
