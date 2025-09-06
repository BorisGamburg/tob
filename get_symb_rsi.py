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

# Получение списка токенов
tokens = get_perpetual_tokens()

# Вывод списка токенов
if tokens:
    print("Список бессрочных USDT-перпетуалов на Bybit:")
    for token in tokens:
        try:
            last_rsi = bybit_driver.calculate_last_rsi(token, interval="D")
            if last_rsi > 60:
                cur_price = bybit_driver.get_last_price(token)
                print(f"{token} - RSI: {last_rsi} (overbought), Price={cur_price}")
        except:
            pass
        

