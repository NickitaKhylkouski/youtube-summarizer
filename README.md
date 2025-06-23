
## Architecture Overview

This is a YouTube channel processing tool that downloads video transcripts from a specified channel and generates AI-powered summaries. The architecture consists of:

### Core Components

**YouTubeChannelProcessor Class** (`youtube_downloader.py:17-371`)
- Main processing engine that handles both YouTube API and yt-dlp fallback methods
- Manages video discovery, download, and transcript extraction

**TranscriptSummarizer Class** (`transcript_summarizer.py:12-280`)
- AI-powered summarization using OpenAI's GPT models
- Processes transcript files and generates structured summaries
- Chapter-aware summarization: automatically detects and incorporates YouTube chapters
- Timestamp-based content mapping: assigns transcript text to specific chapters using timestamps
- Focuses on key points, actionable advice, and target audience insights

**Video Discovery Methods**
- Primary: YouTube Data API v3 for reliable channel and video metadata
- Fallback: yt-dlp for direct channel processing when API unavailable
- Handles various channel URL formats including @username handles

**Transcript Processing Pipeline**
1. Download subtitles (VTT format) using yt-dlp
2. Extract video metadata including chapter information
3. Parse VTT content preserving timestamps for chapter mapping
4. Organize transcript content by chapters using timestamp analysis (when chapters available)
5. Format into readable paragraphs with timestamp references and chapter organization
6. Save as organized text files with date-prefixed filenames

### Directory Structure
- `videos/` - Temporary storage for subtitle files (VTT files are removed after processing)
- `transcripts/` - Final processed transcript files in readable text format
- `summaries/` - AI-generated summaries of transcript files
- File naming convention: `YYYY-MM-DD_Video_Title.txt` (transcripts), `YYYY-MM-DD_Video_Title_summary.txt` (summaries)

### Key Dependencies
- `yt-dlp` - Video/subtitle downloading and metadata extraction
- `google-api-python-client` - YouTube Data API v3 integration
- `google-auth-*` - Authentication for YouTube API
- `openai` - AI-powered text summarization
- `python-dotenv` - Environment variable management

### Configuration
- Default channel: College Admission Secrets (`@collegeadmissionsecrets`)
- Default video limit: 50 videos
- Transcript formatting: 100 characters per line, grouped into logical paragraphs
- Language: English subtitles only
- Summarization: Configurable via `.env` file (model, max tokens, temperature)

### Environment Variables
All configuration is managed through a `.env` file:
- `OPENAI_API_KEY` - Required for summarization
- `YOUTUBE_API_KEY` - Optional, improves video discovery
- `OPENAI_MODEL` - Default: gpt-4.1 (latest GPT-4 model with 1M context)
- `OPENAI_MAX_TOKENS` - Default: 1000
- `OPENAI_TEMPERATURE` - Default: 0.3

The tool is designed to work with or without YouTube API access, automatically falling back to yt-dlp-only mode when API key is unavailable.


## Common Commands

### Setup and Dependencies
```bash
pip install -r requirements.txt
```

### Environment Setup
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your API keys
# OPENAI_API_KEY=your_openai_api_key_here
# YOUTUBE_API_KEY=your_youtube_api_key_here (optional)
```

### Run the YouTube Downloader
```bash
python youtube_downloader.py
```

### Run the Transcript Summarizer
```bash
python transcript_summarizer.py
```

### Test the Summarizer
```bash
python test_summarizer.py
```
