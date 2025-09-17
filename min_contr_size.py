from pybit.unified_trading import HTTP

# Инициализация клиента
session = HTTP(api_key="", api_secret="")  # Замените testnet=False для основной сети

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
        print(f"Символ: {symbol}")
        print(f"Текущая цена (lastPrice): {last_price}")
        print(f"Минимальный размер контракта (minOrderQty): {min_order_qty}")
        print(f"Минимальный размер в USDT (minOrderQty * price): {min_size_usdt}")
        
        return min_size_usdt
        
    except Exception as e:
        print(f"Исключение: {e}")
        return None

# Пример использования
if __name__ == "__main__":
    symbol = "ZECUSDT"  # Измените на нужный символ
    get_min_size_in_usdt(symbol, category="linear")