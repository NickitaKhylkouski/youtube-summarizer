#!/usr/bin/env python3
"""
Test script to process a single transcript with improved formatting
"""

import os
from pathlib import Path
from transcript_summarizer import TranscriptSummarizer

def test_single_file():
    """Test processing a single transcript file"""
    try:
        # Initialize summarizer
        summarizer = TranscriptSummarizer()
        
        # Get the first transcript file
        transcripts_dir = Path('transcripts')
        transcript_files = list(transcripts_dir.glob('*.txt'))
        
        if not transcript_files:
            print("No transcript files found!")
            return
        
        # Process just the first file
        test_file = transcript_files[0]
        print(f"Testing with file: {test_file.name}")
        
        # Remove existing summary if it exists to force regeneration
        summary_filename = test_file.name.replace('.txt', '_summary.txt')
        summary_path = Path('summaries') / summary_filename
        
        if summary_path.exists():
            summary_path.unlink()
            print(f"Removed existing summary: {summary_filename}")
        
        # Process the file
        success = summarizer.process_single_transcript(test_file)
        
        if success:
            print(f"\n✅ Successfully processed {test_file.name}")
            print(f"Check the summary at: summaries/{summary_filename}")
        else:
            print(f"❌ Failed to process {test_file.name}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_single_file()