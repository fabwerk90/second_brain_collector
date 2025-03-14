import os
import textwrap
from typing import Any, Dict, List, Optional

import requests
import yaml
from youtube_transcript_api import YouTubeTranscriptApi


def load_config() -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Returns:
        Dict[str, Any]: Configuration dictionary containing API tokens and database IDs

    Raises:
        FileNotFoundError: If the config file doesn't exist
        yaml.YAMLError: If the YAML file is malformed
    """
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config.yaml"
    )
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def get_youtube_items(token: str, database_id: str) -> List[Dict[str, Any]]:
    """
    Query Notion database for items with Category = YouTube.

    Args:
        token (str): Notion API token
        database_id (str): ID of the Notion database to query

    Returns:
        List[Dict[str, Any]]: List of Notion pages with YouTube category
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    payload = {"filter": {"property": "Category", "select": {"equals": "YouTube"}}}

    response = requests.post(
        f"https://api.notion.com/v1/databases/{database_id}/query",
        headers=headers,
        json=payload,
    )

    if response.status_code != 200:
        print(f"Error querying database: {response.status_code} - {response.text}")
        return []

    return response.json().get("results", [])


def extract_youtube_link(page: Dict[str, Any]) -> Optional[str]:
    """
    Extract the YouTube link from a Notion page.

    Args:
        page (Dict[str, Any]): Notion page object

    Returns:
        Optional[str]: YouTube URL if found, None otherwise
    """
    # Check various common property names for URL
    url_property_names = ["URL", "Link", "Url", "url", "link"]

    for prop_name in url_property_names:
        if prop_name in page.get("properties", {}):
            prop = page["properties"][prop_name]
            if "url" in prop:
                return prop["url"]

    return None


def chunk_text(text: str, chunk_size: int = 1900) -> List[str]:
    """
    Split text into chunks smaller than chunk_size.

    Args:
        text (str): Text to be chunked
        chunk_size (int, optional): Maximum size of each chunk. Defaults to 1900.

    Returns:
        List[str]: List of text chunks
    """
    return textwrap.wrap(
        text, width=chunk_size, replace_whitespace=False, break_long_words=False
    )


def clear_page_content(token: str, page_id: str) -> bool:
    """
    Clear existing content from a Notion page.

    Args:
        token (str): Notion API token
        page_id (str): ID of the page to clear

    Returns:
        bool: True if successful, False otherwise
    """
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"}

    # Get existing blocks
    response = requests.get(
        f"https://api.notion.com/v1/blocks/{page_id}/children", headers=headers
    )

    if response.status_code != 200:
        print(f"Error getting blocks: {response.status_code} - {response.text}")
        return False

    # Delete each block
    blocks = response.json().get("results", [])
    for block in blocks:
        delete_response = requests.delete(
            f"https://api.notion.com/v1/blocks/{block['id']}", headers=headers
        )
        if delete_response.status_code != 200:
            print(f"Error deleting block: {delete_response.status_code}")

    return True


def update_page_with_transcript(
    token: str, page_id: str, transcript_chunks: List[str]
) -> bool:
    """
    Update a Notion page with transcript chunks.

    Args:
        token (str): Notion API token
        page_id (str): ID of the page to update
        transcript_chunks (List[str]): List of transcript text chunks

    Returns:
        bool: True if update was successful, False otherwise
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # Clear existing content
    if not clear_page_content(token, page_id):
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
        headers=headers,
        json={"children": children},
    )

    if response.status_code != 200:
        print(f"Error updating page: {response.status_code} - {response.text}")
        return False

    return True


def get_youtube_transcript(video_link: str) -> str:
    """
    Get the transcript of a YouTube video or Short.

    Args:
        video_link (str): YouTube video URL

    Returns:
        str: The full transcript text or error message
    """
    try:
        # Extract the video ID from the YouTube link
        video_id = None

        if "youtube.com/watch?v=" in video_link:
            video_id = video_link.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_link:
            video_id = video_link.split("youtu.be/")[1].split("?")[0]
        elif "youtube.com/shorts/" in video_link:
            video_id = video_link.split("shorts/")[1].split("?")[0]

        if not video_id:
            return "Error: Invalid YouTube URL format"

        # First try to get English transcript
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id, languages=["en"]
            )
            transcript_text = " ".join(part["text"] for part in transcript_list)
            print("English transcript successfully retrieved")
            return transcript_text
        except Exception as e:
            print(f"No English transcript available: {str(e)}")

            # Try to get available transcript languages
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

                # Try auto-generated transcripts in any language
                for transcript in transcript_list:
                    try:
                        if transcript.is_generated:
                            trans_list = transcript.fetch()
                            transcript_text = " ".join(
                                part["text"] for part in trans_list
                            )
                            print(
                                f"Auto-generated transcript in {transcript.language_code} retrieved"
                            )

                            # If not English, try to translate it
                            if transcript.language_code != "en":
                                try:
                                    translated = transcript.translate("en").fetch()
                                    transcript_text = " ".join(
                                        part["text"] for part in translated
                                    )
                                    print(
                                        f"Transcript translated from {transcript.language_code} to English"
                                    )
                                except Exception as e:
                                    print(
                                        f"Could not translate from {transcript.language_code} to English: {str(e)}"
                                    )

                            return transcript_text
                    except Exception:
                        continue

                # If no auto-generated found, try any manual transcript
                for transcript in transcript_list:
                    try:
                        trans_list = transcript.fetch()
                        transcript_text = " ".join(part["text"] for part in trans_list)
                        print(f"Transcript in {transcript.language_code} retrieved")
                        return transcript_text
                    except Exception:
                        continue

                return "Error: No usable transcript found in any language"

            except Exception as inner_e:
                return f"Error: No transcripts available: {str(inner_e)}"

    except Exception as e:
        return f"Error getting transcript: {str(e)}"


def main() -> None:
    """
    Main function to process YouTube videos from Notion database
    and update pages with transcripts.
    """
    try:
        # Load configuration
        config = load_config()
        token = config["token"]
        database_id = config["database_id"]

        # Get YouTube items
        youtube_items = get_youtube_items(token, database_id)
        print(f"Found {len(youtube_items)} items with Category = YouTube")

        # Process each item
        for item in youtube_items:
            page_id = item["id"]
            youtube_link = extract_youtube_link(item)

            if not youtube_link:
                print(f"No YouTube link found for page {page_id}")
                continue

            print(f"Processing: {youtube_link}")

            # Get transcript
            transcript = get_youtube_transcript(youtube_link)

            if transcript.startswith("Error"):
                print(f"Failed to get transcript: {transcript}")
                continue

            # Split transcript into chunks
            transcript_chunks = chunk_text(transcript)
            print(f"Transcript split into {len(transcript_chunks)} chunks")

            # Update the page
            try:
                success = update_page_with_transcript(token, page_id, transcript_chunks)
                status = "Successfully updated" if success else "Failed to update"
                print(f"{status} page {page_id}")
            except Exception as e:
                print(f"Error updating page {page_id}: {str(e)}")

    except Exception as e:
        print(f"An error occurred in the main function: {str(e)}")


if __name__ == "__main__":
    main()
