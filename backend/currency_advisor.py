import asyncio
import logging
import json
from datetime import datetime, timedelta
import pytz
from config import Config
from news_analyzer import NewsAnalyzer
from economic_data import EconomicDataCollector
from groq_analyzer import GroqAnalyzer
from data_handler import DataHandler

logger = logging.getLogger("currency_advisor")

class CurrencyAdvisor:
    def __init__(self):
        self.news_analyzer = NewsAnalyzer()
        self.economic_data = EconomicDataCollector()
        self.groq_analyzer = GroqAnalyzer()
        self.data_handler = DataHandler()
        
        # Налаштування
        self.cache_hours = Config.CACHE_HOURS
        self.max_recommendations = Config.MAX_RECOMMENDATIONS
        self.language = Config.LANGUAGE

    async def analyze_market(self):
        """Основний метод аналізу ринку"""
        logger.info("=" * 60)
        logger.info(f"🚀 ПОЧАТОК АНАЛІЗУ РИНКУ")
        logger.info(f"🌐 Мова: {self.language}")
        logger.info(f"🕐 Час: {Config.get_kyiv_time().strftime('%Y-%m-%d %H:%M:%S')} (Київ)")
        logger.info(f"💾 Кеш: {self.cache_hours} годин")
        logger.info("=" * 60)

        try:
            # 1. Збір новин
            logger.info("📰 Збір останніх новин...")
            news_data = await self.news_analyzer.get_latest_news()
            
            if not news_data or len(news_data) < 5:
                logger.warning("⚠️  Отримано замало новин, використовуємо кешовані дані")
                news_data = self.data_handler.get_cached_news()

            # 2. Збір економічних показників
            logger.info("📊 Збір економічних показників...")
            economic_data = await self.economic_data.get_latest_indicators()
            
            # 3. Аналіз впливу на валюти
            logger.info("🔍 Аналіз впливу новин на валюти...")
            currency_impact = self._analyze_currency_impact(news_data, economic_data)
            
            # 4. Генерація рекомендацій через AI
            logger.info("🧠 Генерація рекомендацій через AI...")
            recommendations = await self.groq_analyzer.generate_recommendations(
                news_data, 
                economic_data, 
                currency_impact,
                language=self.language
            )
            
            # 5. Формування результату
            market_overview = self._create_market_overview(news_data, economic_data, currency_impact)
            
            result = {
                'timestamp': Config.get_kyiv_time().isoformat(),
                'timestamp_utc': datetime.utcnow().isoformat() + 'Z',
                'timezone': 'Europe/Kiev (UTC+2)',
                'language': self.language,
                'recommendations': recommendations[:self.max_recommendations],
                'market_overview': market_overview,
                'news_count': len(news_data),
                'economic_indicators_count': len(economic_data.get('indicators', {})),
                'currency_impact_summary': self._summarize_impact(currency_impact),
                'analysis_id': f"analysis_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            
            # 6. Збереження результатів
            logger.info("💾 Збереження результатів...")
            save_result = self.data_handler.save_recommendations(result)
            
            if save_result:
                logger.info(f"✅ Збережено {len(recommendations)} рекомендацій")
                
                # Вивід результатів
                logger.info(f"\n🎯 ЗГЕНЕРОВАНО РЕКОМЕНДАЦІЙ: {len(recommendations)}")
                for i, rec in enumerate(recommendations[:5], 1):
                    action_icon = '✅' if 'BUY' in rec['action'] else '❌'
                    logger.info(f"   {i}. {action_icon} {rec['asset']}: {rec['action']} ({rec['confidence']*100:.1f}%)")
                    logger.info(f"      Причина: {rec['reason'][:80]}...")
                
                logger.info(f"\n📊 ОГЛЯД РИНКУ:")
                logger.info(f"   • Загальний настрій: {market_overview.get('overall_sentiment', 'НЕЙТРАЛЬНИЙ')}")
                logger.info(f"   • Найкраща валюта: {market_overview.get('top_currency', 'N/A')}")
                logger.info(f"   • Найгірша валюта: {market_overview.get('worst_currency', 'N/A')}")
            else:
                logger.error("❌ Помилка збереження рекомендацій")
            
            logger.info("=" * 60)
            return result
            
        except Exception as e:
            logger.error(f"💥 Критична помилка аналізу: {e}")
            import traceback
            logger.error(f"📋 Трейс: {traceback.format_exc()}")
            return {}

    def _analyze_currency_impact(self, news_data, economic_data):
        """Аналіз впливу новин на окремі валюти"""
        impact = {}
        
        # Словник ключових слів для кожної валюти
        currency_keywords = {
            'USD': ['долар', 'американськ', 'США', 'ФРС', 'американська економіка', 'долар США'],
            'EUR': ['євро', 'єврозон', 'ЄС', 'Європ', 'ЄЦБ', 'європейськ'],
            'GBP': ['фунт', 'британ', 'Великобритані', 'Банк Англії', 'стерлінг'],
            'JPY': ['єна', 'япон', 'японськ', 'Банк Японії'],
            'UAH': ['гривн', 'україн', 'Україн', 'НБУ', 'українськ'],
            'PLN': ['злотий', 'польськ', 'Польщ', 'польська'],
            'CHF': ['франк', 'швейцар', 'Швейцарія'],
            'CNY': ['юань', 'китай', 'китайськ', 'Китай', 'CNY'],
            'RUB': ['рубл', 'росі', 'Росі', 'російськ'],
            'BTC': ['біткоїн', 'bitcoin', 'BTC', 'крипто', 'криптовалют'],
            'ETH': ['етеріум', 'ethereum', 'ETH'],
            'GOLD': ['золот', 'золото', 'gold', 'коштовні метали']
        }
        
        for currency, keywords in currency_keywords.items():
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            relevant_news = []
            
            for news_item in news_data:
                title = news_item.get('title', '').upper()
                summary = news_item.get('summary', '').upper()
                text = title + ' ' + summary
                
                # Перевіряємо, чи новина стосується цієї валюти
                if any(keyword.upper() in text for keyword in keywords):
                    sentiment = news_item.get('sentiment', 'neutral')
                    
                    if sentiment == 'positive':
                        positive_count += 1
                    elif sentiment == 'negative':
                        negative_count += 1
                    else:
                        neutral_count += 1
                    
                    relevant_news.append({
                        'title': news_item.get('title', '')[:100],
                        'sentiment': sentiment,
                        'source': news_item.get('source', '')
                    })
            
            # Розраховуємо загальний вплив
            total_news = positive_count + negative_count + neutral_count
            if total_news > 0:
                sentiment_score = (positive_count - negative_count) / total_news
                sentiment_score = (sentiment_score + 1) / 2  # Приводимо до діапазону 0-1
            else:
                sentiment_score = 0.5  # Нейтральний, якщо немає новин
            
            impact[currency] = {
                'sentiment_score': round(sentiment_score, 3),
                'positive_news': positive_count,
                'negative_news': negative_count,
                'neutral_news': neutral_count,
                'total_news': total_news,
                'relevant_news_count': len(relevant_news),
                'key_news': relevant_news[:3]  # Топ-3 найважливіші новини
            }
        
        return impact

    def _create_market_overview(self, news_data, economic_data, currency_impact):
        """Створення загального огляду ринку"""
        
        # Аналізуємо загальний настрій новин
        total_positive = sum(1 for n in news_data if n.get('sentiment') == 'positive')
        total_negative = sum(1 for n in news_data if n.get('sentiment') == 'negative')
        
        if total_positive > total_negative * 1.5:
            overall_sentiment = 'ПОЗИТИВНИЙ'
        elif total_negative > total_positive * 1.5:
            overall_sentiment = 'НЕГАТИВНИЙ'
        else:
            overall_sentiment = 'НЕЙТРАЛЬНИЙ'
        
        # Знаходимо найкращу та найгіршу валюту
        if currency_impact:
            sorted_currencies = sorted(
                currency_impact.items(), 
                key=lambda x: x[1]['sentiment_score'], 
                reverse=True
            )
            
            top_currency = sorted_currencies[0][0] if sorted_currencies else 'N/A'
            worst_currency = sorted_currencies[-1][0] if sorted_currencies else 'N/A'
        else:
            top_currency = 'N/A'
            worst_currency = 'N/A'
        
        return {
            'overall_sentiment': overall_sentiment,
            'positive_news_count': total_positive,
            'negative_news_count': total_negative,
            'total_news_analyzed': len(news_data),
            'top_currency': top_currency,
            'worst_currency': worst_currency,
            'market_status': economic_data.get('market_status', {}),
            'last_economic_update': economic_data.get('timestamp', 'N/A'),
            'analysis_time': Config.get_kyiv_time().strftime('%H:%M')
        }

    def _summarize_impact(self, currency_impact):
        """Короткий звіт про вплив"""
        summary = {}
        
        for currency, data in currency_impact.items():
            if data['total_news'] > 0:  # Тільки валюти з новинами
                summary[currency] = {
                    'score': data['sentiment_score'],
                    'trend': '📈' if data['sentiment_score'] > 0.6 else 
                            '📉' if data['sentiment_score'] < 0.4 else '➡️',
                    'news_count': data['total_news']
                }
        
        return summary

async def main():
    """Головна функція"""
    print("\n" + "="*60)
    print(f"🎯 ЗАПУСК КУРСОВОГО РАДНИКА - {Config.get_kyiv_time().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Дата: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"🌐 Мова: {Config.LANGUAGE}")
    print(f"💡 Концепція: Макроекономічний аналіз на основі новин")
    print(f"🔄 Частота: 4 рази на день (08:00, 12:00, 16:00, 20:00 за Києвом)")
    print("="*60)
    
    # Перевірка конфігурації
    if not Config.validate():
        print("❌ Помилка валідації конфігурації. Перевірте змінні оточення.")
        return {}
    
    # Налаштування логування
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Запуск аналізу
    advisor = CurrencyAdvisor()
    result = await advisor.analyze_market()
    
    if result and result.get('recommendations'):
        recommendations = result['recommendations']
        
        print(f"\n✅ АНАЛІЗ ЗАВЕРШЕНО УСПІШНО")
        print(f"📊 Згенеровано рекомендацій: {len(recommendations)}")
        print(f"📰 Проаналізовано новин: {result.get('news_count', 0)}")
        print(f"🏦 Загальний настрій ринку: {result['market_overview'].get('overall_sentiment', 'НЕЙТРАЛЬНИЙ')}")
        
        print(f"\n🎯 ТОП-5 РЕКОМЕНДАЦІЙ:")
        for i, rec in enumerate(recommendations[:5], 1):
            action_icon = '🟢 КУПУВАТИ' if 'BUY' in rec['action'] else '🔴 УНИКАТИ'
            print(f"   {i}. {rec['asset']}: {action_icon} ({rec['confidence']*100:.0f}%)")
            print(f"      📝 {rec['reason'][:80]}...")
        
        print(f"\n📈 НАЙКРАЩА ВАЛЮТА: {result['market_overview'].get('top_currency', 'N/A')}")
        print(f"📉 НАЙГІРША ВАЛЮТА: {result['market_overview'].get('worst_currency', 'N/A')}")
        
        # Інформація про наступний аналіз
        now_kyiv = Config.get_kyiv_time()
        analysis_times = [8, 12, 16, 20]
        
        next_times = []
        for hour in analysis_times:
            if now_kyiv.hour < hour:
                next_time = now_kyiv.replace(hour=hour, minute=0, second=0, microsecond=0)
                time_diff = next_time - now_kyiv
                hours_left = time_diff.seconds // 3600
                minutes_left = (time_diff.seconds % 3600) // 60
                next_times.append(f"{hour:02d}:00 (через {hours_left} год {minutes_left} хв)")
        
        if next_times:
            print(f"\n⏰ НАСТУПНИЙ АНАЛІЗ: {next_times[0]}")
        else:
            print(f"\n⏰ НАСТУПНИЙ АНАЛІЗ: завтра о 08:00")
        
    else:
        print("\n⚠️  РЕКОМЕНДАЦІЙ НЕ ЗНАЙДЕНО")
        print("ℹ️  Можливі причини:")
        print("   - Недостатньо новин для аналізу")
        print("   - Проблеми з отриманням даних")
        print("   - AI не зміг згенерувати рекомендації")
    
    print("="*60)
    print(f"🕐 Час завершення: {Config.get_kyiv_time().strftime('%H:%M:%S')}")
    print("="*60)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
