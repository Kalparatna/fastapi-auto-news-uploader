from pymongo import MongoClient, ASCENDING
from datetime import datetime, timedelta
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class MongoDBService:
    """Pure MongoDB service for all data operations"""
    
    def __init__(self):
        try:
            self.client = MongoClient(settings.MONGO_STRING)
            self.db = self.client[settings.MONGODB_DATABASE]
            logger.info("✅ Connected to MongoDB")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
        
        # Collections
        self.articles_collection = self.db['news_articles']
        self.bot_status_collection = self.db['bot_status']
        self.scheduler_collection = self.db['scheduler_tasks']
        
        # Setup indexes
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup MongoDB indexes for better performance"""
        try:
            self.articles_collection.create_index([('title', ASCENDING), ('source', ASCENDING)], unique=True)
            self.articles_collection.create_index([('posted_at', ASCENDING)])
            self.articles_collection.create_index([('is_posted', ASCENDING)])
            self.bot_status_collection.create_index([('last_run', ASCENDING)])
            self.scheduler_collection.create_index([('name', ASCENDING)], unique=True)
            self.scheduler_collection.create_index([('enabled', ASCENDING)])
            logger.info("✅ MongoDB indexes setup completed")
        except Exception as e:
            logger.error(f"Error setting up indexes: {e}")
    
    def save_article(self, article_data):
        """Save article to MongoDB"""
        try:
            article_doc = {
                'title': article_data['title'],
                'link': article_data['link'],
                'image_url': article_data.get('image_url'),
                'description': article_data.get('description'),
                'source': article_data['source'],
                'posted_at': datetime.utcnow(),
                'is_posted': article_data.get('is_posted', False)
            }
            
            result = self.articles_collection.update_one(
                {'title': article_data['title'], 'source': article_data['source']},
                {'$setOnInsert': article_doc},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Saved new article: {article_data['title'][:50]}...")
                return str(result.upserted_id)
            else:
                logger.info(f"Article already exists: {article_data['title'][:50]}...")
                existing = self.articles_collection.find_one(
                    {'title': article_data['title'], 'source': article_data['source']}
                )
                return str(existing['_id']) if existing else None
        except Exception as e:
            logger.error(f"Error saving article: {e}")
            return None
    
    def get_articles(self, limit=50):
        """Get all articles from MongoDB"""
        try:
            articles = list(self.articles_collection.find().sort('posted_at', -1).limit(limit))
            return [
                {
                    'id': str(article['_id']),
                    'title': article['title'],
                    'link': article['link'],
                    'image_url': article.get('image_url'),
                    'description': article.get('description'),
                    'source': article['source'],
                    'posted_at': article['posted_at'].isoformat(),
                    'is_posted': article['is_posted']
                }
                for article in articles
            ]
        except Exception as e:
            logger.error(f"Error fetching articles: {e}")
            return []
    
    def get_todays_articles(self):
        """Get today's articles from MongoDB"""
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            articles = list(self.articles_collection.find({
                'posted_at': {'$gte': today_start, '$lt': today_end}
            }).sort('posted_at', -1))
            
            return [
                {
                    'id': str(article['_id']),
                    'title': article['title'],
                    'link': article['link'],
                    'image_url': article.get('image_url'),
                    'description': article.get('description'),
                    'source': article['source'],
                    'posted_at': article['posted_at'].isoformat(),
                    'is_posted': article['is_posted']
                }
                for article in articles
            ]
        except Exception as e:
            logger.error(f"Error fetching today's articles: {e}")
            return []
    
    def article_exists(self, title, source):
        """Check if article exists in MongoDB"""
        try:
            return self.articles_collection.find_one({'title': title, 'source': source}) is not None
        except Exception as e:
            logger.error(f"Error checking article existence: {e}")
            return False
    
    def mark_article_posted(self, title, source):
        """Mark article as posted in MongoDB"""
        try:
            self.articles_collection.update_one(
                {'title': title, 'source': source},
                {'$set': {'is_posted': True}}
            )
        except Exception as e:
            logger.error(f"Error marking article as posted: {e}")
    
    def cleanup_old_articles(self):
        """Delete articles older than 7 days from MongoDB"""
        try:
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            result = self.articles_collection.delete_many({'posted_at': {'$lt': seven_days_ago}})
            deleted_count = result.deleted_count
            logger.info(f"Cleaned up {deleted_count} old articles (older than 7 days)")
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old articles: {e}")
            return 0
    
    def save_bot_status(self, status_data):
        """Save bot status to MongoDB"""
        try:
            status_doc = {
                'last_run': datetime.utcnow(),
                'articles_posted': status_data.get('articles_posted', 0),
                'status': status_data.get('status', 'active'),
                'error_message': status_data.get('error_message')
            }
            result = self.bot_status_collection.insert_one(status_doc)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving bot status: {e}")
            return None
    
    def get_latest_bot_status(self):
        """Get latest bot status from MongoDB"""
        try:
            status = self.bot_status_collection.find_one(sort=[('last_run', -1)])
            if status:
                return {
                    'id': str(status['_id']),
                    'last_run': status['last_run'].isoformat(),
                    'articles_posted': status['articles_posted'],
                    'status': status['status'],
                    'error_message': status.get('error_message')
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching bot status: {e}")
            return None
    
    def get_statistics(self):
        """Get bot statistics from MongoDB"""
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            total_articles = self.articles_collection.count_documents({'is_posted': True})
            today_articles = self.articles_collection.count_documents({
                'is_posted': True,
                'posted_at': {'$gte': today_start, '$lt': today_end}
            })
            
            return {
                'total_articles_posted': total_articles,
                'today_articles_posted': today_articles
            }
        except Exception as e:
            logger.error(f"Error fetching statistics: {e}")
            return {'total_articles_posted': 0, 'today_articles_posted': 0}
    
    def setup_scheduled_tasks(self):
        """Setup scheduled tasks in MongoDB - Hourly news fetching"""
        tasks = []
        
        # Create hourly news fetching tasks (24 hours)
        for hour in range(24):
            tasks.append({
                'name': f'cricket_news_hour_{hour:02d}',
                'task': 'fetch_and_post_cricket_news',
                'schedule': {'hour': hour, 'minute': 0},
                'enabled': True,
                'last_run': None
            })
        
        # Daily cleanup task at 3:00 AM UTC
        tasks.append({
            'name': 'cleanup_old_articles_daily',
            'task': 'cleanup_old_articles',
            'schedule': {'hour': 3, 'minute': 0},
            'enabled': True,
            'last_run': None
        })
        
        for task in tasks:
            self.scheduler_collection.update_one(
                {'name': task['name']},
                {'$setOnInsert': task},
                upsert=True
            )
        
        logger.info("✅ Scheduled tasks setup completed")
    
    def get_scheduled_tasks(self):
        """Get all scheduled tasks from MongoDB"""
        try:
            return list(self.scheduler_collection.find({'enabled': True}))
        except Exception as e:
            logger.error(f"Error fetching scheduled tasks: {e}")
            return []
    
    def update_task_last_run(self, task_name):
        """Update task last run time in MongoDB"""
        try:
            self.scheduler_collection.update_one(
                {'name': task_name},
                {'$set': {'last_run': datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"Error updating task last run: {e}")
    
    def close_connection(self):
        """Close MongoDB connection"""
        if hasattr(self, 'client'):
            self.client.close()
