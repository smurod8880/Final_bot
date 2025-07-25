"""
Модуль ИИ для предсказания движения цены
Простая реализация без сложных нейронных сетей
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from globals import AI_MODEL_CONFIG, STRATEGY_CONFIG

logger = logging.getLogger(__name__)

class AIPredictor:
    def __init__(self):
        self.config = AI_MODEL_CONFIG
        self.strategy_config = STRATEGY_CONFIG
        
        # Простая модель на основе весов
        self.model_weights = {
            'rsi': 0.15,
            'macd': 0.20,
            'volume_ratio': 0.15,
            'bb_position': 0.10,
            'vwap_gradient': 0.15,
            'price_momentum': 0.12,
            'volume_momentum': 0.08,
            'volatility': 0.05
        }
        
        # Исторические данные для обучения
        self.historical_data = {}
        self.performance_history = []
        
    async def predict(self, features: np.ndarray, pair: str, timeframe: str) -> float:
        """Предсказание движения цены"""
        try:
            # Нормализация входных данных
            normalized_features = self._normalize_features(features)
            
            # Базовое предсказание
            base_prediction = self._calculate_base_prediction(normalized_features)
            
            # Коррекция на основе исторических данных
            historical_correction = self._get_historical_correction(pair, timeframe)
            
            # Коррекция на основе времени
            time_correction = self._get_time_correction()
            
            # Коррекция на основе рыночных условий
            market_correction = self._get_market_correction(normalized_features)
            
            # Финальное предсказание
            final_prediction = (
                base_prediction * 0.6 +
                historical_correction * 0.2 +
                time_correction * 0.1 +
                market_correction * 0.1
            )
            
            # Ограничение значений
            final_prediction = max(0.0, min(1.0, final_prediction))
            
            # Логирование
            logger.debug(f"AI предсказание для {pair} {timeframe}: {final_prediction:.3f}")
            
            return final_prediction
            
        except Exception as e:
            logger.error(f"Ошибка AI предсказания: {e}")
            return 0.5  # Нейтральное значение при ошибке
            
    def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Нормализация признаков"""
        try:
            # Простая нормализация
            normalized = np.zeros_like(features)
            
            # Индекс 0-4: ценовые данные
            if len(features) > 4:
                # Нормализация цен относительно текущей цены
                current_price = features[0]
                if current_price > 0:
                    normalized[0] = 1.0  # Текущая цена
                    normalized[1] = features[1] / current_price  # High
                    normalized[2] = features[2] / current_price  # Low
                    normalized[3] = features[3] / (current_price * 1000)  # Volume
                    normalized[4] = np.tanh(features[4] * 100)  # Price change
                
            # Индекс 5+: индикаторы
            for i in range(5, len(features)):
                if i < len(features):
                    # Нормализация индикаторов
                    normalized[i] = self._normalize_indicator(features[i], i)
                    
            return normalized
            
        except Exception as e:
            logger.error(f"Ошибка нормализации: {e}")
            return np.zeros_like(features)
            
    def _normalize_indicator(self, value: float, index: int) -> float:
        """Нормализация отдельного индикатора"""
        try:
            # Различные методы нормализации для разных индикаторов
            if index == 5:  # RSI
                return value / 100.0
            elif index == 6:  # MACD
                return np.tanh(value)
            elif index == 7:  # MACD Histogram
                return np.tanh(value)
            elif index == 8:  # BB Position
                return max(0.0, min(1.0, value))
            elif index == 9:  # Volume Ratio
                return min(value / 5.0, 1.0)
            elif index == 10:  # VWAP Gradient
                return np.tanh(value * 100)
            else:
                # Общая нормализация
                return np.tanh(value)
                
        except Exception as e:
            return 0.0
            
    def _calculate_base_prediction(self, features: np.ndarray) -> float:
        """Базовое предсказание на основе весов"""
        try:
            if len(features) < 15:
                return 0.5
                
            # Извлечение ключевых признаков
            feature_map = {
                'rsi': features[5] if len(features) > 5 else 0.5,
                'macd': features[6] if len(features) > 6 else 0.0,
                'volume_ratio': features[9] if len(features) > 9 else 1.0,
                'bb_position': features[8] if len(features) > 8 else 0.5,
                'vwap_gradient': features[10] if len(features) > 10 else 0.0,
                'price_momentum': features[4] if len(features) > 4 else 0.0,
                'volume_momentum': features[3] if len(features) > 3 else 0.0,
                'volatility': features[13] if len(features) > 13 else 0.0
            }
            
            # Расчет взвешенной суммы
            prediction = 0.0
            for feature, weight in self.model_weights.items():
                feature_value = feature_map.get(feature, 0.0)
                
                # Преобразование в сигнал
                signal_strength = self._feature_to_signal(feature, feature_value)
                prediction += signal_strength * weight
                
            # Нормализация
            prediction = max(0.0, min(1.0, prediction))
            
            return prediction
            
        except Exception as e:
            logger.error(f"Ошибка базового предсказания: {e}")
            return 0.5
            
    def _feature_to_signal(self, feature_name: str, value: float) -> float:
        """Преобразование признака в сигнал"""
        try:
            if feature_name == 'rsi':
                # RSI сигнал
                if value < 0.3:  # Oversold
                    return 0.8
                elif value > 0.7:  # Overbought
                    return 0.2
                else:
                    return 0.5
                    
            elif feature_name == 'macd':
                # MACD сигнал
                return 0.7 if value > 0 else 0.3
                
            elif feature_name == 'volume_ratio':
                # Volume сигнал
                if value > 0.6:  # Высокий объем
                    return 0.8
                elif value < 0.2:  # Низкий объем
                    return 0.3
                else:
                    return 0.5
                    
            elif feature_name == 'bb_position':
                # Bollinger Bands сигнал
                if value < 0.2:  # Нижняя полоса
                    return 0.8
                elif value > 0.8:  # Верхняя полоса
                    return 0.2
                else:
                    return 0.5
                    
            elif feature_name == 'vwap_gradient':
                # VWAP градиент сигнал
                return 0.7 if value > 0 else 0.3
                
            elif feature_name == 'price_momentum':
                # Моментум цены
                return 0.7 if value > 0 else 0.3
                
            elif feature_name == 'volume_momentum':
                # Моментум объема
                return 0.6 if value > 0 else 0.4
                
            elif feature_name == 'volatility':
                # Волатильность
                return 0.6 if 0.1 < value < 0.5 else 0.4
                
            else:
                return 0.5
                
        except Exception as e:
            return 0.5

    def _get_historical_correction(self, pair: str, timeframe: str) -> float:
        """Коррекция на основе исторических данных"""
        try:
            key = f"{pair}_{timeframe}"
            
            if key not in self.historical_data:
                return 0.5
                
            # Анализ исторической производительности
            history = self.historical_data[key]
            
            if len(history) < 5:
                return 0.5
                
            # Расчет средней точности
            recent_accuracy = np.mean([h['accuracy'] for h in history[-10:]])
            
            # Коррекция на основе тренда
            if len(history) >= 2:
                trend = history[-1]['accuracy'] - history[-2]['accuracy']
                trend_correction = trend * 0.1
            else:
                trend_correction = 0.0
                
            # Финальная коррекция
            correction = recent_accuracy + trend_correction
            
            return max(0.0, min(1.0, correction))
            
        except Exception as e:
            logger.error(f"Ошибка исторической коррекции: {e}")
            return 0.5
            
    def _get_time_correction(self) -> float:
        """Коррекция на основе времени"""
        try:
            current_hour = datetime.now().hour
            
            # Коррекция на основе времени торгов
            if 8 <= current_hour <= 16:  # Активные часы
                return 0.6
            elif 16 <= current_hour <= 20:  # Вечерние часы
                return 0.7
            elif 0 <= current_hour <= 6:  # Ночные часы
                return 0.4
            else:
                return 0.5
                
        except Exception as e:
            return 0.5
            
    def _get_market_correction(self, features: np.ndarray) -> float:
        """Коррекция на основе рыночных условий"""
        try:
            # Анализ рыночных условий
            volatility = features[13] if len(features) > 13 else 0.0
            volume = features[3] if len(features) > 3 else 0.0
            
            # Коррекция на волатильность
            if volatility > 0.3:  # Высокая волатильность
                return 0.4
            elif volatility < 0.1:  # Низкая волатильность
                return 0.6
            else:
                return 0.5
                
        except Exception as e:
            return 0.5
            
    async def update_model_performance(self, pair: str, timeframe: str, prediction: float, actual_result: float):
        """Обновление производительности модели"""
        try:
            key = f"{pair}_{timeframe}"
            
            if key not in self.historical_data:
                self.historical_data[key] = []
                
            # Добавление результата
            result = {
                'timestamp': datetime.now().isoformat(),
                'prediction': prediction,
                'actual': actual_result,
                'accuracy': 1.0 if abs(prediction - actual_result) < 0.2 else 0.0,
                'error': abs(prediction - actual_result)
            }
            
            self.historical_data[key].append(result)
            
            # Ограничение размера истории
            if len(self.historical_data[key]) > 100:
                self.historical_data[key] = self.historical_data[key][-100:]
                
            # Обновление общей производительности
            self.performance_history.append(result)
            
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]
                
            logger.debug(f"Обновлена производительность модели: {key}")
            
        except Exception as e:
            logger.error(f"Ошибка обновления производительности: {e}")
            
    def get_model_performance(self) -> Dict[str, Any]:
        """Получение статистики производительности модели"""
        try:
            if not self.performance_history:
                return {
                    'total_predictions': 0,
                    'average_accuracy': 0.0,
                    'average_error': 0.0
                }
                
            total_predictions = len(self.performance_history)
            average_accuracy = np.mean([p['accuracy'] for p in self.performance_history])
            average_error = np.mean([p['error'] for p in self.performance_history])
            
            # Производительность по парам
            pair_performance = {}
            for key, history in self.historical_data.items():
                if history:
                    pair_performance[key] = {
                        'predictions': len(history),
                        'accuracy': np.mean([h['accuracy'] for h in history]),
                        'error': np.mean([h['error'] for h in history])
                    }
                    
            return {
                'total_predictions': total_predictions,
                'average_accuracy': average_accuracy,
                'average_error': average_error,
                'pair_performance': pair_performance
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
            
    async def retrain_model(self):
        """Переобучение модели (упрощенная версия)"""
        try:
            if not self.performance_history:
                return
                
            # Анализ производительности
            recent_performance = self.performance_history[-50:]
            
            if len(recent_performance) < 10:
                return
                
            # Корректировка весов на основе производительности
            avg_accuracy = np.mean([p['accuracy'] for p in recent_performance])
            
            if avg_accuracy < 0.6:
                # Снижение весов неэффективных индикаторов
                for feature in self.model_weights:
                    self.model_weights[feature] *= 0.95
                    
            elif avg_accuracy > 0.8:
                # Усиление весов эффективных индикаторов
                for feature in self.model_weights:
                    self.model_weights[feature] *= 1.05
                    
            # Нормализация весов
            total_weight = sum(self.model_weights.values())
            for feature in self.model_weights:
                self.model_weights[feature] /= total_weight
                
            logger.info(f"Модель переобучена. Средняя точность: {avg_accuracy:.3f}")
            
        except Exception as e:
            logger.error(f"Ошибка переобучения модели: {e}")
            
    def save_model(self, filepath: str):
        """Сохранение модели"""
        try:
            model_data = {
                'weights': self.model_weights,
                'historical_data': self.historical_data,
                'performance_history': self.performance_history[-100:],  # Последние 100 записей
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(model_data, f, indent=2)
                
            logger.info(f"Модель сохранена: {filepath}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения модели: {e}")
            
    def load_model(self, filepath: str):
        """Загрузка модели"""
        try:
            with open(filepath, 'r') as f:
                model_data = json.load(f)
                
            self.model_weights = model_data.get('weights', self.model_weights)
            self.historical_data = model_data.get('historical_data', {})
            self.performance_history = model_data.get('performance_history', [])
            
            logger.info(f"Модель загружена: {filepath}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
