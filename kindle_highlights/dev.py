import concurrent.futures
import re
from pathlib import Path

import requests
import yaml


class NotionClient:
    def __init__(self, token, database_id=None):
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    def create_page(self, page_title, database_id=None):
        database_id = database_id or self.database_id
        create_page_url = "https://api.notion.com/v1/pages"
        create_page_data = {
            "parent": {"database_id": database_id},
            "properties": {"Name": {"title": [{"text": {"content": page_title}}]}},
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

    def create_database_in_page(self, page_id):
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

    def append_raw_text_to_page(self, page_id, raw_text):
        """
        Append the raw text content to a page as a source reference.

        Args:
            page_id: ID of the parent page
            raw_text: Raw text content to be added
        """

        # Add a heading for the source text
        # Split text into chunks to avoid Notion API limits (around 2000 chars per block)
        chunk_size = 1900  # Keep some buffer below the 2000 char limit
        text_chunks = [
            raw_text[i : i + chunk_size] for i in range(0, len(raw_text), chunk_size)
        ]

        # Create a new page for the raw text
        create_page_url = "https://api.notion.com/v1/pages"
        create_page_data = {
            "parent": {"page_id": page_id},
            "properties": {
                "title": {"title": [{"text": {"content": "Source Raw Text"}}]}
            },
            "children": [],
        }

        # Add each text chunk as a paragraph block in the children array
        for chunk in text_chunks:
            create_page_data["children"].append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    },
                }
            )
        # Create the new page with all content
        response = requests.post(
            create_page_url, headers=self.headers, json=create_page_data
        )

        if response.status_code != 200:
            raise Exception(
                f"Error creating raw text page: {response.status_code}\n{response.text}"
            )

        return response.json()

    def add_quotes_to_database(self, database_id, quotes, notes):
        create_page_url = "https://api.notion.com/v1/pages"

        def add_single_quote(item):
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


def get_config(yaml_path):
    with open(Path(yaml_path), "r") as config_file:
        config = yaml.safe_load(config_file)
        return config["token"], config["database_id"]


def extract_quotes_from_file(filename):
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


def process_kindle_highlights(input_file, config_path):
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
    # Simple hardcoded configuration
    input_file = "./second_brain_collector/kindle_highlights/Daily Stoic.txt"
    config_file = "./second_brain_collector/config.yaml"

    print(f"Processing highlights from: {input_file}")
    result = process_kindle_highlights(input_file, config_file)

    if result:
        print("Highlights were successfully processed!")
    else:
        print("Failed to process highlights.")


if __name__ == "__main__":
    main()
