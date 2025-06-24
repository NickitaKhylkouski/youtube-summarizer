#!/usr/bin/env python3
"""
Script to generate JSON data from summary files for the web interface.
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path

def parse_summary_file(file_path):
    """Parse a summary file and extract structured data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title (first line after #)
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else "Untitled"
    
    # Extract date
    date_match = re.search(r'\*\*Date:\*\* (.+)$', content, re.MULTILINE)
    date = date_match.group(1) if date_match else ""
    
    # Extract overview
    overview_match = re.search(r'## 🎯 Overview\s*\n\n(.+?)(?=\n## |\Z)', content, re.DOTALL)
    overview = overview_match.group(1).strip() if overview_match else ""
    
    # Extract main topics
    topics_match = re.search(r'## 📝 Main Topics Covered\s*\n(.+?)(?=\n## |\Z)', content, re.DOTALL)
    topics = topics_match.group(1).strip() if topics_match else ""
    
    # Extract chapters if available
    chapters_match = re.search(r'## 📚 Chapter Breakdown\s*\n(.+?)(?=\n## |\Z)', content, re.DOTALL)
    chapters = chapters_match.group(1).strip() if chapters_match else ""
    
    # Parse date for sorting
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        sort_date = parsed_date.isoformat()
    except:
        sort_date = date
    
    return {
        'title': title,
        'date': date,
        'sort_date': sort_date,
        'overview': overview,
        'topics': topics,
        'chapters': chapters,
        'filename': os.path.basename(file_path),
        'content': content
    }

def generate_json_data():
    """Generate JSON data from all summary files."""
    summaries_dir = Path(__file__).parent.parent / 'summaries'
    data = []
    
    # Process all .txt files in summaries directory
    for file_path in summaries_dir.glob('*.txt'):
        if file_path.name.endswith('_summary.txt'):
            try:
                summary_data = parse_summary_file(file_path)
                data.append(summary_data)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    
    # Sort by date (newest first)
    data.sort(key=lambda x: x['sort_date'], reverse=True)
    
    # Write to JSON file
    output_file = Path(__file__).parent / 'data' / 'summaries.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(data)} summaries in {output_file}")
    return data

if __name__ == '__main__':
    generate_json_data()