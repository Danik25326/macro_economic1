import aiohttp
import asyncio
import feedparser
from datetime import datetime, timedelta
import pytz
import re
from typing import List, Dict, Any
from config import Config

logger = logging.getLogger("news_analyzer")

class NewsAnalyzer:
    def __init__(self):
        self.kyiv_tz = pytz.timezone('Europe/Kiev')
        self.session = None
        
        # Словник для перекладу днів/місяців в RSS
        self.ukrainian_months = {
            'січня': '01', 'лютого': '02', 'березня': '03', 'квітня': '04',
            'травня': '05', 'червня': '06', 'липня': '07', 'серпня': '08',
            'вересня': '09', 'жовтня': '10', 'листопада': '11', 'грудня': '12'
        }
        
        # Детальніші ключові слова для кращого аналізу
        self.keyword_groups = {
            'positive_market': ['зростання', 'підвищення', 'прибуток', 'інвестиції', 'розвиток',
                               'покращення', 'стабільність', 'позитивний', 'сильний', 'рекорд'],
            
            'negative_market': ['спад', 'падіння', 'зниження', 'збитки', 'криза', 'нестабільність',
                               'негативний', 'слабкий', 'обмеження', 'дефіцит', 'імпічмент'],
            
            'inflation': ['інфляція', 'інфляційний', 'ціни', 'підвищення цін', 'зростання цін'],
            
            'interest_rates': ['відсоткова ставка', 'ключова ставка', 'ставка НБУ', 'ставка ФРС'],
            
            'geopolitical': ['війна', 'конфлікт', 'санкції', 'переговори', 'угода', 'мир'],
            
            'economic_data': ['ВВП', 'економічне зростання', 'безробіття', 'експорт', 'імпорт']
        }

    async def get_latest_news(self, hours_back: int = 24, min_news_count: int = 10) -> List[Dict[str, Any]]:
        """Отримати останні новини з різних джерел"""
        logger.info(f"📰 Отримання новин за останні {hours_back} годин...")
        
        all_news = []
        
        # Створюємо сесію aiohttp
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Асинхронно отримуємо новини з усіх джерел
            tasks = []
            for source in Config.NEWS_SOURCES:
                if source['type'] == 'rss':
                    tasks.append(self._fetch_rss_news(source, hours_back))
                elif source['type'] == 'api':
                    if source.get('requires_key', False) and not Config.NEWS_API_KEY:
                        continue
                    tasks.append(self._fetch_api_news(source, hours_back))
            
            # Виконуємо всі запити паралельно
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Об'єднуємо результати
            for result in results:
                if isinstance(result, list):
                    all_news.extend(result)
        
        # Фільтруємо дублікати
        unique_news = self._remove_duplicates(all_news)
        
        # Сортуємо за датою (новіші перші)
        unique_news.sort(key=lambda x: x.get('published_timestamp', ''), reverse=True)
        
        # Обмежуємо кількість
        news_to_return = unique_news[:50]  # Беремо максимум 50 новин
        
        logger.info(f"✅ Отримано {len(news_to_return)} унікальних новин")
        
        if len(news_to_return) < min_news_count:
            logger.warning(f"⚠️ Отримано замало новин ({len(news_to_return)}), додаємо кешовані")
            # Додаємо кешовані новини якщо потрібно
            cached = self._get_cached_news()
            if cached:
                news_to_return.extend(cached[:min_news_count - len(news_to_return)])
                news_to_return = news_to_return[:50]
        
        return news_to_return

    async def _fetch_rss_news(self, source: Dict, hours_back: int) -> List[Dict]:
        """Отримати новини з RSS джерела"""
        news_items = []
        
        try:
            # Отримуємо RSS
            async with self.session.get(source['url'], timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Парсимо RSS
                    feed = feedparser.parse(content)
                    
                    for entry in feed.entries[:20]:  # Беремо 20 останніх записів
                        try:
                            # Отримуємо та парсимо дату
                            published_time = self._parse_rss_date(entry.get('published', ''))
                            
                            if not published_time:
                                # Якщо дату не вдалося розпізнати, беремо поточний час
                                published_time = datetime.now(pytz.UTC)
                            
                            # Перевіряємо, чи новина не застаріла
                            time_diff = datetime.now(pytz.UTC) - published_time
                            if time_diff <= timedelta(hours=hours_back):
                                
                                # Аналізуємо заголовок та опис
                                title = entry.get('title', '')
                                summary = entry.get('summary', entry.get('description', ''))
                                
                                # Очищаємо HTML теги
                                summary = self._clean_html(summary)
                                
                                # Аналізуємо тональність
                                sentiment = self._analyze_sentiment(title + ' ' + summary)
                                
                                # Визначаємо релевантність для фінансів
                                relevance = self._calculate_relevance(title + ' ' + summary)
                                
                                news_item = {
                                    'title': title[:200],
                                    'summary': summary[:500],
                                    'link': entry.get('link', ''),
                                    'published': published_time.isoformat(),
                                    'published_timestamp': published_time.timestamp(),
                                    'source': source['name'],
                                    'source_url': source['url'],
                                    'category': source.get('category', 'general'),
                                    'sentiment': sentiment,
                                    'relevance': relevance,
                                    'has_financial_keywords': relevance > 0,
                                    'id': self._generate_news_id(entry)
                                }
                                
                                # Додаємо тільки якщо релевантність > 0 або тональність не нейтральна
                                if relevance > 0 or sentiment != 'neutral':
                                    news_items.append(news_item)
                                    
                        except Exception as e:
                            logger.debug(f"Помилка обробки RSS запису: {e}")
                            continue
                            
        except Exception as e:
            logger.warning(f"⚠️ Помилка отримання RSS з {source['name']}: {e}")
        
        logger.debug(f"📡 {source['name']}: {len(news_items)} новин")
        return news_items

    async def _fetch_api_news(self, source: Dict, hours_back: int) -> List[Dict]:
        """Отримати новини через API"""
        # Тут можна додати інтеграцію з NewsAPI, Alpha Vantage News тощо
        # Заглушка для майбутньої реалізації
        return []

    def _parse_rss_date(self, date_str: str):
        """Розпізнавання дати з різних форматів"""
        if not date_str:
            return None
        
        try:
            # Спробувати стандартні формати
            for fmt in [
                '%a, %d %b %Y %H:%M:%S %z',
                '%a, %d %b %Y %H:%M:%S %Z',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S',
                '%d %b %Y %H:%M:%S'
            ]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    if dt.tzinfo is None:
                        dt = pytz.UTC.localize(dt)
                    return dt
                except:
                    continue
            
            # Спробувати український формат "1 січня 2024"
            for uk_month, num_month in self.ukrainian_months.items():
                if uk_month in date_str.lower():
                    pattern = r'(\d{1,2})\s+' + uk_month + r'\s+(\d{4})'
                    match = re.search(pattern, date_str.lower())
                    if match:
                        day = match.group(1)
                        year = match.group(2)
                        date_str_iso = f"{year}-{num_month}-{day.zfill(2)}T12:00:00"
                        dt = datetime.strptime(date_str_iso, '%Y-%m-%dT%H:%M:%S')
                        return pytz.UTC.localize(dt)
                        
        except Exception as e:
            logger.debug(f"Помилка парсингу дати '{date_str}': {e}")
        
        return None

    def _analyze_sentiment(self, text: str) -> str:
        """Аналіз тональності тексту"""
        if not text:
            return 'neutral'
        
        text_lower = text.lower()
        
        # Рахуємо позитивні та негативні ключові слова
        positive_score = 0
        negative_score = 0
        
        for word in self.keyword_groups['positive_market']:
            if word in text_lower:
                positive_score += 1
        
        for word in self.keyword_groups['negative_market']:
            if word in text_lower:
                negative_score += 1
        
        # Додаткові бали за сильні слова
        strong_positive = ['рекорд', 'прорив', 'істотне зростання', 'значне покращення']
        strong_negative = ['криза', 'крах', 'колапс', 'катастрофа', 'руйнування']
        
        for word in strong_positive:
            if word in text_lower:
                positive_score += 2
        
        for word in strong_negative:
            if word in text_lower:
                negative_score += 2
        
        # Визначаємо тональність
        if positive_score == 0 and negative_score == 0:
            return 'neutral'
        elif positive_score > negative_score * 1.5:
            return 'positive'
        elif negative_score > positive_score * 1.5:
            return 'negative'
        else:
            return 'neutral'

    def _calculate_relevance(self, text: str) -> int:
        """Розрахунок релевантності для фінансового аналізу"""
        if not text:
            return 0
        
        text_lower = text.lower()
        relevance = 0
        
        # Перевіряємо всі групи ключових слів
        for group_name, keywords in self.keyword_groups.items():
            for keyword in keywords:
                if keyword in text_lower:
                    relevance += 1
        
        # Додаткові бали за валюти та крипту
        for currency in Config.CURRENCIES:
            if currency.lower() in text_lower:
                relevance += 2
        
        for crypto in Config.CRYPTO:
            if crypto.lower() in text_lower:
                relevance += 2
        
        return relevance

    def _clean_html(self, text: str) -> str:
        """Очищення HTML тегів з тексту"""
        if not text:
            return ''
        
        # Видаляємо HTML теги
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        
        # Видаляємо спеціальні символи
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&quot;', '"').replace('&#39;', "'")
        
        # Обрізаємо зайві пробіли
        text = ' '.join(text.split())
        
        return text[:500]  # Обмежуємо довжину

    def _remove_duplicates(self, news_list: List[Dict]) -> List[Dict]:
        """Видалення дублікатів новин"""
        seen_titles = set()
        unique_news = []
        
        for news in news_list:
            title_key = news.get('title', '').lower()[:100]
            
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)
        
        return unique_news

    def _generate_news_id(self, entry) -> str:
        """Генерація унікального ID для новини"""
        import hashlib
        
        title = entry.get('title', '')
        link = entry.get('link', '')
        source = entry.get('source', {}).get('title', '') if hasattr(entry, 'source') else ''
        
        id_string = f"{title}{link}{source}"
        return hashlib.md5(id_string.encode()).hexdigest()[:10]

    def _get_cached_news(self) -> List[Dict]:
        """Отримати кешовані новини"""
        try:
            cache_file = Config.DATA_DIR / 'news_cache.json'
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Перевіряємо, чи кеш не застарів
                    cache_time_str = data.get('last_update')
                    if cache_time_str:
                        cache_time = datetime.fromisoformat(cache_time_str)
                        if datetime.now(pytz.UTC) - cache_time <= timedelta(hours=Config.CACHE_HOURS):
                            return data.get('news', [])
        except Exception as e:
            logger.debug(f"Помилка читання кешу новин: {e}")
        
        return []
