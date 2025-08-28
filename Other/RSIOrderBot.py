import logging
import time
from bybit_driver import BybitDriver
from telegram import Telegram
from config_manager import ConfigManager  # Импортируем ConfigManager

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RSIOrderBot:
    def __init__(self):
        # Значения по умолчанию (будут перезаписаны из config.txt)
        self.symbol = ""
        self.rsi_threshold_high = 0
        self.rsi_threshold_low = 0
        self.interval = ""
        self.check_interval = 0
        self.order_quantity = 0.0
        self.enable_buy_order = True
        self.enable_sell_order = True

        # Загрузка конфигурации
        self.config_manager = ConfigManager(config_file="RSIOrderBot.txt", instance=self, logger=logger)

        self.bybit_driver = BybitDriver(symbol=self.symbol, logger=logger)
        self.telegram = Telegram(logger=logger)
        self.last_rsi = None
        self.order_placed = False

    def check_rsi_and_place_order(self):
        """Проверяет RSI и размещает рыночный ордер при достижении пороговых значений."""
        if self.order_placed:
            logger.info("Ордер уже размещен. Завершение работы.")
            return True

        try:
            current_rsi = self.bybit_driver.calculate_last_rsi(interval=self.interval)
            logger.info(f"RSI({self.interval}): {current_rsi:.2f}")

            # Краткий вывод настроек при каждой проверке
            logger.info(f"{self.symbol}, RSI High: {self.rsi_threshold_high} {self.enable_sell_order}, RSI Low: {self.rsi_threshold_low} {self.enable_buy_order} ")

            # Проверка на перекупленность и размещение ордера на продажу
            if current_rsi >= self.rsi_threshold_high:
                if self.enable_sell_order:
                    message = f"⚠️ RSI: {current_rsi:.2f} (>{self.rsi_threshold_high}) на {self.interval}m. Размещаю рыночный ордер на ПРОДАЖУ."
                    logger.info(message)
                    self.telegram.send_telegram_message(message)
                    order_result = self.bybit_driver.place_market_order(side="Sell", position_idx=1, qty=self.order_quantity)
                    logger.info(f"Результат ордера на продажу: {order_result}")
                    self.order_placed = True
                    return True
                else:
                    logger.info(f"RSI: {current_rsi:.2f} (>{self.rsi_threshold_high}) на {self.interval}m. Размещение ордера на продажу ЗАПРЕЩЕНО настройками.")

            # Проверка на перепроданность и размещение ордера на покупку
            if current_rsi <= self.rsi_threshold_low:
                if self.enable_buy_order:
                    message = f"⚠️ RSI: {current_rsi:.2f} (<{self.rsi_threshold_low}) на {self.interval}m. Размещаю рыночный ордер на ПОКУПКУ."
                    logger.info(message)
                    self.telegram.send_telegram_message(message)
                    order_result = self.bybit_driver.place_market_order(side="Buy", position_idx=2, qty=self.order_quantity)
                    logger.info(f"Результат ордера на покупку: {order_result}")
                    self.order_placed = True
                    return True
                else:
                    logger.info(f"RSI: {current_rsi:.2f} (<{self.rsi_threshold_low}) на {self.interval}m. Размещение ордера на покупку ЗАПРЕЩЕНО настройками.")

            self.last_rsi = current_rsi
            return False

        except Exception as e:
            logger.error(f"Ошибка при проверке RSI и размещении ордера: {e}")
            return False

    def run(self):
        """Запускает бесконечный цикл для периодической проверки RSI и размещения ордеров."""
        logger.info(f"Запуск бота для {self.symbol} с интервалом проверки {self.check_interval} секунд")

        while True:
            try:
                if self.check_rsi_and_place_order():
                    break
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("Бот остановлен пользователем")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле: {e}")
                time.sleep(self.check_interval)

def main():
    bot = RSIOrderBot()
    bot.run()
    logger.info("Работа бота завершена.")

if __name__ == "__main__":
    main()
