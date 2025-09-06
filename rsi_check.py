#import logging
#import time
#from bybit_driver import BybitDriver
#from telegram import Telegram
#from config_manager import ConfigManager
from price_check import PriceCheck
#import sys

class RSICheck:
    def __init__(self, symbol=None, rsi_threshold=0, timeframe="15", bybit_driver=None, 
                 logger=None, telegram=None):
        self.symbol = symbol
        self.rsi_threshold = rsi_threshold
        self.timeframe = timeframe
        self.last_rsi = None
        self.bybit_driver = bybit_driver
        self.logger = logger
        self.telegram = telegram
        self.price_check = PriceCheck(symbol, bybit_driver, logger, telegram)
        self.is_rsi_snapped = False
        self.rsi_curr = None



    def log(self, message):
        self.telegram.send_telegram_message(message)
        self.logger.info(f"{message}")


    def rsi_snapped(self, tf=None, threshold=None, side=None):
        self.rsi_curr = self.bybit_driver.calculate_last_rsi(self.symbol, interval=tf)

        if self.is_rsi_snapped:
            return True

        if self.check_rsi_threshold(threshold, side=side): 
            self.is_rsi_snapped = True
            self.logger.debug(f"rsi_snapped. {side} TF={tf}")
            return True
        else:
            return False
        
        
    def check_rsi_threshold(self, rsi_threshold, side=None):
        if rsi_threshold is None:
            #self.log("Проверка rsi_threshold выключена.")
            return True
        
        """Проверяет RSI и защелкивает состояние, если порог превышен."""
        rsi_exceeded = self._check_rsi_threshold(rsi_threshold, side=side)
        if rsi_exceeded: 
            #self.logger.info(f"rsi_threshold превышен.")
            return True
        else:
            return False


    def _check_rsi_threshold(self, rsi_threshold, side=None):
        """Проверяет достиг ли RSI порога."""
        if side == "Buy":
            if self.rsi_curr < rsi_threshold:
                self.logger.debug(f"{self.symbol}: RSI {self.rsi_curr} меньше порога {rsi_threshold}")
                return True
            else:
                return False
        elif side == "Sell":
            if self.rsi_curr > rsi_threshold:
                self.logger.debug(f"{self.symbol}: RSI {self.rsi_curr} больше порога {rsi_threshold}")
                return True
            else:
                return False

