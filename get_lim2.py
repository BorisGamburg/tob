import logging
from bybit_driver import BybitDriver
import random

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

def main():
    logger = DummyLogger()
    telegram = DummyTelegram()

    driver = BybitDriver(
        api_key=API_KEY,
        api_secret=API_SECRET,
        logger=logger,
        telegram=telegram
    )

    symbol = "FUSDT"  # Замените на нужную торговую пару
    side = "Sell"     # Или "Sell"

    try:
        # Получаем текущие лимитные ордера для примера
        print(f"Поиск открытых лимитных ордеров {side} для {symbol}...")
        current_orders = driver.get_limit_orders(symbol=symbol, side=side)
        if not current_orders:
            print("Лимитные ордера для перемещения не найдены. Создайте ордер вручную и запустите скрипт еще раз.")
            return
        
        # Выбираем первый ордер
        order_to_move = current_orders[0]
        original_price = float(order_to_move['price'])
        
        # Рассчитываем новую цену. Например, смещаем на 0.1% от текущей.
        # Это предотвратит ошибку, если новая цена будет такой же, как и старая.
        price_change_percent = 0.05
        new_price = original_price * (1 + price_change_percent)
        
        print(f"Текущая цена ордера: {original_price}")
        print(f"Перемещаем ордер на новую цену: {new_price}")
        
        # Вызываем новую функцию для перемещения ордера
        result = driver.move_limit_order(
            symbol=symbol, 
            side=side, 
            new_price=new_price
        )

        if result.get("retCode") == 0:
            print("✅ Ордер успешно перемещен!")
        else:
            print(f"❌ Не удалось переместить ордер. Ошибка: {result.get('retMsg')}")
            
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")


if __name__ == "__main__":
    main()