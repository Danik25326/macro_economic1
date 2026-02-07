
import re
from datetime import datetime


class Validator:
    @staticmethod
    def validate_signal(signal):
        """Валідація сигналу"""
        required_fields = ['asset', 'direction', 'confidence', 'entry_time']
        
        # Перевірка наявності обов'язкових полів
        for field in required_fields:
            if field not in signal:
                return False, f"Missing required field: {field}"
        
        # Валідація активу
        if not Validator.validate_asset(signal['asset']):
            return False, f"Invalid asset: {signal['asset']}"
        
        # Валідація напрямку
        if signal['direction'] not in ['UP', 'DOWN']:
            return False, f"Invalid direction: {signal['direction']}"
        
        # Валідація впевненості
        if not 0 <= signal['confidence'] <= 1:
            return False, f"Invalid confidence: {signal['confidence']}"
        
        # Валідація часу
        if not Validator.validate_time(signal['entry_time']):
            return False, f"Invalid time format: {signal['entry_time']}"
        
        return True, "Signal is valid"
    
    @staticmethod
    def validate_asset(asset):
        """Валідація назви активу"""
        # Список допустимих активів (можна розширити)
        valid_assets = [
            'GBP/JPY_otc', 'EUR/USD_otc', 'USD/JPY_otc', 'EUR/JPY_otc',
            'GBP/USD_otc', 'AUD/USD_otc', 'USD/CAD_otc', 'NZD/USD_otc'
        ]
        return asset in valid_assets
    
    @staticmethod
    def validate_time(time_str):
        """Валідація формату часу HH:MM"""
        pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$'
        return bool(re.match(pattern, time_str))
    
    @staticmethod
    def validate_confidence(confidence, min_confidence=0.7):
        """Перевірка, чи проходить сигнал по впевненості"""
        return confidence >= min_confidence
