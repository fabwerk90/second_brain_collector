# second_brain_collector

## Project Description

The `second_brain_collector` project is designed to help you collect and organize your Kindle highlights and YouTube transcripts into a Notion database. This project provides tools to extract highlights and transcripts, and then upload them to Notion for easy access and organization.

## Installation Instructions

To install the `second_brain_collector` project, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/fabwerk90/second_brain_collector.git
   cd second_brain_collector
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

### Kindle Highlights

To process Kindle highlights and add them to Notion, use the following command:
```bash
python kindle_highlights/main.py <path_to_kindle_highlights_file> <path_to_config_file>
```

### YouTube Transcripts

To process YouTube transcripts and add them to Notion, use the following command:
```bash
python youtube_transcripts/main.py
```

## Parameters

### Kindle Highlights

- `<path_to_kindle_highlights_file>`: The path to the text file containing Kindle highlights.
- `<path_to_config_file>`: The path to the YAML configuration file containing the Notion API token and database ID.

### YouTube Transcripts

- `main.py`: The main script to process YouTube videos from Notion database and update pages with transcripts.

## Code Structure

```mermaid
graph TD;
    A[second_brain_collector] --> B[kindle_highlights];
    A --> C[youtube_transcripts];
    B --> D[main.py];
    B --> E[process_highlights.py];
    B --> F[config.py];
    B --> G[extract_quotes.py];
    B --> H[notion_client.py];
    E --> I[get_config from config.py];
    E --> J[extract_quotes_from_file from extract_quotes.py];
    E --> K[NotionClient from notion_client.py];
    K --> L[create_page];
    K --> M[create_database_in_page];
    K --> N[append_raw_text_to_page];
    K --> O[add_quotes_to_database];
    C --> P[main.py];
    C --> Q[notion_client.py];
    C --> R[youtube_transcript_fetcher.py];
    Q --> S[get_youtube_items];
    Q --> T[clear_page_content];
    Q --> U[update_page_with_transcript];
    R --> V[extract_youtube_link];
    R --> W[chunk_text];
    R --> X[get_youtube_transcript];
```

## Contributing Guidelines

We welcome contributions to the `second_brain_collector` project! To contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Make your changes and commit them with clear commit messages.
4. Push your changes to your forked repository.
5. Create a pull request to the main repository.

## License Information

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for more information.
