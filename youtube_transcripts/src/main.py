from typing import Any, Dict, List

from youtube_transcripts.src.notion_client import NotionClient
from youtube_transcripts.src.youtube_transcript_fetcher import (
    chunk_text,
    extract_youtube_link,
    get_youtube_transcript,
    load_config,
)


def initialize_notion_client() -> NotionClient:
    """
    Initialize and return a NotionClient with configuration from config file.

    Returns:
        NotionClient: Configured Notion client instance
    """
    config = load_config()
    token = config["token"]
    database_id = config["database_id"]
    return NotionClient(token, database_id)


def process_youtube_item(item: Dict[str, Any], notion_client: NotionClient) -> bool:
    """
    Process a single YouTube item: extract link, get transcript, and update page.    Args:
        item: Notion page item containing YouTube link
        notion_client: NotionClient instance for updating pages

    Returns:
        bool: True if processing was successful, False otherwise
    """
    page_id = item["id"]
    youtube_link = extract_youtube_link(item)

    if not youtube_link:
        print(f"No YouTube link found for page {page_id}")
        return False

    print(f"Processing: {youtube_link}")

    # Get transcript
    transcript = get_youtube_transcript(youtube_link)

    if transcript.startswith("Error"):
        print(f"Failed to get transcript: {transcript}")
        return False  # Split transcript into chunks
    transcript_chunks = chunk_text(transcript)
    print(f"Transcript split into {len(transcript_chunks)} chunks")

    # Update the page
    return update_page_with_transcript(notion_client, page_id, transcript_chunks)


def update_page_with_transcript(
    notion_client: NotionClient, page_id: str, transcript_chunks: List[str]
) -> bool:
    """
    Update a Notion page with transcript chunks.

    Args:
        notion_client: NotionClient instance
        page_id: ID of the page to update
        transcript_chunks: List of transcript text chunks

    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        success = notion_client.update_page_with_transcript(page_id, transcript_chunks)
        status = "Successfully updated" if success else "Failed to update"
        print(f"{status} page {page_id}")
        return success
    except Exception as e:
        print(f"Error updating page {page_id}: {str(e)}")
        return False


def process_youtube_items(
    youtube_items: List[Dict[str, Any]], notion_client: NotionClient
) -> None:
    """
    Process all YouTube items from the Notion database.

    Args:
        youtube_items: List of Notion page items with YouTube category
        notion_client: NotionClient instance for updating pages
    """
    print(f"Found {len(youtube_items)} items with Category = YouTube")

    successful_count = 0
    for item in youtube_items:
        if process_youtube_item(item, notion_client):
            successful_count += 1

    print(
        f"Successfully processed {successful_count} out of {len(youtube_items)} items"
    )


def main() -> None:
    """
    Main function to process YouTube videos from Notion database
    and update pages with transcripts.
    """
    try:
        # Initialize Notion client
        notion_client = initialize_notion_client()

        # Get YouTube items
        youtube_items = notion_client.get_youtube_items()

        # Process all items
        process_youtube_items(youtube_items, notion_client)

    except Exception as e:
        print(f"An error occurred in the main function: {str(e)}")


if __name__ == "__main__":
    main()
