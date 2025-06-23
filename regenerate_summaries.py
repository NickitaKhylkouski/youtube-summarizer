#!/usr/bin/env python3
"""
Regenerate all summaries with improved formatting
"""

import os
from pathlib import Path
from transcript_summarizer import TranscriptSummarizer

def regenerate_all_summaries():
    """Regenerate all summaries with improved formatting"""
    try:
        # Initialize summarizer
        summarizer = TranscriptSummarizer()
        
        # Get all transcript files
        transcripts_dir = Path('transcripts')
        transcript_files = list(transcripts_dir.glob('*.txt'))
        
        if not transcript_files:
            print("No transcript files found!")
            return
        
        print(f"Found {len(transcript_files)} transcript files")
        print("Regenerating all summaries with improved formatting...")
        
        successful = 0
        failed = 0
        
        for i, transcript_path in enumerate(transcript_files, 1):
            print(f"\n[{i}/{len(transcript_files)}] Processing: {transcript_path.name}")
            
            # Remove existing summary to force regeneration
            summary_filename = transcript_path.name.replace('.txt', '_summary.txt')
            summary_path = Path('summaries') / summary_filename
            
            if summary_path.exists():
                summary_path.unlink()
                print(f"Removed existing summary")
            
            # Process the file
            if summarizer.process_single_transcript(transcript_path):
                successful += 1
                print(f"✅ Success")
            else:
                failed += 1
                print(f"❌ Failed")
        
        print(f"\n🎉 Regeneration complete!")
        print(f"Successfully processed: {successful}")
        print(f"Failed: {failed}")
        print(f"All summaries saved in: summaries/")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    regenerate_all_summaries()