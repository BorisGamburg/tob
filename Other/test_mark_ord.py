import logging
from bybit_driver import BybitDriver

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

bybit_driver = BybitDriver('DOGEUSDT', logger=logger)

bybit_driver.place_market_order(side='Buy', position_idx=2, qty=1)
