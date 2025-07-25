"""
Глобальные переменные и настройки системы
"""
import os

# Параметры торговых пар и таймфреймов
TRADING_PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT", "SOLUSDT", "DOGEUSDT"
]
TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

# Telegram настройки
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_telegram_bot_token")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "your_chat_id")

# WebSocket Binance
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"

# База данных
DB_PATH = "./trading_signals.db"
DATABASE_CONFIG = {
    "signals_table": "signals",
    "market_data_table": "market_data",
    "performance_table": "performance"
}

# Стратегия и параметры безопасности
STRATEGY_CONFIG = {
    "target_accuracy": 0.85,
    "daily_signals_target": 35,
    "update_interval": 10,  # секунд между циклами
    "signal_threshold": 0.87,
    "rsi_upper_limit": 65,
    "vwap_gradient_threshold": 0.002,
    "volume_multiplier": 2.5  # для Volume Tsunami
}

SAFETY_LIMITS = {
    "max_signals_per_hour": 5,
    "max_daily_signals": 40,
    "min_signal_interval": 60  # минимальный интервал между сигналами, секунд
}

# Конфиг индикаторов (Исправлено: добавлена буква 'S')
INDICATORS_CONFIG = {  # Было: INDICATOR_CONFIG
    "sma_periods": [9, 21, 50, 200],
    "ema_periods": [9, 21, 50, 200],
    "rsi_period": 14,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bollinger_period": 20,
    "bollinger_std": 2,
    "volume_sma_period": 20,
    "stoch_k": 14,
    "stoch_d": 3,
    "williams_period": 14,
    "cci_period": 20,
    "adx_period": 14,
    "parabolic_sar": {"acceleration": 0.02, "maximum": 0.2},
}

# Веса для AI модели и анализа
INDICATOR_WEIGHTS = {
    "rsi": 0.10,
    "macd": 0.15,
    "volume": 0.10,
    "bollinger": 0.10,
    "vwap": 0.10,
    "momentum": 0.10,
    "volatility": 0.10,
    "pattern": 0.10,
    "ai": 0.15
}

# Форматы сообщений Telegram
MESSAGE_FORMATS = {
    "signal": (
        "🚀 <b>НОВЫЙ СИГНАЛ</b>\n"
        "Пара: <b>{pair}</b> | Таймфрейм: <b>{timeframe}</b>\n"
        "Точность: <b>{accuracy}%</b> | Вход: <b>{entry_time}</b>\n"
        "Держать: <b>{hold_duration} мин</b>\n"
        "VWAP Gradient: {vwap_gradient:.4f}\n"
        "Volume Tsunami: {volume_tsunami:.2f}\n"
        "Neural MACD: {neural_macd:.3f}\n"
        "Quantum RSI: {quantum_rsi:.1f}\n"
        "AI Score: {ai_score:.1f}\n"
        "Направление: <b>{direction}</b>"
    ),
    "error": (
        "❌ <b>Ошибка в модуле: {module}</b>\n"
        "<i>{error}</i>\n"
        "Время: {timestamp}"
    ),
    "daily_stats": (
        "📊 <b>Дневная статистика сигналов</b>\n"
        "Всего сигналов: <b>{total_signals}</b>\n"
        "Успешных: <b>{successful_signals}</b>\n"
        "Точность: <b>{accuracy:.1f}%</b>\n"
        "Средний профит: <b>{avg_profit:.2f}</b>\n"
        "<b>Лучшие пары:</b>\n"
        "{best_pairs}"
    ),
    "status": (
        "🟢 <b>Статус бота</b>\n"
        "Аптайм: <b>{uptime}</b>\n"
        "Пары: <b>{pairs_count}</b>\n"
        "Таймфреймы: <b>{timeframes_count}</b>\n"
        "Текущая точность: <b>{current_accuracy:.1f}%</b>\n"
        "Сигналов/час: <b>{signals_per_hour}</b>"
    )
}

# AI модель (стартовые веса для быстрой инициализации)
AI_MODEL_CONFIG = {
    "learning_rate": 0.01,
    "epochs": 10,
    "batch_size": 32
}

# Глобальные переменные для статистики и состояния
performance_stats = {
    "total_signals": 0,
    "daily_signals": 0,
    "hourly_signals": 0
}

trading_active = False
bot_controller = None
