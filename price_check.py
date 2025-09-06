import logging
import time
from bybit_driver import BybitDriver # Убедитесь, что этот модуль доступен

class PriceCheck:
    def __init__(self, symbol: str, bybit_driver: BybitDriver, 
                 logger: logging.Logger, telegram):
        """
        Инициализирует PriceChecker.

        Args:
            symbol (str): Торговый символ (например, 'BTCUSDT').
            target_price (float): Целевая цена для сравнения.
            logger (logging.Logger): Объект логгера для вывода информации.
        """
        self.symbol = symbol
        self.logger = logger
        self.telegram = telegram
        self.bybit_driver = bybit_driver
        self.last_price = None
        self.price_threshold = None
        self.price_snapped = False
        self.base_cond_price = None  # Базовая цена для дальнейших проверок

    def set_base_cond_price(self, base_cond_price: float):
        """
        Устанавливает базовую цену для дальнейших проверок.
        """
        self.base_cond_price = base_cond_price
        self.logger.info(f"base_cond_price для {self.symbol} установлена: {self.base_cond_price}")

    def curr_price(self):
        return self.bybit_driver.get_last_price(self.symbol)

    def check_price(self) -> bool:
        """
        Проверяет, достигла ли текущая цена целевого значения.

        Returns:
            bool: True, если текущая цена равна или превышает целевую, иначе False.
        """
        current_price = self.bybit_driver.get_last_price()
        if current_price is not None:
            if current_price >= self.base_cond_price:
                self.logger.info(f"🟢 Цена {self.symbol} ({current_price}) достигла или превысила целевую цену ({self.base_cond_price}).")
                return True
            else:
                self.logger.info(f"🔴 Цена {self.symbol} ({current_price}) ниже целевой цены ({self.base_cond_price}).")
                return False
        else:
            self.logger.warning(f"Не удалось проверить цену для {self.symbol} из-за отсутствия данных.")
            return False

    def monitor_price(self, interval_seconds: int = 5):
        """
        Мониторит цену в бесконечном цикле, проверяя ее через заданный интервал.

        Args:
            interval_seconds (int): Интервал между проверками цены в секундах.
        """
        self.logger.info(f"Начинаю мониторинг цены {self.symbol}. Целевая цена: {self.base_cond_price}. Интервал: {interval_seconds} сек.")
        while True:
            try:
                price_reached = self.check_price()
                if price_reached:
                    self.logger.info(f"✅ Успех! Цена {self.symbol} достигла целевого значения. Мониторинг завершен.")
                    # Если нужно остановить мониторинг после достижения цены
                    break
                    # Если нужно продолжать мониторинг и сообщать каждый раз
                    # time.sleep(interval_seconds)
                    # continue
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                self.logger.info("Мониторинг цены остановлен пользователем.")
                break
            except Exception as e:
                self.logger.error(f"Произошла ошибка во время мониторинга: {e}")
                time.sleep(interval_seconds) # Ждем перед повторной попыткой после ошибки
                

    def reset_check_price_threshold(self, threshold):
        self.last_price = None
        self.price_threshold = threshold


    def _check_price_threshold(self) -> bool:
        """
        Определяет, находится ли значение threshold между curr_price и last_price.

        Args:
            threshold (float): Пороговое значение для проверки.
            curr_price (float): Текущая цена.
            last_price (float): Предыдущая (последняя) цена.

        Returns:
            bool: True, если threshold находится строго между curr_price и last_price,
                иначе False.
        """
        # Найдем минимум и максимум из двух цен
        min_price = min(self.curr_price, self.last_price)
        max_price = max(self.curr_price, self.last_price)

        # Проверяем, находится ли threshold  между min_price и max_price
        if min_price <= self.price_threshold <= max_price:
            return True
        else:    
            return False
        
        
    def check_price_threshold(self, threshold_condition):
        last_price = self.bybit_driver.get_last_price()
        cond = f"last_price {threshold_condition}"
        if eval(cond):
            return True
        else:
            False



    def check_price_threshold_old(self):
        # Первый цикл?
        if self.last_price == None:
            # Первый цикл. Порог не проверяем
            self.last_price = self.bybit_driver.get_last_price()
            return False
        else:
            # Непервый цикл. Проверяем порог цены
            # Порог между текущей и предыдущей ценой?
            self.curr_price = self.bybit_driver.get_last_price()
            if self._check_price_threshold():
                # Порог пересечен. 
                self.last_price = self.curr_price
                return True
            else:
                # Порог не пересечен
                self.last_price = self.curr_price
                return False
            

    def check_price_snap(self, price_snap):
        if self.price_snapped:
            return True

        price_cond_met = self._check_price_cond(price_snap)
        if price_cond_met == None:
            self.price_snapped = True
            self.logger.info("Price Snap None.")
            return True
        elif price_cond_met: 
            self.price_snapped = True
            self.logger.info("Price Snap защелкнут.")
            return True
        else:
            return False
        
    def calc_price_cond(self, base_cond_price=None, side=None, offset_min=None):
        if base_cond_price is None:
            return ""
        
        cur_price = self.curr_price()

        # Вычисляем offset
        offset = offset_min * cur_price

        # Вычисляем cond_price
        if side == "Buy":
            cond_price = base_cond_price - offset
            price_cond = f"< {cond_price}"
        elif side == "Sell":
            cond_price = base_cond_price + offset
            price_cond = f"> {cond_price}"
        else:
            raise ValueError("Неизвестная сторона сделки. Используйте 'Buy' или 'Sell'.")

        return price_cond

    def check_price_cond(self, base_cond_price=None, side=None, offset_min=None):
        self.price_cond = self.calc_price_cond(base_cond_price=base_cond_price,  
                                               side=side, offset_min=offset_min)
        price_cond_met = self._check_price_cond(self.price_cond)
        if price_cond_met == None:
            return True
        elif price_cond_met: 
            return True
        else:
            return False


    def _check_price_cond(self, price_condition):
        if price_condition != "":
            # price_condition включен: проверяем price condition
            curr_price = self.curr_price()
            cond = f"{curr_price} {price_condition}"
            if not eval(cond):
                # price condition НЕ выполнен: Выходим
                return False
            else:
                # price condition выполнен
                return True
        else:
            # self.log("price condition выключен")
            return None


    def log(self, message):
        self.logger.info(message)
        self.telegram.send_telegram_message(message)

