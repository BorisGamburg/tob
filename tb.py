import logging
import time
import argparse
from ha_revers import HARevers
from rsi_check import RSICheck
from telegram import Telegram
from price_check import PriceCheck
from bybit_driver import BybitDriver
from config_manager import ConfigManager
from order_manag import OrderManager
import sys


class TradingBot:
    """A trading bot class for managing market orders based on RSI, HA, and price conditions."""
    
    def __init__(
        self, 
        api_key=None,
        api_secret=None,
        symbol=None,
        rsi_tf_aver_down=None,
        rsi_tf_prof_take=None,
        rsi_threshold_aver_down=None,  
        rsi_threshold_prof_take=None,
        ha_rev_prof_take_tf=None,
        ha_rev_aver_down_tf=None,
        side=None,
        posIdx=None,
        qty=None,
        qty1h70=None,
        check_interval=None,
        logger=None, 
        telegram=None,
        shared_dict=None
    ):
        """Initialize the trading bot with configuration and dependencies."""


        # Default trading parameters
        self.logger = logger
        self.telegram = telegram
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol
        self.rsi_tf_aver_down=rsi_tf_aver_down
        self.rsi_tf_prof_take=rsi_tf_prof_take
        self.rsi_threshold_aver_down = rsi_threshold_aver_down
        self.rsi_threshold_prof_take = rsi_threshold_prof_take
        self.ha_rev_prof_take_tf = ha_rev_prof_take_tf
        self.ha_rev_aver_down_tf = ha_rev_aver_down_tf
        self.side = side
        self.posIdx = posIdx
        self.qty = qty
        self.qty1h70 = qty1h70
        self.check_interval = check_interval
        self.order_prof_take_lim_id = None
        self.order_prof_take_lim_filled = False
        self.offset_aver_down = None
        self.offset_prof_take = None
        self.order_aver_down_extrem = None
        self.order_id_aver_down_extrem = None
        self.order_aver_down_extrem_filled = True
        self.shared_dict = shared_dict
        self.order_prof_take_lim_saved = None


        # Create an instance of the BybitDriver
        self.bybit_driver = BybitDriver(api_key=self.api_key, api_secret=self.api_secret, logger=self.logger, telegram=self.telegram)

        # Initialize strategy components
        self.ha_rev_prof_take = HARevers(
            symbol=self.symbol,
            timeframe=self.ha_rev_prof_take_tf, 
            bybit_driver=self.bybit_driver,
            logger=self.logger,
            telegram=self.telegram
        )
        
        self.ha_rev_aver_down = HARevers(
            symbol=self.symbol,
            timeframe=self.ha_rev_aver_down_tf, 
            bybit_driver=self.bybit_driver,
            logger=self.logger,
            telegram=self.telegram
        )
        
        self.rsi_check_aver_down = RSICheck(
            symbol=self.symbol,
            timeframe=self.rsi_tf_aver_down, 
            rsi_threshold=self.rsi_threshold_aver_down,
            bybit_driver=self.bybit_driver,
            logger=self.logger,
            telegram=self.telegram
        )
        
        self.rsi_check_prof_take = RSICheck(
            symbol=self.symbol,
            timeframe=self.rsi_tf_prof_take, 
            rsi_threshold=self.rsi_threshold_prof_take,
            bybit_driver=self.bybit_driver,
            logger=self.logger,
            telegram=self.telegram
        )
        
        self.price_check = PriceCheck(
            symbol=self.symbol,
            bybit_driver=self.bybit_driver,
            logger=self.logger,
            telegram=self.telegram
        )
        #self.price_check.set_base_cond_price(self.base_cond_price)

        # Create an instance of the OrderManager 
        self.order_man = OrderManager(
            api_key=self.api_key, 
            api_secret=self.api_secret, 
            bybit_driver=self.bybit_driver, 
            callback_function=self.order_manag_callback,
            logger=self.logger
        )
        self.order_man.start()


    def order_manag_callback(self, order):
        if order.get("orderId") == self.order_prof_take_lim_id:
            # Запоминаем для вывода позже
            self.order_prof_take_lim_saved = order
            # order_prof_take_lim_id исполнен
            self.order_prof_take_lim_filled = True
            self.logger.debug(f"Исполнен order_prof_take_lim. {self.symbol} {order.get('side')} Qty:{order.get('qty')} " \
                     f"Price: {order.get('price')}")


    def place_market_order(self, side, posIdx, qty):
        """Place a market order and log the action."""
        self.bybit_driver.place_market_order(symbol=self.symbol, side=side, position_idx=posIdx, qty=qty)
        #message = f"Выполнен рыночный ордер. {self.symbol} side={side} posIdx={posIdx} qty={self.qty}"
        #self.log(message=message)


    def check_averaging_down(self, base_cond_price=None):
            # if self.bybit_driver.calculate_last_rsi(self.symbol, "60") > 70:
            #     h170 = True
            # else:
            #     h170 = False


            # Проверяем rsi
            rsi_aver_down_snapped = self.rsi_check_aver_down.rsi_snapped(self.rsi_threshold_aver_down, side=self.side)

            # Если RSI пересек 50, то сбрасываем защелку
            if ((self.rsi_check_aver_down.rsi_curr < 50) and (self.side == "Sell")) or \
               ((self.rsi_check_aver_down.rsi_curr > 50) and (self.side == "Buy")):
                self.rsi_check_aver_down.is_rsi_snapped = False
                #self.logger.debug(f"self.rsi_check_aver_down.is_rsi_snapped сброшен")
                #self.logger.debug(f"rsi_cur={self.rsi_check_aver_down.rsi_curr}")

            # Проверяем price cond
            price_cond_filled =  self.price_check.check_price_cond(
                base_cond_price=base_cond_price,
                interval=self.ha_rev_aver_down_tf,
                side=self.side,
                offset_min=self.offset_aver_down
            )

            # Проверяем разворот HA
            HA_reversed =  self.ha_rev_aver_down.check_HA_revers(self.side)
            if HA_reversed:
                self.logger.debug(f"")
                self.logger.debug(f"check_averaging_down")
                self.logger.debug(f"HA Rev Aver Down развернулся. TF={self.ha_rev_aver_down_tf}")   
                self.logger.debug(f"HA Rev Prof Take развернулся. TF={self.ha_rev_prof_take_tf}")   
                self.logger.debug(f"rsi_aver_down_snapped: {rsi_aver_down_snapped}")  
                self.logger.debug(f"price_cond_filled: {price_cond_filled}")
                self.logger.debug(f"Price condition: {self.price_check.price_cond}")

            # Проверяем выполнение всех условий
            if not (rsi_aver_down_snapped and HA_reversed and price_cond_filled):
                return False

            # *** Все условия выполнены *

            # Выставляем лим ордер для профита
            #self.place_opposit_order(base_cond_price)

            # Сбрасываем rsi snapper
            self.rsi_check_aver_down.is_rsi_snapped = False

            return True
    
    
    def check_profit_taking(self, base_cond_price):
            if base_cond_price is None:
                # Базовой цены нет => еще ничего не открыто => закрывать нечего. Выходим
                self.logger.debug("Базовая цена не задана. Profit taking не выполняем.")
                return False   

            # *** Проверяем достигла ли цена предыдущую позицию ***
            #self.logger.debug(f"stack_second_last_price: {self.stack_second_last_price}")
            if self.stack_second_last_price != None:
                price_cur = self.bybit_driver.get_last_price(self.symbol)
                if (price_cur < float(self.stack_second_last_price)) and (price_cur < price_cur * (1 - self.offset_prof_take)):
                    return True

            # *** Проверяем RSI, HA_Resvers, Price_Cond
            # Проверяем rsi
            #self.logger.debug(f"Checking profit taking conditions.")
            rsi_prof_take_snapped = self.rsi_check_prof_take.rsi_snapped(self.rsi_threshold_prof_take, side=self.inverse_side())
            if rsi_prof_take_snapped:   
                self.logger.debug(f"rsi_prof_take_snapped = {rsi_prof_take_snapped}")

            # Если RSI пересек 50, то сбрасываем защелку
            if ((self.rsi_check_prof_take.rsi_curr > 50) and (self.side == "Sell")) or \
               ((self.rsi_check_prof_take.rsi_curr < 50) and (self.side == "Buy")):
                self.rsi_check_prof_take.is_rsi_snapped = False
                #self.logger.debug(f"self.rsi_check_prof_take.is_rsi_snapped сброшен")
                #self.logger.debug(f"rsi_cur({self.rsi_tf_prof_take})={self.rsi_check_prof_take.rsi_curr}")

            # Проверяем price cond 
            price_cond_filled =  self.price_check.check_price_cond(
                base_cond_price=base_cond_price,
                interval=self.ha_rev_prof_take_tf,
                side=self.inverse_side(),
                offset_min=self.offset_prof_take
            )

            # Проверяем разворот HA
            #self.logger.debug(f"Проверяем HA Prof Take") 
            HA_reversed =  self.ha_rev_prof_take.check_HA_revers(self.inverse_side())
            if HA_reversed:
                self.logger.debug(f"")
                self.logger.debug(f"Checking profit taking.")
                self.logger.debug(f"HA Prof Take развернулся. TF={self.ha_rev_prof_take_tf}")   
                self.logger.debug(f"rsi_prof_take_snapped: {rsi_prof_take_snapped}")  
                self.logger.debug(f"price_cond_filled: {price_cond_filled}")
                self.logger.debug(f"Price condition: {self.price_check.price_cond}")

            # Проверяем выполнение всех условий
            if not (rsi_prof_take_snapped and HA_reversed and price_cond_filled):
                return False

            # *** Все условия для profit take выполнены ***
            # Сбрасываем rsi snapper
            self.rsi_check_prof_take.is_rsi_snapped = False

            return True
    

    def inverse_posIdx(self):
        """Return the inverse position index"""
        if self.posIdx == 1:
            return 2
        elif self.posIdx == 2:
            return 1


    def run(
            self, 
            base_cond_price=None, 
            offset_aver_down=None, 
            offset_prof_take=None, 
            order_aver_down_extrem=None,
            stack_second_last=None,
            order_stack_str=None
        ):
        self.offset_aver_down = offset_aver_down 
        self.offset_prof_take = offset_prof_take 
        self.order_stack_str = order_stack_str
        self.order_aver_down_extrem = order_aver_down_extrem
        self.order_prof_take_lim_filled = False
        if stack_second_last == None:
            self.stack_second_last_price = None
            self.stack_second_last_qty = None
            self.order_prof_take_lim_id = None
        else:     
            self.stack_second_last_price, self.stack_second_last_qty = stack_second_last
            # Выставляем order_prof_take_lim
            res = self.bybit_driver.place_limit_order(
                self.symbol, 
                self.inverse_side(), 
                "Close", 
                self.stack_second_last_qty, 
                self.stack_second_last_price
            )
            self.order_prof_take_lim_id = res["orderId"]
            self.logger.info(f"order_prof_take_lim установлен. {self.symbol} {res["side"]} " \
                             f"PosIdx={res["position_idx"]} Qty={res["qty"]} Price= {res["price"]}")

        while True:
            # Обновляем атрибуты TradingBot из shared_dict на каждой итерации
            if self.shared_dict:
                for key, value in self.shared_dict.items():
                    # Проверяем, существует ли такой атрибут и обновляем его
                    if hasattr(self, key):
                        setattr(self, key, value)

            if self.order_prof_take_lim_filled:
                res = "profit_take_lim"
                break


            # Получаем реверс сигнал. Можно только один раз за цикл
            self.ha_rev_prof_take._check_HA_revers()            
            self.ha_rev_aver_down._check_HA_revers()

            # Проверяем averaging down
            res_aver_down = self.check_averaging_down(base_cond_price=base_cond_price)
            if res_aver_down:
                res = "average_down"
                break

            # Проверяем profit taking
            if self.check_profit_taking(base_cond_price=base_cond_price):
                res = "profit_take_market"
                break

            # Загружаем shared_dict
            self.shared_dict.update(self.get_exposed_attributes())

            # Выгружаем shared_dict
            self.update_from_shared_dict()

            # Ждем интервал 
            time.sleep(self.check_interval)

            # Переход на начало цикла
            continue

        return res

    def stop(self):
        # Удаляем order_prof_take_lim, если он есть
        if self.order_prof_take_lim_id is None:
            return
        
        res = self.bybit_driver.cancel_lim_order(self.symbol, self.order_prof_take_lim_id)
        if res == 0:
            self.logger.info("order_prof_take_lim удален")

    def update_from_shared_dict(self):
        if 'offset_aver_down' in self.shared_dict:
            self.offset_aver_down = self.shared_dict['offset_aver_down']
        if 'offset_prof_take' in self.shared_dict:
            self.offset_prof_take = self.shared_dict['offset_prof_take']
        if 'qty' in self.shared_dict:
            self.qty = self.shared_dict['qty']


    def log(self, message):
        self.logger.info(message)
        self.telegram.send_telegram_message(message)
    def inverse_side(self):
        if self.side == "Buy":
            return "Sell"
        elif self.side == "Sell":
            return "Buy"
        else:
            return None
        



    def get_exposed_attributes(self):
        return {
            "symbol": self.symbol,
            "side": self.side,
            "posIdx": self.posIdx,
            "qty": self.qty,
            "offset_aver_down": self.offset_aver_down,
            "offset_prof_take": self.offset_prof_take,
            "check_interval": self.check_interval,
            "order_stack_str": self.order_stack_str,
            "ha_rev_prof_take_tf": self.ha_rev_prof_take_tf,
            "ha_rev_aver_down_tf": self.ha_rev_aver_down_tf
        }

        

    
    


