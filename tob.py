import logging
from tb import TradingBot
from config_manager import ConfigManager
import argparse
from stack import Stack
from telegram import Telegram
import sys

# Настройка логирования
logging.getLogger('pybit').setLevel(logging.WARNING)
logging.getLogger('websocket').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Функция для запуска Flask-сервера
class TradeOverBot:
    def __init__(self, config_tag=None, logger=None, telegram=None):
        self.api_key = None
        self.api_secret = None
        self.symbol = None
        self.base_cond_price = None
        self.order_stack_str = None
        self.avdo_offset=None
        self.tp_offset=None
        self.avdo_tf_rsi=None
        self.rsi_tf_prof_take=None
        self.rsi_threshold_aver_down=None
        self.rsi_threshold_prof_take=None
        self.ha_tf_prof_take=None
        self.avdo_tf_ha=None
        self.side=None
        self.posIdx=None
        self.qty=None
        self.check_interval=None
        self.avdo_amount=None
        self.debug=False
        self.tf_avdo_mapping = None
        self.tf_avdo_default = None
        self.tf_avdo_map_dict = None

        self.logger = logger
        self.telegram = telegram

        self.config_manager = ConfigManager(
            config_file="CFG/" + config_tag + ".cfg", 
            instance=self, 
            logger=self.logger
        )
        self.config_manager.load_config_to_instance()
        if self.debug:
            self.logger.setLevel(logging.DEBUG)
            self.logger.debug("Debug mode is ON")

        # Преобразуем tf_aver_down_mapping в словарь
        self.tf_avdo_map_dict = {}  # создаём пустой словарь

        for pair in self.tf_avdo_mapping.split(','):
            parts = pair.split(':')           # разбиваем, например "0:15:60" → ["0", "15", "60"]

            key = int(parts[0].strip())       # ключ верхнего уровня, например 0
            avdo_tf_rsi = int(parts[1].strip())    #
            avdo_tf_ha = int(parts[2].strip())     # 
            tp_tf_rsi_ = int(parts[3].strip())     # 
            tp_tf_ha = int(parts[4].strip())     # 

            # формируем вложенный словарь
            self.tf_avdo_map_dict[key] = {
                "avdo_tf_rsi": avdo_tf_rsi,
                "avdo_tf_ha": avdo_tf_ha,
                "tp_tf_rsi": tp_tf_rsi_,
                "tp_tf_ha": tp_tf_ha
            }


        # self.tf_avdo_map_dict = {
        #     int(parts[0].strip()): {
        #         "avdo_tf_rsi": int(parts[1].strip()),
        #         "avdo_tf_ha": int(parts[2].strip())
        #     }
        #     for parts in (pair.split(':') for pair in self.tf_avdo_mapping.split(','))

        # }    

        # Инициализируем стек
        self.order_stack = Stack()
        self.order_stack.from_string(self.order_stack_str)

        self.tb = TradingBot(
            api_key=self.api_key, 
            api_secret=self.api_secret,
            symbol=self.symbol,
            rsi_tf_prof_take=self.rsi_tf_prof_take,
            avdo_rsi_threshold=self.rsi_threshold_aver_down,
            tp_rsi_threshold=self.rsi_threshold_prof_take,
            tp_tf_ha=self.ha_tf_prof_take,
            side=self.side,
            posIdx=self.posIdx,
            qty=self.qty,
            check_interval=self.check_interval,
            logger=self.logger,
            telegram=self.telegram,
            config_tag=config_tag,
            tf_avdo_mapping=self.tf_avdo_mapping,
        )

        self.log_parameters()


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
                self.set_tf_aver_down()
                res = self.tb.run(
                    base_cond_price, 
                    self.avdo_offset, 
                    self.tp_offset, 
                    self.order_stack.peek_second_last(),
                    self.order_stack.to_string(),
                    self.avdo_tf_rsi,
                    self.avdo_tf_ha,
                    self.tp_tf_rsi,
                    self.tp_tf_ha,
                    self.order_stack.size(),
                    self.order_stack.peek()
                )
            finally:
                self.tb.stop()


            cur_price = self.tb.bybit_driver.get_last_price(self.symbol)
            if res == "average_down":
                self.handle_avdo(cur_price)
            elif res == "profit_take_market":
                self.handle_prof_take_market(cur_price)
            elif res == "profit_take_lim":
                self.handle_prof_take_lim()
            else:
                raise ValueError(f"Unknown result from trading bot: {res}")

            # Приверяем сколько осталось AvDo лим ордеров
            
            i += 1
            self.logger.debug(f"beg_stack_size={beg_stack_size}, avdo_amount={self.avdo_amount}, cur_stack_size={len(self.order_stack.items)}")
            if self.avdo_amount <= len(self.order_stack.items):
                self.log("Все итерации выполнены.")
                break

    def handle_prof_take_lim(self):
        self.order_stack.pop()
        self.log(
                    f"Prof Take lim выпол {self.symbol} {self.tb.order_prof_take_lim_saved.get('side')} " \
                    f"Stack Size: {self.order_stack.size()}"
                    f"PosIdx={self.tb.order_prof_take_lim_saved.get('positionIdx')} " \
                    f"Qty={self.tb.order_prof_take_lim_saved.get('qty')} "
                    f"Price={self.tb.order_prof_take_lim_saved.get('price')}\n" \
                    f"Стек: {self.order_stack.items}"
                )

    def handle_avdo(self, cur_price):
        res = self.tb.bybit_driver.wait_chase_order(symbol=self.symbol, side=self.side, qty=self.qty)
        if res == "NO_ORDERS":
            raise ValueError(f"{self.symbol} Нет лим ордеров для AvDo.")
            #self.tb.place_market_order(self.tb.side, self.tb.posIdx, self.qty)

        self.order_stack.push((cur_price, self.tb.qty))
        self.log(f"Average down order выполнен. {self.symbol} {self.tb.side} PosIdx={self.tb.posIdx} " \
                         f"Qty={self.tb.qty} Price={cur_price}\n" \
                         f"Стек: {self.order_stack.items}")

    def handle_prof_take_market(self, cur_price):
        while True:
            # Если стек пустой - выходим
            if self.order_stack.is_empty():
                return 

            # Вычисляем текущий offset
            price_stack, qty_stack = self.order_stack.peek()
            stack_top_price = float(price_stack)
            offset_cur =(cur_price - stack_top_price) / cur_price * self.get_side_factor()

            # Проверяем надо ли выполнить order_prof_take
            if offset_cur > self.tp_offset:
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
            
    def set_tf_aver_down(self):
        stack_size = self.order_stack.size()

        # Получаем таймфрейм из словаря, используя значение по умолчанию, если ключа нет
        #tf = self.tf_avdo_map_dict.get(stack_size, self.tf_avdo_default)
        cfg = self.tf_avdo_map_dict.get(stack_size, {"avdo_tf_rsi": self.tf_avdo_default, "avdo_tf_ha": self.tf_avdo_default})
        self.avdo_tf_rsi = cfg["avdo_tf_rsi"]
        self.avdo_tf_ha = cfg["avdo_tf_ha"]
        self.tp_tf_rsi = cfg["tp_tf_rsi"]
        self.tp_tf_ha = cfg["tp_tf_ha"]

        self.logger.info(f"Таймфреймы для AvDo и TP: rsi_tf=" \
                         f"avdo_tf_rsi={self.avdo_tf_rsi}, avdo_tf_ha={self.avdo_tf_ha}, " \
                        f"tp_tf_rsi={self.tp_tf_rsi}, tp_tf_ha={self.tp_tf_ha}")            

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
        self.logger.info(f"RSI Threshold: {self.rsi_threshold_aver_down}")
        self.logger.info(f"offset={self.avdo_offset}")
        self.logger.info("")
        self.logger.info("# Prof Take")
        self.logger.info(f"RSI Threshold: {self.rsi_threshold_prof_take}")
        self.logger.info(f"offset={self.tp_offset}")
        self.logger.info("")
        self.logger.info("# Mapping")
        self.logger.info(f"tf_mapping={self.tf_avdo_mapping}")
        self.logger.info("")
        self.logger.info("# Рыночный ордер")
        self.logger.info(f"Side: {self.side}")
        self.logger.info(f"Position Index: {self.posIdx}")
        self.logger.info(f"Quantity: {self.qty}")
        self.logger.info("")
        self.logger.info("# Стек")
        self.logger.info(f"Stack Str: {self.order_stack_str}")
        self.logger.info(f"Stack Size: {self.order_stack.size()}")
        self.logger.info("")
        self.logger.info("# Интервал опроса")
        self.logger.info(f"Check Interval: {self.check_interval}")
        self.logger.info("")
        self.logger.info("# Кол-во avdo")
        self.logger.info(f"AvDo amount: {self.avdo_amount}")
        self.logger.info("")

