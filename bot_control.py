"""
Модуль управления состоянием торгового бота
Координация всех компонентов системы
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import signal
import sys

from core import TradingCore
from telegram_bot import TelegramBotHandler
from database import Database

logger = logging.getLogger(__name__)

class BotController:
    def __init__(self, trading_core, telegram_bot):
        self.core = trading_core
        self.telegram = telegram_bot
        self.is_active = False
        self.start_time = None
        self.last_signal_time = None
        self.signals_sent_today = 0
        self.signals_sent_hour = 0
        self.hour_reset_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        # Статистика
        self.total_cycles = 0
        self.successful_cycles = 0
        self.errors_count = 0
        
        # Безопасность
        self.emergency_stop = False
        self.max_errors_per_hour = 20
        self.errors_this_hour = 0
        self.error_reset_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        # Регистрация глобального контроллера
        import globals
        globals.bot_controller = self
        
    async def start_trading(self):
        """Запуск торговли"""
        try:
            if self.is_active:
                logger.warning("⚠️ Торговля уже активна")
                return
                
            logger.info("🚀 Запуск торговой системы...")
            
            # Проверка готовности всех компонентов
            if not await self._check_system_readiness():
                logger.error("❌ Система не готова к торговле")
                return
                
            # Установка флагов
            self.is_active = True
            self.start_time = datetime.now()
            
            # Сброс счетчиков
            self._reset_counters()
            
            # Отправка уведомления
            await self.telegram.send_message(
                "🟢 **ТОРГОВЛЯ НАЧАТА**\n\n"
                f"⏰ Время запуска: {self.start_time.strftime('%H:%M:%S')}\n"
                f"🎯 Стратегия: Quantum Precision V2\n"
                f"📊 Пар: {len(self.core.pairs)}\n"
                f"⏱️ Таймфреймы: {len(self.core.timeframes)}\n\n"
                "Начинаю поиск торговых сигналов..."
            )
            
            # Запуск основного цикла
            await self._main_trading_loop()
            
        except Exception as e:
            logger.error(f"Ошибка запуска торговли: {e}")
            await self.telegram.send_error("BotController", str(e))
            
    async def stop_trading(self):
        """Остановка торговли"""
        try:
            if not self.is_active:
                logger.warning("⚠️ Торговля не активна")
                return
                
            logger.info("🛑 Остановка торговой системы...")
            
            # Установка флагов
            self.is_active = False
            
            # Отправка уведомления
            uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            
            await self.telegram.send_message(
                "🔴 **ТОРГОВЛЯ ОСТАНОВЛЕНА**\n\n"
                f"⏰ Время работы: {str(uptime).split('.')[0]}\n"
                f"📊 Циклов выполнено: {self.total_cycles}\n"
                f"✅ Успешных циклов: {self.successful_cycles}\n"
                f"📈 Сignalов отправлено: {self.signals_sent_today}\n"
                f"❌ Ошибок: {self.errors_count}\n\n"
                "Торговая система остановлена."
            )
            
            logger.info("✅ Торговля остановлена")
            
        except Exception as e:
            logger.error(f"Ошибка остановки торговли: {e}")
            
    async def _check_system_readiness(self) -> bool:
        """Проверка готовности всех компонентов системы"""
        try:
            logger.info("🔍 Проверка готовности системы...")
            
            # Проверка торгового ядра
            if not self.core:
                logger.error("❌ Торговое ядро не инициализировано")
                return False
                
            # Проверка Telegram бота
            if not self.telegram:
                logger.error("❌ Telegram бот не инициализирован")
                return False
                
            # Проверка WebSocket соединений
            if not self.core.websocket or not self.core.websocket.connections:
                logger.warning("⚠️ WebSocket соединения в демонстрационном режиме")
                # Для демонстрации разрешаем продолжить
                
            # Проверка рыночных данных
            market_data = self.core.websocket.get_market_data()
            if not market_data:
                logger.error("❌ Рыночные данные недоступны")
                return False
                
            # Проверка минимального количества данных
            data_check_passed = True
            for pair in self.core.pairs:
                for timeframe in self.core.timeframes:
                    if pair in market_data and timeframe in market_data[pair]:
                        df = market_data[pair][timeframe]
                        if len(df) < 100:  # Минимум 100 свечей
                            logger.warning(f"⚠️ Недостаточно данных для {pair} {timeframe}: {len(df)}")
                            data_check_passed = False
                            
            if not data_check_passed:
                logger.error("❌ Недостаточно исторических данных")
                return False
                
            logger.info("✅ Система готова к торговле")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки готовности: {e}")
            return False
            
    async def _main_trading_loop(self):
        """Основной цикл торговли"""
        try:
            logger.info("🔄 Запуск основного торгового цикла...")
            
            while self.is_active and not self.emergency_stop:
                cycle_start = datetime.now()
                
                try:
                    # Проверка лимитов безопасности
                    if not self._check_safety_limits():
                        logger.warning("⚠️ Превышены лимиты безопасности, пауза...")
                        await asyncio.sleep(300)  # 5 минут пауза
                        continue
                        
                    # Получение рыночных данных
                    market_data = self.core.websocket.get_market_data()
                    
                    if not market_data:
                        logger.warning("⚠️ Рыночные данные недоступны")
                        await asyncio.sleep(10)
                        continue
                        
                    # Анализ рынка и поиск сигналов
                    signals = await self.core.signal_analyzer.analyze_all_pairs(market_data)
                    
                    # Обработка найденных сигналов
                    if signals:
                        await self._process_signals(signals)
                        
                    # Обновление статистики
                    self.total_cycles += 1
                    self.successful_cycles += 1
                    
                    # Логирование прогресса
                    if self.total_cycles % 100 == 0:
                        await self._log_progress()
                        
                    # Сброс счетчиков по времени
                    self._reset_time_based_counters()
                    
                except Exception as e:
                    logger.error(f"Ошибка в торговом цикле: {e}")
                    self.errors_count += 1
                    self.errors_this_hour += 1
                    
                    await self.telegram.send_error("TradingLoop", str(e))
                    
                finally:
                    # Пауза между циклами
                    await self._wait_next_cycle(cycle_start)
                    
        except Exception as e:
            logger.error(f"Критическая ошибка в основном цикле: {e}")
            await self.telegram.send_error("MainLoop", str(e))
        finally:
            logger.info("🔄 Основной торговый цикл завершен")
            
    async def _process_signals(self, signals: List[Dict[str, Any]]):
        """Обработка найденных сигналов"""
        try:
            logger.info(f"📊 Обработка {len(signals)} сигналов...")
            
            for signal in signals:
                try:
                    # Валидация сигнала
                    if not await self._validate_signal(signal):
                        continue
                        
                    # Проверка лимитов
                    if not self._check_signal_limits():
                        logger.warning("⚠️ Превышены лимиты сигналов")
                        break
                        
                    # Отправка сигнала
                    success = await self.telegram.send_signal(signal)
                    
                    if success:
                        # Сохранение в базу данных
                        signal_id = await self.core.database.save_signal(signal)
                        
                        # Обновление счетчиков
                        self.signals_sent_today += 1
                        self.signals_sent_hour += 1
                        self.last_signal_time = datetime.now()
                        
                        # Обновление глобальной статистики
                        import globals
                        globals.performance_stats['total_signals'] += 1
                        globals.performance_stats['daily_signals'] += 1
                        globals.performance_stats['hourly_signals'] += 1
                        
                        logger.info(f"✅ Сignal отправлен: {signal['pair']} {signal['timeframe']}")
                        
                    else:
                        logger.error(f"❌ Ошибка отправки сигнала: {signal['pair']} {signal['timeframe']}")
                        
                except Exception as e:
                    logger.error(f"Ошибка обработки сигнала: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Ошибка обработки сигналов: {e}")
            
    async def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Валидация сигнала"""
        try:
            # Проверка обязательных полей
            required_fields = ['pair', 'timeframe', 'direction', 'accuracy', 'entry_time']
            for field in required_fields:
                if field not in signal:
                    logger.warning(f"⚠️ Отсутствует поле {field} в сигнале")
                    return False
                    
            # Проверка точности
            if signal['accuracy'] < 85:  # Уровень точности
                logger.debug(f"📊 Сignal не прошел проверку точности: {signal['accuracy']}%")
                return False
                
            # Проверка интервала между сигналами
            if self.last_signal_time:
                time_diff = (datetime.now() - self.last_signal_time).total_seconds()
                if time_diff < 60:  # Минимальный интервал 60 секунд
                    logger.debug(f"⏱️ Слишком частые сигналы: {time_diff}s")
                    return False
                    
            # Дополнительная валидация через анализатор
            return await self.core.signal_analyzer.validate_signal_quality(signal)
            
        except Exception as e:
            logger.error(f"Ошибка валидации сигнала: {e}")
            return False
            
    def _check_signal_limits(self) -> bool:
        """Проверка лимитов сигналов"""
        try:
            # Проверка часового лимита
            if self.signals_sent_hour >= 5:  # Максимум 5 сигналов в час
                logger.warning(f"⚠️ Превышен часовой лимит сигналов: {self.signals_sent_hour}")
                return False

            # Проверка дневного лимита
            if self.signals_sent_today >= 40:  # Максимум 40 сигналов в день
                logger.warning(f"⚠️ Превышен дневной лимит сигналов: {self.signals_sent_today}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки лимитов: {e}")
            return False
            
    def _check_safety_limits(self) -> bool:
        """Проверка лимитов безопасности"""
        try:
            # Проверка количества ошибок в час
            if self.errors_this_hour >= self.max_errors_per_hour:
                logger.warning(f"⚠️ Превышен лимит ошибок в час: {self.errors_this_hour}")
                return False
                
            # Проверка аварийной остановки
            if self.emergency_stop:
                logger.warning("⚠️ Активна аварийная остановка")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки безопасности: {e}")
            return False
            
    def _reset_time_based_counters(self):
        """Сброс счетчиков по времени"""
        try:
            current_time = datetime.now()
            
            # Сброс часового счетчика
            if current_time >= self.hour_reset_time + timedelta(hours=1):
                self.signals_sent_hour = 0
                self.hour_reset_time = current_time.replace(minute=0, second=0, microsecond=0)
                
            # Сброс счетчика ошибок
            if current_time >= self.error_reset_time + timedelta(hours=1):
                self.errors_this_hour = 0
                self.error_reset_time = current_time.replace(minute=0, second=0, microsecond=0)
                
            # Сброс дневного счетчика
            if current_time.date() != self.start_time.date():
                self.signals_sent_today = 0
                
        except Exception as e:
            logger.error(f"Ошибка сброса счетчиков: {e}")
            
    async def _wait_next_cycle(self, cycle_start: datetime):
        """Ожидание следующего цикла"""
        try:
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            wait_time = max(0, 10 - cycle_duration)  # Интервал между циклами 10 секунд
            
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                
        except Exception as e:
            logger.error(f"Ошибка ожидания цикла: {e}")
            await asyncio.sleep(10)
            
    async def _log_progress(self):
        """Логирование прогресса"""
        try:
            uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            success_rate = (self.successful_cycles / self.total_cycles * 100) if self.total_cycles > 0 else 0
            
            logger.info(
                f"📊 Прогресс: {self.total_cycles} циклов, "
                f"{success_rate:.1f}% успешных, "
                f"{self.signals_sent_today} сигналов сегодня, "
                f"работает {str(uptime).split('.')[0]}"
            )
            
        except Exception as e:
            logger.error(f"Ошибка логирования прогресса: {e}")
            
    def _reset_counters(self):
        """Сброс всех счетчиков"""
        try:
            self.total_cycles = 0
            self.successful_cycles = 0
            self.errors_count = 0
            self.signals_sent_today = 0
            self.signals_sent_hour = 0
            self.errors_this_hour = 0
            
        except Exception as e:
            logger.error(f"Ошибка сброса счетчиков: {e}")
            
    def is_trading_active(self) -> bool:
        """Проверка активности торговли"""
        return self.is_active and not self.emergency_stop
        
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса контроллера"""
        try:
            uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            return {
                'is_active': self.is_active,
                'emergency_stop': self.emergency_stop,
                'uptime': str(uptime).split('.')[0],
                'total_cycles': self.total_cycles,
                'successful_cycles': self.successful_cycles,
                'success_rate': (self.successful_cycles / self.total_cycles * 100) if self.total_cycles > 0 else 0,
                'signals_sent_today': self.signals_sent_today,
                'signals_sent_hour': self.signals_sent_hour,
                'errors_count': self.errors_count,
                'errors_this_hour': self.errors_this_hour,
                'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time else None
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return {}
            
    async def emergency_shutdown(self, reason: str = "Unknown"):
        """Аварийное отключение"""
        try:
            logger.critical(f"🚨 АВАРИЙНОЕ ОТКЛЮЧЕНИЕ: {reason}")
            
            self.emergency_stop = True
            self.is_active = False
            
            # Отправка уведомления
            await self.telegram.send_message(
                f"🚨 **АВАРИЙНОЕ ОТКЛЮЧЕНИЕ**\n\n"
                f"⚠️ Причина: {reason}\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
                "Система остановлена для безопасности."
            )
            
            # Остановка всех компонентов
            await self.core.shutdown()
            
        except Exception as e:
            logger.error(f"Ошибка аварийного отключения: {e}")
            
    def setup_signal_handlers(self):
        """Настройка обработчиков системных сигналов"""
        try:
            def signal_handler(signum, frame):
                logger.info(f"Получен сигнал {signum}")
                asyncio.create_task(self.emergency_shutdown(f"System signal {signum}"))
                
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
        except Exception as e:
            logger.error(f"Ошибка настройки обработчиков сигналов: {e}")

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
  
