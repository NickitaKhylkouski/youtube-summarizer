#!/usr/bin/env python3
"""
YouTube Channel Video Downloader and Transcript Extractor
Downloads last 20 videos from a YouTube channel and extracts transcripts.
"""

import os
import json
import re
import textwrap
from pathlib import Path
import yt_dlp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class YouTubeChannelProcessor:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.youtube = None
        if api_key:
            self.youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Create output directories
        self.videos_dir = Path('videos')
        self.transcripts_dir = Path('transcripts')
        self.videos_dir.mkdir(exist_ok=True)
        self.transcripts_dir.mkdir(exist_ok=True)
    
    def get_channel_id_from_url(self, channel_url):
        """Extract channel ID from YouTube channel URL"""
        # Handle @username format
        if '@' in channel_url:
            username = channel_url.split('@')[-1].split('/')[0]
            if self.youtube:
                try:
                    request = self.youtube.search().list(
                        part='snippet',
                        q=username,
                        type='channel',
                        maxResults=1
                    )
                    response = request.execute()
                    if response['items']:
                        return response['items'][0]['snippet']['channelId']
                except HttpError as e:
                    print(f"Error finding channel: {e}")
            return None
        
        # Handle direct channel ID or channel URL
        if 'channel/' in channel_url:
            return channel_url.split('channel/')[-1]
        return channel_url
    
    def get_latest_videos(self, channel_url, max_results=20):
        """Get latest videos from a YouTube channel"""
        channel_id = self.get_channel_id_from_url(channel_url)
        
        if not channel_id and not self.youtube:
            # Fallback: use yt-dlp to get video URLs
            return self.get_videos_with_ytdlp(channel_url, max_results)
        
        if not self.youtube:
            print("No YouTube API key provided, using yt-dlp fallback")
            return self.get_videos_with_ytdlp(channel_url, max_results)
        
        try:
            # Get channel's uploads playlist
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from uploads playlist
            playlist_response = self.youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=max_results
            ).execute()
            
            videos = []
            for item in playlist_response['items']:
                video_data = {
                    'id': item['snippet']['resourceId']['videoId'],
                    'title': item['snippet']['title'],
                    'url': f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}",
                    'published_at': item['snippet']['publishedAt']
                }
                videos.append(video_data)
            
            return videos
            
        except HttpError as e:
            print(f"Error accessing YouTube API: {e}")
            return self.get_videos_with_ytdlp(channel_url, max_results)
    
    def get_videos_with_ytdlp(self, channel_url, max_results=20):
        """Fallback method to get videos using yt-dlp"""
        ydl_opts = {
            'quiet': True,
            'extract_flat': False,  # Changed to False to get more metadata
            'playlistend': max_results
        }
        
        videos = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(channel_url, download=False)
                if 'entries' in info:
                    for entry in info['entries'][:max_results]:
                        if entry:  # Check if entry exists
                            # Get upload date in various possible formats
                            upload_date = (entry.get('upload_date') or 
                                         entry.get('timestamp') or 
                                         entry.get('release_date') or 
                                         'unknown')
                            
                            video_data = {
                                'id': entry.get('id', 'unknown'),
                                'title': entry.get('title', 'Unknown Title'),
                                'url': entry.get('webpage_url') or entry.get('url', ''),
                                'published_at': upload_date
                            }
                            videos.append(video_data)
            except Exception as e:
                print(f"Error extracting video list: {e}")
        
        return videos
    
    def download_video_and_transcript(self, video_data):
        """Download subtitles, extract transcript, and get chapter information"""
        video_id = video_data['id']
        
        # Format date from published_at
        published_date = video_data.get('published_at', '')
        if published_date and published_date != 'unknown':
            try:
                # Handle different date formats
                if isinstance(published_date, (int, float)):
                    # Unix timestamp
                    import datetime
                    dt = datetime.datetime.fromtimestamp(published_date)
                    formatted_date = dt.strftime('%Y-%m-%d')
                elif 'T' in str(published_date):
                    # ISO format: 2024-06-15T10:30:00Z
                    date_part = str(published_date).split('T')[0]
                    formatted_date = date_part
                elif len(str(published_date)) == 8 and str(published_date).isdigit():
                    # YYYYMMDD format (common from yt-dlp)
                    date_str = str(published_date)
                    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                elif len(str(published_date)) >= 10:
                    # Already in YYYY-MM-DD format or similar
                    date_part = str(published_date)[:10]
                    if '-' in date_part:
                        formatted_date = date_part
                    else:
                        formatted_date = "unknown-date"
                else:
                    formatted_date = "unknown-date"
            except Exception as e:
                print(f"Error parsing date '{published_date}': {e}")
                formatted_date = "unknown-date"
        else:
            formatted_date = "unknown-date"
        
        # Clean title and create filename with date prefix
        clean_title = re.sub(r'[<>:"/\\|?*]', '_', video_data['title'])[:80]  # Reduced to 80 chars for date prefix
        filename = f"{formatted_date}_{clean_title}"
        
        # Check if transcript already exists
        transcript_file = self.transcripts_dir / f'{filename}.txt'
        if transcript_file.exists():
            print(f"Transcript already exists for {filename}, skipping...")
            return True
        
        print(f"Processing: {filename}")
        
        # Configure yt-dlp options
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'subtitlesformat': 'vtt',
            'skip_download': True,  # Only download subtitles, not videos
            'outtmpl': str(self.videos_dir / f'{filename}.%(ext)s'),
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Download subtitles only
                ydl.download([video_data['url']])
                
                # Get video info for chapters
                video_info = ydl.extract_info(video_data['url'], download=False)
                chapters = video_info.get('chapters', []) if video_info else []
                
                # Extract and save clean transcript with chapter info
                self.extract_clean_transcript(video_id, filename, chapters)
                
                return True
            except Exception as e:
                print(f"Error downloading {filename}: {e}")
                return False
    
    def extract_clean_transcript(self, video_id, filename, chapters=None):
        """Extract clean text from VTT subtitle file and format for readability with chapter markers"""
        # Look for subtitle files
        vtt_files = list(self.videos_dir.glob(f'{filename}.*.vtt'))
        
        if not vtt_files:
            print(f"No subtitle file found for {filename}")
            return
        
        vtt_file = vtt_files[0]
        transcript_text = []
        seen_lines = set()  # Track seen lines to avoid duplicates
        
        try:
            with open(vtt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse VTT content by segments, preserving timestamps
            segments = content.split('\n\n')
            
            for segment in segments:
                lines = segment.strip().split('\n')
                if len(lines) < 2:
                    continue
                
                timestamp = None
                text_lines = []
                
                # Extract timestamp and text
                if '-->' in lines[0]:
                    # First line has timestamp
                    timestamp = lines[0]
                    text_lines = lines[1:]
                elif len(lines) > 1 and '-->' in lines[1]:
                    # Second line has timestamp
                    timestamp = lines[1]
                    text_lines = lines[2:] if len(lines) > 2 else []
                else:
                    continue
                
                # Process text lines with timestamp
                for line in text_lines:
                    line = line.strip()
                    if line and not line.startswith('WEBVTT') and not line.startswith('NOTE'):
                        # Remove HTML tags and clean up
                        clean_line = re.sub(r'<[^>]+>', '', line)
                        clean_line = clean_line.strip()
                        
                        if clean_line and clean_line not in seen_lines:
                            # Extract start time from timestamp
                            if timestamp and '-->' in timestamp:
                                start_time = timestamp.split('-->')[0].strip()
                                # Format: [HH:MM:SS.mmm] text
                                transcript_entry = f"[{start_time}] {clean_line}"
                                transcript_text.append(transcript_entry)
                                seen_lines.add(clean_line)
            
            if not transcript_text:
                print(f"No transcript content found for {filename}")
                return
            
            # Format transcript for better readability with chapters
            formatted_transcript = self.format_transcript_with_chapters(transcript_text, chapters)
            
            # Save formatted transcript
            transcript_file = self.transcripts_dir / f'{filename}.txt'
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(formatted_transcript)
            
            print(f"Transcript saved: {transcript_file}")
            
            # Optionally remove the VTT file
            vtt_file.unlink()
            
        except Exception as e:
            print(f"Error processing transcript for {filename}: {e}")
    
    def format_transcript(self, transcript_lines):
        """Format transcript for better readability with proper paragraphs and line wrapping"""
        if not transcript_lines:
            return ""
        
        # Join all lines into one text block
        full_text = ' '.join(transcript_lines)
        
        # Split into sentences (roughly)
        sentences = re.split(r'[.!?]+\s+', full_text)
        
        # Group sentences into paragraphs (every 4-6 sentences)
        paragraphs = []
        current_paragraph = []
        sentence_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            current_paragraph.append(sentence)
            sentence_count += 1
            
            # Create paragraph break every 4-6 sentences or at natural breaks
            if (sentence_count >= 4 and 
                (sentence_count >= 6 or 
                 any(keyword in sentence.lower() for keyword in [
                     'so', 'now', 'but', 'however', 'first', 'second', 'third', 
                     'next', 'then', 'finally', 'in conclusion', 'moving on',
                     'let me', 'let\'s', 'okay', 'alright', 'well'
                 ]))):
                
                if current_paragraph:
                    # Join sentences with proper punctuation
                    paragraph_text = '. '.join(current_paragraph)
                    if not paragraph_text.endswith(('.', '!', '?')):
                        paragraph_text += '.'
                    paragraphs.append(paragraph_text)
                    current_paragraph = []
                    sentence_count = 0
        
        # Add any remaining sentences
        if current_paragraph:
            paragraph_text = '. '.join(current_paragraph)
            if not paragraph_text.endswith(('.', '!', '?')):
                paragraph_text += '.'
            paragraphs.append(paragraph_text)
        
        # Format each paragraph to max 100 characters per line
        formatted_lines = []
        for paragraph in paragraphs:
            if paragraph.strip():
                # Wrap paragraph to 100 characters per line
                wrapped_lines = textwrap.wrap(
                    paragraph, 
                    width=100, 
                    break_long_words=False, 
                    break_on_hyphens=False
                )
                formatted_lines.extend(wrapped_lines)
        
        # Join all lines with single newlines (no blank lines)
        return '\n'.join(formatted_lines)
    
    def format_transcript_with_chapters(self, transcript_lines, chapters=None):
        """Format transcript with chapter markers and timestamp-based organization"""
        if not chapters:
            # If no chapters, format with timestamps but no chapter divisions
            return self.format_transcript_with_timestamps(transcript_lines)
        
        # If chapters exist, organize transcript by chapters using timestamps
        formatted_content = []
        
        # Add chapter information header
        formatted_content.append("=== VIDEO CHAPTERS ===\n")
        for i, chapter in enumerate(chapters, 1):
            start_time = chapter.get('start_time', 0)
            title = chapter.get('title', f'Chapter {i}')
            minutes = int(start_time // 60)
            seconds = int(start_time % 60)
            formatted_content.append(f"{i}. {title} ({minutes:02d}:{seconds:02d})")
        
        formatted_content.append("\n=== TRANSCRIPT BY CHAPTERS ===\n")
        
        # Organize transcript lines by chapters based on timestamps
        chapter_content = self.organize_transcript_by_chapters(transcript_lines, chapters)
        
        for i, chapter in enumerate(chapters):
            chapter_title = chapter.get('title', f'Chapter {i+1}')
            start_time = chapter.get('start_time', 0)
            minutes = int(start_time // 60)
            seconds = int(start_time % 60)
            
            formatted_content.append(f"\n## Chapter {i+1}: {chapter_title} ({minutes:02d}:{seconds:02d})\n")
            
            if i in chapter_content:
                # Format the chapter content nicely
                chapter_text = self.format_chapter_content(chapter_content[i])
                formatted_content.append(chapter_text)
            else:
                formatted_content.append("No content found for this chapter.\n")
        
        return '\n'.join(formatted_content)
    
    def format_transcript_with_timestamps(self, transcript_lines):
        """Format transcript preserving timestamps but without chapters"""
        formatted_content = []
        formatted_content.append("=== TRANSCRIPT WITH TIMESTAMPS ===\n")
        
        # Group lines into paragraphs while preserving timestamps
        current_paragraph = []
        for line in transcript_lines:
            if line.strip():
                current_paragraph.append(line)
                
                # Create paragraph breaks every 4-6 lines
                if len(current_paragraph) >= 5:
                    formatted_content.append(' '.join(current_paragraph))
                    formatted_content.append('')  # Add blank line
                    current_paragraph = []
        
        # Add any remaining content
        if current_paragraph:
            formatted_content.append(' '.join(current_paragraph))
        
        return '\n'.join(formatted_content)
    
    def organize_transcript_by_chapters(self, transcript_lines, chapters):
        """Organize transcript lines by chapters based on timestamps"""
        chapter_content = {}
        
        # Convert chapter start times to seconds for comparison
        chapter_times = []
        for i, chapter in enumerate(chapters):
            start_time = chapter.get('start_time', 0)
            chapter_times.append((start_time, i))
        
        # Sort chapters by start time
        chapter_times.sort()
        
        # Assign transcript lines to chapters
        for line in transcript_lines:
            if not line.strip():
                continue
                
            # Extract timestamp from line format: [HH:MM:SS.mmm] text
            if line.startswith('[') and ']' in line:
                timestamp_str = line.split(']')[0][1:]  # Remove [ and ]
                try:
                    # Convert timestamp to seconds
                    time_parts = timestamp_str.split(':')
                    if len(time_parts) >= 3:
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        seconds = float(time_parts[2])
                        total_seconds = hours * 3600 + minutes * 60 + seconds
                        
                        # Find which chapter this timestamp belongs to
                        chapter_index = 0
                        for start_time, idx in chapter_times:
                            if total_seconds >= start_time:
                                chapter_index = idx
                            else:
                                break
                        
                        # Add line to appropriate chapter
                        if chapter_index not in chapter_content:
                            chapter_content[chapter_index] = []
                        chapter_content[chapter_index].append(line)
                        
                except (ValueError, IndexError):
                    # If timestamp parsing fails, add to first chapter
                    if 0 not in chapter_content:
                        chapter_content[0] = []
                    chapter_content[0].append(line)
        
        return chapter_content
    
    def format_chapter_content(self, lines):
        """Format content for a specific chapter"""
        if not lines:
            return "No content found for this chapter."
        
        # Remove timestamps and create readable paragraphs
        text_lines = []
        for line in lines:
            if ']' in line:
                text = line.split(']', 1)[1].strip()  # Remove timestamp
                if text:
                    text_lines.append(text)
        
        # Group into paragraphs
        paragraphs = []
        current_paragraph = []
        
        for text in text_lines:
            current_paragraph.append(text)
            
            # Create paragraph breaks every 4-5 sentences
            if len(current_paragraph) >= 4:
                paragraph_text = ' '.join(current_paragraph)
                paragraphs.append(paragraph_text)
                current_paragraph = []
        
        # Add any remaining content
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            paragraphs.append(paragraph_text)
        
        return '\n\n'.join(paragraphs)
    
    def process_channel(self, channel_url, max_videos=50):
        """Main method to process entire channel"""
        print(f"Processing channel: {channel_url}")
        print(f"Getting latest {max_videos} videos...")
        
        videos = self.get_latest_videos(channel_url, max_videos)
        
        if not videos:
            print("No videos found!")
            return
        
        print(f"Found {len(videos)} videos")
        
        successful_downloads = 0
        for i, video in enumerate(videos, 1):
            print(f"\n[{i}/{len(videos)}] Processing video...")
            if self.download_video_and_transcript(video):
                successful_downloads += 1
        
        print(f"\nCompleted! Successfully processed {successful_downloads}/{len(videos)} videos")
        print(f"Videos saved in: {self.videos_dir}")
        print(f"Transcripts saved in: {self.transcripts_dir}")


def main():
    # Configuration
    CHANNEL_URL = "https://www.youtube.com/@collegeadmissionsecrets/videos"
    MAX_VIDEOS = 200
    
    # Optional: Add your YouTube Data API key here for better performance
    # Get it from: https://console.developers.google.com/
    API_KEY = os.getenv('YOUTUBE_API_KEY')  # Set as environment variable
    
    # Initialize processor
    processor = YouTubeChannelProcessor(api_key=API_KEY)
    
    # Process the channel
    processor.process_channel(CHANNEL_URL, MAX_VIDEOS)


if __name__ == "__main__":
    main()