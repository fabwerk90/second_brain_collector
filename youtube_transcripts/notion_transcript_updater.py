import os
import textwrap

import requests
import yaml
from youtube_transcript_api import YouTubeTranscriptApi


def load_config():
    """Load configuration from YAML file"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config.yaml"
    )
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config


def get_youtube_items(token, database_id):
    """Query Notion database for items with Category = YouTube using requests"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",  # Update version as needed
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

    return response.json()["results"]


def extract_youtube_link(page):
    """Extract the YouTube link from a Notion page"""
    # Assuming the URL is stored in a property called "URL" or "Link"
    for prop_name in ["URL", "Link", "Url", "url", "link"]:
        if prop_name in page["properties"]:
            prop = page["properties"][prop_name]
            if "url" in prop:
                return prop["url"]
    return None


def chunk_text(text, chunk_size=1900):
    """Split text into chunks smaller than chunk_size"""
    chunks = textwrap.wrap(
        text, width=chunk_size, replace_whitespace=False, break_long_words=False
    )
    return chunks


def clear_page_content(token, page_id):
    """Clear existing content from a page"""
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"}

    # First, get the existing blocks
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


def update_page_with_transcript(token, page_id, transcript_chunks):
    """Update a Notion page with transcript chunks using requests"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # Clear existing content
    if not clear_page_content(token, page_id):
        return False

    # Prepare blocks for update
    children = []
    for chunk in transcript_chunks:
        children.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                },
            }
        )

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


def get_youtube_transcript(video_link):
    """
    Get the transcript of a YouTube video or Short.

    Args:
        video_id (str): The YouTube video ID (the part after v= in the URL or after /shorts/)

    Returns:
        str: The full transcript text
    """
    try:
        # Extract the video ID from the YouTube link
        if "youtube.com/watch?v=" in video_link:
            video_id = video_link.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_link:
            video_id = video_link.split("youtu.be/")[1].split("?")[0]
        elif "youtube.com/shorts/" in video_link:
            video_id = video_link.split("shorts/")[1].split("?")[0]
        else:
            raise ValueError("Invalid YouTube URL format")
        # Get the transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

        # Combine all transcript parts
        transcript_text = " ".join([part["text"] for part in transcript_list])

        print("Transcript successfully retrieved")
        return transcript_text

    except Exception as e:
        return f"Error getting transcript: {str(e)}"


def main():
    # Load configuration
    config = load_config()
    token = config["token"]

    # Get YouTube items
    youtube_items = get_youtube_items(token, config["database_id"])

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
            if success:
                print(f"Successfully updated page {page_id}")
            else:
                print(f"Failed to update page {page_id}")
        except Exception as e:
            print(f"Error updating page {page_id}: {str(e)}")


if __name__ == "__main__":
    main()