def setup_logging(config_tag):
    # Создаем основной логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s-%(levelname)s-%(message)s', datefmt='%d %H:%M:%S')
    #formatter = logging.Formatter('%(asctime)s - %(levelname)s - PID:%(process)d - %(message)s')

    # Обработчик для вывода в консоль. Указываем 'utf-8' для поддержки кириллицы.
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Обработчик для вывода в файл. Указываем 'utf-8' для поддержки кириллицы.
    fh = logging.FileHandler("LOG/" + config_tag + ".log", encoding='utf-8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run trading bot with a specified config file")
    parser.add_argument('--config', type=str, default='trad_bot_class_test.txt', 
                        help='Path to the configuration file (e.g., trad_bot.txt)')
    args = parser.parse_args()

    logger = setup_logging(args.config)

    telegram = Telegram(logger=logger)

    tob = TradeOverBot(
        config_tag=args.config, 
        logger=logger, 
        telegram=telegram
    )

    try:
        logger.info("Запуск основного цикла TradeOverBot...")
        tob.run()   
    except KeyboardInterrupt:
        logger.info("Получен KeyboardInterrupt. Завершение работы...")
    except Exception as e:
        tob.log(f"{tob.symbol} Выход по Exception: {e}")
    finally:
        tob.stop()
        logger.info("Все процессы завершены.")
