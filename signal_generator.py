import asyncio
import os
import uvicorn
from data_manager import RealTimeData
from feature_engineer import FeatureEngineer
from model_ensemble import HybridModel
from telegram_bot import send_signal
from config import *

class SignalGenerator:
    def __init__(self):
        self.data_manager = RealTimeData()
        self.feature_engineer = FeatureEngineer()
        self.model = HybridModel()
        self.active = True
    
    async def start(self):
        print("🚀 Starting QuotexSignalNet v1.0")
        
        # Инициализация менеджера данных
        asyncio.create_task(self.data_manager.start())
        
        # Инициализация генератора сигналов
        generator = SignalGenerator()
        await generator.start()

if __name__ == "__main__":
    # Конфигурация для запуска
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Запуск сервера на {host}:{port}")
    
    # Для разработки
    if os.getenv("ENVIRONMENT") == "development":
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    else:
        # Для продакшена
        uvicorn.run(
            "app",
            host=host,
            port=port,
            log_level="info"
        )
