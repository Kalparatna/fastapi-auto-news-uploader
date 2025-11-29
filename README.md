# 🏏 Cricket News Bot - FastAPI Backend

FastAPI backend for automated cricket news fetching and posting to Telegram with hourly scheduling.

## 🚀 Features

- **Hourly Automation**: Posts cricket news every hour (24 times daily)
- **Dual News Sources**: ESPN RSS (primary) + NewsAPI (fallback)
- **Smart Image Extraction**: Scrapes article images with fallback handling
- **MongoDB Storage**: Pure MongoDB architecture
- **Real-time API**: FastAPI with automatic OpenAPI documentation
- **Duplicate Prevention**: Intelligent article filtering
- **Auto Cleanup**: Daily cleanup of articles older than 7 days
- **25 Scheduled Tasks**: 24 hourly + 1 daily cleanup

## 📁 Project Structure

```
News bot with Fastapi/
├── app/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── news_fetcher.py      # News fetching logic
│   │   └── telegram_bot.py      # Telegram posting
│   ├── __init__.py
│   ├── config.py                # Configuration settings
│   ├── main.py                  # FastAPI application
│   ├── mongodb_service.py       # MongoDB operations
│   ├── scheduler.py             # Task scheduler
│   └── tasks.py                 # Background tasks
├── venv/                        # Virtual environment
├── .env                         # Environment variables
├── .env.example                 # Environment template
├── .gitignore
├── requirements.txt
└── README.md
```

## 🔧 Setup Instructions

### 1. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# MongoDB Configuration
MONGO_STRING=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=cricket_news_bot

# Telegram Bot Configuration
BOT_TOKEN=your-telegram-bot-token
CHAT_ID=@your-telegram-channel

# News API Configuration
NEWSAPI_KEY=your-newsapi-key

# News Sources (Optional - defaults provided)
ESPN_RSS_URL=https://www.espncricinfo.com/rss/content/story/feeds/0.xml
NEWSAPI_EVERYTHING_URL=https://newsapi.org/v2/everything
NEWSAPI_HEADLINES_URL=https://newsapi.org/v2/top-headlines

# Scheduler Configuration
ENABLE_SCHEDULER=true
```

### 4. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📡 API Endpoints

### Base URL
- **Local**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

### Core Endpoints

#### 1. Health Check
```http
GET /api/health
```
Check if API and scheduler are running.

#### 2. Get All Articles
```http
GET /api/articles
```
Retrieve all posted articles.

#### 3. Get Today's Headlines
```http
GET /api/headlines
```
Retrieve only today's cricket headlines.

#### 4. Get Bot Status
```http
GET /api/status
```
Get current bot status and statistics.

#### 5. Manual News Fetch
```http
POST /api/trigger
```
Manually trigger news fetching and posting.

#### 6. Cleanup Old Data
```http
POST /api/cleanup
```
Remove articles older than 7 days.

### Scheduler Endpoints

#### 7. Scheduler Status
```http
GET /api/scheduler/status
```
Get basic scheduler information.

#### 8. Scheduler Health
```http
GET /api/scheduler/health
```
Get detailed scheduler health with all 25 tasks.

#### 9. Start Scheduler
```http
POST /api/scheduler/start
```
Manually start the scheduler.

## 📚 API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 🧪 Testing the API

### Using cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Get articles
curl http://localhost:8000/api/articles

# Manual trigger
curl -X POST http://localhost:8000/api/trigger

# Scheduler status
curl http://localhost:8000/api/scheduler/status
```

### Using Python

```python
import requests

# Health check
response = requests.get('http://localhost:8000/api/health')
print(response.json())

# Manual trigger
response = requests.post('http://localhost:8000/api/trigger')
print(response.json())
```

### Using JavaScript/Fetch

```javascript
// Health check
fetch('http://localhost:8000/api/health')
  .then(res => res.json())
  .then(data => console.log(data));

// Manual trigger
fetch('http://localhost:8000/api/trigger', { method: 'POST' })
  .then(res => res.json())
  .then(data => console.log(data));
```

## 🔄 How It Works

