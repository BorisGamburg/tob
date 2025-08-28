import requests
import pandas as pd
import ta
import time
from datetime import datetime
from pybit.unified_trading import HTTP


# Настройки
API_ENDPOINT = "https://api.bybit.com/v5/market/kline"
SYMBOL = "SPECUSDT"  # Торгуемая пара
INTERVAL = "5"      # Интервал в минутах (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
EMA_PERIOD = 50     # Период для EMA
LIMIT = 100         # Количество свечей для запроса

http_client = HTTP(
    testnet=False,
    api_key="",
    api_secret="",
    timeout=60,
)



# Функция для получения исторических данных (K-line)
def get_kline_data(self, symbol, interval, limit=100):
    response = http_client.get_kline(
        category="linear",
        symbol=symbol,
        interval=interval,  # Интервал в минутах (15 минут в данном случае)
        limit=limit        # Количество свечей
    )
    
    # Проверяем успешность запроса
    if response['retCode'] != 0:
        print(f"Ошибка API: {response['retMsg']}")
        return None
    
    # Извлекаем данные
    klines = response['result']['list']
    
    # Форматируем в DataFrame
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
    df = df.astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[::-1]  # Переворачиваем, чтобы данные шли от старых к новым
    return df
    
def calculate_ema(df, period):
    """Расчет EMA с использованием библиотеки TA"""
    # Добавляем EMA в DataFrame
    df["EMA"] = ta.trend.EMAIndicator(close=df["close"], window=period).ema_indicator()
    return df

def main():
    print(f"Запуск расчета EMA для {SYMBOL} (период: {EMA_PERIOD})")
    print(f"Текущая дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    
    while True:
        # Получаем данные
        df = get_kline_data("SPECUSDT", "50", 100)
        
        if df is not None:
            # Рассчитываем EMA
            df = calculate_ema(df, 50)
            
            # Выводим последнюю свечу с EMA
            latest = df.iloc[-1]
            print(f"\nВремя: {latest['timestamp']}")
            print(f"Цена закрытия: {latest['close']}")
            print(f"EMA: {latest['EMA']:.3f}")
        
        # Ждем перед следующим обновлением (например, 60 секунд)
        time.sleep(60)

if __name__ == "__main__":
    # Убедитесь, что у вас установлена библиотека ta
    # pip install ta
    try:
        main()
    except KeyboardInterrupt:
        print("\nОстановлено пользователем")