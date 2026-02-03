import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import pytz

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

logger = logging.getLogger("currency_advisor")

BASE_DIR = Path(__file__).parent.parent

class Config:
    # Groq AI
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b')
    
    # API ключі для новин та економічних даних
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
    FRED_API_KEY = os.getenv('FRED_API_KEY', '')
    
    # Налаштування аналізу
    LANGUAGE = os.getenv('LANGUAGE', 'uk')
    CACHE_HOURS = int(os.getenv('CACHE_HOURS', 6))  # Кількість годин кешування
    MAX_RECOMMENDATIONS = int(os.getenv('MAX_RECOMMENDATIONS', 8))
    
    # Мінімальна впевненість для рекомендацій
    MIN_CONFIDENCE = float(os.getenv('MIN_CONFIDENCE', 0.65))
    
    # Часовий пояс
    KYIV_TZ = pytz.timezone('Europe/Kiev')
    
    # Логування
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / 'logs' / 'recommendations.log'
    
    # Шляхи до файлів
    DATA_DIR = BASE_DIR / 'data'
    RECOMMENDATIONS_FILE = DATA_DIR / 'recommendations.json'
    HISTORY_FILE = DATA_DIR / 'history_recommendations.json'
    NEWS_CACHE_FILE = DATA_DIR / 'news_cache.json'
    ECONOMIC_INDICATORS_FILE = DATA_DIR / 'economic_indicators.json'
    
    # Налаштування новинних джерел
    NEWS_SOURCES = [
        {
            'name': 'Reuters',
            'url': 'https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best',
            'type': 'rss',
            'category': 'finance'
        },
        {
            'name': 'Bloomberg',
            'url': 'https://www.bloomberg.com/europe',
            'type': 'scrape',
            'category': 'finance'
        },
        {
            'name': 'Українська правда',
            'url': 'https://www.epravda.com.ua/rss/',
            'type': 'rss',
            'category': 'ukraine'
        },
        {
            'name': 'BBC Україна',
            'url': 'https://www.bbc.com/ukrainian/index.xml',
            'type': 'rss',
            'category': 'ukraine'
        },
        {
            'name': 'Investing.com RSS',
            'url': 'https://www.investing.com/rss/news.rss',
            'type': 'rss',
            'category': 'markets'
        }
    ]
    
    # Основні валюти для аналізу
    CURRENCIES = [
        'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD',
        'CNY', 'RUB', 'UAH', 'PLN', 'TRY', 'INR', 'BRL', 'MXN'
    ]
    
    # Криптовалюти
    CRYPTO = [
        'BTC', 'ETH', 'BNB', 'XRP', 'SOL', 'ADA', 'DOT', 'DOGE'
    ]
    
    # Ключові слова для аналізу новин
    KEYWORDS = {
        'positive': ['зростання', 'підвищення', 'покращення', 'сильний', 'стабільність',
                    'перемога', 'успіх', 'прорив', 'рекорд', 'позитив'],
        'negative': ['спад', 'падіння', 'криза', 'інфляція', 'війна', 'конфлікт',
                    'обмеження', 'санкції', 'дефіцит', 'зниження', 'негатив'],
        'economic': ['ВВП', 'інфляція', 'відсоткова ставка', 'безробіття', 'експорт',
                    'імпорт', 'бюджет', 'борг', 'дефіцит', 'профицит'],
        'institutions': ['ФРС', 'ЄЦБ', 'НБУ', 'МВФ', 'Світовий банк', 'Мінфін']
    }

    @staticmethod
    def get_kyiv_time():
        """Отримання поточного часу в Києві"""
        return datetime.now(Config.KYIV_TZ)

    @classmethod
    def validate(cls):
        """Перевірка конфігурації"""
        errors = []
        
        if not cls.GROQ_API_KEY:
            errors.append("❌ GROQ_API_KEY не встановлено")
        
        if not cls.CURRENCIES:
            errors.append("❌ Не вказано валюти для аналізу")
        
        if errors:
            for error in errors:
                logger.error(error)
            return False
        return True

    @staticmethod
    def save_config_update():
        """Зберегти інформацію про оновлення конфігурації"""
        config_info = {
            'last_config_update': Config.get_kyiv_time().isoformat(),
            'currencies_count': len(Config.CURRENCIES),
            'crypto_count': len(Config.CRYPTO),
            'news_sources': len(Config.NEWS_SOURCES),
            'language': Config.LANGUAGE
        }
        
        config_file = Config.DATA_DIR / 'config_info.json'
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Не вдалося зберегти інфо конфігурації: {e}")
