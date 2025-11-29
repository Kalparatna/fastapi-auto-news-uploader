import requests
import feedparser
from bs4 import BeautifulSoup
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class NewsFetcher:
    def __init__(self):
        self.espn_rss_url = settings.ESPN_RSS_URL

    def is_valid_image_url(self, url):
        """Check if URL is a valid image"""
        if not url:
            return False
        return url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))

    def is_generic_image(self, url):
        """Check if image is a generic placeholder"""
        if not url:
            return True
        generic_keywords = ['logo', 'icon', 'placeholder', 'spacer', 'default']
        return any(keyword in url.lower() for keyword in generic_keywords)

    def extract_article_content(self, url):
        """Extract image and description from article page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }

            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch article page: {response.status_code}")
                return None, None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract image
            image_url = None
            image_selectors = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
                '.story-image img',
                '.article-image img',
                'article img',
                'img[src*="cricket"]',
            ]

            for selector in image_selectors:
                element = soup.select_one(selector)
                if element:
                    found_image_url = element.get('content') or element.get('src')
                    if found_image_url:
                        if found_image_url.startswith('//'):
                            found_image_url = 'https:' + found_image_url
                        elif found_image_url.startswith('/'):
                            found_image_url = 'https://www.espncricinfo.com' + found_image_url

                        if self.is_valid_image_url(found_image_url) and not self.is_generic_image(found_image_url):
                            image_url = found_image_url
                            break

            # Extract description
            description = None
            description_selectors = [
                'meta[property="og:description"]',
                'meta[name="description"]',
                '.story-intro',
                'article p:first-of-type',
            ]

            for selector in description_selectors:
                element = soup.select_one(selector)
                if element:
                    desc_text = element.get('content') or element.get_text(strip=True)
                    if desc_text and len(desc_text) > 50:
                        description = desc_text
                        break

            return image_url, description

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None, None

    def fetch_cricket_news(self):
        """Fetch cricket news from ESPN RSS feed"""
        try:
            logger.info("🏏 Fetching cricket news from ESPN RSS...")
            feed = feedparser.parse(self.espn_rss_url)
            
            if not feed.entries:
                logger.error("No entries found in ESPN RSS feed")
                return []
            
            logger.info(f"📰 Found {len(feed.entries)} articles in ESPN RSS")
            
            articles = []
            max_articles = min(10, len(feed.entries))
            
            for i, item in enumerate(feed.entries[:max_articles]):
                try:
                    # Extract image and description from article page
                    image_url, description = self.extract_article_content(item.link)
                    
                    # Use RSS summary if no description extracted
                    if not description and hasattr(item, 'summary'):
                        description = item.summary
                    
                    articles.append({
                        'title': item.title,
                        'link': item.link,
                        'image_url': image_url,
                        'description': description,
                        'source': 'ESPN'
                    })
                    
                    # Stop after getting 5 articles
                    if len(articles) >= 5:
                        break
                    
                except Exception as e:
                    logger.error(f"❌ Error processing article {i+1}: {e}")
                    continue
            
            logger.info(f"✅ Successfully fetched {len(articles)} articles from ESPN")
            return articles
            
        except Exception as e:
            logger.error(f"❌ ESPN RSS fetch failed: {e}")
            return []
