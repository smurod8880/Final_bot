import numpy as np
import pandas as pd
import logging

from globals import INDICATORS_CONFIG, STRATEGY_CONFIG

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    def __init__(self):
        self.config = INDICATORS_CONFIG
        self.strategy_config = STRATEGY_CONFIG
        
    def calculate_all_indicators(self, data):
        try:
            if len(data) < 200:
                return {}
                
            indicators = {}
            
            indicators.update(self._calculate_moving_averages(data))
            indicators.update(self._calculate_rsi(data))
            indicators.update(self._calculate_macd(data))
            indicators.update(self._calculate_bollinger_bands(data))
            indicators.update(self._calculate_volume_indicators(data))
            indicators.update(self._calculate_momentum_indicators(data))
            indicators.update(self._calculate_volatility_indicators(data))
            
            indicators.update(self._calculate_vwap_gradient(data))
            indicators.update(self._calculate_volume_tsunami(data))
            indicators.update(self._calculate_neural_macd(data))
            indicators.update(self._calculate_quantum_rsi(data))
            
            return indicators
            
        except Exception as e:
            logger.error(f"Ошибка расчета индикаторов: {e}")
            return {}
            
    def _calculate_moving_averages(self, data):
        try:
            result = {}
            
            for period in self.config['sma_periods']:
                result[f'sma_{period}'] = data['close'].rolling(window=period).mean().iloc[-1]
            
            for period in self.config['ema_periods']:
                result[f'ema_{period}'] = data['close'].ewm(span=period).mean().iloc[-1]
                
            result['sma_20_slope'] = self._calculate_slope(data['close'].rolling(window=20).mean())
            result['ema_crossover'] = 1 if result['ema_9'] > result['ema_21'] else 0
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка расчета MA: {e}")
            return {}
            
    def _calculate_rsi(self, data):
        try:
            period = self.config['rsi_period']
            
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return {
                'rsi': rsi.iloc[-1],
                'rsi_overbought': 1 if rsi.iloc[-1] > 70 else 0,
                'rsi_oversold': 1 if rsi.iloc[-1] < 30 else 0,
                'rsi_divergence': self._calculate_rsi_divergence(data, rsi)
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета RSI: {e}")
            return {}
            
    def _calculate_macd(self, data):
        try:
            fast = self.config['macd_fast']
            slow = self.config['macd_slow']
            signal = self.config['macd_signal']
            
            ema_fast = data['close'].ewm(span=fast).mean()
            ema_slow = data['close'].ewm(span=slow).mean()
            
            macd_line = ema_fast - ema_slow
            macd_signal = macd_line.ewm(span=signal).mean()
            macd_histogram = macd_line - macd_signal
            
            return {
                'macd': macd_line.iloc[-1],
                'macd_signal': macd_signal.iloc[-1],
                'macd_histogram': macd_histogram.iloc[-1],
                'macd_crossover': 1 if macd_line.iloc[-1] > macd_signal.iloc[-1] else 0,
                'macd_divergence': self._calculate_macd_divergence(data, macd_line)
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета MACD: {e}")
            return {}
            
    def _calculate_bollinger_bands(self, data):
        try:
            period = self.config['bollinger_period']
            std_dev = self.config['bollinger_std']
            
            sma = data['close'].rolling(window=period).mean()
            std = data['close'].rolling(window=period).std()
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            current_price = data['close'].iloc[-1]
            
            return {
                'bb_upper': upper_band.iloc[-1],
                'bb_middle': sma.iloc[-1],
                'bb_lower': lower_band.iloc[-1],
                'bb_width': (upper_band.iloc[-1] - lower_band.iloc[-1]) / sma.iloc[-1],
                'bb_position': (current_price - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1]),
                'bb_squeeze': 1 if (upper_band.iloc[-1] - lower_band.iloc[-1]) / sma.iloc[-1] < 0.1 else 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета Bollinger Bands: {e}")
            return {}
            
    def _calculate_volume_indicators(self, data):
        try:
            result = {}
            
            vol_sma = data['volume'].rolling(window=self.config['volume_sma_period']).mean()
            result['volume_sma'] = vol_sma.iloc[-1]
            result['volume_ratio'] = data['volume'].iloc[-1] / vol_sma.iloc[-1]
            
            obv = self._calculate_obv(data)
            result['obv'] = obv.iloc[-1]
            result['obv_trend'] = self._calculate_slope(obv)
            
            vwap = self._calculate_vwap(data)
            result['vwap'] = vwap.iloc[-1]
            result['vwap_deviation'] = (data['close'].iloc[-1] - vwap.iloc[-1]) / vwap.iloc[-1]
            
            mfi = self._calculate_mfi(data)
            result['mfi'] = mfi.iloc[-1]
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка расчета объемных индикаторов: {e}")
            return {}
            
    def _calculate_momentum_indicators(self, data):
        try:
            result = {}
            
            stoch_k, stoch_d = self._calculate_stochastic(data)
            result['stoch_k'] = stoch_k.iloc[-1]
            result['stoch_d'] = stoch_d.iloc[-1]
            result['stoch_crossover'] = 1 if stoch_k.iloc[-1] > stoch_d.iloc[-1] else 0
            
            williams_r = self._calculate_williams_r(data)
            result['williams_r'] = williams_r.iloc[-1]
            
            cci = self._calculate_cci(data)
            result['cci'] = cci.iloc[-1]
            
            roc = self._calculate_roc(data)
            result['roc'] = roc.iloc[-1]
            
            ao = self._calculate_awesome_oscillator(data)
            result['awesome_oscillator'] = ao.iloc[-1]
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка расчета momentum индикаторов: {e}")
            return {}
            
    def _calculate_volatility_indicators(self, data):
        try:
            result = {}
            
            atr = self._calculate_atr(data)
            result['atr'] = atr.iloc[-1]
            
            adx = self._calculate_adx(data)
            result['adx'] = adx.iloc[-1]
            
            sar = self._calculate_parabolic_sar(data)
            result['parabolic_sar'] = sar.iloc[-1]
            result['sar_signal'] = 1 if data['close'].iloc[-1] > sar.iloc[-1] else 0
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка расчета volatility индикаторов: {e}")
            return {}
            
    def _calculate_vwap_gradient(self, data):
        try:
            vwap = self._calculate_vwap(data)
            
            gradient = vwap.diff().rolling(window=5).mean()
            
            gradient_norm = gradient / vwap * 100
            
            gradient_signal = 1 if gradient_norm.iloc[-1] > self.strategy_config['vwap_gradient_threshold'] else 0
            
            return {
                'vwap_gradient': gradient_norm.iloc[-1],
                'vwap_gradient_signal': gradient_signal,
                'vwap_trend_strength': abs(gradient_norm.iloc[-1]),
                'vwap_acceleration': gradient_norm.diff().iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета VWAP Gradient: {e}")
            return {}
            
    def _calculate_volume_tsunami(self, data):
        try:
            volume_sma = data['volume'].rolling(window=20).mean()
            
            volume_ratio = data['volume'].iloc[-1] / volume_sma.iloc[-1]
            
            tsunami_signal = 1 if volume_ratio > self.strategy_config['volume_multiplier'] else 0
            
            tsunami_strength = min(volume_ratio / self.strategy_config['volume_multiplier'], 3.0)
            
            return {
                'volume_tsunami': volume_ratio,
                'volume_tsunami_signal': tsunami_signal,
                'tsunami_strength': tsunami_strength,
                'volume_acceleration': data['volume'].pct_change().iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета Volume Tsunami: {e}")
            return {}
            
    def _calculate_neural_macd(self, data):
        try:
            macd_result = self._calculate_macd(data)
            
            macd_line = data['close'].ewm(span=12).mean() - data['close'].ewm(span=26).mean()
            macd_signal = macd_line.ewm(span=9).mean()
            
            volatility = data['close'].pct_change().rolling(window=14).std()
            neural_correction = volatility.iloc[-1] * 0.5
            
            neural_macd = macd_line.iloc[-1] + neural_correction
            
            neural_signal = 1 if neural_macd > macd_signal.iloc[-1] else 0
            
            return {
                'neural_macd': neural_macd,
                'neural_macd_signal': neural_signal,
                'neural_correction': neural_correction,
                'macd_strength': abs(neural_macd - macd_signal.iloc[-1])
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета Neural MACD: {e}")
            return {}
            
    def _calculate_quantum_rsi(self, data):
        try:
            rsi_result = self._calculate_rsi(data)
            
            volume_factor = (data['volume'].iloc[-1] / data['volume'].rolling(window=20).mean().iloc[-1]) * 0.1
            
            quantum_rsi = rsi_result['rsi'] + volume_factor
            quantum_rsi = max(0, min(100, quantum_rsi))
            
            quantum_overbought = quantum_rsi > 75
            quantum_oversold = quantum_rsi < 25
            
            quantum_signal = 1 if 30 < quantum_rsi < 70 else 0
            
            return {
                'quantum_rsi': quantum_rsi,
                'quantum_rsi_signal': quantum_signal,
                'quantum_overbought': 1 if quantum_overbought else 0,
                'quantum_oversold': 1 if quantum_oversold else 0,
                'rsi_momentum': quantum_rsi - rsi_result['rsi']
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета Quantum RSI: {e}")
            return {}
            
    def _calculate_slope(self, series, window=5):
        try:
            if len(series) < window:
                return 0.0
            
            y = series.tail(window).values
            x = np.arange(len(y))
            
            slope = np.polyfit(x, y, 1)[0]
            return slope
            
        except Exception as e:
            return 0.0
            
    def _calculate_obv(self, data):
        obv = pd.Series(index=data.index, dtype=float)
        obv.iloc[0] = data['volume'].iloc[0]
        
        for i in range(1, len(data)):
            if data['close'].iloc[i] > data['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + data['volume'].iloc[i]
            elif data['close'].iloc[i] < data['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - data['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
                
        return obv
        
    def _calculate_vwap(self, data):
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        vwap = (typical_price * data['volume']).cumsum() / data['volume'].cumsum()
        return vwap
        
    def _calculate_mfi(self, data):
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        money_flow = typical_price * data['volume']
        
        positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
        negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
        
        positive_mf = positive_flow.rolling(window=14).sum()
        negative_mf = negative_flow.rolling(window=14).sum()
        
        mfi = 100 - (100 / (1 + positive_mf / negative_mf))
        return mfi
        
    def _calculate_stochastic(self, data):
        k_period = self.config['stoch_k']
        d_period = self.config['stoch_d']
        
        low_k = data['low'].rolling(window=k_period).min()
        high_k = data['high'].rolling(window=k_period).max()
        
        stoch_k = 100 * (data['close'] - low_k) / (high_k - low_k)
        stoch_d = stoch_k.rolling(window=d_period).mean()
        
        return stoch_k, stoch_d
        
    def _calculate_williams_r(self, data):
        period = self.config['williams_period']
        
        high_n = data['high'].rolling(window=period).max()
        low_n = data['low'].rolling(window=period).min()
        
        williams_r = -100 * (high_n - data['close']) / (high_n - low_n)
        return williams_r
        
    def _calculate_cci(self, data):
        period = self.config['cci_period']
        
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        sma = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
        
        cci = (typical_price - sma) / (0.015 * mad)
        return cci
        
    def _calculate_roc(self, data):
        period = 12
        roc = 100 * (data['close'] - data['close'].shift(period)) / data['close'].shift(period)
        return roc
        
    def _calculate_awesome_oscillator(self, data):
        median_price = (data['high'] + data['low']) / 2
        ao = median_price.rolling(window=5).mean() - median_price.rolling(window=34).mean()
        return ao
        
    def _calculate_atr(self, data):
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = pd.Series(true_range).rolling(window=14).mean()
        return atr
        
    def _calculate_adx(self, data):
        period = self.config['adx_period']
        
        high_diff = data['high'].diff()
        low_diff = data['low'].diff()
        
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        
        atr = self._calculate_atr(data)
        plus_di = 100 * (plus_dm.rolling(window=period).sum() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).sum() / atr)
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx
        
    def _calculate_parabolic_sar(self, data):
        config = self.config['parabolic_sar']
        acceleration = config['acceleration']
        maximum = config['maximum']
        
        sar = pd.Series(index=data.index, dtype=float)
        trend = 1
        af = acceleration
        ep = data['high'].iloc[0] if trend == 1 else data['low'].iloc[0]
        sar.iloc[0] = data['low'].iloc[0]
        
        for i in range(1, len(data)):
            if trend == 1:
                sar.iloc[i] = sar.iloc[i-1] + af * (ep - sar.iloc[i-1])
                
                if data['high'].iloc[i] > ep:
                    ep = data['high'].iloc[i]
                    af = min(af + acceleration, maximum)
                    
                if data['low'].iloc[i] < sar.iloc[i]:
                    trend = -1
                    sar.iloc[i] = ep
                    af = acceleration
                    ep = data['low'].iloc[i]
            else:
                sar.iloc[i] = sar.iloc[i-1] - af * (sar.iloc[i-1] - ep)
                
                if data['low'].iloc[i] < ep:
                    ep = data['low'].iloc[i]
                    af = min(af + acceleration, maximum)
                    
                if data['high'].iloc[i] > sar.iloc[i]:
                    trend = 1
                    sar.iloc[i] = ep
                    af = acceleration
                    ep = data['high'].iloc[i]
                    
        return sar
        
    def _calculate_rsi_divergence(self, data, rsi):
        try:
            price_slope = self._calculate_slope(data['close'])
            rsi_slope = self._calculate_slope(rsi)
            
            if (price_slope > 0 and rsi_slope < 0) or (price_slope < 0 and rsi_slope > 0):
                return 1.0
            else:
                return 0.0
                
        except Exception as e:
            return 0.0
            
    def _calculate_macd_divergence(self, data, macd):
        try:
            price_slope = self._calculate_slope(data['close'])
            macd_slope = self._calculate_slope(macd)
            
            if (price_slope > 0 and macd_slope < 0) or (price_slope < 0 and macd_slope > 0):
                return 1.0
            else:
                return 0.0
                
        except Exception as e:
            return 0.0