### Scheduler System (25 Tasks)
1. **24 Hourly Tasks**: Run at :00 minutes every hour (00:00, 01:00, ..., 23:00 UTC)
2. **1 Daily Cleanup**: Runs at 03:00 UTC (removes articles older than 7 days)

### News Fetching Process
1. **ESPN Priority**: Tries ESPN Cricket RSS first
2. **NewsAPI Fallback**: Supplements with NewsAPI if needed
3. **Target**: 5 articles per hour (3 Indian + 2 World cricket)

### Telegram Posting
1. Posts each article individually with image
2. Includes title, description, and link
3. 1-second delay between posts

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn with ASGI
- **Database**: MongoDB (PyMongo 4.6.0)
- **News Sources**: ESPN RSS, NewsAPI
- **Telegram**: Telegram Bot API
- **Scraping**: BeautifulSoup4, Feedparser
- **Configuration**: Pydantic Settings

## 📊 Monitoring

### Check Scheduler Status
```bash
curl http://localhost:8000/api/scheduler/health
```

Expected response:
```json
{
  "scheduler_running": true,
  "total_tasks": 25,
  "enabled_tasks": 25,
  "health_status": "healthy"
}
```

### View Logs
The application logs all operations:
- ✅ Successful operations
- ❌ Errors and failures
- 💓 Scheduler heartbeat (every 10 minutes)
- 🎯 Task executions

## 🚀 Deployment

### Using Uvicorn (Production)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn + Uvicorn Workers

```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t cricket-news-bot .
docker run -p 8000:8000 --env-file .env cricket-news-bot
```

### Environment Variables for Production

```env
ENABLE_SCHEDULER=true
MONGO_STRING=mongodb+srv://...
BOT_TOKEN=your-bot-token
CHAT_ID=@your-channel
NEWSAPI_KEY=your-api-key
```

## 🐛 Troubleshooting

### Scheduler Not Running
```bash
# Check status
curl http://localhost:8000/api/scheduler/health

# Start manually
curl -X POST http://localhost:8000/api/scheduler/start
```

### MongoDB Connection Issues
- Verify `MONGO_STRING` in `.env`
- Check MongoDB Atlas IP whitelist
- Ensure database user has proper permissions

### Telegram Bot Issues
- Verify `BOT_TOKEN` is correct
- Check `CHAT_ID` format (should start with @)
- Ensure bot is admin in the channel

### No Articles Found
- Check NewsAPI key validity
- Verify ESPN RSS URL is accessible
- Check internet connectivity

## 📝 Development

### Running in Development Mode
```bash
uvicorn app.main:app --reload
```

### Code Structure
- `app/main.py`: FastAPI routes and application setup
- `app/config.py`: Configuration management
- `app/mongodb_service.py`: Database operations
- `app/scheduler.py`: Task scheduling logic
- `app/tasks.py`: Background task implementations
- `app/services/`: External service integrations

## 🔐 Security

- Environment variables for sensitive data
- CORS configured for frontend access
- MongoDB connection string encryption
- Rate limiting recommended for production

## 📈 Performance

- **Response Times**: 100-500ms for data retrieval
- **Manual Trigger**: 5-15 seconds
- **Hourly Articles**: Up to 5 per hour (120+ daily)
- **Database**: Automatic cleanup keeps it optimized

## 🎯 API Response Examples

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2025-11-15T10:30:00.000000",
  "message": "Cricket News Bot API is running",
  "database": "MongoDB Only",
  "scheduler": {
    "running": true,
    "status": "active"
  }
}
```

### Articles Response
```json
[
  {
    "id": "article_id",
    "title": "India wins the match",
    "link": "https://espncricinfo.com/...",
    "image_url": "https://img.espncricinfo.com/...",
    "description": "India secured victory...",
    "source": "ESPN",
    "posted_at": "2025-11-15T10:00:00.000000",
    "is_posted": true
  }
]
```

## 📞 Support

For issues or questions:
1. Check the logs for error messages
2. Verify environment variables
3. Test individual endpoints
4. Check MongoDB connection
5. Verify Telegram bot configuration

---

**🏏 Your FastAPI Cricket News Bot is ready! Visit `/docs` for interactive API documentation! ⚡**
