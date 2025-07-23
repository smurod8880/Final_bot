#!/usr/bin/env python3
"""
Демонстрационная версия торгового бота
Генерирует сигналы для демонстрации работы
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random

from telegram_bot import TelegramBotHandler
from globals import BOT_TOKEN, CHAT_ID, TRADING_PAIRS, TIMEFRAMES, MESSAGE_FORMATS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('demo_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DemoTradingBot:
    def __init__(self):
        self.telegram = TelegramBotHandler(BOT_TOKEN, CHAT_ID)
        self.is_running = False
        self.signals_sent = 0
        self.start_time = None
        
    async def initialize(self):
        """Инициализация демо-бота"""
        try:
            logger.info("🚀 Инициализация демо-бота...")
            
            # Инициализация Telegram
            await self.telegram.initialize()
            
            # Стартовое сообщение
            await self.telegram.send_message(
                "🤖 Quantum Precision V2 (DEMO)\n\n"
                "📊 Демонстрация работы торгового бота\n"
                "🎯 Точность: 90%+\n"
                "📈 Будет генерировать сигналы для демонстрации\n\n"
                "🟢 Система запущена!"
            )
            
            logger.info("✅ Демо-бот инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            raise
            
    async def run(self):
        """Запуск демо-бота"""
        try:
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info("🔄 Запуск демонстрационного цикла...")
            
            while self.is_running:
                try:
                    # Генерация демонстрационного сигнала
                    signal = self._generate_demo_signal()
                    
                    # Отправка сигнала
                    await self.telegram.send_signal(signal)
                    
                    self.signals_sent += 1
                    
                    logger.info(f"✅ Отправлен демо-сигнал #{self.signals_sent}: {signal['pair']} {signal['timeframe']}")
                    
                    # Статистика каждые 10 сигналов
                    if self.signals_sent % 10 == 0:
                        await self._send_statistics()
                    
                    # Пауза между сигналами (30-60 секунд)
                    await asyncio.sleep(random.randint(30, 60))
                    
                except Exception as e:
                    logger.error(f"Ошибка в демо-цикле: {e}")
                    await asyncio.sleep(30)
                    
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
        finally:
            await self.shutdown()
            
    def _generate_demo_signal(self) -> Dict[str, Any]:
        """Генерация демонстрационного сигнала"""
        try:
            # Случайный выбор пары и таймфрейма
            pair = random.choice(TRADING_PAIRS)
            timeframe = random.choice(TIMEFRAMES)
            
            # Случайные параметры в реалистичных диапазонах
            accuracy = random.uniform(87.5, 98.5)
            direction = random.choice(["BUY", "SELL"])
            
            # Время удержания в зависимости от таймфрейма
            hold_durations = {
                "1m": random.randint(5, 15),
                "5m": random.randint(15, 45),
                "15m": random.randint(30, 90),
                "30m": random.randint(60, 180),
                "1h": random.randint(120, 300),
                "4h": random.randint(240, 600),
                "1d": random.randint(480, 1440)
            }
            
            hold_duration = hold_durations.get(timeframe, 60)
            
            # Реалистичные значения индикаторов
            vwap_gradient = random.uniform(0.001, 0.005)
            volume_tsunami = random.uniform(2.5, 5.0)
            neural_macd = random.uniform(0.05, 0.25)
            quantum_rsi = random.uniform(35, 65)
            ai_score = random.uniform(85, 95)
            
            # Создание сигнала
            signal = {
                'pair': pair,
                'timeframe': timeframe,
                'accuracy': round(accuracy, 1),
                'entry_time': datetime.now().strftime('%H:%M:%S'),
                'hold_duration': hold_duration,
                'vwap_gradient': round(vwap_gradient, 4),
                'volume_tsunami': round(volume_tsunami, 1),
                'neural_macd': round(neural_macd, 2),
                'quantum_rsi': round(quantum_rsi, 1),
                'ai_score': round(ai_score, 1),
                'direction': direction
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Ошибка генерации сигнала: {e}")
            return self._get_fallback_signal()
            
    def _get_fallback_signal(self) -> Dict[str, Any]:
        """Запасной сигнал"""
        return {
            'pair': 'BTCUSDT',
            'timeframe': '1h',
            'accuracy': 90.0,
            'entry_time': datetime.now().strftime('%H:%M:%S'),
            'hold_duration': 120,
            'vwap_gradient': 0.0025,
            'volume_tsunami': 3.5,
            'neural_macd': 0.15,
            'quantum_rsi': 45.0,
            'ai_score': 92.0,
            'direction': 'BUY'
        }
        
    async def _send_statistics(self):
        """Отправка статистики"""
        try:
            uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            
            stats_message = f"""
📊 СТАТИСТИКА ДЕМО-БОТА

🎯 Сигналов отправлено: {self.signals_sent}
⏰ Время работы: {str(uptime).split('.')[0]}
📈 Средняя точность: 92.5%
🟢 Успешных сделок: {int(self.signals_sent * 0.925)}
🔴 Неудачных сделок: {int(self.signals_sent * 0.075)}

🔥 Лучшие пары сегодня:
• BTC/USDT: 94.2% (5 сигналов)
• ETH/USDT: 91.8% (4 сигнала)
• SOL/USDT: 96.1% (3 сигнала)

💡 Система работает стабильно!
            """
            
            await self.telegram.send_message(stats_message)
            
        except Exception as e:
            logger.error(f"Ошибка отправки статистики: {e}")
            
    async def shutdown(self):
        """Корректное завершение работы"""
        try:
            logger.info("🛑 Завершение работы демо-бота...")
            
            self.is_running = False
            
            if self.telegram:
                await self.telegram.send_message(
                    f"🛑 **Демо-бот остановлен**\n\n"
                    f"📊 Всего сигналов: {self.signals_sent}\n"
                    f"⏰ Время работы: {str(datetime.now() - self.start_time).split('.')[0] if self.start_time else 'N/A'}\n\n"
                    "Спасибо за использование Quantum Precision V2!"
                )
                
            logger.info("✅ Демо-бот завершен корректно")
            
        except Exception as e:
            logger.error(f"Ошибка завершения: {e}")

async def main():
    """Точка входа"""
    bot = DemoTradingBot()
    
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
