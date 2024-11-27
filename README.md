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

## Quick Start with Docker (Recommended)

1. Clone the repository:
```bash
git clone [repository-url]
cd njdoescraper
```

2. Build and start the application using Docker Compose:
```bash
docker-compose up --build
```

3. Access the web interface:
- Open your browser and navigate to `http://localhost:8080`

## Usage

The application runs as a set of Docker containers:

1. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

2. The application will be available at the following URLs:
   - Frontend: `http://<your-host>:8080`
   - Backend API: `http://<your-host>:8000`

## Environment Variables

### Backend Service
- `ALLOWED_ORIGINS`: Allowed CORS origins (default: http://frontend:80)
- `ALLOWED_METHODS`: Allowed HTTP methods (default: *)
- `ALLOWED_HEADERS`: Allowed HTTP headers (default: *)
- `FRONTEND_URL`: URL of the frontend service (default: http://localhost:8080)

### Frontend Service
- `API_URL`: URL of the backend API service (default: http://backend:8000)

Other configurations:
- Default rate limit: 1 second between requests
- Starting URL: https://www.nj.gov/state/elections/election-information-results.shtml
- Starting XPath: /html/body/div[8]/div/div/div[1]/div/div/table

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

## Logs

Crawler logs are stored in the `logs` directory and are persisted through Docker volumes.
