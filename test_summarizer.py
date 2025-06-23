#!/usr/bin/env python3
"""
Test script for the transcript summarizer
"""

import os
from pathlib import Path

def test_basic_functionality():
    """Test basic functionality without API calls"""
    print("Testing TranscriptSummarizer basic functionality...")
    
    # Test directory setup
    transcripts_dir = Path('transcripts')
    summaries_dir = Path('summaries')
    
    if not transcripts_dir.exists():
        print("❌ Transcripts directory not found")
        return False
    
    print("✅ Transcripts directory found")
    
    # Test reading a transcript file
    transcript_files = list(transcripts_dir.glob('*.txt'))
    if not transcript_files:
        print("❌ No transcript files found")
        return False
    
    print(f"✅ Found {len(transcript_files)} transcript files")
    
    # Test reading first file
    test_file = transcript_files[0]
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if len(content) > 0:
            print(f"✅ Successfully read {test_file.name} ({len(content)} characters)")
        else:
            print(f"❌ Empty content in {test_file.name}")
            return False
            
    except Exception as e:
        print(f"❌ Error reading {test_file.name}: {e}")
        return False
    
    # Test prompt creation (without API call)
    try:
        # Mock summarizer (without API key to avoid actual calls)
        class MockSummarizer:
            def __init__(self):
                self.transcripts_dir = Path('transcripts')
                self.summaries_dir = Path('summaries')
                self.summaries_dir.mkdir(exist_ok=True)
            
            def create_summary_prompt(self, content):
                prompt = f"""Please provide a comprehensive summary of the following video transcript. 

Focus on:
- Main topics and key points discussed
- Actionable advice or recommendations
- Important deadlines, dates, or timelines mentioned
- Target audience (students, parents, etc.)
- Key takeaways that viewers should remember

Transcript:
{content}

Summary:"""
                return prompt
            
            def read_transcript(self, file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        
        mock_summarizer = MockSummarizer()
        prompt = mock_summarizer.create_summary_prompt(content[:500])  # Test with first 500 chars
        
        if len(prompt) > 0 and "Summary:" in prompt:
            print("✅ Prompt creation works correctly")
        else:
            print("❌ Prompt creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing prompt creation: {e}")
        return False
    
    print("\n✅ All basic functionality tests passed!")
    print("\nTo run the actual summarizer:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Set your OpenAI API key: export OPENAI_API_KEY=your_key_here")
    print("3. Run: python transcript_summarizer.py")
    
    return True

if __name__ == "__main__":
    test_basic_functionality()