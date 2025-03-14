import re
from pathlib import Path
from typing import List, Tuple

def extract_quotes_from_file(filename: str) -> Tuple[str, List[str], List[str], str]:
    """Extract quotes and notes from a text file.

    Args:
        filename: Path to the text file containing quotes and notes.

    Returns:
        A tuple containing the raw content, list of quotes, list of notes, and the page title.
    """
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

        # Get metadata from standard positions
        try:
            title = lines[6].strip()[9:].split(":", 1)[0].strip()
            author = lines[7].strip()[10:].strip()
        except (IndexError, AttributeError):
            # Fallback to filename if metadata can't be parsed
            title = Path(filename).stem
            author = "Unknown"

        # Extract quotes and notes
        content = "".join(lines)
        raw_sections = re.findall(r"> (.*?)(?:\n\n|$)", content, re.DOTALL)

        quotes, notes = [], []
        for section in raw_sections:
            section_lines = section.strip().split("\n")
            quote = section_lines[0].strip()
            # Limit quotes to 2000 characters to comply with Notion API limits
            if len(quote) > 2000:
                quote = quote[:1997] + "..."
            quotes.append(quote)

            # Extract note if present
            note = ""
            if len(section_lines) > 1 and section_lines[1].strip().startswith("-"):
                note = section_lines[1].strip()[1:].strip()
            notes.append(note)

        return content, quotes, notes, f"{author} - {title}"
