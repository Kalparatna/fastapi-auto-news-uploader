from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from app.mongodb_service import MongoDBService
from app.tasks import fetch_and_post_cricket_news
from app.scheduler import scheduler
from app.config import get_settings
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting FastAPI Cricket News Bot...")
    
    if settings.ENABLE_SCHEDULER:
        try:
            scheduler.start()
            logger.info("✅ Scheduler started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    if scheduler.running:
        scheduler.stop()

app = FastAPI(
    title="Cricket News Bot API",
    description="Automated cricket news fetching and posting to Telegram",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Cricket News Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Cricket News Bot API is running",
        "database": "MongoDB Only",
        "scheduler": {
            "running": scheduler.running,
            "status": "active" if scheduler.running else "inactive"
        }
    }

@app.get("/api/articles")
async def get_articles():
    """Get all posted articles"""
    mongodb_service = MongoDBService()
    try:
        articles = mongodb_service.get_articles()
        return articles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        mongodb_service.close_connection()

@app.get("/api/headlines")
async def get_headlines():
    """Get today's headlines only"""
    mongodb_service = MongoDBService()
    try:
        todays_articles = mongodb_service.get_todays_articles()
        return {
            'date': datetime.utcnow().date().isoformat(),
            'count': len(todays_articles),
            'headlines': todays_articles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        mongodb_service.close_connection()

@app.get("/api/status")
async def get_bot_status():
    """Get bot status and statistics"""
    mongodb_service = MongoDBService()
    try:
        latest_status = mongodb_service.get_latest_bot_status()
        stats = mongodb_service.get_statistics()
        
        if latest_status:
            latest_status.update(stats)
            return latest_status
        else:
            return {
                'status': 'inactive',
                'message': 'Bot has not run yet',
                'total_articles_posted': 0,
                'today_articles_posted': 0
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        mongodb_service.close_connection()

@app.post("/api/trigger")
async def trigger_news_fetch(request: Request):
    """Manually trigger news fetch and post"""
    start_time = datetime.utcnow()
    
    # Log trigger source
    user_agent = request.headers.get('user-agent', 'Unknown')
    client_host = request.client.host if request.client else 'Unknown'
    
    logger.info(f"🚀 News fetch triggered by {user_agent} from {client_host}")
    
    try:
        result = fetch_and_post_cricket_news()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Manual trigger completed in {duration:.1f}s")
        
        return {
            'success': True,
            'message': 'News fetch task completed successfully',
            'result': result,
            'execution_time': f"{duration:.1f}s",
            'triggered_at': start_time.isoformat(),
            'completed_at': end_time.isoformat(),
            'triggered_by': user_agent
        }
    except Exception as e:
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.error(f"❌ Manual trigger failed after {duration:.1f}s: {e}")
        
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e),
                'execution_time': f"{duration:.1f}s",
                'triggered_at': start_time.isoformat(),
                'failed_at': end_time.isoformat(),
                'triggered_by': user_agent
            }
        )

@app.post("/api/cleanup")
async def cleanup_old_data():
    """Manually trigger cleanup of old articles"""
    mongodb_service = MongoDBService()
    try:
        cleaned_count = mongodb_service.cleanup_old_articles()
        return {
            'message': f'Successfully cleaned up {cleaned_count} old articles',
            'cleaned_count': cleaned_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        mongodb_service.close_connection()

@app.get("/api/scheduler/status")
async def scheduler_status():
    """Get scheduler status"""
    # Calculate next hourly run
    now = datetime.utcnow()
    next_hour = now.replace(minute=0, second=0, microsecond=0)
    if now.minute > 0:
        next_hour = next_hour.replace(hour=(next_hour.hour + 1) % 24)
    
    return {
        'scheduler_running': scheduler.running,
        'scheduler_status': 'active' if scheduler.running else 'inactive',
        'schedule_type': 'hourly',
        'next_runs': {
            'news_fetch': f'Every hour at :00 (next: {next_hour.strftime("%H:00 UTC")})',
            'cleanup': '3:00 AM UTC daily (8:30 AM IST)'
        },
        'articles_per_run': '5 articles (ESPN priority, NewsAPI fallback)',
        'frequency': 'Every hour (24 times daily)',
        'message': 'Scheduler is running automatically' if scheduler.running else 'Scheduler is not running'
    }

@app.post("/api/scheduler/start")
async def start_scheduler():
    """Manually start the scheduler"""
    try:
        if not scheduler.running:
            scheduler.start()
            return {
                'message': 'Scheduler started successfully',
                'status': 'started'
            }
        else:
            return {
                'message': 'Scheduler is already running',
                'status': 'already_running'
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'error': str(e),
                'status': 'failed'
            }
        )

@app.get("/api/scheduler/health")
async def scheduler_health():
    """Detailed scheduler health check"""
    try:
        mongodb_service = MongoDBService()
        
        scheduler_running = scheduler.running
        tasks = mongodb_service.get_scheduled_tasks()
        
        # Calculate next run times
        now = datetime.utcnow()
        next_runs = []
        
        for task in tasks:
            schedule = task['schedule']
            next_run = now.replace(
                hour=schedule['hour'],
                minute=schedule['minute'],
                second=0,
                microsecond=0
            )
            
            if next_run <= now:
                next_run = next_run + timedelta(days=1)
            
            next_runs.append({
                'task': task['name'],
                'next_run': next_run.isoformat(),
                'schedule': f"{schedule['hour']:02d}:{schedule['minute']:02d} UTC",
                'last_run': task.get('last_run').isoformat() if task.get('last_run') else None
            })
        
        mongodb_service.close_connection()
        
        return {
            'scheduler_running': scheduler_running,
            'scheduler_thread_alive': scheduler.thread.is_alive() if scheduler.thread else False,
            'total_tasks': len(tasks),
            'enabled_tasks': len([t for t in tasks if t.get('enabled', True)]),
            'next_runs': next_runs,
            'current_time_utc': now.isoformat(),
            'health_status': 'healthy' if scheduler_running else 'unhealthy'
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'error': str(e),
                'health_status': 'error'
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
