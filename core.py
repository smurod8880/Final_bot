"""
Основной модуль торгового ядра
Инициализация и координация всех компонентов
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

from globals import TRADING_PAIRS, TIMEFRAMES, STRATEGY_CONFIG
from database import Database
from websocket import BinanceWebSocket
from signal_analyzer import SignalAnalyzer
from ai_model import AIPredictor

logger = logging.getLogger(__name__)

class TradingCore:
    def __init__(self, telegram_bot, database):
        self.telegram = telegram_bot
        self.database = database
        
        # Компоненты системы
        self.websocket = None
        self.signal_analyzer = None
        self.ai_predictor = None
        
        # Настройки
        self.pairs = TRADING_PAIRS
        self.timeframes = TIMEFRAMES
        self.config = STRATEGY_CONFIG
        
        # Состояние
        self.is_initialized = False
        self.is_running = False
        self.initialization_time = None
        
        # Статистика
        self.total_analysis_cycles = 0
        self.successful_analysis_cycles = 0
        self.total_signals_generated = 0
        
    async def initialize(self):
        """Инициализация торгового ядра"""
        try:
            logger.info("🔧 Инициализация торгового ядра...")
            
            # Инициализация WebSocket
            await self._initialize_websocket()
            
            # Инициализация анализатора сигналов
            await self._initialize_signal_analyzer()
            
            # Инициализация AI предсказателя
            await self._initialize_ai_predictor()
            
            # Финальная проверка
            if not await self._validate_initialization():
                raise Exception("Не удалось завершить инициализацию")
                
            self.is_initialized = True
            self.initialization_time = datetime.now()
            
            logger.info("✅ Торговое ядро инициализировано успешно")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации торгового ядра: {e}")
            raise
            
    async def _initialize_websocket(self):
        """Инициализация WebSocket соединения"""
        try:
            logger.info("🔌 Инициализация WebSocket...")
            
            self.websocket = BinanceWebSocket()
            await self.websocket.initialize()
            
            logger.info("✅ WebSocket инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации WebSocket: {e}")
            raise
            
    async def _initialize_signal_analyzer(self):
        """Инициализация анализатора сигналов"""
        try:
            logger.info("🔍 Инициализация анализатора сигналов...")
            
            self.signal_analyzer = SignalAnalyzer(self.telegram, self.database)
            
            logger.info("✅ Анализатор сигналов инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации анализатора сигналов: {e}")
            raise
            
    async def _initialize_ai_predictor(self):
        """Инициализация AI предсказателя"""
        try:
            logger.info("🤖 Инициализация AI предсказателя...")
            
            self.ai_predictor = AIPredictor()
            
            # Попытка загрузки сохраненной модели
            try:
                model_path = "trading_model.json"
                self.ai_predictor.load_model(model_path)
                logger.info("📁 Модель загружена из файла")
            except Exception as e:
                logger.warning("🆕 Используется новая модель")
                
            logger.info("✅ AI предсказатель инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации AI предсказателя: {e}")
            raise
            
    async def _validate_initialization(self) -> bool:
        """Валидация инициализации"""
        try:
            logger.info("✅ Проверка инициализации...")
            
            # Проверка WebSocket
            if not self.websocket:
                logger.error("❌ WebSocket не инициализирован")
                return False
                
            # Проверка анализатора
            if not self.signal_analyzer:
                logger.error("❌ Анализатор сигналов не инициализирован")
                return False
                
            # Проверка AI предсказателя
            if not self.ai_predictor:
                logger.error("❌ AI предсказатель не инициализирован")
                return False
                
            # Проверка данных
            await asyncio.sleep(2)  # Даем время для получения данных
            
            market_data = self.websocket.get_market_data()
            if not market_data:
                logger.error("❌ Рыночные данные не получены")
                return False
                
            # Проверка минимального количества данных
            data_ok = True
            for pair in self.pairs[:2]:  # Проверяем первые 2 пары
                for timeframe in self.timeframes[:2]:  # Проверяем первые 2 таймфрейма
                    if pair in market_data and timeframe in market_data[pair]:
                        df = market_data[pair][timeframe]
                        if len(df) < 50:
                            logger.warning(f"⚠️ Мало данных для {pair} {timeframe}: {len(df)}")
                            data_ok = False
                            
            if not data_ok:
                logger.warning("⚠️ Недостаточно данных, но продолжаем...")
                
            logger.info("✅ Инициализация прошла успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка валидации инициализации: {e}")
            return False
            
    async def start_trading(self):
        """Запуск торговли"""
        try:
            if not self.is_initialized:
                logger.error("❌ Торговое ядро не инициализировано")
                return
                
            logger.info("🔄 Запуск торгового цикла...")
            
            # Запуск WebSocket потока данных
            websocket_task = asyncio.create_task(self.websocket.start_data_stream())
            
            # Запуск периодического переобучения AI
            ai_retrain_task = asyncio.create_task(self._ai_retrain_loop())
            
            # Запуск мониторинга производительности
            monitoring_task = asyncio.create_task(self._performance_monitoring_loop())
            
            self.is_running = True
            
            logger.info("✅ Торговля запущена")
            
            # Ожидание завершения задач
            await asyncio.gather(
                websocket_task,
                ai_retrain_task,
                monitoring_task,
                return_exceptions=True
            )
            
        except Exception as e:
            logger.error(f"Ошибка запуска торговли: {e}")
            raise
        finally:
            self.is_running = False
            
    async def _ai_retrain_loop(self):
        """Цикл переобучения AI модели"""
        try:
            logger.info("🔄 Запуск цикла переобучения AI...")
            
            while self.is_running:
                try:
                    # Ожидание интервала переобучения
                    await asyncio.sleep(3600)  # 1 час
                    
                    if not self.is_running:
                        break
                        
                    # Переобучение модели
                    await self.ai_predictor.retrain_model()
                    
                    # Сохранение модели
                    model_path = "trading_model.json"
                    self.ai_predictor.save_model(model_path)
                    
                    logger.info("🤖 AI модель переобучена и сохранена")
                    
                except Exception as e:
                    logger.error(f"Ошибка переобучения AI: {e}")
                    await asyncio.sleep(300)  # 5 минут пауза при ошибке
                    
        except Exception as e:
            logger.error(f"Ошибка цикла переобучения AI: {e}")
            
    async def _performance_monitoring_loop(self):
        """Цикл мониторинга производительности"""
        try:
            logger.info("📊 Запуск мониторинга производительности...")
            
            while self.is_running:
                try:
                    # Ожидание интервала мониторинга
                    await asyncio.sleep(1800)  # 30 минут
                    
                    if not self.is_running:
                        break
                        
                    # Получение статистики
                    stats = await self._collect_performance_stats()
                    
                    # Отправка статистики в Telegram
                    await self.telegram.send_daily_stats(stats)
                    
                    logger.info("📈 Отчет о производительности отправлен")
                    
                except Exception as e:
                    logger.error(f"Ошибка мониторинга производительности: {e}")
                    await asyncio.sleep(300)  # 5 минут пауза при ошибке
                    
        except Exception as e:
            logger.error(f"Ошибка цикла мониторинга: {e}")
            
    async def _collect_performance_stats(self) -> Dict[str, Any]:
        """Сбор статистики производительности"""
        try:
            # Статистика базы данных
            db_stats = await self.database.get_daily_stats()
            
            # Статистика WebSocket
            ws_stats = self.websocket.get_connection_status()
            
            # Статистика AI модели
            ai_stats = self.ai_predictor.get_model_performance()
            
            # Статистика торгового ядра
            core_stats = {
                'total_analysis_cycles': self.total_analysis_cycles,
                'successful_analysis_cycles': self.successful_analysis_cycles,
                'success_rate': (self.successful_analysis_cycles / self.total_analysis_cycles * 100) if self.total_analysis_cycles > 0 else 0,
                'total_signals_generated': self.total_signals_generated,
                'uptime': (datetime.now() - self.initialization_time).total_seconds() if self.initialization_time else 0
            }
            
            return {
                'database': db_stats,
                'websocket': ws_stats,
                'ai_model': ai_stats,
                'core': core_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка сбора статистики: {e}")
            return {}
            
    async def analyze_market_and_generate_signals(self, market_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Анализ рынка и генерация сигналов"""
        try:
            self.total_analysis_cycles += 1
            
            # Анализ через анализатор сигналов
            signals = await self.signal_analyzer.analyze_all_pairs(market_data)
            
            if signals:
                self.total_signals_generated += len(signals)
                self.successful_analysis_cycles += 1
                
                logger.info(f"📊 Анализ завершен: найдено {len(signals)} сигналов")
            else:
                logger.debug("📊 Анализ завершен: сигналов не найдено")
                
            return signals
            
        except Exception as e:
            logger.error(f"Ошибка анализа рынка: {e}")
            return []
            
    async def get_market_data(self) -> Dict[str, Dict[str, Any]]:
        """Получение рыночных данных"""
        try:
            if not self.websocket:
                logger.error("❌ WebSocket не инициализирован")
                return {}
                
            return self.websocket.get_market_data()
            
        except Exception as e:
            logger.error(f"Ошибка получения рыночных данных: {e}")
            return {}
            
    async def get_latest_price(self, pair: str) -> Optional[float]:
        """Получение последней цены для пары"""
        try:
            if not self.websocket:
                return None
                
            return self.websocket.get_latest_price(pair)
            
        except Exception as e:
            logger.error(f"Ошибка получения цены {pair}: {e}")
            return None
            
    async def shutdown(self):
        """Корректное завершение работы"""
        try:
            logger.info("🛑 Завершение работы торгового ядра...")
            
            self.is_running = False
            
            # Завершение WebSocket
            if self.websocket:
                await self.websocket.shutdown()
                
            # Сохранение AI модели
            if self.ai_predictor:
                try:
                    model_path = "trading_model.json"
                    self.ai_predictor.save_model(model_path)
                    logger.info("💾 AI модель сохранена")
                except Exception as e:
                    logger.error(f"Ошибка сохранения AI модели: {e}")
                    
            logger.info("✅ Торговое ядро завершено")
            
        except Exception as e:
            logger.error(f"Ошибка завершения торгового ядра: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса торгового ядра"""
        try:
            uptime = (datetime.now() - self.initialization_time).total_seconds() if self.initialization_time else 0
            
            return {
                'is_initialized': self.is_initialized,
                'is_running': self.is_running,
                'uptime': uptime,
                'initialization_time': self.initialization_time.isoformat() if self.initialization_time else None,
                'total_analysis_cycles': self.total_analysis_cycles,
                'successful_analysis_cycles': self.successful_analysis_cycles,
                'success_rate': (self.successful_analysis_cycles / self.total_analysis_cycles * 100) if self.total_analysis_cycles > 0 else 0,
                'total_signals_generated': self.total_signals_generated,
                'pairs_count': len(self.pairs),
                'timeframes_count': len(self.timeframes),
                'websocket_status': self.websocket.get_connection_status() if self.websocket else {},
                'ai_model_performance': self.ai_predictor.get_model_performance() if self.ai_predictor else {}
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return {}
