from pybit.unified_trading import HTTP
from bybit_driver import BybitDriver
from telegram import Telegram
import pandas as pd
import logging
from datetime import datetime, timedelta, timezone


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
    api_key=api_key,
    api_secret=api_secret
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
            logger.error(f"Ошибка API: {response['retMsg']}")
            return []
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
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
            logger.error(f"Ошибка при получении цены: {ticker_response['retMsg']}")
            return None
        
        ticker = ticker_response['result']['list'][0]
        last_price = float(ticker['lastPrice'])
        
        # 2. Запрос информации об инструменте (minOrderQty)
        instrument_response = session.get_instruments_info(
            category=category,
            symbol=symbol
        )
        
        if instrument_response['retCode'] != 0:
            logger.error(f"Ошибка при получении инструмента: {instrument_response['retMsg']}")
            return None
        
        instrument = instrument_response['result']['list'][0]
        lot_size_filter = instrument['lotSizeFilter']
        min_order_qty = float(lot_size_filter['minOrderQty'])
        
        # 3. Вычисление минимального размера в USDT
        min_size_usdt = min_order_qty * last_price
        
        return min_size_usdt
        
    except Exception as e:
        logger.error(f"Исключение: {e}")
        return None

def get_volume_metrics(symbol="BTCUSDT", category="linear", interval="60", hours_for_average=24, use_volume=True):
    """
    Возвращает объем предпоследней свечи и средний объем за указанный период.
    
    Args:
        symbol (str): Торговая пара (например, "BTCUSDT")
        category (str): Тип рынка ("spot" или "linear")
        interval (str): Интервал свечи в минутах (например, "60")
        hours_for_average (int): Количество часов для расчета среднего
        use_volume (bool): True для volume (в базовой монете), False для turnover (в USDT)
    
    Returns:
        tuple: (last_volume, avg_volume, last_timestamp) или (None, None, None) в случае ошибки
    """
    try:
        # Инициализация сессии
        session = HTTP(testnet=False)
        
        # Текущее время в UTC
        now = datetime.now(timezone.utc)
        end_time_ms = int(now.timestamp() * 1000)
        
        # Начало периода
        start_time = now - timedelta(hours=hours_for_average + 1)
        start_time_ms = int(start_time.timestamp() * 1000)
        
        # Получение kline данных
        result = session.get_kline(
            category=category,
            symbol=symbol,
            interval=interval,
            start=start_time_ms,
            end=end_time_ms
        )
        
        if result['retCode'] != 0:
            print(f"Ошибка API: {result['retMsg']} (ErrCode: {result['retCode']})")
            return None, None, None
            
        klines = result['result']['list']
        if not klines:
            print("Не удалось получить данные.")
            return None, None, None
            
        # Перевернем данные (новые сверху)
        klines.reverse()
        
        # Парсинг данных
        volumes = []
        timestamps = []
        
        for kline in klines:
            ts = int(kline[0]) / 1000
            vol = float(kline[5]) if use_volume else float(kline[6])
            volumes.append(vol)
            timestamps.append(datetime.fromtimestamp(ts, tz=timezone.utc))
        
        if len(volumes) < hours_for_average + 1:
            print(f"Недостаточно данных. Получено {len(volumes)} свечей.")
            return None, None, None
            
        # Объем предпоследней свечи и её временная метка
        last_volume = volumes[-2]
        last_timestamp = timestamps[-2]
        open_price = float(klines[-2][1])
        close_price = float(klines[-2][4])   
        if close_price > open_price:
            candle_color = "green"
        else:
            candle_color = "red"
        
        # Средний объем за предыдущие часы (без последней свечи)
        avg_volume = sum(volumes[:-1]) / len(volumes[:-1]) if volumes[:-1] else 0
        
        return last_volume, avg_volume, candle_color, last_timestamp
        
    except Exception as e:
        print(f"Исключение: {str(e)}")
        return None, None, None


# Получение списка токенов
tokens = get_perpetual_tokens()

# Вывод списка токенов
if tokens:
    logger.info("Список символов:")
    i = 0
    for token in tokens:
        i += 1
        if i % 10 == 0:
            print(i)
        try:
            last_rsi = bybit_driver.calculate_last_rsi(token, interval="D")
            if last_rsi < 50:
                min_size = get_min_size_in_usdt(token, category="linear")
                if min_size < 0.2:
                    cur_price = bybit_driver.get_last_price(token)
                    last_vol, avg_vol, candle_color, last_ts = get_volume_metrics(
                        symbol=token,
                        category="linear",
                        interval="60",
                        hours_for_average=24,
                        use_volume=True
                    )
                    if (last_vol / avg_vol > 3) and (candle_color == "green"):
                        print(f"{token}: Price: {cur_price}, Min Size USDT: {min_size}, RSI: {last_rsi}")
                        print(f"Предпоследний час объем ({last_ts.strftime('%Y-%m-%d %H:%M UTC')}): {last_vol:,.4f}")
                        print(f"Средний объем за 24 часа: {avg_vol:,.4f} ")
                        print(f"Отношение: {(last_vol / avg_vol * 100):.2f}%")

        except KeyboardInterrupt:
            print("\nСкрипт остановлен пользователем.")
            exit(0)        
        except Exception as e:
            if "Недостаточно данных для RSI" not in str(e):
                logger.error(f"Ошибка при обработке {token}: {e}")
            continue