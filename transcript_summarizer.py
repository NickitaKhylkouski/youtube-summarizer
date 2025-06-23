#!/usr/bin/env python3
"""
Transcript Summarizer
Summarizes transcript files using OpenAI's API and saves summaries to a summary folder.
"""

import os
import json
from pathlib import Path
import openai
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class TranscriptSummarizer:
    def __init__(self, api_key=None):
        """Initialize the summarizer with OpenAI API key"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Setup directories
        self.transcripts_dir = Path('transcripts')
        self.summaries_dir = Path('summaries')
        self.summaries_dir.mkdir(exist_ok=True)
        
        # Summarization settings (configurable via .env)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '500'))
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
    
    def read_transcript(self, file_path):
        """Read transcript content from file and extract chapter information"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Check if transcript contains chapter information
            chapters, chapter_content = self.extract_chapters(content)
            return content, chapters, chapter_content
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None, None, None
    
    def extract_chapters(self, content):
        """Extract chapter information and chapter-organized content from transcript"""
        chapters = []
        chapter_content = {}
        lines = content.split('\n')
        
        # Look for chapter markers
        in_chapters_section = False
        in_chapter_content = False
        current_chapter_index = None
        
        for line in lines:
            if '=== VIDEO CHAPTERS ===' in line:
                in_chapters_section = True
                continue
            elif '=== TRANSCRIPT BY CHAPTERS ===' in line:
                in_chapters_section = False
                in_chapter_content = True
                continue
            elif in_chapters_section and line.strip():
                # Parse chapter line: "1. Chapter Title (mm:ss)"
                if line.strip() and not line.startswith('='):
                    chapters.append(line.strip())
            elif in_chapter_content and line.startswith('## Chapter'):
                # New chapter section: "## Chapter 1: Title (mm:ss)"
                try:
                    chapter_num = int(line.split(':')[0].split()[-1]) - 1  # Convert to 0-based index
                    current_chapter_index = chapter_num
                    if current_chapter_index not in chapter_content:
                        chapter_content[current_chapter_index] = []
                except (ValueError, IndexError):
                    current_chapter_index = None
            elif in_chapter_content and current_chapter_index is not None and line.strip():
                # Add content to current chapter
                chapter_content[current_chapter_index].append(line.strip())
        
        return chapters, chapter_content
    
    def format_text_for_readability(self, text):
        """Format text with better line breaks for readability"""
        import textwrap
        
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Skip empty lines and preserve them
            if not line.strip():
                formatted_lines.append(line)
                continue
            
            # For long lines (>100 characters), break them up
            if len(line) > 100:
                # Preserve markdown headers as-is if they're not too long
                if line.strip().startswith('#') and len(line) < 120:
                    formatted_lines.append(line)
                    continue
                
                # Handle list items (bullets and numbered)
                if line.strip().startswith(('-', '*')):
                    # Find the bullet and preserve indentation
                    indent = len(line) - len(line.lstrip())
                    bullet_pos = line.find('-', indent) if '-' in line else line.find('*', indent)
                    if bullet_pos >= 0:
                        prefix = line[:bullet_pos + 2]  # Include bullet and space
                        content = line[bullet_pos + 2:].strip()
                        
                        # Wrap the content
                        wrapped = textwrap.fill(content, width=75, 
                                              initial_indent=prefix,
                                              subsequent_indent=' ' * len(prefix))
                        formatted_lines.append(wrapped)
                        continue
                
                # Handle numbered lists
                stripped = line.lstrip()
                if stripped and stripped[0].isdigit() and '.' in stripped[:5]:
                    # Find the number and period
                    period_pos = stripped.find('.')
                    if period_pos > 0:
                        indent = len(line) - len(stripped)
                        prefix = line[:indent + period_pos + 2]  # Include number, period and space
                        content = line[indent + period_pos + 2:].strip()
                        
                        # Wrap the content
                        wrapped = textwrap.fill(content, width=75,
                                              initial_indent=prefix,
                                              subsequent_indent=' ' * len(prefix))
                        formatted_lines.append(wrapped)
                        continue
                
                # For regular paragraphs, just wrap normally
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                content = line.strip()
                
                wrapped = textwrap.fill(content, width=80,
                                      initial_indent=indent_str,
                                      subsequent_indent=indent_str)
                formatted_lines.append(wrapped)
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def create_summary_prompt(self, transcript_content, chapters=None, chapter_content=None):
        """Create a prompt for summarizing the transcript"""
        chapter_instruction = ""
        if chapters and chapter_content:
            chapter_instruction = f"""
**IMPORTANT: This video has chapters with content already organized by timestamp. Please create a detailed summary that follows this chapter structure:**

CHAPTERS:
{chr(10).join(chapters)}

The transcript content is already organized by chapters. In your summary, reference specific chapters and organize your analysis according to this structure. Pay special attention to the '📚 Chapter Breakdown' section where you should provide detailed analysis of each chapter's content.
"""
        elif chapters:
            chapter_instruction = f"""
**IMPORTANT: This video has chapters. Please organize your summary to align with these chapters where possible:**
{chr(10).join(chapters)}

When summarizing, reference specific chapters in your analysis and organize content according to the chapter structure.
"""
        
        prompt = f"""Please provide a comprehensive, detailed summary of the following video transcript. Create a well-structured, in-depth analysis that captures all important information, strategies, and insights.

{chapter_instruction}

Format your response exactly as follows:

# VIDEO SUMMARY

## 🎯 Overview
[Provide a detailed 4-5 sentence overview explaining what this video covers, the main educational goals, and the context/background of the content]

## 📚 Chapter Breakdown
[If chapters exist, provide a detailed analysis of each chapter. Format each chapter description with proper line breaks for readability. Break long paragraphs into shorter lines (60-80 characters) and use multiple paragraphs when needed. If no chapters, state "This video does not have defined chapters."]

## 📝 Main Topics Covered
[Provide a comprehensive list of all major topics, subtopics, and themes discussed. Include specific strategies, frameworks, methods, and concepts mentioned]
- [Topic 1 with detailed explanation]
- [Topic 2 with detailed explanation]
- [Topic 3 with detailed explanation]
- [Continue with all relevant topics...]

## 💡 Key Takeaways & Insights
[Provide detailed explanations of the most important lessons, strategies, and insights. Include specific examples, data points, statistics, or case studies mentioned]
1. [Detailed key point 1 with explanation and context]
2. [Detailed key point 2 with explanation and context]
3. [Detailed key point 3 with explanation and context]
[Continue with all significant takeaways...]

## 🎯 Actionable Strategies & Recommendations
[Provide specific, detailed action items organized by category. Include step-by-step processes, timelines, and implementation details]

### For Students:
- [Detailed strategy 1 with implementation steps]
- [Detailed strategy 2 with implementation steps]
- [Continue with all student-specific advice...]

### For Parents:
- [Detailed strategy 1 with implementation steps]
- [Detailed strategy 2 with implementation steps]
- [Continue with all parent-specific advice...]

### Timeline & Deadlines:
- [Specific dates, deadlines, and timing recommendations with explanations]
- [Grade-level specific timing advice]
- [Seasonal or annual planning recommendations]

## 📊 Specific Details & Examples
[Include any specific examples, case studies, success stories, statistics, or data points mentioned in the video]
- [Specific example 1 with details]
- [Specific example 2 with details]
- [Continue with all relevant specifics...]

## ⚠️ Critical Warnings & Common Mistakes
[Provide detailed explanations of mistakes to avoid, potential pitfalls, and important cautions mentioned]
- [Detailed warning 1 with explanation of consequences]
- [Detailed warning 2 with explanation of consequences]
- [Continue with all warnings and mistakes to avoid...]

## 🔗 Resources & Next Steps
[Include any specific resources, tools, websites, programs, or follow-up actions recommended in the video]
- [Resource 1 with description and how to access]
- [Resource 2 with description and how to access]
- [Continue with all mentioned resources...]

---

Transcript:
{transcript_content}"""
        return prompt
    
    def summarize_with_openai(self, transcript_content, chapters=None, chapter_content=None):
        """Generate summary using OpenAI API"""
        try:
            prompt = self.create_summary_prompt(transcript_content, chapters, chapter_content)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates clear, concise summaries of educational video transcripts about college admissions and academic preparation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            summary = response.choices[0].message.content.strip()
            # Format the summary for better readability
            formatted_summary = self.format_text_for_readability(summary)
            return formatted_summary
            
        except Exception as e:
            print(f"Error generating summary with OpenAI: {e}")
            return None
    
    def save_summary(self, summary, original_filename):
        """Save summary to file with header information"""
        try:
            # Create summary filename
            summary_filename = original_filename.replace('.txt', '_summary.txt')
            summary_path = self.summaries_dir / summary_filename
            
            # Extract title and date from filename
            title_clean = original_filename.replace('.txt', '').replace('_', ' ')
            date_part = title_clean.split(' ', 1)[0] if title_clean else 'Unknown Date'
            title_part = title_clean.split(' ', 1)[1] if len(title_clean.split(' ', 1)) > 1 else 'Unknown Title'
            
            # Create formatted content with header
            formatted_content = f"""# {title_part}
**Date:** {date_part}  
**Original File:** {original_filename}

---

{summary}

---
*Summary generated by AI using OpenAI's {self.model} model*
"""
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            print(f"Summary saved: {summary_path}")
            return True
            
        except Exception as e:
            print(f"Error saving summary for {original_filename}: {e}")
            return False
    
    def process_single_transcript(self, transcript_path):
        """Process a single transcript file"""
        print(f"Processing: {transcript_path.name}")
        
        # Read transcript and extract chapters
        content, chapters, chapter_content = self.read_transcript(transcript_path)
        if not content:
            return False
        
        # Check if transcript is too short to summarize
        if len(content.split()) < 50:
            print(f"Skipping {transcript_path.name} - too short to summarize")
            return False
        
        # Generate summary with chapter information
        summary = self.summarize_with_openai(content, chapters, chapter_content)
        if not summary:
            return False
        
        # Save summary
        return self.save_summary(summary, transcript_path.name)
    
    def process_all_transcripts(self, skip_existing=True):
        """Process all transcript files in the transcripts directory"""
        if not self.transcripts_dir.exists():
            print(f"Transcripts directory not found: {self.transcripts_dir}")
            return
        
        # Get all transcript files
        transcript_files = list(self.transcripts_dir.glob('*.txt'))
        
        if not transcript_files:
            print("No transcript files found!")
            return
        
        print(f"Found {len(transcript_files)} transcript files")
        
        successful_summaries = 0
        skipped_files = 0
        
        for i, transcript_path in enumerate(transcript_files, 1):
            print(f"\n[{i}/{len(transcript_files)}]", end=" ")
            
            # Check if summary already exists
            summary_filename = transcript_path.name.replace('.txt', '_summary.txt')
            summary_path = self.summaries_dir / summary_filename
            
            if skip_existing and summary_path.exists():
                print(f"Skipping {transcript_path.name} - summary already exists")
                skipped_files += 1
                continue
            
            # Process transcript
            if self.process_single_transcript(transcript_path):
                successful_summaries += 1
            else:
                print(f"Failed to process {transcript_path.name}")
        
        print(f"\nCompleted!")
        print(f"Successfully summarized: {successful_summaries}")
        print(f"Skipped (already exists): {skipped_files}")
        print(f"Failed: {len(transcript_files) - successful_summaries - skipped_files}")
        print(f"Summaries saved in: {self.summaries_dir}")
    
    def process_specific_files(self, filenames):
        """Process specific transcript files by name"""
        successful_summaries = 0
        
        for filename in filenames:
            transcript_path = self.transcripts_dir / filename
            
            if not transcript_path.exists():
                print(f"File not found: {filename}")
                continue
            
            if self.process_single_transcript(transcript_path):
                successful_summaries += 1
        
        print(f"\nProcessed {successful_summaries}/{len(filenames)} files successfully")


def main():
    """Main function to run the summarizer"""
    # Configuration
    API_KEY = os.getenv('OPENAI_API_KEY')
    
    if not API_KEY:
        print("Error: OpenAI API key not found!")
        print("Set your API key as an environment variable:")
        print("export OPENAI_API_KEY=your_api_key_here")
        return
    
    try:
        # Initialize summarizer
        summarizer = TranscriptSummarizer(api_key=API_KEY)
        
        # Process all transcripts
        # Set skip_existing=False to re-process existing summaries
        summarizer.process_all_transcripts(skip_existing=True)
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()