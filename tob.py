import logging
from tb import TradingBot
from config_manager import ConfigManager
import argparse
from stack import Stack
from telegram import Telegram
from flask import Flask, current_app, jsonify, request
from multiprocessing import Process, Manager
from waitress import serve
import os

# Настройка логирования
logging.getLogger('pybit').setLevel(logging.WARNING)
logging.getLogger('websocket').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Функция для запуска Flask-сервера
class TradeOverBot:
    def __init__(self, config_file_path=None, logger=None, telegram=None, shared_dict=None):
        self.api_key = None
        self.api_secret = None
        self.symbol = None
        self.base_cond_price = None
        self.order_stack_str = None
        self.offset_aver_down=None
        self.offset_prof_take=None
        self.rsi_tf_aver_down=None
        self.rsi_tf_prof_take=None
        self.rsi_threshold_aver_down=None
        self.rsi_threshold_prof_take=None
        self.ha_tf_prof_take=None
        self.ha_tf_aver_down=None
        self.side=None
        self.posIdx=None
        self.qty=None
        self.qty1h70=None
        self.check_interval=None
        self.order_aver_down_extrem=None
        self.avdo_amount=None

        self.logger = logger
        self.telegram = telegram
        self.shared_dict = shared_dict        

        self.config_manager = ConfigManager(
            config_file=config_file_path, 
            instance=self, 
            logger=self.logger
        )
        self.config_manager.load_config_to_instance()
        self.log_parameters()

        self.order_stack = Stack()
        self.order_stack.from_string(self.order_stack_str)

        self.tb = TradingBot(
            api_key=self.api_key, 
            api_secret=self.api_secret,
            symbol=self.symbol,
            rsi_tf_aver_down=self.rsi_tf_aver_down,
            rsi_tf_prof_take=self.rsi_tf_prof_take,
            rsi_threshold_aver_down=self.rsi_threshold_aver_down,
            rsi_threshold_prof_take=self.rsi_threshold_prof_take,
            ha_rev_prof_take_tf=self.ha_tf_prof_take,
            ha_rev_aver_down_tf=self.ha_tf_aver_down,
            side=self.side,
            posIdx=self.posIdx,
            qty=self.qty,
            qty1h70=self.qty1h70,
            check_interval=self.check_interval,
            logger=self.logger,
            telegram=self.telegram,
            shared_dict=shared_dict
        )

    def stop(self):
        self.order_stack_str = self.order_stack.to_string()
        self.config_manager.set_config_param("order_stack_str", self.order_stack_str, "string")

    def run(self):
        i = 1
        beg_stack_size = len(self.order_stack.items)
        while True:
            self.logger.info(f"")
            self.logger.info(f"Iteration {i}")

            stack_item = self.order_stack.peek()
            price, qty_stack = stack_item or (None, None)                
            base_cond_price = float(price) if price is not None else None

            try:
                res = self.tb.run(
                    base_cond_price, 
                    self.offset_aver_down, 
                    self.offset_prof_take, 
                    self.order_aver_down_extrem,
                    self.order_stack.peek_second_last(),
                    self.order_stack.to_string()
                )
            finally:
                self.tb.stop()


            cur_price = self.tb.bybit_driver.get_last_price(self.symbol)
            if res == "average_down":
                self.tb.place_market_order(self.tb.side, self.tb.posIdx,self.qty)
                self.order_stack.push((cur_price, self.tb.qty))
                self.log(f"Average down order выполнен. {self.symbol} {self.tb.side} PosIdx={self.tb.posIdx} " \
                         f"Qty={self.tb.qty} Price={cur_price}\n" \
                         f"Стек: {self.order_stack.items}")
            elif res == "profit_take_market":
                self.check_pos_for_close(cur_price)
            elif res == "profit_take_lim":
                self.order_stack.pop()
                self.log(
                    f"Profit Take lim order выполнен. {self.symbol} {self.tb.order_prof_take_lim_saved.get('side')} " \
                    f"PosIdx={self.tb.order_prof_take_lim_saved.get('positionIdx')} " \
                    f"Qty={self.tb.order_prof_take_lim_saved.get('qty')} "
                    f"Price={self.tb.order_prof_take_lim_saved.get('price')}\n" \
                    f"Стек: {self.order_stack.items}"
                )
            else:
                raise ValueError(f"Unknown result from trading bot: {res}")
            
            i += 1
            print(f"beg_stack_size={beg_stack_size}, avdo_amount={self.avdo_amount}, cur_stack_size={len(self.order_stack.items)}")
            if beg_stack_size + self.avdo_amount == len(self.order_stack.items):
                self.log("Все итерации выполнены.")
                break


    def check_pos_for_close(self, cur_price):
        while True:
            # ЕСли стек пустой - выходим
            if self.order_stack.is_empty():
                return 

            # Вычисляем текущий offset
            price_stack, qty_stack = self.order_stack.peek()
            stack_top_price = float(price_stack)
            offset_cur =(cur_price - stack_top_price) / cur_price * self.get_side_factor()

            # Проверяем надо ли выполнить order_prof_take
            if offset_cur > self.offset_prof_take:
                # Выполняем order_prof_take
                self.tb.place_market_order(self.tb.inverse_side(), self.tb.inverse_posIdx(), qty_stack)
                # Уменьшаем стек
                self.order_stack.pop()
                # Лог
                self.log(f"Profit take market order выполнен. {self.symbol} {self.tb.inverse_side()} PosIdx={self.tb.inverse_posIdx()} " \
                        f"Qty={self.tb.qty} Price={cur_price}. Закрыта позиция по цене {stack_top_price}\n" \
                        f"Стек: {self.order_stack.items}") 
                continue
            else:
                return 

    def get_side_factor(self):
        if self.tb.side == "Sell":
            return -1
        elif self.tb.side == "Buy":
            return 1
        else:
            raise ValueError(f"Unknown side: {self.tb.side}")

    def log(self, message):
        self.logger.info(message)
        self.telegram.send_telegram_message(message)

    def log_parameters(self):
        self.logger.info("# Символ")
        self.logger.info(f"Symbol: {self.symbol}")
        self.logger.info("")
        self.logger.info("# Aver Down")
        self.logger.info(f"Timeframe RSI Aver Down: {self.rsi_tf_aver_down}")
        self.logger.info(f"RSI Threshold Aver Down: {self.rsi_threshold_aver_down}")
        self.logger.info(f"Timeframe HA Aver Down: {self.ha_tf_aver_down}")
        self.logger.info(f"offset_aver_down={self.offset_aver_down}")
        self.logger.info("")
        self.logger.info("Prof Take")
        self.logger.info(f"Timeframe RSI Prof Take: {self.rsi_tf_prof_take}")
        self.logger.info(f"RSI Threshold Profit Take: {self.rsi_threshold_prof_take}")
        self.logger.info(f"Timeframe HA Prof Take: {self.ha_tf_prof_take}")
        self.logger.info(f"offset_prof_take={self.offset_prof_take}")
        self.logger.info("")
        self.logger.info("# Рыночный ордер")
        self.logger.info(f"Side: {self.side}")
        self.logger.info(f"Position Index: {self.posIdx}")
        self.logger.info(f"Quantity: {self.qty}")
        self.logger.info("")
        self.logger.info("# Стек строка")
        self.logger.info(f"order_stack_str: {self.order_stack_str}")
        self.logger.info("")
        self.logger.info("# Интервал опроса")
        self.logger.info(f"Check Interval: {self.check_interval}")
        self.logger.info("")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run trading bot with a specified config file")
    parser.add_argument('--config', type=str, default='trad_bot_class_test.txt', 
                        help='Path to the configuration file (e.g., trad_bot.txt)')
    args = parser.parse_args()

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - PID:%(process)d - %(message)s')
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    telegram = Telegram(logger=logger)

    with Manager() as manager:
        shared_dict = manager.dict()

        tob = TradeOverBot(
            config_file_path=args.config, 
            logger=logger, 
            telegram=telegram, 
            shared_dict=shared_dict
        )

        try:
            logger.info("Запуск основного цикла TradeOverBot...")
            tob.run()   
        except KeyboardInterrupt:
            logger.info("Получен KeyboardInterrupt. Завершение работы...")
        finally:
            tob.stop()
            logger.info("Завершение Flask-сервера...")
            logger.info("Все процессы завершены.")
