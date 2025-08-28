from pybit.unified_trading import WebSocket
from time import sleep
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def handle_message(message):
    """Обработка сообщений от WebSocket."""
    try:
        # Проверяем, есть ли данные по ордерам
        if "topic" in message and message["topic"] == "order":
            for order in message["data"]:
                order_id = order.get("orderId", "N/A")
                status = order.get("orderStatus", "Unknown")
                side = order.get("side", "N/A")
                qty = order.get("qty", "N/A")
                price = order.get("price", "N/A")
                symbol = order.get("symbol", "N/A")
                
                # Формируем сообщение в зависимости от статуса
                if status == "Filled":
                    logger.info(f"✅ Ордер исполнен: {symbol} {side} {qty} @ {price} (ID: {order_id})")
                elif status == "Cancelled":
                    logger.info(f"❌ Ордер отменен: {symbol} {side} {qty} @ {price} (ID: {order_id})")
                elif status == "New":
                    logger.info(f"📝 Новый ордер: {symbol} {side} {qty} @ {price} (ID: {order_id})")
                elif status == "PartiallyFilled":
                    logger.info(f"🔄 Ордер частично исполнен: {symbol} {side} {qty} @ {price} (ID: {order_id})")
                else:
                    logger.info(f"ℹ️ Обновление ордера: {symbol} {side} {qty} @ {price}, Статус: {status} (ID: {order_id})")
        else:
            logger.info(f"Получено сообщение: {message}")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")

def main():
    # Инициализация WebSocket
    ws = WebSocket(
        testnet=True,
        channel_type="private",
        api_key="tdOOHexstm9ewR4JL6",
        api_secret="Nte5SL2QuL4rKQeScAPp9WXzVInIhXPVCXyA"
    )

    # Запуск стрима ордеров
    ws.order_stream(callback=handle_message)

    # Бесконечный цикл для поддержания работы
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
        ws.exit()  # Корректное завершение WebSocket соединения

if __name__ == "__main__":
    main()