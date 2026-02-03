import aiohttp
import feedparser
from datetime import datetime, timedelta
import pytz
from config import Config

class NewsAnalyzer:
    def __init__(self):
        self.kyiv_tz = pytz.timezone('Europe/Kiev')
        
        # Джерела новин (RSS, API)
        self.news_sources = [
            # Фінансові новини
            {'url': 'https://www.bloomberg.com/feeds/europe.xml', 'type': 'rss', 'category': 'finance'},
            {'url': 'https://www.reutersagency.com/feed/?best-topics=tech&post_type=best', 'type': 'rss', 'category': 'finance'},
            
            # Українські новини
            {'url': 'https://www.epravda.com.ua/rss/', 'type': 'rss', 'category': 'ukraine'},
            {'url': 'https://www.unian.ua/rss/news.rss', 'type': 'rss', 'category': 'ukraine'},
            
            # Світові новини
            {'url': 'https://www.bbc.com/news/world/rss.xml', 'type': 'rss', 'category': 'world'},
        ]
        
        # Ключові слова для аналізу
        self.keywords = {
            'positive': ['зростання', 'підвищення', 'покращення', 'рік', 'сильний', 'стабільність'],
            'negative': ['спад', 'падіння', 'криза', 'інфляція', 'війна', 'конфлікт', 'обмеження'],
            'currency': ['долар', 'євро', 'гривня', 'фунт', 'єна', 'юань', 'франк'],
            'economic': ['ФРС', 'ЄЦБ', 'НБУ', 'інфляція', 'ВВП', 'ринок', 'економіка']
        }

    async def get_latest_news(self, hours_back=24):
        """Отримати останні новини"""
        news_items = []
        
        for source in self.news_sources:
            if source['type'] == 'rss':
                try:
                    feed = feedparser.parse(source['url'])
                    
                    for entry in feed.entries[:10]:  # Беремо 10 останніх
                        published_time = self._parse_date(entry.get('published', ''))
                        
                        # Фільтруємо за часом
                        if published_time:
                            time_diff = datetime.now(pytz.utc) - published_time
                            if time_diff <= timedelta(hours=hours_back):
                                
                                # Аналізуємо тональність
                                sentiment = self._analyze_sentiment(
                                    entry.get('title', '') + ' ' + entry.get('summary', '')
                                )
                                
                                news_items.append({
                                    'title': entry.get('title', ''),
                                    'summary': entry.get('summary', ''),
                                    'link': entry.get('link', ''),
                                    'published': published_time.isoformat(),
                                    'source': source['url'],
                                    'category': source['category'],
                                    'sentiment': sentiment,
                                    'relevance': self._calculate_relevance(entry)
                                })
                except Exception as e:
                    print(f"⚠️ Помилка отримання RSS {source['url']}: {e}")
        
        # Сортуємо за релевантністю та часом
        news_items.sort(key=lambda x: (x['relevance'], x['published']), reverse=True)
        
        return news_items[:20]  # Повертаємо 20 найважливіших новин

    def _analyze_sentiment(self, text: str) -> str:
        """Простий аналіз тональності тексту"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.keywords['positive'] if word in text_lower)
        negative_count = sum(1 for word in self.keywords['negative'] if word in text_lower)
        
        if positive_count > negative_count * 1.5:
            return 'positive'
        elif negative_count > positive_count * 1.5:
            return 'negative'
        else:
            return 'neutral'

    def _calculate_relevance(self, entry) -> float:
        """Розрахунок релевантності новини"""
        relevance = 0
        text = (entry.get('title', '') + ' ' + entry.get('summary', '')).lower()
        
        # Перевіряємо наявність ключових слів
        for category in ['currency', 'economic']:
            for keyword in self.keywords[category]:
                if keyword in text:
                    relevance += 1
        
        # Більше релевантності для фінансових новин
        if 'finance' in text or 'економік' in text or 'ринок' in text:
            relevance += 2
        
        return relevance

    def _parse_date(self, date_str):
        """Парсинг дати з різних форматів"""
        try:
            # Спробувати різні формати
            for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z', '%a, %d %b %Y %H:%M:%S %Z']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    if dt.tzinfo is None:
                        dt = pytz.utc.localize(dt)
                    return dt
                except:
                    continue
        except:
            pass
        return None
