from pybit.unified_trading import HTTP
import pandas as pd
from ta.trend import ADXIndicator
import time

# Настройки API (замените на свои ключи)
api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"

# Инициализация сессии Bybit
session = HTTP(
    testnet=False,  # Используем тестовую сеть для примера, смените на False для реального аккаунта
    api_key=api_key,
    api_secret=api_secret
)

# Функция для получения исторических данных (K-line)
def get_kline_data(symbol="SPECUSDT", interval="15", limit=100):
    response = session.get_kline(
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

# Функция для расчета ADX
def calculate_adx(df, period=14):
    adx_indicator = ADXIndicator(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=period,
        fillna=False
    )
    adx_value = adx_indicator.adx()
    return adx_value.iloc[-1]  # Возвращаем последнее значение ADX

# Основная функция
def get_current_adx():
    # Получаем данные
    df = get_kline_data(symbol="SPECUSDT", interval="15", limit=100)
    
    if df is not None:
        # Рассчитываем ADX
        current_adx = calculate_adx(df)
        print(" ")
        print(f"Текущее значение ADX для SPECUSDT: {current_adx:.2f}")
    else:
        print("Не удалось получить данные для расчета ADX")

# Выполняем скрипт
if __name__ == "__main__":
    get_current_adx()