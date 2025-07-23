import requests
from config import *

async def send_signal(signal):
    direction_emoji = "🟢" if signal['direction'] == 'UP' else "🔴"
    patterns = "\n".join([f"• {p}" for p in signal.get('reasons', [])])
    
    message = (
        f"{direction_emoji} *QUOTEX SIGNAL* {direction_emoji}\n\n"
        f"• Активе: `{signal['asset']}`\n"
        f"• Таймфрейм: `{signal['timeframe']}`\n"
        f"• Направление: `{signal['direction']}`\n"
        f"• Точность: `{signal['confidence']:.2f}%`\n"
        f"• Цена: `{signal['price']:.6f}`\n"
        f"• Экспирация: `{signal['expiration']}`\n\n"
        f"📊 *Обоснование:*\n{patterns}\n\n"
        f"_Сгенерировано AI QuotexSignalNet v1.0_"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Telegram send error: {str(e)}")
      
