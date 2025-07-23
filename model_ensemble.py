import joblib
import numpy as np
import xgboost as xgb
from tensorflow.keras.models import load_model
from transformers import pipeline

class HybridModel:
    def __init__(self):
        # Загрузка реальных моделей (для демо используем инициализацию)
        self.xgb_model = xgb.XGBClassifier()
        self.lstm_model = load_model('lstm_model.h5') if False else None
        self.transformer = pipeline(
            'text-classification', 
            model='distilbert-base-uncased'
        )
        self.weights = {'xgb': 0.4, 'lstm': 0.35, 'transformer': 0.25}
        
        # Инициализация XGBoost с параметрами
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            objective='binary:logistic'
        )
        
        # Тренировка на демо-данных (в реальности загружайте предобученные)
        X_demo = np.random.rand(100, 15)
        y_demo = np.random.randint(0, 2, 100)
        self.xgb_model.fit(X_demo, y_demo)
    
    def predict(self, features):
        # Подготовка данных
        feature_values = list(features.values())[:-1]  # Исключаем patterns
        
        # XGBoost предсказание
        xgb_input = np.array([feature_values])
        xgb_proba = self.xgb_model.predict_proba(xgb_input)[0]
        
        # LSTM предсказание (заглушка)
        lstm_proba = [0.4, 0.6] if features['rsi'] < 40 else [0.6, 0.4]
        
        # Transformer предсказание на основе паттернов
        if features['patterns']:
            text = " ".join(features['patterns'])
            tf_result = self.transformer(text)[0]
            tf_proba = [0.3, 0.7] if tf_result['label'] == 'POSITIVE' else [0.7, 0.3]
        else:
            tf_proba = [0.5, 0.5]
        
        # Ансамблевое усреднение
        ensemble_proba = [
            self.weights['xgb'] * xgb_proba[0] + 
            self.weights['lstm'] * lstm_proba[0] + 
            self.weights['transformer'] * tf_proba[0],
            
            self.weights['xgb'] * xgb_proba[1] + 
            self.weights['lstm'] * lstm_proba[1] + 
            self.weights['transformer'] * tf_proba[1]
        ]
        
        confidence = max(ensemble_proba) * 100
        direction = 'UP' if ensemble_proba[1] > ensemble_proba[0] else 'DOWN'
        
        return {
            'direction': direction,
            'confidence': confidence,
            'expiration': self.calculate_expiration(features),
            'reasons': self.generate_reasons(features, direction)
        }
    
    def calculate_expiration(self, features):
        if features['atr'] > 0.01:
            return "1m"
        elif features['atr'] > 0.005:
            return "3m"
        else:
            return "5m"
    
    def generate_reasons(self, features, direction):
        reasons = []
        
        if direction == 'UP':
            if features['rsi'] < 35:
                reasons.append(f"RSI oversold ({features['rsi']:.1f})")
            if 'bullish_engulfing' in features['patterns']:
                reasons.append("Bullish engulfing pattern")
            if features['macd'] > features['macd_signal']:
                reasons.append("MACD bullish crossover")
        else:
            if features['rsi'] > 65:
                reasons.append(f"RSI overbought ({features['rsi']:.1f})")
            if 'hammer' not in features['patterns']:
                reasons.append("Lack of bullish patterns")
            if features['stoch_k'] > 80:
                reasons.append(f"Stochastic overbought ({features['stoch_k']:.1f})")
        
        if features['volume_spike']:
            reasons.append("Volume spike detected")
        
        return reasons
      
