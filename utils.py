"""
Утилитные функции
"""

import logging
import time
import asyncio

logger = logging.getLogger(__name__)

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('trading_bot.log'),
            logging.StreamHandler()
        ]
    )

async def async_sleep(seconds: float):
    """Асинхронная задержка"""
    await asyncio.sleep(seconds)
  
