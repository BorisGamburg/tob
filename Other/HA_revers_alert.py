import logging
import time
from ha_revers import HARevers
from telegram import Telegram


class TradingBot:
    """A trading bot class for managing market orders based on RSI, HA, and price conditions."""
    
    def __init__(self):
        """Initialize the trading bot with configuration and dependencies."""
        # Logging Setup
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # Default trading parameters
        self.symbol = 'DOGEUSDT'
        self.timeframe = 15
        self.check_interval = 30

        # Telegram Setup
        self.telegram = Telegram(logger=self.logger)
        
        # Initialize strategy components
        self.ha_revers = HARevers(
            symbol=self.symbol,
            timeframe=self.timeframe,
            logger=self.logger,
            telegram=self.telegram
        )

    def log_parameters(self):
        """Log the trading parameters for reference."""
        self.logger.info("")
        self.logger.info(f"Symbol: {self.symbol}")
        self.logger.info(f"Timeframe: {self.timeframe}")
        self.logger.info(f"Check Interval: {self.check_interval}")
        self.logger.info("")

    def run(self):
        """Main loop of the bot: fetch data, process signals, and execute trades."""
        self.logger.info("Starting bot...")
        while True:
            try:
                # Проверяем разворот HA
                if not self.ha_revers._check_HA_revers():
                    time.sleep(self.check_interval)
                    continue
            except KeyboardInterrupt:
                self.logger.info("Bot stopped by user.")
                break
            except Exception as e:
                self.logger.error(f"An error occurred in the main loop: {e}")
                time.sleep(5)

    def log(self, message):
        self.logger.info(message)
        self.telegram.send_telegram_message(message)


if __name__ == '__main__':
    bot = TradingBot()
    bot.run()