# YouTube Agent

An AI-powered chat interface that answers questions by searching YouTube, reading video transcripts, and analyzing comments — powered by Gemini 2.5 Flash.

## How it works

When you ask a question, the agent automatically:
1. Searches YouTube for relevant videos (multiple queries, 10+ results)
2. Reads the transcripts of the most relevant videos (5+)
3. Fetches top comments to surface tips and community insights
4. Synthesizes a response based entirely on that content

## Tools

| Tool | Description |
|------|-------------|
| `search_youtube` | Search YouTube for videos by query. Filters out Shorts by default. Returns title, channel, views, and video ID. |
| `get_transcript` | Extract the full transcript from a video by URL or ID. Optionally includes timestamps. |
| `get_comments` | Fetch top or newest comments from a video. Useful for community tips and common questions. |

## Prerequisites

- Python 3.13+
- Node.js 18+
- A [Google AI Studio](https://aistudio.google.com/) API key with access to Gemini

## Running locally

### API

```bash
cd api
pip install -r requirements.txt
```

Create a `.env` file in the `api/` directory:

```
GOOGLE_API_KEY=your_api_key_here
```

Start the server:

```bash
python main.py
```

The API runs at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

## Running with Docker

### API

```bash
docker build -t youtube-agent-api ./api
docker run -p 8000:8000 -e GOOGLE_API_KEY=your_api_key_here youtube-agent-api
```

### Frontend

```bash
docker build -t youtube-agent-frontend ./frontend
docker run -p 8080:8080 youtube-agent-frontend
```

The frontend will be available at `http://localhost:8080`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send a message. Returns a streaming plain-text response. |
| `POST` | `/clear` | Clear the current conversation history and start a new thread. |

### Example

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the best tips for learning React?"}'
```
