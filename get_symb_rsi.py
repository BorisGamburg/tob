from pybit.unified_trading import HTTP
from bybit_driver import BybitDriver
from telegram import Telegram
import pandas as pd
import logging

# Logging Setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# Telegram Setup
telegram = Telegram(logger=logger)

# Create an instance of the BybitDriver
# Ключи
api_key="beERCRcFrsJl19mupg"
api_secret="e9kHWxgBwhWjVWC5U7CheH0sAWDawUVtpXUY"
bybit_driver = BybitDriver(api_key=api_key, api_secret=api_secret, logger=logger, telegram=telegram)

# Инициализация клиента Bybit
session = HTTP(
    testnet=False,  # Укажите True для тестовой сети
    api_key="ВАШ_API_КЛЮЧ",  # Замените на ваш API ключ (опционально)
    api_secret="ВАШ_API_СЕКРЕТ"  # Замените на ваш API секрет (опционально)
)

# Функция для получения всех бессрочных USDT-перпетуалов
def get_perpetual_tokens():
    try:
        # Запрос списка торговых пар для категории linear (USDT-перпетуалы)
        response = session.get_instruments_info(category="linear")
        
        # Проверка успешности запроса
        if response['retCode'] == 0:
            symbols = response['result']['list']
            # Извлекаем только символы (торговые пары)
            token_list = [symbol['symbol'] for symbol in symbols]
            return token_list
        else:
            print(f"Ошибка API: {response['retMsg']}")
            return []
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return []
    
def get_min_size_in_usdt(symbol, category="linear"):
    """
    Получает текущую цену, минимальный размер контракта и вычисляет мин. размер в USDT.
    
    :param symbol: Символ, например "BTCUSDT"
    :param category: Тип продукта, "linear" для USDT-контрактов
    :return: Минимальный размер в USDT или None, если ошибка
    """
    try:
        # 1. Запрос текущей цены (lastPrice)
        ticker_response = session.get_tickers(
            category=category,
            symbol=symbol
        )
        
        if ticker_response['retCode'] != 0:
            print(f"Ошибка при получении цены: {ticker_response['retMsg']}")
            return None
        
        ticker = ticker_response['result']['list'][0]
        last_price = float(ticker['lastPrice'])
        
        # 2. Запрос информации об инструменте (minOrderQty)
        instrument_response = session.get_instruments_info(
            category=category,
            symbol=symbol
        )
        
        if instrument_response['retCode'] != 0:
            print(f"Ошибка при получении инструмента: {instrument_response['retMsg']}")
            return None
        
        instrument = instrument_response['result']['list'][0]
        lot_size_filter = instrument['lotSizeFilter']
        min_order_qty = float(lot_size_filter['minOrderQty'])
        
        # 3. Вычисление минимального размера в USDT
        min_size_usdt = min_order_qty * last_price
        
        # Вывод результатов
        # print(f"Символ: {symbol}")
        # print(f"Текущая цена (lastPrice): {last_price}")
        # print(f"Минимальный размер контракта (minOrderQty): {min_order_qty}")
        # print(f"Минимальный размер в USDT (minOrderQty * price): {min_size_usdt}")
        
        return min_size_usdt
        
    except Exception as e:
        print(f"Исключение: {e}")
        return None


# Получение списка токенов
tokens = get_perpetual_tokens()

# Вывод списка токенов
if tokens:
    print("Список символов:")
    for token in tokens:
        try:
            last_rsi = bybit_driver.calculate_last_rsi(token, interval="D")
            if last_rsi > 70:
                min_size = get_min_size_in_usdt(token, category="linear")
                if min_size < 0.2:
                    cur_price = bybit_driver.get_last_price(token)
                    print(f"{token} - RSI: {last_rsi} (overbought), Price={cur_price}")
                    print(f"Минимальный размер контракта в USDT для {token}: {min_size}\n")
        except:
            pass
        

