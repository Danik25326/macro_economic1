import json
import os
import logging
from datetime import datetime, timedelta
import pytz
from config import Config

logger = logging.getLogger("data_handler")

class DataHandler:
    def __init__(self):
        self.data_dir = Config.DATA_DIR
        self.kyiv_tz = pytz.timezone('Europe/Kiev')
        self.create_data_dir()

    def create_data_dir(self):
        """Створення директорій для даних"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Створюємо всі необхідні файли, якщо їх немає
        if not os.path.exists(Config.RECOMMENDATIONS_FILE):
            with open(Config.RECOMMENDATIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "last_update": None,
                    "recommendations": [],
                    "market_overview": {},
                    "timezone": "Europe/Kiev",
                    "analysis_id": None,
                    "total_recommendations": 0,
                    "next_analysis": None
                }, f, indent=2, ensure_ascii=False)
        
        if not os.path.exists(Config.HISTORY_FILE):
            with open(Config.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2, ensure_ascii=False)
                
        if not os.path.exists(Config.NEWS_CACHE_FILE):
            with open(Config.NEWS_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "last_update": None,
                    "news": [],
                    "news_count": 0,
                    "cache_expiry": None
                }, f, indent=2, ensure_ascii=False)
        
        if not os.path.exists(Config.ECONOMIC_INDICATORS_FILE):
            with open(Config.ECONOMIC_INDICATORS_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "last_update": None,
                    "indicators": {},
                    "market_status": {}
                }, f, indent=2, ensure_ascii=False)

    def save_recommendations(self, data):
        """Збереження рекомендацій"""
        try:
            if not data or 'recommendations' not in data:
                logger.error("⚠️ Немає даних для збереження")
                return False
            
            recommendations = data.get('recommendations', [])
            
            if not recommendations:
                logger.warning("⚠️ Немає рекомендацій для збереження")
                return False
            
            now_kyiv = Config.get_kyiv_time()
            
            # Оновлюємо дані
            data_to_save = {
                "last_update": now_kyiv.isoformat(),
                "last_update_display": now_kyiv.strftime('%Y-%m-%d %H:%M:%S'),
                "recommendations": recommendations,
                "market_overview": data.get('market_overview', {}),
                "timezone": "Europe/Kiev (UTC+2)",
                "analysis_id": data.get('analysis_id', ''),
                "total_recommendations": len(recommendations),
                "news_count": data.get('news_count', 0),
                "language": data.get('language', 'uk'),
                "next_analysis": self._calculate_next_analysis_time()
            }
            
            # Зберігаємо в основний файл
            with open(Config.RECOMMENDATIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False, default=str)
            
            # Додаємо в історію
            self._add_to_history(data)
            
            # Оновлюємо кеш новин
            if 'news_summary' in data:
                self._update_news_cache(data.get('news_data', []))
            
            logger.info(f"💾 Збережено {len(recommendations)} рекомендацій")
            
            # Очищаємо старі дані з історії
            self._cleanup_old_history()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Помилка збереження рекомендацій: {e}")
            import traceback
            logger.error(f"Деталі: {traceback.format_exc()}")
            return False

    def _calculate_next_analysis_time(self):
        """Розрахунок часу наступного аналізу"""
        now_kyiv = Config.get_kyiv_time()
        analysis_hours = [8, 12, 16, 20]
        
        for hour in analysis_hours:
            if now_kyiv.hour < hour:
                next_time = now_kyiv.replace(hour=hour, minute=0, second=0, microsecond=0)
                return next_time.isoformat()
        
        # Якщо всі години минули сьогодні, беремо першу годину завтра
        next_time = (now_kyiv + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
        return next_time.isoformat()

    def _add_to_history(self, data):
        """Додавання даних до історії"""
        try:
            history = []
            if os.path.exists(Config.HISTORY_FILE):
                with open(Config.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # Створюємо запис історії
            history_entry = {
                'timestamp': data.get('timestamp', Config.get_kyiv_time().isoformat()),
                'analysis_id': data.get('analysis_id', ''),
                'recommendations_count': len(data.get('recommendations', [])),
                'market_overview': data.get('market_overview', {}),
                'top_recommendations': data.get('recommendations', [])[:3]
            }
            
            history.append(history_entry)
            
            # Обмежуємо історію останніми 100 записами
            if len(history) > 100:
                history = history[-100:]
            
            with open(Config.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False, default=str)
                
            logger.debug(f"📚 Додано запис до історії: {history_entry['analysis_id']}")
                
        except Exception as e:
            logger.error(f"❌ Помилка додавання в історію: {e}")

    def _update_news_cache(self, news_data):
        """Оновлення кешу новин"""
        try:
            if not news_data:
                return
            
            cache_data = {
                'last_update': Config.get_kyiv_time().isoformat(),
                'news': news_data[:50],  # Кешуємо максимум 50 новин
                'news_count': len(news_data),
                'cache_expiry': (Config.get_kyiv_time() + timedelta(hours=Config.CACHE_HOURS)).isoformat()
            }
            
            with open(Config.NEWS_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.debug(f"💾 Оновлено кеш новин: {len(news_data)} записів")
            
        except Exception as e:
            logger.error(f"❌ Помилка оновлення кешу новин: {e}")

    def get_cached_news(self):
        """Отримати кешовані новини"""
        try:
            if os.path.exists(Config.NEWS_CACHE_FILE):
                with open(Config.NEWS_CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Перевіряємо, чи кеш не застарів
                cache_expiry_str = data.get('cache_expiry')
                if cache_expiry_str:
                    cache_expiry = datetime.fromisoformat(cache_expiry_str)
                    if Config.get_kyiv_time() < cache_expiry:
                        return data.get('news', [])
        
        except Exception as e:
            logger.debug(f"Помилка читання кешу новин: {e}")
        
        return []

    def load_recommendations(self):
        """Завантаження поточних рекомендацій"""
        try:
            if os.path.exists(Config.RECOMMENDATIONS_FILE):
                with open(Config.RECOMMENDATIONS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            return {
                "last_update": None,
                "recommendations": [],
                "market_overview": {},
                "timezone": "Europe/Kiev",
                "analysis_id": None,
                "total_recommendations": 0,
                "next_analysis": None
            }
        except Exception as e:
            logger.error(f"❌ Помилка завантаження рекомендацій: {e}")
            return {}

    def load_history(self, days=7):
        """Завантаження історії за останні дні"""
        try:
            if os.path.exists(Config.HISTORY_FILE):
                with open(Config.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                # Фільтруємо за датою
                filtered_history = []
                cutoff_date = Config.get_kyiv_time() - timedelta(days=days)
                
                for entry in history:
                    entry_date_str = entry.get('timestamp')
                    if entry_date_str:
                        try:
                            entry_date = datetime.fromisoformat(entry_date_str)
                            if entry_date.tzinfo is None:
                                entry_date = pytz.UTC.localize(entry_date)
                            
                            if entry_date >= cutoff_date:
                                filtered_history.append(entry)
                        except:
                            continue
                
                return filtered_history
        
        except Exception as e:
            logger.error(f"❌ Помилка завантаження історії: {e}")
        
        return []

    def _cleanup_old_history(self):
        """Очищення старої історії"""
        try:
            # Завантажуємо всю історію
            history = self.load_history(days=365)  # Завантажуємо за рік
            
            # Залишаємо тільки останні 100 записів
            if len(history) > 100:
                history = history[-100:]
                
                with open(Config.HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=2, ensure_ascii=False, default=str)
                
                logger.debug(f"🧹 Очищено історію: залишено {len(history)} записів")
                
        except Exception as e:
            logger.error(f"❌ Помилка очищення історії: {e}")

    def get_statistics(self):
        """Отримання статистики"""
        stats = {
            'total_analyses': 0,
            'last_analysis': None,
            'avg_recommendations': 0,
            'most_recommended': [],
            'least_recommended': []
        }
        
        try:
            history = self.load_history(days=30)
            
            if history:
                stats['total_analyses'] = len(history)
                stats['last_analysis'] = history[-1].get('timestamp') if history else None
                
                # Рахуємо середню кількість рекомендацій
                total_recs = sum(h.get('recommendations_count', 0) for h in history)
                stats['avg_recommendations'] = round(total_recs / len(history), 1) if history else 0
                
                # Аналізуємо найбільш рекомендовані активи
                asset_counts = {}
                for entry in history:
                    for rec in entry.get('top_recommendations', []):
                        asset = rec.get('asset')
                        action = rec.get('action')
                        
                        if asset and ('BUY' in action or 'STRONG_BUY' in action):
                            asset_counts[asset] = asset_counts.get(asset, 0) + 1
                
                if asset_counts:
                    sorted_assets = sorted(asset_counts.items(), key=lambda x: x[1], reverse=True)
                    stats['most_recommended'] = sorted_assets[:5]
        
        except Exception as e:
            logger.error(f"❌ Помилка отримання статистики: {e}")
        
        return stats
