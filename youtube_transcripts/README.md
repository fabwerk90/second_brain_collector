# YouTube Transcripts

## Project Description

The `youtube_transcripts` project is designed to help you collect and organize YouTube transcripts into a Notion database. This project provides tools to extract transcripts and upload them to Notion for easy access and organization.

## Installation Instructions

To install the `youtube_transcripts` project, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/fabwerk90/second_brain_collector.git
   cd second_brain_collector/youtube_transcripts
   ```

2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage Instructions

To process YouTube transcripts and add them to Notion, use the following command:
```bash
python main.py
```

## Parameters

- `main.py`: The main script to process YouTube videos from Notion database and update pages with transcripts.

## Code Structure

```mermaid
graph TD;
    A[main.py] --> B[notion_client.py];
    A --> C[youtube_transcript_fetcher.py];
    B --> D[get_youtube_items];
    B --> E[clear_page_content];
    B --> F[update_page_with_transcript];
    C --> G[extract_youtube_link];
    C --> H[chunk_text];
    C --> I[get_youtube_transcript];
```

## Contributing Guidelines

We welcome contributions to the `youtube_transcripts` project! To contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Make your changes and commit them with clear commit messages.
4. Push your changes to your forked repository.
5. Create a pull request to the main repository.

## License Information

This project is licensed under the Apache License 2.0. See the [LICENSE](../LICENSE) file for more information.
