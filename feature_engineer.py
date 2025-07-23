"""
Модуль технических индикаторов
Стратегия "Quantum Precision V2"
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Any
import logging
from datetime import datetime

from globals import *
import talib

logger = logging.getLogger(__name__)

class FeatureEngineer:
    def calculate_features(self, df, orderbook=None, ticker=None):
        """Расчет признаков с учетом новых данных"""
        if len(df) < 50:
            return None
            
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        volumes = df['volume'].values
        
        # Основные индикаторы (без изменений)
        features = {
            'rsi': talib.RSI(closes, RSI_PERIOD)[-1],
            'macd': talib.MACD(closes, MACD_FAST_PERIOD, MACD_SLOW_PERIOD, MACD_SIGNAL_PERIOD)[0][-1],
            'price': closes[-1]
        }
        
        # Добавляем анализ стакана
        if orderbook:
            features['orderbook_imbalance'] = self.calculate_orderbook_imbalance(orderbook)
            features['spread'] = orderbook['asks'][0][0] - orderbook['bids'][0][0]
        
        # Добавляем анализ тикера
        if ticker:
            features['volume_change'] = ticker['volume'] / np.mean(volumes[-10:])
            features['price_change'] = ticker['change']
        
        return features
    
    def calculate_orderbook_imbalance(self, orderbook):
        """Расчет дисбаланса стакана"""
        top_bids = sum(qty for _, qty in orderbook['bids'][:5])
        top_asks = sum(qty for _, qty in orderbook['asks'][:5])
        return (top_bids - top_asks) / (top_bids + top_asks)
      
