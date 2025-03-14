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
python kindle_highlights/main.py <path_to_kindle_highlights_file>
```

### YouTube Transcripts

To process YouTube transcripts and add them to Notion, use the following command:
```bash
python youtube_transcripts/notion_transcript_updater.py
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
