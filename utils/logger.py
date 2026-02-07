import logging
import os
from datetime import datetime
from pathlib import Path

class Logger:
    def __init__(self, name="macroeconomic_bot", log_dir="logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Створюємо папку для логів
        log_path = Path(__file__).parent.parent / log_dir
        log_path.mkdir(exist_ok=True)
        
        # Файловий handler
        log_file = log_path / f"{datetime.now().strftime('%Y%m%d')}.log"
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
        
        # Видаляємо існуючі handler, щоб уникнути дублювання
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def get_logger(self):
        return self.logger

# Глобальний логер для всієї системи
logger_instance = Logger()
logger = logger_instance.get_logger()
