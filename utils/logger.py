
import logging
import os
from datetime import datetime

class Logger:
    def __init__(self, name="signal_bot", log_dir="logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Створюємо папку для логів
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Файловий handler
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Консольний handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Форматер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def debug(self, message):
        self.logger.debug(message)

# Глобальний логер
logger = Logger().logger
