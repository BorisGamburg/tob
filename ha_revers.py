import logging
import pandas as pd
import time
from datetime import datetime
from bybit_driver import BybitDriver
from config_manager import ConfigManager
from telegram import Telegram
from price_check import PriceCheck


class HARevers:
    def __init__(self, symbol='DOGEUSDT', bybit_driver=None, logger=None
    ):
        self.symbol = symbol
        self.timeframe = None
        self.candle_limit = 200
        self.percent_of_interval = 0.99
        self.logger = logger
        self.last_candle_ts = None  
        self.revers_signal = None
        self.bybit_driver = bybit_driver


    def reset(self, tf=None):
        self.timeframe = tf
        self.last_candle_ts = None  
        self.revers_signal = None


    # --- Heikin Ashi Calculation Function ---
    def _calc_HA(self, ohlcv_df):
        try:
            df = ohlcv_df.copy()
            df['HA_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
            df['HA_open'] = 0.0
            df.loc[df.index[0], 'HA_open'] = df['open'].iloc[0]
            for i in range(1, len(df)):
                df.loc[df.index[i], 'HA_open'] = (df['HA_open'].iloc[i - 1] + df['HA_close'].iloc[i - 1]) / 2
            df['HA_high'] = df[['high', 'HA_open', 'HA_close']].max(axis=1)
            df['HA_low'] = df[['low', 'HA_open', 'HA_close']].min(axis=1)
            return df[['HA_open', 'HA_high', 'HA_low', 'HA_close']]
        except Exception as e:
            self.logger.error(f"Ошибка при вычислении Heikin Ashi: {e}")
            return pd.DataFrame()

    ## Функция проверки разворота
    def check_for_reversal(self, ha_df):
        if len(ha_df) < 3:
            # We need at least three candles for analysis: forming, just closed, and previously closed.
            return None, None

        prev_ha = ha_df.iloc[-2]
        # prev_ha is the candle before the just-closed one (iloc[-3])
        prevprev_ha = ha_df.iloc[-3]

        current_is_green = prev_ha['HA_close'] > prev_ha['HA_open']
        prev_is_green = prevprev_ha['HA_close'] > prevprev_ha['HA_open']

        # Bearish reversal (SELL signal)
        if prev_is_green and not current_is_green:
            return 'Sell', {
                'time': ha_df.index[-1], # Timestamp
                'type': 'Sell',
                'price': prev_ha['HA_close'],
                'description': 'Heikin Ashi Bearish Reversal (Sell Signal)'
            }
        # Bullish reversal (BUY signal)
        if not prev_is_green and current_is_green:
            return 'Buy', {
                'time': ha_df.index[-1], # Timestamp 
                'type': 'Buy',
                'price': prev_ha['HA_close'],
                'description': 'Heikin Ashi Bullish Reversal (Buy Signal)'
            }
        
        return None, None # No reversal detected


    def wait_control_time(self):
        ts_last_candle_s = self.get_curr_candle_ts()

        # Получить текущее время: ts_now
        ts_now_s = time.time()

        # Найти время контроля: ts_control
        ts_control_s = ts_last_candle_s + (int(self.timeframe) * 60 * self.percent_of_interval)

        # Сравниваем ts_now и ts_control 
        if (ts_now_s < ts_control_s):
            # ждать до ts_control
            wait_time_s = ts_control_s - ts_now_s
            self.logger.info(f"Current time ({datetime.fromtimestamp(ts_now_s).strftime('%H:%M:%S')}) is before control point ({datetime.fromtimestamp(ts_control_s).strftime('%H:%M:%S')}). Waiting for {wait_time_s:.2f} seconds...")
            time.sleep(wait_time_s)
        else:
            # Время контроля наступило -> выходим
            return


    def get_curr_candle_ts(self):
        ohlcv_df = self.bybit_driver.get_kline_data(self.symbol, self.timeframe, self.candle_limit)
        ts_prev_candle_s = ohlcv_df.iloc[-1]['timestamp'].timestamp()
        return ts_prev_candle_s
    

    def is_new_candle(self):
        # Первый заход
        if self.last_candle_ts is None:
            # Первый заход
            self.last_candle_ts = self.get_curr_candle_ts()
            return False

        if self._is_new_candle(self.last_candle_ts):
            self.last_candle_ts = self.get_curr_candle_ts()
            return True
        else:
            self.last_candle_ts = self.get_curr_candle_ts()
            return False



    def _is_new_candle(self, ts_prev_candle_s):
        # Получаем TS текущей свечи
        ts_curr_candle_s = self.get_curr_candle_ts()

        # Сравниваем TS 
        if ts_prev_candle_s != ts_curr_candle_s:
            # Новая свеча
            return True
        else:
            # Старая свеча.
            return False
        

    def check_HA_revers(self, side):
        # revers_signal может быть None, "Buy" или "Sell"
        if self.revers_signal is not None:
            if self.revers_signal == side:
                return True
            else:
                return False
        else:
            return False

        
    def _check_HA_revers(self):
        if self.is_new_candle():
            self.revers_signal = self.__check_HA_revers()
        else:
            self.revers_signal = None


    def __check_HA_revers(self):    
        ohlcv_df = self.bybit_driver.get_kline_data(self.symbol, self.timeframe, self.candle_limit)
        ha_df = self.calc_HA(ohlcv_df)
        if not ha_df.empty:
            revers_signal, signal_data = self.check_for_reversal(ha_df)
            if revers_signal is not None:
                return revers_signal
            else:
                return None
        else:
            self.logger.warning("Received empty Heikin Ashi DataFrame. Check OHLCV data.")
            return None # No signal, return old timestamp
        

    def calc_HA(self, ohlcv_df):
        # Prepare OHLCV data for Heikin Ashi calculation
        ohlcv_df_processed = ohlcv_df.copy()
        ohlcv_df_processed.set_index(pd.to_datetime(ohlcv_df_processed['timestamp'], unit='ms'), inplace=True)
        if 'timestamp' in ohlcv_df_processed.columns:
            ohlcv_df_processed.drop(columns=['timestamp'], inplace=True)

        ha_df = self._calc_HA(ohlcv_df_processed)
        return ha_df# No signal, return old timestamp
    
    def log_signal(self, signal):
        log_time = signal['time'].strftime('%Y-%m-%d %H:%M:%S')

        self.logger.debug(f"----- NEW SIGNAL -----")
        self.logger.debug(f"Time: {log_time}")
        self.logger.debug(f"Type: {signal['type']}")
        self.logger.debug(f"Price: {signal['price']:.3f}")
        self.logger.debug(f"Timeframe: {self.timeframe}")
        self.logger.debug(f"Description: {signal['description']}")
        self.logger.debug(f"-------------------------")




