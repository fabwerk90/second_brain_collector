import concurrent.futures
import re
from pathlib import Path
from typing import List, Tuple

import requests
import yaml


class NotionClient:
    def __init__(self, token: str, database_id: str = None):
        """
        Initializes a client for interacting with the Notion API.

        Parameters:
        ----------
        token : str
            The Notion API token for authorization.
        database_id : str, optional
            The ID of the Notion database to connect to.

        Attributes:
        ----------
        token : str
            The stored Notion API token.
        database_id : str
            The ID of the connected Notion database.
        headers : dict
            HTTP headers used for Notion API requests, including authorization token.
        """
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    def create_page(self, page_title: str, database_id: str = None) -> str:
        """
        Creates a new page in Notion database with the given title.
        Args:
            page_title (str): The title of the page to create.
            database_id (str, optional): The ID of the database to create the page in.
                                         Defaults to self.database_id.
        Returns:
            str: The ID of the newly created page.
        Raises:
            Exception: If the page creation fails, including the status code and response text.
        Note:
            The page is created with "Book / Kindle" category by default.
        """
        database_id = database_id or self.database_id
        create_page_url = "https://api.notion.com/v1/pages"
        create_page_data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Name": {"title": [{"text": {"content": page_title}}]},
                "Category": {"select": {"name": "Book / Kindle"}},
            },
        }

        response = requests.post(
            create_page_url, headers=self.headers, json=create_page_data
        )
        if response.status_code != 200:
            raise Exception(
                f"Error creating page: {response.status_code}\n{response.text}"
            )

        page_id = response.json()["id"]
        print(f"Created page with ID: {page_id}")
        return page_id

    def create_database_in_page(self, page_id: str) -> str:
        """
        Create a new database in a specified Notion page for storing Kindle highlights.
        Creates a database titled "All Kindle Highlights" with properties for quote numbers,
        the quotes themselves, and any associated notes. The database is created as a child
        of the specified page.
        Args:
            page_id (str): The ID of the parent Notion page where the database will be created.
        Returns:
            str: The ID of the newly created database.
        Raises:
            Exception: If the database creation fails, including the HTTP status code and response text.
        """
        create_db_url = "https://api.notion.com/v1/databases"
        create_db_data = {
            "parent": {"page_id": page_id},
            "title": [{"text": {"content": "All Kindle Highlights"}}],
            "properties": {
                "Quote No.": {"title": {}},
                "Quote": {"rich_text": {}},
                "Notes": {"rich_text": {}},
            },
        }

        response = requests.post(
            create_db_url, headers=self.headers, json=create_db_data
        )
        if response.status_code != 200:
            raise Exception(
                f"Error creating database: {response.status_code}\n{response.text}"
            )

        database_id = response.json()["id"]
        print(f"Created database with ID: {database_id}")
        return database_id

    def _chunk_text(self, text: str, chunk_size: int = 1900) -> list[str]:
        """Split text into chunks to avoid Notion API limits.

        Args:
            text: The text to split into chunks.
            chunk_size: Maximum size of each chunk. Defaults to 1900
                        (Notion API has 2000 char limit per block).

        Returns:
            List of text chunks of specified size.
        """
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    def append_raw_text_to_page(self, page_id: str, raw_text: str) -> dict:
        """Create a child page containing the raw text content.

        Creates a new page under the specified parent page and adds the raw text
        content split into appropriate chunks to avoid API limits.

        Args:
            page_id: ID of the parent page.
            raw_text: Raw text content to be added to the page.

        Returns:
            The JSON response from the Notion API.

        Raises:
            Exception: If the API request fails.
        """
        # First add a heading for the raw text section
        append_heading_url = "https://api.notion.com/v1/blocks/" + page_id + "/children"
        heading_data = {
            "children": [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Source"}}]
                    },
                }
            ]
        }

        heading_response = requests.patch(
            append_heading_url, headers=self.headers, json=heading_data
        )
        if heading_response.status_code != 200:
            raise Exception(
                f"Error adding heading: {heading_response.status_code}\n{heading_response.text}"
            )

        create_page_url = "https://api.notion.com/v1/pages"

        # Create a new page for the raw text with chunked content
        text_chunks = self._chunk_text(raw_text)
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                },
            }
            for chunk in text_chunks
        ]

        create_page_data = {
            "parent": {"page_id": page_id},
            "properties": {
                "title": {"title": [{"text": {"content": "Source Raw Text"}}]}
            },
            "children": children,
        }

        response = requests.post(
            create_page_url, headers=self.headers, json=create_page_data
        )

        if response.status_code != 200:
            raise Exception(
                f"Error creating raw text page: {response.status_code}\n{response.text}"
            )

        return response.json()

    def add_quotes_to_database(
        self, database_id: str, quotes: List[str], notes: List[str]
    ) -> int:
        """Add quotes and notes to the specified Notion database.

        Args:
            database_id: ID of the Notion database.
            quotes: List of quotes to be added.
            notes: List of notes corresponding to the quotes.

        Returns:
            The number of successfully added quotes.

        Raises:
            Exception: If the API request fails.
        """
        create_page_url = "https://api.notion.com/v1/pages"

        def add_single_quote(item: Tuple[int, Tuple[str, str]]) -> bool:
            i, (quote, note) = item
            create_page_data = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Quote No.": {"title": [{"text": {"content": str(i)}}]},
                    "Quote": {"rich_text": [{"text": {"content": quote}}]},
                    "Notes": {"rich_text": [{"text": {"content": note}}]},
                },
            }

            response = requests.post(
                create_page_url, headers=self.headers, json=create_page_data
            )
            if response.status_code != 200:
                print(f"Error adding quote {i}: {response.status_code}")
                print(response.text)
                return False
            else:
                print(f"Added quote {i} to database")
                return True

        # Process quotes in parallel with a thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Create an enumerated list of quote/note pairs
            items = list(enumerate(zip(quotes, notes), 1))
            # Submit all tasks to the executor and wait for completion
            results = list(executor.map(add_single_quote, items))

        # Return success count
        return sum(results)


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
            quotes.append(section_lines[0].strip())

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


def main():
    """Main function to process Kindle highlights."""
    # Simple hardcoded configuration
    input_file = "./second_brain_collector/kindle_highlights/Atomic.txt"
    config_file = "./second_brain_collector/config.yaml"

    print(f"Processing highlights from: {input_file}")
    result = process_kindle_highlights(input_file, config_file)

    if result:
        print("Highlights were successfully processed!")
    else:
        print("Failed to process highlights.")


if __name__ == "__main__":
    main()
