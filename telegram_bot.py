import requests
from globals import BOT_TOKEN, CHAT_ID  # Используем переменные из globals.py

async def send_signal(signal):
    direction_emoji = "🟢" if signal['direction'] == 'UP' else "🔴"
    patterns = "\n".join([f"• {p}" for p in signal.get('reasons', [])])
    
    message = (
        f"{direction_emoji} *QUOTEX SIGNAL* {direction_emoji}\n\n"
        f"• Актив: `{signal['pair']}`\n"
        f"• Таймфрейм: `{signal['timeframe']}`\n"
        f"• Направление: `{signal['direction']}`\n"
        f"• Точность: `{signal['confidence']:.2f}%`\n"
        f"• Цена: `{signal['price']:.6f}`\n"
        f"• Экспирация: `{signal['expiration']}`\n\n"
        f"📊 *Обоснование:*\n{patterns}\n\n"
        f"_Сгенерировано AI QuotexSignalNet v1.0_"
    )
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"  # Убран лишний пробел
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Telegram send error: {str(e)}")
