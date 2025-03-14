from kindle_highlights.config import get_config
from kindle_highlights.extract_quotes import extract_quotes_from_file
from kindle_highlights.notion_client import NotionClient


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
