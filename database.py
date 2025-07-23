"""
Модуль для работы с базой данных SQLite
Хранение истории сигналов и статистики
"""

import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

from globals import DB_PATH, DATABASE_CONFIG

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.config = DATABASE_CONFIG
        self.connection = None
        self.lock = asyncio.Lock()
        
    async def initialize(self):
        """Инициализация базы данных"""
        try:
            logger.info("📊 Инициализация базы данных...")
            
            # Создание подключения
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            
            # Создание таблиц
            await self._create_tables()
            
            # Очистка старых данных
            await self._cleanup_old_data()
            
            logger.info("✅ База данных инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise
            
    async def _create_tables(self):
        """Создание таблиц"""
        try:
            cursor = self.connection.cursor()
            
            # Таблица сигналов
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.config['signals_table']} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pair TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    accuracy REAL NOT NULL,
                    entry_time TEXT NOT NULL,
                    hold_duration INTEGER NOT NULL,
                    signal_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    result TEXT DEFAULT 'pending',
                    profit REAL DEFAULT 0.0,
                    closed_at DATETIME NULL
                )
            """)
            
            # Таблица рыночных данных
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.config['market_data_table']} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pair TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    volume REAL NOT NULL,
                    indicators_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица производительности
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.config['performance_table']} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    total_signals INTEGER DEFAULT 0,
                    successful_signals INTEGER DEFAULT 0,
                    failed_signals INTEGER DEFAULT 0,
                    accuracy REAL DEFAULT 0.0,
                    avg_profit REAL DEFAULT 0.0,
                    best_pair TEXT NULL,
                    best_timeframe TEXT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                )
            """)
            
            # Индексы для оптимизации
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_signals_pair_time 
                ON {self.config['signals_table']} (pair, timeframe, created_at)
            """)
            
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_market_data_pair_time 
                ON {self.config['market_data_table']} (pair, timeframe, timestamp)
            """)
            
            self.connection.commit()
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            raise
            
    async def save_signal(self, signal_data: Dict[str, Any]) -> int:
        """Сохранение сигнала"""
        try:
            async with self.lock:
                cursor = self.connection.cursor()
                
                cursor.execute(f"""
                    INSERT INTO {self.config['signals_table']} 
                    (pair, timeframe, direction, accuracy, entry_time, hold_duration, signal_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal_data['pair'],
                    signal_data['timeframe'],
                    signal_data['direction'],
                    signal_data['accuracy'],
                    signal_data['entry_time'],
                    signal_data['hold_duration'],
                    json.dumps(signal_data)
                ))
                
                signal_id = cursor.lastrowid
                self.connection.commit()
                
                logger.info(f"💾 Сignal сохранен: {signal_data['pair']} {signal_data['timeframe']}")
                return signal_id
                
        except Exception as e:
            logger.error(f"Ошибка сохранения сигнала: {e}")
            return 0
            
    async def update_signal_result(self, signal_id: int, result: str, profit: float):
        """Обновление результата сигнала"""
        try:
            async with self.lock:
                cursor = self.connection.cursor()
                
                cursor.execute(f"""
                    UPDATE {self.config['signals_table']} 
                    SET result = ?, profit = ?, closed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (result, profit, signal_id))
                
                self.connection.commit()
                
                logger.info(f"📊 Результат сигнала обновлен: {signal_id} -> {result}")
                
        except Exception as e:
            logger.error(f"Ошибка обновления результата: {e}")
            
    async def save_market_data(self, market_data: Dict[str, Any]):
        """Сохранение рыночных данных"""
        try:
            async with self.lock:
                cursor = self.connection.cursor()
                
                cursor.execute(f"""
                    INSERT INTO {self.config['market_data_table']} 
                    (pair, timeframe, timestamp, open_price, high_price, low_price, 
                     close_price, volume, indicators_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    market_data['pair'],
                    market_data['timeframe'],
                    market_data['timestamp'],
                    market_data['open'],
                    market_data['high'],
                    market_data['low'],
                    market_data['close'],
                    market_data['volume'],
                    json.dumps(market_data['indicators'])
                ))
                
                self.connection.commit()
                
        except Exception as e:
            logger.error(f"Ошибка сохранения рыночных данных: {e}")
            
    async def get_daily_stats(self, date: str = None) -> Dict[str, Any]:
        """Получение дневной статистики"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
                
            async with self.lock:
                cursor = self.connection.cursor()
                
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_signals,
                        SUM(CASE WHEN result = 'success' THEN 1 ELSE 0 END) as successful_signals,
                        SUM(CASE WHEN result = 'failed' THEN 1 ELSE 0 END) as failed_signals,
                        AVG(CASE WHEN result = 'success' THEN profit ELSE 0 END) as avg_profit,
                        AVG(accuracy) as avg_accuracy
                    FROM {self.config['signals_table']}
                    WHERE DATE(created_at) = ?
                """, (date,))
                
                row = cursor.fetchone()
                
                if row:
                    total = row['total_signals'] or 0
                    successful = row['successful_signals'] or 0
                    
                    return {
                        'date': date,
                        'total_signals': total,
                        'successful_signals': successful,
                        'failed_signals': row['failed_signals'] or 0,
                        'accuracy': (successful / total * 100) if total > 0 else 0.0,
                        'avg_profit': row['avg_profit'] or 0.0,
                        'avg_accuracy': row['avg_accuracy'] or 0.0
                    }
                else:
                    return {
                        'date': date,
                        'total_signals': 0,
                        'successful_signals': 0,
                        '.failed_signals': 0,
                        'accuracy': 0.0,
                        'avg_profit': 0.0,
                        'avg_accuracy': 0.0
                    }
                    
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
            
    async def get_best_pairs(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Получение лучших торговых пар"""
        try:
            async with self.lock:
                cursor = self.connection.cursor()
                
                cursor.execute(f"""
                    SELECT 
                        pair,
                        COUNT(*) as total_signals,
                        SUM(CASE WHEN result = 'success' THEN 1 ELSE 0 END) as successful_signals,
                        AVG(CASE WHEN result = 'success' THEN profit ELSE 0 END) as avg_profit
                    FROM {self.config['signals_table']}
                    WHERE DATE(created_at) = DATE('now')
                    GROUP BY pair
                    HAVING total_signals > 0
                    ORDER BY (successful_signals * 1.0 / total_signals) DESC, avg_profit DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    total = row['total_signals']
                    successful = row['successful_signals']
                    accuracy = (successful / total * 100) if total > 0 else 0.0
                    
                    result.append({
                        'pair': row['pair'],
                        'total_signals': total,
                        'successful_signals': successful,
                        'accuracy': accuracy,
                        'avg_profit': row['avg_profit'] or 0.0
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Ошибка получения лучших пар: {e}")
            return []
            
    async def get_recent_signals(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение последних сигналов"""
        try:
            async with self.lock:
                cursor = self.connection.cursor()
                
                cursor.execute(f"""
                    SELECT * FROM {self.config['signals_table']}
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    signal_data = json.loads(row['signal_data'])
                    result.append({
                        'id': row['id'],
                        'pair': row['pair'],
                        'timeframe': row['timeframe'],
                        'direction': row['direction'],
                        'accuracy': row['accuracy'],
                        'entry_time': row['entry_time'],
                        'hold_duration': row['hold_duration'],
                        'result': row['result'],
                        'profit': row['profit'],
                        'created_at': row['created_at'],
                        'signal_data': signal_data
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Ошибка получения последних сигналов: {e}")
            return []
            
    async def _cleanup_old_data(self):
        """Очистка старых данных"""
        try:
            async with self.lock:
                cursor = self.connection.cursor()
                
                # Удаление старых сигналов (старше 30 дней)
                cursor.execute(f"""
                    DELETE FROM {self.config['signals_table']}
                    WHERE created_at < datetime('now', '-30 days')
                """)
                
                # Удаление старых рыночных данных (старше 7 дней)
                cursor.execute(f"""
                    DELETE FROM {self.config['market_data_table']}
                    WHERE created_at < datetime('now', '-7 days')
                """)
                
                self.connection.commit()
                
                logger.info("🗑 Очистка старых данных выполнена")
                
        except Exception as e:
            logger.error(f"Ошибка очистки данных: {e}")
            
    async def close(self):
        """Закрытие соединения с базой данных"""
        try:
            if self.connection:
                self.connection.close()
                logger.info("📊 Соединение с БД закрыто")
        except Exception as e:
            logger.error(f"Ошибка закрытия БД: {e}")
          
