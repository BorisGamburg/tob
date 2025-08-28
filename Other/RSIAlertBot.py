import logging
import time
from bybit_driver import BybitDriver
from telegram import Telegram
from config_manager import PSRSI_Manager
import sys

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RSIAlertBot:
    def __init__(self, symbol, rsi_threshold_high=70, rsi_threshold_low=30, interval="15", check_interval=60,
                 trend_flat="UP", deposit_usdt=10):
        self.symbol = symbol
        self.rsi_threshold_high = rsi_threshold_high
        self.rsi_threshold_low = rsi_threshold_low
        self.interval = interval
        self.check_interval = check_interval  # Интервал проверки в секундах
        self.bybit_driver = BybitDriver(symbol=symbol, logger=logger)
        self.telegram = Telegram(logger=logger)
        self.PSRSI_Manager = PSRSI_Manager()
        self.last_rsi = None
        self.trend_flat = trend_flat
        self.deposit_usdt = deposit_usdt

    def check_rsi_and_notify(self):
        """Проверяет RSI и отправляет уведомление при достижении пороговых значений."""
        try:
            current_rsi = self.bybit_driver.calculate_last_rsi(interval=self.interval)
            PSRSI = self.PSRSI_Manager.load_PSRSI(trend_flat=self.trend_flat)
            soll_percent_from_rsi = self.PSRSI_Manager.get_soll_percent_from_rsi(current_rsi, PSRSI)
            last_price = self.bybit_driver.get_last_price()
            soll = self.deposit_usdt * soll_percent_from_rsi / 100 / last_price
            logger.info(f"RSI({self.interval}): {current_rsi:.2f} Soll={soll:.2f}")

            # if soll < -0.2:
            #     message = f"soll < -0.2"
            #     self.telegram.send_telegram_message(message)
            #     logger.info(message)
            #     sys.exit(0)

            # if soll > 0.1:
            #     message = f"soll > 0"
            #     self.telegram.send_telegram_message(message)
            #     logger.info(message)
            #     sys.exit(0)

            # Проверка на перекупленность (RSI выше верхнего порога)
            if current_rsi >= self.rsi_threshold_high and (self.last_rsi is None or self.last_rsi < self.rsi_threshold_high):
                message = f"⚠️ {self.symbol} перекуплен! RSI: {current_rsi:.2f} (>{self.rsi_threshold_high}) на {self.interval}m"
                self.telegram.send_telegram_message(message)
                logger.info(f"Отправлено уведомление: {message}")

            # Проверка на перепроданность (RSI ниже нижнего порога)
            elif current_rsi <= self.rsi_threshold_low and (self.last_rsi is None or self.last_rsi > self.rsi_threshold_low):
                message = f"⚠️ {self.symbol} перепродан! RSI: {current_rsi:.2f} (<{self.rsi_threshold_low}) на {self.interval}m"
                self.telegram.send_telegram_message(message)
                logger.info(f"Отправлено уведомление: {message}")

            self.last_rsi = current_rsi

        except Exception as e:
            logger.error(f"Ошибка при проверке RSI: {e}")

    def run(self):
        """Запускает бесконечный цикл для периодической проверки RSI."""
        logger.info(f"Запуск бота для {self.symbol} с интервалом проверки {self.check_interval} секунд")
        while True:
            try:
                self.check_rsi_and_notify()
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
    rsi_threshold_high = 70  # Верхний порог RSI
    rsi_threshold_low = 30   # Нижний порог RSI
    interval = "60"          # Интервал в минутах
    check_interval = 30     # Интервал проверки в секундах
    trend_flat = "UP"
    deposit_usdt = 10

    # Инициализация бота
    bot = RSIAlertBot(
        symbol=symbol,
        rsi_threshold_high=rsi_threshold_high,
        rsi_threshold_low=rsi_threshold_low,
        interval=interval,
        check_interval=check_interval,
        trend_flat=trend_flat,
        deposit_usdt=deposit_usdt
    )

    # Запуск бота в бесконечном цикле
    bot.run()

if __name__ == "__main__":
    main()