import logging
import time
from bybit_driver import BybitDriver
from telegram import Telegram

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RSIOrderBot:
    def __init__(self, symbol, rsi_threshold_high=70, rsi_threshold_low=30, interval="15", check_interval=60,
                 order_quantity=1):
        self.symbol = symbol
        self.rsi_threshold_high = rsi_threshold_high
        self.rsi_threshold_low = rsi_threshold_low
        self.interval = interval
        self.check_interval = check_interval  # Интервал проверки в секундах
        self.order_quantity = order_quantity  # Количество для рыночного ордера
        self.bybit_driver = BybitDriver(symbol=symbol, logger=logger)
        self.telegram = Telegram(logger=logger)
        self.last_rsi = None
        self.in_overbought_condition = False
        self.in_oversold_condition = False
        self.order_placed = False  # Флаг, указывающий, был ли размещен ордер

    def check_rsi_and_place_order(self):
        """Проверяет RSI и размещает рыночный ордер при достижении пороговых значений."""
        if self.order_placed:
            logger.info("Ордер уже размещен. Завершение работы.")
            return True  # Сигнализируем о завершении работы

        try:
            current_rsi = self.bybit_driver.calculate_last_rsi(interval=self.interval)
            logger.info(f"Текущий RSI для {self.symbol} на интервале {self.interval}m: {current_rsi:.2f}")

            # Проверка на перекупленность и размещение ордера на продажу
            # if current_rsi >= self.rsi_threshold_high and not self.in_overbought_condition:
            #     message = f"⚠️ {self.symbol} достиг зоны перекупленности! RSI: {current_rsi:.2f} (>{self.rsi_threshold_high}) на {self.interval}m. Размещаю рыночный ордер на ПРОДАЖУ."
            #     logger.info(message)
            #     self.telegram.send_telegram_message(message)
            #     order_result = self.bybit_driver.place_market_order(side="Sell", quantity=self.order_quantity)
            #     logger.info(f"Результат ордера на продажу: {order_result}")
            #     self.in_overbought_condition = True
            #     self.in_oversold_condition = False # Сброс флага перепроданности
            #     self.order_placed = True
            #     return True  # Сигнализируем о завершении работы

            # elif current_rsi < self.rsi_threshold_high:
            #     self.in_overbought_condition = False # Сброс флага перекупленности

            # Проверка на перепроданность и размещение ордера на покупку
            if current_rsi <= self.rsi_threshold_low and not self.in_oversold_condition:
                message = f"⚠️ {self.symbol} достиг зоны перепроданности! RSI: {current_rsi:.2f} (<{self.rsi_threshold_low}) на {self.interval}m. Размещаю рыночный ордер на ПОКУПКУ."
                logger.info(message)
                self.telegram.send_telegram_message(message)
                order_result = self.bybit_driver.place_market_order(side="Buy", quantity=self.order_quantity)
                logger.info(f"Результат ордера на покупку: {order_result}")
                self.in_oversold_condition = True
                self.in_overbought_condition = False # Сброс флага перекупленности
                self.order_placed = True
                return True  # Сигнализируем о завершении работы

            elif current_rsi > self.rsi_threshold_low:
                self.in_oversold_condition = False # Сброс флага перепроданности

            self.last_rsi = current_rsi
            return False # Ордер еще не размещен

        except Exception as e:
            logger.error(f"Ошибка при проверке RSI и размещении ордера: {e}")
            return False

    def run(self):
        """Запускает бесконечный цикл для периодической проверки RSI и размещения ордеров."""
        logger.info(f"Запуск бота для {self.symbol} с интервалом проверки {self.check_interval} секунд")
        while True:
            try:
                if self.check_rsi_and_place_order():
                    break  # Выход из цикла после размещения ордера
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("Бот остановлен пользователем")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле: {e}")
                time.sleep(self.check_interval)  # Пауза перед следующей попыткой

def main():
    # Настройки бота
    symbol = "TRUMPUSDT"  # Символ для мониторинга
    rsi_threshold_high = 70  # Верхний порог RSI для продажи
    rsi_threshold_low = 30   # Нижний порог RSI для покупки
    interval = "5"          # Интервал RSI в минутах
    check_interval = 30      # Интервал проверки RSI и размещения ордера в секундах
    order_quantity = 0.1       # Количество для рыночного ордера

    # Инициализация бота
    bot = RSIOrderBot(
        symbol=symbol,
        rsi_threshold_high=rsi_threshold_high,
        rsi_threshold_low=rsi_threshold_low,
        interval=interval,
        check_interval=check_interval,
        order_quantity=order_quantity
    )

    # Запуск бота
    bot.run()
    logger.info("Работа бота завершена.")

if __name__ == "__main__":
    main()