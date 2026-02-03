import aiohttp
import json
from datetime import datetime
import pytz

class EconomicDataCollector:
    def __init__(self):
        self.base_urls = {
            'exchange_rates': 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json',
            'inflation': 'https://api.example.com/inflation',  # Замінити на реальне API
            'interest_rates': 'https://api.example.com/rates'   # Замінити на реальне API
        }
        
    async def get_latest_indicators(self):
        """Отримати останні економічні показники"""
        indicators = {}
        
        try:
            # Курси валют НБУ
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_urls['exchange_rates']) as response:
                    if response.status == 200:
                        data = await response.json()
                        indicators['exchange_rates'] = {
                            'USD': next((item for item in data if item['cc'] == 'USD'), {}).get('rate', 0),
                            'EUR': next((item for item in data if item['cc'] == 'EUR'), {}).get('rate', 0)
                        }
        except Exception as e:
            print(f"⚠️ Помилка отримання економічних даних: {e}")
        
        # Додаємо інші показники
        indicators['timestamp'] = datetime.now(pytz.timezone('Europe/Kiev')).isoformat()
        indicators['market_status'] = self._get_market_status()
        
        return indicators
    
    def _get_market_status(self):
        """Статус ринків (відкриті/закриті)"""
        now_kyiv = datetime.now(pytz.timezone('Europe/Kiev'))
        hour = now_kyiv.hour
        
        status = {
            'forex': 'OPEN' if 1 <= hour <= 23 else 'CLOSED',
            'crypto': 'OPEN',  # Крипта працює 24/7
            'us_stock': 'OPEN' if 16 <= hour <= 23 else 'CLOSED',  # 16:00-23:00 за Києвом
            'eu_stock': 'OPEN' if 10 <= hour <= 18 else 'CLOSED'   # 10:00-18:00 за Києвом
        }
        
        return status
