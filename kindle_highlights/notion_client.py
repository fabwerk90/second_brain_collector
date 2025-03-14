import concurrent.futures
import requests
from typing import List, Tuple


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
