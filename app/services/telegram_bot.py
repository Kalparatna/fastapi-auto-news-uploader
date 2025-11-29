import requests
import time
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class TelegramBot:
    def __init__(self):
        self.bot_token = settings.BOT_TOKEN
        self.chat_id = settings.CHAT_ID
        self.api_base = f'https://api.telegram.org/bot{self.bot_token}'
    
    def send_message(self, article):
        """Send article as text message (when no image available)"""
        try:
            message = f"<b>{article['title']}</b>"
            
            if article.get('description'):
                description = article['description'][:300] + "..." if len(article['description']) > 300 else article['description']
                message += f"\n\n{description}"
            
            message += f"\n\n<a href=\"{article['link']}\">Read full article</a>"
            
            if len(message) > 4096:
                message = message[:4090] + "..."
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': False
            }
            
            logger.info(f"📤 Sending text message: {article['title'][:30]}...")
            
            response = requests.post(f'{self.api_base}/sendMessage', data=payload, timeout=30)
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            
            if response.status_code == 200 and result.get('ok'):
                logger.info(f"✅ Successfully sent text message")
                return result
            else:
                error_description = result.get('description', 'Unknown error')
                raise Exception(f"Telegram API error: {error_description}")
                
        except Exception as e:
            logger.error(f"❌ Error sending text message: {e}")
            raise e

    def send_photo(self, article):
        """Send a single article as photo with caption"""
        try:
            caption = f"<b>{article['title']}</b>"
            
            if article.get('description'):
                description = article['description'][:200] + "..." if len(article['description']) > 200 else article['description']
                caption += f"\n\n{description}"
            
            caption += f"\n\n<a href=\"{article['link']}\">Read full article</a>"
            
            if len(caption) > 1024:
                caption = caption[:1020] + "..."
            
            payload = {
                'chat_id': self.chat_id,
                'photo': article['image_url'],
                'caption': caption,
                'parse_mode': 'HTML'
            }
            
            logger.info(f"📤 Sending photo: {article['title'][:30]}...")
            
            response = requests.post(f'{self.api_base}/sendPhoto', data=payload, timeout=30)
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            
            if response.status_code == 200 and result.get('ok'):
                logger.info(f"✅ Successfully sent photo")
                return result
            else:
                error_description = result.get('description', 'Unknown error')
                raise Exception(f"Telegram API error: {error_description}")
                
        except Exception as e:
            logger.error(f"❌ Error sending photo: {e}")
            raise e

    def post_articles(self, articles):
        """Post multiple articles with delay"""
        posted_count = 0
        
        logger.info(f"📤 Starting to post {len(articles)} articles to Telegram...")
        
        for i, article in enumerate(articles):
            try:
                logger.info(f"📸 Posting article {i+1}/{len(articles)}")
                
                if article.get('image_url'):
                    self.send_photo(article)
                else:
                    self.send_message(article)
                
                posted_count += 1
                
                if i < len(articles) - 1:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ Failed to send article: {e}")
                continue
        
        logger.info(f"🎉 Completed posting {posted_count}/{len(articles)} articles")
        return posted_count
    
    def get_bot_info(self):
        """Get bot information for testing"""
        try:
            response = requests.get(f'{self.api_base}/getMe', timeout=10)
            result = response.json()
            
            if response.status_code == 200 and result.get('ok'):
                return result.get('result', {})
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting bot info: {e}")
            return None
