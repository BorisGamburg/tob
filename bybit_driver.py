import logging
import pandas as pd
import requests
from time import sleep
from pybit.unified_trading import HTTP
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from pybit.exceptions import InvalidRequestError
from ta.trend import ADXIndicator
import ta

class BybitDriver:
    def __init__(self, api_key, api_secret, logger, telegram, timeout=20):
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logger
        self.telegram = telegram
        self.timeout = timeout
        self.max_attempts = 5
        self.retry_delay = 10

        # Создаем клиент
        self.create_http_client()       

    def create_http_client(self):
        self.http_client = HTTP(
            demo=False,
            api_key=self.api_key,
            api_secret=self.api_secret,
            timeout=self.timeout,
        )

    def retry_api_call(self, func, *args, **kwargs):
        """Оборачивает вызов API в цикл с попытками."""
        for attempt in range(1, self.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                if isinstance(result, dict) and "retCode" in result and result["retCode"] != 0:
                    error_msg = f"1-Ошибка API (попытка {attempt}/{self.max_attempts}): {result['retMsg']}"
                    self.logger.error(error_msg)
                    if attempt == self.max_attempts:
                        raise Exception(f"Не удалось выполнить вызов API после {self.max_attempts} попыток: {result['retMsg']}")
                    sleep(self.retry_delay)
                    continue
                return result
            except Exception as e:
                error_msg = f"Ошибка API (попытка {attempt}/{self.max_attempts}): {str(e)} " 
                self.log(error_msg)
                #self.telegram.send_telegram_message(error_msg)
                if attempt == self.max_attempts:
                    raise Exception(f"Не удалось выполнить вызов API после {self.max_attempts} попыток: {str(e)}")
                
                # Пересоздаем клиент
                self.logger.info("Пересоздаем клиент")
                self.create_http_client()       
                
                sleep(self.retry_delay)
                
    

    def get_last_price(self, symbol):
        """Получает последнюю цену тикера."""
        def call():
            ticker = self.http_client.get_tickers(category="linear", symbol=symbol)
            return float(ticker['result']['list'][0]['lastPrice'])
        return self.retry_api_call(call)
    
    def get_bid_ask_prices(self, symbol):
        def call():
            response = self.http_client.get_tickers(
                category="linear",
                symbol=symbol
            )
            result = response['result']['list'][0]
            return float(result['bid1Price']), float(result['ask1Price'])
        return self.retry_api_call(call)
    

    def get_position_data(self, symbol):
        """Получает детали позиций."""
        def call():
            response = self.http_client.get_positions(category="linear", symbol=symbol)
            if response["retCode"] != 0:
                self.logger.error(f"Ошибка получения позиций: {response['retMsg']}")
                return None
            
            # Создаем переменнные для выходных значений
            buy_size = 0.0
            buy_unpnl = 0.0
            buy_price = 0.0
            sell_unpnl = 0.0
            sell_size = 0.0
            sell_price = 0.0

            # Проходим в цикле по списку позиций
            for position in response["result"]["list"]:
                if position["symbol"] == symbol:
                    if position["side"] == '':
                        # Позиции нет
                        continue

                    if position["side"] == "Buy":
                        buy_size =  float(position["size"])
                        buy_unpnl = float(position["unrealisedPnl"])
                        buy_price = float(position["avgPrice"])
                    elif position["side"] == "Sell":
                        sell_size =  float(position["size"])
                        sell_unpnl = float(position["unrealisedPnl"])
                        sell_price = float(position["avgPrice"])

            # Возврат значений
            return buy_size, sell_size, buy_unpnl, sell_unpnl, buy_price, sell_price
        
        result = self.retry_api_call(call)
        return result if result is not None else (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    

    def get_active_orders(self, symbol):
        """Получает список активных ордеров."""
        def call():
            response = self.http_client.get_open_orders(category="linear", symbol=symbol)
            if response["retCode"] != 0:
                self.logger.error(f"Ошибка получения активных ордеров: {response['retMsg']}")
                return None
            active_orders = []
            for order in response["result"]["list"]:
                active_orders.append({
                    "order_id": order["orderId"],
                    "price": float(order["price"]),
                    "side": order["side"],
                    "qty": float(order["qty"])
                })
            return active_orders
        result = self.retry_api_call(call)
        return result if result is not None else []

    def get_total_realised_pnl(self, symbol):
        """Получает общий реализованный PNL."""
        def call():
            response = self.http_client.get_closed_pnl(category="linear", symbol=symbol, limit=50)
            if response["retCode"] != 0:
                self.logger.error(f"Ошибка получения PNL: {response['retMsg']}")
                return None
            total_pnl = 0.0
            for trade in response["result"]["list"]:
                total_pnl += float(trade["closedPnl"])
            return total_pnl
        result = self.retry_api_call(call)
        return result if result is not None else 0.0
    
    def get_close_prices(self, symbol=None, interval="15", limit=100):
        """Получает цены закрытия для расчёта индикаторов."""
        df = self.get_kline_data(symbol=symbol, interval=interval, limit=limit)
        return df["close"]
    


    def get_close_prices_old(self, symbol=None, interval="15", limit=100):
        """Получает цены закрытия для расчёта индикаторов."""
        def call():
            url = "https://api.bybit.com/v5/market/kline"
            params = {
                "category": "linear",
                "symbol": symbol,
                "interval": str(interval),  # Преобразуем в строку для API
                "limit": limit
            }
            response = requests.get(url, params=params, timeout=self.timeout)
            data = response.json()
            if data["retCode"] != 0:
                self.logger.error(f"Ошибка получения свечей: {data['retMsg']}")
                return None
            if not data["result"]["list"]:
                self.logger.warning("Нет данных в ответе от API")
                return pd.Series()
            df = pd.DataFrame(data["result"]["list"], columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"])
            df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="ms")
            df["close"] = df["close"].astype(float)
            df = df.sort_values(by="timestamp", ascending=True)
            self.logger.debug(f"Получено свеч: {len(df)}, последние 5: {df[['timestamp', 'close']].tail(5).to_dict('records')}")
            return df["close"]
        result = self.retry_api_call(call)
        return result if result is not None else pd.Series()
    

    def _calculate_atr(self, window=14, interval=5):
        """Рассчитывает ATR."""
        def call():
            close_prices = self.get_close_prices(interval=str(interval), limit=window + 1)
            if len(close_prices) < window + 1:
                self.logger.warning("Недостаточно данных для расчёта ATR")
                return 0.0
            df = pd.DataFrame()
            df["close"] = close_prices
            df["high"] = close_prices.rolling(2).max()
            df["low"] = close_prices.rolling(2).min()
            df["tr"] = df["high"] - df["low"]
            atr = df["tr"].rolling(window=window).mean().iloc[-1]
            return atr if not pd.isna(atr) else 0.0
        result = self.retry_api_call(call)
        return result if result is not None else 0.0
    

    def cancel_lim_order(self, symbol, order_id):
        """Отменяет указанный ордер бота напрямую через API Bybit с повторными попытками."""
        self.logger.debug(f"Попытка отменить ордер {order_id}, symbol={symbol}")
        
        # Проверка параметров
        if not symbol or not order_id:
            self.logger.error(f"Некорректные параметры: symbol={symbol}, orderId={order_id}")
            return -1

        def call():
            try:
                response = self.http_client.cancel_order(
                    category="linear",
                    symbol=symbol,
                    orderId=order_id
                )
                if "retCode" in response and response["retCode"] in (0, 110001):
                    return response["retCode"]
                return -1
            except InvalidRequestError as e:
                if e.status_code == 110001:  # Ордер не существует или уже отменён
                    return 110001
                self.logger.error(f"Ошибка в cancel_order: {e}", exc_info=True)
                raise  # Пробрасываем другие ошибки InvalidRequestError
            except Exception as e:
                self.logger.error(f"Ошибка в cancel_order: {e}", exc_info=True)
                raise  # Пробрасываем исключение в retry_api_call

        result = self.retry_api_call(call)
        return result

    
    def place_limit_order(self, symbol, side, mode, qty, price, orderLinkId=None):
        """Выставляет лимитный ордер с поддержкой orderLinkId."""
        def call():
            if side == "Buy":
                if mode == "Open":
                    position_idx = 1
                elif mode == "Close":
                    position_idx = 2
            elif side == "Sell":
                if mode == "Open":
                    position_idx = 2
                elif mode == "Close":
                    position_idx = 1

            qty_rounded = qty

            params = {
                "category": "linear",
                "symbol": symbol,
                "side": side,
                "order_type": "Limit",
                "qty": str(qty_rounded),
                "price": str(price),
                "position_idx": position_idx
            }
            if orderLinkId:
                params["orderLinkId"] = orderLinkId

            response = self.http_client.place_order(**params)

            if response["retCode"] == 0:
                return {
                    "orderId": response["result"]["orderId"],
                    "side": side,
                    "position_idx": position_idx,
                    "qty": qty_rounded,
                    "price": price,
                    "orderLinkId": orderLinkId
                }
            else:
                self.logger.error(f"Не удалось создать ордер: {response['retMsg']}")
                return {
                    "error": response["retMsg"],
                    "side": side,
                    "position_idx": position_idx,
                    "qty": qty_rounded,
                    "price": price,
                    "orderLinkId": orderLinkId
                }

        result = self.retry_api_call(call)
        if result is None:
            self.logger.warning(f"Прекращаем пытаться выставить ордер {side}, так как позиция для закрытия отсутствует.")
            return None
        return result


    def place_market_order(self, symbol, side, position_idx, qty):
        """Выставляет рыночный ордер."""
        def call():
            self.logger.debug(f"Попытка открыть {side} позицию размером {qty} (position_idx={position_idx})")
            response = self.http_client.place_order(
                category="linear",
                symbol=symbol,
                side=side,
                order_type="Market",
                qty=str(qty),
                position_idx=position_idx
            )
            self.logger.debug(f"Ответ на рыночный ордер {side}: {response}")
            if response["retCode"] == 0:
                #self.logger.info(f"Выполнен рыночный ордер: {symbol} {side} posIdx={position_idx} qty={qty}")
                return True
            else:
                self.logger.error(f"Не удалось открыть {side} позицию: {response['retMsg']}")
                return response
        result = self.retry_api_call(call)
        if result is True:
            return True
        return False
    
    
    def calculate_last_rsi(self, symbol=None, interval="15", limit=200):
        """Рассчитывает RSI как на TradingView с использованием Wilder's RMA."""
        close_prices = self.get_close_prices(symbol=symbol, interval=interval, limit=limit)
        if len(close_prices) < 15:
            raise Exception(f"Недостаточно данных для RSI: получено {len(close_prices)} свечей, требуется минимум 15")

        rsi_indicator = RSIIndicator(close=close_prices, window=14, fillna=False)
        rsi_series = rsi_indicator.rsi()
        last_rsi = rsi_series.iloc[-1]

        if pd.isna(last_rsi):
            raise Exception("RSI не рассчитан")

        #self.logger.debug(f"Рассчитан RSI({interval}): {last_rsi:.2f}, последние 5 цен: {close_prices.tail(5).tolist()}")
        return last_rsi
    
    def calc_bb(self, symbol=None, window=20, window_dev=2, interval="240", limit=200):
        """Рассчитывает последние значения Bollinger Bands."""
        close_prices = self.get_close_prices(symbol=symbol, interval=interval, limit=limit)
        if not self._is_valid_price_data(close_prices, window):
            return None, None, None
        bb_values = self._compute_bollinger_bands(close_prices, window, window_dev)
        return self._extract_last_bb_values(bb_values)

    def _is_valid_price_data(self, close_prices, window):
        """Проверяет, достаточно ли данных для расчёта Bollinger Bands."""
        if close_prices.empty or len(close_prices) < window:
            self.logger.warning(f"Недостаточно данных для Bollinger Bands: получено {len(close_prices)}, нужно {window}")
            return False
        return True

    def _compute_bollinger_bands(self, close_prices, window, window_dev):
        """Вычисляет Bollinger Bands с заданными параметрами."""
        bb_indicator = BollingerBands(close=close_prices, window=window, window_dev=window_dev)
        bb_high = bb_indicator.bollinger_hband()
        bb_mid = bb_indicator.bollinger_mavg()
        bb_low = bb_indicator.bollinger_lband()
        return bb_high, bb_mid, bb_low

    def _extract_last_bb_values(self, bb_values):
        """Извлекает последние значения верхней, средней и нижней полос."""
        bb_high, bb_mid, bb_low = bb_values
        last_high = float(bb_high.iloc[-1]) if not pd.isna(bb_high.iloc[-1]) else None
        last_mid = float(bb_mid.iloc[-1]) if not pd.isna(bb_mid.iloc[-1]) else None
        last_low = float(bb_low.iloc[-1]) if not pd.isna(bb_low.iloc[-1]) else None
        return last_high, last_mid, last_low    
    
    # Функция для получения исторических данных (K-line)
    def get_kline_data(self, symbol, interval, limit=100):
        def call():
            response = self.http_client.get_kline(
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
    
        return self.retry_api_call(call)

    # Функция для расчета ADX
    def calculate_adx(self, df, period=14):
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
    def get_current_adx(self, symbol, interval):
        # Получаем данные
        df = self.get_kline_data(symbol, interval, limit=100)
        
        if df is not None:
            # Рассчитываем ADX
            return self.calculate_adx(df)
        else:
            return None
        
    def _calc_ema(self, df, period):
        """Расчет EMA с использованием библиотеки TA"""
        # Добавляем EMA в DataFrame
        df["EMA"] = ta.trend.EMAIndicator(close=df["close"], window=period).ema_indicator()
        return df
    
    def calc_ema(self, symbol, interval, period):
        # Получаем данные
        df = self.get_kline_data(symbol, interval, period*2,)
        
        # Рассчитываем EMA
        df = self._calc_ema(df, period)
        
        # Выводим последнюю свечу с EMA
        latest = df.iloc[-1]
        return latest['EMA']
    
    def log(self, message):
        self.logger.info(message)
        self.telegram.send_telegram_message(message)

    def get_limit_orders(self, category="linear", symbol=None, side=None):
        """
        Получает список лимитных ордеров.
        """
        def call():
            response = self.http_client.get_open_orders(category=category, symbol=symbol, limit=50)
            if response.get("retCode") != 0:
                self.logger.error(f"Ошибка получения открытых ордеров: {response.get('retMsg')}")
                return None

            orders = response.get("result", {}).get("list", [])
            limit_orders = [o for o in orders if o.get("orderType") == "Limit"]

            if side:
                limit_orders = [o for o in limit_orders if o.get("side") == side]
            
            return limit_orders
        
        result = self.retry_api_call(call)
        return result if result is not None else []


    def change_order_price(self, order, new_price, new_qty=None):
        """
        Изменяет цену существующего ордера.
        """
        def call():
            response = self.http_client.amend_order(
                category="linear",
                symbol=order["symbol"],
                orderId=order["orderId"],
                price=str(new_price),
                qty=str(new_qty)
            )
            if response.get("retCode") != 0:
                self.logger.error(f"Ошибка изменения ордера: {response.get('retMsg')}")
                return None
            return response

        result = self.retry_api_call(call)
        return result
    
    
    def move_limit_order(self, symbol, side, new_price, new_qty):
        """
        Ищет существующий лимитный ордер по символу и стороне и перемещает его на новую цену.
        """
        self.logger.info(f"Ищем лимитный ордер {side} для {symbol} для перемещения на цену {new_price}.")
        
        # Шаг 1: Находим существующий лимитный ордер
        open_limit_orders = self.get_limit_orders(symbol=symbol, side=side)

        if not open_limit_orders:
            self.logger.warning(f"Нет открытых лимитных ордеров {side} для {symbol}.")
            return {"retCode": "NO_ORDERS"} 

        # Шаг 2: Выбираем первый найденный ордер
        order_to_move = open_limit_orders[0]
        order_id = order_to_move["orderId"]
        current_price = order_to_move["price"]

        self.logger.info(f"Найден ордер для перемещения: ID={order_id}, Текущая цена={current_price}, Новая цена={new_price}.")
        
        # Шаг 3: Перемещаем ордер, используя метод change_order_price
        result = self.change_order_price(order_to_move, new_price, new_qty=new_qty)

        if result.get("retCode") == 0:
            self.logger.info(f"✅ Ордер {order_id} успешно перемещен на цену {new_price}.")
            return {"retCode": "OK", "orderId": order_id, "newPrice": new_price}
        else:
            self.logger.error(f"❌ Не удалось переместить ордер {order_id}. Ошибка: {result.get('retMsg')}")
            raise Exception(f"Не удалось переместить ордер: {result.get('retMsg')}")
        
        
    def wait_chase_order(self, symbol=None, side=None, poll_interval=5, qty=None):
        self.logger.info(f"Попытка выставить и отслеживать лимитный ордер {side} для {symbol}...")
        my_order_id = None
        my_order_price = None
        is_order_active = True

        # Основной цикл, который работает, пока ордер активен
        while is_order_active:
            if my_order_id is not None:
                # Существует ли еще ордер?
                if not self.exist_order(symbol=symbol, side=side, order_id=my_order_id):
                    # Ордер больше не существует, выходим из функции
                    self.logger.info(f"Ордер {my_order_id} больше не существует. Выходим из функции.")
                    return "OK"

                # Получение последней цены 
                current_price = self.get_last_price(symbol=symbol)
                # Сместилась ли цена?  
                if my_order_price != current_price:
                    # Цена сместилась, перемещаем ордер
                    self.logger.info(f"Цена {current_price} сместилась. Перемещаем ордер {my_order_id} с цены {my_order_price} на {current_price}.")
                    move_order = True
                else:
                    # Цена не сместилась, ордер не двигаем
                    self.logger.info(f"Цена {current_price} не сместилась. Ордер {my_order_id} остается на цене {my_order_price}.")
                    move_order = False  
            else:
                # Ордер еще не выставлен, выставляем новый лимитный ордер
                self.logger.info(f"Выставляем новый лимитный ордер {side} для {symbol} по цене рыночной {self.get_last_price(symbol=symbol)}.")
                move_order = True
                # Получение последней цены 
                current_price = self.get_last_price(symbol=symbol)

            if move_order:
                # Вызываем функцию для перемещения ордера
                move_result = self.move_limit_order(symbol=symbol, side=side, new_price=current_price, new_qty=qty)
                if move_result.get("retCode") == "OK":
                    self.logger.info("✅ Ордер успешно перемещен.")
                    my_order_id = move_result.get("orderId")
                    my_order_price = move_result.get("newPrice")
                elif move_result.get("retCode") == "NO_ORDERS":
                    # Нет ордеров для перемещения, выходим из функции
                    self.logger.info("Нет ордеров для перемещения.")
                    return "NO_ORDERS"
            
            # Ожидание перед следующей проверкой
            sleep(poll_interval)


    def exist_order(self, symbol=None, side= None, order_id=None):
        # Получаем список лим ордеров
        existing_orders = self.get_limit_orders(symbol=symbol, side=side)

        # Ищем наш ордер по ID
        my_order = next((o for o in existing_orders if o['orderId'] == order_id), None)

        # Если ордер не найден
        if not my_order:
            self.logger.info(f"✅ Ордер с ID {order_id} больше не активен.")
            return False
        
        return True


        
        







