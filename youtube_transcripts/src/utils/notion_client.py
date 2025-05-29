from typing import Any, Dict, List

import httpx


class NotionClient:
    def __init__(self, token: str, database_id: str):
        """Initialize Notion client with API token and database ID."""
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    def get_youtube_items(self) -> List[Dict[str, Any]]:
        """Query Notion database for items with Category = YouTube."""
        payload = {"filter": {"property": "Category", "select": {"equals": "YouTube"}}}

        response = httpx.post(
            f"https://api.notion.com/v1/databases/{self.database_id}/query",
            headers=self.headers,
            json=payload,
        )

        if response.status_code != 200:
            print(f"Error querying database: {response.status_code} - {response.text}")
            return []

        return response.json().get("results", [])

    def update_page_with_transcript(
        self, page_id: str, transcript_chunks: List[str]
    ) -> bool:
        """Update a Notion page with transcript chunks."""
        # Clear existing content first
        if not self._clear_page_content(page_id):
            return False

        # Add new content
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                },
            }
            for chunk in transcript_chunks
        ]

        response = httpx.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=self.headers,
            json={"children": children},
        )

        if response.status_code != 200:
            print(f"Error updating page: {response.status_code} - {response.text}")
            return False

        return True

    def _clear_page_content(self, page_id: str) -> bool:
        """Clear existing content from a Notion page."""
        # Get existing blocks
        response = httpx.get(
            f"https://api.notion.com/v1/blocks/{page_id}/children", headers=self.headers
        )

        if response.status_code != 200:
            print(f"Error getting blocks: {response.status_code} - {response.text}")
            return False

        # Delete each block
        blocks = response.json().get("results", [])
        for block in blocks:
            delete_response = httpx.delete(
                f"https://api.notion.com/v1/blocks/{block['id']}", headers=self.headers
            )
            if delete_response.status_code != 200:
                print(f"Error deleting block: {delete_response.status_code}")

        return True
