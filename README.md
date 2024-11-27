# NJ Elections Web Crawler

A web crawler application that maps the link and data hierarchy of the New Jersey elections website. The crawler starts from a specific table on the elections page and follows links contained within it, providing real-time statistics and control through a web interface.

## Features

- Web-based control interface
- Real-time crawling statistics
- Start/Stop/Pause functionality
- Adjustable rate limiting
- Error logging
- WebSocket-based live updates

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. Clone the repository:
```bash
git clone [repository-url]
cd njdoescraper
```

2. Start the application using Docker Compose:
```bash
docker-compose up --build
```

3. Access the web interface:
- Open your browser and navigate to `http://localhost:8080`

## Usage

1. Open the web interface in your browser
2. Use the control panel to:
   - Start the crawler
   - Stop the crawler
   - Pause/Resume crawling
   - Adjust the rate limit
3. Monitor the crawling progress through:
   - Real-time statistics
   - Crawler log
   - Current URL display

## Configuration

The application can be configured using environment variables:

### Backend Environment Variables
- `FRONTEND_URL`: URL of the frontend service (default: http://localhost:8080)

### Frontend Environment Variables
- `API_URL`: URL of the backend API service (default: http://localhost:8000)

## Project Structure

```
njdoescraper/
├── backend/
│   ├── crawler.py      # Web crawler implementation
│   ├── main.py         # FastAPI server
│   ├── requirements.txt # Python dependencies
│   └── Dockerfile      # Backend container configuration
├── frontend/
│   ├── index.html      # Web interface
│   ├── main.js         # Frontend logic
│   └── Dockerfile      # Frontend container configuration
├── compose.yaml        # Docker Compose configuration
└── README.md          # This file
```

## Technical Details

- Backend: FastAPI (Python)
- Frontend: HTML/JavaScript with Tailwind CSS
- Real-time updates: WebSocket
- Web scraping: BeautifulSoup4 and aiohttp
- Containerization: Docker with multi-container setup

## Development

To run the application in development mode:

1. Start the backend:
```bash
cd backend
pip install -r requirements.txt
python main.py
```

2. Open the frontend:
- Navigate to the `frontend` directory
- Open `index.html` in a web browser

## Logs

Crawler logs are stored in the `logs` directory and are persisted through Docker volumes.
