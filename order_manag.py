from pybit.unified_trading import WebSocket
from time import sleep
import logging
from bybit_driver import BybitDriver


class OrderManager:
    def __init__(self, api_key: str, api_secret: str, bybit_driver: BybitDriver, callback_function=None, logger=None):
        """
        Initializes the BybitOrderTracker.

        Args:
            api_key (str): Your Bybit API key.
            api_secret (str): Your Bybit API secret.
            testnet (bool): Set to True for testnet, False for mainnet. Defaults to False.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.bybit_driver = bybit_driver 
        self.callback_func = callback_function
        self.logger = logger 

        self.ws = None
        self.logger.debug("OrderManager initialized.")


    def _handle_message(self, message: dict):
        """
        Processes incoming WebSocket messages.

        Args:
            message (dict): The message received from the WebSocket.
        """
        try:
            if "topic" in message and message["topic"] == "order":
                for order in message["data"]:
                    if order.get("orderStatus") == "Filled":
                        if self.callback_func:
                            self.callback_func(order)
            else:
                self.logger.info(f"Получено сообщение: {message}")

        except Exception as e:
            self.logger.error(f"Ошибка при обработке сообщения: {e}")


    def start(self):
        """Starts the WebSocket connection and subscribes to the order stream."""
        if self.ws:
            self.logger.warning("WebSocket already running. Please stop it first.")
            return

        self.ws = WebSocket(
            testnet=False,
            channel_type="private",
            api_key=self.api_key,
            api_secret=self.api_secret
        )
        self.ws.order_stream(callback=self._handle_message)



