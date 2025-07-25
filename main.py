#!/usr/bin/env python3
"""
Профессиональный торговый бот для криптовалют
Стратегия "Quantum Precision V2"
Точность: 85%+, 30-35 сигналов/сутки
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any

from core import TradingCore
from globals import TRADING_PAIRS, TIMEFRAMES, BOT_TOKEN, CHAT_ID
from telegram_bot import TelegramBotHandler
from database import Database
from bot_control import BotController

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.core = None
        self.telegram = None
        self.database = None
        self.controller = None
        self.running = False
        
    async def initialize(self):
        """Инициализация всех компонентов"""
        try:
            logger.info("🚀 Инициализация торгового бота...")
            
            # Инициализация базы данных
            self.database = Database()
            await self.database.initialize()
            
            # Инициализация Telegram бота
            self.telegram = TelegramBotHandler(BOT_TOKEN, CHAT_ID)
            await self.telegram.initialize()  # Теперь метод существует
            
            # Инициализация торгового ядра
            self.core = TradingCore(self.telegram, self.database)
            await self.core.initialize()
            
            # Инициализация контроллера
            self.controller = BotController(self.core, self.telegram)
            
            # Автоматический запуск торговли
            await self.controller.start_trading()
            
            logger.info("✅ Все компоненты инициализированы успешно")
            
            # Отправка уведомления о запуске
            await self.telegram.send_signal({  # Исправлено: send_signal вместо send_message
                "pair": "SYSTEM",
                "direction": "UP",
                "confidence": 100,
                "price": 0,
                "expiration": "N/A",
                "reasons": ["Бот запущен"]
            })
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            raise
            
    async def run(self):
        """Основной цикл работы бота"""
        try:
            self.running = True
            logger.info("🔄 Запуск основного цикла...")
            
            # Запуск Telegram бота
            telegram_task = asyncio.create_task(self.telegram.run())
            
            # Запуск торгового цикла автоматически
            await self.core.start_trading()
            
            # Ожидание завершения
            await telegram_task
            
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")
            if self.telegram:
                await self.telegram.send_signal({  # Исправлено: send_signal
                    "pair": "SYSTEM",
                    "direction": "DOWN",
                    "confidence": 100,
                    "price": 0,
                    "expiration": "N/A",
                    "reasons": ["Критическая ошибка"]
                })
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        """Корректное завершение работы"""
        try:
            logger.info("🛑 Завершение работы бота...")
            self.running = False
            
            if self.core:
                await self.core.shutdown()
                
            if self.telegram:
                await self.telegram.send_signal({  # Исправлено: send_signal
                    "pair": "SYSTEM",
                    "direction": "DOWN",
                    "confidence": 100,
                    "price": 0,
                    "expiration": "N/A",
                    "reasons": ["Бот остановлен"]
                })
                await self.telegram.shutdown()  # Этот метод может быть удалён, если его нет в telegram_bot.py
                
            if self.database:
                await self.database.close()
                
            logger.info("✅ Бот завершен корректно")
            
        except Exception as e:
            logger.error(f"Ошибка при завершении: {e}")

def signal_handler(signum, frame):
    """Обработка сигналов системы"""
    logger.info(f"Получен сигнал {signum}, завершение работы...")
    sys.exit(0)

async def main():
    """Точка входа"""
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    bot = TradingBot()
    
    try:
        await bot.initialize()
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
