from pybit.unified_trading import HTTP
from datetime import datetime, timedelta, timezone

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
        
        # Средний объем за предыдущие часы (без последней свечи)
        avg_volume = sum(volumes[:-1]) / len(volumes[:-1]) if volumes[:-1] else 0
        
        return last_volume, avg_volume, last_timestamp
        
    except Exception as e:
        print(f"Исключение: {str(e)}")
        return None, None, None

# Основная часть скрипта
if __name__ == "__main__":
    # Вызов функции с параметрами по умолчанию
    last_vol, avg_vol, last_ts = get_volume_metrics(
        symbol="BTCUSDT",
        category="linear",
        interval="60",
        hours_for_average=24,
        use_volume=True
    )
    
    # Вывод результатов
    if last_vol is not None:
        unit = "BTC" if True else "USDT"
        print(f"Предпоследний час ({last_ts.strftime('%Y-%m-%d %H:%M UTC')}): {last_vol:,.4f} {unit}")
        print(f"Средний объем за 24 часа: {avg_vol:,.4f} {unit}")
        print(f"Отношение: {(last_vol / avg_vol * 100):.2f}%")
    else:
        print("Не удалось получить метрики объема.")