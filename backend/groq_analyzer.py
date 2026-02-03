import json
import logging
from groq import Groq
from datetime import datetime
from config import Config

logger = logging.getLogger("groq_analyzer")

class GroqAnalyzer:
    def __init__(self):
        if not Config.GROQ_API_KEY:
            logger.error("❌ GROQ_API_KEY не налаштовано!")
            self.client = None
        else:
            self.client = Groq(api_key=Config.GROQ_API_KEY)
            logger.info(f"✅ Groq AI ініціалізовано (модель: {Config.GROQ_MODEL})")

    async def generate_recommendations(self, news_data, economic_data, currency_impact, language='uk'):
        """
        Генерація рекомендацій через AI на основі новин та економічних даних
        """
        if not self.client:
            logger.error("Groq AI не ініціалізовано.")
            return []

        if not news_data or len(news_data) < 3:
            logger.warning("Недостатньо новин для аналізу")
            return []

        now_kyiv = Config.get_kyiv_time()

        # Підготовка даних для AI
        news_summary = self._prepare_news_summary(news_data, language)
        economic_summary = self._prepare_economic_summary(economic_data, language)
        
        # Формування промпта
        if language == 'ru':
            prompt = self._create_russian_prompt(news_summary, economic_summary, now_kyiv)
        else:
            prompt = self._create_ukrainian_prompt(news_summary, economic_summary, now_kyiv)

        try:
            logger.info("🧠 Генерація рекомендацій через AI...")
            
            completion = self.client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(language)
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,  # Нижча температура для більш консервативних рекомендацій
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            response_text = completion.choices[0].message.content
            logger.debug(f"AI відповідь (перші 300 символів): {response_text[:300]}...")
            
            response = json.loads(response_text)
            
            # Валідація відповіді
            recommendations = self._validate_recommendations(response.get('recommendations', []))
            
            logger.info(f"✅ AI згенерував {len(recommendations)} рекомендацій")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Помилка Groq AI: {e}")
            # Резервні рекомендації на основі простих правил
            return self._generate_fallback_recommendations(currency_impact, language)

    def _prepare_news_summary(self, news_data, language):
        """Підготовка зведення новин для AI"""
        # Беремо 10 найважливіших новин
        top_news = sorted(news_data, key=lambda x: x.get('relevance', 0), reverse=True)[:10]
        
        summary_lines = []
        
        for i, news in enumerate(top_news, 1):
            title = news.get('title', '')
            sentiment = news.get('sentiment', 'neutral')
            source = news.get('source', '')
            
            sentiment_emoji = {
                'positive': '📈',
                'negative': '📉',
                'neutral': '📊'
            }.get(sentiment, '📊')
            
            summary_lines.append(f"{i}. {sentiment_emoji} {title} ({source})")
        
        return "\n".join(summary_lines[:15])  # Обмежуємо довжину

    def _prepare_economic_summary(self, economic_data, language):
        """Підготовка зведення економічних показників"""
        indicators = economic_data.get('indicators', {})
        
        summary = []
        
        # Курси валют
        exchange_rates = indicators.get('exchange_rates', {})
        if exchange_rates:
            rates_text = []
            for currency in ['USD', 'EUR', 'GBP', 'JPY']:
                if currency in exchange_rates:
                    rate_info = exchange_rates[currency]
                    rate = rate_info.get('rate', 0)
                    if currency == 'UAH':
                        rates_text.append(f"{currency}: {rate:.2f} (базова)")
                    else:
                        rates_text.append(f"{currency}: {rate:.2f}")
            
            if rates_text:
                summary.append(f"💱 Курси валют: {', '.join(rates_text[:4])}")
        
        # Криптовалюти
        crypto = indicators.get('crypto', {})
        if crypto:
            crypto_text = []
            for coin in ['BTC', 'ETH']:
                if coin in crypto:
                    price = crypto[coin].get('USD', 0)
                    crypto_text.append(f"{coin}: ${price:,.0f}")
            
            if crypto_text:
                summary.append(f"🪙 Криптовалюти: {', '.join(crypto_text)}")
        
        # Статус ринків
        market_status = economic_data.get('market_status', {})
        if market_status.get('overall') == 'ACTIVE':
            summary.append("🏛️ Ринки: АКТИВНІ")
        else:
            summary.append("🏛️ Ринки: НЕАКТИВНІ")
        
        return "\n".join(summary)

    def _create_ukrainian_prompt(self, news_summary, economic_summary, now_kyiv):
        """Створення промпта українською"""
        return f"""
Ти - фінансовий аналітик з досвідом 20 років. Твоя задача - дати інвестиційні рекомендації на основі новин та економічних даних.

Дата аналізу: {now_kyiv.strftime('%Y-%m-%d %H:%M')} (Київський час)

📰 ОСТАННІ НОВИНИ (впорядковано за важливістю):
{news_summary}

📊 ЕКОНОМІЧНІ ПОКАЗНИКИ:
{economic_summary}

Аналізуй та дай рекомендації щодо наступних активів:
- Основні валюти: USD, EUR, GBP, JPY, CHF, UAH
- Криптовалюти: BTC, ETH
- Товари: GOLD (золото)

ФОРМАТ ВІДПОВІДІ (JSON):
{{
  "market_overview": "Короткий огляд ринкової ситуації (2-3 речення)",
  "overall_sentiment": "positive/neutral/negative",
  "recommendations": [
    {{
      "asset": "EUR",
      "action": "STRONG_BUY/BUY/NEUTRAL/AVOID/STRONG_AVOID",
      "confidence": 0.85,
      "reason": "Детальне пояснення (2-3 речення)",
      "timeframe": "Найближчий час/1-3 дні/тиждень",
      "risk_level": "low/medium/high"
    }}
  ],
  "key_risks": ["Основний ризик 1", "Основний ризик 2"],
  "general_advice": "Загальна порада інвесторам"
}}

ВИМОГИ:
1. Мінімум 3 рекомендації, максимум 8
2. Confidence (впевненість) має бути від 0.6 до 0.95
3. Пояснення мають бути конкретними та ґрунтуватися на новинах
4. Не рекомендуй активи, якщо немає достатніх даних
5. Будь консервативним, уникай надмірно ризикованих рекомендацій
"""

    def _create_russian_prompt(self, news_summary, economic_summary, now_kyiv):
        """Створення промпта російською"""
        return f"""
Ты - финансовый аналитик с 20-летним опытом. Твоя задача - дать инвестиционные рекомендации на основе новостей и экономических данных.

Дата анализа: {now_kyiv.strftime('%Y-%m-%d %H:%M')} (Киевское время)

📰 ПОСЛЕДНИЕ НОВОСТИ (отсортированы по важности):
{news_summary}

📊 ЭКОНОМИЧЕСКИЕ ПОКАЗАТЕЛИ:
{economic_summary}

Проанализируй и дай рекомендации по следующим активам:
- Основные валюты: USD, EUR, GBP, JPY, CHF, UAH
- Криптовалюты: BTC, ETH
- Товары: GOLD (золото)

ФОРМАТ ОТВЕТА (JSON):
{{
  "market_overview": "Краткий обзор рыночной ситуации (2-3 предложения)",
  "overall_sentiment": "positive/neutral/negative",
  "recommendations": [
    {{
      "asset": "EUR",
      "action": "STRONG_BUY/BUY/NEUTRAL/AVOID/STRONG_AVOID",
      "confidence": 0.85,
      "reason": "Подробное объяснение (2-3 предложения)",
      "timeframe": "Ближайшее время/1-3 дня/неделя",
      "risk_level": "low/medium/high"
    }}
  ],
  "key_risks": ["Основной риск 1", "Основной риск 2"],
  "general_advice": "Общий совет инвесторам"
}}

ТРЕБОВАНИЯ:
1. Минимум 3 рекомендации, максимум 8
2. Confidence (уверенность) должна быть от 0.6 до 0.95
3. Объяснения должны быть конкретными и основанными на новостях
4. Не рекомендуй активы, если нет достаточных данных
5. Будь консервативным, избегай излишне рискованных рекомендаций
"""

    def _get_system_prompt(self, language):
        """Системний промпт для AI"""
        if language == 'ru':
            return """Ты опытный финансовый аналитик. Твои рекомендации должны быть:
1. Основаны на фактах из новостей
2. Консервативны и взвешены
3. Содержат конкретные причины
4. Учитывают риски
5. Практичны и полезны для инвесторов"""
        else:
            return """Ти досвідчений фінансовий аналітик. Твої рекомендації мають бути:
1. Засновані на фактах з новин
2. Консервативні та зважені
3. Містити конкретні причини
4. Враховувати ризики
5. Практичні та корисні для інвесторів"""

    def _validate_recommendations(self, recommendations):
        """Валідація рекомендацій від AI"""
        valid_recommendations = []
        
        for rec in recommendations:
            try:
                # Перевіряємо обов'язкові поля
                required_fields = ['asset', 'action', 'confidence', 'reason']
                for field in required_fields:
                    if field not in rec:
                        logger.warning(f"Рекомендація пропущена: немає поля {field}")
                        continue
                
                # Перевіряємо впевненість
                confidence = float(rec['confidence'])
                if confidence < Config.MIN_CONFIDENCE:
                    logger.debug(f"Рекомендація {rec['asset']} пропущена: низька впевненість {confidence}")
                    continue
                
                # Додаємо додаткові поля
                rec['id'] = f"{rec['asset']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                rec['generated_at'] = Config.get_kyiv_time().isoformat()
                rec['confidence'] = round(confidence, 3)
                
                # Перевіряємо дію
                valid_actions = ['STRONG_BUY', 'BUY', 'NEUTRAL', 'AVOID', 'STRONG_AVOID']
                if rec['action'] not in valid_actions:
                    rec['action'] = 'NEUTRAL'
                
                valid_recommendations.append(rec)
                
            except Exception as e:
                logger.warning(f"Помилка валідації рекомендації: {e}")
                continue
        
        # Сортуємо за впевненістю
        valid_recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return valid_recommendations[:Config.MAX_RECOMMENDATIONS]

    def _generate_fallback_recommendations(self, currency_impact, language):
        """Резервні рекомендації на основі простих правил"""
        logger.info("Генерація резервних рекомендацій...")
        
        recommendations = []
        
        # Аналізуємо вплив на валюти
        for currency, data in currency_impact.items():
            score = data['sentiment_score']
            
            if score >= 0.7:
                action = 'BUY'
                confidence = min(0.9, score)
                reason_uk = f"Позитивний вплив новин ({data['positive_news']} позитивних)"
                reason_ru = f"Позитивное влияние новостей ({data['positive_news']} позитивных)"
            elif score >= 0.6:
                action = 'BUY'
                confidence = score
                reason_uk = f"Переважно позитивний вплив новин"
                reason_ru = f"Преимущественно позитивное влияние новостей"
            elif score <= 0.4:
                action = 'AVOID'
                confidence = 1 - score
                reason_uk = f"Негативний вплив новин ({data['negative_news']} негативних)"
                reason_ru = f"Негативное влияние новостей ({data['negative_news']} негативных)"
            elif score <= 0.3:
                action = 'STRONG_AVOID'
                confidence = 1 - score
                reason_uk = f"Сильний негативний вплив новин"
                reason_ru = f"Сильное негативное влияние новостей"
            else:
                continue  # Пропускаємо нейтральні
            
            reason = reason_uk if language == 'uk' else reason_ru
            
            recommendations.append({
                'asset': currency,
                'action': action,
                'confidence': round(confidence, 3),
                'reason': reason,
                'timeframe': '1-2 дні' if language == 'uk' else '1-2 дня',
                'risk_level': 'medium',
                'id': f"{currency}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'generated_at': Config.get_kyiv_time().isoformat()
            })
        
        # Сортуємо за впевненістю
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return recommendations[:5]
