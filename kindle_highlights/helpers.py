import concurrent.futures
import re
from pathlib import Path
from typing import List, Tuple

import requests
import yaml


def get_config(yaml_path: str) -> Tuple[str, str]:
    """Load configuration from a YAML file.

    Args:
        yaml_path: Path to the YAML configuration file.

    Returns:
        A tuple containing the Notion API token and database ID.
    """
    with open(Path(yaml_path), "r") as config_file:
        config = yaml.safe_load(config_file)
        return config["token"], config["database_id"]


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


def process_kindle_highlights(input_file: str, config_path: str) -> bool:
    """Process Kindle highlights and add them to Notion.

    Args:
        input_file: Path to the text file containing Kindle highlights.
        config_path: Path to the YAML configuration file.

    Returns:
        True if the highlights were successfully processed, False otherwise.
    """
    try:
        # Get configuration and extract quotes
        token, database_id = get_config(config_path)
        content, quotes, notes, page_title = extract_quotes_from_file(input_file)

        # Process with Notion API
        client = NotionClient(token, database_id)
        page_id = client.create_page(page_title, database_id)
        highlights_db_id = client.create_database_in_page(page_id)
        client.append_raw_text_to_page(page_id, content)
        client.add_quotes_to_database(highlights_db_id, quotes, notes)

        print(f"Successfully processed {len(quotes)} quotes from '{page_title}'")
        return True
    except Exception as e:
        print(f"Error processing highlights: {str(e)}")
        return False
