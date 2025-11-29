from datetime import datetime
from app.mongodb_service import MongoDBService
from app.services.news_fetcher import NewsFetcher
from app.services.telegram_bot import TelegramBot
import logging

logger = logging.getLogger(__name__)

def fetch_and_post_cricket_news():
    """Task to fetch and post cricket news (Hourly execution)"""
    mongodb_service = MongoDBService()
    
    try:
        logger.info("🏏 Starting hourly cricket news fetch and post task...")
        
        news_fetcher = NewsFetcher()
        telegram_bot = TelegramBot()
        
        # Test Telegram bot
        logger.info("🤖 Testing Telegram bot connection...")
        bot_info = telegram_bot.get_bot_info()
        if not bot_info:
            raise Exception("Failed to connect to Telegram bot")
        logger.info(f"✅ Telegram bot connected: @{bot_info.get('username', 'unknown')}")
        
        # Fetch news
        logger.info("📰 Fetching latest cricket news...")
        articles = news_fetcher.fetch_cricket_news()
        
        if not articles:
            logger.warning("❌ No articles found")
            mongodb_service.save_bot_status({
                'articles_posted': 0,
                'status': 'success',
                'error_message': 'No articles found'
            })
            return {"status": "success", "message": "No articles found"}
        
        logger.info(f"📄 Found {len(articles)} articles")
        
        # Filter new articles
        new_articles = []
        for article_data in articles:
            if not mongodb_service.article_exists(article_data['title'], article_data['source']):
                article_data['is_posted'] = False
                mongodb_service.save_article(article_data)
                new_articles.append(article_data)
            else:
                logger.info(f"⏭️ Skipping duplicate: {article_data['title'][:50]}...")
        
        if not new_articles:
            logger.info("ℹ️ No new articles to post")
            mongodb_service.save_bot_status({
                'articles_posted': 0,
                'status': 'success',
                'error_message': 'No new articles'
            })
            return {"status": "success", "message": "No new articles"}
        
        logger.info(f"📤 Posting {len(new_articles)} new articles")
        
        # Post to Telegram
        posted_count = telegram_bot.post_articles(new_articles)
        
        if posted_count == 0:
            raise Exception("Failed to post any articles")
        
        # Mark as posted
        for article_data in new_articles:
            mongodb_service.mark_article_posted(article_data['title'], article_data['source'])
        
        # Update status
        mongodb_service.save_bot_status({
            'articles_posted': posted_count,
            'status': 'success'
        })
        
        logger.info(f"✅ Successfully posted {posted_count}/{len(new_articles)} articles")
        
        return {
            "status": "success",
            "articles_found": len(articles),
            "new_articles": len(new_articles),
            "articles_posted": posted_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error in cricket news task: {e}")
        
        try:
            mongodb_service.save_bot_status({
                'status': 'error',
                'error_message': str(e),
                'articles_posted': 0
            })
        except:
            pass
        
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    finally:
        try:
            mongodb_service.close_connection()
        except:
            pass

def cleanup_old_articles():
    """Task to clean up old articles (runs daily)"""
    mongodb_service = MongoDBService()
    
    try:
        cleaned_count = mongodb_service.cleanup_old_articles()
        logger.info(f"🧹 Daily cleanup: removed {cleaned_count} old articles")
        return {"status": "success", "cleaned_articles": cleaned_count}
    except Exception as e:
        logger.error(f"❌ Error in cleanup task: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        mongodb_service.close_connection()
