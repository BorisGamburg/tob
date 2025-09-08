class RSICheck:
    def __init__(self, symbol=None, bybit_driver=None, logger=None):
        self.symbol = symbol
        self.side = None
        self.threshold = None
        self.timeframe = None
        self.is_rsi_snapped = False
        self.rsi_curr = None
        self.bybit_driver = bybit_driver
        self.logger = logger


    def reset(self, tf=None, threshold=None, side=None):
        self.is_rsi_snapped = False
        self.timeframe = tf
        self.threshold = threshold
        self.side = side


    def rsi_snapped(self):
        self.rsi_curr = self.bybit_driver.calculate_last_rsi(self.symbol, interval=self.timeframe)
        #self.logger.debug(f"RSI {self.rsi_curr} на TF={self.timeframe}")

        if self.is_rsi_snapped:
            # Проверяем, не надо ли сбросить is_rsi_snapped
            if ((self.side == "Sell") and (self.rsi_curr < 50)) or \
               ((self.side == "Buy") and (self.rsi_curr > 50)):
                self.is_rsi_snapped = False
                self.logger.debug(f"is_rsi_snapped сброшен. {self.side} TF={self.timeframe}")

        else:
            # Проверяем, не надо ли установить is_rsi_snapped
            if self.check_rsi_threshold(): 
                self.is_rsi_snapped = True
                self.logger.debug(f"rsi_snapped. {self.side} TF={self.timeframe}")

        return self.is_rsi_snapped
        
        
    def check_rsi_threshold(self):
        """Проверяет RSI и защелкивает состояние, если порог превышен."""
        rsi_exceeded = self._check_rsi_threshold()
        if rsi_exceeded: 
            #self.logger.info(f"rsi_threshold превышен.")
            return True
        else:
            return False


    def _check_rsi_threshold(self):
        """Проверяет достиг ли RSI порога."""
        if self.side == "Buy":
            if self.rsi_curr < self.threshold:
                self.logger.debug(f"{self.symbol}: RSI({self.timeframe}) {self.rsi_curr} меньше порога {self.threshold}")
                return True
            else:
                return False
        elif self.side == "Sell":
            if self.rsi_curr > self.threshold:
                self.logger.debug(f"{self.symbol}: RSI({self.timeframe}) {self.rsi_curr} больше порога {self.threshold}")
                return True
            else:
                return False

