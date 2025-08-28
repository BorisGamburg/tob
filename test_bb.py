from bybit_driver import BybitDriver
from telegram import Telegram
import logging


def main():
    # Logging Setup
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Telegram Setup
    telegram = Telegram(logger=logger)

    # BybitDriver Setup
    api_key="beERCRcFrsJl19mupg"
    api_secret="e9kHWxgBwhWjVWC5U7CheH0sAWDawUVtpXUY"
    bybit_driver = BybitDriver(
        api_key=api_key, 
        api_secret=api_secret, 
        logger=logger, 
        telegram=telegram
    )

    #print(bybit_driver.get_close_prices_old(symbol="BLASTUSDT", interval="60"))
    #print(bybit_driver.get_close_prices(symbol="BLASTUSDT", interval="60"))
    
    h, m, l = bybit_driver.calc_bb(symbol="BLASTUSDT1", interval="60")
    logger.info(f"High: {h}, Middle: {m}, Low: {l}")

# Добавьте это, чтобы main() вызывалась
if __name__ == "__main__":
    main()    