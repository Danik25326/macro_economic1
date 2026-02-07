
import json
from datetime import datetime, timedelta
import pytz

class Helpers:
    @staticmethod
    def format_candles_for_ai(candles):
        """Форматує свічки для AI аналізу"""
        if not candles:
            return "Немає даних"
        
        formatted = []
        for i, candle in enumerate(candles[-20:]):  # Беремо останні 20 свічок
            time = candle.timestamp.strftime('%H:%M')
            formatted.append(
                f"{i+1}. {time} | O:{candle.open:.5f} H:{candle.high:.5f} "
                f"L:{candle.low:.5f} C:{candle.close:.5f}"
            )
        return "\n".join(formatted)
    
    @staticmethod
    def calculate_indicators(candles):
        """Розрахунок простих технічних індикаторів"""
        if len(candles) < 10:
            return {}
        
        closes = [c.close for c in candles]
        
        # Проста середня (SMA)
        sma_5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else 0
        sma_10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else 0
        
        # Визначення тренду
        trend = "NEUTRAL"
        if sma_5 > sma_10:
            trend = "UP"
        elif sma_5 < sma_10:
            trend = "DOWN"
        
        # Волатильність
        recent_closes = closes[-10:]
        volatility = max(recent_closes) - min(recent_closes) if recent_closes else 0
        
        return {
            "sma_5": sma_5,
            "sma_10": sma_10,
            "trend": trend,
            "volatility": volatility,
            "current_price": closes[-1] if closes else 0
        }
    
    @staticmethod
    def get_ukraine_time():
        """Отримання поточного часу в Україні"""
        ukraine_tz = pytz.timezone('Europe/Kiev')
        return datetime.now(ukraine_tz)
    
    @staticmethod
    def time_until_next_signal():
        """Час до наступного сигналу"""
        now = Helpers.get_ukraine_time()
        next_run = now + timedelta(minutes=5 - (now.minute % 5))
        return (next_run - now).seconds
    
    @staticmethod
    def create_signal_id(asset, timestamp):
        """Створення унікального ID для сигналу"""
        time_str = timestamp.strftime('%Y%m%d%H%M')
        return f"{asset}_{time_str}"
