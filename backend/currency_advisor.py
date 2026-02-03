import asyncio
import logging
from datetime import datetime
from typing import Dict, List
import pytz
from config import Config
from news_analyzer import NewsAnalyzer
from economic_data import EconomicDataCollector

logger = logging.getLogger("currency_advisor")

class CurrencyAdvisor:
    def __init__(self):
        self.news_analyzer = NewsAnalyzer()
        self.economic_data = EconomicDataCollector()
        
        # Основні валюти та активи для аналізу
        self.currencies = [
            'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD',
            'CNY', 'RUB', 'UAH'
        ]
        
        self.crypto = [
            'BTC', 'ETH', 'XRP', 'SOL', 'ADA'
        ]
        
        self.commodities = [
            'GOLD', 'OIL', 'SILVER'
        ]

    async def analyze_market_sentiment(self) -> Dict:
        """Аналіз ринкової ситуації на основі новин"""
        try:
            logger.info("📰 Збір та аналіз новин...")
            
            # Збираємо останні новини
            news = await self.news_analyzer.get_latest_news()
            
            # Збираємо економічні показники
            economic_data = await self.economic_data.get_latest_indicators()
            
            # Аналізуємо вплив на валюти
            analysis = await self._analyze_impact(news, economic_data)
            
            # Формуємо рекомендації
            recommendations = self._generate_recommendations(analysis)
            
            return {
                'timestamp': Config.get_kyiv_time().isoformat(),
                'analysis': analysis,
                'recommendations': recommendations,
                'news_summary': news[:3],  # 3 найважливіші новини
                'economic_indicators': economic_data
            }
            
        except Exception as e:
            logger.error(f"❌ Помилка аналізу: {e}")
            return {}

    async def _analyze_impact(self, news: List, economic_data: Dict) -> Dict:
        """Аналіз впливу новин на валюти"""
        impact_analysis = {}
        
        # Ключові слова для кожної валюти
        currency_keywords = {
            'USD': ['ФРС', 'долар', 'американська економіка', 'інфляція США'],
            'EUR': ['ЄЦБ', 'євро', 'єврозона', 'економіка ЄС'],
            'GBP': ['Банк Англії', 'фунт', 'Великобританія'],
            'JPY': ['Банк Японії', 'єна', 'Японія'],
            'UAH': ['НБУ', 'гривня', 'Україна']
        }
        
        for currency, keywords in currency_keywords.items():
            impact = {
                'positive_news': 0,
                'negative_news': 0,
                'neutral_news': 0,
                'sentiment_score': 0.5,  # нейтральний по дефолту
                'key_events': []
            }
            
            # Аналізуємо новини для кожної валюти
            for item in news:
                if any(keyword in item.get('title', '').upper() for keyword in keywords):
                    sentiment = item.get('sentiment', 'neutral')
                    if sentiment == 'positive':
                        impact['positive_news'] += 1
                        impact['sentiment_score'] += 0.1
                    elif sentiment == 'negative':
                        impact['negative_news'] += 1
                        impact['sentiment_score'] -= 0.1
                    
                    impact['key_events'].append({
                        'title': item.get('title', ''),
                        'sentiment': sentiment
                    })
            
            impact_analysis[currency] = impact
            
        return impact_analysis

    def _generate_recommendations(self, analysis: Dict) -> List[Dict]:
        """Генерація рекомендацій на основі аналізу"""
        recommendations = []
        
        for currency, data in analysis.items():
            score = data['sentiment_score']
            
            if score >= 0.7:
                recommendation = {
                    'asset': currency,
                    'action': 'STRONG_BUY',
                    'confidence': score,
                    'reason': f'Позитивні новини для {currency} ({data["positive_news"]} позитивних новин)',
                    'timeframe': '1-3 дні'
                }
            elif score >= 0.6:
                recommendation = {
                    'asset': currency,
                    'action': 'BUY',
                    'confidence': score,
                    'reason': f'Переважно позитивні новини для {currency}',
                    'timeframe': '1-2 дні'
                }
            elif score <= 0.4:
                recommendation = {
                    'asset': currency,
                    'action': 'AVOID',
                    'confidence': 1 - score,
                    'reason': f'Негативні новини для {currency} ({data["negative_news"]} негативних новин)',
                    'timeframe': 'Найближчий час'
                }
            elif score <= 0.3:
                recommendation = {
                    'asset': currency,
                    'action': 'STRONG_AVOID',
                    'confidence': 1 - score,
                    'reason': f'Сильні негативні новини для {currency}',
                    'timeframe': 'Декілька днів'
                }
            else:
                continue  # Пропускаємо нейтральні
            
            recommendations.append(recommendation)
        
        # Сортуємо за впевненістю
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return recommendations[:6]  # Повертаємо топ-6 рекомендацій

async def main():
    """Головна функція"""
    print(f"\n🎯 ЗАПУСК КУРСОВОГО РАДНИКА - {Config.get_kyiv_time().strftime('%Y-%m-%d %H:%M:%S')}")
    
    advisor = CurrencyAdvisor()
    result = await advisor.analyze_market_sentiment()
    
    if result:
        print(f"\n📊 РЕКОМЕНДАЦІЇ:")
        for rec in result.get('recommendations', []):
            action_icon = '✅' if 'BUY' in rec['action'] else '❌'
            print(f"{action_icon} {rec['asset']}: {rec['action']} ({rec['confidence']*100:.0f}%)")
            print(f"   Причина: {rec['reason']}")
            print(f"   Час: {rec['timeframe']}")
        
        # Зберігаємо результати
        DataHandler().save_recommendations(result)
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
