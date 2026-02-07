import aiohttp
import asyncio
import json
import logging
from datetime import datetime, timedelta
import pytz
from typing import Dict, Any, List
from config import Config

logger = logging.getLogger("economic_data")

class EconomicDataCollector:
    def __init__(self):
        self.kyiv_tz = pytz.timezone('Europe/Kiev')
        self.session = None
        
        # API endpoints для економічних даних
        self.api_endpoints = {
            'nbu_exchange': 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json',
            'nbu_interest': 'https://bank.gov.ua/NBUStatService/v1/statdirectory/discount?json',
            'cryptocompare': 'https://min-api.cryptocompare.com/data/pricemulti',
            'metal_api': 'https://api.metalpriceapi.com/v1/latest'  # Потребує API ключ
        }
        
        # Кешовані дані
        self.cache = {}
        self.cache_expiry = {}

    async def get_latest_indicators(self) -> Dict[str, Any]:
        """Отримати останні економічні показники"""
        logger.info("📊 Збір економічних показників...")
        
        indicators = {
            'timestamp': datetime.now(self.kyiv_tz).isoformat(),
            'indicators': {},
            'market_status': {},
            'warnings': []
        }
        
        # Виконуємо всі запити паралельно
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            tasks = [
                self._get_exchange_rates(),
                self._get_market_status(),
                self._get_interest_rates(),
                self._get_crypto_prices(),
                self._get_commodity_prices()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обробляємо результати
            exchange_rates = results[0] if not isinstance(results[0], Exception) else {}
            market_status = results[1] if not isinstance(results[1], Exception) else {}
            interest_rates = results[2] if not isinstance(results[2], Exception) else {}
            crypto_prices = results[3] if not isinstance(results[3], Exception) else {}
            commodity_prices = results[4] if not isinstance(results[4], Exception) else {}
            
            # Збираємо всі показники
            indicators['indicators']['exchange_rates'] = exchange_rates
            indicators['indicators']['interest_rates'] = interest_rates
            indicators['indicators']['crypto'] = crypto_prices
            indicators['indicators']['commodities'] = commodity_prices
            indicators['market_status'] = market_status
            
            # Додаємо примітки про джерела
            indicators['sources'] = {
                'exchange_rates': 'НБУ',
                'market_status': 'Розрахунковий',
                'crypto': 'CryptoCompare',
                'commodities': 'Різні джерела'
            }
            
            # Перевіряємо наявність критичних даних
            if not exchange_rates:
                indicators['warnings'].append('Відсутні дані про курси валют')
            
            if not market_status:
                indicators['warnings'].append('Немає інформації про статус ринків')
        
        logger.info(f"✅ Отримано {len(indicators['indicators'])} категорій економічних даних")
        return indicators

    async def _get_exchange_rates(self) -> Dict[str, float]:
        """Отримати курси валют від НБУ"""
        try:
            # Перевіряємо кеш
            cache_key = 'exchange_rates'
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]
            
            async with self.session.get(self.api_endpoints['nbu_exchange'], timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    exchange_rates = {}
                    currencies_needed = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'PLN']
                    
                    for item in data:
                        currency = item.get('cc')
                        if currency in currencies_needed:
                            exchange_rates[currency] = {
                                'rate': item.get('rate', 0),
                                'date': item.get('exchangedate', ''),
                                'name': item.get('txt', '')
                            }
                    
                    # Додаємо гривню
                    exchange_rates['UAH'] = {
                        'rate': 1.0,
                        'date': datetime.now().strftime('%d.%m.%Y'),
                        'name': 'Українська гривня'
                    }
                    
                    # Кешуємо результати на 1 годину
                    self._update_cache(cache_key, exchange_rates, hours=1)
                    
                    return exchange_rates
                    
        except Exception as e:
            logger.warning(f"⚠️ Помилка отримання курсів валют: {e}")
        
        # Повертаємо останні кешовані дані або пустий словник
        return self.cache.get('exchange_rates', {})

    async def _get_market_status(self) -> Dict[str, str]:
        """Визначити статус ринків (відкриті/закриті)"""
        now_kyiv = datetime.now(self.kyiv_tz)
        weekday = now_kyiv.weekday()  # 0 - понеділок, 6 - неділя
        hour = now_kyiv.hour
        
        status = {}
        
        # Форекс працює 24/5 (з неділі 23:00 до п'ятниці 23:00)
        if weekday < 5 or (weekday == 5 and hour < 23) or (weekday == 6 and hour >= 23):
            status['forex'] = {
                'status': 'OPEN',
                'next_change': 'Пт 23:00' if weekday < 5 else 'Нд 23:00'
            }
        else:
            status['forex'] = {
                'status': 'CLOSED',
                'next_change': 'Нд 23:00'
            }
        
        # Криптовалютний ринок працює 24/7
        status['crypto'] = {
            'status': 'OPEN',
            'next_change': 'Немає'
        }
        
        # Європейські ринки (09:00-17:30 за Києвом)
        if weekday < 5 and 8 <= hour < 17:
            status['european_stocks'] = {
                'status': 'OPEN',
                'next_change': '17:30'
            }
        else:
            status['european_stocks'] = {
                'status': 'CLOSED',
                'next_change': 'Пн 09:00' if weekday >= 5 else '09:00'
            }
        
        # Американські ринки (16:30-23:00 за Києвом)
        if weekday < 5 and 16 <= hour < 23:
            status['us_stocks'] = {
                'status': 'OPEN',
                'next_change': '23:00'
            }
        else:
            status['us_stocks'] = {
                'status': 'CLOSED',
                'next_change': 'Пн 16:30' if weekday >= 5 else '16:30'
            }
        
        # Український ринок (10:00-18:00 за Києвом)
        if weekday < 5 and 10 <= hour < 18:
            status['ukrainian_stocks'] = {
                'status': 'OPEN',
                'next_change': '18:00'
            }
        else:
            status['ukrainian_stocks'] = {
                'status': 'CLOSED',
                'next_change': 'Пн 10:00' if weekday >= 5 else '10:00'
            }
        
        # Загальний статус
        if any(s['status'] == 'OPEN' for s in status.values()):
            status['overall'] = 'ACTIVE'
        else:
            status['overall'] = 'INACTIVE'
        
        return status

    async def _get_interest_rates(self) -> Dict[str, float]:
        """Отримати відсоткові ставки центральних банків"""
        try:
            cache_key = 'interest_rates'
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]
            
            # Ставки центральних банків (можна отримати з API, поки що статичні дані)
            rates = {
                'ФРС США': 5.25,      # Federal Reserve
                'ЄЦБ': 4.0,           # European Central Bank
                'Банк Англії': 5.25,   # Bank of England
                'НБУ': 15.0,           # Національний банк України
                'Банк Японії': -0.1,   # Bank of Japan (негативна ставка)
                'ШНБ': 1.75            # Швейцарський національний банк
            }
            
            self._update_cache(cache_key, rates, hours=24)
            return rates
            
        except Exception as e:
            logger.warning(f"⚠️ Помилка отримання ставок: {e}")
            return {}

    async def _get_crypto_prices(self) -> Dict[str, Any]:
        """Отримати ціни криптовалют"""
        try:
            cache_key = 'crypto_prices'
            if self._is_cache_valid(cache_key, minutes=5):  # Крипта часто змінюється
                return self.cache[cache_key]
            
            # Використовуємо CryptoCompare API
            cryptos = ['BTC', 'ETH', 'BNB', 'XRP', 'SOL', 'ADA', 'DOT', 'DOGE']
            fsyms = ','.join(cryptos)
            
            url = f"{self.api_endpoints['cryptocompare']}?fsyms={fsyms}&tsyms=USD,EUR"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    crypto_data = {}
                    for crypto in cryptos:
                        if crypto in data:
                            crypto_data[crypto] = {
                                'USD': data[crypto].get('USD', 0),
                                'EUR': data[crypto].get('EUR', 0),
                                'updated': datetime.now().isoformat()
                            }
                    
                    self._update_cache(cache_key, crypto_data, minutes=5)
                    return crypto_data
                    
        except Exception as e:
            logger.warning(f"⚠️ Помилка отримання цін криптовалют: {e}")
        
        return {}

    async def _get_commodity_prices(self) -> Dict[str, float]:
        """Отримати ціни на товари (золото, нафта)"""
        try:
            cache_key = 'commodity_prices'
            if self._is_cache_valid(cache_key, hours=1):
                return self.cache[cache_key]
            
            # Тут можна додати реальні API для товарів
            # Поки що статичні дані або симуляція
            commodities = {
                'GOLD': {
                    'price': 1950.50,
                    'currency': 'USD',
                    'unit': 'за тройську унцію',
                    'change': '+0.5%'
                },
                'OIL_BRENT': {
                    'price': 82.30,
                    'currency': 'USD',
                    'unit': 'за барель',
                    'change': '-0.3%'
                },
                'SILVER': {
                    'price': 23.15,
                    'currency': 'USD',
                    'unit': 'за тройську унцію',
                    'change': '+0.2%'
                },
                'NATURAL_GAS': {
                    'price': 2.85,
                    'currency': 'USD',
                    'unit': 'за млн BTU',
                    'change': '-1.1%'
                }
            }
            
            self._update_cache(cache_key, commodities, hours=1)
            return commodities
            
        except Exception as e:
            logger.warning(f"⚠️ Помилка отримання цін товарів: {e}")
            return {}

    def _is_cache_valid(self, key: str, minutes: int = 60, hours: int = 0) -> bool:
        """Перевірити, чи кеш ще дійсний"""
        if key not in self.cache or key not in self.cache_expiry:
            return False
        
        expiry_time = self.cache_expiry[key]
        return datetime.now() < expiry_time

    def _update_cache(self, key: str, data: Any, minutes: int = 0, hours: int = 0):
        """Оновити кеш"""
        self.cache[key] = data
        
        # Розраховуємо час закінчення
        expiry = datetime.now() + timedelta(minutes=minutes, hours=hours)
        self.cache_expiry[key] = expiry

    def get_cached_data(self, key: str) -> Any:
        """Отримати кешовані дані"""
        return self.cache.get(key, None)

    async def get_economic_calendar(self, days: int = 7) -> List[Dict]:
        """Отримати економічний календар (майбутні події)"""
        # Заглушка для майбутньої реалізації
        # Можна використати API як Investing.com, ForexFactory тощо
        return [
            {
                'date': '2024-01-15',
                'time': '15:30',
                'country': 'USA',
                'event': 'Рішення ФРС щодо процентної ставки',
                'importance': 'high',
                'previous': '5.25%',
                'forecast': '5.25%'
            },
            {
                'date': '2024-01-16',
                'time': '11:00',
                'country': 'EU',
                'event': 'Інфляція в Єврозоні',
                'importance': 'medium',
                'previous': '2.4%',
                'forecast': '2.3%'
            }
        ]
