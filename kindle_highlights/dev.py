import re
from pathlib import Path

import requests
import yaml


def get_config(yaml_path):
    config_path = Path(yaml_path)
    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)
        NOTION_TOKEN = config["token"]
        DATABASE_ID = config["database_id"]
        return NOTION_TOKEN, DATABASE_ID


def extract_quotes_from_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

        # Get title from line 7 (index 6)
        title_line = lines[6].strip()
        # Extract title and cut off everything after the first colon
        title = title_line[9:].split(":", 1)[0].strip()

        # Get author from line 8 (index 7)
        author_line = lines[7].strip()
        author = author_line[10:].strip()

        # Join the lines to create a single string for regex searching
        content = "".join(lines)

        # Find all quotes and potential notes
        raw_sections = re.findall(r"> (.*?)(?:\n\n|$)", content, re.DOTALL)

        quotes = []
        notes = []

        for section in raw_sections:
            section_lines = section.strip().split("\n")
            quote = section_lines[0].strip()
            quotes.append(quote)

            # Check if there's a note (starts with "-")
            note = ""
            if len(section_lines) > 1 and section_lines[1].strip().startswith("-"):
                note = section_lines[1].strip()[1:].strip()  # Remove the "-" and trim
            notes.append(note)

        page_title = f"{author} - {title}"
        return quotes, notes, page_title


NOTION_TOKEN, DATABASE_ID = get_config("./second_brain_collector/config.yaml")

QUOTES, NOTES, PAGE_TITLE = extract_quotes_from_file(
    "./second_brain_collector/kindle_highlights/Daily Stoic.txt"
)


def create_notion_page(token, database_id, page_title):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # Create a new page in the database
    create_page_url = "https://api.notion.com/v1/pages"
    create_page_data = {
        "parent": {"database_id": database_id},
        "properties": {"Name": {"title": [{"text": {"content": page_title}}]}},
    }

    response = requests.post(create_page_url, headers=headers, json=create_page_data)
    if response.status_code != 200:
        print(f"Error creating page: {response.status_code}")
        print(response.text)
        return

    page_id = response.json()["id"]
    print(f"Created page with ID: {page_id}")
    return page_id


def create_database_in_page(token, page_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # Create a new database in the page
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

    response = requests.post(create_db_url, headers=headers, json=create_db_data)
    if response.status_code != 200:
        print(f"Error creating database: {response.status_code}")
        print(response.text)
        return None

    database_id = response.json()["id"]
    print(f"Created database with ID: {database_id}")
    return database_id


def write_quotes_to_database(token, database_id, quotes, notes):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    for i, (quote, note) in enumerate(zip(quotes, notes), 1):
        # Create a new page (row) in the database for each quote
        create_page_url = "https://api.notion.com/v1/pages"
        create_page_data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Quote No.": {"title": [{"text": {"content": str(i)}}]},
                "Quote": {"rich_text": [{"text": {"content": quote}}]},
                "Notes": {"rich_text": [{"text": {"content": note}}]},
            },
        }

        response = requests.post(
            create_page_url, headers=headers, json=create_page_data
        )
        if response.status_code != 200:
            print(f"Error adding quote {i}: {response.status_code}")
            print(response.text)
        else:
            print(f"Added quote {i} to database")


PAGE_ID = create_notion_page(NOTION_TOKEN, DATABASE_ID, PAGE_TITLE)
NEW_DATABASE_ID = create_database_in_page(NOTION_TOKEN, PAGE_ID)
write_quotes_to_database(NOTION_TOKEN, NEW_DATABASE_ID, QUOTES, NOTES)
