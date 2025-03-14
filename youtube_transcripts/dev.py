from youtube_transcript_api import YouTubeTranscriptApi


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


# Example usage
link1 = "https://www.youtube.com/watch?v=hcz1Q4gweYQ"
link2 = "https://youtu.be/l6BoSORXCUg?si=3DmhygZKMbgwnJdC"
link3 = "https://www.youtube.com/shorts/-ZV-9zqjUME"
transcript = get_youtube_transcript(link3)
print(f"Transcript length: {len(transcript)} characters")
print(transcript[:500])  # Print the first 500 characters of the transcript
