from youtube_transcripts.notion_client import NotionClient
from youtube_transcripts.youtube_transcript_fetcher import YouTubeTranscriptFetcher, load_config


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

        # Initialize Notion client
        notion_client = NotionClient(token, database_id)

        # Get YouTube items
        youtube_items = notion_client.get_youtube_items()
        print(f"Found {len(youtube_items)} items with Category = YouTube")

        # Process each item
        for item in youtube_items:
            page_id = item["id"]
            youtube_link = YouTubeTranscriptFetcher.extract_youtube_link(item)

            if not youtube_link:
                print(f"No YouTube link found for page {page_id}")
                continue

            print(f"Processing: {youtube_link}")

            # Get transcript
            transcript = YouTubeTranscriptFetcher.get_youtube_transcript(youtube_link)

            if transcript.startswith("Error"):
                print(f"Failed to get transcript: {transcript}")
                continue

            # Split transcript into chunks
            transcript_chunks = YouTubeTranscriptFetcher.chunk_text(transcript)
            print(f"Transcript split into {len(transcript_chunks)} chunks")

            # Update the page
            try:
                success = notion_client.update_page_with_transcript(page_id, transcript_chunks)
                status = "Successfully updated" if success else "Failed to update"
                print(f"{status} page {page_id}")
            except Exception as e:
                print(f"Error updating page {page_id}: {str(e)}")

    except Exception as e:
        print(f"An error occurred in the main function: {str(e)}")


if __name__ == "__main__":
    main()
