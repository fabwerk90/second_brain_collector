import requests
from typing import Any, Dict, List


class NotionClient:
    def __init__(self, token: str, database_id: str):
        """
        Initializes a client for interacting with the Notion API.

        Parameters:
        ----------
        token : str
            The Notion API token for authorization.
        database_id : str
            The ID of the Notion database to connect to.
        """
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    def get_youtube_items(self) -> List[Dict[str, Any]]:
        """
        Query Notion database for items with Category = YouTube.

        Returns:
            List[Dict[str, Any]]: List of Notion pages with YouTube category
        """
        payload = {"filter": {"property": "Category", "select": {"equals": "YouTube"}}}

        response = requests.post(
            f"https://api.notion.com/v1/databases/{self.database_id}/query",
            headers=self.headers,
            json=payload,
        )

        if response.status_code != 200:
            print(f"Error querying database: {response.status_code} - {response.text}")
            return []

        return response.json().get("results", [])

    def clear_page_content(self, page_id: str) -> bool:
        """
        Clear existing content from a Notion page.

        Args:
            page_id (str): ID of the page to clear

        Returns:
            bool: True if successful, False otherwise
        """
        # Get existing blocks
        response = requests.get(
            f"https://api.notion.com/v1/blocks/{page_id}/children", headers=self.headers
        )

        if response.status_code != 200:
            print(f"Error getting blocks: {response.status_code} - {response.text}")
            return False

        # Delete each block
        blocks = response.json().get("results", [])
        for block in blocks:
            delete_response = requests.delete(
                f"https://api.notion.com/v1/blocks/{block['id']}", headers=self.headers
            )
            if delete_response.status_code != 200:
                print(f"Error deleting block: {delete_response.status_code}")

        return True

    def update_page_with_transcript(
        self, page_id: str, transcript_chunks: List[str]
    ) -> bool:
        """
        Update a Notion page with transcript chunks.

        Args:
            page_id (str): ID of the page to update
            transcript_chunks (List[str]): List of transcript text chunks

        Returns:
            bool: True if update was successful, False otherwise
        """
        # Clear existing content
        if not self.clear_page_content(page_id):
            return False

        # Prepare blocks for update
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]},
            }
            for chunk in transcript_chunks
        ]

        # Update the page with new content
        response = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=self.headers,
            json={"children": children},
        )

        if response.status_code != 200:
            print(f"Error updating page: {response.status_code} - {response.text}")
            return False

        return True
