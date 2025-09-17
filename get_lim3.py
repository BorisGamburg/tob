import logging
import time
from bybit_driver import BybitDriver  # Убедитесь, что ваш класс находится в этом файле

# Заглушки для логгера и телеграма
class DummyLogger:
    def info(self, message):
        print(f"[INFO] {message}")
    def error(self, message):
        print(f"[ERROR] {message}")
    def debug(self, message):
        print(f"[DEBUG] {message}")
    def warning(self, message):
        print(f"[WARNING] {message}")

class DummyTelegram:
    def send_telegram_message(self, message):
        print(f"[TELEGRAM] {message}")


# Ваши API-ключи
API_KEY = "UBX1dpzpCux8bgJv6V"
API_SECRET = "8tCnPYBiqkAxqojMfM6xRt2MwEK8UDcZgzVN"

# Параметры торговли
SYMBOL = "RFCUSDT"  # Символ, например "FUSDT" или "BTCUSDT"
SIDE = "Sell"    # Или "Buy"
POLL_INTERVAL_SECONDS = 5       # Частота проверки (в секундах)

logger = DummyLogger()
telegram = DummyTelegram()

driver = BybitDriver(
    api_key=API_KEY,
    api_secret=API_SECRET,
    logger=logger,
    telegram=telegram
)

def main():
    driver.wait_chase_order(SYMBOL, SIDE)

if __name__ == "__main__":

    main()