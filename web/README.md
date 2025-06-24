# YouTube Summary Viewer

A web interface to browse and search through AI-generated YouTube video summaries.

## Features

- **Browse Summaries**: View all 128+ video summaries in a clean, card-based layout
- **Search**: Full-text search across titles, overviews, topics, and chapters
- **Sort**: Sort by date (newest/oldest) or title (A-Z/Z-A)
- **Modal View**: Click any summary card to view the full content in a modal
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Tags**: Automatically extracted topic tags for quick identification

## Getting Started

1. **Generate the data file**:
   ```bash
   cd web
   python3 generate_data.py
   ```

2. **Serve the website**:
   You can use any local web server. Here are a few options:

   **Python (recommended)**:
   ```bash
   cd web
   python3 -m http.server 8000
   ```
   Then open http://localhost:8000

   **Node.js (if you have it)**:
   ```bash
   cd web
   npx serve .
   ```

   **PHP (if you have it)**:
   ```bash
   cd web
   php -S localhost:8000
   ```

3. **Open in browser**: Navigate to the local server URL

## File Structure

```
web/
├── index.html          # Main HTML template
├── css/
│   └── styles.css      # All styling and responsive design
├── js/
│   └── app.js          # JavaScript functionality
├── data/
│   └── summaries.json  # Generated data from summary files
├── generate_data.py    # Python script to create JSON data
└── README.md          # This file
```

## How It Works

1. **Data Generation**: `generate_data.py` reads all `*_summary.txt` files from the `../summaries/` directory and converts them into a structured JSON format
2. **Web Interface**: The HTML/CSS/JS frontend loads the JSON data and provides an interactive interface
3. **Search & Filter**: JavaScript handles real-time search and sorting without page reloads
4. **Modal Display**: Full summary content is displayed in a modal overlay when cards are clicked

## Customization

- **Colors**: Edit CSS custom properties in `styles.css`
- **Layout**: Modify the grid system in `.summaries-grid`
- **Data Fields**: Update `generate_data.py` to extract additional fields from summary files
- **Search**: Extend search functionality in `app.js` to include more fields

## Updating Data

When new summary files are added to the `summaries/` directory, run the data generation script again:

```bash
cd web
python3 generate_data.py
```

The website will automatically reflect the new summaries on the next page load.