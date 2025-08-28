class SmartStopLoss:
    def __init__(self, symbol, poll_interval,
                 get_cur_balance_func, get_cur_pos_size_func, get_cur_price_func,
                 get_pos_side_func, reduce_pos_func, log_action_func, log_info_func,
                 set_trading_enabled_func, logger, bybit_driver: BybitDriver,
                 liquidation_warning_margin_ratio=0.10,
                 liquidation_critical_margin_ratio=0.05,
                 liquidation_price_proximity_warning=0.05, # 5% до ликвидации
                 liquidation_price_proximity_critical=0.01): # 1% до ликвидации
        """
        Инициализация класса SmartStopLoss для контроля риска ликвидации.
        """
        self.logger = logger
        self.bybit_driver = bybit_driver
        self.symbol = symbol
        self.poll_interval = poll_interval
        self.get_cur_balance = get_cur_balance_func
        self.get_cur_pos_size = get_cur_pos_size_func
        self.get_cur_price = get_cur_price_func
        self.get_pos_side = get_pos_side_func
        self.reduce_pos = reduce_pos_func
        self.log_action = log_action_func
        self.log_info = log_info_func
        self.set_trading_enabled = set_trading_enabled_func
        self.trading_enabled = True
        self.telegram_notifier = Telegram(self.logger)
        self.liquidation_warning_margin = liquidation_warning_margin_ratio
        self.liquidation_critical_margin = liquidation_critical_margin_ratio
        self.liquidation_proximity_warning = liquidation_price_proximity_warning
        self.liquidation_proximity_critical = liquidation_price_proximity_critical

    def run(self):
        while True:
            try:
                positions = self.bybit_driver.get_positions(symbol=self.symbol)
                if positions and positions['result']['list']:
                    for position in positions['result']['list']:
                        if position['symbol'] == self.symbol and float(position['size']) != 0:
                            liquidation_price = float(position.get('liquidationPrice', float('inf'))) # Обработка отсутствия цены
                            margin_ratio = float(position.get('marginRatio', 1.0)) # Обработка отсутствия ratio
                            current_price = self.get_cur_price()

                            # Проверка риска ликвидации по марже
                            if margin_ratio < self.liquidation_critical_margin:
                                self.logger.critical(f"Критически низкая маржа: {margin_ratio:.4f}")
                                self.telegram_notifier.send_telegram_message(f"🚨 КРИТИЧНО! Риск ликвидации по марже: {margin_ratio:.4f}. Попытка закрыть позицию.")
                                # Действия по закрытию позиции
                                self.reduce_pos(self.get_cur_pos_size()) # Пример: закрыть всю позицию
                            elif margin_ratio < self.liquidation_warning_margin:
                                self.logger.warning(f"Предупреждение: низкая маржа: {margin_ratio:.4f}")
                                self.telegram_notifier.send_telegram_message(f"⚠️ Внимание! Низкая маржа: {margin_ratio:.4f}. Рассмотрите уменьшение плеча или закрытие позиции.")

                            # Проверка риска ликвидации по близости цены
                            if liquidation_price != float('inf') and current_price != 0:
                                proximity = abs(current_price - liquidation_price) / current_price
                                if proximity < self.liquidation_proximity_critical:
                                    self.logger.critical(f"Критически близко к цене ликвидации: {proximity:.4f} ({current_price:.4f} vs {liquidation_price:.4f})")
                                    self.telegram_notifier.send_telegram_message(f"🚨 КРИТИЧНО! Цена ликвидации близко: {proximity:.4f} ({current_price:.4f} vs {liquidation_price:.4f}). Попытка закрыть позицию.")
                                    # Действия по закрытию позиции
                                    self.reduce_pos(self.get_cur_pos_size()) # Пример: закрыть всю позицию
                                elif proximity < self.liquidation_proximity_warning:
                                    self.logger.warning(f"Предупреждение: цена ликвидации близко: {proximity:.4f} ({current_price:.4f} vs {liquidation_price:.4f})")
                                    self.telegram_notifier.send_telegram_message(f"⚠️ Внимание! Цена ликвидации рядом: {proximity:.4f} ({current_price:.4f} vs {liquidation_price:.4f}). Рассмотрите стоп-лосс.")
            except Exception as e:
                self.logger.error(f"Ошибка при получении информации о позиции для контроля ликвидации: {e}")

            time.sleep(self.poll_interval)

if __name__ == "__main__":
    # Пример использования (необходимо адаптировать под ваш BybitDriver)
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    symbol = "BTCUSDT"

    # Инициализация BybitDriver (предполагается, что он у вас уже есть)
    bybit_driver_instance = BybitDriver(symbol=symbol, logger=logger)

    def get_bal():
        # ... (ваша функция для получения баланса) ...
        return 1000

    def get_pos_size():
        buy_size, sell_size, _, _ = bybit_driver_instance.get_position_sizes()
        return buy_size + sell_size

    def get_price():
        return bybit_driver_instance.get_last_price()

    def get_side():
        buy_size, sell_size, _, _ = bybit_driver_instance.get_position_sizes()
        if buy_size > 0 and sell_size == 0:
            return "Buy"
        elif sell_size > 0 and buy_size == 0:
            return "Sell"
        else:
            return None

    def reduce_pos(new_size):
        print(f"Bot Action: Запрос на уменьшение позиции до {new_size}")
        return True

    def log_act(message):
        logger.info(message)

    def log_inf(message):
        logger.info(message)

    def set_trade_enabled(enabled):
        print(f"Bot Trading Enabled: {enabled}")

    smart_stop = SmartStopLoss(
        symbol=symbol,
        poll_interval=10,
        get_cur_balance_func=get_bal,
        get_cur_pos_size_func=get_pos_size,
        get_cur_price_func=get_price,
        get_pos_side_func=get_side,
        reduce_pos_func=reduce_pos,
        log_action_func=log_act,
        log_info_func=log_inf,
        set_trading_enabled_func=set_trade_enabled,
        logger=logger,
        bybit_driver=bybit_driver_instance,
        liquidation_warning_margin_ratio=0.15,
        liquidation_critical_margin_ratio=0.08,
        liquidation_price_proximity_warning=0.03,
        liquidation_price_proximity_critical=0.015
    )

    print("Запуск класса SmartStopLoss (контроль риска ликвидации)...")
    smart_stop.run()