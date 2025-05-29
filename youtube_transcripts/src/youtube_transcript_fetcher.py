import os
import textwrap
from typing import Any, Dict, List, Optional

import yaml
from youtube_transcript_api import YouTubeTranscriptApi


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
        video_id = _extract_video_id(video_link)

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
            return _get_fallback_transcript(video_id)

    except Exception as e:
        return f"Error getting transcript: {str(e)}"


def _extract_video_id(video_link: str) -> Optional[str]:
    """Extract video ID from YouTube URL."""
    if "youtube.com/watch?v=" in video_link:
        return video_link.split("v=")[1].split("&")[0]
    elif "youtu.be/" in video_link:
        return video_link.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com/shorts/" in video_link:
        return video_link.split("shorts/")[1].split("?")[0]
    return None


def _get_fallback_transcript(video_id: str) -> str:
    """Try to get transcript in any available language."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try auto-generated transcripts first
        for transcript in transcript_list:
            if transcript.is_generated:
                transcript_text = _fetch_and_translate_transcript(transcript)
                if transcript_text:
                    return transcript_text

        # If no auto-generated found, try any manual transcript
        for transcript in transcript_list:
            transcript_text = _fetch_transcript(transcript)
            if transcript_text:
                return transcript_text

        return "Error: No usable transcript found in any language"

    except Exception as e:
        return f"Error: No transcripts available: {str(e)}"


def _fetch_and_translate_transcript(transcript) -> Optional[str]:
    """Fetch transcript and translate to English if needed."""
    try:
        trans_list = transcript.fetch()
        transcript_text = " ".join(part["text"] for part in trans_list)
        print(f"Auto-generated transcript in {transcript.language_code} retrieved")

        # If not English, try to translate it
        if transcript.language_code != "en":
            try:
                translated = transcript.translate("en").fetch()
                transcript_text = " ".join(part["text"] for part in translated)
                print(
                    f"Transcript translated from {transcript.language_code} to English"
                )
            except Exception as e:
                print(
                    f"Could not translate from {transcript.language_code} to English: {str(e)}"
                )

        return transcript_text
    except Exception:
        return None


def _fetch_transcript(transcript) -> Optional[str]:
    """Fetch transcript without translation."""
    try:
        trans_list = transcript.fetch()
        transcript_text = " ".join(part["text"] for part in trans_list)
        print(f"Transcript in {transcript.language_code} retrieved")
        return transcript_text
    except Exception:
        return None


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
