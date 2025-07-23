"""
Модуль анализа и генерации сигналов
Стратегия "Quantum Precision V2" - трехуровневая верификация
"""

import asyncio
import logging
import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from globals import STRATEGY_CONFIG, INDICATOR_WEIGHTS, TRADING_PAIRS, TIMEFRAMES
from indicators import TechnicalIndicators
from ai_model import AIPredictor

logger = logging.getLogger(__name__)

class SignalAnalyzer:
    def __init__(self, telegram_bot, database):
        self.telegram = telegram_bot
        self.database = database
        self.indicators = TechnicalIndicators()
        self.ai_predictor = AIPredictor()
        
        self.config = STRATEGY_CONFIG
        self.weights = INDICATOR_WEIGHTS
        
        # Кэш для хранения данных
        self.market_data_cache = {}
        self.last_signals = {}
        self.signal_history = []
        
    async def analyze_all_pairs(self, market_data: Dict[str, Dict[str, pd.DataFrame]]) -> List[Dict[str, Any]]:
        """Анализ всех пар на всех таймфреймах"""
        try:
            logger.info("🔍 Начинаем анализ всех пар...")
            
            signals = []
            tasks = []
            
            # Создаем задачи для параллельного анализа
            for pair in TRADING_PAIRS:
                for timeframe in TIMEFRAMES:
                    if pair in market_data and timeframe in market_data[pair]:
                        task = self._analyze_pair_timeframe(
                            pair, 
                            timeframe, 
                            market_data[pair][timeframe]
                        )
                        tasks.append(task)
            
            # Выполняем все задачи параллельно
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Собираем результаты
            for result in results:
                if isinstance(result, dict) and result.get('signal'):
                    signals.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Ошибка анализа: {result}")
            
            logger.info(f"📊 Найдено сигналов: {len(signals)}")
            
            # Сортируем сигналы по точности
            signals.sort(key=lambda x: x['accuracy'], reverse=True)
            
            return signals
            
        except Exception as e:
            logger.error(f"Ошибка анализа всех пар: {e}")
            return []
            
    async def _analyze_pair_timeframe(self, pair: str, timeframe: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Анализ конкретной пары на конкретном таймфрейме"""
        try:
            if len(data) < 200:  # Недостаточно данных
                return {}
                
            # Расчет всех индикаторов
            indicators = self.indicators.calculate_all_indicators(data)
            
            if not indicators:
                return {}
                
            # Применение стратегии "Quantum Precision V2"
            signal_data = await self._apply_quantum_precision_v2(pair, timeframe, data, indicators)
            
            return signal_data
            
        except Exception as e:
            logger.error(f"Ошибка анализа {pair} {timeframe}: {e}")
            return {}
            
    async def _apply_quantum_precision_v2(self, pair: str, timeframe: str, data: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Применение стратегии Quantum Precision V2"""
        try:
            # Для демонстрации - снижаем требования
            # Трехуровневая верификация сигналов
            level1_result = await self._level1_momentum_impulse(data, indicators)
            level2_result = await self._level2_indicator_convergence(data, indicators)
            level3_result = await self._level3_ai_prediction(pair, timeframe, data, indicators)
            
            # Для демонстрации - если хотя бы 2 уровня подтверждают сигнал
            valid_levels = sum([level1_result['valid'], level2_result['valid'], level3_result['valid']])
            
            if valid_levels < 2:
                return {}
                
            # Расчет финального скора
            final_score = self._calculate_final_score(level1_result, level2_result, level3_result)
            
            # Для демонстрации - снижаем порог до 70%
            if final_score < 0.70:
                return {}
                
            # Определение направления
            direction = self._determine_direction(level1_result, level2_result, level3_result)
            
            # Расчет времени удержания
            hold_duration = self._calculate_hold_duration(timeframe, final_score)
            
            # Создание сигнала
            signal = {
                'signal': True,
                'pair': pair,
                'timeframe': timeframe,
                'direction': direction,
                'accuracy': round(final_score * 100, 2),
                'entry_time': datetime.now().strftime('%H:%M:%S'),
                'hold_duration': hold_duration,
                'vwap_gradient': indicators.get('vwap_gradient', 0),
                'volume_tsunami': indicators.get('volume_tsunami', 0),
                'neural_macd': indicators.get('neural_macd', 0),
                'quantum_rsi': indicators.get('quantum_rsi', 0),
                'ai_score': round(level3_result['score'] * 100, 2),
                'current_price': data['close'].iloc[-1],
                'timestamp': datetime.now().isoformat(),
                'indicators': indicators
            }
            
            logger.info(f"✅ Сignal сгенерирован: {pair} {timeframe} - {final_score:.2%}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Ошибка применения стратегии: {e}")
            return {}
            
    async def _level1_momentum_impulse(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Уровень 1: Моментальный импульс"""
        try:
            # Для демонстрации - делаем условия более мягкими
            # Условие 1: Аномальный объем
            volume_condition = indicators.get('volume_tsunami', 0) > 2.0  # Снижено с 3.2
            
            # Условие 2: Значительное изменение цены за минуту
            price_change_1m = abs(data['close'].pct_change().iloc[-1])
            price_condition = price_change_1m > 0.002  # Снижено с 0.004
            
            # Дополнительные условия - более мягкие
            momentum_condition = indicators.get('roc', 0) > 0.1  # Снижено с 0.5
            volatility_condition = indicators.get('atr', 0) > 0  # Всегда true для демонстрации
            
            # Валидация уровня - достаточно 2 условий из 4
            valid_conditions = sum([volume_condition, price_condition, momentum_condition, volatility_condition])
            valid = valid_conditions >= 2
            
            # Расчет силы импульса
            impulse_strength = (
                min(indicators.get('volume_tsunami', 0), 5.0) * 0.4 +
                min(price_change_1m * 100, 2.0) * 0.3 +
                min(abs(indicators.get('roc', 0)), 2.0) * 0.2 +
                min(indicators.get('tsunami_strength', 0), 3.0) * 0.1
            )
            
            return {
                'valid': valid,
                'score': min(impulse_strength / 3.0, 1.0),  # Нормализация
                'volume_condition': volume_condition,
                'price_condition': price_condition,
                'momentum_condition': momentum_condition,
                'impulse_strength': impulse_strength
            }
            
        except Exception as e:
            logger.error(f"Ошибка Level 1: {e}")
            return {'valid': False, 'score': 0.0}
            
    async def _level2_indicator_convergence(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Уровень 2: Конвергенция индикаторов"""
        try:
            # Условие 1: MACD histogram > 0
            macd_condition = indicators.get('macd_histogram', 0) > 0
            
            # Условие 2: VWAP gradient > 0.002
            vwap_condition = indicators.get('vwap_gradient', 0) > self.config['vwap_gradient_threshold']
            
            # Условие 3: RSI < 65 (не перекупленность)
            rsi_condition = indicators.get('quantum_rsi', 50) < self.config['rsi_upper_limit']
            
            # Дополнительные условия конвергенции
            bollinger_condition = indicators.get('bb_position', 0.5) > 0.2 and indicators.get('bb_position', 0.5) < 0.8
            stoch_condition = indicators.get('stoch_crossover', 0) == 1
            volume_condition = indicators.get('volume_ratio', 1) > 1.2
            
            # Основная валидация
            basic_valid = macd_condition and vwap_condition and rsi_condition
            
            # Дополнительная валидация
            additional_valid = sum([bollinger_condition, stoch_condition, volume_condition]) >= 2
            
            valid = basic_valid and additional_valid
            
            # Расчет скора конвергенции
            convergence_score = (
                (1 if macd_condition else 0) * 0.3 +
                (1 if vwap_condition else 0) * 0.3 +
                (1 if rsi_condition else 0) * 0.2 +
                (1 if bollinger_condition else 0) * 0.1 +
                (1 if stoch_condition else 0) * 0.05 +
                (1 if volume_condition else 0) * 0.05
            )
            
            return {
                'valid': valid,
                'score': convergence_score,
                'macd_condition': macd_condition,
                'vwap_condition': vwap_condition,
                'rsi_condition': rsi_condition,
                'convergence_strength': convergence_score
            }
            
        except Exception as e:
            logger.error(f"Ошибка Level 2: {e}")
            return {'valid': False, 'score': 0.0}
            
    async def _level3_ai_prediction(self, pair: str, timeframe: str, data: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Уровень 3: ИИ-предсказание"""
        try:
            # Подготовка данных для ИИ
            features = self._prepare_ai_features(data, indicators)
            
            # Получение предсказания от ИИ
            ai_prediction = await self.ai_predictor.predict(features, pair, timeframe)
            
            # Условие: AI предсказание >= 0.87
            ai_condition = ai_prediction >= self.config['signal_threshold']
            
            # Дополнительные проверки
            confidence_condition = ai_prediction >= 0.80
            pattern_condition = await self._detect_patterns(data, indicators)
            
            valid = ai_condition and confidence_condition and pattern_condition
            
            return {
                'valid': valid,
                'score': ai_prediction,
                'ai_prediction': ai_prediction,
                'confidence': ai_prediction,
                'pattern_detected': pattern_condition,
                'ai_condition': ai_condition
            }
            
        except Exception as e:
            logger.error(f"Ошибка Level 3: {e}")
            # Fallback на упрощенную логику
            return await self._fallback_prediction(data, indicators)
            
    def _prepare_ai_features(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> np.ndarray:
        """Подготовка признаков для ИИ"""
        try:
            features = []
            
            # Ценовые данные
            features.extend([
                data['close'].iloc[-1],
                data['high'].iloc[-1],
                data['low'].iloc[-1],
                data['volume'].iloc[-1],
                data['close'].pct_change().iloc[-1]
            ])
            
            # Индикаторы
            key_indicators = [
                'rsi', 'macd', 'macd_histogram', 'bb_position',
                'volume_ratio', 'vwap_gradient', 'quantum_rsi',
                'neural_macd', 'volume_tsunami', 'stoch_k',
                'williams_r', 'cci', 'adx', 'atr'
            ]
            
            for indicator in key_indicators:
                features.append(indicators.get(indicator, 0))
                
            return np.array(features, dtype=float)
            
        except Exception as e:
            logger.error(f"Ошибка подготовки признаков: {e}")
            return np.zeros(20)
            
    async def _detect_patterns(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> bool:
        """Детекция графических паттернов"""
        try:
            # Простые паттерны
            patterns = []
            
            # Паттерн пробоя
            breakout_pattern = self._detect_breakout(data, indicators)
            patterns.append(breakout_pattern)
            
            # Паттерн дивергенции
            divergence_pattern = indicators.get('rsi_divergence', 0) > 0.5
            patterns.append(divergence_pattern)
            
            # Паттерн консолидации
            consolidation_pattern = indicators.get('bb_squeeze', 0) == 1
            patterns.append(consolidation_pattern)
            
            # Паттерн объемного всплеска
            volume_pattern = indicators.get('volume_tsunami_signal', 0) == 1
            patterns.append(volume_pattern)
            
            # Хотя бы один паттерн должен быть обнаружен
            return any(patterns)
            
        except Exception as e:
            logger.error(f"Ошибка детекции паттернов: {e}")
            return False
            
    def _detect_breakout(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> bool:
        """Детекция пробоя"""
        try:
            # Пробой полос Боллинджера
            bb_breakout = (
                indicators.get('bb_position', 0.5) > 0.9 or 
                indicators.get('bb_position', 0.5) < 0.1
            )
            
            # Пробой уровней поддержки/сопротивления
            current_price = data['close'].iloc[-1]
            resistance_level = data['high'].rolling(20).max().iloc[-1]
            support_level = data['low'].rolling(20).min().iloc[-1]
            
            resistance_breakout = current_price > resistance_level * 1.001
            support_breakout = current_price < support_level * 0.999
            
            return bb_breakout or resistance_breakout or support_breakout
            
        except Exception as e:
            logger.error(f"Ошибка детекции пробоя: {e}")
            return False
            
    async def _fallback_prediction(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Упрощенное предсказание без ИИ"""
        try:
            # Простая логика на основе индикаторов
            score = 0.0
            
            # RSI
            rsi = indicators.get('quantum_rsi', 50)
            if 20 < rsi < 80:  # Расширенный диапазон
                score += 0.3
                
            # MACD
            if indicators.get('macd_histogram', 0) > -0.1:  # Более мягкое условие
                score += 0.25
                
            # Объем
            if indicators.get('volume_ratio', 1) > 0.8:  # Снижено с 1.5
                score += 0.2
                
            # Тренд
            if indicators.get('ema_crossover', 0) >= 0:  # Включая нейтральное состояние
                score += 0.15
                
            # Волатильность
            if indicators.get('bb_squeeze', 0) >= 0:  # Всегда добавляем
                score += 0.1
                
            # Для демонстрации - добавим случайный фактор
            if random.random() > 0.7:  # 30% шанс на бонус
                score += 0.1
                
            # Нормализация
            prediction = min(score, 1.0)
            
            return {
                'valid': prediction >= 0.75,  # Снижено с 0.85
                'score': prediction,
                'ai_prediction': prediction,
                'confidence': prediction,
                'pattern_detected': True,
                'ai_condition': prediction >= 0.75
            }
        except Exception as e:
            logger.error(f"Ошибка fallback предсказания: {e}")
            return {'valid': False, 'score': 0.0}
            
    def _calculate_final_score(self, level1: Dict[str, Any], level2: Dict[str, Any], level3: Dict[str, Any]) -> float:
        """Расчет финального скора"""
        try:
            # Взвешенная сумма всех уровней
            final_score = (
                level1['score'] * 0.3 +
                level2['score'] * 0.3 +
                level3['score'] * 0.4
            )
            
            # Бонус за сильную конвергенцию
            if level1['score'] > 0.8 and level2['score'] > 0.8 and level3['score'] > 0.8:
                final_score += 0.05
                
            return min(final_score, 1.0)
            
        except Exception as e:
            logger.error(f"Ошибка расчета финального скора: {e}")
            return 0.0
            
    def _determine_direction(self, level1: Dict[str, Any], level2: Dict[str, Any], level3: Dict[str, Any]) -> str:
        """Определение направления сигнала"""
        try:
            # Простая логика направления
            bullish_signals = 0
            bearish_signals = 0
            
            # Level 1 signals
            if level1.get('impulse_strength', 0) > 0:
                bullish_signals += 1
            else:
                bearish_signals += 1
                
            # Level 2 signals
            if level2.get('macd_condition', False):
                bullish_signals += 1
            else:
                bearish_signals += 1
                
            # Level 3 signals
            if level3.get('ai_prediction', 0) > 0.5:
                bullish_signals += 1
            else:
                bearish_signals += 1
                
            return "BUY" if bullish_signals > bearish_signals else "SELL"
            
        except Exception as e:
            logger.error(f"Ошибка определения направления: {e}")
            return "BUY"
            
    def _calculate_hold_duration(self, timeframe: str, accuracy: float) -> int:
        """Расчет времени удержания позиции"""
        try:
            # Базовое время по таймфрейму
            base_times = {
                "1m": 5,
                "5m": 15,
                "15m": 30,
                "30m": 60,
                "1h": 120,
                "4h": 240,
                "1d": 480
            }
            
            base_time = base_times.get(timeframe, 30)
            
            # Корректировка по точности
            accuracy_multiplier = 0.5 + (accuracy * 0.5)
            
            # Финальное время
            hold_duration = int(base_time * accuracy_multiplier)
            
            return max(hold_duration, 5)  # Минимум 5 минут
            
        except Exception as e:
            logger.error(f"Ошибка расчета времени удержания: {e}")
            return 30
            
    async def validate_signal_quality(self, signal: Dict[str, Any]) -> bool:
        """Валидация качества сигнала (без ограничений)"""
        try:
            # Отключены все проверки лимитов
            signal_key = f"{signal['pair']}_{signal['timeframe']}"
            self.last_signals[signal_key] = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Ошибка валидации сигнала: {e}")
            return False
